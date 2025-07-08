import pytest
import sys
import os
import json
from unittest.mock import MagicMock
import mitmproxy.http
from mitmproxy.test import tflow

# Add the parent directory to path so we can import our modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import project modules
import payment_filter
from approval_mechanism import app as flask_app

@pytest.fixture
def app():
    """Create a Flask app for testing."""
    flask_app.config.update({
        "TESTING": True,
    })
    return flask_app

@pytest.fixture
def client(app):
    """Create a test client for Flask app."""
    return app.test_client()

@pytest.fixture
def payment_config():
    """Create a test PaymentFilterConfig."""
    return payment_filter.PaymentFilterConfig()

@pytest.fixture
def mock_flow():
    """Create a mock HTTP flow for testing."""
    flow = tflow.tflow()  # Create test flow from mitmproxy test utils
    return flow

@pytest.fixture
def payment_flow():
    """Create a mock HTTP flow that looks like a payment request."""
    flow = tflow.tflow(resp=True)  # Create test flow with response
    
    # Create a properly mocked request for payment
    mock_req = MagicMock()
    mock_req.url = "https://checkout.stripe.com/pay"
    mock_req.pretty_url = "https://checkout.stripe.com/pay"
    mock_req.content = b'{"card_number": "4242XXXX", "amount": 100}'
    mock_req.headers = {"Content-Type": "application/json"}
    mock_req.get_text = MagicMock(return_value='{"card_number": "4242XXXX", "amount": 100}')
    mock_req.host = "checkout.stripe.com"
    
    # Replace the request in the flow
    flow.request = mock_req
    
    return flow

@pytest.fixture
def non_payment_flow():
    """Create a mock HTTP flow that doesn't look like a payment request."""
    flow = tflow.tflow(resp=True)
    
    # Create a properly mocked request for non-payment
    mock_req = MagicMock()
    mock_req.url = "https://example.com/article"
    mock_req.pretty_url = "https://example.com/article"
    mock_req.content = b'{"title": "Test Article"}'
    mock_req.headers = {"Content-Type": "application/json"}
    mock_req.get_text = MagicMock(return_value='{"title": "Test Article"}')
    mock_req.host = "example.com"
    
    # Replace the request in the flow
    flow.request = mock_req
    
    return flow

@pytest.fixture
def mock_redis():
    """Create a mock Redis client."""
    redis_mock = MagicMock()
    # Add common Redis methods that will be used
    redis_mock.get.return_value = None
    redis_mock.set.return_value = True
    redis_mock.publish.return_value = 1
    
    return redis_mock
