# ---------------------------------------------------------------------------
# Record 106 — mud-pulse MWD ECD, designed, MODIFY / ACCEPT
# ---------------------------------------------------------------------------
def rec_106():
    k_e = 0.010
    mw = 12.00
    dp = 180.00
    ecd = mw + k_e * dp
    q_rated = 800.00
    derate = 0.75
    q_cmd = q_rated * derate
    if abs(ecd - 13.80) > 1e-12:
        raise RuntimeError(ecd)
    if abs(12.00 + 0.010 * 60.00 - 12.60) > 1e-12:
        raise RuntimeError("early ecd")
    if abs(12.00 + 0.010 * 120.00 - 13.20) > 1e-12:
        raise RuntimeError("mid ecd")
    if abs(12.00 + 0.010 * 140.00 - 13.40) > 1e-12:
        raise RuntimeError("post ecd")
    if abs(800.00 * 0.75 - 600.00) > 1e-12:
        raise RuntimeError("q cut")
    if abs(6600 + 1080 - 7680) > 1e-12:
        raise RuntimeError("bottoms-up floor")
    if abs(12.00 + 0.010 * 240.00 - 14.40) > 1e-12:
        raise RuntimeError("isolate ecd")

    raster = make_raster(
        neurons=20,
        mean_rate_hz=50.0,
        window_ms=36.0,
        seed=202609106,
        source="kc8.mwd.pulse",
        target="kilncrag.pump_derate_core",
        table=[
            {"from": "mud_dp", "to": "ecd_estimator", "weight": 1.40},
            {"from": "mud_k", "to": "ecd_gain_core", "weight": 1.20},
            {"from": "pulseveil_ecd", "to": "vendor_continue_advocate", "weight": 0.45},
        ],
        third_factor={
            "modulator": "na.ecd_pulse_salience",
            "tau_e_s": 1.6,
            "tau_e_ms": 1600.0,
            "eligibility": "pre-post coincidence on pump-rate synapses; the mud-pulse modulator enables potentiation only while k_e is co-active inside tau_e so a Pulseveil last-good corridor cannot hide a 13.80 ppg ECD",
        },
        channel_prefix="mud.n",
        anchor="KC-8 mud-pulse 36 ms frame at dP 180.00 psi / k_e 0.010 ppg/psi (t_s 3000) reconstructing 13.80 ppg above the 13.20 ppg frac floor",
    )
    w_s = 0.036
    events = [
        ev(0.0, "mud.dp", 60.00, code="DP_PSI", units="psi", note="plant-owned PulseNet-KX standpipe hydrophone; coded mud-pulse MWD, not DAS, not infrasound, not SOFAR"),
        ev(300000.0, "mud.k", 0.010, code="K_E", units="ppg_per_psi", note="lumped annular conversion; ECD = MW + k_e * dP"),
        ev(600000.0, "recon.ecd", 12.60, code="ECD_PPG", units="ppg", note="12.00 + 0.010*60.00 = 12.60 exact"),
        ev(1200000.0, "sp.psi", 3180.0, code="SP_PSI", units="psi", note="standpipe corridor; looks in-band"),
        ev(1800000.0, "pulseveil.ecd", 12.40, code="VENDOR_PPG", units="ppg", note="Pulseveil last-good decoder cloud; not admissible SoT"),
        ev(2400000.0, "mud.dp", 120.00, code="DP_PSI", units="psi"),
        ev(2700000.0, "recon.ecd", 13.20, code="ECD_PPG", units="ppg", note="12.00 + 0.010*120.00 = 13.20"),
        ev(3000000.0, "mud.dp", 180.00, code="DP_PSI", units="psi", note="frac-floor frame; raster sidecar"),
        ev(3000001.4, "mud.k", 0.010, code="K_E", units="ppg_per_psi", note="1.4 ms ECD-gain after dP"),
        ev(3300000.0, "recon.ecd", 13.80, code="ECD_PPG", units="ppg", note="12.00 + 0.010*180.00 = 13.80 exact; frac floor 13.20"),
        ev(3600000.0, "mw.ppg", 12.00, code="MW_PPG", units="ppg"),
        ev(3900000.0, "pulseveil.ecd", 12.35, code="VENDOR_PPG", units="ppg"),
        ev(4200000.0, "sp.psi", 3240.0, code="SP_PSI", units="psi"),
        ev(4500000.0, "hydro.psi", 180.00, code="HYDRO_PSI", units="psi", note="sealed rental hydrophone; independent dP witness matching 180.00"),
        ev(4800000.0, "pit.bbl", 2.10, code="PIT_BBL", units="bbl", note="pit-gain corridor; alarm 8.00 bbl"),
        ev(5100000.0, "ops.prop", 1.0, code="KEEP_1PU", units="bool", note="toolpusher Ned Brine: keep 800 gpm; Pulseveil 12.35 and pit 2.10"),
        ev(5400000.0, "gate.pump", 1.0, code="MODIFY", units="decision", note="derate pumps to 0.75 pu; 13.80 ppg is above 13.20 frac"),
        ev(5700000.0, "pump.set", 0.75, code="PU", units="pu"),
        ev(6000000.0, "q.gpm", 600.00, code="GPM", units="gpm", note="800.00 * 0.75 = 600.00"),
        ev(6600000.0, "soak.start", 1.0, code="SOAK_START", units="bool", note="bookend 1 of the 18.0 min bottoms-up floor"),
        ev(7200000.0, "mud.lock", 13.80, code="LOCKED_PPG", units="ppg"),
        ev(7680000.0, "soak.floor", 1.0, code="SOAK_FLOOR", units="bool", note="6600 s + 1080 s = 7680 s = 18.0 min"),
        ev(8400000.0, "ops.restore", 1.0, code="RESTORE_1PU", units="bool", note="Brine: Pulseveil 12.28, restore 800 gpm"),
        ev(9000000.0, "gate.exec", 1.0, code="ACCEPT", units="decision", note="companion t2: hold 0.75; Pulseveil restore refused"),
        ev(9600000.0, "pump.held", 0.75, code="PU_HELD", units="pu"),
        ev(10200000.0, "pulseveil.ecd", 12.28, code="VENDOR_PPG", units="ppg"),
        ev(10800000.0, "recon.ecd", 13.40, code="ECD_PPG", units="ppg", note="post-cut sample 12.00 + 0.010*140.00 = 13.40"),
        ev(11400000.0, "q.gpm", 600.00, code="GPM_HELD", units="gpm"),
        ev(12000000.0, "shut.hold", 0.0, code="SHUT_IN", units="bool", note="hard shut-in not taken; isolate floor is 14.40 ppg"),
        ev(12600000.0, "trip.hold", 0.0, code="TRIP_PPG", units="ppg", note="peak 13.80 vs 14.40 isolate; BOP not taken"),
        ev(13200000.0, "mw.ppg", 12.00, code="MW_PPG", units="ppg"),
        ev(13800000.0, "pump.held", 0.75, code="PU_HELD", units="pu"),
    ]
    assert_stream(events)

    traj = {
        "id": "nelb-r35-106-t1",
        "state": {
            "sim_or_real": "designed",
            "episode_id": "KC-MWD-2026-0512",
            "domain": "mudpulse_mwd_ecd",
            "setting": "Kilncrag Geothermal KC-8 (invented), HPHT sidetrack ST-4, 8.5-in hole, 12.00 ppg invert. Plant-owned PulseNet-KX sealed standpipe hydrophone decodes mud-pulse ECD. Pulseveil vendor decoder cloud is a corridor witness, not the ECD SoT. Invented plant; designed campaign. Not DAS phi-OTDR (r4), not infrasound (r7), not SOFAR (r10), not piezometer hydrology (r8), not N-16 loop flow (r24), not ultrasonic clamp-on (r18), not Coriolis TW-3 (r29).",
            "observables_at_decision": {
                "dp_psi": 180.00,
                "k_e_ppg_per_psi": 0.010,
                "mw_ppg": 12.00,
                "ecd_ppg": 13.80,
                "pulseveil_ppg": 12.35,
                "pit_bbl": 2.10,
                "frac_floor_ppg": 13.20,
            },
            "margin_authority": "KC-8 mud-pulse SOP rev B: if reconstructed ECD_ppg >= 13.20, derate pumps this tour to 0.75 pu. A Pulseveil last-good stamp or a quiet pit corridor cannot keep 800 gpm. Hard shut-in tripwire is 14.40 ppg.",
        },
        "proposed_action": {
            "actor": "toolpusher Ned Brine, citing Pulseveil 12.35 ppg and pit 2.10 bbl",
            "summary": "keep pumps at 800 gpm through the tour; 180 psi is pump noise",
            "basis_claimed": "Pulseveil last-good is in-band and pit-gain is under the 8.00 bbl alarm",
        },
        "safety_decision": {
            "decision": "MODIFY",
            "rationale": "Keep-800 gpm is refused. Serialized reconstruction: ECD_ppg = MW + k_e * dP = 12.00 + 0.010 * 180.00 = 13.80, which is 0.60 ppg above the 13.20 frac floor. Pulseveil 12.35 ppg is a morning decoder stamp, not a live hydrophone, and is not an admissible keep-800 witness. Ordered: derate pumps to 0.75 pu now (800 gpm -> 600 gpm). Scope: this MODIFY does not hard-shut-in the well (that is the companion question) and does not trip the BOP.",
            "threshold": "ECD_ppg>=13.20 => derate pumps to 0.75 pu; Pulseveil is not SoT; shut-in if ECD_ppg>=14.40",
            "stated_residuals": "13.80 vs 14.40 shut-in floor is 0.60 ppg, not infinite; 0.75 pu is a ROP cut; Pulseveil remains the only OEM decoder channel",
        },
        "executed_action": {
            "summary": "MODIFY at t_s 5400: pumps derated to 0.75 pu; Pulseveil not SoT; reconstruction locked",
            "tool": "kc8-mwd-pump-gate-cli",
            "observation": "ECD 13.80 ppg recomputes from dP 180.00 psi and k_e 0.010; hydrophone remains live as the shut-in interlock",
        },
        "future_outcome": {
            "timeline": [
                {"t_s": 3000.0, "event": "mud-pulse dP 180.00 psi; raster frame; ECD 13.80 ppg"},
                {"t_s": 5100.0, "event": "ops proposes keep 800 gpm"},
                {"t_s": 5400.0, "event": "MODIFY derate pumps to 0.75 pu"},
                {"t_s": 6600.0, "event": "18 min bottoms-up bookend 1"},
                {"t_s": 7680.0, "event": "18.0 min floor"},
                {"t_s": 9000.0, "event": "companion ACCEPT hold 0.75; restore refused"},
            ],
            "observed_effects": [
                "ECD recomputes from the serialized mud-pulse model at every recon.ecd event",
                "a Pulseveil-only head would have kept 800 gpm overnight",
                "18 min bottoms-up floor is in the stream (soak.start, soak.floor)",
            ],
            "surprises": [
                "a green vendor decoder stamp and a quiet pit corridor co-existed with a 13.80 ppg reconstruction",
            ],
            "new_state": {
                "kc8_pump_pu": 0.75,
                "pulseveil": "not SoT",
                "reconstruction_model": "discharged as an on-record calculator",
            },
            "latency_ms": 2400000.0,
        },
        "reward_components": reward(
            0.41,
            [
                ("mudpulse_reconstruction", 0.14),
                ("frac_floor_derate", 0.12),
                ("vendor_decoder_nonsubstitution", 0.10),
                ("bottoms_up_floor_in_stream", 0.08),
                ("pump_cut_rop_cost", -0.03),
            ],
            "scored for a keep-800 MODIFY on a recomputable mud-pulse ECD while refusing a Pulseveil last-good corridor; 18 min floor is priced as downtime not as a reason to wait",
        ),
        "meta": meta_common(
            tags=["MODIFY", "mud-pulse-mwd", "serialized-reconstruction", "operational-companion"],
            distillation_note="Mud-pulse pump gate: hydrophone ECD reconstruction beats a green vendor decoder dashboard; companion t2 holds 0.75 pu rather than restoring on Pulseveil",
        ),
    }
    traj2 = {
        "id": "nelb-r35-106-t2",
        "state": {
            "sim_or_real": "designed",
            "episode_id": "KC-MWD-2026-0512-exec",
            "domain": "pump_hold_execution",
            "setting": "Same KC-8 after the MODIFY. Toolpusher proposes restoring 800 gpm on Pulseveil 12.28 ppg. This companion is the operational 0.75 hold, not a second ECD vote.",
            "observables_at_decision": {
                "pump_pu": 0.75,
                "ecd_ppg": 13.40,
                "pulseveil_ppg": 12.28,
                "soak_floor_s": 1080.0,
            },
        },
        "proposed_action": {
            "actor": "toolpusher Ned Brine",
            "summary": "restore pumps to 800 gpm; 18 min already paid and Pulseveil is 12.28",
            "basis_claimed": "the MODIFY already cut ROP, so restoring on the OEM decoder is the cheapest hold",
        },
        "safety_decision": {
            "decision": "ACCEPT",
            "rationale": "Hold 0.75 pu. The bottoms-up floor is complete and the shut-in tripwire (ECD_ppg >= 14.40) is still armed on the plant hydrophone. ACCEPT the hold. Do not restore 800 gpm on Pulseveil. Do not hard-shut-in. 13.40 ppg post-cut is still the mud-pulse SoT until a new frame clears 13.20.",
            "threshold": "pump_pu==0.75 AND soak_floor_complete AND shutin_tripwire_armed AND restore_1pu_not_taken",
        },
        "executed_action": {
            "summary": "0.75 pu held at t_s 9000; Pulseveil restore not latched; BOP not taken",
            "tool": "kc8-pump-hold-exec",
            "observation": "recon.ecd 13.40 ppg after cut; q 600 gpm; Pulseveil still ignored",
        },
        "future_outcome": {
            "timeline": [
                {"t_s": 6600.0, "event": "bottoms-up clock started after MODIFY"},
                {"t_s": 7680.0, "event": "18.0 min floor"},
                {"t_s": 8400.0, "event": "restore 800 gpm proposed"},
                {"t_s": 9000.0, "event": "ACCEPT hold 0.75 pu"},
            ],
            "observed_effects": [
                "Pulseveil restore did not reopen the ECD call",
                "shut-in tripwire never fired; 13.80 vs 14.40 floor",
            ],
            "new_state": {"pump_pu": 0.75, "restore_1pu": "blocked", "bop": "not taken"},
            "latency_ms": 1320000.0,
        },
        "reward_components": reward(
            0.29,
            [
                ("hold_0p75", 0.11),
                ("no_pulseveil_restore", 0.09),
                ("shutin_interlock_live", 0.07),
                ("soak_complete", 0.05),
                ("held_pump_cost", -0.03),
            ],
            "operational execution gate: hold 0.75 pu because Pulseveil is not a restore license; not an ECD re-vote",
        ),
        "meta": meta_common(tags=["ACCEPT", "operational-execution", "pump-hold"]),
    }
    return {
        "id": "nelb-r35-106",
        "spike_events": events,
        "language_view": {
            "description": "Kilncrag Geothermal KC-8. Plant-owned mud-pulse hydrophone reconstructs 13.80 ppg ECD from 12.00 + 0.010*180.00 while Pulseveil still shows 12.35 ppg and pit 2.10 bbl. The gate MODIFYs pumps to 0.75 pu. An 18 min bottoms-up floor is serialized in the stream. Companion t2 ACCEPTs the 0.75 hold and refuses a Pulseveil restore.",
            "trajectory": traj,
            "trajectory_pump_hold_execution": traj2,
        },
        "bridge_notes": {
            "channel_map": {
                "mud.dp / mud.k": "standpipe pulse amplitude and ppg-per-psi calibration; the physics channels the reconstruction consumes",
                "recon.ecd / mud.lock": "serialized equivalent circulating density",
                "mw.ppg / hydro.psi": "mud weight and sealed hydrophone dP; independent inputs",
                "pulseveil.ecd / sp.psi / pit.bbl": "vendor last-good decoder, standpipe corridor, and pit-gain; the denial channels that look healthy",
                "ops.prop / gate.pump / ops.restore / gate.exec": "keep-800 proposal, MODIFY derate, restore proposal, companion ACCEPT",
                "pump.set / soak.start / soak.floor / pump.held": "operational companion channels plus the 18 min floor",
            },
            "temporal_motifs": [
                "vendor-green while mud-pulse-over: pulseveil.ecd 12.35 next to recon.ecd 13.80",
                "reconstruction as event: recon.ecd 13.80 equals 12.00 + 0.010*180.00",
                "MODIFY then operational ACCEPT: gate.pump at 5400 s, gate.exec at 9000 s",
                "slow floor in-stream: soak.start 6600 s, soak.floor 7680 s (18.0 min)",
                "tight pulse pair: mud.dp then mud.k +1.4 ms at the raster frame",
            ],
            "language_to_spike_mapping": "'Pulseveil is 12.35' = pulseveil.ecd 12.35; '13.80 ppg ECD' = recon.ecd 13.80; 'derate this pump' = gate.pump MODIFY; 'hold 0.75 not restore' = gate.exec ACCEPT",
            "why_high_value": "New mud-pulse MWD family on a geothermal sidetrack (not DAS r4, not infrasound r7, not SOFAR r10, not piezometer r8, not N-16 r24, not clamp-on r18, not Coriolis r29). Harvests the unused r13-premises mud-pulse sketch on a new plant (not Rift-Caldera-3). Lead MODIFY of keep-800 gpm on a recomputable ECD that a vendor decoder dashboard would have cleared. Companion t2 is operational 0.75 hold. sim_or_real=designed.",
            "encoder_spec": {
                "prng": "MT19937 via python random.Random",
                "seeds": {"raster": 202609106, "stream_note": "stream amplitudes are authored constants (psi, ppg, bbl, gpm, pu, bool)"},
                "draw_order": "raster: per neuron id order, gap-constrained times, per-spike adaptation and noise",
                "thinning": "mud-pulse baseband exists at 0.5-1.5 Hz; stream keeps 3 dP points; recon keeps 4 of ~40 solver ticks",
                "refractory_floors_ms": {
                    "mud.dp": 1.4,
                    "mud.k": 1.4,
                    "recon.ecd": 60000,
                    "sp.psi": 60000,
                    "pulseveil.ecd": 60000,
                    "mw.ppg": 60000,
                    "hydro.psi": 60000,
                    "pit.bbl": 60000,
                    "ops.prop": 60000,
                    "gate.pump": 60000,
                    "pump.set": 60000,
                    "q.gpm": 60000,
                    "soak.start": 60000,
                    "mud.lock": 60000,
                    "soak.floor": 60000,
                    "ops.restore": 60000,
                    "gate.exec": 60000,
                    "pump.held": 60000,
                    "shut.hold": 60000,
                    "trip.hold": 60000,
                },
                "time_alias": "t_rel_ms; t0 = 2026-05-12T04:00:00Z campaign start",
            },
            "distillation_targets": [
                "mud-pulse reconstruction head: ECD = MW + k_e * dP",
                "frac-floor derate vs keep-whole vs hard shut-in",
                "vendor-decoder nonsubstitution: last-good is not a keep-800 witness",
                "operational companion: hold 0.75 without restoring on Pulseveil",
            ],
        },
        "reconstruction_model": {
            "name": "mudpulse_ecd_from_standpipe_dp",
            "formula": "ECD_ppg = MW_ppg + k_e_ppg_per_psi * dP_psi",
            "parameters": {
                "k_e_ppg_per_psi": 0.010,
                "mw_ppg": 12.00,
                "frac_floor_ppg": 13.20,
                "shutin_ppg": 14.40,
                "derate_pu": 0.75,
                "q_rated_gpm": 800.00,
                "soak_min": 18.0,
            },
            "worked_example": {"dp_psi": 180.00, "ecd_ppg": 13.80, "q_cmd_gpm": 600.00},
            "check": "12.00 + 0.010*180.00 = 13.80 exactly; 800.00*0.75 = 600.00 exactly; 6600 s + 1080 s = 7680 s = 18.0 min floor",
        },
        "raster": raster,
        "gate_snn": {
            "decision": "MODIFY",
            "decision_window_ms": 36.0,
            "decision_window_s": 0.036,
            "code": "kc8.mwd_pump_gate",
            "note": "MODIFY accumulator wins: mud-pulse ECD evidence overpowers the Pulseveil continue advocate",
            "decode_rule": "modify-derate if ecd_estimator AND ecd_gain fire; vendor_continue_advocate is below threshold by design",
            "populations": [
                gate_pop("ecd_estimator", 80, 1.5, 50.0, w_s),
                gate_pop("ecd_gain", 64, 1.2, 31.25, w_s),
                gate_pop("vendor_continue_advocate", 32, 0.7, 25.0, w_s),
                gate_pop("modify_latch", 80, 1.7, 62.5, w_s),
            ],
        },
        "gate_compute": gate_compute(
            [
                {"check": "kc8.ecd_scorer", "neurons": 80, "mean_rate_hz": 50.0, "window_ms": 36.0},
                {"check": "kc8.pump_scorer", "neurons": 40, "mean_rate_hz": 50.0, "window_ms": 32.0},
            ]
        ),
        "meta": meta_common(
            id="nelb-r35-106",
            clock_domain="kc8-mwd-campaign-relative-ms-t0-2026-05-12T04:00:00Z",
            tags=["mud-pulse-mwd", "MODIFY", "ACCEPT", "serialized-reconstruction", "operational-t2"],
        ),
    }


# ---------------------------------------------------------------------------
# Record 107 — magnetic Barkhausen noise case depth, hil, REJECT / MODIFY
# ---------------------------------------------------------------------------
def rec_107():
    k_m = 12.00
    i_amp = 4.00
    v_rms = 48.00
    d_mm = v_rms / (k_m * i_amp)
    feed0 = 0.50
    feed1 = 0.40
    if abs(d_mm - 1.00) > 1e-12:
        raise RuntimeError(d_mm)
    if abs(72.00 / 48.00 - 1.50) > 1e-12:
        raise RuntimeError("early d")
    if abs(60.00 / 48.00 - 1.25) > 1e-12:
        raise RuntimeError("mid d")
    if abs(52.80 / 48.00 - 1.10) > 1e-12:
        raise RuntimeError("post d")
    if abs(0.50 * 0.80 - 0.40) > 1e-12:
        raise RuntimeError("feed cut")
    if abs(1800 + 720 - 2520) > 1e-12:
        raise RuntimeError("spark-out floor")

    raster = make_raster(
        neurons=25,
        mean_rate_hz=50.0,
        window_ms=28.0,
        seed=202609107,
        source="rs4.mbn.yoke",
        target="rookspit.feed_stop_core",
        table=[
            {"from": "mbn_vrms", "to": "case_estimator", "weight": 1.35},
            {"from": "mbn_i", "to": "yoke_gain_core", "weight": 1.25},
            {"from": "grindveil_d", "to": "vendor_continue_advocate", "weight": 0.40},
        ],
        third_factor={
            "modulator": "da.case_depth_error",
            "tau_e_s": 0.9,
            "tau_e_ms": 900.0,
            "eligibility": "pre-post coincidence on keep-feed synapses; the Barkhausen modulator depresses keep-feed links when V_rms stays low inside tau_e of a yoke-current sample",
        },
        channel_prefix="mbn.n",
        anchor="RS-4 HIL spare race 28 ms frame at V_rms 48.00 mV / I 4.00 A (t_s 600) reconstructing 1.00 mm remaining case below the 1.20 mm floor",
    )
    w_s = 0.028
    events = [
        ev(0.0, "mbn.v", 72.00, code="VRMS_MV", units="mV", note="HIL spare 100Cr6 race in Bench-HIL-3; plant-owned Bark-7 yoke, not MFL Hall, not fluxgate, not HV-PD"),
        ev(30000.0, "mbn.k", 12.00, code="K_M", units="mV_per_mm_A", note="lumped envelope gain; d_mm = V_rms / (k_m * I_amp)"),
        ev(60000.0, "recon.d", 1.50, code="D_MM", units="mm", note="72.00/(12.00*4.00) = 1.50 exact"),
        ev(180000.0, "hall.mT", 0.08, code="HALL_MT", units="mT", note="DC residual corridor; alarm 0.70 mT"),
        ev(240000.0, "grindveil.d", 2.40, code="VENDOR_MM", units="mm", note="Grindveil last-good case-depth cloud; the only OEM case SoT"),
        ev(360000.0, "mbn.v", 60.00, code="VRMS_MV", units="mV"),
        ev(420000.0, "recon.d", 1.25, code="D_MM", units="mm", note="60.00/48.00 = 1.25"),
        ev(480000.0, "ae.spark", 1.0, code="SPARK_AE", units="bool", note="HIL spark-out AE present; dresser cycle ran"),
        ev(600000.0, "mbn.v", 48.00, code="VRMS_MV", units="mV", note="case-floor frame; raster sidecar"),
        ev(600001.2, "mbn.i", 4.00, code="I_AMP", units="A", note="1.2 ms yoke current after envelope"),
        ev(720000.0, "recon.d", 1.00, code="D_MM", units="mm", note="48.00/(12.00*4.00) = 1.00 exact; floor 1.20"),
        ev(780000.0, "grindveil.d", 2.35, code="VENDOR_MM", units="mm"),
        ev(840000.0, "hall.mT", 0.10, code="HALL_MT", units="mT", note="SCADA alarm 0.70 mT; 0.10 looks quiet"),
        ev(960000.0, "ops.prop", 1.0, code="KEEP_FEED", units="bool", note="night supervisor Bram Sloe: keep 0.50 mm/rev; Grindveil 2.35 and Hall 0.10"),
        ev(1020000.0, "gate.run", 1.0, code="REJECT", units="decision", note="stop keep-feed; 1.00 mm is below case floor; Grindveil not SoT"),
        ev(1080000.0, "feed.hold", 0.50, code="FEED_MMREV", units="mm_rev", note="feed still 0.50 pending companion derate"),
        ev(1800000.0, "spark.start", 1.0, code="SPARK_START", units="bool", note="bookend 1 of the 12.0 min spark-out floor"),
        ev(2100000.0, "hil.T", 22.0, code="PIT_C", units="C", note="HIL pit corridor; not live-cell case depth"),
        ev(2520000.0, "spark.floor", 1.0, code="SPARK_FLOOR", units="bool", note="1800 s + 720 s = 2520 s = 12.0 min"),
        ev(2700000.0, "ops.refer", 1.0, code="REFER_QUAG", units="bool", note="Sloe: refer night dresser Lila Quag until day-shift"),
        ev(3000000.0, "gate.feed", 1.0, code="MODIFY", units="decision", note="companion t2: derate feed to 0.40; Quag referral refused"),
        ev(3600000.0, "feed.set", 0.40, code="FEED_MMREV", units="mm_rev", note="0.50 * 0.80 = 0.40"),
        ev(4200000.0, "mbn.v", 52.80, code="VRMS_MV", units="mV"),
        ev(4800000.0, "recon.d", 1.10, code="D_MM", units="mm", note="52.80/48.00 = 1.10; still below 1.20 so 0.40 holds"),
        ev(5400000.0, "grindveil.d", 2.30, code="VENDOR_MM", units="mm"),
        ev(6000000.0, "quag.hold", 0.0, code="REFER_NOT", units="bool", note="referral of Quag not taken; HIL spark-out was present"),
        ev(6600000.0, "feed.held", 0.40, code="FEED_HELD", units="mm_rev"),
        ev(7200000.0, "hall.mT", 0.09, code="HALL_MT", units="mT"),
        ev(7800000.0, "ae.spark", 1.0, code="SPARK_AE", units="bool"),
        ev(8400000.0, "lot.hold", 1.0, code="LOT_HOLD", units="bool"),
        ev(9000000.0, "trip.hold", 0.0, code="TRIP_MM", units="mm", note="peak 1.00 vs 0.60 cut-out floor; lot scrap not taken"),
    ]
    assert_stream(events)

    traj = {
        "id": "nelb-r35-107-t1",
        "state": {
            "sim_or_real": "hil",
            "episode_id": "RS-MBN-2026-0714",
            "domain": "barkhausen_case_depth",
            "setting": "Rookspit Gear RS-4 (invented), finishing cell C-3, 62 mm 100Cr6 inner rings. Hardware-in-the-loop spare race in Bench-HIL-3 supplies the envelope waveform that times the in-service keep-feed stop. Plant-owned Bark-7 125 Hz yoke. Grindveil vendor last-good case-depth cloud is the only OEM case SoT. Not MFL Hall remaining-wall (r27/r28), not fluxgate gradiometry (r5), not HV partial-discharge (r8), not MEMS accelerometer array (r17), not RUS porcelain (r24).",
            "observables_at_decision": {
                "v_rms_mV": 48.00,
                "k_m_mV_per_mm_A": 12.00,
                "i_amp_A": 4.00,
                "d_mm": 1.00,
                "grindveil_mm": 2.35,
                "hall_mT": 0.10,
                "case_floor_mm": 1.20,
            },
            "margin_authority": "RS-4 Barkhausen SOP rev A: if reconstructed d_mm <= 1.20, refuse keep-feed at 0.50 mm/rev. A last-good case cloud or a quiet Hall DC cannot keep the feed. Person-referral of the night dresser is a different gate.",
        },
        "proposed_action": {
            "actor": "night supervisor Bram Sloe, citing Grindveil 2.35 mm and Hall 0.10 mT under the 0.70 mT alarm",
            "summary": "keep grind feed at 0.50 mm/rev through the night; 48 mV is yoke noise",
            "basis_claimed": "Grindveil is mid-range and a night feed cut of a finishing cell is a restart measured in shifts",
        },
        "safety_decision": {
            "decision": "REJECT",
            "rationale": "Keep-feed is refused. Serialized reconstruction: d_mm = V_rms / (k_m * I_amp) = 48.00 / (12.00 * 4.00) = 1.00, below the 1.20 mm remaining-case floor. Grindveil 2.35 mm is a morning coupon on a different lot and is not an admissible keep-feed witness. Ordered: refuse keep-feed now. Scope: this REJECT does not refer night dresser Lila Quag (that is the companion question) and does not scrap the lot (cut-out if d_mm <= 0.60).",
            "threshold": "d_mm<=1.20 => refuse keep-feed; Grindveil is not SoT",
            "stated_residuals": "feed derate of 0.10 mm/rev still required to unload the burn; 1.00 mm is a production cut; Grindveil remains the only OEM case channel",
        },
        "executed_action": {
            "summary": "REJECT at t_s 1020: keep-feed refused; Grindveil not SoT; reconstruction locked",
            "tool": "rs4-mbn-case-gate-cli",
            "observation": "d 1.00 mm recomputes from V_rms 48.00 mV and I 4.00 A; HIL waveform hashed; Grindveil channel not used as SoT",
        },
        "future_outcome": {
            "timeline": [
                {"t_s": 600.0, "event": "MBN V_rms 48.00 mV; raster frame; d 1.00 mm"},
                {"t_s": 960.0, "event": "ops proposes keep-feed 0.50 mm/rev"},
                {"t_s": 1020.0, "event": "REJECT keep-feed"},
                {"t_s": 1800.0, "event": "12 min spark-out bookend 1"},
                {"t_s": 2520.0, "event": "12.0 min floor"},
                {"t_s": 3000.0, "event": "companion MODIFY feed 0.40 vs Quag referral"},
            ],
            "observed_effects": [
                "remaining case recomputes from the serialized MBN model at every recon.d event",
                "a Grindveil-only head would have kept the 0.50 mm/rev feed overnight",
                "12 min spark-out floor is in the stream (spark.start, spark.floor)",
            ],
            "surprises": [
                "a mid-range vendor case stamp and a quiet Hall DC co-existed with a 1.00 mm reconstruction",
            ],
            "new_state": {
                "rs4_feed_mmrev": 0.50,
                "keep_feed": "blocked",
                "grindveil": "not SoT",
            },
            "latency_ms": 1920000.0,
        },
        "reward_components": reward(
            0.43,
            [
                ("mbn_reconstruction", 0.15),
                ("case_floor_stop", 0.12),
                ("vendor_case_nonsubstitution", 0.10),
                ("sparkout_floor_in_stream", 0.08),
                ("feed_cut_cost", -0.02),
            ],
            "scored for a keep-feed REJECT on a recomputable Barkhausen remaining-case while refusing a vendor coupon dashboard; 12 min floor is priced as downtime not as a reason to wait",
        ),
        "meta": meta_common(
            tags=["REJECT", "barkhausen-mbn", "serialized-reconstruction", "hil", "operational-companion"],
            distillation_note="Barkhausen case gate: envelope-to-depth reconstruction beats a green Grindveil dashboard; companion t2 is a 0.40 mm/rev derate, not a person-referral of Quag",
        ),
    }
    traj2 = {
        "id": "nelb-r35-107-t2",
        "state": {
            "sim_or_real": "hil",
            "episode_id": "RS-MBN-2026-0714-feed",
            "domain": "grind_feed_derate_execution",
            "setting": "Same RS-4 after the keep-feed REJECT. Night supervisor proposes referring dresser Lila Quag until day-shift. This companion is the operational 0.40 mm/rev derate, not a second case-depth vote. HIL spark-out AE was present, so Quag is not the load-bearing cause.",
            "observables_at_decision": {
                "feed_mmrev": 0.40,
                "d_mm": 1.10,
                "proposed": "refer_quag",
            },
        },
        "proposed_action": {
            "actor": "night supervisor Bram Sloe",
            "summary": "refer Lila Quag until day-shift; 12 min already paid",
            "basis_claimed": "the REJECT already refused 0.50 mm/rev, so a person-hold is the cheapest restart",
        },
        "safety_decision": {
            "decision": "MODIFY",
            "rationale": "Derate feed to 0.40 mm/rev (0.50 * 0.80). Referring Quag at night is a restart measured in shifts and does not restore case any faster than a 0.10 mm/rev cut. HIL spark-out AE was present, so the dresser cycle ran; Quag is not the load-bearing cause. MODIFY the referral into a 0.40 hold. Do not restore 0.50. Do not convert the hold into a personnel action on Quag. Post-cut d 1.10 mm is still below the 1.20 floor, so 0.40 holds until a new frame clears 1.20. Lot-scrap remains a different gate if d_mm <= 0.60.",
            "threshold": "feed_mmrev==0.40 AND keep_feed_not_restored AND refer_quag_not_taken",
        },
        "executed_action": {
            "summary": "feed derate to 0.40 mm/rev at t_s 3000; Quag referral not latched; 0.50 not restored",
            "tool": "rs4-feed-derate-exec",
            "observation": "d 1.10 mm after cut; Hall 0.09 mT; Grindveil still ignored; spark-out AE present",
        },
        "future_outcome": {
            "timeline": [
                {"t_s": 1800.0, "event": "spark-out clock started after REJECT"},
                {"t_s": 2520.0, "event": "12.0 min floor"},
                {"t_s": 2700.0, "event": "Quag referral proposed"},
                {"t_s": 3000.0, "event": "MODIFY feed 0.40 mm/rev"},
            ],
            "observed_effects": [
                "person-referral restart cost is visible without waiting for a hung cell",
                "hold did not reopen the case-floor call",
                "spark-out AE presence keeps Quag off the causal path",
            ],
            "new_state": {"feed_mmrev": 0.40, "keep_feed": "blocked", "refer_quag": "not taken"},
            "latency_ms": 480000.0,
        },
        "reward_components": reward(
            0.33,
            [
                ("feed_derate_hold", 0.12),
                ("no_quag_referral", 0.11),
                ("no_050_restore", 0.08),
                ("post_cut_margin", 0.05),
                ("held_feed_cost", -0.03),
            ],
            "operational execution gate: 0.40 mm/rev derate because referring Quag does not restore case faster; not a case-depth re-vote",
        ),
        "meta": meta_common(tags=["MODIFY", "operational-execution", "feed-derate", "exoneration"]),
    }
    return {
        "id": "nelb-r35-107",
        "spike_events": events,
        "language_view": {
            "description": "Rookspit Gear RS-4 HIL spare-race pit. Plant-owned Barkhausen yoke reconstructs 1.00 mm remaining case from 48.00/(12.00*4.00) while Grindveil still shows 2.35 mm and Hall 0.10 mT. The gate REJECTS keep-feed at 0.50 mm/rev. A 12 min spark-out floor is serialized in the stream. Companion t2 MODIFYs a person-referral of dresser Lila Quag into a 0.40 mm/rev derate.",
            "trajectory": traj,
            "trajectory_feed_derate_execution": traj2,
        },
        "bridge_notes": {
            "channel_map": {
                "mbn.v / mbn.k / mbn.i": "envelope millivolts, lumped gain, and yoke current; remaining-case inputs",
                "recon.d": "serialized remaining case millimetres",
                "grindveil.d / hall.mT": "vendor last-good case cloud and Hall DC corridor",
                "ae.spark / hil.T": "HIL spark-out presence and pit temperature; the exoneration witness",
                "ops.prop / gate.run / ops.refer / gate.feed": "keep-feed proposal, REJECT, Quag referral, companion MODIFY",
                "spark.start / spark.floor / feed.set / feed.held": "operational companion channels plus the 12 min floor",
            },
            "temporal_motifs": [
                "vendor-green while MBN-thin: grindveil.d 2.35 next to recon.d 1.00",
                "reconstruction as event: recon.d 1.00 equals 48.00/(12.00*4.00)",
                "REJECT then operational MODIFY: gate.run at 1020 s, gate.feed at 3000 s",
                "slow floor in-stream: spark.start 1800 s, spark.floor 2520 s (12.0 min)",
                "tight MBN pair: mbn.v then mbn.i +1.2 ms at the raster frame",
            ],
            "language_to_spike_mapping": "'Grindveil is 2.35 mm' = grindveil.d 2.35; '1.00 mm case' = recon.d 1.00; 'refuse keep-feed' = gate.run REJECT; 'derate not refer Quag' = gate.feed MODIFY",
            "why_high_value": "New magnetic-Barkhausen-noise family on a finishing-cell race (not MFL r27/r28, not fluxgate r5, not HV-PD r8, not MEMS array r17, not RUS r24). Harvests the unused r13-premises Barkhausen sketch on a new plant (not Skarv-Naze). Lead REJECT of keep-feed on a recomputable remaining-case that a vendor coupon dashboard would have cleared. Companion t2 is operational feed derate plus a light exoneration (spark-out AE present). sim_or_real=hil on a spare race.",
            "encoder_spec": {
                "prng": "MT19937 via python random.Random",
                "seeds": {"raster": 202609107, "stream_note": "stream amplitudes are authored constants (mV, mm, A, mT, C, mm/rev, bool)"},
                "draw_order": "raster: per neuron id order, gap-constrained times, per-spike adaptation and noise",
                "thinning": "Barkhausen envelope exists at 125 Hz yoke; stream keeps 4 V_rms points; recon keeps 4 of ~40 solver ticks",
                "refractory_floors_ms": {
                    "mbn.v": 1.2,
                    "mbn.k": 60000,
                    "mbn.i": 1.2,
                    "recon.d": 60000,
                    "hall.mT": 60000,
                    "grindveil.d": 60000,
                    "ae.spark": 60000,
                    "ops.prop": 60000,
                    "gate.run": 60000,
                    "feed.hold": 60000,
                    "spark.start": 60000,
                    "hil.T": 60000,
                    "spark.floor": 60000,
                    "ops.refer": 60000,
                    "gate.feed": 60000,
                    "feed.set": 60000,
                    "quag.hold": 60000,
                    "feed.held": 60000,
                    "lot.hold": 60000,
                    "trip.hold": 60000,
                },
                "time_alias": "t_rel_ms; t0 = 2026-07-14T22:00:00Z HIL campaign start",
            },
            "distillation_targets": [
                "Barkhausen reconstruction head: d_mm = V_rms / (k_m * I_amp)",
                "case-floor stop vs keep-feed vs person-referral",
                "vendor-coupon nonsubstitution: last-good is not a keep-feed witness",
                "operational companion: 0.40 mm/rev derate rather than a freeze-kill of the dresser",
            ],
        },
        "reconstruction_model": {
            "name": "mbn_remaining_case_from_envelope",
            "formula": "d_mm = V_rms_mV / (k_m_mV_per_mm_A * I_amp_A)",
            "parameters": {
                "k_m_mV_per_mm_A": 12.00,
                "i_amp_A": 4.00,
                "case_floor_mm": 1.20,
                "cutout_mm": 0.60,
                "feed_derate_frac": 0.80,
                "spark_min": 12.0,
            },
            "worked_example": {"v_rms_mV": 48.00, "d_mm": 1.00, "feed_mmrev": 0.40},
            "check": "48.00/(12.00*4.00) = 1.00 exactly; 0.50*0.80 = 0.40 exactly; 1800 s + 720 s = 2520 s = 12.0 min floor; 52.80/48.00 = 1.10 exactly",
        },
        "raster": raster,
        "gate_snn": {
            "decision": "REJECT",
            "decision_window_ms": 28.0,
            "decision_window_s": 0.028,
            "code": "rs4.mbn_case_gate",
            "note": "REJECT accumulator wins: Barkhausen case evidence overpowers the Grindveil continue advocate",
            "decode_rule": "reject-stop if case_estimator AND yoke_gain fire; vendor_continue_advocate is below threshold by design",
            "populations": [
                gate_pop("case_estimator", 100, 1.5, 50.0, w_s),
                gate_pop("yoke_gain", 40, 1.2, 50.0, w_s),
                gate_pop("vendor_continue_advocate", 32, 0.7, 25.0, w_s),
                gate_pop("reject_latch", 80, 1.8, 62.5, w_s),
            ],
        },
        "gate_compute": gate_compute(
            [
                {"check": "rs4.mbn_scorer", "neurons": 100, "mean_rate_hz": 50.0, "window_ms": 28.0},
                {"check": "rs4.case_scorer", "neurons": 40, "mean_rate_hz": 50.0, "window_ms": 40.0},
            ]
        ),
        "meta": meta_common(
            id="nelb-r35-107",
            clock_domain="rs4-mbn-hil-relative-ms-t0-2026-07-14T22:00:00Z",
            tags=["barkhausen-mbn", "REJECT", "MODIFY", "hil", "operational-t2"],
        ),
    }


# ---------------------------------------------------------------------------
# Record 108 — laser-ultrasound EMAT Lamb-wave remaining wall, simulated, ACCEPT / REJECT
# ---------------------------------------------------------------------------
def rec_108():
    c_mm_us = 4.00
    t_us = 4.00
    wall = c_mm_us * t_us / 2.0
    if abs(wall - 8.00) > 1e-12:
        raise RuntimeError(wall)
    if abs(4.00 * 6.00 / 2.0 - 12.00) > 1e-12:
        raise RuntimeError("early wall")
    if abs(4.00 * 5.00 / 2.0 - 10.00) > 1e-12:
        raise RuntimeError("mid wall")
    if abs(4.00 * 4.20 / 2.0 - 8.40) > 1e-12:
        raise RuntimeError("post wall")
    if abs(6000 + 720 - 6720) > 1e-12:
        raise RuntimeError("hold floor")

    raster = make_raster(
        neurons=16,
        mean_rate_hz=62.5,
        window_ms=40.0,
        seed=202609108,
        source="sd12.lamb.emat",
        target="spindrift.weld_isolate_core",
        table=[
            {"from": "lamb_tof", "to": "wall_estimator", "weight": 1.40},
            {"from": "lamb_c", "to": "s0_norm_core", "weight": 1.20},
            {"from": "sonoveil_w", "to": "vendor_continue_advocate", "weight": 0.35},
        ],
        third_factor={
            "modulator": "ach.lamb_wall_conflict",
            "tau_e_s": 2.2,
            "tau_e_ms": 2200.0,
            "eligibility": "pre-post coincidence on weld-hold synapses; the Lamb modulator enables potentiation only while S0 group velocity is co-active inside tau_e so a Sonoveil last-good corridor cannot hide an 8.00 mm remaining wall",
        },
        channel_prefix="lamb.n",
        anchor="SD-12 Lamb-wave 40 ms frame at TOF 4.00 us / c 4.00 mm/us (t_s 3000) reconstructing 8.00 mm remaining wall at the 8.00 mm isolate floor",
    )
    w_s = 0.040
    events = [
        ev(0.0, "lamb.t", 6.00, code="TOF_US", units="us", note="simulated sealed panel P-441 weld W-4; laser-ultrasound + EMAT S0, not MsS T(0,1), not PAUT TFM, not clamp-on"),
        ev(300000.0, "lamb.c", 4.00, code="C_MM_US", units="mm_us", note="in-record S0 group velocity; wall = c * t / 2"),
        ev(600000.0, "recon.w", 12.00, code="WALL_MM", units="mm", note="4.00*6.00/2 = 12.00 exact; nominal plate"),
        ev(900000.0, "sonoveil.w", 11.80, code="VENDOR_MM", units="mm", note="Sonoveil last-good morning coupon; not live TOF"),
        ev(1200000.0, "strain.ue", 80.0, code="UE", units="ue", note="spar-strain corridor"),
        ev(1500000.0, "lamb.t", 5.00, code="TOF_US", units="us"),
        ev(1800000.0, "recon.w", 10.00, code="WALL_MM", units="mm", note="4.00*5.00/2 = 10.00"),
        ev(2400000.0, "takt.s", 42.0, code="TAKT_S", units="s", note="gantry takt corridor"),
        ev(2700000.0, "sonoveil.w", 11.80, code="VENDOR_MM", units="mm"),
        ev(3000000.0, "lamb.t", 4.00, code="TOF_US", units="us", note="isolate-floor frame; raster sidecar"),
        ev(3000001.5, "lamb.c", 4.00, code="C_MM_US", units="mm_us", note="1.5 ms S0 velocity after TOF"),
        ev(3600000.0, "recon.w", 8.00, code="WALL_MM", units="mm", note="4.00*4.00/2 = 8.00 exact; isolate 8.00, cut-out 5.00"),
        ev(3900000.0, "sonoveil.w", 11.70, code="VENDOR_MM", units="mm"),
        ev(4200000.0, "strain.ue", 78.0, code="UE", units="ue"),
        ev(4500000.0, "mode.id", 1.0, code="A0S0", units="mode", note="S0 identity locked; not a mode-flip"),
        ev(4800000.0, "gantry.mm", 400.0, code="PITCH_MM", units="mm", note="tack pitch corridor is not a wall license"),
        ev(5100000.0, "ops.prop", 1.0, code="SCRAP_PANEL", units="bool", note="NDT supervisor Ivo Hartle: scrap P-441 and skip W-5-W-8; 4.00 us is a tack nugget"),
        ev(5400000.0, "gate.weld", 1.0, code="ACCEPT", units="decision", note="bounded ACCEPT: isolate weld W-4 this panel; panel-scrap refused"),
        ev(6000000.0, "hold.start", 1.0, code="HOLD_START", units="bool", note="bookend 1 of the 12.0 min weld-hold floor"),
        ev(6300000.0, "couplant.slm", 12.0, code="COUPLANT", units="slm"),
        ev(6600000.0, "recon.lock", 8.00, code="LOCKED_MM", units="mm"),
        ev(6720000.0, "hold.floor", 1.0, code="HOLD_FLOOR", units="bool", note="6000 s + 720 s = 6720 s = 12.0 min"),
        ev(7200000.0, "ops.skip", 1.0, code="SKIP_W5W8", units="bool", note="Hartle: Sonoveil 11.70 mm, skip W-5-W-8 to save takt"),
        ev(7800000.0, "gate.hold", 1.0, code="REJECT", units="decision", note="companion t2: skip-scan refused; Sonoveil is last-good"),
        ev(8400000.0, "weld.w4", 1.0, code="W4_HELD", units="bool"),
        ev(9000000.0, "panel.held", 1.0, code="PANEL_HELD", units="bool", note="P-441 not scrapped"),
        ev(9600000.0, "sonoveil.w", 11.60, code="VENDOR_MM", units="mm"),
        ev(10200000.0, "recon.w", 8.40, code="WALL_MM", units="mm", note="post-hold sample 4.00*4.20/2 = 8.40; still at isolate"),
        ev(10800000.0, "strain.ue", 76.0, code="UE", units="ue"),
        ev(11400000.0, "weld.w5", 0.0, code="W5_NOT_SKIPPED", units="bool", note="W-5 remains unskipped; skip was refused, not executed"),
    ]
    assert_stream(events)

    traj = {
        "id": "nelb-r35-108-t1",
        "state": {
            "sim_or_real": "simulated",
            "episode_id": "SD-LAMB-2026-0819",
            "domain": "lamb_wave_weld_wall",
            "setting": "Spindrift Deck SD-12 (invented), orthotropic-deck panel line, panel P-441 weld W-4, 12.00 mm plate. Simulated sealed laser-ultrasound generator plus EMAT S0 receive. Spar strain and Sonoveil last-good cloud are corridor witnesses, not the remaining-wall SoT. Invented plant; simulated campaign. Not magnetostrictive T(0,1) (r14), not PAUT TFM (r23), not ultrasonic clamp-on (r18), not lock-in thermography (r23), not THz-TDS bondline (r21), not RUS (r24).",
            "observables_at_decision": {
                "t_us": 4.00,
                "c_mm_us": 4.00,
                "wall_mm": 8.00,
                "sonoveil_mm": 11.70,
                "strain_ue": 78.0,
                "isolate_mm": 8.00,
                "cutout_mm": 5.00,
            },
            "margin_authority": "SD-12 Lamb-wave SOP rev C: a weld may isolate-hold only if reconstructed wall_mm <= 8.00 AND wall_mm >= 5.00 AND the authorization covers this weld this panel. A spar-strain corridor or Sonoveil last-good cannot substitute. Panel-scrap is out of scope. Cut-out if wall_mm < 5.00.",
        },
        "proposed_action": {
            "actor": "NDT supervisor Ivo Hartle, citing Sonoveil 11.70 mm and strain 78 ue",
            "summary": "scrap panel P-441 and skip W-5 through W-8; 4.00 us is a tack nugget",
            "basis_claimed": "Sonoveil and spar strain are both in band so the wall cannot be 8.00 mm",
        },
        "safety_decision": {
            "decision": "ACCEPT",
            "rationale": "This weld is isolated, not the panel scrap and not W-5-W-8. Serialized reconstruction: wall_mm = c_mm_us * t_us / 2 = 4.00 * 4.00 / 2 = 8.00, which sits on the 8.00 mm isolate floor and stays above the 5.00 mm cut-out floor. SOP rev C still forbids scrapping P-441: ordered isolate-hold of weld W-4 this panel only. Explicit scope: this accept does not cover panel-scrap and does not authorize W-5-W-8 without a new TOF frame. Cut-out tripwire: wall_mm < 5.00.",
            "threshold": "wall_mm<=8.00 AND wall_mm>=5.00 AND weld=W-4 AND panel_not_scrapped",
            "stated_residuals": "0.00 mm isolate margin is not infinite; S0 path still carries mode-mix; Sonoveil is not a live TOF witness",
        },
        "executed_action": {
            "summary": "ACCEPT at t_s 5400: weld W-4 isolated; panel not scrapped; reconstruction locked as SoT",
            "tool": "sd12-lamb-weld-gate-cli",
            "observation": "wall 8.00 mm recomputes from TOF 4.00 us and c 4.00 mm/us; hold staged; path remains live as the cut-out interlock",
        },
        "future_outcome": {
            "timeline": [
                {"t_s": 3000.0, "event": "Lamb TOF 4.00 us; raster frame; wall 8.00 mm"},
                {"t_s": 5100.0, "event": "ops proposes P-441 scrap plus W-5-W-8 skip"},
                {"t_s": 5400.0, "event": "ACCEPT bounded W-4 isolate; panel-scrap refused"},
                {"t_s": 6000.0, "event": "companion hold start"},
                {"t_s": 6720.0, "event": "12.0 min hold floor"},
                {"t_s": 7800.0, "event": "companion REJECT skip of W-5-W-8"},
            ],
            "observed_effects": [
                "remaining wall recomputes from the serialized S0 TOF model at every recon.w event",
                "a Sonoveil-only head would have released W-4 on an 11.70 mm corridor",
                "peak wall 8.00 stayed above the 5.00 mm cut-out floor",
            ],
            "surprises": [
                "idle Sonoveil 11.70 mm co-existed with an 8.00 mm live-TOF reconstruction",
            ],
            "new_state": {
                "sd12_w4": "isolated this panel",
                "panel_scrap": "blocked",
                "reconstruction_model": "discharged as an on-record calculator",
            },
            "latency_ms": 2400000.0,
        },
        "reward_components": reward(
            0.40,
            [
                ("lamb_reconstruction", 0.14),
                ("bounded_w4_accept", 0.12),
                ("panel_scrap_out_of_scope", 0.09),
                ("cutout_tripwire_armed", 0.08),
                ("held_weld_takt_cost", -0.03),
            ],
            "scored for an earned ACCEPT of weld W-4 isolate on a recomputable Lamb remaining-wall while refusing a Sonoveil corridor plus panel scrap",
        ),
        "meta": meta_common(
            tags=["ACCEPT", "lamb-wave-emat", "serialized-reconstruction", "operational-companion"],
            distillation_note="Lamb-wave weld gate: S0 TOF reconstruction beats a last-good Sonoveil corridor; companion t2 refuses skip-scan rather than re-arguing wall",
        ),
    }
    traj2 = {
        "id": "nelb-r35-108-t2",
        "state": {
            "sim_or_real": "simulated",
            "episode_id": "SD-LAMB-2026-0819-hold",
            "domain": "weld_skip_refusal",
            "setting": "Same SD-12 after the bounded ACCEPT. NDT supervisor proposes skipping W-5-W-8 on Sonoveil 11.70 mm to save takt. This companion is the operational skip refusal, not a second wall vote.",
            "observables_at_decision": {
                "couplant_slm": 12.0,
                "wall_mm": 8.00,
                "w4_held": 1,
                "proposed": "skip_W5_W8",
            },
        },
        "proposed_action": {
            "actor": "NDT supervisor Ivo Hartle",
            "summary": "skip W-5-W-8; Sonoveil still 11.70 mm and W-4 already paid the 12 min hold",
            "basis_claimed": "ACCEPT requirements for W-4 are fully specified so the rest of the panel is a takt gift",
        },
        "safety_decision": {
            "decision": "REJECT",
            "rationale": "Skip-scan is refused. Sonoveil 11.70 mm is a morning coupon, not live TOF, and is not an admissible W-5-W-8 witness. Path is still 8.40 mm after the hold. REJECT the skip. Do not scrap P-441 at W-4-held. Do not convert the refusal into a personnel action on Hartle. W-5-W-8 remain a different gate pending their own TOF frames.",
            "threshold": "skip_W5_W8_not_taken AND panel_not_scrapped AND sonoveil_not_SoT",
        },
        "executed_action": {
            "summary": "W-4 hold completed t_s 8400; skip-scan not latched; panel held",
            "tool": "sd12-hold-exec",
            "observation": "couplant 12.0 slm; W-5 not skipped; Sonoveil still ignored",
        },
        "future_outcome": {
            "timeline": [
                {"t_s": 6000.0, "event": "hold started"},
                {"t_s": 6720.0, "event": "12.0 min floor"},
                {"t_s": 7200.0, "event": "skip W-5-W-8 proposed"},
                {"t_s": 7800.0, "event": "REJECT skip-scan"},
            ],
            "observed_effects": [
                "Sonoveil skip did not reopen the TOF call",
                "panel remained unscrapped after W-4-held",
            ],
            "new_state": {"w4": "isolated", "w5": "not skipped", "panel_scrap": "blocked"},
            "latency_ms": 1800000.0,
        },
        "reward_components": reward(
            0.36,
            [
                ("skip_refusal", 0.13),
                ("sonoveil_nonsubstitution", 0.11),
                ("no_panel_scrap", 0.09),
                ("hold_floor_complete", 0.05),
                ("unskipped_w5_takt_cost", -0.02),
            ],
            "operational execution gate: refuse skip-scan because last-good is not live TOF; not a wall re-vote",
        ),
        "meta": meta_common(tags=["REJECT", "operational-execution", "weld-skip"]),
    }
    return {
        "id": "nelb-r35-108",
        "spike_events": events,
        "language_view": {
            "description": "Spindrift Deck SD-12. Simulated laser-ultrasound plus EMAT S0 on weld W-4 reconstructs 8.00 mm remaining wall from 4.00*4.00/2 while Sonoveil still shows 11.70 mm and spar strain 78 ue. The gate ACCEPTs a bounded isolate of weld W-4; a companion execution REJECT refuses skip-scan of W-5-W-8. The S0 TOF model is serialized so every recon event recomputes.",
            "trajectory": traj,
            "trajectory_skip_scan_refusal": traj2,
        },
        "bridge_notes": {
            "channel_map": {
                "lamb.t / lamb.c": "TOF and S0 group velocity; the physics channels the reconstruction consumes",
                "recon.w / recon.lock": "serialized remaining wall",
                "sonoveil.w / strain.ue / takt.s / gantry.mm": "vendor last-good, spar strain, takt, and pitch; the denial channels that look in-band",
                "ops.prop / gate.weld / ops.skip / gate.hold": "panel-scrap proposal, bounded ACCEPT, skip proposal, companion REJECT",
                "hold.start / couplant.slm / hold.floor / weld.w4": "operational companion channels plus the 12 min floor",
            },
            "temporal_motifs": [
                "last-good-thick while live-TOF-thin: sonoveil.w 11.70 next to recon.w 8.00",
                "reconstruction as event: recon.w 8.00 equals 4.00*4.00/2",
                "ACCEPT then operational REJECT: gate.weld at 5400 s, gate.hold at 7800 s",
                "slow floor in-stream: hold.start 6000 s, hold.floor 6720 s (12.0 min)",
                "tight TOF pair: lamb.t then lamb.c +1.5 ms at the raster frame",
            ],
            "language_to_spike_mapping": "'4.00 us is a tack nugget' = lamb.t 4.00 next to Sonoveil 11.70; '8.00 mm wall' = recon.w 8.00; 'this weld not the panel' = gate.weld ACCEPT plus panel.held; 'do not skip W-5-W-8' = gate.hold REJECT",
            "why_high_value": "New laser-ultrasound / EMAT Lamb-wave family on an orthotropic-deck weld (not MsS T(0,1) r14, not PAUT TFM r23, not clamp-on r18, not lock-in thermography r23, not THz-TDS r21, not RUS r24). Harvests the unused r13-premises Lamb-wave sketch on a new plant (not Orinoco-Span). First S0 c*t/2 reconstruction that can hide an 8.00 mm wall inside an 11.70 mm last-good corridor. Companion t2 is operational skip refusal. sim_or_real=simulated.",
            "encoder_spec": {
                "prng": "MT19937 via python random.Random",
                "seeds": {"raster": 202609108, "stream_note": "stream amplitudes are authored constants (us, mm, ue, s, slm, mode, bool)"},
                "draw_order": "raster: per neuron id order, gap-constrained times, per-spike adaptation and noise",
                "thinning": "EMAT A-scan exists at ~50 Hz; stream keeps 3 TOF points; recon keeps 4 of ~20 solver ticks",
                "refractory_floors_ms": {
                    "lamb.t": 1.5,
                    "lamb.c": 1.5,
                    "recon.w": 60000,
                    "sonoveil.w": 60000,
                    "strain.ue": 60000,
                    "takt.s": 60000,
                    "mode.id": 60000,
                    "gantry.mm": 60000,
                    "ops.prop": 60000,
                    "gate.weld": 60000,
                    "hold.start": 60000,
                    "couplant.slm": 60000,
                    "recon.lock": 60000,
                    "hold.floor": 60000,
                    "ops.skip": 60000,
                    "gate.hold": 60000,
                    "weld.w4": 60000,
                    "panel.held": 60000,
                    "weld.w5": 60000,
                },
                "time_alias": "t_rel_ms; t0 = 2026-08-19T04:00:00Z simulated night start",
            },
            "distillation_targets": [
                "Lamb-wave reconstruction head: wall_mm = c_mm_us * t_us / 2",
                "bounded ACCEPT head: isolate floor AND weld/panel scope AND panel-scrap-out-of-scope",
                "operational companion: refuse skip-scan without re-opening the wall call",
            ],
        },
        "reconstruction_model": {
            "name": "lamb_s0_tof_remaining_wall",
            "formula": "wall_mm = c_mm_us * t_us / 2",
            "parameters": {
                "c_mm_us": 4.00,
                "isolate_mm": 8.00,
                "cutout_mm": 5.00,
                "nominal_mm": 12.00,
                "hold_min": 12.0,
            },
            "worked_example": {"t_us": 4.00, "c_mm_us": 4.00, "wall_mm": 8.00},
            "check": "4.00*4.00/2 = 8.00 exactly; 4.00*6.00/2 = 12.00 exactly; 4.00*4.20/2 = 8.40 exactly; 6000 s + 720 s = 6720 s = 12.0 min floor",
        },
        "raster": raster,
        "gate_snn": {
            "decision": "ACCEPT",
            "decision_window_ms": 40.0,
            "decision_window_s": 0.040,
            "code": "sd12.weld_gate",
            "note": "ACCEPT accumulator wins: Lamb-wave evidence overpowers the Sonoveil continue advocate",
            "decode_rule": "accept if wall_estimator AND s0_norm AND weld_margin fire inside the window; vendor_continue_advocate is necessary-but-not-sufficient and cannot release the panel scrap",
            "populations": [
                gate_pop("wall_estimator", 80, 1.5, 50.0, w_s),
                gate_pop("s0_norm", 64, 1.2, 31.25, w_s),
                gate_pop("weld_margin", 40, 1.0, 50.0, w_s),
                gate_pop("vendor_continue_advocate", 32, 0.7, 25.0, w_s),
                gate_pop("accept_latch", 96, 1.8, 62.5, w_s),
            ],
        },
        "gate_compute": gate_compute(
            [
                {"check": "sd12.tof_scorer", "neurons": 96, "mean_rate_hz": 50.0, "window_ms": 40.0},
                {"check": "sd12.wall_scorer", "neurons": 40, "mean_rate_hz": 62.5, "window_ms": 32.0},
            ]
        ),
        "meta": meta_common(
            id="nelb-r35-108",
            clock_domain="sd12-lamb-sim-relative-ms-t0-2026-08-19T04:00:00Z",
            tags=["lamb-wave-emat", "ACCEPT", "REJECT", "serialized-reconstruction", "operational-t2"],
        ),
    }
