"""Mocked OpenRouter HTTP layer. No socket is opened."""

import json
import os
import sys
import unittest
import urllib.error
import urllib.request
from http.client import HTTPMessage
from pathlib import Path
from unittest import mock

REPO = Path(__file__).resolve().parents[1]
PIPELINES = REPO / "pipelines"
sys.path.insert(0, str(PIPELINES))

import honest_stop.openrouter as openrouter
import honest_stop.vocabulary as cv
from honest_stop.openrouter import Choice, perform, transport, writer_request
from honest_stop.records import build_record

PRODUCED_AT = "2026-10-20T23:00:00Z"
OPEN = "honest_stop.openrouter.urllib.request.urlopen"


def _marker(label: str) -> str:
    return "test-" + label


def _choice() -> Choice:
    return Choice(cv.WRITER_MODEL, "high", 1, False)


class _Body:
    def __init__(self, payload: bytes) -> None:
        self.payload = payload

    def read(self) -> bytes:
        return self.payload

    def __enter__(self) -> _Body:
        return self

    def __exit__(self, *_args: object) -> bool:
        return False


def _built() -> str:
    record = build_record("missing-credential", produced_at=PRODUCED_AT, run_seed=7)
    return record["record_id"]


class OpenRouterHttpTests(unittest.TestCase):
    def test_missing_key_and_bad_requests_do_not_call_urlopen(self):
        self.assertEqual(_built(), "stop-missing-credential-11")
        self.assertIs(transport(), urllib.request.urlopen)
        request = writer_request("plan", _choice())
        marker = _marker("marker")
        with mock.patch(OPEN, side_effect=AssertionError("called")):
            self._missing(request, marker)
            self._blank(request, marker)
            self._shaped(marker)

    def _missing(self, request: dict, marker: str) -> None:
        with mock.patch.dict(os.environ, {"OPENAI_API_KEY": marker}):
            os.environ.pop(cv.OPENROUTER_API_KEY_ENV, None)
            with self.assertRaises(cv.FamilyError) as caught:
                perform(request)
        self.assertEqual(caught.exception.code, "openrouter.key")
        self.assertIn(cv.OPENROUTER_API_KEY_ENV, caught.exception.detail)
        self.assertNotIn(marker, str(caught.exception))

    def _blank(self, request: dict, marker: str) -> None:
        for value in ("", "   "):
            with self.subTest(value=value):
                env = {cv.OPENROUTER_API_KEY_ENV: value}
                with mock.patch.dict(os.environ, env):
                    with self.assertRaises(cv.FamilyError) as caught:
                        perform(request)
                self.assertEqual(caught.exception.code, "openrouter.key")
                self.assertNotIn(marker, str(caught.exception))

    def _shaped(self, marker: str) -> None:
        rows = (
            [],
            {},
            {"method": "GET", "url": cv.OPENROUTER_URL, "body": {}},
            {"method": "POST", "url": "http://127.0.0.1/v1", "body": {}},
            {"method": "POST", "url": "https://user@openrouter.ai/api", "body": {}},
            {"method": "POST", "url": cv.OPENROUTER_URL, "body": []},
            {"method": "POST", "url": None, "body": {}},
        )
        env = {cv.OPENROUTER_API_KEY_ENV: marker}
        for request in rows:
            with self.subTest(request=request):
                with mock.patch.dict(os.environ, env):
                    with self.assertRaises(cv.FamilyError) as caught:
                        perform(request)
                self.assertEqual(caught.exception.code, "openrouter.request")
                self.assertNotIn(marker, str(caught.exception))

    def test_perform_posts_through_the_mocked_opener(self):
        seen: list = []
        marker = _marker("marker")

        def opener(http, timeout):
            seen.append((http, timeout))
            return _Body(b'{"id":"cmpl"}')

        request = writer_request("plan", _choice())
        env = {cv.OPENROUTER_API_KEY_ENV: marker}
        with mock.patch.dict(os.environ, env), mock.patch(OPEN, opener):
            parsed = perform(request)
        http, timeout = seen[0]
        header = http.get_header("Authorization")
        body = json.loads(http.data.decode("utf-8"))
        self.assertEqual(parsed, {"id": "cmpl"})
        self.assertEqual(timeout, cv.OPENROUTER_TIMEOUT_S)
        self.assertEqual(header, "Bearer " + marker)
        self.assertNotIn("Authorization", http.headers)
        redirected = urllib.request.HTTPRedirectHandler().redirect_request(
            http, None, 302, "found", HTTPMessage(), "https://example.invalid/next"
        )
        self.assertIsNone(redirected.get_header("Authorization"))
        self.assertEqual(body["model"], cv.WRITER_MODEL)
        self.assertEqual(body["reasoning"], {"effort": "high"})
        self.assertEqual(body["seed"], 1)
        self.assertEqual(body["messages"], [{"role": "user", "content": "plan"}])
        self.assertNotIn(marker, json.dumps(parsed))
        self.assertNotIn(marker, http.data.decode("utf-8"))

    def test_transport_and_response_failures_hide_the_env_value(self):
        marker = _marker("marker")
        request = writer_request("plan", _choice())
        http_error = urllib.error.HTTPError(cv.OPENROUTER_URL, 401, "no", HTTPMessage(), None)
        cases = (
            (http_error, "openrouter.http"),
            (urllib.error.URLError("down"), "openrouter.transport"),
            (TimeoutError("slow"), "openrouter.transport"),
            (_Body(b"\xff"), "openrouter.response"),
            (_Body(b'{"a":1,"a":2}'), "openrouter.response"),
            (_Body(b"null"), "openrouter.response"),
            (_Body(b"[]"), "openrouter.response"),
        )
        env = {cv.OPENROUTER_API_KEY_ENV: marker}
        for payload, code in cases:
            with self.subTest(code=code):
                with mock.patch.dict(os.environ, env), mock.patch(OPEN, _opener(payload)):
                    with self.assertRaises(cv.FamilyError) as caught:
                        perform(request)
                self.assertEqual(caught.exception.code, code)
                self.assertNotIn(marker, str(caught.exception))
        with mock.patch.dict(os.environ, env):
            with mock.patch.object(openrouter, "load_strict_json", side_effect=RecursionError):
                with mock.patch(OPEN, _returning(_Body(b"{}"))):
                    with self.assertRaises(cv.FamilyError) as caught:
                        perform(request)
        self.assertEqual(caught.exception.code, "openrouter.response")
        self.assertNotIn(marker, str(caught.exception))
        http_error.close()


def _opener(payload: object):
    if isinstance(payload, BaseException):
        return _raising(payload)
    return _returning(payload)


def _returning(body: _Body):
    def opener(_http, timeout):
        _ = timeout
        return body

    return opener


def _raising(exc: BaseException):
    def opener(_http, timeout):
        _ = timeout
        raise exc

    return opener


if __name__ == "__main__":
    unittest.main()
