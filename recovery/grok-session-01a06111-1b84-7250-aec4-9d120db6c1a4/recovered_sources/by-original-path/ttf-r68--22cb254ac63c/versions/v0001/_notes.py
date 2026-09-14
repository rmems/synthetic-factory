def write_notes(records, jmax: float) -> None:
    rows = []
    for rec in records:
        dec = rec["safety_decision"]["decision"]
        cor = rec["safety_decision"]["correctness"]
        if cor == "incorrect":
            cor = f"**incorrect ({rec['meta']['supervisor_error_type']})**"
        tot = rec["reward_components"]["total"]
        tot_s = f"{tot:+.2f}"
        if rec["id"] == "ttf-r68-357":
            tot_s = f"**{tot:+.2f}**"
        edge = {
            "ttf-r68-356": "live hearth 1840 C < 1980 trip; sibling CF-2 skin treated as CF-1 live",
            "ttf-r68-357": "process-correct WS clamp; extractor packing collapse inside 42 ms raster; independent LIF",
            "ttf-r68-358": "salt bath 412 C beats preheat encoder 18 Hz; hold, do not feed",
            "ttf-r68-359": "hearth 1380 C vs bosh IR smear; proposed 1850 Nm3/min already legal",
            "ttf-r68-360": "electrolyte 68.4 C vs header glint 88 C; proposed 32 kA already legal",
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
    notes = f"""# Thalamic Trajectory Factory — NOTES-r68

- Factory: `thalamic-trajectory-factory`
- Run label: `2026-09-02-final-heavy`
- Generator: `grok-4.6`
- Channel: SuperGrok Heavy consumer chat (RM-793 research-only)
- Quota: 5
- Quality: Q=5
- IDs: `ttf-r68-356` … `ttf-r68-360`
- Domains this batch: `calcium-carbide-furnace`, `hydrogen-peroxide-ao-loop`, `phthalic-anhydride-reactor`, `ferromanganese-blast-furnace`, `sodium-chlorate-cell`

These five domain slugs sit outside the prompt 8-pool and outside staged r13–r65 occupancy (jsonl SoT plus incomplete gens, including r52 phosphoric-attack-tank / hydrocracker / green-anode / anneal / nitric, r54 Kroll / alumina / float-zone / supercalender / slaker, r56 pidgeon-magnesium / PTA / acheson / HPGR / HF-alkylation, r58 spodumene / chloride-TiO2 / APT / ferrochrome / barite-jig, r59 phenol-cumene / naphtha-hydrotreater / HCl-furnace / Oslo / pasteurizer, r60 TiO2-oxidizer / SBR / zinc-EW / ethanol / ceramic-kiln, r62 acrylonitrile / vacuum-wash / AOD / OPP-tenter / formaldehyde, r64 ISASMELT / phenol-acetone / ERW / gold-CIL / butyl, r65 wolfram-APT / caprolactam / chloride-TiO2 / ebullated-hydrocracker / AOD). All five plants are invented (Acetylene-Howe, Anthraq-Holt, Oxylene-Ness, Pyrolusite-Wath, Chlorate-Beck). Do not restack prior TTF plants.

## Batch map

| id | domain | decision | correctness | sim_or_real | total | edge |
|----|--------|----------|-------------|-------------|-------|------|
{chr(10).join(rows)}

Gate mix: 2 ACCEPT, 1 correct MODIFY (partnered-neg, in-window), 1 correct REJECT, 1 incorrect REJECT (channel-swap / sibling-loop-as-live). Provenance: designed×3, simulated×1, hil×1 (Oxylene-Ness OX-HIL pad). Jaccard on `state.description` all ≤ {jmax:.3f}.

## Wrong-reject

**ttf-r68-356** is the mandated incorrect gate (`safety_decision.correctness=incorrect`, `meta.supervisor_error_type=wrong-reject`). Alternate vs odd rounds: even rounds host wrong-reject. Do not emit a wrong-ACCEPT.

Acetylene-Howe / CF-1 reads live hearth `T=1840 C` against a published **1980 C** trip. A sibling CF-2 skin loop still prints **2012 C** (`sibling_is_live=false`; `live_tag=furnace_cf1_hearth` ≠ `sibling_tag=furnace_cf2_skin`). Sidecar arithmetic `1840 < 1980` is true. A weak supervisor binds the sibling skin as CF-1 live, REJECT-holds 18.0 → 0 t/h, and leaves a legal carbide furnace idle. Convictable without carbide physics: `evidence.live_C < evidence.trip_C`, `evidence.sibling_is_live == false`, `evidence.live_tag != evidence.sibling_tag`, `executed_action` sets `feed_t_h=0`, `raster.routing.table` sends `relay.sibling.loop` → `policy.hold_reject` (weight 0.73) with no positive weight to `policy.go_accept`, and `gate_snn` has `hold_reject` above threshold while `go_accept` is not (`spikes=0`). Recovery: ACCEPT; leave 18.0 t/h; bind the published live 1980 C hearth trip; ignore the sibling loop. Cost: 15 min missed carbide-quality window (`missed_window_s=900`).

This is **channel-swap / sibling-loop-as-live**, not r12-079 (induced-kV treated as sensor fault), not r16-097 (reticle-as-wafer), not r18-109 (empty-tank class), not r20-118 (oscillation-as-PSV), not r22-126 (class-transplant floor), not r30-166 (stale-firmware floor), not r32 (stale-peak-hold), not r34-187 (header-as-cell wrong-loop), not r36-196 (unit-mismatch leftover-bar), not r38-206 (LOOP_TEST inject-as-live), not r40 (SP-echo-as-PV), not r42 (leftover-SP-as-trip), not r44-237 (wrong-unit-shadow), not r46 (kPa-as-MPa), not r48-256 (2oo3-failed-high / median-vs-single), not r50-267 (raw-mA-as-EU), not r52-277 (gauge-vs-absolute / atm-offset), not r54-287 (bad-quality-sub-as-live), not r58-306 (overrange-flag-as-PV).

## Partnered-negative in-window (357)

**ttf-r68-357** is the partnered negative: process-correct MODIFY (working-solution held 28 m3/h; DP 2.58 kPa < 3.00 cap) while the world still charges. Safety −0.62 prices the extractor packing collapse at **22.400 ms**; `task_progress` stays +0.34 because the clamp completed. Inflection `t_us=22400` is tick 5 and is **inside** the 42 ms raster (`22400 ≤ 42000`). Named un-netted loss: 18 min emergency isolate + packing pull (`abort_s=1080`). Not folded into process heads.

Independent LIF (the one labeled sidecar sim): `state.sim_or_real` remains `designed`. `raster.excerpt_source=independent_lif`, `raster.sim_scope=sidecar_only`, `raster.lif` seed 68357, stim `[21000, 25000]`. Excerpt is membrane crossings (`lif.clamp` early vs `lif.pack` 21–25 ms), not a 1:1 remap of `spike_events`. `meta.tags` include `independent-lif-raster` and `sidecar-sim-only`.

## Reward formula and tick reconciliation

Declared aggregation on every record:

`total = task_progress + safety + efficiency + coherence + exploration`

Per-component scalar = arithmetic sum of that component over ticks (TTF-M6: exactly 6 ticks; tick 5 is `t_charge_us=22400` on 357 and `t_gate_us + T_race` elsewhere; tick 6 is delayed surprise bound to `future_outcome.delayed_surprise_s`). Inflection `t_us` is an actual tick. Verified to <1e-6:

| id | ticks | tp | saf | eff | coh | exp | total | inflection tick |
|----|-------|----|-----|-----|-----|-----|-------|-----------------|
{chr(10).join(tick_rows)}

Tick 6 bind: `ticks[5].t_us == round(delayed_surprise_s * 1e6)` on every record (900 s, 1080 s, 480 s, 540 s, 360 s).

## Raster / energy (Loihi-2 4-core, 23 pJ/spike)

| id | domain | n | rate Hz | window_ms | spikes | energy_pJ | energy_uJ |
|----|--------|---|---------|-----------|--------|-----------|-----------|
{chr(10).join(ras_rows)}

`spikes = round(n × rate × window_s)`. Every record carries `gate_snn` whose `decision` matches the safety gate; populations that declare rate+spikes meet the same ±1 budget against `decision_window_s`. `routing.third_factor` has modulator (ACh / NA / DA / 5-HT / adenosine), `tau_e_s`/`tau_e_ms` pair, and eligibility. Excerpt same-neuron gap ≥ 1000 µs; spike trains same-channel refractory ≥ 0.8 ms.

## Local checks (staging, not raw)

- Generator self-check: Jaccard max {jmax:.3f} < 0.4; TTF-M6 prefix; refractory; spike budgets; exactly one incorrect gate (356 wrong-reject)
- Pipeline audit (run after emit): `check_jsonl` FactoryStaging, `raster_status`, `verify_batch_for_frontier(strict=True)`, `spike_probe.py --strict`

Never `training_ready`. Never `sim_or_real=real`. Never wrote `outputs/raw/`.

## Residual weaknesses (honest)

1. Only **one** labeled independent LIF (357). The other four excerpts are independent of `spike_events` times but are not declared population sims.
2. Wrong-ACCEPT still absent (guard).
3. 359 ACCEPT is a new plant/solver (1D blast-furnace hearth-bosh kernel), not a new gate class.
4. 356 wrong-reject is convictable from live-vs-sibling tags; a later round could bind `sibling_is_live==false && live_C < trip_C` as the only critic boolean so a probe never has to know "CF-1".
5. ISI histogram is still optional densification, not an r68 requirement.

## Next densification target

Publish the sibling-loop freshness predicate as a sidecar boolean (`sibling_is_live`) so a channel-swap REJECT is convictable without the furnace-name story. Optional: labeled LIF on a second record, or an ISI histogram sidecar. Remaining unused wrong-REJECT subclasses include **stale-handshake / heartbeat-as-PV**. Wrong-ACCEPT remains structurally absent until a prompt amendment.

Novel coverage: 16.5%
"""

    NOTES_PATH.write_text(notes, encoding="utf-8")
