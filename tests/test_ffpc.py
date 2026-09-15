#!/usr/bin/env python3
"""The cleaned ``ffpc`` family home under ``pipelines/ffpc/``.

Recovered Session-A builders on ``origin/codex/recover-grok-01a06111`` were
AST-extracted. These tests pin identity, catalog fidelity, and preference
shape without publishing a raw round and without importing a ``*mill*.py``
module.
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
FFPC_DIR = REPO / "pipelines" / "ffpc"
sys.path.insert(0, str(REPO / "pipelines"))

from ffpc import catalog as cat  # noqa: E402
from ffpc import cli, generate  # noqa: E402
from ffpc._contract import (  # noqa: E402
    FACTORY,
    FAMILY_PREFIX,
    FINDING_DESTINATION_EXISTS,
    FINDING_DESTINATION_UNDER_RAW,
    FINDING_ROUND_OUT_OF_DOMAIN,
    FINDING_VENDOR_PATH,
    GENERATOR,
    ISOLATION,
    QUOTA_PER_ROUND,
    SOURCE_COMMIT,
    SOURCE_REF,
    FfpcRefusal,
    refuse_vendor_paths,
)
from mill_signals import mill_prefix  # noqa: E402
from record_kind import classify_kind, preference_side_kinds  # noqa: E402

PACKAGE_FILES = (
    "__init__.py",
    "_contract.py",
    "catalog.py",
    "generate.py",
    "cli.py",
)
SNIPPET = """
FACTORY = "failure-as-fuel-preference-cascade"
ROUND = 15
GENERATOR = "grok-4.6"
ISOLATION = "two-session"

PAIR_01_STATE = {
    "sim_or_real": "designed",
    "domain": "copper solvent-extraction electrowinning",
    "environment": {"site": "Complejo Lixivia de la Cuesta SX-EW MS-4"},
}
PAIR_01_DIAGNOSIS = {"root_cause": "lagging lab composite used as a trip veto"}
PAIR_02_STATE = {
    "sim_or_real": "designed",
    "domain": "high-head Francis hydro",
    "environment": {"site": "Hidroelectrica Canon Oscuro Francis U-3"},
}
PAIR_02_DIAGNOSIS = {"root_cause": "statutory min flow used as a close veto"}
PAIR_03_STATE = {
    "sim_or_real": "designed",
    "domain": "mechanical vapor-recompression brine evaporator",
    "environment": {"site": "Salinas de Costa Bruma MVR EV-2"},
}
PAIR_03_DIAGNOSIS = {"root_cause": "watchdog reset painted as live health"}

PAIRS = [
    {
        "index": 1,
        "id": "ffpc-r15-001",
        "state": PAIR_01_STATE,
        "diagnosis": PAIR_01_DIAGNOSIS,
        "failure_archetype": "lagging_lab_composite_as_inline_trip_veto",
        "site": "Complejo Lixivia de la Cuesta SX-EW MS-4",
    },
    {
        "index": 2,
        "id": "ffpc-r15-002",
        "state": PAIR_02_STATE,
        "diagnosis": PAIR_02_DIAGNOSIS,
        "failure_archetype": "statutory_min_flow_as_protective_close_veto",
        "site": "Hidroelectrica Canon Oscuro Francis U-3",
    },
    {
        "index": 3,
        "id": "ffpc-r15-003",
        "state": PAIR_03_STATE,
        "diagnosis": PAIR_03_DIAGNOSIS,
        "failure_archetype": "watchdog_reset_as_live_process_health",
        "site": "Salinas de Costa Bruma MVR EV-2",
    },
]
"""


def invoke(argv):
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        code = cli.run(argv)
    return code, out.getvalue(), err.getvalue()


class PackageShape(unittest.TestCase):
    def test_family_home_is_the_five_cleaned_modules(self):
        names = {path.name for path in FFPC_DIR.glob("*.py")}
        self.assertEqual(names, set(PACKAGE_FILES))
        self.assertEqual(list(FFPC_DIR.glob("*mill*.py")), [])
        self.assertFalse(any("mill" in name for name in names))

    def test_both_import_spellings_are_one_object(self):
        if str(REPO) not in sys.path:
            sys.path.append(str(REPO))
        from pipelines.ffpc import catalog as packaged

        self.assertIs(packaged, cat)
        self.assertIs(sys.modules["ffpc.catalog"], sys.modules["pipelines.ffpc.catalog"])

    def test_vendor_paths_are_refused(self):
        with self.assertRaises(FfpcRefusal) as ctx:
            refuse_vendor_paths(["pipelines/ffpc/ffpc-mill-r15.py"])
        self.assertEqual(ctx.exception.code, FINDING_VENDOR_PATH)


class Contract(unittest.TestCase):
    def test_factory_matches_the_hosted_preference_lane(self):
        self.assertEqual(FACTORY, "failure-as-fuel-preference-cascade")
        self.assertEqual(FAMILY_PREFIX, "ffpc")
        self.assertEqual(GENERATOR, "grok-4.6")
        self.assertEqual(ISOLATION, "two-session")
        self.assertEqual(QUOTA_PER_ROUND, 3)
        self.assertEqual(SOURCE_REF, "origin/codex/recover-grok-01a06111")
        self.assertEqual(SOURCE_COMMIT, "e5206e72fa829931162944648e1e180949baaf0b")


class AstExtract(unittest.TestCase):
    def test_plants_from_source_reads_dict_pairs(self):
        plants = cat.plants_from_source(SNIPPET, "snippet")
        self.assertEqual(len(plants), 3)
        self.assertEqual([plant.record_id for plant in plants], [
            "ffpc-r15-001",
            "ffpc-r15-002",
            "ffpc-r15-003",
        ])
        self.assertEqual(plants[0].site, "Complejo Lixivia de la Cuesta SX-EW MS-4")
        self.assertEqual(plants[0].failure_mode, "lagging_lab_composite_as_inline_trip_veto")
        self.assertEqual(plants[2].sim_or_real, "designed")

    def test_state_slot_extract_does_not_exec(self):
        source = (
            "FACTORY = 'failure-as-fuel-preference-cascade'\n"
            "ROUND = 16\n"
            "STATE_01 = {'sim_or_real': 'designed', 'domain': 'chlor-alkali',\n"
            "            'environment': {'unit': 'Cloro del Banco MH-2'}}\n"
            "DIAG_01 = {'root': 'cal-gas parked as live O2'}\n"
            "STATE_02 = {'sim_or_real': 'designed', 'domain': 'steam cracker',\n"
            "            'environment': {'unit': 'Olefinas Quilla F-2105'}}\n"
            "DIAG_02 = {'root': 'coil metal spent as COT'}\n"
            "STATE_03 = {'sim_or_real': 'designed', 'domain': 'Francis penstock',\n"
            "            'environment': {'unit': 'Presa del Cardo U-2'}}\n"
            "DIAG_03 = {'root': 'residual head after gate close'}\n"
            "PAIRS = [(REJECTED_01, DIAG_01), (REJECTED_02, DIAG_02), (REJECTED_03, DIAG_03)]\n"
        )
        plants = cat.plants_from_source(source, "slots")
        self.assertEqual([plant.record_id for plant in plants], [
            "ffpc-r16-001",
            "ffpc-r16-002",
            "ffpc-r16-003",
        ])
        self.assertEqual(plants[0].site, "Cloro del Banco MH-2")
        self.assertEqual(plants[0].root_cause, "cal-gas parked as live O2")


class CommittedCatalog(unittest.TestCase):
    def test_catalog_is_a_three_stride(self):
        loaded = cat.load_catalog()
        report = cat.catalog_check()
        self.assertEqual(loaded.catalog_id, "ffpc-recover-v1")
        self.assertEqual(report["status"], "ok")
        self.assertEqual(report["plants"], len(loaded.plants))
        self.assertEqual(report["plants"] % 3, 0)
        self.assertGreaterEqual(report["triples"], 17)
        self.assertEqual(report["first_round"], 1)
        self.assertIn(15, report["rounds"])
        self.assertEqual(loaded.plants[0].record_id[:5], "ffpc-")
        r15 = cat.plants_for_round(15)
        self.assertEqual(len(r15), 3)
        self.assertEqual(r15[0].record_id, "ffpc-r15-001")

    def test_a_round_outside_the_recovered_wave_is_refused(self):
        with self.assertRaises(FfpcRefusal) as ctx:
            cat.plants_for_round(3)
        self.assertEqual(ctx.exception.code, FINDING_ROUND_OUT_OF_DOMAIN)
        with self.assertRaises(FfpcRefusal) as ctx:
            cat.plants_for_round(True)  # type: ignore[arg-type]
        self.assertEqual(ctx.exception.code, FINDING_ROUND_OUT_OF_DOMAIN)


class Generate(unittest.TestCase):
    def setUp(self):
        self.root = Path(tempfile.mkdtemp(prefix="ffpc-gen-"))
        self.addCleanup(shutil.rmtree, self.root, True)

    def test_pair_is_a_same_state_preference_record(self):
        plant = cat.plants_for_round(15)[0]
        rec = generate.pair(plant)
        self.assertEqual(rec["id"], "ffpc-r15-001")
        self.assertEqual(classify_kind(rec), "preference")
        self.assertEqual(preference_side_kinds(rec), ("thalamic", "thalamic"))
        self.assertEqual(mill_prefix(rec), "ffpc")
        self.assertEqual(rec["meta"]["factory"], FACTORY)
        self.assertEqual(rec["meta"]["isolation"], ISOLATION)
        self.assertEqual(rec["chosen"]["state"], rec["rejected"]["state"])
        self.assertEqual(rec["chosen"]["proposed_action"], rec["rejected"]["proposed_action"])
        self.assertEqual(rec["rejected"]["safety_decision"]["decision"], "ACCEPT")
        self.assertIn(rec["chosen"]["safety_decision"]["decision"], {"MODIFY", "REJECT"})

    def test_round_15_writes_three_records_and_refuses_clobber_or_raw(self):
        out = self.root / "run"
        summary = generate.run(generate.RunRequest(15, out))
        self.assertEqual(summary["records"], 3)
        self.assertEqual(summary["ids"], ["ffpc-r15-001", "ffpc-r15-002", "ffpc-r15-003"])
        batch = (out / "batch-r15.jsonl").read_text(encoding="utf-8").splitlines()
        self.assertEqual(len(batch), 3)
        first = json.loads(batch[0])
        self.assertEqual(first["meta"]["factory"], FACTORY)
        notes = (out / "NOTES-r15.md").read_text(encoding="utf-8")
        self.assertIn("two-session", notes)
        with self.assertRaises(FfpcRefusal) as exists:
            generate.run(generate.RunRequest(15, out))
        self.assertEqual(exists.exception.code, FINDING_DESTINATION_EXISTS)
        raw = self.root / "outputs" / "raw" / "x"
        with self.assertRaises(FfpcRefusal) as under_raw:
            generate.run(generate.RunRequest(15, raw))
        self.assertEqual(under_raw.exception.code, FINDING_DESTINATION_UNDER_RAW)
        self.assertFalse(raw.exists())

    def test_an_interrupt_during_the_write_removes_the_destination(self):
        out = self.root / "run"

        def interrupt(*_args, **_kwargs):
            raise KeyboardInterrupt

        with mock.patch.object(generate, "_fsync_destination", interrupt):
            with self.assertRaises(KeyboardInterrupt):
                generate.run(generate.RunRequest(15, out))
        self.assertFalse(out.exists())
        summary = generate.run(generate.RunRequest(15, out))
        self.assertEqual(summary["records"], 3)

    def test_batch_jsonl_uses_literal_lf_record_boundaries(self):
        out = self.root / "run"
        generate.run(generate.RunRequest(15, out))
        payload = (out / "batch-r15.jsonl").read_bytes()
        self.assertNotIn(b"\r", payload)
        records = payload.split(b"\n")
        self.assertEqual(records[-1], b"")
        self.assertEqual(len(records) - 1, 3)


class Cli(unittest.TestCase):
    def setUp(self):
        self.root = Path(tempfile.mkdtemp(prefix="ffpc-cli-"))
        self.addCleanup(shutil.rmtree, self.root, True)

    def test_catalog_lists_plants(self):
        code, out, err = invoke(["catalog"])
        self.assertEqual((code, err), (0, ""))
        self.assertIn("ffpc-recover-v1", out)
        self.assertIn("ffpc-r15-001", out)

    def test_catalog_check_json(self):
        code, out, err = invoke(["catalog-check", "--json"])
        self.assertEqual((code, err), (0, ""))
        payload = json.loads(out)
        self.assertEqual(payload["status"], "ok")
        self.assertGreaterEqual(payload["plants"], 51)

    def test_generate_stdout_and_a_raw_refusal(self):
        code, out, err = invoke(["generate", "--round", "15"])
        self.assertEqual((code, err), (0, ""))
        lines = [line for line in out.splitlines() if line]
        self.assertEqual(len(lines), 3)
        self.assertEqual(json.loads(lines[0])["id"], "ffpc-r15-001")
        dest = self.root / "dest"
        code, stdout, err = invoke(
            ["generate", "--round", "15", "--out", str(dest), "--json"]
        )
        self.assertEqual((code, err), (0, ""))
        payload = json.loads(stdout)
        self.assertEqual(payload["status"], "ok")
        self.assertEqual(payload["summary"]["records"], 3)
        code, stdout, _err = invoke(
            [
                "generate",
                "--round",
                "15",
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
