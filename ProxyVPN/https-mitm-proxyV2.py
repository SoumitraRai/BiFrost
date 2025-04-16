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
                 log_dir: str = '../bifrost-ui/public/proxy_logs',  # Changed this for our project
                 cert_dir: str = 'certs',
                 config: Optional[Dict[str, Any]] = None):
        """
        Starting the HTTPS proxy with options we can change
        
        host - where to listen (default is everywhere)
        port - which port to use
        log_dir - where to save our logs
        cert_dir - where to keep our certificates
        config - other settings we might want to change
        """
        self.host = host
        self.port = port
        self.log_dir = log_dir
        self.cert_dir = cert_dir
        
        # Making folders if they don't exist yet
        os.makedirs(log_dir, exist_ok=True)
        os.makedirs(cert_dir, exist_ok=True)
        
        # Default settings
        self.config = {
            'intercept_all': False,  # Grab everything
            'whitelist_domains': [],  # Only intercept these websites
            'blacklist_domains': [],  # Ignore these websites
            'log_requests': True,
            'log_responses': True,
            'max_log_size': 1024 * 1024,  # 1MB per file should be enough
            'save_files': False,  # Save stuff we intercept
            'file_save_dir': os.path.join(log_dir, 'files')
        }
        
        # Use custom config if provided
        if config:
            self.config.update(config)
        
        # Setting up logs
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s: %(message)s',
            handlers=[
                logging.FileHandler(os.path.join(log_dir, 'proxy.log')),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
        
        self.master = None
    
    def should_intercept(self, flow: mitmproxy.http.HTTPFlow) -> bool:
        """
        Decides if we should capture this request
        """
        # Check if in whitelist
        if self.config['whitelist_domains']:
            return any(domain in flow.request.host for domain in self.config['whitelist_domains'])
        
        # Check if in blacklist
        if self.config['blacklist_domains']:
            return not any(domain in flow.request.host for domain in self.config['blacklist_domains'])
        
        # Default to whatever we set
        return self.config['intercept_all']
    
    def log_request(self, flow: mitmproxy.http.HTTPFlow):
        """
        Save request details to our log
        """
        if not self.config['log_requests']:
            return
        
        request_log = {
            'method': flow.request.method,
            'url': flow.request.url,
            'headers': dict(flow.request.headers),
        }
        
        # Try to get the body text
        try:
            request_log['body'] = flow.request.text
        except:
            request_log['body_length'] = len(flow.request.content)
        
        self.logger.info(f"Request: {json.dumps(request_log, indent=2)}")
    
    def log_response(self, flow: mitmproxy.http.HTTPFlow):
        """
        Save response details from server
        """
        if not self.config['log_responses']:
            return
        
        response_log = {
            'status_code': flow.response.status_code,
            'url': flow.request.url,
            'headers': dict(flow.response.headers),
        }
        
        # Try to get the body text
        try:
            # Not saving huge responses
            response_log['body'] = flow.response.text[:1024]
        except:
            response_log['body_length'] = len(flow.response.content)
        
        self.logger.info(f"Response: {json.dumps(response_log, indent=2)}")
    
    def save_intercepted_file(self, flow: mitmproxy.http.HTTPFlow):
        """
        Save files we intercept
        """
        if not self.config['save_files']:
            return
        
        os.makedirs(self.config['file_save_dir'], exist_ok=True)
        
        # Make a filename that won't break things
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
        Handle incoming requests
        """
        if self.should_intercept(flow):
            self.log_request(flow)
    
    def response(self, flow: mitmproxy.http.HTTPFlow):
        """
        Handle server responses
        """
        if self.should_intercept(flow):
            self.log_response(flow)
            self.save_intercepted_file(flow)
    
    async def run_proxy(self):
        """
        Start the proxy server
        """
        try:
            # Set up mitmproxy options
            opts = options.Options(
                listen_host=self.host,
                listen_port=self.port,
                confdir=self.cert_dir,         # Where to store config and certs
                ssl_insecure=True,             # Don't be picky about certificates
                ssl_verify_upstream_trusted_ca=os.path.join(self.cert_dir, 'mitmproxy-ca.pem'),
                add_upstream_certs_to_client_chain=True
            )
            
            # Create the proxy
            self.master = DumpMaster(opts)
            self.master.addons.add(self)
            
            self.logger.info(f"HTTPS Proxy started on {self.host}:{self.port}")
            self.logger.info(f"Certificate authority files will be stored in {self.cert_dir}")
            self.logger.info(f"Install the CA certificate from {os.path.join(self.cert_dir, 'mitmproxy-ca-cert.pem')} on your clients")
            self.logger.info(f"Logs will be stored in {os.path.join(self.log_dir, 'proxy.log')}")
            
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
        Run the proxy using asyncio
        """
        try:
            # Windows needs ProactorEventLoop
            if sys.platform == "win32":
                try:
                    asyncio.set_event_loop(asyncio.ProactorEventLoop())
                except AttributeError:
                    # For newer Python
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
    # My example settings
    proxy_config = {
        'intercept_all': True,
        'whitelist_domains': ['github.com', 'example.com'],
        'log_requests': True,
        'log_responses': True,
        'save_files': True,
        'file_save_dir': 'bifrost-ui/public/proxy_logs/'  # Changed this path for our project
    }
    
    proxy = AdvancedHTTPSProxy(config=proxy_config)
    proxy.run()

if __name__ == "__main__":
    main()