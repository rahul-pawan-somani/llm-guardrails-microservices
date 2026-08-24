import logging
import os
import re

import requests
from flask import Flask, jsonify, request


app = Flask(__name__)

GUARDRAILS_URL = os.getenv(
    "GUARDRAILS_URL",
    "http://localhost:3001"
).rstrip("/")

LLM_URL = os.getenv(
    "LLM_URL",
    "http://localhost:3000/llm"
)

TIMEOUT = float(os.getenv("SERVICE_TIMEOUT", "10"))

logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO").upper(),
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)

logger = logging.getLogger(__name__)


def apply_guardrails(text: str):
    try:
        response = requests.get(
            f"{GUARDRAILS_URL}/guardrails",
            timeout=TIMEOUT,
        )

        if response.status_code != 200:
            logger.warning(
                "Guardrails list request returned status %s",
                response.status_code,
            )
            return None, "Failed to fetch guardrail list"

        guardrail_ids = response.json()

        if not isinstance(guardrail_ids, list):
            logger.error(
                "Guardrails service returned a non-list response"
            )
            return None, "Bad response from Guardrails service"

        for guardrail_id in guardrail_ids:
            response = requests.get(
                f"{GUARDRAILS_URL}/guardrails/{guardrail_id}",
                timeout=TIMEOUT,
            )

            if response.status_code != 200:
                logger.warning(
                    "Guardrail request for %s returned status %s",
                    guardrail_id,
                    response.status_code,
                )
                return None, "Failed to fetch guardrail"

            guardrail = response.json()

            if not isinstance(guardrail, dict):
                logger.error(
                    "Guardrails service returned a non-object guardrail"
                )
                return None, "Bad response from Guardrails service"

            pattern = guardrail.get("regx")
            replacement = guardrail.get("sub")

            if (
                not isinstance(pattern, str)
                or not isinstance(replacement, str)
            ):
                logger.error(
                    "Guardrails service returned an invalid guardrail payload"
                )
                return None, "Bad response from Guardrails service"

            try:
                text = re.sub(
                    pattern,
                    replacement,
                    text,
                    flags=re.IGNORECASE,
                )
            except re.error:
                logger.exception(
                    "Guardrails service returned an invalid regular expression"
                )
                return None, "Invalid guardrail pattern"

        return text, None

    except requests.RequestException:
        logger.exception(
            "Guardrails service request failed"
        )
        return None, "Guardrails service unavailable"

    except ValueError:
        logger.exception(
            "Guardrails service returned invalid JSON"
        )
        return None, "Bad response from Guardrails service"


@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok"}), 200


@app.route("/auberge", methods=["POST"])
def auberge():
    data = request.get_json(silent=True)

    if not isinstance(data, dict) or "prompt" not in data:
        return jsonify({"error": "Missing prompt"}), 400

    prompt = data["prompt"]

    if not isinstance(prompt, str):
        return jsonify(
            {"error": "prompt must be string"}
        ), 400

    # Apply guardrails before sending the prompt to the LLM.
    sanitised_prompt, error = apply_guardrails(prompt)

    if error:
        return jsonify({"error": error}), 502

    # Send the sanitised prompt to the LLM service.
    try:
        response = requests.post(
            LLM_URL,
            json={"prompt": sanitised_prompt},
            timeout=TIMEOUT,
        )

        if response.status_code != 200:
            logger.warning(
                "LLM service returned status %s",
                response.status_code,
            )
            return jsonify(
                {"error": "LLM service failed"}
            ), 502

        payload = response.json()
        output = payload["output"]

        if not isinstance(output, str):
            raise TypeError(
                "LLM output is not a string"
            )

    except requests.RequestException:
        logger.exception(
            "LLM service request failed"
        )
        return jsonify(
            {"error": "LLM service unavailable"}
        ), 502

    except (KeyError, TypeError, ValueError):
        logger.exception(
            "LLM service returned an invalid response"
        )
        return jsonify(
            {"error": "Bad response from LLM service"}
        ), 502

    # Apply the same guardrails to the generated output.
    sanitised_output, error = apply_guardrails(output)

    if error:
        return jsonify({"error": error}), 502

    return jsonify(
        {"output": sanitised_output}
    ), 200


if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=3002,
    )
