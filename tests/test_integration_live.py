import os
import re
import unittest

import requests

from tests.firebase_helper import delete_guardrail


LLM_URL = os.getenv(
    "LLM_TEST_URL",
    "http://localhost:3000/llm",
)

GUARDRAILS_URL = os.getenv(
    "GUARDRAILS_TEST_URL",
    "http://localhost:3001/guardrails",
)

AUBERGE_URL = os.getenv(
    "AUBERGE_TEST_URL",
    "http://localhost:3002/auberge",
)

TIMEOUT = float(
    os.getenv("LIVE_TEST_TIMEOUT", "30")
)

RUN_LIVE_TESTS = (
    os.getenv("RUN_LIVE_TESTS") == "1"
)


@unittest.skipUnless(
    RUN_LIVE_TESTS,
    (
        "Set RUN_LIVE_TESTS=1 "
        "to run live integration tests"
    ),
)
class LiveIntegrationTests(unittest.TestCase):

    def tearDown(self):
        for guardrail_id in (
            "name-001",
            "email-live-001",
            "broken",
            "rome-live-001",
        ):
            try:
                delete_guardrail(guardrail_id)
            except requests.RequestException:
                pass

    def test_001_llm_returns_output(self):
        response = requests.post(
            LLM_URL,
            json={
                "prompt":
                "What is the melting point "
                "of silver?"
            },
            timeout=TIMEOUT,
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        output = response.json().get("output")

        self.assertIsInstance(
            output,
            str,
        )

        self.assertTrue(
            output.strip()
        )

    def test_002_guardrail_create_and_read(self):
        guardrail_id = "name-001"

        payload = {
            "id": guardrail_id,
            "regx": r"Example Name",
            "sub": "Replacement Name",
        }

        create_response = requests.put(
            (
                f"{GUARDRAILS_URL}/"
                f"{guardrail_id}"
            ),
            json=payload,
            timeout=TIMEOUT,
        )

        self.assertEqual(
            create_response.status_code,
            201,
        )

        read_response = requests.get(
            (
                f"{GUARDRAILS_URL}/"
                f"{guardrail_id}"
            ),
            timeout=TIMEOUT,
        )

        self.assertEqual(
            read_response.status_code,
            200,
        )

        self.assertEqual(
            read_response.json(),
            payload,
        )

    def test_003_email_guardrail_create_and_read(
        self
    ):
        guardrail_id = "email-live-001"

        payload = {
            "id": guardrail_id,
            "regx": (
                r"[a-zA-Z0-9_.+-]+"
                r"@[a-zA-Z0-9-]+"
                r"\.[a-zA-Z0-9-.]+"
            ),
            "sub": "<Email Address>",
        }

        create_response = requests.put(
            (
                f"{GUARDRAILS_URL}/"
                f"{guardrail_id}"
            ),
            json=payload,
            timeout=TIMEOUT,
        )

        self.assertEqual(
            create_response.status_code,
            201,
        )

        read_response = requests.get(
            (
                f"{GUARDRAILS_URL}/"
                f"{guardrail_id}"
            ),
            timeout=TIMEOUT,
        )

        self.assertEqual(
            read_response.status_code,
            200,
        )

        self.assertEqual(
            read_response.json(),
            payload,
        )

    def test_004_invalid_regex_is_rejected(self):
        guardrail_id = "broken"

        payload = {
            "id": guardrail_id,
            "regx": r"*a-z]",
            "sub": "replacement",
        }

        response = requests.put(
            (
                f"{GUARDRAILS_URL}/"
                f"{guardrail_id}"
            ),
            json=payload,
            timeout=TIMEOUT,
        )

        self.assertEqual(
            response.status_code,
            400,
        )

    def test_005_output_guardrail_end_to_end(self):
        guardrail_id = "rome-live-001"

        payload = {
            "id": guardrail_id,
            "regx": r"\bRome\b",
            "sub": "Roma",
        }

        create_response = requests.put(
            (
                f"{GUARDRAILS_URL}/"
                f"{guardrail_id}"
            ),
            json=payload,
            timeout=TIMEOUT,
        )

        self.assertEqual(
            create_response.status_code,
            201,
        )

        response = requests.post(
            AUBERGE_URL,
            json={
                "prompt": (
                    "What is the capital of Italy? "
                    "Reply with only the city name."
                )
            },
            timeout=TIMEOUT,
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        output = response.json().get("output")

        self.assertIsInstance(
            output,
            str,
        )

        self.assertIn(
            "Roma",
            output,
        )

        self.assertIsNone(
            re.search(
                r"\bRome\b",
                output,
                flags=re.IGNORECASE,
            )
        )


if __name__ == "__main__":
    unittest.main()
