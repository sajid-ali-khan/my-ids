# Suspicious Classification Feature

## Overview
The IDS dashboard now automatically detects and alerts on "Suspicious" traffic - normal traffic that is classified with low confidence. This helps identify network activity that may warrant closer inspection even though it's not confidently classified as an attack.

## How It Works

### Detection Logic
The pipeline monitors all classifications and applies this logic:

```
IF (prediction == "Normal Traffic" OR prediction == "Benign")
  AND confidence < 65%
THEN
  Mark as "Suspicious" and save to database
```

**Confidence Threshold: 65%**
- Above 65%: Trusted as benign (not saved)
- Below 65%: Marked as "Suspicious" (saved to database)

### Severity Assignment
Suspicious traffic is always assigned **LOW** severity regardless of other factors:
- Automatically kept with low severity for prioritization
- Allows SOC teams to focus on confirmed attacks first
- Easy to filter for manual review later

## Backend Implementation

### New Method: `_is_suspicious_traffic()`
Located in `ids_core/pipeline.py`, checks if a classification is suspicious:

```python
def _is_suspicious_traffic(self, prediction: str, confidence: float) -> bool:
    """Check if traffic is suspicious (normal/benign with low confidence)."""
    is_benign = prediction == 'Benign' or prediction == 'Normal Traffic'
    is_low_confidence = confidence < 0.65
    return is_benign and is_low_confidence
```

### Modified Method: `_save_alert_if_attack()`
Now saves both:
1. **Regular attacks** - Confidently identified malicious traffic
2. **Suspicious traffic** - Normal traffic with questionable confidence

```python
def _save_alert_if_attack(self, pred_record, flow, prediction, confidence):
    """Save alert to database if prediction is attack or suspicious."""
    
    # Check for suspicious traffic
    is_suspicious = self._is_suspicious_traffic(prediction, confidence)
    
    # Determine if should be saved
    is_attack = not (prediction == 'Benign' or prediction == 'Normal Traffic')
    
    if is_suspicious:
        # Save as Suspicious with low severity
        attack_type = 'Suspicious'
        severity = 'low'
    else:
        # Regular attack classification
        attack_type = prediction
        severity = determine_severity(confidence)
```

### Console Output
When suspicious traffic is detected:

```
⚠️  SUSPICIOUS TRAFFIC (normal/benign with low confidence)
Prediction: Normal Traffic
Confidence: 0.6234
Flow: 192.168.1.100:54321 -> 8.8.8.8:443

[DB] ⚠️  Saved SUSPICIOUS alert: 192.168.1.100:54321 -> 8.8.8.8:443 (confidence: 62.34%)
```

## Frontend Implementation

### Alert History Filter
The "Alert Type" filter now includes:
```html
<option value="Suspicious">⚠️  Suspicious</option>
```

Users can filter to show only suspicious alerts for review.

### Visual Styling
Suspicious alerts are visually distinct:

**Row Styling:**
- Background: `#fffbf0` (light yellow/cream)
- Hover: `#fff8e6` (slightly darker)

**Attack Type Cell:**
- Background: `#fff3cd` (yellow)
- Border-left: 3px solid `#ffc107` (orange)
- Text: `#856404` (dark brown)
- Prefix: `⚠️  Suspicious`

Example row display:
```
[Time] | [LOW] | ⚠️  Suspicious | 192.168.1.1:1234 | 10.0.0.1:443 | 62% | Pending | [Acknowledge]
       (light yellow background)
```

### JavaScript Rendering
In `web/script.js`, the `updateAlertTable()` function:

```javascript
// Check if this is a suspicious alert
const isSuspicious = alert.attack_type === 'Suspicious';
const rowClass = isSuspicious ? 'suspicious-row' : '';
const attackTypeClass = isSuspicious ? 'attack-type-suspicious' : '';
const attackTypeDisplay = isSuspicious ? '⚠️  ' + alert.attack_type : alert.attack_type;

// Render with appropriate styling
return `
    <tr class="${rowClass}">
        ...
        <td><span class="${attackTypeClass}">${attackTypeDisplay}</span></td>
        ...
    </tr>
`;
```

## Database Schema
Suspicious alerts are stored in the same `alerts` table:

```sql
INSERT INTO alerts (
    timestamp,
    src_ip, dst_ip,
    src_port, dst_port,
    protocol,
    attack_type,        -- "Suspicious"
    confidence,         -- < 0.65
    severity,           -- "low"
    is_aggregated,
    flow_count
) VALUES (...)
```

## Usage Examples

### Example 1: DNS over HTTPS
```
Encrypted DNS query to cloudflare (1.1.1.1:443)
Classified as: Normal Traffic
Confidence: 52%
Result: Marked as SUSPICIOUS ⚠️

Reason: Model typically sees 85%+ confidence for known HTTPS patterns.
Action: SOC team can review to ensure it's legitimate DNS-over-HTTPS
```

### Example 2: Unusual Web Traffic
```
HTTP request to unusual port
Classified as: Benign
Confidence: 61%
Result: Marked as SUSPICIOUS ⚠️

Reason: Model is uncertain about this traffic pattern
Action: Could be benign web service or suspicious activity
```

### Example 3: P2P Traffic
```
P2P communication between internal machines
Classified as: Normal Traffic
Confidence: 59%
Result: Marked as SUSPICIOUS ⚠️

Reason: Model hasn't seen enough similar patterns to be confident
Action: SOC can verify if this is authorized P2P application
```

## Filtering & Reporting

### Alert History Tab
1. Click "🔍 Alert History" tab
2. Select "Alert Type" filter: "⚠️  Suspicious"
3. Adjust confidence threshold if needed
4. Review suspicious alerts identified by the system

### CSV Export
Export suspicious alerts with all metadata:
```csv
Time,Severity,Attack Type,Source,Destination,Confidence,Status,Acknowledged
22:45:31,LOW,⚠️  Suspicious,192.168.1.1:5432,10.0.0.50:443,62%,Pending,False
22:43:15,LOW,⚠️  Suspicious,192.168.1.2:51234,1.1.1.1:443,58%,Pending,False
```

### Statistics Dashboard
Statistics updated to track suspicious alerts:
- "Total Alerts" includes suspicious classifications
- "Low Severity" count reflects suspicious traffic
- Timeline shows suspicious alert patterns

## Configuration

### Adjusting Confidence Threshold
To change the suspicious classification threshold, modify in `ids_core/pipeline.py`:

```python
def _is_suspicious_traffic(self, prediction: str, confidence: float) -> bool:
    # Change this value (currently 0.65 = 65%)
    is_low_confidence = confidence < 0.65  # ← Adjust here
    return is_benign and is_low_confidence
```

Common thresholds:
- `0.50` (50%) - More aggressive, more alerts
- `0.65` (65%) - Balanced (current)
- `0.75` (75%) - Conservative, fewer alerts

### Severity Level
Suspicious classifications are always "low" severity. To change:

```python
if is_suspicious:
    severity = 'low'  # ← Change to 'medium' or 'high' if desired
```

## SOC Workflow

### Recommended Process
1. **Dashboard Monitoring**
   - Monitor Live Monitor tab for real-time alerts
   - Critical/High alerts require immediate investigation

2. **Alert History Review**
   - Check Low/Medium alerts in Alert History tab
   - Filter by "Suspicious" to review questionable traffic
   - Daily review of suspicious alerts (15-30 min)

3. **Verification**
   - Check source IP: Is it internal or external?
   - Check destination: Is it known/trusted service?
   - Check timing: Unusual hours?
   - Check pattern: One-off or recurring?

4. **Action**
   - **False Positive**: Acknowledge and whitelist IP if legitimate
   - **Legitimate**: Acknowledge and monitor
   - **Suspicious**: Escalate for further investigation
   - **Threat**: Escalate to incident response team

## Performance Impact

### Database
- Suspicious alerts added to persistent storage
- Minimal performance impact
- Index optimization handles additional queries efficiently

### Real-time Processing
- Negligible overhead (simple confidence comparison)
- No latency added to detection pipeline

### Display
- Table rendering slightly increased but still fast
- CSS transitions smooth for visual highlighting

## Future Enhancements

1. **ML-based Confidence Tuning**
   - Learn optimal confidence thresholds per attack type
   - Adjust thresholds based on false positive rates

2. **Contextual Suspicious Detection**
   - Time-of-day analysis
   - Source IP reputation checking
   - Protocol combination analysis

3. **Suspicious Alert Notifications**
   - Optional email alerts for suspicious traffic
   - Slack/Teams integration for SOC teams
   - Custom alerting rules

4. **Suspicious Traffic ML Module**
   - Second-stage classifier for uncertain traffic
   - Anomaly detection on suspicious flows
   - Behavioral baseline comparison

5. **Reporting**
   - Suspicious traffic trends report
   - False positive rate tracking
   - Feedback loop for model improvement

## Troubleshooting

### Too Many Suspicious Alerts
- Check if model confidence is too low
- May indicate model needs retraining on current traffic
- Increase threshold: `confidence < 0.75` → `confidence < 0.50`

### Too Few Suspicious Alerts
- Model may be overly confident
- Decrease threshold: `confidence < 0.65` → `confidence < 0.80`

### Not Seeing Suspicious in Alert Type Filter
- Clear browser cache
- Refresh page
- Check browser console for JavaScript errors

### Suspicious Alerts Not Appearing in Database
- Check database enabled: `pipeline.db_enabled == True`
- Check logs for database write errors
- Verify `/opt/nids/alerts.db` has write permissions

## Testing

Run the comprehensive test suite:
```bash
python3 test_suspicious_classification.py
```

This verifies:
- ✓ Backend detection logic
- ✓ Database storage
- ✓ Frontend filtering options
- ✓ CSS styling classes
- ✓ JavaScript rendering
- ✓ HTML structure

Expected output:
```
✓ ALL TESTS PASSED - Suspicious classification feature ready!
```

## Support

For questions or issues:
1. Check test output: `python3 test_suspicious_classification.py`
2. Review logs: Check Flask server console output
3. Monitor: View browser developer console for errors
4. Check database: Verify alerts table has suspicious entries
   ```bash
   sqlite3 /opt/nids/alerts.db "SELECT attack_type, COUNT(*) FROM alerts GROUP BY attack_type;"
   ```

## Summary

| Feature | Details |
|---------|---------|
| **Trigger** | Normal/Benign traffic with confidence < 65% |
| **Storage** | Saved to alerts database as "Suspicious" |
| **Severity** | Low (for prioritization) |
| **Visibility** | Alert History tab with filter option |
| **Styling** | Yellow highlight with ⚠️  emoji |
| **Export** | Included in CSV exports |
| **Console** | Logged with warning indicator |
| **Performance** | Minimal overhead, instant detection |
| **Customizable** | Confidence threshold adjustable |

---

**Version:** 1.0  
**Last Updated:** April 2026  
**Status:** Production Ready ✓
