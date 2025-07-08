# BiFrost Proxy Connection Troubleshooting Guide

This guide will help you set up and use the BiFrost proxy system correctly.

## Prerequisites

1. Python 3.8 or newer
2. Virtual environment (recommended)
3. Administrative privileges to install certificates (for HTTPS interception)

## Step 1: Set Up the Environment

First, make sure you're in the BiFrost ProxyVPN directory:

```bash
cd ~/Projects/BiFrost/ProxyVPN
```

Create and activate a virtual environment:

```bash
python3 -m venv venv
source venv/bin/activate
```

Install the required packages:

```bash
pip install mitmproxy requests Flask python-dotenv
```

## Step 2: Start the Basic Proxy

We've created a simple script that starts the proxy with minimal configuration:

```bash
./run_basic_proxy.py
```

This will start mitmproxy on port 8080.

## Step 3: Configure Your Browser/System to Use the Proxy

### Firefox
1. Open Firefox
2. Go to Settings (≡) > Settings/Preferences > General > Network Settings
3. Select "Manual proxy configuration"
4. Set HTTP Proxy to "localhost" and Port to "8080"
5. Check "Use this proxy server for all protocols"
6. Click "OK"

### Chrome
1. Open Chrome
2. Go to Settings > Advanced > System > Open your computer's proxy settings
3. Set up a manual proxy with:
   - HTTP proxy: localhost
   - Port: 8080
   - For Windows, use "Manual proxy setup"; for macOS, use "Web Proxy (HTTP)"

### System-wide (Linux)
1. Go to Settings > Network
2. Click on your active connection > Settings/Gear icon
3. Go to "Proxy" tab
4. Select "Manual"
5. Set HTTP and HTTPS proxy to "localhost" and port "8080"
6. Apply settings

## Step 4: Install the MITM Certificate (CRITICAL STEP)

For the proxy to intercept HTTPS traffic, you must install the mitmproxy CA certificate:

1. With the proxy running, navigate to http://mitm.it in your browser
2. Select your operating system/browser and follow the instructions
3. Download and install the certificate

### For Firefox:
- After downloading the certificate
- Go to Preferences > Privacy & Security > View Certificates > Import
- Select the downloaded certificate and check "Trust this CA to identify websites"

### For Chrome/System:
- Follow the OS-specific instructions from http://mitm.it
- Make sure to trust the certificate for website identification

## Step 5: Test the Proxy

1. With the proxy running and certificate installed, try accessing a simple HTTP website like http://example.com
2. Then try an HTTPS website like https://github.com
3. If both load correctly, your proxy setup is working!

## Common Issues and Solutions

### 1. Cannot access any websites
- Verify the proxy is running (terminal should show activity)
- Check proxy settings in your browser/system
- Try restarting your browser

### 2. HTTP sites work but HTTPS sites don't
- Certificate is not installed or not trusted
- Visit http://mitm.it and reinstall the certificate
- Make sure to mark it as trusted for identifying websites

### 3. Certificate warnings in browser
- Certificate is not installed correctly
- Try reinstalling the certificate and ensuring it's in the trusted root store

### 4. Connection refused errors
- Verify the proxy is running on the correct port (8080)
- Check for firewall issues blocking the connection
- Ensure no other application is using port 8080

### 5. Slow connections
- This is normal for proxy connections, especially for first requests
- The proxy intercepts and logs traffic which adds overhead

## Additional BiFrost Components

The full BiFrost system includes:
- Payment detection filters
- Approval mechanisms
- UI components

These require additional setup and will be covered in separate documentation.

## Reverting Proxy Settings

When you're done testing, remember to turn off the proxy in your browser/system settings to restore normal internet access.
