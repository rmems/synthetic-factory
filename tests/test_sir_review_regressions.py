"""Catalog corruption and AST binding regressions independent of archive Git objects."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from pipelines.sir.catalog import load_catalog
from pipelines.sir.catalog_extract import (
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


class SirReviewRegressions(unittest.TestCase):
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
        source = "alias = FACTORY\nprint(alias)\ncallback = lambda: PAIRS.clear()\n"
        self.assertEqual(_extract(source)["n_rows"], 1)

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
                self.assertEqual(_extract("loader = " + expression)["loads_sibling"], expected)
