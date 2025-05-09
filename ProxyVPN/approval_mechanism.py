from flask import Flask, request, jsonify
from threading import Lock
import time

app = Flask(__name__)

# Store intercepted flows
pending_requests = {}
decision_lock = Lock()

@app.route("/intercepted", methods=["POST"])
def intercepted():
    data = request.json
    flow_id = data["id"]
    with decision_lock:
        pending_requests[flow_id] = {"data": data, "decision": None}
    return jsonify({"status": "waiting", "id": flow_id})

@app.route("/requests", methods=["GET"])
def get_pending():
    return jsonify([
        {"id": k, "details": v["data"]}
        for k, v in pending_requests.items() if v["decision"] is None
    ])

@app.route("/decision", methods=["POST"])
def make_decision():
    data = request.json
    flow_id = data["id"]
    action = data["action"]
    with decision_lock:
        if flow_id in pending_requests:
            pending_requests[flow_id]["decision"] = action
            return jsonify({"status": "received"})
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
