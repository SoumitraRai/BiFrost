import pytest
from unittest.mock import patch, MagicMock
import os
import json

# Import our modules
from Proxy import AdvancedHTTPSProxy

class TestAdvancedHTTPSProxy:
    """Test cases for the AdvancedHTTPSProxy class."""
    
    def test_init_default_config(self):
        """Test initialization with default config."""
        with patch('Proxy.os.makedirs'), \
             patch('Proxy.logging'):
            proxy = AdvancedHTTPSProxy()
            
            # Check default values
            assert proxy.host == '0.0.0.0'
            assert proxy.port == 8080
            assert proxy.config is not None
            assert 'whitelist_domains' in proxy.config
            assert 'blacklist_domains' in proxy.config
            assert 'github.com' in proxy.config['blacklist_domains']
    
    def test_init_custom_config(self):
        """Test initialization with custom config."""
        custom_config = {
            'intercept_all': True,
            'whitelist_domains': ['example.com', 'test.com'],
            'blacklist_domains': [],
            'log_requests': False
        }
        
        with patch('Proxy.os.makedirs'), \
             patch('Proxy.logging'):
            proxy = AdvancedHTTPSProxy(
                host='127.0.0.1',
                port=9090,
                config=custom_config
            )
            
            # Check custom values
            assert proxy.host == '127.0.0.1'
            assert proxy.port == 9090
            assert proxy.config['intercept_all'] is True
            assert proxy.config['whitelist_domains'] == ['example.com', 'test.com']
            assert proxy.config['blacklist_domains'] == []
            assert proxy.config['log_requests'] is False
    
    def test_should_intercept_whitelist(self, mock_flow):
        """Test should_intercept with whitelist domains."""
        with patch('Proxy.os.makedirs'), \
             patch('Proxy.logging'):
            proxy = AdvancedHTTPSProxy(config={
                'whitelist_domains': ['example.com'],
                'blacklist_domains': []
            })
            
            # Create a mock request for the flow
            mock_request = MagicMock()
            
            # Set flow host to match whitelist
            mock_request.host = 'example.com'
            mock_flow.request = mock_request
            assert proxy.should_intercept(mock_flow) is True
            
            # Set flow host to not match whitelist
            mock_request = MagicMock()
            mock_request.host = 'google.com'
            mock_flow.request = mock_request
            assert proxy.should_intercept(mock_flow) is False
    
    def test_should_intercept_blacklist(self, mock_flow):
        """Test should_intercept with blacklist domains."""
        with patch('Proxy.os.makedirs'), \
             patch('Proxy.logging'):
            proxy = AdvancedHTTPSProxy(config={
                'whitelist_domains': [],
                'blacklist_domains': ['github.com'],
                'intercept_all': True
            })
            
            # Create a mock request for the flow
            mock_request = MagicMock()
            
            # Set flow host to match blacklist
            mock_request.host = 'github.com'
            mock_flow.request = mock_request
            assert proxy.should_intercept(mock_flow) is False
            
            # Set flow host to not match blacklist
            mock_request = MagicMock()
            mock_request.host = 'google.com'
            mock_flow.request = mock_request
            assert proxy.should_intercept(mock_flow) is True
    
    def test_log_request(self, mock_flow):
        """Test log_request functionality."""
        with patch('Proxy.os.makedirs'), \
             patch('Proxy.logging') as mock_logging:
            # Create a logger mock
            logger_mock = MagicMock()
            
            proxy = AdvancedHTTPSProxy(config={'log_requests': True})
            proxy.logger = logger_mock
            
            # Create a mock request for the flow
            mock_request = MagicMock()
            mock_request.method = 'GET'
            mock_request.url = 'https://example.com'
            mock_request.pretty_url = 'https://example.com'
            mock_request.headers = {'User-Agent': 'Test'}
            mock_request.text = 'test content'
            mock_request.get_text = MagicMock(return_value='test content')
            
            # Replace the request in the flow
            mock_flow.request = mock_request
            
            # Call the log_request method
            proxy.log_request(mock_flow)
            
            # Verify the logger was called
            logger_mock.info.assert_called_once()
            
            # Check that logging was bypassed when disabled
            logger_mock.reset_mock()
            proxy.config['log_requests'] = False
            proxy.log_request(mock_flow)
            logger_mock.info.assert_not_called()
    
    def test_log_response(self, mock_flow):
        """Test log_response functionality."""
        with patch('Proxy.os.makedirs'), \
             patch('Proxy.logging') as mock_logging:
            # Create a logger mock
            logger_mock = MagicMock()
            
            proxy = AdvancedHTTPSProxy(config={'log_responses': True})
            proxy.logger = logger_mock
            
            # Set up the mock flow
            mock_flow.response = MagicMock()
            mock_flow.response.status_code = 200
            mock_flow.response.headers = {'Content-Type': 'text/html'}
            mock_flow.response.text = 'response content'
            
            # Create a mock request
            mock_request = MagicMock()
            mock_request.url = 'https://example.com'
            mock_request.pretty_url = 'https://example.com'
            mock_flow.request = mock_request
            
            # Call the log_response method
            proxy.log_response(mock_flow)
            
            # Verify the logger was called
            logger_mock.info.assert_called_once()
            
            # Check that logging was bypassed when disabled
            logger_mock.reset_mock()
            proxy.config['log_responses'] = False
            proxy.log_response(mock_flow)
            logger_mock.info.assert_not_called()
    
    @patch('requests.get')
    def test_request_method_intercept(self, mock_get, mock_flow):
        """Test the request method logic with interception."""
        with patch('Proxy.os.makedirs'), \
             patch('Proxy.logging'):
            proxy = AdvancedHTTPSProxy()
            
            # Setup mock flow with intercept as a MagicMock
            mock_flow.id = 'test123'
            mock_flow.intercept = MagicMock()
            
            # Mock should_intercept to return True
            with patch.object(proxy, 'should_intercept', return_value=True):
                # Setup mock response for approval check
                mock_response = MagicMock()
                mock_response.status_code = 200
                mock_response.json.return_value = {"decision": None}
                mock_get.return_value = mock_response
                
                # Mock the logger
                proxy.logger = MagicMock()
                
                # Call the request method
                proxy.request(mock_flow)
                
                # Verify flow.intercept was called
                mock_flow.intercept.assert_called_once()
                
                # Verify the logger was called with some message
                assert proxy.logger.info.called
