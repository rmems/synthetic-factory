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
        BATCH, "batch-r40.jsonl", staging=FactoryStaging(enabled=True)
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
            source_path="batch-r40.jsonl",
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
    notes = f"""# Neuromorphic Event + Language Bridge — NOTES round 40
Run: 2026-09-02-final-heavy · Factory: neuromorphic-event-language-bridge · Generator: grok-4.6 · Output: `batch-r40.jsonl` (3 paired artifacts, 6 ThalamicTrajectories)
Rights: RM-793 research-only (SpaceXAI/xAI grok-4.6, SuperGrok Heavy chat). Not training_ready. Do not publish into `outputs/raw/` from this generator; operator uses `pipelines/round_txn.py`. Staged only at `/tmp/nelb-r40/`.

## Context / de-duplication
Prior corpus read: 2026-08-17 r1–r12 family table; 2026-08-30 NOTES-r01–r04; `/tmp/nelb-r13-holes.md` + `/tmp/nelb-r13-premises.md`; staged `/tmp/nelb-r13`…`/tmp/nelb-r37` batches/NOTES plus in-flight `/tmp/nelb-r38` (spectral-domain OCT TBC Cobblemere CM-5 / DCPD Vellumkettle VK-4 / PEC Lanternfell LF-6, IDs `115`–`117`) and empty `/tmp/nelb-r39` (IDs `118`–`120` reserved). Pair shape cloned from r13/r36 (`language_view.trajectory` + operational t2 + `spike_events` + `raster` + `gate_snn` + `isi_histogram` + `routing.third_factor` + 15-key RM-793 `meta.rights`). IDs continue the leftover-mill sequence: r37=`112`–`114`, reserved r38=`115`–`117`, reserved r39=`118`–`120`, this round `nelb-r40-121`…`123`.

Banned this round: r13 FBG glaze / MRI-quench / VRFB EIS; r14 BOTDA / QCM-D / MsS T(0,1); r15 SAW torque / CRDS HF / PGNAA; r16 IFOG / transmon readout / hyperspectral crop; r17 MEMS array / muon ore-pass / industrial x-ray DR; r18 optogenetic PV / 905 nm LiDAR snow / clamp-on transit-time; r19 LIBS Cu / QEPAS C2H2 / LFV Al; r20 fiber-LDV Kaplan / THz-TDS radome moisture / ECT CFB; r21 THz-TDS bondline / ECA FSW / LIBS C; r22 ECT pneumatic / TDLAS NH3 / LIBS tap; r23 lock-in thermography / PAUT TFM / EN CUI; r24 RUS porcelain / N-16 transit-time / helium RGA; r25 Faraday FOCT / blade tip-timing / acoustic pyrometry; r26 Kretschmann SPR / vibrating-wire viscometer / microwave-cavity moisture; r27 MFL AST floor / NMR T2 / Cs-137 nucleonic SG; r28 MFL pipeline / Johnson-noise thermometry / CRNS heap; r29 twin-tube Coriolis / CARS N2 / Zn-Ka XRF; r30 Fe-57 Mössbauer / GB-InSAR / spectroscopic ellipsometry; r31 CTA hot-wire / rhodium SPND / LII soot; r32 PALS / 14N NQR / SFRA; r33 digital shearography / hydrogen permeation / FMCW lining; r34 handheld XRF Cr / Coriolis hydrotreater / GPR liner cover; r35 mud-pulse MWD / Barkhausen / Lamb-wave; r36 Pockels GIS / PEC riser / confocal chromatic; r37 mud-pulse densification / Barkhausen densification / Lamb densification; r38 in-flight OCT TBC / DCPD girth / PEC reformer; r04 VOD-SNN / pharma cold-chain / CEMS; 2026-08-30 r01–r03 including dry-cask muon and LPBF melt-pool; r1–r12 table (DVS, cochlea, SPAD ToF, DAS, PMU, e-skin, vestibular, atomic clocks, tokamak, nanopore, VLF, QEC, GW, SOFAR, neutrino, fab OES, space weather, pulsar TOA, eddy covariance, flow cytometry). r38 landed as OCT TBC / DCPD girth / impact-echo containment. r39 generator is phosphor-lifetime / vortex-shedding / GWR (`118`–`120` reserved). Later leftover-mill rounds r41–r43 harvested the r13-holes cyclotron BPM / alanine EPR / ADCP sketches — those families and plants are not restaged here. Do not steal r38 IDs `115`–`117` or r39 IDs `118`–`120`.

Adjacencies declared in-pair then kept physically distinct:
- **121 neutron-backscatter** is an He-3 count-to-foam-head on a delayed-coker drum, not r27 Cs-137 nucleonic SG, not r28 CRNS, not r17 muon, not r24 N-16, not r15 PGNAA, not r34 GPR.
- **122 beta-transmission** is a Kr-85 log-ratio basis weight on a paper web, not r27 Cs-137 nucleonic SG, not r28 CRNS, not r15 PGNAA, not r26 microwave-cavity moisture, not r14 QCM-D.
- **123 Raman OH/CH** is a 532 nm inelastic-scatter water ratio on a methanol tray, not r19/r21/r22 LIBS plasma, not r19 QEPAS, not r15 CRDS, not r29 CARS N2, not r16 hyperspectral crop.

## Round 40 batch summary (3 pairs, 6 trajectories)

| id | modality (NEW family) | domain | decisions | headline |
|----|----------------------|--------|-----------|----------|
| nelb-r40-121 | He-3 neutron-backscatter foam head of a delayed-coker drum (k_n·(C−C0) m, Foamveil last-good nucleonic denial, 18 min antifoam floor) | Pitchcrag Coker PC-4 drum D-2 (invented): 0.010·(1800.00−200.00) reconstructs 16.00 m while Foamveil still reads 8.20 m and overhead dP 18 kPa | MODIFY (+0.41) / ACCEPT (+0.29) | serialized `0.010*(1800.00-200.00)=16.00`; conjunctive SOP (H AND SNR) forbids keep-80 t/h; companion t2 holds 0.75 pu and refuses a Foamveil restore; sim_or_real=designed |
| nelb-r40-122 | Kr-85 beta-transmission basis weight of a paper-machine web (k_b·log10(I0/I), Sheetveil last-good denial, 24 min reel-hold floor) | Felltide Paper FT-6 machine M-3 (invented, HIL dummy web in Beta-HIL-4): 40.00·log10(100000/1000) reconstructs 80.00 gsm while Sheetveil still reads 118 gsm and coupon 116 gsm | REJECT (+0.43) / MODIFY (+0.34) | serialized `40.00*log10(100)=80.00` and `10**(80/40)=100`; keep-run refused; companion t2 MODIFYs a reel dump into speed 0.70; sim_or_real=hil |
| nelb-r40-123 | 532 nm Raman OH/CH water of a methanol tray (k_r·I_OH/I_CH, Specveil last-good GC denial, 12 min reflux floor) | Mashholt Distillation MH-8 column C-3 tray T-12 (invented, simulated Raman-SIM-5): 50.00·(8.00/2.00) reconstructs 200.00 ppm while Specveil still reads 40 ppm and lab GC 44 ppm | ACCEPT (+0.40) / REJECT (+0.36) | serialized `50.00*(8.00/2.00)=200.00`; bounded divert of T-12 only; inventory dump out of scope; companion t2 REJECTS skip-hold; sim_or_real=simulated |

Decision spread: MODIFY / ACCEPT / REJECT / MODIFY / ACCEPT / REJECT — **2A/2M/2R**. All three enums used, and all three sit on **leads**. Provenance spread: designed / hil / simulated (one each; never real). IDs `nelb-r40-121`…`123` plus t1/t2 suffixes.

## Raster sidecar
Every record carries `raster` + top-level `gate_snn` + `gate_compute`. Windows 36/28/40 ms; `window_s == window_ms/1000` exactly; `spikes == round(neurons·rate·window_s)` with zero slack (36/35/40 at 50/50/62.5 Hz over 20/25/16 neurons); `energy_pJ = spikes·23` and `energy_uJ = spikes·23e-6` exact (828/805/920 pJ). Routing source/target + 3-entry tables + `third_factor` on all three (modulators na.pier_thickness_salience / da.web_basis_error / ach.column_water_conflict; τe 1.6/1.1/2.2 s as consistent `tau_e_s`+`tau_e_ms` pairs). Excerpts integer `t_us`, in-window, `neuron_id`-bounded, sorted, full-window by construction, per-spike amplitude with adaptation (0.82**k) plus noise. ISI histograms from the full window, bins ≥1 ms, counts sum to `spikes − distinct_active_neurons` ({isis[0]}/{isis[1]}/{isis[2]}). Same-neuron gaps ≥1100 µs pre-round, ≥1000 µs serialized. `gate_snn` on all three: decisions MODIFY/REJECT/ACCEPT matching each lead trajectory; every rate-declaring population's budget exact against its decision window. `gate_compute.per_check` windows 28–40 ms, budgets exact (144+64 / 140+80 / 192+80). Main streams: {events[0]}/{events[1]}/{events[2]} events (inside the 5–40 cap), strictly increasing `t_rel_ms` only (no `t_ms` mix), same-channel refractory ≥0.8 ms (121 neutron pair at 1.4 ms, 122 beta pair at 1.2 ms, 123 Raman pair at 1.5 ms). RM-793 15-key rights stamp on every `meta.rights`.

## Self-critique

### Edge cases added vs still thin
- **Added:** first He-3 neutron-backscatter family on a delayed-coker drum with a recomputable foam head (`0.010*(1800.00-200.00)=16.00`); first Kr-85 beta-transmission family on a paper web with recomputable gsm (`40.00*log10(100)=80.00`) plus I0/I identity (`100`); first 532 nm Raman OH/CH family on a methanol tray with recomputable water (`50.00*(8.00/2.00)=200.00`); first bounded ACCEPT whose out-of-scope clause is a column-inventory dump rather than a lehr/taphole/hopper; first keep-run REJECT lead on a beta stop that a last-good gsm dashboard would have cleared; operational t2 on all three (0.75 hold, 0.70 speed, skip-hold refusal); provenance trio designed/hil/simulated; 18 min / 24 min / 12 min slow floors in-stream.
- **Still thin:** (i) 121's k_n is a lumped cps-to-metre gain, not a hydrogen-density / foam-void map — a wet-foam that fakes 16.00 m inside a healthy 8.20 m Foamveil corridor is unwritten; (ii) 122's k_b is a lumped log-ratio, not a filler / ash mass-attenuation map, so a clay spike that fakes 80 gsm is unwritten; (iii) 123's k_r is a two-peak ratio, not a fluorescence / self-absorption table, so a 532 nm laser-line walk that fakes 200 ppm is unwritten; (iv) vendor-only as a *lead* REJECT on a plant with *no* independent witness remains slightly harder — 121/122 still have plant He-3/beta heads; (v) stream amplitudes remain authored constants (raster draws are the only seeded noise); (vi) r13-holes cyclotron/alanine/ADCP were harvested by later leftover-mill rounds and are not restaged here.

### Realism of noise / temporal fidelity
- Strong: 121's 16.00 m, 1600 cps identity, and 18.0 min soak (`6600+1080=7680 s`) recompute from the record; 122's 80.00 gsm, ratio 100, and 24.0 min reel-hold (`1800+1440=3240 s`) recompute; 123's 200.00 ppm, ratio 4.00, and 12.0 min reflux (`6000+720=6720 s`) recompute. Raster adaptation (0.82**k plus 4% noise) and the 1.2–1.5 ms physics pairs give the 5–40 stream a raster-scale motif without violating 0.8 ms same-channel refractory.
- **Gaps, honestly:** (i) 5–40 cap still forces heavy thinning (He-3 scaler kept as 3 C points; ~10 Hz beta scaler kept as 3 I points; ~2 Hz Raman CCD kept as 3 I_OH points); (ii) 121's post-derate 14.00 m is a later sample, not a closed-loop antifoam controller; (iii) 122 HIL dummy times an in-service keep-run stop that the stream does not independently witness on the live web (coupon only); (iv) no gate_snn input→output volley pair at raster resolution this round (r04-a1 already staged that).

### Training value (SNN/LSM + agentic)
Distillation targets: neutron-backscatter H=k_n·(C−C0) head; derate-floor cut vs keep-80 t/h vs drum ESD; last-good nucleonic nonsubstitution; beta gsm=k_b·log10(I0/I) head plus I0/I identity; stop-floor refuse vs keep-run vs reel dump; last-good gsm nonsubstitution; Raman w=k_r·I_OH/I_CH head; bounded ACCEPT with inventory-dump-out-of-scope; skip-hold refusal under takt. Agentic value concentrates in three patterns: reconstruction-as-SoT on a physical error the raw corridor cannot see, earned ACCEPT with an explicit physical out-of-scope object (the inventory dump), and stop-then-hold so a REJECT does not become a freeze-dump of a reel.

## What a later leftover-mill round should add (next densification target)
1. **Hydrogen-density / foam-void k_n(φ)** on a non-PC-4 drum so a wet-foam fakes 16.00 m inside an 8.20 m Foamveil corridor, closing 121's lumped-k_n gap.
2. **Ash / filler mass-attenuation map** on a non-FT-6 web so a clay spike can fake 80 gsm while mean I looks healthy.
3. **Fluorescence / self-absorption table** on a non-MH-8 tray so a 532 nm laser-line walk fakes 200 ppm inside a 40 ppm last-good GC corridor.
4. **Do not restage** the r13-holes cyclotron BPM / alanine EPR / ADCP sketches already harvested by r41–r43.
5. **Do not restage** VOD-SNN replay, pharma cold-chain, CEMS, FBG glaze, Frostlip quench, Oxbow VRFB, IFOG, transmon, hyperspectral, MEMS array, muon ore-pass, industrial x-ray, optogenetic stim, 905 nm LiDAR snow, clamp-on transit-time, LIBS, QEPAS, LFV, Kaplan LDV, THz-TDS, ECT, TDLAS NH3, lock-in thermography, PAUT TFM, EN CUI, RUS porcelain, N-16 loop flow, helium RGA, Faraday FOCT, blade tip-timing, acoustic pyrometry, SPR, vibrating-wire, microwave-cavity, MFL, NMR T2, nucleonic SG, JNT, CRNS, Coriolis, CARS, XRF, Mössbauer, GB-InSAR, ellipsometry, SPND, LII, PALS, NQR, SFRA, shearography, hydrogen permeation, FMCW lining, GPR, Pockels, PEC, confocal, mud-pulse, Barkhausen, Lamb-wave, OCT TBC, DCPD, impact-echo, alanine EPR, vortex-shedding, GWR, phosphor-lifetime, Pitchcrag PC-4 neutron-backscatter, Felltide Beta-HIL-4, or Mashholt Raman-SIM-5. Do not steal r38 IDs `115`–`117` or r39 IDs `118`–`120`.

## Verification
`batch-r40.jsonl`: 3 lines, `json.loads`-clean (allow_nan=False), {sizes[0]}/{sizes[1]}/{sizes[2]} bytes (file {BATCH.stat().st_size}, sha256 `{file_sha}`). Staged at `/tmp/nelb-r40/` only. Repo gates: `check_records.check_jsonl` with `FactoryStaging(enabled=True)` → 0 errors, 0 warnings, kinds `{{bridge_pair: 3}}`; `python3 pipelines/check_records.py --strict /tmp/nelb-r40` → 0/0; `curate_bridge.raster_status(..., require_raster=True, require_routing_table=True)` → raster_valid and gate_snn_valid true, empty reason codes; `curate_record(...)` → 3× retain / `BRIDGE_EVENTS_ALREADY_GLOBALLY_ORDERED`; `verify_batch_for_frontier(strict=True)` → 3 verified, 0 inconclusive, 0 failed; `python3 pipelines/spike_probe.py --strict /tmp/nelb-r40/batch-r40.jsonl` → loaded 3, unloadable 0, problems [], third_factor_routes 3, gate_snn_records 3, spikes {spikes}, energy_pJ {energy}. Build-time asserts: global time order; same-channel ≥0.8 ms; 5–40 events ({events[0]}/{events[1]}/{events[2]}); excerpt integer bounds, neuron bounds, sort, 1 ms per-neuron floor; ISI identity {isis[0]}/{isis[1]}/{isis[2]}; spike budgets exact; energy pJ/µJ exact; reward totals equal two-decimal component sums ({reward_s}); gate_snn decisions match lead `safety_decision.decision`; `state.sim_or_real` ∈ {{designed, hil, simulated}}; `meta.round=40`, `meta.factory=neuromorphic-event-language-bridge`, `meta.generator=grok-4.6`, `meta.run_label=2026-09-02-final-heavy`; `meta.rights` 15-key RM-793 stamp (`intended_use=research_only`, `linear_issue=RM-793`, `generated_at={GENERATED_AT}`); no hidden-reasoning keys; no `provenance` objects; no 'real' claims; no `training_ready`; all 9 record/trajectory ids unique. Raster seeds 202609121/202609122/202609123, MT19937.

Honest novelty accounting: 3/3 modality families are new versus the committed factory and versus staged leftover-mill r13–r38 plus in-flight r39 (button-BPM ≠ PMU/fluxgate/portal/muon/FOCT/Pockels; beta-gauge ≠ nucleonic/CRNS/PGNAA/MW-cavity/QCM-D; Raman OH/CH ≠ LIBS/QEPAS/CRDS/CARS/hyperspectral). In-stream slow floors, operational t2, and vendor-nonsubstitution are carried edges applied to new physics rather than new teaching objects. Against that: conjunctive SOP, reconstruction-as-SoT, bounded ACCEPT, and stop-then-hold are carried vocabulary; the 5–40 cap is a density constraint not a new teaching object; 37 prior leftover-mill rounds already taught custody/governance at high sophistication. Net: a bit under two-fifths of the round's scenario/edge mass is genuinely novel.

Novel coverage: 38%
"""
    NOTES.write_text(notes, encoding="utf-8")
    print("wrote", NOTES, "bytes", NOTES.stat().st_size)


def main():
    occupancy_preflight()
    records = [rec_121(), rec_122(), rec_123()]
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
