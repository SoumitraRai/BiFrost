import logging
import re
from mitmproxy import http
import json
import urllib.parse

class NetworkProxyFilter:
    def __init__(self):
        # Initialize logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
        
        # Tracking variables
        self.total_requests = 0
        self.request_types = {}

    def format_url(self, flow):
        """
        Parse and format URL for clean display
        """
        url = flow.request.url
        parsed = urllib.parse.urlparse(url)
        return f"{parsed.netloc}{parsed.path}"

    def log_request_type(self, method):
        """
        Track request types
        """
        self.request_types[method] = self.request_types.get(method, 0) + 1

    def request(self, flow: http.HTTPFlow) -> None:
        """
        Comprehensive request logging
        """
        self.total_requests += 1
        
        # Log request type
        method = flow.request.method
        self.log_request_type(method)

        # Format request details
        request_size = len(flow.request.content) if flow.request.content else 0
        protocol = flow.request.scheme.upper()
        formatted_url = self.format_url(flow)
        
        # Prepare headers preview
        headers_preview = dict(flow.request.headers)
        
        # Print detailed request information
        print(f"[>] {method} {protocol} REQUEST to {formatted_url}")
        print(f"[*] Request Size: {request_size} bytes")
        print(f"[*] Headers: {json.dumps(headers_preview, indent=2)}")

        # Optional: print request body if not too large
        if request_size > 0 and request_size < 1024:  # Limit to 1KB
            try:
                body_preview = flow.request.content.decode('utf-8')[:100]
                print(f"[*] Request Body Preview: {body_preview}")
            except Exception:
                print("[*] Request body is not text-decodable")

    def response(self, flow: http.HTTPFlow) -> None:
        """
        Comprehensive response logging
        """
        if not flow.response:
            return

        # Get response details
        response_size = len(flow.response.content) if flow.response.content else 0
        protocol = flow.request.scheme.upper()
        formatted_url = self.format_url(flow)
        status_code = flow.response.status_code

        # Print response information
        print(f"[<] {protocol} RESPONSE from {formatted_url}")
        print(f"[*] Status Code: {status_code}")
        print(f"[*] Response Size: {response_size} bytes")

        # Attempt to parse and preview response content
        try:
            # Try parsing as JSON
            content = flow.response.content.decode('utf-8')
            try:
                json_content = json.loads(content)
                json_preview = json.dumps(json_content, indent=2)[:200] + "..." \
                    if len(json.dumps(json_content)) > 200 \
                    else json.dumps(json_content)
                print(f"[*] JSON Response Preview: {json_preview}")
            except json.JSONDecodeError:
                # If not JSON, try text preview
                text_preview = content[:200] + "..." if len(content) > 200 else content
                print(f"[*] Text Response Preview: {text_preview}")
        except Exception:
            print("[*] Response content is not text-decodable")

    def error(self, flow: http.HTTPFlow) -> None:
        """
        Log any errors during request/response
        """
        if flow.error:
            print(f"[!] ERROR: {flow.error.msg}")

    def done(self):
        """
        Print summary when proxy is done
        """
        print("\n--- Proxy Session Summary ---")
        print(f"Total Requests: {self.total_requests}")
        print("Request Types:")
        for method, count in self.request_types.items():
            print(f"  {method}: {count}")
        print("-----------------------------")

# Create an addon instance to use with mitmproxy
network_proxy = NetworkProxyFilter()
addons = [network_proxy]