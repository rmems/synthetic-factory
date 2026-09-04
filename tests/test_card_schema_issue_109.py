#!/usr/bin/env python3
"""Issue #50 leaf tests for the per-dataset card schema declaration."""

import test_card_schema as _shared

unittest = _shared.unittest
io = _shared.io
json = _shared.json
tempfile = _shared.tempfile
redirect_stderr = _shared.redirect_stderr
redirect_stdout = _shared.redirect_stdout
Path = _shared.Path
mock = _shared.mock
REPO = _shared.REPO
card_schema = _shared.card_schema
publisher = _shared.publisher
LONG_HORIZON = _shared.LONG_HORIZON
MINIMAL = _shared.MINIMAL
write_declaration = _shared.write_declaration


SSL_CERT_ROTATION = "ssl-cert-rotation-trajectories"

# The Hub item and published-payload facts the card must render, derived from
# the mirror at ~/rmems/hf/grok-4.6/ssl-cert-rotation-trajectories/data/raw.
SSL_ITEM = {
    "slug": "ssl-cert-rotation-factory",
    "hub": SSL_CERT_ROTATION,
    "pretty": "Ssl Cert Rotation Trajectories",
    "blurb": "TLS leftover-cert-object rotation episodes.",
    "tags": ["synthetic-data", "tls", "certificates"],
}
SSL_SUMMARY = dict(
    records=730,
    bytes_=4632576,
    first="r01",
    last="r365",
    names=["batch-r01.jsonl", "batch-r180.jsonl"],
)


class SslCertRotationDeclarationTests(unittest.TestCase):
    """Issue #50: thin `meta` vs designed/domain/stack plus reward extras.

    Every count asserted here was derived by reading the published mirror at
    `~/rmems/hf/grok-4.6/ssl-cert-rotation-trajectories/data/raw` (365 shards,
    730 records, 12043 steps, 0 parse failures), not copied from the issue.
    """

    def setUp(self):
        self.declaration = card_schema.load(SSL_CERT_ROTATION)
        self.assertIsNotNone(self.declaration, "config/card-schemas is missing #50")
        self.item = dict(SSL_ITEM)
        self.card = publisher.render_card(
            self.item, summary=publisher.PayloadSummary(**SSL_SUMMARY)
        )

    def test_declaration_matches_the_observed_union_schema(self):
        names = {feature["name"]: feature for feature in self.declaration["features"]}
        self.assertEqual(
            set(names),
            {"id", "goal", "plan", "steps", "outcome", "reward", "meta"},
        )
        # Unlike long-horizon-coding, `plan` is on all 730 records here.
        self.assertNotIn("optional", names["plan"])
        self.assertEqual(names["plan"]["dtype"], "string")
        self.assertEqual(names["meta"]["dtype"], "json")
        self.assertEqual(names["reward"]["dtype"], "json")
        steps = {feature["name"]: feature for feature in names["steps"]["list"]}
        self.assertEqual(
            set(steps), {"n", "decision_basis", "tool_call", "observation", "reflection"}
        )
        self.assertTrue(steps["reflection"]["optional"])
        self.assertIn("5889 of 12043", steps["reflection"]["note"])
        tool_call = {feature["name"]: feature for feature in steps["tool_call"]["struct"]}
        self.assertEqual(tool_call["args"]["dtype"], "json")
        self.assertEqual(self.declaration["issues"], [50])

    def test_key_bag_columns_are_declared_json(self):
        self.assertEqual(
            card_schema.json_columns(self.declaration["features"]),
            ["steps[].tool_call.args", "reward", "meta"],
        )

    def test_card_front_matter_declares_the_default_config_over_raw_batches(self):
        front_matter = self.card.split("---", 2)[1]
        self.assertIn("configs:\n- config_name: default\n", front_matter)
        self.assertIn('    path: "data/raw/batch-*.jsonl"\n', front_matter)
        self.assertIn("dataset_info:\n  features:\n", front_matter)
        self.assertIn("  - name: meta\n    dtype: json\n", front_matter)
        self.assertIn("  - name: reward\n    dtype: json\n", front_matter)
        self.assertIn("  - name: plan\n    dtype: string\n", front_matter)
        # The card-only annotations must never reach the feature YAML.
        self.assertNotIn("optional", front_matter)
        # license/tags/status claims stay exactly where they were.
        self.assertIn("license: apache-2.0", front_matter)
        self.assertIn("**not training-ready**", self.card)

    def test_card_body_discloses_thin_meta_lane_and_leftover_mill_records(self):
        self.assertIn("## Dataset viewer schema", self.card)
        self.assertNotIn("**Not declared yet.**", self.card)
        self.assertIn("| `steps[].reflection` | optional |", self.card)
        for record_id in (
            "ssl-r01-nginx-reload-old-inode",
            "ssl-r06-nginx-must-staple-on-e7f2",
            "scr-r2-nginx-ocsp-p6",
            "scr-r4-istio-sds-p16",
            "sir-r180-xapian-flint-leftover3d-rebuild",
            "sir-r181-vespa-drop-document-leftover3d-handoff",
        ):
            with self.subTest(record_id=record_id):
                self.assertIn(f"`{record_id}`", self.card)
        self.assertIn("### Known payload disclosures", self.card)
        self.assertIn("issues/44", self.card)
        self.assertIn("Every one of the 730 records is stamped", self.card)
        self.assertIn("Every step publishes a public `decision_basis`", self.card)

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
