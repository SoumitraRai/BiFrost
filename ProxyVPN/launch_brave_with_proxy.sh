#!/usr/bin/env bash
# This script launches Brave with certificate bypass for mitmproxy

CERT_PATH="./certs/mitmproxy-ca-cert.pem"
if [ ! -f "$CERT_PATH" ]; then
    CERT_PATH="$HOME/.mitmproxy/mitmproxy-ca-cert.pem"
    if [ ! -f "$CERT_PATH" ]; then
        echo "❌ mitmproxy certificate not found!"
        echo "Please run the proxy first to generate certificates."
        exit 1
    fi
fi

# Check if Brave is installed
if ! command -v brave-browser &> /dev/null; then
    echo "❌ brave-browser command not found."
    if command -v brave &> /dev/null; then
        BRAVE_CMD="brave"
    else
        echo "Could not find Brave browser. Is it installed?"
        exit 1
    fi
else
    BRAVE_CMD="brave-browser"
fi

# Generate the certificate fingerprint
CERT_HASH=$(openssl x509 -noout -pubkey -in "$CERT_PATH" | openssl pkey -pubin -outform der | openssl dgst -sha256 -binary | base64)

echo "Launching Brave with certificate bypass for mitmproxy..."
echo "Certificate: $CERT_PATH"
echo "Certificate hash: $CERT_HASH"

# Launch Brave with certificate bypass
$BRAVE_CMD --ignore-certificate-errors-spki-list="$CERT_HASH" "$@"
