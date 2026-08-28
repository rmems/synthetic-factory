import hashlib
import json
import math
import sys
import tempfile
import unittest
from collections import Counter
from pathlib import Path

_TESTS = Path(__file__).resolve().parent
_PIPELINES = _TESTS.parent / "pipelines"
for _path in (_TESTS, _PIPELINES):
    if str(_path) not in sys.path:
        sys.path.insert(0, str(_path))

from tag_test_support import (  # noqa: E402
    REASON_INVALID_JSON,
    REASON_INVALID_UTF8,
    REASON_RECORD_TOO_DEEP,
    REASON_TAG_NOT_STRING,
    REASON_TAGS_UNMAPPED,
    TAG_PROVENANCE_FIELD,
    TAXONOMY,
    UNMAPPED_MARKER_TAG,
    canonical_json,
    curate_jsonl,
    record,
    vocabulary_entropy,
)


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

    def test_duplicate_record_keys_are_invalid_json(self):
        with tempfile.TemporaryDirectory() as temporary:
            source = Path(temporary) / "corpus.jsonl"
            source.write_text(
                '{"id":"a","tags":["MODIFY"],"tags":["REJECT"]}\n',
                encoding="utf-8",
            )
            result = curate_jsonl(source, TAXONOMY)
        self.assertEqual(result["summary"]["output_records"], 0)
        self.assertIn(REASON_INVALID_JSON, result["manifest"][0]["reason_codes"])

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



class JsonlIdentityTests(unittest.TestCase):
    def test_source_hash_keeps_payload_carriage_returns(self):
        with tempfile.TemporaryDirectory() as temporary:
            source = Path(temporary) / "corpus.jsonl"
            payload = b'{"id":"cr","meta":{"tags":["MODIFY"]}}\r\r\n'
            source.write_bytes(payload)
            result = curate_jsonl(source, TAXONOMY)
        expected = hashlib.sha256(b'{"id":"cr","meta":{"tags":["MODIFY"]}}\r').hexdigest()
        self.assertEqual(result["manifest"][0]["source_hash"], expected)

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


if __name__ == "__main__":
    unittest.main()
