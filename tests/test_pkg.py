#!/usr/bin/env python3
"""The cleaned ``pkg`` family home under ``pipelines/pkg/``.

Eleven in-scope ``experiments/pkg-mill-r*.py`` mills on
``origin/legacy-mill-lane`` (through ``pkg-mill-r316.py``) were
AST-extracted into compact ``pipelines/pkg/plants.jsonl``. These tests pin
identity, catalog fidelity, and episode shape without publishing a raw
round and without importing a mill or loop module. Demoted digest/lock-yank
twins, attest-wave, leftover3, licrep, and pkgs mills stay out.
"""

from __future__ import annotations

import contextlib
import io
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

REPO = Path(__file__).resolve().parents[1]
PKG_DIR = REPO / "pipelines" / "pkg"
sys.path.insert(0, str(REPO / "pipelines"))

from mill_reviewed_vocabulary import REVIEWED_MILL_PREFIX_HOMES  # noqa: E402
from mill_signals import mill_prefix  # noqa: E402
from pkg import catalog as cat  # noqa: E402
from pkg import cli, generate  # noqa: E402
from pkg._contract import (  # noqa: E402
    CATALOG_ID,
    FACTORY,
    FAMILY_PREFIX,
    FINDING_DESTINATION_EXISTS,
    FINDING_DESTINATION_UNDER_RAW,
    FINDING_ROUND_OUT_OF_DOMAIN,
    FINDING_VENDOR_PATH,
    GENERATOR,
    PLANTS_FILENAME,
    QUOTA_PER_ROUND,
    SOURCE_COMMIT,
    SOURCE_MILLS,
    SOURCE_PATH,
    SOURCE_REF,
    PkgRefusal,
    refuse_vendor_paths,
)
from record_kind import classify_kind  # noqa: E402

PACKAGE_FILES = (
    "__init__.py",
    "_contract.py",
    "catalog.py",
    "generate.py",
    "cli.py",
)
SNIPPET = """
CATALOG_FIRST = 163
FACTORY = "package-release-factory"

def _pairs():
    return [
        (
            "cosign_reusable",
            {
                "slug": "cosign-reusable-workflow-san",
                "plant": "lawsonite-ctl",
                "seed": "calling-repo identity = reusable SAN",
                "first": "verify calling-repo release.yml",
                "change": "reusable acme-infra/oidc-release@v3",
                "term": "success; :latest 1.7.9 unsigned",
                "leftover": ":latest still 1.7.9 unsigned",
                "digest": hx("lawsonite-img", 64),
            },
            "fail_leftover",
            {
                "slug": "npm-oidc-id-token-missing",
                "plant": "pumpellyite-js",
                "seed": "id-token missing so provenance omitted",
                "first": "unpublish 2.4.0 + republish --provenance",
                "change": "2.4.1 + id-token: write",
                "term": "fail: latest still 2.4.0 attest=null",
                "goal": "Publish 2.4.1 with OIDC provenance.",
                "plan": "Do not unpublish 2.4.0.",
            },
        ),
    ]
"""


def invoke(argv):
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        code = cli.run(argv)
    return code, out.getvalue(), err.getvalue()


class PackageShape(unittest.TestCase):
    def test_family_home_is_the_five_cleaned_modules(self):
        names = {path.name for path in PKG_DIR.glob("*.py")}
        self.assertEqual(names, set(PACKAGE_FILES))
        self.assertEqual(list(PKG_DIR.glob("*mill*.py")), [])
        self.assertEqual(list(PKG_DIR.glob("*loop*.py")), [])
        self.assertFalse(any("mill" in name or "loop" in name for name in names))

    def test_both_import_spellings_are_one_object(self):
        if str(REPO) not in sys.path:
            sys.path.append(str(REPO))
        from pipelines.pkg import catalog as packaged

        self.assertIs(packaged, cat)
        self.assertIs(sys.modules["pkg.catalog"], sys.modules["pipelines.pkg.catalog"])

    def test_vendor_paths_are_refused(self):
        for name in (
            "pkg-mill-r163.py",
            "pkg-loop-r163.py",
            "pkgs-mill-r098.py",
        ):
            with self.assertRaises(PkgRefusal) as ctx:
                refuse_vendor_paths([f"pipelines/pkg/{name}"])
            self.assertEqual(ctx.exception.code, FINDING_VENDOR_PATH)


class Contract(unittest.TestCase):
    def test_factory_matches_the_reviewed_pkg_home(self):
        self.assertEqual(FACTORY, "package-release-factory")
        self.assertEqual(FAMILY_PREFIX, "pkg")
        self.assertEqual(GENERATOR, "grok-4.6")
        self.assertEqual(QUOTA_PER_ROUND, 2)
        self.assertEqual(CATALOG_ID, "pkg-r163-r331-v1")
        self.assertEqual(SOURCE_REF, "origin/legacy-mill-lane")
        self.assertEqual(SOURCE_COMMIT, "813f93f1969c1c4421e5663492e9663739efa642")
        self.assertEqual(SOURCE_PATH, "experiments/pkg-mill-r163.py")
        self.assertEqual(len(SOURCE_MILLS), 11)
        self.assertEqual(SOURCE_MILLS[0], ("experiments/pkg-mill-r163.py", "pkg-mill-r163.py", 163, 180))
        self.assertEqual(SOURCE_MILLS[-1], ("experiments/pkg-mill-r316.py", "pkg-mill-r316.py", 316, 331))
        self.assertEqual(REVIEWED_MILL_PREFIX_HOMES[FAMILY_PREFIX], FACTORY)


class AstExtract(unittest.TestCase):
    def test_plants_from_source_reads_four_tuples_and_skips_hx(self):
        plants = cat.plants_from_source(SNIPPET, "snippet")
        self.assertEqual(len(plants), 2)
        self.assertEqual(
            [plant.record_id for plant in plants],
            [
                "pkg-r163-cosign-reusable-workflow-san",
                "pkg-r163-npm-oidc-id-token-missing",
            ],
        )
        self.assertEqual(plants[0].kind, "cosign_reusable")
        self.assertEqual(plants[0].leftover, ":latest still 1.7.9 unsigned")
        self.assertEqual(plants[1].role, "fail")
        self.assertEqual(plants[1].goal, "Publish 2.4.1 with OIDC provenance.")

    def test_legacy_sources_reextract_when_the_archive_is_fetched(self):
        try:
            subprocess.check_output(
                ["git", "rev-parse", SOURCE_REF],
                cwd=REPO,
                stderr=subprocess.DEVNULL,
            )
        except (subprocess.CalledProcessError, FileNotFoundError):
            self.skipTest("origin/legacy-mill-lane is not fetched")
        committed = cat.load_catalog().plants
        for path, source_name, first_round, last_round in SOURCE_MILLS:
            text = subprocess.check_output(
                ["git", "show", f"{SOURCE_COMMIT}:{path}"],
                cwd=REPO,
                text=True,
            )
            extracted = cat.plants_from_source(text, source_name)
            slice_plants = tuple(
                plant for plant in committed if plant.source_name == source_name
            )
            self.assertEqual(len(extracted), len(slice_plants))
            self.assertEqual(
                [(plant.record_id, plant.slug, plant.kind, plant.role) for plant in extracted],
                [
                    (plant.record_id, plant.slug, plant.kind, plant.role)
                    for plant in slice_plants
                ],
            )
            rounds = {plant.source_round for plant in extracted}
            self.assertEqual(min(rounds), first_round)
            self.assertEqual(max(rounds), last_round)


class CommittedCatalog(unittest.TestCase):
    def test_compact_jsonl_pins_the_committed_plants(self):
        catalog_dir = PKG_DIR
        self.assertTrue((catalog_dir / PLANTS_FILENAME).is_file())
        loaded = cat.load_catalog()
        self.assertEqual(len(loaded.plants), 256)

    def test_catalog_is_a_two_stride_through_r331(self):
        loaded = cat.load_catalog()
        report = cat.catalog_check()
        self.assertEqual(loaded.catalog_id, "pkg-r163-r331-v1")
        self.assertEqual(report["status"], "ok")
        self.assertEqual(report["plants"], 256)
        self.assertEqual(report["pairs"], 128)
        self.assertEqual(report["first_round"], 163)
        self.assertEqual(report["last_round"], 331)
        wave = cat.WAVE_ROUNDS
        self.assertEqual(wave[0], 163)
        self.assertEqual(wave[-1], 331)
        self.assertNotIn(200, wave)
        pair = cat.plants_for_round(163)
        self.assertEqual(len(pair), 2)
        self.assertEqual(pair[0].record_id, "pkg-r163-cosign-reusable-workflow-san")
        self.assertEqual(pair[1].record_id, "pkg-r163-npm-oidc-id-token-missing")
        slugs = [plant.slug for plant in loaded.plants]
        self.assertEqual(len(set(slugs)), 256)
        blob = " ".join(slugs)
        self.assertNotIn("digest-vs-git", blob)
        self.assertNotIn("lock-yank", blob)

    def test_a_round_outside_the_committed_catalog_is_refused(self):
        with self.assertRaises(PkgRefusal) as ctx:
            cat.plants_for_round(98)
        self.assertEqual(ctx.exception.code, FINDING_ROUND_OUT_OF_DOMAIN)
        pair = cat.plants_for_round(209)
        self.assertEqual(len(pair), 2)
        with self.assertRaises(PkgRefusal) as ctx:
            cat.plants_for_round(200)
        self.assertEqual(ctx.exception.code, FINDING_ROUND_OUT_OF_DOMAIN)
        with self.assertRaises(PkgRefusal) as ctx:
            cat.plants_for_round(True)  # type: ignore[arg-type]
        self.assertEqual(ctx.exception.code, FINDING_ROUND_OUT_OF_DOMAIN)


class Generate(unittest.TestCase):
    def setUp(self):
        self.root = Path(tempfile.mkdtemp(prefix="pkg-gen-"))
        self.addCleanup(shutil.rmtree, self.root, True)

    def test_episode_is_a_designed_pkg_record(self):
        plant = cat.plants_for_round(163)[0]
        rec = generate.episode(plant)
        self.assertEqual(rec["id"], "pkg-r163-cosign-reusable-workflow-san")
        self.assertEqual(classify_kind(rec), "episode")
        self.assertEqual(mill_prefix(rec), "pkg")
        self.assertEqual(rec["meta"]["factory"], FACTORY)
        self.assertEqual(rec["reward"]["success"], True)
        self.assertEqual(len(rec["steps"]), 12)
        self.assertTrue(rec["goal"])
        self.assertNotIn("thought", json.dumps(rec))

    def test_round_163_writes_two_records_and_refuses_clobber_or_raw(self):
        out = self.root / "run"
        summary = generate.run(generate.RunRequest(163, out))
        self.assertEqual(summary["records"], 2)
        self.assertEqual(
            summary["ids"],
            [
                "pkg-r163-cosign-reusable-workflow-san",
                "pkg-r163-npm-oidc-id-token-missing",
            ],
        )
        batch = (out / "batch-r163.jsonl").read_text(encoding="utf-8").splitlines()
        self.assertEqual(len(batch), 2)
        first = json.loads(batch[0])
        second = json.loads(batch[1])
        self.assertEqual(classify_kind(first), "episode")
        self.assertEqual(first["reward"]["success"], True)
        self.assertEqual(second["reward"]["success"], False)
        notes = (out / "NOTES-r163.md").read_text(encoding="utf-8")
        self.assertIn("demoted", notes)
        with self.assertRaises(PkgRefusal) as exists:
            generate.run(generate.RunRequest(163, out))
        self.assertEqual(exists.exception.code, FINDING_DESTINATION_EXISTS)
        raw = self.root / "outputs" / "raw" / "x"
        with self.assertRaises(PkgRefusal) as under_raw:
            generate.run(generate.RunRequest(163, raw))
        self.assertEqual(under_raw.exception.code, FINDING_DESTINATION_UNDER_RAW)
        self.assertFalse(raw.exists())

    def test_an_interrupt_during_the_write_removes_the_destination(self):
        out = self.root / "run"

        def interrupt(*_args, **_kwargs):
            raise KeyboardInterrupt

        with mock.patch.object(generate, "_fsync_destination", interrupt):
            with self.assertRaises(KeyboardInterrupt):
                generate.run(generate.RunRequest(163, out))
        self.assertFalse(out.exists())
        summary = generate.run(generate.RunRequest(163, out))
        self.assertEqual(summary["records"], 2)

    def test_batch_jsonl_uses_literal_lf_record_boundaries(self):
        out = self.root / "run"
        generate.run(generate.RunRequest(163, out))
        payload = (out / "batch-r163.jsonl").read_bytes()
        self.assertNotIn(b"\r", payload)
        records = payload.split(b"\n")
        self.assertEqual(records[-1], b"")
        self.assertEqual(len(records) - 1, 2)


class Cli(unittest.TestCase):
    def setUp(self):
        self.root = Path(tempfile.mkdtemp(prefix="pkg-cli-"))
        self.addCleanup(shutil.rmtree, self.root, True)

    def test_catalog_lists_plants(self):
        code, out, err = invoke(["catalog"])
        self.assertEqual((code, err), (0, ""))
        self.assertIn("pkg-r163-r331-v1", out)
        self.assertIn("pkg-r163-cosign-reusable-workflow-san", out)

    def test_catalog_check_json(self):
        code, out, err = invoke(["catalog-check", "--json"])
        self.assertEqual((code, err), (0, ""))
        payload = json.loads(out)
        self.assertEqual(payload["status"], "ok")
        self.assertEqual(payload["plants"], 256)
        self.assertEqual(payload["pairs"], 128)

    def test_generate_stdout_and_a_raw_refusal(self):
        code, out, err = invoke(["generate", "--round", "163"])
        self.assertEqual((code, err), (0, ""))
        lines = [line for line in out.splitlines() if line]
        self.assertEqual(len(lines), 2)
        self.assertEqual(json.loads(lines[0])["id"], "pkg-r163-cosign-reusable-workflow-san")
        dest = self.root / "dest"
        code, stdout, err = invoke(
            ["generate", "--round", "163", "--out", str(dest), "--json"]
        )
        self.assertEqual((code, err), (0, ""))
        payload = json.loads(stdout)
        self.assertEqual(payload["status"], "ok")
        self.assertEqual(payload["summary"]["records"], 2)
        code, stdout, _err = invoke(
            [
                "generate",
                "--round",
                "163",
                "--out",
                str(self.root / "outputs" / "raw" / "x"),
                "--json",
            ]
        )
        self.assertEqual(code, 2)
        refused = json.loads(stdout)
        self.assertEqual(refused["status"], "refused")
        self.assertEqual(refused["code"], FINDING_DESTINATION_UNDER_RAW)


if __name__ == "__main__":
    unittest.main()
