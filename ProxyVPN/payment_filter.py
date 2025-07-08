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
    def __init__(self, config: PaymentFilterConfig):
        self.config = config
        self.setup_logging()

        # Initialize Redis client with fallback to None if Redis not available
        try:
            self.redis_client = redis.Redis(host=os.getenv("REDIS_HOST", "localhost"), 
                                          port=int(os.getenv("REDIS_PORT", "6379")),
                                          socket_connect_timeout=2)
            # Test connection
            self.redis_client.ping()
            self.redis_available = True
        except:
            self.payment_logger.warning("Redis not available. Caching functionality disabled.")
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

    def handle_request_with_fallback(self, flow):
        if self.check_approval_service_health():
            # Normal flow
            pass
        else:
            # Fallback behavior (e.g., log and allow, or deny based on config)
            pass

    def get_cached_decision(self, flow):
        """Get decision from cache based on request pattern"""
        if not self.redis_available:
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
        if not self.redis_available:
            return
            
        try:
            cache_key = f"decision:{flow.request.host}:{flow.request.path.split('?')[0]}"
            self.redis_client.set(cache_key, decision, ex=ttl)
        except Exception as e:
            self.payment_logger.error(f"Redis error in cache_decision: {e}")

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