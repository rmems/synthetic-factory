#!/usr/bin/env python3
"""The cleaned ``maos`` family home under ``pipelines/maos/``.

Recovered builders on ``origin/codex/recover-grok-01a06111`` were AST-extracted.
These tests pin identity, catalog fidelity, and replay shape without publishing
a raw round and without importing a ``*mill*.py`` or ``*loop*.py`` module.
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
MAOS_DIR = REPO / "pipelines" / "maos"
sys.path.insert(0, str(REPO / "pipelines"))

from maos import catalog as cat  # noqa: E402
from maos import cli, generate  # noqa: E402
from maos._contract import (  # noqa: E402
    FACTORY,
    FAMILY_PREFIX,
    FINDING_DESTINATION_EXISTS,
    FINDING_DESTINATION_UNDER_RAW,
    FINDING_ROUND_OUT_OF_DOMAIN,
    FINDING_VENDOR_PATH,
    GENERATOR,
    QUOTA_PER_ROUND,
    SOURCE_COMMIT,
    SOURCE_REF,
    MaosRefusal,
    refuse_vendor_paths,
)
from mill_signals import mill_prefix  # noqa: E402

PACKAGE_FILES = (
    "__init__.py",
    "_contract.py",
    "catalog.py",
    "generate.py",
    "cli.py",
)
SNIPPET = """
GEN_AT = "2026-09-02T08:10:56Z"
RIGHTS = {"intended_use": "research_only", "project_training_policy": "blocked"}

def build_record():
    spike_events = [{"channel": "torr.pirani", "t_rel_ms": 1.22}]
    raster = {"spikes": 41, "window_ms": 36}
    rec = {
        "id": "maos-r14-001",
        "title": "LYOSHIELD LYO-4",
        "rights": RIGHTS,
        "state": {
            "sim_or_real": "designed",
            "domain": "pharmaceutical-lyophilization",
            "scenario_name": "LYOSHIELD / Helixmere Biologics LYO-4",
        },
        "safety_decision": {"decision": "MODIFY", "correctness": "correct"},
        "spike_events": spike_events,
        "raster": raster,
        "meta": {
            "round": 14,
            "factory": "multi-agent-ouroboros-swarm",
            "generator": "grok-4.6",
            "run_label": "2026-09-02-final-heavy",
            "domain": "pharmaceutical-lyophilization",
        },
    }
    return rec
"""


def invoke(argv):
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        code = cli.run(argv)
    return code, out.getvalue(), err.getvalue()


class PackageShape(unittest.TestCase):
    def test_family_home_is_the_five_cleaned_modules(self):
        names = {path.name for path in MAOS_DIR.glob("*.py")}
        self.assertEqual(names, set(PACKAGE_FILES))
        self.assertEqual(list(MAOS_DIR.glob("*mill*.py")), [])
        self.assertEqual(list(MAOS_DIR.glob("*loop*.py")), [])
        self.assertFalse(any("mill" in name or "loop" in name for name in names))

    def test_both_import_spellings_are_one_object(self):
        if str(REPO) not in sys.path:
            sys.path.append(str(REPO))
        from pipelines.maos import catalog as packaged

        self.assertIs(packaged, cat)
        self.assertIs(sys.modules["maos.catalog"], sys.modules["pipelines.maos.catalog"])

    def test_vendor_paths_are_refused(self):
        with self.assertRaises(MaosRefusal) as ctx:
            refuse_vendor_paths(["pipelines/maos/maos-mill-r14.py"])
        self.assertEqual(ctx.exception.code, FINDING_VENDOR_PATH)
        with self.assertRaises(MaosRefusal) as loop:
            refuse_vendor_paths(["experiments/maos-loop-g46.py"])
        self.assertEqual(loop.exception.code, FINDING_VENDOR_PATH)


class Contract(unittest.TestCase):
    def test_factory_matches_the_hosted_ouroboros_lane(self):
        self.assertEqual(FACTORY, "multi-agent-ouroboros-swarm")
        self.assertEqual(FAMILY_PREFIX, "maos")
        self.assertEqual(GENERATOR, "grok-4.6")
        self.assertEqual(QUOTA_PER_ROUND, 1)
        self.assertEqual(SOURCE_REF, "origin/codex/recover-grok-01a06111")
        self.assertEqual(SOURCE_COMMIT, "e5206e72fa829931162944648e1e180949baaf0b")


class AstExtract(unittest.TestCase):
    def test_plants_from_source_reads_build_record_rec(self):
        plants = cat.plants_from_source(SNIPPET, "snippet")
        self.assertEqual(len(plants), 1)
        self.assertEqual(plants[0].record_id, "maos-r14-001")
        self.assertEqual(plants[0].scenario, "LYOSHIELD / Helixmere Biologics LYO-4")
        self.assertEqual(plants[0].domain, "pharmaceutical-lyophilization")
        self.assertEqual(plants[0].decision, "MODIFY")
        self.assertEqual(plants[0].spike_events, 1)
        self.assertEqual(plants[0].raster_spikes, 41)
        self.assertEqual(plants[0].generated_at, "2026-09-02T08:10:56Z")

    def test_extract_does_not_exec(self):
        source = (
            "raise RuntimeError('executed')\n"
            "def build_record():\n"
            "    rec = {\n"
            "        'id': 'maos-r14-001',\n"
            "        'title': 'x',\n"
            "        'state': {'sim_or_real': 'designed', 'domain': 'd',\n"
            "                  'scenario_name': 's'},\n"
            "        'safety_decision': {'decision': 'MODIFY', 'correctness': 'correct'},\n"
            "        'spike_events': [],\n"
            "        'raster': {'spikes': 0},\n"
            "        'meta': {'round': 14,\n"
            "                 'factory': 'multi-agent-ouroboros-swarm',\n"
            "                 'generator': 'grok-4.6', 'run_label': 'lab'},\n"
            "    }\n"
        )
        plants = cat.plants_from_source(source, "raises")
        self.assertEqual(plants[0].record_id, "maos-r14-001")
        self.assertEqual(plants[0].decision, "MODIFY")


class RecoverGitShow(unittest.TestCase):
    R19_BLOB = (
        "recovery/grok-session-01a06111-1b84-7250-aec4-9d120db6c1a4/"
        "recovered_sources/by-original-path/maos-r19--17818e5dd11c/versions/v0005/build_r19.py"
    )
    R23_BLOB = (
        "recovery/grok-session-01a06111-1b84-7250-aec4-9d120db6c1a4/"
        "recovered_sources/by-original-path/maos-r23--80d63e849dce/versions/v0001/build_r23.py"
    )

    def test_rank2_r19_matches_the_committed_row(self):
        try:
            text = subprocess.check_output(
                ["git", "show", f"e5206e72:{self.R19_BLOB}"],
                cwd=REPO,
                text=True,
            )
        except subprocess.CalledProcessError:
            self.skipTest("recover-grok maos-r19 builder is not fetched")
        plants = cat.plants_from_source(text, "build_r19.py")
        self.assertEqual(plants[0].record_id, "maos-r19-001")
        self.assertEqual(plants[0].source_round, 19)
        self.assertTrue(plants[0].scenario.startswith("CASSITER"))

    def test_rank3_r23_matches_the_committed_row(self):
        try:
            text = subprocess.check_output(
                ["git", "show", f"e5206e72:{self.R23_BLOB}"],
                cwd=REPO,
                text=True,
            )
        except subprocess.CalledProcessError:
            self.skipTest("recover-grok maos-r23 builder is not fetched")
        plants = cat.plants_from_source(text, "build_r23.py")
        self.assertEqual(plants[0].record_id, "maos-r23-001")
        self.assertEqual(plants[0].source_round, 23)
        self.assertTrue(plants[0].scenario.startswith("STRIAFOIL"))


class CommittedCatalog(unittest.TestCase):
    def test_pinned_catalog_covers_all_twenty_seven_exact_rounds(self):
        loaded = cat.load_catalog()
        report = cat.catalog_check()
        expected_rounds = [
            14,
            15,
            16,
            19,
            20,
            21,
            23,
            24,
            25,
            29,
            30,
            31,
            32,
            33,
            34,
            35,
            36,
            39,
            41,
            42,
            43,
            46,
            47,
            48,
            51,
            52,
            67,
        ]
        self.assertEqual(loaded.catalog_id, "maos-recover-v1")
        self.assertEqual(report["status"], "ok")
        self.assertEqual(report["plants"], 27)
        self.assertEqual(report["rounds"], expected_rounds)
        self.assertEqual(report["first_round"], 14)
        self.assertEqual(loaded.plants[0].record_id, "maos-r14-001")
        self.assertEqual(cat.plants_for_round(15)[0].record_id, "maos-r15-001")
        self.assertTrue(cat.plants_for_round(16)[0].scenario.startswith("QUILLFORGE"))
        self.assertEqual(cat.plants_for_round(19)[0].record_id, "maos-r19-001")
        self.assertTrue(cat.plants_for_round(21)[0].scenario.startswith("REDHALL"))
        self.assertEqual(cat.plants_for_round(23)[0].record_id, "maos-r23-001")
        self.assertTrue(cat.plants_for_round(67)[0].scenario.startswith("FEN-SPIT"))

    def test_a_round_outside_the_pinned_catalog_is_refused(self):
        with self.assertRaises(MaosRefusal) as ctx:
            cat.plants_for_round(3)
        self.assertEqual(ctx.exception.code, FINDING_ROUND_OUT_OF_DOMAIN)
        with self.assertRaises(MaosRefusal) as ctx:
            cat.plants_for_round(True)  # type: ignore[arg-type]
        self.assertEqual(ctx.exception.code, FINDING_ROUND_OUT_OF_DOMAIN)


class Generate(unittest.TestCase):
    def setUp(self):
        self.root = Path(tempfile.mkdtemp(prefix="maos-gen-"))
        self.addCleanup(shutil.rmtree, self.root, True)

    def test_record_is_a_compact_catalog_replay(self):
        plant = cat.plants_for_round(14)[0]
        rec = generate.record(plant)
        self.assertEqual(rec["id"], "maos-r14-001")
        self.assertEqual(mill_prefix(rec), "maos")
        self.assertEqual(rec["meta"]["factory"], FACTORY)
        self.assertEqual(rec["meta"]["kind"], "catalog_replay")
        self.assertEqual(rec["state"]["scenario_name"], plant.scenario)
        self.assertNotIn("thought", rec)
        self.assertNotIn("spike_events", rec)

    def test_round_14_writes_one_record_and_refuses_clobber_or_raw(self):
        out = self.root / "run"
        summary = generate.run(generate.RunRequest(14, out))
        self.assertEqual(summary["records"], 1)
        self.assertEqual(summary["ids"], ["maos-r14-001"])
        batch = (out / "batch-r14.jsonl").read_text(encoding="utf-8").splitlines()
        self.assertEqual(len(batch), 1)
        first = json.loads(batch[0])
        self.assertEqual(first["meta"]["factory"], FACTORY)
        notes = (out / "NOTES-r14.md").read_text(encoding="utf-8")
        self.assertIn("research_only", notes)
        with self.assertRaises(MaosRefusal) as exists:
            generate.run(generate.RunRequest(14, out))
        self.assertEqual(exists.exception.code, FINDING_DESTINATION_EXISTS)
        raw = self.root / "outputs" / "raw" / "x"
        with self.assertRaises(MaosRefusal) as under_raw:
            generate.run(generate.RunRequest(14, raw))
        self.assertEqual(under_raw.exception.code, FINDING_DESTINATION_UNDER_RAW)
        self.assertFalse(raw.exists())

    def test_an_interrupt_during_the_write_removes_the_destination(self):
        out = self.root / "run"

        def interrupt(*_args, **_kwargs):
            raise KeyboardInterrupt

        with mock.patch.object(generate, "_fsync_destination", interrupt):
            with self.assertRaises(KeyboardInterrupt):
                generate.run(generate.RunRequest(14, out))
        self.assertFalse(out.exists())
        summary = generate.run(generate.RunRequest(14, out))
        self.assertEqual(summary["records"], 1)

    def test_batch_jsonl_uses_literal_lf_record_boundaries(self):
        out = self.root / "run"
        generate.run(generate.RunRequest(14, out))
        payload = (out / "batch-r14.jsonl").read_bytes()
        self.assertNotIn(b"\r", payload)
        records = payload.split(b"\n")
        self.assertEqual(records[-1], b"")
        self.assertEqual(len(records) - 1, 1)


class Cli(unittest.TestCase):
    def setUp(self):
        self.root = Path(tempfile.mkdtemp(prefix="maos-cli-"))
        self.addCleanup(shutil.rmtree, self.root, True)

    def test_catalog_lists_plants(self):
        code, out, err = invoke(["catalog"])
        self.assertEqual((code, err), (0, ""))
        self.assertIn("maos-recover-v1", out)
        self.assertIn("maos-r14-001", out)

    def test_catalog_check_json(self):
        code, out, err = invoke(["catalog-check", "--json"])
        self.assertEqual((code, err), (0, ""))
        payload = json.loads(out)
        self.assertEqual(payload["status"], "ok")
        self.assertEqual(payload["plants"], 27)

    def test_generate_stdout_and_a_raw_refusal(self):
        code, out, err = invoke(["generate", "--round", "14"])
        self.assertEqual((code, err), (0, ""))
        lines = [line for line in out.splitlines() if line]
        self.assertEqual(len(lines), 1)
        self.assertEqual(json.loads(lines[0])["id"], "maos-r14-001")
        dest = self.root / "dest"
        code, stdout, err = invoke(
            ["generate", "--round", "14", "--out", str(dest), "--json"]
        )
        self.assertEqual((code, err), (0, ""))
        payload = json.loads(stdout)
        self.assertEqual(payload["status"], "ok")
        self.assertEqual(payload["summary"]["records"], 1)
        code, stdout, _err = invoke(
            [
                "generate",
                "--round",
                "14",
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
