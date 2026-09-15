#!/usr/bin/env python3
"""Leftover leftover leftover leftover leftover leftover L6 mill catalog."""

from __future__ import annotations

import ast
import contextlib
import io
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
PIPELINES = REPO / "pipelines"
sys.path.insert(0, str(PIPELINES))

from lll import catalog as cat  # noqa: E402
from lll import cli, generate  # noqa: E402
from lll._contract import (  # noqa: E402
    CATALOG_ID,
    FACTORY,
    FAMILY_PREFIX,
    FINDING_AST_NOT_A_PLANT,
    FINDING_FIELD_MISSING,
    FINDING_VENDOR_PATH,
    GENERATOR,
    REVIEWED_ID_PREFIX,
    SOURCE_COMMIT,
    SOURCE_FILES,
    LllRefusal,
    is_vendor_filename,
    refuse_vendor_paths,
)
from mill_reviewed_vocabulary import REVIEWED_MILL_PREFIX_HOMES  # noqa: E402

PACKAGE = PIPELINES / "lll"

PAIRS_SNIPPET = """
PAIRS = [
    dict(
        slug="pm-serverid-bind",
        fail="pm-drop-serverid-handoff",
        mod="pmsid",
        drop="pmdsid",
        esp="Postmark",
        idf="MessageID",
        evf="ServerID",
        naive="email",
        doc="https://example.invalid/docs",
        domain="postmark-leftover-msgid-plus-serverid",
        ticket="PM-L6-56",
        test_ok="test_msgid_plus_serverid",
        short="pmsid",
        dshort="pmdsid",
    ),
]
"""

REPLACE_SNIPPET = """
PAIRS = [
    dict(
        slug="loops-contactid-bind",
        fail="loops-drop-contactid-handoff",
        mod="lpcid",
        drop="lpd cid".replace(" ", ""),
        esp="Loops",
        idf="emailId",
        evf="contactId",
        naive="email",
        domain="loops-leftover-emailid-plus-contactid",
        ticket="LP-L6-59",
        short="lpcid",
        dshort="lpdcid",
    ),
]
"""


def invoke(argv):
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        code = cli.run(argv)
    return code, out.getvalue(), err.getvalue()


def _legacy_available() -> bool:
    try:
        subprocess.check_output(
            ["git", "show", f"{SOURCE_COMMIT}:{SOURCE_FILES[0]}"],
            cwd=REPO,
            stderr=subprocess.DEVNULL,
        )
        return True
    except subprocess.CalledProcessError:
        return False


def _module_uses_exec(path: Path) -> list[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    hits: list[str] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call) or not isinstance(node.func, ast.Name):
            continue
        if node.func.id in {"exec", "eval", "compile"}:
            hits.append(f"{path.name}:{node.lineno}:{node.func.id}")
    return hits


class PackageShape(unittest.TestCase):
    def test_the_package_does_not_vendor_leftover_mill_scripts(self):
        names = {path.name for path in PACKAGE.iterdir() if path.suffix in {".py", ".json"}}
        self.assertEqual(
            names,
            {
                "CATALOG.json",
                "__init__.py",
                "_contract.py",
                "catalog.py",
                "cli.py",
                "generate.py",
            },
        )
        self.assertEqual(list(PACKAGE.glob("mill_leftover_leftover_leftover_*.py")), [])
        self.assertEqual(list(PACKAGE.glob("*mill*.py")), [])

    def test_both_import_spellings_are_one_object(self):
        if str(REPO) not in sys.path:
            sys.path.append(str(REPO))
        from pipelines.lll import catalog as packaged

        self.assertIs(packaged, cat)
        self.assertIs(sys.modules["lll.catalog"], sys.modules["pipelines.lll.catalog"])

    def test_reviewed_ewr_prefix_maps_to_this_factory(self):
        self.assertEqual(FAMILY_PREFIX, "leftover")
        self.assertNotIn(FAMILY_PREFIX, REVIEWED_MILL_PREFIX_HOMES)
        self.assertEqual(REVIEWED_ID_PREFIX, "ewr")
        self.assertEqual(REVIEWED_MILL_PREFIX_HOMES["ewr"], FACTORY)
        self.assertEqual(FACTORY, "email-webhook-retry-factory")
        self.assertEqual(GENERATOR, "grok-4.6")

    def test_refuse_vendor_paths(self):
        self.assertTrue(is_vendor_filename("mill_leftover_leftover_leftover_r56.py"))
        self.assertTrue(is_vendor_filename("mill_leftover_leftover_leftover_r91.py"))
        self.assertFalse(is_vendor_filename("generate.py"))
        self.assertFalse(is_vendor_filename("catalog.py"))
        with self.assertRaises(LllRefusal) as ctx:
            refuse_vendor_paths([Path("experiments/mill_leftover_leftover_leftover_r56.py")])
        self.assertEqual(ctx.exception.code, FINDING_VENDOR_PATH)

    def test_extractor_modules_never_exec(self):
        hits = []
        for name in ("_contract.py", "catalog.py", "generate.py", "cli.py", "__init__.py"):
            hits.extend(_module_uses_exec(PACKAGE / name))
        self.assertEqual(hits, [])


class AstExtract(unittest.TestCase):
    def test_plants_from_source_reads_pairs_dicts(self):
        plants = generate.plants_from_source(PAIRS_SNIPPET)
        self.assertEqual(len(plants), 1)
        self.assertEqual(plants[0]["slug"], "pm-serverid-bind")
        self.assertEqual(plants[0]["fail"], "pm-drop-serverid-handoff")
        self.assertEqual(plants[0]["ticket"], "PM-L6-56")
        self.assertNotIn("doc", plants[0])
        self.assertNotIn("test_ok", plants[0])

    def test_plants_from_source_evals_constant_replace(self):
        plants = generate.plants_from_source(REPLACE_SNIPPET)
        self.assertEqual(plants[0]["drop"], "lpdcid")
        self.assertEqual(plants[0]["slug"], "loops-contactid-bind")

    def test_a_pair_without_slug_is_refused(self):
        with self.assertRaises(LllRefusal) as ctx:
            generate.plants_from_source(
                "PAIRS = [dict(fail='x', mod='m', drop='d', esp='E', "
                "idf='i', evf='v', naive='n', domain='dom', ticket='T', "
                "short='s', dshort='ds')]\n"
            )
        self.assertEqual(ctx.exception.code, FINDING_FIELD_MISSING)

    def test_a_module_without_pairs_is_refused(self):
        with self.assertRaises(LllRefusal) as ctx:
            generate.plants_from_source("FAC = 'email-webhook-retry-factory'\n")
        self.assertEqual(ctx.exception.code, FINDING_AST_NOT_A_PLANT)


class CommittedCatalog(unittest.TestCase):
    def test_full_extract_and_source_pins(self):
        loaded = cat.load_catalog()
        report = cat.catalog_check()
        self.assertEqual(loaded.catalog_id, CATALOG_ID)
        self.assertEqual(loaded.factory, FACTORY)
        self.assertEqual(len(loaded.plants), 64)
        self.assertEqual(len(loaded.sources), 4)
        self.assertEqual(report["status"], "ok")
        self.assertEqual(report["plants"], 64)
        self.assertEqual(report["full_row_count"], 64)
        self.assertEqual(report["catalog_files"], 4)
        self.assertEqual(report["first_round"], 56)
        self.assertFalse(report["exec"])
        self.assertEqual(loaded.plants[0].slug, "pm-serverid-bind")
        self.assertEqual(loaded.plants[0].ticket, "PM-L6-56")
        self.assertEqual(loaded.plants[16].slug, "loops-contactid-bind")
        self.assertEqual(loaded.plants[16].drop, "lpdcid")
        self.assertEqual(loaded.plants[32].slug, "loops-mailingid-bind")
        self.assertEqual(loaded.plants[48].slug, "sg-asm-group-bind")
        self.assertEqual(loaded.sources[0].first_slug, "pm-serverid-bind")
        self.assertEqual(loaded.sources[1].n_rows, 16)

    def test_legacy_mills_reextract_the_committed_identities(self):
        if not _legacy_available():
            self.skipTest("legacy-mill-lane leftover L6 mills are not in this environment")
        committed = cat.load_catalog().plants
        offset = 0
        for path in SOURCE_FILES:
            text = subprocess.check_output(
                ["git", "show", f"{SOURCE_COMMIT}:{path}"],
                cwd=REPO,
                text=True,
            )
            extracted = generate.plants_from_source(text)
            slice_ = committed[offset:offset + 16]
            self.assertEqual(len(extracted), 16)
            self.assertEqual(
                [(row["slug"], row["ticket"], row["drop"]) for row in extracted],
                [(plant.slug, plant.ticket, plant.drop) for plant in slice_],
            )
            offset += 16
        self.assertEqual(offset, 64)


class Cli(unittest.TestCase):
    def test_catalog_check_json_reports_the_full_extract(self):
        code, out, err = invoke(["catalog-check", "--json"])
        self.assertEqual((code, err), (0, ""))
        payload = json.loads(out)
        self.assertEqual(payload["status"], "ok")
        self.assertEqual(payload["plants"], 64)
        self.assertEqual(payload["full_row_count"], 64)
        self.assertFalse(payload["exec"])

    def test_extract_json_from_a_pairs_snippet(self):
        handle = tempfile.NamedTemporaryFile(
            "w", encoding="utf-8", suffix="-lll-snippet.py", delete=False
        )
        handle.write(PAIRS_SNIPPET)
        handle.close()
        snippet = Path(handle.name)
        self.addCleanup(snippet.unlink)
        code, out, err = invoke(["extract", "--source", str(snippet), "--json"])
        self.assertEqual((code, err), (0, ""))
        payload = json.loads(out)
        self.assertEqual(payload["status"], "ok")
        self.assertEqual(payload["plants"][0]["slug"], "pm-serverid-bind")
        self.assertNotIn("doc", payload["plants"][0])


if __name__ == "__main__":
    unittest.main()
