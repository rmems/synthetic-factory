#!/usr/bin/env python3
"""Tests for pipelines/promote.py."""

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
PIPELINES = REPO / "pipelines"
FIXTURES = Path(__file__).resolve().parent / "fixtures"
PROMOTER = PIPELINES / "promote.py"

sys.path.insert(0, str(PIPELINES))
import promote  # noqa: E402


CLAIMED_LIVE = "real (production \u2026 actions live)"


def _thalamic(sim_or_real=CLAIMED_LIVE, **overrides):
    rec = {
        "state": {"sim_or_real": sim_or_real, "domain": "test"},
        "proposed_action": {"action_type": "noop"},
        "safety_decision": {"decision": "ACCEPT", "rationale": "ok"},
        "executed_action": {"action_type": "noop"},
        "future_outcome": {"success": "full"},
        "reward_components": {"task_progress": 0.4, "safety": 0.6, "total": 1.0},
        "meta": {"id": "t-001"},
    }
    rec.update(overrides)
    return rec


def _write_jsonl(path, records):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in records))


def _snapshot(root):
    out = {}
    for path in sorted(Path(root).rglob("*")):
        if path.is_file():
            out[str(path.relative_to(root))] = path.read_bytes()
    return out


def _cli(args, cwd=None):
    return subprocess.run(
        [sys.executable, str(PROMOTER), *args],
        cwd=str(cwd or REPO),
        capture_output=True,
        text=True,
    )


def _units_migration():
    return {
        "standard": {"unit_usd": 10000, "since_round": 3},
        "records": [
            {
                "scope": "preferences.jsonl (round 1, 6 records: r1-1..r1-6)",
                "native_units": "UNITLESS / no USD anchor stated",
                "usd_conversion_factor": None,
                "recommendation": "NO reliable USD anchor exists. Do NOT magnitude-mix. Use SIGN/ORDER-only DPO.",
            },
            {
                "scope": "batch-r02.jsonl / ffpc-r2-001 (grid BESS dispatch)",
                "native_units": "1.0 = USD 2,000",
                "usd_conversion_factor": 0.2,
            },
            {
                "scope": "batch-r02.jsonl / ffpc-r2-002 (semiconductor fab dispatch)",
                "native_units": "1.0 = USD 20,000",
                "usd_conversion_factor": 2.0,
            },
            {
                "scope": "batch-r02.jsonl / ffpc-r2-003 (harbor tug berthing)",
                "native_units": "normalized berthing-episode scale",
                "usd_conversion_factor": None,
                "recommendation": "non-USD design-margin scale; exclude from USD-magnitude-weighted batches. Safe for sign/order-only DPO.",
            },
            {
                "scope": "batch-r03.jsonl (round 3) and batch-r04.jsonl (round 4)",
                "native_units": "1.0 = USD 10,000 (STANDARD)",
                "usd_conversion_factor": 1.0,
            },
        ],
    }


def _scale_entry(scale, factory, filename):
    """Accept nested {factory: {file: entry}} or a list of entries."""
    if isinstance(scale, dict) and factory in scale:
        bucket = scale[factory]
        if isinstance(bucket, dict) and filename in bucket:
            return bucket[filename]
        if isinstance(bucket, list):
            for item in bucket:
                if item.get("file") == filename:
                    return item
    if isinstance(scale, dict) and "files" in scale:
        for item in scale["files"]:
            if item.get("factory") == factory and item.get("file") == filename:
                return item
    if isinstance(scale, list):
        for item in scale:
            rel = item.get("file") or item.get("path") or ""
            if rel == filename or rel.endswith(f"{factory}/{filename}"):
                if item.get("factory") in (None, factory):
                    return item
    rel = f"{factory}/{filename}"
    if isinstance(scale, dict) and rel in scale:
        return scale[rel]
    raise AssertionError(f"no reward-scale entry for {factory}/{filename}: {scale!r}")


class TestRemapClaimed(unittest.TestCase):
    def test_production_actions_live_is_designed(self):
        prov = promote.remap_claimed(CLAIMED_LIVE)
        self.assertEqual(prov["kind"], "designed")
        self.assertEqual(prov["claimed"], CLAIMED_LIVE)

    def test_exact_real_is_designed(self):
        self.assertEqual(promote.remap_claimed("real")["kind"], "designed")
        self.assertEqual(promote.remap_claimed("REAL")["kind"], "designed")

    def test_live_prefix_is_designed(self):
        claimed = "live allocation; arbiter writes schedules"
        self.assertEqual(promote.remap_claimed(claimed)["kind"], "designed")
        self.assertEqual(promote.remap_claimed(claimed)["claimed"], claimed)

    def test_simulation_and_high_fidelity(self):
        hi = "high-fidelity plant simulation calibrated on telemetry"
        self.assertEqual(promote.remap_claimed(hi)["kind"], "simulated")
        self.assertEqual(
            promote.remap_claimed("operations-grade simulation calibrated on HIL valve")["kind"],
            "simulated",
        )

    def test_hil(self):
        self.assertEqual(
            promote.remap_claimed("hardware-in-the-loop (flight SPAD array)")["kind"],
            "hil",
        )
        self.assertEqual(promote.remap_claimed("hil-rig-3")["kind"], "hil")

    def test_missing_is_unknown_claimed_null(self):
        self.assertEqual(
            promote.remap_claimed(None),
            {"kind": "unknown", "claimed": None},
        )

    def test_unmatched_keeps_claimed(self):
        claimed = "decision-support in live IOC; the relay's disposition drives recovery"
        prov = promote.remap_claimed(claimed)
        self.assertEqual(prov["kind"], "unknown")

    def test_existing_provenance_still_strips_real_sim_or_real(self):
        rec = _thalamic()
        rec["provenance"] = {"kind": "designed", "claimed": "already stamped"}
        rec["state"]["sim_or_real"] = "real"
        out = promote.promote_record(rec)
        self.assertEqual(out["state"]["sim_or_real"], "designed")
        self.assertEqual(out["state"]["provenance"]["claimed"], "real")


class TestPromoteRecord(unittest.TestCase):
    def test_fixture_real_production_becomes_designed(self):
        rec = _thalamic()
        out = promote.promote_record(json.loads(json.dumps(rec)))
        self.assertEqual(out["provenance"]["kind"], "designed")
        self.assertEqual(out["provenance"]["claimed"], CLAIMED_LIVE)
        self.assertEqual(out["state"]["provenance"]["kind"], "designed")
        self.assertEqual(out["state"]["provenance"]["claimed"], CLAIMED_LIVE)
        self.assertEqual(out["state"]["sim_or_real"], "designed")
        self.assertNotEqual(out["state"]["sim_or_real"].lower(), "real")

    def test_nested_chosen_rejected_and_trajectory(self):
        pair = {
            "chosen": _thalamic(sim_or_real="real", meta={"id": "c"}),
            "rejected": _thalamic(
                sim_or_real="high-fidelity plant simulation",
                meta={"id": "r"},
            ),
            "critique": "process over luck",
            "meta": {"id": "pref-1"},
        }
        out = promote.promote_record(pair)
        self.assertEqual(out["chosen"]["provenance"]["kind"], "designed")
        self.assertEqual(out["chosen"]["state"]["sim_or_real"], "designed")
        self.assertEqual(out["chosen"]["provenance"]["claimed"], "real")
        self.assertEqual(out["rejected"]["provenance"]["kind"], "simulated")
        self.assertEqual(out["rejected"]["state"]["sim_or_real"], "simulated")

        bridge = {
            "language_view": {
                "trajectory": _thalamic(
                    sim_or_real="hardware-in-the-loop (flight SPAD array)"
                )
            },
            "spike_events": [
                {"channel": "a", "t_rel_ms": 10.0},
                {"channel": "b", "t_rel_ms": 20.0},
            ],
            "meta": {"id": "bridge-1"},
        }
        bout = promote.promote_record(bridge)
        traj = bout["language_view"]["trajectory"]
        self.assertEqual(traj["provenance"]["kind"], "hil")
        self.assertEqual(traj["state"]["sim_or_real"], "hil")

    def test_missing_sim_or_real_unknown(self):
        rec = _thalamic()
        del rec["state"]["sim_or_real"]
        out = promote.promote_record(rec)
        self.assertEqual(out["provenance"]["kind"], "unknown")
        self.assertIsNone(out["provenance"]["claimed"])
        self.assertEqual(out["state"]["provenance"]["kind"], "unknown")
        self.assertNotIn("sim_or_real", out["state"])

    def test_stateless_factory_record_is_stamped_designed(self):
        record = {
            "id": "coding-episode-1",
            "goal": "repair a queue consumer",
            "steps": [],
            "outcome": "verified",
            "meta": {"factory": "agentic-coding-trajectory-factory"},
            "provenance": {"kind": "unknown", "claimed": None},
        }

        out = promote.promote_record(record)

        self.assertEqual(out["provenance"]["kind"], "designed")
        self.assertIsNone(out["provenance"]["claimed"])
        self.assertEqual(out["provenance"]["inferred_from"], "meta.factory")

    def test_unsorted_spikes_are_sorted_and_flagged(self):
        rec = json.loads((FIXTURES / "bad-spikes.jsonl").read_text().splitlines()[0])
        out = promote.promote_record(rec)
        times = [e["t_rel_ms"] for e in out["spike_events"]]
        self.assertEqual(times, sorted(times))
        self.assertTrue(out["meta"]["spike_events_resorted"])

    def test_already_sorted_spikes_not_flagged(self):
        rec = _thalamic()
        rec["spike_events"] = [
            {"channel": "a", "t_ms": 1.0},
            {"channel": "b", "t_ms": 2.0},
        ]
        out = promote.promote_record(rec)
        self.assertNotIn("spike_events_resorted", out.get("meta", {}))
        self.assertEqual([e.get("t_rel_ms") or e.get("t_ms") for e in out["spike_events"]], [1.0, 2.0])

    def test_mixed_timestamp_keys_are_not_resorted_as_one_clock(self):
        rec = _thalamic()
        rec["spike_events"] = [
            {"channel": "a", "t_rel_ms": 120.0},
            {"channel": "b", "t_ms": 90.0},
        ]
        out = promote.promote_record(rec)
        self.assertEqual(
            [event.get("t_rel_ms") or event.get("t_ms") for event in out["spike_events"]],
            [120.0, 90.0],
        )
        self.assertNotIn("spike_events_resorted", out.get("meta", {}))

    def test_large_integer_timestamp_order_is_resorted_without_precision_loss(self):
        rec = _thalamic()
        rec["spike_events"] = [
            {"channel": "a", "t_rel_ms": 9007199254740993},
            {"channel": "b", "t_rel_ms": 9007199254740992},
        ]
        out = promote.promote_record(rec)
        self.assertEqual(
            [event["t_rel_ms"] for event in out["spike_events"]],
            [9007199254740992, 9007199254740993],
        )
        self.assertTrue(out["meta"]["spike_events_resorted"])


class TestPromoteRun(unittest.TestCase):
    def test_rejects_destination_inside_raw(self):
        with tempfile.TemporaryDirectory() as td:
            raw = Path(td) / "raw"
            _write_jsonl(raw / "f" / "a.jsonl", [_thalamic()])
            with self.assertRaisesRegex(ValueError, "not nested inside"):
                promote.promote_run(raw, raw / "cleaned")
            self.assertFalse((raw / "cleaned").exists())

    def test_rejects_existing_destination_without_touching_it(self):
        with tempfile.TemporaryDirectory() as td:
            raw = Path(td) / "raw"
            cleaned = Path(td) / "cleaned"
            _write_jsonl(raw / "f" / "a.jsonl", [_thalamic()])
            cleaned.mkdir()
            sentinel = cleaned / "sentinel.txt"
            sentinel.write_text("keep\n")
            with self.assertRaisesRegex(ValueError, "refusing to overwrite"):
                promote.promote_run(raw, cleaned)
            self.assertEqual(sentinel.read_text(), "keep\n")

    def test_raw_fixture_bytes_unchanged_and_cleaned_remapped(self):
        with tempfile.TemporaryDirectory() as td:
            raw = Path(td) / "raw"
            cleaned = Path(td) / "cleaned"
            src = raw / "thalamic-trajectory-factory" / "batch.jsonl"
            rec = _thalamic()
            _write_jsonl(src, [rec])
            (raw / "NOTES.md").write_text("do not copy me\n")
            before = _snapshot(raw)

            result = promote.promote_run(raw, cleaned)

            self.assertEqual(_snapshot(raw), before)
            dest = cleaned / "thalamic-trajectory-factory" / "batch.jsonl"
            self.assertTrue(dest.is_file())
            out = json.loads(dest.read_text().splitlines()[0])
            self.assertEqual(out["provenance"]["kind"], "designed")
            self.assertEqual(out["provenance"]["claimed"], CLAIMED_LIVE)
            self.assertEqual(out["state"]["sim_or_real"], "designed")
            blob = dest.read_text()
            self.assertNotRegex(blob, r'"sim_or_real":\s*"real')
            self.assertFalse((cleaned / "NOTES.md").exists())
            self.assertGreaterEqual(result["files"], 1)
            self.assertGreaterEqual(result["records"], 1)

    def test_cleaned_never_emits_real_kind(self):
        with tempfile.TemporaryDirectory() as td:
            raw = Path(td) / "raw"
            cleaned = Path(td) / "cleaned"
            _write_jsonl(
                raw / "f" / "a.jsonl",
                [
                    _thalamic(sim_or_real="real"),
                    _thalamic(sim_or_real="real (production plant; actions live)"),
                ],
            )
            promote.promote_run(raw, cleaned)
            text = (cleaned / "f" / "a.jsonl").read_text()
            for line in text.splitlines():
                obj = json.loads(line)
                self.assertNotEqual(obj["state"]["sim_or_real"], "real")
                self.assertNotEqual(obj["provenance"]["kind"], "real")
                self.assertIn(obj["provenance"]["kind"], {"designed", "simulated", "hil", "unknown"})

    def test_reward_scale_uses_units_migration_else_sign_order_only(self):
        with tempfile.TemporaryDirectory() as td:
            raw = Path(td) / "raw"
            cleaned = Path(td) / "cleaned"
            ffpc = raw / "failure-as-fuel-preference-cascade"
            ttf = raw / "thalamic-trajectory-factory"
            _write_jsonl(ffpc / "preferences.jsonl", [_thalamic(meta={"id": "p"})])
            _write_jsonl(ffpc / "batch-r02.jsonl", [_thalamic(meta={"id": "r2"})])
            _write_jsonl(ffpc / "batch-r03.jsonl", [_thalamic(meta={"id": "r3"})])
            _write_jsonl(ffpc / "batch-r05.jsonl", [_thalamic(meta={"id": "r5"})])
            _write_jsonl(ttf / "trajectories.jsonl", [_thalamic(meta={"id": "t"})])
            (ffpc / "units-migration.json").write_text(
                json.dumps(_units_migration(), indent=2) + "\n"
            )

            promote.promote_run(raw, cleaned)
            scale_path = cleaned / "reward-scale.json"
            self.assertTrue(scale_path.is_file())
            scale = json.loads(scale_path.read_text())

            prefs = _scale_entry(scale, "failure-as-fuel-preference-cascade", "preferences.jsonl")
            self.assertIsNone(prefs["usd_factor_or_null"])
            self.assertEqual(prefs["mix_policy"], "sign_order_only")
            self.assertIn("aggregation", prefs)
            self.assertIn("native_unit", prefs)

            r02 = _scale_entry(scale, "failure-as-fuel-preference-cascade", "batch-r02.jsonl")
            self.assertIsNone(r02["usd_factor_or_null"])
            self.assertEqual(r02["mix_policy"], "exclude_from_magnitude")

            r03 = _scale_entry(scale, "failure-as-fuel-preference-cascade", "batch-r03.jsonl")
            self.assertEqual(r03["usd_factor_or_null"], 1.0)
            self.assertNotEqual(r03["mix_policy"], "exclude_from_magnitude")

            r05 = _scale_entry(scale, "failure-as-fuel-preference-cascade", "batch-r05.jsonl")
            self.assertEqual(r05["mix_policy"], "sign_order_only")
            self.assertIsNone(r05["usd_factor_or_null"])
            self.assertEqual(r05["aggregation"], "unspecified")

            ttf_e = _scale_entry(scale, "thalamic-trajectory-factory", "trajectories.jsonl")
            self.assertEqual(ttf_e["mix_policy"], "sign_order_only")
            self.assertIsNone(ttf_e["usd_factor_or_null"])
            self.assertEqual(ttf_e["aggregation"], "unspecified")

    def test_provenance_md_and_cli(self):
        with tempfile.TemporaryDirectory() as td:
            raw = Path(td) / "raw"
            cleaned = Path(td) / "cleaned"
            records = []
            for index in range(5):
                record = _thalamic(
                    sim_or_real="real" if index == 0 else "unknown",
                    meta={"id": f"t-{index}"},
                )
                record["state"]["domain"] = f"distinct-domain-{index}"
                record["state"]["note"] = f"independent scenario vocabulary {index}"
                record["proposed_action"]["action_type"] = f"proposal-{index}"
                record["executed_action"]["action_type"] = f"execution-{index}"
                records.append(record)
            _write_jsonl(raw / "f" / "a.jsonl", records)
            proc = _cli([str(raw), str(cleaned)])
            self.assertEqual(proc.returncode, 0, proc.stderr)
            note = (cleaned / "PROVENANCE.md").read_text()
            self.assertRegex(note.lower(), r"never|not")
            self.assertRegex(note.lower(), r"\breal\b")
            self.assertRegex(note.lower(), r"source of truth|sot|raw")
            payload = json.loads(proc.stdout)
            self.assertGreaterEqual(payload.get("files", 0), 1)
            self.assertGreaterEqual(payload.get("records", 0), 1)
            self.assertFalse(payload["quality_gate"]["blocked"])
            manifest = cleaned / "quality-manifest.json"
            self.assertTrue(manifest.is_file())
            self.assertFalse(json.loads(manifest.read_text())["blocked"])

    def test_cli_returns_one_and_keeps_manifest_when_quality_gate_blocks(self):
        with tempfile.TemporaryDirectory() as td:
            raw = Path(td) / "raw"
            cleaned = Path(td) / "cleaned"
            record = _thalamic(meta={"id": "duplicate"})
            _write_jsonl(raw / "f" / "a.jsonl", [record, record])

            proc = _cli([str(raw), str(cleaned)])

            self.assertEqual(proc.returncode, 1, proc.stderr)
            payload = json.loads(proc.stdout)
            self.assertTrue(payload["quality_gate"]["blocked"])
            self.assertTrue(any("duplicate" in b for b in payload["quality_gate"]["blockers"]))
            manifest = cleaned / "quality-manifest.json"
            self.assertTrue(manifest.is_file())
            report = json.loads(manifest.read_text())
            self.assertTrue(report["blocked"])
            self.assertEqual(report["counts"]["excluded_records"], 1)

    def test_cli_rejects_manifest_inside_raw_before_writing_cleaned_output(self):
        with tempfile.TemporaryDirectory() as td:
            raw = Path(td) / "raw"
            cleaned = Path(td) / "cleaned"
            _write_jsonl(raw / "f" / "a.jsonl", [_thalamic()])

            proc = _cli(
                [
                    str(raw),
                    str(cleaned),
                    "--quality-manifest",
                    str(raw / "quality-manifest.json"),
                ]
            )

            self.assertEqual(proc.returncode, 2)
            self.assertFalse(cleaned.exists())
            self.assertFalse((raw / "quality-manifest.json").exists())

    def test_cli_rejects_manifest_equal_to_or_ancestor_of_destination_preflight(self):
        with tempfile.TemporaryDirectory() as td:
            base = Path(td)
            for label, cleaned, manifest in (
                (
                    "equal",
                    base / "equal-cleaned",
                    base / "equal-cleaned",
                ),
                (
                    "ancestor",
                    base / "future-parent" / "cleaned",
                    base / "future-parent",
                ),
            ):
                with self.subTest(label=label):
                    raw = base / f"raw-{label}"
                    _write_jsonl(raw / "f" / "a.jsonl", [_thalamic()])

                    proc = _cli(
                        [
                            str(raw),
                            str(cleaned),
                            "--quality-manifest",
                            str(manifest),
                        ]
                    )

                    self.assertEqual(proc.returncode, 2, proc.stderr)
                    self.assertIn("must not equal or contain", proc.stderr)
                    self.assertFalse(cleaned.exists())
                    self.assertFalse(manifest.exists())

    def test_cli_rejects_threshold_one_before_writing_destination(self):
        with tempfile.TemporaryDirectory() as td:
            raw = Path(td) / "raw"
            cleaned = Path(td) / "cleaned"
            _write_jsonl(raw / "f" / "a.jsonl", [_thalamic()])

            proc = _cli([str(raw), str(cleaned), "--threshold", "1.0"])

            self.assertEqual(proc.returncode, 2, proc.stderr)
            self.assertIn("[-1, 1)", proc.stderr)
            self.assertFalse(cleaned.exists())


if __name__ == "__main__":
    unittest.main()
