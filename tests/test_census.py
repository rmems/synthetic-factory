#!/usr/bin/env python3
"""census.py prints a read-only JSON census of a run directory."""

import json
import subprocess
import sys
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
CENSUS = REPO / "pipelines" / "census.py"
MINI_RUN = REPO / "tests" / "fixtures" / "mini-run"

EXPECTED = {
    "files": 2,
    "records": 3,
    "parse_failures": 1,
    "by_kind": {
        "thalamic": 2,
        "preference": 1,
        "bridge_pair": 0,
        "multi_agent": 0,
        "safety_case": 0,
        "episode": 0,
        "unknown": 0,
    },
    "sim_or_real": {
        "real": 1,
        "real*": 1,
        "sim*": 1,
        "hil*": 0,
        "other": 0,
        "<missing>": 0,
    },
    "by_factory": {
        "failure-as-fuel-preference-cascade": 1,
        "thalamic-trajectory-factory": 2,
    },
}


def _snapshot(root: Path):
    out = {}
    for path in sorted(root.rglob("*")):
        if path.is_file():
            st = path.stat()
            out[str(path.relative_to(root))] = (st.st_mtime_ns, st.st_size)
    return out


def _invoke(*args):
    return subprocess.run(
        [sys.executable, str(CENSUS), *args],
        capture_output=True,
        text=True,
        check=False,
    )


class CensusMiniRun(unittest.TestCase):
    def test_fixture_counts_and_histogram(self):
        result = _invoke(str(MINI_RUN))
        self.assertEqual(result.returncode, 0, result.stderr)
        report = json.loads(result.stdout)
        for key, value in EXPECTED.items():
            self.assertEqual(report[key], value, key)
        self.assertEqual(Path(report["run_dir"]).resolve(), MINI_RUN.resolve())

    def test_does_not_write_into_run_dir(self):
        before = _snapshot(MINI_RUN)
        result = _invoke(str(MINI_RUN))
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(_snapshot(MINI_RUN), before)
        self.assertFalse((MINI_RUN / "manifest.json").exists())


class CensusBuckets(unittest.TestCase):
    def setUp(self):
        sys.path.insert(0, str(REPO / "pipelines"))
        import census  # noqa: E402

        self.census = census

    def tearDown(self):
        sys.path[:] = [p for p in sys.path if p != str(REPO / "pipelines")]
        sys.modules.pop("census", None)

    def test_kind_routing(self):
        six = {
            "state": {},
            "proposed_action": {},
            "safety_decision": {},
            "executed_action": {},
            "future_outcome": {},
            "reward_components": {},
        }
        self.assertEqual(self.census.classify_kind(six), "thalamic")
        self.assertEqual(
            self.census.classify_kind({"chosen": {}, "rejected": {}}),
            "preference",
        )
        self.assertEqual(
            self.census.classify_kind({"language_view": {}, "spike_events": []}),
            "bridge_pair",
        )
        self.assertEqual(
            self.census.classify_kind({"agents": [], "transcript": []}),
            "multi_agent",
        )
        self.assertEqual(self.census.classify_kind({"case_type": "correct_refusal"}), "safety_case")
        self.assertEqual(
            self.census.classify_kind({"goal": "x", "steps": []}),
            "episode",
        )
        self.assertEqual(self.census.classify_kind({"meta": {}}), "unknown")

    def test_sim_or_real_buckets(self):
        bucket = self.census.bucket_sim_or_real
        self.assertEqual(bucket("real"), "real")
        self.assertEqual(bucket("real (production, actions live)"), "real*")
        self.assertEqual(bucket("live allocation; arbiter writes schedules"), "real*")
        self.assertEqual(
            bucket("high-fidelity plant simulation calibrated on telemetry"),
            "sim*",
        )
        self.assertEqual(
            bucket("hardware-in-the-loop (flight SPAD array)"),
            "hil*",
        )
        self.assertEqual(bucket("hil-rig-3"), "hil*")
        self.assertEqual(
            bucket(
                "operations-grade simulation calibrated on HIL valve testbench"
            ),
            "sim*",
        )
        self.assertEqual(
            bucket(
                "decision-support in live IOC; the relay's disposition drives recovery"
            ),
            "other",
        )


if __name__ == "__main__":
    unittest.main()
