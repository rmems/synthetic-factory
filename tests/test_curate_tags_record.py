import copy
import json
import sys
import tempfile
import unittest
from pathlib import Path

_TESTS = Path(__file__).resolve().parent
_PIPELINES = _TESTS.parent / "pipelines"
for _path in (_TESTS, _PIPELINES):
    if str(_path) not in sys.path:
        sys.path.insert(0, str(_path))

import curate_tags  # noqa: E402
from tag_test_support import (  # noqa: E402
    REASON_PROVENANCE_CONFLICT,
    REASON_RECORD_NOT_OBJECT,
    REASON_TAGS_DEDUPLICATED,
    REASON_TAGS_MAPPED,
    REASON_TAGS_NOT_LIST,
    REASON_TAGS_PROVENANCE_REUSED,
    REASON_TAGS_UNMAPPED,
    TAG_PROVENANCE_FIELD,
    TAXONOMY,
    TRANSFORM_NAME,
    TRANSFORM_VERSION,
    UNMAPPED_MARKER_TAG,
    curate_jsonl,
    curate_record,
    record,
)


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


class RecordSidecarTests(unittest.TestCase):
    def test_empty_tag_container_records_a_modification_reason(self):
        curated, manifest = curate_record(record([]), taxonomy=TAXONOMY)
        self.assertEqual(manifest["action"], "modified")
        self.assertTrue(manifest["reason_codes"])
        self.assertIn(curate_tags.REASON_TAGS_PROVENANCE_WRITTEN, manifest["reason_codes"])
        self.assertIn(TAG_PROVENANCE_FIELD, curated)

    def test_empty_provenance_sidecar_is_a_conflict_not_a_delete(self):
        source = record(["MODIFY"])
        source[TAG_PROVENANCE_FIELD] = {
            "taxonomy_version": TAXONOMY.version,
            "transform": curate_tags.TRANSFORM_NAME,
            "transform_version": curate_tags.TRANSFORM_VERSION,
            "containers": [],
        }
        curated, manifest = curate_record(source, taxonomy=TAXONOMY)
        self.assertIsNone(curated)
        self.assertIn(REASON_PROVENANCE_CONFLICT, manifest["reason_codes"])


if __name__ == "__main__":
    unittest.main()
