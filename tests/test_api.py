#!/usr/bin/env python3
"""Test script for Flask API"""

import sys
import time
import requests
import json
from threading import Thread

def test_api(base_url='http://localhost:5000'):
    """Test API endpoints"""
    print("\n" + "="*60)
    print("IDS Flask API - Test Suite")
    print("="*60)
    
    # Wait for server to start
    time.sleep(2)
    
    try:
        # Test 1: Health check
        print("\n[TEST 1] Health check...")
        resp = requests.get(f'{base_url}/health')
        print(f"Status: {resp.status_code}, Response: {resp.json()}")
        
        # Test 2: Get config
        print("\n[TEST 2] Get config...")
        resp = requests.get(f'{base_url}/api/config')
        print(f"Status: {resp.status_code}")
        config = resp.json()
        print(f"Interface: {config['network_interface']}")
        print(f"Features: {config['features_count']}")
        
        # Test 3: Start pipeline
        print("\n[TEST 3] Start pipeline...")
        resp = requests.post(f'{base_url}/api/start')
        print(f"Status: {resp.status_code}, Response: {resp.json()}")
        
        time.sleep(3)
        
        # Test 4: Get status
        print("\n[TEST 4] Get status...")
        resp = requests.get(f'{base_url}/api/status')
        status = resp.json()
        print(f"Running: {status['running']}")
        print(f"Active flows: {status['active_flows']}")
        
        # Test 5: Get summary
        print("\n[TEST 5] Get summary...")
        resp = requests.get(f'{base_url}/api/summary')
        summary = resp.json()
        print(f"Total predictions: {summary['statistics']['total_predictions']}")
        print(f"Benign: {summary['statistics']['benign_traffic']}")
        print(f"Attacks: {summary['statistics']['attack_traffic']}")
        
        # Test 6: Get recent predictions
        print("\n[TEST 6] Get predictions...")
        resp = requests.get(f'{base_url}/api/predictions?limit=5')
        preds = resp.json()
        print(f"Retrieved {preds['count']} predictions")
        if preds['predictions']:
            print(f"Latest: {preds['predictions'][0]['prediction']}")
        
        # Test 7: Get flows
        print("\n[TEST 7] Get active flows...")
        resp = requests.get(f'{base_url}/api/flows')
        flows = resp.json()
        print(f"Active flows: {flows['active']}")
        
        # Test 8: Get stats
        print("\n[TEST 8] Get stats...")
        resp = requests.get(f'{base_url}/api/stats')
        stats = resp.json()
        print(f"By class breakdown: {stats['by_class']}")
        
        # Test 9: Stop pipeline
        print("\n[TEST 9] Stop pipeline...")
        resp = requests.post(f'{base_url}/api/stop')
        print(f"Status: {resp.status_code}, Response: {resp.json()}")
        
        print("\n" + "="*60)
        print("✓ All tests completed successfully!")
        print("="*60)
        
    except requests.exceptions.ConnectionError:
        print("✗ Could not connect to server. Make sure it's running on port 5000")
        sys.exit(1)
    except Exception as e:
        print(f"✗ Test failed: {e}")
        sys.exit(1)


if __name__ == '__main__':
    test_api()
