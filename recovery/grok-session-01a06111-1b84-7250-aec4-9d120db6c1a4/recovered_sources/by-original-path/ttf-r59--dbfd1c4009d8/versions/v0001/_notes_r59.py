def notes_text(jmax: float, jprior: float) -> str:
    return f"""# Thalamic Trajectory Factory — NOTES-r59

- Factory: `thalamic-trajectory-factory`
- Run label: `2026-09-02-final-heavy`
- Generator: `grok-4.6`
- Channel: SuperGrok Heavy consumer chat (RM-793 research-only)
- Quota: 5
- Quality: Q=5
- IDs: `ttf-r59-311` … `ttf-r59-315`
- Domains this batch: `phenol-cumene-oxidizer`, `naphtha-hydrotreater`, `hcl-synthesis-furnace`, `oslo-crystallizer`, `tunnel-pasteurizer`

These five domain slugs sit outside the prompt 8-pool and outside staged r13–r55 occupancy (jsonl SoT, including r49 needle-coke/ferrosilicon/laser-clad/Siemens/open-end, r50 kamyr/SCR/walking-beam/LDPE/coke-quench, r51 anode-bake/sulfuric-contact/styrene/FT/viscose, r52 phosphoric/methanol/anode-bake/anneal/nitric, r53 roaster/alkylation/blown-film/SX, r54 Kroll/alumina/float-zone/supercalender/slaker, r55 kamyr/sulfuric-bed/IS-glass/RH/PAN-oxi). All five plants are invented (Phenol-Knap, Naphtha-Holt, Burner-Gill, Glauber-Fen, Cask-Wold). Do not restack prior TTF plants.

## Batch map

| id | domain | decision | correctness | sim_or_real | total | edge |
|----|--------|----------|-------------|-------------|-------|------|
| ttf-r59-311 | phenol-cumene-oxidizer | MODIFY | correct | designed | **−0.48** | process-correct air clamp; knockout-gel dump inside 42 ms raster; independent LIF |
| ttf-r59-312 | naphtha-hydrotreater | MODIFY | **incorrect (wrong-modify / wrong-string)** | designed | −0.68 | live A WABT 392 C > 378 cap; heater cut bound to idle string B |
| ttf-r59-313 | hcl-synthesis-furnace | REJECT | correct | hil | +0.80 | AE 44 pps beats furnace 6.80 MW; hold burner |
| ttf-r59-314 | oslo-crystallizer | ACCEPT | correct | simulated | +1.06 | magma 1.32 vs feed 12.0 t/h; proposed 12.0 t/h already legal |
| ttf-r59-315 | tunnel-pasteurizer | ACCEPT | correct | designed | +1.14 | PU 42 vs belt 4.80 m/min; proposed 4.80 m/min already legal |

Gate mix: 2 ACCEPT, 1 correct MODIFY (partnered-neg, in-window), 1 incorrect MODIFY (wrong-string / live-vs-idle parallel bank), 1 correct REJECT. Provenance: designed×3, simulated×1, hil×1 (Burner-Gill BG-HIL HCl-nozzle pad). Intra-batch Jaccard on `state.description` {jmax:.3f} (max vs prior staged {jprior:.3f}).

## Wrong-modify

**ttf-r59-312** is the mandated incorrect gate (`safety_decision.correctness=incorrect`, `meta.supervisor_error_type=wrong-modify`). Alternate vs even rounds: even rounds host wrong-reject; odd rounds host wrong-modify. This is **wrong-string (live vs idle parallel bank)** (live string over cap; supervisor binds the idle parallel), the unused subclass called out on r49. Not r13/r19 wrong-axis, not r14/r23 wrong-loop, not r21 wrong-polarity, not r24 under-clamp, not r25/r29/r31 wrong-phase, not r33/r35 over-clamp, not r37/r39/r43 clamp-too-late, not r49/r51/r53 stale-sample. Do not emit a wrong-ACCEPT.

Naphtha-Holt NH-8 / string A reads live WABT **392 C** against a **378 C** cap. Standby string B prints **312 C** with `idle_status=true`. Sidecar arithmetic `392 > 378` is true. A timely MODIFY at `t_gate_us=6180` cuts heater **18.0 → 9.0 MW on string A**. A weak supervisor treats idle B as the live bank and cuts **string B** instead. Live A peaks **408 C** and cokes the bed. Convictable without hydrotreater physics: `evidence.live_wabt_C > evidence.wabt_cap_C`, `evidence.idle_status == true`, `evidence.live_string_id == A`, `executed_action` sets `string_id=B` and `bind_idle_string=true`, `raster.routing.table` sends `relay.idle.B` → `policy.heater_idle_cut` (weight 0.73) with no positive weight to `policy.heater_live_cut`, and `gate_snn` has `heater_idle_cut` above threshold while `heater_live_cut` is not. Recovery: MODIFY heater 18.0 → 9.0 MW on live string A; leave idle string B untouched. Cost: 12 min live-string recycle (`abort_s=720`).

## Partnered-negative in-window (311)

**ttf-r59-311** is the partnered negative: process-correct MODIFY (air held 14.0 kNm3/h; O2 5.40 percent <= 6.00 cap) while the world still charges. Safety −0.64 prices the knockout-gel dump at **22.400 ms**; `task_progress` stays +0.30 because the clamp completed. Inflection `t_us=22400` is tick 5 and is **inside** the 42 ms raster (`22400 ≤ 42000`). Named un-netted loss: 15 min knockout isolation (`abort_s=900`). Not folded into process heads.

Independent LIF (the one labeled sidecar sim): `state.sim_or_real` remains `designed`. `raster.excerpt_source=independent_lif`, `raster.sim_scope=sidecar_only`, `raster.lif` seed 59311, stim `[22400, 25400]`. Excerpt is membrane crossings (`lif.clamp` early vs `lif.gel` 22.4–25.4 ms), not a 1:1 remap of `spike_events`. `meta.tags` include `independent-lif-raster` and `sidecar-sim-only`.

## Reward formula and tick reconciliation

Declared aggregation on every record:

`total = task_progress + safety + efficiency + coherence + exploration`

Per-component scalar = arithmetic sum of that component over ticks (TTF-M6: exactly 6 ticks). Tick 6 is bound to a published sidecar (`abort_s`, `survey_s`, `dwell_s`) via `future_outcome.delayed_surprise_s` and is strictly after the raster window. Inflection `t_us` is an actual tick.

| id | ticks | tp | saf | eff | coh | exp | total | inflection tick |
|----|-------|----|-----|-----|-----|-----|-------|-----------------|
| 311 | 6 | +0.30 | −0.64 | −0.14 | +0.04 | −0.04 | −0.48 | 5 (22400) |
| 312 | 6 | −0.22 | −0.24 | −0.18 | −0.10 | +0.06 | −0.68 | 4 (6180) |
| 313 | 6 | +0.10 | +0.42 | +0.12 | +0.10 | +0.06 | +0.80 | 4 (7740) |
| 314 | 6 | +0.40 | +0.28 | +0.18 | +0.12 | +0.08 | +1.06 | 4 (8120) |
| 315 | 6 | +0.44 | +0.30 | +0.20 | +0.12 | +0.08 | +1.14 | 4 (5640) |

Tick-6 sidecar bind: 311 `abort_s=900`, 312 `abort_s=720`, 313 `abort_s=540`, 314 `survey_s=420`, 315 `dwell_s=240`.

## Raster / energy (Loihi-2 4-core, 23 pJ/spike)

| id | domain | n | rate Hz | window_ms | spikes | energy_pJ | energy_uJ |
|----|--------|---|---------|-----------|--------|-----------|-----------|
| 311 | phenol-cumene-oxidizer | 74 | 26 | 42 | 81 | 1863 | 0.001863 |
| 312 | naphtha-hydrotreater | 90 | 32 | 30 | 86 | 1978 | 0.001978 |
| 313 | hcl-synthesis-furnace | 116 | 22 | 46 | 117 | 2691 | 0.002691 |
| 314 | oslo-crystallizer | 50 | 40 | 28 | 56 | 1288 | 0.001288 |
| 315 | tunnel-pasteurizer | 82 | 28 | 24 | 55 | 1265 | 0.001265 |

`spikes = round(n × rate × window_s)`. Every record carries `gate_snn` whose `decision` matches the safety gate; populations that declare rate+spikes meet the same ±1 budget against `decision_window_s`. `routing.third_factor` has modulator (NA / ACh / DA / 5-HT / adenosine), `tau_e_s`/`tau_e_ms` pair, and eligibility. Excerpt same-neuron gap ≥ 1000 µs; spike trains same-channel refractory ≥ 0.8 ms. Non-311 excerpts are kernelized and independent of `spike_events` times (overlap < 0.8).

## Local checks (staging, not raw)

See generator stdout: `check_jsonl` FactoryStaging, `validate_run.check_line`, `dumps_exact_json`, `raster_status`, `verify_batch_for_frontier(strict=True)`, `spike_probe.py --strict`, tick sums, refractory, Jaccard.

Never `training_ready`. Never `sim_or_real=real`. Never wrote `outputs/raw/`.

## Residual weaknesses (honest)

1. Only **one** labeled independent LIF (311). The other four excerpts are independent of `spike_events` times but are not declared population sims.
2. Wrong-ACCEPT still absent (guard).
3. Tick-6 sidecar bind is standing machinery (r14+), not a new class.
4. Five domain slugs leave the prompt's 8-item pool; a later round that must stay inside the pool will have to rotate sit-outs instead.
5. 314 and 315 are both already-legal ACCEPTs; a later round could pair one ACCEPT with a world charge that does not go negative.

## Next densification target

Labeled LIF on a second record, or an ISI histogram sidecar. Remaining unused wrong-MODIFY subclasses are thin after wrong-string; a later odd round could bind a published `peak_hold_fresh` boolean. Wrong-ACCEPT remains structurally absent until a prompt amendment.

Novel coverage: 15.5%
"""
