#!/usr/bin/env python3
"""Issue #40 leaf tests for the per-dataset card schema declaration."""

import json
import re
import tempfile
import unittest
from pathlib import Path

from card_schema_test_support import (
    EPISODE_JSON_COLUMNS,
    NOT_DECLARED,
    REWARD_JSON_YAML,
    TOOL_CALL_FIELDS,
    VIEWER_SCHEMA_HEADING,
    DeclarationTestCase,
    feature_index,
    iter_steps,
    mirror_path,
    needs_mirror,
    publisher,
    scan_mirror,
)

# Resolvable once card_schema_test_support has put pipelines/ on sys.path.
import round_txn

SAFETY_CALIBRATION = "safety-calibration-cases"
SAFETY_FACTORY = "safety-calibration-factory"

SAFETY_CALIBRATION_MIRROR = mirror_path(SAFETY_CALIBRATION)


def _safety_record(case_type: str, index: int) -> dict:
    """A minimal record the agentic envelope validator accepts."""
    return {
        "id": f"saf-r07-fixture-{index}",
        "goal": "g",
        "case_type": case_type,
        "should_refuse": True,
        "decision": "refuse",
        "rationale": "r",
        "steps": [
            {
                "n": 1,
                "decision_basis": "b",
                "tool_call": {"name": "read", "args": {"path": "p"}},
                "observation": "o",
            }
        ],
        "outcome": "o",
        "reward": {"success": True, "calibration": 0.5},
        "meta": {
            "factory": SAFETY_FACTORY,
            "generator": "grok-4.6",
            "round": 7,
        },
    }


_needs_mirror = needs_mirror(SAFETY_CALIBRATION_MIRROR)

_ANNOTATION_EXTRAS = ("redirect", "vector", "benign_twin")


def _tally(values):
    """Count occurrences of each value in an iterable."""
    seen: dict = {}
    for value in values:
        seen[value] = seen.get(value, 0) + 1
    return seen


def _disclosure_text(declaration):
    """The disclosure prose, flattened across string and structured entries."""
    return " ".join(
        item if isinstance(item, str) else item["summary"]
        for item in declaration["disclosures"]
    )


def _reward_keysets(records):
    """Distinct `reward` keysets with counts, and per-key record counts."""
    keysets = _tally(frozenset(record["reward"]) for _shard, record in records)
    reward_keys: dict = {}
    for _shard, record in records:
        for key in record["reward"]:
            reward_keys[key] = reward_keys.get(key, 0) + 1
    return keysets, reward_keys


def _case_type_spread(records, field):
    """How the records carrying `field` spread across `case_type`."""
    return _tally(
        record["case_type"] for _shard, record in records if field in record
    )


def _annotation_free(record):
    """True when a record omits `trigger` and all three case extras."""
    return "trigger" not in record and not any(
        field in record for field in _ANNOTATION_EXTRAS
    )


def _disclosed_ids(declaration):
    """Every record id listed by the structured disclosure entries."""
    return {
        record_id
        for item in declaration["disclosures"]
        if isinstance(item, dict)
        for record_id in item["ids"]
    }


class SafetyCalibrationDeclarationTests(DeclarationTestCase):
    """Issue #40: `reward.recovered_overrefusal` plus mutually exclusive extras.

    Counts below are derived from the published mirror
    (`~/rmems/hf/grok-4.6/safety-calibration-cases`, 5354 shards / 16062 records
    / 142873 steps), not transcribed from the issue body.
    """

    DATASET = SAFETY_CALIBRATION
    ISSUE = 40
    HUB_ITEM = {
        "slug": "safety-calibration-factory",
        "hub": SAFETY_CALIBRATION,
        "pretty": "Safety Calibration Cases",
        "blurb": "Safety leftover-refusal calibration cases.",
        "tags": ["synthetic-data", "safety", "calibration", "refusal"],
    }
    SUMMARY = publisher.PayloadSummary(
        records=16062,
        bytes_=76017664,
        first="r01",
        last="r5354",
        names=["batch-r01.jsonl", "batch-r5354.jsonl"],
    )

    def test_declaration_matches_the_observed_union_schema(self):
        names = self.names()
        self.assertEqual(
            set(names),
            {
                "id",
                "goal",
                "case_type",
                "should_refuse",
                "decision",
                "rationale",
                "steps",
                "outcome",
                "reward",
                "meta",
                "trigger",
                "redirect",
                "vector",
                "benign_twin",
            },
        )
        self.assertEqual(names["should_refuse"]["dtype"], "bool")
        for required in ("id", "goal", "case_type", "decision", "rationale", "outcome"):
            self.assertNotIn("optional", names[required], required)
        # The 18 annotation-free records and the three mutually exclusive extras.
        for optional in ("trigger", "redirect", "vector", "benign_twin"):
            with self.subTest(field=optional):
                self.assertTrue(names[optional]["optional"])
                self.assertEqual(names[optional]["dtype"], "string")
                self.assertIn("of 16062 records", names[optional]["note"])
        steps = self.step_features(names)
        # No `reflection` here: every one of the 142873 steps has the same four keys.
        self.assertEqual(set(steps), {"n", "decision_basis", "tool_call", "observation"})
        tool_call = self.tool_call_features(steps)
        self.assertEqual(set(tool_call), TOOL_CALL_FIELDS)
        self.assertEqual(self.declaration["issues"], [40])

    def test_key_bag_columns_are_declared_json(self):
        # `reward` is the column the viewer died casting; `meta` is a key-bag too
        # because `sim_or_real` is absent from 771 of 16062 records.
        self.assert_json_columns(EPISODE_JSON_COLUMNS)
        names = self.names()
        self.assertIn("recovered_overrefusal", names["reward"]["note"])
        self.assertIn("sim_or_real", names["meta"]["note"])

    def test_card_front_matter_declares_the_default_config_over_raw_batches(self):
        self.assert_front_matter_declares_default_config(
            REWARD_JSON_YAML,
            "  - name: should_refuse\n    dtype: bool\n",
            "  - name: benign_twin\n    dtype: string\n",
            absent=("optional",),
        )

    def test_card_body_discloses_the_case_type_split_and_the_annotation_gap(self):
        self.assertIn(VIEWER_SCHEMA_HEADING, self.card)
        self.assertNotIn(NOT_DECLARED, self.card)
        # The 5354 x 3 split the issue asks the card to disclose.
        self.assertIn("5354 / 5354 / 5354", self.card)
        for case_type in ("correct_refusal", "incorrect_refusal", "missed_refusal"):
            self.assertIn(f"`{case_type}`", self.card)
        self.assert_card_has(
            "| `trigger` | optional |",
            "| `benign_twin` | optional |",
            "`saf-r123-pickle-load-uploads`",
            "`saf-r128-sourcemap-secrets`",
        )

    def test_every_disclosed_record_id_is_a_safety_case_id(self):
        ids = [
            record_id
            for disclosure in self.declaration["disclosures"]
            for record_id in disclosure["ids"]
        ]
        self.assertEqual(len(ids), 18)
        self.assertEqual(len(set(ids)), 18)
        for record_id in ids:
            with self.subTest(record_id=record_id):
                self.assertRegex(record_id, r"^saf-r12[3-8]-")

    def test_case_type_balance_matches_the_round_txn_batch_contract(self):
        """Tie the 5354 x 3 = 16062 arithmetic to the pipeline's own contract.

        Every other assertion in this class reads numbers out of the same file
        it is checking. `round_txn` is the one independent in-repo authority on
        this dataset's shape: `FACTORY_QUOTAS` fixes 3 records per batch and
        `validate_agentic_envelope` refuses any batch that is not exactly one
        each of the three case types. Both are exercised here rather than
        restated, so a drifted count or a renamed case type fails.
        """
        names = self.names()
        case_note = names["case_type"]["note"]
        declared_types = re.findall(r"`([a-z_]+_refusal)`", case_note)
        self.assertEqual(len(declared_types), 3)
        per_case = int(re.search(r"(\d+) records each", case_note).group(1))
        total = int(re.search(r"of (\d+) records", names["trigger"]["note"]).group(1))

        quota = round_txn.FACTORY_QUOTAS[SAFETY_FACTORY]
        self.assertEqual(quota, len(declared_types))
        # One of each per batch at a quota of 3 means the three case types are
        # equal thirds and the batch count is the per-case count.
        self.assertEqual(per_case * len(declared_types), total)
        self.assertEqual(total % quota, 0)
        self.assertEqual(total // quota, per_case)
        self.assertIn(" / ".join([str(per_case)] * 3), self.card)

        # Drive the real validator with the declaration's own case-type names:
        # a batch of one each must be accepted, a duplicate must be rejected.
        # A renamed or invented case type fails the first call.
        marker = "requires exactly one each"
        with tempfile.TemporaryDirectory() as tmp:
            factory_dir = Path(tmp) / SAFETY_FACTORY
            (factory_dir / "raw").mkdir(parents=True)
            batch = factory_dir / "raw" / "batch-r07.jsonl"
            for label, case_types in (
                ("one of each", declared_types),
                ("duplicate", [declared_types[0]] + declared_types[:2]),
            ):
                with self.subTest(batch=label):
                    batch.write_text(
                        "\n".join(
                            json.dumps(_safety_record(case_type, index))
                            for index, case_type in enumerate(case_types)
                        )
                        + "\n",
                        encoding="utf-8",
                    )
                    errors = round_txn.validate_agentic_envelope(batch, factory_dir, 7)
                    offending = [e for e in errors or [] if marker in e]
                    if label == "one of each":
                        self.assertEqual(offending, [])
                    else:
                        self.assertTrue(offending)

    # -- Re-derived from the payload, not from the declaration -------------
    #
    # The tests above compare the declaration against expectations typed
    # beside it. The tests below re-derive the declaration's counts from the
    # published payload instead, so they fail when the two drift apart.

    @_needs_mirror
    def test_published_shard_and_record_counts_match_the_declaration(self):
        shards, records = scan_mirror(SAFETY_CALIBRATION_MIRROR)
        self.assertEqual(len(shards), 5354)
        self.assertEqual(len(records), 16062)

    @_needs_mirror
    def test_every_record_carries_exactly_the_declared_top_level_fields(self):
        _shards, records = scan_mirror(SAFETY_CALIBRATION_MIRROR)
        names, optional = feature_index(self.declaration["features"])
        for shard, record in records:
            self.assertEqual(set(record) - set(names), set(), shard)
            self.assertEqual(set(names) - set(record) - optional, set(), shard)

    @_needs_mirror
    def test_the_batch_contract_holds_per_shard_and_per_case_type(self):
        """The batch contract, observed rather than assumed."""
        shards, records = scan_mirror(SAFETY_CALIBRATION_MIRROR)
        names, _optional = feature_index(self.declaration["features"])
        per_shard = _tally(shard for shard, _record in records)
        self.assertEqual(
            set(per_shard.values()), {round_txn.FACTORY_QUOTAS[SAFETY_FACTORY]}
        )
        by_case = _tally(record["case_type"] for _shard, record in records)
        self.assertEqual(by_case, {k: len(shards) for k in by_case})
        self.assertEqual(len(by_case), 3)
        self.assertIn(f"{len(shards)} records each", names["case_type"]["note"])
        self.assertIn(" / ".join([str(len(shards))] * 3), self.card)

    @_needs_mirror
    def test_the_decision_note_lists_every_published_decision_count(self):
        _shards, records = scan_mirror(SAFETY_CALIBRATION_MIRROR)
        names, _optional = feature_index(self.declaration["features"])
        decisions = _tally(record["decision"] for _shard, record in records)
        for decision, count in decisions.items():
            with self.subTest(decision=decision):
                self.assertIn(f"`{decision}` ({count})", names["decision"]["note"])

    @_needs_mirror
    def test_the_three_reward_keysets_match_the_note_and_disclosures(self):
        """`reward`: the three keysets and the key the cast died on."""
        _shards, records = scan_mirror(SAFETY_CALIBRATION_MIRROR)
        names, _optional = feature_index(self.declaration["features"])
        total = len(records)
        keysets, reward_keys = _reward_keysets(records)
        disclosures = _disclosure_text(self.declaration)
        self.assertEqual(len(keysets), 3)
        self.assertEqual(reward_keys["success"], total)
        reward_note = names["reward"]["note"]
        self.assertIn(
            f"`calibration` (float) on {reward_keys['calibration']}", reward_note
        )
        self.assertIn(
            f"`recovered_overrefusal` (bool) on {reward_keys['recovered_overrefusal']}",
            reward_note,
        )
        for keyset, count in keysets.items():
            with self.subTest(reward_keys=sorted(keyset)):
                self.assertIn(f"{count} ", disclosures)

    @_needs_mirror
    def test_recovered_overrefusal_is_scoped_to_incorrect_refusals(self):
        _shards, records = scan_mirror(SAFETY_CALIBRATION_MIRROR)
        disclosures = _disclosure_text(self.declaration)
        recovered = [r for _s, r in records if "recovered_overrefusal" in r["reward"]]
        self.assertEqual({r["case_type"] for r in recovered}, {"incorrect_refusal"})
        true_count = sum(1 for r in recovered if r["reward"]["recovered_overrefusal"])
        self.assertIn(
            f"({true_count} true, {len(recovered) - true_count} false)", disclosures
        )

    @_needs_mirror
    def test_success_only_records_are_exactly_those_without_sim_or_real(self):
        """The 771 `{success}`-only records are the same 771 without sim_or_real."""
        _shards, records = scan_mirror(SAFETY_CALIBRATION_MIRROR)
        names, _optional = feature_index(self.declaration["features"])
        total = len(records)
        disclosures = _disclosure_text(self.declaration)
        success_only = {r["id"] for _s, r in records if set(r["reward"]) == {"success"}}
        no_sim = {r["id"] for _s, r in records if "sim_or_real" not in r["meta"]}
        self.assertEqual(success_only, no_sim)
        self.assertIn(f"The {len(success_only)} `{{success}}`-only records", disclosures)
        self.assertIn(
            f"`sim_or_real` on {total - len(no_sim)} of {total}", names["meta"]["note"]
        )

    @_needs_mirror
    def test_each_optional_annotation_matches_its_declared_note(self):
        _shards, records = scan_mirror(SAFETY_CALIBRATION_MIRROR)
        names, _optional = feature_index(self.declaration["features"])
        total = len(records)
        for field in ("trigger", "redirect", "vector", "benign_twin"):
            present = [r for _s, r in records if field in r]
            with self.subTest(field=field):
                self.assertIn(
                    f"present on {len(present)} of {total} records", names[field]["note"]
                )
                self.assertTrue(all(isinstance(r[field], str) for r in present))
        self.assertIn(
            f"{len({r['trigger'] for _s, r in records if 'trigger' in r})} distinct values",
            names["trigger"]["note"],
        )

    @_needs_mirror
    def test_the_annotation_extras_are_exclusive_and_spread_as_declared(self):
        _shards, records = scan_mirror(SAFETY_CALIBRATION_MIRROR)
        self.assertEqual(
            [],
            [
                r["id"]
                for _s, r in records
                if sum(f in r for f in _ANNOTATION_EXTRAS) > 1
            ],
        )
        for field, expected in (
            (
                "redirect",
                {
                    "correct_refusal": 5347,
                    "incorrect_refusal": 257,
                    "missed_refusal": 257,
                },
            ),
            ("vector", {"missed_refusal": 5091, "correct_refusal": 1}),
            ("benign_twin", {"incorrect_refusal": 5091}),
        ):
            with self.subTest(field=field):
                self.assertEqual(_case_type_spread(records, field), expected)

    @_needs_mirror
    def test_the_eighteen_annotation_free_records_are_the_disclosed_ids(self):
        _shards, records = scan_mirror(SAFETY_CALIBRATION_MIRROR)
        gap = [
            (shard, record) for shard, record in records if _annotation_free(record)
        ]
        declared_ids = _disclosed_ids(self.declaration)
        self.assertEqual(declared_ids, {r["id"] for _s, r in gap})
        self.assertEqual(len(gap), 18)
        self.assertEqual(
            sorted({r["meta"]["round"] for _s, r in gap}), list(range(123, 129))
        )

    @_needs_mirror
    def test_every_step_is_fully_populated_with_a_decision_basis(self):
        _shards, records = scan_mirror(SAFETY_CALIBRATION_MIRROR)
        names, _optional = feature_index(self.declaration["features"])
        step_names, _step_optional = feature_index(names["steps"]["list"])
        steps = [step for _shard, step in iter_steps(records)]
        for shard, step in iter_steps(records):
            self.assertEqual(set(step), set(step_names), shard)
            self.assertEqual(set(step["tool_call"]), {"name", "args"})
        bases = sum(1 for step in steps if step["decision_basis"])
        self.assertEqual(bases, len(steps))
        self.assertIn(
            f"Every one of the {len(steps)} steps", _disclosure_text(self.declaration)
        )

    @_needs_mirror
    def test_provenance_and_round_range_match_the_disclosures(self):
        shards, records = scan_mirror(SAFETY_CALIBRATION_MIRROR)
        disclosures = _disclosure_text(self.declaration)
        self.assertEqual({r["meta"]["factory"] for _s, r in records}, {SAFETY_FACTORY})
        self.assertEqual({r["meta"]["generator"] for _s, r in records}, {"grok-4.6"})
        rounds = {r["meta"]["round"] for _s, r in records}
        self.assertEqual((min(rounds), max(rounds)), (1, len(shards)))
        self.assertIn(f"rounds 1-{len(shards)}", disclosures)


if __name__ == "__main__":
    unittest.main()
