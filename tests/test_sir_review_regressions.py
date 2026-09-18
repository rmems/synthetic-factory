"""Catalog corruption and AST binding regressions independent of archive Git objects."""

from __future__ import annotations

import ast
import json
import sys
import tempfile
import unittest
from pathlib import Path

from pipelines.sir.catalog import load_catalog
from pipelines.sir.catalog_extract import (
    _literal_sibling_path,
    catalog_json_path,
    extract_mill_catalog,
    pairs_jsonl_path,
)

if __package__:
    from .pipeline_import_test_support import clean_package_imports, direct_pipeline_path
    from .test_sir import _LEFTOVER_SNIPPET
else:
    from pipeline_import_test_support import clean_package_imports, direct_pipeline_path
    from test_sir import _LEFTOVER_SNIPPET


def _extract(appendix):
    return extract_mill_catalog(
        _LEFTOVER_SNIPPET + "\n" + appendix,
        path="experiments/sir-mill-leftover3-r72.py",
    )


def _catalog_models(package_first):
    if package_first:
        from pipelines.sir import catalog_model as first
        from sir import catalog_model as second
    else:
        from sir import catalog_model as first
        from pipelines.sir import catalog_model as second
    return first, second


def _catalog_classes():
    from pipelines.sir.catalog import MillCatalog as packaged
    from sir.catalog import MillCatalog as direct

    return packaged, direct


def _catalog_modules():
    from pipelines.sir import catalog as packaged
    from sir import catalog as direct

    return packaged, direct


def _source_modules():
    import pipelines.sir.sources as packaged
    import sir.sources as direct

    return packaged, direct


def _ast_modules(package_first):
    if package_first:
        from pipelines.sir import catalog_ast as first
        from sir import catalog_ast as second
    else:
        from sir import catalog_ast as first
        from pipelines.sir import catalog_ast as second
    return first, second


def _assert_literal_module_identity(test, catalog_ast):
    from pipelines.sir import catalog_literals as packaged
    from sir import catalog_literals as direct

    test.assertIs(packaged, direct)
    test.assertIs(packaged.UNSET, catalog_ast.UNSET)
    test.assertIs(packaged.literal_value, catalog_ast.literal_value)


class SirReviewRegressions(unittest.TestCase):
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

    def test_catalog_class_identity_survives_both_import_orders(self):
        for package_first in (True, False):
            with (
                self.subTest(package_first=package_first),
                clean_package_imports(),
                direct_pipeline_path(),
            ):
                first_module, second_module = _catalog_models(package_first)
                self.assertIs(first_module, second_module)
                for catalog_class in _catalog_classes():
                    self.assertIs(catalog_class, first_module.MillCatalog)
                packaged, direct = _catalog_modules()
                self.assertIs(sys.modules["pipelines.sir.catalog"], sys.modules["sir.catalog"])
                self.assertIs(packaged, direct)
                self.assertIs(packaged.SirCatalog, direct.SirCatalog)
                self.assertIs(packaged.CATALOG, direct.CATALOG)
                packaged_sources, direct_sources = _source_modules()
                self.assertIs(sys.modules["pipelines.sir.sources"], sys.modules["sir.sources"])
                self.assertIs(packaged_sources, direct_sources)
                self.assertIs(packaged_sources.MillSource, direct_sources.MillSource)
                self.assertIs(packaged_sources.MILL_SOURCES, direct_sources.MILL_SOURCES)

    def test_ast_unresolved_sentinel_survives_both_import_orders(self):
        for package_first in (True, False):
            with self.subTest(package_first=package_first), clean_package_imports(), direct_pipeline_path():
                first, second = _ast_modules(package_first)
                self.assertIs(first, second)
                self.assertIs(first.UNSET, second.UNSET)
                self.assertIs(first.literal_value(ast.parse("unknown", mode="eval").body), second.UNSET)
                _assert_literal_module_identity(self, first)

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

    def test_loader_integer_metadata_rejects_booleans(self):
        for field in ("catalog_first", "n_rounds", "n_rows", "n_hops", "source_lines"):
            with self.subTest(field=field):
                self._assert_catalog_refuses("sir-mill-leftover3-r72", field, False)

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

    def test_source_derived_metadata_cannot_be_fabricated(self):
        for mill_id in ("sir-mill-leftover3-r72", "sir_r108_leftover3d_mill"):
            for field, value in (("source_lines", 1), ("doc_first_line", "forged description")):
                with self.subTest(mill_id=mill_id, field=field):
                    self._assert_catalog_refuses(mill_id, field, value)

    def test_header_count_and_extraction_claims_are_pinned(self):
        for field in ("n_mills", "n_source_files", "extraction"):
            with self.subTest(field=field), tempfile.TemporaryDirectory() as tmp:
                directory = Path(tmp)
                header = json.loads(catalog_json_path().read_bytes())
                header[field] = "publisher was executed" if field == "extraction" else 1
                destination = directory / "CATALOG.json"
                destination.write_text(json.dumps(header), encoding="utf-8")
                (directory / "pairs.jsonl").write_bytes(pairs_jsonl_path().read_bytes())
                with self.assertRaisesRegex(ValueError, field):
                    load_catalog(destination)

    def test_validated_catalog_mappings_cannot_be_changed_after_loading(self):
        catalog = load_catalog()
        mill = next(iter(catalog.mills.values()))
        with self.assertRaises(TypeError):
            catalog.mills[mill.mill_id] = mill
        with self.assertRaises(TypeError):
            mill.pairs[0]["success_slug"] = "forged"

    def test_header_json_refuses_duplicate_keys_and_nonfinite_values(self):
        original = catalog_json_path().read_text(encoding="utf-8")
        mutations = (
            original.replace('"n_mills": 2', '"n_mills": 99, "n_mills": 2'),
            original.replace('"n_mills": 2', '"unsupported": NaN, "n_mills": 2'),
            original.replace('"n_mills": 2', '"unsupported": 1e999, "n_mills": 2'),
        )
        for header in mutations:
            with self.subTest(header=header), tempfile.TemporaryDirectory() as tmp:
                directory = Path(tmp)
                destination = directory / "CATALOG.json"
                destination.write_text(header, encoding="utf-8")
                (directory / "pairs.jsonl").write_bytes(pairs_jsonl_path().read_bytes())
                with self.assertRaises(ValueError):
                    load_catalog(destination)

    def test_catalog_document_and_mills_require_mapping_shapes(self):
        original = json.loads(catalog_json_path().read_bytes())
        missing = dict(original)
        del missing["mills"]
        documents = [None, [], "catalog", 42, missing]
        documents.extend(dict(original, mills=value) for value in (None, [], "mills", 42))
        for document in documents:
            with self.subTest(document=document), tempfile.TemporaryDirectory() as tmp:
                destination = Path(tmp) / "CATALOG.json"
                destination.write_text(json.dumps(document), encoding="utf-8")
                with self.assertRaises(ValueError):
                    load_catalog(destination)

    def test_loader_rejects_valid_string_content_drift(self):
        with tempfile.TemporaryDirectory() as tmp:
            directory = Path(tmp)
            (directory / "CATALOG.json").write_bytes(catalog_json_path().read_bytes())
            lines = pairs_jsonl_path().read_text(encoding="utf-8").splitlines()
            pair = json.loads(lines[1])
            pair["success_url"] = "https://example.invalid/replaced-source"
            lines[1] = json.dumps(pair, separators=(",", ":"))
            (directory / "pairs.jsonl").write_text("\n".join(lines) + "\n", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "SHA-256"):
                load_catalog(directory / "CATALOG.json")

    def _assert_catalog_refuses(self, mill_id, field, value):
        with tempfile.TemporaryDirectory() as tmp:
            directory = Path(tmp)
            header = json.loads(catalog_json_path().read_text(encoding="utf-8"))
            header["mills"][mill_id][field] = value
            destination = directory / "CATALOG.json"
            destination.write_text(json.dumps(header), encoding="utf-8")
            (directory / "pairs.jsonl").write_bytes(pairs_jsonl_path().read_bytes())
            with self.assertRaisesRegex(ValueError, field):
                load_catalog(destination)

    def test_loader_refuses_malformed_hops_with_matching_count(self):
        for hops in ("abcdefghijk", [1] * 11, [""] * 11, ["other"] * 11):
            with self.subTest(hops=hops):
                self._assert_catalog_refuses("sir_r108_leftover3d_mill", "hops", hops)

    def test_loader_refuses_valid_hop_names_that_drift_from_preserved_source(self):
        self._assert_catalog_refuses("sir_r108_leftover3d_mill", "hops", ["forged-factory"] * 11)

    def test_loader_refuses_fabricated_sha256_without_reading_git(self):
        for mill_id in ("sir-mill-leftover3-r72", "sir_r108_leftover3d_mill"):
            with self.subTest(mill_id=mill_id):
                self._assert_catalog_refuses(mill_id, "sha256", "0" * 64)

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
