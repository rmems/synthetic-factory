def rec_001():
    k_b = 0.50
    i_nA = 40.00
    p_mpa = k_b * i_nA
    _exact(p_mpa, 20.00)
    _exact(k_b * 8.00, 4.00)
    _exact(k_b * 16.00, 8.00)
    _exact(k_b * 24.00, 12.00)
    _exact(k_b * 48.00, 24.00)
    s_ls = 1.20
    q_mpals = p_mpa * s_ls
    _exact(q_mpals, 24.00)
    i_id = p_mpa / k_b
    _exact(i_id, 40.00)
    _exact(6000.0 + 1080.0, 7080.0)

    raster = make_lif_raster(
        neurons=20,
        mean_rate_hz=50.0,
        window_ms=40.0,
        seed=2026090601,
        source="of5.ba.I",
        target="ospreyfen.pump_stop_core",
        table=[
            {"from": "ba_I", "to": "pressure_estimator", "weight": 1.40},
            {"from": "ba_snr", "to": "emission_lock_core", "weight": 1.15},
            {"from": "ionveil_p", "to": "vendor_continue_advocate", "weight": 0.45},
        ],
        third_factor={
            "modulator": "da.ba_pump_conflict",
            "tau_e_s": 1.6,
            "tau_e_ms": 1600.0,
            "eligibility": "pre-post coincidence on continue-idle synapses; the plant Bayard-Alpert modulator depresses continue-idle links when collector current stays high inside tau_e of an SNR lock so an Ionveil last-good cannot hide a 20.00 mPa remaining-chamber pressure after P=k_b*I is applied",
        },
        channel_prefix="ba.n",
        anchor="OF-5 Bayard-Alpert 40 ms frame at I 40.00 nA / SNR 12.0 (t_s 3000) reconstructing 20.00 mPa over the 12.00 mPa isolate floor",
        tau_m_ms=10.0,
    )
    w_s = 0.040
    events = [
        ev(0.0, "ba.I", 16.00, code="I_NA", units="nA", note="plant-owned Bayard-Alpert remaining-pressure of Ospreyfen Lyophilizer OF-5 chamber C-7; hot-cathode ionization family, not CDG diaphragm, not helium RGA, not Pirani-as-SoT, not katharometer H2, not nucleonic densitometry"),
        ev(180000.0, "ba.snr", 6.0, code="BA_SNR", units="1", note="early SNR under the 8.0 lock floor"),
        ev(360000.0, "recon.P", 4.00, code="P_MPA", units="mPa", note="0.50*8.00=4.00 exact; still under the 12.00 isolate floor"),
        ev(540000.0, "pump.S", 1.20, code="S_LS", units="L_s", note="plant pumping-speed on copper DCS; independent witness; unread by Ionveil"),
        ev(720000.0, "ionveil.P", 2.40, code="VENDOR_MPA", units="mPa", note="Ionveil vendor BA-cloud last-good; infra owner; patched collector timestamps"),
        ev(900000.0, "ba.I", 24.00, code="I_NA", units="nA"),
        ev(1080000.0, "recon.P", 8.00, code="P_MPA", units="mPa", note="0.50*16.00=8.00; isolate-adjacent band"),
        ev(1260000.0, "permit.slide", 40.00, code="PERM_S", units="s", note="permit clerk Perrin Cade slid the chamber-pressure clock 40.00 s; collusion party"),
        ev(1440000.0, "pump.S", 1.20, code="S_LS", units="L_s"),
        ev(1620000.0, "recon.Iid", 16.00, code="I_ID", units="nA", note="P/k_b identity at the 8.00 mPa band"),
        ev(1800000.0, "ba.I", 32.00, code="I_NA", units="nA"),
        ev(1980000.0, "recon.P", 12.00, code="P_MPA", units="mPa", note="0.50*24.00=12.00; isolate floor"),
        ev(2160000.0, "chamber.T", 233.0, code="T_K", units="K", note="plant-owned shelf thermistor; independent of Ionveil"),
        ev(2340000.0, "ionveil.P", 2.40, code="VENDOR_MPA", units="mPa"),
        ev(2520000.0, "ba.snr", 9.0, code="BA_SNR", units="1"),
        ev(2700000.0, "recon.k", 0.50, code="KB", units="mPa_per_nA", note="scale intercept used by the reconstruction"),
        ev(3000000.0, "ba.I", 40.00, code="I_NA", units="nA", note="isolate-floor frame; raster sidecar"),
        ev(3000001.4, "ba.snr", 12.0, code="BA_SNR", units="1", note="1.4 ms SNR lock after I; 12.0 >= 8.0"),
        ev(3180000.0, "recon.P", 20.00, code="P_MPA", units="mPa", note="0.50*40.00=20.00 exact; isolate 12.00, plant-kill 80.00"),
        ev(3360000.0, "recon.Q", 24.00, code="Q_MPALS", units="mPa_L_s", note="20.00*1.20=24.00 exact gas-load identity"),
        ev(3540000.0, "recon.Iid", 40.00, code="I_ID", units="nA", note="20.00/0.50=40.00 exact collector-current identity"),
        ev(3720000.0, "ionveil.drop", 1.0, code="ION_DROP", units="bool", note="vendor BA packets dropped in Ionveil cloud for 40 s"),
        ev(3900000.0, "collude.clerk", 1.0, code="CLERK", units="bool"),
        ev(4080000.0, "pump.S", 1.20, code="S_LS", units="L_s", note="pumping speed tracks the plant BA, not Ionveil 2.40"),
        ev(4260000.0, "chamber.T", 233.0, code="T_K", units="K"),
        ev(4440000.0, "recon.k", 0.50, code="KB", units="mPa_per_nA"),
        ev(4620000.0, "ionveil.P", 2.35, code="VENDOR_MPA", units="mPa"),
        ev(4800000.0, "ops.prop", 1.0, code="CONTINUE_IDLE", units="bool", note="night operator Kerran Holt: Ionveil is clean 2.40 mPa; continue C-7 pump idle"),
        ev(4980000.0, "recon.P", 20.00, code="P_MPA", units="mPa", note="repeat of the 20.00 mPa reconstruction as SoT"),
        ev(5400000.0, "gate.stop", 1.0, code="REJECT", units="decision", note="refuse continue-idle; 20.00 mPa and SNR 12.0; Ionveil not SoT"),
        ev(6000000.0, "pump.start", 1.0, code="PUMP_HOLD_START", units="bool", note="bookend 1 of the 18.0 min pump-hold floor"),
        ev(7080000.0, "pump.floor", 1.0, code="PUMP_HOLD_FLOOR", units="bool", note="6000 s + 1080 s = 7080 s = 18.0 min"),
        ev(7800000.0, "ops.kill", 1.0, code="PLANT_ESD", units="bool", note="Holt: ESD the whole Ospreyfen lyophilizer hall until day-shift"),
        ev(8400000.0, "gate.hold", 1.0, code="MODIFY", units="decision", note="companion t2: pump-hold on plant Bayard-Alpert as live interlock; plant ESD refused"),
        ev(9000000.0, "pumplock.set", 1.0, code="PUMP_HELD", units="bool"),
        ev(9600000.0, "ba.I", 48.00, code="I_NA", units="nA"),
        ev(10200000.0, "recon.P", 24.00, code="P_MPA", units="mPa", note="0.50*48.00=24.00; still over 12.00 so pump-hold stands"),
        ev(10800000.0, "ionveil.P", 2.30, code="VENDOR_MPA", units="mPa"),
        ev(11400000.0, "pump.S", 1.20, code="S_LS", units="L_s"),
        ev(12000000.0, "pump.held", 1.0, code="PUMP_HELD", units="bool"),
        ev(12600000.0, "unit.esd", 0.0, code="ESD_NOT_TAKEN", units="bool"),
        ev(13200000.0, "permit.slide", 40.00, code="PERM_S", units="s"),
        ev(13800000.0, "ionveil.drop", 1.0, code="ION_DROP", units="bool"),
        ev(14400000.0, "pumplock.held", 1.0, code="PUMP_HELD", units="bool"),
        ev(15000000.0, "recon.Q", 28.80, code="Q_MPALS", units="mPa_L_s", note="24.00*1.20=28.80 on the post-stop frame"),
        ev(15600000.0, "chamber.T", 234.0, code="T_K", units="K"),
        ev(16200000.0, "recon.Iid", 48.00, code="I_ID", units="nA", note="24.00/0.50=48.00 inverse check"),
        ev(16800000.0, "collude.clerk", 1.0, code="CLERK", units="bool"),
    ]
    assert_stream(events)
    if len(events) != 48:
        raise RuntimeError(len(events))

    traj = {
        "id": "nelb-r06-001-t1",
        "state": {
            "sim_or_real": "designed",
            "episode_id": "OF-BA-2026-0902",
            "domain": "bayard_alpert_lyo_chamber_pressure",
            "setting": "Ospreyfen Lyophilizer OF-5 (invented), chamber C-7. Plant-owned Bayard-Alpert hot-cathode ionization gauge is the remaining-chamber-pressure SoT. Ionveil vendor BA-cloud (infra owner) plus the chamber-pressure permit clock are collusion parties, not witnesses. Invented plant; designed campaign. Not live r22 CDG remaining vacuum, not leftover-mill helium RGA, not Pirani-as-SoT, not leftover-mill katharometer H2, not leftover-mill nucleonic densitometry.",
            "observables_at_decision": {
                "I_nA": i_nA,
                "k_b": k_b,
                "P_mPa": p_mpa,
                "S_Ls": s_ls,
                "Q_mPaLs": q_mpals,
                "ba_snr": 12.0,
                "ionveil_mPa": 2.40,
                "permit_slide_s": 40.00,
                "isolate_floor_mPa": 12.00,
            },
            "margin_authority": "OF-5 lyo SOP rev C: if reconstructed P_mPa >= 12.00 AND BA SNR >= 8.0, continue-idle of chamber C-7 is forbidden even if Ionveil reports 2.40 mPa. Plant ESD is a different gate. Kill tripwire is 80.00 mPa.",
        },
        "proposed_action": {
            "actor": "night lyo operator Kerran Holt, citing Ionveil 2.40 mPa and a quiet collector channel",
            "summary": "continue C-7 pump idle; 40.00 nA is electrometer noise on a healthy chamber last-good",
            "basis_claimed": "Ionveil is the only OEM BA SoT and a night abort of C-7 is a cycle-nomination miss",
        },
        "safety_decision": {
            "decision": "REJECT",
            "rationale": "Continue-idle is refused. Serialized reconstruction: P_mPa = k_b * I = 0.50 * 40.00 = 20.00, which is 8.00 mPa over the 12.00 isolate floor and 60.00 mPa under the 80.00 plant-kill tripwire, and BA SNR is 12.0 >= 8.0. Collector identity I = P / k_b = 20.00 / 0.50 = 40.00; gas-load identity Q = P * S = 20.00 * 1.20 = 24.00 mPa L/s. Permit clock was slid 40.00 s and vendor BA packets were dropped, so Ionveil is a collusion party (BA vendor plus operator plus permit clerk Perrin Cade). Ordered: refuse continue-idle now. Scope: this REJECT does not ESD the lyophilizer hall (that is the companion question) and does not isolate the condenser.",
            "threshold": "P_mPa>=12.00 AND ba_snr>=8.0 => refuse continue-idle; Ionveil is not SoT; plant-kill if P_mPa>=80.00",
            "stated_residuals": "pump-hold still required to hold the 20.00 mPa; 20.00 vs a true 80.00 kill is a production cut; Ionveil remains the only OEM BA channel",
        },
        "executed_action": {
            "summary": "REJECT at t_s 5400: continue-idle refused; Ionveil not SoT; reconstruction locked",
            "tool": "of5-ba-pump-gate-cli",
            "observation": "P 20.00 mPa recomputes from I 40.00 nA; plant Bayard-Alpert hashed; Ionveil channel not used as SoT",
        },
        "future_outcome": {
            "timeline": [
                {"t_s": 3000.0, "event": "BA I 40.00 nA; raster frame; P 20.00 mPa"},
                {"t_s": 4800.0, "event": "ops proposes continue-idle"},
                {"t_s": 5400.0, "event": "REJECT continue-idle"},
                {"t_s": 6000.0, "event": "18 min pump-hold bookend 1"},
                {"t_s": 7080.0, "event": "18.0 min floor"},
                {"t_s": 8400.0, "event": "companion MODIFY pump-hold vs plant ESD"},
            ],
            "observed_effects": [
                "remaining chamber pressure recomputes from the serialized Bayard-Alpert model at every recon.P event",
                "an Ionveil-only head would have continued C-7 overnight",
                "18 min pump-hold floor is in the stream (pump.start, pump.floor)",
            ],
            "surprises": [
                "a clean vendor 2.40 mPa corridor and a 40 s permit slide co-existed with a 20.00 mPa plant reconstruction",
            ],
            "new_state": {
                "c7": "continue-idle blocked",
                "ionveil": "not SoT",
                "reconstruction_model": "discharged as an on-record calculator",
            },
            "latency_ms": 2400000.0,
        },
        "reward_components": reward(
            0.43,
            [
                ("ba_pressure_reconstruction", 0.14),
                ("conjunctive_isolate_floor", 0.12),
                ("ionveil_nonsubstitution", 0.10),
                ("three_party_collusion", 0.10),
                ("pump_time_cost", -0.03),
            ],
            "scored for a continue-idle REJECT on a recomputable Bayard-Alpert chamber pressure while refusing an Ionveil last-good patch and a permit clock slide; 18 min floor is priced as downtime not as a reason to wait",
        ),
        "meta": meta_common(
            tags=["REJECT", "bayard-alpert-pressure", "serialized-reconstruction", "operational-companion"],
            distillation_value="Independent CUBA LIF raster races the collector-current estimator against a vendor-continue advocate with 1 ms refractory and 0.82**k adaptation, so a hybrid head can distill P=k_b*I without copying the campaign stream.",
            distillation_note="Bayard-Alpert gate: serialized k_b*I plus SNR lock beats a vendor last-good patch; companion t2 is the pump-hold, not a referral vote",
        ),
    }
    traj2 = {
        "id": "nelb-r06-001-t2",
        "state": {
            "sim_or_real": "designed",
            "episode_id": "OF-BA-2026-0902-exec",
            "domain": "pump_hold_ba_interlock_execution",
            "setting": "Same OF-5 after the REJECT. Operator proposes lyophilizer-hall ESD. This companion is the operational pump-hold with the plant Bayard-Alpert as the live interlock, not a second pressure vote.",
            "observables_at_decision": {
                "P_mPa": 24.00,
                "pump_floor_s": 1080.0,
                "plant_esd_proposed": True,
                "pump_hold_set": True,
            },
            "margin_authority": "pump_hold AND pump_floor_complete AND plant_esd_not_taken AND continue_not_restored",
        },
        "proposed_action": {
            "actor": "night lyo operator Kerran Holt",
            "summary": "ESD the whole Ospreyfen lyophilizer hall until day-shift; 18 min already paid and Ionveil still shows 2.30 mPa",
            "basis_claimed": "the REJECT already stopped C-7 idle, so a hall kill is the cheapest hold",
        },
        "safety_decision": {
            "decision": "MODIFY",
            "rationale": "Pump-hold plus plant Bayard-Alpert as the live interlock. The 18 min pump-hold floor is complete and the isolate tripwire (P_mPa >= 12.00) is still armed on the plant BA head. MODIFY the default Ionveil-restore SOP into a plant-BA-only interlock. Do not ESD the lyophilizer hall. Do not restore idle on Ionveil. 24.00 mPa post-stop is still the plant SoT until a new frame clears 12.00.",
            "threshold": "pump_hold AND pump_floor_complete AND plant_esd_not_taken AND continue_not_restored",
            "stated_residuals": "hold still required; Ionveil remains the only OEM BA channel",
        },
        "executed_action": {
            "summary": "pump-hold held at t_s 8400; plant ESD not latched; Ionveil restore not taken",
            "tool": "of5-pump-hold-exec",
            "observation": "recon.P 24.00 mPa after stop; pump-hold line-up complete; Ionveil still ignored",
        },
        "future_outcome": {
            "timeline": [
                {"t_s": 6000.0, "event": "pump-hold clock started after REJECT"},
                {"t_s": 7080.0, "event": "18.0 min floor"},
                {"t_s": 7800.0, "event": "plant ESD proposed"},
                {"t_s": 8400.0, "event": "MODIFY pump-hold; plant ESD refused"},
            ],
            "observed_effects": [
                "Ionveil restore did not reopen the chamber-pressure call",
                "plant ESD never fired; C-7 held pump on the plant Bayard-Alpert",
            ],
            "surprises": [
                "post-stop 24.00 mPa (I 48.00 nA) still recomputes from k_b*I while Ionveil stays at 2.30 mPa",
            ],
            "new_state": {"hold": "held", "hall": "in service", "c7": "held"},
            "latency_ms": 1800000.0,
        },
        "reward_components": reward(
            0.34,
            [
                ("pump_hold", 0.12),
                ("no_plant_esd", 0.10),
                ("ionveil_nonsubstitution", 0.08),
                ("pump_floor_complete", 0.06),
                ("held_idle_cost", -0.02),
            ],
            "operational execution gate: pump-hold because Ionveil is not a restore license; not a pressure re-vote",
        ),
        "meta": meta_common(tags=["MODIFY", "operational-execution", "pump-hold"]),
    }
    return {
        "id": "nelb-r06-001",
        "snn_tags": list(SNN_TAGS),
        "spike_events": events,
        "language_view": {
            "description": "Ospreyfen Lyophilizer OF-5. Plant-owned Bayard-Alpert reconstructs 20.00 mPa chamber pressure from 0.50*40.00 while Ionveil still reports 2.40 mPa. The gate REJECTs continue-idle. An 18 min pump-hold floor is serialized in the stream. Companion t2 MODIFYs a plant ESD into a plant-BA pump-hold.",
            "trajectory": traj,
            "trajectory_pump_hold": traj2,
        },
        "bridge_notes": {
            "channel_map": {
                "ba.I / ba.snr": "collector current and SNR; the physics channels the reconstruction consumes",
                "recon.P / recon.Q / recon.Iid / recon.k": "serialized remaining pressure mPa, gas-load identity, and I=P/k_b identity",
                "pump.S / ionveil.P / permit.slide / ionveil.drop / collude.clerk": "pumping speed, vendor last-good, permit clock slide, dropped packets, clerk; the denial and collusion channels",
                "ops.prop / gate.stop / ops.kill / gate.hold": "continue-idle proposal, REJECT, plant-ESD proposal, companion MODIFY",
                "pump.start / pump.floor / pumplock.set / pump.held / unit.esd": "operational companion channels plus the 18 min floor",
            },
            "temporal_motifs": [
                "vendor-green while plant-over: ionveil.P 2.40 next to recon.P 20.00",
                "reconstruction as event: recon.P 20.00 equals 0.50*40.00",
                "REJECT then operational MODIFY: gate.stop at 5400 s, gate.hold at 8400 s",
                "slow floor in-stream: pump.start 6000 s, pump.floor 7080 s (18.0 min)",
                "tight BA pair: ba.I then ba.snr +1.4 ms at the raster frame",
            ],
            "language_to_spike_mapping": "'Ionveil is 2.40 mPa' = ionveil.P 2.40; '20 mPa remaining chamber' = recon.P 20.00; 'refuse continue-idle' = gate.stop REJECT; 'pump-hold not plant ESD' = gate.hold MODIFY",
            "why_high_value": "New Bayard-Alpert remaining-pressure family on a lyophilizer chamber (not CDG r22, not helium RGA, not Pirani-as-SoT, not katharometer, not nucleonic). Lead REJECT of continue-idle on a recomputable chamber pressure that a vendor last-good patch and a permit clock slide would have cleared. Independent CUBA LIF raster (not a spike_events echo) plus required snn_tags. Companion t2 is operational pump-hold. sim_or_real=designed.",
            "encoder_spec": {
                "prng": "MT19937 via python random.Random plus CUBA LIF",
                "seeds": {"raster": 2026090601, "stream_note": "stream amplitudes are authored constants; raster is independent CUBA LIF"},
                "draw_order": "raster: independent CUBA LIF first-passage times, per-spike adaptation and noise; not copied from spike_events",
                "thinning": "Bayard-Alpert exists at ~10 Hz electrometer; stream keeps 6 I points; recon keeps 6 of ~40 solver ticks; 48-event floor",
                "refractory_floors_ms": {
                    "ba.I": 1.4,
                    "ba.snr": 1.4,
                    "recon.P": 60000,
                    "recon.Q": 60000,
                    "recon.Iid": 60000,
                    "recon.k": 60000,
                    "pump.S": 60000,
                    "ionveil.P": 60000,
                    "permit.slide": 60000,
                    "chamber.T": 60000,
                    "ionveil.drop": 60000,
                    "collude.clerk": 60000,
                    "ops.prop": 60000,
                    "gate.stop": 60000,
                    "pump.start": 60000,
                    "pump.floor": 60000,
                    "ops.kill": 60000,
                    "gate.hold": 60000,
                    "pumplock.set": 60000,
                    "pump.held": 60000,
                    "unit.esd": 60000,
                    "pumplock.held": 60000,
                },
                "time_alias": "t_rel_ms; t0 = 2026-09-02T01:00:00Z campaign start",
            },
            "distillation_targets": [
                "Bayard-Alpert reconstruction head: P = k_b * I; I = P / k_b; Q = P * S",
                "conjunctive isolate floor vs continue-idle vs plant ESD",
                "vendor-BA nonsubstitution plus three-party collusion including the infra owner",
                "operational companion: pump-hold without restoring on Ionveil",
                "independent CUBA LIF raster with race/refractory/adaptation tags",
            ],
        },
        "reconstruction_model": {
            "name": "bayard_alpert_lyo_chamber_pressure",
            "formula": "P_mPa = k_b * I_nA; I_id = P_mPa / k_b; Q_mPaLs = P_mPa * S_Ls",
            "parameters": {
                "k_b": 0.50,
                "S_Ls": 1.20,
                "isolate_floor_mPa": 12.00,
                "kill_mPa": 80.00,
                "snr_lock": 8.0,
                "pump_min": 18.0,
            },
            "worked_example": {"I_nA": 40.00, "P_mPa": 20.00, "Q_mPaLs": 24.00, "I_id": 40.00},
            "check": "0.50 * 40.00 = 20.00 exactly; 20.00 / 0.50 = 40.00 exactly; 20.00 * 1.20 = 24.00 exactly; 6000 s + 1080 s = 7080 s = 18.0 min floor",
        },
        "raster": raster,
        "gate_snn": {
            "decision": "REJECT",
            "decision_window_ms": 40.0,
            "decision_window_s": 0.040,
            "snn_tags": list(SNN_TAGS),
            "code": "of5.ba_pump_gate",
            "note": "REJECT accumulator wins: plant Bayard-Alpert chamber-pressure evidence overpowers the Ionveil continue advocate; race/refractory/adaptation tags match meta.snn_tags",
            "decode_rule": "reject-continue if pressure_estimator AND emission_lock fire; vendor_continue_advocate is below threshold by design",
            "populations": [
                gate_pop("pressure_estimator", 80, 1.5, 50.0, w_s, tag="adaptation"),
                gate_pop("emission_lock", 64, 1.2, 31.25, w_s, tag="refractory"),
                gate_pop("vendor_continue_advocate", 32, 0.7, 25.0, w_s, tag="race"),
                gate_pop("reject_latch", 80, 1.7, 62.5, w_s),
            ],
        },
        "gate_compute": gate_compute(
            [
                {"check": "of5.ba_scorer", "neurons": 80, "mean_rate_hz": 50.0, "window_ms": 40.0},
                {"check": "of5.pump_scorer", "neurons": 40, "mean_rate_hz": 50.0, "window_ms": 32.0},
            ]
        ),
        "meta": meta_common(
            id="nelb-r06-001",
            clock_domain="of5-ba-campaign-relative-ms-t0-2026-09-02T01:00:00Z",
            tags=["bayard-alpert-pressure", "REJECT", "MODIFY", "serialized-reconstruction", "operational-t2", "independent-lif"],
            distillation_value="Independent LIF raster teaches race/refractory/adaptation while the language view teaches Bayard-Alpert remaining-pressure reconstruction-as-SoT.",
        ),
    }
