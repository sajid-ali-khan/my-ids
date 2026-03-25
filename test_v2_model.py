#!/usr/bin/env python3
"""Test v2 model on live traffic and SSH brute-force detection."""

import subprocess
import time
import json
import requests
import sys

def run_test():
    """Run comprehensive model testing."""
    
    print("="*80)
    print("TESTING V2 MODEL - SSH BRUTE-FORCE DETECTION")
    print("="*80)
    
    # 1. Start server (requires sudo for packet capture)
    print("\n[1] Starting IDS server (requires sudo)...")
    server_proc = subprocess.Popen(
        ["sudo", "python3", "run_server.py"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        cwd="/home/sajid/Desktop/fyp"
    )
    time.sleep(5)  # Wait longer for server to start
    
    try:
        # 2. Verify server is running
        print("[2] Verifying server...")
        response = requests.post("http://localhost:5000/api/start")
        if response.status_code == 200:
            print("    ✓ Server started and pipeline activatedwait a moment...")
        else:
            print(f"    ✗ Failed to start pipeline: {response.text}")
            return
            
        time.sleep(2)
        
        # 3. Generate SSH brute-force traffic
        print("[3] Generating SSH brute-force traffic...")
        for i in range(10):
            subprocess.run(
                ["timeout", "1", "ssh", "-o", "ConnectTimeout=1", 
                 "-o", "StrictHostKeyChecking=no", 
                 f"baduser{i}@localhost", "-p", "22"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            time.sleep(0.5)
        print("    ✓ SSH traffic generated")
        
        # 4. Wait for model to process flows
        print("[4] Waiting for model to process flows (5 seconds)...")
        time.sleep(5)
        
        # 5. Fetch predictions
        print("[5] Fetching predictions from IDS...")
        response = requests.get("http://localhost:5000/api/predictions")
        
        if response.status_code == 200:
            predictions = response.json()
            print(f"\n    Total predictions: {len(predictions)}")
            
            if len(predictions) > 0:
                print("\n    Recent predictions:")
                print("    " + "-"*76)
                for pred in predictions[-5:]:  # Show last 5
                    print(f"    Flow: {pred['src_ip']}:{pred['src_port']} → {pred['dst_ip']}:{pred['dst_port']}")
                    print(f"    Prediction: {pred['prediction']}")
                    print(f"    Confidence: {pred['confidence']:.4f}")
                    print(f"    Packets: {pred['packets']}")
                    
                    # Check for brute-force detection
                    if "Brute" in pred['prediction']:
                        print(f"    ✓ ATTACK DETECTED: {pred['prediction']}")
                    else:
                        print(f"    ✗ Detected as: {pred['prediction']}")
                    print()
            else:
                print("    ⚠ No predictions recorded yet (flows may not have completed)")
        else:
            print(f"    ✗ Failed to fetch predictions: {response.text}")
        
        # 6. Check stats
        print("\n[6] IDS Statistics:")
        response = requests.get("http://localhost:5000/api/stats")
        if response.status_code == 200:
            stats = response.json()
            print(f"    Total predictions: {stats.get('total_predictions', 0)}")
            print(f"    Benign: {stats.get('benign', 0)}")
            print(f"    Class breakdown: {stats.get('class_counts', {})}")
    
    finally:
        # Stop server
        print("\n[7] Stopping server...")
        server_proc.terminate()
        time.sleep(1)
        server_proc.kill()
        print("    ✓ Server stopped")
    
    print("\n" + "="*80)
    print("TEST COMPLETE")
    print("="*80)

if __name__ == "__main__":
    run_test()
