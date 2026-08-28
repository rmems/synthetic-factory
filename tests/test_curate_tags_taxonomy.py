import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

_TESTS = Path(__file__).resolve().parent
_PIPELINES = _TESTS.parent / "pipelines"
for _path in (_TESTS, _PIPELINES):
    if str(_path) not in sys.path:
        sys.path.insert(0, str(_path))

from tag_test_support import (  # noqa: E402
    DEFAULT_TAXONOMY_PATH,
    GROUPED_OPTIONAL_REGEX_PATTERNS,
    INVALID_REGEX_PATTERNS,
    MAX_CANONICAL_TAGS,
    REGEX_RESOURCE_EXCEPTION_TYPES,
    SAFE_GROUP_BOUNDARY_CASES,
    TAXONOMY,
    UNMAPPED_MARKER_TAG,
    UNSAFE_LINEAR_REGEX_PATTERNS,
    Taxonomy,
    TagTaxonomyError,
    load_taxonomy,
    minimal_taxonomy,
    normalize_tag,
)


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
            ("parser", "tag_regex._re_parser.parse"),
            ("compiler", "tag_regex.re.compile"),
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

    def test_taxonomy_rejects_extra_transform_emitted_tags(self):
        document = minimal_taxonomy(
            transform_emitted_tags=[UNMAPPED_MARKER_TAG, "decision:accept"]
        )
        with self.assertRaisesRegex(TagTaxonomyError, "cannot emit"):
            Taxonomy(document, source="<test>")

    def test_taxonomy_rejects_omitted_normalization(self):
        document = minimal_taxonomy()
        del document["normalization"]
        with self.assertRaisesRegex(TagTaxonomyError, "normalization must declare"):
            Taxonomy(document, source="<test>")

    def test_taxonomy_rejects_foreign_normalization_steps(self):
        document = minimal_taxonomy(normalization={"steps": ["lowercase"]})
        with self.assertRaisesRegex(
            TagTaxonomyError, "normalization steps must match"
        ):
            Taxonomy(document, source="<test>")

    def test_loading_a_non_object_document_is_rejected(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "taxonomy.json"
            path.write_text("[]", encoding="utf-8")
            with self.assertRaises(TagTaxonomyError):
                load_taxonomy(path)


    def test_load_taxonomy_wraps_excessive_nesting(self):
        with mock.patch("tag_taxonomy.json.loads", side_effect=RecursionError):
            with self.assertRaises(TagTaxonomyError):
                load_taxonomy(DEFAULT_TAXONOMY_PATH)



if __name__ == "__main__":
    unittest.main()
