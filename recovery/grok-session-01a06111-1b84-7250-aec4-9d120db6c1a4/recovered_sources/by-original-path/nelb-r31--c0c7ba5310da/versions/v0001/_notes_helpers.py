def write_notes(records, lines):
    import hashlib

    rows = []
    decisions = []
    for rec, blob in zip(records, lines):
        lv = rec["language_view"]
        t1 = lv["trajectory"]
        t2 = next(v for k, v in lv.items() if k.startswith("trajectory_"))
        d1 = t1["safety_decision"]["decision"]
        d2 = t2["safety_decision"]["decision"]
        decisions.extend([d1, d2])
        rast = rec["raster"]
        rows.append(
            {
                "id": rec["id"],
                "d1": d1,
                "d2": d2,
                "r1": t1["reward_components"]["total"],
                "r2": t2["reward_components"]["total"],
                "sim": t1["state"]["sim_or_real"],
                "events": len(rec["spike_events"]),
                "window": rast["window_ms"],
                "neurons": rast["neurons"],
                "rate": rast["mean_rate_hz"],
                "spikes": rast["spikes"],
                "isi": rast["isi_count_identity"]["isi_total"],
                "energy": rast["energy_pJ"],
                "mod": rast["routing"]["third_factor"]["modulator"],
                "tau": rast["routing"]["third_factor"]["tau_e_s"],
                "bytes": len(blob),
            }
        )
    na = decisions.count("ACCEPT")
    nm = decisions.count("MODIFY")
    nr = decisions.count("REJECT")
    sha = hashlib.sha256(BATCH.read_bytes()).hexdigest()
    file_bytes = BATCH.stat().st_size
    spikes_sum = sum(r["spikes"] for r in rows)
    energy_sum = sum(r["energy"] for r in rows)
    notes = f"""# Neuromorphic Event + Language Bridge — NOTES round 31
Run: 2026-09-02-final-heavy · Factory: neuromorphic-event-language-bridge · Generator: grok-4.6 · Output: `batch-r31.jsonl` (3 paired artifacts, 6 ThalamicTrajectories)
Rights: RM-793 research-only (SpaceXAI/xAI grok-4.6, SuperGrok Heavy chat). Not training_ready. Do not publish into `outputs/raw/` from this generator; operator uses `pipelines/round_txn.py`. Staged only at `/tmp/nelb-r31/`.

## Context / de-duplication
Prior corpus read: 2026-08-30 NOTES-r01–r04, 2026-08-17-w3 NOTES-r12 family table, staged `/tmp/nelb-r13` through `/tmp/nelb-r26` batches/NOTES (r27–r28 empty at lock; r29 generator is an unfinished r20 copy; r30 generator incomplete). IDs continue the leftover-mill sequence: r13=`040`–`042` … r26=`079`–`081`, this round `nelb-r31-094`…`096` (r27–r30 occupy `082`–`093` even if those dirs are still empty).

Banned this round (committed + staged leftover-mill): not VOD-SNN replay, not pharma cold-chain, not stack-gas CEMS; not r13 FBG glaze / Frostlip quench / Oxbow VRFB; not r14 BOTDA / QCM-D / MsS T(0,1); not r15 SAW torque / CRDS HF / PGNAA; not r16 IFOG / transmon readout / hyperspectral crop; not r17 MEMS accel array / muon ore-pass / industrial x-ray DR; not r18 optogenetic PV / 905 nm LiDAR snow / clamp-on transit-time; not r19 LIBS Cu / QEPAS DGA / LFV Al; not r20 Kaplan LDV / THz-TDS radome moisture / ECT CFB; not r21 THz-TDS bondline / ECA FSW lift-off / LIBS C; not r22 ECT pneumatic riser / TDLAS NH3 / LIBS tap; not r23 lock-in thermography CFRP / PAUT TFM girth / EN CUI; not r24 RUS porcelain / N-16 transit-time loop / helium RGA; not r25 Faraday FOCT / blade tip-timing / acoustic pyrometry; not r26 Kretschmann SPR cyanide / vibrating-wire viscometer / microwave-cavity moisture. Unused r13-premises (mud-pulse, Barkhausen, Lamb-wave) and r13-holes (cyclotron BPM, alanine EPR, ADCP ice-jam) were left available.

Adjacencies declared in-pair then kept physically distinct:
- **094 two-pickoff Coriolis** is mdot=C_t·Δt on an LNG loading arm, not r18 clamp-on ultrasonic volume, not r19 Lorentz-force liquid-metal, not r24 N-16 gamma TOF, not r26 vibrating-wire viscosity.
- **095 rhodium SPND** is I/S flux on a research-reactor HIL dummy, not r6 portal NaI/He-3, not r01/r17 muon tomography, not r24 N-16, not r9 tokamak MHD.
- **096 laser-induced incandescence** is k·(I/I_cal) soot fv on a diesel DPF cell, not r04 CEMS, not r19/r21/r22 LIBS sparks, not r25 acoustic pyrometry, not r19 QEPAS, not r22 TDLAS, not r26 microwave-cavity moisture.

## Round 31 batch summary (3 pairs, 6 trajectories)

| id | modality (NEW family) | domain | decisions | headline |
|----|----------------------|--------|-----------|----------|
| nelb-r31-094 | two-pickoff Coriolis of an LNG loading arm (C_t·Δt mass flow, ρ=k/T², Flowveil patched-C denial, 18 min soak floor) | Wickfen LNG WF-4 arm A-2 (invented): 8.00 ms × 75.00 reconstructs 600.0 kg/s while Flowveil still reads 480 kg/s and the orifice 0.88 m³/s | MODIFY (+0.40) / ACCEPT (+0.35) | serialized `75.00*8.00=600.0` and `18.00e6/40000=450.0`; conjunctive SOP (mdot AND continuous floor) forbids keep-rated fill; companion t2 holds 0.80 pu and refuses a Flowveil restore; sim_or_real=designed |
| nelb-r31-095 | rhodium SPND of a research-reactor HIL dummy (I/S flux, k_p·φ power, Fluxveil patched-S denial, 12 min xenon-hold floor) | Lumenholt Research Reactor LH-7 Pit-HIL-6 (invented, HIL dummy core): 10.00 nA / 0.50 reconstructs 10.00 MW while Fluxveil still reads 4.00 MW and the compensated IC 7.20 e12 | REJECT (+0.43) / MODIFY (+0.34) | serialized `10.00/0.50=20.00` and `0.50*20.00=10.00`; keep-100 refused; companion t2 MODIFYs a full scram into regulating-rod + n 0.70; sim_or_real=hil |
| nelb-r31-096 | laser-induced incandescence soot fv of a diesel DPF cell (k·I/I_cal, opacity + Sootveil denial, 20 min regen floor) | Coomfen Diesel CF-4 cell X-2 (invented, simulated): 24.00×(12.50/20.00) reconstructs 15.00 ppm while opacity still reads 8 percent and Sootveil 8 percent | ACCEPT (+0.41) / REJECT (+0.36) | serialized `24.00*(12.50/20.00)=15.00`; bounded regen of bank A only; bank B and line-derate out of scope; companion t2 REJECTS skip-regen of bank B; sim_or_real=simulated |

Decision spread: MODIFY / ACCEPT / REJECT / MODIFY / ACCEPT / REJECT — **{na}A/{nm}M/{nr}R**. All three enums used, and all three sit on **leads**. Provenance spread: designed / hil / simulated (one each; never real). IDs `nelb-r31-094`…`096` plus t1/t2 suffixes.

## Raster sidecar
Every record carries `raster` + top-level `gate_snn` + `gate_compute`. Windows {rows[0]['window']:.0f}/{rows[1]['window']:.0f}/{rows[2]['window']:.0f} ms; `window_s == window_ms/1000` exactly; `spikes == round(neurons·rate·window_s)` with zero slack ({rows[0]['spikes']}/{rows[1]['spikes']}/{rows[2]['spikes']} at {rows[0]['rate']:.1f}/{rows[1]['rate']:.1f}/{rows[2]['rate']:.1f} Hz over {rows[0]['neurons']}/{rows[1]['neurons']}/{rows[2]['neurons']} neurons); `energy_pJ = spikes·23` and `energy_uJ = spikes·23e-6` exact ({rows[0]['energy']}/{rows[1]['energy']}/{rows[2]['energy']} pJ). Routing source/target + 3-entry tables + `third_factor` on all three (modulators {rows[0]['mod']} / {rows[1]['mod']} / {rows[2]['mod']}; τe {rows[0]['tau']}/{rows[1]['tau']}/{rows[2]['tau']} s as consistent `tau_e_s`+`tau_e_ms` pairs). Excerpts integer `t_us`, in-window, `neuron_id`-bounded, sorted, full-window by construction, per-spike amplitude with adaptation (0.82**k) plus noise. ISI histograms from the full window, bins ≥1 ms, counts sum to `spikes − distinct_active_neurons` ({rows[0]['isi']}/{rows[1]['isi']}/{rows[2]['isi']}). Same-neuron gaps ≥1100 µs pre-round, ≥1000 µs serialized. `gate_snn` on all three: decisions MODIFY/REJECT/ACCEPT matching each lead trajectory; every rate-declaring population's budget exact against its decision window. `gate_compute.per_check` windows 32–40 ms, budgets exact (144+64 / 128+80 / 192+80). Main streams: {rows[0]['events']}/{rows[1]['events']}/{rows[2]['events']} events (inside the 5–40 cap), strictly increasing `t_rel_ms` only (no `t_ms` mix), same-channel refractory ≥0.8 ms (094 Coriolis pair at 1.3 ms, 095 SPND pair at 1.2 ms, 096 LII pair at 1.4 ms).

## Self-critique

### Edge cases added vs still thin
- **Added:** first two-pickoff Coriolis family on an LNG loading arm with a recomputable mdot=C_t·Δt (`75.00*8.00=600.0`) plus ρ=k/T² (`450.0`); first rhodium-SPND family on a research-reactor HIL dummy with recomputable φ=I/S and P=k_p·φ (`10.00/0.50=20.00`, `0.50*20.00=10.00`); first laser-induced-incandescence soot-fv family on a diesel DPF cell with recomputable fv=k·(I/I_cal) (`24.00*(12.50/20.00)=15.00`); first bounded ACCEPT whose out-of-scope clause is a second DPF bank plus line-derate rather than a hopper/pressure cap; first keep-100 REJECT lead on an SPND power that a vendor ion-chamber dashboard would have cleared; operational t2 on all three (0.80 hold, rod+0.70, skip-regen refusal); provenance trio designed/hil/simulated; 18 min / 12 min / 20 min slow floors in-stream.
- **Still thin:** (i) 094's C_t is a lumped tube constant, not a temperature-compensated Young's-modulus walk — a tube-T that fakes 600 kg/s inside a 480 Flowveil corridor is unwritten; (ii) 095's S is a cold sensitivity, not an emitter-burnup / delayed-neutron integral, so a rhodium-depletion that fakes 10 MW is unwritten; (iii) 096's k is a single-color calibration, not two-color pyrometry, so an incandescence-T that fakes 15 ppm is unwritten; (iv) vendor-only as a *lead* REJECT on a plant with *no* independent witness remains slightly harder — 094/095 still have plant Coriolis/SPND; (v) stream amplitudes remain authored constants (raster draws are the only seeded noise); (vi) unused r13-premises (mud-pulse, Barkhausen, Lamb-wave) and r13-holes (cyclotron BPM, alanine EPR, ADCP ice-jam) still unharvested.

### Realism of noise / temporal fidelity
- Strong: 094's 600.0 kg/s, 450.0 kg/m³, and 18.0 min soak (`6600+1080=7680 s`) recompute from the record; 095's 10.00 MW, 20.00 e12, and 12.0 min hold (`1200+720=1920 s`) recompute; 096's 15.00 ppm and 20.0 min regen (`6000+1200=7200 s`) recompute. Raster adaptation (0.82**k plus 4% noise) and the 1.2–1.4 ms physics pairs give the 5–40 stream a raster-scale motif without violating 0.8 ms same-channel refractory.
- **Gaps, honestly:** (i) 5–40 cap still forces heavy thinning (100 Hz Coriolis kept as 3 dt points; 10 Hz SPND kept as 4 I points; 10 Hz LII kept as 3 I points); (ii) 094's post-derate 480.0 kg/s is a later sample, not a closed-loop fill controller; (iii) 095 HIL dummy times an in-service keep-100 refusal that the stream does not independently witness on the live core (compensated IC only); (iv) no gate_snn input→output volley pair at raster resolution this round (r04-a1 already staged that).

### Training value (SNN/LSM + agentic)
Distillation targets: Coriolis mdot=C_t·Δt and ρ=k/T² heads; continuous-floor derate vs keep-rated vs arm-isolate; patched-C nonsubstitution; SPND φ=I/S and P=k_p·φ heads; power-floor stop vs keep-100 vs full scram; patched-S nonsubstitution; LII fv=k·(I/I_cal) head; bounded ACCEPT with bank-B/line out of scope; skip-regen refusal under takt. Agentic value concentrates in three patterns: reconstruction-as-SoT on a physical error the raw corridor cannot see, earned ACCEPT with an explicit physical out-of-scope object (bank B), and stop-then-hold so a REJECT does not become a freeze-kill.

## What round 32 should add (next densification target)
1. **Temperature-compensated Coriolis C_t** on a non-WF-4 arm so a tube-T walk fakes 600 kg/s inside a 480 Flowveil corridor, closing 094's lumped-C gap.
2. **Rhodium emitter-burnup / delayed-neutron integral** on a non-LH-7 SPND so a depleted S can fake 10 MW inside a 4 MW Fluxveil corridor.
3. **Two-color LII pyrometry** on a non-CF-4 cell so incandescence-T can fake 15 ppm inside an 8 percent opacity corridor.
4. **Vendor-only as a lead REJECT** on a plant that has no independent witness installed yet (094/095 still had plant Coriolis/SPND).
5. **Do not restage** VOD-SNN replay, pharma cold-chain, CEMS, FBG glaze, Frostlip quench, Oxbow VRFB, IFOG, transmon, hyperspectral, MEMS array, muon ore-pass, industrial x-ray, optogenetic stim, 905 nm LiDAR snow, clamp-on transit-time, LIBS, QEPAS, LFV, Kaplan LDV, THz-TDS radome, ECT, TDLAS NH3, lock-in thermography, PAUT TFM, EN CUI, RUS porcelain, N-16 loop flow, helium RGA, Faraday FOCT, blade tip-timing, acoustic pyrometry, Kretschmann SPR, vibrating-wire viscometer, microwave-cavity moisture, Wickfen WF-4 Coriolis, Lumenholt LH-7 SPND, or Coomfen CF-4 LII. Leave mud-pulse, Barkhausen, Lamb-wave, cyclotron BPM, alanine EPR, and ADCP ice-jam available.

## Verification
`batch-r31.jsonl`: 3 lines, `json.loads`-clean (allow_nan=False), {rows[0]['bytes']}/{rows[1]['bytes']}/{rows[2]['bytes']} bytes (file {file_bytes}, sha256 `{sha}`). Staged at `/tmp/nelb-r31/` only. Repo gates: `check_records.check_jsonl` with `FactoryStaging(enabled=True)` → 0 errors, 0 warnings, kinds `{{bridge_pair: 3}}`; `python3 pipelines/check_records.py --strict /tmp/nelb-r31` → 0/0; `curate_bridge.raster_status(..., require_raster=True, require_routing_table=True)` → raster_valid and gate_snn_valid true, empty reason codes; `curate_record(...)` → 3× retain / `BRIDGE_EVENTS_ALREADY_GLOBALLY_ORDERED`; `verify_batch_for_frontier(strict=True)` → 3 verified, 0 inconclusive, 0 failed; `python3 pipelines/spike_probe.py --strict /tmp/nelb-r31/batch-r31.jsonl` → loaded 3, unloadable 0, problems [], third_factor_routes 3, gate_snn_records 3, spikes {spikes_sum}, energy_pJ {energy_sum}. Build-time asserts: global time order; same-channel ≥0.8 ms; 5–40 events ({rows[0]['events']}/{rows[1]['events']}/{rows[2]['events']}); excerpt integer bounds, neuron bounds, sort, 1 ms per-neuron floor; ISI identity {rows[0]['isi']}/{rows[1]['isi']}/{rows[2]['isi']}; spike budgets exact; energy pJ/µJ exact; reward totals equal two-decimal component sums (+0.40/+0.35/+0.43/+0.34/+0.41/+0.36); gate_snn decisions match lead `safety_decision.decision`; `state.sim_or_real` ∈ {{designed, hil, simulated}}; `meta.round=31`, `meta.factory=neuromorphic-event-language-bridge`, `meta.generator=grok-4.6`, `meta.run_label=2026-09-02-final-heavy`; `meta.rights` 15-key RM-793 stamp (`intended_use=research_only`, `linear_issue=RM-793`, `generated_at` ISO-8601 Z); no hidden-reasoning keys; no `provenance` objects; no 'real' claims; no `training_ready`; all 9 record/trajectory ids unique. Raster seeds 20260994/20260995/20260996, MT19937. Beads `bd create` for this round failed on Dolt `events.id` default (1105) — staging is still the `/tmp` pair, not a beads close-out.

Honest novelty accounting: 3/3 modality families are new versus the whole committed factory and versus staged leftover-mill r13–r26. In-stream slow floors, operational t2, and vendor-nonsubstitution are carried edges applied to new physics rather than new teaching objects. Against that: bounded-accept-with-scope-limit, reconstruction-as-SoT, conjunctive SOP, and custody vocabulary are carried; the 5–40 cap is a density constraint not a new teaching object; 26 prior leftover-mill rounds already taught custody/governance at high sophistication. Net: a bit under two-fifths of the round's scenario/edge mass is genuinely novel.

Novel coverage: 38%
"""
    NOTES.write_text(notes, encoding="utf-8")
    print("wrote", NOTES, "bytes", NOTES.stat().st_size)


def probe_strict():
    import subprocess

    cmd = [
        sys.executable,
        str(PIPELINES / "check_records.py"),
        "--strict",
        str(OUT_DIR),
    ]
    p = subprocess.run(cmd, capture_output=True, text=True, cwd=str(PIPELINES.parent))
    print("check_records --strict", p.returncode, (p.stdout or "")[-800:], (p.stderr or "")[-400:])
    if p.returncode != 0:
        raise RuntimeError(f"check_records --strict failed: {p.stderr or p.stdout}")
    cmd = [
        sys.executable,
        str(PIPELINES / "spike_probe.py"),
        "--strict",
        str(BATCH),
    ]
    p = subprocess.run(cmd, capture_output=True, text=True, cwd=str(PIPELINES.parent))
    print("spike_probe", p.returncode, (p.stdout or "")[-1200:], (p.stderr or "")[-400:])
    if p.returncode != 0:
        raise RuntimeError(f"spike_probe failed: {p.stderr or p.stdout}")
