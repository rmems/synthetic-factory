#!/usr/bin/env python3
"""PR #132 / issue #66 leaf tests for the per-dataset card schema declaration."""

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


INCIDENT_RESPONSE = "incident-response-oncall-trajectories"
INCIDENT_RESPONSE_MIRROR = (
    Path.home() / "rmems/hf/grok-4.6/incident-response-oncall-trajectories/data/raw"
)
INCIDENT_RESPONSE_PAYLOAD_NAMES = tuple(
    f"batch-r{round_number:02}.jsonl" for round_number in range(1, 3853)
)


# Minimal values copied from one published record in each payload family. These
# fixtures ground the declaration tests in observed values instead of deriving
# both the expected and actual types from the declaration under test.
OBSERVED_FAMILY_TYPE_FIXTURES = {
    "oncall": {
        "id": "irc-r01-oom-sidecar-helm-2661",
        "kind": "episode",
        "false_lead": {
            "claim": "CPU throttle on checkout-api; scale past HPA max",
            "survived_steps": [6, 7, 8],
            "falsified_at": 10,
        },
        "rca": "helm history checkout-api -n checkout",
        "remediate": "rollback",
    },
    "opensre": {
        "id": "irc-r02-b-replag-cpu-analytics",
        "true_root_cause": "replication_lag_wal_volume",
        "red_herring": "CPUUtilization from an unrelated analytics SELECT",
        "forbidden_diagnosis": "cpu_saturation",
        "required_evidence": [
            "pagerduty",
            "aws_cloudwatch_metrics",
            "aws_performance_insights",
            "aws_rds_events",
            "describe_rds_instance",
            "checkout_dsn",
        ],
    },
    "sir": {"id": "sir-r3382-meili-swap-leftover3c-rebuild"},
}


INCIDENT_RESPONSE_SIR_IDS = (
    "sir-r3382-meili-swap-leftover3c-rebuild",
    "sir-r3382-meili-drop-index-leftover3c-handoff",
    "sir-r3383-typesense-alias-leftover3c-rebuild",
    "sir-r3383-typesense-drop-coll-leftover3c-handoff",
    "sir-r3384-sonic-push-leftover3c-rebuild",
    "sir-r3384-sonic-drop-bucket-leftover3c-handoff",
    "sir-r3385-tantivy-commit-leftover3c-rebuild",
    "sir-r3385-tantivy-drop-writer-leftover3c-handoff",
    "sir-r3386-xapian-flint-leftover3c-rebuild",
    "sir-r3386-xapian-drop-flint-leftover3c-handoff",
    "sir-r3387-manticore-rt-leftover3c-rebuild",
    "sir-r3387-manticore-drop-rt-leftover3c-handoff",
    "sir-r3388-zinc-alias-leftover3c-rebuild",
    "sir-r3388-zinc-drop-index-leftover3c-handoff",
    "sir-r3389-opensearch-reindex-leftover3c-rebuild",
    "sir-r3389-opensearch-drop-reindex-leftover3c-handoff",
)


class IncidentResponseOncallDeclarationTests(unittest.TestCase):
    """PR #132 / issue #66: three record families share one destination.

    The counts asserted here were derived by scanning every published record in
    the read-only mirror at
    ``~/rmems/hf/grok-4.6/incident-response-oncall-trajectories`` (7704 records
    across 3852 shards, 0 parse failures, 139086 steps), not transcribed from
    the issue. The three families are 7668 on-call RCA episodes, 20 OpenSRE
    seed rows, and the 16 dest-stamped ``sir-*`` search-index rows.
    """

    def setUp(self):
        self.declaration = card_schema.load(INCIDENT_RESPONSE)
        self.assertIsNotNone(
            self.declaration,
            "PR #132 is missing the config/card-schemas declaration for issue #66",
        )
        self.item = {
            "slug": "incident-response-oncall-factory",
            "hub": INCIDENT_RESPONSE,
            "pretty": "Incident Response Oncall Trajectories",
            "blurb": "On-call leftover-signal RCA trajectories.",
            "tags": ["synthetic-data", "trajectories", "incident-response", "sre"],
        }
        self.card = publisher.render_card(
            self.item,
            records=7704,
            bytes_=66481787,
            first="01",
            last="3852",
            payload_names=list(INCIDENT_RESPONSE_PAYLOAD_NAMES),
        )

    def test_declaration_matches_the_observed_union_schema(self):
        features = self.declaration["features"]
        self.assertEqual(
            [feature["name"] for feature in features],
            [
                "id",
                "goal",
                "plan",
                "kind",
                "true_root_cause",
                "red_herring",
                "forbidden_diagnosis",
                "required_evidence",
                "steps",
                "outcome",
                "reward",
                "false_lead",
                "rca",
                "remediate",
                "meta",
            ],
        )
        names = {feature["name"]: feature for feature in features}
        # Present on every one of the 7704 records, so never flagged optional.
        for name in ("id", "goal", "plan", "steps", "outcome", "reward", "meta"):
            with self.subTest(field=name):
                self.assertFalse(names[name].get("optional", False))
        # `plan` is a plain string on all 7704 records: it is neither optional
        # (as in the worked #36 example) nor list-vs-string.
        self.assertEqual(names["plan"]["dtype"], "string")
        # Each of these belongs to exactly one family, so each is absent on the
        # other two and must be declared optional or the cast dies.
        for name in (
            "kind",
            "true_root_cause",
            "red_herring",
            "forbidden_diagnosis",
            "required_evidence",
            "false_lead",
            "rca",
            "remediate",
        ):
            with self.subTest(field=name):
                self.assertTrue(names[name]["optional"], f"{name} is not on every record")
        self.assertEqual(self.declaration["issues"], [66])

    def test_family_specific_scalars_keep_their_real_types(self):
        oncall = OBSERVED_FAMILY_TYPE_FIXTURES["oncall"]
        opensre = OBSERVED_FAMILY_TYPE_FIXTURES["opensre"]
        sir = OBSERVED_FAMILY_TYPE_FIXTURES["sir"]
        self.assertIsInstance(oncall["kind"], str)
        self.assertIsInstance(oncall["rca"], str)
        self.assertIsInstance(oncall["remediate"], str)
        self.assertIsInstance(opensre["true_root_cause"], str)
        self.assertIsInstance(opensre["red_herring"], str)
        self.assertIsInstance(opensre["forbidden_diagnosis"], str)
        self.assertTrue(all(isinstance(item, str) for item in opensre["required_evidence"]))
        self.assertNotIn("kind", sir)

        names = {feature["name"]: feature for feature in self.declaration["features"]}
        # The issue asks for these as `json`, but each is a plain string on
        # 100% of the records that carry it, so a nullable string is both
        # castable and searchable in the viewer.
        for name in ("kind", "true_root_cause", "red_herring", "forbidden_diagnosis"):
            with self.subTest(field=name):
                self.assertEqual(names[name]["dtype"], "string")
        # `required_evidence` is a list of strings on the 2 records that have it.
        self.assertEqual(names["required_evidence"]["list"], "string")

    def test_false_lead_is_declared_as_its_stable_struct(self):
        observed = OBSERVED_FAMILY_TYPE_FIXTURES["oncall"]["false_lead"]
        self.assertEqual(set(observed), {"claim", "survived_steps", "falsified_at"})
        self.assertIsInstance(observed["claim"], str)
        self.assertTrue(all(isinstance(step, int) for step in observed["survived_steps"]))
        self.assertIsInstance(observed["falsified_at"], int)

        false_lead = next(
            feature
            for feature in self.declaration["features"]
            if feature["name"] == "false_lead"
        )
        children = {child["name"]: child for child in false_lead["struct"]}
        # All 7668 on-call episodes carry exactly these three keys, and none of
        # them varies in type, so the nullable struct is castable and more
        # useful in the viewer than an opaque json blob.
        self.assertEqual(set(children), {"claim", "survived_steps", "falsified_at"})
        self.assertEqual(children["claim"]["dtype"], "string")
        self.assertEqual(children["survived_steps"]["list"], "int64")
        self.assertEqual(children["falsified_at"]["dtype"], "int64")

    def test_steps_keep_the_public_decision_basis_and_a_json_arg_bag(self):
        steps = next(
            feature
            for feature in self.declaration["features"]
            if feature["name"] == "steps"
        )
        children = {child["name"]: child for child in steps["list"]}
        self.assertEqual(
            set(children), {"n", "decision_basis", "tool_call", "observation", "reflection"}
        )
        self.assertFalse(children["decision_basis"].get("optional", False))
        # 40625 of 139086 steps carry a reflection.
        self.assertTrue(children["reflection"]["optional"])
        tool_call = {child["name"]: child for child in children["tool_call"]["struct"]}
        self.assertEqual(set(tool_call), {"name", "args"})
        self.assertEqual(tool_call["args"]["dtype"], "json")

    def test_only_the_key_bag_columns_are_declared_json(self):
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
        self.assertIn("  - name: required_evidence\n    list: string\n", front_matter)
        # The card-only annotations must never reach the YAML.
        self.assertNotIn("optional:", front_matter)
        self.assertNotIn("note:", front_matter)
        # license/tags/status claims stay exactly where they were.
        self.assertIn("license: apache-2.0", front_matter)
        self.assertIn("**not training-ready**", self.card)

    def test_declared_glob_covers_the_complete_published_payload_snapshot(self):
        self.assertEqual(len(INCIDENT_RESPONSE_PAYLOAD_NAMES), 3852)
        self.assertEqual(
            card_schema.payload_coverage_errors(
                self.declaration,
                list(INCIDENT_RESPONSE_PAYLOAD_NAMES),
            ),
            [],
        )

    def test_card_body_discloses_all_three_families(self):
        self.assertIn("## Dataset viewer schema", self.card)
        self.assertNotIn("**Not declared yet.**", self.card)
        for record_id in INCIDENT_RESPONSE_SIR_IDS:
            with self.subTest(record_id=record_id):
                self.assertIn(f"`{record_id}`", self.card)
        # The same-factory leftover-signal mechanic is named as such, so it is
        # not mistaken for the dest-stamped mill rows.
        self.assertIn("advertised leftover-signal mechanic", self.card)
        # The OpenSRE rows are disclosed as same-factory, not foreign payload.
        self.assertIn("`meta.opensre_seed`", self.card)
        self.assertIn("| `false_lead` | optional |", self.card)
        self.assertIn("| `steps[].reflection` | optional |", self.card)
        self.assertIn("| `required_evidence` | optional |", self.card)
        self.assertIn("| `plan` | present on every record |", self.card)

    def test_the_disclosed_mill_rows_carry_the_related_mill_issues(self):
        mill = next(
            disclosure
            for disclosure in self.declaration["disclosures"]
            if disclosure["ids"]
        )
        self.assertEqual(tuple(mill["ids"]), INCIDENT_RESPONSE_SIR_IDS)
        # Neither frozen mill census owns this destination, so #66 keeps it
        # while still pointing at the related mill issues.
        self.assertEqual(mill["issues"], [43, 44, 66])

    @unittest.skipUnless(
        INCIDENT_RESPONSE_MIRROR.is_dir(),
        "read-only published mirror is not available",
    )
    def test_published_mirror_independently_matches_the_schema_snapshot(self):
        payloads = sorted(INCIDENT_RESPONSE_MIRROR.glob("*.jsonl"))
        self.assertEqual(
            {payload.name for payload in payloads},
            set(INCIDENT_RESPONSE_PAYLOAD_NAMES),
        )
        self.assertEqual(
            card_schema.payload_coverage_errors(
                self.declaration,
                [payload.name for payload in payloads],
            ),
            [],
        )

        records = 0
        steps = 0
        reflections = 0
        family_counts = {"oncall": 0, "opensre": 0, "sir": 0}
        field_counts = {
            "true_root_cause": 0,
            "red_herring": 0,
            "forbidden_diagnosis": 0,
            "required_evidence": 0,
        }
        leftover_irc_ids = 0
        leftover_irc_goals = 0
        leftover_all_goals = 0
        sir_ids = set()

        for payload in payloads:
            with payload.open(encoding="utf-8") as handle:
                for line_number, line in enumerate(handle, start=1):
                    if not line.strip():
                        continue
                    record = json.loads(line)
                    location = f"{payload.name}:{line_number}"
                    self.assertIsInstance(record["plan"], str, location)
                    self.assertTrue(record["plan"].strip(), location)

                    if "false_lead" in record:
                        family_counts["oncall"] += 1
                        self.assertIsInstance(record["kind"], str, location)
                        self.assertIsInstance(record["rca"], str, location)
                        self.assertIsInstance(record["remediate"], str, location)
                        false_lead = record["false_lead"]
                        self.assertEqual(
                            set(false_lead),
                            {"claim", "survived_steps", "falsified_at"},
                            location,
                        )
                        self.assertIsInstance(false_lead["claim"], str, location)
                        self.assertTrue(
                            all(isinstance(step, int) for step in false_lead["survived_steps"]),
                            location,
                        )
                        self.assertIsInstance(false_lead["falsified_at"], int, location)
                    elif "opensre_seed" in record["meta"]:
                        family_counts["opensre"] += 1
                    else:
                        family_counts["sir"] += 1
                        sir_ids.add(record["id"])

                    for name in field_counts:
                        if name not in record:
                            continue
                        field_counts[name] += 1
                        if name == "required_evidence":
                            self.assertTrue(
                                all(isinstance(item, str) for item in record[name]),
                                location,
                            )
                        else:
                            self.assertIsInstance(record[name], str, location)

                    is_irc = record["id"].startswith("irc-")
                    leftover_irc_ids += is_irc and "leftover" in record["id"].lower()
                    leftover_irc_goals += is_irc and "leftover" in record["goal"].lower()
                    leftover_all_goals += "leftover" in record["goal"].lower()
                    steps += len(record["steps"])
                    reflections += sum("reflection" in step for step in record["steps"])
                    records += 1

        self.assertEqual(records, 7704)
        self.assertEqual(steps, 139086)
        self.assertEqual(reflections, 40625)
        self.assertEqual(family_counts, {"oncall": 7668, "opensre": 20, "sir": 16})
        self.assertEqual(
            field_counts,
            {
                "true_root_cause": 20,
                "red_herring": 20,
                "forbidden_diagnosis": 16,
                "required_evidence": 2,
            },
        )
        self.assertEqual(leftover_irc_ids, 113)
        self.assertEqual(leftover_irc_goals, 1701)
        self.assertEqual(leftover_all_goals, 1717)
        self.assertEqual(sir_ids, set(INCIDENT_RESPONSE_SIR_IDS))


if __name__ == "__main__":
    unittest.main()
