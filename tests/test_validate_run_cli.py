#!/usr/bin/env python3
"""validate_run.py's CLI-level contract: manifest writes, error reporting,
id layering, and the frontier's handling of malformed records.

validate_run.py must not write manifest.json unless --write is passed. This
also locks the shape layer's id-layering rule (`id` coverage belongs to the
deep layer — check_records / training_audit; this layer only type-checks an
id that is present) and the frontier entry point's obligation to return a
verdict instead of raising on untrusted, malformed generated JSONL.
"""

import copy
import io
import json
import sys
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

_TESTS = Path(__file__).resolve().parent
if str(_TESTS) not in sys.path:
    sys.path.insert(0, str(_TESTS))

from validate_run_test_helpers import (  # noqa: E402
    EXPECTED_TOTALS,
    REPO,
    TINY_THALAMIC,
    _invoke,
    _run_with_record,
    _tiny_run_dir,
)

import validate_run  # noqa: E402
import verify_execution  # noqa: E402

V2_SCHEMA = REPO / "schemas" / "thalamic-trajectory-v2.schema.json"


class ValidateRunWriteFlag(unittest.TestCase):
    def test_v2_schema_requires_root_id_and_state_provenance(self):
        schema = json.loads(V2_SCHEMA.read_text())
        strict = schema["allOf"][1]
        self.assertIn("id", strict["required"])
        self.assertIn("state", strict["required"])
        self.assertIn("sim_or_real", strict["properties"]["state"]["required"])

    def test_default_does_not_create_manifest(self):
        with tempfile.TemporaryDirectory() as raw:
            run_dir = _tiny_run_dir(Path(raw))
            result = _invoke(str(run_dir))
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(json.loads(result.stdout), EXPECTED_TOTALS)
            self.assertFalse(
                (run_dir / "manifest.json").exists(),
                "default invoke must not create manifest.json",
            )

    def test_write_creates_manifest_with_matching_totals(self):
        with tempfile.TemporaryDirectory() as raw:
            run_dir = _tiny_run_dir(Path(raw))
            result = _invoke("--write", str(run_dir))
            self.assertEqual(result.returncode, 0, result.stderr)
            stdout_totals = json.loads(result.stdout)
            self.assertEqual(stdout_totals, EXPECTED_TOTALS)
            manifest_path = run_dir / "manifest.json"
            self.assertTrue(manifest_path.is_file())
            manifest = json.loads(manifest_path.read_text())
            self.assertEqual(manifest["totals"], stdout_totals)

    def test_default_does_not_overwrite_existing_manifest(self):
        with tempfile.TemporaryDirectory() as raw:
            run_dir = _tiny_run_dir(Path(raw))
            sentinel = {"sentinel": True, "files": []}
            manifest_path = run_dir / "manifest.json"
            manifest_path.write_text(json.dumps(sentinel) + "\n")
            result = _invoke(str(run_dir))
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(json.loads(manifest_path.read_text()), sentinel)

    def test_non_object_line_is_error_not_traceback(self):
        with tempfile.TemporaryDirectory() as raw:
            run_dir = Path(raw) / "run"
            run_dir.mkdir()
            (run_dir / "junk.jsonl").write_text("null\n")
            result = _invoke(str(run_dir))
            self.assertEqual(result.returncode, 1, result.stderr)
            self.assertNotIn("Traceback", result.stderr)
            self.assertIn("must be a JSON object", result.stderr)

    def test_invalid_utf8_is_error_not_traceback(self):
        with tempfile.TemporaryDirectory() as raw:
            run_dir = Path(raw) / "run"
            run_dir.mkdir()
            (run_dir / "bad.jsonl").write_bytes(b'{"id":"bad-\xff"}\n')
            result = _invoke(str(run_dir))
            self.assertEqual(result.returncode, 1)
            self.assertNotIn("Traceback", result.stderr)
            self.assertIn("invalid UTF-8", result.stderr)

    def test_nonstandard_json_constants_are_parse_errors(self):
        for constant in ("NaN", "Infinity", "-Infinity"):
            with self.subTest(constant=constant), tempfile.TemporaryDirectory() as raw:
                run_dir = Path(raw) / "run"
                run_dir.mkdir()
                (run_dir / "bad-number.jsonl").write_text(
                    '{"goal":"test","steps":[{"decision_basis":"observe",'
                    '"tool_call":{"name":"probe","args":{"value":'
                    + constant
                    + '}},"observation":"ok"}],"outcome":"passed",'
                    '"reward":{"success":true}}\n'
                )

                result = _invoke(str(run_dir))

                self.assertEqual(result.returncode, 1, result.stderr)
                self.assertNotIn("Traceback", result.stderr)
                self.assertIn("JSON parse error", result.stderr)
                self.assertIn(
                    f"non-standard JSON numeric constant {constant}", result.stderr
                )

    def test_literal_unicode_line_separators_stay_inside_one_jsonl_record(self):
        with tempfile.TemporaryDirectory() as raw:
            run_dir = Path(raw) / "run"
            run_dir.mkdir()
            record = copy.deepcopy(TINY_THALAMIC)
            record["safety_decision"]["rationale"] = "before\u2028middle\u2029after"
            (run_dir / "unicode-separators.jsonl").write_text(
                json.dumps(record, ensure_ascii=False) + "\n",
                encoding="utf-8",
            )
            stdout = io.StringIO()
            stderr = io.StringIO()

            with redirect_stdout(stdout), redirect_stderr(stderr):
                with self.assertRaises(SystemExit) as raised:
                    validate_run.main([str(run_dir)])

            self.assertEqual(raised.exception.code, 0, stderr.getvalue())
            self.assertEqual(json.loads(stdout.getvalue()), EXPECTED_TOTALS)
            self.assertEqual(stderr.getvalue(), "")

    def test_non_object_episode_step_is_error_not_traceback(self):
        with tempfile.TemporaryDirectory() as raw:
            run_dir = Path(raw) / "run"
            run_dir.mkdir()
            episode = {
                "goal": "test",
                "steps": [None],
                "outcome": "failed",
                "reward": {"success": False},
            }
            (run_dir / "episode.jsonl").write_text(json.dumps(episode) + "\n")
            result = _invoke(str(run_dir))
            self.assertEqual(result.returncode, 1, result.stderr)
            self.assertNotIn("Traceback", result.stderr)
            self.assertIn("step 0: must be an object", result.stderr)

    def test_bridge_requires_globally_sorted_finite_events(self):
        with tempfile.TemporaryDirectory() as raw:
            run_dir = Path(raw) / "run"
            run_dir.mkdir()
            bridge = {
                "spike_events": [
                    {"channel": "a", "t_rel_ms": 2.0, "amplitude": 0.4},
                    {"channel": "b", "t_rel_ms": 1.0, "amplitude": 0.3},
                ],
                "language_view": {"trajectory": copy.deepcopy(TINY_THALAMIC)},
            }
            (run_dir / "bridge.jsonl").write_text(json.dumps(bridge) + "\n")
            result = _invoke(str(run_dir))
            self.assertEqual(result.returncode, 1, result.stderr)
            self.assertIn("not globally non-decreasing", result.stderr)


class ValidateIdLayering(unittest.TestCase):
    """The shape layer type-checks `id`; coverage is a deep-layer concern.

    check_records / training_audit own "every record has a canonical id".
    validate_run must not reject a legacy record for a missing id, or the
    routing regresses to hiding every other invariant behind an id error.
    """

    def test_valid_string_id_accepted(self):
        rec = copy.deepcopy(TINY_THALAMIC)
        rec["id"] = "tiny-001"
        result = _run_with_record(rec)
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_missing_id_is_not_a_shape_error(self):
        rec = copy.deepcopy(TINY_THALAMIC)
        rec.pop("id", None)
        result = _run_with_record(rec)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertNotIn("'id'", result.stderr)

    def test_non_string_id_rejected(self):
        rec = copy.deepcopy(TINY_THALAMIC)
        rec["id"] = 123
        result = _run_with_record(rec)
        self.assertEqual(result.returncode, 1, result.stderr)
        self.assertIn("'id' must be a non-empty string", result.stderr)

    def test_blank_id_rejected(self):
        rec = copy.deepcopy(TINY_THALAMIC)
        rec["id"] = "   "
        result = _run_with_record(rec)
        self.assertEqual(result.returncode, 1, result.stderr)
        self.assertIn("'id' must be a non-empty string", result.stderr)


class VerifyFrontierMalformedRecords(unittest.TestCase):
    """Malformed records must reach a verdict through the frontier entry point.

    verify_batch_for_frontier runs over untrusted generated JSONL, so a
    non-string safety_decision.rationale or a non-object
    language_view.trajectory must return failed instead of raising and taking
    the frontier gate down with it.
    """

    def _verify(self, record):
        with tempfile.TemporaryDirectory() as raw:
            batch = Path(raw) / "batch-r01.jsonl"
            batch.write_text(json.dumps(record) + "\n")
            return verify_execution.verify_batch_for_frontier(batch, strict=True)

    def test_non_string_rationale_blocks_without_raising(self):
        rec = copy.deepcopy(TINY_THALAMIC)
        rec["safety_decision"] = {
            "decision": "ACCEPT",
            "rationale": {"hidden": "object"},
        }
        counts, findings, blocked = self._verify(rec)
        self.assertEqual(counts["failed"], 1, findings)
        self.assertTrue(blocked)
        self.assertEqual(findings[0]["status"], "failed")

    def test_non_object_trajectory_blocks_without_raising(self):
        record = {
            "spike_events": [{"channel": "a", "t_rel_ms": 1.0, "amplitude": 0.2}],
            "language_view": {"trajectory": "not-an-object"},
        }
        counts, findings, blocked = self._verify(record)
        self.assertEqual(counts["failed"], 1, findings)
        self.assertEqual(counts["verified"], 0, findings)
        self.assertTrue(blocked)
        self.assertIn("missing or not an object", findings[0]["reason"])


if __name__ == "__main__":
    unittest.main()
