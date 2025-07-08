#!/usr/bin/env bash
# Helper script to install mitmproxy certificate for Brave Browser

echo "BiFrost Proxy Certificate Installer for Brave"
echo "=============================================="

# Check if certutil is available
if ! command -v certutil &> /dev/null; then
    echo "❌ certutil not found. Installing libnss3-tools..."
    sudo apt-get update && sudo apt-get install -y libnss3-tools
    if [ $? -ne 0 ]; then
        echo "❌ Failed to install libnss3-tools. Please install it manually."
        exit 1
    fi
fi

# Locate the certificate
CERT_PATH="./certs/mitmproxy-ca-cert.pem"
if [ ! -f "$CERT_PATH" ]; then
    CERT_PATH="$HOME/.mitmproxy/mitmproxy-ca-cert.pem"
    if [ ! -f "$CERT_PATH" ]; then
        echo "❌ mitmproxy certificate not found!"
        echo "Please run the proxy first to generate certificates."
        exit 1
    fi
fi

echo "✅ Found certificate at: $CERT_PATH"

# Find Brave's NSS database directories
echo "Looking for Brave's certificate databases..."
NSS_DIRS=$(find ~/.config/BraveSoftware -name "cert*.db" 2>/dev/null | xargs -n1 dirname | sort | uniq)

if [ -z "$NSS_DIRS" ]; then
    echo "❌ Could not find Brave's certificate databases."
    echo "Is Brave installed and has it been run at least once?"
    
    # Offer to install in system store
    read -p "Would you like to install the certificate in the system store instead? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo "Installing in system store..."
        sudo cp "$CERT_PATH" /usr/local/share/ca-certificates/mitmproxy-ca.crt
        sudo update-ca-certificates
        echo "✅ Certificate installed in system store. Please restart Brave."
    fi
    
    # Offer alternative method
    echo
    echo "Alternatively, you can start Brave with certificate bypass using:"
    echo "brave-browser --ignore-certificate-errors-spki-list=\$(openssl x509 -noout -pubkey -in $CERT_PATH | openssl pkey -pubin -outform der | openssl dgst -sha256 -binary | base64)"
    
    exit 1
fi

# Install the certificate in each database found
echo "Found Brave certificate databases in:"
for NSS_DIR in $NSS_DIRS; do
    echo "  $NSS_DIR"
    echo "Installing certificate..."
    certutil -d "sql:$NSS_DIR" -A -t "C,," -n "mitmproxy" -i "$CERT_PATH"
    if [ $? -ne 0 ]; then
        echo "❌ Failed to install certificate in $NSS_DIR"
    else
        echo "✅ Certificate installed in $NSS_DIR"
    fi
done

echo
echo "Certificate installation complete!"
echo "Please restart Brave browser and ensure it's configured to use the proxy:"
echo "  - Settings > System > Open your computer's proxy settings"
echo "  - Set HTTP and HTTPS proxy to localhost:8080"
echo
echo "To test, visit https://example.com in Brave"
echo "You can also visit http://mitm.it to verify the proxy connection"
