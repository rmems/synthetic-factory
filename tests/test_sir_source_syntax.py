"""Python validity is checked without executing recovered SIR source."""

import unittest
from unittest import mock

from pipelines.sir.catalog_ast import module_constants
from pipelines.sir.catalog_extract import extract_mill_catalog
from tests.test_sir import _LEFTOVER_SNIPPET


class SourceSyntaxTests(unittest.TestCase):
    def test_source_path_must_be_a_plain_string(self):
        path = 'experiments/sir-mill-leftover3-r72.py'

        class ForgedPath(str):
            def __hash__(self):
                return hash(path)

            def __eq__(self, other):
                return True

        for extractor in (extract_mill_catalog, module_constants):
            for forged in (ForgedPath('/unreviewed/untrusted-leftover.py'), None, 7):
                with self.subTest(extractor=extractor.__name__, kind=type(forged)):
                    with self.assertRaisesRegex(ValueError, 'path'):
                        extractor(_LEFTOVER_SNIPPET, path=forged)

    def test_compiler_invalid_original_source_is_refused(self):
        for suffix in ('__debug__ = 0', 'def f(x, x): pass', 'def f(): break',
                       'if __name__ == "__main__":\n    break'):
            for extractor in (extract_mill_catalog, module_constants):
                with self.subTest(suffix=suffix, extractor=extractor.__name__):
                    with self.assertRaises(ValueError):
                        extractor(_LEFTOVER_SNIPPET + '\n' + suffix, path='experiments/sir-mill-leftover3-r72.py')

    def test_compiler_validation_never_executes_source(self):
        deferred = '\ndef unused():\n    open("unexpected", "w")'
        guard = '\nif __name__ == "__main__":\n    open("unexpected", "w")'
        with mock.patch('builtins.open', side_effect=AssertionError('source executed')):
            found = extract_mill_catalog(_LEFTOVER_SNIPPET + deferred + guard, path='experiments/sir-mill-leftover3-r72.py')
            self.assertEqual(found['n_rows'], 1)
            with self.assertRaises(ValueError):
                extract_mill_catalog(_LEFTOVER_SNIPPET + '\nopen("unexpected", "w")', path='experiments/sir-mill-leftover3-r72.py')


if __name__ == "__main__":
    unittest.main()
