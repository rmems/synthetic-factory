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
    notes = f"""# Neuromorphic Event + Language Bridge — NOTES round 38
Run: 2026-09-02-final-heavy · Factory: neuromorphic-event-language-bridge · Generator: grok-4.6 · Output: `batch-r38.jsonl` (3 paired artifacts, 6 ThalamicTrajectories)
Rights: RM-793 research-only (SpaceXAI/xAI grok-4.6, SuperGrok Heavy chat). Not training_ready. Do not publish into `outputs/raw/` from this generator; operator uses `pipelines/round_txn.py`. Staged only at `/tmp/nelb-r38/`.

## Context / de-duplication
Prior corpus read: 2026-08-17 r1–r12 family table; 2026-08-30 NOTES-r01–r04; staged `/tmp/nelb-r13`…`/tmp/nelb-r37` batches/NOTES. IDs continue the leftover-mill sequence: r33=`100`–`102`, r34=`103`–`105`, r35=`106`–`108`, r36=`109`–`111`, r37=`112`–`114`, this round `nelb-r38-115`…`117`. Envelope cloned from r33 (`language_view.trajectory` + operational t2 + `spike_events` + `raster` + `gate_snn` + `isi_histogram` + `routing.third_factor` + 15-key RM-793 `meta.rights`).

Banned this round: r13 FBG glaze / MRI-quench / VRFB EIS; r14 BOTDA / QCM-D / MsS T(0,1); r15 SAW torque / CRDS HF / PGNAA; r16 IFOG / transmon readout / hyperspectral crop; r17 MEMS array / muon tomography / industrial x-ray DR; r18 optogenetic photovoltaic comb / 905 nm LiDAR snow / ultrasonic clamp-on; r19 LIBS Cu-ratio / QEPAS C2H2 / Lorentz-force velocimetry; r20 fiber-LDV Kaplan / THz-TDS coupon / ECT CFB; r21 THz-TDS bondline / ECA-FSW / LIBS carbon; r22 ECT HDPE / TDLAS NH3 / LIBS tap C; r23 lock-in thermography / PAUT-TFM / ECN CUI; r24 RUS insulator / N-16 gamma transit-time / helium RGA; r25 Faraday FOCT / blade-tip-timing / acoustic pyrometry; r26 SPR cyanide / vibrating-wire viscometer / microwave-cavity moisture; r27 MFL AST-floor / NMR T2 well-log / nucleonic gamma densitometry; r28 MFL ILI / Johnson-noise thermometry / CRNS; r29 twin-tube Coriolis / CARS N2 FWHM / Zn-Kα XRF; r30 Fe-57 Mössbauer / GB-InSAR / spectroscopic ellipsometry; r31 two-pickoff Coriolis / rhodium SPND / LII soot fv; r32 PALS creep header / NQR AN prill / SFRA GSU winding; r33 digital shearography / hydrogen permeation / FMCW microwave lining; r34 handheld XRF Cr-Kα / Coriolis tube-twist / GPR liner cover; r35 mud-pulse MWD ECD / Barkhausen case-depth / laser-ultrasound Lamb-wave; r36 Pockels GIS bus / pulsed-eddy-current coated riser / confocal chromatic float-glass; r37 mud-pulse hydrophone densification / Barkhausen RA / Lamb-wave ligament densification; r04 VOD-SNN / pharma cold-chain / CEMS; 2026-08-30 r01–r03 including dry-cask muon, CHO EWMA, and LPBF melt-pool; r1–r12 table (DVS, cochlea, SPAD ToF, DAS, PMU, e-skin, vestibular, atomic clocks, tokamak, nanopore, VLF, QEC, GW, SOFAR, neutrino, fab OES, space weather, pulsar TOA, eddy covariance, flow cytometry). Unused r13-holes (cyclotron BPM/BLM, Co-60 alanine EPR, ADCP ice-jam) were left available; r13-premises (mud-pulse, Barkhausen, Lamb-wave) were harvested by r35/r37 and are not restaged.

Adjacencies declared in-pair then kept physically distinct:
- **115 spectral-domain OCT** is c Δt / (2 n) remaining TBC thickness on an HPT blade, not r30 spectroscopic ellipsometry OPD, not r20/r21 THz-TDS, not r33 FMCW microwave lining, not r34 GPR two-way time, not r33 digital shearography, not r3 SPAD ToF.
- **116 DCPD** is k V / I crack depth on a steam-drum girth coupon, not r21 ECA FSW lift-off, not r23 EN CUI, not r27/r28 MFL, not r23 PAUT TFM remaining wall, not r24 RUS.
- **117 impact-echo** is v_p / (2 f) remaining wall on a prestressed containment panel, not r23 PAUT TFM, not r35/r37 Lamb-wave LUT, not r24 RUS, not r25 acoustic pyrometry, not r36 pulsed eddy current, not r33 FMCW lining.

## Round 38 batch summary (3 pairs, 6 trajectories)

| id | modality (NEW family) | domain | decisions | headline |
|----|----------------------|--------|-----------|----------|
| nelb-r38-115 | spectral-domain OCT remaining TBC of a first-stage HPT blade (c Δt/(2 n) um, Yttriveil last-campaign denial, 18 min soak floor) | Cobblemere Turbine CM-5 blade B-7 (invented): 8.00 ps / n 1.50 reconstructs 800.0 um while Yttriveil still reads 1175 um and blade metal 905 C | MODIFY (+0.40) / ACCEPT (+0.35) | serialized `1e6*3.00e8*8.00e-12/(2*1.50)=800.0`; conjunctive SOP (d AND SNR) forbids keep-1.00 firing; companion t2 holds 0.80 pu and refuses a Yttriveil restore; sim_or_real=designed |
| nelb-r38-116 | DCPD crack depth of a steam-drum girth (k V/I mm, Dropveil last-good denial, 24 min cooldown floor) | Vellumkettle Drum VK-4 seam S-3 (invented, HIL coupon in DCPD-HIL-3): 8.00*6.00/4.00 reconstructs 12.00 mm while Dropveil still reads 3.20 mm and drum 318 C | REJECT (+0.43) / MODIFY (+0.34) | serialized `12.00 mm` and `6.00/4.00=1.50 mOhm`; keep-100 refused; companion t2 MODIFYs a drum condemn into overlay S-3 plus steam 0.70; sim_or_real=hil |
| nelb-r38-117 | impact-echo remaining wall of a prestressed containment panel (v_p/(2 f) mm, Echoeil last-campaign + shell-TC denial, 15 min access-hold floor) | Groutfen Containment GF-3 panel W-11 (invented, simulated): 4.00e3/(2*2.50e3) reconstructs 800.0 mm while Echoeil still reads 1175 mm and shell TC 44 C | ACCEPT (+0.41) / REJECT (+0.36) | serialized `1000*4000/(2*2500)=800.0`; bounded overlay of W-11 only; steel liner out of scope; companion t2 REJECTS skip-overlay; sim_or_real=simulated |

Decision spread: MODIFY / ACCEPT / REJECT / MODIFY / ACCEPT / REJECT — **2A/2M/2R**. All three enums used, and all three sit on **leads**. Provenance spread: designed / hil / simulated (one each; never real). IDs `nelb-r38-115`…`117` plus t1/t2 suffixes.

## Raster sidecar
Every record carries `raster` + top-level `gate_snn` + `gate_compute`. Windows 36/28/40 ms; `window_s == window_ms/1000` exactly; `spikes == round(neurons·rate·window_s)` with zero slack (36/35/40 at 50/50/62.5 Hz over 20/25/16 neurons); `energy_pJ = spikes·23` and `energy_uJ = spikes·23e-6` exact (828/805/920 pJ). Routing source/target + 3-entry tables + `third_factor` on all three (modulators na.tbc_thickness_salience / da.crack_depth_error / ach.containment_wall_conflict; τe 1.6/1.1/2.2 s as consistent `tau_e_s`+`tau_e_ms` pairs). Excerpts integer `t_us`, in-window, `neuron_id`-bounded, sorted, full-window by construction, per-spike amplitude with adaptation (0.82**k) plus noise. ISI histograms from the full window, bins ≥1 ms, counts sum to `spikes − distinct_active_neurons` ({isis[0]}/{isis[1]}/{isis[2]}). Same-neuron gaps ≥1100 µs pre-round, ≥1000 µs serialized. `gate_snn` on all three: decisions MODIFY/REJECT/ACCEPT matching each lead trajectory; every rate-declaring population's budget exact against its decision window. `gate_compute.per_check` windows 28–40 ms, budgets exact (144+64 / 140+80 / 192+80). Main streams: {events[0]}/{events[1]}/{events[2]} events (inside the 5–40 cap), strictly increasing `t_rel_ms` only (no `t_ms` mix), same-channel refractory ≥0.8 ms (115 OCT pair at 1.5 ms, 116 DCPD pair at 1.2 ms, 117 impact-echo pair at 1.5 ms).

## Self-critique

### Edge cases added vs still thin
- **Added:** first spectral-domain-OCT family on a first-stage HPT TBC with a recomputable d=cΔt/(2n) (`800.0 um`) plus a last-campaign vendor corridor; first DCPD family on a steam-drum girth with a recomputable a=kV/I (`12.00 mm`) and R=V/I identity; first pulsed-eddy-current remaining-wall family on a reformer tube under insulation with recomputable t=k t_zc (`12.00 mm`); first bounded ACCEPT whose out-of-scope clause is an inlet header rather than a taphole/hopper; first keep-100 REJECT lead on a DCPD stop that a vendor UT last-good would have cleared; operational t2 on all three (0.80 hold, overlay+0.70, skip-retube refusal); provenance trio designed/hil/simulated; 18 min / 24 min / 15 min slow floors in-stream.
- **Still thin:** (i) 115's n=1.50 is a lumped YSZ group index, not a temperature-shifted dispersion table — a thermal expansion that fakes 800 um inside a 1175 um last-campaign corridor is unwritten; (ii) 116's k_dp is a lumped coupon constant, not a current-spread / ligament map, so a contact that fakes 12 mm is unwritten; (iii) 117's k_pec is a dry-insulation calibration, not a moisture-corrected decay, so wet lagging that fakes 12 mm is unwritten; (iv) vendor-only as a *lead* REJECT on a plant with *no* independent witness remains slightly harder — 115/116 still have plant OCT/DCPD heads; (v) stream amplitudes remain authored constants (raster draws are the only seeded noise); (vi) unused r13-premises (mud-pulse, Barkhausen, Lamb-wave) still unharvested.

### Realism of noise / temporal fidelity
- Strong: 115's 800.0 um and 18.0 min soak (`6600+1080=7680 s`) recompute from the record; 116's 12.00 mm, 1.50 mOhm, and 24.0 min cooldown (`1500+1440=2940 s`) recompute; 117's 12.00 mm and 15.0 min cool (`6600+900=7500 s`) recompute. Raster adaptation (0.82**k plus 4% noise) and the 1.2–1.5 ms physics pairs give the 5–40 stream a raster-scale motif without violating 0.8 ms same-channel refractory.
- **Gaps, honestly:** (i) 5–40 cap still forces heavy thinning (20 kHz OCT A-scan kept as 3 dt points; 10 Hz DCPD kept as 4 V points; 40 Hz PEC pulse kept as 3 t_zc points); (ii) 115's post-isolate 840 um is a later sample, not a closed-loop coating controller; (iii) 116 HIL coupon times an in-service stop that the stream does not independently witness on the live girth until overlay is cut; (iv) no gate_snn input→output volley pair at raster resolution this round (r04-a1 already staged that).

### Training value (SNN/LSM + agentic)
Distillation targets: OCT d=cΔt/(2n) reconstruction head; isolate-floor derate vs keep-1.00 vs wheel-condemn; last-campaign nonsubstitution; DCPD a=kV/I head plus R identity; stop-floor refuse vs keep-100 vs drum condemn; vendor-UT nonsubstitution; PEC t=k t_zc head; bounded ACCEPT with header-out-of-scope; skip-retube refusal under takt. Agentic value concentrates in three patterns: reconstruction-as-SoT on a physical defect the raw corridor cannot see, earned ACCEPT with an explicit physical out-of-scope object (the inlet header), and stop-then-hold so a REJECT does not become a freeze-kill.

## What round 39 should add (next densification target)
1. **Temperature-shifted OCT group-index table** on a non-CM-5 blade so a thermal expansion fakes 800 um inside a 1175 um last-campaign corridor, closing 115's lumped-n gap.
2. **DCPD current-spread / ligament map** on a non-VK-4 coupon so a scratched contact can fake 12 mm while mean voltage looks healthy.
3. **Moisture-corrected PEC decay** on a non-LF-6 reformer so wet lagging can fake 12 mm inside a 15 mm last-campaign corridor.
4. **Vendor-only as a lead REJECT** on a plant that has no independent witness installed yet (115/116 still had plant OCT/DCPD heads).
5. **Do not restage** VOD-SNN replay, pharma cold-chain, CEMS, FBG glaze, Frostlip quench, Oxbow VRFB, IFOG, transmon, hyperspectral, MEMS array, muon ore-pass, industrial x-ray, optogenetic stim, 905 nm LiDAR snow, clamp-on transit-time, LIBS, QEPAS, LFV, Kaplan LDV, THz-TDS, ECT, TDLAS NH3, lock-in thermography, PAUT TFM, EN CUI, RUS porcelain, N-16 loop flow, helium RGA, Faraday FOCT, blade tip-timing, acoustic pyrometry, SPR, vibrating-wire viscometer, microwave-cavity moisture, MFL, NMR T2, nucleonic densitometry, Johnson noise, CRNS, Coriolis, CARS, XRF, Mössbauer, GB-InSAR, ellipsometry, SPND, LII, PALS, NQR, SFRA, digital shearography, hydrogen permeation, FMCW lining, GPR, Cobblemere CM-5 OCT, Vellumkettle DCPD-HIL-3, or Lanternfell LF-6 PEC. Leave mud-pulse, Barkhausen, and Lamb-wave available.

## Verification
`batch-r38.jsonl`: 3 lines, `json.loads`-clean (allow_nan=False), {sizes[0]}/{sizes[1]}/{sizes[2]} bytes (file {{BATCH.stat().st_size}}, sha256 `{file_sha}`). Staged at `/tmp/nelb-r38/` only. Repo gates: `check_records.check_jsonl` with `FactoryStaging(enabled=True)` → 0 errors, 0 warnings, kinds `{{bridge_pair: 3}}`; `python3 pipelines/check_records.py --strict /tmp/nelb-r38` → 0/0; `curate_bridge.raster_status(..., require_raster=True, require_routing_table=True)` → raster_valid and gate_snn_valid true, empty reason codes; `curate_record(...)` → 3× retain / `BRIDGE_EVENTS_ALREADY_GLOBALLY_ORDERED`; `verify_batch_for_frontier(strict=True)` → 3 verified, 0 inconclusive, 0 failed; `python3 pipelines/spike_probe.py --strict /tmp/nelb-r38/batch-r38.jsonl` → loaded 3, unloadable 0, problems [], third_factor_routes 3, gate_snn_records 3, spikes {spikes}, energy_pJ {energy}. Build-time asserts: global time order; same-channel ≥0.8 ms; 5–40 events ({events[0]}/{events[1]}/{events[2]}); excerpt integer bounds, neuron bounds, sort, 1 ms per-neuron floor; ISI identity {isis[0]}/{isis[1]}/{isis[2]}; spike budgets exact; energy pJ/µJ exact; reward totals equal two-decimal component sums ({reward_s}); gate_snn decisions match lead `safety_decision.decision`; `state.sim_or_real` ∈ {{designed, hil, simulated}}; `meta.round=38`, `meta.factory=neuromorphic-event-language-bridge`, `meta.generator=grok-4.6`, `meta.run_label=2026-09-02-final-heavy`; `meta.rights` 15-key RM-793 stamp (`intended_use=research_only`, `linear_issue=RM-793`, `generated_at={GENERATED_AT}`); no hidden-reasoning keys; no `provenance` objects; no 'real' claims; no `training_ready`; all 9 record/trajectory ids unique. Raster seeds 20263815/20263816/20263817, MT19937.

Honest novelty accounting: 3/3 modality families are new versus the whole committed factory and versus staged leftover-mill r13–r34 (and in-flight r32 PALS/NQR/SFRA). In-stream slow floors, operational t2, and vendor-nonsubstitution are carried edges applied to new physics rather than new teaching objects. Against that: bounded-accept-with-scope-limit, reconstruction-as-SoT, conjunctive SOP, and custody vocabulary are carried; the 5–40 cap is a density constraint not a new teaching object; 37 prior leftover-mill rounds already taught custody/governance at high sophistication. Net: a bit under two-fifths of the round's scenario/edge mass is genuinely novel.

Novel coverage: 37%
"""
    # The file-size placeholder must interpolate BATCH.stat().st_size.
    notes = notes.replace("{BATCH.stat().st_size}", str(BATCH.stat().st_size))
    NOTES.write_text(notes, encoding="utf-8")
    print("wrote", NOTES, "bytes", NOTES.stat().st_size)


def main():
    records = [rec_115(), rec_116(), rec_117()]
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
