import os
import json
import logging
import requests
import time
import redis
from mitmproxy import http
from dotenv import load_dotenv
import pybreaker
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
        self.log_dir = "../logs"
        self.approval_url = os.getenv("APPROVAL_SERVICE_URL", "http://localhost:5000")

class PaymentFilter:
    def __init__(self, config=None):
        if config is None:
            self.config = PaymentFilterConfig()
        else:
            self.config = config
        self.setup_logging()
        
        # Store flows waiting for approval
        self.pending_flows = {}

        # Initialize Redis client with fallback to None if Redis not available
        try:
            self.redis_client = redis.Redis(host=os.getenv("REDIS_HOST", "localhost"), 
                                          port=int(os.getenv("REDIS_PORT", "6379")),
                                          socket_connect_timeout=2)
            # Test connection
            self.redis_client.ping()
            self.redis_available = True
        except:
            if hasattr(self, 'payment_logger'):
                self.payment_logger.warning("Redis not available. Caching functionality disabled.")
            else:
                print("Redis not available. Caching functionality disabled.")
            self.redis_client = None
            self.redis_available = False

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

            # If we get here, it's not a payment request
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
            
    def block_request(self, flow):
        """Block a payment request by returning a custom error page"""
        flow.response = http.Response.make(
            403,  # Forbidden status code
            b"<html><body><h1>Payment Blocked</h1><p>This payment request has been blocked by BiFrost Proxy.</p></body></html>",
            {"Content-Type": "text/html"}
        )

    def handle_request_with_fallback(self, flow):
        """Handle a request with fallback behavior when approval service is unavailable"""
        if self.check_approval_service_health():
            # Normal flow - use approval service
            try:
                # Prepare flow data to send to approval mechanism
                flow_data = {
                    "id": flow.id,
                    "url": flow.request.url,
                    "method": flow.request.method,
                    "headers": dict(flow.request.headers),
                    "timestamp": time.time()
                }
                
                # Send to approval mechanism
                self.send_to_approval_mechanism(flow_data)
                return True
            except Exception as ex:
                self.payment_logger.error(f"Error in approval process: {ex}")
                # Fall through to fallback
        
        # Fallback behavior - block payments by default for safety
        self.payment_logger.warning(f"Using fallback behavior: BLOCKING payment to {flow.request.url}")
        self.block_request(flow)
        return False

    def get_cached_decision(self, flow):
        """Get decision from cache based on request pattern"""
        if not self.redis_available or not self.redis_client:
            return None
            
        try:
            # Generate a cache key based on domain, path pattern, etc.
            cache_key = f"decision:{flow.request.host}:{flow.request.path.split('?')[0]}"
            
            # Check if we have a cached decision
            cached = self.redis_client.get(cache_key)
            if cached:
                return cached.decode('utf-8')
        except Exception as e:
            self.payment_logger.error(f"Redis error in get_cached_decision: {e}")
        
        return None

    def cache_decision(self, flow, decision, ttl=3600):
        """Cache a decision for similar requests"""
        if not self.redis_available or not self.redis_client:
            return
            
        try:
            cache_key = f"decision:{flow.request.host}:{flow.request.path.split('?')[0]}"
            self.redis_client.set(cache_key, decision, ex=ttl)
        except Exception as e:
            self.payment_logger.error(f"Redis error in cache_decision: {e}")

    # The request and response methods are defined elsewhere in the file
    # We'll delete these duplicates

    # Create circuit breaker
    approval_breaker = pybreaker.CircuitBreaker(
        fail_max=5,
        reset_timeout=60,
        exclude=[requests.exceptions.Timeout]
    )

    # Use retry decorator for resilience
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=10))
    @approval_breaker
    def send_to_approval_mechanism(self, flow_data):
        response = requests.post(
            f"{self.config.approval_url}/intercepted",
            json=flow_data,
            timeout=5
        )
        if response.status_code != 200:
            raise Exception(f"Error sending to approval mechanism: {response.status_code}")
        return response.json()
        
    # mitmproxy addon hooks
    def request(self, flow):
        """
        Called when a client request is intercepted.
        This hook is used to detect and handle payment requests.
        """
        # Skip if flow is already being processed
        if hasattr(flow, "payment_intercepted") and flow.payment_intercepted:
            return
            
        # Check if this is a payment request
        if self.is_payment_request(flow):
            flow.payment_intercepted = True
            
            # Log the intercepted payment request
            self.payment_logger.info(f"[Payment Detected] {flow.request.url}")
            
            # 1. Check cached decision first
            cached_decision = self.get_cached_decision(flow)
            if cached_decision:
                self.payment_logger.info(f"[Cached Decision] {cached_decision} for {flow.request.url}")
                if cached_decision == "deny":
                    # Block immediately based on cached decision
                    self.block_request(flow)
                return
                
            # 2. If no cached decision, check if approval service is available
            if self.check_approval_service_health():
                try:
                    # Prepare flow data to send to approval mechanism
                    flow_data = {
                        "id": flow.id,
                        "url": flow.request.url,
                        "method": flow.request.method,
                        "headers": dict(flow.request.headers),
                        "timestamp": time.time()
                    }
                    
                    # Send to approval mechanism
                    result = self.send_to_approval_mechanism(flow_data)
                    
                    # Block the request while waiting for approval
                    flow.intercept()
                    
                    # Store the flow ID for tracking
                    self.pending_flows[flow.id] = flow
                    
                    # Start a background task to check for decision
                    self.check_for_decision(flow.id)
                    
                except Exception as e:
                    self.payment_logger.error(f"[Approval Error] {e}")
                    # Fallback to blocking on error (safer option)
                    self.block_request(flow)
            else:
                # Approval service is not available, use fallback behavior
                self.payment_logger.warning(f"[Approval Service Unavailable] Blocking payment request: {flow.request.url}")
                self.block_request(flow)
                
    def response(self, flow):
        """
        Called when a server response is intercepted.
        """
        # We can add response analysis here if needed
        pass
                
    def block_request(self, flow):
        """Block a payment request by returning a custom error page"""
        flow.response = http.Response.make(
            403,  # Forbidden status code
            b"<html><body><h1>Payment Blocked</h1><p>This payment request has been blocked by BiFrost Proxy.</p></body></html>",
            {"Content-Type": "text/html"}
        )
        
    def check_for_decision(self, flow_id):
        """
        Check for a decision from the approval mechanism.
        This can be implemented as a non-blocking background task.
        """
        try:
            # Try to get the flow
            if flow_id not in self.pending_flows:
                return
                
            flow = self.pending_flows[flow_id]
            
            # Get decision (blocking call)
            response = requests.get(f"{self.config.approval_url}/wait_decision/{flow_id}", timeout=35)
            
            if response.status_code == 200:
                decision = response.json().get("decision")
                
                if decision == "approve":
                    # Allow the request to continue
                    if hasattr(flow, "intercepted") and flow.intercepted:
                        flow.resume()
                    self.cache_decision(flow, "approve")
                    self.payment_logger.info(f"[Payment Approved] {flow.request.url}")
                else:
                    # Block the request
                    self.block_request(flow)
                    self.cache_decision(flow, "deny")
                    self.payment_logger.info(f"[Payment Denied] {flow.request.url}")
            else:
                # Default to blocking on error
                self.block_request(flow)
                self.payment_logger.warning(f"[Decision Error] Status {response.status_code} for {flow_id}")
                     # Clean up
        if flow_id in self.pending_flows:
            del self.pending_flows[flow_id]
                
        except Exception as e:
            self.payment_logger.error(f"[Decision Error] {e} for {flow_id}")
            # Try to get the flow and block it
            if flow_id in self.pending_flows:
                flow = self.pending_flows[flow_id]
                self.block_request(flow)
                del self.pending_flows[flow_id]


# Create a default instance of the filter that can be used as an addon
payment_filter_addon = PaymentFilter()

# This function can be used to add the payment filter to mitmproxy
def create_addon():
    """Creates and returns a new instance of the payment filter addon"""
    return PaymentFilter()