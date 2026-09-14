#!/usr/bin/env python3
"""Clone r113 → r119. Writes gen_r119.py only. Never outputs/raw/."""
from __future__ import annotations

from pathlib import Path

SRC = Path("/tmp/ttf-r113/gen_r113.py")
DST = Path("/tmp/ttf-r119/gen_r119.py")

NOTES = r'''def notes_text(jmax: float, jprior: float) -> str:
    return f"""# Thalamic Trajectory Factory — NOTES-r119

- Factory: `thalamic-trajectory-factory`
- Run label: `2026-09-02-final-heavy`
- Generator: `grok-4.6`
- Channel: SuperGrok Heavy consumer chat (RM-793 research-only)
- Quota: 5
- Quality: Q=5
- IDs: `ttf-r119-611` … `ttf-r119-615`
- Domains this batch: `dimethyl-sulfate-esterifier`, `sulfur-tetrafluoride-reactor`, `lutetium-oxyorthosilicate-puller`, `europium-oxalate-precipitator`, `cesium-iodide-bridgman`

These five domain slugs sit outside the prompt 8-pool and outside staged r13–r115 occupancy (jsonl SoT) plus in-flight gens r109 / r114 / r116 / r118 (`methanol-to-olefins-reactor` / `tert-butyl-hydroperoxide-oxidizer` / `anthrahydroquinone-oxidizer` / r118 restack of r110 glyoxal). Distinct from r111 phthalic-anhydride-oxidizer / TBHP-column / LaF3, r112 RuO4 / Ta-ethoxide / InCl3, r113 P4S10 / BF3-etherate / GaCl3 / DEZ / Ho2O3, r115 iodine-prill / BrF3 / iridium-crucible / EPDM / BPS. All five plants are invented (Dmsest-Aysgarth, Tetraf-Bainbridge, Lsoce-Westburton, Euoxal-Carperby, Csidide-Redmire). Do not restack prior TTF plants.

## Batch map

| id | domain | decision | correctness | sim_or_real | total | edge |
|----|--------|----------|-------------|-------------|-------|------|
| ttf-r119-611 | dimethyl-sulfate-esterifier | MODIFY | correct | designed | **−0.44** | process-correct methanol clamp; packing-gland dump inside 42 ms raster; independent LIF |
| ttf-r119-612 | sulfur-tetrafluoride-reactor | MODIFY | **incorrect (wrong-modify / gauge-as-absolute)** | designed | −0.68 | live 2.80 bar(a) > 2.40 cap; 92.0 percent-open SF4 OPEN on leftover gauge 1.787 bar(g) |
| ttf-r119-613 | lutetium-oxyorthosilicate-puller | REJECT | correct | hil | +0.80 | AE 58 pps beats heater 1.9 kW; hold tap |
| ttf-r119-614 | europium-oxalate-precipitator | ACCEPT | correct | simulated | +1.06 | liquor 18.6 C vs jacket 41 C; proposed 1.4 t/h already legal |
| ttf-r119-615 | cesium-iodide-bridgman | ACCEPT | correct | designed | +1.14 | ampoule 842 C vs O2 8.4 vol%; proposed 2.6 kg/h already legal |

Gate mix: 2 ACCEPT, 1 correct MODIFY (partnered-neg, in-window), 1 incorrect MODIFY (gauge-as-absolute), 1 correct REJECT. Provenance: designed×3, simulated×1, hil×1 (Lsoce-Westburton LW-HIL LSO puller). Intra-batch Jaccard on `state.description` {jmax:.3f} (max vs prior staged {jprior:.3f}).

## Wrong-modify

**ttf-r119-612** is the mandated incorrect gate (`safety_decision.correctness=incorrect`, `meta.supervisor_error_type=wrong-modify`). Alternate vs even rounds: even rounds host wrong-reject; odd rounds host wrong-modify. This is **gauge-as-absolute** (live SF4 reactor PT 2.80 bar(a) over 2.40 bar(a) cap; leftover DCS tag still publishes gauge 1.787 bar(g) = 2.80 − 1.013; supervisor treats leftover gauge as if it were absolute and OPENS the SF4 stem 78.0 → 92.0 because 1.787 looks under 2.40, while live 2.80 stays over 2.40). Not r13/r19 wrong-axis, not r14/r23 wrong-loop, not r21 wrong-polarity, not r24 under-clamp, not r25/r29/r31/r63 wrong-phase, not r33/r35 over-clamp, not r39 extra-PLC-scan clamp-too-late, not r53/r55/r57 stale-sample / lagged-tag, not r59/r65/r67 wrong-string / idle-bank, not r69 split-range-wrong-half, not r71/r73/r75/r77 wrong-unit / lagged-bus (those convert the *same* live transmitter), not r79/r81 selector-wrong-leg, not r83 wrong-bank polarity invert, not r85 ratio-pair invert, not r87 wrong-deadband, not r89 dual-range-wrong-band, not r91 wrong-polarity-fresh-tag, not r93 valve-travel as PV, not r95/r97 lead-lag invert, not r99/r107 feedforward-as-feedback, not r101/r111/r113 percent-open vs percent-closed, not r103/r105 shadow-setpoint leftover faceplate, not r115 wrong-hysteresis on a split-range valve. Distinct from r71-r77: the leftover tag is a gauge echo of the *same* vessel, offset by 1.013 bar, not a lagged engineering-unit conversion of the live loop. Distinct from even-round leftover-SP-as-trip (r42/r84), which REJECT-holds a legal PV; this round MODIFY-opens an illegal PV. Do not emit a wrong-ACCEPT.

Tetraf-Bainbridge TB-6 / Reactor R-4 (LIVE) reads live absolute **2.80 bar(a)** against a **2.40 bar(a)** cap. Live stem is **78.0 percent-open**. Leftover tag `R4_SF4.PG` is `LEFTOVER` at **1.787 bar(g)**. Sidecar arithmetic `2.80 > 2.40` is true, `gauge_is_pv == false` is true, and `1.787 == 2.80 − 1.013` is true. A timely MODIFY at `t_gate_us=6120` cuts live stem **78.0 → 34.0 percent-open**. A weak supervisor binds leftover gauge as if it were absolute and MODIFY-opens **78.0 → 92.0 percent-open**. Live stays **2.80 > 2.40**. Convictable without SF4 physics: `evidence.live_bara > evidence.cap_bara`, `evidence.gauge_is_pv == false`, `evidence.shadow_barg == evidence.live_bara - evidence.atm_bar`, `evidence.gauge_tag_status == LEFTOVER`, `executed_action` sets `bind_gauge_as_absolute=true` and `valve_po_pct=92.0` with `live_bara=2.80`, `raster.routing.table` sends `relay.pg.shadow` → `policy.gauge_open` (weight 0.74) with no positive weight to `policy.abs_cut`, and `gate_snn` has `gauge_open` above threshold while `abs_cut` is not. Recovery: MODIFY live stem 78.0 → 34.0 percent-open on R-4 at t_gate; leave N2 carrier at 4.2 t/h; leave R4_SF4.PG unbound. Cost: 12 min SF4 dump (`abort_s=720`).

## Partnered-negative in-window (611)

**ttf-r119-611** is the partnered negative: process-correct MODIFY (methanol held 8.4 t/h; DMS mist 5.8 g/Nm3 <= 6.5 cap) while the world still charges. Safety −0.60 prices the packing-gland dump at **22.400 ms**; `task_progress` stays +0.32 because the clamp completed. Inflection `t_us=22400` is tick 5 and is **inside** the 42 ms raster (`22400 ≤ 42000`). Named un-netted loss: 15 min gland isolate (`abort_s=900`). Not folded into process heads.

Independent LIF (the one labeled sidecar sim): `state.sim_or_real` remains `designed`. `raster.excerpt_source=independent_lif`, `raster.sim_scope=sidecar_only`, `raster.lif` seed 119611, stim `[22000, 25000]`. Excerpt is membrane crossings (`lif.clamp` early vs `lif.gland` 22–25 ms), not a 1:1 remap of `spike_events`. `meta.tags` include `independent-lif-raster` and `sidecar-sim-only`.

## Reward formula and tick reconciliation

Declared aggregation on every record:

`total = task_progress + safety + efficiency + coherence + exploration`

Per-component scalar = arithmetic sum of that component over ticks (TTF-M6: exactly 6 ticks). Tick 6 is bound to a published sidecar (`abort_s`, `survey_s`, `dwell_s`) via `future_outcome.delayed_surprise_s` and is strictly after the raster window. Inflection `t_us` is an actual tick.

| id | ticks | tp | saf | eff | coh | exp | total | inflection tick |
|----|-------|----|-----|-----|-----|-----|-------|-----------------|
| 611 | 6 | +0.32 | −0.60 | −0.16 | +0.04 | −0.04 | −0.44 | 5 (22400) |
| 612 | 6 | −0.22 | −0.24 | −0.18 | −0.10 | +0.06 | −0.68 | 4 (6120) |
| 613 | 6 | +0.10 | +0.42 | +0.12 | +0.10 | +0.06 | +0.80 | 4 (7640) |
| 614 | 6 | +0.40 | +0.28 | +0.18 | +0.12 | +0.08 | +1.06 | 4 (7840) |
| 615 | 6 | +0.44 | +0.30 | +0.20 | +0.12 | +0.08 | +1.14 | 4 (5640) |

Tick-6 sidecar bind: 611 `abort_s=900`, 612 `abort_s=720`, 613 `abort_s=480`, 614 `survey_s=360`, 615 `dwell_s=240`.

## Raster / energy (Loihi-2 4-core, 23 pJ/spike)

| id | domain | n | rate Hz | window_ms | spikes | energy_pJ | energy_uJ |
|----|--------|---|---------|-----------|--------|-----------|-----------|
| 611 | dimethyl-sulfate-esterifier | 76 | 26 | 42 | 83 | 1909 | 0.001909 |
| 612 | sulfur-tetrafluoride-reactor | 88 | 34 | 28 | 84 | 1932 | 0.001932 |
| 613 | lutetium-oxyorthosilicate-puller | 120 | 20 | 46 | 110 | 2530 | 0.002530 |
| 614 | europium-oxalate-precipitator | 48 | 42 | 28 | 56 | 1288 | 0.001288 |
| 615 | cesium-iodide-bridgman | 80 | 28 | 24 | 54 | 1242 | 0.001242 |

`spikes = round(n × rate × window_s)`. Every record carries `gate_snn` whose `decision` matches the safety gate; populations that declare rate+spikes meet the same ±1 budget against `decision_window_s`. `routing.third_factor` has modulator (NA / ACh / DA / 5-HT / adenosine), `tau_e_s`/`tau_e_ms` pair, and eligibility. Excerpt same-neuron gap ≥ 1000 µs; spike trains same-channel refractory ≥ 0.8 ms. Non-611 excerpts are kernelized and independent of `spike_events` times (overlap < 0.8).

## Local checks (staging, not raw)

See generator stdout: `check_jsonl` FactoryStaging, `validate_run.check_line`, `dumps_exact_json`, `raster_status`, `verify_batch_for_frontier(strict=True)`, `spike_probe.py --strict`, tick sums, refractory, Jaccard.

Never `training_ready`. Never `sim_or_real=real`. Never wrote `outputs/raw/`.

## Residual weaknesses (honest)

1. Only **one** labeled independent LIF (611). The other four excerpts are independent of `spike_events` times but are not declared population sims.
2. Wrong-ACCEPT still absent (guard).
3. Tick-6 sidecar bind is standing machinery (r14+), not a new class.
4. Five domain slugs leave the prompt's 8-item pool; a later round that must stay inside the pool will have to rotate sit-outs instead.
5. 614 and 615 are both already-legal ACCEPTs; a later round could pair one ACCEPT with a world charge that does not go negative.

## Next densification target

Labeled LIF on a second record, or an ISI histogram sidecar. Remaining unused wrong-MODIFY subclasses include **dewpoint-as-drybulb** and **wet-basis as dry-basis** once gauge-as-absolute is staged. Wrong-ACCEPT remains structurally absent until a prompt amendment.

Novel coverage: 17.4%
"""
'''

SELF_CHECK_612 = '''        if rec["id"] == "ttf-r119-612":
            ev = rec["proposed_action"]["evidence"]
            if not (ev["live_bara"] > ev["cap_bara"]):
                issues.append("612 live abs P not over cap")
            if ev.get("gauge_is_pv") is not False:
                issues.append("612 gauge_is_pv should be false")
            if abs(ev["shadow_barg"] - (ev["live_bara"] - ev["atm_bar"])) > 1e-6:
                issues.append("612 leftover gauge is not live_bara - atm")
            if ev.get("gauge_tag_status") != "LEFTOVER":
                issues.append("612 gauge tag not LEFTOVER")
            if rec["executed_action"]["parameters"].get("bind_gauge_as_absolute") is not True:
                issues.append("612 bind_gauge_as_absolute not true")
            if rec["executed_action"]["parameters"].get("valve_po_pct") != 92.0:
                issues.append("612 valve should open to 92.0")
            if rec["executed_action"]["parameters"].get("live_bara") != 2.80:
                issues.append("612 live abs P should stay 2.80")
            if "recovery" not in rec["future_outcome"]:
                issues.append("612 missing recovery")
            table_to = {row["to"] for row in rec["raster"]["routing"]["table"]}
            if "policy.abs_cut" in table_to:
                issues.append("612 routing still has abs_cut")
            if "policy.gauge_open" not in table_to:
                issues.append("612 routing missing gauge_open")
            if "gauge-as-absolute" not in rec["meta"]["tags"]:
                issues.append("612 missing gauge-as-absolute tag")
'''


def splice_fn(text: str, name: str, next_name: str) -> tuple[str, str, str]:
    start = text.index(f"def {name}(")
    end = text.index(f"def {next_name}(")
    return text[:start], text[start:end], text[end:]


def main() -> None:
    src = SRC.read_text()
    src = src.replace("range(581, 586)", "range(611, 616)")
    for a, b in [(585, 615), (584, 614), (583, 613), (582, 612), (581, 611)]:
        src = src.replace(str(a), str(b))
    src = src.replace("r113", "r119")
    src = src.replace('("round", 113)', '("round", 119)')
    src = src.replace('if rec["meta"]["round"] != 113:', 'if rec["meta"]["round"] != 119:')
    src = src.replace(
        '"""Prior staged batches + in-flight gens are global occupancy. r119 must not reuse them."""',
        '"""Prior staged batches + in-flight gens are global occupancy. r119 must not reuse them."""',
    )

    old_dom = '''THIS_DOMAINS = {
    "phosphorus-pentasulfide-kettle",
    "boron-trifluoride-etherate-kettle",
    "gallium-trichloride-bubbler",
    "diethylzinc-bubbler",
    "holmium-oxide-calciner",
}
THIS_PLANTS = (
    "Pentasulf-Reen",
    "Borether-Ghyll",
    "Gallichl-Tarn",
    "Zincethyl-Beck",
    "Holmox-Wath",
)'''
    new_dom = '''THIS_DOMAINS = {
    "dimethyl-sulfate-esterifier",
    "sulfur-tetrafluoride-reactor",
    "lutetium-oxyorthosilicate-puller",
    "europium-oxalate-precipitator",
    "cesium-iodide-bridgman",
}
THIS_PLANTS = (
    "Dmsest-Aysgarth",
    "Tetraf-Bainbridge",
    "Lsoce-Westburton",
    "Euoxal-Carperby",
    "Csidide-Redmire",
)'''
    if old_dom not in src:
        raise SystemExit("THIS_DOMAINS block missing after remap")
    src = src.replace(old_dom, new_dom, 1)

    # Domain / plant swaps (longest first).
    pairs = [
        ("phosphorus-pentasulfide-kettle", "dimethyl-sulfate-esterifier"),
        ("boron-trifluoride-etherate-kettle", "sulfur-tetrafluoride-reactor"),
        ("gallium-trichloride-bubbler", "lutetium-oxyorthosilicate-puller"),
        ("diethylzinc-bubbler", "europium-oxalate-precipitator"),
        ("holmium-oxide-calciner", "cesium-iodide-bridgman"),
        ("Pentasulf-Reen", "Dmsest-Aysgarth"),
        ("Borether-Ghyll", "Tetraf-Bainbridge"),
        ("Gallichl-Tarn", "Lsoce-Westburton"),
        ("Zincethyl-Beck", "Euoxal-Carperby"),
        ("Holmox-Wath", "Csidide-Redmire"),
        ("PR-3", "DA-3"),
        ("BG-6", "TB-6"),
        ("GT-HIL", "LW-HIL"),
        ("ZB-4", "EC-4"),
        ("HW-5", "CR-5"),
        ("Kettle K-2", "Esterifier E-2"),
        ("kettle K-2", "esterifier E-2"),
        ("Bubbler U-7", "Precipitator V-7"),
        ("bubbler U-7", "precipitator V-7"),
        ("Calciner C-8", "Bridgman F-8"),
        ("calciner C-8", "Bridgman F-8"),
        ("Bubbler B-2", "Puller P-2"),
        ("bubbler B-2", "puller P-2"),
        ("Kettle R-4", "Reactor R-4"),
        ("kettle R-4", "reactor R-4"),
    ]
    for a, b in pairs:
        src = src.replace(a, b)

    # Record 611 chemistry / channels.
    rec611 = [
        ("p4s10.vapor.gNm3", "dms.mist.gNm3"),
        ("pt.p4.bar", "pt.meoh.bar"),
        ("ae.seal.dump", "ae.gland.dump"),
        ("lif.seal", "lif.gland"),
        ("p4s10_cap_gNm3", "dms_cap_gNm3"),
        ("observed_p4s10_gNm3", "observed_dms_gNm3"),
        ("p4_liquor_tph", "meoh_tph"),
        ("p4_bar", "meoh_bar"),
        ("p4_cap_bar", "meoh_cap_bar"),
        ("p4s10_gNm3", "dms_gNm3"),
        ("p4s10", "dms_mist"),
        ("P4S10 vapor", "DMS mist"),
        ("P4S10", "DMS"),
        ("P4 liquor", "methanol"),
        ("P4-liquor", "methanol"),
        ("P4-header", "methanol-header"),
        ("P4 header", "methanol header"),
        ("P4 Coriolis", "methanol Coriolis"),
        ("Yellow-phosphorus header", "Methanol header"),
        ("yellow-phosphorus header", "methanol header"),
        ("pentasulfide cook", "esterification pass"),
        ("pentasulfide UV", "dimethyl-sulfate UV"),
        ("off-gas UV P4S10 pentasulfide UV cell", "off-gas UV dimethyl-sulfate mist cell"),
        ("agitator-seal", "packing-gland"),
        ("agitator seal", "packing gland"),
        ("seal dump", "gland dump"),
        ("seal isolate", "gland isolate"),
        ("seal failure", "gland failure"),
        ("P4-liquor clamp bias", "methanol clamp bias"),
        ("cruise_p4_liquor", "cruise_meoh"),
        ("clamped_p4_liquor", "clamped_meoh"),
        ("policy.p4_clamp", "policy.meoh_clamp"),
        ("policy.p4-clamp", "policy.meoh-clamp"),
        ("thalamic-relay.p4s10-vapor", "thalamic-relay.dms-mist"),
        ("relay.p4s10.vapor", "relay.dms.mist"),
        ("relay.pt.p4", "relay.pt.meoh"),
        ("relay.ae.seal", "relay.ae.gland"),
        ("p4_clamp", "meoh_clamp"),
        ("header_hold", "header_hold"),
        ("seal_veto", "gland_veto"),
        ("P4S10-wet liquor", "DMS-wet methanol"),
        ("P4S10-wet", "DMS-wet"),
        ("liquor clamp", "methanol clamp"),
        ("UV cell reads 9.4 g/Nm3 DMS over the 6.5 g/Nm3 stop.",
         "UV already reports dimethyl-sulfate mist 9.4 g/Nm3 versus a 6.5 g/Nm3 condenser ceiling."),
    ]
    # Apply 611-ish replacements globally — some strings are unique.
    for a, b in rec611:
        src = src.replace(a, b)

    # Record 613 HIL puller.
    rec613 = [
        ("ae.b2.pps", "ae.p2.pps"),
        ("p.bub.kW", "p.heat.kW"),
        ("quartz AE puck on bubbler B-2", "quartz AE puck on puller P-2"),
        ("Bubbler RF remains", "Heater kW remains"),
        ("bubbler RF remains", "heater kW remains"),
        ("Legal action\n                parks the 2.6 kW tap at zero; a power-first dispatch would energize a noisy\n                ampoule. RF kW meters do not outrank the puck.",
         "Legal action\n                parks the 2.6 kW tap at zero; a power-first dispatch would energize a noisy\n                LSO crucible. Heater kW meters do not outrank the puck."),
        ("Keep B-2 from dispatching a growling quartz ampoule while bubbler RF remains under",
         "Keep P-2 from dispatching a growling LSO crucible while heater kW remains under"),
        ("this HIL gallium-trichloride bubbler bus", "this HIL lutetium-oxyorthosilicate puller bus"),
        ("this HIL lutetium-oxyorthosilicate-puller bus", "this HIL lutetium-oxyorthosilicate puller bus"),
        ("GaCl3 bubbler", "LSO puller"),
        ("GaCl3-carrier MFC", "LSO-melt pyrometer"),
        ("ampoule wall TC", "crucible wall TC"),
        ("growling ampoule", "growling crucible"),
        ("growling quartz ampoule", "growling LSO crucible"),
        ("bubbler_kW", "heater_kW"),
        ("bubbler_cap_kW", "heater_cap_kW"),
        ("bubbler RF CT", "heater CT"),
        ("Bubbler RF", "Heater kW"),
        ("bubbler RF", "heater kW"),
        ("dispatch_bubbler", "dispatch_puller"),
        ("hold_bubbler", "hold_puller"),
        ("thalamic-relay.b2-ae", "thalamic-relay.p2-ae"),
        ("spikenaut.policy.b2-hold", "spikenaut.policy.p2-hold"),
        ("relay.ae.b2", "relay.ae.p2"),
        ("relay.p.bub", "relay.p.heat"),
        ("policy.b2_hold", "policy.p2_hold"),
        ("b2_hold", "p2_hold"),
        ("8 min bubbler reset", "8 min puller reset"),
        ("HIL bubbler", "HIL puller"),
        ("B-2 HIL indexed", "P-2 HIL indexed"),
        ("held B-2", "held P-2"),
        ("Ampoule inspected", "Crucible inspected"),
        ("ampoule", "crucible"),
        ("rectifier hash rather than a growling", "rectifier hash rather than a growling"),
        ("current story", "heater-kW story"),
        ("legal bubbler-RF header", "legal heater-kW header"),
        ("growling-ampoule", "growling-crucible"),
        ("ae-vs-kw", "ae-vs-heater"),
        ("simulated-dez-bubbler", "simulated-euox-precip"),
        ("bath-vs-jacket", "liquor-vs-jacket"),
        ("already-legal-holmia", "already-legal-csi"),
        ("bed-vs-oxygen", "ampoule-vs-oxygen"),
    ]
    for a, b in rec613:
        src = src.replace(a, b)

    # Record 614 precipitator.
    rec614 = [
        ("tc.bath.C", "tc.liquor.C"),
        ("dez_kgh", "euox_tph"),
        ("bath_C", "liquor_C"),
        ("bath_cap_C", "liquor_cap_C"),
        ("observed_bath_C", "observed_liquor_C"),
        ("proposed_dez_kgh", "proposed_euox_tph"),
        ("executed_dez_kgh", "executed_euox_tph"),
        ("feed_dez_14", "feed_euox_14"),
        ("carrier_slm", "seed_slm"),
        ("carrier_cap_slm", "seed_cap_slm"),
        ("carrier N2 MFC", "seed-slurry MFC"),
        ("DEZ mass-flow", "oxalate mass-flow"),
        ("bath TC well on DEZ bubbler", "liquor TC well on Eu oxalate precipitator"),
        ("bath TC well", "liquor TC well"),
        ("diethylzinc-bubbler bus", "europium-oxalate precipitator bus"),
        ("europium-oxalate-precipitator bus", "europium-oxalate precipitator bus"),
        ("DEZ feed", "oxalate feed"),
        ("DEZ bubbler", "oxalate precipitator"),
        ("kg/h DEZ", "t/h oxalate"),
        ("1.4 kg/h", "1.4 t/h"),
        ("legal DEZ", "legal oxalate"),
        ("quiet MOCVD train", "quiet europia train"),
        ("bath <= 32.0 C", "liquor <= 32.0 C"),
        ("Bath-first", "Liquor-first"),
        ("bath-first", "liquor-first"),
        ("bath TC", "liquor TC"),
        ("Bath 18.6", "Liquor 18.6"),
        ("bath 18.6", "liquor 18.6"),
        ("policy.dez_go", "policy.euox_go"),
        ("policy.dez-go", "policy.euox-go"),
        ("thalamic-relay.dez-bath", "thalamic-relay.euox-liquor"),
        ("relay.tc.bath", "relay.tc.liquor"),
        ("dez_go", "euox_go"),
        ("legal_dez_stdp", "legal_euox_stdp"),
        ("dez_go bind", "euox_go bind"),
        ("bath-TC win", "liquor-TC win"),
        ("jacket_hold", "jacket_hold"),
        ("bath_veto", "liquor_veto"),
        ("U-7", "V-7"),
        ("simulated bubbler", "simulated precipitator"),
        ("bubbler pass", "precipitator pass"),
    ]
    for a, b in rec614:
        src = src.replace(a, b)

    # Record 615 Bridgman.
    rec615 = [
        ("ho2o3_tph", "csi_kgh"),
        ("tc.bed.C", "tc.amp.C"),
        ("bed_C", "amp_C"),
        ("bed_cap_C", "amp_cap_C"),
        ("observed_bed_C", "observed_amp_C"),
        ("executed_ho2o3_tph", "executed_csi_kgh"),
        ("hold_ho2o3_tph", "hold_csi_kgh"),
        ("2.6 t/h", "2.6 kg/h"),
        ("holmia stack", "CsI boule"),
        ("holmia calciner", "CsI Bridgman"),
        ("holmia run", "CsI run"),
        ("quiet holmia", "quiet CsI"),
        ("legal holmia", "legal CsI"),
        ("oxalate-feed Coriolis", "CsI-charge Coriolis"),
        ("bed TC well", "ampoule TC well"),
        ("bed well is 842", "ampoule well is 842"),
        ("Bed-first", "Ampoule-first"),
        ("bed-first", "ampoule-first"),
        ("Bed TC", "Ampoule TC"),
        ("bed TC", "ampoule TC"),
        ("Bed 842", "Ampoule 842"),
        ("bed 842", "ampoule 842"),
        ("thalamic-relay.holmia-bed", "thalamic-relay.csi-ampoule"),
        ("spikenaut.policy.holmia-go", "spikenaut.policy.csi-go"),
        ("relay.tc.bed", "relay.tc.amp"),
        ("policy.holmia_go", "policy.csi_go"),
        ("policy.holmia_hold", "policy.csi_hold"),
        ("holmia_go", "csi_go"),
        ("holmia_hold", "csi_hold"),
        ("accept_stdp; adenosine tags the bed-TC win as an already-legal holmia run",
         "accept_stdp; adenosine tags the ampoule-TC win as an already-legal CsI run"),
        ("already-legal holmia", "already-legal CsI"),
        ("hood reseq", "afterheater reseq"),
        ("zirconia-O2 publisher on this holmia calciner bus",
         "zirconia-O2 publisher on this CsI Bridgman bus"),
        ("zirconia-O2 publisher on this cesium-iodide-bridgman bus",
         "zirconia-O2 publisher on this CsI Bridgman bus"),
        ("the calciner is already legal", "the Bridgman furnace is already legal"),
        ("Run C-8 at 2.6 kg/h", "Run F-8 at 2.6 kg/h"),
        ("leave\n                the holmia calcine on schedule", "leave\n                the CsI boule on schedule"),
        ("stack limit", "lid limit"),
        ("oxygen-first veto would idle a quiet holmia stack",
         "oxygen-first veto would idle a quiet CsI boule"),
    ]
    for a, b in rec615:
        src = src.replace(a, b)

    # Patch record 612 in isolation.
    pre, body, post = splice_fn(src, "record_612", "record_613")
    r612 = [
        ("ft.ether.tph", "ft.n2.tph"),
        ("enc.po.pct", "pt.abs.bara"),
        ("tag.pc.pct", "tag.gauge.barg"),
        ("live_tc_C", "live_bara"),
        ("cap_tc_C", "cap_bara"),
        ("shadow_pc_pct", "shadow_barg"),
        ("pc_is_pv", "gauge_is_pv"),
        ("bind_percent_closed", "bind_gauge_as_absolute"),
        ("pc_tag_status", "gauge_tag_status"),
        ("ether_tph", "n2_tph"),
        ("correct_ether_tph", "correct_n2_tph"),
        ("R4_BF3.PC", "R4_SF4.PG"),
        ("R4_BF3.PO", "R4_SF4.PA"),
        ("R4_bf3_stem_direct", "R4_sf4_stem_direct"),
        ("R4_SF4.PG_as_percent_open", "R4_SF4.PG_as_absolute"),
        ("percent_closed_as_open", "gauge_as_absolute_open"),
        ("cruise_etherate_live", "cruise_sf4_live"),
        ("policy.pc_open", "policy.gauge_open"),
        ("policy.po_cut", "policy.abs_cut"),
        ("relay.pc.shadow", "relay.pg.shadow"),
        ("relay.enc.po", "relay.pt.abs"),
        ("thalamic-relay.bf3-percent-closed", "thalamic-relay.sf4-gauge"),
        ("spikenaut.policy.pc-open", "spikenaut.policy.gauge-open"),
        ("pc_open", "gauge_open"),
        ("po_cut", "abs_cut"),
        ("pair_veto", "pair_veto"),
        ("percent_closed_stdp", "gauge_as_absolute_stdp"),
        ("etherate", "sf4"),
        ("BF3-etherate", "SF4"),
        ("bf3", "sf4"),
        ("diethyl ether", "N2 carrier"),
        ("diethyl-ether Coriolis", "N2-carrier Coriolis"),
        ("percent-open vs percent-closed", "gauge-as-absolute"),
        ("percent-closed", "gauge"),
        ("percent-open", "percent-open"),
        ("Live-PO-first", "Abs-PT-first"),
        ("live-PO-first", "abs-PT-first"),
        ("Live-percent-open-first", "Live-absolute-first"),
        ("live-percent-open-first", "live-absolute-first"),
        ("leftover_pc", "leftover_pg"),
        ("wrong_pair", "wrong_pair"),
    ]
    for a, b in r612:
        body = body.replace(a, b)
    # Numeric PV swap inside 612 only (keep 78/92/34 stem percents).
    body = body.replace("94.0 C", "2.80 bar(a)")
    body = body.replace("94.0", "2.80")
    body = body.replace("82.0 C", "2.40 bar(a)")
    body = body.replace("82.0", "2.40")
    body = body.replace("22.0 percent-closed", "1.787 bar(g)")
    body = body.replace("22.0 leftover", "1.787 leftover")
    body = body.replace("22.0", "1.787")
    body = body.replace('("live_po_pct", 78.0)', '("live_po_pct", 78.0),\n                        ("atm_bar", 1.013)')
    # Fix evidence keys that still mention kettle TC.
    body = body.replace("kettle TC", "absolute PT")
    body = body.replace("kettle-TC", "absolute-PT")
    body = body.replace("live well 2.80 bar(a) versus 2.40", "live PT 2.80 bar(a) versus 2.40")
    body = body.replace("stale well", "stale gauge")
    body = body.replace("100 minus 78", "2.80 minus 1.013 atm")
    body = body.replace("100 − 78", "2.80 − 1.013")
    body = body.replace("scale invert that opens the valve because 1.787 looks starved",
                        "gauge-as-absolute bind that opens the valve because 1.787 looks under the 2.40 abs cap")
    body = body.replace("chasing 1.787 opens R-4 instead of cutting under 2.40 bar(a)",
                        "chasing 1.787 bar(g) as if it were bar(a) opens R-4 instead of cutting under 2.40 bar(a)")
    body = body.replace("LIVE etherating", "LIVE fluorinating")
    body = body.replace("ether 4.2 t/h", "N2 4.2 t/h")
    body = body.replace("live stem percent-open encoder", "live absolute PT")
    body = body.replace("leftover gauge tag", "leftover gauge PT tag")
    body = body.replace('"percent-open"', '"gauge-as-absolute"')
    body = body.replace('"percent-closed"', '"leftover-gauge"')
    # If those tags were already swapped by earlier percent-closed → gauge:
    if '"gauge-as-absolute"' not in body:
        body = body.replace(
            '''        [
            "modify",
            "wrong-gate",
            "gauge",
            "gauge",
            "sidecar-convictable",
            "designed",
        ]''',
            '''        [
            "modify",
            "wrong-gate",
            "gauge-as-absolute",
            "leftover-gauge",
            "sidecar-convictable",
            "designed",
        ]''',
        )
    src = pre + body + post

    # Rewrite 611 / 612 / 613 / 614 / 615 opening descriptions for Jaccard.
    src = src.replace(
        '"Dmsest-Aysgarth DA-3 esterifier E-2 UV cell reads 9.4 g/Nm3 DMS over the 6.5 g/Nm3 stop. "',
        '"Methanol header PT on Dmsest-Aysgarth DA-3 is still legal, but esterifier E-2 UV already reports dimethyl-sulfate mist 9.4 g/Nm3 versus a 6.5 g/Nm3 condenser ceiling. "',
    )
    # fallback if previous rec611 rewrite changed the sentence
    src = src.replace(
        '"Dmsest-Aysgarth DA-3 esterifier E-2 UV already reports dimethyl-sulfate mist 9.4 g/Nm3 versus a 6.5 g/Nm3 condenser ceiling. "',
        '"Methanol header PT on Dmsest-Aysgarth DA-3 is still legal, but esterifier E-2 UV already reports dimethyl-sulfate mist 9.4 g/Nm3 versus a 6.5 g/Nm3 condenser ceiling. "',
    )

    src = src.replace(
        "Yellow-phosphorus header PT sits at 3.2 bar, 2.0 shy of the 5.2 bar liquor-pump lock.",
        "Methanol header PT sits at 3.2 bar, 2.0 shy of the 5.2 bar liquor-pump lock.",
    )
    src = src.replace(
        "Vapor-first clamps methanol 14.0 t/h down to 8.4; header-first would keep 14.0 t/h",
        "Mist-first clamps methanol 14.0 t/h down to 8.4; header-first would keep 14.0 t/h",
    )
    src = src.replace("Vapor-first latches", "Mist-first latches")
    src = src.replace("Vapor-first", "Mist-first")
    src = src.replace("vapor-first", "mist-first")
    src = src.replace("Packing-gland AE stays mute until a later seal dump.",
                      "Packing-gland AE stays mute until a later gland dump.")
    src = src.replace("Agitator-seal AE stays mute until a later gland dump.",
                      "Packing-gland AE stays mute until a later gland dump.")

    # 614 opening
    src = src.replace(
        '"Euoxal-Carperby EC-4 simulated precipitator V-7 bath TC already sits at 18.6 C versus a "',
        '"Nucleation liquor on Euoxal-Carperby EC-4 precipitator V-7 already sits at 18.6 C versus a "',
    )
    src = src.replace(
        '"Euoxal-Carperby EC-4 simulated precipitator V-7 liquor TC already sits at 18.6 C versus a "',
        '"Nucleation liquor on Euoxal-Carperby EC-4 precipitator V-7 already sits at 18.6 C versus a "',
    )

    # 615 opening
    src = src.replace(
        '"Csidide-Redmire CR-5 Bridgman F-8 bed well is 842 C, 138 K shy of the "',
        '"Ampoule skin on Csidide-Redmire CR-5 Bridgman F-8 is 842 C, 138 K shy of the "',
    )
    src = src.replace(
        '"Csidide-Redmire CR-5 Bridgman F-8 ampoule well is 842 C, 138 K shy of the "',
        '"Ampoule skin on Csidide-Redmire CR-5 Bridgman F-8 is 842 C, 138 K shy of the "',
    )

    # 613 opening
    src = src.replace(
        '"Lsoce-Westburton LW-HIL quartz AE puck on puller P-2 is 58 pps, fourfold the 14 pps "',
        '"HIL quartz AE on Lsoce-Westburton LW-HIL puller P-2 already sits at 58 pps, fourfold the 14 pps "',
    )
    src = src.replace(
        '"Lsoce-Westburton LW-HIL quartz AE puck on bubbler B-2 is 58 pps, fourfold the 14 pps "',
        '"HIL quartz AE on Lsoce-Westburton LW-HIL puller P-2 already sits at 58 pps, fourfold the 14 pps "',
    )

    # Replace notes_text and 612 self-check.
    n0 = src.index("def notes_text(")
    n1 = src.index("def run_pipelines(")
    src = src[:n0] + NOTES + "\n\n" + src[n1:]

    s0 = src.index('        if rec["id"] == "ttf-r119-612":')
    s1 = src.index("        blob_l = blob.lower()")
    src = src[:s0] + SELF_CHECK_612 + "        " + src[s1:]

    # Evidence atm_bar must be present on proposed.evidence too.
    # Insert atm_bar beside live_bara in evidence OrderedDict if missing.
    if '("%s"' % "atm_bar" not in src and '("atm_bar", 1.013)' not in src.split("def record_612")[1].split("def record_613")[0]:
        chunk_pre, chunk, chunk_post = splice_fn(src, "record_612", "record_613")
        if '("atm_bar", 1.013)' not in chunk:
            chunk = chunk.replace(
                '("live_bara", 2.80)',
                '("live_bara", 2.80),\n                        ("atm_bar", 1.013)',
            )
        src = chunk_pre + chunk + chunk_post

    DST.write_text(src)
    print(f"wrote {DST} bytes={DST.stat().st_size}")


if __name__ == "__main__":
    main()
