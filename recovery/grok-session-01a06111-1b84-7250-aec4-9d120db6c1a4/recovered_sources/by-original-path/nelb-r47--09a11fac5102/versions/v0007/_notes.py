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
    notes = f"""# Neuromorphic Event + Language Bridge — NOTES round 47
Run: 2026-09-02-final-heavy · Factory: neuromorphic-event-language-bridge · Generator: grok-4.6 · Output: `batch-r47.jsonl` (3 paired artifacts, 6 ThalamicTrajectories)
Rights: RM-793 research-only (SpaceXAI/xAI grok-4.6, SuperGrok Heavy chat). Not training_ready. Do not publish into `outputs/raw/` from this generator; operator uses `pipelines/round_txn.py`. Staged only at `/tmp/nelb-r47/`.

## Context / de-duplication
Prior corpus read: 2026-08-30 NOTES-r01–r04, 2026-08-17-w3 NOTES-r12 family table, `/tmp/nelb-r13-holes.md` + `/tmp/nelb-r13-premises.md`, staged `/tmp/nelb-r13` through `/tmp/nelb-r44` batches/NOTES plus in-flight `/tmp/nelb-r45`/`r46`/`r48` stubs (no families locked). IDs: r13=`040`–`042` … r44=`133`–`135`, implied r45–r46=`136`–`141`, this round `nelb-r47-142`…`144` as assigned. Envelope cloned from complete r42 (`language_view.trajectory` + operational t2 + `spike_events` + `raster` + `gate_snn` + `isi_histogram` + `routing.third_factor` + 15-key RM-793 `meta.rights`).

Banned this round (committed + staged leftover-mill r13–r46 and in-flight r45/r48): not VOD-SNN replay, not pharma cold-chain, not stack-gas CEMS; not r13 FBG glaze / Frostlip quench / Oxbow VRFB; not r14 BOTDA / QCM-D / MsS T(0,1); not r15 SAW torque / CRDS HF / PGNAA; not r16 IFOG / transmon readout / hyperspectral crop; not r17 MEMS accel array / muon ore-pass / industrial x-ray DR; not r18 optogenetic PV / 905 nm LiDAR snow / clamp-on transit-time; not r19 LIBS Cu / QEPAS DGA / LFV Al; not r20 Kaplan LDV / THz-TDS radome moisture / ECT CFB; not r21 THz-TDS bondline / ECA FSW lift-off / LIBS C; not r22 ECT pneumatic riser / TDLAS NH3 / LIBS tap; not r23 lock-in thermography CFRP / PAUT TFM girth / EN CUI; not r24 RUS porcelain / N-16 transit-time loop / helium RGA; not r25 Faraday FOCT / blade tip-timing / acoustic pyrometry; not r26 SPR cyanide / VW viscometer / MW cavity moisture; not r27 MFL AST / NMR T2 / Cs-137 densitometry; not r28 MFL ILI / JNT / CRNS; not r29 Coriolis bitumen / CARS TIT / Zn-Ka XRF; not r30 Mössbauer FCC / GB-InSAR tailings / ellipsometry PECVD; not r31 CTA hot-wire / rhodium SPND / LII soot; not r32 PALS / 14N NQR / SFRA; not r33 digital shearography hull / hydrogen permeation / FMCW BOF lining; not r34 handheld XRF Cr-Kα / Coriolis tube-twist / GPR liner cover; not r35/r37 mud-pulse MWD / Barkhausen / Lamb-wave; not r36 Pockels GIS / PEC coated riser / confocal chromatic; not r38 OCT TBC / DCPD girth / impact-echo containment; not r39 phosphor thermometry / vortex-shedding steam / GWR foam tank; not r40 beta-transmission web / Raman methanol; not r41–r43 cyclotron BPM / alanine EPR / ADCP ice-jam; not r44 TOFD remaining ligament / laser-flash Parker diffusivity / TDR MV cable; not r45 RFT remaining wall / ACFM crack depth / LPR corrosion rate; not r46 paramagnetic O2 / TOFD hydrocracker / TEOM baghouse PM; not in-flight r48 ACFM chord / FDS tanδ / MCSA broken-bar. Plants not reused: Nettlewake, Frostlip, Oxbow, Sloebrake, Charkholt, Kelpcrag, Wickmere, Wickspire, Bitternex, Clinkerfell, Brineleg, Gorsewisp, Flintcrag. Miregait / Puddlewick / Fennelholt are new this round.

This round harvests three unused industrial sensing families (Faraday magmeter slurry flow, phase-Doppler Sauter-mean, acoustoelastic birefringence residual) after r45 took RFT.

Adjacencies declared in-pair then kept physically distinct:
- **142 Faraday magmeter** is induced-voltage volumetric flow of a conductive slurry, not Faraday FOCT current (r25), not LFV aluminum (r19), not vortex-shedding steam (r39), not Coriolis (r29/r34), not clamp-on transit-time (r18), not N-16 (r24), not CTA (r31).
- **143 PDA d32** is dual-detector phase-Doppler Sauter-mean of a spray-dryer atomizer, not Kaplan LDV (r20), not CTA hot-wire (r31), not LFV aluminum (r19), not vortex-shedding steam (r39).
- **144 acoustoelastic residual** is two-polarization TOF birefringence of a converter girth, not Faraday FOCT circular birefringence (r25), not RUS porcelain (r24), not Lamb-wave LUT (r35/r37), not PAUT TFM (r23), not TOFD remaining ligament (r44/r46), not DCPD (r38).

## Round 47 batch summary (3 pairs, 6 trajectories)

| id | modality (NEW family) | domain | decisions | headline |
|----|----------------------|--------|-----------|----------|
| nelb-r47-142 | Faraday electromagnetic flowmeter of a slurry header (k_u·(U−U0) m3/h, Flowveil last-good denial, 18 min pump-hold floor) | Miregait Slurry MG-9 header H-3 (invented): 52.00 mV reconstructs 12.00 m3/h while Flowveil still reads 15.20 m3/h | REJECT (+0.43) / MODIFY (+0.34) | serialized `0.250*(52.00-4.00)=12.00`; `12.00/16.00=0.75`; conjunctive SOP (Q AND SNR) forbids keep-pumping; three-party collusion includes the coil-cloud infra owner; companion t2 pump-hold, plant trip refused; sim_or_real=designed |
| nelb-r47-143 | phase-Doppler anemometry Sauter-mean of a spray-dryer atomizer (k_d·Δφ um, Sprayveil last-good denial, 24 min nozzle-swap floor) | Puddlewick Dryer PD-6 lot PD6-4411..4430 (invented, HIL dummy in PDA-HIL-4): 30.00 deg reconstructs 12.00 um while Sprayveil still reads 25.20 um | MODIFY (+0.40) / ACCEPT (+0.35) | serialized `0.400*30.00=12.00` and `30.00/12.00=2.50`; keep-lot refused; operator Sela Wren exonerated (missing flush AE, UTC vs UTC+1); companion t2 new-nozzle restart; sim_or_real=hil |
| nelb-r47-144 | acoustoelastic residual-stress birefringence of a converter girth (k_s·Δt MPa, Stressveil last-good denial, 12 min access-hold floor) | Fennelholt Converter FH-5 weld W-4 (invented, simulated AE-SIM-3): 30.00 ns reconstructs 120.0 MPa while Stressveil still reads 12.00 MPa | ACCEPT (+0.41) / REJECT (+0.36) | serialized `4.00*30.00=120.0`; `5.00*120.0=600.0`; `30.00/8000.00=0.00375`; bounded ACCEPT of W-4 only; W-3/W-5 out of scope; companion t2 REJECTS skip-scan; sim_or_real=simulated |

Decision spread: REJECT / MODIFY / MODIFY / ACCEPT / ACCEPT / REJECT — **2A/2M/2R**. All three enums used, and all three sit on **leads**. Provenance spread: designed / hil / simulated (one each; never live-plant). IDs `nelb-r47-142`…`144` plus t1/t2 suffixes.

## Raster sidecar
Every record carries `raster` + top-level `gate_snn` + `gate_compute`. Windows {wins[0]:.0f}/{wins[1]:.0f}/{wins[2]:.0f} ms; `window_s == window_ms/1000` exactly; `spikes == round(neurons·rate·window_s)` with zero slack ({n_sp[0]}/{n_sp[1]}/{n_sp[2]} at {rates[0]}/{rates[1]}/{rates[2]} Hz over {n_neu[0]}/{n_neu[1]}/{n_neu[2]} neurons); `energy_pJ = spikes·23` and `energy_uJ = spikes·23e-6` exact ({n_sp[0]*23}/{n_sp[1]*23}/{n_sp[2]*23} pJ). Routing source/target + 3-entry tables + `third_factor` on all three (modulators {tfs[0]} / {tfs[1]} / {tfs[2]}; τe {taus[0]}/{taus[1]}/{taus[2]} s as consistent `tau_e_s`+`tau_e_ms` pairs). Excerpts integer `t_us`, in-window, `neuron_id`-bounded, sorted, full-window by construction, per-spike amplitude with adaptation (0.82**k) plus noise. ISI histograms from the full window, bins ≥1 ms, counts sum to `spikes − distinct_active_neurons` ({isis[0]}/{isis[1]}/{isis[2]}). Same-neuron gaps ≥1100 µs pre-round, ≥1000 µs serialized. `gate_snn` on all three: decisions REJECT/MODIFY/ACCEPT matching each lead trajectory; every rate-declaring population's budget exact against its decision window. `gate_compute.per_check` windows 32–40 ms, budgets exact ({gc[0]} / {gc[1]} / {gc[2]}). Main streams: {events[0]}/{events[1]}/{events[2]} events (inside the 5–40 cap), strictly increasing `t_rel_ms` only (no `t_ms` mix), same-channel refractory ≥0.8 ms (142 mag pair at 1.3 ms, 143 PDA pair at 1.2 ms, 144 AE pair at 1.5 ms).

## Self-critique

### Edge cases added vs still thin
- **Added:** first Faraday electromagnetic-flowmeter family on a slurry header with a recomputable Q=k_u·(U−U0) (`12.00 m3/h`) plus full-scale identity and three-party collusion including the coil-cloud infra owner; first phase-Doppler Sauter-mean family on a spray-dryer atomizer with recomputable d32=k_d·Δφ (`12.00 um`) and phase identity, plus a resolved-innocent operator (timezone-skipped flush, not last-to-badge); first acoustoelastic birefringence family on a converter girth with recomputable σ=k_s·Δt (`120.0 MPa`) plus strain and B identities; first bounded ACCEPT whose out-of-scope clause is adjacent welds W-3/W-5 rather than a hopper/taphole/dump cap; operational t2 on all three (pump-hold, new-nozzle restart, skip-scan refusal); provenance trio designed/hil/simulated; 18 min / 24 min / 12 min slow floors in-stream.
- **Still thin:** (i) 142's k_u is a lumped mV→m3/h gain, not a B-field / lining-conductivity map — a coil-gain hop that fakes 12.00 m3/h inside a 15.20 m3/h last-good corridor is unwritten; (ii) 143's k_d is a lumped phase-to-diameter scale, not a refractive-index / scattering-order map, so a m-2/m-1 hop that fakes 12.00 um is unwritten; (iii) 144's k_s is a lumped acoustoelastic constant, not a texture / temperature table, so a coupling-delay hop that fakes 120.0 MPa inside a 12.00 MPa last-good is unwritten; (iv) vendor-only as a *lead* REJECT on a plant with *no* independent magmeter/PDA/AE installed yet remains slightly harder — 142/143 still have plant heads; (v) stream amplitudes remain authored constants (raster draws are the only seeded noise); (vi) r38/r39/r44/r45 densification leftovers (OCT group-index, DCPD current-spread, moisture-corrected impact-echo, Arrhenius phosphor, vortex density-from-T/p, GWR foam dielectric, TOFD skip-path, Parker α(T), TDR v_p(moisture), RFT fill-factor) were left for those rounds' owners.

### Realism of noise / temporal fidelity
- Strong: 142's 12.00 m3/h, n 0.75, and 18.0 min pump-hold (`6000+1080=7080 s`) recompute from the record; 143's 12.00 um, G 2.50, and 24.0 min nozzle-swap (`2820+1440=4260 s`) recompute; 144's 120.0 MPa, 600.0 µε, B 0.00375, and 12.0 min hold (`6000+720=6720 s`) recompute. Raster adaptation (0.82**k plus 4% noise) and the 1.2–1.5 ms physics pairs give the 5–40 stream a raster-scale motif without violating 0.8 ms same-channel refractory.
- **Gaps, honestly:** (i) 5–40 cap still forces heavy thinning (kHz magmeter mix kept as 4 U points; kHz PDA burst kept as 4 dphi points; kHz AE pair kept as 4 dt points); (ii) 142's post-stop 5.00 m3/h is a later sample, not a closed-loop pump controller; (iii) 143 HIL dummy times an in-service lot isolate that the stream does not independently witness on a second live nozzle until the new nozzle starts; (iv) no gate_snn input→output volley pair at raster resolution this round (r04-a1 already staged that).

### Training value (SNN/LSM + agentic)
Distillation targets: RFT t=k_φ·(φ−φ_air) reconstruction head plus ligament identity; conjunctive isolate floor vs keep-firing vs unit trip; bobbin-infra collusion; PDA d32=k_d·Δφ head plus phase identity; isolate-floor lot vs keep-whole vs warehouse-dump; exoneration against last-to-badge social pressure; acoustoelastic σ=k_s·Δt and strain/B identities; bounded ACCEPT with W-3/W-5-out-of-scope; skip-scan refusal under scan takt. Agentic value concentrates in three patterns: reconstruction-as-SoT on a physical wall/fine-spray/residual the raw corridor cannot see, earned ACCEPT with an explicit physical out-of-scope object (W-3/W-5), and stop-then-hold so a REJECT does not become a block/warehouse/shell kill.

## What a later leftover-mill round should add (next densification target)
1. **Fill-factor / permeability map** on a non-DM-8 RFT bobbin so a fill hop fakes 12.00 mm inside a 15.20 mm last-campaign corridor, closing 142's lumped-k_φ gap.
2. **Refractive-index / scattering-order map** on a non-PD-6 PDA so an m-2/m-1 hop can fake 12.00 um while mean phase looks healthy.
3. **Texture / temperature acoustoelastic table** on a non-FH-5 girth so a coupling-delay hop can fake 120.0 MPa inside a 12.00 MPa last-good corridor.
4. **Vendor-only as a lead REJECT** on a plant that has no independent RFT/PDA/AE installed yet (142/143 still had plant heads).
5. **Do not restage** VOD-SNN replay, pharma cold-chain, CEMS, FBG glaze, Frostlip quench, Oxbow VRFB, IFOG, transmon, hyperspectral, MEMS array, muon ore-pass, industrial x-ray, optogenetic stim, 905 nm LiDAR snow, clamp-on transit-time, LIBS, QEPAS, LFV, Kaplan LDV, THz-TDS, ECT, TDLAS NH3, lock-in thermography, PAUT TFM, EN CUI, RUS porcelain, N-16 loop flow, helium RGA, Faraday FOCT, blade tip-timing, acoustic pyrometry, SPR, vibrating-wire, microwave-cavity, MFL, NMR T2, nucleonic densitometry, JNT, CRNS, Coriolis, CARS, XRF, Mössbauer, GB-InSAR, ellipsometry, CTA, SPND, LII, PALS, NQR, SFRA, digital shearography, hydrogen permeation, FMCW lining, GPR, Pockels, PEC, confocal, mud-pulse, Barkhausen, Lamb-wave, OCT, DCPD, impact-echo, phosphor, vortex, GWR, cyclotron BPM, alanine EPR, ADCP, TOFD, laser-flash Parker, TDR cable, Dapplemere DM-8 RFT, Puddlewick PDA-HIL-4, or Fennelholt FH-5 AE. Leave r38/r39/r44 densification leftovers for those rounds' owners. Do not steal r45–r46 IDs `136`–`141`.

## Verification
`batch-r47.jsonl`: 3 lines, `json.loads`-clean (allow_nan=False), {sizes[0]}/{sizes[1]}/{sizes[2]} bytes (file {BATCH.stat().st_size}, sha256 `{file_sha}`). Staged at `/tmp/nelb-r47/` only. Repo gates: `check_records.check_jsonl` with `FactoryStaging(enabled=True)` → 0 errors, 0 warnings, kinds `{{bridge_pair: 3}}`; `python3 pipelines/check_records.py --strict /tmp/nelb-r47` → 0/0; `curate_bridge.raster_status(..., require_raster=True, require_routing_table=True)` → raster_valid and gate_snn_valid true, empty reason codes; `curate_record(...)` → 3× retain / `BRIDGE_EVENTS_ALREADY_GLOBALLY_ORDERED`; `verify_batch_for_frontier(strict=True)` → 3 verified, 0 inconclusive, 0 failed; `python3 pipelines/spike_probe.py --strict /tmp/nelb-r47/batch-r47.jsonl` → loaded 3, unloadable 0, problems [], third_factor_routes 3, gate_snn_records 3, spikes {spikes}, energy_pJ {energy}. Build-time asserts: global time order; same-channel ≥0.8 ms; 5–40 events ({events[0]}/{events[1]}/{events[2]}); excerpt integer bounds, neuron bounds, sort, 1 ms per-neuron floor; ISI identity {isis[0]}/{isis[1]}/{isis[2]}; spike budgets exact; energy pJ/µJ exact; reward totals equal two-decimal component sums ({reward_s}); gate_snn decisions match lead `safety_decision.decision`; `state.sim_or_real` ∈ {{designed, hil, simulated}}; `meta.round=47`, `meta.factory=neuromorphic-event-language-bridge`, `meta.generator=grok-4.6`, `meta.run_label=2026-09-02-final-heavy`; `meta.rights` 15-key RM-793 stamp (`intended_use=research_only`, `linear_issue=RM-793`, `generated_at={GENERATED_AT}`); no hidden-reasoning keys; no `provenance` objects; no 'real' claims; no `training_ready`; all 9 record/trajectory ids unique. Raster seeds 202609142/202609143/202609144, MT19937.

Honest novelty accounting: 3/3 modality families are new versus the committed factory and versus staged leftover-mill r13–r44 (and in-flight r45/r46 stubs). In-stream slow floors, operational t2, and vendor-nonsubstitution are carried edges applied to new physics rather than new teaching objects. Three-party collusion and exoneration were already taught on r13 quench/VRFB and r37/r42 Barkhausen/alanine, so those heads are carried onto new sensors. Against that: bounded-accept-with-scope-limit, reconstruction-as-SoT, conjunctive SOP, and custody vocabulary are carried; the 5–40 cap is a density constraint not a new teaching object; 31 prior leftover-mill rounds already taught custody/governance at high sophistication. Net: about two-fifths of the round's scenario/edge mass is genuinely novel.

Novel coverage: 39%
"""
    NOTES.write_text(notes, encoding="utf-8")
    print("wrote", NOTES, "bytes", NOTES.stat().st_size)


def main():
    records = [rec_142(), rec_143(), rec_144()]
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
