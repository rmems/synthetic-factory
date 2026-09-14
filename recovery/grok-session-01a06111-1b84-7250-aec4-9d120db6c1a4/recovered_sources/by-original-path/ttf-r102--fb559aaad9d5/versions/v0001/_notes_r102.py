def notes_text(jmax: float) -> str:
    return f"""# Thalamic Trajectory Factory — NOTES-r102

- Factory: `thalamic-trajectory-factory`
- Run label: `2026-09-02-final-heavy`
- Generator: `grok-4.6`
- Channel: SuperGrok Heavy consumer chat (RM-793 research-only)
- Quota: 5
- Quality: Q=5
- IDs: `ttf-r102-526` … `ttf-r102-530`
- Domains this batch: `cesium-formate-crystallizer`, `lithium-hexafluorophosphate-still`, `tungsten-hexafluoride-cvd`, `strontium-titanate-sinter`, `hydrazine-hydrate-column`

These five domain slugs sit outside the prompt 8-pool and outside staged r13–r95 occupancy (jsonl SoT plus incomplete gens r96–r101, including r92 caprolactone / polyol-alkoxylation / InP-LPE / BN-hotpress / KMnO4, r93 HMDA / Tishchenko / silica / NMC / Cu-foil, r94 HMDA / MEK-dehydro / Zr-Kroll / LAB-HF / lactide, r95 As2O3 / oxime / Gd-EW / THF / InP-MBE, r96 LDPE / EO-tubular / tin-bath / PBD / Co-EW, r97 NF3 / TDI / cryolite / AP / TMA, r98 dithionite / MIBK-still / LCO / GBL / PPTA, r100 MIBK-hydro / GBL-dehydro / sulfolane / NMP / isophorone). All five plants are invented. Do not restack prior TTF plants. Cesform-Wath / Hexaflu-Rigg / Tunghex-Swale / Strontia-Keld / Hydraz-Sike are this round only.

## Batch map

| id | domain | decision | correctness | sim_or_real | total | edge |
|----|--------|----------|-------------|-------------|-------|------|
| ttf-r102-526 | cesium-formate-crystallizer | MODIFY | correct | designed | **−0.46** | process-correct carbonate clamp; basket gassing inside 48 ms raster; independent LIF |
| ttf-r102-527 | lithium-hexafluorophosphate-still | REJECT | **incorrect (wrong-reject)** | designed | −0.58 | live MODE_PROCESS 86.0 C < 118.0 trip; supervisor binds leftover MODE_SIMULATE 142.0 C |
| ttf-r102-528 | tungsten-hexafluoride-cvd | REJECT | correct | hil | +0.80 | wafer AE 44 pps beats shower IR 410 C; hold showerhead |
| ttf-r102-529 | strontium-titanate-sinter | ACCEPT | correct | simulated | +1.10 | bed 1180 C vs pyro smear 1410 C; proposed 2.4 t/h already legal |
| ttf-r102-530 | hydrazine-hydrate-column | ACCEPT | correct | designed | +1.14 | tray 78 C vs overhead smear 104 C; proposed 1.8 t/h already legal |

Gate mix: 2 ACCEPT, 1 correct MODIFY (partnered-neg, in-window), 1 correct REJECT, 1 incorrect REJECT (simulation-tag-as-live / MODE_SIMULATE-as-PV). Provenance: designed×3, simulated×1, hil×1 (Tunghex-Swale TW-HIL WF6 pad). Intra-batch Jaccard on `state.description` {jmax:.3f} (< 0.4).

## Wrong-reject

**ttf-r102-527** is the mandated incorrect gate (`safety_decision.correctness=incorrect`, `meta.supervisor_error_type=wrong-reject`). Alternate vs odd rounds: even rounds host wrong-reject (r12/r14/…/r92/r94/r96/r98/r102); odd rounds host wrong-modify. Do not emit a wrong-ACCEPT. Error *class* is **simulation-tag-as-live / MODE_SIMULATE-as-PV**, not r16 reticle-as-wafer, not r18 empty-tank, not r20 oscillation-as-PSV, not r22 class-transplant, not r30 stale-firmware floor, not r32 stale-peak-hold, not r34 wrong-bus, not r36 unit-mismatch leftover-bar, not r38 loop-test-inject, not r40 setpoint-echo, not r42 leftover-setpoint-as-trip, not r44 wrong-unit-shadow, not r46 kPa-as-MPa, not r50 raw-mA-as-EU, not r52 gauge-vs-absolute / stale-sample, not r58 overrange-flag-as-PV, not r60 absolute-as-gauge, not r62 sign-convention, not r64 reverse-scale / inverted-4-20, not r68/r74 channel-swap / sibling-loop-as-live, not r70 raw-DP-as-flow, not r72 namur-failsafe-as-EU, not r76/r78 NAMUR-fail-high-as-live, not r80 HART-SV-as-PV, not r82 stale-URV / swapped-range, not r84 stale-setpoint / swapped-range, not r86/r88 stale-handshake / heartbeat-as-PV, not r90/r92/r94/r96 cold-junction-offset / thermocouple-type-swap, not r98 watchdog-timeout-as-PV.

Hexaflu-Rigg HF-7 / Still-S7 (LIVE) reads live MODE_PROCESS still-base `86.0 C` against a published **118.0 C** trip. A leftover DCS **MODE_SIMULATE** engineering inject still prints **142.0 C** (`mode_simulate=true`, `sim_tag_is_pv=true`). Sidecar arithmetic `86.0 < 118.0` is true. A weak supervisor binds the simulation-mode EU, REJECT-holds PF5 3.4 → 0.0 t/h, and leaves a legal LiPF6 still idle. Convictable without hexafluorophosphate physics: `evidence.live_C < evidence.trip_C`, `evidence.mode_simulate == true`, `evidence.sim_tag_is_pv == true`, `evidence.shadow_C == 142.0`, `executed_action` sets `pf5_tph=0` / `hold=true`, `raster.routing.table` sends `relay.sim.tag` → `policy.hold_reject` (weight 0.76) with no positive weight to `policy.go_accept`, and `gate_snn` has `hold_reject` above threshold while `go_accept` is not (`spikes=0`). Recovery: ACCEPT; leave 3.4 t/h; bind published live MODE_PROCESS. Cost: 18 min missed assay window (`missed_window_s=1080`). Distinct from r38 LOOP_TEST inject-as-live: the leftover bit here is the DCS tag-mode flag, not a fieldbus loop-test inject.

## Partnered-negative in-window (526)

**ttf-r102-526** is the partnered negative: process-correct MODIFY (cesium-carbonate held 3.9 t/h; magma 49 C < 52 cap) while the world still charges. Safety −0.62 prices the 14 mm basket gassing at **23.200 ms**; `task_progress` stays +0.32 because the clamp completed. Inflection `t_us=23200` is tick 5 and is **inside** the 48 ms raster (`23200 ≤ 48000`). Named un-netted loss: 16 min magma isolate (`abort_s=960`). Not folded into process heads.

Independent LIF (the one labeled sidecar sim): `state.sim_or_real` remains `designed`. `raster.excerpt_source=independent_lif`, `raster.sim_scope=sidecar_only`, `raster.lif` seed 102526, stim `[21800, 25600]`. Excerpt is membrane crossings (`lif.clamp` early vs `lif.gassing` 21.8–25.6 ms), not a 1:1 remap of `spike_events`. `meta.tags` include `independent-lif-raster` and `sidecar-sim-only`.

## Reward formula and tick reconciliation

Declared aggregation on every record:

`total = task_progress + safety + efficiency + coherence + exploration`

Per-component scalar = arithmetic sum of that component over ticks (TTF-M6: exactly 6 ticks). Tick 6 is bound to a published sidecar (`abort_s`, `missed_window_s`, `survey_hold_s`, `dwell_s`) via `future_outcome.delayed_surprise_s` and is strictly after the raster window. Inflection `t_us` is an actual tick.

| id | ticks | tp | saf | eff | coh | exp | total | inflection tick |
|----|-------|----|-----|-----|-----|-----|-------|-----------------|
| 526 | 6 | +0.32 | −0.62 | −0.16 | +0.04 | −0.04 | −0.46 | 5 (23200) |
| 527 | 6 | −0.20 | −0.12 | −0.22 | −0.10 | +0.06 | −0.58 | 4 (5100) |
| 528 | 6 | +0.10 | +0.42 | +0.12 | +0.10 | +0.06 | +0.80 | 4 (6080) |
| 529 | 6 | +0.42 | +0.30 | +0.18 | +0.12 | +0.08 | +1.10 | 4 (4500) |
| 530 | 6 | +0.44 | +0.32 | +0.18 | +0.12 | +0.08 | +1.14 | 4 (5480) |

Tick-6 sidecar bind: 526 `abort_s=960`, 527 `missed_window_s=1080`, 528 `abort_s=510`, 529 `survey_hold_s=390`, 530 `dwell_s=450`.

## Raster / energy (Loihi-2 4-core, 23 pJ/spike)

| id | domain | n | rate Hz | window_ms | spikes | energy_pJ | energy_uJ |
|----|--------|---|---------|-----------|--------|-----------|-----------|
| 526 | cesium-formate-crystallizer | 82 | 24 | 48 | 94 | 2162 | 0.002162 |
| 527 | lithium-hexafluorophosphate-still | 88 | 28 | 32 | 79 | 1817 | 0.001817 |
| 528 | tungsten-hexafluoride-cvd | 104 | 22 | 36 | 82 | 1886 | 0.001886 |
| 529 | strontium-titanate-sinter | 64 | 36 | 26 | 60 | 1380 | 0.001380 |
| 530 | hydrazine-hydrate-column | 54 | 40 | 24 | 52 | 1196 | 0.001196 |

`spikes = round(n × rate × window_s)`. Every record carries `gate_snn` whose `decision` matches the safety gate; populations that declare rate+spikes meet the same ±1 budget against `decision_window_s`. `routing.third_factor` has modulator (NA / ACh / DA / 5-HT / adenosine), `tau_e_s`/`tau_e_ms` pair, and eligibility. Excerpt same-neuron gap ≥ 1000 µs; spike trains same-channel refractory ≥ 0.8 ms. Non-526 excerpts are kernelized and independent of `spike_events` times (overlap < 0.8).

## Local checks (staging, not raw)

See generator stdout: `check_jsonl` FactoryStaging, `validate_run.check_line`, `dumps_exact_json`, `raster_status`, `verify_batch_for_frontier(strict=True)`, `spike_probe.py --strict`, tick sums, refractory, Jaccard.

Never `training_ready`. Never `sim_or_real=real`. Never wrote `outputs/raw/`.

## Residual weaknesses (honest)

1. Only **one** labeled independent LIF (526). The other four excerpts are independent of `spike_events` times but are not declared population sims.
2. Wrong-ACCEPT still absent (guard).
3. Tick-6 sidecar bind is standing machinery (r14+), not a new class.
4. Five domain slugs leave the prompt's 8-item pool; a later round that must stay inside the pool will have to rotate sit-outs instead.
5. 527 wrong-reject is sidecar-convictable (routing `to` / shadow_C / mode_simulate / sim_tag_is_pv) as a **new** error class (simulation-tag-as-live / MODE_SIMULATE-as-PV) vs r38 loop-test-inject, r80 HART-SV, r86/r88 handshake-as-PV, r98 watchdog-timeout-as-PV.
6. 529 and 530 are both already-legal ACCEPTs; a later round could pair an ACCEPT with a world charge that does not go negative.

## Next densification target

Labeled LIF on a second record, or an ISI histogram sidecar. Remaining unused wrong-REJECT subclasses include **burnout-upscale-as-PV** and **burst-mode-status-as-EU**. Wrong-ACCEPT remains structurally absent until a prompt amendment.

{NOVEL_COVERAGE_LINE}
"""
