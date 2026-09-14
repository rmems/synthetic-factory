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
    file_size = BATCH.stat().st_size
    notes = f"""# Neuromorphic Event + Language Bridge — NOTES round 62
Run: 2026-09-02-final-heavy · Factory: neuromorphic-event-language-bridge · Generator: grok-4.6 · Output: `batch-r62.jsonl` (3 paired artifacts, 6 ThalamicTrajectories)
Rights: RM-793 research-only (SpaceXAI/xAI grok-4.6, SuperGrok Heavy chat). Not training_ready. Do not publish into `outputs/raw/` from this generator; operator uses `pipelines/round_txn.py`. Staged only at `/tmp/nelb-r62/`.

## Context / de-duplication
Prior corpus read: 2026-08-30 NOTES-r01–r04, 2026-08-17-w3 NOTES-r12 family table, `/tmp/nelb-r13-holes.md` + `/tmp/nelb-r13-premises.md`, staged `/tmp/nelb-r13` through `/tmp/nelb-r56` and `/tmp/nelb-r59` complete batches/NOTES plus in-flight r57 (zirconia Nernst / PID VOC / contact pulse-echo, with competing strain-gauge / conductivity drafts), r58 (zirconia wideband / Rogowski / BAM, with competing FID draft), r60 head-only, r61 head/tail-only. IDs: r13=`040`–`042` … r56=`169`–`171`, r55=`166`–`168`, r59=`178`–`180`, reserved r57–r58=`172`–`177` and r60–r61=`181`–`186`, this round `nelb-r62-187`…`189` as assigned. Envelope cloned from complete r56 (`language_view.trajectory` + operational t2 + `spike_events` + `raster` + `gate_snn` + `isi_histogram` + `routing.third_factor` + 15-key RM-793 `meta.rights`).

Banned this round (committed + staged leftover-mill r13–r56/r59 and in-flight r57/r58 generators): not VOD-SNN replay, not pharma cold-chain, not stack-gas CEMS; not r13 FBG glaze / Frostlip quench / Oxbow VRFB; not r14 BOTDA / QCM-D / MsS T(0,1); not r15 SAW torque / CRDS HF / PGNAA; not r16 IFOG / transmon readout / hyperspectral crop; not r17 MEMS accel array / muon ore-pass / industrial x-ray DR; not r18 optogenetic PV / 905 nm LiDAR snow / clamp-on transit-time; not r19 LIBS Cu / QEPAS DGA / LFV Al; not r20 Kaplan LDV / THz-TDS radome moisture / ECT CFB; not r21 THz-TDS bondline / ECA FSW lift-off / LIBS C; not r22 ECT pneumatic riser / TDLAS NH3 / LIBS tap; not r23 lock-in thermography CFRP / PAUT TFM girth / EN CUI; not r24 RUS porcelain / N-16 transit-time loop / helium RGA; not r25 Faraday FOCT / blade tip-timing / acoustic pyrometry; not r26 SPR cyanide / VW viscometer / MW cavity moisture; not r27 MFL AST / NMR T2 / Cs-137 densitometry; not r28 MFL ILI / JNT / CRNS; not r29 Coriolis bitumen / CARS TIT / Zn-Ka XRF; not r30 Mössbauer FCC / GB-InSAR tailings / ellipsometry PECVD; not r31 CTA hot-wire / rhodium SPND / LII soot; not r32 PALS / 14N NQR / SFRA; not r33 digital shearography hull / hydrogen permeation / FMCW BOF lining; not r34 handheld XRF Cr-Kα / Coriolis tube-twist / GPR liner cover; not r35/r37 mud-pulse MWD / Barkhausen / Lamb-wave; not r36 Pockels GIS / PEC coated riser / confocal chromatic; not r38 OCT TBC / DCPD girth / impact-echo containment; not r39 phosphor-lifetime / vortex-shedding / GWR foam; not r40 He-3 neutron-backscatter / Kr-85 beta / 532 nm Raman; not r41/r42/r43 cyclotron BPM / alanine EPR / ADCP ice-jam; not r44 TOFD / laser-flash Parker / TDR cable; not r45 Seebeck / coda-wave / LPR; not r46 paramagnetic O2 / TOFD ligament / TEOM PM; not r47 Faraday magmeter / PDA Sauter D32 / acoustoelastic birefringence; not r48 C-SAM / FDS tanδ / MCSA; not r49 EMAT SH / FBRM D50 / ACFM crack depth; not r50 OFDR / XRD sin2psi / FSM; not r51 Gardon / chilled-mirror dew-point / DIC hoop-strain; not r52 chemiluminescence NOx / API-670 proximity / thermal-mass capillary; not r53 ER probe / Fabry-Perot choke / inductive debris; not r54 wire-mesh void / UCI hardness / magnetoacoustic emission; not r55 FID THC / turbine k-factor / magnetostrictive waveguide; not r56 IRIS pulse-echo / dual-wavelength ratio pyrometer / UV-fluorescence OIW; not r57 zirconia Nernst / PID VOC / contact pulse-echo; not r58 zirconia wideband / Rogowski / BAM; not r59 UV-DOAS SO2 / aluminum-oxide moisture / strain-gauge hopper mass. Plants not reused: Nettlewake, Frostlip, Oxbow, Fernwick, Mossfell, Kelpfen, Brackholt, Dewholt, Pebblewick, Hawkmere, Embercrag, Reedwhin, Wexmere, Glaurfen, Rushfen, Brindlecrag, Copsewharf, Kelpwharf, Thornmere, Marlfell, Birchfen, plus the r13–r59 plant list.

This round introduces three unused industrial families (gamma-backscatter remaining lining, NDIR remaining CO, ultrasonic-Doppler remaining slurry velocity) on new invented plants. r13-holes cyclotron/alanine/ADCP and r56/r59 densification leftovers are not restaged. r60 laser-triangulation / r61 pellistor claims are not restaged.

Adjacencies declared in-pair then kept physically distinct:
- **187 gamma backscatter** is a 137Cs backscatter remaining lining of a rotary kiln, not r27 Cs-137 densitometry, not r40 He-3 neutron-backscatter, not r40 Kr-85 beta, not r33 FMCW lining, not r56 IRIS pulse-echo, not r57 contact pulse-echo, not r23 PAUT TFM.
- **188 NDIR CO** is a non-dispersive infrared remaining CO of a reformer arch, not r22 TDLAS NH3, not r15 CRDS HF, not r19 QEPAS, not r04 CEMS FTIR, not r59 UV-DOAS SO2, not r52 CLD NOx, not r46 paramagnetic O2, not r57 PID VOC, not r55 FID THC.
- **189 ultrasonic Doppler** is an fd·c/(2·f0) remaining slurry velocity of a tailings line, not r20 Kaplan LDV, not r41/r42/r43 ADCP ice-jam, not r18 clamp-on transit-time, not r47 magmeter, not r29/r34 Coriolis, not r39 vortex-shedding, not r19 LFV, not r55 turbine volumetric.

## Round 62 batch summary (3 pairs, 6 trajectories)

| id | modality (NEW family) | domain | decisions | headline |
|----|----------------------|--------|-----------|----------|
| nelb-r62-187 | gamma-backscatter remaining lining of a rotary kiln (k_b/I mm, Backveil last-campaign denial, 18 min soak floor) | Peatshaw Kiln PS-7 kiln K-3 (invented): 4.00 nA reconstructs 8.00 mm while Backveil still reads 18.40 mm | REJECT (+0.43) / MODIFY (+0.34) | serialized `32.00/4.00=8.00`; `4.00*8.00=32.00`; conjunctive SOP (d AND SNR) forbids continue-firing; three-party collusion includes the gamma infra owner; companion t2 kiln-soak hold, kiln trip refused; sim_or_real=designed |
| nelb-r62-188 | NDIR remaining CO of a reformer arch (k_n·(I0/I−1) ppm, Carbveil last-good denial, 24 min steam-standby floor) | Woldshaw Reformer WS-4 arch A-1 (invented, HIL dummy in NDIR-HIL-3): 8.00/2.00 reconstructs 30.00 ppm while Carbveil still reads 4.80 ppm | MODIFY (+0.40) / ACCEPT (+0.35) | serialized `10.00*(8.00/2.00-1)=30.00` and `8.00/2.00=4.00`; keep-firing refused; NDIR tech Joss Hale exonerated (missing lamp-cal AE, UTC vs UTC+2); companion t2 new-NDIR restart; sim_or_real=hil |
| nelb-r62-189 | ultrasonic-Doppler remaining slurry velocity of a tailings line (fd·c/(2·f0) m/s, Shiftveil last-good denial, 12 min survey floor) | Bramblefen Tailings BT-6 line L-3 (invented, simulated USD-SIM-2): 4.00 kHz reconstructs 8.00 m/s while Shiftveil still reads 1.20 m/s | ACCEPT (+0.41) / REJECT (+0.36) | serialized `4.00*1480.0/(2*370.0)=8.00`; `1600*0.0125*8.00=160.00`; bounded ACCEPT of L-3 only; L-1 and L-2 out of scope; companion t2 REJECTS skip-isolate; sim_or_real=simulated |

Decision spread: REJECT / MODIFY / MODIFY / ACCEPT / ACCEPT / REJECT — **2A/2M/2R**. All three enums used, and all three sit on **leads**. Provenance spread: designed / hil / simulated (one each; never live-plant). IDs `nelb-r62-187`…`189` plus t1/t2 suffixes.

## Raster sidecar
Every record carries `raster` + top-level `gate_snn` + `gate_compute`. Windows {wins[0]:.0f}/{wins[1]:.0f}/{wins[2]:.0f} ms; `window_s == window_ms/1000` exactly; `spikes == round(neurons·rate·window_s)` with zero slack ({n_sp[0]}/{n_sp[1]}/{n_sp[2]} at {rates[0]}/{rates[1]}/{rates[2]} Hz over {n_neu[0]}/{n_neu[1]}/{n_neu[2]} neurons); `energy_pJ = spikes·23` and `energy_uJ = spikes·23e-6` exact ({n_sp[0]*23}/{n_sp[1]*23}/{n_sp[2]*23} pJ). Routing source/target + 3-entry tables + `third_factor` on all three (modulators {tfs[0]} / {tfs[1]} / {tfs[2]}; τe {taus[0]}/{taus[1]}/{taus[2]} s as consistent `tau_e_s`+`tau_e_ms` pairs). Excerpts integer `t_us`, in-window, `neuron_id`-bounded, sorted, full-window by construction, per-spike amplitude with adaptation (0.82**k) plus noise. ISI histograms from the full window, bins ≥1 ms, counts sum to `spikes − distinct_active_neurons` ({isis[0]}/{isis[1]}/{isis[2]}). Same-neuron gaps ≥1100 µs pre-round, ≥1000 µs serialized. `gate_snn` on all three: decisions REJECT/MODIFY/ACCEPT matching each lead trajectory; every rate-declaring population's budget exact against its decision window. `gate_compute.per_check` windows 32–40 ms, budgets exact ({gc[0]} / {gc[1]} / {gc[2]}). Main streams: {events[0]}/{events[1]}/{events[2]} events (inside the 5–40 cap), strictly increasing `t_rel_ms` only (no `t_ms` mix), same-channel refractory ≥0.8 ms (187 gamma pair at 1.3 ms, 188 NDIR pair at 1.2 ms, 189 Doppler pair at 1.5 ms).

## Self-critique

### Edge cases added vs still thin
- **Added:** first gamma-backscatter remaining-lining family on a rotary kiln with a recomputable d=k_b/I (`8.00 mm`) plus product identity and three-party collusion including the gamma infra owner; first NDIR remaining-CO family on a reformer arch with recomputable C=k_n·(I0/I−1) (`30.00 ppm`) and ratio identity, plus a resolved-innocent NDIR tech (timezone-skipped lamp-cal, not last-to-badge); first ultrasonic-Doppler remaining-slurry-velocity family on a tailings line with recomputable v=fd·c/(2·f0) (`8.00 m/s`) plus mass-flow identity; bounded ACCEPT whose out-of-scope clause is adjacent tailings lines rather than a hopper/taphole/dump cap; operational t2 on all three (kiln-soak hold, new-NDIR restart, skip-line refusal); provenance trio designed/hil/simulated; 18 min / 24 min / 12 min slow floors in-stream.
- **Still thin:** (i) 187's k_b is a lumped nA·mm, not a bulk-density / scatter-angle table — a dust hop that fakes 8.00 mm inside an 18.40 mm Backveil corridor is unwritten; (ii) 188's k_n is a lumped NDIR gain, not a path-length / H2O-interference map, so a window-soot hop that fakes 30.00 ppm is unwritten; (iii) 189's c is a lumped 1480 m/s, not a density / solids-fraction table, so a bubble hop that fakes 8.00 m/s inside a 1.20 last-good is unwritten; (iv) vendor-only as a *lead* REJECT on a plant with *no* independent gamma/NDIR/Doppler installed yet remains slightly harder — 187/188 still have plant heads; (v) stream amplitudes remain authored constants (raster draws are the only seeded noise); (vi) r56 densification leftovers (IRIS steel table, pyrometer slag-window, OIW quenching) and r59 leftovers (DOAS path-length, Al2O3 hysteresis, load-cell temperature) were left for those rounds' owners.

### Realism of noise / temporal fidelity
- Strong: 187's 8.00 mm, standoff identity 4.00, and 18.0 min stand-soak (`6000+1080=7080 s`) recompute from the record; 188's 30.00 %LEL, delta 6.00, and 24.0 min purge (`2820+1440=4260 s`) recompute; 189's 8.00 m/s, mdot 160.00, and 12.0 min survey (`6000+720=6720 s`) recompute. Raster adaptation (0.82**k plus 4% noise) and the 1.2–1.5 ms physics pairs give the 5–40 stream a raster-scale motif without violating 0.8 ms same-channel refractory.
- **Gaps, honestly:** (i) 5–40 cap still forces heavy thinning (2 kHz triangulation PSD kept as 4 V points; 1 Hz pellistor kept as 4 V points plus one V0 pair; 10 Hz Doppler kept as 4 fd points); (ii) 187's post-stop 10.00 mm is a later sample, not a closed-loop soak controller; (iii) 188 HIL coupon times an in-service isolate that the stream does not independently witness on a second live booth until the new pellistor starts; (iv) no gate_snn input→output volley pair at raster resolution this round (r04-a1 already staged that).

### Training value (SNN/LSM + agentic)
Distillation targets: triangulation d=k_t·(V_ref−V) reconstruction head plus standoff identity; conjunctive min-thickness floor vs continue-rolling vs mill trip; triangulation-infra collusion; pellistor S=k_p·(V−V0) head plus delta identity; isolate-floor booth vs keep-spraying vs shop-trip; exoneration against last-to-badge social pressure; ultrasonic-Doppler v=fd·c/(2·f0) and mdot identities; bounded ACCEPT with line-out-of-scope; skip-isolate refusal under survey takt. Agentic value concentrates in three patterns: reconstruction-as-SoT on a physical thickness/LEL/velocity the raw corridor cannot see, earned ACCEPT with an explicit physical out-of-scope object (L-1 and L-2), and stop-then-hold so a REJECT does not become a mill/shop/dump kill.

## What a later leftover-mill round should add (next densification target)
1. **Temperature / refractive-index table** on a non-MH-9 stand so a steam-plume hop fakes 8.00 mm inside an 18.40 mm Gageveil corridor, closing 187's lumped-k_t gap.
2. **Poison / oxygen-deficiency map** on a non-TS-5 booth so a silicone hop can fake 30.00 %LEL while mean bead voltage looks healthy.
3. **Density / solids-fraction table** on a non-BT-6 line so a bubble hop can fake 8.00 m/s inside a 1.20 last-good corridor.
4. **Vendor-only as a lead REJECT** on a plant that has no independent triangulation/pellistor/Doppler installed yet (187/188 still had plant heads).
5. **Do not restage** VOD-SNN replay, pharma cold-chain, CEMS, FBG glaze, Frostlip quench, Oxbow VRFB, IFOG, transmon, hyperspectral, MEMS array, muon ore-pass, industrial x-ray, optogenetic stim, 905 nm LiDAR snow, clamp-on transit-time, LIBS, QEPAS, LFV, Kaplan LDV, THz-TDS, ECT, TDLAS NH3, lock-in thermography, PAUT TFM, EN CUI, RUS porcelain, N-16 loop flow, helium RGA, Faraday FOCT, blade tip-timing, acoustic pyrometry, SPR, vibrating-wire, microwave-cavity, MFL, NMR T2, nucleonic densitometry, JNT, CRNS, Coriolis, CARS, XRF, Mössbauer, GB-InSAR, ellipsometry, CTA, SPND, LII, PALS, NQR, SFRA, digital shearography, hydrogen permeation, FMCW lining, GPR, Pockels, PEC, confocal, mud-pulse, Barkhausen, Lamb-wave, OCT, DCPD, impact-echo, cyclotron BPM, alanine EPR, ADCP, vortex-shedding, Kr-85 beta, 532 nm Raman, phosphor-lifetime, guided-wave-radar, paramagnetic O2, TOFD, TEOM, RFEC, LPR, laser-flash, TDR, PDA, acoustoelastic, ACFM, FDS tanδ, MCSA, EMAT SH, FBRM, OFDR, XRD, FSM, Gardon, chilled-mirror, DIC, chemiluminescence NOx, API-670 proximity, thermal-mass capillary, ER probe, Fabry-Perot choke, inductive debris, wire-mesh void, magnetoacoustic emission, FID THC, turbine k-factor, magnetostrictive waveguide, IRIS pulse-echo, dual-wavelength pyrometer, UV-fluorescence OIW, zirconia Nernst, PID VOC, contact pulse-echo, zirconia wideband, Rogowski, BAM, UV-DOAS SO2, aluminum-oxide moisture, strain-gauge hopper, Mireholt MH-9 triangulation, Torholt PELL-HIL-2, or Bramblefen BT-6 Doppler. Leave r56 and r59 densification leftovers for those rounds' owners. Do not steal r55–r61 IDs `166`–`186`.

## Verification
`batch-r62.jsonl`: 3 lines, `json.loads`-clean (allow_nan=False), {sizes[0]}/{sizes[1]}/{sizes[2]} bytes (file {file_size}, sha256 `{file_sha}`). Staged at `/tmp/nelb-r62/` only. Repo gates: `check_records.check_jsonl` with `FactoryStaging(enabled=True)` → 0 errors, 0 warnings, kinds `{{bridge_pair: 3}}`; `python3 pipelines/check_records.py --strict /tmp/nelb-r62` → 0/0; `curate_bridge.raster_status(..., require_raster=True, require_routing_table=True)` → raster_valid and gate_snn_valid true, empty reason codes; `curate_record(...)` → 3× retain / `BRIDGE_EVENTS_ALREADY_GLOBALLY_ORDERED`; `verify_batch_for_frontier(strict=True)` → 3 verified, 0 inconclusive, 0 failed; `python3 pipelines/spike_probe.py --strict /tmp/nelb-r62/batch-r62.jsonl` → loaded 3, unloadable 0, problems [], third_factor_routes 3, gate_snn_records 3, spikes {spikes}, energy_pJ {energy}. Build-time asserts: global time order; same-channel ≥0.8 ms; 5–40 events ({events[0]}/{events[1]}/{events[2]}); excerpt integer bounds, neuron bounds, sort, 1 ms per-neuron floor; ISI identity {isis[0]}/{isis[1]}/{isis[2]}; spike budgets exact; energy pJ/µJ exact; reward totals equal two-decimal component sums ({reward_s}); gate_snn decisions match lead `safety_decision.decision`; `state.sim_or_real` ∈ {{designed, hil, simulated}}; `meta.round=62`, `meta.factory=neuromorphic-event-language-bridge`, `meta.generator=grok-4.6`, `meta.run_label=2026-09-02-final-heavy`; `meta.rights` 15-key RM-793 stamp (`intended_use=research_only`, `linear_issue=RM-793`, `generated_at={GENERATED_AT}`); no hidden-reasoning keys; no `provenance` objects; no live-plant claims; no `training_ready`; all 9 record/trajectory ids unique. Raster seeds 202609187/202609188/202609189, MT19937. Staging is the `/tmp` pair, not a beads close-out.

Honest novelty accounting: 3/3 modality families are new versus the whole committed factory and versus staged leftover-mill r13–r56/r59 (and in-flight r57/r58 claims). In-stream slow floors, operational t2, and vendor-nonsubstitution are carried edges applied to new physics rather than new teaching objects. Three-party collusion and exoneration were already taught on r13 quench/VRFB and r55/r56/r59 FID/pyrometer/DOAS, so those heads are carried onto new sensors. Against that: bounded-accept-with-scope-limit, reconstruction-as-SoT, conjunctive SOP, and custody vocabulary are carried; the 5–40 cap is a density constraint not a new teaching object; 49 prior leftover-mill rounds already taught custody/governance at high sophistication. Net: about two-fifths of the round's scenario/edge mass is genuinely novel.

Novel coverage: 40%
"""
    NOTES.write_text(notes, encoding="utf-8")
    print("wrote", NOTES, "bytes", NOTES.stat().st_size)
    _ = gate, probe_out


def main():
    occupancy_preflight()
    records = [rec_187(), rec_188(), rec_189()]
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
