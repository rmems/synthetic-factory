#!/usr/bin/env python3
"""Splice r53 header, records, self-check, and notes into the cloned generator."""
from pathlib import Path
import re

root = Path("/tmp/ttf-r53")
src = (root / "gen_r53.py").read_text()
records = (root / "_records.py").read_text()

# Header / paths
src = src.replace(
    '"""Emit TTF r39 JSONL (ttf-r39-211..215) into /tmp/ttf-r39/. Never writes outputs/raw/."""',
    '"""Emit TTF r53 JSONL (ttf-r53-281..285) into /tmp/ttf-r53/. Never writes outputs/raw/."""',
)
src = src.replace('OUT_DIR = Path("/tmp/ttf-r39")', 'OUT_DIR = Path("/tmp/ttf-r53")')
src = src.replace('BATCH_PATH = OUT_DIR / "batch-r39.jsonl"', 'BATCH_PATH = OUT_DIR / "batch-r53.jsonl"')
src = src.replace('NOTES_PATH = OUT_DIR / "NOTES-r39.md"', 'NOTES_PATH = OUT_DIR / "NOTES-r53.md"')
src = src.replace('("generated_at", "2026-09-02T17:25:00Z")', '("generated_at", "2026-09-02T17:45:00Z")')

old_doms = '''THIS_DOMAINS = {
    "sulfur-claus-furnace",
    "pvc-suspension-kettle",
    "corrugator-singlefacer",
    "once-through-steam-gen",
    "stenter-frame",
}
THIS_PLANTS = (
    "Pyrite-Gill",
    "Vinyl-Garth",
    "Flute-Wick",
    "Otter-Brae",
    "Tenter-Howe",
)'''
new_doms = '''THIS_DOMAINS = {
    "fluid-bed-roaster",
    "alkylation-contactor",
    "anode-bake-furnace",
    "blown-film-tower",
    "SX-mixer-settler",
}
THIS_PLANTS = (
    "Gossan-Weald",
    "Raffinate-Holt",
    "Butts-Howe",
    "Frostline-Kame",
    "Pregnant-Lea",
)'''
if old_doms not in src:
    raise SystemExit("THIS_DOMAINS block not found")
src = src.replace(old_doms, new_doms)

extra_domains = '''
    "mine-skip-winder",
    "geothermal-flash-separator",
    "HRSG-attemperator",
    "overland-conveyor",
    "galvanize-kettle",
    "mushroom-compost-tunnel",
    "fcc-riser-regenerator",
    "mri-helium-quench",
    "chocolate-conche",
    "uht-sterilizer",
    "ore-sinter-strand",
    "fcc-riser",
    "nickel-electrowinning",
    "hydrogen-PSA-bed",
    "cold-tandem-mill",
    "sulfur-claus-furnace",
    "pvc-suspension-kettle",
    "corrugator-singlefacer",
    "once-through-steam-gen",
    "stenter-frame",
    "delayed-coker",
    "tissue-yankee-dryer",
    "copper-flash-smelter",
    "hot-isostatic-press",
    "sinter-strand",
    "cold-pilger-mill",
    "yankee-tissue-dryer",
    "osb-hot-press",
    "midrex-dri-shaft",
    "brick-tunnel-kiln",
    "steam-methane-reformer",
    "Bayer-digester",
    "polyethylene-loop-reactor",
    "copper-electrorefining",
    "carbon-black-reactor",
    "asphalt-drum-mixer",
    "beamline-undulator",
    "nylon-spin-pack",
    "longwall-shearer",
    "esr-ingot-melt",
    "hip-isostatic-press",
    "fcc-riser-cracker",
    "galvanize-pot-line",
    "ethylene-cracker-coil",
    "stacker-reclaimer-boom",
    "glass-fiber-bushing",
    "oil-pipeline-pig-trap",
    "coke-oven-battery",
    "chlor-alkali-membrane",
    "air-separation-coldbox",
    "eaf-arc-furnace",
    "spray-dryer-tower",
    "geothermal-binary-ORC",
    "ammonia-converter",
    "foundry-core-shooter",
    "photovoltaic-laminator",
    "urea-prill-tower",
    "trona-calciner",
    "kraft-recovery-boiler",
    "var-ingot-melt",
    "msf-flash-desal",
    "hot-strip-mill",
    "spiral-freezer",
    "offset-web-press",
    "bascule-bridge",
    "vacuum-induction-melt",
    "airport-jetbridge",
    "air-sep-coldbox",
    "rotary-tablet-press",
    "spent-fuel-bridge",
    "PET-stretch-blow",
    "jackup-preload",
    "dairy-falling-film",
    "dissolved-air-flotation",
    "cement-precalciner",
    "steel-caster-mold",
    "wind-nacelle-yaw",
    "perlite-expander",
    "hdd-pilot-bore",
    "kaolin-filter-press",
    "hydro-penstock",
    "malt-kiln-turn",
    "sugar-vacuum-pan",
    "hydro-wicket-gate",
    "wind-turbine-pitch",
    "escalator-comb-plate",
    "helium-liquefier",
    "czochralski-puller",
    "escalator-comb",
    "jet-fuel-hydrant",
    "sawmill-carriage",
    "composite-autoclave",
    "electron-linac",
    "die-cast-cell",
    "desal-RO-train",
    "salt-cavern-CAES",
    "tire-curing-press",
    "electrostatic-precipitator",
    "wind-tunnel-balance",
    "olive-oil-decanter",
    "electrolyzer-stack",
    "hvdc-thyristor-valve",
    "autoclave-retort",
    "solar-trough-htf",
    "transformer-oltc",
    "lng-open-rack",
    "metro-psd",
    "aluminum-potline",
    "vial-lyophilizer",
    "sts-quay-crane",
'''
# insert extra domains before closing of BANNED_DOMAINS
src = src.replace(
    '    "cement-precalciner",\n}',
    '    "cement-precalciner",' + extra_domains + "}",
    1,
)

extra_plants = '''
    "Pyro-Knap",
    "Thoria-Kettle",
    "Nitrid-Fell",
    "Riser-Wold",
    "Crepe-Noll",
    "Zinc-Fen",
    "Bitumen-Cairn",
    "Crepe-Nave",
    "Isostat-Wold",
    "Matte-Fell",
    "Olefin-Noll",
    "Lampblack-Fen",
    "Tack-Drum",
    "Tile-Warden",
    "Setter-Naze",
    "Scraper-Ness",
    "Winze-Capstan",
    "Pallet-Rigg",
    "Laterite-Vat",
    "Methane-Howe",
    "Bauxite-Naze",
    "Cathode-Howe",
    "Pack-Quill",
    "Zeolite-Knap",
    "Adiabat-Sieve",
    "Fumarole-Dyke",
    "Cocoa-Noll",
    "Dewar-Nave",
    "Flight-Furlong",
    "Gneiss-Tap",
    "Solder-Kite",
    "Yankee-Crest",
    "Bush-Fen",
    "Spelter-Holt",
    "Zinc-Cistern",
    "Pyrite-Gill",
    "Vinyl-Garth",
    "Flute-Wick",
    "Otter-Brae",
    "Tenter-Howe",
    "Bustle-Shaw",
    "Crepe-Cap",
    "Coke-Drum",
    "Firth-Spur",
    "Barrow-Mezz",
    "Cleat-Face",
'''
src = src.replace(
    '    "Skim-Loom",\n)',
    '    "Skim-Loom",' + extra_plants + ")",
    1,
)

# splice records
m = re.search(r"\ndef lif_211_excerpt\(\):", src)
n = re.search(r"\ndef tokenize\(text: str\)", src)
if not m or not n:
    raise SystemExit(f"splice markers missing m={bool(m)} n={bool(n)}")
src = src[: m.start() + 1] + records + "\n\n" + src[n.start() + 1 :]

src = src.replace('("round", 39),', '("round", 53),')
src = src.replace('ttf-r39-211', 'ttf-r53-281')
src = src.replace('ttf-r39-212', 'ttf-r53-282')
src = src.replace('ttf-r39-213', 'ttf-r53-283')
src = src.replace('ttf-r39-214', 'ttf-r53-284')
src = src.replace('ttf-r39-215', 'ttf-r53-285')
src = src.replace('if rec["id"] == "ttf-r53-281":\n            if rec["raster"].get("excerpt_source") != "independent_lif":\n                issues.append("211 missing independent_lif")\n            if rec["future_outcome"]["reward_inflection_t_us"] > rec["raster"]["window_ms"] * 1000:\n                issues.append("211 inflection outside window")\n            if rec["reward_components"]["total"] >= 0:\n                issues.append("211 partnered-neg total not negative")',
                  'if rec["id"] == "ttf-r53-281":\n            if rec["raster"].get("excerpt_source") != "independent_lif":\n                issues.append("281 missing independent_lif")\n            if rec["future_outcome"]["reward_inflection_t_us"] > rec["raster"]["window_ms"] * 1000:\n                issues.append("281 inflection outside window")\n            if rec["reward_components"]["total"] >= 0:\n                issues.append("281 partnered-neg total not negative")')
src = src.replace('if rec["meta"]["round"] != 39:', 'if rec["meta"]["round"] != 53:')
src = src.replace(
    'if ids != [f"ttf-r39-{n}" for n in range(211, 216)]:',
    'if ids != [f"ttf-r53-{n}" for n in range(281, 286)]:',
)
# leftover ttf-r39 after replacements
src = src.replace('ttf-r39', 'ttf-r53')
src = src.replace('batch-r39.jsonl', 'batch-r53.jsonl')
src = src.replace('NOTES-r39', 'NOTES-r53')
src = src.replace('record_211()', 'record_281()')
src = src.replace('record_212()', 'record_282()')
src = src.replace('record_213()', 'record_283()')
src = src.replace('record_214()', 'record_284()')
src = src.replace('record_215()', 'record_285()')

# replace leftover 212 kettle checks with lagged-tag checks
old_212 = '''        if rec["id"] == "ttf-r53-282":
            ev = rec["proposed_action"]["evidence"]
            if not (ev["kettle_bar"] > ev["kettle_cap_bar"]):
                issues.append("212 kettle not over cap")
            if not (ev["t_exec_us"] > ev["latest_legal_clamp_us"]):
                issues.append("212 t_exec not after latest_legal_clamp")
            if rec["executed_action"]["parameters"].get("extra_plc_scan") is not True:
                issues.append("212 extra_plc_scan not true")
            if rec["executed_action"]["parameters"].get("t_exec_us") != 10860:
                issues.append("212 expected t_exec_us=10860")
            if rec["executed_action"]["parameters"].get("kettle_bar") != 10.2:
                issues.append("212 expected late-but-correct 10.2 bar vent")
            if "recovery" not in rec["future_outcome"]:
                issues.append("212 missing recovery")
            table_to = {row["to"] for row in rec["raster"]["routing"]["table"]}
            if "policy.vent_now" in table_to:
                issues.append("212 routing still has vent_now")
            if "policy.wait_scan" not in table_to:
                issues.append("212 routing missing wait_scan")
            if "clamp-too-late" not in rec["meta"]["tags"]:
                issues.append("212 missing clamp-too-late tag")'''
new_282 = '''        if rec["id"] == "ttf-r53-282":
            ev = rec["proposed_action"]["evidence"]
            if not (ev["acid_live_wt_pct"] < ev["acid_floor_wt_pct"]):
                issues.append("282 live acid not under floor")
            if not (ev["tag_age_s"] > ev["max_legal_tag_age_s"]):
                issues.append("282 tag not stale")
            if rec["executed_action"]["parameters"].get("bind_lagged_tag") is not True:
                issues.append("282 bind_lagged_tag not true")
            if rec["executed_action"]["parameters"].get("olefin_tph") != 22.0:
                issues.append("282 expected olefin bump 22.0 t/h")
            if rec["executed_action"]["parameters"].get("olefin_tph") == ev.get("correct_olefin_tph"):
                issues.append("282 executed the correct 9.0 t/h cut")
            if "recovery" not in rec["future_outcome"]:
                issues.append("282 missing recovery")
            table_to = {row["to"] for row in rec["raster"]["routing"]["table"]}
            if "policy.olefin_cut" in table_to:
                issues.append("282 routing still has olefin_cut")
            if "policy.olefin_bump" not in table_to:
                issues.append("282 routing missing olefin_bump")
            if "stale-sample" not in rec["meta"]["tags"]:
                issues.append("282 missing stale-sample tag")'''
if old_212 not in src:
    raise SystemExit("212 check block not found after id rewrite")
src = src.replace(old_212, new_282)

# notes_text function body
notes_start = src.find("def notes_text(jmax: float, jprior: float) -> str:")
notes_end = src.find("\ndef run_pipelines(records):")
if notes_start < 0 or notes_end < 0:
    raise SystemExit("notes_text bounds missing")
notes = r'''def notes_text(jmax: float, jprior: float) -> str:
    return f"""# Thalamic Trajectory Factory — NOTES-r53

- Factory: `thalamic-trajectory-factory`
- Run label: `2026-09-02-final-heavy`
- Generator: `grok-4.6`
- Channel: SuperGrok Heavy consumer chat (RM-793 research-only)
- Quota: 5
- Quality: Q=5
- IDs: `ttf-r53-281` … `ttf-r53-285`
- Domains this batch: `fluid-bed-roaster`, `alkylation-contactor`, `anode-bake-furnace`, `blown-film-tower`, `SX-mixer-settler`

These five domain slugs sit outside the prompt 8-pool and outside staged r13–r45 occupancy (jsonl SoT plus generator sit-ins: r36 skip/HRSG/overland, r37 compost/FCC-regen/MRI/conche/UHT, r38 sinter/FCC/electrowinning/PSA/tandem, r39 Claus/PVC/corrugator/OTSG/stenter, r40 coker/yankee/flash/HIP, r42 brick/SMR/Bayer/PE-loop/electrorefining, r43 carbon-black/asphalt/undulator/nylon/longwall, r44 ESR/HIP/FCC-riser/yankee/galvanize, r45 cracker/PSA/stacker/bushing/pig-trap). All five plants are invented (Gossan-Weald, Raffinate-Holt, Butts-Howe, Frostline-Kame, Pregnant-Lea). Do not restack prior TTF plants (Marrow-Dock, Vesper-Lattice, Brine-Well, Saddle-Arc, Ashlar-Gait, Pyrite-Gill, Vinyl-Garth, Flute-Wick, Otter-Brae, Tenter-Howe, Thoria-Kettle, Nitrid-Fell, Riser-Wold, Crepe-Noll, Zinc-Fen, Pyro-Knap, Haber-Knoll, Loam-Hurst, Lamina-Kame, Prill-Flue).

## Batch map

| id | domain | decision | correctness | sim_or_real | total | edge |
|----|--------|----------|-------------|-------------|-------|------|
| ttf-r53-281 | fluid-bed-roaster | MODIFY | correct | designed | **−0.48** | process-correct air clamp; cyclone dipleg collapse inside 42 ms raster; independent LIF |
| ttf-r53-282 | alkylation-contactor | MODIFY | **incorrect (wrong-modify / stale-sample)** | designed | −0.68 | live acid 86.8 wt% < 90.0 floor; olefin bumped 18→22 t/h on lagged 92.4 tag |
| ttf-r53-283 | anode-bake-furnace | REJECT | correct | hil | +0.80 | AE 36 pps beats flue O2 3.1 pct; hold ram |
| ttf-r53-284 | blown-film-tower | ACCEPT | correct | simulated | +1.04 | frost 1.92 m vs haul 38 m/min; proposed 38 m/min already legal |
| ttf-r53-285 | SX-mixer-settler | ACCEPT | correct | designed | +1.14 | organic 0.94 vs mixer 165 rpm; proposed 165 rpm already legal |

Gate mix: 2 ACCEPT, 1 correct MODIFY (partnered-neg, in-window), 1 incorrect MODIFY (stale-sample / lagged-tag), 1 correct REJECT. Provenance: designed×3, simulated×1, hil×1 (Butts-Howe BH-HIL bake-pit mockup). Intra-batch Jaccard on `state.description` {jmax:.3f} (max vs prior staged {jprior:.3f}).

## Wrong-modify

**ttf-r53-282** is the mandated incorrect gate (`safety_decision.correctness=incorrect`, `meta.supervisor_error_type=wrong-modify`). Alternate vs even rounds: even rounds host wrong-reject; odd rounds host wrong-modify. This is **stale-sample / lagged-tag** (live analyzer under floor; MODIFY binds a lagged DCS tag past `max_legal_tag_age_s`), unused in staged jsonl through r44. Not r13/r19 wrong-axis, not r14/r23 wrong-loop, not r15/r39 clamp-too-late, not r21 wrong-polarity, not r24 under-clamp, not r25/r29/r31 wrong-phase, not r33/r35 over-clamp. Do not emit a wrong-ACCEPT.

Raffinate-Holt RH-3 / Contactor C-7 reads live acid **86.8 wt percent** against a **90.0 wt percent** floor. A lagged DCS tag still shows **92.4 wt percent**, age **48 s > 8 s** freshness. Sidecar arithmetic `86.8 < 90.0` and `tag_age_s > max_legal_tag_age_s` is true. A timely MODIFY at `t_gate_us=6280` cuts olefin **18.0 → 9.0 t/h**. A weak supervisor treats the lagged 92.4 as live and bumps olefin **18.0 → 22.0 t/h**. Live acid falls to **84.1 wt percent**. Convictable without alkylation physics: `evidence.acid_live_wt_pct < evidence.acid_floor_wt_pct`, `evidence.tag_age_s > evidence.max_legal_tag_age_s`, `executed_action` sets `olefin_tph=22.0` ≠ `correct_olefin_tph=9.0` and `bind_lagged_tag=true`, `raster.routing.table` sends `relay.an.acid.lag` → `policy.olefin_bump` (weight 0.75) with no positive weight to `policy.olefin_cut`, and `gate_snn` has `olefin_bump` above threshold while `olefin_cut` is not. Recovery: MODIFY olefin 18.0 → 9.0 t/h on the live titrator; leave lagged 92.4 on its own bus. Cost: 12 min acid dump (`abort_s=720`).

## Partnered-negative in-window (281)

**ttf-r53-281** is the partnered negative: process-correct MODIFY (air held 11.6 kNm3/h; bed 878 C <= 890 cap) while the world still charges. Safety −0.62 prices the cyclone dipleg collapse at **22.600 ms**; `task_progress` stays +0.30 because the clamp completed. Inflection `t_us=22600` is tick 5 and is **inside** the 42 ms raster (`22600 ≤ 42000`). Named un-netted loss: 15 min dipleg isolate (`abort_s=900`). Not folded into process heads.

Independent LIF (the one labeled sidecar sim): `state.sim_or_real` remains `designed`. `raster.excerpt_source=independent_lif`, `raster.sim_scope=sidecar_only`, `raster.lif` seed 53281, stim `[22000, 25200]`. Excerpt is membrane crossings (`lif.clamp` early vs `lif.cyclone` 22–25.2 ms), not a 1:1 remap of `spike_events`. `meta.tags` include `independent-lif-raster` and `sidecar-sim-only`.

## Reward formula and tick reconciliation

Declared aggregation on every record:

`total = task_progress + safety + efficiency + coherence + exploration`

Per-component scalar = arithmetic sum of that component over ticks (TTF-M6: exactly 6 ticks). Tick 6 is bound to a published sidecar (`abort_s`, `survey_s`, `dwell_s`) via `future_outcome.delayed_surprise_s` and is strictly after the raster window. Inflection `t_us` is an actual tick.

| id | ticks | tp | saf | eff | coh | exp | total | inflection tick |
|----|-------|----|-----|-----|-----|-----|-------|-----------------|
| 281 | 6 | +0.30 | −0.62 | −0.16 | +0.04 | −0.04 | −0.48 | 5 (22600) |
| 282 | 6 | −0.22 | −0.24 | −0.18 | −0.10 | +0.06 | −0.68 | 4 (6280) |
| 283 | 6 | +0.10 | +0.42 | +0.12 | +0.10 | +0.06 | +0.80 | 4 (7620) |
| 284 | 6 | +0.40 | +0.28 | +0.18 | +0.12 | +0.08 | +1.04 | 4 (7840) |
| 285 | 6 | +0.44 | +0.30 | +0.20 | +0.12 | +0.08 | +1.14 | 4 (5760) |

Tick-6 sidecar bind: 281 `abort_s=900`, 282 `abort_s=720`, 283 `abort_s=480`, 284 `survey_s=360`, 285 `dwell_s=240`.

## Raster / energy (Loihi-2 4-core, 23 pJ/spike)

| id | domain | n | rate Hz | window_ms | spikes | energy_pJ | energy_uJ |
|----|--------|---|---------|-----------|--------|-----------|-----------|
| 281 | fluid-bed-roaster | 72 | 28 | 42 | 85 | 1955 | 0.001955 |
| 282 | alkylation-contactor | 96 | 32 | 26 | 80 | 1840 | 0.001840 |
| 283 | anode-bake-furnace | 104 | 22 | 40 | 92 | 2116 | 0.002116 |
| 284 | blown-film-tower | 60 | 40 | 26 | 62 | 1426 | 0.001426 |
| 285 | SX-mixer-settler | 84 | 30 | 22 | 55 | 1265 | 0.001265 |

`spikes = round(n × rate × window_s)`. Every record carries `gate_snn` whose `decision` matches the safety gate; populations that declare rate+spikes meet the same ±1 budget against `decision_window_s`. `routing.third_factor` has modulator (NA / ACh / DA / 5-HT / adenosine), `tau_e_s`/`tau_e_ms` pair, and eligibility. Excerpt same-neuron gap ≥ 1000 µs; spike trains same-channel refractory ≥ 0.8 ms. Non-281 excerpts are kernelized and independent of `spike_events` times (overlap < 0.8).

## Local checks (staging, not raw)

See generator stdout: `check_jsonl` FactoryStaging, `validate_run.check_line`, `dumps_exact_json`, `raster_status`, `verify_batch_for_frontier(strict=True)`, `spike_probe.py --strict`, tick sums, refractory, Jaccard.

Never `training_ready`. Never `sim_or_real=real`. Never wrote `outputs/raw/`.

## Residual weaknesses (honest)

1. Only **one** labeled independent LIF (281). The other four excerpts are independent of `spike_events` times but are not declared population sims.
2. Wrong-ACCEPT still absent (guard).
3. Tick-6 sidecar bind is standing machinery (r14+), not a new class.
4. Five domain slugs leave the prompt's 8-item pool; a later round that must stay inside the pool will have to rotate sit-outs instead.
5. 284 and 285 are both already-legal ACCEPTs; a later round could pair one ACCEPT with a world charge that does not go negative.

## Next densification target

Labeled LIF on a second record, or an ISI histogram sidecar. Remaining unused wrong-MODIFY subclasses include **wrong-unit on a lagged bus** (not stale-sample itself). Wrong-ACCEPT remains structurally absent until a prompt amendment.

Novel coverage: 18.0%
"""


'''
src = src[:notes_start] + notes + src[notes_end + 1 :]

# enhance prior_domains to also harvest generator domains
old_prior = '''def prior_domains_and_descs():
    domains = set()
    descs = []
    blobs = []
    for path in sorted(Path("/tmp").glob("ttf-r*/batch-r*.jsonl")):
        if path.resolve() == BATCH_PATH.resolve():
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except OSError:
            continue
        blobs.append(text)
        for line in text.split("\\n"):
            if not line.strip():
                continue
            try:
                rec = json.loads(line)
            except json.JSONDecodeError:
                continue
            d = rec.get("state", {}).get("domain") or rec.get("meta", {}).get("domain")
            if d:
                domains.add(str(d))
            desc = rec.get("state", {}).get("description")
            if isinstance(desc, str):
                descs.append(desc)
    return domains, descs, "\\n".join(blobs)
'''
new_prior = '''def prior_domains_and_descs():
    domains = set()
    descs = []
    blobs = []
    for path in sorted(Path("/tmp").glob("ttf-r*/batch-r*.jsonl")):
        if path.resolve() == BATCH_PATH.resolve():
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except OSError:
            continue
        blobs.append(text)
        for line in text.split("\\n"):
            if not line.strip():
                continue
            try:
                rec = json.loads(line)
            except json.JSONDecodeError:
                continue
            d = rec.get("state", {}).get("domain") or rec.get("meta", {}).get("domain")
            if d:
                domains.add(str(d))
            desc = rec.get("state", {}).get("description")
            if isinstance(desc, str):
                descs.append(desc)
    for path in sorted(Path("/tmp").glob("ttf-r*/gen_r*.py")):
        if path.resolve() == Path(__file__).resolve():
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except OSError:
            continue
        blobs.append(text)
        m = re.search(r"THIS_DOMAINS\\s*=\\s*\\{([^}]+)\\}", text)
        if m:
            for d in re.findall(r'"([^"]+)"', m.group(1)):
                domains.add(d)
        for d in re.findall(r'\\("domain",\\s*"([^"]+)"\\)', text):
            domains.add(d)
    return domains, descs, "\\n".join(blobs)
'''
if old_prior not in src:
    raise SystemExit("prior_domains_and_descs not found")
src = src.replace(old_prior, new_prior)

(root / "gen_r53.py").write_text(src)
print("patched", root / "gen_r53.py", "lines", src.count("\n") + 1)
'''
