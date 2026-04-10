"""Core IDS Pipeline Manager - Thread-safe pipeline orchestration"""

import threading
import queue
import time
from collections import deque
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple

import pandas as pd
from scapy.all import sniff, packet, conf
from scapy.layers.inet import IP, TCP, UDP

# Import Flow from project root (works with pipx installation)
import sys
from pathlib import Path
_project_root = Path(__file__).parent.parent
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))


from flow import Flow
from .model_loader import load_model_and_features
from .flow_aggregator import FlowAggregator
from .store import init_db, save_alert, get_alerts, get_alert_stats, is_ip_whitelisted

# Disable Scapy debug output
conf.debug_dissector = 0


class PipelineManager:
    """Manages the multi-threaded IDS pipeline.
    
    Orchestrates:
    - Sniffer thread: Captures packets, groups into flows
    - Flusher thread: Detects idle/timeout flows
    - Classifier thread: Extracts features, runs predictions
    
    Thread-safe data access for external APIs.
    """
    
    def __init__(self, model_dir: str, network_interface: str = 'wlp3s0',
                 flusher_interval: int = 20, idle_timeout: int = 30,
                 max_history: int = 100):
        """Initialize PipelineManager.
        
        Args:
            model_dir: Path to model directory (contains .pkl and .joblib files)
            network_interface: Network interface to sniff on (e.g., 'wlp3s0')
            flusher_interval: Time between idle flow checks (seconds)
            idle_timeout: Flow idle timeout (seconds)
            max_history: Max predictions to keep in history
        """
        # Configuration
        self.network_interface = network_interface
        self.flusher_interval = flusher_interval
        self.idle_timeout = idle_timeout
        self.max_history = max_history
        
        # Load model and features (v2 preferred for real-world traffic)
        self.model, self.feature_columns, self.is_model_v2 = load_model_and_features(model_dir, use_v2=True)
        
        # Thread management
        self.threads = {}
        self.stop_event = threading.Event()
        self.is_running = False
        
        # Thread-safe shared data structures
        self.flows_lock = threading.RLock()
        self.active_flows = {}  # {flow_key: Flow_object}
        
        self.history_lock = threading.RLock()
        self.predictions_history = deque(maxlen=max_history)  # Recent predictions
        
        self.stats_lock = threading.RLock()
        self.stats = {
            'total_predictions': 0,
            'benign': 0,
            'class_counts': {}  # {class_name: count}
        }
        
        # Queue for completed flows
        self.completed_flows_queue = queue.Queue()
        
        # Flow aggregator for detecting SSH/FTP brute force
        self.flow_aggregator = FlowAggregator(time_window=60.0)
        
        # Initialize SQLite database for persistent alert storage
        try:
            init_db()
            self.db_enabled = True
        except Exception as e:
            print(f"⚠️  Database initialization failed: {e}")
            self.db_enabled = False
        
        print(f"✓ PipelineManager initialized")
        print(f"  - Model: {'v2 (optimized for real traffic)' if self.is_model_v2 else 'v1 (legacy)'}")
        print(f"  - Interface: {network_interface}")
        print(f"  - Model features: {len(self.feature_columns)}")
        print(f"  - Flusher interval: {flusher_interval}s")
        print(f"  - Idle timeout: {idle_timeout}s")
        print(f"  - Flow aggregation: Enabled (SSH/FTP brute force detection)")
        print(f"  - Database: {'Enabled (/opt/nids/alerts.db)' if self.db_enabled else 'Disabled'}")
    
    # ========================================================================
    # PUBLIC API - CONTROL METHODS
    # ========================================================================
    
    def start(self):
        """Start the pipeline (all threads)."""
        if self.is_running:
            print("[PIPELINE] Already running")
            return
        
        self.stop_event.clear()
        self.is_running = True
        
        # Start threads
        self.threads['sniffer'] = threading.Thread(target=self._sniffer_thread, daemon=True)
        self.threads['flusher'] = threading.Thread(target=self._flusher_thread, daemon=True)
        self.threads['classifier'] = threading.Thread(target=self._classifier_thread, daemon=True)
        
        for thread in self.threads.values():
            thread.start()
        
        print("[PIPELINE] Started all threads")
    
    def stop(self):
        """Stop the pipeline gracefully (all threads)."""
        if not self.is_running:
            print("[PIPELINE] Already stopped")
            return
        
        print("[PIPELINE] Stopping all threads...")
        self.stop_event.set()
        
        # Wait for threads to finish
        for name, thread in self.threads.items():
            if thread.is_alive():
                thread.join(timeout=5)
                if thread.is_alive():
                    print(f"[PIPELINE] Warning: {name} thread still alive after timeout")
        
        self.is_running = False
        print("[PIPELINE] All threads stopped")
    
    # ========================================================================
    # PUBLIC API - DATA ACCESS METHODS
    # ========================================================================
    
    def get_status(self) -> Dict[str, Any]:
        """Get pipeline status.
        
        Returns:
            dict: {
                'running': bool,
                'active_flows': int,
                'predictions_processed': int,
                'interface': str
            }
        """
        with self.flows_lock:
            active_count = len(self.active_flows)
        
        with self.stats_lock:
            total_preds = self.stats['total_predictions']
        
        return {
            'running': self.is_running,
            'active_flows': active_count,
            'predictions_processed': total_preds,
            'interface': self.network_interface
        }
    
    def get_predictions(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get recent predictions.
        
        Args:
            limit: Max predictions to return
            
        Returns:
            list: Recent predictions with metadata
        """
        with self.history_lock:
            preds = list(self.predictions_history)[-limit:]
        
        return preds
    
    def get_stats(self) -> Dict[str, Any]:
        """Get pipeline statistics.
        
        Returns:
            dict: {
                'total': int,
                'benign': int,
                'by_class': {class_name: count, ...}
            }
        """
        with self.stats_lock:
            return {
                'total': self.stats['total_predictions'],
                'benign': self.stats['benign'],
                'by_class': self.stats['class_counts'].copy()
            }
    
    def get_active_flows(self) -> List[Dict[str, Any]]:
        """Get currently active flows.
        
        Returns:
            list: Active flow info
        """
        with self.flows_lock:
            flows = []
            for flow_key, flow in self.active_flows.items():
                flows.append({
                    'flow_key': str(flow_key),
                    'src_ip': flow.src_ip,
                    'src_port': flow.src_port,
                    'dst_ip': flow.dst_ip,
                    'dst_port': flow.dst_port,
                    'packets': len(flow.packets),
                    'active_time': time.time() - flow.start_time
                })
        
        return flows
    
    def get_aggregation_windows(self) -> List[Dict[str, Any]]:
        """Get information about active flow aggregation windows.
        
        Used for monitoring SSH/FTP brute force detection progress.
        
        Returns:
            list: Active aggregation window info
        """
        return self.flow_aggregator.get_active_windows()
    
    def get_persistent_alerts(self, limit: int = 50, severity: Optional[str] = None,
                             attack_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get persistent alerts from SQLite database.
        
        Args:
            limit: Maximum alerts to return
            severity: Filter by severity ('critical', 'high', 'medium', 'low')
            attack_type: Filter by attack type
            
        Returns:
            list: Alert records from database
        """
        if not self.db_enabled:
            return []
        
        return get_alerts(limit=limit, severity=severity, attack_type=attack_type)
    
    def get_persistent_alert_stats(self) -> Dict[str, Any]:
        """Get statistics about persistent alerts from database.
        
        Returns:
            dict: Alert statistics
        """
        if not self.db_enabled:
            return {
                'total_alerts': 0,
                'by_severity': {},
                'by_attack_type': {},
                'critical_count': 0,
                'high_count': 0,
                'acknowledged_count': 0,
                'today_count': 0
            }
        
        return get_alert_stats()
    
    def _is_suspicious_traffic(self, prediction: str, confidence: float) -> bool:
        """Check if traffic is suspicious (normal/benign with low confidence).
        
        Args:
            prediction: Class prediction
            confidence: Confidence score
            
        Returns:
            bool: True if suspicious
        """
        is_benign = prediction == 'Benign' or prediction == 'Normal Traffic'
        is_low_confidence = confidence < 0.91
        return is_benign and is_low_confidence
    
    def _save_alert_if_attack(self, pred_record: Dict[str, Any], 
                             flow: 'Flow', prediction: str, 
                             confidence: float) -> bool:
        """Save alert to database if prediction is an attack or suspicious.
        
        Saves two types of alerts:
        1. Regular attacks (confidently identified malicious traffic)
        2. Suspicious traffic (normal traffic classified with low confidence)
        
        Args:
            pred_record: Prediction record (has metadata)
            flow: Flow object
            prediction: Class prediction
            confidence: Confidence score
            
        Returns:
            bool: True if alert was saved
        """
        if not self.db_enabled:
            return False
        
        # Check for suspicious traffic (normal/benign with low confidence)
        is_suspicious = self._is_suspicious_traffic(prediction, confidence)
        
        # Determine if this should be saved
        is_attack = not (prediction == 'Benign' or prediction == 'Normal Traffic')
        
        if not (is_attack or is_suspicious):
            return False
        
        # Check whitelist
        if is_ip_whitelisted(flow.src_ip):
            return False
        
        # Determine severity based on confidence and prediction
        if is_suspicious:
            # Suspicious traffic is always marked as low severity
            severity = 'low'
            attack_type = 'Suspicious'
        else:
            # Regular attack severity determination
            if confidence >= 0.9:
                severity = 'critical'
            elif confidence >= 0.75:
                severity = 'high'
            elif confidence >= 0.6:
                severity = 'medium'
            else:
                severity = 'low'
            attack_type = prediction
        
        alert_dict = {
            'timestamp': time.time(),
            'src_ip': flow.src_ip,
            'dst_ip': flow.dst_ip,
            'src_port': flow.src_port,
            'dst_port': flow.dst_port,
            'protocol': flow.protocol,
            'attack_type': attack_type,
            'confidence': confidence,
            'severity': severity,
            'is_aggregated': 0,
            'flow_count': 1
        }
        
        try:
            save_alert(alert_dict)
            if is_suspicious:
                print(f"[DB] ⚠️  Saved SUSPICIOUS alert: {flow.src_ip}:{flow.src_port} -> {flow.dst_ip}:{flow.dst_port} (confidence: {confidence:.2%})")
            else:
                print(f"[DB] ✓ Saved attack alert: {attack_type}")
            return True
        except Exception as e:
            print(f"[DB] Error saving alert: {e}")
            return False
    
    def _save_aggregated_alert(self, aggregated_alert: Dict[str, Any]) -> bool:
        """Save aggregated alert (brute force) to database.
        
        Args:
            aggregated_alert: Alert from flow aggregator
            
        Returns:
            bool: True if alert was saved
        """
        if not self.db_enabled:
            return False
        
        # Check whitelist
        if is_ip_whitelisted(aggregated_alert['src_ip']):
            return False
        
        # Determine severity
        confidence = aggregated_alert['confidence']
        if confidence >= 0.9:
            severity = 'critical'
        elif confidence >= 0.75:
            severity = 'high'
        else:
            severity = 'medium'
        
        alert_dict = {
            'timestamp': time.time(),
            'src_ip': aggregated_alert['src_ip'],
            'dst_ip': aggregated_alert['dst_ip'],
            'src_port': 0,  # Not applicable for aggregate
            'dst_port': aggregated_alert['dst_port'],
            'protocol': 6,  # TCP (typically brute force)
            'attack_type': aggregated_alert['attack_type'],
            'confidence': confidence,
            'severity': severity,
            'is_aggregated': 1,
            'flow_count': aggregated_alert.get('flow_count', 1)
        }
        
        try:
            save_alert(alert_dict)
            return True
        except Exception as e:
            print(f"[DB] Error saving aggregated alert: {e}")
            return False
    
    # ========================================================================
    # PRIVATE - UTILITY FUNCTIONS
    # ========================================================================
    
    def _get_flow_key(self, pkt: packet.Packet) -> Optional[Tuple]:
        """Generate bidirectional flow key from packet."""
        if not pkt.haslayer(IP):
            return None
        
        proto = pkt[IP].proto
        src_ip, dst_ip = pkt[IP].src, pkt[IP].dst
        
        if pkt.haslayer(TCP):
            src_port, dst_port = pkt[TCP].sport, pkt[TCP].dport
        elif pkt.haslayer(UDP):
            src_port, dst_port = pkt[UDP].sport, pkt[UDP].dport
        else:
            return None
        
        return tuple(sorted([(src_ip, src_port), (dst_ip, dst_port)])) + (proto,)
    
    def _get_packet_direction(self, pkt: packet.Packet, flow_key: tuple) -> str:
        """Determine packet direction: 'fwd' or 'bwd'."""
        src_ip = pkt[IP].src
        flow_endpoints = flow_key[:-1]
        
        if (src_ip, pkt[TCP].sport if pkt.haslayer(TCP) else pkt[UDP].sport) == flow_endpoints[0]:
            return 'fwd'
        else:
            return 'bwd'
    
    def _extract_tcp_flags(self, pkt: packet.Packet) -> int:
        """Extract TCP flags from packet."""
        if not pkt.haslayer(TCP):
            return 0
        return pkt[TCP].flags
    
    def _align_features_to_model(self, flow_dict: dict) -> pd.DataFrame:
        """Reorder flow features to match model's expected column order."""
        aligned = []
        for col in self.feature_columns:
            aligned.append(flow_dict.get(col, 0))
        
        return pd.DataFrame([aligned], columns=self.feature_columns)
    
    def _update_stats(self, prediction: str):
        """Update statistics with prediction result."""
        with self.stats_lock:
            self.stats['total_predictions'] += 1
            
            if prediction == 'Normal Traffic':
                self.stats['benign'] += 1
            
            if prediction not in self.stats['class_counts']:
                self.stats['class_counts'][prediction] = 0
            self.stats['class_counts'][prediction] += 1
    
    # ========================================================================
    # PRIVATE - THREAD FUNCTIONS
    # ========================================================================
    
    def _sniffer_thread(self):
        """Capture packets, group into flows, detect TCP completion."""
        print(f"[SNIFFER] Starting packet capture on {self.network_interface}...")
        
        def process_packet(pkt):
            if self.stop_event.is_set():
                return
            
            flow_key = self._get_flow_key(pkt)
            if not flow_key:
                return
            
            with self.flows_lock:
                # Create or update flow
                if flow_key not in self.active_flows:
                    src_ip, src_port = flow_key[0]
                    dst_ip, dst_port = flow_key[1]
                    proto = flow_key[2]
                    self.active_flows[flow_key] = Flow(src_ip, dst_ip, src_port, dst_port, proto)
                
                flow = self.active_flows[flow_key]
                
                # Extract packet info
                timestamp = time.time()
                length = len(pkt)
                direction = self._get_packet_direction(pkt, flow_key)
                flags = self._extract_tcp_flags(pkt)
                ip_header_len = pkt[IP].ihl * 4 if pkt.haslayer(IP) else 0
                tcp_win = pkt[TCP].window if pkt.haslayer(TCP) else 0
                tcp_seg_size = len(pkt[TCP].payload) if pkt.haslayer(TCP) and pkt[TCP].payload else 0
                
                # Add packet to flow
                flow.add_packet(timestamp, length, direction, flags, ip_header_len, tcp_win, tcp_seg_size)
                
                # Check for TCP FIN/RST (flow completion)
                if pkt.haslayer(TCP) and (flags & 0x01 or flags & 0x04):  # FIN or RST
                    self.completed_flows_queue.put((flow_key, flow))
                    del self.active_flows[flow_key]
        
        try:
            sniff(iface=self.network_interface, prn=process_packet, store=0,
                  stop_filter=lambda x: self.stop_event.is_set())
        except KeyboardInterrupt:
            pass
        except Exception as e:
            print(f"[SNIFFER] Error: {e}")
        
        print("[SNIFFER] Stopped.")
    
    def _flusher_thread(self):
        """Periodically check for idle flows and move them to queue."""
        print(f"[FLUSHER] Starting (interval={self.flusher_interval}s, timeout={self.idle_timeout}s)")
        
        while not self.stop_event.is_set():
            time.sleep(self.flusher_interval)
            
            with self.flows_lock:
                expired_keys = [key for key, flow in self.active_flows.items()
                               if flow.is_expired(self.idle_timeout)]
            
            for key in expired_keys:
                with self.flows_lock:
                    if key in self.active_flows:
                        flow = self.active_flows[key]
                        self.completed_flows_queue.put((key, flow))
                        del self.active_flows[key]
            
            # Periodically cleanup expired aggregation windows
            self.flow_aggregator.cleanup_expired_windows()
        
        print("[FLUSHER] Stopped.")
    
    def _classifier_thread(self):
        """Consume completed flows, extract features, and classify."""
        print("[CLASSIFIER] Started")
        
        while not self.stop_event.is_set() or not self.completed_flows_queue.empty():
            try:
                flow_key, flow = self.completed_flows_queue.get(timeout=1)
            except queue.Empty:
                continue
            
            # Extract features from flow
            features_dict = flow.extract_features()
            features_aligned = self._align_features_to_model(features_dict)
            
            # Make prediction
            prediction = self.model.predict(features_aligned)[0]
            probabilities = self.model.predict_proba(features_aligned)[0]
            
            # Store in history
            pred_record = {
                'timestamp': datetime.now().isoformat(),
                'flow_key': str(flow_key),
                'src_ip': flow.src_ip,
                'src_port': flow.src_port,
                'dst_ip': flow.dst_ip,
                'dst_port': flow.dst_port,
                'prediction': prediction,
                'confidence': float(max(probabilities)),
                'packets': len(flow.packets)
            }
            
            with self.history_lock:
                self.predictions_history.append(pred_record)
            
            # Update stats
            self._update_stats(prediction)
            
            # Check for suspicious traffic
            confidence_val = float(max(probabilities))
            is_suspicious = self._is_suspicious_traffic(prediction, confidence_val)
            
            # Console output
            print(f"\n[CLASSIFIER] {'='*60}")
            if is_suspicious:
                print(f"⚠️  SUSPICIOUS TRAFFIC (normal/benign with low confidence)")
            print(f"Prediction: {prediction}")
            print(f"Confidence: {confidence_val:.4f}")
            print(f"Flow: {flow.src_ip}:{flow.src_port} -> {flow.dst_ip}:{flow.dst_port}")
            print(f"Packets: {len(flow.packets)}")
            print(f"{'='*60}")
            
            # Save attack to persistent database (attacks only, benign with low confidence)
            self._save_alert_if_attack(pred_record, flow, prediction, confidence_val)
            
            # Pass flow to aggregator for brute force detection
            flow_duration = flow.last_seen - flow.start_time
            has_fin = any(flags & 0x01 for _, _, _, flags, _, _, _ in flow.packets)
            has_rst = any(flags & 0x04 for _, _, _, flags, _, _, _ in flow.packets)
            total_bytes = sum(length for _, length, _, _, _, _, _ in flow.packets)
            
            aggregated_alert = self.flow_aggregator.add_flow(
                src_ip=flow.src_ip,
                dst_ip=flow.dst_ip,
                src_port=flow.src_port,
                dst_port=flow.dst_port,
                duration=flow_duration,
                packet_count=len(flow.packets),
                bytes_count=total_bytes,
                has_fin=has_fin,
                has_rst=has_rst
            )
            
            # If brute force detected, add to history
            if aggregated_alert:
                with self.history_lock:
                    self.predictions_history.append(aggregated_alert)
                
                # Update stats for aggregated alert
                self._update_stats(aggregated_alert['prediction'])
                
                # Save aggregated alert to persistent database
                self._save_aggregated_alert(aggregated_alert)
                
                # Console output for brute force alert
                print(f"\n[AGGREGATOR] {'*'*60}")
                print(f"🚨 {aggregated_alert['attack_type']} DETECTED")
                print(f"Source IP: {aggregated_alert['src_ip']}")
                print(f"Target: {aggregated_alert['dst_ip']}:{aggregated_alert['dst_port']}")
                print(f"Flows in window: {aggregated_alert['flow_count']}")
                print(f"Confidence: {aggregated_alert['confidence']:.4f}")
                print(f"Window: {aggregated_alert['window_start']} -> {aggregated_alert['window_end']}")
                print(f"Aggregate metrics:")
                for key, value in aggregated_alert['aggregate_metrics'].items():
                    if isinstance(value, float):
                        print(f"  {key}: {value:.2f}")
                    else:
                        print(f"  {key}: {value}")
                print(f"{'*'*60}\n")
        
        print("[CLASSIFIER] Stopped.")
