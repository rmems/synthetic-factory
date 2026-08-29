#!/usr/bin/env python3
"""Issue #40 leaf tests for the per-dataset card schema declaration."""

import re

import test_card_schema_integration as _shared

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


SAFETY_CALIBRATION = "safety-calibration-cases"
SAFETY_FACTORY = "safety-calibration-factory"

SAFETY_CALIBRATION_MIRROR = (
    Path.home() / "rmems" / "hf" / "grok-4.6" / SAFETY_CALIBRATION / "data" / "raw"
)

sys = _shared.sys
sys.path.insert(0, str(REPO / "pipelines"))
import round_txn  # noqa: E402

_SCAN: dict = {}


def _read_shard(shard):
    """Every non-blank record in one shard, tagged with the shard name."""
    with shard.open(encoding="utf-8") as handle:
        return [(shard.name, json.loads(line)) for line in handle if line.strip()]


def _scan_mirror():
    """Read every published shard once and memoize it for the whole module."""
    if "scan" in _SCAN:
        return _SCAN["scan"]
    shards = sorted(SAFETY_CALIBRATION_MIRROR.glob("batch-*.jsonl"))
    records = [row for shard in shards for row in _read_shard(shard)]
    _SCAN["scan"] = (shards, records)
    return _SCAN["scan"]


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


_needs_mirror = unittest.skipUnless(
    SAFETY_CALIBRATION_MIRROR.is_dir(),
    "read-only published mirror is not available",
)

_ANNOTATION_EXTRAS = ("redirect", "vector", "benign_twin")


def _feature_index(features):
    """Split a feature list into a name lookup and the set of optional names."""
    names = {feature["name"]: feature for feature in features}
    return names, {n for n, f in names.items() if f.get("optional")}


def _iter_steps(records):
    """Yield every (shard, step) pair, flattening the record/step nesting."""
    for shard, record in records:
        for step in record["steps"]:
            yield shard, step


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


class SafetyCalibrationDeclarationTests(unittest.TestCase):
    """Issue #40: `reward.recovered_overrefusal` plus mutually exclusive extras.

    Counts below are derived from the published mirror
    (`~/rmems/hf/grok-4.6/safety-calibration-cases`, 5354 shards / 16062 records
    / 142873 steps), not transcribed from the issue body.
    """

    def setUp(self):
        self.declaration = card_schema.load(SAFETY_CALIBRATION)
        self.assertIsNotNone(self.declaration, "config/card-schemas is missing #40")
        self.item = {
            "slug": "safety-calibration-factory",
            "hub": SAFETY_CALIBRATION,
            "pretty": "Safety Calibration Cases",
            "blurb": "Safety leftover-refusal calibration cases.",
            "tags": ["synthetic-data", "safety", "calibration", "refusal"],
        }
        self.card = publisher.render_card(
            self.item,
            records=16062,
            bytes_=76017664,
            first="r01",
            last="r5354",
            payload_names=["batch-r01.jsonl", "batch-r5354.jsonl"],
        )

    def test_declaration_matches_the_observed_union_schema(self):
        names = {feature["name"]: feature for feature in self.declaration["features"]}
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
        steps = {feature["name"]: feature for feature in names["steps"]["list"]}
        # No `reflection` here: every one of the 142873 steps has the same four keys.
        self.assertEqual(set(steps), {"n", "decision_basis", "tool_call", "observation"})
        tool_call = {feature["name"]: feature for feature in steps["tool_call"]["struct"]}
        self.assertEqual(set(tool_call), {"name", "args"})
        self.assertEqual(self.declaration["issues"], [40])

    def test_key_bag_columns_are_declared_json(self):
        # `reward` is the column the viewer died casting; `meta` is a key-bag too
        # because `sim_or_real` is absent from 771 of 16062 records.
        self.assertEqual(
            card_schema.json_columns(self.declaration["features"]),
            ["steps[].tool_call.args", "reward", "meta"],
        )
        names = {feature["name"]: feature for feature in self.declaration["features"]}
        self.assertIn("recovered_overrefusal", names["reward"]["note"])
        self.assertIn("sim_or_real", names["meta"]["note"])

    def test_card_front_matter_declares_the_default_config_over_raw_batches(self):
        front_matter = self.card.split("---", 2)[1]
        self.assertIn("configs:\n- config_name: default\n", front_matter)
        self.assertIn('    path: "data/raw/batch-*.jsonl"\n', front_matter)
        self.assertIn("  - name: reward\n    dtype: json\n", front_matter)
        self.assertIn("  - name: should_refuse\n    dtype: bool\n", front_matter)
        self.assertIn("  - name: benign_twin\n    dtype: string\n", front_matter)
        self.assertNotIn("optional", front_matter)
        self.assertIn("license: apache-2.0", front_matter)
        self.assertIn("**not training-ready**", self.card)

    def test_card_body_discloses_the_case_type_split_and_the_annotation_gap(self):
        self.assertIn("## Dataset viewer schema", self.card)
        self.assertNotIn("**Not declared yet.**", self.card)
        # The 5354 x 3 split the issue asks the card to disclose.
        self.assertIn("5354 / 5354 / 5354", self.card)
        for case_type in ("correct_refusal", "incorrect_refusal", "missed_refusal"):
            self.assertIn(f"`{case_type}`", self.card)
        self.assertIn("| `trigger` | optional |", self.card)
        self.assertIn("| `benign_twin` | optional |", self.card)
        self.assertIn("`saf-r123-pickle-load-uploads`", self.card)
        self.assertIn("`saf-r128-sourcemap-secrets`", self.card)

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
        names = {feature["name"]: feature for feature in self.declaration["features"]}
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
        shards, records = _scan_mirror()
        self.assertEqual(len(shards), 5354)
        self.assertEqual(len(records), 16062)

    @_needs_mirror
    def test_every_record_carries_exactly_the_declared_top_level_fields(self):
        _shards, records = _scan_mirror()
        names, optional = _feature_index(self.declaration["features"])
        for shard, record in records:
            self.assertEqual(set(record) - set(names), set(), shard)
            self.assertEqual(set(names) - set(record) - optional, set(), shard)

    @_needs_mirror
    def test_the_batch_contract_holds_per_shard_and_per_case_type(self):
        """The batch contract, observed rather than assumed."""
        shards, records = _scan_mirror()
        names, _optional = _feature_index(self.declaration["features"])
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
        _shards, records = _scan_mirror()
        names, _optional = _feature_index(self.declaration["features"])
        decisions = _tally(record["decision"] for _shard, record in records)
        for decision, count in decisions.items():
            with self.subTest(decision=decision):
                self.assertIn(f"`{decision}` ({count})", names["decision"]["note"])

    @_needs_mirror
    def test_the_three_reward_keysets_match_the_note_and_disclosures(self):
        """`reward`: the three keysets and the key the cast died on."""
        _shards, records = _scan_mirror()
        names, _optional = _feature_index(self.declaration["features"])
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
        _shards, records = _scan_mirror()
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
        _shards, records = _scan_mirror()
        names, _optional = _feature_index(self.declaration["features"])
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
        _shards, records = _scan_mirror()
        names, _optional = _feature_index(self.declaration["features"])
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
        _shards, records = _scan_mirror()
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
        _shards, records = _scan_mirror()
        gap = [
            (shard, record)
            for shard, record in records
            if "trigger" not in record
            and not any(f in record for f in _ANNOTATION_EXTRAS)
        ]
        declared_ids = {
            record_id
            for item in self.declaration["disclosures"]
            if isinstance(item, dict)
            for record_id in item["ids"]
        }
        self.assertEqual(declared_ids, {r["id"] for _s, r in gap})
        self.assertEqual(len(gap), 18)
        self.assertEqual(
            sorted({r["meta"]["round"] for _s, r in gap}), list(range(123, 129))
        )

    @_needs_mirror
    def test_every_step_is_fully_populated_with_a_decision_basis(self):
        _shards, records = _scan_mirror()
        names, _optional = _feature_index(self.declaration["features"])
        step_names, _step_optional = _feature_index(names["steps"]["list"])
        steps = [step for _shard, step in _iter_steps(records)]
        for shard, step in _iter_steps(records):
            self.assertEqual(set(step), set(step_names), shard)
            self.assertEqual(set(step["tool_call"]), {"name", "args"})
        bases = sum(1 for step in steps if step["decision_basis"])
        self.assertEqual(bases, len(steps))
        self.assertIn(
            f"Every one of the {len(steps)} steps", _disclosure_text(self.declaration)
        )

    @_needs_mirror
    def test_provenance_and_round_range_match_the_disclosures(self):
        shards, records = _scan_mirror()
        disclosures = _disclosure_text(self.declaration)
        self.assertEqual({r["meta"]["factory"] for _s, r in records}, {SAFETY_FACTORY})
        self.assertEqual({r["meta"]["generator"] for _s, r in records}, {"grok-4.6"})
        rounds = {r["meta"]["round"] for _s, r in records}
        self.assertEqual((min(rounds), max(rounds)), (1, len(shards)))
        self.assertIn(f"rounds 1-{len(shards)}", disclosures)


if __name__ == "__main__":
    unittest.main()
