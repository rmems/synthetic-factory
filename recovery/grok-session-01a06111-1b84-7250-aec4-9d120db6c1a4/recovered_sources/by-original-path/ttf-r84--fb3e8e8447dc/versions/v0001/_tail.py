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
        if start <= ev["t_rel_ms"] <= end:
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
        for k, v in obj.items():
            p = f"{path}.{k}" if path else k
            if str(k).lower() in THOUGHT_KEYS:
                found.append(p)
            found.extend(walk_keys(v, p))
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            found.extend(walk_keys(v, f"{path}[{i}]"))
    return found


def notes_text(jmax: float) -> str:
    return f"""# Thalamic Trajectory Factory — NOTES-r84

- Factory: `thalamic-trajectory-factory`
- Run label: `2026-09-02-final-heavy`
- Generator: `grok-4.6`
- Channel: SuperGrok Heavy consumer chat (RM-793 research-only)
- Quota: 5
- Quality: Q=5
- IDs: `ttf-r84-436` … `ttf-r84-440`
- Domains this batch: `nylon-66-salt-autoclave`, `methanol-to-olefins-riser`, `acrylic-acid-oxidation`, `pentane-isomerization-penex`, `fluorine-kf2hf-cell`

These five domain slugs sit outside the prompt 8-pool and outside staged r13–r83 occupancy (jsonl SoT plus incomplete gens r50/r54/r56/r63/r66–r83, including r75 Acheson/ethylbenzene, r76 adiponitrile-EHD / MTBE / Si3N4, r77 steam-char / Catofin / MDI, r78 Cativa / oxo / lyocell / BOF / RH, r79 Ge / Te / Hf / lysine / Se, r80 r70-restack prefix). Harvest includes r52 phosphoric / methanol / anode-bake, r56 pidgeon / PTA / Acheson, r58 spodumene / ferrochrome, r60 TiO2-chloride / SBR, r62 acrylo / vacuum-wash / AOD, r64 isasmelt / phenol-acetone / ERW, r65 wolfram-APT / caprolactam, r67 mond-nickel / maleic-FBR, r68 calcium-carbide / chlorate, r70 aniline / phthalic-switch / MgCl2, r72 Waelz / ATR / Peirce-Smith, r74 VAM / HPPO / Andrussow. All five plants are invented. Do not restack prior TTF plants. Spinelle-Wath / Gorse-Keld / Propenoate-Dell / Isomer-Spurn / Cryolite-Force are this round only.

## Batch map

| id | domain | decision | correctness | sim_or_real | total | edge |
|----|--------|----------|-------------|-------------|-------|------|
| ttf-r84-436 | nylon-66-salt-autoclave | MODIFY | correct | designed | **−0.45** | process-correct salt clamp; gasket blow inside 44 ms raster; independent LIF |
| ttf-r84-437 | methanol-to-olefins-riser | REJECT | **incorrect (wrong-reject)** | designed | −0.60 | live 1.68 bar < 3.20 trip; supervisor binds leftover 0-40 bar span (8.40 bar) + stale 8.50 bar SP |
| ttf-r84-438 | acrylic-acid-oxidation | REJECT | correct | hil | +0.80 | tube AE 48 pps beats IR 312 C; hold oxidizer |
| ttf-r84-439 | pentane-isomerization-penex | ACCEPT | correct | simulated | +1.10 | recycle H2 2.12 bar vs heater smear 3.88; proposed 14.0 t/h already legal |
| ttf-r84-440 | fluorine-kf2hf-cell | ACCEPT | correct | designed | +1.14 | cell 8.6 V vs HF 28 ppm; proposed 6.2 t/d already legal |

Gate mix: 2 ACCEPT, 1 correct MODIFY (partnered-neg, in-window), 1 correct REJECT, 1 incorrect REJECT (stale-setpoint / swapped-range). Provenance: designed×3, simulated×1, hil×1 (Propenoate-Dell PD-HIL oxidation pad). Intra-batch Jaccard on `state.description` {jmax:.3f} (< 0.4).

## Wrong-reject

**ttf-r84-437** is the mandated incorrect gate (`safety_decision.correctness=incorrect`, `meta.supervisor_error_type=wrong-reject`). Alternate vs odd rounds: even rounds host wrong-reject (r12/r14/…/r74/r84); odd rounds host wrong-modify. Do not emit a wrong-ACCEPT. Error *class* is **stale-setpoint / swapped-range**, not r16 reticle-as-wafer, not r18 empty-tank, not r20 oscillation-as-PSV, not r22 class-transplant, not r30 stale-firmware floor, not r32 stale-peak-hold, not r34 wrong-bus, not r36 unit-mismatch leftover-bar, not r38 loop-test-inject, not r40 setpoint-echo, not r42 leftover-SP-as-trip, not r44 wrong-unit-shadow, not r46 kPa-as-MPa, not r50 raw-mA-as-EU, not r52 gauge-vs-absolute / stale-sample, not r58 overrange-flag-as-PV, not r60 absolute-as-gauge, not r62 sign-convention, not r64 reverse-scale / inverted-4-20, not r66 idle-twin-string-as-live, not r74 channel-swap / sibling-loop-as-live.

Gorse-Keld GK-3 / MTO-R2 (LIVE) reads live riser `1.68 bar` on a published **0-8.00 bar** 4-20 mA span (`pv_ma=7.36`) against a published **3.20 bar** trip. A leftover **0-40.00 bar** range card from last campaign scales the same 7.36 mA to **8.40 bar**; a stale **8.50 bar** setpoint from that campaign sits on the faceplate (`swapped_range=true`, `stale_setpoint=true`). Sidecar arithmetic `1.68 < 3.20` is true. A weak supervisor binds the leftover span as live, REJECT-holds methanol 18.0 → 0.0 t/h, and leaves a legal SAPO-34 riser idle. Convictable without MTO physics: `evidence.live_bar < evidence.trip_bar`, `evidence.live_span_bar == 8.00`, `evidence.bound_span_bar == 40.00` on the executed bind, `evidence.scaled_wrong_bar == 8.40`, `evidence.stale_setpoint_bar == 8.50`, `executed_action` sets `feed_tph=0` / `hold=true`, `raster.routing.table` sends `relay.span.stale` → `policy.hold_reject` (weight 0.74) with no positive weight to `policy.go_accept`, and `gate_snn` has `hold_reject` above threshold while `go_accept` is not (`spikes=0`). Recovery: ACCEPT; leave 18.0 t/h; bind published 0-8.00 bar span. Cost: 21 min missed olefin-quality window (`missed_window_s=1260`).

## Partnered-negative in-window (436)

**ttf-r84-436** is the partnered negative: process-correct MODIFY (AH-salt held 8.4 t/h; wall 252 C < 265 cap) while the world still charges. Safety −0.58 prices the 14 mm lid-gasket blow at **22.200 ms**; `task_progress` stays +0.30 because the clamp completed. Inflection `t_us=22200` is tick 5 and is **inside** the 44 ms raster (`22200 ≤ 44000`). Named un-netted loss: 15 min autoclave isolate (`abort_s=900`). Not folded into process heads.

Independent LIF (the one labeled sidecar sim): `state.sim_or_real` remains `designed`. `raster.excerpt_source=independent_lif`, `raster.sim_scope=sidecar_only`, `raster.lif` seed 84386, stim `[21200, 24800]`. Excerpt is membrane crossings (`lif.clamp` early vs `lif.gasket` 21.2–24.8 ms), not a 1:1 remap of `spike_events`. `meta.tags` include `independent-lif-raster` and `sidecar-sim-only`.

## Reward formula and tick reconciliation

Declared aggregation on every record:

`total = task_progress + safety + efficiency + coherence + exploration`

Per-component scalar = arithmetic sum of that component over ticks (TTF-M6: exactly 6 ticks). Tick 6 is bound to a published sidecar (`abort_s`, `missed_window_s`, `survey_hold_s`, `dwell_s`) via `future_outcome.delayed_surprise_s` and is strictly after the raster window. Inflection `t_us` is an actual tick.

| id | ticks | tp | saf | eff | coh | exp | total | inflection tick |
|----|-------|----|-----|-----|-----|-----|-------|-----------------|
| 436 | 6 | +0.30 | −0.58 | −0.16 | +0.04 | −0.05 | −0.45 | 5 (22200) |
| 437 | 6 | −0.20 | −0.11 | −0.23 | −0.12 | +0.06 | −0.60 | 4 (5280) |
| 438 | 6 | +0.10 | +0.42 | +0.12 | +0.10 | +0.06 | +0.80 | 4 (6180) |
| 439 | 6 | +0.42 | +0.30 | +0.18 | +0.12 | +0.08 | +1.10 | 4 (4720) |
| 440 | 6 | +0.44 | +0.30 | +0.20 | +0.12 | +0.08 | +1.14 | 4 (5520) |

Tick-6 sidecar bind: 436 `abort_s=900`, 437 `missed_window_s=1260`, 438 `abort_s=540`, 439 `survey_hold_s=300`, 440 `dwell_s=480`.

## Raster / energy (Loihi-2 4-core, 23 pJ/spike)

| id | domain | n | rate Hz | window_ms | spikes | energy_pJ | energy_uJ |
|----|--------|---|---------|-----------|--------|-----------|-----------|
| 436 | nylon-66-salt-autoclave | 78 | 26 | 44 | 89 | 2047 | 0.002047 |
| 437 | methanol-to-olefins-riser | 96 | 30 | 30 | 86 | 1978 | 0.001978 |
| 438 | acrylic-acid-oxidation | 108 | 24 | 38 | 98 | 2254 | 0.002254 |
| 439 | pentane-isomerization-penex | 60 | 38 | 24 | 55 | 1265 | 0.001265 |
| 440 | fluorine-kf2hf-cell | 48 | 40 | 22 | 42 | 966 | 0.000966 |

`spikes = round(n × rate × window_s)`. Every record carries `gate_snn` whose `decision` matches the safety gate; populations that declare rate+spikes meet the same ±1 budget against `decision_window_s`. `routing.third_factor` has modulator (NA / ACh / DA / 5-HT / adenosine), `tau_e_s`/`tau_e_ms` pair, and eligibility. Excerpt same-neuron gap ≥ 1000 µs; spike trains same-channel refractory ≥ 0.8 ms. Non-436 excerpts are kernelized and independent of `spike_events` times (overlap < 0.8).

## Local checks (staging, not raw)

See generator stdout: `check_jsonl` FactoryStaging, `validate_run.check_line`, `dumps_exact_json`, `raster_status`, `verify_batch_for_frontier(strict=True)`, `spike_probe.py --strict`, tick sums, refractory, Jaccard.

Never `training_ready`. Never `sim_or_real=real`. Never wrote `outputs/raw/`.

## Residual weaknesses (honest)

1. Only **one** labeled independent LIF (436). The other four excerpts are independent of `spike_events` times but are not declared population sims.
2. Wrong-ACCEPT still absent (guard).
3. Tick-6 sidecar bind is standing machinery (r14+), not a new class.
4. Five domain slugs leave the prompt's 8-item pool; a later round that must stay inside the pool will have to rotate sit-outs instead.
5. 437 wrong-reject is sidecar-convictable (routing `to` / bound_span_bar / swapped_range / stale_setpoint) as a **new** error class (stale-setpoint / swapped-range) vs r42 leftover-SP-as-trip, r50 raw-mA-as-EU, r74 channel-swap.
6. 439 and 440 are both already-legal ACCEPTs; a later round could pair an ACCEPT with a world charge that does not go negative.

## Next densification target

Labeled LIF on a second record, or an ISI histogram sidecar. Remaining unused wrong-REJECT subclasses include **cold-junction-offset / thermocouple-type-swap**. Wrong-ACCEPT remains structurally absent until a prompt amendment.

{NOVEL_COVERAGE_LINE}
"""


def self_check(records, notes: str):
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
    domains = [r["state"]["domain"] for r in records]
    if len(set(domains)) != 5:
        issues.append(f"domain collision {domains}")
    if tuple(domains) != THIS_DOMAINS:
        issues.append(f"domain order {domains}")
    prior_domains, prior_plants = harvest_occupancy()
    if set(domains) & prior_domains:
        issues.append(f"restacked domains {set(domains) & prior_domains}")
    blob_all = "\n".join(json.dumps(r) for r in records)
    for plant in THIS_PLANTS:
        if plant not in blob_all:
            issues.append(f"missing plant {plant}")
        if plant in prior_plants:
            issues.append(f"restacked plant {plant}")
    wrong = [
        r
        for r in records
        if r["safety_decision"].get("correctness") == "incorrect"
        or r["meta"].get("supervisor_error_type")
    ]
    if len(wrong) != 1 or wrong[0]["id"] != "ttf-r84-437":
        issues.append(f"wrong-gate set {[w['id'] for w in wrong]}")
    if any(r["state"]["sim_or_real"] == "real" for r in records):
        issues.append("sim_or_real=real")
    hil = [r["id"] for r in records if r["state"]["sim_or_real"] == "hil"]
    if hil != ["ttf-r84-438"]:
        issues.append(f"hil set {hil}")
    decisions = [r["safety_decision"]["decision"] for r in records]
    if (
        decisions.count("ACCEPT") != 2
        or decisions.count("MODIFY") != 1
        or decisions.count("REJECT") != 2
    ):
        issues.append(f"gate mix {decisions}")
    if [r["id"] for r in records] != IDS:
        issues.append(f"ids {[r['id'] for r in records]}")
    for rec in records:
        blob = json.dumps(rec)
        if "training_ready" in blob:
            issues.append(f"{rec['id']} training_ready present")
        hidden = walk_keys(rec)
        if hidden:
            issues.append(f"{rec['id']} hidden keys {hidden}")
        err = check_refractory(rec["spike_events"])
        if err:
            issues.append(f"{rec['id']} refractory {err}")
        err = check_race(rec)
        if err:
            issues.append(f"{rec['id']} {err}")
        n = rec["raster"]["neurons"]
        rate = rec["raster"]["mean_rate_hz"]
        window_s = rec["raster"]["window_s"]
        expected = round(n * rate * window_s)
        if abs(rec["raster"]["spikes"] - expected) > 1:
            issues.append(f"{rec['id']} spike budget {rec['raster']['spikes']} vs {expected}")
        overlap = excerpt_vs_spikes(rec)
        if rec["id"] == "ttf-r84-436":
            if rec["raster"].get("excerpt_source") != "independent_lif":
                issues.append("436 missing independent_lif")
            if rec["future_outcome"]["reward_inflection_t_us"] > rec["raster"]["window_ms"] * 1000:
                issues.append("436 inflection outside window")
            if rec["reward_components"]["total"] >= 0:
                issues.append("436 partnered-neg total not negative")
        elif overlap >= 0.8:
            issues.append(f"{rec['id']} excerpt overlap {overlap:.2f}")
        inf = rec["future_outcome"]["reward_inflection_t_us"]
        tick_times = [t["t_us"] for t in rec["reward_components"]["ticks"]]
        if inf not in tick_times:
            issues.append(f"{rec['id']} inflection {inf} not a tick")
        if len(rec["reward_components"]["ticks"]) != 6:
            issues.append(f"{rec['id']} tick count")
        delayed = rec["future_outcome"].get("delayed_surprise_s")
        if delayed is None:
            issues.append(f"{rec['id']} missing delayed_surprise_s")
        else:
            tick6 = rec["reward_components"]["ticks"][5]["t_us"]
            if tick6 != int(round(float(delayed) * 1e6)):
                issues.append(f"{rec['id']} tick6 {tick6} vs delayed {delayed}")
            if tick6 <= rec["raster"]["window_ms"] * 1000:
                issues.append(f"{rec['id']} tick6 inside raster")
        if not (8 <= len(rec["state"]["episode_steps"]) <= 15):
            issues.append(f"{rec['id']} episode_steps")
        if rec["gate_snn"]["decision"] != rec["safety_decision"]["decision"]:
            issues.append(f"{rec['id']} gate_snn decision mismatch")
        if rec["meta"]["round"] != 84:
            issues.append(f"{rec['id']} meta.round")
        if rec["meta"]["rights"]["intended_use"] != "research_only":
            issues.append(f"{rec['id']} rights")
        if rec["meta"]["rights"]["linear_issue"] != "RM-793":
            issues.append(f"{rec['id']} RM-793")
        heads = ["task_progress", "safety", "efficiency", "coherence", "exploration"]
        total = sum(rec["reward_components"][h] for h in heads)
        if abs(total - rec["reward_components"]["total"]) > 1e-6:
            issues.append(f"{rec['id']} total mismatch {total}")
        for h in heads:
            s = sum(t[h] for t in rec["reward_components"]["ticks"])
            if abs(s - rec["reward_components"][h]) > 1e-6:
                issues.append(f"{rec['id']} {h} tick sum {s} vs {rec['reward_components'][h]}")
        nspk = len(rec["spike_events"])
        if not (5 <= nspk <= 40):
            issues.append(f"{rec['id']} spike count {nspk}")
        times = [e["t_rel_ms"] for e in rec["spike_events"]]
        if times != sorted(times):
            issues.append(f"{rec['id']} spike order")
        exec_p = rec["executed_action"]["parameters"]
        prop_p = rec["proposed_action"]["parameters"]
        if rec["safety_decision"]["decision"] == "ACCEPT" and exec_p != prop_p:
            issues.append(f"{rec['id']} ACCEPT params differ")
        dw_s = rec["gate_snn"]["decision_window_ms"] / 1000.0
        for popu in rec["gate_snn"]["populations"]:
            if "mean_rate_hz" in popu:
                exp = round(popu["neurons"] * popu["mean_rate_hz"] * dw_s)
                if abs(popu["spikes"] - exp) > 1:
                    issues.append(
                        f"{rec['id']} gate_snn {popu['name']} spikes {popu['spikes']} vs {exp}"
                    )
        if not (8 <= len(rec["raster"]["excerpt"]) <= 16):
            issues.append(f"{rec['id']} excerpt n={len(rec['raster']['excerpt'])}")
        if rec["state"]["sim_or_real"] not in {"designed", "simulated", "hil"}:
            issues.append(f"{rec['id']} provenance")
        table_tos = {row["to"] for row in rec["raster"]["routing"]["table"]}
        if rec["id"] == "ttf-r84-437":
            if "policy.go_accept" in table_tos:
                issues.append("437 routing has go_accept")
            if "policy.hold_reject" not in table_tos:
                issues.append("437 missing hold_reject routing")
            ev = rec["proposed_action"]["evidence"]
            if not (ev["live_bar"] < ev["trip_bar"]):
                issues.append("437 live_bar not under trip")
            if rec["executed_action"]["parameters"].get("bound_span_bar") != 40.00:
                issues.append("437 executed span not leftover 40 bar")
            if rec["raster"].get("swapped_range") is not True:
                issues.append("437 missing swapped_range sidecar")
        win_ms = rec["raster"]["window_ms"]
        if not (20 <= win_ms <= 50):
            issues.append(f"{rec['id']} window_ms {win_ms}")
        for item in rec["raster"]["excerpt"]:
            if not (0 <= item["t_us"] <= win_ms * 1000):
                issues.append(f"{rec['id']} excerpt t_us {item['t_us']}")
            if not (0 <= item["neuron_id"] < rec["raster"]["neurons"]):
                issues.append(f"{rec['id']} neuron_id {item['neuron_id']}")
        tf = rec["raster"]["routing"]["third_factor"]
        tau_pair = abs(tf["tau_e_ms"] / 1000.0 - tf["tau_e_s"])
        if tau_pair > 1e-9:
            issues.append(f"{rec['id']} tau_e pair {tf}")
        pj_ok = abs(rec["raster"]["energy_pJ"] - rec["raster"]["spikes"] * 23) > 1e-6
        uj_ok = abs(rec["raster"]["energy_uJ"] - rec["raster"]["spikes"] * 23e-6) > 1e-9
        if pj_ok or uj_ok:
            issues.append(f"{rec['id']} energy")
    notes_hits = [ln for ln in notes.splitlines() if ln.strip().lower().startswith("novel coverage")]
    if notes_hits != [NOVEL_COVERAGE_LINE]:
        issues.append(f"novel coverage lines {notes_hits}")
    return issues, jmax


def run_pipelines(records):
    sys.path.insert(0, str(PIPELINES))
    from check_records import FactoryStaging, check_jsonl
    from curate_bridge import raster_status
    from exact_json import dumps_exact_json
    from round_txn import validate_novel_coverage
    from validate_run import check_line
    from verify_execution import verify_batch_for_frontier

    report = []
    errors, warnings, kinds, nrec = check_jsonl(
        BATCH_PATH, "batch-r84.jsonl", staging=FactoryStaging(enabled=True)
    )
    report.append(("check_jsonl FactoryStaging", errors, warnings, kinds, nrec))
    line_errs = []
    for i, rec in enumerate(records, 1):
        errs, kind = check_line(rec, f"batch-r84.jsonl:{i}", factory_staging=True)
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
    counts, findings, blocked = verify_batch_for_frontier(BATCH_PATH, strict=True)
    report.append(("verify_batch_for_frontier", counts, findings, blocked, None))
    cov = validate_novel_coverage(
        NOTES_PATH,
        Path("thalamic-trajectory-factory"),
        notes_text=NOTES_PATH.read_text(),
        required=True,
    )
    report.append(("validate_novel_coverage", cov, None, None, None))
    probe = subprocess.run(
        [sys.executable, str(PIPELINES / "spike_probe.py"), "--strict", str(BATCH_PATH)],
        cwd=str(REPO),
        capture_output=True,
        text=True,
    )
    report.append(("spike_probe", probe.returncode, probe.stdout[-2000:], probe.stderr[-2000:], None))
    return report


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    records = [record_436(), record_437(), record_438(), record_439(), record_440()]
    descs = [r["state"]["description"] for r in records]
    jmax = 0.0
    for i in range(5):
        for j in range(i + 1, 5):
            jmax = max(jmax, jaccard(descs[i], descs[j]))
    notes = notes_text(jmax)
    issues, jmax2 = self_check(records, notes)
    jmax = max(jmax, jmax2)
    notes = notes_text(jmax)
    issues, _ = self_check(records, notes)
    lines = [
        json.dumps(rec, ensure_ascii=False, separators=(",", ":"), allow_nan=False)
        for rec in records
    ]
    BATCH_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")
    NOTES_PATH.write_text(notes, encoding="utf-8")
    print(f"wrote {BATCH_PATH} lines={len(lines)} jmax={jmax:.3f}")
    print(f"wrote {NOTES_PATH}")
    if issues:
        print("SELF_CHECK_ISSUES:")
        for item in issues:
            print(" -", item)
        return 1
    print("SELF_CHECK_OK")
    report = run_pipelines(records)
    failed = False
    for item in report:
        name = item[0]
        print(f"PIPELINE {name}: {item[1:]}")
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
                print("  FINDINGS", item[2])
        elif name == "validate_novel_coverage":
            if item[1]:
                failed = True
        elif name == "spike_probe":
            if item[1] != 0:
                failed = True
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
