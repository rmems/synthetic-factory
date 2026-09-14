# ---------------------------------------------------------------------------
# Record 070 — scanning LDV Francis runner crack, designed, MODIFY / ACCEPT
# ---------------------------------------------------------------------------
def rec_070():
    assert abs(32.0 * 12.50 / 80.0 - 5.00) < 1e-12
    raster = make_raster(
        neurons=20,
        mean_rate_hz=50.0,
        window_ms=36.0,
        seed=20260970,
        source="sk5.nacre.ldv",
        target="skelwick.runner_crack_core",
        table=[
            {"from": "ldv_V_mV", "to": "disp_reconstructor", "weight": 1.40},
            {"from": "scan_coh_4x", "to": "fault_identity_core", "weight": 1.15},
            {"from": "scada_shaft_vib", "to": "production_advocate", "weight": 0.50},
        ],
        third_factor={
            "modulator": "na.runner_crack_salience",
            "tau_e_s": 1.6,
            "tau_e_ms": 1600.0,
            "eligibility": "pre-post coincidence on TE-opening synapses; the crack-salience modulator enables potentiation only while scan-coherence and 4x-shaft identity are co-active inside tau_e",
        },
        channel_prefix="ldv.n",
        anchor="SK-5 Nacre-ν 36 ms frame at V 12.50 mV / f 80.0 Hz (t_s 7200); reconstructed TE opening 5.00 um first exceeds the 4.00 um trip",
    )
    w_s = 0.036
    events = [
        ev(0.0, "scada.vib", 1.20, code="SHAFT_VIB", units="mm_s", note="SK-5 shaft single-point SCADA; alarm 2.50 mm/s"),
        ev(6.0e5, "scada.p", 38.0, code="RATED_MW", units="MW", note="38 MW Francis Gull-F9 holding rated on the freshet"),
        ev(1.2e6, "rpm.n", 1200.0, code="SHAFT_RPM", units="rpm"),
        ev(1.8e6, "f.rot", 20.0, code="F_ROT", units="Hz", note="1200/60 = 20.0 exact"),
        ev(2.4e6, "ldv.V", 4.80, code="V_MV", units="mV", note="Nacre-ν grid point 12, trailing-edge suction side"),
        ev(3.0e6, "recon.u", 1.92, code="DISP_UM", units="um", note="32.0*4.80/80.0 = 1.92 exact"),
        ev(3.6e6, "coh.scan", 0.25, code="COHERENCE", units="ratio", note="4 of 16 grid points hot"),
        ev(4.8e6, "ldv.V", 8.00, code="V_MV", units="mV"),
        ev(5.4e6, "recon.u", 3.20, code="DISP_UM", units="um", note="32.0*8.00/80.0 = 3.20"),
        ev(6.0e6, "scada.vib", 1.18, code="SHAFT_VIB", units="mm_s"),
        ev(7.2e6, "ldv.V", 12.50, code="V_MV", units="mV", note="authorization frame; raster sidecar"),
        ev(7200001.2, "ldv.V", 10.25, code="V_MV", units="mV", note="same-channel refractory 1.2 ms; amplitude adapted 0.82x plus noise"),
        ev(7200002.6, "ldv.V", 8.40, code="V_MV", units="mV", note="third LDV packet; adapted"),
        ev(7.32e6, "recon.u", 5.00, code="DISP_UM", units="um", note="32.0*12.50/80.0 = 5.00 exact; tripwire 4.00 um"),
        ev(7.44e6, "coh.scan", 0.62, code="COHERENCE", units="ratio", note="10 of 16 grid points hot"),
        ev(7.56e6, "f.peak", 80.0, code="F_PEAK", units="Hz", note="4*20.0 = 80.0; 4th shaft harmonic at the weld HAZ"),
        ev(8.4e6, "scada.vib", 1.20, code="STILL_UNDER_ALARM", units="mm_s", note="ops reads shaft vib as healthy; the denial channel"),
        ev(9.0e6, "scada.p", 37.9, code="STILL_RATED", units="MW"),
        ev(9.6e6, "ops.prop", 1.0, code="KEEP_RATED", units="bool", note="night ops Tamsin Wold: hold 38 MW through the freshet; grid-12 is a dust speckle"),
        ev(9.72e6, "gate.vib", 1.0, code="MODIFY", units="decision", note="derate 40 percent plus isolate Gull-F9"),
        ev(9.84e6, "derate.cmd", 40.0, code="DERATE_PCT", units="pct_rated"),
        ev(10.8e6, "isol.unit", 1.0, code="UNIT_ISOLATED", units="bool"),
        ev(12.0e6, "recon.u", 2.40, code="DISP_UM", units="um"),
        ev(13.2e6, "ldv.V", 6.00, code="V_MV", units="mV"),
        ev(14.4e6, "recon.u", 1.80, code="DISP_UM", units="um"),
        ev(15.6e6, "restore.cmd", 70.0, code="RESTORE_PCT", units="pct_rated", note="companion restore cap 70 percent after disp < 2.00 um"),
        ev(15.72e6, "coh.scan", 0.31, code="COHERENCE", units="ratio"),
        ev(16.8e6, "recon.u", 1.40, code="DISP_UM", units="um"),
        ev(16.92e6, "gate.exec", 1.0, code="ACCEPT", units="decision", note="companion t2: derate/isolate sequence completed"),
        ev(18.0e6, "scada.p", 15.2, code="PARTIAL_RESTORE", units="MW", note="40 percent of 38.0 MW = 15.2"),
        ev(18.6e6, "rpm.n", 840.0, code="SHAFT_RPM", units="rpm"),
        ev(19.2e6, "scada.vib", 0.71, code="SHAFT_VIB", units="mm_s"),
    ]
    assert_stream(events)

    traj = {
        "id": "nelb-r23-070-t1",
        "state": {
            "sim_or_real": "designed",
            "episode_id": "SK-LDV-2026-0412",
            "domain": "scanning_ldv_francis_runner",
            "setting": "Skelwick Hydro SK-5 (invented), 38 MW Francis Gull-F9. Nacre-ν 16-point scanning laser Doppler vibrometer on the trailing-edge suction side, 40 mm pitch. Night freshet: 1200 rpm, rated 38 MW. Invented plant; designed campaign. Not FBG glaze, not MEMS housing-array, not MsS T(0,1).",
            "observables_at_decision": {
                "V_mV": 12.50,
                "f_hz": 80.0,
                "disp_um": 5.00,
                "coherence_scan": 0.62,
                "scada_vib_mm_s": 1.20,
                "scada_mw": 37.9,
            },
            "margin_authority": "SK-5 runner SOP rev B: if reconstructed disp_um >= 4.00 AND scan-coherence >= 0.50 AND peak frequency matches 4*f_rot ±1 Hz, rated load is forbidden even if SCADA shaft vib is under the 2.50 mm/s alarm",
        },
        "proposed_action": {
            "actor": "night ops Tamsin Wold, citing shaft vib under alarm and no bearing-temp trip",
            "summary": "hold Gull-F9 at rated 38 MW through the freshet; treat grid-12 rise as a dust speckle on the LDV head",
            "basis_claimed": "SCADA shaft 1.20 mm/s is under 2.50; derate would cost 12 MWh on the freshet",
        },
        "safety_decision": {
            "decision": "MODIFY",
            "rationale": "Rated load is refused, not the unit. SOP rev B is conjunctive: reconstructed TE opening is 5.00 um (32.0 * 12.50 / 80.0, serialized) and scan-coherence is 0.62 and the peak sits at 4*f_rot 80.0 Hz (4*20.0), all over the 4.00 um / 0.50 / ±1 Hz floors, while SCADA still reads 1.20 mm/s. Holding rated load puts the weld HAZ in a growth regime. Ordered: derate to 40 percent rated, isolate Gull-F9 from grid-following, and hold the derate until disp_um < 2.00 AND coherence < 0.40. Shaft-vib agreement cannot substitute for the LDV reconstruction.",
            "threshold": "disp_um>=4.00 AND coherence>=0.50 AND |f-4*f_rot|<=1 Hz => forbid rated load",
            "stated_residuals": "12 MWh deferred on the freshet; 1x shaft 20.0 Hz is present and is not a release condition",
        },
        "executed_action": {
            "summary": "MODIFY at t_s 9720: 40 percent derate commanded, Gull-F9 isolated; disp 5.00 -> 1.40 um by t_s 16800",
            "tool": "sk5-ldv-runner-gate-cli",
            "observation": "wicket-gate derate reached 40 percent in 48 s; grid-12 fell 12.50 -> 6.00 mV by t_s 13200 with 80.0 Hz still identified, consistent with a TE opening not a dust speckle",
        },
        "future_outcome": {
            "timeline": [
                {"t_s": 7200.0, "event": "LDV V 12.50 mV; raster frame captured"},
                {"t_s": 7320.0, "event": "disp 5.00 um reconstructed; coherence 0.62; 4x 80.0 Hz"},
                {"t_s": 9600.0, "event": "ops proposes keep-rated"},
                {"t_s": 9720.0, "event": "MODIFY: derate 40 percent plus isolate"},
                {"t_s": 16920.0, "event": "companion execution ACCEPT; disp 1.40 um; power 15.2 MW"},
            ],
            "observed_effects": [
                "reconstructed opening is recomputable from the serialized model at every recon.u event",
                "SCADA shaft vib never left the alarm-free corridor until the derate, so a single-point head would have ACCEPTed",
                "coherence and 4x identity jointly crossed SOP rev B 40 s before the proposal",
            ],
            "surprises": [
                "bearing RTD stayed quiet the entire freshet; oil-temp is not a substitute TE-opening detector on this unit",
            ],
            "new_state": {
                "sk5": "partial restore 70 percent pending dawn dye-penetrant",
                "gull_f9": "isolated",
                "reconstruction_model": "discharged as an on-record calculator, not a referenced envelope",
            },
            "latency_ms": 48000.0,
        },
        "reward_components": reward(
            0.41,
            [
                ("ldv_disp_reconstruction", 0.14),
                ("conjunctive_sop_enforcement", 0.12),
                ("derate_plus_isolate", 0.10),
                ("shaft_vib_nonsubstitution", 0.08),
                ("production_deferral_cost", -0.03),
            ],
            "scored for refusing rated load on a recomputable scanning-LDV opening while SCADA shaft vib looked healthy; production_deferral_cost prices 12 MWh",
        ),
        "meta": meta_common(
            tags=["MODIFY", "scanning-ldv", "serialized-reconstruction", "operational-companion"],
            distillation_note="Francis gate: serialized V/f → um reconstruction plus 4x-shaft identity beats a clean shaft-vib corridor; companion t2 is the execution of the derate, not a governance vote",
        ),
    }
    traj2 = {
        "id": "nelb-r23-070-t2",
        "state": {
            "sim_or_real": "designed",
            "episode_id": "SK-LDV-2026-0412-exec",
            "domain": "francis_derate_isolate_execution",
            "setting": "Same SK-5 after the MODIFY. This companion is the operational derate/isolate sequence, not a second policy vote.",
            "observables_at_decision": {
                "derate_cmd_pct": 40.0,
                "disp_um": 5.00,
                "unit_isolated": True,
            },
        },
        "proposed_action": {
            "actor": "unit controller following the MODIFY",
            "summary": "execute 40 percent derate and Gull-F9 isolation, then restore to 70 percent when disp_um < 2.00 and coherence < 0.40",
            "basis_claimed": "MODIFY requirements are fully specified and in-envelope for the wicket-gate servo",
        },
        "safety_decision": {
            "decision": "ACCEPT",
            "rationale": "The execution envelope is intact: wicket-gate rate 1.6 deg/s is under the 2.2 deg/s freshet-load limit, isolation interlock is confirmed, and the restore condition (disp_um < 2.00 AND coherence < 0.40) is the same conjunctive pair the MODIFY used. ACCEPT the sequence. Do not restore to rated until dawn dye-penetrant; 70 percent is the cap tonight.",
            "threshold": "gate_rate<=2.2 deg/s AND unit_isolated AND restore_cap=70pct",
        },
        "executed_action": {
            "summary": "derate 40 percent in 48 s; unit isolated; restore 70 percent at t_s 15600 after disp 1.80 um and coherence 0.31",
            "tool": "sk5-derate-isolate-exec",
            "observation": "no overspeed; 80.0 Hz identity persisted at lower amplitude; power 15.2 MW",
        },
        "future_outcome": {
            "timeline": [
                {"t_s": 9840.0, "event": "derate 40 percent latched"},
                {"t_s": 10800.0, "event": "Gull-F9 isolation confirmed"},
                {"t_s": 15600.0, "event": "restore 70 percent after disp 1.80 um"},
            ],
            "observed_effects": [
                "disp 5.00 -> 1.40 um without a shaft-vib-only story",
                "restore stopped at 70 percent as capped; rated not re-entered",
            ],
            "new_state": {"sk5_power_mw": 15.2, "restore_cap_pct": 70.0},
            "latency_ms": 48000.0,
        },
        "reward_components": reward(
            0.29,
            [
                ("envelope_respect", 0.12),
                ("conjunctive_restore", 0.11),
                ("rated_not_reentered", 0.08),
                ("energy_cost", -0.02),
            ],
            "operational execution gate: the companion does the derate rather than re-arguing the TE-opening call",
        ),
        "meta": meta_common(tags=["ACCEPT", "operational-execution", "francis-isolate"]),
    }
    return {
        "id": "nelb-r23-070",
        "spike_events": events,
        "language_view": {
            "description": "Skelwick Hydro SK-5. Plant-owned scanning LDV reconstructs 5.00 um trailing-edge opening from 12.50 mV at 80.0 Hz while SCADA shaft vib still shows 1.20 mm/s. The gate MODIFYs to a 40 percent derate plus isolate; a companion execution ACCEPT runs the sequence and caps restore at 70 percent. The V/f model is serialized so every recon event recomputes.",
            "trajectory": traj,
            "trajectory_runner_derate_execution": traj2,
        },
        "bridge_notes": {
            "channel_map": {
                "ldv.V / f.peak / f.rot": "LDV photodiode millivolts and 4x-shaft identity; the physics channels the reconstruction consumes",
                "recon.u / coh.scan": "serialized TE opening um and scan-coherence",
                "scada.vib / scada.p": "shaft-vib and rated-power corridor; the denial channels that look healthy",
                "ops.prop / gate.vib / gate.exec": "keep-rated proposal, MODIFY, companion ACCEPT",
                "derate.cmd / isol.unit / restore.cmd": "operational companion channels",
            },
            "temporal_motifs": [
                "shaft-healthy while TE-opening-present: scada.vib 1.20 next to recon.u 5.00",
                "compensation as event: recon.u 5.00 equals 32.0*12.50/80.0",
                "MODIFY then operational ACCEPT: gate.vib at 9720 s, gate.exec at 16920 s",
                "tight LDV triplet: 1.2 ms then 1.4 ms at the raster frame with amplitude adaptation",
            ],
            "language_to_spike_mapping": "'dust speckle' = ldv.V 12.50 next to scada.vib 1.20; '5.00 um opening' = recon.u 5.00; 'forbid rated' = gate.vib MODIFY; 'execute the derate' = derate.cmd then companion ACCEPT",
            "why_high_value": "New scanning-LDV Francis-runner family (not FBG glaze, not MEMS HSS array, not MsS T(0,1)). First V/f displacement reconstruction that can hide a TE opening inside a shaft-vib corridor. Companion t2 is operational derate/isolate execution. sim_or_real=designed.",
            "encoder_spec": {
                "prng": "MT19937 via python random.Random",
                "seeds": {"raster": 20260970, "stream_note": "stream amplitudes are authored constants (mV, um, mm/s, MW, Hz, rpm, bool)"},
                "draw_order": "raster: per neuron id order, gap-constrained times, per-spike adaptation and noise",
                "thinning": "LDV scan exists at 2 kHz; stream keeps 5 V points; recon keeps 5 of ~40 solver ticks",
                "refractory_floors_ms": {
                    "scada.vib": 60000,
                    "scada.p": 60000,
                    "rpm.n": 60000,
                    "f.rot": 60000,
                    "ldv.V": 1.2,
                    "recon.u": 60000,
                    "coh.scan": 60000,
                    "f.peak": 60000,
                    "ops.prop": 60000,
                    "gate.vib": 60000,
                    "derate.cmd": 60000,
                    "isol.unit": 60000,
                    "restore.cmd": 60000,
                    "gate.exec": 60000,
                },
                "time_alias": "t_rel_ms; t0 = 2026-04-12T03:00:00Z campaign start",
            },
            "distillation_targets": [
                "LDV reconstruction head: disp_um = G * V_mV / f_hz",
                "conjunctive SOP that a clean shaft-vib corridor cannot substitute for",
                "operational companion: execute the derate without re-opening the crack call",
            ],
        },
        "reconstruction_model": {
            "name": "ldv_v_over_f_displacement",
            "formula": "disp_um = G_ldv * V_mV / f_hz",
            "parameters": {
                "G_ldv_um_hz_per_mV": 32.0,
                "f_hz": 80.0,
                "tripwire_um": 4.00,
                "restore_um": 2.00,
                "f_rot_hz": 20.0,
            },
            "worked_example": {"V_mV": 12.50, "f_hz": 80.0, "disp_um": 5.00},
            "check": "32.0 * 12.50 / 80.0 = 5.00 exactly; 4 * 20.0 = 80.0",
        },
        "raster": raster,
        "gate_snn": {
            "decision": "MODIFY",
            "decision_window_ms": 36.0,
            "decision_window_s": 0.036,
            "code": "sk5.runner_crack_gate",
            "note": "MODIFY accumulator wins: disp reconstruction and 4x identity overpower the shaft-vib advocate",
            "decode_rule": "modify-derate if disp_reconstructor AND fault_identity fire inside the window; production_advocate is necessary-but-not-sufficient and cannot keep rated load",
            "populations": [
                gate_pop("disp_reconstructor", 80, 1.5, 50.0, w_s),
                gate_pop("fault_identity", 64, 1.2, 31.25, w_s),
                gate_pop("scan_margin", 40, 1.0, 50.0, w_s),
                gate_pop("shaft_vib_advocate", 40, 0.8, 25.0, w_s),
                gate_pop("modify_latch", 96, 1.8, 62.5, w_s),
            ],
        },
        "gate_compute": gate_compute(
            [
                {"check": "sk5.disp_scorer", "neurons": 80, "mean_rate_hz": 50.0, "window_ms": 36.0},
                {"check": "sk5.peak_scorer", "neurons": 40, "mean_rate_hz": 50.0, "window_ms": 32.0},
            ]
        ),
        "meta": meta_common(
            id="nelb-r23-070",
            clock_domain="sk5-ldv-campaign-relative-ms-t0-2026-04-12T03:00:00Z",
            tags=["scanning-ldv", "MODIFY", "ACCEPT", "serialized-reconstruction", "operational-t2"],
        ),
    }


# ---------------------------------------------------------------------------
# Record 071 — THz TDS sonar-dome coating, HIL, REJECT / MODIFY
# ---------------------------------------------------------------------------
def rec_071():
    assert abs(300.0 * 8.00 / (2 * 1.50) - 800.0) < 1e-12
    assert 8400 + 1200 == 9600
    raster = make_raster(
        neurons=16,
        mean_rate_hz=50.0,
        window_ms=40.0,
        seed=20260971,
        source="bd4.mothreed.thz",
        target="whinholt.coating_launch_core",
        table=[
            {"from": "thz_dt_ps", "to": "thickness_estimator", "weight": 1.35},
            {"from": "n_gfrp", "to": "index_norm_core", "weight": 1.20},
            {"from": "kelpcoat_log", "to": "vendor_launch_advocate", "weight": 0.35},
        ],
        third_factor={
            "modulator": "da.coating_thickness_error",
            "tau_e_s": 0.9,
            "tau_e_ms": 900.0,
            "eligibility": "pre-post coincidence on echo-delay synapses; the thickness-error modulator depresses launch links when dt stays high inside tau_e of a plant-owned coupon sample",
        },
        channel_prefix="thz.n",
        anchor="BD-4 Mothreed TDS 40 ms frame at dt 8.00 ps / n 1.50 (t_s 5400) that reconstructs 800.0 um remaining coating against a 1800 um spec floor",
    )
    w_s = 0.040
    events = [
        ev(0.0, "thz.dt", 4.00, code="DT_PS", units="ps", note="HIL pit spare GFRP dome BD-4; Mothreed reflection TDS"),
        ev(6.0e5, "n.gfrp", 1.50, code="N_GFRP", units="index"),
        ev(1.2e6, "recon.t", 400.0, code="T_UM", units="um", note="300.0*4.00/(2*1.50) = 400.0 exact"),
        ev(1.8e6, "vend.t", 2.00, code="VENDOR_MM", units="mm", note="Kelpcoat cloud coating log; the only OEM thickness SoT"),
        ev(2.4e6, "coupon.t", 800.0, code="COUPON_UM", units="um", note="plant-owned GFRP coupon of known 800 um paint; HIL witness"),
        ev(3.0e6, "thz.dt", 6.00, code="DT_PS", units="ps"),
        ev(3.6e6, "recon.t", 600.0, code="T_UM", units="um", note="300.0*6.00/(2*1.50) = 600.0"),
        ev(4.2e6, "pit.T", 18.0, code="PIT_C", units="C", note="pit air looks cool; a thermal corridor is not a coating license"),
        ev(4.8e6, "vend.t", 2.00, code="VENDOR_MM", units="mm"),
        ev(5.4e6, "thz.dt", 8.00, code="DT_PS", units="ps", note="launch-authorization frame; raster sidecar"),
        ev(5400001.2, "thz.dt", 6.56, code="DT_PS", units="ps", note="same-channel refractory 1.2 ms; amplitude adapted"),
        ev(5400002.6, "thz.dt", 5.38, code="DT_PS", units="ps", note="third echo packet; adapted"),
        ev(5.52e6, "recon.t", 800.0, code="T_UM", units="um", note="300.0*8.00/(2*1.50) = 800.0 exact; spec floor 1800 um"),
        ev(5.64e6, "n.gfrp", 1.50, code="N_GFRP", units="index"),
        ev(5.76e6, "coupon.t", 800.0, code="COUPON_AGREE", units="um", note="coupon matches the reconstruction; Kelpcoat does not"),
        ev(6.6e6, "vend.t", 2.00, code="VENDOR_MM", units="mm"),
        ev(7.2e6, "hull.slot", 1.0, code="SLOT_TONIGHT", units="bool", note="Kestrel-7 undock window; BD-4 is the staged spare"),
        ev(7.8e6, "ops.prop", 1.0, code="LAUNCH_BD4", units="bool", note="dock boss Orrin Glaur: keep the slot, fit BD-4; Kelpcoat 2.00 mm is green"),
        ev(7.92e6, "gate.thz", 1.0, code="REJECT", units="decision", note="launch-with-BD-4 refused"),
        ev(8.04e6, "bd4.hold", 1.0, code="BD4_HELD", units="bool"),
        ev(8.4e6, "swap.start", 1.0, code="SWAP_START", units="bool", note="bookend 1 of the 20.0 min BD-5 swap floor"),
        ev(9.0e6, "pit.T", 19.0, code="PIT_C", units="C", note="in-stream marker during the swap floor"),
        ev(9.6e6, "swap.floor", 1.0, code="SWAP_FLOOR", units="bool", note="8400 s + 1200 s = 9600 s = 20.0 min"),
        ev(9.72e6, "bd5.dt", 21.00, code="DT_PS", units="ps", note="BD-5 plant TDS; 300.0*21.00/(2*1.50) = 2100 um"),
        ev(9.84e6, "recon.bd5", 2100.0, code="T_UM", units="um"),
        ev(9.96e6, "gate.swap", 1.0, code="MODIFY", units="decision", note="companion t2: swap to BD-5 rather than cancel the slot"),
        ev(10.08e6, "bd5.fit", 1.0, code="BD5_FIT", units="bool"),
        ev(10.2e6, "vend.t", 2.00, code="VENDOR_MM", units="mm", note="Kelpcoat still claims BD-4 is 2.00 mm"),
        ev(10.8e6, "slot.kept", 1.0, code="SLOT_KEPT", units="bool"),
        ev(11.4e6, "coupon.t", 800.0, code="COUPON_UM", units="um"),
        ev(12.0e6, "bd4.hold", 1.0, code="BD4_HELD", units="bool"),
    ]
    assert_stream(events)

    traj = {
        "id": "nelb-r23-071-t1",
        "state": {
            "sim_or_real": "hil",
            "episode_id": "WH-THZ-2026-0219",
            "domain": "thz_tds_sonar_dome_coating",
            "setting": "Whinholt Sonar Works (invented). HIL pit spare GFRP dome Brine-Dome BD-4 times a live Kestrel-7 undock. Mothreed 0.1-2.5 THz reflection TDS is plant-owned. Kelpcoat OEM cloud is the only coating-log SoT and is not admissible. Not industrial x-ray DR, not BOTDA wall-loss, not SPAD ToF LiDAR.",
            "observables_at_decision": {
                "dt_ps": 8.00,
                "n_gfrp": 1.50,
                "t_um": 800.0,
                "vendor_mm": 2.00,
                "coupon_um": 800.0,
                "spec_floor_um": 1800.0,
            },
            "margin_authority": "WH undock SOP rev D: a spare dome may fit only if reconstructed t_um >= 1800 AND the authorization covers this dome this hull. A vendor coating log cannot clear a launch. BD-4 is out of spec at 800 um.",
        },
        "proposed_action": {
            "actor": "dock boss Orrin Glaur, citing Kelpcoat 2.00 mm and a cool pit",
            "summary": "fit BD-4 onto Kestrel-7 and keep tonight's undock slot",
            "basis_claimed": "Kelpcoat log is green at 2.00 mm against a 1.80 mm spec and cancelling the slot costs a tide",
        },
        "safety_decision": {
            "decision": "REJECT",
            "rationale": "Launch-with-BD-4 is refused. Serialized reconstruction: t_um = 300.0 * dt_ps / (2 * n_gfrp) = 300.0 * 8.00 / (2 * 1.50) = 800.0, under the 1800 um spec floor. Plant-owned coupon agrees at 800 um; Kelpcoat 2.00 mm is vendor-writable and disagrees by 1.20 mm. Ordered: do not fit BD-4. Scope: this REJECT does not cancel the undock slot (that is the companion question) and does not scrap the hull.",
            "threshold": "t_um<1800 OR coupon disagrees with vendor => forbid fit of this dome; Kelpcoat is not SoT",
            "stated_residuals": "slot still needs a dome; BD-4 remains a repair candidate; Kelpcoat remains the only OEM log",
        },
        "executed_action": {
            "summary": "REJECT at t_s 7920: BD-4 not fitted; Kelpcoat channel not used as SoT; reconstruction locked",
            "tool": "wh-thz-launch-gate-cli",
            "observation": "t 800.0 um recomputes from dt 8.00 ps and n 1.50; coupon agrees; hull slot still open",
        },
        "future_outcome": {
            "timeline": [
                {"t_s": 5400.0, "event": "THz dt 8.00 ps; raster frame; t 800.0 um"},
                {"t_s": 7800.0, "event": "ops proposes fit BD-4"},
                {"t_s": 7920.0, "event": "REJECT launch-with-BD-4"},
                {"t_s": 8400.0, "event": "swap bookend 1"},
                {"t_s": 9600.0, "event": "20.0 min floor; companion MODIFY swap to BD-5"},
            ],
            "observed_effects": [
                "thickness recomputes from the serialized TDS model at every recon.t event",
                "a Kelpcoat-only head would have fitted BD-4 on a 2.00 mm corridor",
                "20.0 min swap floor is in the stream (swap.start, pit.T marker, swap.floor), not only in the companion timeline",
            ],
            "surprises": [
                "a cool pit and a green vendor log co-existed with an 800 um reconstruction that the coupon independently matched",
            ],
            "new_state": {
                "bd4": "held, not fitted",
                "kestrel7_slot": "open pending BD-5",
                "kelpcoat": "not SoT",
            },
            "latency_ms": 1680000.0,
        },
        "reward_components": reward(
            0.43,
            [
                ("thz_tds_reconstruction", 0.15),
                ("launch_refusal", 0.12),
                ("vendor_log_nonsubstitution", 0.10),
                ("coupon_agreement", 0.09),
                ("slot_deferral_cost", -0.03),
            ],
            "scored for refusing a dome fit on a recomputable THz thickness while a vendor coating log looked green; coupon agreement is the HIL witness",
        ),
        "meta": meta_common(
            tags=["REJECT", "thz-tds", "serialized-reconstruction", "operational-companion"],
            distillation_note="THz coating gate: echo-delay reconstruction beats a green vendor log; companion t2 swaps the spare rather than cancelling the slot",
        ),
    }
    traj2 = {
        "id": "nelb-r23-071-t2",
        "state": {
            "sim_or_real": "hil",
            "episode_id": "WH-THZ-2026-0219-swap",
            "domain": "dome_swap_execution",
            "setting": "Same Whinholt pit after the REJECT. Dock boss proposes cancelling the undock. Operational quality gate: swap to BD-5 (plant TDS 2100 um) after a 20.0 min floor, rather than freeze-kill the slot.",
            "observables_at_decision": {
                "bd5_t_um": 2100.0,
                "swap_floor_min": 20.0,
                "bd4_held": 1,
                "spec_floor_um": 1800.0,
            },
        },
        "proposed_action": {
            "actor": "dock boss Orrin Glaur",
            "summary": "cancel tonight's undock; BD-4 failed and there is no time to certify another dome",
            "basis_claimed": "the tide window is 40 min and a second TDS would miss it",
        },
        "safety_decision": {
            "decision": "MODIFY",
            "rationale": "Cancel is refused, and BD-4 is not fitted. BD-5 plant TDS reconstructs 2100.0 um (300.0 * 21.00 / (2 * 1.50)), which clears 1800 um, and the 20.0 min swap floor is already in the stream (8400 + 1200 = 9600 s). Ordered: fit BD-5, keep the slot, leave BD-4 held. Scope: this MODIFY does not re-open BD-4 and does not treat Kelpcoat as SoT on BD-5 either.",
            "threshold": "bd5_t_um>=1800 AND swap_floor_elapsed AND bd4_not_fitted",
        },
        "executed_action": {
            "summary": "MODIFY at t_s 9960: BD-5 fitted; slot kept; BD-4 held; Kelpcoat not SoT",
            "tool": "wh-dome-swap-exec",
            "observation": "BD-5 2100 um; 20.0 min floor marked; slot.kept 1",
        },
        "future_outcome": {
            "timeline": [
                {"t_s": 8400.0, "event": "swap clock started"},
                {"t_s": 9600.0, "event": "20.0 min floor marked"},
                {"t_s": 9960.0, "event": "MODIFY fit BD-5; keep slot"},
            ],
            "observed_effects": [
                "REJECT was not converted into a cancelled tide",
                "BD-5 reconstruction is the same TDS model, not a vendor log",
            ],
            "new_state": {
                "bd5": "fitted",
                "bd4": "held",
                "slot": "kept",
            },
            "latency_ms": 1560000.0,
        },
        "reward_components": reward(
            0.33,
            [
                ("swap_not_cancel", 0.13),
                ("bd5_reconstruction", 0.11),
                ("floor_in_stream", 0.08),
                ("bd4_not_reopened", 0.04),
                ("swap_labor_cost", -0.03),
            ],
            "operational execution gate: the companion swaps the spare rather than freeze-killing the undock after the REJECT",
        ),
        "meta": meta_common(tags=["MODIFY", "operational-execution", "hil-swap"]),
    }
    return {
        "id": "nelb-r23-071",
        "spike_events": events,
        "language_view": {
            "description": "Whinholt Sonar Works HIL pit. Plant-owned THz TDS reconstructs 800.0 um remaining coating on spare dome BD-4 from an 8.00 ps echo at n 1.50 while Kelpcoat vendor log still shows 2.00 mm. The gate REJECTS fitting BD-4. Companion t2 MODIFYs a slot-cancel into a 20.0 min swap onto BD-5 (2100 um). The delay model is serialized so every recon event recomputes.",
            "trajectory": traj,
            "trajectory_dome_swap_execution": traj2,
        },
        "bridge_notes": {
            "channel_map": {
                "thz.dt / n.gfrp": "echo delay and GFRP index; the physics channels the reconstruction consumes",
                "recon.t / recon.bd5": "serialized remaining coating um",
                "vend.t / pit.T": "vendor coating log and cool-pit corridor; the denial channels",
                "coupon.t": "HIL coupon of known 800 um; collusion-independent witness",
                "ops.prop / gate.thz / gate.swap": "fit-BD-4 proposal, REJECT, companion MODIFY",
                "swap.start / swap.floor / bd5.fit / slot.kept": "operational companion channels",
            },
            "temporal_motifs": [
                "vendor-healthy while coating-thin: vend.t 2.00 next to recon.t 800.0",
                "compensation as event: recon.t 800.0 equals 300.0*8.00/(2*1.50)",
                "REJECT then operational MODIFY: gate.thz at 7920 s, gate.swap at 9960 s",
                "slow swap floor as events: swap.start, pit.T marker, swap.floor at 20.0 min",
                "tight TDS triplet: 1.2 ms then 1.4 ms at the raster frame",
            ],
            "language_to_spike_mapping": "'Kelpcoat is green' = vend.t 2.00 next to recon.t 800; '800 um remaining' = recon.t 800.0; 'do not fit BD-4' = gate.thz REJECT; 'swap not cancel' = gate.swap MODIFY plus slot.kept",
            "why_high_value": "New THz-TDS coating-thickness family (not industrial x-ray DR, not BOTDA remaining-wall, not SPAD ToF). First echo-delay reconstruction that a vendor coating log would have cleared. 20.0 min swap floor is in the stream. Companion t2 is operational spare-swap, not a cancelled tide. sim_or_real=hil.",
            "encoder_spec": {
                "prng": "MT19937 via python random.Random",
                "seeds": {"raster": 20260971, "stream_note": "stream amplitudes are authored constants (ps, um, mm, C, index, bool)"},
                "draw_order": "raster: per neuron id order, gap-constrained times, per-spike adaptation and noise",
                "thinning": "THz waveform exists at 50 Hz; stream keeps 4 dt points plus BD-5; recon keeps 4 of ~40 solver ticks",
                "refractory_floors_ms": {
                    "thz.dt": 1.2,
                    "n.gfrp": 60000,
                    "recon.t": 60000,
                    "vend.t": 60000,
                    "coupon.t": 60000,
                    "pit.T": 60000,
                    "hull.slot": 60000,
                    "ops.prop": 60000,
                    "gate.thz": 60000,
                    "bd4.hold": 60000,
                    "swap.start": 60000,
                    "swap.floor": 60000,
                    "bd5.dt": 60000,
                    "recon.bd5": 60000,
                    "gate.swap": 60000,
                    "bd5.fit": 60000,
                    "slot.kept": 60000,
                },
                "time_alias": "t_rel_ms; t0 = 2026-02-19T21:00:00Z HIL campaign start",
            },
            "distillation_targets": [
                "THz TDS reconstruction head: t = c * dt / (2 * n)",
                "launch refusal vs vendor-log nonsubstitution",
                "operational companion: swap-the-spare rather than cancel-the-slot after a REJECT",
                "slow swap floor as events: two bookends plus a temperature marker at 20.0 min",
            ],
        },
        "reconstruction_model": {
            "name": "thz_tds_echo_delay_thickness",
            "formula": "t_um = c_um_ps * dt_ps / (2 * n_gfrp)",
            "parameters": {
                "c_um_ps": 300.0,
                "n_gfrp": 1.50,
                "spec_floor_um": 1800.0,
                "swap_floor_min": 20.0,
            },
            "worked_example": {"dt_ps": 8.00, "t_um": 800.0, "bd5_dt_ps": 21.00, "bd5_t_um": 2100.0},
            "check": "300.0 * 8.00 / (2 * 1.50) = 800.0 exactly; 300.0 * 21.00 / (2 * 1.50) = 2100.0; 8400 s + 1200 s = 9600 s = 20.0 min floor",
        },
        "raster": raster,
        "gate_snn": {
            "decision": "REJECT",
            "decision_window_ms": 40.0,
            "decision_window_s": 0.040,
            "code": "wh.thz_launch_gate",
            "note": "REJECT accumulator wins: thickness evidence overpowers the vendor-launch advocate (weight 0.35)",
            "decode_rule": "reject-hold if thickness_estimator AND index_norm fire; vendor_launch_advocate is below threshold by design",
            "populations": [
                gate_pop("thickness_estimator", 80, 1.5, 50.0, w_s),
                gate_pop("index_norm", 64, 1.3, 31.25, w_s),
                gate_pop("vendor_launch_advocate", 32, 0.7, 25.0, w_s),
                gate_pop("reject_latch", 96, 1.8, 62.5, w_s),
            ],
        },
        "gate_compute": gate_compute(
            [
                {"check": "wh.thz_scorer", "neurons": 96, "mean_rate_hz": 50.0, "window_ms": 40.0},
                {"check": "wh.delay_scorer", "neurons": 40, "mean_rate_hz": 50.0, "window_ms": 32.0},
            ]
        ),
        "meta": meta_common(
            id="nelb-r23-071",
            clock_domain="wh-thz-hil-relative-ms-t0-2026-02-19T21:00:00Z",
            tags=["thz-tds", "REJECT", "MODIFY", "vendor-coating", "hil", "operational-t2"],
        ),
    }


# ---------------------------------------------------------------------------
# Record 072 — electrochemical noise CUI on black-liquor header, simulated, ACCEPT / REJECT
# ---------------------------------------------------------------------------
def rec_072():
    assert abs(48.0 / 12.0 - 4.00) < 1e-12
    raster = make_raster(
        neurons=25,
        mean_rate_hz=50.0,
        window_ms=28.0,
        seed=20260972,
        source="pk9.pell.en",
        target="pellwick.cui_isolate_core",
        table=[
            {"from": "en_sigma_E", "to": "rn_estimator", "weight": 1.30},
            {"from": "en_sigma_I", "to": "current_norm_core", "weight": 1.25},
            {"from": "foamveil_rtd", "to": "keep_header_advocate", "weight": 0.45},
        ],
        third_factor={
            "modulator": "ach.cui_noise_conflict",
            "tau_e_s": 2.2,
            "tau_e_ms": 2200.0,
            "eligibility": "pre-post coincidence on EN-resistance synapses; the CUI-conflict modulator enables potentiation only while current-skewness is co-active inside tau_e so a dry lagging-RTD corridor cannot hide a pit",
        },
        channel_prefix="en.n",
        anchor="PK-9 Pell-EN 28 ms frame at sigma_E 48.0 uV / sigma_I 12.0 nA (t_s 5400) that reconstructs R_n 4.00 kOhm under the 5.00 kOhm pit floor",
    )
    w_s = 0.028
    events = [
        ev(0.0, "en.E", 18.0, code="SIGMA_E", units="uV", note="simulated sealed EN coupon under PU foam on Lye-H3"),
        ev(6.0e5, "en.I", 4.0, code="SIGMA_I", units="nA"),
        ev(1.2e6, "recon.Rn", 4.50, code="RN_KOHM", units="kOhm", note="18.0/4.0 = 4.50 exact"),
        ev(1.8e6, "dcs.T", 82.0, code="LAGGING_C", units="C", note="Foamveil vendor lagging RTD; reads dry"),
        ev(2.4e6, "skew.I", 0.41, code="SKEW", units="ratio"),
        ev(3.0e6, "en.E", 32.0, code="SIGMA_E", units="uV"),
        ev(3.6e6, "en.I", 8.0, code="SIGMA_I", units="nA"),
        ev(4.2e6, "recon.Rn", 4.00, code="RN_KOHM", units="kOhm", note="32.0/8.0 = 4.00"),
        ev(4.8e6, "dcs.T", 81.0, code="LAGGING_C", units="C"),
        ev(5.4e6, "en.E", 48.0, code="SIGMA_E", units="uV", note="pit-class frame; raster sidecar"),
        ev(5400001.3, "en.I", 12.0, code="SIGMA_I", units="nA", note="1.3 ms current-norm after E"),
        ev(5.52e6, "recon.Rn", 4.00, code="RN_KOHM", units="kOhm", note="48.0/12.0 = 4.00 exact; pit floor 5.00 kOhm"),
        ev(5.64e6, "skew.I", 0.92, code="SKEW", units="ratio", note="localized; floor 0.80"),
        ev(5.76e6, "dcs.T", 82.0, code="STILL_DRY", units="C", note="ops reads lagging as dry; the denial channel"),
        ev(6.6e6, "foam.ok", 1.0, code="JACKET_INTACT", units="bool", note="outer jacket looks intact; a visual corridor is not a CUI license"),
        ev(7.2e6, "ops.prop", 1.0, code="KEEP_HEADER", units="bool", note="shift super Ned Pell: keep 100 percent liquor; Foamveil 82 C is dry"),
        ev(7.8e6, "gate.cui", 1.0, code="ACCEPT", units="decision", note="bounded ACCEPT: isolate weld W-17 to W-18 this spool only"),
        ev(7.92e6, "isol.spool", 1.0, code="SPOOL_ISOLATED", units="bool"),
        ev(8.4e6, "header.pct", 80.0, code="HEADER_PCT", units="pct", note="remainder of Lye-H3 held at 80 percent"),
        ev(9.0e6, "wrap.prop", 1.0, code="HOT_WRAP", units="bool", note="Pell: hot-wrap the coupon to restore takt; bury Pell-EN under new foam"),
        ev(9.6e6, "gate.wrap", 1.0, code="REJECT", units="decision", note="companion t2: refuse wrap that would hide the only plant-owned CUI witness"),
        ev(9.72e6, "coupon.live", 1.0, code="COUPON_LIVE", units="bool"),
        ev(10.8e6, "recon.Rn", 3.90, code="RN_KOHM", units="kOhm"),
        ev(11.4e6, "dcs.T", 80.0, code="LAGGING_C", units="C"),
        ev(12.0e6, "skew.I", 0.88, code="SKEW", units="ratio"),
        ev(12.6e6, "isol.held", 1.0, code="SPOOL_HELD", units="bool"),
        ev(13.2e6, "en.E", 49.2, code="SIGMA_E", units="uV"),
        ev(13.8e6, "trip.hold", 0.0, code="ESD_TRIP", units="bool", note="R_n 3.90 vs 2.00 kOhm ESD floor; trip not taken"),
        ev(14.4e6, "header.pct", 80.0, code="HEADER_HELD", units="pct"),
        ev(15.0e6, "foam.ok", 1.0, code="JACKET_INTACT", units="bool"),
    ]
    assert_stream(events)

    traj = {
        "id": "nelb-r23-072-t1",
        "state": {
            "sim_or_real": "simulated",
            "episode_id": "PK-EN-2026-0703",
            "domain": "en_cui_black_liquor_header",
            "setting": "Pellwick Pulp PK-9 (invented), insulated black-liquor header Lye-H3. Simulated sealed electrochemical-noise coupon (Pell-EN) under PU foam between welds W-17 and W-18. Foamveil OEM lagging-RTD cloud is a corridor witness, not the CUI SoT. Not Cinderwell MsS steam, not QCM-D fouling, not clamp-on transit-time.",
            "observables_at_decision": {
                "sigma_E_uV": 48.0,
                "sigma_I_nA": 12.0,
                "R_n_kOhm": 4.00,
                "skew": 0.92,
                "dcs_T_C": 82.0,
                "pit_floor_kOhm": 5.00,
            },
            "margin_authority": "PK-9 CUI SOP rev A: if reconstructed R_n_kOhm < 5.00 AND current-skewness >= 0.80, isolate this spool (W-17 to W-18) even if Foamveil lagging RTD reads dry. ESD tripwire R_n < 2.00. Remainder of Lye-H3 is out of this authorization.",
        },
        "proposed_action": {
            "actor": "shift super Ned Pell, citing Foamveil 82 C dry and an intact jacket",
            "summary": "keep Lye-H3 at 100 percent liquor through the cook; treat EN drop as a wet-foam nuisance",
            "basis_claimed": "Foamveil is dry, the jacket is intact, and isolating a spool mid-cook costs 40 t of liquor",
        },
        "safety_decision": {
            "decision": "ACCEPT",
            "rationale": "This spool is isolated, not the header. Serialized reconstruction: R_n_kOhm = sigma_E_uV / sigma_I_nA = 48.0 / 12.0 = 4.00, under the 5.00 kOhm pit floor, with skew 0.92 over 0.80. SOP rev A still forbids a whole-header cut: ordered isolate of welds W-17 to W-18 only, remainder at 80 percent. Explicit scope: this accept does not cover adjacent spools without a new coupon and does not arm an ESD. Tripwire: R_n < 2.00. Foamveil 82 C is vendor-writable lagging-RTD and is not an admissible keep-flow witness.",
            "threshold": "R_n<5.00 AND skew>=0.80 AND spool=W17-W18 AND remainder_not_cut",
            "stated_residuals": "1.00 kOhm margin to ESD is not infinite; 6 m of liquor line still carries pit variance; Foamveil is not a wall-loss witness",
        },
        "executed_action": {
            "summary": "ACCEPT at t_s 7800: W-17 to W-18 isolated; remainder 80 percent; reconstruction locked as SoT",
            "tool": "pk9-en-cui-gate-cli",
            "observation": "R_n 4.00 kOhm recomputes from 48.0 uV and 12.0 nA; coupon remains live as the ESD interlock",
        },
        "future_outcome": {
            "timeline": [
                {"t_s": 5400.0, "event": "EN 48.0 uV / 12.0 nA; raster frame; R_n 4.00 kOhm"},
                {"t_s": 7200.0, "event": "ops proposes keep 100 percent header"},
                {"t_s": 7800.0, "event": "ACCEPT bounded spool isolate"},
                {"t_s": 9000.0, "event": "hot-wrap proposed"},
                {"t_s": 9600.0, "event": "companion REJECT wrap"},
            ],
            "observed_effects": [
                "R_n recomputes from the serialized EN model at every recon.Rn event",
                "a Foamveil-only head would have kept 100 percent liquor on an 82 C dry corridor",
                "peak R_n 3.90 stayed over the 2.00 kOhm ESD floor",
            ],
            "surprises": [
                "outer jacket stayed visually intact; a walk-down-only head would have treated intact cladding as a license",
            ],
            "new_state": {
                "w17_w18": "isolated",
                "lye_h3_remainder": "80 percent",
                "reconstruction_model": "discharged as an on-record calculator",
            },
            "latency_ms": 2400000.0,
        },
        "reward_components": reward(
            0.40,
            [
                ("en_rn_reconstruction", 0.14),
                ("bounded_spool_accept", 0.12),
                ("header_not_cut", 0.10),
                ("esd_tripwire_armed", 0.07),
                ("liquor_deferral_cost", -0.03),
            ],
            "scored for an earned ACCEPT of this spool on a recomputable EN resistance while refusing a dry-RTD corridor plus whole-header cut",
        ),
        "meta": meta_common(
            tags=["ACCEPT", "en-cui", "serialized-reconstruction", "operational-companion"],
            distillation_note="EN CUI gate: sigma_E/sigma_I reconstruction beats a dry lagging-RTD corridor; companion t2 refuses a wrap that would hide the coupon",
        ),
    }
    traj2 = {
        "id": "nelb-r23-072-t2",
        "state": {
            "sim_or_real": "simulated",
            "episode_id": "PK-EN-2026-0703-wrap",
            "domain": "cui_coupon_wrap_refusal",
            "setting": "Same PK-9 after the bounded ACCEPT. Shift super proposes a hot-wrap that would bury the Pell-EN coupon under new foam to restore takt. Operational quality gate, not a disclosure vote.",
            "observables_at_decision": {
                "wrap_proposed": 1,
                "coupon_live": 1,
                "R_n_kOhm": 3.90,
                "independent_wt_present": 0,
            },
        },
        "proposed_action": {
            "actor": "shift super Ned Pell",
            "summary": "hot-wrap W-17 to W-18 now that the spool is isolated; bury the coupon, restore takt on the remainder",
            "basis_claimed": "the isolate is already paid and Foamveil never left 80 C dry",
        },
        "safety_decision": {
            "decision": "REJECT",
            "rationale": "Wrap is refused. The coupon is the only plant-owned CUI witness on Lye-H3: independent wall-thickness is 0, Foamveil is vendor-writable, and R_n still reads 3.90 kOhm under the pit floor. Ordered: leave the coupon live, do not wrap, hold the isolate. The gate must refuse on custody plus reconstruction, not on a magnitude fight against 80 C. Do not convert the refusal into a personnel action on Pell.",
            "threshold": "wrap requires independent wall-thickness OR R_n>=8.00 with coupon remaining live; neither holds",
        },
        "executed_action": {
            "summary": "REJECT at t_s 9600: wrap not taken; coupon live; Pell not referred",
            "tool": "pk9-en-custody-gate-cli",
            "observation": "coupon.live stayed 1; recon.Rn 3.90; header 80 percent held",
        },
        "future_outcome": {
            "timeline": [
                {"t_s": 9000.0, "event": "hot-wrap proposed"},
                {"t_s": 9600.0, "event": "REJECT wrap; coupon remains live"},
                {"t_s": 12600.0, "event": "isolate held; ESD not taken"},
            ],
            "observed_effects": [
                "refusal is structural (wrap would hide the only plant EN) plus reconstruction still in pit class, not a magnitude argument against 80 C",
                "spool ACCEPT was not re-opened as an ESD",
            ],
            "new_state": {
                "wrap": "not taken",
                "coupon": "live",
                "pell": "not referred",
            },
            "latency_ms": 600000.0,
        },
        "reward_components": reward(
            0.36,
            [
                ("coupon_custody_refusal", 0.13),
                ("wrap_not_hiding_sot", 0.12),
                ("isolate_held", 0.09),
                ("no_personnel_reopen", 0.05),
                ("takt_cost", -0.03),
            ],
            "operational refusal: wrap dies on hiding the only plant-owned CUI witness plus EN still in pit class",
        ),
        "meta": meta_common(tags=["REJECT", "operational-execution", "coupon-custody"]),
    }
    return {
        "id": "nelb-r23-072",
        "spike_events": events,
        "language_view": {
            "description": "Pellwick Pulp PK-9 simulated EN coupon. Photo-current noise 48.0 uV / 12.0 nA reconstructs R_n 4.00 kOhm under the 5.00 kOhm pit floor while Foamveil vendor lagging RTD still shows 82 C dry. The gate ACCEPTs isolate of welds W-17 to W-18 only. Companion t2 REJECTS a hot-wrap that would bury the only plant-owned CUI witness. The R_n model is serialized so every recon event recomputes.",
            "trajectory": traj,
            "trajectory_coupon_wrap_refusal": traj2,
        },
        "bridge_notes": {
            "channel_map": {
                "en.E / en.I": "EN potential and current RMS; the physics channels the reconstruction consumes",
                "recon.Rn / skew.I": "serialized noise resistance and localization skew",
                "dcs.T / foam.ok": "vendor lagging RTD and intact-jacket corridor; the denial channels",
                "ops.prop / gate.cui / gate.wrap": "keep-header proposal, bounded ACCEPT, companion REJECT",
                "isol.spool / header.pct / coupon.live": "operational companion channels",
            },
            "temporal_motifs": [
                "lagging-dry while pit-present: dcs.T 82 next to recon.Rn 4.00",
                "compensation as event: recon.Rn 4.00 equals 48.0/12.0",
                "ACCEPT then operational REJECT: gate.cui at 7800 s, gate.wrap at 9600 s",
                "tight EN pair: en.E then en.I +1.3 ms at the raster frame",
            ],
            "language_to_spike_mapping": "'Foamveil is dry' = dcs.T 82 next to recon.Rn 4.00; '4.00 kOhm pit' = recon.Rn 4.00; 'this spool not the header' = gate.cui ACCEPT plus header.pct 80; 'do not bury the coupon' = gate.wrap REJECT",
            "why_high_value": "New electrochemical-noise CUI family on a black-liquor header (not Cinderwell MsS steam, not QCM-D RO fouling, not clamp-on flow). First R_n reconstruction that can hide a pit inside a dry lagging-RTD corridor. Companion t2 refuses a wrap that would hide the SoT. sim_or_real=simulated.",
            "encoder_spec": {
                "prng": "MT19937 via python random.Random",
                "seeds": {"raster": 20260972, "stream_note": "stream amplitudes are authored constants (uV, nA, kOhm, C, ratio, pct, bool)"},
                "draw_order": "raster: per neuron id order, gap-constrained times, per-spike adaptation and noise",
                "thinning": "EN exists at 2 Hz; stream keeps 4 E/I pairs; recon keeps 4 of ~40 solver ticks",
                "refractory_floors_ms": {
                    "en.E": 60000,
                    "en.I": 1.3,
                    "recon.Rn": 60000,
                    "dcs.T": 60000,
                    "skew.I": 60000,
                    "foam.ok": 60000,
                    "ops.prop": 60000,
                    "gate.cui": 60000,
                    "isol.spool": 60000,
                    "header.pct": 60000,
                    "wrap.prop": 60000,
                    "gate.wrap": 60000,
                    "coupon.live": 60000,
                    "isol.held": 60000,
                    "trip.hold": 60000,
                },
                "time_alias": "t_rel_ms; t0 = 2026-07-03T14:00:00Z campaign start",
            },
            "distillation_targets": [
                "EN reconstruction head: R_n = sigma_E / sigma_I",
                "bounded ACCEPT head: pit floor AND skew AND spool scope AND header-not-cut",
                "operational companion: refuse a wrap that would hide the only plant-owned witness",
            ],
        },
        "reconstruction_model": {
            "name": "en_noise_resistance_kohm",
            "formula": "R_n_kOhm = sigma_E_uV / sigma_I_nA",
            "parameters": {
                "pit_floor_kOhm": 5.00,
                "esd_floor_kOhm": 2.00,
                "skew_floor": 0.80,
            },
            "worked_example": {"sigma_E_uV": 48.0, "sigma_I_nA": 12.0, "R_n_kOhm": 4.00},
            "check": "48.0 / 12.0 = 4.00 exactly",
        },
        "raster": raster,
        "gate_snn": {
            "decision": "ACCEPT",
            "decision_window_ms": 28.0,
            "decision_window_s": 0.028,
            "code": "pk9.cui_isolate_gate",
            "note": "ACCEPT accumulator wins: R_n and skew evidence overpower the keep-header advocate",
            "decode_rule": "accept-isolate if rn_estimator AND current_norm AND skew fire inside the window; keep_header_advocate cannot release the whole header",
            "populations": [
                gate_pop("rn_estimator", 80, 1.5, 50.0, w_s),
                gate_pop("current_norm", 64, 1.2, 31.25, w_s),
                gate_pop("skew_margin", 40, 1.0, 50.0, w_s),
                gate_pop("keep_header_advocate", 40, 0.8, 25.0, w_s),
                gate_pop("accept_latch", 96, 1.8, 62.5, w_s),
            ],
        },
        "gate_compute": gate_compute(
            [
                {"check": "pk9.rn_scorer", "neurons": 80, "mean_rate_hz": 50.0, "window_ms": 28.0},
                {"check": "pk9.en_scorer", "neurons": 50, "mean_rate_hz": 40.0, "window_ms": 40.0},
            ]
        ),
        "meta": meta_common(
            id="nelb-r23-072",
            clock_domain="pk9-en-campaign-relative-ms-t0-2026-07-03T14:00:00Z",
            tags=["en-cui", "ACCEPT", "REJECT", "serialized-reconstruction", "operational-t2"],
        ),
    }
