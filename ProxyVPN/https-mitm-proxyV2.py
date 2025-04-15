import asyncio
import mitmproxy.http
import mitmproxy.ctx
import logging
import json
import os
import sys
from typing import Optional, Dict, Any
from mitmproxy import options
from mitmproxy.tools.dump import DumpMaster

class AdvancedHTTPSProxy:
    def __init__(self, 
                 host: str = '0.0.0.0', 
                 port: int = 8080, 
                 log_dir: str = 'proxy_logs',
                 cert_dir: str = 'certs',
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
            'blacklist_domains': [],  # Domains to ignore
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
            # Configure mitmproxy options with basic certificate generation
            opts = options.Options(
                listen_host=self.host,
                listen_port=self.port,
                confdir=self.cert_dir,         # Directory for mitmproxy configuration and certs
                ssl_insecure=True,             # Allow invalid certificates
                # Basic certificate options
                ssl_verify_upstream_trusted_ca=os.path.join(self.cert_dir, 'mitmproxy-ca.pem'),
                add_upstream_certs_to_client_chain=True
            )
            
            # Create the proxy master
            self.master = DumpMaster(opts)
            self.master.addons.add(self)
            
            self.logger.info(f"HTTPS Proxy started on {self.host}:{self.port}")
            self.logger.info(f"Certificate authority files will be stored in {self.cert_dir}")
            self.logger.info(f"Install the CA certificate from {os.path.join(self.cert_dir, 'mitmproxy-ca-cert.pem')} on your clients")
            
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


def main():
    # Example configuration
    proxy_config = {
        'intercept_all': True,
        'whitelist_domains': ['github.com', 'example.com'],
        'log_requests': True,
        'log_responses': True,
        'save_files': True
    }
    
    proxy = AdvancedHTTPSProxy(config=proxy_config)
    proxy.run()

if __name__ == "__main__":
    main()