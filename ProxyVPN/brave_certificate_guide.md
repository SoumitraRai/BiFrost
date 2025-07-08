# Installing mitmproxy Certificate in Brave Browser

Brave uses the Chrome certificate store system, which is different from Firefox. Here's how to install the mitmproxy certificate in Brave:

## Method 1: Using the System Certificate Store (Recommended)

1. Install the certificate in your system certificate store first:
   ```
   ./install_certificate.py
   ```

2. For Linux systems, after running the installer, you might need to restart Brave to pick up the new certificate.

## Method 2: Import Directly into Brave

1. With the proxy configured in Brave, visit: http://mitm.it

2. Click on the appropriate icon for your operating system to download the certificate.

3. Open Brave Settings (three lines in the top-right corner)

4. Search for "certificates" in the settings search box

5. Click on "Security" in the left sidebar

6. Scroll down to "Security" section and click on "Manage certificates"

7. Go to the "Authorities" tab

8. Click "Import" and select the downloaded certificate file (mitmproxy-ca-cert.pem)

9. Check "Trust this certificate for identifying websites" and click "OK"

10. Restart Brave browser

## Method 3: Using Chrome's Certificate Store (Linux)

If you're on Linux and the above methods don't work, you can try:

1. Close Brave completely

2. Open a terminal and run:
   ```
   brave-browser --ignore-certificate-errors-spki-list=$(openssl x509 -noout -pubkey -in /home/soumitra/Projects/BiFrost/ProxyVPN/certs/mitmproxy-ca-cert.pem | openssl pkey -pubin -outform der | openssl dgst -sha256 -binary | base64)
   ```

3. This will start Brave ignoring certificate errors for the mitmproxy certificate

## Method 4: Create a Custom Certificate Configuration (Linux)

Create a custom certificate configuration for Brave:

1. Find the NSS database directories:
   ```
   find ~/.config/BraveSoftware -name "cert*.db" 2>/dev/null
   ```

2. For each directory found, import the certificate:
   ```
   certutil -d sql:~/.config/BraveSoftware/Brave-Browser/Default -A -t "C,," -n mitmproxy -i /home/soumitra/Projects/BiFrost/ProxyVPN/certs/mitmproxy-ca-cert.pem
   ```
   (Adjust paths as needed for your system)

3. Restart Brave browser

## Verifying the Certificate Installation

1. With Brave configured to use the proxy, try visiting https://example.com

2. If the page loads without certificate warnings, the configuration is working!

3. If you see certificate warnings, the certificate installation was not successful.

## Troubleshooting

1. **Certificate errors persist:** Try using Method 3 temporarily to verify the proxy works

2. **Connection refused errors:** Make sure the proxy is running (use ./check_proxy_status.py)

3. **Certificate installation issues:** Check if you have the certutil tool installed
   ```
   sudo apt-get install libnss3-tools
   ```

4. **No websites load:** Ensure the proxy settings are correctly applied in Brave

5. **Some websites don't load:** This could be normal as the proxy might block certain connections
