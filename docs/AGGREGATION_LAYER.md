# Flow Aggregation Layer for SSH/FTP Brute Force Detection

## Overview

The flow aggregation layer is a new component in the IDS pipeline that detects SSH and FTP brute force attacks by analyzing patterns across multiple short-lived flows. Unlike the per-flow classifier, which analyzes individual connections, the aggregator groups flows by `(src_ip, dst_ip, dst_port)` and applies rule-based thresholds to identify coordinated brute force attempts.

### The Problem It Solves

**Without aggregation:**
- SSH brute force attacks (e.g., Hydra) open many short-lived parallel connections from different source ports
- Each connection becomes a separate flow with few packets and short duration
- The trained model sees each flow independently and classifies them as "Normal Traffic"
- The brute force pattern is missed entirely

**With aggregation:**
- All flows from the same source IP to the same destination IP:port are grouped
- Aggregate metrics are computed across all flows in a 60-second time window
- Rule-based thresholds detect when the pattern matches SSH/FTP brute force
- A single aggregated alert is emitted to the dashboard instead of hundreds of individual normal flows

## Architecture

### Integration Points

The aggregation layer integrates seamlessly with the existing pipeline:

```
┌─────────────────────────────────────────────────────────────┐
│                    Packet Sniffer Thread                     │
│  Captures packets & groups into flows by 5-tuple            │
└────────────────────────┬────────────────────────────────────┘
                         │ (flow completion: FIN/RST or idle timeout)
                         ▼
┌─────────────────────────────────────────────────────────────┐
│               Completed Flows Queue                          │
└────────────────────────┬────────────────────────────────────┘
                         │
        ┌────────────────┴────────────────┐
        │                                 │
        ▼                                 ▼
┌─────────────────────────┐    ┌─────────────────────────┐
│  Per-Flow Classifier    │    │   Flow Aggregator       │
│ (ML Model v2)           │    │ (Rule-Based Detection)  │
│ - Extract features      │    │ - Group by (s,d,p)     │
│ - Get prediction        │    │ - Compute aggregate     │
│ - Add to history        │    │   features              │
└─────────────────────────┘    │ - Check thresholds      │
        │                       │ - Emit alert if match   │
        └───────────┬───────────┘
                    ▼
        ┌───────────────────────┐
        │  Predictions History  │
        │  (deque, maxlen=100)  │
        └────────────┬──────────┘
                     │
                     ▼
        ┌────────────────────────┐
        │   REST API Endpoints   │
        │  - /api/predictions    │
        │  - /api/aggregation*   │
        │  - /api/status         │
        └────────────────────────┘
```

Both per-flow predictions and aggregated alerts go into the same `predictions_history` deque, so the dashboard sees all alerts in chronological order.

## Algorithm Details

### Flow Grouping

Flows are grouped by a 3-tuple instead of the full 5-tuple:

```
Group Key = (src_ip, dst_ip, dst_port)
  │         Ignores src_port entirely
  └─ This captures attempts from different ports on the same source
```

**Why?** Brute force tools like Hydra use different source ports for each attempt. Grouping by `(src, dst, port)` captures all attempts to the same target service.

### Time Window

Each group maintains a **60-second sliding window**:

- When a new flow is added, the aggregator finds an existing window for that group
- If the window is still active (< 60 seconds old), the flow is added to it
- If the window has expired, a new window is started
- Expired windows are automatically cleaned up by the flusher thread

### Aggregate Features

For each flow group, the aggregator computes:

| Feature | Definition | Threshold |
|---------|-----------|-----------|
| `flow_count` | Number of flows in window | > 10 |
| `avg_duration` | Mean duration across flows (seconds) | < 5.0 |
| `min_duration` | Minimum flow duration | (informational) |
| `max_duration` | Maximum flow duration | (informational) |
| `avg_packet_count` | Mean packets per flow | < 20 |
| `min_packet_count` | Minimum packets in a flow | (informational) |
| `max_packet_count` | Maximum packets in a flow | (informational) |
| `avg_bytes` | Mean bytes per flow | (informational) |
| `fin_ratio` | Fraction of flows with FIN flag | (informational) |
| `rst_ratio` | Fraction of flows with RST flag | (informational) |
| `connection_rate` | Flows per second in window | (informational) |

### Detection Rules

An alert is generated if **ALL** of these conditions are met:

```python
if (
    dst_port in (22, 21) and              # SSH or FTP
    flow_count > 10 and                    # More than 10 connection attempts
    avg_duration < 5.0 and                 # Attempts are short-lived
    avg_packet_count < 20                  # Few packets exchanged
):
    # Classify as SSH/FTP Brute Force
```

**Why these thresholds?**

- **Port 22/21**: These are the standard SSH and FTP ports
- **flow_count > 10**: Legitimate SSH/FTP usage rarely has 10+ attempts in 60 seconds
- **avg_duration < 5s**: Successful logins or data transfers take longer; failed attempts abort quickly
- **avg_packet_count < 20**: Authentication failures involve minimal packet exchange (typically 3-way handshake + a few payload packets)

### Confidence Scoring

When brute force is detected, a confidence score is computed:

```python
confidence = min(
    0.95,  # Cap at 95% max
    (flow_count / 20) * 0.4 +           # 40% weight on flow count
    ((5.0 - avg_duration) / 5.0) * 0.3 + # 30% weight on short duration
    ((20 - avg_packet_count) / 20) * 0.3  # 30% weight on low packet count
)
```

- Higher flow count → higher confidence
- Shorter durations → higher confidence
- Fewer packets → higher confidence

### Double-Alert Prevention

Once a group is flagged in a time window, it is marked as "alerted" for that window. The same group in the same window will not generate another alert, even if more flows arrive.

A new window (60+ seconds later) would generate a new alert.

## Data Structures

### FlowMetrics (Per Group)

```python
@dataclass
class FlowMetrics:
    src_ip: str               # Source IP
    dst_ip: str               # Destination IP
    dst_port: int             # Destination port
    flow_count: int = 0       # Number of flows added
    durations: List[float]    # Duration of each flow
    packet_counts: List[int]  # Packet count of each flow
    bytes_counts: List[int]   # Byte count of each flow
    fin_count: int = 0        # Flows with FIN flag
    rst_count: int = 0        # Flows with RST flag
    window_start_time: float  # When this window started
```

### FlowAggregator (Main Class)

```python
class FlowAggregator:
    flow_groups: Dict[Tuple, FlowMetrics]  # All active windows
    alerted_groups: set                    # Windows that generated alerts
    time_window: float = 60.0              # Window duration in seconds
    lock: threading.RLock                  # Thread-safe access
```

## API Endpoints

### GET /api/aggregation-windows

Get information about active flow aggregation windows:

**Response:**
```json
{
  "active_windows": 3,
  "windows": [
    {
      "src_ip": "192.168.1.100",
      "src_domain": "workstation.local",
      "dst_ip": "10.0.0.5",
      "dst_domain": "server.example.com",
      "dst_port": 22,
      "flow_count": 15,
      "window_age_seconds": 32.5,
      "aggregate_features": {
        "flow_count": 15.0,
        "avg_duration": 2.3,
        "min_duration": 1.8,
        "max_duration": 4.2,
        "avg_packet_count": 12.5,
        "min_packet_count": 8,
        "max_packet_count": 18,
        "avg_bytes": 650.0,
        "min_bytes": 400,
        "max_bytes": 950,
        "fin_ratio": 0.2,
        "rst_ratio": 0.6,
        "connection_rate": 0.46
      }
    }
  ]
}
```

### GET /api/predictions (Enhanced)

Per-flow predictions and aggregated alerts appear together:

**Response:**
```json
{
  "count": 5,
  "predictions": [
    {
      "timestamp": "2024-04-02T10:35:22.123456",
      "prediction": "Normal Traffic",
      "confidence": 0.92,
      "src_ip": "192.168.1.50",
      "dst_ip": "8.8.8.8",
      "dst_port": 53,
      "packets": 3,
      "is_aggregated": false
    },
    {
      "timestamp": "2024-04-02T10:35:45.654321",
      "attack_type": "SSH Brute Force",
      "prediction": "SSH Brute Force",
      "confidence": 0.87,
      "src_ip": "192.168.1.100",
      "dst_ip": "10.0.0.5",
      "dst_port": 22,
      "is_aggregated": true,
      "flow_count": 18,
      "window_start": "2024-04-02T10:35:15.000000",
      "window_end": "2024-04-02T10:35:45.654321",
      "aggregate_metrics": {
        "flow_count": 18.0,
        "avg_duration": 2.8,
        "avg_packet_count": 11.0,
        ...
      }
    }
  ]
}
```

**Key differences for aggregated alerts:**
- `is_aggregated: true` flag
- `attack_type`: SSH or FTP Brute Force (instead of model output)
- `flow_count`: Number of individual flows in the group
- `window_start` and `window_end`: Time window boundaries
- `aggregate_metrics`: All computed aggregation features

## Console Output

### Per-Flow Classification

```
[CLASSIFIER] ============================================================
Prediction: Normal Traffic
Confidence: 0.9234
Flow: 192.168.1.50:54321 -> 8.8.8.8:53
Packets: 3
============================================================
```

### Aggregated Alert (Brute Force)

```
[AGGREGATOR] ************************************************************
🚨 SSH Brute Force DETECTED
Source IP: 192.168.1.100
Target: 10.0.0.5:22
Flows in window: 18
Confidence: 0.8734
Window: 2024-04-02T10:35:15.000000 -> 2024-04-02T10:35:45.654321
Aggregate metrics:
  flow_count: 18.00
  avg_duration: 2.84
  avg_packet_count: 11.20
  avg_bytes: 680.50
  fin_ratio: 0.17
  rst_ratio: 0.61
  connection_rate: 0.46
************************************************************
```

## Testing the Aggregator

### Manual Testing with Hydra

1. **Start the IDS pipeline:**
   ```bash
   cd /home/sajid/Desktop/fyp
   source myenv/bin/activate
   python run_server.py
   ```

2. **In another terminal, simulate SSH brute force:**
   ```bash
   # Install Hydra if not present
   sudo apt-get install hydra-gtk
   
   # Or use nmap NSE script for SSH testing:
   nmap --script ssh-brute \
     --script-args userdb=users.txt,passdb=passwords.txt \
     target_ip
   ```

3. **Monitor the pipeline:**
   ```bash
   # Watch console output for aggregated alerts
   # Or check API endpoint:
   curl http://localhost:5000/api/predictions?limit=10
   curl http://localhost:5000/api/aggregation-windows
   ```

### Expected Behavior

**Before first few flows (0-5 seconds):**
- Individual flows appear in `/api/predictions`
- `/api/aggregation-windows` shows a growing window for (attacker_ip, target_ip, port 22)
- Per-flow model classifies each as "Normal Traffic"

**After threshold crosses (~ 10-20 flows in 60s):**
- An aggregated alert appears in `/api/predictions` with `is_aggregated: true`
- `prediction` field shows "SSH Brute Force"
- `confidence` is typically 0.80-0.95 depending on how aggressive the attack is
- Window remains in `/api/aggregation-windows` but is marked as "alerted"
- Subsequent flows from the same source to the same target go into the same window but don't generate new alerts

### Test Script

Create `test_aggregator.py`:

```python
#!/usr/bin/env python3
"""Test the flow aggregator detection."""

import requests
import json
import time
from datetime import datetime

API_BASE = "http://localhost:5000/api"

def print_section(title):
    print(f"\n{'='*60}")
    print(f"  {title}")
    print('='*60)

def monitor_aggregator():
    """Monitor aggregator detection in real-time."""
    
    print_section("Aggregator Monitoring Started")
    print(f"Time: {datetime.now().isoformat()}\n")
    
    last_alert_count = 0
    
    try:
        while True:
            # Get predictions
            resp = requests.get(f"{API_BASE}/predictions?limit=20")
            if resp.status_code != 200:
                print(f"❌ Error: {resp.status_code}")
                time.sleep(2)
                continue
            
            preds = resp.json()['predictions']
            
            # Get aggregation windows
            resp_agg = requests.get(f"{API_BASE}/aggregation-windows")
            windows = resp_agg.json()['windows'] if resp_agg.status_code == 200 else []
            
            # Check for new alerts
            alerts = [p for p in preds if p.get('is_aggregated', False)]
            
            if len(alerts) > last_alert_count:
                print_section("🚨 NEW BRUTE FORCE ALERT DETECTED")
                new_alert = alerts[-1]
                print(f"Attack Type: {new_alert.get('attack_type', 'N/A')}")
                print(f"Source IP: {new_alert['src_ip']}")
                print(f"Target: {new_alert['dst_ip']}:{new_alert['dst_port']}")
                print(f"Flows in window: {new_alert.get('flow_count', 'N/A')}")
                print(f"Confidence: {new_alert['confidence']:.2%}")
                print(f"Timestamp: {new_alert['timestamp']}")
                
                metrics = new_alert.get('aggregate_metrics', {})
                print(f"\nAggregate Metrics:")
                for key, value in metrics.items():
                    if isinstance(value, float):
                        print(f"  {key}: {value:.2f}")
                    else:
                        print(f"  {key}: {value}")
                
                last_alert_count = len(alerts)
            
            # Show active windows
            if windows:
                print(f"\n📊 Active Windows: {len(windows)}")
                for w in windows[-3:]:  # Show last 3
                    metrics = w.get('aggregate_features', {})
                    print(f"  {w['src_ip']} -> {w['dst_ip']}:{w['dst_port']}")
                    print(f"    Flows: {w['flow_count']}, Age: {w['window_age_seconds']:.1f}s")
                    if 'avg_duration' in metrics:
                        print(f"    Avg Duration: {metrics['avg_duration']:.2f}s, "
                              f"Avg Packets: {metrics['avg_packet_count']:.1f}")
            
            time.sleep(2)
    
    except KeyboardInterrupt:
        print_section("Monitoring Stopped")

if __name__ == '__main__':
    monitor_aggregator()
```

Run it:
```bash
python test_aggregator.py
```

## Configuration & Tuning

### Adjusting Thresholds

To change detection thresholds, modify [flow_aggregator.py](flow_aggregator.py) line ~150:

```python
def _check_brute_force(self, metrics: FlowMetrics, window_key: Tuple) -> Optional[Dict]:
    # Current thresholds:
    CONDITIONS_MET = (
        flow_count > 10 and              # Change this (lower = more sensitive)
        avg_duration < 5.0 and           # Change this
        avg_packet_count < 20            # Change this
    )
```

**Sensitivity tuning:**

| Threat Model | flow_count | avg_duration | avg_packet_count |
|--------------|-----------|-------------|------------------|
| **Paranoid** (catch everything) | > 5 | < 10.0 | < 30 |
| **Strict** (default) | > 10 | < 5.0 | < 20 |
| **Relaxed** (fewer false positives) | > 20 | < 3.0 | < 15 |

### Time Window Adjustment

In [pipeline.py](ids_core/pipeline.py) __init__, change:

```python
self.flow_aggregator = FlowAggregator(time_window=60.0)  # seconds
```

- **Shorter windows (30s)**: React faster to attacks, but more windows to manage
- **Longer windows (120s)**: Capture slower brute force, but higher memory usage

## Thread Safety

The aggregator uses `threading.RLock` to ensure thread-safe access:

```python
self.lock = threading.RLock()
    
with self.lock:
    # Add flow / check brute force / cleanup
```

The classifier thread calls `add_flow()` for every completed flow. The flusher thread periodically calls `cleanup_expired_windows()`. Both operations are serialized by the lock, so no race conditions occur.

## Performance Notes

- **Memory:** Each window stores lists of durations, packet counts, and byte counts. With max 100+ flows per 60s window, this is negligible (< 10KB per window)
- **CPU:** Computing stats is O(n) where n = flows in window (~100 flows → μs of work)
- **Cleanup:** Runs every 20 seconds (flusher interval), removes expired windows in O(m) where m = number of active windows (typically < 100)

## Troubleshooting

### No alerts being generated

1. Check `/api/aggregation-windows` to see if windows are being created
   - If no windows: flows aren't reaching the aggregator (check `/api/flows`)
   - If windows exist but no alerts: thresholds might be too strict
   
2. Check console output for "[AGGREGATOR]" messages
   
3. Verify network interface is correctly set in `run_server.py`

### Too many false positives

- Increase `flow_count` threshold (e.g., 15 instead of 10)
- Increase `avg_duration` threshold (e.g., 7 instead of 5)
- Increase `avg_packet_count` threshold (e.g., 25 instead of 20)

### Legitimate SSH traffic flagged

- SSH key-based authentication with multiple attempts could trigger alerts
- Solution: Add IP whitelist or increase thresholds for non-brute-force patterns
- Consider checking FIN/RST ratio — legitimate sessions typically have FIN, brute force has RST

## Future Enhancements

1. **IP Reputation Scoring**: Score based on historical behavior
2. **Temporal Analysis**: Different thresholds for peak vs. off-peak hours
3. **Whitelist Exceptions**: Exclude known good IPs (e.g., CI/CD servers)
4. **Port Scanning Detection**: Apply similar logic to port scans (many flows, few packets)
5. **Machine Learning Integration**: Train ensemble with aggregated features as input

## References

- CIC-IDS2017 Dataset: SSH Brute Force [Dataset Paper](https://www.unb.ca/cic/datasets/ids-2017.html)
- [RFC 3526 - TCP Connection States](https://tools.ietf.org/html/rfc793)
- [Scapy Documentation](https://scapy.readthedocs.io/)

---

**Author:** IDS Development Team  
**Date:** April 2024  
**Version:** 1.0
