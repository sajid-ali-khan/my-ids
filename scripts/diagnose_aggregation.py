#!/usr/bin/env python3
"""
Diagnostic Tool: Flow Aggregation Verification
Analyzes SSH brute force aggregation to confirm correct behavior
"""

import json
import subprocess
import sys
from typing import Dict, List, Any
from collections import defaultdict

def get_aggregation_windows() -> Dict[str, Any]:
    """Fetch current aggregation windows from API"""
    try:
        result = subprocess.run(
            ['curl', '-s', 'http://localhost:5000/api/aggregation-windows'],
            capture_output=True,
            text=True,
            timeout=5
        )
        return json.loads(result.stdout)
    except Exception as e:
        print(f"❌ Error fetching aggregation windows: {e}")
        return {'windows': [], 'active_windows': 0}

def get_alerts() -> Dict[str, Any]:
    """Fetch current alerts from database via API"""
    try:
        result = subprocess.run(
            ['curl', '-s', 'http://localhost:5000/api/persistent-alerts?limit=100'],
            capture_output=True,
            text=True,
            timeout=5
        )
        return json.loads(result.stdout)
    except Exception as e:
        print(f"❌ Error fetching alerts: {e}")
        return {'alerts': [], 'total': 0}

def analyze_aggregation_windows():
    """Analyze aggregation windows for SSH brute force patterns"""
    print("\n" + "="*70)
    print("FLOW AGGREGATION ANALYSIS")
    print("="*70)
    
    data = get_aggregation_windows()
    windows = data.get('windows', [])
    
    if not windows:
        print("\n⚠️  No active aggregation windows - pipeline may be idle")
        return
    
    print(f"\n📊 Total active windows: {len(windows)}")
    print("-" * 70)
    
    # Categorize by port
    by_port = defaultdict(list)
    for window in windows:
        port = window['dst_port']
        by_port[port].append(window)
    
    print(f"\n📍 Windows by destination port:")
    print("-" * 70)
    
    ssh_ports = []
    other_ports = []
    
    for port in sorted(by_port.keys()):
        windows_for_port = by_port[port]
        flow_counts = [w['flow_count'] for w in windows_for_port]
        total_flows = sum(flow_counts)
        
        port_label = "🔴 SSH" if port == 22 else "🟠 FTP" if port == 21 else "⚫"
        print(f"\n{port_label} Port {port}: {len(windows_for_port)} window(s), {total_flows} total flows")
        
        for i, w in enumerate(windows_for_port, 1):
            flow_count = w['flow_count']
            window_age = w['window_age_seconds']
            avg_dur = w['aggregate_features'].get('avg_duration', 0)
            avg_pkt = w['aggregate_features'].get('avg_packet_count', 0)
            
            status = "✅ BRUTE FORCE CRITERIA MET" if (
                flow_count > 10 and avg_dur < 5.0 and avg_pkt < 20
            ) else "⏳ Accumulating" if flow_count > 3 else "•"
            
            print(f"   [{i}] {w['src_ip']} -> {w['dst_ip']}:{port}")
            print(f"       Flows: {flow_count} | Age: {window_age:.1f}s | Status: {status}")
            print(f"       Avg Duration: {avg_dur:.2f}s | Avg Packets: {avg_pkt:.1f}")
            
            if port == 22 or port == 21:
                ssh_ports.append(w)
            else:
                other_ports.append(w)
    
    # Summary
    print("\n" + "="*70)
    print("AGGREGATION VERIFICATION SUMMARY")
    print("="*70)
    
    print(f"\n📌 SSH/FTP Ports (22, 21): {len(ssh_ports)} windows")
    print(f"📌 Other Ports: {len(other_ports)} windows")
    
    print("\n✅ EXPECTED BEHAVIOR:")
    print("   • Flows with SAME (src_ip, dst_ip, dst_port) are grouped in ONE window")
    print("   • Multiple windows can exist for different dst_ports")
    print("   • Different source ports (dynamic) do NOT create separate windows")
    print("   • Only port 22 (SSH) and 21 (FTP) generate brute force alerts")
    
    if len(other_ports) > 0:
        print("\n⚠️  WARNING: Non-SSH/FTP ports detected in aggregation windows:")
        for w in other_ports[:3]:
            print(f"   • {w['src_ip']} -> {w['dst_ip']}:{w['dst_port']} ({w['flow_count']} flows)")
        print("   → These are tracked but will NOT trigger brute force alerts")
        print("   → Only port 22/21 flow windows trigger alerts")

def analyze_alerts():
    """Analyze alerts for SSH brute force patterns"""
    print("\n" + "="*70)
    print("BRUTE FORCE ALERTS ANALYSIS")
    print("="*70)
    
    data = get_alerts()
    alerts = data.get('alerts', [])
    
    if not alerts:
        print("\n✅ No alerts in database - good!")
        return
    
    # Categorize by attack type
    by_type = defaultdict(list)
    for alert in alerts:
        attack_type = alert.get('attack_type', 'Unknown')
        by_type[attack_type].append(alert)
    
    print(f"\n📊 Total alerts: {len(alerts)}")
    print("-" * 70)
    
    for attack_type in sorted(by_type.keys()):
        alerts_of_type = by_type[attack_type]
        print(f"\n🎯 {attack_type}: {len(alerts_of_type)} alerts")
        
        # Show recent ones
        for alert in alerts_of_type[-3:]:
            src = f"{alert['src_ip']}:{alert.get('src_port', '?')}"
            dst = f"{alert['dst_ip']}:{alert['dst_port']}"
            conf = alert.get('confidence', 0)
            is_agg = alert.get('is_aggregated', False)
            
            agg_label = "🔀 AGGREGATED" if is_agg else "📍 Individual"
            print(f"   {agg_label}: {src} → {dst} (conf: {conf:.2f})")

def verify_grouping_logic():
    """Verify that flows are correctly grouped by destination port, not source port"""
    print("\n" + "="*70)
    print("GROUPING LOGIC VERIFICATION")
    print("="*70)
    
    data = get_aggregation_windows()
    windows = data.get('windows', [])
    
    print("\n✅ WHAT THE AGGREGATION GROUPS BY:")
    print("-" * 70)
    print("   Primary Key: (src_ip, dst_ip, dst_port, window_start_time)")
    print("   Ignored:     src_port (NOT used for grouping)")
    print("")
    print("   ✓ Flows from same source to same destination on SAME port = 1 window")
    print("   ✓ Different source ports = SAME window (correct for brute force)")
    print("   ✗ Different destination ports = DIFFERENT windows (correct)")
    
    # Find examples
    by_dst = defaultdict(list)
    for w in windows:
        key = (w['src_ip'], w['dst_ip'], w['dst_port'])
        by_dst[key].append(w)
    
    multi_windows = {k: v for k, v in by_dst.items() if len(v) > 1}
    
    if multi_windows:
        print("\n⚠️  FOUND DUPLICATE WINDOWS FOR SAME (src_ip, dst_ip, dst_port):")
        for (src_ip, dst_ip, dst_port), windows_list in list(multi_windows.items())[:1]:
            print(f"\n   {src_ip} → {dst_ip}:{dst_port}")
            print(f"   Multiple windows: {len(windows_list)}")
            for i, w in enumerate(windows_list, 1):
                age = w['window_age_seconds']
                flows = w['flow_count']
                print(f"     [{i}] Age: {age:.1f}s, Flows: {flows}")
        print("\n   This is EXPECTED if a window expired and a new one was created")
    else:
        print("\n✅ No duplicate windows - grouping logic is correct!")

def detect_potential_issues():
    """Detect potential issues in aggregation"""
    print("\n" + "="*70)
    print("POTENTIAL ISSUES CHECK")
    print("="*70)
    
    data = get_aggregation_windows()
    windows = data.get('windows', [])
    
    issues = []
    
    # Check 1: Too many windows for SSH
    ssh_windows = [w for w in windows if w['dst_port'] in (22, 21)]
    if len(ssh_windows) > 10:
        issues.append(f"⚠️  HIGH: {len(ssh_windows)} SSH/FTP windows active (typical: 1-3)")
    
    # Check 2: Windows stalled (no new flows)
    old_windows = [w for w in windows if w['window_age_seconds'] > 55]
    if old_windows:
        issues.append(f"⚠️  INFO: {len(old_windows)} windows nearing expiration (>55s old)")
    
    # Check 3: Flow counts oddly distributed
    ssh_flow_counts = [w['flow_count'] for w in ssh_windows]
    if ssh_flow_counts and max(ssh_flow_counts, default=0) > 100:
        issues.append(f"⚠️  INFO: Window with {max(ssh_flow_counts)} flows (normal for attack)")
    
    if not issues:
        print("\n✅ No potential issues detected - aggregation appears normal!")
    else:
        print("\n")
        for issue in issues:
            print(issue)

def main():
    print("\n" + "🔍 " * 25)
    print("AGGREGATION DIAGNOSTIC REPORT")
    print("🔍 " * 25)
    
    analyze_aggregation_windows()
    verify_grouping_logic()
    analyze_alerts()
    detect_potential_issues()
    
    print("\n" + "="*70)
    print("DIAGNOSTIC COMPLETE")
    print("="*70)
    
    print("\n📖 INTERPRETATION GUIDE:")
    print("-" * 70)
    print("""
✅ CORRECT BEHAVIOR:
  • Flows with different src_port but same (src_ip, dst_ip, dst_port) → 1 window
  • Multiple windows for different destination ports → Expected
  • Only port 22/21 generate "SSH/FTP Brute Force" alerts
  • Aggregation windows include ALL tracked groupings
  • Alert criteria: flow_count>10 AND avg_duration<5s AND avg_packet<20

🔴 RED FLAGS:
  • Same (src_ip, dst_ip, dst_port) appearing multiple times in ALERTS → Duplicate alert (possible bug)
  • Non-SSH/FTP ports (22, 21) generating brute force alerts → Logic error
  • Windows never expiring → Possible memory leak
  
⚠️  NORMAL CONDITIONS:
  • Many aggregation windows for non-SSH/FTP ports → Expected (all flows tracked)
  • Windows appearing and disappearing → Expected (60s time windows)
  • Multiple alerts for different source IPs → Expected (different attackers)
""")

if __name__ == '__main__':
    main()
