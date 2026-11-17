import os
from datetime import datetime, timezone
from flask import Flask, jsonify, request

app = Flask(__name__)

APP_NAME = "Release Gatekeeper API"
APP_VERSION = os.getenv("APP_VERSION", "1.0.0")
APP_ENV = os.getenv("APP_ENV", "ci-staging")


@app.route("/", methods=["GET"])
def index():
    return jsonify({
        "service": APP_NAME,
        "project": "project-02",
        "version": APP_VERSION,
        "environment": APP_ENV,
        "timestamp_utc": datetime.now(timezone.utc).isoformat()
    }), 200


@app.route("/health", methods=["GET"])
def health():
    return jsonify({
        "status": "ok",
        "service": APP_NAME,
        "version": APP_VERSION
    }), 200


@app.route("/validate", methods=["POST"])
def validate_deployment():
    payload = request.get_json(silent=True) or {}
    required_fields = ["service_name", "image_tag", "replicas"]
    missing = [field for field in required_fields if field not in payload]

    if missing:
        return jsonify({
            "valid": False,
            "missing_fields": missing
        }), 400

    replicas = payload.get("replicas")
    if not isinstance(replicas, int) or replicas < 1:
        return jsonify({
            "valid": False,
            "error": "replicas must be an integer >= 1"
        }), 400

    return jsonify({
        "valid": True,
        "release_candidate": f"{payload['service_name']}:{payload['image_tag']}",
        "replicas": replicas,
        "validated_by": APP_NAME
    }), 200


if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
