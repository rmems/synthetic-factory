import copy
import json
import math
import subprocess
import sys
import tempfile
import unittest
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PIPELINES = ROOT / "pipelines"
if str(PIPELINES) not in sys.path:
    sys.path.insert(0, str(PIPELINES))

from curate_tags import (  # noqa: E402
    DEFAULT_TAXONOMY_PATH,
    REASON_INVALID_JSON,
    REASON_INVALID_UTF8,
    REASON_PROVENANCE_CONFLICT,
    REASON_RECORD_NOT_OBJECT,
    REASON_TAG_ALIAS,
    REASON_TAG_CANONICAL,
    REASON_TAG_EMPTY,
    REASON_TAG_NOT_STRING,
    REASON_TAG_PATTERN,
    REASON_TAG_UNMAPPED,
    REASON_TAGS_DEDUPLICATED,
    REASON_TAGS_MAPPED,
    REASON_TAGS_NOT_LIST,
    REASON_TAGS_PROVENANCE_REUSED,
    REASON_TAGS_UNMAPPED,
    TAG_PROVENANCE_FIELD,
    UNMAPPED_MARKER_TAG,
    Taxonomy,
    TagTaxonomyError,
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

    def test_canonical_tag_outside_its_facet_is_rejected(self):
        document = minimal_taxonomy()
        document["facets"][0]["terms"][0]["tag"] = "verdict:accept"
        with self.assertRaises(TagTaxonomyError):
            Taxonomy(document, source="<test>")

    def test_taxonomy_without_unmapped_marker_is_rejected(self):
        document = minimal_taxonomy()
        document["facets"] = document["facets"][:1]
        document["transform_emitted_tags"] = []
        with self.assertRaises(TagTaxonomyError):
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
        for tag in sorted(TAXONOMY.canonical_tags):
            mapping = TAXONOMY.map_tag(tag)
            self.assertEqual(mapping["canonical"], tag)
            self.assertEqual(mapping["reason"], REASON_TAG_CANONICAL)

    def test_alias_pattern_and_unmapped_decisions_are_explained(self):
        alias = TAXONOMY.map_tag("preference_pair")
        self.assertEqual(alias["canonical"], "kind:preference_pair")
        self.assertEqual(alias["reason"], REASON_TAG_ALIAS)
        self.assertEqual(alias["rule"], "alias")

        pattern = TAXONOMY.map_tag("cross_ref_ttf-r06-029")
        self.assertEqual(pattern["canonical"], "link:cross_reference")
        self.assertEqual(pattern["reason"], REASON_TAG_PATTERN)
        self.assertEqual(pattern["rule"], "pattern:cross_reference")

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
        self.assertEqual(result["summary"]["unmapped_unique_tags"], 0)
        self.assertEqual(
            curated[TAG_PROVENANCE_FIELD]["containers"][0]["source_tags"],
            ["MODIFY", 17, None],
        )
        reasons = {
            mapping["reason"]
            for mapping in curated[TAG_PROVENANCE_FIELD]["containers"][0]["mappings"]
        }
        self.assertIn(REASON_TAG_NOT_STRING, reasons)

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


if __name__ == "__main__":
    unittest.main()
