#!/usr/bin/env python3
"""Call-time facade contracts for the extracted record service graph."""

from __future__ import annotations

import importlib
import sys
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

if __package__:
    from . import compose_curated_import_contract_support as import_contract_support
else:
    import compose_curated_import_contract_support as import_contract_support


REPO = Path(__file__).resolve().parents[1]
PIPELINES = REPO / "pipelines"
if str(PIPELINES) not in sys.path:
    sys.path.insert(0, str(PIPELINES))


class FacadeSentinel(RuntimeError):
    """A replacement facade binding reached through an existing service."""


def _unused(*_args, **_kwargs):
    return None


class ComposeRecordServiceContracts(unittest.TestCase):
    def test_record_service_builder_has_one_package_direct_identity(self):
        for package_first in (False, True):
            with self.subTest(package_first=package_first):
                exit_code = import_contract_support.clean_process_identity_exit_code(
                    REPO,
                    (
                        "compose_curated_record_dispatch",
                        "compose_curated_record_services",
                    ),
                    package_first=package_first,
                )
                self.assertEqual(exit_code, 0)

    def test_clean_process_timeout_terminates_and_reaps_the_child(self):
        process = mock.Mock(exitcode=None)
        process.is_alive.side_effect = (True, False)
        context = mock.Mock()
        context.Process.return_value = process

        with (
            mock.patch.object(
                import_contract_support.multiprocessing,
                "get_context",
                return_value=context,
            ),
            self.assertRaisesRegex(TimeoutError, "module identity check timed out"),
        ):
            import_contract_support.clean_process_identity_exit_code(
                REPO,
                ("compose_curated_record_services",),
                package_first=False,
            )

        process.terminate.assert_called_once_with()
        self.assertEqual(len(process.join.call_args_list), 2)
        self.assertTrue(all(call.args for call in process.join.call_args_list))

    def test_built_services_resolve_every_stage_from_the_live_facade(self):
        try:
            service_builder = importlib.import_module("compose_curated_record_services")
        except ModuleNotFoundError:
            self.fail("compose_curated_record_services is missing")
        from compose_curated_record import RecordServices

        facade = SimpleNamespace(
            RecordServices=RecordServices,
            _compose_identity_stage=_unused,
            _compose_bridge_stage=_unused,
            _compose_preferences_stage=_unused,
            _compose_coding_stage=_unused,
            _compose_rewards_stage=_unused,
        )
        services = service_builder.build_record_services(facade)
        source = SimpleNamespace(
            path="factory/batch.jsonl",
            line=1,
            sha256="a" * 64,
            file_sha256="b" * 64,
        )
        context = SimpleNamespace(source=source, calibration=None)
        cases = (
            ("_compose_identity_stage", services.identity, ({}, [], source)),
            ("_compose_bridge_stage", services.bridge, ({}, [], source)),
            ("_compose_preferences_stage", services.preferences, ({}, [], context)),
            ("_compose_coding_stage", services.coding, ({}, None, [], context)),
            ("_compose_rewards_stage", services.rewards, ({}, [], context)),
        )
        for binding, invocation, arguments in cases:
            with self.subTest(binding=binding):
                setattr(
                    facade,
                    binding,
                    lambda *_args, _binding=binding, **_kwargs: (_ for _ in ()).throw(
                        FacadeSentinel(_binding)
                    ),
                )
                with self.assertRaisesRegex(FacadeSentinel, binding):
                    invocation(*arguments)
                setattr(facade, binding, _unused)


if __name__ == "__main__":
    unittest.main()
