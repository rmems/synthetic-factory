#!/usr/bin/env python3
"""Issue #405: a card states its NOTES coverage and carries no Hub tip framing.

``observability-debug-trajectories`` on Hub main publishes raw batches for
rounds ``r01`` through ``r1435`` but NOTES files for only 974 of them; ``r38``
through ``r498`` have none. The generated card said only "Supporting notes are
under ``data/metadata/NOTES-*.md``", which implies every round is annotated.
The snapshot path itself refuses an agentic round without notes, so these tests
pin both halves: the card counts the published coverage, and a source missing
notes is refused rather than published with a hole or filled with invented notes.
"""

import hashlib
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))
sys.path.insert(0, str(REPO / "tests"))

import publish_grok46_hub as publisher  # noqa: E402

from test_publish_grok46_hub import (  # noqa: E402
    ITEM,
    write_valid_completed_long_horizon,
    write_valid_legacy,
)

card_notes = publisher.card_notes

OBSERVABILITY_HUB = "observability-debug-trajectories"
OBSERVABILITY_ITEM = {
    "slug": "observability-debug-factory",
    "hub": OBSERVABILITY_HUB,
    "pretty": "Observability Debug Trajectories",
    "blurb": "Observability leftover-lie (wrong dashboard / dropped label) episodes.",
    "tags": ["synthetic-data", "trajectories", "observability", "tracing"],
}
# The published Hub main payload measured for issue #405.
PUBLISHED_ROUNDS = range(1, 1436)
NOTED_ROUNDS = [n for n in PUBLISHED_ROUNDS if not 38 <= n <= 498]
OBSERVABILITY_SUMMARY = publisher.PayloadSummary(
    records=2869,
    bytes_=17170432,
    first="r01",
    last="r1435",
    names=[f"batch-r{n:02d}.jsonl" for n in PUBLISHED_ROUNDS],
)
# Point-in-time Hub state that belongs in a Hub discussion, never in a card a
# script regenerates: PR tips, old SHAs, datasets-server size and reindex state.
HUB_STATE_PHRASES = (
    "this PR tip",
    "until this tip merges",
    "b450ab",
    "/size",
    "reindex",
    "config-size",
    "pending",
)


def published_paths(names):
    return [Path(name) for name in names]


class NotesCoverageTests(unittest.TestCase):
    def test_missing_rounds_collapse_into_contiguous_spans(self):
        self.assertEqual(card_notes.missing_spans([5, 3, 4, 9, 1]), ((1, 1), (3, 5), (9, 9)))
        self.assertEqual(card_notes.missing_spans([]), ())

    def test_issue_405_hole_is_reported_as_one_span(self):
        coverage = card_notes.notes_coverage(PUBLISHED_ROUNDS, NOTED_ROUNDS)

        self.assertEqual(coverage, card_notes.NotesCoverage(1435, 974, ((38, 498),)))
        sentence = card_notes.render_notes_sentence(coverage)
        self.assertIn("for 974 of the 1435 published rounds", sentence)
        self.assertIn("The other 461 have no published NOTES file", sentence)
        self.assertIn("`r38`–`r498` (461 rounds)", sentence)
        self.assertIn("no NOTES file is written after the fact", sentence)

    def test_notes_for_unpublished_rounds_are_not_claimed(self):
        coverage = card_notes.notes_coverage([1, 2], [1, 2, 3])

        self.assertEqual(coverage, card_notes.NotesCoverage(2, 2, ()))

    def test_full_and_empty_coverage_render_their_own_sentences(self):
        full = card_notes.render_notes_sentence(card_notes.notes_coverage([1, 2], [1, 2]))
        none = card_notes.render_notes_sentence(card_notes.notes_coverage([1, 2], []))

        self.assertIn("every one of the 2 published rounds has one", full)
        self.assertEqual(
            none,
            "No supporting `data/metadata/NOTES-*.md` file is published for any of "
            "the 2 published rounds.",
        )

    def test_without_coverage_the_legacy_sentence_is_kept(self):
        self.assertEqual(
            card_notes.render_notes_sentence(None), card_notes.LEGACY_NOTES_SENTENCE
        )
        self.assertEqual(
            card_notes.render_notes_sentence(card_notes.notes_coverage([], [])),
            card_notes.LEGACY_NOTES_SENTENCE,
        )

    def test_a_scattered_hole_names_every_missing_round(self):
        # Twenty isolated gaps: every one is named, none is folded into a count.
        rounds = range(1, 41)
        noted = [n for n in rounds if n % 2]
        sentence = card_notes.render_notes_sentence(card_notes.notes_coverage(rounds, noted))

        self.assertIn("The other 20 have no published NOTES file: `r02`, `r04`", sentence)
        for number in range(2, 41, 2):
            self.assertIn(f"`r{number:02d}`", sentence)
        self.assertIn("`r38`, `r40`. Their raw batches", sentence)
        self.assertNotIn("more span", sentence)


class PublisherCoverageTests(unittest.TestCase):
    def test_rounds_come_from_batch_and_note_names(self):
        coverage = publisher.published_notes_coverage(
            published_paths(["batch-r01.jsonl", "batch-r02b.jsonl", "batch-r04.jsonl"]),
            published_paths(["NOTES-r02b.md", "NOTES-r04.md", "unrelated.md"]),
        )

        self.assertEqual(coverage, card_notes.NotesCoverage(3, 2, ((1, 1),)))

    def test_a_legacy_r1_payload_counts_as_round_one(self):
        legacy = min(publisher.LEGACY_R1_NAMES)
        coverage = publisher.published_notes_coverage(
            published_paths([legacy, "batch-r02.jsonl"]), published_paths(["NOTES-r01.md"])
        )

        self.assertEqual(coverage, card_notes.NotesCoverage(2, 1, ((2, 2),)))


def render_observability_card(**keywords):
    return publisher.render_card(
        OBSERVABILITY_ITEM, summary=OBSERVABILITY_SUMMARY, **keywords
    )


class ObservabilityCardTests(unittest.TestCase):
    def test_card_discloses_the_r38_r498_notes_hole(self):
        coverage = card_notes.notes_coverage(PUBLISHED_ROUNDS, NOTED_ROUNDS)
        card = render_observability_card(notes=coverage)

        self.assertIn(
            "Supporting notes are under\n`data/metadata/NOTES-*.md` for 974 of the 1435 "
            "published rounds.",
            card,
        )
        self.assertIn("`r38`–`r498` (461 rounds)", card)

    def test_card_without_coverage_is_byte_identical_to_the_legacy_card(self):
        legacy = render_observability_card()

        self.assertIn(
            "`outputs/raw/2026-08-19-agentic/observability-debug-factory/`. "
            "Supporting notes are under\n`data/metadata/NOTES-*.md`. The factory source",
            legacy,
        )
        self.assertEqual(legacy, render_observability_card(notes=None))

    def test_notes_keyword_refuses_anything_but_coverage(self):
        with self.assertRaisesRegex(TypeError, "notes= takes a card_notes.NotesCoverage"):
            render_observability_card(notes=["NOTES-r01.md"])

    def test_card_carries_no_hub_tip_or_reindex_framing(self):
        coverage = card_notes.notes_coverage(PUBLISHED_ROUNDS, NOTED_ROUNDS)
        card = render_observability_card(notes=coverage)

        for phrase in HUB_STATE_PHRASES:
            with self.subTest(phrase=phrase):
                self.assertNotIn(phrase, card)

    def test_declaration_counts_describe_the_published_payload(self):
        path = REPO / "config" / "card-schemas" / f"{OBSERVABILITY_HUB}.json"
        declaration = json.loads(path.read_text(encoding="utf-8"))
        card = render_observability_card()

        self.assertIn(405, declaration["issues"])
        self.assertIn("present on all 2869 records", card)
        self.assertIn("12964 of 43054 steps", card)
        self.assertIn("1 of 2869 in the published `r01`-`r1435` payload", card)
        # 1749 survives only where the note says which audit it replaces.
        self.assertEqual(card.count("1749"), 1)
        self.assertIn("replace the earlier 1749-record `r01`-`r875` audit", card)
        self.assertNotIn("875 shards", card)


def commit_round_without_notes(source, number):
    """Commit a marker-mode round whose manifest carries no NOTES file."""
    batch = source / f"batch-r{number:02d}.jsonl"
    write_valid_completed_long_horizon(batch, number)
    marker = f"ROUND-r{number:02d}.complete.json"
    (source / marker).write_text(
        json.dumps(
            {
                "version": 1,
                "factory": ITEM["slug"],
                "round": number,
                "records": 2,
                "expected_records": 2,
                "commit_point": marker,
                "files": [
                    {"name": batch.name, "sha256": hashlib.sha256(batch.read_bytes()).hexdigest()}
                ],
            }
        )
        + "\n"
    )


class SnapshotNotesTests(unittest.TestCase):
    """The snapshot publishes the factory's own notes or refuses; it never fills a hole."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.source = self.root / "raw" / ITEM["slug"]
        self.source.mkdir(parents=True)
        self.destination_root = self.root / "hf"
        self.dest = self.destination_root / publisher.HF_DATASETS_DIRNAME / ITEM["hub"]
        for number in range(1, 5):
            write_valid_legacy(self.source / f"batch-r{number:02d}.jsonl")

    def publisher_roots(self):
        return mock.patch.multiple(
            publisher, FACTORY_ROOT=self.root / "raw", HF_ROOT=self.destination_root
        )

    def test_snapshot_card_states_full_notes_coverage_and_preflight_pins_it(self):
        with self.publisher_roots():
            stats = publisher.snapshot_one(ITEM)
            publisher.validate_upload_snapshot(ITEM, self.dest)
        readme = self.dest / "README.md"
        card = readme.read_text()

        full = card_notes.render_notes_sentence(card_notes.notes_coverage(range(1, 5), range(1, 5)))

        self.assertEqual((stats["batches"], stats["notes"]), (4, 4))
        self.assertIn("every one of the 4 published rounds has one", full)
        self.assertIn(full, card)
        readme.write_text(card.replace(full, card_notes.LEGACY_NOTES_SENTENCE))
        with self.publisher_roots(), self.assertRaisesRegex(SystemExit, "README.md"):
            publisher.validate_upload_snapshot(ITEM, self.dest)

    def test_snapshot_refuses_a_baseline_round_without_notes(self):
        (self.source / "NOTES-r02.md").unlink()

        with self.publisher_roots(), self.assertRaisesRegex(
            SystemExit, "legacy baseline notes missing or unsafe for r02"
        ):
            publisher.snapshot_one(ITEM)
        self.assertFalse(self.dest.exists())

    def test_snapshot_refuses_a_committed_round_without_notes(self):
        (self.source / ".round-marker-mode.json").write_text(
            '{"version":1,"legacy_baseline":4,"commit_point":"ROUND-rNN.complete.json"}\n'
        )
        commit_round_without_notes(self.source, 5)

        with self.publisher_roots(), self.assertRaisesRegex(
            SystemExit, "completion marker has no unique notes entry"
        ):
            publisher.snapshot_one(ITEM)
        self.assertFalse(self.dest.exists())


if __name__ == "__main__":
    unittest.main()
