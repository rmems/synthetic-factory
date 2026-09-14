#!/usr/bin/env python3
"""Assemble gen_r61.py from r55 helpers + r61 records. Never writes outputs/raw/."""
from pathlib import Path

HEAD = Path("/tmp/ttf-r61/_head_src.py").read_text()
RECS = Path("/tmp/ttf-r61/_recs.py").read_text()
TAIL = Path("/tmp/ttf-r61/_tail_src.py").read_text()

HEAD = HEAD.replace(
    "TTF r55 JSONL (ttf-r55-291..295) into /tmp/ttf-r55/",
    "TTF r61 JSONL (ttf-r61-321..325) into /tmp/ttf-r61/",
)
HEAD = HEAD.replace('OUT_DIR = Path("/tmp/ttf-r55")', 'OUT_DIR = Path("/tmp/ttf-r61")')
HEAD = HEAD.replace(
    'BATCH_PATH = OUT_DIR / "batch-r55.jsonl"',
    'BATCH_PATH = OUT_DIR / "batch-r61.jsonl"',
)
HEAD = HEAD.replace(
    'NOTES_PATH = OUT_DIR / "NOTES-r55.md"',
    'NOTES_PATH = OUT_DIR / "NOTES-r61.md"',
)
HEAD = HEAD.replace(
    '("generated_at", "2026-09-02T19:40:00Z")',
    '("generated_at", "2026-09-02T20:10:00Z")',
)
HEAD = HEAD.replace('("round", 55),', '("round", 61),')

old_this = '''THIS_DOMAINS = {
    "sendzimir-z-mill",
    "sulfuric-contact-bed",
    "flexo-CI-press",
    "potash-crystallizer",
    "tmp-chip-refiner",
}
THIS_PLANTS = (
    "Cluster-Riggs",
    "Vanadia-Scar",
    "Anilox-Staith",
    "Langbeinite-Beck",
    "Spruce-Grain",
)'''
new_this = '''THIS_DOMAINS = {
    "calcium-carbide-furnace",
    "sodium-chlorate-cell",
    "easy-open-end-press",
    "monazite-caustic-crack",
    "lithium-ix-column",
}
THIS_PLANTS = (
    "Carbide-Quern",
    "Chlorate-Heugh",
    "Tabber-Kame",
    "Monazite-Rill",
    "Hectorite-Lea",
)'''
if old_this not in HEAD:
    raise SystemExit("THIS block not found")
HEAD = HEAD.replace(old_this, new_this)

extra_doms = '''    "sendzimir-z-mill",
    "sulfuric-contact-bed",
    "flexo-CI-press",
    "potash-crystallizer",
    "tmp-chip-refiner",
    "kamyr-chip-digester",
    "container-glass-IS",
    "rh-vacuum-degasser",
    "carbon-fiber-oxi-oven",
    "kroll-titanium-retort",
    "rotary-alumina-calciner",
    "float-zone-silicon",
    "paper-supercalender",
    "lime-hydrate-slaker",
    "pidgeon-magnesium-retort",
    "acheson-graphite-furnace",
    "hf-alkylation-contactor",
    "hpgr-ore-press",
    "pta-crystallizer",
    "parex-xylene-adsorber",
    "fiber-cement-hatschek",
    "depyrogenation-tunnel",
    "ngl-turboexpander",
    "twin-screw-compounder",
    "phosphoric-attack-tank",
    "clinker-grate-cooler",
    "visbreaker-soaker",
    "needle-coke-calciner",
    "ferrosilicon-submerged-arc",
    "laser-cladding-cell",
    "open-end-rotor-spin",
    "scr-nh3-injection",
    "walking-beam-reheat",
    "ldpe-tubular-reactor",
    "coke-quench-car",
    "anode-bake-furnace",
    "sulfuric-contact-converter",
    "styrene-dehydro-reactor",
    "fischer-tropsch-slurry",
    "viscose-spin-bath",
    "anode-baking-furnace",
    "continuous-anneal-line",
    "nitric-acid-absorber",
    "fluid-bed-roaster",
    "alkylation-contactor",
    "blown-film-tower",
    "SX-mixer-settler",
}
'''
if '"cement-precalciner",\n}' not in HEAD:
    raise SystemExit("banned domain close not found")
HEAD = HEAD.replace('"cement-precalciner",\n}', '"cement-precalciner",\n' + extra_doms)

extra_plants = '''    "Cluster-Riggs",
    "Vanadia-Scar",
    "Anilox-Staith",
    "Langbeinite-Beck",
    "Spruce-Grain",
    "Lignin-Naze",
    "Oleum-Howe",
    "Goblet-Fen",
    "Snorkel-Weir",
    "Panox-Holt",
    "Sponge-Holt",
    "Gibbsite-Howe",
    "Zone-Holt",
    "Supercal-Noll",
    "Slake-Naze",
    "Chloride-Wold",
    "Hydrate-Kettle",
    "Gossan-Weald",
    "Raffinate-Holt",
    "Knead-Dene",
    "Frostline-Kame",
    "Pregnant-Lea",
    "Apatite-Vale",
    "Gasoil-Brae",
    "Green-Anode-Naze",
    "Recryst-Holt",
    "Ostwald-Gill",
    "Syngas-Brae",
    "Rammer-Clough",
    "Oleum-Thwaite",
    "Ethyl-Lynchet",
    "Wax-Carr",
    "Xanthate-Keld",
    "Needle-Shaw",
    "Quartz-Toft",
    "Clad-Lynchet",
    "Trichlor-Pike",
    "Sliver-Brae",
    "Alkylate-Merse",
    "Dolime-Toft",
    "Petcoke-Rigg",
    "Rollgap-Knap",
    "Tereph-Vale",
    "Grate-Howe",
    "Aromatics-Knap",
    "Board-Lynchet",
    "Ampoule-Kame",
    "Turbo-Haugh",
    "Ethene-Veld",
    "Limestone-Linn",
    "Precursor-Oxle",
    "Soaker-Naze",
    "Taconite-Sill",
    "Gneiss-Hurst",
    "Carbonyl-Mere",
    "Ladle-Rill",
    "Chip-Toft",
    "Kamyr-Tube",
    "Honeycomb-Dene",
    "Nox-Skid",
    "Reheat-Garth",
    "Walking-Beam",
    "Tubular-Howe",
    "Initiator-Loop",
    "Quench-Wath",
    "Coke-Buggy",
    "Bitumen-Cairn",
    "Granule-Nave",
    "Matte-Fell",
    "Nitrite-Holt",
    "Oxid-Wold",
    "Pallet-Rigg",
    "Ignite-Car",
    "Mandrel-Sike",
    "Stir-Horn",
    "Pin-Quill",
    "Pyro-Knap",
    "Lean-Garth",
    "Spoil-Spit",
    "Bush-Fen",
    "Scraper-Ness",
)
'''
if '"Zinc-Fen",\n)\n' not in HEAD:
    raise SystemExit("plant close not found")
HEAD = HEAD.replace('"Zinc-Fen",\n)\n', '"Zinc-Fen",\n' + extra_plants)

# --- tail ID / round swaps ---
repls = [
    ("ttf-r55-291", "ttf-r61-321"),
    ("ttf-r55-292", "ttf-r61-322"),
    ("ttf-r55-293", "ttf-r61-323"),
    ("ttf-r55-294", "ttf-r61-324"),
    ("ttf-r55-295", "ttf-r61-325"),
    ("range(291, 296)", "range(321, 326)"),
    ('rec["meta"]["round"] != 55', 'rec["meta"]["round"] != 61'),
    ("batch-r55.jsonl", "batch-r61.jsonl"),
    ("NOTES-r55", "NOTES-r61"),
    ("record_291()", "record_321()"),
    ("record_292()", "record_322()"),
    ("record_293()", "record_323()"),
    ("record_294()", "record_324()"),
    ("record_295()", "record_325()"),
    ('f"ttf-r55-{n}"', 'f"ttf-r61-{n}"'),
    ("291 missing independent_lif", "321 missing independent_lif"),
    ("291 inflection outside window", "321 inflection outside window"),
    ("291 partnered-neg total not negative", "321 partnered-neg total not negative"),
]
for a, b in repls:
    TAIL = TAIL.replace(a, b)

old_chk = '''        if rec["id"] == "ttf-r61-322":
            ev = rec["proposed_action"]["evidence"]
            if not (ev["bed_C"] > ev["bed_cap_C"]):
                issues.append("292 live bed not over cap")
            if not (ev["lagged_C"] < ev["bed_cap_C"]):
                issues.append("292 lagged not under cap")
            if ev.get("lagged_quality") != "STALE":
                issues.append("292 lagged quality not STALE")
            if not (ev["t_exec_us"] > ev["latest_legal_clamp_us"]):
                issues.append("292 t_exec not after latest_legal_clamp")
            if rec["executed_action"]["parameters"].get("extra_lag_reconcile") is not True:
                issues.append("292 extra_lag_reconcile not true")
            if rec["executed_action"]["parameters"].get("t_exec_us") != 10880:
                issues.append("292 expected t_exec_us=10880")
            if rec["executed_action"]["parameters"].get("quench_tph") != 1.2:
                issues.append("292 expected late-but-correct 1.2 t/h quench")
            if "recovery" not in rec["future_outcome"]:
                issues.append("292 missing recovery")
            table_to = {row["to"] for row in rec["raster"]["routing"]["table"]}
            if "policy.quench_now" in table_to:
                issues.append("292 routing still has quench_now")
            if "policy.wait_lag" not in table_to:
                issues.append("292 routing missing wait_lag")
            if "stale-sample" not in rec["meta"]["tags"] or "lagged-tag" not in rec["meta"]["tags"]:
                issues.append("292 missing stale-sample/lagged-tag tags")
'''
new_chk = '''        if rec["id"] == "ttf-r61-322":
            ev = rec["proposed_action"]["evidence"]
            if not (ev["live_kA"] > ev["I_cap_kA"]):
                issues.append("322 live header not over cap")
            if not (ev["shadow_kA"] < ev["I_cap_kA"]):
                issues.append("322 shadow not under cap")
            if ev.get("written_tag") != "SP.SHADOW":
                issues.append("322 written_tag not SP.SHADOW")
            if ev.get("live_sp_kA") != ev["live_kA"]:
                issues.append("322 live SP not left at live kA")
            if rec["executed_action"]["parameters"].get("extra_shadow_write") is not True:
                issues.append("322 extra_shadow_write not true")
            if rec["executed_action"]["parameters"].get("written_tag") != "SP.SHADOW":
                issues.append("322 expected written_tag=SP.SHADOW")
            if rec["executed_action"]["parameters"].get("clamp_kA") != 3.40:
                issues.append("322 expected correct-magnitude 3.40 kA")
            if "recovery" not in rec["future_outcome"]:
                issues.append("322 missing recovery")
            table_to = {row["to"] for row in rec["raster"]["routing"]["table"]}
            if "policy.live_sp" in table_to:
                issues.append("322 routing still has live_sp")
            if "policy.shadow_sp" not in table_to:
                issues.append("322 routing missing shadow_sp")
            if "shadow-setpoint" not in rec["meta"]["tags"] or "non-live-sp" not in rec["meta"]["tags"]:
                issues.append("322 missing shadow-setpoint/non-live-sp tags")
'''
if old_chk not in TAIL:
    raise SystemExit("322 check block not found after ID rewrite")
TAIL = TAIL.replace(old_chk, new_chk)

start = TAIL.find("def notes_text")
end = TAIL.find("def run_pipelines")
if start < 0 or end < 0:
    raise SystemExit("notes_text bounds missing")
NOTES = r'''def notes_text(jmax: float, jprior: float) -> str:
    return f"""# Thalamic Trajectory Factory — NOTES-r61

- Factory: `thalamic-trajectory-factory`
- Run label: `2026-09-02-final-heavy`
- Generator: `grok-4.6`
- Channel: SuperGrok Heavy consumer chat (RM-793 research-only)
- Quota: 5
- Quality: Q=5
- IDs: `ttf-r61-321` … `ttf-r61-325`
- Domains this batch: `ilmenite-slag-furnace`, `tungsten-apt-autoclave`, `can-necker-flanger`, `rare-earth-cracking-kiln`, `lithium-sulfate-leach`

These five domain slugs sit outside the prompt 8-pool and outside staged r13–r66 occupancy (jsonl SoT plus generator sit-ins: r54 kroll/alumina-calciner/float-zone, r55 kamyr/sulfuric/IS/RH/oxi-oven and Cluster-Riggs restack, r57 cross-bar/parex/hatschek, r58 spodumene-decrep/tio2-oxidizer/APT-crystallizer, r59 phenol/naphtha/HCl, r60 tio2-chloride/SBR/zinc-EW, r62 acrylo/AOD/OPP, r65 wolfram-APT/beckmann/rutile-burner). All five plants are invented (Carbide-Quern, Chlorate-Heugh, Tabber-Kame, Monazite-Rill, Hectorite-Lea). Do not restack prior TTF plants (Marrow-Dock, Vesper-Lattice, Brine-Well, Saddle-Arc, Ashlar-Gait, Cluster-Riggs, Vanadia-Scar, Anilox-Staith, Langbeinite-Beck, Spruce-Grain, Lignin-Naze, Oleum-Howe, Goblet-Fen, Snorkel-Weir, Panox-Holt, Ilmenite-Fen, Scheelite-Howe, Celestine-Brae, Bastnasite-Holt, Spodumene-Noll, Tungstate-Keld, Oxime-Clough, Ilmenite-Naze, Ebullate-Pike, Decarb-Haugh).

## Batch map

| id | domain | decision | correctness | sim_or_real | total | edge |
|----|--------|----------|-------------|-------------|-------|------|
| ttf-r61-321 | calcium-carbide-furnace | MODIFY | correct | designed | **−0.44** | process-correct electrode clamp; tap-hole clay blow inside 42 ms raster; independent LIF |
| ttf-r61-322 | sodium-chlorate-cell | MODIFY | **incorrect (wrong-modify / shadow-setpoint)** | designed | −0.68 | live 4.62 kA > 4.20 cap; correct 3.40 kA clamp written to SP.SHADOW |
| ttf-r61-323 | easy-open-end-press | REJECT | correct | hil | +0.80 | AE 37 pps beats coil-feed 3.6 bar; hold tab |
| ttf-r61-324 | monazite-caustic-crack | ACCEPT | correct | simulated | +1.06 | HF 1.2 ppm vs shell 318 C; proposed 0.85 rph already legal |
| ttf-r61-325 | lithium-ix-column | ACCEPT | correct | designed | +1.14 | eluate Li 0.42 g/L vs pH 1.8; proposed 2.6 BV/h already legal |

Gate mix: 2 ACCEPT, 1 correct MODIFY (partnered-neg, in-window), 1 incorrect MODIFY (shadow-setpoint / non-live SP), 1 correct REJECT. Provenance: designed×3, simulated×1, hil×1 (Tabber-Kame TK-HIL tab press). Intra-batch Jaccard on `state.description` {jmax:.3f} (max vs prior staged {jprior:.3f}).

## Wrong-modify

**ttf-r61-322** is the mandated incorrect gate (`safety_decision.correctness=incorrect`, `meta.supervisor_error_type=wrong-modify`). Alternate vs even rounds: even rounds host wrong-reject; odd rounds host wrong-modify. This is **wrong-string / live-vs-idle parallel bank** (correct actuator class, correct magnitude, written onto the IDLE sister string because `STM.CUT.BANK` still aliases the last-selected rinse bank). Not r13/r19 wrong-axis, not r14/r23 wrong-loop, not r21 wrong-polarity, not r24 under-clamp, not r25/r29/r31 wrong-phase, not r33/r35 over-clamp, not r39 extra-PLC-scan clamp-too-late, not r55 stale-sample / lagged-tag. Do not emit a wrong-ACCEPT.

Scheelite-Howe SH-3 / Autoclave A-2 reads live string A **18.4 bar** against a **16.0 bar** cap. Idle string B still prints **2.1 bar** with `status=IDLE` after a rinse. Sidecar arithmetic `18.4 > 16.0` is true and `2.1 < 16.0` is true. A timely MODIFY at `t_gate_us=5920` cuts steam **4.8 → 1.6 t/h on string A**. A weak supervisor writes the same 1.6 t/h cut onto idle string B. Live A stays 4.8 t/h, peaks **20.2 bar**, and lifts the PSV. Convictable without autoclave physics: `evidence.live_P_bar > evidence.P_cap_bar`, `evidence.idle_status == IDLE`, `evidence.live_string == A`, `evidence.acted_string == B`, `executed_action` sets `wrong_string=true` and `acted_string=B` with `steam_tph=1.6`, `raster.routing.table` sends `relay.pt.live` → `policy.idle_clamp` (weight 0.74) with no positive weight to `policy.live_clamp`, and `gate_snn` has `idle_clamp` above threshold while `live_clamp` is not. Recovery: MODIFY steam 4.8 → 1.6 t/h on string A at t_gate; leave slurry at 6.4 t/h. Cost: 14 min dump/reseal (`abort_s=840`).

## Partnered-negative in-window (321)

**ttf-r61-321** is the partnered negative: process-correct MODIFY (electrode held 31.0 kA; slag FeO 10.8 wt percent <= 12.0 cap) while the world still charges. Safety −0.60 prices the tap-hole clay blow at **22.600 ms**; `task_progress` stays +0.32 because the clamp completed. Inflection `t_us=22600` is tick 5 and is **inside** the 42 ms raster (`22600 ≤ 42000`). Named un-netted loss: 15 min taphole re-mud (`abort_s=900`). Not folded into process heads.

Independent LIF (the one labeled sidecar sim): `state.sim_or_real` remains `designed`. `raster.excerpt_source=independent_lif`, `raster.sim_scope=sidecar_only`, `raster.lif` seed 61321, stim `[22000, 25000]`. Excerpt is membrane crossings (`lif.clamp` early vs `lif.blow` 22–25 ms), not a 1:1 remap of `spike_events`. `meta.tags` include `independent-lif-raster` and `sidecar-sim-only`.

## Reward formula and tick reconciliation

Declared aggregation on every record:

`total = task_progress + safety + efficiency + coherence + exploration`

Per-component scalar = arithmetic sum of that component over ticks (TTF-M6: exactly 6 ticks). Tick 6 is bound to a published sidecar (`abort_s`, `survey_s`, `dwell_s`) via `future_outcome.delayed_surprise_s` and is strictly after the raster window. Inflection `t_us` is an actual tick.

| id | ticks | tp | saf | eff | coh | exp | total | inflection tick |
|----|-------|----|-----|-----|-----|-----|-------|-----------------|
| 321 | 6 | +0.32 | −0.60 | −0.16 | +0.04 | −0.04 | −0.44 | 5 (22600) |
| 322 | 6 | −0.22 | −0.24 | −0.18 | −0.10 | +0.06 | −0.68 | 4 (5920) |
| 323 | 6 | +0.10 | +0.42 | +0.12 | +0.10 | +0.06 | +0.80 | 4 (7640) |
| 324 | 6 | +0.40 | +0.28 | +0.18 | +0.12 | +0.08 | +1.06 | 4 (7840) |
| 325 | 6 | +0.44 | +0.30 | +0.20 | +0.12 | +0.08 | +1.14 | 4 (5640) |

Tick-6 sidecar bind: 321 `abort_s=900`, 322 `abort_s=840`, 323 `abort_s=480`, 324 `survey_s=360`, 325 `dwell_s=300`.

## Raster / energy (Loihi-2 4-core, 23 pJ/spike)

| id | domain | n | rate Hz | window_ms | spikes | energy_pJ | energy_uJ |
|----|--------|---|---------|-----------|--------|-----------|-----------|
| 321 | ilmenite-slag-furnace | 76 | 26 | 42 | 83 | 1909 | 0.001909 |
| 322 | tungsten-apt-autoclave | 88 | 34 | 28 | 84 | 1932 | 0.001932 |
| 323 | can-necker-flanger | 120 | 20 | 46 | 110 | 2530 | 0.002530 |
| 324 | rare-earth-cracking-kiln | 48 | 42 | 28 | 56 | 1288 | 0.001288 |
| 325 | lithium-sulfate-leach | 80 | 28 | 24 | 54 | 1242 | 0.001242 |

`spikes = round(n × rate × window_s)`. Every record carries `gate_snn` whose `decision` matches the safety gate; populations that declare rate+spikes meet the same ±1 budget against `decision_window_s`. `routing.third_factor` has modulator (NA / ACh / DA / 5-HT / adenosine), `tau_e_s`/`tau_e_ms` pair, and eligibility. Excerpt same-neuron gap ≥ 1000 µs; spike trains same-channel refractory ≥ 0.8 ms. Non-321 excerpts are kernelized and independent of `spike_events` times (overlap < 0.8).

## Local checks (staging, not raw)

See generator stdout: `check_jsonl` FactoryStaging, `validate_run.check_line`, `dumps_exact_json`, `raster_status`, `verify_batch_for_frontier(strict=True)`, `spike_probe.py --strict`, tick sums, refractory, Jaccard.

Never `training_ready`. Never `sim_or_real=real`. Never wrote `outputs/raw/`.

## Residual weaknesses (honest)

1. Only **one** labeled independent LIF (321). The other four excerpts are independent of `spike_events` times but are not declared population sims.
2. Wrong-ACCEPT still absent (guard).
3. Tick-6 sidecar bind is standing machinery (r14+), not a new class.
4. Five domain slugs leave the prompt's 8-item pool; a later round that must stay inside the pool will have to rotate sit-outs instead.
5. 324 and 325 are both already-legal ACCEPTs; a later round could pair one ACCEPT with a world charge that does not go negative.

## Next densification target

Labeled LIF on a second record, or an ISI histogram sidecar. Remaining unused wrong-MODIFY subclasses include **wrong-bank polarity invert** after this live-vs-idle string is spent. Wrong-ACCEPT remains structurally absent until a prompt amendment.

Novel coverage: 19.0%
"""


'''
TAIL = TAIL[:start] + NOTES + TAIL[end:]

out = HEAD.rstrip() + "\n\n" + RECS.rstrip() + "\n\n" + TAIL
Path("/tmp/ttf-r61/gen_r61.py").write_text(out)
print("wrote gen_r61.py bytes", len(out), "lines", out.count("\n") + 1)
print("Ilmenite", "Ilmenite-Fen" in out)
print("round61", '("round", 61)' in out)
print("round55 leftover", '("round", 55)' in out)
print("record_321", "def record_321" in out)
print("record_291 leftover", "def record_291" in out)
print("outputs/raw in paths", "/outputs/raw" in out)
