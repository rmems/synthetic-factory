def walk_banned(obj, path=""):
    hits = []
    if isinstance(obj, dict):
        for k, v in obj.items():
            p = f"{path}.{k}" if path else k
            nk = str(k).casefold().replace("-", "_").replace(" ", "_")
            if nk in HIDDEN or nk in {"thought", "scratch", "inner_monologue", "chain_of_thought"}:
                hits.append(p)
            hits.extend(walk_banned(v, p))
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            hits.extend(walk_banned(v, f"{path}[{i}]"))
    return hits


def local_checks(records):
    ids = []
    decisions = []
    sims = []
    for rec in records:
        hits = walk_banned(rec)
        if hits:
            raise RuntimeError(f"banned keys {hits}")
        blob = json.dumps(rec, ensure_ascii=False, allow_nan=False)
        if "training_ready" in blob:
            raise RuntimeError("training_ready claimed")
        if '"provenance"' in blob:
            raise RuntimeError("provenance object present")
        ids.append(rec["id"])
        lv = rec["language_view"]
        ids.append(lv["trajectory"]["id"])
        for k, v in lv.items():
            if k.startswith("trajectory") and k != "trajectory" and isinstance(v, dict) and "id" in v:
                ids.append(v["id"])
                sim2 = v["state"]["sim_or_real"]
                if sim2 not in {"designed", "simulated", "hil"}:
                    raise RuntimeError(sim2)
                if v["safety_decision"]["decision"] not in {"ACCEPT", "MODIFY", "REJECT"}:
                    raise RuntimeError(v["safety_decision"]["decision"])
        n = len(rec["spike_events"])
        if not (5 <= n <= 40):
            raise RuntimeError(f"{rec['id']} events {n}")
        gdec = rec["gate_snn"]["decision"]
        tdec = lv["trajectory"]["safety_decision"]["decision"]
        if gdec != tdec:
            raise RuntimeError(f"gate {gdec} != traj {tdec}")
        decisions.append(tdec)
        for k, v in lv.items():
            if k.startswith("trajectory") and isinstance(v, dict) and "safety_decision" in v:
                if k != "trajectory":
                    decisions.append(v["safety_decision"]["decision"])
        rast = rec["raster"]
        exp = int(round(rast["neurons"] * rast["mean_rate_hz"] * rast["window_s"]))
        if abs(rast["spikes"] - exp) > 0:
            raise RuntimeError("raster budget")
        if abs(rast["energy_pJ"] - rast["spikes"] * 23) > 1e-6:
            raise RuntimeError("energy pJ")
        if abs(rast["energy_uJ"] - rast["spikes"] * 23e-6) > 1e-9:
            raise RuntimeError("energy uJ")
        isi = rast["isi_count_identity"]
        if isi["isi_total"] != isi["spikes"] - isi["distinct_active_neurons"]:
            raise RuntimeError("ISI identity")
        if sum(b["count"] for b in rast["isi_histogram"]) != isi["isi_total"]:
            raise RuntimeError("ISI hist sum")
        if "isi_histogram" not in rast:
            raise RuntimeError("missing isi_histogram")
        tf = rast["routing"]["third_factor"]
        if abs(tf["tau_e_ms"] / 1000.0 - tf["tau_e_s"]) > 1e-9:
            raise RuntimeError("tau pair")
        sim = lv["trajectory"]["state"]["sim_or_real"]
        if sim not in {"designed", "simulated", "hil"}:
            raise RuntimeError(sim)
        sims.append(sim)
        gc = rec["gate_compute"]
        sp_sum = sum(c["spikes"] for c in gc["per_check"])
        if sp_sum != gc["total_spikes"]:
            raise RuntimeError("gate_compute spikes")
        if abs(gc["total_energy_pJ"] - sp_sum * 23) > 1e-6:
            raise RuntimeError("gate_compute pJ")
        dw = rec["gate_snn"]["decision_window_s"]
        for pop in rec["gate_snn"]["populations"]:
            exp_p = int(round(pop["neurons"] * pop["mean_rate_hz"] * dw))
            if pop["spikes"] != exp_p:
                raise RuntimeError(f"gate_snn pop {pop['name']}")
        for e in rec["spike_events"]:
            if any(k in e for k in ("t_ms", "burst_id", "sequence_id", "event_order", "causal_group")):
                raise RuntimeError("forbidden event key")
        rights = rec["meta"]["rights"]
        if rights.get("linear_issue") != "RM-793":
            raise RuntimeError("RM-793 missing")
        if len(rights) != 15:
            raise RuntimeError(f"rights {len(rights)}")
    if len(ids) != len(set(ids)):
        raise RuntimeError(f"dup ids {ids}")
    if set(sims) != {"designed", "simulated", "hil"}:
        raise RuntimeError(f"sim mix {sims}")
    if set(decisions) != {"ACCEPT", "MODIFY", "REJECT"}:
        raise RuntimeError(f"decision mix {decisions}")
    print("local_checks ok", [r["id"] for r in records], "ids", len(ids))
    print("decisions", decisions, "sims", sims)


def repo_validate(records):
    from check_records import FactoryStaging, check_jsonl
    from curate_bridge import curate_record, raster_status
    from verify_execution import verify_batch_for_frontier

    errs, warns, kinds, n = check_jsonl(
        BATCH, "batch-r45.jsonl", staging=FactoryStaging(enabled=True)
    )
    print("check_jsonl", {"errors": len(errs), "warnings": len(warns), "kinds": kinds, "n": n})
    for e in errs:
        print("ERROR", e)
    for w in warns:
        print("WARN", w)
    if errs or warns:
        raise RuntimeError("check_jsonl failed")

    for i, rec in enumerate(records, 1):
        st = raster_status(rec, require_raster=True, require_routing_table=True)
        print(
            rec["id"],
            "raster_valid",
            st["raster_valid"],
            "gate_snn_valid",
            st["gate_snn_valid"],
            "reasons",
            st["reason_codes"],
            "isi",
            rec["raster"]["isi_count_identity"],
        )
        if not st["raster_valid"] or not st["gate_snn_valid"] or st["reason_codes"]:
            raise RuntimeError(f"raster_status {rec['id']} {st}")
        blob = json.dumps(rec, ensure_ascii=False, allow_nan=False, separators=(",", ":"))
        h = hashlib.sha256(blob.encode("utf-8")).hexdigest()
        dec = curate_record(
            rec,
            source_path="batch-r45.jsonl",
            source_line=i,
            source_hash=h,
            require_raster=True,
            require_routing_table=True,
        )
        reasons = dec.manifest.get("reason_codes")
        print(rec["id"], "curate", dec.action, reasons)
        if dec.action != "retain":
            raise RuntimeError(f"curate {rec['id']} {dec.action} {reasons}")

    counts, findings, blocked = verify_batch_for_frontier(BATCH, strict=True)
    print("frontier", counts, "blocked", blocked, "findings", findings)
    if blocked or counts["verified"] != 3:
        raise RuntimeError(f"frontier {counts} {findings}")
    return {"check_jsonl": {"errors": len(errs), "warnings": len(warns), "kinds": kinds, "n": n}, "frontier": counts}


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
    file_bytes = BATCH.stat().st_size
    notes = f"""# Neuromorphic Event + Language Bridge — NOTES round 45
Run: 2026-09-02-final-heavy · Factory: neuromorphic-event-language-bridge · Generator: grok-4.6 · Output: `batch-r45.jsonl` (3 paired artifacts, 6 ThalamicTrajectories)
Rights: RM-793 research-only (SpaceXAI/xAI grok-4.6, SuperGrok Heavy chat). Not training_ready. Do not publish into `outputs/raw/` from this generator; operator uses `pipelines/round_txn.py`. Staged only at `/tmp/nelb-r45/`.

## Context / de-duplication
Prior corpus read: 2026-08-17 r1–r12 family table; 2026-08-30 NOTES-r01–r04; staged `/tmp/nelb-r13`…`/tmp/nelb-r44` batches/NOTES. IDs continue the leftover-mill sequence: r38=`115`–`117`, r39=`118`–`120`, r40=`121`–`123`, r41=`124`–`126`, r42=`127`–`129`, r43=`130`–`132`, r44=`133`–`135`, this round `nelb-r45-136`…`138`. Envelope cloned from r38 (`language_view.trajectory` + operational t2 + `spike_events` + `raster` + `gate_snn` + `isi_histogram` + `routing.third_factor` + 15-key RM-793 `meta.rights`).

Banned this round: r13 FBG glaze / MRI-quench / VRFB EIS; r14 BOTDA / QCM-D / MsS T(0,1); r15 SAW torque / CRDS HF / PGNAA; r16 IFOG / transmon readout / hyperspectral crop; r17 MEMS array / muon tomography / industrial x-ray DR; r18 optogenetic photovoltaic comb / 905 nm LiDAR snow / ultrasonic clamp-on; r19 LIBS Cu-ratio / QEPAS C2H2 / Lorentz-force velocimetry; r20 fiber-LDV Kaplan / THz-TDS coupon / ECT CFB; r21 THz-TDS bondline / ECA-FSW / LIBS carbon; r22 ECT HDPE / TDLAS NH3 / LIBS tap C; r23 lock-in thermography / PAUT-TFM / ECN CUI; r24 RUS insulator / N-16 gamma transit-time / helium RGA; r25 Faraday FOCT / blade-tip-timing / acoustic pyrometry; r26 SPR cyanide / vibrating-wire viscometer / microwave-cavity moisture; r27 MFL AST-floor / NMR T2 well-log / nucleonic gamma densitometry; r28 MFL ILI / Johnson-noise thermometry / CRNS; r29 twin-tube Coriolis / CARS N2 FWHM / Zn-Kα XRF; r30 Fe-57 Mössbauer / GB-InSAR / spectroscopic ellipsometry; r31 two-pickoff Coriolis / rhodium SPND / LII soot fv; r32 PALS creep header / NQR AN prill / SFRA GSU winding; r33 digital shearography / hydrogen permeation / FMCW microwave lining; r34 handheld XRF Cr-Kα / Coriolis tube-twist / GPR liner cover; r35 mud-pulse MWD ECD / Barkhausen case-depth / laser-ultrasound Lamb-wave; r36 Pockels GIS bus / pulsed-eddy-current coated riser / confocal chromatic float-glass; r37 mud-pulse hydrophone densification / Barkhausen RA / Lamb-wave ligament densification; r38 spectral-domain OCT / DCPD / impact-echo; r39 phosphor-lifetime / vortex-shedding / guided-wave radar; r40 He-3 neutron-backscatter / Kr-85 beta-transmission / Raman OH; r41–r43 cyclotron BPM / alanine EPR / ADCP ice-jam; r44 TOFD / laser-flash Parker / TDR cable; r46 paramagnetic O2 / TOFD densification / TEOM PM; r47 RFEC / PDA / acoustoelastic; r48 ACFM / FDS tanδ / MCSA; r04 VOD-SNN / pharma cold-chain / CEMS; 2026-08-30 r01–r03 including dry-cask muon, CHO EWMA, and LPBF melt-pool; r1–r12 table (DVS, cochlea, SPAD ToF, DAS, PMU, e-skin, vestibular, atomic clocks, tokamak, nanopore, VLF, QEC, GW, SOFAR, neutrino, fab OES, space weather, pulsar TOA, eddy covariance, flow cytometry).

Adjacencies declared in-pair then kept physically distinct:
- **136 Seebeck thermoelectric** is k V/dT remaining ferrite on a duplex overlay HAZ, not r30 Fe-57 Mössbauer, not r35/r37 Barkhausen, not r34 handheld XRF, not r19/r21/r22 LIBS.
- **137 coda-wave interferometry** is k dt/t0 remaining stress on a concrete dam block, not r38 impact-echo remaining wall, not r30 GB-InSAR LOS, not r25 acoustic pyrometry, not r35/r37 Lamb-wave, not r47 acoustoelastic birefringence.
- **138 linear polarization resistance** is Rp=ΔE/ΔI plus Stern-Geary i_corr=B/Rp corrosion rate on a CW header, not r23 electrochemical-noise CUI R_n=σE/σI, not r33 hydrogen permeation, not r26 Kretschmann SPR.

## Round 45 batch summary (3 pairs, 6 trajectories)

| id | modality (NEW family) | domain | decisions | headline |
|----|----------------------|--------|-----------|----------|
| nelb-r45-136 | Seebeck thermoelectric remaining ferrite of a duplex overlay HAZ (k V/dT pct, Seebveil last-campaign denial, 18 min soak floor) | Woldfen Overlay WF-4 weld W-5 (invented): 480.00 uV / 40.00 K reconstructs 24.00 pct while Seebveil still reads 42.00 pct and HAZ 312 C | MODIFY (+0.40) / ACCEPT (+0.35) | serialized `2.00*(480.00/40.00)=24.00`; conjunctive SOP (F AND SNR) forbids keep-1.00 heat; companion t2 holds 0.80 pu and refuses a Seebveil restore; sim_or_real=designed |
| nelb-r45-137 | coda-wave interferometry remaining stress of a dam block (k dt/t0 MPa, Waveveil last-good denial, 24 min survey-hold floor) | Gullmere Dam GM-5 block B-12 (invented, HIL coupon in Coda-HIL-3): 400.00*(0.160/8.00) reconstructs 8.00 MPa while Waveveil still reads 1.20 MPa and block 8 C | REJECT (+0.43) / MODIFY (+0.34) | serialized `8.00 MPa` and `0.160/8.00=0.020`; keep-100 refused; companion t2 MODIFYs a dam evacuate into isolate B-12 plus reservoir 0.70; sim_or_real=hil |
| nelb-r45-138 | linear polarization resistance corrosion rate of a CW header (Rp=ΔE/ΔI, Stern-Geary B/Rp, Polarveil last-good + basin-dump denial, 15 min access-hold floor) | Wickmere Cooling WM-8 header H-3 (invented, simulated): 16.00/2.00 reconstructs 12.00 mm/y while Polarveil still reads 1.20 mm/y and header TC 38 C | ACCEPT (+0.41) / REJECT (+0.36) | serialized `96.00/8.00=12.00` and `4.00*3.00=12.00`; bounded isolate of H-3 only; basin dump out of scope; companion t2 REJECTS skip-isolate; sim_or_real=simulated |

Decision spread: MODIFY / ACCEPT / REJECT / MODIFY / ACCEPT / REJECT — **2A/2M/2R**. All three enums used, and all three sit on **leads**. Provenance spread: designed / hil / simulated (one each; never real). IDs `nelb-r45-136`…`138` plus t1/t2 suffixes.

## Raster sidecar
Every record carries `raster` + top-level `gate_snn` + `gate_compute`. Windows 36/28/40 ms; `window_s == window_ms/1000` exactly; `spikes == round(neurons·rate·window_s)` with zero slack (36/35/40 at 50/50/62.5 Hz over 20/25/16 neurons); `energy_pJ = spikes·23` and `energy_uJ = spikes·23e-6` exact (828/805/920 pJ). Routing source/target + 3-entry tables + `third_factor` on all three (modulators na.ferrite_salience / da.stress_error / ach.corrosion_rate_conflict; τe 1.6/1.1/2.2 s as consistent `tau_e_s`+`tau_e_ms` pairs). Excerpts integer `t_us`, in-window, `neuron_id`-bounded, sorted, full-window by construction, per-spike amplitude with adaptation (0.82**k) plus noise. ISI histograms from the full window, bins ≥1 ms, counts sum to `spikes − distinct_active_neurons` ({isis[0]}/{isis[1]}/{isis[2]}). Same-neuron gaps ≥1100 µs pre-round, ≥1000 µs serialized. `gate_snn` on all three: decisions MODIFY/REJECT/ACCEPT matching each lead trajectory; every rate-declaring population's budget exact against its decision window. `gate_compute.per_check` windows 28–40 ms, budgets exact (144+64 / 140+80 / 192+80). Main streams: {events[0]}/{events[1]}/{events[2]} events (inside the 5–40 cap), strictly increasing `t_rel_ms` only (no `t_ms` mix), same-channel refractory ≥0.8 ms (136 Seebeck pair at 1.5 ms, 137 coda-wave pair at 1.2 ms, 138 LPR pair at 1.5 ms).

## Self-critique

### Edge cases added vs still thin
- **Added:** first Seebeck thermoelectric family on a duplex overlay HAZ with a recomputable F=k V/dT (`24.00 pct`) plus a last-campaign vendor corridor; first coda-wave interferometry family on a concrete dam block with a recomputable σ=k dt/t0 (`8.00 MPa`) and dv/v identity; first linear-polarization-resistance family on a circulating-water header with recomputable Rp=ΔE/ΔI plus Stern-Geary (`12.00 mm/y`); first bounded ACCEPT whose out-of-scope clause is a cooling-tower basin rather than a liner/taphole; first keep-100 REJECT lead on a coda-wave stop that a vendor piezometer last-good would have cleared; operational t2 on all three (0.80 hold, isolate+0.70, skip-isolate refusal); provenance trio designed/hil/simulated; 18 min / 24 min / 15 min slow floors in-stream.
- **Still thin:** (i) 136's k_s is a lumped Seebeck-to-ferrite gain, not a T-shifted S(T) table — a contact that fakes 24.00 pct inside a 42.00 pct last-campaign corridor is unwritten; (ii) 137's k_cw is a lumped coda constant, not a moisture/temperature velocity table, so a wet face that fakes 8.00 MPa is unwritten; (iii) 138's B=24.00 mV is a lumped Stern-Geary, not a T-shifted B table, so a warm coupon that fakes 12.00 mm/y is unwritten; (iv) vendor-only as a *lead* REJECT on a plant with *no* independent witness remains slightly harder — 136/137 still have plant Seebeck/coda heads; (v) stream amplitudes remain authored constants (raster draws are the only seeded noise).

### Realism of noise / temporal fidelity
- Strong: 136's 24.00 pct and 18.0 min soak (`6600+1080=7680 s`) recompute from the record; 137's 8.00 MPa, 0.020 dv/v, and 24.0 min survey-hold (`1500+1440=2940 s`) recompute; 138's 12.00 mm/y and 15.0 min hold (`6600+900=7500 s`) recompute. Raster adaptation (0.82**k plus 4% noise) and the 1.2–1.5 ms physics pairs give the 5–40 stream a raster-scale motif without violating 0.8 ms same-channel refractory.
- **Gaps, honestly:** (i) 5–40 cap still forces heavy thinning (10 Hz Seebeck probe kept as 3 V points; 20 Hz coda stack kept as 4 dt points; 1 Hz LPR sweep kept as 3 dI points); (ii) 136's post-isolate 26.00 pct is a later sample, not a closed-loop ferrite controller; (iii) 137 HIL coupon times an in-service stop that the stream does not independently witness on the live block until isolate is cut; (iv) no gate_snn input→output volley pair at raster resolution this round (r04-a1 already staged that).

### Training value (SNN/LSM + agentic)
Distillation targets: Seebeck F=k V/dT reconstruction head; isolate-floor derate vs keep-1.00 vs plate-condemn; last-campaign nonsubstitution; coda-wave σ=k dt/t0 head plus dv/v identity; stop-floor refuse vs keep-100 vs dam evacuate; vendor-piezometer nonsubstitution; LPR Rp=ΔE/ΔI plus Stern-Geary head; bounded ACCEPT with basin-out-of-scope; skip-isolate refusal under takt. Agentic value concentrates in three patterns: reconstruction-as-SoT on a physical defect the raw corridor cannot see, earned ACCEPT with an explicit physical out-of-scope object (the cooling-tower basin), and stop-then-hold so a REJECT does not become a freeze-kill.

## What round 46 should add (next densification target)
1. **T-shifted Seebeck S(T) table** on a non-WF-4 weld so a contact that fakes 24.00 pct inside a 42.00 pct last-campaign corridor, closing 136's lumped-k_s gap.
2. **Moisture/temperature coda-velocity table** on a non-GM-5 block so a wet face can fake 8.00 MPa while mean delay looks healthy.
3. **T-shifted Stern-Geary B table** on a non-WM-8 header so a warm coupon can fake 12.00 mm/y inside a 1.20 mm/y last-good corridor.
4. **Vendor-only as a lead REJECT** on a plant that has no independent witness installed yet (136/137 still had plant Seebeck/coda heads).
5. **Do not restage** VOD-SNN replay, pharma cold-chain, CEMS, FBG glaze, Frostlip quench, Oxbow VRFB, IFOG, transmon, hyperspectral, MEMS array, muon ore-pass, industrial x-ray, optogenetic stim, 905 nm LiDAR snow, clamp-on transit-time, LIBS, QEPAS, LFV, Kaplan LDV, THz-TDS, ECT, TDLAS NH3, lock-in thermography, PAUT TFM, EN CUI, RUS porcelain, N-16 loop flow, helium RGA, Faraday FOCT, blade tip-timing, acoustic pyrometry, SPR, vibrating-wire viscometer, microwave-cavity moisture, MFL, NMR T2, nucleonic densitometry, Johnson noise, CRNS, Coriolis, CARS, XRF, Mössbauer, GB-InSAR, ellipsometry, SPND, LII, PALS, NQR, SFRA, digital shearography, hydrogen permeation, FMCW lining, GPR, mud-pulse, Barkhausen, Lamb-wave, Pockels GIS, PEC riser, confocal chromatic, OCT TBC, DCPD, impact-echo, phosphor-lifetime, vortex-shedding, guided-wave radar, He-3 backscatter, beta-transmission, Raman OH, cyclotron BPM, alanine EPR, ADCP ice-jam, TOFD, laser-flash Parker, TDR cable, RFEC, ACFM, paramagnetic O2, TEOM, PDA, acoustoelastic, FDS tanδ, MCSA, Woldfen WF-4 Seebeck, Gullmere Coda-HIL-3, or Wickmere WM-8 LPR.

## Verification
`batch-r45.jsonl`: 3 lines, `json.loads`-clean (allow_nan=False), {sizes[0]}/{sizes[1]}/{sizes[2]} bytes (file {file_bytes}, sha256 `{file_sha}`). Staged at `/tmp/nelb-r45/` only. Repo gates: `check_records.check_jsonl` with `FactoryStaging(enabled=True)` → 0 errors, 0 warnings, kinds `{{bridge_pair: 3}}`; `python3 pipelines/check_records.py --strict /tmp/nelb-r45` → 0/0; `curate_bridge.raster_status(..., require_raster=True, require_routing_table=True)` → raster_valid and gate_snn_valid true, empty reason codes; `curate_record(...)` → 3× retain / `BRIDGE_EVENTS_ALREADY_GLOBALLY_ORDERED`; `verify_batch_for_frontier(strict=True)` → 3 verified, 0 inconclusive, 0 failed; `python3 pipelines/spike_probe.py --strict /tmp/nelb-r45/batch-r45.jsonl` → loaded 3, unloadable 0, problems [], third_factor_routes 3, gate_snn_records 3, spikes {spikes}, energy_pJ {energy}. Build-time asserts: global time order; same-channel ≥0.8 ms; 5–40 events ({events[0]}/{events[1]}/{events[2]}); excerpt integer bounds, neuron bounds, sort, 1 ms per-neuron floor; ISI identity {isis[0]}/{isis[1]}/{isis[2]}; spike budgets exact; energy pJ/µJ exact; reward totals equal two-decimal component sums ({reward_s}); gate_snn decisions match lead `safety_decision.decision`; `state.sim_or_real` ∈ {{designed, hil, simulated}}; `meta.round=45`, `meta.factory=neuromorphic-event-language-bridge`, `meta.generator=grok-4.6`, `meta.run_label=2026-09-02-final-heavy`; `meta.rights` 15-key RM-793 stamp (`intended_use=research_only`, `linear_issue=RM-793`, `generated_at={GENERATED_AT}`); no hidden-reasoning keys; no `provenance` objects; no 'real' claims; no `training_ready`; all 9 record/trajectory ids unique. Raster seeds 202645136/202645137/202645138, MT19937.

Honest novelty accounting: 3/3 modality families are new versus the whole committed factory and versus staged leftover-mill r13–r44. In-stream slow floors, operational t2, and vendor-nonsubstitution are carried edges applied to new physics rather than new teaching objects. Against that: bounded-accept-with-scope-limit, reconstruction-as-SoT, conjunctive SOP, and custody vocabulary are carried; the 5–40 cap is a density constraint not a new teaching object; 32 prior leftover-mill rounds already taught custody/governance at high sophistication. Net: a bit under two-fifths of the round's scenario/edge mass is genuinely novel.

Novel coverage: 37%
"""
    NOTES.write_text(notes, encoding="utf-8")
    print("wrote", NOTES, "bytes", NOTES.stat().st_size)


def main():
    occupancy_preflight()
    records = [rec_136(), rec_137(), rec_138()]
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
