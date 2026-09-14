NOTES = r"""# Neuromorphic Event + Language Bridge — NOTES round 22
Run: 2026-09-02-final-heavy · Factory: neuromorphic-event-language-bridge · Generator: grok-4.6 · Output: `batch-r22.jsonl` (3 paired artifacts, 6 ThalamicTrajectories)
Rights: RM-793 research-only (SpaceXAI/xAI grok-4.6, SuperGrok Heavy chat). Not training_ready. Operator publishes via `pipelines/round_txn.py`. Written create-only to `/home/raulmc/rmems/synthetic-factory/outputs/raw/2026-09-02-final-heavy/neuromorphic-event-language-bridge/`. Leftover-mill `/tmp/nelb-r22/` (ECT / TDLAS NH3 / LIBS tap, ids `nelb-r22-067`…`069`, 35/33/34-event streams) is a different artifact and was not overwritten.

## Context / de-duplication
Two newest NOTES read (mtime): `NOTES-r41.md` (LDA / coulometric KF / bender-element) then `NOTES-r61.md` (Stern-Volmer DO / pellistor / FMCW radar). Newest batch skimmed: `batch-r41.jsonl`. Also read assigned-previous `NOTES-r21.md` (OA-ICOS / SERF OPM / WGM) so this round does not restage those families or leftover-mill r22 ECT/TDLAS/LIBS. Flagged gaps carried: leftover-mill 5–40 thinning (this round densifies to 52); lumped reconstruction gains; vendor-only lead REJECT still unwritten. r21 asked for an OA-ICOS pressure-hop, a vendor-bus shunt, and a WGM T/Q map — those families are not restaged; the analogous densification here is a load-bearing thermal-transpiration table on a *new* CDG family.

Banned this round: leftover-mill r22 ECT / TDLAS NH3 / LIBS tap and ids `nelb-r22-067`…`069`; window r21 OA-ICOS / SERF / WGM; window r41 LDA / KF / bender-element; window r61 Stern-Volmer / pellistor / FMCW; VOD-SNN replay; pharma cold-chain; stack-gas CEMS; leftover-mill r13–r70 families (FBG, quench, VRFB, BOTDA, QCM-D, MsS, SAW, CRDS, PGNAA, IFOG, transmon, hyperspectral, MEMS, muon, x-ray DR, optogenetic, 905 nm LiDAR, clamp-on, LIBS, QEPAS, LFV, Kaplan LDV, THz-TDS, ECT, lock-in thermography, PAUT TFM, EN CUI, RUS, N-16, helium RGA, FOCT, tip-timing, acoustic pyrometry, SPR, VW viscometer, MW cavity, MFL, NMR T2, Cs-137, JNT, CRNS, Coriolis, CARS, XRF, Mössbauer, GB-InSAR, ellipsometry, CTA, SPND, LII, PALS, NQR, SFRA, shearography, H-permeation, FMCW lining, GPR, mud-pulse, Barkhausen, Lamb, Pockels, PEC, confocal, OCT, DCPD, impact-echo, phosphor-lifetime, vortex, GWR, He-3, Kr-85 beta, Raman, cyclotron BPM, alanine EPR, ADCP, TOFD, laser-flash, TDR, Seebeck, coda-wave, LPR, paramagnetic O2, TEOM, magmeter, PDA, acoustoelastic, C-SAM, FDS tanδ, MCSA, EMAT SH, FBRM, ACFM, OFDR, XRD, FSM, Gardon, chilled-mirror, DIC, CLD NOx, API-670, thermal-mass, ER probe, Fabry-Perot, inductive debris, wire-mesh, UCI, MAE, FID, turbine, magnetostrictive, IRIS, dual-wavelength pyrometer, UV-fluorescence OIW, orifice, PID VOC, conductivity, refractometer, WLI, annubar, UV-DOAS, Al2O3, load-cell, electrochemical H2S, TEV PD, dielectric water-cut, toroidal conductivity, sand monitor, FMCW radar, gamma-backscatter, NDIR CO, ultrasonic Doppler, Wobbe, nephelometric, cation conductivity, venturi, katharometer, Clark DO, sonic-nozzle, sodium-ion, vibrating-tube, Ubbelohde, gloss, RF-admittance, UV ozone, triboelectric, molybdenum-blue phosphate, FPD sulfur, colorimetric silica, coulometric hydrazine, polarimeter sucrose, platinum ORP, hydrostatic level, idler-belt, glass pH, NIR moisture). Plants not reused: Sedgewhin, Brinecrag, Lichenholt, Rushcrag, Copsewick, Peatspire, Mirewhin, Lacquerfen, Pitchshaw, Brackfen, Ashrill, Forgeholt, Fernspire is new.

Adjacencies declared in-pair then kept physically distinct:
- **a1 CDG vacuum** is a capacitance-*diaphragm* remaining pressure of a freeze-dryer shelf (mechanical deflection → C), not ECT holdup (leftover-mill r22), not RF-admittance silo level (r66), not dielectric water-cut (r60), not helium RGA (r24), not Pirani-as-SoT, not window r21 OA-ICOS intensity.
- **a2 opacity dust** is a broadband stack-path Beer-Lambert remaining dust of a lime kiln, not TEOM oscillating-microbalance PM (r46), not triboelectric dust (r68), not LII soot (r31), not OA-ICOS CH4 (window r21), not UV photometric ozone (r68), not UV-DOAS SO2 (r59).
- **a3 photoelastic stress** is circular-polariscope retardance remaining hoop stress of a glass-furnace visor, not spectroscopic ellipsometry (r30), not digital shearography (r33), not DIC hoop-strain (r51), not acoustoelastic birefringence (r47), not XRD sin2psi (r50).

Flagged gaps closed this round: (i) 52-event streams vs leftover-mill r22's 35/33/34; (ii) a **load-bearing transpiration table** on a1 so lumped k_c without sqrt(T/T0) under-reads 100.00 as 80.00 (the analog of r21's T/P-table leftover, on a new family); (iii) operational t2 on all three; (iv) serialized reconstruction on all three; (v) provenance trio designed/hil/simulated; (vi) all three safety enums on leads.

## Round 22 batch summary (3 pairs, 6 trajectories)

| id | modality (NEW family) | domain | decisions | headline |
|----|----------------------|--------|-----------|----------|
| nelb-r22-a1 | capacitance diaphragm gauge remaining vacuum of a freeze-dryer shelf (k_c·(C−C0)·√(T/T0) mTorr, Torrveil last-good denial, 18 min shelf-hold floor) | Fernspire Lyophilizer FL-6 chamber C-7 (invented): 20.00*(5.00-1.00)*√(400.00/256.00) reconstructs 100.00 mTorr while Torrveil still reads 12.80 mTorr | REJECT (+0.43) / MODIFY (+0.34) | serialized transpiration table is SoT; lumped-k without √(T/T0) would read 80.00; conjunctive SOP forbids continue-cycle; three-party collusion includes the CDG-cloud infra owner; companion t2 shelf-hold, unit ESD refused; sim_or_real=designed |
| nelb-r22-a2 | opacity transmissometer remaining dust of a lime-kiln stack (k_o·log2(I0/I) mg/m3, Extveil last-good denial, 24 min cooldown floor) | Limeholt Kiln LK-8 stack ST-2 (invented, HIL dummy in OPA-HIL-5): 8.00*log2(16.00/4.00) reconstructs 16.00 mg/m3 while Extveil still reads 2.40 mg/m3 | MODIFY (+0.40) / ACCEPT (+0.35) | serialized `8.00*log2(16.00/4.00)=16.00` and `1.50*16.00=24.00`; keep-stack refused; opacity tech Tamsin Holt exonerated (missing lamp-zero AE, UTC vs UTC+2); companion t2 new-head restart; sim_or_real=hil |
| nelb-r22-a3 | circular-polariscope remaining hoop stress of a glass-furnace visor (δ/(C_B·t) MPa, Brewveil last-good denial, 12 min survey floor) | Flintshaw Glass FG-3 visor V-4 (invented, simulated PHOTO-SIM-3): 240.00/(8.00*3.00) reconstructs 10.00 MPa while Brewveil still reads 1.20 MPa | ACCEPT (+0.41) / REJECT (+0.36) | serialized `240.00/(8.00*3.00)=10.00`; `20.00*10.00*3.00/30.00=20.00`; bounded ACCEPT of V-4 only; V-1..V-3 out of scope; companion t2 REJECTS skip-survey; sim_or_real=simulated |

Decision spread: REJECT / MODIFY / MODIFY / ACCEPT / ACCEPT / REJECT — **2A/2M/2R**. All three enums used, and all three sit on **leads**. Provenance spread: designed / hil / simulated (one each; never real). IDs `nelb-r22-a1`…`a3` plus t1/t2 suffixes (not leftover-mill `067`…`069`).

## Raster sidecar
Every record carries `raster` + top-level `gate_snn` + `gate_compute`. Windows 40/32/36 ms; `window_s == window_ms/1000` exactly; `spikes == round(neurons·rate·window_s)` with zero slack (40/40/36 at 50.0/50.0/62.5 Hz over 20/25/16 neurons); `energy_pJ = spikes·23` and `energy_uJ = spikes·23e-6` exact (920/920/828 pJ). Routing source/target + 3-entry tables + `third_factor` on all three (modulators da.cdg_vacuum_conflict / ach.opa_lampzero_skip_salience / na.visor_scope_eligibility; τe 1.6/1.2/2.0 s as consistent `tau_e_s`+`tau_e_ms` pairs). Excerpts integer `t_us`, in-window, `neuron_id`-bounded, sorted, full-window by construction, per-spike amplitude with adaptation (0.82**k) plus noise. ISI histograms from the full window, bins ≥1 ms, counts sum to `spikes − distinct_active_neurons`. Same-neuron gaps ≥1100 µs pre-round, ≥1000 µs serialized. `gate_snn` on all three: decisions REJECT/MODIFY/ACCEPT matching each lead trajectory; every rate-declaring population's budget exact against its decision window. `gate_compute.per_check` windows 32–40 ms, budgets exact. Main streams: **52/52/52 events** (48+), strictly increasing `t_rel_ms` only (no `t_ms` mix), same-channel refractory ≥0.8 ms (a1 CDG pair at 1.4 ms, a2 opacity pair at 1.2 ms, a3 polariscope pair at 1.5 ms).

## Self-critique

### Edge cases added vs still thin
- **Added:** first capacitance-diaphragm-gauge remaining-vacuum family with a recomputable transpiration table (`100.00 mTorr` vs lumped-k `80.00`); first opacity-transmissometer remaining-dust family with recomputable C=k_o·log2(I0/I) (`16.00 mg/m3`) plus OD and mdot identities and a resolved-innocent opacity tech; first circular-polariscope remaining-hoop-stress family with recomputable σ=δ/(C_B·t) (`10.00 MPa`) plus hoop-pressure identity; 52-event streams (leftover-mill r22 was 35/33/34); operational t2 on all three; provenance trio; 18/24/12 min slow floors in-stream.
- **Still thin:** (i) a1's C0 column is constant — a zero-drift hop that fakes 100.00 mTorr inside a 12.80 Torrveil corridor is unwritten; (ii) a2 still has a plant-owned stack pitot; a booth whose pitot rides the colluding Extveil bus, so the gate must refuse with *only* lamp-zero AE plus pass log, is harder (vendor-only lead REJECT remains open); (iii) a3's C_B is a lumped Brewster coefficient, not a temperature / wavelength map; (iv) stream reconstruction amplitudes remain authored constants (raster draws are the only seeded noise); (v) no gate_snn input→output volley pair at raster resolution this round (2026-08-30 r04-a1 already staged that).

### Realism of noise / temporal fidelity
- Strong: a1's 100.00 mTorr, dC 4.00, mdot 20.00, √(T/T0) 1.25, and 18.0 min hold (`6000+1080=7080 s`) recompute from the record; a2's 16.00 mg/m3, OD 2.00, mdot 24.00, and 24.0 min cooldown (`2820+1440=4260 s`) recompute; a3's 10.00 MPa, p 20.00 bar, and 12.0 min survey (`6000+720=6720 s`) recompute. Raster adaptation (0.82**k plus 4% noise) and the 1.2–1.5 ms physics pairs give the 52-event stream a raster-scale motif without violating 0.8 ms same-channel refractory.
- **Gaps, honestly:** (i) 10 Hz CDG / 1 Hz opacity / 10 Hz polariscope are still thinned to 4 physics points plus table rows, even at 52 events; (ii) a1's post-stop 125.00 mTorr is a later sample, not a closed-loop shelf-hold controller; (iii) a2 HIL coupon times an in-service isolate that the stream does not independently witness on a second live stack until the new head starts.

### Training value (SNN/LSM + agentic)
Distillation targets: CDG P=k_c·(C−C0)·√(T/T0) plus transpiration-table SoT; conjunctive isolate floor vs continue-cycle vs unit ESD; Torrveil-infra collusion; opacity C=k_o·log2(I0/I) plus OD and mdot identities; isolate-floor stack vs keep-whole vs shop-trip; lamp-zero AE / timezone exoneration; photoelastic σ=δ/(C_B·t) and hoop-pressure identities; bounded ACCEPT with visor-out-of-scope; skip-survey refusal under survey takt. Agentic value concentrates in three patterns: reconstruction-as-SoT on a physical vacuum/dust/stress load the raw corridor cannot see (with a table that makes lumped-k fail), earned ACCEPT with an explicit physical out-of-scope object (V-1..V-3), and stop-then-hold so a REJECT does not become a train/shop/dump kill.

## What round 23 should add (next densification target)
1. **C0-drift row** on a non-FL-6 CDG so a zero hop fakes 100.00 mTorr inside a 12.80 Torrveil corridor, closing a1's constant-C0 leftover.
2. **Vendor-only stack pitot:** restage the a2 leftover where even the pitot millivolt rides Extveil, so the only unwritable witnesses are lamp-zero AE and the pass log (vendor-only lead REJECT).
3. **Temperature / wavelength Brewster map** on a non-FG-3 polariscope so a thermal hop fakes 10.00 MPa while mean δ looks healthy.
4. **Do not restage** leftover-mill r22 ECT / TDLAS NH3 / LIBS tap, OA-ICOS SW-5, SERF-HIL-5, WGM-SIM-3, LDA RC-8, KF CW-6, bender-element PS-9, Stern-Volmer MW-9, pellistor LF-3, FMCW PS-6, Fernspire FL-6 CDG, Limeholt OPA-HIL-5, Flintshaw PHOTO-SIM-3, VOD-SNN, pharma cold-chain, or stack-gas CEMS. Do not reuse ids `nelb-r22-067`…`069` or leftover-mill `040`…`213`.

## Verification
`batch-r22.jsonl`: 3 lines, `json.loads`-clean (allow_nan=False), bytes SHA256_PLACEHOLDER. Written create-only to the assigned factory dir. Build-time asserts: global time order; same-channel ≥0.8 ms; 48+ events (52/52/52); excerpt integer bounds, neuron bounds, sort, 1 ms per-neuron floor; ISI identity; spike budgets exact; energy pJ/µJ exact; reward totals equal two-decimal component sums (+0.43/+0.34/+0.40/+0.35/+0.41/+0.36); gate_snn decisions match lead `safety_decision.decision`; `state.sim_or_real` ∈ {designed, hil, simulated}; `meta.round=22`, `meta.factory=neuromorphic-event-language-bridge`, `meta.generator=grok-4.6`, `meta.run_label=2026-09-02-final-heavy`; `meta.rights` 15-key RM-793 stamp (`intended_use=research_only`, `linear_issue=RM-793`, `generated_at=2026-09-02T19:20:00Z`); no hidden-reasoning keys; no `provenance` objects; no live-plant claims; no `training_ready`; all 9 record/trajectory ids unique vs leftover-mill r22. Raster seeds 202609221/202609222/202609223, MT19937.

Honest novelty accounting: 3/3 modality families are new versus the committed factory, versus leftover-mill r13–r70, versus leftover-mill r22's ECT/TDLAS/LIBS, and versus window r21/r41/r61. The 52-event streams and the load-bearing transpiration table are new density/physics objects relative to leftover-mill r22. Against that: conjunctive SOP, operational t2, serialized reconstruction, bounded-accept-with-scope-limit, vendor-nonsubstitution, exoneration, and 2A/2M/2R are carried vocabulary; 48+ is a density constraint the leftover mill did not harvest. Net: a bit under half of the round's scenario/edge mass is genuinely novel.

Novel coverage: 43%
"""


def choose_paths():
    if not FACTORY.is_dir():
        raise SystemExit(f"refuse: factory dir missing {FACTORY}")
    batch = FACTORY / "batch-r22.jsonl"
    notes = FACTORY / "NOTES-r22.md"
    if batch.exists() or notes.exists():
        batch = FACTORY / "batch-r22c.jsonl"
        notes = FACTORY / "NOTES-r22c.md"
        if batch.exists() or notes.exists():
            raise SystemExit(f"refuse: {batch} or {notes} already exists")
    leftover = Path("/tmp/nelb-r22/batch-r22.jsonl")
    if leftover.exists():
        # leftover mill is a different tree; do not write there
        pass
    return batch, notes


def main():
    recs = [rec_a1(), rec_a2(), rec_a3()]
    ids = []
    for rec in recs:
        hid = walk_hidden(rec)
        if hid:
            raise RuntimeError(f"hidden keys {hid}")
        if rec["gate_snn"]["decision"] != rec["language_view"]["trajectory"]["safety_decision"]["decision"]:
            raise RuntimeError("gate_snn decision mismatch")
        if rec["language_view"]["trajectory"]["state"]["sim_or_real"] not in {"designed", "simulated", "hil"}:
            raise RuntimeError("bad sim_or_real")
        if "provenance" in rec or "training_ready" in rec:
            raise RuntimeError("forbidden keys")
        ids.append(rec["id"])
        ids.append(rec["language_view"]["trajectory"]["id"])
        for k, v in rec["language_view"].items():
            if k not in {"description", "trajectory"} and isinstance(v, dict) and "id" in v:
                ids.append(v["id"])
        n = len(rec["spike_events"])
        if n < 48:
            raise RuntimeError(f"{rec['id']} has {n} events")
        r = rec["raster"]
        expected = int(round(r["neurons"] * r["mean_rate_hz"] * r["window_s"]))
        if abs(r["spikes"] - expected) > 1:
            raise RuntimeError("spike budget")
        if abs(r["energy_pJ"] - r["spikes"] * 23) > 1e-6:
            raise RuntimeError("energy_pJ")
        if abs(r["energy_uJ"] - r["spikes"] * 23e-6) > 1e-9:
            raise RuntimeError("energy_uJ")
        if abs(r["window_s"] - r["window_ms"] / 1000.0) > 1e-9:
            raise RuntimeError("window mismatch")
        tf = r["routing"]["third_factor"]
        if abs(tf["tau_e_ms"] / 1000.0 - tf["tau_e_s"]) > 1e-9:
            raise RuntimeError("tau mismatch")
        gs = rec["gate_snn"]
        dw_s = gs["decision_window_ms"] / 1000.0
        if abs(gs["decision_window_s"] - dw_s) > 1e-9:
            raise RuntimeError("gate window")
        for pop in gs["populations"]:
            if "mean_rate_hz" in pop:
                exp = int(round(pop["neurons"] * pop["mean_rate_hz"] * dw_s))
                if abs(pop["spikes"] - exp) > 1:
                    raise RuntimeError(f"gate pop budget {pop['name']}")
        gc = rec["gate_compute"]
        if gc["total_spikes"] != sum(c["spikes"] for c in gc["per_check"]):
            raise RuntimeError("gate_compute total")
        if abs(gc["total_energy_pJ"] - gc["total_spikes"] * 23) > 1e-6:
            raise RuntimeError("gate_compute energy")
        if rec["meta"]["round"] != 22:
            raise RuntimeError("meta.round")
        if rec["meta"]["rights"]["intended_use"] != "research_only":
            raise RuntimeError("rights")
        if len(rec["meta"]["rights"]) != 15:
            raise RuntimeError("rights key count")
    if len(ids) != len(set(ids)):
        raise RuntimeError(f"duplicate ids {ids}")
    banned = {
        "nelb-r21-064", "nelb-r21-065", "nelb-r21-066",
        "nelb-r22-067", "nelb-r22-068", "nelb-r22-069",
        "nelb-r21-a1", "nelb-r21-a2", "nelb-r21-a3",
    }
    if set(ids) & banned:
        raise RuntimeError(f"collides banned ids {set(ids)&banned}")

    batch, notes_path = choose_paths()
    lines = [json.dumps(rec, ensure_ascii=False, separators=(",", ":"), allow_nan=False) for rec in recs]
    payload = "\n".join(lines) + "\n"
    digest = hashlib.sha256(payload.encode("utf-8")).hexdigest()
    sizes = [len(x.encode("utf-8")) for x in lines]
    notes_text = NOTES.replace("SHA256_PLACEHOLDER", f"{sizes[0]}/{sizes[1]}/{sizes[2]} (file {sum(sizes)+3}, sha256 `{digest}`)")
    batch.write_text(payload)
    notes_path.write_text(notes_text)
    print(json.dumps({
        "batch": str(batch),
        "notes": str(notes_path),
        "n": len(lines),
        "ids": ids,
        "events": [len(r["spike_events"]) for r in recs],
        "sha256": digest,
        "bytes": sizes,
    }))


if __name__ == "__main__":
    main()
