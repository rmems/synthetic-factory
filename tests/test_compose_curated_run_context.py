#!/usr/bin/env python3
"""Focused contracts for the extracted compose run boundary."""

import tempfile
import unittest
from dataclasses import FrozenInstanceError
from pathlib import Path

PIPELINES = Path(__file__).resolve().parents[1] / "pipelines"
if str(PIPELINES) not in __import__("sys").path:
    __import__("sys").path.insert(0, str(PIPELINES))

from compose_contract import ComposeError  # noqa: E402


def calibration_services():
    """Provide deterministic collaborators unused by the guard under test."""

    from compose_curated_calibration import CalibrationServices

    def unexpected(*_args, **_kwargs):
        raise AssertionError("the malformed default must fail before file parsing")

    return CalibrationServices(
        read_exact_child_file=unexpected,
        reject_duplicate_object_keys=unexpected,
        reject_json_constant=unexpected,
        parse_finite_json_float=unexpected,
        units_migration_catalog=unexpected,
        sha256_hex=unexpected,
        audit_run=unexpected,
    )


class ComposeRunContextContract(unittest.TestCase):
    def test_run_coordinates_are_immutable(self):
        """Mutation must not redirect a run after source authentication."""

        try:
            from compose_curated_run import ComposeRunContext
        except ModuleNotFoundError:
            self.fail("compose_curated_run.ComposeRunContext is missing")

        context = ComposeRunContext(Path("source"), Path("destination"), None)

        with self.assertRaises(FrozenInstanceError):
            context.destination = Path("other")

    def test_physical_jsonl_framing_uses_lf_only(self):
        """Unicode separators remain payload bytes while CRLF loses only CR."""

        try:
            from compose_curated_run import jsonl_physical_lines
        except ModuleNotFoundError:
            self.fail("compose_curated_run.jsonl_physical_lines is missing")

        payload = b'"line\xe2\x80\xa8separator"\r\n{"second":true}\n'

        self.assertEqual(
            jsonl_physical_lines(payload),
            [b'"line\xe2\x80\xa8separator"', b'{"second":true}'],
        )

    def test_non_regular_default_calibration_fails_closed(self):
        """A canonical directory must never be recorded as no calibration."""

        try:
            from compose_curated_calibration import CalibrationContext, load_calibration
        except ModuleNotFoundError:
            self.fail("compose_curated_calibration boundary is missing")

        with tempfile.TemporaryDirectory() as td:
            source = Path(td)
            default = source / "failure-as-fuel-preference-cascade/units-migration.json"
            default.mkdir(parents=True)
            context = CalibrationContext(source, None)

            with self.assertRaisesRegex(ComposeError, "not an exact regular file"):
                load_calibration(context, calibration_services())

    def test_direct_factory_root_selects_its_own_calibration_sidecar(self):
        from compose_curated_calibration import CalibrationContext, _calibration_path

        with tempfile.TemporaryDirectory() as td:
            source = Path(td) / "failure-as-fuel-preference-cascade"
            source.mkdir()
            sidecar = source / "units-migration.json"
            sidecar.write_text("{}", encoding="utf-8")

            self.assertEqual(
                _calibration_path(CalibrationContext(source, None)),
                (sidecar, "source_run"),
            )

    def test_nested_calibration_exhaustion_is_reported_as_invalid_json(self):
        """A pathological calibration document must not abort the compose run."""

        from compose_curated_calibration import _decode_calibration

        depth = 200_000
        payload = b"[" * depth + b"]" * depth

        with self.assertRaisesRegex(ComposeError, "invalid calibration JSON"):
            _decode_calibration(Path("units-migration.json"), payload, calibration_services())


if __name__ == "__main__":
    unittest.main()
