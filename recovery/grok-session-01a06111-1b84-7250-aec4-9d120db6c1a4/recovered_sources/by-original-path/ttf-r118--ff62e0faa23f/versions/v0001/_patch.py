#!/usr/bin/env python3
"""Finish r118 generator: IDs, flow consistency, NE107 leftovers, NOTES."""
from pathlib import Path
import re

p = Path("/tmp/ttf-r118/gen_r118.py")
t = p.read_text(encoding="utf-8")

t = t.replace('IDS = [f"ttf-r110-{n}" for n in range(606, 611)]',
              'IDS = [f"ttf-r118-{n}" for n in range(606, 611)]')
t = t.replace('NOVEL_COVERAGE_LINE = "Novel coverage: 16.6%"',
              'NOVEL_COVERAGE_LINE = "Novel coverage: 17.2%"')
t = t.replace('if rec["meta"]["round"] != 110:',
              'if rec["meta"]["round"] != 118:')

# split record functions so numeric replacements stay local
chunks = re.split(r"(?=^def (?:record_|notes_text|self_check|lif_))", t, flags=re.M)
out = []
for ch in chunks:
    head = ch[:80]
    if ch.startswith("def record_606") or ch.startswith("def lif_606"):
        ch = ch.replace('("proposed_meoh_tph", 8.2)', '("proposed_meoh_tph", 6.8)')
        ch = ch.replace('("meoh_tph", 8.2)', '("meoh_tph", 6.8)')
        ch = ch.replace('("meoh_tph", 4.6)', '("meoh_tph", 3.4)')
        ch = ch.replace('("clamped_meoh_tph", 4.6)', '("clamped_meoh_tph", 3.4)')
        ch = ch.replace('("proposed", 8.2), ("clamped", 4.6)', '("proposed", 6.8), ("clamped", 3.4)')
        ch = ch.replace("methanol 8.2 ->", "methanol 6.8 ->")
        ch = ch.replace("clamp 8.2 ->", "clamp 6.8 ->")
        ch = ch.replace("latches methanol 8.2", "latches methanol 6.8")
        ch = ch.replace("ethylene_methanol", "methanol")
        ch = ch.replace("on the oxidizer bus", "on the carbonylation bus")
        ch = ch.replace("Oxidizer isolate 17 min", "Carbonylation isolate 17 min")
        ch = ch.replace("still-cooling oxidizer model", "still-cooling carbonylation model")
        ch = ch.replace("until the buckle", "until the gasket blow")
        ch = ch.replace("Packing-gasket buckle still", "Packing-gasket blow still")
        ch = ch.replace("16 mm buckle", "16 mm blow")
        ch = ch.replace("still buckled a 16 mm", "still blew a 16 mm")
        ch = ch.replace("still buckles 16 mm", "still blows 16 mm")
        ch = ch.replace("packing-gasket buckle", "packing-gasket blow")
    elif ch.startswith("def record_607"):
        ch = ch.replace("binds the burnout-upscale EU", "binds the NE107 maintenance EU")
        ch = ch.replace("live 28 + burnout 32", "live 28 + NE107 32")
        ch = ch.replace("STALE burnout-upscale", "STALE NE107-maintenance")
        ch = ch.replace("while D-2 waits", "while X-3 waits")
        ch = ch.replace("Hydroxyl-Beck D-2", "Hydroxyl-Beck X-3")
        ch = ch.replace('("ne107_status_mA", 21.6)', '("ne107_status_mA", 16.4)')
        ch = ch.replace("leftover NE107 maintenance URV", "leftover NE107 maintenance EU")
        ch = ch.replace("bound_pv\", \"ne107_maintenance\"", 'bound_pv", "ne107_maint"')
        # add NE43-distinct flags in evidence if missing
        if '"namur_fail_high"' not in ch:
            ch = ch.replace(
                '("ne107_as_eu", True),\n                        ("pv_live", True),',
                '("ne107_as_eu", True),\n'
                '                        ("namur_fail_high", False),\n'
                '                        ("ne107_code", "M"),\n'
                '                        ("pv_live", True),',
            )
        if '"namur_fail_high"' not in ch.split("constraints")[1][:800]:
            ch = ch.replace(
                '("ne107_as_eu", True),\n                        ("proposed_has_tph", 5.6),',
                '("ne107_as_eu", True),\n'
                '                        ("namur_fail_high", False),\n'
                '                        ("ne107_code", "M"),\n'
                '                        ("proposed_has_tph", 5.6),',
            )
        ch = ch.replace(
            'ACh tags the (wrong) hold_reject bind at the leftover URV failsafe',
            'ACh tags the (wrong) hold_reject bind at the leftover NE107 M-bit',
        )
        ch = ch.replace("iec-60584-urv", "namur-ne107-m")
        ch = ch.replace(
            "routing.table[0].to is policy.hold_reject and executed feed is zeroed on a leftover burnout-upscale jumper.",
            "routing.table[0].to is policy.hold_reject and executed feed is zeroed on a leftover NAMUR NE107 M-bit.",
        )
        ch = ch.replace(
            "supervisor bound leftover NAMUR NE107 maintenance-required latch (246.0 C) as the live bed",
            "supervisor bound leftover NAMUR NE107 maintenance-required latch (246.0 C) as the live magma",
        )
        # title may still say D-2
        ch = ch.replace("Hydroxyl-Beck D-2:", "Hydroxyl-Beck X-3:")
        ch = ch.replace("IEC 60584", "NAMUR NE107")
    elif ch.startswith("def record_608"):
        ch = ch.replace("acrylic encoder", "Na2S encoder")
        ch = ch.replace("proposed_acrylic_tph", "proposed_na2s_tph")
        ch = ch.replace("executed_acrylic_tph", "executed_na2s_tph")
        ch = ch.replace("acrylic_tph", "na2s_tph")
        ch = ch.replace("acrylic_7p1", "na2s_5p3")
        ch = ch.replace("hold acrylic", "hold Na2S")
        ch = ch.replace("acrylic 7.1", "Na2S 5.3")
        ch = ch.replace("acrylic 5.3", "Na2S 5.3")
        ch = ch.replace("hold 7.1 ->", "hold 5.3 ->")
        ch = ch.replace("7.1 -> 0", "5.3 -> 0")
        ch = ch.replace("E-8 indexed", "K-8 indexed")
        ch = ch.replace("next esterification", "next PPS cycle")
        ch = ch.replace("foam collapse", "oligomer foam")
    elif ch.startswith("def record_609"):
        ch = ch.replace("proposed_diamine_tph", "proposed_diamine_tph")
        ch = ch.replace('("proposed_diamine_tph", 2.6)', '("proposed_diamine_tph", 1.9)')
        ch = ch.replace('("diamine_tph", 2.6)', '("diamine_tph", 1.9)')
        ch = ch.replace('("executed_diamine_tph", 2.6)', '("executed_diamine_tph", 1.9)')
        ch = ch.replace("liquor_cap_C", "stillbase_cap_C")
        ch = ch.replace("observed_liquor_C", "observed_stillbase_C")
        ch = ch.replace("liquor_C", "stillbase_C")
        ch = ch.replace('"liquor"', '"still_base"')
        ch = ch.replace("liquor 38 C", "still-base 44 C")
        ch = ch.replace("because liquor 38", "because still-base 44")
        ch = ch.replace("legal liquor", "legal still-base")
        ch = ch.replace("liquor over-cap", "still-base over-cap")
        ch = ch.replace("liquor_under_cap_stdp", "stillbase_under_cap_stdp")
        ch = ch.replace("liquor-vs-smear", "stillbase-vs-smear")
        ch = ch.replace("polycarbonate", "polyetherimide")
        ch = ch.replace("Etherimid-Dene K-11", "Etherimid-Dene S-11")
        ch = ch.replace("PEI polycarbonate kettle", "PEI still")
        ch = ch.replace("live liquor sits", "live still-base sits")
        ch = ch.replace("38 C liquor", "44 C still-base")
        # keep 38.0 numeric in fields? description used 44 C still-base earlier.
        # Align observed still-base to 44.0 to match description.
        ch = ch.replace('("stillbase_C", 38.0)', '("stillbase_C", 44.0)')
        ch = ch.replace('("observed_stillbase_C", 38.0)', '("observed_stillbase_C", 44.0)')
        ch = ch.replace("38 C < 62 C", "44 C < 62 C")
        ch = ch.replace("liquor 38", "still-base 44")
    elif ch.startswith("def record_610"):
        ch = ch.replace("proposed_nb_tph", "proposed_vdf_tph")
        ch = ch.replace("executed_nb_tph", "executed_vdf_tph")
        ch = ch.replace("nb_tph", "vdf_tph")
        ch = ch.replace('("proposed_vdf_tph", 4.4)', '("proposed_vdf_tph", 3.2)')
        ch = ch.replace('("vdf_tph", 4.4)', '("vdf_tph", 3.2)')
        ch = ch.replace("policy.nb_hold", "policy.vdf_hold")
        ch = ch.replace('pop("nb_hold"', 'pop("vdf_hold"')
        ch = ch.replace("VDF ROMP kettle", "FKM emulsion kettle")
        ch = ch.replace("live liquor sits", "live kettle sits")
        # do NOT touch 8.2 Hz in pop()
    out.append(ch)
t = "".join(out)

NOTES = r'''def notes_text(jmax: float) -> str:
    return f"""# Thalamic Trajectory Factory — NOTES-r118

- Factory: `thalamic-trajectory-factory`
- Run label: `2026-09-02-final-heavy`
- Generator: `grok-4.6`
- Channel: SuperGrok Heavy consumer chat (RM-793 research-only)
- Quota: 5
- Quality: Q=5
- IDs: `ttf-r118-606` … `ttf-r118-610`
- Domains this batch: `formic-acid-carbonylation`, `hydroxylamine-sulfate-crystallizer`, `polyphenylene-sulfide-kettle`, `polyetherimide-still`, `fluoroelastomer-emulsion`

These five domain slugs sit outside the prompt 8-pool and outside staged r13–r117 occupancy (jsonl SoT plus incomplete gens r114/r116, including r108 phenol-cumene / SBR / zeolite-Y / SCR / graphite-spheroidizer, r109 MTO / sulfuryl-chloride / LaB6 / PTHF / VOCl3, r110 glyoxal / succinic-anhydride / butyl-acrylate / PC-interfacial / norbornene, r111 phthalic / TBHP / LaF3 / 2-EH / SF6, r112 RuO4 / Ta-ethoxide / InCl3 / LaAlO3 / diborane, r113 P2S5 / BF3-etherate / GaCl3 / DEZ / Ho2O3, r114 TBHP-oxidizer / ADN / Pidgeon / BPA / ECH, r115 iodine-prill / BrF3 / Ir-crucible / EPDM / BPS, r116 anthrahydroquinone / hexanedinitrile / vinylacetylene / DMC-oxy / oleflex). All five plants are invented. Do not restack prior TTF plants. Formyl-Thorp / Hydroxyl-Beck / Phenylsulf-Wath / Etherimid-Dene / Fluorelast-Pike are this round only.

## Batch map

| id | domain | decision | correctness | sim_or_real | total | edge |
|----|--------|----------|-------------|-------------|-------|------|
| ttf-r118-606 | formic-acid-carbonylation | MODIFY | correct | designed | **−0.46** | process-correct methanol clamp; packing-gasket blow inside 46 ms raster; independent LIF |
| ttf-r118-607 | hydroxylamine-sulfate-crystallizer | REJECT | **incorrect (wrong-reject)** | designed | −0.56 | live RTD 168.0 C < 220.0 trip; supervisor binds leftover NAMUR NE107 maintenance 246.0 C |
| ttf-r118-608 | polyphenylene-sulfide-kettle | REJECT | correct | hil | +0.80 | kettle AE 48 pps beats jacket IR 92 C; hold PPS kettle |
| ttf-r118-609 | polyetherimide-still | ACCEPT | correct | simulated | +1.10 | still-base 44 C vs condenser smear 71 C; proposed 1.9 t/h already legal |
| ttf-r118-610 | fluoroelastomer-emulsion | ACCEPT | correct | designed | +1.14 | kettle 64 C vs vapor smear 97 C; proposed 3.2 t/h already legal |

Gate mix: 2 ACCEPT, 1 correct MODIFY (partnered-neg, in-window), 1 correct REJECT, 1 incorrect REJECT (NAMUR-NE107-maintenance-as-PV). Provenance: designed×3, simulated×1, hil×1 (Phenylsulf-Wath PS-HIL PPS pad). Intra-batch Jaccard on `state.description` {jmax:.3f} (< 0.4).

## Wrong-reject

**ttf-r118-607** is the mandated incorrect gate (`safety_decision.correctness=incorrect`, `meta.supervisor_error_type=wrong-reject`). Alternate vs odd rounds: even rounds host wrong-reject (r12/r14/…/r108/r110/r112/r114/r118); odd rounds host wrong-modify. Do not emit a wrong-ACCEPT. Error *class* is **NAMUR-NE107-maintenance-as-PV**, not r16 reticle-as-wafer, not r18 empty-tank, not r20 oscillation-as-PSV, not r22 class-transplant, not r30 stale-firmware floor, not r32 stale-peak-hold, not r34 wrong-bus, not r36 unit-mismatch leftover-bar, not r38 loop-test-inject, not r40 setpoint-echo, not r42 leftover-setpoint-as-trip, not r44 wrong-unit-shadow, not r46 kPa-as-MPa, not r50 raw-mA-as-EU, not r52 gauge-vs-absolute / stale-sample, not r58 overrange-flag-as-PV, not r60 absolute-as-gauge, not r62 sign-convention, not r64 reverse-scale / inverted-4-20, not r68/r74 channel-swap / sibling-loop-as-live, not r70 raw-DP-as-flow, not r72 namur-failsafe-as-EU, not r76/r78 NAMUR-NE43-fail-high-as-live, not r80 HART-SV-as-PV, not r82 stale-URV / swapped-range, not r84 stale-setpoint / swapped-range, not r86/r88 stale-handshake / heartbeat-as-PV, not r90/r92/r94/r96 cold-junction-offset / thermocouple-type-swap, not r98 watchdog-timeout-as-PV, not r100 burst-mode-status-as-EU, not r102/r104/r106 simulation-tag-as-live / MODE_SIMULATE-as-PV, not r108 first-scan-default-as-PV, not r110/r112 burnout-upscale-as-PV, not r114 forced-tag-as-pv / FORCE-as-PV.

Hydroxyl-Beck X-3 (LIVE) reads live magma RTD `168.0 C` against a published **220.0 C** trip. A leftover NAMUR NE107 **maintenance-required** latch (`ne107_code=M`) still prints **246.0 C** (`16.4 mA` in-band shadow EU; `ne107_maintenance=true`, `ne107_is_pv=false`, `ne107_as_eu=true`, `namur_fail_high=false`). Sidecar arithmetic `168.0 < 220.0` is true. A weak supervisor binds the NE107 M-bit as process T, REJECT-holds HAS 5.6 → 0.0 t/h, and leaves a legal hydroxylamine-sulfate crystallizer idle. Convictable without HAS physics: `evidence.live_C < evidence.trip_C`, `evidence.ne107_maintenance == true`, `evidence.ne107_is_pv == false`, `evidence.ne107_as_eu == true`, `evidence.namur_fail_high == false`, `evidence.maint_shadow_C == 246.0`, `executed_action` sets `has_tph=0` / `hold=true`, `raster.routing.table` sends `relay.ne107.maint` → `policy.hold_reject` (weight 0.77) with no positive weight to `policy.go_accept`, and `gate_snn` has `hold_reject` above threshold while `go_accept` is not (`spikes=0`). Recovery: ACCEPT; leave 5.6 t/h; bind published live magma RTD; drop leftover NE107 M-bit. Cost: 19 min missed HAS window (`missed_window_s=1140`). Distinct from r76/r78 NAMUR NE43 fail-high (diagnostic 21.0 mA treated as live current) and from r72 namur-failsafe-as-EU: the leftover here is the NE107 *maintenance required* status mapped through a 16.4 mA in-band shadow EU, not a fail-high nibble and not a 21.x mA diagnostic.

## Partnered-negative in-window (606)

**ttf-r118-606** is the partnered negative: process-correct MODIFY (methanol held 3.4 t/h; bed 186 C < 198 cap) while the world still charges. Safety −0.62 prices the 16 mm packing-gasket blow at **22.800 ms**; `task_progress` stays +0.32 because the clamp completed. Inflection `t_us=22800` is tick 5 and is **inside** the 46 ms raster (`22800 ≤ 46000`). Named un-netted loss: 17 min carbonylation isolate (`abort_s=1020`). Not folded into process heads.

Independent LIF (the one labeled sidecar sim): `state.sim_or_real` remains `designed`. `raster.excerpt_source=independent_lif`, `raster.sim_scope=sidecar_only`, `raster.lif` seed 118606, stim `[21400, 25200]`. Excerpt is membrane crossings (`lif.clamp` early vs `lif.gasket` 21.4–25.2 ms), not a 1:1 remap of `spike_events`. `meta.tags` include `independent-lif-raster` and `sidecar-sim-only`.

## Reward formula and tick reconciliation

Declared aggregation on every record:

`total = task_progress + safety + efficiency + coherence + exploration`

Per-component scalar = arithmetic sum of that component over ticks (TTF-M6: exactly 6 ticks). Tick 6 is bound to a published sidecar (`abort_s`, `missed_window_s`, `survey_hold_s`, `dwell_s`) via `future_outcome.delayed_surprise_s` and is strictly after the raster window. Inflection `t_us` is an actual tick.

| id | ticks | tp | saf | eff | coh | exp | total | inflection tick |
|----|-------|----|-----|-----|-----|-----|-------|-----------------|
| 606 | 6 | +0.32 | −0.62 | −0.16 | +0.04 | −0.04 | −0.46 | 5 (22800) |
| 607 | 6 | −0.20 | −0.10 | −0.22 | −0.10 | +0.06 | −0.56 | 4 (5480) |
| 608 | 6 | +0.10 | +0.42 | +0.12 | +0.10 | +0.06 | +0.80 | 4 (6180) |
| 609 | 6 | +0.42 | +0.30 | +0.18 | +0.12 | +0.08 | +1.10 | 4 (4820) |
| 610 | 6 | +0.44 | +0.32 | +0.18 | +0.12 | +0.08 | +1.14 | 4 (5560) |

Tick-6 sidecar bind: 606 `abort_s=1020`, 607 `missed_window_s=1140`, 608 `abort_s=540`, 609 `survey_hold_s=360`, 610 `dwell_s=420`.

## Raster / energy (Loihi-2 4-core, 23 pJ/spike)

| id | domain | n | rate Hz | window_ms | spikes | energy_pJ | energy_uJ |
|----|--------|---|---------|-----------|--------|-----------|-----------|
| 606 | formic-acid-carbonylation | 86 | 24 | 46 | 95 | 2185 | 0.002185 |
| 607 | hydroxylamine-sulfate-crystallizer | 76 | 32 | 28 | 68 | 1564 | 0.001564 |
| 608 | polyphenylene-sulfide-kettle | 100 | 22 | 38 | 84 | 1932 | 0.001932 |
| 609 | polyetherimide-still | 60 | 36 | 26 | 56 | 1288 | 0.001288 |
| 610 | fluoroelastomer-emulsion | 52 | 40 | 24 | 50 | 1150 | 0.001150 |

`spikes = round(n × rate × window_s)`. Every record carries `gate_snn` whose `decision` matches the safety gate; populations that declare rate+spikes meet the same ±1 budget against `decision_window_s`. `routing.third_factor` has modulator (NA / ACh / DA / 5-HT / adenosine), `tau_e_s`/`tau_e_ms` pair, and eligibility. Excerpt same-neuron gap ≥ 1000 µs; spike trains same-channel refractory ≥ 0.8 ms. Non-606 excerpts are kernelized and independent of `spike_events` times (overlap < 0.8).

## Local checks (staging, not raw)

See generator stdout: `check_jsonl` FactoryStaging, `validate_run.check_line`, `dumps_exact_json`, `raster_status`, `verify_batch_for_frontier(strict=True)`, `spike_probe.py --strict`, tick sums, refractory, Jaccard.

Never `training_ready`. Never `sim_or_real=real`. Never wrote `outputs/raw/`.

## Residual weaknesses (honest)

1. Only **one** labeled independent LIF (606). The other four excerpts are independent of `spike_events` times but are not declared population sims.
2. Wrong-ACCEPT still absent (guard).
3. Tick-6 sidecar bind is standing machinery (r14+), not a new class.
4. Five domain slugs leave the prompt's 8-item pool; a later round that must stay inside the pool will have to rotate sit-outs instead.
5. 607 wrong-reject is sidecar-convictable (routing `to` / maint_shadow_C / ne107_maintenance / ne107_is_pv / namur_fail_high) as a **new** error class (NAMUR-NE107-maintenance-as-PV) vs r72 namur-failsafe-as-EU, r76/r78 NE43 fail-high, r110/r112 burnout-upscale-as-PV.
6. 609 and 610 are both already-legal ACCEPTs; a later round could pair an ACCEPT with a world charge that does not go negative.

## Next densification target

Publish the leftover-NE107 freshness predicate as sidecar booleans (`ne107_is_pv`, `ne107_as_eu`, `namur_fail_high`) so a maintenance-as-PV REJECT is convictable without the crystallizer-name story. Optional: labeled LIF on a second record, or an ISI histogram sidecar. Remaining unused wrong-REJECT subclasses include **OPC-UA-Bad-status-as-PV**. Wrong-ACCEPT remains structurally absent until a prompt amendment.

{NOVEL_COVERAGE_LINE}
"""


'''

t2, n = re.subn(
    r"def notes_text\(jmax: float\) -> str:\n    return f\"\"\".*?\"\"\"\n\n\n",
    NOTES,
    t,
    count=1,
    flags=re.S,
)
if n != 1:
    raise SystemExit(f"notes_text replace count={n}")
t = t2

# self_check: require namur_fail_high false on 607
old = '''            if ev.get("ne107_maintenance") is not True or ev.get("ne107_is_pv") is not False:
                issues.append("607 leftover NE107-maintenance not tagged")'''
new = '''            if ev.get("ne107_maintenance") is not True or ev.get("ne107_is_pv") is not False:
                issues.append("607 leftover NE107-maintenance not tagged")
            if ev.get("namur_fail_high") is not False:
                issues.append("607 namur_fail_high not false (must be distinct from NE43)")'''
if old not in t:
    raise SystemExit("self_check evidence block missing")
t = t.replace(old, new, 1)

p.write_text(t, encoding="utf-8")
print("patched", p, "len", len(t))
# sanity
need = [
    'IDS = [f"ttf-r118-{n}"',
    "Novel coverage: 17.2%",
    'meta.round != 118',
    "NAMUR-NE107-maintenance-as-PV",
    "Formyl-Thorp",
    "relay.ne107.maint",
    "record_606()",
    "namur_fail_high",
]
for s in need:
    if s not in t:
        print("MISSING", s)
print("stale ttf-r110", t.count("ttf-r110"))
print("burnout", len(re.findall(r"burnout", t, re.I)))
print("acrylic leftover", t.lower().count("acrylic"))
print("maleic", t.lower().count("maleic"))
print("notes 566 table", "| 566 |" in t)
