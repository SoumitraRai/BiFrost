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
        # Set to DEBUG level to capture all the detailed logs we've added
        self.payment_logger.setLevel(logging.DEBUG)

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
            content = flow.request.get_text()
            if content:
                content = str(content).lower()
            else:
                content = ""

            # Check if the URL matches any payment domains
            if any(domain in url for domain in self.config.payment_domains):
                return True

            # Combine content and headers for keyword searching
            combined_text = content + " " + " ".join(f"{str(k).lower()}:{str(v).lower()}" for k, v in headers.items())
            if any(keyword in combined_text for keyword in self.config.payment_keywords):
                return True

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
        if flow:
            flow.response = http.Response.make(
                403,
                b"<html><body><h1>Payment Blocked</h1><p>This payment request has been blocked by BiFrost Proxy for your safety.</p></body></html>",
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

    def cache_decision(self, flow, decision, ttl=120):
        """Cache a decision for similar requests for 2 minutes"""
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
        import threading
        # Skip if flow is already being processed
        if hasattr(flow, "payment_intercepted") and flow.payment_intercepted:
            return

        # Check if this is a payment request
        if self.is_payment_request(flow):
            flow.payment_intercepted = True
            self.payment_logger.info(f"[Payment Detected] {flow.request.url}")
            self.payment_logger.debug(f"[DEBUG] Flow ID: {flow.id}, URL: {flow.request.url}")

            # Check for cached decision first
            cached_decision = self.get_cached_decision(flow)
            if cached_decision:
                self.payment_logger.info(f"[Cached Decision] {cached_decision} for {flow.request.url}")
                if cached_decision == "deny":
                    self.block_request(flow)
                elif cached_decision == "approve":
                    # Let the request go through
                    pass
                self.payment_logger.debug(f"[DEBUG] Returning on cached decision: {cached_decision}")
                return

            # If approval service is available, intercept the request for approval
            if self.check_approval_service_health():
                try:
                    # Send flow data to approval mechanism
                    flow_data = {
                        "id": flow.id,
                        "url": flow.request.url,
                        "method": flow.request.method,
                        "headers": dict(flow.request.headers),
                        "timestamp": time.time()
                    }
                    self.send_to_approval_mechanism(flow_data)

                    # Intercept the flow so the browser keeps loading
                    self.payment_logger.info(f"[INTERCEPT] Intercepting flow {flow.id} for approval")
                    flow.intercept()

                    # Store the flow for later reference
                    self.pending_flows[flow.id] = flow

                    # Start a background thread to wait for decision
                    self.payment_logger.info(f"[THREAD] Starting approval wait thread for {flow.id}")
                    thread = threading.Thread(target=self.wait_for_approval, args=(flow.id,), daemon=True)
                    thread.start()
                    self.payment_logger.debug(f"[DEBUG] Thread started: {thread.is_alive()}")
                except Exception as e:
                    self.payment_logger.error(f"[Approval Error] {e}")
                    self.block_request(flow)
            else:
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
        
    def wait_for_approval(self, flow_id):
        """
        Wait for approval or timeout (60s) for a payment request.
        If approved, create a response that mimics the original request going through.
        """
        timeout = 60
        start_time = time.time()
        flow = self.pending_flows.get(flow_id)
        
        if not flow:
            self.payment_logger.error(f"[CRITICAL] Flow {flow_id} not found in pending_flows!")
            return
            
        self.payment_logger.debug(f"[DEBUG] Starting approval wait for flow {flow_id}")
        
        while flow and time.time() - start_time < timeout:
            try:
                response = requests.get(f"{self.config.approval_url}/decision/{flow_id}", timeout=2)
                self.payment_logger.debug(f"[DEBUG] Approval poll response: {response.status_code}")
                
                if response.status_code == 200:
                    decision_data = response.json()
                    decision = decision_data.get("decision")
                    self.payment_logger.debug(f"[DEBUG] Decision received: {decision}")
                    
                    if decision == "approve":
                        self.payment_logger.info(f"[APPROVE] Approved flow {flow_id}")
                        
                        # Instead of trying to resume an already-blocked flow, 
                        # we'll modify the response to indicate approval
                        url = getattr(getattr(flow, 'request', None), 'url', flow_id)
                        self.payment_logger.info(f"[Payment Approved] {url}")
                        
                        # Save this decision for future requests
                        self.cache_decision(flow, "approve")
                        
                        # This will allow the user to retry the request now that it's in the cache as approved
                        flow.response = http.Response.make(
                            200,
                            b"<html><body><h1>Payment Approved</h1><p>This payment request has been approved. Please refresh or try again.</p></body></html>",
                            {"Content-Type": "text/html"}
                        )
                        break
                        
                    elif decision == "deny":
                        self.payment_logger.info(f"[BLOCK] Denying flow {flow_id}")
                        # Flow is already blocked, but we'll update the response message
                        flow.response = http.Response.make(
                            403,
                            b"<html><body><h1>Payment Denied</h1><p>This payment request has been denied by the administrator.</p></body></html>",
                            {"Content-Type": "text/html"}
                        )
                        self.cache_decision(flow, "deny")
                        url = getattr(getattr(flow, 'request', None), 'url', flow_id)
                        self.payment_logger.info(f"[Payment Denied] {url}")
                        break
            except Exception as e:
                self.payment_logger.error(f"[Approval Poll Error] {e} for {flow_id}")
            
            time.sleep(1)
            
        else:
            # Timeout reached, make sure the request is blocked with a timeout message
            self.payment_logger.warning(f"[Timeout] Approval wait timed out for flow {flow_id}")
            
            # Flow is already blocked, but we'll update the response message
            flow.response = http.Response.make(
                403,
                b"<html><body><h1>Payment Timeout</h1><p>This payment request timed out waiting for approval.</p></body></html>",
                {"Content-Type": "text/html"}
            )
            
            url = getattr(getattr(flow, 'request', None), 'url', flow_id)
            self.payment_logger.warning(f"[Approval Timeout] Payment request timed out for {url}")
            
        # Clean up
        if flow_id in self.pending_flows:
            self.payment_logger.debug(f"[DEBUG] Removing flow {flow_id} from pending_flows")
            del self.pending_flows[flow_id]


# Create a default instance of the filter that can be used as an addon
payment_filter_addon = PaymentFilter()

# This function can be used to add the payment filter to mitmproxy
def create_addon():
    """Creates and returns a new instance of the payment filter addon"""
    return PaymentFilter()