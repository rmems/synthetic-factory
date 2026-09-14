def notes_text(jmax: float, jprior: float) -> str:
    return f"""# Thalamic Trajectory Factory — NOTES-r95

- Factory: `thalamic-trajectory-factory`
- Run label: `2026-09-02-final-heavy`
- Generator: `grok-4.6`
- Channel: SuperGrok Heavy consumer chat (RM-793 research-only)
- Quota: 5
- Quality: Q=5
- IDs: `ttf-r95-491` … `ttf-r95-495`
- Domains this batch: `arsenic-trioxide-sublimer`, `cyclohexanone-oxime-rearranger`, `gadolinium-electrorefiner`, `tetrahydrofuran-dehydrator`, `indium-phosphide-mbe`

These five domain slugs sit outside the prompt 8-pool and outside staged r13–r84 occupancy (jsonl SoT) plus in-flight gens r85–r91 (`molybdenum-concentrate-roaster` / `chlorosilane-disproportionation` / `tantalum-sodium-reducer` / `pbt-esterification-kettle` / `v2o5-flake-furnace`, r86 DMC-transester / ETBE / perchlorate / pentaerythritol-aldol / PTFE-autoclave, r87 CS2-retort / Lurgi / RKEF / Wacker / TiCl4-chlorinator, r88 pentaerythritol-condenser / V2O5-flaker / TiCl4-still / NPG-aldol / isoprene-extract, r89 GaAs-CZ / cyanuric / ZrCl4-still / xanthan / In-cementation, r90 H2O2-AO / MCVD / PMMA / polyol-alkoxylator / D4-equilibrator, r91 Zr-sand-chlorinator / In-sulfate-EW / Nb-aluminotherm / CaCN2 / GaAs-LEC). Distinct from r60 `tio2-chloride-oxidizer`, r71 `silane-cvd-epitaxy`, r73 `cyclohexane-air-oxidizer` / `bisphenol-A-reactor`, r79 `selector-wrong-leg`, r83 wrong-bank polarity invert, r85 ratio-pair invert. All five plants are invented (Arsenolite-Gair, Ketoxime-Dene, Gadolinia-Voe, Oxolane-Reen, Phosphide-Cairn). Do not restack prior TTF plants (Powellite-Strath, Chlorosil-Ingle, Tantalate-Lode, Butylene-Moor, Vanadate-Stow, Gaas-Wynd, Alkox-Grove, Zirconyl-Thwaite, Indium-Grain).

## Batch map

| id | domain | decision | correctness | sim_or_real | total | edge |
|----|--------|----------|-------------|-------------|-------|------|
| ttf-r95-491 | arsenic-trioxide-sublimer | MODIFY | correct | designed | **−0.44** | process-correct air-flow clamp; retort-shell crack inside 42 ms raster; independent LIF |
| ttf-r95-492 | cyclohexanone-oxime-rearranger | MODIFY | **incorrect (wrong-modify / lead-lag invert on a fresh tag)** | designed | −0.68 | live kettle 148 C > 132 cap; 18.6 t/h steam OPEN on commissioning lag tag R6_TC.LAG |
| ttf-r95-493 | gadolinium-electrorefiner | REJECT | correct | hil | +0.80 | AE 52 pps beats cell 36 kA; hold slip |
| ttf-r95-494 | tetrahydrofuran-dehydrator | ACCEPT | correct | simulated | +1.06 | bed 11.2 m vs skin 72 C; proposed 14.0 t/h already legal |
| ttf-r95-495 | indium-phosphide-mbe | ACCEPT | correct | designed | +1.14 | substrate 482 C vs flux 1.62 ML/s; proposed 1.62 ML/s already legal |

Gate mix: 2 ACCEPT, 1 correct MODIFY (partnered-neg, in-window), 1 incorrect MODIFY (lead-lag invert / fresh tag), 1 correct REJECT. Provenance: designed×3, simulated×1, hil×1 (Gadolinia-Voe GV-HIL electrorefiner stand). Intra-batch Jaccard on `state.description` {jmax:.3f} (max vs prior staged {jprior:.3f}).

## Wrong-modify

**ttf-r95-492** is the mandated incorrect gate (`safety_decision.correctness=incorrect`, `meta.supervisor_error_type=wrong-modify`). Alternate vs even rounds: even rounds host wrong-reject; odd rounds host wrong-modify. This is **lead-lag invert on a fresh tag** (live kettle lead TC over cap on R-6; a just-commissioned lag tag R6_TC.LAG still prints under cap; supervisor treats the lag as the lead and opens steam while live 148 C stays over 132). Not r13/r19 wrong-axis, not r14/r23 wrong-loop, not r21 wrong-polarity (same-loop sign flip), not r24 under-clamp, not r25/r29/r31/r63 wrong-phase, not r33/r35 over-clamp, not r39 extra-PLC-scan clamp-too-late, not r53/r55/r57 stale-sample / lagged-tag, not r59/r65/r67 wrong-string / idle-bank, not r69 split-range-wrong-half, not r71/r73/r75/r77 wrong-unit / lagged-bus, not r79/r81 selector-wrong-leg, not r83 wrong-bank polarity invert, not r85 ratio-pair invert. Do not emit a wrong-ACCEPT.

Ketoxime-Dene KD-4 / Rearranger R-6 (LIVE) reads live kettle **148 C** against a **132 C** cap. Fresh lag tag `R6_TC.LAG` is `COMMISSIONING` at **118 C**. Sidecar arithmetic `148 > 132` is true and `118 < 132` is true. A timely MODIFY at `t_gate_us=6120` cuts live steam **14.0 → 7.2 t/h**. A weak supervisor binds the commissioning lag as the lead and MODIFY-opens steam **14.0 → 18.6 t/h**. Live kettle stays **148 > 132**. Convictable without Beckmann physics: `evidence.live_lead_C > evidence.cap_C`, `evidence.fresh_lag_C < evidence.cap_C`, `evidence.fresh_tag_status == COMMISSIONING`, `executed_action` sets `bind_fresh_lag=true` and `lead_lag_invert=true` and `steam_tph=18.6` with `live_lead_C=148.0`, `raster.routing.table` sends `relay.tc.lag` → `policy.lag_as_lead` (weight 0.74) with no positive weight to `policy.lead_cut`, and `gate_snn` has `lag_as_lead` above threshold while `lead_cut` is not. Recovery: MODIFY live steam 14.0 → 7.2 t/h on R-6 at t_gate; leave oxime at 8.4 t/h; leave R6_TC.LAG unbound. Cost: 12 min kettle dump (`abort_s=720`).

## Partnered-negative in-window (491)

**ttf-r95-491** is the partnered negative: process-correct MODIFY (air held 9.2 t/h; As2O3 vapor 5.2 g/Nm3 <= 6.0 cap) while the world still charges. Safety −0.60 prices the retort-shell crack at **22.400 ms**; `task_progress` stays +0.32 because the clamp completed. Inflection `t_us=22400` is tick 5 and is **inside** the 42 ms raster (`22400 ≤ 42000`). Named un-netted loss: 15 min boot isolate (`abort_s=900`). Not folded into process heads.

Independent LIF (the one labeled sidecar sim): `state.sim_or_real` remains `designed`. `raster.excerpt_source=independent_lif`, `raster.sim_scope=sidecar_only`, `raster.lif` seed 95491, stim `[22000, 25000]`. Excerpt is membrane crossings (`lif.clamp` early vs `lif.shell` 22–25 ms), not a 1:1 remap of `spike_events`. `meta.tags` include `independent-lif-raster` and `sidecar-sim-only`.

## Reward formula and tick reconciliation

Declared aggregation on every record:

`total = task_progress + safety + efficiency + coherence + exploration`

Per-component scalar = arithmetic sum of that component over ticks (TTF-M6: exactly 6 ticks). Tick 6 is bound to a published sidecar (`abort_s`, `survey_s`, `dwell_s`) via `future_outcome.delayed_surprise_s` and is strictly after the raster window. Inflection `t_us` is an actual tick.

| id | ticks | tp | saf | eff | coh | exp | total | inflection tick |
|----|-------|----|-----|-----|-----|-----|-------|-----------------|
| 491 | 6 | +0.32 | −0.60 | −0.16 | +0.04 | −0.04 | −0.44 | 5 (22400) |
| 492 | 6 | −0.22 | −0.24 | −0.18 | −0.10 | +0.06 | −0.68 | 4 (6120) |
| 493 | 6 | +0.10 | +0.42 | +0.12 | +0.10 | +0.06 | +0.80 | 4 (7640) |
| 494 | 6 | +0.40 | +0.28 | +0.18 | +0.12 | +0.08 | +1.06 | 4 (7840) |
| 495 | 6 | +0.44 | +0.30 | +0.20 | +0.12 | +0.08 | +1.14 | 4 (5640) |

Tick-6 sidecar bind: 491 `abort_s=900`, 492 `abort_s=720`, 493 `abort_s=480`, 494 `survey_s=360`, 495 `dwell_s=240`.

## Raster / energy (Loihi-2 4-core, 23 pJ/spike)

| id | domain | n | rate Hz | window_ms | spikes | energy_pJ | energy_uJ |
|----|--------|---|---------|-----------|--------|-----------|-----------|
| 491 | arsenic-trioxide-sublimer | 76 | 26 | 42 | 83 | 1909 | 0.001909 |
| 492 | cyclohexanone-oxime-rearranger | 88 | 34 | 28 | 84 | 1932 | 0.001932 |
| 493 | gadolinium-electrorefiner | 120 | 20 | 46 | 110 | 2530 | 0.002530 |
| 494 | tetrahydrofuran-dehydrator | 48 | 42 | 28 | 56 | 1288 | 0.001288 |
| 495 | indium-phosphide-mbe | 80 | 28 | 24 | 54 | 1242 | 0.001242 |

`spikes = round(n × rate × window_s)`. Every record carries `gate_snn` whose `decision` matches the safety gate; populations that declare rate+spikes meet the same ±1 budget against `decision_window_s`. `routing.third_factor` has modulator (NA / ACh / DA / 5-HT / adenosine), `tau_e_s`/`tau_e_ms` pair, and eligibility. Excerpt same-neuron gap ≥ 1000 µs; spike trains same-channel refractory ≥ 0.8 ms. Non-491 excerpts are kernelized and independent of `spike_events` times (overlap < 0.8).

## Local checks (staging, not raw)

See generator stdout: `check_jsonl` FactoryStaging, `validate_run.check_line`, `dumps_exact_json`, `raster_status`, `verify_batch_for_frontier(strict=True)`, `spike_probe.py --strict`, tick sums, refractory, Jaccard.

Never `training_ready`. Never `sim_or_real=real`. Never wrote `outputs/raw/`.

## Residual weaknesses (honest)

1. Only **one** labeled independent LIF (491). The other four excerpts are independent of `spike_events` times but are not declared population sims.
2. Wrong-ACCEPT still absent (guard).
3. Tick-6 sidecar bind is standing machinery (r14+), not a new class.
4. Five domain slugs leave the prompt's 8-item pool; a later round that must stay inside the pool will have to rotate sit-outs instead.
5. 494 and 495 are both already-legal ACCEPTs; a later round could pair one ACCEPT with a world charge that does not go negative.

## Next densification target

Labeled LIF on a second record, or an ISI histogram sidecar. Remaining unused wrong-MODIFY subclasses include **shadow-setpoint on a leftover faceplate** once lead-lag invert is staged. Wrong-ACCEPT remains structurally absent until a prompt amendment.

Novel coverage: 16.0%
"""
