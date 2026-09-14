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
    notes = f"""# Neuromorphic Event + Language Bridge — NOTES round 51
Run: 2026-09-02-final-heavy · Factory: neuromorphic-event-language-bridge · Generator: grok-4.6 · Output: `batch-r51.jsonl` (3 paired artifacts, 6 ThalamicTrajectories)
Rights: RM-793 research-only (SpaceXAI/xAI grok-4.6, SuperGrok Heavy chat). Not training_ready. Do not publish into `outputs/raw/` from this generator; operator uses `pipelines/round_txn.py`. Staged only at `/tmp/nelb-r51/`.

## Context / de-duplication
Prior corpus read: 2026-08-30 NOTES-r01–r04, 2026-08-17-w3 NOTES-r12 family table, `/tmp/nelb-r13-holes.md` + `/tmp/nelb-r13-premises.md`, staged `/tmp/nelb-r13` through `/tmp/nelb-r46` batches/NOTES plus in-flight `/tmp/nelb-r45` (RFEC / ACFM / LPR), `/tmp/nelb-r47` (RFT / PDA / acoustoelastic plus Faraday magmeter slurry fragment), `/tmp/nelb-r48` (C-SAM / FDS tanδ / MCSA plus ACFM jack-up fragment), `/tmp/nelb-r49` (EMAT SH / FBRM D50 / ACFM chord), `/tmp/nelb-r50` (r44-clone envelope only). IDs: r13=`040`–`042` … r46=`139`–`141`, reserved r47–r50=`142`–`153`, this round `nelb-r51-154`…`156` as assigned. Envelope cloned from complete r46 (`language_view.trajectory` + operational t2 + `spike_events` + `raster` + `gate_snn` + `isi_histogram` + `routing.third_factor` + 15-key RM-793 `meta.rights`).

Banned this round (committed + staged leftover-mill r13–r46 and in-flight r45/r47/r48/r49/r50 generators): not VOD-SNN replay, not pharma cold-chain, not stack-gas CEMS; not r13 FBG glaze / Frostlip quench / Oxbow VRFB; not r14 BOTDA / QCM-D / MsS T(0,1); not r15 SAW torque / CRDS HF / PGNAA; not r16 IFOG / transmon readout / hyperspectral crop; not r17 MEMS accel array / muon ore-pass / industrial x-ray DR; not r18 optogenetic PV / 905 nm LiDAR snow / clamp-on transit-time; not r19 LIBS Cu / QEPAS DGA / LFV Al; not r20 Kaplan LDV / THz-TDS radome moisture / ECT CFB; not r21 THz-TDS bondline / ECA FSW lift-off / LIBS C; not r22 ECT pneumatic riser / TDLAS NH3 / LIBS tap; not r23 lock-in thermography CFRP / PAUT TFM girth / EN CUI; not r24 RUS porcelain / N-16 transit-time loop / helium RGA; not r25 Faraday FOCT / blade tip-timing / acoustic pyrometry; not r26 SPR cyanide / VW viscometer / MW cavity moisture; not r27 MFL AST / NMR T2 / Cs-137 densitometry; not r28 MFL ILI / JNT / CRNS; not r29 Coriolis bitumen / CARS TIT / Zn-Ka XRF; not r30 Mössbauer FCC / GB-InSAR tailings / ellipsometry PECVD; not r31 CTA hot-wire / rhodium SPND / LII soot; not r32 PALS / 14N NQR / SFRA; not r33 digital shearography hull / hydrogen permeation / FMCW BOF lining; not r34 handheld XRF Cr-Kα / Coriolis tube-twist / GPR liner cover; not r35/r37 mud-pulse MWD / Barkhausen / Lamb-wave; not r36 Pockels GIS / PEC coated riser / confocal chromatic; not r38 OCT TBC / DCPD girth / impact-echo containment; not r39 alanine EPR / vortex-shedding / impact-echo PT grout / phosphor-lifetime / GWR foam; not r40 impact-echo pier / Kr-85 beta / 532 nm Raman; not r41/r42/r43 cyclotron BPM / alanine EPR / ADCP ice-jam; not r44 TOFD ligament / laser-flash Parker / TDR XLPE; not r45 RFEC boiler / ACFM jacket / LPR header; not r46 paramagnetic O2 / TOFD hydrocracker / TEOM PM; not r47 RFT / PDA / acoustoelastic / Faraday magmeter slurry; not r48 C-SAM / FDS tanδ / MCSA; not r49 EMAT SH / FBRM D50 / ACFM chord. Plants not reused: Nettlewake, Frostlip, Oxbow, Rift-Caldera-3, Skarv-Naze GN-14, Orinoco-Span OD-12, Kilncrag KC-8, Rookspit RS-4, Spindrift SD-12, Gorsekettle GK-5, Flintspit FG-8, Wharfleck WD-11, Thistlemere TM-6, Murkspit MS-6, Culmholt CH-5, Cobblemere CM-5, Vellumkettle VK-4, Lanternfell LF-6, Greyfen KCTC-7, Pellucid IRRAD-P4, Whitefork WF-9, Sloebrake STC-4, Brinewharf IRRAD-B6, Fernspit FR-6, Slatefen ST-3, Brinecairn BC-6, Mossferry MF-4, Groutfen GF-3, Peatholt PH-7, Drizzlewick DW-5, Cloughmere CM-6, Gritfen GV-9, Felltide FT-6, Mashholt MH-8, Wickspire WS-8, Bitternex BX-5, Clinkerfell CK-3, Cinderholt CH-7, Ashfen AH-4, Siltfen SF-9, Charkholt CH-6, Kelpcrag KJ-5, Wickmere WM-8, Dapplemere DM-8, Puddlewick PD-6, Fennelholt FH-5, Ashholt AH-7, Gorsewisp GW-5, Flintcrag FC-4, Kettermere KM-6, Mirebank MB-5, Terncrag TC-4, Miregait MG-9.

This round introduces three unused industrial families (Gardon-gauge incident heat flux, chilled-mirror dew-point, digital-image-correlation hoop-strain) on new invented plants. Magmeter slurry was already claimed in-flight by r47 and is not restaged. ACFM was claimed by r45/r48/r49 and is not restaged.

Adjacencies declared in-pair then kept physically distinct:
- **154 Gardon heat flux** is a foil calorimeter emf of a steam-reformer arch, not r25 acoustic pyrometry, not r39 phosphor-lifetime, not r31 LII soot, not r29 CARS TIT, not r33 FMCW lining, not r23 lock-in thermography.
- **155 chilled-mirror dew-point** is a condensate-onset hygrometer of a TEG contactor, not r26 MW-cavity moisture, not r28 CRNS, not r14 QCM-D, not r44 TDR cable, not r39 GWR foam, not r40 Raman OH-CH.
- **156 DIC hoop-strain** is in-plane subset displacement of a coke-drum skirt, not r33 digital shearography hull (out-of-plane slope), not r30 GB-InSAR, not r13 FBG glaze, not r35/r37 Lamb-wave LUT.

## Round 51 batch summary (3 pairs, 6 trajectories)

| id | modality (NEW family) | domain | decisions | headline |
|----|----------------------|--------|-----------|----------|
| nelb-r51-154 | Gardon-gauge incident heat flux of a reformer arch (k_g·E kW/m2, Heatveil foil denial, 18 min spray floor) | Brackholt Reformer BH-8 arch A-2 (invented): 12.50 mV reconstructs 50.00 kW/m2 while Heatveil still reads 6.40 kW/m2 | REJECT (+0.43) / MODIFY (+0.34) | serialized `4.00*12.50=50.00`; `0.80*12.50=10.00`; conjunctive SOP (q AND SNR) forbids keep-firing; three-party collusion includes the Heatveil infra owner; companion t2 water-spray hold, reformer ESD refused; sim_or_real=designed |
| nelb-r51-155 | chilled-mirror dew-point of a TEG dryer (k_p·2**(T/10) kPa, k_x·p_w/P ppmv, Dewveil last-good denial, 24 min reclean floor) | Dewholt TEG DH-5 contactor C-1 (invented, HIL dummy in DP-HIL-5): 20.00 C reconstructs 80.00 ppmv while Dewveil still reads 8.40 ppmv | MODIFY (+0.40) / ACCEPT (+0.35) | serialized `0.500*2**(20/10)=2.00`; `40.00*2.00=80.00`; keep-dryer refused; tech Maren Quill exonerated (missing frost AE, UTC vs UTC+2); companion t2 new-mirror restart; sim_or_real=hil |
| nelb-r51-156 | DIC hoop-strain of a coke-drum skirt (k_u·n ue, k_s·eps MPa, Correlveil last-good denial, 12 min survey floor) | Pebblewick Coke PW-3 drum D-2 (invented, simulated DIC-SIM-2): 4.00 px reconstructs 200.00 ue / 40.00 MPa while Correlveil still reads 40.00 ue | ACCEPT (+0.41) / REJECT (+0.36) | serialized `50.00*4.00=200.00`; `0.200*200.00=40.00`; `1000*4.00/20.00=200.00`; bounded ACCEPT of D-2 only; D-1/D-3 out of scope; companion t2 REJECTS skip-overlay; sim_or_real=simulated |

Decision spread: REJECT / MODIFY / MODIFY / ACCEPT / ACCEPT / REJECT — **2A/2M/2R**. All three enums used, and all three sit on **leads**. Provenance spread: designed / hil / simulated (one each; never live-plant). IDs `nelb-r51-154`…`156` plus t1/t2 suffixes.

## Raster sidecar
Every record carries `raster` + top-level `gate_snn` + `gate_compute`. Windows {wins[0]:.0f}/{wins[1]:.0f}/{wins[2]:.0f} ms; `window_s == window_ms/1000` exactly; `spikes == round(neurons·rate·window_s)` with zero slack ({n_sp[0]}/{n_sp[1]}/{n_sp[2]} at {rates[0]}/{rates[1]}/{rates[2]} Hz over {n_neu[0]}/{n_neu[1]}/{n_neu[2]} neurons); `energy_pJ = spikes·23` and `energy_uJ = spikes·23e-6` exact ({n_sp[0]*23}/{n_sp[1]*23}/{n_sp[2]*23} pJ). Routing source/target + 3-entry tables + `third_factor` on all three (modulators {tfs[0]} / {tfs[1]} / {tfs[2]}; τe {taus[0]}/{taus[1]}/{taus[2]} s as consistent `tau_e_s`+`tau_e_ms` pairs). Excerpts integer `t_us`, in-window, `neuron_id`-bounded, sorted, full-window by construction, per-spike amplitude with adaptation (0.82**k) plus noise. ISI histograms from the full window, bins ≥1 ms, counts sum to `spikes − distinct_active_neurons` ({isis[0]}/{isis[1]}/{isis[2]}). Same-neuron gaps ≥1100 µs pre-round, ≥1000 µs serialized. `gate_snn` on all three: decisions REJECT/MODIFY/ACCEPT matching each lead trajectory; every rate-declaring population's budget exact against its decision window. `gate_compute.per_check` windows 32–40 ms, budgets exact ({gc[0]} / {gc[1]} / {gc[2]}). Main streams: {events[0]}/{events[1]}/{events[2]} events (inside the 5–40 cap), strictly increasing `t_rel_ms` only (no `t_ms` mix), same-channel refractory ≥0.8 ms (154 Gardon pair at 1.3 ms, 155 mirror pair at 1.2 ms, 156 DIC pair at 1.5 ms).

## Self-critique

### Edge cases added vs still thin
- **Added:** first Gardon-gauge incident-heat-flux family on a steam-reformer arch with a recomputable q=k_g·E (`50.00 kW/m2`) plus foil dT identity and three-party collusion including the Heatveil infra owner; first chilled-mirror dew-point family on a TEG contactor with recomputable p_w=k_p·2**(T/10) and x=k_x·p_w/P (`80.00 ppmv`) plus a resolved-innocent tech (timezone-skipped frost AE, not last-to-badge); first DIC hoop-strain family on a coke-drum skirt with recomputable eps=k_u·n (`200.00 ue`) and σ=k_s·eps (`40.00 MPa`) plus gauge/E identities; first bounded ACCEPT whose out-of-scope clause is adjacent coke drums rather than a hopper/taphole/dump cap; operational t2 on all three (water-spray hold, new-mirror restart, skip-overlay refusal); provenance trio designed/hil/simulated; 18 min / 24 min / 12 min slow floors in-stream.
- **Still thin:** (i) 154's k_g is a lumped mV→kW/m2 gain, not an emissivity / view-factor table — a soot-coated foil that fakes 50.00 kW/m2 inside a 6.40 Heatveil corridor is unwritten; (ii) 155's k_p is a lumped doubling-every-10 C vapor-pressure gain, not a Magnus/ITS-90 table, so a contamination hop that fakes 80.00 ppmv is unwritten; (iii) 156's k_u is a lumped px→ue gain, not a subset-size / interpolation map, so a rigid-body hop that fakes 200.00 ue inside a 40 ue last-good is unwritten; (iv) vendor-only as a *lead* REJECT on a plant with *no* independent Gardon/mirror/DIC installed yet remains slightly harder — 154/155 still have plant heads; (v) stream amplitudes remain authored constants (raster draws are the only seeded noise); (vi) r38 densification leftovers (OCT group-index table, DCPD current-spread map, moisture-corrected impact-echo) were left for that round's owner.

### Realism of noise / temporal fidelity
- Strong: 154's 50.00 kW/m2, dT 10.00 K, and 18.0 min spray (`6000+1080=7080 s`) recompute from the record; 155's 80.00 ppmv, p_w 2.00 kPa, and 24.0 min reclean (`2820+1440=4260 s`) recompute; 156's 200.00 ue, 40.00 MPa, and 12.0 min survey (`6000+720=6720 s`) recompute. Raster adaptation (0.82**k plus 4% noise) and the 1.2–1.5 ms physics pairs give the 5–40 stream a raster-scale motif without violating 0.8 ms same-channel refractory.
- **Gaps, honestly:** (i) 5–40 cap still forces heavy thinning (10 Hz Gardon kept as 4 E points; 1 Hz chilled-mirror servo kept as 4 T_dp points; 10 Hz DIC subset kept as 4 n points); (ii) 154's post-stop 32.00 kW/m2 is a later sample, not a closed-loop spray controller; (iii) 155 HIL coupon times an in-service dryer isolate that the stream does not independently witness on a second live contactor until the new mirror starts; (iv) no gate_snn input→output volley pair at raster resolution this round (r04-a1 already staged that).

### Training value (SNN/LSM + agentic)
Distillation targets: Gardon q=k_g·E reconstruction head plus dT identity; conjunctive isolate floor vs keep-firing vs reformer ESD; Heatveil-infra collusion; chilled-mirror p_w=k_p·2**(T/10) and x=k_x·p_w/P heads; isolate-floor dryer vs keep-whole vs glycol-dump; exoneration against last-to-badge social pressure; DIC eps=k_u·n and σ=k_s·eps identities; bounded ACCEPT with drum-out-of-scope; skip-overlay refusal under survey takt. Agentic value concentrates in three patterns: reconstruction-as-SoT on a physical flux/moisture/hoop load the raw corridor cannot see, earned ACCEPT with an explicit physical out-of-scope object (D-1/D-3), and stop-then-hold so a REJECT does not become a reformer/glycol/pair kill.

## What round 52 should add (next densification target)
1. **Emissivity / view-factor table** on a non-BH-8 arch so a soot-coated foil fakes 50.00 kW/m2 inside a 6.40 Heatveil corridor, closing 154's lumped-k_g gap.
2. **Magnus / ITS-90 vapor-pressure table** on a non-DH-5 contactor so a contamination hop can fake 80.00 ppmv while mean dew-point looks healthy.
3. **Subset-size / interpolation map** on a non-PW-3 skirt so a rigid-body hop can fake 200.00 ue inside a 40 ue last-good corridor.
4. **Vendor-only as a lead REJECT** on a plant that has no independent Gardon/mirror/DIC installed yet (154/155 still had plant heads).
5. **Do not restage** VOD-SNN replay, pharma cold-chain, CEMS, FBG glaze, Frostlip quench, Oxbow VRFB, IFOG, transmon, hyperspectral, MEMS array, muon ore-pass, industrial x-ray, optogenetic stim, 905 nm LiDAR snow, clamp-on transit-time, LIBS, QEPAS, LFV, Kaplan LDV, THz-TDS, ECT, TDLAS NH3, lock-in thermography, PAUT TFM, EN CUI, RUS porcelain, N-16 loop flow, helium RGA, Faraday FOCT, blade tip-timing, acoustic pyrometry, SPR, vibrating-wire, microwave-cavity, MFL, NMR T2, nucleonic densitometry, JNT, CRNS, Coriolis, CARS, XRF, Mössbauer, GB-InSAR, ellipsometry, CTA, SPND, LII, PALS, NQR, SFRA, digital shearography, hydrogen permeation, FMCW lining, GPR, Pockels, PEC, confocal, mud-pulse, Barkhausen, Lamb-wave, OCT, DCPD, impact-echo, cyclotron BPM, alanine EPR, ADCP, vortex-shedding, Kr-85 beta, 532 nm Raman, phosphor-lifetime, guided-wave-radar, paramagnetic O2, TOFD, TEOM, TDR, laser-flash Parker, RFEC, ACFM, LPR, RFT, PDA, acoustoelastic, Faraday magmeter, C-SAM, FDS tanδ, MCSA, EMAT SH, FBRM, Brackholt BH-8 Gardon, Dewholt DP-HIL-5, or Pebblewick DIC-SIM-2. Leave r38 densification leftovers (OCT group-index, DCPD current-spread, moisture-corrected impact-echo) for that round's owner. Do not steal r38–r50 IDs `115`–`153`.

## Verification
`batch-r51.jsonl`: 3 lines, `json.loads`-clean (allow_nan=False), {sizes[0]}/{sizes[1]}/{sizes[2]} bytes (file {BATCH.stat().st_size}, sha256 `{file_sha}`). Staged at `/tmp/nelb-r51/` only. Repo gates: `check_records.check_jsonl` with `FactoryStaging(enabled=True)` → 0 errors, 0 warnings, kinds `{{bridge_pair: 3}}`; `python3 pipelines/check_records.py --strict /tmp/nelb-r51` → 0/0; `curate_bridge.raster_status(..., require_raster=True, require_routing_table=True)` → raster_valid and gate_snn_valid true, empty reason codes; `curate_record(...)` → 3× retain / `BRIDGE_EVENTS_ALREADY_GLOBALLY_ORDERED`; `verify_batch_for_frontier(strict=True)` → 3 verified, 0 inconclusive, 0 failed; `python3 pipelines/spike_probe.py --strict /tmp/nelb-r51/batch-r51.jsonl` → loaded 3, unloadable 0, problems [], third_factor_routes 3, gate_snn_records 3, spikes {spikes}, energy_pJ {energy}. Build-time asserts: global time order; same-channel ≥0.8 ms; 5–40 events ({events[0]}/{events[1]}/{events[2]}); excerpt integer bounds, neuron bounds, sort, 1 ms per-neuron floor; ISI identity {isis[0]}/{isis[1]}/{isis[2]}; spike budgets exact; energy pJ/µJ exact; reward totals equal two-decimal component sums ({reward_s}); gate_snn decisions match lead `safety_decision.decision`; `state.sim_or_real` ∈ {{designed, hil, simulated}}; `meta.round=51`, `meta.factory=neuromorphic-event-language-bridge`, `meta.generator=grok-4.6`, `meta.run_label=2026-09-02-final-heavy`; `meta.rights` 15-key RM-793 stamp (`intended_use=research_only`, `linear_issue=RM-793`, `generated_at={GENERATED_AT}`); no hidden-reasoning keys; no `provenance` objects; no live-plant claims; no `training_ready`; all 9 record/trajectory ids unique. Raster seeds 202609154/202609155/202609156, MT19937. Beads `bd create` for this round failed on Dolt `events.id` default (1105) — staging is still the `/tmp` pair, not a beads close-out.

Honest novelty accounting: 3/3 modality families are new versus the whole committed factory and versus staged leftover-mill r13–r46 (and in-flight r45/r47/r48/r49 claims). In-stream slow floors, operational t2, and vendor-nonsubstitution are carried edges applied to new physics rather than new teaching objects. Three-party collusion and exoneration were already taught on r13 quench/VRFB and r37/r42 Barkhausen/alanine, so those heads are carried onto new sensors. Against that: bounded-accept-with-scope-limit, reconstruction-as-SoT, conjunctive SOP, and custody vocabulary are carried; the 5–40 cap is a density constraint not a new teaching object; 38 prior leftover-mill rounds already taught custody/governance at high sophistication. Net: about two-fifths of the round's scenario/edge mass is genuinely novel.

Novel coverage: 40%
"""
    NOTES.write_text(notes, encoding="utf-8")
    print("wrote", NOTES, "bytes", NOTES.stat().st_size)


def main():
    occupancy_preflight()
    records = [rec_154(), rec_155(), rec_156()]
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
