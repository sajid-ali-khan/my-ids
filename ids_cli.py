#!/usr/bin/env python3
"""
IDS CLI Entry Point

This script allows running the IDS CLI as:
  python ids_cli.py [command] [options]
  
Or after installation:
  ids-cli [command] [options]
"""

import sys
from ids_cli.cli import main

if __name__ == '__main__':
    main()
