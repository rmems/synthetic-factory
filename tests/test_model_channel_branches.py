"""Fail-closed branches of the model-channel policy, clients, launch specs and CLI.

Every case runs offline: snapshots and policy copies live in temporary directories,
and the one HTTPS case replaces the response reader so no socket is opened.
"""

import json
import re
import tempfile
import unittest
from io import StringIO
from pathlib import Path
from unittest import mock

from pipelines.model_channel import cli, generate, openai_client, openrouter, vllm
from pipelines.model_channel import source_policy as policy
from tests.test_model_channel import NANO, TASK, episode_payload

OLLAMA = "nemotron-nano-4b-ollama-factory"
MODEL = "exact-model"
ENDPOINT = "http://localhost/v1"
UTC_STAMP = re.compile(r"\d{4}-\d\d-\d\dT\d\d:\d\d:\d\dZ")
LAUNCH = {"runtime_version": "0.11.0", "device": "fixture-gpu"}
SNAPSHOT = {
    "sha256": "0" * 64,
    "data": (
        {"id": "vendor/withdrawn", "distillable": False},
        {"id": "vendor/twin"},
        {"id": "vendor/twin"},
    ),
}


def _reviewed_with(**changes):
    row = policy.reviewed_row(NANO)
    row.update(changes)
    return row


def _launch(path_id=NANO, **changes):
    return lambda: vllm.launch_spec(path_id, **{**LAUNCH, **changes})


def _registry(raw):
    return lambda: policy.validate_registry_row(raw)


def _entry(model_id):
    return lambda: openrouter.catalog_entry(SNAPSHOT, model_id)


def _chat(base_url, model):
    return lambda: openai_client.chat_completions(base_url, model, [])


# (label, zero-argument call, exception type, exact message)
REFUSALS = (
    ("unknown path id", lambda: policy.reviewed_row("missing-factory"), policy.SourcePolicyError,
     "unknown reviewed model-channel path_id: missing-factory"),
    ("registry row type", _registry([]), policy.SourcePolicyError,
     "model-channel registry row must be an object"),
    ("registry authority", _registry({"identity_authoritative": False}),
     policy.SourcePolicyError, "model-channel registry row must be identity-authoritative"),
    ("registry path id", _registry({"identity_authoritative": True, "path_id": ""}),
     policy.SourcePolicyError, "model-channel registry row must name a path_id"),
    ("registry drift", _registry(_reviewed_with(model_revision="0" * 40)),
     policy.SourcePolicyError,
     "model-channel registry row drifts from independently sealed policy"),
    ("blank model id", _entry(" "), openrouter.OpenRouterError,
     "OpenRouter model id must be an exact non-empty tag"),
    ("padded model id", _entry("vendor/twin "), openrouter.OpenRouterError,
     "OpenRouter model id must be an exact non-empty tag"),
    ("withdrawn model", _entry("vendor/withdrawn"), openrouter.OpenRouterError,
     "'vendor/withdrawn' is present but distillable is not true"),
    ("duplicated model", _entry("vendor/twin"), openrouter.OpenRouterError,
     "'vendor/twin' is duplicated in the distillable snapshot"),
    ("undated snapshot",
     lambda: openrouter.evidence(model_id="m", snapshot={"retrieved_at": " "}, entry={},
                                 terms_sha256="t", underlying_license_sha256="u"),
     openrouter.OpenRouterError, "distillable snapshot must record retrieved_at"),
    ("url scheme", _chat("ftp://localhost/v1", MODEL), openai_client.OpenAIClientError,
     "unsupported OpenAI-compatible URL: 'ftp://localhost/v1'"),
    ("blank model", _chat(ENDPOINT, ""), openai_client.OpenAIClientError,
     "model must be a non-empty exact tag; no silent rewrite"),
    ("padded model", _chat(ENDPOINT, f" {MODEL}"), openai_client.OpenAIClientError,
     "model must be a non-empty exact tag; no silent rewrite"),
    ("not a vLLM route", _launch(OLLAMA), vllm.VLLMSpecError,
     f"{OLLAMA} is not a local vLLM factory"),
    ("blank runtime identity", _launch(device=" "), vllm.VLLMSpecError,
     "runtime_version and device identity are required"),
    ("served name", _launch(served_model_name="other-name"), vllm.VLLMSpecError,
     "served_model_name must match the pinned runtime tag or model_id"),
    ("parser requirement", lambda: vllm.require_plain_generation({"require_reasoning_parser": 1}),
     vllm.VLLMSpecError, "bulk generation must not require tool or reasoning parsers"),
)


def _write(directory, name, payload):
    path = directory / name
    path.write_bytes(payload)
    return path


class ModelChannelRefusals(unittest.TestCase):
    def test_each_call_raises_its_exact_refusal(self):
        for label, call, error, message in REFUSALS:
            with self.subTest(label), self.assertRaises(error) as caught:
                call()
            self.assertEqual(str(caught.exception), message)


class ModelChannelFileBoundaries(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)

    def _snapshot_refusal(self, payload):
        path = _write(self.root, "snapshot.json", payload)
        with self.assertRaises(openrouter.OpenRouterError) as caught:
            openrouter.load_snapshot(path)
        return str(caught.exception)

    def _policy_refusal(self, path):
        with self.assertRaises(policy.SourcePolicyError) as caught:
            policy.load_policy(path)
        return str(caught.exception)

    def test_snapshot_shape_refusals(self):
        cases = (
            (b"{", "distillable snapshot unreadable or invalid: "),
            (b"[]", "distillable snapshot must be a JSON object"),
            (b'{"data": []}', "distillable snapshot data must be a non-empty list"),
        )
        for payload, message in cases:
            with self.subTest(payload=payload):
                self.assertTrue(self._snapshot_refusal(payload).startswith(message))

    def test_policy_copies_have_no_independent_authority(self):
        missing = self._policy_refusal(self.root / "absent.json")
        self.assertTrue(missing.startswith("model-channel policy unreadable or invalid: "))
        copy = _write(self.root, "policy.json", policy.POLICY_PATH.read_bytes() + b"\n")
        self.assertEqual(
            self._policy_refusal(copy),
            "model-channel policy differs from independently reviewed bytes",
        )


class ModelChannelAcceptedPaths(unittest.TestCase):
    def test_registry_row_equal_to_the_sealed_row_is_accepted(self):
        self.assertIsNone(policy.validate_registry_row(policy.reviewed_row(NANO)))

    def test_route_claims_cover_source_type_and_channel_fields(self):
        cases = (
            ([], False),
            ({"source_type": "model_channel"}, True),
            ({"runtime_tag": "tag"}, True),
            ({"provider": "hosted"}, False),
        )
        for raw, expected in cases:
            with self.subTest(raw=raw):
                self.assertIs(policy.claims_model_channel_route(raw), expected)

    def test_evidence_defaults_generation_time_and_canonical_slug(self):
        found = openrouter.evidence(
            model_id="vendor/model", snapshot={"retrieved_at": "2026-09-18", "sha256": "abc"},
            entry={"canonical_slug": ""}, terms_sha256="t", underlying_license_sha256="u",
        )
        self.assertEqual(found["canonical_slug"], "vendor/model")
        self.assertRegex(found["generated_at"], UTC_STAMP)

    def test_https_requests_carry_tls_and_bearer_authorization(self):
        with mock.patch.object(openai_client, "_read_response", return_value=b'{"id": "x"}') as read:
            found = openai_client.chat_completions("https://example.invalid/v1", MODEL, [], api_key="k")
        conn, path, _body, headers = read.call_args.args
        self.assertEqual(found, {"id": "x"})
        self.assertEqual((conn.host, conn.port, path), ("example.invalid", 443, "/v1/chat/completions"))
        self.assertEqual(headers["Authorization"], "Bearer k")

    def test_docker_launch_spec_carries_digest_and_optional_parsers(self):
        spec = vllm.launch_spec(
            NANO, **LAUNCH, container_image="vllm/vllm-openai", container_digest="sha256:abc",
            reasoning_parser="nano_v3", tool_parser="hermes",
        )
        self.assertEqual(
            [spec[key] for key in ("container_image", "container_digest", "reasoning_parser",
                                   "tool_parser")],
            ["vllm/vllm-openai", "sha256:abc", "nano_v3", "hermes"],
        )

    def test_untrainable_stripping_keeps_non_string_keys(self):
        stripped = generate.strip_untrainable({1: "a <think>x</think>", "reasoning": "r"})
        self.assertEqual(stripped, {1: "a"})

    def test_candidate_usage_keeps_only_integer_token_counts(self):
        response = {
            "choices": [{"message": {"content": json.dumps(episode_payload())}}],
            "usage": {"prompt_tokens": 3, "completion_tokens": "4", "total_tokens": 7},
        }
        with mock.patch.object(openai_client, "chat_completions", return_value=response):
            record = generate.generate_candidate(NANO, TASK, endpoint=ENDPOINT)
        self.assertEqual(record["_generation"]["usage"], {"prompt_tokens": 3, "total_tokens": 7})


class ModelChannelCli(unittest.TestCase):
    def test_vllm_spec_command_prints_the_pinned_launch_contract(self):
        stdout = StringIO()
        argv = ["vllm-spec", "--path-id", NANO, "--runtime-version", "0.11.0",
                "--device", "fixture-gpu", "--json"]
        with mock.patch("sys.stdout", stdout):
            code = cli.run(argv)
        spec = json.loads(stdout.getvalue())
        self.assertEqual((code, spec["path_id"], spec["runtime"]), (0, NANO, "vllm"))

    def test_record_stamp_falls_back_when_the_candidate_stamp_is_not_text(self):
        with mock.patch.object(generate, "_utc_now", return_value="fallback-stamp"):
            stamp = cli.record_stamp([{"meta": {"generated_at": 5}}])
        self.assertEqual(stamp, "fallback-stamp")


if __name__ == "__main__":
    unittest.main()
