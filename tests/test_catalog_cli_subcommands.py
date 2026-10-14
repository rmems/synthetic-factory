"""The shared subcommand layer behind seven mill packages' ``cli`` modules.

``tests/test_flk.py`` ... ``tests/test_sbox.py`` drive each package's
``cli.run`` end to end against its real catalog. This module pins what those
suites cannot reach through a real package: the ``catalog-check`` findings
exit (a real catalog refuses an empty plant list before it can report a
finding), the prose and stderr renderings, the extract shape's error and
bare-``ContractError`` paths, and both import forms of every thin ``cli``.
"""

from __future__ import annotations

import ast
import contextlib
import io
import json
import multiprocessing
import shutil
import sys
import tempfile
import unittest
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path
from types import ModuleType, SimpleNamespace
from unittest import mock

if __package__:
    from . import catalog_cli_import_probe as probe
    from .pipeline_import_test_support import clean_package_imports, direct_pipeline_path
else:
    import catalog_cli_import_probe as probe
    from pipeline_import_test_support import clean_package_imports, direct_pipeline_path

from pipelines.catalog_cli import source_const, subcommands
from pipelines.catalog_cli.entry import _import_sibling

GENERATE_PACKAGES = ("flk", "gql", "msd", "rag", "saf")
EXTRACT_PACKAGES = ("mac", "sbox")


class StubRefusal(Exception):
    def __init__(self, code: str, message: str) -> None:
        super().__init__(f"{code}: {message}")
        self.code = code


class CodeLessRefusal(Exception):
    """A generate-shape refusal that never sets ``code``."""


class StubContractError(ValueError):
    """Stands in for ``envelope.ContractError``: a refusal that may carry no code."""


class CodedContractError(StubContractError):
    def __init__(self, code: str, message: str) -> None:
        super().__init__(f"{code}: {message}")
        self.code = code


def _module(name: str, **attributes: object) -> ModuleType:
    module = ModuleType(name)
    vars(module).update(attributes)
    return module


def _invoke(commands, argv: list[str]) -> tuple[int, str, str]:
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        code = commands.run(argv)
    return code, out.getvalue(), err.getvalue()


class GenerateShape(unittest.TestCase):
    def setUp(self):
        self.checked: list[Path] = []
        self.requests: list[dict] = []
        self.findings: list[dict] = []
        self.failure: Exception | None = None
        catalog = _module(
            "stub_catalog",
            default_catalog_dir=lambda: Path("/stub/default"),
            catalog_check=self._catalog_check,
            load_catalog=lambda directory: SimpleNamespace(
                catalog_id="stub-v1", plants=(1, 2), mills=(1,)
            ),
        )
        generate = _module(
            "stub_generate",
            GenerateRequest=lambda **fields: fields,
            run=self._run,
        )
        self.commands = subcommands.GenerateCommands(
            prog="stub.cli",
            description="Stub mill commands.",
            catalog=catalog,
            generate=generate,
            refusal=StubRefusal,
        )

    def _catalog_check(self, directory: Path) -> list[dict]:
        self.checked.append(directory)
        return self.findings

    def _run(self, request: dict) -> dict:
        self.requests.append(request)
        if self.failure is not None:
            raise self.failure
        return {"records": 2, "pairs": 1}

    def _help(self, commands, argv: list[str]) -> str:
        out = io.StringIO()
        with contextlib.redirect_stdout(out), self.assertRaises(SystemExit) as caught:
            commands.run(argv)
        self.assertEqual(caught.exception.code, 0)
        return out.getvalue()

    def test_findings_exit_one_and_report_them_on_the_default_catalog(self):
        self.findings = [{"code": "stub.empty", "detail": "empty catalog"}]
        code, out, err = _invoke(self.commands, ["catalog-check", "--json"])
        self.assertEqual((code, err), (1, ""))
        self.assertEqual(self.checked, [Path("/stub/default")])
        self.assertEqual(
            out,
            "{\n"
            '  "catalog_id": "stub-v1",\n'
            '  "command": "catalog-check",\n'
            '  "findings": [\n'
            "    {\n"
            '      "code": "stub.empty",\n'
            '      "detail": "empty catalog"\n'
            "    }\n"
            "  ],\n"
            '  "mills": 1,\n'
            '  "plants": 2,\n'
            '  "status": "findings"\n'
            "}\n",
        )
        code, out, _ = _invoke(self.commands, ["catalog-check"])
        self.assertEqual((code, out), (1, "catalog-check findings: stub-v1 2 plants / 1 mills\n"))

    def test_catalog_check_prose_reads_the_named_catalog(self):
        code, out, err = _invoke(self.commands, ["catalog-check", "--catalog", "/stub/named"])
        self.assertEqual((code, out, err), (0, "catalog-check ok: stub-v1 2 plants / 1 mills\n", ""))
        self.assertEqual(self.checked, [Path("/stub/named")])

    def test_generate_passes_every_selector_and_prints_one_prose_line(self):
        code, out, err = _invoke(
            self.commands, ["generate", "--out", "/stub/out", "--mill", "stub_r0001"]
        )
        self.assertEqual((code, out, err), (0, "generated 2 records (1 pairs) into /stub/out\n", ""))
        self.assertEqual(
            self.requests,
            [
                {
                    "catalog_dir": Path("/stub/default"),
                    "out_dir": Path("/stub/out"),
                    "plant_id": None,
                    "mill_id": "stub_r0001",
                    "all_plants": False,
                    "round": None,
                }
            ],
        )

    def test_a_refusal_is_prose_on_stderr_or_one_compact_exact_json_line(self):
        self.failure = StubRefusal("stub.destination_exists", "/stub/out exists")
        argv = ["generate", "--out", "/stub/out", "--all"]
        code, out, err = _invoke(self.commands, argv)
        self.assertEqual((code, out), (2, ""))
        self.assertEqual(err, "stub.destination_exists: /stub/out exists\n")
        code, out, err = _invoke(self.commands, [*argv, "--json"])
        self.assertEqual((code, err), (2, ""))
        self.assertEqual(
            out,
            '{"code":"stub.destination_exists","command":"generate",'
            '"message":"stub.destination_exists: /stub/out exists","status":"refused"}\n',
        )

    def test_any_other_exception_propagates(self):
        self.failure = RuntimeError("not a refusal")
        with self.assertRaisesRegex(RuntimeError, "not a refusal"):
            _invoke(self.commands, ["generate", "--out", "/stub/out", "--all"])

    def test_a_refusal_without_code_raises(self):
        commands = subcommands.GenerateCommands(
            prog="stub.cli",
            description="Stub mill commands.",
            catalog=self.commands.catalog,
            generate=self.commands.generate,
            refusal=CodeLessRefusal,
        )
        self.failure = CodeLessRefusal("no code")
        with self.assertRaises(AttributeError):
            _invoke(commands, ["generate", "--out", "/stub/out", "--all", "--json"])

    def test_help_names_the_package_unit(self):
        default_help = self._help(self.commands, ["generate", "--help"])
        self.assertIn("every plant in order", default_help)
        self.assertIn("every plant in the catalog", default_help)
        pairs = subcommands.GenerateCommands(
            prog="stub.cli",
            description="Stub.",
            catalog=self.commands.catalog,
            generate=self.commands.generate,
            refusal=StubRefusal,
            generate_help="safety-case pairs into a new directory",
            unit="pair",
        )
        self.assertIn("safety-case pairs into a new directory", self._help(pairs, ["--help"]))
        pair_help = self._help(pairs, ["generate", "--help"])
        self.assertIn("every pair in order", pair_help)
        self.assertIn("every pair in the catalog", pair_help)


class ExtractShape(unittest.TestCase):
    def setUp(self):
        self.failure: Exception | None = None
        catalog = _module(
            "stub_catalog",
            catalog_check=lambda: {
                "status": "ok",
                "plants": 3,
                "sources": 2,
                "full_row_count": 9,
            },
        )
        generate = _module("stub_generate", plants_from_source=self._plants)
        self.commands = subcommands.ExtractCommands(
            prog="stub.cli",
            description="Stub extract commands.",
            catalog=catalog,
            generate=generate,
            refusal=StubContractError,
        )
        root = Path(tempfile.mkdtemp(prefix="catalog-cli-"))
        self.addCleanup(shutil.rmtree, root, True)
        self.source = root / "src.py"
        self.source.write_text("PLANTS = []\n", encoding="utf-8")
        self.argv = ["extract", "--source", str(self.source)]

    def _plants(self, text: str) -> tuple[dict, ...]:
        if self.failure is not None:
            raise self.failure
        return ({"slug": "stub", "chars": len(text)},)

    def test_catalog_check_and_extract_print_one_prose_line(self):
        self.assertEqual(
            _invoke(self.commands, ["catalog-check"]),
            (0, "catalog-check ok: 3 plants / 2 sources / 9 full rows\n", ""),
        )
        self.assertEqual(_invoke(self.commands, self.argv), (0, "extract ok: 1 plants from src.py\n", ""))

    def test_an_unexpected_exception_is_reported_as_an_error(self):
        self.failure = KeyError("slug")
        self.assertEqual(_invoke(self.commands, self.argv), (2, "", "KeyError: 'slug'\n"))
        error_line = '{"command": "extract", "message": "KeyError: \'slug\'", "status": "error"}\n'
        self.assertEqual(_invoke(self.commands, [*self.argv, "--json"]), (2, error_line, ""))

    def test_a_coded_refusal_reports_its_code(self):
        self.failure = CodedContractError("SOURCE_NOT_PARSEABLE", "bad source")
        self.assertEqual(
            _invoke(self.commands, self.argv), (2, "", "SOURCE_NOT_PARSEABLE: bad source\n")
        )
        refusal_line = (
            '{"code": "SOURCE_NOT_PARSEABLE", "command": "extract", '
            '"message": "SOURCE_NOT_PARSEABLE: bad source", "status": "refused"}\n'
        )
        self.assertEqual(_invoke(self.commands, [*self.argv, "--json"]), (2, refusal_line, ""))

    def test_a_bare_contract_error_reports_a_null_code(self):
        self.failure = StubContractError("no code here")
        refusal_line = (
            '{"code": null, "command": "extract", "message": "no code here", '
            '"status": "refused"}\n'
        )
        self.assertEqual(_invoke(self.commands, [*self.argv, "--json"]), (2, refusal_line, ""))


def _package_clis() -> dict[str, ModuleType]:
    from pipelines.flk import cli as flk
    from pipelines.gql import cli as gql
    from pipelines.mac import cli as mac
    from pipelines.msd import cli as msd
    from pipelines.rag import cli as rag
    from pipelines.saf import cli as saf
    from pipelines.sbox import cli as sbox

    return {"flk": flk, "gql": gql, "msd": msd, "rag": rag, "saf": saf, "mac": mac, "sbox": sbox}


def _flat_clis() -> dict[str, ModuleType]:
    from flk import cli as flk
    from gql import cli as gql
    from mac import cli as mac
    from msd import cli as msd
    from rag import cli as rag
    from saf import cli as saf
    from sbox import cli as sbox

    return {"flk": flk, "gql": gql, "msd": msd, "rag": rag, "saf": saf, "mac": mac, "sbox": sbox}


def _shared_twins() -> tuple[ModuleType, ModuleType]:
    """Both names of the shared module, as loaded by the ``cli`` imports above."""

    return sys.modules["catalog_cli.subcommands"], sys.modules["pipelines.catalog_cli.subcommands"]


class ImportForms(unittest.TestCase):
    def _assert_one_object_each(self, flat: dict, packaged: dict) -> None:
        shared_flat, shared_packaged = _shared_twins()
        self.assertIs(shared_flat, shared_packaged)
        shapes = {name: shared_flat.GenerateCommands for name in GENERATE_PACKAGES}
        shapes.update({name: shared_flat.ExtractCommands for name in EXTRACT_PACKAGES})
        for name, shape in shapes.items():
            with self.subTest(package=name):
                self.assertIs(flat[name], packaged[name])
                self.assertEqual(flat[name].__all__, ["build_parser", "run"])
                self.assertIsInstance(flat[name].run.__self__, shape)
                self.assertEqual(flat[name].build_parser().prog, f"{name}.cli")
        for name in GENERATE_PACKAGES:
            self.assertTrue(callable(flat[name].main))

    def test_package_first_then_flat(self):
        with clean_package_imports():
            packaged = _package_clis()
            with direct_pipeline_path():
                flat = _flat_clis()
                self._assert_one_object_each(flat, packaged)

    def test_flat_first_then_package(self):
        with clean_package_imports(), direct_pipeline_path():
            flat = _flat_clis()
            packaged = _package_clis()
            self._assert_one_object_each(flat, packaged)

    def _main_exit(self, cli: ModuleType, argv: list[str]) -> tuple[object, str]:
        out = io.StringIO()
        with (
            mock.patch.object(sys, "argv", argv),
            contextlib.redirect_stdout(out),
            self.assertRaises(SystemExit) as caught,
        ):
            cli.main()
        return caught.exception.code, out.getvalue()

    def test_pipelines_loaded_before_the_flat_form_gets_the_attribute(self):
        with clean_package_imports():
            import pipelines

            with direct_pipeline_path():
                flat = _flat_clis()
                packaged = _package_clis()
                self._assert_one_object_each(flat, packaged)
                self.assertIs(pipelines.catalog_cli, sys.modules["catalog_cli"])

    def test_the_parent_attribute_resolves_in_every_order_in_a_fresh_interpreter(self):
        context = multiprocessing.get_context("spawn")
        for order in probe.ORDERS:
            with (
                self.subTest(order=order),
                ProcessPoolExecutor(max_workers=1, mp_context=context) as pool,
            ):
                report = pool.submit(probe.report, order).result(timeout=180)
                self.assertEqual(report, {"attribute": True, "chain": True, "package_twin": True})

    def test_generate_shape_main_exits_with_the_run_code(self):
        clis = _package_clis()
        for name in GENERATE_PACKAGES:
            with self.subTest(package=name):
                code, out = self._main_exit(clis[name], [name, "catalog-check", "--json"])
                self.assertEqual(code, 0)
                self.assertIn('"status": "ok"', out)


class SourceConstTests(unittest.TestCase):
    def test_const_dict_rejects_unpacking_before_evaluating(self):
        node = ast.parse("{**{}}").body[0].value
        self.assertIsInstance(node, ast.Dict)
        seen: list[ast.AST] = []

        def evaluate(item: ast.AST) -> int:
            seen.append(item)
            return 1

        with self.assertRaises(StubRefusal) as caught:
            source_const.const_dict(
                node,
                evaluate,
                lambda: StubRefusal("code", "plant source uses dict unpacking"),
            )
        self.assertEqual(seen, [])
        self.assertIn("dict unpacking", str(caught.exception))

    def test_const_dict_evaluates_literal_keys(self):
        node = ast.parse("{'a': 1}").body[0].value
        result = source_const.const_dict(
            node, ast.literal_eval, lambda: StubRefusal("code", "unused")
        )
        self.assertEqual(result, {"a": 1})

    def test_registry_ids_skip_non_strings_and_refuse_a_bad_shape(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            registry = root / "config"
            registry.mkdir()
            (registry / "FACTORY-REGISTRY.json").write_text(
                json.dumps(
                    {
                        "factories": [
                            {"path_id": "flk"},
                            "not-a-row",
                            {"path_id": 3},
                            {"path_id": "gql"},
                        ]
                    }
                ),
                encoding="utf-8",
            )

            def repo_root() -> Path:
                return root

            def refuse(message: str) -> StubRefusal:
                return StubRefusal("finding", message)

            ids = source_const.registry_factory_ids(repo_root, json.loads, refuse)
            self.assertEqual(ids, {"flk", "gql"})

            (registry / "FACTORY-REGISTRY.json").write_text(
                json.dumps({"factories": {}}), encoding="utf-8"
            )
            with self.assertRaises(StubRefusal) as caught:
                source_const.registry_factory_ids(repo_root, json.loads, refuse)
            self.assertIn("not a list", str(caught.exception))

            (registry / "FACTORY-REGISTRY.json").unlink()
            with self.assertRaises(StubRefusal) as caught:
                source_const.registry_factory_ids(repo_root, json.loads, refuse)
            self.assertIn("unreadable", str(caught.exception))

    def test_plant_const_eval_folds_literals_and_refuses_the_rest(self):
        folded = source_const.plant_const_eval(
            ast.parse("[1, (2,), {'a': -3}]").body[0].value,
            StubRefusal,
            "code",
        )
        self.assertEqual(folded, [1, (2,), {"a": -3}])
        with self.assertRaises(StubRefusal) as caught:
            source_const.plant_const_eval(
                ast.parse("{**{}}").body[0].value, StubRefusal, "code"
            )
        self.assertEqual(caught.exception.code, "code")
        self.assertIn("dict unpacking", str(caught.exception))
        with self.assertRaises(StubRefusal) as caught:
            source_const.plant_const_eval(
                ast.parse("name").body[0].value, StubRefusal, "code"
            )
        self.assertIn("Name", str(caught.exception))

    def test_unknown_mill_module_is_refused(self):
        with self.assertRaises(ImportError):
            _import_sibling({"__package__": "pipelines.flk"}, "missing")
        with self.assertRaises(ImportError):
            _import_sibling({"__package__": "", "__file__": __file__}, "missing")

    def test_script_mode_imports_the_flat_sibling(self):
        cli_path = Path(__file__).resolve().parents[1] / "pipelines" / "flk" / "cli.py"
        with clean_package_imports(), direct_pipeline_path():
            catalog = _import_sibling(
                {"__package__": "", "__file__": str(cli_path)}, "catalog"
            )
            generate = _import_sibling(
                {"__package__": "", "__file__": str(cli_path)}, "generate"
            )
            contract = _import_sibling({"__package__": "mac"}, "_contract")
        self.assertEqual(catalog.__name__, "flk.catalog")
        self.assertEqual(generate.__name__, "flk.generate")
        self.assertEqual(contract.__name__, "mac._contract")


if __name__ == "__main__":
    unittest.main()
