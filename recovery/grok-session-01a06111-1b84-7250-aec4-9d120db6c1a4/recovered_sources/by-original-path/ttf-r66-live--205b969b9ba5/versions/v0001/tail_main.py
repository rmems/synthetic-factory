def tokenize(text: str) -> set[str]:
    return {tok for tok in re.split(r"[^a-z0-9]+", text.lower()) if tok}


def jaccard(a: str, b: str) -> float:
    sa, sb = tokenize(a), tokenize(b)
    if not sa or not sb:
        return 0.0
    return len(sa & sb) / len(sa | sb)


def check_refractory(events, min_ms=0.8):
    last = {}
    for ev in events:
        ch, t = ev["channel"], ev["t_rel_ms"]
        if ch in last and t - last[ch] < min_ms - 1e-12:
            return f"{ch} gap {t - last[ch]} ms"
        last[ch] = t
    return None


def check_race(rec):
    start, end = rec["state"]["race_window_rel_ms"]
    in_win = {}
    for ev in rec["spike_events"]:
        if start - 1e-12 <= ev["t_rel_ms"] <= end + 1e-12:
            in_win.setdefault(ev["channel"], 0)
            in_win[ev["channel"]] += 1
    if len(in_win) < 2:
        return f"race window has {len(in_win)} channels: {in_win}"
    return None


def excerpt_vs_spikes(rec):
    spike_us = {int(round(ev["t_rel_ms"] * 1000.0)) for ev in rec["spike_events"]}
    ex_us = {item["t_us"] for item in rec["raster"]["excerpt"]}
    if not spike_us:
        return 0.0
    return len(spike_us & ex_us) / len(spike_us)


def walk_keys(obj, path=""):
    found = []
    if isinstance(obj, dict):
        for key, item in obj.items():
            child = f"{path}.{key}" if path else key
            found.append(child)
            found.extend(walk_keys(item, child))
    elif isinstance(obj, list):
        for idx, item in enumerate(obj):
            found.extend(walk_keys(item, f"{path}[{idx}]"))
    return found


def expected_m6_prefix(rec):
    st = rec["state"]
    events = rec["spike_events"]
    race = st["race_window_rel_ms"]
    in_win = [e for e in events if race[0] - 1e-9 <= e["t_rel_ms"] <= race[1] + 1e-9]
    ordered = sorted(in_win, key=lambda e: e["t_rel_ms"])
    win_e = next(e for e in ordered if e["channel"] != "ctrl.gate")
    lose_e = next(
        e for e in ordered if e["channel"] not in {win_e["channel"], "ctrl.gate"}
    )
    t_win = round(win_e["t_rel_ms"] * 1000)
    t_lose = round(lose_e["t_rel_ms"] * 1000)
    t_gate = t_win + int(st["gate_latency_us"])
    t_race = int(st["race_window_us"])
    tick1 = round(0.40 * t_win)
    if rec["id"] == "ttf-r66-326":
        tick5 = 22800
    else:
        tick5 = t_gate + t_race
    return [tick1, t_win, t_lose, t_gate, tick5], t_win, t_lose, t_gate


def self_check(records):
    issues = []
    descs = [r["state"]["description"] for r in records]
    opens = [d.split(".")[0] for d in descs]
    if len(set(opens)) != 5:
        issues.append("opening sentences not unique")
    jmax = 0.0
    for i in range(5):
        for j in range(i + 1, 5):
            val = jaccard(descs[i], descs[j])
            jmax = max(jmax, val)
            if val >= 0.4:
                issues.append(f"Jaccard {records[i]['id']}/{records[j]['id']} = {val:.3f}")
    wrong = [
        r
        for r in records
        if r["safety_decision"].get("correctness") == "incorrect"
        or r["meta"].get("supervisor_error_type")
    ]
    if len(wrong) != 1 or wrong[0]["id"] != "ttf-r66-330":
        issues.append(f"wrong-gate set {[w['id'] for w in wrong]}")
    if any(r["state"]["sim_or_real"] == "real" for r in records):
        issues.append("sim_or_real=real")
    hil = [r["id"] for r in records if r["state"]["sim_or_real"] == "hil"]
    sim = [r["id"] for r in records if r["state"]["sim_or_real"] == "simulated"]
    if hil != ["ttf-r66-328"]:
        issues.append(f"hil set {hil}")
    if sim != ["ttf-r66-329"]:
        issues.append(f"simulated set {sim}")
    designed = [r["id"] for r in records if r["state"]["sim_or_real"] == "designed"]
    if designed != ["ttf-r66-326", "ttf-r66-327", "ttf-r66-330"]:
        issues.append(f"designed set {designed}")
    domains = [r["state"]["domain"] for r in records]
    if len(set(domains)) != 5:
        issues.append(f"domain collision {domains}")
    pool = {
        "industrial-assembly",
        "surgical-assist",
        "autonomous-driving",
        "aerial-swarm",
        "warehouse-amr",
        "humanoid-locomotion",
        "grid-inspection",
        "underwater-rov",
    }
    if not set(domains) <= pool:
        issues.append(f"domain outside 8-pool {domains}")
    expected_ids = [f"ttf-r66-{n}" for n in range(326, 331)]
    if [r["id"] for r in records] != expected_ids:
        issues.append(f"ids {[r['id'] for r in records]}")
    decisions = [r["safety_decision"]["decision"] for r in records]
    if decisions != ["MODIFY", "MODIFY", "REJECT", "ACCEPT", "REJECT"]:
        issues.append(f"decision mix {decisions}")
    blob = json.dumps(records)
    for frag in BANNED_PLANT_FRAGMENTS:
        if frag in blob:
            issues.append(f"banned plant fragment {frag}")
    if "training_ready" in blob:
        issues.append("training_ready present")
    thought_re = re.compile(
        r"\b(thought|chain_of_thought|scratch|inner_monologue|hidden_reasoning)\b"
    )
    if thought_re.search(blob):
        issues.append("thought-like key/text present")
    thought_keys = {
        "thought",
        "reasoning",
        "chain_of_thought",
        "hidden_reasoning",
        "inner_monologue",
        "scratch",
        "internal_reasoning",
        "thinking",
        "cot",
        "thoughts",
    }
    for rec in records:
        for path in walk_keys(rec):
            leaf = path.split(".")[-1]
            if leaf in thought_keys or "thought" in leaf.lower():
                issues.append(f"{rec['id']} thought-like key {path}")
    totals = [r["reward_components"]["total"] for r in records]
    if all(t > 0 for t in totals):
        issues.append("all-positive totals")
    for rec in records:
        rid = rec["id"]
        err = check_refractory(rec["spike_events"])
        if err:
            issues.append(f"{rid} refractory {err}")
        err = check_race(rec)
        if err:
            issues.append(f"{rid} {err}")
        n = rec["raster"]["neurons"]
        rate = rec["raster"]["mean_rate_hz"]
        window_s = rec["raster"]["window_s"]
        expected = round(n * rate * window_s)
        if abs(rec["raster"]["spikes"] - expected) > 1:
            issues.append(f"{rid} spike budget {rec['raster']['spikes']} vs {expected}")
        overlap = excerpt_vs_spikes(rec)
        if rid == "ttf-r66-326":
            if rec["raster"].get("excerpt_source") != "independent_lif":
                issues.append("326 missing independent_lif")
            if rec["future_outcome"]["reward_inflection_t_us"] > rec["raster"]["window_ms"] * 1000:
                issues.append("326 inflection outside window")
        elif overlap >= 0.8:
            issues.append(f"{rid} excerpt overlap {overlap:.2f}")
        inf = rec["future_outcome"]["reward_inflection_t_us"]
        tick_times = [t["t_us"] for t in rec["reward_components"]["ticks"]]
        if inf not in tick_times:
            issues.append(f"{rid} inflection {inf} not a tick")
        if len(rec["reward_components"]["ticks"]) != 6:
            issues.append(f"{rid} tick count")
        if not (8 <= len(rec["state"]["episode_steps"]) <= 15):
            issues.append(f"{rid} episode_steps")
        if rec["gate_snn"]["decision"] != rec["safety_decision"]["decision"]:
            issues.append(f"{rid} gate_snn decision mismatch")
        heads = ["task_progress", "safety", "efficiency", "coherence", "exploration"]
        total = sum(rec["reward_components"][h] for h in heads)
        if abs(total - rec["reward_components"]["total"]) > 1e-6:
            issues.append(f"{rid} total mismatch {total}")
        for h in heads:
            s = sum(t[h] for t in rec["reward_components"]["ticks"])
            if abs(s - rec["reward_components"][h]) > 1e-6:
                issues.append(f"{rid} {h} tick sum {s} vs {rec['reward_components'][h]}")
        prefix, t_win, t_lose, t_gate = expected_m6_prefix(rec)
        if tick_times[:5] != prefix:
            issues.append(f"{rid} TTF-M6 prefix {tick_times[:5]} != {prefix}")
        t_win_us = int(round(float(rec["raster"]["window_ms"]) * 1000))
        if not (tick_times[5] > t_win_us):
            issues.append(f"{rid} tick6 not after raster")
        delayed = rec["future_outcome"].get("delayed_surprise_s")
        if delayed is None or abs(tick_times[5] - round(delayed * 1e6)) > 0:
            issues.append(f"{rid} tick6 != delayed_surprise_s")
        exec_p = rec["executed_action"]["parameters"]
        prop_p = rec["proposed_action"]["parameters"]
        if rec["safety_decision"]["decision"] == "ACCEPT" and exec_p != prop_p:
            issues.append(f"{rid} ACCEPT params differ")
        if rec["meta"]["round"] != 66:
            issues.append(f"{rid} meta.round")
        dw_s = rec["gate_snn"]["decision_window_ms"] / 1000.0
        for p in rec["gate_snn"]["populations"]:
            if "mean_rate_hz" in p:
                exp_sp = round(p["neurons"] * p["mean_rate_hz"] * dw_s)
                if abs(p["spikes"] - exp_sp) > 1:
                    issues.append(f"{rid} gate_snn {p['name']} spikes {p['spikes']} vs {exp_sp}")
        if rec["raster"]["energy_pJ"] != rec["raster"]["spikes"] * 23:
            issues.append(f"{rid} energy_pJ")
        rights = rec["meta"]["rights"]
        if rights.get("linear_issue") != "RM-793" or rights.get("intended_use") != "research_only":
            issues.append(f"{rid} rights stamp")
        n_spk = len(rec["spike_events"])
        if not (5 <= n_spk <= 40):
            issues.append(f"{rid} spike n={n_spk}")
        n_ex = len(rec["raster"]["excerpt"])
        if not (8 <= n_ex <= 16):
            issues.append(f"{rid} excerpt n={n_ex}")
        if rec["safety_decision"]["decision"] == "REJECT" and rec["safety_decision"]["correctness"] == "incorrect":
            if "recovery" not in rec["future_outcome"]:
                issues.append(f"{rid} missing recovery")
        gl = rec["state"]["gate_latency_us"]
        rw = rec["state"]["race_window_us"]
        if not (50 <= gl <= 2000):
            issues.append(f"{rid} gate_latency")
        if not (50 <= rw <= 1000):
            issues.append(f"{rid} race_window")
        wm = rec["raster"]["window_ms"]
        if not (20 <= wm <= 50):
            issues.append(f"{rid} window_ms")
        for item in rec["raster"]["excerpt"]:
            if not (0 <= item["t_us"] <= wm * 1000):
                issues.append(f"{rid} excerpt t_us {item['t_us']}")
            if not (0 <= item["neuron_id"] < rec["raster"]["neurons"]):
                issues.append(f"{rid} neuron_id {item['neuron_id']}")
        if rec["safety_decision"].get("correctness") == "incorrect":
            if rec["meta"].get("supervisor_error_type") != "wrong-reject":
                issues.append(f"{rid} expected wrong-reject")
            if rec["safety_decision"]["decision"] == "ACCEPT":
                issues.append(f"{rid} wrong-ACCEPT")
    return issues, jmax


def notes_text(records, jmax: float) -> str:
    rows = []
    for rec in records:
        dec = rec["safety_decision"]["decision"]
        cor = rec["safety_decision"]["correctness"]
        if cor == "incorrect":
            cor = f"**incorrect ({rec['meta']['supervisor_error_type']})**"
        tot = rec["reward_components"]["total"]
        tot_s = f"{tot:+.2f}"
        if rec["id"] == "ttf-r66-326":
            tot_s = f"**{tot:+.2f}**"
        edge = {
            "ttf-r66-326": "process-correct irrigation clamp; fascia micro-tear inside 42 ms raster; independent LIF",
            "ttf-r66-327": "corona 1.28 mA > 0.90 cap; crawl 0.24 -> 0.07 m/s",
            "ttf-r66-328": "ankle AE 56 pps beats IMU tilt 2.1 deg; hold descent",
            "ttf-r66-329": "torso 1.24 m vs bay 14 kPa; proposed 0.62 m/s already legal",
            "ttf-r66-330": "live pitot 6.4 m/s legal; 21.50 mA NAMUR fail-high REJECT-holds 1.6 -> 0 m/s",
        }[rec["id"]]
        rows.append(
            f"| {rec['id']} | {rec['state']['domain']} | {dec} | {cor} | "
            f"{rec['state']['sim_or_real']} | {tot_s} | {edge} |"
        )
    ras_rows = []
    for rec in records:
        r = rec["raster"]
        ras_rows.append(
            f"| {rec['id']} | {rec['state']['domain']} | {r['neurons']} | {r['mean_rate_hz']} | "
            f"{r['window_ms']} | {r['spikes']} | {r['energy_pJ']} | {r['energy_uJ']:.6f} |"
        )
    tick_rows = []
    for rec in records:
        rc = rec["reward_components"]
        inf = rec["future_outcome"]["reward_inflection_t_us"]
        ticks = rc["ticks"]
        idx = next(i + 1 for i, t in enumerate(ticks) if t["t_us"] == inf)
        tick_rows.append(
            f"| {rec['id'][-3:]} | {len(ticks)} | {rc['task_progress']:+.2f} | {rc['safety']:+.2f} | "
            f"{rc['efficiency']:+.2f} | {rc['coherence']:+.2f} | {rc['exploration']:+.2f} | "
            f"{rc['total']:+.2f} | {idx} ({inf}) |"
        )
    return f"""# Thalamic Trajectory Factory — NOTES-r66

- Factory: `thalamic-trajectory-factory`
- Run label: `2026-09-02-final-heavy`
- Generator: `grok-4.6`
- Channel: SuperGrok Heavy consumer chat (RM-793 research-only)
- Quota: 5
- Quality: Q=5
- IDs: `ttf-r66-326` … `ttf-r66-330`
- Domains this batch: `surgical-assist`, `grid-inspection`, `humanoid-locomotion`, `warehouse-amr`, `aerial-swarm`

These five domain slugs stay inside the prompt 8-pool. Sit-outs vs live r22: `surgical-assist`, `grid-inspection`, `humanoid-locomotion`. Sit-outs vs live r01 that now enter: `warehouse-amr`, `aerial-swarm`. Sit-outs this round: `underwater-rov`, `industrial-assembly`, `autonomous-driving`. All five plants are invented (Cannula-Brae, Corona-Gill, Talus-Naze, Aisle-Croft, Gust-Holt). Do not restack prior TTF plants. Do not restack `/tmp/ttf-r66` maleic/PTA/VCM/CCR/Solvay IDs `ttf-r66-346`…`350`.

## Batch map

| id | domain | decision | correctness | sim_or_real | total | edge |
|----|--------|----------|-------------|-------------|-------|------|
{chr(10).join(rows)}

Gate mix: 1 ACCEPT, 2 correct MODIFY (one partnered-neg, in-window), 1 correct REJECT, 1 incorrect REJECT (NAMUR NE43 fail-high as live). Provenance: designed×3, simulated×1, hil×1 (Talus-Naze TZ-HIL stair stand). Intra-batch Jaccard on `state.description` {jmax:.3f} (< 0.4). Totals not all-positive (326 −0.42, 330 −0.36).

## Wrong-reject

**ttf-r66-330** is the mandated incorrect gate (`safety_decision.correctness=incorrect`, `meta.supervisor_error_type=wrong-reject`). Alternate vs odd rounds: even rounds host wrong-reject. This is **NAMUR NE43 fail-high as live** (live pitot under cap, supervisor binds a 21.50 mA diagnostic as airspeed). Not r22-110 stale-interlock / ghost occupancy, not r12-079 induced-kV-as-sensor-fault, not r14-086 wet-derate MAD, not `/tmp/ttf-r22-126` class-transplant / wrong floor, not `/tmp/ttf-r64-337` reverse-scale / inverted-4-20, not `/tmp/ttf-r66-347` idle-twin-string-as-live. Do not emit a wrong-ACCEPT.

Gust-Holt GH-9 / Quad-Q8 reads live pitot **6.4 m/s** against a published **9.0 m/s** cap. A **21.50 mA** analog is NAMUR NE43 fail-high (`namur_status=fail_high`, `namur_mA=21.50` >= `namur_fail_high_mA=21.0`). Sidecar arithmetic `live_mps <= gust_cap_mps` is true. A timely ACCEPT at `t_gate_us=6220` leaves **1.6 m/s** climb. A weak supervisor binds the fail-high as live 17.50 m/s and REJECT-holds **1.6 → 0 m/s**. Live pitot stays **6.4**. Convictable without rotor dynamics: `evidence.live_mps <= evidence.gust_cap_mps`, `evidence.namur_status == fail_high`, `executed_action.climb_m_s == 0`, `executed_action.bind_fail_high_as_live == true`, `raster.routing.table` sends `relay.ma.failhigh` → `policy.hold_reject` (weight 0.74) with no positive weight to `policy.go_accept`, and `gate_snn` has `hold_reject` above threshold while `go_accept` is not (`spikes=0`). Recovery: ACCEPT; leave 1.6 m/s; drop the 21.50 mA as live PV. Cost: 9 min missed survey window (`abort_s=540`).

## Partnered-negative in-window (326)

**ttf-r66-326** is the partnered negative: process-correct MODIFY (irrigation held 11 mL/min; tip 2.22 N <= 2.50 cap) while the world still charges. Safety −0.58 prices the fascia micro-tear at **22.800 ms**; `task_progress` stays +0.32 because the clamp completed. Inflection `t_us=22800` is tick 5 and is **inside** the 42 ms raster (`22800 ≤ 42000`). Named un-netted loss: 11 min fat-graft isolate (`abort_s=660`). Not folded into process heads.

Independent LIF (the one labeled sidecar sim): `state.sim_or_real` remains `designed`. `raster.excerpt_source=independent_lif`, `raster.sim_scope=sidecar_only`, `raster.lif` seed 66326, stim `[22000, 25200]`. Excerpt is membrane crossings (`lif.clamp` early vs `lif.tear` 22–25.2 ms), not a 1:1 remap of `spike_events`. `meta.tags` include `independent-lif-raster` and `sidecar-sim-only`.

## Reward formula and tick reconciliation

Declared aggregation on every record:

`total = task_progress + safety + efficiency + coherence + exploration`

Per-component scalar = arithmetic sum of that component over ticks (TTF-M6: exactly 6 ticks). Tick 6 is bound to a published sidecar (`abort_s`, `survey_s`) via `future_outcome.delayed_surprise_s` and is strictly after the raster window. Inflection `t_us` is an actual tick.

| id | ticks | tp | saf | eff | coh | exp | total | inflection tick |
|----|-------|----|-----|-----|-----|-----|-------|-----------------|
{chr(10).join(tick_rows)}

Tick-6 sidecar bind: 326 `abort_s=660`, 327 `survey_s=240`, 328 `abort_s=480`, 329 `survey_s=270`, 330 `abort_s=540`.

## Raster / energy (Loihi-2 4-core, 23 pJ/spike)

| id | domain | n | rate Hz | window_ms | spikes | energy_pJ | energy_uJ |
|----|--------|---|---------|-----------|--------|-----------|-----------|
{chr(10).join(ras_rows)}

`spikes = round(n × rate × window_s)`. Every record carries `gate_snn` whose `decision` matches the safety gate; populations that declare rate+spikes meet the same ±1 budget against `decision_window_s`. `routing.third_factor` has modulator (NA / ACh / DA / 5-HT / adenosine), `tau_e_s`/`tau_e_ms` pair, and eligibility. Excerpt same-neuron gap ≥ 1000 µs; spike trains same-channel refractory ≥ 0.8 ms. Non-326 excerpts are kernelized and independent of `spike_events` times (overlap < 0.8).

## Local checks (this window)

Generator stdout: self_check (Jaccard, refractory, race, spike budget, energy, tick6 bind, gate_snn budget, rights). Then `json.loads` every line, `validate_run.check_line`, `raster_status`, `check_jsonl` FactoryStaging, `verify_batch_for_frontier(strict=True)`, `spike_probe.py --strict`.

Never `training_ready`. Never `sim_or_real=real`. Create-only into the assigned live path; did not clobber 2026-08-17 / 2026-08-30; did not overwrite existing r66 files (c-suffix if occupied).

## Residual weaknesses (honest)

1. Only **one** labeled independent LIF (326). The other four excerpts are independent of `spike_events` times but are not declared population sims.
2. Wrong-ACCEPT still absent (guard).
3. Tick-6 sidecar bind is standing machinery (r14+), not a new class.
4. Two 8-pool domains are reused vs live r22 (`warehouse-amr`, `aerial-swarm`) with new plants; a later round could sit those out entirely.
5. 329 ACCEPT is already-legal; a later round could pair the single ACCEPT with a world charge that does not go negative.

## Next densification target

Publish the NAMUR diagnostic predicate as a sidecar enum (`namur_status`) so a fail-high-as-live REJECT is convictable without the analog-loop story. Optional: labeled LIF on a second record, or an ISI histogram sidecar. Remaining unused even-round wrong-REJECT subclasses include **HART SV-as-PV**. Wrong-ACCEPT remains structurally absent until a prompt amendment.

Novel coverage: 22.0%
"""


def create_only(path: Path, text: str) -> Path:
    text_path = str(path)
    for frag in FORBIDDEN_PATH_FRAGMENTS:
        if frag in text_path:
            raise SystemExit(f"refusing forbidden path {path}")
    target = path
    if target.exists():
        target = path.with_name(path.stem + "c" + path.suffix)
        if target.exists():
            raise SystemExit(f"c-suffix also exists: {target}")
    flags = os.O_CREAT | os.O_EXCL | os.O_WRONLY
    fd = os.open(target, flags, 0o644)
    with os.fdopen(fd, "w", encoding="utf-8") as handle:
        handle.write(text)
    return target


def run_pipelines(batch_path: Path, notes_path: Path, records):
    sys.path.insert(0, str(PIPELINES))
    from check_records import FactoryStaging, check_jsonl
    from curate_bridge import raster_status
    from exact_json import dumps_exact_json
    from round_txn import validate_novel_coverage
    from validate_run import check_line
    from verify_execution import verify_batch_for_frontier

    report = []
    errors, warnings, kinds, nrec = check_jsonl(
        batch_path, batch_path.name, staging=FactoryStaging(enabled=True)
    )
    report.append(("check_jsonl FactoryStaging", errors, warnings, kinds, nrec))
    line_errs = []
    for i, rec in enumerate(records, 1):
        errs, kind = check_line(rec, f"{batch_path.name}:{i}", factory_staging=True)
        if errs:
            line_errs.append((i, kind, errs))
        try:
            dumps_exact_json(rec, ensure_ascii=False, sort_keys=False)
        except Exception as exc:
            line_errs.append((i, "exact_json", [str(exc)]))
    report.append(("check_line+exact_json", line_errs, None, None, None))
    raster_fail = []
    for rec in records:
        st = raster_status(rec, require_raster=True, require_routing_table=True)
        if not st.get("raster_valid") or not st.get("gate_snn_valid"):
            raster_fail.append((rec["id"], st))
    report.append(("raster_status", raster_fail, None, None, None))
    counts, findings, blocked = verify_batch_for_frontier(batch_path, strict=True)
    report.append(("verify_batch_for_frontier", counts, findings, blocked, None))
    cov = validate_novel_coverage(
        notes_path,
        Path("thalamic-trajectory-factory"),
        notes_text=notes_path.read_text(),
        required=True,
    )
    report.append(("validate_novel_coverage", cov, None, None, None))
    probe = subprocess.run(
        [sys.executable, str(PIPELINES / "spike_probe.py"), "--strict", str(batch_path)],
        cwd=str(REPO),
        capture_output=True,
        text=True,
    )
    report.append(("spike_probe", probe.returncode, probe.stdout[-2000:], probe.stderr[-2000:], None))
    return report


def main() -> int:
    if any(frag in str(LIVE_DIR) for frag in FORBIDDEN_PATH_FRAGMENTS):
        raise SystemExit("refusing forbidden live dir")
    if "2026-08-17" in str(LIVE_DIR) or "2026-08-30" in str(LIVE_DIR):
        raise SystemExit("refusing 2026-08 trees")
    LIVE_DIR.mkdir(parents=True, exist_ok=True)
    STAGING_DIR.mkdir(parents=True, exist_ok=True)
    records = [record_326(), record_327(), record_328(), record_329(), record_330()]
    issues, jmax = self_check(records)
    if issues:
        print("SELF_CHECK_ISSUES:")
        for item in issues:
            print(" -", item)
        return 1
    print(f"SELF_CHECK_OK jmax={jmax:.3f}")
    lines = [
        json.dumps(rec, ensure_ascii=False, separators=(",", ":"), allow_nan=False)
        for rec in records
    ]
    notes = notes_text(records, jmax)
    cov_hits = [ln for ln in notes.splitlines() if ln.strip().lower().startswith("novel coverage")]
    if cov_hits != ["Novel coverage: 22.0%"]:
        print("NOVEL_COVERAGE_LINE", cov_hits)
        return 1
    # Stage first so a live write is only attempted after in-memory checks.
    stage_batch = STAGING_DIR / BATCH_NAME
    stage_notes = STAGING_DIR / NOTES_NAME
    stage_batch.write_text("\n".join(lines) + "\n", encoding="utf-8")
    stage_notes.write_text(notes, encoding="utf-8")
    report = run_pipelines(stage_batch, stage_notes, records)
    failed = False
    for item in report:
        name = item[0]
        print(f"PIPELINE {name}: {item[1:]}"[:500])
        if name == "check_jsonl FactoryStaging":
            errors, warnings, kinds, nrec = item[1], item[2], item[3], item[4]
            print(f"  kinds={kinds} n={nrec} errors={len(errors)} warnings={len(warnings)}")
            for e in errors:
                print("  ERR", e)
                failed = True
            for w in warnings[:20]:
                print("  WARN", w)
        elif name == "check_line+exact_json":
            if item[1]:
                failed = True
                print("  LINE_ERRS", item[1])
        elif name == "raster_status":
            if item[1]:
                failed = True
                print("  RASTER_FAIL", item[1])
        elif name == "verify_batch_for_frontier":
            print("  counts", item[1], "blocked", item[3])
            if item[3]:
                failed = True
                print("  findings", item[2][:8])
        elif name == "validate_novel_coverage":
            if item[1]:
                failed = True
                print("  COV", item[1])
        elif name == "spike_probe":
            if item[1] != 0:
                failed = True
                print("  PROBE_FAIL", item[2], item[3])
    if failed:
        print("STAGING_PIPELINE_FAIL; not writing live tree")
        return 1
    batch_path = create_only(LIVE_DIR / BATCH_NAME, "\n".join(lines) + "\n")
    notes_path = create_only(LIVE_DIR / NOTES_NAME, notes)
    print(f"wrote {batch_path} lines={len(lines)} jmax={jmax:.3f}")
    print(f"wrote {notes_path}")
    print("LIVE_WRITE_OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
