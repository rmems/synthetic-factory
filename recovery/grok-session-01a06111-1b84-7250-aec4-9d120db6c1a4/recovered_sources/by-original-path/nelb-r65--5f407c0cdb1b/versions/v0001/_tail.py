def occupancy_preflight():
    claimed = (
        "nozzveil",
        "owlmere fuel",
        "sonic-nozzle remaining",
        "fogmere steam",
        "sodaveil",
        "sodium-ion remaining",
        "stoatfen bitumen",
        "tubeveil",
        "vibrating-tube remaining",
        "na-hil-5",
        "tube-sim-4",
        "edda wold",
        "padrig vole",
        "bram quist",
        "tamsin keld",
        "rory fenwick",
    )
    steal = (
        "ventveil",
        "rindleholt steam",
        "kathveil",
        "woadfen chlorate",
        "polarveil",
        "pellmire boiler",
        "calorveil",
        "thornfell fuel",
        "wobbe remaining",
        "chlorveil",
        "pewterholt cooling",
        "brixveil",
        "quillmere sugar",
        "spotveil",
        "yewspit tandem",
        "flameveil",
        "brimwhin rto",
        "cutveil",
        "hagholt crude",
        "sternveil",
        "mirewhin wwtp",
        "pellveil",
        "lacquerfen oven",
        "rangveil",
        "pitchshaw crude",
        "gageveil",
        "mireholt cold-mill",
        "beadveil",
        "torholt solvent",
        "shiftveil",
        "bramblefen tailings",
        "doasveil",
        "oxveil",
        "cellveil",
        "irisveil",
        "pyroveil",
        "fluoveil",
        "orifveil",
        "lampveil",
        "condveil",
        "fidveil",
        "rotorveil",
        "floatveil",
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
    )
    for n in scan:
        if "nelb-r65" in str(n):
            continue
        text = n.read_text(encoding="utf-8", errors="replace").casefold()
        for b in claimed:
            if b in text:
                hits.append(f"{n}:{b}")
    if hits:
        raise RuntimeError(f"r65 family/plant collision {hits}")
    blob = json.dumps([rec_196(), rec_197(), rec_198()], ensure_ascii=False).casefold()
    for s in steal:
        if s in blob:
            raise RuntimeError(f"r65 stole occupied family {s}")


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
        BATCH, "batch-r65.jsonl", staging=FactoryStaging(enabled=True)
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
            source_path="batch-r65.jsonl",
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
    notes = f"""# Neuromorphic Event + Language Bridge — NOTES round 65
Run: 2026-09-02-final-heavy · Factory: neuromorphic-event-language-bridge · Generator: grok-4.6 · Output: `batch-r65.jsonl` (3 paired artifacts, 6 ThalamicTrajectories)
Rights: RM-793 research-only (SpaceXAI/xAI grok-4.6, SuperGrok Heavy chat). Not training_ready. Do not publish into `outputs/raw/` from this generator; operator uses `pipelines/round_txn.py`. Staged only at `/tmp/nelb-r65/`.

## Context / de-duplication
Prior corpus read: 2026-08-30 NOTES-r01–r04, 2026-08-17-w3 NOTES-r12 family table, `/tmp/nelb-r13-holes.md` + `/tmp/nelb-r13-premises.md`, staged `/tmp/nelb-r13` through `/tmp/nelb-r59` complete batches/NOTES plus in-flight `/tmp/nelb-r60` (laser-triangulation remaining strip / FID remaining VOC / dielectric remaining water-cut, ids `181`–`183`), `/tmp/nelb-r61` (Stern-Volmer DO / pellistor LEL / FMCW tank-radar, ids `184`–`186`), `/tmp/nelb-r62` (laser-triangulation cold-mill / pellistor booth / ultrasonic Doppler slurry, ids `187`–`189`), `/tmp/nelb-r63` (Wobbe calorific / critical-angle Brix / amperometric chlorine, ids `190`–`192`), `/tmp/nelb-r64` (venturi steam-flow / katharometer H2 / Clark polarographic DO, ids `193`–`195`). IDs: r13=`040`–`042` … r64=`193`–`195`, this round `nelb-r65-196`…`198` as assigned. Envelope cloned from complete r59 (`language_view.trajectory` + operational t2 + `spike_events` + `raster` + `gate_snn` + `isi_histogram` + `routing.third_factor` + 15-key RM-793 `meta.rights`).

Banned this round (committed + staged leftover-mill r13–r59 and in-flight r60–r64 envelopes): not VOD-SNN replay, not pharma cold-chain, not stack-gas CEMS; not r13 FBG glaze / Frostlip quench / Oxbow VRFB; not r14 BOTDA / QCM-D / MsS T(0,1); not r15 SAW torque / CRDS HF / PGNAA / Gorse-UV DOAS-as-witness; not r16 IFOG / transmon readout / hyperspectral crop; not r17 MEMS accel array / muon ore-pass / industrial x-ray DR; not r18 optogenetic PV / 905 nm LiDAR snow / clamp-on transit-time; not r19 LIBS Cu / QEPAS DGA / LFV Al; not r20 Kaplan LDV / THz-TDS radome moisture / ECT CFB; not r21 THz-TDS bondline / ECA FSW lift-off / LIBS C; not r22 ECT pneumatic riser / TDLAS NH3 / LIBS tap; not r23 lock-in thermography CFRP / PAUT TFM girth / EN CUI; not r24 RUS porcelain / N-16 transit-time loop / helium RGA; not r25 Faraday FOCT / blade tip-timing / acoustic pyrometry; not r26 SPR cyanide / VW viscometer / MW cavity moisture; not r27 MFL AST / NMR T2 / Cs-137 densitometry; not r28 MFL ILI / JNT / CRNS; not r29 Coriolis bitumen / CARS TIT / Zn-Ka XRF; not r30 Mössbauer FCC / GB-InSAR tailings / ellipsometry PECVD; not r31 CTA hot-wire / rhodium SPND / LII soot; not r32 PALS / 14N NQR / SFRA; not r33 digital shearography hull / hydrogen permeation / FMCW BOF lining; not r34 handheld XRF Cr-Kα / Coriolis tube-twist / GPR liner cover; not r35/r37 mud-pulse MWD / Barkhausen / Lamb-wave; not r36 Pockels GIS / PEC coated riser / confocal chromatic; not r38 OCT TBC / DCPD girth / impact-echo containment; not r39 phosphor-lifetime / vortex-shedding / GWR foam; not r40 He-3 neutron-backscatter / Kr-85 beta / 532 nm Raman; not r41/r42/r43 cyclotron BPM / alanine EPR / ADCP ice-jam; not r44 TOFD ligament / laser-flash Parker / TDR remaining-length; not r45 RFEC boiler tube / ACFM jacket node / LPR cooling header / Seebeck remaining ferrite; not r46 paramagnetic O2 / TOFD ligament / TEOM PM; not r47 magmeter slurry / PDA Sauter-mean / acoustoelastic residual; not r48 C-SAM IGBT void / FDS tanδ bushing / MCSA broken-bar; not r49 EMAT SH coil / FBRM chord D50 / ACFM jack-up; not r50 OFDR hoop-strain / XRD sin²ψ / FSM jumper; not r51 Gardon heat flux / chilled-mirror dew-point / DIC hoop-strain; not r52 CLD NOx / API-670 proximity / thermal-mass capillary; not r53 ER remaining wall / Fabry-Perot choke / inductive oil-debris; not r54 wire-mesh void / UCI hardness / MAE remaining case; not r55 FID THC / turbine k-factor / magnetostrictive waveguide level; not r56 IRIS HEX wall / ratio pyrometer / UV-fluorescence oil-in-water; not r57 orifice-plate dP / PID VOC / four-electrode conductivity; not r58 critical-angle Brix / WLI thickness / annubar averaging-pitot; not r59 UV-DOAS SO2 / Al2O3 moisture / load-cell hopper mass; not r60 laser-triangulation strip / FID VOC RTO / dielectric water-cut; not r61 Stern-Volmer DO / pellistor LEL / FMCW tank-radar; not r62 laser-triangulation cold-mill / pellistor booth / ultrasonic Doppler slurry; not r63 Wobbe calorific / critical-angle Brix evaporator / amperometric chlorine; not r64 venturi steam-flow / katharometer H2 / Clark polarographic DO. Plants not reused: Nettlewake, Frostlip, Oxbow, Thornmere, Marlfell, Birchfen, Yewspit, Brimwhin, Hagholt, Mirewhin, Lacquerfen, Pitchshaw, Mireholt, Torholt, Bramblefen, Thornfell, Quillmere, Pewterholt, Rindleholt, Woadfen, Pellmire, plus the r13–r64 plant list.

This round introduces three unused industrial families (sonic-nozzle remaining mass-flow, sodium-ion remaining Na, vibrating-tube remaining density) on new invented plants. r13-holes cyclotron/alanine/ADCP and r60–r64 in-flight families are not restaged.

Adjacencies declared in-pair then kept physically distinct:
- **196 sonic-nozzle mass-flow** is a critical-flow P/sqrt(T) remaining slip of a fuel-gas prover, not r64 venturi k·sqrt(h), not r57 orifice dP, not r58 annubar, not r39 vortex, not r55 turbine k-factor, not r52 thermal-mass, not r18 clamp-on, not r24 N-16, not r62 ultrasonic Doppler.
- **197 sodium-ion Na** is a glass-electrode decade C0·10**(V/S) remaining sodium of a condensate polisher, not r55/r57 zirconia Nernst O2, not r64 Clark polarographic DO, not r63 amperometric chlorine, not r57 four-electrode conductivity-as-SoT, not r51 chilled-mirror, not r59 Al2O3 moisture.
- **198 vibrating-tube density** is a U-tube period remaining density of a bitumen header, not r29/r34 Coriolis, not r26 VW viscometer, not r27 Cs-137 densitometry, not r27 NMR T2, not r60 dielectric water-cut.

## Round 65 batch summary (3 pairs, 6 trajectories)

| id | modality (NEW family) | domain | decisions | headline |
|----|----------------------|--------|-----------|----------|
| nelb-r65-196 | sonic-nozzle remaining mass-flow of a fuel-gas prover (k_n·P/sqrt(T) kg/h, Nozzveil last-good denial, 18 min soak floor) | Owlmere Fuel OM-5 prover P-3 (invented): 12.00*20.00/20.00 reconstructs 12.00 kg/h while Nozzveil still reads 3.20 kg/h | REJECT (+0.43) / MODIFY (+0.34) | serialized `12.00*20.00/20.00=12.00`; `20.00/20.00=1.00`; conjunctive SOP (mdot AND SNR) forbids continue-prove; three-party collusion includes the critical-flow-cloud infra owner; companion t2 prover-soak hold, header ESD refused; sim_or_real=designed |
| nelb-r65-197 | sodium-ion remaining Na of a steam condensate polisher (C0·10**(V/S) ppb, Sodaveil last-good denial, 24 min regen floor) | Fogmere Steam FM-8 polisher E-2 (invented, HIL dummy in NA-HIL-5): 0.01*10**(60.00/20.00) reconstructs 10.00 ppb while Sodaveil still reads 1.20 ppb | MODIFY (+0.40) / ACCEPT (+0.35) | serialized `0.01*10**(3.00)=10.00` and `0.200*10.00=2.00`; keep-polisher refused; electrode tech Tamsin Keld exonerated (missing slope-cal AE, UTC vs UTC+2); companion t2 new-electrode restart; sim_or_real=hil |
| nelb-r65-198 | vibrating-tube remaining density of a bitumen header (k_d·(τ²−τ0²) kg/m3, Tubeveil last-good denial, 12 min survey floor) | Stoatfen Bitumen SF-2 header H-5 (invented, simulated TUBE-SIM-4): 15.00*(10.00²−6.00²) reconstructs 960.0 kg/m3 while Tubeveil still reads 620.0 kg/m3 | ACCEPT (+0.41) / REJECT (+0.36) | serialized `15.00*64.00=960.0`; `960.0*45.00/3600=12.00`; bounded ACCEPT of H-5 only; H-1..H-4 out of scope; companion t2 REJECTS skip-survey; sim_or_real=simulated |

Decision spread: REJECT / MODIFY / MODIFY / ACCEPT / ACCEPT / REJECT — **2A/2M/2R**. All three enums used, and all three sit on **leads**. Provenance spread: designed / hil / simulated (one each; never live-plant). IDs `nelb-r65-196`…`198` plus t1/t2 suffixes.

## Raster sidecar
Every record carries `raster` + top-level `gate_snn` + `gate_compute`. Windows {wins[0]:.0f}/{wins[1]:.0f}/{wins[2]:.0f} ms; `window_s == window_ms/1000` exactly; `spikes == round(neurons·rate·window_s)` with zero slack ({n_sp[0]}/{n_sp[1]}/{n_sp[2]} at {rates[0]}/{rates[1]}/{rates[2]} Hz over {n_neu[0]}/{n_neu[1]}/{n_neu[2]} neurons); `energy_pJ = spikes·23` and `energy_uJ = spikes·23e-6` exact ({n_sp[0]*23}/{n_sp[1]*23}/{n_sp[2]*23} pJ). Routing source/target + 3-entry tables + `third_factor` on all three (modulators {tfs[0]} / {tfs[1]} / {tfs[2]}; τe {taus[0]}/{taus[1]}/{taus[2]} s as consistent `tau_e_s`+`tau_e_ms` pairs). Excerpts integer `t_us`, in-window, `neuron_id`-bounded, sorted, full-window by construction, per-spike amplitude with adaptation (0.82**k) plus noise. ISI histograms from the full window, bins ≥1 ms, counts sum to `spikes − distinct_active_neurons` ({isis[0]}/{isis[1]}/{isis[2]}). Same-neuron gaps ≥1100 µs pre-round, ≥1000 µs serialized. `gate_snn` on all three: decisions REJECT/MODIFY/ACCEPT matching each lead trajectory; every rate-declaring population's budget exact against its decision window. `gate_compute.per_check` windows 32–40 ms, budgets exact ({gc[0]} / {gc[1]} / {gc[2]}). Main streams: {events[0]}/{events[1]}/{events[2]} events (inside the 5–40 cap), strictly increasing `t_rel_ms` only (no `t_ms` mix), same-channel refractory ≥0.8 ms (196 nozzle pair at 1.4 ms, 197 Na-ISE pair at 1.2 ms, 198 vibrating-tube pair at 1.5 ms).

## Self-critique

### Edge cases added vs still thin
- **Added:** first sonic-nozzle remaining-mass-flow family on a fuel-gas prover with a recomputable mdot=k_n·P/sqrt(T) (`12.00 kg/h`) plus P/sqrt(T) identity and three-party collusion including the critical-flow-cloud infra owner; first sodium-ion remaining-Na family on a condensate polisher with recomputable C=C0·10**(V/S) (`10.00 ppb`) and conductivity identity, plus a resolved-innocent electrode tech (timezone-skipped slope-cal, not last-to-badge); first vibrating-tube remaining-density family on a bitumen header with recomputable rho=k_d·(τ²−τ0²) (`960.0 kg/m3`) plus mdot identity; bounded ACCEPT whose out-of-scope clause is adjacent rundown headers rather than a hopper/taphole/dump cap; operational t2 on all three (prover-soak hold, new-electrode restart, skip-survey refusal); provenance trio designed/hil/simulated; 18 min / 24 min / 12 min slow floors in-stream.
- **Still thin:** (i) 196's k_n is a lumped critical-flow gain, not a C_d/throat-area/Z-factor table — a gas-composition hop that fakes 12.00 kg/h inside a 3.20 kg/h Nozzveil corridor is unwritten; (ii) 197's S is a lumped 20.00 mV/decade, not an isotherm / junction-potential map, so a temperature hop that fakes 10.00 ppb is unwritten; (iii) 198's k_d is a lumped period-square factor, not a temperature / viscosity table, so a thermal hop that fakes 960.0 kg/m3 inside a 620 last-good is unwritten; (iv) vendor-only as a *lead* REJECT on a plant with *no* independent sonic-nozzle/Na-ISE/vibrating-tube head installed yet remains slightly harder — 196/197 still have plant heads; (v) stream amplitudes remain authored constants (raster draws are the only seeded noise); (vi) r60–r64 densification leftovers were left for those rounds' owners.

### Realism of noise / temporal fidelity
- Strong: 196's 12.00 kg/h, P/sqrt(T) 1.00, and 18.0 min soak (`6000+1080=7080 s`) recompute from the record; 197's 10.00 ppb, kappa 2.00, and 24.0 min regen (`2820+1440=4260 s`) recompute; 198's 960.0 kg/m3, mdot 12.00, and 12.0 min survey (`6000+720=6720 s`) recompute. Raster adaptation (0.82**k plus 4% noise) and the 1.2–1.5 ms physics pairs give the 5–40 stream a raster-scale motif without violating 0.8 ms same-channel refractory.
- **Gaps, honestly:** (i) 5–40 cap still forces heavy thinning (10 Hz sonic-nozzle kept as 4 P points; 1 Hz Na-ISE kept as 4 V points; 10 Hz vibrating-tube kept as 4 τ points); (ii) 196's post-stop 18.00 kg/h is a later sample, not a closed-loop soak controller; (iii) 197 HIL coupon times an in-service polisher isolate that the stream does not independently witness on a second live polisher until the new electrode starts; (iv) no gate_snn input→output volley pair at raster resolution this round (r04-a1 already staged that).

### Training value (SNN/LSM + agentic)
Distillation targets: sonic-nozzle mdot=k_n·P/sqrt(T) reconstruction head plus P/sqrt(T) identity; conjunctive isolate floor vs continue-prove vs header ESD; Nozzveil-infra collusion; Na-ISE C=C0·10**(V/S) head plus conductivity identity; isolate-floor polisher vs keep-whole vs condensate dump; exoneration against last-to-badge social pressure; vibrating-tube rho=k_d·(τ²−τ0²) and mdot identities; bounded ACCEPT with header-out-of-scope; skip-survey refusal under survey takt. Agentic value concentrates in three patterns: reconstruction-as-SoT on a physical mass-flow/Na/density load the raw corridor cannot see, earned ACCEPT with an explicit physical out-of-scope object (H-1..H-4), and stop-then-hold so a REJECT does not become a header/dump/line kill.

## What a later leftover-mill round should add (next densification target)
1. **C_d / throat-area / Z-factor table** on a non-OM-5 prover so a composition hop fakes 12.00 kg/h inside a 3.20 kg/h Nozzveil corridor, closing 196's lumped-k_n gap.
2. **Isotherm / junction-potential map** on a non-FM-8 polisher so a thermal hop can fake 10.00 ppb while mean electrode millivolt looks healthy.
3. **Temperature / viscosity table** on a non-SF-2 header so a thermal hop can fake 960.0 kg/m3 inside a 620 last-good corridor.
4. **Vendor-only as a lead REJECT** on a plant that has no independent sonic-nozzle/Na-ISE/vibrating-tube head installed yet (196/197 still had plant heads).
5. **Do not restage** VOD-SNN replay, pharma cold-chain, CEMS, FBG glaze, Frostlip quench, Oxbow VRFB, IFOG, transmon, hyperspectral, MEMS array, muon ore-pass, industrial x-ray, optogenetic stim, 905 nm LiDAR snow, clamp-on transit-time, LIBS, QEPAS, LFV, Kaplan LDV, THz-TDS, ECT, TDLAS NH3, lock-in thermography, PAUT TFM, EN CUI, RUS porcelain, N-16 loop flow, helium RGA, Faraday FOCT, blade tip-timing, acoustic pyrometry, SPR, vibrating-wire, microwave-cavity, MFL, NMR T2, nucleonic densitometry, JNT, CRNS, Coriolis, CARS, XRF, Mössbauer, GB-InSAR, ellipsometry, CTA, SPND, LII, PALS, NQR, SFRA, digital shearography, hydrogen permeation, FMCW lining, GPR, Pockels, PEC, confocal, mud-pulse, Barkhausen, Lamb-wave, OCT, DCPD, impact-echo, cyclotron BPM, alanine EPR, ADCP, vortex-shedding, Kr-85 beta, 532 nm Raman, phosphor-lifetime, guided-wave-radar, paramagnetic O2, TOFD, TEOM, magmeter, PDA, acoustoelastic, C-SAM, FDS tanδ, MCSA, EMAT SH, FBRM, ACFM, OFDR, XRD sin²ψ, FSM, Gardon, chilled-mirror, DIC, CLD NOx, proximity orbit, thermal-mass, ER probe, Fabry-Perot, inductive debris, wire-mesh, UCI, MAE, IRIS, ratio pyrometer, UV-fluorescence oil-in-water, zirconia Nernst, PID VOC, contact pulse-echo, Rogowski, beta-attenuation, UV-DOAS, Al2O3, load-cell, laser-triangulation, FID VOC, dielectric water-cut, Stern-Volmer DO, pellistor LEL, FMCW tank-radar, ultrasonic Doppler, Wobbe, critical-angle Brix, amperometric chlorine, venturi steam-flow, katharometer H2, Clark polarographic DO, Owlmere OM-5 sonic-nozzle, Fogmere NA-HIL-5, or Stoatfen TUBE-SIM-4. Leave r60–r64 densification leftovers for those rounds' owners. Do not steal r55–r64 IDs `166`–`195`.

## Verification
`batch-r65.jsonl`: 3 lines, `json.loads`-clean (allow_nan=False), {sizes[0]}/{sizes[1]}/{sizes[2]} bytes (file {BATCH.stat().st_size}, sha256 `{file_sha}`). Staged at `/tmp/nelb-r65/` only. Repo gates: `check_records.check_jsonl` with `FactoryStaging(enabled=True)` → 0 errors, 0 warnings, kinds `{{bridge_pair: 3}}`; `python3 pipelines/check_records.py --strict /tmp/nelb-r65` → 0/0; `curate_bridge.raster_status(..., require_raster=True, require_routing_table=True)` → raster_valid and gate_snn_valid true, empty reason codes; `curate_record(...)` → 3× retain / `BRIDGE_EVENTS_ALREADY_GLOBALLY_ORDERED`; `verify_batch_for_frontier(strict=True)` → 3 verified, 0 inconclusive, 0 failed; `python3 pipelines/spike_probe.py --strict /tmp/nelb-r65/batch-r65.jsonl` → loaded 3, unloadable 0, problems [], third_factor_routes 3, gate_snn_records 3, spikes {spikes}, energy_pJ {energy}. Build-time asserts: global time order; same-channel ≥0.8 ms; 5–40 events ({events[0]}/{events[1]}/{events[2]}); excerpt integer bounds, neuron bounds, sort, 1 ms per-neuron floor; ISI identity {isis[0]}/{isis[1]}/{isis[2]}; spike budgets exact; energy pJ/µJ exact; reward totals equal two-decimal component sums ({reward_s}); gate_snn decisions match lead `safety_decision.decision`; `state.sim_or_real` ∈ {{designed, hil, simulated}}; `meta.round=65`, `meta.factory=neuromorphic-event-language-bridge`, `meta.generator=grok-4.6`, `meta.run_label=2026-09-02-final-heavy`; `meta.rights` 15-key RM-793 stamp (`intended_use=research_only`, `linear_issue=RM-793`, `generated_at={GENERATED_AT}`); no hidden-reasoning keys; no `provenance` objects; no live-plant claims; no `training_ready`; all 9 record/trajectory ids unique. Raster seeds 202609196/202609197/202609198, MT19937.

Honest novelty accounting: 3/3 modality families are new versus the whole committed factory and versus staged leftover-mill r13–r59 (and in-flight r60–r64 envelopes). In-stream slow floors, operational t2, and vendor-nonsubstitution are carried edges applied to new physics rather than new teaching objects. Three-party collusion and exoneration were already taught on r13 quench/VRFB and later leftover-mill rounds, so those heads are carried onto new sensors. Against that: bounded-accept-with-scope-limit, reconstruction-as-SoT, conjunctive SOP, and custody vocabulary are carried; the 5–40 cap is a density constraint not a new teaching object; 52 prior leftover-mill rounds already taught custody/governance at high sophistication. Net: about two-fifths of the round's scenario/edge mass is genuinely novel.

Novel coverage: 40%
"""
    NOTES.write_text(notes, encoding="utf-8")
    print("wrote", NOTES, "bytes", NOTES.stat().st_size)


def main():
    occupancy_preflight()
    records = [rec_196(), rec_197(), rec_198()]
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
