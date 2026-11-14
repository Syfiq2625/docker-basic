import os
import platform
import socket
from datetime import datetime, timezone
from flask import Flask, jsonify, request

app = Flask(__name__)


@app.route("/", methods=["GET"])
def index():
    return jsonify({
        "service": "DevOps Node Inspector API",
        "project": "project-1",
        "status": "running",
        "container_hostname": socket.gethostname(),
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "endpoints": [
            "GET /",
            "GET /health",
            "GET /info",
            "POST /echo"
        ]
    }), 200


@app.route("/health", methods=["GET"])
def health_check():
    return jsonify({
        "status": "healthy",
        "service": "project-1-node-inspector"
    }), 200


@app.route("/info", methods=["GET"])
def system_info():
    return jsonify({
        "container_hostname": socket.gethostname(),
        "working_directory": os.getcwd(),
        "python_version": platform.python_version(),
        "os_system": platform.system(),
        "os_release": platform.release(),
        "architecture": platform.machine(),
        "app_env": os.getenv("APP_ENV", "production")
    }), 200


@app.route("/echo", methods=["POST"])
def echo_payload():
    data = request.get_json(silent=True) or {}
    return jsonify({
        "received_by_container": socket.gethostname(),
        "payload": data
    }), 200


if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
