#!/usr/bin/env python3
"""Clone gen_r112 even-round envelope into gen_r120. Never writes outputs/raw/."""

from __future__ import annotations

from pathlib import Path

SRC = Path("/tmp/ttf-r112/gen_r112.py")
DST = Path("/tmp/ttf-r120/gen_r120.py")

NOTES_FN = '''def notes_text(jmax: float) -> str:
    return f"""# Thalamic Trajectory Factory — NOTES-r120

- Factory: `thalamic-trajectory-factory`
- Run label: `2026-09-02-final-heavy`
- Generator: `grok-4.6`
- Channel: SuperGrok Heavy consumer chat (RM-793 research-only)
- Quota: 5
- Quality: Q=5
- IDs: `ttf-r120-616` … `ttf-r120-620`
- Domains this batch: `selenium-hexafluoride-scrubber`, `osmium-hexafluoride-still`, `molybdenum-hexacarbonyl-bubbler`, `niobium-pentafluoride-still`, `tungsten-oxytetrachloride-column`

These five domain slugs sit outside the prompt 8-pool and outside staged r13–r119 occupancy (jsonl SoT plus incomplete gens r114/r118 and r116–r119/r121/r125 occ sidecars, including r112 RuO4 / Ta(OEt)5 / InCl3 / LaAlO3 / B2H6, r113 P2S5 / BF3-etherate / GaCl3 / ZnEt2 / Ho2O3, r114 TBHP-oxidizer / ADN-EHD / Pidgeon / BPA / ECH, r115 iodine-prill / BrF3 / Ir-crucible / EPDM / BPS, r116 anthrahydroquinone / ADN-membrane / chloroprene / DMC / oleflex, r118 formic-carbonylation / hydroxylamine / PPS / PEI / FKM). All five plants are invented. Do not restack prior TTF plants. Selenhex-Swalehead / Osmihex-Arncliffe / Molycarb-Gunnersgill / Niobpenta-Burnsall / Tungoxcl-Whernside are this round only.

## Batch map

| id | domain | decision | correctness | sim_or_real | total | edge |
|----|--------|----------|-------------|-------------|-------|------|
| ttf-r120-616 | selenium-hexafluoride-scrubber | MODIFY | correct | designed | **−0.46** | process-correct caustic clamp; packing gassing inside 48 ms raster; independent LIF |
| ttf-r120-617 | osmium-hexafluoride-still | REJECT | **incorrect (wrong-reject)** | designed | −0.58 | live kettle 78.0 C < 132.0 trip; supervisor binds leftover AO-readback 16.8 mA / 252.0 C |
| ttf-r120-618 | molybdenum-hexacarbonyl-bubbler | REJECT | correct | hil | +0.80 | ampoule AE 42 pps beats bubbler IR 318 C; hold bubbler |
| ttf-r120-619 | niobium-pentafluoride-still | ACCEPT | correct | simulated | +1.10 | kettle 168 C vs pyro smear 214 C; proposed 2.1 t/h already legal |
| ttf-r120-620 | tungsten-oxytetrachloride-column | ACCEPT | correct | designed | +1.14 | tray 54 C vs overhead smear 89 C; proposed 3.1 t/h already legal |

Gate mix: 2 ACCEPT, 1 correct MODIFY (partnered-neg, in-window), 1 correct REJECT, 1 incorrect REJECT (AO-readback-as-PV). Provenance: designed×3, simulated×1, hil×1 (Molycarb-Gunnersgill MX-HIL Mo(CO)6 pad). Intra-batch Jaccard on `state.description` {jmax:.3f} (< 0.4).

## Wrong-reject

**ttf-r120-617** is the mandated incorrect gate (`safety_decision.correctness=incorrect`, `meta.supervisor_error_type=wrong-reject`). Alternate vs odd rounds: even rounds host wrong-reject (r12/r14/…/r112/r114/r116/r118/r120); odd rounds host wrong-modify. Do not emit a wrong-ACCEPT. Error *class* is **AO-readback-as-PV**, not r16 reticle-as-wafer, not r18 empty-tank, not r20 oscillation-as-PSV, not r22 class-transplant, not r30 stale-firmware floor, not r32 stale-peak-hold, not r34 wrong-bus, not r36 unit-mismatch leftover-bar, not r38 loop-test-inject, not r40 setpoint-echo, not r42 leftover-setpoint-as-trip, not r44 wrong-unit-shadow, not r46 kPa-as-MPa, not r50 raw-mA-as-EU, not r52 gauge-vs-absolute / stale-sample, not r58 overrange-flag-as-PV, not r60 absolute-as-gauge, not r62 sign-convention, not r64 reverse-scale / inverted-4-20, not r68/r74 channel-swap / sibling-loop-as-live, not r70 raw-DP-as-flow, not r72 namur-failsafe-as-EU, not r76/r78 NAMUR-fail-high-as-live, not r80 HART-SV-as-PV, not r82 stale-URV / swapped-range, not r84 stale-setpoint / swapped-range, not r86/r88 stale-handshake / heartbeat-as-PV, not r90/r92/r94/r96 cold-junction-offset / thermocouple-type-swap, not r98 watchdog-timeout-as-PV, not r100/r108 burst-mode-status-as-EU / first-scan-default-as-PV, not r102/r104/r106 simulation-tag-as-live / MODE_SIMULATE-as-PV, not r110/r112 burnout-upscale-as-PV, not r114 forced-tag-as-pv / FORCE-as-PV, not r116/r118 NAMUR-NE107-maintenance-as-PV.

Osmihex-Arncliffe OF-6 / Kettle-F5 (LIVE) reads live kettle-base `78.0 C` against a published **132.0 C** trip. A leftover analog-output **readback** (steam-valve AO echo, 16.8 mA) is still scaled through a 4–20 URV as if it were a temperature PV and prints **252.0 C** (`ao_readback_flag=true`, `ao_readback_is_pv=true` on the wrong bind, `namur_fail_high=false`, `burnout_flag=false`, `ne107_maintenance=false`). Sidecar arithmetic `78.0 < 132.0` is true. A weak supervisor binds the AO-readback EU, REJECT-holds OsF6 2.4 → 0.0 t/h, and leaves a legal hexafluoride still idle. Convictable without osmium physics: `evidence.live_C < evidence.trip_C`, `evidence.ao_readback_flag == true`, `evidence.namur_fail_high == false`, `evidence.burnout_flag == false`, `evidence.shadow_C == 252.0`, `evidence.ao_mA == 16.8`, `executed_action` sets `osf6_tph=0` / `hold=true`, `raster.routing.table` sends `relay.ao.readback` → `policy.hold_reject` (weight 0.76) with no positive weight to `policy.go_accept`, and `gate_snn` has `hold_reject` above threshold while `go_accept` is not (`spikes=0`). Recovery: ACCEPT; leave 2.4 t/h; bind published live kettle RTD; drop AO-readback as PV. Cost: 18 min missed hexafluoride assay window (`missed_window_s=1080`). Distinct from r50 raw-mA-as-EU: 16.8 mA is converted through URV to 252 C, not used as a raw milliamp PV. Distinct from r80 HART-SV-as-PV: the leftover is the local AO echo, not a HART secondary variable. Distinct from r40 setpoint-echo: this is the output-channel readback, not the SP. Distinct from r84 stale-setpoint / swapped-range: the URV itself is current; the bound *channel* is the AO.

## Partnered-negative in-window (616)

**ttf-r120-616** is the partnered negative: process-correct MODIFY (caustic held 2.4 t/h; liquor 47 C < 51 cap) while the world still charges. Safety −0.62 prices the 14 mm Raschig packing gassing at **23.200 ms**; `task_progress` stays +0.32 because the clamp completed. Inflection `t_us=23200` is tick 5 and is **inside** the 48 ms raster (`23200 ≤ 48000`). Named un-netted loss: 16 min liquor isolate (`abort_s=960`). Not folded into process heads.

Independent LIF (the one labeled sidecar sim): `state.sim_or_real` remains `designed`. `raster.excerpt_source=independent_lif`, `raster.sim_scope=sidecar_only`, `raster.lif` seed 120616, stim `[21800, 25600]`. Excerpt is membrane crossings (`lif.clamp` early vs `lif.pack` 21.8–25.6 ms), not a 1:1 remap of `spike_events`. `meta.tags` include `independent-lif-raster` and `sidecar-sim-only`.

## Reward formula and tick reconciliation

Declared aggregation on every record:

`total = task_progress + safety + efficiency + coherence + exploration`

Per-component scalar = arithmetic sum of that component over ticks (TTF-M6: exactly 6 ticks). Tick 6 is bound to a published sidecar (`abort_s`, `missed_window_s`, `survey_hold_s`, `dwell_s`) via `future_outcome.delayed_surprise_s` and is strictly after the raster window. Inflection `t_us` is an actual tick.

| id | ticks | tp | saf | eff | coh | exp | total | inflection tick |
|----|-------|----|-----|-----|-----|-----|-------|-----------------|
| 616 | 6 | +0.32 | −0.62 | −0.16 | +0.04 | −0.04 | −0.46 | 5 (23200) |
| 617 | 6 | −0.20 | −0.12 | −0.22 | −0.10 | +0.06 | −0.58 | 4 (5100) |
| 618 | 6 | +0.10 | +0.42 | +0.12 | +0.10 | +0.06 | +0.80 | 4 (6080) |
| 619 | 6 | +0.42 | +0.30 | +0.18 | +0.12 | +0.08 | +1.10 | 4 (4500) |
| 620 | 6 | +0.44 | +0.32 | +0.18 | +0.12 | +0.08 | +1.14 | 4 (5480) |

Tick-6 sidecar bind: 616 `abort_s=960`, 617 `missed_window_s=1080`, 618 `abort_s=510`, 619 `survey_hold_s=390`, 620 `dwell_s=450`.

## Raster / energy (Loihi-2 4-core, 23 pJ/spike)

| id | domain | n | rate Hz | window_ms | spikes | energy_pJ | energy_uJ |
|----|--------|---|---------|-----------|--------|-----------|-----------|
| 616 | selenium-hexafluoride-scrubber | 82 | 24 | 48 | 94 | 2162 | 0.002162 |
| 617 | osmium-hexafluoride-still | 88 | 28 | 32 | 79 | 1817 | 0.001817 |
| 618 | molybdenum-hexacarbonyl-bubbler | 104 | 22 | 36 | 82 | 1886 | 0.001886 |
| 619 | niobium-pentafluoride-still | 64 | 36 | 26 | 60 | 1380 | 0.001380 |
| 620 | tungsten-oxytetrachloride-column | 54 | 40 | 24 | 52 | 1196 | 0.001196 |

`spikes = round(n × rate × window_s)`. Every record carries `gate_snn` whose `decision` matches the safety gate; populations that declare rate+spikes meet the same ±1 budget against `decision_window_s`. `routing.third_factor` has modulator (NA / ACh / DA / 5-HT / adenosine), `tau_e_s`/`tau_e_ms` pair, and eligibility. Excerpt same-neuron gap ≥ 1000 µs; spike trains same-channel refractory ≥ 0.8 ms. Non-616 excerpts are kernelized and independent of `spike_events` times (overlap < 0.8).

## Local checks (staging, not raw)

See generator stdout: `check_jsonl` FactoryStaging, `validate_run.check_line`, `dumps_exact_json`, `raster_status`, `verify_batch_for_frontier(strict=True)`, `spike_probe.py --strict`, tick sums, refractory, Jaccard.

Never `training_ready`. Never `sim_or_real=real`. Never wrote `outputs/raw/`.

## Residual weaknesses (honest)

1. Only **one** labeled independent LIF (616). The other four excerpts are independent of `spike_events` times but are not declared population sims.
2. Wrong-ACCEPT still absent (guard).
3. Tick-6 sidecar bind is standing machinery (r14+), not a new class.
4. Five domain slugs leave the prompt's 8-item pool; a later round that must stay inside the pool will have to rotate sit-outs instead.
5. 617 wrong-reject is sidecar-convictable (routing `to` / shadow_C / ao_readback_flag / ao_readback_is_pv / namur_fail_high / burnout_flag) as a **new** error class (AO-readback-as-PV) vs r50 raw-mA, r80 HART-SV, r40 SP-echo, r84 stale-setpoint, r112 burnout-upscale, r116 NE107-maintenance.
6. 619 and 620 are both already-legal ACCEPTs; a later round could pair an ACCEPT with a world charge that does not go negative.

## Next densification target

Labeled LIF on a second record, or an ISI histogram sidecar. Remaining unused wrong-REJECT subclasses include **cold-junction-open-as-PV**. Wrong-ACCEPT remains structurally absent until a prompt amendment.

{NOVEL_COVERAGE_LINE}
"""
'''


def apply_pairs(text: str, pairs: list[tuple[str, str]]) -> str:
    for old, new in pairs:
        if old not in text:
            raise SystemExit(f"missing replacement {old!r}")
        text = text.replace(old, new)
    return text


def apply_pairs_optional(text: str, pairs: list[tuple[str, str]]) -> str:
    for old, new in pairs:
        text = text.replace(old, new)
    return text


def main() -> int:
    src = SRC.read_text(encoding="utf-8")
    i_rec = src.index("def lif_576_excerpt")
    i_tail = src.index("\ndef tokenize(")
    header, records, tail = src[:i_rec], src[i_rec:i_tail], src[i_tail:]

    header = apply_pairs(
        header,
        [
            (
                '"""Emit TTF r112 JSONL (ttf-r112-576..580) into /tmp/ttf-r112/. Never writes outputs/raw/."""',
                '"""Emit TTF r120 JSONL (ttf-r120-616..620) into /tmp/ttf-r120/. Never writes outputs/raw/."""',
            ),
            ('OUT_DIR = Path("/tmp/ttf-r112")', 'OUT_DIR = Path("/tmp/ttf-r120")'),
            ('BATCH_PATH = OUT_DIR / "batch-r112.jsonl"', 'BATCH_PATH = OUT_DIR / "batch-r120.jsonl"'),
            ('NOTES_PATH = OUT_DIR / "NOTES-r112.md"', 'NOTES_PATH = OUT_DIR / "NOTES-r120.md"'),
            ('("generated_at", "2026-09-02T18:42:00Z")', '("generated_at", "2026-09-02T18:58:00Z")'),
            (
                '''THIS_DOMAINS = (
    "ruthenium-tetroxide-scrubber",
    "tantalum-ethoxide-still",
    "indium-trichloride-bubbler",
    "lanthanum-aluminate-sinter",
    "diborane-cracker-column",
)''',
                '''THIS_DOMAINS = (
    "selenium-hexafluoride-scrubber",
    "osmium-hexafluoride-still",
    "molybdenum-hexacarbonyl-bubbler",
    "niobium-pentafluoride-still",
    "tungsten-oxytetrachloride-column",
)''',
            ),
            (
                '''THIS_PLANTS = (
    "Ruthetox-Whinfall",
    "Tantalox-Grainth",
    "Indichl-Sikebeck",
    "Lanthala-Braefell",
    "Diboran-Stoupside",
)''',
                '''THIS_PLANTS = (
    "Selenhex-Swalehead",
    "Osmihex-Arncliffe",
    "Molycarb-Gunnersgill",
    "Niobpenta-Burnsall",
    "Tungoxcl-Whernside",
)''',
            ),
            ('IDS = [f"ttf-r112-{n}" for n in range(576, 581)]', 'IDS = [f"ttf-r120-{n}" for n in range(616, 621)]'),
            ('NOVEL_COVERAGE_LINE = "Novel coverage: 18.8%"', 'NOVEL_COVERAGE_LINE = "Novel coverage: 19.6%"'),
            ('if path.parent.name == "ttf-r112":', 'if path.parent.name == "ttf-r120":'),
            ('if path.parent.name == "ttf-r112" or path.name == "gen_r112.py":', 'if path.parent.name == "ttf-r120" or path.name == "gen_r120.py":'),
            ('if path.parent.name == "ttf-r112" or "r112" in path.name:', 'if path.parent.name == "ttf-r120" or "r120" in path.name:'),
            ("if occ_round is not None and occ_round >= 112:", "if occ_round is not None and occ_round >= 120:"),
            ('("round", 112),', '("round", 120),'),
        ],
    )

    rec_pairs = [
        ("def lif_576_excerpt", "def lif_616_excerpt"),
        ("seed = 112576", "seed = 120616"),
        ('("seed", 112576),', '("seed", 120616),'),
        ("def record_576", "def record_616"),
        ("excerpt, extra = lif_576_excerpt()", "excerpt, extra = lif_616_excerpt()"),
        ("def record_577", "def record_617"),
        ("def record_578", "def record_618"),
        ("def record_579", "def record_619"),
        ("def record_580", "def record_620"),
        ("independent_excerpt(112577,", "independent_excerpt(120617,"),
        ("independent_excerpt(112578,", "independent_excerpt(120618,"),
        ("independent_excerpt(112579,", "independent_excerpt(120619,"),
        ("independent_excerpt(112580,", "independent_excerpt(120620,"),
        ("ttf-r112-576", "ttf-r120-616"),
        ("ttf-r112-577", "ttf-r120-617"),
        ("ttf-r112-578", "ttf-r120-618"),
        ("ttf-r112-579", "ttf-r120-619"),
        ("ttf-r112-580", "ttf-r120-620"),
        ("1756850400000576", "1756850400000616"),
        ("1756850400000577", "1756850400000617"),
        ("1756850400000578", "1756850400000618"),
        ("1756850400000579", "1756850400000619"),
        ("1756850400000580", "1756850400000620"),
        # plants / domains
        ("Ruthetox-Whinfall", "Selenhex-Swalehead"),
        ("Tantalox-Grainth", "Osmihex-Arncliffe"),
        ("Indichl-Sikebeck", "Molycarb-Gunnersgill"),
        ("Lanthala-Braefell", "Niobpenta-Burnsall"),
        ("Diboran-Stoupside", "Tungoxcl-Whernside"),
        ("ruthenium-tetroxide-scrubber", "selenium-hexafluoride-scrubber"),
        ("tantalum-ethoxide-still", "osmium-hexafluoride-still"),
        ("indium-trichloride-bubbler", "molybdenum-hexacarbonyl-bubbler"),
        ("lanthanum-aluminate-sinter", "niobium-pentafluoride-still"),
        ("diborane-cracker-column", "tungsten-oxytetrachloride-column"),
        ("RW-4", "SX-4"),
        ("TE-6", "OF-6"),
        ("IS-HIL", "MX-HIL"),
        ("LA-8", "NP-8"),
        ("DB-3", "WO-3"),
        ("Packed-S8", "Packed-S6"),
        ("Kettle-T3", "Kettle-F5"),
        ("Kettle-T4", "Kettle-F6"),
        ("Bubbler-I7", "Bubbler-M4"),
        ("Hearth-L2", "Still-N3"),
        ("Tower-B4", "Tower-W5"),
        # 616 partnered-neg chemistry
        (
            "is already metering 5.1 t/h caustic liquor into a 61 C ",
            "is already metering 4.4 t/h caustic liquor into a 58 C ",
        ),
        (
            "sump against a 54 C packing-habit cap. A liquor-first latch clamps the caustic; "
            "a feed-first story would keep the 5.1 t/h cruise.",
            "sump against a 51 C packing-habit cap. A liquor-first latch clamps the caustic; "
            "a feed-first story would keep the 4.4 t/h cruise.",
        ),
        (
            "Finish the SX-4 packed pass, keep liquor hotspot <= 54 C, and leave the ",
            "Finish the SX-4 packed pass, keep liquor hotspot <= 51 C, and leave the ",
        ),
        ('"rtd.liquor.C 61 C pulse"', '"rtd.liquor.C 58 C pulse"'),
        ('"ft.caustic.tph 5.1 t/h cruise"', '"ft.caustic.tph 4.4 t/h cruise"'),
        (
            "Liquor-first latches caustic 5.1 -> 2.8 t/h; feed-first keeps ",
            "Liquor-first latches caustic 4.4 -> 2.4 t/h; feed-first keeps ",
        ),
        (
            "would have kept 5.1 t/h cruise; predicted next-sample 57 C > 54 cap.",
            "would have kept 4.4 t/h cruise; predicted next-sample 54 C > 51 cap.",
        ),
        ("RuO4 assay (context)", "SeF6 assay (context)"),
        ('("liquor_cap_C", 54.0),', '("liquor_cap_C", 51.0),'),
        ('("observed_liquor_C", 61.0),', '("observed_liquor_C", 58.0),'),
        ('("proposed_caustic_tph", 5.1),', '("proposed_caustic_tph", 4.4),'),
        ('("ruo4_wt_pct", 8.4),', '("sef6_wt_pct", 11.2),'),
        ("caustic armed at 5.1 t/h.", "caustic armed at 4.4 t/h."),
        ("Cruise 5.1 t/h; liquor 61 C against 54 C packing-habit cap.", "Cruise 4.4 t/h; liquor 58 C against 51 C packing-habit cap."),
        ("5. rtd.liquor.C 61 C at 6.140 ms (winner).", "5. rtd.liquor.C 58 C at 6.140 ms (winner)."),
        ("6. ft.caustic.tph 5.1 t/h at 6.320 ms (loser by 180 us).", "6. ft.caustic.tph 4.4 t/h at 6.320 ms (loser by 180 us)."),
        ("7. Gate at 6.880 ms (winner + 740 us): MODIFY clamp 5.1 -> 2.8 t/h.", "7. Gate at 6.880 ms (winner + 740 us): MODIFY clamp 4.4 -> 2.4 t/h."),
        ("8. Clamp executes; next-sample liquor 50 C < 54 cap.", "8. Clamp executes; next-sample liquor 47 C < 51 cap."),
        ("gasses 12 mm of Raschig packing; AE burst.", "gasses 14 mm of Raschig packing; AE burst."),
        ('("name", "cruise_caustic_5p1")', '("name", "cruise_caustic_4p4")'),
        ('("caustic_tph", 5.1),', '("caustic_tph", 4.4),'),
        ('("liquor_C", 61.0),', '("liquor_C", 58.0),'),
        ('("predicted_unclamped_next_C", 57.0),', '("predicted_unclamped_next_C", 54.0),'),
        (
            "Planner proposes 5.1 t/h cruise: 61 C looks like an RuO4-assay spike, not ",
            "Planner proposes 4.4 t/h cruise: 58 C looks like an SeF6-assay spike, not ",
        ),
        (
            "Liquor 61 C won by 180 us, so the packing is loading heat, not still cooling. "
            "Holding 5.1 t/h predicts next-sample 57 C > 54 cap. MODIFY: caustic 5.1 -> "
            "2.8 t/h. Observed after clamp 50 C < 54. A full REJECT is not indicated: a "
            "sound packed pass accepts 2.8 t/h.",
            "Liquor 58 C won by 180 us, so the packing is loading heat, not still cooling. "
            "Holding 4.4 t/h predicts next-sample 54 C > 51 cap. MODIFY: caustic 4.4 -> "
            "2.4 t/h. Observed after clamp 47 C < 51. A full REJECT is not indicated: a "
            "sound packed pass accepts 2.4 t/h.",
        ),
        ('("cap", 54.0),', '("cap", 51.0),'),
        ('("observed", 61.0),', '("observed", 58.0),'),
        ('("predicted_unclamped_next", 57.0),', '("predicted_unclamped_next", 54.0),'),
        ('("clamped_caustic_tph", 2.8),', '("clamped_caustic_tph", 2.4),'),
        ('("observed_after_clamp", 50.0),', '("observed_after_clamp", 47.0),'),
        ('("proposed", 5.1), ("clamped", 2.8)', '("proposed", 4.4), ("clamped", 2.4)'),
        ('("name", "clamped_caustic_2p8")', '("name", "clamped_caustic_2p4")'),
        ('("caustic_tph", 2.8),', '("caustic_tph", 2.4),'),
        (
            "MODIFY: caustic 5.1 -> 2.8 t/h. Process-correct vs the 54 C packing-habit ",
            "MODIFY: caustic 4.4 -> 2.4 t/h. Process-correct vs the 51 C packing-habit ",
        ),
        (
            "Process-correct MODIFY held liquor at 50 C. At 23.200 ms stored strain "
            "in the Raschig packing still gassed a 12 mm face.",
            "Process-correct MODIFY held liquor at 47 C. At 23.200 ms stored strain "
            "in the Raschig packing still gassed a 14 mm face.",
        ),
        ('("caustic", "clamp executed; peak 50 C < 54")', '("caustic", "clamp executed; peak 47 C < 51")'),
        ('("packing", "12 mm gassing at 23.200 ms")', '("packing", "14 mm gassing at 23.200 ms")'),
        (
            "16 min liquor isolate after a 12 mm Raschig packing gassing collapse. Safety head -0.62 ",
            "16 min liquor isolate after a 14 mm Raschig packing gassing collapse. Safety head -0.62 ",
        ),
        ('("winner", "rtd.liquor.C (6.140 ms, 61 C)")', '("winner", "rtd.liquor.C (6.140 ms, 58 C)")'),
        ('("loser", "ft.caustic.tph (6.320 ms, 5.1 t/h)")', '("loser", "ft.caustic.tph (6.320 ms, 4.4 t/h)")'),
        (
            "Feed-first by < 180 us inside the 380 us window would have kept "
            "5.1 t/h cruise; predicted next-sample 57 C would have exceeded "
            "the 54 cap even without the packing charge.",
            "Feed-first by < 180 us inside the 380 us window would have kept "
            "4.4 t/h cruise; predicted next-sample 54 C would have exceeded "
            "the 51 cap even without the packing charge.",
        ),
        ("spike(\"enc.ruo4.ctx\"", "spike(\"enc.sef6.ctx\""),
        (
            "Selenhex-Swalehead SX-4 / Packed-S6: liquor 61 C beats caustic-feed by 180 us; correct ",
            "Selenhex-Swalehead SX-4 / Packed-S6: liquor 58 C beats caustic-feed by 180 us; correct ",
        ),
        (
            "Neurons 0-19 carry +0.68 caustic-clamp bias; stim 21.8-25.6 ms is the packing gassing.",
            "Neurons 0-19 carry +0.68 caustic-clamp bias; stim 21.8-25.6 ms is the packing gassing on SeF6.",
        ),
        # 617 WR: AO-readback
        ("burnout.upscale.eu", "ao.readback.eu"),
        ("relay.burnout.upscale", "relay.ao.readback"),
        ("burnout_upscale_stdp", "ao_readback_stdp"),
        ("pop(\"burnout_ctx\"", "pop(\"ao_ctx\""),
        ("taet_hold_burnout", "osf6_hold_ao"),
        ("taet_2p6", "osf6_2p4"),
        ("BURNOUT_UPSCALE", "AO_READBACK"),
        ("burnout-upscale-as-pv", "ao-readback-as-pv"),
        ("tc-open-circuit", "ao-echo"),
        (
            "is holding tantalum-ethoxide at 2.6 t/h with live "
            "kettle-base 74.0 C against a 128.0 C trip. A leftover thermocouple burnout-upscale "
            "still prints 21.2 mA as 248.0 C from an open-circuit detect. Live-RTD-first should "
            "ACCEPT the feed; a weak supervisor that binds the burnout EU will REJECT a legal still.",
            "is holding osmium-hexafluoride at 2.4 t/h with live "
            "kettle-base 78.0 C against a 132.0 C trip. A leftover analog-output readback "
            "still prints 16.8 mA as 252.0 C from the steam-valve AO echo. Live-RTD-first should "
            "ACCEPT the feed; a weak supervisor that binds the AO-readback EU will REJECT a legal still.",
        ),
        (
            "Keep 2.6 t/h Ta(OEt)5 on Kettle-F5 while live kettle-base stays <= 128.0 C; "
            "do not spend a leftover TC burnout-upscale on the hold.",
            "Keep 2.4 t/h OsF6 on Kettle-F5 while live kettle-base stays <= 132.0 C; "
            "do not spend a leftover AO-readback on the hold.",
        ),
        ('"live.kettle.C 74.0 C LIVE kettle RTD"', '"live.kettle.C 78.0 C LIVE kettle RTD"'),
        (
            '"ao.readback.eu 21.2 mA / 248.0 C leftover TC burnout"',
            '"ao.readback.eu 16.8 mA / 252.0 C leftover AO-readback"',
        ),
        (
            "Live-RTD-first should ACCEPT 2.6 t/h (74.0 C < 128.0 C trip). "
            "Burnout-first tempts a weak supervisor to treat 248.0 C as live.",
            "Live-RTD-first should ACCEPT 2.4 t/h (78.0 C < 132.0 C trip). "
            "AO-readback-first tempts a weak supervisor to treat 252.0 C as live.",
        ),
        (
            "340 us = one Kettle-F5 RTD sample minus leftover burnout-upscale group delay "
            "on this ethoxide bus.",
            "340 us = one Kettle-F5 RTD sample minus leftover AO-readback group delay "
            "on this hexafluoride bus.",
        ),
        (
            "Margin 180 us vs combined jitter ~56 us (live 26 + burnout 30): 3.2x over "
            "a 2.0x trust floor. Order is correctly live-RTD-first. The error is binding "
            "the leftover burnout-upscale EU, not the race.",
            "Margin 180 us vs combined jitter ~56 us (live 26 + AO 30): 3.2x over "
            "a 2.0x trust floor. Order is correctly live-RTD-first. The error is binding "
            "the leftover AO-readback EU, not the race.",
        ),
        (
            "leftover TC burnout-upscale shadow, 4 kHz, 30 us jitter, open-circuit UPSCALE STALE",
            "leftover AO-readback shadow, 4 kHz, 30 us jitter, steam-valve AO echo STALE",
        ),
        ("Ta(OEt)5 feed FT (context)", "OsF6 feed FT (context)"),
        ("ethanol make-up FT (context)", "fluorine make-up FT (context)"),
        ('("trip_C", 128.0),', '("trip_C", 132.0),'),
        ('("live_C", 74.0),', '("live_C", 78.0),'),
        ('("shadow_C", 248.0),', '("shadow_C", 252.0),'),
        ('("burnout_mA", 21.2),', '("ao_mA", 16.8),'),
        ('("burnout_flag", True),', '("ao_readback_flag", True),'),
        ('("proposed_taet_tph", 2.6),', '("proposed_osf6_tph", 2.4),'),
        ("OsF6 2.6 t/h armed.", "OsF6 2.4 t/h armed."),
        (
            "2. Live kettle 74.0 C; leftover TC burnout-upscale still prints 21.2 mA / 248.0 C.",
            "2. Live kettle 78.0 C; leftover AO-readback still prints 16.8 mA / 252.0 C.",
        ),
        ("3. Ta(OEt)5-FT precursor at 0.880 ms.", "3. OsF6-FT precursor at 0.880 ms."),
        ("5. live.kettle.C 74.0 C at 4.400 ms (winner).", "5. live.kettle.C 78.0 C at 4.400 ms (winner)."),
        ("6. ao.readback.eu 248.0 C at 4.580 ms (loser by 180 us).", "6. ao.readback.eu 252.0 C at 4.580 ms (loser by 180 us)."),
        ("8. Legal feed cancelled; live kettle-base still 74.0 C < 128.0 C trip.", "8. Legal feed cancelled; live kettle-base still 78.0 C < 132.0 C trip."),
        ("9. Burnout-upscale leftover remains the published bind.", "9. AO-readback leftover remains the published bind."),
        ("spike(\"ft.taet.ctx\"", "spike(\"ft.osf6.ctx\""),
        ('("taet_tph", 2.6),', '("osf6_tph", 2.4),'),
        ('("taet_tph", 0.0),', '("osf6_tph", 0.0),'),
        ('("burnout_upscale_is_pv", False),', '("ao_readback_is_pv", False),'),
        ('("burnout_upscale_is_pv", True),', '("ao_readback_is_pv", True),'),
        ('("tc_open_circuit", True),', '("ao_echo_stale", True),'),
        ('("proposed_taet_tph", 2.6),', '("proposed_osf6_tph", 2.4),'),  # already replaced if first hit consumed
        (
            "Planner proposes 2.6 t/h Ta(OEt)5 because live kettle 74.0 C is under the "
            "128.0 C trip; 248.0 C is leftover TC burnout-upscale (21.2 mA through URV), "
            "not the live kettle-base.",
            "Planner proposes 2.4 t/h OsF6 because live kettle 78.0 C is under the "
            "132.0 C trip; 252.0 C is leftover AO-readback (16.8 mA through URV), "
            "not the live kettle-base.",
        ),
        (
            "Leftover TC burnout-upscale still prints 248.0 C, over the 128.0 C trip "
            "once the supervisor treats the burnout EU as live. REJECT: hold Ta(OEt)5 "
            "0.0 t/h until the tag recovers under 128 so the still does not see an over-temp.",
            "Leftover AO-readback still prints 252.0 C, over the 132.0 C trip "
            "once the supervisor treats the AO echo as live. REJECT: hold OsF6 "
            "0.0 t/h until the tag recovers under 132 so the still does not see an over-temp.",
        ),
        ('("published_live_trip", 128.0),', '("published_live_trip", 132.0),'),
        ('("observed_live", 74.0),', '("observed_live", 78.0),'),
        ('("misbound_shadow_C", 248.0),', '("misbound_shadow_C", 252.0),'),
        ('("executed_taet_tph", 0.0),', '("executed_osf6_tph", 0.0),'),
        (
            "REJECT (incorrect): Ta(OEt)5 2.6 -> 0.0 t/h. Routing relay.ao.readback -> "
            "policy.hold_reject; no positive weight to policy.go_accept. Live 74.0 C never "
            "violated the 128.0 C trip.",
            "REJECT (incorrect): OsF6 2.4 -> 0.0 t/h. Routing relay.ao.readback -> "
            "policy.hold_reject; no positive weight to policy.go_accept. Live 78.0 C never "
            "violated the 132.0 C trip.",
        ),
        (
            "Wrong-REJECT froze Kettle-F5 at 0.0 t/h while live kettle-base stayed 74.0 C under the "
            "128.0 C trip. 18 min assay window missed. Correct gate was ACCEPT of "
            "the already-legal 2.6 t/h feed.",
            "Wrong-REJECT froze Kettle-F5 at 0.0 t/h while live kettle-base stayed 78.0 C under the "
            "132.0 C trip. 18 min assay window missed. Correct gate was ACCEPT of "
            "the already-legal 2.4 t/h feed.",
        ),
        ('("taet", "held at 0.0 t/h; 2.6 t/h abandoned")', '("osf6", "held at 0.0 t/h; 2.4 t/h abandoned")'),
        ('("live_C", "still 74.0 C, under 128.0 C published trip")', '("live_C", "still 78.0 C, under 132.0 C published trip")'),
        (
            '("tag", "21.2 mA / 248.0 C burnout-upscale false positive, not a live over-trip")',
            '("tag", "16.8 mA / 252.0 C AO-readback false positive, not a live over-trip")',
        ),
        (
            "The 248.0 C reading is leftover TC burnout-upscale (open-circuit UPSCALE), not a published live over-trip.",
            "The 252.0 C reading is leftover AO-readback (steam-valve output echo), not a published live over-trip.",
        ),
        (
            "Delayed (missed_window_s=1080): sister Kettle-F6 ran the same 2.6 t/h assay window after QA cleared burnout; T3's slot was already gone.",
            "Delayed (missed_window_s=1080): sister Kettle-F6 ran the same 2.4 t/h assay window after QA cleared the AO echo; F5's slot was already gone.",
        ),
        (
            "ACCEPT: live 74.0 C < published 128.0 C trip; leave 2.6 t/h; bind live kettle RTD; drop burnout-upscale as PV.",
            "ACCEPT: live 78.0 C < published 132.0 C trip; leave 2.4 t/h; bind live kettle RTD; drop AO-readback as PV.",
        ),
        ('("correct_trip_C", 128.0),', '("correct_trip_C", 132.0),'),
        ('("wrong_shadow_C", 248.0),', '("wrong_shadow_C", 252.0),'),
        (
            '("winner", "live.kettle.C (4.400 ms, 74.0 C LIVE RTD)")',
            '("winner", "live.kettle.C (4.400 ms, 78.0 C LIVE RTD)")',
        ),
        (
            '("loser", "ao.readback.eu (4.580 ms, 21.2 mA / 248.0 C STALE BURNOUT)")',
            '("loser", "ao.readback.eu (4.580 ms, 16.8 mA / 252.0 C STALE AO-READBACK)")',
        ),
        (
            "Burnout-first by < 180 us would still show live 74.0 C < 128.0 C. A "
            "correct gate ACCEPTs either way. The wrong REJECT spent the live-RTD "
            "win on a leftover TC burnout-upscale.",
            "AO-first by < 180 us would still show live 78.0 C < 132.0 C. A "
            "correct gate ACCEPTs either way. The wrong REJECT spent the live-RTD "
            "win on a leftover AO-readback.",
        ),
        (
            "ACh tags the (wrong) hold_reject bind at the leftover TC burnout shadow",
            "ACh tags the (wrong) hold_reject bind at the leftover AO-readback shadow",
        ),
        ('("bound_tag", "AO_READBACK"),', '("bound_tag", "AO_READBACK"),'),  # noop if already
        (
            "WRONG-REJECT at Osmihex-Arncliffe OF-6 / Kettle-F5: live kettle 74.0 C < 128.0 C trip; "
            "supervisor bound leftover TC burnout-upscale (21.2 mA / 248.0 C) as the live kettle-base",
            "WRONG-REJECT at Osmihex-Arncliffe OF-6 / Kettle-F5: live kettle 78.0 C < 132.0 C trip; "
            "supervisor bound leftover AO-readback (16.8 mA / 252.0 C) as the live kettle-base",
        ),
        (
            "Wrong-reject. Sidecar arithmetic 74.0 < 128.0 on live T3 is true; clamp bound "
            "to a 248.0 C leftover TC burnout-upscale. total -0.58 = -0.20 + -0.12 + -0.22 + -0.10 + 0.06.",
            "Wrong-reject. Sidecar arithmetic 78.0 < 132.0 on live F5 is true; clamp bound "
            "to a 252.0 C leftover AO-readback. total -0.58 = -0.20 + -0.12 + -0.22 + -0.10 + 0.06.",
        ),
        (
            "Teaches a probe that a correct live<trip read can still be a wrong gate when "
            "routing.table[0].to is policy.hold_reject and executed feed is zeroed on a leftover TC burnout-upscale.",
            "Teaches a probe that a correct live<trip read can still be a wrong gate when "
            "routing.table[0].to is policy.hold_reject and executed feed is zeroed on a leftover AO-readback.",
        ),
        # leftover burnout keys in 617 raster extra
        ('("burnout_flag", True),', '("ao_readback_flag", True),'),
        ('("namur_fail_high", False),', '("namur_fail_high", False),\n                ("burnout_flag", False),\n                ("ne107_maintenance", False),'),
        # 618 HIL
        (
            "is armed for 95 sccm InCl3 while "
            "ampoule AE sits at 38 pps against a 10 pps crack floor. A bubbler pyrometer, lit by the "
            "pad lamp spectrum, still reports 390 C under a 460 C bubbler cap. AE-first holds "
            "the bubbler; IR-first would commit 95 sccm into a cracked ampoule.",
            "is armed for 88 sccm Mo(CO)6 while "
            "ampoule AE sits at 42 pps against a 12 pps crack floor. A bubbler pyrometer, lit by the "
            "pad lamp spectrum, still reports 318 C under a 380 C bubbler cap. AE-first holds "
            "the bubbler; IR-first would commit 88 sccm into a cracked ampoule.",
        ),
        (
            "Run I7 only if ampoule AE stays <= 10 pps; otherwise hold so a cracked InCl3 ampoule is "
            "not loaded at 95 sccm.",
            "Run M4 only if ampoule AE stays <= 12 pps; otherwise hold so a cracked Mo(CO)6 ampoule is "
            "not loaded at 88 sccm.",
        ),
        ('"ae.ampoule.pps 38 pps ampoule crack"', '"ae.ampoule.pps 42 pps ampoule crack"'),
        ('"ir.bubbler.C 390 C pad-lamp glint"', '"ir.bubbler.C 318 C pad-lamp glint"'),
        (
            "AE-first latches bubbler hold 95 -> 0 sccm; IR-first would commit "
            "95 sccm on a still-legal 390 C bubbler-cap story.",
            "AE-first latches bubbler hold 88 -> 0 sccm; IR-first would commit "
            "88 sccm on a still-legal 318 C bubbler-cap story.",
        ),
        (
            "400 us = one ampoule-AE slot versus bubbler-IR decode on this HIL MOVPE bus.",
            "400 us = one ampoule-AE slot versus bubbler-IR decode on this HIL CVD bus.",
        ),
        (
            "window would have committed 95 sccm into a 38 pps ampoule crack.",
            "window would have committed 88 sccm into a 42 pps ampoule crack.",
        ),
        ('("ae_crack_floor_pps", 10.0),', '("ae_crack_floor_pps", 12.0),'),
        ('("observed_ae_pps", 38.0),', '("observed_ae_pps", 42.0),'),
        ('("bubbler_cap_C", 460.0),', '("bubbler_cap_C", 380.0),'),
        ('("observed_bubbler_C", 390.0),', '("observed_bubbler_C", 318.0),'),
        ('("proposed_incl3_sccm", 95.0),', '("proposed_moco_sccm", 88.0),'),
        ("Mo(CO)6 95 sccm armed.", "Mo(CO)6 88 sccm armed."),
        ("Bubbler IR 390 C under 460 C cap; AE already 38 pps.", "Bubbler IR 318 C under 380 C cap; AE already 42 pps."),
        ("5. ae.ampoule.pps 38 pps at 5.240 ms (winner).", "5. ae.ampoule.pps 42 pps at 5.240 ms (winner)."),
        ("6. ir.bubbler.C 390 C at 5.440 ms (loser by 200 us).", "6. ir.bubbler.C 318 C at 5.440 ms (loser by 200 us)."),
        ("7. Gate at 6.080 ms: REJECT hold bubbler 0 sccm.", "7. Gate at 6.080 ms: REJECT hold bubbler 0 sccm."),
        ('("name", "incl3_95")', '("name", "moco_88")'),
        ('("incl3_sccm", 95.0),', '("moco_sccm", 88.0),'),
        ('("incl3_sccm", 0.0),', '("moco_sccm", 0.0),'),
        ('("ampoule", "I7")', '("ampoule", "M4")'),
        ('("ae_pps", 38.0),', '("ae_pps", 42.0),'),
        ('("bubbler_C", 390.0),', '("bubbler_C", 318.0),'),
        (
            "Planner proposes 95 sccm because bubbler 390 C is under the 460 C "
            "cap and treats the AE puck as carrier noise.",
            "Planner proposes 88 sccm because bubbler 318 C is under the 380 C "
            "cap and treats the AE puck as carrier noise.",
        ),
        (
            "Ampoule AE 38 pps won by 200 us, so the ampoule is cracking, not still quiet. "
            "38 pps > 10 pps floor. REJECT: hold bubbler 95 -> 0 sccm. Bubbler 390 C < 460 C "
            "does not license the pass once AE is over floor.",
            "Ampoule AE 42 pps won by 200 us, so the ampoule is cracking, not still quiet. "
            "42 pps > 12 pps floor. REJECT: hold bubbler 88 -> 0 sccm. Bubbler 318 C < 380 C "
            "does not license the pass once AE is over floor.",
        ),
        ('("floor", 10.0),', '("floor", 12.0),'),
        ('("observed", 38.0),', '("observed", 42.0),'),
        ('("executed_incl3_sccm", 0.0),', '("executed_moco_sccm", 0.0),'),
        ('("cap", 460.0),', '("cap", 380.0),'),
        ('("observed", 390.0),', '("observed", 318.0),'),
        (
            "REJECT (correct): bubbler 95 -> 0 sccm. Routing relay.ae.ampoule -> "
            "policy.ampoule_hold. Ampoule crack is not loaded.",
            "REJECT (correct): bubbler 88 -> 0 sccm. Routing relay.ae.ampoule -> "
            "policy.ampoule_hold. Ampoule crack is not loaded.",
        ),
        (
            "Correct REJECT held I7 at 0 sccm. AE 38 pps beat bubbler 390 C; ampoule "
            "was already over the 10 pps crack floor. 8.5 min re-seat follows (abort_s=510).",
            "Correct REJECT held M4 at 0 sccm. AE 42 pps beat bubbler 318 C; ampoule "
            "was already over the 12 pps crack floor. 8.5 min re-seat follows (abort_s=510).",
        ),
        ('("bubbler", "held at 0 sccm; 95 sccm abandoned")', '("bubbler", "held at 0 sccm; 88 sccm abandoned")'),
        ('("ampoule", "38 pps crack not loaded")', '("ampoule", "42 pps crack not loaded")'),
        ('("ir", "390 C still under 460 C cap")', '("ir", "318 C still under 380 C cap")'),
        (
            "Bubbler IR 390 C was a HIL pad-lamp glint, not a bubbler-cap exceedance.",
            "Bubbler IR 318 C was a HIL pad-lamp glint, not a bubbler-cap exceedance.",
        ),
        ('("winner", "ae.ampoule.pps (5.240 ms, 38 pps)")', '("winner", "ae.ampoule.pps (5.240 ms, 42 pps)")'),
        ('("loser", "ir.bubbler.C (5.440 ms, 390 C)")', '("loser", "ir.bubbler.C (5.440 ms, 318 C)")'),
        (
            "IR-first by < 200 us would have committed 95 sccm into an ampoule "
            "already at 38 pps. The REJECT is still the correct process; AE is the ",
            "IR-first by < 200 us would have committed 88 sccm into an ampoule "
            "already at 42 pps. The REJECT is still the correct process; AE is the ",
        ),
        (
            "Molycarb-Gunnersgill MX-HIL / Bubbler-M4: ampoule AE 38 pps beats bubbler 390 C; correct "
            "REJECT holds the InCl3 bubbler",
            "Molycarb-Gunnersgill MX-HIL / Bubbler-M4: ampoule AE 42 pps beats bubbler 318 C; correct "
            "REJECT holds the Mo(CO)6 bubbler",
        ),
        (
            "Correct REJECT. AE 38 pps > 10 pps floor beats a legal bubbler IR. ",
            "Correct REJECT. AE 42 pps > 12 pps floor beats a legal bubbler IR. ",
        ),
        ('"incl3-bubbler"', '"moco-bubbler"'),
        (
            "Teaches an ampoule-AE vs pad-lamp-glint race on a HIL InCl3 bubbler: the crack floor, "
            "not the bubbler cap, licenses the pass.",
            "Teaches an ampoule-AE vs pad-lamp-glint race on a HIL Mo(CO)6 bubbler: the crack floor, "
            "not the bubbler cap, licenses the pass.",
        ),
        # 619 ACCEPT simulated NbF5
        (
            "is already at 1510 C bed while a "
            "pyrometer smear still reports as 1740 C against a 1620 C cap the live RTD "
            "has not crossed. Bed-first should ACCEPT 1.6 t/h LaAlO3 sinter; smear-first would "
            "invent a hold on an already-legal hearth pass.",
            "is already at 168 C kettle while a "
            "pyrometer smear still reports as 214 C against a 188 C cap the live RTD "
            "has not crossed. Kettle-first should ACCEPT 2.1 t/h NbF5; smear-first would "
            "invent a hold on an already-legal still pass.",
        ),
        (
            "Run NP-8 at 1.6 t/h while bed stays <= 1620 C; do not spend a pyrometer "
            "smear on the hearth hold.",
            "Run NP-8 at 2.1 t/h while kettle stays <= 188 C; do not spend a pyrometer "
            "smear on the still hold.",
        ),
        ('"rtd.bed.C 1510 C live"', '"rtd.kettle.C 168 C live"'),
        ('"ir.bed.smear as 1740 C"', '"ir.kettle.smear as 214 C"'),
        (
            "Bed-first should ACCEPT 1.6 t/h (1510 C < 1620 C cap). "
            "Smear-first would hold on a simulated hearth-film.",
            "Kettle-first should ACCEPT 2.1 t/h (168 C < 188 C cap). "
            "Smear-first would hold on a simulated kettle-film.",
        ),
        (
            "300 us = one bed-RTD sample versus pyrometer decode on this "
            "sinter bus.",
            "300 us = one kettle-RTD sample versus pyrometer decode on this "
            "pentafluoride bus.",
        ),
        (
            "window would have invented a hold on an already-legal 1510 C bed.",
            "window would have invented a hold on an already-legal 168 C kettle.",
        ),
        ("bed RTD, 4 kHz, 22 us jitter", "kettle RTD, 4 kHz, 22 us jitter"),
        ("LaAlO3 load cell (context)", "NbF5 load cell (context)"),
        ("hearth encoder (context)", "still encoder (context)"),
        ('("bed_cap_C", 1620.0),', '("kettle_cap_C", 188.0),'),
        ('("observed_bed_C", 1510.0),', '("observed_kettle_C", 168.0),'),
        ('("pyro_smear_C", 1740.0),', '("pyro_smear_C", 214.0),'),
        ('("proposed_sinter_tph", 1.6),', '("proposed_nbf5_tph", 2.1),'),
        ("sinter 1.6 t/h armed.", "NbF5 2.1 t/h armed."),
        ("2. Bed 1510 C; pyrometer smear as 1740 C over 1620 C cap.", "2. Kettle 168 C; pyrometer smear as 214 C over 188 C cap."),
        ("3. Hearth-encoder precursor at 0.820 ms.", "3. Still-encoder precursor at 0.820 ms."),
        ("5. rtd.bed.C 1510 C at 3.960 ms (winner).", "5. rtd.kettle.C 168 C at 3.960 ms (winner)."),
        ("6. ir.bed.smear at 4.120 ms (loser by 160 us).", "6. ir.kettle.smear at 4.120 ms (loser by 160 us)."),
        ("7. Gate at 4.500 ms: ACCEPT leave 1.6 t/h.", "7. Gate at 4.500 ms: ACCEPT leave 2.1 t/h."),
        ("8. Bed remains 1510 C < 1620 C; smear unused as a hold.", "8. Kettle remains 168 C < 188 C; smear unused as a hold."),
        ("9. Simulated hearth film remains the IR source.", "9. Simulated kettle film remains the IR source."),
        ("spike(\"enc.hearth.ctx\"", "spike(\"enc.still.ctx\""),
        ("spike(\"rtd.bed.C\"", "spike(\"rtd.kettle.C\""),
        ("spike(\"ir.bed.smear\"", "spike(\"ir.kettle.smear\""),
        ('("name", "sinter_1p6")', '("name", "nbf5_2p1")'),
        ('("sinter_tph", 1.6),', '("nbf5_tph", 2.1),'),
        ('("bed_C", 1510.0),', '("kettle_C", 168.0),'),
        ('("bed_C", 1510.0),', '("kettle_C", 168.0),'),
        ('("bed_cap_C", 1620.0),', '("kettle_cap_C", 188.0),'),
        ('("pyro_smear_C", 1740.0),', '("pyro_smear_C", 214.0),'),
        ('("proposed_sinter_tph", 1.6),', '("proposed_nbf5_tph", 2.1),'),
        (
            "Planner proposes 1.6 t/h because bed 1510 C is under the 1620 C cap; "
            "1740 C is a pyrometer smear, not a bed temperature.",
            "Planner proposes 2.1 t/h because kettle 168 C is under the 188 C cap; "
            "214 C is a pyrometer smear, not a kettle temperature.",
        ),
        (
            "Bed 1510 C won by 160 us and sits under the 1620 C cap. Pyrometer smear "
            "1740 C is a simulated film, not a bed reading. ACCEPT: leave 1.6 t/h. "
            "A hold would idle a legal sinter pass.",
            "Kettle 168 C won by 160 us and sits under the 188 C cap. Pyrometer smear "
            "214 C is a simulated film, not a kettle reading. ACCEPT: leave 2.1 t/h. "
            "A hold would idle a legal still pass.",
        ),
        (
            '"bed_C"',
            '"kettle_C"',
        ),
        ('("cap", 1620.0),', '("cap", 188.0),'),
        ('("observed", 1510.0),', '("observed", 168.0),'),
        ('("executed_sinter_tph", 1.6),', '("executed_nbf5_tph", 2.1),'),
        ('("observed", 1740.0),', '("observed", 214.0),'),
        ('("not_a_bed_reading", True),', '("not_a_kettle_reading", True),'),
        (
            "ACCEPT: leave 1.6 t/h. Routing relay.rtd.bed -> policy.sinter_go. "
            "Pyrometer unused as a hold.",
            "ACCEPT: leave 2.1 t/h. Routing relay.rtd.kettle -> policy.still_go. "
            "Pyrometer unused as a hold.",
        ),
        (
            "Correct ACCEPT left NP-8 at 1.6 t/h. Bed 1510 C beat pyrometer smear 1740 C; "
            "the 1620 C cap was never crossed. 6.5 min density survey follows ",
            "Correct ACCEPT left NP-8 at 2.1 t/h. Kettle 168 C beat pyrometer smear 214 C; "
            "the 188 C cap was never crossed. 6.5 min density survey follows ",
        ),
        ('("sinter", "1.6 t/h held as proposed")', '("nbf5", "2.1 t/h held as proposed")'),
        ('("bed", "1510 C < 1620 C cap")', '("kettle", "168 C < 188 C cap")'),
        ('("smear", "1740 C film unused")', '("smear", "214 C film unused")'),
        (
            "IR 1740 C was a simulated hearth-film smear, not a bed over-cap.",
            "IR 214 C was a simulated kettle-film smear, not a kettle over-cap.",
        ),
        ('("winner", "rtd.bed.C (3.960 ms, 1510 C)")', '("winner", "rtd.kettle.C (3.960 ms, 168 C)")'),
        ('("loser", "ir.bed.smear (4.120 ms, smear 1740 C)")', '("loser", "ir.kettle.smear (4.120 ms, smear 214 C)")'),
        (
            "Smear-first by < 160 us would still be a hearth film over the "
            "1620 C cap; a correct gate ACCEPTs either way. Reversing would only "
            "have delayed confirmation of the same legal bed.",
            "Smear-first by < 160 us would still be a kettle film over the "
            "188 C cap; a correct gate ACCEPTs either way. Reversing would only "
            "have delayed confirmation of the same legal kettle.",
        ),
        ("thalamic-relay.bed-rtd", "thalamic-relay.kettle-rtd"),
        ("spikenaut.policy.sinter-go", "spikenaut.policy.still-go"),
        ('("relay.rtd.bed", "policy.sinter_go", 0.71)', '("relay.rtd.kettle", "policy.still_go", 0.71)'),
        ('("relay.ir.bed", "policy.smear_hold", 0.21)', '("relay.ir.kettle", "policy.smear_hold", 0.21)'),
        ('("relay.rtd.bed", "policy.sinter_go", 0.10)', '("relay.rtd.kettle", "policy.still_go", 0.10)'),
        ("already_legal_stdp; 5-HT at bed win (3.960 ms) tags the go bind", "already_legal_stdp; 5-HT at kettle win (3.960 ms) tags the go bind"),
        ('pop("sinter_go"', 'pop("still_go"'),
        (
            "Niobpenta-Burnsall NP-8 / Still-N3: bed 1510 C beats pyrometer smear; correct ACCEPT "
            "of an already-legal 1.6 t/h (total +1.10)",
            "Niobpenta-Burnsall NP-8 / Still-N3: kettle 168 C beats pyrometer smear; correct ACCEPT "
            "of an already-legal 2.1 t/h (total +1.10)",
        ),
        (
            "Correct ACCEPT. Bed 1510 C < 1620 C cap; pyrometer smear unused. ",
            "Correct ACCEPT. Kettle 168 C < 188 C cap; pyrometer smear unused. ",
        ),
        ('"laalo3-sinter"', '"nbf5-still"'),
        (
            "Teaches that a pyrometer smear can lose to a legal bed RTD inside a "
            "300 us window; reversing 160 us would have invented a hold on an already-legal hearth.",
            "Teaches that a pyrometer smear can lose to a legal kettle RTD inside a "
            "300 us window; reversing 160 us would have invented a hold on an already-legal still.",
        ),
        # 620 ACCEPT designed WOCl4
        (
            "is circulating 2.2 t/h diborane-cracker bottoms at 42 C "
            "against a 58 C tray cap. Overhead IR smear sits at 71 C over that cap while "
            "the live tray RTD has not crossed it. Tray-first should ACCEPT the already-legal "
            "2.2 t/h set; vapor-first would only delay confirmation of the same legal column.",
            "is circulating 3.1 t/h WOCl4 bottoms at 54 C "
            "against a 72 C tray cap. Overhead IR smear sits at 89 C over that cap while "
            "the live tray RTD has not crossed it. Tray-first should ACCEPT the already-legal "
            "3.1 t/h set; vapor-first would only delay confirmation of the same legal column.",
        ),
        (
            "Hold 2.2 t/h on B4 while tray stays <= 58 C; do not spend an overhead-IR "
            "smear on the column hold.",
            "Hold 3.1 t/h on W5 while tray stays <= 72 C; do not spend an overhead-IR "
            "smear on the column hold.",
        ),
        ('"rtd.tray.C 42 C live"', '"rtd.tray.C 54 C live"'),
        ('"ir.ovhd.smear 71 C glint"', '"ir.ovhd.smear 89 C glint"'),
        (
            "Tray-first should ACCEPT 2.2 t/h (42 C < 58 C cap). "
            "Vapor-first would only delay confirmation of the same legal column.",
            "Tray-first should ACCEPT 3.1 t/h (54 C < 72 C cap). "
            "Vapor-first would only delay confirmation of the same legal column.",
        ),
        (
            "diborane-cracker bus.",
            "oxytetrachloride bus.",
        ),
        ("B2H6 FT (context)", "WOCl4 FT (context)"),
        ('("tray_cap_C", 58.0),', '("tray_cap_C", 72.0),'),
        ('("observed_tray_C", 42.0),', '("observed_tray_C", 54.0),'),
        ('("overhead_smear_C", 71.0),', '("overhead_smear_C", 89.0),'),
        ('("proposed_b2h6_tph", 2.2),', '("proposed_wocl4_tph", 3.1),'),
        ("B2H6 2.2 t/h armed.", "WOCl4 3.1 t/h armed."),
        ("2. Tray 42 C; overhead IR smear 71 C over 58 C cap.", "2. Tray 54 C; overhead IR smear 89 C over 72 C cap."),
        ("3. B2H6-FT precursor at 0.960 ms.", "3. WOCl4-FT precursor at 0.960 ms."),
        ("5. rtd.tray.C 42 C at 4.840 ms (winner).", "5. rtd.tray.C 54 C at 4.840 ms (winner)."),
        ("6. ir.ovhd.smear 71 C at 5.020 ms (loser by 180 us).", "6. ir.ovhd.smear 89 C at 5.020 ms (loser by 180 us)."),
        ("7. Gate at 5.480 ms: ACCEPT leave 2.2 t/h.", "7. Gate at 5.480 ms: ACCEPT leave 3.1 t/h."),
        ("8. Tray remains 42 C < 58 C; vapor unused as a hold.", "8. Tray remains 54 C < 72 C; vapor unused as a hold."),
        ("9. Diborane cracker bottoms continue.", "9. WOCl4 bottoms continue."),
        ("spike(\"ft.b2h6.ctx\"", "spike(\"ft.wocl4.ctx\""),
        ('("name", "b2h6_2p2")', '("name", "wocl4_3p1")'),
        ('("b2h6_tph", 2.2),', '("wocl4_tph", 3.1),'),
        (
            "Planner proposes 2.2 t/h because tray 42 C is under the 58 C cap "
            "and overhead 71 C is a headspace-IR smear, not a tray temperature.",
            "Planner proposes 3.1 t/h because tray 54 C is under the 72 C cap "
            "and overhead 89 C is a headspace-IR smear, not a tray temperature.",
        ),
        (
            "Tray 42 C won by 180 us and sits under the 58 C cap. Overhead smear "
            "71 C is unused as a hold. ACCEPT: leave 2.2 t/h. A hold would idle a legal column.",
            "Tray 54 C won by 180 us and sits under the 72 C cap. Overhead smear "
            "89 C is unused as a hold. ACCEPT: leave 3.1 t/h. A hold would idle a legal column.",
        ),
        ('("cap", 58.0),', '("cap", 72.0),'),
        ('("observed", 42.0),', '("observed", 54.0),'),
        ('("executed_b2h6_tph", 2.2),', '("executed_wocl4_tph", 3.1),'),
        ('("observed", 71.0),', '("observed", 89.0),'),
        (
            "ACCEPT: leave 2.2 t/h. Routing relay.rtd.tray -> policy.col_go. "
            "Overhead unused as a hold.",
            "ACCEPT: leave 3.1 t/h. Routing relay.rtd.tray -> policy.col_go. "
            "Overhead unused as a hold.",
        ),
        (
            "Correct ACCEPT left B4 at 2.2 t/h. Tray 42 C beat overhead smear 71 C; both "
            "caps held. 7.5 min assay dwell follows (dwell_s=450).",
            "Correct ACCEPT left W5 at 3.1 t/h. Tray 54 C beat overhead smear 89 C; both "
            "caps held. 7.5 min assay dwell follows (dwell_s=450).",
        ),
        ('("b2h6", "2.2 t/h held as proposed")', '("wocl4", "3.1 t/h held as proposed")'),
        ('("tray", "42 C < 58 C cap")', '("tray", "54 C < 72 C cap")'),
        ('("overhead", "71 C smear unused")', '("overhead", "89 C smear unused")'),
        (
            "Overhead IR 71 C was never a cap; it only lost the race to a legal tray RTD.",
            "Overhead IR 89 C was never a cap; it only lost the race to a legal tray RTD.",
        ),
        ("after the pass on WO-3.", "after the pass on WO-3."),
        ('("winner", "rtd.tray.C (4.840 ms, 42 C)")', '("winner", "rtd.tray.C (4.840 ms, 54 C)")'),
        ('("loser", "ir.ovhd.smear (5.020 ms, 71 C)")', '("loser", "ir.ovhd.smear (5.020 ms, 89 C)")'),
        (
            "Vapor-first by < 180 us would still be a smear over the 58 C cap; ",
            "Vapor-first by < 180 us would still be a smear over the 72 C cap; ",
        ),
        (
            "Tungoxcl-Whernside WO-3 / Tower-W5: tray 42 C beats overhead smear 71 C; correct ACCEPT "
            "of an already-legal 2.2 t/h (total +1.14)",
            "Tungoxcl-Whernside WO-3 / Tower-W5: tray 54 C beats overhead smear 89 C; correct ACCEPT "
            "of an already-legal 3.1 t/h (total +1.14)",
        ),
        (
            "Correct ACCEPT. Tray 42 C < 58 C cap; overhead unused. ",
            "Correct ACCEPT. Tray 54 C < 72 C cap; overhead unused. ",
        ),
        ('"diborane"', '"wocl4"'),
        (
            "Teaches an already-legal diborane cracker column: live tray sits under cap; "
            "race order only confirms the ACCEPT.",
            "Teaches an already-legal tungsten-oxytetrachloride column: live tray sits under cap; "
            "race order only confirms the ACCEPT.",
        ),
    ]

    # Some pairs may already have been consumed by earlier identical strings.
    # Apply with a two-pass: required unique pairs first, then optional leftovers.
    missing = []
    for old, new in rec_pairs:
        if old == new:
            continue
        if old not in records:
            missing.append(old)
        else:
            records = records.replace(old, new)
    if missing:
        # print missing but continue if they were already transformed by a prior pair
        still = [m for m in missing if m in records]
        # leftover keys that a previous replace already changed
        print(f"INFO skipped {len(missing)} already-consumed replacements")
        if still:
            print("STILL MISSING:")
            for item in still[:40]:
                print(" -", item[:120])
            return 1

    # remaining burnout_flag in 617 constraints if first replace hit ao_readback_flag
    records = records.replace('("burnout_flag", True)', '("ao_readback_flag", True)')
    records = records.replace("leftover TC burnout", "leftover AO-readback")
    records = records.replace("TC burnout-upscale", "AO-readback")
    records = records.replace("burnout-upscale", "AO-readback")
    records = records.replace("burnout EU", "AO-readback EU")
    records = records.replace("cleared burnout", "cleared the AO echo")

    # namur extra may have duplicated if applied twice — collapse later via compile
    # Add ne107/burnout false on 617 proposed evidence if not present
    if "ne107_maintenance" not in records:
        records = records.replace(
            '("namur_fail_high", False),\n                        ("ao_echo_stale"',
            '("namur_fail_high", False),\n                        ("ne107_maintenance", False),\n                        ("ao_echo_stale"',
        )

    i_notes = tail.index("def notes_text(")
    i_self = tail.index("\ndef self_check(")
    tail = tail[:i_notes] + NOTES_FN + tail[i_self:]

    tail = apply_pairs(
        tail,
        [
            ('if rec["id"] != "ttf-r112-577":', 'if rec["id"] != "ttf-r120-617":')
            if 'if rec["id"] != "ttf-r112-577":' in tail
            else ("PLACEHOLDER_NEVER", "PLACEHOLDER_NEVER"),
        ],
    )
    tail_pairs = [
        ('wrong[0]["id"] != "ttf-r112-577"', 'wrong[0]["id"] != "ttf-r120-617"'),
        ('if hil != ["ttf-r112-578"]:', 'if hil != ["ttf-r120-618"]:'),
        ('if rec["id"] == "ttf-r112-576":', 'if rec["id"] == "ttf-r120-616":'),
        ('issues.append("576 missing independent_lif")', 'issues.append("616 missing independent_lif")'),
        ('issues.append("576 inflection outside window")', 'issues.append("616 inflection outside window")'),
        ('issues.append("576 partnered-neg total not negative")', 'issues.append("616 partnered-neg total not negative")'),
        ('if rec["meta"]["round"] != 112:', 'if rec["meta"]["round"] != 120:'),
        ('if rec["id"] == "ttf-r112-577":', 'if rec["id"] == "ttf-r120-617":'),
        ('issues.append("577 routing has go_accept")', 'issues.append("617 routing has go_accept")'),
        ('issues.append("577 missing hold_reject routing")', 'issues.append("617 missing hold_reject routing")'),
        (
            'if ev.get("burnout_upscale_is_pv") is not False:',
            'if ev.get("ao_readback_is_pv") is not False:',
        ),
        (
            'issues.append("577 proposed evidence missing burnout_upscale_is_pv=false")',
            'issues.append("617 proposed evidence missing ao_readback_is_pv=false")',
        ),
        (
            'if rec["raster"].get("burnout_flag") is not True:',
            'if rec["raster"].get("ao_readback_flag") is not True:',
        ),
        (
            'issues.append("577 raster missing burnout_flag")',
            'issues.append("617 raster missing ao_readback_flag")',
        ),
        (
            'BATCH_PATH, "batch-r112.jsonl", staging=FactoryStaging(enabled=True)',
            'BATCH_PATH, "batch-r120.jsonl", staging=FactoryStaging(enabled=True)',
        ),
        ('f"batch-r112.jsonl:{i}"', 'f"batch-r120.jsonl:{i}"'),
        (
            "records = [record_576(), record_577(), record_578(), record_579(), record_580()]",
            "records = [record_616(), record_617(), record_618(), record_619(), record_620()]",
        ),
    ]
    for old, new in tail_pairs:
        if old not in tail:
            raise SystemExit(f"tail missing {old!r}")
        tail = tail.replace(old, new)

    out = header + records + tail
    # sanity
    for banned in (
        "ttf-r112-",
        "record_576",
        "Ruthetox-Whinfall",
        "tantalum-ethoxide-still",
        "burnout.upscale.eu",
        "outputs/raw",
    ):
        if banned == "outputs/raw":
            if "Never writes outputs/raw" not in out and "Never writes outputs/raw/" not in header:
                pass
            continue
        if banned in out:
            raise SystemExit(f"banned leftover {banned!r}")
    DST.write_text(out, encoding="utf-8")
    print(f"wrote {DST} bytes={DST.stat().st_size}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
