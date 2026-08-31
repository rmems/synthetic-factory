#!/usr/bin/env python3
"""Issue #68 leaf tests for the per-dataset card schema declaration."""

try:
    # The shared card-schema test module was renamed on the stack's shared
    # infrastructure branch (`test_card_schema` -> `test_card_schema_integration`)
    # after this branch was cut. Prefer the new name so this leaf still imports
    # on the post-merge tree, where the old monolith no longer exists; fall back
    # to the old name, which is what this branch's own history carries today.
    import test_card_schema_integration as _shared
except ModuleNotFoundError:
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


K8S_CRASHLOOP = "k8s-crashloop-trajectories"


class K8sCrashloopDeclarationTests(unittest.TestCase):
    """Issue #68: thin `meta` vs the late `designed` / `plant` / `kind` records.

    Every count asserted here was derived from the published mirror
    (1643 shards, 3286 records, 55903 steps), not copied from the issue text.
    """

    MILL_IDS = (
        "gql-r1330-edgedb-globals-after-access-policy",
        "gql-r1330-edgedb-drop-session-globals",
        "gql-r1331-prisma-preview-client-after-generate",
        "gql-r1331-prisma-disable-preview-flags",
        "gql-r1332-gqlgen-gofield-after-bind-rename",
        "gql-r1332-gqlgen-drop-field-bind",
        "gql-r1333-juniper-field-with-after-executor",
        "gql-r1333-juniper-drop-executor-with",
        "gql-r1334-async-graphql-guard-after-complexity",
        "gql-r1334-async-graphql-disable-field-guard",
        "gql-r1335-absinthe-pipeline-after-phase-swap",
        "gql-r1335-absinthe-drop-pipeline-phase",
    )
    DESIGNED_PLANT_IDS = (
        "kcl-r1336-deploy-termination-grace-0-be0a",
        "kcl-r1336-deploy-startup-probe-fail-1-ed58",
        "kcl-r1337-deploy-share-process-namespace-332f",
        "kcl-r1337-deploy-fs-group-change-policy-df26",
        "kcl-r1338-sts-pod-management-parallel-0394",
        "kcl-r1338-cronjob-concurrency-forbid-b46b",
    )

    def setUp(self):
        self.declaration = card_schema.load(K8S_CRASHLOOP)
        self.assertIsNotNone(self.declaration, "config/card-schemas is missing #68")
        self.item = {
            "slug": "k8s-crashloop-factory",
            "hub": K8S_CRASHLOOP,
            "pretty": "K8S Crashloop Trajectories",
            "blurb": "Kubernetes CrashLoop leftover-field episodes.",
            "tags": ["synthetic-data", "kubernetes"],
        }
        self.card = publisher.render_card(
            self.item,
            records=3286,
            bytes_=27423440,
            first="r01",
            last="r1643",
            payload_names=["batch-r01.jsonl", "batch-r1330.jsonl", "batch-r1643.jsonl"],
        )

    def test_declaration_matches_the_observed_union_schema(self):
        names = {feature["name"]: feature for feature in self.declaration["features"]}
        self.assertEqual(
            set(names),
            {"id", "goal", "plan", "steps", "outcome", "reward", "meta"},
        )
        self.assertEqual(self.declaration["issues"], [68])
        for scalar in ("id", "goal", "plan", "outcome"):
            with self.subTest(scalar=scalar):
                self.assertEqual(names[scalar]["dtype"], "string")
                self.assertNotIn("optional", names[scalar])
        self.assertEqual(names["meta"]["dtype"], "json")
        self.assertEqual(names["reward"]["dtype"], "json")
        self.assertIn("list", names["steps"])
        self.assertNotIn("dtype", names["steps"])
        steps = {feature["name"]: feature for feature in names["steps"]["list"]}
        self.assertEqual(
            set(steps), {"n", "decision_basis", "tool_call", "observation", "reflection"}
        )
        self.assertEqual(steps["n"]["dtype"], "int64")
        for scalar in ("decision_basis", "observation", "reflection"):
            with self.subTest(step_scalar=scalar):
                self.assertEqual(steps[scalar]["dtype"], "string")
        self.assertTrue(steps["reflection"]["optional"])
        self.assertIn("struct", steps["tool_call"])
        self.assertNotIn("dtype", steps["tool_call"])
        tool_call = {feature["name"]: feature for feature in steps["tool_call"]["struct"]}
        self.assertEqual(set(tool_call), {"name", "args"})
        self.assertEqual(tool_call["name"]["dtype"], "string")
        self.assertEqual(tool_call["args"]["dtype"], "json")

    def test_plan_is_mandatory_here_unlike_the_worked_example(self):
        # `plan` is a string on all 3286 records in this dump. Copying the
        # optional `plan` of #36 would publish a claim the payload denies.
        plan = next(
            feature
            for feature in self.declaration["features"]
            if feature["name"] == "plan"
        )
        self.assertEqual(plan["dtype"], "string")
        self.assertNotIn("optional", plan)
        self.assertIn("| `plan` | present on every record |", self.card)

    def test_key_bag_columns_are_declared_json(self):
        self.assertEqual(
            card_schema.json_columns(self.declaration["features"]),
            ["steps[].tool_call.args", "reward", "meta"],
        )

    def test_card_front_matter_declares_the_default_config_over_raw_batches(self):
        front_matter = self.card.split("---", 2)[1]
        self.assertIn("configs:\n- config_name: default\n", front_matter)
        self.assertIn("  - split: train\n", front_matter)
        self.assertIn('    path: "data/raw/batch-*.jsonl"\n', front_matter)
        self.assertIn("dataset_info:\n  features:\n", front_matter)
        self.assertIn("  - name: meta\n    dtype: json\n", front_matter)
        self.assertIn("  - name: reward\n    dtype: json\n", front_matter)
        self.assertIn("      - name: args\n        dtype: json\n", front_matter)
        # Card-only annotations must never be read back as a feature type.
        self.assertNotIn("optional", front_matter)
        self.assertNotIn("note:", front_matter)
        # license/tags/status claims stay exactly where they were.
        self.assertIn("license: apache-2.0", front_matter)
        self.assertIn("**not training-ready**", self.card)

    def test_card_body_owns_the_dest_stamped_mill_rows_without_re_filing_them(self):
        self.assertIn("## Dataset viewer schema", self.card)
        self.assertIn("### Known payload disclosures", self.card)
        for record_id in self.MILL_IDS:
            with self.subTest(record_id=record_id):
                self.assertIn(f"`{record_id}`", self.card)
        # The 12 rows are attributed to the frozen census in #44, not re-filed.
        self.assertIn("issues/44", self.card)

    def test_card_body_keeps_the_designed_plant_outlier_with_this_issue(self):
        for record_id in self.DESIGNED_PLANT_IDS:
            with self.subTest(record_id=record_id):
                self.assertIn(f"`{record_id}`", self.card)
        self.assertIn("run_terminal_command", self.card)
        self.assertNotIn("issues/43", self.card)

    def test_card_body_separates_the_own_leftover_mechanic_from_the_mill(self):
        self.assertIn("791 of the 3274 `kcl-*` records", self.card)
        self.assertIn("803 leftover-in-goal", self.card)
        self.assertIn("| `steps[].reflection` | optional |", self.card)
        self.assertNotIn("**Not declared yet.**", self.card)


if __name__ == "__main__":
    unittest.main()
