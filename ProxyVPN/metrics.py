# In a new file: metrics.py
from prometheus_client import Counter, Histogram, start_http_server
import time

# Define metrics
REQUESTS_TOTAL = Counter(
    'bifrost_requests_total',
    'Total number of requests processed',
    ['status', 'domain']
)

PAYMENT_REQUESTS = Counter(
    'bifrost_payment_requests_total',
    'Total number of payment requests detected',
    ['status', 'domain']
)

REQUEST_LATENCY = Histogram(
    'bifrost_request_duration_seconds',
    'Request duration in seconds',
    ['endpoint']
)

def track_request(domain, status):
    REQUESTS_TOTAL.labels(status=status, domain=domain).inc()

def track_payment_request(domain, status):
    PAYMENT_REQUESTS.labels(status=status, domain=domain).inc()

class LatencyTracker:
    def __init__(self, endpoint):
        self.endpoint = endpoint
        
    def __enter__(self):
        self.start_time = time.time()
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        duration = time.time() - self.start_time
        REQUEST_LATENCY.labels(endpoint=self.endpoint).observe(duration)

# Start metrics server
def start_metrics_server(port=8000):
    start_http_server(port)
    print(f"Prometheus metrics available at http://localhost:{port}/metrics")