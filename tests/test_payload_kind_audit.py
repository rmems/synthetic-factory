#!/usr/bin/env python3
"""Tests for the read-only payload-kind audit and the published #74 finding."""

import hashlib
import io
import json
import sys
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from unittest.mock import patch

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "pipelines"))

import payload_kind_audit  # noqa: E402

AUDIT_JSON = REPO / "docs" / "agentic-coding-payload-kind.json"
AUDIT_DOC = REPO / "docs" / "agentic-coding-payload-kind.md"

# The keys build_audit derives from a corpus. The published document adds
# context around them (Hub cross-reference, card text) that no corpus scan can
# produce; only the derived keys are re-derivable.
DERIVED_KEYS = ("schema_version", "source", "summary", "files", "records")

# Every thalamic record id issue #74 lists, in published order.
ISSUE_74_THALAMIC_IDS = (
    "act-r02-001",
    "act-r02-002",
    "act-r03-001",
    "act-r03-002",
    "act-r04-001",
    "act-r04-002",
    "act-r05-001",
    "act-r05-002",
    "act-r06-001",
    "act-r06-002",
    "act-r07-001",
    "act-r07-002",
    "act-r08-001",
    "act-r08-002",
    "act-r09-001",
    "act-r09-002",
)


def _step(n, **extra):
    step = {
        "n": n,
        "tool_call": {"name": "bash", "args": {"command": "pytest -q"}},
        "observation": "1 failed",
    }
    step.update(extra)
    return step


def _episode(steps):
    return {
        "goal": "fix the failing test",
        "steps": steps,
        "outcome": "SUCCESS",
        "reward": {"success": True},
        "meta": {"factory": "agentic-coding-trajectory-factory", "round": 2},
    }


def _thalamic(episode_id, executed, *, supervisor="gate-v1", decision="MODIFY"):
    return {
        "state": {"episode_id": episode_id, "domain": "software_engineering.demo"},
        "proposed_action": {"action_type": "quarantine"},
        "safety_decision": {"supervisor_id": supervisor, "decision": decision},
        "executed_action": executed,
        "future_outcome": {"realized": "ok"},
        "reward_components": {"total": 0.8},
        "meta": {"factory": "agentic-coding-trajectory-factory", "round": 2},
    }


def _write_corpus(directory, files):
    for name, records in files.items():
        (directory / name).write_text(
            "".join(json.dumps(record) + "\n" for record in records), encoding="utf-8"
        )


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
        with tempfile.TemporaryDirectory() as raw:
            directory = Path(raw)
            (directory / "episodes.jsonl").write_text(
                '{"goal":"g","steps":[],"meta":{"score":NaN}}\n',
                encoding="utf-8",
            )
            with self.assertRaises(payload_kind_audit.PayloadKindAuditError) as caught:
                payload_kind_audit.build_audit(directory)
        self.assertIn("non-standard JSON constant", str(caught.exception))

    def test_numeric_literals_that_overflow_to_infinity_are_rejected(self):
        with tempfile.TemporaryDirectory() as raw:
            directory = Path(raw)
            (directory / "episodes.jsonl").write_text(
                '{"id":1e400,"goal":"g","steps":[]}\n',
                encoding="utf-8",
            )
            with self.assertRaises(payload_kind_audit.PayloadKindAuditError) as caught:
                payload_kind_audit.build_audit(directory)
        self.assertIn("outside the finite float range", str(caught.exception))

    def test_duplicate_object_keys_are_rejected(self):
        with tempfile.TemporaryDirectory() as raw:
            directory = Path(raw)
            (directory / "episodes.jsonl").write_text(
                '{"goal":"g","steps":"bad","steps":[]}\n',
                encoding="utf-8",
            )
            with self.assertRaises(payload_kind_audit.PayloadKindAuditError) as caught:
                payload_kind_audit.build_audit(directory)
        self.assertIn("duplicate JSON object key", str(caught.exception))

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

    def test_expect_rejects_bool_int_type_drift(self):
        with tempfile.TemporaryDirectory() as raw:
            directory = Path(raw)
            _write_corpus(directory, {"episodes.jsonl": [_episode([])]})
            published = payload_kind_audit.build_audit(directory)
            serialized = json.dumps(published).replace('"records": 1', '"records": true', 1)
            expected = directory / "audit.json"
            expected.write_text(serialized, encoding="utf-8")
            err = io.StringIO()
            with redirect_stderr(err), redirect_stdout(io.StringIO()):
                code = payload_kind_audit.main([str(directory), "--expect", str(expected)])
        self.assertEqual(code, 1)
        self.assertIn("summary differs from the published audit", err.getvalue())

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

    def test_documented_json_flag_is_an_explicit_alias_for_the_default(self):
        with tempfile.TemporaryDirectory() as raw:
            directory = Path(raw)
            _write_corpus(directory, {"episodes.jsonl": [_episode([])]})
            default_out = io.StringIO()
            with redirect_stdout(default_out):
                self.assertEqual(payload_kind_audit.main([str(directory)]), 0)
            explicit_out = io.StringIO()
            with redirect_stdout(explicit_out):
                self.assertEqual(payload_kind_audit.main([str(directory), "--json"]), 0)
        self.assertEqual(default_out.getvalue(), explicit_out.getvalue())

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

    def test_a_record_the_lane_cannot_classify_fails_loudly_with_its_coordinate(self):
        with tempfile.TemporaryDirectory() as raw:
            directory = Path(raw)
            _write_corpus(directory, {"batch-r02.jsonl": [{"who": "knows"}]})
            with self.assertRaises(payload_kind_audit.PayloadKindAuditError) as caught:
                payload_kind_audit.build_audit(directory)
        self.assertIn("batch-r02.jsonl:1", str(caught.exception))

    def test_a_malformed_line_fails_loudly_instead_of_being_skipped(self):
        with tempfile.TemporaryDirectory() as raw:
            directory = Path(raw)
            (directory / "batch-r02.jsonl").write_text(
                json.dumps(_episode([_step(1)])) + "\nnot json\n", encoding="utf-8"
            )
            with self.assertRaises(payload_kind_audit.PayloadKindAuditError) as caught:
                payload_kind_audit.build_audit(directory)
        self.assertIn("batch-r02.jsonl:2", str(caught.exception))

    def test_a_non_object_record_is_rejected(self):
        with tempfile.TemporaryDirectory() as raw:
            directory = Path(raw)
            (directory / "batch-r02.jsonl").write_text("[1, 2, 3]\n", encoding="utf-8")
            with self.assertRaises(payload_kind_audit.PayloadKindAuditError) as caught:
                payload_kind_audit.build_audit(directory)
        self.assertIn("must be a JSON object", str(caught.exception))

    def test_a_missing_corpus_directory_is_rejected(self):
        with self.assertRaises(payload_kind_audit.PayloadKindAuditError):
            payload_kind_audit.build_audit(REPO / "docs" / "no-such-corpus")

    def test_expect_accepts_a_faithful_audit_and_names_drift(self):
        with tempfile.TemporaryDirectory() as raw:
            directory = Path(raw)
            _write_corpus(
                directory,
                {"episodes.jsonl": [_episode([_step(1, thought="t")])]},
            )
            audit = payload_kind_audit.build_audit(directory)
            faithful = directory / "audit.json"
            faithful.write_text(json.dumps(audit), encoding="utf-8")

            out = io.StringIO()
            with redirect_stdout(out):
                code = payload_kind_audit.main([str(directory), "--expect", str(faithful)])
            self.assertEqual(code, 0, out.getvalue())

            drifted = dict(audit)
            drifted["summary"] = dict(audit["summary"], records=99)
            stale = directory / "stale.json"
            stale.write_text(json.dumps(drifted), encoding="utf-8")

            err = io.StringIO()
            with redirect_stderr(err), redirect_stdout(io.StringIO()):
                code = payload_kind_audit.main([str(directory), "--expect", str(stale)])
            self.assertEqual(code, 1)
            self.assertIn("summary differs from the published audit", err.getvalue())

    def test_expect_reaudits_the_named_snapshot_not_later_appends(self):
        with tempfile.TemporaryDirectory() as raw:
            directory = Path(raw)
            _write_corpus(
                directory,
                {"episodes.jsonl": [_episode([_step(1, thought="published")])]},
            )
            published = payload_kind_audit.build_audit(directory)
            expected = directory / "audit.json"
            expected.write_text(json.dumps(published), encoding="utf-8")

            _write_corpus(
                directory,
                {"batch-r10.jsonl": [_episode([_step(1, thought="later")])]},
            )
            self.assertEqual(payload_kind_audit.build_audit(directory)["summary"]["records"], 2)
            out = io.StringIO()
            with redirect_stdout(out):
                code = payload_kind_audit.main([str(directory), "--expect", str(expected)])
            self.assertEqual(code, 0, out.getvalue())

    def test_expect_rejects_unsafe_or_duplicate_snapshot_names(self):
        with tempfile.TemporaryDirectory() as raw:
            directory = Path(raw)
            _write_corpus(directory, {"episodes.jsonl": [_episode([])]})
            base = payload_kind_audit.build_audit(directory)
            for paths in (("episodes.jsonl", "episodes.jsonl"), ("../escape.jsonl",)):
                with self.subTest(paths=paths):
                    published = dict(base)
                    published["files"] = [{"path": path} for path in paths]
                    expected = directory / "audit.json"
                    expected.write_text(json.dumps(published), encoding="utf-8")
                    err = io.StringIO()
                    with redirect_stderr(err):
                        code = payload_kind_audit.main([str(directory), "--expect", str(expected)])
                    self.assertEqual(code, 2)
                    self.assertIn("payload-kind audit failed", err.getvalue())

    def test_snapshot_name_type_errors_are_controlled(self):
        with tempfile.TemporaryDirectory() as raw:
            directory = Path(raw)
            _write_corpus(directory, {"episodes.jsonl": [_episode([])]})
            with self.assertRaises(payload_kind_audit.PayloadKindAuditError) as caught:
                payload_kind_audit.build_audit(directory, payload_names=[[]])
        self.assertIn("unsafe snapshot payload name", str(caught.exception))

    def test_expect_rejects_non_standard_json_constants_as_input_errors(self):
        with tempfile.TemporaryDirectory() as raw:
            directory = Path(raw)
            _write_corpus(directory, {"episodes.jsonl": [_episode([])]})
            published = payload_kind_audit.build_audit(directory)
            serialized = json.dumps(published).replace('"records": 1', '"records": NaN', 1)
            expected = directory / "audit.json"
            expected.write_text(serialized, encoding="utf-8")
            err = io.StringIO()
            with redirect_stderr(err):
                code = payload_kind_audit.main([str(directory), "--expect", str(expected)])
        self.assertEqual(code, 2)
        self.assertIn("non-standard JSON constant", err.getvalue())

    def test_expect_rejects_numeric_literals_that_overflow_to_infinity(self):
        with tempfile.TemporaryDirectory() as raw:
            directory = Path(raw)
            _write_corpus(directory, {"episodes.jsonl": [_episode([])]})
            published = payload_kind_audit.build_audit(directory)
            serialized = json.dumps(published).replace('"records": 1', '"records": 1e400', 1)
            expected = directory / "audit.json"
            expected.write_text(serialized, encoding="utf-8")
            err = io.StringIO()
            with redirect_stderr(err):
                code = payload_kind_audit.main([str(directory), "--expect", str(expected)])
        self.assertEqual(code, 2)
        self.assertIn("outside the finite float range", err.getvalue())


class PublishedAgenticCodingPayloadKindAudit(unittest.TestCase):
    """Pin the #74 finding from the committed evidence alone.

    These assertions need no Hub access and no gitignored raw tree: they hold
    the committed audit to its own arithmetic, and hold the write-up to the
    committed audit. If either drifts, the numbers quoted in the PR and in the
    card text stop agreeing with each other here first.
    """

    @classmethod
    def setUpClass(cls):
        cls.audit = json.loads(AUDIT_JSON.read_text(encoding="utf-8"))
        cls.doc = AUDIT_DOC.read_text(encoding="utf-8")

    def test_the_committed_audit_balances(self):
        summary = self.audit["summary"]
        self.assertEqual(summary["files"], len(self.audit["files"]))
        self.assertEqual(summary["records"], len(self.audit["records"]))
        self.assertEqual(sum(summary["kinds"].values()), summary["records"])
        self.assertEqual(sum(entry["records"] for entry in self.audit["files"]), summary["records"])
        steps = summary["coding_steps"]
        self.assertEqual(steps["native"] + steps["wrapped"], steps["total"])
        self.assertEqual(
            summary["coding_episodes_including_wrapped"],
            summary["coding_episodes_reachable_at_top_level"]
            + summary["thalamic_records_wrapping_a_coding_episode"],
        )

    def test_generated_audit_and_supplementary_evidence_are_distinct(self):
        provenance = self.audit["document_provenance"]
        generated = provenance["generated_audit"]
        supplementary = provenance["supplementary_evidence"]

        self.assertNotIn("generated_by", self.audit)
        self.assertEqual(generated["generated_by"], "pipelines/payload_kind_audit.py")
        self.assertEqual(tuple(generated["fields"]), DERIVED_KEYS)
        self.assertIn("not emitted by the audit pipeline", supplementary["description"])

        generated_fields = set(generated["fields"])
        supplementary_fields = set(supplementary["fields"])
        self.assertTrue(generated_fields.isdisjoint(supplementary_fields))
        self.assertEqual(
            generated_fields | supplementary_fields,
            set(self.audit) - {"document_provenance"},
        )

    def test_the_payload_kind_split_is_three_episodes_and_sixteen_gate_records(self):
        summary = self.audit["summary"]
        self.assertEqual(summary["records"], 19)
        self.assertEqual(summary["kinds"], {"episode": 3, "thalamic": 16})
        # The whole point of #74: a top-level coding-episode loader reaches 3.
        self.assertEqual(summary["coding_episodes_reachable_at_top_level"], 3)
        # And the sibling scan's point: every gate record does wrap one.
        self.assertEqual(summary["thalamic_records_wrapping_a_coding_episode"], 16)
        self.assertEqual(summary["coding_episodes_including_wrapped"], 19)

    def test_all_three_episodes_live_in_the_legacy_filename_and_carry_no_id(self):
        episodes = [row for row in self.audit["records"] if row["kind"] == "episode"]
        self.assertEqual(len(episodes), 3)
        self.assertEqual({row["source_file"] for row in episodes}, {"episodes.jsonl"})
        self.assertEqual([row["source_line"] for row in episodes], [1, 2, 3])
        self.assertEqual([row["id"] for row in episodes], [None, None, None])
        # A batch-only glob would drop the one file that holds every coding
        # episode: no batch shard contributes a single episode record.
        batch_files = [entry for entry in self.audit["files"] if entry["path"].startswith("batch-")]
        self.assertEqual(len(batch_files), 8)
        self.assertEqual(sum(entry["kinds"].get("episode", 0) for entry in batch_files), 0)

    def test_the_gate_record_ids_are_the_sixteen_the_issue_lists(self):
        gate_ids = tuple(row["id"] for row in self.audit["records"] if row["kind"] == "thalamic")
        self.assertEqual(gate_ids, ISSUE_74_THALAMIC_IDS)
        self.assertTrue(
            all(
                row["wraps_coding_episode"]
                for row in self.audit["records"]
                if row["kind"] == "thalamic"
            )
        )

    def test_no_published_step_carries_decision_basis(self):
        fields = self.audit["summary"]["coding_steps_by_reasoning_field"]
        total = self.audit["summary"]["coding_steps"]["total"]
        self.assertEqual(total, 361)
        self.assertEqual(fields["decision_basis"], 0)
        self.assertEqual(fields["thought"], total)
        self.assertEqual(fields["reflection"], total)
        # #74 counts only the 3 top-level episodes' 77 steps.
        self.assertEqual(self.audit["summary"]["coding_steps"]["native"], 77)

    def test_every_record_is_stamped_by_this_factory(self):
        self.assertEqual(
            self.audit["summary"]["meta_factory_stamps"],
            {"agentic-coding-trajectory-factory": self.audit["summary"]["records"]},
        )

    def test_the_viewer_projection_is_recorded_as_healthy_and_complete(self):
        viewer = self.audit["hub"]["viewer"]
        self.assertTrue(viewer["healthy"])
        self.assertTrue(viewer["lossless_against_raw"])
        self.assertEqual(viewer["rows"], self.audit["summary"]["records"])
        self.assertEqual(
            viewer["rows_by_source_file"],
            {entry["path"]: entry["records"] for entry in self.audit["files"]},
        )
        # The fix must stay card-side: no default config over data/raw/*.jsonl.
        self.assertIn("must not be replaced by", self.audit["card_disclosure"]["markdown"])

    def test_no_card_schema_declaration_was_added_for_this_dataset(self):
        # agentic-coding-trajectories is a Fable-5 dataset. The card-schema
        # mechanism belongs to the Grok 4.6 publisher, which does not manage it;
        # a declaration file here would be orphaned.
        self.assertFalse(
            (REPO / "config" / "card-schemas" / "agentic-coding-trajectories.json").exists()
        )

    def test_the_write_up_carries_the_generated_record_table_verbatim(self):
        self.assertIn(payload_kind_audit.render_markdown(self.audit), self.doc)

    def test_the_write_up_carries_the_card_disclosure_verbatim(self):
        opening = "```markdown\n"
        start = self.doc.index(opening) + len(opening)
        end = self.doc.index("\n```", start) + 1
        self.assertEqual(self.doc[start:end], self.audit["card_disclosure"]["markdown"])

    def test_the_card_corrections_name_the_stale_license_claim(self):
        corrections = self.audit["card_corrections"]
        self.assertTrue(corrections)
        for row in corrections:
            self.assertEqual({"field", "current", "replacement", "why"}, set(row))
            for value in row.values():
                self.assertIsInstance(value, str)
                self.assertTrue(value.strip())
        fields = " ".join(row["field"] for row in corrections)
        self.assertIn("release-status.json", fields)
        self.assertIn(
            "apache-2.0",
            " ".join(row["replacement"] for row in corrections).lower(),
        )

    def test_the_write_up_says_the_hub_write_is_not_done_here(self):
        self.assertIn("Nothing was uploaded to the Hugging Face Hub", self.doc)


RAW_AGENTIC_CODING = REPO / "outputs" / "raw" / "2026-08-17" / "agentic-coding-trajectory-factory"


@unittest.skipUnless(
    RAW_AGENTIC_CODING.is_dir(),
    "raw agentic-coding corpus not present in this checkout (gitignored); "
    "the published audit is re-derived only where the immutable raw tree exists",
)
class AgenticCodingRawCorpusFidelity(unittest.TestCase):
    """Re-derive the published snapshot from its append-only source, read-only."""

    def test_the_published_audit_is_a_fresh_scan_of_the_raw_corpus(self):
        before = {
            path.name: hashlib.sha256(path.read_bytes()).hexdigest()
            for path in sorted(RAW_AGENTIC_CODING.glob("*.jsonl"))
        }
        published = json.loads(AUDIT_JSON.read_text(encoding="utf-8"))
        derived = payload_kind_audit.build_audit(
            RAW_AGENTIC_CODING,
            payload_names=[entry["path"] for entry in published["files"]],
        )
        after = {
            path.name: hashlib.sha256(path.read_bytes()).hexdigest()
            for path in sorted(RAW_AGENTIC_CODING.glob("*.jsonl"))
        }
        self.assertEqual(before, after, "the audit must never write to the raw corpus")

        self.assertEqual(
            {key: derived[key] for key in DERIVED_KEYS},
            {key: published[key] for key in DERIVED_KEYS},
        )
        self.assertEqual(set(derived), set(DERIVED_KEYS))


if __name__ == "__main__":
    unittest.main()
