import pytest
import json
from unittest.mock import patch, MagicMock
import time

# Approval mechanism is imported via the flask_app fixture from conftest.py

class TestApprovalMechanism:
    """Test cases for the approval mechanism Flask app."""
    
    def test_intercepted_endpoint(self, client):
        """Test the /intercepted endpoint."""
        # Test data
        test_data = {
            "id": "test123",
            "url": "https://stripe.com/payment",
            "method": "POST"
        }
        
        # Send POST request to /intercepted
        response = client.post('/intercepted', 
                              json=test_data,
                              headers={"X-API-Key": "default-dev-key-change-this"})
        
        # Check response
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["status"] == "waiting"
        assert data["id"] == "test123"
        
    def test_get_pending_requests(self, client):
        """Test the /requests endpoint."""
        # First add a pending request
        test_data = {
            "id": "test456",
            "url": "https://paypal.com/checkout",
            "method": "POST"
        }
        
        # Send POST to add a pending request
        client.post('/intercepted', 
                   json=test_data,
                   headers={"X-API-Key": "default-dev-key-change-this"})
        
        # Now get the pending requests
        response = client.get('/requests',
                            headers={"X-API-Key": "default-dev-key-change-this"})
        
        # Check response
        assert response.status_code == 200
        data = json.loads(response.data)
        assert isinstance(data, list)
        
        # Check that our test request is in the list
        found = False
        for req in data:
            if req["id"] == "test456":
                found = True
                assert req["details"]["url"] == "https://paypal.com/checkout"
                break
        
        assert found is True
        
    def test_make_decision(self, client):
        """Test the /decision endpoint for making decisions."""
        # First add a pending request
        test_data = {
            "id": "test789",
            "url": "https://example.com/payment",
            "method": "POST"
        }
        
        # Send POST to add a pending request
        client.post('/intercepted', 
                   json=test_data,
                   headers={"X-API-Key": "default-dev-key-change-this"})
        
        # Now make a decision
        decision_data = {
            "id": "test789",
            "action": "approve"
        }
        
        response = client.post('/decision', 
                              json=decision_data,
                              headers={"X-API-Key": "default-dev-key-change-this"})
        
        # Check response
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["status"] == "received"
        
        # Now check that the decision was recorded
        response = client.get('/decision/test789',
                             headers={"X-API-Key": "default-dev-key-change-this"})
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["decision"] == "approve"
        
    def test_get_missing_decision(self, client):
        """Test getting a decision for a flow that doesn't exist."""
        response = client.get('/decision/nonexistent',
                             headers={"X-API-Key": "default-dev-key-change-this"})
        
        assert response.status_code == 404
        data = json.loads(response.data)
        assert "error" in data
        
    @patch('time.sleep', return_value=None)  # Don't actually sleep in tests
    def test_wait_for_decision_with_timeout(self, mock_sleep, client):
        """Test the /wait_decision endpoint with timeout."""
        # We'll mock time.time to simulate timeout
        with patch('time.time') as mock_time:
            # First return start time, then timeout reached
            mock_time.side_effect = [100, 131]  # 31s elapsed (more than 30s timeout)
            
            response = client.get('/wait_decision/nonexistent',
                                 headers={"X-API-Key": "default-dev-key-change-this"})
            
            assert response.status_code == 408  # Request Timeout
            data = json.loads(response.data)
            assert data["error"] == "timeout"
            assert data["decision"] == "deny"
            
    def test_wait_for_decision_immediate_response(self, client):
        """Test the /wait_decision endpoint with immediate decision."""
        # Add a request with an immediate decision
        test_data = {
            "id": "test999",
            "url": "https://example.com/payment",
            "method": "POST"
        }
        
        # Send POST to add a pending request
        client.post('/intercepted', 
                   json=test_data,
                   headers={"X-API-Key": "default-dev-key-change-this"})
        
        # Make a decision
        decision_data = {
            "id": "test999",
            "action": "deny"
        }
        
        client.post('/decision', 
                   json=decision_data,
                   headers={"X-API-Key": "default-dev-key-change-this"})
        
        # Now wait for the decision (should return immediately)
        response = client.get('/wait_decision/test999',
                             headers={"X-API-Key": "default-dev-key-change-this"})
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["decision"] == "deny"
