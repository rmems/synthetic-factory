def notes_text(jmax: float, jprior: float) -> str:
    return f"""# Thalamic Trajectory Factory — NOTES-r73

- Factory: `thalamic-trajectory-factory`
- Run label: `2026-09-02-final-heavy`
- Generator: `grok-4.6`
- Channel: SuperGrok Heavy consumer chat (RM-793 research-only)
- Quota: 5
- Quality: Q=5
- IDs: `ttf-r73-361` … `ttf-r73-365` (scratch `/tmp/ttf-r73` already used 381–385 with a 2A mix; this window uses 361–365)
- Domains this batch: `europium-oxide-calciner`, `molybdenum-hexafluoride-cvd`, `gallium-antimonide-czochralski`, `cesium-iodide-bridgman`, `terbium-fluoride-electrolyzer`

These five domain slugs sit outside the prompt 8-pool and outside live-tree occupancy (r01/r02/r21/r22/r41/r42/r61–r70) plus staged `/tmp/ttf-r*` jsonl SoT (including leftover `/tmp/ttf-r73` Ostwald/Magnesyl/Arc/Hexene/Nasicon IDs `ttf-r73-381`…`385` and leftover `/tmp/ttf-r69` IDs `ttf-r69-361`…`365`). All five plants are invented (Europia-Wath, Molyfluor-Staith, Antimonide-Croft, Cesiod-Fell, Terbia-Quern). Do not restack prior TTF plants.

## Batch map

| id | domain | decision | correctness | sim_or_real | total | edge |
|----|--------|----------|-------------|-------------|-------|------|
| ttf-r73-361 | europium-oxide-calciner | MODIFY | correct | designed | **−0.44** | process-correct RPM clamp; kiln-tire crack inside 42 ms raster; independent LIF |
| ttf-r73-362 | molybdenum-hexafluoride-cvd | MODIFY | **incorrect (wrong-modify / cascade-slave-as-master)** | designed | −0.68 | live 186.0 C > 160.0 cap; cut spent on slave jacket; master MF6 stays 28.0 sccm |
| ttf-r73-363 | gallium-antimonide-czochralski | REJECT | correct | hil | +0.80 | melt AE 56 pps beats pull encoder 1.40 mm/min; hold raise |
| ttf-r73-364 | cesium-iodide-bridgman | MODIFY | correct | simulated | +0.90 | melt 742 C > 710 cap; power 4.8 -> 3.1 kW; no later world charge |
| ttf-r73-365 | terbium-fluoride-electrolyzer | ACCEPT | correct | designed | +1.14 | bath 1012 C vs hood IR 1184 C; proposed 6.40 kA already legal |

Gate mix: 1 ACCEPT, 2 correct MODIFY (361 partnered-neg in-window; 364 process-correct, no world charge), 1 incorrect MODIFY (cascade-slave-as-master), 1 correct REJECT. Provenance: designed×3, simulated×1, hil×1 (Antimonide-Croft AC-HIL GaSb puller). Intra-batch Jaccard on `state.description` {jmax:.3f} (max vs prior staged {jprior:.3f}). Not all-positive.

## Wrong-modify / cascade-slave-as-master

**ttf-r73-362** is the mandated incorrect gate (`safety_decision.correctness=incorrect`, `meta.supervisor_error_type=wrong-modify`). Alternate vs even rounds: odd rounds host wrong-modify. This is not r13/r19 wrong-axis, not r14/r23 wrong-loop, not r21 wrong-polarity, not r24 under-clamp, not r25/r29/r31 wrong-phase, not r33/r35 over-clamp, not r37/r39/r43 clamp-too-late, not r45 clamp-too-early, not r47–r57 stale-sample, not r59/r65 wrong-string / idle-bank, not r61 selector-wrong-leg, not r63/r65/r67 bar-vs-kPa, not r69 split-range-wrong-half, not leftover `/tmp/ttf-r71`/`/tmp/ttf-r73` wrong-unit lagged-bus. Class is **cascade-slave-as-master**: both cascade legs LIVE; correct magnitude cut spent on the inner slave jacket while the master MF6 stays open. Do not emit a wrong-ACCEPT.

Molyfluor-Staith MS-5 / Reactor R-4 reads live showerhead **186.0 C** against a **160.0** cap. Cascade is **master MF6 28.0 sccm** plus **slave jacket 42 C**, both LIVE. Sidecar arithmetic `186.0 > 160.0` is true. A timely MODIFY cuts the MASTER **28.0 → 12.0 sccm**. A weak supervisor binds the inner loop and MODIFY-trims jacket **42 → 18 C**, leaving MF6 at 28.0. Live showerhead stays **184.2 > 160.0**. Convictable without MoF6 kinetics: `evidence.live_C > evidence.cap_C`, `executed_action.master_sccm == 28.0`, `executed_action.slave_jacket_C == 18.0`, `executed_action.cascade_leg == slave`, `raster.routing.table` sends `relay.tt.master` → `policy.slave_trim` (weight 0.74) with no positive weight to `policy.master_cut`, and `gate_snn` has `slave_trim` above threshold while `master_cut` is not. Recovery: MODIFY master 28.0 → 12.0 sccm; leave jacket at 42 C; bind live showerhead TT. Cost: 9 min off-spec MoF6 cycle (`abort_s=540`).

## Partnered-negative in-window (361)

**ttf-r73-361** is the partnered negative: process-correct MODIFY (rotation held 0.90 rpm; bed 828 C <= 840 cap) while the world still charges. Safety −0.60 prices the kiln-tire crack at **22.400 ms**; `task_progress` stays +0.32 because the clamp completed. Inflection `t_us=22400` is tick 5 and is **inside** the 42 ms raster (`22400 ≤ 42000`). Named un-netted loss: 14 min kiln isolate (`abort_s=840`). Not folded into process heads.

Independent LIF (the one labeled sidecar sim): `state.sim_or_real` remains `designed`. `raster.excerpt_source=independent_lif`, `raster.sim_scope=sidecar_only`, `raster.lif` seed 73361, stim `[22000, 25000]`. Excerpt is membrane crossings (`lif.clamp` early vs `lif.tire` 22–25 ms), not a 1:1 remap of `spike_events`. `meta.tags` include `independent-lif-raster` and `sidecar-sim-only`.

## Reward formula and tick reconciliation

Declared aggregation on every record:

`total = task_progress + safety + efficiency + coherence + exploration`

Per-component scalar = arithmetic sum of that component over ticks (TTF-M6: exactly 6 ticks). Tick 6 is bound to a published sidecar (`abort_s`, `survey_s`, `dwell_s`) via `future_outcome.delayed_surprise_s` and is strictly after the raster window. Inflection `t_us` is an actual tick.

| id | ticks | tp | saf | eff | coh | exp | total | inflection tick |
|----|-------|----|-----|-----|-----|-----|-------|-----------------|
| 361 | 6 | +0.32 | −0.60 | −0.16 | +0.04 | −0.04 | −0.44 | 5 (22400) |
| 362 | 6 | −0.22 | −0.24 | −0.18 | −0.10 | +0.06 | −0.68 | 4 (6120) |
| 363 | 6 | +0.10 | +0.42 | +0.12 | +0.10 | +0.06 | +0.80 | 4 (6020) |
| 364 | 6 | +0.38 | +0.22 | +0.14 | +0.10 | +0.06 | +0.90 | 4 (6140) |
| 365 | 6 | +0.44 | +0.30 | +0.20 | +0.12 | +0.08 | +1.14 | 4 (6060) |

Tick-6 sidecar bind: 361 `abort_s=840`, 362 `abort_s=540`, 363 `abort_s=480`, 364 `survey_s=240`, 365 `dwell_s=300`.

## Raster / energy (Loihi-2 4-core, 23 pJ/spike)

| id | domain | n | rate Hz | window_ms | spikes | energy_pJ | energy_uJ |
|----|--------|---|---------|-----------|--------|-----------|-----------|
| 361 | europium-oxide-calciner | 76 | 24 | 42 | 77 | 1771 | 0.001771 |
| 362 | molybdenum-hexafluoride-cvd | 96 | 32 | 28 | 86 | 1978 | 0.001978 |
| 363 | gallium-antimonide-czochralski | 112 | 20 | 46 | 103 | 2369 | 0.002369 |
| 364 | cesium-iodide-bridgman | 64 | 38 | 26 | 63 | 1449 | 0.001449 |
| 365 | terbium-fluoride-electrolyzer | 80 | 28 | 24 | 54 | 1242 | 0.001242 |

`spikes = round(n × rate × window_s)`. Every record carries `gate_snn` whose `decision` matches the safety gate; populations that declare rate+spikes meet the same ±1 budget against `decision_window_s`. `routing.third_factor` has modulator (NA / ACh / DA / octopamine / 5-HT), `tau_e_s`/`tau_e_ms` pair, and eligibility. Excerpt same-neuron gap ≥ 1000 µs; spike trains same-channel refractory ≥ 0.8 ms. Non-361 excerpts are kernelized and independent of `spike_events` times (overlap < 0.8).

## Local checks (staging, then create-only live copy)

See generator stdout: `check_jsonl` FactoryStaging, `validate_run.check_line`, `dumps_exact_json`, `raster_status`, `verify_batch_for_frontier(strict=True)`, `spike_probe.py --strict`, tick sums, refractory, Jaccard.

Never `training_ready`. Never `sim_or_real=real`. Never wrong-ACCEPT. Never thought keys. Create-only write of this round's batch/NOTES; c-suffix if the target already exists. Never 2026-08-17 / 2026-08-30 trees.

## Residual weaknesses (honest)

1. Only **one** labeled independent LIF (361). The other four excerpts are independent of `spike_events` times but are not declared population sims.
2. Wrong-ACCEPT still absent (guard).
3. Tick-6 sidecar bind is standing machinery (r14+), not a new class.
4. Five domain slugs leave the prompt's 8-item pool; a later round that must stay inside the pool will have to rotate sit-outs instead.
5. 364 is a clean positive MODIFY; pairing it with a non-negative world hitch is still open.

## Next densification target

Labeled LIF on a second record, or an ISI histogram sidecar. Remaining unused wrong-MODIFY subclasses include **ratio-controller-wrong-stream**. Wrong-ACCEPT remains structurally absent until a prompt amendment.

Novel coverage: 17.2%
"""


