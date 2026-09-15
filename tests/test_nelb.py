#!/usr/bin/env python3
"""The cleaned ``nelb`` family home under ``pipelines/nelb/``.

Recovered Session-A builders on ``origin/codex/recover-grok-01a06111`` were
AST-extracted into compact JSONL. These tests pin identity, catalog fidelity,
and bridge-pair shape without publishing a raw round and without importing a
``*mill*.py`` or ``gen_r*.py`` module.
"""

from __future__ import annotations

import contextlib
import io
import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

REPO = Path(__file__).resolve().parents[1]
NELB_DIR = REPO / "pipelines" / "nelb"
sys.path.insert(0, str(REPO / "pipelines"))

from mill_signals import mill_prefix  # noqa: E402
from nelb import catalog as cat  # noqa: E402
from nelb import cli, generate  # noqa: E402
from nelb._contract import (  # noqa: E402
    CATALOG_FILENAME,
    FACTORY,
    FAMILY_PREFIX,
    FINDING_DESTINATION_EXISTS,
    FINDING_DESTINATION_UNDER_RAW,
    FINDING_ROUND_OUT_OF_DOMAIN,
    FINDING_VENDOR_PATH,
    GENERATOR,
    ISOLATION,
    LEGACY_COMMIT,
    LEGACY_REF,
    PLANTS_FILENAME,
    QUOTA_PER_ROUND,
    SOURCE_COMMIT,
    SOURCE_REF,
    NelbRefusal,
    refuse_vendor_paths,
    sha256_bytes,
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
FACTORY = "neuromorphic-event-language-bridge"
ROUND = 1
MUST_NOT_RUN = undefined_name

def rec_001():
    traj = {
        "id": "nelb-r01-001-t1",
        "state": {
            "sim_or_real": "designed",
            "domain": "johnson_noise_spent_fuel_pool_t",
            "setting": "Brackfen Pool BF-3 (invented), Reedspire Fuel Yard, bay B-7.",
        },
        "safety_decision": {"decision": "REJECT", "rationale": "continue-recirc refused"},
    }
    traj2 = {
        "id": "nelb-r01-001-t2",
        "safety_decision": {"decision": "MODIFY", "rationale": "recirc-hold"},
    }
    return {
        "id": "nelb-r01-001",
        "language_view": {
            "description": "Johnson-noise remaining-temperature family",
            "trajectory": traj,
            "trajectory_recirc_hold": traj2,
        },
        "reconstruction_model": {
            "name": "johnson_noise_pool_temperature",
            "formula": "T_K = k_j * V_rms_uV^2",
        },
        "bridge_notes": {"why_high_value": "Johnson-noise remaining-temperature family"},
    }

def rec_002():
    traj = {
        "id": "nelb-r01-002-t1",
        "state": {
            "sim_or_real": "hil",
            "domain": "coulter_cmp_slurry_particles",
            "setting": "Flintshaw CMP FS-6 (invented), Ashlar Polish, pad P-4.",
        },
        "safety_decision": {"decision": "MODIFY", "rationale": "isolate pad"},
    }
    traj2 = {
        "id": "nelb-r01-002-t2",
        "safety_decision": {"decision": "ACCEPT", "rationale": "new aperture"},
    }
    return {
        "id": "nelb-r01-002",
        "language_view": {
            "description": "Coulter remaining-particle family",
            "trajectory": traj,
            "trajectory_new_aperture": traj2,
        },
        "reconstruction_model": {
            "name": "coulter_cmp_particle_concentration",
            "formula": "C_ppm = k_c * (Vp_mV / Vref_mV)",
        },
        "bridge_notes": {"why_high_value": "Coulter remaining-particle family"},
    }

def rec_003():
    traj = {
        "id": "nelb-r01-003-t1",
        "state": {
            "sim_or_real": "simulated",
            "domain": "photoelastic_copv_hoop_stress",
            "setting": "Yewholt COPV YH-9 (invented), Bramble Tank Yard, vessel V-4.",
        },
        "safety_decision": {"decision": "ACCEPT", "rationale": "isolate V-4 only"},
    }
    traj2 = {
        "id": "nelb-r01-003-t2",
        "safety_decision": {"decision": "REJECT", "rationale": "do not skip V-1..V-3"},
    }
    return {
        "id": "nelb-r01-003",
        "language_view": {
            "description": "Photoelastic remaining-hoop family",
            "trajectory": traj,
            "trajectory_skip_vessel_refusal": traj2,
        },
        "reconstruction_model": {
            "name": "photoelastic_copv_hoop_stress",
            "formula": "sigma_MPa = k_p * N",
        },
        "bridge_notes": {"why_high_value": "Photoelastic remaining-hoop family"},
    }
"""


def invoke(argv):
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        code = cli.run(argv)
    return code, out.getvalue(), err.getvalue()


class PackageShape(unittest.TestCase):
    def test_family_home_is_the_five_cleaned_modules(self):
        names = {path.name for path in NELB_DIR.glob("*.py")}
        self.assertEqual(names, set(PACKAGE_FILES))
        self.assertEqual(list(NELB_DIR.glob("*mill*.py")), [])
        self.assertEqual(list(NELB_DIR.glob("gen_r*.py")), [])
        self.assertFalse(any("mill" in name for name in names))

    def test_catalog_is_compact_jsonl_plus_header(self):
        header = NELB_DIR / CATALOG_FILENAME
        plants = NELB_DIR / PLANTS_FILENAME
        self.assertTrue(header.is_file())
        self.assertTrue(plants.is_file())
        payload = plants.read_bytes()
        self.assertTrue(payload.endswith(b"\n"))
        self.assertNotIn(b"\r", payload)
        lines = payload.splitlines()
        self.assertGreater(len(lines), 3)
        self.assertEqual(len(lines), len({line for line in lines if line}))

    def test_both_import_spellings_are_one_object(self):
        if str(REPO) not in sys.path:
            sys.path.append(str(REPO))
        from pipelines.nelb import catalog as packaged

        self.assertIs(packaged, cat)
        self.assertIs(sys.modules["nelb.catalog"], sys.modules["pipelines.nelb.catalog"])

    def test_vendor_paths_are_refused(self):
        with self.assertRaises(NelbRefusal) as ctx:
            refuse_vendor_paths(["pipelines/nelb/nelb-mill-r01.py"])
        self.assertEqual(ctx.exception.code, FINDING_VENDOR_PATH)
        with self.assertRaises(NelbRefusal) as ctx:
            refuse_vendor_paths(["/tmp/nelb-r01-live/gen_r01.py"])
        self.assertEqual(ctx.exception.code, FINDING_VENDOR_PATH)


class Contract(unittest.TestCase):
    def test_factory_matches_the_hosted_bridge_lane(self):
        self.assertEqual(FACTORY, "neuromorphic-event-language-bridge")
        self.assertEqual(FAMILY_PREFIX, "nelb")
        self.assertEqual(GENERATOR, "grok-4.6")
        self.assertEqual(ISOLATION, "single-session")
        self.assertEqual(QUOTA_PER_ROUND, 3)
        self.assertEqual(SOURCE_REF, "origin/codex/recover-grok-01a06111")
        self.assertEqual(SOURCE_COMMIT, "e5206e72fa829931162944648e1e180949baaf0b")


class AstExtract(unittest.TestCase):
    def test_plants_from_source_reads_rec_functions_without_exec(self):
        plants = cat.plants_from_source(SNIPPET, "snippet")
        self.assertEqual(len(plants), 3)
        self.assertEqual(
            [plant.record_id for plant in plants],
            ["nelb-r01-001", "nelb-r01-002", "nelb-r01-003"],
        )
        self.assertEqual(plants[0].site, "Brackfen Pool BF-3")
        self.assertEqual(plants[0].lead_decision, "REJECT")
        self.assertEqual(plants[0].companion_key, "trajectory_recirc_hold")
        self.assertEqual(plants[1].sim_or_real, "hil")
        self.assertEqual(plants[1].reconstruction, "coulter_cmp_particle_concentration")
        self.assertEqual(plants[2].companion_decision, "REJECT")
        self.assertEqual(plants[2].companion_key, "trajectory_skip_vessel_refusal")

    def test_pairs_list_extract_does_not_exec(self):
        source = (
            "FACTORY = 'neuromorphic-event-language-bridge'\n"
            "ROUND = 1\n"
            "MUST_NOT_RUN = undefined_name\n"
            "PAIRS = [\n"
            "  {'id': 'nelb-r01-001', 'index': 1, 'site': 'Brackfen Pool BF-3',\n"
            "   'domain': 'johnson_noise_spent_fuel_pool_t', 'sim_or_real': 'designed',\n"
            "   'reconstruction': 'johnson_noise_pool_temperature',\n"
            "   'lead_decision': 'REJECT', 'companion_decision': 'MODIFY',\n"
            "   'goal': 'gate continue-recirc'},\n"
            "  {'id': 'nelb-r01-002', 'index': 2, 'site': 'Flintshaw CMP FS-6',\n"
            "   'domain': 'coulter_cmp_slurry_particles', 'sim_or_real': 'hil',\n"
            "   'reconstruction': 'coulter_cmp_particle_concentration',\n"
            "   'lead_decision': 'MODIFY', 'companion_decision': 'ACCEPT',\n"
            "   'goal': 'gate keep-polish'},\n"
            "  {'id': 'nelb-r01-003', 'index': 3, 'site': 'Yewholt COPV YH-9',\n"
            "   'domain': 'photoelastic_copv_hoop_stress', 'sim_or_real': 'simulated',\n"
            "   'reconstruction': 'photoelastic_copv_hoop_stress',\n"
            "   'lead_decision': 'ACCEPT', 'companion_decision': 'REJECT',\n"
            "   'goal': 'gate V-4 isolate'},\n"
            "]\n"
        )
        plants = cat.plants_from_source(source, "pairs")
        self.assertEqual([plant.record_id for plant in plants], [
            "nelb-r01-001",
            "nelb-r01-002",
            "nelb-r01-003",
        ])
        self.assertEqual(plants[1].site, "Flintshaw CMP FS-6")
        self.assertEqual(plants[2].lead_decision, "ACCEPT")


class CommittedCatalog(unittest.TestCase):
    def test_catalog_covers_recovered_triples_with_r01_pinned(self):
        loaded = cat.load_catalog()
        report = cat.catalog_check()
        self.assertEqual(loaded.catalog_id, "nelb-plants-v2")
        self.assertEqual(report["status"], "ok")
        self.assertEqual(report["plants"], 102)
        self.assertEqual(report["triples"], 34)
        self.assertEqual(report["first_round"], 1)
        self.assertIn(2, report["rounds"])
        r01 = cat.plants_for_round(1)
        self.assertEqual(
            [plant.record_id for plant in r01],
            ["nelb-r01-001", "nelb-r01-002", "nelb-r01-003"],
        )
        self.assertEqual(r01[0].site, "Brackfen Pool BF-3")
        self.assertEqual(r01[0].lead_decision, "REJECT")
        self.assertEqual(r01[1].sim_or_real, "hil")
        self.assertEqual(r01[2].companion_key, "trajectory_skip_vessel_refusal")
        r02 = cat.plants_for_round(2)
        self.assertEqual([plant.record_id for plant in r02], [
            "nelb-r02-001",
            "nelb-r02-002",
            "nelb-r02-003",
        ])

    def test_plants_jsonl_digest_matches_catalog_header(self):
        header = json.loads((NELB_DIR / CATALOG_FILENAME).read_text(encoding="utf-8"))
        digest = sha256_bytes((NELB_DIR / PLANTS_FILENAME).read_bytes())
        self.assertEqual(header["plants_sha256"], digest)
        self.assertEqual(header["extract"]["legacy_ref"], LEGACY_REF)
        self.assertEqual(header["extract"]["legacy_commit"], LEGACY_COMMIT)

    def test_a_round_outside_the_committed_catalog_is_refused(self):
        with self.assertRaises(NelbRefusal) as ctx:
            cat.plants_for_round(4)
        self.assertEqual(ctx.exception.code, FINDING_ROUND_OUT_OF_DOMAIN)
        with self.assertRaises(NelbRefusal) as ctx:
            cat.plants_for_round(True)  # type: ignore[arg-type]
        self.assertEqual(ctx.exception.code, FINDING_ROUND_OUT_OF_DOMAIN)


class Generate(unittest.TestCase):
    def setUp(self):
        self.root = Path(tempfile.mkdtemp(prefix="nelb-gen-"))
        self.addCleanup(shutil.rmtree, self.root, True)

    def test_record_is_a_bridge_pair(self):
        plant = cat.plants_for_round(1)[0]
        rec = generate.record(plant)
        self.assertEqual(rec["id"], "nelb-r01-001")
        self.assertEqual(classify_kind(rec), "bridge_pair")
        self.assertEqual(mill_prefix(rec), "nelb")
        self.assertEqual(rec["meta"]["factory"], FACTORY)
        self.assertEqual(rec["meta"]["isolation"], ISOLATION)
        self.assertEqual(rec["language_view"]["trajectory"]["safety_decision"]["decision"], "REJECT")
        self.assertEqual(
            rec["language_view"]["trajectory_recirc_hold"]["safety_decision"]["decision"],
            "MODIFY",
        )
        self.assertEqual(len(rec["spike_events"]), 2)
        self.assertNotIn("chosen", rec)
        self.assertNotIn("rejected", rec)

    def test_round_1_writes_three_records_and_refuses_clobber_or_raw(self):
        out = self.root / "run"
        summary = generate.run(generate.RunRequest(1, out))
        self.assertEqual(summary["records"], 3)
        self.assertEqual(summary["ids"], ["nelb-r01-001", "nelb-r01-002", "nelb-r01-003"])
        batch = (out / "batch-r01.jsonl").read_text(encoding="utf-8").splitlines()
        self.assertEqual(len(batch), 3)
        first = json.loads(batch[0])
        self.assertEqual(first["meta"]["factory"], FACTORY)
        self.assertEqual(classify_kind(first), "bridge_pair")
        notes = (out / "NOTES-r01.md").read_text(encoding="utf-8")
        self.assertIn("single-session", notes)
        with self.assertRaises(NelbRefusal) as exists:
            generate.run(generate.RunRequest(1, out))
        self.assertEqual(exists.exception.code, FINDING_DESTINATION_EXISTS)
        raw = self.root / "outputs" / "raw" / "x"
        with self.assertRaises(NelbRefusal) as under_raw:
            generate.run(generate.RunRequest(1, raw))
        self.assertEqual(under_raw.exception.code, FINDING_DESTINATION_UNDER_RAW)
        self.assertFalse(raw.exists())

    def test_an_interrupt_during_the_write_removes_the_destination(self):
        out = self.root / "run"

        def interrupt(*_args, **_kwargs):
            raise KeyboardInterrupt

        with mock.patch.object(generate, "_fsync_destination", interrupt):
            with self.assertRaises(KeyboardInterrupt):
                generate.run(generate.RunRequest(1, out))
        self.assertFalse(out.exists())
        summary = generate.run(generate.RunRequest(1, out))
        self.assertEqual(summary["records"], 3)

    def test_batch_jsonl_uses_literal_lf_record_boundaries(self):
        out = self.root / "run"
        generate.run(generate.RunRequest(1, out))
        payload = (out / "batch-r01.jsonl").read_bytes()
        self.assertNotIn(b"\r", payload)
        records = payload.split(b"\n")
        self.assertEqual(records[-1], b"")
        self.assertEqual(len(records) - 1, 3)


class Cli(unittest.TestCase):
    def setUp(self):
        self.root = Path(tempfile.mkdtemp(prefix="nelb-cli-"))
        self.addCleanup(shutil.rmtree, self.root, True)

    def test_catalog_lists_plants(self):
        code, out, err = invoke(["catalog"])
        self.assertEqual((code, err), (0, ""))
        self.assertIn("nelb-plants-v2", out)
        self.assertIn("nelb-r01-001", out)

    def test_catalog_check_json(self):
        code, out, err = invoke(["catalog-check", "--json"])
        self.assertEqual((code, err), (0, ""))
        payload = json.loads(out)
        self.assertEqual(payload["status"], "ok")
        self.assertEqual(payload["plants"], 102)
        self.assertEqual(payload["triples"], 34)

    def test_generate_stdout_and_a_raw_refusal(self):
        code, out, err = invoke(["generate", "--round", "1"])
        self.assertEqual((code, err), (0, ""))
        lines = [line for line in out.splitlines() if line]
        self.assertEqual(len(lines), 3)
        self.assertEqual(json.loads(lines[0])["id"], "nelb-r01-001")
        dest = self.root / "dest"
        code, stdout, err = invoke(
            ["generate", "--round", "1", "--out", str(dest), "--json"]
        )
        self.assertEqual((code, err), (0, ""))
        payload = json.loads(stdout)
        self.assertEqual(payload["status"], "ok")
        self.assertEqual(payload["summary"]["records"], 3)
        code, stdout, _err = invoke(
            [
                "generate",
                "--round",
                "1",
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
