"""Catalog corruption and AST binding regressions independent of archive Git objects."""

from __future__ import annotations

import ast
import hashlib
import unittest

from pipelines.sir.catalog_ast import module_constants
from pipelines.sir.catalog_extract import (
    _literal_sibling_path,
    extract_mill_catalog,
)

if __package__:
    from .test_sir import _LEFTOVER_SNIPPET
else:
    from test_sir import _LEFTOVER_SNIPPET


def _extract(appendix):
    return extract_mill_catalog(
        _LEFTOVER_SNIPPET + "\n" + appendix,
        path="experiments/sir-mill-leftover3-r72.py",
    )


class SirReviewRegressions(unittest.TestCase):
    def test_source_encoding_cannot_be_overridden(self):
        class ForgedSource(str):
            def encode(self, *args, **kwargs):
                return _LEFTOVER_SNIPPET.encode('utf-8')

        forged = ForgedSource(_LEFTOVER_SNIPPET + '\n# forged source bytes\n')
        path = 'experiments/sir-mill-leftover3-r72.py'
        for extract in (extract_mill_catalog, module_constants):
            with self.subTest(extract=extract.__name__), self.assertRaisesRegex(ValueError, 'source'):
                extract(forged, path=path)
        plain = _LEFTOVER_SNIPPET.replace('\n', '\r\n')
        found = extract_mill_catalog(plain, path=path)
        self.assertEqual(found['n_rows'], 1)
        self.assertEqual(found['sha256'], hashlib.sha256(plain.encode('utf-8')).hexdigest())

    def test_blob_identity_does_not_trust_custom_equality(self):
        class ForgedBlob(str):
            def __eq__(self, other):
                return True

        class ForgedObject:
            __eq__ = ForgedBlob.__eq__

        for blob in (ForgedBlob('forged-git-identity'), ForgedObject()):
            with self.subTest(kind=type(blob)), self.assertRaisesRegex(ValueError, 'blob'):
                extract_mill_catalog(_LEFTOVER_SNIPPET,
                                     path='experiments/sir-mill-leftover3-r72.py', blob_sha=blob)

    def test_supplied_blob_identity_must_match_exact_utf8_source(self):
        source = _LEFTOVER_SNIPPET + '\n# caf\u00e9\n'
        path = 'experiments/sir-mill-leftover3-r72.py'
        payload = source.encode('utf-8')
        framed = b'blob ' + str(len(payload)).encode('ascii') + b'\0' + payload
        # nosemgrep: python.lang.security.insecure-hash-algorithms.insecure-hash-algorithm-sha1 -- Git blob object identity for extractor contract tests
        blob = hashlib.sha1(framed, usedforsecurity=False).hexdigest()  # nosec B324
        self.assertEqual(extract_mill_catalog(source, path=path, blob_sha=blob)['blob_sha'], blob)
        self.assertEqual(extract_mill_catalog(source, path=path)['blob_sha'], '')
        self.assertEqual(extract_mill_catalog(source, path=path, blob_sha='')['blob_sha'], '')
        for bad in ('definitely-not-a-sha', 'a' * 40, None, 42):
            with self.subTest(blob=bad), self.assertRaisesRegex(ValueError, 'blob'):
                extract_mill_catalog(source, path=path, blob_sha=bad)
        with self.assertRaisesRegex(ValueError, 'blob'):
            extract_mill_catalog(source + '\n', path=path, blob_sha=blob)

    def test_future_imports_must_stay_in_the_original_module_header(self):
        future = 'from __future__ import annotations\n'
        path = 'experiments/sir-mill-leftover3-r72.py'
        for prefix in (future, '\"module docstring\"\n' + future + future):
            with self.subTest(prefix=prefix):
                self.assertEqual(extract_mill_catalog(prefix + _LEFTOVER_SNIPPET, path=path)['n_rows'], 1)
        invalid = (_LEFTOVER_SNIPPET + future, 'pass\n' + future + _LEFTOVER_SNIPPET,
                   '\"doc\"\n\"second string\"\n' + future + _LEFTOVER_SNIPPET,
                   _LEFTOVER_SNIPPET + '\ndef unused():\n    ' + future,
                   _LEFTOVER_SNIPPET + '\nif __name__ == "__main__":\n    ' + future)
        for source in invalid:
            with self.subTest(source=source), self.assertRaises(ValueError):
                extract_mill_catalog(source, path=path)

    def test_unknown_module_effects_cannot_preserve_literal_rows(self):
        effects = ('import sys\nsys._getframe().f_globals["PAIRS"] = []',
                   'import inspect\ninspect.currentframe().f_globals["PAIRS"] = []',
                   'import builtins\nexecute = getattr(builtins, "exec")\nexecute("PAIRS=[]")',
                   'unrelated()', 'result = unrelated()', 'import extension',
                   'from extension import *', 'if unknown:\n    unrelated()',
                   'def unused(value=unrelated()):\n    pass',
                   'unused = lambda value=unrelated(): None')
        for effect in effects:
            with self.subTest(effect=effect), self.assertRaises(ValueError):
                _extract(effect)
        deferred = 'def unused():\n    unrelated()\ncallback = lambda: unrelated()'
        self.assertEqual(_extract(deferred)['n_rows'], 1)


    def test_wildcard_import_cannot_preserve_prior_catalog_bindings(self):
        with self.assertRaises(ValueError):
            _extract("from replacement import *")

    def test_dynamic_namespace_writes_cannot_preserve_catalog_bindings(self):
        mutations = (
            'globals()["PAIRS"] = []',
            'globals().__setitem__("PAIRS", [])',
            'locals()["PAIRS"] = []',
            'vars()["PAIRS"] = []',
            'exec("PAIRS = []")',
            'eval("PAIRS.clear()")',
            'namespace = globals()\nnamespace["PAIRS"] = []',
        )
        for mutation in mutations:
            with self.subTest(mutation=mutation), self.assertRaises(ValueError):
                _extract(mutation)

    def test_dynamic_builtin_attributes_and_import_aliases_fail_closed(self):
        statements = (
            'import builtins as b\nb.globals()["PAIRS"] = []',
            'import builtins as b\nb.exec("PAIRS=[]")',
            'from builtins import exec as execute\nexecute("PAIRS=[]")',
            'from builtins import globals as namespace\nnamespace()["PAIRS"] = []',
        )
        for statement in statements:
            with self.subTest(statement=statement), self.assertRaises(ValueError):
                _extract(statement)
        deferred = 'def unused():\n    import builtins as b\n    b.exec("PAIRS=[]")'
        self.assertEqual(_extract(deferred)["n_rows"], 1)

    def test_deferred_loader_bodies_do_not_claim_sibling_lineage(self):
        deferred = (
            'def unused():\n    SourceFileLoader("fake", "fake.py")',
            'unused = lambda: SourceFileLoader("fake", "fake.py")',
            'if __name__ == "__main__":\n    SourceFileLoader("fake", "fake.py")',
        )
        for source in deferred:
            with self.subTest(source=source):
                self.assertEqual(_extract(source)["loads_sibling"], "")
                actual = source + '\nSourceFileLoader("real", "real.py")'
                with self.assertRaises(ValueError):
                    _extract(actual)

    def test_unpinned_definition_time_loader_calls_are_refused(self):
        sources = (
            'def unused(value=SourceFileLoader("real", "real.py")):\n    pass',
            'unused = lambda value=SourceFileLoader("real", "real.py"): None',
            'class Publisher:\n    loader = SourceFileLoader("real", "real.py")',
            '@decorate(SourceFileLoader("real", "real.py"))\ndef unused():\n    pass',
        )
        for source in sources:
            with self.subTest(source=source):
                with self.assertRaises(ValueError):
                    _extract(source)
                self.assertEqual(_literal_sibling_path(ast.parse(source)), "experiments/real.py")

    def test_destructuring_invalidates_every_bound_catalog_name(self):
        targets = ("{field}, extra", "[extra, [{field}]]", "extra, *{field}")
        for field in ("PAIRS", "FACTORY", "GEN", "HOP", "N_ROUNDS"):
            for template in targets:
                assignment = template.format(field=field) + " = build()"
                with self.subTest(assignment=assignment), self.assertRaises(ValueError):
                    _extract(assignment)

    def test_unsupported_top_level_mutations_cannot_retain_literal_pairs(self):
        mutations = (
            "PAIRS += build()",
            "del PAIRS",
            "PAIRS[0] = build()",
            "del PAIRS[0]",
            "PAIRS.append(build())",
            "if condition:\n    PAIRS = build()",
            "for PAIRS in build():\n    pass",
            "import unknown as PAIRS",
        )
        for mutation in mutations:
            with self.subTest(mutation=mutation), self.assertRaises(ValueError):
                _extract(mutation)

    def test_unsupported_top_level_optional_metadata_mutations_are_unknown(self):
        for field in ("FACTORY", "GEN", "HOP", "N_ROUNDS"):
            for mutation in (f"{field} += build()", f"del {field}"):
                with self.subTest(mutation=mutation), self.assertRaises(ValueError):
                    _extract(mutation)

    def test_publisher_function_bodies_do_not_change_module_literals(self):
        source = "def publish():\n    PAIRS.append(build())\n    del PAIRS\n"
        self.assertEqual(_extract(source)["n_rows"], 1)

    def test_definition_time_mutations_cannot_retain_literal_pairs(self):
        definitions = (
            "def publish(value=PAIRS.clear()):\n    pass",
            "def publish(*, value=PAIRS.clear()):\n    pass",
            "@decorate(PAIRS.clear())\ndef publish():\n    pass",
            "class Publisher:\n    PAIRS.clear()",
            "class Publisher(base(PAIRS.clear())):\n    pass",
            "@decorate(PAIRS.clear())\nclass Publisher:\n    pass",
            "publish = lambda value=PAIRS.clear(): None",
            "def publish() -> PAIRS.clear():\n    pass",
            "async def publish() -> PAIRS.clear():\n    pass",
        )
        for definition in definitions:
            with self.subTest(definition=definition), self.assertRaises(ValueError):
                _extract(definition)

    def test_mutable_aliases_cannot_hide_catalog_mutation(self):
        aliases = (
            ("PAIRS", "alias.clear()"),
            ("(PAIRS,)", "alias[0].clear()"),
            ("{'rows': PAIRS}", "alias['rows'].clear()"),
            ("PAIRS[0]", "alias.clear()"),
        )
        for value, mutation in aliases:
            with self.subTest(value=value), self.assertRaises(ValueError):
                _extract(f"alias = {value}\n{mutation}")
        with self.assertRaises(ValueError):
            _extract("removed = PAIRS.pop()")

    def test_deferred_bodies_and_immutable_aliases_preserve_catalog_literals(self):
        source = "alias = FACTORY\ncallback = lambda: PAIRS.clear()\n"
        self.assertEqual(_extract(source)["n_rows"], 1)

    def test_boolean_round_metadata_is_not_an_integer(self):
        for field in ("CATALOG_FIRST", "N_ROUNDS"):
            for value in (True, False):
                with self.subTest(field=field, value=value), self.assertRaises(ValueError):
                    _extract(f"{field} = {value!r}")


    def test_invoked_local_helpers_make_catalog_mutations_unproven(self):
        definition = "def clear():\n    PAIRS.clear()\n"
        for call in ("clear()", "unused = clear()", "alias = (clear,)\nalias[0]()"):
            with self.subTest(call=call), self.assertRaises(ValueError):
                _extract(definition + call)
        with self.assertRaises(ValueError):
            _extract("clear = lambda: PAIRS.clear()\nclear()")

    def test_script_entry_body_is_deferred_but_import_else_branch_is_checked(self):
        definition = "def clear():\n    PAIRS.clear()\n"
        guarded = definition + "if __name__ == '__main__':\n    clear()\n"
        self.assertEqual(_extract(guarded)["n_rows"], 1)
        with self.assertRaises(ValueError):
            _extract(guarded + "else:\n    clear()\n")

    def test_rebound_module_name_cannot_hide_script_guard_mutation(self):
        rebindings = (
            '__name__ = "__main__"',
            '__name__: str = "__main__"',
            '(__name__, extra) = ("__main__", 0)',
            'if condition:\n    __name__ = "__main__"',
            'import replacement as __name__',
        )
        guard = '\nif __name__ == "__main__":\n    PAIRS = []'
        for rebinding in rebindings:
            with self.subTest(rebinding=rebinding), self.assertRaises(ValueError):
                _extract(rebinding + guard)
        self.assertEqual(_extract('def unused():\n    __name__ = "__main__"' + guard)["n_rows"], 1)

    def test_module_registry_writes_cannot_preserve_catalog_bindings(self):
        mutations = (
            'import sys\nsys.modules[__name__].PAIRS = []',
            'import sys as s\ns.modules[__name__].PAIRS = []',
            'from sys import modules as registry\nregistry[__name__].PAIRS = []',
            'import sys\nmodule = sys.modules[__name__]\nmodule.PAIRS = []',
        )
        for mutation in mutations:
            with self.subTest(mutation=mutation), self.assertRaises(ValueError):
                _extract(mutation)
        deferred = 'def unused():\n    import sys\n    sys.modules[__name__].PAIRS = []'
        self.assertEqual(_extract(deferred)["n_rows"], 1)

    def test_pattern_and_exception_bindings_invalidate_previous_pairs(self):
        statements = (
            "match []:\n    case PAIRS: pass",
            "match []:\n    case [*PAIRS]: pass",
            "match {}:\n    case {**PAIRS}: pass",
            "try:\n    raise Exception()\nexcept Exception as PAIRS:\n    pass",
        )
        for statement in statements:
            with self.subTest(statement=statement), self.assertRaises(ValueError):
                _extract(statement)


    def test_loader_sibling_uses_only_the_actual_path_argument(self):
        cases = (
            ('SourceFileLoader("plugin.py", dynamic_path())', ""),
            ('SourceFileLoader("plugin.py", "real.py")', "experiments/real.py"),
            ('SourceFileLoader("name", path="real.py")', "experiments/real.py"),
            ('SourceFileLoader(fullname="plugin.py", path="real.py")', "experiments/real.py"),
            ('SourceFileLoader(*arguments, "false.py")', ""),
        )
        for expression, expected in cases:
            with self.subTest(expression=expression):
                self.assertEqual(_literal_sibling_path(ast.parse("loader = " + expression)), expected)
                with self.assertRaises(ValueError):
                    _extract("loader = " + expression)

    def test_builtin_namespace_rebinding_is_not_a_literal_module(self):
        rebindings = ('__builtins__ = {}', '__builtins__: dict = {}',
                      'namespace = {}\n__builtins__ = namespace',
                      'def __builtins__():\n    pass',
                      'async def __builtins__():\n    pass')
        for rebinding in rebindings:
            with self.subTest(rebinding=rebinding), self.assertRaises(ValueError):
                _extract(rebinding)
        self.assertEqual(_extract('def unused():\n    __builtins__ = {}')['n_rows'], 1)

    def test_conditional_annotation_state_cannot_bind_catalog_literals(self):
        appendix = "__conditional_annotations__ = PAIRS\nignored: int\n"
        with self.assertRaisesRegex(ValueError, "__conditional_annotations__"):
            _extract(appendix)

    def test_unhashable_literal_members_fail_as_value_error(self):
        for appendix in ("EXTRA = {[]: 1}\n", "EXTRA = {1, []}\n"):
            with self.subTest(appendix=appendix), self.assertRaises(ValueError):
                _extract(appendix)
