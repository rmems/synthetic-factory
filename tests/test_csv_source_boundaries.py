"""Source projections never authenticate unproven module-time behavior."""

import hashlib
import unittest
from unittest import mock

from pipelines.csv_mill import catalog
from pipelines.csv_mill._contract import CsvRefusal, FACTORY, RECORD_PREFIX
from tests.test_csv import LEGACY_MILL, TINY_PAIR, _dict_source, _git_show


class SourceBoundaries(unittest.TestCase):
    def setUp(self):
        self.source = _dict_source([TINY_PAIR], FAC=FACTORY, PREFIX=RECORD_PREFIX)

    def _extract(self, source, **kwargs):
        return catalog.plants_from_source(source, mill_id="csv_r114", source="literal.py", **kwargs)

    def _refuses(self, source):
        with self.assertRaises(CsvRefusal) as caught:
            self._extract(source)
        self.assertEqual(caught.exception.code, "SOURCE_NOT_PARSEABLE")

    def test_compiler_invalid_original_source_is_refused(self):
        for suffix in ('__debug__ = 0', 'def f(x, x): pass', 'def f(): break',
                       'if __name__ == "__main__":\n    break'):
            with self.subTest(suffix=suffix):
                self._refuses(self.source + '\n' + suffix)

    def test_source_path_must_be_a_plain_string(self):
        class ForgedPath(str):
            def __eq__(self, other):
                return True

        for path in (ForgedPath('literal.py'), None, 7):
            with self.subTest(kind=type(path)), self.assertRaises(CsvRefusal) as caught:
                catalog.plants_from_source(self.source, mill_id='csv_r114', source=path)
            self.assertEqual(caught.exception.code, 'SOURCE_NOT_PARSEABLE')

    def test_compiler_validation_never_executes_source(self):
        deferred = '\ndef unused():\n    open("unexpected", "w")'
        guard = '\nif __name__ == "__main__":\n    open("unexpected", "w")'
        with mock.patch('builtins.open', side_effect=AssertionError('source executed')):
            self.assertEqual(len(self._extract(self.source + deferred + guard)), 1)
            self._refuses(self.source + '\nopen("unexpected", "w")')

    def test_later_tracked_name_writes_and_mutations_refuse(self):
        for effect in ("PAIRS += [dict(slug='added')]", "FAC += '-changed'",
                       "PREFIX += '-changed'", "CATALOG_FIRST = 114\nCATALOG_FIRST += 1",
                       "del PAIRS", "PAIRS.clear()", "PAIRS[0] = {}",
                       "PAIRS, other = [], None", "import replacement as PAIRS",
                       "def PAIRS():\n    pass", "if True:\n    PAIRS = []"):
            with self.subTest(effect=effect):
                self._refuses(self.source + "\n" + effect)

    def test_unproven_execution_cannot_preserve_source_literals(self):
        for effect in ("unrelated()", "result = unrelated()", "import extension",
                       "ALIAS = PAIRS\nALIAS.clear()", "class Mutator:\n    PAIRS.clear()",
                       "def unused(default=PAIRS.clear()):\n    pass",
                       "@decorate(PAIRS)\ndef unused():\n    pass",
                       "__name__ = '__main__'", "__builtins__ = {}"):
            with self.subTest(effect=effect):
                self._refuses(self.source + "\n" + effect)

    def test_shadowed_dict_cannot_claim_literal_constructor_rows(self):
        for prefix in ("dict = lambda **kwargs: {}\n", "def dict(**kwargs):\n    return {}\n"):
            with self.subTest(prefix=prefix):
                self._refuses(prefix + self.source)

    def test_deferred_bodies_and_exact_script_guard_remain_inert(self):
        deferred = ("\ndef unused():\n    PAIRS.clear()\n"
                    "callback = lambda: unrelated()\n"
                    "if __name__ == '__main__':\n    publish()\n")
        self.assertEqual(self._extract(self.source + deferred)[0]["slug"], TINY_PAIR["slug"])

    def test_annotations_and_future_headers_preserve_literal_rows(self):
        source = '"module docstring"\nfrom __future__ import annotations\n' + self.source
        source += "\nPAIRS: list\ndef unused(value: int = 1) -> str:\n    return 'value'\n"
        self.assertEqual(len(self._extract(source)), 1)
        self._refuses(self.source + "\nfrom __future__ import annotations\n")

    def test_source_encoding_failures_are_coded(self):
        self._refuses(self.source + "\n# \udcff")

    def test_source_encoding_cannot_be_overridden(self):
        original = self.source

        class ForgedSource(str):
            def encode(self, *args, **kwargs):
                return original.encode("utf-8")

        self._refuses(ForgedSource(self.source))

    def test_every_extracted_effective_round_fits_exact_json(self):
        second = dict(TINY_PAIR, slug="second-slug", fail="second-fail", ticket="SECOND-114")
        source = _dict_source([TINY_PAIR, second], FAC=FACTORY, PREFIX=RECORD_PREFIX)
        base = 10 ** 4096 - 1
        with self.assertRaises(CsvRefusal) as caught:
            catalog.plants_from_source(source, mill_id=f"csv_r{base}", source="literal.py", base_round=base)
        self.assertEqual(caught.exception.code, "PLANT_FIELD_INVALID")
        rows = catalog.plants_from_source(self.source, mill_id=f"csv_r{base}",
                                         source="literal.py", base_round=base)
        self.assertEqual(rows[0]["base_round"], base)

    def test_only_exact_archived_bytes_and_path_get_text_projection(self):
        source = _git_show(LEGACY_MILL)
        if source is None:
            self.skipTest("preserved Git source is unavailable")
        self.assertEqual(hashlib.sha256(source.encode()).hexdigest(),
                         "98faa233ffe331fbd1d563c0aa3e190b48e40f18c5939939eab07d078d0ba570")
        rows = catalog.plants_from_source(source, mill_id="csv_r114", source=LEGACY_MILL)
        self.assertEqual(len(rows), 16)
        for text, path in ((source + "\n", LEGACY_MILL),
                           (source + "\nPAIRS.clear()\n", LEGACY_MILL),
                           (source, "other.py")):
            with self.subTest(path=path, length=len(text)), self.assertRaises(CsvRefusal):
                catalog.plants_from_source(text, mill_id="csv_r114", source=path)


if __name__ == "__main__":
    unittest.main()
