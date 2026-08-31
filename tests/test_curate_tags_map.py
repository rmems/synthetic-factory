import sys
import unittest
from pathlib import Path

_TESTS = Path(__file__).resolve().parent
_PIPELINES = _TESTS.parent / "pipelines"
for _path in (_TESTS, _PIPELINES):
    if str(_path) not in sys.path:
        sys.path.insert(0, str(_path))

from tag_test_support import (  # noqa: E402
    REASON_TAG_ALIAS,
    REASON_TAG_CANONICAL,
    REASON_TAG_EMPTY,
    REASON_TAG_MAPPING_AMBIGUOUS,
    REASON_TAG_NOT_STRING,
    REASON_TAG_PATTERN,
    REASON_TAG_UNMAPPED,
    REASON_TAGS_PROVENANCE_REUSED,
    REASON_TAGS_UNMAPPED,
    TAG_PROVENANCE_FIELD,
    TAXONOMY,
    UNMAPPED_MARKER_TAG,
    Taxonomy,
    curate_record,
    map_tags,
    minimal_taxonomy,
    record,
)


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



if __name__ == "__main__":
    unittest.main()
