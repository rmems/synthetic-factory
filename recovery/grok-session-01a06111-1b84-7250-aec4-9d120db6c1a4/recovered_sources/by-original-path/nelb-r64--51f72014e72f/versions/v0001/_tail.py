def occupancy_preflight():
    claimed = (
        "ventveil",
        "rindleholt steam",
        "venturi remaining-dp",
        "kathveil",
        "woadfen chlorate",
        "katharometer remaining-h2",
        "deaerveil",
        "pellmire boiler",
        "clark polarographic remaining-do",
        "kath-hil-7",
        "clark-sim-5",
        "joss amber",
        "hale voss",
        "mira fenn",
        "tamsin veld",
        "orrin cask",
    )
    steal = (
        "irisveil",
        "wexmere hydrotreater",
        "glaurfen converter",
        "pyroveil",
        "nernstveil",
        "glimmerholt",
        "rogowski coil",
        "coilveil",
        "beta-attenuation",
        "betaveil",
        "photoionization-detector",
        "contact pulse-echo remaining-wall",
        "wire-mesh remaining void",
        "uci remaining hardness",
        "magnetoacoustic-emission remaining case",
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
    )
    hits = []
    root = Path("/tmp")
    scan = (
        sorted(root.glob("nelb-r*/NOTES-r*.md"))
        + sorted(root.glob("nelb-r*/gen_r*.py"))
        + sorted(root.glob("nelb-r*/records_block.py"))
        + sorted(root.glob("nelb-r*/_recs.py"))
        + sorted(root.glob("nelb-r*/recs.py"))
    )
    for n in scan:
        if "nelb-r64" in str(n):
            continue
        text = n.read_text(encoding="utf-8", errors="replace").casefold()
        for b in claimed:
            if b in text:
                hits.append(f"{n}:{b}")
    if hits:
        raise RuntimeError(f"r64 family/plant collision {hits}")
    blob = json.dumps([rec_193(), rec_194(), rec_195()], ensure_ascii=False).casefold()
    for s in steal:
        if s in blob:
            raise RuntimeError(f"r64 stole occupied family {s}")


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
        BATCH, "batch-r64.jsonl", staging=FactoryStaging(enabled=True)
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
            source_path="batch-r64.jsonl",
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
    notes = f"""# Neuromorphic Event + Language Bridge — NOTES round 64
Run: 2026-09-02-final-heavy · Factory: neuromorphic-event-language-bridge · Generator: grok-4.6 · Output: `batch-r64.jsonl` (3 paired artifacts, 6 ThalamicTrajectories)
Rights: RM-793 research-only (SpaceXAI/xAI grok-4.6, SuperGrok Heavy chat). Not training_ready. Do not publish into `outputs/raw/` from this generator; operator uses `pipelines/round_txn.py`. Staged only at `/tmp/nelb-r64/`.

## Context / de-duplication
Prior corpus read: 2026-08-30 NOTES-r01–r04, 2026-08-17-w3 NOTES-r12 family table, `/tmp/nelb-r13-holes.md` + `/tmp/nelb-r13-premises.md`, staged `/tmp/nelb-r13` through `/tmp/nelb-r59` complete or in-flight batches/NOTES/generators (r55 FID-THC / turbine k-factor / magnetostrictive; r56 IRIS / ratio pyrometer / UV-fluorescence OIW; r57 load-cell hopper / PID VOC / four-electrode conductivity; r58 FID-THC / Rogowski / beta-attenuation; r59 UV-DOAS SO2 / Al2O3 moisture / load-cell hopper). r60–r63 are incomplete head/tail stubs cloned from r56 and are treated as occupancy noise, not clone sources. IDs: r13=`040`–`042` … r59=`178`–`180`, reserved r60–r63=`181`–`192`, this round `nelb-r64-193`…`195` as assigned. Envelope cloned from complete r59 (`language_view.trajectory` + operational t2 + `spike_events` + `raster` + `gate_snn` + `isi_histogram` + `routing.third_factor` + 15-key RM-793 `meta.rights`).

Banned this round (committed + staged leftover-mill r13–r59 and in-flight r57/r58 generators): not VOD-SNN replay, not pharma cold-chain, not stack-gas CEMS; not r13 FBG glaze / Frostlip quench / Oxbow VRFB; not r14 BOTDA / QCM-D / MsS T(0,1); not r15 SAW torque / CRDS HF / PGNAA / Gorse-UV DOAS-as-witness; not r16 IFOG / transmon readout / hyperspectral crop; not r17 MEMS accel array / muon ore-pass / industrial x-ray DR; not r18 optogenetic PV / 905 nm LiDAR snow / clamp-on transit-time; not r19 LIBS Cu / QEPAS DGA / LFV Al; not r20 Kaplan LDV / THz-TDS radome moisture / ECT CFB; not r21 THz-TDS bondline / ECA FSW lift-off / LIBS C; not r22 ECT pneumatic riser / TDLAS NH3 / LIBS tap; not r23 lock-in thermography CFRP / PAUT TFM girth / EN CUI; not r24 RUS porcelain / N-16 transit-time loop / helium RGA; not r25 Faraday FOCT / blade tip-timing / acoustic pyrometry; not r26 SPR cyanide / VW viscometer / MW cavity moisture; not r27 MFL AST / NMR T2 / Cs-137 densitometry; not r28 MFL ILI / JNT / CRNS; not r29 Coriolis bitumen / CARS TIT / Zn-Ka XRF; not r30 Mössbauer FCC / GB-InSAR tailings / ellipsometry PECVD; not r31 CTA hot-wire / rhodium SPND / LII soot; not r32 PALS / 14N NQR / SFRA; not r33 digital shearography hull / hydrogen permeation / FMCW BOF lining; not r34 handheld XRF Cr-Kα / Coriolis tube-twist / GPR liner cover; not r35/r37 mud-pulse MWD / Barkhausen / Lamb-wave; not r36 Pockels GIS / PEC coated riser / confocal chromatic; not r38 OCT TBC / DCPD girth / impact-echo containment; not r39 phosphor-lifetime / vortex-shedding / GWR foam; not r40 He-3 neutron-backscatter / Kr-85 beta / 532 nm Raman; not r41/r42/r43 cyclotron BPM / alanine EPR / ADCP ice-jam; not r44 TOFD ligament / laser-flash Parker / TDR remaining-length; not r45 RFEC boiler tube / ACFM jacket node / LPR cooling header / Seebeck remaining ferrite; not r46 paramagnetic O2 / TOFD ligament / TEOM PM; not r47 magmeter slurry / PDA Sauter-mean / acoustoelastic residual; not r48 C-SAM IGBT void / FDS tanδ bushing / MCSA broken-bar; not r49 EMAT SH coil / FBRM chord D50 / ACFM jack-up; not r50 OFDR hoop-strain / XRD sin²ψ / FSM jumper; not r51 Gardon heat flux / chilled-mirror dew-point / DIC hoop-strain; not r52 CLD NOx / API-670 proximity / thermal-mass capillary; not r53 ER remaining wall / Fabry-Perot choke / inductive oil-debris; not r54 wire-mesh void / UCI hardness / MAE remaining case; not r55 FID THC / turbine k-factor / magnetostrictive waveguide; not r56 IRIS HEX wall / ratio pyrometer / UV-fluorescence oil-in-water; not r57 load-cell hopper / PID VOC / four-electrode conductivity; not r58 Rogowski / beta-attenuation / FID-THC occupancy; not r59 UV-DOAS remaining SO2 / aluminum-oxide remaining moisture / strain-gauge load-cell remaining hopper mass. Plants not reused: Nettlewake, Frostlip, Oxbow, Wickspire, Bitternex, Clinkerfell, Miregait, Puddlewick, Fennelholt, Ashholt, Gorsewisp, Flintcrag, Kettermere, Mirebank, Terncrag, Quaycrag, Copsefell, Heatherfen, Charkholt, Kelpcrag, Wickmere, Dapplemere, Hawkmere, Embercrag, Reedwhin, Brackholt, Dewholt, Pebblewick, Fernwick, Mossfell, Kelpfen, Larchmere, Quernspit, Hearthspit, Wexmere, Glaurfen, Brindlecrag, Copsewharf, Kelpwharf, Thornmere, Marlfell, Birchfen, Cressholt, Dunlinholt, Oreholt, Sedgecrag, Yarrowfen, plus r13–r59 plant list.

This round introduces three unused industrial families (venturi remaining-dP steam mass flow, katharometer remaining H2, Clark polarographic remaining dissolved oxygen) on new invented plants. r56/r57/r58/r59 in-flight families and r45 Polarveil LPR vendor token are not restaged.

Adjacencies declared in-pair then kept physically distinct:
- **193 venturi dP steam** is a Bernoulli sqrt(h) remaining slip of a superheat header, not r55 turbine pulse-count, not r47 magmeter, not r29/r34 Coriolis, not r39 vortex-shedding, not r18 clamp-on, not r24 N-16, not r52 thermal-mass, not r53 Fabry-Perot pressure, not r29/r34/r39 frozen-orifice *denial* channels.
- **194 katharometer H2** is a TCD bridge-voltage remaining slip of a chlorate cell-room vent, not r52 thermal-mass capillary, not r31 CTA hot-wire, not r46 paramagnetic O2, not r55 FID THC, not r57 PID VOC, not r22 TDLAS NH3, not r40 532 nm Raman.
- **195 Clark polarographic DO** is a remaining-ppb aqueous oxygen of a boiler deaerator, not r46 paramagnetic O2, not r57 Nernst flue O2, not r52 CLD NOx, not r31 LII, not r51 chilled-mirror, not r59 Al2O3 moisture, not r45 Polarveil LPR.

## Round 64 batch summary (3 pairs, 6 trajectories)

| id | modality (NEW family) | domain | decisions | headline |
|----|----------------------|--------|-----------|----------|
| nelb-r64-193 | venturi remaining-dP steam mass flow of a superheat header (k_v·sqrt(h) t/h, Ventveil last-good denial, 18 min trap-drain floor) | Rindleholt Steam RH-6 header H-5 (invented): 2.50*sqrt(16.00) reconstructs 10.00 t/h while Ventveil still reads 1.80 t/h | REJECT (+0.43) / MODIFY (+0.34) | serialized `2.50*sqrt(16.00)=10.00`; `(10.00/2.50)^2=16.00`; `10.00*2.00=20.00`; conjunctive SOP (Q AND SNR) forbids continue-firing; three-party collusion includes the dP-cloud infra owner; companion t2 trap-drain hold, header ESD refused; sim_or_real=designed |
| nelb-r64-194 | katharometer remaining H2 of a chlorate cell-room vent (k_h·(V−V0) vol%, Kathveil last-good denial, 24 min N2-purge floor) | Woadfen Chlorate WF-9 vent V-3 (invented, HIL dummy in KATH-HIL-7): 15.00*(1.00-0.20) reconstructs 12.00 vol% while Kathveil still reads 1.20 vol% | MODIFY (+0.40) / ACCEPT (+0.35) | serialized `15.00*(1.00-0.20)=12.00` and `48.00/12.00=4.00`; keep-venting refused; filament tech Mira Fenn exonerated (missing filament-zero AE, UTC vs UTC+2); companion t2 new-filament restart; sim_or_real=hil |
| nelb-r64-195 | Clark polarographic remaining DO of a boiler deaerator (k_c·I ppb, Deaerveil last-good denial, 12 min survey floor) | Pellmire Boiler PM-3 deaerator D-4 (invented, simulated CLARK-SIM-5): 2.00*6.00 reconstructs 12.00 ppb while Deaerveil still reads 1.20 ppb | ACCEPT (+0.41) / REJECT (+0.36) | serialized `2.00*6.00=12.00`; `2.00*(6.00-2.00)/4.00=2.00`; bounded ACCEPT of D-4 only; D-1..D-3 out of scope; companion t2 REJECTS skip-survey; sim_or_real=simulated |

Decision spread: REJECT / MODIFY / MODIFY / ACCEPT / ACCEPT / REJECT — **2A/2M/2R**. All three enums used, and all three sit on **leads**. Provenance spread: designed / hil / simulated (one each; never live-plant). IDs `nelb-r64-193`…`195` plus t1/t2 suffixes.

## Raster sidecar
Every record carries `raster` + top-level `gate_snn` + `gate_compute`. Windows {wins[0]:.0f}/{wins[1]:.0f}/{wins[2]:.0f} ms; `window_s == window_ms/1000` exactly; `spikes == round(neurons·rate·window_s)` with zero slack ({n_sp[0]}/{n_sp[1]}/{n_sp[2]} at {rates[0]}/{rates[1]}/{rates[2]} Hz over {n_neu[0]}/{n_neu[1]}/{n_neu[2]} neurons); `energy_pJ = spikes·23` and `energy_uJ = spikes·23e-6` exact ({n_sp[0]*23}/{n_sp[1]*23}/{n_sp[2]*23} pJ). Routing source/target + 3-entry tables + `third_factor` on all three (modulators {tfs[0]} / {tfs[1]} / {tfs[2]}; τe {taus[0]}/{taus[1]}/{taus[2]} s as consistent `tau_e_s`+`tau_e_ms` pairs). Excerpts integer `t_us`, in-window, `neuron_id`-bounded, sorted, full-window by construction, per-spike amplitude with adaptation (0.82**k) plus noise. ISI histograms from the full window, bins ≥1 ms, counts sum to `spikes − distinct_active_neurons` ({isis[0]}/{isis[1]}/{isis[2]}). Same-neuron gaps ≥1100 µs pre-round, ≥1000 µs serialized. `gate_snn` on all three: decisions REJECT/MODIFY/ACCEPT matching each lead trajectory; every rate-declaring population's budget exact against its decision window. `gate_compute.per_check` windows 32–40 ms, budgets exact ({gc[0]} / {gc[1]} / {gc[2]}). Main streams: {events[0]}/{events[1]}/{events[2]} events (inside the 5–40 cap), strictly increasing `t_rel_ms` only (no `t_ms` mix), same-channel refractory ≥0.8 ms (193 venturi pair at 1.4 ms, 194 katharometer pair at 1.2 ms, 195 Clark pair at 1.5 ms).

## Self-critique

### Edge cases added vs still thin
- **Added:** first venturi remaining-dP steam-flow family on a superheat header with a recomputable Q=k_v·sqrt(h) (`10.00 t/h`) plus Bernoulli and steam-load identities and three-party collusion including the dP-cloud infra owner; first katharometer remaining-H2 family on a chlorate cell-room vent with recomputable x=k_h·(V−V0) (`12.00 vol%`) and bridge-impedance identity, plus a resolved-innocent filament tech (timezone-skipped filament-zero, not last-to-badge); first Clark polarographic remaining-DO family on a boiler deaerator with recomputable C=k_c·I (`12.00 ppb`) plus mdot identity; bounded ACCEPT whose out-of-scope clause is adjacent deaerators rather than a hopper/taphole/dump cap; operational t2 on all three (trap-drain hold, new-filament restart, skip-survey refusal); provenance trio designed/hil/simulated; 18 min / 24 min / 12 min slow floors in-stream.
- **Still thin:** (i) 193's k_v is a lumped sqrt(h) factor, not a T/P/beta/discharge table — a density hop that fakes 10.00 t/h inside a 1.80 t/h Ventveil corridor is unwritten; (ii) 194's k_h is a lumped nA/V→vol% gain, not a filament-temperature / carrier-gas map, so a thermal hop that fakes 12.00 vol% is unwritten; (iii) 195's k_c is a lumped nA→ppb factor, not a temperature / membrane-aging table, so a thermal hop that fakes 12.00 ppb inside a 1.20 last-good is unwritten; (iv) vendor-only as a *lead* REJECT on a plant with *no* independent venturi/TCD/Clark head installed yet remains slightly harder — 193/194 still have plant heads; (v) stream amplitudes remain authored constants (raster draws are the only seeded noise); (vi) r56–r59 densification leftovers were left for those rounds' owners.

### Realism of noise / temporal fidelity
- Strong: 193's 10.00 t/h, load 20.00, Bernoulli 16.00, and 18.0 min trap (`6000+1080=7080 s`) recompute from the record; 194's 12.00 vol%, Z 4.00 Ohm, and 24.0 min N2-purge (`2820+1440=4260 s`) recompute; 195's 12.00 ppb, mdot 2.00, and 12.0 min survey (`6000+720=6720 s`) recompute. Raster adaptation (0.82**k plus 4% noise) and the 1.2–1.5 ms physics pairs give the 5–40 stream a raster-scale motif without violating 0.8 ms same-channel refractory.
- **Gaps, honestly:** (i) 5–40 cap still forces heavy thinning (10 Hz venturi kept as 4 h points; 1 Hz TCD kept as 4 V points; 1 Hz Clark kept as 4 I points); (ii) 193's post-stop 15.00 t/h is a later sample, not a closed-loop trap controller; (iii) 194 HIL coupon times an in-service vent isolate that the stream does not independently witness on a second live vent until the new filament starts; (iv) no gate_snn input→output volley pair at raster resolution this round (r04-a1 already staged that).

### Training value (SNN/LSM + agentic)
Distillation targets: venturi Q=k_v·sqrt(h) reconstruction head plus Bernoulli and steam-load identities; conjunctive isolate floor vs continue-firing vs header ESD; Ventveil-infra collusion; katharometer x=k_h·(V−V0) head plus impedance identity; isolate-floor vent vs keep-whole vs cell-room dump; exoneration against last-to-badge social pressure; Clark C=k_c·I and mdot identities; bounded ACCEPT with deaerator-out-of-scope; skip-survey refusal under survey takt. Agentic value concentrates in three patterns: reconstruction-as-SoT on a physical steam/H2/DO load the raw corridor cannot see, earned ACCEPT with an explicit physical out-of-scope object (D-1..D-3), and stop-then-hold so a REJECT does not become a main/room/dump kill.

## What a later leftover-mill round should add (next densification target)
1. **T/P/beta/discharge table** on a non-RH-6 superheat header so a density hop fakes 10.00 t/h inside a 1.80 t/h Ventveil corridor, closing 193's lumped-k_v gap.
2. **Filament-temperature / carrier-gas map** on a non-WF-9 vent so a thermal hop can fake 12.00 vol% while mean bridge voltage looks healthy.
3. **Temperature / membrane-aging table** on a non-PM-3 deaerator so a thermal hop can fake 12.00 ppb inside a 1.20 last-good corridor.
4. **Vendor-only as a lead REJECT** on a plant that has no independent venturi/TCD/Clark head installed yet (193/194 still had plant heads).
5. **Do not restage** VOD-SNN replay, pharma cold-chain, CEMS, FBG glaze, Frostlip quench, Oxbow VRFB, IFOG, transmon, hyperspectral, MEMS array, muon ore-pass, industrial x-ray, optogenetic stim, 905 nm LiDAR snow, clamp-on transit-time, LIBS, QEPAS, LFV, Kaplan LDV, THz-TDS, ECT, TDLAS NH3, lock-in thermography, PAUT TFM, EN CUI, RUS porcelain, N-16 loop flow, helium RGA, Faraday FOCT, blade tip-timing, acoustic pyrometry, SPR, vibrating-wire, microwave-cavity, MFL, NMR T2, nucleonic densitometry, JNT, CRNS, Coriolis, CARS, XRF, Mössbauer, GB-InSAR, ellipsometry, CTA, SPND, LII, PALS, NQR, SFRA, digital shearography, hydrogen permeation, FMCW lining, GPR, Pockels, PEC, confocal, mud-pulse, Barkhausen, Lamb-wave, OCT, DCPD, impact-echo, cyclotron BPM, alanine EPR, ADCP, vortex-shedding, Kr-85 beta, 532 nm Raman, phosphor-lifetime, guided-wave-radar, paramagnetic O2, TOFD, TEOM, magmeter, PDA, acoustoelastic, C-SAM, FDS tanδ, MCSA, EMAT SH, FBRM, ACFM, OFDR, XRD sin²ψ, FSM, Gardon, chilled-mirror, DIC, CLD NOx, proximity orbit, thermal-mass, ER probe, Fabry-Perot, inductive debris, wire-mesh, UCI, MAE, IRIS, ratio pyrometer, UV-fluorescence oil-in-water, zirconia Nernst, PID VOC, contact pulse-echo, Rogowski, beta-attenuation, FID THC, turbine k-factor, magnetostrictive waveguide, UV-DOAS SO2, Al2O3 moisture, load-cell hopper, four-electrode conductivity, Rindleholt RH-6 venturi, Woadfen KATH-HIL-7, or Pellmire CLARK-SIM-5. Leave r56–r59 densification leftovers for those rounds' owners. Do not steal r55–r63 IDs `166`–`192`.

## Verification
`batch-r64.jsonl`: 3 lines, `json.loads`-clean (allow_nan=False), {sizes[0]}/{sizes[1]}/{sizes[2]} bytes (file {{BATCH.stat().st_size}}, sha256 `{file_sha}`). Staged at `/tmp/nelb-r64/` only. Repo gates: `check_records.check_jsonl` with `FactoryStaging(enabled=True)` → 0 errors, 0 warnings, kinds `{{bridge_pair: 3}}`; `python3 pipelines/check_records.py --strict /tmp/nelb-r64` → 0/0; `curate_bridge.raster_status(..., require_raster=True, require_routing_table=True)` → raster_valid and gate_snn_valid true, empty reason codes; `curate_record(...)` → 3× retain / `BRIDGE_EVENTS_ALREADY_GLOBALLY_ORDERED`; `verify_batch_for_frontier(strict=True)` → 3 verified, 0 inconclusive, 0 failed; `python3 pipelines/spike_probe.py --strict /tmp/nelb-r64/batch-r64.jsonl` → loaded 3, unloadable 0, problems [], third_factor_routes 3, gate_snn_records 3, spikes {spikes}, energy_pJ {energy}. Build-time asserts: global time order; same-channel ≥0.8 ms; 5–40 events ({events[0]}/{events[1]}/{events[2]}); excerpt integer bounds, neuron bounds, sort, 1 ms per-neuron floor; ISI identity {isis[0]}/{isis[1]}/{isis[2]}; spike budgets exact; energy pJ/µJ exact; reward totals equal two-decimal component sums ({reward_s}); gate_snn decisions match lead `safety_decision.decision`; `state.sim_or_real` ∈ {{designed, hil, simulated}}; `meta.round=64`, `meta.factory=neuromorphic-event-language-bridge`, `meta.generator=grok-4.6`, `meta.run_label=2026-09-02-final-heavy`; `meta.rights` 15-key RM-793 stamp (`intended_use=research_only`, `linear_issue=RM-793`, `generated_at={GENERATED_AT}`); no hidden-reasoning keys; no `provenance` objects; no live-plant claims; no `training_ready`; all 9 record/trajectory ids unique. Raster seeds 202664193/202664194/202664195, MT19937.

Honest novelty accounting: 3/3 modality families are new versus the whole committed factory and versus staged leftover-mill r13–r59 (and in-flight r57/r58 envelopes). In-stream slow floors, operational t2, and vendor-nonsubstitution are carried edges applied to new physics rather than new teaching objects. Three-party collusion and exoneration were already taught on r13 quench/VRFB and r46 TOFD/r47 PDA, so those heads are carried onto new sensors. Against that: bounded-accept-with-scope-limit, reconstruction-as-SoT, conjunctive SOP, and custody vocabulary are carried; the 5–40 cap is a density constraint not a new teaching object; 51 prior leftover-mill rounds already taught custody/governance at high sophistication. Net: about two-fifths of the round's scenario/edge mass is genuinely novel.

Novel coverage: 40%
"""
    NOTES.write_text(notes, encoding="utf-8")
    print("wrote", NOTES, "bytes", NOTES.stat().st_size)


def main():
    occupancy_preflight()
    records = [rec_193(), rec_194(), rec_195()]
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
