#!/usr/bin/env python3
"""Issue #38 leaf tests for the per-dataset card schema declaration."""

import re

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


CASCADING = "cascading-error-recovery-trajectories"

CASCADING_MIRROR = (
    Path.home() / "rmems" / "hf" / "grok-4.6" / CASCADING / "data" / "raw"
)

# What each declared dtype is allowed to be once decoded from JSONL. `json`
# is deliberately wide: it is the encoding chosen precisely because the column
# holds more than one shape.
DTYPE_TYPES = {
    "string": (str,),
    "int64": (int,),
    "bool": (bool,),
    "json": (str, int, float, bool, list, dict),
}

_SCAN: dict = {}


def _scan_mirror():
    """Read every published shard once and memoize it for the whole module."""
    if "scan" not in _SCAN:
        shards = sorted(CASCADING_MIRROR.glob("batch-*.jsonl"))
        records = []
        for shard in shards:
            with shard.open(encoding="utf-8") as handle:
                for line in handle:
                    if line.strip():
                        records.append((shard.name, json.loads(line)))
        _SCAN["scan"] = (shards, records)
    return _SCAN["scan"]


CASCADING_LEFTOVER_IDS = (
    "dbc-r2021-containerd-content-lease-l3",
    "dbc-r2021-containerd-gc-root-label-l3",
    "dbc-r2022-crio-imagestore-pin-l3",
    "dbc-r2022-crio-overlay-merged-l3",
    "dbc-r2023-buildx-driver-opt-network-l3",
    "dbc-r2023-buildx-provenance-attest-l3",
    "dbc-r2024-bake-group-legacy-target-l3",
    "dbc-r2024-bake-hcl-cache-from-l3",
)


class CascadingErrorRecoveryDeclarationTests(unittest.TestCase):
    """Issue #38: the fault-report fields carry two shapes, so the cast fails.

    The counts asserted here were derived by scanning every published record in
    the read-only mirror at
    ``~/rmems/hf/grok-4.6/cascading-error-recovery-trajectories`` (4722 records
    across 2361 shards, 0 parse failures), not transcribed from the issue.
    """

    def setUp(self):
        self.declaration = card_schema.load(CASCADING)
        self.assertIsNotNone(self.declaration, "config/card-schemas is missing #38")
        self.item = {
            "slug": "cascading-error-recovery-factory",
            "hub": CASCADING,
            "pretty": "Cascading Error Recovery Trajectories",
            "blurb": "Cascading-error diagnosis and recovery (fault@4, multi-hop).",
            "tags": ["synthetic-data", "debugging", "recovery", "errors"],
        }
        self.card = publisher.render_card(
            self.item,
            records=4722,
            bytes_=31062016,
            first="r01",
            last="r2361",
            payload_names=["batch-r01.jsonl", "batch-r2021.jsonl"],
        )

    def test_declaration_matches_the_observed_union_schema(self):
        features = self.declaration["features"]
        self.assertEqual(
            [feature["name"] for feature in features],
            [
                "id",
                "goal",
                "plan",
                "error_introduced",
                "propagation",
                "diagnosis",
                "recovery",
                "verification",
                "steps",
                "outcome",
                "reward",
                "meta",
            ],
        )
        names = {feature["name"]: feature for feature in features}
        # Absent on the 8 leftover-mill rows (error_introduced/diagnosis) or on
        # the 2158-record family that publishes only a string diagnosis.
        for name in (
            "plan",
            "error_introduced",
            "propagation",
            "diagnosis",
            "recovery",
            "verification",
        ):
            with self.subTest(field=name):
                self.assertTrue(names[name]["optional"], f"{name} is not on every record")
        # String on the majority, object on the 182-record family: json is the
        # only encoding that survives both without an Arrow cast error.
        for name in ("propagation", "diagnosis", "recovery", "verification"):
            with self.subTest(field=name):
                self.assertEqual(names[name]["dtype"], "json")
        self.assertEqual(names["reward"]["dtype"], "json")
        self.assertEqual(names["meta"]["dtype"], "json")
        self.assertEqual(self.declaration["issues"], [38])

    def test_error_introduced_declares_both_payload_and_description(self):
        error_introduced = next(
            feature
            for feature in self.declaration["features"]
            if feature["name"] == "error_introduced"
        )
        children = {child["name"]: child for child in error_introduced["struct"]}
        self.assertEqual(set(children), {"step", "kind", "payload", "description"})
        self.assertEqual(children["step"]["dtype"], "int64")
        self.assertEqual(children["kind"]["dtype"], "string")
        # The viewer's TypeError was exactly this pair: struct<step, kind,
        # payload> could not cast to struct<step, kind, description>.
        self.assertTrue(children["payload"]["optional"])
        self.assertTrue(children["description"]["optional"])

    def test_steps_keep_the_public_decision_basis_and_a_json_arg_bag(self):
        steps = next(
            feature for feature in self.declaration["features"] if feature["name"] == "steps"
        )
        children = {child["name"]: child for child in steps["list"]}
        self.assertEqual(
            set(children), {"n", "decision_basis", "tool_call", "observation", "reflection"}
        )
        self.assertTrue(children["reflection"]["optional"])
        tool_call = {child["name"]: child for child in children["tool_call"]["struct"]}
        self.assertEqual(tool_call["args"]["dtype"], "json")

    def test_key_bag_and_variant_columns_are_declared_json(self):
        self.assertEqual(
            card_schema.json_columns(self.declaration["features"]),
            [
                "propagation",
                "diagnosis",
                "recovery",
                "verification",
                "steps[].tool_call.args",
                "reward",
                "meta",
            ],
        )

    def test_card_front_matter_declares_the_default_config_over_raw_batches(self):
        front_matter = self.card.split("---", 2)[1]
        self.assertIn("configs:\n- config_name: default\n", front_matter)
        self.assertIn('    path: "data/raw/batch-*.jsonl"\n', front_matter)
        self.assertIn("dataset_info:\n  features:\n", front_matter)
        self.assertIn("  - name: error_introduced\n    struct:\n", front_matter)
        self.assertIn("    - name: description\n      dtype: string\n", front_matter)
        self.assertIn("  - name: diagnosis\n    dtype: json\n", front_matter)
        # Card-only annotations must never be read back as a feature type.
        self.assertNotIn("optional", front_matter)
        # license/tags/status claims stay exactly where they were.
        self.assertIn("license: apache-2.0", front_matter)
        self.assertIn("**not training-ready**", self.card)

    def test_card_body_discloses_the_eight_leftover_mill_records(self):
        self.assertIn("## Dataset viewer schema", self.card)
        self.assertNotIn("**Not declared yet.**", self.card)
        self.assertIn("### Known payload disclosures", self.card)
        for record_id in CASCADING_LEFTOVER_IDS:
            with self.subTest(record_id=record_id):
                self.assertIn(f"`{record_id}`", self.card)
        self.assertIn("| `plan` | optional |", self.card)
        self.assertIn("| `error_introduced.description` | optional |", self.card)
        self.assertIn("| `steps[].reflection` | optional |", self.card)
        self.assertIn("issues/38", self.card)


    def _assert_conforms(self, value, feature, where):
        """Walk one value against one declared feature node.

        This is the check the declaration exists to guarantee: every published
        value must be encodable as the declared type, or the datasets-server
        cast fails and the viewer index is never built.
        """
        if "struct" in feature:
            self.assertIsInstance(value, dict, where)
            children = {child["name"]: child for child in feature["struct"]}
            self.assertEqual(set(value) - set(children), set(), where)
            for name, child in children.items():
                if name in value:
                    self._assert_conforms(value[name], child, f"{where}.{name}")
                else:
                    self.assertTrue(child.get("optional"), f"{where}.{name} missing")
            return
        if "list" in feature:
            self.assertIsInstance(value, list, where)
            children = {child["name"]: child for child in feature["list"]}
            for index, element in enumerate(value):
                self.assertIsInstance(element, dict, f"{where}[{index}]")
                self.assertEqual(set(element) - set(children), set(), f"{where}[{index}]")
                for name, child in children.items():
                    if name in element:
                        self._assert_conforms(
                            element[name], child, f"{where}[{index}].{name}"
                        )
                    else:
                        self.assertTrue(
                            child.get("optional"), f"{where}[{index}].{name} missing"
                        )
            return
        allowed = DTYPE_TYPES[feature["dtype"]]
        self.assertIsInstance(value, allowed, f"{where} is {type(value).__name__}")
        # `bool` is a subclass of `int`; an int64 column must not accept one.
        if feature["dtype"] == "int64":
            self.assertNotIsInstance(value, bool, where)

    def test_card_payload_prose_names_real_batch_shards(self):
        """The card must not advertise a shard name the publisher cannot emit.

        `batch_label` derives labels as `r{number:02d}`, and `snapshot_one`
        only fills `first`/`last` when every shard is named
        `batch-{label}.jsonl`, so a bare `01` renders `data/raw/batch-01.jsonl`
        -- a file that cannot exist.
        """
        printed = set(re.findall(r"data/raw/(batch-[0-9a-z]+\.jsonl)", self.card))
        self.assertIn("batch-r01.jsonl", printed)
        for name in printed:
            with self.subTest(name=name):
                label = publisher.batch_label(Path(name))
                self.assertIsNotNone(label, f"{name} is not a publishable shard name")
                self.assertEqual(f"batch-{label[2]}.jsonl", name)

    @unittest.skipUnless(
        CASCADING_MIRROR.is_dir(), "read-only published mirror is not available"
    )
    def test_every_published_record_conforms_to_the_declared_union(self):
        """Walk every published record through the declared feature tree.

        The rest of this class checks the declaration against constants written
        beside it. This walks the payload itself, so a fourth shape outside the
        declared union -- a string `error_introduced`, a list `verification`, a
        step with an extra key, a new top-level field -- fails here, which is
        the exact viewer TypeError #38 exists to prevent.

        Deliberately expressed without snapshot totals: this factory is still
        producing rounds, so pinning record counts would break on every new
        round while saying nothing about the cast. The shape invariants below
        are what the cast actually depends on.
        """
        shards, records = _scan_mirror()
        self.assertTrue(records)
        features = {f["name"]: f for f in self.declaration["features"]}
        optional = {n for n, f in features.items() if f.get("optional")}
        for shard, record in records:
            where = f"{shard}:{record['id']}"
            self.assertEqual(set(record) - set(features), set(), where)
            self.assertEqual(set(features) - set(record) - optional, set(), where)
            for name, feature in features.items():
                if name in record:
                    self._assert_conforms(record[name], feature, f"{where}.{name}")
            self._assert_two_shapes(record, f"{where}.")

        # --- The two-shape families the declaration was written for. ---
        variants = self.VARIANTS
        object_forms = {
            "propagation": {"hops", "survived_steps", "mask", "first_symptom_step"},
            "diagnosis": {"step", "how_survived"},
            "recovery": {"step", "action"},
            "verification": {"step", "evidence"},
        }
        for field in variants:
            present = [r for _s, r in records if field in r]
            objects = [r for r in present if isinstance(r[field], dict)]
            with self.subTest(field=field):
                # Exactly two shapes reach the column: string, or the one object.
                self.assertEqual(
                    {type(r[field]).__name__ for r in present}, {"str", "dict"}
                )
                self.assertEqual(
                    {key for obj in objects for key in obj[field]},
                    object_forms[field],
                )
                self.assertEqual(len(objects), 182)
                self.assertIn("an object", features[field]["note"])
                self.assertIn(f"on {len(objects)}", features[field]["note"])

        # The object family is one family: the same records in all four columns.
        object_family = {
            r["id"] for _s, r in records if isinstance(r.get("diagnosis"), dict)
        }
        for field in variants:
            with self.subTest(field=field, check="same family"):
                self.assertEqual(
                    {r["id"] for _s, r in records if isinstance(r.get(field), dict)},
                    object_family,
                )
        self.assertEqual(len(object_family), 182)
        self.assertIn(
            f"`{{step, kind, description}}` on {len(object_family)}",
            self.declaration["note"],
        )

        # `payload` and `description` are strictly mutually exclusive, which is
        # the pair the inferred schema died on.
        reports = [r["error_introduced"] for _s, r in records if "error_introduced" in r]
        self.assertTrue(reports)
        for report in reports:
            self.assertEqual(("payload" in report) + ("description" in report), 1)
        described = [r for r in reports if "description" in r]
        self.assertEqual(len(described), len(object_family))

        # --- The two disclosed eight-record sets, derived rather than copied. ---
        missing_report = {r["id"] for _s, r in records if "error_introduced" not in r}
        declared_leftover = {
            record_id
            for item in self.declaration["disclosures"]
            if isinstance(item, dict)
            for record_id in item["ids"]
        }
        self.assertEqual(declared_leftover, missing_report)
        self.assertEqual(declared_leftover, set(CASCADING_LEFTOVER_IDS))
        for _shard, record in records:
            if record["id"] in missing_report:
                for absent in ("diagnosis", "propagation", "recovery", "verification"):
                    self.assertNotIn(absent, record, record["id"])
                self.assertEqual(record["meta"]["kind"], "designed")

        # The 8 records without `plan` are a different 8, exactly as disclosed.
        missing_plan = {r["id"] for _s, r in records if "plan" not in r}
        # `card_schema.load` normalizes every disclosure to a dict, so the
        # prose lives under "summary" whether or not it carried ids.
        prose = " ".join(item["summary"] for item in self.declaration["disclosures"])
        self.assertEqual(missing_plan, set(re.findall(r"`(cer-[a-z0-9-]+)`", prose)))
        self.assertEqual(missing_plan & missing_report, set())
        self.assertEqual(len(missing_plan), 8)

        # --- Steps: no hidden reasoning, and a public basis on every step. ---
        step_children = {c["name"]: c for c in features["steps"]["list"]}
        total_steps = bases = 0
        for _shard, record in records:
            for step in record["steps"]:
                total_steps += 1
                bases += bool(step["decision_basis"])
                self.assertEqual(set(step) - set(step_children), set(), record["id"])
        self.assertEqual(bases, total_steps)
        self.assertEqual({r["meta"]["factory"] for _s, r in records},
                         {"cascading-error-recovery-factory"})


    # Three representative rows, one per published shape. Written here rather
    # than copied out of the mirror so the union check runs on CI, where the
    # read-only mirror is not mounted.
    STRING_FORM_ROW = {
        "id": "cer-r10-retry-storm-a1",
        "goal": "recover the cascade",
        "plan": "isolate, then roll back",
        "error_introduced": {"step": 4, "kind": "config", "payload": "ndots:5"},
        "propagation": "hop 4 -> 7",
        "diagnosis": "resolver retry storm",
        "recovery": "pin ndots",
        "verification": "suite green",
        "steps": [
            {
                "n": 1,
                "decision_basis": "read the resolver config",
                "tool_call": {"name": "read", "args": {"path": "/etc/resolv.conf"}},
                "observation": "ndots:5",
                "reflection": "that is the fault",
            }
        ],
        "outcome": "recovered",
        "reward": {"success": True, "cascade_steps": 3},
        "meta": {"factory": "cascading-error-recovery-factory", "generator": "grok-4.6", "round": 10},
    }

    OBJECT_FORM_ROW = {
        "id": "cer-r11-mask-survives-b2",
        "goal": "recover the cascade",
        "plan": "trace the mask",
        "error_introduced": {"step": 4, "kind": "logic", "description": "mask survives"},
        "propagation": {"hops": 3, "survived_steps": 2, "mask": "0o022", "first_symptom_step": 5},
        "diagnosis": {"step": 6, "how_survived": "umask inherited"},
        "recovery": {"step": 7, "action": "reset umask"},
        "verification": {"step": 8, "evidence": "perms 0644"},
        "steps": [
            {
                "n": 1,
                "decision_basis": "inspect the umask",
                "tool_call": {"name": "bash", "args": {"command": "umask"}},
                "observation": "0022",
            }
        ],
        "outcome": "recovered",
        "reward": {"success": True, "residual": 0},
        "meta": {"factory": "cascading-error-recovery-factory", "generator": "grok-4.6", "round": 11},
    }

    LEFTOVER_ROW = {
        "id": "dbc-r2021-containerd-content-lease-l3",
        "goal": "leftover content lease blocks the cache",
        "plan": "drop the stale lease",
        "steps": [
            {
                "n": 1,
                "decision_basis": "list the leases",
                "tool_call": {"name": "bash", "args": {"command": "ctr leases list"}},
                "observation": "one stale lease",
            }
        ],
        "outcome": "recovered",
        "reward": {"success": True},
        "meta": {
            "factory": "cascading-error-recovery-factory",
            "generator": "grok-4.6",
            "round": 2021,
            "kind": "designed",
            "product": "containerd",
            "mechanic": "content-lease",
        },
    }

    # The four fault-report columns the declaration was written for.
    VARIANTS = ("propagation", "diagnosis", "recovery", "verification")

    def _assert_two_shapes(self, record, where=""):
        """The variant columns hold a string or the one object, nothing else.

        `json` as a dtype would tolerate a list or a number, and such a value
        would not actually break the Arrow cast. It would still contradict the
        note that documents exactly two shapes, so it is checked separately
        from the dtype walk rather than folded into it.
        """
        for field in self.VARIANTS:
            if field in record:
                self.assertIsInstance(record[field], (str, dict), f"{where}{field}")

    def _walk_record(self, record):
        features = {f["name"]: f for f in self.declaration["features"]}
        optional = {n for n, f in features.items() if f.get("optional")}
        self.assertEqual(set(record) - set(features), set())
        self.assertEqual(set(features) - set(record) - optional, set())
        for name, feature in features.items():
            if name in record:
                self._assert_conforms(record[name], feature, name)
        self._assert_two_shapes(record)

    def test_representative_rows_walk_the_declared_feature_tree(self):
        """The declared union must accept all three published shapes."""
        for label, row in (
            ("string form with payload", self.STRING_FORM_ROW),
            ("object form with description", self.OBJECT_FORM_ROW),
            ("leftover-mill row", self.LEFTOVER_ROW),
        ):
            with self.subTest(row=label):
                self._walk_record(row)

    def test_a_shape_outside_the_declared_union_is_rejected(self):
        """The walk must fail on the shapes that would re-break the cast.

        Without these, the conformance check could silently accept anything and
        the mirror test would look green for the wrong reason.
        """
        def mutate(**changes):
            row = json.loads(json.dumps(self.STRING_FORM_ROW))
            for key, value in changes.items():
                if value is None:
                    row.pop(key)
                else:
                    row[key] = value
            return row

        deeper = json.loads(json.dumps(self.STRING_FORM_ROW))
        deeper["error_introduced"]["step"] = "four"
        extra_step = json.loads(json.dumps(self.STRING_FORM_ROW))
        extra_step["steps"][0]["thought"] = "hidden"
        extra_report = json.loads(json.dumps(self.STRING_FORM_ROW))
        extra_report["error_introduced"]["severity"] = "high"
        bad_bool = json.loads(json.dumps(self.STRING_FORM_ROW))
        bad_bool["error_introduced"]["step"] = True

        for label, row in (
            ("error_introduced as a string", mutate(error_introduced="config drift")),
            ("verification as a list", mutate(verification=["a", "b"])),
            ("a new top-level field", mutate(severity="high")),
            ("id as an int", mutate(id=7)),
            ("steps not a list", mutate(steps={"n": 1})),
            ("error_introduced.step as a string", deeper),
            ("a step with a hidden key", extra_step),
            ("an undeclared error_introduced key", extra_report),
            ("error_introduced.step as a bool", bad_bool),
        ):
            with self.subTest(row=label):
                with self.assertRaises(AssertionError):
                    self._walk_record(row)


if __name__ == "__main__":
    unittest.main()
