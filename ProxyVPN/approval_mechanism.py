from flask import Flask, request, jsonify
from threading import Lock
import time
from functools import wraps
import os
from flask_socketio import SocketIO
import logging
from flask_cors import CORS  # Add explicit import of flask-cors

# Record start time for uptime calculation
start_time = time.time()

app = Flask(__name__)
# Apply CORS with more explicit configuration
CORS(app, resources={r"/*": {"origins": "*"}}, supports_credentials=True)

# Keep the after_request handler as an additional safety measure
@app.after_request
def after_request(response):
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization,X-API-Key')
    response.headers.add('Access-Control-Allow-Methods', 'GET,POST,OPTIONS')
    response.headers.add('Access-Control-Allow-Credentials', 'true')
    return response

# Enable SocketIO with CORS
socketio = SocketIO(app, cors_allowed_origins="*", logger=True, engineio_logger=True)

# Set up logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Store intercepted flows
pending_requests = {}
decision_lock = Lock()

API_KEY = os.getenv("API_KEY", "default-dev-key-change-this")

# Add an OPTIONS handler for all routes to support preflight requests
@app.route('/', defaults={'path': ''}, methods=['OPTIONS'])
@app.route('/<path:path>', methods=['OPTIONS'])
def handle_options(path):
    return '', 200

def require_api_key(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Skip API key check for OPTIONS requests
        if request.method == 'OPTIONS':
            return '', 200
            
        # Only enforce API key for non-GET requests
        if request.method != 'GET' and request.headers.get('X-API-Key') != API_KEY:
            logger.warning(f"Unauthorized access attempt: {request.path}")
            return jsonify({"error": "unauthorized"}), 401
        return f(*args, **kwargs)
    return decorated_function

@app.route("/intercepted", methods=["POST"])
@require_api_key
def intercepted():
    data = request.get_json()
    if not data:
        return jsonify({"error": "No JSON data provided"}), 400
        
    if "id" not in data:
        return jsonify({"error": "Missing 'id' field"}), 400
        
    flow_id = data["id"]
    with decision_lock:
        pending_requests[flow_id] = {"data": data, "decision": None}
    
    logger.info(f"Received intercepted request with ID {flow_id}")
    return jsonify({"status": "waiting", "id": flow_id})

@app.route("/requests", methods=["GET"])
def get_pending():
    logger.debug(f"GET /requests called, returning {len([k for k, v in pending_requests.items() if v['decision'] is None])} pending requests")
    
    pending = [
        {"id": k, "details": v["data"]}
        for k, v in pending_requests.items() if v["decision"] is None
    ]
    
    logger.debug(f"Pending requests data: {pending}")
    return jsonify(pending)

@app.route("/decision", methods=["POST"])
def make_decision():
    data = request.get_json()
    if not data:
        logger.error("No JSON data provided in decision request")
        return jsonify({"error": "No JSON data provided"}), 400
        
    if "id" not in data:
        logger.error("Missing 'id' field in decision request")
        return jsonify({"error": "Missing 'id' field"}), 400
        
    if "action" not in data:
        logger.error("Missing 'action' field in decision request")
        return jsonify({"error": "Missing 'action' field"}), 400
    
    flow_id = data["id"]
    action = data["action"]
    
    logger.info(f"Decision request received: ID={flow_id}, Action={action}")
    
    with decision_lock:
        if flow_id in pending_requests:
            pending_requests[flow_id]["decision"] = action
            # Emit socket event with decision
            logger.debug(f"Emitting socket event for decision_{flow_id}")
            socketio.emit(f'decision_{flow_id}', {"decision": action})
            return jsonify({"status": "received"})
    
    logger.error(f"Decision request for unknown flow ID: {flow_id}")
    return jsonify({"error": "not found"}), 404

@app.route("/decision/<flow_id>", methods=["GET"])
def get_decision(flow_id):
    with decision_lock:
        if flow_id in pending_requests:
            decision = pending_requests[flow_id].get("decision")
            return jsonify({"decision": decision})
    return jsonify({"error": "flow not found"}), 404

@app.route("/wait_decision/<flow_id>", methods=["GET"])
def wait_for_decision(flow_id):
    """
    Block until a decision is made or timeout occurs
    """
    start_time = time.time()
    timeout = 30  # 30 seconds timeout

    while time.time() - start_time < timeout:
        with decision_lock:
            if flow_id in pending_requests:
                decision = pending_requests[flow_id].get("decision")
                if decision:
                    return jsonify({"decision": decision})
        time.sleep(1)  # Wait 1 second between checks
    
    return jsonify({"error": "timeout", "decision": "deny"}), 408

@app.route("/health", methods=["GET"])
def health_check():
    # Add a debug log to see when health checks are happening
    logger.debug("Health check endpoint called")
    return jsonify({
        "status": "healthy", 
        "uptime": time.time() - start_time,
        "version": "1.0.0",
        "pending_count": len(pending_requests)
    })

# Add test endpoints to help with debugging
@app.route("/debug/add-test-request", methods=["GET"])
def add_test_request():
    """Add a test request to the pending requests for UI testing"""
    test_id = f"test-{int(time.time())}"
    test_data = {
        "id": test_id,
        "url": "https://example.com/payment",
        "method": "POST",
        "timestamp": time.time(),
        "headers": {"Content-Type": "application/json"}
    }
    
    with decision_lock:
        pending_requests[test_id] = {"data": test_data, "decision": None}
    
    logger.info(f"Added test request with ID {test_id}")
    return jsonify({"status": "added", "id": test_id})

@app.route("/debug/pending-count", methods=["GET"])
def debug_pending_count():
    """Return the count of pending requests"""
    count = len([k for k, v in pending_requests.items() if v["decision"] is None])
    return jsonify({"count": count})

# Add a main block to run the server directly
if __name__ == "__main__":
    print("🚀 Starting Approval Mechanism Service...")
    print(f"💻 API Key: {API_KEY}")
    print("⏱️ Initializing with empty request queue")
    print("🌐 Starting Flask server on http://localhost:5000")
    
    # Install flask-cors if not available
    try:
        import flask_cors
    except ImportError:
        print("⚠️ flask-cors not installed, attempting to install...")
        import subprocess
        subprocess.call(["pip", "install", "flask-cors"])
        print("✅ flask-cors installed")
    
    socketio.run(app, host='0.0.0.0', port=5000, debug=True, allow_unsafe_werkzeug=True)
