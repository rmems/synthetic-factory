#!/usr/bin/env python3
"""Shared surface for the per-dataset card-schema declaration tests.

Every ``tests/test_card_schema_issue_*.py`` leaf loads one declaration from
``config/card-schemas``, renders that dataset's Hub card through the publisher
and checks the same generic shapes before asserting what is particular to its
own payload. This module carries that common part once -- the ``sys.path``
bootstrap, the ``card_schema`` / ``publish_grok46_hub`` imports, the fixture
``setUp`` parameterised by dataset, issue and payload facts, and the checks
that recur verbatim across the leaves -- so a leaf subclasses
``DeclarationTestCase`` and keeps only its dataset-specific expectations.

Test discovery runs with ``-s tests``, so the leaves import this module by its
bare name, the same way the other ``*_test_support`` modules are reached.
"""

import json
import sys
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "pipelines"))
sys.path.insert(0, str(REPO / "scripts"))

import card_schema  # noqa: E402
import publish_grok46_hub as publisher  # noqa: E402

# The first dataset to use the mechanism (issue #36). Several leaves contrast
# their mandatory `plan` with the optional one declared there.
LONG_HORIZON = "long-horizon-coding-trajectories"

# The read-only published mirrors live outside the repository. Data-backed
# tests skip when a mirror is absent instead of fabricating a payload.
MIRROR_ROOT = Path.home() / "rmems" / "hf" / "grok-4.6"
MIRROR_MISSING = "read-only published mirror is not available"

DEFAULT_DATA_FILES = ["data/raw/batch-*.jsonl"]

# The episode record shape most trajectory dumps share.
EPISODE_FIELD_ORDER = ["id", "goal", "plan", "steps", "outcome", "reward", "meta"]
EPISODE_FIELDS = set(EPISODE_FIELD_ORDER)
STEP_FIELD_ORDER = ["n", "decision_basis", "tool_call", "observation", "reflection"]
STEP_FIELDS = set(STEP_FIELD_ORDER)
TOOL_CALL_FIELDS = {"name", "args"}
EPISODE_JSON_COLUMNS = ["steps[].tool_call.args", "reward", "meta"]

# The annotation-free YAML projection of that step list.
STEPS_YAML_FEATURE = {
    "name": "steps",
    "list": [
        {"name": "n", "dtype": "int64"},
        {"name": "decision_basis", "dtype": "string"},
        {
            "name": "tool_call",
            "struct": [
                {"name": "name", "dtype": "string"},
                {"name": "args", "dtype": "json"},
            ],
        },
        {"name": "observation", "dtype": "string"},
        {"name": "reflection", "dtype": "string"},
    ],
}

# Front-matter fragments the rendered YAML carries.
CONFIGS_YAML = "configs:\n- config_name: default\n"
TRAIN_SPLIT_YAML = "  - split: train\n"
BATCH_GLOB_YAML = '    path: "data/raw/batch-*.jsonl"\n'
FEATURES_YAML = "dataset_info:\n  features:\n"
META_JSON_YAML = "  - name: meta\n    dtype: json\n"
REWARD_JSON_YAML = "  - name: reward\n    dtype: json\n"
PLAN_STRING_YAML = "  - name: plan\n    dtype: string\n"
ARGS_JSON_YAML = "      - name: args\n        dtype: json\n"
# Bare `n` is a YAML 1.1 boolean, so the step index must stay quoted.
QUOTED_N_YAML = '    - name: "n"\n      dtype: int64\n'
LICENSE_YAML = "license: apache-2.0"

# Card-body fragments.
VIEWER_SCHEMA_HEADING = "## Dataset viewer schema"
DISCLOSURES_HEADING = "### Known payload disclosures"
NOT_DECLARED = "**Not declared yet.**"
NOT_TRAINING_READY = "**not training-ready**"
REFLECTION_OPTIONAL_ROW = "| `steps[].reflection` | optional |"
PLAN_OPTIONAL_ROW = "| `plan` | optional |"
PLAN_PRESENT_ROW = "| `plan` | present on every record |"
NO_FOREIGN_PAYLOAD = "no dest-stamped foreign payload"


def by_name(features):
    """Index a feature list by ``name``."""
    return {feature["name"]: feature for feature in features}


def feature_names(features):
    """The feature names of one level, in declaration order."""
    return [feature["name"] for feature in features]


def feature_index(features):
    """Split a feature list into a name lookup and the set of optional names."""
    names = by_name(features)
    return names, {name for name, feature in names.items() if feature.get("optional")}


def iter_steps(records):
    """Yield every (shard, step) pair, flattening the record/step nesting."""
    for shard, record in records:
        for step in record["steps"]:
            yield shard, step


def bag_key_counts(records, bag):
    """Count how many records carry each key of a free-form bag."""
    seen = {}
    for _shard, record in records:
        for key in record[bag]:
            seen[key] = seen.get(key, 0) + 1
    return seen


def mirror_path(dataset):
    """The raw payload directory of one dataset's read-only published mirror."""
    return MIRROR_ROOT / dataset / "data" / "raw"


def needs_mirror(mirror):
    """Skip a data-backed test while the published mirror is not mounted."""
    return unittest.skipUnless(mirror.is_dir(), MIRROR_MISSING)


def read_shard(shard):
    """Every non-blank record in one shard, tagged with the shard name."""
    with shard.open(encoding="utf-8") as handle:
        return [(shard.name, json.loads(line)) for line in handle if line.strip()]


_SCANS: dict = {}


def scan_mirror(mirror):
    """Every ``batch-*.jsonl`` shard of a mirror and its tagged rows, read once."""
    if mirror not in _SCANS:
        shards = sorted(mirror.glob("batch-*.jsonl"))
        _SCANS[mirror] = (shards, [row for shard in shards for row in read_shard(shard)])
    return _SCANS[mirror]


class DeclarationTestCase(unittest.TestCase):
    """One dataset's declaration and rendered card, plus the checks every leaf shares.

    A leaf sets ``DATASET``, ``ISSUE``, ``HUB_ITEM`` and ``SUMMARY``. ``setUp``
    loads the declaration, fails naming the issue when it is missing, and
    renders the card through the publisher's ``summary=`` surface, which the
    publisher keeps byte-identical to the legacy keyword surface.
    """

    DATASET = ""
    ISSUE = 0
    # Set when the missing-declaration message must name a PR as well.
    MISSING_MESSAGE = None
    HUB_ITEM: dict = {}
    SUMMARY = None

    def setUp(self):
        self.declaration = card_schema.load(self.DATASET)
        self.assertIsNotNone(self.declaration, self.missing_declaration_message())
        self.item = dict(self.HUB_ITEM)
        self.card = self.render_card(self.SUMMARY)

    def missing_declaration_message(self):
        """What the leaf reports when ``config/card-schemas`` lacks its file."""
        return self.MISSING_MESSAGE or f"config/card-schemas is missing #{self.ISSUE}"

    def render_card(self, summary):
        """Render this dataset's card for one ``PayloadSummary``."""
        return publisher.render_card(self.item, summary=summary)

    # -- declaration lookups -----------------------------------------------

    def names(self):
        """Top-level features by name."""
        return by_name(self.declaration["features"])

    def feature(self, name):
        """The top-level feature called ``name``."""
        return self.names()[name]

    def step_features(self, names):
        """The step-list features by name."""
        return by_name(names["steps"]["list"])

    def tool_call_features(self, steps):
        """The ``tool_call`` struct features by name."""
        return by_name(steps["tool_call"]["struct"])

    def front_matter(self):
        """The YAML block between the card's first two ``---`` fences."""
        return self.card.split("---", 2)[1]

    # -- assertions shared by the leaves ------------------------------------

    def assert_json_columns(self, expected):
        """Exactly ``expected`` columns are declared ``json``, in order."""
        self.assertEqual(card_schema.json_columns(self.declaration["features"]), expected)

    def assert_episode_steps(self, names, reflection_note=None):
        """The shared step list: only `reflection` optional, `args` a json bag."""
        steps = self.step_features(names)
        self.assertEqual(set(steps), STEP_FIELDS)
        self.assertTrue(steps["reflection"]["optional"])
        if reflection_note is not None:
            self.assertIn(reflection_note, steps["reflection"]["note"])
        tool_call = self.tool_call_features(steps)
        self.assertEqual(tool_call["args"]["dtype"], "json")
        return steps, tool_call

    def assert_episode_union(self, reflection_note=None):
        """The plain episode record: seven columns, a mandatory string `plan`,
        `reward` and `meta` key bags, the shared step list, and this issue.

        Returns the top-level, step and ``tool_call`` feature indexes so a leaf
        can add what is particular to its own payload.
        """
        names = self.names()
        self.assertEqual(set(names), EPISODE_FIELDS)
        self.assertNotIn("optional", names["plan"])
        self.assertEqual(names["plan"]["dtype"], "string")
        self.assertEqual(names["meta"]["dtype"], "json")
        self.assertEqual(names["reward"]["dtype"], "json")
        steps, tool_call = self.assert_episode_steps(names, reflection_note)
        self.assertEqual(self.declaration["issues"], [self.ISSUE])
        return names, steps, tool_call

    def assert_steps_carry_declared_fields(self, records, names):
        """Every published step carries exactly the declared step fields."""
        step_names, step_optional = feature_index(names["steps"]["list"])
        for shard, step in iter_steps(records):
            self.assertEqual(set(step) - set(step_names), set(), shard)
            self.assertEqual(set(step_names) - set(step) - step_optional, set(), shard)
            self.assertEqual(set(step["tool_call"]), TOOL_CALL_FIELDS)

    def assert_front_matter_declares_default_config(self, *fragments, absent=()):
        """The default config over raw batches, plus each leaf's own fragments.

        Card-only annotations are passed through ``absent`` so they never reach
        the feature YAML. Returns the front matter for any further checks.
        """
        front_matter = self.front_matter()
        self.assertIn(CONFIGS_YAML, front_matter)
        self.assertIn(BATCH_GLOB_YAML, front_matter)
        for fragment in fragments:
            self.assertIn(fragment, front_matter)
        for fragment in absent:
            self.assertNotIn(fragment, front_matter)
        # license/tags/status claims stay exactly where they were.
        self.assertIn(LICENSE_YAML, front_matter)
        self.assertIn(NOT_TRAINING_READY, self.card)
        return front_matter

    def assert_card_has(self, *fragments):
        """Every fragment appears somewhere on the rendered card."""
        for fragment in fragments:
            self.assertIn(fragment, self.card)

    def assert_card_lacks(self, *fragments):
        """No fragment appears anywhere on the rendered card."""
        for fragment in fragments:
            self.assertNotIn(fragment, self.card)

    def assert_card_names_records(self, record_ids):
        """Each record id is named on the card, as inline code."""
        for record_id in record_ids:
            with self.subTest(record_id=record_id):
                self.assertIn(f"`{record_id}`", self.card)
