import logging
import os
import re

import requests
from flask import Flask, jsonify, request


app = Flask(__name__)

TIMEOUT = float(
    os.getenv("FIREBASE_TIMEOUT", "10")
)

logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO").upper(),
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)

logger = logging.getLogger(__name__)


def _base_url() -> str:
    firebase_db = os.getenv("FIREBASE_DB")

    if not firebase_db:
        raise RuntimeError(
            "FIREBASE_DB environment variable not set"
        )

    return (
        f"https://{firebase_db}"
        "-default-rtdb.europe-west1"
        ".firebasedatabase.app"
    )


def _guardrail_url(guardrail_id: str) -> str:
    return (
        f"{_base_url()}/guardrails/"
        f"{guardrail_id}.json"
    )


def _validate_guardrail_payload(
    data,
    guardrail_id_from_path: str,
):
    if not isinstance(data, dict):
        return "JSON body must be an object"

    for key in ("id", "regx", "sub"):
        if key not in data:
            return (
                f"Missing required property: {key}"
            )

    if (
        not isinstance(data["id"], str)
        or not data["id"]
    ):
        return "id must be a non-empty string"

    if (
        not isinstance(data["regx"], str)
        or not data["regx"]
    ):
        return "regx must be a non-empty string"

    if not isinstance(data["sub"], str):
        return "sub must be a string"

    if data["id"] != guardrail_id_from_path:
        return (
            "id in body must match id in URL path"
        )

    try:
        re.compile(data["regx"])
    except re.error:
        return "Invalid regular expression"

    return None


def _firebase_failure(
    action: str,
    status_code: int,
):
    logger.warning(
        "Firebase %s returned status %s",
        action,
        status_code,
    )

    return jsonify(
        {
            "error": "Firebase error",
            "status": status_code,
        }
    ), 502


@app.route("/health", methods=["GET"])
def health():
    return jsonify(
        {
            "status": "ok",
            "firebase_configured": bool(
                os.getenv("FIREBASE_DB")
            ),
        }
    ), 200


@app.route(
    "/guardrails/<guardrail_id>",
    methods=["PUT"],
)
def create_guardrail(guardrail_id):
    data = request.get_json(silent=True)

    error = _validate_guardrail_payload(
        data,
        guardrail_id,
    )

    if error:
        return jsonify({"error": error}), 400

    try:
        response = requests.put(
            _guardrail_url(guardrail_id),
            json=data,
            timeout=TIMEOUT,
        )

        if response.status_code >= 400:
            return _firebase_failure(
                "create request",
                response.status_code,
            )

        return jsonify(data), 201

    except RuntimeError as exc:
        logger.error(
            "Guardrails service configuration error: %s",
            exc,
        )

        return jsonify(
            {"error": str(exc)}
        ), 500

    except requests.RequestException:
        logger.exception(
            "Firebase create request failed"
        )

        return jsonify(
            {"error": "Firebase request failed"}
        ), 502


@app.route(
    "/guardrails/<guardrail_id>",
    methods=["GET"],
)
def read_guardrail(guardrail_id):
    try:
        response = requests.get(
            _guardrail_url(guardrail_id),
            timeout=TIMEOUT,
        )

        if response.status_code >= 400:
            return _firebase_failure(
                "read request",
                response.status_code,
            )

        guardrail = response.json()

        if guardrail is None:
            return jsonify(
                {"error": "Not found"}
            ), 404

        if not isinstance(guardrail, dict):
            logger.error(
                "Firebase returned a non-object guardrail"
            )

            return jsonify(
                {
                    "error":
                    "Unexpected data in Firebase"
                }
            ), 502

        return jsonify(guardrail), 200

    except RuntimeError as exc:
        logger.error(
            "Guardrails service configuration error: %s",
            exc,
        )

        return jsonify(
            {"error": str(exc)}
        ), 500

    except requests.RequestException:
        logger.exception(
            "Firebase read request failed"
        )

        return jsonify(
            {"error": "Firebase request failed"}
        ), 502

    except ValueError:
        logger.exception(
            "Firebase returned invalid JSON"
        )

        return jsonify(
            {"error": "Bad response from Firebase"}
        ), 502


@app.route(
    "/guardrails/<guardrail_id>",
    methods=["DELETE"],
)
def delete_guardrail(guardrail_id):
    try:
        existing = requests.get(
            _guardrail_url(guardrail_id),
            timeout=TIMEOUT,
        )

        if existing.status_code >= 400:
            return _firebase_failure(
                "existence check",
                existing.status_code,
            )

        if existing.json() is None:
            return jsonify(
                {"error": "Not found"}
            ), 404

        response = requests.delete(
            _guardrail_url(guardrail_id),
            timeout=TIMEOUT,
        )

        if response.status_code >= 400:
            return _firebase_failure(
                "delete request",
                response.status_code,
            )

        return jsonify(
            {"deleted": guardrail_id}
        ), 200

    except RuntimeError as exc:
        logger.error(
            "Guardrails service configuration error: %s",
            exc,
        )

        return jsonify(
            {"error": str(exc)}
        ), 500

    except requests.RequestException:
        logger.exception(
            "Firebase delete request failed"
        )

        return jsonify(
            {"error": "Firebase request failed"}
        ), 502

    except ValueError:
        logger.exception(
            "Firebase returned invalid JSON"
        )

        return jsonify(
            {"error": "Bad response from Firebase"}
        ), 502


@app.route(
    "/guardrails",
    methods=["GET"],
)
def list_guardrails():
    try:
        response = requests.get(
            f"{_base_url()}/guardrails.json",
            timeout=TIMEOUT,
        )

        if response.status_code >= 400:
            return _firebase_failure(
                "list request",
                response.status_code,
            )

        data = response.json()

        if data is None:
            return jsonify([]), 200

        if not isinstance(data, dict):
            logger.error(
                "Firebase returned unexpected "
                "guardrail collection data"
            )

            return jsonify(
                {
                    "error":
                    "Unexpected data in Firebase"
                }
            ), 502

        return jsonify(
            sorted(data.keys())
        ), 200

    except RuntimeError as exc:
        logger.error(
            "Guardrails service configuration error: %s",
            exc,
        )

        return jsonify(
            {"error": str(exc)}
        ), 500

    except requests.RequestException:
        logger.exception(
            "Firebase list request failed"
        )

        return jsonify(
            {"error": "Firebase request failed"}
        ), 502

    except ValueError:
        logger.exception(
            "Firebase returned invalid JSON"
        )

        return jsonify(
            {"error": "Bad response from Firebase"}
        ), 502


if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=3001,
    )
