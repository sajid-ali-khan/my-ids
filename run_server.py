#!/usr/bin/env python3
"""
IDS Flask API Server
- Sets up the environment
- Initializes the core pipeline
- Creates and runs the Flask API server
"""

import os
import sys
from pathlib import Path

# Ensure the project root is in the Python path
# This is necessary for the pipx installation to find the modules
project_root = Path(__file__).parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from ids_api import create_app
from ids_core import PipelineManager
from ids_cli.config import ConfigManager


def main():
    """Load config and run the server."""
    
    print("🚀 Starting IDS Server...")
    
    # Load configuration from ~/.ids/config.json
    config = ConfigManager.load()
    
    # Get settings from config, with fallbacks to environment variables or defaults
    interface = config.get('interface', os.getenv('IDS_INTERFACE', 'eth0'))
    port = int(config.get('port', os.getenv('IDS_PORT', 5000)))
    model_dir = config.get('model_dir', os.getenv('IDS_MODEL_DIR', './model'))
    debug = config.get('debug', False)
    host = config.get('host', '0.0.0.0')
    
    print(f"  - Interface: {interface}")
    print(f"  - Port: {port}")
    print(f"  - Model Dir: {model_dir}")
    print(f"  - Debug Mode: {debug}")
    
    # --- Initialize Core Pipeline ---
    try:
        pipeline = PipelineManager(
            model_dir=model_dir,
            network_interface=interface
        )
    except Exception as e:
        print(f"✗ FATAL: Failed to initialize pipeline: {e}")
        print("  Please ensure the model path is correct and files are accessible.")
        exit(1)
    
    # --- Create and Run Flask App ---
    app = create_app(pipeline)
    
    print(f"\n✓ Server ready and listening on http://{host}:{port}")
    print("  Press CTRL+C to stop the server.")
    
    try:
        app.run(host=host, port=port, debug=debug)
    except PermissionError:
        print(f"\n✗ FATAL: Permission denied to bind to port {port} or access interface {interface}.")
        print("  Try running with 'sudo'.")
        exit(1)
    except Exception as e:
        print(f"\n✗ FATAL: An unexpected error occurred: {e}")
        exit(1)
    finally:
        if pipeline.is_running:
            print("\nShutting down pipeline...")
            pipeline.stop()


if __name__ == '__main__':
    main()
