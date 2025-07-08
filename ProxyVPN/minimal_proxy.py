#!/usr/bin/env python3
"""
Minimal proxy script for BiFrost
This script runs mitmproxy directly with minimal configuration
"""

import os
import sys
from mitmproxy.tools.main import mitmdump

def run_proxy():
    print("Starting mitmproxy...")
    sys.argv = [
        'mitmdump',
        '--listen-host', '0.0.0.0',
        '--listen-port', '8080',
    ]
    
    try:
        mitmdump()
    except KeyboardInterrupt:
        print("Proxy stopped.")

if __name__ == "__main__":
    run_proxy()
