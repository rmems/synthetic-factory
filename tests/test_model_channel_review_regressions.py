"""Model-channel input, candidate, and output publication boundaries."""

import json
from io import StringIO
from pathlib import Path
import tempfile
import unittest
from unittest import mock

from pipelines.model_channel import cli, generate
from pipelines import rights_classifier, rights_policy
from test_model_channel import NANO, episode_payload


def completion(record):
    return {"choices": [{"message": {"content": json.dumps(record)}}]}


class InputFiles(unittest.TestCase):
    def test_task_and_runtime_files_require_strict_json_objects(self):
        invalid = (
            '{"goal":"first","goal":"second"}',
            '{"value":NaN}',
            '{"value":Infinity}',
            '{"value":1e400}',
            "[]",
        )
        for target in ("task", "runtime"):
            for payload in invalid:
                with (
                    self.subTest(target=target, payload=payload),
                    tempfile.TemporaryDirectory() as tmp,
                ):
                    root = Path(tmp)
                    task, runtime, out = root / "task.json", root / "runtime.json", root / "out"
                    task.write_text('{"goal":"repair the fixture"}', encoding="utf-8")
                    runtime.write_text("{}", encoding="utf-8")
                    {"task": task, "runtime": runtime}[target].write_text(payload, encoding="utf-8")
                    args = [
                        "generate",
                        "--path-id",
                        NANO,
                        "--task",
                        str(task),
                        "--runtime-json",
                        str(runtime),
                        "--endpoint",
                        "http://localhost/v1",
                        "--out",
                        str(out),
                        "--produced-at",
                        "2026-09-18T00:00:00Z",
                    ]
                    with (
                        mock.patch.object(
                            generate, "generate_candidate", return_value=episode_payload()
                        ),
                        mock.patch("sys.stderr", StringIO()),
                        mock.patch("sys.stdout", StringIO()),
                    ):
                        code = cli.run(args)
                    self.assertEqual(code, 2)
                    self.assertFalse(out.exists())


class CandidateValidation(unittest.TestCase):
    def test_reasoning_key_variants_are_removed_recursively(self):
        keys = ("chainOfThought", "Chain-Of-Thought", "INTERNAL_REASONING", "reasoningContent")
        for key in keys:
            with self.subTest(key=key):
                record = episode_payload()
                record["steps"][0][key] = "private trace"
                accepted = generate._accepted_record(completion(record))
                self.assertNotIn(key, accepted["steps"][0])
                self.assertEqual(accepted["steps"][0]["observation"], "removed lock")

    def test_self_certification_key_variants_are_refused_recursively(self):
        for key in ("trainingReady", "Training-Eligible", "ORACLE_VERIFIED", "executionVerified"):
            with self.subTest(key=key):
                record = episode_payload()
                record["steps"][0][key] = True
                with self.assertRaisesRegex(generate.GenerateError, "self-certify"):
                    generate._accepted_record(completion(record))

    def test_incomplete_or_malformed_tool_turns_are_refused(self):
        invalid = (
            {},
            {"tool_call": "bash"},
            {"tool_call": {"name": "bash", "args": []}},
            {"observation": ""},
            {"decision_basis": ""},
            {"decision_basis": "I just know this is best"},
        )
        for fields in invalid:
            with self.subTest(fields=fields):
                record = episode_payload()
                if fields:
                    record["steps"][0].update(fields)
                else:
                    record["steps"] = [{}]
                with self.assertRaises(generate.GenerateError):
                    generate._accepted_record(completion(record))

    def test_terminal_outcome_must_agree_with_success(self):
        with self.assertRaises(generate.GenerateError):
            generate._accepted_record(completion(episode_payload(outcome="failed")))


class RunPublication(unittest.TestCase):
    def _write(self, out, records=None):
        return generate.write_run(
            out,
            path_id=NANO,
            records=[episode_payload()] if records is None else records,
            attempted=1,
            rejected=[],
            produced_at="2026-09-18T00:00:00Z",
        )

    def test_serialization_failure_leaves_no_destination_and_allows_retry(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            out = root / "out"
            with self.assertRaises(ValueError):
                self._write(out, [{"bad": float("nan")}])
            self.assertFalse(out.exists())
            self.assertEqual(list(root.iterdir()), [])
            self.assertEqual(self._write(out)["accepted"], 1)

    def test_summary_write_failure_leaves_no_destination_and_allows_retry(self):
        original_write = Path.write_text

        def fail_summary(path, *args, **kwargs):
            if path.name == "RUN.json":
                raise OSError("injected summary write failure")
            return original_write(path, *args, **kwargs)

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            out = root / "out"
            with mock.patch.object(Path, "write_text", fail_summary):
                with self.assertRaisesRegex(OSError, "injected summary"):
                    self._write(out)
            self.assertFalse(out.exists())
            self.assertEqual(list(root.iterdir()), [])
            self.assertEqual(self._write(out)["accepted"], 1)

    def test_destination_created_during_staging_is_not_replaced(self):
        original_write = Path.write_text
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            out = root / "out"

            def concurrent_destination(path, *args, **kwargs):
                if path.name == "RUN.json":
                    out.mkdir(exist_ok=True)
                return original_write(path, *args, **kwargs)

            with mock.patch.object(Path, "write_text", concurrent_destination):
                with self.assertRaises(generate.GenerateError):
                    self._write(out)
            self.assertEqual(list(root.iterdir()), [out])
            self.assertEqual(list(out.iterdir()), [])


class OllamaVocabulary(unittest.TestCase):
    def test_vocabulary_only_ollama_routes_cannot_get_training_authorization(self):
        for provider in ("nvidia", "meta", "ibm"):
            with (
                self.subTest(provider=provider),
                self.assertRaises(rights_policy.RightsPolicyError),
            ):
                rights_classifier.classify_rights(
                    rights_classifier.RightsRoute(
                        provider, "local_ollama", rights_policy.OPEN_WEIGHT_LOCAL_PROFILE_ID
                    ),
                    source_sha256="sha256:" + "a" * 64,
                    factory_registry_sha256="sha256:" + "b" * 64,
                )
