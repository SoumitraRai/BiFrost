import pytest
from unittest.mock import patch, MagicMock, mock_open
import numpy as np

# Import our module (assuming it exists now)
from ml_payment_detector import MLPaymentDetector

class TestMLPaymentDetector:
    """Test cases for the ML-based payment detector."""
    
    def test_init_with_model_available(self):
        """Test initialization when model is available."""
        # Mock the joblib.load calls
        with patch('ml_payment_detector.joblib.load') as mock_load:
            # Set the return values for model and vectorizer
            mock_model = MagicMock()
            mock_vectorizer = MagicMock()
            mock_load.side_effect = [mock_model, mock_vectorizer]
            
            # Create the detector
            detector = MLPaymentDetector()
            
            # Check that model was loaded
            assert detector.ml_available is True
            assert detector.model == mock_model
            assert detector.vectorizer == mock_vectorizer
    
    def test_init_with_model_unavailable(self):
        """Test initialization when model is not available."""
        # Mock the joblib.load calls to raise an exception
        with patch('ml_payment_detector.joblib.load', side_effect=FileNotFoundError):
            # Create the detector
            detector = MLPaymentDetector()
            
            # Check that ml_available is False
            assert detector.ml_available is False
    
    def test_extract_features(self, mock_flow):
        """Test feature extraction from flows."""
        detector = MLPaymentDetector()
        
        # Instead of setting pretty_url directly, mock the entire request object
        mock_request = MagicMock()
        mock_request.pretty_url = "https://example.com/checkout"
        mock_request.get_text.return_value = "payment processing"
        mock_request.headers = {
            "Content-Type": "application/json",
            "Referer": "https://example.com/cart"
        }
        
        # Replace the flow's request with our mock
        mock_flow.request = mock_request
        
        # Extract features
        features = detector.extract_features(mock_flow)
        
        # Verify that features contain all the expected information
        assert "example.com/checkout" in features.lower()
        assert "payment processing" in features.lower()
        assert "content-type:application/json" in features.lower()
        assert "referer:https://example.com/cart" in features.lower()
    
    def test_is_payment_ml_unavailable(self, mock_flow):
        """Test behavior when ML model is not available."""
        detector = MLPaymentDetector()
        detector.ml_available = False
        
        # Call is_payment
        result = detector.is_payment(mock_flow)
        
        # Should return None to fallback to rule-based approach
        assert result is None
    
    def test_is_payment_with_model(self, mock_flow):
        """Test payment detection with ML model."""
        # Create mock model and vectorizer
        mock_model = MagicMock()
        mock_vectorizer = MagicMock()
        
        # Set up the prediction probability
        mock_model.predict_proba.return_value = np.array([[0.2, 0.8]])  # 80% confidence it's a payment
        
        # Set up the vectorizer transform
        mock_vectorizer.transform.return_value = "transformed_features"
        
        with patch('ml_payment_detector.joblib.load') as mock_load:
            mock_load.side_effect = [mock_model, mock_vectorizer]
            
            detector = MLPaymentDetector()
            detector.model = mock_model
            detector.vectorizer = mock_vectorizer
            
            # Set up mock flow with a mock request object
            mock_request = MagicMock()
            mock_request.pretty_url = "https://example.com/checkout"
            mock_request.get_text.return_value = "payment processing"
            mock_request.headers = {"Content-Type": "application/json"}
            mock_flow.request = mock_request
            
            # Test with default threshold (0.6)
            result = detector.is_payment(mock_flow)
            assert result == True  # Use == instead of 'is' for NumPy boolean comparison
            
            # Test with higher threshold
            result = detector.is_payment(mock_flow, threshold=0.9)
            assert result == False  # Use == instead of 'is' for NumPy boolean comparison
            
            # Check that vectorizer.transform was called
            mock_vectorizer.transform.assert_called_with([detector.extract_features(mock_flow)])
            
            # Check that model.predict_proba was called with transformed features
            mock_model.predict_proba.assert_called_with("transformed_features")
