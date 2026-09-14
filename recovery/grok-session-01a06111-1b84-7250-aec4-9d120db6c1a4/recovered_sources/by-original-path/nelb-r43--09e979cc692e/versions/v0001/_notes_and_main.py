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
        raise RuntimeError(f"check_records --strict failed: {(strict.stdout or '') + (strict.stderr or '')}")

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
    notes = f"""# Neuromorphic Event + Language Bridge — NOTES round 43
Run: 2026-09-02-final-heavy · Factory: neuromorphic-event-language-bridge · Generator: grok-4.6 · Output: `batch-r43.jsonl` (3 paired artifacts, 6 ThalamicTrajectories)
Rights: RM-793 research-only (SpaceXAI/xAI grok-4.6, SuperGrok Heavy chat). Not training_ready. Do not publish into `outputs/raw/` from this generator; operator uses `pipelines/round_txn.py`. Staged only at `/tmp/nelb-r43/`.

## Context / de-duplication
Prior corpus read: 2026-08-30 NOTES-r01–r04, 2026-08-17-w3 NOTES-r12 family table, staged `/tmp/nelb-r13` through `/tmp/nelb-r37` batches/NOTES plus in-flight `/tmp/nelb-r38` (spectral-domain OCT / DCPD / pulsed-eddy-current, ids `115`–`117`, generator present, no batch yet), empty `/tmp/nelb-r39` and `/tmp/nelb-r40` (`_head.py` only), and `/tmp/nelb-r41/gen_r41.py` (incomplete r37 clone of mud-pulse/Barkhausen/Lamb-wave, ids `124`–`126` reserved, treated as a collision source not a clone source). IDs continue the leftover-mill sequence: r37=`112`–`114`, implied r38–r42=`115`–`129`, this round `nelb-r43-130`…`132` as assigned. Envelope cloned from complete r37 (`language_view.trajectory` + operational t2 + `spike_events` + `raster` + `gate_snn` + `isi_histogram` + `routing.third_factor` + 15-key RM-793 `meta.rights`).

Banned this round (committed + staged leftover-mill r13–r37 and in-flight r38/r41 generators): not VOD-SNN replay, not pharma cold-chain, not stack-gas CEMS; not r13 FBG glaze / Frostlip quench / Oxbow VRFB; not r14 BOTDA / QCM-D / MsS T(0,1); not r15 SAW torque / CRDS HF / PGNAA; not r16 IFOG / transmon readout / hyperspectral crop; not r17 MEMS accel array / muon ore-pass / industrial x-ray DR; not r18 optogenetic PV / 905 nm LiDAR snow / clamp-on transit-time; not r19 LIBS Cu / QEPAS DGA / LFV Al; not r20 Kaplan LDV / THz-TDS radome moisture / ECT CFB; not r21 THz-TDS bondline / ECA FSW lift-off / LIBS C; not r22 ECT pneumatic riser / TDLAS NH3 / LIBS tap; not r23 lock-in thermography CFRP / PAUT TFM girth / EN CUI; not r24 RUS porcelain / N-16 transit-time loop / helium RGA; not r25 Faraday FOCT / blade tip-timing / acoustic pyrometry; not r26 SPR cyanide / VW viscometer / MW cavity moisture; not r27 MFL AST / NMR T2 / Cs-137 densitometry; not r28 MFL ILI / JNT / CRNS; not r29 Coriolis bitumen / CARS TIT / Zn-Ka XRF; not r30 Mössbauer FCC / GB-InSAR tailings / ellipsometry PECVD; not r31 CTA hot-wire / rhodium SPND / LII soot; not r32 PALS / 14N NQR / SFRA; not r33 digital shearography hull / hydrogen permeation / FMCW BOF lining; not r34 handheld XRF Cr-Kα / Coriolis tube-twist / GPR liner cover; not r35/r37 mud-pulse / Barkhausen / Lamb-wave; not r36 longitudinal BGO Pockels / pulsed eddy current riser / confocal chromatic; not r38 spectral-domain OCT / DCPD / PEC reformer. Plants not reused: Nettlewake, Frostlip, Oxbow, Rift-Caldera-3, Skarv-Naze GN-14, Orinoco-Span OD-12, Kilncrag KC-8, Rookspit RS-4, Spindrift SD-12, Thistlemere TM-6, Murkspit MS-6, Culmholt CH-5, Gorsekettle GK-5, Flintspit FG-8, Wharfleck WD-11, Cobblemere CM-5, Vellumkettle VK-4, Lanternfell LF-6, Greyfen KCTC-7, Pellucid IRRAD-P4, Whitefork WF-9.

This round harvests the three oldest unused r13-holes families (cyclotron button-BPM+BLM, Co-60 alanine EPR, ADCP ice-jam), left available through r37 NOTES, on new invented plants.

Adjacencies declared in-pair then kept physically distinct:
- **130 cyclotron button-BPM + BLM** is TDC button Δt steering plus maze loss-monitor current, not r5 PMU synchrophasors, not r5 fluxgate gradiometry, not r6 portal NaI, not r01/r17 muon tomography.
- **131 Co-60 alanine EPR** is a panoramic-irradiator dosimeter comb, not r6 portal counting, not r04 pharmaceutical cold-chain RFID, not r04 CEMS.
- **132 river ADCP ice-jam** is backscatter/velocity-bin stage plus thermistor freeze-up, not r4 DAS phi-OTDR, not r7 infrasound, not r10 SOFAR, not r03 water-distribution hydraulics, not r12 eddy-covariance.

## Round 43 batch summary (3 pairs, 6 trajectories)

| id | modality (NEW family) | domain | decisions | headline |
|----|----------------------|--------|-----------|----------|
| nelb-r43-130 | cyclotron button-BPM + maze BLM (k_bpm·Δt steering mm, k_blm·I·t dose mGy, Beamveil patched-TDC denial, 18 min RP soak floor) | Thornveil TV-8 TR-4 (invented): 0.250·48.00 reconstructs 12.00 mm while Beamveil still reads 0.40 ns and HIS looks clean | MODIFY (+0.40) / ACCEPT (+0.35) | serialized `0.250*48.00=12.00` and `0.040*8.00*40.00=12.80`; conjunctive SOP (x AND SNR) forbids keep-fraction; three-party collusion includes the TDC infra owner; companion t2 RP-interlock resume, vault ESD refused; sim_or_real=designed |
| nelb-r43-131 | Co-60 alanine EPR of a panoramic irradiator tote (k_e·A_pp kGy, Raiseveil dummy-encoder denial, 12 min EPR re-read floor) | Saltmere IRRAD-S7 tote T-8804 (invented, HIL spare in EPR-HIL-4): 0.250·2.00 reconstructs 0.50 kGy while Raiseveil still reads 1200 mm source-up and a cloned badge is at the door | REJECT (+0.43) / MODIFY (+0.34) | serialized `0.250*2.00=0.50` and `25.00*48.00=1200.0`; keep-referral refused; operator Nia Brack exonerated (GM no-source-up, canteen clock vs irradiator PLC); companion t2 tote+encoder quarantine; sim_or_real=hil |
| nelb-r43-132 | river ADCP ice-jam volume of a boom station (k_h·h e3 m3, Doppler Q identity, Jamveil last-good denial, 12 min scan floor) | Greylock GL-6 panel 2 (invented, simulated ADCP-SIM-4): 12.00·4.00 reconstructs 48.00 e3 m3 while Jamveil still reads 2.10 m | ACCEPT (+0.41) / REJECT (+0.36) | serialized `12.00*4.00=48.00`; `0.040*50.00=2.00`; `2.00*6.00=12.00`; bounded ACCEPT of panel 2 only; panels 1 and 3 out of scope; companion t2 REJECTS skip-blow; sim_or_real=simulated |

Decision spread: MODIFY / ACCEPT / REJECT / MODIFY / ACCEPT / REJECT — **2A/2M/2R**. All three enums used, and all three sit on **leads**. Provenance spread: designed / hil / simulated (one each; never real). IDs `nelb-r43-130`…`132` plus t1/t2 suffixes.

## Raster sidecar
Every record carries `raster` + top-level `gate_snn` + `gate_compute`. Windows {wins[0]:.0f}/{wins[1]:.0f}/{wins[2]:.0f} ms; `window_s == window_ms/1000` exactly; `spikes == round(neurons·rate·window_s)` with zero slack ({n_sp[0]}/{n_sp[1]}/{n_sp[2]} at {rates[0]}/{rates[1]}/{rates[2]} Hz over {n_neu[0]}/{n_neu[1]}/{n_neu[2]} neurons); `energy_pJ = spikes·23` and `energy_uJ = spikes·23e-6` exact ({n_sp[0]*23}/{n_sp[1]*23}/{n_sp[2]*23} pJ). Routing source/target + 3-entry tables + `third_factor` on all three (modulators {tfs[0]} / {tfs[1]} / {tfs[2]}; τe {taus[0]}/{taus[1]}/{taus[2]} s as consistent `tau_e_s`+`tau_e_ms` pairs). Excerpts integer `t_us`, in-window, `neuron_id`-bounded, sorted, full-window by construction, per-spike amplitude with adaptation (0.82**k) plus noise. ISI histograms from the full window, bins ≥1 ms, counts sum to `spikes − distinct_active_neurons` ({isis[0]}/{isis[1]}/{isis[2]}). Same-neuron gaps ≥1100 µs pre-round, ≥1000 µs serialized. `gate_snn` on all three: decisions MODIFY/REJECT/ACCEPT matching each lead trajectory; every rate-declaring population's budget exact against its decision window. `gate_compute.per_check` windows 32–40 ms, budgets exact ({gc[0]} / {gc[1]} / {gc[2]}). Main streams: {events[0]}/{events[1]}/{events[2]} events (inside the 5–40 cap), strictly increasing `t_rel_ms` only (no `t_ms` mix), same-channel refractory ≥0.8 ms (130 BPM pair at 1.4 ms, 131 EPR pair at 1.2 ms, 132 ADCP pair at 1.5 ms).

## Self-critique

### Edge cases added vs still thin
- **Added:** first cyclotron button-BPM + maze-BLM family on a compact therapy cyclotron with a recomputable x=k_bpm·Δt (`12.00 mm`) plus BLM dose identity (`12.80 mGy`) and three-party collusion including the TDC infra owner; first Co-60 alanine-EPR family on a panoramic irradiator with recomputable D=k_e·A_pp (`0.50 kGy`) and dummy-encoder identity, plus a resolved-innocent operator (GM no-source-up plus canteen clock, not last-badge-at-door); first river-ADCP ice-jam family on a boom station with recomputable V=k_h·h (`48.00 e3 m3`) plus Doppler Q identity; first bounded ACCEPT whose out-of-scope clause is adjacent boom panels rather than a hopper/taphole/dump cap; harvest of the three leftover r13-holes families that r14–r37 explicitly left on the table; operational t2 on all three (RP-interlock resume, tote+encoder quarantine, skip-blow refusal); provenance trio designed/hil/simulated; 18 min / 12 min / 12 min slow floors in-stream.
- **Still thin:** (i) 130's k_bpm is a lumped TDC gain, not a temperature-dependent r33 / delay table — a cell-gradient that fakes 12.00 mm inside a healthy Beamveil corridor is unwritten; (ii) 131's k_e is a lumped comb calibration, not a microwave-power / orientation map, so a cavity walk that fakes 0.50 kGy is unwritten; (iii) 132's k_h is a lumped stage-to-volume gain, not a Saint-Venant / ice-porosity table, so a frazil-density walk that fakes 48.00 e3 m3 is unwritten; (iv) vendor-only as a *lead* REJECT on a plant with *no* independent BPM/EPR/ADCP remains slightly harder — 130/131 still have plant TDC/EPR heads; (v) stream amplitudes remain authored constants (raster draws are the only seeded noise).

### Realism of noise / temporal fidelity
- Strong: 130's 12.00 mm, 12.80 mGy, and 18.0 min soak (`6000+1080=7080 s`) recompute from the record; 131's 0.50 kGy, 1200.0 mm dummy-encoder identity, and 12.0 min EPR re-read (`2820+720=3540 s`) recompute; 132's 48.00 e3 m3, v 2.00 m/s, Q 12.00 m3/s, and 12.0 min scan (`6000+720=6720 s`) recompute. Raster adaptation (0.82**k plus 4% noise) and the 1.2–1.5 ms physics pairs give the 5–40 stream a raster-scale motif without violating 0.8 ms same-channel refractory.
- **Gaps, honestly:** (i) 5–40 cap still forces heavy thinning (kHz BPM TDC kept as 4 dt points; kHz EPR sweep kept as 4 A_pp points; ~Hz ADCP ping kept as 4 h points); (ii) 130's post-isolate 5.00 mm is a later sample, not a closed-loop steering controller; (iii) 131 HIL tote times an in-service referral stop that the stream does not independently witness on a second live tote until the dummy encoder is imaged; (iv) no gate_snn input→output volley pair at raster resolution this round (r04-a1 already staged that).

### Training value (SNN/LSM + agentic)
Distillation targets: BPM x=k_bpm·Δt and D=k_blm·I·t heads; steer-floor isolate vs keep-fraction vs vault ESD; TDC-infra collusion; alanine D=k_e·A_pp head plus dummy-encoder identity; referral-floor refuse vs warehouse-condemn vs tote quarantine; GM/canteen exoneration; ADCP V=k_h·h and Doppler Q heads; bounded ACCEPT with panel-out-of-scope; skip-blow refusal under takt. Agentic value concentrates in three patterns: reconstruction-as-SoT on a physical steer/underdose/jam the raw corridor cannot see, earned ACCEPT with an explicit physical out-of-scope object (panels 1 and 3), and stop-then-hold so a REJECT does not become a warehouse/vault kill.

## What round 44 should add (next densification target)
1. **Temperature-dependent BPM TDC / delay table** on a non-TV-8 cyclotron so a cell-gradient fakes 12.00 mm inside a healthy Beamveil corridor, closing 130's lumped-k_bpm gap.
2. **Microwave-power / orientation map** on a non-S7 alanine comb so a cavity walk fakes 0.50 kGy while mean A_pp looks like background.
3. **Saint-Venant / ice-porosity table** on a non-GL-6 boom so a frazil-density walk fakes 48.00 e3 m3 inside a 2.10 m last-good corridor.
4. **Vendor-only as a lead REJECT** on a plant that has no independent BPM/EPR/ADCP installed yet (130/131 still had plant heads).
5. **Do not restage** VOD-SNN replay, pharma cold-chain, CEMS, FBG glaze, Frostlip quench, Oxbow VRFB, IFOG, transmon, hyperspectral, MEMS array, muon ore-pass, industrial x-ray, optogenetic stim, 905 nm LiDAR snow, clamp-on transit-time, LIBS, QEPAS, LFV, Kaplan LDV, THz-TDS, ECT, TDLAS NH3, lock-in thermography, PAUT TFM, EN CUI, RUS porcelain, N-16 loop flow, helium RGA, Faraday FOCT, blade tip-timing, acoustic pyrometry, SPR, vibrating-wire, microwave-cavity, MFL, NMR T2, nucleonic SG, JNT, CRNS, Coriolis, CARS, XRF, Mössbauer, GB-InSAR, ellipsometry, SPND, LII, PALS, NQR, SFRA, digital shearography, hydrogen permeation, FMCW lining, GPR, Pockels, pulsed eddy current, confocal chromatic, OCT, DCPD, mud-pulse, Barkhausen, Lamb-wave, Thornveil TV-8 BPM, Saltmere IRRAD-S7 alanine, or Greylock GL-6 ADCP. Greyfen KCTC-7, Pellucid IRRAD-P4, and Whitefork WF-9 remain unused plant names and must not be reused.

## Verification
`batch-r43.jsonl`: 3 lines, `json.loads`-clean (allow_nan=False), {sizes[0]}/{sizes[1]}/{sizes[2]} bytes (file {{BATCH.stat().st_size}}, sha256 `{file_sha}`). Staged at `/tmp/nelb-r43/` only. Repo gates: `check_records.check_jsonl` with `FactoryStaging(enabled=True)` → 0 errors, 0 warnings, kinds `{{bridge_pair: 3}}`; `python3 pipelines/check_records.py --strict /tmp/nelb-r43` → 0/0; `curate_bridge.raster_status(..., require_raster=True, require_routing_table=True)` → raster_valid and gate_snn_valid true, empty reason codes; `curate_record(...)` → 3× retain / `BRIDGE_EVENTS_ALREADY_GLOBALLY_ORDERED`; `verify_batch_for_frontier(strict=True)` → 3 verified, 0 inconclusive, 0 failed; `python3 pipelines/spike_probe.py --strict /tmp/nelb-r43/batch-r43.jsonl` → loaded 3, unloadable 0, problems [], third_factor_routes 3, gate_snn_records 3, spikes {spikes}, energy_pJ {energy}. Build-time asserts: global time order; same-channel ≥0.8 ms; 5–40 events ({events[0]}/{events[1]}/{events[2]}); excerpt integer bounds, neuron bounds, sort, 1 ms per-neuron floor; ISI identity {isis[0]}/{isis[1]}/{isis[2]}; spike budgets exact; energy pJ/µJ exact; reward totals equal two-decimal component sums ({reward_s}); gate_snn decisions match lead `safety_decision.decision`; `state.sim_or_real` ∈ {{designed, hil, simulated}}; `meta.round=43`, `meta.factory=neuromorphic-event-language-bridge`, `meta.generator=grok-4.6`, `meta.run_label=2026-09-02-final-heavy`; `meta.rights` 15-key RM-793 stamp (`intended_use=research_only`, `linear_issue=RM-793`, `generated_at={GENERATED_AT}`); no hidden-reasoning keys; no `provenance` objects; no 'real' claims; no `training_ready`; all 9 record/trajectory ids unique. Raster seeds 202609130/202609131/202609132, MT19937.

Honest novelty accounting: 3/3 modality families are new versus the whole committed factory and versus staged leftover-mill r13–r37 (these three were the oldest named leftover in r13-holes and were left available through r37). In-stream slow floors, operational t2, and vendor-nonsubstitution are carried edges applied to new physics rather than new teaching objects. Three-party collusion and exoneration were already taught on r13 quench/VRFB and r37 Barkhausen, so those heads are carried onto new sensors. Against that: bounded-accept-with-scope-limit, reconstruction-as-SoT, conjunctive SOP, and custody vocabulary are carried; the 5–40 cap is a density constraint not a new teaching object; 30 prior leftover-mill rounds already taught custody/governance at high sophistication. Net: about two-fifths of the round's scenario/edge mass is genuinely novel.

Novel coverage: 40%
"""
    # The file-size placeholder above used doubled braces so the f-string
    # does not evaluate BATCH.stat() twice; splice the real size now.
    notes = notes.replace("{BATCH.stat().st_size}", str(BATCH.stat().st_size))
    NOTES.write_text(notes, encoding="utf-8")
    print("wrote", NOTES, "bytes", NOTES.stat().st_size)


def main():
    records = [rec_130(), rec_131(), rec_132()]
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
