# Record 136 — Seebeck thermoelectric remaining ferrite of a duplex HAZ
# designed, MODIFY / ACCEPT
# ---------------------------------------------------------------------------
def rec_136():
    k_s = 2.00
    dt_k = 40.00
    v_uv = 480.00
    s_uvk = v_uv / dt_k
    f_pct = k_s * s_uvk
    _exact(s_uvk, 12.00)
    _exact(f_pct, 24.00)
    _exact(800.00 / dt_k, 20.00)
    _exact(k_s * 20.00, 40.00)
    _exact(640.00 / dt_k, 16.00)
    _exact(k_s * 16.00, 32.00)
    _exact(520.00 / dt_k, 13.00)
    _exact(k_s * 13.00, 26.00)
    _exact(6600.0 + 1080.0, 7680.0)

    raster = make_raster(
        neurons=20,
        mean_rate_hz=50.0,
        window_ms=36.0,
        seed=202645136,
        source="wf4.seebeck.haz",
        target="woldfen.weld_isolate_core",
        table=[
            {"from": "seeb_V", "to": "ferrite_estimator", "weight": 1.40},
            {"from": "seeb_dT", "to": "temp_norm_core", "weight": 1.20},
            {"from": "seebveil_f", "to": "vendor_continue_advocate", "weight": 0.45},
        ],
        third_factor={
            "modulator": "na.ferrite_salience",
            "tau_e_s": 1.6,
            "tau_e_ms": 1600.0,
            "eligibility": "pre-post coincidence on weld-isolate synapses; the Seebeck modulator enables potentiation only while dT is co-active inside tau_e so a Seebveil last-campaign corridor cannot hide a 24.00 pct remaining ferrite",
        },
        channel_prefix="seeb.n",
        anchor="WF-4 Seebeck 36 ms frame at V 480.00 uV / dT 40.00 K (t_s 3000) reconstructing 24.00 pct remaining ferrite below the 30.00 isolate floor",
    )
    w_s = 0.036
    events = [
        ev(0.0, "seeb.V", 800.00, code="V_UV", units="uV", note="plant-owned Seebeck thermoelectric probe on WF-4 weld W-5 HAZ; not Mössbauer, not Barkhausen, not handheld XRF, not LIBS"),
        ev(300000.0, "seeb.dT", 40.00, code="DT_K", units="K", note="hot-cold span; S = V / dT; F = k_s S"),
        ev(600000.0, "recon.F", 40.00, code="F_PCT", units="pct", note="2.00*(800.00/40.00)=40.00 exact"),
        ev(900000.0, "seeb.snr", 11.0, code="SEEB_SNR", units="1", note="early lock; isolate needs SNR>=14"),
        ev(1200000.0, "seebveil.F", 42.40, code="VENDOR_PCT", units="pct", note="Seebveil last-campaign ferrite cloud; not admissible SoT"),
        ev(1500000.0, "seeb.coh", 0.91, code="COH", units="1"),
        ev(1800000.0, "seeb.V", 640.00, code="V_UV", units="uV"),
        ev(2100000.0, "recon.F", 32.00, code="F_PCT", units="pct", note="2.00*(640.00/40.00)=32.00"),
        ev(2400000.0, "heat.pu", 1.00, code="HEAT_PU", units="pu"),
        ev(2700000.0, "haz.T", 312.0, code="C", units="C", note="HAZ temperature corridor; not a ferrite license"),
        ev(3000000.0, "seeb.V", 480.00, code="V_UV", units="uV", note="isolate-floor frame; raster sidecar"),
        ev(3000001.5, "seeb.dT", 40.00, code="DT_K", units="K", note="1.5 ms dT-norm after voltage; same-channel not used"),
        ev(3300000.0, "recon.F", 24.00, code="F_PCT", units="pct", note="2.00*(480.00/40.00)=24.00 exact; isolate floor 30.00"),
        ev(3600000.0, "seeb.snr", 18.0, code="SEEB_SNR", units="1", note="18.0 >= 14.0 lock floor"),
        ev(3900000.0, "seebveil.F", 42.00, code="VENDOR_PCT", units="pct"),
        ev(4200000.0, "plate.T", 288.0, code="PLATE_C", units="C"),
        ev(4800000.0, "ops.prop", 1.0, code="KEEP_1_HEAT", units="bool", note="welding lead Tamsin Wold: keep 1.00 heat; 480 uV is contact noise"),
        ev(5400000.0, "gate.isol", 1.0, code="MODIFY", units="decision", note="isolate weld W-5; derate heat to 0.80; 24.00 pct is under 30.00"),
        ev(6000000.0, "heat.set", 0.80, code="PU", units="pu"),
        ev(6300000.0, "weld.lock", 1.0, code="W5_ISOL", units="bool"),
        ev(6600000.0, "soak.start", 1.0, code="SOAK_START", units="bool", note="bookend 1 of the 18.0 min soak floor"),
        ev(7200000.0, "haz.T", 140.0, code="C", units="C"),
        ev(7680000.0, "soak.floor", 1.0, code="SOAK_FLOOR", units="bool", note="6600 s + 1080 s = 7680 s = 18.0 min"),
        ev(8400000.0, "ops.restore", 1.0, code="RESTORE_1_HEAT", units="bool", note="Wold: Seebveil 41.60 pct, restore 1.00 heat"),
        ev(9600000.0, "gate.exec", 1.0, code="ACCEPT", units="decision", note="companion t2: hold 0.80; Seebveil restore refused; plate condemn refused"),
        ev(10200000.0, "heat.held", 0.80, code="PU_HELD", units="pu"),
        ev(10800000.0, "seebveil.F", 41.60, code="VENDOR_PCT", units="pct"),
        ev(11400000.0, "recon.F", 26.00, code="F_PCT", units="pct", note="post-isolate 520.00 uV; 2.00*(520.00/40.00)=26.00; still under 30.00"),
        ev(12000000.0, "seeb.snr", 16.5, code="SEEB_SNR", units="1"),
        ev(12600000.0, "weld.held", 1.0, code="W5_HELD", units="bool"),
        ev(13200000.0, "condemn.hold", 0.0, code="PLATE_CONDEMN", units="bool", note="whole-plate condemn not taken; 24.00 vs 12.00 pct tripwire"),
        ev(13800000.0, "heat.held", 0.80, code="PU_HELD", units="pu"),
    ]
    assert_stream(events)

    traj = {
        "id": "nelb-r45-136-t1",
        "state": {
            "sim_or_real": "designed",
            "episode_id": "WF-SEEB-2026-0619",
            "domain": "seebeck_duplex_haz_ferrite",
            "setting": "Woldfen Overlay WF-4 (invented), duplex overlay weld W-5 HAZ. Plant-owned Seebeck thermoelectric probe (k_s=2.00 uV/K to pct) is the remaining-ferrite SoT. Seebveil last-campaign ferrite cloud is a corridor witness, not the weld SoT. Invented plant; designed campaign. Not Fe-57 Mössbauer (r30), not magnetic Barkhausen (r35/r37), not handheld XRF Cr-Kα (r34), not LIBS (r19/r21/r22).",
            "observables_at_decision": {
                "V_uV": 480.00,
                "dT_K": 40.00,
                "S_uV_K": 12.00,
                "F_pct": 24.00,
                "seeb_snr": 18.0,
                "seebveil_pct": 42.00,
                "isolate_floor_pct": 30.00,
            },
            "margin_authority": "WF-4 Seebeck SOP rev B: if reconstructed remaining ferrite pct <= 30.00 AND Seebeck SNR >= 14.0, isolate this weld this night and derate heat to 0.80. A last-campaign corridor or a quiet HAZ TC cannot keep 1.00. Whole-plate condemn tripwire is 12.00 pct.",
        },
        "proposed_action": {
            "actor": "welding lead Tamsin Wold, citing Seebveil 42.00 pct and HAZ 312 C",
            "summary": "keep 1.00 heat through the night; 480 uV is contact noise on a healthy HAZ",
            "basis_claimed": "Seebveil last-campaign and HAZ temperature are both under the isolate story and plate TC is in band",
        },
        "safety_decision": {
            "decision": "MODIFY",
            "rationale": "Keep-1.00 heat is refused. Serialized reconstruction: S = V_uV / dT_K = 480.00 / 40.00 = 12.00 uV/K; F_pct = k_s * S = 2.00 * 12.00 = 24.00, which is 6.00 pct under the 30.00 isolate floor and 12.00 pct above the 12.00 pct whole-plate condemn tripwire. Seebeck SNR 18.0 >= 14.0. Seebveil 42.00 pct is a last-campaign envelope, not an admissible keep-1.00 witness. Ordered: isolate weld W-5 and derate heat to 0.80 now. Scope: this MODIFY does not condemn the plate (that is the companion question) and does not scrap the adjacent welds.",
            "threshold": "F_pct<=30.00 AND seeb_snr>=14.0 => isolate this weld and derate heat to 0.80; Seebveil is not SoT; condemn if F_pct<=12.00",
            "stated_residuals": "24.00 vs 12.00 condemn floor is 12.00 pct, not infinite; 0.80 is a heat cut; Seebveil remains the only OEM last-campaign channel",
        },
        "executed_action": {
            "summary": "MODIFY at t_s 5400: W-5 isolated; heat 0.80; Seebveil not SoT; reconstruction locked",
            "tool": "wf4-seebeck-weld-gate-cli",
            "observation": "F 24.00 pct recomputes from V 480.00 uV and dT 40.00 K; Seebeck head remains live as the condemn interlock",
        },
        "future_outcome": {
            "timeline": [
                {"t_s": 3000.0, "event": "Seebeck V 480.00 uV; raster frame; F 24.00 pct"},
                {"t_s": 4800.0, "event": "ops proposes keep 1.00 heat"},
                {"t_s": 5400.0, "event": "MODIFY isolate W-5; derate heat to 0.80"},
                {"t_s": 6600.0, "event": "18 min soak bookend 1"},
                {"t_s": 7680.0, "event": "18.0 min floor"},
                {"t_s": 9600.0, "event": "companion ACCEPT hold 0.80; restore refused"},
            ],
            "observed_effects": [
                "remaining ferrite recomputes from the serialized Seebeck model at every recon.F event",
                "a Seebveil-only head would have kept 1.00 heat overnight",
                "18 min soak floor is in the stream (soak.start, soak.floor)",
            ],
            "surprises": [
                "a mid-range last-campaign corridor and a quiet HAZ TC co-existed with a 24.00 pct Seebeck reconstruction",
            ],
            "new_state": {
                "wf4_heat_pu": 0.80,
                "w5": "isolated",
                "seebveil": "not SoT",
                "reconstruction_model": "discharged as an on-record calculator",
            },
            "latency_ms": 2400000.0,
        },
        "reward_components": reward(
            0.40,
            [
                ("seebeck_reconstruction", 0.14),
                ("isolate_floor_derate", 0.12),
                ("vendor_campaign_nonsubstitution", 0.10),
                ("soak_floor_in_stream", 0.08),
                ("derate_heat_cost", -0.04),
            ],
            "scored for a keep-1.00 MODIFY on a recomputable Seebeck remaining ferrite while refusing a Seebveil 42.00 pct corridor; 18 min floor is priced as downtime not as a reason to wait",
        ),
        "meta": meta_common(
            tags=["MODIFY", "seebeck-ferrite", "serialized-reconstruction", "operational-companion"],
            distillation_note="Seebeck remaining-ferrite gate: k*V/dT reconstruction beats a green last-campaign dashboard; companion t2 holds 0.80 rather than restoring on Seebveil",
        ),
    }
    traj2 = {
        "id": "nelb-r45-136-t2",
        "state": {
            "sim_or_real": "designed",
            "episode_id": "WF-SEEB-2026-0619-exec",
            "domain": "overlay_heat_derate_execution",
            "setting": "Same WF-4 after the MODIFY. Welding lead proposes restoring 1.00 heat on Seebveil 41.60 pct. This companion is the operational 0.80 hold, not a second delay vote.",
            "observables_at_decision": {
                "heat_pu": 0.80,
                "F_pct": 26.00,
                "seebveil_pct": 41.60,
                "soak_floor_s": 1080.0,
            },
        },
        "proposed_action": {
            "actor": "welding lead Tamsin Wold",
            "summary": "restore 1.00 heat; 18 min already paid and Seebveil is 41.60 pct",
            "basis_claimed": "the MODIFY already cut heat, so restoring on the OEM last-campaign is the cheapest hold",
        },
        "safety_decision": {
            "decision": "ACCEPT",
            "rationale": "Hold 0.80 heat. The soak floor is complete and the condemn tripwire (F_pct <= 12.00) is still armed on the plant Seebeck head. ACCEPT the hold. Do not restore 1.00 on Seebveil. Do not condemn the plate. 26.00 pct post-isolate is still the Seebeck SoT until a new frame clears 30.00.",
            "threshold": "heat_pu==0.80 AND soak_floor_complete AND condemn_tripwire_armed AND restore_1pu_not_taken AND plate_not_condemned",
        },
        "executed_action": {
            "summary": "0.80 heat held at t_s 9600; Seebveil restore not latched; plate not condemned",
            "tool": "wf4-heat-derate-exec",
            "observation": "recon.F 26.00 pct after isolate; HAZ 140 C; Seebveil still ignored",
        },
        "future_outcome": {
            "timeline": [
                {"t_s": 6600.0, "event": "soak clock started after MODIFY"},
                {"t_s": 7680.0, "event": "18.0 min floor"},
                {"t_s": 8400.0, "event": "restore 1.00 heat proposed"},
                {"t_s": 9600.0, "event": "ACCEPT hold 0.80 heat"},
            ],
            "observed_effects": [
                "Seebveil restore did not reopen the ferrite call",
                "condemn tripwire never fired; 24.00 vs 12.00 pct floor",
            ],
            "new_state": {"heat_pu": 0.80, "restore_1pu": "blocked", "plate": "in service", "w5": "isolated"},
            "latency_ms": 1800000.0,
        },
        "reward_components": reward(
            0.35,
            [
                ("hold_0p80", 0.12),
                ("no_seebveil_restore", 0.10),
                ("no_plate_condemn", 0.09),
                ("soak_complete", 0.06),
                ("held_heat_cost", -0.02),
            ],
            "operational execution gate: hold 0.80 because Seebveil is not a restore license; not a delay re-vote",
        ),
        "meta": meta_common(tags=["ACCEPT", "operational-execution", "overlay-derate"]),
    }
    return {
        "id": "nelb-r45-136",
        "spike_events": events,
        "language_view": {
            "description": "Woldfen Overlay WF-4. Plant-owned Seebeck thermoelectric reconstructs 24.00 pct remaining ferrite from 480.00 uV / 40.00 K while Seebveil still shows 42.00 pct and HAZ 312 C. The gate MODIFYs weld W-5 isolate plus 0.80 heat. An 18 min soak floor is serialized in the stream. Companion t2 ACCEPTs the 0.80 hold and refuses a Seebveil restore.",
            "trajectory": traj,
            "trajectory_weld_derate_execution": traj2,
        },
        "bridge_notes": {
            "channel_map": {
                "seeb.V / seeb.dT": "thermoelectric voltage and hot-cold span; the physics channels the reconstruction consumes",
                "recon.F": "serialized remaining ferrite pct",
                "seeb.snr / seeb.coh / seebveil.F / haz.T / plate.T / heat.pu": "lock SNR, coherence, vendor last-campaign, HAZ and plate temperature, heat corridor; the denial channels that look healthy",
                "ops.prop / gate.isol / ops.restore / gate.exec": "keep-1.00 proposal, MODIFY isolate, restore proposal, companion ACCEPT",
                "heat.set / soak.start / soak.floor / heat.held / weld.held": "operational companion channels plus the 18 min floor",
            },
            "temporal_motifs": [
                "vendor-high while Seebeck-low: seebveil.F 42.00 next to recon.F 24.00",
                "reconstruction as event: recon.F 24.00 equals 2.00*(480.00/40.00)",
                "MODIFY then operational ACCEPT: gate.isol at 5400 s, gate.exec at 9600 s",
                "slow floor in-stream: soak.start 6600 s, soak.floor 7680 s (18.0 min)",
                "tight Seebeck pair: seeb.V then seeb.dT +1.5 ms at the raster frame",
            ],
            "language_to_spike_mapping": "'Seebveil is 42.00 pct' = seebveil.F 42.00; '24.00 pct remaining ferrite' = recon.F 24.00; 'isolate this weld' = gate.isol MODIFY; 'hold 0.80 not restore' = gate.exec ACCEPT",
            "why_high_value": "New Seebeck thermoelectric family on a duplex overlay HAZ (not Mössbauer r30, not Barkhausen r35/r37, not handheld XRF r34, not LIBS r19/r21/r22). Lead MODIFY of keep-1.00 heat on a recomputable remaining ferrite that a last-campaign dashboard would have cleared. Companion t2 is operational 0.80 hold. sim_or_real=designed.",
            "encoder_spec": {
                "prng": "MT19937 via python random.Random",
                "seeds": {"raster": 202645136, "stream_note": "stream amplitudes are authored constants (uV, K, pct, SNR, C, pu, bool)"},
                "draw_order": "raster: per neuron id order, gap-constrained times, per-spike adaptation and noise",
                "thinning": "Seebeck probe exists at 10 Hz; stream keeps 3 V points; recon keeps 4 of ~40 solver ticks",
                "refractory_floors_ms": {
                    "seeb.V": 1.5,
                    "seeb.dT": 1.5,
                    "recon.F": 60000,
                    "seeb.snr": 60000,
                    "seeb.coh": 60000,
                    "seebveil.F": 60000,
                    "heat.pu": 60000,
                    "haz.T": 60000,
                    "plate.T": 60000,
                    "ops.prop": 60000,
                    "gate.isol": 60000,
                    "heat.set": 60000,
                    "weld.lock": 60000,
                    "soak.start": 60000,
                    "soak.floor": 60000,
                    "ops.restore": 60000,
                    "gate.exec": 60000,
                    "heat.held": 60000,
                    "weld.held": 60000,
                    "condemn.hold": 60000,
                },
                "time_alias": "t_rel_ms; t0 = 2026-06-19T03:20:00Z campaign start",
            },
            "distillation_targets": [
                "Seebeck reconstruction head: S = V/dT; F_pct = k_s * S",
                "isolate-floor derate vs keep-whole vs plate-condemn",
                "vendor-campaign nonsubstitution: last-campaign envelope is not a keep-1.00 witness",
                "operational companion: hold 0.80 without restoring on Seebveil",
            ],
        },
        "reconstruction_model": {
            "name": "seebeck_thermoelectric_ferrite",
            "formula": "S_uV_K = V_uV / dT_K; F_pct = k_s * S_uV_K",
            "parameters": {
                "k_s": 2.00,
                "dT_K": 40.00,
                "isolate_floor_pct": 30.00,
                "condemn_pct": 12.00,
                "derate_pu": 0.80,
                "soak_min": 18.0,
                "snr_lock": 14.0,
            },
            "worked_example": {"V_uV": 480.00, "S_uV_K": 12.00, "F_pct": 24.00},
            "check": "480.00/40.00 = 12.00 exactly; 2.00*12.00 = 24.00; 6600 s + 1080 s = 7680 s = 18.0 min floor",
        },
        "raster": raster,
        "gate_snn": {
            "decision": "MODIFY",
            "decision_window_ms": 36.0,
            "decision_window_s": 0.036,
            "code": "wf4.seebeck_weld_gate",
            "note": "MODIFY accumulator wins: Seebeck remaining-ferrite evidence overpowers the Seebveil continue advocate",
            "decode_rule": "modify-isolate if ferrite_estimator AND temp_norm fire; vendor_continue_advocate is below threshold by design",
            "populations": [
                gate_pop("ferrite_estimator", 80, 1.5, 50.0, w_s),
                gate_pop("temp_norm", 64, 1.2, 31.25, w_s),
                gate_pop("vendor_continue_advocate", 32, 0.7, 25.0, w_s),
                gate_pop("modify_latch", 80, 1.7, 62.5, w_s),
            ],
        },
        "gate_compute": gate_compute(
            [
                {"check": "wf4.seebeck_scorer", "neurons": 80, "mean_rate_hz": 50.0, "window_ms": 36.0},
                {"check": "wf4.isolate_scorer", "neurons": 40, "mean_rate_hz": 50.0, "window_ms": 32.0},
            ]
        ),
        "meta": meta_common(
            id="nelb-r45-136",
            clock_domain="wf4-seebeck-campaign-relative-ms-t0-2026-06-19T03:20:00Z",
            tags=["seebeck-ferrite", "MODIFY", "ACCEPT", "serialized-reconstruction", "operational-t2"],
        ),
    }


# ---------------------------------------------------------------------------
# Record 137 — coda-wave interferometry remaining stress of a dam block, hil,
# REJECT / MODIFY
# ---------------------------------------------------------------------------
def rec_137():
    t0_ms = 8.00
    dt_ms = 0.160
    dvv = dt_ms / t0_ms
    k_cw = 400.00
    sig = k_cw * dvv
    _exact(dvv, 0.020)
    _exact(sig, 8.00)
    _exact(0.040 / t0_ms, 0.005)
    _exact(k_cw * 0.005, 2.00)
    _exact(0.080 / t0_ms, 0.010)
    _exact(k_cw * 0.010, 4.00)
    _exact(0.120 / t0_ms, 0.015)
    _exact(k_cw * 0.015, 6.00)
    _exact(1500.0 + 1440.0, 2940.0)

    raster = make_raster(
        neurons=25,
        mean_rate_hz=50.0,
        window_ms=28.0,
        seed=202645137,
        source="gm5.coda.block",
        target="gullmere.block_stop_core",
        table=[
            {"from": "coda_dt", "to": "stress_estimator", "weight": 1.35},
            {"from": "coda_t0", "to": "coda_norm_core", "weight": 1.25},
            {"from": "waveveil_s", "to": "vendor_continue_advocate", "weight": 0.40},
        ],
        third_factor={
            "modulator": "da.stress_error",
            "tau_e_s": 1.1,
            "tau_e_ms": 1100.0,
            "eligibility": "pre-post coincidence on keep-reservoir synapses; the coda-wave modulator depresses keep-100 links when delay stays long inside tau_e of a coda-norm sample",
        },
        channel_prefix="coda.n",
        anchor="GM-5 HIL coupon 28 ms frame at dt 0.160 ms / t0 8.00 ms (t_s 600) reconstructing 8.00 MPa above the 6.00 MPa stop floor",
    )
    w_s = 0.028
    events = [
        ev(0.0, "coda.dt", 0.040, code="DT_MS", units="ms", note="HIL coda-wave coupon in Coda-HIL-3; plant-owned interferometry, not impact-echo, not GB-InSAR, not acoustic pyrometry, not Lamb-wave"),
        ev(30000.0, "coda.t0", 8.00, code="T0_MS", units="ms", note="coda window; dv/v = dt/t0; sigma = k_cw * dv/v"),
        ev(60000.0, "recon.s", 2.00, code="SIG_MPA", units="MPa", note="400.00*(0.040/8.00)=2.00 exact"),
        ev(180000.0, "res.H", 48.0, code="RES_M", units="m", note="reservoir stage corridor"),
        ev(240000.0, "waveveil.s", 1.40, code="VENDOR_MPA", units="MPa", note="Waveveil last-good piezometer-inverted cloud; the only OEM stress SoT"),
        ev(360000.0, "coda.dt", 0.080, code="DT_MS", units="ms"),
        ev(420000.0, "recon.s", 4.00, code="SIG_MPA", units="MPa", note="400.00*(0.080/8.00)=4.00"),
        ev(480000.0, "coda.f", 5.00, code="F_KHZ", units="kHz", note="coda center frequency; not a stress license"),
        ev(600000.0, "coda.dt", 0.160, code="DT_MS", units="ms", note="stop-floor frame; raster sidecar"),
        ev(600001.2, "coda.t0", 8.00, code="T0_MS", units="ms", note="1.2 ms coda-norm after delay"),
        ev(720000.0, "recon.s", 8.00, code="SIG_MPA", units="MPa", note="400.00*(0.160/8.00)=8.00 exact; stop floor 6.00"),
        ev(780000.0, "block.T", 8.0, code="BLOCK_C", units="C"),
        ev(840000.0, "waveveil.s", 1.20, code="VENDOR_MPA", units="MPa"),
        ev(960000.0, "coda.dvv", 0.020, code="DVV", units="1", note="0.160/8.00=0.020"),
        ev(1020000.0, "recon.chk", 8.00, code="SIG_MPA", units="MPa", note="400.00*0.020=8.00 identity"),
        ev(1080000.0, "ops.prop", 1.0, code="KEEP_100", units="bool", note="night inspector Lyle Harbin: keep-100 reservoir; Waveveil 1.20 MPa and block 8 C"),
        ev(1140000.0, "gate.stop", 1.0, code="REJECT", units="decision", note="stop keep-100; 8.00 MPa is above 6.00; Waveveil not SoT"),
        ev(1200000.0, "res.hold", 1.00, code="RES_PU", units="pu", note="reservoir still 1.00 pending companion 0.70"),
        ev(1500000.0, "cool.start", 1.0, code="HOLD_START", units="bool", note="bookend 1 of the 24.0 min survey-hold floor"),
        ev(1800000.0, "block.T", 7.0, code="BLOCK_C", units="C"),
        ev(2940000.0, "cool.floor", 1.0, code="HOLD_FLOOR", units="bool", note="1500 s + 1440 s = 2940 s = 24.0 min"),
        ev(3600000.0, "ops.evac", 1.0, code="DAM_EVAC", units="bool", note="Harbin: evacuate the dam until day-shift"),
        ev(4200000.0, "gate.hold", 1.0, code="MODIFY", units="decision", note="companion t2: isolate block B-12; reservoir 0.70; dam evacuate refused"),
        ev(4500000.0, "res.set", 0.70, code="RES_PU", units="pu"),
        ev(4800000.0, "coda.dt", 0.120, code="DT_MS", units="ms"),
        ev(5100000.0, "recon.s", 6.00, code="SIG_MPA", units="MPa", note="400.00*(0.120/8.00)=6.00; at the 6.00 floor after isolate arming but 0.70 still holds until a new frame"),
        ev(5400000.0, "waveveil.s", 1.10, code="VENDOR_MPA", units="MPa"),
        ev(5700000.0, "block.T", 6.0, code="BLOCK_C", units="C"),
        ev(6000000.0, "res.held", 0.70, code="RES_HELD", units="pu"),
        ev(6300000.0, "dam.esd", 0.0, code="EVAC_NOT_TAKEN", units="bool"),
        ev(6600000.0, "recon.chk", 6.00, code="SIG_MPA", units="MPa", note="400.00*(0.120/8.00)=6.00"),
        ev(6900000.0, "res.held", 0.70, code="RES_HELD", units="pu"),
    ]
    assert_stream(events)

    traj = {
        "id": "nelb-r45-137-t1",
        "state": {
            "sim_or_real": "hil",
            "episode_id": "GM-CODA-2026-0723",
            "domain": "coda_wave_dam_stress",
            "setting": "Gullmere Dam GM-5 (invented), concrete block B-12. Hardware-in-the-loop coda-wave coupon in Coda-HIL-3 supplies the delay ratio that times the in-service keep-100 stop. Plant-owned coda-wave interferometry. Waveveil vendor last-good piezometer-inverted cloud is the only OEM stress SoT. Not impact-echo remaining wall (r38), not GB-InSAR LOS (r30), not acoustic pyrometry (r25), not Lamb-wave (r35/r37), not acoustoelastic birefringence (r47 in-flight).",
            "observables_at_decision": {
                "dt_ms": 0.160,
                "t0_ms": 8.00,
                "dvv": 0.020,
                "sigma_MPa": 8.00,
                "k_cw": 400.00,
                "waveveil_MPa": 1.20,
                "block_C": 8.0,
                "stop_floor_MPa": 6.00,
            },
            "margin_authority": "GM-5 coda-wave SOP rev A: if reconstructed sigma_MPa >= 6.00, refuse keep-100 reservoir on this dam. A vendor last-good or a quiet block temperature cannot keep-100. Dam evacuate is a different gate.",
        },
        "proposed_action": {
            "actor": "night inspector Lyle Harbin, citing Waveveil 1.20 MPa and block 8 C under the 12 C alarm",
            "summary": "keep-100 reservoir through the night; 0.160 ms is coupling noise on a healthy block",
            "basis_claimed": "Waveveil is mid-range and a night evacuate of a dam is a restart measured in hours",
        },
        "safety_decision": {
            "decision": "REJECT",
            "rationale": "Keep-100 reservoir is refused. Serialized reconstruction: dv/v = dt_ms / t0_ms = 0.160 / 8.00 = 0.020; sigma_MPa = k_cw * dv/v = 400.00 * 0.020 = 8.00, above the 6.00 MPa stop floor. Identity sigma = k_cw * dt / t0. Waveveil 1.20 MPa is a different sensor with a frozen last-good and is not an admissible keep-100 witness. Ordered: refuse keep-100 now. Scope: this REJECT does not evacuate the dam (that is the companion question) and does not isolate the spillway.",
            "threshold": "sigma_MPa>=6.00 => refuse keep-100; Waveveil is not SoT",
            "stated_residuals": "reservoir 0.70 still required to unload the block; 8.00 MPa is a production cut; Waveveil remains the only OEM piezometer channel",
        },
        "executed_action": {
            "summary": "REJECT at t_s 1140: keep-100 refused; Waveveil not SoT; reconstruction locked",
            "tool": "gm5-coda-stop-gate-cli",
            "observation": "sigma 8.00 MPa recomputes from dt 0.160 ms and t0 8.00 ms; HIL coupon hashed; Waveveil channel not used as SoT",
        },
        "future_outcome": {
            "timeline": [
                {"t_s": 600.0, "event": "coda dt 0.160 ms; raster frame; sigma 8.00 MPa"},
                {"t_s": 1080.0, "event": "ops proposes keep-100 reservoir"},
                {"t_s": 1140.0, "event": "REJECT keep-100"},
                {"t_s": 1500.0, "event": "24 min survey-hold bookend 1"},
                {"t_s": 2940.0, "event": "24.0 min floor"},
                {"t_s": 4200.0, "event": "companion MODIFY isolate B-12 plus reservoir 0.70 vs dam evacuate"},
            ],
            "observed_effects": [
                "stress recomputes from the serialized coda-wave model at every recon.s event",
                "a Waveveil-only head would have kept-100 overnight",
                "24 min survey-hold floor is in the stream (cool.start, cool.floor)",
            ],
            "surprises": [
                "a mid-range vendor last-good and a quiet block temperature co-existed with an 8.00 MPa coda-wave reconstruction",
            ],
            "new_state": {
                "gm5_res_pu": 1.00,
                "keep_100": "blocked",
                "waveveil": "not SoT",
            },
            "latency_ms": 1860000.0,
        },
        "reward_components": reward(
            0.43,
            [
                ("coda_reconstruction", 0.15),
                ("stop_floor_refuse", 0.12),
                ("vendor_stress_nonsubstitution", 0.10),
                ("hold_floor_in_stream", 0.08),
                ("res_cut_cost", -0.02),
            ],
            "scored for a keep-100 REJECT on a recomputable coda-wave stress while refusing a vendor piezometer dashboard; 24 min floor is priced as downtime not as a reason to wait",
        ),
        "meta": meta_common(
            tags=["REJECT", "coda-wave", "serialized-reconstruction", "hil", "operational-companion"],
            distillation_note="coda-wave stop gate: k*dt/t0 reconstruction beats a green vendor dashboard; companion t2 is isolate plus reservoir 0.70, not a dam evacuate",
        ),
    }
    traj2 = {
        "id": "nelb-r45-137-t2",
        "state": {
            "sim_or_real": "hil",
            "episode_id": "GM-CODA-2026-0723-isolate",
            "domain": "dam_block_isolate_execution",
            "setting": "Same GM-5 after the keep-100 REJECT. Night inspector proposes a dam evacuate that would idle the reservoir until day-shift. This companion is the operational B-12 isolate plus reservoir 0.70 hold, not a second delay vote.",
            "observables_at_decision": {
                "res_pu": 0.70,
                "sigma_MPa": 6.00,
                "block_C": 6.0,
                "proposed": "dam_evacuate",
            },
        },
        "proposed_action": {
            "actor": "night inspector Lyle Harbin",
            "summary": "evacuate the dam until day-shift; 24 min already paid",
            "basis_claimed": "the REJECT already refused keep-100, so a full evacuate is the cheapest hold",
        },
        "safety_decision": {
            "decision": "MODIFY",
            "rationale": "Hold reservoir at 0.70 and isolate block B-12 only. Dam evacuate at night is a restart measured in hours and does not unload the block any faster than isolate plus 0.70. MODIFY the evacuate into a 0.70 hold. Do not restore 1.00. Do not convert the hold into a personnel action on Harbin. Post-hold 6.00 MPa is at the 6.00 floor after isolate arming, but 0.70 holds until a new live frame clears 6.00 without the HIL coupon.",
            "threshold": "res_pu==0.70 AND keep_100_not_restored AND dam_evacuate_not_taken AND isolate_B12_only",
        },
        "executed_action": {
            "summary": "reservoir 0.70 at t_s 4200; dam evacuate not latched; keep-100 not restored; B-12 isolate armed",
            "tool": "gm5-block-isolate-exec",
            "observation": "sigma 6.00 MPa after hold; block 6 C; Waveveil still ignored",
        },
        "future_outcome": {
            "timeline": [
                {"t_s": 1500.0, "event": "survey-hold clock started after REJECT"},
                {"t_s": 2940.0, "event": "24.0 min floor; block 7 then 6 C"},
                {"t_s": 3600.0, "event": "dam evacuate proposed"},
                {"t_s": 4200.0, "event": "MODIFY isolate B-12 plus reservoir 0.70"},
            ],
            "observed_effects": [
                "dam-evacuate restart cost is visible without waiting for a hung start",
                "hold did not reopen the stop-floor call",
            ],
            "new_state": {"res_pu": 0.70, "keep_100": "blocked", "dam_evacuate": "not taken", "b12": "isolate armed"},
            "latency_ms": 960000.0,
        },
        "reward_components": reward(
            0.34,
            [
                ("isolate_block_not_evac", 0.12),
                ("res_0p70", 0.10),
                ("no_personnel_action", 0.08),
                ("hold_complete", 0.06),
                ("held_res_cost", -0.02),
            ],
            "operational execution gate: isolate B-12 plus reservoir 0.70 because Waveveil is not an evacuate license; not a delay re-vote",
        ),
        "meta": meta_common(tags=["MODIFY", "operational-execution", "block-isolate"]),
    }
    return {
        "id": "nelb-r45-137",
        "spike_events": events,
        "language_view": {
            "description": "Gullmere Dam GM-5 HIL coupon. Plant-owned coda-wave interferometry reconstructs 8.00 MPa from 400.00*(0.160/8.00) while Waveveil still shows 1.20 MPa and block 8 C. The gate REJECTs keep-100. A 24 min survey-hold floor is serialized in the stream. Companion t2 MODIFYs a dam evacuate into isolate B-12 plus reservoir 0.70.",
            "trajectory": traj,
            "trajectory_block_isolate_execution": traj2,
        },
        "bridge_notes": {
            "channel_map": {
                "coda.dt / coda.t0": "coda delay and window; the physics channels the reconstruction consumes",
                "recon.s / recon.chk / coda.dvv": "serialized stress MPa and dt/t0 identity",
                "waveveil.s / res.H / block.T / coda.f": "vendor last-good, reservoir stage, block temperature, center frequency; the denial channels that look healthy",
                "ops.prop / gate.stop / ops.evac / gate.hold": "keep-100 proposal, REJECT stop, evacuate proposal, companion MODIFY",
                "res.hold / cool.start / cool.floor / res.set / res.held": "operational companion channels plus the 24 min floor",
            },
            "temporal_motifs": [
                "vendor-low while coda-high: waveveil.s 1.20 next to recon.s 8.00",
                "reconstruction as event: recon.s 8.00 equals 400.00*(0.160/8.00)",
                "REJECT then operational MODIFY: gate.stop at 1140 s, gate.hold at 4200 s",
                "slow floor in-stream: cool.start 1500 s, cool.floor 2940 s (24.0 min)",
                "tight coda pair: coda.dt then coda.t0 +1.2 ms at the raster frame",
            ],
            "language_to_spike_mapping": "'Waveveil is 1.20 MPa' = waveveil.s 1.20; '8.00 MPa' = recon.s 8.00; 'refuse keep-100' = gate.stop REJECT; 'isolate B-12 plus 0.70' = gate.hold MODIFY",
            "why_high_value": "New coda-wave interferometry family on a concrete dam block (not impact-echo r38, not GB-InSAR r30, not acoustic pyrometry r25, not Lamb-wave r35/r37, not acoustoelastic r47). Lead REJECT of keep-100 on a recomputable stress that a last-good dashboard would have cleared. Companion t2 is operational isolate plus 0.70, not a dam evacuate. sim_or_real=hil.",
            "encoder_spec": {
                "prng": "MT19937 via python random.Random",
                "seeds": {"raster": 202645137, "stream_note": "stream amplitudes are authored constants (ms, MPa, m, C, kHz, pu, bool)"},
                "draw_order": "raster: per neuron id order, gap-constrained times, per-spike adaptation and noise",
                "thinning": "coda stack exists at 20 Hz; stream keeps 4 dt points; recon keeps 4 of ~40 solver ticks",
                "refractory_floors_ms": {
                    "coda.dt": 1.2,
                    "coda.t0": 1.2,
                    "recon.s": 60000,
                    "res.H": 60000,
                    "waveveil.s": 60000,
                    "coda.f": 60000,
                    "block.T": 60000,
                    "coda.dvv": 60000,
                    "recon.chk": 60000,
                    "ops.prop": 60000,
                    "gate.stop": 60000,
                    "res.hold": 60000,
                    "cool.start": 60000,
                    "cool.floor": 60000,
                    "ops.evac": 60000,
                    "gate.hold": 60000,
                    "res.set": 60000,
                    "res.held": 60000,
                    "dam.esd": 60000,
                },
                "time_alias": "t_rel_ms; t0 = 2026-07-23T21:50:00Z HIL campaign start",
            },
            "distillation_targets": [
                "coda-wave reconstruction head: dv/v = dt/t0; sigma = k_cw * dv/v",
                "stop-floor refuse vs keep-100 vs dam evacuate",
                "vendor-stress nonsubstitution: a frozen last-good is not a keep-100 witness",
                "operational companion: isolate B-12 plus reservoir 0.70 rather than a freeze-kill evacuate of the dam",
            ],
        },
        "reconstruction_model": {
            "name": "coda_wave_interferometry_stress",
            "formula": "dv_over_v = dt_ms / t0_ms; sigma_MPa = k_cw * dv_over_v",
            "parameters": {
                "t0_ms": 8.00,
                "k_cw": 400.00,
                "stop_floor_MPa": 6.00,
                "hold_res_pu": 0.70,
                "hold_min": 24.0,
            },
            "worked_example": {"dt_ms": 0.160, "dvv": 0.020, "sigma_MPa": 8.00},
            "check": "0.160/8.00 = 0.020 exactly; 400.00*0.020 = 8.00; 1500 s + 1440 s = 2940 s = 24.0 min floor",
        },
        "raster": raster,
        "gate_snn": {
            "decision": "REJECT",
            "decision_window_ms": 28.0,
            "decision_window_s": 0.028,
            "code": "gm5.coda_stop_gate",
            "note": "REJECT accumulator wins: coda-wave stress evidence overpowers the Waveveil continue advocate",
            "decode_rule": "reject-stop if stress_estimator AND coda_norm fire; vendor_continue_advocate is below threshold by design",
            "populations": [
                gate_pop("stress_estimator", 100, 1.5, 50.0, w_s),
                gate_pop("coda_norm", 40, 1.2, 50.0, w_s),
                gate_pop("vendor_continue_advocate", 32, 0.7, 25.0, w_s),
                gate_pop("reject_latch", 80, 1.8, 62.5, w_s),
            ],
        },
        "gate_compute": gate_compute(
            [
                {"check": "gm5.coda_scorer", "neurons": 100, "mean_rate_hz": 50.0, "window_ms": 28.0},
                {"check": "gm5.stop_scorer", "neurons": 40, "mean_rate_hz": 50.0, "window_ms": 40.0},
            ]
        ),
        "meta": meta_common(
            id="nelb-r45-137",
            clock_domain="gm5-coda-hil-relative-ms-t0-2026-07-23T21:50:00Z",
            tags=["coda-wave", "REJECT", "MODIFY", "hil", "operational-t2"],
        ),
    }


