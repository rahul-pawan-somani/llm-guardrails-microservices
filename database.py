import os
import requests

TIMEOUT = 10

FIREBASE_DB = os.environ.get("FIREBASE_DB")
if not FIREBASE_DB:
    raise RuntimeError("FIREBASE_DB environment variable not set")

BASE_URL = f"https://{FIREBASE_DB}-default-rtdb.europe-west1.firebasedatabase.app"

class _DB:
    def clear(self):
        """
        Clears all guardrails from Firebase so tests start from a clean state.
        """
        url = f"{BASE_URL}/guardrails.json"
        r = requests.delete(url, timeout=TIMEOUT)
        r.raise_for_status()

db = _DB()
