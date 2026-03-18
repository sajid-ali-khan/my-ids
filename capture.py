from scapy.all import sniff, packet
from scapy.layers.inet import IP, TCP, UDP
def get_flow_key(pkt: packet.Packet):
    if not pkt.haslayer(IP):
        return

    proto = pkt[IP].proto
    src_ip, dst_ip = pkt[IP].src, pkt[IP].dst
    
    if pkt.haslayer(TCP):
        src_port, dst_port = pkt[TCP].sport, pkt[TCP].dport
    elif pkt.haslayer(UDP):
        src_port, dst_port = pkt[UDP].sport, pkt[UDP].dport
    else:
        return
    return tuple(sorted([(src_ip, src_port), (dst_ip, dst_port)])) + (proto,)

flows = {}

def process_packet(pkt):
    key = get_flow_key(pkt)
    if not key:
        return
    if key not in flows:
        flows[key] = []
    if len(flows[key]) % 10 == 0:
        print(f'Pckets in the flow, {key}, reached {len(flows[key])} length.')
    flows[key].append(pkt)

print('Starting sniffer...')
sniff(prn = process_packet, store = 0)
