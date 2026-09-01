#!/usr/bin/env python3
"""Issue #37 leaf tests for the per-dataset card schema declaration."""

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


EXPECTED_FEATURE_MANIFEST = (
    ("id", "string", False),
    ("lesson_category", "string", True),
    ("goal", "string", True),
    ("outcome", "string", True),
    ("chosen", "struct", False),
    ("chosen.goal", "string", True),
    ("chosen.steps", "list", False),
    ("chosen.steps[].n", "int64", False),
    ("chosen.steps[].decision_basis", "string", False),
    ("chosen.steps[].tool_call", "struct", False),
    ("chosen.steps[].tool_call.name", "string", False),
    ("chosen.steps[].tool_call.args", "json", False),
    ("chosen.steps[].observation", "string", False),
    ("chosen.steps[].reflection", "string", True),
    ("chosen.outcome", "string", False),
    ("chosen.reward", "json", False),
    ("rejected", "struct", False),
    ("rejected.goal", "string", True),
    ("rejected.steps", "list", False),
    ("rejected.steps[].n", "int64", False),
    ("rejected.steps[].decision_basis", "string", False),
    ("rejected.steps[].tool_call", "struct", False),
    ("rejected.steps[].tool_call.name", "string", False),
    ("rejected.steps[].tool_call.args", "json", False),
    ("rejected.steps[].observation", "string", False),
    ("rejected.steps[].reflection", "string", True),
    ("rejected.outcome", "string", False),
    ("rejected.reward", "json", False),
    ("critique", "string", False),
    ("reward", "json", False),
    ("meta", "json", False),
)


def _walk_features(features, prefix):
    """Yield (path, encoding-or-dtype, optional) rows in declaration order."""
    child_prefixes = {"list": "{path}[].", "struct": "{path}."}
    for feature in features:
        path = f"{prefix}{feature['name']}"
        encodings = [key for key in ("dtype", "list", "struct") if key in feature]
        if len(encodings) != 1:
            raise AssertionError(f"{path} has {len(encodings)} feature encodings")
        encoding = encodings[0]
        yield (
            path,
            feature[encoding] if encoding == "dtype" else encoding,
            feature.get("optional", False),
        )
        if encoding in child_prefixes:
            child_prefix = child_prefixes[encoding].format(path=path)
            yield from _walk_features(feature[encoding], child_prefix)


def feature_manifest(features, prefix=""):
    """Flatten a declaration without consulting the independent expected manifest."""
    return tuple(_walk_features(features, prefix))


class ToolUsePreferenceDeclarationTests(unittest.TestCase):
    """Issue #37: a preference triple whose steps are nested one branch deep.

    Unlike #36 the step struct is not a top-level column: `chosen` and
    `rejected` each carry their own `steps` / `outcome` / `reward`, so the
    union has to be declared twice and `reward` exists at two levels with two
    different key bags. The top-level union spans the published mirror (6192
    records, 147471 steps) and the current producer contract.
    """

    DATASET = "tool-use-preference-pairs"
    STEP_FIELDS = {"n", "decision_basis", "tool_call", "observation", "reflection"}

    def setUp(self):
        self.declaration = card_schema.load(self.DATASET)
        self.assertIsNotNone(self.declaration, "config/card-schemas is missing #37")
        self.item = {
            "slug": "tool-use-preference-factory",
            "hub": self.DATASET,
            "pretty": "Tool Use Preference Pairs",
            "blurb": "Tool-use leftover-fork chosen/rejected preference pairs.",
            "tags": ["synthetic-data", "preference-data"],
        }
        self.card = publisher.render_card(
            self.item,
            records=6192,
            bytes_=55617283,
            first="r01",
            last="r2064",
            payload_names=["batch-r01.jsonl", "batch-r2064.jsonl"],
        )

    @staticmethod
    def _by_name(features):
        return {feature["name"]: feature for feature in features}

    def test_complete_feature_manifest_matches_the_independent_contract_scan(self):
        # This oracle is intentionally separate from the declaration: it combines
        # the read-only published-data census with the current producer contract,
        # so omitted paths, wrong fixed dtypes, and incorrect optional flags fail.
        self.assertEqual(feature_manifest(self.declaration["features"]), EXPECTED_FEATURE_MANIFEST)

    def test_declaration_matches_the_published_and_producer_union_schema(self):
        names = self._by_name(self.declaration["features"])
        self.assertEqual(
            set(names),
            {
                "id",
                "lesson_category",
                "goal",
                "outcome",
                "chosen",
                "rejected",
                "critique",
                "reward",
                "meta",
            },
        )
        # Historical rows omit lesson_category; current rows omit the historical
        # record-level outcome and may move the shared goal into both branches.
        self.assertEqual(
            [name for name, feature in names.items() if feature.get("optional")],
            ["lesson_category", "goal", "outcome"],
        )
        self.assertEqual(names["lesson_category"]["dtype"], "string")
        self.assertEqual(names["goal"]["dtype"], "string")
        self.assertEqual(names["outcome"]["dtype"], "string")
        self.assertEqual(names["reward"]["dtype"], "json")
        self.assertEqual(names["meta"]["dtype"], "json")
        self.assertEqual(self.declaration["issues"], [37])

    def test_both_branches_declare_the_same_nested_step_union(self):
        names = self._by_name(self.declaration["features"])
        for side in ("chosen", "rejected"):
            branch = self._by_name(names[side]["struct"])
            self.assertEqual(set(branch), {"goal", "steps", "outcome", "reward"}, side)
            self.assertEqual(branch["goal"]["dtype"], "string", side)
            self.assertTrue(branch["goal"]["optional"], side)
            self.assertEqual(branch["outcome"]["dtype"], "string", side)
            # The per-branch reward is its own key bag, not the record-level one.
            self.assertEqual(branch["reward"]["dtype"], "json", side)
            steps = self._by_name(branch["steps"]["list"])
            self.assertEqual(set(steps), self.STEP_FIELDS, side)
            self.assertEqual(steps["n"]["dtype"], "int64", side)
            self.assertTrue(steps["reflection"]["optional"], side)
            tool_call = self._by_name(steps["tool_call"]["struct"])
            self.assertEqual(set(tool_call), {"name", "args"}, side)
            self.assertEqual(tool_call["name"]["dtype"], "string", side)
            # Heterogeneous `body` values are why args cannot be a struct.
            self.assertEqual(tool_call["args"]["dtype"], "json", side)

    def test_key_bag_columns_are_declared_json(self):
        self.assertEqual(
            card_schema.json_columns(self.declaration["features"]),
            [
                "chosen.steps[].tool_call.args",
                "chosen.reward",
                "rejected.steps[].tool_call.args",
                "rejected.reward",
                "reward",
                "meta",
            ],
        )

    def test_card_front_matter_declares_the_default_config_over_raw_batches(self):
        front_matter = self.card.split("---", 2)[1]
        self.assertIn("configs:\n- config_name: default\n", front_matter)
        self.assertIn('    path: "data/raw/batch-*.jsonl"\n', front_matter)
        self.assertIn("dataset_info:\n  features:\n", front_matter)
        self.assertIn("  - name: lesson_category\n    dtype: string\n", front_matter)
        self.assertIn("  - name: outcome\n    dtype: string\n", front_matter)
        self.assertEqual(front_matter.count("- name: goal\n"), 3)
        # The two fields the datasets-server could not cast, once per branch.
        self.assertEqual(front_matter.count("      - name: reflection\n        dtype: string\n"), 2)
        self.assertEqual(front_matter.count("        - name: args\n          dtype: json\n"), 2)
        # Bare `n` is a YAML 1.1 boolean, so the step index must stay quoted.
        self.assertIn('      - name: "n"\n        dtype: int64\n', front_matter)
        # Card-only annotations never reach the feature encoding.
        self.assertNotIn("optional:", front_matter)
        self.assertNotIn("note:", front_matter)
        # license/tags/status claims stay exactly where they were.
        self.assertIn("license: apache-2.0", front_matter)
        self.assertIn("**not training-ready**", self.card)

    def test_card_body_documents_the_optional_reflection_and_empty_args(self):
        self.assertIn("## Dataset viewer schema", self.card)
        self.assertIn(
            "| `chosen.steps[].reflection` | optional | present on 55556 of 73741", self.card
        )
        self.assertIn(
            "| `rejected.steps[].reflection` | optional | present on 57153 of 73730",
            self.card,
        )
        self.assertIn("`chosen.steps[].tool_call.args`", self.card)
        self.assertIn("`rejected.steps[].tool_call.args`", self.card)
        self.assertIn("| `lesson_category` | optional |", self.card)
        self.assertIn("| `goal` | optional |", self.card)
        self.assertIn("| `outcome` | optional |", self.card)
        self.assertIn("| `chosen.goal` | optional |", self.card)
        self.assertIn("| `rejected.goal` | optional |", self.card)
        for record_id in (
            "tup-r03-diatool-slot-fill",
            "tup-r03-diatool-oos-reject",
            "tup-r08-diatool-redundant-slot",
        ):
            self.assertIn(f"`{record_id}`", self.card)
        self.assertIn("no leftover-mill mix", self.card)
        self.assertIn("Current valid batches require a non-empty `lesson_category`", self.card)
        self.assertNotIn("**Not declared yet.**", self.card)


if __name__ == "__main__":
    unittest.main()
