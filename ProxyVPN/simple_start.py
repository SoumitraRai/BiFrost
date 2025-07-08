#!/usr/bin/env python3
"""
Simplified BiFrost Controller
This version starts only the proxy server with minimal dependencies
"""

import subprocess
import sys
import os
import time

def start_proxy_server():
    print("🕵️‍♂️ Starting HTTPS Proxy Server...")
    # Use the simple payment filter version
    os.environ["PYTHONPATH"] = os.getcwd()
    return subprocess.Popen([sys.executable, "-m", "mitmproxy", "-s", "payment_filter_simple.py", 
                            "--listen-host", "0.0.0.0", "--listen-port", "8080"])

def main():
    try:
        print("🌈 Starting BiFrost Proxy System (Simplified Version)...")

        # Start only the proxy server
        proxy_process = start_proxy_server()
        print("✅ Proxy server running at localhost:8080")
        print("🔒 IMPORTANT: Make sure to install the mitmproxy certificate on your device/browser!")
        print("🔎 Visit http://mitm.it in your browser to download the certificate after configuring the proxy")
        print("\n💻 Press Ctrl+C to stop the proxy")

        # Wait for the proxy process
        proxy_process.wait()

    except KeyboardInterrupt:
        print("\n🛑 Shutting down BiFrost components...")
        if 'proxy_process' in locals():
            proxy_process.terminate()
        sys.exit(0)
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    # Simplified check for just the mitmproxy availability
    try:
        import mitmproxy
    except ImportError:
        print("❌ Error: mitmproxy is not installed!")
        print("📦 Please run: pip install mitmproxy")
        sys.exit(1)
    
    main()
