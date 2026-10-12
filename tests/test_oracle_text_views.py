"""The oracle-grounded text view: rows, coded refusals, one named tamper per leak code, CLI.

One small reference run is generated with ``oracle_generate`` into a temporary
directory for the whole module. Every accepted record must yield an SFT, a chat
and a multiple-choice row with no findings; every rejected record must be
refused with a coded refusal; each leak code has a named tamper that must be
reported; and the CLI must write its files once and refuse an existing, a
raw-tree or an unauthenticated destination or source.
"""

from __future__ import annotations

import contextlib
import copy
import hashlib
import io
import json
import math
import shutil
import subprocess  # nosec B404 -- runs the fixed local CLI script under test
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

REPO = Path(__file__).resolve().parents[1]
PIPELINES = REPO / "pipelines"
sys.path.insert(0, str(PIPELINES))

import oracle_generate
import oracle_text_view_rows as views
import oracle_text_view_vocabulary as tv
import oracle_text_views as cli
from oracle_grounded import canon, envelope

CLI_SCRIPT = PIPELINES / "oracle_text_views.py"
_STATE: dict = {}


def setUpModule():
    temp = tempfile.TemporaryDirectory(prefix="oracle-text-views-")
    run_dir = Path(temp.name) / "run"
    with contextlib.redirect_stdout(io.StringIO()):
        status = oracle_generate.main(["--count", "3", str(run_dir)])
    if status != 0:
        temp.cleanup()
        raise RuntimeError(f"oracle_generate exited {status}")
    run = cli.read_run(run_dir)
    _STATE.update(temp=temp, run_dir=run_dir, run=run)


def tearDownModule():
    _STATE.pop("temp").cleanup()


def records(status):
    return [record for _, record in _STATE["run"].records
            if record["validation"]["status"] == status]


def reseal(record):
    """Recompute both stored hashes so only the edit under test differs."""
    record["proposal_hash"] = canon.digest(envelope.proposal_of(record))
    record["result_hash"] = canon.digest(record["result"])
    return record


def invoke(argv):
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        status = cli.main([str(arg) for arg in argv])
    return status, out.getvalue(), err.getvalue()


class PositiveRows(unittest.TestCase):
    def test_every_accepted_record_yields_three_rows_with_no_findings(self):
        accepted = records(tv.STATUS_ACCEPTED)
        self.assertEqual({record["family"] for record in accepted}, set(tv.FAMILIES))
        for record in accepted:
            with self.subTest(record=record["id"]):
                self.assertTrue(views.is_positive(record))
                rows = views.rows_for(record)
                self.assertEqual(rows[tv.KIND_SFT], views.sft_row(record))
                self.assertEqual(rows[tv.KIND_CHAT], views.chat_row(record))
                self.assertEqual(rows[tv.KIND_CHOICE], views.choice_row(record))
                for kind, row in rows.items():
                    self.assertEqual(set(row), tv.ROW_KEYS[kind])
                    self.assertEqual(views.view_findings(record, row), [])
                self.assertIn(rows[tv.KIND_CHOICE]["answer"], rows[tv.KIND_CHOICE]["options"])
                prompt = rows[tv.KIND_SFT]["prompt"]
                self.assertEqual(prompt, views.render_prompt(views.public_view(record)))
                self.assertNotIn(tv.PREDICTED_PREFIX, prompt)
                self.assertNotIn(record["candidate_prediction"]["basis"], prompt)
                self.assertEqual(rows[tv.KIND_SFT]["completion"], views.completion_of(record))
                self.assertEqual(json.loads(rows[tv.KIND_SFT]["completion"]),
                                 json.loads(rows[tv.KIND_CHAT]["messages"][1]["content"]))

    def test_long_numeric_arrays_are_summarized_deterministically(self):
        record = next(r for r in records(tv.STATUS_ACCEPTED) if r["family"] == tv.ENCODER_FAMILY)
        signal = record["scenario"]["signal"]
        summary = views.public_view(record).scenario["signal"]
        self.assertGreater(len(signal), tv.MAX_INLINE_VALUES)
        self.assertEqual(summary, {
            tv.SUMMARY_MARKER: True, "length": len(signal), "min": min(signal),
            "max": max(signal), "mean": round(math.fsum(signal) / len(signal), 6),
        })
        compact_signal = json.dumps(signal, separators=(",", ":"))
        self.assertNotIn(compact_signal, views.sft_row(record)["prompt"])


class CodedRefusals(unittest.TestCase):
    def assert_refused(self, record, code):
        self.assertFalse(views.is_positive(record))
        self.assertEqual(views.refusal_of(record)[0], code)
        for builder in (views.sft_row, views.chat_row, views.choice_row, views.rows_for):
            with self.assertRaises(views.TextViewRefusal) as caught:
                builder(record)
            self.assertEqual(caught.exception.code, code)
            self.assertTrue(str(caught.exception).startswith(f"{code}: "))

    def test_rejected_records_are_refused(self):
        rejected = records("rejected")
        self.assertTrue(rejected, "the seeded run must contain a rejected record")
        for record in rejected:
            with self.subTest(record=record["id"]):
                self.assert_refused(record, tv.FINDING_RECORD_NOT_A_POSITIVE_EXAMPLE)

    def test_each_record_gate_has_its_code(self):
        base = records(tv.STATUS_ACCEPTED)[0]
        unpublishable = copy.deepcopy(base)
        unpublishable["validation"]["publishable"] = False
        not_simulated = copy.deepcopy(base)
        not_simulated["provenance"]["kind"] = "measured"
        misattributed = copy.deepcopy(base)
        misattributed["result"]["produced_by"] = "someone-else"
        unsealed = copy.deepcopy(base)
        unsealed["scenario"]["question"] += " (edited after sealing)"
        shapeless = copy.deepcopy(base)
        del shapeless["scenario"][tv.SCENARIO_KEYS[base["family"]][0]]
        cases = (
            ("unknown family", {**base, "family": "not-a-family"}, tv.FINDING_UNKNOWN_FAMILY),
            ("unpublishable", unpublishable, tv.FINDING_RECORD_NOT_A_POSITIVE_EXAMPLE),
            ("not simulated", not_simulated, tv.FINDING_RECORD_NOT_A_POSITIVE_EXAMPLE),
            ("misattributed", reseal(misattributed), tv.FINDING_RECORD_NOT_A_POSITIVE_EXAMPLE),
            ("unsealed", unsealed, tv.FINDING_RECORD_NOT_SEALED),
            ("missing public key", reseal(shapeless), tv.FINDING_UNSUPPORTED_RECORD_SHAPE),
        )
        for name, record, code in cases:
            with self.subTest(case=name):
                self.assert_refused(record, code)

    def test_a_leak_in_the_public_sections_refuses_the_row(self):
        record = copy.deepcopy(records(tv.STATUS_ACCEPTED)[0])
        record["scenario"]["reasoning"] = "a private chain of thought"
        reseal(record)
        self.assertTrue(views.is_positive(record))
        with self.assertRaises(views.TextViewRefusal) as caught:
            views.sft_row(record)
        self.assertEqual(caught.exception.code, tv.FINDING_RECORD_FAILS_VIEW_GATE)
        self.assertIn(tv.LEAK_HIDDEN_REASONING_KEY, str(caught.exception))


def _wrong_guess_neuron_record():
    for record in records(tv.STATUS_ACCEPTED):
        if record["family"] != tv.NEURON_FAMILY:
            continue
        guess = record["candidate_prediction"]["predicted_direction"]
        if guess != json.loads(views.completion_of(record))["direction"]:
            return record
    raise AssertionError("the seeded run must contain a neuron record with a wrong guess")


def _tampers(record):
    """``(name, leak code, tampered record, row)`` -- one or more per leak code."""
    sft, chat, choice = (views.render_row(record, kind) for kind in tv.ROW_KINDS)
    candidate = record["candidate_prediction"]
    completion = json.loads(sft["completion"])
    guess = candidate["predicted_direction"]
    measured = record["result"]["measured"]
    other = next(o for o in choice["options"] if o not in {choice["answer"], guess})
    off_by_one = {**completion, "spike_count_after": completion["spike_count_after"] + 1}
    guessed = {**completion, "direction": guess}
    edited_result, edited_scenario = copy.deepcopy(record), copy.deepcopy(record)
    edited_result["result"]["measured"]["after"]["spike_count"] += 1
    edited_scenario["scenario"]["question"] += " Explain."
    rejected = records("rejected")[0]
    with_reasoning = {**completion, "reasoning": "first I simulated it"}
    return (
        ("an id key added to the row", tv.LEAK_VIEW_EXTRA_KEYS,
         record, {**sft, "id": record["id"]}),
        ("a system message added to the chat", tv.LEAK_VIEW_EXTRA_KEYS,
         record, {"messages": [{"role": "system", "content": "x"}, *chat["messages"]]}),
        ("the measurement appended to the prompt", tv.LEAK_PROMPT_NOT_RENDERED_FROM_PUBLIC_VIEW,
         record, {**sft, "prompt": sft["prompt"] + json.dumps(measured["delta"])}),
        ("the choice options reordered", tv.LEAK_PROMPT_NOT_RENDERED_FROM_PUBLIC_VIEW,
         record, {**choice, "options": list(reversed(choice["options"]))}),
        ("a spike count off by one", tv.LEAK_COMPLETION_NOT_FROM_MEASUREMENT,
         record, {**sft, "completion": json.dumps(off_by_one, sort_keys=True)}),
        ("a choice answer that is neither label nor guess",
         tv.LEAK_LABEL_NOT_DERIVED_FROM_MEASUREMENT, record, {**choice, "answer": other}),
        ("the measurement edited after sealing", tv.LEAK_MEASUREMENT_DIGEST_MISMATCH,
         edited_result, sft),
        ("the scenario edited after sealing", tv.LEAK_PROPOSAL_DIGEST_MISMATCH,
         edited_scenario, sft),
        ("the heuristic basis in the prompt", tv.LEAK_CANDIDATE_PREDICTION_LEAKED,
         record, {**sft, "prompt": sft["prompt"] + candidate["basis"]}),
        ("the guessed value hinted in the prompt", tv.LEAK_CANDIDATE_PREDICTION_LEAKED,
         record, {**sft, "prompt": sft["prompt"] + f"Hint: {guess}\n"}),
        ("the completion copied from the guess", tv.LEAK_CANDIDATE_PREDICTION_LEAKED,
         record, {**sft, "completion": json.dumps(guessed, sort_keys=True)}),
        ("the choice answer copied from the guess", tv.LEAK_CANDIDATE_PREDICTION_LEAKED,
         record, {**choice, "answer": guess}),
        ("a predicted_* key in the row", tv.LEAK_CANDIDATE_PREDICTION_LEAKED,
         record, {**sft, "predicted_direction": guess}),
        ("a reasoning key in the completion", tv.LEAK_HIDDEN_REASONING_KEY,
         record, {**sft, "completion": json.dumps(with_reasoning, sort_keys=True)}),
        ("an internal_reasoning key on the row", tv.LEAK_HIDDEN_REASONING_KEY,
         record, {**sft, "internal_reasoning": "hidden"}),
        ("a row rendered from a rejected record", tv.LEAK_ROW_FROM_NON_POSITIVE_RECORD,
         rejected, views.render_row(rejected, tv.KIND_SFT)),
    )


class LeakTampers(unittest.TestCase):
    def test_each_named_tamper_is_reported_with_its_code(self):
        tampers = _tampers(_wrong_guess_neuron_record())
        self.assertEqual({code for _, code, _, _ in tampers}, tv.LEAK_CODE_SET)
        for name, code, record, row in tampers:
            with self.subTest(tamper=name):
                self.assertIn(code, views.view_findings(record, row))

    def test_tampers_report_only_what_they_did(self):
        record = _wrong_guess_neuron_record()
        tampers = {name: (record_, row) for name, _, record_, row in _tampers(record)}
        exact = {
            "an id key added to the row": [tv.LEAK_VIEW_EXTRA_KEYS],
            "a spike count off by one": [tv.LEAK_COMPLETION_NOT_FROM_MEASUREMENT],
            "a choice answer that is neither label nor guess":
                [tv.LEAK_LABEL_NOT_DERIVED_FROM_MEASUREMENT],
            "a row rendered from a rejected record": [tv.LEAK_ROW_FROM_NON_POSITIVE_RECORD],
        }
        for name, expected in exact.items():
            with self.subTest(tamper=name):
                self.assertEqual(views.view_findings(*tampers[name]), expected)

    def test_a_row_that_is_not_a_mapping_is_reported(self):
        record = records(tv.STATUS_ACCEPTED)[0]
        findings = views.view_findings(record, ["not", "a", "row"])
        self.assertIn(tv.LEAK_VIEW_EXTRA_KEYS, findings)
        self.assertIn(tv.LEAK_PROMPT_NOT_RENDERED_FROM_PUBLIC_VIEW, findings)


class CommandLine(unittest.TestCase):
    def setUp(self):
        self._temp = tempfile.TemporaryDirectory(prefix="oracle-text-views-out-")
        self.addCleanup(self._temp.cleanup)
        self.root = Path(self._temp.name)

    def test_writes_every_family_file_and_a_summary_once(self):
        out = self.root / "views"
        status, stdout, _ = invoke([_STATE["run_dir"], "--out", out, "--json"])
        self.assertEqual(status, cli.EXIT_OK)
        summary = json.loads((out / tv.SUMMARY_FILENAME).read_text(encoding="utf-8"))
        self.assertEqual(json.loads(stdout), summary)
        expected_files = {
            f"{family}.{kind}.jsonl" for family in tv.FAMILIES for kind in tv.ROW_KINDS
        }
        self.assertEqual({path.name for path in out.iterdir()},
                         expected_files | {tv.SUMMARY_FILENAME})
        for name, entry in summary["files"].items():
            self.assertEqual(hashlib.sha256((out / name).read_bytes()).hexdigest(),
                             entry["sha256"])
        accepted, rejected = records(tv.STATUS_ACCEPTED), records("rejected")
        self.assertEqual(summary["totals"]["rows"], len(accepted))
        self.assertEqual(sorted(entry["id"] for entry in summary["refused"]),
                         sorted(record["id"] for record in rejected))
        self.assertEqual({entry["code"] for entry in summary["refused"]},
                         {tv.FINDING_RECORD_NOT_A_POSITIVE_EXAMPLE})
        for family in tv.FAMILIES:
            lines = (out / f"{family}.sft.jsonl").read_text(encoding="utf-8").splitlines()
            wanted = [views.sft_row(r) for r in accepted if r["family"] == family]
            self.assertEqual([json.loads(line) for line in lines], wanted)
        before = {path.name: path.read_bytes() for path in out.iterdir()}
        status, _, stderr = invoke([_STATE["run_dir"], "--out", out])
        self.assertEqual(status, cli.EXIT_REFUSED)
        self.assertIn(tv.FINDING_DESTINATION_EXISTS, stderr)
        self.assertEqual({path.name: path.read_bytes() for path in out.iterdir()}, before)

    def test_refuses_a_raw_tree_destination(self):
        out = self.root / "outputs" / "raw" / "views"
        status, stdout, _ = invoke([_STATE["run_dir"], "--out", out, "--json"])
        self.assertEqual(status, cli.EXIT_REFUSED)
        self.assertEqual(json.loads(stdout)["refusal"]["code"], tv.FINDING_DESTINATION_UNDER_RAW)
        self.assertFalse((self.root / "outputs").exists())

    def test_refuses_a_destination_inside_the_run(self):
        out = _STATE["run_dir"] / "views"
        status, _, stderr = invoke([_STATE["run_dir"], "--out", out])
        self.assertEqual((status, stderr.split(": ")[1]),
                         (cli.EXIT_REFUSED, tv.FINDING_DESTINATION_INSIDE_RUN))
        self.assertFalse(out.exists())

    def test_refuses_a_missing_or_unauthenticated_run(self):
        status, _, stderr = invoke([self.root / "absent", "--out", self.root / "a"])
        self.assertEqual((status, stderr.split(": ")[1]),
                         (cli.EXIT_REFUSED, tv.FINDING_RUN_DIR_MISSING))
        tampered = self.root / "tampered"
        shutil.copytree(_STATE["run_dir"], tampered)
        target = next(tampered.glob(f"{tv.NEURON_FAMILY}/accepted-*.jsonl"))
        target.write_text(target.read_text().replace("_firing", "_firing "), encoding="utf-8")
        status, _, stderr = invoke([tampered, "--out", self.root / "b"])
        self.assertEqual((status, stderr.split(": ")[1]),
                         (cli.EXIT_REFUSED, tv.FINDING_RUN_NOT_AUTHENTICATED))
        self.assertFalse((self.root / "a").exists() or (self.root / "b").exists())

    def test_a_leak_finding_exits_one_and_writes_nothing(self):
        rows_of = cli._rows_of

        def leaky(record):
            return {kind: {**row, "id": record["id"]} for kind, row in rows_of(record).items()}

        out = self.root / "views"
        with mock.patch.object(cli, "_rows_of", leaky):
            status, _, stderr = invoke([_STATE["run_dir"], "--out", out])
        self.assertEqual(status, cli.EXIT_FINDINGS)
        self.assertIn(tv.LEAK_VIEW_EXTRA_KEYS, stderr)
        self.assertFalse(out.exists())

    def test_the_script_runs_directly(self):
        out = self.root / "direct"
        done = subprocess.run(  # nosec B603 -- fixed interpreter and script, explicit argv
            [sys.executable, str(CLI_SCRIPT), str(_STATE["run_dir"]), "--out", str(out)],
            capture_output=True, text=True, check=False, cwd=str(REPO),
        )
        self.assertEqual(done.returncode, cli.EXIT_OK, done.stderr)
        self.assertTrue((out / tv.SUMMARY_FILENAME).is_file())


if __name__ == "__main__":
    unittest.main()
