#!/usr/bin/env python3
"""The distillation contract's surface: the schema file agrees with the module,
the domain-neutral primitives are the shared envelope's own objects, and the
facade re-exports every sibling under both import forms."""

import importlib
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))  # the shared test support, by bare name

from distill_contract_test_support import (  # noqa: E402
    REPO,
    SCHEMA_PATH,
    envelope,
    minimal_record,
    oc,
)


class SchemaFileAgreesWithTheModule(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))

    def test_family_enum_matches(self):
        enum = self.schema["properties"]["family"]["enum"]
        self.assertEqual(sorted(enum), sorted(oc.FAMILIES))

    def test_schema_version_const_matches(self):
        self.assertEqual(
            self.schema["properties"]["schema_version"]["const"], oc.SCHEMA_VERSION
        )

    def test_oracle_type_enum_matches(self):
        enum = self.schema["$defs"]["oracle"]["properties"]["type"]["enum"]
        self.assertEqual(set(enum), set(oc.ORACLE_TYPES))

    def test_generator_authority_const_matches(self):
        const = self.schema["$defs"]["generator"]["properties"]["authority"]["const"]
        self.assertEqual(const, oc.GENERATOR_AUTHORITY)

    def test_oracle_authority_enum_matches(self):
        enum = self.schema["$defs"]["oracle"]["properties"]["authority"]["enum"]
        self.assertEqual(set(enum), set(oc.ORACLE_AUTHORITIES))


class BuiltOnTheSharedEnvelope(unittest.TestCase):
    """The domain-neutral primitives are the envelope's own objects (#172)."""

    MOVED = (
        "GENERATOR_SECTIONS",
        "SHA256_RE",
        "ISO_8601_RE",
        "ContractError",
        "OracleUnavailable",
        "canonical_json",
        "utc_now_iso",
        "is_number",
        "is_enum_value",
        "record_digest",
    )

    def test_the_moved_primitives_are_the_envelopes_objects(self):
        for name in self.MOVED:
            with self.subTest(name=name):
                self.assertIs(getattr(oc, name), getattr(envelope, name))

    def test_the_reserved_key_scan_is_the_envelopes_bounded_walker(self):
        record = minimal_record()
        record["scenario"]["junk"] = [{"outcome": index} for index in range(10_000)]
        errors = oc.check_generator_oracle_separation(record, "x")
        reserved = [e for e in errors if "ORACLE_FIELD_IN_GENERATOR_NAMESPACE" in e]
        self.assertEqual(len(reserved), 1, errors)
        self.assertLess(len(reserved[0]), 4_000, len(reserved[0]))
        self.assertIn("scan capped", reserved[0])

    def test_the_prediction_naming_rule_runs_after_the_shared_scan(self):
        record = minimal_record()
        record["scenario"]["outcome"] = "leaked"
        record["candidate_prediction"]["expected_latency_ms"] = 3.0
        errors = oc.check_generator_oracle_separation(record, "x")
        shared = envelope.check_generator_oracle_separation(record, oc.ORACLE_ONLY_KEYS, "x")
        self.assertEqual(errors[: len(shared)], shared)
        self.assertEqual(len(errors), len(shared) + 1, errors)
        self.assertIn("predicted_*", errors[-1])

    def test_read_jsonl_uses_the_envelopes_parse_hooks(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "overflow.jsonl"
            path.write_text('{"id": "x", "value": 1e999}\n{"id": "y", "value": 0.5}\n')
            entries = oc.read_jsonl(path)
            self.assertIsNone(entries[0][1])
            self.assertEqual(entries[1][1], {"id": "y", "value": 0.5})

    def test_both_import_forms_are_one_module_object(self):
        if str(REPO) not in sys.path:
            sys.path.append(str(REPO))
        module = importlib.import_module("pipelines.oracle_grounded.distill_contract")
        self.assertIs(module, oc)
        self.assertIs(module.ContractError, envelope.ContractError)


class SplitByResponsibility(unittest.TestCase):
    """The contract is a facade over sibling modules that bind both import forms."""

    SIBLINGS = (
        "import_twins",
        "distill_vocabulary",
        "distill_builders",
        "distill_measurements",
        "distill_energy_claims",
        "distill_blocks",
        "distill_curation",
        "distill_jsonl",
        "distill_labels",
    )

    def test_every_sibling_binds_both_import_forms_to_one_module_object(self):
        if str(REPO) not in sys.path:
            sys.path.append(str(REPO))
        for name in self.SIBLINGS:
            with self.subTest(name=name):
                direct = importlib.import_module(f"oracle_grounded.{name}")
                packaged = importlib.import_module(f"pipelines.oracle_grounded.{name}")
                self.assertIs(direct, packaged)

    def test_the_facade_exports_every_declared_name(self):
        for name in oc.__all__:
            with self.subTest(name=name):
                self.assertTrue(hasattr(oc, name), name)

    def test_the_facade_names_are_the_siblings_objects(self):
        from oracle_grounded import distill_builders, distill_vocabulary

        self.assertIs(oc.build_record, distill_builders.build_record)
        self.assertIs(oc.FAMILIES, distill_vocabulary.FAMILIES)
        self.assertIs(oc.ContractError, envelope.ContractError)

    def test_an_unknown_measurement_option_is_refused(self):
        with self.assertRaises(TypeError):
            oc.new_measurement("latency_ms", 1.0, "clock", bogus=True)



class VocabularyPredicates(unittest.TestCase):
    """The identity predicates the checks are built on refuse truthiness."""

    def test_is_true_accepts_only_the_boolean_true(self):
        self.assertTrue(oc.is_true(True))
        for value in (1, "yes", [0], {"a": 1}, None, False):
            with self.subTest(value=value):
                self.assertFalse(oc.is_true(value))

    def test_is_genuine_int_excludes_booleans_and_floats(self):
        self.assertTrue(oc.is_genuine_int(3))
        for value in (True, False, 3.0, "3", None):
            with self.subTest(value=value):
                self.assertFalse(oc.is_genuine_int(value))

    def test_missing_string_treats_blank_and_non_strings_as_missing(self):
        self.assertFalse(oc.missing_string("x"))
        for value in ("", "   ", None, 7):
            with self.subTest(value=value):
                self.assertTrue(oc.missing_string(value))


class ImportTwinNames(unittest.TestCase):
    def test_the_twin_of_each_import_form_is_the_other(self):
        from oracle_grounded import import_twins

        self.assertEqual(
            import_twins.import_twin_of("oracle_grounded.distill_contract"),
            "pipelines.oracle_grounded.distill_contract",
        )
        self.assertEqual(
            import_twins.import_twin_of("pipelines.oracle_grounded.distill_contract"),
            "oracle_grounded.distill_contract",
        )


class SupportedImportForms(unittest.TestCase):
    """The advertised import forms, each in a fresh interpreter.

    The CLI form puts ``pipelines/`` on ``sys.path``; the package form puts
    the repository root there. Both may be used in one process in either
    order and resolve to one module object, so a ``ContractError`` raised
    through one name is caught through the other. The flat-then-package
    order once failed with ``ImportError: cannot import name
    'oracle_grounded' from 'pipelines'`` because the bound twin of the
    module short-circuited the import of its parent package.
    """

    FLAT = f"import sys; sys.path.insert(0, {str(REPO / 'pipelines')!r}); "
    FLAT += "from oracle_grounded import distill_contract as flat; "
    PKG = f"import sys; sys.path.insert(0, {str(REPO)!r}); "
    PKG += "from pipelines.oracle_grounded import distill_contract as pkg; "
    SAME = (
        "assert pkg is flat, 'two module objects'; "
        "assert pkg.ContractError is flat.ContractError, 'two error classes'; "
        "print('one object')"
    )

    def run_fresh(self, code: str) -> str:
        with tempfile.TemporaryDirectory() as cwd:
            completed = subprocess.run(
                [sys.executable, "-c", code], capture_output=True, text=True, cwd=cwd, timeout=120
            )
        self.assertEqual(completed.returncode, 0, completed.stderr[-2000:])
        return completed.stdout.strip()

    def test_the_cli_form_alone(self):
        self.assertEqual(
            self.run_fresh(self.FLAT + "print(flat.SCHEMA_VERSION == flat.SCHEMA_VERSION)"), "True"
        )

    def test_the_package_form_alone(self):
        self.assertEqual(
            self.run_fresh(self.PKG + "import pipelines.oracle_grounded.distill_contract as x; "
                           "print(x is pkg)"),
            "True",
        )

    def test_package_then_cli_is_one_object(self):
        self.assertEqual(self.run_fresh(self.PKG + self.FLAT + self.SAME), "one object")

    def test_cli_then_package_is_one_object(self):
        # The once-failing order, through both spellings of the package form.
        code = (
            self.FLAT
            + "import pipelines.oracle_grounded.distill_contract as pkg; "
            + "from pipelines.oracle_grounded import distill_contract as pkg2; "
            + "assert pkg2 is pkg; "
            + self.SAME
        )
        self.assertEqual(self.run_fresh(code), "one object")

    def test_every_sibling_is_one_object_across_both_forms(self):
        code = (
            self.FLAT
            + self.PKG
            + "import importlib, sys; names = "
            + repr(list(SplitByResponsibility.SIBLINGS))
            + "; bad = [n for n in names if sys.modules.get(f'oracle_grounded.{n}') "
            + "is not sys.modules.get(f'pipelines.oracle_grounded.{n}')]; print(bad)"
        )
        self.assertEqual(self.run_fresh(code), "[]")


if __name__ == "__main__":
    unittest.main()
