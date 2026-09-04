#!/usr/bin/env python3
"""Issue #55 leaf tests for the per-dataset card schema declaration."""

import unittest

from card_schema_test_support import (
    EPISODE_JSON_COLUMNS,
    FEATURES_YAML,
    META_JSON_YAML,
    NOT_DECLARED,
    PLAN_PRESENT_ROW,
    REFLECTION_OPTIONAL_ROW,
    REWARD_JSON_YAML,
    VIEWER_SCHEMA_HEADING,
    DeclarationTestCase,
    publisher,
)


def _is_numeric_note(value):
    """True for a `note` string that pins at least one digit-bearing count."""
    return isinstance(value, str) and any(character.isdigit() for character in value)


def _numeric_notes(value):
    """Yield every digit-bearing `note` string nested anywhere under ``value``."""
    if isinstance(value, dict):
        if _is_numeric_note(value.get("note")):
            yield value["note"]
        children = [item for key, item in value.items() if key != "note"]
    elif isinstance(value, list):
        children = value
    else:
        return
    for child in children:
        yield from _numeric_notes(child)


class PaymentIdempotencyDeclarationTests(DeclarationTestCase):
    """Issue #55: dest-stamped `sir-*` leftover mill plus thin `meta` vs designed.

    Every count asserted here was derived by scanning all 347 published shards
    of the local mirror, not transcribed from the issue body.
    """

    DATASET = "payment-idempotency-trajectories"
    ISSUE = 55
    HUB_ITEM = {
        "slug": "payment-idempotency-factory",
        "hub": DATASET,
        "pretty": "Payment Idempotency Trajectories",
        "blurb": "Payment leftover-idempotency-key episodes.",
        "tags": ["synthetic-data", "trajectories"],
    }
    SUMMARY = publisher.PayloadSummary(
        records=694,
        bytes_=4778432,
        first="r01",
        last="r347",
        names=["batch-r01.jsonl", "batch-r311.jsonl", "batch-r347.jsonl"],
    )

    def test_declaration_matches_the_observed_union_schema(self):
        # Unlike the long-horizon dump, `plan` is on all 694 records here.
        self.assert_episode_union("280 of 11385 steps")

    def test_key_bag_columns_are_declared_json(self):
        self.assert_json_columns(EPISODE_JSON_COLUMNS)

    def test_card_front_matter_declares_the_default_config_over_raw_batches(self):
        self.assert_front_matter_declares_default_config(
            FEATURES_YAML, META_JSON_YAML, REWARD_JSON_YAML
        )

    def test_card_discloses_the_six_dest_stamped_sir_leftovers(self):
        disclosure = self.declaration["disclosures"][0]
        self.assertEqual(
            disclosure["ids"],
            [
                "sir-r311-vespa-doc-leftover3c-rebuild",
                "sir-r311-vespa-drop-document-leftover3c-handoff",
                "sir-r312-es-reindex-leftover3c-rebuild",
                "sir-r312-es-drop-reindex-leftover3c-handoff",
                "sir-r313-whoosh-writer-leftover3c-rebuild",
                "sir-r313-whoosh-drop-leftover3c-handoff",
            ],
        )
        # Owned by the census (#43) and the dest-stamp detector (#44), not re-filed.
        self.assertEqual(disclosure["issues"], [43, 44])
        self.assert_card_names_records(disclosure["ids"])
        self.assertIn("dest-stamped", self.card)

    def test_card_body_carries_the_optional_and_key_bag_notes(self):
        self.assert_card_has(
            VIEWER_SCHEMA_HEADING,
            REFLECTION_OPTIONAL_ROW,
            PLAN_PRESENT_ROW,
            # The two early `pid-` records the issue body never mentions.
            "`pid-r01-idem-key-not-bound-to-body`",
            "`pid-r01-webhook-replay-double-credit`",
        )
        self.assertNotIn(NOT_DECLARED, self.card)

    def test_fixed_counts_are_scoped_to_the_audited_snapshot(self):
        scope = "audited 694-record snapshot through round 347"
        self.assertIn(scope, self.declaration["note"])
        self.assertIn(scope, self.card)

        for note in _numeric_notes(self.declaration["features"]):
            with self.subTest(note=note):
                self.assertIn(scope, note)

        for disclosure in self.declaration["disclosures"]:
            summary = disclosure["summary"] if isinstance(disclosure, dict) else disclosure
            with self.subTest(disclosure=summary):
                self.assertIn(scope, summary)


if __name__ == "__main__":
    unittest.main()
