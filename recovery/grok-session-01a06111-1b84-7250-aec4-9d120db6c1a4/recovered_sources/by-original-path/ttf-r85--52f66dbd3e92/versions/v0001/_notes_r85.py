def notes_text(jmax: float, jprior: float) -> str:
    return f"""# Thalamic Trajectory Factory — NOTES-r85

- Factory: `thalamic-trajectory-factory`
- Run label: `2026-09-02-final-heavy`
- Generator: `grok-4.6`
- Channel: SuperGrok Heavy consumer chat (RM-793 research-only)
- Quota: 5
- Quality: Q=5
- IDs: `ttf-r85-441` … `ttf-r85-445`
- Domains this batch: `molybdenum-concentrate-roaster`, `chlorosilane-disproportionation`, `tantalum-sodium-reducer`, `pbt-esterification-kettle`, `v2o5-flake-furnace`

These five domain slugs sit outside the prompt 8-pool and outside staged r13–r80 occupancy (jsonl SoT) plus in-flight gens r73–r84 (`ammonia-oxidation-burner` / `grignard-kettle`, r75 Acheson/ethylbenzene/ISF/LFP/ketazine, r76 adiponitrile-EHD/MTBE/Si3N4/epichlorohydrin/furfural, r77 steam-carbon/Catofin/MDI/adipic-KA/Si-metal, r78 Cativa/oxo/lyocell/BOF/RH, r79 Ge-zone/Te-EW/Hf-column/lysine/Se-roaster, r80 acetic-carbonylation/AN-prill/Si-furnace/acrylic/LiOH, r81 fumed-silica/bromine-blowout/POX/urea-pool/Corex, r82 MTO-SAPO/HDPE-slurry/sapphire/neoprene/LNG-MR, r83 styrene-dehydro/Ni-EW/ketene/PVC/DME, r84 nylon-66/MTO-riser/acrylic-ox/Penex/fluorine-cell). Distinct from r60 `tio2-chloride-oxidizer`, r68 `ethylbenzene-alkylation`, r71 `silane-cvd-epitaxy`, r73 `cyclohexane-air-oxidizer` / `bisphenol-A-reactor`, r79 `selector-wrong-leg`. All five plants are invented (Powellite-Strath, Chlorosil-Ingle, Tantalate-Lode, Butylene-Moor, Vanadate-Stow). Do not restack prior TTF plants (Marrow-Dock, Vesper-Lattice, Brine-Well, Saddle-Arc, Ashlar-Gait, Ostwald-Sike, Magnesyl-Beck, Arc-Staith, Hexene-Sike, Nasicon-Holt, Steamchar-Riggs, Catofin-Veld, Bardeen-Clart, Catholyte-Ingle, Cativa-Pightle).

## Batch map

| id | domain | decision | correctness | sim_or_real | total | edge |
|----|--------|----------|-------------|-------------|-------|------|
| ttf-r85-441 | molybdenum-concentrate-roaster | MODIFY | correct | designed | **−0.44** | process-correct air-flow clamp; hearth-arch crack inside 42 ms raster; independent LIF |
| ttf-r85-442 | chlorosilane-disproportionation | MODIFY | **incorrect (wrong-modify / wrong-bank polarity invert)** | designed | −0.68 | live TCS 8.4 mol% > 6.0 cap; 9.6 t/h steam OPEN on idle reverse-acting D-5 |
| ttf-r85-443 | tantalum-sodium-reducer | REJECT | correct | hil | +0.80 | AE 48 pps beats arc 38 kA; hold slip |
| ttf-r85-444 | pbt-esterification-kettle | ACCEPT | correct | simulated | +1.06 | inventory 12.4 m vs skin 78 C; proposed 18.0 t/h already legal |
| ttf-r85-445 | v2o5-flake-furnace | ACCEPT | correct | designed | +1.14 | bath 590 C vs cell 6.8 V; proposed 18.0 kA already legal |

Gate mix: 2 ACCEPT, 1 correct MODIFY (partnered-neg, in-window), 1 incorrect MODIFY (wrong-bank polarity invert), 1 correct REJECT. Provenance: designed×3, simulated×1, hil×1 (Tantalate-Lode TL-HIL sodium-reducer stand). Intra-batch Jaccard on `state.description` {jmax:.3f} (max vs prior staged {jprior:.3f}).

## Wrong-modify

**ttf-r85-442** is the mandated incorrect gate (`safety_decision.correctness=incorrect`, `meta.supervisor_error_type=wrong-modify`). Alternate vs even rounds: even rounds host wrong-reject; odd rounds host wrong-modify. This is **wrong-bank polarity invert** (live TCS over cap on D-4; spare D-5 is IDLE and reverse-acting; a 'cut' on that stem opens steam on the idle bank while live D-4 stays 12.0 t/h). Not r13/r19 wrong-axis, not r14/r23 wrong-loop, not r21 wrong-polarity (same-loop sign flip), not r24 under-clamp, not r25/r29/r31/r63 wrong-phase, not r33/r35 over-clamp, not r39 extra-PLC-scan clamp-too-late, not r53/r55/r57 stale-sample / lagged-tag, not r59/r65/r67 wrong-string / idle-bank (correct-direction cut on idle), not r69 split-range-wrong-half, not r71/r73/r75/r77 wrong-unit / lagged-bus, not r79 selector-wrong-leg. Do not emit a wrong-ACCEPT.

Chlorosil-Ingle CI-4 / Column D-4 (LIVE) reads live bottoms TCS **8.4 mol percent** against a **6.0** cap. Idle sibling D-5 prints **2.1 mol percent** with `idle_valve_action=reverse`. Sidecar arithmetic `8.4 > 6.0` is true and `2.1 < 6.0` is true. A timely MODIFY at `t_gate_us=6120` cuts live steam **12.0 → 6.4 t/h on D-4**. A weak supervisor binds the leftover reverse-acting stem and MODIFY-opens idle steam **2.0 → 9.6 t/h**. Live TCS stays **8.4 > 6.0**. Convictable without TCS physics: `evidence.live_tcs_molpct > evidence.cap_tcs_molpct`, `evidence.idle_tcs_molpct < evidence.cap_tcs_molpct`, `evidence.idle_status == IDLE`, `evidence.idle_valve_action == "reverse"`, `executed_action` sets `bind_idle_bank=true` and `polarity_invert=true` and `idle_steam_tph=9.6` with `live_steam_tph=12.0`, `raster.routing.table` sends `relay.gc.idle` → `policy.idle_invert` (weight 0.74) with no positive weight to `policy.live_cut`, and `gate_snn` has `idle_invert` above threshold while `live_cut` is not. Recovery: MODIFY live steam 12.0 → 6.4 t/h on D-4 at t_gate; leave D-5 parked at 2.0 t/h; leave SiHCl3 at 9.2 t/h. Cost: 12 min column dump (`abort_s=720`).

## Partnered-negative in-window (441)

**ttf-r85-441** is the partnered negative: process-correct MODIFY (air held 11.0 t/h; off-gas O2 5.4 vol percent <= 6.0 cap) while the world still charges. Safety −0.60 prices the hearth-arch crack at **22.400 ms**; `task_progress` stays +0.32 because the clamp completed. Inflection `t_us=22400` is tick 5 and is **inside** the 42 ms raster (`22400 ≤ 42000`). Named un-netted loss: 15 min drop-out isolate (`abort_s=900`). Not folded into process heads.

Independent LIF (the one labeled sidecar sim): `state.sim_or_real` remains `designed`. `raster.excerpt_source=independent_lif`, `raster.sim_scope=sidecar_only`, `raster.lif` seed 85441, stim `[22000, 25000]`. Excerpt is membrane crossings (`lif.clamp` early vs `lif.leak` 22–25 ms), not a 1:1 remap of `spike_events`. `meta.tags` include `independent-lif-raster` and `sidecar-sim-only`.

## Reward formula and tick reconciliation

Declared aggregation on every record:

`total = task_progress + safety + efficiency + coherence + exploration`

Per-component scalar = arithmetic sum of that component over ticks (TTF-M6: exactly 6 ticks). Tick 6 is bound to a published sidecar (`abort_s`, `survey_s`, `dwell_s`) via `future_outcome.delayed_surprise_s` and is strictly after the raster window. Inflection `t_us` is an actual tick.

| id | ticks | tp | saf | eff | coh | exp | total | inflection tick |
|----|-------|----|-----|-----|-----|-----|-------|-----------------|
| 441 | 6 | +0.32 | −0.60 | −0.16 | +0.04 | −0.04 | −0.44 | 5 (22400) |
| 442 | 6 | −0.22 | −0.24 | −0.18 | −0.10 | +0.06 | −0.68 | 4 (6120) |
| 443 | 6 | +0.10 | +0.42 | +0.12 | +0.10 | +0.06 | +0.80 | 4 (7640) |
| 444 | 6 | +0.40 | +0.28 | +0.18 | +0.12 | +0.08 | +1.06 | 4 (7840) |
| 445 | 6 | +0.44 | +0.30 | +0.20 | +0.12 | +0.08 | +1.14 | 4 (5640) |

Tick-6 sidecar bind: 441 `abort_s=900`, 442 `abort_s=720`, 443 `abort_s=480`, 444 `survey_s=360`, 445 `dwell_s=240`.

## Raster / energy (Loihi-2 4-core, 23 pJ/spike)

| id | domain | n | rate Hz | window_ms | spikes | energy_pJ | energy_uJ |
|----|--------|---|---------|-----------|--------|-----------|-----------|
| 441 | molybdenum-concentrate-roaster | 76 | 26 | 42 | 83 | 1909 | 0.001909 |
| 442 | chlorosilane-disproportionation | 88 | 34 | 28 | 84 | 1932 | 0.001932 |
| 443 | tantalum-sodium-reducer | 120 | 20 | 46 | 110 | 2530 | 0.002530 |
| 444 | pbt-esterification-kettle | 48 | 42 | 28 | 56 | 1288 | 0.001288 |
| 445 | v2o5-flake-furnace | 80 | 28 | 24 | 54 | 1242 | 0.001242 |

`spikes = round(n × rate × window_s)`. Every record carries `gate_snn` whose `decision` matches the safety gate; populations that declare rate+spikes meet the same ±1 budget against `decision_window_s`. `routing.third_factor` has modulator (NA / ACh / DA / 5-HT / adenosine), `tau_e_s`/`tau_e_ms` pair, and eligibility. Excerpt same-neuron gap ≥ 1000 µs; spike trains same-channel refractory ≥ 0.8 ms. Non-441 excerpts are kernelized and independent of `spike_events` times (overlap < 0.8).

## Local checks (staging, not raw)

See generator stdout: `check_jsonl` FactoryStaging, `validate_run.check_line`, `dumps_exact_json`, `raster_status`, `verify_batch_for_frontier(strict=True)`, `spike_probe.py --strict`, tick sums, refractory, Jaccard.

Never `training_ready`. Never `sim_or_real=real`. Never wrote `outputs/raw/`.

## Residual weaknesses (honest)

1. Only **one** labeled independent LIF (441). The other four excerpts are independent of `spike_events` times but are not declared population sims.
2. Wrong-ACCEPT still absent (guard).
3. Tick-6 sidecar bind is standing machinery (r14+), not a new class.
4. Five domain slugs leave the prompt's 8-item pool; a later round that must stay inside the pool will have to rotate sit-outs instead.
5. 444 and 445 are both already-legal ACCEPTs; a later round could pair one ACCEPT with a world charge that does not go negative.

## Next densification target

Labeled LIF on a second record, or an ISI histogram sidecar. Remaining unused wrong-MODIFY subclasses include **shadow-setpoint on a fresh tag** once polarity-invert is staged. Wrong-ACCEPT remains structurally absent until a prompt amendment.

Novel coverage: 16.0%
"""
