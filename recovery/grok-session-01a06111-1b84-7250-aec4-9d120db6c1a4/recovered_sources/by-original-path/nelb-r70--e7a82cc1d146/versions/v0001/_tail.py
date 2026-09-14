def occupancy_preflight():
    claimed = (
        "beltveil",
        "slagmere sinter",
        "idler-belt remaining",
        "pondveil",
        "mirebrook neutralization",
        "glass remaining ph",
        "nirveil",
        "pulpmere paper",
        "nir remaining moisture",
        "ph-hil-6",
        "nir-sim-5",
        "nessa crag",
        "olan brisk",
        "kellan muir",
        "lira voss",
        "ryn pever",
        "nelb-r70-211",
        "nelb-r70-212",
        "nelb-r70-213",
        "gritfen mixing",
    )
    steal = (
        "viscveil",
        "gleamveil",
        "admveil",
        "karlveil",
        "polveil",
        "headveil",
        "nozzveil",
        "sodaveil",
        "tubeveil",
        "nephveil",
        "calorveil",
        "ventveil",
        "kathveil",
        "deaerveil",
        "owlmere",
        "fogmere",
        "stoatfen",
        "sallowfen",
        "wychholt",
        "marshspit",
        "limewhin",
        "mallowholt",
        "wetherholt",
        "floatveil",
        "fidveil",
        "rotorveil",
        "doasveil",
        "oxveil",
        "cellveil",
        "irisveil",
        "pyroveil",
        "fluoveil",
        "orifveil",
        "lampveil",
        "condveil",
        "brixveil",
        "chlorveil",
        "spotveil",
        "flameveil",
        "sternveil",
        "pellveil",
        "rangveil",
        "gageveil",
        "beadveil",
        "shiftveil",
        "cutveil",
        "polarveil",
        "na-hil-5",
        "tube-sim-4",
        "gloss-hil-4",
        "adm-sim-3",
        "pol-hil-4",
        "hydro-sim-6",
        "rindleholt steam",
        "woadfen chlorate",
        "pellmire boiler",
        "quillmere sugar",
    )
    hits = []
    root = Path("/tmp")
    scan = (
        sorted(root.glob("nelb-r*/NOTES-r*.md"))
        + sorted(root.glob("nelb-r*/gen_r*.py"))
        + sorted(root.glob("nelb-r*/records_block.py"))
        + sorted(root.glob("nelb-r*/_recs.py"))
        + sorted(root.glob("nelb-r*/recs.py"))
        + sorted(root.glob("nelb-r*/_recs_and_tail.py"))
        + sorted(root.glob("nelb-r*/_rec*.py"))
        + sorted(root.glob("nelb-r*/_new*.py"))
        + sorted(root.glob("nelb-r*/_front*.py"))
    )
    for n in scan:
        if "nelb-r70" in str(n):
            continue
        text = n.read_text(encoding="utf-8", errors="replace").casefold()
        for b in claimed:
            if b in text:
                hits.append(f"{n}:{b}")
    if hits:
        raise RuntimeError(f"r70 family/plant collision {hits}")
    blob = json.dumps([rec_211(), rec_212(), rec_213()], ensure_ascii=False).casefold()
    for s in steal:
        if s in blob:
            raise RuntimeError(f"r70 stole occupied family {s}")


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
        if rec["meta"]["round"] != 70:
            raise RuntimeError("round stamp")
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
        BATCH, "batch-r70.jsonl", staging=FactoryStaging(enabled=True)
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
            source_path="batch-r70.jsonl",
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
    notes = f"""# Neuromorphic Event + Language Bridge — NOTES round 70
Run: 2026-09-02-final-heavy · Factory: neuromorphic-event-language-bridge · Generator: grok-4.6 · Output: `batch-r70.jsonl` (3 paired artifacts, 6 ThalamicTrajectories)
Rights: RM-793 research-only (SpaceXAI/xAI grok-4.6, SuperGrok Heavy chat). Not training_ready. Do not publish into `outputs/raw/` from this generator; operator uses `pipelines/round_txn.py`. Staged only at `/tmp/nelb-r70/`.

## Context / de-duplication
Prior corpus read: 2026-08-30 NOTES-r01–r04, 2026-08-17-w3 NOTES-r12 family table, `/tmp/nelb-r13-holes.md` + `/tmp/nelb-r13-premises.md`, staged `/tmp/nelb-r13` through `/tmp/nelb-r66` complete batches/NOTES plus in-flight `/tmp/nelb-r67` (coulometric Karl Fischer transformer water / polarimetric sucrose / hydrostatic dP phosphoric-acid level, ids `202`–`204`), `/tmp/nelb-r68` and `/tmp/nelb-r69` head-only stubs. IDs: r13=`040`–`042` … r66=`199`–`201`, reserved r67–r69=`202`–`210`, this round `nelb-r70-211`…`213` as assigned. Envelope cloned from complete r65 (`language_view.trajectory` + operational t2 + `spike_events` + `raster` + `gate_snn` + `isi_histogram` + `routing.third_factor` + 15-key RM-793 `meta.rights`).

Banned this round (committed + staged leftover-mill r13–r66 and in-flight r67–r69 envelopes): not VOD-SNN replay, not pharma cold-chain, not stack-gas CEMS; not r13 FBG glaze / Frostlip quench / Oxbow VRFB; not r14 BOTDA / QCM-D / MsS T(0,1); not r15 SAW torque / CRDS HF / PGNAA / Gorse-UV DOAS-as-witness / wet-belt scale as PGNAA witness; not r16 IFOG / transmon readout / hyperspectral crop; not r17 MEMS accel array / muon ore-pass / industrial x-ray DR; not r18 optogenetic PV / 905 nm LiDAR snow / clamp-on transit-time; not r19 LIBS Cu / QEPAS DGA / LFV Al; not r20 Kaplan LDV / THz-TDS radome moisture / ECT CFB; not r21 THz-TDS bondline / ECA FSW lift-off / LIBS C; not r22 ECT pneumatic riser / TDLAS NH3 / LIBS tap; not r23 lock-in thermography CFRP / PAUT TFM girth / EN CUI; not r24 RUS porcelain / N-16 transit-time loop / helium RGA; not r25 Faraday FOCT / blade tip-timing / acoustic pyrometry; not r26 SPR cyanide / VW viscometer / MW cavity moisture; not r27 MFL AST / NMR T2 / Cs-137 densitometry; not r28 MFL ILI / JNT / CRNS; not r29 Coriolis bitumen / CARS TIT / Zn-Ka XRF; not r30 Mössbauer FCC / GB-InSAR tailings / ellipsometry PECVD; not r31 CTA hot-wire / rhodium SPND / LII soot; not r32 PALS / 14N NQR / SFRA; not r33 digital shearography hull / hydrogen permeation / FMCW BOF lining; not r34 handheld XRF Cr-Kα / Coriolis tube-twist / GPR liner cover; not r35/r37 mud-pulse MWD / Barkhausen / Lamb-wave; not r36 Pockels GIS / PEC coated riser / confocal chromatic; not r38 OCT TBC / DCPD girth / impact-echo containment; not r39 phosphor-lifetime / vortex-shedding / GWR foam; not r40 He-3 neutron-backscatter / Kr-85 beta / 532 nm Raman; not r41/r42/r43 cyclotron BPM / alanine EPR / ADCP ice-jam; not r44 TOFD ligament / laser-flash Parker / TDR remaining-length; not r45 RFEC boiler tube / ACFM jacket node / LPR cooling header / Seebeck remaining ferrite; not r46 paramagnetic O2 / TOFD ligament / TEOM PM; not r47 magmeter slurry / PDA Sauter-mean / acoustoelastic residual; not r48 C-SAM IGBT void / FDS tanδ bushing / MCSA broken-bar; not r49 EMAT SH coil / FBRM chord D50 / ACFM jack-up; not r50 OFDR hoop-strain / XRD sin²ψ / FSM jumper; not r51 Gardon heat flux / chilled-mirror dew-point / DIC hoop-strain; not r52 CLD NOx / API-670 proximity / thermal-mass capillary; not r53 ER remaining wall / Fabry-Perot choke / inductive oil-debris; not r54 wire-mesh void / UCI hardness / MAE remaining case; not r55 FID THC / turbine k-factor / magnetostrictive waveguide level; not r56 IRIS HEX wall / ratio pyrometer / UV-fluorescence oil-in-water; not r57 orifice-plate dP / PID VOC / four-electrode conductivity; not r58 critical-angle Brix / WLI thickness / annubar averaging-pitot; not r59 UV-DOAS SO2 / Al2O3 moisture / load-cell hopper mass; not r60 laser-triangulation strip / FID VOC RTO / dielectric water-cut; not r61 Stern-Volmer DO / pellistor LEL / FMCW tank-radar; not r62 laser-triangulation cold-mill / pellistor booth / ultrasonic Doppler slurry; not r63 Wobbe calorific / 90-degree nephelometric turbidity / cation conductivity / amperometric chlorine; not r64 venturi steam-flow / katharometer H2 / Clark polarographic DO; not r65 sonic-nozzle remaining mass-flow / sodium-ion remaining Na / vibrating-tube remaining density; not r66 Ubbelohde remaining kinematic viscosity / 60-degree remaining gloss / RF-admittance remaining level; not r67 coulometric Karl Fischer remaining water / polarimetric remaining sucrose / hydrostatic remaining dP level. Plants not reused: Nettlewake, Frostlip, Oxbow, Thornmere, Marlfell, Birchfen, Yewspit, Brimwhin, Hagholt, Mirewhin, Lacquerfen, Pitchshaw, Mireholt, Torholt, Bramblefen, Thornfell, Quillmere, Pewterholt, Rindleholt, Woadfen, Pellmire, Owlmere, Fogmere, Stoatfen, Sallowfen, Wychholt, Marshspit, Ashwhin, Wetherholt, Mallowholt, Sedgeholt, Limewhin, Kelpholt, plus the r13–r69 plant list.

This round introduces three unused industrial families (idler-belt remaining mass-flow, glass remaining pH, NIR remaining moisture) on new invented plants. r13-holes cyclotron/alanine/ADCP and r67–r69 in-flight families are not restaged.

Adjacencies declared in-pair then kept physically distinct:
- **211 idler-belt mass-flow** is an idler load-cell k_b·(F−F0)·v remaining slip of a sinter strand, not r15 wet-belt scale as a PGNAA witness, not r59 strain-gauge load-cell hopper static mass, not r66 RF-admittance silo level, not r67 hydrostatic dP tank level, not r29/r34 Coriolis, not r65 sonic-nozzle, not r64 venturi, not r52 thermal-mass, not r55 turbine k-factor.
- **212 glass pH** is a Nernst 7−V/S remaining pH of a neutralization sump, not r65 sodium-ion ISE, not r55/r57 zirconia Nernst O2, not r64 Clark polarographic DO, not r63 amperometric chlorine, not r57 four-electrode conductivity-as-SoT, not r67 Karl Fischer transformer water, not r67 polarimetric sucrose.
- **213 NIR moisture** is an absorbance k_n·(A−A0) remaining moisture of a paper sheet, not r26 MW cavity moisture, not r59 Al2O3 moisture, not r51 chilled-mirror dew-point, not r20 THz-TDS radome moisture, not r67 Karl Fischer transformer water, not r16 hyperspectral crop, not r40 532 nm Raman.

## Round 70 batch summary (3 pairs, 6 trajectories)

| id | modality (NEW family) | domain | decisions | headline |
|----|----------------------|--------|-----------|----------|
| nelb-r70-211 | idler-belt remaining mass-flow of a sinter strand (k_b·(F−F0)·v kg/s, Beltveil last-good denial, 18 min soak floor) | Slagmere Sinter SM-7 strand B-3 (invented): 1.50*(12.00-4.00)*2.00 reconstructs 24.00 kg/s while Beltveil still reads 3.20 kg/s | REJECT (+0.43) / MODIFY (+0.34) | serialized `1.50*(12.00-4.00)*2.00=24.00`; `24.00/(1.50*2.00)=8.00`; conjunctive SOP (mdot AND SNR) forbids continue-feed; three-party collusion includes the idler-cloud infra owner; companion t2 strand-soak hold, header ESD refused; sim_or_real=designed |
| nelb-r70-212 | glass remaining pH of a neutralization sump (7−V/S, Pondveil last-good denial, 24 min buffer floor) | Mirebrook Neutralization MB-4 sump S-2 (invented, HIL dummy in PH-HIL-6): 7.00-80.00/20.00 reconstructs pH 3.00 while Pondveil still reads 6.80 | MODIFY (+0.40) / ACCEPT (+0.35) | serialized `7.00-80.00/20.00=3.00` and `1000.0*10**(-3.00)*12.00=12.00`; keep-sump refused; electrode tech Lira Voss exonerated (missing slope-cal AE, UTC vs UTC+2); companion t2 new-electrode restart; sim_or_real=hil |
| nelb-r70-213 | NIR remaining moisture of a paper sheet (k_n·(A−A0) wt%, Nirveil last-good denial, 12 min survey floor) | Pulpmere Paper PM-6 reel R-3 (invented, simulated NIR-SIM-5): 4.00*(8.00-2.00) reconstructs 24.00 wt% while Nirveil still reads 6.20 wt% | ACCEPT (+0.41) / REJECT (+0.36) | serialized `4.00*6.00=24.00`; `24.00/100*50.00=12.00`; bounded ACCEPT of R-3 only; R-1..R-2 out of scope; companion t2 REJECTS skip-survey; sim_or_real=simulated |

Decision spread: REJECT / MODIFY / MODIFY / ACCEPT / ACCEPT / REJECT — **2A/2M/2R**. All three enums used, and all three sit on **leads**. Provenance spread: designed / hil / simulated (one each; never live-plant). IDs `nelb-r70-211`…`213` plus t1/t2 suffixes.

## Raster sidecar
Every record carries `raster` + top-level `gate_snn` + `gate_compute`. Windows {wins[0]:.0f}/{wins[1]:.0f}/{wins[2]:.0f} ms; `window_s == window_ms/1000` exactly; `spikes == round(neurons·rate·window_s)` with zero slack ({n_sp[0]}/{n_sp[1]}/{n_sp[2]} at {rates[0]}/{rates[1]}/{rates[2]} Hz over {n_neu[0]}/{n_neu[1]}/{n_neu[2]} neurons); `energy_pJ = spikes·23` and `energy_uJ = spikes·23e-6` exact ({n_sp[0]*23}/{n_sp[1]*23}/{n_sp[2]*23} pJ). Routing source/target + 3-entry tables + `third_factor` on all three (modulators {tfs[0]} / {tfs[1]} / {tfs[2]}; τe {taus[0]}/{taus[1]}/{taus[2]} s as consistent `tau_e_s`+`tau_e_ms` pairs). Excerpts integer `t_us`, in-window, `neuron_id`-bounded, sorted, full-window by construction, per-spike amplitude with adaptation (0.82**k) plus noise. ISI histograms from the full window, bins ≥1 ms, counts sum to `spikes − distinct_active_neurons` ({isis[0]}/{isis[1]}/{isis[2]}). Same-neuron gaps ≥1100 µs pre-round, ≥1000 µs serialized. `gate_snn` on all three: decisions REJECT/MODIFY/ACCEPT matching each lead trajectory; every rate-declaring population's budget exact against its decision window. `gate_compute.per_check` windows 32–40 ms, budgets exact ({gc[0]} / {gc[1]} / {gc[2]}). Main streams: {events[0]}/{events[1]}/{events[2]} events (inside the 5–40 cap), strictly increasing `t_rel_ms` only (no `t_ms` mix), same-channel refractory ≥0.8 ms (211 idler-belt pair at 1.4 ms, 212 glass-pH pair at 1.2 ms, 213 NIR pair at 1.5 ms).

## Self-critique

### Edge cases added vs still thin
- **Added:** first idler-belt remaining-mass-flow family on a sinter strand with a recomputable mdot=k_b·(F−F0)·v (`24.00 kg/s`) plus force-tare identity and three-party collusion including the idler-cloud infra owner; first glass remaining-pH family on a neutralization sump with recomputable pH=7−V/S (`3.00`) and acid-load identity, plus a resolved-innocent electrode tech (timezone-skipped slope-cal, not last-to-badge); first NIR remaining-moisture family on a paper sheet with recomputable M=k_n·(A−A0) (`24.00 wt%`) plus water-mass identity; bounded ACCEPT whose out-of-scope clause is adjacent reels rather than a hopper/taphole/dump cap; operational t2 on all three (strand-soak hold, new-electrode restart, skip-survey refusal); provenance trio designed/hil/simulated; 18 min / 24 min / 12 min slow floors in-stream.
- **Still thin:** (i) 211's k_b is a lumped idler gain, not a weigh-span / belt-stiffness table — a speed hop that fakes 24.00 kg/s inside a 3.20 kg/s Beltveil corridor is unwritten; (ii) 212's S is a lumped 20.00 mV/pH, not an isotherm / junction-potential map, so a temperature hop that fakes pH 3.00 is unwritten; (iii) 213's k_n is a lumped absorbance-to-moisture factor, not a basis-weight / scattering table, so a caliper hop that fakes 24.00 wt% inside a 6.20 last-good is unwritten; (iv) vendor-only as a *lead* REJECT on a plant with *no* independent idler-belt/glass-pH/NIR head installed yet remains slightly harder — 211/212 still have plant heads; (v) stream amplitudes remain authored constants (raster draws are the only seeded noise); (vi) r67–r69 densification leftovers were left for those rounds' owners.

### Realism of noise / temporal fidelity
- Strong: 211's 24.00 kg/s, dF 8.00, and 18.0 min soak (`6000+1080=7080 s`) recompute from the record; 212's pH 3.00, n 12.00 mol/h, and 24.0 min buffer (`2820+1440=4260 s`) recompute; 213's 24.00 wt%, water 12.00 kg/h, and 12.0 min survey (`6000+720=6720 s`) recompute. Raster adaptation (0.82**k plus 4% noise) and the 1.2–1.5 ms physics pairs give the 5–40 stream a raster-scale motif without violating 0.8 ms same-channel refractory.
- **Gaps, honestly:** (i) 5–40 cap still forces heavy thinning (10 Hz idler-belt kept as 4 F points; 1 Hz glass pH kept as 4 V points; 10 Hz NIR kept as 4 A points); (ii) 211's post-stop 36.00 kg/s is a later sample, not a closed-loop soak controller; (iii) 212 HIL coupon times an in-service sump isolate that the stream does not independently witness on a second live sump until the new electrode starts; (iv) no gate_snn input→output volley pair at raster resolution this round (r04-a1 already staged that).

### Training value (SNN/LSM + agentic)
Distillation targets: idler-belt mdot=k_b·(F−F0)·v reconstruction head plus force-tare identity; conjunctive isolate floor vs continue-feed vs header ESD; Beltveil-infra collusion; glass pH=7−V/S head plus acid-load identity; isolate-floor sump vs keep-whole vs acid dump; exoneration against last-to-badge social pressure; NIR M=k_n·(A−A0) and water identities; bounded ACCEPT with reel-out-of-scope; skip-survey refusal under survey takt. Agentic value concentrates in three patterns: reconstruction-as-SoT on a physical mass-flow/pH/moisture load the raw corridor cannot see, earned ACCEPT with an explicit physical out-of-scope object (R-1..R-2), and stop-then-hold so a REJECT does not become a header/dump/line kill.

## What a later leftover-mill round should add (next densification target)
1. **Weigh-span / belt-stiffness table** on a non-SM-7 strand so a speed hop fakes 24.00 kg/s inside a 3.20 kg/s Beltveil corridor, closing 211's lumped-k_b gap.
2. **Isotherm / junction-potential map** on a non-MB-4 sump so a thermal hop can fake pH 3.00 while mean electrode millivolt looks healthy.
3. **Basis-weight / scattering table** on a non-PM-6 reel so a caliper hop can fake 24.00 wt% inside a 6.20 last-good corridor.
4. **Vendor-only as a lead REJECT** on a plant that has no independent idler-belt/glass-pH/NIR head installed yet (211/212 still had plant heads).
5. **Do not restage** VOD-SNN replay, pharma cold-chain, CEMS, FBG glaze, Frostlip quench, Oxbow VRFB, IFOG, transmon, hyperspectral, MEMS array, muon ore-pass, industrial x-ray, optogenetic stim, 905 nm LiDAR snow, clamp-on transit-time, LIBS, QEPAS, LFV, Kaplan LDV, THz-TDS, ECT, TDLAS NH3, lock-in thermography, PAUT TFM, EN CUI, RUS porcelain, N-16 loop flow, helium RGA, Faraday FOCT, blade tip-timing, acoustic pyrometry, SPR, vibrating-wire, microwave-cavity, MFL, NMR T2, nucleonic densitometry, JNT, CRNS, Coriolis, CARS, XRF, Mössbauer, GB-InSAR, ellipsometry, CTA, SPND, LII, PALS, NQR, SFRA, digital shearography, hydrogen permeation, FMCW lining, GPR, Pockels, PEC, confocal, mud-pulse, Barkhausen, Lamb-wave, OCT, DCPD, impact-echo, cyclotron BPM, alanine EPR, ADCP, vortex-shedding, Kr-85 beta, 532 nm Raman, phosphor-lifetime, guided-wave-radar, paramagnetic O2, TOFD, TEOM, magmeter, PDA, acoustoelastic, C-SAM, FDS tanδ, MCSA, EMAT SH, FBRM, ACFM, OFDR, XRD sin²ψ, FSM, Gardon, chilled-mirror, DIC, CLD NOx, proximity orbit, thermal-mass, ER probe, Fabry-Perot, inductive debris, wire-mesh, UCI, MAE, IRIS, ratio pyrometer, UV-fluorescence oil-in-water, zirconia Nernst, PID VOC, contact pulse-echo, Rogowski, beta-attenuation, UV-DOAS, Al2O3, load-cell, laser-triangulation, FID VOC, dielectric water-cut, Stern-Volmer DO, pellistor LEL, FMCW tank-radar, ultrasonic Doppler, Wobbe, critical-angle Brix, amperometric chlorine, venturi steam-flow, katharometer H2, Clark polarographic DO, sonic-nozzle, sodium-ion, vibrating-tube, Ubbelohde, 60-degree gloss, RF-admittance, Karl Fischer, polarimetric sucrose, hydrostatic dP, Slagmere SM-7 idler-belt, Mirebrook PH-HIL-6, or Pulpmere NIR-SIM-5. Leave r67–r69 densification leftovers for those rounds' owners. Do not steal r55–r69 IDs `166`–`210`.

## Verification
`batch-r70.jsonl`: 3 lines, `json.loads`-clean (allow_nan=False), {sizes[0]}/{sizes[1]}/{sizes[2]} bytes (file {BATCH.stat().st_size}, sha256 `{{file_sha}}`). Staged at `/tmp/nelb-r70/` only. Repo gates: `check_records.check_jsonl` with `FactoryStaging(enabled=True)` → 0 errors, 0 warnings, kinds `{{bridge_pair: 3}}`; `python3 pipelines/check_records.py --strict /tmp/nelb-r70` → 0/0; `curate_bridge.raster_status(..., require_raster=True, require_routing_table=True)` → raster_valid and gate_snn_valid true, empty reason codes; `curate_record(...)` → 3× retain / `BRIDGE_EVENTS_ALREADY_GLOBALLY_ORDERED`; `verify_batch_for_frontier(strict=True)` → 3 verified, 0 inconclusive, 0 failed; `python3 pipelines/spike_probe.py --strict /tmp/nelb-r70/batch-r70.jsonl` → loaded 3, unloadable 0, problems [], third_factor_routes 3, gate_snn_records 3, spikes {spikes}, energy_pJ {energy}. Build-time asserts: global time order; same-channel ≥0.8 ms; 5–40 events ({events[0]}/{events[1]}/{events[2]}); excerpt integer bounds, neuron bounds, sort, 1 ms per-neuron floor; ISI identity {isis[0]}/{isis[1]}/{isis[2]}; spike budgets exact; energy pJ/µJ exact; reward totals equal two-decimal component sums ({reward_s}); gate_snn decisions match lead `safety_decision.decision`; `state.sim_or_real` ∈ {{designed, hil, simulated}}; `meta.round=70`, `meta.factory=neuromorphic-event-language-bridge`, `meta.generator=grok-4.6`, `meta.run_label=2026-09-02-final-heavy`; `meta.rights` 15-key RM-793 stamp (`intended_use=research_only`, `linear_issue=RM-793`, `generated_at={GENERATED_AT}`); no hidden-reasoning keys; no `provenance` objects; no live-plant claims; no `training_ready`; all 9 record/trajectory ids unique. Raster seeds 202609211/202609212/202609213, MT19937.

Honest novelty accounting: 3/3 modality families are new versus the whole committed factory and versus staged leftover-mill r13–r66 (and in-flight r67–r69 envelopes). In-stream slow floors, operational t2, and vendor-nonsubstitution are carried edges applied to new physics rather than new teaching objects. Three-party collusion and exoneration were already taught on r13 quench/VRFB and later leftover-mill rounds, so those heads are carried onto new sensors. Against that: bounded-accept-with-scope-limit, reconstruction-as-SoT, conjunctive SOP, and custody vocabulary are carried; the 5–40 cap is a density constraint not a new teaching object; 57 prior leftover-mill rounds already taught custody/governance at high sophistication. Net: about two-fifths of the round's scenario/edge mass is genuinely novel.

Novel coverage: 40%
"""
    NOTES.write_text(notes, encoding="utf-8")
    print("wrote", NOTES, "bytes", NOTES.stat().st_size)


def main():
    occupancy_preflight()
    records = [rec_211(), rec_212(), rec_213()]
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
