import contextlib
import copy
import io
import json
import math
import subprocess
import sys
import tempfile
import unittest
from collections import Counter
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
PIPELINES = ROOT / "pipelines"
if str(PIPELINES) not in sys.path:
    sys.path.insert(0, str(PIPELINES))

import curate_tags  # noqa: E402
from curate_tags import (  # noqa: E402
    DEFAULT_TAXONOMY_PATH,
    REASON_INVALID_JSON,
    REASON_INVALID_UTF8,
    REASON_PROVENANCE_CONFLICT,
    REASON_RECORD_NOT_OBJECT,
    REASON_RECORD_TOO_DEEP,
    REASON_TAG_ALIAS,
    REASON_TAG_CANONICAL,
    REASON_TAG_EMPTY,
    REASON_TAG_NOT_STRING,
    REASON_TAG_PATTERN,
    REASON_TAG_MAPPING_AMBIGUOUS,
    REASON_TAG_UNMAPPED,
    REASON_TAGS_DEDUPLICATED,
    REASON_TAGS_MAPPED,
    REASON_TAGS_NOT_LIST,
    REASON_TAGS_PROVENANCE_REUSED,
    REASON_TAGS_UNMAPPED,
    TAG_PROVENANCE_FIELD,
    TRANSFORM_NAME,
    TRANSFORM_VERSION,
    UNMAPPED_MARKER_TAG,
    Taxonomy,
    TagTaxonomyError,
    _preflight_destinations,
    _write_destinations,
    canonical_json,
    curate_jsonl,
    curate_record,
    load_taxonomy,
    map_tags,
    normalize_tag,
    vocabulary_entropy,
)


# A compact vocabulary is the point of the lane. Twenty-one terms replace the
# 2790-string free-form surface of the 2026-08-17 run; this bound keeps a later
# edit from quietly reintroducing a long tail.
MAX_CANONICAL_TAGS = 40
DEEP_REGEX_GROUPS = sys.getrecursionlimit() * 2
GROUPED_OPTIONAL_REPEATS = 28
INVALID_REGEX_PATTERNS = (
    ("re.error", "^($"),
    ("OverflowError", "^a{999999999999999999999999999999999999}$"),
    (
        "RecursionError",
        "^" + "(" * DEEP_REGEX_GROUPS + "a" + ")" * DEEP_REGEX_GROUPS + "$",
    ),
)
GROUPED_OPTIONAL_REGEX_PATTERNS = (
    (
        "capturing_grouped_optionals",
        "^" + "(a?)" * GROUPED_OPTIONAL_REPEATS + "a" * GROUPED_OPTIONAL_REPEATS + "$",
    ),
    (
        "noncapturing_grouped_optionals",
        "^"
        + "(?:a?)" * GROUPED_OPTIONAL_REPEATS
        + "a" * GROUPED_OPTIONAL_REPEATS
        + "$",
    ),
)
UNSAFE_LINEAR_REGEX_PATTERNS = (
    ("nested_repeat", "^(a+)+$"),
    ("repeated_alternation", "^(a|aa)+$"),
    ("overlapping_adjacent_repeats", "^a+a+$"),
    ("ambiguous_wildcard_boundary", "^.*x.*$"),
    ("overlapping_repeat_suffix", "^a+a$"),
    ("overlapping_optional_suffix", "^a?a$"),
    ("overlapping_alternation", "^(a|aa)b$"),
    *GROUPED_OPTIONAL_REGEX_PATTERNS,
    ("capturing_group_literal_suffix", "^(a?)a$"),
    ("noncapturing_group_literal_suffix", "^(?:a?)a$"),
    ("capturing_group_variable_repeat_suffix", "^(a?)a+$"),
    ("noncapturing_group_variable_repeat_suffix", "^(?:a?)a+$"),
    ("capturing_group_fixed_repeat_suffix", "^(a?)a{2}$"),
    ("noncapturing_group_fixed_repeat_suffix", "^(?:a?)a{2}$"),
    ("capturing_nullable_group_between_repeats", "^a+(b?)a$"),
    ("noncapturing_nullable_group_between_repeats", "^a+(?:b?)a$"),
    ("capturing_multiple_nullable_tails", "^(a?b?)a$"),
    ("noncapturing_multiple_nullable_tails", "^(?:a?b?)a$"),
)
SAFE_GROUP_BOUNDARY_CASES = (
    ("capturing_literal_boundary", "^(a?)b$", "ab"),
    ("noncapturing_literal_boundary", "^(?:a?)b$", "ab"),
    ("capturing_variable_repeat_boundary", "^(a?)b+$", "abbb"),
    ("noncapturing_variable_repeat_boundary", "^(?:a?)b+$", "abbb"),
    ("capturing_fixed_repeat_boundary", "^(a?)b{2}$", "abb"),
    ("noncapturing_fixed_repeat_boundary", "^(?:a?)b{2}$", "abb"),
    ("capturing_nullable_group_boundary", "^a+(b?)c$", "aaabc"),
    ("noncapturing_nullable_group_boundary", "^a+(?:b?)c$", "aaabc"),
)
REGEX_RESOURCE_EXCEPTION_TYPES = (OverflowError, RecursionError, MemoryError)

TAXONOMY = load_taxonomy()


def record(tags, **overrides):
    value = {
        "id": "ttf-r01-001",
        "meta": {"factory": "thalamic-trajectory-factory", "round": 1, "tags": tags},
    }
    value.update(overrides)
    return value


def minimal_taxonomy(**overrides):
    document = {
        "version": "tag-taxonomy-test",
        "canonical_tag_pattern": "^[a-z][a-z0-9_]*:[a-z][a-z0-9_]*$",
        "facets": [
            {
                "id": "decision",
                "description": "gate decision",
                "terms": [
                    {
                        "tag": "decision:accept",
                        "definition": "accept",
                        "aliases": ["accept"],
                    }
                ],
            },
            {
                "id": "curation",
                "description": "bookkeeping",
                "terms": [
                    {
                        "tag": UNMAPPED_MARKER_TAG,
                        "definition": "unmapped source tags were dropped",
                        "aliases": [],
                    }
                ],
            },
        ],
        "pattern_rules": [],
        "transform_emitted_tags": [UNMAPPED_MARKER_TAG],
    }
    document.update(overrides)
    return document


class TaxonomyDocumentTests(unittest.TestCase):
    def test_shipped_taxonomy_is_compact_and_versioned(self):
        self.assertEqual(TAXONOMY.version, "tag-taxonomy-v1")
        self.assertEqual(TAXONOMY.source, str(DEFAULT_TAXONOMY_PATH))
        self.assertLessEqual(len(TAXONOMY.canonical_tags), MAX_CANONICAL_TAGS)
        self.assertGreater(len(TAXONOMY.canonical_tags), 0)
        self.assertIn(UNMAPPED_MARKER_TAG, TAXONOMY.canonical_tags)

    def test_every_canonical_tag_is_facet_qualified_and_defined(self):
        for tag in TAXONOMY.canonical_tags:
            facet, _, term = tag.partition(":")
            self.assertTrue(term, tag)
            self.assertEqual(TAXONOMY.facet_of[tag], facet)
            self.assertTrue(TAXONOMY.definition_of[tag].strip(), tag)

    def test_every_alias_resolves_to_exactly_one_canonical_tag(self):
        document = json.loads(DEFAULT_TAXONOMY_PATH.read_text(encoding="utf-8"))
        seen = {}
        for facet in document["facets"]:
            for term in facet["terms"]:
                for alias in [term["tag"], *term.get("aliases", [])]:
                    key = normalize_tag(alias)
                    self.assertNotIn(
                        key,
                        {k: v for k, v in seen.items() if v != term["tag"]},
                        f"{alias} is claimed by two terms",
                    )
                    seen[key] = term["tag"]
                    self.assertEqual(TAXONOMY.alias_index[key], term["tag"])

    def test_pattern_rules_are_anchored_and_target_declared_tags(self):
        self.assertTrue(TAXONOMY.pattern_rules)
        for _rule_id, tag, compiled in TAXONOMY.pattern_rules:
            self.assertIn(tag, TAXONOMY.canonical_tags)
            self.assertTrue(compiled.pattern.startswith("^"))
            self.assertTrue(compiled.pattern.endswith("$"))

    def test_shipped_regexes_are_in_the_supported_linear_subset(self):
        reloaded = load_taxonomy(DEFAULT_TAXONOMY_PATH)

        self.assertEqual(reloaded.version, TAXONOMY.version)
        self.assertEqual(
            [compiled.pattern for _rule_id, _tag, compiled in reloaded.pattern_rules],
            [compiled.pattern for _rule_id, _tag, compiled in TAXONOMY.pattern_rules],
        )

    def test_duplicate_alias_across_terms_is_rejected(self):
        document = minimal_taxonomy()
        document["facets"][0]["terms"].append(
            {"tag": "decision:reject", "definition": "reject", "aliases": ["accept"]}
        )
        with self.assertRaises(TagTaxonomyError):
            Taxonomy(document, source="<test>")

    def test_unanchored_pattern_rule_is_rejected(self):
        document = minimal_taxonomy(
            pattern_rules=[
                {"id": "loose", "tag": "decision:accept", "pattern": "accept_.*"}
            ]
        )
        with self.assertRaises(TagTaxonomyError):
            Taxonomy(document, source="<test>")

    def test_pattern_rule_targeting_undeclared_tag_is_rejected(self):
        document = minimal_taxonomy(
            pattern_rules=[
                {"id": "ghost", "tag": "decision:ghost", "pattern": "^ghost_.*$"}
            ]
        )
        with self.assertRaises(TagTaxonomyError):
            Taxonomy(document, source="<test>")

    def test_pattern_rule_targeting_transform_emitted_tag_is_rejected(self):
        document = minimal_taxonomy(
            pattern_rules=[
                {
                    "id": "source_marker",
                    "tag": UNMAPPED_MARKER_TAG,
                    "pattern": "^source_marker$",
                }
            ]
        )

        with self.assertRaisesRegex(
            TagTaxonomyError,
            "pattern rule 'source_marker' targets transform-emitted tag",
        ):
            Taxonomy(document, source="<test>")

    def test_regex_compile_failures_are_wrapped_for_both_sites(self):
        for exception_name, pattern in INVALID_REGEX_PATTERNS:
            documents = (
                (
                    "canonical_tag_pattern",
                    minimal_taxonomy(canonical_tag_pattern=pattern),
                ),
                (
                    "pattern_rule",
                    minimal_taxonomy(
                        pattern_rules=[
                            {
                                "id": "invalid_regex",
                                "tag": "decision:accept",
                                "pattern": pattern,
                            }
                        ]
                    ),
                ),
            )
            for site, document in documents:
                with self.subTest(exception=exception_name, site=site):
                    with self.assertRaisesRegex(
                        TagTaxonomyError, "not a valid regex"
                    ):
                        Taxonomy(document, source="<test>")

    def test_unsafe_regexes_are_rejected_for_both_sites(self):
        for unsafe_name, pattern in UNSAFE_LINEAR_REGEX_PATTERNS:
            documents = (
                (
                    "canonical_tag_pattern",
                    minimal_taxonomy(canonical_tag_pattern=pattern),
                ),
                (
                    "pattern_rule",
                    minimal_taxonomy(
                        pattern_rules=[
                            {
                                "id": "unsafe_regex",
                                "tag": "decision:accept",
                                "pattern": pattern,
                            }
                        ]
                    ),
                ),
            )
            for site, document in documents:
                with self.subTest(pattern=unsafe_name, site=site):
                    with self.assertRaises(TagTaxonomyError) as raised:
                        Taxonomy(document, source="<test>")
                    self.assertIn(
                        "supported linear-time regex subset", str(raised.exception)
                    )

    def test_grouped_optionals_are_rejected_during_taxonomy_construction(self):
        for group_kind, pattern in GROUPED_OPTIONAL_REGEX_PATTERNS:
            document = minimal_taxonomy(
                pattern_rules=[
                    {
                        "id": group_kind,
                        "tag": "decision:accept",
                        "pattern": pattern,
                    }
                ]
            )

            with self.subTest(group=group_kind):
                with self.assertRaises(TagTaxonomyError) as raised:
                    Taxonomy(document, source="<test>")
                self.assertIn(
                    "supported linear-time regex subset", str(raised.exception)
                )

    def test_disjoint_group_boundaries_remain_supported(self):
        for rule_id, pattern, source_tag in SAFE_GROUP_BOUNDARY_CASES:
            taxonomy = Taxonomy(
                minimal_taxonomy(
                    pattern_rules=[
                        {
                            "id": rule_id,
                            "tag": "decision:accept",
                            "pattern": pattern,
                        }
                    ]
                ),
                source=f"<{rule_id}>",
            )

            with self.subTest(case=rule_id):
                mapping = taxonomy.map_tag(source_tag)
                self.assertEqual(mapping["canonical"], "decision:accept")
                self.assertEqual(mapping["rule"], f"pattern:{rule_id}")

    def test_later_pathological_same_target_rule_is_rejected_before_mapping(self):
        fast_rule = {
            "id": "a_fast",
            "tag": "decision:accept",
            "pattern": "^a+x$",
        }
        safe = Taxonomy(
            minimal_taxonomy(pattern_rules=[fast_rule]), source="<safe>"
        )
        self.assertEqual(
            safe.map_tag("a" * 28 + "x")["rule"],
            "pattern:a_fast",
        )

        document = minimal_taxonomy(
            pattern_rules=[
                fast_rule,
                {
                    "id": "z_pathological",
                    "tag": "decision:accept",
                    "pattern": "^(a+)+$",
                },
            ]
        )
        with self.assertRaises(TagTaxonomyError) as raised:
            Taxonomy(document, source="<test>")

        self.assertIn("pattern rule 'z_pathological'", str(raised.exception))
        self.assertIn("supported linear-time regex subset", str(raised.exception))

    def test_parser_and_compiler_resource_errors_are_wrapped(self):
        stages = (
            ("parser", "curate_tags._re_parser.parse"),
            ("compiler", "curate_tags.re.compile"),
        )
        for stage, target in stages:
            for exception_type in REGEX_RESOURCE_EXCEPTION_TYPES:
                with self.subTest(stage=stage, exception=exception_type.__name__):
                    forced = exception_type("forced resource failure")
                    with mock.patch(target, side_effect=forced):
                        with self.assertRaises(TagTaxonomyError) as raised:
                            Taxonomy(minimal_taxonomy(), source="<test>")

                    self.assertIn("not a valid regex", str(raised.exception))
                    self.assertIs(raised.exception.__cause__, forced)

    def test_canonical_tag_outside_its_facet_is_rejected(self):
        document = minimal_taxonomy()
        document["facets"][0]["terms"][0]["tag"] = "verdict:accept"
        with self.assertRaises(TagTaxonomyError):
            Taxonomy(document, source="<test>")

    def test_canonical_pattern_must_match_the_entire_tag(self):
        document = minimal_taxonomy()
        document["facets"][0]["terms"][0]["tag"] = "decision:accept\n"
        with self.assertRaisesRegex(TagTaxonomyError, "does not match"):
            Taxonomy(document, source="<test>")

    def test_taxonomy_rejects_surrogate_strings_that_can_reach_output(self):
        version = minimal_taxonomy()
        version["version"] = "bad\ud800"

        rule_id = minimal_taxonomy(
            pattern_rules=[
                {
                    "id": "bad\ud800",
                    "tag": "decision:accept",
                    "pattern": "^accept_[0-9]+$",
                }
            ]
        )

        canonical_tag = minimal_taxonomy(
            canonical_tag_pattern="^[a-z]+:.+$"
        )
        canonical_tag["facets"][0]["terms"][0]["tag"] = "decision:accept\ud800"

        for label, document in (
            ("version", version),
            ("pattern rule id", rule_id),
            ("canonical tag", canonical_tag),
        ):
            with self.subTest(label=label):
                with self.assertRaisesRegex(TagTaxonomyError, "valid UTF-8"):
                    Taxonomy(document, source="<test>")

    def test_taxonomy_without_unmapped_marker_is_rejected(self):
        document = minimal_taxonomy()
        document["facets"] = document["facets"][:1]
        document["transform_emitted_tags"] = []
        with self.assertRaises(TagTaxonomyError):
            Taxonomy(document, source="<test>")

    def test_unmapped_marker_must_be_declared_as_transform_emitted(self):
        document = minimal_taxonomy(transform_emitted_tags=[])
        with self.assertRaisesRegex(
            TagTaxonomyError, "transform_emitted_tags must include"
        ):
            Taxonomy(document, source="<test>")

    def test_loading_a_non_object_document_is_rejected(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "taxonomy.json"
            path.write_text("[]", encoding="utf-8")
            with self.assertRaises(TagTaxonomyError):
                load_taxonomy(path)


class NormalizationTests(unittest.TestCase):
    def test_normalization_is_a_lexical_fold_only(self):
        self.assertEqual(normalize_tag("  MODIFY "), "modify")
        self.assertEqual(normalize_tag("near-miss"), "near_miss")
        self.assertEqual(normalize_tag("wrong_REJECT"), "wrong_reject")
        self.assertEqual(
            normalize_tag("cross_ref_ttf-r06-029"), "cross_ref_ttf_r06_029"
        )
        self.assertEqual(normalize_tag("---"), "")

    def test_case_and_separator_variants_share_one_canonical_tag(self):
        variants = ["MODIFY", "modify", "Modify", "MoDiFy"]
        mapped = {TAXONOMY.map_tag(tag)["canonical"] for tag in variants}
        self.assertEqual(mapped, {"decision:modify"})

        near_miss = {
            TAXONOMY.map_tag(tag)["canonical"] for tag in ["near_miss", "near-miss"]
        }
        self.assertEqual(near_miss, {"pair:near_miss"})


class MapTagTests(unittest.TestCase):
    def test_canonical_tags_map_to_themselves(self):
        source_readable = TAXONOMY.canonical_tags.difference(
            TAXONOMY.transform_emitted_tags
        )
        for tag in sorted(source_readable):
            mapping = TAXONOMY.map_tag(tag)
            self.assertEqual(mapping["canonical"], tag)
            self.assertEqual(mapping["reason"], REASON_TAG_CANONICAL)

    def test_transform_emitted_marker_is_unmapped_from_source_but_reusable(self):
        source = record([UNMAPPED_MARKER_TAG])

        mapping = TAXONOMY.map_tag(UNMAPPED_MARKER_TAG)
        self.assertIsNone(mapping["canonical"])
        self.assertEqual(mapping["reason"], REASON_TAG_UNMAPPED)

        once, manifest = curate_record(source, taxonomy=TAXONOMY)
        container = once[TAG_PROVENANCE_FIELD]["containers"][0]
        self.assertEqual(once["meta"]["tags"], [UNMAPPED_MARKER_TAG])
        self.assertEqual(manifest["tag_counts"]["unmapped_uses"], 1)
        self.assertIn(REASON_TAGS_UNMAPPED, manifest["reason_codes"])
        self.assertEqual(container["mappings"][0]["canonical"], None)
        self.assertEqual(container["mappings"][-1]["rule"], "transform")

        twice, second_manifest = curate_record(once, taxonomy=TAXONOMY)
        self.assertEqual(twice, once)
        self.assertIn(
            REASON_TAGS_PROVENANCE_REUSED, second_manifest["reason_codes"]
        )

    def test_transform_emitted_alias_conflict_with_pattern_is_ambiguous(self):
        document = minimal_taxonomy(
            pattern_rules=[
                {
                    "id": "marker_hijack",
                    "tag": "decision:accept",
                    "pattern": "^curation_unmapped_source_tags$",
                }
            ]
        )
        taxonomy = Taxonomy(document, source="<test>")

        mapping = taxonomy.map_tag(UNMAPPED_MARKER_TAG)

        self.assertIsNone(mapping["canonical"])
        self.assertIsNone(mapping["rule"])
        self.assertEqual(mapping["reason"], REASON_TAG_MAPPING_AMBIGUOUS)

        container = map_tags([UNMAPPED_MARKER_TAG], taxonomy)
        self.assertEqual(container["canonical_tags"], [UNMAPPED_MARKER_TAG])
        self.assertEqual(container["unmapped_tags"], [UNMAPPED_MARKER_TAG])
        self.assertEqual(
            container["mappings"][0]["reason"], REASON_TAG_MAPPING_AMBIGUOUS
        )
        self.assertEqual(container["mappings"][-1]["rule"], "transform")

    def test_alias_pattern_and_unmapped_decisions_are_explained(self):
        alias = TAXONOMY.map_tag("preference_pair")
        self.assertEqual(alias["canonical"], "kind:preference_pair")
        self.assertEqual(alias["reason"], REASON_TAG_ALIAS)
        self.assertEqual(alias["rule"], "alias")

        pattern = TAXONOMY.map_tag("cross_ref_ttf-r06-029")
        self.assertEqual(pattern["canonical"], "link:cross_reference")
        self.assertEqual(pattern["reason"], REASON_TAG_PATTERN)
        self.assertEqual(pattern["rule"], "pattern:cross_reference")
        self.assertEqual(
            TAXONOMY.map_tag("densification_pass_2")["canonical"],
            "process:densification_pass",
        )
        self.assertEqual(
            TAXONOMY.map_tag("identity_note_ttf_r01_001")["canonical"],
            "note:identity_note",
        )

        unmapped = TAXONOMY.map_tag("neoclassical-tearing-mode")
        self.assertIsNone(unmapped["canonical"])
        self.assertEqual(unmapped["reason"], REASON_TAG_UNMAPPED)
        self.assertEqual(unmapped["source"], "neoclassical-tearing-mode")

    def test_compound_decision_labels_are_not_folded_into_a_decision(self):
        # These qualify or judge a decision rather than name one. Folding them
        # into decision:* would invent semantics the source never stated.
        for tag in (
            "wrong_REJECT",
            "ACCEPT_defective",
            "REJECT_with_replan",
            "both_sides_REJECT",
            "over_conservative_MODIFY",
        ):
            with self.subTest(tag=tag):
                self.assertIsNone(TAXONOMY.map_tag(tag)["canonical"])

    def test_free_text_after_a_pattern_stays_unmapped(self):
        self.assertEqual(
            TAXONOMY.map_tag("post_r5_gap_closure")["canonical"],
            "process:gap_closure",
        )
        self.assertEqual(
            TAXONOMY.map_tag("gap1-closure")["canonical"], "process:gap_closure"
        )
        self.assertIsNone(TAXONOMY.map_tag("r3b_gap6_closed_tables")["canonical"])

    def test_pattern_rule_matches_the_whole_normalized_tag(self):
        taxonomy = Taxonomy(
            minimal_taxonomy(
                pattern_rules=[
                    {
                        "id": "alternation",
                        "tag": "decision:accept",
                        "pattern": "^foo|bar$",
                    }
                ]
            ),
            source="<test>",
        )

        self.assertEqual(taxonomy.map_tag("bar")["canonical"], "decision:accept")
        self.assertIsNone(taxonomy.map_tag("foo-extra")["canonical"])

    def test_overlapping_pattern_rules_leave_the_source_tag_unmapped(self):
        document = minimal_taxonomy()
        document["facets"][0]["terms"].append(
            {
                "tag": "decision:reject",
                "definition": "reject",
                "aliases": ["reject"],
            }
        )
        document["pattern_rules"] = [
            {
                "id": "broad",
                "tag": "decision:accept",
                "pattern": "^foo.*$",
            },
            {
                "id": "specific",
                "tag": "decision:reject",
                "pattern": "^foo_bar$",
            },
        ]
        taxonomy = Taxonomy(document, source="<test>")

        mapping = taxonomy.map_tag("foo-bar")

        self.assertIsNone(mapping["canonical"])
        self.assertIsNone(mapping["rule"])
        self.assertEqual(mapping["reason"], REASON_TAG_MAPPING_AMBIGUOUS)

        container = map_tags(["foo-bar"], taxonomy)
        self.assertEqual(container["canonical_tags"], [UNMAPPED_MARKER_TAG])
        self.assertEqual(container["unmapped_tags"], ["foo-bar"])
        self.assertEqual(
            container["mappings"][0]["reason"], REASON_TAG_MAPPING_AMBIGUOUS
        )

    def test_same_target_pattern_matches_do_not_depend_on_rule_order(self):
        rules = [
            {
                "id": "first",
                "tag": "decision:accept",
                "pattern": "^foo.*$",
            },
            {
                "id": "second",
                "tag": "decision:accept",
                "pattern": "^foo_bar$",
            },
        ]
        forward = Taxonomy(
            minimal_taxonomy(pattern_rules=rules), source="<forward>"
        ).map_tag("foo-bar")
        reverse = Taxonomy(
            minimal_taxonomy(pattern_rules=list(reversed(rules))), source="<reverse>"
        ).map_tag("foo-bar")

        self.assertEqual(forward, reverse)
        self.assertEqual(forward["canonical"], "decision:accept")
        self.assertEqual(forward["rule"], "pattern:first")
        self.assertEqual(forward["reason"], REASON_TAG_PATTERN)

    def test_alias_and_pattern_conflict_leaves_the_source_tag_unmapped(self):
        document = minimal_taxonomy()
        document["facets"][0]["terms"].append(
            {
                "tag": "decision:reject",
                "definition": "reject",
                "aliases": ["reject"],
            }
        )
        document["pattern_rules"] = [
            {
                "id": "reject_accept_alias",
                "tag": "decision:reject",
                "pattern": "^accept$",
            }
        ]
        mapping = Taxonomy(document, source="<test>").map_tag("accept")

        self.assertIsNone(mapping["canonical"])
        self.assertIsNone(mapping["rule"])
        self.assertEqual(mapping["reason"], REASON_TAG_MAPPING_AMBIGUOUS)

    def test_non_string_and_empty_tags_are_reported_not_guessed(self):
        not_string = TAXONOMY.map_tag(17)
        self.assertIsNone(not_string["canonical"])
        self.assertEqual(not_string["reason"], REASON_TAG_NOT_STRING)

        empty = TAXONOMY.map_tag("   ")
        self.assertIsNone(empty["canonical"])
        self.assertEqual(empty["reason"], REASON_TAG_EMPTY)


class MapTagsTests(unittest.TestCase):
    def test_duplicates_collapse_and_output_is_sorted(self):
        entry = map_tags(["MODIFY", "modify", "ACCEPT"], TAXONOMY)
        self.assertEqual(entry["canonical_tags"], ["decision:accept", "decision:modify"])
        self.assertEqual(entry["duplicates_collapsed"], 1)
        self.assertEqual(entry["unmapped_tags"], [])

    def test_unmapped_tags_add_the_marker_exactly_once(self):
        entry = map_tags(["tokamak", "nanopore", "MODIFY"], TAXONOMY)
        self.assertEqual(
            entry["canonical_tags"], [UNMAPPED_MARKER_TAG, "decision:modify"]
        )
        self.assertEqual(entry["unmapped_tags"], ["tokamak", "nanopore"])

    def test_source_tags_are_preserved_verbatim(self):
        source = ["MODIFY", "tokamak"]
        entry = map_tags(source, TAXONOMY)
        self.assertEqual(entry["source_tags"], source)
        self.assertIsNot(entry["source_tags"], source)


class CurateRecordTests(unittest.TestCase):
    def test_retained_records_use_only_canonical_tags(self):
        source = record(["preference_pair", "MODIFY", "tokamak"])
        curated, manifest = curate_record(source, taxonomy=TAXONOMY)

        self.assertIsNotNone(curated)
        for tag in curated["meta"]["tags"]:
            self.assertIn(tag, TAXONOMY.canonical_tags)
        self.assertEqual(
            curated["meta"]["tags"],
            [UNMAPPED_MARKER_TAG, "decision:modify", "kind:preference_pair"],
        )
        self.assertEqual(manifest["action"], "modified")
        self.assertIn(REASON_TAGS_MAPPED, manifest["reason_codes"])
        self.assertIn(REASON_TAGS_UNMAPPED, manifest["reason_codes"])

    def test_original_tags_remain_recoverable_from_provenance(self):
        source_tags = ["preference_pair", "MODIFY", "tokamak", "nanopore"]
        curated, _ = curate_record(record(list(source_tags)), taxonomy=TAXONOMY)

        provenance = curated[TAG_PROVENANCE_FIELD]
        self.assertEqual(provenance["taxonomy_version"], TAXONOMY.version)
        self.assertEqual(len(provenance["containers"]), 1)
        container = provenance["containers"][0]
        self.assertEqual(container["json_pointer"], "/meta/tags")
        self.assertEqual(container["source_tags"], source_tags)
        recovered = [
            mapping["source"]
            for mapping in container["mappings"]
            if mapping["rule"] != "transform"
        ]
        self.assertEqual(recovered, source_tags)

    def test_unmapped_tags_are_reported_explicitly(self):
        curated, manifest = curate_record(
            record(["tokamak", "MODIFY", "nanopore"]), taxonomy=TAXONOMY
        )

        self.assertEqual(manifest["unmapped_tags"], ["nanopore", "tokamak"])
        self.assertEqual(manifest["tag_counts"]["unmapped_uses"], 2)
        self.assertEqual(manifest["tag_counts"]["mapped_uses"], 1)
        self.assertEqual(
            manifest["containers"][0]["unmapped_tags"], ["tokamak", "nanopore"]
        )
        self.assertEqual(
            curated[TAG_PROVENANCE_FIELD]["containers"][0]["unmapped_tags"],
            ["tokamak", "nanopore"],
        )

    def test_nested_containers_are_curated_with_stable_pointers(self):
        source = {
            "id": "ffpc-r02-004",
            "meta": {"tags": ["preference_pair"]},
            "chosen": {"meta": {"tags": ["ACCEPT", "chosen"]}},
            "rejected": {"meta": {"tags": ["REJECT", "rejected", "tokamak"]}},
        }
        curated, manifest = curate_record(source, taxonomy=TAXONOMY)

        pointers = [
            container["json_pointer"]
            for container in curated[TAG_PROVENANCE_FIELD]["containers"]
        ]
        self.assertEqual(pointers, ["/chosen/meta/tags", "/meta/tags", "/rejected/meta/tags"])
        self.assertEqual(
            curated["chosen"]["meta"]["tags"], ["decision:accept", "side:chosen"]
        )
        self.assertEqual(
            curated["rejected"]["meta"]["tags"],
            [UNMAPPED_MARKER_TAG, "decision:reject", "side:rejected"],
        )
        self.assertEqual(manifest["tag_counts"]["containers"], 3)

    def test_tag_containers_inside_arrays_are_reached(self):
        source = {"id": "x", "views": [{"meta": {"tags": ["MODIFY"]}}]}
        curated, _ = curate_record(source, taxonomy=TAXONOMY)

        self.assertEqual(curated["views"][0]["meta"]["tags"], ["decision:modify"])
        self.assertEqual(
            curated[TAG_PROVENANCE_FIELD]["containers"][0]["json_pointer"],
            "/views/0/meta/tags",
        )

    def test_pointer_tokens_are_escaped(self):
        source = {"a/b": {"tags": ["MODIFY"]}, "c~d": {"tags": ["ACCEPT"]}}
        curated, _ = curate_record(source, taxonomy=TAXONOMY)

        pointers = sorted(
            container["json_pointer"]
            for container in curated[TAG_PROVENANCE_FIELD]["containers"]
        )
        self.assertEqual(pointers, ["/a~1b/tags", "/c~0d/tags"])

    def test_deduplication_is_reported(self):
        _curated, manifest = curate_record(
            record(["MODIFY", "modify"]), taxonomy=TAXONOMY
        )
        self.assertIn(REASON_TAGS_DEDUPLICATED, manifest["reason_codes"])

    def test_record_without_tags_is_left_alone(self):
        source = {"id": "x", "meta": {"round": 1}}
        curated, manifest = curate_record(source, taxonomy=TAXONOMY)

        self.assertEqual(curated, source)
        self.assertNotIn(TAG_PROVENANCE_FIELD, curated)
        self.assertEqual(manifest["action"], "unchanged")
        self.assertEqual(manifest["reason_codes"], [])

    def test_non_object_record_is_excluded(self):
        curated, manifest = curate_record(["not", "a", "record"], taxonomy=TAXONOMY)
        self.assertIsNone(curated)
        self.assertEqual(manifest["reason_codes"], [REASON_RECORD_NOT_OBJECT])

    def test_non_list_tag_container_is_excluded_not_guessed(self):
        curated, manifest = curate_record(
            {"id": "x", "meta": {"tags": "MODIFY"}}, taxonomy=TAXONOMY
        )
        self.assertIsNone(curated)
        self.assertEqual(manifest["reason_codes"], [REASON_TAGS_NOT_LIST])

    def test_foreign_tag_provenance_is_a_conflict(self):
        source = record(["MODIFY"])
        source[TAG_PROVENANCE_FIELD] = {"taxonomy_version": "someone-elses-v9"}
        curated, manifest = curate_record(source, taxonomy=TAXONOMY)

        self.assertIsNone(curated)
        self.assertEqual(manifest["reason_codes"], [REASON_PROVENANCE_CONFLICT])

    def test_explicit_null_tag_provenance_is_a_conflict(self):
        sources = (
            record(["MODIFY"], tag_provenance=None),
            {"id": "tagless", TAG_PROVENANCE_FIELD: None},
        )
        for source in sources:
            with self.subTest(record=source["id"]):
                curated, manifest = curate_record(source, taxonomy=TAXONOMY)
                self.assertIsNone(curated)
                self.assertEqual(
                    manifest["reason_codes"], [REASON_PROVENANCE_CONFLICT]
                )

    def test_provenance_requires_matching_transform_identity(self):
        curated, _ = curate_record(record(["MODIFY"]), taxonomy=TAXONOMY)
        mutations = {
            "missing transform": lambda stored: stored.pop("transform"),
            "foreign transform": lambda stored: stored.__setitem__(
                "transform", "foreign_transform"
            ),
            "missing version": lambda stored: stored.pop("transform_version"),
            "foreign version": lambda stored: stored.__setitem__(
                "transform_version", "999"
            ),
        }
        for name, mutate in mutations.items():
            with self.subTest(name=name):
                tampered = copy.deepcopy(curated)
                stored = tampered[TAG_PROVENANCE_FIELD]
                mutate(stored)
                again, manifest = curate_record(tampered, taxonomy=TAXONOMY)
                self.assertIsNone(again)
                self.assertEqual(
                    manifest["reason_codes"], [REASON_PROVENANCE_CONFLICT]
                )

        self.assertEqual(
            curated[TAG_PROVENANCE_FIELD]["transform"], TRANSFORM_NAME
        )
        self.assertEqual(
            curated[TAG_PROVENANCE_FIELD]["transform_version"],
            TRANSFORM_VERSION,
        )

    def test_provenance_with_noncanonical_tags_is_a_conflict(self):
        source = record(["decision:modify"])
        source[TAG_PROVENANCE_FIELD] = {
            "taxonomy_version": TAXONOMY.version,
            "containers": [
                {
                    "json_pointer": "/meta/tags",
                    "source_tags": ["MODIFY"],
                    "canonical_tags": ["tokamak"],
                    "mappings": [],
                    "unmapped_tags": [],
                }
            ],
        }
        curated, manifest = curate_record(source, taxonomy=TAXONOMY)

        self.assertIsNone(curated)
        self.assertEqual(manifest["reason_codes"], [REASON_PROVENANCE_CONFLICT])

    def test_provenance_that_no_longer_describes_the_tags_is_a_conflict(self):
        curated, _ = curate_record(record(["MODIFY", "tokamak"]), taxonomy=TAXONOMY)
        curated["meta"]["tags"] = ["decision:accept"]

        again, manifest = curate_record(curated, taxonomy=TAXONOMY)

        self.assertIsNone(again)
        self.assertEqual(manifest["reason_codes"], [REASON_PROVENANCE_CONFLICT])

    def test_provenance_contents_must_recompute_from_source_tags(self):
        curated, _ = curate_record(
            record(["MODIFY", "modify", "tokamak"]), taxonomy=TAXONOMY
        )
        mutations = {
            "source tags": lambda entry: entry.__setitem__("source_tags", ["ACCEPT"]),
            "scalar mapping": lambda entry: entry["mappings"].__setitem__(0, 17),
            "mapping contents": lambda entry: entry["mappings"][0].__setitem__(
                "canonical", "decision:accept"
            ),
            "unmapped tags": lambda entry: entry.__setitem__("unmapped_tags", []),
            "duplicate count": lambda entry: entry.__setitem__(
                "duplicates_collapsed", 0
            ),
        }

        for label, mutate in mutations.items():
            with self.subTest(label=label):
                tampered = copy.deepcopy(curated)
                entry = tampered[TAG_PROVENANCE_FIELD]["containers"][0]
                mutate(entry)
                again, manifest = curate_record(tampered, taxonomy=TAXONOMY)
                self.assertIsNone(again)
                self.assertEqual(
                    manifest["reason_codes"], [REASON_PROVENANCE_CONFLICT]
                )

    def test_provenance_replay_compares_json_numeric_types_strictly(self):
        curated, _ = curate_record(record([1]), taxonomy=TAXONOMY)
        entry = curated[TAG_PROVENANCE_FIELD]["containers"][0]
        entry["source_tags"] = [True]

        again, manifest = curate_record(curated, taxonomy=TAXONOMY)

        self.assertIsNone(again)
        self.assertEqual(manifest["reason_codes"], [REASON_PROVENANCE_CONFLICT])

    def test_provenance_missing_a_container_is_a_conflict(self):
        curated, _ = curate_record(record(["MODIFY"]), taxonomy=TAXONOMY)
        curated["chosen"] = {"meta": {"tags": ["ACCEPT"]}}

        again, manifest = curate_record(curated, taxonomy=TAXONOMY)

        self.assertIsNone(again)
        self.assertEqual(manifest["reason_codes"], [REASON_PROVENANCE_CONFLICT])

    def test_curating_does_not_mutate_the_input_record(self):
        source = record(["MODIFY", "tokamak"])
        original = copy.deepcopy(source)

        curate_record(source, taxonomy=TAXONOMY)

        self.assertEqual(source, original)

    def test_output_hash_is_stable_for_identical_input(self):
        first, first_manifest = curate_record(record(["MODIFY"]), taxonomy=TAXONOMY)
        second, second_manifest = curate_record(record(["MODIFY"]), taxonomy=TAXONOMY)

        self.assertEqual(first, second)
        self.assertEqual(first_manifest["output_hash"], second_manifest["output_hash"])
        self.assertEqual(first_manifest["output_id"], "ttf-r01-001")

    def test_spelling_variants_share_a_tag_but_keep_distinct_provenance(self):
        upper, upper_manifest = curate_record(record(["MODIFY"]), taxonomy=TAXONOMY)
        lower, lower_manifest = curate_record(record(["modify"]), taxonomy=TAXONOMY)

        self.assertEqual(upper["meta"]["tags"], ["decision:modify"])
        self.assertEqual(lower["meta"]["tags"], ["decision:modify"])
        # The curated vocabulary collapses, but the source spelling stays
        # recoverable, so the two records are not byte-identical.
        self.assertNotEqual(upper_manifest["output_hash"], lower_manifest["output_hash"])
        self.assertEqual(
            upper[TAG_PROVENANCE_FIELD]["containers"][0]["source_tags"], ["MODIFY"]
        )
        self.assertEqual(
            lower[TAG_PROVENANCE_FIELD]["containers"][0]["source_tags"], ["modify"]
        )


class IdempotenceTests(unittest.TestCase):
    def test_curating_a_curated_record_is_a_fixpoint(self):
        source = record(["preference_pair", "MODIFY", "modify", "tokamak"])
        once, _ = curate_record(source, taxonomy=TAXONOMY)
        twice, manifest = curate_record(once, taxonomy=TAXONOMY)

        self.assertEqual(twice, once)
        self.assertEqual(manifest["action"], "unchanged")
        self.assertIn(REASON_TAGS_PROVENANCE_REUSED, manifest["reason_codes"])

    def test_reused_provenance_still_names_the_original_tags(self):
        source = record(["MODIFY", "tokamak"])
        once, _ = curate_record(source, taxonomy=TAXONOMY)
        twice, _ = curate_record(once, taxonomy=TAXONOMY)

        self.assertEqual(
            twice[TAG_PROVENANCE_FIELD]["containers"][0]["source_tags"],
            ["MODIFY", "tokamak"],
        )

    def test_canonical_tags_are_stable_without_provenance(self):
        source = record(["preference_pair", "MODIFY", "tokamak"])
        once, _ = curate_record(source, taxonomy=TAXONOMY)
        stripped = copy.deepcopy(once)
        del stripped[TAG_PROVENANCE_FIELD]
        again, _ = curate_record(stripped, taxonomy=TAXONOMY)

        self.assertEqual(again["meta"]["tags"], once["meta"]["tags"])

    def test_jsonl_curation_is_idempotent(self):
        rows = [
            record(["preference_pair", "MODIFY", "tokamak"]),
            record(["cross_ref_ttf-r06-029", "densification_pass_2"]),
            record(["sparse_reward_ticks", "per-tick-reward"]),
        ]
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            first_source = root / "first.jsonl"
            first_source.write_text(
                "".join(json.dumps(row, sort_keys=True) + "\n" for row in rows),
                encoding="utf-8",
            )
            first = curate_jsonl(first_source, TAXONOMY)

            second_source = root / "second.jsonl"
            second_source.write_text(
                "".join(
                    json.dumps(row, sort_keys=True) + "\n" for row in first["records"]
                ),
                encoding="utf-8",
            )
            second = curate_jsonl(second_source, TAXONOMY)

        self.assertEqual(second["records"], first["records"])
        self.assertEqual(
            second["summary"]["canonical_tag_counts"],
            first["summary"]["canonical_tag_counts"],
        )
        self.assertEqual(second["unmapped"], first["unmapped"])


class EntropyTests(unittest.TestCase):
    def test_entropy_matches_the_shannon_definition(self):
        self.assertEqual(vocabulary_entropy(Counter()), 0.0)
        self.assertEqual(vocabulary_entropy(Counter({"a": 5})), 0.0)
        self.assertEqual(vocabulary_entropy(Counter({"a": 1, "b": 1})), 1.0)
        self.assertEqual(
            vocabulary_entropy(Counter({"a": 1, "b": 1, "c": 1, "d": 1})), 2.0
        )
        self.assertAlmostEqual(
            vocabulary_entropy(Counter({"a": 3, "b": 1})),
            -(0.75 * math.log2(0.75) + 0.25 * math.log2(0.25)),
            places=5,
        )

    def test_curation_collapses_a_free_form_surface(self):
        rows = [record(["MODIFY"], id="ttf-r01-001")]
        for index in range(200):
            rows.append(
                record(
                    ["preference_pair", f"one-off-scenario-{index}"],
                    id=f"ttf-r02-{index:03d}",
                )
            )
        with tempfile.TemporaryDirectory() as temporary:
            source = Path(temporary) / "corpus.jsonl"
            source.write_text(
                "".join(json.dumps(row, sort_keys=True) + "\n" for row in rows),
                encoding="utf-8",
            )
            summary = curate_jsonl(source, TAXONOMY)["summary"]

        self.assertEqual(summary["source_unique_tags"], 202)
        self.assertEqual(summary["unmapped_unique_tags"], 200)
        self.assertLessEqual(
            summary["canonical_unique_tags"], len(TAXONOMY.canonical_tags)
        )
        self.assertLess(
            summary["canonical_unique_tags"], summary["source_unique_tags"] / 10
        )
        self.assertLess(
            summary["entropy_bits"]["canonical"], summary["entropy_bits"]["source"]
        )
        self.assertGreater(summary["entropy_bits"]["reduction"], 1.0)
        self.assertEqual(
            summary["entropy_bits"]["reduction"],
            round(
                summary["entropy_bits"]["source"]
                - summary["entropy_bits"]["canonical"],
                6,
            ),
        )


class CurateJsonlTests(unittest.TestCase):
    def test_summary_reports_the_unmapped_surface(self):
        rows = [
            record(["MODIFY", "tokamak"], id="a"),
            record(["tokamak", "nanopore"], id="b"),
        ]
        with tempfile.TemporaryDirectory() as temporary:
            source = Path(temporary) / "corpus.jsonl"
            source.write_text(
                "".join(json.dumps(row, sort_keys=True) + "\n" for row in rows),
                encoding="utf-8",
            )
            result = curate_jsonl(source, TAXONOMY)

        summary = result["summary"]
        self.assertEqual(summary["taxonomy_version"], TAXONOMY.version)
        self.assertEqual(summary["taxonomy_size"], len(TAXONOMY.canonical_tags))
        self.assertEqual(summary["input_records"], 2)
        self.assertEqual(summary["output_records"], 2)
        self.assertEqual(summary["source_tag_uses"], 4)
        self.assertEqual(summary["unmapped_tag_uses"], 3)
        self.assertEqual(summary["unmapped_unique_tags"], 2)
        self.assertEqual(
            result["unmapped"],
            [{"tag": "tokamak", "count": 2}, {"tag": "nanopore", "count": 1}],
        )
        self.assertEqual(summary["rule_uses"]["alias"], 1)
        self.assertEqual(summary["rule_uses"]["transform"], 2)

    def test_nonstring_tag_entries_are_counted_and_preserved(self):
        rows = [record(["MODIFY", 17, None], id="a")]
        with tempfile.TemporaryDirectory() as temporary:
            source = Path(temporary) / "corpus.jsonl"
            source.write_text(
                "".join(json.dumps(row, sort_keys=True) + "\n" for row in rows),
                encoding="utf-8",
            )
            result = curate_jsonl(source, TAXONOMY)

        curated = result["records"][0]
        self.assertEqual(
            curated["meta"]["tags"], [UNMAPPED_MARKER_TAG, "decision:modify"]
        )
        self.assertEqual(result["summary"]["nonstring_tag_uses"], 2)
        self.assertEqual(result["summary"]["source_tag_uses"], 3)
        self.assertEqual(result["summary"]["source_unique_tags"], 3)
        self.assertEqual(result["manifest"][0]["tag_counts"]["source_unique"], 3)
        self.assertEqual(
            result["summary"]["entropy_bits"]["source"],
            round(math.log2(3), 6),
        )
        self.assertEqual(result["summary"]["unmapped_unique_tags"], 2)
        self.assertEqual(
            result["manifest"][0]["unmapped_tags"],
            [17, None],
        )
        tags_in_report = {item["tag"] for item in result["unmapped"]}
        self.assertEqual(tags_in_report, {17, None})
        self.assertEqual(result["manifest"][0]["tag_counts"]["source_uses"], 3)
        self.assertEqual(result["manifest"][0]["tag_counts"]["unmapped_uses"], 2)
        self.assertIn(REASON_TAGS_UNMAPPED, result["manifest"][0]["reason_codes"])
        self.assertEqual(
            curated[TAG_PROVENANCE_FIELD]["containers"][0]["source_tags"],
            ["MODIFY", 17, None],
        )
        reasons = {
            mapping["reason"]
            for mapping in curated[TAG_PROVENANCE_FIELD]["containers"][0]["mappings"]
        }
        self.assertIn(REASON_TAG_NOT_STRING, reasons)

    def test_summary_unmapped_total_includes_nonstring_entries(self):
        rows = [record([17, None], id="a")]
        with tempfile.TemporaryDirectory() as temporary:
            source = Path(temporary) / "corpus.jsonl"
            source.write_text(
                "".join(json.dumps(row, sort_keys=True) + "\n" for row in rows),
                encoding="utf-8",
            )
            summary = curate_jsonl(source, TAXONOMY)["summary"]

        self.assertEqual(summary["nonstring_tag_uses"], 2)
        self.assertEqual(summary["unmapped_tag_uses"], 2)
        self.assertEqual(summary["unmapped_unique_tags"], 2)
        self.assertEqual(
            {item["tag"] for item in summary["unmapped_tags"]},
            {17, None},
        )

    def test_every_retained_record_carries_only_canonical_tags(self):
        rows = [
            record(["MODIFY", "tokamak"], id="a"),
            record(["cross_ref_ttf-r06-029"], id="b"),
            record([], id="c"),
        ]
        with tempfile.TemporaryDirectory() as temporary:
            source = Path(temporary) / "corpus.jsonl"
            source.write_text(
                "".join(json.dumps(row, sort_keys=True) + "\n" for row in rows),
                encoding="utf-8",
            )
            result = curate_jsonl(source, TAXONOMY)

        self.assertEqual(len(result["records"]), 3)
        for curated in result["records"]:
            for tag in curated["meta"]["tags"]:
                self.assertIn(tag, TAXONOMY.canonical_tags)

    def test_invalid_json_and_utf8_are_excluded_deterministically(self):
        with tempfile.TemporaryDirectory() as temporary:
            source = Path(temporary) / "corpus.jsonl"
            source.write_bytes(b"{not json}\n\xff\n")
            result = curate_jsonl(source, TAXONOMY)

        self.assertEqual(result["summary"]["input_records"], 2)
        self.assertEqual(result["summary"]["output_records"], 0)
        self.assertEqual(result["manifest"][0]["reason_codes"], [REASON_INVALID_JSON])
        self.assertEqual(result["manifest"][1]["reason_codes"], [REASON_INVALID_UTF8])

    def test_nonstandard_numeric_constants_are_invalid_json(self):
        with tempfile.TemporaryDirectory() as temporary:
            source = Path(temporary) / "corpus.jsonl"
            source.write_text(
                "".join(
                    f'{{"id":"{index}","metric":{constant},"tags":["MODIFY"]}}\n'
                    for index, constant in enumerate(("NaN", "Infinity", "-Infinity"))
                ),
                encoding="utf-8",
            )
            result = curate_jsonl(source, TAXONOMY)

        self.assertEqual(result["summary"]["output_records"], 0)
        self.assertEqual(
            [entry["reason_codes"] for entry in result["manifest"]],
            [[REASON_INVALID_JSON]] * 3,
        )
        with self.assertRaises(ValueError):
            canonical_json({"metric": math.nan})

    def test_lone_surrogate_is_excluded_without_aborting_the_batch(self):
        with tempfile.TemporaryDirectory() as temporary:
            source = Path(temporary) / "corpus.jsonl"
            source.write_bytes(
                b'{"id":"bad","meta":{"tags":["\\ud800"]}}\n'
                b'{"id":"good","meta":{"tags":["MODIFY"]}}\n'
            )
            result = curate_jsonl(source, TAXONOMY)

        self.assertEqual(result["summary"]["input_records"], 2)
        self.assertEqual(result["summary"]["output_records"], 1)
        self.assertEqual(
            result["manifest"][0]["reason_codes"], [REASON_INVALID_JSON]
        )
        self.assertEqual(result["records"][0]["id"], "good")

    def test_deep_record_is_excluded_without_aborting_the_batch(self):
        depth = 600
        deep_line = (
            '{"id":"deep","payload":'
            + "[" * depth
            + "0"
            + "]" * depth
            + "}\n"
        )
        good_line = json.dumps(record(["MODIFY"], id="good")) + "\n"
        with tempfile.TemporaryDirectory() as temporary:
            source = Path(temporary) / "corpus.jsonl"
            source.write_text(deep_line + good_line, encoding="utf-8")
            result = curate_jsonl(source, TAXONOMY)

        self.assertEqual(result["summary"]["input_records"], 2)
        self.assertEqual(result["summary"]["output_records"], 1)
        self.assertEqual(result["summary"]["excluded_records"], 1)
        self.assertEqual(
            result["manifest"][0]["reason_codes"], [REASON_RECORD_TOO_DEEP]
        )
        self.assertEqual(result["records"][0]["id"], "good")

    def test_manifest_carries_source_identity_for_every_line(self):
        with tempfile.TemporaryDirectory() as temporary:
            source = Path(temporary) / "corpus.jsonl"
            source.write_text(
                json.dumps(record(["MODIFY"]), sort_keys=True) + "\n", encoding="utf-8"
            )
            result = curate_jsonl(source, TAXONOMY)

        entry = result["manifest"][0]
        self.assertEqual(entry["source_path"], str(source))
        self.assertEqual(entry["source_line"], 1)
        self.assertEqual(len(entry["source_hash"]), 64)
        self.assertEqual(entry["transform"], "tag_taxonomy")
        self.assertEqual(entry["transform_version"], "1")
        self.assertEqual(entry["taxonomy_version"], TAXONOMY.version)


class CliTests(unittest.TestCase):
    def _source(self, root):
        source = root / "corpus.jsonl"
        source.write_text(
            json.dumps(record(["MODIFY", "tokamak"]), sort_keys=True) + "\n",
            encoding="utf-8",
        )
        return source

    def test_cli_writes_new_files_and_refuses_clobber(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = self._source(root)
            output = root / "new" / "tags.jsonl"
            manifest = root / "new" / "manifest.jsonl"
            unmapped = root / "new" / "unmapped.jsonl"
            command = [
                sys.executable,
                str(PIPELINES / "curate_tags.py"),
                str(source),
                "--output-jsonl",
                str(output),
                "--manifest-jsonl",
                str(manifest),
                "--unmapped-jsonl",
                str(unmapped),
            ]

            first = subprocess.run(command, capture_output=True, text=True, check=False)
            second = subprocess.run(command, capture_output=True, text=True, check=False)

            self.assertEqual(first.returncode, 0, first.stderr)
            self.assertNotEqual(second.returncode, 0)
            self.assertEqual(len(output.read_text().splitlines()), 1)
            self.assertEqual(len(manifest.read_text().splitlines()), 1)
            self.assertEqual(
                json.loads(unmapped.read_text()), {"tag": "tokamak", "count": 1}
            )
            summary = json.loads(first.stdout)
            self.assertEqual(summary["unmapped_unique_tags"], 1)

    def test_cli_preflights_all_destinations_before_writing(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = self._source(root)
            output = root / "new" / "tags.jsonl"
            manifest = root / "existing-manifest.jsonl"
            manifest.write_text("sentinel\n", encoding="utf-8")

            result = subprocess.run(
                [
                    sys.executable,
                    str(PIPELINES / "curate_tags.py"),
                    str(source),
                    "--output-jsonl",
                    str(output),
                    "--manifest-jsonl",
                    str(manifest),
                ],
                capture_output=True,
                text=True,
                check=False,
            )

            self.assertNotEqual(result.returncode, 0)
            self.assertFalse(output.exists())
            self.assertEqual(manifest.read_text(), "sentinel\n")

    def test_destination_race_preserves_competitor_and_rolls_back(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            output = root / "output.jsonl"
            manifest = root / "manifest.jsonl"
            _preflight_destinations([output, manifest])
            manifest.write_text("competitor\n", encoding="utf-8")

            with self.assertRaises(FileExistsError):
                _write_destinations([(output, [{"id": "x"}]), (manifest, [])])

            self.assertFalse(output.exists())
            self.assertEqual(manifest.read_text(encoding="utf-8"), "competitor\n")

    def test_cli_rejects_destinations_that_contain_one_another(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = self._source(root)
            output = root / "artifact"
            manifest = output / "manifest.jsonl"

            result = subprocess.run(
                [
                    sys.executable,
                    str(PIPELINES / "curate_tags.py"),
                    str(source),
                    "--output-jsonl",
                    str(output),
                    "--manifest-jsonl",
                    str(manifest),
                ],
                capture_output=True,
                text=True,
                check=False,
            )

            self.assertNotEqual(result.returncode, 0)
            self.assertFalse(output.exists())

    def test_cli_refuses_any_destination_under_outputs_raw(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = self._source(root)
            output = root / "outputs" / "raw" / "forbidden.jsonl"

            result = subprocess.run(
                [
                    sys.executable,
                    str(PIPELINES / "curate_tags.py"),
                    str(source),
                    "--output-jsonl",
                    str(output),
                ],
                capture_output=True,
                text=True,
                check=False,
            )

            self.assertNotEqual(result.returncode, 0)
            self.assertFalse(output.exists())

    def test_cli_refuses_a_lexical_raw_path_through_a_symlink(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = self._source(root)
            external = root / "external-raw"
            external.mkdir()
            raw = root / "outputs" / "raw"
            raw.parent.mkdir()
            raw.symlink_to(external, target_is_directory=True)
            output = raw / "forbidden.jsonl"

            result = subprocess.run(
                [
                    sys.executable,
                    str(PIPELINES / "curate_tags.py"),
                    str(source),
                    "--output-jsonl",
                    str(output),
                ],
                capture_output=True,
                text=True,
                check=False,
            )

            self.assertNotEqual(result.returncode, 0)
            self.assertFalse((external / "forbidden.jsonl").exists())

    def test_cli_refuses_to_overwrite_its_source(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = self._source(root)
            before = source.read_text()

            result = subprocess.run(
                [
                    sys.executable,
                    str(PIPELINES / "curate_tags.py"),
                    str(source),
                    "--output-jsonl",
                    str(source),
                ],
                capture_output=True,
                text=True,
                check=False,
            )

            self.assertNotEqual(result.returncode, 0)
            self.assertEqual(source.read_text(), before)

    def test_cli_rejects_an_invalid_taxonomy(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = self._source(root)
            taxonomy = root / "broken.json"
            taxonomy.write_text("{", encoding="utf-8")

            result = subprocess.run(
                [
                    sys.executable,
                    str(PIPELINES / "curate_tags.py"),
                    str(source),
                    "--taxonomy",
                    str(taxonomy),
                ],
                capture_output=True,
                text=True,
                check=False,
            )

            self.assertNotEqual(result.returncode, 0)

    def test_cli_reports_regex_compile_failures_without_tracebacks(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = self._source(root)

            for exception_name, pattern in INVALID_REGEX_PATTERNS:
                documents = (
                    (
                        "canonical_tag_pattern",
                        minimal_taxonomy(canonical_tag_pattern=pattern),
                    ),
                    (
                        "pattern_rule",
                        minimal_taxonomy(
                            pattern_rules=[
                                {
                                    "id": "invalid_regex",
                                    "tag": "decision:accept",
                                    "pattern": pattern,
                                }
                            ]
                        ),
                    ),
                )
                for site, document in documents:
                    with self.subTest(exception=exception_name, site=site):
                        taxonomy = root / (
                            f"{exception_name.replace('.', '_')}-{site}.json"
                        )
                        taxonomy.write_text(json.dumps(document), encoding="utf-8")
                        result = subprocess.run(
                            [
                                sys.executable,
                                str(PIPELINES / "curate_tags.py"),
                                str(source),
                                "--taxonomy",
                                str(taxonomy),
                            ],
                            capture_output=True,
                            text=True,
                            check=False,
                        )

                        self.assertEqual(result.returncode, 2, result.stderr)
                        self.assertIn("not a valid regex", result.stderr)
                        self.assertNotIn("Traceback", result.stderr)

    def test_cli_rejects_unsafe_regexes_without_writing_or_tracebacks(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = self._source(root)
            cases = []
            for unsafe_name, pattern in UNSAFE_LINEAR_REGEX_PATTERNS:
                cases.extend(
                    [
                        (
                            f"{unsafe_name}-canonical",
                            minimal_taxonomy(canonical_tag_pattern=pattern),
                        ),
                        (
                            f"{unsafe_name}-rule",
                            minimal_taxonomy(
                                pattern_rules=[
                                    {
                                        "id": "unsafe_regex",
                                        "tag": "decision:accept",
                                        "pattern": pattern,
                                    }
                                ]
                            ),
                        ),
                    ]
                )
            cases.append(
                (
                    "fast-then-pathological",
                    minimal_taxonomy(
                        pattern_rules=[
                            {
                                "id": "a_fast",
                                "tag": "decision:accept",
                                "pattern": "^a+x$",
                            },
                            {
                                "id": "z_pathological",
                                "tag": "decision:accept",
                                "pattern": "^(a+)+$",
                            },
                        ]
                    ),
                )
            )

            for index, (label, document) in enumerate(cases):
                with self.subTest(case=label):
                    taxonomy = root / f"unsafe-{index}.json"
                    output = root / f"unsafe-output-{index}.jsonl"
                    taxonomy.write_text(json.dumps(document), encoding="utf-8")
                    result = subprocess.run(
                        [
                            sys.executable,
                            str(PIPELINES / "curate_tags.py"),
                            str(source),
                            "--taxonomy",
                            str(taxonomy),
                            "--output-jsonl",
                            str(output),
                        ],
                        capture_output=True,
                        text=True,
                        check=False,
                    )

                    self.assertEqual(result.returncode, 2, result.stderr)
                    self.assertIn(
                        "supported linear-time regex subset", result.stderr
                    )
                    self.assertNotIn("Traceback", result.stderr)
                    self.assertFalse(output.exists())

    def test_cli_rejects_grouped_optionals_before_matching_the_source(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = root / "grouped-optionals-source.jsonl"
            source.write_text(
                json.dumps(record(["a" * GROUPED_OPTIONAL_REPEATS])) + "\n",
                encoding="utf-8",
            )

            for index, (group_kind, pattern) in enumerate(
                GROUPED_OPTIONAL_REGEX_PATTERNS
            ):
                with self.subTest(group=group_kind):
                    taxonomy = root / f"grouped-optionals-{index}.json"
                    output = root / f"grouped-optionals-{index}.jsonl"
                    taxonomy.write_text(
                        json.dumps(
                            minimal_taxonomy(
                                pattern_rules=[
                                    {
                                        "id": group_kind,
                                        "tag": "decision:accept",
                                        "pattern": pattern,
                                    }
                                ]
                            )
                        ),
                        encoding="utf-8",
                    )

                    result = subprocess.run(
                        [
                            sys.executable,
                            str(PIPELINES / "curate_tags.py"),
                            str(source),
                            "--taxonomy",
                            str(taxonomy),
                            "--output-jsonl",
                            str(output),
                        ],
                        capture_output=True,
                        text=True,
                        check=False,
                        timeout=3,
                    )

                    self.assertEqual(result.returncode, 2, result.stderr)
                    self.assertEqual(result.stdout, "")
                    self.assertIn(
                        "supported linear-time regex subset", result.stderr
                    )
                    self.assertNotIn("Traceback", result.stderr)
                    self.assertFalse(output.exists())


class TagCliInProcessTests(unittest.TestCase):
    def test_main_writes_outputs_and_rejects_unsafe_destinations(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = root / "in.jsonl"
            source.write_text(
                json.dumps(record(["MODIFY"])) + "\n", encoding="utf-8"
            )
            output = root / "out.jsonl"
            manifest = root / "man.jsonl"
            unmapped = root / "unm.jsonl"
            stdout = io.StringIO()
            with contextlib.redirect_stdout(stdout):
                code = curate_tags.main(
                    [
                        str(source),
                        "--output-jsonl",
                        str(output),
                        "--manifest-jsonl",
                        str(manifest),
                        "--unmapped-jsonl",
                        str(unmapped),
                    ]
                )
            self.assertEqual(code, 0)
            self.assertTrue(output.is_file())
            self.assertTrue(manifest.is_file())
            self.assertTrue(unmapped.is_file())
            self.assertIn("input_records", json.loads(stdout.getvalue()))

            with contextlib.redirect_stderr(io.StringIO()), self.assertRaises(
                SystemExit
            ):
                curate_tags.main([str(source), "--output-jsonl", str(source)])
            with contextlib.redirect_stderr(io.StringIO()), self.assertRaises(
                SystemExit
            ):
                curate_tags.main([str(source), "--output-jsonl", str(output)])
            nested = root / "nested"
            with contextlib.redirect_stderr(io.StringIO()), self.assertRaises(
                SystemExit
            ):
                curate_tags.main(
                    [
                        str(source),
                        "--output-jsonl",
                        str(nested / "a.jsonl"),
                        "--manifest-jsonl",
                        str(nested),
                    ]
                )
            raw = root / "outputs" / "raw" / "x.jsonl"
            with contextlib.redirect_stderr(io.StringIO()), self.assertRaises(
                SystemExit
            ):
                curate_tags.main([str(source), "--output-jsonl", str(raw)])
            missing_taxonomy = root / "missing-taxonomy.json"
            with contextlib.redirect_stderr(io.StringIO()), self.assertRaises(
                SystemExit
            ):
                curate_tags.main(
                    [
                        str(source),
                        "--taxonomy",
                        str(missing_taxonomy),
                        "--output-jsonl",
                        str(root / "fresh.jsonl"),
                    ]
                )
            missing_source = root / "nope.jsonl"
            stderr = io.StringIO()
            with contextlib.redirect_stderr(stderr), self.assertRaises(SystemExit):
                curate_tags.main([str(missing_source)])
            self.assertNotIn("Traceback", stderr.getvalue())
            curate_tags._unlink_created_file(root / "absent.jsonl", (0, 0))
            with self.assertRaisesRegex(ValueError, "distinct"):
                curate_tags._preflight_destinations([output, output])

    def test_load_taxonomy_wraps_excessive_nesting(self):
        with mock.patch("curate_tags.json.loads", side_effect=RecursionError):
            with self.assertRaises(TagTaxonomyError):
                load_taxonomy(DEFAULT_TAXONOMY_PATH)

    def test_unmapped_counters_keep_distinct_json_types(self):
        rows = [record(["{}", {}, True, 1, 1.0], id="a")]
        with tempfile.TemporaryDirectory() as temporary:
            source = Path(temporary) / "corpus.jsonl"
            source.write_text(
                "".join(json.dumps(row, sort_keys=True) + "\n" for row in rows),
                encoding="utf-8",
            )
            result = curate_jsonl(source, TAXONOMY)
        tags = [item["tag"] for item in result["unmapped"]]
        by_identity = {
            (type(tag).__name__, canonical_json(tag)): tag for tag in tags
        }
        self.assertEqual(len(by_identity), 5)
        self.assertEqual(by_identity[("str", canonical_json("{}"))], "{}")
        self.assertEqual(by_identity[("dict", canonical_json({}))], {})
        self.assertIs(by_identity[("bool", canonical_json(True))], True)
        self.assertEqual(by_identity[("int", canonical_json(1))], 1)
        self.assertEqual(by_identity[("float", canonical_json(1.0))], 1.0)
        self.assertEqual(result["summary"]["unmapped_unique_tags"], 5)
        self.assertEqual(result["summary"]["source_unique_tags"], 5)

    def test_cli_reports_write_parent_not_a_directory(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = root / "in.jsonl"
            source.write_text(json.dumps(record(["MODIFY"])) + "\n", encoding="utf-8")
            blocker = root / "notdir"
            blocker.write_text("file", encoding="utf-8")
            dest = blocker / "out.jsonl"
            stderr = io.StringIO()
            with contextlib.redirect_stderr(stderr), self.assertRaises(SystemExit):
                curate_tags.main([str(source), "--output-jsonl", str(dest)])
            self.assertNotIn("Traceback", stderr.getvalue())


if __name__ == "__main__":
    unittest.main()
