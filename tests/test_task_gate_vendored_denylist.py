"""The omitted denylist is the vendored eval-exclusion list."""

import hashlib
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent))

from task_gate_test_support import (
    ADD, PASSED, PROGRAMS, REPO, FakeHarness, cv, decide, denylist, proposal, proposal_for, refused,
    rules,
)
from task_gate import runner


class VendoredDenylist(unittest.TestCase):
    def test_none_loads_the_vendored_denylist(self):
        self.assertEqual(
            denylist.VENDORED_DENYLIST, REPO / "config" / "eval-exclusion" / "eval-denylist.json",
        )
        loaded = denylist.load_denylist(None)
        vendored = denylist.load_denylist(denylist.VENDORED_DENYLIST)
        self.assertEqual(loaded.program_ids, vendored.program_ids)
        self.assertEqual(loaded.sha256, vendored.sha256)
        self.assertEqual(len(loaded), 19)

    def test_a_missing_vendored_denylist_is_refused(self):
        with tempfile.TemporaryDirectory() as tmp:
            missing = Path(tmp) / "nope.json"
            bad = Path(tmp) / "bad.txt"
            bad.write_bytes(b"")
            with mock.patch.object(denylist, "VENDORED_DENYLIST", missing):
                self.assertEqual(refused(denylist.load_denylist, None), cv.REFUSE_DENYLIST_MISSING)
            with mock.patch.object(denylist, "VENDORED_DENYLIST", bad):
                self.assertEqual(refused(denylist.load_denylist, None), cv.REFUSE_DENYLIST_MALFORMED)

    def test_an_omitted_denylist_records_the_vendored_digest(self):
        vendored = denylist.load_denylist(None)
        with tempfile.TemporaryDirectory() as tmp:
            summary = runner.run(
                runner.GateRequest(PROGRAMS, [proposal_for()], None, Path(tmp) / "out"),
                FakeHarness({ADD: PASSED}),
            )
        self.assertEqual(summary["inputs"]["denylist"]["sha256"], vendored.sha256)
        self.assertEqual(summary["inputs"]["denylist"]["entries"], len(vendored))

    def test_a_missing_vendored_denylist_refuses_and_writes_nothing(self):
        with tempfile.TemporaryDirectory() as tmp:
            missing = Path(tmp) / "missing.json"
            bad = Path(tmp) / "bad.txt"
            bad.write_bytes(b"")
            for path, code_name in (
                (missing, cv.REFUSE_DENYLIST_MISSING), (bad, cv.REFUSE_DENYLIST_MALFORMED),
            ):
                out = Path(tmp) / f"out-{path.name}"
                with self.subTest(code=code_name):
                    with mock.patch.object(denylist, "VENDORED_DENYLIST", path):
                        request = runner.GateRequest(PROGRAMS, [proposal_for()], None, out)
                        code = refused(runner.run, request, FakeHarness({ADD: PASSED}))
                    self.assertEqual(code, code_name)
                    self.assertFalse(out.exists())

    def test_vendored_held_out_program_ids_are_all_denylisted(self):
        loaded = denylist.load_denylist(REPO / "config/eval-exclusion/eval-denylist.json")
        self.assertEqual(len(loaded.program_ids), 19)
        gate_rules = rules(deny=loaded)
        for program_id in loaded.program_ids:
            with self.subTest(program_id=program_id):
                item = proposal.MalformedProposal("held-out", program_id, cv.DETAIL_MALFORMED_ROW)
                decision, fake = decide(item, rule_set=gate_rules)
                self.assertEqual(decision.verdict, cv.VERDICT_DENYLISTED)
                self.assertEqual(fake.calls, [])

    def test_run_summary_records_the_denylist_file_digest(self):
        path = REPO / "config/eval-exclusion/eval-denylist.json"
        loaded = denylist.load_denylist(path)
        with tempfile.TemporaryDirectory() as tmp:
            summary = runner.run(
                runner.GateRequest(PROGRAMS, [proposal_for()], loaded, Path(tmp) / "out"),
                FakeHarness({ADD: PASSED}),
            )
        self.assertEqual(summary["inputs"]["denylist"]["sha256"], loaded.sha256)
        self.assertEqual(summary["inputs"]["eval_program_ids"], {
            "count": 0,
            "sha256": hashlib.sha256(b"").hexdigest(),
        })
