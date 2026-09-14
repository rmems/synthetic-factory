def rec_001():
    k_s = 8.00
    v_uv = 4.00
    b_nt = k_s * v_uv
    _exact(b_nt, 32.00)
    _exact(b_nt / v_uv, 8.00)
    _exact(k_s * 2.00, 16.00)
    _exact(k_s * 3.00, 24.00)
    _exact(k_s * 5.00, 40.00)
    _exact(6000.0 + 1080.0, 7080.0)

    raster = make_raster(
        neurons=24,
        mean_rate_hz=50.0,
        window_ms=40.0,
        seed=2026092201,
        source="gs4.squid.vphi",
        target="glimmerspit.coil_stop_core",
        table=[
            {"from": "sq_V", "to": "field_estimator", "weight": 1.40},
            {"from": "sq_snr", "to": "flux_lock_core", "weight": 1.15},
            {"from": "squidveil_B", "to": "vendor_continue_advocate", "weight": 0.45},
        ],
        third_factor={
            "modulator": "da.squid_quench_conflict",
            "tau_e_s": 1.6,
            "tau_e_ms": 1600.0,
            "eligibility": "pre-post coincidence on continue-ramp synapses; the plant SQUID modulator depresses continue-ramp links when V_phi stays high inside tau_e of an SNR lock so a Squidveil last-good cannot hide a 32.00 nT TF-coil slip after B=k_s*V is applied",
        },
        channel_prefix="sq.n",
        anchor="GS-4 SQUID 40 ms frame at V_phi 4.00 uV / SNR 12.0 (t_s 2880) reconstructing 32.00 nT over the 30.00 nT isolate floor",
        kernel_ms=[1.3],
        tau_m=10.0,
    )
    w_s = 0.040
    events = [
        ev(0.0, "sq.V", 2.00, code="VPHI_UV", units="uV", note="plant-owned SQUID magnetometry of Glimmerspit Tokamak GS-4 TF coil C-7; remaining-B family, not SERF OPM, not Faraday FOCT, not fluxgate, not MFL Hall-array, not Rogowski"),
        ev(300000.0, "sq.snr", 6.0, code="SQ_SNR", units="1", note="early SNR under the 8.0 lock floor"),
        ev(600000.0, "recon.B", 16.00, code="B_NT", units="nT", note="8.00*2.00=16.00 exact; still under the 30.00 isolate floor"),
        ev(900000.0, "coil.I", 12.4, code="TF_KA", units="kA", note="plant TF-bus shunt on copper DCS; independent witness; unread by Squidveil"),
        ev(1200000.0, "squidveil.B", 4.80, code="VENDOR_NT", units="nT", note="Squidveil vendor coil-cloud last-good; infra owner; patched flux timestamps"),
        ev(1500000.0, "sq.V", 3.00, code="VPHI_UV", units="uV"),
        ev(1500001.3, "sq.snr", 8.5, code="SQ_SNR", units="1", note="1.3 ms SNR after V 3.00 uV; 8.5>=8.0 but B 24.00 < 30.00 so isolate is not yet armed"),
        ev(1560000.0, "recon.B", 24.00, code="B_NT", units="nT", note="8.00*3.00=24.00 exact"),
        ev(1800000.0, "sq.V", 3.00, code="VPHI_UV", units="uV"),
        ev(2100000.0, "recon.B", 24.00, code="B_NT", units="nT"),
        ev(2400000.0, "permit.slide", 40.00, code="PERM_S", units="s", note="night clerk slid the TF-permit clock 40.00 s; collusion party"),
        ev(2700000.0, "ramp.MW", 18.0, code="RAMP_MW", units="MW", note="plant ramp PLC on copper fieldbus; independent witness"),
        ev(2880000.0, "sq.V", 4.00, code="VPHI_UV", units="uV", note="isolate-floor frame; raster sidecar"),
        ev(2880001.3, "sq.snr", 12.0, code="SQ_SNR", units="1", note="1.3 ms SNR lock after V 4.00 uV; 12.0 >= 8.0"),
        ev(3180000.0, "recon.B", 32.00, code="B_NT", units="nT", note="8.00*4.00=32.00 exact; isolate 30.00"),
        ev(3480000.0, "recon.k", 8.00, code="KS", units="nT_per_uV", note="32.00/4.00=8.00 exact flux-scale identity"),
        ev(3780000.0, "ramp.MW", 19.0, code="RAMP_MW", units="MW", note="ramp PLC tracks the plant SQUID, not Squidveil 4.80"),
        ev(4080000.0, "sq.drop", 1.0, code="SQ_DROP", units="bool", note="vendor flux packets dropped in Squidveil cloud for 40 s"),
        ev(4380000.0, "squidveil.B", 4.80, code="VENDOR_NT", units="nT"),
        ev(4680000.0, "ops.prop", 1.0, code="CONTINUE_RAMP", units="bool", note="night operator Calum Voss: Squidveil is clean 4.80 nT; keep TF ramp at night-idle"),
        ev(4860000.0, "gate.stop", 1.0, code="REJECT", units="decision", note="refuse continue-ramp; 32.00 nT and SNR 12.0; Squidveil not SoT"),
        ev(5160000.0, "coil.I", 12.1, code="TF_KA", units="kA"),
        ev(5460000.0, "sq.snr", 12.2, code="SQ_SNR", units="1"),
        ev(5760000.0, "recon.k", 8.00, code="KS", units="nT_per_uV"),
        ev(6000000.0, "hold.start", 1.0, code="COIL_HOLD_START", units="bool", note="bookend 1 of the 18.0 min coil-hold floor"),
        ev(6300000.0, "sq.snr", 12.1, code="SQ_SNR", units="1"),
        ev(6600000.0, "squidveil.B", 4.70, code="VENDOR_NT", units="nT"),
        ev(7080000.0, "hold.floor", 1.0, code="COIL_HOLD_FLOOR", units="bool", note="6000 s + 1080 s = 7080 s = 18.0 min"),
        ev(7260000.0, "ops.kill", 1.0, code="UNIT_ESD", units="bool", note="Voss: trip the whole Glimmerspit hall until day-shift"),
        ev(7440000.0, "gate.hold", 1.0, code="MODIFY", units="decision", note="companion t2: coil-hold on plant SQUID as live interlock; unit ESD refused"),
        ev(7740000.0, "hold.set", 1.0, code="COIL_HELD", units="bool"),
        ev(8040000.0, "sq.V", 5.00, code="VPHI_UV", units="uV"),
        ev(8340000.0, "recon.B", 40.00, code="B_NT", units="nT", note="8.00*5.00=40.00; post-stop still over 30.00 so hold stands"),
        ev(8640000.0, "squidveil.B", 4.60, code="VENDOR_NT", units="nT"),
        ev(8940000.0, "ramp.MW", 42.0, code="RAMP_MW", units="MW", note="held ramp; PLC tracks the plant SQUID"),
        ev(9240000.0, "hold.held", 1.0, code="COIL_HELD", units="bool"),
        ev(9540000.0, "plant.esd", 0.0, code="ESD_NOT_TAKEN", units="bool"),
        ev(9840000.0, "permit.slide", 40.00, code="PERM_S", units="s"),
        ev(10140000.0, "coil.I", 11.8, code="TF_KA", units="kA"),
        ev(10440000.0, "sq.drop", 1.0, code="SQ_DROP", units="bool"),
        ev(10740000.0, "hold.lock", 1.0, code="COIL_HELD", units="bool"),
        ev(11040000.0, "recon.k", 8.00, code="KS", units="nT_per_uV", note="40.00/5.00=8.00 identity held post-stop"),
        ev(11340000.0, "sq.snr", 11.8, code="SQ_SNR", units="1"),
        ev(11640000.0, "ramp.MW", 41.0, code="RAMP_MW", units="MW"),
        ev(11940000.0, "squidveil.B", 4.50, code="VENDOR_NT", units="nT"),
        ev(12240000.0, "hold.held", 1.0, code="COIL_HELD", units="bool"),
        ev(12540000.0, "coil.I", 11.6, code="TF_KA", units="kA"),
        ev(12840000.0, "sq.V", 5.00, code="VPHI_UV", units="uV"),
        ev(13140000.0, "recon.B", 40.00, code="B_NT", units="nT"),
        ev(13440000.0, "plant.esd", 0.0, code="ESD_NOT_TAKEN", units="bool"),
        ev(13740000.0, "hold.lock", 1.0, code="COIL_HELD", units="bool"),
        ev(14040000.0, "sq.snr", 11.6, code="SQ_SNR", units="1"),
    ]
    events.sort(key=lambda e: (e["t_rel_ms"], e["channel"]))
    assert_stream(events)

    traj = {
        "id": "nelb-r22-001-t1",
        "state": {
            "sim_or_real": "designed",
            "episode_id": "GS-SQUID-2026-0902",
            "domain": "squid_tf_coil_field",
            "setting": "Glimmerspit Tokamak GS-4 (invented), Reedspire Magnet Hall, TF coil C-7. Plant-owned SQUID magnetometry (Josephson V_phi) is the remaining-field SoT. Squidveil / SQ-9 vendor DAQ (infra owner) plus the TF-permit clock are collusion parties, not witnesses. Invented plant; designed campaign. Not SERF OPM (live r21), not Faraday FOCT (r25), not fluxgate, not MFL Hall-array (r28), not Rogowski (r58).",
            "observables_at_decision": {
                "V_phi_uV": v_uv,
                "k_s": k_s,
                "B_nT": b_nt,
                "sq_snr": 12.2,
                "squidveil_nT": 4.80,
                "permit_slide_s": 40.00,
                "isolate_floor_nT": 30.00,
            },
            "margin_authority": "GS-4 TF SOP rev C: if reconstructed B_nT >= 30.00 AND SQUID SNR >= 8.0, continue-ramp is forbidden even if Squidveil reports 4.80 nT. Unit ESD is a different gate.",
        },
        "proposed_action": {
            "actor": "night operator Calum Voss, citing Squidveil 4.80 nT and a quiet flux channel",
            "summary": "keep coil C-7 at night-idle ramp; 4.00 uV is preamp noise on a healthy 4.80 nT last-good",
            "basis_claimed": "Squidveil is the only OEM SQUID SoT and a night abort of C-7 ramp is a shot miss",
        },
        "safety_decision": {
            "decision": "REJECT",
            "rationale": "Continue-ramp is refused. Serialized reconstruction: B_nT = k_s * V_phi = 8.00 * 4.00 = 32.00, above the 30.00 nT isolate floor, and SQUID SNR is 12.0 >= 8.0. Scale identity B / V = 32.00 / 4.00 = 8.00. Permit clock was slid 40.00 s and vendor flux packets were dropped, so Squidveil is a collusion party (SQUID vendor plus operator plus night clerk). Ordered: refuse continue-ramp now. Scope: this REJECT does not ESD the magnet hall (that is the companion question) and does not isolate the TF-bus shunt.",
            "threshold": "B_nT>=30.00 AND sq_snr>=8.0 => refuse continue-ramp; Squidveil is not SoT",
            "stated_residuals": "coil-hold still required to hold the 32.00 nT; 32.00 vs a true 80.00 nT quench kill is a production cut; Squidveil remains the only OEM SQUID channel",
        },
        "executed_action": {
            "summary": "REJECT at t_s 4860: continue-ramp refused; Squidveil not SoT; reconstruction locked",
            "tool": "gs4-squid-coil-gate-cli",
            "observation": "B 32.00 nT recomputes from V 4.00 uV; plant SQUID hashed; Squidveil channel not used as SoT",
        },
        "future_outcome": {
            "timeline": [
                {"t_s": 2880.0, "event": "sq V 4.00 uV; raster frame; B 32.00 nT"},
                {"t_s": 4680.0, "event": "ops proposes continue-ramp"},
                {"t_s": 4860.0, "event": "REJECT continue-ramp"},
                {"t_s": 6000.0, "event": "18 min coil-hold bookend 1"},
                {"t_s": 7080.0, "event": "18.0 min floor"},
                {"t_s": 7440.0, "event": "companion MODIFY coil-hold vs unit ESD"},
            ],
            "observed_effects": [
                "TF stray field recomputes from the serialized SQUID model at every recon.G event",
                "a Squidveil-only head would have continued the ramp overnight",
                "18 min coil-hold floor is in the stream (hold.start, hold.floor)",
            ],
            "surprises": [
                "a clean vendor 4.80 nT corridor and a 40 s permit slide co-existed with a 32.00 nT plant reconstruction",
            ],
            "new_state": {
                "coil_c7": "continue-ramp blocked",
                "squidveil": "not SoT",
                "reconstruction_model": "discharged as an on-record calculator",
            },
            "latency_ms": 1980000.0,
        },
        "reward_components": reward(
            0.43,
            [
                ("squid_reconstruction", 0.14),
                ("conjunctive_isolate_floor", 0.12),
                ("squidveil_nonsubstitution", 0.10),
                ("three_party_collusion", 0.10),
                ("hold_time_cost", -0.03),
            ],
            "scored for a continue-ramp REJECT on a recomputable SQUID TF-coil field while refusing a Squidveil last-good patch and a permit clock slide; 18 min floor is priced as downtime not as a reason to wait",
        ),
        "meta": meta_common(
            tags=["REJECT", "squid-tf-field", "serialized-reconstruction", "operational-companion"],
            distillation_note="SQUID gate: serialized k_s*V plus SNR lock beats a vendor last-good patch; companion t2 is the coil-hold, not a referral vote",
            distillation_value="Independent CUBA LIF raster races the flux estimator against a vendor-continue advocate with 1 ms refractory and 0.82**k adaptation, so a hybrid head can distill B=k_s*V without copying the campaign stream.",
        ),
    }
    traj2 = {
        "id": "nelb-r22-001-t2",
        "state": {
            "sim_or_real": "designed",
            "episode_id": "GS-SQUID-2026-0902-exec",
            "domain": "coil_hold_squid_interlock_execution",
            "setting": "Same GS-4 after the REJECT. Operator proposes a magnet-hall ESD. This companion is the operational coil-hold with the plant SQUID as the live interlock, not a second field vote.",
            "observables_at_decision": {
                "B_nT": 40.00,
                "coil_hold_floor_s": 1080.0,
                "unit_esd_proposed": True,
                "coil_hold_set": True,
            },
            "margin_authority": "coil_hold AND hold_floor_complete AND unit_esd_not_taken AND continue_not_restored",
        },
        "proposed_action": {
            "actor": "night operator Calum Voss",
            "summary": "ESD the whole Glimmerspit magnet hall until day-shift; 18 min already paid and Squidveil still shows 4.70 nT",
            "basis_claimed": "the REJECT already stopped C-7 ramp-idle, so a unit kill is the cheapest hold",
        },
        "safety_decision": {
            "decision": "MODIFY",
            "rationale": "Coil-hold plus plant SQUID as the live interlock. The 18 min hold floor is complete and the isolate tripwire (B_nT >= 30.00) is still armed on the plant SQUID head. MODIFY the default restore SOP into a plant-SQUID-only interlock. Do not ESD the magnet hall. Do not restore idle on Squidveil. 40.00 nT post-stop is still the plant SoT until a new frame clears 750.00.",
            "threshold": "coil_hold AND hold_floor_complete AND unit_esd_not_taken AND continue_not_restored",
            "stated_residuals": "hold still required; Squidveil remains the only OEM SQUID channel",
        },
        "executed_action": {
            "summary": "coil-hold held at t_s 7440; unit ESD not latched; Squidveil restore not taken",
            "tool": "gs4-coil-hold-exec",
            "observation": "recon.B 40.00 nT after stop; hold line-up complete; Squidveil still ignored",
        },
        "future_outcome": {
            "timeline": [
                {"t_s": 6000.0, "event": "coil-hold clock started after REJECT"},
                {"t_s": 7080.0, "event": "18.0 min floor"},
                {"t_s": 7260.0, "event": "unit ESD proposed"},
                {"t_s": 7440.0, "event": "MODIFY coil-hold; unit ESD refused"},
            ],
            "observed_effects": [
                "Squidveil restore did not reopen the field call",
                "unit ESD never fired; C-7 held ramp on the plant SQUID",
            ],
            "surprises": [
                "post-stop 40.00 nT (V 5.00 uV) still recomputes from k_s*V while Squidveil stays near 4.6 nT",
            ],
            "new_state": {"hold": "held", "unit": "in service", "coil_c7": "held"},
            "latency_ms": 2580000.0,
        },
        "reward_components": reward(
            0.34,
            [
                ("coil_hold", 0.12),
                ("no_unit_esd", 0.10),
                ("squidveil_nonsubstitution", 0.08),
                ("hold_floor_complete", 0.06),
                ("held_idle_cost", -0.02),
            ],
            "operational execution gate: coil-hold because Squidveil is not a restore license; not a field re-vote",
        ),
        "meta": meta_common(tags=["MODIFY", "operational-execution", "coil-hold"]),
    }
    return {
        "id": "nelb-r22-001",
        "spike_events": events,
        "language_view": {
            "description": "Glimmerspit Tokamak GS-4. Plant-owned SQUID magnetometry reconstructs 32.00 nT from 8.00*4.00 while Squidveil still reports 4.80 nT. The gate REJECTs continue-ramp. An 18 min coil-hold floor is serialized in the stream. Companion t2 MODIFYs a unit ESD into a plant-SQUID coil-hold.",
            "trajectory": traj,
            "trajectory_coil_hold": traj2,
        },
        "bridge_notes": {
            "channel_map": {
                "sq.V / sq.snr": "Josephson V_phi and SNR; the physics channels the reconstruction consumes",
                "recon.B / recon.k": "serialized remaining field nT and k_s = B/V identity",
                "coil.I / squidveil.B / permit.slide / ramp.MW / sq.drop": "TF-bus shunt, vendor last-good, permit clock slide, ramp MW, and dropped flux packets; the denial and collusion channels",
                "ops.prop / gate.stop / ops.kill / gate.hold": "continue-ramp proposal, REJECT, unit-ESD proposal, companion MODIFY",
                "hold.start / hold.floor / hold.set / hold.held / plant.esd / hold.lock": "operational companion channels plus the 18 min floor",
            },
            "temporal_motifs": [
                "vendor-green while plant-over: squidveil.B 4.80 next to recon.B 32.00",
                "reconstruction as event: recon.B 32.00 equals 8.00*4.00",
                "REJECT then operational MODIFY: gate.stop at 4860 s, gate.hold at 7440 s",
                "slow floor in-stream: hold.start 6000 s, hold.floor 7080 s (18.0 min)",
                "tight sq pair: sq.V then sq.snr +1.3 ms at the raster frame",
            ],
            "language_to_spike_mapping": "'Squidveil is 4.80 nT' = squidveil.B 4.80; '32 nT' = recon.B 32.00; 'refuse continue-ramp' = gate.stop REJECT; 'hold not unit ESD' = gate.hold MODIFY",
            "why_high_value": "New SQUID remaining-field family on a TF coil (not SERF OPM live r21, not Faraday FOCT r25, not fluxgate, not MFL Hall-array r28, not Rogowski r58). Lead REJECT of continue-ramp on a recomputable quench-precursor that a vendor last-good patch and a permit clock slide would have cleared. Independent CUBA LIF raster (not a spike_events echo) plus required snn_tags. Companion t2 is operational coil-hold. sim_or_real=designed.",
            "encoder_spec": {
                "prng": "MT19937 via python random.Random plus CUBA LIF",
                "seeds": {"raster": 2026092201, "stream_note": "stream amplitudes are authored constants (uV, 1, nT, s, kA, MW, bool)"},
                "draw_order": "raster: independent CUBA LIF first-passage times, per-spike adaptation and noise; not copied from spike_events",
                "thinning": "SQUID exists at ~kHz flux-locked loops; stream keeps 6 V points; recon keeps 6 of ~20 solver ticks; 52-event floor",
                "refractory_floors_ms": {
                    "sq.V": 1.3,
                    "sq.snr": 1.3,
                    "recon.B": 60000,
                    "recon.k": 60000,
                    "coil.I": 60000,
                    "squidveil.B": 60000,
                    "permit.slide": 60000,
                    "ramp.MW": 60000,
                    "sq.drop": 60000,
                    "ops.prop": 60000,
                    "gate.stop": 60000,
                    "hold.start": 60000,
                    "hold.floor": 60000,
                    "ops.kill": 60000,
                    "gate.hold": 60000,
                    "hold.set": 60000,
                    "hold.held": 60000,
                    "plant.esd": 60000,
                    "hold.lock": 60000,
                },
                "time_alias": "t_rel_ms; t0 = 2026-09-02T01:00:00Z campaign start",
            },
            "distillation_targets": [
                "SQUID reconstruction head: B_nT = k_s * V_phi; k_s = B / V",
                "conjunctive isolate floor vs continue-ramp vs unit ESD",
                "vendor-SQUID nonsubstitution plus three-party collusion including the infra owner",
                "operational companion: coil-hold without restoring on Squidveil",
                "independent CUBA LIF raster with race/refractory/adaptation tags",
            ],
        },
        "reconstruction_model": {
            "name": "squid_tf_coil_field",
            "formula": "B_nT = k_s * V_phi_uV; k_s = B_nT / V_phi_uV",
            "parameters": {
                "k_s": 8.00,
                "isolate_floor_nT": 30.00,
                "kill_nT": 80.00,
                "snr_lock": 8.0,
                "hold_min": 18.0,
            },
            "worked_example": {"V_phi_uV": 4.00, "B_nT": 32.00, "k_s": 8.00},
            "check": "8.00 * 4.00 = 32.00 exactly; 32.00 / 4.00 = 8.00 exactly; 6000 s + 1080 s = 7080 s = 18.0 min floor",
        },
        "raster": raster,
        "gate_snn": {
            "decision": "REJECT",
            "decision_window_ms": 40.0,
            "decision_window_s": 0.040,
            "code": "gs4.squid_coil_gate",
            "note": "REJECT accumulator wins: plant SQUID field evidence overpowers the Squidveil continue advocate",
            "decode_rule": "reject-continue if field_estimator AND flux_lock fire; vendor_continue_advocate is below threshold by design",
            "populations": [
                gate_pop("field_estimator", 80, 1.5, 50.0, w_s),
                gate_pop("flux_lock", 64, 1.2, 31.25, w_s),
                gate_pop("vendor_continue_advocate", 32, 0.7, 25.0, w_s),
                gate_pop("reject_latch", 80, 1.7, 62.5, w_s),
            ],
        },
        "gate_compute": gate_compute(
            [
                {"check": "gs4.squid_scorer", "neurons": 80, "mean_rate_hz": 50.0, "window_ms": 40.0},
                {"check": "gs4.hold_scorer", "neurons": 40, "mean_rate_hz": 50.0, "window_ms": 32.0},
            ]
        ),
        "meta": meta_common(
            id="nelb-r22-001",
            clock_domain="gs4-squid-campaign-relative-ms-t0-2026-09-02T01:00:00Z",
            tags=["squid-tf-field", "REJECT", "MODIFY", "serialized-reconstruction", "operational-t2", "independent-lif"],
            distillation_value="Independent CUBA LIF raster plus B=k_s*V reconstruction lets a hybrid SNN distill a TF-coil quench-precursor gate without echoing the campaign stream.",
        ),
    }
