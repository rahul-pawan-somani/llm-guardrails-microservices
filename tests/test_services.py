import os
import unittest
from unittest.mock import Mock, patch

import requests

import auberge
import guardrails
import llm


def mock_response(
    status_code=200,
    json_data=None,
):
    response = Mock()
    response.status_code = status_code
    response.json.return_value = json_data

    return response


class ServiceTests(unittest.TestCase):

    def setUp(self):
        self.environment = patch.dict(
            os.environ,
            {
                "FIREBASE_DB": "test-project",
                "MISTRAL_API_KEY": "test-key",
            },
            clear=False,
        )

        self.environment.start()

        self.llm_client = (
            llm.app.test_client()
        )

        self.guardrails_client = (
            guardrails.app.test_client()
        )

        self.auberge_client = (
            auberge.app.test_client()
        )

    def tearDown(self):
        self.environment.stop()

    def test_llm_rejects_missing_prompt(self):
        response = self.llm_client.post(
            "/llm",
            json={},
        )

        self.assertEqual(
            response.status_code,
            400,
        )

        self.assertEqual(
            response.get_json(),
            {"error": "Missing prompt"},
        )

    @patch("llm.requests.post")
    def test_llm_returns_mocked_mistral_output(
        self,
        mock_post,
    ):
        mock_post.return_value = mock_response(
            json_data={
                "choices": [
                    {
                        "message": {
                            "content":
                            "Rome is the capital of Italy."
                        }
                    }
                ]
            }
        )

        response = self.llm_client.post(
            "/llm",
            json={
                "prompt":
                "What is the capital of Italy?"
            },
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        self.assertEqual(
            response.get_json(),
            {
                "output":
                "Rome is the capital of Italy."
            },
        )

    @patch("guardrails.requests.put")
    def test_invalid_regex_is_rejected(
        self,
        mock_put,
    ):
        response = self.guardrails_client.put(
            "/guardrails/broken",
            json={
                "id": "broken",
                "regx": "*a-z]",
                "sub": "replacement",
            },
        )

        self.assertEqual(
            response.status_code,
            400,
        )

        self.assertEqual(
            response.get_json(),
            {
                "error":
                "Invalid regular expression"
            },
        )

        mock_put.assert_not_called()

    @patch("guardrails.requests.get")
    @patch("guardrails.requests.put")
    def test_guardrail_create_and_read(
        self,
        mock_put,
        mock_get,
    ):
        guardrail = {
            "id": "email-001",
            "regx": (
                r"[a-zA-Z0-9_.+-]+"
                r"@[a-zA-Z0-9-]+"
                r"\.[a-zA-Z0-9-.]+"
            ),
            "sub": "<Email Address>",
        }

        mock_put.return_value = mock_response(
            status_code=200
        )

        mock_get.return_value = mock_response(
            status_code=200,
            json_data=guardrail,
        )

        create_response = (
            self.guardrails_client.put(
                "/guardrails/email-001",
                json=guardrail,
            )
        )

        read_response = (
            self.guardrails_client.get(
                "/guardrails/email-001"
            )
        )

        self.assertEqual(
            create_response.status_code,
            201,
        )

        self.assertEqual(
            create_response.get_json(),
            guardrail,
        )

        self.assertEqual(
            read_response.status_code,
            200,
        )

        self.assertEqual(
            read_response.get_json(),
            guardrail,
        )

    @patch("auberge.requests.post")
    @patch("auberge.requests.get")
    def test_auberge_sanitises_input_and_output(
        self,
        mock_get,
        mock_post,
    ):
        guardrail = {
            "id": "email-001",
            "regx": (
                r"[a-zA-Z0-9_.+-]+"
                r"@[a-zA-Z0-9-]+"
                r"\.[a-zA-Z0-9-.]+"
            ),
            "sub": "<Email Address>",
        }

        mock_get.side_effect = [
            mock_response(
                json_data=["email-001"]
            ),
            mock_response(
                json_data=guardrail
            ),
            mock_response(
                json_data=["email-001"]
            ),
            mock_response(
                json_data=guardrail
            ),
        ]

        mock_post.return_value = mock_response(
            json_data={
                "output":
                "Reply to admin@example.com"
            }
        )

        response = self.auberge_client.post(
            "/auberge",
            json={
                "prompt":
                "Contact test@example.com"
            },
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        self.assertEqual(
            response.get_json(),
            {
                "output":
                "Reply to <Email Address>"
            },
        )

        self.assertEqual(
            mock_post.call_args.kwargs["json"],
            {
                "prompt":
                "Contact <Email Address>"
            },
        )

    @patch("auberge.requests.get")
    def test_auberge_handles_guardrails_failure(
        self,
        mock_get,
    ):
        mock_get.side_effect = (
            requests.RequestException(
                "service unavailable"
            )
        )

        response = self.auberge_client.post(
            "/auberge",
            json={"prompt": "Hello"},
        )

        self.assertEqual(
            response.status_code,
            502,
        )

        self.assertEqual(
            response.get_json(),
            {
                "error":
                "Guardrails service unavailable"
            },
        )


if __name__ == "__main__":
    unittest.main()
