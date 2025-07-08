import pytest
from unittest.mock import patch, MagicMock
import time

# Import our module
from metrics import (
    track_request, 
    track_payment_request, 
    LatencyTracker,
    REQUESTS_TOTAL,
    PAYMENT_REQUESTS,
    REQUEST_LATENCY
)

class TestMetrics:
    """Test cases for the metrics module."""
    
    def test_track_request(self):
        """Test tracking a request."""
        # Mock the counter
        with patch('metrics.REQUESTS_TOTAL') as mock_counter:
            # Create a labels mock
            labels_mock = MagicMock()
            mock_counter.labels.return_value = labels_mock
            
            # Track a request
            track_request("example.com", "success")
            
            # Verify the counter was incremented correctly
            mock_counter.labels.assert_called_with(status="success", domain="example.com")
            labels_mock.inc.assert_called_once()
    
    def test_track_payment_request(self):
        """Test tracking a payment request."""
        # Mock the counter
        with patch('metrics.PAYMENT_REQUESTS') as mock_counter:
            # Create a labels mock
            labels_mock = MagicMock()
            mock_counter.labels.return_value = labels_mock
            
            # Track a payment request
            track_payment_request("stripe.com", "approved")
            
            # Verify the counter was incremented correctly
            mock_counter.labels.assert_called_with(status="approved", domain="stripe.com")
            labels_mock.inc.assert_called_once()
    
    def test_latency_tracker(self):
        """Test the latency tracker context manager."""
        # Mock time.time to return controlled values
        with patch('time.time') as mock_time:
            # First call returns start_time, second call returns end_time
            mock_time.side_effect = [100.0, 100.5]  # 0.5s elapsed
            
            # Mock the histogram
            with patch('metrics.REQUEST_LATENCY') as mock_histogram:
                # Create a labels mock
                labels_mock = MagicMock()
                mock_histogram.labels.return_value = labels_mock
                
                # Use the latency tracker
                with LatencyTracker("test_endpoint"):
                    pass  # Just context entry and exit
                
                # Verify the duration was observed correctly
                mock_histogram.labels.assert_called_with(endpoint="test_endpoint")
                labels_mock.observe.assert_called_with(0.5)  # 100.5 - 100.0 = 0.5
    
    @patch('metrics.start_http_server')
    def test_start_metrics_server(self, mock_server):
        """Test starting the metrics server."""
        from metrics import start_metrics_server
        
        # Start the server
        start_metrics_server(port=9090)
        
        # Verify the server was started
        mock_server.assert_called_with(9090)
