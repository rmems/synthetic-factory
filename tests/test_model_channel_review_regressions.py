"""Model-channel input, candidate, and output publication boundaries."""

import json
import os
from io import StringIO
from pathlib import Path
import tempfile
import unittest
from unittest import mock

from pipelines.model_channel import _contract as contract
from pipelines.model_channel import cli, generate, openrouter
from pipelines import rights_classifier, rights_policy, validate_run, validate_run_episode
from pipelines import validate_run_episode_turns as episode_turns
from test_model_channel import NANO, episode_payload

OUTSIDE_PATHS = ("/etc/passwd", os.getcwd() + "/../" * 12 + "etc/passwd")
OUTSIDE_NEW = Path("/etc/model-channel-new-out")
OUTSIDE_MSG = "outside the working, home and temp trees"


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

    def test_dangling_destination_symlink_is_preserved(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            out = root / "out"
            out.symlink_to("missing-directory", target_is_directory=True)
            with self.assertRaisesRegex(generate.GenerateError, "already exists"):
                self._write(out)
            self.assertEqual(out.readlink(), Path("missing-directory"))
            self.assertEqual(list(root.iterdir()), [out])

    def test_raw_tree_destination_is_refused_before_parent_creation(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            with self.assertRaisesRegex(generate.GenerateError, "raw tree"):
                self._write(root / "outputs/raw/factory")
            self.assertEqual(list(root.iterdir()), [])


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


class FacadeCompatibility(unittest.TestCase):
    def test_direct_spelling_keeps_the_same_facade_bindings(self):
        import model_channel._contract as direct

        self.assertIs(direct.check_episode, validate_run.check_episode)
        self.assertIs(direct.normalized_key, episode_turns._normalized_hidden_key)
        self.assertIs(direct.check_episode, contract.check_episode)

    def test_facade_kwargs_still_refuse_terminal_mismatch(self):
        mismatched = episode_payload(outcome="failed")
        errors = contract.check_episode(
            mismatched,
            "candidate episode",
            forbid_hidden_thought=True,
            enforce_terminal_outcome=True,
        )
        self.assertTrue(any("outcome must agree" in item for item in errors))
        with self.assertRaises(generate.GenerateError):
            generate._require_episode(mismatched)

    def test_staged_check_episode_rejects_the_legacy_kwargs(self):
        with self.assertRaises(TypeError):
            validate_run_episode.check_episode(
                episode_payload(),
                "candidate episode",
                forbid_hidden_thought=True,
                enforce_terminal_outcome=True,
            )


class OperatorPathGuards(unittest.TestCase):
    def test_input_object_refuses_outside_paths_without_reading_them(self):
        reads = []
        original = Path.read_bytes

        def spy(self, *args, **kwargs):
            reads.append(os.fspath(self))
            return original(self, *args, **kwargs)

        with mock.patch.object(Path, "read_bytes", spy):
            for candidate in OUTSIDE_PATHS:
                with self.subTest(candidate=candidate):
                    with self.assertRaisesRegex(ValueError, OUTSIDE_MSG):
                        cli._input_object(Path(candidate), argument="--task")
        self.assertEqual(reads, [])

    def test_read_snapshot_refuses_outside_paths_without_reading_them(self):
        reads = []
        original = Path.read_bytes

        def spy(self, *args, **kwargs):
            reads.append(os.fspath(self))
            return original(self, *args, **kwargs)

        with mock.patch.object(Path, "read_bytes", spy):
            for candidate in OUTSIDE_PATHS:
                with self.subTest(candidate=candidate):
                    with self.assertRaisesRegex(openrouter.OpenRouterError, OUTSIDE_MSG):
                        openrouter._read_snapshot(Path(candidate))
        self.assertEqual(reads, [])

    def test_publish_run_refuses_an_outside_destination_before_opening_it(self):
        opened = []
        original_open = os.open

        def spy(path, flags, *args, **kwargs):
            opened.append(path)
            return original_open(path, flags, *args, **kwargs)

        with tempfile.TemporaryDirectory() as tmp, mock.patch.object(os, "open", spy):
            staged = Path(tmp) / "staged"
            staged.mkdir()
            with self.assertRaisesRegex(generate.GenerateError, OUTSIDE_MSG):
                generate._publish_run(staged, OUTSIDE_NEW)
        self.assertEqual(opened, [])
        self.assertFalse(OUTSIDE_NEW.exists())

    def test_write_run_refuses_an_outside_destination_without_creating_it(self):
        with self.assertRaisesRegex(generate.GenerateError, OUTSIDE_MSG):
            generate.write_run(
                OUTSIDE_NEW,
                path_id=NANO,
                records=[episode_payload()],
                attempted=1,
                rejected=[],
                produced_at="2026-09-18T00:00:00Z",
            )
        self.assertFalse(OUTSIDE_NEW.exists())

    def test_input_object_and_snapshot_refuse_symlinked_leaves(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            real = root / "payload.json"
            real.write_text('{"goal":"repair the fixture","data":[{"id":"x"}]}', encoding="utf-8")
            link = root / "linked.json"
            link.symlink_to(real)
            with self.assertRaisesRegex(ValueError, "symlink"):
                cli._input_object(link, argument="--task")
            with self.assertRaisesRegex(openrouter.OpenRouterError, "symlink"):
                openrouter._read_snapshot(link)
