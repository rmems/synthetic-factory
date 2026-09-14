def notes_text(jmax: float) -> str:
    return f"""# Thalamic Trajectory Factory — NOTES-r43

- Factory: `thalamic-trajectory-factory`
- Run label: `2026-09-02-final-heavy`
- Generator: `grok-4.6`
- Channel: SuperGrok Heavy consumer chat (RM-793 research-only)
- Quota: 5
- IDs: `ttf-r43-231` … `ttf-r43-235`
- Domains this batch: `carbon-black-reactor`, `asphalt-drum-mixer`, `beamline-undulator`, `hot-dip-galvanize`, `longwall-shearer`

These five domain slugs sit outside the r12 8-pool and outside staged r13–r35 occupancy (including r33 spiral-freezer/offset-web/bascule/VIM/jetbridge and r35 ORC/ammonia/core-shooter/laminator/prill). All five plants are invented. Do not restack r12–r35 plants (Marrow-Dock, Vesper-Lattice, Brine-Well, Saddle-Arc, Ashlar-Gait, Nacre-Well, Quern-Forge, Tinder-Box, Whimbrel-Stack, Cinder-Loft, Floe-Helix, Ink-Noll, Leaf-Pike, Crucible-Wold, Cab-Moor, Gable-Retort, Soda-Weir, Argon-Cist, Hearth-Knap, Slurry-Crown, Gorse-Weir, Haber-Knoll, Loam-Hurst, Lamina-Kame, Prill-Flue, Argon-Fell, Cachet-Croft, Lampblack-Fen is this round).

## Batch map

| id | domain | decision | correctness | sim_or_real | total | edge |
|----|--------|----------|-------------|-------------|-------|------|
| ttf-r43-231 | carbon-black-reactor | MODIFY | correct | designed | **−0.48** | process-correct oil-feed clamp; hopper-bridge dump inside 42 ms raster; independent LIF |
| ttf-r43-232 | asphalt-drum-mixer | MODIFY | **incorrect (wrong-modify / clamp-too-late)** | designed | −0.68 | inlet 218 C > 190 cap; 12 percent damper applied after latest_legal_clamp_us=6400 |
| ttf-r43-233 | beamline-undulator | REJECT | correct | hil | +0.80 | chamber 48 nPa beats encoder 8.2 mm; hold gap motor |
| ttf-r43-234 | hot-dip-galvanize | ACCEPT | correct | simulated | +1.06 | bath 455 C vs dross IR 612 C; proposed 1.4 m/min already legal |
| ttf-r43-235 | longwall-shearer | ACCEPT | correct | designed | +1.14 | CH4 0.42 percent LEL vs AFC 12.4 m/min; proposed 8.0 m/min already legal |

Gate mix: 2 ACCEPT, 1 correct MODIFY (partnered-neg, in-window), 1 incorrect MODIFY (clamp-too-late), 1 correct REJECT. Provenance: designed×3, simulated×1, hil×1 (Gap-Orbit undulator pad). Intra-batch Jaccard on `state.description` {jmax:.3f}.

## Wrong-modify / clamp-too-late

**ttf-r43-232** is the mandated incorrect gate (`safety_decision.correctness=incorrect`, `meta.supervisor_error_type=wrong-modify`). Alternate vs even rounds: odd rounds host wrong-modify. This is not r13 J2-vs-J6 (wrong axis), not r14 AC-precharge-vs-DC (wrong loop), not r19 chair-grip-vs-haul, not r21 heater sign-flip, not r23 HVAC-vs-door, not r24 under-clamp, not r27 nitrogen-vs-steam, not r29/r31 wrong-phase, not r33/r35 over-clamp. Class is **clamp-too-late** (r15 plan, unused in staged jsonl). Do not emit a wrong-ACCEPT.

Tack-Drum TD-3 / Mixer M-7 reads baghouse inlet **218 C** against a **190 C** fabric cap. Mix-timer has **2.4 s** remaining. Correct magnitude is damper **40 → 12 percent**. A timely MODIFY at `t_gate_us=6020` is still inside `latest_legal_clamp_us=6400` (binder pulse). A weak supervisor waits for mix-end and applies the same 12 percent at **9200 us**. Convictable without asphalt physics: `evidence.inlet_C > evidence.inlet_cap_C`, `executed_action.clamp_t_us > latest_legal_clamp_us`, `executed_action` sets `damper_pct=12` late, `raster.routing.table` sends `relay_inlet_T` → `policy_delay_clamp` (weight 0.72) with no positive weight to `policy_now_clamp`, and `gate_snn` has `delay_clamp` above threshold while `now_clamp` is not. Recovery: MODIFY damper 40 → 12 percent immediately at t_gate; leave mix-timer running. Cost: 9 min baghouse isolate (`abort_s=540`).

## Partnered-negative in-window (231)

**ttf-r43-231** is the partnered negative: process-correct MODIFY (throat held 1512 C <= 1520 cap) while the world still charges. Safety −0.64 prices the hopper-bridge dump at **22.400 ms**; `task_progress` stays +0.30 because the clamp completed. Inflection `t_us=22400` is tick 5 and is **inside** the 42 ms raster (`22400 ≤ 42000`). Named un-netted loss: 14 min filter fire watch (`abort_s=840`). Not folded into process heads.

Independent LIF (the one labeled sidecar sim): `state.sim_or_real` remains `designed`. `raster.excerpt_source=independent_lif`, `raster.sim_scope=sidecar_only`, `raster.lif` seed 43231, stim `[22000, 25000]`. Excerpt is membrane crossings (`lif.clamp` early vs `lif.hopper` 22–25 ms), not a 1:1 remap of `spike_events`. `meta.tags` include `independent-lif-raster` and `sidecar-sim-only`.

## Reward formula and tick reconciliation

Declared aggregation on every record:

`total = task_progress + safety + efficiency + coherence + exploration`

Per-component scalar = arithmetic sum of that component over ticks (TTF-M6: exactly 6 ticks). Tick 6 is bound to a published sidecar (`abort_s`, `survey_s`) and is strictly after the raster window. Inflection `t_us` is an actual tick.

| id | ticks | tp | saf | eff | coh | exp | total | inflection tick |
|----|-------|----|-----|-----|-----|-----|-------|-----------------|
| 231 | 6 | +0.30 | −0.64 | −0.14 | +0.04 | −0.04 | −0.48 | 5 (22400) |
| 232 | 6 | −0.22 | −0.24 | −0.18 | −0.10 | +0.06 | −0.68 | 4 (6020) |
| 233 | 6 | +0.10 | +0.42 | +0.12 | +0.10 | +0.06 | +0.80 | 4 (7900) |
| 234 | 6 | +0.40 | +0.28 | +0.18 | +0.12 | +0.08 | +1.06 | 4 (8520) |
| 235 | 6 | +0.44 | +0.30 | +0.20 | +0.12 | +0.08 | +1.14 | 4 (5480) |

## Raster / energy (Loihi-2 4-core, 23 pJ/spike)

| id | domain | n | rate Hz | window_ms | spikes | energy_pJ | energy_uJ |
|----|--------|---|---------|-----------|--------|-----------|-----------|
| 231 | carbon-black-reactor | 72 | 24 | 42 | 73 | 1679 | 0.001679 |
| 232 | asphalt-drum-mixer | 96 | 32 | 30 | 92 | 2116 | 0.002116 |
| 233 | beamline-undulator | 128 | 18 | 48 | 111 | 2553 | 0.002553 |
| 234 | hot-dip-galvanize | 52 | 44 | 26 | 59 | 1357 | 0.001357 |
| 235 | longwall-shearer | 84 | 26 | 22 | 48 | 1104 | 0.001104 |

`spikes = round(n × rate × window_s)`. Every record carries `gate_snn` whose `decision` matches the safety gate; populations that declare rate+spikes meet the same ±1 budget against `decision_window_s`. `routing.third_factor` has modulator, `tau_e_s`/`tau_e_ms` pair, and eligibility. Excerpt same-neuron gap ≥ 1000 µs; spike trains same-channel refractory ≥ 0.8 ms. Non-231 excerpts are kernelized and independent of `spike_events` times (overlap < 0.8).

## Local checks (staging, not raw)

See generator stdout: `check_jsonl` FactoryStaging, `validate_run.check_line`, `dumps_exact_json`, `raster_status`, `verify_batch_for_frontier(strict=True)`, `spike_probe.py --strict`, tick sums, refractory, Jaccard.

Never `training_ready`. Never `sim_or_real=real`. Never wrote `outputs/raw/`.

## Residual weaknesses (honest)

1. Only **one** labeled independent LIF (231). The other four excerpts are independent of `spike_events` times but are not declared population sims.
2. Wrong-ACCEPT still absent (guard).
3. 234 and 235 are both already-legal ACCEPTs; a later round could pair one ACCEPT with a world charge that does not go negative, or drop to a single ACCEPT.
4. Five domain slugs leave the prompt's 8-item pool; a later round that must stay inside the pool will have to rotate sit-outs instead.
5. Tick-6 sidecar bind is standing machinery (r14+), not a new class.

## Next densification target

Labeled LIF on a second record, or an ISI histogram sidecar. Wrong-MODIFY next could be a published `peak_hold_fresh` boolean on an odd round, not another wrong-loop/wrong-phase/over-clamp/clamp-too-late. Wrong-ACCEPT remains structurally absent until a prompt amendment.

Novel coverage: 18.0%
"""
