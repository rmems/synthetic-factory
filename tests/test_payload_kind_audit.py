#!/usr/bin/env python3
"""Classification tests for the read-only payload-kind audit.

CLI (--json/--expect) behavior is covered in test_payload_kind_audit_cli.py.
The published #74 finding itself is pinned in test_payload_kind_audit_published.py
(committed evidence) and test_payload_kind_audit_fidelity.py (raw-corpus re-derivation).
"""

import hashlib
import io
import json
import sys
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from unittest.mock import patch

_TESTS = Path(__file__).resolve().parent
if str(_TESTS) not in sys.path:
    sys.path.insert(0, str(_TESTS))

from payload_kind_audit_fixtures import REPO, _episode, _step, _thalamic, _write_corpus  # noqa: E402

PIPELINES = REPO / "pipelines"
if str(PIPELINES) not in sys.path:
    sys.path.insert(0, str(PIPELINES))

import payload_kind_audit  # noqa: E402


class PayloadKindClassification(unittest.TestCase):
    """The auditor measures the mix; it never guesses at an unknown shape."""

    def _audit(self, files):
        with tempfile.TemporaryDirectory() as raw:
            directory = Path(raw)
            _write_corpus(directory, files)
            before = {
                path.name: hashlib.sha256(path.read_bytes()).hexdigest()
                for path in sorted(directory.iterdir())
            }
            audit = payload_kind_audit.build_audit(directory)
            after = {
                path.name: hashlib.sha256(path.read_bytes()).hexdigest()
                for path in sorted(directory.iterdir())
            }
            self.assertEqual(before, after, "the audit must never write to the corpus")
            return audit

    def _assert_build_audit_rejects(self, name, content, expected_substring):
        """Write one raw-text payload file and assert build_audit fails closed.

        Shares the boilerplate across the "one malformed file -> one
        PayloadKindAuditError substring" tests without hiding any of their
        per-input file name, content, or expected message - each caller still
        states its own three values explicitly.
        """
        with tempfile.TemporaryDirectory() as raw:
            directory = Path(raw)
            (directory / name).write_text(content, encoding="utf-8")
            with self.assertRaises(payload_kind_audit.PayloadKindAuditError) as caught:
                payload_kind_audit.build_audit(directory)
        self.assertIn(expected_substring, str(caught.exception))

    def test_a_mixed_corpus_reports_both_kinds_and_where_they_live(self):
        audit = self._audit(
            {
                "batch-r02.jsonl": [
                    _thalamic("act-r02-001", _episode([_step(1, thought="t")])),
                    _thalamic(
                        "act-r02-002",
                        _episode([_step(1, thought="t"), _step(2, thought="t")]),
                        supervisor="gate-v2",
                        decision="REJECT",
                    ),
                ],
                # Legacy payload filename: it does not match batch-r*.jsonl and is
                # exactly what a batch-only glob drops.
                "episodes.jsonl": [
                    _episode([_step(1, decision_basis="b"), _step(2, decision_basis="b")])
                ],
            }
        )

        self.assertEqual(audit["summary"]["files"], 2)
        self.assertEqual(audit["summary"]["records"], 3)
        self.assertEqual(audit["summary"]["kinds"], {"episode": 1, "thalamic": 2})
        self.assertEqual(
            audit["summary"]["meta_factory_stamps"],
            {"agentic-coding-trajectory-factory": 3},
        )
        self.assertEqual(audit["summary"]["thalamic_records_wrapping_a_coding_episode"], 2)
        self.assertEqual(audit["summary"]["coding_episodes_reachable_at_top_level"], 1)
        self.assertEqual(audit["summary"]["coding_episodes_including_wrapped"], 3)
        self.assertEqual(audit["summary"]["coding_steps"], {"native": 2, "wrapped": 3, "total": 5})
        self.assertEqual(
            audit["summary"]["coding_steps_by_reasoning_field"],
            {"decision_basis": 2, "reflection": 0, "thought": 3},
        )

        by_source = {(row["source_file"], row["source_line"]): row for row in audit["records"]}
        self.assertEqual(by_source[("batch-r02.jsonl", 1)]["id"], "act-r02-001")
        self.assertEqual(by_source[("batch-r02.jsonl", 2)]["gate_decision"], "REJECT")
        self.assertEqual(by_source[("batch-r02.jsonl", 2)]["supervisor_id"], "gate-v2")
        # An episode record in this lane carries no top-level id, and the audit
        # reports that rather than inventing one.
        self.assertIsNone(by_source[("episodes.jsonl", 1)]["id"])
        self.assertFalse(by_source[("episodes.jsonl", 1)]["wraps_coding_episode"])

        files = {entry["path"]: entry for entry in audit["files"]}
        self.assertEqual(files["episodes.jsonl"]["kinds"], {"episode": 1})
        self.assertEqual(files["batch-r02.jsonl"]["kinds"], {"thalamic": 2})

    def test_a_gate_record_without_a_wrapped_episode_is_reported_as_such(self):
        audit = self._audit(
            {"batch-r02.jsonl": [_thalamic("act-r02-001", {"summary": "no episode was executed"})]}
        )
        row = audit["records"][0]
        self.assertEqual(row["kind"], "thalamic")
        self.assertFalse(row["wraps_coding_episode"])
        self.assertEqual(row["coding_steps"], 0)
        self.assertEqual(audit["summary"]["thalamic_records_wrapping_a_coding_episode"], 0)
        self.assertEqual(audit["summary"]["coding_episodes_including_wrapped"], 0)

    def test_episode_identity_uses_every_supported_legacy_key(self):
        for key in payload_kind_audit.LEGACY_ID_KEYS:
            with self.subTest(key=key):
                record = _episode([])
                record[key] = f"{key}-value"
                audit = self._audit({"episodes.jsonl": [record]})
                self.assertEqual(audit["records"][0]["id"], f"{key}-value")

    def test_episode_identity_uses_the_first_present_supported_key(self):
        record = _episode([])
        for key in reversed(payload_kind_audit.LEGACY_ID_KEYS):
            record[key] = f"{key}-value"
        audit = self._audit({"episodes.jsonl": [record]})
        self.assertEqual(
            audit["records"][0]["id"],
            f"{payload_kind_audit.LEGACY_ID_KEYS[0]}-value",
        )

    def test_thalamic_identity_prefers_the_top_level_id_over_state_episode_id(self):
        record = _thalamic("legacy-episode-id", {"summary": "no episode was executed"})
        record["id"] = "canonical-record-id"
        audit = self._audit({"batch-r02.jsonl": [record]})
        self.assertEqual(audit["records"][0]["id"], "canonical-record-id")

    def test_thalamic_identity_falls_back_to_state_episode_id_without_a_top_level_id(self):
        record = _thalamic("legacy-episode-id", {"summary": "no episode was executed"})
        self.assertNotIn("id", record)
        audit = self._audit({"batch-r02.jsonl": [record]})
        self.assertEqual(audit["records"][0]["id"], "legacy-episode-id")

    def test_steps_without_a_goal_are_not_counted_as_a_wrapped_episode(self):
        audit = self._audit({"batch-r02.jsonl": [_thalamic("act-r02-001", {"steps": [_step(1)]})]})
        self.assertFalse(audit["records"][0]["wraps_coding_episode"])
        self.assertEqual(audit["records"][0]["coding_steps"], 0)
        self.assertEqual(
            audit["summary"]["coding_steps"],
            {"native": 0, "wrapped": 0, "total": 0},
        )

    def test_malformed_gate_metadata_containers_fail_closed(self):
        for field in ("state", "safety_decision"):
            with self.subTest(field=field):
                with tempfile.TemporaryDirectory() as raw:
                    directory = Path(raw)
                    record = _thalamic("act-r02-001", {"summary": "no episode"})
                    record[field] = "not-an-object"
                    _write_corpus(directory, {"batch-r02.jsonl": [record]})
                    with self.assertRaises(payload_kind_audit.PayloadKindAuditError) as caught:
                        payload_kind_audit.build_audit(directory)
                self.assertIn(
                    f"batch-r02.jsonl:1.{field} must be a JSON object", str(caught.exception)
                )

    def test_malformed_episode_step_containers_fail_closed(self):
        malformed = (
            _episode("not-a-list"),
            _episode([_step(1), "not-an-object"]),
        )
        for record in malformed:
            with self.subTest(steps=record["steps"]):
                with tempfile.TemporaryDirectory() as raw:
                    directory = Path(raw)
                    _write_corpus(directory, {"episodes.jsonl": [record]})
                    with self.assertRaises(payload_kind_audit.PayloadKindAuditError) as caught:
                        payload_kind_audit.build_audit(directory)
                self.assertIn("episodes.jsonl:1.steps", str(caught.exception))

    def test_other_valid_curation_kinds_are_rejected_not_misreported_as_episodes(self):
        preference = {
            "id": "pair-1",
            "chosen": _episode([_step(1)]),
            "rejected": _episode([_step(1)]),
        }
        bridge = {
            "language_view": {"trajectory": _thalamic("bridge-1", _episode([_step(1)]))},
            "spike_events": [],
        }
        for record, kind in ((preference, "preference"), (bridge, "bridge_pair")):
            with self.subTest(kind=kind):
                with tempfile.TemporaryDirectory() as raw:
                    directory = Path(raw)
                    _write_corpus(directory, {"batch-r01.jsonl": [record]})
                    with self.assertRaises(payload_kind_audit.PayloadKindAuditError) as caught:
                        payload_kind_audit.build_audit(directory)
                self.assertIn(f"payload kind '{kind}'", str(caught.exception))

    def test_unicode_line_separator_inside_json_string_is_not_a_record_boundary(self):
        with tempfile.TemporaryDirectory() as raw:
            directory = Path(raw)
            record = _episode([_step(1)])
            record["goal"] = "first\u2028second"
            (directory / "episodes.jsonl").write_text(
                json.dumps(record, ensure_ascii=False) + "\n", encoding="utf-8"
            )
            audit = payload_kind_audit.build_audit(directory)
        self.assertEqual(audit["summary"]["records"], 1)

    def test_non_standard_json_constants_are_rejected(self):
        self._assert_build_audit_rejects(
            "episodes.jsonl",
            '{"goal":"g","steps":[],"meta":{"score":NaN}}\n',
            "non-standard JSON constant",
        )

    def test_numeric_literals_that_overflow_to_infinity_are_rejected(self):
        self._assert_build_audit_rejects(
            "episodes.jsonl",
            '{"id":1e400,"goal":"g","steps":[]}\n',
            "outside the finite float range",
        )

    def test_duplicate_object_keys_are_rejected(self):
        self._assert_build_audit_rejects(
            "episodes.jsonl",
            '{"goal":"g","steps":"bad","steps":[]}\n',
            "duplicate JSON object key",
        )

    def test_unicode_whitespace_only_lines_are_rejected(self):
        with tempfile.TemporaryDirectory() as raw:
            directory = Path(raw)
            (directory / "episodes.jsonl").write_bytes(
                b'{"goal":"g","steps":[]}\n' + "\u00a0".encode("utf-8") + b"\n"
            )
            with self.assertRaises(payload_kind_audit.PayloadKindAuditError) as caught:
                payload_kind_audit.build_audit(directory)
        self.assertIn("episodes.jsonl:2", str(caught.exception))

    def test_unpaired_surrogates_are_rejected(self):
        with tempfile.TemporaryDirectory() as raw:
            directory = Path(raw)
            (directory / "episodes.jsonl").write_text(
                '{"id":"\\ud800","goal":"g","steps":[]}\n',
                encoding="utf-8",
            )
            with self.assertRaises(payload_kind_audit.PayloadKindAuditError) as caught:
                payload_kind_audit.build_audit(directory)
            err = io.StringIO()
            with redirect_stderr(err), redirect_stdout(io.StringIO()):
                code = payload_kind_audit.main([str(directory), "--markdown"])
        self.assertIn("unpaired UTF-16 surrogate", str(caught.exception))
        self.assertEqual(code, 2)
        self.assertIn("payload-kind audit failed", err.getvalue())

    def test_excessively_nested_json_is_a_controlled_audit_error(self):
        depth = 2000
        nested = "[" * depth + "]" * depth
        line = '{"goal":"g","steps":[],"meta":' + nested + "}"
        with tempfile.TemporaryDirectory() as raw:
            directory = Path(raw)
            (directory / "episodes.jsonl").write_text(line + "\n", encoding="utf-8")
            with self.assertRaises(payload_kind_audit.PayloadKindAuditError) as caught:
                payload_kind_audit.build_audit(directory)
            err = io.StringIO()
            with redirect_stderr(err), redirect_stdout(io.StringIO()):
                code = payload_kind_audit.main([str(directory)])
        self.assertIn("episodes.jsonl:1", str(caught.exception))
        self.assertEqual(code, 2)
        self.assertIn("payload-kind audit failed", err.getvalue())


    def test_final_bare_cr_is_preserved_in_record_digest(self):
        record = b'{"goal":"g","steps":[]}'
        with tempfile.TemporaryDirectory() as raw:
            directory = Path(raw)
            (directory / "episodes.jsonl").write_bytes(record + b"\r")
            audit = payload_kind_audit.build_audit(directory)
        self.assertEqual(
            audit["records"][0]["sha256"],
            hashlib.sha256(record + b"\r").hexdigest(),
        )

    def test_invalid_utf8_and_read_failures_are_controlled_audit_errors(self):
        with tempfile.TemporaryDirectory() as raw:
            directory = Path(raw)
            payload = directory / "episodes.jsonl"
            payload.write_bytes(b'{"goal":"\xff","steps":[]}\n')
            with self.assertRaises(payload_kind_audit.PayloadKindAuditError) as caught:
                payload_kind_audit.build_audit(directory)
            self.assertIn("not valid UTF-8", str(caught.exception))

            payload.write_text(json.dumps(_episode([])) + "\n", encoding="utf-8")
            with patch.object(Path, "read_bytes", side_effect=OSError("denied")):
                with self.assertRaises(payload_kind_audit.PayloadKindAuditError) as caught:
                    payload_kind_audit.build_audit(directory)
            self.assertIn("cannot read payload", str(caught.exception))

    def test_empty_or_payload_free_corpora_are_rejected(self):
        for empty_file in (False, True):
            with self.subTest(empty_file=empty_file):
                with tempfile.TemporaryDirectory() as raw:
                    directory = Path(raw)
                    if empty_file:
                        (directory / "episodes.jsonl").write_text("\n", encoding="utf-8")
                    with self.assertRaises(payload_kind_audit.PayloadKindAuditError) as caught:
                        payload_kind_audit.build_audit(directory)
                expected = "no auditable records" if empty_file else "no *.jsonl payloads"
                self.assertIn(expected, str(caught.exception))


    def test_markdown_preserves_falsy_record_identifiers(self):
        for identifier in (0, False):
            with self.subTest(identifier=identifier):
                record = _episode([])
                record["id"] = identifier
                audit = self._audit({"episodes.jsonl": [record]})
                self.assertEqual(audit["records"][0]["id"], identifier)
                rendered = payload_kind_audit.render_markdown(audit)
                self.assertIn(f"| episode | `{identifier}` |", rendered)
        audit = self._audit({"episodes.jsonl": [_episode([])]})
        self.assertIsNone(audit["records"][0]["id"])
        self.assertIn("| episode | — |", payload_kind_audit.render_markdown(audit))

    def test_markdown_preserves_falsy_supervisor_ids(self):
        for supervisor in (0, False):
            with self.subTest(supervisor=supervisor):
                record = _thalamic("act-r02-001", _episode([]), supervisor=supervisor)
                audit = self._audit({"batch-r02.jsonl": [record]})
                self.assertEqual(audit["records"][0]["supervisor_id"], supervisor)
                rendered = payload_kind_audit.render_markdown(audit)
                self.assertIn(f"| {supervisor} / MODIFY |", rendered)
        record = _thalamic("act-r02-001", _episode([]), supervisor=None)
        audit = self._audit({"batch-r02.jsonl": [record]})
        self.assertIsNone(audit["records"][0]["supervisor_id"])
        self.assertIn("| — / MODIFY |", payload_kind_audit.render_markdown(audit))

    def test_markdown_escapes_dynamic_table_values(self):
        audit = {
            "records": [
                {
                    "source_file": "batch|name.jsonl",
                    "source_line": 1,
                    "kind": "thalamic",
                    "id": "id|`tick`\nnext",
                    "supervisor_id": "gate|one",
                    "gate_decision": "MODIFY\nNOW",
                    "wraps_coding_episode": True,
                    "coding_steps": 2,
                }
            ]
        }
        rendered = payload_kind_audit.render_markdown(audit)
        self.assertIn("batch&#124;name.jsonl", rendered)
        self.assertIn("id&#124;`tick`<br>next", rendered)
        self.assertIn("gate&#124;one / MODIFY<br>NOW", rendered)

    def test_markdown_escapes_link_and_image_syntax_in_gate_cells(self):
        audit = {
            "records": [
                {
                    "source_file": "batch.jsonl",
                    "source_line": 1,
                    "kind": "thalamic",
                    "id": "id-1",
                    "supervisor_id": "![tracker](https://example.test/pixel)",
                    "gate_decision": "[click me](https://example.test/bad)",
                    "wraps_coding_episode": True,
                    "coding_steps": 2,
                }
            ]
        }
        rendered = payload_kind_audit.render_markdown(audit)
        self.assertNotIn("![tracker](", rendered)
        self.assertNotIn("[click me](", rendered)
        self.assertIn("!&#91;tracker&#93;(https://example.test/pixel)", rendered)
        self.assertIn("&#91;click me&#93;(https://example.test/bad)", rendered)

    def test_a_record_the_lane_cannot_classify_fails_loudly_with_its_coordinate(self):
        with tempfile.TemporaryDirectory() as raw:
            directory = Path(raw)
            _write_corpus(directory, {"batch-r02.jsonl": [{"who": "knows"}]})
            with self.assertRaises(payload_kind_audit.PayloadKindAuditError) as caught:
                payload_kind_audit.build_audit(directory)
        self.assertIn("batch-r02.jsonl:1", str(caught.exception))

    def test_a_malformed_line_fails_loudly_instead_of_being_skipped(self):
        self._assert_build_audit_rejects(
            "batch-r02.jsonl",
            json.dumps(_episode([_step(1)])) + "\nnot json\n",
            "batch-r02.jsonl:2",
        )

    def test_a_non_object_record_is_rejected(self):
        self._assert_build_audit_rejects(
            "batch-r02.jsonl", "[1, 2, 3]\n", "must be a JSON object"
        )

    def test_a_missing_corpus_directory_is_rejected(self):
        with self.assertRaises(payload_kind_audit.PayloadKindAuditError):
            payload_kind_audit.build_audit(REPO / "docs" / "no-such-corpus")


if __name__ == "__main__":
    unittest.main()
