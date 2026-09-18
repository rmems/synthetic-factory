"""SIR package and direct imports share module state in either import order."""

import ast
import importlib
import sys
import unittest

if __package__:
    from .pipeline_import_test_support import clean_package_imports, direct_pipeline_path
else:
    from pipeline_import_test_support import clean_package_imports, direct_pipeline_path


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



class SirImportIdentity(unittest.TestCase):
    def test_public_module_twins_share_runtime_state(self):
        for leaf in ("catalog_extract", "identity", "vocabulary"):
            for prefixes in (("pipelines.sir", "sir"), ("sir", "pipelines.sir")):
                with self.subTest(leaf=leaf, prefixes=prefixes), clean_package_imports(), direct_pipeline_path():
                    first = importlib.import_module(f"{prefixes[0]}.{leaf}")
                    second = importlib.import_module(f"{prefixes[1]}.{leaf}")
                    self.assertIs(first, second)

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

