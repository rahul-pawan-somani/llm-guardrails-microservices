from flask import Flask, request, jsonify
import os
import requests

app = Flask(__name__)

MISTRAL_API_KEY = os.environ.get("MISTRAL_API_KEY")
TIMEOUT = 30

MISTRAL_URL = "https://api.mistral.ai/v1/chat/completions"
MODEL = "mistral-small-latest"


@app.route("/llm", methods=["POST"])
def llm():
    data = request.get_json(silent=True)
    if not isinstance(data, dict) or "prompt" not in data:
        return jsonify({"error": "Missing prompt"}), 400

    prompt = data["prompt"]
    if not isinstance(prompt, str):
        return jsonify({"error": "prompt must be a string"}), 400

    if not MISTRAL_API_KEY:
        return jsonify({"error": "MISTRAL_API_KEY not set"}), 500

    payload = {
        "model": MODEL,
        "messages": [
            {"role": "system", "content": "Respond in plain text. Do not use emojis."},
            {"role": "user", "content": prompt}
        ],
        # Keep it simple/deterministic-ish for tests
        "temperature": 0.2,
    }

    headers = {
        "Authorization": f"Bearer {MISTRAL_API_KEY}",
        "Content-Type": "application/json",
    }

    try:
        r = requests.post(MISTRAL_URL, json=payload, headers=headers, timeout=TIMEOUT)
        if r.status_code >= 400:
            return jsonify({"error": "Mistral error", "status": r.status_code}), 500

        resp = r.json()
        output = resp["choices"][0]["message"]["content"].strip()
        if output.startswith('"') and output.endswith('"'):
            output = output[1:-1]

        if not isinstance(output, str):
            return jsonify({"error": "Unexpected Mistral response"}), 500

        return jsonify({"output": output}), 200

    except requests.RequestException:
        return jsonify({"error": "Request to Mistral failed"}), 500
    except (KeyError, IndexError, TypeError, ValueError):
        return jsonify({"error": "Bad response from Mistral"}), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=3000)
