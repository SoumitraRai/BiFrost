import subprocess
import threading
import time
import sys
import os
from approval_mechanism import app as flask_app

# === Step 1: Start the Flask Approval Server ===
def start_flask_server():
    flask_app.run(host="0.0.0.0", port=5000, debug=False, use_reloader=False)

# === Step 2: Start Proxy with Integrated Payment Filter ===
def start_proxy_server():
    print("🕵️‍♂️ Starting HTTPS Proxy Server with Payment Filter...")
    return subprocess.Popen([sys.executable, "Proxy.py"])

# === Controller Main Function ===
def main():
    try:
        # Start Flask server in background
        flask_thread = threading.Thread(target=start_flask_server, daemon=True)
        flask_thread.start()
        print("✅ Flask approval server running at http://localhost:5000")

        # Give Flask time to start
        time.sleep(2)

        # Start Proxy (now includes payment filter)
        proxy_process = start_proxy_server()
        print("✅ Proxy server with payment filter running at localhost:8080")

        # Wait for the proxy process
        proxy_process.wait()

    except KeyboardInterrupt:
        print("\n🛑 Shutting down Bifrost components...")
        if 'proxy_process' in locals():
            proxy_process.terminate()
        sys.exit(0)
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    # Check if required files exist
    required_files = ["Proxy.py", "payment_filter.py", "approval_mechanism.py"]
    for file in required_files:
        if not os.path.exists(file):
            print(f"❌ Error: Required file '{file}' not found!")
            sys.exit(1)
    
    print("🌈 Starting Bifrost System...")
    main()
