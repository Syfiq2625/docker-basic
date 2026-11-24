import getpass
import os
import platform
import socket
import sys
from datetime import datetime, timezone
from flask import Flask, jsonify, request

app = Flask(__name__)

SERVICE_NAME = "Container Security & Config Audit API"
APP_VERSION = os.getenv("APP_VERSION", "0.0.0-dev")
APP_ENV = os.getenv("APP_ENV", "production")


def get_runtime_security():
    uid = os.getuid() if hasattr(os, "getuid") else -1
    gid = os.getgid() if hasattr(os, "getgid") else -1
    try:
        username = getpass.getuser()
    except Exception:
        username = os.getenv("USER", "unknown")

    return {
        "user": username,
        "uid": uid,
        "gid": gid,
        "is_non_root": uid != 0,
        "virtual_env": sys.prefix,
        "python_unbuffered": os.getenv("PYTHONUNBUFFERED") == "1",
        "dont_write_bytecode": os.getenv("PYTHONDONTWRITEBYTECODE") == "1",
    }


@app.route("/", methods=["GET"])
def index():
    return jsonify({
        "service": SERVICE_NAME,
        "project": "project-05",
        "version": APP_VERSION,
        "environment": APP_ENV,
        "container_hostname": socket.gethostname(),
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "endpoints": [
            "GET /",
            "GET /health",
            "GET /security",
            "POST /audit"
        ]
    }), 200


@app.route("/health", methods=["GET"])
def health():
    security = get_runtime_security()
    if not security["is_non_root"]:
        return jsonify({
            "status": "unhealthy",
            "reason": "Container is running as root (UID 0)"
        }), 503

    return jsonify({
        "status": "healthy",
        "service": SERVICE_NAME,
        "version": APP_VERSION,
        "running_as": security["user"]
    }), 200


@app.route("/security", methods=["GET"])
def security_report():
    return jsonify({
        "service": SERVICE_NAME,
        "version": APP_VERSION,
        "platform": {
            "python_version": platform.python_version(),
            "os": platform.system(),
            "arch": platform.machine(),
            "working_dir": os.getcwd(),
        },
        "runtime_security": get_runtime_security()
    }), 200


@app.route("/audit", methods=["POST"])
def audit_config():
    payload = request.get_json(silent=True) or {}
    service = payload.get("service")
    port = payload.get("port")
    run_as_root = payload.get("run_as_root", True)

    if not service or not isinstance(port, int):
        return jsonify({
            "passed": False,
            "error": "Field 'service' (string) dan 'port' (integer) wajib diisi"
        }), 400

    findings = []
    if run_as_root:
        findings.append("HIGH: Container tidak boleh berjalan sebagai root user")
    if port < 1024:
        findings.append("MEDIUM: Privileged port (<1024) sebaiknya dihindari untuk non-root user")

    return jsonify({
        "service": service,
        "port": port,
        "passed": len(findings) == 0,
        "findings": findings,
        "audited_by": f"{SERVICE_NAME} v{APP_VERSION}"
    }), 200


if __name__ == "__main__":
    port = int(os.getenv("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
