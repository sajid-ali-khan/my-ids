import joblib
import os
import threading
import queue
import time
import numpy as np
import pandas as pd
from scapy.all import sniff, packet, conf
conf.debug_dissector=2
from scapy.layers.inet import IP, TCP, UDP
from flow import Flow

# ============================================================================
# CONFIGURATION
# ============================================================================
MODEL_PATH = os.path.join(os.path.dirname(__file__), 'model', 'random_forest_model.pkl')
COLUMNS_PATH = os.path.join(os.path.dirname(__file__), 'model', 'model_columns.joblib')
NETWORK_INTERFACE = 'wlp3s0'
FLUSHER_INTERVAL = 20  # seconds
FLOW_IDLE_TIMEOUT = 30  # seconds

# ============================================================================
# LOAD MODEL & FEATURES
# ============================================================================
model = joblib.load(MODEL_PATH)
feature_columns = joblib.load(COLUMNS_PATH)

print("✓ Model loaded.")
print(f'✓ Features expected: {len(feature_columns)}')
print(f'✓ Starting IDS pipeline on interface: {NETWORK_INTERFACE}')
print(f'✓ Flusher interval: {FLUSHER_INTERVAL}s, Idle timeout: {FLOW_IDLE_TIMEOUT}s\n')

# ============================================================================
# SHARED DATA STRUCTURES
# ============================================================================
active_flows = {}  # {flow_key: Flow_object}
flows_lock = threading.Lock()  # Thread-safe access to active_flows
completed_flows_queue = queue.Queue()  # Thread-safe queue for completed flows
stop_event = threading.Event()  # Signal to stop all threads

# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================
def get_flow_key(pkt: packet.Packet):
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


def get_packet_direction(pkt: packet.Packet, flow_key: tuple):
    """Determine packet direction: 'fwd' or 'bwd'."""
    src_ip = pkt[IP].src
    flow_endpoints = flow_key[:-1]  # Remove protocol from key
    
    # flow_key has sorted endpoints: (smaller, larger)
    if (src_ip, pkt[TCP].sport if pkt.haslayer(TCP) else pkt[UDP].sport) == flow_endpoints[0]:
        return 'fwd'
    else:
        return 'bwd'


def extract_tcp_flags(pkt: packet.Packet):
    """Extract TCP flags from packet."""
    if not pkt.haslayer(TCP):
        return 0
    return pkt[TCP].flags


def align_features_to_model(flow_dict: dict, feature_columns: list) -> pd.DataFrame:
    """Reorder flow features to match model's expected column order."""
    aligned = []
    for col in feature_columns:
        aligned.append(flow_dict.get(col, 0))  # Default to 0 if feature missing
    return pd.DataFrame([aligned], columns=feature_columns)  # Return DataFrame with column names


# ============================================================================
# THREAD 1: SNIFFER (Producer)
# ============================================================================
def sniffer_thread():
    """Capture packets, group into flows, detect TCP completion."""
    print(f"[SNIFFER] Starting packet capture on {NETWORK_INTERFACE}...")
    
    def process_packet(pkt):
        if stop_event.is_set():
            return
            
        flow_key = get_flow_key(pkt)
        if not flow_key:
            return
        
        with flows_lock:
            if flow_key not in active_flows:
                src_ip, src_port = flow_key[0]
                dst_ip, dst_port = flow_key[1]
                proto = flow_key[2]
                active_flows[flow_key] = Flow(src_ip, dst_ip, src_port, dst_port, proto)
            
            flow = active_flows[flow_key]
            timestamp = time.time()
            length = len(pkt)
            direction = get_packet_direction(pkt, flow_key)
            flags = extract_tcp_flags(pkt)
            ip_header_len = pkt[IP].ihl * 4 if pkt.haslayer(IP) else 0
            tcp_win = pkt[TCP].window if pkt.haslayer(TCP) else 0
            tcp_seg_size = len(pkt[TCP].payload) if pkt.haslayer(TCP) and pkt[TCP].payload else 0
            
            flow.add_packet(timestamp, length, direction, flags, ip_header_len, tcp_win, tcp_seg_size)
            
            if pkt.haslayer(TCP) and (flags & 0x01 or flags & 0x04):
                print(f"[SNIFFER] TCP {['FIN', 'RST'][bool(flags & 0x04)]} detected: {flow_key}")
                completed_flows_queue.put((flow_key, flow))
                del active_flows[flow_key]
    
    try:
        sniff(iface=NETWORK_INTERFACE, prn=process_packet, store=0, stop_filter = lambda x: stop_event.is_set())
    except KeyboardInterrupt:
        pass
    except Exception as e:
        print(f"[SNIFFER] Error: {e}")
    
    print("[SNIFFER] Stopped.")

# ============================================================================
# THREAD 2: FLUSHER (Producer)
# ============================================================================
def flusher_thread():
    """Periodically check for idle flows and move them to queue."""
    print(f"[FLUSHER] Starting (interval={FLUSHER_INTERVAL}s, timeout={FLOW_IDLE_TIMEOUT}s)")
    
    while not stop_event.is_set():
        time.sleep(FLUSHER_INTERVAL)
        
        with flows_lock:
            expired_keys = [key for key, flow in active_flows.items() if flow.is_expired(FLOW_IDLE_TIMEOUT)]
        
        for key in expired_keys:
            print(f"[FLUSHER] Flow timed out: {key}")
            with flows_lock:
                if key in active_flows:
                    flow = active_flows[key]
                    completed_flows_queue.put((key, flow))
                    del active_flows[key]
    
    print("[FLUSHER] Stopped.")


# ============================================================================
# THREAD 3: CLASSIFIER (Consumer)
# ============================================================================
def classifier_thread():
    """Consume completed flows, extract features, and classify."""
    print("[CLASSIFIER] Started")
    
    while not stop_event.is_set() or not completed_flows_queue.empty():
        try:flow_key, flow = completed_flows_queue.get(timeout=1)
        except queue.Empty:
            continue
        
        # Extract features from flow
        features_dict = flow.extract_features()
        features_aligned = align_features_to_model(features_dict, feature_columns)
        
        # Make prediction
        prediction = model.predict(features_aligned)[0]
        probabilities = model.predict_proba(features_aligned)[0]
        
        # Output result
        print(f"\n[CLASSIFIER] " + "="*60)
        print(f"Flow Key: {flow_key}")
        print(f"Src: {flow.src_ip}:{flow.src_port} -> Dst: {flow.dst_ip}:{flow.dst_port}")
        print(f"Prediction: {prediction}")
        print(f"Confidence: {max(probabilities):.4f}")
        print(f"Probabilities: {probabilities}")
        print(f"Packets: {len(flow.packets)} total")
        print(f"[CLASSIFIER] Processing: {flow_key}")
    
    print("[CLASSIFIER] Stopped.")


# ============================================================================
# MAIN
# ============================================================================
if __name__ == '__main__':
    # Start threads
    sniffer = threading.Thread(target=sniffer_thread, daemon=False)
    flusher = threading.Thread(target=flusher_thread, daemon=False)
    classifier = threading.Thread(target=classifier_thread, daemon=False)
    
    try:
        sniffer.start()
        flusher.start()
        classifier.start()
        
        # Keep main thread alive
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n[MAIN] Stopping all threads...")
        stop_event.set()
        
        sniffer.join(timeout=5)
        flusher.join(timeout=5)
        classifier.join(timeout=5)
        
        print("[MAIN] All threads stopped.")
