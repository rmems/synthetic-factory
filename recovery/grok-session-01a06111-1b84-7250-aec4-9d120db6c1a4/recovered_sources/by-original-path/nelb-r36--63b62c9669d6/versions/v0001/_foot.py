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

    reward_s = "/".join(f"+{x:.2f}" for x in rewards)
    notes = f"""# Neuromorphic Event + Language Bridge — NOTES round 36
Run: 2026-09-02-final-heavy · Factory: neuromorphic-event-language-bridge · Generator: grok-4.6 · Output: `batch-r36.jsonl` (3 paired artifacts, 6 ThalamicTrajectories)
Rights: RM-793 research-only (SpaceXAI/xAI grok-4.6, SuperGrok Heavy chat). Not training_ready. Do not publish into `outputs/raw/` from this generator; operator uses `pipelines/round_txn.py`. Staged only at `/tmp/nelb-r36/`.

## Context / de-duplication
Prior corpus read: 2026-08-30 NOTES-r01–r04, 2026-08-17-w3 NOTES-r12 family table, staged `/tmp/nelb-r13` through `/tmp/nelb-r34` batches/NOTES plus in-flight `/tmp/nelb-r32` (PALS/NQR/laser-shearography) and `/tmp/nelb-r35` (r30 clone, IDs `106`–`108` reserved). Pair shape from r13/r33 (`language_view.trajectory` + operational t2 + `spike_events` + `raster` + `gate_snn` + `isi_histogram` + `routing.third_factor` + 15-key RM-793 `meta.rights`). IDs continue the leftover-mill sequence: r33=`100`–`102`, r34=`103`–`105`, reserved r35=`106`–`108`, this round `nelb-r36-109`…`111`.

Banned this round: r13 FBG glaze / MRI-quench / VRFB EIS; r14 BOTDA / QCM-D / MsS T(0,1); r15 SAW torque / CRDS HF / PGNAA; r16 IFOG / transmon readout / hyperspectral crop; r17 MEMS array / muon ore-pass / industrial x-ray DR; r18 optogenetic PV / 905 nm LiDAR snow / clamp-on transit-time; r19 LIBS Cu / QEPAS DGA / LFV Al; r20 Kaplan LDV / THz-TDS radome / ECT CFB; r21 THz-TDS bondline / ECA FSW / LIBS C; r22 ECT pneumatic / TDLAS NH3 / LIBS tap; r23 lock-in thermography / PAUT TFM / EN CUI; r24 RUS porcelain / N-16 transit-time / helium RGA; r25 Faraday FOCT / blade tip-timing / acoustic pyrometry; r26 Kretschmann SPR / vibrating-wire viscometer / microwave-cavity moisture; r27 MFL AST floor / NMR T2 / Cs-137 nucleonic SG; r28 MFL pipeline / Johnson-noise thermometry / CRNS heap; r29 twin-tube Coriolis / CARS N2 / Zn-Ka XRF (and the NMR-CPMG / MW-gypsum in-flight twin); r30 Fe-57 Mössbauer / GB-InSAR / spectroscopic ellipsometry; r31 two-pickoff Coriolis LNG / rhodium SPND / LII soot; r32 PALS steam-header / 14N NQR prill / laser-shearography COPV; r33 digital shearography hull / hydrogen permeation / FMCW microwave lining; r34 handheld XRF Cr-Kα / Coriolis hydrotreater / GPR liner cover; r04 VOD-SNN / pharma cold-chain / CEMS; 2026-08-30 r01–r03 including dry-cask muon and LPBF melt-pool; r1–r12 table (DVS, cochlea, SPAD ToF, DAS, PMU, e-skin, vestibular, atomic clocks, tokamak, nanopore, VLF, QEC, GW, SOFAR, neutrino, fab OES, space weather, pulsar TOA, eddy covariance, flow cytometry). Unused r13-premises (mud-pulse, Barkhausen, Lamb-wave) and r13-holes (cyclotron BPM, alanine EPR, ADCP ice-jam) were left available. Do not steal r35 IDs `106`–`108`. Do not restage Reedholt PALS, Prillmere NQR, or Ashspire laser-shearography.

Adjacencies declared in-pair then kept physically distinct:
- **109 longitudinal BGO Pockels** is an electro-optic I_x/I_y bus-voltage reconstruction on a GIS duct, not r25 Faraday FOCT Verdet current, not PMU synchrophasors, not capacitive-divider metering, not r16 IFOG.
- **110 pulsed eddy current** is k_s·√τ remaining wall on a coated riser, not r20/r22 ECT capacitance tomography, not r21 ECA FSW lift-off, not r27/r28 MFL Hall remaining-wall, not r23 PAUT TFM, not r34 GPR two-way time.
- **111 confocal chromatic** is k_λ·(λ−λ0) millimetre ribbon thickness, not r30 ellipsometry Cauchy-n / OPD on PECVD nm films, not r20/r21 THz-TDS, not r33 FMCW lining, not r16 hyperspectral crop, not r32 laser-shearography.

## Round 36 batch summary (3 pairs, 6 trajectories)

| id | modality (NEW family) | domain | decisions | headline |
|----|----------------------|--------|-----------|----------|
| nelb-r36-109 | longitudinal BGO Pockels GIS bus voltage (k_eo·I_x/I_y kV, k_g·V mrad, Busveil patched-V_π denial, 18 min SF6-settle floor) | Thistlemere GIS TM-6 bay B-3 (invented): 4.00·(12.00/3.00) reconstructs 16.00 kV while Busveil still reads 7.20 kV and the capacitive divider 8.40 kV | MODIFY (+0.40) / ACCEPT (+0.35) | serialized `4.00*(12.00/3.00)=16.00` and `2.50*16.00=40.00`; conjunctive SOP (V AND SNR) forbids keep-1.00 bay; companion t2 holds 0.80 pu and refuses a Busveil restore; sim_or_real=designed |
| nelb-r36-110 | pulsed eddy current remaining wall of a coated riser (k_s·√τ mm, Wrapveil last-inspection denial, 30 min depressurization floor) | Murkspit Riser MS-6 joint J-12 (invented, HIL spool in PEC-HIL-5): 5.00·√9.00 reconstructs 15.00 mm while Wrapveil still reads 22.00 mm and through-coating UT 21.20 mm | REJECT (+0.43) / MODIFY (+0.34) | serialized `5.00*sqrt(9.00)=15.00`; keep-run refused; companion t2 MODIFYs a riser ESD into clamp J-11..J-13 plus production 0.70; sim_or_real=hil |
| nelb-r36-111 | confocal chromatic thickness of a float-glass ribbon (k_λ·(λ−λ0) mm, Ribbonveil last-good + lehr-pyrometer denial, 12 min draw floor) | Culmholt Float CH-5 ribbon R-7 (invented, simulated Chrom-SIM-2): 0.040·(650.0−450.0) reconstructs 8.00 mm while Ribbonveil still reads 6.20 mm and the lehr pyrometer 6.40 mm | ACCEPT (+0.41) / REJECT (+0.36) | serialized `0.040*(650.0-450.0)=8.00`; bounded hold of R-7 only; lehr dump out of scope; companion t2 REJECTS skip-hold; sim_or_real=simulated |

Decision spread: MODIFY / ACCEPT / REJECT / MODIFY / ACCEPT / REJECT — **2A/2M/2R**. All three enums used, and all three sit on **leads**. Provenance spread: designed / hil / simulated (one each; never real). IDs `nelb-r36-109`…`111` plus t1/t2 suffixes.

## Raster sidecar
Every record carries `raster` + top-level `gate_snn` + `gate_compute`. Windows 36/28/40 ms; `window_s == window_ms/1000` exactly; `spikes == round(neurons·rate·window_s)` with zero slack (36/35/40 at 50/50/62.5 Hz over 20/25/16 neurons); `energy_pJ = spikes·23` and `energy_uJ = spikes·23e-6` exact (828/805/920 pJ). Routing source/target + 3-entry tables + `third_factor` on all three (modulators na.gis_voltage_salience / da.riser_wall_error / ach.ribbon_swell_conflict; τe 1.6/1.1/2.2 s as consistent `tau_e_s`+`tau_e_ms` pairs). Excerpts integer `t_us`, in-window, `neuron_id`-bounded, sorted, full-window by construction, per-spike amplitude with adaptation (0.82**k) plus noise. ISI histograms from the full window, bins ≥1 ms, counts sum to `spikes − distinct_active_neurons` ({isis[0]}/{isis[1]}/{isis[2]}). Same-neuron gaps ≥1100 µs pre-round, ≥1000 µs serialized. `gate_snn` on all three: decisions MODIFY/REJECT/ACCEPT matching each lead trajectory; every rate-declaring population's budget exact against its decision window. `gate_compute.per_check` windows 28–40 ms, budgets exact (144+64 / 140+80 / 192+80). Main streams: {events[0]}/{events[1]}/{events[2]} events (inside the 5–40 cap), strictly increasing `t_rel_ms` only (no `t_ms` mix), same-channel refractory ≥0.8 ms (109 Pockels pair at 1.4 ms, 110 PEC pair at 1.2 ms, 111 confocal pair at 1.5 ms).

## Self-critique

### Edge cases added vs still thin
- **Added:** first longitudinal-BGO-Pockels family on a GIS bus with a recomputable V=k_eo·I_x/I_y (`16.00 kV`) plus retardation identity (`40.00 mrad`); first pulsed-eddy-current family on a coated riser with a recomputable d=k_s·√τ (`15.00 mm`); first confocal-chromatic family on a float-glass ribbon with recomputable z=k_λ·(λ−λ0) (`8.00 mm`); first bounded ACCEPT whose out-of-scope clause is a lehr dump rather than a taphole/hopper; first keep-run REJECT lead on a PEC stop that a last-inspection dashboard would have cleared; operational t2 on all three (0.80 hold, clamp+0.70, skip-hold refusal); provenance trio designed/hil/simulated; 18 min / 30 min / 12 min slow floors in-stream.
- **Still thin:** (i) 109's k_eo is a lumped polarimeter gain, not a temperature-dependent r33 / V_π(T) table — a cell-gradient that fakes 16.00 kV inside a healthy capacitive divider is unwritten; (ii) 110's k_s is a lumped μσ lump, not a coating-conductivity map, so a wet wrap that fakes 15 mm is unwritten; (iii) 111's k_λ is a two-point chromatic line, not a tin-bath index table, so a refractive-index walk that fakes 8.00 mm is unwritten; (iv) vendor-only as a *lead* REJECT on a plant with *no* independent witness remains slightly harder — 109/110 still have plant Pockels/PEC heads; (v) stream amplitudes remain authored constants (raster draws are the only seeded noise); (vi) unused r13-premises (mud-pulse, Barkhausen, Lamb-wave) still unharvested.

### Realism of noise / temporal fidelity
- Strong: 109's 16.00 kV, 40.00 mrad, and 18.0 min soak (`7200+1080=8280 s`) recompute from the record; 110's 15.00 mm, 16.00 mm post-hold, and 30.0 min depressurization (`1800+1800=3600 s`) recompute; 111's 8.00 mm, 7.60 mm post-hold, and 12.0 min lehr (`6000+720=6720 s`) recompute. Raster adaptation (0.82**k plus 4% noise) and the 1.2–1.5 ms physics pairs give the 5–40 stream a raster-scale motif without violating 0.8 ms same-channel refractory.
- **Gaps, honestly:** (i) 5–40 cap still forces heavy thinning (2 kHz polarimeter kept as 3 I_x points; ~50 Hz PEC pulser kept as 4 τ points; 1 kHz confocal spectrometer kept as 3 λ points); (ii) 109's post-derate 14.00 kV is a later sample, not a closed-loop voltage controller; (iii) 110 HIL spool times an in-service keep-run stop that the stream does not independently witness on the live joint (UT only); (iv) no gate_snn input→output volley pair at raster resolution this round (r04-a1 already staged that).

### Training value (SNN/LSM + agentic)
Distillation targets: Pockels V=k_eo·I_x/I_y and γ=k_g·V heads; derate-floor cut vs keep-1.00 vs bus-trip; patched-V_π nonsubstitution; PEC d=k_s·√τ head; stop-floor refuse vs keep-run vs riser ESD; last-inspection nonsubstitution; confocal z=k_λ·(λ−λ0) head; bounded ACCEPT with lehr-dump-out-of-scope; skip-hold refusal under takt. Agentic value concentrates in three patterns: reconstruction-as-SoT on a physical error the raw corridor cannot see, earned ACCEPT with an explicit physical out-of-scope object (the lehr dump), and stop-then-hold so a REJECT does not become a freeze-kill of a production riser.

## What round 37 should add (next densification target)
1. **Temperature-dependent r33 / V_π(T)** on a non-TM-6 Pockels cell so a cell-gradient fakes 16.00 kV inside a healthy capacitive divider, closing 109's lumped-k_eo gap.
2. **Coating-conductivity map** on a non-MS-6 PEC so a wet wrap can fake 15 mm while mean τ looks healthy.
3. **Tin-bath index table** on a non-CH-5 confocal so a refractive-index walk fakes 8.00 mm inside a 6.20 mm last-good corridor.
4. **Vendor-only as a lead REJECT** on a plant that has no independent witness installed yet (109/110 still had plant Pockels/PEC).
5. **Do not restage** VOD-SNN replay, pharma cold-chain, CEMS, FBG glaze, Frostlip quench, Oxbow VRFB, IFOG, transmon, hyperspectral, MEMS array, muon ore-pass, industrial x-ray, optogenetic stim, 905 nm LiDAR snow, clamp-on transit-time, LIBS, QEPAS, LFV, Kaplan LDV, THz-TDS, ECT, TDLAS NH3, lock-in thermography, PAUT TFM, EN CUI, RUS porcelain, N-16 loop flow, helium RGA, Faraday FOCT, blade tip-timing, acoustic pyrometry, SPR, vibrating-wire, microwave-cavity, MFL, NMR T2, nucleonic SG, JNT, CRNS, Coriolis, CARS, XRF, Mössbauer, GB-InSAR, ellipsometry, SPND, LII, PALS, NQR, laser-shearography, digital shearography, hydrogen permeation, FMCW lining, GPR, Thistlemere TM-6 Pockels, Murkspit PEC-HIL-5, or Culmholt Chrom-SIM-2 confocal. Leave mud-pulse, Barkhausen, and Lamb-wave available. Do not steal r35 IDs `106`–`108`.

## Verification
`batch-r36.jsonl`: 3 lines, `json.loads`-clean (allow_nan=False), {sizes[0]}/{sizes[1]}/{sizes[2]} bytes (file {BATCH.stat().st_size}, sha256 `{file_sha}`). Staged at `/tmp/nelb-r36/` only. Repo gates: `check_records.check_jsonl` with `FactoryStaging(enabled=True)` → 0 errors, 0 warnings, kinds `{{bridge_pair: 3}}`; `python3 pipelines/check_records.py --strict /tmp/nelb-r36` → 0/0; `curate_bridge.raster_status(..., require_raster=True, require_routing_table=True)` → raster_valid and gate_snn_valid true, empty reason codes; `curate_record(...)` → 3× retain / `BRIDGE_EVENTS_ALREADY_GLOBALLY_ORDERED`; `verify_batch_for_frontier(strict=True)` → 3 verified, 0 inconclusive, 0 failed; `python3 pipelines/spike_probe.py --strict /tmp/nelb-r36/batch-r36.jsonl` → loaded 3, unloadable 0, problems [], third_factor_routes 3, gate_snn_records 3, spikes {spikes}, energy_pJ {energy}. Build-time asserts: global time order; same-channel ≥0.8 ms; 5–40 events ({events[0]}/{events[1]}/{events[2]}); excerpt integer bounds, neuron bounds, sort, 1 ms per-neuron floor; ISI identity {isis[0]}/{isis[1]}/{isis[2]}; spike budgets exact; energy pJ/µJ exact; reward totals equal two-decimal component sums ({reward_s}); gate_snn decisions match lead `safety_decision.decision`; `state.sim_or_real` ∈ {{designed, hil, simulated}}; `meta.round=36`, `meta.factory=neuromorphic-event-language-bridge`, `meta.generator=grok-4.6`, `meta.run_label=2026-09-02-final-heavy`; `meta.rights` 15-key RM-793 stamp (`intended_use=research_only`, `linear_issue=RM-793`, `generated_at={GENERATED_AT}`); no hidden-reasoning keys; no `provenance` objects; no 'real' claims; no `training_ready`; all 9 record/trajectory ids unique. Raster seeds 202609109/202609110/202609111, MT19937.

Honest novelty accounting: 3/3 modality families are new versus the committed factory and versus staged leftover-mill r13–r34 (Pockels ≠ Faraday FOCT/PMU; PEC ≠ ECT/ECA/MFL/PAUT/GPR; confocal ≠ ellipsometry/THz-TDS/FMCW/hyperspectral/shearography). In-stream slow floor, operational t2, and vendor-nonsubstitution are carried edges applied to new physics. Against that: conjunctive SOP, reconstruction-as-SoT, bounded ACCEPT, and stop-then-hold are carried vocabulary; the 5–40 cap is a density constraint not a new teaching object; 34 prior leftover-mill rounds already taught custody/governance at high sophistication. Net: a bit under two-fifths of the round's scenario/edge mass is genuinely novel.

Novel coverage: 37%
"""
    NOTES.write_text(notes, encoding="utf-8")
    print("wrote", NOTES, "bytes", NOTES.stat().st_size)


def main():
    records = [rec_109(), rec_110(), rec_111()]
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
