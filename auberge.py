from flask import Flask, request, jsonify
import requests
import re

app = Flask(__name__)

GUARDRAILS_URL = "http://localhost:3001"
LLM_URL = "http://localhost:3000/llm"
TIMEOUT = 10


def apply_guardrails(text):
    try:
        # Get list of guardrail IDs
        r = requests.get(f"{GUARDRAILS_URL}/guardrails", timeout=TIMEOUT)
        if r.status_code != 200:
            return None, "Failed to fetch guardrail list"

        ids = r.json()

        # Apply each guardrail in order
        for gid in ids:
            r2 = requests.get(f"{GUARDRAILS_URL}/guardrails/{gid}", timeout=TIMEOUT)
            if r2.status_code != 200:
                return None, "Failed to fetch guardrail"

            guardrail = r2.json()
            regx = guardrail["regx"]
            sub = guardrail["sub"]

            text = re.sub(regx, sub, text, flags=re.IGNORECASE)

        return text, None

    except requests.RequestException:
        return None, "Guardrails service unavailable"


@app.route("/auberge", methods=["POST"])
def auberge():
    data = request.get_json(silent=True)
    if not isinstance(data, dict) or "prompt" not in data:
        return jsonify({"error": "Missing prompt"}), 400

    prompt = data["prompt"]
    if not isinstance(prompt, str):
        return jsonify({"error": "prompt must be string"}), 400

    # Sanitise input
    sanitised_prompt, err = apply_guardrails(prompt)
    if err:
        return jsonify({"error": err}), 500

    # Send to LLM
    try:
        r = requests.post(LLM_URL, json={"prompt": sanitised_prompt}, timeout=TIMEOUT)
        if r.status_code != 200:
            return jsonify({"error": "LLM failed"}), 500

        output = r.json()["output"]

    except requests.RequestException:
        return jsonify({"error": "LLM service unavailable"}), 500
    except (KeyError, ValueError):
        return jsonify({"error": "Bad response from LLM"}), 500

    # Sanitise output
    sanitised_output, err = apply_guardrails(output)
    if err:
        return jsonify({"error": err}), 500

    return jsonify({"output": sanitised_output}), 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=3002)
