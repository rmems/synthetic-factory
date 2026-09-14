def occupancy_preflight():
    claimed = (
        "chaffholt detox",
        "orpveil",
        "platinum-orp remaining-cyanide",
        "furzeholt cyanide",
        "mallowholt sugar",
        "polveil",
        "polarimetric remaining-sucrose",
        "pol-hil-4",
        "vetchwharf phosphate",
        "headveil",
        "hydrostatic remaining-level",
        "hydro-sim-6",
        "limewhin acid",
        "sedgeholt pans",
        "rooke venn",
        "odel marr",
        "sera dunne",
        "ivo harn",
        "kell marsh",
        "nelb-r67-202",
        "nelb-r67-203",
        "nelb-r67-204",
    )
    steal = (
        "irisveil",
        "pyroveil",
        "fluoveil",
        "orifveil",
        "lampveil",
        "condveil",
        "brixveil",
        "wliveil",
        "pitoveil",
        "doasveil",
        "oxveil",
        "cellveil",
        "sourveil",
        "cubveil",
        "cutveil",
        "donutveil",
        "sandveil",
        "chirpveil",
        "backveil",
        "carbveil",
        "shiftveil",
        "calorveil",
        "nephveil",
        "catveil",
        "ventveil",
        "kathveil",
        "deaerveil",
        "nozzveil",
        "sodaveil",
        "tubeveil",
        "viscveil",
        "gleamveil",
        "admveil",
        "fidveil",
        "rotorveil",
        "floatveil",
        "ashwhin caustic",
        "rowanholt sour",
        "sallowfen turbine",
        "wychholt coil",
        "marshspit fly-ash",
        "owlmere fuel",
        "fogmere steam",
        "stoatfen bitumen",
        "rindleholt steam",
        "sonic-nozzle remaining",
        "sodium-ion remaining",
        "vibrating-tube remaining",
        "rf-admittance remaining",
        "ubbelohde remaining",
        "toroidal inductive",
        "nephelometric remaining",
        "gamma-backscatter remaining",
        "ndir remaining co",
        "wobbe remaining",
        "venturi remaining",
        "katharometer remaining",
        "clark polarographic",
    )
    hits = []
    root = Path("/tmp")
    scan = (
        sorted(root.glob("nelb-r*/NOTES-r*.md"))
        + sorted(root.glob("nelb-r*/gen_r*.py"))
        + sorted(root.glob("nelb-r*/records_block.py"))
        + sorted(root.glob("nelb-r*/_recs.py"))
        + sorted(root.glob("nelb-r*/recs.py"))
        + sorted(root.glob("nelb-r*/batch-r*.jsonl"))
    )
    for n in scan:
        if "nelb-r67" in str(n):
            continue
        text = n.read_text(encoding="utf-8", errors="replace").casefold()
        for b in claimed:
            if b in text:
                hits.append(f"{n}:{b}")
    if hits:
        raise RuntimeError(f"r67 family/plant collision {hits}")
    blob = json.dumps([rec_202(), rec_203(), rec_204()], ensure_ascii=False).casefold()
    for s in steal:
        if s in blob:
            raise RuntimeError(f"r67 stole occupied family {s}")


def write_notes(records, lines, gate):
    import subprocess

    sizes = [len(x) for x in lines]
    file_size = BATCH.stat().st_size
    file_sha = hashlib.sha256(BATCH.read_bytes()).hexdigest()
    spikes = sum(r["raster"]["spikes"] for r in records)
    energy = spikes * 23
    isis = [r["raster"]["isi_count_identity"]["isi_total"] for r in records]
    events = [len(r["spike_events"]) for r in records]
    rewards = []
    for r in records:
        lv = r["language_view"]
        rewards.append(lv["trajectory"]["reward_components"]["total"])
        for k, v in lv.items():
            if k.startswith("trajectory") and k != "trajectory":
                rewards.append(v["reward_components"]["total"])
    probe = subprocess.run(
        [
            sys.executable,
            str(PIPELINES / "spike_probe.py"),
            "--strict",
            str(BATCH),
        ],
        check=False,
        capture_output=True,
        text=True,
    )
    probe_out = (probe.stdout or "") + (probe.stderr or "")
    if probe.returncode != 0:
        raise RuntimeError(f"spike_probe failed {probe.returncode}: {probe_out[-2000:]}")
    strict = subprocess.run(
        [
            sys.executable,
            str(PIPELINES / "check_records.py"),
            "--strict",
            str(OUT_DIR),
        ],
        check=False,
        capture_output=True,
        text=True,
    )
    if strict.returncode != 0:
        raise RuntimeError(
            f"check_records --strict failed: {(strict.stdout or '') + (strict.stderr or '')}"
        )

    gc = []
    for r in records:
        per = r["gate_compute"]["per_check"]
        gc.append("+".join(str(c["spikes"]) for c in per))
    wins = [r["raster"]["window_ms"] for r in records]
    n_sp = [r["raster"]["spikes"] for r in records]
    n_neu = [r["raster"]["neurons"] for r in records]
    rates = [r["raster"]["mean_rate_hz"] for r in records]
    tfs = [r["raster"]["routing"]["third_factor"]["modulator"] for r in records]
    taus = [r["raster"]["routing"]["third_factor"]["tau_e_s"] for r in records]
    reward_s = "/".join(f"+{x:.2f}" for x in rewards)
    notes = f"""# Neuromorphic Event + Language Bridge — NOTES round 67
Run: 2026-09-02-final-heavy · Factory: neuromorphic-event-language-bridge · Generator: grok-4.6 · Output: `batch-r67.jsonl` (3 paired artifacts, 6 ThalamicTrajectories)
Rights: RM-793 research-only (SpaceXAI/xAI grok-4.6, SuperGrok Heavy chat). Not training_ready. Do not publish into `outputs/raw/` from this generator; operator uses `pipelines/round_txn.py`. Staged only at `/tmp/nelb-r67/`.

## Context / de-duplication
Prior corpus read: 2026-08-30 NOTES-r01–r04, 2026-08-17-w3 NOTES-r12 family table, `/tmp/nelb-r13-holes.md` + `/tmp/nelb-r13-premises.md`, staged `/tmp/nelb-r13` through `/tmp/nelb-r66` complete batches/NOTES (r64/r61/r62/r63/r65/r66 landed before this generator locked plants). IDs: r13=`040`–`042` … r66=`199`–`201`, this round `nelb-r67-202`…`204` as assigned. Envelope cloned from complete r59 (`language_view.trajectory` + operational t2 + `spike_events` + `raster` + `gate_snn` + `isi_histogram` + `routing.third_factor` + 15-key RM-793 `meta.rights`).

Banned this round (committed + staged leftover-mill r13–r66): not VOD-SNN replay, not pharma cold-chain, not stack-gas CEMS; not r13 FBG glaze / Frostlip quench / Oxbow VRFB; not r14 BOTDA / QCM-D / MsS T(0,1); not r15 SAW torque / CRDS HF / PGNAA; not r16 IFOG / transmon readout / hyperspectral crop; not r17 MEMS accel array / muon ore-pass / industrial x-ray DR; not r18 optogenetic PV / 905 nm LiDAR snow / clamp-on transit-time; not r19 LIBS Cu / QEPAS DGA / LFV Al; not r20 Kaplan LDV / THz-TDS radome moisture / ECT CFB; not r21 THz-TDS bondline / ECA FSW lift-off / LIBS C; not r22 ECT pneumatic riser / TDLAS NH3 / LIBS tap; not r23 lock-in thermography CFRP / PAUT TFM girth / EN CUI; not r24 RUS porcelain / N-16 transit-time loop / helium RGA; not r25 Faraday FOCT / blade tip-timing / acoustic pyrometry; not r26 SPR cyanide / VW viscometer / MW cavity moisture; not r27 MFL AST / NMR T2 / Cs-137 densitometry; not r28 MFL ILI / JNT / CRNS; not r29 Coriolis bitumen / CARS TIT / Zn-Ka XRF; not r30 Mössbauer FCC / GB-InSAR tailings / ellipsometry PECVD; not r31 CTA hot-wire / rhodium SPND / LII soot; not r32 PALS / 14N NQR / SFRA; not r33 digital shearography hull / hydrogen permeation / FMCW BOF lining; not r34 handheld XRF Cr-Kα / Coriolis tube-twist / GPR liner cover; not r35/r37 mud-pulse MWD / Barkhausen / Lamb-wave; not r36 Pockels GIS / PEC coated riser / confocal chromatic; not r38 OCT TBC / DCPD girth / impact-echo; not r39 phosphor-lifetime / vortex-shedding / GWR foam; not r40 He-3 neutron-backscatter / Kr-85 beta / 532 nm Raman; not r41–r43 cyclotron BPM / alanine EPR / ADCP ice-jam; not r44 TOFD / laser-flash Parker / TDR remaining-length; not r45 Seebeck ferrite / RFEC / LPR / ACFM; not r46 paramagnetic O2 / TOFD ligament / TEOM PM; not r47 Faraday magmeter / PDA d32 / acoustoelastic; not r48 C-SAM / FDS tanδ / MCSA; not r49 EMAT SH / FBRM D50 / ACFM; not r50 OFDR / XRD sin²ψ / FSM; not r51 Gardon / chilled-mirror / DIC; not r52 CLD NOx / API-670 proximity / thermal-mass capillary; not r53 ER probe / Fabry-Perot pressure / inductive debris; not r54 wire-mesh void / UCI hardness / MAE case depth; not r55 FID THC / turbine k-factor / magnetostrictive level; not r56 IRIS pulse-echo / dual-wavelength pyrometer / UV-fluorescence OIW; not r57 orifice-plate dP / PID VOC / four-electrode conductivity; not r58 critical-angle Brix / WLI thickness / annubar pitot; not r59 UV-DOAS SO2 / Al2O3 moisture / strain-gauge load-cell; not r60 electrochemical H2S / TEV PD / dielectric water-cut; not r61 toroidal conductivity / acoustic sand / FMCW tank-radar; not r62 gamma-backscatter lining / NDIR CO / ultrasonic-Doppler slurry; not r63 Wobbe calorific / nephelometric turbidity / cation conductivity; not r64 venturi dP steam / katharometer H2 / Clark polarographic DO; not r65 sonic-nozzle critical-flow / sodium-ion condensate / vibrating-tube density; not r66 Ubbelohde viscosity / 60-degree gloss / RF-admittance silo level. Plants not reused: Nettlewake, Frostlip, Oxbow, Ashwhin, Rowanholt, Sallowfen, Wychholt, Marshspit, Owlmere, Fogmere, Stoatfen, Rindleholt, Woadfen, Pellmire, Peatshaw, Woldshaw, Bramblefen, Slagholt, Copsewhin, Siltwharf, Thornmere, Marlfell, Birchfen, plus r13–r66 plant list.

This round introduces three unused industrial families (coulometric Karl Fischer remaining transformer water, polarimetric remaining sucrose, hydrostatic remaining phosphoric-acid tank level) on new invented plants. r65 sodium-ion / vibrating-tube and r66 RF-admittance / Ubbelohde / gloss are not restaged.

Adjacencies declared in-pair then kept physically distinct:
- **202 coulometric KF water** is a Faraday titration charge of a transformer conservator, not r59 Al2O3 moisture, not r51 chilled-mirror dew-point, not r26 MW-cavity moisture, not r20/r21 THz-TDS, not r14 QCM-D, not r28 CRNS, not r65 sodium-ion condensate.
- **203 polarimetric sucrose** is an optical-rotation cell of a sugar pan, not r58 critical-angle Brix, not r63 nephelometric turbidity, not r66 60-degree gloss, not r58 WLI thickness, not r59 UV-DOAS, not r26 SPR.
- **204 hydrostatic dP level** is a rho-g remaining height of a phosphoric-acid tank, not r39 GWR foam, not r55 magnetostrictive waveguide, not r61 FMCW tank-radar, not r66 RF-admittance silo, not r44 TDR, not r64 venturi dP steam, not r57 orifice-plate dP, not r65 vibrating-tube density.

## Round 67 batch summary (3 pairs, 6 trajectories)

| id | modality (NEW family) | domain | decisions | headline |
|----|----------------------|--------|-----------|----------|
| nelb-r67-202 | coulometric Karl Fischer remaining water of a transformer conservator (k_f·Q/m ppm, Karlveil last-good denial, 18 min dry-out floor) | Wetherholt Transformer WT-4 conservator C-2 (invented): 2.50*8.00/2.00 reconstructs 10.00 ppm while Karlveil still reads 1.80 ppm | REJECT (+0.43) / MODIFY (+0.34) | serialized `2.50*8.00/2.00=10.00`; `10.00*2.00/2.50=8.00`; conjunctive SOP (w AND SNR) forbids continue-energize; three-party collusion includes the KF-cloud infra owner; companion t2 vacuum dry-out hold, bank ESD refused; sim_or_real=designed |
| nelb-r67-203 | polarimetric remaining sucrose of a sugar pan (k_r·α/L g/100mL, Polveil last-good denial, 24 min water-zero floor) | Mallowholt Sugar MH-5 pan P-2 (invented, HIL dummy in POL-HIL-4): 2.00*8.00/2.00 reconstructs 8.00 g/100mL while Polveil still reads 1.20 g/100mL | MODIFY (+0.40) / ACCEPT (+0.35) | serialized `2.00*8.00/2.00=8.00` and `8.00*2.00/2.00=8.00`; keep-pan refused; cell tech Ivo Harn exonerated (missing water-zero AE, UTC vs UTC+2); companion t2 new-cell restart; sim_or_real=hil |
| nelb-r67-204 | hydrostatic remaining dP level of a phosphoric-acid tank (dP/(ρ·g) m, Headveil last-good denial, 12 min survey floor) | Vetchwharf Phosphate VW-6 tank TK-4 (invented, simulated HYDRO-SIM-6): 192000/(1600*10.00) reconstructs 12.00 m while Headveil still reads 4.80 m | ACCEPT (+0.41) / REJECT (+0.36) | serialized `192000/(1600*10.00)=12.00`; `1600*10.00*12.00/1000=192.00`; bounded ACCEPT of TK-4 only; TK-1..TK-3 out of scope; companion t2 REJECTS skip-survey; sim_or_real=simulated |

Decision spread: REJECT / MODIFY / MODIFY / ACCEPT / ACCEPT / REJECT — **2A/2M/2R**. All three enums used, and all three sit on **leads**. Provenance spread: designed / hil / simulated (one each; never live-plant). IDs `nelb-r67-202`…`204` plus t1/t2 suffixes.

## Raster sidecar
Every record carries `raster` + top-level `gate_snn` + `gate_compute`. Windows {wins[0]:.0f}/{wins[1]:.0f}/{wins[2]:.0f} ms; `window_s == window_ms/1000` exactly; `spikes == round(neurons·rate·window_s)` with zero slack ({n_sp[0]}/{n_sp[1]}/{n_sp[2]} at {rates[0]}/{rates[1]}/{rates[2]} Hz over {n_neu[0]}/{n_neu[1]}/{n_neu[2]} neurons); `energy_pJ = spikes·23` and `energy_uJ = spikes·23e-6` exact ({n_sp[0]*23}/{n_sp[1]*23}/{n_sp[2]*23} pJ). Routing source/target + 3-entry tables + `third_factor` on all three (modulators {tfs[0]} / {tfs[1]} / {tfs[2]}; τe {taus[0]}/{taus[1]}/{taus[2]} s as consistent `tau_e_s`+`tau_e_ms` pairs). Excerpts integer `t_us`, in-window, `neuron_id`-bounded, sorted, full-window by construction, per-spike amplitude with adaptation (0.82**k) plus noise. ISI histograms from the full window, bins ≥1 ms, counts sum to `spikes − distinct_active_neurons` ({isis[0]}/{isis[1]}/{isis[2]}). Same-neuron gaps ≥1100 µs pre-round, ≥1000 µs serialized. `gate_snn` on all three: decisions REJECT/MODIFY/ACCEPT matching each lead trajectory; every rate-declaring population's budget exact against its decision window. `gate_compute.per_check` windows 32–40 ms, budgets exact ({gc[0]} / {gc[1]} / {gc[2]}). Main streams: {events[0]}/{events[1]}/{events[2]} events (inside the 5–40 cap), strictly increasing `t_rel_ms` only (no `t_ms` mix), same-channel refractory ≥0.8 ms (202 KF pair at 1.4 ms, 203 polarimeter pair at 1.2 ms, 204 hydrostatic pair at 1.5 ms).

## Self-critique

### Edge cases added vs still thin
- **Added:** first coulometric Karl Fischer remaining-water family on a transformer conservator with a recomputable w=k_f·Q/m (`10.00 ppm`) plus charge and I·t identities and three-party collusion including the KF-cloud infra owner; first polarimetric remaining-sucrose family on a sugar pan with recomputable C=k_r·α/L (`8.00 g/100mL`) and rotation identity, plus a resolved-innocent cell tech (timezone-skipped water-zero, not last-to-badge); first hydrostatic remaining-level family on a phosphoric-acid tank with recomputable h=dP/(ρ·g) (`12.00 m`) plus dP and SG identities; bounded ACCEPT whose out-of-scope clause is adjacent acid tanks rather than a hopper/taphole/dump cap; operational t2 on all three (vacuum dry-out hold, new-cell restart, skip-survey refusal); provenance trio designed/hil/simulated; 18 min / 24 min / 12 min slow floors in-stream.
- **Still thin:** (i) 202's k_f is a lumped C→ppm gain, not a 10.71 C/mg Faraday table — a reagent-blank hop that fakes 10.00 ppm inside a 1.80 ppm Karlveil corridor is unwritten; (ii) 203's k_r is a lumped rotation factor, not a temperature / wavelength / quartz-control table, so a thermal hop that fakes 8.00 g/100mL is unwritten; (iii) 204's g_coupon is a lumped 10.00 m/s², not a density/temperature table, so a rho hop that fakes 12.00 m inside a 4.80 last-good is unwritten; (iv) vendor-only as a *lead* REJECT on a plant with *no* independent KF/polarimeter/hydrostatic head installed yet remains slightly harder — 202/203 still have plant heads; (v) stream amplitudes remain authored constants (raster draws are the only seeded noise); (vi) r65/r66 densification leftovers were left for those rounds' owners.

### Realism of noise / temporal fidelity
- Strong: 202's 10.00 ppm, Q 8.00 C, and 18.0 min dry-out (`6000+1080=7080 s`) recompute from the record; 203's 8.00 g/100mL, α 8.00 deg, and 24.0 min water-zero (`2820+1440=4260 s`) recompute; 204's 12.00 m, dP 192.00 kPa, and 12.0 min survey (`6000+720=6720 s`) recompute. Raster adaptation (0.82**k plus 4% noise) and the 1.2–1.5 ms physics pairs give the 5–40 stream a raster-scale motif without violating 0.8 ms same-channel refractory.
- **Gaps, honestly:** (i) 5–40 cap still forces heavy thinning (1 Hz KF kept as 4 Q points; 1 Hz polarimeter kept as 4 α points; 10 Hz hydrostatic kept as 4 dP points); (ii) 202's post-stop 15.00 ppm is a later sample, not a closed-loop vacuum controller; (iii) 203 HIL coupon times an in-service pan isolate that the stream does not independently witness on a second live pan until the new cell starts; (iv) no gate_snn input→output volley pair at raster resolution this round (r04-a1 already staged that).

### Training value (SNN/LSM + agentic)
Distillation targets: coulometric-KF w=k_f·Q/m reconstruction head plus charge identity; conjunctive isolate floor vs continue-energize vs bank ESD; Karlveil-infra collusion; polarimeter C=k_r·α/L head plus rotation identity; isolate-floor pan vs keep-whole vs liquor dump; exoneration against last-to-badge social pressure; hydrostatic h=dP/(ρ·g) and SG identities; bounded ACCEPT with tank-out-of-scope; skip-survey refusal under survey takt. Agentic value concentrates in three patterns: reconstruction-as-SoT on a physical water/sucrose/level load the raw corridor cannot see, earned ACCEPT with an explicit physical out-of-scope object (TK-1..TK-3), and stop-then-hold so a REJECT does not become a bank/header/overflow kill.

## What a later leftover-mill round should add (next densification target)
1. **Faraday 10.71 C/mg table** on a non-WT-4 conservator so a reagent-blank hop fakes 10.00 ppm inside a 1.80 ppm Karlveil corridor, closing 202's lumped-k_f gap.
2. **Temperature / wavelength / quartz-control table** on a non-MH-5 pan so a thermal hop can fake 8.00 g/100mL while mean rotation looks healthy.
3. **Density / temperature table** on a non-VW-6 tank so a rho hop can fake 12.00 m inside a 4.80 last-good corridor.
4. **Vendor-only as a lead REJECT** on a plant that has no independent KF/polarimeter/hydrostatic head installed yet (202/203 still had plant heads).
5. **Do not restage** VOD-SNN replay, pharma cold-chain, CEMS, FBG glaze, Frostlip quench, Oxbow VRFB, IFOG, transmon, hyperspectral, MEMS array, muon ore-pass, industrial x-ray, optogenetic stim, 905 nm LiDAR snow, clamp-on transit-time, LIBS, QEPAS, LFV, Kaplan LDV, THz-TDS, ECT, TDLAS NH3, lock-in thermography, PAUT TFM, EN CUI, RUS porcelain, N-16 loop flow, helium RGA, Faraday FOCT, blade tip-timing, acoustic pyrometry, SPR, vibrating-wire, microwave-cavity, MFL, NMR T2, nucleonic densitometry, JNT, CRNS, Coriolis, CARS, XRF, Mössbauer, GB-InSAR, ellipsometry, CTA, SPND, LII, PALS, NQR, SFRA, digital shearography, hydrogen permeation, FMCW lining, GPR, Pockels, PEC, confocal, mud-pulse, Barkhausen, Lamb-wave, OCT, DCPD, impact-echo, cyclotron BPM, alanine EPR, ADCP, vortex-shedding, Kr-85 beta, 532 nm Raman, phosphor-lifetime, guided-wave-radar, paramagnetic O2, TOFD, TEOM, magmeter, PDA, acoustoelastic, C-SAM, FDS tanδ, MCSA, EMAT SH, FBRM, ACFM, OFDR, XRD sin²ψ, FSM, Gardon, chilled-mirror, DIC, CLD NOx, proximity orbit, thermal-mass, ER probe, Fabry-Perot, inductive debris, wire-mesh, UCI, MAE, FID THC, turbine k-factor, magnetostrictive level, IRIS, ratio pyrometer, UV-fluorescence oil-in-water, orifice-plate, PID VOC, four-electrode conductivity, critical-angle Brix, WLI, annubar, UV-DOAS, Al2O3 moisture, load-cell, electrochemical H2S, TEV PD, dielectric water-cut, toroidal conductivity, acoustic sand, FMCW tank-radar, gamma-backscatter, NDIR CO, ultrasonic-Doppler, Wobbe, nephelometric turbidity, cation conductivity, venturi dP, katharometer, Clark DO, sonic-nozzle, sodium-ion, vibrating-tube density, Ubbelohde, 60-degree gloss, RF-admittance silo, Wetherholt WT-4 KF, Mallowholt POL-HIL-4, or Vetchwharf HYDRO-SIM-6. Leave r65/r66 densification leftovers for those rounds' owners. Do not steal r66 IDs `199`–`201`.

## Verification
`batch-r67.jsonl`: 3 lines, `json.loads`-clean (allow_nan=False), {sizes[0]}/{sizes[1]}/{sizes[2]} bytes (file {file_size}, sha256 `{file_sha}`). Staged at `/tmp/nelb-r67/` only. Repo gates: `check_records.check_jsonl` with `FactoryStaging(enabled=True)` → 0 errors, 0 warnings, kinds `{{bridge_pair: 3}}`; `python3 pipelines/check_records.py --strict /tmp/nelb-r67` → 0/0; `curate_bridge.raster_status(..., require_raster=True, require_routing_table=True)` → raster_valid and gate_snn_valid true, empty reason codes; `curate_record(...)` → 3× retain / `BRIDGE_EVENTS_ALREADY_GLOBALLY_ORDERED`; `verify_batch_for_frontier(strict=True)` → 3 verified, 0 inconclusive, 0 failed; `python3 pipelines/spike_probe.py --strict /tmp/nelb-r67/batch-r67.jsonl` → loaded 3, unloadable 0, problems [], third_factor_routes 3, gate_snn_records 3, spikes {spikes}, energy_pJ {energy}. Build-time asserts: global time order; same-channel ≥0.8 ms; 5–40 events ({events[0]}/{events[1]}/{events[2]}); excerpt integer bounds, neuron bounds, sort, 1 ms per-neuron floor; ISI identity {isis[0]}/{isis[1]}/{isis[2]}; spike budgets exact; energy pJ/µJ exact; reward totals equal two-decimal component sums ({reward_s}); gate_snn decisions match lead `safety_decision.decision`; `state.sim_or_real` ∈ {{designed, hil, simulated}}; `meta.round=67`, `meta.factory=neuromorphic-event-language-bridge`, `meta.generator=grok-4.6`, `meta.run_label=2026-09-02-final-heavy`; `meta.rights` 15-key RM-793 stamp (`intended_use=research_only`, `linear_issue=RM-793`, `generated_at={GENERATED_AT}`); no hidden-reasoning keys; no `provenance` objects; no live-plant claims; no `training_ready`; all 9 record/trajectory ids unique. Raster seeds 202609202/202609203/202609204, MT19937.

Honest novelty accounting: 3/3 modality families are new versus the whole committed factory and versus staged leftover-mill r13–r66. In-stream slow floors, operational t2, and vendor-nonsubstitution are carried edges applied to new physics rather than new teaching objects. Three-party collusion and exoneration were already taught on r13 quench/VRFB and later leftover-mill rounds, so those heads are carried onto new sensors. Against that: bounded-accept-with-scope-limit, reconstruction-as-SoT, conjunctive SOP, and custody vocabulary are carried; the 5–40 cap is a density constraint not a new teaching object; 54 prior leftover-mill rounds already taught custody/governance at high sophistication. Net: about two-fifths of the round's scenario/edge mass is genuinely novel.

Novel coverage: 40%
"""
    NOTES.write_text(notes, encoding="utf-8")
    print("wrote", NOTES, "bytes", NOTES.stat().st_size)


def main():
    occupancy_preflight()
    records = [rec_202(), rec_203(), rec_204()]
    local_checks(records)
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    lines = [
        json.dumps(r, ensure_ascii=False, allow_nan=False, separators=(",", ":"))
        for r in records
    ]
    BATCH.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("wrote", BATCH, "bytes", BATCH.stat().st_size, "lines", len(lines))
    for i, r in enumerate(records):
        print(
            r["id"],
            "events",
            len(r["spike_events"]),
            "excerpt",
            len(r["raster"]["excerpt"]),
            "spikes",
            r["raster"]["spikes"],
            "isi",
            r["raster"]["isi_count_identity"],
            "sim",
            r["language_view"]["trajectory"]["state"]["sim_or_real"],
            "dec",
            r["language_view"]["trajectory"]["safety_decision"]["decision"],
            "bytes",
            len(lines[i]),
        )
    gate = repo_validate(records)
    write_notes(records, lines, gate)


if __name__ == "__main__":
    main()
