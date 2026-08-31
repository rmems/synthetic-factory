#!/usr/bin/env python3
"""Payload-first kind-mix quarantine and the preference publish gate.

Covers the frozen issue #30 provenance ledger, kind-mix detection over raw
payloads, the publish gate that a new leftover-mill record must block, and
the raw-corpus fidelity re-derivation. The issue #43 factory-mix census
reporting lives in ``tests/test_leftover_mill.py``.
"""

import hashlib
import json
import re
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "pipelines"))
sys.path.insert(0, str(REPO / "scripts"))

import leftover_mill  # noqa: E402
import publish_grok46_hub as publisher  # noqa: E402

QUARANTINE_DOC = REPO / "docs" / "leftover-mill-quarantine.md"
CODE_REVIEW_SLUG = "code-review-preference-factory"

PREFERENCE_ITEM = {
    "slug": CODE_REVIEW_SLUG,
    "hub": "code-review-preference-pairs",
    "pretty": "Code Review Preference Pairs",
    "blurb": "Code-review chosen/rejected/critique preference pairs.",
    "tags": ["synthetic-data", "preference-data"],
}
EPISODE_ITEM = {
    "slug": "long-horizon-coding-factory",
    "hub": "long-horizon-coding-trajectories",
    "pretty": "Long Horizon Coding Trajectories",
    "blurb": "Test factory.",
    "tags": ["synthetic-data"],
}


def episode_side(goal="repair the leftover vfs image id"):
    phases = (
        "review the patch diff",
        "find the incorrect bug risk",
        "prefer the better correction",
        "verify tests are correct and safe",
    )
    return {
        "goal": goal,
        "steps": [
            {
                "n": index,
                "decision_basis": f"Observation: {phases[index - 1]}",
                "tool_call": {"name": "bash", "args": {"command": f"echo {index}"}},
                "observation": phases[index - 1],
            }
            for index in range(1, 5)
        ],
        "outcome": "leftover object removed",
        "reward": {"success": True},
    }


def preference_record(record_id):
    chosen = episode_side()
    rejected = episode_side()
    rejected["reward"] = {"success": False}
    return {
        "id": record_id,
        "chosen": chosen,
        "rejected": rejected,
        "critique": "the rejected patch never re-reads the leftover object",
        "reward_delta": 0.4,
        "reward": {"success": True},
        "meta": {"factory": CODE_REVIEW_SLUG, "round": 1, "generator": "grok-4.6"},
    }


def episode_record(record_id):
    record = episode_side()
    record["id"] = record_id
    record["plan"] = "inspect, repair, verify"
    record["meta"] = {
        "factory": CODE_REVIEW_SLUG,
        "round": 723,
        "generator": "grok-4.6",
    }
    return record


def write_jsonl(path, records):
    path.write_text("".join(json.dumps(record) + "\n" for record in records))


def stage_legacy_baseline(source, records, *, raw_text=None):
    """Stage one payload visible through a marker-mode legacy baseline.

    Rounds at or below ``legacy_baseline`` are published on their recorded
    digest alone. That is how the 12 code-review episodes reached the Hub: they
    predate the commit-time kind check in ``pipelines/round_txn.py``, so the
    publish boundary is the only place left that can still see them.
    """
    source.mkdir(parents=True, exist_ok=True)
    batch = source / "batch-r01.jsonl"
    if raw_text is None:
        write_jsonl(batch, records)
    else:
        batch.write_text(raw_text)
    notes = source / "NOTES-r01.md"
    notes.write_text("Novel coverage: 80%\n")
    (source / ".round-marker-mode.json").write_text(
        json.dumps(
            {
                "version": 1,
                "legacy_baseline": 1,
                "commit_point": "ROUND-rNN.complete.json",
            }
        )
        + "\n"
    )
    return batch


class LedgerContract(unittest.TestCase):
    def test_ledger_names_the_twelve_published_code_review_episodes(self):
        provenance = leftover_mill.KIND_MIX_QUARANTINE[CODE_REVIEW_SLUG]
        ids = [entry.record_id for entry in provenance]
        self.assertEqual(len(provenance), 12)
        self.assertEqual(len(set(provenance)), 12)
        self.assertEqual(
            sorted({identifier.split("-")[1] for identifier in ids}),
            ["r723", "r724", "r725", "r726", "r727", "r728"],
        )
        self.assertEqual(leftover_mill.quarantined_ids(CODE_REVIEW_SLUG), set(ids))
        self.assertTrue(all(entry.record_kind == "episode" for entry in provenance))
        self.assertTrue(
            all(re.fullmatch(r"[0-9a-f]{64}", entry.source_sha256) for entry in provenance)
        )

    def test_only_the_code_review_preference_lane_has_acknowledged_records(self):
        self.assertEqual(list(leftover_mill.KIND_MIX_QUARANTINE), [CODE_REVIEW_SLUG])
        self.assertEqual(
            leftover_mill.quarantined_ids("tool-use-preference-factory"), frozenset()
        )

    def test_documentation_lists_exactly_the_ledger_records(self):
        text = QUARANTINE_DOC.read_text()
        documented = set(re.findall(r"`(dbc-r7\d\d-[a-z0-9-]+)`", text))
        self.assertEqual(
            documented, leftover_mill.quarantined_ids(CODE_REVIEW_SLUG)
        )
        self.assertIn("payload-first", text)
        for entry in leftover_mill.KIND_MIX_QUARANTINE[CODE_REVIEW_SLUG]:
            self.assertIn(entry.source_sha256, text)

    def test_destination_kind_comes_from_the_factory_registry(self):
        self.assertEqual(leftover_mill.destination_kind(CODE_REVIEW_SLUG), "preference")
        self.assertEqual(
            leftover_mill.destination_kind("long-horizon-coding-factory"), "episode"
        )
        self.assertIsNone(leftover_mill.destination_kind("not-a-factory"))
        self.assertTrue(leftover_mill.is_preference_destination(CODE_REVIEW_SLUG))
        self.assertTrue(
            leftover_mill.is_preference_destination("tool-use-preference-factory")
        )
        self.assertFalse(
            leftover_mill.is_preference_destination("long-horizon-coding-factory")
        )


class KindMixDetection(unittest.TestCase):
    def test_kind_is_read_from_the_payload_not_the_id_suffix(self):
        # A ``-leftover`` id is scenario naming: thousands of legitimate
        # episodes carry it. Only the payload decides.
        native = preference_record("dbc-r900-buildkit-cachemount-leftover")
        self.assertIsNone(leftover_mill.kind_mix_kind(native, "preference"))

        foreign = episode_record("crp-r900-review-patch-native-looking-id")
        self.assertEqual(leftover_mill.kind_mix_kind(foreign, "preference"), "episode")

    def test_unclassifiable_and_legacy_shapes_are_not_reported_as_mill_mix(self):
        self.assertIsNone(leftover_mill.kind_mix_kind({"id": "ordinary"}, "preference"))
        self.assertIsNone(leftover_mill.kind_mix_kind("not-a-record", "preference"))
        thalamic_side = {
            "state": {},
            "proposed_action": {},
            "safety_decision": {},
            "executed_action": {},
            "future_outcome": {},
            "reward_components": {},
        }
        legacy = {"id": "legacy", "chosen": thalamic_side, "rejected": thalamic_side}
        self.assertIsNone(leftover_mill.kind_mix_kind(legacy, "preference"))

    def test_destinations_without_a_declared_kind_report_nothing(self):
        foreign = episode_record("dbc-r723-buildah-layers-vfs-id-leftover")
        self.assertIsNone(leftover_mill.kind_mix_kind(foreign, None))
        self.assertEqual(
            leftover_mill.find_kind_mix(
                [(1, foreign)],
                None,
                leftover_mill.KindMixSource(
                    slug=CODE_REVIEW_SLUG, source_name="x.jsonl"
                ),
            ),
            [],
        )

    def test_record_id_falls_back_to_meta_id(self):
        self.assertEqual(leftover_mill.record_id({"id": " top "}), "top")
        self.assertEqual(leftover_mill.record_id({"meta": {"id": "nested"}}), "nested")
        self.assertIsNone(leftover_mill.record_id({"id": "  "}))
        self.assertIsNone(leftover_mill.record_id([]))

    def test_scan_marks_ledger_records_acknowledged_and_others_not(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "batch-r723.jsonl"
            known = "dbc-r723-buildah-layers-vfs-id-leftover"
            records = [
                episode_record(known),
                preference_record("crp-r723-ok"),
                episode_record("crp-r723-brand-new-mill-leak"),
            ]
            raw_lines = [json.dumps(record) + "\n" for record in records]
            path.write_text("".join(raw_lines))
            provenance = leftover_mill.KindMixProvenance(
                source_name=path.name,
                source_line=1,
                record_id=known,
                record_kind="episode",
                source_sha256=hashlib.sha256(raw_lines[0].encode()).hexdigest(),
            )
            with mock.patch.dict(
                leftover_mill.KIND_MIX_QUARANTINE,
                {CODE_REVIEW_SLUG: (provenance,)},
                clear=True,
            ):
                findings = leftover_mill.scan_jsonl_kind_mix(
                    path, "preference", slug=CODE_REVIEW_SLUG
                )
            self.assertEqual([f.source_line for f in findings], [1, 3])
            self.assertEqual([f.acknowledged for f in findings], [True, False])
            self.assertEqual(
                [f.record_id for f in leftover_mill.unacknowledged(findings)],
                ["crp-r723-brand-new-mill-leak"],
            )
            self.assertIn("is 'episode'", findings[0].describe())

    def test_acknowledgement_requires_exact_source_line_kind_and_bytes(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "batch-r723.jsonl"
            record = episode_record("dbc-r723-buildah-layers-vfs-id-leftover")
            raw_line = json.dumps(record) + "\n"
            path.write_text(raw_line)
            exact = leftover_mill.KindMixProvenance(
                source_name=path.name,
                source_line=1,
                record_id=record["id"],
                record_kind="episode",
                source_sha256=hashlib.sha256(raw_line.encode()).hexdigest(),
            )

            def acknowledged(*, source_name=path.name):
                return leftover_mill.scan_jsonl_kind_mix(
                    path,
                    "preference",
                    slug=CODE_REVIEW_SLUG,
                    source_name=source_name,
                )[0].acknowledged

            with mock.patch.dict(
                leftover_mill.KIND_MIX_QUARANTINE,
                {CODE_REVIEW_SLUG: (exact,)},
                clear=True,
            ):
                self.assertTrue(acknowledged())
                self.assertFalse(acknowledged(source_name="batch-r724.jsonl"))

                path.write_text("\n" + raw_line)
                self.assertFalse(acknowledged())

                changed = dict(record)
                changed["outcome"] = "same id, different bytes"
                path.write_text(json.dumps(changed) + "\n")
                self.assertFalse(acknowledged())

                wrong_kind = leftover_mill.KindMixProvenance(
                    source_name=exact.source_name,
                    source_line=exact.source_line,
                    record_id=exact.record_id,
                    record_kind="multi_agent",
                    source_sha256=exact.source_sha256,
                )
                path.write_text(raw_line)
                with mock.patch.dict(
                    leftover_mill.KIND_MIX_QUARANTINE,
                    {CODE_REVIEW_SLUG: (wrong_kind,)},
                    clear=True,
                ):
                    self.assertFalse(acknowledged())

    def test_undecodable_lines_are_reported_and_never_acknowledged(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "batch-r01.jsonl"
            path.write_bytes(
                json.dumps(preference_record("crp-r01-ok")).encode("utf-8")
                + b"\n\n"
                + b"{not json}\n"
                + b'{"id":"\xff\xfe"}\n'
            )
            findings = leftover_mill.scan_jsonl_kind_mix(
                path, "preference", slug=CODE_REVIEW_SLUG
            )
            self.assertEqual([f.record_kind for f in findings], ["unparseable"] * 2)
            self.assertEqual([f.source_line for f in findings], [3, 4])
            self.assertEqual(leftover_mill.unacknowledged(findings), findings)

    def test_scan_is_inert_for_destinations_without_a_declared_kind(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "batch-r01.jsonl"
            path.write_text("{not json}\n")
            self.assertEqual(
                leftover_mill.scan_jsonl_kind_mix(path, None, slug="not-a-factory"), []
            )


class PreferencePublishGate(unittest.TestCase):
    def _snapshot(self, root, item, records, *, raw_text=None):
        source = root / "raw" / item["slug"]
        stage_legacy_baseline(source, records, raw_text=raw_text)
        with mock.patch.object(
            publisher, "FACTORY_ROOT", root / "raw"
        ), mock.patch.object(
            publisher, "HF_ROOT", root / "hf"
        ):
            return publisher.snapshot_one(item)

    def _card(self, root, item):
        return (
            root / "hf" / publisher.HF_DATASETS_DIRNAME / item["hub"] / "README.md"
        ).read_text()

    def test_new_leftover_mill_blocks_a_preference_snapshot(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            with self.assertRaises(SystemExit) as caught:
                self._snapshot(
                    root,
                    PREFERENCE_ITEM,
                    [
                        preference_record("crp-r01-a"),
                        episode_record("crp-r01-fresh-mill-leak"),
                    ],
                )
            message = str(caught.exception)
            self.assertIn("unquarantined leftover-mill", message)
            self.assertIn("crp-r01-fresh-mill-leak", message)
            self.assertIn("batch-r01.jsonl:2", message)
            self.assertFalse(
                (
                    root
                    / "hf"
                    / publisher.HF_DATASETS_DIRNAME
                    / PREFERENCE_ITEM["hub"]
                ).exists()
            )

    def test_a_blocked_snapshot_leaves_the_mirror_untouched(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            mirror_raw = (
                root
                / "hf"
                / publisher.HF_DATASETS_DIRNAME
                / PREFERENCE_ITEM["hub"]
                / "data"
                / "raw"
            )
            mirror_raw.mkdir(parents=True)
            previous = mirror_raw / "batch-r01.jsonl"
            write_jsonl(previous, [preference_record("crp-r01-previously-published")])
            previous_bytes = previous.read_bytes()

            with self.assertRaises(SystemExit):
                self._snapshot(
                    root,
                    PREFERENCE_ITEM,
                    [
                        preference_record("crp-r01-a"),
                        episode_record("crp-r01-fresh-mill-leak"),
                    ],
                )

            # The gate runs before any copy or reconcile, so the already
            # published mirror is neither overwritten nor pruned.
            self.assertEqual(previous.read_bytes(), previous_bytes)
            self.assertFalse(
                (
                    root
                    / "hf"
                    / publisher.HF_DATASETS_DIRNAME
                    / PREFERENCE_ITEM["hub"]
                    / "README.md"
                ).exists()
            )

    def test_undecodable_payload_blocks_a_preference_snapshot(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            with self.assertRaisesRegex(SystemExit, "unquarantined leftover-mill"):
                self._snapshot(
                    root,
                    PREFERENCE_ITEM,
                    [preference_record("crp-r01-a")],
                    raw_text=json.dumps(preference_record("crp-r01-a"))
                    + "\n{ truncated\n",
                )

    def test_ledger_records_publish_with_a_disclosed_corrected_count(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            known = "dbc-r723-buildah-layers-vfs-id-leftover"
            records = [
                preference_record("crp-r01-a"),
                preference_record("crp-r01-b"),
                episode_record(known),
            ]
            known_line = json.dumps(records[2]) + "\n"
            provenance = leftover_mill.KindMixProvenance(
                source_name="batch-r01.jsonl",
                source_line=3,
                record_id=known,
                record_kind="episode",
                source_sha256=hashlib.sha256(known_line.encode()).hexdigest(),
            )
            with mock.patch.dict(
                leftover_mill.KIND_MIX_QUARANTINE,
                {CODE_REVIEW_SLUG: (provenance,)},
                clear=True,
            ):
                stats = self._snapshot(root, PREFERENCE_ITEM, records)
                self.assertEqual(stats["records"], 3)
                self.assertEqual(stats["quarantined"], 1)

                card = self._card(root, PREFERENCE_ITEM)
                self.assertIn("## Leftover-mill quarantine", card)
                self.assertIn(f"`{known}`", card)
                self.assertIn(provenance.source_sha256, card)
                self.assertIn("Quarantined: 1 of the 3 published raw records", card)
                self.assertIn("**2**, not 3", card)
                self.assertIn("raw JSONL is published unmodified", card)

                # Raw evidence is mirrored byte-for-byte; nothing is rewritten.
                raw = (
                    root
                    / "hf"
                    / publisher.HF_DATASETS_DIRNAME
                    / PREFERENCE_ITEM["hub"]
                    / "data"
                    / "raw"
                    / "batch-r01.jsonl"
                )
                source = root / "raw" / PREFERENCE_ITEM["slug"] / "batch-r01.jsonl"
                self.assertEqual(raw.read_bytes(), source.read_bytes())

                dest = (
                    root
                    / "hf"
                    / publisher.HF_DATASETS_DIRNAME
                    / PREFERENCE_ITEM["hub"]
                )
                with mock.patch.object(
                    publisher, "FACTORY_ROOT", root / "raw"
                ), mock.patch.object(
                    publisher, "HF_ROOT", root / "hf"
                ):
                    publisher.validate_upload_snapshot(PREFERENCE_ITEM, dest)

    def test_marker_snapshot_pins_bytes_before_deriving_exemptions(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            source = root / "raw" / PREFERENCE_ITEM["slug"]
            known = episode_record("dbc-r723-buildah-layers-vfs-id-leftover")
            native_a = preference_record("crp-r01-native-a")
            native_b = preference_record("crp-r01-native-b")
            batch = stage_legacy_baseline(source, [known, native_a, native_b])
            known_line = json.dumps(known) + "\n"
            provenance = leftover_mill.KindMixProvenance(
                source_name=batch.name,
                source_line=1,
                record_id=known["id"],
                record_kind="episode",
                source_sha256=hashlib.sha256(known_line.encode()).hexdigest(),
            )
            real_legacy_kind_mix = publisher.legacy_kind_mix

            def replace_after_scan(src, baseline):
                findings = real_legacy_kind_mix(src, baseline)
                replacement = preference_record("crp-r01-replaced-after-scan")
                replacement["chosen"]["steps"][0]["thought"] = "private scratch"
                write_jsonl(batch, [replacement, native_a, native_b])
                return findings

            with mock.patch.dict(
                leftover_mill.KIND_MIX_QUARANTINE,
                {CODE_REVIEW_SLUG: (provenance,)},
                clear=True,
            ), mock.patch.object(
                publisher, "FACTORY_ROOT", root / "raw"
            ), mock.patch.object(
                publisher, "HF_ROOT", root / "hf"
            ), mock.patch.object(
                publisher, "legacy_kind_mix", side_effect=replace_after_scan
            ):
                with self.assertRaisesRegex(
                    SystemExit, "legacy baseline changed during validation"
                ):
                    publisher.snapshot_one(PREFERENCE_ITEM)

            copied = (
                root
                / "hf"
                / publisher.HF_DATASETS_DIRNAME
                / PREFERENCE_ITEM["hub"]
                / "data"
                / "raw"
                / batch.name
            )
            self.assertFalse(copied.exists())

    def test_clean_preference_snapshot_has_no_quarantine_section(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            stats = self._snapshot(
                root,
                PREFERENCE_ITEM,
                [
                    preference_record("crp-r01-a"),
                    preference_record("crp-r01-b"),
                    preference_record("crp-r01-c"),
                ],
            )
            self.assertEqual(stats["quarantined"], 0)
            self.assertNotIn("Leftover-mill quarantine", self._card(root, PREFERENCE_ITEM))

    def test_non_preference_destinations_are_left_alone(self):
        # Factory mix and dest-stamped family mix on episode slugs belong to
        # separate detectors; this gate must not reach into them.
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            source = root / "batch-r01.jsonl"
            write_jsonl(
                source, [preference_record("crp-r01-foreign")]
            )
            self.assertEqual(
                publisher.gate_leftover_mill(
                    EPISODE_ITEM, [(source, source.name)]
                ),
                [],
            )


RAW_CODE_REVIEW = (
    REPO
    / "outputs"
    / "raw"
    / "2026-08-19-agentic"
    / "code-review-preference-factory"
)


@unittest.skipUnless(
    RAW_CODE_REVIEW.is_dir(),
    "raw code-review corpus not present in this checkout (gitignored); "
    "fidelity is re-derived only where immutable raw evidence exists",
)
class KindMixRawCorpusFidelity(unittest.TestCase):
    def test_frozen_provenance_matches_exact_raw_lines(self):
        expected = leftover_mill.quarantine_provenance(CODE_REVIEW_SLUG)
        findings = []
        for source_name in sorted({entry.source_name for entry in expected}):
            findings.extend(
                leftover_mill.scan_jsonl_kind_mix(
                    RAW_CODE_REVIEW / source_name,
                    "preference",
                    slug=CODE_REVIEW_SLUG,
                )
            )
        actual = {
            leftover_mill.KindMixProvenance(
                source_name=finding.source_name,
                source_line=finding.source_line,
                record_id=finding.record_id,
                record_kind=finding.record_kind,
                source_sha256=finding.source_sha256,
            )
            for finding in findings
            if finding.record_id is not None
            and finding.source_sha256 is not None
        }
        self.assertEqual(actual, expected)
        self.assertTrue(all(finding.acknowledged for finding in findings))


if __name__ == "__main__":
    unittest.main()
