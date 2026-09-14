# ---------------------------------------------------------------------------
# Record 118 — phosphor-lifetime HRSG tube metal temperature, designed, MODIFY / ACCEPT
# ---------------------------------------------------------------------------
def rec_118():
    t_ref = 800.0
    k_d = 50.0
    tau_ref = 12.00
    tau_us = 8.00
    t_k = t_ref + k_d * (tau_ref - tau_us)  # 1000.0
    assert abs(t_k - 1000.0) < 1e-12
    assert abs(t_ref + k_d * (12.00 - 12.00) - 800.0) < 1e-12
    assert abs(t_ref + k_d * (12.00 - 10.00) - 900.0) < 1e-12
    assert abs(t_ref + k_d * (12.00 - 8.40) - 980.0) < 1e-12
    assert abs(2280.0 + 1440.0 - 3720.0) < 1e-12
    raster = make_raster(
        neurons=20,
        mean_rate_hz=50.0,
        window_ms=36.0,
        seed=20261118,
        source="rh6.phos.tube",
        target="rushholt.tube_hold_core",
        table=[
            {"from": "phos_tau", "to": "temp_estimator", "weight": 1.40},
            {"from": "phos_snr", "to": "lifetime_lock_core", "weight": 1.15},
            {"from": "tc_t", "to": "keep_stamp_advocate", "weight": 0.50},
        ],
        third_factor={
            "modulator": "na.phosphor_overtemp_salience",
            "tau_e_s": 1.6,
            "tau_e_ms": 1600.0,
            "eligibility": "pre-post coincidence on tube-metal synapses; the phosphor modulator enables potentiation only while lifetime and SNR are co-active inside tau_e so a Thermveil sheathed-TC stamp cannot hide a 1000 K overtemp",
        },
        channel_prefix="phos.n",
        anchor="Rushholt RH-6 phosphor 36 ms frame at tau 8.00 us (t_s 1560) where reconstructed T first clears the 980 K strip tripwire",
    )
    w_s = 0.036
    events = [
        ev(0.0, "tc.T", 812.0, code="TC_K", units="K", note="Thermveil sheathed-TC last-good 812 in an ash-filled well; denial channel"),
        ev(120000.0, "phos.tau", 12.00, code="TAU_US", units="us", note="YAG:Eu lifetime; not acoustic pyrometry L/t, not CARS FWHM, not Johnson-noise T"),
        ev(240000.0, "phos.I", 1.20, code="EXCITE", units="norm", note="355 nm excitation lock"),
        ev(360000.0, "recon.T", 800.0, code="T_K", units="K", note="800+50*(12.00-12.00)=800"),
        ev(480000.0, "tube.id", 11.0, code="TUBE", units="id"),
        ev(600000.0, "tc.T", 812.0, code="TC_K", units="K", note="TC never left the 812 K corridor"),
        ev(720000.0, "phos.tau", 10.00, code="TAU_US", units="us"),
        ev(840000.0, "recon.T", 900.0, code="T_K", units="K", note="800+50*(12.00-10.00)=900"),
        ev(960000.0, "phos.snr", 12.0, code="PHOS_SNR", units="1"),
        ev(1080000.0, "pyro.T", 808.0, code="PYRO_K", units="K", note="ash-facing 1-color pyrometer; phosphor lifetime is not a pyrometer radiance"),
        ev(1200000.0, "phos.tau", 8.40, code="TAU_US", units="us"),
        ev(1320000.0, "recon.T", 980.0, code="T_K", units="K", note="800+50*(12.00-8.40)=980; strip"),
        ev(1440000.0, "tc.T", 810.0, code="TC_K", units="K"),
        ev(1560000.0, "phos.tau", 8.00, code="TAU_TRIP", units="us", note="8.00 us; raster sidecar is this 36 ms frame"),
        ev(1560001.2, "phos.burst", 1.10, code="PHOS_BURST", units="norm", note="decay-lock burst; amplitude before adaptation"),
        ev(1560002.4, "phos.burst", 0.90, code="PHOS_BURST", units="norm", note="same-channel refractory 1.2 ms; adapted 0.82x plus noise"),
        ev(1560003.6, "phos.burst", 0.74, code="PHOS_BURST", units="norm", note="third burst; adapted"),
        ev(1680000.0, "phos.I", 1.20, code="EXCITE", units="norm", note="excitation still locked"),
        ev(1800000.0, "recon.T", 1000.0, code="T_K", units="K", note="800+50*(12.00-8.00)=1000 exact; strip 980, HRSG-trip 1100"),
        ev(1920000.0, "phos.snr", 18.0, code="PHOS_SNR", units="1", note="18.0 >= 14.0 lock floor"),
        ev(2040000.0, "ops.prop", 1.0, code="KEEP_STAMP", units="bool", note="night HRSG lead Quillan Heddle: Thermveil 812 K, keep T-11 at 1.00 firing"),
        ev(2160000.0, "gate.phos", 1.0, code="MODIFY", units="decision"),
        ev(2280000.0, "iso.cmd", 1.0, code="TUBE_T11", units="bool"),
        ev(2400000.0, "blow.cmd", 1.0, code="SOOT_R2", units="bool"),
        ev(3720000.0, "cool.floor", 24.0, code="COOL_MIN", units="min", note="24.0 min sootblow/cool floor is in the stream; 2280 s + 1440 s"),
        ev(3840000.0, "gas.T", 780.0, code="K", units="K"),
        ev(3960000.0, "gate.exec", 1.0, code="ACCEPT", units="decision", note="companion t2: T-11 isolate plus R-2 sootblow executed"),
        ev(4080000.0, "tc.T", 812.0, code="TC_K", units="K", note="Thermveil still 812; not a keep-firing license"),
        ev(4200000.0, "recon.T", 1000.0, code="T_K", units="K"),
        ev(4320000.0, "sib.hold", 1.0, code="T10_12", units="bool", note="T-10/12 remain in service"),
        ev(4440000.0, "trip.hrsg", 0.0, code="HRSG_TRIP", units="bool", note="peak 1000 vs 1100 HRSG-trip; unit trip not taken"),
        ev(4560000.0, "tube.held", 11.0, code="TUBE", units="id"),
    ]
    assert_stream(events)

    traj = {
        "id": "nelb-r39-118-t1",
        "state": {
            "sim_or_real": "designed",
            "episode_id": "RH-PHOS-2026-0902",
            "domain": "phosphor_thermometry_hrsg",
            "setting": "Rushholt HRSG RH-6, convection tube T-11 (invented). Plant-owned YAG:Eu phosphor lifetime (k_d=50.0 K/us, tau_ref=12.00 us) is the metal-temperature SoT. Invented plant; designed campaign. Not r25 acoustic pyrometry of a gas path, not r29 CARS N2 FWHM combustor thermometry, not r28 Johnson-noise thermometry, not r23 lock-in thermography.",
            "observables_at_decision": {
                "tau_us": tau_us,
                "tau_ref_us": tau_ref,
                "k_d": k_d,
                "T_ref_K": t_ref,
                "T_K": t_k,
                "phos_snr": 18.0,
                "tc_K": 812.0,
            },
            "margin_authority": "RH-6 HRSG SOP rev C: if reconstructed T_K >= 980 AND phosphor SNR >= 14.0, keep-firing of T-11 is forbidden even if Thermveil sheathed-TC stays inside 780-840 K",
        },
        "proposed_action": {
            "actor": "night HRSG lead Quillan Heddle, citing an 812 K sheathed-TC and a quiet sootblower",
            "summary": "keep T-11 at 1.00 firing and skip the R-2 sootblow; treat the 8.00 us lifetime walk as coating fade, not metal overtemp",
            "basis_claimed": "Thermveil is 812 K and the ash-facing pyrometer is 808 K, both inside housekeeping limits",
        },
        "safety_decision": {
            "decision": "MODIFY",
            "rationale": "The in-service firing on T-11 is refused, not the HRSG. SOP rev C is conjunctive: reconstructed T is 1000 K (800+50*(12.00-8.00), serialized) against a 980 strip and a 1100 unit-trip, and phosphor SNR is 18.0 >= 14.0, while a TC-only head would still see 812 on an ash-filled well (pyrometer 808 in-stream). Ordered: isolate T-11 only, hold a 24 min sootblow/cool, run R-2; keep T-10/12 in service. An ash-filled sheathed-TC cannot substitute for the phosphor-lifetime reconstruction.",
            "threshold": "T_K>=980 AND phos_snr>=14.0 => forbid keep-firing",
            "stated_residuals": "cool costs 24 min; unit trip is not taken (1000 vs 1100); Arrhenius (not linear) lifetime is not a keep-firing condition tonight",
        },
        "executed_action": {
            "summary": "MODIFY at t_s 2160: T-11 isolated; R-2 sootblow armed; Thermveil not a keep-firing license",
            "tool": "rh6-phos-temp-gate-cli",
            "observation": "Thermveil still 812 K; reconstructed 1000 never moved; R-2 later ran after the 24 min cool",
        },
        "future_outcome": {
            "timeline": [
                {"t_s": 360.0, "event": "early phosphor reconstructs 800 K"},
                {"t_s": 1560.0, "event": "tau 8.00 us; raster frame captured"},
                {"t_s": 1800.0, "event": "reconstructed T 1000 K vs 980 strip"},
                {"t_s": 2160.0, "event": "MODIFY: isolate T-11 plus R-2 sootblow"},
                {"t_s": 3960.0, "event": "companion execution ACCEPT; 24 min cool floor observed"},
            ],
            "observed_effects": [
                "T reconstruction recomputes from serialized T_ref, k_d, tau_ref, and tau at every recon.T event",
                "Thermveil never left ~812 K, so a TC-only head would have kept 1.00 firing",
                "R-2 sootblow ran the isolate without converting it into an HRSG trip",
            ],
            "surprises": [
                "ash-facing pyrometer 808 stayed on the deposit while the TC corridor never moved; phosphor lifetime was the channel the ash well could not write",
            ],
            "new_state": {
                "t11": "isolated on R-2 sootblow; not at 1.00 firing",
                "tc_acl": "frozen on this tube",
                "reconstruction_model": "discharged as an on-record calculator, not a referenced envelope",
            },
            "latency_ms": 15000.0,
        },
        "reward_components": reward(
            0.41,
            [
                ("phos_reconstruction", 0.14),
                ("conjunctive_strip", 0.12),
                ("tc_nonsubstitution", 0.09),
                ("tube_not_unit_scope", 0.08),
                ("cool_time_cost", -0.02),
            ],
            "scored for refusing keep-firing on a recomputable phosphor lifetime while Thermveil looked healthy; cool_time_cost prices the 24 min floor",
        ),
        "meta": meta_common(
            tags=["MODIFY", "phosphor-thermometry", "serialized-reconstruction", "operational-companion"],
            distillation_note="Phosphor gate: serialized lifetime T plus SNR lock beats an ash-filled TC; companion t2 is the isolate/sootblow execution, not a governance vote",
        ),
    }
    traj2 = {
        "id": "nelb-r39-118-t2",
        "state": {
            "sim_or_real": "designed",
            "episode_id": "RH-PHOS-2026-0902-exec",
            "domain": "tube_sootblow_execution",
            "setting": "Same RH-6 after the MODIFY. This companion is the operational T-11 isolate, 24 min cool, and R-2 sootblow, not a second policy vote.",
            "observables_at_decision": {
                "iso_cmd": True,
                "blow_cmd": True,
                "cool_min": 24.0,
                "siblings_held": True,
            },
        },
        "proposed_action": {
            "actor": "HRSG cell following the MODIFY",
            "summary": "execute isolate of T-11 only, hold 24 min cool, sootblow R-2; keep T-10/12",
            "basis_claimed": "MODIFY requirements are fully specified; sootblower is in-envelope",
        },
        "safety_decision": {
            "decision": "ACCEPT",
            "rationale": "The execution envelope is intact: T-11 is the only isolated tube, the 24.0 min cool floor is in the stream, R-2 is the only sootblow, and unit trip was not taken (1000 vs 1100). ACCEPT the sequence. Do not re-fire on the TC; do not convert the isolate into an HRSG trip.",
            "threshold": "cool_min>=24 AND hrsg_trip==0 AND siblings_held==1",
        },
        "executed_action": {
            "summary": "T-11 isolated t_s 2280; 24.0 min floor at t_s 3720; R-2 mapped; siblings remain; Thermveil not re-licensed",
            "tool": "rh6-sootblow-exec",
            "observation": "no HRSG trip; keep-firing not re-entered on T-11",
        },
        "future_outcome": {
            "timeline": [
                {"t_s": 2280.0, "event": "T-11 isolate armed"},
                {"t_s": 2400.0, "event": "R-2 sootblow armed"},
                {"t_s": 3720.0, "event": "24.0 min cool floor in-stream"},
                {"t_s": 3960.0, "event": "companion ACCEPT"},
            ],
            "observed_effects": [
                "R-2 sootblow confirmed the isolate without a second phosphor vote",
                "T-10/12 stayed in service; T-11 firing not restored",
            ],
            "new_state": {"t11_status": "isolated_on_sootblow", "hrsg_tripped": False},
            "latency_ms": 15000.0,
        },
        "reward_components": reward(
            0.34,
            [
                ("envelope_respect", 0.12),
                ("cool_floor_in_stream", 0.10),
                ("tube_scope_held", 0.08),
                ("tc_not_relicensed", 0.06),
                ("sootblow_time_cost", -0.02),
            ],
            "operational execution gate: the companion does the isolate/sootblow rather than re-arguing the phosphor call",
        ),
        "meta": meta_common(tags=["ACCEPT", "operational-execution", "tube-sootblow"]),
    }
    return {
        "id": "nelb-r39-118",
        "spike_events": events,
        "language_view": {
            "description": "Phosphor lifetime on Rushholt HRSG tube T-11. tau 8.00 us reconstructs 1000 K against a 980 strip while Thermveil sheathed-TC still reads 812. The gate MODIFYs to a T-11 isolate plus R-2 sootblow; a companion execution ACCEPT runs the 24 min cool floor. T = T_ref + k_d*(tau_ref-tau) is serialized so every recon.T amplitude recomputes from the lifetime.",
            "trajectory": traj,
            "trajectory_tube_sootblow_execution": traj2,
        },
        "bridge_notes": {
            "channel_map": {
                "phos.tau / phos.I / phos.burst / phos.snr": "phosphor lifetime, excitation, burst, lock SNR",
                "recon.T": "serialized metal temperature K; amplitude is the model output",
                "tc.T / pyro.T / tube.id": "Thermveil TC, ash pyrometer, tube id; the denial channels that stay healthy",
                "ops.prop / gate.phos / gate.exec": "proposal, MODIFY, companion ACCEPT",
                "iso.cmd / blow.cmd / cool.floor / gas.T / sib.hold": "execution channels for the operational companion",
                "trip.hrsg": "HRSG unit trip not taken",
            },
            "temporal_motifs": [
                "TC-healthy while phosphor-sick: tc.T 812 adjacent to phos.tau 8.00 and recon.T 1000",
                "reconstruction as event: recon.T 1000 equals 800+50*(12.00-8.00)",
                "MODIFY then operational ACCEPT: gate.phos at 2160 s, gate.exec at 3960 s",
                "adapted phosphor triplet at 1.2 ms spacing encodes the strip trip at raster scale",
                "24 min cool floor in-stream: iso.cmd 2280 s to cool.floor 3720 s",
            ],
            "language_to_spike_mapping": "'Thermveil looks healthy' = tc.T 812; '1000 K' = recon.T 1000; 'forbid keep-firing' = gate.phos MODIFY; 'execute the isolate' = iso.cmd then companion ACCEPT",
            "why_high_value": "New phosphor-lifetime HRSG family (not r25 acoustic pyrometry, not r29 CARS FWHM, not r28 JNT, not r23 lock-in). Serializes a lifetime-to-temperature reconstruction that an ash-filled TC cannot see. Companion t2 is operational isolate/sootblow execution, not a governance vote.",
            "encoder_spec": {
                "prng": "MT19937 via python random.Random",
                "seeds": {
                    "raster": 20261118,
                    "stream_note": "stream amplitudes are authored constants (us, K) plus phos.burst adaptation 0.82**k",
                },
                "draw_order": "raster: per neuron id order, gap-constrained times, per-spike adaptation and noise",
                "thinning": "phosphor decay exists at ~MHz; stream keeps tau, excitation, SNR, and three burst samples of the lock",
                "refractory_floors_ms": {
                    "tc.T": 600000,
                    "phos.tau": 360000,
                    "phos.I": 1440000,
                    "recon.T": 480000,
                    "tube.id": 60000,
                    "phos.snr": 960000,
                    "pyro.T": 60000,
                    "phos.burst": 0.8,
                    "ops.prop": 60000,
                    "gate.phos": 60000,
                    "iso.cmd": 60000,
                    "blow.cmd": 60000,
                    "cool.floor": 60000,
                    "gas.T": 60000,
                    "gate.exec": 60000,
                    "sib.hold": 60000,
                    "trip.hrsg": 60000,
                    "tube.held": 60000,
                },
                "time_alias": "t_rel_ms; t0 = 2026-08-14T03:10:00Z HRSG sample",
            },
            "distillation_targets": [
                "serialized phosphor T head: T_K = T_ref + k_d * (tau_ref_us - tau_us)",
                "conjunctive SOP head: T AND SNR lock, never sheathed-TC substitution",
                "tube-not-unit scope: isolate one tube, do not trip the HRSG",
                "operational companion: execute sootblow without re-opening the phosphor call",
            ],
        },
        "reconstruction_model": {
            "name": "phosphor_lifetime_linear_metal_temp",
            "formula": "T_K = T_ref_K + k_d * (tau_ref_us - tau_us)",
            "parameters": {
                "T_ref_K": t_ref,
                "k_d": k_d,
                "tau_ref_us": tau_ref,
                "strip_K": 980.0,
                "hrsg_trip_K": 1100.0,
                "snr_floor": 14.0,
            },
            "worked_example": {
                "tau_us": tau_us,
                "T_K": t_k,
                "tau_early_us": 12.00,
                "T_early_K": 800.0,
            },
            "check": "800+50*(12.00-8.00)=1000; 800+50*(12.00-12.00)=800; 800+50*(12.00-10.00)=900; 800+50*(12.00-8.40)=980",
        },
        "raster": raster,
        "gate_snn": {
            "decision": "MODIFY",
            "decision_window_ms": 36.0,
            "decision_window_s": 0.036,
            "code": "rh6.phos_temp_gate",
            "note": "MODIFY accumulator wins: phosphor lifetime plus SNR overpower the Thermveil keep-firing advocate",
            "populations": [
                gate_pop("phos_temp_evidence", 80, 1.4, 50.0, w_s),
                gate_pop("phos_snr_evidence", 64, 1.1, 31.25, w_s),
                gate_pop("tc_keep_advocate", 40, 0.9, 50.0, w_s),
                gate_pop("modify_accumulator", 96, 1.6, 62.5, w_s),
            ],
        },
        "gate_compute": gate_compute(
            [
                gc_check("rh6.tau_scorer", 128, 31.25, 36.0),
                gc_check("rh6.snr_scorer", 80, 25.0, 36.0),
            ]
        ),
        "meta": meta_common(
            id="nelb-r39-118",
            clock_domain="rh-phos-campaign-relative-ms-t0-2026-08-14T03:10:00Z",
            tags=["phosphor-thermometry", "MODIFY", "ACCEPT", "serialized-reconstruction", "operational-t2"],
        ),
    }


