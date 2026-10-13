"""JSON Pointer and semantic-identity branches of the native and facade adapters.

``compose_curated_source_pointers`` is the native implementation and
``compose_curated_identity_facade_semantics`` is the live facade adapter that
``compose_curated`` re-exports under the historically pinned private names.
Each behaviour is asserted against both so the two cannot drift apart.
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

TESTS = Path(__file__).resolve().parent
for _path in (TESTS, TESTS.parent / "pipelines"):
    if str(_path) not in sys.path:
        sys.path.insert(0, str(_path))

import compose_curated
import compose_curated_source_pointers as pointers
from compose_contract import REASON_DUPLICATE_CURATED_RECORD, ComposeDecision, ComposeError

IMPLEMENTATIONS = {
    "native": {
        "identity_owner": pointers.identity_owner,
        "pop": pointers.pop_json_pointer,
        "legacy_paths": pointers.mapped_legacy_id_paths,
    },
    "facade": {
        "identity_owner": compose_curated._identity_owner,
        "pop": compose_curated._pop_json_pointer,
        "legacy_paths": compose_curated._mapped_legacy_id_paths,
    },
}

ID_MAPPINGS: tuple = (
    "skip",
    {"original_ids": [{"path": "/chosen/legacy"}, {"path": "/meta/legacy"}]},
)
ID_DETAIL = {
    "original_ids": [{"path": "/meta/legacy"}, {"path": 7}, "skip"],
    "id_mappings": list(ID_MAPPINGS),
}


def _retained(record: dict, stages=()) -> ComposeDecision:
    return ComposeDecision("retained", record, (), tuple(stages), None, record.get("id"))


class PointerCase(unittest.TestCase):
    @staticmethod
    def each(name: str) -> list:
        """The native and facade spellings of one pointer helper."""

        return [implementation[name] for implementation in IMPLEMENTATIONS.values()]


class IdentityOwnerTests(PointerCase):
    def test_root_pointer_names_the_record(self):
        record = {"id": "r"}
        for owner in self.each("identity_owner"):
            self.assertIs(owner(record, "/"), record)

    def test_non_pointer_has_no_owner(self):
        for owner in self.each("identity_owner"):
            self.assertIsNone(owner({"chosen": {}}, "chosen"))

    def test_escaped_tokens_reach_a_nested_mapping(self):
        record = {"a/b": {"c~d": {"id": "x"}}}
        for owner in self.each("identity_owner"):
            self.assertEqual(owner(record, "/a~1b/c~0d"), {"id": "x"})

    def test_scalar_along_the_path_has_no_owner(self):
        for owner in self.each("identity_owner"):
            self.assertIsNone(owner({"chosen": "text"}, "/chosen/meta"))

    def test_scalar_target_has_no_owner(self):
        for owner in self.each("identity_owner"):
            self.assertIsNone(owner({"chosen": {"id": "x"}}, "/chosen/id"))


class PopPointerTests(PointerCase):
    def test_non_pointer_leaves_the_record_alone(self):
        for pop in self.each("pop"):
            record = {"id": "r"}
            pop(record, "id")
            self.assertEqual(record, {"id": "r"})

    def test_scalar_along_the_path_leaves_the_record_alone(self):
        for pop in self.each("pop"):
            record = {"meta": "text"}
            pop(record, "/meta/legacy/id")
            self.assertEqual(record, {"meta": "text"})

    def test_empty_final_token_leaves_the_record_alone(self):
        for pop in self.each("pop"):
            record = {"meta": {"": 1}}
            pop(record, "/meta/")
            self.assertEqual(record, {"meta": {"": 1}})

    def test_nested_field_is_removed(self):
        for pop in self.each("pop"):
            record = {"meta": {"legacy": "x", "keep": 1}}
            pop(record, "/meta/legacy")
            self.assertEqual(record, {"meta": {"keep": 1}})


class LegacyPathTests(PointerCase):
    def test_non_mapping_detail_has_no_paths(self):
        for paths in self.each("legacy_paths"):
            self.assertEqual(paths(None), ())

    def test_non_list_mappings_keep_only_top_level_paths(self):
        for paths in self.each("legacy_paths"):
            detail = {"original_ids": [{"path": "/a"}], "id_mappings": {"original_ids": []}}
            self.assertEqual(paths(detail), ("/a",))

    def test_mapping_paths_are_collected_once_in_order(self):
        for paths in self.each("legacy_paths"):
            self.assertEqual(paths(ID_DETAIL), ("/meta/legacy", "/chosen/legacy"))

    def test_non_list_original_ids_have_no_paths(self):
        self.assertEqual(pointers.original_id_paths({"path": "/a"}), [])
        self.assertEqual(compose_curated._original_id_paths({"path": "/a"}), [])


class FacadeSemanticTests(unittest.TestCase):
    def test_assigned_ids_and_legacy_paths_are_stripped(self):
        semantic = {
            "id": "assigned",
            "meta": {"legacy": "old", "keep": 1},
            "chosen": {"id": "foreign", "legacy": "old"},
        }
        detail = dict(ID_DETAIL)
        detail["id_mappings"] = [
            *ID_MAPPINGS,
            {"owner_path": "/", "output_id": "assigned"},
            {"owner_path": "/chosen", "output_id": "other"},
            {"owner_path": "/missing", "output_id": "x"},
        ]

        compose_curated._strip_assigned_ids(semantic, detail)

        self.assertEqual(semantic, {"meta": {"keep": 1}, "chosen": {"id": "foreign"}})

    def test_non_dict_detail_strips_nothing(self):
        semantic = {"id": "assigned"}

        compose_curated._strip_assigned_ids(semantic, None)

        self.assertEqual(semantic, {"id": "assigned"})

    def test_provenance_labels_are_stripped_from_mapping_meta_only(self):
        semantic = {
            "meta": {"factory": "f", "round": 1, "tags": ["t"]},
            "chosen": {"meta": "not a mapping"},
        }

        compose_curated._strip_provenance_labels(semantic)

        self.assertEqual(semantic, {"meta": {"tags": ["t"]}, "chosen": {"meta": "not a mapping"}})

    def test_missing_record_cannot_be_hashed(self):
        decision = ComposeDecision("excluded", None, (), (), None, None)

        with self.assertRaises(ComposeError) as caught:
            compose_curated._post_transform_semantic_sha256(decision)

        self.assertEqual(str(caught.exception), "cannot hash a missing curated record")

    def test_provenance_only_differences_hash_identically(self):
        first = _retained({"goal": "g", "meta": {"factory": "a", "round": 1}})
        second = _retained({"goal": "g", "meta": {"factory": "b", "round": 2}})

        self.assertEqual(
            compose_curated._post_transform_semantic_sha256(first),
            compose_curated._post_transform_semantic_sha256(second),
        )


class FacadeDeduplicationTests(unittest.TestCase):
    @staticmethod
    def dedup(decision, seen, line=2):
        return compose_curated._deduplicate_curated_record(
            decision, source_path="f/batch-r01.jsonl", source_line=line, seen_curated_semantics=seen
        )

    def test_missing_index_returns_the_decision(self):
        decision = _retained({"goal": "g"})

        self.assertIs(self.dedup(decision, None), decision)

    def test_excluded_decision_is_not_indexed(self):
        decision = ComposeDecision("excluded", None, ("x",), (), None, None)
        seen: dict = {}

        self.assertIs(self.dedup(decision, seen), decision)
        self.assertEqual(seen, {})

    def test_first_record_is_indexed_and_retained(self):
        decision = _retained({"goal": "g"})
        seen: dict = {}

        self.assertIs(self.dedup(decision, seen, line=1), decision)
        self.assertEqual(list(seen.values()), [("f/batch-r01.jsonl", 1)])

    def test_converging_record_is_excluded_with_first_coordinates(self):
        seen: dict = {}
        self.dedup(_retained({"goal": "g", "meta": {"round": 1}}), seen, line=1)

        duplicate = self.dedup(_retained({"goal": "g", "meta": {"round": 2}}), seen, line=2)

        self.assertEqual(
            (duplicate.action, duplicate.record, duplicate.reason_codes),
            ("excluded", None, (REASON_DUPLICATE_CURATED_RECORD,)),
        )
        evidence = duplicate.stages[-1]
        self.assertEqual(evidence["lane"], "post_transform_dedup")
        self.assertEqual(
            (evidence["first_source_path"], evidence["first_source_line"]),
            ("f/batch-r01.jsonl", 1),
        )

    def test_excluded_source_line_carries_its_reason_and_detail(self):
        decision = compose_curated._excluded_source_line("compose.invalid_json", {"error": "e"})

        self.assertEqual(decision.reason_codes, ("compose.invalid_json",))
        self.assertEqual(decision.stages[0]["lane"], "source")
        self.assertEqual(decision.stages[0]["detail"], {"error": "e"})


if __name__ == "__main__":
    unittest.main()
