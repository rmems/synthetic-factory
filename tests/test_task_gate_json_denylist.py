"""Strict JSON denylist refusals and the recorded eval-program-id digest."""

import hashlib
import sys
import tempfile
import unittest
from dataclasses import replace
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent))

from task_gate import runner
from task_gate_test_support import (
    ADD, DENY, PASSED, PROGRAMS, FakeHarness, cv, denylist, lists, proposal_for, refused,
    write_denylist_json,
)


class JsonDenylistRefusals(unittest.TestCase):
    def _canonical(self, **overrides) -> bytes:
        document = {
            "schema_version": lists.LIST_SCHEMA_VERSION,
            "list": lists.LIST_EVAL_DENYLIST,
            "status": "reviewed",
            "note": "loader test",
            "repos": [],
            "program_ids": ["prog-eval"],
            "task_ids": [],
        }
        document.update(overrides)
        return lists.canonical_bytes(document)

    def test_json_loader_refuses_documents_the_strict_list_loader_refuses(self):
        cases = {
            "wrong list": self._canonical(list="do_not_train"),
            "placeholder with entries": self._canonical(status="placeholder"),
            "unsorted ids": self._canonical(program_ids=["prog-z", "prog-a"]),
            "non-string id": self._canonical(program_ids=[123]),
            "json array": b'["prog-eval"]\n',
            "leading space": b" " + self._canonical(),
        }
        with tempfile.TemporaryDirectory() as tmp:
            for name, payload in cases.items():
                path = Path(tmp) / f"{name}.json"
                path.write_bytes(payload)
                with self.subTest(name=name):
                    self.assertEqual(
                        refused(denylist.load_denylist, path), cv.REFUSE_DENYLIST_MALFORMED,
                    )

    def test_empty_program_ids_name_the_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "empty.json"
            path.write_bytes(self._canonical(program_ids=[], repos=["clap-rs/clap"]))
            with self.assertRaises(cv.GateRefusal) as caught:
                denylist.load_denylist(path)
            self.assertEqual(caught.exception.code, cv.REFUSE_DENYLIST_MALFORMED)
            self.assertIn(str(path), caught.exception.detail)
            self.assertIn("repos names 1", caught.exception.detail)
            path.write_bytes(self._canonical(program_ids=[], repos=[]))
            with self.assertRaises(cv.GateRefusal) as empty:
                denylist.load_denylist(path)
            self.assertIn(f"{path}: denylist has no entries", empty.exception.detail)

    def test_a_denylist_that_changes_while_loading_is_malformed(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "deny.json"
            write_denylist_json(path, ["prog-eval"])
            loaded = lists.load_list(path, lists.LIST_EVAL_DENYLIST)
            stale = replace(loaded, sha256="0" * 64)
            with mock.patch.object(denylist._exclusion_lists, "load_list", return_value=stale):
                code = refused(denylist.load_denylist, path)
        self.assertEqual(code, cv.REFUSE_DENYLIST_MALFORMED)

    def test_run_summary_records_eval_program_ids_and_rejects_an_override(self):
        ids = frozenset({"prog-held", "prog-eval"})
        digest = hashlib.sha256(b"prog-eval\nprog-held\n").hexdigest()
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "out"
            summary = runner.run(
                runner.GateRequest(
                    PROGRAMS, [proposal_for()], DENY, out, eval_program_ids=ids,
                ),
                FakeHarness({ADD: PASSED}),
            )
            self.assertEqual(summary["inputs"]["eval_program_ids"], {"count": 2, "sha256": digest})
            self.assertFalse((Path(tmp) / "overridden").exists())
            overridden = Path(tmp) / "overridden"
            code = refused(
                runner.run,
                runner.GateRequest(
                    PROGRAMS, [proposal_for()], DENY, overridden, eval_program_ids=ids,
                    provenance={"eval_program_ids": {"count": 0, "sha256": "0" * 64}},
                ),
                FakeHarness({ADD: PASSED}),
            )
            self.assertEqual(code, cv.REFUSE_INPUT_INVALID)
            self.assertFalse(overridden.exists())
