#!/usr/bin/env python3
"""Package/direct-import compatibility regressions for pipeline modules."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path
from types import ModuleType
from unittest import mock


REPO = Path(__file__).resolve().parents[1]
PIPELINES = REPO / "pipelines"


class PipelinesPackageImports(unittest.TestCase):
    def test_00_direct_first_bridge_modules_retain_identity(self):
        sys.path.insert(0, str(PIPELINES))
        try:
            import curate_bridge as direct_bridge
            import curate_bridge_materialize_fs as direct_materialize_fs
        finally:
            sys.path.remove(str(PIPELINES))

        from pipelines import curate_bridge as packaged_bridge
        from pipelines import curate_bridge_materialize_fs as packaged_materialize_fs

        self.assertIs(direct_bridge, packaged_bridge)
        self.assertIs(direct_bridge.CurationDecision, packaged_bridge.CurationDecision)
        self.assertIs(direct_materialize_fs, packaged_materialize_fs)
        self.assertIs(
            direct_materialize_fs.BridgeCurationError,
            packaged_materialize_fs.BridgeCurationError,
        )

    def test_curate_bridge_imports_from_the_pipelines_package(self):
        from pipelines import curate_bridge

        self.assertTrue(callable(curate_bridge.curate_jsonl))

    def test_exact_json_has_one_identity_in_package_and_direct_modes(self):
        from pipelines import exact_json as packaged_exact_json

        sys.path.insert(0, str(PIPELINES))
        try:
            import exact_json as direct_exact_json
        finally:
            sys.path.remove(str(PIPELINES))

        value = direct_exact_json.parse_finite_json_float("1.00000000000000001")
        self.assertIs(packaged_exact_json, direct_exact_json)
        self.assertIs(packaged_exact_json.ExactJSONFloat, direct_exact_json.ExactJSONFloat)
        self.assertEqual(
            packaged_exact_json.dumps_exact_json({"value": value}),
            '{"value":1.00000000000000001}',
        )

    def test_package_rejects_foreign_top_level_exact_json_module(self):
        import pipelines

        foreign = ModuleType("exact_json")
        foreign.__file__ = str(REPO.parent / "unrelated" / "exact_json.py")
        with mock.patch.dict(sys.modules, {"exact_json": foreign}):
            self.assertIsNone(pipelines._local_sibling_module("exact_json"))


if __name__ == "__main__":
    unittest.main()
