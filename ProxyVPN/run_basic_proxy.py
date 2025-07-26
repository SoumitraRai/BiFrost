#!/usr/bin/env python3
"""
Basic proxy runner for BiFrost
"""

import os
import sys
import logging
import subprocess

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s: %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("bifrost")

def run_mitmdump():
    """Run mitmproxy in dump mode"""
    try:
        logger.info("Starting mitmproxy on port 8080...")
        
        # Create the certs directory if it doesn't exist
        os.makedirs("certs", exist_ok=True)
        
        # Run mitmdump with basic configuration
        cmd = [
            "mitmdump",
            "--ssl-insecure",  # Allow invalid certificates - helpful for testing
            "--listen-host", "0.0.0.0",
            "--listen-port", "8080",
            "--set", "confdir=./certs"
        ]
        
        logger.info(f"Running command: {' '.join(cmd)}")
        
        # Execute mitmdump as a subprocess
        process = subprocess.Popen(cmd)
        
        logger.info("Mitmdump started. Configure your browser/system to use localhost:8080 as proxy")
        logger.info("Visit http://mitm.it in your browser to download and install the certificates")
        
        # Wait for the process to complete or be interrupted
        process.wait()
    
    except KeyboardInterrupt:
        logger.info("Stopping proxy server...")
    except Exception as e:
        logger.error(f"Error running proxy: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(run_mitmdump())
