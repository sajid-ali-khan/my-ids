# core/flow.py
import numpy as np
from dataclasses import dataclass, field
from typing import List, Tuple
import time

@dataclass
class Flow:
    src_ip: str
    dst_ip: str
    src_port: int
    dst_port: int
    protocol: int
    start_time: float = field(default_factory=time.time)
    last_seen: float = field(default_factory=time.time)

    # raw packet storage: (timestamp, length, direction, flags, ip_header_len, tcp_win, tcp_seg_size)
    # direction: 'fwd' or 'bwd'
    packets: List[Tuple] = field(default_factory=list)

    # initial window sizes — captured from first fwd and bwd packets only
    init_win_fwd: int = 0
    init_win_bwd: int = 0
    init_win_fwd_set: bool = False
    init_win_bwd_set: bool = False

    def add_packet(self, timestamp, length, direction, flags, ip_header_len, tcp_win, tcp_seg_size):
        self.last_seen = timestamp
        self.packets.append((timestamp, length, direction, flags, ip_header_len, tcp_win, tcp_seg_size))

        if direction == 'fwd' and not self.init_win_fwd_set:
            self.init_win_fwd = tcp_win
            self.init_win_fwd_set = True
        if direction == 'bwd' and not self.init_win_bwd_set:
            self.init_win_bwd = tcp_win
            self.init_win_bwd_set = True

    def is_expired(self, idle_timeout=120):
        return (time.time() - self.last_seen) > idle_timeout

    def extract_features(self):
        fwd = [(ts, ln, fl, hl, tw, ts_) for ts, ln, d, fl, hl, tw, ts_ in self.packets if d == 'fwd']
        bwd = [(ts, ln, fl, hl, tw, ts_) for ts, ln, d, fl, hl, tw, ts_ in self.packets if d == 'bwd']

        all_lengths = [ln for _, ln, _, _, _, _, _ in self.packets]
        fwd_lengths = [ln for _, ln, _, _, _, _ in fwd]
        bwd_lengths = [ln for _, ln, _, _, _, _ in bwd]
        all_times   = [ts for ts, _, _, _, _, _, _ in self.packets]
        fwd_times   = [ts for ts, _, _, _, _, _ in fwd]
        bwd_times   = [ts for ts, _, _, _, _, _ in bwd]

        duration = (all_times[-1] - all_times[0]) * 1e6 if len(all_times) > 1 else 0  # microseconds

        def safe_stats(lst):
            if not lst:
                return 0, 0, 0, 0
            return min(lst), max(lst), float(np.mean(lst)), float(np.std(lst))

        def iat(times):
            if len(times) < 2:
                return []
            return [(times[i] - times[i-1]) * 1e6 for i in range(1, len(times))]

        flow_iats = iat(all_times)
        fwd_iats  = iat(fwd_times)
        bwd_iats  = iat(bwd_times)

        f_iat_min, f_iat_max, f_iat_mean, f_iat_std = safe_stats(flow_iats)
        fwd_iat_min, fwd_iat_max, fwd_iat_mean, fwd_iat_std = safe_stats(fwd_iats)
        bwd_iat_min, bwd_iat_max, bwd_iat_mean, bwd_iat_std = safe_stats(bwd_iats)

        pkt_min, pkt_max, pkt_mean, pkt_std = safe_stats(all_lengths)
        fwd_min, fwd_max, fwd_mean, fwd_std = safe_stats(fwd_lengths)
        bwd_min, bwd_max, bwd_mean, bwd_std = safe_stats(bwd_lengths)

        total_bytes = sum(all_lengths)
        fwd_bytes   = sum(fwd_lengths)
        duration_s  = duration / 1e6 if duration > 0 else 1e-6

        fin_count = sum(1 for _, _, _, fl, _, _, _ in self.packets if fl & 0x01)
        psh_count = sum(1 for _, _, _, fl, _, _, _ in self.packets if fl & 0x08)
        ack_count = sum(1 for _, _, _, fl, _, _, _ in self.packets if fl & 0x10)

        fwd_hdr = sum(hl for _, _, _, hl, _, _ in fwd)
        bwd_hdr = sum(hl for _, _, _, hl, _, _ in bwd)

        act_data_pkt_fwd = sum(1 for _, ln, _, _, _, _ in fwd if ln > 0)
        min_seg_fwd = min((ts_ for _, _, _, _, _, ts_ in fwd), default=0)
        avg_pkt_size = float(np.mean(all_lengths)) if all_lengths else 0

        # active/idle — periods where gap > 1s are considered idle
        IDLE_THRESHOLD = 1_000_000  # 1 second in microseconds
        active_times, idle_times = [], []
        if flow_iats:
            current_active = flow_iats[0]
            for iat_val in flow_iats[1:]:
                if iat_val > IDLE_THRESHOLD:
                    active_times.append(current_active)
                    idle_times.append(iat_val)
                    current_active = 0
                else:
                    current_active += iat_val
            active_times.append(current_active)

        act_min, act_max, act_mean, _ = safe_stats(active_times)
        idl_min, idl_max, idl_mean, _ = safe_stats(idle_times)

        return {
            'Destination Port':             self.dst_port,
            'Flow Duration':                duration,
            'Total Fwd Packets':            len(fwd),
            'Total Length of Fwd Packets':  fwd_bytes,
            'Fwd Packet Length Max':        fwd_max,
            'Fwd Packet Length Min':        fwd_min,
            'Fwd Packet Length Mean':       fwd_mean,
            'Fwd Packet Length Std':        fwd_std,
            'Bwd Packet Length Max':        bwd_max,
            'Bwd Packet Length Min':        bwd_min,
            'Bwd Packet Length Mean':       bwd_mean,
            'Bwd Packet Length Std':        bwd_std,
            'Flow Bytes/s':                 total_bytes / duration_s,
            'Flow Packets/s':               len(self.packets) / duration_s,
            'Flow IAT Mean':                f_iat_mean,
            'Flow IAT Std':                 f_iat_std,
            'Flow IAT Max':                 f_iat_max,
            'Flow IAT Min':                 f_iat_min,
            'Fwd IAT Total':                sum(fwd_iats),
            'Fwd IAT Mean':                 fwd_iat_mean,
            'Fwd IAT Std':                  fwd_iat_std,
            'Fwd IAT Max':                  fwd_iat_max,
            'Fwd IAT Min':                  fwd_iat_min,
            'Bwd IAT Total':                sum(bwd_iats),
            'Bwd IAT Mean':                 bwd_iat_mean,
            'Bwd IAT Std':                  bwd_iat_std,
            'Bwd IAT Max':                  bwd_iat_max,
            'Bwd IAT Min':                  bwd_iat_min,
            'Fwd Header Length':            fwd_hdr,
            'Bwd Header Length':            bwd_hdr,
            'Fwd Packets/s':                len(fwd) / duration_s,
            'Bwd Packets/s':                len(bwd) / duration_s,
            'Min Packet Length':            pkt_min,
            'Max Packet Length':            pkt_max,
            'Packet Length Mean':           pkt_mean,
            'Packet Length Std':            pkt_std,
            'Packet Length Variance':       pkt_std ** 2,
            'FIN Flag Count':               fin_count,
            'PSH Flag Count':               psh_count,
            'ACK Flag Count':               ack_count,
            'Average Packet Size':          avg_pkt_size,
            'Subflow Fwd Bytes':            fwd_bytes,
            'Init_Win_bytes_forward':       self.init_win_fwd,
            'Init_Win_bytes_backward':      self.init_win_bwd,
            'act_data_pkt_fwd':             act_data_pkt_fwd,
            'min_seg_size_forward':         min_seg_fwd,
            'Active Mean':                  act_mean,
            'Active Max':                   act_max,
            'Active Min':                   act_min,
            'Idle Mean':                    idl_mean,
            'Idle Max':                     idl_max,
            'Idle Min':                     idl_min,
        }