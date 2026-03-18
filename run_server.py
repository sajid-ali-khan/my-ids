#!/usr/bin/env python3
"""Flask API server startup script"""

import sys
import os
from ids_api import create_app

if __name__ == '__main__':
    # Configuration
    model_dir = './model'
    interface = os.environ.get('IDS_INTERFACE', 'wlp3s0')
    port = int(os.environ.get('IDS_PORT', 5000))
    debug = os.environ.get('IDS_DEBUG', 'False') == 'True'
    
    print("\n" + "="*60)
    print("IDS Flask API Server")
    print("="*60)
    print(f"Interface: {interface}")
    print(f"Port: {port}")
    print(f"Debug: {debug}")
    print("="*60 + "\n")
    
    try:
        # Create and run Flask app
        app = create_app(model_dir=model_dir, interface=interface)
        
        print(f"✓ Starting server on http://0.0.0.0:{port}")
        print("Press Ctrl+C to stop\n")
        
        app.run(
            host='0.0.0.0',
            port=port,
            debug=debug,
            use_reloader=False,
            threaded=True
        )
    
    except KeyboardInterrupt:
        print("\n\nShutting down...")
        if hasattr(app, 'pipeline'):
            app.pipeline.stop()
        sys.exit(0)
    
    except Exception as e:
        print(f"\n✗ Error: {e}")
        sys.exit(1)
