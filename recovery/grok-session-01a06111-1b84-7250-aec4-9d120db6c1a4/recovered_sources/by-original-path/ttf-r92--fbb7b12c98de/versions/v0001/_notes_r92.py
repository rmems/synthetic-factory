def notes_text(jmax: float) -> str:
    return f"""# Thalamic Trajectory Factory — NOTES-r92

- Factory: `thalamic-trajectory-factory`
- Run label: `2026-09-02-final-heavy`
- Generator: `grok-4.6`
- Channel: SuperGrok Heavy consumer chat (RM-793 research-only)
- Quota: 5
- Quality: Q=5
- IDs: `ttf-r92-476` … `ttf-r92-480`
- Domains this batch: `caprolactone-baeyer-villiger`, `polyether-polyol-alkoxylation`, `indium-phosphide-lpe`, `boron-nitride-hotpress`, `potassium-permanganate-oxidizer`

These five domain slugs sit outside the prompt 8-pool and outside staged r13–r91 occupancy (jsonl SoT plus incomplete gens r85–r91, including r84 nylon-66 / MTO-riser / acrylic-ox / Penex / KF2HF, r85 moly-roaster / chlorosilane / Ta-Na / PBT / V2O5, r86 DMC / ETBE, r87 CS2 / Lurgi / RKEF / Wacker / TiCl4-chlorinator, r88 pentaerythritol / V2O5-flaker / TiCl4-still / NPG / isoprene-MeCN, r89 GaAs-Cz / cyanuric / ZrCl4 / xanthan / In-cementation, r91 Zr-sand / In-EW / Nb-aluminotherm / CaCN2 / GaAs-LEC). All five plants are invented. Do not restack prior TTF plants. Caprol-Stang / Alkoxyl-Nab / Indphos-Lythe / Nitridex-Dike / Permang-Edge are this round only.

## Batch map

| id | domain | decision | correctness | sim_or_real | total | edge |
|----|--------|----------|-------------|-------------|-------|------|
| ttf-r92-476 | caprolactone-baeyer-villiger | MODIFY | correct | designed | **−0.44** | process-correct ketone clamp; packing gassing inside 46 ms raster; independent LIF |
| ttf-r92-477 | polyether-polyol-alkoxylation | REJECT | **incorrect (wrong-reject)** | designed | −0.58 | live Type-J 168.0 C < 210.0 trip; supervisor binds leftover Type-K table 221.0 C |
| ttf-r92-478 | indium-phosphide-lpe | REJECT | correct | hil | +0.80 | seed AE 52 pps beats melt IR 980 C; hold slider |
| ttf-r92-479 | boron-nitride-hotpress | ACCEPT | correct | simulated | +1.10 | die 1480 C vs pyro smear 1720 C; proposed 18.0 MPa already legal |
| ttf-r92-480 | potassium-permanganate-oxidizer | ACCEPT | correct | designed | +1.14 | liquor 72 C vs vapor smear 98 C; proposed 4.8 t/h already legal |

Gate mix: 2 ACCEPT, 1 correct MODIFY (partnered-neg, in-window), 1 correct REJECT, 1 incorrect REJECT (cold-junction-offset / thermocouple-type-swap). Provenance: designed×3, simulated×1, hil×1 (Indphos-Lythe IL-HIL LPE pad). Intra-batch Jaccard on `state.description` {jmax:.3f} (< 0.4).

## Wrong-reject

**ttf-r92-477** is the mandated incorrect gate (`safety_decision.correctness=incorrect`, `meta.supervisor_error_type=wrong-reject`). Alternate vs odd rounds: even rounds host wrong-reject (r12/r14/…/r84/r86/r88/r92); odd rounds host wrong-modify. Do not emit a wrong-ACCEPT. Error *class* is **cold-junction-offset / thermocouple-type-swap**, not r16 reticle-as-wafer, not r18 empty-tank, not r20 oscillation-as-PSV, not r22 class-transplant, not r30 stale-firmware floor, not r32 stale-peak-hold, not r34 wrong-bus, not r36 unit-mismatch leftover-bar, not r38 loop-test-inject, not r40 setpoint-echo, not r42 leftover-setpoint-as-trip, not r44 wrong-unit-shadow, not r46 kPa-as-MPa, not r50 raw-mA-as-EU, not r52 gauge-vs-absolute / stale-sample, not r58 overrange-flag-as-PV, not r60 absolute-as-gauge, not r62 sign-convention, not r64 reverse-scale / inverted-4-20, not r68/r74 channel-swap / sibling-loop-as-live, not r70 raw-DP-as-flow, not r72 namur-failsafe-as-EU, not r76/r78 NAMUR-fail-high-as-live, not r80 HART-SV-as-PV, not r82 stale-URV / swapped-range, not r84 stale-setpoint / swapped-range, not r86/r88 stale-handshake / heartbeat-as-PV.

Alkoxyl-Nab AN-6 / Alkox-K3 (LIVE) reads live Type-J kettle `168.0 C` (8.98 mV, CJC 24 C) against a published **210.0 C** trip. A leftover Type-K millivolt table still prints **221.0 C** from the same 8.98 mV; a leftover **72 C** hot-box CJC remains on the faceplate (`type_swap=true`, `leftover_cjc=true`). Sidecar arithmetic `168.0 < 210.0` is true. A weak supervisor binds the leftover Type-K table, REJECT-holds propylene-oxide 9.6 → 0.0 t/h, and leaves a legal alkoxylation idle. Convictable without polyol physics: `evidence.live_C < evidence.trip_C`, `evidence.live_mV == 8.98`, `evidence.tc_type_live == J`, `evidence.shadow_C == 221.0`, `executed_action` sets `po_tph=0` / `hold=true`, `raster.routing.table` sends `relay.tc.stale` → `policy.hold_reject` (weight 0.75) with no positive weight to `policy.go_accept`, and `gate_snn` has `hold_reject` above threshold while `go_accept` is not (`spikes=0`). Recovery: ACCEPT; leave 9.6 t/h; bind published live Type-J with CJC 24 C. Cost: 19 min missed OH-number window (`missed_window_s=1140`).

## Partnered-negative in-window (476)

**ttf-r92-476** is the partnered negative: process-correct MODIFY (cyclohexanone held 7.1 t/h; bed 149 C < 155 cap) while the world still charges. Safety −0.60 prices the 16 mm packing gassing at **22.400 ms**; `task_progress` stays +0.32 because the clamp completed. Inflection `t_us=22400` is tick 5 and is **inside** the 46 ms raster (`22400 ≤ 46000`). Named un-netted loss: 15 min bed isolate (`abort_s=900`). Not folded into process heads.

Independent LIF (the one labeled sidecar sim): `state.sim_or_real` remains `designed`. `raster.excerpt_source=independent_lif`, `raster.sim_scope=sidecar_only`, `raster.lif` seed 92476, stim `[21200, 25000]`. Excerpt is membrane crossings (`lif.clamp` early vs `lif.gassing` 21.2–25.0 ms), not a 1:1 remap of `spike_events`. `meta.tags` include `independent-lif-raster` and `sidecar-sim-only`.

## Reward formula and tick reconciliation

Declared aggregation on every record:

`total = task_progress + safety + efficiency + coherence + exploration`

Per-component scalar = arithmetic sum of that component over ticks (TTF-M6: exactly 6 ticks). Tick 6 is bound to a published sidecar (`abort_s`, `missed_window_s`, `survey_hold_s`, `dwell_s`) via `future_outcome.delayed_surprise_s` and is strictly after the raster window. Inflection `t_us` is an actual tick.

| id | ticks | tp | saf | eff | coh | exp | total | inflection tick |
|----|-------|----|-----|-----|-----|-----|-------|-----------------|
| 476 | 6 | +0.32 | −0.60 | −0.16 | +0.04 | −0.04 | −0.44 | 5 (22400) |
| 477 | 6 | −0.20 | −0.12 | −0.22 | −0.10 | +0.06 | −0.58 | 4 (5240) |
| 478 | 6 | +0.10 | +0.42 | +0.12 | +0.10 | +0.06 | +0.80 | 4 (6340) |
| 479 | 6 | +0.42 | +0.30 | +0.18 | +0.12 | +0.08 | +1.10 | 4 (4680) |
| 480 | 6 | +0.44 | +0.32 | +0.18 | +0.12 | +0.08 | +1.14 | 4 (5640) |

Tick-6 sidecar bind: 476 `abort_s=900`, 477 `missed_window_s=1140`, 478 `abort_s=480`, 479 `survey_hold_s=360`, 480 `dwell_s=420`.

## Raster / energy (Loihi-2 4-core, 23 pJ/spike)

| id | domain | n | rate Hz | window_ms | spikes | energy_pJ | energy_uJ |
|----|--------|---|---------|-----------|--------|-----------|-----------|
| 476 | caprolactone-baeyer-villiger | 78 | 25 | 46 | 90 | 2070 | 0.002070 |
| 477 | polyether-polyol-alkoxylation | 90 | 30 | 30 | 81 | 1863 | 0.001863 |
| 478 | indium-phosphide-lpe | 110 | 21 | 38 | 88 | 2024 | 0.002024 |
| 479 | boron-nitride-hotpress | 60 | 38 | 24 | 55 | 1265 | 0.001265 |
| 480 | potassium-permanganate-oxidizer | 52 | 42 | 22 | 48 | 1104 | 0.001104 |

`spikes = round(n × rate × window_s)`. Every record carries `gate_snn` whose `decision` matches the safety gate; populations that declare rate+spikes meet the same ±1 budget against `decision_window_s`. `routing.third_factor` has modulator (NA / ACh / DA / 5-HT / adenosine), `tau_e_s`/`tau_e_ms` pair, and eligibility. Excerpt same-neuron gap ≥ 1000 µs; spike trains same-channel refractory ≥ 0.8 ms. Non-476 excerpts are kernelized and independent of `spike_events` times (overlap < 0.8).

## Local checks (staging, not raw)

See generator stdout: `check_jsonl` FactoryStaging, `validate_run.check_line`, `dumps_exact_json`, `raster_status`, `verify_batch_for_frontier(strict=True)`, `spike_probe.py --strict`, tick sums, refractory, Jaccard.

Never `training_ready`. Never `sim_or_real=real`. Never wrote `outputs/raw/`.

## Residual weaknesses (honest)

1. Only **one** labeled independent LIF (476). The other four excerpts are independent of `spike_events` times but are not declared population sims.
2. Wrong-ACCEPT still absent (guard).
3. Tick-6 sidecar bind is standing machinery (r14+), not a new class.
4. Five domain slugs leave the prompt's 8-item pool; a later round that must stay inside the pool will have to rotate sit-outs instead.
5. 477 wrong-reject is sidecar-convictable (routing `to` / shadow_C / type_swap / leftover_cjc) as a **new** error class (cold-junction-offset / thermocouple-type-swap) vs r80 HART-SV, r82 stale-URV, r84 stale-setpoint, r86/r88 handshake-as-PV.
6. 479 and 480 are both already-legal ACCEPTs; a later round could pair an ACCEPT with a world charge that does not go negative.

## Next densification target

Labeled LIF on a second record, or an ISI histogram sidecar. Remaining unused wrong-REJECT subclasses include **simulation-tag-as-live / MODE_SIMULATE-as-PV**. Wrong-ACCEPT remains structurally absent until a prompt amendment.

{NOVEL_COVERAGE_LINE}
"""
