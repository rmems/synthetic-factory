#!/usr/bin/env python3
"""Issue #61 leaf tests for the per-dataset card schema declaration."""

import os
import unittest
from pathlib import Path

from card_schema_test_support import (
    EPISODE_FIELDS,
    EPISODE_JSON_COLUMNS,
    FEATURES_YAML,
    LONG_HORIZON,
    META_JSON_YAML,
    NOT_DECLARED,
    PLAN_PRESENT_ROW,
    QUOTED_N_YAML,
    REFLECTION_OPTIONAL_ROW,
    REWARD_JSON_YAML,
    STEPS_YAML_FEATURE,
    TOOL_CALL_FIELDS,
    VIEWER_SCHEMA_HEADING,
    DeclarationTestCase,
    by_name,
    card_schema,
    feature_index,
    iter_steps,
    mirror_path,
    publisher,
    scan_mirror,
)

DOCKER_BUILD_CACHE = "docker-build-cache-trajectories"

# The published mirror is read-only and lives outside the repo. Point
# CARD_SCHEMA_MIRROR_ROOT at the directory holding the dataset folders to run
# the data-backed test somewhere other than a workstation (CI included);
# without it the test skips rather than fabricating a payload to check against.
MIRROR_ROOT_ENV = "CARD_SCHEMA_MIRROR_ROOT"


def _mirror_root() -> Path:
    override = os.environ.get(MIRROR_ROOT_ENV)
    if override:
        return Path(override) / DOCKER_BUILD_CACHE / "data" / "raw"
    return mirror_path(DOCKER_BUILD_CACHE)


DOCKER_BUILD_CACHE_MIRROR = _mirror_root()

SHARD_NAMES = [f"batch-r{number:02d}.jsonl" for number in range(1, 1029)]


def _spelled(number: int) -> str:
    """The declaration spells small counts in prose; compare like for like."""
    return {8: "eight", 9: "nine"}.get(number, str(number))


def _shard_number(name: str) -> int:
    label = publisher.batch_label(Path(name))
    if label is None:
        raise AssertionError(f"shard name the publisher cannot label: {name}")
    return label[0]


def _shard_range(rows):
    """The (lowest, highest) shard number a set of (shard, record) rows spans."""
    numbers = sorted(_shard_number(shard) for shard, _record in rows)
    return numbers[0], numbers[-1]


def _edge_numbers(note_range):
    """The two shard numbers a note's `batch-rNNN` edge pair names."""
    return tuple(int(edge.removeprefix("batch-r")) for edge in note_range)


def _plant_runs(plant):
    """The `plant` rows split into the named run and the literal `designed` run."""
    named = [(s, r) for s, r in plant if r["meta"]["plant"] != "designed"]
    literal = [(s, r) for s, r in plant if r["meta"]["plant"] == "designed"]
    return named, literal


_needs_mirror = unittest.skipUnless(
    DOCKER_BUILD_CACHE_MIRROR.is_dir(),
    f"read-only published mirror is not available (set ${MIRROR_ROOT_ENV})",
)


def _meta_shapes(records):
    """The three disjoint `meta` shapes: thin, `plant`-bearing, `kind`-bearing."""
    thin = [
        r for _s, r in records if set(r["meta"]) == {"factory", "generator", "round"}
    ]
    plant = [(s, r) for s, r in records if "plant" in r["meta"]]
    kinded = [(s, r) for s, r in records if "kind" in r["meta"]]
    return thin, plant, kinded


def _reward_stats(records):
    """Per-key record counts and the set of value type names, over `reward`."""
    counts: dict = {}
    types: dict = {}
    for _shard, record in records:
        for key, value in record["reward"].items():
            counts[key] = counts.get(key, 0) + 1
            types.setdefault(key, set()).add(type(value).__name__)
    return counts, types


def _tool_arg_stats(records):
    """Per-key counts, value type names and distinct tool names, over args."""
    arg_keys: dict = {}
    arg_types: dict = {}
    tool_names: set = set()
    for _shard, step in iter_steps(records):
        tool_names.add(step["tool_call"]["name"])
        for key, value in step["tool_call"]["args"].items():
            arg_keys[key] = arg_keys.get(key, 0) + 1
            arg_types.setdefault(key, set()).add(type(value).__name__)
    return arg_keys, arg_types, tool_names


def _disclosed_ids_by_size(declaration):
    """Enumerated disclosure id lists, keyed by how many ids each carries."""
    disclosed = [item for item in declaration["disclosures"] if isinstance(item, dict)]
    return {len(item["ids"]): set(item["ids"]) for item in disclosed if "ids" in item}


class DockerBuildCacheDeclarationTests(DeclarationTestCase):
    """Issue #61: thin `meta` vs the `plant` / `designed` leftover shapes.

    Every count asserted here was derived from the published mirror
    (1028 shards, 2056 records, 36640 steps, 0 parse failures), not copied
    from the issue text.
    """

    DATASET = DOCKER_BUILD_CACHE
    ISSUE = 61
    HUB_ITEM = {
        "slug": "docker-build-cache-factory",
        "hub": DOCKER_BUILD_CACHE,
        "pretty": "Docker Build Cache Trajectories",
        "blurb": "Docker/BuildKit leftover cache-invalidation episodes.",
        "tags": ["synthetic-data", "trajectories", "docker", "buildkit", "cache"],
    }
    SUMMARY = publisher.PayloadSummary(
        records=2056, bytes_=12548477, first="r01", last="r1028", names=list(SHARD_NAMES)
    )

    def test_declaration_matches_the_observed_union_schema(self):
        expected_yaml_features = [
            {"name": "id", "dtype": "string"},
            {"name": "goal", "dtype": "string"},
            {"name": "plan", "dtype": "string"},
            STEPS_YAML_FEATURE,
            {"name": "outcome", "dtype": "string"},
            {"name": "reward", "dtype": "json"},
            {"name": "meta", "dtype": "json"},
        ]
        self.assertEqual(
            card_schema.yaml_features(self.declaration["features"]),
            expected_yaml_features,
        )
        names = self.names()
        self.assertEqual(set(names), EPISODE_FIELDS)
        self.assertEqual(names["meta"]["dtype"], "json")
        self.assertEqual(names["reward"]["dtype"], "json")
        _steps, tool_call = self.assert_episode_steps(names)
        self.assertEqual(set(tool_call), TOOL_CALL_FIELDS)
        self.assertEqual(self.declaration["issues"], [61])

    def test_plan_is_mandatory_here_unlike_the_sibling_declaration(self):
        """`plan` is on 2056 of 2056 records; optionality is never inherited."""
        plan = self.feature("plan")
        self.assertEqual(plan["dtype"], "string")
        self.assertNotIn("optional", plan)
        self.assertIn("2056 of 2056", plan["note"])
        sibling_plan = by_name(card_schema.load(LONG_HORIZON)["features"])["plan"]
        self.assertTrue(sibling_plan["optional"])
        self.assertIn(PLAN_PRESENT_ROW, self.card)

    def test_the_shard_name_list_matches_the_published_padding(self):
        """The coverage cross-check must be fed names the publisher can emit.

        The generated list previously used `batch-r{n}.jsonl`, which invents
        `batch-r1.jsonl` .. `batch-r9.jsonl` for the first nine rounds while the
        published shards are zero-padded `batch-r01.jsonl` .. `batch-r09.jsonl`.
        A fabricated list that cannot match the real layout makes the coverage
        check unfalsifiable, so pin the names to `batch_label`.
        """
        self.assertEqual(len(SHARD_NAMES), 1028)
        self.assertEqual(SHARD_NAMES[0], "batch-r01.jsonl")
        self.assertEqual(SHARD_NAMES[-1], "batch-r1028.jsonl")
        for name in SHARD_NAMES:
            label = publisher.batch_label(Path(name))
            self.assertIsNotNone(label, name)
            self.assertEqual(f"batch-{label[2]}.jsonl", name)
        self.assertEqual(
            card_schema.payload_coverage_errors(self.declaration, SHARD_NAMES), []
        )
        self.assertTrue(
            card_schema.payload_coverage_errors(
                {**self.declaration, "data_files": ["data/raw/batch-r0*.jsonl"]},
                SHARD_NAMES,
            )
        )

    # -- Re-derived from the payload, not from the declaration -------------
    #
    # The rest of this class compares the declaration against expectations
    # typed beside it. The tests below are the ones that can fail when the
    # declaration drifts from the payload, so between them they check the
    # facts the fix actually depends on: the three disjoint `meta` shapes, the
    # two `plant` runs, the enumerated ids, the `reward` type spread and the
    # step counts.

    @_needs_mirror
    def test_published_shards_are_exactly_the_declared_shard_list(self):
        """Real published layout, compared as a set.

        Glob order is lexicographic (`batch-r100` before `batch-r11`) while
        rounds are numbered numerically.
        """
        shards, records = scan_mirror(DOCKER_BUILD_CACHE_MIRROR)
        self.assertEqual(len(shards), 1028)
        self.assertEqual(len(records), 2056)
        published = [shard.name for shard in shards]
        self.assertEqual(len(published), len(SHARD_NAMES))
        self.assertEqual(set(published), set(SHARD_NAMES))
        self.assertEqual(
            card_schema.payload_coverage_errors(self.declaration, published), []
        )

    @_needs_mirror
    def test_every_record_carries_exactly_the_declared_top_level_fields(self):
        _shards, records = scan_mirror(DOCKER_BUILD_CACHE_MIRROR)
        names, optional = feature_index(self.declaration["features"])
        for shard, record in records:
            self.assertEqual(set(record) - set(names), set(), shard)
            self.assertEqual(set(names) - set(record) - optional, set(), shard)
            self.assertIsInstance(record["plan"], str, record["id"])
            self.assertTrue(record["plan"].strip(), record["id"])
        total = len(records)
        self.assertIn(f"present on {total} of {total} records", names["plan"]["note"])

    @_needs_mirror
    def test_meta_splits_into_three_disjoint_shapes_with_the_declared_counts(self):
        _shards, records = scan_mirror(DOCKER_BUILD_CACHE_MIRROR)
        names, _optional = feature_index(self.declaration["features"])
        total = len(records)
        thin, plant, kinded = _meta_shapes(records)
        self.assertEqual(len(thin) + len(plant) + len(kinded), total)
        self.assertEqual([len(thin), len(plant), len(kinded)], [1934, 96, 26])
        self.assertEqual(
            [],
            [
                r["id"]
                for _s, r in records
                if "plant" in r["meta"] and "kind" in r["meta"]
            ],
        )
        note = names["meta"]["note"]
        self.assertIn(f"`factory`, `generator`, `round` on all {total}", note)
        self.assertIn(f"`plant` on {len(plant)}", note)
        self.assertIn(f"`product` on {len(kinded)}", note)
        self.assertIn(f"{len(thin)} are thin", self.declaration["note"])
        self.assertIn(f"{len(plant)} add `plant`", self.declaration["note"])

    @_needs_mirror
    def test_the_two_plant_runs_sit_in_the_shard_ranges_the_note_names(self):
        _shards, records = scan_mirror(DOCKER_BUILD_CACHE_MIRROR)
        names, _optional = feature_index(self.declaration["features"])
        _thin, plant, _kinded = _meta_shapes(records)
        note = names["meta"]["note"]
        for label, rows, note_range in (
            ("named", _plant_runs(plant)[0], ("batch-r526", "batch-r549")),
            ("designed", _plant_runs(plant)[1], ("batch-r647", "batch-r684")),
        ):
            with self.subTest(plant=label):
                self.assertEqual(len(rows), 48)
                self.assertEqual(_shard_range(rows), _edge_numbers(note_range))
                self.assertIn(note_range[0], note)
                self.assertIn(note_range[1], note)

    @_needs_mirror
    def test_the_plant_designed_rows_are_not_the_kinded_rows(self):
        """The 48 `plant: designed` rows are a different set from the 26 whose
        `meta.kind` is `designed`; the disclosure says so, so prove it.
        """
        _shards, records = scan_mirror(DOCKER_BUILD_CACHE_MIRROR)
        _thin, plant, kinded = _meta_shapes(records)
        _named, literal_plant = _plant_runs(plant)
        self.assertEqual(
            {r["id"] for _s, r in literal_plant} & {r["id"] for _s, r in kinded}, set()
        )
        self.assertEqual({r["meta"]["kind"] for _s, r in kinded}, {"designed"})

    @_needs_mirror
    def test_enumerated_disclosure_ids_are_exactly_the_derived_sets(self):
        _shards, records = scan_mirror(DOCKER_BUILD_CACHE_MIRROR)
        _thin, _plant, kinded = _meta_shapes(records)
        by_size = _disclosed_ids_by_size(self.declaration)
        published_ids = {r["id"] for _s, r in records}
        self.assertEqual(
            by_size[26],
            {r["id"] for _s, r in kinded},
            "the 26 -l3 ids are the kinded rows",
        )
        self.assertLessEqual(by_size[26] | by_size[8], published_ids)
        kinded_numbers = sorted(_shard_number(shard) for shard, _r in kinded)
        self.assertEqual((kinded_numbers[0], kinded_numbers[-1]), (634, 646))
        self.assertTrue(all(record_id.endswith("-l3") for record_id in by_size[26]))
        self.assertEqual(
            {r["id"] for _s, r in records if r["id"].endswith("-l3")}, by_size[26]
        )

    @_needs_mirror
    def test_reward_key_counts_match_the_declared_note(self):
        _shards, records = scan_mirror(DOCKER_BUILD_CACHE_MIRROR)
        names, _optional = feature_index(self.declaration["features"])
        counts, _types = _reward_stats(records)
        reward_note = names["reward"]["note"]
        self.assertEqual(
            {k for k, v in counts.items() if v == len(records)},
            {"success", "tests_passed", "cost_steps"},
        )
        self.assertIn(f"`xfailed` on {counts['xfailed']}", reward_note)
        self.assertIn(f"`residual` on {counts['residual']}", reward_note)
        self.assertIn(f"`handoff` on {counts['handoff']}", reward_note)
        self.assertIn(f"`plan_changes` on {counts['plan_changes']}", reward_note)

    @_needs_mirror
    def test_the_eight_single_record_reward_extras_are_the_disclosed_ids(self):
        _shards, records = scan_mirror(DOCKER_BUILD_CACHE_MIRROR)
        names, _optional = feature_index(self.declaration["features"])
        counts, _types = _reward_stats(records)
        by_size = _disclosed_ids_by_size(self.declaration)
        singles = {key for key, count in counts.items() if count == 1}
        self.assertEqual(len(singles), 8)
        self.assertIn(
            f"{_spelled(len(singles))} single-record extras", names["reward"]["note"]
        )
        self.assertEqual(
            by_size[8],
            {r["id"] for _s, r in records if singles & set(r["reward"])},
            "the 8 disclosed ids are the records carrying a single-record extra",
        )

    @_needs_mirror
    def test_the_reward_type_spread_is_what_forces_a_json_column(self):
        _shards, records = scan_mirror(DOCKER_BUILD_CACHE_MIRROR)
        counts, types = _reward_stats(records)
        singles = {key for key, count in counts.items() if count == 1}
        self.assertEqual(types["acorn"], {"str"})
        self.assertEqual(types["glibc"], {"float"})
        self.assertEqual(types["second_build_s"], {"float"})
        for key in singles - {"acorn", "glibc", "second_build_s"}:
            with self.subTest(reward_key=key):
                self.assertEqual(types[key], {"int"})
        self.assertEqual(types["success"], {"bool"})

    @_needs_mirror
    def test_every_step_carries_exactly_the_declared_step_fields(self):
        _shards, records = scan_mirror(DOCKER_BUILD_CACHE_MIRROR)
        self.assert_steps_carry_declared_fields(records, self.names())

    @_needs_mirror
    def test_step_notes_match_the_reflection_and_decision_basis_counts(self):
        _shards, records = scan_mirror(DOCKER_BUILD_CACHE_MIRROR)
        names, _optional = feature_index(self.declaration["features"])
        step_names, _step_optional = feature_index(names["steps"]["list"])
        steps = [step for _shard, step in iter_steps(records)]
        total_steps = len(steps)
        reflections = sum(1 for step in steps if "reflection" in step)
        bases = sum(1 for step in steps if step["decision_basis"])
        self.assertIn(
            f"present on {reflections} of {total_steps} steps",
            step_names["reflection"]["note"],
        )
        self.assertIn(f"{reflections} of {total_steps} steps", self.card)
        self.assertEqual(bases, total_steps)

    @_needs_mirror
    def test_tool_call_arg_key_counts_match_the_struct_note(self):
        _shards, records = scan_mirror(DOCKER_BUILD_CACHE_MIRROR)
        names, _optional = feature_index(self.declaration["features"])
        step_names, _step_optional = feature_index(names["steps"]["list"])
        arg_keys, _arg_types, tool_names = _tool_arg_stats(records)
        args_note = step_names["tool_call"]["struct"][1]["note"]
        # "nine tools" counts distinct tool names; the keys listed after it
        # are the ten argument names those tools use between them.
        self.assertIn(f"across {_spelled(len(tool_names))} tools", args_note)
        self.assertEqual(len(tool_names), 9)
        self.assertEqual(len(arg_keys), 10)
        for key in (
            "command",
            "path",
            "pattern",
            "cmd",
            "diff",
            "glob",
            "limit",
            "contents",
        ):
            with self.subTest(arg=key):
                self.assertIn(f"`{key}` {arg_keys[key]}", args_note)
        self.assertIn(f"`old` / `new` {arg_keys['old']} each", args_note)
        self.assertEqual(arg_keys["old"], arg_keys["new"])

    @_needs_mirror
    def test_limit_is_the_lone_integer_tool_argument(self):
        """`limit` is why the union cannot be a struct of strings.

        That is the reason the declaration exists at all.
        """
        _shards, records = scan_mirror(DOCKER_BUILD_CACHE_MIRROR)
        _arg_keys, arg_types, _tool_names = _tool_arg_stats(records)
        self.assertEqual(arg_types["limit"], {"int"})
        for key, kinds in arg_types.items():
            if key != "limit":
                with self.subTest(arg=key):
                    self.assertEqual(kinds, {"str"})

    @_needs_mirror
    def test_home_dump_provenance_and_the_leftover_count_the_card_prints(self):
        _shards, records = scan_mirror(DOCKER_BUILD_CACHE_MIRROR)
        total = len(records)
        published_ids = {r["id"] for _s, r in records}
        self.assertEqual(
            {r["meta"]["factory"] for _s, r in records}, {"docker-build-cache-factory"}
        )
        self.assertEqual({r["meta"]["generator"] for _s, r in records}, {"grok-4.6"})
        self.assertTrue(
            all(record_id.startswith("dbc-") for record_id in published_ids)
        )
        self.assertEqual(len(published_ids), total)
        leftover = sum(1 for _s, r in records if "leftover" in r["id"])
        self.assertIn(f"{leftover} of the {total} record ids contain `leftover`", self.card)

    def test_key_bag_columns_are_declared_json(self):
        self.assert_json_columns(EPISODE_JSON_COLUMNS)

    def test_card_front_matter_declares_the_default_config_over_raw_batches(self):
        # Parent tests pin the stdlib YAML emitter byte-for-byte. This leaf
        # asserts that the complete structurally validated block is inserted
        # once, at the end of the card front matter.
        emitted = card_schema.metadata_yaml(self.declaration)
        front_matter = self.assert_front_matter_declares_default_config(
            FEATURES_YAML,
            META_JSON_YAML,
            REWARD_JSON_YAML,
            # `n` is a YAML boolean unless quoted, so the step index must stay a string.
            QUOTED_N_YAML,
            # No card-only annotation may reach the YAML: `datasets` reads the
            # feature type from the first key after `name`.
            absent=("optional:", "note:"),
        )
        self.assertEqual(front_matter.count("configs:\n"), 1)
        self.assertEqual(front_matter.count("dataset_info:\n"), 1)
        self.assertTrue(front_matter.endswith(emitted))

    def test_card_body_owns_the_designed_l3_records_and_the_leftover_mechanic(self):
        self.assertIn(VIEWER_SCHEMA_HEADING, self.card)
        self.assertNotIn(NOT_DECLARED, self.card)
        self.assert_card_has(
            # The advertised same-factory leftover-cache mechanic, not a foreign dump.
            "833 of the 2056 record ids contain `leftover`",
            # The 26 designed cache-product templates are owned here by name.
            "`dbc-r634-bk-cachemount-id-alias-l3`",
            "`dbc-r646-containerd-gc-root-label-l3`",
            # Outbound copies in destination dumps stay with #44, not with this card.
            "/issues/44",
            REFLECTION_OPTIONAL_ROW,
            "696 of 36640 steps",
        )

    def test_disclosures_keep_every_record_with_this_factory(self):
        summaries = [item["summary"] for item in self.declaration["disclosures"]]
        joined = " ".join(summaries)
        self.assertIn("no dest-stamped foreign payload", joined)
        self.assertIn("36640 of 36640", joined)
        listed = {
            record_id
            for item in self.declaration["disclosures"]
            for record_id in item["ids"]
        }
        # 26 designed `-l3` ids plus the 8 single-record `reward` extras.
        self.assertEqual(len(listed), 34)
        self.assertEqual(
            sum(1 for record_id in listed if record_id.endswith("-l3")), 26
        )
        self.assertTrue(all(record_id.startswith("dbc-") for record_id in listed))


if __name__ == "__main__":
    unittest.main()
