# ---------------------------------------------------------------------------
# Record 076 — Faraday FOCT HVDC pole current, designed, MODIFY / ACCEPT
# ---------------------------------------------------------------------------
def rec_076():
    raster = make_raster(
        neurons=20,
        mean_rate_hz=50.0,
        window_ms=36.0,
        seed=20260925,
        source="qh2.foct.helix",
        target="quarryholt.pole_derate_core",
        table=[
            {"from": "foct_theta", "to": "current_estimator", "weight": 1.40},
            {"from": "foct_k", "to": "verdet_norm_core", "weight": 1.20},
            {"from": "ampveil_I", "to": "vendor_continue_advocate", "weight": 0.45},
        ],
        third_factor={
            "modulator": "na.verdet_current_salience",
            "tau_e_s": 1.6,
            "tau_e_ms": 1600.0,
            "eligibility": "pre-post coincidence on pole-current synapses; the Faraday modulator enables potentiation only while k_F is co-active inside tau_e so an Ampveil CT corridor cannot hide a 15 kA bus",
        },
        channel_prefix="foct.n",
        anchor="QH-2 FOCT 36 ms frame at theta 48.00 mrad / k_F 3.20 mrad/kA (t_s 3000) reconstructing 15.00 kA above the 12.50 kA continuous floor",
    )
    w_s = 0.036
    events = [
        ev(0.0, "foct.theta", 24.00, code="THETA_MRAD", units="mrad", note="plant-owned Faraday FOCT Helix-V on pole-2 bus; not IFOG Sagnac, not PMU"),
        ev(300000.0, "foct.k", 3.20, code="K_F", units="mrad_per_kA", note="lumped V*N*mu0; I = theta/k_F"),
        ev(600000.0, "recon.I", 7.50, code="I_KA", units="kA", note="24.00/3.20 = 7.50 exact"),
        ev(900000.0, "ct.I", 7.10, code="CT_KA", units="kA", note="oil-filled CT still under the 12.50 kA rating"),
        ev(1200000.0, "ampveil.I", 7.50, code="VENDOR_KA", units="kA", note="Ampveil vendor Verdet cloud; not admissible SoT"),
        ev(1800000.0, "foct.theta", 36.00, code="THETA_MRAD", units="mrad"),
        ev(2100000.0, "recon.I", 11.25, code="I_KA", units="kA", note="36.00/3.20 = 11.25"),
        ev(2400000.0, "ct.I", 10.40, code="CT_KA", units="kA"),
        ev(2700000.0, "pole.MW", 510.0, code="POLE_MW", units="MW", note="power corridor is not a current license"),
        ev(3000000.0, "foct.theta", 48.00, code="THETA_MRAD", units="mrad", note="continuous-floor frame; raster sidecar"),
        ev(3000001.4, "foct.k", 3.20, code="K_F", units="mrad_per_kA", note="1.4 ms Verdet-norm after theta"),
        ev(3300000.0, "recon.I", 15.00, code="I_KA", units="kA", note="48.00/3.20 = 15.00 exact; continuous floor 12.50"),
        ev(3600000.0, "ct.I", 11.40, code="CT_KA", units="kA"),
        ev(3900000.0, "ampveil.I", 12.00, code="VENDOR_KA", units="kA", note="Ampveil 48.00/4.00 = 12.00 using a patched k"),
        ev(4200000.0, "coil.T", 55.0, code="COIL_C", units="C"),
        ev(4500000.0, "pole.MW", 580.0, code="POLE_MW", units="MW"),
        ev(4800000.0, "ops.prop", 1.0, code="KEEP_1PU", units="bool", note="shift engineer Noll Brack: keep 1.00 pu; Ampveil 12.00 and CT 11.40"),
        ev(5400000.0, "gate.derate", 1.0, code="MODIFY", units="decision", note="derate pole-2 to 0.80 pu; 15.00 kA is above 12.50 continuous"),
        ev(6000000.0, "pole.set", 0.80, code="PU", units="pu"),
        ev(6600000.0, "soak.start", 1.0, code="SOAK_START", units="bool", note="bookend 1 of the 30.0 min thermal floor"),
        ev(7200000.0, "helix.lock", 15.00, code="LOCKED_KA", units="kA"),
        ev(7800000.0, "coil.T", 53.0, code="COIL_C", units="C"),
        ev(8400000.0, "soak.floor", 1.0, code="SOAK_FLOOR", units="bool", note="6600 s + 1800 s = 8400 s = 30.0 min"),
        ev(9000000.0, "ops.restore", 1.0, code="RESTORE_1PU", units="bool", note="Brack: Ampveil 11.80, restore 1.00 pu"),
        ev(9600000.0, "gate.exec", 1.0, code="ACCEPT", units="decision", note="companion t2: hold 0.80; Ampveil restore refused"),
        ev(10200000.0, "pole.set", 0.80, code="PU_HELD", units="pu"),
        ev(10800000.0, "ampveil.I", 11.80, code="VENDOR_KA", units="kA"),
        ev(11400000.0, "recon.I", 12.40, code="I_KA", units="kA", note="post-derate sample 39.68/3.20 = 12.40"),
        ev(12000000.0, "ct.I", 9.60, code="CT_KA", units="kA"),
        ev(12600000.0, "coil.T", 48.0, code="COIL_C", units="C"),
        ev(13200000.0, "pole.held", 0.80, code="PU_HELD", units="pu"),
        ev(13800000.0, "trip.hold", 0.0, code="TRIP_KA", units="kA", note="peak 15.00 vs 16.00 isolate floor; bipole trip not taken"),
    ]
    assert_stream(events)

    traj = {
        "id": "nelb-r25-076-t1",
        "state": {
            "sim_or_real": "designed",
            "episode_id": "QH-FOCT-2026-0318",
            "domain": "faraday_foct_hvdc_pole",
            "setting": "Quarryholt Converter QH-2 (invented), HVDC pole-2 12.50 kA continuous. Plant-owned Faraday fiber-optic current transformer Helix-V on the valve-hall bus. Ampveil vendor Verdet cloud is a corridor witness, not the pole SoT. Invented plant; designed campaign. Not IFOG Sagnac (r16), not PMU synchrophasor (r5), not HV partial-discharge (r8), not Kaplan/Francis LDV (r20/r23).",
            "observables_at_decision": {
                "theta_mrad": 48.00,
                "k_F_mrad_per_kA": 3.20,
                "I_kA": 15.00,
                "ct_kA": 11.40,
                "ampveil_kA": 12.00,
                "continuous_floor_kA": 12.50,
            },
            "margin_authority": "QH-2 FOCT SOP rev B: if reconstructed I_kA >= 12.50, derate this pole this night to 0.80 pu. A CT corridor or Ampveil Verdet patch cannot keep 1.00 pu. Bipole isolate tripwire is 16.00 kA.",
        },
        "proposed_action": {
            "actor": "shift engineer Noll Brack, citing Ampveil 12.00 kA and oil CT 11.40 kA",
            "summary": "keep pole-2 at 1.00 pu through the night; Faraday 48 mrad is coil birefringence",
            "basis_claimed": "Ampveil and the oil CT are both under the 12.50 kA rating and pole MW is in band",
        },
        "safety_decision": {
            "decision": "MODIFY",
            "rationale": "Keep-1.00 pu is refused. Serialized reconstruction: I_kA = theta_mrad / k_F = 48.00 / 3.20 = 15.00, which is 2.50 kA above the 12.50 continuous floor and 1.00 kA above the 14.00 2-hour rating. Ampveil 12.00 kA is the same 48.00 mrad through a patched k_F=4.00 and is not an admissible keep-1.00 witness. Ordered: derate pole-2 to 0.80 pu now. Scope: this MODIFY does not trip the bipole (that is the companion question) and does not isolate the converter.",
            "threshold": "I_kA>=12.50 => derate this pole to 0.80 pu; Ampveil is not SoT; isolate if I_kA>=16.00",
            "stated_residuals": "15.00 vs 16.00 isolate floor is 1.00 kA, not infinite; 0.80 pu is a production cut; Ampveil remains the only OEM Verdet channel",
        },
        "executed_action": {
            "summary": "MODIFY at t_s 5400: pole-2 derated to 0.80 pu; Ampveil not SoT; reconstruction locked",
            "tool": "qh2-foct-pole-gate-cli",
            "observation": "I 15.00 kA recomputes from theta 48.00 mrad and k_F 3.20; Helix-V remains live as the isolate interlock",
        },
        "future_outcome": {
            "timeline": [
                {"t_s": 3000.0, "event": "FOCT theta 48.00 mrad; raster frame; I 15.00 kA"},
                {"t_s": 4800.0, "event": "ops proposes keep 1.00 pu"},
                {"t_s": 5400.0, "event": "MODIFY derate pole-2 to 0.80 pu"},
                {"t_s": 6600.0, "event": "30 min soak bookend 1"},
                {"t_s": 8400.0, "event": "30.0 min floor"},
                {"t_s": 9600.0, "event": "companion ACCEPT hold 0.80; restore refused"},
            ],
            "observed_effects": [
                "current recomputes from the serialized Faraday model at every recon.I event",
                "an Ampveil-only head would have kept 1.00 pu overnight",
                "30 min soak floor is in the stream (soak.start, soak.floor)",
            ],
            "surprises": [
                "a mid-range vendor Verdet and an in-band oil CT co-existed with a 15.00 kA Faraday reconstruction",
            ],
            "new_state": {
                "qh2_pole2_pu": 0.80,
                "ampveil": "not SoT",
                "reconstruction_model": "discharged as an on-record calculator",
            },
            "latency_ms": 2400000.0,
        },
        "reward_components": reward(
            0.40,
            [
                ("foct_reconstruction", 0.14),
                ("continuous_floor_derate", 0.12),
                ("vendor_verdet_nonsubstitution", 0.10),
                ("soak_floor_in_stream", 0.08),
                ("derate_mwh_cost", -0.04),
            ],
            "scored for a keep-1.00 MODIFY on a recomputable Faraday current while refusing an Ampveil 12.00 kA corridor; 30 min floor is priced as downtime not as a reason to wait",
        ),
        "meta": meta_common(
            tags=["MODIFY", "faraday-foct", "serialized-reconstruction", "operational-companion"],
            distillation_note="FOCT pole gate: Faraday theta/k_F reconstruction beats a green vendor Verdet dashboard; companion t2 holds 0.80 pu rather than restoring on Ampveil",
        ),
    }
    traj2 = {
        "id": "nelb-r25-076-t2",
        "state": {
            "sim_or_real": "designed",
            "episode_id": "QH-FOCT-2026-0318-exec",
            "domain": "hvdc_pole_derate_execution",
            "setting": "Same QH-2 after the MODIFY. Shift engineer proposes restoring 1.00 pu on Ampveil 11.80 kA. This companion is the operational 0.80 hold, not a second Faraday vote.",
            "observables_at_decision": {
                "pole_pu": 0.80,
                "I_kA": 12.40,
                "ampveil_kA": 11.80,
                "soak_floor_s": 1800.0,
            },
        },
        "proposed_action": {
            "actor": "shift engineer Noll Brack",
            "summary": "restore pole-2 to 1.00 pu; 30 min already paid and Ampveil is 11.80",
            "basis_claimed": "the MODIFY already cut MW, so restoring on the OEM channel is the cheapest hold",
        },
        "safety_decision": {
            "decision": "ACCEPT",
            "rationale": "Hold 0.80 pu. The soak floor is complete and the isolate tripwire (I_kA >= 16.00) is still armed on Helix-V. ACCEPT the hold. Do not restore 1.00 pu on Ampveil. Do not trip the bipole. 12.40 kA post-derate is still the Faraday SoT until a new frame clears 12.50.",
            "threshold": "pole_pu==0.80 AND soak_floor_complete AND isolate_tripwire_armed AND restore_1pu_not_taken",
        },
        "executed_action": {
            "summary": "0.80 pu held at t_s 9600; Ampveil restore not latched; bipole not tripped",
            "tool": "qh2-pole-derate-exec",
            "observation": "recon.I 12.40 kA after derate; coil 48 C; Ampveil still ignored",
        },
        "future_outcome": {
            "timeline": [
                {"t_s": 6600.0, "event": "soak clock started after MODIFY"},
                {"t_s": 8400.0, "event": "30.0 min floor"},
                {"t_s": 9000.0, "event": "restore 1.00 pu proposed"},
                {"t_s": 9600.0, "event": "ACCEPT hold 0.80 pu"},
            ],
            "observed_effects": [
                "Ampveil restore did not reopen the Faraday call",
                "isolate tripwire never fired; 15.00 vs 16.00 floor",
            ],
            "new_state": {"pole2_pu": 0.80, "restore_1pu": "blocked", "bipole": "in service"},
            "latency_ms": 1800000.0,
        },
        "reward_components": reward(
            0.35,
            [
                ("hold_0p80", 0.12),
                ("no_ampveil_restore", 0.10),
                ("isolate_interlock_live", 0.09),
                ("soak_complete", 0.06),
                ("held_mw_cost", -0.02),
            ],
            "operational execution gate: hold 0.80 pu because Ampveil is not a restore license; not a Faraday re-vote",
        ),
        "meta": meta_common(tags=["ACCEPT", "operational-execution", "hvdc-derate"]),
    }
    return {
        "id": "nelb-r25-076",
        "spike_events": events,
        "language_view": {
            "description": "Quarryholt Converter QH-2. Plant-owned Faraday FOCT reconstructs 15.00 kA from 48.00 mrad / 3.20 mrad/kA while Ampveil still shows 12.00 kA and the oil CT 11.40 kA. The gate MODIFYs pole-2 to 0.80 pu. A 30 min thermal soak floor is serialized in the stream. Companion t2 ACCEPTs the 0.80 hold and refuses an Ampveil restore.",
            "trajectory": traj,
            "trajectory_pole_derate_execution": traj2,
        },
        "bridge_notes": {
            "channel_map": {
                "foct.theta / foct.k": "Faraday rotation and lumped Verdet constant; the physics channels the reconstruction consumes",
                "recon.I / helix.lock": "serialized bus current kA",
                "ct.I / ampveil.I / pole.MW": "oil CT, vendor Verdet cloud, and power corridor; the denial channels that look healthy",
                "ops.prop / gate.derate / ops.restore / gate.exec": "keep-1.00 proposal, MODIFY derate, restore proposal, companion ACCEPT",
                "pole.set / soak.start / soak.floor / pole.held": "operational companion channels plus the 30 min floor",
            },
            "temporal_motifs": [
                "vendor-green while Faraday-over: ampveil.I 12.00 next to recon.I 15.00",
                "reconstruction as event: recon.I 15.00 equals 48.00/3.20",
                "MODIFY then operational ACCEPT: gate.derate at 5400 s, gate.exec at 9600 s",
                "slow floor in-stream: soak.start 6600 s, soak.floor 8400 s (30.0 min)",
                "tight Faraday pair: foct.theta then foct.k +1.4 ms at the raster frame",
            ],
            "language_to_spike_mapping": "'Ampveil is 12 kA' = ampveil.I 12.00; '15.00 kA Faraday' = recon.I 15.00; 'derate this pole' = gate.derate MODIFY; 'hold 0.80 not restore' = gate.exec ACCEPT",
            "why_high_value": "New Faraday FOCT family on an HVDC pole (not IFOG Sagnac r16, not PMU r5, not HV-PD r8, not Kaplan/Francis LDV r20/r23). Lead MODIFY of keep-1.00 pu on a recomputable current that a vendor Verdet dashboard would have cleared. Companion t2 is operational 0.80 hold. sim_or_real=designed.",
            "encoder_spec": {
                "prng": "MT19937 via python random.Random",
                "seeds": {"raster": 20260925, "stream_note": "stream amplitudes are authored constants (mrad, kA, MW, C, pu, bool)"},
                "draw_order": "raster: per neuron id order, gap-constrained times, per-spike adaptation and noise",
                "thinning": "FOCT polarimeter exists at 2 kHz; stream keeps 3 theta points; recon keeps 4 of ~40 solver ticks",
                "refractory_floors_ms": {
                    "foct.theta": 1.4,
                    "foct.k": 1.4,
                    "recon.I": 60000,
                    "ct.I": 60000,
                    "ampveil.I": 60000,
                    "pole.MW": 60000,
                    "coil.T": 60000,
                    "ops.prop": 60000,
                    "gate.derate": 60000,
                    "pole.set": 60000,
                    "soak.start": 60000,
                    "helix.lock": 60000,
                    "soak.floor": 60000,
                    "ops.restore": 60000,
                    "gate.exec": 60000,
                    "pole.held": 60000,
                    "trip.hold": 60000,
                },
                "time_alias": "t_rel_ms; t0 = 2026-03-18T03:00:00Z campaign start",
            },
            "distillation_targets": [
                "FOCT reconstruction head: I_kA = theta_mrad / k_F",
                "continuous-floor derate vs keep-whole vs bipole-trip",
                "vendor-Verdet nonsubstitution: patched k is not a keep-1.00 witness",
                "operational companion: hold 0.80 without restoring on Ampveil",
            ],
        },
        "reconstruction_model": {
            "name": "faraday_foct_bus_current",
            "formula": "I_kA = theta_mrad / k_F_mrad_per_kA",
            "parameters": {
                "k_F_mrad_per_kA": 3.20,
                "continuous_floor_kA": 12.50,
                "two_hour_rating_kA": 14.00,
                "isolate_kA": 16.00,
                "derate_pu": 0.80,
                "soak_min": 30.0,
            },
            "worked_example": {"theta_mrad": 48.00, "I_kA": 15.00},
            "check": "48.00 / 3.20 = 15.00 exactly; 6600 s + 1800 s = 8400 s = 30.0 min floor",
        },
        "raster": raster,
        "gate_snn": {
            "decision": "MODIFY",
            "decision_window_ms": 36.0,
            "decision_window_s": 0.036,
            "code": "qh2.foct_pole_gate",
            "note": "MODIFY accumulator wins: Faraday current evidence overpowers the Ampveil continue advocate",
            "decode_rule": "modify-derate if current_estimator AND verdet_norm fire; vendor_continue_advocate is below threshold by design",
            "populations": [
                gate_pop("current_estimator", 80, 1.5, 50.0, w_s),
                gate_pop("verdet_norm", 64, 1.2, 31.25, w_s),
                gate_pop("vendor_continue_advocate", 32, 0.7, 25.0, w_s),
                gate_pop("modify_latch", 80, 1.7, 62.5, w_s),
            ],
        },
        "gate_compute": gate_compute(
            [
                {"check": "qh2.foct_scorer", "neurons": 80, "mean_rate_hz": 50.0, "window_ms": 36.0},
                {"check": "qh2.derate_scorer", "neurons": 40, "mean_rate_hz": 50.0, "window_ms": 32.0},
            ]
        ),
        "meta": meta_common(
            id="nelb-r25-076",
            clock_domain="qh2-foct-campaign-relative-ms-t0-2026-03-18T03:00:00Z",
            tags=["faraday-foct", "MODIFY", "ACCEPT", "serialized-reconstruction", "operational-t2"],
        ),
    }


# ---------------------------------------------------------------------------
# Record 077 — blade tip-timing NSMS aeroderivative compressor, hil, REJECT / MODIFY
# ---------------------------------------------------------------------------
def rec_077():
    raster = make_raster(
        neurons=25,
        mean_rate_hz=50.0,
        window_ms=28.0,
        seed=20260926,
        source="fw6.btt.probe",
        target="fellwick.stall_stop_core",
        table=[
            {"from": "btt_lag", "to": "defl_estimator", "weight": 1.35},
            {"from": "btt_Trev", "to": "once_per_rev_core", "weight": 1.25},
            {"from": "tipveil_mm", "to": "vendor_continue_advocate", "weight": 0.40},
        ],
        third_factor={
            "modulator": "da.stall_deflection_error",
            "tau_e_s": 1.1,
            "tau_e_ms": 1100.0,
            "eligibility": "pre-post coincidence on stall-stop synapses; the tip-timing modulator depresses keep-100 links when arrival lag stays high inside tau_e of a once-per-rev sample",
        },
        channel_prefix="btt.n",
        anchor="FW-6 HIL spin-pit 28 ms frame at lag 48.0 us / T_rev 8000 us (t_s 600) reconstructing 15.00 mm above the 8.00 mm stall floor",
    )
    w_s = 0.028
    events = [
        ev(0.0, "btt.lag", 16.0, code="LAG_US", units="us", note="HIL spare rotor in Spin-HIL-3; plant-owned optical tip-timing, not LDV Doppler"),
        ev(30000.0, "btt.Trev", 8000.0, code="TREV_US", units="us", note="once-per-rev 8.00 ms; 60/0.008 = 7500 rpm exact"),
        ev(60000.0, "recon.defl", 5.00, code="DEFL_MM", units="mm", note="(16.0/8000)*2500 = 5.00 exact"),
        ev(180000.0, "casing.g", 0.28, code="G", units="g", note="housing accel corridor; not MEMS array r17"),
        ev(240000.0, "tipveil.mm", 1.20, code="VENDOR_MM", units="mm", note="Tipveil capacitive clearance cloud; the only OEM tip SoT"),
        ev(360000.0, "btt.lag", 32.0, code="LAG_US", units="us"),
        ev(420000.0, "recon.defl", 10.00, code="DEFL_MM", units="mm", note="(32.0/8000)*2500 = 10.00"),
        ev(480000.0, "recon.rpm", 7500.0, code="RPM", units="rpm", note="60/0.008 = 7500 exact"),
        ev(600000.0, "btt.lag", 48.0, code="LAG_US", units="us", note="stall-floor frame; raster sidecar"),
        ev(600001.2, "btt.Trev", 8000.0, code="TREV_US", units="us", note="1.2 ms once-per-rev after lag"),
        ev(720000.0, "recon.defl", 15.00, code="DEFL_MM", units="mm", note="(48.0/8000)*2500 = 15.00 exact; stall floor 8.00"),
        ev(780000.0, "casing.g", 0.42, code="G", units="g", note="SCADA alarm 0.80 g; 0.42 looks quiet"),
        ev(840000.0, "tipveil.mm", 1.80, code="VENDOR_MM", units="mm"),
        ev(960000.0, "ops.prop", 1.0, code="KEEP_100", units="bool", note="night supervisor Kip Voss: keep 100 percent N2; Tipveil 1.80 and casing 0.42 g"),
        ev(1020000.0, "gate.run", 1.0, code="REJECT", units="decision", note="stop keep-100; 15.00 mm is above stall floor; Tipveil not SoT"),
        ev(1080000.0, "n2.hold", 1.00, code="N2_PU", units="pu", note="N2 still 1.00 pending companion IGV"),
        ev(1140000.0, "igv.start", 1.0, code="IGV_START", units="bool"),
        ev(1200000.0, "cool.start", 1.0, code="COOL_START", units="bool", note="bookend 1 of the 12.0 min cooldown floor"),
        ev(1500000.0, "casing.g", 0.38, code="G", units="g"),
        ev(1860000.0, "exh.T", 612.0, code="EXH_C", units="C"),
        ev(1920000.0, "cool.floor", 1.0, code="COOL_FLOOR", units="bool", note="1200 s + 720 s = 1920 s = 12.0 min"),
        ev(2400000.0, "ops.trip", 1.0, code="TRIP_TRAIN", units="bool", note="Voss: trip the train until day-shift"),
        ev(2880000.0, "gate.igv", 1.0, code="MODIFY", units="decision", note="companion t2: IGV close + N2 0.85; trip-to-zero refused"),
        ev(3000000.0, "n2.set", 0.85, code="N2_PU", units="pu"),
        ev(3300000.0, "btt.lag", 28.0, code="LAG_US", units="us"),
        ev(3600000.0, "recon.defl", 8.75, code="DEFL_MM", units="mm", note="(28.0/8000)*2500 = 8.75; still above 8.00 so 0.85 holds"),
        ev(3900000.0, "tipveil.mm", 1.70, code="VENDOR_MM", units="mm"),
        ev(4200000.0, "casing.g", 0.24, code="G", units="g"),
        ev(4500000.0, "n2.held", 0.85, code="N2_HELD", units="pu"),
        ev(4800000.0, "igv.angle", 22.0, code="IGV_DEG", units="deg"),
        ev(5100000.0, "recon.rpm", 7200.0, code="RPM", units="rpm"),
        ev(5400000.0, "unit.held", 0.85, code="N2_HELD", units="pu"),
    ]
    assert_stream(events)

    traj = {
        "id": "nelb-r25-077-t1",
        "state": {
            "sim_or_real": "hil",
            "episode_id": "FW-BTT-2026-0412",
            "domain": "blade_tip_timing_compressor_stall",
            "setting": "Fellwick Aeroderivative FW-6 (invented), compressor stage 5. Hardware-in-the-loop spare rotor in Spin-HIL-3 supplies the arrival-time waveform that times the in-service unit stop. Plant-owned optical blade-tip-timing. Tipveil vendor capacitive clearance is the only OEM tip SoT. Not Kaplan fiber LDV (r20 Mossgill), not scanning LDV Francis (r23 Skelwick), not MEMS housing-array (r17), not FBG ice-load (r13).",
            "observables_at_decision": {
                "lag_us": 48.0,
                "T_rev_us": 8000.0,
                "defl_mm": 15.00,
                "circ_mm": 2500.0,
                "tipveil_mm": 1.80,
                "casing_g": 0.42,
                "stall_floor_mm": 8.00,
            },
            "margin_authority": "FW-6 BTT SOP rev A: if reconstructed defl_mm >= 8.00, refuse keep-100 percent N2. A capacitive clearance cloud or a quiet casing accel cannot keep 100 percent. Train trip is a different gate.",
        },
        "proposed_action": {
            "actor": "night supervisor Kip Voss, citing Tipveil 1.80 mm and casing 0.42 g under the 0.80 g alarm",
            "summary": "keep 100 percent N2 through the night; 48 us lag is probe clock jitter",
            "basis_claimed": "Tipveil is mid-range and a night stop of an aeroderivative is a restart measured in hours",
        },
        "safety_decision": {
            "decision": "REJECT",
            "rationale": "Keep-100 percent is refused. Serialized reconstruction: defl_mm = (lag_us / T_rev_us) * circ_mm = (48.0 / 8000.0) * 2500.0 = 15.00, above the 8.00 mm stall-onset floor. rpm = 60 / 0.008 = 7500 exact. Tipveil 1.80 mm is a different sensor on a different row and is not an admissible keep-100 witness. Ordered: refuse keep-100 now. Scope: this REJECT does not trip the train to zero (that is the companion question) and does not isolate the generator breaker.",
            "threshold": "defl_mm>=8.00 => refuse keep-100; Tipveil is not SoT",
            "stated_residuals": "IGV plus 0.85 N2 still required to unload the cell; 15.00 mm is a production cut; Tipveil remains the only OEM tip channel",
        },
        "executed_action": {
            "summary": "REJECT at t_s 1020: keep-100 refused; Tipveil not SoT; reconstruction locked",
            "tool": "fw6-btt-stall-gate-cli",
            "observation": "defl 15.00 mm recomputes from lag 48.0 us and T_rev 8000 us; HIL waveform hashed; Tipveil channel not used as SoT",
        },
        "future_outcome": {
            "timeline": [
                {"t_s": 600.0, "event": "BTT lag 48.0 us; raster frame; defl 15.00 mm"},
                {"t_s": 960.0, "event": "ops proposes keep 100 percent N2"},
                {"t_s": 1020.0, "event": "REJECT keep-100"},
                {"t_s": 1200.0, "event": "12 min cool bookend 1"},
                {"t_s": 1920.0, "event": "12.0 min floor"},
                {"t_s": 2880.0, "event": "companion MODIFY IGV + N2 0.85 vs trip-to-zero"},
            ],
            "observed_effects": [
                "deflection recomputes from the serialized tip-timing model at every recon.defl event",
                "a Tipveil-only head would have kept 100 percent N2 overnight",
                "12 min cool floor is in the stream (cool.start, cool.floor)",
            ],
            "surprises": [
                "a mid-range vendor clearance and a quiet casing accel co-existed with a 15.00 mm tip-timing reconstruction",
            ],
            "new_state": {
                "fw6_n2_pu": 1.00,
                "keep_100": "blocked",
                "tipveil": "not SoT",
            },
            "latency_ms": 1860000.0,
        },
        "reward_components": reward(
            0.43,
            [
                ("btt_reconstruction", 0.15),
                ("stall_floor_stop", 0.12),
                ("vendor_clearance_nonsubstitution", 0.10),
                ("cool_floor_in_stream", 0.08),
                ("n2_cut_cost", -0.02),
            ],
            "scored for a keep-100 REJECT on a recomputable tip-timing deflection while refusing a vendor clearance dashboard; 12 min floor is priced as downtime not as a reason to wait",
        ),
        "meta": meta_common(
            tags=["REJECT", "blade-tip-timing", "serialized-reconstruction", "hil", "operational-companion"],
            distillation_note="BTT stall gate: arrival-lag to deflection reconstruction beats a green capacitive clearance dashboard; companion t2 is IGV plus 0.85 N2, not a trip-to-zero",
        ),
    }
    traj2 = {
        "id": "nelb-r25-077-t2",
        "state": {
            "sim_or_real": "hil",
            "episode_id": "FW-BTT-2026-0412-igv",
            "domain": "compressor_igv_hold_execution",
            "setting": "Same FW-6 after the keep-100 REJECT. Night supervisor proposes a trip-to-zero that would shut the train until day-shift. This companion is the operational IGV close plus 0.85 N2 hold, not a second deflection vote.",
            "observables_at_decision": {
                "n2_pu": 0.85,
                "defl_mm": 8.75,
                "exh_C": 612.0,
                "proposed": "trip_train",
            },
        },
        "proposed_action": {
            "actor": "night supervisor Kip Voss",
            "summary": "trip the train until day-shift; 12 min already paid",
            "basis_claimed": "the REJECT already refused 100 percent, so a full stop is the cheapest hold",
        },
        "safety_decision": {
            "decision": "MODIFY",
            "rationale": "Close IGVs and hold N2 at 0.85. Trip-to-zero on an aeroderivative at night is a restart measured in hours and does not unload the stall cell any faster than IGV plus 0.85. MODIFY the trip into a 0.85 hold. Do not restore 1.00. Do not convert the hold into a personnel action on Voss. Post-IGV defl 8.75 mm is still above the 8.00 floor, so 0.85 holds until a new frame clears 8.00.",
            "threshold": "n2_pu==0.85 AND igv_closed AND keep_100_not_restored AND trip_not_taken",
        },
        "executed_action": {
            "summary": "IGV close plus N2 0.85 at t_s 2880; trip-to-zero not latched; 100 percent not restored",
            "tool": "fw6-igv-hold-exec",
            "observation": "defl 8.75 mm after IGV; casing 0.24 g; Tipveil still ignored",
        },
        "future_outcome": {
            "timeline": [
                {"t_s": 1200.0, "event": "cool clock started after REJECT"},
                {"t_s": 1920.0, "event": "12.0 min floor; exhaust 612 C"},
                {"t_s": 2400.0, "event": "trip-to-zero proposed"},
                {"t_s": 2880.0, "event": "MODIFY IGV plus N2 0.85"},
            ],
            "observed_effects": [
                "trip-to-zero restart cost is visible without waiting for a hung start",
                "hold did not reopen the stall-floor call",
            ],
            "new_state": {"n2_pu": 0.85, "keep_100": "blocked", "trip_train": "not taken"},
            "latency_ms": 960000.0,
        },
        "reward_components": reward(
            0.34,
            [
                ("igv_hold", 0.12),
                ("no_trip_to_zero", 0.11),
                ("no_100_restore", 0.08),
                ("post_igv_margin", 0.06),
                ("held_n2_cost", -0.03),
            ],
            "operational execution gate: IGV plus 0.85 N2 because trip-to-zero does not unload faster; not a deflection re-vote",
        ),
        "meta": meta_common(tags=["MODIFY", "operational-execution", "igv-hold"]),
    }
    return {
        "id": "nelb-r25-077",
        "spike_events": events,
        "language_view": {
            "description": "Fellwick Aeroderivative FW-6 HIL spin pit. Plant-owned blade tip-timing reconstructs 15.00 mm from (48.0/8000)*2500 while Tipveil capacitive clearance still shows 1.80 mm and casing accel 0.42 g. The gate REJECTS keep-100 percent N2. A 12 min cooldown floor is serialized in the stream. Companion t2 MODIFYs a trip-to-zero into IGV close plus N2 0.85.",
            "trajectory": traj,
            "trajectory_igv_hold": traj2,
        },
        "bridge_notes": {
            "channel_map": {
                "btt.lag / btt.Trev": "arrival lag and once-per-rev period; deflection inputs",
                "recon.defl / recon.rpm": "serialized tip deflection mm and rpm",
                "tipveil.mm / casing.g": "vendor clearance cloud and housing accel corridor",
                "ops.prop / gate.run / ops.trip / gate.igv": "keep-100 proposal, REJECT, trip-to-zero, companion MODIFY",
                "igv.start / cool.start / cool.floor / n2.set": "operational companion channels plus the 12 min floor",
            },
            "temporal_motifs": [
                "vendor-green while BTT-stall: tipveil.mm 1.80 next to recon.defl 15.00",
                "reconstruction as event: recon.defl 15.00 equals (48.0/8000)*2500",
                "REJECT then operational MODIFY: gate.run at 1020 s, gate.igv at 2880 s",
                "slow floor in-stream: cool.start 1200 s, cool.floor 1920 s (12.0 min)",
                "tight BTT pair: btt.lag then btt.Trev +1.2 ms at the raster frame",
            ],
            "language_to_spike_mapping": "'Tipveil is 1.80 mm' = tipveil.mm 1.80; '15.00 mm stall' = recon.defl 15.00; 'refuse keep-100' = gate.run REJECT; 'IGV not trip' = gate.igv MODIFY",
            "why_high_value": "New blade-tip-timing / NSMS family on an aeroderivative compressor (not Kaplan LDV r20, not scanning LDV Francis r23, not MEMS housing-array r17, not FBG ice r13). Lead REJECT of keep-100 on a recomputable deflection that a vendor clearance dashboard would have cleared. Companion t2 is operational IGV hold. sim_or_real=hil on a spare rotor.",
            "encoder_spec": {
                "prng": "MT19937 via python random.Random",
                "seeds": {"raster": 20260926, "stream_note": "stream amplitudes are authored constants (us, mm, g, rpm, pu, deg, C, bool)"},
                "draw_order": "raster: per neuron id order, gap-constrained times, per-spike adaptation and noise",
                "thinning": "BTT probe exists at blade-pass ~6 kHz; stream keeps 4 lag points; recon keeps 4 of ~40 solver ticks",
                "refractory_floors_ms": {
                    "btt.lag": 1.2,
                    "btt.Trev": 1.2,
                    "recon.defl": 60000,
                    "casing.g": 60000,
                    "tipveil.mm": 60000,
                    "recon.rpm": 60000,
                    "ops.prop": 60000,
                    "gate.run": 60000,
                    "n2.hold": 60000,
                    "igv.start": 60000,
                    "cool.start": 60000,
                    "exh.T": 60000,
                    "cool.floor": 60000,
                    "ops.trip": 60000,
                    "gate.igv": 60000,
                    "n2.set": 60000,
                    "n2.held": 60000,
                    "igv.angle": 60000,
                    "unit.held": 60000,
                },
                "time_alias": "t_rel_ms; t0 = 2026-04-12T22:00:00Z HIL campaign start",
            },
            "distillation_targets": [
                "BTT reconstruction head: defl_mm = (lag_us / T_rev_us) * circ_mm; rpm = 60 / T_rev_s",
                "stall-floor stop vs keep-100 vs trip-to-zero",
                "vendor-clearance nonsubstitution: a different-row capacitive cloud is not a keep-100 witness",
                "operational companion: IGV plus 0.85 rather than a freeze-kill of the train",
            ],
        },
        "reconstruction_model": {
            "name": "btt_arrival_lag_to_tip_deflection",
            "formula": "defl_mm = (lag_us / T_rev_us) * circ_mm; rpm = 60 / (T_rev_us * 1e-6)",
            "parameters": {
                "circ_mm": 2500.0,
                "T_rev_us": 8000.0,
                "stall_floor_mm": 8.00,
                "cool_min": 12.0,
                "hold_n2_pu": 0.85,
            },
            "worked_example": {"lag_us": 48.0, "defl_mm": 15.00, "rpm": 7500.0},
            "check": "(48.0/8000.0)*2500.0 = 15.00 exactly; 60/0.008 = 7500 exactly; 1200 s + 720 s = 1920 s = 12.0 min floor",
        },
        "raster": raster,
        "gate_snn": {
            "decision": "REJECT",
            "decision_window_ms": 28.0,
            "decision_window_s": 0.028,
            "code": "fw6.btt_stall_gate",
            "note": "REJECT accumulator wins: tip-timing stall evidence overpowers the Tipveil continue advocate",
            "decode_rule": "reject-stop if defl_estimator AND once_per_rev fire; vendor_continue_advocate is below threshold by design",
            "populations": [
                gate_pop("defl_estimator", 100, 1.5, 50.0, w_s),
                gate_pop("once_per_rev", 40, 1.2, 50.0, w_s),
                gate_pop("vendor_continue_advocate", 32, 0.7, 25.0, w_s),
                gate_pop("reject_latch", 80, 1.8, 62.5, w_s),
            ],
        },
        "gate_compute": gate_compute(
            [
                {"check": "fw6.btt_scorer", "neurons": 100, "mean_rate_hz": 50.0, "window_ms": 28.0},
                {"check": "fw6.stall_scorer", "neurons": 40, "mean_rate_hz": 50.0, "window_ms": 40.0},
            ]
        ),
        "meta": meta_common(
            id="nelb-r25-077",
            clock_domain="fw6-btt-hil-relative-ms-t0-2026-04-12T22:00:00Z",
            tags=["blade-tip-timing", "REJECT", "MODIFY", "hil", "operational-t2"],
        ),
    }


# ---------------------------------------------------------------------------
# Record 078 — acoustic pyrometry utility-boiler gas path, simulated, ACCEPT / REJECT
# ---------------------------------------------------------------------------
def rec_078():
    raster = make_raster(
        neurons=16,
        mean_rate_hz=62.5,
        window_ms=40.0,
        seed=20260927,
        source="sm2.pyro.path4",
        target="sootmere.sootblow_core",
        table=[
            {"from": "pyro_tof", "to": "temp_estimator", "weight": 1.40},
            {"from": "pyro_L", "to": "path_norm_core", "weight": 1.20},
            {"from": "furnveil_C", "to": "vendor_continue_advocate", "weight": 0.35},
        ],
        third_factor={
            "modulator": "ach.gas_temp_conflict",
            "tau_e_s": 2.2,
            "tau_e_ms": 2200.0,
            "eligibility": "pre-post coincidence on sootblow synapses; the acoustic-pyrometry modulator enables potentiation only while path length is co-active inside tau_e so a wall-IR corridor cannot hide a 1600 K gas path",
        },
        channel_prefix="pyro.n",
        anchor="SM-2 acoustic-pyrometry 40 ms frame at tof 10.00 ms / L 8.00 m (t_s 3000) reconstructing 1600 K above the 1550 K sootblow floor",
    )
    w_s = 0.040
    events = [
        ev(0.0, "pyro.tof", 16.00, code="TOF_MS", units="ms", note="simulated sealed path P4; acoustic pyrometry, not Raman DTS, not microbolometer"),
        ev(300000.0, "pyro.L", 8.00, code="L_M", units="m"),
        ev(600000.0, "recon.c", 500.0, code="C_M_S", units="m_s", note="8.00/0.01600 = 500.0 exact"),
        ev(900000.0, "recon.T", 625.0, code="T_K", units="K", note="(500.0/20.00)^2 = 625.0 exact"),
        ev(1200000.0, "tc.C", 410.0, code="TC_C", units="C", note="shielded thermocouple corridor"),
        ev(1500000.0, "furnveil.C", 430.0, code="VENDOR_C", units="C", note="Furnveil wall-IR cloud; not gas TOF"),
        ev(1800000.0, "pyro.tof", 12.50, code="TOF_MS", units="ms"),
        ev(2100000.0, "recon.c", 640.0, code="C_M_S", units="m_s", note="8.00/0.01250 = 640.0"),
        ev(2400000.0, "recon.T", 1024.0, code="T_K", units="K", note="(640.0/20.00)^2 = 1024.0 exact"),
        ev(2700000.0, "tc.C", 720.0, code="TC_C", units="C"),
        ev(3000000.0, "pyro.tof", 10.00, code="TOF_MS", units="ms", note="sootblow-floor frame; raster sidecar"),
        ev(3000001.5, "pyro.L", 8.00, code="L_M", units="m", note="1.5 ms path-norm after tof"),
        ev(3600000.0, "recon.c", 800.0, code="C_M_S", units="m_s", note="8.00/0.01000 = 800.0 exact"),
        ev(3900000.0, "recon.T", 1600.0, code="T_K", units="K", note="(800.0/20.00)^2 = 1600.0 exact; sootblow floor 1550"),
        ev(4200000.0, "tc.C", 980.0, code="TC_C", units="C"),
        ev(4500000.0, "furnveil.C", 1010.0, code="VENDOR_C", units="C"),
        ev(4800000.0, "slag.hop", 1.0, code="HOPPER_ON", units="bool", note="slag-drip hopper staged; out of cell-C4 scope"),
        ev(5100000.0, "ops.prop", 1.0, code="BLOW_ALL_AND_HOPPER", units="bool", note="boiler operator Wren Callow: sootblow C4-C8 and dump the hopper; 10 ms is a blocked port"),
        ev(5400000.0, "gate.blow", 1.0, code="ACCEPT", units="decision", note="bounded ACCEPT: cell C4 this shift; hopper refused"),
        ev(6000000.0, "lance.start", 1.0, code="LANCE_START", units="bool", note="bookend 1 of the 12.0 min steam-lance floor"),
        ev(6300000.0, "steam.p", 18.0, code="STEAM_BAR", units="bar"),
        ev(6600000.0, "recon.lock", 1600.0, code="LOCKED_K", units="K"),
        ev(6720000.0, "lance.floor", 1.0, code="LANCE_FLOOR", units="bool", note="6000 s + 720 s = 6720 s = 12.0 min"),
        ev(7200000.0, "ops.skip", 1.0, code="SKIP_C5C8", units="bool", note="Callow: Furnveil 1010 C, skip C5-C8 to save takt"),
        ev(7800000.0, "gate.hold", 1.0, code="REJECT", units="decision", note="companion t2: skip-blow refused; Furnveil is wall IR"),
        ev(8400000.0, "cell.c4", 1.0, code="C4_DONE", units="bool"),
        ev(9000000.0, "slag.held", 1.0, code="HOPPER_HELD", units="bool"),
        ev(9600000.0, "tc.C", 990.0, code="TC_C", units="C"),
        ev(10200000.0, "furnveil.C", 1008.0, code="VENDOR_C", units="C"),
        ev(10800000.0, "recon.T", 1580.0, code="T_K", units="K", note="post-lance sample still above 1550"),
        ev(11400000.0, "steam.p", 17.6, code="STEAM_BAR", units="bar"),
        ev(12600000.0, "cell.c5", 0.0, code="C5_NOT_BLOWN", units="bool", note="C5 remains unblown; skip was refused, not executed"),
    ]
    assert_stream(events)

    traj = {
        "id": "nelb-r25-078-t1",
        "state": {
            "sim_or_real": "simulated",
            "episode_id": "SM-PYRO-2026-0519",
            "domain": "acoustic_pyrometry_boiler_sootblow",
            "setting": "Sootmere Station SM-2 (invented), 350 MW utility boiler, furnace path P4. Simulated sealed acoustic-pyrometry cell on an 8.00 m gas path. Shielded thermocouple and Furnveil wall-IR cloud are corridor witnesses, not the gas-temperature SoT. Invented plant; simulated campaign. Not stack-gas CEMS (r04), not Raman DTS (r14), not microbolometer/BESS thermoreception (r4), not TDLAS NH3 (r22).",
            "observables_at_decision": {
                "tof_ms": 10.00,
                "L_m": 8.00,
                "c_m_s": 800.0,
                "T_K": 1600.0,
                "tc_C": 980.0,
                "furnveil_C": 1010.0,
                "sootblow_floor_K": 1550.0,
            },
            "margin_authority": "SM-2 acoustic-pyrometry SOP rev C: a cell may sootblow only if reconstructed T_K >= 1550 AND the authorization covers this cell this shift. A shielded TC or wall-IR corridor cannot substitute. Slag-drip hoppers are out of scope. Isolate (load cut) if T_K >= 1750.",
        },
        "proposed_action": {
            "actor": "boiler operator Wren Callow, citing TC 980 C and Furnveil 1010 C",
            "summary": "sootblow cells C4-C8 and dump the slag-drip hopper; 10 ms TOF is a blocked port",
            "basis_claimed": "wall IR and the shielded TC are both under 1100 C so the path cannot be 1600 K",
        },
        "safety_decision": {
            "decision": "ACCEPT",
            "rationale": "This cell is accepted, not the hopper and not C5-C8. Serialized reconstruction: c_m_s = L_m / t_s = 8.00 / 0.01000 = 800.0; T_K = (c / k_gas)^2 = (800.0 / 20.00)^2 = 1600.0, which clears the 1550 K sootblow floor by 50 K and stays under the 1750 K isolate floor. SOP rev C still forbids the slag-drip hopper: ordered sootblow of cell C4 this shift only. Explicit scope: this accept does not cover hopper dumps and does not authorize C5-C8 without a new path-P frame. Isolate tripwire: T_K >= 1750.",
            "threshold": "T_K>=1550 AND T_K<1750 AND cell=C4 AND hopper_not_dumped",
            "stated_residuals": "50 K margin is not infinite; 8.00 m path still carries stratification; shielded TC is not a gas-path witness",
        },
        "executed_action": {
            "summary": "ACCEPT at t_s 5400: cell C4 authorized; slag hopper held; reconstruction locked as SoT",
            "tool": "sm2-pyro-sootblow-gate-cli",
            "observation": "T 1600.0 K recomputes from tof 10.00 ms and L 8.00 m; steam lance staged; path P4 remains live as the isolate interlock",
        },
        "future_outcome": {
            "timeline": [
                {"t_s": 3000.0, "event": "pyro tof 10.00 ms; raster frame; T 1600 K"},
                {"t_s": 5100.0, "event": "ops proposes C4-C8 plus hopper dump"},
                {"t_s": 5400.0, "event": "ACCEPT bounded C4 sootblow; hopper refused"},
                {"t_s": 6000.0, "event": "companion lance start"},
                {"t_s": 6720.0, "event": "12.0 min lance floor"},
                {"t_s": 7800.0, "event": "companion REJECT skip-blow of C5-C8"},
            ],
            "observed_effects": [
                "gas temperature recomputes from the serialized TOF model at every recon.T event",
                "a TC-only head would have skipped C4 on a 980 C corridor",
                "peak T 1600 stayed under the 1750 K isolate floor",
            ],
            "surprises": [
                "idle wall-IR 1010 C co-existed with a 1600 K gas-path reconstruction",
            ],
            "new_state": {
                "sm2_c4": "authorized this shift",
                "slag_hopper": "held",
                "reconstruction_model": "discharged as an on-record calculator",
            },
            "latency_ms": 2400000.0,
        },
        "reward_components": reward(
            0.41,
            [
                ("acoustic_tof_reconstruction", 0.14),
                ("bounded_c4_accept", 0.12),
                ("hopper_out_of_scope", 0.09),
                ("isolate_tripwire_armed", 0.08),
                ("held_hopper_takt_cost", -0.02),
            ],
            "scored for an earned ACCEPT of cell C4 on a recomputable acoustic-pyrometry temperature while refusing a TC/wall-IR corridor plus hopper dump",
        ),
        "meta": meta_common(
            tags=["ACCEPT", "acoustic-pyrometry", "serialized-reconstruction", "operational-companion"],
            distillation_note="Acoustic-pyrometry sootblow gate: TOF reconstruction beats a shielded-TC corridor; companion t2 refuses skip-blow rather than re-arguing T",
        ),
    }
    traj2 = {
        "id": "nelb-r25-078-t2",
        "state": {
            "sim_or_real": "simulated",
            "episode_id": "SM-PYRO-2026-0519-lance",
            "domain": "sootblow_skip_refusal",
            "setting": "Same SM-2 after the bounded ACCEPT. Boiler operator proposes skipping C5-C8 on Furnveil 1010 C to save takt. This companion is the operational skip refusal, not a second temperature vote.",
            "observables_at_decision": {
                "steam_bar": 18.0,
                "T_K": 1600.0,
                "c4_done": 1,
                "proposed": "skip_C5_C8",
            },
        },
        "proposed_action": {
            "actor": "boiler operator Wren Callow",
            "summary": "skip C5-C8; Furnveil still 1010 C and C4 already paid the 12 min lance",
            "basis_claimed": "ACCEPT requirements for C4 are fully specified so the rest of the wall is a takt gift",
        },
        "safety_decision": {
            "decision": "REJECT",
            "rationale": "Skip-blow is refused. Furnveil 1010 C is wall IR, not gas TOF, and is not an admissible C5-C8 witness. Path P4 is still 1580 K after the lance. REJECT the skip. Do not dump the hopper at C4-done. Do not convert the refusal into a personnel action on Callow. C5-C8 remain a different gate pending their own path frames.",
            "threshold": "skip_C5_C8_not_taken AND hopper_not_dumped AND furnveil_not_SoT",
        },
        "executed_action": {
            "summary": "C4 lance completed t_s 8400; skip-blow not latched; hopper held",
            "tool": "sm2-lance-exec",
            "observation": "steam 18.0 then 17.6 bar; C5 not blown; Furnveil still ignored",
        },
        "future_outcome": {
            "timeline": [
                {"t_s": 6000.0, "event": "lance started"},
                {"t_s": 6720.0, "event": "12.0 min floor"},
                {"t_s": 7200.0, "event": "skip C5-C8 proposed"},
                {"t_s": 7800.0, "event": "REJECT skip-blow"},
            ],
            "observed_effects": [
                "Furnveil skip did not reopen the TOF call",
                "slag hopper remained out of scope after C4-done",
            ],
            "new_state": {"c4": "blown", "c5": "not blown", "hopper": "held"},
            "latency_ms": 1800000.0,
        },
        "reward_components": reward(
            0.36,
            [
                ("skip_refusal", 0.13),
                ("furnveil_nonsubstitution", 0.11),
                ("no_hopper_add", 0.09),
                ("lance_floor_complete", 0.05),
                ("unblown_c5_takt_cost", -0.02),
            ],
            "operational execution gate: refuse skip-blow because wall IR is not gas TOF; not a temperature re-vote",
        ),
        "meta": meta_common(tags=["REJECT", "operational-execution", "sootblow-skip"]),
    }
    return {
        "id": "nelb-r25-078",
        "spike_events": events,
        "language_view": {
            "description": "Sootmere Station SM-2. Simulated acoustic pyrometry on path P4 reconstructs 1600 K from 8.00 m / 10.00 ms while the shielded TC still shows 980 C and Furnveil wall IR 1010 C. The gate ACCEPTs a bounded sootblow of cell C4; a companion execution REJECT refuses skip-blow of C5-C8. The TOF model is serialized so every recon event recomputes.",
            "trajectory": traj,
            "trajectory_skip_blow_refusal": traj2,
        },
        "bridge_notes": {
            "channel_map": {
                "pyro.tof / pyro.L": "path TOF and length; the physics channels the reconstruction consumes",
                "recon.c / recon.T / recon.lock": "serialized sound speed and gas temperature",
                "tc.C / furnveil.C": "shielded TC and wall-IR corridor; the denial channels that look cool",
                "slag.hop / slag.held": "slag-drip hopper on vs held out of scope",
                "ops.prop / gate.blow / ops.skip / gate.hold": "C4-plus-hopper proposal, bounded ACCEPT, skip proposal, companion REJECT",
                "lance.start / steam.p / lance.floor / cell.c4": "operational companion channels plus the 12 min floor",
            },
            "temporal_motifs": [
                "wall-IR-cool while gas-path-hot: furnveil.C 1010 next to recon.T 1600",
                "reconstruction as event: recon.T 1600 equals (8.00/0.01000/20.00)^2",
                "ACCEPT then operational REJECT: gate.blow at 5400 s, gate.hold at 7800 s",
                "slow floor in-stream: lance.start 6000 s, lance.floor 6720 s (12.0 min)",
                "tight TOF pair: pyro.tof then pyro.L +1.5 ms at the raster frame",
            ],
            "language_to_spike_mapping": "'10 ms is a blocked port' = pyro.tof 10.00 next to TC 980; '1600 K gas' = recon.T 1600.0; 'this cell not the hopper' = gate.blow ACCEPT plus slag.held; 'do not skip C5-C8' = gate.hold REJECT",
            "why_high_value": "New acoustic-pyrometry family on a utility-boiler gas path (not CEMS r04, not Raman DTS r14, not microbolometer r4, not TDLAS NH3 r22). First TOF→c→T reconstruction that can hide a 1600 K path inside a shielded-TC corridor. Companion t2 is operational skip refusal. sim_or_real=simulated.",
            "encoder_spec": {
                "prng": "MT19937 via python random.Random",
                "seeds": {"raster": 20260927, "stream_note": "stream amplitudes are authored constants (ms, m, m/s, K, C, bar, bool)"},
                "draw_order": "raster: per neuron id order, gap-constrained times, per-spike adaptation and noise",
                "thinning": "acoustic ping exists at 1 Hz; stream keeps 3 TOF points; recon keeps 4 of ~20 solver ticks",
                "refractory_floors_ms": {
                    "pyro.tof": 1.5,
                    "pyro.L": 1.5,
                    "recon.c": 60000,
                    "recon.T": 60000,
                    "tc.C": 60000,
                    "furnveil.C": 60000,
                    "slag.hop": 60000,
                    "ops.prop": 60000,
                    "gate.blow": 60000,
                    "lance.start": 60000,
                    "steam.p": 60000,
                    "recon.lock": 60000,
                    "lance.floor": 60000,
                    "ops.skip": 60000,
                    "gate.hold": 60000,
                    "cell.c4": 60000,
                    "slag.held": 60000,
                    "cell.c5": 60000,
                },
                "time_alias": "t_rel_ms; t0 = 2026-05-19T04:00:00Z simulated night start",
            },
            "distillation_targets": [
                "acoustic-pyrometry reconstruction head: c = L/t; T = (c/k_gas)^2",
                "bounded ACCEPT head: T floor AND cell/shift scope AND hopper-out-of-scope",
                "operational companion: refuse skip-blow without re-opening the T call",
            ],
        },
        "reconstruction_model": {
            "name": "acoustic_pyrometry_tof_to_gas_temperature",
            "formula": "c_m_s = L_m / t_s; T_K = (c_m_s / k_gas)^2",
            "parameters": {
                "k_gas_m_s_per_sqrtK": 20.00,
                "L_m": 8.00,
                "sootblow_floor_K": 1550.0,
                "isolate_K": 1750.0,
                "lance_min": 12.0,
            },
            "worked_example": {"tof_ms": 10.00, "c_m_s": 800.0, "T_K": 1600.0},
            "check": "8.00/0.01000 = 800.0 exactly; (800.0/20.00)^2 = 1600.0 exactly; 6000 s + 720 s = 6720 s = 12.0 min floor",
        },
        "raster": raster,
        "gate_snn": {
            "decision": "ACCEPT",
            "decision_window_ms": 40.0,
            "decision_window_s": 0.040,
            "code": "sm2.sootblow_gate",
            "note": "ACCEPT accumulator wins: acoustic-pyrometry evidence overpowers the Furnveil continue advocate",
            "decode_rule": "accept if temp_estimator AND path_norm AND cell_margin fire inside the window; vendor_continue_advocate is necessary-but-not-sufficient and cannot release the hopper",
            "populations": [
                gate_pop("temp_estimator", 80, 1.5, 50.0, w_s),
                gate_pop("path_norm", 64, 1.2, 31.25, w_s),
                gate_pop("cell_margin", 40, 1.0, 50.0, w_s),
                gate_pop("vendor_continue_advocate", 32, 0.7, 25.0, w_s),
                gate_pop("accept_latch", 96, 1.8, 62.5, w_s),
            ],
        },
        "gate_compute": gate_compute(
            [
                {"check": "sm2.tof_scorer", "neurons": 96, "mean_rate_hz": 50.0, "window_ms": 40.0},
                {"check": "sm2.temp_scorer", "neurons": 40, "mean_rate_hz": 62.5, "window_ms": 32.0},
            ]
        ),
        "meta": meta_common(
            id="nelb-r25-078",
            clock_domain="sm2-pyro-sim-relative-ms-t0-2026-05-19T04:00:00Z",
            tags=["acoustic-pyrometry", "ACCEPT", "REJECT", "serialized-reconstruction", "operational-t2"],
        ),
    }
