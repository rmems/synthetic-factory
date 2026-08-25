#!/usr/bin/env python3
"""Issue #65 leaf tests for the per-dataset card schema declaration."""

from collections import Counter

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


GIT_OPS = "git-ops-recovery-trajectories"
GIT_OPS_MIRROR = (
    Path.home()
    / "rmems"
    / "hf"
    / "grok-4.6"
    / GIT_OPS
    / "data"
    / "raw"
)


class GitOpsRecoveryDeclarationTests(unittest.TestCase):
    """Issue #65: thin `meta` versus the designed/plant leftover union schema."""

    # The published dump is 1416 shards of exactly two records each, with no
    # gaps: batch-r01.jsonl through batch-r1416.jsonl.
    PAYLOAD_NAMES = [f"batch-r{n:02d}.jsonl" for n in range(1, 1417)]

    SIR_IDS = [
        "sir-r1194-es-reindex-leftover3d-rebuild",
        "sir-r1194-es-drop-reindex-leftover3d-handoff",
        "sir-r1195-whoosh-writer-leftover3d-rebuild",
        "sir-r1195-whoosh-drop-leftover3d-handoff",
    ]

    def setUp(self):
        self.declaration = card_schema.load(GIT_OPS)
        self.assertIsNotNone(self.declaration, "config/card-schemas is missing #65")
        self.item = {
            "slug": "git-ops-recovery-factory",
            "hub": GIT_OPS,
            "pretty": "Git Ops Recovery Trajectories",
            "blurb": "Git-ops leftover-state recovery (rebase/LFS/filter-repo).",
            "tags": ["synthetic-data", "trajectories", "git", "recovery"],
        }
        self.card = publisher.render_card(
            self.item,
            records=2832,
            bytes_=16825174,
            first="r01",
            last="r1416",
            payload_names=self.PAYLOAD_NAMES,
        )

    def test_declaration_matches_the_observed_union_schema(self):
        names = {feature["name"]: feature for feature in self.declaration["features"]}
        self.assertEqual(
            set(names),
            {"id", "goal", "plan", "steps", "outcome", "reward", "meta"},
        )
        # `plan` is a string on 2756 of 2832 records and absent on 76 -- optional
        # here, unlike most sibling dumps where it is mandatory.
        self.assertTrue(names["plan"]["optional"])
        self.assertEqual(names["plan"]["dtype"], "string")
        self.assertEqual(names["meta"]["dtype"], "json")
        self.assertEqual(names["reward"]["dtype"], "json")
        steps = {feature["name"]: feature for feature in names["steps"]["list"]}
        self.assertEqual(
            set(steps), {"n", "decision_basis", "tool_call", "observation", "reflection"}
        )
        self.assertTrue(steps["reflection"]["optional"])
        self.assertNotIn("optional", steps["decision_basis"])
        tool_call = {feature["name"]: feature for feature in steps["tool_call"]["struct"]}
        self.assertEqual(tool_call["args"]["dtype"], "json")
        self.assertEqual(self.declaration["issues"], [65])
        self.assertIn(
            "25 further multi-record int counters", names["reward"]["note"]
        )
        self.assertIn("24 single-record int extras", names["reward"]["note"])
        self.assertIn(
            "`kind` and `plant` co-occur on 266 records", names["meta"]["note"]
        )
        self.assertIn(
            "four `sir-*` records carry `kind` with no `plant`",
            names["meta"]["note"],
        )

    def test_key_bag_columns_are_declared_json(self):
        self.assertEqual(
            card_schema.json_columns(self.declaration["features"]),
            ["steps[].tool_call.args", "reward", "meta"],
        )

    @unittest.skipUnless(
        GIT_OPS_MIRROR.is_dir(),
        "read-only published mirror is not available",
    )
    def test_published_mirror_reconciles_reward_and_meta_censuses(self):
        """Recheck the corrected card claims when the mirror is present."""
        payloads = sorted(GIT_OPS_MIRROR.glob("batch-*.jsonl"))
        self.assertEqual(len(payloads), 1416)
        reward_counts = Counter()
        meta_counts = Counter()
        records = 0
        for payload in payloads:
            with payload.open(encoding="utf-8") as handle:
                for line in handle:
                    if not line.strip():
                        continue
                    record = json.loads(line)
                    reward_counts.update(record["reward"].keys())
                    keys = record["meta"].keys()
                    meta_counts["kind"] += "kind" in keys
                    meta_counts["plant"] += "plant" in keys
                    meta_counts["kind_and_plant"] += "kind" in keys and "plant" in keys
                    meta_counts["kind_without_plant"] += (
                        "kind" in keys and "plant" not in keys
                    )
                    records += 1

        self.assertEqual(records, 2832)
        self.assertEqual(len(reward_counts), 58)
        self.assertEqual(sum(count == 1 for count in reward_counts.values()), 24)
        self.assertEqual(sum(count > 1 for count in reward_counts.values()), 34)
        six_named = {
            "success",
            "tests_passed",
            "cost_steps",
            "pr",
            "blocked",
            "handoff",
        }
        float_triple = {
            "process_quality",
            "verify_rigor",
            "recovery_completeness",
        }
        further_multi = {
            key
            for key, count in reward_counts.items()
            if count > 1 and key not in six_named | float_triple
        }
        self.assertEqual(len(further_multi), 25)
        self.assertEqual(
            meta_counts,
            Counter(
                kind=270,
                plant=266,
                kind_and_plant=266,
                kind_without_plant=4,
            ),
        )

    def test_declared_glob_covers_every_published_shard(self):
        self.assertEqual(self.declaration["data_files"], ["data/raw/batch-*.jsonl"])
        self.assertEqual(
            card_schema.payload_coverage_errors(self.declaration, self.PAYLOAD_NAMES),
            [],
        )

    def test_card_front_matter_declares_the_default_config_over_raw_batches(self):
        front_matter = self.card.split("---", 2)[1]
        self.assertIn("configs:\n- config_name: default\n", front_matter)
        self.assertIn('    path: "data/raw/batch-*.jsonl"\n', front_matter)
        self.assertIn("dataset_info:\n  features:\n", front_matter)
        self.assertIn("  - name: meta\n    dtype: json\n", front_matter)
        self.assertIn("  - name: reward\n    dtype: json\n", front_matter)
        # license/tags/status claims stay exactly where they were.
        self.assertIn("license: apache-2.0", front_matter)
        self.assertIn("**not training-ready**", self.card)

    def test_card_body_discloses_the_four_dest_stamped_leftover3d_rows(self):
        self.assertIn("## Dataset viewer schema", self.card)
        self.assertNotIn("**Not declared yet.**", self.card)
        for record_id in self.SIR_IDS:
            self.assertIn(f"`{record_id}`", self.card)
        self.assertIn("| `plan` | optional |", self.card)
        self.assertIn("| `steps[].reflection` | optional |", self.card)

    def test_card_keeps_ownership_of_the_leftover3d_rows_with_this_issue(self):
        # Neither frozen mill census covers this dump: #43 keys off a foreign
        # `meta.factory` (these rows are dest-stamped) and #44 excludes
        # leftover-in-id rows (these four are leftover-in-id). The card must not
        # hand the rows to either census.
        disclosure = self.declaration["disclosures"][0]
        self.assertEqual(disclosure["ids"], self.SIR_IDS)
        self.assertEqual(disclosure["issues"], [])
        self.assertIn("Ownership therefore stays with this dataset", disclosure["summary"])
        # 171 leftover-in-id names split 167 same-factory + 4 foreign, not 171.
        joined = " ".join(item["summary"] for item in self.declaration["disclosures"])
        self.assertIn("167 same-factory plus 4 foreign", joined)


if __name__ == "__main__":
    unittest.main()
