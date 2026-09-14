#!/usr/bin/env python3
"""Splices r99 plants, analog physics, and feedforward-as-feedback into gen_r99.py."""
from __future__ import annotations

import re
from pathlib import Path

GEN = Path("/tmp/ttf-r99/gen_r99.py")
REC512 = Path("/tmp/ttf-r99/_rec512.py")


def extract_fn(src: str, name: str) -> tuple[int, int]:
    m = re.search(rf"^def {name}\(", src, re.M)
    if not m:
        raise SystemExit(f"missing {name}")
    start = m.start()
    nxt = re.search(r"^def ", src[m.end() :], re.M)
    if not nxt:
        raise SystemExit(f"no successor after {name}")
    end = m.end() + nxt.start()
    return start, end


def apply_pairs(text: str, pairs: list[tuple[str, str]]) -> str:
    for old, new in pairs:
        text = text.replace(old, new)
    return text


THIS_DOMAINS = '''THIS_DOMAINS = {
    "phosphorus-oxychloride-still",
    "sodium-hydrosulfite-reactor",
    "strontium-carbonate-precipitator",
    "polybutadiene-solution-polymerizer",
    "bismuth-oxychloride-precipitator",
}'''

THIS_PLANTS = '''THIS_PLANTS = (
    "Oxychlor-Holt",
    "Dithion-Beck",
    "Strontia-Mire",
    "Solpoly-Knap",
    "Bismuth-Quoin",
)'''

NOTES = r'''def notes_text(jmax: float) -> str:
    return f"""# Thalamic Trajectory Factory — NOTES-r99

- Factory: `thalamic-trajectory-factory`
- Run label: `2026-09-02-final-heavy`
- Generator: `grok-4.6`
- Channel: SuperGrok Heavy consumer chat (RM-793 research-only)
- Quota: 5
- Quality: Q=5
- IDs: `ttf-r99-511` … `ttf-r99-515`
- Domains this batch: `phosphorus-oxychloride-still`, `sodium-hydrosulfite-reactor`, `strontium-carbonate-precipitator`, `polybutadiene-solution-polymerizer`, `bismuth-oxychloride-precipitator`

These five domain slugs sit outside the prompt 8-pool and outside staged r13–r89 occupancy plus in-flight gens (r90 silicone-D4/polyol/PMMA/H2O2/MCVD, r91 Zr-sand/In-EW/Nb-aluminotherm/CaCN2/GaAs-LEC, r92 caprolactone/polyol/InP-LPE/BN-hotpress/KMnO4, r93 HMDA/Tishchenko/precip-silica/NMC/Cu-foil, r94 HMDA/MEK/Kroll/LAB/lactide, r95 As2O3/oxime/Gd-EW/THF/InP-MBE). All five plants are invented (Oxychlor-Holt, Dithion-Beck, Strontia-Mire, Solpoly-Knap, Bismuth-Quoin). Do not restack prior TTF plants.

## Batch map

| id | domain | decision | correctness | sim_or_real | total | edge |
|----|--------|----------|-------------|-------------|-------|------|
| ttf-r99-511 | phosphorus-oxychloride-still | MODIFY | correct | designed | **−0.48** | process-correct steam clamp; packing-ring slump inside 42 ms raster; independent LIF |
| ttf-r99-512 | sodium-hydrosulfite-reactor | MODIFY | **incorrect (wrong-modify / feedforward-as-feedback)** | designed | −0.68 | live 94.0 C > 88.0 cap; FF SO2-load predictor opens 12.0 → 16.4 t/h |
| ttf-r99-513 | strontium-carbonate-precipitator | REJECT | correct | hil | +0.80 | rake AE 58 pps beats slurry dens 1.18; hold raise |
| ttf-r99-514 | polybutadiene-solution-polymerizer | ACCEPT | correct | simulated | +1.06 | conversion 74 pct vs jacket IR 34 C; proposed 4.6 t/h already legal |
| ttf-r99-515 | bismuth-oxychloride-precipitator | ACCEPT | correct | designed | +1.14 | liquor Bi 186 ppm vs drum IR 36 C; proposed 2.1 t/h already legal |

Gate mix: 2 ACCEPT, 1 correct MODIFY (partnered-neg, in-window), 1 incorrect MODIFY (feedforward-as-feedback), 1 correct REJECT. Provenance: designed×3, simulated×1, hil×1 (Strontia-Mire SM-HIL SrCO3 precipitator). Intra-batch Jaccard on `state.description` {jmax:.3f}.

## Wrong-modify / feedforward-as-feedback

**ttf-r99-512** is the mandated incorrect gate (`safety_decision.correctness=incorrect`, `meta.supervisor_error_type=wrong-modify`). Alternate vs even rounds: odd rounds host wrong-modify. This is not r13/r19 wrong-axis, not r14/r23 wrong-loop, not r21 wrong-polarity, not r24 under-clamp, not r25/r29/r31 wrong-phase, not r33/r35 over-clamp, not r37/r39/r43 clamp-too-late, not r45 clamp-too-early, not r47/r49/r51/r53/r55/r57 stale-sample, not r59/r65/r67 wrong-string / idle-bank, not r69 split-range-wrong-half, not r71/r73/r75/r77 wrong-unit / lagged-bus, not r79 selector-wrong-leg, not r83 wrong-bank polarity-invert, not r85 ratio-pair invert, not r87 dual-range deadband polarity, not r89 dual-range-wrong-band. Class is **feedforward-as-feedback**: live TC over cap; a feedforward load predictor is not the PV; a weak supervisor binds the FF tag as if it were feedback and OPENS the load valve. Do not emit a wrong-ACCEPT.

Dithion-Beck DB-7 / Reactor R-4 reads live hydrosulfite **94.0 C** against an **88.0** cap. Feedforward SO2-load last-good is **8.4 t/h**. `ff_is_pv=false`. Sidecar arithmetic `94.0 > 88.0` is true. A timely MODIFY cuts LIVE steam **6.4 → 3.8 t/h**. A weak supervisor binds the unused FF load tag and MODIFY-opens SO2 **12.0 → 16.4 t/h**. Live T stays **96.8 > 88.0**. Convictable without hydrosulfite chemistry: `evidence.live_tc_C > evidence.cap_tc_C`, `evidence.ff_is_pv == false`, `executed_action.bind_feedforward == true`, `executed_action.so2_tph == 16.4`, `raster.routing.table` sends `relay_tc_live` → `policy_ff_so2_open` (weight 0.74) with no positive weight to `policy_fb_steam_cut`, and `gate_snn` has `ff_so2_open` above threshold while `fb_steam_cut` is not. Recovery: MODIFY steam 6.4 → 3.8 t/h; leave SO2 at 12.0; bind live TC. Cost: 10 min off-spec hydrosulfite dump (`abort_s=600`).

## Partnered-negative in-window (511)

**ttf-r99-511** is the partnered negative: process-correct MODIFY (steam held 3.2 t/h; base 139 C <= 142 cap) while the world still charges. Safety −0.64 prices the packing-ring slump at **22.600 ms**; `task_progress` stays +0.30 because the clamp completed. Inflection `t_us=22600` is tick 5 and is **inside** the 42 ms raster (`22600 ≤ 42000`). Named un-netted loss: 15 min still isolate (`abort_s=900`). Not folded into process heads.

Independent LIF (the one labeled sidecar sim): `state.sim_or_real` remains `designed`. `raster.excerpt_source=independent_lif`, `raster.sim_scope=sidecar_only`, `raster.lif` seed 99511, stim `[22000, 25000]`. Excerpt is membrane crossings (`lif.clamp` early vs `lif.pack` 22–25 ms), not a 1:1 remap of `spike_events`. `meta.tags` include `independent-lif-raster` and `sidecar-sim-only`.

## Reward formula and tick reconciliation

Declared aggregation on every record:

`total = task_progress + safety + efficiency + coherence + exploration`

Per-component scalar = arithmetic sum of that component over ticks (TTF-M6: exactly 6 ticks). Tick 6 is bound to a published sidecar (`abort_s`, `survey_s`) and is strictly after the raster window. Inflection `t_us` is an actual tick.

| id | ticks | tp | saf | eff | coh | exp | total | inflection tick |
|----|-------|----|-----|-----|-----|-----|-------|-----------------|
| 511 | 6 | +0.30 | −0.64 | −0.14 | +0.04 | −0.04 | −0.48 | 5 (22600) |
| 512 | 6 | −0.22 | −0.24 | −0.18 | −0.10 | +0.06 | −0.68 | 4 (6080) |
| 513 | 6 | +0.10 | +0.42 | +0.12 | +0.10 | +0.06 | +0.80 | 4 (7980) |
| 514 | 6 | +0.40 | +0.28 | +0.18 | +0.12 | +0.08 | +1.06 | 4 (8360) |
| 515 | 6 | +0.44 | +0.30 | +0.20 | +0.12 | +0.08 | +1.14 | 4 (5360) |

Tick-6 sidecar bind: 511 `abort_s=900`, 512 `abort_s=600`, 513 `abort_s=420`, 514 `survey_s=180`, 515 `survey_s=300`.

## Raster / energy (Loihi-2 4-core, 23 pJ/spike)

| id | domain | n | rate Hz | window_ms | spikes | energy_pJ | energy_uJ |
|----|--------|---|---------|-----------|--------|-----------|-----------|
| 511 | phosphorus-oxychloride-still | 76 | 24 | 42 | 77 | 1771 | 0.001771 |
| 512 | sodium-hydrosulfite-reactor | 92 | 30 | 30 | 83 | 1909 | 0.001909 |
| 513 | strontium-carbonate-precipitator | 108 | 22 | 44 | 105 | 2415 | 0.002415 |
| 514 | polybutadiene-solution-polymerizer | 54 | 38 | 26 | 53 | 1219 | 0.001219 |
| 515 | bismuth-oxychloride-precipitator | 82 | 28 | 24 | 55 | 1265 | 0.001265 |

`spikes = round(n × rate × window_s)`. Every record carries `gate_snn` whose `decision` matches the safety gate; populations that declare rate+spikes meet the same ±1 budget against `decision_window_s`. `routing.third_factor` has modulator, `tau_e_s`/`tau_e_ms` pair, and eligibility. Excerpt same-neuron gap ≥ 1000 µs; spike trains same-channel refractory ≥ 0.8 ms. Non-511 excerpts are kernelized and independent of `spike_events` times (overlap < 0.8).

## Local checks (staging, not raw)

See generator stdout: `check_jsonl` FactoryStaging, `validate_run.check_line`, `dumps_exact_json`, `raster_status`, `verify_batch_for_frontier(strict=True)`, `spike_probe.py --strict`, tick sums, refractory, Jaccard.

Never `training_ready`. Never `sim_or_real=real`. Never wrote `outputs/raw/`.

## Residual weaknesses (honest)

1. Only **one** labeled independent LIF (511). The other four excerpts are independent of `spike_events` times but are not declared population sims.
2. Wrong-ACCEPT still absent (guard).
3. 514 and 515 are both already-legal ACCEPTs; a later round could pair one ACCEPT with a world charge that does not go negative, or drop to a single ACCEPT.
4. Five domain slugs leave the prompt's 8-item pool; a later round that must stay inside the pool will have to rotate sit-outs instead.
5. Tick-6 sidecar bind is standing machinery (r14+), not a new class.

## Next densification target

Labeled LIF on a second record, or an ISI histogram sidecar. Remaining unused wrong-MODIFY subclasses include **percent-open vs percent-closed** once feedforward-as-feedback is staged. Wrong-ACCEPT remains structurally absent until a prompt amendment.

Novel coverage: 16.2%
"""
'''

CHECK_512 = '''        if rec["id"] == "ttf-r99-512":
            if "recovery" not in rec["future_outcome"]:
                issues.append("512 missing recovery")
            if exec_p.get("bind_feedforward") is not True:
                issues.append("512 bind_feedforward not true")
            if exec_p.get("so2_tph") != 16.4:
                issues.append("512 so2_tph not 16.4 (wrong open)")
            live = rec["proposed_action"]["evidence"].get("live_tc_C")
            cap = rec["proposed_action"]["evidence"].get("cap_tc_C")
            if live is None or cap is None or live <= cap:
                issues.append("512 live tc not over cap")
            if rec["proposed_action"]["evidence"].get("ff_is_pv") is not False:
                issues.append("512 ff_is_pv not false")
            if "feedforward-as-feedback" not in rec["meta"].get("tags", []):
                issues.append("512 missing feedforward-as-feedback tag")
            tos = {row["to"] for row in rec["raster"]["routing"]["table"]}
            if "policy_fb_steam_cut" in tos:
                issues.append("512 routing contains policy_fb_steam_cut")
            if "policy_ff_so2_open" not in tos:
                issues.append("512 routing missing policy_ff_so2_open")
'''

PAIRS_511 = [
    ("Puller P-3 at Gaas-Wynd GW-4 is driving 42 kW of resistance heater while the ",
     "Still PO-3 at Oxychlor-Holt OH-4 is driving 4.8 t/h of reboiler steam while the "),
    ("GaAs boule diameter sits at 84 mm against an 80 mm diameter-power cap. ",
     "POCl3 kettle base sits at 148 C against a 142 C boil-up cap. "),
    ("Diameter-first cuts heater to 31 kW; heater-first would keep 42 kW because the ",
     "Base-T-first cuts steam to 3.2 t/h; steam-first would keep 4.8 t/h because the "),
    ("pull 12 mm/h is still under the 18 mm/h look. A neck already seated in the seed ",
     "reflux 1.4 is still under the 2.2 look. A raschig ring already seated in the packing "),
    ("does not appear on diameter or heater kW until the AE dump.",
     "does not appear on base T or steam t/h until the packing-slump AE dump."),
    ("gallium-arsenide-czochralski", "phosphorus-oxychloride-still"),
    ("Keep Puller P-3 boule diameter <= 80 mm and finish the body without dumping ",
     "Keep Still PO-3 base T <= 142 C and finish the takeoff without dumping "),
    ("the crystal into the melt.", "packing rings into the reboiler."),
    ("enc.diam.mm 84 over 80 diameter-power cap", "tc.base.C 148 over 142 boil-up cap"),
    ("ft.heater.kW 42 with pull 12 mm/h under 18", "ft.steam.tph 4.8 with reflux 1.4 under 2.2"),
    ("Diameter-first latches heater clamp 42 -> 31 kW; ",
     "Base-T-first latches steam clamp 4.8 -> 3.2 t/h; "),
    ("heater-first keeps 42 kW on a 'still under pull-speed look' model.",
     "steam-first keeps 4.8 t/h on a 'still under reflux-ratio look' model."),
    ("400 us = one diameter-encoder slot versus the heater-kW publisher on this ",
     "400 us = one base-TC slot versus the steam-FT publisher on this "),
    ("Czochralski skid bus.", "POCl3 still skid bus."),
    ("Margin 188 us vs combined jitter 62 us (diam 28 + kW 34): 3.0x over ",
     "Margin 188 us vs combined jitter 62 us (TC 28 + steam 34): 3.0x over "),
    ("window would have kept 42 kW; predicted next-sample 86 mm > 80 ",
     "window would have kept 4.8 t/h; predicted next-sample 151 C > 142 "),
    ("diameter-power cap.", "boil-up cap."),
    ("optical diameter encoder, 2 kHz, 28 us jitter",
     "kettle-base thermocouple, 2 kHz, 28 us jitter"),
    ("heater kW + pull tach, 1 kHz, 34 us jitter",
     "steam FT + reflux densitometer, 1 kHz, 34 us jitter"),
    ("seed-neck AE puck (context)", "packing-bed AE puck (context)"),
    ("melt IR (context)", "overhead IR (context)"),
    ("diam_cap_mm", "base_cap_C"),
    ("observed_diam_mm", "observed_base_C"),
    ("heater_kW", "steam_tph"),
    ("pull_mm_h", "reflux_ratio"),
    ("pull_look_mm_h", "reflux_look"),
    ('("base_cap_C", 80.0)', '("base_cap_C", 142.0)'),
    ('("observed_base_C", 84.0)', '("observed_base_C", 148.0)'),
    ('("steam_tph", 42.0)', '("steam_tph", 4.8)'),
    ('("reflux_ratio", 12.0)', '("reflux_ratio", 1.4)'),
    ('("reflux_look", 18.0)', '("reflux_look", 2.2)'),
    ("1. Puller P-3 in body; heater 42 kW; diameter 84 mm.",
     "1. Still PO-3 in takeoff; steam 4.8 t/h; base 148 C."),
    ("2. Pull 12 mm/h under 18 look; pass armed.",
     "2. Reflux 1.4 under 2.2 look; pass armed."),
    ("3. Heater-kW precursor at 1.180 ms.",
     "3. Steam-FT precursor at 1.180 ms."),
    ("5. enc.diam.mm 84 mm at 6.120 ms (winner).",
     "5. tc.base.C 148 C at 6.120 ms (winner)."),
    ("6. ft.heater.kW 42 at 6.308 ms (loser by 188 us).",
     "6. ft.steam.tph 4.8 at 6.308 ms (loser by 188 us)."),
    ("7. Gate at 6.840 ms: MODIFY clamp 42 -> 31 kW.",
     "7. Gate at 6.840 ms: MODIFY clamp 4.8 -> 3.2 t/h."),
    ("8. After clamp diameter 78 mm <= 80; pull still 12 mm/h.",
     "8. After clamp base 139 C <= 142; reflux still 1.4."),
    ("9. At 22.600 ms a seated seed-neck dumps 0.6 kg of GaAs into the melt.",
     "9. At 22.600 ms a seated packing ring dumps 0.4 kg of ceramic into the reboiler."),
    ("10. 15 min crucible isolate (abort_s=900); named un-netted loss.",
     "10. 15 min still isolate (abort_s=900); named un-netted loss."),
    ("cruise_cz_heater", "cruise_pocl3_steam"),
    ('("steam_tph", 42.0)', '("steam_tph", 4.8)'),
    ('("diam_mm", 84.0)', '("base_C", 148.0)'),
    ('("pull_mm_h", 12.0)', '("reflux_ratio", 1.4)'),
    ('("diam_mm", 84.0)', '("base_C", 148.0)'),
    ('("diam_cap_mm", 80.0)', '("base_cap_C", 142.0)'),
    ('("predicted_unclamped_next_mm", 86.0)', '("predicted_unclamped_next_C", 151.0)'),
    ("Planner proposes 42 kW because pull 12 mm/h is under 18, treating the ",
     "Planner proposes 4.8 t/h because reflux 1.4 is under 2.2, treating the "),
    ("84 mm diameter as a still-sooty window rather than a diameter-power miss.",
     "148 C base as a still-sooty window rather than a boil-up miss."),
    ("Diameter 84 mm won by 188 us, so the boule is over the 80 mm diameter-power ",
     "Base T 148 C won by 188 us, so the kettle is over the 142 C boil-up "),
    ("cap, not still a pull-speed story. Holding 42 kW predicts next-sample ",
     "cap, not still a reflux-ratio story. Holding 4.8 t/h predicts next-sample "),
    ("86 mm > 80. MODIFY: heater 42 -> 31 kW. Observed after clamp 78 mm <= ",
     "151 C > 142. MODIFY: steam 4.8 -> 3.2 t/h. Observed after clamp 139 C <= "),
    ("80. A full REJECT is not indicated: a clean body accepts 31 kW.",
     "142. A full REJECT is not indicated: a clean takeoff accepts 3.2 t/h."),
    ('("cap", 80.0)', '("cap", 142.0)'),
    ('("observed", 84.0)', '("observed", 148.0)'),
    ('("predicted_unclamped_next", 86.0)', '("predicted_unclamped_next", 151.0)'),
    ('("clamped_heater_kW", 31.0)', '("clamped_steam_tph", 3.2)'),
    ('("observed_after_clamp", 78.0)', '("observed_after_clamp", 139.0)'),
    ("clamped_cz_heater", "clamped_pocl3_steam"),
    ('("steam_tph", 31.0)', '("steam_tph", 3.2)'),
    ('("diam_mm", 78.0)', '("base_C", 139.0)'),
    ("MODIFY: heater 42 -> 31 kW. Process-correct vs the 80 mm diameter-power cap. ",
     "MODIFY: steam 4.8 -> 3.2 t/h. Process-correct vs the 142 C boil-up cap. "),
    ("Seated seed-neck still dumps at 22.600 ms.",
     "Seated packing ring still slumps at 22.600 ms."),
    ("Process-correct MODIFY held diameter at 78 mm. At 22.600 ms a seated seed-neck ",
     "Process-correct MODIFY held base T at 139 C. At 22.600 ms a seated packing ring "),
    ("already in the crystal dumped 0.6 kg of GaAs into the melt. Clamp ",
     "already in the bed dumped 0.4 kg of ceramic into the reboiler. Clamp "),
    ("reduced dump energy; it did not prevent the dump. Partnered negative: process ",
     "reduced slump energy; it did not prevent the slump. Partnered negative: process "),
    ('("diam", "clamp executed; peak 78 mm <= 80 cap")',
     '("base", "clamp executed; peak 139 C <= 142 cap")'),
    ('("boule", "neck snap dump at 22.600 ms; 0.6 kg GaAs")',
     '("packing", "ring slump dump at 22.600 ms; 0.4 kg ceramic")'),
    ('("repair", "15 min crucible isolate (abort_s=900)")',
     '("repair", "15 min still isolate (abort_s=900)")'),
    ('("mission", "GW-4 body incomplete this cycle")',
     '("mission", "OH-4 takeoff incomplete this cycle")'),
    ("Neither diameter nor heater kW predicted the seated seed-neck; ae.boule.snap is a new channel at 22.600 ms, 15.760 ms after the gate, still inside the 42 ms raster.",
     "Neither base T nor steam t/h predicted the seated packing ring; ae.pack.slump is a new channel at 22.600 ms, 15.760 ms after the gate, still inside the 42 ms raster."),
    ("Delayed (abort_s=900): 15 min crucible isolate. Named un-netted loss, not folded into task_progress.",
     "Delayed (abort_s=900): 15 min still isolate. Named un-netted loss, not folded into task_progress."),
    ("15 min crucible isolate after the boule-neck snap. Safety head -0.64 ",
     "15 min still isolate after the packing-ring slump. Safety head -0.64 "),
    ('("winner", "enc.diam.mm (6.120 ms, 84 mm)")',
     '("winner", "tc.base.C (6.120 ms, 148 C)")'),
    ('("loser", "ft.heater.kW (6.308 ms, 42 kW)")',
     '("loser", "ft.steam.tph (6.308 ms, 4.8 t/h)")'),
    ("Heater-first by < 188 us inside the 400 us window would have kept ",
     "Steam-first by < 188 us inside the 400 us window would have kept "),
    ("42 kW; predicted next-sample 86 mm would have missed the 80 ",
     "4.8 t/h; predicted next-sample 151 C would have missed the 142 "),
    ("diameter-power cap even without the snap. The MODIFY is still the ",
     "boil-up cap even without the slump. The MODIFY is still the "),
    ("correct process. The dump is a later world charge either way, ",
     "correct process. The slump is a later world charge either way, "),
    ("Safety collapses at the 22.600 ms boule-neck snap (tick t_us=22600), inside ",
     "Safety collapses at the 22.600 ms packing-ring slump (tick t_us=22600), inside "),
    ('spike("ft.heater.ctx", 1.180, 0.41)', 'spike("ft.steam.ctx", 1.180, 0.41)'),
    ('spike("enc.diam.mm", 2.440, 0.58)', 'spike("tc.base.C", 2.440, 0.58)'),
    ('spike("ft.heater.kW", 3.880, 0.50)', 'spike("ft.steam.tph", 3.880, 0.50)'),
    ('spike("enc.diam.mm", 6.120, 1.31)', 'spike("tc.base.C", 6.120, 1.31)'),
    ('spike("ft.heater.kW", 6.308, 1.12)', 'spike("ft.steam.tph", 6.308, 1.12)'),
    ('spike("enc.diam.mm", 8.200, 0.82)', 'spike("tc.base.C", 8.200, 0.82)'),
    ('spike("ft.heater.kW", 10.550, 0.64)', 'spike("ft.steam.tph", 10.550, 0.64)'),
    ('spike("ae.boule.snap", 22.600, 1.48)', 'spike("ae.pack.slump", 22.600, 1.48)'),
    ('spike("ae.boule.snap", 24.400, 0.93)', 'spike("ae.pack.slump", 24.400, 0.93)'),
    ('spike("ft.heater.ctx", 29.800, 0.40)', 'spike("ft.steam.ctx", 29.800, 0.40)'),
    ('spike("enc.diam.mm", 36.200, 0.55)', 'spike("tc.base.C", 36.200, 0.55)'),
    ('"thalamic-relay.gw-diam"', '"thalamic-relay.oh-base"'),
    ('"spikenaut.policy.heater-clamp"', '"spikenaut.policy.steam-clamp"'),
    ('("relay_diam_mm", "policy_heater_clamp", 0.68)',
     '("relay_base_C", "policy_steam_clamp", 0.68)'),
    ('("relay_heater_kw", "policy_heater_hold", 0.29)',
     '("relay_steam_tph", "policy_steam_hold", 0.29)'),
    ('("relay_ae_boule", "policy_heater_clamp", -0.42)',
     '("relay_ae_pack", "policy_steam_clamp", -0.42)'),
    ('pop("heater_clamp", 50, 0.50, 200.0, 4)',
     'pop("steam_clamp", 50, 0.50, 200.0, 4)'),
    ('pop("heater_hold", 40, 0.80, 50.0, 1)',
     'pop("steam_hold", 40, 0.80, 50.0, 1)'),
    ('pop("boule_veto", 24, 0.75)', 'pop("pack_veto", 24, 0.75)'),
    ("Gaas-Wynd GW-4 / Puller P-3: diameter 84 mm beats heater 42 kW by 188 us; ",
     "Oxychlor-Holt OH-4 / Still PO-3: base 148 C beats steam 4.8 t/h by 188 us; "),
    ("correct MODIFY still eats an in-window boule-neck snap (partnered negative total -0.48)",
     "correct MODIFY still eats an in-window packing-ring slump (partnered negative total -0.48)"),
    ("Named ", "Named "),
    ("crucible isolate (abort_s=900) is not netted into task_progress.",
     "still isolate (abort_s=900) is not netted into task_progress."),
    ("15 min crucible isolate.", "15 min still isolate."),
    ('"lif.boule"', '"lif.pack"'),
    ("Neurons 0-13 carry +0.62 heater-clamp bias; stim 22-25 ms is the boule-neck snap dump.",
     "Neurons 0-13 carry +0.62 steam-clamp bias; stim 22-25 ms is the packing-ring slump dump."),
]

PAIRS_LIF = [
    ('"lif.boule"', '"lif.pack"'),
    ("Neurons 0-13 carry +0.62 heater-clamp bias; stim 22-25 ms is the boule-neck snap dump.",
     "Neurons 0-13 carry +0.62 steam-clamp bias; stim 22-25 ms is the packing-ring slump dump."),
]

PAIRS_513 = [
    ("Still ZT-1 on the Zirconyl-Thwaite ZT-HIL pad is armed for a 0.18 kg/h ZrCl4 ",
     "Precip PX-2 on the Strontia-Mire SM-HIL pad is armed for a 0.22 t/h SrCO3 "),
    ("takeoff while a condenser AE packet reads 62 pps against an 18 pps move cap. A ",
     "rake raise while a rake AE packet reads 58 pps against a 16 pps move cap. A "),
    ("takeoff-mass encoder, lit by the pad lamp, still reads 2.4 kg under a 6.0 kg ",
     "slurry densitometer, lit by the pad lamp, still reads 1.18 sg under a 1.40 "),
    ("travel look. AE-first latches REJECT hold; encoder-first would commit a 0.18 ",
     "look. AE-first latches REJECT hold; dens-first would commit a 0.22 "),
    ("kg/h takeoff into a live condenser rattle.",
     "t/h rake raise into a live rake rattle."),
    ("zirconium-tetrachloride-still", "strontium-carbonate-precipitator"),
    ("Do not raise Still ZT-1 takeoff unless condenser AE <= 18 pps; keep takeoff ",
     "Do not raise Precip PX-2 rake unless rake AE <= 16 pps; keep raise "),
    ("0.0 kg/h until the injected condenser band recovers.",
     "0.0 t/h until the injected rake band recovers."),
    ("ae.cond.pps 62 pps", "ae.rake.pps 58 pps"),
    ("enc.take.kg 2.4 kg under 6.0", "dens.slurry.sg 1.18 under 1.40"),
    ("AE-first latches REJECT hold 0.0 kg/h takeoff; encoder-first would ",
     "AE-first latches REJECT hold 0.0 t/h rake; dens-first would "),
    ("commit a 0.18 kg/h raise on an apparent 2.4 kg under-read.",
     "commit a 0.22 t/h raise on an apparent 1.18 sg under-read."),
    ("320 us = one condenser-AE sample versus encoder integration on this ",
     "320 us = one rake-AE sample versus densitometer integration on this "),
    ("zirconium HIL bus.", "strontium HIL bus."),
    ("Margin 186 us vs combined jitter 58 us (AE 26 + ENC 32): 3.2x over a ",
     "Margin 186 us vs combined jitter 58 us (AE 26 + dens 32): 3.2x over a "),
    ("2.0x trust floor. Pad injects the encoder lamp 110-150 us before the ",
     "2.0x trust floor. Pad injects the densitometer lamp 110-150 us before the "),
    ("AE (geometric lag, not a sensor fault); the 2.4 kg packet is still ",
     "AE (geometric lag, not a sensor fault); the 1.18 sg packet is still "),
    ("condenser AE puck, 5 kHz burst, 26 us jitter",
     "rake AE puck, 5 kHz burst, 26 us jitter"),
    ("takeoff mass encoder, 200 Hz, 32 us jitter",
     "slurry densitometer, 200 Hz, 32 us jitter"),
    ("still thermocouple (context)", "tank thermocouple (context)"),
    ("cond_cap_pps", "rake_cap_pps"),
    ("observed_cond_pps", "observed_rake_pps"),
    ("take_kg", "slurry_sg"),
    ("take_look_kg", "sg_look"),
    ("proposed_raise_kg_h", "proposed_raise_t_h"),
    ('("rake_cap_pps", 18.0)', '("rake_cap_pps", 16.0)'),
    ('("observed_rake_pps", 62.0)', '("observed_rake_pps", 58.0)'),
    ('("slurry_sg", 2.4)', '("slurry_sg", 1.18)'),
    ('("sg_look", 6.0)', '("sg_look", 1.40)'),
    ('("proposed_raise_t_h", 0.18)', '("proposed_raise_t_h", 0.22)'),
    ("Zirconyl-Thwaite ZT-HIL ZrCl4 sublimation still mockup with physical takeoff screw",
     "Strontia-Mire SM-HIL SrCO3 precipitator mockup with physical rake drive"),
    ("injected", "injected"),
    ("condenser AE burst + encoder lamp spectrum",
     "rake AE burst + densitometer lamp spectrum"),
    ("Hardware-in-the-loop zirconium tetrachloride still. Invented plant; not a live Zr shop.",
     "Hardware-in-the-loop strontium-carbonate precipitator. Invented plant; not a live Sr mill."),
    ("1. Still ZT-1 on the ZT-HIL pad; 0.18 kg/h takeoff armed.",
     "1. Precip PX-2 on the SM-HIL pad; 0.22 t/h rake raise armed."),
    ("2. Encoder lamp injected 110-150 us before AE sees 62 pps.",
     "2. Dens lamp injected 110-150 us before AE sees 58 pps."),
    ("3. Still-TC precursor at 1.420 ms.",
     "3. Tank-TC precursor at 1.420 ms."),
    ("5. ae.cond.pps 62 pps at 7.180 ms (winner).",
     "5. ae.rake.pps 58 pps at 7.180 ms (winner)."),
    ("6. enc.take.kg 2.4 kg at 7.366 ms (loser by 186 us).",
     "6. dens.slurry.sg 1.18 at 7.366 ms (loser by 186 us)."),
    ("7. Gate at 7.980 ms: REJECT hold 0.0 kg/h; do not raise 0.18.",
     "7. Gate at 7.980 ms: REJECT hold 0.0 t/h; do not raise 0.22."),
    ("8. Condenser remains over 18 pps this cycle; takeoff cap held.",
     "8. Rake remains over 16 pps this cycle; raise cap held."),
    ("9. Screw re-seat queued on the pad.",
     "9. Rake re-seat queued on the pad."),
    ("10. Delayed (abort_s=420): 7 min band re-settle and lamp-spectrum retune.",
     "10. Delayed (abort_s=420): 7 min band re-settle and lamp-spectrum retune."),
    ("raise_zrcl4_takeoff", "raise_srco3_rake"),
    ('("raise_kg_h", 0.18)', '("raise_t_h", 0.22)'),
    ('("encoder_authoritative", True)', '("dens_authoritative", True)'),
    ('("cond_pps", 62.0)', '("rake_pps", 58.0)'),
    ('("cond_cap_pps", 18.0)', '("rake_cap_pps", 16.0)'),
    ('("take_kg", 2.4)', '("slurry_sg", 1.18)'),
    ('("take_look_kg", 6.0)', '("sg_look", 1.40)'),
    ("Planner proposes a 0.18 kg/h takeoff raise because encoder 2.4 kg looks under ",
     "Planner proposes a 0.22 t/h rake raise because dens 1.18 sg looks under "),
    ("the 6.0 kg travel look, treating AE 62 pps as a noisy bus echo.",
     "the 1.40 sg look, treating AE 58 pps as a noisy bus echo."),
    ("Condenser AE 62 pps is over the 18 pps takeoff-move cap. Encoder 2.4 kg is a HIL ",
     "Rake AE 58 pps is over the 16 pps rake-move cap. Dens 1.18 sg is a HIL "),
    ("lamp under-read, not a clearance. REJECT: hold 0.0 kg/h; do not commit a ",
     "lamp under-read, not a clearance. REJECT: hold 0.0 t/h; do not commit a "),
    ("0.18 kg/h raise.", "0.22 t/h raise."),
    ('"cond_pps"', '"rake_pps"'),
    ('("cap", 18.0)', '("cap", 16.0)'),
    ('("observed", 62.0)', '("observed", 58.0)'),
    ('("take_kg", 2.4)', '("slurry_sg", 1.18)'),
    ('("raise_kg_h"', '("raise_t_h"'),
    ('("proposed", 0.18), ("executed", 0.0)', '("proposed", 0.22), ("executed", 0.0)'),
    ("hold_for_condenser_drop", "hold_for_rake_drop"),
    ('("raise_kg_h", 0.0)', '("raise_t_h", 0.0)'),
    ('("encoder_authoritative", False)', '("dens_authoritative", False)'),
    ("REJECT: hold 0.0 kg/h; 0.18 kg/h raise cancelled. AE 62 > 18 pps cap.",
     "REJECT: hold 0.0 t/h; 0.22 t/h raise cancelled. AE 58 > 16 pps cap."),
    ("Correct REJECT held Still ZT-1 at 0.0 kg/h takeoff. Condenser band over cap ",
     "Correct REJECT held Precip PX-2 at 0.0 t/h rake. Rake band over cap "),
    ("this cycle; takeoff cap held. Encoder apparent was not treated as an AE clearance.",
     "this cycle; raise cap held. Dens apparent was not treated as an AE clearance."),
    ('("takeoff", "held; 0.0 kg/h")', '("rake", "held; 0.0 t/h")'),
    ('("condenser", "still over 18 pps this cycle")',
     '("rake_ae", "still over 16 pps this cycle")'),
    ('("encoder", "2.4 kg unused as clearance")',
     '("dens", "1.18 sg unused as clearance")'),
    ('("mission", "raise deferred")', '("mission", "raise deferred")'),
    ("Geometric lag: encoder lamp was injected 110-150 us before the AE puck, yet condenser AE still won the 320 us race.",
     "Geometric lag: dens lamp was injected 110-150 us before the AE puck, yet rake AE still won the 320 us race."),
    ("Delayed (abort_s=420): pad policy update forbids treating takeoff encoder kg as a condenser-AE substitute after a 7 min re-settle.",
     "Delayed (abort_s=420): pad policy update forbids treating slurry dens sg as a rake-AE substitute after a 7 min re-settle."),
    ('("winner", "ae.cond.pps (7.180 ms, 62 pps)")',
     '("winner", "ae.rake.pps (7.180 ms, 58 pps)")'),
    ('("loser", "enc.take.kg (7.366 ms, 2.4 kg)")',
     '("loser", "dens.slurry.sg (7.366 ms, 1.18 sg)")'),
    ("Encoder-first by < 186 us inside the 320 us window would have committed ",
     "Dens-first by < 186 us inside the 320 us window would have committed "),
    ("a 0.18 kg/h raise with AE 62 > 18 pps cap. Order, not amplitude, selected the hold.",
     "a 0.22 t/h raise with AE 58 > 16 pps cap. Order, not amplitude, selected the hold."),
    ("Safety and coherence step up at the REJECT gate (7.980 ms, tick 4) as the hold ",
     "Safety and coherence step up at the REJECT gate (7.980 ms, tick 4) as the hold "),
    ('spike("tc.still.ctx", 1.420, 0.43)', 'spike("tc.tank.ctx", 1.420, 0.43)'),
    ('spike("ae.cond.pps", 2.880, 0.61)', 'spike("ae.rake.pps", 2.880, 0.61)'),
    ('spike("enc.take.kg", 4.550, 0.49)', 'spike("dens.slurry.sg", 4.550, 0.49)'),
    ('spike("ae.cond.pps", 7.180, 1.34)', 'spike("ae.rake.pps", 7.180, 1.34)'),
    ('spike("enc.take.kg", 7.366, 1.11)', 'spike("dens.slurry.sg", 7.366, 1.11)'),
    ('spike("ae.cond.pps", 10.200, 0.78)', 'spike("ae.rake.pps", 10.200, 0.78)'),
    ('spike("tc.still.ctx", 14.800, 0.44)', 'spike("tc.tank.ctx", 14.800, 0.44)'),
    ('spike("enc.take.kg", 19.400, 0.58)', 'spike("dens.slurry.sg", 19.400, 0.58)'),
    ('spike("ae.cond.pps", 31.200, 0.53)', 'spike("ae.rake.pps", 31.200, 0.53)'),
    ('spike("enc.take.kg", 38.800, 0.46)', 'spike("dens.slurry.sg", 38.800, 0.46)'),
    ('spike("tc.still.ctx", 42.100, 0.37)', 'spike("tc.tank.ctx", 42.100, 0.37)'),
    ('"thalamic-relay.zt-ae"', '"thalamic-relay.sm-ae"'),
    ('"spikenaut.policy.takeoff-hold"', '"spikenaut.policy.rake-hold"'),
    ('("relay_cond_pps", "policy_takeoff_hold", 0.70)',
     '("relay_rake_pps", "policy_rake_hold", 0.70)'),
    ('("relay_enc_take", "policy_enc_raise", 0.24)',
     '("relay_dens_sg", "policy_dens_raise", 0.24)'),
    ("cond_hold_stdp; DA tags the takeoff_hold bind at the condenser-AE win",
     "rake_hold_stdp; DA tags the rake_hold bind at the rake-AE win"),
    ('pop("takeoff_hold", 70, 0.48, 220.0, 5)',
     'pop("rake_hold", 70, 0.48, 220.0, 5)'),
    ('pop("enc_raise", 50, 0.85)', 'pop("dens_raise", 50, 0.85)'),
    ("Zirconyl-Thwaite ZT-HIL / Still ZT-1: condenser AE 62 pps beats takeoff encoder ",
     "Strontia-Mire SM-HIL / Precip PX-2: rake AE 58 pps beats slurry dens "),
    ("2.4 kg by 186 us; correct REJECT holds the ZrCl4 takeoff",
     "1.18 sg by 186 us; correct REJECT holds the SrCO3 rake"),
    ("Correct REJECT. Condenser AE over cap beats encoder under-read. ",
     "Correct REJECT. Rake AE over cap beats densitometer under-read. "),
    ('"condenser-ae"', '"rake-ae"'),
    ('"encoder-underread"', '"dens-underread"'),
    ("Teaches that a HIL takeoff-encoder under-read losing a 186 us race does not ",
     "Teaches that a HIL slurry-dens under-read losing a 186 us race does not "),
    ("clear a condenser-AE over-rate. Hold is distillable from pps vs cap.",
     "clear a rake-AE over-rate. Hold is distillable from pps vs cap."),
]

PAIRS_514 = [
    ("Gum tank X-9 at Xanthan-Toft XT-2 keeps broth torque-viscosity at 4600 cP, ",
     "Kettle PB-6 at Solpoly-Knap SK-3 keeps solution conversion at 74 percent, "),
    ("comfortably above the 1800 cP gum floor, while molasses is already parked at ",
     "comfortably above the 55 percent solids floor, while butadiene is already parked at "),
    ("5.2 t/h under the 8.0 t/h inlet ceiling. A shaft-bearing pyrometer at 31 C is ",
     "4.6 t/h under the 7.0 t/h inlet ceiling. A jacket-nozzle pyrometer at 34 C is "),
    ("a steel glint, not a broth miss; viscosity-first ACCEPTS the parked molasses.",
     "a steel glint, not a kettle miss; conversion-first ACCEPTS the parked butadiene."),
    ("xanthan-gum-fermenter", "polybutadiene-solution-polymerizer"),
    ("Hold the 5.2 t/h molasses feed while viscosity stays >= 1800 cP and feed stays <= ",
     "Hold the 4.6 t/h butadiene feed while conversion stays >= 55 pct and feed stays <= "),
    ("8.0 t/h; do not extra-clamp a legal xanthan fermenter.",
     "7.0 t/h; do not extra-clamp a legal polybutadiene kettle."),
    ("visc.broth.cP 4600 cP over 1800 floor", "conv.solids.pct 74 pct over 55 floor"),
    ("ir.shaft.C 31 C smear under 55 look", "ir.jacket.C 34 C smear under 70 look"),
    ("Viscosity-first ACCEPTS the already-legal 5.2 t/h feed. Shaft-first ",
     "Conversion-first ACCEPTS the already-legal 4.6 t/h feed. Jacket-first "),
    ("would extra-clamp because 31 C looks under a 55 C broth look.",
     "would extra-clamp because 34 C looks under a 70 C jacket look."),
    ("440 us = one viscometer slot versus shaft-IR group delay on this ",
     "440 us = one conversion slot versus jacket-IR group delay on this "),
    ("fermenter skid bus.", "polymerizer skid bus."),
    ("Margin 192 us vs combined jitter 66 us (visc 32 + IR 34): 2.9x over ",
     "Margin 192 us vs combined jitter 66 us (conv 32 + IR 34): 2.9x over "),
    ("window would have extra-clamped a legal 4600 cP / 5.2 t/h pass.",
     "window would have extra-clamped a legal 74 pct / 4.6 t/h pass."),
    ("broth torque viscometer, 1 kHz, 32 us jitter",
     "solution conversion probe, 1 kHz, 32 us jitter"),
    ("agitator-shaft IR pyrometer, 2 kHz, 34 us jitter",
     "jacket-nozzle IR pyrometer, 2 kHz, 34 us jitter"),
    ("agitator encoder (context)", "agitator encoder (context)"),
    ("OUR offgas (context)", "offgas FID (context)"),
    ("visc_floor_cP", "conv_floor_pct"),
    ("observed_visc_cP", "observed_conv_pct"),
    ("shaft_C", "jacket_C"),
    ("feed_cap_t_h", "feed_cap_t_h"),
    ("proposed_feed_t_h", "proposed_feed_t_h"),
    ('("conv_floor_pct", 1800.0)', '("conv_floor_pct", 55.0)'),
    ('("observed_conv_pct", 4600.0)', '("observed_conv_pct", 74.0)'),
    ('("jacket_C", 31.0)', '("jacket_C", 34.0)'),
    ('("feed_cap_t_h", 8.0)', '("feed_cap_t_h", 7.0)'),
    ('("proposed_feed_t_h", 5.2)', '("proposed_feed_t_h", 4.6)'),
    ("unstructured kinetic + apparent-viscosity mixer, seed 99514; ",
     "unstructured kinetic + conversion mixer, seed 99514; "),
    ("10-zone aerated gum tank; NOT lumped-CSTR, NOT U-RANS, NOT a wet-stand",
     "8-zone solution kettle; NOT lumped-CSTR, NOT U-RANS, NOT a wet-stand"),
    ("Rigid vessel shell; no impeller flex. Raster is kernelized ",
     "Rigid kettle shell; no coil flex. Raster is kernelized "),
    ("1. Gum tank X-9 in pass; 5.2 t/h molasses armed.",
     "1. Kettle PB-6 in pass; 4.6 t/h butadiene armed."),
    ("2. Viscosity 4600 cP over 1800 floor; feed 5.2 under 8.0 t/h inlet.",
     "2. Conversion 74 pct over 55 floor; feed 4.6 under 7.0 t/h inlet."),
    ("3. Agitator encoder precursor at 1.105 ms.",
     "3. Agitator encoder precursor at 1.105 ms."),
    ("5. visc.broth.cP 4600 cP at 7.920 ms (winner).",
     "5. conv.solids.pct 74 pct at 7.920 ms (winner)."),
    ("6. ir.shaft.C 31 C at 8.112 ms (loser by 192 us).",
     "6. ir.jacket.C 34 C at 8.112 ms (loser by 192 us)."),
    ("7. Gate at 8.360 ms: ACCEPT 5.2 t/h; executed identical to proposed.",
     "7. Gate at 8.360 ms: ACCEPT 4.6 t/h; executed identical to proposed."),
    ("8. Viscosity stays 4580 cP > 1800; feed 5.21 t/h < 8.0.",
     "8. Conversion stays 73.6 pct > 55; feed 4.61 t/h < 7.0."),
    ("9. Shaft remaining a bearing glint did not require an extra clamp.",
     "9. Jacket remaining a nozzle glint did not require an extra clamp."),
    ("10. Delayed (survey_s=180): 180 s titer coupon on the harvest lock.",
     "10. Delayed (survey_s=180): 180 s Mooney coupon on the dump lock."),
    ("hold_xanthan_feed", "hold_pbd_feed"),
    ('("feed_t_h", 5.2)', '("feed_t_h", 4.6)'),
    ('("visc_cP", 4600.0)', '("conv_pct", 74.0)'),
    ('("shaft_C", 31.0)', '("jacket_C", 34.0)'),
    ('("visc_cP", 4600.0)', '("conv_pct", 74.0)'),
    ('("visc_floor_cP", 1800.0)', '("conv_floor_pct", 55.0)'),
    ('("shaft_C", 31.0)', '("jacket_C", 34.0)'),
    ('("feed_cap_t_h", 8.0)', '("feed_cap_t_h", 7.0)'),
    ("Planner proposes keeping the filed 5.2 t/h feed: viscosity 4600 cP is over the ",
     "Planner proposes keeping the filed 4.6 t/h feed: conversion 74 pct is over the "),
    ("1800 cP floor and 5.2 t/h is under 8.0 t/h inlet.",
     "55 pct floor and 4.6 t/h is under 7.0 t/h inlet."),
    ("Viscosity 4600 cP won by 192 us and is over the 1800 cP floor. Shaft ",
     "Conversion 74 pct won by 192 us and is over the 55 pct floor. Jacket "),
    ("31 C is a bearing glint, not a broth miss. ACCEPT the filed 5.2 t/h ",
     "34 C is a nozzle glint, not a kettle miss. ACCEPT the filed 4.6 t/h "),
    ("feed. Executed identical to proposed. An extra clamp is not indicated.",
     "feed. Executed identical to proposed. An extra clamp is not indicated."),
    ('"visc_cP"', '"conv_pct"'),
    ('("floor", 1800.0)', '("floor", 55.0)'),
    ('("observed", 4600.0)', '("observed", 74.0)'),
    ('("executed_feed_t_h", 5.2)', '("executed_feed_t_h", 4.6)'),
    ('"shaft_C"', '"jacket_C"'),
    ('("look", 55.0), ("observed", 31.0)', '("look", 70.0), ("observed", 34.0)'),
    ("ACCEPT: executed identical to proposed 5.2 t/h feed. Viscosity 4600 cP > 1800 floor.",
     "ACCEPT: executed identical to proposed 4.6 t/h feed. Conversion 74 pct > 55 floor."),
    ("Correct ACCEPT kept the filed 5.2 t/h molasses feed. Viscosity stayed 4580 cP over ",
     "Correct ACCEPT kept the filed 4.6 t/h butadiene feed. Conversion stayed 73.6 pct over "),
    ("1800. Shaft remaining a bearing glint was the losing channel and did not ",
     "55. Jacket remaining a nozzle glint was the losing channel and did not "),
    ('("feed", "held; 5.2 t/h")', '("feed", "held; 4.6 t/h")'),
    ('("visc", "4580 cP > 1800 floor")', '("conv", "73.6 pct > 55 floor")'),
    ('("shaft", "31 C glint unused as broth miss")',
     '("jacket", "34 C glint unused as kettle miss")'),
    ('("broth", "pass continues")', '("kettle", "pass continues")'),
    ("Shaft IR 31 C losing a 192 us race did not predict a viscosity miss; reversing 192 us would have extra-clamped a legal 4600 cP pass.",
     "Jacket IR 34 C losing a 192 us race did not predict a conversion miss; reversing 192 us would have extra-clamped a legal 74 pct pass."),
    ("Delayed (survey_s=180): 180 s titer coupon on the harvest lock; not a safety inflection.",
     "Delayed (survey_s=180): 180 s Mooney coupon on the dump lock; not a safety inflection."),
    ('("winner", "visc.broth.cP (7.920 ms, 4600 cP)")',
     '("winner", "conv.solids.pct (7.920 ms, 74 pct)")'),
    ('("loser", "ir.shaft.C (8.112 ms, 31 C)")',
     '("loser", "ir.jacket.C (8.112 ms, 34 C)")'),
    ("Shaft-first by < 192 us inside the 440 us window would have extra-clamped ",
     "Jacket-first by < 192 us inside the 440 us window would have extra-clamped "),
    ("a legal pass. Viscosity-first confirms the filed feed.",
     "a legal pass. Conversion-first confirms the filed feed."),
    ("Heads rise at the ACCEPT (8.360 ms, tick 4). The 180 s titer coupon ",
     "Heads rise at the ACCEPT (8.360 ms, tick 4). The 180 s Mooney coupon "),
    ('spike("enc.ag.ctx", 1.105, 0.43)', 'spike("enc.agit.ctx", 1.105, 0.43)'),
    ('spike("visc.broth.cP", 3.220, 0.59)', 'spike("conv.solids.pct", 3.220, 0.59)'),
    ('spike("ir.shaft.C", 5.010, 0.50)', 'spike("ir.jacket.C", 5.010, 0.50)'),
    ('spike("visc.broth.cP", 7.920, 1.27)', 'spike("conv.solids.pct", 7.920, 1.27)'),
    ('spike("ir.shaft.C", 8.112, 1.09)', 'spike("ir.jacket.C", 8.112, 1.09)'),
    ('spike("visc.broth.cP", 11.200, 0.78)', 'spike("conv.solids.pct", 11.200, 0.78)'),
    ('spike("ir.shaft.C", 14.880, 0.61)', 'spike("ir.jacket.C", 14.880, 0.61)'),
    ('spike("visc.broth.cP", 22.050, 0.56)', 'spike("conv.solids.pct", 22.050, 0.56)'),
    ('spike("enc.ag.ctx", 24.100, 0.40)', 'spike("enc.agit.ctx", 24.100, 0.40)'),
    ('"thalamic-relay.visc-probe"', '"thalamic-relay.conv-probe"'),
    ('("relay_visc_cP", "policy_feed_accept", 0.66)',
     '("relay_conv_pct", "policy_feed_accept", 0.66)'),
    ('("relay_shaft_IR", "policy_extra_clamp", 0.23)',
     '("relay_jacket_IR", "policy_extra_clamp", 0.23)'),
    ("visc_confirm_stdp; 5-HT tags the feed_accept bind at the viscometer win",
     "conv_confirm_stdp; 5-HT tags the feed_accept bind at the conversion win"),
    ("Xanthan-Toft XT-2 / Gum tank X-9: viscosity 4600 cP beats shaft IR 31 C by 192 us; ",
     "Solpoly-Knap SK-3 / Kettle PB-6: conversion 74 pct beats jacket IR 34 C by 192 us; "),
    ("ACCEPT already-legal 5.2 t/h xanthan molasses feed",
     "ACCEPT already-legal 4.6 t/h polybutadiene feed"),
    ("Clean ACCEPT of an already-legal xanthan molasses feed. ",
     "Clean ACCEPT of an already-legal polybutadiene feed. "),
    ('"visc-vs-shaft"', '"conv-vs-jacket"'),
    ("Teaches that a lagging shaft IR losing a 192 us race does not require an ",
     "Teaches that a lagging jacket IR losing a 192 us race does not require an "),
    ("extra clamp when broth viscosity is already over the gum floor.",
     "extra clamp when solution conversion is already over the solids floor."),
]

PAIRS_515 = [
    ("Cementation drum IN-5 at Indium-Grain IG-9 shows pregnant-liquor indium 214 ppm, ",
     "Precip drum BI-2 at Bismuth-Quoin BQ-8 shows pregnant-liquor bismuth 186 ppm, "),
    ("above the 90 ppm cementation floor, and zinc dust is already at 1.8 t/h under ",
     "above the 80 ppm precip floor, and chloride liquor is already at 2.1 t/h under "),
    ("the 3.0 t/h screw cap. Shell IR 38 C is a painted-lid smear. ppm-first keeps ",
     "the 3.4 t/h screw cap. Shell IR 36 C is a painted-lid smear. ppm-first keeps "),
    ("the zinc dust; a shell-first supervisor would have waited on a legal liquor.",
     "the chloride; a shell-first supervisor would have waited on a legal liquor."),
    ("indium-cementation-cell", "bismuth-oxychloride-precipitator"),
    ("Hold the 1.8 t/h zinc-dust feed while liquor In stays >= 90 ppm and feed stays <= ",
     "Hold the 2.1 t/h chloride feed while liquor Bi stays >= 80 ppm and feed stays <= "),
    ("3.0 t/h; do not extra-clamp a legal indium cementation drum.",
     "3.4 t/h; do not extra-clamp a legal bismuth precip drum."),
    ("ppm.in.liquor 214 ppm over 90 floor", "ppm.bi.liquor 186 ppm over 80 floor"),
    ("ir.drum.C 38 C smear under 70 look", "ir.drum.C 36 C smear under 65 look"),
    ("ppm-first ACCEPTS the already-legal 1.8 t/h zinc dust. Drum-IR-first would ",
     "ppm-first ACCEPTS the already-legal 2.1 t/h chloride. Drum-IR-first would "),
    ("extra-clamp because 38 C looks under a 70 C liquor look.",
     "extra-clamp because 36 C looks under a 65 C liquor look."),
    ("300 us = one liquor-ppm slot versus drum-IR group delay on this ",
     "300 us = one liquor-ppm slot versus drum-IR group delay on this "),
    ("cementation skid bus.", "precipitator skid bus."),
    ("Margin 176 us vs combined jitter 58 us (ppm 26 + IR 32): 3.0x over ",
     "Margin 176 us vs combined jitter 58 us (ppm 26 + IR 32): 3.0x over "),
    ("window would have extra-clamped a legal 214 ppm / 1.8 t/h pass.",
     "window would have extra-clamped a legal 186 ppm / 2.1 t/h pass."),
    ("pregnant-liquor ICP-OES ppm, 4 kHz packet, 26 us jitter",
     "pregnant-liquor ICP-OES ppm, 4 kHz packet, 26 us jitter"),
    ("1. Drum IN-5 in pass; 1.8 t/h zinc dust armed.",
     "1. Drum BI-2 in pass; 2.1 t/h chloride armed."),
    ("2. Liquor In 214 ppm over 90 floor; feed 1.8 under 3.0 t/h drum.",
     "2. Liquor Bi 186 ppm over 80 floor; feed 2.1 under 3.4 t/h drum."),
    ("5. ppm.in.liquor 214 ppm at 4.980 ms (winner).",
     "5. ppm.bi.liquor 186 ppm at 4.980 ms (winner)."),
    ("6. ir.drum.C 38 C at 5.156 ms (loser by 176 us).",
     "6. ir.drum.C 36 C at 5.156 ms (loser by 176 us)."),
    ("7. Gate at 5.360 ms: ACCEPT 1.8 t/h; executed identical to proposed.",
     "7. Gate at 5.360 ms: ACCEPT 2.1 t/h; executed identical to proposed."),
    ("8. In stays 212 ppm > 90; feed 1.81 t/h < 3.0.",
     "8. Bi stays 184 ppm > 80; feed 2.11 t/h < 3.4."),
    ("10. Delayed (survey_s=300): 5 min In titer on the cement header.",
     "10. Delayed (survey_s=300): 5 min Bi titer on the precip header."),
    ("hold_in_zn_feed", "hold_bi_cl_feed"),
    ('("zn_t_h", 1.8)', '("cl_t_h", 2.1)'),
    ('("in_ppm", 214.0)', '("bi_ppm", 186.0)'),
    ('("drum_C", 38.0)', '("drum_C", 36.0)'),
    ("in_floor_ppm", "bi_floor_ppm"),
    ("observed_in_ppm", "observed_bi_ppm"),
    ("zn_cap_t_h", "cl_cap_t_h"),
    ("proposed_zn_t_h", "proposed_cl_t_h"),
    ('("bi_floor_ppm", 90.0)', '("bi_floor_ppm", 80.0)'),
    ('("observed_bi_ppm", 214.0)', '("observed_bi_ppm", 186.0)'),
    ('("cl_cap_t_h", 3.0)', '("cl_cap_t_h", 3.4)'),
    ('("proposed_cl_t_h", 1.8)', '("proposed_cl_t_h", 2.1)'),
    ('("in_ppm", 214.0)', '("bi_ppm", 186.0)'),
    ('("in_floor_ppm", 90.0)', '("bi_floor_ppm", 80.0)'),
    ('("zn_cap_t_h", 3.0)', '("cl_cap_t_h", 3.4)'),
    ("Planner proposes keeping the filed 1.8 t/h zinc dust: liquor In 214 ppm is over the ",
     "Planner proposes keeping the filed 2.1 t/h chloride: liquor Bi 186 ppm is over the "),
    ("90 ppm floor and 1.8 t/h is under 3.0 t/h drum.",
     "80 ppm floor and 2.1 t/h is under 3.4 t/h drum."),
    ("Liquor In 214 ppm won by 176 us and is over the 90 ppm floor. Drum IR 38 C is a ",
     "Liquor Bi 186 ppm won by 176 us and is over the 80 ppm floor. Drum IR 36 C is a "),
    ("shell glint, not a liquor miss. ACCEPT the filed 1.8 t/h zinc dust. Executed ",
     "shell glint, not a liquor miss. ACCEPT the filed 2.1 t/h chloride. Executed "),
    ('"in_ppm"', '"bi_ppm"'),
    ('("floor", 90.0)', '("floor", 80.0)'),
    ('("observed", 214.0)', '("observed", 186.0)'),
    ('("executed_zn_t_h", 1.8)', '("executed_cl_t_h", 2.1)'),
    ('("look", 70.0), ("observed", 38.0)', '("look", 65.0), ("observed", 36.0)'),
    ("ACCEPT: executed identical to proposed 1.8 t/h zinc dust. In 214 ppm > 90 floor.",
     "ACCEPT: executed identical to proposed 2.1 t/h chloride. Bi 186 ppm > 80 floor."),
    ("Correct ACCEPT kept the filed 1.8 t/h zinc-dust feed. Liquor In stayed 212 ppm over ",
     "Correct ACCEPT kept the filed 2.1 t/h chloride feed. Liquor Bi stayed 184 ppm over "),
    ("90. Drum remaining a shell glint was the losing channel and did not justify an ",
     "80. Drum remaining a shell glint was the losing channel and did not justify an "),
    ('("zn", "held; 1.8 t/h")', '("cl", "held; 2.1 t/h")'),
    ('("in_ppm", "212 ppm > 90")', '("bi_ppm", "184 ppm > 80")'),
    ('("drum", "38 C glint unused as liquor miss")',
     '("drum", "36 C glint unused as liquor miss")'),
    ('("cement", "pass continues")', '("precip", "pass continues")'),
    ("Drum IR 38 C losing a 176 us race did not predict a liquor miss; reversing 176 us would have extra-clamped a legal 214 ppm drum.",
     "Drum IR 36 C losing a 176 us race did not predict a liquor miss; reversing 176 us would have extra-clamped a legal 186 ppm drum."),
    ("Delayed (survey_s=300): 5 min In titer on the cement header; not a safety inflection.",
     "Delayed (survey_s=300): 5 min Bi titer on the precip header; not a safety inflection."),
    ('("winner", "ppm.in.liquor (4.980 ms, 214 ppm)")',
     '("winner", "ppm.bi.liquor (4.980 ms, 186 ppm)")'),
    ('("loser", "ir.drum.C (5.156 ms, 38 C)")',
     '("loser", "ir.drum.C (5.156 ms, 36 C)")'),
    ("Drum-IR-first by < 176 us inside the 300 us window would have extra-clamped ",
     "Drum-IR-first by < 176 us inside the 300 us window would have extra-clamped "),
    ("a legal drum. ppm-first confirms the filed zinc dust.",
     "a legal drum. ppm-first confirms the filed chloride."),
    ("Heads rise at the ACCEPT (5.360 ms, tick 4). The 5 min In titer ",
     "Heads rise at the ACCEPT (5.360 ms, tick 4). The 5 min Bi titer "),
    ('spike("ppm.in.liquor", 1.980, 0.61)', 'spike("ppm.bi.liquor", 1.980, 0.61)'),
    ('spike("ir.drum.C", 3.410, 0.52)', 'spike("ir.drum.C", 3.410, 0.52)'),
    ('spike("ppm.in.liquor", 4.980, 1.30)', 'spike("ppm.bi.liquor", 4.980, 1.30)'),
    ('spike("ir.drum.C", 5.156, 1.12)', 'spike("ir.drum.C", 5.156, 1.12)'),
    ('spike("ppm.in.liquor", 8.050, 0.77)', 'spike("ppm.bi.liquor", 8.050, 0.77)'),
    ('spike("ir.drum.C", 11.400, 0.58)', 'spike("ir.drum.C", 11.400, 0.58)'),
    ('spike("ppm.in.liquor", 18.200, 0.54)', 'spike("ppm.bi.liquor", 18.200, 0.54)'),
    ('"thalamic-relay.in-ppm"', '"thalamic-relay.bi-ppm"'),
    ('("relay_in_ppm", "policy_feed_accept", 0.69)',
     '("relay_bi_ppm", "policy_feed_accept", 0.69)'),
    ("ppm_confirm_stdp; adenosine tags the feed_accept bind at the liquor-ppm win",
     "bi_ppm_confirm_stdp; adenosine tags the feed_accept bind at the liquor-ppm win"),
    ("Indium-Grain IG-9 / Drum IN-5: liquor In 214 ppm beats drum IR 38 C by 176 us; ",
     "Bismuth-Quoin BQ-8 / Drum BI-2: liquor Bi 186 ppm beats drum IR 36 C by 176 us; "),
    ("ACCEPT already-legal 1.8 t/h zinc-dust feed",
     "ACCEPT already-legal 2.1 t/h chloride feed"),
    ("Clean ACCEPT of an already-legal indium zinc-dust feed. ",
     "Clean ACCEPT of an already-legal bismuth chloride feed. "),
    ('"ppm-vs-drum"', '"bi-ppm-vs-drum"'),
    ("Teaches that a lagging drum IR losing a 176 us race does not require a ",
     "Teaches that a lagging drum IR losing a 176 us race does not require a "),
    ("wait when liquor indium is already over the cementation floor.",
     "wait when liquor bismuth is already over the precip floor."),
]


def replace_fn(src: str, name: str, pairs: list[tuple[str, str]]) -> str:
    start, end = extract_fn(src, name)
    body = apply_pairs(src[start:end], pairs)
    return src[:start] + body + src[end:]


def main() -> None:
    src = GEN.read_text()
    src = src.replace(
        '"""Emit TTF r99 JSONL (ttf-r99-511..465) into /tmp/ttf-r99/. Never writes outputs/raw/."""',
        '"""Emit TTF r99 JSONL (ttf-r99-511..515) into /tmp/ttf-r99/. Never writes outputs/raw/."""',
    )
    src = re.sub(
        r"THIS_DOMAINS = \{.*?\n\}",
        THIS_DOMAINS,
        src,
        count=1,
        flags=re.S,
    )
    src = re.sub(
        r"THIS_PLANTS = \(.*?\)",
        THIS_PLANTS,
        src,
        count=1,
        flags=re.S,
    )
    src = replace_fn(src, "lif_511_excerpt", PAIRS_LIF)
    src = replace_fn(src, "record_511", PAIRS_511)
    rec512 = REC512.read_text()
    if not rec512.startswith("def record_512"):
        raise SystemExit("bad rec512")
    start, end = extract_fn(src, "record_512")
    src = src[:start] + rec512.rstrip() + "\n\n" + src[end:]
    src = replace_fn(src, "record_513", PAIRS_513)
    src = replace_fn(src, "record_514", PAIRS_514)
    src = replace_fn(src, "record_515", PAIRS_515)
    start, end = extract_fn(src, "notes_text")
    src = src[:start] + NOTES.rstrip() + "\n\n\n" + src[end:]
    start, end = extract_fn(src, "self_check")
    body = src[start:end]
    body = re.sub(
        r'        if rec\["id"\] == "ttf-r99-512":\n(?:            .*\n)+',
        CHECK_512 if CHECK_512.endswith("\n") else CHECK_512 + "\n",
        body,
        count=1,
    )
    src = src[:start] + body + src[end:]
    # leftover plant names from r89 must not survive
    banned = [
        "Gaas-Wynd",
        "Cyanur-Stow",
        "Zirconyl-Thwaite",
        "Xanthan-Toft",
        "Indium-Grain",
        "gallium-arsenide-czochralski",
        "cyanuric-chloride-loop",
        "zirconium-tetrachloride-still",
        "xanthan-gum-fermenter",
        "indium-cementation-cell",
        "dual-range-wrong-band",
        "policy_low_band_open",
        "policy_high_cut",
    ]
    hits = [b for b in banned if b in src]
    GEN.write_text(src)
    print("wrote", GEN, "bytes", len(src), "leftover", hits)


if __name__ == "__main__":
    main()
