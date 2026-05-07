"""Flow aggregator module for detecting SSH/FTP brute force attacks via pattern analysis.

This module maintains a time-windowed buffer of completed flows grouped by
(src_ip, dst_ip, dst_port) and detects brute force patterns by analyzing
aggregate metrics across flows in that group.
"""

import threading
import time
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple
from datetime import datetime
import numpy as np


@dataclass
class FlowMetrics:
    """Aggregated metrics for a group of flows."""
    src_ip: str
    dst_ip: str
    dst_port: int
    flow_count: int = 0
    durations: List[float] = field(default_factory=list)
    packet_counts: List[int] = field(default_factory=list)
    bytes_counts: List[int] = field(default_factory=list)
    fin_count: int = 0
    rst_count: int = 0
    window_start_time: float = field(default_factory=time.time)
    
    def __post_init__(self):
        """Initialize window start time if not provided."""
        if self.window_start_time == 0:
            self.window_start_time = time.time()
    
    def add_flow(self, duration: float, packet_count: int, bytes_count: int, has_fin: bool, has_rst: bool):
        """Add a flow's metrics to this group."""
        self.durations.append(duration)
        self.packet_counts.append(packet_count)
        self.bytes_counts.append(bytes_count)
        self.fin_count += int(has_fin)
        self.rst_count += int(has_rst)
        self.flow_count += 1
    
    def get_aggregate_features(self) -> Dict[str, float]:
        """Compute aggregate features for this group."""
        if self.flow_count == 0:
            return {}
        
        return {
            'flow_count': float(self.flow_count),
            'avg_duration': float(np.mean(self.durations)) if self.durations else 0.0,
            'min_duration': float(np.min(self.durations)) if self.durations else 0.0,
            'max_duration': float(np.max(self.durations)) if self.durations else 0.0,
            'avg_packet_count': float(np.mean(self.packet_counts)) if self.packet_counts else 0.0,
            'min_packet_count': float(np.min(self.packet_counts)) if self.packet_counts else 0,
            'max_packet_count': float(np.max(self.packet_counts)) if self.packet_counts else 0,
            'avg_bytes': float(np.mean(self.bytes_counts)) if self.bytes_counts else 0.0,
            'min_bytes': float(np.min(self.bytes_counts)) if self.bytes_counts else 0,
            'max_bytes': float(np.max(self.bytes_counts)) if self.bytes_counts else 0,
            'fin_ratio': float(self.fin_count / self.flow_count) if self.flow_count > 0 else 0.0,
            'rst_ratio': float(self.rst_count / self.flow_count) if self.flow_count > 0 else 0.0,
            'connection_rate': float(self.flow_count / max(time.time() - self.window_start_time, 1)),
        }


class FlowAggregator:
    """Detects SSH/FTP brute force using time-windowed flow aggregation.
    
    Maintains a buffer of flows grouped by (src_ip, dst_ip, dst_port) within
    a 60-second time window. When a new flow is added, checks if the group
    meets brute force thresholds and generates alerts.
    """
    
    def __init__(self, time_window: float = 60.0):
        """Initialize flow aggregator.
        
        Args:
            time_window: Time window size in seconds (default: 60)
        """
        self.time_window = time_window
        
        # Thread-safe storage
        self.lock = threading.RLock()
        
        # Buffer: {(src_ip, dst_ip, dst_port, window_start): FlowMetrics}
        self.flow_groups: Dict[Tuple, FlowMetrics] = {}
        
        # Track alerted groups to avoid double-alerting
        # {(src_ip, dst_ip, dst_port, window_start): True}
        self.alerted_groups: set = set()
    
    def add_flow(self, src_ip: str, dst_ip: str, src_port: int, dst_port: int,
                 duration: float, packet_count: int, bytes_count: int,
                 has_fin: bool = False, has_rst: bool = False) -> Optional[Dict]:
        """Add a completed flow and check for brute force patterns.
        
        Args:
            src_ip: Source IP address
            dst_ip: Destination IP address
            src_port: Source port (ignored for grouping)
            dst_port: Destination port
            duration: Flow duration in seconds
            packet_count: Total packets in flow
            bytes_count: Total bytes in flow
            has_fin: Whether flow had FIN flag
            has_rst: Whether flow had RST flag
        
        Returns:
            Alert dict if brute force detected, None otherwise
        """
        with self.lock:
            current_time = time.time()
            
            # Group key (ignoring src_port as per requirements)
            group_key_base = (src_ip, dst_ip, dst_port)
            
            # Find active window for this group
            # Check if there's an existing window within time_window
            active_window_key = None
            for key in list(self.flow_groups.keys()):
                if key[:-1] == group_key_base:  # Same src_ip, dst_ip, dst_port
                    window_start = key[3]
                    if current_time - window_start <= self.time_window:
                        active_window_key = key
                        break
                    else:
                        # Window expired, clean up
                        del self.flow_groups[key]
                        if key in self.alerted_groups:
                            self.alerted_groups.discard(key)
            
            # Create or use existing window
            if active_window_key is None:
                active_window_key = (src_ip, dst_ip, dst_port, int(current_time))
                self.flow_groups[active_window_key] = FlowMetrics(
                    src_ip=src_ip,
                    dst_ip=dst_ip,
                    dst_port=dst_port,
                    window_start_time=current_time
                )
            
            # Add flow to existing window
            metrics = self.flow_groups[active_window_key]
            metrics.add_flow(duration, packet_count, bytes_count, has_fin, has_rst)
            
            # Check for brute force pattern
            alert = self._check_brute_force(metrics, active_window_key)
            
            return alert
    
    def _check_brute_force(self, metrics: FlowMetrics, window_key: Tuple) -> Optional[Dict]:
        """Check if flow group exhibits SSH/FTP brute force pattern.
        
        Thresholds:
        - dst_port in (22, 21) for SSH/FTP
        - flow_count > 10 in 60 seconds
        - avg_duration < 5 seconds
        - avg_packet_count < 20
        
        Args:
            metrics: FlowMetrics for the group
            window_key: Window key for tracking alerts
        
        Returns:
            Alert dict if brute force detected, None otherwise
        """
        # Avoid double-alerting
        if window_key in self.alerted_groups:
            return None
        
        # Check SSH/FTP port
        if metrics.dst_port not in (22, 21):
            return None
        
        agg_features = metrics.get_aggregate_features()
        
        # Apply brute force thresholds
        flow_count = agg_features['flow_count']
        avg_duration = agg_features['avg_duration']
        avg_packet_count = agg_features['avg_packet_count']
        
        # All conditions must be met
        CONDITIONS_MET = (
            flow_count > 10 and
            avg_duration < 5.0 and
            avg_packet_count < 20
        )
        
        if not CONDITIONS_MET:
            return None
        
        # Mark as alerted
        self.alerted_groups.add(window_key)
        
        # Determine attack type
        attack_type = "SSH Brute Force" if metrics.dst_port == 22 else "FTP Brute Force"
        
        # Calculate confidence based on how severe the pattern is
        # More flows, shorter durations, fewer packets → higher confidence
        confidence = min(
            0.95,  # Cap at 0.95
            (flow_count / 20) * 0.4 +  # 40% weight on flow count
            ((5.0 - avg_duration) / 5.0) * 0.3 +  # 30% weight on duration
            ((20 - avg_packet_count) / 20) * 0.3   # 30% weight on packet count
        )
        
        # Generate alert
        alert = {
            'timestamp': datetime.now().isoformat(),
            'attack_type': attack_type,
            'src_ip': metrics.src_ip,
            'dst_ip': metrics.dst_ip,
            'dst_port': metrics.dst_port,
            'prediction': attack_type,  # Use attack type as prediction
            'confidence': float(confidence),
            'is_aggregated': True,  # Flag to distinguish from per-flow predictions
            'aggregate_metrics': agg_features,
            'window_start': datetime.fromtimestamp(metrics.window_start_time).isoformat(),
            'window_end': datetime.now().isoformat(),
            'flow_count': metrics.flow_count,
            'packets': int(agg_features['flow_count']),  # Number of flows
        }
        
        return alert
    
    def cleanup_expired_windows(self):
        """Remove expired windows from the buffer.
        
        Call this periodically to clean up memory.
        """
        with self.lock:
            current_time = time.time()
            expired_keys = []
            
            for key in self.flow_groups.keys():
                window_start = key[3]
                if current_time - window_start > self.time_window:
                    expired_keys.append(key)
            
            for key in expired_keys:
                del self.flow_groups[key]
                if key in self.alerted_groups:
                    self.alerted_groups.discard(key)
    
    def get_active_windows(self) -> List[Dict]:
        """Get information about currently active flow windows.
        
        Returns:
            List of dicts with window info
        """
        with self.lock:
            windows = []
            current_time = time.time()
            
            for key, metrics in self.flow_groups.items():
                window_start = key[3]
                if current_time - window_start <= self.time_window:
                    windows.append({
                        'src_ip': metrics.src_ip,
                        'dst_ip': metrics.dst_ip,
                        'dst_port': metrics.dst_port,
                        'flow_count': metrics.flow_count,
                        'window_age_seconds': current_time - metrics.window_start_time,
                        'aggregate_features': metrics.get_aggregate_features()
                    })
            
            return windows
