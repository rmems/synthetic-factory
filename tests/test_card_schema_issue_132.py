#!/usr/bin/env python3
"""PR #132 / issue #66 leaf tests for the per-dataset card schema declaration."""

import json
import unittest

from card_schema_test_support import (
    EPISODE_FIELD_ORDER,
    EPISODE_JSON_COLUMNS,
    FEATURES_YAML,
    META_JSON_YAML,
    NOT_DECLARED,
    PLAN_PRESENT_ROW,
    REFLECTION_OPTIONAL_ROW,
    REWARD_JSON_YAML,
    STEP_FIELDS,
    TOOL_CALL_FIELDS,
    VIEWER_SCHEMA_HEADING,
    DeclarationTestCase,
    by_name,
    card_schema,
    feature_names,
    mirror_path,
    needs_mirror,
    publisher,
)

INCIDENT_RESPONSE = "incident-response-oncall-trajectories"
INCIDENT_RESPONSE_MIRROR = mirror_path(INCIDENT_RESPONSE)
INCIDENT_RESPONSE_PAYLOAD_NAMES = tuple(
    f"batch-r{round_number:02}.jsonl" for round_number in range(1, 5027)
)

# The published column order interleaves the families: the OpenSRE seed
# fields follow `kind`, the on-call RCA fields follow `reward`.
OPENSRE_SEED_FIELDS = ["true_root_cause", "red_herring", "forbidden_diagnosis", "required_evidence"]
ONCALL_RCA_FIELDS = ["false_lead", "rca", "remediate"]
INCIDENT_RESPONSE_FIELD_ORDER = [
    "id", "goal", "plan", "kind", *OPENSRE_SEED_FIELDS,
    "steps", "outcome", "reward", *ONCALL_RCA_FIELDS, "meta",
]

_needs_mirror = needs_mirror(INCIDENT_RESPONSE_MIRROR)


def _load_mirror_records(mirror):
    """Read every payload record in the mirror, tagged with its location."""
    payloads = sorted(mirror.glob("*.jsonl"))
    records = []
    for payload in payloads:
        with payload.open(encoding="utf-8") as handle:
            for line_number, line in enumerate(handle, start=1):
                if line.strip():
                    location = f"{payload.name}:{line_number}"
                    records.append((location, json.loads(line)))
    return payloads, records


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


class IncidentResponseOncallDeclarationTests(DeclarationTestCase):
    """PR #132 / issue #66: three record families share one destination.

    The counts asserted here were derived by scanning every published record in
    the read-only mirror at
    ``~/rmems/hf/grok-4.6/incident-response-oncall-trajectories`` (10052 records
    across 5026 shards, 0 parse failures, 178998 steps), not transcribed from
    the issue. The three families are 10016 on-call RCA episodes, 20 OpenSRE
    seed rows, and the 16 dest-stamped ``sir-*`` search-index rows. The census
    was re-grounded on 2026-08-30 after the factory appended rounds
    r3853-r5026 (2348 further on-call episodes; no new field, family, reward
    key set, or foreign row).
    """

    DATASET = INCIDENT_RESPONSE
    ISSUE = 66
    MISSING_MESSAGE = "PR #132 is missing the config/card-schemas declaration for issue #66"
    HUB_ITEM = {
        "slug": "incident-response-oncall-factory",
        "hub": INCIDENT_RESPONSE,
        "pretty": "Incident Response Oncall Trajectories",
        "blurb": "On-call leftover-signal RCA trajectories.",
        "tags": ["synthetic-data", "trajectories", "incident-response", "sre"],
    }
    SUMMARY = publisher.PayloadSummary(
        records=10052,
        bytes_=85596311,
        first="01",
        last="5026",
        names=list(INCIDENT_RESPONSE_PAYLOAD_NAMES),
    )

    def test_declaration_matches_the_observed_union_schema(self):
        self.assertEqual(feature_names(self.declaration["features"]), INCIDENT_RESPONSE_FIELD_ORDER)
        names = self.names()
        # Present on every one of the 10052 records, so never flagged optional.
        for name in EPISODE_FIELD_ORDER:
            with self.subTest(field=name):
                self.assertFalse(names[name].get("optional", False))
        # `plan` is a plain string on all 10052 records: it is neither optional
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

        names = self.names()
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

        children = by_name(self.feature("false_lead")["struct"])
        # All 10016 on-call episodes carry exactly these three keys, and none of
        # them varies in type, so the nullable struct is castable and more
        # useful in the viewer than an opaque json blob.
        self.assertEqual(set(children), {"claim", "survived_steps", "falsified_at"})
        self.assertEqual(children["claim"]["dtype"], "string")
        self.assertEqual(children["survived_steps"]["list"], "int64")
        self.assertEqual(children["falsified_at"]["dtype"], "int64")

    def test_steps_keep_the_public_decision_basis_and_a_json_arg_bag(self):
        children = by_name(self.feature("steps")["list"])
        self.assertEqual(set(children), STEP_FIELDS)
        self.assertFalse(children["decision_basis"].get("optional", False))
        # 54713 of 178998 steps carry a reflection.
        self.assertTrue(children["reflection"]["optional"])
        tool_call = self.tool_call_features(children)
        self.assertEqual(set(tool_call), TOOL_CALL_FIELDS)
        self.assertEqual(tool_call["args"]["dtype"], "json")

    def test_only_the_key_bag_columns_are_declared_json(self):
        self.assert_json_columns(EPISODE_JSON_COLUMNS)

    def test_card_front_matter_declares_the_default_config_over_raw_batches(self):
        self.assert_front_matter_declares_default_config(
            FEATURES_YAML,
            META_JSON_YAML,
            REWARD_JSON_YAML,
            "  - name: required_evidence\n    list: string\n",
            # The card-only annotations must never reach the YAML.
            absent=("optional:", "note:"),
        )

    def test_declared_glob_covers_the_complete_published_payload_snapshot(self):
        self.assertEqual(len(INCIDENT_RESPONSE_PAYLOAD_NAMES), 5026)
        self.assertEqual(
            card_schema.payload_coverage_errors(
                self.declaration,
                list(INCIDENT_RESPONSE_PAYLOAD_NAMES),
            ),
            [],
        )

    def test_card_body_discloses_all_three_families(self):
        self.assertIn(VIEWER_SCHEMA_HEADING, self.card)
        self.assertNotIn(NOT_DECLARED, self.card)
        self.assert_card_names_records(INCIDENT_RESPONSE_SIR_IDS)
        self.assert_card_has(
            # The same-factory leftover-signal mechanic is named as such, so it is
            # not mistaken for the dest-stamped mill rows.
            "advertised leftover-signal mechanic",
            # The OpenSRE rows are disclosed as same-factory, not foreign payload.
            "`meta.opensre_seed`",
            "| `false_lead` | optional |",
            REFLECTION_OPTIONAL_ROW,
            "| `required_evidence` | optional |",
            PLAN_PRESENT_ROW,
        )

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

    # -- Re-derived from the payload, not from the declaration -------------
    #
    # Every assertion of the original single mirror walk is preserved below,
    # split into focused tests over one cached read-only scan so no method
    # carries the whole census by itself.

    @classmethod
    def _mirror(cls):
        """Scan the published mirror once, then reuse it across these tests."""
        if getattr(cls, "_mirror_cache", None) is None:
            cls._mirror_cache = _load_mirror_records(INCIDENT_RESPONSE_MIRROR)
        return cls._mirror_cache

    @staticmethod
    def _family(record):
        """The family classifier the declaration's three shapes are built on."""
        if "false_lead" in record:
            return "oncall"
        if "opensre_seed" in record["meta"]:
            return "opensre"
        return "sir"

    @_needs_mirror
    def test_published_shards_are_exactly_the_declared_shard_list(self):
        payloads, _records = self._mirror()
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

    @_needs_mirror
    def test_mirror_census_counts_match_the_declared_snapshot(self):
        _payloads, records = self._mirror()
        steps = [step for _location, record in records for step in record["steps"]]
        self.assertEqual(len(records), 10052)
        self.assertEqual(len(steps), 178998)
        self.assertEqual(sum("reflection" in step for step in steps), 54713)

    @_needs_mirror
    def test_mirror_family_counts_and_sir_ids_match_the_disclosures(self):
        _payloads, records = self._mirror()
        family_counts = {"oncall": 0, "opensre": 0, "sir": 0}
        sir_ids = set()
        for _location, record in records:
            family = self._family(record)
            family_counts[family] += 1
            if family == "sir":
                sir_ids.add(record["id"])
        self.assertEqual(family_counts, {"oncall": 10016, "opensre": 20, "sir": 16})
        self.assertEqual(sir_ids, set(INCIDENT_RESPONSE_SIR_IDS))

    @_needs_mirror
    def test_mirror_plans_are_always_nonempty_strings(self):
        _payloads, records = self._mirror()
        for location, record in records:
            self.assertIsInstance(record["plan"], str, location)
            self.assertTrue(record["plan"].strip(), location)

    @_needs_mirror
    def test_mirror_opensre_scalars_keep_their_declared_presence_and_types(self):
        _payloads, records = self._mirror()
        field_counts = {
            "true_root_cause": 0,
            "red_herring": 0,
            "forbidden_diagnosis": 0,
            "required_evidence": 0,
        }
        for location, record in records:
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
        self.assertEqual(
            field_counts,
            {
                "true_root_cause": 20,
                "red_herring": 20,
                "forbidden_diagnosis": 16,
                "required_evidence": 2,
            },
        )

    @_needs_mirror
    def test_mirror_oncall_rows_keep_the_closed_false_lead_struct(self):
        _payloads, records = self._mirror()
        oncall = [
            (location, record)
            for location, record in records
            if self._family(record) == "oncall"
        ]
        self.assertEqual(len(oncall), 10016)
        for location, record in oncall:
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

    @_needs_mirror
    def test_mirror_leftover_naming_counts_match_the_disclosure(self):
        _payloads, records = self._mirror()
        irc = [record for _location, record in records if record["id"].startswith("irc-")]
        self.assertEqual(
            sum("leftover" in record["id"].lower() for record in irc), 113
        )
        self.assertEqual(
            sum("leftover" in record["goal"].lower() for record in irc), 4049
        )
        self.assertEqual(
            sum("leftover" in record["goal"].lower() for _location, record in records),
            4065,
        )


if __name__ == "__main__":
    unittest.main()
