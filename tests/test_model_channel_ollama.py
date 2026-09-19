#!/usr/bin/env python3
"""Local Ollama model-channel lane: launch spec, served identity, provenance."""

from __future__ import annotations

import json
import sys
import unittest
from io import StringIO
from pathlib import Path
from unittest import mock

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "pipelines"))
sys.path.insert(0, str(REPO / "tests"))

from model_channel import generate  # noqa: E402
from model_channel import ollama  # noqa: E402
from model_channel import source_policy as policy  # noqa: E402
from test_model_channel import NANO, TASK, _Server, episode_payload  # noqa: E402

NANO_OLLAMA = "nemotron-nano-4b-ollama-factory"
OLLAMA_TAG = "nemotron-3-nano:4b-bf16"
OLLAMA_DIGEST = "sha256:4bc6e34d03fbad91da54a96ccf62d6fcba9d0efdf665219c2292cd1a42822394"


class OllamaLaneTests(unittest.TestCase):
    def _runtime(self):
        return {
            "runtime": "ollama",
            "ollama_version": "0.12.6",
            "device": "NVIDIA GeForce RTX 4080 Laptop GPU",
            "ollama_model_digest": OLLAMA_DIGEST,
        }

    def _models(self, name=OLLAMA_TAG, digest=OLLAMA_DIGEST):
        return [{"name": name, "model": name, "digest": digest}]

    def test_spec_pins_pull_serve_and_manifest_digest(self):
        spec = ollama.launch_spec(
            NANO_OLLAMA, ollama_version="0.12.6", device="test-gpu"
        )
        self.assertEqual(spec["runtime"], "ollama")
        self.assertEqual(spec["model_tag"], OLLAMA_TAG)
        self.assertEqual(spec["model_revision"], OLLAMA_DIGEST)
        self.assertEqual(spec["base_url"], "http://127.0.0.1:11434/v1")
        self.assertEqual(spec["pull_command"], ["ollama", "pull", OLLAMA_TAG])
        self.assertFalse(spec["require_tool_parser"])
        self.assertFalse(spec["require_reasoning_parser"])

    def test_spec_rejects_non_ollama_rows(self):
        with self.assertRaisesRegex(ollama.OllamaSpecError, "local ollama"):
            ollama.launch_spec(NANO, ollama_version="0.12.6", device="test-gpu")

    def test_verify_refuses_non_loopback_and_tls_endpoints(self):
        row = policy.reviewed_row(NANO_OLLAMA)
        for endpoint in (
            "http://192.168.1.10:11434/v1",
            "https://127.0.0.1:11434/v1",
            "http://ollama.example.com/v1",
        ):
            with self.subTest(endpoint=endpoint):
                with self.assertRaises(ollama.OllamaSpecError):
                    ollama.verify_served_identity(endpoint, row)

    def test_verify_refuses_wrong_digest_or_missing_model(self):
        row = policy.reviewed_row(NANO_OLLAMA)
        with _Server(json.dumps(episode_payload()), OLLAMA_TAG,
                   tags={"models": self._models(digest="sha256:" + "0" * 64)}) as server:
            with self.assertRaisesRegex(ollama.OllamaSpecError, "digest"):
                ollama.verify_served_identity(server.endpoint, row)
        with _Server(json.dumps(episode_payload()), OLLAMA_TAG,
                   tags={"models": self._models(name="nemotron-3-nano:30b")}) as server:
            with self.assertRaisesRegex(ollama.OllamaSpecError, "not served"):
                ollama.verify_served_identity(server.endpoint, row)

    def test_verify_refuses_cloud_tag_identity(self):
        row = dict(policy.reviewed_row(NANO_OLLAMA))
        row["runtime_tag"] = "nemotron-3-nano:30b-cloud"
        with self.assertRaisesRegex(ollama.OllamaSpecError, "cloud"):
            ollama.verify_served_identity("http://127.0.0.1:11434/v1", row)

    def test_candidate_preserves_ollama_provenance(self):
        content = json.dumps(episode_payload())
        with _Server(content, OLLAMA_TAG, tags={"models": self._models()}) as server:
            record = generate.generate_candidate(
                NANO_OLLAMA,
                TASK,
                endpoint=server.endpoint,
                runtime=self._runtime(),
                generated_at="2026-09-19T12:30:00Z",
            )
            request = server.httpd.requests[0]
        self.assertEqual(request["model"], OLLAMA_TAG)
        self.assertEqual(record["meta"]["channel"], "local_ollama")
        self.assertEqual(record["meta"]["ollama_model_tag"], OLLAMA_TAG)
        self.assertEqual(record["meta"]["ollama_model_digest"], OLLAMA_DIGEST)
        self.assertEqual(record["meta"]["runtime_ollama_version"], "0.12.6")
        self.assertEqual(record["meta"]["runtime_device"], self._runtime()["device"])
        self.assertTrue(record["meta"]["candidate_only"])

    def test_missing_or_drifting_runtime_provenance_refuses_before_network(self):
        with self.assertRaisesRegex(ollama.OllamaSpecError, "runtime"):
            generate.generate_candidate(
                NANO_OLLAMA, TASK, endpoint="http://127.0.0.1:11434/v1"
            )
        bad = self._runtime()
        bad["ollama_model_digest"] = "sha256:" + "f" * 64
        with self.assertRaisesRegex(ollama.OllamaSpecError, "digest"):
            generate.generate_candidate(
                NANO_OLLAMA, TASK, endpoint="http://127.0.0.1:11434/v1", runtime=bad
            )

    def test_spec_requires_identity_and_positive_ctx(self):
        for kwargs in (
            {"ollama_version": "  ", "device": "test-gpu"},
            {"ollama_version": "0.12.6", "device": ""},
            {"ollama_version": "0.12.6", "device": "test-gpu", "num_ctx": 0},
        ):
            with self.subTest(kwargs=kwargs):
                with self.assertRaises(ollama.OllamaSpecError):
                    ollama.launch_spec(NANO_OLLAMA, **kwargs)
        spec = ollama.launch_spec(
            NANO_OLLAMA, ollama_version="0.12.6", device="test-gpu", num_ctx=8192
        )
        self.assertEqual(spec["num_ctx"], 8192)

    def test_row_requires_exact_tag_and_manifest_digest(self):
        row = dict(policy.reviewed_row(NANO_OLLAMA))
        row["runtime_tag"] = f" {OLLAMA_TAG} "
        with self.assertRaisesRegex(ollama.OllamaSpecError, "tag"):
            ollama.verify_served_identity("http://127.0.0.1:11434/v1", row)
        row = dict(policy.reviewed_row(NANO_OLLAMA))
        row["model_revision"] = "dfaf35d"
        with self.assertRaisesRegex(ollama.OllamaSpecError, "manifest digest"):
            ollama.verify_served_identity("http://127.0.0.1:11434/v1", row)

    def test_verify_refuses_unexpected_base_path(self):
        row = policy.reviewed_row(NANO_OLLAMA)
        with self.assertRaisesRegex(ollama.OllamaSpecError, "base path"):
            ollama.verify_served_identity("http://127.0.0.1:11434/api", row)

    def test_verify_refuses_http_errors_and_non_json_bodies(self):
        row = policy.reviewed_row(NANO_OLLAMA)
        content = json.dumps(episode_payload())
        cases = [
            ({"status": 500, "body": b"broken"}, "HTTP 500"),
            ({"body": b"not json"}, "not JSON"),
            ({"body": b"[1, 2]"}, "JSON object"),
            ({"body": json.dumps({"models": {}}).encode()}, "models list"),
        ]
        for tags, reason in cases:
            with self.subTest(reason=reason):
                with _Server(content, OLLAMA_TAG, tags=tags) as server:
                    with self.assertRaisesRegex(ollama.OllamaSpecError, reason):
                        ollama.verify_served_identity(server.endpoint, row)

    def test_verify_refuses_duplicated_served_tag(self):
        row = policy.reviewed_row(NANO_OLLAMA)
        content = json.dumps(episode_payload())
        models = ["oops"] + self._models() + self._models()
        with _Server(content, OLLAMA_TAG, tags={"models": models}) as server:
            with self.assertRaisesRegex(ollama.OllamaSpecError, "duplicated"):
                ollama.verify_served_identity(server.endpoint, row)

    def test_verify_ignores_non_mapping_tag_entries(self):
        row = policy.reviewed_row(NANO_OLLAMA)
        content = json.dumps(episode_payload())
        models = ["oops", 7] + self._models()
        with _Server(content, OLLAMA_TAG, tags={"models": models}) as server:
            provenance = ollama.verify_served_identity(server.endpoint, row)
        self.assertEqual(provenance["ollama_model_tag"], OLLAMA_TAG)

    def test_runtime_provenance_requires_fields_and_ollama_kind(self):
        row = policy.reviewed_row(NANO_OLLAMA)
        runtime = self._runtime()
        del runtime["device"]
        with self.assertRaisesRegex(ollama.OllamaSpecError, "missing"):
            ollama.require_runtime_provenance(row, runtime)
        runtime = self._runtime()
        runtime["runtime"] = "vllm"
        with self.assertRaisesRegex(ollama.OllamaSpecError, "ollama"):
            ollama.require_runtime_provenance(row, runtime)
        del runtime["runtime"]
        ollama.require_runtime_provenance(row, runtime)

    def test_cli_ollama_spec_prints_the_pinned_spec(self):
        from model_channel import cli as model_cli

        stdout = StringIO()
        with mock.patch("sys.stdout", stdout):
            code = model_cli.run(
                [
                    "ollama-spec",
                    "--path-id", NANO_OLLAMA,
                    "--ollama-version", "0.12.6",
                    "--device", "test-gpu",
                    "--num-ctx", "8192",
                    "--json",
                ]
            )
        self.assertEqual(code, 0)
        payload = json.loads(stdout.getvalue())
        self.assertEqual(payload["model_tag"], OLLAMA_TAG)
        self.assertEqual(payload["num_ctx"], 8192)

    def test_cli_ollama_spec_error_returns_two(self):
        from model_channel import cli as model_cli

        stderr = StringIO()
        with mock.patch("sys.stderr", stderr):
            code = model_cli.run(
                [
                    "ollama-spec",
                    "--path-id", NANO,
                    "--ollama-version", "0.12.6",
                    "--device", "test-gpu",
                ]
            )
        self.assertEqual(code, 2)
        self.assertIn("local ollama", stderr.getvalue())

    def test_unverified_served_identity_refuses_generation(self):
        content = json.dumps(episode_payload())
        runtime = self._runtime()
        cloud = self._models(name="nemotron-3-nano:30b-cloud")
        with _Server(content, OLLAMA_TAG, tags={"models": cloud}) as server:
            endpoint = server.endpoint
            with self.assertRaisesRegex(ollama.OllamaSpecError, "not served"):
                generate.generate_candidate(
                    NANO_OLLAMA, TASK, endpoint=endpoint, runtime=runtime
                )
        self.assertEqual(server.httpd.requests, [])


if __name__ == "__main__":
    unittest.main()
