#!/usr/bin/env python3
"""Issue #46 leaf tests for the per-dataset card schema declaration."""

import hashlib

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


API_CONTRACT = "api-contract-migration-trajectories"
REPRESENTATIVE_FIXTURE = (
    REPO
    / "tests"
    / "fixtures"
    / "card-schema"
    / "api-contract-migration-trajectories.jsonl"
)
MIRROR = (
    Path.home()
    / "rmems"
    / "hf"
    / "grok-4.6"
    / API_CONTRACT
    / "data"
    / "raw"
)
PUBLISHED_PAYLOADS = [
    f"batch-r{round_number:02d}.jsonl" for round_number in range(1, 4007)
]
INVENTORY_SHA256 = "666f1809b7d1728e418aa7be0e1eb1953e752b24cdec926ab560f25eea293ac6"
REPRESENTATIVE_SOURCES = {
    "acm-r01-disc-wallet-map-b7e2": (
        "batch-r01.jsonl",
        1,
        "f5f423cecac086dabd503474d27fabf59c5c0303026c8b7479b4db63ca2ea153",
    ),
    "acm-r02-callback-hmac256-9b30": (
        "batch-r02.jsonl",
        2,
        "a2589c510d7c43023b14bef7f4532bdf7683d6d1b49839550424d2db4d1da5cf",
    ),
    "acm-r98-idem-header-sunset-7e19": (
        "batch-r98.jsonl",
        2,
        "5abe5ca94cc67124c1f2731e4d200cedd54c0aa970d9f91686e9eee7834f7b05",
    ),
    "acm-r03-createdAt-to-created-at": (
        "batch-r03.jsonl",
        1,
        "64a9665a3cb4873f12f17c5d08a1a8689a3d81c46909614321313f7d69594ab5",
    ),
    "acm-r839-b-path-param-rename-sao": (
        "batch-r839.jsonl",
        1,
        "ae3981aa1f515e2176e4f14a576a7007111058ca06b98b01aafa06a193fb0af6",
    ),
    "acm-r3561-json-schema-if-then-else-096a": (
        "batch-r3561.jsonl",
        1,
        "a2bcfcad6731c2325d6be51dd983b064bdf23c04814dc812ad318d8ae6abb76c",
    ),
    "dbc-r3714-buildkit-cache-mount-sharing-locked-leftover": (
        "batch-r3714.jsonl",
        2,
        "9e9fc165cae56aad9e2612d598a89f0a98c9af657dce42d3f80764a9d801de19",
    ),
}
THIN_META_LOCATIONS = [
    ("batch-r01.jsonl", 1, "acm-r01-disc-wallet-map-b7e2"),
    ("batch-r01.jsonl", 2, "acm-r01-orders-v2-email-req-4c91"),
    ("batch-r02.jsonl", 1, "acm-r02-addprop-reqid-a61e"),
    ("batch-r02.jsonl", 2, "acm-r02-callback-hmac256-9b30"),
    ("batch-r98.jsonl", 1, "acm-r98-oas31-null-phone-d4a2"),
    ("batch-r98.jsonl", 2, "acm-r98-idem-header-sunset-7e19"),
]
META_SHAPE_COUNTS = {
    (
        "designed",
        "domain",
        "factory",
        "generator",
        "kind",
        "lane",
        "round",
        "seed",
        "stack",
    ): 5440,
    ("domain", "factory", "generator", "round", "stack", "theme"): 1674,
    (
        "designed",
        "domain",
        "factory",
        "generator",
        "kind",
        "round",
        "seed",
        "stack",
    ): 890,
    ("factory", "generator", "round"): 6,
    ("factory", "generator", "kind", "mechanic", "product", "round"): 2,
}


def _fixture_rows() -> list[tuple[bytes, dict]]:
    rows = []
    for raw_line in REPRESENTATIVE_FIXTURE.read_bytes().splitlines(keepends=True):
        if raw_line.strip():
            rows.append((raw_line, json.loads(raw_line)))
    return rows


def _assert_scalar_matches(test_case, value, dtype: str, path: str) -> None:
    if dtype == "string":
        test_case.assertIs(type(value), str, path)
    elif dtype == "bool":
        test_case.assertIs(type(value), bool, path)
    elif dtype in {"int32", "int64"}:
        test_case.assertIs(type(value), int, path)
    elif dtype in {"float32", "float64"}:
        test_case.assertIn(type(value), {int, float}, path)
    else:
        test_case.assertEqual(dtype, "json", path)
        try:
            json.dumps(value, allow_nan=False)
        except (TypeError, ValueError) as exc:
            test_case.fail(f"{path} is not JSON-serializable: {exc}")


def _assert_value_matches(test_case, value, feature: dict, path: str) -> None:
    if "dtype" in feature:
        _assert_scalar_matches(test_case, value, feature["dtype"], path)
        return
    if "struct" in feature:
        _assert_object_matches(test_case, value, feature["struct"], path)
        return

    test_case.assertIs(type(value), list, path)
    child = feature["list"]
    for index, item in enumerate(value):
        item_path = f"{path}[{index}]"
        if isinstance(child, str):
            _assert_scalar_matches(test_case, item, child, item_path)
        else:
            _assert_object_matches(test_case, item, child, item_path)


def _assert_object_matches(test_case, value, features: list[dict], path: str) -> None:
    test_case.assertIs(type(value), dict, path)
    by_name = {feature["name"]: feature for feature in features}
    test_case.assertEqual(
        sorted(set(value) - set(by_name)),
        [],
        f"{path or '<record>'} has undeclared fields",
    )
    for name, feature in by_name.items():
        child_path = f"{path}.{name}" if path else name
        if name not in value:
            test_case.assertTrue(
                feature.get("optional", False),
                f"{child_path} is required but absent",
            )
            continue
        _assert_value_matches(test_case, value[name], feature, child_path)


class ApiContractMigrationDeclarationTests(unittest.TestCase):
    """Issue #46: leftover mill mix plus `meta` drift in the contract-migration dump.

    Counts come from a read-only scan of the published mirror
    ``~/rmems/hf/grok-4.6/api-contract-migration-trajectories``: 4006 shards,
    8012 records, 130021 steps, 0 parse failures.
    """

    def setUp(self):
        self.declaration = card_schema.load(API_CONTRACT)
        self.assertIsNotNone(self.declaration, "config/card-schemas is missing #46")
        self.item = {
            "slug": "api-contract-migration-factory",
            "hub": API_CONTRACT,
            "pretty": "Api Contract Migration Trajectories",
            "blurb": "OpenAPI / protocol leftover contract-migration episodes.",
            "tags": ["synthetic-data", "trajectories", "openapi"],
        }
        self.card = publisher.render_card(
            self.item,
            records=8012,
            bytes_=78346988,
            first="r01",
            last="r4006",
            payload_names=PUBLISHED_PAYLOADS,
        )

    def test_declaration_matches_the_observed_union_schema(self):
        names = {feature["name"]: feature for feature in self.declaration["features"]}
        self.assertEqual(
            set(names),
            {"id", "goal", "plan", "steps", "outcome", "reward", "meta"},
        )
        # Unlike long-horizon-coding, every one of the 8012 records carries a
        # `plan`, so it is declared present rather than optional.
        self.assertNotIn("optional", names["plan"])
        self.assertEqual(names["meta"]["dtype"], "json")
        self.assertEqual(names["reward"]["dtype"], "json")
        steps = {feature["name"]: feature for feature in names["steps"]["list"]}
        self.assertEqual(
            set(steps), {"n", "decision_basis", "tool_call", "observation", "reflection"}
        )
        self.assertTrue(steps["reflection"]["optional"])
        self.assertIn("129909 of 130021 steps", steps["reflection"]["note"])
        tool_call = {feature["name"]: feature for feature in steps["tool_call"]["struct"]}
        self.assertEqual(tool_call["args"]["dtype"], "json")
        self.assertEqual(self.declaration["issues"], [46])

    def test_key_bag_columns_are_declared_json(self):
        self.assertEqual(
            card_schema.json_columns(self.declaration["features"]),
            ["steps[].tool_call.args", "reward", "meta"],
        )

    def test_meta_notes_pin_thin_locations_and_seed_count(self):
        note = self.declaration["note"]
        self.assertIn("two records in `batch-r01.jsonl`", note)
        self.assertIn("four more thin-meta records", note)
        self.assertIn("`batch-r02.jsonl`", note)
        self.assertIn("`batch-r98.jsonl`", note)
        meta = next(
            feature
            for feature in self.declaration["features"]
            if feature["name"] == "meta"
        )
        self.assertIn("`seed` (6330)", meta["note"])

    def test_reward_note_names_every_extra_key_found_in_the_payload(self):
        reward = next(
            feature
            for feature in self.declaration["features"]
            if feature["name"] == "reward"
        )
        # The issue body listed only breaking_oasdiff / xfailed / handoff; the
        # mirror also carries a single `skipped`.
        for key in ("breaking_oasdiff", "xfailed", "skipped", "handoff"):
            with self.subTest(key=key):
                self.assertIn(f"`{key}`", reward["note"])

    def test_card_front_matter_declares_the_default_config_over_raw_batches(self):
        front_matter = self.card.split("---", 2)[1]
        self.assertIn("configs:\n- config_name: default\n", front_matter)
        self.assertIn('    path: "data/raw/batch-*.jsonl"\n', front_matter)
        self.assertIn("dataset_info:\n  features:\n", front_matter)
        self.assertIn("  - name: meta\n    dtype: json\n", front_matter)
        self.assertIn("  - name: reward\n    dtype: json\n", front_matter)
        self.assertIn("license: apache-2.0", front_matter)
        self.assertIn("**not training-ready**", self.card)

    def test_card_reports_the_full_r01_through_r4006_range(self):
        self.assertIn(
            "`data/raw/batch-r01.jsonl` through `data/raw/batch-r4006.jsonl`",
            self.card,
        )
        self.assertNotIn(
            "through `data/raw/batch-r999.jsonl`",
            self.card,
        )

    def test_card_body_discloses_the_two_leftover_mill_records(self):
        self.assertIn("## Dataset viewer schema", self.card)
        self.assertIn("`dbc-r3714-buildkit-cache-mount-id-leftover`", self.card)
        self.assertIn("`dbc-r3714-buildkit-cache-mount-sharing-locked-leftover`", self.card)
        self.assertIn("### Known payload disclosures", self.card)
        self.assertNotIn("**Not declared yet.**", self.card)

    def test_card_body_discloses_the_six_thin_meta_records(self):
        for record_id in (
            "acm-r01-disc-wallet-map-b7e2",
            "acm-r01-orders-v2-email-req-4c91",
            "acm-r02-addprop-reqid-a61e",
            "acm-r02-callback-hmac256-9b30",
            "acm-r98-oas31-null-phone-d4a2",
            "acm-r98-idem-header-sunset-7e19",
        ):
            with self.subTest(record_id=record_id):
                self.assertIn(f"`{record_id}`", self.card)
        self.assertIn("| `steps[].reflection` | optional |", self.card)
        self.assertIn(
            "two each in `batch-r01.jsonl`, `batch-r02.jsonl` and "
            "`batch-r98.jsonl`",
            self.card,
        )
        self.assertIn(
            "The two in `batch-r01.jsonl` are the schema-inference source",
            self.card,
        )

    def test_declared_globs_cover_every_published_shard_name(self):
        # The mirror publishes 4006 shards and nothing but `batch-rNN.jsonl`.
        self.assertEqual(len(PUBLISHED_PAYLOADS), 4006)
        self.assertEqual(PUBLISHED_PAYLOADS[0], "batch-r01.jsonl")
        self.assertEqual(PUBLISHED_PAYLOADS[-1], "batch-r4006.jsonl")
        self.assertEqual(
            card_schema.payload_coverage_errors(
                self.declaration,
                PUBLISHED_PAYLOADS,
            ),
            [],
        )
        self.assertTrue(
            card_schema.payload_coverage_errors(self.declaration, ["episodes.jsonl"])
        )

    def test_representative_records_match_the_declared_feature_tree(self):
        rows = _fixture_rows()
        self.assertEqual(len(rows), len(REPRESENTATIVE_SOURCES))
        self.assertEqual(
            {record["id"] for _raw_line, record in rows},
            set(REPRESENTATIVE_SOURCES),
        )
        for _raw_line, record in rows:
            with self.subTest(record_id=record["id"]):
                _assert_object_matches(
                    self,
                    record,
                    self.declaration["features"],
                    "",
                )

        self.assertEqual(
            {tuple(sorted(record["meta"])) for _raw_line, record in rows},
            set(META_SHAPE_COUNTS),
        )
        steps = [
            step
            for _raw_line, record in rows
            for step in record["steps"]
        ]
        self.assertTrue(any("reflection" in step for step in steps))
        self.assertTrue(any("reflection" not in step for step in steps))


@unittest.skipUnless(
    MIRROR.is_dir(),
    "api-contract-migration mirror not present; read-only fidelity requires it",
)
class ApiContractMigrationRawMirrorFidelity(unittest.TestCase):
    def test_representative_fixture_is_byte_identical_to_mirror_coordinates(self):
        fixture_by_id = {
            record["id"]: raw_line for raw_line, record in _fixture_rows()
        }
        self.assertEqual(set(fixture_by_id), set(REPRESENTATIVE_SOURCES))
        for record_id, (filename, line_number, expected_digest) in (
            REPRESENTATIVE_SOURCES.items()
        ):
            with self.subTest(record_id=record_id):
                source_lines = (MIRROR / filename).read_bytes().splitlines(
                    keepends=True
                )
                source_line = source_lines[line_number - 1]
                fixture_line = fixture_by_id[record_id]
                self.assertEqual(
                    hashlib.sha256(source_line).hexdigest(),
                    expected_digest,
                )
                self.assertEqual(
                    hashlib.sha256(fixture_line).hexdigest(),
                    expected_digest,
                )
                self.assertEqual(fixture_line, source_line)

    def test_mirror_inventory_and_census_match_pinned_evidence(self):
        actual_payloads = {path.name for path in MIRROR.glob("*.jsonl")}
        self.assertEqual(actual_payloads, set(PUBLISHED_PAYLOADS))
        inventory = ("\n".join(PUBLISHED_PAYLOADS) + "\n").encode()
        self.assertEqual(hashlib.sha256(inventory).hexdigest(), INVENTORY_SHA256)

        record_count = 0
        step_count = 0
        seed_count = 0
        parse_failures = []
        thin_meta_locations = []
        reflection_missing_by_file: dict[str, int] = {}
        meta_shape_counts: dict[tuple[str, ...], int] = {}

        for filename in PUBLISHED_PAYLOADS:
            with (MIRROR / filename).open(encoding="utf-8") as handle:
                for line_number, line in enumerate(handle, 1):
                    try:
                        record = json.loads(line)
                    except json.JSONDecodeError as exc:
                        parse_failures.append(f"{filename}:{line_number}: {exc}")
                        continue
                    record_count += 1
                    steps = record["steps"]
                    step_count += len(steps)
                    meta = record["meta"]
                    seed_count += int("seed" in meta)
                    shape = tuple(sorted(meta))
                    meta_shape_counts[shape] = meta_shape_counts.get(shape, 0) + 1
                    if set(meta) == {"factory", "generator", "round"}:
                        thin_meta_locations.append(
                            (filename, line_number, record["id"])
                        )
                    missing = sum("reflection" not in step for step in steps)
                    if missing:
                        reflection_missing_by_file[filename] = (
                            reflection_missing_by_file.get(filename, 0) + missing
                        )

        self.assertEqual(parse_failures, [])
        self.assertEqual(record_count, 8012)
        self.assertEqual(step_count, 130021)
        self.assertEqual(seed_count, 6330)
        self.assertEqual(meta_shape_counts, META_SHAPE_COUNTS)
        self.assertEqual(thin_meta_locations, THIN_META_LOCATIONS)
        self.assertEqual(
            reflection_missing_by_file,
            {
                "batch-r01.jsonl": 38,
                "batch-r02.jsonl": 36,
                "batch-r98.jsonl": 38,
            },
        )


if __name__ == "__main__":
    unittest.main()
