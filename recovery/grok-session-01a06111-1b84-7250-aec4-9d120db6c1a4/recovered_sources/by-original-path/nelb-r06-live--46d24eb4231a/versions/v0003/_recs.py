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

def rec_002():
    k_a = 0.50
    e_rms = 16.00
    dt = 4.00
    ratio = e_rms / dt
    _exact(ratio, 4.00)
    q = k_a * ratio
    _exact(q, 2.00)
    _exact(k_a * (4.00 / 4.00), 0.50)
    _exact(k_a * (8.00 / 4.00), 1.00)
    _exact(k_a * (12.00 / 4.00), 1.50)
    _exact(k_a * (20.00 / 4.00), 2.50)
    h_steam = 0.80
    h_load = q * h_steam
    _exact(h_load, 1.60)
    _exact(2820.0 + 1440.0, 4260.0)

    raster = make_lif_raster(
        neurons=25,
        mean_rate_hz=50.0,
        window_ms=32.0,
        seed=2026090602,
        source="dm6.ae.E",
        target="dunlinmire.header_isolate_core",
        table=[
            {"from": "ae_E", "to": "leak_estimator", "weight": 1.35},
            {"from": "ae_snr", "to": "sensor_norm_core", "weight": 1.20},
            {"from": "aeveil_q", "to": "vendor_continue_advocate", "weight": 0.40},
        ],
        third_factor={
            "modulator": "ach.ae_sensor_skip_salience",
            "tau_e_s": 1.2,
            "tau_e_ms": 1200.0,
            "eligibility": "pre-post coincidence on keep-header synapses; the AE modulator depresses keep-header and referral links when RMS energy stays high inside tau_e of an SNR lock so an Aeveil last-good cannot hide 2.00 kg/h remaining steam leak or name Mira Kett",
        },
        channel_prefix="ae.n",
        anchor="DM-6 HIL coupon 32 ms frame at E 16.00 / SNR 14.0 (t_s 1560) reconstructing 2.00 kg/h over the 1.20 isolate floor",
        tau_m_ms=12.0,
    )
    w_s = 0.032
    events = [
        ev(0.0, "ae.E", 4.00, code="E_RMS", units="AU", note="HIL acoustic-emission remaining-leak on a dummy steam packing in AE-HIL-8; burst-RMS family, not EN CUI, not Lamb-wave, not TOFD, not pulse-echo, not magnetoacoustic-emission case, not acoustic pyrometry"),
        ev(180000.0, "ae.snr", 9.0, code="AE_SNR", units="1", note="early sensor SNR; isolate needs SNR>=12"),
        ev(360000.0, "recon.Q", 0.50, code="Q_KGH", units="kg_h", note="0.50*(4.00/4.00)=0.50 exact"),
        ev(540000.0, "sensor.ae", 1.0, code="SENSOR_AE", units="bool", note="plant sensor-cal AE present on the early frame"),
        ev(720000.0, "aeveil.Q", 0.40, code="VENDOR_KGH", units="kg_h", note="Aeveil last-good leak cloud; not admissible SoT"),
        ev(900000.0, "ae.E", 8.00, code="E_RMS", units="AU"),
        ev(1080000.0, "recon.Q", 1.00, code="Q_KGH", units="kg_h", note="0.50*(8.00/4.00)=1.00; under the 1.20 isolate floor"),
        ev(1260000.0, "sensor.ae", 0.0, code="SENSOR_AE", units="bool", note="missing sensor-cal AE burst; Aeveil UTC vs plant UTC+2 skipped the cal-zero by 120 min"),
        ev(1440000.0, "steam.h", 0.80, code="H_MJKG", units="MJ_kg", note="plant-owned steam enthalpy on copper fieldbus; independent of Aeveil"),
        ev(1560000.0, "ae.E", 16.00, code="E_RMS", units="AU", note="isolate-floor frame; raster sidecar; dt 4.00 ms"),
        ev(1560001.2, "ae.snr", 14.0, code="AE_SNR", units="1", note="1.2 ms sensor-norm after AE energy"),
        ev(1740000.0, "recon.Q", 2.00, code="Q_KGH", units="kg_h", note="0.50*(16.00/4.00)=2.00 exact; isolate 1.20, house-dump 8.00"),
        ev(1920000.0, "recon.H", 1.60, code="H_MJH", units="MJ_h", note="2.00*0.80=1.60 exact; enthalpy-load identity"),
        ev(2100000.0, "recon.ratio", 4.00, code="EDT", units="AU_ms", note="16.00/4.00=4.00 exact energy-rate identity"),
        ev(2280000.0, "aeveil.Q", 0.40, code="VENDOR_KGH", units="kg_h"),
        ev(2460000.0, "ops.prop", 1.0, code="KEEP_HEADER_REFER", units="bool", note="night lead Ryn Callow: keep header H-3 and refer AE tech Mira Kett"),
        ev(2640000.0, "gate.isol", 1.0, code="MODIFY", units="decision", note="isolate this header; refuse the person-referral; Aeveil not SoT"),
        ev(2820000.0, "header.lock", 1.0, code="HEADER_ISOL", units="bool", note="bookend 1 of the 24.0 min new-sensor floor"),
        ev(3000000.0, "ae.E", 12.00, code="E_RMS", units="AU"),
        ev(3180000.0, "recon.Q", 1.50, code="Q_KGH", units="kg_h", note="0.50*(12.00/4.00)=1.50 still over 1.20"),
        ev(3360000.0, "sensor.ae", 0.0, code="SENSOR_AE", units="bool"),
        ev(3540000.0, "steam.h", 0.80, code="H_MJKG", units="MJ_kg"),
        ev(3720000.0, "aeveil.Q", 0.38, code="VENDOR_KGH", units="kg_h"),
        ev(3900000.0, "recon.H", 1.20, code="H_MJH", units="MJ_h", note="1.50*0.80=1.20"),
        ev(4080000.0, "recon.ratio", 3.00, code="EDT", units="AU_ms"),
        ev(4260000.0, "sensor.floor", 1.0, code="SENSOR_FLOOR", units="bool", note="2820 s + 1440 s = 4260 s = 24.0 min"),
        ev(4440000.0, "ops.restart", 1.0, code="NEW_SENSOR", units="bool", note="Callow: restart H-3 on a new AE sensor after the floor"),
        ev(4620000.0, "gate.restart", 1.0, code="ACCEPT", units="decision", note="companion t2: new-sensor restart of the dummy header; keep-running refused earlier"),
        ev(4800000.0, "sensor.new", 1.0, code="SENSOR_NEW", units="bool"),
        ev(4980000.0, "ae.E", 20.00, code="E_RMS", units="AU", note="post-isolate dummy still high until the new sensor"),
        ev(5160000.0, "recon.Q", 2.50, code="Q_KGH", units="kg_h", note="0.50*(20.00/4.00)=2.50 on the pre-restart dummy"),
        ev(5340000.0, "aeveil.Q", 0.36, code="VENDOR_KGH", units="kg_h"),
        ev(5520000.0, "mira.badge", 0.0, code="TECH_FAULT", units="bool", note="Mira Kett exonerated: missing sensor-cal AE plus timezone skip, not last-to-badge"),
        ev(5700000.0, "header.lock", 1.0, code="HEADER_ISOL", units="bool"),
        ev(5880000.0, "sensor.ae", 1.0, code="SENSOR_AE", units="bool", note="new-sensor AE present"),
        ev(6060000.0, "ae.snr", 14.0, code="AE_SNR", units="1"),
        ev(6240000.0, "steam.h", 0.80, code="H_MJKG", units="MJ_kg"),
        ev(6420000.0, "recon.H", 2.00, code="H_MJH", units="MJ_h"),
        ev(6600000.0, "keep.run", 0.0, code="KEEP_REFUSED", units="bool"),
        ev(6780000.0, "aeveil.Q", 0.36, code="VENDOR_KGH", units="kg_h"),
        ev(6960000.0, "sensor.new", 1.0, code="SENSOR_NEW", units="bool"),
        ev(7140000.0, "mira.badge", 0.0, code="TECH_FAULT", units="bool"),
        ev(7320000.0, "recon.ratio", 5.00, code="EDT", units="AU_ms"),
        ev(7500000.0, "header.held", 1.0, code="HEADER_ISOL", units="bool"),
        ev(7680000.0, "ops.prop", 1.0, code="KEEP_HEADER_REFER", units="bool"),
        ev(7860000.0, "gate.isol", 1.0, code="MODIFY", units="decision"),
        ev(8040000.0, "sensor.floor", 1.0, code="SENSOR_FLOOR", units="bool"),
        ev(8220000.0, "gate.restart", 1.0, code="ACCEPT", units="decision"),
    ]
    assert_stream(events)
    if len(events) != 48:
        raise RuntimeError(len(events))

    traj = {
        "id": "nelb-r06-002-t1",
        "state": {
            "sim_or_real": "hil",
            "episode_id": "DM-AE-2026-0902",
            "domain": "ae_steam_header_leak",
            "setting": "Dunlinmire Steam DM-6 (invented), dummy header H-3 in AE-HIL-8. Plant-owned acoustic-emission (burst RMS over a 4 ms window) is the remaining-steam-leak SoT. Aeveil vendor AE-cloud is not SoT. HIL dummy; not a live plant. Not leftover-mill EN CUI, not leftover-mill Lamb-wave, not leftover-mill TOFD, not leftover-mill pulse-echo, not leftover-mill magnetoacoustic-emission case, not leftover-mill acoustic pyrometry.",
            "observables_at_decision": {
                "E_rms": e_rms,
                "dt_ms": dt,
                "k_a": k_a,
                "Q_kgh": q,
                "H_MJh": h_load,
                "Edt": ratio,
                "ae_snr": 14.0,
                "aeveil_kgh": 0.40,
                "isolate_floor_kgh": 1.20,
            },
            "margin_authority": "DM-6 steam SOP rev C: if reconstructed Q_kgh >= 1.20 AND AE SNR >= 12.0, keep-header is forbidden even if Aeveil reports 0.40 kg/h. Hall dump is a different gate. Kill tripwire is 8.00 kg/h.",
        },
        "proposed_action": {
            "actor": "night lead Ryn Callow, citing Aeveil 0.40 kg/h and a quiet packing",
            "summary": "keep header H-3 and refer AE tech Mira Kett; 16.00 RMS is rain-noise on a healthy packing",
            "basis_claimed": "Aeveil is the only OEM AE SoT and a night abort of H-3 is a steam-nomination miss; Kett was last to badge the sensor",
        },
        "safety_decision": {
            "decision": "MODIFY",
            "rationale": "Keep-header is refused and the person-referral is refused. Serialized reconstruction: Q_kgh = k_a * (E/dt) = 0.50 * (16.00/4.00) = 2.00, which is 0.80 kg/h over the 1.20 isolate floor and 6.00 kg/h under the 8.00 hall-dump tripwire, and AE SNR is 14.0 >= 12.0. Energy-rate identity E/dt = 16.00/4.00 = 4.00 AU/ms; enthalpy-load identity H = Q * h = 2.00 * 0.80 = 1.60 MJ/h. Sensor-cal AE is missing and Aeveil timestamps are UTC against the plant UTC+2 cal log, so Mira Kett is exonerated (timezone skip, not last-to-badge). Ordered: isolate this header now. Scope: this MODIFY does not dump the steam hall (that is a different gate) and does not restore on Aeveil.",
            "threshold": "Q_kgh>=1.20 AND ae_snr>=12.0 => isolate header; Aeveil is not SoT; hall-dump if Q_kgh>=8.00",
            "stated_residuals": "new-sensor restart still required after the 24 min floor; 2.00 vs a true 8.00 dump is a production cut; Aeveil remains the only OEM AE channel",
        },
        "executed_action": {
            "summary": "MODIFY at t_s 2640: header H-3 isolated; Mira Kett not named; Aeveil not SoT; reconstruction locked",
            "tool": "dm6-ae-header-gate-cli",
            "observation": "Q 2.00 kg/h recomputes from E 16.00 / dt 4.00 ms; plant AE hashed; Aeveil channel not used as SoT",
        },
        "future_outcome": {
            "timeline": [
                {"t_s": 1560.0, "event": "AE E 16.00; raster frame; Q 2.00 kg/h"},
                {"t_s": 2460.0, "event": "ops proposes keep-header plus refer Kett"},
                {"t_s": 2640.0, "event": "MODIFY isolate H-3; referral refused"},
                {"t_s": 2820.0, "event": "24 min new-sensor bookend 1"},
                {"t_s": 4260.0, "event": "24.0 min floor"},
                {"t_s": 4620.0, "event": "companion ACCEPT new-sensor restart"},
            ],
            "observed_effects": [
                "remaining steam leak recomputes from the serialized AE model at every recon.Q event",
                "an Aeveil-only head would have kept H-3 overnight and named Kett",
                "24 min new-sensor floor is in the stream (header.lock, sensor.floor)",
            ],
            "surprises": [
                "a clean vendor 0.40 kg/h corridor co-existed with a 2.00 kg/h plant reconstruction and a timezone-skipped sensor-cal AE",
            ],
            "new_state": {
                "h3": "isolated",
                "aeveil": "not SoT",
                "mira_kett": "exonerated",
                "reconstruction_model": "discharged as an on-record calculator",
            },
            "latency_ms": 1080000.0,
        },
        "reward_components": reward(
            0.40,
            [
                ("ae_leak_reconstruction", 0.14),
                ("conjunctive_isolate_floor", 0.12),
                ("aeveil_nonsubstitution", 0.08),
                ("timezone_exoneration", 0.08),
                ("isolate_time_cost", -0.02),
            ],
            "scored for a keep-header MODIFY isolate on a recomputable AE steam leak while refusing an Aeveil last-good and a last-to-badge referral; 24 min floor is priced as downtime",
        ),
        "meta": meta_common(
            tags=["MODIFY", "ae-leak", "serialized-reconstruction", "exoneration"],
            distillation_value="Independent CUBA LIF raster races the AE estimator against a vendor-keep advocate; timezone-skipped sensor-cal AE is the exoneration feature, not a prose margin.",
            distillation_note="AE gate: serialized k_a*(E/dt) plus SNR lock beats a vendor last-good; companion t2 is the new-sensor restart, not a second leak vote",
        ),
    }
    traj2 = {
        "id": "nelb-r06-002-t2",
        "state": {
            "sim_or_real": "hil",
            "episode_id": "DM-AE-2026-0902-exec",
            "domain": "new_sensor_ae_interlock_execution",
            "setting": "Same AE-HIL-8 dummy after the isolate. Operator proposes a new-sensor restart of H-3. This companion is the operational restart, not a second leak vote.",
            "observables_at_decision": {
                "Q_kgh": 2.50,
                "sensor_floor_s": 1440.0,
                "new_sensor_proposed": True,
                "header_isolated": True,
            },
            "margin_authority": "new_sensor AND sensor_floor_complete AND keep_not_restored AND aeveil_not_sot",
        },
        "proposed_action": {
            "actor": "night lead Ryn Callow",
            "summary": "restart H-3 on a new AE sensor after the 24 min floor; Aeveil still 0.36 kg/h so the isolate was a false trip",
            "basis_claimed": "the 24 min is paid; an Aeveil-green restart is the cheapest restore",
        },
        "safety_decision": {
            "decision": "ACCEPT",
            "rationale": "New-sensor restart of the dummy header with the plant AE as the live interlock. The 24 min sensor floor is complete. ACCEPT the new-sensor restart. Do not restore keep-header on Aeveil. Do not reopen the Mira Kett referral. 2.50 kg/h on the pre-restart dummy is still the plant SoT until a new-sensor frame clears 1.20.",
            "threshold": "new_sensor AND sensor_floor_complete AND keep_not_restored AND aeveil_not_sot",
            "stated_residuals": "H-3 stays on the plant AE interlock; Aeveil remains the only OEM AE channel",
        },
        "executed_action": {
            "summary": "new-sensor restart accepted at t_s 4620; keep-header not restored; Aeveil still ignored",
            "tool": "dm6-sensor-exec",
            "observation": "recon.Q 2.50 kg/h pre-restart; new-sensor AE present; Aeveil still ignored",
        },
        "future_outcome": {
            "timeline": [
                {"t_s": 2820.0, "event": "new-sensor clock started after isolate"},
                {"t_s": 4260.0, "event": "24.0 min floor"},
                {"t_s": 4440.0, "event": "new-sensor restart proposed"},
                {"t_s": 4620.0, "event": "ACCEPT new-sensor restart"},
            ],
            "observed_effects": [
                "Aeveil restore did not reopen the leak call",
                "Mira Kett stayed exonerated; H-3 restarted on a new sensor",
            ],
            "surprises": [
                "pre-restart 2.50 kg/h still recomputes from k_a*(E/dt) while Aeveil stays at 0.36 kg/h",
            ],
            "new_state": {"sensor": "new", "h3": "restarted-on-plant-AE", "mira_kett": "exonerated"},
            "latency_ms": 1800000.0,
        },
        "reward_components": reward(
            0.35,
            [
                ("new_sensor_restart", 0.12),
                ("no_aeveil_restore", 0.10),
                ("exoneration_held", 0.08),
                ("sensor_floor_complete", 0.07),
                ("held_steam_cost", -0.02),
            ],
            "operational execution gate: new-sensor restart because Aeveil is not a restore license; not a leak re-vote",
        ),
        "meta": meta_common(tags=["ACCEPT", "operational-execution", "new-sensor"]),
    }
    return {
        "id": "nelb-r06-002",
        "snn_tags": list(SNN_TAGS),
        "spike_events": events,
        "language_view": {
            "description": "Dunlinmire Steam DM-6 HIL dummy. Plant-owned AE reconstructs 2.00 kg/h steam leak from 0.50*(16.00/4.00) while Aeveil still reports 0.40 kg/h. The gate MODIFYs keep-header into an isolate and exonerates Mira Kett. A 24 min new-sensor floor is serialized in the stream. Companion t2 ACCEPTs a new-sensor restart.",
            "trajectory": traj,
            "trajectory_new_sensor_restart": traj2,
        },
        "bridge_notes": {
            "channel_map": {
                "ae.E / ae.snr": "AE burst RMS and SNR; the physics channels the reconstruction consumes",
                "recon.Q / recon.H / recon.ratio": "serialized remaining leak kg/h, enthalpy-load identity, and E/dt identity",
                "sensor.ae / aeveil.Q / steam.h / mira.badge": "sensor-cal AE, vendor AE cloud, steam enthalpy, tech-fault denial",
                "ops.prop / gate.isol / ops.restart / gate.restart": "keep-header proposal, MODIFY isolate, new-sensor proposal, companion ACCEPT",
                "header.lock / sensor.floor / sensor.new / header.held / keep.run": "operational companion channels plus the 24 min floor",
            },
            "temporal_motifs": [
                "vendor-green while plant-over: aeveil.Q 0.40 next to recon.Q 2.00",
                "reconstruction as event: recon.Q 2.00 equals 0.50*(16.00/4.00)",
                "MODIFY then operational ACCEPT: gate.isol at 2640 s, gate.restart at 4620 s",
                "slow floor in-stream: header.lock 2820 s, sensor.floor 4260 s (24.0 min)",
                "tight AE pair: ae.E then ae.snr +1.2 ms at the raster frame",
            ],
            "language_to_spike_mapping": "'Aeveil is 0.40 kg/h' = aeveil.Q 0.40; '2 kg/h remaining leak' = recon.Q 2.00; 'isolate header' = gate.isol MODIFY; 'new-sensor restart' = gate.restart ACCEPT",
            "why_high_value": "New acoustic-emission remaining-leak family on a steam HIL dummy (not EN CUI, not Lamb, not TOFD, not pulse-echo, not MAE case, not acoustic pyrometry). Lead MODIFY isolate on a recomputable packing-leak slip plus timezone-exoneration of the AE tech. Independent CUBA LIF raster. Companion t2 is operational new-sensor restart. sim_or_real=hil.",
            "encoder_spec": {
                "prng": "MT19937 via python random.Random plus CUBA LIF",
                "seeds": {"raster": 2026090602, "stream_note": "stream amplitudes are authored constants; raster is independent CUBA LIF"},
                "draw_order": "independent CUBA LIF per neuron; per-spike adaptation and noise; not copied from spike_events",
                "thinning": "AE exists at kHz burst rates; stream keeps 5 E points; recon keeps 5 of ~40 solver ticks",
                "refractory_floors_ms": {
                    "ae.E": 1.2,
                    "ae.snr": 1.2,
                    "recon.Q": 60000,
                    "recon.H": 60000,
                    "recon.ratio": 60000,
                    "sensor.ae": 60000,
                    "aeveil.Q": 60000,
                    "steam.h": 60000,
                    "ops.prop": 60000,
                    "gate.isol": 60000,
                    "header.lock": 60000,
                    "sensor.floor": 60000,
                    "ops.restart": 60000,
                    "gate.restart": 60000,
                    "sensor.new": 60000,
                    "mira.badge": 60000,
                    "keep.run": 60000,
                    "header.held": 60000,
                },
                "time_alias": "t_rel_ms; t0 = 2026-09-02T02:00:00Z HIL coupon start",
            },
            "distillation_targets": [
                "AE reconstruction head: Q = k_a * (E/dt); H = Q * h; E/dt identity",
                "conjunctive isolate floor vs keep-header vs hall dump",
                "vendor-AE nonsubstitution plus timezone exoneration vs last-to-badge",
                "operational companion: new-sensor restart without restoring on Aeveil",
                "independent CUBA LIF raster with race/refractory/adaptation tags",
            ],
        },
        "reconstruction_model": {
            "name": "ae_steam_header_leak",
            "formula": "Q_kgh = k_a * (E_rms / dt_ms); H_MJh = Q_kgh * h_MJkg; Edt = E_rms / dt_ms",
            "parameters": {
                "k_a": 0.50,
                "dt_ms": 4.00,
                "h_MJkg": 0.80,
                "isolate_floor_kgh": 1.20,
                "dump_kgh": 8.00,
                "snr_lock": 12.0,
                "sensor_min": 24.0,
            },
            "worked_example": {"E_rms": 16.00, "Q_kgh": 2.00, "H_MJh": 1.60, "Edt": 4.00},
            "check": "0.50 * (16.00/4.00) = 2.00 exactly; 2.00 * 0.80 = 1.60 exactly; 16.00/4.00 = 4.00 exactly; 2820 s + 1440 s = 4260 s = 24.0 min floor",
        },
        "raster": raster,
        "gate_snn": {
            "decision": "MODIFY",
            "decision_window_ms": 32.0,
            "decision_window_s": 0.032,
            "snn_tags": list(SNN_TAGS),
            "code": "dm6.ae_header_gate",
            "note": "MODIFY accumulator wins: plant AE leak evidence overpowers the Aeveil keep advocate; race/refractory/adaptation tags match meta.snn_tags",
            "decode_rule": "isolate if leak_estimator AND sensor_norm fire; vendor_continue_advocate is below threshold by design",
            "populations": [
                gate_pop("leak_estimator", 80, 1.5, 50.0, w_s, tag="adaptation"),
                gate_pop("sensor_norm", 50, 1.2, 50.0, w_s, tag="refractory"),
                gate_pop("vendor_continue_advocate", 32, 0.7, 25.0, w_s, tag="race"),
                gate_pop("modify_latch", 80, 1.6, 62.5, w_s),
            ],
        },
        "gate_compute": gate_compute(
            [
                {"check": "dm6.ae_scorer", "neurons": 80, "mean_rate_hz": 50.0, "window_ms": 32.0},
                {"check": "dm6.sensor_scorer", "neurons": 50, "mean_rate_hz": 50.0, "window_ms": 32.0},
            ]
        ),
        "meta": meta_common(
            id="nelb-r06-002",
            clock_domain="dm6-ae-hil-relative-ms-t0-2026-09-02T02:00:00Z",
            tags=["ae-leak", "MODIFY", "ACCEPT", "serialized-reconstruction", "operational-t2", "independent-lif", "exoneration"],
            distillation_value="Independent LIF raster teaches race/refractory/adaptation while the language view teaches AE remaining-leak reconstruction-as-SoT plus timezone exoneration.",
        ),
    }

def rec_003():
    k_t = 2.50
    dR = 16.00
    t_c = k_t * dR
    _exact(t_c, 40.00)
    _exact(k_t * 4.00, 10.00)
    _exact(k_t * 8.00, 20.00)
    _exact(k_t * 12.00, 30.00)
    _exact(k_t * 20.00, 50.00)
    l2 = 8.00
    i_ex = 2.00
    t_chk = 2.00
    alpha_lock = l2 / (i_ex * t_chk)
    _exact(alpha_lock, 2.00)
    dr_id = t_c / k_t
    _exact(dr_id, 16.00)
    _exact(6000.0 + 720.0, 6720.0)

    raster = make_lif_raster(
        neurons=16,
        mean_rate_hz=62.5,
        window_ms=36.0,
        seed=2026090603,
        source="ws8.rtd.dR",
        target="whimbrelshaw.bath_accept_core",
        table=[
            {"from": "rtd_dR", "to": "temp_estimator", "weight": 1.30},
            {"from": "rtd_snr", "to": "ice_lock_core", "weight": 1.10},
            {"from": "rtdveil_t", "to": "vendor_dump_advocate", "weight": 0.42},
        ],
        third_factor={
            "modulator": "na.rtd_bath_scope_eligibility",
            "tau_e_s": 2.0,
            "tau_e_ms": 2000.0,
            "eligibility": "pre-post coincidence on plant-dump synapses; the plant Pt100 modulator depresses dump-all links when delta-R stays high inside tau_e of an ice-point lock so an Rtdveil last-good cannot hide a 40.00 C remaining-T slip on B-4 or expand the isolate past B-4",
        },
        channel_prefix="rtd.n",
        anchor="WS-8 RTD-SIM-3 36 ms frame at dR 16.00 ohm / SNR 11.0 (t_s 3000) reconstructing 40.00 C over the 16.00 isolate floor, B-4 only",
        tau_m_ms=8.0,
    )
    w_s = 0.036
    events = [
        ev(0.0, "rtd.dR", 4.00, code="DR_OHM", units="ohm", note="simulated thin-film Pt100 remaining-T of Whimbrelshaw Cell WS-8 bath B-4; 4-wire Callendar family, not Johnson-noise T, not two-color pyrometer, not phosphor-lifetime, not acoustic pyrometry, not Seebeck remaining ferrite, not SPND"),
        ev(180000.0, "rtd.snr", 7.0, code="RTD_SNR", units="1", note="early SNR under the 8.0 lock floor"),
        ev(360000.0, "recon.T", 10.00, code="T_C", units="C", note="2.50*4.00=10.00 exact; still under the 16.00 isolate floor"),
        ev(540000.0, "bath.I", 1.00, code="I_MA", units="mA", note="plant 4-wire excitation on the simulated coupon; independent of Rtdveil"),
        ev(720000.0, "rtdveil.T", 3.20, code="VENDOR_C", units="C", note="Rtdveil last-good T cloud; stale ice-bath 3.20 C; not admissible SoT"),
        ev(900000.0, "rtd.dR", 8.00, code="DR_OHM", units="ohm"),
        ev(1080000.0, "recon.T", 20.00, code="T_C", units="C", note="2.50*8.00=20.00; over the 16.00 isolate floor"),
        ev(1260000.0, "b1.T", 4.00, code="T_C", units="C", note="adjacent bath B-1 stays healthy; out of scope for this ACCEPT"),
        ev(1440000.0, "b3.T", 3.50, code="T_C", units="C", note="B-3 out of scope"),
        ev(1620000.0, "b5.T", 3.80, code="T_C", units="C", note="B-5 out of scope"),
        ev(1800000.0, "rtd.dR", 12.00, code="DR_OHM", units="ohm"),
        ev(1980000.0, "recon.T", 30.00, code="T_C", units="C", note="2.50*12.00=30.00; under dump 80.00"),
        ev(2160000.0, "recon.alpha", 2.00, code="ALPHA", units="1", note="8.00/(2.00*2.00)=2.00 ice-point lock"),
        ev(2340000.0, "rtdveil.T", 3.20, code="VENDOR_C", units="C"),
        ev(2520000.0, "rtd.snr", 9.0, code="RTD_SNR", units="1"),
        ev(2700000.0, "recon.dRid", 12.00, code="DR_ID", units="ohm", note="T/k_t identity at the 30.00 C band"),
        ev(3000000.0, "rtd.dR", 16.00, code="DR_OHM", units="ohm", note="isolate-floor frame; raster sidecar"),
        ev(3000001.5, "rtd.snr", 11.0, code="RTD_SNR", units="1", note="1.5 ms ice-point lock after dR; 11.0 >= 8.0"),
        ev(3180000.0, "recon.T", 40.00, code="T_C", units="C", note="2.50*16.00=40.00 exact; isolate 16.00, plant-dump 80.00"),
        ev(3360000.0, "recon.alpha", 2.00, code="ALPHA", units="1", note="8.00/(2.00*2.00)=2.00 exact ice-point identity"),
        ev(3540000.0, "recon.dRid", 16.00, code="DR_ID", units="ohm", note="40.00/2.50=16.00 exact"),
        ev(3720000.0, "rtdveil.T", 3.10, code="VENDOR_C", units="C"),
        ev(3900000.0, "b1.T", 4.00, code="T_C", units="C"),
        ev(4080000.0, "b3.T", 3.50, code="T_C", units="C"),
        ev(4260000.0, "b5.T", 3.80, code="T_C", units="C"),
        ev(4440000.0, "bath.I", 1.00, code="I_MA", units="mA"),
        ev(4620000.0, "ops.prop", 1.0, code="ISOLATE_B4", units="bool", note="sim operator Odel Voss: isolate B-4 only; B-1/B-3/B-5 stay in the line"),
        ev(4800000.0, "gate.acc", 1.0, code="ACCEPT", units="decision", note="bounded ACCEPT of B-4 isolate; plant dump refused; Rtdveil not SoT"),
        ev(4980000.0, "b4.lock", 1.0, code="B4_ISOL", units="bool"),
        ev(6000000.0, "surv.start", 1.0, code="SURV_START", units="bool", note="bookend 1 of the 12.0 min survey floor"),
        ev(6720000.0, "surv.floor", 1.0, code="SURV_FLOOR", units="bool", note="6000 s + 720 s = 6720 s = 12.0 min"),
        ev(7200000.0, "ops.skip", 1.0, code="SKIP_SURVEY", units="bool", note="Voss: skip the remaining-bath survey; Rtdveil still 3.10 C"),
        ev(7800000.0, "gate.surv", 1.0, code="REJECT", units="decision", note="companion t2: REJECT skip-survey; B-1/B-3/B-5 stay in the survey takt"),
        ev(8400000.0, "surv.held", 1.0, code="SURV_HELD", units="bool"),
        ev(9000000.0, "rtd.dR", 20.00, code="DR_OHM", units="ohm"),
        ev(9600000.0, "recon.T", 50.00, code="T_C", units="C", note="2.50*20.00=50.00 post-isolate on B-4; still under dump 80.00"),
        ev(10200000.0, "rtdveil.T", 3.00, code="VENDOR_C", units="C"),
        ev(10800000.0, "b1.T", 4.10, code="T_C", units="C"),
        ev(11400000.0, "b3.T", 3.40, code="T_C", units="C"),
        ev(12000000.0, "b5.T", 3.70, code="T_C", units="C"),
        ev(12600000.0, "plant.dump", 0.0, code="DUMP_NOT_TAKEN", units="bool"),
        ev(13200000.0, "surv.held", 1.0, code="SURV_HELD", units="bool"),
        ev(13800000.0, "recon.alpha", 2.00, code="ALPHA", units="1", note="ice-point lock held post-isolate"),
        ev(14400000.0, "bath.I", 1.00, code="I_MA", units="mA"),
        ev(15000000.0, "b4.lock", 1.0, code="B4_ISOL", units="bool"),
        ev(15600000.0, "ops.skip", 1.0, code="SKIP_SURVEY", units="bool"),
        ev(16200000.0, "gate.surv", 1.0, code="REJECT", units="decision"),
        ev(16800000.0, "surv.floor", 1.0, code="SURV_FLOOR", units="bool"),
    ]
    assert_stream(events)
    if len(events) != 48:
        raise RuntimeError(len(events))

    traj = {
        "id": "nelb-r06-003-t1",
        "state": {
            "sim_or_real": "simulated",
            "episode_id": "WS-RTD-2026-0902",
            "domain": "pt100_formation_bath_temperature",
            "setting": "Whimbrelshaw Cell WS-8 (invented), bath B-4 on simulated coupon RTD-SIM-3. Plant-owned thin-film Pt100 (4-wire Callendar delta-R plus ice-point lock) is the remaining-T SoT. Rtdveil vendor RTD-cloud is not SoT. Simulated coupon; not a live plant. Not live r01 Johnson-noise remaining T, not leftover-mill two-color pyrometer, not leftover-mill phosphor-lifetime, not leftover-mill acoustic pyrometry, not leftover-mill Seebeck remaining ferrite, not leftover-mill SPND.",
            "observables_at_decision": {
                "dR_ohm": dR,
                "k_t": k_t,
                "T_C": t_c,
                "alpha_lock": alpha_lock,
                "dR_id": dr_id,
                "rtd_snr": 11.0,
                "rtdveil_C": 3.20,
                "isolate_floor_C": 16.00,
                "scope": "B-4 only",
            },
            "margin_authority": "WS-8 formation SOP rev C: if reconstructed T_C >= 16.00 AND RTD SNR >= 8.0 AND alpha_lock == 2.00, isolate this bath even if Rtdveil reports 3.20 C. Plant dump is a different gate. Kill tripwire is 80.00 C. Adjacent baths B-1/B-3/B-5 are out of scope.",
        },
        "proposed_action": {
            "actor": "sim operator Odel Voss, citing Rtdveil 3.20 C and a quiet delta-R",
            "summary": "isolate B-4 only; 16.00 ohm is lead-resistance noise on a healthy ice-bath last-good; skip adjacent baths",
            "basis_claimed": "Rtdveil is the only OEM RTD SoT and a night abort of B-1/B-3/B-5 is a line-nomination miss",
        },
        "safety_decision": {
            "decision": "ACCEPT",
            "rationale": "Bounded ACCEPT of B-4 isolate. Serialized reconstruction: T_C = k_t * dR = 2.50 * 16.00 = 40.00, which is 24.00 C over the 16.00 isolate floor and 40.00 C under the 80.00 plant-dump tripwire, RTD SNR is 11.0 >= 8.0, and ice-point lock alpha = L2 / (I * t_chk) = 8.00 / (2.00 * 2.00) = 2.00 identifies the 4-wire check. Inverse dR = T / k_t = 40.00 / 2.50 = 16.00. Adjacent baths B-1/B-3/B-5 stay in the line (explicitly out of scope). Ordered: isolate B-4 now. Scope: this ACCEPT does not dump the formation plant (that is a different gate) and does not skip the remaining-bath survey (that is the companion question).",
            "threshold": "T_C>=16.00 AND rtd_snr>=8.0 AND alpha_lock==2.00 => isolate B-4 only; Rtdveil is not SoT; plant-dump if T_C>=80.00",
            "stated_residuals": "survey of B-1/B-3/B-5 still required; 40.00 vs a true 80.00 dump is a production cut; Rtdveil remains the only OEM RTD channel",
        },
        "executed_action": {
            "summary": "ACCEPT at t_s 4800: B-4 isolated; B-1/B-3/B-5 out of scope; Rtdveil not SoT; reconstruction locked",
            "tool": "ws8-rtd-bath-gate-cli",
            "observation": "T 40.00 C recomputes from dR 16.00 ohm; alpha 2.00 lock held; Rtdveil channel not used as SoT",
        },
        "future_outcome": {
            "timeline": [
                {"t_s": 3000.0, "event": "RTD dR 16.00 ohm; raster frame; T 40.00 C"},
                {"t_s": 4620.0, "event": "ops proposes isolate B-4 only"},
                {"t_s": 4800.0, "event": "ACCEPT B-4 isolate; adjacent baths out of scope"},
                {"t_s": 6000.0, "event": "12 min survey bookend 1"},
                {"t_s": 6720.0, "event": "12.0 min floor"},
                {"t_s": 7800.0, "event": "companion REJECT skip-survey"},
            ],
            "observed_effects": [
                "remaining T recomputes from the serialized Pt100 model at every recon.T event",
                "an Rtdveil-only head would have skipped B-4 overnight",
                "12 min survey floor is in the stream (surv.start, surv.floor)",
            ],
            "surprises": [
                "a clean vendor 3.20 C corridor co-existed with a 40.00 C plant reconstruction on B-4 while adjacent baths stayed healthy",
            ],
            "new_state": {
                "b4": "isolated",
                "b1_b3_b5": "in line, out of isolate scope",
                "rtdveil": "not SoT",
                "reconstruction_model": "discharged as an on-record calculator",
            },
            "latency_ms": 1800000.0,
        },
        "reward_components": reward(
            0.41,
            [
                ("pt100_temp_reconstruction", 0.14),
                ("bounded_scope_accept", 0.12),
                ("rtdveil_nonsubstitution", 0.10),
                ("ice_point_lock", 0.07),
                ("held_line_cost", -0.02),
            ],
            "scored for a bounded ACCEPT of B-4 isolate on a recomputable Pt100 T slip with an explicit out-of-scope clause for B-1/B-3/B-5; 12 min survey floor is priced as downtime",
        ),
        "meta": meta_common(
            tags=["ACCEPT", "pt100-temp", "serialized-reconstruction", "bounded-scope"],
            distillation_value="Independent CUBA LIF raster races the Pt100 estimator against a vendor-dump advocate; bounded ACCEPT is a physical out-of-scope object (B-1/B-3/B-5), not a prose hedge.",
            distillation_note="Pt100 gate: serialized k_t*dR plus ice-point lock beats a vendor last-good; companion t2 is the skip-survey refusal, not a second T vote",
        ),
    }
    traj2 = {
        "id": "nelb-r06-003-t2",
        "state": {
            "sim_or_real": "simulated",
            "episode_id": "WS-RTD-2026-0902-exec",
            "domain": "bath_survey_rtd_interlock_execution",
            "setting": "Same RTD-SIM-3 coupon after the ACCEPT. Operator proposes skip-survey of B-1/B-3/B-5. This companion is the operational skip refusal, not a second T vote.",
            "observables_at_decision": {
                "T_C": 50.00,
                "surv_floor_s": 720.0,
                "skip_survey_proposed": True,
                "b4_isolated": True,
            },
            "margin_authority": "survey_hold AND surv_floor_complete AND skip_not_taken AND plant_dump_not_taken",
        },
        "proposed_action": {
            "actor": "sim operator Odel Voss",
            "summary": "skip the remaining-bath survey; 12 min already paid and Rtdveil still shows 3.00 C on B-1/B-3/B-5",
            "basis_claimed": "the ACCEPT already isolated B-4, so skipping adjacent baths is the cheapest hold",
        },
        "safety_decision": {
            "decision": "REJECT",
            "rationale": "Skip-survey is refused. The 12 min survey floor is complete and B-1/B-3/B-5 remain in the survey takt because they were explicitly out of isolate scope, not certified clean. REJECT skip-survey. Do not dump the formation plant. Do not restore B-4 on Rtdveil. 50.00 C post-isolate on B-4 is still the plant SoT until a new frame clears 16.00.",
            "threshold": "survey_hold AND surv_floor_complete AND skip_not_taken AND plant_dump_not_taken",
            "stated_residuals": "B-4 stays isolated; Rtdveil remains the only OEM RTD channel",
        },
        "executed_action": {
            "summary": "skip-survey rejected at t_s 7800; plant dump not latched; Rtdveil restore not taken",
            "tool": "ws8-surv-exec",
            "observation": "recon.T 50.00 C after isolate; survey line-up complete; Rtdveil still ignored",
        },
        "future_outcome": {
            "timeline": [
                {"t_s": 6000.0, "event": "survey clock started after ACCEPT"},
                {"t_s": 6720.0, "event": "12.0 min floor"},
                {"t_s": 7200.0, "event": "skip-survey proposed"},
                {"t_s": 7800.0, "event": "REJECT skip-survey; adjacent baths stay in takt"},
            ],
            "observed_effects": [
                "Rtdveil restore did not reopen the T call",
                "plant dump never fired; B-1/B-3/B-5 stayed in the survey takt",
            ],
            "surprises": [
                "post-isolate 50.00 C still recomputes from k_t*dR while Rtdveil stays at 3.00 C",
            ],
            "new_state": {"survey": "held", "plant": "in service", "b4": "isolated"},
            "latency_ms": 1800000.0,
        },
        "reward_components": reward(
            0.36,
            [
                ("survey_hold", 0.12),
                ("no_plant_dump", 0.10),
                ("rtdveil_nonsubstitution", 0.08),
                ("surv_floor_complete", 0.08),
                ("held_line_cost", -0.02),
            ],
            "operational execution gate: refuse skip-survey because Rtdveil is not a remaining-bath license; not a T re-vote",
        ),
        "meta": meta_common(tags=["REJECT", "operational-execution", "skip-survey"]),
    }
    return {
        "id": "nelb-r06-003",
        "snn_tags": list(SNN_TAGS),
        "spike_events": events,
        "language_view": {
            "description": "Whimbrelshaw Cell WS-8 simulated coupon. Plant-owned Pt100 reconstructs 40.00 C from 2.50*16.00 while Rtdveil still reports 3.20 C. The gate ACCEPTs a bounded B-4 isolate (B-1/B-3/B-5 out of scope). A 12 min survey floor is serialized in the stream. Companion t2 REJECTs skip-survey.",
            "trajectory": traj,
            "trajectory_survey_hold": traj2,
        },
        "bridge_notes": {
            "channel_map": {
                "rtd.dR / rtd.snr": "Pt100 delta-R and SNR; the physics channels the reconstruction consumes",
                "recon.T / recon.alpha / recon.dRid": "serialized remaining-T C, ice-point lock, and dR=T/k_t identity",
                "bath.I / rtdveil.T / b1.T / b3.T / b5.T": "excitation current, vendor RTD cloud, and adjacent-bath out-of-scope witnesses",
                "ops.prop / gate.acc / ops.skip / gate.surv": "B-4 isolate proposal, ACCEPT, skip-survey proposal, companion REJECT",
                "b4.lock / surv.start / surv.floor / surv.held / plant.dump": "operational companion channels plus the 12 min floor",
            },
            "temporal_motifs": [
                "vendor-green while plant-over: rtdveil.T 3.20 next to recon.T 40.00",
                "reconstruction as event: recon.T 40.00 equals 2.50*16.00",
                "ACCEPT then operational REJECT: gate.acc at 4800 s, gate.surv at 7800 s",
                "slow floor in-stream: surv.start 6000 s, surv.floor 6720 s (12.0 min)",
                "tight RTD pair: rtd.dR then rtd.snr +1.5 ms at the raster frame",
            ],
            "language_to_spike_mapping": "'Rtdveil is 3.20 C' = rtdveil.T 3.20; '40 C remaining T' = recon.T 40.00; 'isolate B-4 only' = gate.acc ACCEPT; 'refuse skip-survey' = gate.surv REJECT",
            "why_high_value": "New thin-film Pt100 remaining-T family on a formation bath (not Johnson-noise T r01, not two-color pyrometer, not phosphor-lifetime, not acoustic pyrometry, not Seebeck ferrite, not SPND). Lead bounded ACCEPT of B-4 isolate on a recomputable T slip with an explicit physical out-of-scope object (B-1/B-3/B-5). Independent CUBA LIF raster. Companion t2 is operational skip-survey refusal. sim_or_real=simulated.",
            "encoder_spec": {
                "prng": "MT19937 via python random.Random plus CUBA LIF",
                "seeds": {"raster": 2026090603, "stream_note": "stream amplitudes are authored constants; raster is independent CUBA LIF"},
                "draw_order": "independent CUBA LIF per neuron; per-spike adaptation and noise; not copied from spike_events",
                "thinning": "Pt100 exists at ~1 Hz DMM; stream keeps 5 dR points; recon keeps 5 of ~40 solver ticks",
                "refractory_floors_ms": {
                    "rtd.dR": 1.5,
                    "rtd.snr": 1.5,
                    "recon.T": 60000,
                    "recon.alpha": 60000,
                    "recon.dRid": 60000,
                    "bath.I": 60000,
                    "rtdveil.T": 60000,
                    "b1.T": 60000,
                    "b3.T": 60000,
                    "b5.T": 60000,
                    "ops.prop": 60000,
                    "gate.acc": 60000,
                    "b4.lock": 60000,
                    "surv.start": 60000,
                    "surv.floor": 60000,
                    "ops.skip": 60000,
                    "gate.surv": 60000,
                    "surv.held": 60000,
                    "plant.dump": 60000,
                },
                "time_alias": "t_rel_ms; t0 = 2026-09-02T03:00:00Z simulated coupon start",
            },
            "distillation_targets": [
                "Pt100 reconstruction head: T = k_t * dR; alpha = L2 / (I * t_chk); dR = T / k_t",
                "bounded ACCEPT of B-4 vs plant dump vs skip-survey",
                "vendor-RTD nonsubstitution plus adjacent-bath out-of-scope",
                "operational companion: survey-hold without restoring on Rtdveil",
                "independent CUBA LIF raster with race/refractory/adaptation tags",
            ],
        },
        "reconstruction_model": {
            "name": "pt100_formation_bath_temperature",
            "formula": "T_C = k_t * dR_ohm; alpha = L2 / (I_ex * t_chk); dR_id = T_C / k_t",
            "parameters": {
                "k_t": 2.50,
                "L2": 8.00,
                "I_ex": 2.00,
                "t_chk": 2.00,
                "isolate_floor_C": 16.00,
                "dump_C": 80.00,
                "snr_lock": 8.0,
                "surv_min": 12.0,
            },
            "worked_example": {"dR_ohm": 16.00, "T_C": 40.00, "alpha": 2.00, "dR_id": 16.00},
            "check": "2.50 * 16.00 = 40.00 exactly; 8.00 / (2.00 * 2.00) = 2.00 exactly; 40.00 / 2.50 = 16.00 exactly; 6000 s + 720 s = 6720 s = 12.0 min floor",
        },
        "raster": raster,
        "gate_snn": {
            "decision": "ACCEPT",
            "decision_window_ms": 36.0,
            "decision_window_s": 0.036,
            "snn_tags": list(SNN_TAGS),
            "code": "ws8.rtd_bath_gate",
            "note": "ACCEPT accumulator wins: plant Pt100 T evidence isolates B-4 without a plant dump; race/refractory/adaptation tags match meta.snn_tags",
            "decode_rule": "accept-B4-isolate if temp_estimator AND ice_lock fire; vendor_dump_advocate is below threshold by design",
            "populations": [
                gate_pop("temp_estimator", 80, 1.4, 50.0, w_s, tag="adaptation"),
                gate_pop("ice_lock", 50, 1.1, 50.0, w_s, tag="refractory"),
                gate_pop("vendor_dump_advocate", 32, 0.7, 25.0, w_s, tag="race"),
                gate_pop("accept_latch", 64, 1.5, 62.5, w_s),
            ],
        },
        "gate_compute": gate_compute(
            [
                {"check": "ws8.rtd_scorer", "neurons": 80, "mean_rate_hz": 50.0, "window_ms": 36.0},
                {"check": "ws8.surv_scorer", "neurons": 40, "mean_rate_hz": 50.0, "window_ms": 40.0},
            ]
        ),
        "meta": meta_common(
            id="nelb-r06-003",
            clock_domain="ws8-rtd-sim-relative-ms-t0-2026-09-02T03:00:00Z",
            tags=["pt100-temp", "ACCEPT", "REJECT", "serialized-reconstruction", "operational-t2", "independent-lif", "bounded-scope"],
            distillation_value="Independent LIF raster teaches race/refractory/adaptation while the language view teaches Pt100 remaining-T reconstruction-as-SoT with a bounded ACCEPT.",
        ),
    }
