"""Pin the cer burst-mill runner and the burst plan's refusal order.

``publish_burst_mill`` drives ``round_txn`` through a subprocess; these tests
replace that call with a scripted fake and point the repository root at a
temporary directory, so staging happens in a scratch tree and nothing is
reserved or written under the real ``outputs/raw/``.
"""

from __future__ import annotations

import contextlib
import copy
import io
import json
import sys
import tempfile
import types
import unittest
from pathlib import Path
from unittest import mock

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "pipelines"))

from cer import cli as cer_cli
from cer import mill_runner as mr
from cer import plants_r1901
from cer import record_builder as rb
from cer import usage_burst_plan as ubp
from cer import vocabulary as cv

_CALLER_STAGE = "abc"
_UNSTAGED = "zzz"
_PLAN = json.loads((REPO / cv.DEFAULT_PLAN_PATH).read_text(encoding="utf-8"))


class _Txn:
    """Scripted ``round_txn`` CLI: frontier rounds, staging dirs under ``root``."""

    def __init__(self, root: Path, frontier, *, make_stage=True):
        self.root = root
        self.frontier = list(frontier)
        self.make_stage = make_stage
        self.calls: list[tuple[str, ...]] = []
        self._i = 0

    def __call__(self, *args: str) -> dict:
        self.calls.append(args)
        if args[0] == "frontier":
            rnd = self.frontier[min(self._i, len(self.frontier) - 1)]
            self._i += 1
            return {"next_round": str(rnd)}
        if args[0] == "reserve":
            stage = self.root / f"stage-{args[3]}"
            if self.make_stage:
                stage.mkdir()
            return {"token": f"tok{args[3]}", "staging_dir": str(stage)}
        return {"published": args[3]}


class PublishBurstMillTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory(prefix="cer-runner-")
        self.root = Path(self._tmp.name)
        self.reserved_once: set[int] = set()
        seen: set[int] = set()
        real_exists = Path.exists

        def exists(path, *a, **k):
            if path.name.endswith(".reserved.json"):
                rnd = int(path.name.split("-r")[1].split(".")[0])
                first = rnd not in seen
                seen.add(rnd)
                return rnd in self.reserved_once and first
            return real_exists(path, *a, **k)

        for patcher in (
            mock.patch.object(mr, "_repo_root", return_value=self.root),
            mock.patch.object(mr.time, "sleep"),
            mock.patch.object(Path, "exists", autospec=True, side_effect=exists),
        ):
            patcher.start()
            self.addCleanup(patcher.stop)
        self.addCleanup(self._tmp.cleanup)

    @staticmethod
    def _publish(txn, **kwargs):
        with mock.patch.object(mr, "_txn", txn):
            return mr.publish_burst_mill("cer_r1901", run_label="lbl", **kwargs)

    def test_publishes_every_pair_through_reserve_stage_publish(self):
        txn = _Txn(self.root, range(1901, 1917))
        published = self._publish(txn)
        self.assertEqual([item["round"] for item in published], list(range(1901, 1917)))
        factory = str(self.root / "outputs/raw" / "lbl" / cv.FACTORY)
        self.assertEqual(txn.calls[0], ("frontier", factory))
        self.assertEqual(
            txn.calls[1], ("reserve", factory, "--round", "1901", "--expected", str(cv.QUOTA_PER_ROUND))
        )
        self.assertEqual(txn.calls[2], ("publish", factory, "--round", "1901", "--token", "tok1901"))
        okp, badp = plants_r1901.PAIRS[0]
        rec_a, rec_b = rb.episode(1901, okp), rb.episode(1901, badp)
        stage = self.root / "stage-1901"
        self.assertEqual(
            (stage / "batch-r1901.jsonl").read_text(),
            json.dumps(rec_a, separators=(",", ":")) + "\n" + json.dumps(rec_b, separators=(",", ":")) + "\n",
        )
        self.assertEqual(
            (stage / "NOTES-r1901.md").read_text(),
            rb.notes_markdown(1901, rec_a, rec_b, ok_slug=okp["slug"], fail_slug=badp["slug"]),
        )
        self.assertEqual(published[0], {"round": 1901, "ids": [rec_a["id"], rec_b["id"]], "publish": {"published": "1901"}})

    def test_reserved_round_waits_and_rereads_the_frontier(self):
        self.reserved_once = {1901}
        txn = _Txn(self.root, [1901] + list(range(1901, 1917)))
        published = self._publish(txn)
        self.assertEqual(len(published), plants_r1901.N_ROUNDS)
        self.assertEqual([call[0] for call in txn.calls[:3]], ["frontier", "frontier", "reserve"])
        mr.time.sleep.assert_any_call(0.25)

    def test_caller_token_reuses_its_existing_staging_directory(self):
        stage = self.root / "outputs/staging" / "lbl" / cv.FACTORY / f"r1901-{_CALLER_STAGE}"
        stage.mkdir(parents=True)
        txn = _Txn(self.root, range(1901, 1917))
        self._publish(txn, first_token=_CALLER_STAGE)
        self.assertEqual([call[0] for call in txn.calls[:2]], ["frontier", "publish"])
        self.assertEqual(txn.calls[1][-1], _CALLER_STAGE)
        self.assertTrue((stage / "batch-r1901.jsonl").is_file())
        self.assertEqual(txn.calls[3][0], "reserve")

    def test_caller_token_without_staging_directory_is_refused(self):
        txn = _Txn(self.root, [1901])
        with self.assertRaises(FileNotFoundError) as caught:
            self._publish(txn, first_token=_UNSTAGED)
        self.assertEqual(
            Path(str(caught.exception)), self.root / "outputs/staging" / "lbl" / cv.FACTORY / f"r1901-{_UNSTAGED}"
        )
        self.assertEqual([call[0] for call in txn.calls], ["frontier"])

    def test_gives_up_after_max_reserve_tries(self):
        self.reserved_once = {1901}
        txn = _Txn(self.root, [1901])
        with self.assertRaisesRegex(RuntimeError, "^gave up after 1 reserve tries, published 0$"):
            self._publish(txn, max_reserve_tries=1)

    def test_staging_failure_after_reserve_raises_without_publish_or_abort(self):
        # Behaviour on main: the runner never aborts a reservation it made.
        txn = _Txn(self.root, [1901], make_stage=False)
        with self.assertRaises(FileNotFoundError):
            self._publish(txn)
        self.assertEqual([call[0] for call in txn.calls], ["frontier", "reserve"])

    def test_unknown_mill_is_refused(self):
        with self.assertRaisesRegex(KeyError, "unknown cer burst mill 'nope'"):
            mr.publish_burst_mill("nope")


class BurstPlanRefusalTests(unittest.TestCase):
    @staticmethod
    def _load(plan, **kwargs):
        with tempfile.TemporaryDirectory(prefix="cer-plan-") as td:
            path = Path(td) / "plan.json"
            path.write_text(json.dumps(plan), encoding="utf-8")
            return ubp.load_mill_usage_burst_plan(path, repo_root=REPO, **kwargs)

    @staticmethod
    def _variant(mutate):
        plan = copy.deepcopy(_PLAN)
        mutate(plan)
        return plan

    def test_header_quota_mills_and_totals_refuse_in_order(self):
        cases = (
            (lambda p: p.update(schema_id="x", factory="y"), "schema_id must be"),
            (lambda p: p.update(family_prefix="x"), "family_prefix must be"),
            (lambda p: p.update(factory="x"), "factory must be"),
            (lambda p: p.update(slice="B"), "slice must be"),
            (lambda p: p.update(quota_per_round=True), "quota_per_round must be an integer, got True"),
            (lambda p: p.update(quota_per_round=3, mills=[]), "quota_per_round must be 2"),
            (lambda p: p.update(mills={}), "mills must be a non-empty list"),
            (lambda p: p.update(mills=[]), "mills must be a non-empty list"),
            (lambda p: p.update(label="", totals={"mills": 9}), "label must be a non-empty string"),
            (lambda p: p["totals"].update(rounds=1), "totals.rounds is 1, expected 32"),
        )
        for mutate, message in cases:
            with self.subTest(message=message), self.assertRaisesRegex(ubp.PlanValidationError, message):
                self._load(self._variant(mutate))

    def test_non_object_totals_are_not_compared(self):
        plan = self._load(self._variant(lambda p: p.update(totals=[1])))
        self.assertEqual(plan.counts()["episodes"], 64)

    def test_plant_modules_are_cross_checked_per_mill(self):
        cases = (
            (lambda p: p["mills"][0].update(id="cer_r9999"), "cer_r9999: not registered in burst_registry"),
            (lambda p: p["mills"][1].update(plants_module="cer.plants_r1901"), "cer_r1958: module MILL_ID='cer_r1901'"),
            (lambda p: p["mills"][1].update(start_round=1958), "cer_r1958: module START=1966, plan expects 1958"),
            (
                lambda p: p["mills"][1].update(n_rounds=15, pair_count=15),
                "cer_r1958: module N_ROUNDS=16, plan expects 15",
            ),
        )
        for mutate, message in cases:
            with self.subTest(message=message):
                plan = self._variant(mutate)
                plan.pop("totals")
                with self.assertRaisesRegex(ubp.PlanValidationError, message):
                    self._load(plan)

    def test_missing_module_and_short_pairs_are_refused(self):
        plan = self._variant(lambda p: p["mills"][0].update(plants_module="cer.no_such_plants"))
        with self.assertRaisesRegex(ubp.PlanValidationError, "plants module 'cer.no_such_plants' not importable"):
            self._load(plan)
        short = types.ModuleType("cer_short_plants")
        short.MILL_ID, short.START, short.N_ROUNDS = "cer_r1901", 1901, 16
        short.PAIRS = plants_r1901.PAIRS[:3]
        plan = self._variant(lambda p: p["mills"][0].update(plants_module="cer_short_plants"))
        with (
            mock.patch.dict(sys.modules, {"cer_short_plants": short}),
            self.assertRaisesRegex(ubp.PlanValidationError, r"cer_r1901: len\(PAIRS\)=3, expected 16"),
        ):
            self._load(plan)
        self.assertEqual(self._load(plan, validate_plants=False).mills[0].plants_module, "cer_short_plants")


class PlanCliTests(unittest.TestCase):
    @staticmethod
    def _run(*argv: str) -> tuple[int, str]:
        printed = io.StringIO()
        with contextlib.redirect_stdout(printed):
            status = cer_cli.run(list(argv))
        return status, printed.getvalue()

    def test_plan_prints_counts_as_text_and_as_json(self):
        status, text = self._run("plan")
        self.assertEqual(status, 0)
        self.assertRegex(text, r"^slice \S+ .+: \d+ mills, \d+ rounds, \d+ episodes\n$")
        status, raw = self._run("plan", "--json")
        payload = json.loads(raw)
        self.assertEqual(status, 0)
        self.assertEqual(len(payload["mills"]), payload["counts"]["mills"])


if __name__ == "__main__":
    unittest.main()
