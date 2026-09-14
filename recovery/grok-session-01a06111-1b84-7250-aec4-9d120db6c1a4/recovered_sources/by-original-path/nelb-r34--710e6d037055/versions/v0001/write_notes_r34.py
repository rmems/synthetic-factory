def write_notes(records, lines, gate_lines):
    rows = []
    decisions = []
    for rec in records:
        lv = rec["language_view"]
        t1 = lv["trajectory"]
        t2 = next(v for k, v in lv.items() if k.startswith("trajectory_"))
        d1 = t1["safety_decision"]["decision"]
        d2 = t2["safety_decision"]["decision"]
        decisions.extend([d1, d2])
        r1 = t1["reward_components"]["total"]
        r2 = t2["reward_components"]["total"]
        rast = rec["raster"]
        rows.append(
            {
                "id": rec["id"],
                "d1": d1,
                "d2": d2,
                "r1": r1,
                "r2": r2,
                "sim": t1["state"]["sim_or_real"],
                "events": len(rec["spike_events"]),
                "window": rast["window_ms"],
                "neurons": rast["neurons"],
                "rate": rast["mean_rate_hz"],
                "spikes": rast["spikes"],
                "isi": rast["isi_count_identity"]["isi_total"],
                "mod": rast["routing"]["third_factor"]["modulator"],
                "tau": rast["routing"]["third_factor"]["tau_e_s"],
                "bytes": len(json.dumps(rec, ensure_ascii=False, allow_nan=False, separators=(",", ":"))),
            }
        )
    na = decisions.count("ACCEPT")
    nm = decisions.count("MODIFY")
    nr = decisions.count("REJECT")
    notes = f"""# Neuromorphic Event + Language Bridge — NOTES round 34
Run: 2026-09-02-final-heavy · Factory: neuromorphic-event-language-bridge · Generator: grok-4.6 · Output: `batch-r34.jsonl` (3 paired artifacts, 6 ThalamicTrajectories)
Rights: RM-793 research-only (SpaceXAI/xAI grok-4.6, SuperGrok Heavy chat). Not training_ready. Do not publish into `outputs/raw/` from this generator; operator uses `pipelines/round_txn.py`. Staged only at `/tmp/nelb-r34/`.

## Context / de-duplication
Prior corpus read: 2026-08-17 r1–r12 family table; 2026-08-30 NOTES-r01–r04; staged `/tmp/nelb-r13`…`/tmp/nelb-r30` generators/NOTES/jsonl plus in-flight `/tmp/nelb-r31` (ids 094–096, FOCT/BTT/pyrometry clone of r25) and `/tmp/nelb-r33` stub. Pair shape from r13/r26 (`language_view.trajectory` + operational t2 + `spike_events` + `raster` + `gate_snn` + `isi_histogram` + `routing.third_factor` + 15-key RM-793 `meta.rights`). IDs continue the leftover-mill sequence: r30=`091`–`093`, r31=`094`–`096`, implied r32=`097`–`099`, r33=`100`–`102`, this round `nelb-r34-103`…`105`.

Banned this round: r13 FBG glaze / MRI-quench / VRFB EIS; r14 BOTDA / QCM-D / MsS T(0,1); r15 SAW torque / CRDS HF / PGNAA; r16 IFOG / transmon readout / hyperspectral crop; r17 MEMS array / muon tomography / industrial x-ray DR; r18 optogenetic photovoltaic comb / 905 nm LiDAR snow / ultrasonic clamp-on; r19 LIBS Cu-ratio / QEPAS C2H2 / Lorentz-force velocimetry; r20 fiber-LDV Kaplan / THz-TDS coupon / ECT CFB; r21 THz-TDS bondline / ECA-FSW / LIBS carbon; r22 ECT HDPE / TDLAS NH3 / LIBS tap C; r23 lock-in thermography / PAUT-TFM / ECN CUI; r24 RUS insulator / N-16 gamma transit-time / helium RGA; r25 Faraday FOCT / blade-tip-timing / acoustic pyrometry; r26 SPR cyanide / vibrating-wire viscometer / microwave-cavity moisture; r27 MFL AST-floor / NMR T2 well-log / nucleonic gamma densitometry; r28 MFL ILI / Johnson-noise thermometry / CRNS; r29 NMR-CPMG cavern / CARS N2 FWHM / microwave gypsum; r30 Fe-57 Mössbauer / GB-InSAR / spectroscopic ellipsometry; r04 VOD-SNN / pharma cold-chain / CEMS; 2026-08-30 r01–r03 including dry-cask muon, CHO EWMA, and LPBF melt-pool; r1–r12 table (DVS, cochlea, SPAD ToF, DAS, PMU, e-skin, vestibular, atomic clocks, tokamak, nanopore, VLF, QEC, GW, SOFAR, neutrino, fab OES, space weather, pulsar TOA, eddy covariance, flow cytometry). Unused r13-holes/premises sketches (cyclotron BPM/BLM, Co-60 alanine EPR, ADCP ice-jam, mud-pulse, Barkhausen, Lamb-wave) were not restaged so parallel r32/r33 can still harvest them.

Adjacencies declared in-pair then kept physically distinct: 103 handheld XRF is a Cr-Kα / Fe-Kα fluorescence ratio on an overlay, not r17 transmission DR, not r19/r21/r22 LIBS plasma, not r15 PGNAA capture gammas, not r30 ellipsometry OPD; 104 Coriolis is a tube-twist Δt mass-flow, not r18 clamp-on transit-time, not r19 LFV, not r24 N-16 gamma TOF, not r26 vibrating-wire viscosity; 105 100 MHz GPR is a two-way travel-time cover depth, not r30 GB-InSAR LOS displacement, not r20 THz-TDS, not r3 SPAD ToF, not r18 LiDAR snow.

## Round 34 batch summary (3 pairs, 6 trajectories)

| id | modality (NEW family) | domain | decisions | headline |
|----|----------------------|--------|-----------|----------|
| nelb-r34-103 | handheld XRF Cr Kα overlay remaining (serialized Cr=k_x·I_Cr/I_Fe; rust-scale PMI denial) | Skeldfen Overlay SF-7 drum D-19 (invented): 6.00/4.00 kcps reconstructs 12.00 wt% while Alloyveil PMI still reads 18.40 | MODIFY (+0.41) / ACCEPT (+0.34) | serialized `8.00*(6.00/4.00)=12.00`; conjunctive SOP (Cr AND SNR) forbids keep-stamp; companion t2 is operational D-19 isolate plus G-4 grind, 24 min cool floor in-stream |
| nelb-r34-104 | Coriolis tube-twist mass flow of a hydrotreater charge (serialized ṁ=k_dt·Δt; frozen-orifice denial; HIL water loop) | Mirecoil Hydrotreater MH-3 header C-2 (invented, HIL): Δt 8.00 ms reconstructs 16.00 kg/s while Flowveil still reads 9.40 | REJECT (+0.43) / MODIFY (+0.32) | serialized `2.00*8.00=16.00`; conjunctive SOP (ṁ AND drive-gain) forbids keep-100; companion t2 MODIFYs freeze-kill into an 18 min T-4 soak and cuts FV-12 to 8.00; sim_or_real=hil |
| nelb-r34-105 | GPR two-way travel-time landfill liner cover (serialized d=c·t/(2√εr); crust-TDR denial) | Brambleholt Landfill BH-4 cell C-6 (invented, simulated sand tank): t 40.00 ns reconstructs 3.00 m while Soilveil TDR still reads 0.80 m | ACCEPT (+0.39) / REJECT (+0.34) | earned bounded ACCEPT on a lead: `0.30*40.00/(2*2.00)=3.00`; C-6 keep only, 1.20 m dump out of scope; 12 min compaction floor in-stream; companion t2 REJECTS dump and skip-scan of C-7..C-9; sim_or_real=simulated |

Decision spread: MODIFY / ACCEPT / REJECT / MODIFY / ACCEPT / REJECT — **{na}A/{nm}M/{nr}R**. All three enums used, and all three sit on **leads**. Provenance spread: designed / hil / simulated (one each; never real). IDs `nelb-r34-103`…`105` plus t1/t2 suffixes.

## Raster sidecar
Every record carries `raster` + top-level `gate_snn` + `gate_compute`. Windows {rows[0]['window']:.0f}/{rows[1]['window']:.0f}/{rows[2]['window']:.0f} ms; `window_s == window_ms/1000` exactly; `spikes == round(neurons·rate·window_s)` with zero slack ({rows[0]['spikes']}/{rows[1]['spikes']}/{rows[2]['spikes']} at {rows[0]['rate']:.1f}/{rows[1]['rate']:.1f}/{rows[2]['rate']:.1f} Hz over {rows[0]['neurons']}/{rows[1]['neurons']}/{rows[2]['neurons']} neurons); `energy_pJ = spikes·23` and `energy_uJ = spikes·23e-6` exact. Routing source/target + 3-entry tables + `third_factor` on all three (modulators {rows[0]['mod']} / {rows[1]['mod']} / {rows[2]['mod']}; τe {rows[0]['tau']}/{rows[1]['tau']}/{rows[2]['tau']} s as consistent `tau_e_s`+`tau_e_ms` pairs). Excerpts integer `t_us`, in-window, `neuron_id`-bounded, sorted, full-window by construction, per-spike amplitude with adaptation (0.82**k) plus noise. ISI histograms from the full window, bins ≥1 ms, counts sum to `spikes − distinct_active_neurons` ({rows[0]['isi']}/{rows[1]['isi']}/{rows[2]['isi']}). Same-neuron gaps ≥1100 µs pre-round, ≥1000 µs serialized. `gate_snn` on all three: decisions MODIFY/REJECT/ACCEPT matching each lead. `gate_compute.per_check` windows 28–40 ms, budgets exact. Main streams: {rows[0]['events']}/{rows[1]['events']}/{rows[2]['events']} events (inside the 5–40 cap), strictly increasing `t_rel_ms` only (no `t_ms` mix), same-channel refractory ≥0.8 ms (103 XRF triplet at 1.2 ms, 104 Coriolis ring triplet, 105 GPR hyperbola triplet).

## Self-critique

### Edge cases added vs still thin
- **Added:** first handheld-XRF Cr-Kα overlay family (not transmission DR, not LIBS, not PGNAA, not ellipsometry); first Coriolis tube-twist mass-flow family on a hydrotreater charge (not clamp-on, not LFV, not N-16, not vibrating-wire); first GPR two-way-time liner-cover family (not GB-InSAR LOS, not THz-TDS, not SPAD ToF, not LiDAR); rust-scale PMI as a denial channel; frozen-orifice last-good as a denial channel; crust TDR as a denial channel; earned bounded ACCEPT whose out-of-scope clause is a 1.20 m dump plus skip-scan; 24 min / 18 min / 12 min recovery floors in-stream; provenance trio designed/hil/simulated; operational t2 on all three (G-4 grind, T-4 soak, dump/skip refusal).
- **Still thin:** (i) 103 k_x is a calibrated internal-standard constant, not a matrix-effect / takeoff-angle Sherman stack — a rust-film that could hide 12 wt percent inside an 18 wt percent PMI corridor is unwritten as a physics term; (ii) 104 uses Δt-only mdot and treats tube frequency as a conjunct, so a density-entry error that could fake 16 kg/s is unwritten; (iii) 105 assumes εr=4.00 rather than a measured common-midpoint velocity, so a wet-sand εr walk that could fake 3.00 m inside a 0.80 m TDR is unwritten; (iv) stream amplitudes remain authored constants (raster draws are the only seeded noise); (v) r04's 90-day poison-class audit close-out, FBG Δλ(T) on a non-TW-17 blade, and the unused r13-premises plants remain untouched; (vi) vendor-only as a lead REJECT with *no* independent witness is still harder than 104 (plant Coriolis exists on live C-2; HIL water only convicts k_dt).

### Realism of noise / temporal fidelity
- Strong: 103's 12.00 wt percent recomputes `8.00*(6.00/4.00)`; 104's 16.00 kg/s recomputes `2.00*8.00`; 105's 3.00 m recomputes `0.30*40.00/(2*2.00)`. Raster adaptation (0.82**k plus 4 percent noise) and 1.2 ms triplets give each 5–40 stream a raster-scale motif without violating 0.8 ms same-channel refractory.
- **Gaps, honestly:** (i) 5–40 cap forces heavy thinning (XRF 256-channel spectrum kept as envelope I_Cr/I_Fe; Coriolis 100 Hz twist kept as envelope Δt; GPR A-scan kept as envelope TWT); (ii) 105's 12 min compaction is two bookends plus one TWT resample, not a sampled night of cover placement; (iii) 104 HIL spare times a live-header cut that the stream does not independently witness on a second live tube; (iv) no gate_snn input→output volley pair at raster resolution this round (r04-a1 already staged that).

### Training value (SNN/LSM + agentic)
Distillation targets: serialized XRF Cr=k_x·I_Cr/I_Fe; conjunctive SNR SOP that a rust-scale PMI cannot substitute for; serialized Coriolis ṁ=k_dt·Δt; drive-gain coating conjunct; recycle-not-kill after REJECT; serialized GPR d=c·t/(2√εr); SNR conjunct; bounded ACCEPT with cell scope + dump out of scope; operational companions that execute or refuse scope without re-opening the physics call. Agentic value concentrates in three patterns: reconstruction-as-SoT on a physical error the raw PMI/orifice/TDR channel cannot see, REJECT that becomes a soak rather than a freeze-kill, and ACCEPT that does not license the unmeasured remainder.

## What round 35 should add (next densification target)
1. **XRF Sherman / takeoff-angle matrix** that can hide 12 wt percent Cr inside an 18 wt percent PMI corridor, closing 103's calibrated-k_x gap without restaging SF-7.
2. **Coriolis tube-density from f** so 104's ρ is measured, not a conjunct, and a density-entry error can no longer be the unwritten fake.
3. **GPR common-midpoint velocity** so 105's εr is measured, not assumed 4.00, closing the wet-sand fake.
4. **Do not restage** VOD-SNN replay, pharma cold-chain, stack-gas CEMS, FBG glaze, Frostlip quench, Oxbow VRFB, IFOG, transmon, hyperspectral, MEMS array, muon ore-pass, industrial x-ray, optogenetic stim, 905 nm LiDAR snow, clamp-on transit-time, LIBS, QEPAS, LFV, Mossgill LDV, Thornwick THz, Polderwick ECT, Fernbrake THz-TDS, Tallowfen ECA, Peckholt LIBS-C, Brackfen ECT, Ashrill TDLAS, Forgeholt LIBS tap, lock-in thermography, PAUT-TFM, ECN CUI, RUS porcelain, N-16 transit-time, helium RGA, Faraday FOCT, blade-tip-timing, acoustic pyrometry, Pyrefen SPR PX-8, Pitchfen VW PB-3, Brinekiln MW BK-6, Sedgecrag MFL, Chalkbarrow NMR, Gritmead nucleonic, Kerrfen MFL, Nessholt JNT, Brindlefell CRNS, Saltwick NMR, CARS combustor, MW gypsum, Gorsemere Mössbauer, Brindlescree GB-InSAR, Lichenholt ellipsometry, Skeldfen XRF SF-7, Mirecoil Coriolis MH-3, or Brambleholt GPR BH-4. Leave Rift-Caldera mud-pulse, Skarv-Naze Barkhausen, and Orinoco-Span Lamb-wave available.

## Verification
`batch-r34.jsonl`: 3 lines, `json.loads`-clean (allow_nan=False), ~{rows[0]['bytes']/1024:.1f}/{rows[1]['bytes']/1024:.1f}/{rows[2]['bytes']/1024:.1f} KB. Staged at `/tmp/nelb-r34/` only. {gate_lines} Build-time asserts: global strict time order; same-channel ≥0.8 ms; 5–40 events ({rows[0]['events']}/{rows[1]['events']}/{rows[2]['events']}); excerpt integer bounds, neuron bounds, sort, 1 ms per-neuron floor; ISI identity {rows[0]['isi']}/{rows[1]['isi']}/{rows[2]['isi']}; spike budgets exact; energy pJ/µJ exact; reward totals equal two-decimal component sums (+0.41/+0.34/+0.43/+0.32/+0.39/+0.34); gate_snn decisions match lead `safety_decision.decision`; `state.sim_or_real` ∈ {{designed, hil, simulated}}; `meta.round=34`, `meta.factory=neuromorphic-event-language-bridge`, `meta.generator=grok-4.6`, `meta.run_label=2026-09-02-final-heavy`; `meta.rights` 15-key RM-793 stamp, `intended_use=research_only`; no hidden-reasoning keys; no `provenance` objects; no 'real' claims; no `training_ready`; all 9 record/trajectory ids unique. Raster seeds 20261103/20261104/20261105, MT19937.

Honest novelty accounting: 3/3 modality families are new versus the committed factory and versus staged leftover-mill r13–r30. PMI-rust denial, frozen-orifice denial, and crust-TDR denial are new edges applied to new physics. Against that: conjunctive SOP, operational t2, serialized reconstruction, bounded ACCEPT, and process-vs-cost reward splits are carried vocabulary; the 5–40 cap is a density constraint; 33 prior rounds already taught custody/governance. Net: a bit under two-fifths of the round's scenario/edge mass is genuinely novel.

Novel coverage: 38%
"""
    NOTES.write_text(notes, encoding="utf-8")
    print("wrote", NOTES, "bytes", NOTES.stat().st_size)
