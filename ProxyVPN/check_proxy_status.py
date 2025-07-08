#!/usr/bin/env python3
"""
Check if the BiFrost proxy is running
"""

import socket
import sys

def is_port_in_use(port, host='localhost'):
    """Check if a port is in use"""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        try:
            s.connect((host, port))
            return True
        except socket.error:
            return False

def main():
    proxy_port = 8080
    proxy_host = 'localhost'
    
    print("BiFrost Proxy Status Check")
    print("=========================")
    
    # Check if proxy is running
    if is_port_in_use(proxy_port, proxy_host):
        print(f"✅ Proxy is RUNNING on {proxy_host}:{proxy_port}")
        print("You can configure your browser to use this proxy address.")
    else:
        print(f"❌ Proxy is NOT RUNNING on {proxy_host}:{proxy_port}")
        print("Start the proxy using one of these commands:")
        print("  ./run_basic_proxy.py")
        print("  mitmdump --listen-host 0.0.0.0 --listen-port 8080")
    
    print("\nRemember to:")
    print("1. Configure your browser to use the proxy")
    print("2. Install the mitmproxy certificate (visit http://mitm.it)")
    
    return 0 if is_port_in_use(proxy_port, proxy_host) else 1

if __name__ == "__main__":
    sys.exit(main())
