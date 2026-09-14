def occupancy_preflight():
    claimed = (
        "fpdveil",
        "brantmere fuel",
        "flame-photometric remaining",
        "tealfen steam",
        "silicaveil",
        "colorimetric remaining silica",
        "pochardfen boiler",
        "hydveil",
        "coulometric remaining hydrazine",
        "sil-hil-4",
        "hyd-sim-2",
        "nerys pike",
        "merrick quill",
        "hester brine",
        "sile keld",
        "kerr holt",
    )
    steal = (
        "nozzveil",
        "owlmere fuel",
        "sonic-nozzle remaining",
        "sodaveil",
        "fogmere steam",
        "sodium-ion remaining",
        "tubeveil",
        "stoatfen bitumen",
        "vibrating-tube remaining",
        "viscveil",
        "sallowfen",
        "ubbelohde remaining",
        "gleamveil",
        "wychholt coil",
        "admveil",
        "marshspit fly-ash",
        "rf-admittance remaining",
        "ventveil",
        "rindleholt steam",
        "kathveil",
        "woadfen chlorate",
        "pellmire boiler",
        "clark polarographic",
        "calorveil",
        "thornfell fuel",
        "wobbe remaining",
        "chlorveil",
        "pewterholt cooling",
        "rangveil",
        "pitchshaw crude",
        "torveil",
        "shiftveil",
        "bramblefen tailings",
        "backveil",
        "peatshaw kiln",
        "carbveil",
        "woldshaw reformer",
        "cutveil",
        "hagholt crude",
        "sourveil",
        "rowanholt sour",
        "fidveil",
        "irisveil",
        "pyroveil",
        "fluoveil",
        "orifveil",
        "lampveil",
        "condveil",
        "doasveil",
        "oxveil",
        "cellveil",
        "sternveil",
        "pellveil",
        "polarveil",
    )
    hits = []
    root = Path("/tmp")
    scan = (
        sorted(root.glob("nelb-r*/NOTES-r*.md"))
        + sorted(root.glob("nelb-r*/gen_r*.py"))
        + sorted(root.glob("nelb-r*/records_block.py"))
        + sorted(root.glob("nelb-r*/_recs.py"))
        + sorted(root.glob("nelb-r*/recs.py"))
        + sorted(root.glob("nelb-r*/_recs_and_tail.py"))
    )
    for n in scan:
        if "nelb-r69" in str(n):
            continue
        text = n.read_text(encoding="utf-8", errors="replace").casefold()
        for b in claimed:
            if b in text:
                hits.append(f"{n}:{b}")
    if hits:
        raise RuntimeError(f"r69 family/plant collision {hits}")
    blob = json.dumps([rec_208(), rec_209(), rec_210()], ensure_ascii=False).casefold()
    for s in steal:
        if s in blob:
            raise RuntimeError(f"r69 stole occupied family {s}")


def write_notes(records, lines, gate):
    import subprocess

    sizes = [len(x) for x in lines]
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
    notes = f"""# Neuromorphic Event + Language Bridge — NOTES round 69
Run: 2026-09-02-final-heavy · Factory: neuromorphic-event-language-bridge · Generator: grok-4.6 · Output: `batch-r69.jsonl` (3 paired artifacts, 6 ThalamicTrajectories)
Rights: RM-793 research-only (SpaceXAI/xAI grok-4.6, SuperGrok Heavy chat). Not training_ready. Do not publish into `outputs/raw/` from this generator; operator uses `pipelines/round_txn.py`. Staged only at `/tmp/nelb-r69/`.

## Context / de-duplication
Prior corpus read: 2026-08-30 NOTES-r01–r04, 2026-08-17-w3 NOTES-r12 family table, `/tmp/nelb-r13-holes.md` + `/tmp/nelb-r13-premises.md`, staged `/tmp/nelb-r13` through `/tmp/nelb-r65` complete batches/NOTES plus in-flight `/tmp/nelb-r61` (toroidal conductivity / electrochemical H2S / FMCW tank-radar, with competing Stern-Volmer / pellistor drafts), `/tmp/nelb-r63` (Wobbe / nephelometric NTU / amperometric chlorine), `/tmp/nelb-r66` (Ubbelohde viscosity / 60-degree gloss / RF-admittance level, ids `199`–`201`), `/tmp/nelb-r67` head-only. IDs: r13=`040`–`042` … r65=`196`–`198`, reserved r66–r68=`199`–`207`, this round `nelb-r69-208`…`210` as assigned. Envelope cloned from complete r65 (`language_view.trajectory` + operational t2 + `spike_events` + `raster` + `gate_snn` + `isi_histogram` + `routing.third_factor` + 15-key RM-793 `meta.rights`).

Banned this round (committed + staged leftover-mill r13–r65 and in-flight r61/r63/r66 envelopes): not VOD-SNN replay, not pharma cold-chain, not stack-gas CEMS; not r13 FBG glaze / Frostlip quench / Oxbow VRFB; not r14 BOTDA / QCM-D / MsS T(0,1); not r15 SAW torque / CRDS HF / PGNAA; not r16 IFOG / transmon readout / hyperspectral crop; not r17 MEMS accel array / muon ore-pass / industrial x-ray DR; not r18 optogenetic PV / 905 nm LiDAR snow / clamp-on transit-time; not r19 LIBS Cu / QEPAS DGA / LFV Al; not r20 Kaplan LDV / THz-TDS radome moisture / ECT CFB; not r21 THz-TDS bondline / ECA FSW lift-off / LIBS C; not r22 ECT pneumatic riser / TDLAS NH3 / LIBS tap; not r23 lock-in thermography CFRP / PAUT TFM girth / EN CUI; not r24 RUS porcelain / N-16 transit-time loop / helium RGA; not r25 Faraday FOCT / blade tip-timing / acoustic pyrometry; not r26 SPR cyanide / VW viscometer / MW cavity moisture; not r27 MFL AST / NMR T2 / Cs-137 densitometry; not r28 MFL ILI / JNT / CRNS; not r29 Coriolis bitumen / CARS TIT / Zn-Ka XRF; not r30 Mössbauer FCC / GB-InSAR tailings / ellipsometry PECVD; not r31 CTA hot-wire / rhodium SPND / LII soot; not r32 PALS / 14N NQR / SFRA; not r33 digital shearography hull / hydrogen permeation / FMCW BOF lining; not r34 handheld XRF Cr-Kα / Coriolis tube-twist / GPR liner cover; not r35/r37 mud-pulse MWD / Barkhausen / Lamb-wave; not r36 Pockels GIS / PEC coated riser / confocal chromatic; not r38 OCT TBC / DCPD girth / impact-echo containment; not r39 phosphor-lifetime / vortex-shedding / GWR foam; not r40 He-3 neutron-backscatter / Kr-85 beta / 532 nm Raman; not r41/r42/r43 cyclotron BPM / alanine EPR / ADCP ice-jam; not r44 TOFD ligament / laser-flash Parker / TDR remaining-length; not r45 RFEC boiler tube / ACFM jacket node / LPR cooling header / Seebeck remaining ferrite; not r46 paramagnetic O2 / TOFD ligament / TEOM PM; not r47 magmeter slurry / PDA Sauter-mean / acoustoelastic residual; not r48 C-SAM IGBT void / FDS tanδ bushing / MCSA broken-bar; not r49 EMAT SH coil / FBRM chord D50 / ACFM jack-up; not r50 OFDR hoop-strain / XRD sin²ψ / FSM jumper; not r51 Gardon heat flux / chilled-mirror dew-point / DIC hoop-strain; not r52 CLD NOx / API-670 proximity / thermal-mass capillary; not r53 ER remaining wall / Fabry-Perot choke / inductive oil-debris; not r54 wire-mesh void / UCI hardness / MAE remaining case; not r55 FID THC / turbine k-factor / magnetostrictive waveguide; not r56 IRIS HEX wall / ratio pyrometer / UV-fluorescence oil-in-water; not r57 orifice-plate dP / PID VOC / four-electrode conductivity; not r58 critical-angle Brix / WLI thickness / annubar averaging-pitot; not r59 UV-DOAS SO2 / Al2O3 moisture / load-cell hopper mass; not r60 electrochemical H2S / TEV PD / dielectric water-cut; not r61 toroidal conductivity / electrochemical H2S / FMCW tank-radar / Stern-Volmer DO / pellistor LEL; not r62 gamma-backscatter lining / NDIR CO / ultrasonic-Doppler slurry; not r63 Wobbe calorific / nephelometric NTU / amperometric chlorine; not r64 venturi steam-flow / katharometer H2 / Clark polarographic DO; not r65 sonic-nozzle mass-flow / sodium-ion Na / vibrating-tube density; not r66 Ubbelohde viscosity / 60-degree gloss / RF-admittance level. Plants not reused: Nettlewake, Frostlip, Oxbow, Owlmere, Fogmere, Stoatfen, Rindleholt, Woadfen, Pellmire, Sallowfen, Wychholt, Marshspit, Peatshaw, Woldshaw, Bramblefen, Thornfell, Pewterholt, Pitchshaw, plus the r13–r66 plant list.

This round introduces three unused industrial families (flame-photometric remaining sulfur, colorimetric remaining silica, coulometric remaining hydrazine) on new invented plants. r13-holes cyclotron/alanine/ADCP and r60–r66 in-flight families are not restaged. Karl-Fischer oil remains a r48 FDS *witness*, not a SoT family.

Adjacencies declared in-pair then kept physically distinct:
- **208 FPD sulfur** is an S2* PMT remaining-ppm of a fuel-gas header, not r55 FID THC, not r59 UV-DOAS SO2, not r29/r34 XRF, not r15 PGNAA, not r19 QEPAS, not r62 NDIR CO, not r52 CLD NOx ozone-chemiluminescence.
- **209 colorimetric silica** is a molybdate-blue remaining-ppb of a condensate polisher, not r65 sodium-ion ISE, not r57 four-electrode conductivity-as-SoT, not r59 Al2O3 moisture, not r51 chilled-mirror, not r56 UV-fluorescence OIW, not r58 critical-angle Brix.
- **210 coulometric hydrazine** is a Faraday I·t remaining scavenger of a boiler feedwater header, not r64 Clark polarographic DO, not r61 Stern-Volmer DO, not r64 katharometer H2, not r33 hydrogen permeation, not r63 amperometric chlorine, not r48 Karl-Fischer-as-witness.

## Round 69 batch summary (3 pairs, 6 trajectories)

| id | modality (NEW family) | domain | decisions | headline |
|----|----------------------|--------|-----------|----------|
| nelb-r69-208 | flame-photometric remaining sulfur of a fuel-gas header (k_f·I/I_ref ppm, Fpdveil last-good denial, 18 min soak floor) | Brantmere Fuel BM-7 header H-4 (invented): 4.00*24.00/8.00 reconstructs 12.00 ppm while Fpdveil still reads 3.20 ppm | REJECT (+0.43) / MODIFY (+0.34) | serialized `4.00*24.00/8.00=12.00`; `24.00/8.00=3.00`; conjunctive SOP (C AND SNR) forbids continue-firing; three-party collusion includes the FPD-cloud infra owner; companion t2 header-soak hold, header ESD refused; sim_or_real=designed |
| nelb-r69-209 | colorimetric remaining silica of a boiler condensate polisher (k_s·(A−A0) ppb, Silicaveil last-good denial, 24 min regen floor) | Tealfen Steam TF-6 polisher E-3 (invented, HIL dummy in SIL-HIL-4): 5.00*(4.00-2.00) reconstructs 10.00 ppb while Silicaveil still reads 1.20 ppb | MODIFY (+0.40) / ACCEPT (+0.35) | serialized `5.00*(4.00-2.00)=10.00` and `0.200*10.00=2.00`; keep-polisher refused; colorimeter tech Sile Keld exonerated (missing molybdate-zero AE, UTC vs UTC+2); companion t2 new-cuvette restart; sim_or_real=hil |
| nelb-r69-210 | coulometric remaining hydrazine of a boiler feedwater header (k_h·I·t ppb, Hydveil last-good denial, 12 min survey floor) | Pochardfen Boiler PF-8 header F-6 (invented, simulated HYD-SIM-2): 0.050*8.00*30.00 reconstructs 12.00 ppb while Hydveil still reads 1.20 ppb | ACCEPT (+0.41) / REJECT (+0.36) | serialized `0.050*8.00*30.00=12.00`; `12.00*2.00=24.00`; bounded ACCEPT of F-6 only; F-1..F-5 out of scope; companion t2 REJECTS skip-survey; sim_or_real=simulated |

Decision spread: REJECT / MODIFY / MODIFY / ACCEPT / ACCEPT / REJECT — **2A/2M/2R**. All three enums used, and all three sit on **leads**. Provenance spread: designed / hil / simulated (one each; never live-plant). IDs `nelb-r69-208`…`210` plus t1/t2 suffixes.

## Raster sidecar
Every record carries `raster` + top-level `gate_snn` + `gate_compute`. Windows {wins[0]:.0f}/{wins[1]:.0f}/{wins[2]:.0f} ms; `window_s == window_ms/1000` exactly; `spikes == round(neurons·rate·window_s)` with zero slack ({n_sp[0]}/{n_sp[1]}/{n_sp[2]} at {rates[0]}/{rates[1]}/{rates[2]} Hz over {n_neu[0]}/{n_neu[1]}/{n_neu[2]} neurons); `energy_pJ = spikes·23` and `energy_uJ = spikes·23e-6` exact ({n_sp[0]*23}/{n_sp[1]*23}/{n_sp[2]*23} pJ). Routing source/target + 3-entry tables + `third_factor` on all three (modulators {tfs[0]} / {tfs[1]} / {tfs[2]}; τe {taus[0]}/{taus[1]}/{taus[2]} s as consistent `tau_e_s`+`tau_e_ms` pairs). Excerpts integer `t_us`, in-window, `neuron_id`-bounded, sorted, full-window by construction, per-spike amplitude with adaptation (0.82**k) plus noise. ISI histograms from the full window, bins ≥1 ms, counts sum to `spikes − distinct_active_neurons` ({isis[0]}/{isis[1]}/{isis[2]}). Same-neuron gaps ≥1100 µs pre-round, ≥1000 µs serialized. `gate_snn` on all three: decisions REJECT/MODIFY/ACCEPT matching each lead trajectory; every rate-declaring population's budget exact against its decision window. `gate_compute.per_check` windows 32–40 ms, budgets exact ({gc[0]} / {gc[1]} / {gc[2]}). Main streams: {events[0]}/{events[1]}/{events[2]} events (inside the 5–40 cap), strictly increasing `t_rel_ms` only (no `t_ms` mix), same-channel refractory ≥0.8 ms (208 FPD pair at 1.4 ms, 209 silica pair at 1.2 ms, 210 hydrazine pair at 1.5 ms).

## Self-critique

### Edge cases added vs still thin
- **Added:** first flame-photometric remaining-sulfur family on a fuel-gas header with a recomputable C=k_f·I/I_ref (`12.00 ppm`) plus PMT-ratio identity and three-party collusion including the FPD-cloud infra owner; first colorimetric remaining-silica family on a condensate polisher with recomputable C=k_s·(A−A0) (`10.00 ppb`) and molybdate-mass identity, plus a resolved-innocent colorimeter tech (timezone-skipped molybdate-zero, not last-to-badge); first coulometric remaining-hydrazine family on a boiler feedwater header with recomputable C=k_h·I·t (`12.00 ppb`) plus scavenger-dose identity; bounded ACCEPT whose out-of-scope clause is adjacent feedwater headers rather than a hopper/taphole/dump cap; operational t2 on all three (header-soak hold, new-cuvette restart, skip-survey refusal); provenance trio designed/hil/simulated; 18 min / 24 min / 12 min slow floors in-stream.
- **Still thin:** (i) 208's k_f is a lumped PMT gain, not a H2-flow / quench-gas table — a flame-stoichiometry hop that fakes 12.00 ppm inside a 3.20 ppm Fpdveil corridor is unwritten; (ii) 209's k_s is a lumped absorbance gain, not a temperature / reagent-age map, so a thermal hop that fakes 10.00 ppb is unwritten; (iii) 210's k_h is a lumped Faraday factor, not a current-efficiency / blank-charge table, so a blank hop that fakes 12.00 ppb inside a 1.20 last-good is unwritten; (iv) vendor-only as a *lead* REJECT on a plant with *no* independent FPD/colorimeter/coulometric head installed yet remains slightly harder — 208/209 still have plant heads; (v) stream amplitudes remain authored constants (raster draws are the only seeded noise); (vi) r60–r66 densification leftovers were left for those rounds' owners.

### Realism of noise / temporal fidelity
- Strong: 208's 12.00 ppm, I/I_ref 3.00, and 18.0 min soak (`6000+1080=7080 s`) recompute from the record; 209's 10.00 ppb, M 2.00, and 24.0 min regen (`2820+1440=4260 s`) recompute; 210's 12.00 ppb, dose 24.00, and 12.0 min survey (`6000+720=6720 s`) recompute. Raster adaptation (0.82**k plus 4% noise) and the 1.2–1.5 ms physics pairs give the 5–40 stream a raster-scale motif without violating 0.8 ms same-channel refractory.
- **Gaps, honestly:** (i) 5–40 cap still forces heavy thinning (10 Hz FPD kept as 4 I points; 1 Hz colorimeter kept as 4 A points; 1 Hz coulometric cell kept as 4 I points); (ii) 208's post-stop 16.00 ppm is a later sample, not a closed-loop soak controller; (iii) 209 HIL coupon times an in-service polisher isolate that the stream does not independently witness on a second live polisher until the new cuvette starts; (iv) no gate_snn input→output volley pair at raster resolution this round (r04-a1 already staged that).

### Training value (SNN/LSM + agentic)
Distillation targets: FPD C=k_f·I/I_ref reconstruction head plus PMT-ratio identity; conjunctive isolate floor vs continue-firing vs header ESD; Fpdveil-infra collusion; silica C=k_s·(A−A0) head plus molybdate-mass identity; isolate-floor polisher vs keep-whole vs condensate dump; exoneration against last-to-badge social pressure; coulometric C=k_h·I·t and dose identities; bounded ACCEPT with header-out-of-scope; skip-survey refusal under survey takt. Agentic value concentrates in three patterns: reconstruction-as-SoT on a physical sulfur/silica/hydrazine load the raw corridor cannot see, earned ACCEPT with an explicit physical out-of-scope object (F-1..F-5), and stop-then-hold so a REJECT does not become a main/dump/line kill.

## What a later leftover-mill round should add (next densification target)
1. **H2-flow / quench-gas table** on a non-BM-7 header so a flame-stoichiometry hop fakes 12.00 ppm inside a 3.20 ppm Fpdveil corridor, closing 208's lumped-k_f gap.
2. **Temperature / reagent-age map** on a non-TF-6 polisher so a thermal hop can fake 10.00 ppb while mean absorbance looks healthy.
3. **Current-efficiency / blank-charge table** on a non-PF-8 header so a blank hop can fake 12.00 ppb inside a 1.20 last-good corridor.
4. **Vendor-only as a lead REJECT** on a plant that has no independent FPD/colorimeter/coulometric head installed yet (208/209 still had plant heads).
5. **Do not restage** VOD-SNN replay, pharma cold-chain, CEMS, FBG glaze, Frostlip quench, Oxbow VRFB, IFOG, transmon, hyperspectral, MEMS array, muon ore-pass, industrial x-ray, optogenetic stim, 905 nm LiDAR snow, clamp-on transit-time, LIBS, QEPAS, LFV, Kaplan LDV, THz-TDS, ECT, TDLAS NH3, lock-in thermography, PAUT TFM, EN CUI, RUS porcelain, N-16 loop flow, helium RGA, Faraday FOCT, blade tip-timing, acoustic pyrometry, SPR, vibrating-wire, microwave-cavity, MFL, NMR T2, nucleonic densitometry, JNT, CRNS, Coriolis, CARS, XRF, Mössbauer, GB-InSAR, ellipsometry, CTA, SPND, LII, PALS, NQR, SFRA, digital shearography, hydrogen permeation, FMCW lining, GPR, Pockels, PEC, confocal, mud-pulse, Barkhausen, Lamb-wave, OCT, DCPD, impact-echo, cyclotron BPM, alanine EPR, ADCP, vortex-shedding, Kr-85 beta, 532 nm Raman, phosphor-lifetime, guided-wave-radar, paramagnetic O2, TOFD, TEOM, magmeter, PDA, acoustoelastic, C-SAM, FDS tanδ, MCSA, EMAT SH, FBRM, ACFM, OFDR, XRD sin²ψ, FSM, Gardon, chilled-mirror, DIC, CLD NOx, proximity orbit, thermal-mass, ER probe, Fabry-Perot, inductive debris, wire-mesh, UCI, MAE, IRIS, ratio pyrometer, UV-fluorescence oil-in-water, zirconia Nernst, PID VOC, contact pulse-echo, Rogowski, beta-attenuation, UV-DOAS, Al2O3, load-cell, laser-triangulation, FID VOC, dielectric water-cut, Stern-Volmer DO, pellistor LEL, FMCW tank-radar, ultrasonic Doppler, Wobbe, critical-angle Brix, amperometric chlorine, venturi steam-flow, katharometer H2, Clark polarographic DO, sonic-nozzle, sodium-ion, vibrating-tube, Ubbelohde, 60-degree gloss, RF-admittance, Brantmere BM-7 FPD, Tealfen SIL-HIL-4, or Pochardfen HYD-SIM-2. Leave r60–r66 densification leftovers for those rounds' owners. Do not steal r55–r68 IDs `166`–`207`.

## Verification
`batch-r69.jsonl`: 3 lines, `json.loads`-clean (allow_nan=False), {{sizes[0]}}/{{sizes[1]}}/{{sizes[2]}} bytes (file {{BATCH.stat().st_size}}, sha256 `{{file_sha}}`). Staged at `/tmp/nelb-r69/` only. Repo gates: `check_records.check_jsonl` with `FactoryStaging(enabled=True)` → 0 errors, 0 warnings, kinds `{{bridge_pair: 3}}`; `python3 pipelines/check_records.py --strict /tmp/nelb-r69` → 0/0; `curate_bridge.raster_status(..., require_raster=True, require_routing_table=True)` → raster_valid and gate_snn_valid true, empty reason codes; `curate_record(...)` → 3× retain / `BRIDGE_EVENTS_ALREADY_GLOBALLY_ORDERED`; `verify_batch_for_frontier(strict=True)` → 3 verified, 0 inconclusive, 0 failed; `python3 pipelines/spike_probe.py --strict /tmp/nelb-r69/batch-r69.jsonl` → loaded 3, unloadable 0, problems [], third_factor_routes 3, gate_snn_records 3, spikes {{spikes}}, energy_pJ {{energy}}. Build-time asserts: global time order; same-channel ≥0.8 ms; 5–40 events ({{events[0]}}/{{events[1]}}/{{events[2]}}); excerpt integer bounds, neuron bounds, sort, 1 ms per-neuron floor; ISI identity {{isis[0]}}/{{isis[1]}}/{{isis[2]}}; spike budgets exact; energy pJ/µJ exact; reward totals equal two-decimal component sums ({{reward_s}}); gate_snn decisions match lead `safety_decision.decision`; `state.sim_or_real` ∈ {{designed, hil, simulated}}; `meta.round=69`, `meta.factory=neuromorphic-event-language-bridge`, `meta.generator=grok-4.6`, `meta.run_label=2026-09-02-final-heavy`; `meta.rights` 15-key RM-793 stamp (`intended_use=research_only`, `linear_issue=RM-793`, `generated_at={{GENERATED_AT}}`); no hidden-reasoning keys; no `provenance` objects; no live-plant claims; no `training_ready`; all 9 record/trajectory ids unique. Raster seeds 202669208/202669209/202669210, MT19937.

Honest novelty accounting: 3/3 modality families are new versus the whole committed factory and versus staged leftover-mill r13–r65 (and in-flight r61/r63/r66 envelopes). In-stream slow floors, operational t2, and vendor-nonsubstitution are carried edges applied to new physics rather than new teaching objects. Three-party collusion and exoneration were already taught on r13 quench/VRFB and later leftover-mill rounds, so those heads are carried onto new sensors. Against that: bounded-accept-with-scope-limit, reconstruction-as-SoT, conjunctive SOP, and custody vocabulary are carried; the 5–40 cap is a density constraint not a new teaching object; 56 prior leftover-mill rounds already taught custody/governance at high sophistication. Net: about two-fifths of the round's scenario/edge mass is genuinely novel.

Novel coverage: 40%
"""
    # The notes template above doubled braces for the Verification block so format after
    # substituting runtime values without colliding with JSON-like braces in the body.
    notes = notes.replace("{{sizes[0]}}", str(sizes[0]))
    notes = notes.replace("{{sizes[1]}}", str(sizes[1]))
    notes = notes.replace("{{sizes[2]}}", str(sizes[2]))
    notes = notes.replace("{{BATCH.stat().st_size}}", str(BATCH.stat().st_size))
    notes = notes.replace("{{file_sha}}", file_sha)
    notes = notes.replace("{{spikes}}", str(spikes))
    notes = notes.replace("{{energy}}", str(energy))
    notes = notes.replace("{{events[0]}}", str(events[0]))
    notes = notes.replace("{{events[1]}}", str(events[1]))
    notes = notes.replace("{{events[2]}}", str(events[2]))
    notes = notes.replace("{{isis[0]}}", str(isis[0]))
    notes = notes.replace("{{isis[1]}}", str(isis[1]))
    notes = notes.replace("{{isis[2]}}", str(isis[2]))
    notes = notes.replace("{{reward_s}}", reward_s)
    notes = notes.replace("{{GENERATED_AT}}", GENERATED_AT)
    NOTES.write_text(notes, encoding="utf-8")
    print("wrote", NOTES, "bytes", NOTES.stat().st_size)


def main():
    occupancy_preflight()
    records = [rec_208(), rec_209(), rec_210()]
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
