#!/usr/bin/env python3
"""Test script for refactored PipelineManager"""

import sys
import time
from ids_core import PipelineManager

if __name__ == '__main__':
    # Configuration
    model_dir = './model'
    interface = 'wlp3s0'
    
    # Create pipeline manager
    try:
        pipeline = PipelineManager(
            model_dir=model_dir,
            network_interface=interface,
            flusher_interval=20,
            idle_timeout=30,
            max_history=100
        )
    except Exception as e:
        print(f"Error initializing pipeline: {e}")
        sys.exit(1)
    
    print("\n" + "="*60)
    print("IDS Pipeline - Refactored PipelineManager Test")
    print("="*60)
    
    try:
        # Start pipeline
        pipeline.start()
        
        # Keep running and periodically show stats
        while True:
            time.sleep(10)
            
            status = pipeline.get_status()
            stats = pipeline.get_stats()
            
            print(f"\n[STATUS] Running: {status['running']}")
            print(f"[STATUS] Active flows: {status['active_flows']}")
            print(f"[STATUS] Predictions: {status['predictions_processed']}")
            print(f"[STATS] Benign: {stats['benign']}, Classes: {stats['by_class']}")
    
    except KeyboardInterrupt:
        print("\n\nShutting down...")
        pipeline.stop()
        print("Goodbye!")
