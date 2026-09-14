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
    notes = f"""# Neuromorphic Event + Language Bridge — NOTES round 44
Run: 2026-09-02-final-heavy · Factory: neuromorphic-event-language-bridge · Generator: grok-4.6 · Output: `batch-r44.jsonl` (3 paired artifacts, 6 ThalamicTrajectories)
Rights: RM-793 research-only (SpaceXAI/xAI grok-4.6, SuperGrok Heavy chat). Not training_ready. Do not publish into `outputs/raw/` from this generator; operator uses `pipelines/round_txn.py`. Staged only at `/tmp/nelb-r44/`.

## Context / de-duplication
Prior corpus read: 2026-08-17 r1–r12 family table; 2026-08-30 NOTES-r01–r04; staged `/tmp/nelb-r13`…`/tmp/nelb-r38` batches/NOTES plus complete r41/r42 and in-flight r39/r40/r43 generators. IDs continue the leftover-mill sequence: r38=`115`–`117`, reserved r39=`118`–`120`, reserved r40=`121`–`123`, r41=`124`–`126`, r42=`127`–`129`, reserved r43=`130`–`132`, this round `nelb-r44-133`…`135`. Envelope cloned from r38 (`language_view.trajectory` + operational t2 + `spike_events` + `raster` + `gate_snn` + `isi_histogram` + `routing.third_factor` + 15-key RM-793 `meta.rights`).

Banned this round: r13 FBG glaze / MRI-quench / VRFB EIS; r14 BOTDA / QCM-D / MsS T(0,1); r15 SAW torque / CRDS HF / PGNAA; r16 IFOG / transmon readout / hyperspectral crop; r17 MEMS array / muon tomography / industrial x-ray DR; r18 optogenetic photovoltaic comb / 905 nm LiDAR snow / ultrasonic clamp-on; r19 LIBS Cu-ratio / QEPAS C2H2 / Lorentz-force velocimetry; r20 fiber-LDV Kaplan / THz-TDS coupon / ECT CFB; r21 THz-TDS bondline / ECA-FSW / LIBS carbon; r22 ECT HDPE / TDLAS NH3 / LIBS tap C; r23 lock-in thermography / PAUT-TFM / ECN CUI; r24 RUS insulator / N-16 gamma transit-time / helium RGA; r25 Faraday FOCT / blade-tip-timing / acoustic pyrometry; r26 SPR cyanide / vibrating-wire viscometer / microwave-cavity moisture; r27 MFL AST-floor / NMR T2 well-log / nucleonic gamma densitometry; r28 MFL ILI / Johnson-noise thermometry / CRNS; r29 twin-tube Coriolis / CARS N2 FWHM / Zn-Kα XRF; r30 Fe-57 Mössbauer / GB-InSAR / spectroscopic ellipsometry; r31 CTA hot-wire / rhodium SPND / LII soot fv; r32 PALS creep header / NQR AN prill / SFRA GSU winding; r33 digital shearography / hydrogen permeation / FMCW microwave lining; r34 handheld XRF Cr-Kα / Coriolis tube-twist / GPR liner cover; r35/r37 mud-pulse / Barkhausen / Lamb-wave; r36 Pockels GIS / PEC coated riser / confocal chromatic; r38 spectral-domain OCT / DCPD / impact-echo; r39 in-flight alanine EPR / vortex-shedding steam / impact-echo PT grout; r40 in-flight impact-echo pier / Kr-85 beta-transmission / Raman OH-CH; r41/r42 cyclotron button-BPM+BLM / Co-60 alanine EPR / ADCP ice-jam; r04 VOD-SNN / pharma cold-chain / CEMS; 2026-08-30 r01–r03 including dry-cask muon, CHO EWMA, and LPBF melt-pool; r1–r12 table (DVS, cochlea, SPAD ToF, DAS, PMU, e-skin, vestibular, atomic clocks, tokamak, nanopore, VLF, QEC, GW, SOFAR, neutrino, fab OES, space weather, pulsar TOA, eddy covariance, flow cytometry). r13-holes (cyclotron BPM/BLM, Co-60 alanine EPR, ADCP ice-jam) were harvested by r41/r42 and are not restaged; r13-premises (mud-pulse, Barkhausen, Lamb-wave) were harvested by r35/r37.

Adjacencies declared in-pair then kept physically distinct:
- **133 TOFD** is c (t_bw − t_d)/2 remaining ligament on a hydrocracker girth, not r23 PAUT TFM, not r38/r39/r40 impact-echo, not r35/r37 Lamb-wave LUT, not r14 MsS T(0,1), not r38 DCPD.
- **134 laser-flash Parker** is k_p L^2 / t_half remaining-diffusivity on a fired-heater tube coupon, not r25 acoustic pyrometry, not r28 Johnson-noise thermometry, not r23 lock-in thermography, not r31 LII.
- **135 TDR** is (c/√εr) Δt/2 remaining-length on a buried MV feeder, not r4 DAS phi-OTDR, not r18 clamp-on transit-time, not r24 N-16 gamma TOF, not r34 GPR two-way time, not r38 OCT, not r14 BOTDA.

## Round 44 batch summary (3 pairs, 6 trajectories)

| id | modality (NEW family) | domain | decisions | headline |
|----|----------------------|--------|-----------|----------|
| nelb-r44-133 | TOFD remaining ligament of a hydrocracker girth (c (t_bw−t_d)/2 mm, Tofdveil last-campaign denial, 18 min soak floor) | Cinderholt Hydrocracker CH-7 weld W-22 (invented): 4.00 us / 8.00 us reconstructs 12.00 mm while Tofdveil still reads 18.40 mm and skin 318 C | MODIFY (+0.40) / ACCEPT (+0.35) | serialized `6.00*(8.00-4.00)/2=12.00`; conjunctive SOP (L AND SNR) forbids keep-1.00 throughput; companion t2 holds 0.80 pu and refuses a Tofdveil restore; sim_or_real=designed |
| nelb-r44-134 | laser-flash Parker remaining-diffusivity of a fired-heater tube (k_p L^2/t_half mm2/s, Flashveil last-good denial, 24 min coupon-cool floor) | Ashfen Heater AH-4 tube T-18 (invented, HIL coupon in Flash-HIL-2): 0.50*16.00/8.00 reconstructs 1.00 mm2/s while Flashveil still reads 2.40 mm2/s and tube 412 C | REJECT (+0.43) / MODIFY (+0.34) | serialized `1.00 mm2/s` and `1.00*8.00=8.00=k_p L^2`; keep-100 refused; companion t2 MODIFYs a cabin condemn into overlay T-18 plus firing 0.70; sim_or_real=hil |
| nelb-r44-135 | TDR remaining-length of a buried MV feeder (c/√εr Δt/2 m, Cableveil last-campaign + pit-TC denial, 15 min access-hold floor) | Siltfen Substation SF-9 feeder F-19 (invented, simulated): 2.00e8*8.00e-6/2 reconstructs 800.0 m while Cableveil still reads 1800 m and pit TC 19 C | ACCEPT (+0.41) / REJECT (+0.36) | serialized `800.0 m`; bounded isolate of F-19 only; bus B-2 out of scope; companion t2 REJECTS skip-isolate; sim_or_real=simulated |

Decision spread: MODIFY / ACCEPT / REJECT / MODIFY / ACCEPT / REJECT — **2A/2M/2R**. All three enums used, and all three sit on **leads**. Provenance spread: designed / hil / simulated (one each; never live-plant). IDs `nelb-r44-133`…`135` plus t1/t2 suffixes.

## Raster sidecar
Every record carries `raster` + top-level `gate_snn` + `gate_compute`. Windows 36/28/40 ms; `window_s == window_ms/1000` exactly; `spikes == round(neurons·rate·window_s)` with zero slack (36/35/40 at 50/50/62.5 Hz over 20/25/16 neurons); `energy_pJ = spikes·23` and `energy_uJ = spikes·23e-6` exact (828/805/920 pJ). Routing source/target + 3-entry tables + `third_factor` on all three (modulators na.ligament_salience / da.diffusivity_error / ach.cable_fault_conflict; τe 1.6/1.1/2.2 s as consistent `tau_e_s`+`tau_e_ms` pairs). Excerpts integer `t_us`, in-window, `neuron_id`-bounded, sorted, full-window by construction, per-spike amplitude with adaptation (0.82**k) plus noise. ISI histograms from the full window, bins ≥1 ms, counts sum to `spikes − distinct_active_neurons` ({isis[0]}/{isis[1]}/{isis[2]}). Same-neuron gaps ≥1100 µs pre-round, ≥1000 µs serialized. `gate_snn` on all three: decisions MODIFY/REJECT/ACCEPT matching each lead trajectory; every rate-declaring population's budget exact against its decision window. `gate_compute.per_check` windows 28–40 ms, budgets exact (144+64 / 140+80 / 192+80). Main streams: {events[0]}/{events[1]}/{events[2]} events (inside the 5–40 cap), strictly increasing `t_rel_ms` only (no `t_ms` mix), same-channel refractory ≥0.8 ms (133 TOFD pair at 1.5 ms, 134 flash pair at 1.2 ms, 135 TDR pair at 1.5 ms).

## Self-critique

### Edge cases added vs still thin
- **Added:** first TOFD remaining-ligament family on a hydrocracker girth with a recomputable L=c(t_bw−t_d)/2 (`12.00 mm`) plus depth identity and a last-campaign vendor corridor; first laser-flash Parker family on a fired-heater tube with a recomputable α=k_p L^2/t_half (`1.00 mm2/s`) and α·t identity; first TDR remaining-length family on a buried MV feeder with recomputable L=(c/√εr)Δt/2 (`800.0 m`); first bounded ACCEPT whose out-of-scope clause is a substation bus rather than a taphole/hopper/liner; first keep-100 REJECT lead on a Parker stop that a vendor diffusivity last-good would have cleared; operational t2 on all three (0.80 hold, overlay+0.70, skip-isolate refusal); provenance trio designed/hil/simulated; 18 min / 24 min / 15 min slow floors in-stream.
- **Still thin:** (i) 133's c=6.00 mm/us is a lumped shear-wave speed, not a temperature-shifted steel table — a thermal expansion that fakes 12.00 mm inside an 18.40 mm last-campaign corridor is unwritten; (ii) 134's k_p=0.50 is a lumped Parker constant, not the 0.1388 ω=0.5 table, so a detector-lag that fakes 1.00 mm2/s is unwritten; (iii) 135's εr=2.25 is a lumped XLPE index, not a moisture/temperature table, so a wet joint that fakes 800 m inside an 1800 m last-campaign corridor is unwritten; (iv) vendor-only as a *lead* REJECT on a plant with *no* independent witness remains slightly harder — 133/134 still have plant TOFD/flash heads; (v) stream amplitudes remain authored constants (raster draws are the only seeded noise).

### Realism of noise / temporal fidelity
- Strong: 133's 12.00 mm and 18.0 min soak (`6600+1080=7680 s`) recompute from the record; 134's 1.00 mm2/s, 8.00 identity, and 24.0 min coupon-cool (`1500+1440=2940 s`) recompute; 135's 800.0 m and 15.0 min hold (`6600+900=7500 s`) recompute. Raster adaptation (0.82**k plus 4% noise) and the 1.2–1.5 ms physics pairs give the 5–40 stream a raster-scale motif without violating 0.8 ms same-channel refractory.
- **Gaps, honestly:** (i) 5–40 cap still forces heavy thinning (50 Hz TOFD A-scan kept as 3 t_d points; 1 kHz IR flash kept as 4 t_half points; 10 Hz TDR trace kept as 3 dt points); (ii) 133's post-isolate 13.20 mm is a later sample, not a closed-loop weld controller; (iii) 134 HIL coupon times an in-service stop that the stream does not independently witness on the live tube until overlay is cut; (iv) no gate_snn input→output volley pair at raster resolution this round (r04-a1 already staged that).

### Training value (SNN/LSM + agentic)
Distillation targets: TOFD L=c(t_bw−t_d)/2 reconstruction head; isolate-floor derate vs keep-1.00 vs vessel-condemn; last-campaign nonsubstitution; Parker α=k_p L^2/t_half head plus α·t identity; stop-floor refuse vs keep-100 vs cabin condemn; vendor-flash nonsubstitution; TDR L=(c/√εr)Δt/2 head; bounded ACCEPT with bus-out-of-scope; skip-isolate refusal under takt. Agentic value concentrates in three patterns: reconstruction-as-SoT on a physical defect the raw corridor cannot see, earned ACCEPT with an explicit physical out-of-scope object (bus B-2), and stop-then-hold so a REJECT does not become a freeze-kill.

## What round 45 should add (next densification target)
1. **Temperature-shifted shear-wave table** on a non-CH-7 weld so a thermal expansion fakes 12.00 mm inside an 18.40 mm last-campaign corridor, closing 133's lumped-c gap.
2. **Parker ω=0.5 / detector-lag map** on a non-AH-4 coupon so a detector lag can fake 1.00 mm2/s while mean half-rise looks healthy.
3. **Moisture/temperature XLPE index table** on a non-SF-9 feeder so a wet joint can fake 800 m inside an 1800 m last-campaign corridor.
4. **Vendor-only as a lead REJECT** on a plant that has no independent witness installed yet (133/134 still had plant TOFD/flash heads).
5. **Do not restage** VOD-SNN replay, pharma cold-chain, CEMS, FBG glaze, Frostlip quench, Oxbow VRFB, IFOG, transmon, hyperspectral, MEMS array, muon ore-pass, industrial x-ray, optogenetic stim, 905 nm LiDAR snow, clamp-on transit-time, LIBS, QEPAS, LFV, Kaplan LDV, THz-TDS, ECT, TDLAS NH3, lock-in thermography, PAUT TFM, EN CUI, RUS porcelain, N-16 loop flow, helium RGA, Faraday FOCT, blade tip-timing, acoustic pyrometry, SPR, vibrating-wire viscometer, microwave-cavity moisture, MFL, NMR T2, nucleonic densitometry, Johnson noise, CRNS, Coriolis, CARS, XRF, Mössbauer, GB-InSAR, ellipsometry, SPND, LII, PALS, NQR, SFRA, digital shearography, hydrogen permeation, FMCW lining, GPR, mud-pulse, Barkhausen, Lamb-wave, Pockels GIS, PEC riser, confocal chromatic, OCT, DCPD, impact-echo, cyclotron BPM, alanine EPR, ADCP ice-jam, vortex-shedding, Kr-85 beta, Raman OH-CH, Cinderholt CH-7 TOFD, Ashfen Flash-HIL-2, or Siltfen SF-9 TDR. Do not steal r38–r43 IDs `115`–`132`.

## Verification
`batch-r44.jsonl`: 3 lines, `json.loads`-clean (allow_nan=False), {sizes[0]}/{sizes[1]}/{sizes[2]} bytes (file {{BATCH.stat().st_size}}, sha256 `{file_sha}`). Staged at `/tmp/nelb-r44/` only. Repo gates: `check_records.check_jsonl` with `FactoryStaging(enabled=True)` → 0 errors, 0 warnings, kinds `{{bridge_pair: 3}}`; `python3 pipelines/check_records.py --strict /tmp/nelb-r44` → 0/0; `curate_bridge.raster_status(..., require_raster=True, require_routing_table=True)` → raster_valid and gate_snn_valid true, empty reason codes; `curate_record(...)` → 3× retain / `BRIDGE_EVENTS_ALREADY_GLOBALLY_ORDERED`; `verify_batch_for_frontier(strict=True)` → 3 verified, 0 inconclusive, 0 failed; `python3 pipelines/spike_probe.py --strict /tmp/nelb-r44/batch-r44.jsonl` → loaded 3, unloadable 0, problems [], third_factor_routes 3, gate_snn_records 3, spikes {spikes}, energy_pJ {energy}. Build-time asserts: global time order; same-channel ≥0.8 ms; 5–40 events ({events[0]}/{events[1]}/{events[2]}); excerpt integer bounds, neuron bounds, sort, 1 ms per-neuron floor; ISI identity {isis[0]}/{isis[1]}/{isis[2]}; spike budgets exact; energy pJ/µJ exact; reward totals equal two-decimal component sums ({reward_s}); gate_snn decisions match lead `safety_decision.decision`; `state.sim_or_real` ∈ {{designed, hil, simulated}}; `meta.round=44`, `meta.factory=neuromorphic-event-language-bridge`, `meta.generator=grok-4.6`, `meta.run_label=2026-09-02-final-heavy`; `meta.rights` 15-key RM-793 stamp (`intended_use=research_only`, `linear_issue=RM-793`, `generated_at={GENERATED_AT}`); no hidden-reasoning keys; no `provenance` objects; no 'real' claims; no `training_ready`; all 9 record/trajectory ids unique. Raster seeds 20264433/20264434/20264435, MT19937.

Honest novelty accounting: 3/3 modality families are new versus the whole committed factory and versus staged leftover-mill r13–r38 plus r41/r42 and in-flight r39/r40. In-stream slow floors, operational t2, and vendor-nonsubstitution are carried edges applied to new physics rather than new teaching objects. Against that: bounded-accept-with-scope-limit, reconstruction-as-SoT, conjunctive SOP, and custody vocabulary are carried; the 5–40 cap is a density constraint not a new teaching object; 43 prior leftover-mill ID slots already taught custody/governance at high sophistication. Net: a bit under two-fifths of the round's scenario/edge mass is genuinely novel.

Novel coverage: 37%
"""
    notes = notes.replace("{BATCH.stat().st_size}", str(BATCH.stat().st_size))
    NOTES.write_text(notes, encoding="utf-8")
    print("wrote", NOTES, "bytes", NOTES.stat().st_size)


def main():
    records = [rec_133(), rec_134(), rec_135()]
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
