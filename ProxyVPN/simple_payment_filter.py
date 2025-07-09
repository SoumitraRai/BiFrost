"""
Payment Filter Module for BiFrost Proxy
Detects and blocks payment-related traffic
"""
import os
import json
import logging
from mitmproxy import http
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

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

class SimplePaymentFilter:
    """
    A simplified payment filter that blocks all payment-related traffic.
    """
    def __init__(self):
        self.config = PaymentFilterConfig()
        self.setup_logging()
        self.payment_logger.info("[PAYMENT FILTER] Initialized and ready")

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
                self.payment_logger.info(f"[PAYMENT DOMAIN MATCH] {url}")
                return True
                
            # Combine content and headers for keyword searching
            combined_text = content + " " + " ".join(f"{k.lower()}:{v.lower()}" for k, v in headers.items())
            if any(keyword in combined_text for keyword in self.config.payment_keywords):
                self.payment_logger.info(f"[PAYMENT KEYWORD MATCH] {url}")
                return True
                
            # If we get here, it's not a payment request
            return False
            
        except Exception as e:
            self.payment_logger.error(f"[Detection Error] {e}")
            return False

    def block_request(self, flow: http.HTTPFlow):
        """Block a payment request by returning a custom error page"""
        self.payment_logger.info(f"[PAYMENT BLOCKED] {flow.request.url}")
        
        flow.response = http.Response.make(
            403,  # Forbidden status code
            b"<html><body><h1>Payment Blocked</h1><p>This payment request has been blocked by BiFrost Proxy for your safety.</p></body></html>",
            {"Content-Type": "text/html"}
        )

    # mitmproxy addon hooks
    def request(self, flow: http.HTTPFlow):
        """
        This is called by mitmproxy for each request.
        Check if this is a payment request and block if needed.
        """
        # Skip options and other special requests
        if flow.request.method == "OPTIONS":
            return
            
        # Check if this is a payment request
        if self.is_payment_request(flow):
            # Block the payment request
            self.block_request(flow)

    def response(self, flow: http.HTTPFlow):
        """
        This is called by mitmproxy for each response.
        We could add additional response filtering here if needed.
        """
        pass

# Create a single instance to be used by the proxy
payment_filter = SimplePaymentFilter()
