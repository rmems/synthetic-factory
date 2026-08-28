import os
import sys
import unittest
from pathlib import Path

_TESTS = Path(__file__).resolve().parent
_PIPELINES = _TESTS.parent / "pipelines"
for _path in (_TESTS, _PIPELINES):
    if str(_path) not in sys.path:
        sys.path.insert(0, str(_path))

from tag_jsonutil import display_source_path  # noqa: E402
from tag_test_support import TAXONOMY, normalize_tag  # noqa: E402


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


class SourcePathSpellingTests(unittest.TestCase):
    def test_utf8_path_keeps_non_ascii_spelling(self):
        path = Path("/tmp/fábrica/café.jsonl")
        self.assertEqual(display_source_path(path), "/tmp/fábrica/café.jsonl")
        latin1_corruption = os.fsencode(os.fspath(path)).decode("latin-1")
        self.assertNotEqual(display_source_path(path), latin1_corruption)

    def test_non_utf8_bytes_stay_distinct_via_latin1(self):
        raw = b"/tmp/caf\xe9.jsonl"
        path = Path(os.fsdecode(raw))
        self.assertEqual(display_source_path(path), raw.decode("latin-1"))


if __name__ == "__main__":
    unittest.main()
