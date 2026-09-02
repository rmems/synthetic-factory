#!/usr/bin/env python3
"""Import-order and facade contracts for split compose modules."""

from __future__ import annotations

import io
import itertools
import multiprocessing
import unittest
from contextlib import redirect_stdout
from types import ModuleType
from unittest import mock

if __package__:
    from . import pipeline_import_catalog
    from .pipeline_import_test_support import (
        direct_pipeline_path,
        isolated_pipeline_modules,
    )
else:
    import pipeline_import_catalog
    from pipeline_import_test_support import (
        direct_pipeline_path,
        isolated_pipeline_modules,
    )


ADAPTER_FIRST_CASES = tuple(
    itertools.product(
        ("compose_curated_identity_facade", "compose_curated_record_facade"),
        ("direct", "package"),
        ("direct", "package"),
    )
)
FACADE_IMPORT_ORDERS = {
    None: """
        compose_contract compose_curated_calibration compose_curated_coding
        compose_curated_identity compose_curated_identity_facade
        compose_curated_record_facade compose_curated_record compose_curated_run
        compose_curated_run_facade compose_destination compose_mill compose_trajectory
        curate_agentic curate_bridge curate_coding curate_identity curate_preferences
        curate_rewards training_audit check_records census record_kind round_txn
        """.split(),
    "pipelines": """
        compose_mill curate_agentic curate_bridge curate_coding curate_identity
        curate_preferences curate_rewards training_audit compose_contract
        compose_curated_calibration compose_curated_coding compose_curated_identity
        compose_curated_identity_facade compose_curated_record_facade
        compose_curated_record compose_curated_run compose_curated_run_facade
        compose_destination compose_trajectory check_records census record_kind round_txn
        """.split(),
}
COMPOSE_SPLIT_MODULES = tuple(
    name
    for name in pipeline_import_catalog.COMPOSE_DIRECT_LOADERS
    if name
    not in {
        "compose_curated_record_dispatch",
        "compose_curated_record_services",
        "compose_curated_run_bootstrap",
    }
)


def _load_direct(name: str) -> ModuleType:
    with direct_pipeline_path():
        return pipeline_import_catalog.load_direct(name)


def _load_mode(name: str, mode: str) -> ModuleType:
    if mode == "direct":
        return _load_direct(name)
    return pipeline_import_catalog.load_package(name)


def _facade_pair(mode: str) -> tuple[ModuleType, ModuleType]:
    if mode == "direct":
        direct = _load_direct("compose_curated")
        packaged = pipeline_import_catalog.load_package("compose_curated")
    else:
        packaged = pipeline_import_catalog.load_package("compose_curated")
        direct = _load_direct("compose_curated")
    return direct, packaged


def _assert_adapter_first_process(
    adapter_name: str,
    adapter_mode: str,
    facade_mode: str,
) -> None:
    adapter = _load_mode(adapter_name, adapter_mode)
    direct, packaged = _facade_pair(facade_mode)
    other_mode = "package" if adapter.__package__ == "" else "direct"
    if direct is not packaged:
        raise AssertionError("compose_curated module identity diverged")
    if adapter is not _load_mode(adapter_name, other_mode):
        raise AssertionError("adapter module identity diverged")
    if adapter._facade() is not direct:
        raise AssertionError("adapter bound an abandoned facade")


def _missing_optional_recorder(imported: list[str], optional_name: str):
    def record_import(name: str, package: str | None = None) -> ModuleType:
        full_name = f"{package}{name}" if package else name
        imported.append(full_name)
        if full_name == optional_name:
            raise ModuleNotFoundError(f"No module named {full_name!r}", name=full_name)
        return ModuleType(full_name)

    return record_import


def _missing_optional_dependency(name: str, package: str | None = None) -> ModuleType:
    if name == "curate_trajectory_preferences":
        raise ModuleNotFoundError(
            "No module named 'trajectory_dependency'",
            name="trajectory_dependency",
        )
    return ModuleType(name)


class ComposeCuratedImportContracts(unittest.TestCase):
    def test_facade_bootstrap_preserves_import_order_and_optional_fail_open(self):
        bootstrap = pipeline_import_catalog.load_package("compose_curated_facade_bootstrap")
        for package, names in FACADE_IMPORT_ORDERS.items():
            with self.subTest(package=package):
                imported: list[str] = []
                prefix = f"{package}." if package else ""
                optional_name = f"{prefix}curate_trajectory_preferences"
                import_module = _missing_optional_recorder(imported, optional_name)

                with (
                    mock.patch.object(bootstrap, "_prepare_facade_identity"),
                    mock.patch.object(
                        bootstrap.importlib,
                        "import_module",
                        side_effect=import_module,
                    ),
                ):
                    modules = bootstrap.bootstrap_facade_imports(package)

                self.assertEqual(
                    imported,
                    [*(f"{prefix}{name}" for name in names), optional_name],
                )
                self.assertIsNone(modules["curate_trajectory_preferences"])
                self.assertEqual(
                    modules["allowed_missing"],
                    {
                        "curate_trajectory_preferences",
                        f"{package}.curate_trajectory_preferences",
                    },
                )

    def test_facade_bootstrap_reraises_a_missing_optional_dependency(self):
        bootstrap = pipeline_import_catalog.load_package("compose_curated_facade_bootstrap")
        with (
            mock.patch.object(bootstrap, "_prepare_facade_identity"),
            mock.patch.object(
                bootstrap.importlib,
                "import_module",
                side_effect=_missing_optional_dependency,
            ),
            self.assertRaisesRegex(ModuleNotFoundError, "trajectory_dependency"),
        ):
            bootstrap.bootstrap_facade_imports(None)

    def test_compose_adapters_import_first_bind_the_canonical_facade(self):
        for adapter_name, adapter_mode, facade_mode in ADAPTER_FIRST_CASES:
            with self.subTest(
                adapter=adapter_name,
                adapter_mode=adapter_mode,
                facade_mode=facade_mode,
            ):
                context = multiprocessing.get_context("spawn")
                process = context.Process(
                    target=_assert_adapter_first_process,
                    args=(adapter_name, adapter_mode, facade_mode),
                )
                process.start()
                process.join(30)
                if process.is_alive():
                    process.terminate()
                    process.join(5)
                    if process.is_alive():
                        process.kill()
                        process.join(5)
                    self.fail("adapter-first import probe timed out")
                self.assertEqual(
                    process.exitcode,
                    0,
                    "adapter-first import probe failed in its clean interpreter",
                )

    def test_split_cli_preserves_original_help_contract(self):
        """Extraction retains the core CLI's published description and option text."""

        with isolated_pipeline_modules(COMPOSE_SPLIT_MODULES):
            core = pipeline_import_catalog.load_package("compose_curated_run")
            cli = pipeline_import_catalog.load_package("compose_curated_run_cli")
            output = io.StringIO()
            with redirect_stdout(output), self.assertRaises(SystemExit) as raised:
                cli.parse_args(["--help"])
            self.assertEqual(raised.exception.code, 0)
            help_text = output.getvalue()
            normalized_help = " ".join(help_text.split())
            self.assertIn(core.__doc__.split("\n\n")[0], help_text)
            self.assertIn(
                "explicit reward calibration sidecar; defaults to the FFPC sidecar",
                normalized_help,
            )
            self.assertIn(
                "exit 1 when the composed tree is not training_ready",
                normalized_help,
            )

    def test_compose_facade_preserves_internal_compatibility_bindings(self):
        """The split retains base-era bindings beyond the documented public API."""

        facade = pipeline_import_catalog.load_package("compose_curated")
        historical = """
        CalibrationContext CalibrationServices RecordContext RecordServices
        SourceCoordinates SourceLineContext StageDefinition _COMPATIBILITY_EXPORTS
        _authenticate_composed_artifacts_impl _calibration_services
        _capture_source_snapshot_impl _claim_output_id_impl
        _commit_compose_summary_impl _compose_one_line_impl
        _compose_record_from_context _compose_record_impl _compose_run_impl
        _compose_run_summary_impl _compose_source_file_impl
        _compose_source_line_impl _facade_run_hooks _facade_run_services
        _new_manifest_entry_impl _only_identity_shape_details
        _record_excluded_line_impl _record_retained_line_impl _record_services
        _retained_rewards_impl _reward_not_applicable_impl _reward_refusal_impl
        _transform_contract_impl _write_compose_provenance_impl
        _write_emitted_records_impl stage
        """.split()
        self.assertEqual(
            [name for name in historical if not hasattr(facade, name)],
            [],
        )

    def test_compose_facade_delegate_remains_a_live_seam(self):
        facade = pipeline_import_catalog.load_package("compose_curated")
        with mock.patch.object(
            facade,
            "_facade_delegate",
            side_effect=RuntimeError("facade delegation seam"),
        ):
            with self.assertRaisesRegex(RuntimeError, "facade delegation seam"):
                facade.jsonl_physical_lines(b"{}\n")


if __name__ == "__main__":
    unittest.main()
