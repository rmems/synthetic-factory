#!/usr/bin/env python3
"""Fail-closed TTF r12 audit runner. Does not write outputs/raw/."""

from __future__ import annotations

import json
import math
import re
import subprocess
import sys
import traceback
from collections import defaultdict
from copy import deepcopy
from pathlib import Path

sys.path.insert(0, str(Path("/home/raulmc/rmems/synthetic-factory/pipelines")))

from check_records import FactoryStaging, check_jsonl
from curate_bridge import raster_status
from exact_json import dumps_exact_json
from round_txn import validate_novel_coverage
from validate_run import HIDDEN_THOUGHT_KEYS, check_line, is_number
from verify_execution import verify_batch_for_frontier

BATCH = Path("/tmp/batch-r12.jsonl")
NOTES = Path("/tmp/NOTES-r12.md")
REPO = Path("/home/raulmc/rmems/synthetic-factory")
HEADS = ("task_progress", "safety", "efficiency", "coherence", "exploration")
EXPECTED_IDS = [f"ttf-r12-{n:03d}" for n in range(76, 81)]
EXPECTED_DOMAINS = [
    "warehouse-amr",
    "aerial-swarm",
    "underwater-rov",
    "grid-inspection",
    "humanoid-locomotion",
]
RASTER_BUDGETS = {
    "ttf-r12-076": {"n": 64, "rate": 40, "window_ms": 25, "spikes": 64, "energy_pJ": 1472},
    "ttf-r12-077": {"n": 128, "rate": 25, "window_ms": 40, "spikes": 128, "energy_pJ": 2944},
    "ttf-r12-078": {"n": 32, "rate": 50, "window_ms": 20, "spikes": 32, "energy_pJ": 736},
    "ttf-r12-079": {"n": 96, "rate": 30, "window_ms": 32, "spikes": 92, "energy_pJ": 2116},
    "ttf-r12-080": {"n": 48, "rate": 35, "window_ms": 28, "spikes": 47, "energy_pJ": 1081},
}
SPIKE_TIME_KEYS = ("t_rel_ms", "t_us", "t_ms", "t_s", "t")
HIDDEN_KEY_RE = re.compile(r"[^a-z0-9]+")


def load_records():
    text = BATCH.read_bytes().decode("utf-8")
    records = []
    for lineno, line in enumerate(text.split("\n"), 1):
        if not line.strip():
            continue
        obj = json.loads(line)
        records.append((lineno, obj, line))
    return records


def token_set(text: str):
    return set(re.findall(r"[a-z0-9]+", (text or "").lower()))


def jaccard(a, b):
    if not a and not b:
        return 0.0
    inter = len(a & b)
    union = len(a | b)
    return inter / union if union else 0.0


def walk_keys(value, path=""):
    found = []
    if isinstance(value, dict):
        for key, item in value.items():
            child = f"{path}.{key}" if path else str(key)
            found.append((str(key), child, item))
            found.extend(walk_keys(item, child))
    elif isinstance(value, list):
        for i, item in enumerate(value):
            found.extend(walk_keys(item, f"{path}[{i}]"))
    return found


def normalize_key(key: str) -> str:
    camel = re.sub(r"(?<=[a-z0-9])(?=[A-Z])", "_", str(key))
    return HIDDEN_KEY_RE.sub("_", camel.casefold()).strip("_")


def event_time_keys(event):
    if not isinstance(event, dict):
        return []
    return [k for k in SPIKE_TIME_KEYS if k in event] or [
        k for k in event if str(k).startswith("t_") or k in ("t",)
    ]


def finite(value):
    return is_number(value)


def expected_spikes(neurons, rate, window_s):
    return round(float(neurons) * float(rate) * float(window_s))


def main():
    results = []
    records = load_records()
    by_id = {obj["id"]: (lineno, obj) for lineno, obj, _ in records}

    # ------------------------------------------------------------------
    # 1. check_jsonl staging
    # ------------------------------------------------------------------
    try:
        errors, warnings, kinds, n = check_jsonl(
            BATCH,
            "batch-r12.jsonl",
            staging=FactoryStaging(enabled=True),
        )
        ok = not errors
        results.append(
            {
                "n": 1,
                "name": "check_jsonl(..., staging=FactoryStaging(enabled=True))",
                "pass": ok,
                "errors": list(errors),
                "warnings": list(warnings),
                "detail": {"kinds": kinds, "records": n, "error_count": len(errors), "warning_count": len(warnings)},
            }
        )
    except Exception as exc:
        results.append(
            {
                "n": 1,
                "name": "check_jsonl(..., staging=FactoryStaging(enabled=True))",
                "pass": False,
                "errors": [f"{type(exc).__name__}: {exc}"],
                "warnings": [],
                "detail": {"traceback": traceback.format_exc()},
            }
        )

    # ------------------------------------------------------------------
    # 2. check_line factory_staging=True
    # ------------------------------------------------------------------
    line_errors = []
    line_kinds = {}
    for lineno, obj, _ in records:
        where = f"batch-r12.jsonl:{lineno}"
        try:
            errs, kind = check_line(obj, where, factory_staging=True)
            line_kinds[obj.get("id")] = kind
            line_errors.extend(errs)
        except Exception as exc:
            line_errors.append(f"{where}: {type(exc).__name__}: {exc}")
    results.append(
        {
            "n": 2,
            "name": "validate_run.check_line(obj, factory_staging=True) per record",
            "pass": not line_errors,
            "errors": line_errors,
            "warnings": [],
            "detail": {"kinds": line_kinds},
        }
    )

    # ------------------------------------------------------------------
    # 3. exact_json.dumps_exact_json per record
    # ------------------------------------------------------------------
    exact_errors = []
    for lineno, obj, raw in records:
        where = f"batch-r12.jsonl:{lineno}"
        try:
            dumps_exact_json(obj)
        except Exception as exc:
            exact_errors.append(f"{where} {obj.get('id')}: {type(exc).__name__}: {exc}")
    results.append(
        {
            "n": 3,
            "name": "exact_json.dumps_exact_json per record",
            "pass": not exact_errors,
            "errors": exact_errors,
            "warnings": [],
            "detail": {},
        }
    )

    # ------------------------------------------------------------------
    # 4. raster_status
    # ------------------------------------------------------------------
    raster_errors = []
    raster_details = {}
    for lineno, obj, _ in records:
        rid = obj.get("id")
        try:
            status = raster_status(obj)
        except Exception as exc:
            raster_errors.append(f"{rid}: raster_status raised {type(exc).__name__}: {exc}")
            continue
        codes = list(status.get("reason_codes") or [])
        present = bool(status.get("gate_snn_present"))
        entries = int(status.get("routing_table_entries") or 0)
        raster_details[rid] = {
            "reason_codes": codes,
            "gate_snn_present": present,
            "gate_snn_valid": status.get("gate_snn_valid"),
            "routing_table_entries": entries,
            "raster_valid": status.get("raster_valid"),
            "spikes": status.get("spikes"),
        }
        if codes:
            raster_errors.append(f"{rid}: reason_codes={codes}")
        if not present:
            raster_errors.append(f"{rid}: gate_snn_present is False")
        if entries < 1:
            raster_errors.append(f"{rid}: routing_table_entries={entries} < 1")
    results.append(
        {
            "n": 4,
            "name": "curate_bridge.raster_status per record",
            "pass": not raster_errors,
            "errors": raster_errors,
            "warnings": [],
            "detail": raster_details,
        }
    )

    # ------------------------------------------------------------------
    # 5. verify_batch_for_frontier strict
    # ------------------------------------------------------------------
    try:
        counts, findings, blocked = verify_batch_for_frontier(BATCH, strict=True)
        v_ok = counts.get("verified") == 5 and blocked is False
        v_errors = []
        if counts.get("verified") != 5:
            v_errors.append(f"verified={counts.get('verified')} (want 5); counts={counts}")
        if blocked:
            v_errors.append(f"blocked={blocked}; findings={findings}")
        for finding in findings:
            v_errors.append(
                f"{finding.get('file')}:{finding.get('line')} {finding.get('status')}: {finding.get('reason')}"
            )
        results.append(
            {
                "n": 5,
                "name": "verify_execution.verify_batch_for_frontier(..., strict=True)",
                "pass": v_ok and not findings,
                "errors": v_errors,
                "warnings": [],
                "detail": {"counts": counts, "blocked": blocked, "findings": findings},
            }
        )
    except Exception as exc:
        results.append(
            {
                "n": 5,
                "name": "verify_execution.verify_batch_for_frontier(..., strict=True)",
                "pass": False,
                "errors": [f"{type(exc).__name__}: {exc}"],
                "warnings": [],
                "detail": {"traceback": traceback.format_exc()},
            }
        )

    # ------------------------------------------------------------------
    # 6. spike_probe --strict
    # ------------------------------------------------------------------
    probe = subprocess.run(
        [sys.executable, str(REPO / "pipelines" / "spike_probe.py"), "--strict", str(BATCH)],
        capture_output=True,
        text=True,
        cwd=str(REPO),
    )
    probe_errors = []
    if probe.returncode != 0:
        probe_errors.append(f"exit={probe.returncode}")
        if probe.stderr.strip():
            probe_errors.append(probe.stderr.strip())
        if probe.stdout.strip():
            # include problems from summary
            try:
                summary = json.loads(probe.stdout)
                for problem in summary.get("problems") or []:
                    probe_errors.append(
                        f"{problem.get('source')} {problem.get('record_id')} "
                        f"{problem.get('scope')} {problem.get('reason_codes')}"
                    )
            except Exception:
                probe_errors.append(probe.stdout.strip()[:4000])
    results.append(
        {
            "n": 6,
            "name": "python3 pipelines/spike_probe.py --strict /tmp/batch-r12.jsonl",
            "pass": probe.returncode == 0,
            "errors": probe_errors,
            "warnings": [],
            "detail": {
                "returncode": probe.returncode,
                "stdout": probe.stdout,
                "stderr": probe.stderr,
            },
        }
    )

    # ------------------------------------------------------------------
    # 7. Reward arithmetic
    # ------------------------------------------------------------------
    reward_errors = []
    reward_detail = {}
    for lineno, obj, _ in records:
        rid = obj.get("id")
        rc = obj.get("reward_components") or {}
        fo = obj.get("future_outcome") or {}
        heads = {h: rc.get(h) for h in HEADS}
        total = rc.get("total")
        missing = [h for h, v in heads.items() if not finite(v)]
        if missing or not finite(total):
            reward_errors.append(f"{rid}: non-finite heads/total missing={missing} total={total!r}")
            continue
        head_sum = sum(float(heads[h]) for h in HEADS)
        if abs(float(total) - head_sum) > 1e-6:
            reward_errors.append(
                f"{rid}: total {total} != sum(heads) {head_sum} (diff {abs(float(total)-head_sum)})"
            )
        ticks = rc.get("ticks")
        if not isinstance(ticks, list) or not ticks:
            reward_errors.append(f"{rid}: ticks missing or empty")
            ticks = []
        col = {h: 0.0 for h in HEADS}
        t_us_vals = []
        for i, tick in enumerate(ticks):
            if not isinstance(tick, dict):
                reward_errors.append(f"{rid}: tick[{i}] is not an object")
                continue
            if not finite(tick.get("t_us")):
                reward_errors.append(f"{rid}: tick[{i}].t_us not finite: {tick.get('t_us')!r}")
            else:
                t_us_vals.append(tick["t_us"])
            for h in HEADS:
                if not finite(tick.get(h)):
                    reward_errors.append(f"{rid}: tick[{i}].{h} not finite: {tick.get(h)!r}")
                else:
                    col[h] += float(tick[h])
        for h in HEADS:
            if abs(col[h] - float(heads[h])) > 1e-6:
                reward_errors.append(
                    f"{rid}: tick column {h} sums to {col[h]} != head {heads[h]} "
                    f"(diff {abs(col[h]-float(heads[h]))})"
                )
        inflection = fo.get("reward_inflection_t_us")
        if not finite(inflection):
            reward_errors.append(f"{rid}: future_outcome.reward_inflection_t_us missing/non-finite")
        elif inflection not in t_us_vals:
            reward_errors.append(
                f"{rid}: inflection t_us={inflection} is not a tick (ticks={t_us_vals})"
            )
        reward_detail[rid] = {
            "heads": heads,
            "head_sum": head_sum,
            "total": total,
            "tick_column_sums": col,
            "inflection": inflection,
            "tick_t_us": t_us_vals,
            "n_ticks": len(ticks),
        }
    results.append(
        {
            "n": 7,
            "name": "reward arithmetic (heads, ticks, inflection)",
            "pass": not reward_errors,
            "errors": reward_errors,
            "warnings": [],
            "detail": reward_detail,
        }
    )

    # ------------------------------------------------------------------
    # 8. Spike trains
    # ------------------------------------------------------------------
    spike_errors = []
    spike_detail = {}
    for lineno, obj, _ in records:
        rid = obj.get("id")
        events = obj.get("spike_events")
        state = obj.get("state") or {}
        if not isinstance(events, list):
            spike_errors.append(f"{rid}: spike_events is not a list")
            continue
        n_ev = len(events)
        if not (5 <= n_ev <= 40):
            spike_errors.append(f"{rid}: spike_events count {n_ev} not in 5–40")
        keys_used = []
        times = []
        by_ch = defaultdict(list)
        for i, ev in enumerate(events):
            if not isinstance(ev, dict):
                spike_errors.append(f"{rid}: spike_events[{i}] not an object")
                continue
            tkeys = [k for k in ev if k in SPIKE_TIME_KEYS or str(k).startswith("t_")]
            # keep only timestamp-like keys besides channel/amplitude
            tkeys = [k for k in ev.keys() if k not in ("channel", "amplitude")]
            keys_used.append(tuple(sorted(tkeys)))
            if "t_rel_ms" not in ev:
                spike_errors.append(f"{rid}: spike_events[{i}] missing t_rel_ms")
            extra = [k for k in tkeys if k != "t_rel_ms"]
            if extra:
                spike_errors.append(
                    f"{rid}: spike_events[{i}] extra timestamp keys {extra} (want only t_rel_ms)"
                )
            t = ev.get("t_rel_ms")
            if not finite(t):
                spike_errors.append(f"{rid}: spike_events[{i}].t_rel_ms not finite: {t!r}")
                continue
            times.append(float(t))
            ch = ev.get("channel")
            by_ch[ch].append(float(t))
        unique_keysets = set(keys_used)
        if unique_keysets != {("t_rel_ms",)}:
            spike_errors.append(
                f"{rid}: timestamp keysets {sorted(unique_keysets)} — want only {{t_rel_ms}}"
            )
        for i in range(1, len(times)):
            if times[i] < times[i - 1]:
                spike_errors.append(
                    f"{rid}: t_rel_ms not globally non-decreasing at index {i}: "
                    f"{times[i-1]} -> {times[i]}"
                )
                break
        for ch, ts in by_ch.items():
            for a, b in zip(ts, ts[1:]):
                gap = b - a
                if gap < 0.8:
                    spike_errors.append(
                        f"{rid}: same-channel gap {gap} ms < 0.8 on {ch!r} ({a} -> {b})"
                    )
        rw = state.get("race_window_rel_ms")
        if not (isinstance(rw, list) and len(rw) == 2 and finite(rw[0]) and finite(rw[1])):
            spike_errors.append(f"{rid}: state.race_window_rel_ms invalid: {rw!r}")
            in_window_channels = set()
        else:
            lo, hi = float(rw[0]), float(rw[1])
            in_window_channels = set()
            for ch, ts in by_ch.items():
                if ch is None:
                    continue
                if any(lo <= t <= hi for t in ts):
                    in_window_channels.add(ch)
            if len(in_window_channels) < 2:
                spike_errors.append(
                    f"{rid}: {len(in_window_channels)} channel(s) with spike in "
                    f"race_window_rel_ms {rw}: {sorted(in_window_channels)}"
                )
        spike_detail[rid] = {
            "n_events": n_ev,
            "channels": {str(k): v for k, v in by_ch.items()},
            "times": times,
            "race_window_rel_ms": rw,
            "in_window_channels": sorted(in_window_channels),
        }
    results.append(
        {
            "n": 8,
            "name": "spike trains (key, order, refractory, density, race window)",
            "pass": not spike_errors,
            "errors": spike_errors,
            "warnings": [],
            "detail": spike_detail,
        }
    )

    # ------------------------------------------------------------------
    # 9. Raster budgets EXACT
    # ------------------------------------------------------------------
    raster_budget_errors = []
    raster_budget_detail = {}
    for rid, want in RASTER_BUDGETS.items():
        if rid not in by_id:
            raster_budget_errors.append(f"{rid}: missing from batch")
            continue
        obj = by_id[rid][1]
        raster = obj.get("raster") or {}
        got = {
            "n": raster.get("neurons"),
            "rate": raster.get("mean_rate_hz"),
            "window_ms": raster.get("window_ms"),
            "spikes": raster.get("spikes"),
            "energy_pJ": raster.get("energy_pJ"),
        }
        raster_budget_detail[rid] = {"want": want, "got": got}
        for field in want:
            if got[field] != want[field]:
                raster_budget_errors.append(
                    f"{rid}: raster.{field}={got[field]!r} != {want[field]!r}"
                )
    results.append(
        {
            "n": 9,
            "name": "raster budgets EXACT (n/rate/window_ms/spikes/energy_pJ)",
            "pass": not raster_budget_errors,
            "errors": raster_budget_errors,
            "warnings": [],
            "detail": raster_budget_detail,
        }
    )

    # ------------------------------------------------------------------
    # 10. gate_snn.decision == safety_decision.decision; pop budget ±1
    # ------------------------------------------------------------------
    gate_errors = []
    gate_detail = {}
    for lineno, obj, _ in records:
        rid = obj.get("id")
        gs = obj.get("gate_snn") or {}
        sd = obj.get("safety_decision") or {}
        gdec = gs.get("decision")
        sdec = sd.get("decision")
        if gdec != sdec:
            gate_errors.append(
                f"{rid}: gate_snn.decision={gdec!r} != safety_decision.decision={sdec!r}"
            )
        dw_ms = gs.get("decision_window_ms")
        dw_s = gs.get("decision_window_s")
        if finite(dw_s):
            window_s = float(dw_s)
        elif finite(dw_ms):
            window_s = float(dw_ms) / 1000.0
        else:
            window_s = None
            gate_errors.append(f"{rid}: gate_snn missing decision_window_ms/s")
        pops = gs.get("populations") or []
        pop_rows = []
        for i, pop in enumerate(pops):
            if not isinstance(pop, dict):
                gate_errors.append(f"{rid}: populations[{i}] not an object")
                continue
            rate = pop.get("mean_rate_hz", pop.get("rate_hz"))
            spikes = pop.get("spikes")
            neurons = pop.get("neurons")
            row = {
                "name": pop.get("name"),
                "neurons": neurons,
                "rate": rate,
                "spikes": spikes,
                "declares_budget": rate is not None or spikes is not None,
            }
            if rate is not None or spikes is not None:
                if not (finite(rate) and finite(neurons) and finite(spikes) and window_s is not None):
                    gate_errors.append(
                        f"{rid}: population {pop.get('name')!r} incomplete rate/spikes/neurons/window"
                    )
                else:
                    exp = expected_spikes(neurons, rate, window_s)
                    row["expected"] = exp
                    if abs(int(spikes) - exp) > 1:
                        gate_errors.append(
                            f"{rid}: population {pop.get('name')!r} spikes={spikes} "
                            f"vs expected round({neurons}*{rate}*{window_s})={exp} (tol ±1)"
                        )
            pop_rows.append(row)
        gate_detail[rid] = {
            "gate_snn.decision": gdec,
            "safety_decision.decision": sdec,
            "decision_window_ms": dw_ms,
            "window_s": window_s,
            "populations": pop_rows,
        }
    results.append(
        {
            "n": 10,
            "name": "gate_snn.decision match + population rate/spikes ±1",
            "pass": not gate_errors,
            "errors": gate_errors,
            "warnings": [],
            "detail": gate_detail,
        }
    )

    # ------------------------------------------------------------------
    # 11. ACCEPT (076) executed parameters == proposed parameters
    # ------------------------------------------------------------------
    accept_errors = []
    rec076 = by_id.get("ttf-r12-076")
    accept_detail = {}
    if rec076 is None:
        accept_errors.append("ttf-r12-076 missing")
    else:
        obj = rec076[1]
        decision = (obj.get("safety_decision") or {}).get("decision")
        if decision != "ACCEPT":
            accept_errors.append(f"ttf-r12-076 safety_decision.decision={decision!r} != ACCEPT")
        proposed = (obj.get("proposed_action") or {}).get("parameters")
        executed = (obj.get("executed_action") or {}).get("parameters")
        accept_detail = {"proposed": proposed, "executed": executed, "decision": decision}
        if proposed != executed:
            accept_errors.append(
                f"ttf-r12-076 executed parameters != proposed parameters: "
                f"proposed={proposed!r} executed={executed!r}"
            )
    results.append(
        {
            "n": 11,
            "name": "ACCEPT (076) executed parameters == proposed parameters",
            "pass": not accept_errors,
            "errors": accept_errors,
            "warnings": [],
            "detail": accept_detail,
        }
    )

    # ------------------------------------------------------------------
    # 12. Gate mix
    # ------------------------------------------------------------------
    mix_errors = []
    mix_rows = []
    for rid in EXPECTED_IDS:
        if rid not in by_id:
            mix_errors.append(f"{rid}: missing")
            continue
        obj = by_id[rid][1]
        sd = obj.get("safety_decision") or {}
        meta = obj.get("meta") or {}
        mix_rows.append(
            {
                "id": rid,
                "decision": sd.get("decision"),
                "correctness": sd.get("correctness"),
                "supervisor_error_type": meta.get("supervisor_error_type"),
            }
        )
    decisions = [r["decision"] for r in mix_rows]
    correctness = {r["id"]: r["correctness"] for r in mix_rows}
    incorrect = [r for r in mix_rows if r["correctness"] != "correct"]
    if len(incorrect) != 1:
        mix_errors.append(f"incorrect-gate count {len(incorrect)} != 1: {incorrect}")
    else:
        bad = incorrect[0]
        if bad["id"] != "ttf-r12-079":
            mix_errors.append(f"incorrect gate is {bad['id']} not ttf-r12-079")
        if bad["decision"] != "REJECT":
            mix_errors.append(f"ttf-r12-079 decision={bad['decision']!r} != REJECT")
        if bad["correctness"] != "incorrect":
            mix_errors.append(f"ttf-r12-079 correctness={bad['correctness']!r} != incorrect")
        err_type = bad.get("supervisor_error_type")
        if err_type != "wrong-reject":
            mix_errors.append(
                f"ttf-r12-079 meta.supervisor_error_type={err_type!r} != 'wrong-reject'"
            )
    for rid in EXPECTED_IDS:
        if rid == "ttf-r12-079":
            continue
        if rid in correctness and correctness[rid] != "correct":
            mix_errors.append(f"{rid} correctness={correctness[rid]!r} != correct")
    n_accept = decisions.count("ACCEPT")
    n_modify = decisions.count("MODIFY")
    n_reject = decisions.count("REJECT")
    if n_accept != 1:
        mix_errors.append(f"ACCEPT count {n_accept} != 1")
    if n_modify != 2:
        mix_errors.append(f"MODIFY count {n_modify} != 2")
    if n_reject != 2:
        mix_errors.append(f"REJECT count {n_reject} != 2 (want 1 correct + 1 wrong)")
    correct_reject = [
        r for r in mix_rows if r["decision"] == "REJECT" and r["correctness"] == "correct"
    ]
    wrong_reject = [
        r for r in mix_rows if r["decision"] == "REJECT" and r["correctness"] == "incorrect"
    ]
    if len(correct_reject) != 1:
        mix_errors.append(f"correct REJECT count {len(correct_reject)} != 1: {correct_reject}")
    if len(wrong_reject) != 1:
        mix_errors.append(f"wrong REJECT count {len(wrong_reject)} != 1: {wrong_reject}")
    results.append(
        {
            "n": 12,
            "name": "gate mix (1 ACCEPT, 2 MODIFY, 1 correct REJECT, 1 wrong REJECT at 079)",
            "pass": not mix_errors,
            "errors": mix_errors,
            "warnings": [],
            "detail": mix_rows,
        }
    )

    # ------------------------------------------------------------------
    # 13. Domains
    # ------------------------------------------------------------------
    domain_errors = []
    domain_rows = []
    got_domains = []
    for rid, expected in zip(EXPECTED_IDS, EXPECTED_DOMAINS):
        if rid not in by_id:
            domain_errors.append(f"{rid}: missing")
            continue
        obj = by_id[rid][1]
        state_d = (obj.get("state") or {}).get("domain")
        meta_d = (obj.get("meta") or {}).get("domain")
        domain_rows.append({"id": rid, "state.domain": state_d, "meta.domain": meta_d, "expected": expected})
        got_domains.append(state_d)
        if state_d != expected:
            domain_errors.append(f"{rid}: state.domain={state_d!r} != {expected!r}")
        if meta_d != expected:
            domain_errors.append(f"{rid}: meta.domain={meta_d!r} != {expected!r}")
    if got_domains != EXPECTED_DOMAINS:
        domain_errors.append(f"domain sequence {got_domains} != {EXPECTED_DOMAINS}")
    results.append(
        {
            "n": 13,
            "name": "domains exactly warehouse-amr, aerial-swarm, underwater-rov, grid-inspection, humanoid-locomotion",
            "pass": not domain_errors,
            "errors": domain_errors,
            "warnings": [],
            "detail": domain_rows,
        }
    )

    # ------------------------------------------------------------------
    # 14. 078 hil; none real
    # ------------------------------------------------------------------
    prov_errors = []
    prov_rows = []
    for lineno, obj, _ in records:
        rid = obj.get("id")
        val = (obj.get("state") or {}).get("sim_or_real")
        prov_rows.append({"id": rid, "sim_or_real": val})
        if val == "real":
            prov_errors.append(f"{rid}: sim_or_real='real'")
        if rid == "ttf-r12-078" and val != "hil":
            prov_errors.append(f"ttf-r12-078 sim_or_real={val!r} != 'hil'")
        if rid != "ttf-r12-078" and val == "hil":
            prov_errors.append(f"{rid}: unexpected hil (only 078 should be hil)")
    if "ttf-r12-078" not in by_id:
        prov_errors.append("ttf-r12-078 missing")
    results.append(
        {
            "n": 14,
            "name": "078 sim_or_real=hil; none real",
            "pass": not prov_errors,
            "errors": prov_errors,
            "warnings": [],
            "detail": prov_rows,
        }
    )

    # ------------------------------------------------------------------
    # 15. Hidden thought keys absent; training_ready absent
    # ------------------------------------------------------------------
    hidden_errors = []
    hidden_hits = []
    for lineno, obj, _ in records:
        rid = obj.get("id")
        for key, path, _item in walk_keys(obj):
            nk = normalize_key(key)
            if nk in HIDDEN_THOUGHT_KEYS:
                hidden_errors.append(f"{rid}: hidden thought key {key!r} at {path}")
                hidden_hits.append((rid, key, path))
            if nk == "training_ready" or key == "training_ready":
                hidden_errors.append(f"{rid}: training_ready present at {path}")
                hidden_hits.append((rid, key, path))
    results.append(
        {
            "n": 15,
            "name": "hidden thought keys absent; training_ready absent",
            "pass": not hidden_errors,
            "errors": hidden_errors,
            "warnings": [],
            "detail": {"hits": hidden_hits, "hidden_keys": sorted(HIDDEN_THOUGHT_KEYS)},
        }
    )

    # ------------------------------------------------------------------
    # 16. meta.round/factory/generator/run_label
    # ------------------------------------------------------------------
    meta_errors = []
    meta_rows = []
    want_meta = {
        "round": 12,
        "factory": "thalamic-trajectory-factory",
        "generator": "grok-4.6",
        "run_label": "2026-09-02-final-heavy",
    }
    for lineno, obj, _ in records:
        rid = obj.get("id")
        meta = obj.get("meta") or {}
        row = {k: meta.get(k) for k in want_meta}
        row["id"] = rid
        meta_rows.append(row)
        for k, v in want_meta.items():
            if meta.get(k) != v:
                meta_errors.append(f"{rid}: meta.{k}={meta.get(k)!r} != {v!r}")
    results.append(
        {
            "n": 16,
            "name": "meta.round=12 factory=thalamic-trajectory-factory generator=grok-4.6 run_label=2026-09-02-final-heavy",
            "pass": not meta_errors,
            "errors": meta_errors,
            "warnings": [],
            "detail": meta_rows,
        }
    )

    # ------------------------------------------------------------------
    # 17. meta.rights RM-793 research_only
    # ------------------------------------------------------------------
    rights_errors = []
    rights_rows = []
    for lineno, obj, _ in records:
        rid = obj.get("id")
        rights = (obj.get("meta") or {}).get("rights")
        rights_rows.append({"id": rid, "rights": rights})
        if not isinstance(rights, dict):
            rights_errors.append(f"{rid}: meta.rights missing or not an object: {rights!r}")
            continue
        intended = rights.get("intended_use")
        linear = rights.get("linear_issue")
        basis = rights.get("status_basis")
        if intended != "research_only":
            rights_errors.append(f"{rid}: rights.intended_use={intended!r} != 'research_only'")
        if linear != "RM-793":
            rights_errors.append(f"{rid}: rights.linear_issue={linear!r} != 'RM-793'")
        if not (isinstance(basis, str) and "RM-793" in basis):
            rights_errors.append(f"{rid}: rights.status_basis does not name RM-793: {basis!r}")
        blob = json.dumps(rights, sort_keys=True)
        if "RM-793" not in blob:
            rights_errors.append(f"{rid}: rights object does not mention RM-793")
        if "research_only" not in blob:
            rights_errors.append(f"{rid}: rights object does not mention research_only")
    results.append(
        {
            "n": 17,
            "name": "meta.rights RM-793 research_only",
            "pass": not rights_errors,
            "errors": rights_errors,
            "warnings": [],
            "detail": rights_rows,
        }
    )

    # ------------------------------------------------------------------
    # 18. NOTES Novel coverage
    # ------------------------------------------------------------------
    cov_errors = []
    try:
        cov = validate_novel_coverage(
            NOTES,
            REPO / "outputs" / "raw" / "thalamic-trajectory-factory",
            required=True,
        )
        if cov is not None:
            cov_errors.append(cov)
    except Exception as exc:
        cov_errors.append(f"{type(exc).__name__}: {exc}")
    notes_text = NOTES.read_text()
    labeled = [
        line
        for line in re.split(r"\r\n|\n|\r", notes_text)
        if re.search(r"^[ \t]*novel[ _-]?coverage\b", line, re.I)
    ]
    results.append(
        {
            "n": 18,
            "name": "NOTES Novel coverage via round_txn.validate_novel_coverage required=True",
            "pass": not cov_errors,
            "errors": cov_errors,
            "warnings": [],
            "detail": {"labeled_lines": labeled, "return": None if not cov_errors else cov_errors},
        }
    )

    # ------------------------------------------------------------------
    # 19. Jaccard overlap < 0.4
    # ------------------------------------------------------------------
    jac_errors = []
    jac_pairs = []
    descs = []
    for rid in EXPECTED_IDS:
        if rid not in by_id:
            jac_errors.append(f"{rid}: missing")
            continue
        desc = (by_id[rid][1].get("state") or {}).get("description") or ""
        descs.append((rid, token_set(desc), desc))
    max_j = 0.0
    max_pair = None
    for i in range(len(descs)):
        for j in range(i + 1, len(descs)):
            score = jaccard(descs[i][1], descs[j][1])
            jac_pairs.append({"a": descs[i][0], "b": descs[j][0], "jaccard": score})
            if score > max_j:
                max_j = score
                max_pair = (descs[i][0], descs[j][0])
            if score >= 0.4:
                jac_errors.append(
                    f"Jaccard({descs[i][0]}, {descs[j][0]}) = {score:.6f} >= 0.4"
                )
    results.append(
        {
            "n": 19,
            "name": "Jaccard overlap of state.description all pairs < 0.4",
            "pass": not jac_errors,
            "errors": jac_errors,
            "warnings": [],
            "detail": {"pairs": jac_pairs, "max": max_j, "max_pair": max_pair},
        }
    )

    # ------------------------------------------------------------------
    # 20. 079 recovery names ACCEPT + missed window cost
    # ------------------------------------------------------------------
    recov_errors = []
    recov_detail = {}
    if "ttf-r12-079" not in by_id:
        recov_errors.append("ttf-r12-079 missing")
    else:
        fo = by_id["ttf-r12-079"][1].get("future_outcome") or {}
        recovery = fo.get("recovery")
        recov_detail = {"recovery": recovery, "future_outcome_keys": sorted(fo.keys())}
        if not isinstance(recovery, dict):
            recov_errors.append(f"ttf-r12-079 future_outcome.recovery missing/not object: {recovery!r}")
        else:
            blob = json.dumps(recovery)
            correct_gate = recovery.get("correct_gate")
            if not (isinstance(correct_gate, str) and "ACCEPT" in correct_gate):
                recov_errors.append(
                    f"ttf-r12-079 recovery.correct_gate does not name ACCEPT: {correct_gate!r}"
                )
            mwc = recovery.get("missed_window_cost")
            if mwc is None or (isinstance(mwc, str) and not mwc.strip()):
                recov_errors.append(
                    f"ttf-r12-079 recovery.missed_window_cost missing/empty: {mwc!r}"
                )
            if "ACCEPT" not in blob:
                recov_errors.append("ttf-r12-079 recovery JSON does not contain ACCEPT")
            if "missed_window_cost" not in recovery and "missed window" not in blob.lower():
                recov_errors.append("ttf-r12-079 recovery does not name missed window cost")
    results.append(
        {
            "n": 20,
            "name": "079 future_outcome.recovery names ACCEPT + missed window cost",
            "pass": not recov_errors,
            "errors": recov_errors,
            "warnings": [],
            "detail": recov_detail,
        }
    )

    # ------------------------------------------------------------------
    # 21. 080 partnered negative total ≈ -0.50 and un_netted_loss present
    # ------------------------------------------------------------------
    pn_errors = []
    pn_detail = {}
    if "ttf-r12-080" not in by_id:
        pn_errors.append("ttf-r12-080 missing")
    else:
        obj = by_id["ttf-r12-080"][1]
        total = (obj.get("reward_components") or {}).get("total")
        fo = obj.get("future_outcome") or {}
        un = fo.get("un_netted_loss")
        pn_detail = {"total": total, "un_netted_loss": un}
        if not finite(total):
            pn_errors.append(f"ttf-r12-080 total not finite: {total!r}")
        elif abs(float(total) - (-0.50)) > 1e-6:
            pn_errors.append(f"ttf-r12-080 total {total!r} not ≈ -0.50 (diff {abs(float(total)+0.50)})")
        if un is None or (isinstance(un, str) and not un.strip()):
            pn_errors.append(f"ttf-r12-080 future_outcome.un_netted_loss missing/empty: {un!r}")
        sd = obj.get("safety_decision") or {}
        if sd.get("decision") != "MODIFY" or sd.get("correctness") != "correct":
            pn_errors.append(
                f"ttf-r12-080 expected correct MODIFY, got {sd.get('decision')}/{sd.get('correctness')}"
            )
    results.append(
        {
            "n": 21,
            "name": "080 partnered negative total ≈ -0.50 and un_netted_loss present",
            "pass": not pn_errors,
            "errors": pn_errors,
            "warnings": [],
            "detail": pn_detail,
        }
    )

    out = {
        "batch": str(BATCH),
        "notes": str(NOTES),
        "n_records": len(records),
        "ids": [obj.get("id") for _, obj, _ in records],
        "checks": results,
        "all_pass": all(r["pass"] for r in results),
        "failed": [r["n"] for r in results if not r["pass"]],
    }
    Path("/tmp/ttf-r12-validate.json").write_text(json.dumps(out, indent=2, default=str) + "\n")
    print(json.dumps({"all_pass": out["all_pass"], "failed": out["failed"], "n_records": out["n_records"], "ids": out["ids"]}, indent=2))
    for r in results:
        status = "PASS" if r["pass"] else "FAIL"
        print(f"[{status}] {r['n']:02d} {r['name']}")
        for e in r["errors"][:20]:
            print(f"    ERROR: {e}")
        if len(r["errors"]) > 20:
            print(f"    ... {len(r['errors'])-20} more errors")


if __name__ == "__main__":
    main()
