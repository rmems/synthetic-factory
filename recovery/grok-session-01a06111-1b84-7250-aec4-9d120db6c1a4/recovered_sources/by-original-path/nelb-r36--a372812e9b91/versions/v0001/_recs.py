# ---------------------------------------------------------------------------
# Record 109 — longitudinal BGO Pockels GIS bus voltage, designed,
# MODIFY / ACCEPT
# ---------------------------------------------------------------------------
def rec_109():
    k_eo = 4.00
    i_y = 3.00
    i_x = 12.00
    v_kv = k_eo * (i_x / i_y)
    k_g = 2.50
    gamma_mrad = k_g * v_kv
    _exact(v_kv, 16.00)
    _exact(gamma_mrad, 40.00)
    _exact(k_eo * (6.00 / i_y), 8.00)
    _exact(k_eo * (9.00 / i_y), 12.00)
    _exact(k_eo * (10.50 / i_y), 14.00)
    _exact(7200.0 + 1080.0, 8280.0)
    _exact(20.00 * 0.80, 16.00)

    raster = make_raster(
        neurons=20,
        mean_rate_hz=50.0,
        window_ms=36.0,
        seed=202609109,
        source="tm6.pock.bay",
        target="thistlemere.bay_derate_core",
        table=[
            {"from": "pock_ix", "to": "voltage_estimator", "weight": 1.40},
            {"from": "pock_iy", "to": "polarimeter_norm_core", "weight": 1.20},
            {"from": "busveil_v", "to": "vendor_continue_advocate", "weight": 0.45},
        ],
        third_factor={
            "modulator": "na.gis_voltage_salience",
            "tau_e_s": 1.6,
            "tau_e_ms": 1600.0,
            "eligibility": "pre-post coincidence on bay-derate synapses; the Pockels modulator enables potentiation only while the reference photodiode is co-active inside tau_e so a Busveil patched-V_pi corridor cannot hide a 16.00 kV bus",
        },
        channel_prefix="pock.n",
        anchor="TM-6 Pockels 36 ms frame at I_x 12.00 / I_y 3.00 (t_s 3000) reconstructing 16.00 kV above the 12.00 kV derate floor",
    )
    w_s = 0.036
    events = [
        ev(0.0, "pock.ix", 6.00, code="IX_AU", units="au", note="plant-owned longitudinal BGO Pockels cell on GIS bay B-3; not Faraday FOCT, not PMU, not capacitive divider"),
        ev(300000.0, "pock.iy", 3.00, code="IY_AU", units="au", note="reference photodiode; V_kV = k_eo * (I_x / I_y)"),
        ev(600000.0, "recon.v", 8.00, code="V_KV", units="kV", note="4.00*(6.00/3.00)=8.00 exact"),
        ev(900000.0, "cap.v", 7.80, code="CAP_KV", units="kV", note="capacitive divider corridor; looks healthy"),
        ev(1200000.0, "busveil.v", 7.20, code="VENDOR_KV", units="kV", note="Busveil last-good patched V_pi stamp; not admissible SoT"),
        ev(1800000.0, "pock.ix", 9.00, code="IX_AU", units="au"),
        ev(2100000.0, "recon.v", 12.00, code="V_KV", units="kV", note="4.00*(9.00/3.00)=12.00; at the 12.00 derate floor"),
        ev(2400000.0, "gis.P", 5.80, code="SF6_BAR", units="bar", note="SF6 density corridor; not a voltage license"),
        ev(2700000.0, "load.mw", 42.0, code="LOAD_MW", units="MW"),
        ev(3000000.0, "pock.ix", 12.00, code="IX_AU", units="au", note="derate-floor frame; raster sidecar"),
        ev(3000001.4, "pock.iy", 3.00, code="IY_AU", units="au", note="1.4 ms polarimeter-norm after I_x"),
        ev(3300000.0, "recon.v", 16.00, code="V_KV", units="kV", note="4.00*(12.00/3.00)=16.00 exact; derate floor 12.00"),
        ev(3600000.0, "recon.g", 40.00, code="GAMMA_MRAD", units="mrad", note="2.50*16.00=40.00 exact retardation identity"),
        ev(3900000.0, "cap.v", 8.40, code="CAP_KV", units="kV"),
        ev(4200000.0, "busveil.v", 7.20, code="VENDOR_KV", units="kV", note="Busveil still 7.20 through a patched V_pi"),
        ev(4500000.0, "pock.snr", 18.0, code="POCK_SNR", units="1", note="18.0 >= 14.0 polarimeter lock floor"),
        ev(4800000.0, "ops.prop", 1.0, code="KEEP_1PU", units="bool", note="shift engineer Orrin Hale: keep 1.00 bay; 12 au is LED aging"),
        ev(5400000.0, "gate.isol", 1.0, code="MODIFY", units="decision", note="derate bay B-3 to 0.80; 16.00 kV is above 12.00; Busveil not SoT"),
        ev(6000000.0, "bay.set", 0.80, code="PU", units="pu", note="20.00 kV rated * 0.80 = 16.00 kV hold"),
        ev(6600000.0, "feeder.lock", 1.0, code="B3_ISOL", units="bool"),
        ev(7200000.0, "soak.start", 1.0, code="SOAK_START", units="bool", note="bookend 1 of the 18.0 min SF6-settle floor"),
        ev(7800000.0, "gis.P", 5.70, code="SF6_BAR", units="bar"),
        ev(8280000.0, "soak.floor", 1.0, code="SOAK_FLOOR", units="bool", note="7200 s + 1080 s = 8280 s = 18.0 min"),
        ev(9000000.0, "ops.restore", 1.0, code="RESTORE_1PU", units="bool", note="Hale: Busveil 7.00 kV, restore 1.00 bay"),
        ev(9600000.0, "gate.exec", 1.0, code="ACCEPT", units="decision", note="companion t2: hold 0.80; Busveil restore refused; bus trip refused"),
        ev(10200000.0, "bay.held", 0.80, code="PU_HELD", units="pu"),
        ev(10800000.0, "busveil.v", 7.00, code="VENDOR_KV", units="kV"),
        ev(11400000.0, "recon.v", 14.00, code="V_KV", units="kV", note="post-derate 4.00*(10.50/3.00)=14.00; still above 12.00"),
        ev(12000000.0, "cap.v", 8.10, code="CAP_KV", units="kV"),
        ev(12600000.0, "feeder.held", 1.0, code="B3_HELD", units="bool"),
        ev(13200000.0, "trip.hold", 0.0, code="BUS_TRIP", units="bool", note="whole-bus trip not taken; 16.00 vs 22.00 kV tripwire"),
        ev(13800000.0, "bay.held", 0.80, code="PU_HELD", units="pu"),
    ]
    assert_stream(events)

    traj = {
        "id": "nelb-r36-109-t1",
        "state": {
            "sim_or_real": "designed",
            "episode_id": "TM-POCK-2026-0618",
            "domain": "pockels_gis_bus_voltage",
            "setting": "Thistlemere GIS TM-6 (invented), bay B-3, 145 kV class. Plant-owned longitudinal BGO Pockels cell on the bus duct. Busveil vendor last-good patched-V_pi cloud is a corridor witness, not the voltage SoT. Invented plant; designed campaign. Not Faraday FOCT current (r25 Quarryholt), not PMU synchrophasor (r1-r12 / r5), not capacitive-divider metering, not SAW torque (r15), not IFOG (r16).",
            "observables_at_decision": {
                "I_x_au": 12.00,
                "I_y_au": 3.00,
                "k_eo_kV": 4.00,
                "V_kV": 16.00,
                "gamma_mrad": 40.00,
                "busveil_kV": 7.20,
                "cap_kV": 8.40,
                "derate_floor_kV": 12.00,
            },
            "margin_authority": "TM-6 Pockels SOP rev B: if reconstructed V_kV >= 12.00 AND polarimeter SNR >= 14, derate this bay this night to 0.80 pu. A Busveil last-good stamp or a quiet capacitive divider cannot keep 1.00. Bus tripwire is 22.00 kV.",
        },
        "proposed_action": {
            "actor": "shift engineer Orrin Hale, citing Busveil 7.20 kV and capacitive divider 8.40 kV",
            "summary": "keep bay B-3 at 1.00 pu through the night; 12 au is LED aging on a healthy cell",
            "basis_claimed": "Busveil last-good is the OEM V_pi and the capacitive divider is under the 10.00 kV alarm",
        },
        "safety_decision": {
            "decision": "MODIFY",
            "rationale": "Keep-1.00 bay is refused. Serialized reconstruction: V_kV = k_eo * (I_x / I_y) = 4.00 * (12.00 / 3.00) = 16.00, which is 4.00 kV above the 12.00 derate floor. Retardation identity gamma_mrad = k_g * V_kV = 2.50 * 16.00 = 40.00. Busveil 7.20 kV is a morning patched-V_pi stamp, not a live polarimeter, and is not an admissible keep-1.00 witness. Ordered: derate bay B-3 to 0.80 pu now (20.00 kV rated -> 16.00 kV hold). Scope: this MODIFY does not trip the 145 kV bus (that is the companion question) and does not isolate the adjacent bay.",
            "threshold": "V_kV>=12.00 AND SNR>=14 => derate bay to 0.80 pu; Busveil is not SoT; trip if V_kV>=22.00",
            "stated_residuals": "16.00 vs 22.00 trip floor is 6.00 kV, not infinite; 0.80 pu is a load cut; Busveil remains the only OEM V_pi channel",
        },
        "executed_action": {
            "summary": "MODIFY at t_s 5400: bay derated to 0.80 pu; Busveil not SoT; reconstruction locked",
            "tool": "tm6-pock-bay-gate-cli",
            "observation": "V 16.00 kV recomputes from I_x 12.00 and I_y 3.00; Pockels cell remains live as the trip interlock",
        },
        "future_outcome": {
            "timeline": [
                {"t_s": 3000.0, "event": "Pockels I_x 12.00; raster frame; V 16.00 kV"},
                {"t_s": 4800.0, "event": "ops proposes keep 1.00 bay"},
                {"t_s": 5400.0, "event": "MODIFY derate bay to 0.80 pu"},
                {"t_s": 7200.0, "event": "18 min soak bookend 1"},
                {"t_s": 8280.0, "event": "18.0 min floor"},
                {"t_s": 9600.0, "event": "companion ACCEPT hold 0.80; restore refused"},
            ],
            "observed_effects": [
                "bus voltage recomputes from the serialized Pockels ratio at every recon.v event",
                "a Busveil-only head would have kept 1.00 pu overnight",
                "18 min SF6-settle floor is in the stream (soak.start, soak.floor)",
            ],
            "surprises": [
                "a patched-V_pi vendor stamp and a quiet capacitive divider co-existed with a 16.00 kV Pockels reconstruction",
            ],
            "new_state": {
                "tm6_bay_pu": 0.80,
                "busveil": "not SoT",
                "reconstruction_model": "discharged as an on-record calculator",
            },
            "latency_ms": 2400000.0,
        },
        "reward_components": reward(
            0.40,
            [
                ("pockels_ratio_reconstruction", 0.14),
                ("derate_floor_cut", 0.12),
                ("vendor_vpi_nonsubstitution", 0.10),
                ("soak_floor_in_stream", 0.07),
                ("load_cut_cost", -0.03),
            ],
            "scored for a keep-1.00 MODIFY on a recomputable BGO Pockels intensity ratio while refusing a Busveil patched-V_pi corridor; 18 min floor is priced as downtime not as a reason to wait",
        ),
        "meta": meta_common(
            tags=["MODIFY", "pockels-gis", "serialized-reconstruction", "operational-companion"],
            distillation_note="Pockels bay gate: I_x/I_y voltage reconstruction beats a green vendor V_pi dashboard; companion t2 holds 0.80 pu rather than restoring on Busveil",
        ),
    }
    traj2 = {
        "id": "nelb-r36-109-t2",
        "state": {
            "sim_or_real": "designed",
            "episode_id": "TM-POCK-2026-0618-exec",
            "domain": "gis_bay_hold_execution",
            "setting": "Same TM-6 after the MODIFY. Shift engineer proposes restoring 1.00 pu on Busveil 7.00 kV. This companion is the operational 0.80 hold, not a second polarimeter vote.",
            "observables_at_decision": {
                "bay_pu": 0.80,
                "V_kV": 14.00,
                "busveil_kV": 7.00,
                "soak_floor_s": 1080.0,
            },
        },
        "proposed_action": {
            "actor": "shift engineer Orrin Hale",
            "summary": "restore 1.00 bay; 18 min already paid and Busveil is 7.00 kV",
            "basis_claimed": "the MODIFY already cut the bay, so restoring on the OEM V_pi is the cheapest hold",
        },
        "safety_decision": {
            "decision": "ACCEPT",
            "rationale": "Hold 0.80 bay. The SF6-settle floor is complete and the bus-trip tripwire (V_kV >= 22.00) is still armed on the plant Pockels head. ACCEPT the hold. Do not restore 1.00 on Busveil. Do not trip the 145 kV bus. 14.00 kV post-derate is still the Pockels SoT until a new frame clears 12.00.",
            "threshold": "bay_pu==0.80 AND soak_floor_complete AND trip_tripwire_armed AND restore_1pu_not_taken AND bus_not_tripped",
        },
        "executed_action": {
            "summary": "0.80 bay held at t_s 9600; Busveil restore not latched; bus not tripped",
            "tool": "tm6-bay-derate-exec",
            "observation": "recon.v 14.00 kV after derate; SF6 5.70 bar; Busveil still ignored",
        },
        "future_outcome": {
            "timeline": [
                {"t_s": 7200.0, "event": "soak clock started after MODIFY"},
                {"t_s": 8280.0, "event": "18.0 min floor"},
                {"t_s": 9000.0, "event": "restore 1.00 bay proposed"},
                {"t_s": 9600.0, "event": "ACCEPT hold 0.80 bay"},
            ],
            "observed_effects": [
                "Busveil restore did not reopen the voltage call",
                "bus tripwire never fired; 16.00 vs 22.00 kV floor",
            ],
            "new_state": {"bay_pu": 0.80, "restore_1pu": "blocked", "bus": "in service", "b3": "derated"},
            "latency_ms": 1800000.0,
        },
        "reward_components": reward(
            0.35,
            [
                ("hold_0p80", 0.12),
                ("no_busveil_restore", 0.10),
                ("no_bus_trip", 0.09),
                ("soak_complete", 0.06),
                ("held_load_cost", -0.02),
            ],
            "operational execution gate: hold 0.80 because Busveil is not a restore license; not a polarimeter re-vote",
        ),
        "meta": meta_common(tags=["ACCEPT", "operational-execution", "gis-derate"]),
    }
    return {
        "id": "nelb-r36-109",
        "spike_events": events,
        "language_view": {
            "description": "Thistlemere GIS TM-6. Plant-owned longitudinal BGO Pockels cell reconstructs 16.00 kV from 4.00*(12.00/3.00) while Busveil still shows 7.20 kV and the capacitive divider 8.40 kV. The gate MODIFYs bay B-3 derate to 0.80 pu. An 18 min SF6-settle floor is serialized in the stream. Companion t2 ACCEPTs the 0.80 hold and refuses a Busveil restore.",
            "trajectory": traj,
            "trajectory_bay_hold": traj2,
        },
        "bridge_notes": {
            "channel_map": {
                "pock.ix / pock.iy": "crossed-polarizer photodiodes; the physics channels the reconstruction consumes",
                "recon.v / recon.g": "serialized bus kV and retardation mrad identity",
                "cap.v / busveil.v / gis.P / load.mw / pock.snr": "capacitive divider, vendor V_pi cloud, SF6 density, load, and lock SNR; the denial channels that look healthy",
                "ops.prop / gate.isol / ops.restore / gate.exec": "keep-1.00 proposal, MODIFY derate, restore proposal, companion ACCEPT",
                "bay.set / soak.start / soak.floor / bay.held / feeder.held": "operational companion channels plus the 18 min floor",
            },
            "temporal_motifs": [
                "vendor-green while pockels-over: busveil.v 7.20 next to recon.v 16.00",
                "reconstruction as event: recon.v 16.00 equals 4.00*(12.00/3.00)",
                "MODIFY then operational ACCEPT: gate.isol at 5400 s, gate.exec at 9600 s",
                "slow floor in-stream: soak.start 7200 s, soak.floor 8280 s (18.0 min)",
                "tight Pockels pair: pock.ix then pock.iy +1.4 ms at the raster frame",
            ],
            "language_to_spike_mapping": "'Busveil is 7.20 kV' = busveil.v 7.20; '16 kV bus' = recon.v 16.00; 'derate this bay' = gate.isol MODIFY; 'hold 0.80 not restore' = gate.exec ACCEPT",
            "why_high_value": "New longitudinal-BGO-Pockels family on a GIS bus (not Faraday FOCT r25, not PMU r5, not SAW r15, not IFOG r16). Lead MODIFY of keep-1.00 bay on a recomputable intensity ratio that a patched-V_pi dashboard would have cleared. Companion t2 is operational 0.80 hold. sim_or_real=designed.",
            "encoder_spec": {
                "prng": "MT19937 via python random.Random",
                "seeds": {"raster": 202609109, "stream_note": "stream amplitudes are authored constants (au, kV, mrad, bar, MW, pu, bool)"},
                "draw_order": "raster: per neuron id order, gap-constrained times, per-spike adaptation and noise",
                "thinning": "polarimeter exists at 2 kHz; stream keeps 3 I_x points; recon keeps 4 of ~40 solver ticks",
                "refractory_floors_ms": {
                    "pock.ix": 1.4,
                    "pock.iy": 1.4,
                    "recon.v": 60000,
                    "recon.g": 60000,
                    "cap.v": 60000,
                    "busveil.v": 60000,
                    "gis.P": 60000,
                    "load.mw": 60000,
                    "pock.snr": 60000,
                    "ops.prop": 60000,
                    "gate.isol": 60000,
                    "bay.set": 60000,
                    "feeder.lock": 60000,
                    "soak.start": 60000,
                    "soak.floor": 60000,
                    "ops.restore": 60000,
                    "gate.exec": 60000,
                    "bay.held": 60000,
                    "feeder.held": 60000,
                    "trip.hold": 60000,
                },
                "time_alias": "t_rel_ms; t0 = 2026-06-18T03:00:00Z campaign start",
            },
            "distillation_targets": [
                "Pockels reconstruction head: V_kV = k_eo * (I_x / I_y); gamma_mrad = k_g * V_kV",
                "derate-floor cut vs keep-1.00 vs bus-trip",
                "vendor-V_pi nonsubstitution: patched half-wave voltage is not a keep-1.00 witness",
                "operational companion: hold 0.80 without restoring on Busveil",
            ],
        },
        "reconstruction_model": {
            "name": "longitudinal_bgo_pockels_bus_voltage",
            "formula": "V_kV = k_eo * (I_x / I_y); gamma_mrad = k_g * V_kV",
            "parameters": {
                "k_eo_kV": 4.00,
                "I_y_au": 3.00,
                "k_g_mrad_per_kV": 2.50,
                "derate_floor_kV": 12.00,
                "trip_kV": 22.00,
                "derate_pu": 0.80,
                "soak_min": 18.0,
            },
            "worked_example": {"I_x_au": 12.00, "V_kV": 16.00, "gamma_mrad": 40.00},
            "check": "4.00*(12.00/3.00)=16.00 exactly; 2.50*16.00=40.00 exactly; 7200 s + 1080 s = 8280 s = 18.0 min floor",
        },
        "raster": raster,
        "gate_snn": {
            "decision": "MODIFY",
            "decision_window_ms": 36.0,
            "decision_window_s": 0.036,
            "code": "tm6.pock_bay_gate",
            "note": "MODIFY accumulator wins: Pockels voltage evidence overpowers the Busveil continue advocate",
            "decode_rule": "modify-derate if voltage_estimator AND polarimeter_norm fire; vendor_continue_advocate is below threshold by design",
            "populations": [
                gate_pop("voltage_estimator", 80, 1.5, 50.0, w_s),
                gate_pop("polarimeter_norm", 64, 1.2, 31.25, w_s),
                gate_pop("vendor_continue_advocate", 32, 0.7, 25.0, w_s),
                gate_pop("modify_latch", 80, 1.7, 62.5, w_s),
            ],
        },
        "gate_compute": gate_compute(
            [
                {"check": "tm6.pock_scorer", "neurons": 80, "mean_rate_hz": 50.0, "window_ms": 36.0},
                {"check": "tm6.derate_scorer", "neurons": 40, "mean_rate_hz": 50.0, "window_ms": 32.0},
            ]
        ),
        "meta": meta_common(
            id="nelb-r36-109",
            clock_domain="tm6-pock-campaign-relative-ms-t0-2026-06-18T03:00:00Z",
            tags=["pockels-gis", "MODIFY", "ACCEPT", "serialized-reconstruction", "operational-t2"],
        ),
    }


# ---------------------------------------------------------------------------
# Record 110 — pulsed-eddy-current remaining wall of a coated riser, hil,
# REJECT / MODIFY
# ---------------------------------------------------------------------------
def rec_110():
    k_s = 5.00
    tau_ms = 9.00
    d_mm = k_s * math.sqrt(tau_ms)
    _exact(d_mm, 15.00)
    _exact(k_s * math.sqrt(16.00), 20.00)
    _exact(k_s * math.sqrt(12.25), 17.50)
    _exact(k_s * math.sqrt(10.24), 16.00)
    _exact(1800.0 + 1800.0, 3600.0)

    raster = make_raster(
        neurons=25,
        mean_rate_hz=50.0,
        window_ms=28.0,
        seed=202609110,
        source="ms6.pec.spool",
        target="murkspit.riser_stop_core",
        table=[
            {"from": "pec_tau", "to": "wall_estimator", "weight": 1.35},
            {"from": "pec_ks", "to": "diff_norm_core", "weight": 1.25},
            {"from": "wrapveil_d", "to": "vendor_continue_advocate", "weight": 0.40},
        ],
        third_factor={
            "modulator": "da.riser_wall_error",
            "tau_e_s": 1.1,
            "tau_e_ms": 1100.0,
            "eligibility": "pre-post coincidence on keep-run synapses; the PEC modulator depresses keep-run links when decay time stays short inside tau_e of a diffusivity-norm sample",
        },
        channel_prefix="pec.n",
        anchor="MS-6 HIL spool 28 ms frame at tau 9.00 ms / k_s 5.00 (t_s 600) reconstructing 15.00 mm below the 16.00 mm stop floor",
    )
    w_s = 0.028
    events = [
        ev(0.0, "pec.tau", 16.00, code="TAU_MS", units="ms", note="HIL coated spare spool in PEC-HIL-5; plant-owned pulsed eddy current, not ECT, not ECA FSW, not MFL Hall"),
        ev(30000.0, "pec.ks", 5.00, code="K_S", units="mm_per_sqrt_ms", note="diffusion calibration; d_mm = k_s * sqrt(tau_ms)"),
        ev(60000.0, "recon.d", 20.00, code="D_MM", units="mm", note="5.00*sqrt(16.00)=20.00 exact"),
        ev(180000.0, "ut.d", 21.40, code="UT_MM", units="mm", note="through-coating UT corridor; scatter, not PEC tau"),
        ev(240000.0, "wrapveil.d", 22.00, code="VENDOR_MM", units="mm", note="Wrapveil last-inspection remaining-wall cloud; the only OEM wall SoT"),
        ev(360000.0, "pec.tau", 12.25, code="TAU_MS", units="ms"),
        ev(420000.0, "recon.d", 17.50, code="D_MM", units="mm", note="5.00*sqrt(12.25)=17.50"),
        ev(480000.0, "pec.lo", 1.80, code="LIFTOFF_MM", units="mm", note="probe lift-off conjunct; not remaining wall"),
        ev(600000.0, "pec.tau", 9.00, code="TAU_MS", units="ms", note="stop-floor frame; raster sidecar"),
        ev(600001.2, "pec.ks", 5.00, code="K_S", units="mm_per_sqrt_ms", note="1.2 ms diffusivity-norm after tau"),
        ev(720000.0, "recon.d", 15.00, code="D_MM", units="mm", note="5.00*sqrt(9.00)=15.00 exact; stop floor 16.00"),
        ev(780000.0, "ut.d", 21.20, code="UT_MM", units="mm"),
        ev(840000.0, "wrapveil.d", 22.00, code="VENDOR_MM", units="mm"),
        ev(960000.0, "pec.lo", 1.90, code="LIFTOFF_MM", units="mm"),
        ev(1020000.0, "ops.prop", 1.0, code="KEEP_RUN", units="bool", note="night inspector Nessa Bram: keep-run; Wrapveil 22.00 mm and UT 21.20"),
        ev(1080000.0, "gate.stop", 1.0, code="REJECT", units="decision", note="stop keep-run; 15.00 mm is below 16.00; Wrapveil not SoT"),
        ev(1140000.0, "prod.hold", 1.00, code="PROD_PU", units="pu", note="production still 1.00 pending companion 0.70"),
        ev(1800000.0, "dep.start", 1.0, code="DEP_START", units="bool", note="bookend 1 of the 30.0 min depressurization floor"),
        ev(2400000.0, "ut.d", 21.00, code="UT_MM", units="mm"),
        ev(3600000.0, "dep.floor", 1.0, code="DEP_FLOOR", units="bool", note="1800 s + 1800 s = 3600 s = 30.0 min"),
        ev(4200000.0, "ops.esd", 1.0, code="RISER_ESD", units="bool", note="Bram: ESD the riser until day-shift"),
        ev(4800000.0, "gate.hold", 1.0, code="MODIFY", units="decision", note="companion t2: clamp J-11..J-13 and cut production to 0.70; riser ESD refused"),
        ev(5100000.0, "prod.set", 0.70, code="PROD_PU", units="pu"),
        ev(5400000.0, "pec.tau", 10.24, code="TAU_MS", units="ms"),
        ev(5700000.0, "recon.d", 16.00, code="D_MM", units="mm", note="5.00*sqrt(10.24)=16.00; at the 16.00 floor so 0.70 holds"),
        ev(6000000.0, "wrapveil.d", 21.80, code="VENDOR_MM", units="mm"),
        ev(6300000.0, "clamp.j", 3.0, code="JOINTS", units="count", note="J-11 J-12 J-13 clamped"),
        ev(6600000.0, "prod.held", 0.70, code="PROD_HELD", units="pu"),
        ev(6900000.0, "unit.esd", 0.0, code="ESD_NOT_TAKEN", units="bool"),
        ev(7200000.0, "recon.d", 16.00, code="D_MM", units="mm"),
        ev(7500000.0, "prod.held", 0.70, code="PROD_HELD", units="pu"),
        ev(7800000.0, "pec.lo", 1.70, code="LIFTOFF_MM", units="mm"),
    ]
    assert_stream(events)

    traj = {
        "id": "nelb-r36-110-t1",
        "state": {
            "sim_or_real": "hil",
            "episode_id": "MS-PEC-2026-0722",
            "domain": "pulsed_eddy_current_riser_wall",
            "setting": "Murkspit Riser MS-6 (invented), coated joint J-12. Hardware-in-the-loop coated spare spool in PEC-HIL-5 supplies the decay waveform that times the in-service keep-run stop. Plant-owned pulsed eddy current. Wrapveil vendor last-inspection remaining-wall cloud is the only OEM wall SoT. Not ECT capacitance tomography (r20/r22), not ECA FSW lift-off (r21), not MFL Hall remaining-wall (r27/r28), not PAUT TFM (r23), not GPR two-way time (r34).",
            "observables_at_decision": {
                "tau_ms": 9.00,
                "k_s": 5.00,
                "d_mm": 15.00,
                "wrapveil_mm": 22.00,
                "ut_mm": 21.20,
                "stop_floor_mm": 16.00,
                "liftoff_mm": 1.90,
            },
            "margin_authority": "MS-6 PEC SOP rev A: if reconstructed d_mm <= 16.00, refuse keep-run on this riser. A last-inspection cloud or a through-coating UT corridor cannot keep-run. Riser ESD is a different gate.",
        },
        "proposed_action": {
            "actor": "night inspector Nessa Bram, citing Wrapveil 22.00 mm and UT 21.20 mm under the 18 mm alarm",
            "summary": "keep-run through the night; 9 ms is coating conductivity on a healthy spool",
            "basis_claimed": "Wrapveil is last-inspection and a night ESD of a production riser is a restart measured in hours",
        },
        "safety_decision": {
            "decision": "REJECT",
            "rationale": "Keep-run is refused. Serialized reconstruction: d_mm = k_s * sqrt(tau_ms) = 5.00 * sqrt(9.00) = 15.00, which is 1.00 mm under the 16.00 mm stop floor. Wrapveil 22.00 mm is a last-inspection freeze, not a live decay, and is not an admissible keep-run witness. Ordered: refuse keep-run now. Scope: this REJECT does not ESD the riser (that is the companion question) and does not isolate the export header.",
            "threshold": "d_mm<=16.00 => refuse keep-run; Wrapveil is not SoT",
            "stated_residuals": "production 0.70 still required to unload the joint; 15.00 mm is a production cut; Wrapveil remains the only OEM wall channel",
        },
        "executed_action": {
            "summary": "REJECT at t_s 1080: keep-run refused; Wrapveil not SoT; reconstruction locked",
            "tool": "ms6-pec-stop-gate-cli",
            "observation": "d 15.00 mm recomputes from tau 9.00 ms and k_s 5.00; HIL spool hashed; Wrapveil channel not used as SoT",
        },
        "future_outcome": {
            "timeline": [
                {"t_s": 600.0, "event": "PEC tau 9.00 ms; raster frame; d 15.00 mm"},
                {"t_s": 1020.0, "event": "ops proposes keep-run"},
                {"t_s": 1080.0, "event": "REJECT keep-run"},
                {"t_s": 1800.0, "event": "30 min depressurization bookend 1"},
                {"t_s": 3600.0, "event": "30.0 min floor"},
                {"t_s": 4800.0, "event": "companion MODIFY clamp plus production 0.70 vs riser ESD"},
            ],
            "observed_effects": [
                "remaining wall recomputes from the serialized PEC diffusion model at every recon.d event",
                "a Wrapveil-only head would have kept-run overnight",
                "30 min depressurization floor is in the stream (dep.start, dep.floor)",
            ],
            "surprises": [
                "a last-inspection 22 mm cloud and a quiet through-coating UT co-existed with a 15.00 mm PEC reconstruction",
            ],
            "new_state": {
                "ms6_prod_pu": 1.00,
                "keep_run": "blocked",
                "wrapveil": "not SoT",
            },
            "latency_ms": 1860000.0,
        },
        "reward_components": reward(
            0.43,
            [
                ("pec_sqrt_reconstruction", 0.15),
                ("stop_floor_refuse", 0.12),
                ("vendor_inspection_nonsubstitution", 0.10),
                ("dep_floor_in_stream", 0.08),
                ("production_cut_cost", -0.02),
            ],
            "scored for a keep-run REJECT on a recomputable PEC remaining wall while refusing a last-inspection dashboard; 30 min floor is priced as downtime not as a reason to wait",
        ),
        "meta": meta_common(
            tags=["REJECT", "pulsed-eddy-current", "serialized-reconstruction", "hil", "operational-companion"],
            distillation_note="PEC stop gate: k_s*sqrt(tau) reconstruction beats a green last-inspection dashboard; companion t2 is clamp plus 0.70, not a riser ESD",
        ),
    }
    traj2 = {
        "id": "nelb-r36-110-t2",
        "state": {
            "sim_or_real": "hil",
            "episode_id": "MS-PEC-2026-0722-clamp",
            "domain": "riser_clamp_hold_execution",
            "setting": "Same MS-6 after the keep-run REJECT. Night inspector proposes a riser ESD that would shut the export until day-shift. This companion is the operational clamp of J-11..J-13 plus production 0.70, not a second decay vote.",
            "observables_at_decision": {
                "prod_pu": 0.70,
                "d_mm": 16.00,
                "joints_clamped": 3,
                "proposed": "riser_esd",
            },
        },
        "proposed_action": {
            "actor": "night inspector Nessa Bram",
            "summary": "ESD the riser until day-shift; 30 min already paid",
            "basis_claimed": "the REJECT already refused keep-run, so a full ESD is the cheapest hold",
        },
        "safety_decision": {
            "decision": "MODIFY",
            "rationale": "Hold production at 0.70 and clamp joints J-11..J-13. Riser ESD at night is a restart measured in hours and does not unload the coated joint any faster than a three-joint clamp plus 0.70. MODIFY the ESD into that hold. Do not restore 1.00. Do not convert the hold into a personnel action on Bram. Post-hold d 16.00 mm is still at the 16.00 floor, so 0.70 holds until a new frame clears 16.00.",
            "threshold": "prod_pu==0.70 AND keep_run_not_restored AND riser_esd_not_taken AND joints_clamped==3",
        },
        "executed_action": {
            "summary": "production 0.70 and three-joint clamp at t_s 4800; riser ESD not latched; keep-run not restored",
            "tool": "ms6-riser-clamp-exec",
            "observation": "d 16.00 mm after hold; Wrapveil still ignored",
        },
        "future_outcome": {
            "timeline": [
                {"t_s": 1800.0, "event": "depressurization clock started after REJECT"},
                {"t_s": 3600.0, "event": "30.0 min floor"},
                {"t_s": 4200.0, "event": "riser ESD proposed"},
                {"t_s": 4800.0, "event": "MODIFY clamp plus production 0.70"},
            ],
            "observed_effects": [
                "riser-ESD restart cost is visible without waiting for a hung start",
                "hold did not reopen the stop-floor call",
            ],
            "new_state": {"prod_pu": 0.70, "keep_run": "blocked", "riser_esd": "not taken", "joints_clamped": 3},
            "latency_ms": 960000.0,
        },
        "reward_components": reward(
            0.34,
            [
                ("clamp_hold", 0.12),
                ("no_riser_esd", 0.11),
                ("no_keeprun_restore", 0.08),
                ("post_hold_margin", 0.06),
                ("held_production_cost", -0.03),
            ],
            "operational execution gate: clamp plus 0.70 because riser ESD does not unload faster; not a PEC re-vote",
        ),
        "meta": meta_common(tags=["MODIFY", "operational-execution", "riser-clamp"]),
    }
    return {
        "id": "nelb-r36-110",
        "spike_events": events,
        "language_view": {
            "description": "Murkspit Riser MS-6 HIL spool pit. Plant-owned pulsed eddy current reconstructs 15.00 mm from 5.00*sqrt(9.00) while Wrapveil still shows 22.00 mm and through-coating UT 21.20 mm. The gate REJECTS keep-run. A 30 min depressurization floor is serialized in the stream. Companion t2 MODIFYs a riser ESD into a three-joint clamp plus production 0.70.",
            "trajectory": traj,
            "trajectory_clamp_hold": traj2,
        },
        "bridge_notes": {
            "channel_map": {
                "pec.tau / pec.ks": "decay time and diffusion calibration; remaining-wall inputs",
                "recon.d": "serialized remaining wall mm",
                "wrapveil.d / ut.d / pec.lo": "vendor last-inspection cloud, through-coating UT corridor, and lift-off conjunct",
                "ops.prop / gate.stop / ops.esd / gate.hold": "keep-run proposal, REJECT, riser-ESD proposal, companion MODIFY",
                "dep.start / dep.floor / prod.set / prod.held / clamp.j": "operational companion channels plus the 30 min floor",
            },
            "temporal_motifs": [
                "vendor-green while pec-thin: wrapveil.d 22.00 next to recon.d 15.00",
                "reconstruction as event: recon.d 15.00 equals 5.00*sqrt(9.00)",
                "REJECT then operational MODIFY: gate.stop at 1080 s, gate.hold at 4800 s",
                "slow floor in-stream: dep.start 1800 s, dep.floor 3600 s (30.0 min)",
                "tight PEC pair: pec.tau then pec.ks +1.2 ms at the raster frame",
            ],
            "language_to_spike_mapping": "'Wrapveil is 22 mm' = wrapveil.d 22.00; '15 mm remaining' = recon.d 15.00; 'stop keep-run' = gate.stop REJECT; 'clamp not ESD' = gate.hold MODIFY",
            "why_high_value": "New pulsed-eddy-current family on a coated riser (not ECT r20/r22, not ECA FSW r21, not MFL r27/r28, not PAUT TFM r23, not GPR r34). Lead REJECT of keep-run on a recomputable sqrt-tau wall that a last-inspection dashboard would have cleared. Companion t2 is operational clamp plus 0.70. sim_or_real=hil.",
            "encoder_spec": {
                "prng": "MT19937 via python random.Random",
                "seeds": {"raster": 202609110, "stream_note": "stream amplitudes are authored constants (ms, mm, pu, count, bool)"},
                "draw_order": "raster: per neuron id order, gap-constrained times, per-spike adaptation and noise",
                "thinning": "PEC pulser exists at ~50 Hz; stream keeps 4 tau points; recon keeps 5 of ~40 solver ticks",
                "refractory_floors_ms": {
                    "pec.tau": 1.2,
                    "pec.ks": 1.2,
                    "recon.d": 30000,
                    "ut.d": 60000,
                    "wrapveil.d": 60000,
                    "pec.lo": 60000,
                    "ops.prop": 60000,
                    "gate.stop": 60000,
                    "prod.hold": 60000,
                    "dep.start": 60000,
                    "dep.floor": 60000,
                    "ops.esd": 60000,
                    "gate.hold": 60000,
                    "prod.set": 60000,
                    "clamp.j": 60000,
                    "prod.held": 60000,
                    "unit.esd": 60000,
                },
                "time_alias": "t_rel_ms; t0 = 2026-07-22T22:00:00Z campaign start",
            },
            "distillation_targets": [
                "PEC reconstruction head: d_mm = k_s * sqrt(tau_ms)",
                "stop-floor refuse vs keep-run vs riser ESD",
                "vendor-inspection nonsubstitution: last-campaign remaining wall is not a keep-run witness",
                "operational companion: clamp plus 0.70 rather than a freeze-kill ESD of the riser",
            ],
        },
        "reconstruction_model": {
            "name": "pulsed_eddy_current_remaining_wall",
            "formula": "d_mm = k_s * sqrt(tau_ms)",
            "parameters": {
                "k_s": 5.00,
                "stop_floor_mm": 16.00,
                "isolate_mm": 10.00,
                "hold_prod_pu": 0.70,
                "dep_min": 30.0,
            },
            "worked_example": {"tau_ms": 9.00, "d_mm": 15.00},
            "check": "5.00*sqrt(9.00)=15.00 exactly; 5.00*sqrt(10.24)=16.00 exactly; 1800 s + 1800 s = 3600 s = 30.0 min floor",
        },
        "raster": raster,
        "gate_snn": {
            "decision": "REJECT",
            "decision_window_ms": 28.0,
            "decision_window_s": 0.028,
            "code": "ms6.pec_stop_gate",
            "note": "REJECT accumulator wins: PEC remaining-wall evidence overpowers the Wrapveil continue advocate",
            "decode_rule": "reject-stop if wall_estimator AND diff_norm fire; vendor_continue_advocate is below threshold by design",
            "populations": [
                gate_pop("wall_estimator", 100, 1.5, 50.0, w_s),
                gate_pop("diff_norm", 40, 1.2, 50.0, w_s),
                gate_pop("vendor_continue_advocate", 32, 0.7, 25.0, w_s),
                gate_pop("reject_latch", 80, 1.8, 62.5, w_s),
            ],
        },
        "gate_compute": gate_compute(
            [
                {"check": "ms6.pec_scorer", "neurons": 100, "mean_rate_hz": 50.0, "window_ms": 28.0},
                {"check": "ms6.stop_scorer", "neurons": 40, "mean_rate_hz": 50.0, "window_ms": 40.0},
            ]
        ),
        "meta": meta_common(
            id="nelb-r36-110",
            clock_domain="ms6-pec-hil-relative-ms-t0-2026-07-22T22:00:00Z",
            tags=["pulsed-eddy-current", "REJECT", "MODIFY", "hil", "operational-t2"],
        ),
    }


# ---------------------------------------------------------------------------
# Record 111 — confocal-chromatic thickness of a float-glass ribbon,
# simulated, ACCEPT / REJECT
# ---------------------------------------------------------------------------
def rec_111():
    k_lam = 0.040
    lam0 = 450.0
    lam_nm = 650.0
    z_mm = k_lam * (lam_nm - lam0)
    _exact(z_mm, 8.00)
    _exact(k_lam * (550.0 - lam0), 4.00)
    _exact(k_lam * (600.0 - lam0), 6.00)
    _exact(k_lam * (640.0 - lam0), 7.60)
    _exact(6000.0 + 720.0, 6720.0)

    raster = make_raster(
        neurons=16,
        mean_rate_hz=62.5,
        window_ms=40.0,
        seed=202609111,
        source="ch5.chrom.ribbon",
        target="culmholt.hold_core",
        table=[
            {"from": "chrom_lam", "to": "thickness_estimator", "weight": 1.40},
            {"from": "chrom_k", "to": "lambda_norm_core", "weight": 1.20},
            {"from": "ribbonveil_z", "to": "vendor_continue_advocate", "weight": 0.35},
        ],
        third_factor={
            "modulator": "ach.ribbon_swell_conflict",
            "tau_e_s": 2.2,
            "tau_e_ms": 2200.0,
            "eligibility": "pre-post coincidence on hold synapses; the confocal modulator enables potentiation only while the chromatic calibration is co-active inside tau_e so a Ribbonveil last-good corridor cannot hide an 8.00 mm swell",
        },
        channel_prefix="chrom.n",
        anchor="CH-5 confocal 40 ms frame at lambda 650.0 nm / k_lam 0.040 (t_s 3000) reconstructing 8.00 mm above the 7.20 mm hold floor",
    )
    w_s = 0.040
    events = [
        ev(0.0, "chrom.lam", 550.0, code="LAM_NM", units="nm", note="simulated sealed ribbon coupon in Chrom-SIM-2; confocal chromatic thickness, not ellipsometry, not THz-TDS, not FMCW lining"),
        ev(300000.0, "chrom.k", 0.040, code="K_LAM", units="mm_per_nm", note="chromatic calibration; z_mm = k_lam * (lambda_nm - 450)"),
        ev(600000.0, "recon.z", 4.00, code="Z_MM", units="mm", note="0.040*(550.0-450.0)=4.00 exact"),
        ev(900000.0, "py.z", 6.20, code="PY_MM", units="mm", note="lehr two-color pyrometer corridor"),
        ev(1200000.0, "chrom.snr", 16.0, code="CHROM_SNR", units="1"),
        ev(1500000.0, "ribbonveil.z", 6.20, code="VENDOR_MM", units="mm", note="Ribbonveil last-good cloud; not confocal lambda"),
        ev(1800000.0, "chrom.lam", 600.0, code="LAM_NM", units="nm"),
        ev(2100000.0, "recon.z", 6.00, code="Z_MM", units="mm", note="0.040*(600.0-450.0)=6.00"),
        ev(2400000.0, "lehr.T", 620.0, code="LEHR_C", units="C"),
        ev(2700000.0, "boats.n", 8.0, code="BOATS", units="count"),
        ev(3000000.0, "chrom.lam", 650.0, code="LAM_NM", units="nm", note="hold-floor frame; raster sidecar"),
        ev(3000001.5, "chrom.k", 0.040, code="K_LAM", units="mm_per_nm", note="1.5 ms lambda-norm after peak"),
        ev(3600000.0, "recon.z", 8.00, code="Z_MM", units="mm", note="0.040*(650.0-450.0)=8.00 exact; hold floor 7.20"),
        ev(3900000.0, "py.z", 6.40, code="PY_MM", units="mm"),
        ev(4200000.0, "ribbonveil.z", 6.20, code="VENDOR_MM", units="mm"),
        ev(4500000.0, "dump.staged", 1.0, code="LEHR_DUMP_STAGED", units="bool", note="lehr dump staged; out of R-7 hold scope"),
        ev(4800000.0, "ops.prop", 1.0, code="HOLD_AND_DUMP", units="bool", note="lehr captain Pia Solt: hold R-7 and dump the lehr; 650 nm is a tin-bath glitch"),
        ev(5400000.0, "gate.hold", 1.0, code="ACCEPT", units="decision", note="bounded ACCEPT: ribbon R-7 this day; lehr dump refused"),
        ev(6000000.0, "lehr.start", 1.0, code="LEHR_START", units="bool", note="bookend 1 of the 12.0 min draw-stabilize floor"),
        ev(6300000.0, "draw.mps", 0.12, code="DRAW_MPS", units="m_s"),
        ev(6600000.0, "recon.lock", 8.00, code="LOCKED_MM", units="mm"),
        ev(6720000.0, "lehr.floor", 1.0, code="LEHR_FLOOR", units="bool", note="6000 s + 720 s = 6720 s = 12.0 min"),
        ev(7200000.0, "ops.skip", 1.0, code="SKIP_HOLD", units="bool", note="Solt: Ribbonveil 6.20 mm, skip R-7 hold to save takt"),
        ev(7800000.0, "gate.skip", 1.0, code="REJECT", units="decision", note="companion t2: skip-hold refused; Ribbonveil is last-good"),
        ev(8400000.0, "r7.held", 1.0, code="R7_HOLD", units="bool"),
        ev(9000000.0, "dump.held", 1.0, code="DUMP_HELD", units="bool"),
        ev(9600000.0, "py.z", 6.35, code="PY_MM", units="mm"),
        ev(10200000.0, "ribbonveil.z", 6.18, code="VENDOR_MM", units="mm"),
        ev(10800000.0, "recon.z", 7.60, code="Z_MM", units="mm", note="post-hold sample 640 nm; 0.040*(640.0-450.0)=7.60; still over 7.20"),
        ev(11400000.0, "draw.mps", 0.10, code="DRAW_MPS", units="m_s"),
        ev(12600000.0, "r8.skip", 0.0, code="R8_NOT_THIS_GATE", units="bool", note="R-8 remains a different gate; skip of R-7 was refused, not executed"),
        ev(13200000.0, "isolate.hold", 0.0, code="LEHR_DUMP", units="bool", note="8.00 vs 9.50 mm dump floor; lehr dump not taken"),
    ]
    assert_stream(events)

    traj = {
        "id": "nelb-r36-111-t1",
        "state": {
            "sim_or_real": "simulated",
            "episode_id": "CH-CHROM-2026-0819",
            "domain": "confocal_chromatic_float_ribbon",
            "setting": "Culmholt Float CH-5 (invented), ribbon R-7. Simulated sealed confocal-chromatic cell on the tin-bath exit in Chrom-SIM-2. Lehr two-color pyrometer and Ribbonveil last-good cloud are corridor witnesses, not the thickness SoT. Invented plant; simulated campaign. Not spectroscopic ellipsometry (r30 Lichenholt), not THz-TDS (r20/r21), not FMCW microwave lining (r33), not hyperspectral crop (r16), not industrial x-ray DR (r17), not laser-shearography (r32 Ashspire).",
            "observables_at_decision": {
                "lambda_nm": 650.0,
                "lambda0_nm": 450.0,
                "k_lam": 0.040,
                "z_mm": 8.00,
                "py_mm": 6.40,
                "ribbonveil_mm": 6.20,
                "hold_floor_mm": 7.20,
            },
            "margin_authority": "CH-5 confocal SOP rev C: a ribbon may hold/slow only if reconstructed z_mm >= 7.20 AND the authorization covers this ribbon this day. A lehr pyrometer or last-good corridor cannot substitute. Lehr dumps are out of scope. Dump the lehr if z_mm >= 9.50.",
        },
        "proposed_action": {
            "actor": "lehr captain Pia Solt, citing pyrometer 6.40 mm and Ribbonveil 6.20 mm",
            "summary": "hold R-7 and dump the lehr; 650 nm is a tin-bath glitch",
            "basis_claimed": "last-good Ribbonveil and the lehr pyrometer are both consistent with 6.2 mm so the path cannot be 8.00 mm",
        },
        "safety_decision": {
            "decision": "ACCEPT",
            "rationale": "This ribbon is accepted, not the lehr dump and not R-8. Serialized reconstruction: z_mm = k_lam * (lambda_nm - lambda0) = 0.040 * (650.0 - 450.0) = 8.00, which is 0.80 mm over the 7.20 mm hold floor and 1.50 mm under the 9.50 mm dump floor. SOP rev C still forbids the lehr dump: ordered hold/slow of ribbon R-7 this day only. Explicit scope: this accept does not cover dumping the lehr and does not authorize R-8 without a new lambda frame. Dump tripwire: z_mm >= 9.50.",
            "threshold": "z_mm>=7.20 AND z_mm<9.50 AND ribbon=R-7 AND lehr_not_dumped",
            "stated_residuals": "0.80 mm margin is not infinite; 0.040 mm/nm still carries tin-bath index; lehr pyrometer is not a ribbon-thickness witness",
        },
        "executed_action": {
            "summary": "ACCEPT at t_s 5400: R-7 hold authorized; lehr dump held; reconstruction locked as SoT",
            "tool": "ch5-chrom-hold-gate-cli",
            "observation": "z 8.00 mm recomputes from lambda 650.0 nm and k_lam 0.040; draw stabilize staged; R-7 remains live as the dump interlock",
        },
        "future_outcome": {
            "timeline": [
                {"t_s": 3000.0, "event": "confocal lambda 650.0 nm; raster frame; z 8.00 mm"},
                {"t_s": 4800.0, "event": "ops proposes R-7 hold plus lehr dump"},
                {"t_s": 5400.0, "event": "ACCEPT bounded R-7 hold; dump refused"},
                {"t_s": 6000.0, "event": "companion lehr-stabilize start"},
                {"t_s": 6720.0, "event": "12.0 min lehr floor"},
                {"t_s": 7800.0, "event": "companion REJECT skip-hold of R-7"},
            ],
            "observed_effects": [
                "ribbon thickness recomputes from the serialized confocal model at every recon.z event",
                "a Ribbonveil-only head would have skipped R-7 on a 6.20 mm corridor",
                "peak swell 8.00 mm stayed under the 9.50 mm dump floor",
            ],
            "surprises": [
                "idle last-good 6.20 mm co-existed with an 8.00 mm confocal reconstruction",
            ],
            "new_state": {
                "ch5_r7": "authorized this day",
                "lehr_dump": "held",
                "reconstruction_model": "discharged as an on-record calculator",
            },
            "latency_ms": 2400000.0,
        },
        "reward_components": reward(
            0.41,
            [
                ("confocal_lambda_reconstruction", 0.14),
                ("bounded_r7_accept", 0.12),
                ("lehr_dump_out_of_scope", 0.09),
                ("dump_tripwire_armed", 0.08),
                ("held_dump_takt_cost", -0.02),
            ],
            "scored for an earned ACCEPT of R-7 hold on a recomputable confocal chromatic thickness while refusing a Ribbonveil corridor plus lehr dump",
        ),
        "meta": meta_common(
            tags=["ACCEPT", "confocal-chromatic", "serialized-reconstruction", "operational-companion"],
            distillation_note="Confocal ribbon gate: k_lam*(lambda-lambda0) reconstruction beats a last-good corridor; companion t2 refuses skip-hold rather than re-arguing thickness",
        ),
    }
    traj2 = {
        "id": "nelb-r36-111-t2",
        "state": {
            "sim_or_real": "simulated",
            "episode_id": "CH-CHROM-2026-0819-lehr",
            "domain": "ribbon_skip_hold_refusal",
            "setting": "Same CH-5 after the bounded ACCEPT. Lehr captain proposes skipping R-7 hold on Ribbonveil 6.20 mm to save takt. This companion is the operational skip refusal, not a second thickness vote.",
            "observables_at_decision": {
                "draw_mps": 0.12,
                "z_mm": 8.00,
                "r7_authorized": 1,
                "proposed": "skip_hold",
            },
        },
        "proposed_action": {
            "actor": "lehr captain Pia Solt",
            "summary": "skip R-7 hold; Ribbonveil still 6.20 mm and the 12 min stabilize already paid",
            "basis_claimed": "ACCEPT requirements for R-7 are fully specified so skipping the hold is a takt gift",
        },
        "safety_decision": {
            "decision": "REJECT",
            "rationale": "Skip-hold is refused. Ribbonveil 6.20 mm is last-good freeze, not confocal lambda, and is not an admissible skip witness. R-7 is still 7.60 mm after the stabilize. REJECT the skip. Do not dump the lehr at R-7-authorized. Do not convert the refusal into a personnel action on Solt. R-8 remains a different gate pending its own lambda frame.",
            "threshold": "skip_hold_not_taken AND lehr_not_dumped AND ribbonveil_not_SoT",
        },
        "executed_action": {
            "summary": "R-7 stabilize completed t_s 8400; skip-hold not latched; lehr dump held",
            "tool": "ch5-lehr-exec",
            "observation": "draw 0.12 then 0.10 m/s; R-7 still authorized; Ribbonveil still ignored",
        },
        "future_outcome": {
            "timeline": [
                {"t_s": 6000.0, "event": "lehr stabilize started"},
                {"t_s": 6720.0, "event": "12.0 min floor"},
                {"t_s": 7200.0, "event": "skip-hold proposed"},
                {"t_s": 7800.0, "event": "REJECT skip-hold"},
            ],
            "observed_effects": [
                "Ribbonveil skip did not reopen the confocal call",
                "lehr dump remained out of scope after R-7-authorized",
            ],
            "new_state": {"r7": "hold authorized", "r8": "not this gate", "lehr_dump": "held"},
            "latency_ms": 1800000.0,
        },
        "reward_components": reward(
            0.36,
            [
                ("skip_refusal", 0.13),
                ("ribbonveil_nonsubstitution", 0.11),
                ("no_lehr_dump_add", 0.09),
                ("lehr_floor_complete", 0.05),
                ("held_takt_cost", -0.02),
            ],
            "operational execution gate: refuse skip-hold because Ribbonveil is last-good, not confocal lambda; not a thickness re-vote",
        ),
        "meta": meta_common(tags=["REJECT", "operational-execution", "ribbon-hold"]),
    }
    return {
        "id": "nelb-r36-111",
        "spike_events": events,
        "language_view": {
            "description": "Culmholt Float CH-5 simulated coupon. Plant-owned confocal chromatic reconstructs 8.00 mm from 0.040*(650.0-450.0) while Ribbonveil still shows 6.20 mm and the lehr pyrometer 6.40 mm. The gate ACCEPTs a bounded hold of ribbon R-7. A 12 min draw-stabilize floor is serialized in the stream. Companion t2 REJECTS skip-hold of R-7.",
            "trajectory": traj,
            "trajectory_skip_refusal": traj2,
        },
        "bridge_notes": {
            "channel_map": {
                "chrom.lam / chrom.k": "peak wavelength and chromatic calibration; thickness inputs",
                "recon.z / recon.lock": "serialized ribbon thickness mm",
                "py.z / ribbonveil.z / lehr.T / boats.n / chrom.snr": "lehr pyrometer, vendor last-good, lehr temperature, boat count, lock SNR",
                "ops.prop / gate.hold / ops.skip / gate.skip": "hold-and-dump proposal, ACCEPT, skip-hold proposal, companion REJECT",
                "lehr.start / lehr.floor / r7.held / dump.held": "operational companion channels plus the 12 min floor",
            },
            "temporal_motifs": [
                "vendor-green while confocal-thick: ribbonveil.z 6.20 next to recon.z 8.00",
                "reconstruction as event: recon.z 8.00 equals 0.040*(650.0-450.0)",
                "ACCEPT then operational REJECT: gate.hold at 5400 s, gate.skip at 7800 s",
                "slow floor in-stream: lehr.start 6000 s, lehr.floor 6720 s (12.0 min)",
                "tight confocal pair: chrom.lam then chrom.k +1.5 ms at the raster frame",
            ],
            "language_to_spike_mapping": "'Ribbonveil is 6.20 mm' = ribbonveil.z 6.20; '8 mm swell' = recon.z 8.00; 'hold this ribbon' = gate.hold ACCEPT; 'do not skip' = gate.skip REJECT",
            "why_high_value": "New confocal-chromatic family on a float-glass ribbon (not ellipsometry r30, not THz-TDS r20/r21, not FMCW lining r33, not hyperspectral r16, not x-ray DR r17, not laser-shearography r32). Lead ACCEPT of a bounded R-7 hold on a recomputable lambda map that a last-good dashboard would have skipped. Companion t2 is operational skip refusal. sim_or_real=simulated.",
            "encoder_spec": {
                "prng": "MT19937 via python random.Random",
                "seeds": {"raster": 202609111, "stream_note": "stream amplitudes are authored constants (nm, mm, C, count, m/s, pu, bool)"},
                "draw_order": "raster: per neuron id order, gap-constrained times, per-spike adaptation and noise",
                "thinning": "confocal spectrometer exists at 1 kHz; stream keeps 3 lambda points; recon keeps 4 of ~40 solver ticks",
                "refractory_floors_ms": {
                    "chrom.lam": 1.5,
                    "chrom.k": 1.5,
                    "recon.z": 60000,
                    "py.z": 60000,
                    "ribbonveil.z": 60000,
                    "chrom.snr": 60000,
                    "lehr.T": 60000,
                    "boats.n": 60000,
                    "dump.staged": 60000,
                    "ops.prop": 60000,
                    "gate.hold": 60000,
                    "lehr.start": 60000,
                    "draw.mps": 60000,
                    "recon.lock": 60000,
                    "lehr.floor": 60000,
                    "ops.skip": 60000,
                    "gate.skip": 60000,
                    "r7.held": 60000,
                    "dump.held": 60000,
                    "r8.skip": 60000,
                    "isolate.hold": 60000,
                },
                "time_alias": "t_rel_ms; t0 = 2026-08-19T04:00:00Z campaign start",
            },
            "distillation_targets": [
                "confocal reconstruction head: z_mm = k_lam * (lambda_nm - lambda0)",
                "bounded hold vs skip vs lehr dump",
                "vendor-last-good nonsubstitution: a 6.20 mm stamp is not a skip witness",
                "operational companion: refuse skip-hold without re-opening thickness",
            ],
        },
        "reconstruction_model": {
            "name": "confocal_chromatic_ribbon_thickness",
            "formula": "z_mm = k_lam * (lambda_nm - lambda0_nm)",
            "parameters": {
                "k_lam": 0.040,
                "lambda0_nm": 450.0,
                "hold_floor_mm": 7.20,
                "dump_mm": 9.50,
                "lehr_min": 12.0,
            },
            "worked_example": {"lambda_nm": 650.0, "z_mm": 8.00},
            "check": "0.040*(650.0-450.0)=8.00 exactly; 0.040*(640.0-450.0)=7.60 exactly; 6000 s + 720 s = 6720 s = 12.0 min floor",
        },
        "raster": raster,
        "gate_snn": {
            "decision": "ACCEPT",
            "decision_window_ms": 40.0,
            "decision_window_s": 0.040,
            "code": "ch5.hold_gate",
            "note": "ACCEPT accumulator wins: confocal thickness evidence overpowers the Ribbonveil continue advocate",
            "decode_rule": "accept if thickness_estimator AND lambda_norm AND vessel_margin fire inside the window; vendor_continue_advocate is necessary-but-not-sufficient and cannot release the lehr dump",
            "populations": [
                gate_pop("thickness_estimator", 80, 1.5, 50.0, w_s),
                gate_pop("lambda_norm", 64, 1.2, 31.25, w_s),
                gate_pop("vessel_margin", 40, 1.0, 50.0, w_s),
                gate_pop("vendor_continue_advocate", 32, 0.7, 25.0, w_s),
                gate_pop("accept_latch", 96, 1.8, 62.5, w_s),
            ],
        },
        "gate_compute": gate_compute(
            [
                {"check": "ch5.chrom_scorer", "neurons": 96, "mean_rate_hz": 50.0, "window_ms": 40.0},
                {"check": "ch5.thick_scorer", "neurons": 40, "mean_rate_hz": 62.5, "window_ms": 32.0},
            ]
        ),
        "meta": meta_common(
            id="nelb-r36-111",
            clock_domain="ch5-chrom-sim-relative-ms-t0-2026-08-19T04:00:00Z",
            tags=["confocal-chromatic", "ACCEPT", "REJECT", "serialized-reconstruction", "operational-t2"],
        ),
    }
