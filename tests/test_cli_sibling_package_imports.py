"""The formerly direct-only CLIs import as package children, as one object.

``next_round``, ``quality_gate_audit``, ``quality_gate_embedding``,
``card_schema``, ``card_schema_validate``, ``card_schema_yaml``,
``verify_execution`` and ``verify_execution_shapes`` now open with the
assert/join/expose prelude, so ``importlib.import_module("pipelines.<name>")``
works without ``pipelines/`` on ``sys.path``. Their package form imports their
siblings relatively, so every pipelines module a converted module loads has to
be one object under both names as well, not only the converted module: the
helpers they reach (``card_schema_core``, ``card_schema_coverage``,
``card_schema_render``, ``quality_gate_identity``, ``verify_execution_safety``,
``check_records``, ``record_kind``) carry the same prelude for that reason.

The in-process cases take the package branch of every prelude here, where the
coverage report is measured. The fresh-interpreter cases
(``tests/cli_sibling_import_probe.py``) import each converted module in four
orders, each in its own isolated interpreter, and report every loaded pipelines
module that is not one object under both names.
"""

from __future__ import annotations

import importlib
import sys
import unittest
from unittest import mock

if __package__:
    from . import cli_sibling_import_probe as probe
    from .pipeline_import_test_support import (
        PIPELINES,
        REPO,
        clean_package_imports,
        direct_pipeline_path,
    )
else:
    import cli_sibling_import_probe as probe
    from pipeline_import_test_support import (
        PIPELINES,
        REPO,
        clean_package_imports,
        direct_pipeline_path,
    )

MODULES = probe.MODULES


def _package_root_on_path() -> None:
    if str(REPO) not in sys.path:
        sys.path.append(str(REPO))


def _load_packaged() -> dict:
    _package_root_on_path()
    return {name: load() for name, load in probe.PACKAGE_LOADERS.items()}


def _load_flat() -> dict:
    with direct_pipeline_path():
        return {name: load() for name, load in probe.FLAT_LOADERS.items()}


def _flat_first() -> tuple[dict, dict]:
    flat = _load_flat()
    return flat, _load_packaged()


def _package_first() -> tuple[dict, dict]:
    packaged = _load_packaged()
    return _load_flat(), packaged


def _package_root_first() -> tuple[dict, dict]:
    """The bare package is already loaded, so the package branch runs after the CLI form."""

    _package_root_on_path()
    importlib.import_module("pipelines")
    return _flat_first()


# Each loader returns ``(flat, packaged)``.
ORDERS = (
    ("flat_first", _flat_first),
    ("package_first", _package_first),
    ("package_root_first", _package_root_first),
)


class PackageForm(unittest.TestCase):
    def _assert_bound_once(self, flat: dict, packaged: dict) -> None:
        for name in MODULES:
            self.assertIs(flat[name], packaged[name], name)
        for module, attribute in probe.SHARED_CLASSES:
            self.assertIs(
                getattr(flat[module], attribute),
                getattr(packaged[module], attribute),
                f"{module}.{attribute}",
            )
        # An error raised through one spelling is caught through the other.
        with self.assertRaisesRegex(
            packaged["card_schema"].CardSchemaError, "must be a JSON object"
        ):
            flat["card_schema"].validate([], "dataset")
        self.assertTrue(probe.caught_across(packaged, flat))

    def test_both_loader_tables_name_the_same_eight_modules(self):
        self.assertEqual(len(MODULES), 8)
        self.assertEqual(tuple(probe.FLAT_LOADERS), MODULES)

    def test_each_module_imports_from_a_clean_package_without_the_cli_path(self):
        with clean_package_imports():
            packaged = _load_packaged()
            self.assertNotIn(str(PIPELINES), sys.path)
            for name, module in packaged.items():
                with self.subTest(name=name):
                    self.assertEqual(module.__name__, f"pipelines.{name}")
                    self.assertEqual(module.__package__, "pipelines")
                    self.assertIs(sys.modules[f"pipelines.{name}"], module)
                    self.assertIs(sys.modules[name], module)

    def test_every_order_binds_one_object_and_one_class(self):
        for order, load in ORDERS:
            with self.subTest(order=order), clean_package_imports():
                self._assert_bound_once(*load())

    def test_package_form_binds_the_real_validators_and_one_host(self):
        with clean_package_imports():
            packaged = _load_packaged()
            host = packaged["verify_execution"]
            validate_run = importlib.import_module("pipelines.validate_run")
            check_records = importlib.import_module("pipelines.check_records")
            self.assertIs(host.check_line, validate_run.check_line)
            self.assertIs(host.check_episode, validate_run.check_episode)
            self.assertIs(host.ALLOWED_SIM_OR_REAL, check_records.ALLOWED_SIM_OR_REAL)
            shapes = packaged["verify_execution_shapes"]
            self.assertIs(shapes._host(), host)
            with mock.patch.object(host, "check_episode", None):
                status, reason = shapes.verify_episode({"steps": []}, "where")
            self.assertEqual(
                (status, reason), ("failed", "episode shape checker unavailable")
            )


# Splits main already has. On main the converted modules cannot be imported as
# package children, but importing their own dependencies (round_txn, validate_run,
# training_audit, check_records) under both names splits these same modules,
# because they lack the binding prelude. They may stay split here; any other
# split fails. ``tag_jsonutil`` is a parity shared source, so it cannot take the
# prelude without an owner-reviewed re-seal; it holds only pure functions and
# raises only ValueError, so nothing compares its two copies.
_ROUND_TXN_SPLITS = frozenset(
    {
        "round_txn_coverage",
        "round_txn_execution",
        "round_txn_preference",
        "round_txn_raster",
        "round_txn_stage",
    }
)
_VALIDATE_RUN_SPLITS = frozenset({"validate_run_input"})
_SEALED_SPLITS = frozenset({"tag_jsonutil"})
_TRAINING_AUDIT_SPLITS = frozenset(
    {
        "census",
        "census_sim",
        "code_repair._sandbox",
        "coding_constants",
        "coding_verify",
        "coding_verify_manifest",
        "coding_verify_steps",
        "curate_coding",
        "curate_identity_checks",
        "distillation_audit",
        "mill_evidence",
        "mill_family",
        "mill_findings",
        "mill_locations",
        "mill_ownership",
        "mill_resolution",
        "mill_reviewed_vocabulary",
        "mill_signals",
        "training_audit_bridge",
        "training_audit_mill",
        "training_audit_report",
    }
)
MAIN_BASELINE_SPLITS = {
    "card_schema": frozenset(),
    "card_schema_validate": frozenset(),
    "card_schema_yaml": frozenset(),
    "next_round": _ROUND_TXN_SPLITS | _VALIDATE_RUN_SPLITS | _SEALED_SPLITS,
    "quality_gate_audit": (
        _ROUND_TXN_SPLITS | _VALIDATE_RUN_SPLITS | _SEALED_SPLITS | _TRAINING_AUDIT_SPLITS
    ),
    "quality_gate_embedding": frozenset(),
    "verify_execution": _VALIDATE_RUN_SPLITS | _SEALED_SPLITS,
    "verify_execution_shapes": frozenset(),
}

# Helpers the converted modules import relatively; each carries the prelude, so
# none of them may ever split.
PRELUDE_HELPERS = frozenset(
    {
        "card_schema_core",
        "card_schema_coverage",
        "card_schema_render",
        "check_records",
        "quality_gate_identity",
        "record_kind",
        "verify_execution_safety",
    }
)


class FreshInterpreter(unittest.TestCase):
    def test_the_baseline_names_every_converted_module_and_no_helper(self):
        self.assertEqual(tuple(MAIN_BASELINE_SPLITS), MODULES)
        allowed = frozenset().union(*MAIN_BASELINE_SPLITS.values())
        self.assertEqual(sorted(allowed & (PRELUDE_HELPERS | set(MODULES))), [])

    def test_every_loaded_module_is_one_object_in_every_order(self):
        calls = [(form, name) for name in MODULES for form in probe.FORMS]
        loaded = set()
        for report in probe.in_fresh_interpreters(probe.run_closure, calls):
            loaded.update(report["loaded"])
            with self.subTest(module=report["module"], form=report["form"]):
                self.assertIn(report["module"], report["loaded"])
                unexpected = set(report["split"]) - MAIN_BASELINE_SPLITS[report["module"]]
                self.assertEqual(sorted(unexpected), [], report["split"])
        self.assertLessEqual(PRELUDE_HELPERS, loaded)

    def test_package_first_then_bare_helpers_share_classes_and_sentinels(self):
        # import pipelines.card_schema; from card_schema_core import CardSchemaError
        # must catch what card_schema.validate raises, as it does on main.
        (report,) = probe.in_fresh_interpreters(probe.run_shared_objects, [()])
        self.assertEqual([name for name, same in report.items() if not same], [], report)


if __name__ == "__main__":
    unittest.main()
