import subprocess
import threading
import time
import sys
import os
from approval_mechanism import app as flask_app

# === Step 1: Start the Flask Approval Server ===
def start_flask_server():
    flask_app.run(host="0.0.0.0", port=5000, debug=False, use_reloader=False)

# === Step 2: Start Proxy by calling Proxy.py ===
def start_proxy_server():
    print("🕵️‍♂️ Starting HTTPS Proxy Server...")
    return subprocess.Popen([sys.executable, "Proxy.py"])

# === Step 3: Start Payment Filter Script ===
def start_payment_filter():
    print("💰 Starting Payment Filter Watcher...")
    return subprocess.Popen([sys.executable, "payment_filter.py"])

# === Controller Main Function ===
def main():
    try:
        # Start Flask server in background
        flask_thread = threading.Thread(target=start_flask_server, daemon=True)
        flask_thread.start()
        print("✅ Flask approval server running at http://localhost:5000")

        time.sleep(2)

        # Start Proxy and Payment Filter in parallel
        proxy_process = start_proxy_server()
        filter_process = start_payment_filter()

        # Wait for the proxy process (blocks here)
        proxy_process.wait()

    except KeyboardInterrupt:
        print("\n🛑 Shutting down Bifrost components...")
        if proxy_process:
            proxy_process.terminate()
        if filter_process:
            filter_process.terminate()
        sys.exit(0)

if __name__ == "__main__":
    main()
