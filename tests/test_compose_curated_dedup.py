#!/usr/bin/env python3
"""Semantic deduplication before identity and after the lossy curation lanes."""

import copy
import json
import sys
import tempfile
import unittest
from pathlib import Path

TESTS = Path(__file__).resolve().parent
REPO = TESTS.parent
for _path in (TESTS, REPO / "pipelines"):
    if str(_path) not in sys.path:
        sys.path.insert(0, str(_path))

import compose_curated  # noqa: E402
from compose_curated_test_support import (  # noqa: E402
    bridge_pair,
    episode,
    read_jsonl,
    thalamic,
    trajectory_preference_pair,
    write_jsonl,
)


class ComposeSemanticDeduplication(unittest.TestCase):
    """Split from test_compose_curated.py: source- and curated-level dedup."""

    def test_semantic_source_duplicates_are_excluded_before_identity(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            source = root / "run" / "thalamic-trajectory-factory"
            source.mkdir(parents=True)
            record = thalamic("semantic-duplicate")
            first = json.dumps(record, ensure_ascii=False)
            duplicate = json.dumps(
                record,
                ensure_ascii=False,
                sort_keys=True,
                separators=(",", ":"),
            )
            (source / "batch-r01.jsonl").write_text(
                first + "\n" + duplicate + "\n", encoding="utf-8"
            )

            summary = compose_curated.compose_run(root / "run", root / "curated")
            manifest = read_jsonl(root / "curated" / summary["manifest"]["path"])

            self.assertEqual(summary["counts"]["source_records"], 2)
            self.assertEqual(summary["counts"]["retained"], 1)
            self.assertEqual(summary["counts"]["excluded"], 1)
            self.assertEqual(
                summary["exclusions"],
                {compose_curated.REASON_DUPLICATE_SOURCE_RECORD: 1},
            )
            self.assertEqual(
                manifest[1]["reason_codes"],
                [compose_curated.REASON_DUPLICATE_SOURCE_RECORD],
            )
            duplicate_stage = manifest[1]["stages"][0]
            self.assertEqual(duplicate_stage["lane"], "source")
            self.assertEqual(
                duplicate_stage["detail"]["first_source_path"],
                "thalamic-trajectory-factory/batch-r01.jsonl",
            )
            self.assertEqual(duplicate_stage["detail"]["first_source_line"], 1)
            output = read_jsonl(root / "curated" / manifest[0]["output_path"])
            self.assertEqual(len(output), 1)

    def test_excluded_coordinate_does_not_claim_the_source_duplicate_key(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            source = root / "run"
            record = thalamic("eligible-copy")
            write_jsonl(source / "aaa-unregistered" / "batch-r01.jsonl", [record])
            write_jsonl(
                source / "thalamic-trajectory-factory" / "batch-r01.jsonl",
                [record],
            )

            summary = compose_curated.compose_run(source, root / "curated")
            manifest = read_jsonl(root / "curated" / summary["manifest"]["path"])

            self.assertEqual(summary["counts"]["source_records"], 2)
            self.assertEqual(summary["counts"]["retained"], 1)
            self.assertEqual(summary["counts"]["excluded"], 1)
            self.assertNotIn(
                compose_curated.REASON_DUPLICATE_SOURCE_RECORD,
                manifest[1]["reason_codes"],
            )
            self.assertEqual(manifest[1]["action"], compose_curated.ACTION_RETAINED)

    def test_records_that_converge_after_coding_are_excluded_before_export(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            source = root / "run" / "agentic-coding-trajectory-factory"
            source.mkdir(parents=True)
            first = episode("converged")
            second = copy.deepcopy(first)
            second["steps"][0]["thought"] = "different hidden text"
            write_jsonl(source / "batch-r01.jsonl", [first, second])

            summary = compose_curated.compose_run(root / "run", root / "curated")
            manifest = read_jsonl(root / "curated" / summary["manifest"]["path"])

            self.assertEqual(summary["counts"]["source_records"], 2)
            self.assertEqual(summary["counts"]["retained"], 1)
            self.assertEqual(summary["counts"]["excluded"], 1)
            self.assertEqual(
                summary["exclusions"],
                {compose_curated.REASON_DUPLICATE_CURATED_RECORD: 1},
            )
            duplicate = manifest[1]
            self.assertEqual(
                duplicate["reason_codes"],
                [compose_curated.REASON_DUPLICATE_CURATED_RECORD],
            )
            dedup_stage = duplicate["stages"][-1]
            self.assertEqual(dedup_stage["lane"], "post_transform_dedup")
            self.assertEqual(
                dedup_stage["first_source_path"],
                "agentic-coding-trajectory-factory/batch-r01.jsonl",
            )
            self.assertEqual(dedup_stage["first_source_line"], 1)

    def test_preserved_legacy_ids_do_not_hide_post_curation_duplicates(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            source = root / "run" / "agentic-coding-trajectory-factory"
            source.mkdir(parents=True)
            first = episode("same")
            first["meta"]["id"] = "legacy-a"
            second = copy.deepcopy(first)
            second["id"] = "legacy-episode-other"
            second["meta"]["id"] = "legacy-b"
            write_jsonl(source / "batch-r01.jsonl", [first, second])

            summary = compose_curated.compose_run(root / "run", root / "curated")
            manifest = read_jsonl(root / "curated" / summary["manifest"]["path"])

            self.assertEqual(summary["counts"]["source_records"], 2)
            self.assertEqual(summary["counts"]["retained"], 1)
            self.assertEqual(summary["counts"]["excluded"], 1)
            self.assertEqual(
                summary["exclusions"],
                {compose_curated.REASON_DUPLICATE_CURATED_RECORD: 1},
            )
            duplicate = manifest[1]
            self.assertEqual(
                duplicate["reason_codes"],
                [compose_curated.REASON_DUPLICATE_CURATED_RECORD],
            )
            output = read_jsonl(root / "curated" / manifest[0]["output_path"])
            self.assertEqual(len(output), 1)
            self.assertNotEqual(output[0]["meta"]["id"], output[0]["id"])

    def test_cross_factory_episode_duplicates_are_deduplicated_by_content_not_provenance(self):
        """Codex #97 P1: the semantic-dedup digest must ignore factory/generator labels.

        The registry authorizes dozens of distinct path_id factories that all
        produce the generic "episode" record kind. The same episode content
        resubmitted under a second authorized episode factory differs only
        in meta.factory and its legacy id -- exactly the identity-binding
        fields this digest already strips for same-factory duplicates.
        Leaving meta.factory in the hash would keep both rows and, on a
        two-row corpus, the deterministic train/eval split would then put
        one copy in train and the other in eval: near-duplicate training
        content leaking across the holdout.
        """
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            source = root / "run"
            first = episode("cross-factory")
            first["meta"]["id"] = "legacy-a"
            second = copy.deepcopy(first)
            second["id"] = "legacy-episode-other"
            second["meta"]["id"] = "legacy-b"
            second["meta"]["factory"] = "agent-memory-compaction-factory"
            write_jsonl(
                source / "agentic-coding-trajectory-factory" / "batch-r01.jsonl",
                [first],
            )
            write_jsonl(
                source / "agent-memory-compaction-factory" / "batch-r01.jsonl",
                [second],
            )

            summary = compose_curated.compose_run(source, root / "curated")
            manifest = read_jsonl(root / "curated" / summary["manifest"]["path"])

            self.assertEqual(summary["counts"]["source_records"], 2)
            self.assertEqual(summary["counts"]["retained"], 1)
            self.assertEqual(summary["counts"]["excluded"], 1)
            self.assertEqual(
                summary["exclusions"],
                {compose_curated.REASON_DUPLICATE_CURATED_RECORD: 1},
            )
            duplicate = next(
                entry
                for entry in manifest
                if entry["reason_codes"]
                == [compose_curated.REASON_DUPLICATE_CURATED_RECORD]
            )
            dedup_stage = duplicate["stages"][-1]
            self.assertEqual(dedup_stage["lane"], "post_transform_dedup")
            retained = next(
                entry for entry in manifest if entry is not duplicate
            )
            output = read_jsonl(root / "curated" / retained["output_path"])
            self.assertEqual(len(output), 1)
            # The surviving row still names its own real factory -- only the
            # dedup digest, not the emitted record, ignores provenance.
            self.assertIn(
                output[0]["meta"]["factory"],
                {"agentic-coding-trajectory-factory", "agent-memory-compaction-factory"},
            )

    def test_side_stamped_preference_duplicates_are_deduplicated(self):
        """Codex #97 P1: side-level factory labels must not survive the digest.

        A Fable preference wrapper predates a wrapper-level ``meta.factory``
        and attests its factory on ``chosen``/``rejected`` instead --
        ``curate_identity._payload_factory`` accepts exactly that shape. If the
        semantic digest normalizes only ``semantic["meta"]``, the same pair
        submitted under two authorized preference factories survives twice,
        and on a two-record corpus the deterministic split necessarily puts
        one copy in train and its twin in eval.
        """

        def side_stamped(factory, tag):
            record = trajectory_preference_pair()
            record["id"] = f"legacy-pref-{tag}"
            record["meta"] = {"round": 1}
            for side in ("chosen", "rejected"):
                record[side]["meta"] = {"factory": factory}
            return record

        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            source = root / "run"
            write_jsonl(
                source / "tool-use-preference-factory" / "batch-r01.jsonl",
                [side_stamped("tool-use-preference-factory", "a")],
            )
            write_jsonl(
                source / "code-review-preference-factory" / "batch-r01.jsonl",
                [side_stamped("code-review-preference-factory", "b")],
            )

            summary = compose_curated.compose_run(source, root / "curated")

            self.assertEqual(summary["counts"]["source_records"], 2)
            self.assertEqual(summary["counts"]["retained"], 1)
            self.assertEqual(
                summary["exclusions"],
                {compose_curated.REASON_DUPLICATE_CURATED_RECORD: 1},
            )

    def test_run_and_round_provenance_duplicates_are_deduplicated(self):
        """Codex #97 P1: run/round provenance must not survive the digest.

        ``meta.run``/``meta.round`` name when a row was produced, exactly as
        ``meta.factory``/``meta.generator`` name who produced it. Two rows
        that are otherwise identical after curation must converge, or on a
        two-record corpus the deterministic split necessarily places one
        substantive copy in train and its twin in eval.
        """
        first = episode("provenance-twin")
        second = episode("provenance-twin")
        second["meta"]["round"] = 7
        second["meta"]["run"] = "2026-08-18"
        second["meta"]["factory"] = "agent-memory-compaction-factory"

        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            source = root / "run"
            write_jsonl(
                source / "agentic-coding-trajectory-factory" / "batch-r01.jsonl",
                [first],
            )
            write_jsonl(
                source / "agent-memory-compaction-factory" / "batch-r01.jsonl",
                [second],
            )

            summary = compose_curated.compose_run(source, root / "curated")

            self.assertEqual(summary["counts"]["source_records"], 2)
            self.assertEqual(summary["counts"]["retained"], 1)
            self.assertEqual(
                summary["exclusions"],
                {compose_curated.REASON_DUPLICATE_CURATED_RECORD: 1},
            )

    def test_bridge_trajectory_provenance_duplicates_are_deduplicated(self):
        """Codex #97 P1: bridge trajectory provenance must not survive the digest.

        Identity treats ``language_view.trajectory`` as the owner of a bridge
        record, so the semantic digest has to normalize provenance on that
        owner exactly as it does for the wrapper and both preference sides.
        Two bridge records whose nested trajectory differs only in
        ``meta.run``/``meta.round`` are the same training content; keeping
        both would place the duplicate on opposite sides of a two-record
        train/eval split.
        """
        first = bridge_pair()
        second = copy.deepcopy(first)
        second["id"] = "legacy-bridge-2"
        second["language_view"]["trajectory"]["meta"]["round"] = 7
        second["language_view"]["trajectory"]["meta"]["run"] = "2026-08-18"

        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            source = root / "run"
            write_jsonl(
                source / "neuromorphic-event-language-bridge" / "batch-r01.jsonl",
                [first, second],
            )

            summary = compose_curated.compose_run(source, root / "curated")

            self.assertEqual(summary["counts"]["source_records"], 2)
            self.assertEqual(summary["counts"]["retained"], 1)
            self.assertEqual(
                summary["exclusions"],
                {compose_curated.REASON_DUPLICATE_CURATED_RECORD: 1},
            )

    def test_calibration_evidence_coordinates_do_not_split_duplicates(self):
        """Codex #97 P1: calibration evidence coordinates must not survive the digest.

        ``magnitude.values[*].calibration_source`` embeds the calibration
        document path and entry index. Two otherwise identical records whose
        distinct catalog entries declare the same conversion factor differ
        only in that evidence coordinate, so keeping it in the digest retains
        both substantive copies — and a two-record factory then necessarily
        splits them across train and eval. The emitted record keeps its
        ``calibration_source``; only the dedup digest ignores it.
        """

        def calibrated(tag):
            record = thalamic(f"cal-{tag}")
            record["id"] = f"ffpc-r5-00{tag}"
            record["state"]["domain"] = "compose-cal"
            return record

        migration = {
            "records": [
                {
                    "scope": "batch-r01.jsonl / ffpc-r5-001 (grid)",
                    "usd_conversion_factor": 0.2,
                },
                {
                    "scope": "batch-r01.jsonl / ffpc-r5-002 (grid)",
                    "usd_conversion_factor": 0.2,
                },
            ]
        }
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            source = root / "run"
            write_jsonl(
                source / "thalamic-trajectory-factory" / "batch-r01.jsonl",
                [calibrated(1), calibrated(2)],
            )
            migration_path = root / "units-migration.json"
            migration_path.write_text(
                json.dumps(migration) + "\n", encoding="utf-8"
            )

            summary = compose_curated.compose_run(
                source, root / "curated", units_migration=migration_path
            )

            self.assertEqual(summary["counts"]["source_records"], 2)
            self.assertEqual(summary["counts"]["retained"], 1)
            self.assertEqual(
                summary["exclusions"],
                {compose_curated.REASON_DUPLICATE_CURATED_RECORD: 1},
            )
            records_dir = root / "curated" / compose_curated.RECORDS_DIRNAME
            (emitted,) = [
                record
                for path in sorted(records_dir.rglob("*.jsonl"))
                for record in read_jsonl(path)
            ]
            values = emitted["reward_training"]["magnitude"]["values"]
            self.assertTrue(
                all("calibration_source" in value for value in values), values
            )


if __name__ == "__main__":
    unittest.main()
