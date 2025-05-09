import asyncio
import mitmproxy.http
import mitmproxy.ctx
import logging
import json
import os
import sys
import requests
import time
from typing import Optional, Dict, Any
from mitmproxy import options
from mitmproxy.tools.dump import DumpMaster
import payment_filter


class AdvancedHTTPSProxy:
    def __init__(self, 
                 host: str = '0.0.0.0', 
                 port: int = 8080, 
                 log_dir: str = '../bifrost-ui/public/proxy_logs',  # Changed log directory
                 cert_dir: str = './certs',
                 config: Optional[Dict[str, Any]] = None):
        """
        Initialize the advanced HTTPS proxy with configurable options
        
        Args:
            host (str): Proxy listening host
            port (int): Proxy listening port
            log_dir (str): Directory to store logs and intercepted traffic
            cert_dir (str): Directory to store generated certificates
            config (dict): Configuration dictionary for advanced settings
        """
        self.host = host
        self.port = port
        self.log_dir = log_dir
        self.cert_dir = cert_dir
        
        # Create log and cert directories if they don't exist
        os.makedirs(log_dir, exist_ok=True)
        os.makedirs(cert_dir, exist_ok=True)
        
        # Default configuration
        self.config = {
            'intercept_all': False,  # Intercept all traffic
            'whitelist_domains': [],  # Domains to specifically intercept
            'blacklist_domains': ['github.com'],  # Domains to ignore
            'log_requests': True,
            'log_responses': True,
            'max_log_size': 1024 * 1024,  # 1MB max log size per file
            'save_files': False,  # Save intercepted files
            'file_save_dir': os.path.join(log_dir, 'files')
        }
        
        # Update with provided configuration
        if config:
            self.config.update(config)
        
        # Setup logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s: %(message)s',
            handlers=[
                logging.FileHandler(os.path.join(log_dir, 'proxy.log')),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
        
        # Proxy master 
        self.master = None

        # Initialize the payment filter
        self.payment_filter = payment_filter

        # Initialize metrics
        self.metrics = {
            'requests_total': 0,
            'payments_intercepted': 0,
            'errors': 0
        }

    def should_intercept(self, flow: mitmproxy.http.HTTPFlow) -> bool:
        """
        Determine whether a request should be intercepted based on configuration
        
        Args:
            flow (HTTPFlow): The HTTP flow to check
        
        Returns:
            bool: Whether the flow should be intercepted
        """
        # Check if the domain is in whitelist
        if self.config['whitelist_domains']:
            return any(domain in flow.request.host for domain in self.config['whitelist_domains'])
        
        # Check if the domain is in blacklist
        if self.config['blacklist_domains']:
            return not any(domain in flow.request.host for domain in self.config['blacklist_domains'])
        
        # Default to intercept_all setting
        return self.config['intercept_all']
    
    def log_request(self, flow: mitmproxy.http.HTTPFlow):
        """
        Log details of an HTTP request flow (HTTPFlow): The HTTP flow containing request details
        """
        if not self.config['log_requests']:
            return
        
        request_log = {
            'method': flow.request.method,
            'url': flow.request.url,
            'headers': dict(flow.request.headers),
        }
        
        # Try to decode and log body if possible
        try:
            request_log['body'] = flow.request.text
        except:
            request_log['body_length'] = len(flow.request.content)
        
        self.logger.info(f"Request: {json.dumps(request_log, indent=2)}")
    
    def log_response(self, flow: mitmproxy.http.HTTPFlow):
        """
        Log details of an HTTP response
        
        flow (HTTPFlow): The HTTP flow containing response details
        """
        if not self.config['log_responses']:
            return
        
        response_log = {
            'status_code': flow.response.status_code,
            'url': flow.request.url,
            'headers': dict(flow.response.headers),
        }
        
        # Try to decode and log body if possible
        try:
            # Limit response body logging to prevent massive logs
            response_log['body'] = flow.response.text[:1024]
        except:
            response_log['body_length'] = len(flow.response.content)
        
        self.logger.info(f"Response: {json.dumps(response_log, indent=2)}")
    
    def save_intercepted_file(self, flow: mitmproxy.http.HTTPFlow):
        """
        Save files from intercepted requests/responses
        flow (HTTPFlow): The HTTP flow to save
        """
        if not self.config['save_files']:
            return
        
        os.makedirs(self.config['file_save_dir'], exist_ok=True)
        
        # Generate a safe filename
        filename = f"{flow.request.host}_{flow.request.path.replace('/', '_')}"
        filepath = os.path.join(self.config['file_save_dir'], filename)
        
        try:
            # Save request
            with open(f"{filepath}_request.txt", 'wb') as f:
                f.write(flow.request.content)
            
            # Save response
            with open(f"{filepath}_response.txt", 'wb') as f:
                f.write(flow.response.content)
        except Exception as e:
            self.logger.error(f"Error saving file: {e}")
    
    def request(self, flow: mitmproxy.http.HTTPFlow):
        """
        Intercept and process requests
        flow (HTTPFlow): The HTTP flow to process
        """
        if self.should_intercept(flow):
            self.log_request(flow)

        # Check with backend: is this flow flagged for approval?
        try:
            res = requests.get(f"http://localhost:5000/decision/{flow.id}")
            if res.status_code == 200 and res.json().get("decision") is None:
                self.logger.info(f"[⏸] Flow {flow.id} flagged for parent approval")
                flow.intercept()
                self.wait_for_decision(flow)
        except Exception as e:
            self.logger.error(f"[!] Error checking approval status for {flow.id}: {e}")
    
    def response(self, flow: mitmproxy.http.HTTPFlow):
        """
        Intercept and process responses
        flow (HTTPFlow): The HTTP flow to process
        """
        if self.should_intercept(flow):
            self.log_response(flow)
            self.save_intercepted_file(flow)
    
    async def run_proxy(self):
        """
        Async method to run the proxy server
        """
        try:
            # Configure mitmproxy options
            opts = options.Options(
                listen_host=self.host,
                listen_port=self.port,
                confdir=self.cert_dir,
                ssl_insecure=True
            )
            
            # Create the proxy master
            self.master = DumpMaster(opts)
            
            # Add payment filter addon
            self.master.addons.add(self.payment_filter)
            
            # Add self as addon for other proxy functionalities
            self.master.addons.add(self)
            
            self.logger.info(f"HTTPS Proxy started on {self.host}:{self.port}")
            self.logger.info("Payment filter activated")
            
            await self.master.run()
            
        except Exception as e:
            self.logger.error(f"Proxy server error: {e}")
            raise

        
        finally:
            if self.master:
                self.master.shutdown()
                self.logger.info("Proxy server shutting down.")
    
    def run(self):
        """
        Run the proxy server using asyncio
        """
        try:
            # Use ProactorEventLoop for better async handling on Windows
            if sys.platform == "win32":
                try:
                    asyncio.set_event_loop(asyncio.ProactorEventLoop())
                except AttributeError:
                    # For newer Python versions
                    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
            else:
                asyncio.set_event_loop_policy(asyncio.DefaultEventLoopPolicy())

            loop = asyncio.get_event_loop()
            loop.run_until_complete(self.run_proxy())

        except KeyboardInterrupt:
            self.logger.info("Proxy server manually stopped.")
        except Exception as e:
            self.logger.error(f"Proxy startup error: {e}")
            sys.exit(1)
        finally:
            if self.master:
                self.master.shutdown()
                self.logger.info("Proxy server stopped.")

    async def health_check(self):
        """Health check endpoint"""
        return {
            'status': 'healthy',
            'metrics': self.metrics,
            'uptime': time.time() - self.start_time
        }
    
    def wait_for_decision(self, flow_id: str) -> bool:
        """
        Wait for a decision from the approval mechanism
        Returns True if approved, False if denied or timeout
        """
        try:
            response = requests.get(
                f"http://localhost:5000/wait_decision/{flow_id}",
                timeout=35  # Slightly longer than approval mechanism timeout
            )
            
            if response.status_code == 200:
                decision = response.json().get("decision")
                return decision == "approve"
            
            return False  # Any other response means deny
            
        except Exception as e:
            self.logger.error(f"Error waiting for decision: {e}")
            return False  # Fail closed (deny on error)


def main():
    # Example configuration
    proxy_config = {
        'intercept_all': True,
        'whitelist_domains': ['example.com'],
        'log_requests': True,
        'log_responses': True,
        'save_files': True,
        # You can override the file save directory if needed
        # 'file_save_dir': '../bifrost-ui/public/proxy_logs'
    }
    
    proxy = AdvancedHTTPSProxy(config=proxy_config)
    proxy.run()

if __name__ == "__main__":
    main()