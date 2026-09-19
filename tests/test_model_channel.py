#!/usr/bin/env python3
"""Local vLLM and OpenRouter-distillable model-channel onboarding."""

from __future__ import annotations

import json
import sys
import tempfile
import threading
import unittest
from http.server import BaseHTTPRequestHandler, HTTPServer
from io import StringIO
from pathlib import Path
from unittest import mock

REPO = Path(__file__).resolve().parents[1]
PIPELINES = REPO / "pipelines"
sys.path.insert(0, str(PIPELINES))
sys.path.insert(0, str(REPO / "tests"))

import curate_identity as identity  # noqa: E402
import rights_classifier  # noqa: E402
import rights_policy  # noqa: E402
import round_txn  # noqa: E402
from round_txn_test_helpers import write_records  # noqa: E402
from model_channel import generate  # noqa: E402
from model_channel import ollama  # noqa: E402
from model_channel import openrouter  # noqa: E402
from model_channel import source_policy as policy  # noqa: E402
from model_channel import vllm as vllm_mod  # noqa: E402

SNAPSHOT = REPO / "tests/fixtures/model-channel/openrouter-distillable-snapshot.json"
TASK = {"goal": "repair a deterministic fixture that fails when the lock file exists"}
NANO = "nemotron-nano-4b-vllm-factory"
NANO_OLLAMA = "nemotron-nano-4b-ollama-factory"
OLLAMA_TAG = "nemotron-3-nano:4b-bf16"
OLLAMA_DIGEST = "sha256:4bc6e34d03fbad91da54a96ccf62d6fcba9d0efdf665219c2292cd1a42822394"
PHI = "openrouter-phi-4-factory"


def episode_payload(**overrides):
    record = {
        "id": "mc-r01-1",
        "goal": TASK["goal"],
        "steps": [
            {
                "decision_basis": "Observation: lock file is present in the fixture",
                "tool_call": {"name": "bash", "args": {"command": "rm lock"}},
                "observation": "removed lock",
            }
        ],
        "outcome": "fixed",
        "reward": {"success": True},
    }
    record.update(overrides)
    return record


class _Handler(BaseHTTPRequestHandler):
    def log_message(self, *_args):
        return

    def do_GET(self):
        if self.path == "/api/tags":
            payload = {"models": self.server.ollama_models}
            body = json.dumps(payload).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return
        self.send_response(404)
        self.end_headers()

    def do_POST(self):
        length = int(self.headers.get("Content-Length", "0"))
        raw = self.rfile.read(length)
        self.server.requests.append(json.loads(raw.decode("utf-8")))
        payload = {
            "id": "chatcmpl-fixture",
            "model": self.server.response_model,
            "choices": [
                {
                    "index": 0,
                    "message": {"role": "assistant", "content": self.server.content},
                    "finish_reason": "stop",
                }
            ],
            "usage": {
                "prompt_tokens": 11,
                "completion_tokens": 22,
                "total_tokens": 33,
            },
        }
        body = json.dumps(payload).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


class _Server:
    def __init__(self, content: str, response_model: str, ollama_models=None):
        self.httpd = HTTPServer(("127.0.0.1", 0), _Handler)
        self.httpd.requests = []
        self.httpd.content = content
        self.httpd.response_model = response_model
        self.httpd.ollama_models = ollama_models or []
        self.thread = threading.Thread(target=self.httpd.serve_forever, daemon=True)

    def __enter__(self):
        self.thread.start()
        host, port = self.httpd.server_address
        self.endpoint = f"http://{host}:{port}/v1"
        return self

    def __exit__(self, *_args):
        self.httpd.shutdown()
        self.thread.join(timeout=2)
        self.httpd.server_close()


class ModelChannelPolicyTests(unittest.TestCase):
    def test_sealed_catalog_matches_committed_registry_rows(self):
        registry = identity.load_registry()
        for row in policy.reviewed_rows():
            loaded = registry.by_path_id[row["path_id"]]
            self.assertEqual(loaded.source_type, "model_channel")
            self.assertEqual(loaded.intended_use, "training_candidate")
            self.assertEqual(loaded.project_training_policy, "allowed")
            self.assertEqual(loaded.training_ready_policy, "never")
            self.assertEqual(loaded.model_id, row["model_id"])
            self.assertEqual(loaded.channel, row["channel"])
            self.assertEqual(loaded.provider, row["provider"])
            self.assertEqual(
                loaded.model_channel_policy_sha256, policy.POLICY_SHA256
            )

    def test_channels_are_not_conflated_across_same_vendor(self):
        registry = identity.load_registry()
        glimmer = registry.by_path_id["muse-glimmer-30b-local-factory"]
        spark = [
            row for row in registry.by_path_id.values()
            if row.generator == "muse-spark-1.2"
        ][0]
        self.assertEqual((glimmer.provider, glimmer.channel), ("meta", "local_vllm"))
        self.assertEqual((spark.provider, spark.channel), ("meta", "api"))
        self.assertNotEqual(glimmer.rights_profile_id, spark.rights_profile_id)

        local_light = registry.by_path_id["nemotron-lightning-30b-vllm-factory"]
        remote_light = registry.by_path_id["openrouter-nemotron-3.5-lightning-factory"]
        self.assertEqual(local_light.channel, "local_vllm")
        self.assertEqual(remote_light.channel, "openrouter_api")
        self.assertNotEqual(local_light.generator, remote_light.generator)

        granite = registry.by_path_id["granite-4.2-30b-local-factory"]
        self.assertEqual((granite.provider, granite.channel), ("ibm", "local_vllm"))
        ibm_hosted = rights_classifier.classify_rights(
            rights_classifier.RightsRoute(
                provider="ibm",
                channel="api",
                rights_profile_id=rights_policy.HOSTED_FRONTIER_PROFILE_ID,
            ),
            source_sha256="sha256:" + "a" * 64,
            factory_registry_sha256="sha256:" + "b" * 64,
        )
        self.assertEqual(ibm_hosted.project_training_policy, "blocked")

    def test_no_minimax_rows_are_admitted(self):
        registry = identity.load_registry()
        self.assertFalse(
            any("minimax" in row.path_id for row in registry.by_path_id.values())
        )
        self.assertNotIn(
            "minimax/minimax-m3",
            {row["model_id"] for row in policy.reviewed_rows()},
        )

    def test_discover_lists_snapshot_members_without_fossilizing_an_allow_list(self):
        from model_channel import cli as model_cli

        stdout = StringIO()
        with mock.patch("sys.stdout", stdout):
            code = model_cli.run(
                ["discover-openrouter", "--snapshot", str(SNAPSHOT), "--json"]
            )
        self.assertEqual(code, 0)
        payload = json.loads(stdout.getvalue())
        by_id = {item["id"]: item for item in payload["models"]}
        self.assertIn("microsoft/phi-4", by_id)
        self.assertIn("meta-llama/llama-3.3-70b-instruct", by_id)
        self.assertTrue(by_id["microsoft/phi-4"]["in_reviewed_pilot"])
        self.assertFalse(by_id["meta-llama/llama-3.3-70b-instruct"]["in_reviewed_pilot"])
        self.assertEqual(
            payload["authority"], "snapshot_membership_not_hardcoded_allow_list"
        )

    def test_openrouter_snapshot_membership_is_the_authority(self):
        snapshot = openrouter.load_snapshot(SNAPSHOT)
        ids = {item["id"] for item in snapshot["data"]}
        self.assertIn("meta-llama/llama-3.3-70b-instruct", ids)
        self.assertNotIn(
            "meta-llama/llama-3.3-70b-instruct",
            {row["model_id"] for row in policy.reviewed_rows()},
        )
        openrouter.catalog_entry(snapshot, "microsoft/phi-4")
        with self.assertRaisesRegex(openrouter.OpenRouterError, "absent"):
            openrouter.catalog_entry(snapshot, "minimax/minimax-m3")
        with self.assertRaisesRegex(openrouter.OpenRouterError, "alias"):
            openrouter.catalog_entry(snapshot, "~deepseek/deepseek-pro-latest")

    def test_historical_snapshot_is_not_rewritten_by_a_later_catalog(self):
        snapshot = openrouter.load_snapshot(SNAPSHOT)
        first = openrouter.evidence(
            model_id="microsoft/phi-4",
            snapshot=snapshot,
            entry=openrouter.catalog_entry(snapshot, "microsoft/phi-4"),
            terms_sha256="f" * 64,
            underlying_license_sha256="e" * 64,
            generated_at="2026-09-15T05:30:00Z",
        )
        later = {
            "retrieved_at": "2026-09-16T00:00:00Z",
            "sha256": "0" * 64,
            "source_url": snapshot["source_url"],
            "data": tuple(
                item for item in snapshot["data"] if item["id"] != "microsoft/phi-4"
            ),
        }
        with self.assertRaisesRegex(openrouter.OpenRouterError, "absent"):
            openrouter.catalog_entry(later, "microsoft/phi-4")
        self.assertEqual(first["catalog_sha256"], snapshot["sha256"])
        self.assertEqual(first["generated_at"], "2026-09-15T05:30:00Z")

    def test_nvidia_local_and_openrouter_rights_stay_distinct(self):
        digest = "sha256:" + "c" * 64
        local = rights_classifier.classify_rights(
            rights_classifier.RightsRoute(
                "nvidia",
                "local_vllm",
                rights_policy.OPEN_WEIGHT_LOCAL_PROFILE_ID,
            ),
            source_sha256=digest,
            factory_registry_sha256=digest,
        )
        remote = rights_classifier.classify_rights(
            rights_classifier.RightsRoute(
                "nvidia",
                "openrouter_api",
                rights_policy.OPENROUTER_DISTILLABLE_PROFILE_ID,
            ),
            source_sha256=digest,
            factory_registry_sha256=digest,
        )
        hosted = rights_classifier.classify_rights(
            rights_classifier.RightsRoute(
                "nvidia",
                "api",
                rights_policy.HOSTED_FRONTIER_PROFILE_ID,
            ),
            source_sha256=digest,
            factory_registry_sha256=digest,
        )
        self.assertEqual(local.project_training_policy, "allowed")
        self.assertEqual(remote.project_training_policy, "allowed")
        self.assertEqual(hosted.project_training_policy, "blocked")
        unknown = rights_classifier.classify_rights(
            rights_classifier.RightsRoute(
                "anthropic",
                "openrouter_api",
                rights_policy.UNKNOWN_PROVENANCE_PROFILE_ID,
            ),
            source_sha256=digest,
            factory_registry_sha256=digest,
        )
        self.assertEqual(unknown.project_training_policy, "blocked")


class ModelChannelGenerateTests(unittest.TestCase):
    def test_strips_reasoning_and_refuses_self_certification(self):
        dirty = episode_payload(
            thought="hidden plan",
            training_ready=True,
            goal="visible <think>secret</think> goal",
        )
        stripped = generate.strip_untrainable(dirty)
        self.assertNotIn("thought", stripped)
        self.assertNotIn("training_ready", stripped)
        self.assertEqual(stripped["goal"], "visible  goal")
        self.assertTrue(generate._contains_self_certify(dirty))

        content = json.dumps(episode_payload(training_ready=True))
        with _Server(content, "NVIDIA-Nemotron-3-Nano-4B-BF16") as server:
            with self.assertRaisesRegex(generate.GenerateError, "self-certify"):
                generate.generate_candidate(
                    NANO, TASK, endpoint=server.endpoint, generated_at="2026-09-15T05:30:00Z"
                )

    def test_local_vllm_candidate_preserves_runtime_provenance(self):
        content = json.dumps(episode_payload())
        runtime = {
            "runtime_version": "vllm-0.11.0",
            "device": "NVIDIA GeForce RTX 4080 Laptop GPU",
            "max_model_len": 8192,
            "require_tool_parser": False,
            "require_reasoning_parser": False,
        }
        with _Server(content, "NVIDIA-Nemotron-3-Nano-4B-BF16") as server:
            record = generate.generate_candidate(
                NANO,
                TASK,
                endpoint=server.endpoint,
                runtime=runtime,
                generated_at="2026-09-15T05:30:00Z",
            )
        self.assertEqual(record["meta"]["factory"], NANO)
        self.assertEqual(record["meta"]["channel"], "local_vllm")
        self.assertEqual(record["meta"]["runtime_device"], runtime["device"])
        self.assertNotIn("thought", record)
        self.assertNotIn("training_ready", record)
        self.assertTrue(record["meta"]["candidate_only"])
        self.assertEqual(record["_generation"]["usage"]["total_tokens"], 33)

    def test_openrouter_refuses_fallback_and_records_distillable_evidence(self):
        content = json.dumps(episode_payload())
        with _Server(content, "microsoft/phi-4:free") as server:
            with self.assertRaisesRegex(openrouter.OpenRouterError, "fallback"):
                generate.generate_candidate(
                    PHI,
                    TASK,
                    endpoint=server.endpoint,
                    openrouter_snapshot=SNAPSHOT,
                    generated_at="2026-09-15T05:30:00Z",
                )
        with _Server(content, "microsoft/phi-4") as server:
            record = generate.generate_candidate(
                PHI,
                TASK,
                endpoint=server.endpoint,
                openrouter_snapshot=SNAPSHOT,
                generated_at="2026-09-15T05:30:00Z",
            )
            request = server.httpd.requests[0]
        self.assertEqual(request["provider"], {"allow_fallbacks": False})
        self.assertEqual(record["meta"]["channel"], "openrouter_api")
        self.assertEqual(record["meta"]["openrouter_model_id"], "microsoft/phi-4")
        self.assertEqual(
            record["meta"]["is_trainable_text"], "distillable_catalog_membership"
        )

    def test_vllm_spec_pins_conservative_context_and_refuses_required_parsers(self):
        spec = vllm_mod.launch_spec(
            NANO,
            runtime_version="0.11.0",
            device="NVIDIA GeForce RTX 4080 Laptop GPU",
        )
        self.assertEqual(spec["base_url"], "http://127.0.0.1:8000/v1")
        self.assertEqual(spec["max_model_len"], 8192)
        self.assertEqual(spec["model_id"], "nvidia/NVIDIA-Nemotron-3-Nano-4B-BF16")
        self.assertFalse(spec["require_tool_parser"])
        with self.assertRaisesRegex(vllm_mod.VLLMSpecError, "container digest"):
            vllm_mod.launch_spec(
                NANO,
                runtime_version="0.11.0",
                device="cpu",
                container_image="vllm/vllm-openai:latest",
            )
        with self.assertRaisesRegex(vllm_mod.VLLMSpecError, "max_model_len"):
            vllm_mod.launch_spec(
                NANO,
                runtime_version="0.11.0",
                device="cpu",
                max_model_len=8193,
            )


class ModelChannelRoundTxnTests(unittest.TestCase):
    def _publish(self, slug: str, record: dict) -> dict:
        with tempfile.TemporaryDirectory() as tmp:
            factory = Path(tmp) / "outputs" / "raw" / "2099-01-01" / slug
            factory.mkdir(parents=True)
            self.assertNotIn(slug, round_txn.FACTORY_QUOTAS)
            self.assertNotIn(slug, round_txn.AGENTIC_FACTORY_KINDS)
            reservation = round_txn.reserve(factory, 1, 1)
            stage = Path(reservation["staging_dir"])
            write_records(stage / reservation["batch_file"], [record])
            (stage / reservation["notes_file"]).write_text(
                "# Model-channel critique\n\nBounded fixture candidate.\n"
            )
            return round_txn.publish(factory, 1, reservation["token"])

    def test_bounded_local_and_remote_batches_publish(self):
        local = episode_payload(id="nano-r01-1")
        local["meta"] = {"factory": NANO, "round": 1}
        remote = episode_payload(id="phi-r01-1")
        remote["meta"] = {"factory": PHI, "round": 1}
        local_manifest = self._publish(NANO, local)
        remote_manifest = self._publish(PHI, remote)
        self.assertEqual(local_manifest["records"], 1)
        self.assertEqual(remote_manifest["records"], 1)


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
                   ollama_models=self._models(digest="sha256:" + "0" * 64)) as server:
            with self.assertRaisesRegex(ollama.OllamaSpecError, "digest"):
                ollama.verify_served_identity(server.endpoint, row)
        with _Server(json.dumps(episode_payload()), OLLAMA_TAG,
                   ollama_models=self._models(name="nemotron-3-nano:30b")) as server:
            with self.assertRaisesRegex(ollama.OllamaSpecError, "not served"):
                ollama.verify_served_identity(server.endpoint, row)

    def test_verify_refuses_cloud_tag_identity(self):
        row = dict(policy.reviewed_row(NANO_OLLAMA))
        row["runtime_tag"] = "nemotron-3-nano:30b-cloud"
        with self.assertRaisesRegex(ollama.OllamaSpecError, "cloud"):
            ollama.verify_served_identity("http://127.0.0.1:11434/v1", row)

    def test_candidate_preserves_ollama_provenance(self):
        content = json.dumps(episode_payload())
        with _Server(content, OLLAMA_TAG, ollama_models=self._models()) as server:
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

    def test_unverified_served_identity_refuses_generation(self):
        content = json.dumps(episode_payload())
        runtime = self._runtime()
        with _Server(content, OLLAMA_TAG,
                   ollama_models=self._models(name="nemotron-3-nano:30b-cloud")) as server:
            endpoint = server.endpoint
            with self.assertRaisesRegex(ollama.OllamaSpecError, "not served"):
                generate.generate_candidate(
                    NANO_OLLAMA, TASK, endpoint=endpoint, runtime=runtime
                )
        self.assertEqual(server.httpd.requests, [])


if __name__ == "__main__":
    unittest.main()
