#!/usr/bin/env python3
"""Per-line and per-record robustness of compose: malformed input never aborts.

Split from test_compose_curated.py (CodeScene: Low Cohesion): resource
limits, identity-lane totality over decoded JSON, coding-step repair
deferral, and calibration lookup each get their own seam here.
"""

import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

TESTS = Path(__file__).resolve().parent
REPO = TESTS.parent
for _path in (TESTS, REPO / "pipelines"):
    if str(_path) not in sys.path:
        sys.path.insert(0, str(_path))

import compose_curated  # noqa: E402
import curate_coding  # noqa: E402
from compose_curated_test_support import (  # noqa: E402
    episode,
    thalamic,
)


class ComposeSourceLineResourceLimits(unittest.TestCase):
    """One malformed line must be excluded, never abort the whole composition."""

    def compose(self, physical_line):
        return compose_curated.compose_source_line(
            physical_line,
            source_path="tool-use-preference-factory/batch-r01.jsonl",
            source_line=1,
            source_file_sha256="7" * 64,
        )

    def test_deeply_nested_line_is_excluded_instead_of_raising(self):
        # ``json.loads`` recurses over the document, so a deep enough line
        # exhausts the stack.  ``RecursionError`` is not a ``ValueError``:
        # unguarded it escaped ``compose_source_line`` and rolled the whole
        # destination back over a single bad line.
        depth = 200_000
        decision = self.compose(b"[" * depth + b"]" * depth)

        self.assertEqual(decision.action, compose_curated.ACTION_EXCLUDED)
        self.assertEqual(
            decision.reason_codes, (compose_curated.REASON_INVALID_JSON,)
        )
        self.assertIsNone(decision.record)
        stage = decision.stages[0]
        self.assertEqual(stage["lane"], "source")
        self.assertEqual(stage["action"], compose_curated.ACTION_EXCLUDED)
        self.assertIn("error", stage["detail"])

    def test_canonical_hash_recursion_is_excluded_per_line(self):
        # A line shallow enough for ``json.loads`` can still be too deep for
        # the canonical hash, which recurses separately.  The hashing call
        # therefore has to sit inside the same guarded block as the decode.
        payload = json.dumps({"kind": "coding_episode", "steps": []}).encode("utf-8")

        with mock.patch.object(
            compose_curated, "_canonical_sha256", side_effect=RecursionError
        ):
            decision = self.compose(payload)

        self.assertEqual(decision.action, compose_curated.ACTION_EXCLUDED)
        self.assertEqual(
            decision.reason_codes, (compose_curated.REASON_INVALID_JSON,)
        )
        self.assertIsNone(decision.record)

    def test_curation_depth_recursion_is_excluded_per_line(self):
        # Codex #97 P2: a depth that survives the guarded decode and canonical
        # hash can still exhaust the stack inside a lane (``copy.deepcopy``
        # spends several frames per level), so the curation and deduplication
        # path needs the same per-line guard.
        record = episode()
        deep = None
        for _ in range(500):
            deep = [deep]
        record["extra"] = deep
        payload = json.dumps(record).encode("utf-8")

        decision = compose_curated.compose_source_line(
            payload,
            source_path="agentic-coding-trajectory-factory/batch-r01.jsonl",
            source_line=1,
            source_file_sha256="7" * 64,
        )

        self.assertEqual(decision.action, compose_curated.ACTION_EXCLUDED)
        self.assertEqual(
            decision.reason_codes, (compose_curated.REASON_INVALID_JSON,)
        )
        self.assertIsNone(decision.record)
        self.assertIn(
            "recursion depth exhausted", decision.stages[0]["detail"]["error"]
        )

    def test_duplicate_object_keys_are_excluded_per_line(self):
        # Codex #97 P2: plain ``json.loads`` keeps the last duplicate key
        # silently, creating parser-dependent source semantics that the
        # identity lane's own reader already refuses. The composed reader must
        # refuse the same shape instead of exporting an ambiguous record.
        payload = (
            json.dumps(episode())
            .replace(
                '"goal": "fix the failing test"',
                '"goal": "another goal", "goal": "fix the failing test"',
            )
            .encode("utf-8")
        )
        self.assertIn(b'"goal": "another goal", "goal"', payload)

        decision = self.compose(payload)

        self.assertEqual(decision.action, compose_curated.ACTION_EXCLUDED)
        self.assertEqual(
            decision.reason_codes, (compose_curated.REASON_INVALID_JSON,)
        )
        self.assertIn(
            "duplicate JSON object key", decision.stages[0]["detail"]["error"]
        )

    def test_a_fatal_line_does_not_roll_back_the_whole_run(self):
        # The unguarded ``RecursionError`` escaped ``compose_run``, which
        # discards the destination on any error, so one deep line destroyed
        # the composition of every other record in the run.
        depth = 200_000
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            source = root / "run" / "thalamic-trajectory-factory"
            source.mkdir(parents=True)
            (source / "batch-r01.jsonl").write_text(
                json.dumps(thalamic("keep"))
                + "\n"
                + "[" * depth
                + "]" * depth
                + "\n",
                encoding="utf-8",
            )

            summary = compose_curated.compose_run(root / "run", root / "curated")

            self.assertTrue((root / "curated").exists())
            self.assertEqual(summary["counts"]["source_records"], 2)
            self.assertEqual(summary["counts"]["retained"], 1)
            self.assertEqual(summary["counts"]["excluded"], 1)
            self.assertEqual(
                summary["exclusions"],
                {compose_curated.REASON_INVALID_JSON: 1},
            )


class IdentityLaneTotality(unittest.TestCase):
    """Codex #97 P2: malformed field types become identity exclusions.

    A structurally invalid but valid-JSON value (a list where an enum string
    belongs) used to raise ``TypeError`` out of ``check_thalamic``'s
    set-membership test, rolling back the whole destination over one line.
    """

    def test_unhashable_safety_decision_is_excluded_not_a_crash(self):
        record = thalamic("unhashable-decision")
        record["safety_decision"] = {"decision": [], "rationale": "bounded"}

        decision = compose_curated.compose_record(
            record,
            source_path="thalamic-trajectory-factory/batch-r01.jsonl",
            source_line=1,
            source_sha256="4" * 64,
        )

        self.assertEqual(decision.action, compose_curated.ACTION_EXCLUDED)
        self.assertIsNone(decision.record)

    def test_unhashable_provenance_kind_is_excluded_not_a_crash(self):
        record = thalamic("unhashable-kind")
        record["provenance"] = {"kind": [], "claimed": "designed"}

        decision = compose_curated.compose_record(
            record,
            source_path="thalamic-trajectory-factory/batch-r01.jsonl",
            source_line=1,
            source_sha256="5" * 64,
        )

        self.assertEqual(decision.action, compose_curated.ACTION_EXCLUDED)
        self.assertIsNone(decision.record)


class CodingStepRepairDeferral(unittest.TestCase):
    """Codex #97 P2: coding-owned step errors defer to the coding lane.

    ``curate_coding.curate_episode`` is designed to exclude only an unusable
    step and retain the episode with ``coding_steps_excluded``. Identity
    applies the same step-shape invariant first, so its refusal must defer to
    the lane that knows how to repair, exactly like the bridge-order path.
    """

    def compose(self, record, line=1):
        return compose_curated.compose_record(
            record,
            source_path="agentic-coding-trajectory-factory/batch-r01.jsonl",
            source_line=line,
            source_sha256="6" * 64,
        )

    def test_a_repairable_invalid_step_is_dropped_not_the_whole_record(self):
        record = episode()
        record["steps"] = record["steps"] + [None]

        decision = self.compose(record)

        self.assertEqual(decision.action, compose_curated.ACTION_RETAINED)
        self.assertIn(
            curate_coding.REASON_STEPS_EXCLUDED, decision.reason_codes
        )
        self.assertEqual(len(decision.record["steps"]), 1)
        identity_stage = next(
            stage for stage in decision.stages if stage["lane"] == "identity"
        )
        self.assertTrue(
            identity_stage["detail"]["coding_steps_deferred_to_coding_lane"]
        )
        coding_stage = next(
            stage for stage in decision.stages if stage["lane"] == "coding"
        )
        self.assertIn(
            curate_coding.REASON_STEPS_EXCLUDED, coding_stage["reason_codes"]
        )

    def test_an_episode_with_no_usable_step_stays_excluded(self):
        record = episode()
        record["steps"] = [None, 17]

        decision = self.compose(record)

        self.assertEqual(decision.action, compose_curated.ACTION_EXCLUDED)
        self.assertEqual(
            decision.reason_codes, ("identity.invalid_payload_shape",)
        )

    def test_a_non_step_shape_error_is_not_deferred(self):
        record = episode()
        record["steps"] = record["steps"] + [None]
        record.pop("goal")

        decision = self.compose(record)

        self.assertEqual(decision.action, compose_curated.ACTION_EXCLUDED)


class CalibrationLookup(unittest.TestCase):
    """Rewards are calibrated by the record's *source* identifier."""

    CATALOG = {"ffpc-r5-002": {"canonical_factor": 0.5}}

    def test_an_absent_catalog_never_calibrates(self):
        for catalog in (None, {}):
            with self.subTest(catalog=catalog):
                self.assertIsNone(
                    compose_curated.calibration_for({"id": "ffpc-r5-002"}, catalog)
                )

    def test_a_top_level_id_is_matched_case_insensitively(self):
        self.assertEqual(
            compose_curated.calibration_for({"id": "FFPC-R5-002"}, self.CATALOG),
            self.CATALOG["ffpc-r5-002"],
        )

    def test_a_meta_id_is_used_when_the_top_level_id_is_gone(self):
        # Compose runs the identity lane first, which replaces ``id`` with a
        # canonical digest, so the pre-identity id has to be reachable.
        self.assertEqual(
            compose_curated.calibration_for(
                {"id": None, "meta": {"id": "ffpc-r5-002"}}, self.CATALOG
            ),
            self.CATALOG["ffpc-r5-002"],
        )

    def test_an_unusable_identifier_yields_no_calibration(self):
        for record in (
            {"id": 17},
            {"meta": "not a mapping"},
            {"meta": {"id": 17}},
            {},
            "not a record",
        ):
            with self.subTest(record=record):
                self.assertIsNone(
                    compose_curated.calibration_for(record, self.CATALOG)
                )

    def test_an_unlisted_record_is_not_calibrated(self):
        self.assertIsNone(
            compose_curated.calibration_for({"id": "ffpc-r5-999"}, self.CATALOG)
        )

    def test_every_identity_accepted_legacy_id_form_can_calibrate(self):
        """Codex #97 P1: pair_id-only records must not silently downgrade.

        Identity accepts every ``LEGACY_ID_KEYS`` form on the record root and
        its meta/state containers; a calibrated FFPC pair that declares its
        catalogued id only as ``pair_id`` must calibrate exactly like its
        ``id``-carrying twin.
        """
        for record in (
            {"pair_id": "ffpc-r5-002"},
            {"record_id": "FFPC-R5-002"},
            {"meta": {"pair_id": "ffpc-r5-002"}},
            {"state": {"episode_id": "ffpc-r5-002"}},
        ):
            with self.subTest(record=record):
                self.assertEqual(
                    compose_curated.calibration_for(record, self.CATALOG),
                    self.CATALOG["ffpc-r5-002"],
                )

    def test_the_first_catalogued_identifier_wins_deterministically(self):
        catalog = {
            "ffpc-r5-002": {"canonical_factor": 0.5},
            "ffpc-r5-003": {"canonical_factor": 0.7},
        }
        record = {"id": "ffpc-r5-002", "pair_id": "ffpc-r5-003"}
        self.assertEqual(
            compose_curated.calibration_for(record, catalog),
            catalog["ffpc-r5-002"],
        )


class DefaultCalibrationEvidence(unittest.TestCase):
    """Codex #97 P2: a malformed canonical calibration path fails composition.

    ``default.is_file()`` is false for a directory, broken symlink, or fifo,
    so compose used to record mode "none" and build a tree the export step
    must then refuse (it checks ``lexists``); fail at compose time instead.
    """

    def test_duplicate_keys_in_calibration_evidence_refuse_composition(self):
        """Codex #97 P2: repeated calibration fields are ambiguous, not last-wins."""
        from compose_curated_test_support import thalamic as support_thalamic
        from compose_curated_test_support import write_jsonl

        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            source = root / "run"
            write_jsonl(
                source / "thalamic-trajectory-factory" / "batch-r01.jsonl",
                [support_thalamic("clean-1")],
            )
            default = source / compose_curated.FFPC_UNITS_MIGRATION
            default.parent.mkdir(parents=True)
            default.write_text(
                '{"records":[{"scope":"ffpc-r5-002",'
                '"usd_conversion_factor":0.1,"usd_conversion_factor":2.0}]}\n',
                encoding="utf-8",
            )

            with self.assertRaisesRegex(
                compose_curated.ComposeError, "duplicate JSON object key"
            ):
                compose_curated.compose_run(source, root / "curated")
            self.assertFalse((root / "curated").exists())

    def test_non_regular_default_calibration_evidence_refuses_composition(self):
        from compose_curated_test_support import thalamic as support_thalamic
        from compose_curated_test_support import write_jsonl

        for member in ("directory", "broken_symlink"):
            with self.subTest(member=member), tempfile.TemporaryDirectory() as td:
                root = Path(td)
                source = root / "run"
                write_jsonl(
                    source / "thalamic-trajectory-factory" / "batch-r01.jsonl",
                    [support_thalamic("clean-1")],
                )
                default = source / compose_curated.FFPC_UNITS_MIGRATION
                default.parent.mkdir(parents=True)
                if member == "directory":
                    default.mkdir()
                else:
                    default.symlink_to(root / "missing-target.json")

                # The directory hits the new default-calibration guard; a
                # symlink is already refused by the alias-hardened scanner.
                with self.assertRaisesRegex(
                    compose_curated.ComposeError,
                    "not an exact regular file|symlink alias",
                ):
                    compose_curated.compose_run(source, root / "curated")
                self.assertFalse((root / "curated").exists())


if __name__ == "__main__":
    unittest.main()
