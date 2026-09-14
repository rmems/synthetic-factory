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
    notes = f"""# Neuromorphic Event + Language Bridge — NOTES round 42
Run: 2026-09-02-final-heavy · Factory: neuromorphic-event-language-bridge · Generator: grok-4.6 · Output: `batch-r42.jsonl` (3 paired artifacts, 6 ThalamicTrajectories)
Rights: RM-793 research-only (SpaceXAI/xAI grok-4.6, SuperGrok Heavy chat). Not training_ready. Do not publish into `outputs/raw/` from this generator; operator uses `pipelines/round_txn.py`. Staged only at `/tmp/nelb-r42/`.

## Context / de-duplication
Prior corpus read: 2026-08-30 NOTES-r01–r04, 2026-08-17-w3 NOTES-r12 family table, `/tmp/nelb-r13-holes.md` + `/tmp/nelb-r13-premises.md`, staged `/tmp/nelb-r13` through `/tmp/nelb-r37` batches/NOTES plus in-flight `/tmp/nelb-r38` (spectral-domain OCT / DCPD / PEC, ids `115`–`117` reserved, no batch yet). IDs: r13=`040`–`042` … r37=`112`–`114`, reserved r38–r41=`115`–`126`, this round `nelb-r42-127`…`129` as assigned. Envelope cloned from complete r37 (`language_view.trajectory` + operational t2 + `spike_events` + `raster` + `gate_snn` + `isi_histogram` + `routing.third_factor` + 15-key RM-793 `meta.rights`).

Banned this round (committed + staged leftover-mill r13–r37 and in-flight r38 generator): not VOD-SNN replay, not pharma cold-chain, not stack-gas CEMS; not r13 FBG glaze / Frostlip quench / Oxbow VRFB; not r14 BOTDA / QCM-D / MsS T(0,1); not r15 SAW torque / CRDS HF / PGNAA; not r16 IFOG / transmon readout / hyperspectral crop; not r17 MEMS accel array / muon ore-pass / industrial x-ray DR; not r18 optogenetic PV / 905 nm LiDAR snow / clamp-on transit-time; not r19 LIBS Cu / QEPAS DGA / LFV Al; not r20 Kaplan LDV / THz-TDS radome moisture / ECT CFB; not r21 THz-TDS bondline / ECA FSW lift-off / LIBS C; not r22 ECT pneumatic riser / TDLAS NH3 / LIBS tap; not r23 lock-in thermography CFRP / PAUT TFM girth / EN CUI; not r24 RUS porcelain / N-16 transit-time loop / helium RGA; not r25 Faraday FOCT / blade tip-timing / acoustic pyrometry; not r26 SPR cyanide / VW viscometer / MW cavity moisture; not r27 MFL AST / NMR T2 / Cs-137 densitometry; not r28 MFL ILI / JNT / CRNS; not r29 Coriolis bitumen / CARS TIT / Zn-Ka XRF; not r30 Mössbauer FCC / GB-InSAR tailings / ellipsometry PECVD; not r31 CTA hot-wire / rhodium SPND / LII soot; not r32 PALS / 14N NQR / SFRA; not r33 digital shearography hull / hydrogen permeation / FMCW BOF lining; not r34 handheld XRF Cr-Kα / Coriolis tube-twist / GPR liner cover; not r35/r37 mud-pulse MWD / Barkhausen / Lamb-wave; not r36 Pockels GIS / PEC coated riser / confocal chromatic; not r38 OCT TBC / DCPD girth / PEC reformer. Plants not reused: Nettlewake, Frostlip, Oxbow, Rift-Caldera-3, Skarv-Naze GN-14, Orinoco-Span OD-12, Kilncrag KC-8, Rookspit RS-4, Spindrift SD-12, Gorsekettle GK-5, Flintspit FG-8, Wharfleck WD-11, Thistlemere TM-6, Murkspit MS-6, Culmholt CH-5, Cobblemere CM-5, Vellumkettle VK-4, Lanternfell LF-6, Greyfen KCTC-7, Pellucid IRRAD-P4, Whitefork WF-9.

This round harvests the three oldest unused r13-holes families (cyclotron BPM/BLM, Co-60 alanine EPR, ADCP ice-jam), left available through r37 NOTES, on new invented plants.

Adjacencies declared in-pair then kept physically distinct:
- **127 cyclotron BPM/BLM** is button-BPM TDC plus RP ion-chamber maze dose on a compact therapy cyclotron, not r5 PMU, not r5 fluxgate, not r6 portal NaI, not r01/r17 muon tomography, not r31 rhodium SPND.
- **128 alanine EPR** is peak-to-peak comb dosimetry on a panoramic Co-60 irradiator, not r6 portal counting, not r04 cold-chain RFID-as-primary, not r04 CEMS, not r6 cardiovascular interoception.
- **129 ADCP ice-jam** is backscatter/velocity bins plus thermistor-string freeze-up on a river boom, not r4 DAS phi-OTDR, not r10 SOFAR, not r7 infrasound, not r03 water-distribution hydraulics, not r12 eddy-covariance.

## Round 42 batch summary (3 pairs, 6 trajectories)

| id | modality (NEW family) | domain | decisions | headline |
|----|----------------------|--------|-----------|----------|
| nelb-r42-127 | cyclotron button-BPM + BLM / RP ion-chamber maze dose (k_rp·(I−I_bg) mGy, Bpmveil TDC denial, 18 min RF-off floor) | Sloebrake Therapy Cyclotron STC-4 TR-3 (invented): 52.00 nA reconstructs 12.00 mGy while Bpmveil still reads 0.20 mGy | REJECT (+0.43) / MODIFY (+0.34) | serialized `0.250*(52.00-4.00)=12.00`; `12.00/0.80=15.00`; conjunctive SOP (D AND SNR) forbids continue-fraction; three-party collusion includes the TDC infra owner; companion t2 RF-off hold, annex ESD refused; sim_or_real=designed |
| nelb-r42-128 | Co-60 alanine EPR absorbed dose of a panoramic tote (k_e·A_pp kGy, Doseveil last-good denial, 24 min source-down floor) | Brinewharf IRRAD-B6 tote T-7718..T-7740 (invented, HIL dummy in EPR-HIL-4): 30.00 peak-to-peak reconstructs 12.00 kGy while Doseveil still reads 25.20 kGy | MODIFY (+0.40) / ACCEPT (+0.35) | serialized `0.400*30.00=12.00` and `30.00/12.00=2.50`; keep-tote refused; operator Nia Vellum exonerated (missing source-raise AE, UTC vs UTC+1); companion t2 new-encoder restart; sim_or_real=hil |
| nelb-r42-129 | river ADCP ice-jam volume (k_v·Δh·A dam3, Stageveil last-good denial, 12 min survey floor) | Fernspit River boom FR-6 panel 3 (invented, simulated Ice-SIM-2): 2.50 m / 6.00 reconstructs 12.00 dam3 while Stageveil still reads 1.20 m | ACCEPT (+0.41) / REJECT (+0.36) | serialized `0.80*2.50*6.00=12.00`; `40.00/8.00=5.00`; `5.00*2.40=12.00`; bounded ACCEPT of panel 3 only; panels 1-2 out of scope; companion t2 REJECTS skip-blow; sim_or_real=simulated |

Decision spread: REJECT / MODIFY / MODIFY / ACCEPT / ACCEPT / REJECT — **2A/2M/2R**. All three enums used, and all three sit on **leads**. Provenance spread: designed / hil / simulated (one each; never real). IDs `nelb-r42-127`…`129` plus t1/t2 suffixes.

## Raster sidecar
Every record carries `raster` + top-level `gate_snn` + `gate_compute`. Windows {wins[0]:.0f}/{wins[1]:.0f}/{wins[2]:.0f} ms; `window_s == window_ms/1000` exactly; `spikes == round(neurons·rate·window_s)` with zero slack ({n_sp[0]}/{n_sp[1]}/{n_sp[2]} at {rates[0]}/{rates[1]}/{rates[2]} Hz over {n_neu[0]}/{n_neu[1]}/{n_neu[2]} neurons); `energy_pJ = spikes·23` and `energy_uJ = spikes·23e-6` exact ({n_sp[0]*23}/{n_sp[1]*23}/{n_sp[2]*23} pJ). Routing source/target + 3-entry tables + `third_factor` on all three (modulators {tfs[0]} / {tfs[1]} / {tfs[2]}; τe {taus[0]}/{taus[1]}/{taus[2]} s as consistent `tau_e_s`+`tau_e_ms` pairs). Excerpts integer `t_us`, in-window, `neuron_id`-bounded, sorted, full-window by construction, per-spike amplitude with adaptation (0.82**k) plus noise. ISI histograms from the full window, bins ≥1 ms, counts sum to `spikes − distinct_active_neurons` ({isis[0]}/{isis[1]}/{isis[2]}). Same-neuron gaps ≥1100 µs pre-round, ≥1000 µs serialized. `gate_snn` on all three: decisions REJECT/MODIFY/ACCEPT matching each lead trajectory; every rate-declaring population's budget exact against its decision window. `gate_compute.per_check` windows 32–40 ms, budgets exact ({gc[0]} / {gc[1]} / {gc[2]}). Main streams: {events[0]}/{events[1]}/{events[2]} events (inside the 5–40 cap), strictly increasing `t_rel_ms` only (no `t_ms` mix), same-channel refractory ≥0.8 ms (127 RP pair at 1.3 ms, 128 EPR pair at 1.2 ms, 129 ADCP pair at 1.5 ms).

## Self-critique

### Edge cases added vs still thin
- **Added:** first cyclotron button-BPM + BLM / RP ion-chamber family on a compact therapy cyclotron with a recomputable D=k_rp·(I−I_bg) (`12.00 mGy`) plus fluence identity and three-party collusion including the TDC infra owner; first Co-60 alanine-EPR family on a panoramic irradiator with recomputable D=k_e·A_pp (`12.00 kGy`) and comb identity, plus a resolved-innocent operator (timezone-skipped source-raise, not last-to-badge); first river-ADCP ice-jam family on a boom station with recomputable V=k_v·Δh·A (`12.00 dam3`) plus v and Q identities; first bounded ACCEPT whose out-of-scope clause is adjacent boom panels rather than a hopper/taphole/dump cap; operational t2 on all three (RF-off hold, new-encoder restart, skip-blow refusal); provenance trio designed/hil/simulated; 18 min / 24 min / 12 min slow floors in-stream.
- **Still thin:** (i) 127's k_rp is a lumped nA→mGy gain, not a wall-scatter / energy-dependent chamber table — a cable-offset that fakes 12.00 mGy inside a 0.20 mGy BPM corridor is unwritten; (ii) 128's k_e is a lumped comb calibration, not a humidity / orientation map, so a pellet-tilt that fakes 12 kGy is unwritten; (iii) 129's k_v is a lumped porosity/shape factor, not a full Saint-Venant / ice-porosity table, so a frazil-density hop that fakes 12.00 dam3 inside a 1.20 m last-good is unwritten; (iv) vendor-only as a *lead* REJECT on a plant with *no* independent RP/EPR/ADCP installed yet remains slightly harder — 127/128 still have plant heads; (v) stream amplitudes remain authored constants (raster draws are the only seeded noise); (vi) r38 densification leftovers (OCT group-index table, DCPD current-spread map, moisture-corrected PEC) were left for that round's owner.

### Realism of noise / temporal fidelity
- Strong: 127's 12.00 mGy, Phi 15.00, and 18.0 min RF-off (`6000+1080=7080 s`) recompute from the record; 128's 12.00 kGy, G 2.50, and 24.0 min source-down (`2820+1440=4260 s`) recompute; 129's 12.00 dam3, v 5.00, Q 12.00, and 12.0 min survey (`6000+720=6720 s`) recompute. Raster adaptation (0.82**k plus 4% noise) and the 1.2–1.5 ms physics pairs give the 5–40 stream a raster-scale motif without violating 0.8 ms same-channel refractory.
- **Gaps, honestly:** (i) 5–40 cap still forces heavy thinning (50 Hz RP chamber kept as 4 I points; X-band EPR comb kept as 4 A points; 1 Hz ADCP ping kept as 4 dh points); (ii) 127's post-stop 5.00 mGy is a later sample, not a closed-loop RF controller; (iii) 128 HIL tote times an in-service lot isolate that the stream does not independently witness on a second live tote until the new encoder starts; (iv) no gate_snn input→output volley pair at raster resolution this round (r04-a1 already staged that).

### Training value (SNN/LSM + agentic)
Distillation targets: cyclotron D=k_rp·(I−I_bg) reconstruction head plus fluence identity; conjunctive maze floor vs continue-fraction vs annex ESD; TDC-infra collusion; alanine D=k_e·A_pp head plus comb identity; isolate-floor tote vs keep-whole vs warehouse-dump; exoneration against last-to-badge social pressure; ADCP V=k_v·Δh·A and Q identities; bounded ACCEPT with panel-out-of-scope; skip-blow refusal under survey takt. Agentic value concentrates in three patterns: reconstruction-as-SoT on a physical maze/underdose/jam the raw corridor cannot see, earned ACCEPT with an explicit physical out-of-scope object (panels 1-2), and stop-then-hold so a REJECT does not become an annex/warehouse kill.

## What round 43 should add (next densification target)
1. **Wall-scatter / energy-dependent RP chamber table** on a non-STC-4 cyclotron so a cable-offset fakes 12.00 mGy inside a 0.20 mGy BPM corridor, closing 127's lumped-k_rp gap.
2. **Humidity / orientation map** on a non-IRRAD-B6 alanine comb so a pellet-tilt can fake 12 kGy while mean peak-to-peak looks healthy.
3. **Full Saint-Venant / ice-porosity table** on a non-FR-6 boom so a frazil-density hop can fake 12.00 dam3 inside a 1.20 m last-good corridor.
4. **Vendor-only as a lead REJECT** on a plant that has no independent RP/EPR/ADCP installed yet (127/128 still had plant heads).
5. **Do not restage** VOD-SNN replay, pharma cold-chain, CEMS, FBG glaze, Frostlip quench, Oxbow VRFB, IFOG, transmon, hyperspectral, MEMS array, muon ore-pass, industrial x-ray, optogenetic stim, 905 nm LiDAR snow, clamp-on transit-time, LIBS, QEPAS, LFV, Kaplan LDV, THz-TDS, ECT, TDLAS NH3, lock-in thermography, PAUT TFM, EN CUI, RUS porcelain, N-16 loop flow, helium RGA, Faraday FOCT, blade tip-timing, acoustic pyrometry, SPR, vibrating-wire, microwave-cavity, MFL, NMR T2, nucleonic densitometry, JNT, CRNS, Coriolis, CARS, XRF, Mössbauer, GB-InSAR, ellipsometry, CTA, SPND, LII, PALS, NQR, SFRA, digital shearography, hydrogen permeation, FMCW lining, GPR, Pockels, PEC, confocal, mud-pulse, Barkhausen, Lamb-wave, OCT, DCPD, Sloebrake STC-4 BPM, Brinewharf EPR-HIL-4, or Fernspit FR-6 ADCP. Leave r38 densification leftovers (OCT group-index, DCPD current-spread, moisture-corrected PEC) for that round's owner. Do not steal r38–r41 IDs `115`–`126`.

## Verification
`batch-r42.jsonl`: 3 lines, `json.loads`-clean (allow_nan=False), {sizes[0]}/{sizes[1]}/{sizes[2]} bytes (file {BATCH.stat().st_size}, sha256 `{file_sha}`). Staged at `/tmp/nelb-r42/` only. Repo gates: `check_records.check_jsonl` with `FactoryStaging(enabled=True)` → 0 errors, 0 warnings, kinds `{{bridge_pair: 3}}`; `python3 pipelines/check_records.py --strict /tmp/nelb-r42` → 0/0; `curate_bridge.raster_status(..., require_raster=True, require_routing_table=True)` → raster_valid and gate_snn_valid true, empty reason codes; `curate_record(...)` → 3× retain / `BRIDGE_EVENTS_ALREADY_GLOBALLY_ORDERED`; `verify_batch_for_frontier(strict=True)` → 3 verified, 0 inconclusive, 0 failed; `python3 pipelines/spike_probe.py --strict /tmp/nelb-r42/batch-r42.jsonl` → loaded 3, unloadable 0, problems [], third_factor_routes 3, gate_snn_records 3, spikes {spikes}, energy_pJ {energy}. Build-time asserts: global time order; same-channel ≥0.8 ms; 5–40 events ({events[0]}/{events[1]}/{events[2]}); excerpt integer bounds, neuron bounds, sort, 1 ms per-neuron floor; ISI identity {isis[0]}/{isis[1]}/{isis[2]}; spike budgets exact; energy pJ/µJ exact; reward totals equal two-decimal component sums ({reward_s}); gate_snn decisions match lead `safety_decision.decision`; `state.sim_or_real` ∈ {{designed, hil, simulated}}; `meta.round=42`, `meta.factory=neuromorphic-event-language-bridge`, `meta.generator=grok-4.6`, `meta.run_label=2026-09-02-final-heavy`; `meta.rights` 15-key RM-793 stamp (`intended_use=research_only`, `linear_issue=RM-793`, `generated_at={GENERATED_AT}`); no hidden-reasoning keys; no `provenance` objects; no 'real' claims; no `training_ready`; all 9 record/trajectory ids unique. Raster seeds 202609127/202609128/202609129, MT19937.

Honest novelty accounting: 3/3 modality families are new versus the whole committed factory and versus staged leftover-mill r13–r37 (and in-flight r38 OCT/DCPD/PEC). These three were the oldest named leftover in r13-holes and were left available through r37. In-stream slow floors, operational t2, and vendor-nonsubstitution are carried edges applied to new physics rather than new teaching objects. Three-party collusion and exoneration were already taught on r13 quench/VRFB and r37 Barkhausen, so those heads are carried onto new sensors. Against that: bounded-accept-with-scope-limit, reconstruction-as-SoT, conjunctive SOP, and custody vocabulary are carried; the 5–40 cap is a density constraint not a new teaching object; 29 prior leftover-mill rounds already taught custody/governance at high sophistication. Net: about two-fifths of the round's scenario/edge mass is genuinely novel.

Novel coverage: 40%
"""
    NOTES.write_text(notes, encoding="utf-8")
    print("wrote", NOTES, "bytes", NOTES.stat().st_size)


def main():
    records = [rec_127(), rec_128(), rec_129()]
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
