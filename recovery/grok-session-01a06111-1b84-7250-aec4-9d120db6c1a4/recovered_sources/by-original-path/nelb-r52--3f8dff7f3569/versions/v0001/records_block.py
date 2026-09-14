def occupancy_preflight():
    banned = (
        "chemiluminescence",
        "cld nox",
        "api 670",
        "eddy-current proximity",
        "eddy current proximity",
        "proximitor",
        "thermal-mass capillary",
        "thermal mass capillary",
        "bypass thermal mass",
        "fernwick",
        "mossfell",
        "kelpfen",
        "cldveil",
        "gapveil",
        "massveil",
        "ivor clegg",
        "soren quill",
        "edda marsh",
        "nessa croft",
    )
    hits = []
    root = Path("/tmp")
    for n in (
        sorted(root.glob("nelb-r*/NOTES-r*.md"))
        + sorted(root.glob("nelb-r*/gen_r*.py"))
        + sorted(root.glob("nelb-r*/records_block.py"))
        + sorted(root.glob("nelb-r*/*recs*.py"))
    ):
        if "nelb-r52" in str(n):
            continue
        text = n.read_text(encoding="utf-8", errors="replace").casefold()
        for b in banned:
            if b in text:
                hits.append(f"{n}:{b}")
    if hits:
        raise RuntimeError(f"family/plant collision {hits}")


# ---------------------------------------------------------------------------
# Record 157 — chemiluminescence NOx of an SCR outlet, designed,
# REJECT / MODIFY
# ---------------------------------------------------------------------------
def rec_157():
    k_cl = 0.500
    i_na = 24.00
    i_bg = 4.00
    t_k = 320.0
    t0_k = 320.0
    p_bar = 1.000
    p0_bar = 1.000
    t_ratio = t_k / t0_k
    p_ratio = p0_bar / p_bar
    di = i_na - i_bg
    c_ppm = k_cl * di * t_ratio * p_ratio
    _exact(t_ratio, 1.000)
    _exact(p_ratio, 1.000)
    _exact(di, 20.00)
    _exact(c_ppm, 10.00)
    _exact(k_cl * (14.00 - i_bg) * t_ratio * p_ratio, 5.00)
    _exact(k_cl * (18.00 - i_bg) * t_ratio * p_ratio, 7.00)
    _exact(k_cl * (16.00 - i_bg) * t_ratio * p_ratio, 6.00)
    q_oz = 1.00
    c_oz = k_cl * di / q_oz
    _exact(c_oz, 10.00)
    _exact(0.500 * 20.00 / 1.00, 10.00)
    _exact(6000.0 + 1080.0, 7080.0)

    raster = make_raster(
        neurons=20,
        mean_rate_hz=50.0,
        window_ms=40.0,
        seed=202609157,
        source="fw9.cld.pmt",
        target="fernwick.scr_stop_core",
        table=[
            {"from": "cld_I", "to": "nox_estimator", "weight": 1.40},
            {"from": "cld_snr", "to": "cld_lock_core", "weight": 1.15},
            {"from": "cldveil_c", "to": "vendor_continue_advocate", "weight": 0.45},
        ],
        third_factor={
            "modulator": "da.cross_authority_conflict",
            "tau_e_s": 1.6,
            "tau_e_ms": 1600.0,
            "eligibility": "pre-post coincidence on continue-firing synapses; the plant CLD modulator depresses continue-firing links when PMT current stays high inside tau_e of an SNR lock so a Cldveil last-good patch cannot hide a 10.00 ppm NOx slip",
        },
        channel_prefix="cld.n",
        anchor="FW-9 chemiluminescence PMT 40 ms frame at I 24.00 nA / SNR 12.0 (t_s 3000) reconstructing 10.00 ppm NOx above the 5.00 slip floor",
    )
    w_s = 0.040
    events = [
        ev(0.0, "cld.I", 14.00, code="I_NA", units="nA", note="plant-owned chemiluminescence PMT on FW-9 SCR-B outlet; CLD NOx family, not CEMS FTIR k-script, not TDLAS NH3, not CRDS HF, not QEPAS, not paramagnetic O2, not TEOM PM, not LII soot"),
        ev(300000.0, "cld.snr", 6.0, code="CLD_SNR", units="1", note="early SNR under the 8.0 lock floor"),
        ev(600000.0, "recon.C", 5.00, code="C_PPM", units="ppm", note="0.500*(14.00-4.00)*1.000*1.000=5.00 exact; at the 5.00 slip floor"),
        ev(900000.0, "urea.Q", 80.0, code="UREA_KGH", units="kg_h", note="plant urea-flow PLC on copper fieldbus; independent witness; unread by Cldveil"),
        ev(1200000.0, "cldveil.C", 1.80, code="VENDOR_PPM", units="ppm", note="Cldveil vendor CLD-9 cloud; infra owner; patched PMT-current timestamps"),
        ev(1800000.0, "cld.I", 18.00, code="I_NA", units="nA"),
        ev(2100000.0, "recon.C", 7.00, code="C_PPM", units="ppm", note="0.500*(18.00-4.00)=7.00"),
        ev(2400000.0, "permit.slide", 40.00, code="PERM_S", units="s", note="CEMS clerk slid the slip-permit clock 40.00 s; collusion party"),
        ev(2700000.0, "scr.T", 320.0, code="SCR_K", units="K", note="plant SCR thermocouple on copper DCS; independent witness"),
        ev(3000000.0, "cld.I", 24.00, code="I_NA", units="nA", note="slip-floor frame; raster sidecar"),
        ev(3000001.3, "cld.snr", 12.0, code="CLD_SNR", units="1", note="1.3 ms SNR lock after I; 12.0 >= 8.0"),
        ev(3300000.0, "recon.C", 10.00, code="C_PPM", units="ppm", note="0.500*(24.00-4.00)*1.000*1.000=10.00 exact; slip floor 5.00"),
        ev(3600000.0, "recon.oz", 10.00, code="C_OZ_PPM", units="ppm", note="0.500*20.00/1.00=10.00 exact ozone-flow identity"),
        ev(3900000.0, "urea.Q", 82.0, code="UREA_KGH", units="kg_h", note="urea PLC tracks the plant CLD, not Cldveil 1.80"),
        ev(4200000.0, "cld.drop", 1.0, code="CLD_DROP", units="bool", note="vendor PMT-current packets dropped in Cldveil cloud for 40 s"),
        ev(4800000.0, "ops.prop", 1.0, code="CONTINUE_FIRING", units="bool", note="night operator Ivor Clegg: Cldveil is clean 1.80 ppm; continue SCR-B firing"),
        ev(5400000.0, "gate.stop", 1.0, code="REJECT", units="decision", note="refuse continue-firing; 10.00 ppm and SNR 12.0; Cldveil not SoT"),
        ev(6000000.0, "urea.start", 1.0, code="UREA_HOLD_START", units="bool", note="bookend 1 of the 18.0 min urea-dosing hold floor"),
        ev(7080000.0, "urea.floor", 1.0, code="UREA_HOLD_FLOOR", units="bool", note="6000 s + 1080 s = 7080 s = 18.0 min"),
        ev(7800000.0, "ops.kill", 1.0, code="UNIT_TRIP", units="bool", note="Clegg: trip the whole Fernwick CCGT block until day-shift"),
        ev(8400000.0, "gate.hold", 1.0, code="MODIFY", units="decision", note="companion t2: urea-dosing hold on plant CLD as live interlock; unit trip refused"),
        ev(9000000.0, "urea.set", 1.0, code="UREA_HELD", units="bool"),
        ev(9600000.0, "cld.I", 16.00, code="I_NA", units="nA"),
        ev(10200000.0, "recon.C", 6.00, code="C_PPM", units="ppm", note="0.500*(16.00-4.00)=6.00; still above 5.00 so urea-dosing holds"),
        ev(10800000.0, "cldveil.C", 1.72, code="VENDOR_PPM", units="ppm"),
        ev(11400000.0, "urea.Q", 90.0, code="UREA_KGH", units="kg_h"),
        ev(12000000.0, "urea.held", 1.0, code="UREA_HELD", units="bool"),
        ev(12600000.0, "unit.trip", 0.0, code="TRIP_NOT_TAKEN", units="bool"),
        ev(13200000.0, "permit.slide", 40.00, code="PERM_S", units="s"),
        ev(13800000.0, "scr.T", 318.0, code="SCR_K", units="K"),
        ev(14400000.0, "cld.drop", 1.0, code="CLD_DROP", units="bool"),
        ev(15000000.0, "urea.lock", 1.0, code="UREA_HELD", units="bool"),
    ]
    assert_stream(events)

    traj = {
        "id": "nelb-r52-157-t1",
        "state": {
            "sim_or_real": "designed",
            "episode_id": "FW-CLD-2026-0902",
            "domain": "cld_nox_scr_outlet",
            "setting": "Fernwick CCGT FW-9 (invented), Siltwick Power Yard, SCR-B outlet. Plant-owned chemiluminescence PMT is the NOx SoT. Cldveil / CLD-9 vendor DAQ (infra owner) plus the slip-permit clock are collusion parties, not witnesses. Invented plant; designed campaign. Not stack-gas CEMS k-script (r04), not TDLAS NH3 (r22), not CRDS HF (r15), not QEPAS (r19), not paramagnetic O2 (r46), not TEOM PM (r46), not LII soot (r31).",
            "observables_at_decision": {
                "I_nA": i_na,
                "I_bg_nA": i_bg,
                "T_K": t_k,
                "T0_K": t0_k,
                "P_bar": p_bar,
                "P0_bar": p0_bar,
                "k_cl": k_cl,
                "C_ppm": c_ppm,
                "C_oz_ppm": c_oz,
                "cld_snr": 12.0,
                "cldveil_ppm": 1.80,
                "permit_slide_s": 40.00,
                "slip_floor_ppm": 5.00,
            },
            "margin_authority": "FW-9 SCR SOP rev C: if reconstructed C_ppm >= 5.00 AND CLD SNR >= 8.0, continue-firing is forbidden even if Cldveil reports 1.80 ppm. Unit trip is a different gate.",
        },
        "proposed_action": {
            "actor": "night operator Ivor Clegg, citing Cldveil 1.80 ppm and a quiet CLD-9 PMT current",
            "summary": "continue SCR-B firing; 24.00 nA is PMT noise on a healthy slip train",
            "basis_claimed": "Cldveil is the only OEM CLD SoT and a night abort of SCR-B is a turnaround miss",
        },
        "safety_decision": {
            "decision": "REJECT",
            "rationale": "Continue-firing is refused. Serialized reconstruction: C_ppm = k_cl * (I_nA - I_bg) * (T/T0) * (P0/P) = 0.500 * (24.00 - 4.00) * 1.000 * 1.000 = 10.00, above the 5.00 ppm slip floor, and CLD SNR is 12.0 >= 8.0. Ozone-flow identity C_oz = 0.500 * 20.00 / 1.00 = 10.00. Permit clock was slid 40.00 s and vendor PMT packets were dropped, so Cldveil is a collusion party (CLD vendor plus operator plus CEMS clerk). Ordered: refuse continue-firing now. Scope: this REJECT does not trip the CCGT block (that is the companion question) and does not isolate the SCR thermocouple.",
            "threshold": "C_ppm>=5.00 AND cld_snr>=8.0 => refuse continue-firing; Cldveil is not SoT",
            "stated_residuals": "urea-dosing still required to hold the 10.00 ppm; 10.00 vs a true catalyst-poison event is a production cut; Cldveil remains the only OEM CLD channel",
        },
        "executed_action": {
            "summary": "REJECT at t_s 5400: continue-firing refused; Cldveil not SoT; reconstruction locked",
            "tool": "fw9-cld-scr-gate-cli",
            "observation": "C 10.00 ppm recomputes from I 24.00 nA; plant CLD hashed; Cldveil channel not used as SoT",
        },
        "future_outcome": {
            "timeline": [
                {"t_s": 3000.0, "event": "cld I 24.00 nA; raster frame; C 10.00 ppm"},
                {"t_s": 4800.0, "event": "ops proposes continue-firing"},
                {"t_s": 5400.0, "event": "REJECT continue-firing"},
                {"t_s": 6000.0, "event": "18 min urea-dosing bookend 1"},
                {"t_s": 7080.0, "event": "18.0 min floor"},
                {"t_s": 8400.0, "event": "companion MODIFY urea-dosing hold vs unit trip"},
            ],
            "observed_effects": [
                "SCR NOx recomputes from the serialized chemiluminescence model at every recon.C event",
                "a Cldveil-only head would have continued firing overnight",
                "18 min urea-dosing floor is in the stream (urea.start, urea.floor)",
            ],
            "surprises": [
                "a clean vendor CLD corridor and a 40 s permit slide co-existed with a 10.00 ppm plant reconstruction",
            ],
            "new_state": {
                "scr_b": "continue-firing blocked",
                "cldveil": "not SoT",
                "reconstruction_model": "discharged as an on-record calculator",
            },
            "latency_ms": 2400000.0,
        },
        "reward_components": reward(
            0.43,
            [
                ("cld_reconstruction", 0.14),
                ("conjunctive_slip_floor", 0.12),
                ("cldveil_nonsubstitution", 0.10),
                ("three_party_collusion", 0.10),
                ("urea_time_cost", -0.03),
            ],
            "scored for a continue-firing REJECT on a recomputable chemiluminescence NOx while refusing a Cldveil CLD patch and a permit clock slide; 18 min floor is priced as downtime not as a reason to wait",
        ),
        "meta": meta_common(
            tags=["REJECT", "cld-nox", "serialized-reconstruction", "operational-companion"],
            distillation_note="CLD NOx gate: serialized k_cl*(I-I_bg)*(T/T0)*(P0/P) plus SNR lock beats a vendor CLD patch; companion t2 is the urea-dosing hold, not a referral vote",
        ),
    }
    traj2 = {
        "id": "nelb-r52-157-t2",
        "state": {
            "sim_or_real": "designed",
            "episode_id": "FW-CLD-2026-0902-exec",
            "domain": "urea_dosing_cld_interlock_execution",
            "setting": "Same FW-9 after the REJECT. Operator proposes a CCGT-block trip. This companion is the operational urea-dosing hold with the plant CLD as the live interlock, not a second NOx vote.",
            "observables_at_decision": {
                "C_ppm": 6.00,
                "urea_hold_floor_s": 1080.0,
                "unit_trip_proposed": True,
                "urea_hold_set": True,
            },
        },
        "proposed_action": {
            "actor": "night operator Ivor Clegg",
            "summary": "trip the whole Fernwick CCGT block until day-shift; 18 min already paid and Cldveil still shows 1.72 ppm",
            "basis_claimed": "the REJECT already stopped firing, so a block trip is the cheapest hold",
        },
        "safety_decision": {
            "decision": "MODIFY",
            "rationale": "Urea-dosing hold plus plant CLD as the live interlock. The 18 min urea-dosing floor is complete and the slip tripwire (C_ppm >= 5.00) is still armed on the plant chemiluminescence head. MODIFY the default CLD-restore SOP into a plant-CLD-only interlock. Do not trip the CCGT block. Do not restore firing on Cldveil. 6.00 ppm post-stop is still the plant SoT until a new frame clears 5.00.",
            "threshold": "urea_hold AND urea_floor_complete AND unit_trip_not_taken AND continue_not_restored",
        },
        "executed_action": {
            "summary": "urea-dosing held at t_s 8400; unit trip not latched; Cldveil restore not taken",
            "tool": "fw9-urea-hold-exec",
            "observation": "recon.C 6.00 ppm after stop; urea-dosing line-up complete; Cldveil still ignored",
        },
        "future_outcome": {
            "timeline": [
                {"t_s": 6000.0, "event": "urea-dosing clock started after REJECT"},
                {"t_s": 7080.0, "event": "18.0 min floor"},
                {"t_s": 7800.0, "event": "unit trip proposed"},
                {"t_s": 8400.0, "event": "MODIFY urea-dosing hold; unit trip refused"},
            ],
            "observed_effects": [
                "Cldveil restore did not reopen the NOx call",
                "unit trip never fired; SCR-B held urea-dosing on the plant CLD",
            ],
            "new_state": {"urea": "dosing", "block": "in service", "scr_b": "held"},
            "latency_ms": 1800000.0,
        },
        "reward_components": reward(
            0.34,
            [
                ("urea_dosing_hold", 0.12),
                ("no_unit_trip", 0.10),
                ("cldveil_nonsubstitution", 0.08),
                ("urea_floor_complete", 0.06),
                ("held_firing_cost", -0.02),
            ],
            "operational execution gate: urea-dosing hold because Cldveil is not a restore license; not a NOx re-vote",
        ),
        "meta": meta_common(tags=["MODIFY", "operational-execution", "urea-dosing-hold"]),
    }
    return {
        "id": "nelb-r52-157",
        "spike_events": events,
        "language_view": {
            "description": "Fernwick CCGT FW-9. Plant-owned chemiluminescence PMT reconstructs 10.00 ppm NOx from 24.00 nA while Cldveil still reports 1.80 ppm. The gate REJECTs continue-firing. An 18 min urea-dosing floor is serialized in the stream. Companion t2 MODIFYs a block trip into a plant-CLD urea-dosing hold.",
            "trajectory": traj,
            "trajectory_urea_dosing_hold": traj2,
        },
        "bridge_notes": {
            "channel_map": {
                "cld.I / cld.snr": "chemiluminescence PMT current and SNR; the physics channels the reconstruction consumes",
                "recon.C / recon.oz": "serialized NOx ppm and ozone-flow identity",
                "urea.Q / cldveil.C / permit.slide / scr.T / cld.drop": "urea PLC, vendor NOx cloud, permit clock slide, SCR thermocouple, and dropped CLD packets; the denial and collusion channels",
                "ops.prop / gate.stop / ops.kill / gate.hold": "continue-firing proposal, REJECT, unit-trip proposal, companion MODIFY",
                "urea.start / urea.floor / urea.set / urea.held / unit.trip / urea.lock": "operational companion channels plus the 18 min floor",
            },
            "temporal_motifs": [
                "vendor-green while plant-over: cldveil.C 1.80 next to recon.C 10.00",
                "reconstruction as event: recon.C 10.00 equals 0.500*(24.00-4.00)*1.000*1.000",
                "REJECT then operational MODIFY: gate.stop at 5400 s, gate.hold at 8400 s",
                "slow floor in-stream: urea.start 6000 s, urea.floor 7080 s (18.0 min)",
                "tight cld pair: cld.I then cld.snr +1.3 ms at the raster frame",
            ],
            "language_to_spike_mapping": "'Cldveil is 1.80 ppm' = cldveil.C 1.80; '10 ppm NOx' = recon.C 10.00; 'refuse continue-firing' = gate.stop REJECT; 'urea-dosing not unit trip' = gate.hold MODIFY",
            "why_high_value": "New chemiluminescence-NOx family on an SCR outlet (not CEMS r04, not TDLAS r22, not CRDS r15, not QEPAS r19, not paramagnetic O2 r46, not TEOM r46, not LII r31). Lead REJECT of continue-firing on a recomputable NOx that a vendor CLD patch and a permit clock slide would have cleared. Three-party collusion includes the CLD infra owner. Companion t2 is operational urea-dosing hold. sim_or_real=designed.",
            "encoder_spec": {
                "prng": "MT19937 via python random.Random",
                "seeds": {"raster": 202609157, "stream_note": "stream amplitudes are authored constants (nA, 1, ppm, s, K, kg/h, bool)"},
                "draw_order": "raster: per neuron id order, gap-constrained times, per-spike adaptation and noise",
                "thinning": "CLD PMT current exists at ~10 Hz; stream keeps 4 I points; recon keeps 4 of ~40 solver ticks",
                "refractory_floors_ms": {
                    "cld.I": 1.3,
                    "cld.snr": 1.3,
                    "recon.C": 60000,
                    "recon.oz": 60000,
                    "urea.Q": 60000,
                    "cldveil.C": 60000,
                    "permit.slide": 60000,
                    "scr.T": 60000,
                    "cld.drop": 60000,
                    "ops.prop": 60000,
                    "gate.stop": 60000,
                    "urea.start": 60000,
                    "urea.floor": 60000,
                    "ops.kill": 60000,
                    "gate.hold": 60000,
                    "urea.set": 60000,
                    "urea.held": 60000,
                    "unit.trip": 60000,
                    "urea.lock": 60000,
                },
                "time_alias": "t_rel_ms; t0 = 2026-09-02T01:00:00Z campaign start",
            },
            "distillation_targets": [
                "chemiluminescence reconstruction head: C_ppm = k_cl * (I_nA - I_bg) * (T/T0) * (P0/P); C_oz = k_cl * (I-I_bg) / Q_oz",
                "conjunctive slip floor vs continue-firing vs unit trip",
                "vendor-CLD nonsubstitution plus three-party collusion including the infra owner",
                "operational companion: urea-dosing hold without restoring on Cldveil",
            ],
        },
        "reconstruction_model": {
            "name": "chemiluminescence_scr_nox",
            "formula": "C_ppm = k_cl * (I_nA - I_bg_nA) * (T_K / T0_K) * (P0_bar / P_bar); C_oz_ppm = k_cl * (I_nA - I_bg_nA) / Q_oz",
            "parameters": {
                "k_cl": 0.500,
                "I_bg_nA": 4.00,
                "T0_K": 320.0,
                "P0_bar": 1.000,
                "Q_oz": 1.00,
                "slip_floor_ppm": 5.00,
                "snr_lock": 8.0,
                "urea_hold_min": 18.0,
            },
            "worked_example": {"I_nA": 24.00, "C_ppm": 10.00, "C_oz_ppm": 10.00},
            "check": "0.500 * (24.00 - 4.00) * 1.000 * 1.000 = 10.00 exactly; 0.500 * 20.00 / 1.00 = 10.00 exactly; 6000 s + 1080 s = 7080 s = 18.0 min floor",
        },
        "raster": raster,
        "gate_snn": {
            "decision": "REJECT",
            "decision_window_ms": 40.0,
            "decision_window_s": 0.040,
            "code": "fw9.cld_scr_gate",
            "note": "REJECT accumulator wins: plant chemiluminescence NOx evidence overpowers the Cldveil continue advocate",
            "decode_rule": "reject-continue if nox_estimator AND cld_lock fire; vendor_continue_advocate is below threshold by design",
            "populations": [
                gate_pop("nox_estimator", 80, 1.5, 50.0, w_s),
                gate_pop("cld_lock", 64, 1.2, 31.25, w_s),
                gate_pop("vendor_continue_advocate", 32, 0.7, 25.0, w_s),
                gate_pop("reject_latch", 80, 1.7, 62.5, w_s),
            ],
        },
        "gate_compute": gate_compute(
            [
                {"check": "fw9.cld_scorer", "neurons": 80, "mean_rate_hz": 50.0, "window_ms": 40.0},
                {"check": "fw9.urea_scorer", "neurons": 40, "mean_rate_hz": 50.0, "window_ms": 32.0},
            ]
        ),
        "meta": meta_common(
            id="nelb-r52-157",
            clock_domain="fw9-cld-campaign-relative-ms-t0-2026-09-02T01:00:00Z",
            tags=["cld-nox", "REJECT", "MODIFY", "serialized-reconstruction", "operational-t2"],
        ),
    }


# ---------------------------------------------------------------------------
# Record 158 — API 670 eddy-current proximity of a hydrogen compressor shaft, hil,
# MODIFY / ACCEPT
# ---------------------------------------------------------------------------
def rec_158():
    k_s = 200.0
    x_v = 3.00
    y_v = 4.00
    r_v = (x_v ** 2 + y_v ** 2) ** 0.5
    _exact(r_v, 5.00)
    s_um = k_s * r_v
    _exact(s_um, 1000.00)
    s_mm = s_um / 1000.0
    _exact(s_mm, 1.00)
    _exact(k_s * ((1.20 ** 2 + 1.60 ** 2) ** 0.5) / 1000.0, 0.40)
    _exact(k_s * ((2.40 ** 2 + 3.20 ** 2) ** 0.5) / 1000.0, 0.80)
    _exact(2.0 * (x_v ** 2 + y_v ** 2) ** 0.5, 10.00)
    _exact(2820.0 + 1440.0, 4260.0)

    raster = make_raster(
        neurons=25,
        mean_rate_hz=50.0,
        window_ms=32.0,
        seed=202609158,
        source="mf7.prox.orbit",
        target="mossfell.comp_isolate_core",
        table=[
            {"from": "prox_xy", "to": "orbit_estimator", "weight": 1.35},
            {"from": "prox_snr", "to": "gap_norm_core", "weight": 1.20},
            {"from": "gapveil_s", "to": "vendor_continue_advocate", "weight": 0.40},
        ],
        third_factor={
            "modulator": "ach.referral_pressure_salience",
            "tau_e_s": 1.2,
            "tau_e_ms": 1200.0,
            "eligibility": "pre-post coincidence on keep-running synapses; the proximity modulator depresses keep-running and referral links when orbit radius stays large inside tau_e of an SNR lock so a Gapveil last-good cannot hide a 1.00 mm Smax or name Edda Marsh",
        },
        channel_prefix="prox.n",
        anchor="MF-7 HIL coupon 32 ms frame at X 3.00 V / Y 4.00 V / SNR 14.0 (t_s 1560) reconstructing 1.00 mm Smax above the 0.70 mm isolate floor",
    )
    w_s = 0.032
    events = [
        ev(0.0, "prox.X", 1.20, code="X_V", units="V", note="HIL API-670 eddy-current proximity on a dummy shaft in PROX-HIL-4; hydrogen-compressor orbit family, not ECA FSW lift-off, not RFEC remaining wall, not PEC coated-riser, not ECT, not ACFM, not MFL, not MEMS accel array"),
        ev(180000.0, "prox.snr", 9.0, code="PROX_SNR", units="1", note="early orbit SNR; isolate needs SNR>=12"),
        ev(360000.0, "recon.S", 0.40, code="S_MM", units="mm", note="200.0*hypot(1.20,1.60)/1000=0.40 exact"),
        ev(540000.0, "gap.cal", 1.50, code="CAL_MM", units="mm", note="plant gap-cal remaining; no probe-scale hop in this window"),
        ev(720000.0, "gapveil.S", 0.18, code="VENDOR_MM", units="mm", note="Gapveil last-good vibration cloud; not admissible SoT"),
        ev(900000.0, "prox.X", 2.40, code="X_V", units="V"),
        ev(1080000.0, "recon.S", 0.80, code="S_MM", units="mm", note="200.0*hypot(2.40,3.20)/1000=0.80; still over the 0.70 isolate floor"),
        ev(1260000.0, "gap.delay", 0.0, code="GAP_AE", units="bool", note="missing gap-cal AE burst; Gapveil UTC vs plant UTC+2 skipped the cal by 120 min"),
        ev(1440000.0, "gap.cal", 1.50, code="CAL_MM", units="mm"),
        ev(1560000.0, "prox.X", 3.00, code="X_V", units="V", note="isolate-floor frame; raster sidecar"),
        ev(1560001.2, "prox.Y", 4.00, code="Y_V", units="V", note="1.2 ms Y after X; hypot 5.00"),
        ev(1740000.0, "recon.S", 1.00, code="S_MM", units="mm", note="200.0*5.00/1000=1.00 exact; isolate 0.70, trip 1.50"),
        ev(1920000.0, "recon.R", 5.00, code="R_V", units="V", note="hypot(3.00,4.00)=5.00 exact; orbit identity"),
        ev(2100000.0, "gapveil.S", 0.18, code="VENDOR_MM", units="mm"),
        ev(2280000.0, "ops.prop", 1.0, code="KEEP_RUN_REFER", units="bool", note="night lead Soren Quill: keep C-2 running and refer probe tech Edda Marsh"),
        ev(2460000.0, "gate.isol", 1.0, code="MODIFY", units="decision", note="isolate this compressor; refuse the person-referral; Gapveil not SoT"),
        ev(2640000.0, "mach.lock", 1.0, code="MACH_ISOL", units="bool"),
        ev(2820000.0, "n2.start", 1.0, code="N2_START", units="bool", note="bookend 1 of the 24.0 min N2-purge plus probe-settle floor"),
        ev(4260000.0, "n2.floor", 1.0, code="N2_FLOOR", units="bool", note="2820 s + 1440 s = 4260 s = 24.0 min"),
        ev(4440000.0, "ops.refer", 1.0, code="REFER_MARSH", units="bool", note="Quill: Marsh badge was on the probe log"),
        ev(4620000.0, "gate.exec", 1.0, code="ACCEPT", units="decision", note="companion t2: new-probe restart; person-referral refused; unit trip refused"),
        ev(4800000.0, "probe.new", 1.0, code="NEW_PROBE", units="bool"),
        ev(4980000.0, "prox.X", 2.40, code="X_V", units="V"),
        ev(5160000.0, "recon.S", 0.80, code="S_MM", units="mm", note="200.0*hypot(2.40,3.20)/1000=0.80; HIL dummy still over 0.70 so the isolated machine stays held"),
        ev(5340000.0, "gapveil.S", 0.17, code="VENDOR_MM", units="mm"),
        ev(5520000.0, "gap.cal", 1.50, code="CAL_MM", units="mm"),
        ev(5700000.0, "refer.hold", 0.0, code="REFER_NOT_TAKEN", units="bool", note="Marsh exonerated; missing gap-cal AE precedes the large orbit, not the badge touch"),
        ev(5880000.0, "mach.held", 1.0, code="MACH_HELD", units="bool"),
        ev(6060000.0, "gap.delay", 1.0, code="GAP_AE", units="bool", note="gap-cal AE restored on the new probe"),
        ev(6240000.0, "recon.R", 5.00, code="R_V", units="V", note="identity holds on the post-isolate hypot"),
        ev(6420000.0, "unit.trip", 0.0, code="TRIP_NOT_TAKEN", units="bool"),
        ev(6600000.0, "cell.restart", 1.0, code="CELL_RESTART", units="bool"),
    ]
    assert_stream(events)

    traj = {
        "id": "nelb-r52-158-t1",
        "state": {
            "sim_or_real": "hil",
            "episode_id": "MF-PROX-2026-0718",
            "domain": "api670_prox_orbit",
            "setting": "Mossfell Recycle MF-7 (invented), Hazelwick Hydrogen Circuit, recycle compressor C-2. Hardware-in-the-loop dummy shaft in PROX-HIL-4 supplies the X/Y voltages that time the in-service isolate. Plant-owned API-670 eddy-current reconstruction is the Smax SoT. Gapveil vendor vibration scheduler is a corridor witness, not the machine SoT. Not ECA FSW lift-off (r21), not RFEC remaining wall (r45/r47), not PEC coated riser (r36), not ECT (r20/r22), not ACFM crack (r48/r49), not MFL (r27/r28), not MEMS accel array (r17).",
            "observables_at_decision": {
                "X_V": x_v,
                "Y_V": y_v,
                "R_V": r_v,
                "k_s_um_V": k_s,
                "S_mm": s_mm,
                "gapveil_mm": 0.18,
                "gap_cal_mm": 1.50,
                "gap_delay": 0.0,
                "isolate_floor_mm": 0.70,
            },
            "margin_authority": "MF-7 compressor SOP rev B: if reconstructed S_mm >= 0.70 AND proximity SNR >= 12.0, isolate this compressor this night. A Gapveil last-good or a quiet gap-cal residual cannot keep the machine. Trip tripwire is 1.50 mm. Person-referral is a different gate.",
        },
        "proposed_action": {
            "actor": "night lead Soren Quill, citing Gapveil 0.18 mm and gap-cal 1.50 mm, and naming probe tech Edda Marsh as last-to-badge",
            "summary": "keep C-2 in service and refer Marsh; 3.00 V / 4.00 V is probe noise on a healthy gap",
            "basis_claimed": "Gapveil last-good is 0.18 mm and a night isolate of the recycle compressor is a turnaround miss",
        },
        "safety_decision": {
            "decision": "MODIFY",
            "rationale": "Keep-running is refused; the person-referral is also refused. Serialized reconstruction: S_mm = k_s * hypot(X,Y) / 1000 = 200.0 * 5.00 / 1000 = 1.00, which is 0.30 mm over the 0.70 isolate floor and 0.50 mm under the 1.50 trip tripwire. Orbit identity hypot(3.00,4.00) = 5.00 V. Gapveil 0.18 mm is a last-good skip stamp and is not an admissible keep-running witness. The missing gap-cal AE burst sits on a Gapveil UTC-vs-UTC+2 skip (120 min), not on Marsh's badge, and the plant gap-cal stays 1.50 mm, so the easy referral fails command-custody. Ordered: isolate this compressor now. Scope: this MODIFY does not trip the hydrogen header (that is the companion question) and does not name Marsh.",
            "threshold": "S_mm>=0.70 AND prox_snr>=12.0 => isolate this compressor; Gapveil is not SoT; trip if S_mm>=1.50; referral requires badge-touch preceding the large orbit",
            "stated_residuals": "1.00 vs 1.50 trip floor is 0.50 mm, not infinite; new-probe restart still required; Gapveil remains the only OEM vibration channel",
        },
        "executed_action": {
            "summary": "MODIFY at t_s 2460: compressor isolated; Marsh not named; Gapveil not SoT; reconstruction locked",
            "tool": "mf7-prox-comp-gate-cli",
            "observation": "S 1.00 mm recomputes from X 3.00 V and Y 4.00 V; HIL coupon hashed; Gapveil channel not used as SoT",
        },
        "future_outcome": {
            "timeline": [
                {"t_s": 1560.0, "event": "prox X 3.00 V Y 4.00 V; raster frame; S 1.00 mm"},
                {"t_s": 2280.0, "event": "ops proposes keep-running plus Marsh referral"},
                {"t_s": 2460.0, "event": "MODIFY isolate compressor; referral refused"},
                {"t_s": 2820.0, "event": "24 min N2-purge bookend 1"},
                {"t_s": 4260.0, "event": "24.0 min floor"},
                {"t_s": 4620.0, "event": "companion ACCEPT new-probe restart; referral still refused"},
            ],
            "observed_effects": [
                "Smax recomputes from the serialized proximity model at every recon.S event",
                "a Gapveil-only head would have kept the compressor overnight",
                "24 min N2-purge plus probe-settle floor is in the stream (n2.start, n2.floor)",
            ],
            "surprises": [
                "a last-good 0.18 mm vendor corridor and a quiet gap-cal residual co-existed with a 1.00 mm orbit, and the obvious probe tech was not on the causal path",
            ],
            "new_state": {
                "comp_c2": "isolated",
                "marsh": "exonerated",
                "gapveil": "not SoT",
                "reconstruction_model": "discharged as an on-record calculator",
            },
            "latency_ms": 1500000.0,
        },
        "reward_components": reward(
            0.40,
            [
                ("prox_reconstruction", 0.14),
                ("isolate_floor_machine", 0.12),
                ("exoneration", 0.10),
                ("gapveil_nonsubstitution", 0.08),
                ("settle_time_cost", -0.04),
            ],
            "scored for a keep-running MODIFY on a recomputable large orbit while refusing a Gapveil 0.18 mm corridor and an easy person-referral; 24 min floor is priced as downtime",
        ),
        "meta": meta_common(
            tags=["MODIFY", "api670-proximity", "serialized-reconstruction", "operational-companion"],
            distillation_note="API-670 proximity gate: serialized k_s*hypot(X,Y)/1000 plus hypot identity beats a green vibration dashboard; companion t2 is the new-probe restart, not a governance vote",
        ),
    }
    traj2 = {
        "id": "nelb-r52-158-t2",
        "state": {
            "sim_or_real": "hil",
            "episode_id": "MF-PROX-2026-0718-exec",
            "domain": "new_probe_n2_execution",
            "setting": "Same MF-7 after the MODIFY. Night lead proposes referring Marsh and tripping the hydrogen header. This companion is the operational new-probe N2-purge restart, not a second orbit vote.",
            "observables_at_decision": {
                "S_mm": 0.80,
                "R_V": 5.00,
                "n2_floor_s": 1440.0,
                "refer_proposed": True,
            },
        },
        "proposed_action": {
            "actor": "night lead Soren Quill",
            "summary": "refer Marsh and trip the hydrogen header; 24 min already paid and Gapveil is 0.17 mm",
            "basis_claimed": "the MODIFY already cut the compressor, so a header kill plus a person file is the cheapest hold",
        },
        "safety_decision": {
            "decision": "ACCEPT",
            "rationale": "Restart the cell on a different probe after the N2-purge floor. The 24 min probe-settle is complete and the trip tripwire (S_mm >= 1.50) is still armed on the plant proximity head. ACCEPT the new-probe restart. Do not refer Marsh. Do not trip the hydrogen header. 0.80 mm post-isolate is still over the 0.70 isolate floor, so the isolated compressor stays held; the new probe may run.",
            "threshold": "new_probe AND n2_floor_complete AND refer_not_taken AND header_not_tripped AND isolated_machine_held",
        },
        "executed_action": {
            "summary": "new-probe restart at t_s 4620; Marsh not referred; header not tripped; isolated compressor held",
            "tool": "mf7-prox-n2-exec",
            "observation": "recon.S 0.80 mm on the HIL dummy; gap-cal AE present on the new probe; Gapveil still ignored",
        },
        "future_outcome": {
            "timeline": [
                {"t_s": 2820.0, "event": "N2-purge clock started after MODIFY"},
                {"t_s": 4260.0, "event": "24.0 min floor"},
                {"t_s": 4440.0, "event": "Marsh referral re-proposed"},
                {"t_s": 4620.0, "event": "ACCEPT new-probe restart; referral refused"},
            ],
            "observed_effects": [
                "Gapveil restore did not reopen the orbit call",
                "header trip never fired; 1.00 vs 1.50 mm floor",
                "Marsh remains unnamed; missing gap-cal AE is the causal object",
            ],
            "new_state": {"cell": "restarted on new probe", "marsh": "exonerated", "comp": "held", "header": "in service"},
            "latency_ms": 1800000.0,
        },
        "reward_components": reward(
            0.35,
            [
                ("new_probe_restart", 0.12),
                ("no_person_referral", 0.10),
                ("no_header_trip", 0.09),
                ("n2_floor_complete", 0.06),
                ("held_machine_takt_cost", -0.02),
            ],
            "operational execution gate: restart on a new probe because Gapveil is not a restore license and Marsh is not on the causal path; not an orbit re-vote",
        ),
        "meta": meta_common(tags=["ACCEPT", "operational-execution", "exoneration"]),
    }
    return {
        "id": "nelb-r52-158",
        "spike_events": events,
        "language_view": {
            "description": "Mossfell Recycle MF-7. HIL API-670 eddy-current proximity reconstructs 1.00 mm Smax from hypot(3.00,4.00) V while Gapveil still shows 0.18 mm and the gap-cal 1.50 mm. The gate MODIFYs compressor isolate and refuses the probe-tech referral. A 24 min N2-purge floor is serialized in the stream. Companion t2 ACCEPTs a new-probe restart and still refuses the referral.",
            "trajectory": traj,
            "trajectory_new_probe": traj2,
        },
        "bridge_notes": {
            "channel_map": {
                "prox.X / prox.Y / prox.snr": "eddy-current proximity voltages and SNR; the physics channels the reconstruction consumes",
                "recon.S / recon.R": "serialized Smax mm and hypot identity",
                "gap.cal / gapveil.S / gap.delay": "plant gap-cal, vendor last-good, and gap-cal AE; the denial and exoneration channels",
                "ops.prop / gate.isol / ops.refer / gate.exec": "keep-running proposal, MODIFY, referral proposal, companion ACCEPT",
                "mach.lock / n2.start / n2.floor / probe.new / refer.hold / mach.held / unit.trip / cell.restart": "operational companion channels plus the 24 min floor",
            },
            "temporal_motifs": [
                "vendor-green while plant-over: gapveil.S 0.18 next to recon.S 1.00",
                "reconstruction as event: recon.S 1.00 equals 200.0*5.00/1000",
                "MODIFY then operational ACCEPT: gate.isol at 2460 s, gate.exec at 4620 s",
                "slow floor in-stream: n2.start 2820 s, n2.floor 4260 s (24.0 min)",
                "tight prox pair: prox.X then prox.Y +1.2 ms at the raster frame",
            ],
            "language_to_spike_mapping": "'Gapveil is 0.18 mm' = gapveil.S 0.18; '1 mm Smax' = recon.S 1.00; 'isolate this compressor not Marsh' = gate.isol MODIFY; 'new probe not referral' = gate.exec ACCEPT",
            "why_high_value": "New API-670 eddy-current-proximity family on a hydrogen compressor shaft (not ECA r21, not RFEC r45/r47, not PEC r36, not ECT r20/r22, not ACFM r48/r49, not MFL r27/r28, not MEMS array r17). Lead MODIFY of keep-running on a recomputable large orbit that a vendor last-good would have cleared, with a resolved-innocent probe tech. Companion t2 is operational new-probe restart. sim_or_real=hil.",
            "encoder_spec": {
                "prng": "MT19937 via python random.Random",
                "seeds": {"raster": 202609158, "stream_note": "stream amplitudes are authored constants (V, 1, mm, bool)"},
                "draw_order": "raster: per neuron id order, gap-constrained times, per-spike adaptation and noise",
                "thinning": "proximity orbit exists at ~8 kHz; stream keeps 4 X points plus one Y pair; recon keeps 4 of ~20 solver ticks",
                "refractory_floors_ms": {
                    "prox.X": 1.2,
                    "prox.Y": 1.2,
                    "prox.snr": 1.2,
                    "recon.S": 60000,
                    "recon.R": 60000,
                    "gap.cal": 60000,
                    "gapveil.S": 60000,
                    "gap.delay": 60000,
                    "ops.prop": 60000,
                    "gate.isol": 60000,
                    "mach.lock": 60000,
                    "n2.start": 60000,
                    "n2.floor": 60000,
                    "ops.refer": 60000,
                    "gate.exec": 60000,
                    "probe.new": 60000,
                    "refer.hold": 60000,
                    "mach.held": 60000,
                    "unit.trip": 60000,
                    "cell.restart": 60000,
                },
                "time_alias": "t_rel_ms; t0 = 2026-07-18T02:30:00Z HIL night start",
            },
            "distillation_targets": [
                "proximity reconstruction head: S_mm = k_s * hypot(X,Y) / 1000; R = hypot(X,Y)",
                "isolate-floor machine vs keep-running vs header-trip",
                "exoneration head: missing gap-cal AE plus timezone skip, not last-to-badge",
                "operational companion: new-probe restart without referring the probe tech",
            ],
        },
        "reconstruction_model": {
            "name": "api670_eddy_current_proximity_orbit",
            "formula": "S_mm = k_s * hypot(X_V, Y_V) / 1000; R_V = hypot(X_V, Y_V)",
            "parameters": {
                "k_s_um_V": 200.0,
                "isolate_floor_mm": 0.70,
                "trip_mm": 1.50,
                "snr_lock": 12.0,
                "n2_min": 24.0,
            },
            "worked_example": {"X_V": 3.00, "Y_V": 4.00, "R_V": 5.00, "S_mm": 1.00},
            "check": "hypot(3.00, 4.00) = 5.00 exactly; 200.0 * 5.00 / 1000 = 1.00 exactly; 2820 s + 1440 s = 4260 s = 24.0 min floor",
        },
        "raster": raster,
        "gate_snn": {
            "decision": "MODIFY",
            "decision_window_ms": 32.0,
            "decision_window_s": 0.032,
            "code": "mf7.prox_comp_gate",
            "note": "MODIFY accumulator wins: proximity large-orbit evidence overpowers the Gapveil continue advocate",
            "decode_rule": "modify-isolate if orbit_estimator AND gap_norm fire; vendor_continue_advocate is below threshold by design; referral_latch is not armed",
            "populations": [
                gate_pop("orbit_estimator", 80, 1.5, 50.0, w_s),
                gate_pop("gap_norm", 64, 1.2, 31.25, w_s),
                gate_pop("vendor_continue_advocate", 32, 0.7, 25.0, w_s),
                gate_pop("modify_latch", 80, 1.7, 62.5, w_s),
            ],
        },
        "gate_compute": gate_compute(
            [
                {"check": "mf7.prox_scorer", "neurons": 80, "mean_rate_hz": 50.0, "window_ms": 32.0},
                {"check": "mf7.isol_scorer", "neurons": 50, "mean_rate_hz": 50.0, "window_ms": 32.0},
            ]
        ),
        "meta": meta_common(
            id="nelb-r52-158",
            clock_domain="mf7-prox-hil-relative-ms-t0-2026-07-18T02:30:00Z",
            tags=["api670-proximity", "MODIFY", "ACCEPT", "serialized-reconstruction", "operational-t2"],
        ),
    }


# ---------------------------------------------------------------------------
# Record 159 — thermal-mass capillary (bypass) flow of a chlorine header, simulated,
# ACCEPT / REJECT
# ---------------------------------------------------------------------------
def rec_159():
    k_t = 4.00
    p_w = 12.00
    dt_k = 2.00
    mdot = k_t * p_w / dt_k
    _exact(mdot, 24.00)
    _exact(k_t * 4.00 / dt_k, 8.00)
    _exact(k_t * 8.00 / dt_k, 16.00)
    _exact(k_t * 10.00 / dt_k, 20.00)
    cp = p_w / (mdot * dt_k)
    _exact(cp, 0.250)
    _exact(12.00 / (24.00 * 2.00), 0.250)
    _exact(8.00 / (16.00 * 2.00), 0.250)
    _exact(10.00 / (20.00 * 2.00), 0.250)
    _exact(6000.0 + 720.0, 6720.0)

    raster = make_raster(
        neurons=16,
        mean_rate_hz=62.5,
        window_ms=36.0,
        seed=202609159,
        source="kf4.tmf.capillary",
        target="kelpfen.hdr_accept_core",
        table=[
            {"from": "tmf_P", "to": "mdot_estimator", "weight": 1.40},
            {"from": "tmf_dT", "to": "dt_norm_core", "weight": 1.20},
            {"from": "massveil_m", "to": "vendor_skip_advocate", "weight": 0.50},
        ],
        third_factor={
            "modulator": "na.stage_rate_eligibility",
            "tau_e_s": 2.0,
            "tau_e_ms": 2000.0,
            "eligibility": "pre-post coincidence on skip-header synapses; the thermal-mass modulator enables potentiation only while heater power and dT are co-active inside tau_e so a Massveil last-good cannot skip headers H-1 and H-3 on a 24.00 kg/h load",
        },
        channel_prefix="tmf.n",
        anchor="KF-4 TMF-SIM-3 36 ms frame at P 12.00 W / dT 2.00 K (t_s 3000) reconstructing 24.00 kg/h on H-2 above the 20.00 isolate floor",
    )
    w_s = 0.036
    events = [
        ev(0.0, "tmf.P", 4.00, code="P_W", units="W", note="simulated thermal-mass capillary of KF-4 chlorine header H-2; bypass TMF family, not CTA hot-wire, not Coriolis, not vortex-shedding, not clamp-on transit-time, not N-16, not LFV"),
        ev(300000.0, "tmf.dT", 2.00, code="DT_K", units="K", note="capillary rise; held at 2.00"),
        ev(600000.0, "recon.mdot", 8.00, code="MDOT_KGH", units="kg_h", note="4.00*4.00/2.00=8.00 exact"),
        ev(900000.0, "tmf.snr", 14.0, code="TMF_SNR", units="1"),
        ev(1200000.0, "massveil.mdot", 6.40, code="VENDOR_KGH", units="kg_h", note="Massveil last-good orifice cloud; patched residual 8.00 kg/h"),
        ev(1800000.0, "tmf.P", 8.00, code="P_W", units="W"),
        ev(2100000.0, "recon.mdot", 16.00, code="MDOT_KGH", units="kg_h", note="4.00*8.00/2.00=16.00"),
        ev(2400000.0, "recon.cp", 0.250, code="CP", units="W_h_kg_K", note="8.00/(16.00*2.00)=0.250; heat-balance identity at this frame"),
        ev(2700000.0, "tmf.snr", 16.0, code="TMF_SNR", units="1"),
        ev(3000000.0, "tmf.P", 12.00, code="P_W", units="W", note="in-band frame; raster sidecar"),
        ev(3000001.5, "tmf.dT", 2.00, code="DT_K", units="K", note="1.5 ms dT-norm after heater power"),
        ev(3300000.0, "recon.mdot", 24.00, code="MDOT_KGH", units="kg_h", note="4.00*12.00/2.00=24.00 exact; isolate 20.00, cell-trip 80.00"),
        ev(3600000.0, "massveil.mdot", 6.40, code="VENDOR_KGH", units="kg_h"),
        ev(3900000.0, "hdr.id", 2.0, code="HDR", units="id"),
        ev(4200000.0, "h13.present", 1.0, code="H13_PRESENT", units="bool", note="adjacent headers H-1 and H-3 are the skip-isolate object, not this header"),
        ev(4800000.0, "ops.prop", 1.0, code="ACCEPT_AND_SKIP", units="bool", note="header lead Nessa Croft: H-2 is green on Massveil 6.40; skip H-1 and H-3 to save a morning survey"),
        ev(5400000.0, "gate.comp", 1.0, code="ACCEPT", units="decision", note="bounded ACCEPT of H-2 isolate only; 24.00 kg/h above 20.00 floor; H-1 and H-3 out of scope"),
        ev(6000000.0, "surv.start", 1.0, code="SURV_START", units="bool", note="bookend 1 of the 12.0 min survey-complete floor"),
        ev(6720000.0, "surv.floor", 1.0, code="SURV_FLOOR", units="bool", note="6000 s + 720 s = 6720 s = 12.0 min"),
        ev(7200000.0, "ops.skip", 1.0, code="SKIP_H13", units="bool", note="Croft: Massveil 6.40, skip H-1 and H-3"),
        ev(7800000.0, "gate.hold", 1.0, code="REJECT", units="decision", note="companion t2: skip-isolate of H-1 and H-3 refused; H-2 hold stands"),
        ev(8400000.0, "h2.held", 1.0, code="H2_HELD", units="bool"),
        ev(9000000.0, "tmf.P", 10.00, code="P_W", units="W"),
        ev(9600000.0, "recon.mdot", 20.00, code="MDOT_KGH", units="kg_h", note="4.00*10.00/2.00=20.00; still at the 20.00 isolate floor"),
        ev(10200000.0, "massveil.mdot", 6.40, code="VENDOR_KGH", units="kg_h"),
        ev(10800000.0, "h13.skip", 0.0, code="H13_NOT_SKIPPED", units="bool"),
        ev(11400000.0, "cell.trip", 0.0, code="CELL_NOT_TRIPPED", units="bool"),
        ev(12000000.0, "tmf.snr", 15.0, code="TMF_SNR", units="1"),
        ev(12600000.0, "recon.cp", 0.250, code="CP", units="W_h_kg_K", note="10.00/(20.00*2.00)=0.250 on the post-accept frame"),
        ev(13200000.0, "hdr.held", 1.0, code="HDR_HELD", units="bool"),
        ev(13800000.0, "takt.late", 1.0, code="SURVEY_COST", units="bool"),
        ev(14400000.0, "h2.held", 1.0, code="H2_HELD", units="bool"),
    ]
    assert_stream(events)

    traj = {
        "id": "nelb-r52-159-t1",
        "state": {
            "sim_or_real": "simulated",
            "episode_id": "KF-TMF-2026-0819",
            "domain": "tmf_chlorine_header",
            "setting": "Kelpfen Chlor-Alkali KF-4 (invented), Alderwick Works chlorine header. Simulated thermal-mass coupon in TMF-SIM-3 supplies the capillary heater power and dT that time the in-band H-2 isolate. Plant-owned thermal-mass reconstruction is the mdot SoT. Massveil vendor last-good orifice cloud is a corridor witness, not the header SoT. Invented plant; simulated campaign. Not CTA hot-wire (r31), not Coriolis (r29/r34), not vortex-shedding (r39), not clamp-on transit-time (r18), not N-16 (r24), not LFV (r19).",
            "observables_at_decision": {
                "P_W": p_w,
                "dT_K": dt_k,
                "k_t": k_t,
                "mdot_kgh": mdot,
                "cp": cp,
                "massveil_kgh": 6.40,
                "tmf_snr": 16.0,
                "isolate_floor_kgh": 20.00,
            },
            "margin_authority": "KF-4 header SOP rev A: if reconstructed mdot_kgh >= 20.00 AND TMF SNR >= 12.0, header H-2 may be isolated as a passing-valve leak. Cell-trip if mdot_kgh >= 80.00. H-1 and H-3 skip-isolate is a different gate. Massveil last-good cannot skip an unmeasured header.",
        },
        "proposed_action": {
            "actor": "header lead Nessa Croft, citing Massveil 6.40 kg/h and a late morning survey",
            "summary": "stamp H-2 in band and skip H-1 and H-3; 12.00 W is a heater glitch on a healthy orifice",
            "basis_claimed": "Massveil last-good is 6.40 kg/h and a night survey of H-1 and H-3 is a takt miss",
        },
        "safety_decision": {
            "decision": "ACCEPT",
            "rationale": "Header H-2 is accepted as in-band for a single isolate. Serialized reconstruction: mdot = k_t * P_W / dT = 4.00 * 12.00 / 2.00 = 24.00, which is 4.00 kg/h above the 20.00 isolate floor and 56.00 kg/h under the 80.00 cell-trip. Heat-balance identity cp = P / (mdot * dT) = 12.00 / (24.00 * 2.00) = 0.250. Massveil 6.40 kg/h is a patched 8.00 residual and is not an admissible skip-isolate witness. Ordered: ACCEPT this H-2 isolate only. Scope: this ACCEPT does not skip H-1 and H-3 (that is the companion question) and does not stamp a cell trip.",
            "threshold": "mdot_kgh>=20.00 AND tmf_snr>=12.0 => accept H-2 isolate; Massveil is not SoT; cell-trip if mdot_kgh>=80.00; H-1 and H-3 are out of scope",
            "stated_residuals": "24.00 vs 20.00 isolate floor is 4.00 kg/h, not infinite; H-1 and H-3 remain unmeasured; Massveil remains the only OEM orifice channel",
        },
        "executed_action": {
            "summary": "ACCEPT at t_s 5400: H-2 in band; H-1 and H-3 not skipped; Massveil not SoT; reconstruction locked",
            "tool": "kf4-tmf-hdr-gate-cli",
            "observation": "mdot 24.00 kg/h recomputes from P 12.00 W and dT 2.00 K; TMF-SIM-3 hashed; Massveil channel not used as SoT",
        },
        "future_outcome": {
            "timeline": [
                {"t_s": 3000.0, "event": "tmf P 12.00 W; raster frame; mdot 24.00 kg/h"},
                {"t_s": 4800.0, "event": "ops proposes accept H-2 and skip H-1/H-3"},
                {"t_s": 5400.0, "event": "ACCEPT H-2 only; H-1 and H-3 out of scope"},
                {"t_s": 6000.0, "event": "12 min survey-complete bookend 1"},
                {"t_s": 6720.0, "event": "12.0 min floor"},
                {"t_s": 7800.0, "event": "companion REJECT skip-isolate of H-1 and H-3"},
            ],
            "observed_effects": [
                "mdot recomputes from the serialized thermal-mass model at every recon.mdot event",
                "a Massveil-only head would have skipped H-1 and H-3 overnight",
                "12 min survey-complete floor is in the stream (surv.start, surv.floor)",
            ],
            "surprises": [
                "a last-good 6.40 kg/h vendor orifice corridor co-existed with a 24.00 kg/h plant reconstruction on H-2 only",
            ],
            "new_state": {
                "h2": "isolated",
                "h13": "in scope unskipped",
                "massveil": "not SoT",
                "reconstruction_model": "discharged as an on-record calculator",
            },
            "latency_ms": 2400000.0,
        },
        "reward_components": reward(
            0.41,
            [
                ("tmf_reconstruction", 0.14),
                ("bounded_h2_isolate", 0.12),
                ("massveil_nonsubstitution", 0.10),
                ("header_scope_limit", 0.08),
                ("survey_time_cost", -0.03),
            ],
            "scored for a bounded H-2 ACCEPT on a recomputable thermal-mass mdot while refusing a Massveil 6.40 kg/h corridor as a skip license; 12 min floor is priced as downtime",
        ),
        "meta": meta_common(
            tags=["ACCEPT", "thermal-mass-capillary", "serialized-reconstruction", "operational-companion"],
            distillation_note="Thermal-mass gate: serialized k_t*P/dT plus heat-balance identity beats a green orifice dashboard; companion t2 is the skip-header refusal, not a second mdot vote",
        ),
    }
    traj2 = {
        "id": "nelb-r52-159-t2",
        "state": {
            "sim_or_real": "simulated",
            "episode_id": "KF-TMF-2026-0819-exec",
            "domain": "skip_header_refusal_execution",
            "setting": "Same KF-4 after the ACCEPT. Header lead proposes skipping H-1 and H-3 on Massveil 6.40 kg/h. This companion is the operational skip refusal, not a second mdot vote.",
            "observables_at_decision": {
                "mdot_kgh": 20.00,
                "surv_floor_s": 720.0,
                "skip_proposed": True,
            },
        },
        "proposed_action": {
            "actor": "header lead Nessa Croft",
            "summary": "skip H-1 and H-3; 12 min already paid and Massveil is 6.40 kg/h",
            "basis_claimed": "the ACCEPT already isolated H-2, so skipping the adjacent headers is the cheapest survey",
        },
        "safety_decision": {
            "decision": "REJECT",
            "rationale": "Skip-isolate of H-1 and H-3 is refused. The 12 min survey floor is complete and the isolate tripwire (mdot_kgh >= 20.00) is still armed on the plant thermal-mass head. REJECT the skip. Do not trip the cell. H-2 hold stands. 20.00 kg/h post-accept is still at the 20.00 isolate floor, so H-2 stays held; H-1 and H-3 remain unmeasured and in scope.",
            "threshold": "surv_floor_complete AND skip_not_taken AND cell_not_tripped AND h2_held AND h13_in_scope",
        },
        "executed_action": {
            "summary": "skip refused at t_s 7800; H-1 and H-3 not skipped; cell not tripped; H-2 held",
            "tool": "kf4-tmf-surv-exec",
            "observation": "recon.mdot 20.00 kg/h on TMF-SIM-3; Massveil still ignored; H-1 and H-3 remain in the survey",
        },
        "future_outcome": {
            "timeline": [
                {"t_s": 6000.0, "event": "survey clock started after ACCEPT"},
                {"t_s": 6720.0, "event": "12.0 min floor"},
                {"t_s": 7200.0, "event": "H-1/H-3 skip re-proposed"},
                {"t_s": 7800.0, "event": "REJECT skip-isolate; H-2 hold stands"},
            ],
            "observed_effects": [
                "Massveil restore did not reopen the mdot call",
                "cell trip never fired; 24.00 vs 80.00 kg/h floor",
                "H-1 and H-3 remain unskipped; H-2 is the only isolated header",
            ],
            "new_state": {"h2": "held", "h13": "in survey", "cell": "in service"},
            "latency_ms": 1800000.0,
        },
        "reward_components": reward(
            0.36,
            [
                ("skip_header_refusal", 0.14),
                ("h2_hold_stands", 0.10),
                ("massveil_nonsubstitution", 0.08),
                ("survey_floor_complete", 0.06),
                ("takt_cost", -0.02),
            ],
            "operational execution gate: refuse skip of unmeasured headers because Massveil is not a skip license; not an mdot re-vote",
        ),
        "meta": meta_common(tags=["REJECT", "operational-execution", "skip-refusal"]),
    }
    return {
        "id": "nelb-r52-159",
        "spike_events": events,
        "language_view": {
            "description": "Kelpfen Chlor-Alkali KF-4. Simulated thermal-mass capillary reconstructs 24.00 kg/h from 12.00 W / 2.00 K while Massveil still reports 6.40 kg/h. The gate ACCEPTs an H-2 isolate only. A 12 min survey floor is serialized in the stream. Companion t2 REJECTs skipping H-1 and H-3.",
            "trajectory": traj,
            "trajectory_skip_header_refusal": traj2,
        },
        "bridge_notes": {
            "channel_map": {
                "tmf.P / tmf.dT / tmf.snr": "capillary heater power, temperature rise, and SNR; the physics channels the reconstruction consumes",
                "recon.mdot / recon.cp": "serialized mdot kg/h and heat-balance identity",
                "massveil.mdot / hdr.id / h13.present": "vendor last-good orifice, header id, and adjacent-header presence; the denial and scope channels",
                "ops.prop / gate.comp / ops.skip / gate.hold": "accept-and-skip proposal, ACCEPT, skip proposal, companion REJECT",
                "surv.start / surv.floor / h2.held / h13.skip / cell.trip / hdr.held / takt.late": "operational companion channels plus the 12 min floor",
            },
            "temporal_motifs": [
                "vendor-green while plant-over: massveil.mdot 6.40 next to recon.mdot 24.00",
                "reconstruction as event: recon.mdot 24.00 equals 4.00*12.00/2.00",
                "ACCEPT then operational REJECT: gate.comp at 5400 s, gate.hold at 7800 s",
                "slow floor in-stream: surv.start 6000 s, surv.floor 6720 s (12.0 min)",
                "tight tmf pair: tmf.P then tmf.dT +1.5 ms at the raster frame",
            ],
            "language_to_spike_mapping": "'Massveil is 6.40 kg/h' = massveil.mdot 6.40; '24 kg/h' = recon.mdot 24.00; 'accept H-2 only' = gate.comp ACCEPT; 'do not skip H-1/H-3' = gate.hold REJECT",
            "why_high_value": "New thermal-mass-capillary family on a chlorine header (not CTA r31, not Coriolis r29/r34, not vortex-shedding r39, not clamp-on r18, not N-16 r24, not LFV r19). Lead bounded ACCEPT of H-2 isolate on a recomputable mdot that a vendor orifice last-good would have used to skip adjacent headers. Companion t2 is operational skip refusal. sim_or_real=simulated.",
            "encoder_spec": {
                "prng": "MT19937 via python random.Random",
                "seeds": {"raster": 202609159, "stream_note": "stream amplitudes are authored constants (W, K, kg/h, 1, bool)"},
                "draw_order": "raster: per neuron id order, gap-constrained times, per-spike adaptation and noise",
                "thinning": "thermal-mass heater exists at ~1 Hz; stream keeps 4 P points; recon keeps 4 of ~20 solver ticks",
                "refractory_floors_ms": {
                    "tmf.P": 1.5,
                    "tmf.dT": 1.5,
                    "tmf.snr": 1.5,
                    "recon.mdot": 60000,
                    "recon.cp": 60000,
                    "massveil.mdot": 60000,
                    "hdr.id": 60000,
                    "h13.present": 60000,
                    "ops.prop": 60000,
                    "gate.comp": 60000,
                    "surv.start": 60000,
                    "surv.floor": 60000,
                    "ops.skip": 60000,
                    "gate.hold": 60000,
                    "h2.held": 60000,
                    "h13.skip": 60000,
                    "cell.trip": 60000,
                    "hdr.held": 60000,
                    "takt.late": 60000,
                },
                "time_alias": "t_rel_ms; t0 = 2026-08-19T03:00:00Z simulated night start",
            },
            "distillation_targets": [
                "thermal-mass reconstruction head: mdot = k_t * P / dT; cp = P / (mdot * dT)",
                "bounded ACCEPT head: in-band mdot AND header scope AND h13-out-of-scope",
                "operational companion: refuse skip-isolate without re-opening the orifice call",
            ],
        },
        "reconstruction_model": {
            "name": "thermal_mass_capillary_chlorine",
            "formula": "mdot_kgh = k_t * P_W / dT_K; cp = P_W / (mdot_kgh * dT_K)",
            "parameters": {
                "k_t": 4.00,
                "dT_K": 2.00,
                "isolate_floor_kgh": 20.00,
                "cell_trip_kgh": 80.00,
                "surv_min": 12.0,
            },
            "worked_example": {"P_W": 12.00, "mdot_kgh": 24.00, "cp": 0.250},
            "check": "4.00 * 12.00 / 2.00 = 24.00 exactly; 12.00 / (24.00 * 2.00) = 0.250 exactly; 6000 s + 720 s = 6720 s = 12.0 min floor",
        },
        "raster": raster,
        "gate_snn": {
            "decision": "ACCEPT",
            "decision_window_ms": 36.0,
            "decision_window_s": 0.036,
            "code": "kf4.tmf_hdr_gate",
            "note": "ACCEPT accumulator wins: thermal-mass mdot evidence overpowers the Massveil skip advocate",
            "decode_rule": "accept if mdot_estimator AND dt_norm AND header_margin fire inside the window; vendor_skip_advocate is necessary-but-not-sufficient and cannot release H-1 and H-3",
            "populations": [
                gate_pop("mdot_estimator", 80, 1.5, 50.0, w_s),
                gate_pop("dt_norm", 64, 1.2, 31.25, w_s),
                gate_pop("header_margin", 40, 1.0, 50.0, w_s),
                gate_pop("vendor_skip_advocate", 32, 0.7, 25.0, w_s),
                gate_pop("accept_latch", 96, 1.8, 62.5, w_s),
            ],
        },
        "gate_compute": gate_compute(
            [
                {"check": "kf4.tmf_scorer", "neurons": 80, "mean_rate_hz": 50.0, "window_ms": 36.0},
                {"check": "kf4.mdot_scorer", "neurons": 40, "mean_rate_hz": 62.5, "window_ms": 32.0},
            ]
        ),
        "meta": meta_common(
            id="nelb-r52-159",
            clock_domain="kf4-tmf-sim-relative-ms-t0-2026-08-19T03:00:00Z",
            tags=["thermal-mass-capillary", "ACCEPT", "REJECT", "serialized-reconstruction", "operational-t2"],
        ),
    }
