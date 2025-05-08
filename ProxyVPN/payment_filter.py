import os
import json
import logging
import requests
from mitmproxy import http

LOG_DIR = '../bifrost-ui/public/proxy_logs'
PAYMENT_LOG_FILE = os.path.join(LOG_DIR, 'payment_traffic.log')

# Create the directory if it doesn't exist
os.makedirs(LOG_DIR, exist_ok=True)

# Setup logger for payment filter
payment_logger = logging.getLogger("payment_filter")
payment_logger.setLevel(logging.INFO)

# Configure handlers only if they haven't been added already
if not payment_logger.handlers:
    # File handler to log to a file
    file_handler = logging.FileHandler(PAYMENT_LOG_FILE)
    file_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s: %(message)s'))

    # Stream handler to log to the console
    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s: %(message)s'))

    # Add handlers to the logger
    payment_logger.addHandler(file_handler)
    payment_logger.addHandler(stream_handler)

def is_payment_request(flow: http.HTTPFlow) -> bool:
    """
    Determines if an HTTP flow is related to a payment transaction.
    """
    try:
        url = flow.request.pretty_url.lower()
        headers = flow.request.headers
        content = flow.request.get_text().lower() if flow.request.content else ""

        payment_domains = [
            "paypal", "stripe", "razorpay", "paytm", "phonepe", "gpay",
            "apple.com/payment", "google.com/pay", "checkout", "secure.pay"
        ]
        payment_keywords = [
            "payment", "transaction", "card", "wallet", "upi", "purchase",
            "order", "billing", "credit", "debit", "checkout", "pay"
        ]

        # Check if the URL matches any payment domains
        if any(domain in url for domain in payment_domains):
            return True

        # Combine content and headers for keyword searching
        combined_text = content + " " + " ".join(f"{k.lower()}:{v.lower()}" for k, v in headers.items())
        if any(keyword in combined_text for keyword in payment_keywords):
            return True

    except Exception as e:
        payment_logger.error(f"[Detection Error in is_payment_request] {e}")
        return False  # Return False if an error occurs during detection

    return False # Return False if no payment indicators are found

def request(flow: http.HTTPFlow):
    """
    This function is called for every HTTP request.
    It checks if the request is a payment request and logs relevant information.
    """
    if is_payment_request(flow):
        try:
            req = {
                "id": flow.id,
                "method": flow.request.method,
                "url": flow.request.pretty_url,
                "headers": dict(flow.request.headers),
                "content": flow.request.get_text() if flow.request.content else ""
            }
            payment_logger.info("[PAYMENT REQUEST]\n" + json.dumps(req, indent=2))

            # Try to send the request details to an approval server
            try:
                r = requests.post("http://localhost:5000/intercepted", json=req, timeout=5)
                if r.status_code == 200:
                    payment_logger.info(f"[SENT TO APPROVAL SERVER] ID: {flow.id}")
                else:
                    payment_logger.warning(f"[FAILED TO SEND TO APPROVAL SERVER] ID: {flow.id}, Status: {r.status_code}, Response: {r.text[:200]}")
            except requests.exceptions.RequestException as e: # More specific exception for network errors
                payment_logger.error(f"[ERROR SENDING TO APPROVAL SERVER] ID: {flow.id}, Error: {e}")
            except Exception as e: # Catch other potential exceptions
                payment_logger.error(f"[UNEXPECTED ERROR SENDING TO APPROVAL SERVER] ID: {flow.id}, Error: {e}")

        except Exception as e:
            payment_logger.error(f"[Request Logging Error] ID: {flow.id}, Error: {e}")

def response(flow: http.HTTPFlow):
    """
    This function is called for every HTTP response.
    It checks if the corresponding request was a payment request and logs response details.
    """
    # Check if the original request was flagged as a payment request
    # This ensures we only log responses for requests we've already identified.
    # For a more robust check, one might store flow IDs of payment requests.
    # However, re-evaluating is_payment_request is also common.
    if is_payment_request(flow): # Assuming the flow object is the same and contains request details
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
                payment_logger.info("[PAYMENT RESPONSE]\n" + json.dumps(res, indent=2))
            else:
                payment_logger.warning(f"[PAYMENT RESPONSE SKIPPED] No response object or status code for flow ID: {flow.id}")

        except Exception as e:
            payment_logger.error(f"[Response Logging Error] ID: {flow.id}, Error: {e}")