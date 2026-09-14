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
            if str(k).lower() in THOUGHT_KEYS or str(k).lower() in {
                "chain_of_thought",
                "hidden_reasoning",
            }:
                found.append(p)
            found.extend(walk_keys(v, p))
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            found.extend(walk_keys(v, f"{path}[{i}]"))
    return found


def prior_descriptions():
    descs = []
    paths = list(Path("/tmp").glob("ttf-r*/batch-r*.jsonl"))
    if WINDOW_FACTORY.is_dir():
        paths.extend(WINDOW_FACTORY.glob("batch-r*.jsonl"))
    for path in sorted(set(paths)):
        if path.parent.name == "ttf-r42w":
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except OSError:
            continue
        for line in text.splitlines():
            if not line.strip():
                continue
            rec = json.loads(line)
            d = (rec.get("state") or {}).get("description")
            if isinstance(d, str):
                descs.append(d)
    return descs


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
    jprior = 0.0
    for d in prior_descriptions():
        for mine in descs:
            jprior = max(jprior, jaccard(d, mine))
    if jprior >= 0.4:
        issues.append(f"prior Jaccard {jprior:.3f}")
    domains = [r["state"]["domain"] for r in records]
    if tuple(domains) != THIS_DOMAINS:
        issues.append(f"domain set {domains}")
    if set(domains) & SITOUT_DOMAINS:
        issues.append(f"sitout domains {set(domains) & SITOUT_DOMAINS}")
    occ_d, occ_p = harvest_occupancy()
    if set(domains) & occ_d:
        issues.append(f"live occupancy collision {set(domains) & occ_d}")
    blob_all = "\n".join(json.dumps(r) for r in records)
    for plant in THIS_PLANTS:
        if plant not in blob_all:
            issues.append(f"missing plant {plant}")
        if plant in occ_p:
            issues.append(f"restacked occupancy plant {plant}")
    wrong = [
        r
        for r in records
        if r["safety_decision"].get("correctness") == "incorrect"
        or r["meta"].get("supervisor_error_type")
    ]
    if len(wrong) != 1 or wrong[0]["id"] != "ttf-r42-702":
        issues.append(f"wrong-gate set {[w['id'] for w in wrong]}")
    if wrong and wrong[0]["meta"].get("supervisor_error_type") != "wrong-reject":
        issues.append("expected wrong-reject")
    if any(r["state"]["sim_or_real"] == "real" for r in records):
        issues.append("sim_or_real=real")
    hil = [r["id"] for r in records if r["state"]["sim_or_real"] == "hil"]
    if hil != ["ttf-r42-703"]:
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
        if rec["id"] == "ttf-r42-701":
            if rec["raster"].get("excerpt_source") != "independent_lif":
                issues.append("701 missing independent_lif")
            if rec["future_outcome"]["reward_inflection_t_us"] > rec["raster"]["window_ms"] * 1000:
                issues.append("701 inflection outside window")
            if rec["reward_components"]["total"] >= 0:
                issues.append("701 partnered-neg total not negative")
        elif overlap >= 0.8:
            issues.append(f"{rec['id']} excerpt overlap {overlap:.2f}")
        inf = rec["future_outcome"]["reward_inflection_t_us"]
        tick_times = [t["t_us"] for t in rec["reward_components"]["ticks"]]
        if inf not in tick_times:
            issues.append(f"{rec['id']} inflection {inf} not a tick")
        if len(rec["reward_components"]["ticks"]) != 6:
            issues.append(f"{rec['id']} tick count")
        if not (8 <= len(rec["state"]["episode_steps"]) <= 15):
            issues.append(f"{rec['id']} episode_steps")
        if rec["gate_snn"]["decision"] != rec["safety_decision"]["decision"]:
            issues.append(f"{rec['id']} gate_snn decision mismatch")
        if rec["meta"]["round"] != 42:
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
        if rec["id"] == "ttf-r42-702":
            if "policy_still_go" in table_tos:
                issues.append("702 routing has still_go")
            if "policy_still_hold" not in table_tos:
                issues.append("702 missing still_hold routing")
        win_ms = rec["raster"]["window_ms"]
        if not (20 <= win_ms <= 50):
            issues.append(f"{rec['id']} window_ms {win_ms}")
        for item in rec["raster"]["excerpt"]:
            if not (0 <= item["t_us"] <= win_ms * 1000):
                issues.append(f"{rec['id']} excerpt t_us {item['t_us']}")
            if not (0 <= item["neuron_id"] < rec["raster"]["neurons"]):
                issues.append(f"{rec['id']} neuron_id {item['neuron_id']}")
        lat = rec["state"]["gate_latency_us"]
        win = rec["state"]["race_window_us"]
        if not (50 <= lat <= 2000):
            issues.append(f"{rec['id']} gate_latency {lat}")
        if not (50 <= win <= 1000):
            issues.append(f"{rec['id']} race_window {win}")
    return issues, jmax, jprior


def notes_text(jmax: float, jprior: float) -> str:
    return f"""# Thalamic Trajectory Factory — NOTES-r42

- Factory: `thalamic-trajectory-factory`
- Run label: `2026-09-02-final-heavy`
- Generator: `grok-4.6`
- Channel: SuperGrok Heavy consumer chat (RM-793 research-only)
- Quota: 5
- Quality: Q=5
- IDs: `ttf-r42-701` … `ttf-r42-705` (226–230 already occupy `/tmp/ttf-r42`; this window uses 701–705)
- Domains this batch: `potassium-perchlorate-crystallizer`, `holmium-chloride-still`, `gadolinium-gallium-garnet-puller`, `erbium-oxide-calciner`, `thulium-metal-distiller`

These five domain slugs sit outside the prompt 8-pool and outside staged occupancy (jsonl + generator SoT), including original r42 (`brick-tunnel-kiln` / `steam-methane-reformer` / `Bayer-digester` / `polyethylene-loop-reactor` / `copper-electrorefining`) and window r01/r21/r41/r61. All five plants are invented (Perchlor-Beck, Holmia-Knap, Garnet-Wold, Erbia-Clough, Thulia-Fen). Do not restack prior TTF plants. Original r42 leftover-SP-as-trip is not restacked.

## Batch map

| id | domain | decision | correctness | sim_or_real | total | edge |
|----|--------|----------|-------------|-------------|-------|------|
| ttf-r42-701 | potassium-perchlorate-crystallizer | MODIFY | correct | designed | **−0.48** | process-correct liquor clamp; scraper-blade jam inside 42 ms raster; independent LIF |
| ttf-r42-702 | holmium-chloride-still | REJECT | **incorrect (wrong-reject / burst-mode-status-as-EU)** | designed | −0.68 | live 2.40 bar valid 8.16 mA < 5.60 cap; supervisor treats HART burst STATUS 0x80 as 7.20 bar EU |
| ttf-r42-703 | gadolinium-gallium-garnet-puller | REJECT | correct | hil | +0.80 | AE 48 pps beats pull encoder 2.10 mm/min; hold, do not pull 0.28 |
| ttf-r42-704 | erbium-oxide-calciner | ACCEPT | correct | simulated | +1.06 | bed 842 C vs hood IR 980 C smear; proposed 4.8 t/h already legal |
| ttf-r42-705 | thulium-metal-distiller | ACCEPT | correct | designed | +1.14 | still 1280 C vs condenser DP 7.8 kPa; proposed 0.38 kg/h already legal; ISI histogram |

Gate mix: 2 ACCEPT, 1 correct MODIFY (partnered-neg, in-window), 1 correct REJECT, 1 incorrect REJECT (burst-mode-status-as-EU). Provenance: designed×3, simulated×1, hil×1 (Garnet-Wold GW-HIL GGG pull axis). Intra-batch Jaccard on `state.description` {jmax:.3f} (max vs prior staged {jprior:.3f}).

## Wrong-reject

**ttf-r42-702** is the mandated incorrect gate (`safety_decision.correctness=incorrect`, `meta.supervisor_error_type=wrong-reject`). Alternate vs odd rounds: even rounds host wrong-reject. Do not emit a wrong-ACCEPT. Error *class* is **burst-mode-status-as-EU**, the r98 densification subclass, not original r42 leftover-SP-as-trip, not r40 SP-echo-as-PV, not r50 raw-mA-as-EU, not r76 NAMUR fail-high, not r80 HART SV-as-PV, not r86/r88 heartbeat-as-PV, not r98 watchdog-timeout-as-PV.

Holmia-Knap HK-6 / Still ST-8 reads live kettle `2.40 bar` on a valid `8.16 mA` loop against a published **5.60 bar** trip. A leftover HART burst-mode STATUS word `0x80` is still scaled as if it were a 4-20 mA EU and prints **7.20 bar** (`burst_age_ms=6200` > `max_legal_burst_age_ms=250`; `burst_is_pv=false`; `burst_mode_status_as_eu=true`). Sidecar arithmetic `2.40 < 5.60` is true. A weak supervisor binds the burst STATUS as live PV, REJECT-holds feed 3.6 → 0.0 t/h, and leaves a legal HoCl3 still idle. Convictable without HoCl3 physics: `evidence.live_bar < evidence.live_cap_bar`, `burst_is_pv == false`, `burst_age_ms > max_legal_burst_age_ms`, `executed_action` sets `feed_tph=0` / `hold=true`, `raster.routing.table` sends `relay_hart_burst` → `policy_still_hold` (weight 0.74) with no positive weight to `policy_still_go`, and `gate_snn` has `still_hold` above threshold while `still_go` is not. Recovery: ACCEPT the 3.6 t/h distillate; leave 7.20 bar as a burst diagnostic. Cost: missed 18 min chloride-quality window (`missed_window_s=1080`).

## Partnered-negative in-window (701)

**ttf-r42-701** is the partnered negative: process-correct MODIFY (feed held 11.2 t/h; liquor 70.8 C <= 72 cap) while the world still charges. Safety −0.64 prices the scraper-blade jam at **22.200 ms**; `task_progress` stays +0.30 because the clamp completed. Inflection `t_us=22200` is tick 5 and is **inside** the 42 ms raster (`22200 ≤ 42000`). Named un-netted loss: 14 min basket re-pack (`abort_s=840`). Not folded into process heads.

Independent LIF (the one labeled sidecar sim): `state.sim_or_real` remains `designed`. `raster.excerpt_source=independent_lif`, `raster.sim_scope=sidecar_only`, `raster.lif` seed 42701, stim `[22000, 25000]`. Excerpt is membrane crossings (`lif.clamp` early vs `lif.jam` 22–25 ms), not a 1:1 remap of `spike_events`. `meta.tags` include `independent-lif-raster` and `sidecar-sim-only`.

## ISI histogram (705)

**ttf-r42-705** carries `raster.isi_histogram` (bin 0.8 ms, same-channel ISIs from `spike_events`, min gap ≥ 0.8 ms). Addresses the standing densification ask for an ISI sidecar without claiming a second labeled LIF.

## Reward formula and tick reconciliation

Declared aggregation on every record:

`total = task_progress + safety + efficiency + coherence + exploration`

Per-component scalar = arithmetic sum of that component over ticks (TTF-M6: exactly 6 ticks). Tick 6 is bound to a published sidecar (`abort_s`, `missed_window_s`, `survey_s`) and is strictly after the raster window. Inflection `t_us` is an actual tick.

| id | ticks | tp | saf | eff | coh | exp | total | inflection tick |
|----|-------|----|-----|-----|-----|-----|-------|-----------------|
| 701 | 6 | +0.30 | −0.64 | −0.14 | +0.04 | −0.04 | −0.48 | 5 (22200) |
| 702 | 6 | −0.22 | −0.24 | −0.18 | −0.10 | +0.06 | −0.68 | 4 (6040) |
| 703 | 6 | +0.10 | +0.42 | +0.12 | +0.10 | +0.06 | +0.80 | 4 (7860) |
| 704 | 6 | +0.40 | +0.28 | +0.18 | +0.12 | +0.08 | +1.06 | 4 (8480) |
| 705 | 6 | +0.44 | +0.30 | +0.20 | +0.12 | +0.08 | +1.14 | 4 (5440) |

Tick-6 sidecar bind: 701 `abort_s=840`, 702 `missed_window_s=1080`, 703 `abort_s=480`, 704 `survey_s=180`, 705 `survey_s=240`.

## Raster / energy (Loihi-2 4-core, 23 pJ/spike)

| id | domain | n | rate Hz | window_ms | spikes | energy_pJ | energy_uJ |
|----|--------|---|---------|-----------|--------|-----------|-----------|
| 701 | potassium-perchlorate-crystallizer | 76 | 24 | 42 | 77 | 1771 | 0.001771 |
| 702 | holmium-chloride-still | 96 | 32 | 28 | 86 | 1978 | 0.001978 |
| 703 | gadolinium-gallium-garnet-puller | 112 | 20 | 46 | 103 | 2369 | 0.002369 |
| 704 | erbium-oxide-calciner | 64 | 40 | 26 | 67 | 1541 | 0.001541 |
| 705 | thulium-metal-distiller | 80 | 28 | 24 | 54 | 1242 | 0.001242 |

`spikes = round(n × rate × window_s)`. Every record carries `gate_snn` whose `decision` matches the safety gate; populations that declare rate+spikes meet the same ±1 budget against `decision_window_s`. `routing.third_factor` has modulator (NA / ACh / DA / 5-HT / octopamine), `tau_e_s`/`tau_e_ms` pair, and eligibility. Excerpt same-neuron gap ≥ 1000 µs; spike trains same-channel refractory ≥ 0.8 ms. Non-701 excerpts are kernelized and independent of `spike_events` times (overlap < 0.8).

## Local checks (staging, not a rewrite of other raw files)

See generator stdout: `check_jsonl` FactoryStaging, `validate_run.check_line`, `dumps_exact_json`, `raster_status`, `verify_batch_for_frontier(strict=True)`, `spike_probe.py --strict`, tick sums, refractory, Jaccard.

Never `training_ready`. Never `sim_or_real=real`. Create-only write of this round's batch/NOTES under the operator window.

## Residual weaknesses (honest)

1. Only **one** labeled independent LIF (701). 705 adds an ISI histogram but is not a second population sim.
2. Wrong-ACCEPT still absent (guard).
3. 704 and 705 are both already-legal ACCEPTs; a later round could pair one ACCEPT with a world charge that does not go negative, or drop to a single ACCEPT.
4. Five domain slugs leave the prompt's 8-item pool; a later round that must stay inside the pool will have to rotate sit-outs instead.
5. Tick-6 sidecar bind is standing machinery (r14+), not a new class.
6. 702 wrong-reject is sidecar-convictable (`burst_is_pv` / routing `to`) as a **new** error class vs original r42 leftover-SP-as-trip and r98 watchdog-timeout-as-PV.

## Next densification target

Labeled LIF on a second record, or bind `burst_status_word` vs `live_mA` as the only critic features. Remaining unused even-round wrong-REJECT subclasses include **device-status-bit-as-PV**. Wrong-ACCEPT remains structurally absent until a prompt amendment.

{NOVEL_COVERAGE_LINE}
"""


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
        BATCH_PATH, "batch-r42.jsonl", staging=FactoryStaging(enabled=True)
    )
    report.append(("check_jsonl FactoryStaging", errors, warnings, kinds, nrec))
    line_errs = []
    for i, rec in enumerate(records, 1):
        errs, kind = check_line(rec, f"batch-r42.jsonl:{i}", factory_staging=True)
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
    if "outputs/raw" in str(BATCH_PATH) or "outputs/raw" in str(NOTES_PATH):
        print("refusing to write outputs/raw")
        return 1
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    records = [record_701(), record_702(), record_703(), record_704(), record_705()]
    issues, jmax, jprior = self_check(records)
    notes = notes_text(jmax, jprior)
    cov_hits = [ln for ln in notes.splitlines() if ln.strip().lower().startswith("novel coverage")]
    if cov_hits != [NOVEL_COVERAGE_LINE]:
        issues.append(f"novel coverage lines {cov_hits}")
    lines = [
        json.dumps(rec, ensure_ascii=False, separators=(",", ":"), allow_nan=False)
        for rec in records
    ]
    BATCH_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")
    NOTES_PATH.write_text(notes, encoding="utf-8")
    print(
        f"wrote {BATCH_PATH} lines={len(lines)} bytes={BATCH_PATH.stat().st_size} "
        f"jmax={jmax:.3f} jprior={jprior:.3f}"
    )
    print(f"wrote {NOTES_PATH} bytes={NOTES_PATH.stat().st_size}")
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
                print("  findings", item[2][:8])
        elif name == "validate_novel_coverage":
            if item[1]:
                failed = True
        elif name == "spike_probe":
            if item[1] != 0:
                failed = True
                print("  PROBE_FAIL", item[2], item[3])
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
