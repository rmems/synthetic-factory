#!/usr/bin/env python3
"""Issue #38 leaf tests for the per-dataset card schema declaration."""

import re

try:
    # The stack root (agent/hf-card-viewer-schema-infra, PR #91) renames the
    # shared module to test_card_schema_integration; that split reaches this
    # branch's merge result once the stack beneath (#100) carries it. A
    # checkout of this branch alone -- and its current base tip -- still has
    # the pre-split test_card_schema. Prefer the post-split name so the
    # post-split merge result works, and fall back so a bare checkout of this
    # branch collects and runs too.
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


def _read_shard(shard):
    """Every non-blank record in one shard, tagged with the shard name."""
    with shard.open(encoding="utf-8") as handle:
        return [(shard.name, json.loads(line)) for line in handle if line.strip()]


def _scan_mirror():
    """Read every published shard once and memoize it for the whole module."""
    if "scan" in _SCAN:
        return _SCAN["scan"]
    shards = sorted(CASCADING_MIRROR.glob("batch-*.jsonl"))
    records = [row for shard in shards for row in _read_shard(shard)]
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


_needs_mirror = unittest.skipUnless(
    CASCADING_MIRROR.is_dir(), "read-only published mirror is not available"
)

# The object shape each two-shape variant column takes when it is not a string.
OBJECT_FORMS = {
    "propagation": {"hops", "survived_steps", "mask", "first_symptom_step"},
    "diagnosis": {"step", "how_survived"},
    "recovery": {"step", "action"},
    "verification": {"step", "evidence"},
}


def _feature_index(features):
    """Split a feature list into a name lookup and the set of optional names."""
    names = {feature["name"]: feature for feature in features}
    return names, {n for n, f in names.items() if f.get("optional")}


def _iter_steps(records):
    """Yield every (record, step) pair, flattening the record/step nesting."""
    for _shard, record in records:
        for step in record["steps"]:
            yield record, step


def _ids_where(records, predicate):
    """The set of record ids whose record matches a predicate."""
    return {record["id"] for _shard, record in records if predicate(record)}


def _variant_column_values(records, field):
    """Every value one variant column takes across the payload."""
    return [record[field] for _shard, record in records if field in record]


def _variant_column_census(records, field):
    """Measure one variant column: value shapes, object keys, object count."""
    present = _variant_column_values(records, field)
    objects = [value for value in present if isinstance(value, dict)]
    shapes = {type(value).__name__ for value in present}
    object_keys = {key for value in objects for key in value}
    return shapes, object_keys, len(objects)


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
            summary=publisher.PayloadSummary(
                records=4722,
                bytes_=31062016,
                first="r01",
                last="r2361",
                names=["batch-r01.jsonl", "batch-r2021.jsonl"],
            ),
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
            self._assert_struct(value, feature["struct"], where)
        elif "list" in feature:
            self._assert_list(value, feature["list"], where)
        else:
            self._assert_scalar(value, feature, where)

    def _assert_children(self, mapping, children, where):
        """Each declared key is present and conforming, or declared optional."""
        self.assertEqual(set(mapping) - set(children), set(), where)
        for name, child in children.items():
            if name in mapping:
                self._assert_conforms(mapping[name], child, f"{where}.{name}")
            else:
                self.assertTrue(child.get("optional"), f"{where}.{name} missing")

    def _assert_struct(self, value, struct, where):
        self.assertIsInstance(value, dict, where)
        self._assert_children(value, {c["name"]: c for c in struct}, where)

    def _assert_list(self, value, item_features, where):
        self.assertIsInstance(value, list, where)
        children = {child["name"]: child for child in item_features}
        for index, element in enumerate(value):
            at = f"{where}[{index}]"
            self.assertIsInstance(element, dict, at)
            self._assert_children(element, children, at)

    def _assert_scalar(self, value, feature, where):
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

    @_needs_mirror
    def test_every_published_record_conforms_to_the_declared_union(self):
        """Walk every published record through the declared feature tree.

        The rest of this class checks the declaration against constants written
        beside it. This walks the payload itself, so a fourth shape outside the
        declared union -- a string `error_introduced`, a list `verification`, a
        step with an extra key, a new top-level field -- fails here, which is
        the exact viewer TypeError #38 exists to prevent.

        Deliberately expressed without snapshot totals: this factory is still
        producing rounds, so pinning record counts would break on every new
        round while saying nothing about the cast. The shape invariants checked
        here and below are what the cast actually depends on.
        """
        _shards, records = _scan_mirror()
        self.assertTrue(records)
        features, optional = _feature_index(self.declaration["features"])
        for shard, record in records:
            where = f"{shard}:{record['id']}"
            self.assertEqual(set(record) - set(features), set(), where)
            self.assertEqual(set(features) - set(record) - optional, set(), where)
            for name, feature in features.items():
                if name in record:
                    self._assert_conforms(record[name], feature, f"{where}.{name}")
            self._assert_two_shapes(record, f"{where}.")

    @_needs_mirror
    def test_each_variant_column_takes_exactly_two_declared_shapes(self):
        """The two-shape families the declaration was written for."""
        _shards, records = _scan_mirror()
        features, _optional = _feature_index(self.declaration["features"])
        for field in self.VARIANTS:
            shapes, object_keys, object_count = _variant_column_census(
                records, field
            )
            with self.subTest(field=field):
                # Exactly two shapes reach the column: string, or the one object.
                self.assertEqual(shapes, {"str", "dict"})
                self.assertEqual(object_keys, OBJECT_FORMS[field])
                self.assertEqual(object_count, 182)
                self.assertIn("an object", features[field]["note"])
                self.assertIn(f"on {object_count}", features[field]["note"])

    @_needs_mirror
    def test_the_object_family_is_the_same_records_in_all_four_columns(self):
        _shards, records = _scan_mirror()
        object_family = _ids_where(
            records, lambda r: isinstance(r.get("diagnosis"), dict)
        )
        for field in self.VARIANTS:
            with self.subTest(field=field, check="same family"):
                self.assertEqual(
                    _ids_where(records, lambda r, f=field: isinstance(r.get(f), dict)),
                    object_family,
                )
        self.assertEqual(len(object_family), 182)
        self.assertIn(
            f"`{{step, kind, description}}` on {len(object_family)}",
            self.declaration["note"],
        )

    @_needs_mirror
    def test_payload_and_description_are_strictly_mutually_exclusive(self):
        """That pair is what the inferred schema died on."""
        _shards, records = _scan_mirror()
        object_family = _ids_where(
            records, lambda r: isinstance(r.get("diagnosis"), dict)
        )
        reports = [
            r["error_introduced"] for _s, r in records if "error_introduced" in r
        ]
        self.assertTrue(reports)
        for report in reports:
            self.assertEqual(("payload" in report) + ("description" in report), 1)
        described = [r for r in reports if "description" in r]
        self.assertEqual(len(described), len(object_family))

    @_needs_mirror
    def test_the_disclosed_leftover_ids_are_the_records_without_a_report(self):
        """The disclosed eight-record set, derived rather than copied."""
        _shards, records = _scan_mirror()
        missing_report = _ids_where(records, lambda r: "error_introduced" not in r)
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

    @_needs_mirror
    def test_the_records_without_plan_are_a_different_disclosed_eight(self):
        _shards, records = _scan_mirror()
        missing_report = _ids_where(records, lambda r: "error_introduced" not in r)
        missing_plan = _ids_where(records, lambda r: "plan" not in r)
        # `card_schema.load` normalizes every disclosure to a dict, so the
        # prose lives under "summary" whether or not it carried ids.
        prose = " ".join(item["summary"] for item in self.declaration["disclosures"])
        self.assertEqual(missing_plan, set(re.findall(r"`(cer-[a-z0-9-]+)`", prose)))
        self.assertEqual(missing_plan & missing_report, set())
        self.assertEqual(len(missing_plan), 8)

    @_needs_mirror
    def test_steps_carry_no_hidden_reasoning_and_a_public_basis(self):
        _shards, records = _scan_mirror()
        features, _optional = _feature_index(self.declaration["features"])
        step_children, _step_optional = _feature_index(features["steps"]["list"])
        pairs = list(_iter_steps(records))
        for record, step in pairs:
            self.assertEqual(set(step) - set(step_children), set(), record["id"])
        bases = sum(1 for _record, step in pairs if step["decision_basis"])
        self.assertEqual(bases, len(pairs))
        self.assertEqual(
            {r["meta"]["factory"] for _s, r in records},
            {"cascading-error-recovery-factory"},
        )


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
