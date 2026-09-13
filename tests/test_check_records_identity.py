#!/usr/bin/env python3
"""check_records.py's identity and legacy-provenance warning contract.

Duplicate ids are a hard error (within a file and globally across a run);
legacy meta.id, legacy 'thought' episode steps, and missing sim_or_real are
each a warning, not an error, so the deep layer can flag drift without
blocking a run that a human still needs to read.
"""

import sys
import tempfile
import unittest
from pathlib import Path

_TESTS = Path(__file__).resolve().parent
if str(_TESTS) not in sys.path:
    sys.path.insert(0, str(_TESTS))

from check_records_test_helpers import _run_dir, _thalamic, _write_jsonl  # noqa: E402

import check_records  # noqa: E402


class CheckRecordsIdentityAndLegacy(unittest.TestCase):
    def test_duplicate_record_id_is_error(self):
        a = _thalamic(meta={"id": "dup-1"})
        b = _thalamic(meta={"id": "dup-1"})
        b["state"] = {"sim_or_real": "designed", "domain": "other"}
        tmp, run_dir = _run_dir([a, b])
        with tmp:
            result = check_records.check_run(run_dir)
        blob = "\n".join(result["errors"])
        self.assertIn("duplicate record id", blob)
        self.assertIn("dup-1", blob)
        self.assertIn("batch.jsonl:2", blob)
        self.assertEqual(result["exit_code"], 1)

    def test_legacy_meta_id_is_warning_for_new_corpus(self):
        rec = _thalamic(meta={"id": "legacy-only"})
        rec.pop("id")
        tmp, run_dir = _run_dir([rec])
        with tmp:
            loose = check_records.check_run(run_dir)
            strict = check_records.check_run(run_dir, strict=True)
        self.assertFalse(loose["errors"], loose)
        self.assertIn("legacy meta.id only", "\n".join(loose["warnings"]))
        self.assertEqual(strict["exit_code"], 1)

    def test_legacy_episode_thought_is_warning(self):
        episode = {
            "id": "legacy-episode",
            "goal": "fixture",
            "steps": [
                {
                    "thought": "private scratch",
                    "tool_call": {"name": "rg", "args": {}},
                    "observation": "none",
                }
            ],
            "outcome": "done",
            "reward": {"success": True},
        }
        tmp, run_dir = _run_dir([episode])
        with tmp:
            result = check_records.check_run(run_dir, strict=True)
        self.assertFalse(result["errors"], result)
        self.assertIn("legacy 'thought'", "\n".join(result["warnings"]))
        self.assertEqual(result["exit_code"], 1)

    def test_missing_sim_or_real_is_warning_not_error(self):
        rec = _thalamic()
        rec["state"] = {"domain": "no-provenance"}
        rec["meta"] = {"id": "no-sim", "round": 1}
        tmp, run_dir = _run_dir([rec])
        with tmp:
            result = check_records.check_run(run_dir)
            strict = check_records.check_run(run_dir, strict=True)
        self.assertFalse(result["errors"], result)
        self.assertTrue(result["warnings"], result)
        self.assertIn("sim_or_real", "\n".join(result["warnings"]))
        self.assertEqual(result["exit_code"], 0)
        self.assertEqual(strict["exit_code"], 1)

    def test_duplicate_ids_are_global_across_files(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            _write_jsonl(root / "a.jsonl", [_thalamic(id="root-dup", meta={"id": "meta-a"})])
            _write_jsonl(root / "b.jsonl", [_thalamic(id="root-dup", meta={"id": "meta-b"})])
            result = check_records.check_run(root)
        self.assertEqual(len(result["errors"]), 1, result)
        self.assertIn("root-dup", result["errors"][0])
        self.assertIn("a.jsonl:1", result["errors"][0])
        self.assertIn("b.jsonl:1", result["errors"][0])


if __name__ == "__main__":
    unittest.main()
