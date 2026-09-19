"""Connection lifetime and strict JSON behavior at the model endpoint boundary."""

import unittest
from unittest.mock import Mock, patch

from pipelines.model_channel import openai_client


class ClientLifetime(unittest.TestCase):
    def test_every_network_failure_closes_the_connection(self):
        for phase in ("request", "getresponse", "read"):
            with self.subTest(phase=phase):
                connection = Mock()
                target = connection.getresponse.return_value if phase == "read" else connection
                getattr(target, phase).side_effect = OSError("injected network failure")
                with patch.object(openai_client, "_connection", return_value=connection):
                    with self.assertRaisesRegex(OSError, "injected network failure"):
                        openai_client.chat_completions("http://localhost/v1", "exact-model", [])
                connection.close.assert_called_once()

    def test_http_and_json_refusals_also_close_the_connection(self):
        for status, body in ((503, b"unavailable"), (200, b"not JSON"), (200, b"[]")):
            with self.subTest(status=status, body=body):
                connection = Mock()
                response = connection.getresponse.return_value
                response.status = status
                response.read.return_value = body
                with patch.object(openai_client, "_connection", return_value=connection):
                    with self.assertRaises(openai_client.OpenAIClientError):
                        openai_client.chat_completions("http://localhost/v1", "exact-model", [])
                connection.close.assert_called_once()
