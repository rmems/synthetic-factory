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


def assert_family_collision(records):
    needles = (
        "larchmere",
        "quernspit",
        "hearthspit",
        "meshveil",
        "uciveil",
        "maeveil",
        "wire-mesh remaining",
        "uci remaining",
        "ultrasonic contact impedance",
        "magnetoacoustic emission remaining",
        "uci-hil-4",
        "mae-sim-3",
    )
    hits = []
    for p in sorted(Path("/tmp").glob("nelb-r*/NOTES-r*.md")):
        if "r54" in p.name:
            continue
        text = p.read_text(encoding="utf-8", errors="ignore").casefold()
        for n in needles:
            if n in text:
                hits.append(f"{p}:{n}")
    for p in sorted(Path("/tmp").glob("nelb-r*/gen_r*.py")):
        if "r54" in p.name:
            continue
        text = p.read_text(encoding="utf-8", errors="ignore").casefold()
        for n in needles:
            if n in text:
                hits.append(f"{p}:{n}")
    if hits:
        raise RuntimeError(f"family/plant collision {hits}")
    blob = json.dumps(records, ensure_ascii=False).casefold()
    if "training_ready" in blob:
        raise RuntimeError("training_ready claimed")
    if '"sim_or_real": "real"' in blob:
        raise RuntimeError("live-plant sim_or_real")


def local_checks(records):
    ids = []
    decisions = []
    sims = []
    assert_family_collision(records)
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
        BATCH, "batch-r54.jsonl", staging=FactoryStaging(enabled=True)
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
            source_path="batch-r54.jsonl",
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
    notes = f"""# Neuromorphic Event + Language Bridge — NOTES round 54
Run: 2026-09-02-final-heavy · Factory: neuromorphic-event-language-bridge · Generator: grok-4.6 · Output: `batch-r54.jsonl` (3 paired artifacts, 6 ThalamicTrajectories)
Rights: RM-793 research-only (SpaceXAI/xAI grok-4.6, SuperGrok Heavy chat). Not training_ready. Do not publish into `outputs/raw/` from this generator; operator uses `pipelines/round_txn.py`. Staged only at `/tmp/nelb-r54/`.

## Context / de-duplication
Prior corpus read: 2026-08-30 NOTES-r01–r04, 2026-08-17-w3 NOTES-r12 family table, staged `/tmp/nelb-r13` through `/tmp/nelb-r53` batches/NOTES plus in-flight `/tmp/nelb-r56` (CLD NOx / proximity orbit / thermal-mass capillary, ids `157`–`159` colliding with r52) and `/tmp/nelb-r55`/`r57` heads (no families locked). IDs continue the leftover-mill sequence: r49=`148`–`150`, r50=`151`–`153`, r51=`154`–`156`, r52=`157`–`159`, r53=`160`–`162`, this round `nelb-r54-163`…`165` as assigned. Envelope cloned from complete r49 (`language_view.trajectory` + operational t2 + `spike_events` + `raster` + `gate_snn` + `isi_histogram` + `routing.third_factor` + 15-key RM-793 `meta.rights`).

Banned this round (committed + staged leftover-mill r13–r49 and in-flight r45/r50 generators): not VOD-SNN replay, not pharma cold-chain, not stack-gas CEMS; not r13 FBG glaze / Frostlip quench / Oxbow VRFB; not r14 BOTDA / QCM-D / MsS T(0,1) / Raman DTS-as-compensation; not r15 SAW torque / CRDS HF / PGNAA; not r16 IFOG / transmon readout / hyperspectral crop; not r17 MEMS accel array / muon ore-pass / industrial x-ray DR; not r18 optogenetic PV / 905 nm LiDAR snow / clamp-on transit-time; not r19 LIBS Cu / QEPAS DGA / LFV Al; not r20 Kaplan LDV / THz-TDS radome moisture / ECT capacitance CFB; not r21 THz-TDS bondline / ECA FSW lift-off / LIBS C; not r22 ECT pneumatic riser / TDLAS NH3 / LIBS tap; not r23 lock-in thermography CFRP / PAUT TFM girth / EN CUI; not r24 RUS porcelain / N-16 transit-time loop / helium RGA; not r25 Faraday FOCT / blade tip-timing / acoustic pyrometry; not r26 SPR cyanide / VW viscometer / MW cavity moisture; not r27 MFL AST / NMR T2 / Cs-137 densitometry; not r28 MFL ILI / JNT / CRNS; not r29 Coriolis bitumen / CARS TIT / Zn-Ka XRF; not r30 Mössbauer FCC / GB-InSAR tailings / ellipsometry PECVD; not r31 CTA hot-wire / rhodium SPND / LII soot; not r32 PALS / 14N NQR / SFRA; not r33 digital shearography hull / hydrogen permeation / FMCW BOF lining; not r34 handheld XRF Cr-Kα / Coriolis tube-twist / GPR liner cover; not r35/r37 mud-pulse / Barkhausen / Lamb-wave; not r36 longitudinal BGO Pockels / pulsed eddy current riser / confocal chromatic; not r38 spectral-domain OCT / DCPD / impact-echo; not r39 phosphor-lifetime / vortex-shedding / GWR; not r40 He-3 neutron-backscatter / Kr-85 beta / Raman OH-CH; not r41–r43 cyclotron BPM / alanine EPR / ADCP ice-jam; not r44 TOFD remaining ligament / laser-flash Parker / TDR remaining-length; not r45 Seebeck ferrite / coda-wave / LPR; not r46 paramagnetic O2 / TOFD / TEOM; not r47 Faraday magmeter / PDA d32 / acoustoelastic birefringence; not r48 C-SAM / FDS tanδ / MCSA; not r49 EMAT SH / FBRM D50 / ACFM; not r50 in-flight OFDR / XRD sin2psi / FBRM remaining-chord. Plants not reused: Nettlewake, Frostlip, Oxbow, Rift-Caldera-3, Skarv-Naze GN-14, Orinoco-Span OD-12, Kilncrag KC-8, Rookspit RS-4, Spindrift SD-12, Thistlemere TM-6, Murkspit MS-6, Culmholt CH-5, Gorsekettle GK-5, Flintspit FG-8, Wharfleck WD-11, Cobblemere CM-5, Vellumkettle VK-4, Lanternfell LF-6, Greyfen KCTC-7, Pellucid IRRAD-P4, Whitefork WF-9, Cinderholt CH-7, Ashfen AH-4, Siltfen SF-9, Charkholt CH-6, Siltmere SM-7, Wickmere WM-8, Woldfen WF-4, Gullmere GM-5, Kettermere KM-6, Mirebank MB-5, Terncrag TC-4, Quaycrag QC-6, Copsefell CF-5, Heatherfen HF-7.

This round plants three NEW leftover-mill families that r13–r53 never harvested as leads: wire-mesh remaining void fraction, UCI remaining hardness, and magnetoacoustic-emission remaining case depth.

Adjacencies declared in-pair then kept physically distinct:
- **163 wire-mesh void** is electrode-current holdup on a BWR steam riser, not ECT capacitance tomography (r20/r22), not GWR foam (r39), not He-3 neutron-backscatter (r40), not N-16 (r24), not Coriolis (r29/r34).
- **164 UCI remaining hardness** is vibrating-rod frequency-shift HV on a duplex overlay weld, not RUS porcelain (r24), not Barkhausen (r35/r37), not Seebeck ferrite (r45), not SAW torque (r15), not EMAT SH (r49), not Leeb rebound, not chilled-mirror dew-point (r51).
- **165 MAE remaining case** is magnetoacoustic emission under AC magnetization on a carburized pinion, not Barkhausen (r35/r37), not ACFM (r49), not MFL (r27/r28), not EMAT SH (r49), not RUS (r24), not Seebeck ferrite (r45).

## Round 54 batch summary (3 pairs, 6 trajectories)

| id | modality (NEW family) | domain | decisions | headline |
|----|----------------------|--------|-----------|----------|
| nelb-r54-163 | wire-mesh remaining void fraction of a BWR steam riser (1−I/I_liq, Meshveil last-campaign denial, 18 min riser soak floor) | Larchmere Boiler LM-4 riser R-7 (invented): 1.00−2.00/8.00 reconstructs 0.750 while Meshveil still reads 0.120 and skin 318 C | MODIFY (+0.40) / ACCEPT (+0.35) | serialized `1.00-2.00/8.00=0.750` and `4.00*0.750*4.00=12.00`; conjunctive SOP (α AND SNR) forbids keep-1.00 power; three-party collusion includes the Meshveil infra owner; companion t2 0.80 hold, plant trip refused; sim_or_real=designed |
| nelb-r54-164 | UCI remaining hardness of a duplex overlay weld (k_u·Δf HV, Uciveil last-good denial, 24 min hold floor) | Quernspit Overlay QS-3 weld W-9 (invented, HIL cell in Uci-HIL-4): 4.00·30.00 reconstructs 120.00 HV while Uciveil still reads 220 HV and a cloned badge is at the overlay booth | REJECT (+0.43) / MODIFY (+0.34) | serialized `4.00*30.00=120.00` and `0.100*120.00=12.00`; keep-weld refused; NDT tech Ivo Marn exonerated (shoe ammeter + LVDT + canteen clock); companion t2 weld+shoe quarantine; sim_or_real=hil |
| nelb-r54-165 | magnetoacoustic-emission remaining case of a carburized pinion (k_m·E/I mm, Maeveil last-campaign denial, 12 min scan floor) | Hearthspit Gear HS-4 pinion P-6 (invented, simulated MAE-SIM-3): 0.400·9.00/3.00 reconstructs 1.20 mm while Maeveil still reads 2.80 mm and cell TC 18 C | ACCEPT (+0.41) / REJECT (+0.36) | serialized `0.400*9.00/3.00=1.20`; `6.00/5.00=1.20`; bounded ACCEPT of P-6 only; P-7..P-9 out of scope; companion t2 REJECTS skip-scan; sim_or_real=simulated |

Decision spread: MODIFY / ACCEPT / REJECT / MODIFY / ACCEPT / REJECT — **2A/2M/2R**. All three enums used, and all three sit on **leads**. Provenance spread: designed / hil / simulated (one each; never live-plant). IDs `nelb-r54-163`…`165` plus t1/t2 suffixes.

## Raster sidecar
Every record carries `raster` + top-level `gate_snn` + `gate_compute`. Windows {wins[0]:.0f}/{wins[1]:.0f}/{wins[2]:.0f} ms; `window_s == window_ms/1000` exactly; `spikes == round(neurons·rate·window_s)` with zero slack ({n_sp[0]}/{n_sp[1]}/{n_sp[2]} at {rates[0]}/{rates[1]}/{rates[2]} Hz over {n_neu[0]}/{n_neu[1]}/{n_neu[2]} neurons); `energy_pJ = spikes·23` and `energy_uJ = spikes·23e-6` exact ({n_sp[0]*23}/{n_sp[1]*23}/{n_sp[2]*23} pJ). Routing source/target + 3-entry tables + `third_factor` on all three (modulators {tfs[0]} / {tfs[1]} / {tfs[2]}; τe {taus[0]}/{taus[1]}/{taus[2]} s as consistent `tau_e_s`+`tau_e_ms` pairs). Excerpts integer `t_us`, in-window, `neuron_id`-bounded, sorted, full-window by construction, per-spike amplitude with adaptation (0.82**k) plus noise. ISI histograms from the full window, bins ≥1 ms, counts sum to `spikes − distinct_active_neurons` ({isis[0]}/{isis[1]}/{isis[2]}). Same-neuron gaps ≥1100 µs pre-round, ≥1000 µs serialized. `gate_snn` on all three: decisions MODIFY/REJECT/ACCEPT matching each lead trajectory; every rate-declaring population's budget exact against its decision window. `gate_compute.per_check` windows 32–40 ms, budgets exact ({gc[0]} / {gc[1]} / {gc[2]}). Main streams: {events[0]}/{events[1]}/{events[2]} events (inside the 5–40 cap), strictly increasing `t_rel_ms` only (no `t_ms` mix), same-channel refractory ≥0.8 ms (163 WMS pair at 1.5 ms, 164 UCI pair at 1.2 ms, 165 MAE pair at 1.5 ms).

## Self-critique

### Edge cases added vs still thin
- **Added:** first wire-mesh remaining-void family on a BWR steam riser with a recomputable α=1−I/I_liq (`0.750`) plus steam-carry identity (`12.00 kg/s`) and three-party collusion including the Meshveil infra owner; first UCI remaining-hardness family on a duplex overlay weld with recomputable HV=k_u·Δf (`120.00 HV`) and modulus identity (`12.00 GPa`), plus a resolved-innocent NDT tech (shoe ammeter + LVDT + canteen clock, not last-badge-at-booth); first magnetoacoustic-emission remaining-case family on a carburized pinion with recomputable d=k_m·E/I (`1.20 mm`) plus wavelength identity; first bounded ACCEPT whose out-of-scope clause is adjacent pinions rather than a hopper/taphole/dump cap; operational t2 on all three (0.80 hold, weld+shoe quarantine, skip-scan refusal); provenance trio designed/hil/simulated; 18 min / 24 min / 12 min slow floors in-stream.
- **Still thin:** (i) 163's I_liq is a lumped liquid calibration, not a temperature / conductivity table — a 20 K coolant hop that fakes 0.750 inside a 0.120 Meshveil corridor is unwritten; (ii) 164's k_u is a lumped frequency-to-HV gain, not a shoe-wear / coupling map, so a worn-diamond hop that fakes 120 HV is unwritten; (iii) 165's k_m is a lumped MAE calibration, not a lift-off / permeability table, so a coupling pad that fakes 1.20 mm is unwritten; (iv) vendor-only as a *lead* REJECT on a plant with *no* independent WMS/UCI/MAE installed yet remains slightly harder — 163/164 still have plant heads; (v) stream amplitudes remain authored constants (raster draws are the only seeded noise).

### Realism of noise / temporal fidelity
- Strong: 163's 0.750, 12.00 kg/s, and 18.0 min soak (`6000+1080=7080 s`) recompute from the record; 164's 120.00 HV, 12.00 GPa, and 24.0 min hold (`2820+1440=4260 s`) recompute; 165's 1.20 mm, λ 1.20 mm, and 12.0 min scan (`6000+720=6720 s`) recompute. Raster adaptation (0.82**k plus 4% noise) and the 1.2–1.5 ms physics pairs give the 5–40 stream a raster-scale motif without violating 0.8 ms same-channel refractory.
- **Gaps, honestly:** (i) 5–40 cap still forces heavy thinning (kHz wire-mesh current kept as 4 I points; kHz UCI rod kept as 4 Δf points; kHz MAE burst kept as 4 E points); (ii) 163's post-isolate 0.700 is a later sample, not a closed-loop power controller; (iii) 164 HIL cell times an in-service weld stop that the stream does not independently witness on a second live weld until the shoe is imaged; (iv) no gate_snn input→output volley pair at raster resolution this round (r04-a1 already staged that).

### Training value (SNN/LSM + agentic)
Distillation targets: WMS α=1−I/I_liq and mdot=k_m·α·v heads; isolate-floor derate vs keep-1.00 vs plant trip; Meshveil-infra collusion; UCI HV=k_u·Δf head plus modulus identity; stop-floor refuse vs keep-weld vs vessel dump; shoe/LVDT/canteen exoneration; MAE d=k_m·E/I and λ=v/f heads; bounded ACCEPT with pinion-out-of-scope; skip-scan refusal under takt. Agentic value concentrates in three patterns: reconstruction-as-SoT on a physical void/hardness/case the raw corridor cannot see, earned ACCEPT with an explicit physical out-of-scope object (P-7..P-9), and stop-then-hold so a REJECT does not become a vessel/plant kill.

## What a later leftover-mill round should add (next densification target)
1. **Temperature / conductivity I_liq table** on a non-LM-4 riser so a coolant hop fakes 0.750 inside a 0.120 last-campaign corridor, closing 163's lumped-calibration gap.
2. **Shoe-wear / coupling map** on a non-QS-3 UCI rod so a worn-diamond hop fakes 120 HV while mean Δf looks like spec.
3. **Lift-off / permeability table** on a non-HS-4 MAE yoke so a coupling pad fakes 1.20 mm inside a 2.80 mm last-campaign corridor.
4. **Vendor-only as a lead REJECT** on a plant that has no independent WMS/UCI/MAE installed yet (163/164 still had plant heads).
5. **Do not restage** VOD-SNN replay, pharma cold-chain, CEMS, FBG glaze, Frostlip quench, Oxbow VRFB, IFOG, transmon, hyperspectral, MEMS array, muon ore-pass, industrial x-ray, optogenetic stim, 905 nm LiDAR snow, clamp-on transit-time, LIBS, QEPAS, LFV, Kaplan LDV, THz-TDS, ECT capacitance, TDLAS NH3, lock-in thermography, PAUT TFM, EN CUI, RUS porcelain, N-16 loop flow, helium RGA, Faraday FOCT, blade tip-timing, acoustic pyrometry, SPR, vibrating-wire, microwave-cavity, MFL, NMR T2, nucleonic SG, JNT, CRNS, Coriolis, CARS, XRF, Mössbauer, GB-InSAR, ellipsometry, SPND, LII, PALS, NQR, SFRA, digital shearography, hydrogen permeation, FMCW lining, GPR, Pockels, pulsed eddy current, confocal chromatic, OCT, DCPD, impact-echo, mud-pulse, Barkhausen, Lamb-wave, phosphor-lifetime, vortex-shedding, GWR, He-3 backscatter, Kr-85 beta, Raman OH-CH, Raman DTS compensation, cyclotron BPM, alanine EPR, ADCP ice-jam, TOFD, laser-flash Parker, TDR, Seebeck, coda-wave, LPR, paramagnetic O2, TEOM, Faraday magmeter, PDA d32, acoustoelastic, C-SAM, FDS tanδ, MCSA, EMAT SH, FBRM, ACFM, OFDR, XRD sin2psi, Larchmere LM-4 WMS, Quernspit Uci-HIL-4, or Hearthspit HS-4 MAE. Do not restage r51 chilled-mirror dew-point, r51 Gardon, r51 DIC, r52 CLD NOx, r52 proximity orbit, r52 thermal-mass capillary, r53 ER probe, r53 Fabry-Perot choke, r53 oil-debris, r50 OFDR/XRD/FSM. Greyfen KCTC-7, Pellucid IRRAD-P4, and Whitefork WF-9 remain unused plant names and must not be reused. Do not steal r50–r53 IDs `151`–`162`.

## Verification
`batch-r54.jsonl`: 3 lines, `json.loads`-clean (allow_nan=False), {sizes[0]}/{sizes[1]}/{sizes[2]} bytes (file {{BATCH.stat().st_size}}, sha256 `{file_sha}`). Staged at `/tmp/nelb-r54/` only. Repo gates: `check_records.check_jsonl` with `FactoryStaging(enabled=True)` → 0 errors, 0 warnings, kinds `{{bridge_pair: 3}}`; `python3 pipelines/check_records.py --strict /tmp/nelb-r54` → 0/0; `curate_bridge.raster_status(..., require_raster=True, require_routing_table=True)` → raster_valid and gate_snn_valid true, empty reason codes; `curate_record(...)` → 3× retain / `BRIDGE_EVENTS_ALREADY_GLOBALLY_ORDERED`; `verify_batch_for_frontier(strict=True)` → 3 verified, 0 inconclusive, 0 failed; `python3 pipelines/spike_probe.py --strict /tmp/nelb-r54/batch-r54.jsonl` → loaded 3, unloadable 0, problems [], third_factor_routes 3, gate_snn_records 3, spikes {spikes}, energy_pJ {energy}. Build-time asserts: global time order; same-channel ≥0.8 ms; 5–40 events ({events[0]}/{events[1]}/{events[2]}); excerpt integer bounds, neuron bounds, sort, 1 ms per-neuron floor; ISI identity {isis[0]}/{isis[1]}/{isis[2]}; spike budgets exact; energy pJ/µJ exact; reward totals equal two-decimal component sums ({reward_s}); gate_snn decisions match lead `safety_decision.decision`; `state.sim_or_real` ∈ {{designed, hil, simulated}}; `meta.round=54`, `meta.factory=neuromorphic-event-language-bridge`, `meta.generator=grok-4.6`, `meta.run_label=2026-09-02-final-heavy`; `meta.rights` 15-key RM-793 stamp (`intended_use=research_only`, `linear_issue=RM-793`, `generated_at={GENERATED_AT}`); no hidden-reasoning keys; no `provenance` objects; no live-plant claims; no `training_ready`; all 9 record/trajectory ids unique. Raster seeds 202654163/202654164/202654165, MT19937.

Honest novelty accounting: 3/3 modality families are new versus the whole committed factory and versus staged leftover-mill r13–r49 (and in-flight r45 Seebeck/coda/LPR and r50 OFDR/XRD/FBRM). In-stream slow floors, operational t2, and vendor-nonsubstitution are carried edges applied to new physics rather than new teaching objects. Three-party collusion and exoneration were already taught on r13 quench/VRFB and r49 FBRM, so those heads are carried onto new sensors. Against that: bounded-accept-with-scope-limit, reconstruction-as-SoT, conjunctive SOP, and custody vocabulary are carried; the 5–40 cap is a density constraint not a new teaching object; 41 prior leftover-mill rounds already taught custody/governance at high sophistication. Net: about two-fifths of the round's scenario/edge mass is genuinely novel.

Novel coverage: 40%
"""
    # fix doubled braces for file size interpolation
    notes = notes.replace("{BATCH.stat().st_size}", str(BATCH.stat().st_size))
    NOTES.write_text(notes, encoding="utf-8")
    print("wrote", NOTES, "bytes", NOTES.stat().st_size)


def main():
    records = [rec_163(), rec_164(), rec_165()]
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
