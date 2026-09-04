#!/usr/bin/env python3
"""Issue #50 leaf tests for the per-dataset card schema declaration."""

import unittest

from card_schema_test_support import (
    DISCLOSURES_HEADING,
    EPISODE_FIELDS,
    EPISODE_JSON_COLUMNS,
    FEATURES_YAML,
    META_JSON_YAML,
    NOT_DECLARED,
    PLAN_STRING_YAML,
    REFLECTION_OPTIONAL_ROW,
    REWARD_JSON_YAML,
    VIEWER_SCHEMA_HEADING,
    DeclarationTestCase,
    publisher,
)

SSL_CERT_ROTATION = "ssl-cert-rotation-trajectories"


class SslCertRotationDeclarationTests(DeclarationTestCase):
    """Issue #50: thin `meta` vs designed/domain/stack plus reward extras.

    Every count asserted here was derived by reading the published mirror at
    `~/rmems/hf/grok-4.6/ssl-cert-rotation-trajectories/data/raw` (365 shards,
    730 records, 12043 steps, 0 parse failures), not copied from the issue.
    """

    DATASET = SSL_CERT_ROTATION
    ISSUE = 50
    # The Hub item and published-payload facts the card must render, derived
    # from the mirror at ~/rmems/hf/grok-4.6/ssl-cert-rotation-trajectories.
    HUB_ITEM = {
        "slug": "ssl-cert-rotation-factory",
        "hub": SSL_CERT_ROTATION,
        "pretty": "Ssl Cert Rotation Trajectories",
        "blurb": "TLS leftover-cert-object rotation episodes.",
        "tags": ["synthetic-data", "tls", "certificates"],
    }
    SUMMARY = publisher.PayloadSummary(
        records=730,
        bytes_=4632576,
        first="r01",
        last="r365",
        names=["batch-r01.jsonl", "batch-r180.jsonl"],
    )

    def test_declaration_matches_the_observed_union_schema(self):
        names = self.names()
        self.assertEqual(set(names), EPISODE_FIELDS)
        # Unlike long-horizon-coding, `plan` is on all 730 records here.
        self.assertNotIn("optional", names["plan"])
        self.assertEqual(names["plan"]["dtype"], "string")
        self.assertEqual(names["meta"]["dtype"], "json")
        self.assertEqual(names["reward"]["dtype"], "json")
        self.assert_episode_steps(names, "5889 of 12043")
        self.assertEqual(self.declaration["issues"], [50])

    def test_key_bag_columns_are_declared_json(self):
        self.assert_json_columns(EPISODE_JSON_COLUMNS)

    def test_card_front_matter_declares_the_default_config_over_raw_batches(self):
        self.assert_front_matter_declares_default_config(
            FEATURES_YAML,
            META_JSON_YAML,
            REWARD_JSON_YAML,
            PLAN_STRING_YAML,
            # The card-only annotations must never reach the feature YAML.
            absent=("optional",),
        )

    def test_card_body_discloses_thin_meta_lane_and_leftover_mill_records(self):
        self.assertIn(VIEWER_SCHEMA_HEADING, self.card)
        self.assertNotIn(NOT_DECLARED, self.card)
        self.assertIn(REFLECTION_OPTIONAL_ROW, self.card)
        self.assert_card_names_records(
            (
                "ssl-r01-nginx-reload-old-inode",
                "ssl-r06-nginx-must-staple-on-e7f2",
                "scr-r2-nginx-ocsp-p6",
                "scr-r4-istio-sds-p16",
                "sir-r180-xapian-flint-leftover3d-rebuild",
                "sir-r181-vespa-drop-document-leftover3d-handoff",
            )
        )
        self.assert_card_has(
            DISCLOSURES_HEADING,
            "issues/44",
            "Every one of the 730 records is stamped",
            "Every step publishes a public `decision_basis`",
        )

    def test_every_declared_disclosure_id_names_a_thin_meta_or_odd_record(self):
        disclosed = {
            record_id
            for disclosure in self.declaration["disclosures"]
            for record_id in disclosure["ids"]
        }
        self.assertEqual(len(disclosed), 16)
        self.assertEqual(
            {record_id.split("-")[0] for record_id in disclosed}, {"ssl", "scr", "sir"}
        )


if __name__ == "__main__":
    unittest.main()
