"""Pin the db mill's publish loop, CLI dispatch and self-check refusals.

``run_loop`` publishes through ``round_txn``; these tests replace that module
with an in-memory fake (nothing is reserved, staged or written under
``outputs/raw/``) and record the call sequence, hops and printed JSON so the
loop's branch order stays exactly as it is on main.
"""

from __future__ import annotations

import contextlib
import importlib.machinery
import importlib.util
import io
import json
import sys
import tempfile
import types
import unittest
from pathlib import Path
from unittest import mock

REPO = Path(__file__).resolve().parents[1]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from pipelines.db import check, cli
from pipelines.db import config as cfg
from pipelines.db.episode import build_episode
from pipelines.db.plants import PLANTS


class _OptimizedSourceLoader(importlib.machinery.SourceFileLoader):
    """Compile a module the way ``python -O`` does (asserts stripped), skipping cached bytecode."""

    def get_code(self, fullname):
        return compile(self.get_data(self.path), self.path, "exec", dont_inherit=True, optimize=1)


def _optimized_check_module() -> types.ModuleType:
    """A fresh copy of ``pipelines.db.check`` compiled with ``optimize=1``."""
    name = "pipelines.db._check_optimized"
    loader = _OptimizedSourceLoader(name, check.__file__)
    spec = importlib.util.spec_from_loader(name, loader, origin=check.__file__)
    module = importlib.util.module_from_spec(spec)
    with mock.patch.dict(sys.modules, {name: module}):
        loader.exec_module(module)
    return module


class _TransactionError(Exception):
    pass


class _FakeTxn:
    """Scripted stand-in for ``round_txn``: frontier rounds, reserve/publish errors."""

    def __init__(self, frontier, *, reserve_errors=None, publish_error=None, abort_error=None):
        self.frontier = list(frontier)
        self.reserve_errors = dict(reserve_errors or {})
        self.publish_error = publish_error
        self.abort_error = abort_error
        self.calls: list[tuple] = []
        self._frontier_i = 0
        self._reserve_i = 0

    def module(self) -> types.ModuleType:
        mod = types.ModuleType("pipelines.round_txn")
        mod.TransactionError = _TransactionError
        mod.frontier_status = self.frontier_status
        mod.reserve = self.reserve
        mod.publish = self.publish
        mod.abort = self.abort
        return mod

    def frontier_status(self, factory):
        self.calls.append(("frontier", Path(factory).name))
        rnd = self.frontier[min(self._frontier_i, len(self.frontier) - 1)]
        self._frontier_i += 1
        return {"next_round": rnd}

    def reserve(self, factory, rnd, expected):
        self.calls.append(("reserve", rnd, expected))
        attempt = self._reserve_i
        self._reserve_i += 1
        if attempt in self.reserve_errors:
            raise _TransactionError(self.reserve_errors[attempt])
        return {"staging_dir": f"/nonexistent/stage-{rnd}", "token": f"tok{rnd}"}

    def publish(self, factory, rnd, token):
        self.calls.append(("publish", rnd, token))
        if self.publish_error:
            raise ValueError(self.publish_error)
        return {"records": 2}

    def abort(self, factory, rnd, token):
        self.calls.append(("abort", rnd, token))
        if self.abort_error:
            raise OSError(self.abort_error)


def _run_loop(txn, *args, reserved_once=(), **kwargs):
    """Run ``cli.run_loop`` against ``txn``; return (result, stdout lines, emitted rounds)."""
    emitted: list[int] = []
    seen: set[int] = set()
    real_exists = Path.exists

    def exists(path, *a, **k):
        if path.name.endswith(".reserved.json"):
            rnd = int(path.name.split("-r")[1].split(".")[0])
            first = rnd not in seen
            seen.add(rnd)
            return rnd in reserved_once and first
        return real_exists(path, *a, **k)

    def emit(stage, rnd):
        emitted.append(rnd)
        return (f"dbm-r{rnd}-a", f"dbm-r{rnd}-b")

    out = io.StringIO()
    with (
        mock.patch.dict(sys.modules, {"pipelines.round_txn": txn.module()}),
        mock.patch.object(Path, "exists", autospec=True, side_effect=exists),
        mock.patch.object(cli, "emit_stage", side_effect=emit),
        mock.patch.object(cli.time, "sleep"),
        contextlib.redirect_stdout(out),
    ):
        result = cli.run_loop(*args, **kwargs)
    return result, out.getvalue().splitlines(), emitted


class RunLoopTests(unittest.TestCase):
    def test_publishes_until_max_rounds_and_reports_each_round(self):
        txn = _FakeTxn([845, 846, 847])
        result, lines, emitted = _run_loop(txn, 1, 2)
        self.assertEqual(result, 0)
        self.assertEqual(emitted, [845, 846])
        self.assertEqual(
            [json.loads(line) for line in lines],
            [
                {"published": {"round": 845, "ids": ["dbm-r845-a", "dbm-r845-b"], "records": 2}},
                {"published": {"round": 846, "ids": ["dbm-r846-a", "dbm-r846-b"], "records": 2}},
                {"published_rounds": [845, 846], "hops": []},
            ],
        )
        self.assertEqual(
            [call[0] for call in txn.calls],
            ["frontier", "reserve", "publish", "frontier", "reserve", "publish"],
        )
        self.assertEqual(txn.calls[0], ("frontier", "db-migration-repair-factory"))
        self.assertEqual(txn.calls[1], ("reserve", 845, 2))

    def test_reserved_round_hops_before_reserving(self):
        txn = _FakeTxn([845, 845])
        result, lines, _ = _run_loop(txn, 1, 1, reserved_once=(845,))
        self.assertEqual(result, 0)
        hop = {"dbm_next": 845, "dbm_reserved": True, "action": "HOP", "stolen": False}
        self.assertEqual(json.loads(lines[0]), {"hop": hop})
        self.assertEqual(json.loads(lines[-1]), {"published_rounds": [845], "hops": [hop]})
        self.assertEqual([call[0] for call in txn.calls], ["frontier", "frontier", "reserve", "publish"])

    def test_lost_reservation_races_hop_and_retry(self):
        for message in ("batch path already exists: x", "round r845 is not the frontier; expected r846"):
            with self.subTest(message=message):
                txn = _FakeTxn([845, 846], reserve_errors={0: message})
                result, lines, emitted = _run_loop(txn, 1, 1)
                self.assertEqual(result, 0)
                self.assertEqual(emitted, [846])
                self.assertEqual(lines[0], f"reserve failed r845: {message}")
                hop = {"dbm_next": 845, "error": message, "stolen": False, "action": "HOP"}
                self.assertEqual(json.loads(lines[1]), {"hop": hop})
                self.assertEqual(json.loads(lines[-1]), {"published_rounds": [846], "hops": [hop]})

    def test_other_reserve_errors_propagate_unchanged(self):
        txn = _FakeTxn([845], reserve_errors={0: "disk gone"})
        with self.assertRaises(_TransactionError) as caught:
            _run_loop(txn, 1, 2)
        self.assertEqual(str(caught.exception), "disk gone")
        self.assertEqual([call[0] for call in txn.calls], ["frontier", "reserve"])

    def test_publish_failure_aborts_the_reservation_and_chains(self):
        txn = _FakeTxn([845], publish_error="boom")
        with self.assertRaises(RuntimeError) as caught:
            _run_loop(txn, 1, 2)
        self.assertEqual(str(caught.exception), "stage/publish failed r845: boom")
        self.assertIsInstance(caught.exception.__cause__, ValueError)
        self.assertEqual(txn.calls[-1], ("abort", 845, "tok845"))

    def test_abort_failure_is_reported_and_the_publish_error_still_raises(self):
        txn = _FakeTxn([845], publish_error="boom", abort_error="nope")
        out = io.StringIO()
        with contextlib.redirect_stdout(out), self.assertRaises(RuntimeError):
            _run_loop(txn, 1, 2)
        self.assertEqual(txn.calls[-1], ("abort", 845, "tok845"))

    def test_round_outside_the_catalog_stops_the_loop(self):
        for rnd in (cfg.START_ROUND - 1, 10_000):
            with self.subTest(round=rnd):
                txn = _FakeTxn([rnd])
                result, lines, emitted = _run_loop(txn, 1, 2)
                self.assertEqual(result, 1)
                self.assertEqual(emitted, [])
                self.assertTrue(lines[0].startswith("STOP: "))
                self.assertEqual(json.loads(lines[-1]), {"published_rounds": [], "hops": []})

    def test_deadline_after_min_rounds_and_zero_max_publish_nothing(self):
        for args, kwargs in (((0, 3), {"minutes": -1.0}), ((0, 0), {})):
            with self.subTest(args=args):
                txn = _FakeTxn([845])
                result, lines, _ = _run_loop(txn, *args, **kwargs)
                self.assertEqual(result, 1)
                self.assertEqual(txn.calls, [])
                self.assertEqual(json.loads(lines[-1]), {"published_rounds": [], "hops": []})


class MainDispatchTests(unittest.TestCase):
    def test_loop_reads_optional_min_and_max_rounds(self):
        cases = (
            (["loop"], {"min_rounds": cfg.MIN_ROUNDS, "max_rounds": cfg.MAX_ROUNDS}),
            (["loop", "3"], {"min_rounds": 3, "max_rounds": cfg.MAX_ROUNDS}),
            (["loop", "3", "5"], {"min_rounds": 3, "max_rounds": 5}),
        )
        for argv, expected in cases:
            with self.subTest(argv=argv):
                with mock.patch.object(cli, "self_check") as checked, mock.patch.object(
                    cli, "run_loop", return_value=7
                ) as loop:
                    self.assertEqual(cli.main(argv), 7)
                checked.assert_called_once_with()
                loop.assert_called_once_with(**expected)

    def test_check_smoke_and_emit_write_only_to_fresh_directories(self):
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            self.assertEqual(cli.main(["check"]), 0)
            self.assertEqual(cli.main(["--smoke"]), 0)
        lines = out.getvalue().splitlines()
        self.assertTrue(lines[0].startswith("self_check ok: 44 pairs"))
        smoke = json.loads(lines[-1])
        self.assertEqual(len(smoke["smoke_ids"]), 2)
        with tempfile.TemporaryDirectory(prefix="dbm-emit-") as td:
            dest = Path(td) / "nested"
            out = io.StringIO()
            with contextlib.redirect_stdout(out):
                self.assertEqual(cli.main(["emit", str(cfg.START_ROUND), str(dest)]), 0)
            self.assertEqual(json.loads(out.getvalue())["ids"], smoke["smoke_ids"])
            self.assertTrue((dest / f"batch-r{cfg.START_ROUND:02d}.jsonl").is_file())

    def test_unknown_command_exits_with_usage(self):
        with self.assertRaises(SystemExit) as caught:
            cli.main(["bogus"])
        self.assertEqual(str(caught.exception), "usage: db.cli [check|--smoke|emit N DIR|loop [min] [max]]")


class SelfCheckRefusalTests(unittest.TestCase):
    @staticmethod
    def _self_check(plants):
        with mock.patch.object(check, "PLANTS", plants), contextlib.redirect_stdout(io.StringIO()):
            check.self_check()

    def test_banned_fragment_and_recycle_suffix_slugs_are_refused(self):
        fragment = cfg.BANNED_FRAGMENTS[0]
        with self.assertRaisesRegex(ValueError, f"^banned fragment {fragment} in x-{fragment}$"):
            self._self_check([dict(PLANTS[0], slug=f"x-{fragment}")])
        with self.assertRaisesRegex(ValueError, "^recycle suffix slug x-r12$"):
            self._self_check([dict(PLANTS[0], slug="x-r12")])

    def test_duplicates_are_refused_in_column_order(self):
        with self.assertRaisesRegex(ValueError, "^duplicate slugs$"):
            self._self_check([PLANTS[0], PLANTS[0]])
        with self.assertRaisesRegex(ValueError, "^duplicate surfaces$"):
            self._self_check([PLANTS[0], dict(PLANTS[1], surface=PLANTS[0]["surface"])])

    def test_odd_plant_count_is_refused_after_duplicate_checks(self):
        with self.assertRaisesRegex(ValueError, "^odd plant count$"):
            self._self_check(PLANTS[:3])

    def test_each_built_pair_invariant_fails_the_self_check(self):
        good_a, good_b, good_notes = check.build_pair(cfg.START_ROUND)
        broken = (
            {"reward": dict(good_a["reward"], success=False)},
            {"reward": dict(good_a["reward"], apply_fails=1)},
            {"reward": dict(good_a["reward"], plan_changes=0)},
            {"reward": dict(good_a["reward"], lock_timeouts=2)},
            {"steps": good_a["steps"][:-1]},
            {"meta": dict(good_a["meta"], generator="other")},
            {"meta": dict(good_a["meta"], sim_or_real="real")},
            {"id": good_a["id"] + "-r12"},
        )
        for override in broken:
            with self.subTest(override=sorted(override)):
                pair = (good_a, dict(good_b, **override), good_notes)
                with (
                    mock.patch.object(check, "build_pair", return_value=pair),
                    self.assertRaises(AssertionError) as caught,
                ):
                    self._self_check(PLANTS[:2])
                self.assertEqual(caught.exception.args, ())
        for notes in ("Novel coverage: 1%", "# NOTES-r845 without coverage"):
            with self.subTest(notes=notes):
                pair = (good_a, good_b, notes)
                with (
                    mock.patch.object(check, "build_pair", return_value=pair),
                    self.assertRaises(AssertionError),
                ):
                    self._self_check(PLANTS[:2])

    def test_built_pair_invariants_still_fail_under_python_optimize(self):
        optimized = _optimized_check_module()
        good_a, good_b, good_notes = check.build_pair(cfg.START_ROUND)
        pair = (good_a, dict(good_b, steps=[]), good_notes)
        with (
            mock.patch.object(optimized, "PLANTS", PLANTS[:2]),
            mock.patch.object(optimized, "build_pair", return_value=pair),
            contextlib.redirect_stdout(io.StringIO()),
            self.assertRaises(AssertionError),
        ):
            optimized.self_check()

    def test_recycle_suffix_in_an_episode_id_is_refused(self):
        with self.assertRaisesRegex(ValueError, "^recycle suffix in id: dbm-r845-x-r12$"):
            build_episode(cfg.START_ROUND, dict(PLANTS[0], slug="x-r12"), 0)


if __name__ == "__main__":
    unittest.main()
