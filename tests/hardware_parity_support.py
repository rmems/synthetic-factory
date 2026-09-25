#!/usr/bin/env python3
"""Shared fixtures and CLI helper for the hardware-parity test modules.

`tests/test_hardware_parity*.py` were one 1836-line module; they now split by
responsibility (generation, validation gates, captured-evidence provenance)
and share the committed parity-run fixture and the CLI shim from here.
"""

import collections
import contextlib
import copy
import io
import json
import sys
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
PIPELINES = REPO / "pipelines"
FIXTURE = (
    REPO
    / "tests"
    / "fixtures"
    / "parity-run"
    / "hardware-parity-spike-trajectories"
    / "batch-r01.jsonl"
)
sys.path.insert(0, str(PIPELINES))

WHERE = "unit:1"

CliResult = collections.namedtuple("CliResult", ("returncode", "stdout", "stderr"))


def fixture_records():
    return [
        json.loads(line)
        # Only LF frames a record, matching hp.read_jsonl: str.splitlines()
        # would also split on U+2028/U+2029.
        for line in FIXTURE.read_text(encoding="utf-8").split("\n")
        if line.strip()
    ]


import hardware_parity as hp  # noqa: E402
import hardware_parity_cli  # noqa: E402
import neuro_oracle as oracle  # noqa: E402


def cli(args):
    """Drive the hardware-parity CLI in-process; return its code and streams."""
    stdout, stderr = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
        try:
            code = hardware_parity_cli.main(list(args))
        except SystemExit as exc:  # argparse reports usage errors via sys.exit
            code = exc.code if isinstance(exc.code, int) else 2
    return CliResult(code, stdout.getvalue(), stderr.getvalue())

CAPTURE_MUTATIONS = (
    "bitstream_sha256",
    "truncate_spikes",
    "narrow_spikes",
    "invalid_spike_cell",
    "narrow_membrane",
)


def _mutated_spikes(software, mutations):
    """The reference spike grid, optionally damaged to exercise a rejection."""
    spikes = copy.deepcopy(software["spikes"])
    if mutations.get("truncate_spikes"):
        spikes = spikes[:-1]
    if mutations.get("narrow_spikes"):
        spikes = [row[:-1] for row in spikes]
    invalid_cell = mutations.get("invalid_spike_cell")
    if invalid_cell is not None:
        spikes[0][0] = invalid_cell
    return spikes


def _mutated_membrane(software, mutations):
    """The reference membrane trace, optionally narrowed."""
    membrane = copy.deepcopy(software["membrane"])
    if mutations.get("narrow_membrane"):
        membrane["trace"] = [row[:-1] for row in membrane["trace"]]
    return membrane


def _capture_payload(scenario, spikes, membrane):
    """A capture payload plus the retained repeats and their digests."""
    payload = {
        "spikes": spikes,
        "spike_events": oracle._spike_events(
            spikes, scenario["model_float"]["dt_ms"]
        ),
        "action": oracle._decode_action(
            spikes, scenario["model_float"]["action_labels"]
        ),
        "membrane": membrane,
        "arithmetic": {"format": "Q8.8", "saturation_events": 0},
        "latency": {"measured": True, "value_ms": 0.31},
    }
    repeat_output = {
        key: copy.deepcopy(payload[key])
        for key in (
            "spikes",
            "spike_events",
            "action",
            "membrane",
            "arithmetic",
        )
    }
    payload["repeat_outputs"] = [copy.deepcopy(repeat_output) for _ in range(3)]
    payload["repeat_digests"] = [
        oracle.run_digest(repeat) for repeat in payload["repeat_outputs"]
    ]
    return payload


class CaptureCase(unittest.TestCase):
    """Shared `capture` builders: one recorded capture plus a case that
    exercises a mutation and requires its specific refusal diagnostic."""

    def _capture_adapter(self, tmp, scenario, **mutations):
        unknown = set(mutations) - set(CAPTURE_MUTATIONS)
        if unknown:
            raise TypeError(f"unknown capture mutations: {sorted(unknown)}")
        software = oracle.simulate_float(
            scenario["model_float"], scenario["stimulus"]
        )
        _, quantization = oracle.quantize_model(scenario["model_float"])
        payload = _capture_payload(
            scenario,
            _mutated_spikes(software, mutations),
            _mutated_membrane(software, mutations),
        )
        capture = {
            "execution_target": oracle.TARGET_FPGA_HARDWARE,
            "quantization": quantization,
            "hardware": {"revision": "rev-b", "board_serial": "SN-9"},
            "bitstream": {
                "sha256": mutations.get("bitstream_sha256") or "sha256:" + "b" * 64,
                "toolchain": "vendor 1.2",
            },
            "manifest": {
                "payload_sha256": oracle.digest(payload),
                "input_fixture_sha256": scenario["input_fixture"]["sha256"],
                "recorded_at": "2026-01-01T00:00:00Z",
            },
            "payload": payload,
        }
        path = Path(tmp) / "capture.json"
        path.write_text(json.dumps(capture), encoding="utf-8")
        return oracle.RecordedCaptureAdapter(path)

    def _record(self, tmp, **capture_kwargs):
        scenario = hp.build_scenarios(steps=6)[0]
        return hp.generate_records(
            round_number=1,
            steps=6,
            deployment=(self._capture_adapter(tmp, scenario, **capture_kwargs), None),
            repeats=3,
        )[0]

    def _assert_capture_rejected(self, expected_fragments, mutate=None, **capture_kwargs):
        """Generate one isolated capture and require its specific refusal diagnostic."""
        with tempfile.TemporaryDirectory() as tmp:
            record = self._record(tmp, **capture_kwargs)
            if mutate is not None:
                mutate(record)
            errors = hp.validate_record(record, WHERE)
        self.assertTrue(
            any(all(fragment in error for fragment in expected_fragments) for error in errors),
            errors,
        )

    def _assert_relabelled_adapter_rejected(self, adapter, runtime_class, message):
        def relabel(record):
            record["oracle"]["deployment"].update(adapter=adapter, runtime_class=runtime_class)

        self._assert_capture_rejected((message,), relabel)

    def _assert_repeat_observation_is_bound(self, mutate_repeat):
        def mutate(record):
            capture = record["oracle"]["deployment"]["capture"]
            source = capture["source"]
            payload = source["payload"]
            mutate_repeat(payload["repeat_outputs"][1])
            payload_sha = oracle.digest(payload)
            source["manifest"]["payload_sha256"] = payload_sha
            capture["payload_sha256"] = payload_sha
            capture["manifest_sha256"] = oracle.digest(source["manifest"])
            capture["source_sha256"] = oracle.digest(source)

        self._assert_capture_rejected(("repeat_digests[1] is not derived",), mutate)

    def _reseal_capture(self, record):
        """Refresh every digest that binds the capture source to the record."""
        deployment = record["oracle"]["deployment"]
        capture = deployment["capture"]
        source = capture["source"]
        payload = source["payload"]
        payload_sha = oracle.digest(payload)
        source["manifest"]["payload_sha256"] = payload_sha
        capture["payload_sha256"] = payload_sha
        capture["manifest_sha256"] = oracle.digest(source["manifest"])
        capture["source_sha256"] = oracle.digest(source)
        record["result"]["derived_from"][-1] = hp._capture_evidence_digest(deployment)
        return record

    def _with_q88_raw(self, record, raw_value):
        deployment = record["oracle"]["deployment"]
        payload = deployment["capture"]["source"]["payload"]

        def stamp(membrane):
            raw = [
                [int(round(cell * oracle.Q88_SCALE)) for cell in row]
                for row in membrane["trace"]
            ]
            raw[0][0] = raw_value
            membrane["trace_q88_raw"] = raw

        stamp(payload["membrane"])
        for repeat in payload["repeat_outputs"]:
            stamp(repeat["membrane"])
        stamp(deployment["membrane"])
        payload["repeat_digests"] = [
            oracle.run_digest(repeat) for repeat in payload["repeat_outputs"]
        ]
        payload_sha = oracle.digest(payload)
        source = deployment["capture"]["source"]
        source["manifest"]["payload_sha256"] = payload_sha
        deployment["capture"]["payload_sha256"] = payload_sha
        deployment["capture"]["manifest_sha256"] = oracle.digest(source["manifest"])
        deployment["capture"]["source_sha256"] = oracle.digest(source)
        deployment["output_digest"] = oracle.run_digest(payload)
        deployment["repeat_digests"] = list(payload["repeat_digests"])
        return record
