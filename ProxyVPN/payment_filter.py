import os
import json
import logging
from mitmproxy import http

LOG_DIR = '../bifrost-ui/public/proxy_logs'
PAYMENT_LOG_FILE = os.path.join(LOG_DIR, 'payment_traffic.log')
os.makedirs(LOG_DIR, exist_ok=True)

payment_logger = logging.getLogger("payment_filter")
payment_logger.setLevel(logging.INFO)
if not payment_logger.handlers:
    file_handler = logging.FileHandler(PAYMENT_LOG_FILE)
    file_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s: %(message)s'))
    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s: %(message)s'))
    payment_logger.addHandler(file_handler)
    payment_logger.addHandler(stream_handler)

def is_payment_request(flow: http.HTTPFlow) -> bool:
    try:
        url = flow.request.pretty_url.lower()
        headers = flow.request.headers
        content = flow.request.get_text().lower() if flow.request.content else ""
        payment_domains = ["paypal", "stripe", "razorpay", "paytm", "phonepe", "gpay", 
                           "apple.com/payment", "google.com/pay", "checkout", "secure.pay"]
        payment_keywords = ["payment", "transaction", "card", "wallet", "upi", "purchase",
                            "order", "billing", "credit", "debit", "checkout", "pay"]
        if any(domain in url for domain in payment_domains):
            return True
        combined_text = content + " " + " ".join(f"{k}:{v}" for k, v in headers.items()).lower()
        if any(keyword in combined_text for keyword in payment_keywords):
            return True
    except Exception as e:
        payment_logger.error(f"[Detection Error] {e}")
    return False

def request(flow: http.HTTPFlow):
    if is_payment_request(flow):
        try:
            req = {
                "method": flow.request.method,
                "url": flow.request.url,
                "headers": dict(flow.request.headers),
                "body": flow.request.get_text()
            }
            payment_logger.info("[PAYMENT REQUEST]\n" + json.dumps(req, indent=2))
        except Exception as e:
            payment_logger.error(f"[Request Logging Error] {e}")

def response(flow: http.HTTPFlow):
    if is_payment_request(flow):
        try:
            res = {
                "status_code": flow.response.status_code,
                "url": flow.request.url,
                "headers": dict(flow.response.headers),
                "body": flow.response.text[:1024]
            }
            payment_logger.info("[PAYMENT RESPONSE]\n" + json.dumps(res, indent=2))
        except Exception as e:
            payment_logger.error(f"[Response Logging Error] {e}")
