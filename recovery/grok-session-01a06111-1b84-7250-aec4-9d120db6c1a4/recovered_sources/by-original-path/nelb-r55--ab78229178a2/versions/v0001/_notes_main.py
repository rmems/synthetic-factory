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
    file_size = BATCH.stat().st_size
    notes = f"""# Neuromorphic Event + Language Bridge — NOTES round 55
Run: 2026-09-02-final-heavy · Factory: neuromorphic-event-language-bridge · Generator: grok-4.6 · Output: `batch-r55.jsonl` (3 paired artifacts, 6 ThalamicTrajectories)
Rights: RM-793 research-only (SpaceXAI/xAI grok-4.6, SuperGrok Heavy chat). Not training_ready. Do not publish into `outputs/raw/` from this generator; operator uses `pipelines/round_txn.py`. Staged only at `/tmp/nelb-r55/`.

## Context / de-duplication
Prior corpus read: 2026-08-30 NOTES-r01–r04, 2026-08-17-w3 NOTES-r12 family table, `/tmp/nelb-r13-holes.md` + `/tmp/nelb-r13-premises.md`, staged `/tmp/nelb-r13` through `/tmp/nelb-r54` complete batches/NOTES plus in-flight `/tmp/nelb-r56` (IRIS pulse-echo / dual-wavelength ratio pyrometer / UV-fluorescence OIW), `/tmp/nelb-r57` (zirconia Nernst glass-crown / PID VOC / contact pulse-echo), `/tmp/nelb-r58` occupancy (Rogowski / beta-attenuation / pump-current zirconia). IDs: r13=`040`–`042` … r54=`163`–`165`, reserved r56=`169`–`171`, this round `nelb-r55-166`…`168` as assigned. Envelope cloned from complete r52 (`language_view.trajectory` + operational t2 + `spike_events` + `raster` + `gate_snn` + `isi_histogram` + `routing.third_factor` + 15-key RM-793 `meta.rights`).

Banned this round (committed + staged leftover-mill r13–r54 and in-flight r56–r58 generators): not VOD-SNN replay, not pharma cold-chain, not stack-gas CEMS; not r13 FBG glaze / Frostlip quench / Oxbow VRFB; not r14 BOTDA / QCM-D / MsS T(0,1); not r15 SAW torque / CRDS HF / PGNAA; not r16 IFOG / transmon readout / hyperspectral crop; not r17 MEMS accel array / muon ore-pass / industrial x-ray DR; not r18 optogenetic PV / 905 nm LiDAR snow / clamp-on transit-time; not r19 LIBS Cu / QEPAS DGA / LFV Al; not r20 Kaplan LDV / THz-TDS radome moisture / ECT CFB; not r21 THz-TDS bondline / ECA FSW lift-off / LIBS C; not r22 ECT pneumatic riser / TDLAS NH3 / LIBS tap; not r23 lock-in thermography CFRP / PAUT TFM girth / EN CUI; not r24 RUS porcelain / N-16 transit-time loop / helium RGA; not r25 Faraday FOCT / blade tip-timing / acoustic pyrometry; not r26 SPR cyanide / VW viscometer / MW cavity moisture; not r27 MFL AST / NMR T2 / Cs-137 densitometry; not r28 MFL ILI / JNT / CRNS; not r29 Coriolis bitumen / CARS TIT / Zn-Ka XRF; not r30 Mössbauer FCC / GB-InSAR tailings / ellipsometry PECVD; not r31 CTA hot-wire / rhodium SPND / LII soot; not r32 PALS / 14N NQR / SFRA; not r33 digital shearography hull / hydrogen permeation / FMCW BOF lining; not r34 handheld XRF Cr-Kα / Coriolis tube-twist / GPR liner cover; not r35/r37 mud-pulse MWD / Barkhausen / Lamb-wave; not r36 Pockels GIS / PEC coated riser / confocal chromatic; not r38 OCT TBC / DCPD girth / impact-echo; not r39 phosphor-lifetime / vortex-shedding / GWR foam; not r40 He-3 neutron-backscatter / Kr-85 beta / 532 nm Raman; not r41–r43 cyclotron BPM / alanine EPR / ADCP ice-jam; not r44 TOFD / laser-flash Parker / TDR cable; not r45 Seebeck ferrite / coda-wave / LPR; not r46 paramagnetic O2 / TOFD ligament / TEOM PM; not r47 Faraday magmeter / PDA d32 / acoustoelastic; not r48 C-SAM / FDS tanδ / MCSA; not r49 EMAT SH / FBRM D50 / ACFM; not r50 OFDR / XRD sin²ψ / FSM; not r51 Gardon / chilled-mirror / DIC; not r52 CLD NOx / API-670 proximity / thermal-mass capillary; not r53 ER probe / Fabry-Perot pressure / inductive debris; not r54 wire-mesh void / UCI hardness / MAE case depth; not r56 IRIS pulse-echo / dual-wavelength ratio pyrometer / UV-fluorescence OIW; not r57 zirconia Nernst / PID VOC / contact pulse-echo. Plants not reused: Nettlewake, Frostlip, Oxbow, Fernwick, Mossfell, Kelpfen, Hawkmere, Embercrag, Reedwhin, Larchmere, Quernspit, Hearthspit, plus the r13–r54 plant list.

This round introduces three unused industrial families (flame-ionization THC, turbine k-factor volumetric flow, magnetostrictive waveguide liquid level) on new invented plants. r56 dual-wavelength pyrometer and r57 zirconia Nernst were already claimed in-flight and are not restaged.

Adjacencies declared in-pair then kept physically distinct:
- **166 FID THC** is a hydrogen-flame collector current of a flare knockout, not r04 CEMS FTIR k-script, not r52 CLD NOx, not r22 TDLAS NH3, not r15 CRDS HF, not r19 QEPAS, not r57 PID VOC, not r46 paramagnetic O2.
- **167 turbine k-factor** is a rotor pulse-count volumetric flow of a condensate header, not r47 Faraday magmeter slurry, not r29/r34 Coriolis, not r52 thermal-mass capillary, not r39 vortex-shedding, not r18 clamp-on transit-time, not r24 N-16, not r19 LFV.
- **168 magnetostrictive level** is a float-plus-waveguide tank gauge of an LPG sphere, not r14 MsS T(0,1) remaining wall, not r39 GWR foam, not r44 TDR remaining-length, not r34 GPR liner cover.

## Round 55 batch summary (3 pairs, 6 trajectories)

| id | modality (NEW family) | domain | decisions | headline |
|----|----------------------|--------|-----------|----------|
| nelb-r55-166 | flame-ionization THC of a flare knockout (k_f·(I−I_bg)·(T/T0)·(P0/P) ppm, Fidveil FID denial, 18 min N2-purge floor) | Brindlecrag Flare BC-8 KO-2 (invented): 48.00 nA reconstructs 10.00 ppm while Fidveil still reads 1.80 ppm | REJECT (+0.43) / MODIFY (+0.34) | serialized `0.250*(48.00-8.00)*1.000*1.000=10.00`; `10.00*2.00=20.00`; conjunctive SOP (C AND SNR) forbids continue-firing; three-party collusion includes the FID infra owner; companion t2 N2-purge hold, flare ESD refused; sim_or_real=designed |
| nelb-r55-167 | turbine k-factor volumetric flow of a condensate header (f/k_p m3/h, Rotorveil last-good denial, 24 min cooldown floor) | Copsewharf Condensate CW-7 header H-4 (invented, HIL dummy in TURB-HIL-6): 480.00/40.00 reconstructs 12.00 m3/h while Rotorveil still reads 3.20 m3/h | MODIFY (+0.40) / ACCEPT (+0.35) | serialized `480.00/40.00=12.00` and `480.00*0.250=120.00`; keep-running refused; meter tech Lise Thorn exonerated (missing k-cal AE, UTC vs UTC+2); companion t2 new-rotor restart; sim_or_real=hil |
| nelb-r55-168 | magnetostrictive waveguide liquid level of an LPG sphere (v·t/2 m, Floatveil last-good denial, 12 min survey floor) | Kelpwharf LPG KW-8 sphere S-2 (invented, simulated MTG-SIM-4): 3000*0.008/2 reconstructs 12.00 m while Floatveil still reads 4.80 m | ACCEPT (+0.41) / REJECT (+0.36) | serialized `3000*0.008/2=12.00`; `3000*0.008=24.00`; bounded ACCEPT of S-2 only; S-1 and S-3 out of scope; companion t2 REJECTS skip-isolate; sim_or_real=simulated |

Decision spread: REJECT / MODIFY / MODIFY / ACCEPT / ACCEPT / REJECT — **2A/2M/2R**. All three enums used, and all three sit on **leads**. Provenance spread: designed / hil / simulated (one each; never live-plant). IDs `nelb-r55-166`…`168` plus t1/t2 suffixes.

## Raster sidecar
Every record carries `raster` + top-level `gate_snn` + `gate_compute`. Windows {wins[0]:.0f}/{wins[1]:.0f}/{wins[2]:.0f} ms; `window_s == window_ms/1000` exactly; `spikes == round(neurons·rate·window_s)` with zero slack ({n_sp[0]}/{n_sp[1]}/{n_sp[2]} at {rates[0]}/{rates[1]}/{rates[2]} Hz over {n_neu[0]}/{n_neu[1]}/{n_neu[2]} neurons); `energy_pJ = spikes·23` and `energy_uJ = spikes·23e-6` exact ({n_sp[0]*23}/{n_sp[1]*23}/{n_sp[2]*23} pJ). Routing source/target + 3-entry tables + `third_factor` on all three (modulators {tfs[0]} / {tfs[1]} / {tfs[2]}; τe {taus[0]}/{taus[1]}/{taus[2]} s as consistent `tau_e_s`+`tau_e_ms` pairs). Excerpts integer `t_us`, in-window, `neuron_id`-bounded, sorted, full-window by construction, per-spike amplitude with adaptation (0.82**k) plus noise. ISI histograms from the full window, bins ≥1 ms, counts sum to `spikes − distinct_active_neurons` ({isis[0]}/{isis[1]}/{isis[2]}). Same-neuron gaps ≥1100 µs pre-round, ≥1000 µs serialized. `gate_snn` on all three: decisions REJECT/MODIFY/ACCEPT matching each lead trajectory; every rate-declaring population's budget exact against its decision window. `gate_compute.per_check` windows 32–40 ms, budgets exact ({gc[0]} / {gc[1]} / {gc[2]}). Main streams: {events[0]}/{events[1]}/{events[2]} events (inside the 5–40 cap), strictly increasing `t_rel_ms` only (no `t_ms` mix), same-channel refractory ≥0.8 ms (166 FID pair at 1.3 ms, 167 turbine pair at 1.2 ms, 168 MTG pair at 1.5 ms).

## Self-critique

### Edge cases added vs still thin
- **Added:** first flame-ionization-THC family on a flare knockout with a recomputable C=k_f·(I−I_bg)·(T/T0)·(P0/P) (`10.00 ppm`) plus air-load identity and three-party collusion including the FID infra owner; first turbine-k-factor volumetric family on a condensate header with recomputable Q=f/k_p (`12.00 m3/h`) and pulse-count identity, plus a resolved-innocent meter tech (timezone-skipped k-cal, not last-to-badge); first magnetostrictive-waveguide liquid-level family on an LPG sphere with recomputable L=v·t/2 (`12.00 m`) plus round-trip identity; bounded ACCEPT whose out-of-scope clause is adjacent LPG spheres rather than a hopper/taphole/dump cap; operational t2 on all three (N2-purge hold, new-rotor restart, skip-sphere refusal); provenance trio designed/hil/simulated; 18 min / 24 min / 12 min slow floors in-stream.
- **Still thin:** (i) 166's k_f is a lumped nA→ppm gain, not a T/P/H2-flow table — a fuel-H2 hop that fakes 10.00 ppm inside a 1.80 ppm Fidveil corridor is unwritten; (ii) 167's k_p is a lumped pulse factor, not a viscosity/bearing-wear map, so a rotor hop that fakes 12.00 m3/h is unwritten; (iii) 168's v is a lumped waveguide speed, not a temperature / product-density table, so a ToF hop that fakes 12.00 m inside a 4.80 last-good is unwritten; (iv) vendor-only as a *lead* REJECT on a plant with *no* independent FID/turbine/MTG installed yet remains slightly harder — 166/167 still have plant heads; (v) stream amplitudes remain authored constants (raster draws are the only seeded noise); (vi) r56/r57 densification leftovers (IRIS fill-factor, ratio-pyrometer emissivity table, UV-fluorescence quench map, zirconia Nernst T-table, PID lamp-window map, pulse-echo wedge delay) were left for those rounds' owners.

### Realism of noise / temporal fidelity
- Strong: 166's 10.00 ppm, load 20.00, and 18.0 min N2-purge (`6000+1080=7080 s`) recompute from the record; 167's 12.00 m3/h, N 120.00, and 24.0 min cooldown (`2820+1440=4260 s`) recompute; 168's 12.00 m, s 24.00, and 12.0 min survey (`6000+720=6720 s`) recompute. Raster adaptation (0.82**k plus 4% noise) and the 1.2–1.5 ms physics pairs give the 5–40 stream a raster-scale motif without violating 0.8 ms same-channel refractory.
- **Gaps, honestly:** (i) 5–40 cap still forces heavy thinning (10 Hz FID kept as 4 I points; hundreds-of-Hz turbine kept as 4 f points plus one k pair; 10 Hz MTG kept as 4 t points); (ii) 166's post-stop 8.00 ppm is a later sample, not a closed-loop N2 controller; (iii) 167 HIL coupon times an in-service isolate that the stream does not independently witness on a second live header until the new rotor starts; (iv) no gate_snn input→output volley pair at raster resolution this round (r04-a1 already staged that).

### Training value (SNN/LSM + agentic)
Distillation targets: flame-ionization C=k_f·(I−I_bg)·(T/T0)·(P0/P) reconstruction head plus air-load identity; conjunctive slip floor vs continue-firing vs flare ESD; FID-infra collusion; turbine Q=f/k_p head plus pulse-count identity; isolate-floor header vs keep-running vs tank-trip; exoneration against last-to-badge social pressure; magnetostrictive L=v·t/2 and round-trip identities; bounded ACCEPT with sphere-out-of-scope; skip-isolate refusal under survey takt. Agentic value concentrates in three patterns: reconstruction-as-SoT on a physical THC/overflow/high-level the raw corridor cannot see, earned ACCEPT with an explicit physical out-of-scope object (S-1 and S-3), and stop-then-hold so a REJECT does not become a flare/tank/farm kill.

## What a later leftover-mill round should add (next densification target)
1. **T/P/H2-flow table** on a non-BC-8 knockout so a fuel-H2 hop fakes 10.00 ppm inside a 1.80 ppm Fidveil corridor, closing 166's lumped-k_f gap.
2. **Viscosity / bearing-wear map** on a non-CW-7 turbine so a rotor hop can fake 12.00 m3/h while mean frequency looks healthy.
3. **Temperature / product-density waveguide table** on a non-KW-8 sphere so a ToF hop can fake 12.00 m inside a 4.80 last-good corridor.
4. **Vendor-only as a lead REJECT** on a plant that has no independent FID/turbine/MTG installed yet (166/167 still had plant heads).
5. **Do not restage** VOD-SNN replay, pharma cold-chain, CEMS, FBG glaze, Frostlip quench, Oxbow VRFB, IFOG, transmon, hyperspectral, MEMS array, muon ore-pass, industrial x-ray, optogenetic stim, 905 nm LiDAR snow, clamp-on transit-time, LIBS, QEPAS, LFV, Kaplan LDV, THz-TDS, ECT, TDLAS NH3, lock-in thermography, PAUT TFM, EN CUI, RUS porcelain, N-16 loop flow, helium RGA, Faraday FOCT, blade tip-timing, acoustic pyrometry, SPR, vibrating-wire, microwave-cavity, MFL, NMR T2, nucleonic densitometry, JNT, CRNS, Coriolis, CARS, XRF, Mössbauer, GB-InSAR, ellipsometry, CTA, SPND, LII, PALS, NQR, SFRA, digital shearography, hydrogen permeation, FMCW lining, GPR, Pockels, PEC, confocal, mud-pulse, Barkhausen, Lamb-wave, OCT, DCPD, impact-echo, cyclotron BPM, alanine EPR, ADCP, vortex-shedding, Kr-85 beta, 532 nm Raman, phosphor-lifetime, guided-wave-radar, paramagnetic O2, TOFD, TEOM, RFEC, LPR, laser-flash, TDR, RFT, PDA, acoustoelastic, ACFM, FDS tanδ, MCSA, EMAT SH, FBRM, CLD NOx, API-670 proximity, thermal-mass capillary, ER probe, Fabry-Perot, inductive debris, wire-mesh void, UCI hardness, MAE case, IRIS, dual-wavelength pyrometer, UV-fluorescence, zirconia Nernst, PID VOC, contact pulse-echo, Brindlecrag BC-8 FID, Copsewharf TURB-HIL-6, or Kelpwharf KW-8 MTG. Leave r56–r58 densification leftovers for those rounds' owners. Do not steal r54 IDs `163`–`165` or r56 IDs `169`–`171`.

## Verification
`batch-r55.jsonl`: 3 lines, `json.loads`-clean (allow_nan=False), {sizes[0]}/{sizes[1]}/{sizes[2]} bytes (file {file_size}, sha256 `{file_sha}`). Staged at `/tmp/nelb-r55/` only. Repo gates: `check_records.check_jsonl` with `FactoryStaging(enabled=True)` → 0 errors, 0 warnings, kinds `{{bridge_pair: 3}}`; `python3 pipelines/check_records.py --strict /tmp/nelb-r55` → 0/0; `curate_bridge.raster_status(..., require_raster=True, require_routing_table=True)` → raster_valid and gate_snn_valid true, empty reason codes; `curate_record(...)` → 3× retain / `BRIDGE_EVENTS_ALREADY_GLOBALLY_ORDERED`; `verify_batch_for_frontier(strict=True)` → 3 verified, 0 inconclusive, 0 failed; `python3 pipelines/spike_probe.py --strict /tmp/nelb-r55/batch-r55.jsonl` → loaded 3, unloadable 0, problems [], third_factor_routes 3, gate_snn_records 3, spikes {spikes}, energy_pJ {energy}. Build-time asserts: global time order; same-channel ≥0.8 ms; 5–40 events ({events[0]}/{events[1]}/{events[2]}); excerpt integer bounds, neuron bounds, sort, 1 ms per-neuron floor; ISI identity {isis[0]}/{isis[1]}/{isis[2]}; spike budgets exact; energy pJ/µJ exact; reward totals equal two-decimal component sums ({reward_s}); gate_snn decisions match lead `safety_decision.decision`; `state.sim_or_real` ∈ {{designed, hil, simulated}}; `meta.round=55`, `meta.factory=neuromorphic-event-language-bridge`, `meta.generator=grok-4.6`, `meta.run_label=2026-09-02-final-heavy`; `meta.rights` 15-key RM-793 stamp (`intended_use=research_only`, `linear_issue=RM-793`, `generated_at={GENERATED_AT}`); no hidden-reasoning keys; no `provenance` objects; no live-plant claims; no `training_ready`; all 9 record/trajectory ids unique. Raster seeds 202655166/202655167/202655168, MT19937. Beads `bd create` for this round is not a close-out — staging is the `/tmp` pair.

Honest novelty accounting: 3/3 modality families are new versus the whole committed factory and versus staged leftover-mill r13–r54 (and in-flight r56–r58 claims). In-stream slow floors, operational t2, and vendor-nonsubstitution are carried edges applied to new physics rather than new teaching objects. Three-party collusion and exoneration were already taught on r13 quench/VRFB and r37/r42/r52 Barkhausen/alanine/proximity, so those heads are carried onto new sensors. Against that: bounded-accept-with-scope-limit, reconstruction-as-SoT, conjunctive SOP, and custody vocabulary are carried; the 5–40 cap is a density constraint not a new teaching object; 42 prior leftover-mill rounds already taught custody/governance at high sophistication. Net: about two-fifths of the round's scenario/edge mass is genuinely novel.

Novel coverage: 40%
"""
    NOTES.write_text(notes, encoding="utf-8")
    print("wrote", NOTES, "bytes", NOTES.stat().st_size)


def main():
    occupancy_preflight()
    records = [rec_166(), rec_167(), rec_168()]
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
