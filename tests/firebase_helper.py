import os

import requests


TIMEOUT = float(
    os.getenv("FIREBASE_TIMEOUT", "10")
)


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


def clear_guardrails():
    response = requests.delete(
        f"{_base_url()}/guardrails.json",
        timeout=TIMEOUT,
    )

    response.raise_for_status()
