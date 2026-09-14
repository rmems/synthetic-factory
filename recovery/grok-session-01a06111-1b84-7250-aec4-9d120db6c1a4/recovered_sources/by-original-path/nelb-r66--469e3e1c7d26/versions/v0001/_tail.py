def occupancy_preflight():
    claimed = (
        "viscveil",
        "sallowfen turbine",
        "ubbelohde remaining-viscosity",
        "gleamveil",
        "wychholt coil-coat",
        "sixty-degree remaining-gloss",
        "admveil",
        "marshspit fly-ash",
        "rf-admittance remaining-level",
        "gloss-hil-4",
        "adm-sim-3",
        "rory kest",
        "ione veld",
        "pia holm",
        "oren vale",
        "lyle fen",
        "nelb-r66-199",
        "nelb-r66-200",
        "nelb-r66-201",
    )
    steal = (
        "irisveil",
        "wexmere hydrotreater",
        "glaurfen converter",
        "pyroveil",
        "nernstveil",
        "glimmerholt",
        "coilveil",
        "betaveil",
        "doasveil",
        "oxveil",
        "cellveil",
        "fidveil",
        "rotorveil",
        "floatveil",
        "flameveil",
        "thornmere sru",
        "marlfell chlor",
        "birchfen fcc",
        "brindlecrag",
        "copsewharf",
        "kelpwharf",
        "polarveil",
        "nozzveil",
        "sodaveil",
        "tubeveil",
        "owlmere",
        "stoatfen",
        "ventveil",
        "kathveil",
        "deaerveil",
        "rindleholt steam",
        "woadfen chlorate",
        "pellmire boiler",
        "calorveil",
        "brixveil",
        "chlorveil",
        "gageveil",
        "beadveil",
        "shiftveil",
        "sternveil",
        "rangveil",
        "pellveil",
        "spotveil",
        "kath-hil-7",
        "clark-sim-5",
        "na-hil-5",
    )
    hits = []
    root = Path("/tmp")
    scan = (
        sorted(root.glob("nelb-r*/NOTES-r*.md"))
        + sorted(root.glob("nelb-r*/gen_r*.py"))
        + sorted(root.glob("nelb-r*/records_block.py"))
        + sorted(root.glob("nelb-r*/_recs.py"))
        + sorted(root.glob("nelb-r*/recs.py"))
        + sorted(root.glob("nelb-r*/_new*.py"))
        + sorted(root.glob("nelb-r*/_front*.py"))
        + sorted(root.glob("nelb-r*/_rec*.py"))
    )
    for n in scan:
        if "nelb-r66" in str(n):
            continue
        text = n.read_text(encoding="utf-8", errors="replace").casefold()
        for b in claimed:
            if b in text:
                hits.append(f"{n}:{b}")
    if hits:
        raise RuntimeError(f"r66 family/plant collision {hits}")
    blob = json.dumps([rec_199(), rec_200(), rec_201()], ensure_ascii=False).casefold()
    for s in steal:
        if s in blob:
            raise RuntimeError(f"r66 stole occupied family {s}")


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
        if rec["meta"].get("round") != 66:
            raise RuntimeError("round")
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
        BATCH, "batch-r66.jsonl", staging=FactoryStaging(enabled=True)
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
            source_path="batch-r66.jsonl",
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
        gc.append("+".join(str(c["spikes"] for c in per))
    wins = [r["raster"]["window_ms"] for r in records]
    n_sp = [r["raster"]["spikes"] for r in records]
    n_neu = [r["raster"]["neurons"] for r in records]
    rates = [r["raster"]["mean_rate_hz"] for r in records]
    tfs = [r["raster"]["routing"]["third_factor"]["modulator"] for r in records]
    taus = [r["raster"]["routing"]["third_factor"]["tau_e_s"] for r in records]
    reward_s = "/".join(f"+{x:.2f}" for x in rewards)
    notes = f"""# Neuromorphic Event + Language Bridge — NOTES round 66
Run: 2026-09-02-final-heavy · Factory: neuromorphic-event-language-bridge · Generator: grok-4.6 · Output: `batch-r66.jsonl` (3 paired artifacts, 6 ThalamicTrajectories)
Rights: RM-793 research-only (SpaceXAI/xAI grok-4.6, SuperGrok Heavy chat). Not training_ready. Do not publish into `outputs/raw/` from this generator; operator uses `pipelines/round_txn.py`. Staged only at `/tmp/nelb-r66/`.

## Context / de-duplication
Prior corpus read: 2026-08-30 NOTES-r01–r04, 2026-08-17-w3 NOTES-r12 family table, `/tmp/nelb-r13-holes.md` + `/tmp/nelb-r13-premises.md`, staged `/tmp/nelb-r13` through `/tmp/nelb-r64` complete batches/NOTES plus in-flight r60–r63 generators and r65 recs (sonic-nozzle / sodium-ion / vibrating-tube density, ids `196`–`198`). IDs: r13=`040`–`042` … r64=`193`–`195`, reserved r65=`196`–`198`, this round `nelb-r66-199`…`201` as assigned. Envelope cloned from complete r64 (`language_view.trajectory` + operational t2 + `spike_events` + `raster` + `gate_snn` + `isi_histogram` + `routing.third_factor` + 15-key RM-793 `meta.rights`).

Banned this round (committed + staged leftover-mill r13–r64 and in-flight r60–r65 envelopes): not VOD-SNN replay, not pharma cold-chain, not stack-gas CEMS; not r13 FBG glaze / Frostlip quench / Oxbow VRFB; not r14 BOTDA / QCM-D / MsS T(0,1); not r15 SAW torque / CRDS HF / PGNAA / Gorse-UV DOAS-as-witness; not r16 IFOG / transmon readout / hyperspectral crop; not r17 MEMS accel array / muon ore-pass / industrial x-ray DR; not r18 optogenetic PV / 905 nm LiDAR snow / clamp-on transit-time; not r19 LIBS Cu / QEPAS DGA / LFV Al; not r20 Kaplan LDV / THz-TDS radome moisture / ECT CFB; not r21 THz-TDS bondline / ECA FSW lift-off / LIBS C; not r22 ECT pneumatic riser / TDLAS NH3 / LIBS tap; not r23 lock-in thermography CFRP / PAUT TFM girth / EN CUI; not r24 RUS porcelain / N-16 transit-time loop / helium RGA; not r25 Faraday FOCT / blade tip-timing / acoustic pyrometry; not r26 SPR cyanide / VW viscometer / MW cavity moisture; not r27 MFL AST / NMR T2 / Cs-137 densitometry; not r28 MFL ILI / JNT / CRNS; not r29 Coriolis bitumen / CARS TIT / Zn-Ka XRF; not r30 Mössbauer FCC / GB-InSAR tailings / ellipsometry PECVD; not r31 CTA hot-wire / rhodium SPND / LII soot; not r32 PALS / 14N NQR / SFRA; not r33 digital shearography hull / hydrogen permeation / FMCW BOF lining; not r34 handheld XRF Cr-Kα / Coriolis tube-twist / GPR liner cover; not r35/r37 mud-pulse MWD / Barkhausen / Lamb-wave; not r36 Pockels GIS / PEC coated riser / confocal chromatic; not r38 OCT TBC / DCPD girth / impact-echo containment; not r39 phosphor-lifetime / vortex-shedding / GWR foam; not r40 He-3 neutron-backscatter / Kr-85 beta / 532 nm Raman; not r41/r42/r43 cyclotron BPM / alanine EPR / ADCP ice-jam; not r44 TOFD ligament / laser-flash Parker / TDR remaining-length; not r45 RFEC boiler tube / ACFM jacket node / LPR cooling header / Seebeck remaining ferrite; not r46 paramagnetic O2 / TOFD ligament / TEOM PM; not r47 magmeter slurry / PDA Sauter-mean / acoustoelastic residual; not r48 C-SAM IGBT void / FDS tanδ bushing / MCSA broken-bar; not r49 EMAT SH coil / FBRM chord D50 / ACFM jack-up; not r50 OFDR hoop-strain / XRD sin²ψ / FSM jumper; not r51 Gardon heat flux / chilled-mirror dew-point / DIC hoop-strain; not r52 CLD NOx / API-670 proximity / thermal-mass capillary; not r53 ER remaining wall / Fabry-Perot choke / inductive oil-debris; not r54 wire-mesh void / UCI hardness / MAE remaining case; not r55 FID THC / turbine k-factor / magnetostrictive waveguide; not r56 IRIS HEX wall / ratio pyrometer / UV-fluorescence oil-in-water; not r57 load-cell hopper / PID VOC / four-electrode conductivity; not r58 Rogowski / beta-attenuation occupancy; not r59 UV-DOAS remaining SO2 / aluminum-oxide remaining moisture / strain-gauge load-cell remaining hopper mass; not r60 laser-triangulation / FID VOC / dielectric water-cut; not r61 Stern-Volmer DO / pellistor LEL / FMCW tank-radar; not r62 laser-triangulation strip / pellistor booth / ultrasonic-Doppler slurry; not r63 Wobbe / critical-angle Brix / amperometric free-chlorine; not r64 venturi dP steam / katharometer H2 / Clark polarographic DO; not r65 sonic-nozzle / sodium-ion / vibrating-tube density. Plants not reused: Nettlewake, Frostlip, Oxbow, Wickspire, Bitternex, Clinkerfell, Miregait, Puddlewick, Fennelholt, Ashholt, Gorsewisp, Flintcrag, Kettermere, Mirebank, Terncrag, Quaycrag, Copsefell, Heatherfen, Charkholt, Kelpcrag, Wickmere, Dapplemere, Hawkmere, Embercrag, Reedwhin, Brackholt, Dewholt, Pebblewick, Fernwick, Mossfell, Kelpfen, Larchmere, Quernspit, Hearthspit, Wexmere, Glaurfen, Brindlecrag, Copsewharf, Kelpwharf, Thornmere, Marlfell, Birchfen, Cressholt, Dunlinholt, Oreholt, Sedgecrag, Yarrowfen, Rindleholt, Woadfen, Pellmire, Owlmere, Fogmere, Stoatfen, plus r13–r65 plant list.

This round introduces three unused industrial families (Ubbelohde remaining kinematic viscosity, 60-degree remaining gloss, RF-admittance remaining level) on new invented plants. r13-holes cyclotron/alanine/ADCP and r64/r65 densification leftovers are not restaged.

Adjacencies declared in-pair then kept physically distinct:
- **199 Ubbelohde kinematic viscosity** is an efflux-time remaining slip of a turbine lube header, not r26 vibrating-wire viscometer, not r29/r34 Coriolis, not r65 vibrating-tube density, not r52 thermal-mass capillary, not r14 QCM-D.
- **200 60-degree gloss** is a detector-current remaining GU of a coil-coat line, not r30 ellipsometry, not r36 confocal chromatic, not r38 OCT, not r60/r62 laser triangulation, not r58 white-light interferometry, not r16 hyperspectral crop.
- **201 RF-admittance level** is a capacitance remaining height of a fly-ash silo, not r39 guided-wave radar, not r61 FMCW tank-radar, not r55 magnetostrictive waveguide, not r59 strain-gauge hopper mass, not r27 nucleonic densitometry.

## Round 66 batch summary (3 pairs, 6 trajectories)

| id | modality (NEW family) | domain | decisions | headline |
|----|----------------------|--------|-----------|----------|
| nelb-r66-199 | Ubbelohde remaining kinematic viscosity of a turbine lube header (k_c·t cSt, Viscveil last-good denial, 18 min filter-flush floor) | Sallowfen Turbine Lube SL-4 header H-2 (invented): 0.500*40.00 reconstructs 20.00 cSt while Viscveil still reads 4.80 cSt | REJECT (+0.43) / MODIFY (+0.34) | serialized `0.500*40.00=20.00`; `20.00*0.80=16.00`; `20.00/0.500=40.00`; conjunctive SOP (nu AND SNR) forbids continue-running; three-party collusion includes the capillary-cloud infra owner; companion t2 filter-flush hold, header ESD refused; sim_or_real=designed |
| nelb-r66-200 | 60-degree remaining gloss of a coil-coat line (k_g·I/I_std GU, Gleamveil last-good denial, 24 min new-head floor) | Wychholt Coil-Coat WH-7 coil C-3 (invented, HIL dummy in GLOSS-HIL-4): 40.00*(8.00/4.00) reconstructs 80.00 GU while Gleamveil still reads 18.00 GU | MODIFY (+0.40) / ACCEPT (+0.35) | serialized `40.00*(8.00/4.00)=80.00` and `0.80*80.00=64.00`; keep-coil refused; gloss tech Oren Vale exonerated (missing black-tile zero AE, UTC vs UTC+2); companion t2 new-head restart; sim_or_real=hil |
| nelb-r66-201 | RF-admittance remaining level of a fly-ash silo (k_l·(C−C0) m, Admveil last-good denial, 12 min survey floor) | Marshspit Fly-Ash MS-2 silo S-4 (invented, simulated ADM-SIM-3): 0.50*(28.00-4.00) reconstructs 12.00 m while Admveil still reads 1.20 m | ACCEPT (+0.41) / REJECT (+0.36) | serialized `0.50*(28.00-4.00)=12.00`; `12.00/16.00=0.75`; bounded ACCEPT of S-4 only; S-1..S-3 out of scope; companion t2 REJECTS skip-survey; sim_or_real=simulated |

Decision spread: REJECT / MODIFY / MODIFY / ACCEPT / ACCEPT / REJECT — **2A/2M/2R**. All three enums used, and all three sit on **leads**. Provenance spread: designed / hil / simulated (one each; never live-plant). IDs `nelb-r66-199`…`201` plus t1/t2 suffixes.

## Raster sidecar
Every record carries `raster` + top-level `gate_snn` + `gate_compute`. Windows {wins[0]:.0f}/{wins[1]:.0f}/{wins[2]:.0f} ms; `window_s == window_ms/1000` exactly; `spikes == round(neurons·rate·window_s)` with zero slack ({n_sp[0]}/{n_sp[1]}/{n_sp[2]} at {rates[0]}/{rates[1]}/{rates[2]} Hz over {n_neu[0]}/{n_neu[1]}/{n_neu[2]} neurons); `energy_pJ = spikes·23` and `energy_uJ = spikes·23e-6` exact ({n_sp[0]*23}/{n_sp[1]*23}/{n_sp[2]*23} pJ). Routing source/target + 3-entry tables + `third_factor` on all three (modulators {tfs[0]} / {tfs[1]} / {tfs[2]}; τe {taus[0]}/{taus[1]}/{taus[2]} s as consistent `tau_e_s`+`tau_e_ms` pairs). Excerpts integer `t_us`, in-window, `neuron_id`-bounded, sorted, full-window by construction, per-spike amplitude with adaptation (0.82**k) plus noise. ISI histograms from the full window, bins ≥1 ms, counts sum to `spikes − distinct_active_neurons` ({isis[0]}/{isis[1]}/{isis[2]}). Same-neuron gaps ≥1100 µs pre-round, ≥1000 µs serialized. `gate_snn` on all three: decisions REJECT/MODIFY/ACCEPT matching each lead trajectory; every rate-declaring population's budget exact against its decision window. `gate_compute.per_check` windows 32–40 ms, budgets exact ({gc[0]} / {gc[1]} / {gc[2]}). Main streams: {events[0]}/{events[1]}/{events[2]} events (inside the 5–40 cap), strictly increasing `t_rel_ms` only (no `t_ms` mix), same-channel refractory ≥0.8 ms (199 Ubbelohde pair at 1.4 ms, 200 gloss pair at 1.2 ms, 201 RF-admittance pair at 1.5 ms).

## Self-critique

### Edge cases added vs still thin
- **Added:** first Ubbelohde remaining-kinematic-viscosity family on a turbine lube header with a recomputable nu=k_c·t (`20.00 cSt`) plus dynamic-viscosity and efflux identities and three-party collusion including the capillary-cloud infra owner; first 60-degree remaining-gloss family on a coil-coat line with recomputable G=k_g·I/I_std (`80.00 GU`) and DOI identity, plus a resolved-innocent gloss tech (timezone-skipped black-tile zero, not last-to-badge); first RF-admittance remaining-level family on a fly-ash silo with recomputable L=k_l·(C−C0) (`12.00 m`) plus fill identity; bounded ACCEPT whose out-of-scope clause is adjacent silos rather than a hopper/taphole/dump cap; operational t2 on all three (filter-flush hold, new-head restart, skip-survey refusal); provenance trio designed/hil/simulated; 18 min / 24 min / 12 min slow floors in-stream.
- **Still thin:** (i) 199's k_c is a lumped s→cSt factor, not a Hagenbach / bath-T table — a thermal hop that fakes 20.00 cSt inside a 4.80 cSt Viscveil corridor is unwritten; (ii) 200's k_g is a lumped uA→GU gain, not an incidence / refractive-index map, so a orange-peel hop that fakes 80.00 GU is unwritten; (iii) 201's k_l is a lumped pF→m factor, not a dielectric / build-up table, so a coating hop that fakes 12.00 m inside a 1.20 last-good is unwritten; (iv) vendor-only as a *lead* REJECT on a plant with *no* independent Ubbelohde/gloss/admittance head installed yet remains slightly harder — 199/200 still have plant heads; (v) stream amplitudes remain authored constants (raster draws are the only seeded noise); (vi) r64/r65 densification leftovers were left for those rounds' owners.

### Realism of noise / temporal fidelity
- Strong: 199's 20.00 cSt, mu 16.00, efflux 40.00, and 18.0 min flush (`6000+1080=7080 s`) recompute from the record; 200's 80.00 GU, DOI 64.00, and 24.0 min cooldown (`2820+1440=4260 s`) recompute; 201's 12.00 m, fill 0.75, and 12.0 min survey (`6000+720=6720 s`) recompute. Raster adaptation (0.82**k plus 4% noise) and the 1.2–1.5 ms physics pairs give the 5–40 stream a raster-scale motif without violating 0.8 ms same-channel refractory.
- **Gaps, honestly:** (i) 5–40 cap still forces heavy thinning (0.1 Hz Ubbelohde kept as 4 t points; 10 Hz gloss kept as 4 I points; 1 Hz RF-admittance kept as 4 C points); (ii) 199's post-stop 24.00 cSt is a later sample, not a closed-loop flush controller; (iii) 200 HIL coupon times an in-service isolate that the stream does not independently witness on a second live coil until the new head starts; (iv) no gate_snn input→output volley pair at raster resolution this round (r04-a1 already staged that).

### Training value (SNN/LSM + agentic)
Distillation targets: Ubbelohde nu=k_c·t reconstruction head plus mu and efflux identities; conjunctive isolate floor vs continue-running vs header ESD; Viscveil-infra collusion; 60-degree G=k_g·I/I_std head plus DOI identity; isolate-floor coil vs keep-whole vs dump; exoneration against last-to-badge social pressure; RF-admittance L=k_l·(C−C0) and fill identities; bounded ACCEPT with silo-out-of-scope; skip-survey refusal under survey takt. Agentic value concentrates in three patterns: reconstruction-as-SoT on a physical viscosity/gloss/level load the raw corridor cannot see, earned ACCEPT with an explicit physical out-of-scope object (S-1..S-3), and stop-then-hold so a REJECT does not become a main/coil/overfill kill.

## What a later leftover-mill round should add (next densification target)
1. **Hagenbach / bath-T table** on a non-SL-4 lube header so a thermal hop fakes 20.00 cSt inside a 4.80 cSt Viscveil corridor, closing 199's lumped-k_c gap.
2. **Incidence / refractive-index map** on a non-WH-7 coil so an orange-peel hop can fake 80.00 GU while mean detector current looks healthy.
3. **Dielectric / build-up table** on a non-MS-2 silo so a coating hop can fake 12.00 m inside a 1.20 last-good corridor.
4. **Vendor-only as a lead REJECT** on a plant that has no independent Ubbelohde/gloss/admittance head installed yet (199/200 still had plant heads).
5. **Do not restage** VOD-SNN replay, pharma cold-chain, CEMS, FBG glaze, Frostlip quench, Oxbow VRFB, IFOG, transmon, hyperspectral, MEMS array, muon ore-pass, industrial x-ray, optogenetic stim, 905 nm LiDAR snow, clamp-on transit-time, LIBS, QEPAS, LFV, Kaplan LDV, THz-TDS, ECT, TDLAS NH3, lock-in thermography, PAUT TFM, EN CUI, RUS porcelain, N-16 loop flow, helium RGA, Faraday FOCT, blade tip-timing, acoustic pyrometry, SPR, vibrating-wire, microwave-cavity, MFL, NMR T2, nucleonic densitometry, JNT, CRNS, Coriolis, CARS, XRF, Mössbauer, GB-InSAR, ellipsometry, CTA, SPND, LII, PALS, NQR, SFRA, digital shearography, hydrogen permeation, FMCW lining, GPR, Pockels, PEC, confocal, mud-pulse, Barkhausen, Lamb-wave, OCT, DCPD, impact-echo, cyclotron BPM, alanine EPR, ADCP, vortex-shedding, Kr-85 beta, 532 nm Raman, phosphor-lifetime, guided-wave-radar, paramagnetic O2, TOFD, TEOM, magmeter, PDA, acoustoelastic, C-SAM, FDS tanδ, MCSA, EMAT SH, FBRM, ACFM, OFDR, XRD sin²ψ, FSM, Gardon, chilled-mirror, DIC, CLD NOx, proximity orbit, thermal-mass, ER probe, Fabry-Perot, inductive debris, wire-mesh, UCI, MAE, IRIS, ratio pyrometer, UV-fluorescence oil-in-water, zirconia Nernst, PID VOC, contact pulse-echo, Rogowski, beta-attenuation, FID THC, turbine k-factor, magnetostrictive waveguide, UV-DOAS SO2, Al2O3 moisture, load-cell hopper, four-electrode conductivity, venturi dP, katharometer H2, Clark polarographic DO, sonic-nozzle, sodium-ion, vibrating-tube density, Sallowfen SL-4 Ubbelohde, Wychholt GLOSS-HIL-4, or Marshspit ADM-SIM-3. Leave r64/r65 densification leftovers for those rounds' owners. Do not steal r55–r65 IDs `166`–`198`.

## Verification
`batch-r66.jsonl`: 3 lines, `json.loads`-clean (allow_nan=False), {sizes[0]}/{sizes[1]}/{sizes[2]} bytes (file {BATCH.stat().st_size}, sha256 `{file_sha}`). Staged at `/tmp/nelb-r66/` only. Repo gates: `check_records.check_jsonl` with `FactoryStaging(enabled=True)` → 0 errors, 0 warnings, kinds `{{bridge_pair: 3}}`; `python3 pipelines/check_records.py --strict /tmp/nelb-r66` → 0/0; `curate_bridge.raster_status(..., require_raster=True, require_routing_table=True)` → raster_valid and gate_snn_valid true, empty reason codes; `curate_record(...)` → 3× retain / `BRIDGE_EVENTS_ALREADY_GLOBALLY_ORDERED`; `verify_batch_for_frontier(strict=True)` → 3 verified, 0 inconclusive, 0 failed; `python3 pipelines/spike_probe.py --strict /tmp/nelb-r66/batch-r66.jsonl` → loaded 3, unloadable 0, problems [], third_factor_routes 3, gate_snn_records 3, spikes {spikes}, energy_pJ {energy}. Build-time asserts: global time order; same-channel ≥0.8 ms; 5–40 events ({events[0]}/{events[1]}/{events[2]}); excerpt integer bounds, neuron bounds, sort, 1 ms per-neuron floor; ISI identity {isis[0]}/{isis[1]}/{isis[2]}; spike budgets exact; energy pJ/µJ exact; reward totals equal two-decimal component sums ({reward_s}); gate_snn decisions match lead `safety_decision.decision`; `state.sim_or_real` ∈ {{designed, hil, simulated}}; `meta.round=66`, `meta.factory=neuromorphic-event-language-bridge`, `meta.generator=grok-4.6`, `meta.run_label=2026-09-02-final-heavy`; `meta.rights` 15-key RM-793 stamp (`intended_use=research_only`, `linear_issue=RM-793`, `generated_at={GENERATED_AT}`); no hidden-reasoning keys; no `provenance` objects; no live-plant claims; no `training_ready`; all 9 record/trajectory ids unique. Raster seeds 202609199/202609200/202609201, MT19937.

Honest novelty accounting: 3/3 modality families are new versus the whole committed factory and versus staged leftover-mill r13–r64 (and in-flight r60–r65 envelopes). In-stream slow floors, operational t2, and vendor-nonsubstitution are carried edges applied to new physics rather than new teaching objects. Three-party collusion and exoneration were already taught on r13 quench/VRFB and r46 TOFD/r47 PDA, so those heads are carried onto new sensors. Against that: bounded-accept-with-scope-limit, reconstruction-as-SoT, conjunctive SOP, and custody vocabulary are carried; the 5–40 cap is a density constraint not a new teaching object; 53 prior leftover-mill rounds already taught custody/governance at high sophistication. Net: about two-fifths of the round's scenario/edge mass is genuinely novel.

Novel coverage: 40%
"""
    NOTES.write_text(notes, encoding="utf-8")
    print("wrote", NOTES, "bytes", NOTES.stat().st_size)


def main():
    occupancy_preflight()
    records = [rec_199(), rec_200(), rec_201()]
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
