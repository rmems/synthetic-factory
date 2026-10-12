"""The formerly direct-only CLIs import as package children, as one object.

``next_round``, ``quality_gate_audit``, ``quality_gate_embedding``,
``card_schema``, ``card_schema_validate``, ``card_schema_yaml``,
``verify_execution`` and ``verify_execution_shapes`` now open with the
assert/join/expose prelude, so ``importlib.import_module("pipelines.<name>")``
works without ``pipelines/`` on ``sys.path`` and binds the same module object
as the bare CLI name in either order. The in-process cases take the package
branch of every prelude here, where the coverage report is measured; the
spawned-interpreter cases (``tests/cli_sibling_import_probe.py``) prove each
order with nothing inherited from this process.
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


class FreshInterpreter(unittest.TestCase):
    @staticmethod
    def fresh(form: str) -> dict:
        return probe.in_fresh_interpreter(probe.run_form, form)

    def test_the_cli_form_alone(self):
        report = self.fresh("cli")
        self.assertEqual(report["names"], sorted(MODULES))
        self.assertTrue(report["pipelines_on_path"])

    def test_the_package_form_alone_binds_both_names(self):
        report = self.fresh("package")
        self.assertEqual(report["names"], sorted(f"pipelines.{name}" for name in MODULES))
        self.assertFalse(report["pipelines_on_path"])
        self.assertEqual(report["split_modules"], [])

    def test_either_order_is_one_object_and_one_class(self):
        for form in ("cli_then_package", "package_then_cli"):
            with self.subTest(form=form):
                report = self.fresh(form)
                self.assertEqual(
                    [name for name, same in report["one_object"].items() if not same], [], report
                )
                self.assertEqual(
                    [name for name, same in report["one_class"].items() if not same], [], report
                )
                self.assertEqual(
                    [name for name, ok in report["caught_across"].items() if not ok], [], report
                )
                self.assertEqual(report["split_modules"], [], report)


if __name__ == "__main__":
    unittest.main()
