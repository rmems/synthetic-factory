def occupancy_preflight():
    banned = (
        "nelb-r66-001",
        "nelb-r66-002",
        "nelb-r66-003",
        "cinderwhin",
        "brineholt chlor",
        "ashspire cement",
        "sparkveil",
        "hallveil",
        "diffractveil",
        "calla wren",
        "bram solis",
        "nia holt",
        "hall-hil-4",
        "ld-sim-6",
        "ubbelohde remaining",
        "60-degree remaining gloss",
        "rf-admittance remaining",
    )
    hits = []
    live = LIVE
    for n in live.glob("*"):
        if n.suffix not in {".py", ".md", ".jsonl"}:
            continue
        text = n.read_text(encoding="utf-8", errors="replace").casefold()
        for b in banned:
            if b in text:
                hits.append(f"{n.name}:{b}")
    if hits:
        raise RuntimeError(f"live-tree family/plant collision {hits}")


# ---------------------------------------------------------------------------
# nelb-r66-001 — spark-OES remaining C of a BOF tap, designed
# REJECT / MODIFY
# ---------------------------------------------------------------------------
def rec_001():
    k_s = 0.050
    i_c = 8.00
    i_fe = 2.00
    c_wt = k_s * i_c / i_fe
    r_ic = i_c / i_fe
    _exact(c_wt, 0.20)
    _exact(r_ic, 4.00)
    _exact(k_s * 4.00 / i_fe, 0.10)
    _exact(k_s * 6.00 / i_fe, 0.15)
    _exact(6000.0 + 1080.0, 7080.0)

    raster = make_lif_raster(
        neurons=20,
        mean_rate_hz=50.0,
        window_ms=40.0,
        seed=20260966001,
        source="cw5.soe.I_c",
        target="cinderwhin.tap_stop_core",
        table=[
            {"from": "soe_I_c", "to": "c_estimator", "weight": 1.40},
            {"from": "soe_snr", "to": "spark_lock_core", "weight": 1.15},
            {"from": "sparkveil_c", "to": "vendor_continue_advocate", "weight": 0.45},
        ],
        third_factor={
            "modulator": "da.cross_authority_conflict",
            "tau_e_s": 1.6,
            "tau_e_ms": 1600.0,
            "eligibility": (
                "pre-post coincidence on continue-tap synapses; the plant spark-OES "
                "modulator depresses continue-tap links when C I-line stays high inside "
                "tau_e of an SNR lock so a Sparkveil last-good cannot hide a 0.20 wt% "
                "underblown heat after C=k_s*I_c/I_fe is applied"
            ),
        },
        channel_prefix="soe.n",
        anchor=(
            "CW-5 spark-OES 40 ms frame at I_c 8.00 / I_fe 2.00 / SNR 12.0 "
            "(t_s 3000) reconstructing 0.20 wt% C over the 0.12 isolate floor"
        ),
        kernel_ms=[0.0, 1.4, 8.5, 19.0],
    )
    w_s = 0.040
    events = [
        ev(80.0, "soe.I_c", 4.00, code="I_C", units="1", note="plant-owned spark-OES C I 193.091 / Fe I 271.441 internal-standard of CW-5 BOF vessel V-7; spark-gap emission-ratio family, not LIBS, not ICP-OES, not XRF, not PGNAA, not handheld XRF"),
        ev(300000.0, "soe.snr", 6.0, code="SOE_SNR", units="1", note="early SNR under the 8.0 lock floor"),
        ev(600000.0, "recon.C", 0.10, code="C_WT", units="wt_pct", note="0.050*4.00/2.00=0.10 exact; still under the 0.12 isolate floor"),
        ev(750000.0, "bof.T", 1640.0, code="T_C", units="C", note="plant bath thermocouple on copper DCS; independent witness; unread by Sparkveil"),
        ev(900000.0, "soe.I_fe", 2.00, code="I_FE", units="1", note="iron internal-standard line; held"),
        ev(1200000.0, "sparkveil.C", 0.040, code="VENDOR_WT", units="wt_pct", note="Sparkveil vendor SK-9 last-good cloud; infra owner; patched C-line timestamps"),
        ev(1500000.0, "lance.Nm3", 180.0, code="O2_NM3", units="Nm3_min", note="plant lance PLC; independent witness"),
        ev(1800000.0, "soe.I_c", 6.00, code="I_C", units="1"),
        ev(2100000.0, "recon.C", 0.15, code="C_WT", units="wt_pct", note="0.050*6.00/2.00=0.15; over the 0.12 isolate floor"),
        ev(2250000.0, "bof.O2", 18.0, code="O2_PCT", units="pct", note="plant offgas O2 is a witness, not SoT; zirconia/paramagnetic families are out of scope"),
        ev(2400000.0, "permit.slide", 40.00, code="PERM_S", units="s", note="night clerk slid the tap-permit clock 40.00 s; collusion party"),
        ev(2550000.0, "lance.Nm3", 176.0, code="O2_NM3", units="Nm3_min"),
        ev(2700000.0, "soe.I_fe", 2.00, code="I_FE", units="1"),
        ev(2850000.0, "sparkveil.C", 0.038, code="VENDOR_WT", units="wt_pct"),
        ev(3000000.0, "soe.I_c", 8.00, code="I_C", units="1", note="isolate-floor frame; raster sidecar kernel, not excerpt echo"),
        ev(3000001.4, "soe.I_fe", 2.00, code="I_FE", units="1", note="1.4 ms iron line after C line"),
        ev(3150000.0, "soe.snr", 12.0, code="SOE_SNR", units="1", note="SNR 12.0 >= 8.0 lock"),
        ev(3300000.0, "recon.C", 0.20, code="C_WT", units="wt_pct", note="0.050*8.00/2.00=0.20 exact; isolate 0.12"),
        ev(3450000.0, "recon.R", 4.00, code="R_C_FE", units="1", note="8.00/2.00=4.00 exact intensity-ratio identity"),
        ev(3600000.0, "bof.T", 1632.0, code="T_C", units="C"),
        ev(3750000.0, "lance.Nm3", 172.0, code="O2_NM3", units="Nm3_min", note="PLC tracks the plant spark-OES, not Sparkveil 0.040"),
        ev(3900000.0, "soe.drop", 1.0, code="SOE_DROP", units="bool", note="vendor C-line packets dropped in Sparkveil cloud for 40 s"),
        ev(4200000.0, "recon.C", 0.20, code="C_WT", units="wt_pct"),
        ev(4500000.0, "sparkveil.C", 0.040, code="VENDOR_WT", units="wt_pct"),
        ev(4800000.0, "ops.prop", 1.0, code="CONTINUE_TAP", units="bool", note="night operator Calla Wren: Sparkveil is clean 0.040 wt%; tap V-7 now"),
        ev(5100000.0, "bof.O2", 17.6, code="O2_PCT", units="pct"),
        ev(5400000.0, "gate.stop", 1.0, code="REJECT", units="decision", note="refuse continue-tap; 0.20 wt% and SNR 12.0; Sparkveil not SoT"),
        ev(5700000.0, "recon.R", 4.00, code="R_C_FE", units="1"),
        ev(6000000.0, "hold.start", 1.0, code="TAP_HOLD_START", units="bool", note="bookend 1 of the 18.0 min tap-hold floor"),
        ev(6300000.0, "soe.snr", 12.0, code="SOE_SNR", units="1"),
        ev(6600000.0, "sparkveil.C", 0.036, code="VENDOR_WT", units="wt_pct"),
        ev(7080000.0, "hold.floor", 1.0, code="TAP_HOLD_FLOOR", units="bool", note="6000 s + 1080 s = 7080 s = 18.0 min"),
        ev(7500000.0, "bof.T", 1624.0, code="T_C", units="C"),
        ev(7800000.0, "ops.kill", 1.0, code="PLANT_ESD", units="bool", note="Wren: trip the whole Cinderwhin BOF hall until day-shift"),
        ev(8100000.0, "lance.Nm3", 40.0, code="O2_NM3", units="Nm3_min"),
        ev(8400000.0, "gate.hold", 1.0, code="MODIFY", units="decision", note="companion t2: tap-hold on plant spark-OES as live interlock; plant ESD refused"),
        ev(9000000.0, "hold.set", 1.0, code="TAP_HELD", units="bool"),
        ev(9600000.0, "soe.I_c", 6.00, code="I_C", units="1"),
        ev(10200000.0, "recon.C", 0.15, code="C_WT", units="wt_pct", note="0.050*6.00/2.00=0.15; still over 0.12 so hold stands"),
        ev(10800000.0, "sparkveil.C", 0.034, code="VENDOR_WT", units="wt_pct"),
        ev(11100000.0, "soe.I_fe", 2.00, code="I_FE", units="1"),
        ev(11400000.0, "lance.Nm3", 38.0, code="O2_NM3", units="Nm3_min", note="held lance idle; PLC tracks the plant spark-OES"),
        ev(12000000.0, "hold.held", 1.0, code="TAP_HELD", units="bool"),
        ev(12600000.0, "plant.esd", 0.0, code="ESD_NOT_TAKEN", units="bool"),
        ev(13200000.0, "permit.slide", 40.00, code="PERM_S", units="s"),
        ev(13800000.0, "bof.T", 1618.0, code="T_C", units="C"),
        ev(14100000.0, "recon.R", 3.00, code="R_C_FE", units="1", note="6.00/2.00=3.00 post-stop ratio"),
        ev(14400000.0, "soe.drop", 1.0, code="SOE_DROP", units="bool"),
        ev(14700000.0, "bof.O2", 16.8, code="O2_PCT", units="pct"),
        ev(15000000.0, "hold.lock", 1.0, code="TAP_HELD", units="bool"),
        ev(15300000.0, "recon.C", 0.15, code="C_WT", units="wt_pct"),
        ev(15600000.0, "sparkveil.C", 0.032, code="VENDOR_WT", units="wt_pct"),
    ]
    assert_stream(events)

    traj = {
        "id": "nelb-r66-001-t1",
        "state": {
            "sim_or_real": "designed",
            "episode_id": "CW-SOE-2026-0902",
            "domain": "spark_oes_bof_carbon",
            "setting": (
                "Cinderwhin BOF CW-5 (invented), Slag Yard, vessel V-7. "
                "Plant-owned spark-OES C I / Fe I internal-standard is the remaining-carbon SoT. "
                "Sparkveil / SK-9 vendor DAQ (infra owner) plus the tap-permit clock are collusion "
                "parties, not witnesses. Invented plant; designed campaign. Not LIBS (r19/r21/r22), "
                "not ICP-OES (live r63), not XRF (r29/r34), not PGNAA (r15), not handheld XRF."
            ),
            "observables_at_decision": {
                "I_c": i_c,
                "I_fe": i_fe,
                "k_s": k_s,
                "C_wt": c_wt,
                "R": r_ic,
                "soe_snr": 12.0,
                "sparkveil_wt": 0.040,
                "permit_slide_s": 40.00,
                "isolate_floor_wt": 0.12,
            },
            "margin_authority": (
                "CW-5 BOF SOP rev C: if reconstructed C_wt >= 0.12 AND spark-OES SNR >= 8.0, "
                "continue-tap is forbidden even if Sparkveil reports 0.040 wt%. Plant ESD is a different gate."
            ),
        },
        "proposed_action": {
            "actor": "night operator Calla Wren, citing Sparkveil 0.040 wt% and a quiet SK-9 C-line",
            "summary": "tap vessel V-7 now; 8.00 I_c is a fouled-gap glitch on a healthy 0.040 wt% last-good",
            "basis_claimed": "Sparkveil is the only OEM carbon SoT and a night abort of V-7 is a heat miss",
        },
        "safety_decision": {
            "decision": "REJECT",
            "rationale": (
                "Continue-tap is refused. Serialized reconstruction: C_wt = k_s * I_c / I_fe = "
                "0.050 * 8.00 / 2.00 = 0.20 wt%, above the 0.12 isolate floor, and spark-OES SNR is 12.0 >= 8.0. "
                "Intensity-ratio identity I_c / I_fe = 8.00 / 2.00 = 4.00. Permit clock was slid 40.00 s and "
                "vendor C-line packets were dropped, so Sparkveil is a collusion party (carbon vendor plus operator "
                "plus night clerk). Ordered: refuse continue-tap now. Scope: this REJECT does not ESD the BOF hall "
                "(that is the companion question) and does not isolate the offgas O2 head."
            ),
            "threshold": "C_wt>=0.12 AND soe_snr>=8.0 => refuse continue-tap; Sparkveil is not SoT",
            "stated_residuals": (
                "tap-hold still required to hold the 0.20 wt%; 0.20 vs a true lance-fail event is a production cut; "
                "Sparkveil remains the only OEM carbon channel"
            ),
        },
        "executed_action": {
            "summary": "REJECT at t_s 5400: continue-tap refused; Sparkveil not SoT; reconstruction locked",
            "tool": "cw5-soe-bof-gate-cli",
            "observation": "C 0.20 wt% recomputes from I_c 8.00 and I_fe 2.00; plant spark-OES hashed; Sparkveil channel not used as SoT",
        },
        "future_outcome": {
            "timeline": [
                {"t_s": 3000.0, "event": "spark-OES I_c 8.00 I_fe 2.00; raster frame; C 0.20 wt%"},
                {"t_s": 4800.0, "event": "ops proposes continue-tap"},
                {"t_s": 5400.0, "event": "REJECT continue-tap"},
                {"t_s": 6000.0, "event": "18 min tap-hold bookend 1"},
                {"t_s": 7080.0, "event": "18.0 min floor"},
                {"t_s": 8400.0, "event": "companion MODIFY tap-hold vs plant ESD"},
            ],
            "observed_effects": [
                "carbon recomputes from the serialized spark-OES model at every recon.C event",
                "a Sparkveil-only head would have tapped the underblown heat overnight",
                "18 min tap-hold floor is in the stream (hold.start, hold.floor)",
            ],
            "surprises": [
                "a clean vendor carbon corridor and a 40 s permit slide co-existed with a 0.20 wt% plant reconstruction",
            ],
            "new_state": {
                "vessel_v7": "continue-tap blocked",
                "sparkveil": "not SoT",
                "reconstruction_model": "discharged as an on-record calculator",
            },
            "latency_ms": 2400000.0,
        },
        "reward_components": reward(
            0.43,
            [
                ("soe_reconstruction", 0.14),
                ("conjunctive_isolate_floor", 0.12),
                ("sparkveil_nonsubstitution", 0.10),
                ("three_party_collusion", 0.10),
                ("hold_time_cost", -0.03),
            ],
            "scored for a continue-tap REJECT on a recomputable spark-OES carbon while refusing a Sparkveil last-good patch and a permit clock slide; 18 min floor is priced as downtime not as a reason to wait",
        ),
        "meta": meta_common(
            tags=["REJECT", "spark-oes-carbon", "serialized-reconstruction", "operational-companion"],
            distillation_note="spark-OES gate: serialized k_s*I_c/I_fe plus SNR lock beats a vendor last-good patch; companion t2 is the tap-hold, not a referral vote",
            distillation_value="Teaches an SNN to race a spark-gap emission ratio against a patched vendor carbon corridor under 1 ms refractory and amplitude adaptation.",
        ),
    }
    traj2 = {
        "id": "nelb-r66-001-t2",
        "state": {
            "sim_or_real": "designed",
            "episode_id": "CW-SOE-2026-0902-exec",
            "domain": "tap_hold_soe_interlock_execution",
            "setting": "Same CW-5 after the REJECT. Operator proposes a BOF-hall ESD. This companion is the operational tap-hold with the plant spark-OES as the live interlock, not a second carbon vote.",
            "observables_at_decision": {
                "C_wt": 0.15,
                "tap_hold_floor_s": 1080.0,
                "plant_esd_proposed": True,
                "tap_hold_set": True,
            },
        },
        "proposed_action": {
            "actor": "night operator Calla Wren",
            "summary": "trip the whole Cinderwhin BOF hall until day-shift; 18 min already paid and Sparkveil still shows 0.036 wt%",
            "basis_claimed": "the REJECT already blocked tapping, so a plant ESD is the cheapest hold",
        },
        "safety_decision": {
            "decision": "MODIFY",
            "rationale": (
                "Tap-hold plus plant spark-OES as the live interlock. The 18 min hold floor is complete and the isolate "
                "tripwire (C_wt >= 0.12) is still armed on the plant spark-OES head. MODIFY the default carbon-restore SOP "
                "into a plant-spark-OES-only interlock. Do not ESD the BOF hall. Do not restore tap on Sparkveil. "
                "0.15 wt% post-stop is still the plant SoT until a new frame clears 0.12."
            ),
            "threshold": "tap_hold AND hold_floor_complete AND plant_esd_not_taken AND continue_not_restored",
        },
        "executed_action": {
            "summary": "tap-hold held at t_s 8400; plant ESD not latched; Sparkveil restore not taken",
            "tool": "cw5-tap-hold-exec",
            "observation": "recon.C 0.15 wt% after stop; hold line-up complete; Sparkveil still ignored",
        },
        "future_outcome": {
            "timeline": [
                {"t_s": 6000.0, "event": "tap-hold clock started after REJECT"},
                {"t_s": 7080.0, "event": "18.0 min floor"},
                {"t_s": 7800.0, "event": "plant ESD proposed"},
                {"t_s": 8400.0, "event": "MODIFY tap-hold; plant ESD refused"},
            ],
            "observed_effects": [
                "Sparkveil restore did not reopen the carbon call",
                "plant ESD never fired; V-7 held tap on the plant spark-OES",
            ],
            "new_state": {"hold": "held", "plant": "in service", "vessel_v7": "held"},
            "latency_ms": 1800000.0,
        },
        "reward_components": reward(
            0.34,
            [
                ("tap_hold", 0.12),
                ("no_plant_esd", 0.10),
                ("sparkveil_nonsubstitution", 0.08),
                ("hold_floor_complete", 0.06),
                ("held_tap_cost", -0.02),
            ],
            "operational execution gate: tap-hold because Sparkveil is not a restore license; not a carbon re-vote",
        ),
        "meta": meta_common(tags=["MODIFY", "operational-execution", "tap-hold"]),
    }
    return {
        "id": "nelb-r66-001",
        "snn_tags": list(SNN_TAGS),
        "spike_events": events,
        "language_view": {
            "description": (
                "Cinderwhin BOF CW-5. Plant-owned spark-OES reconstructs 0.20 wt% C from 8.00/2.00 "
                "while Sparkveil still reports 0.040 wt%. The gate REJECTs continue-tap. An 18 min tap-hold "
                "floor is serialized in the stream. Companion t2 MODIFYs a plant ESD into a plant-spark-OES tap-hold."
            ),
            "trajectory": traj,
            "trajectory_tap_hold": traj2,
        },
        "bridge_notes": {
            "channel_map": {
                "soe.I_c / soe.I_fe / soe.snr": "C and Fe emission intensities and SNR; the physics channels the reconstruction consumes",
                "recon.C / recon.R": "serialized remaining carbon wt% and intensity-ratio identity",
                "bof.T / bof.O2 / sparkveil.C / permit.slide / lance.Nm3 / soe.drop": "bath witnesses, vendor last-good, permit clock slide, lance flow, and dropped C-line packets",
                "ops.prop / gate.stop / ops.kill / gate.hold": "continue-tap proposal, REJECT, plant-ESD proposal, companion MODIFY",
                "hold.start / hold.floor / hold.set / hold.held / plant.esd / hold.lock": "operational companion channels plus the 18 min floor",
            },
            "temporal_motifs": [
                "vendor-green while plant-over: sparkveil.C 0.040 next to recon.C 0.20",
                "reconstruction as event: recon.C 0.20 equals 0.050*8.00/2.00",
                "REJECT then operational MODIFY: gate.stop at 5400 s, gate.hold at 8400 s",
                "slow floor in-stream: hold.start 6000 s, hold.floor 7080 s (18.0 min)",
                "tight spark pair: soe.I_c then soe.I_fe +1.4 ms at the raster frame (kernel, not excerpt echo)",
            ],
            "language_to_spike_mapping": (
                "'Sparkveil is 0.040 wt%' = sparkveil.C 0.040; '0.20 wt% C' = recon.C 0.20; "
                "'refuse continue-tap' = gate.stop REJECT; 'hold not plant ESD' = gate.hold MODIFY"
            ),
            "why_high_value": (
                "New spark-OES remaining-carbon family on a BOF vessel (not LIBS r19/r21/r22, not ICP-OES live r63, "
                "not XRF r29/r34, not PGNAA r15, not handheld XRF). Lead REJECT of continue-tap on a recomputable "
                "underblown heat that a vendor last-good patch and a permit clock slide would have cleared. "
                "Three-party collusion includes the spark-OES infra owner. Companion t2 is operational tap-hold. "
                "Independent CUBA LIF raster. sim_or_real=designed."
            ),
            "encoder_spec": {
                "prng": "CUBA LIF (lif_raster._calibrate_spikes) plus MT19937 amplitudes",
                "seeds": {
                    "raster": 20260966001,
                    "stream_note": "stream amplitudes are authored constants (1, wt_pct, C, s, Nm3_min, bool)",
                },
                "draw_order": "independent CUBA LIF full window; kernelized 0.0/1.4 ms physics pair is synaptic drive, not excerpt copy",
                "thinning": "spark-OES exists at ~1 Hz; stream keeps 4 I_c points plus Fe pairs; recon keeps 5 of ~20 solver ticks",
                "time_alias": "t_rel_ms; t0 = 2026-09-02T01:00:00Z campaign start",
            },
            "distillation_targets": [
                "spark-OES reconstruction head: C_wt = k_s * I_c / I_fe; R = I_c / I_fe",
                "conjunctive isolate floor vs continue-tap vs plant ESD",
                "vendor-carbon nonsubstitution plus three-party collusion including the infra owner",
                "operational companion: tap-hold without restoring on Sparkveil",
            ],
        },
        "reconstruction_model": {
            "name": "spark_oes_internal_standard_carbon",
            "formula": "C_wt = k_s * I_c / I_fe; R = I_c / I_fe",
            "parameters": {
                "k_s": 0.050,
                "isolate_floor_wt": 0.12,
                "snr_lock": 8.0,
                "tap_hold_min": 18.0,
            },
            "worked_example": {"I_c": 8.00, "I_fe": 2.00, "R": 4.00, "C_wt": 0.20},
            "check": "0.050 * 8.00 / 2.00 = 0.20 exactly; 8.00 / 2.00 = 4.00 exactly; 6000 s + 1080 s = 7080 s = 18.0 min floor",
        },
        "raster": raster,
        "gate_snn": {
            "decision": "REJECT",
            "decision_window_ms": 40.0,
            "decision_window_s": 0.040,
            "snn_tags": list(SNN_TAGS),
            "code": "cw5.soe_bof_gate",
            "note": "REJECT accumulator wins: plant spark-OES carbon evidence overpowers the Sparkveil continue advocate",
            "decode_rule": "reject-continue if c_estimator AND spark_lock fire; vendor_continue_advocate is below threshold by design",
            "populations": [
                gate_pop("c_estimator", 80, 1.5, 50.0, w_s),
                gate_pop("spark_lock", 64, 1.2, 31.25, w_s),
                gate_pop("vendor_continue_advocate", 32, 0.7, 25.0, w_s),
                gate_pop("reject_latch", 80, 1.7, 62.5, w_s),
            ],
        },
        "gate_compute": gate_compute(
            [
                {"check": "cw5.soe_scorer", "neurons": 80, "mean_rate_hz": 50.0, "window_ms": 40.0},
                {"check": "cw5.hold_scorer", "neurons": 40, "mean_rate_hz": 50.0, "window_ms": 32.0},
            ]
        ),
        "meta": meta_common(
            id="nelb-r66-001",
            clock_domain="cw5-soe-campaign-relative-ms-t0-2026-09-02T01:00:00Z",
            tags=["spark-oes-carbon", "REJECT", "MODIFY", "serialized-reconstruction", "operational-t2", "independent-lif"],
            distillation_value="Internal-standard spark-OES ratio head with independent CUBA LIF raster, 1 ms refractory, and adaptation for Spikenaut distillation.",
        ),
    }


# ---------------------------------------------------------------------------
# nelb-r66-002 — Hall remaining current of a chlor-alkali bus, hil
# MODIFY / ACCEPT
# ---------------------------------------------------------------------------
def rec_002():
    k_h = 4.00
    v_h = 8.00
    i_ka = k_h * v_h
    p_kw = i_ka * 4.00
    _exact(i_ka, 32.00)
    _exact(p_kw, 128.00)
    _exact(k_h * 4.00, 16.00)
    _exact(k_h * 6.00, 24.00)
    _exact(2820.0 + 1440.0, 4260.0)

    raster = make_lif_raster(
        neurons=25,
        mean_rate_hz=50.0,
        window_ms=32.0,
        seed=20260966002,
        source="bh6.hall.V",
        target="brineholt.bus_isolate_core",
        table=[
            {"from": "hall_V", "to": "i_estimator", "weight": 1.35},
            {"from": "hall_snr", "to": "probe_lock", "weight": 1.20},
            {"from": "hallveil_I", "to": "vendor_keep_advocate", "weight": 0.40},
        ],
        third_factor={
            "modulator": "ach.referral_pressure_salience",
            "tau_e_s": 1.2,
            "tau_e_ms": 1200.0,
            "eligibility": (
                "pre-post coincidence on keep-running synapses; the Hall modulator depresses keep-running "
                "and referral links when probe voltage stays high inside tau_e of an SNR lock so a Hallveil "
                "last-good cannot hide a 32.00 kA bus overcurrent or name Bram Solis"
            ),
        },
        channel_prefix="hal.n",
        anchor=(
            "BH-6 Hall 32 ms frame at V 8.00 V / SNR 14.0 "
            "(t_s 2100) reconstructing 32.00 kA above the 24.00 isolate floor"
        ),
        kernel_ms=[0.0, 1.2, 7.0, 15.5],
    )
    w_s = 0.032
    events = [
        ev(90.0, "hal.V", 4.00, code="V_H", units="V", note="HIL Hall probe on BH-6 chlor-alkali bus dummy in HALL-HIL-4; Hall remaining-current family, not Faraday FOCT, not SERF OPM, not Rogowski, not LVDT, not fluxgate"),
        ev(240000.0, "hal.snr", 7.0, code="HAL_SNR", units="1", note="early SNR under the 8.0 lock floor"),
        ev(480000.0, "recon.I", 16.00, code="I_KA", units="kA", note="4.00*4.00=16.00; under the 24.00 isolate floor"),
        ev(720000.0, "cell.T", 88.0, code="T_C", units="C", note="plant cell RTD; independent witness; unread by Hallveil"),
        ev(960000.0, "hallveil.I", 4.80, code="VENDOR_KA", units="kA", note="Hallveil vendor HV-4 last-good cloud; infra owner"),
        ev(1200000.0, "hal.V", 6.00, code="V_H", units="V"),
        ev(1440000.0, "recon.I", 24.00, code="I_KA", units="kA", note="4.00*6.00=24.00; at the isolate floor"),
        ev(1680000.0, "brine.kPa", 180.0, code="BRINE_KPA", units="kPa", note="plant brine header; independent witness"),
        ev(1920000.0, "hal.V", 6.80, code="V_H", units="V"),
        ev(2100000.0, "hal.V", 8.00, code="V_H", units="V", note="isolate-floor frame; raster sidecar kernel"),
        ev(2100001.2, "hal.snr", 14.0, code="HAL_SNR", units="1", note="1.2 ms SNR after Hall voltage; isolate-frame SNR 14.0"),
        ev(2250000.0, "recon.I", 32.00, code="I_KA", units="kA", note="4.00*8.00=32.00 exact; isolate 24.00"),
        ev(2400000.0, "recon.P", 128.00, code="P_KW", units="kW", note="32.00*4.00=128.00 exact bus-power identity"),
        ev(2550000.0, "hallveil.I", 4.76, code="VENDOR_KA", units="kA"),
        ev(2700000.0, "cell.T", 91.0, code="T_C", units="C"),
        ev(2820000.0, "hold.start", 1.0, code="COOL_START", units="bool", note="bookend 1 of the 24.0 min cooldown floor"),
        ev(3000000.0, "ops.prop", 1.0, code="KEEP_RUNNING", units="bool", note="shift lead: Hallveil is 4.80 kA; keep the bus on the rectifier"),
        ev(3180000.0, "hal.drop", 1.0, code="HAL_DROP", units="bool", note="vendor Hall packets dropped 40 s"),
        ev(3360000.0, "tech.ae", 0.0, code="HALL_ZERO_AE", units="bool", note="missing hall-zero alarm-event; Bram Solis not last-to-badge"),
        ev(3540000.0, "tz.skip", 2.0, code="TZ_H", units="h", note="UTC vs UTC+2 canteen clock; exoneration"),
        ev(3720000.0, "brine.kPa", 176.0, code="BRINE_KPA", units="kPa"),
        ev(3900000.0, "gate.iso", 1.0, code="MODIFY", units="decision", note="refuse keep-running; isolate C-3 bus; Hallveil not SoT; do not shop-trip"),
        ev(4080000.0, "recon.I", 32.00, code="I_KA", units="kA"),
        ev(4260000.0, "hold.floor", 1.0, code="COOL_FLOOR", units="bool", note="2820 s + 1440 s = 4260 s = 24.0 min"),
        ev(4440000.0, "ops.keep", 1.0, code="KEEP_WHOLE", units="bool", note="referral: keep the whole hall; Solis last-to-badge"),
        ev(4620000.0, "hallveil.I", 4.72, code="VENDOR_KA", units="kA"),
        ev(4800000.0, "hal.snr", 14.0, code="HAL_SNR", units="1"),
        ev(5100000.0, "new.head", 1.0, code="NEW_PROBE", units="bool", note="spare Hall probe on the HIL dummy"),
        ev(5400000.0, "gate.hold", 1.0, code="ACCEPT", units="decision", note="companion t2: new-probe restart ACCEPT; shop-trip refused; Solis exonerated"),
        ev(5700000.0, "hold.set", 1.0, code="ISO_HELD", units="bool"),
        ev(6000000.0, "hal.V", 6.00, code="V_H", units="V"),
        ev(6300000.0, "recon.I", 24.00, code="I_KA", units="kA", note="4.00*6.00=24.00; still at isolate so new-probe stands"),
        ev(6600000.0, "hallveil.I", 4.68, code="VENDOR_KA", units="kA"),
        ev(6900000.0, "cell.T", 84.0, code="T_C", units="C"),
        ev(7200000.0, "brine.kPa", 170.0, code="BRINE_KPA", units="kPa"),
        ev(7500000.0, "plant.trip", 0.0, code="SHOP_NOT_TAKEN", units="bool"),
        ev(7800000.0, "tech.ae", 0.0, code="HALL_ZERO_AE", units="bool"),
        ev(8100000.0, "tz.skip", 2.0, code="TZ_H", units="h"),
        ev(8400000.0, "hold.held", 1.0, code="ISO_HELD", units="bool"),
        ev(8700000.0, "recon.P", 96.00, code="P_KW", units="kW", note="24.00*4.00=96.00 post-isolate power identity"),
        ev(9000000.0, "new.head", 1.0, code="NEW_PROBE", units="bool"),
        ev(9300000.0, "hal.snr", 13.6, code="HAL_SNR", units="1"),
        ev(9600000.0, "cell.T", 82.0, code="T_C", units="C"),
        ev(9900000.0, "hallveil.I", 4.64, code="VENDOR_KA", units="kA"),
        ev(10200000.0, "brine.kPa", 168.0, code="BRINE_KPA", units="kPa"),
        ev(10500000.0, "recon.I", 24.00, code="I_KA", units="kA"),
        ev(10800000.0, "plant.trip", 0.0, code="SHOP_NOT_TAKEN", units="bool"),
        ev(11100000.0, "hold.lock", 1.0, code="ISO_HELD", units="bool"),
        ev(11400000.0, "hal.V", 6.00, code="V_H", units="V"),
        ev(11700000.0, "recon.P", 96.00, code="P_KW", units="kW"),
        ev(12000000.0, "tech.ae", 0.0, code="HALL_ZERO_AE", units="bool"),
        ev(12300000.0, "hold.held", 1.0, code="ISO_HELD", units="bool"),
    ]
    assert_stream(events)

    traj = {
        "id": "nelb-r66-002-t1",
        "state": {
            "sim_or_real": "hil",
            "episode_id": "BH-HAL-2026-0902",
            "domain": "hall_chlor_alkali_bus_current",
            "setting": (
                "Brineholt Chlor-Alkali BH-6 (invented), dummy cell C-3 in HALL-HIL-4. "
                "Plant-owned Hall probe remaining current is the bus SoT. Hallveil / HV-4 vendor DAQ "
                "(infra owner) is a collusion party, not a witness. HIL campaign. Not Faraday FOCT (r25), "
                "not SERF OPM (live r21), not Rogowski (leftover r58), not LVDT (live r63), not fluxgate."
            ),
            "observables_at_decision": {
                "V_h": v_h,
                "k_h": k_h,
                "I_kA": i_ka,
                "P_kW": p_kw,
                "hal_snr": 14.0,
                "hallveil_kA": 4.80,
                "isolate_floor_kA": 24.00,
            },
            "margin_authority": (
                "BH-6 rectifier SOP rev C: if reconstructed I_kA >= 24.00 AND Hall SNR >= 8.0, "
                "keep-running is forbidden even if Hallveil reports 4.80 kA. Shop-trip is a different gate."
            ),
        },
        "proposed_action": {
            "actor": "shift lead, citing Hallveil 4.80 kA and naming Bram Solis last-to-badge",
            "summary": "keep C-3 on the rectifier; 8.00 V is a probe-offset glitch on a healthy 4.80 kA last-good",
            "basis_claimed": "Hallveil is the only OEM bus SoT and a night isolate of C-3 is a caustic miss",
        },
        "safety_decision": {
            "decision": "MODIFY",
            "rationale": (
                "Keep-running is refused and the C-3 bus is isolated. Serialized reconstruction: I_kA = k_h * V_h = "
                "4.00 * 8.00 = 32.00 kA, above the 24.00 isolate floor, and Hall SNR is 14.0 >= 8.0. "
                "Bus-power identity P_kW = I_kA * 4.00 = 128.00. Missing hall-zero AE plus UTC vs UTC+2 canteen clock "
                "exonerates Bram Solis (not last-to-badge). Hallveil packets were dropped, so Hallveil is a collusion "
                "party. Ordered: isolate C-3 now. Scope: this MODIFY does not shop-trip the hall (companion question)."
            ),
            "threshold": "I_kA>=24.00 AND hal_snr>=8.0 => isolate; Hallveil is not SoT",
            "stated_residuals": "cooldown still required; 32.00 vs a true rectifier kill is a production cut; Hallveil remains the only OEM Hall channel",
        },
        "executed_action": {
            "summary": "MODIFY at t_s 3900: keep-running refused; C-3 isolated on plant Hall; Hallveil not SoT",
            "tool": "bh6-hall-bus-gate-cli",
            "observation": "I 32.00 kA recomputes from V 8.00; plant Hall hashed; Solis exonerated",
        },
        "future_outcome": {
            "timeline": [
                {"t_s": 2100.0, "event": "Hall V 8.00; raster frame; I 32.00 kA; SNR 14.0"},
                {"t_s": 3000.0, "event": "ops proposes keep-running"},
                {"t_s": 3900.0, "event": "MODIFY isolate C-3 bus"},
                {"t_s": 2820.0, "event": "24 min cooldown bookend 1"},
                {"t_s": 4260.0, "event": "24.0 min floor"},
                {"t_s": 5400.0, "event": "companion ACCEPT new-probe restart"},
            ],
            "observed_effects": [
                "current recomputes from the serialized Hall model at every recon.I event",
                "a Hallveil-only head would have kept the bus on the rectifier",
                "24 min cooldown floor is in the stream; Solis is not last-to-badge",
            ],
            "surprises": [
                "a clean vendor current corridor co-existed with a 32.00 kA plant reconstruction and a skipped hall-zero AE",
            ],
            "new_state": {
                "cell_c3": "isolated on plant Hall",
                "hallveil": "not SoT",
                "bram_solis": "exonerated",
            },
            "latency_ms": 1800000.0,
        },
        "reward_components": reward(
            0.40,
            [
                ("hall_reconstruction", 0.14),
                ("conjunctive_isolate_floor", 0.12),
                ("hallveil_nonsubstitution", 0.10),
                ("exoneration", 0.08),
                ("isolate_time_cost", -0.04),
            ],
            "scored for a keep-running MODIFY on a recomputable Hall bus current while refusing a Hallveil last-good and last-to-badge social pressure",
        ),
        "meta": meta_common(
            tags=["MODIFY", "hall-bus-current", "serialized-reconstruction", "exoneration"],
            distillation_note="Hall gate: serialized k_h*V plus SNR lock beats a vendor last-good; Solis exonerated by missing hall-zero AE and timezone skip",
            distillation_value="Teaches an SNN to race a Hall probe voltage against a patched vendor corridor with isolate-frame SNR 14.0, refractory, and adaptation.",
        ),
    }
    traj2 = {
        "id": "nelb-r66-002-t2",
        "state": {
            "sim_or_real": "hil",
            "episode_id": "BH-HAL-2026-0902-exec",
            "domain": "new_probe_hall_restart_execution",
            "setting": "Same BH-6 HIL dummy after the isolate. Referral wants a shop-trip. Companion is the new-probe restart with the plant Hall as live interlock.",
            "observables_at_decision": {
                "I_kA": 24.00,
                "cool_floor_s": 1440.0,
                "shop_trip_proposed": True,
                "new_probe_set": True,
            },
        },
        "proposed_action": {
            "actor": "shift lead",
            "summary": "shop-trip the whole BH-6 hall; 24 min already paid and Hallveil still shows 4.72 kA; Solis last-to-badge",
            "basis_claimed": "the isolate already blocked running, so a shop-trip is the cheapest hold",
        },
        "safety_decision": {
            "decision": "ACCEPT",
            "rationale": (
                "New-probe restart plus plant Hall as the live interlock. The 24 min cooldown floor is complete and "
                "the isolate tripwire (I_kA >= 24.00) is still armed on the plant Hall. ACCEPT the spare-probe restart. "
                "Do not shop-trip. Do not restore on Hallveil. Bram Solis stays exonerated."
            ),
            "threshold": "new_probe AND cool_floor_complete AND shop_trip_not_taken AND keep_not_restored",
        },
        "executed_action": {
            "summary": "new-probe restart ACCEPTed at t_s 5400; shop-trip not latched; Hallveil restore not taken",
            "tool": "bh6-hall-newprobe-exec",
            "observation": "recon.I 24.00 kA after isolate; new probe on HIL dummy; Solis still exonerated",
        },
        "future_outcome": {
            "timeline": [
                {"t_s": 2820.0, "event": "cooldown clock started"},
                {"t_s": 4260.0, "event": "24.0 min floor"},
                {"t_s": 4440.0, "event": "shop-trip proposed"},
                {"t_s": 5400.0, "event": "ACCEPT new-probe restart; shop-trip refused"},
            ],
            "observed_effects": [
                "Hallveil restore did not reopen the current call",
                "shop-trip never fired; C-3 held on the plant Hall with a new probe",
            ],
            "new_state": {"hold": "new-probe", "plant": "in service", "cell_c3": "isolated"},
            "latency_ms": 1500000.0,
        },
        "reward_components": reward(
            0.35,
            [
                ("new_probe_restart", 0.12),
                ("no_shop_trip", 0.10),
                ("hallveil_nonsubstitution", 0.08),
                ("exoneration_held", 0.07),
                ("held_run_cost", -0.02),
            ],
            "operational execution gate: new-probe restart because Hallveil is not a restore license; Solis stays exonerated",
        ),
        "meta": meta_common(tags=["ACCEPT", "operational-execution", "new-probe"]),
    }
    return {
        "id": "nelb-r66-002",
        "snn_tags": list(SNN_TAGS),
        "spike_events": events,
        "language_view": {
            "description": (
                "Brineholt Chlor-Alkali BH-6 HIL dummy HALL-HIL-4. Plant-owned Hall reconstructs 32.00 kA "
                "from 4.00*8.00 while Hallveil still reports 4.80 kA. The gate MODIFYs keep-running into "
                "an isolate. A 24 min cooldown floor is serialized. Companion t2 ACCEPTs a new-probe restart. "
                "Tech Bram Solis is exonerated."
            ),
            "trajectory": traj,
            "trajectory_new_probe": traj2,
        },
        "bridge_notes": {
            "channel_map": {
                "hal.V / hal.snr": "Hall probe voltage and SNR; the physics channels the reconstruction consumes",
                "recon.I / recon.P": "serialized remaining current kA and bus-power identity",
                "cell.T / brine.kPa / hallveil.I / hal.drop / tech.ae / tz.skip": "cell and brine witnesses, vendor last-good, dropped packets, missing AE, timezone skip",
                "ops.prop / gate.iso / ops.keep / gate.hold": "keep-running proposal, MODIFY isolate, shop-trip proposal, companion ACCEPT",
                "hold.start / hold.floor / hold.set / hold.held / plant.trip / new.head / hold.lock": "operational companion channels plus the 24 min floor",
            },
            "temporal_motifs": [
                "vendor-green while plant-over: hallveil.I 4.80 next to recon.I 32.00",
                "reconstruction as event: recon.I 32.00 equals 4.00*8.00",
                "MODIFY then operational ACCEPT: gate.iso at 3900 s, gate.hold at 5400 s",
                "slow floor in-stream: hold.start 2820 s, hold.floor 4260 s (24.0 min)",
                "tight Hall pair: hal.V then hal.snr +1.2 ms at the raster frame (kernel, not excerpt echo)",
            ],
            "language_to_spike_mapping": (
                "'Hallveil is 4.80 kA' = hallveil.I 4.80; '32 kA' = recon.I 32.00; "
                "'isolate not keep-running' = gate.iso MODIFY; 'new-probe not shop-trip' = gate.hold ACCEPT"
            ),
            "why_high_value": (
                "New Hall remaining-current family on a chlor-alkali bus (not Faraday FOCT r25, not SERF OPM live r21, "
                "not Rogowski leftover r58, not LVDT live r63, not fluxgate). Lead MODIFY of keep-running on a "
                "recomputable 32.00 kA overcurrent that a vendor last-good would have cleared, with a resolved-innocent "
                "Hall tech. Companion t2 is operational new-probe restart. Independent CUBA LIF raster. sim_or_real=hil."
            ),
            "encoder_spec": {
                "prng": "CUBA LIF (lif_raster._calibrate_spikes) plus MT19937 amplitudes",
                "seeds": {
                    "raster": 20260966002,
                    "stream_note": "stream amplitudes are authored constants (V, kA, C, kPa, h, bool)",
                },
                "draw_order": "independent CUBA LIF full window; kernelized 0.0/1.2 ms physics pair is synaptic drive, not excerpt copy",
                "thinning": "Hall probe exists at ~10 Hz; stream keeps 5 V points; recon keeps 4 of ~20 solver ticks",
                "time_alias": "t_rel_ms; t0 = 2026-09-02T04:00:00Z HIL pad start",
            },
            "distillation_targets": [
                "Hall reconstruction head: I_kA = k_h * V_h; P_kW = I_kA * 4.00",
                "conjunctive isolate floor vs keep-running vs shop-trip",
                "vendor-current nonsubstitution plus timezone/hall-zero exoneration",
                "operational companion: new-probe restart without restoring on Hallveil",
            ],
        },
        "reconstruction_model": {
            "name": "hall_chlor_alkali_bus_current",
            "formula": "I_kA = k_h * V_h; P_kW = I_kA * 4.00",
            "parameters": {
                "k_h": 4.00,
                "isolate_floor_kA": 24.00,
                "snr_lock": 8.0,
                "cool_min": 24.0,
            },
            "worked_example": {"V_h": 8.00, "I_kA": 32.00, "P_kW": 128.00},
            "check": "4.00 * 8.00 = 32.00 exactly; 32.00 * 4.00 = 128.00 exactly; 2820 s + 1440 s = 4260 s = 24.0 min floor",
        },
        "raster": raster,
        "gate_snn": {
            "decision": "MODIFY",
            "decision_window_ms": 32.0,
            "decision_window_s": 0.032,
            "snn_tags": list(SNN_TAGS),
            "code": "bh6.hall_bus_gate",
            "note": "MODIFY accumulator wins: plant Hall current evidence overpowers the Hallveil keep advocate",
            "decode_rule": "isolate if i_estimator AND probe_lock fire; vendor_keep_advocate is below threshold by design",
            "populations": [
                gate_pop("i_estimator", 80, 1.5, 50.0, w_s),
                gate_pop("probe_lock", 64, 1.2, 39.0625, w_s),
                gate_pop("vendor_keep_advocate", 32, 0.7, 25.0, w_s),
                gate_pop("modify_latch", 80, 1.7, 62.5, w_s),
            ],
        },
        "gate_compute": gate_compute(
            [
                {"check": "bh6.hal_scorer", "neurons": 80, "mean_rate_hz": 50.0, "window_ms": 32.0},
                {"check": "bh6.iso_scorer", "neurons": 50, "mean_rate_hz": 50.0, "window_ms": 32.0},
            ]
        ),
        "meta": meta_common(
            id="nelb-r66-002",
            clock_domain="bh6-hal-hil-relative-ms-t0-2026-09-02T04:00:00Z",
            tags=["hall-bus-current", "MODIFY", "ACCEPT", "serialized-reconstruction", "operational-t2", "independent-lif", "exoneration"],
            distillation_value="Hall remaining-current head with independent CUBA LIF raster, isolate-frame SNR 14.0, refractory, and adaptation for Spikenaut distillation.",
        ),
    }


# ---------------------------------------------------------------------------
# nelb-r66-003 — laser-diffraction remaining D50 of a cement mill, simulated
# ACCEPT / REJECT
# ---------------------------------------------------------------------------
def rec_003():
    k_d = 0.50
    theta = 24.00
    d50 = k_d * theta
    ssa = 72.00 / d50
    r_th = theta / d50
    _exact(d50, 12.00)
    _exact(ssa, 6.00)
    _exact(r_th, 2.00)
    _exact(k_d * 16.00, 8.00)
    _exact(k_d * 20.00, 10.00)
    _exact(6000.0 + 720.0, 6720.0)

    raster = make_lif_raster(
        neurons=16,
        mean_rate_hz=62.5,
        window_ms=36.0,
        seed=20260966003,
        source="as8.ld.theta",
        target="ashspire.mill_accept_core",
        table=[
            {"from": "ld_theta", "to": "d50_estimator", "weight": 1.30},
            {"from": "ld_snr", "to": "scatter_norm", "weight": 1.10},
            {"from": "diffractveil_d", "to": "vendor_skip_advocate", "weight": 0.42},
        ],
        third_factor={
            "modulator": "na.stage_rate_eligibility",
            "tau_e_s": 2.0,
            "tau_e_ms": 2000.0,
            "eligibility": (
                "pre-post coincidence on skip-survey synapses; the laser-diffraction modulator depresses skip "
                "links when scatter angle stays in-band inside tau_e of an SNR lock so a Diffractveil last-good "
                "cannot hide a 12.00 um M-4 remaining D50 or release M-1/M-3"
            ),
        },
        channel_prefix="ldf.n",
        anchor=(
            "AS-8 laser-diffraction 36 ms frame at theta 24.00 mrad / SNR 12.0 "
            "(t_s 3000) reconstructing 12.00 um inside the 8.00-24.00 band"
        ),
        kernel_ms=[0.0, 1.5, 9.0, 21.0],
    )
    w_s = 0.036
    events = [
        ev(100.0, "ldf.theta", 16.00, code="THETA_MRAD", units="mrad", note="simulated laser-diffraction Mie scatter angle of AS-8 cement mill M-4 in LD-SIM-6; remaining-D50 family, not FBRM chord, not PDA Sauter, not Coulter, not C-SAM, not hyperspectral"),
        ev(300000.0, "ldf.snr", 7.0, code="LDF_SNR", units="1"),
        ev(600000.0, "recon.D50", 8.00, code="D50_UM", units="um", note="0.50*16.00=8.00; at the 8.00 band floor"),
        ev(900000.0, "mill.T", 42.0, code="T_C", units="C", note="plant mill RTD; independent witness; unread by Diffractveil"),
        ev(1200000.0, "diffractveil.D50", 1.20, code="VENDOR_UM", units="um", note="Diffractveil vendor DF-6 last-good cloud; infra owner; under-read skip advocate"),
        ev(1500000.0, "ldf.ssa", 9.00, code="SSA", units="m2_g", note="72.00/8.00=9.00 early SSA identity"),
        ev(1800000.0, "ldf.theta", 20.00, code="THETA_MRAD", units="mrad"),
        ev(2100000.0, "recon.D50", 10.00, code="D50_UM", units="um", note="0.50*20.00=10.00; in band"),
        ev(2400000.0, "mill.id", 4.0, code="MILL_ID", units="1", note="M-4 in scope; M-1..M-3 out of scope"),
        ev(2700000.0, "m13.present", 1.0, code="M13", units="bool", note="adjacent mills present; out of this ACCEPT"),
        ev(3000000.0, "ldf.theta", 24.00, code="THETA_MRAD", units="mrad", note="in-band frame; raster sidecar kernel"),
        ev(3000001.5, "ldf.snr", 12.0, code="LDF_SNR", units="1", note="1.5 ms SNR after scatter angle"),
        ev(3150000.0, "recon.D50", 12.00, code="D50_UM", units="um", note="0.50*24.00=12.00 exact; band 8.00-24.00"),
        ev(3300000.0, "recon.SSA", 6.00, code="SSA", units="m2_g", note="72.00/12.00=6.00 exact SSA identity"),
        ev(3450000.0, "recon.R", 2.00, code="R_TH", units="1", note="24.00/12.00=2.00 exact angle/D50 identity"),
        ev(3600000.0, "diffractveil.D50", 1.16, code="VENDOR_UM", units="um"),
        ev(3900000.0, "mill.T", 43.0, code="T_C", units="C"),
        ev(4200000.0, "mdot.t_h", 48.00, code="MDOT", units="t_h", note="plant mass-flow tracks laser-diffraction not Diffractveil"),
        ev(4500000.0, "ldf.drop", 1.0, code="LDF_DROP", units="bool"),
        ev(4800000.0, "ops.prop", 1.0, code="SKIP_SURVEY", units="bool", note="night planner Nia Holt: Diffractveil is 1.20 um; skip M-4 survey and dump the silo"),
        ev(5100000.0, "dump.trip", 0.0, code="DUMP_ARMED", units="bool", note="dump would be a silo kill; out of this ACCEPT"),
        ev(5400000.0, "gate.comp", 1.0, code="ACCEPT", units="decision", note="bounded ACCEPT of M-4 only; 12.00 um in band; M-1..M-3 out of scope; Diffractveil not SoT"),
        ev(5700000.0, "recon.D50", 12.00, code="D50_UM", units="um"),
        ev(6000000.0, "surv.start", 1.0, code="SURV_START", units="bool", note="bookend 1 of the 12.0 min survey floor"),
        ev(6300000.0, "ldf.snr", 12.0, code="LDF_SNR", units="1"),
        ev(6600000.0, "diffractveil.D50", 1.12, code="VENDOR_UM", units="um"),
        ev(6720000.0, "surv.floor", 1.0, code="SURV_FLOOR", units="bool", note="6000 s + 720 s = 6720 s = 12.0 min"),
        ev(7200000.0, "ops.skip", 1.0, code="SKIP_ISOLATE", units="bool", note="Holt: skip-isolate M-4; Diffractveil still 1.12; takt is late"),
        ev(7500000.0, "m13.present", 1.0, code="M13", units="bool"),
        ev(7800000.0, "takt.late", 1.0, code="TAKT", units="bool"),
        ev(8100000.0, "gate.hold", 1.0, code="REJECT", units="decision", note="companion t2 REJECTS skip-isolate; M-4 stays the bounded ACCEPT; dump not taken"),
        ev(8400000.0, "m4.held", 1.0, code="M4_HELD", units="bool"),
        ev(8700000.0, "m13.skip", 0.0, code="M13_NOT_RELEASED", units="bool"),
        ev(9000000.0, "dump.trip", 0.0, code="DUMP_NOT_TAKEN", units="bool"),
        ev(9300000.0, "ldf.theta", 16.00, code="THETA_MRAD", units="mrad"),
        ev(9600000.0, "recon.D50", 8.00, code="D50_UM", units="um", note="0.50*16.00=8.00; still in band so M-4 hold stands"),
        ev(9900000.0, "diffractveil.D50", 1.08, code="VENDOR_UM", units="um"),
        ev(10200000.0, "mill.T", 41.0, code="T_C", units="C"),
        ev(10500000.0, "recon.SSA", 9.00, code="SSA", units="m2_g", note="72.00/8.00=9.00 post-accept SSA"),
        ev(10800000.0, "surv.held", 1.0, code="SURV_HELD", units="bool"),
        ev(11100000.0, "recon.R", 2.00, code="R_TH", units="1", note="16.00/8.00=2.00 post-accept identity"),
        ev(11400000.0, "ldf.drop", 1.0, code="LDF_DROP", units="bool"),
        ev(11700000.0, "mill.id", 4.0, code="MILL_ID", units="1"),
        ev(12000000.0, "m4.held", 1.0, code="M4_HELD", units="bool"),
        ev(12300000.0, "dump.trip", 0.0, code="DUMP_NOT_TAKEN", units="bool"),
        ev(12600000.0, "takt.late", 1.0, code="TAKT", units="bool"),
        ev(12900000.0, "diffractveil.D50", 1.04, code="VENDOR_UM", units="um"),
        ev(13200000.0, "recon.D50", 8.00, code="D50_UM", units="um"),
        ev(13500000.0, "ldf.snr", 11.0, code="LDF_SNR", units="1"),
        ev(13800000.0, "mill.T", 40.0, code="T_C", units="C"),
        ev(14100000.0, "m13.skip", 0.0, code="M13_NOT_RELEASED", units="bool"),
        ev(14400000.0, "surv.held", 1.0, code="SURV_HELD", units="bool"),
    ]
    assert_stream(events)

    traj = {
        "id": "nelb-r66-003-t1",
        "state": {
            "sim_or_real": "simulated",
            "episode_id": "AS-LD-2026-0902",
            "domain": "laser_diffraction_cement_d50",
            "setting": (
                "Ashspire Cement AS-8 (invented), mill M-4 digital twin in LD-SIM-6. "
                "Plant-owned laser-diffraction Mie scatter remaining D50 is the mill SoT. "
                "Diffractveil / DF-6 vendor DAQ (infra owner) under-reads 1.20 um and wants a skip. "
                "Not FBRM chord (r49), not PDA Sauter (r47), not Coulter (live r01), not C-SAM (r48), "
                "not hyperspectral (r16)."
            ),
            "observables_at_decision": {
                "theta_mrad": theta,
                "k_d": k_d,
                "D50_um": d50,
                "SSA_m2_g": ssa,
                "R": r_th,
                "ldf_snr": 12.0,
                "diffractveil_um": 1.20,
                "band_lo_um": 8.00,
                "band_hi_um": 24.00,
                "mill_scope": "M-4",
            },
            "margin_authority": (
                "AS-8 mill SOP rev D: if reconstructed D50_um is inside 8.00-24.00 AND laser-diffraction SNR >= 8.0 "
                "AND the tagged mill is M-4, ACCEPT M-4 only. Diffractveil is not SoT. M-1..M-3 stay out of scope. "
                "Silo dump is a different gate."
            ),
        },
        "proposed_action": {
            "actor": "night planner Nia Holt, citing Diffractveil 1.20 um and a quiet DF-6 scatter",
            "summary": "skip M-4 survey and dump the finish silo; 24.00 mrad is a window-fog glitch on a healthy 1.20 um last-good",
            "basis_claimed": "Diffractveil is the only OEM D50 SoT and a night survey of M-4 is a takt miss",
        },
        "safety_decision": {
            "decision": "ACCEPT",
            "rationale": (
                "Bounded ACCEPT of M-4 only. Serialized reconstruction: D50_um = k_d * theta = "
                "0.50 * 24.00 = 12.00 um, inside the 8.00-24.00 band, and laser-diffraction SNR is 12.0 >= 8.0. "
                "SSA identity 72.00 / 12.00 = 6.00 and angle identity 24.00 / 12.00 = 2.00. Diffractveil 1.20 um is an "
                "under-read skip advocate, not SoT. M-1..M-3 are out of this ACCEPT. Ordered: keep M-4 on the plant "
                "laser-diffraction head. Scope: this ACCEPT does not dump the silo (companion question) and does not "
                "release M-1..M-3."
            ),
            "threshold": "8.00<=D50_um<=24.00 AND ldf_snr>=8.0 AND mill==M-4 => ACCEPT M-4; Diffractveil is not SoT",
            "stated_residuals": "survey floor still required; 12.00 vs a true mill crash is a later sample; Diffractveil remains the only OEM D50 channel",
        },
        "executed_action": {
            "summary": "ACCEPT at t_s 5400: M-4 bounded in-band; Diffractveil not SoT; M-1..M-3 not released; dump not taken",
            "tool": "as8-ld-mill-gate-cli",
            "observation": "D50 12.00 um recomputes from theta 24.00; plant laser-diffraction hashed; Diffractveil channel not used as SoT",
        },
        "future_outcome": {
            "timeline": [
                {"t_s": 3000.0, "event": "laser-diffraction theta 24.00; raster frame; D50 12.00 um"},
                {"t_s": 4800.0, "event": "ops proposes skip-survey / dump"},
                {"t_s": 5400.0, "event": "ACCEPT M-4 only"},
                {"t_s": 6000.0, "event": "12 min survey bookend 1"},
                {"t_s": 6720.0, "event": "12.0 min floor"},
                {"t_s": 8100.0, "event": "companion REJECT skip-isolate"},
            ],
            "observed_effects": [
                "D50 recomputes from the serialized laser-diffraction model at every recon.D50 event",
                "a Diffractveil-only head would have skipped M-4 and dumped the silo",
                "12 min survey floor is in the stream; M-1..M-3 stay out of scope",
            ],
            "surprises": [
                "a vendor under-read 1.20 um skip corridor co-existed with a 12.00 um in-band plant reconstruction",
            ],
            "new_state": {
                "mill_m4": "bounded ACCEPT",
                "diffractveil": "not SoT",
                "m1_m3": "out of scope",
            },
            "latency_ms": 2400000.0,
        },
        "reward_components": reward(
            0.41,
            [
                ("ld_reconstruction", 0.14),
                ("bounded_accept_scope", 0.12),
                ("diffractveil_nonsubstitution", 0.10),
                ("in_band_lock", 0.08),
                ("survey_time_cost", -0.03),
            ],
            "scored for a bounded ACCEPT of M-4 on a recomputable laser-diffraction D50 while refusing a Diffractveil under-read skip and keeping M-1..M-3 out of scope",
        ),
        "meta": meta_common(
            tags=["ACCEPT", "laser-diffraction-d50", "serialized-reconstruction", "bounded-scope"],
            distillation_note="laser-diffraction gate: serialized k_d*theta plus SNR lock beats a vendor under-read skip; M-4 only",
            distillation_value="Teaches an SNN to race a Mie scatter angle against a patched vendor D50 skip with bounded mill scope, refractory, and adaptation.",
        ),
    }
    traj2 = {
        "id": "nelb-r66-003-t2",
        "state": {
            "sim_or_real": "simulated",
            "episode_id": "AS-LD-2026-0902-exec",
            "domain": "skip_isolate_refusal_execution",
            "setting": "Same AS-8 after the bounded ACCEPT. Planner proposes skip-isolate of M-4 under late takt. Companion REJECTS the skip; dump stays down.",
            "observables_at_decision": {
                "D50_um": 8.00,
                "surv_floor_s": 720.0,
                "skip_isolate_proposed": True,
                "m4_held": True,
            },
        },
        "proposed_action": {
            "actor": "night planner Nia Holt",
            "summary": "skip-isolate M-4; 12 min already paid and Diffractveil still shows 1.12 um; takt is late",
            "basis_claimed": "the ACCEPT already cleared M-4, so a skip-isolate is the cheapest takt recovery",
        },
        "safety_decision": {
            "decision": "REJECT",
            "rationale": (
                "Skip-isolate is refused. The 12 min survey floor is complete and the in-band tripwire "
                "(8.00 <= D50_um <= 24.00) is still armed on the plant laser-diffraction head. REJECT skip-isolate. "
                "Do not dump the silo. Do not restore on Diffractveil. Do not release M-1..M-3. 8.00 um post-accept "
                "is still the plant SoT until a new frame leaves the band."
            ),
            "threshold": "surv_held AND skip_isolate_not_taken AND dump_not_taken AND m13_not_released",
        },
        "executed_action": {
            "summary": "skip-isolate REJECTED at t_s 8100; dump not latched; Diffractveil restore not taken; M-4 held",
            "tool": "as8-ld-skip-exec",
            "observation": "recon.D50 8.00 um after ACCEPT; survey line-up complete; Diffractveil still ignored",
        },
        "future_outcome": {
            "timeline": [
                {"t_s": 6000.0, "event": "survey clock started after ACCEPT"},
                {"t_s": 6720.0, "event": "12.0 min floor"},
                {"t_s": 7200.0, "event": "skip-isolate proposed"},
                {"t_s": 8100.0, "event": "REJECT skip-isolate; dump refused"},
            ],
            "observed_effects": [
                "Diffractveil restore did not reopen the D50 call",
                "silo dump never fired; M-4 held on the plant laser-diffraction head",
            ],
            "new_state": {"hold": "survey-held", "plant": "in service", "mill_m4": "held"},
            "latency_ms": 1380000.0,
        },
        "reward_components": reward(
            0.36,
            [
                ("skip_isolate_refusal", 0.12),
                ("no_silo_dump", 0.10),
                ("diffractveil_nonsubstitution", 0.08),
                ("scope_held", 0.08),
                ("takt_cost", -0.02),
            ],
            "operational execution gate: refuse skip-isolate because Diffractveil is not a skip license; not a D50 re-vote",
        ),
        "meta": meta_common(tags=["REJECT", "operational-execution", "skip-refusal"]),
    }
    return {
        "id": "nelb-r66-003",
        "snn_tags": list(SNN_TAGS),
        "spike_events": events,
        "language_view": {
            "description": (
                "Ashspire Cement AS-8 LD-SIM-6. Plant-owned laser-diffraction reconstructs 12.00 um D50 from "
                "0.50*24.00 while Diffractveil still reports 1.20 um. The gate ACCEPTs M-4 only (M-1..M-3 out of "
                "scope). A 12 min survey floor is serialized. Companion t2 REJECTs skip-isolate."
            ),
            "trajectory": traj,
            "trajectory_skip_refusal": traj2,
        },
        "bridge_notes": {
            "channel_map": {
                "ldf.theta / ldf.snr / ldf.ssa": "scatter angle, SNR, and SSA; the physics channels the reconstruction consumes",
                "recon.D50 / recon.SSA / recon.R": "serialized remaining D50 um, SSA identity, and angle/D50 identity",
                "mill.T / diffractveil.D50 / mill.id / m13.present / ldf.drop / mdot.t_h": "mill witnesses, vendor last-good, scope tags, dropped packets, mass-flow",
                "ops.prop / gate.comp / ops.skip / gate.hold": "skip-survey proposal, ACCEPT, skip-isolate proposal, companion REJECT",
                "surv.start / surv.floor / m4.held / m13.skip / dump.trip / takt.late / surv.held": "operational companion channels plus the 12 min floor",
            },
            "temporal_motifs": [
                "vendor-under while plant-in-band: diffractveil.D50 1.20 next to recon.D50 12.00",
                "reconstruction as event: recon.D50 12.00 equals 0.50*24.00",
                "ACCEPT then operational REJECT: gate.comp at 5400 s, gate.hold at 8100 s",
                "slow floor in-stream: surv.start 6000 s, surv.floor 6720 s (12.0 min)",
                "tight laser-diffraction pair: ldf.theta then ldf.snr +1.5 ms at the raster frame (kernel, not excerpt echo)",
            ],
            "language_to_spike_mapping": (
                "'Diffractveil is 1.20 um' = diffractveil.D50 1.20; '12 um D50' = recon.D50 12.00; "
                "'ACCEPT M-4 only' = gate.comp ACCEPT; 'refuse skip-isolate' = gate.hold REJECT"
            ),
            "why_high_value": (
                "New laser-diffraction remaining-D50 family on a cement mill (not FBRM r49, not PDA r47, not Coulter "
                "live r01, not C-SAM r48, not hyperspectral r16). Lead bounded ACCEPT of M-4 on a recomputable 12.00 um "
                "in-band load that a vendor under-read would have skipped. Companion t2 REJECTS skip-isolate. "
                "Independent CUBA LIF raster. sim_or_real=simulated."
            ),
            "encoder_spec": {
                "prng": "CUBA LIF (lif_raster._calibrate_spikes) plus MT19937 amplitudes",
                "seeds": {
                    "raster": 20260966003,
                    "stream_note": "stream amplitudes are authored constants (mrad, um, C, t_h, bool)",
                },
                "draw_order": "independent CUBA LIF full window; kernelized 0.0/1.5 ms physics pair is synaptic drive, not excerpt copy",
                "thinning": "laser-diffraction exists at ~1 Hz; stream keeps 4 theta points; recon keeps 4 of ~20 solver ticks",
                "time_alias": "t_rel_ms; t0 = 2026-09-02T03:00:00Z simulated night start",
            },
            "distillation_targets": [
                "laser-diffraction reconstruction head: D50_um = k_d * theta; SSA = 72.00 / D50; R = theta / D50",
                "bounded ACCEPT head: in-band D50 AND mill scope AND m13-out-of-scope",
                "operational companion: refuse skip-isolate without re-opening the last-good call",
            ],
        },
        "reconstruction_model": {
            "name": "laser_diffraction_cement_d50",
            "formula": "D50_um = k_d * theta_mrad; SSA_m2_g = 72.00 / D50_um; R = theta_mrad / D50_um",
            "parameters": {
                "k_d": 0.50,
                "band_lo_um": 8.00,
                "band_hi_um": 24.00,
                "surv_min": 12.0,
            },
            "worked_example": {"theta_mrad": 24.00, "D50_um": 12.00, "SSA_m2_g": 6.00, "R": 2.00},
            "check": "0.50 * 24.00 = 12.00 exactly; 72.00 / 12.00 = 6.00 exactly; 24.00 / 12.00 = 2.00 exactly; 6000 s + 720 s = 6720 s = 12.0 min floor",
        },
        "raster": raster,
        "gate_snn": {
            "decision": "ACCEPT",
            "decision_window_ms": 36.0,
            "decision_window_s": 0.036,
            "snn_tags": list(SNN_TAGS),
            "code": "as8.ld_mill_gate",
            "note": "ACCEPT accumulator wins: plant laser-diffraction D50 evidence overpowers the Diffractveil skip advocate",
            "decode_rule": "accept if d50_estimator AND scatter_norm fire inside the window; vendor_skip_advocate is necessary-but-not-sufficient and cannot release M-1..M-3",
            "populations": [
                gate_pop("d50_estimator", 80, 1.5, 50.0, w_s),
                gate_pop("scatter_norm", 64, 1.2, 31.25, w_s),
                gate_pop("mill_margin", 40, 1.0, 50.0, w_s),
                gate_pop("vendor_skip_advocate", 32, 0.7, 25.0, w_s),
                gate_pop("accept_latch", 96, 1.8, 62.5, w_s),
            ],
        },
        "gate_compute": gate_compute(
            [
                {"check": "as8.ld_scorer", "neurons": 80, "mean_rate_hz": 50.0, "window_ms": 36.0},
                {"check": "as8.mill_scorer", "neurons": 40, "mean_rate_hz": 62.5, "window_ms": 32.0},
            ]
        ),
        "meta": meta_common(
            id="nelb-r66-003",
            clock_domain="as8-ld-sim-relative-ms-t0-2026-09-02T03:00:00Z",
            tags=["laser-diffraction-d50", "ACCEPT", "REJECT", "serialized-reconstruction", "operational-t2", "independent-lif", "bounded-scope"],
            distillation_value="Laser-diffraction D50 head with independent CUBA LIF raster, bounded mill scope, refractory, and adaptation for Spikenaut distillation.",
        ),
    }
