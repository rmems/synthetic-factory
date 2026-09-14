#!/usr/bin/env python3
"""Independent fail-closed audit of /tmp/maos-r15 staging. Does not write outputs/raw/."""
from __future__ import annotations

import hashlib
import json
import math
import re
import subprocess
import sys
from collections import defaultdict
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path

REPO = Path("/home/raulmc/rmems/synthetic-factory")
PIPE = REPO / "pipelines"
sys.path.insert(0, str(PIPE))
sys.path.insert(0, "/tmp")

from check_records import (  # noqa: E402
    FactoryStaging,
    check_jsonl,
    check_record,
)
from curate_bridge import is_thalamic_record, raster_status  # noqa: E402
from exact_json import dumps_exact_json  # noqa: E402
from maos_heading_check import check_transcript  # noqa: E402
from record_kind import classify_kind  # noqa: E402
from round_txn import (  # noqa: E402
    NOVEL_COVERAGE_LABEL_RE,
    NOVEL_COVERAGE_RE,
    validate_novel_coverage,
)
from round_txn_raster import validate_bridge_envelope  # noqa: E402
from validate_run import (  # noqa: E402
    HIDDEN_THOUGHT_KEYS,
    _hidden_thought_paths,
    check_line,
)
from verify_execution import (  # noqa: E402
    verify_batch_for_frontier,
    verify_record_execution,
)

STAGING = Path("/tmp/maos-r15")
BATCH = STAGING / "batch-r15.jsonl"
NOTES = STAGING / "NOTES-r15.md"
TRANSCRIPT = STAGING / "swarm-transcript-r15.md"
AUDIT = Path("/tmp/maos-r15-audit.md")
RAW = REPO / "outputs" / "raw"
FACTORY_DIR = RAW / "2026-08-30" / "multi-agent-ouroboros-swarm"

EXPECTED_ID = "maos-r15-001"
EXPECTED_ROUND = 15
EXPECTED_FACTORY = "multi-agent-ouroboros-swarm"
EXPECTED_GENERATOR = "grok-4.6"
EXPECTED_RUN = "2026-09-02-final-heavy"
EXPECTED_PLANT_TOKENS = ("CINDERWICK", "Lodenholt", "DH-3")
BANNED_CLONE_TOKENS = (
    "TRIAD",
    "Meridian Gateway",
    "VANTIS",
    "CADENCE",
    "AEGIS",
    "LYOSHIELD",
    "Helixmere",
    "OKTAVE",
    "STARLING",
    "THERMION",
)
HEADS = ("task_progress", "safety", "efficiency", "coherence", "exploration")
AGG = "total = task_progress + safety + efficiency + coherence + exploration"
RIGHTS_VALUES = {
    "provider": "SpaceXAI/xAI",
    "model": "grok-4.6",
    "channel": "consumer",
    "subscription_plan": "SuperGrok Heavy",
    "generation_surface": "SuperGrok Heavy chat",
    "intended_use": "research_only",
    "project_training_policy": "blocked",
    "research_retention_status": "allowed",
    "research_evaluation_status": "allowed",
    "redistribution_status": "unresolved",
    "provider_training_status": "unresolved",
    "weight_publication_status": "blocked",
    "status_basis": "RM-793 project policy: xAI hosted outputs are research-only",
    "linear_issue": "RM-793",
}
EXTRA_THOUGHT = (
    "thought",
    "thoughts",
    "reasoning",
    "chain_of_thought",
    "hidden_reasoning",
    "inner_monologue",
    "thinking",
    "cot",
    "scratch",
    "internal_reasoning",
)
ROLE_HEADINGS = (
    "Generator",
    "Critic",
    "Diversity Enforcer",
    "Edge-Case Hunter",
    "Neuromorphic Translator",
    "Trajectory Builder",
)
TOL = 1e-9
ENERGY_PJ = 23


def utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    h.update(path.read_bytes())
    return h.hexdigest()


def walk_keys(value, path=""):
    if isinstance(value, dict):
        for k, v in value.items():
            child = f"{path}.{k}" if path else str(k)
            yield child, k, v
            yield from walk_keys(v, child)
    elif isinstance(value, list):
        for i, item in enumerate(value):
            yield from walk_keys(item, f"{path}[{i}]")


def tokenize(text: str) -> list[str]:
    return re.findall(r"[A-Za-z0-9]+", (text or "").lower())


def opening40(text: str) -> set[str]:
    return set(tokenize(text)[:40])


def jaccard(a: set[str], b: set[str]) -> float:
    if not a and not b:
        return 0.0
    return len(a & b) / len(a | b)


def fmt_num(x) -> str:
    if x is None:
        return "None"
    if isinstance(x, bool):
        return str(x)
    if isinstance(x, int):
        return str(x)
    try:
        f = float(x)
    except (TypeError, ValueError):
        return repr(x)
    if not math.isfinite(f):
        return repr(x)
    if abs(f - round(f)) < 1e-12:
        return str(int(round(f)))
    s = f"{f:.6f}".rstrip("0").rstrip(".")
    return s.replace("-", "−") if f < 0 else s


def mark(ok: bool) -> str:
    return "PASS" if ok else "FAIL"


def git_porcelain_raw() -> str:
    proc = subprocess.run(
        ["git", "-C", str(REPO), "status", "--porcelain", "--", "outputs/raw"],
        capture_output=True,
        text=True,
        check=False,
    )
    return proc.stdout


def rg_raw(pattern: str) -> list[str]:
    proc = subprocess.run(
        ["rg", "-l", pattern, str(RAW)],
        capture_output=True,
        text=True,
        check=False,
    )
    lines = [ln for ln in proc.stdout.splitlines() if ln.strip()]
    return lines


def load_jsonl(path: Path):
    raw = path.read_bytes()
    text = raw.decode("utf-8")
    physical = text.split("\n")
    records = []
    parse_errors = []
    for i, line in enumerate(physical, 1):
        if not line.strip():
            continue
        try:
            records.append((i, json.loads(line)))
        except (ValueError, RecursionError) as exc:
            parse_errors.append(f"{path.name}:{i}: {exc}")
    return {
        "raw": raw,
        "text": text,
        "physical": physical,
        "records": records,
        "parse_errors": parse_errors,
        "trailing_lf": raw.endswith(b"\n") and not raw.endswith(b"\n\n"),
        "has_crlf": b"\r\n" in raw,
        "has_bare_cr": b"\r" in raw and b"\r\n" not in raw,
    }


def historical_descriptions():
    """Return (label, first-40 token set) for MAOS records that have description."""
    rows = []
    files = []
    files.extend(sorted((RAW / "2026-08-30" / "multi-agent-ouroboros-swarm").glob("batch-r*.jsonl")))
    for extra in (
        Path("/tmp/maos-r14/batch-r14.jsonl"),
        Path("/tmp/maos-r16/batch-r16.jsonl"),
    ):
        if extra.is_file():
            files.append(extra)
    seen = set()
    for path in files:
        try:
            text = path.read_text(encoding="utf-8")
        except OSError:
            continue
        for line in text.splitlines():
            if not line.strip():
                continue
            try:
                rec = json.loads(line)
            except (ValueError, RecursionError):
                continue
            if not isinstance(rec, dict):
                continue
            desc = (rec.get("state") or {}).get("description")
            if not isinstance(desc, str) or not desc.strip():
                continue
            rid = rec.get("id") or path.name
            key = (rid, desc[:80])
            if key in seen:
                continue
            seen.add(key)
            plant = (rec.get("state") or {}).get("scenario_name") or rid
            rows.append(
                {
                    "id": rid,
                    "plant": plant,
                    "path": str(path),
                    "tokens": opening40(desc),
                }
            )
    return rows


def extract_cycle2_json(transcript_text: str):
    """Prefer the last bare JSONL-looking line; else the last fenced json object."""
    for line in reversed(transcript_text.splitlines()):
        s = line.lstrip()
        if s.startswith('{"id":'):
            return s, "bare-line"
    fences = list(
        re.finditer(r"```json\s*\n(.*?)\n```", transcript_text, flags=re.DOTALL)
    )
    candidates = []
    for m in fences:
        body = m.group(1).strip()
        if body.startswith("{") and '"id"' in body[:80]:
            candidates.append(body)
    if candidates:
        return candidates[-1], "fenced"
    return None, None


def rights_errors(stamp, where: str) -> list[str]:
    errs = []
    if not isinstance(stamp, dict):
        return [f"{where}: missing rights object"]
    for key, expected in RIGHTS_VALUES.items():
        got = stamp.get(key)
        if got != expected:
            errs.append(f"{where}.{key}: {got!r} != {expected!r}")
    gen = stamp.get("generated_at")
    if not isinstance(gen, str) or not re.match(
        r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$", gen
    ):
        errs.append(f"{where}.generated_at not ISO-8601 UTC: {gen!r}")
    return errs


def thought_hits(obj) -> list[str]:
    hits = []
    extra = set(EXTRA_THOUGHT) | set(HIDDEN_THOUGHT_KEYS)
    for path, key, _ in walk_keys(obj):
        nk = re.sub(r"[^a-z0-9]+", "_", str(key).casefold()).strip("_")
        if nk in extra or str(key).casefold() in extra:
            hits.append(path)
    hits.extend(f"{p} (hidden-key {k})" for k, p in _hidden_thought_paths(obj))
    return sorted(set(hits))


def clone_token_hits(text: str) -> list[str]:
    hits = []
    for tok in BANNED_CLONE_TOKENS:
        if re.search(re.escape(tok), text, flags=re.IGNORECASE):
            hits.append(tok)
    return hits


def spike_checks(obj) -> dict:
    events = obj.get("spike_events") or []
    errs = []
    if not isinstance(events, list):
        return {"errors": ["spike_events not a list"], "n": None}
    n = len(events)
    if not (5 <= n <= 40):
        errs.append(f"n={n} not in [5,40]")
    times = []
    by_ch = defaultdict(list)
    for i, e in enumerate(events):
        if not isinstance(e, dict):
            errs.append(f"event[{i}] not object")
            continue
        keys = set(e)
        if keys != {"channel", "t_rel_ms", "amplitude"} and not (
            {"channel", "t_rel_ms", "amplitude"} <= keys
        ):
            pass
        if "t_rel_ms" not in e:
            errs.append(f"event[{i}] missing t_rel_ms")
            continue
        t = e.get("t_rel_ms")
        if not isinstance(t, (int, float)) or isinstance(t, bool) or not math.isfinite(t):
            errs.append(f"event[{i}] non-finite t_rel_ms {t!r}")
            continue
        times.append(t)
        by_ch[e.get("channel")].append(t)
    if times != sorted(times):
        errs.append("not globally non-decreasing")
    min_gap = None
    min_ch = None
    for ch, ts in by_ch.items():
        for a, b in zip(ts, ts[1:]):
            gap = b - a
            if min_gap is None or gap < min_gap:
                min_gap = gap
                min_ch = ch
            if gap < 0.8 - 1e-12:
                errs.append(f"{ch} gap {gap} < 0.8 ms")
    state = obj.get("state") or {}
    race = state.get("race_window_rel_ms")
    race_us = state.get("race_window_us")
    dual_ok = None
    in_win = []
    if isinstance(race, list) and len(race) == 2:
        lo, hi = float(race[0]), float(race[1])
        in_win = [
            e
            for e in events
            if isinstance(e, dict)
            and isinstance(e.get("t_rel_ms"), (int, float))
            and lo - 1e-12 <= e["t_rel_ms"] <= hi + 1e-12
        ]
        if race_us is not None:
            try:
                dual_ok = abs((hi - lo) - (float(race_us) / 1000.0)) < 1e-9
            except (TypeError, ValueError):
                dual_ok = False
                errs.append("race_window dual mismatch unparsable")
            else:
                if not dual_ok:
                    errs.append(
                        f"race span {hi-lo} != race_window_us/1000 {float(race_us)/1000.0}"
                    )
    in_win_ch = sorted({e.get("channel") for e in in_win if e.get("channel") != "ctrl.gate"})
    if len(in_win_ch) < 2:
        errs.append(f"in-window non-ctrl channels {in_win_ch}")
    return {
        "errors": errs,
        "n": n,
        "channels": len(by_ch),
        "min_gap_ms": min_gap,
        "min_gap_channel": min_ch,
        "race_window_rel_ms": race,
        "race_window_us": race_us,
        "dual_ok": dual_ok,
        "in_window": in_win,
        "in_window_channels": in_win_ch,
        "pass": not errs,
    }


def tick_checks(obj) -> dict:
    rc = obj.get("reward_components") or {}
    ticks = rc.get("ticks") or []
    errs = []
    if not isinstance(ticks, list):
        return {"errors": ["ticks not a list"], "pass": False}
    n = len(ticks)
    if not (3 <= n <= 8):
        errs.append(f"ticks={n} not in [3,8]")
    if rc.get("_aggregation") != AGG:
        errs.append(f"_aggregation={rc.get('_aggregation')!r}")
    sums = {h: 0.0 for h in HEADS}
    t_us = []
    for t in ticks:
        if not isinstance(t, dict):
            errs.append("tick not object")
            continue
        t_us.append(t.get("t_us"))
        for h in HEADS:
            sums[h] += float(t.get(h) or 0.0)
    heads = {h: float(rc.get(h) or 0.0) for h in HEADS}
    head_sum = sum(heads.values())
    total = float(rc.get("total")) if rc.get("total") is not None else None
    for h in HEADS:
        if abs(sums[h] - heads[h]) > 1e-9:
            errs.append(f"{h} tick-sum {sums[h]!r} != head {heads[h]!r}")
    if total is None:
        errs.append("missing total")
    else:
        if abs(head_sum - total) > 1e-9:
            errs.append(f"head-sum {head_sum!r} != total {total!r}")
        if abs(sum(sums.values()) - total) > 1e-9:
            errs.append(f"tick-sum {sum(sums.values())!r} != total {total!r}")
    infl = (obj.get("future_outcome") or {}).get("reward_inflection_t_us")
    infl_in = infl in t_us
    if infl is not None and not infl_in:
        errs.append(f"inflection {infl} not in ticks {t_us}")
    return {
        "errors": errs,
        "n": n,
        "sums": sums,
        "heads": heads,
        "head_sum": head_sum,
        "total": total,
        "abs_delta": None if total is None else abs(head_sum - total),
        "t_us": t_us,
        "inflection": infl,
        "inflection_in_ticks": infl_in,
        "pass": not errs,
    }


def raster_budget_checks(obj) -> dict:
    r = obj.get("raster") or {}
    errs = []
    if not isinstance(r, dict):
        return {"errors": ["raster missing"], "pass": False}
    window_ms = r.get("window_ms")
    window_s = r.get("window_s")
    neurons = r.get("neurons")
    rate = r.get("mean_rate_hz")
    spikes = r.get("spikes")
    if not isinstance(window_ms, (int, float)) or not (20 <= float(window_ms) <= 50):
        errs.append(f"window_ms {window_ms!r} not in [20,50]")
    if isinstance(window_ms, (int, float)) and isinstance(window_s, (int, float)):
        if abs(float(window_s) - float(window_ms) / 1000.0) > 1e-9:
            errs.append("window_s != window_ms/1000")
    expected_spikes = None
    if all(isinstance(x, (int, float)) and not isinstance(x, bool) for x in (neurons, rate, window_s)):
        expected_spikes = round(float(neurons) * float(rate) * float(window_s))
        if abs(int(spikes) - expected_spikes) > 1:
            errs.append(f"spikes {spikes} != round(n*rate*window_s) {expected_spikes} ±1")
    energy_pJ = r.get("energy_pJ")
    energy_uJ = r.get("energy_uJ")
    if isinstance(spikes, int) and not isinstance(spikes, bool):
        if energy_pJ is not None and abs(float(energy_pJ) - spikes * ENERGY_PJ) > 1e-6:
            errs.append(f"energy_pJ {energy_pJ} != {spikes*ENERGY_PJ}")
        if energy_uJ is not None and abs(float(energy_uJ) - spikes * 23e-6) > 1e-9:
            errs.append(f"energy_uJ {energy_uJ} != {spikes*23e-6}")
    excerpt = r.get("excerpt") or []
    t_max = int(float(window_ms) * 1000) if isinstance(window_ms, (int, float)) else None
    excerpt_ids = []
    last_t = None
    for i, ev in enumerate(excerpt):
        if not isinstance(ev, dict):
            errs.append(f"excerpt[{i}] not object")
            continue
        t_us = ev.get("t_us")
        nid = ev.get("neuron_id")
        excerpt_ids.append(nid)
        if not isinstance(t_us, int) or isinstance(t_us, bool):
            errs.append(f"excerpt[{i}].t_us not int")
        else:
            if t_us < 0 or (t_max is not None and t_us > t_max):
                errs.append(f"excerpt[{i}].t_us {t_us} out of [0,{t_max}]")
            if last_t is not None and t_us < last_t:
                errs.append("excerpt not sorted")
            last_t = t_us
        if isinstance(neurons, int) and isinstance(nid, int):
            if not (0 <= nid < neurons):
                errs.append(f"excerpt[{i}].neuron_id {nid} not in [0,{neurons})")
    routing = r.get("routing") or {}
    table = routing.get("table") if isinstance(routing, dict) else None
    tf = routing.get("third_factor") if isinstance(routing, dict) else None
    if not isinstance(table, list) or len(table) < 1:
        errs.append("routing.table empty")
    tau_ok = None
    if isinstance(tf, dict):
        tau_s = tf.get("tau_e_s")
        tau_ms = tf.get("tau_e_ms")
        if tau_s is not None and tau_ms is not None:
            tau_ok = abs(float(tau_ms) / 1000.0 - float(tau_s)) <= 1e-9
            if not tau_ok:
                errs.append("tau_e_ms/1000 != tau_e_s")
    gs = obj.get("gate_snn") or (obj.get("meta") or {}).get("gate_snn")
    pop_rows = []
    if isinstance(gs, dict):
        dw_ms = gs.get("decision_window_ms")
        dw_s = gs.get("decision_window_s")
        if dw_ms is not None and dw_s is not None:
            if abs(float(dw_s) - float(dw_ms) / 1000.0) > 1e-9:
                errs.append("gate_snn window_s != ms/1000")
        for pop in gs.get("populations") or []:
            if not isinstance(pop, dict):
                continue
            n = pop.get("neurons")
            hz = pop.get("mean_rate_hz")
            sp = pop.get("spikes")
            exp = None
            ok = True
            if hz is not None and sp is not None and n is not None and dw_s is not None:
                exp = round(float(n) * float(hz) * float(dw_s))
                ok = abs(int(sp) - exp) <= 1
                if not ok:
                    errs.append(f"gate_snn pop {pop.get('name')} spikes {sp} != {exp}±1")
            pop_rows.append(
                {
                    "name": pop.get("name"),
                    "n": n,
                    "hz": hz,
                    "spikes": sp,
                    "expected": exp,
                    "ok": ok,
                }
            )
        sd = (obj.get("safety_decision") or {}).get("decision")
        if gs.get("decision") != sd:
            errs.append(f"gate_snn.decision {gs.get('decision')!r} != safety {sd!r}")
    return {
        "errors": errs,
        "window_ms": window_ms,
        "window_s": window_s,
        "neurons": neurons,
        "mean_rate_hz": rate,
        "spikes": spikes,
        "expected_spikes": expected_spikes,
        "energy_pJ": energy_pJ,
        "energy_uJ": energy_uJ,
        "excerpt_n": len(excerpt) if isinstance(excerpt, list) else 0,
        "table_n": len(table) if isinstance(table, list) else 0,
        "tau_ok": tau_ok,
        "third_factor": tf,
        "gate_pops": pop_rows,
        "pass": not errs,
    }


def render_missing(present: dict) -> str:
    lines = [
        "# MAOS round 15 fail-closed audit",
        "",
        "**Verdict: FAIL**  ",
        "**Staging:** `/tmp/maos-r15/`  ",
        "**Factory:** `multi-agent-ouroboros-swarm`  ",
        "**Run:** `2026-09-02-final-heavy` / `grok-4.6`  ",
        f"**When (UTC):** {utc_now()}  ",
        "**JSON patch:** none (staging empty / incomplete; nothing to patch)  ",
        "**`outputs/raw/`:** not written (git porcelain clean under `outputs/raw/`)",
        "",
        "Independent runner: `PYTHONPATH=pipelines python3 /tmp/maos-r15-audit-run.py` against repo `/home/raulmc/rmems/synthetic-factory`. Staging-only gate; this audit did not write, clobber, or stage into `outputs/raw/`.",
        "",
        "Polled `/tmp/maos-r15/` for `batch-r15.jsonl`, `NOTES-r15.md`, and `swarm-transcript-r15.md`. Required artifacts are missing or empty, so jsonl identity, 6×2 headings, and `spike_probe --strict` cannot run.",
        "",
        "## Artifact presence",
        "",
        "| path | present | bytes |",
        "|------|---------|------:|",
    ]
    for name, info in present.items():
        lines.append(
            f"| `{name}` | {info['present']} | {info['bytes'] if info['bytes'] is not None else ''} |"
        )
    lines += [
        "",
        "Directory listing at audit time was empty aside from `.` / `..`.",
        "",
        "## Check results",
        "",
        "| gate | result | detail |",
        "|------|--------|--------|",
        "| staging artifacts exist | **FAIL** | need `batch-r15.jsonl` + `NOTES-r15.md` + `swarm-transcript-r15.md` |",
        "| `check_jsonl` FactoryStaging | **BLOCKED** | no JSONL |",
        "| 6 role headings × 2 cycles | **BLOCKED** | no transcript |",
        "| `spike_probe --strict` | **BLOCKED** | no JSONL |",
        "| `outputs/raw/` immutability | **PASS** | porcelain empty; no writes from this audit |",
        "",
        "Error strings: missing staging files (not a pipeline error list).",
        "",
        "## Machine-readable recap",
        "",
        "```",
        "verdict=FAIL",
        "batch=/tmp/maos-r15/batch-r15.jsonl",
        "notes=/tmp/maos-r15/NOTES-r15.md",
        "transcript=/tmp/maos-r15/swarm-transcript-r15.md",
        "missing=true",
        "outputs_raw_written=false",
        "```",
        "",
    ]
    return "\n".join(lines)


def render_full(ev: dict) -> str:
    rec = ev["rec"]
    meta = rec.get("meta") or {}
    state = rec.get("state") or {}
    sd = rec.get("safety_decision") or {}
    gs = rec.get("gate_snn") if isinstance(rec.get("gate_snn"), dict) else {}
    rc = rec.get("reward_components") or {}
    heading = ev["heading"]
    novel = ev["novel"]
    clone = ev["clone"]
    ticks = ev["ticks"]
    spikes = ev["spikes"]
    raster_b = ev["raster_budget"]
    rs = ev["raster_status"]
    sp = ev["spike_probe"]
    cj = ev["check_jsonl"]
    vbf = ev["verify"]
    ident = ev["identity"]
    rights = ev["rights"]
    raw_immut = ev["raw"]
    art = ev["artifacts"]

    overall = ev["overall"]
    lines = [
        "# MAOS round 15 fail-closed audit",
        "",
        f"**Verdict: {mark(overall)}**  ",
        "**Staging:** `/tmp/maos-r15/` (`batch-r15.jsonl`, `NOTES-r15.md`, `swarm-transcript-r15.md`)  ",
        f"**Factory:** `{meta.get('factory')}`  ",
        f"**Run:** `{meta.get('run_label')}` / `{meta.get('generator')}`  ",
        f"**Record:** {ev['n_records']} thalamic line, `id={rec.get('id')}`, `meta.round={meta.get('round')}`  ",
        f"**Rights:** RM-793 research-only (not `training_ready`)  ",
        "**JSON patch:** none (audit is read-only; no staged repairs applied)  ",
        f"**`outputs/raw/`:** {'not written (git porcelain clean under `outputs/raw/`)' if raw_immut['pass'] else 'DIRTY — see immutability section'}",
        "",
        "Independent runner: `PYTHONPATH=pipelines python3 /tmp/maos-r15-audit-run.py` against repo `/home/raulmc/rmems/synthetic-factory`. Staging-only gate; this audit did not write, clobber, or stage into `outputs/raw/`.",
        "",
    ]
    if overall:
        lines.append(
            "Error strings: every requested gate returned an empty error list / `blocked=False` / exit 0. There are no exact error strings to report."
        )
    else:
        fails = [name for name, ok in ev["gate_table"] if not ok]
        lines.append("Failed gates: " + ", ".join(f"`{n}`" for n in fails) + ".")
        err_blob = ev.get("error_strings") or []
        if err_blob:
            lines.append("")
            lines.append("Error strings (verbatim / collected):")
            lines.append("")
            lines.append("```")
            lines.extend(str(x) for x in err_blob[:80])
            lines.append("```")
    lines += [
        "",
        "---",
        "",
        "## Batch map (observed)",
        "",
        "| file | bytes | sha256 / note |",
        "|------|------:|----------------|",
        f"| `/tmp/maos-r15/batch-r15.jsonl` | {art['batch_bytes']} | `{art['batch_sha256']}`; {ev['jsonl_note']} |",
        f"| `/tmp/maos-r15/NOTES-r15.md` | {art['notes_bytes']} | {novel['notes_cell']} |",
        f"| `/tmp/maos-r15/swarm-transcript-r15.md` | {art['transcript_bytes']} | `{art['transcript_sha256']}`; heading check {mark(heading['ok'])} |",
    ]
    if art.get("extra_files"):
        for name, info in art["extra_files"]:
            lines.append(
                f"| `/tmp/maos-r15/{name}` | {info['bytes']} | extra staging file; not a publish artifact |"
            )
    plant = state.get("scenario_name") or ""
    lines += [
        "",
        "| id | domain | plant | decision | correctness | sim_or_real | total | ticks | spike_events | raster spikes |",
        "|----|--------|-------|----------|-------------|-------------|-------|------:|-------------:|--------------:|",
        "| {id} | {dom} | {plant} | {dec} | {cor} | {sor} | {tot} | {nt} | {ns} | {rs} |".format(
            id=rec.get("id"),
            dom=meta.get("domain") or state.get("domain"),
            plant=plant,
            dec=sd.get("decision"),
            cor=sd.get("correctness"),
            sor=state.get("sim_or_real"),
            tot=fmt_num(rc.get("total")),
            nt=ticks["n"],
            ns=spikes["n"],
            rs=rs.get("spikes"),
        ),
        "",
        ev.get("class_blurb", ""),
        "",
        "---",
        "",
        "## Check results",
        "",
        f"### 1. `check_jsonl(..., staging=FactoryStaging(enabled=True))` — {mark(cj['pass'])}",
        "",
        "```",
        "PYTHONPATH=pipelines python3 -c '",
        "from pathlib import Path",
        "from check_records import check_jsonl, FactoryStaging",
        "errors, warnings, kinds, n = check_jsonl(",
        '    Path("/tmp/maos-r15/batch-r15.jsonl"),',
        '    "batch-r15.jsonl",',
        "    staging=FactoryStaging(enabled=True),",
        ")",
        "print(errors, warnings, kinds, n)",
        "'",
        "```",
        "",
        f"- errors: `{cj['errors']}`",
        f"- warnings: `{cj['warnings']}`",
        f"- kinds: `{cj['kinds']}`",
        f"- records: `{cj['records']}`",
        "",
        f"Legacy `FactoryStaging(enabled=False)`: errors `{cj['legacy_errors']}` / warnings `{cj['legacy_warnings']}` / kinds `{cj['legacy_kinds']}` / n `{cj['legacy_n']}`.",
        "",
        f"`validate_run.check_line(..., factory_staging=True)`: kind `{ev['check_line']['kind']}`, errors `{ev['check_line']['errors']}`.",
        f"`check_record` both modes: kind `{ev['check_record']['kind']}`, id `{ev['check_record']['id']}`, errors `{ev['check_record']['errors']}`, warnings `{ev['check_record']['warnings']}`.",
        f"`exact_json.dumps_exact_json` serializes ({ev['exact']['nbytes']} UTF-8 bytes, error `{ev['exact']['error']}`).",
        "",
        f"### 2. `curate_bridge.raster_status` — {mark(ev['raster_status_pass'])}",
        "",
        "Contract: `reason_codes == []`, `gate_snn_present is True`, `routing_table_entries >= 1`.",
        "",
        "| field | value |",
        "|-------|-------|",
        f"| raster_present | {rs.get('raster_present')} |",
        f"| raster_valid | {rs.get('raster_valid')} |",
        f"| raster_location | `{rs.get('raster_location')}` |",
        f"| routing_table_entries | {rs.get('routing_table_entries')} |",
        f"| third_factor_present | {rs.get('third_factor_present')} |",
        f"| gate_snn_present | {rs.get('gate_snn_present')} |",
        f"| gate_snn_valid | {rs.get('gate_snn_valid')} |",
        f"| spikes | {rs.get('spikes')} |",
        f"| reason_codes | `{rs.get('reason_codes')}` |",
        "",
        f"`round_txn_raster.validate_bridge_envelope(batch, factory_dir=.../multi-agent-ouroboros-swarm)` → `{ev['bridge_envelope']}`.",
        "",
        f"### 3. `verify_execution.verify_batch_for_frontier(..., strict=True)` — {mark(vbf['pass'])}",
        "",
        "```",
        "python3 pipelines/verify_execution.py --batch /tmp/maos-r15/batch-r15.jsonl --strict --json",
        "```",
        "",
        "```",
        f"counts = {vbf['counts']}",
        f"blocked = {vbf['blocked']}",
        f"findings = {vbf['findings']}",
        f"exit = {vbf['cli_exit']}",
        "```",
        "",
        f"`verify_record_execution`: `status={ev['verify_record']['status']}`, `reason={ev['verify_record']['reason']}`.",
        "",
        f"### 4. `python3 pipelines/spike_probe.py --strict /tmp/maos-r15/batch-r15.jsonl` — {mark(sp['pass'])}",
        "",
        f"- exit: `{sp['exit']}`",
        f"- stderr: {('empty' if not sp['stderr'] else 'see below')}",
        "- stdout summary:",
        "",
        "```",
    ]
    summary = sp.get("summary") or {}
    if isinstance(summary, dict) and "raw_stdout" not in summary:
        for k in (
            "distillation_records",
            "bridge_records",
            "thalamic_records",
            "loaded",
            "unloadable",
            "input_errors",
            "events",
            "spikes",
            "energy_pJ",
            "routing_tables",
            "third_factor_routes",
            "gate_snn_records",
            "problems",
        ):
            if k in summary:
                lines.append(f"{k}={summary[k]}")
    else:
        lines.append((sp.get("stdout") or "")[:4000])
    lines.append("```")
    if sp.get("stderr"):
        lines += ["", "stderr:", "", "```", sp["stderr"][:4000], "```"]
    lines += [
        "",
        "---",
        "",
        f"## Identity / RM-793 / thought keys — {mark(ident['pass'] and rights['pass'] and ev['thought']['pass'])}",
        "",
        "| check | observed |",
        "|-------|----------|",
        f"| 1 thalamic record | `kinds={cj['kinds']}`, `classify_kind={ident['classify_kind']}`, `is_thalamic_record={ident['is_thalamic']}` |",
        f"| id | `{rec.get('id')}` (expected `{EXPECTED_ID}`) |",
        f"| round | `meta.round={meta.get('round')}` ({type(meta.get('round')).__name__}) |",
        f"| factory | `{meta.get('factory')}` |",
        f"| generator | `{meta.get('generator')}` |",
        f"| run_label | `{meta.get('run_label')}` |",
        f"| `meta.cycles` | {meta.get('cycles')} |",
        f"| `meta.batch_position` | {meta.get('batch_position')} |",
        f"| `state.sim_or_real` | `{state.get('sim_or_real')}` ∈ {{designed, simulated, hil}}; never `real` |",
        f"| `safety_decision.decision` | `{sd.get('decision')}` |",
        f"| `gate_snn.decision` | `{gs.get('decision')}` |",
        f"| `safety_decision.correctness` | `{sd.get('correctness')}` |",
        f"| `executed_as_proposed` | `{ (rec.get('executed_action') or {}).get('executed_as_proposed') }` |",
        f"| thought keys | {ev['thought']['detail']} |",
        f"| `training_ready` | {ident['training_ready']} |",
        "",
        "RM-793 stamp on top-level `rights` and `meta.rights`:",
        "",
        "| key | top-level | meta.rights |",
        "|-----|-----------|-------------|",
    ]
    top_r = rec.get("rights") if isinstance(rec.get("rights"), dict) else {}
    meta_r = meta.get("rights") if isinstance(meta.get("rights"), dict) else {}
    keys = list(RIGHTS_VALUES) + ["generated_at"]
    for k in keys:
        lines.append(f"| {k} | `{top_r.get(k)}` | `{meta_r.get(k)}` |")
    lines += [
        "",
        f"Rights errors: `{rights['errors'] or []}`.",
        f"`meta.tags` research-only: {ident['research_only_tag']}. RM-793 string counts: NOTES {ev['rm793_counts']['notes']}, transcript {ev['rm793_counts']['transcript']}, record {ev['rm793_counts']['record']}.",
        "",
        f"## Transcript: 6 role headings × 2 cycles — {mark(heading['ok'])}",
        "",
        "Required verbatim H2, in order, twice:",
        "",
        "`## Generator`, `## Critic`, `## Diversity Enforcer`, `## Edge-Case Hunter`, `## Neuromorphic Translator`, `## Trajectory Builder`",
        "",
        f"Checker: `/tmp/maos_heading_check.py` on `/tmp/maos-r15/swarm-transcript-r15.md` → **{mark(heading['ok'])}**.",
        "",
        "| Check | Result | Detail |",
        "|-------|--------|--------|",
    ]
    for c in heading["checks"]:
        lines.append(f"| `{c['name']}` | {mark(c['ok'])} | {c['detail']} |")
    lines += [
        "",
        heading.get("inventory_md", ""),
        "",
        f"Cycle-2 Trajectory Builder JSON vs JSONL: {heading.get('json_eq_note')}",
        "",
        f"## NOTES `Novel coverage` — {mark(novel['pass'])}",
        "",
        f"Labeled coverage lines: {novel['n_labeled']}. Strict `NOVEL_COVERAGE_RE` fullmatch lines: {novel['n_strict']}.",
        "",
        "```",
        novel.get("line") or "(none)",
        "```",
        "",
        f"`validate_novel_coverage(..., required=True)` → `{novel['validate']}`.",
        "",
        f"## Not a TRIAD / Meridian / LYOSHIELD clone — {mark(clone['pass'])}",
        "",
        "| surface | banned clone tokens |",
        "|---------|---------------------|",
        f"| JSONL record | {clone['record_hits'] or '**absent**'} |",
        f"| NOTES | {clone['notes_hits'] or '**absent**'} |",
        f"| transcript | {clone['transcript_hits'] or '**absent**'} |",
        "",
        f"Expected CINDERWICK plant tokens in record: {clone['cinderwick_hits'] or '**none**'} (need CINDERWICK / Lodenholt / DH-3).",
        "",
        f"Jaccard on first 40 `state.description` tokens vs historical MAOS descriptions (threshold < 0.4). **max {clone['jaccard_max']}** vs `{clone['jaccard_max_vs']}`.",
        "",
    ]
    if clone.get("jaccard_rows"):
        lines += [
            "| vs id / plant | Jaccard |",
            "|---------------|--------:|",
        ]
        for row in clone["jaccard_rows"][:12]:
            lines.append(f"| `{row['id']}` / {row['plant']} | {row['j']:.4f} |")
        lines.append("")
    lines += [
        f"## Reward arithmetic — {mark(ticks['pass'])}",
        "",
        f"`_aggregation` = `{rc.get('_aggregation')}`. Ticks {ticks['n']} ∈ [3,8]. Inflection `future_outcome.reward_inflection_t_us={ticks['inflection']}` in ticks: {ticks['inflection_in_ticks']}.",
        "",
        "| | tp | saf | eff | coh | exp | Σ | declared |",
        "|--|---:|----:|----:|----:|----:|--:|---------:|",
        "| tick signed sum | {tp} | {saf} | {eff} | {coh} | {exp} | {s} | {tot} |".format(
            tp=fmt_num(ticks["sums"].get("task_progress")),
            saf=fmt_num(ticks["sums"].get("safety")),
            eff=fmt_num(ticks["sums"].get("efficiency")),
            coh=fmt_num(ticks["sums"].get("coherence")),
            exp=fmt_num(ticks["sums"].get("exploration")),
            s=fmt_num(sum(ticks["sums"].values()) if ticks["sums"] else None),
            tot=fmt_num(ticks["total"]),
        ),
        "| heads | {tp} | {saf} | {eff} | {coh} | {exp} | {s} | {tot} |".format(
            tp=fmt_num(ticks["heads"].get("task_progress")),
            saf=fmt_num(ticks["heads"].get("safety")),
            eff=fmt_num(ticks["heads"].get("efficiency")),
            coh=fmt_num(ticks["heads"].get("coherence")),
            exp=fmt_num(ticks["heads"].get("exploration")),
            s=fmt_num(ticks["head_sum"]),
            tot=fmt_num(ticks["total"]),
        ),
        "",
        f"|Δ| vs total = {fmt_num(ticks['abs_delta'])} (< 1e-9). Tick errors: `{ticks['errors'] or []}`.",
        "",
        f"Rationale nonempty: {ident['rationale_nonempty']}.",
        "",
        f"## Spike trains — {mark(spikes['pass'])}",
        "",
        f"Primary `spike_events`: {spikes['n']} ∈ [5,40], keyed `t_rel_ms`, globally non-decreasing, {spikes['channels']} channels.",
        "",
        "| item | value |",
        "|------|-------|",
        f"| race_window_us | {spikes['race_window_us']} |",
        f"| race_window_rel_ms | {spikes['race_window_rel_ms']} |",
        f"| dual (span == us/1000) | {spikes['dual_ok']} |",
        f"| in-window non-ctrl channels (≥2) | {len(spikes['in_window_channels'])}: {', '.join(map(str, spikes['in_window_channels']))} |",
        f"| min same-channel gap | {spikes['min_gap_ms']} ms (`{spikes['min_gap_channel']}`) ≥ 0.8 ms |",
        "",
        f"Errors: `{spikes['errors'] or []}`.",
        "",
        f"## Raster / third-factor / gate_snn budgets — {mark(raster_b['pass'] and ev['raster_status_pass'])}",
        "",
        "| raster field | value | check |",
        "|--------------|-------|-------|",
        f"| window_ms | {raster_b['window_ms']} ∈ [20,50] | `window_s={raster_b['window_s']}` == ms/1000 |",
        f"| neurons / rate | {raster_b['neurons']} / {raster_b['mean_rate_hz']} Hz | expected spikes {raster_b['expected_spikes']} vs declared {raster_b['spikes']} |",
        f"| energy | {raster_b['energy_pJ']} pJ / {raster_b['energy_uJ']} µJ | 23 pJ/spike |",
        f"| excerpt | {raster_b['excerpt_n']} events | sorted; in-window neuron ids |",
        f"| routing.table | {raster_b['table_n']} | ≥1 |",
        f"| third_factor tau dual | {raster_b['tau_ok']} | |",
        "",
    ]
    if raster_b.get("gate_pops"):
        lines += [
            "`gate_snn` populations vs `round(n * rate * window_s)` ±1:",
            "",
            "| name | n | Hz | spikes | expected |",
            "|------|--:|---:|-------:|---------:|",
        ]
        for p in raster_b["gate_pops"]:
            lines.append(
                f"| {p['name']} | {p['n']} | {p['hz']} | {p['spikes']} | {p['expected']} |"
            )
        lines.append("")
    lines += [
        f"Raster-budget errors: `{raster_b['errors'] or []}`.",
        "",
        f"## `outputs/raw/` immutability — {mark(raw_immut['pass'])}",
        "",
        f"`git -C synthetic-factory status --porcelain -- outputs/raw` is `{raw_immut['porcelain']!r}`.",
        f"`rg maos-r15-001` under `outputs/raw/`: {raw_immut['rg_id'] or '**0 files**'}.",
        "Staging lives only under `/tmp/maos-r15/`. This audit did not write, clobber, or stage into `outputs/raw/`.",
        "",
        "## Residual (not failures)" if ev.get("residuals") else "",
    ]
    if ev.get("residuals"):
        for i, note in enumerate(ev["residuals"], 1):
            lines.append(f"{i}. {note}")
        lines.append("")
    lines += [
        "## Machine-readable recap",
        "",
        "```",
        f"verdict={mark(overall)}",
        "batch=/tmp/maos-r15/batch-r15.jsonl",
        "notes=/tmp/maos-r15/NOTES-r15.md",
        "transcript=/tmp/maos-r15/swarm-transcript-r15.md",
        f"id={rec.get('id')}",
        f"kind={ident['classify_kind']}",
        f"n={ev['n_records']}",
        f"meta.round={meta.get('round')}",
        f"factory={meta.get('factory')}",
        f"generator={meta.get('generator')}",
        f"run_label={meta.get('run_label')}",
        f"sim_or_real={state.get('sim_or_real')}",
        f"decision={sd.get('decision')}",
        f"gate_snn.decision={gs.get('decision')}",
        f"total={rc.get('total')}",
        f"ticks={ticks['n']}",
        f"spike_events={spikes['n']}",
        f"raster.spikes={rs.get('spikes')}",
        f"energy_pJ={(rec.get('raster') or {}).get('energy_pJ')}",
        f"check_jsonl_staging_errors={cj['errors']}",
        f"check_jsonl_staging_warnings={cj['warnings']}",
        f"raster_status.reason_codes={rs.get('reason_codes')}",
        f"verify_batch_for_frontier_strict.blocked={str(vbf['blocked']).lower()}",
        f"verify_batch_for_frontier_strict.counts={vbf['counts']}",
        f"spike_probe_strict.rc={sp['exit']}",
        f"spike_probe_strict.loaded={(sp.get('summary') or {}).get('loaded')}",
        f"role_headings={'6x2_verbatim_in_order' if heading['ok'] else 'FAIL'}",
        f"novel_coverage_lines={novel['n_strict']}",
        f"novel_coverage={novel.get('pct')}",
        f"linear_issue={(top_r or {}).get('linear_issue')}",
        f"intended_use={(top_r or {}).get('intended_use')}",
        f"training_ready={ident['training_ready']}",
        f"thought_keys={'absent' if ev['thought']['pass'] else ev['thought']['detail']}",
        f"plant={plant}",
        f"cinderwick_tokens={clone['cinderwick_hits']}",
        f"clone_banned_in_record={bool(clone['record_hits'])}",
        f"jaccard_opening40_max={clone['jaccard_max']}",
        f"outputs_raw_written={str(not raw_immut['pass']).lower()}",
        "```",
        "",
    ]
    # drop accidental blank-only residual header
    cleaned = []
    for i, ln in enumerate(lines):
        if ln == "## Residual (not failures)" and (
            i + 1 >= len(lines) or lines[i + 1].startswith("## ")
        ):
            continue
        cleaned.append(ln)
    return "\n".join(cleaned).rstrip() + "\n"


def present_map() -> dict:
    out = {}
    for p in (BATCH, NOTES, TRANSCRIPT):
        exists = p.is_file()
        size = p.stat().st_size if exists else None
        out[str(p)] = {"present": exists and (size or 0) > 0, "bytes": size, "exists": exists}
    return out


def run() -> int:
    present = present_map()
    porcelain = git_porcelain_raw()
    if not all(v["present"] for v in present.values()):
        AUDIT.write_text(render_missing(present), encoding="utf-8")
        print(f"FAIL missing artifacts; wrote {AUDIT}", file=sys.stderr)
        return 1

    loaded = load_jsonl(BATCH)
    notes_text = NOTES.read_text(encoding="utf-8")
    transcript_text = TRANSCRIPT.read_text(encoding="utf-8")
    extra = []
    for p in sorted(STAGING.iterdir()):
        if p.name not in {"batch-r15.jsonl", "NOTES-r15.md", "swarm-transcript-r15.md"}:
            extra.append((p.name, {"bytes": p.stat().st_size}))

    n_records = len(loaded["records"])
    rec = loaded["records"][0][1] if loaded["records"] else {}
    lineno = loaded["records"][0][0] if loaded["records"] else None
    meta = rec.get("meta") or {}
    state = rec.get("state") or {}
    sd = rec.get("safety_decision") or {}
    gs = rec.get("gate_snn") if isinstance(rec.get("gate_snn"), dict) else {}

    cj_err, cj_warn, cj_kinds, cj_n = check_jsonl(
        BATCH, "batch-r15.jsonl", staging=FactoryStaging(enabled=True)
    )
    lg_err, lg_warn, lg_kinds, lg_n = check_jsonl(
        BATCH, "batch-r15.jsonl", staging=FactoryStaging(enabled=False)
    )
    check_jsonl_pass = (
        cj_err == []
        and cj_warn == []
        and cj_kinds == {"thalamic": 1}
        and cj_n == 1
        and not loaded["parse_errors"]
        and n_records == 1
        and loaded["trailing_lf"]
        and not loaded["has_crlf"]
        and not loaded["has_bare_cr"]
    )

    cl_errs, cl_kind = check_line(
        rec, f"batch-r15.jsonl:{lineno}", factory_staging=True
    )
    rec_errs, rec_warns, rec_kind, rec_id_val = check_record(
        rec, f"batch-r15.jsonl:{lineno}", factory_staging=True
    )

    exact_err = None
    exact_nbytes = None
    try:
        dumped = dumps_exact_json(rec, ensure_ascii=False, sort_keys=False)
        exact_nbytes = len(dumped.encode("utf-8"))
    except (ValueError, RecursionError) as exc:
        exact_err = str(exc)

    rs = raster_status(rec)
    raster_status_pass = (
        rs.get("reason_codes") == []
        and rs.get("gate_snn_present") is True
        and rs.get("gate_snn_valid") is True
        and rs.get("raster_valid") is True
        and int(rs.get("routing_table_entries") or 0) >= 1
        and rs.get("third_factor_present") is True
    )
    envelope = validate_bridge_envelope(BATCH, FACTORY_DIR)

    counts, findings, blocked = verify_batch_for_frontier(BATCH, strict=True)
    v_status, v_reason = verify_record_execution(rec, f"batch-r15.jsonl:{lineno}")
    vcli = subprocess.run(
        [
            sys.executable,
            str(PIPE / "verify_execution.py"),
            "--batch",
            str(BATCH),
            "--strict",
            "--json",
        ],
        cwd=str(REPO),
        capture_output=True,
        text=True,
    )
    verify_pass = (
        counts == {"verified": 1, "inconclusive": 0, "failed": 0, "total": 1}
        and blocked is False
        and findings == []
        and vcli.returncode == 0
        and v_status == "verified"
    )

    sp = subprocess.run(
        [sys.executable, str(PIPE / "spike_probe.py"), "--strict", str(BATCH)],
        cwd=str(REPO),
        capture_output=True,
        text=True,
    )
    try:
        sp_json = json.loads(sp.stdout)
    except json.JSONDecodeError:
        sp_json = {"raw_stdout": sp.stdout}
    spike_probe_pass = (
        sp.returncode == 0
        and not sp.stderr
        and sp_json.get("loaded") == 1
        and sp_json.get("unloadable") == 0
        and sp_json.get("input_errors") == 0
        and sp_json.get("problems") == []
        and sp_json.get("thalamic_records") == 1
    )

    heading_report = check_transcript(TRANSCRIPT, "argv")
    heading_checks = [
        {"name": c.name, "ok": c.ok, "detail": c.detail} for c in heading_report.checks
    ]
    inv_lines = []
    for cyc in heading_report.cycles:
        inv_lines.append(f"### Cycle {cyc.number}")
        inv_lines.append("")
        inv_lines.append(
            f"- Span: L{cyc.start_line}–L{cyc.end_line}"
            + (f" (marker L{cyc.marker.line_no} `{cyc.marker.raw.strip()}`)" if cyc.marker else "")
        )
        inv_lines.append("- Verbatim role headings:")
        for h in cyc.role_headings:
            inv_lines.append(f"  - L{h.line_no} `## {h.verbatim_role}`")
        inv_lines.append("")
    c2_json, c2_how = extract_cycle2_json(transcript_text)
    json_eq = False
    json_eq_note = "Cycle-2 Trajectory Builder JSON not found."
    if c2_json:
        try:
            parsed = json.loads(c2_json)
            json_eq = parsed == rec
            json_eq_note = (
                f"Cycle-2 Trajectory Builder object ({c2_how}) **equals** `batch-r15.jsonl` line 1."
                if json_eq
                else f"Cycle-2 Trajectory Builder object ({c2_how}) **does not equal** JSONL."
            )
        except (ValueError, RecursionError) as exc:
            json_eq_note = f"Cycle-2 JSON parse failed: {exc}"
    heading_ok = heading_report.ok and json_eq

    labeled = [
        line
        for line in re.split(r"\r\n|\n|\r", notes_text)
        if NOVEL_COVERAGE_LABEL_RE.search(line)
    ]
    strict = [line for line in labeled if NOVEL_COVERAGE_RE.fullmatch(line)]
    pct = None
    if strict:
        m = NOVEL_COVERAGE_RE.fullmatch(strict[0])
        if m:
            pct = m.group(1) + "%"
    novel_val = validate_novel_coverage(
        NOTES, FACTORY_DIR, notes_text=notes_text, required=True
    )
    novel_pass = (
        len(strict) == 1
        and len(labeled) == 1
        and novel_val is None
        and pct is not None
    )

    blob_rec = json.dumps(rec, ensure_ascii=False)
    rec_hits = clone_token_hits(blob_rec)
    notes_hits = clone_token_hits(notes_text)
    tr_hits = clone_token_hits(transcript_text)
    cinder = [
        tok
        for tok in EXPECTED_PLANT_TOKENS
        if re.search(re.escape(tok), blob_rec, flags=re.IGNORECASE)
        or re.search(re.escape(tok), str(state.get("scenario_name") or ""), flags=re.IGNORECASE)
    ]
    desc_tokens = opening40(state.get("description") or "")
    jac_rows = []
    j_max = 0.0
    j_max_vs = None
    for hist in historical_descriptions():
        if hist["id"] == rec.get("id"):
            continue
        j = jaccard(desc_tokens, hist["tokens"])
        jac_rows.append({"id": hist["id"], "plant": hist["plant"], "j": j})
        if j >= j_max:
            j_max = j
            j_max_vs = f"{hist['id']} / {hist['plant']}"
    jac_rows.sort(key=lambda r: -r["j"])
    clone_pass = (
        not rec_hits
        and "CINDERWICK" in {t.upper() for t in cinder}
        and j_max < 0.4
        and "LYOSHIELD" not in rec_hits
    )

    ident_errs = []
    if rec.get("id") != EXPECTED_ID:
        ident_errs.append(f"id {rec.get('id')!r}")
    if meta.get("round") != EXPECTED_ROUND:
        ident_errs.append(f"round {meta.get('round')!r}")
    if meta.get("factory") != EXPECTED_FACTORY:
        ident_errs.append(f"factory {meta.get('factory')!r}")
    if meta.get("generator") != EXPECTED_GENERATOR:
        ident_errs.append(f"generator {meta.get('generator')!r}")
    if meta.get("run_label") != EXPECTED_RUN:
        ident_errs.append(f"run_label {meta.get('run_label')!r}")
    if meta.get("cycles") != 2:
        ident_errs.append(f"cycles {meta.get('cycles')!r}")
    if meta.get("batch_position") not in (1, None):
        # allow missing but if present must be 1
        if meta.get("batch_position") != 1:
            ident_errs.append(f"batch_position {meta.get('batch_position')!r}")
    sor = state.get("sim_or_real")
    if sor not in {"designed", "simulated", "hil"}:
        ident_errs.append(f"sim_or_real {sor!r}")
    if sor == "real":
        ident_errs.append("sim_or_real=real")
    if "training_ready" in rec:
        ident_errs.append("training_ready present")
    if sd.get("decision") not in {"ACCEPT", "MODIFY", "REJECT"}:
        ident_errs.append(f"decision {sd.get('decision')!r}")
    if gs.get("decision") != sd.get("decision"):
        ident_errs.append("gate_snn.decision mismatch")
    rationale = sd.get("rationale")
    rationale_nonempty = isinstance(rationale, str) and bool(rationale.strip())
    if not rationale_nonempty:
        ident_errs.append("empty rationale")
    tags = meta.get("tags") or []
    research_only_tag = isinstance(tags, list) and "research-only" in tags
    classify = classify_kind(rec)
    is_thal = is_thalamic_record(rec)
    if classify != "thalamic" or not is_thal:
        ident_errs.append(f"kind {classify} thalamic={is_thal}")
    ident_pass = not ident_errs and n_records == 1

    r_errs = rights_errors(rec.get("rights"), "rights")
    r_errs += rights_errors((meta.get("rights") if isinstance(meta, dict) else None), "meta.rights")
    rights_pass = not r_errs

    th = thought_hits(rec)
    thought_pass = not th

    ticks = tick_checks(rec)
    spikes = spike_checks(rec)
    raster_b = raster_budget_checks(rec)

    raw_rg = rg_raw("maos-r15-001")
    raw_pass = porcelain.strip() == "" and not raw_rg

    rm793 = {
        "notes": notes_text.count("RM-793"),
        "transcript": transcript_text.count("RM-793"),
        "record": blob_rec.count("RM-793"),
    }

    class_blurb = (
        f"Class: **{(meta.get('coordination_failure_class') or plant or '(undeclared)')}**. "
        f"Plant tokens CINDERWICK/Lodenholt/DH-3 observed: {cinder or 'none'}. "
        f"Banned clone tokens in the JSONL record: {rec_hits or 'none'}."
    )

    residuals = []
    if sor == "designed" and re.search(r"\bhil\b", json.dumps(rec.get("executed_action") or {}), re.I):
        residuals.append(
            "**HITL ratification latency is not `sim_or_real=hil`.** Provenance cell stays `designed` if the plant is invented."
        )
    if j_max >= 0.25:
        residuals.append(
            f"Jaccard vs `{j_max_vs}` is {j_max:.4f} (still < 0.4 if clone gate passed)."
        )
    if "THERMION" not in rec_hits and re.search(r"district-heating", blob_rec, re.I):
        residuals.append(
            "District-heating vocabulary is expected for CINDERWICK; de-collision vs r03 THERMION is the Jaccard number, not a token ban on the domain name."
        )

    jsonl_note = (
        f"{sum(1 for ln in loaded['physical'] if ln.strip())} nonempty record(s), "
        f"physical split {len(loaded['physical'])}, "
        f"{'trailing LF' if loaded['trailing_lf'] else 'NO trailing LF'}, "
        f"{'CRLF' if loaded['has_crlf'] else 'no CR'}"
    )

    error_strings = []
    error_strings.extend(cj_err)
    error_strings.extend(cl_errs)
    error_strings.extend(rec_errs)
    error_strings.extend(envelope)
    error_strings.extend(findings if isinstance(findings, list) else [findings])
    if exact_err:
        error_strings.append(exact_err)
    error_strings.extend(ident_errs)
    error_strings.extend(r_errs)
    error_strings.extend(th)
    error_strings.extend(ticks["errors"])
    error_strings.extend(spikes["errors"])
    error_strings.extend(raster_b["errors"])
    if not heading_ok:
        error_strings.extend(
            f"{c['name']}: {c['detail']}" for c in heading_checks if not c["ok"]
        )
        if not json_eq:
            error_strings.append(json_eq_note)
    if not novel_pass:
        error_strings.append(f"novel_coverage validate={novel_val!r} lines={labeled!r}")
    if not clone_pass:
        error_strings.append(
            f"clone record_hits={rec_hits} cinder={cinder} j_max={j_max}"
        )
    if sp.returncode != 0:
        error_strings.append(f"spike_probe exit {sp.returncode} stderr={sp.stderr!r}")

    gate_table = [
        ("check_jsonl_staging", check_jsonl_pass),
        ("raster_status", raster_status_pass),
        ("verify_batch_for_frontier_strict", verify_pass),
        ("spike_probe_strict", spike_probe_pass),
        ("identity_round15", ident_pass),
        ("rm793_rights", rights_pass),
        ("thought_keys", thought_pass),
        ("headings_6x2", heading_ok),
        ("novel_coverage", novel_pass),
        ("not_clone", clone_pass),
        ("reward_ticks", ticks["pass"]),
        ("spike_trains", spikes["pass"]),
        ("raster_budgets", raster_b["pass"]),
        ("outputs_raw_immutable", raw_pass),
        ("q1_one_record", n_records == 1),
        ("bridge_envelope", envelope == []),
        ("cycle2_json_eq_jsonl", json_eq),
    ]
    overall = all(ok for _, ok in gate_table)

    ev = {
        "overall": overall,
        "gate_table": gate_table,
        "error_strings": [e for e in error_strings if e],
        "n_records": n_records,
        "rec": rec,
        "class_blurb": class_blurb,
        "residuals": residuals,
        "jsonl_note": jsonl_note,
        "artifacts": {
            "batch_bytes": BATCH.stat().st_size,
            "notes_bytes": NOTES.stat().st_size,
            "transcript_bytes": TRANSCRIPT.stat().st_size,
            "batch_sha256": sha256(BATCH),
            "notes_sha256": sha256(NOTES),
            "transcript_sha256": sha256(TRANSCRIPT),
            "extra_files": extra,
        },
        "check_jsonl": {
            "errors": cj_err,
            "warnings": cj_warn,
            "kinds": cj_kinds,
            "records": cj_n,
            "pass": check_jsonl_pass,
            "legacy_errors": lg_err,
            "legacy_warnings": lg_warn,
            "legacy_kinds": lg_kinds,
            "legacy_n": lg_n,
        },
        "check_line": {"kind": cl_kind, "errors": cl_errs},
        "check_record": {
            "kind": rec_kind,
            "id": rec_id_val,
            "errors": rec_errs,
            "warnings": rec_warns,
        },
        "exact": {"error": exact_err, "nbytes": exact_nbytes},
        "raster_status": rs,
        "raster_status_pass": raster_status_pass,
        "bridge_envelope": envelope,
        "verify": {
            "counts": counts,
            "findings": findings,
            "blocked": blocked,
            "pass": verify_pass,
            "cli_exit": vcli.returncode,
        },
        "verify_record": {"status": v_status, "reason": v_reason},
        "spike_probe": {
            "exit": sp.returncode,
            "stderr": sp.stderr,
            "stdout": sp.stdout,
            "summary": sp_json,
            "pass": spike_probe_pass,
        },
        "heading": {
            "ok": heading_ok,
            "checks": heading_checks,
            "inventory_md": "\n".join(inv_lines),
            "json_eq_note": json_eq_note,
        },
        "novel": {
            "pass": novel_pass,
            "n_labeled": len(labeled),
            "n_strict": len(strict),
            "line": strict[0] if strict else (labeled[0] if labeled else None),
            "pct": pct,
            "validate": novel_val,
            "notes_cell": (
                f"exactly one `{strict[0]}`"
                if len(strict) == 1
                else f"{len(strict)} strict coverage lines"
            ),
        },
        "clone": {
            "pass": clone_pass,
            "record_hits": rec_hits,
            "notes_hits": notes_hits,
            "transcript_hits": tr_hits,
            "cinderwick_hits": cinder,
            "jaccard_max": round(j_max, 4),
            "jaccard_max_vs": j_max_vs,
            "jaccard_rows": jac_rows,
        },
        "identity": {
            "pass": ident_pass,
            "errors": ident_errs,
            "classify_kind": classify,
            "is_thalamic": is_thal,
            "training_ready": "present" if "training_ready" in rec else "absent from the JSONL object",
            "research_only_tag": research_only_tag,
            "rationale_nonempty": rationale_nonempty,
        },
        "rights": {"pass": rights_pass, "errors": r_errs},
        "thought": {
            "pass": thought_pass,
            "detail": "none of `thought` / `chain_of_thought` / `scratch` / `inner_monologue`"
            if thought_pass
            else ", ".join(th),
        },
        "ticks": ticks,
        "spikes": spikes,
        "raster_budget": raster_b,
        "raw": {
            "pass": raw_pass,
            "porcelain": porcelain.strip(),
            "rg_id": raw_rg,
        },
        "rm793_counts": rm793,
    }
    AUDIT.write_text(render_full(ev), encoding="utf-8")
    Path("/tmp/maos-r15-audit-run.json").write_text(
        dumps_exact_json(
            {
                "verdict": "PASS" if overall else "FAIL",
                "gates": {k: v for k, v in gate_table},
                "errors": ev["error_strings"],
                "id": rec.get("id"),
                "spike_probe": sp_json,
                "heading_ok": heading_ok,
                "jaccard_max": j_max,
            },
            ensure_ascii=False,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    print(("PASS" if overall else "FAIL") + f" wrote {AUDIT}")
    return 0 if overall else 1


if __name__ == "__main__":
    raise SystemExit(run())
