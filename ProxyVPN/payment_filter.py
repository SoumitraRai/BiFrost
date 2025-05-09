import os
import json
import logging
import requests
import time
from mitmproxy import http

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
        self.approval_url = "http://localhost:5000"

class PaymentFilter:
    def __init__(self, config: PaymentFilterConfig):
        self.config = config
        self.setup_logging()

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

        except Exception as e:
            self.payment_logger.error(f"[Detection Error in is_payment_request] {e}")
            return False  # Return False if an error occurs during detection

        return False # Return False if no payment indicators are found

    def request(self, flow: http.HTTPFlow):
        """
        This function is called for every HTTP request.
        It checks if the request is a payment request, logs it, and handles approval flow.
        """
        if self.is_payment_request(flow):
            try:
                # Send to approval mechanism
                approval_data = {
                    "id": flow.id,
                    "url": flow.request.pretty_url,
                    "method": flow.request.method,
                }
                
                r = requests.post(
                    "http://localhost:5000/intercepted",
                    json=approval_data
                )
                
                if r.status_code == 200:
                    # Wait for decision
                    max_retries = self.config.timeout  # Use configured timeout
                    while max_retries > 0:
                        try:
                            decision_response = requests.get(
                                f"{self.config.approval_url}/decision/{flow.id}",
                                timeout=5
                            )
                            if decision_response.status_code == 200:
                                decision = decision_response.json().get("decision")
                                if decision == "approve":
                                    self.payment_logger.info(f"[PAYMENT APPROVED] ID: {flow.id}")
                                    return  # Let request continue
                                elif decision == "deny":
                                    self.payment_logger.info(f"[PAYMENT DENIED] ID: {flow.id}")
                                    flow.kill()  # Block request
                                    return
                        except requests.exceptions.RequestException as e:
                            self.payment_logger.error(f"[DECISION CHECK ERROR] ID: {flow.id}, Error: {e}")
                        
                        time.sleep(1)
                        max_retries -= 1

                    # Timeout reached
                    self.payment_logger.warning(f"[DECISION TIMEOUT] ID: {flow.id}")
                    flow.kill()
                    return

                else:
                    flow.kill()  # Block on error
                    
            except Exception as e:
                self.payment_logger.error(f"[Request Processing Error] ID: {flow.id}, Error: {e}")
                flow.kill()
                return
    def response(flow: http.HTTPFlow):
        """
        This function is called for every HTTP response.
        It checks if the corresponding request was a payment request and logs response details.
        """
        # Check if the original request was flagged as a payment request
        # This ensures we only log responses for requests we've already identified.
        # For a more robust check, one might store flow IDs of payment requests.
        # However, re-evaluating is_payment_request is also common.
        if self.is_payment_request(flow): # Assuming the flow object is the same and contains request details
            try:
                # Ensure response exists and has attributes before accessing them
                if flow.response and flow.response.status_code:
                    res = {
                        "id": flow.id, # Including flow ID for correlation
                        "status_code": flow.response.status_code,
                        "url": flow.request.pretty_url, # URL from the request for context
                        "headers": dict(flow.response.headers),
                        "body_snippet": flow.response.text[:1024] if flow.response.text else "" # Truncate body
                    }
                    self.payment_logger.info("[PAYMENT RESPONSE]\n" + json.dumps(res, indent=2))
                else:
                    self.payment_logger.warning(f"[PAYMENT RESPONSE SKIPPED] No response object or status code for flow ID: {flow.id}")

            except Exception as e:
                self.payment_logger.error(f"[Response Logging Error] ID: {flow.id}, Error: {e}")