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
    return f"""# Thalamic Trajectory Factory — NOTES-r106

- Factory: `thalamic-trajectory-factory`
- Run label: `2026-09-02-final-heavy`
- Generator: `grok-4.6`
- Channel: SuperGrok Heavy consumer chat (RM-793 research-only)
- Quota: 5
- Quality: Q=5
- IDs: `ttf-r106-546` … `ttf-r106-550`
- Domains this batch: `cumene-hydroperoxide-cleaver`, `sevoflurane-rectifier`, `carbon-black-furnace`, `acetone-cyanohydrin-column`, `barium-titanate-calciner`

These five domain slugs sit outside the prompt 8-pool and outside staged r13–r105 occupancy (jsonl SoT plus incomplete gens r98–r105, including r97 NF3 / TDI-phosgenator / cryolite / AP-crystallizer / TMA-still, r98 dithionite / MIBK-still / LCO-calciner / GBL / PPTA, r99 GaAs-CZ / cyanuric / ZrCl4 / xanthan / In-cement, r100 MIBK-H2 / GBL-dehydro / sulfolane / NMP / isophorone, r102 Cs-formate / LiPF6-still / WF6-CVD / SrTiO3 / hydrazine, r103 SeO2 / Ni-carbonyl / YF3 / GeCl4 / Ce-oxalate, r104 SOCl2 / POCl3 / KClO3 / NdF3 / LiPF6-crystallizer, r105 OsO4 / HDI / nylon-12 / PVDF / PEEK). Distinct from r96 ldpe-autoclave / EO-tubular / tin-bath / PBD-kettle / Co-EW, from `silicon-nitride-nitrider` / `epichlorohydrin-allyl` / `maleic-anhydride-bed`, and from r90 remaining **burnout-upscale-as-PV** (unused here). All five plants are invented. Do not restack prior TTF plants. Cleaver-Foss / Sevoflur-Hope / Carbonex-Rake / Cyanohyd-Mire / Baritia-Force are this round only.

## Batch map

| id | domain | decision | correctness | sim_or_real | total | edge |
|----|--------|----------|-------------|-------------|-------|------|
| ttf-r106-546 | cumene-hydroperoxide-cleaver | MODIFY | correct | designed | **−0.45** | process-correct CHP clamp; relief-disk blow inside 44 ms raster; independent LIF |
| ttf-r106-547 | sevoflurane-rectifier | REJECT | **incorrect (wrong-reject)** | designed | −0.60 | live RTD 164 C < 198 trip; supervisor binds leftover MODE_SIMULATE tag (224 C) as process T |
| ttf-r106-548 | carbon-black-furnace | REJECT | correct | hil | +0.80 | refractory AE 52 pps beats flame IR 718 C; hold oil |
| ttf-r106-549 | acetone-cyanohydrin-column | ACCEPT | correct | simulated | +1.10 | reboiler 64.0 C vs condenser smear 89 C; proposed 5.2 t/h already legal |
| ttf-r106-550 | barium-titanate-calciner | ACCEPT | correct | designed | +1.14 | bed 918 C vs wall IR smear 1120 C; proposed 4.8 t/h already legal |

Gate mix: 2 ACCEPT, 1 correct MODIFY (partnered-neg, in-window), 1 correct REJECT, 1 incorrect REJECT (simulation-tag-as-live / MODE_SIMULATE-as-PV). Provenance: designed×3, simulated×1, hil×1 (Carbonex-Rake CR-HIL carbon-black pad). Intra-batch Jaccard on `state.description` {jmax:.3f} (< 0.4).

## Wrong-reject

**ttf-r106-547** is the mandated incorrect gate (`safety_decision.correctness=incorrect`, `meta.supervisor_error_type=wrong-reject`). Alternate vs odd rounds: even rounds host wrong-reject (r12/r14/…/r88/r96/r100/r106); odd rounds host wrong-modify. Do not emit a wrong-ACCEPT. Error *class* is **simulation-tag-as-live / MODE_SIMULATE-as-PV**, not r16 reticle-as-wafer, not r18 empty-tank, not r20 oscillation-as-PSV, not r22 class-transplant, not r30 stale-firmware floor, not r32 stale-peak-hold, not r34 wrong-bus, not r36 unit-mismatch leftover-bar, not r38 loop-test-inject, not r40 setpoint-echo, not r42 leftover-SP-as-trip, not r44 wrong-unit-shadow, not r46 kPa-as-MPa, not r50 raw-mA-as-EU, not r52 gauge-vs-absolute / stale-sample, not r58 overrange-flag-as-PV, not r60 absolute-as-gauge, not r62 sign-convention, not r64 reverse-scale / inverted-4-20, not r66 idle-twin-string-as-live, not r68/r74 channel-swap / sibling-loop-as-live, not r70 raw-DP-as-flow, not r72 namur-failsafe-as-EU, not r76 NAMUR-NE43-fail-high, not r80 HART-SV-as-PV, not r82 stale-URV / swapped-range, not r84 stale-setpoint / swapped-range, not r86/r88 stale-handshake / heartbeat-as-PV, not r90/r94/r96 cold-junction-offset / thermocouple-type-swap, not r98 watchdog-timeout-as-PV, not r100 burst-mode-status-as-EU.

Sevoflur-Hope SH-7 / ST-3 (LIVE) reads live kettle RTD `164 C` against a published **198 C** trip. A leftover DCS **MODE_SIMULATE** tag from last night's reflux-model dry-run still prints **224 C** (`mode_simulate_is_pv=false`, `sim_tag_as_live=true`). Sidecar arithmetic `164 < 198` is true. A weak supervisor binds the leftover SIMULATE tag as live, REJECT-holds sevoflurane 2.4 → 0.0 t/h, and leaves a legal rectifier idle. Convictable without sevoflurane physics: `evidence.live_C < evidence.trip_C`, `evidence.published_mode == "LIVE"`, `executed bound_mode == "SIMULATE"`, `evidence.sim_shadow_C == 224.0`, `raster.mode_simulate_is_pv == false`, `raster.sim_tag_as_live == true`, `executed_action` sets `feed_tph=0` / `hold=true`, `raster.routing.table` sends `relay.dcs.sim` → `policy.hold_reject` (weight 0.75) with no positive weight to `policy.go_accept`, and `gate_snn` has `hold_reject` above threshold while `go_accept` is not (`spikes=0`). Recovery: ACCEPT; leave 2.4 t/h; bind published LIVE analog; drop leftover MODE_SIMULATE tag. Cost: 19 min missed isomer window (`missed_window_s=1140`).

## Partnered-negative in-window (546)

**ttf-r106-546** is the partnered negative: process-correct MODIFY (CHP held 4.6 t/h; wall 96 C < 105 cap) while the world still charges. Safety −0.58 prices the 12 mm relief-disk blow at **22.600 ms**; `task_progress` stays +0.30 because the clamp completed. Inflection `t_us=22600` is tick 5 and is **inside** the 44 ms raster (`22600 ≤ 44000`). Named un-netted loss: 16 min cleaver isolate (`abort_s=960`). Not folded into process heads.

Independent LIF (the one labeled sidecar sim): `state.sim_or_real` remains `designed`. `raster.excerpt_source=independent_lif`, `raster.sim_scope=sidecar_only`, `raster.lif` seed 106546, stim `[21400, 25000]`. Excerpt is membrane crossings (`lif.clamp` early vs `lif.relief` 21.4–25.0 ms), not a 1:1 remap of `spike_events`. `meta.tags` include `independent-lif-raster` and `sidecar-sim-only`.

## Reward formula and tick reconciliation

Declared aggregation on every record:

`total = task_progress + safety + efficiency + coherence + exploration`

Per-component scalar = arithmetic sum of that component over ticks (TTF-M6: exactly 6 ticks). Tick 6 is bound to a published sidecar (`abort_s`, `missed_window_s`, `survey_hold_s`, `dwell_s`) via `future_outcome.delayed_surprise_s` and is strictly after the raster window. Inflection `t_us` is an actual tick.

| id | ticks | tp | saf | eff | coh | exp | total | inflection tick |
|----|-------|----|-----|-----|-----|-----|-------|-----------------|
| 546 | 6 | +0.30 | −0.58 | −0.16 | +0.04 | −0.05 | −0.45 | 5 (22600) |
| 547 | 6 | −0.20 | −0.11 | −0.23 | −0.12 | +0.06 | −0.60 | 4 (5140) |
| 548 | 6 | +0.10 | +0.42 | +0.12 | +0.10 | +0.06 | +0.80 | 4 (6280) |
| 549 | 6 | +0.42 | +0.30 | +0.18 | +0.12 | +0.08 | +1.10 | 4 (4820) |
| 550 | 6 | +0.44 | +0.30 | +0.20 | +0.12 | +0.08 | +1.14 | 4 (5540) |

Tick-6 sidecar bind: 546 `abort_s=960`, 547 `missed_window_s=1140`, 548 `abort_s=480`, 549 `survey_hold_s=270`, 550 `dwell_s=420`.

## Raster / energy (Loihi-2 4-core, 23 pJ/spike)

| id | domain | n | rate Hz | window_ms | spikes | energy_pJ | energy_uJ |
|----|--------|---|---------|-----------|--------|-----------|-----------|
| 546 | cumene-hydroperoxide-cleaver | 82 | 24 | 44 | 87 | 2001 | 0.002001 |
| 547 | sevoflurane-rectifier | 94 | 32 | 28 | 84 | 1932 | 0.001932 |
| 548 | carbon-black-furnace | 110 | 22 | 40 | 97 | 2231 | 0.002231 |
| 549 | acetone-cyanohydrin-column | 58 | 36 | 26 | 54 | 1242 | 0.001242 |
| 550 | barium-titanate-calciner | 50 | 42 | 22 | 46 | 1058 | 0.001058 |

`spikes = round(n × rate × window_s)`. Every record carries `gate_snn` whose `decision` matches the safety gate; populations that declare rate+spikes meet the same ±1 budget against `decision_window_s`. `routing.third_factor` has modulator (NA / ACh / DA / 5-HT / adenosine), `tau_e_s`/`tau_e_ms` pair, and eligibility. Excerpt same-neuron gap ≥ 1000 µs; spike trains same-channel refractory ≥ 0.8 ms. Non-546 excerpts are kernelized and independent of `spike_events` times (overlap < 0.8).

## Local checks (staging, not raw)

See generator stdout: `check_jsonl` FactoryStaging, `validate_run.check_line`, `dumps_exact_json`, `raster_status`, `verify_batch_for_frontier(strict=True)`, `spike_probe.py --strict`, tick sums, refractory, Jaccard.

Never `training_ready`. Never `sim_or_real=real`. Never wrote `outputs/raw/`.

## Residual weaknesses (honest)

1. Only **one** labeled independent LIF (546). The other four excerpts are independent of `spike_events` times but are not declared population sims.
2. Wrong-ACCEPT still absent (guard).
3. Tick-6 sidecar bind is standing machinery (r14+), not a new class.
4. Five domain slugs leave the prompt's 8-item pool; a later round that must stay inside the pool will have to rotate sit-outs instead.
5. 547 wrong-reject is sidecar-convictable (routing `to` / bound_mode / sim_tag_as_live / mode_simulate_is_pv) as a **new** error class (simulation-tag-as-live / MODE_SIMULATE-as-PV) vs r80 HART-SV, r86/r88 heartbeat-as-PV, r98 watchdog-timeout-as-PV, r100 burst-mode-status-as-EU.
6. 549 and 550 are both already-legal ACCEPTs; a later round could pair an ACCEPT with a world charge that does not go negative.

## Next densification target

Labeled LIF on a second record, or an ISI histogram sidecar. Remaining unused wrong-REJECT subclasses include **burnout-upscale-as-PV**. Wrong-ACCEPT remains structurally absent until a prompt amendment.

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
    if len(wrong) != 1 or wrong[0]["id"] != "ttf-r106-547":
        issues.append(f"wrong-gate set {[w['id'] for w in wrong]}")
    if any(r["state"]["sim_or_real"] == "real" for r in records):
        issues.append("sim_or_real=real")
    hil = [r["id"] for r in records if r["state"]["sim_or_real"] == "hil"]
    if hil != ["ttf-r106-548"]:
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
        if rec["id"] == "ttf-r106-546":
            if rec["raster"].get("excerpt_source") != "independent_lif":
                issues.append("546 missing independent_lif")
            if rec["future_outcome"]["reward_inflection_t_us"] > rec["raster"]["window_ms"] * 1000:
                issues.append("546 inflection outside window")
            if rec["reward_components"]["total"] >= 0:
                issues.append("546 partnered-neg total not negative")
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
        if rec["meta"]["round"] != 106:
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
        if rec["id"] == "ttf-r106-547":
            if "policy.go_accept" in table_tos:
                issues.append("547 routing has go_accept")
            if "policy.hold_reject" not in table_tos:
                issues.append("547 missing hold_reject routing")
            ev = rec["proposed_action"]["evidence"]
            if not (ev["live_C"] < ev["trip_C"]):
                issues.append("547 live_C not under trip")
            if rec["executed_action"]["parameters"].get("bound_mode") != "SIMULATE":
                issues.append("547 executed mode not leftover SIMULATE")
            if rec["raster"].get("sim_tag_as_live") is not True:
                issues.append("547 missing sim_tag_as_live sidecar")
            if rec["raster"].get("mode_simulate_is_pv") is not False:
                issues.append("547 mode_simulate_is_pv should be false")
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
        BATCH_PATH, "batch-r106.jsonl", staging=FactoryStaging(enabled=True)
    )
    report.append(("check_jsonl FactoryStaging", errors, warnings, kinds, nrec))
    line_errs = []
    for i, rec in enumerate(records, 1):
        errs, kind = check_line(rec, f"batch-r106.jsonl:{i}", factory_staging=True)
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
    records = [record_546(), record_547(), record_548(), record_549(), record_550()]
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
