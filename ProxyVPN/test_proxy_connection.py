#!/usr/bin/env python3
"""
Proxy connection test script for BiFrost
This script attempts to make HTTP and HTTPS requests through the proxy
to verify it's working correctly.
"""

import requests
import sys
import time

def test_proxy_connection():
    """Test connection through the proxy for both HTTP and HTTPS"""
    proxy_url = "http://localhost:8080"
    proxies = {
        "http": proxy_url,
        "https": proxy_url
    }
    
    test_urls = [
        "http://example.com",
        "https://example.com",
        "https://github.com"
    ]
    
    print("BiFrost Proxy Connection Tester")
    print("===============================")
    print(f"Testing proxy at: {proxy_url}\n")
    
    for url in test_urls:
        print(f"Testing {url}...")
        try:
            start_time = time.time()
            response = requests.get(url, proxies=proxies, timeout=10, verify=False)
            elapsed = time.time() - start_time
            
            if response.status_code == 200:
                print(f"✅ Success! Status code: {response.status_code}, Time: {elapsed:.2f}s")
                print(f"   Response size: {len(response.content)} bytes")
            else:
                print(f"⚠️ Received status code {response.status_code}, Time: {elapsed:.2f}s")
                
        except requests.exceptions.ProxyError:
            print("❌ Failed: Proxy connection error - Is the proxy running?")
        except requests.exceptions.SSLError:
            print("❌ Failed: SSL certificate error - Certificate not installed correctly")
        except requests.exceptions.ConnectionError:
            print("❌ Failed: Connection error - Check proxy settings and firewall")
        except requests.exceptions.Timeout:
            print("❌ Failed: Connection timeout - Proxy might be slow or unresponsive")
        except Exception as e:
            print(f"❌ Failed: Unexpected error: {e}")
            
        print("")
    
    print("Test completed. If all tests passed, your proxy setup is working correctly!")
    print("For HTTPS sites, make sure you've installed the mitmproxy certificate.")
    print("Visit http://mitm.it through your proxied browser to install the certificate.")

if __name__ == "__main__":
    # Suppress InsecureRequestWarning when verify=False
    import urllib3
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    
    test_proxy_connection()
