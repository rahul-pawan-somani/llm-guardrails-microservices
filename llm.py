import logging
import os

import requests
from flask import Flask, jsonify, request


app = Flask(__name__)

TIMEOUT = float(
    os.getenv("MISTRAL_TIMEOUT", "30")
)

MISTRAL_URL = os.getenv(
    "MISTRAL_URL",
    "https://api.mistral.ai/v1/chat/completions",
)

MODEL = os.getenv(
    "MISTRAL_MODEL",
    "mistral-small-latest",
)

logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO").upper(),
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)

logger = logging.getLogger(__name__)


@app.route("/health", methods=["GET"])
def health():
    return jsonify(
        {
            "status": "ok",
            "mistral_configured": bool(
                os.getenv("MISTRAL_API_KEY")
            ),
            "model": MODEL,
        }
    ), 200


@app.route("/llm", methods=["POST"])
def llm():
    data = request.get_json(silent=True)

    if not isinstance(data, dict) or "prompt" not in data:
        return jsonify(
            {"error": "Missing prompt"}
        ), 400

    prompt = data["prompt"]

    if not isinstance(prompt, str):
        return jsonify(
            {"error": "prompt must be a string"}
        ), 400

    api_key = os.getenv("MISTRAL_API_KEY")

    if not api_key:
        logger.error(
            "MISTRAL_API_KEY is not configured"
        )

        return jsonify(
            {"error": "MISTRAL_API_KEY not set"}
        ), 500

    payload = {
        "model": MODEL,
        "messages": [
            {
                "role": "system",
                "content": (
                    "Respond in plain text. "
                    "Do not use emojis."
                ),
            },
            {
                "role": "user",
                "content": prompt,
            },
        ],
        "temperature": 0.2,
    }

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    try:
        response = requests.post(
            MISTRAL_URL,
            json=payload,
            headers=headers,
            timeout=TIMEOUT,
        )

        if response.status_code >= 400:
            logger.warning(
                "Mistral API returned status %s",
                response.status_code,
            )

            return jsonify(
                {
                    "error": "Mistral API error",
                    "status": response.status_code,
                }
            ), 502

        body = response.json()

        content = (
            body["choices"][0]
            ["message"]["content"]
        )

        if not isinstance(content, str):
            raise TypeError(
                "Mistral response content "
                "is not a string"
            )

        output = content.strip()

        if (
            output.startswith('"')
            and output.endswith('"')
            and len(output) >= 2
        ):
            output = output[1:-1]

        return jsonify(
            {"output": output}
        ), 200

    except requests.RequestException:
        logger.exception(
            "Request to Mistral API failed"
        )

        return jsonify(
            {"error": "Request to Mistral failed"}
        ), 502

    except (
        KeyError,
        IndexError,
        TypeError,
        ValueError,
    ):
        logger.exception(
            "Mistral API returned an invalid response"
        )

        return jsonify(
            {"error": "Bad response from Mistral"}
        ), 502


if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=3000,
    )
