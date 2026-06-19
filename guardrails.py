from flask import Flask, request, jsonify
import re
import os
import requests

app = Flask(__name__)

FIREBASE_DB = os.environ.get("FIREBASE_DB")
if not FIREBASE_DB:
    raise RuntimeError("FIREBASE_DB environment variable not set")

BASE_URL = f"https://{FIREBASE_DB}-default-rtdb.europe-west1.firebasedatabase.app"
TIMEOUT = 10


def _guardrail_url(gid: str) -> str:
    return f"{BASE_URL}/guardrails/{gid}.json"


def _validate_guardrail_payload(data, gid_from_path: str):
    if not isinstance(data, dict):
        return "JSON body must be an object"
    for k in ("id", "regx", "sub"):
        if k not in data:
            return f"Missing required property: {k}"
    if not isinstance(data["id"], str) or not data["id"]:
        return "id must be a non-empty string"
    if not isinstance(data["regx"], str):
        return "regx must be a string"
    if not isinstance(data["sub"], str):
        return "sub must be a string"
    if data["id"] != gid_from_path:
        return "id in body must match id in URL path"
    return None


@app.route("/guardrails/<gid>", methods=["PUT"])
def create_guardrail(gid):
    try:
        data = request.get_json(silent=True)
        err = _validate_guardrail_payload(data, gid)
        if err:
            return jsonify({"error": err}), 400
        # Validate regx
        try:
            re.compile(data["regx"])
        except re.error:
            return jsonify({"error": "Invalid regular expression"}), 400

        r = requests.put(_guardrail_url(gid), json=data, timeout=TIMEOUT)
        if r.status_code >= 400:
            return jsonify({"error": "Firebase error", "status": r.status_code}), 500

        return jsonify(data), 201
    except requests.RequestException:
        return jsonify({"error": "Firebase request failed"}), 500


@app.route("/guardrails/<gid>", methods=["GET"])
def read_guardrail(gid):
    try:
        r = requests.get(_guardrail_url(gid), timeout=TIMEOUT)
        if r.status_code >= 400:
            return jsonify({"error": "Firebase error", "status": r.status_code}), 500

        obj = r.json()
        if obj is None:
            return jsonify({"error": "Not found"}), 404

        # Ensure returned object includes id/regx/sub
        return jsonify(obj), 200
    except requests.RequestException:
        return jsonify({"error": "Firebase request failed"}), 500
    except ValueError:
        return jsonify({"error": "Bad response from Firebase"}), 500


@app.route("/guardrails/<gid>", methods=["DELETE"])
def delete_guardrail(gid):
    try:
        # Check guardrail existence
        r0 = requests.get(_guardrail_url(gid), timeout=TIMEOUT)
        if r0.status_code >= 400:
            return jsonify({"error": "Firebase error", "status": r0.status_code}), 500

        if r0.json() is None:
            return jsonify({"error": "Not found"}), 404

        r = requests.delete(_guardrail_url(gid), timeout=TIMEOUT)
        if r.status_code >= 400:
            return jsonify({"error": "Firebase error", "status": r.status_code}), 500

        return jsonify({"deleted": gid}), 200
    except requests.RequestException:
        return jsonify({"error": "Firebase request failed"}), 500


@app.route("/guardrails", methods=["GET"])
def list_guardrails():
    try:
        r = requests.get(f"{BASE_URL}/guardrails.json", timeout=TIMEOUT)
        if r.status_code >= 400:
            return jsonify({"error": "Firebase error", "status": r.status_code}), 500

        data = r.json()
        if data is None:
            return jsonify([]), 200

        if not isinstance(data, dict):
            return jsonify({"error": "Unexpected data in Firebase"}), 500

        # Deterministic ordering helps unit tests
        ids = sorted(list(data.keys()))
        return jsonify(ids), 200
    except requests.RequestException:
        return jsonify({"error": "Firebase request failed"}), 500
    except ValueError:
        return jsonify({"error": "Bad response from Firebase"}), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=3001)
