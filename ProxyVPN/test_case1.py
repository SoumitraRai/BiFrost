import requests
import random
import time
import uuid
from concurrent.futures import ThreadPoolExecutor
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class ApprovalTester:
    def __init__(self, base_url="http://localhost:5000"):
        self.base_url = base_url
        self.test_urls = [
            "https://paypal.com/checkout",
            "https://stripe.com/payment",
            "https://razorpay.com/pay",
            "https://secure.payment.com/process",
            "https://bank.com/transfer"
        ]
    
    def generate_request(self):
        """Generate a random payment request"""
        flow_id = str(uuid.uuid4())
        url = random.choice(self.test_urls)
        
        data = {
            "id": flow_id,
            "data": {
                "url": url,
                "method": "GET",
                "headers": {
                    "User-Agent": "TestBot/1.0",
                    "Accept": "application/json"
                }
            }
        }
        
        try:
            response = requests.post(
                f"{self.base_url}/intercepted",
                json=data
            )
            if response.status_code == 200:
                logger.info(f"Request created: {flow_id} -> {url}")
                return flow_id
            else:
                logger.error(f"Failed to create request: {response.status_code}")
                return None
        except Exception as e:
            logger.error(f"Error generating request: {e}")
            return None

    def make_random_decision(self, flow_id):
        """Make a random approve/deny decision"""
        time.sleep(random.uniform(1, 5))  # Random delay
        decision = random.choice(["approve", "deny"])
        
        try:
            response = requests.post(
                f"{self.base_url}/decision",
                json={"id": flow_id, "action": decision}
            )
            if response.status_code == 200:
                logger.info(f"Decision made for {flow_id}: {decision}")
            else:
                logger.error(f"Failed to make decision: {response.status_code}")
        except Exception as e:
            logger.error(f"Error making decision: {e}")

    def check_decision(self, flow_id):
        """Check the decision status for a flow"""
        try:
            response = requests.get(
                f"{self.base_url}/decision/{flow_id}"
            )
            if response.status_code == 200:
                result = response.json()
                return result.get("decision")
            return None
        except Exception as e:
            logger.error(f"Error checking decision: {e}")
            return None

    def run_test_scenario(self, num_requests=5, max_workers=3):
        """Run a complete test scenario"""
        logger.info(f"Starting test scenario with {num_requests} requests")
        
        # Generate requests
        flow_ids = []
        for _ in range(num_requests):
            flow_id = self.generate_request()
            if flow_id:
                flow_ids.append(flow_id)
            time.sleep(random.uniform(0.5, 2))  # Random delay between requests
        
        # Make decisions in parallel
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            executor.map(self.make_random_decision, flow_ids)
        
        # Wait a moment for decisions to be processed
        time.sleep(2)
        
        # Check final decisions
        logger.info("\nFinal Decisions:")
        for flow_id in flow_ids:
            decision = self.check_decision(flow_id)
            logger.info(f"Flow {flow_id}: {decision or 'pending'}")
        
        logger.info("Test scenario completed")

def main():
    tester = ApprovalTester()
    
    # Run multiple test scenarios
    scenarios = [
        {"num_requests": 3, "max_workers": 2},
        {"num_requests": 5, "max_workers": 3},
        {"num_requests": 10, "max_workers": 4}
    ]
    
    for i, scenario in enumerate(scenarios, 1):
        logger.info(f"\nRunning scenario {i}")
        logger.info(f"Requests: {scenario['num_requests']}, Workers: {scenario['max_workers']}")
        tester.run_test_scenario(**scenario)
        time.sleep(2)  # Pause between scenarios

if __name__ == "__main__":
    main()