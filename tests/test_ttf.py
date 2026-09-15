#!/usr/bin/env python3
"""The cleaned ``ttf`` family home under ``pipelines/ttf/``.

Recovered ``ttf*`` generators on ``origin/codex/recover-grok-01a06111`` were
AST-extracted into ``plants.jsonl``. These tests pin identity, catalog
fidelity, and thalamic shape without publishing a raw round and without
importing a ``*mill*.py`` module.
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
TTF_DIR = REPO / "pipelines" / "ttf"
sys.path.insert(0, str(REPO / "pipelines"))

from mill_signals import mill_prefix  # noqa: E402
from record_kind import classify_kind  # noqa: E402
from ttf import catalog as cat  # noqa: E402
from ttf import cli, generate  # noqa: E402
from ttf._contract import (  # noqa: E402
    CATALOG_ID,
    FACTORY,
    FAMILY_PREFIX,
    FINDING_DESTINATION_EXISTS,
    FINDING_DESTINATION_UNDER_RAW,
    FINDING_ROUND_OUT_OF_DOMAIN,
    FINDING_SLICE_OUT_OF_DOMAIN,
    FINDING_VENDOR_PATH,
    FULL_PLANT_COUNT,
    GENERATOR,
    LEGACY_COMMIT,
    LEGACY_REF,
    QUOTA_PER_ROUND,
    SLICE_IDS,
    SOURCE_CATALOGS,
    SOURCE_COMMIT,
    SOURCE_REF,
    SOURCE_TREE,
    TtfRefusal,
    refuse_vendor_paths,
)

PACKAGE_FILES = (
    "__init__.py",
    "_contract.py",
    "catalog.py",
    "generate.py",
    "cli.py",
)
CATALOG_FILES = ("CATALOG.json", "plants.jsonl")
SNIPPET = """
FACTORY = "thalamic-trajectory-factory"
REC_011 = {
    "id": "ttf-r02c-011",
    "title": "Heptox-Rehn HR-HIL / Ampoule A-7",
    "state": {
        "domain": "rhenium-heptoxide-sublimer",
        "sim_or_real": "hil",
        "goal": "Keep Ampoule A-7 vapor <= 12.0 kPa.",
    },
    "proposed_action": {"name": "cruise_n2_sweep"},
    "safety_decision": {
        "decision": "MODIFY",
        "correctness": "correct",
        "rationale": "Vapor 18.4 kPa won by 208 us.",
    },
    "executed_action": {"name": "clamped_n2_sweep"},
    "future_outcome": {"summary": "Process-correct MODIFY held vapor at 11.2 kPa."},
    "reward_components": reward(TICKS, SC, TOT, "Partnered negative. total -0.48 = 0.30."),
}
REC_012 = {
    "id": "ttf-r02c-012",
    "title": "Samaco-Fell SF-3 / Press P-8",
    "state": {"domain": "samarium-cobalt-sinter", "sim_or_real": "designed", "goal": "O2 cap"},
    "proposed_action": {"name": "cruise_h2_binder_burn"},
    "safety_decision": {"decision": "MODIFY", "correctness": "correct", "rationale": "O2 84 ppm"},
    "executed_action": {"name": "clamped_h2_binder_burn"},
    "future_outcome": {"summary": "Correct MODIFY held off-gas O2 at 28 ppm."},
    "reward_components": reward(TICKS, SC, TOT, "Correct MODIFY. total +1.01 = 0.38."),
}
REC_013 = {
    "id": "ttf-r02c-013",
    "title": "Tetrach-Germ TG-2 / Kettle K-9",
    "state": {"domain": "germanium-tetrachloride-rectifier", "sim_or_real": "designed", "goal": "AE"},
    "proposed_action": {"name": "cruise_gecl4_hearts"},
    "safety_decision": {"decision": "REJECT", "correctness": "correct", "rationale": "AE 52 pps"},
    "executed_action": {"name": "hold_for_crack"},
    "future_outcome": {"summary": "Correct REJECT held GeCl4 at 0 kg/h."},
    "reward_components": reward(TICKS, SC, TOT, "Correct REJECT. total +0.80 = 0.12."),
}
REC_014 = {
    "id": "ttf-r02c-014",
    "title": "Tantala-Lith TL-2 sim / Puller X-4",
    "state": {"domain": "lithium-tantalate-czochralski", "sim_or_real": "simulated", "goal": "seed"},
    "proposed_action": {"name": "hold_lto_pull"},
    "safety_decision": {"decision": "ACCEPT", "correctness": "correct", "rationale": "Seed 1488 C"},
    "executed_action": {"name": "hold_lto_pull"},
    "future_outcome": {"summary": "Correct ACCEPT kept the filed 0.22 mm/h pull."},
    "reward_components": reward(TICKS, SC, TOT, "Correct ACCEPT. total +1.08 = 0.42."),
}
REC_015 = {
    "id": "ttf-r02c-015",
    "title": "Oxychlor-Van OV-6 / Reactor R-11",
    "state": {"domain": "vanadium-oxytrichloride-oxychlor", "sim_or_real": "designed", "goal": "Cl2"},
    "proposed_action": {"name": "cruise_vocl3_oxychlor"},
    "safety_decision": {"decision": "REJECT", "correctness": "incorrect", "rationale": "XS-12"},
    "executed_action": {"name": "hold_for_lagged_interlock"},
    "future_outcome": {"summary": "Incorrect REJECT held a legal 0.42 vol% Cl2."},
    "reward_components": reward(TICKS, SC, TOT, "Wrong-reject. total -0.62 = -0.26."),
}
RECORDS = [REC_011, REC_012, REC_013, REC_014, REC_015]
"""


def invoke(argv):
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        code = cli.run(argv)
    return code, out.getvalue(), err.getvalue()


class PackageShape(unittest.TestCase):
    def test_family_home_is_the_five_cleaned_modules(self):
        names = {path.name for path in TTF_DIR.glob("*.py")}
        self.assertEqual(names, set(PACKAGE_FILES))
        self.assertEqual(list(TTF_DIR.glob("*mill*.py")), [])
        self.assertEqual(list(TTF_DIR.glob("*loop*.py")), [])
        self.assertFalse(any("mill" in name or "loop" in name for name in names))

    def test_compact_catalog_files_live_beside_the_modules(self):
        for name in CATALOG_FILES:
            self.assertTrue((TTF_DIR / name).is_file(), name)

    def test_both_import_spellings_are_one_object(self):
        if str(REPO) not in sys.path:
            sys.path.append(str(REPO))
        from pipelines.ttf import catalog as packaged

        self.assertIs(packaged, cat)
        self.assertIs(sys.modules["ttf.catalog"], sys.modules["pipelines.ttf.catalog"])

    def test_vendor_paths_are_refused(self):
        with self.assertRaises(TtfRefusal) as ctx:
            refuse_vendor_paths(["pipelines/ttf/ttf-mill-r02c.py"])
        self.assertEqual(ctx.exception.code, FINDING_VENDOR_PATH)
        with self.assertRaises(TtfRefusal) as ctx:
            refuse_vendor_paths(["pipelines/ttf/ttf-loop-r02c.py"])
        self.assertEqual(ctx.exception.code, FINDING_VENDOR_PATH)


class Contract(unittest.TestCase):
    def test_factory_matches_the_hosted_thalamic_lane(self):
        self.assertEqual(FACTORY, "thalamic-trajectory-factory")
        self.assertEqual(FAMILY_PREFIX, "ttf")
        self.assertEqual(GENERATOR, "grok-4.6")
        self.assertEqual(QUOTA_PER_ROUND, 5)
        self.assertEqual(CATALOG_ID, "ttf-recover-v1")
        self.assertEqual(SLICE_IDS, ("r02", "r02c", "r03", "r04", "r12", "r24", "r72"))
        self.assertEqual(FULL_PLANT_COUNT, 35)
        self.assertEqual(SOURCE_REF, "origin/codex/recover-grok-01a06111")
        self.assertEqual(SOURCE_COMMIT, "e5206e72fa829931162944648e1e180949baaf0b")
        self.assertEqual(LEGACY_REF, "origin/legacy-mill-lane")
        self.assertEqual(LEGACY_COMMIT, "813f93f1969c1c4421e5663492e9663739efa642")

    def test_legacy_mill_lane_has_no_experiments_ttf_mills(self):
        listing = subprocess.check_output(
            ["git", "ls-tree", "-r", "--name-only", LEGACY_COMMIT, "experiments/"],
            text=True,
            cwd=REPO,
        )
        self.assertFalse(any("ttf" in line.lower() for line in listing.splitlines()))


class AstExtract(unittest.TestCase):
    def test_plants_from_source_reads_rec_dicts_without_exec(self):
        plants = cat.plants_from_source(SNIPPET, "snippet")
        self.assertEqual(len(plants), 5)
        self.assertEqual([plant.record_id for plant in plants], [
            "ttf-r02c-011",
            "ttf-r02c-012",
            "ttf-r02c-013",
            "ttf-r02c-014",
            "ttf-r02c-015",
        ])
        self.assertEqual(plants[0].domain, "rhenium-heptoxide-sublimer")
        self.assertEqual(plants[0].decision, "MODIFY")
        self.assertEqual(plants[0].sim_or_real, "hil")
        self.assertEqual(plants[0].reward_total, -0.48)
        self.assertEqual(plants[4].correctness, "incorrect")

    def test_builder_fn_extract_does_not_exec(self):
        source = "\n".join(
            f"def rec_{index:03d}():\n"
            f"    return {{'id': 'ttf-r02-{index:03d}', 'domain': 'warehouse-amr',\n"
            f"             'sim_or_real': 'designed', 'decision': 'MODIFY'}}\n"
            for index in range(1, 6)
        )
        plants = cat.plants_from_source(source, "builders")
        self.assertEqual([plant.record_id for plant in plants], [
            "ttf-r02-001",
            "ttf-r02-002",
            "ttf-r02-003",
            "ttf-r02-004",
            "ttf-r02-005",
        ])
        self.assertEqual(plants[0].domain, "warehouse-amr")
        self.assertEqual(plants[0].decision, "MODIFY")


class CommittedCatalog(unittest.TestCase):
    def test_catalog_is_full_recover_grok_coverage(self):
        loaded = cat.load_catalog()
        report = cat.catalog_check()
        self.assertEqual(loaded.catalog_id, CATALOG_ID)
        self.assertEqual(report["status"], "ok")
        self.assertEqual(report["coverage"], "full")
        self.assertEqual(report["plants"], FULL_PLANT_COUNT)
        self.assertEqual(report["source_catalogs"], len(SOURCE_CATALOGS))
        self.assertEqual(report["slices"], list(SLICE_IDS))
        self.assertEqual(len(loaded.plants), FULL_PLANT_COUNT)

    def test_r02c_slice_matches_the_first_committed_identity(self):
        r02c = cat.plants_for_slice("r02c")
        self.assertEqual(len(r02c), 5)
        self.assertEqual(r02c[0].record_id, "ttf-r02c-011")
        self.assertEqual(r02c[-1].record_id, "ttf-r02c-015")
        self.assertEqual(r02c[0].domain, "rhenium-heptoxide-sublimer")
        self.assertEqual(r02c[4].decision, "REJECT")
        self.assertEqual(r02c[4].correctness, "incorrect")

    def test_round_two_is_ambiguous_without_a_slice(self):
        with self.assertRaises(TtfRefusal) as ctx:
            cat.plants_for_round(2)
        self.assertEqual(ctx.exception.code, FINDING_SLICE_OUT_OF_DOMAIN)

    def test_a_round_outside_the_catalog_is_refused(self):
        with self.assertRaises(TtfRefusal) as ctx:
            cat.plants_for_round(99)
        self.assertEqual(ctx.exception.code, FINDING_ROUND_OUT_OF_DOMAIN)
        with self.assertRaises(TtfRefusal) as ctx:
            cat.plants_for_round(True)  # type: ignore[arg-type]
        self.assertEqual(ctx.exception.code, FINDING_ROUND_OUT_OF_DOMAIN)


class RecoverReplay(unittest.TestCase):
    def test_every_source_catalog_replays_the_committed_rows(self):
        prefix = f"{SOURCE_TREE}/"
        for slice_id, source_file, relpath, sha256, _original in SOURCE_CATALOGS:
            path = f"{SOURCE_COMMIT}:{prefix}{relpath}"
            blob = subprocess.check_output(["git", "show", path], cwd=REPO)
            self.assertEqual(__import__("hashlib").sha256(blob).hexdigest(), sha256)
            extracted = cat.plants_from_source(blob.decode("utf-8"), source_file)
            committed = cat.plants_for_slice(slice_id)
            self.assertEqual(
                [plant.as_mapping() for plant in extracted],
                [plant.as_mapping() for plant in committed],
                slice_id,
            )


class Generate(unittest.TestCase):
    def setUp(self):
        self.root = Path(tempfile.mkdtemp(prefix="ttf-gen-"))
        self.addCleanup(shutil.rmtree, self.root, True)

    def test_record_is_a_thalamic_trajectory(self):
        plant = cat.plants_for_slice("r02c")[0]
        rec = generate.record(plant, slice_id="r02c")
        self.assertEqual(rec["id"], "ttf-r02c-011")
        self.assertEqual(classify_kind(rec), "thalamic")
        self.assertEqual(mill_prefix(rec), "ttf")
        self.assertEqual(rec["meta"]["factory"], FACTORY)
        self.assertEqual(rec["meta"]["round"], "r02c")
        self.assertEqual(rec["safety_decision"]["decision"], "MODIFY")
        self.assertEqual(rec["state"]["sim_or_real"], "hil")
        self.assertEqual(rec["reward_components"]["total"], -0.48)

    def test_r02c_writes_five_records_and_refuses_clobber_or_raw(self):
        out = self.root / "run"
        summary = generate.run(generate.RunRequest("r02c", out))
        self.assertEqual(summary["records"], 5)
        self.assertEqual(summary["ids"], [
            "ttf-r02c-011",
            "ttf-r02c-012",
            "ttf-r02c-013",
            "ttf-r02c-014",
            "ttf-r02c-015",
        ])
        batch = (out / "batch-r02c.jsonl").read_text(encoding="utf-8").splitlines()
        self.assertEqual(len(batch), 5)
        first = json.loads(batch[0])
        self.assertEqual(first["meta"]["factory"], FACTORY)
        self.assertEqual(classify_kind(first), "thalamic")
        notes = (out / "NOTES-r02c.md").read_text(encoding="utf-8")
        self.assertIn("r02c", notes)
        with self.assertRaises(TtfRefusal) as exists:
            generate.run(generate.RunRequest("r02c", out))
        self.assertEqual(exists.exception.code, FINDING_DESTINATION_EXISTS)
        raw = self.root / "outputs" / "raw" / "x"
        with self.assertRaises(TtfRefusal) as under_raw:
            generate.run(generate.RunRequest("r02c", raw))
        self.assertEqual(under_raw.exception.code, FINDING_DESTINATION_UNDER_RAW)
        self.assertFalse(raw.exists())

    def test_an_interrupt_during_the_write_removes_the_destination(self):
        out = self.root / "run"

        def interrupt(*_args, **_kwargs):
            raise KeyboardInterrupt

        with mock.patch.object(generate, "_fsync_destination", interrupt):
            with self.assertRaises(KeyboardInterrupt):
                generate.run(generate.RunRequest("r02c", out))
        self.assertFalse(out.exists())
        summary = generate.run(generate.RunRequest("r02c", out))
        self.assertEqual(summary["records"], 5)

    def test_batch_jsonl_uses_literal_lf_record_boundaries(self):
        out = self.root / "run"
        generate.run(generate.RunRequest("r02c", out))
        payload = (out / "batch-r02c.jsonl").read_bytes()
        self.assertNotIn(b"\r", payload)
        records = payload.split(b"\n")
        self.assertEqual(records[-1], b"")
        self.assertEqual(len(records) - 1, 5)


class Cli(unittest.TestCase):
    def setUp(self):
        self.root = Path(tempfile.mkdtemp(prefix="ttf-cli-"))
        self.addCleanup(shutil.rmtree, self.root, True)

    def test_catalog_lists_plants(self):
        code, out, err = invoke(["catalog"])
        self.assertEqual((code, err), (0, ""))
        self.assertIn(CATALOG_ID, out)
        self.assertIn("ttf-r02c-011", out)
        self.assertIn("ttf-r72-360", out)

    def test_catalog_check_json(self):
        code, out, err = invoke(["catalog-check", "--json"])
        self.assertEqual((code, err), (0, ""))
        payload = json.loads(out)
        self.assertEqual(payload["status"], "ok")
        self.assertEqual(payload["plants"], FULL_PLANT_COUNT)
        self.assertEqual(payload["coverage"], "full")

    def test_generate_stdout_and_a_raw_refusal(self):
        code, out, err = invoke(["generate", "--slice", "r02c"])
        self.assertEqual((code, err), (0, ""))
        lines = [line for line in out.splitlines() if line]
        self.assertEqual(len(lines), 5)
        self.assertEqual(json.loads(lines[0])["id"], "ttf-r02c-011")
        dest = self.root / "dest"
        code, stdout, err = invoke(
            ["generate", "--slice", "r02c", "--out", str(dest), "--json"]
        )
        self.assertEqual((code, err), (0, ""))
        payload = json.loads(stdout)
        self.assertEqual(payload["status"], "ok")
        self.assertEqual(payload["summary"]["records"], 5)
        code, stdout, _err = invoke(
            [
                "generate",
                "--slice",
                "r02c",
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
