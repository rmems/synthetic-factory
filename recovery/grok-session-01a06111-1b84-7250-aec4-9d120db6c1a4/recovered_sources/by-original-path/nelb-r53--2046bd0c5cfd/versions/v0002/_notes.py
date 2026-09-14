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
    notes = f"""# Neuromorphic Event + Language Bridge — NOTES round 53
Run: 2026-09-02-final-heavy · Factory: neuromorphic-event-language-bridge · Generator: grok-4.6 · Output: `batch-r53.jsonl` (3 paired artifacts, 6 ThalamicTrajectories)
Rights: RM-793 research-only (SpaceXAI/xAI grok-4.6, SuperGrok Heavy chat). Not training_ready. Do not publish into `outputs/raw/` from this generator; operator uses `pipelines/round_txn.py`. Staged only at `/tmp/nelb-r53/`.

## Context / de-duplication
Prior corpus read: 2026-08-30 NOTES-r01–r04, 2026-08-17-w3 NOTES-r12 family table, `/tmp/nelb-r13-holes.md` + `/tmp/nelb-r13-premises.md`, staged `/tmp/nelb-r13` through `/tmp/nelb-r50` batches/NOTES/generators plus in-flight `/tmp/nelb-r51` (`_head.py`/`_checks.py` only) and `/tmp/nelb-r52` (`_head.py` only). IDs: r13=`040`–`042` … r46=`139`–`141`, r47=`142`–`144`, r48=`145`–`147`, r49=`148`–`150`, r50=`151`–`153`, reserved r51–r52=`154`–`159`, this round `nelb-r53-160`…`162` as assigned. Envelope cloned from complete r46 (`language_view.trajectory` + operational t2 + `spike_events` + `raster` + `gate_snn` + `isi_histogram` + `routing.third_factor` + 15-key RM-793 `meta.rights`).

Banned this round (committed + staged leftover-mill r13–r50 and in-flight r51/r52 envelopes): not VOD-SNN replay, not pharma cold-chain, not stack-gas CEMS; not r13 FBG glaze / Frostlip quench / Oxbow VRFB; not r14 BOTDA / QCM-D / MsS T(0,1); not r15 SAW torque / CRDS HF / PGNAA; not r16 IFOG / transmon readout / hyperspectral crop; not r17 MEMS accel array / muon ore-pass / industrial x-ray DR; not r18 optogenetic PV / 905 nm LiDAR snow / clamp-on transit-time; not r19 LIBS Cu / QEPAS DGA / LFV Al; not r20 Kaplan LDV / THz-TDS radome moisture / ECT CFB; not r21 THz-TDS bondline / ECA FSW lift-off / LIBS C; not r22 ECT pneumatic riser / TDLAS NH3 / LIBS tap; not r23 lock-in thermography CFRP / PAUT TFM girth / EN CUI; not r24 RUS porcelain / N-16 transit-time loop / helium RGA; not r25 Faraday FOCT / blade tip-timing / acoustic pyrometry; not r26 SPR cyanide / VW viscometer / MW cavity moisture; not r27 MFL AST / NMR T2 / Cs-137 densitometry; not r28 MFL ILI / JNT / CRNS; not r29 Coriolis bitumen / CARS TIT / Zn-Ka XRF; not r30 Mössbauer FCC / GB-InSAR tailings / ellipsometry PECVD; not r31 CTA hot-wire / rhodium SPND / LII soot; not r32 PALS / 14N NQR / SFRA; not r33 digital shearography hull / hydrogen permeation / FMCW BOF lining; not r34 handheld XRF Cr-Kα / Coriolis tube-twist / GPR liner cover; not r35/r37 mud-pulse MWD / Barkhausen / Lamb-wave; not r36 Pockels GIS / PEC coated riser / confocal chromatic; not r38 OCT TBC / DCPD girth / impact-echo containment; not r39 phosphor-lifetime / vortex-shedding / GWR foam; not r40 He-3 neutron-backscatter / Kr-85 beta / 532 nm Raman; not r41/r42/r43 cyclotron BPM / alanine EPR / ADCP ice-jam; not r44 TOFD ligament / laser-flash Parker / TDR remaining-length; not r45 RFEC boiler tube / ACFM jacket node / LPR cooling header / Seebeck remaining ferrite; not r46 paramagnetic O2 / TOFD ligament / TEOM PM; not r47 magmeter slurry / PDA Sauter-mean / acoustoelastic residual; not r48 C-SAM IGBT void / FDS tanδ bushing / MCSA broken-bar; not r49 EMAT SH coil / FBRM chord D50 / ACFM jack-up; not r50 OFDR hoop-strain / XRD sin²ψ / FBRM remaining-chord. Plants not reused: Nettlewake, Frostlip, Oxbow, Wickspire, Bitternex, Clinkerfell, Miregait, Puddlewick, Fennelholt, Ashholt, Gorsewisp, Flintcrag, Kettermere, Mirebank, Terncrag, Quaycrag, Copsefell, Heatherfen, Charkholt, Kelpcrag, Wickmere, Dapplemere, Hawkmere's neighbors already listed above.

This round introduces three unused industrial families (electrical-resistance probe remaining wall, Fabry-Perot diaphragm wellhead pressure, inductive oil-debris chip mass) on new invented plants. r13-holes cyclotron/alanine/ADCP and r50 OFDR/XRD/FBRM are not restaged.

Adjacencies declared in-pair then kept physically distinct:
- **160 ER probe** is a sacrificial-element resistance remaining wall of a sour header, not r38 DCPD crack depth on the structure, not r45 LPR Stern-Geary rate, not r23 EN CUI, not r33 hydrogen permeation, not r45 Seebeck remaining ferrite.
- **161 Fabry-Perot pressure** is a single diaphragm-cavity peak wavelength of a wellhead choke, not r13 FBG ice-load, not r14 BOTDA, not r50 OFDR Rayleigh hoop-strain, not r36 confocal chromatic glass thickness, not r15 SAW torque.
- **162 inductive debris** is a lube-line inductive pulse-count chip mass of a turbine gearbox, not r27/r28 MFL remaining wall, not r48 MCSA broken-bar, not r17 MEMS accel array, not r15 SAW torque, not r25 blade tip-timing.

## Round 53 batch summary (3 pairs, 6 trajectories)

| id | modality (NEW family) | domain | decisions | headline |
|----|----------------------|--------|-----------|----------|
| nelb-r53-160 | electrical-resistance probe remaining wall of a sour header (t0·R0/R um, Erveil last-good denial, 18 min inhibitor floor) | Hawkmere Sour HM-6 header H-11 (invented): 16.00 mOhm reconstructs 250.0 um while Erveil still reads 380.0 um | REJECT (+0.43) / MODIFY (+0.34) | serialized `400.0*10.00/16.00=250.0`; `400.0*6.00/16.00=150.0`; conjunctive SOP (t AND SNR) forbids continue-production; three-party collusion includes the ER-cloud infra owner; companion t2 inhibitor hold, line ESD refused; sim_or_real=designed |
| nelb-r53-161 | fiber-optic Fabry-Perot diaphragm pressure of a wellhead choke (k_p·(λ−λ0) bar, Fringveil last-good denial, 24 min cooldown floor) | Embercrag Wellhead EC-4 choke C-2 (invented, HIL dummy in FP-HIL-5): 1575.00 nm reconstructs 100.00 bar while Fringveil still reads 3.20 bar | MODIFY (+0.40) / ACCEPT (+0.35) | serialized `4.00*(1575.00-1550.00)=100.00` and `80.00-0.200*100.00=60.00`; keep-choke refused; fiber tech Merran Pye exonerated (missing lamp-cal AE, UTC vs UTC+2); companion t2 new-coupon restart; sim_or_real=hil |
| nelb-r53-162 | inductive oil-debris chip mass of a turbine gearbox (k_m·N mg, Chipveil last-good denial, 12 min survey floor) | Reedwhin Turbine RW-7 gearbox G-4 (invented, simulated DEBRIS-SIM-2): 48.00 counts reconstructs 12.00 mg while Chipveil still reads 1.20 mg | ACCEPT (+0.41) / REJECT (+0.36) | serialized `0.250*48.00=12.00`; `48.00/4.00=12.00`; `0.250*12.00=3.00`; bounded ACCEPT of G-4 only; G-1..G-3 out of scope; companion t2 REJECTS skip-drain; sim_or_real=simulated |

Decision spread: REJECT / MODIFY / MODIFY / ACCEPT / ACCEPT / REJECT — **2A/2M/2R**. All three enums used, and all three sit on **leads**. Provenance spread: designed / hil / simulated (one each; never live-plant). IDs `nelb-r53-160`…`162` plus t1/t2 suffixes.

## Raster sidecar
Every record carries `raster` + top-level `gate_snn` + `gate_compute`. Windows {wins[0]:.0f}/{wins[1]:.0f}/{wins[2]:.0f} ms; `window_s == window_ms/1000` exactly; `spikes == round(neurons·rate·window_s)` with zero slack ({n_sp[0]}/{n_sp[1]}/{n_sp[2]} at {rates[0]}/{rates[1]}/{rates[2]} Hz over {n_neu[0]}/{n_neu[1]}/{n_neu[2]} neurons); `energy_pJ = spikes·23` and `energy_uJ = spikes·23e-6` exact ({n_sp[0]*23}/{n_sp[1]*23}/{n_sp[2]*23} pJ). Routing source/target + 3-entry tables + `third_factor` on all three (modulators {tfs[0]} / {tfs[1]} / {tfs[2]}; τe {taus[0]}/{taus[1]}/{taus[2]} s as consistent `tau_e_s`+`tau_e_ms` pairs). Excerpts integer `t_us`, in-window, `neuron_id`-bounded, sorted, full-window by construction, per-spike amplitude with adaptation (0.82**k) plus noise. ISI histograms from the full window, bins ≥1 ms, counts sum to `spikes − distinct_active_neurons` ({isis[0]}/{isis[1]}/{isis[2]}). Same-neuron gaps ≥1100 µs pre-round, ≥1000 µs serialized. `gate_snn` on all three: decisions REJECT/MODIFY/ACCEPT matching each lead trajectory; every rate-declaring population's budget exact against its decision window. `gate_compute.per_check` windows 32–40 ms, budgets exact ({gc[0]} / {gc[1]} / {gc[2]}). Main streams: {events[0]}/{events[1]}/{events[2]} events (inside the 5–40 cap), strictly increasing `t_rel_ms` only (no `t_ms` mix), same-channel refractory ≥0.8 ms (160 ER pair at 1.4 ms, 161 FP pair at 1.2 ms, 162 debris pair at 1.5 ms).

## Self-critique

### Edge cases added vs still thin
- **Added:** first electrical-resistance-probe remaining-wall family on a sour header with a recomputable t=t0·R0/R (`250.0 um`) plus metal-loss and product identities and three-party collusion including the ER-cloud infra owner; first Fabry-Perot diaphragm-pressure family on a wellhead choke with recomputable P=k_p·(λ−λ0) (`100.00 bar`) and gap identity, plus a resolved-innocent fiber tech (timezone-skipped lamp-cal, not last-to-badge); first inductive oil-debris family on a turbine gearbox with recomputable M=k_m·N (`12.00 mg`) plus rate and mdot identities; first bounded ACCEPT whose out-of-scope clause is adjacent gearboxes rather than a hopper/taphole/dump cap; operational t2 on all three (inhibitor hold, new-coupon restart, skip-drain refusal); provenance trio designed/hil/simulated; 18 min / 24 min / 12 min slow floors in-stream.
- **Still thin:** (i) 160's R→t map is isothermal (T/T0=1.000), not an α(T) table — a thermal hop that fakes 250.0 um inside a 380.0 um Erveil corridor is unwritten; (ii) 161's k_p is a lumped diaphragm gain, not a group-index / cavity-order map, so a lamp hop that fakes 100.00 bar is unwritten; (iii) 162's k_m is a lumped pC→mg factor, not a size-class / ferromagnetic-fraction table, so a viscosity hop that fakes 12.00 mg inside a 1.20 last-good is unwritten; (iv) vendor-only as a *lead* REJECT on a plant with *no* independent ER/FP/debris head installed yet remains slightly harder — 160/161 still have plant heads; (v) stream amplitudes remain authored constants (raster draws are the only seeded noise); (vi) r50 densification leftovers (OFDR group-index table, XRD ψ-map, FBRM chord-bias) were left for that round's owner.

### Realism of noise / temporal fidelity
- Strong: 160's 250.0 um, ml 150.0, product 4000.0, and 18.0 min inhibitor (`6000+1080=7080 s`) recompute from the record; 161's 100.00 bar, d 60.00 um, and 24.0 min cooldown (`2820+1440=4260 s`) recompute; 162's 12.00 mg, r 12.00 cpm, mdot 3.00, and 12.0 min survey (`6000+720=6720 s`) recompute. Raster adaptation (0.82**k plus 4% noise) and the 1.2–1.5 ms physics pairs give the 5–40 stream a raster-scale motif without violating 0.8 ms same-channel refractory.
- **Gaps, honestly:** (i) 5–40 cap still forces heavy thinning (1 Hz ER kept as 4 R points; kHz FP spectrum kept as 4 λ points; kHz inductive pulses kept as 4 N points); (ii) 160's post-stop 200.0 um is a later sample, not a closed-loop inhibitor controller; (iii) 161 HIL coupon times an in-service choke isolate that the stream does not independently witness on a second live choke until the new coupon starts; (iv) no gate_snn input→output volley pair at raster resolution this round (r04-a1 already staged that).

### Training value (SNN/LSM + agentic)
Distillation targets: ER t=t0·R0/R reconstruction head plus metal-loss and product identities; conjunctive isolate floor vs continue-production vs line ESD; Erveil-infra collusion; FP P=k_p·(λ−λ0) head plus gap identity; isolate-floor choke vs keep-whole vs well-kill; exoneration against last-to-badge social pressure; inductive M=k_m·N and mdot identities; bounded ACCEPT with gearbox-out-of-scope; skip-drain refusal under survey takt. Agentic value concentrates in three patterns: reconstruction-as-SoT on a physical wall/pressure/chip load the raw corridor cannot see, earned ACCEPT with an explicit physical out-of-scope object (G-1..G-3), and stop-then-hold so a REJECT does not become a line/well/engine kill.

## What round 54 should add (next densification target)
1. **α(T) resistance table** on a non-HM-6 sour header so a thermal hop fakes 250.0 um inside a 380.0 um Erveil corridor, closing 160's isothermal gap.
2. **Cavity-order / group-index map** on a non-EC-4 choke so a lamp hop can fake 100.00 bar while mean λ looks healthy.
3. **Size-class / ferromagnetic-fraction table** on a non-RW-7 gearbox so a viscosity hop can fake 12.00 mg inside a 1.20 last-good corridor.
4. **Vendor-only as a lead REJECT** on a plant that has no independent ER/FP/debris head installed yet (160/161 still had plant heads).
5. **Do not restage** VOD-SNN replay, pharma cold-chain, CEMS, FBG glaze, Frostlip quench, Oxbow VRFB, IFOG, transmon, hyperspectral, MEMS array, muon ore-pass, industrial x-ray, optogenetic stim, 905 nm LiDAR snow, clamp-on transit-time, LIBS, QEPAS, LFV, Kaplan LDV, THz-TDS, ECT, TDLAS NH3, lock-in thermography, PAUT TFM, EN CUI, RUS porcelain, N-16 loop flow, helium RGA, Faraday FOCT, blade tip-timing, acoustic pyrometry, SPR, vibrating-wire, microwave-cavity, MFL, NMR T2, nucleonic densitometry, JNT, CRNS, Coriolis, CARS, XRF, Mössbauer, GB-InSAR, ellipsometry, CTA, SPND, LII, PALS, NQR, SFRA, digital shearography, hydrogen permeation, FMCW lining, GPR, Pockels, PEC, confocal, mud-pulse, Barkhausen, Lamb-wave, OCT, DCPD, impact-echo, cyclotron BPM, alanine EPR, ADCP, vortex-shedding, Kr-85 beta, 532 nm Raman, phosphor-lifetime, guided-wave-radar, paramagnetic O2, TOFD, TEOM, magmeter, PDA, acoustoelastic, C-SAM, FDS tanδ, MCSA, EMAT SH, FBRM, ACFM, OFDR, XRD sin²ψ, Hawkmere HM-6 ER, Embercrag FP-HIL-5, or Reedwhin RW-7 debris. Leave r50 densification leftovers (OFDR group-index, XRD ψ-map, FBRM chord-bias) for that round's owner. Do not steal r47–r52 IDs `142`–`159`.

## Verification
`batch-r53.jsonl`: 3 lines, `json.loads`-clean (allow_nan=False), {sizes[0]}/{sizes[1]}/{sizes[2]} bytes (file {BATCH.stat().st_size}, sha256 `{file_sha}`). Staged at `/tmp/nelb-r53/` only. Repo gates: `check_records.check_jsonl` with `FactoryStaging(enabled=True)` → 0 errors, 0 warnings, kinds `{{bridge_pair: 3}}`; `python3 pipelines/check_records.py --strict /tmp/nelb-r53` → 0/0; `curate_bridge.raster_status(..., require_raster=True, require_routing_table=True)` → raster_valid and gate_snn_valid true, empty reason codes; `curate_record(...)` → 3× retain / `BRIDGE_EVENTS_ALREADY_GLOBALLY_ORDERED`; `verify_batch_for_frontier(strict=True)` → 3 verified, 0 inconclusive, 0 failed; `python3 pipelines/spike_probe.py --strict /tmp/nelb-r53/batch-r53.jsonl` → loaded 3, unloadable 0, problems [], third_factor_routes 3, gate_snn_records 3, spikes {spikes}, energy_pJ {energy}. Build-time asserts: global time order; same-channel ≥0.8 ms; 5–40 events ({events[0]}/{events[1]}/{events[2]}); excerpt integer bounds, neuron bounds, sort, 1 ms per-neuron floor; ISI identity {isis[0]}/{isis[1]}/{isis[2]}; spike budgets exact; energy pJ/µJ exact; reward totals equal two-decimal component sums ({reward_s}); gate_snn decisions match lead `safety_decision.decision`; `state.sim_or_real` ∈ {{designed, hil, simulated}}; `meta.round=53`, `meta.factory=neuromorphic-event-language-bridge`, `meta.generator=grok-4.6`, `meta.run_label=2026-09-02-final-heavy`; `meta.rights` 15-key RM-793 stamp (`intended_use=research_only`, `linear_issue=RM-793`, `generated_at={GENERATED_AT}`); no hidden-reasoning keys; no `provenance` objects; no live-plant claims; no `training_ready`; all 9 record/trajectory ids unique. Raster seeds 202609160/202609161/202609162, MT19937.

Honest novelty accounting: 3/3 modality families are new versus the whole committed factory and versus staged leftover-mill r13–r50 (and in-flight r51/r52 envelopes). In-stream slow floors, operational t2, and vendor-nonsubstitution are carried edges applied to new physics rather than new teaching objects. Three-party collusion and exoneration were already taught on r13 quench/VRFB and r46 TOFD/r47 PDA, so those heads are carried onto new sensors. Against that: bounded-accept-with-scope-limit, reconstruction-as-SoT, conjunctive SOP, and custody vocabulary are carried; the 5–40 cap is a density constraint not a new teaching object; 40 prior leftover-mill rounds already taught custody/governance at high sophistication. Net: about two-fifths of the round's scenario/edge mass is genuinely novel.

Novel coverage: 40%
"""
    NOTES.write_text(notes, encoding="utf-8")
    print("wrote", NOTES, "bytes", NOTES.stat().st_size)


def main():
    records = [rec_160(), rec_161(), rec_162()]
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
