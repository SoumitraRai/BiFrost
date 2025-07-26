"""
This is a modified version of payment_filter.py that removes Redis dependency
for users who don't have Redis installed.
"""

import os
import json
import logging
import requests
import time
from mitmproxy import http
from dotenv import load_dotenv
from tenacity import retry, stop_after_attempt, wait_exponential

load_dotenv()  # Load environment variables

class PaymentFilterConfig:
    def __init__(self):
        self.payment_domains = [
            "paypal.com", "stripe.com", "razorpay.com",
            "paytm.com", "phonepe.com", "gpay.com",
            "apple.com/payment", "google.com/pay", "checkout", "secure.pay"
        ]
        self.payment_keywords = [
            "payment", "transaction", "card", "wallet", "upi", "purchase",
            "order", "billing", "credit", "debit", "checkout", "pay"
        ]
        self.timeout = 30  # seconds
        self.log_dir = "../bifrost-ui/public/proxy_logs"
        self.approval_url = os.getenv("APPROVAL_SERVICE_URL", "http://localhost:5000")

class PaymentFilter:
    def __init__(self, config: PaymentFilterConfig = None):
        self.config = config if config else PaymentFilterConfig()
        self.setup_logging()
        # Simple in-memory cache as fallback
        self.memory_cache = {}

    def setup_logging(self):
        LOG_DIR = self.config.log_dir
        PAYMENT_LOG_FILE = os.path.join(LOG_DIR, 'payment_traffic.log')

        # Create the directory if it doesn't exist
        os.makedirs(LOG_DIR, exist_ok=True)

        # Setup logger for payment filter
        self.payment_logger = logging.getLogger("payment_filter")
        self.payment_logger.setLevel(logging.INFO)

        # Configure handlers only if they haven't been added already
        if not self.payment_logger.handlers:
            # File handler to log to a file
            file_handler = logging.FileHandler(PAYMENT_LOG_FILE)
            file_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s: %(message)s'))

            # Stream handler to log to the console
            stream_handler = logging.StreamHandler()
            stream_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s: %(message)s'))

            # Add handlers to the logger
            self.payment_logger.addHandler(file_handler)
            self.payment_logger.addHandler(stream_handler)

    def is_payment_request(self, flow: http.HTTPFlow) -> bool:
        """
        Determines if an HTTP flow is related to a payment transaction.
        """
        try:
            url = flow.request.pretty_url.lower()
            headers = flow.request.headers
            content = flow.request.get_text().lower() if flow.request.content else ""

            # Check if the URL matches any payment domains
            if any(domain in url for domain in self.config.payment_domains):
                return True

            # Combine content and headers for keyword searching
            combined_text = content + " " + " ".join(f"{k.lower()}:{v.lower()}" for k, v in headers.items())
            if any(keyword in combined_text for keyword in self.config.payment_keywords):
                return True
                
            # Not a payment request
            return False

        except Exception as e:
            self.payment_logger.error(f"[Detection Error in is_payment_request] {e}")
            return False

    def check_approval_service_health(self):
        try:
            response = requests.get(f"{self.config.approval_url}/health", timeout=2)
            return response.status_code == 200
        except:
            return False

    def handle_request_with_fallback(self, flow):
        if self.check_approval_service_health():
            # Normal flow
            pass
        else:
            # Fallback behavior (e.g., log and allow, or deny based on config)
            pass

    def get_cached_decision(self, flow):
        """Get decision from memory cache based on request pattern"""
        try:
            # Generate a cache key based on domain, path pattern
            cache_key = f"decision:{flow.request.host}:{flow.request.path.split('?')[0]}"
            
            # Check if we have a cached decision
            if cache_key in self.memory_cache:
                cached_entry = self.memory_cache[cache_key]
                # Check if entry is expired
                if time.time() < cached_entry['expiry']:
                    return cached_entry['decision']
                else:
                    # Remove expired entry
                    del self.memory_cache[cache_key]
        except Exception as e:
            self.payment_logger.error(f"Cache error in get_cached_decision: {e}")
        
        return None

    def cache_decision(self, flow, decision, ttl=3600):
        """Cache a decision in memory for similar requests"""
        try:
            cache_key = f"decision:{flow.request.host}:{flow.request.path.split('?')[0]}"
            self.memory_cache[cache_key] = {
                'decision': decision,
                'expiry': time.time() + ttl
            }
        except Exception as e:
            self.payment_logger.error(f"Cache error in cache_decision: {e}")

    # Use retry decorator for resilience
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=10))
    def send_to_approval_mechanism(self, flow_data):
        response = requests.post(
            f"{self.config.approval_url}/intercepted",
            json=flow_data,
            timeout=5
        )
        if response.status_code != 200:
            raise Exception(f"Error sending to approval mechanism: {response.status_code}")
        return response.json()

    def request(self, flow: http.HTTPFlow):
        """
        Handle each HTTP request intercepted by mitmproxy
        """
        try:
            flow_id = getattr(flow, 'id', str(id(flow)))
            self.payment_logger.info(f"[👀] Processing request: {flow.request.url}")
            
            # Check if this is a payment-related request
            if self.is_payment_request(flow):
                self.payment_logger.warning(f"[💰] DETECTED PAYMENT in request: {flow.request.url}")
                
                # Extract flow data for approval mechanism
                flow_data = {
                    'id': flow_id,
                    'url': flow.request.url,
                    'method': flow.request.method,
                    'host': flow.request.host,
                    'timestamp': time.time()
                }
                
                # Try to get cached decision first
                cached_decision = self.get_cached_decision(flow)
                if cached_decision:
                    self.payment_logger.info(f"[💾] Using cached decision '{cached_decision}' for {flow.request.url}")
                    if cached_decision == 'deny':
                        flow.kill()
                        return
                    # Otherwise allow (continue processing)
                    return
                
                # No cached decision, send to approval mechanism
                try:
                    result = self.send_to_approval_mechanism(flow_data)
                    decision = result.get('decision')
                    
                    if decision == 'deny':
                        self.payment_logger.warning(f"[🛑] DENIED payment request to {flow.request.url}")
                        # Cache this decision for future similar requests
                        self.cache_decision(flow, 'deny')
                        # Kill the flow to block the request
                        flow.kill()
                    elif decision == 'approve':
                        self.payment_logger.info(f"[✅] APPROVED payment request to {flow.request.url}")
                        # Cache this decision for future similar requests
                        self.cache_decision(flow, 'approve')
                    elif decision == 'need_approval':
                        self.payment_logger.info(f"[⏳] Payment request needs parental approval: {flow.request.url}")
                        # Don't cache "need_approval" decisions as they require explicit interaction
                    else:
                        # Default behavior if decision is not recognized - allow but don't cache
                        self.payment_logger.warning(f"[⚠️] Unknown decision '{decision}' for {flow.request.url}")
                        
                except Exception as e:
                    # On approval mechanism error, default to safe behavior (deny)
                    self.payment_logger.error(f"[❌] Error contacting approval mechanism: {e}")
                    flow.kill()
                    
        except Exception as e:
            self.payment_logger.error(f"[❌] Error in request handler: {e}")

# Initialize the config and filter for use by mitmproxy
config = PaymentFilterConfig()
filter_instance = PaymentFilter(config)

# These are the hook methods mitmproxy will call
def request(flow):
    filter_instance.request(flow)

def response(flow):
    # Optional response handling
    pass
