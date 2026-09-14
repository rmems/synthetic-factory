def notes_text(jmax: float, jprior: float) -> str:
    return f"""# Thalamic Trajectory Factory — NOTES-r117

- Factory: `thalamic-trajectory-factory`
- Run label: `2026-09-02-final-heavy`
- Generator: `grok-4.6`
- Channel: SuperGrok Heavy consumer chat (RM-793 research-only)
- Quota: 5
- Quality: Q=5
- IDs: `ttf-r117-601` … `ttf-r117-605`
- Domains this batch: `chromyl-chloride-still`, `iron-pentacarbonyl-cracker`, `niobium-pentachloride-sublimer`, `lithium-niobate-czochralski`, `zinc-selenide-cvd`

These five domain slugs sit outside the prompt 8-pool and outside staged r13–r115 occupancy (jsonl SoT) plus in-flight gens r109 / r114 / r116 / r118 / r119 (`methanol-to-olefins-reactor` / `sulfuryl-chloride-reactor` / `lanthanum-hexaboride-sinter` / `polytetrahydrofuran-polymerizer` / `vanadium-oxytrichloride-still`, r114 TBHP-oxidizer / ADN-EHD / Pidgeon / BPA / epichlorohydrin). Distinct from r107 VDF-autoclave / allyl-chloride / AlN-sinter / NCA / BCl3, r111 PA-oxidizer / TBHP-column / LaF3 / 2-EH / SF6, r113 P4S10 / BF3-etherate / GaCl3 / DEZ / Ho2O3, r115 I2-prill / BrF3 / Ir-crucible / EPDM / BPS. All five plants are invented (Chromyl-Fellwick, Pentacarb-Howbeck, Niobpent-Grainth, Linio-Smeath, Zincsel-Whinfall). Do not restack prior TTF plants.

## Batch map

| id | domain | decision | correctness | sim_or_real | total | edge |
|----|--------|----------|-------------|-------------|-------|------|
| ttf-r117-601 | chromyl-chloride-still | MODIFY | correct | designed | **−0.44** | process-correct chromyl-feed clamp; packing-tube leak inside 42 ms raster; independent LIF |
| ttf-r117-602 | iron-pentacarbonyl-cracker | MODIFY | **incorrect (wrong-modify / cascade-secondary-as-primary)** | designed | −0.68 | live CO 186 ppm > 40 cap; 2.1 t/h jacket cut on the cascade-secondary FT |
| ttf-r117-603 | niobium-pentachloride-sublimer | REJECT | correct | hil | +0.80 | AE 52 pps beats coil 41 kA; hold NbCl5 cake |
| ttf-r117-604 | lithium-niobate-czochralski | ACCEPT | correct | simulated | +1.06 | melt 11.2 mm vs afterheater 71 C; proposed 5.8 mm/h already legal |
| ttf-r117-605 | zinc-selenide-cvd | ACCEPT | correct | designed | +1.14 | susceptor 126 C vs H2Se 1.80 slm; proposed 3.6 um/h already legal |

Gate mix: 2 ACCEPT, 1 correct MODIFY (partnered-neg, in-window), 1 incorrect MODIFY (cascade-secondary-as-primary), 1 correct REJECT. Provenance: designed×3, simulated×1, hil×1 (Niobpent-Grainth NG-HIL NbCl5 sublimer stand). Intra-batch Jaccard on `state.description` {jmax:.3f} (max vs prior staged {jprior:.3f}).

## Wrong-modify

**ttf-r117-602** is the mandated incorrect gate (`safety_decision.correctness=incorrect`, `meta.supervisor_error_type=wrong-modify`). Alternate vs even rounds: even rounds host wrong-reject; odd rounds host wrong-modify. This is **cascade-secondary-as-primary** (live CO IR over cap on C-9; CO IR is the cascade primary PV; jacket-oil FT is a published cascade secondary with `secondary_is_primary=false`; supervisor cuts jacket while Fe(CO)5 stays 8.4 t/h). Not r13/r19 wrong-axis, not r14/r23 wrong-loop, not r21 wrong-polarity, not r24 under-clamp, not r25/r29/r31/r63 wrong-phase, not r33/r35 over-clamp, not r39 extra-PLC-scan clamp-too-late, not r53/r55/r57 stale-sample / lagged-tag, not r59/r65/r67 wrong-string / idle-bank, not r69 split-range-wrong-half, not r71/r73/r75/r77 wrong-unit / lagged-bus, not r79/r81 selector-wrong-leg, not r83 wrong-bank polarity invert, not r85 ratio-pair invert, not r87 wrong-deadband polarity, not r89 dual-range-wrong-band, not r91 wrong-polarity-fresh-tag, not r93 valve-travel as PV, not r95/r97 lead-lag invert, not r99/r107 feedforward-as-feedback (those bind a published *feedforward disturbance* as feedback; jacket here is the inner-loop slave of the same cascade, not a feedforward FT), not r103/r105 shadow-setpoint leftover faceplate, not r111/r113 percent-open vs percent-closed, not r115 wrong-hysteresis on a split-range valve. Do not emit a wrong-ACCEPT.

Pentacarb-Howbeck PH-7 / Cracker C-9 reads live CO **186 ppm** against a **40** ppm cap. Fe(CO)5 **8.4 t/h** (cascade primary IR) and jacket oil **6.0 t/h** (cascade secondary FT, `secondary_is_primary=false`) are both LIVE. Sidecar arithmetic `186 > 40` is true. A timely MODIFY at `t_gate_us=6120` cuts Fe(CO)5 **8.4 → 5.2 t/h**. A weak supervisor binds the cascade secondary as primary and MODIFY-cuts jacket **6.0 → 2.1 t/h** while Fe(CO)5 stays 8.4. Live CO stays **186 > 40**. Convictable without pentacarbonyl physics: `evidence.live_co_ppm > evidence.cap_co_ppm`, `evidence.secondary_is_primary == false`, `evidence.primary_status == LIVE`, `evidence.secondary_status == LIVE`, `executed_action` sets `bind_secondary_as_primary=true` and `secondary_is_primary=true` and `jacket_tph=2.1` with `fe_tph=8.4`, `raster.routing.table` sends `relay.ft.jacket` → `policy.sec_cut` (weight 0.74) with no positive weight to `policy.pri_cut`, and `gate_snn` has `sec_cut` above threshold while `pri_cut` is not. Recovery: MODIFY live Fe(CO)5 8.4 → 5.2 t/h on C-9 at t_gate; leave jacket at 6.0 t/h. Cost: 12 min carbonyl dump (`abort_s=720`).

## Partnered-negative in-window (601)

**ttf-r117-601** is the partnered negative: process-correct MODIFY (chromyl held 9.8 t/h; CrO2Cl2 vapor 6.4 g/Nm3 <= 8.0 cap) while the world still charges. Safety −0.60 prices the packing-tube leak at **22.400 ms**; `task_progress` stays +0.32 because the clamp completed. Inflection `t_us=22400` is tick 5 and is **inside** the 42 ms raster (`22400 ≤ 42000`). Named un-netted loss: 15 min packing isolate (`abort_s=900`). Not folded into process heads.

Independent LIF (the one labeled sidecar sim): `state.sim_or_real` remains `designed`. `raster.excerpt_source=independent_lif`, `raster.sim_scope=sidecar_only`, `raster.lif` seed 117601, stim `[22000, 25000]`. Excerpt is membrane crossings (`lif.clamp` early vs `lif.pack` 22–25 ms), not a 1:1 remap of `spike_events`. `meta.tags` include `independent-lif-raster` and `sidecar-sim-only`.

## Reward formula and tick reconciliation

Declared aggregation on every record:

`total = task_progress + safety + efficiency + coherence + exploration`

Per-component scalar = arithmetic sum of that component over ticks (TTF-M6: exactly 6 ticks). Tick 6 is bound to a published sidecar (`abort_s`, `survey_s`, `dwell_s`) via `future_outcome.delayed_surprise_s` and is strictly after the raster window. Inflection `t_us` is an actual tick.

| id | ticks | tp | saf | eff | coh | exp | total | inflection tick |
|----|-------|----|-----|-----|-----|-----|-------|-----------------|
| 601 | 6 | +0.32 | −0.60 | −0.16 | +0.04 | −0.04 | −0.44 | 5 (22400) |
| 602 | 6 | −0.22 | −0.24 | −0.18 | −0.10 | +0.06 | −0.68 | 4 (6120) |
| 603 | 6 | +0.10 | +0.42 | +0.12 | +0.10 | +0.06 | +0.80 | 4 (7640) |
| 604 | 6 | +0.40 | +0.28 | +0.18 | +0.12 | +0.08 | +1.06 | 4 (7840) |
| 605 | 6 | +0.44 | +0.30 | +0.20 | +0.12 | +0.08 | +1.14 | 4 (5640) |

Tick-6 sidecar bind: 601 `abort_s=900`, 602 `abort_s=720`, 603 `abort_s=480`, 604 `survey_s=360`, 605 `dwell_s=240`.

## Raster / energy (Loihi-2 4-core, 23 pJ/spike)

| id | domain | n | rate Hz | window_ms | spikes | energy_pJ | energy_uJ |
|----|--------|---|---------|-----------|--------|-----------|-----------|
| 601 | chromyl-chloride-still | 76 | 26 | 42 | 83 | 1909 | 0.001909 |
| 602 | iron-pentacarbonyl-cracker | 88 | 34 | 28 | 84 | 1932 | 0.001932 |
| 603 | niobium-pentachloride-sublimer | 120 | 20 | 46 | 110 | 2530 | 0.002530 |
| 604 | lithium-niobate-czochralski | 48 | 42 | 28 | 56 | 1288 | 0.001288 |
| 605 | zinc-selenide-cvd | 80 | 28 | 24 | 54 | 1242 | 0.001242 |

`spikes = round(n × rate × window_s)`. Every record carries `gate_snn` whose `decision` matches the safety gate; populations that declare rate+spikes meet the same ±1 budget against `decision_window_s`. `routing.third_factor` has modulator (NA / ACh / DA / 5-HT / adenosine), `tau_e_s`/`tau_e_ms` pair, and eligibility. Excerpt same-neuron gap ≥ 1000 µs; spike trains same-channel refractory ≥ 0.8 ms. Non-601 excerpts are kernelized and independent of `spike_events` times (overlap < 0.8).

## Local checks (staging, not raw)

See generator stdout: `check_jsonl` FactoryStaging, `validate_run.check_line`, `dumps_exact_json`, `raster_status`, `verify_batch_for_frontier(strict=True)`, `spike_probe.py --strict`, tick sums, refractory, Jaccard.

Never `training_ready`. Never `sim_or_real=real`. Never wrote `outputs/raw/`.

## Residual weaknesses (honest)

1. Only **one** labeled independent LIF (601). The other four excerpts are independent of `spike_events` times but are not declared population sims.
2. Wrong-ACCEPT still absent (guard).
3. Tick-6 sidecar bind is standing machinery (r14+), not a new class.
4. Five domain slugs leave the prompt's 8-item pool; a later round that must stay inside the pool will have to rotate sit-outs instead.
5. 604 and 605 are both already-legal ACCEPTs; a later round could pair one ACCEPT with a world charge that does not go negative.

## Next densification target

Labeled LIF on a second record, or an ISI histogram sidecar. Remaining unused wrong-MODIFY subclasses include **output-tracking-as-PV** and **square-root extract on an already-linear tag** once cascade-secondary-as-primary is staged. Wrong-ACCEPT remains structurally absent until a prompt amendment.

Novel coverage: 16.4%
"""
