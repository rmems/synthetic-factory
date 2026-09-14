# ---------------------------------------------------------------------------
# Record 169 — IRIS pulse-echo remaining wall of a hydrotreater HEX tube, designed,
# REJECT / MODIFY
# ---------------------------------------------------------------------------
def rec_169():
    c_mm_us = 5.00
    tof_us = 3.20
    d_mm = c_mm_us * tof_us / 2.0
    _exact(d_mm, 8.00)
    t_nom = 20.00
    loss_mm = t_nom - d_mm
    _exact(loss_mm, 12.00)
    _exact(2.0 * d_mm / tof_us, 5.00)
    _exact(c_mm_us * 6.40 / 2.0, 16.00)
    _exact(c_mm_us * 4.80 / 2.0, 12.00)
    _exact(c_mm_us * 4.00 / 2.0, 10.00)
    _exact(6000.0 + 1080.0, 7080.0)

    raster = make_raster(
        neurons=20,
        mean_rate_hz=50.0,
        window_ms=40.0,
        seed=202609169,
        source="wx6.iris.tof",
        target="wexmere.hex_stop_core",
        table=[
            {"from": "iris_tof", "to": "wall_estimator", "weight": 1.40},
            {"from": "iris_snr", "to": "iris_lock_core", "weight": 1.15},
            {"from": "irisveil_d", "to": "vendor_continue_advocate", "weight": 0.45},
        ],
        third_factor={
            "modulator": "da.cross_authority_conflict",
            "tau_e_s": 1.6,
            "tau_e_ms": 1600.0,
            "eligibility": "pre-post coincidence on continue-firing synapses; the plant IRIS modulator depresses continue-firing links when pulse-echo ToF stays short inside tau_e of an SNR lock so an Irisveil last-campaign patch cannot hide an 8.00 mm remaining wall",
        },
        channel_prefix="iris.n",
        anchor="WX-6 IRIS pulse-echo 40 ms frame at ToF 3.20 us / SNR 12.0 (t_s 3000) reconstructing 8.00 mm remaining wall below the 12.00 min-wall floor",
    )
    w_s = 0.040
    events = [
        ev(0.0, "iris.tof", 6.40, code="TOF_US", units="us", note="plant-owned IRIS rotating pulse-echo on WX-6 HEX E-210 tube T-14; IRIS remaining-wall family, not PAUT TFM, not TOFD ligament, not EMAT SH, not PEC, not RFEC, not DCPD, not Lamb-wave, not impact-echo"),
        ev(300000.0, "iris.snr", 6.0, code="IRIS_SNR", units="1", note="early SNR under the 8.0 lock floor"),
        ev(600000.0, "recon.d", 16.00, code="D_MM", units="mm", note="5.00*6.40/2=16.00 exact; still above the 12.00 min-wall floor"),
        ev(900000.0, "hex.dP", 48.0, code="DP_KPA", units="kPa", note="plant HEX dP on copper fieldbus; independent witness; unread by Irisveil"),
        ev(1200000.0, "irisveil.d", 18.40, code="VENDOR_MM", units="mm", note="Irisveil vendor IRIS-9 last-campaign cloud; infra owner; patched ToF timestamps"),
        ev(1800000.0, "iris.tof", 4.80, code="TOF_US", units="us"),
        ev(2100000.0, "recon.d", 12.00, code="D_MM", units="mm", note="5.00*4.80/2=12.00; at the 12.00 min-wall floor"),
        ev(2400000.0, "permit.slide", 40.00, code="PERM_S", units="s", note="turnaround clerk slid the remaining-wall permit clock 40.00 s; collusion party"),
        ev(2700000.0, "hex.T", 612.0, code="HEX_K", units="K", note="plant HEX-skin thermocouple on copper DCS; independent witness"),
        ev(3000000.0, "iris.tof", 3.20, code="TOF_US", units="us", note="min-wall frame; raster sidecar"),
        ev(3000001.3, "iris.snr", 12.0, code="IRIS_SNR", units="1", note="1.3 ms SNR lock after ToF; 12.0 >= 8.0"),
        ev(3300000.0, "recon.d", 8.00, code="D_MM", units="mm", note="5.00*3.20/2=8.00 exact; min-wall 12.00"),
        ev(3600000.0, "recon.c", 5.00, code="C_MM_US", units="mm_us", note="2*8.00/3.20=5.00 exact compression-speed identity"),
        ev(3900000.0, "hex.dP", 52.0, code="DP_KPA", units="kPa", note="HEX dP tracks the plant IRIS, not Irisveil 18.40"),
        ev(4200000.0, "iris.drop", 1.0, code="IRIS_DROP", units="bool", note="vendor ToF packets dropped in Irisveil cloud for 40 s"),
        ev(4800000.0, "ops.prop", 1.0, code="CONTINUE_FIRING", units="bool", note="night operator Calum Voss: Irisveil is clean 18.40 mm; keep E-210 in service"),
        ev(5400000.0, "gate.stop", 1.0, code="REJECT", units="decision", note="refuse continue-firing; 8.00 mm and SNR 12.0; Irisveil not SoT"),
        ev(6000000.0, "soak.start", 1.0, code="SOAK_HOLD_START", units="bool", note="bookend 1 of the 18.0 min HEX-soak hold floor"),
        ev(7080000.0, "soak.floor", 1.0, code="SOAK_HOLD_FLOOR", units="bool", note="6000 s + 1080 s = 7080 s = 18.0 min"),
        ev(7800000.0, "ops.kill", 1.0, code="UNIT_TRIP", units="bool", note="Voss: trip the whole Wexmere hydrotreater until day-shift"),
        ev(8400000.0, "gate.hold", 1.0, code="MODIFY", units="decision", note="companion t2: HEX-soak hold on plant IRIS as live interlock; unit trip refused"),
        ev(9000000.0, "soak.set", 1.0, code="SOAK_HELD", units="bool"),
        ev(9600000.0, "iris.tof", 4.00, code="TOF_US", units="us"),
        ev(10200000.0, "recon.d", 10.00, code="D_MM", units="mm", note="5.00*4.00/2=10.00; still below 12.00 so soak holds"),
        ev(10800000.0, "irisveil.d", 18.32, code="VENDOR_MM", units="mm"),
        ev(11400000.0, "hex.dP", 50.0, code="DP_KPA", units="kPa"),
        ev(12000000.0, "soak.held", 1.0, code="SOAK_HELD", units="bool"),
        ev(12600000.0, "unit.trip", 0.0, code="TRIP_NOT_TAKEN", units="bool"),
        ev(13200000.0, "permit.slide", 40.00, code="PERM_S", units="s"),
        ev(13800000.0, "hex.T", 608.0, code="HEX_K", units="K"),
        ev(14400000.0, "iris.drop", 1.0, code="IRIS_DROP", units="bool"),
        ev(15000000.0, "soak.lock", 1.0, code="SOAK_HELD", units="bool"),
    ]
    assert_stream(events)

    traj = {
        "id": "nelb-r56-169-t1",
        "state": {
            "sim_or_real": "designed",
            "episode_id": "WX-IRIS-2026-0902",
            "domain": "iris_hex_remaining_wall",
            "setting": "Wexmere Hydrotreater WX-6 (invented), Alderspit Hydro Yard, HEX E-210 tube T-14. Plant-owned IRIS rotating pulse-echo is the remaining-wall SoT. Irisveil / IRIS-9 vendor DAQ (infra owner) plus the remaining-wall permit clock are collusion parties, not witnesses. Invented plant; designed campaign. Not PAUT TFM girth (r23), not TOFD ligament (r44/r46), not EMAT SH coil (r49), not PEC coated riser (r36), not RFEC boiler (r45), not DCPD girth (r38), not Lamb-wave (r35/r37), not impact-echo (r38).",
            "observables_at_decision": {
                "ToF_us": tof_us,
                "c_mm_us": c_mm_us,
                "d_mm": d_mm,
                "t_nom_mm": t_nom,
                "loss_mm": loss_mm,
                "iris_snr": 12.0,
                "irisveil_mm": 18.40,
                "permit_slide_s": 40.00,
                "min_wall_mm": 12.00,
            },
            "margin_authority": "WX-6 HEX SOP rev C: if reconstructed d_mm <= 12.00 AND IRIS SNR >= 8.0, continue-firing is forbidden even if Irisveil reports 18.40 mm. Unit trip is a different gate.",
        },
        "proposed_action": {
            "actor": "night operator Calum Voss, citing Irisveil 18.40 mm and a quiet IRIS-9 ToF",
            "summary": "keep HEX E-210 in service; 3.20 us is a water-path glitch on a healthy 18.40 mm last campaign",
            "basis_claimed": "Irisveil is the only OEM IRIS SoT and a night abort of E-210 is a turnaround miss",
        },
        "safety_decision": {
            "decision": "REJECT",
            "rationale": "Continue-firing is refused. Serialized reconstruction: d_mm = c * ToF / 2 = 5.00 * 3.20 / 2 = 8.00, below the 12.00 mm min-wall floor, and IRIS SNR is 12.0 >= 8.0. Compression-speed identity c = 2 * 8.00 / 3.20 = 5.00. Loss identity t_nom - d = 20.00 - 8.00 = 12.00. Permit clock was slid 40.00 s and vendor ToF packets were dropped, so Irisveil is a collusion party (IRIS vendor plus operator plus turnaround clerk). Ordered: refuse continue-firing now. Scope: this REJECT does not trip the hydrotreater (that is the companion question) and does not isolate the HEX thermocouple.",
            "threshold": "d_mm<=12.00 AND iris_snr>=8.0 => refuse continue-firing; Irisveil is not SoT",
            "stated_residuals": "soak still required to hold the 8.00 mm; 8.00 vs a true leak event is a production cut; Irisveil remains the only OEM IRIS channel",
        },
        "executed_action": {
            "summary": "REJECT at t_s 5400: continue-firing refused; Irisveil not SoT; reconstruction locked",
            "tool": "wx6-iris-hex-gate-cli",
            "observation": "d 8.00 mm recomputes from ToF 3.20 us; plant IRIS hashed; Irisveil channel not used as SoT",
        },
        "future_outcome": {
            "timeline": [
                {"t_s": 3000.0, "event": "iris ToF 3.20 us; raster frame; d 8.00 mm"},
                {"t_s": 4800.0, "event": "ops proposes continue-firing"},
                {"t_s": 5400.0, "event": "REJECT continue-firing"},
                {"t_s": 6000.0, "event": "18 min HEX-soak bookend 1"},
                {"t_s": 7080.0, "event": "18.0 min floor"},
                {"t_s": 8400.0, "event": "companion MODIFY HEX-soak hold vs unit trip"},
            ],
            "observed_effects": [
                "remaining wall recomputes from the serialized IRIS model at every recon.d event",
                "an Irisveil-only head would have continued firing overnight",
                "18 min HEX-soak floor is in the stream (soak.start, soak.floor)",
            ],
            "surprises": [
                "a clean vendor IRIS corridor and a 40 s permit slide co-existed with an 8.00 mm plant reconstruction",
            ],
            "new_state": {
                "hex_e210": "continue-firing blocked",
                "irisveil": "not SoT",
                "reconstruction_model": "discharged as an on-record calculator",
            },
            "latency_ms": 2400000.0,
        },
        "reward_components": reward(
            0.43,
            [
                ("iris_reconstruction", 0.14),
                ("conjunctive_min_wall", 0.12),
                ("irisveil_nonsubstitution", 0.10),
                ("three_party_collusion", 0.10),
                ("soak_time_cost", -0.03),
            ],
            "scored for a continue-firing REJECT on a recomputable IRIS remaining wall while refusing an Irisveil last-campaign patch and a permit clock slide; 18 min floor is priced as downtime not as a reason to wait",
        ),
        "meta": meta_common(
            tags=["REJECT", "iris-pulse-echo", "serialized-reconstruction", "operational-companion"],
            distillation_note="IRIS remaining-wall gate: serialized c*ToF/2 plus SNR lock beats a vendor last-campaign patch; companion t2 is the HEX-soak hold, not a referral vote",
        ),
    }
    traj2 = {
        "id": "nelb-r56-169-t2",
        "state": {
            "sim_or_real": "designed",
            "episode_id": "WX-IRIS-2026-0902-exec",
            "domain": "hex_soak_iris_interlock_execution",
            "setting": "Same WX-6 after the REJECT. Operator proposes a hydrotreater-unit trip. This companion is the operational HEX-soak hold with the plant IRIS as the live interlock, not a second remaining-wall vote.",
            "observables_at_decision": {
                "d_mm": 10.00,
                "soak_hold_floor_s": 1080.0,
                "unit_trip_proposed": True,
                "soak_hold_set": True,
            },
        },
        "proposed_action": {
            "actor": "night operator Calum Voss",
            "summary": "trip the whole Wexmere hydrotreater until day-shift; 18 min already paid and Irisveil still shows 18.32 mm",
            "basis_claimed": "the REJECT already stopped firing, so a unit trip is the cheapest hold",
        },
        "safety_decision": {
            "decision": "MODIFY",
            "rationale": "HEX-soak hold plus plant IRIS as the live interlock. The 18 min soak floor is complete and the min-wall tripwire (d_mm <= 12.00) is still armed on the plant IRIS head. MODIFY the default IRIS-restore SOP into a plant-IRIS-only interlock. Do not trip the hydrotreater. Do not restore firing on Irisveil. 10.00 mm post-stop is still the plant SoT until a new frame clears 12.00.",
            "threshold": "soak_hold AND soak_floor_complete AND unit_trip_not_taken AND continue_not_restored",
        },
        "executed_action": {
            "summary": "HEX-soak held at t_s 8400; unit trip not latched; Irisveil restore not taken",
            "tool": "wx6-hex-soak-exec",
            "observation": "recon.d 10.00 mm after stop; soak line-up complete; Irisveil still ignored",
        },
        "future_outcome": {
            "timeline": [
                {"t_s": 6000.0, "event": "HEX-soak clock started after REJECT"},
                {"t_s": 7080.0, "event": "18.0 min floor"},
                {"t_s": 7800.0, "event": "unit trip proposed"},
                {"t_s": 8400.0, "event": "MODIFY HEX-soak hold; unit trip refused"},
            ],
            "observed_effects": [
                "Irisveil restore did not reopen the remaining-wall call",
                "unit trip never fired; E-210 held soak on the plant IRIS",
            ],
            "new_state": {"soak": "held", "unit": "in service", "hex_e210": "held"},
            "latency_ms": 1800000.0,
        },
        "reward_components": reward(
            0.34,
            [
                ("hex_soak_hold", 0.12),
                ("no_unit_trip", 0.10),
                ("irisveil_nonsubstitution", 0.08),
                ("soak_floor_complete", 0.06),
                ("held_firing_cost", -0.02),
            ],
            "operational execution gate: HEX-soak hold because Irisveil is not a restore license; not a remaining-wall re-vote",
        ),
        "meta": meta_common(tags=["MODIFY", "operational-execution", "hex-soak-hold"]),
    }
    return {
        "id": "nelb-r56-169",
        "spike_events": events,
        "language_view": {
            "description": "Wexmere Hydrotreater WX-6. Plant-owned IRIS pulse-echo reconstructs 8.00 mm remaining wall from 3.20 us while Irisveil still reports 18.40 mm. The gate REJECTs continue-firing. An 18 min HEX-soak floor is serialized in the stream. Companion t2 MODIFYs a unit trip into a plant-IRIS soak hold.",
            "trajectory": traj,
            "trajectory_hex_soak_hold": traj2,
        },
        "bridge_notes": {
            "channel_map": {
                "iris.tof / iris.snr": "IRIS pulse-echo ToF and SNR; the physics channels the reconstruction consumes",
                "recon.d / recon.c": "serialized remaining wall mm and compression-speed identity",
                "hex.dP / irisveil.d / permit.slide / hex.T / iris.drop": "HEX dP, vendor last-campaign, permit clock slide, HEX thermocouple, and dropped IRIS packets; the denial and collusion channels",
                "ops.prop / gate.stop / ops.kill / gate.hold": "continue-firing proposal, REJECT, unit-trip proposal, companion MODIFY",
                "soak.start / soak.floor / soak.set / soak.held / unit.trip / soak.lock": "operational companion channels plus the 18 min floor",
            },
            "temporal_motifs": [
                "vendor-green while plant-under: irisveil.d 18.40 next to recon.d 8.00",
                "reconstruction as event: recon.d 8.00 equals 5.00*3.20/2",
                "REJECT then operational MODIFY: gate.stop at 5400 s, gate.hold at 8400 s",
                "slow floor in-stream: soak.start 6000 s, soak.floor 7080 s (18.0 min)",
                "tight iris pair: iris.tof then iris.snr +1.3 ms at the raster frame",
            ],
            "language_to_spike_mapping": "'Irisveil is 18.40 mm' = irisveil.d 18.40; '8 mm remaining' = recon.d 8.00; 'refuse continue-firing' = gate.stop REJECT; 'soak not unit trip' = gate.hold MODIFY",
            "why_high_value": "New IRIS pulse-echo remaining-wall family on a hydrotreater HEX tube (not PAUT TFM r23, not TOFD r44/r46, not EMAT SH r49, not PEC r36, not RFEC r45, not DCPD r38, not Lamb-wave r35/r37, not impact-echo r38). Lead REJECT of continue-firing on a recomputable remaining wall that a vendor last-campaign patch and a permit clock slide would have cleared. Three-party collusion includes the IRIS infra owner. Companion t2 is operational HEX-soak hold. sim_or_real=designed.",
            "encoder_spec": {
                "prng": "MT19937 via python random.Random",
                "seeds": {"raster": 202609169, "stream_note": "stream amplitudes are authored constants (us, 1, mm, s, K, kPa, bool)"},
                "draw_order": "raster: per neuron id order, gap-constrained times, per-spike adaptation and noise",
                "thinning": "IRIS ToF exists at ~20 Hz rotation; stream keeps 4 ToF points; recon keeps 4 of ~40 solver ticks",
                "refractory_floors_ms": {
                    "iris.tof": 1.3,
                    "iris.snr": 1.3,
                    "recon.d": 60000,
                    "recon.c": 60000,
                    "hex.dP": 60000,
                    "irisveil.d": 60000,
                    "permit.slide": 60000,
                    "hex.T": 60000,
                    "iris.drop": 60000,
                    "ops.prop": 60000,
                    "gate.stop": 60000,
                    "soak.start": 60000,
                    "soak.floor": 60000,
                    "ops.kill": 60000,
                    "gate.hold": 60000,
                    "soak.set": 60000,
                    "soak.held": 60000,
                    "unit.trip": 60000,
                    "soak.lock": 60000,
                },
                "time_alias": "t_rel_ms; t0 = 2026-09-02T01:00:00Z campaign start",
            },
            "distillation_targets": [
                "IRIS reconstruction head: d_mm = c * ToF / 2; c = 2 * d / ToF; loss = t_nom - d",
                "conjunctive min-wall floor vs continue-firing vs unit trip",
                "vendor-IRIS nonsubstitution plus three-party collusion including the infra owner",
                "operational companion: HEX-soak hold without restoring on Irisveil",
            ],
        },
        "reconstruction_model": {
            "name": "iris_pulse_echo_hex_wall",
            "formula": "d_mm = c_mm_us * ToF_us / 2; c_mm_us = 2 * d_mm / ToF_us; loss_mm = t_nom_mm - d_mm",
            "parameters": {
                "c_mm_us": 5.00,
                "t_nom_mm": 20.00,
                "min_wall_mm": 12.00,
                "snr_lock": 8.0,
                "soak_hold_min": 18.0,
            },
            "worked_example": {"ToF_us": 3.20, "d_mm": 8.00, "c_mm_us": 5.00, "loss_mm": 12.00},
            "check": "5.00 * 3.20 / 2 = 8.00 exactly; 2 * 8.00 / 3.20 = 5.00 exactly; 20.00 - 8.00 = 12.00 exactly; 6000 s + 1080 s = 7080 s = 18.0 min floor",
        },
        "raster": raster,
        "gate_snn": {
            "decision": "REJECT",
            "decision_window_ms": 40.0,
            "decision_window_s": 0.040,
            "code": "wx6.iris_hex_gate",
            "note": "REJECT accumulator wins: plant IRIS remaining-wall evidence overpowers the Irisveil continue advocate",
            "decode_rule": "reject-continue if wall_estimator AND iris_lock fire; vendor_continue_advocate is below threshold by design",
            "populations": [
                gate_pop("wall_estimator", 80, 1.5, 50.0, w_s),
                gate_pop("iris_lock", 64, 1.2, 31.25, w_s),
                gate_pop("vendor_continue_advocate", 32, 0.7, 25.0, w_s),
                gate_pop("reject_latch", 80, 1.7, 62.5, w_s),
            ],
        },
        "gate_compute": gate_compute(
            [
                {"check": "wx6.iris_scorer", "neurons": 80, "mean_rate_hz": 50.0, "window_ms": 40.0},
                {"check": "wx6.soak_scorer", "neurons": 40, "mean_rate_hz": 50.0, "window_ms": 32.0},
            ]
        ),
        "meta": meta_common(
            id="nelb-r56-169",
            clock_domain="wx6-iris-campaign-relative-ms-t0-2026-09-02T01:00:00Z",
            tags=["iris-pulse-echo", "REJECT", "MODIFY", "serialized-reconstruction", "operational-t2"],
        ),
    }


# ---------------------------------------------------------------------------
# Record 170 — dual-wavelength ratio pyrometer of a BOF bath, hil,
# MODIFY / ACCEPT
# ---------------------------------------------------------------------------
def rec_170():
    k_t = 400.0
    i1 = 9.00
    i2 = 2.00
    t_k = k_t * i1 / i2
    _exact(t_k, 1800.0)
    r_i = i1 / i2
    _exact(r_i, 4.50)
    _exact(k_t * 6.00 / 2.00, 1200.0)
    _exact(k_t * 8.00 / 2.00, 1600.0)
    _exact(k_t * 8.60 / 2.00, 1720.0)
    _exact(2820.0 + 1440.0, 4260.0)

    raster = make_raster(
        neurons=25,
        mean_rate_hz=50.0,
        window_ms=32.0,
        seed=202609170,
        source="gf5.pyro.ratio",
        target="glaurfen.heat_isolate_core",
        table=[
            {"from": "pyro_i12", "to": "temp_estimator", "weight": 1.35},
            {"from": "pyro_snr", "to": "ratio_norm_core", "weight": 1.20},
            {"from": "pyroveil_t", "to": "vendor_continue_advocate", "weight": 0.40},
        ],
        third_factor={
            "modulator": "ach.referral_pressure_salience",
            "tau_e_s": 1.2,
            "tau_e_ms": 1200.0,
            "eligibility": "pre-post coincidence on keep-blowing synapses; the pyrometer modulator depresses keep-blowing and referral links when the dual-wavelength ratio stays high inside tau_e of an SNR lock so a Pyroveil last-good cannot hide a 1800.0 K bath or name Nils Kade",
        },
        channel_prefix="pyro.n",
        anchor="GF-5 HIL coupon 32 ms frame at I1 9.00 / I2 2.00 / SNR 14.0 (t_s 1560) reconstructing 1800.0 K above the 1720 K isolate floor",
    )
    w_s = 0.032
    events = [
        ev(0.0, "pyro.I1", 6.00, code="I1", units="1", note="HIL dual-wavelength ratio pyrometer on a dummy BOF bath in PYRO-HIL-4; bath-temperature family, not acoustic pyrometry, not phosphor-lifetime, not CARS TIT, not LII soot, not lock-in thermography, not FMCW BOF lining"),
        ev(180000.0, "pyro.snr", 9.0, code="PYRO_SNR", units="1", note="early ratio SNR; isolate needs SNR>=12"),
        ev(360000.0, "recon.T", 1200.0, code="T_K", units="K", note="400.0*6.00/2.00=1200.0 exact"),
        ev(540000.0, "lamp.cal", 1.00, code="CAL", units="1", note="plant lamp-cal remaining; no emissivity hop in this window"),
        ev(720000.0, "pyroveil.T", 1620.0, code="VENDOR_K", units="K", note="Pyroveil last-good bath-cloud; not admissible SoT"),
        ev(900000.0, "pyro.I1", 8.00, code="I1", units="1"),
        ev(1080000.0, "recon.T", 1600.0, code="T_K", units="K", note="400.0*8.00/2.00=1600.0; still under the 1720 isolate floor"),
        ev(1260000.0, "lamp.delay", 0.0, code="LAMP_AE", units="bool", note="missing lamp-cal AE burst; Pyroveil UTC vs plant UTC+2 skipped the cal by 120 min"),
        ev(1440000.0, "lamp.cal", 1.00, code="CAL", units="1"),
        ev(1560000.0, "pyro.I1", 9.00, code="I1", units="1", note="isolate-floor frame; raster sidecar"),
        ev(1560001.2, "pyro.I2", 2.00, code="I2", units="1", note="1.2 ms I2 after I1; ratio 4.50"),
        ev(1740000.0, "recon.T", 1800.0, code="T_K", units="K", note="400.0*9.00/2.00=1800.0 exact; isolate 1720, trip 1950"),
        ev(1920000.0, "recon.R", 4.50, code="R", units="1", note="9.00/2.00=4.50 exact; ratio identity"),
        ev(2100000.0, "pyroveil.T", 1620.0, code="VENDOR_K", units="K"),
        ev(2280000.0, "ops.prop", 1.0, code="KEEP_BLOW_REFER", units="bool", note="night lead Rhea Pell: keep BOF-3 blowing and refer pyrometer tech Nils Kade"),
        ev(2460000.0, "gate.isol", 1.0, code="MODIFY", units="decision", note="isolate this heat; refuse the person-referral; Pyroveil not SoT"),
        ev(2640000.0, "heat.lock", 1.0, code="HEAT_ISOL", units="bool"),
        ev(2820000.0, "cool.start", 1.0, code="COOL_START", units="bool", note="bookend 1 of the 24.0 min cooldown plus pyrometer-settle floor"),
        ev(4260000.0, "cool.floor", 1.0, code="COOL_FLOOR", units="bool", note="2820 s + 1440 s = 4260 s = 24.0 min"),
        ev(4440000.0, "ops.refer", 1.0, code="REFER_KADE", units="bool", note="Pell: Kade badge was on the pyrometer log"),
        ev(4620000.0, "gate.exec", 1.0, code="ACCEPT", units="decision", note="companion t2: new-pyrometer restart; person-referral refused; shop trip refused"),
        ev(4800000.0, "pyro.new", 1.0, code="NEW_PYRO", units="bool"),
        ev(4980000.0, "pyro.I1", 8.60, code="I1", units="1"),
        ev(5160000.0, "recon.T", 1720.0, code="T_K", units="K", note="400.0*8.60/2.00=1720.0; HIL dummy still at the 1720 isolate floor so the isolated heat stays held"),
        ev(5340000.0, "pyroveil.T", 1614.0, code="VENDOR_K", units="K"),
        ev(5520000.0, "lamp.cal", 1.00, code="CAL", units="1"),
        ev(5700000.0, "refer.hold", 0.0, code="REFER_NOT_TAKEN", units="bool", note="Kade exonerated; missing lamp-cal AE precedes the high ratio, not the badge touch"),
        ev(5880000.0, "heat.held", 1.0, code="HEAT_HELD", units="bool"),
        ev(6060000.0, "lamp.delay", 1.0, code="LAMP_AE", units="bool", note="lamp-cal AE restored on the new pyrometer"),
        ev(6240000.0, "recon.R", 4.50, code="R", units="1", note="identity holds on the post-isolate ratio"),
        ev(6420000.0, "shop.trip", 0.0, code="TRIP_NOT_TAKEN", units="bool"),
        ev(6600000.0, "cell.restart", 1.0, code="CELL_RESTART", units="bool"),
    ]
    assert_stream(events)

    traj = {
        "id": "nelb-r56-170-t1",
        "state": {
            "sim_or_real": "hil",
            "episode_id": "GF-PYRO-2026-0718",
            "domain": "dual_wavelength_bof_bath",
            "setting": "Glaurfen Converter GF-5 (invented), Yarrowshaw Steel, BOF-3 bath. Hardware-in-the-loop dummy bath in PYRO-HIL-4 supplies the dual-wavelength intensities that time the in-service isolate. Plant-owned dual-wavelength reconstruction is the T SoT. Pyroveil vendor bath scheduler is a corridor witness, not the heat SoT. Not acoustic pyrometry (r25), not phosphor-lifetime (r39), not CARS TIT (r29), not LII soot (r31), not lock-in thermography (r23), not FMCW BOF lining (r33).",
            "observables_at_decision": {
                "I1": i1,
                "I2": i2,
                "R": r_i,
                "k_t": k_t,
                "T_K": t_k,
                "pyroveil_K": 1620.0,
                "lamp_cal": 1.00,
                "lamp_delay": 0.0,
                "isolate_floor_K": 1720.0,
            },
            "margin_authority": "GF-5 BOF SOP rev B: if reconstructed T_K >= 1720 AND pyrometer SNR >= 12.0, isolate this heat this night. A Pyroveil last-good or a quiet lamp-cal residual cannot keep the blow. Trip tripwire is 1950 K. Person-referral is a different gate.",
        },
        "proposed_action": {
            "actor": "night lead Rhea Pell, citing Pyroveil 1620 K and lamp-cal 1.00, and naming pyrometer tech Nils Kade as last-to-badge",
            "summary": "keep BOF-3 blowing and refer Kade; 9.00 / 2.00 is slag-emissivity noise on a healthy bath",
            "basis_claimed": "Pyroveil last-good is 1620 K and a night isolate of BOF-3 is a turnaround miss",
        },
        "safety_decision": {
            "decision": "MODIFY",
            "rationale": "Keep-blowing is refused; the person-referral is also refused. Serialized reconstruction: T_K = k_t * I1 / I2 = 400.0 * 9.00 / 2.00 = 1800.0, which is 80.0 K over the 1720 isolate floor and 150.0 K under the 1950 trip tripwire. Ratio identity I1/I2 = 9.00/2.00 = 4.50. Pyroveil 1620 K is a last-good skip stamp and is not an admissible keep-blowing witness. The missing lamp-cal AE burst sits on a Pyroveil UTC-vs-UTC+2 skip (120 min), not on Kade's badge, and the plant lamp-cal stays 1.00, so the easy referral fails command-custody. Ordered: isolate this heat now. Scope: this MODIFY does not trip the melt shop (that is the companion question) and does not name Kade.",
            "threshold": "T_K>=1720 AND pyro_snr>=12.0 => isolate this heat; Pyroveil is not SoT; trip if T_K>=1950; referral requires badge-touch preceding the high ratio",
            "stated_residuals": "1800 vs 1950 trip floor is 150 K, not infinite; new-pyrometer restart still required; Pyroveil remains the only OEM bath channel",
        },
        "executed_action": {
            "summary": "MODIFY at t_s 2460: heat isolated; Kade not named; Pyroveil not SoT; reconstruction locked",
            "tool": "gf5-pyro-heat-gate-cli",
            "observation": "T 1800.0 K recomputes from I1 9.00 and I2 2.00; HIL coupon hashed; Pyroveil channel not used as SoT",
        },
        "future_outcome": {
            "timeline": [
                {"t_s": 1560.0, "event": "pyro I1 9.00 I2 2.00; raster frame; T 1800.0 K"},
                {"t_s": 2280.0, "event": "ops proposes keep-blowing plus Kade referral"},
                {"t_s": 2460.0, "event": "MODIFY isolate heat; referral refused"},
                {"t_s": 2820.0, "event": "24 min cooldown bookend 1"},
                {"t_s": 4260.0, "event": "24.0 min floor"},
                {"t_s": 4620.0, "event": "companion ACCEPT new-pyrometer restart; referral still refused"},
            ],
            "observed_effects": [
                "T recomputes from the serialized dual-wavelength model at every recon.T event",
                "a Pyroveil-only head would have kept the heat blowing overnight",
                "24 min cooldown plus pyrometer-settle floor is in the stream (cool.start, cool.floor)",
            ],
            "surprises": [
                "a last-good 1620 K vendor corridor and a quiet lamp-cal residual co-existed with a 1800.0 K bath, and the obvious pyrometer tech was not on the causal path",
            ],
            "new_state": {
                "bof3": "isolated",
                "kade": "exonerated",
                "pyroveil": "not SoT",
                "reconstruction_model": "discharged as an on-record calculator",
            },
            "latency_ms": 1500000.0,
        },
        "reward_components": reward(
            0.40,
            [
                ("pyro_reconstruction", 0.14),
                ("isolate_floor_heat", 0.12),
                ("exoneration", 0.10),
                ("pyroveil_nonsubstitution", 0.08),
                ("settle_time_cost", -0.04),
            ],
            "scored for a keep-blowing MODIFY on a recomputable high bath temperature while refusing a Pyroveil 1620 K corridor and an easy person-referral; 24 min floor is priced as downtime",
        ),
        "meta": meta_common(
            tags=["MODIFY", "dual-wavelength-pyrometer", "serialized-reconstruction", "operational-companion"],
            distillation_note="Dual-wavelength pyrometer gate: serialized k_t*I1/I2 plus ratio identity beats a green bath dashboard; companion t2 is the new-pyrometer restart, not a governance vote",
        ),
    }
    traj2 = {
        "id": "nelb-r56-170-t2",
        "state": {
            "sim_or_real": "hil",
            "episode_id": "GF-PYRO-2026-0718-exec",
            "domain": "new_pyrometer_cooldown_execution",
            "setting": "Same GF-5 after the MODIFY. Night lead proposes referring Kade and tripping the melt shop. This companion is the operational new-pyrometer cooldown restart, not a second temperature vote.",
            "observables_at_decision": {
                "T_K": 1720.0,
                "R": 4.50,
                "cool_floor_s": 1440.0,
                "refer_proposed": True,
            },
        },
        "proposed_action": {
            "actor": "night lead Rhea Pell",
            "summary": "refer Kade and trip the melt shop; 24 min already paid and Pyroveil is 1614 K",
            "basis_claimed": "the MODIFY already cut the heat, so a shop kill plus a person file is the cheapest hold",
        },
        "safety_decision": {
            "decision": "ACCEPT",
            "rationale": "Restart the cell on a different pyrometer after the cooldown floor. The 24 min pyrometer-settle is complete and the trip tripwire (T_K >= 1950) is still armed on the plant dual-wavelength head. ACCEPT the new-pyrometer restart. Do not refer Kade. Do not trip the melt shop. 1720 K post-isolate is still at the 1720 isolate floor, so the isolated heat stays held; the new pyrometer may run.",
            "threshold": "new_pyrometer AND cool_floor_complete AND refer_not_taken AND shop_not_tripped AND isolated_heat_held",
        },
        "executed_action": {
            "summary": "new-pyrometer restart at t_s 4620; Kade not referred; shop not tripped; isolated heat held",
            "tool": "gf5-pyro-cool-exec",
            "observation": "recon.T 1720.0 K on the HIL dummy; lamp-cal AE present on the new pyrometer; Pyroveil still ignored",
        },
        "future_outcome": {
            "timeline": [
                {"t_s": 2820.0, "event": "cooldown clock started after MODIFY"},
                {"t_s": 4260.0, "event": "24.0 min floor"},
                {"t_s": 4440.0, "event": "Kade referral re-proposed"},
                {"t_s": 4620.0, "event": "ACCEPT new-pyrometer restart; referral refused"},
            ],
            "observed_effects": [
                "Pyroveil restore did not reopen the temperature call",
                "shop trip never fired; 1800 vs 1950 K floor",
                "Kade remains unnamed; missing lamp-cal AE is the causal object",
            ],
            "new_state": {"cell": "restarted on new pyrometer", "kade": "exonerated", "heat": "held", "shop": "in service"},
            "latency_ms": 1800000.0,
        },
        "reward_components": reward(
            0.35,
            [
                ("new_pyrometer_restart", 0.12),
                ("no_person_referral", 0.10),
                ("no_shop_trip", 0.09),
                ("cool_floor_complete", 0.06),
                ("held_heat_takt_cost", -0.02),
            ],
            "operational execution gate: restart on a new pyrometer because Pyroveil is not a restore license and Kade is not on the causal path; not a temperature re-vote",
        ),
        "meta": meta_common(tags=["ACCEPT", "operational-execution", "exoneration"]),
    }
    return {
        "id": "nelb-r56-170",
        "spike_events": events,
        "language_view": {
            "description": "Glaurfen Converter GF-5. HIL dual-wavelength ratio pyrometer reconstructs 1800.0 K from 9.00/2.00 while Pyroveil still shows 1620 K and the lamp-cal 1.00. The gate MODIFYs heat isolate and refuses the pyrometer-tech referral. A 24 min cooldown floor is serialized in the stream. Companion t2 ACCEPTs a new-pyrometer restart and still refuses the referral.",
            "trajectory": traj,
            "trajectory_new_pyrometer": traj2,
        },
        "bridge_notes": {
            "channel_map": {
                "pyro.I1 / pyro.I2 / pyro.snr": "dual-wavelength intensities and SNR; the physics channels the reconstruction consumes",
                "recon.T / recon.R": "serialized bath K and ratio identity",
                "lamp.cal / pyroveil.T / lamp.delay": "plant lamp-cal, vendor last-good, and lamp-cal AE; the denial and exoneration channels",
                "ops.prop / gate.isol / ops.refer / gate.exec": "keep-blowing proposal, MODIFY, referral proposal, companion ACCEPT",
                "heat.lock / cool.start / cool.floor / pyro.new / refer.hold / heat.held / shop.trip / cell.restart": "operational companion channels plus the 24 min floor",
            },
            "temporal_motifs": [
                "vendor-green while plant-over: pyroveil.T 1620 next to recon.T 1800.0",
                "reconstruction as event: recon.T 1800.0 equals 400.0*9.00/2.00",
                "MODIFY then operational ACCEPT: gate.isol at 2460 s, gate.exec at 4620 s",
                "slow floor in-stream: cool.start 2820 s, cool.floor 4260 s (24.0 min)",
                "tight pyro pair: pyro.I1 then pyro.I2 +1.2 ms at the raster frame",
            ],
            "language_to_spike_mapping": "'Pyroveil is 1620 K' = pyroveil.T 1620; '1800 K bath' = recon.T 1800.0; 'isolate this heat not Kade' = gate.isol MODIFY; 'new pyrometer not referral' = gate.exec ACCEPT",
            "why_high_value": "New dual-wavelength ratio-pyrometer family on a BOF bath (not acoustic pyrometry r25, not phosphor-lifetime r39, not CARS r29, not LII r31, not lock-in thermography r23, not FMCW BOF lining r33). Lead MODIFY of keep-blowing on a recomputable high bath temperature that a vendor last-good would have cleared, with a resolved-innocent pyrometer tech. Companion t2 is operational new-pyrometer restart. sim_or_real=hil.",
            "encoder_spec": {
                "prng": "MT19937 via python random.Random",
                "seeds": {"raster": 202609170, "stream_note": "stream amplitudes are authored constants (1, K, bool)"},
                "draw_order": "raster: per neuron id order, gap-constrained times, per-spike adaptation and noise",
                "thinning": "pyrometer ratio exists at ~10 Hz; stream keeps 4 I1 points plus one I2 pair; recon keeps 4 of ~20 solver ticks",
                "refractory_floors_ms": {
                    "pyro.I1": 1.2,
                    "pyro.I2": 1.2,
                    "pyro.snr": 1.2,
                    "recon.T": 60000,
                    "recon.R": 60000,
                    "lamp.cal": 60000,
                    "pyroveil.T": 60000,
                    "lamp.delay": 60000,
                    "ops.prop": 60000,
                    "gate.isol": 60000,
                    "heat.lock": 60000,
                    "cool.start": 60000,
                    "cool.floor": 60000,
                    "ops.refer": 60000,
                    "gate.exec": 60000,
                    "pyro.new": 60000,
                    "refer.hold": 60000,
                    "heat.held": 60000,
                    "shop.trip": 60000,
                    "cell.restart": 60000,
                },
                "time_alias": "t_rel_ms; t0 = 2026-07-18T02:30:00Z HIL night start",
            },
            "distillation_targets": [
                "pyrometer reconstruction head: T_K = k_t * I1 / I2; R = I1 / I2",
                "isolate-floor heat vs keep-blowing vs shop-trip",
                "exoneration head: missing lamp-cal AE plus timezone skip, not last-to-badge",
                "operational companion: new-pyrometer restart without referring the pyrometer tech",
            ],
        },
        "reconstruction_model": {
            "name": "dual_wavelength_ratio_pyrometer_bof",
            "formula": "T_K = k_t * I1 / I2; R = I1 / I2",
            "parameters": {
                "k_t": 400.0,
                "isolate_floor_K": 1720.0,
                "trip_K": 1950.0,
                "snr_lock": 12.0,
                "cool_min": 24.0,
            },
            "worked_example": {"I1": 9.00, "I2": 2.00, "R": 4.50, "T_K": 1800.0},
            "check": "9.00 / 2.00 = 4.50 exactly; 400.0 * 9.00 / 2.00 = 1800.0 exactly; 2820 s + 1440 s = 4260 s = 24.0 min floor",
        },
        "raster": raster,
        "gate_snn": {
            "decision": "MODIFY",
            "decision_window_ms": 32.0,
            "decision_window_s": 0.032,
            "code": "gf5.pyro_heat_gate",
            "note": "MODIFY accumulator wins: dual-wavelength high-T evidence overpowers the Pyroveil continue advocate",
            "decode_rule": "modify-isolate if temp_estimator AND ratio_norm fire; vendor_continue_advocate is below threshold by design; referral_latch is not armed",
            "populations": [
                gate_pop("temp_estimator", 80, 1.5, 50.0, w_s),
                gate_pop("ratio_norm", 64, 1.2, 31.25, w_s),
                gate_pop("vendor_continue_advocate", 32, 0.7, 25.0, w_s),
                gate_pop("modify_latch", 80, 1.7, 62.5, w_s),
            ],
        },
        "gate_compute": gate_compute(
            [
                {"check": "gf5.pyro_scorer", "neurons": 80, "mean_rate_hz": 50.0, "window_ms": 32.0},
                {"check": "gf5.isol_scorer", "neurons": 50, "mean_rate_hz": 50.0, "window_ms": 32.0},
            ]
        ),
        "meta": meta_common(
            id="nelb-r56-170",
            clock_domain="gf5-pyro-hil-relative-ms-t0-2026-07-18T02:30:00Z",
            tags=["dual-wavelength-pyrometer", "MODIFY", "ACCEPT", "serialized-reconstruction", "operational-t2"],
        ),
    }


# ---------------------------------------------------------------------------
# Record 171 — UV fluorescence oil-in-water of a produced-water polisher, simulated,
# ACCEPT / REJECT
# ---------------------------------------------------------------------------
def rec_171():
    k_f = 4.00
    i_uv = 14.00
    i_bg = 2.00
    i_ref = 2.00
    c_ppm = k_f * (i_uv - i_bg) / i_ref
    _exact(c_ppm, 24.00)
    _exact(k_f * (5.00 - i_bg) / i_ref, 6.00)
    _exact(k_f * (8.00 - i_bg) / i_ref, 12.00)
    _exact(k_f * (12.00 - i_bg) / i_ref, 20.00)
    ratio = (i_uv - i_bg) / i_ref
    _exact(ratio, 6.00)
    _exact(12.00 / (20.00 * 0.00 + 2.00) if False else (12.00 - 2.00) / 2.00, 5.00)
    _exact(6000.0 + 720.0, 6720.0)

    raster = make_raster(
        neurons=16,
        mean_rate_hz=62.5,
        window_ms=36.0,
        seed=202609171,
        source="rf9.oiw.uv",
        target="rushfen.pol_accept_core",
        table=[
            {"from": "oiw_I", "to": "ppm_estimator", "weight": 1.40},
            {"from": "oiw_Iref", "to": "ref_norm_core", "weight": 1.20},
            {"from": "fluoveil_c", "to": "vendor_skip_advocate", "weight": 0.50},
        ],
        third_factor={
            "modulator": "na.stage_rate_eligibility",
            "tau_e_s": 2.0,
            "tau_e_ms": 2000.0,
            "eligibility": "pre-post coincidence on skip-polisher synapses; the UV-fluorescence modulator enables potentiation only while sample intensity and I_ref are co-active inside tau_e so a Fluoveil last-good cannot skip polishers P-1 and P-2 on a 24.00 ppm oil load",
        },
        channel_prefix="oiw.n",
        anchor="RF-9 OIW-SIM-2 36 ms frame at I 14.00 / I_ref 2.00 (t_s 3000) reconstructing 24.00 ppm on P-3 above the 20.00 isolate floor",
    )
    w_s = 0.036
    events = [
        ev(0.0, "oiw.I", 5.00, code="I_UV", units="1", note="simulated UV fluorescence oil-in-water of RF-9 produced-water polisher P-3; OIW family, not SPR cyanide, not Raman OH-CH, not QEPAS, not LIBS, not CRDS, not TDLAS, not chemiluminescence NOx, not TEOM PM"),
        ev(300000.0, "oiw.Iref", 2.00, code="I_REF", units="1", note="reference photodiode; held at 2.00"),
        ev(600000.0, "recon.C", 6.00, code="C_PPM", units="ppm", note="4.00*(5.00-2.00)/2.00=6.00 exact"),
        ev(900000.0, "oiw.snr", 14.0, code="OIW_SNR", units="1"),
        ev(1200000.0, "fluoveil.C", 4.80, code="VENDOR_PPM", units="ppm", note="Fluoveil last-good lab-GC cloud; patched residual 6.00 ppm"),
        ev(1800000.0, "oiw.I", 8.00, code="I_UV", units="1"),
        ev(2100000.0, "recon.C", 12.00, code="C_PPM", units="ppm", note="4.00*(8.00-2.00)/2.00=12.00"),
        ev(2400000.0, "recon.R", 6.00, code="R", units="1", note="placeholder early; ratio identity is locked at the in-band frame"),
        ev(2700000.0, "oiw.snr", 16.0, code="OIW_SNR", units="1"),
        ev(3000000.0, "oiw.I", 14.00, code="I_UV", units="1", note="in-band frame; raster sidecar"),
        ev(3000001.5, "oiw.Iref", 2.00, code="I_REF", units="1", note="1.5 ms I_ref-norm after sample intensity"),
        ev(3300000.0, "recon.C", 24.00, code="C_PPM", units="ppm", note="4.00*(14.00-2.00)/2.00=24.00 exact; isolate 20.00, dump-trip 80.00"),
        ev(3600000.0, "fluoveil.C", 4.80, code="VENDOR_PPM", units="ppm"),
        ev(3900000.0, "pol.id", 3.0, code="POL", units="id"),
        ev(4200000.0, "p12.present", 1.0, code="P12_PRESENT", units="bool", note="adjacent polishers P-1 and P-2 are the skip-isolate object, not this polisher"),
        ev(4800000.0, "ops.prop", 1.0, code="ACCEPT_AND_SKIP", units="bool", note="water lead Oren Pike: P-3 is green on Fluoveil 4.80; skip P-1 and P-2 to save a morning survey"),
        ev(5400000.0, "gate.comp", 1.0, code="ACCEPT", units="decision", note="bounded ACCEPT of P-3 isolate only; 24.00 ppm above 20.00 floor; P-1 and P-2 out of scope"),
        ev(6000000.0, "surv.start", 1.0, code="SURV_START", units="bool", note="bookend 1 of the 12.0 min survey-complete floor"),
        ev(6720000.0, "surv.floor", 1.0, code="SURV_FLOOR", units="bool", note="6000 s + 720 s = 6720 s = 12.0 min"),
        ev(7200000.0, "ops.skip", 1.0, code="SKIP_P12", units="bool", note="Pike: Fluoveil 4.80, skip P-1 and P-2"),
        ev(7800000.0, "gate.hold", 1.0, code="REJECT", units="decision", note="companion t2: skip-isolate of P-1 and P-2 refused; P-3 hold stands"),
        ev(8400000.0, "p3.held", 1.0, code="P3_HELD", units="bool"),
        ev(9000000.0, "oiw.I", 12.00, code="I_UV", units="1"),
        ev(9600000.0, "recon.C", 20.00, code="C_PPM", units="ppm", note="4.00*(12.00-2.00)/2.00=20.00; still at the 20.00 isolate floor"),
        ev(10200000.0, "fluoveil.C", 4.80, code="VENDOR_PPM", units="ppm"),
        ev(10800000.0, "p12.skip", 0.0, code="P12_NOT_SKIPPED", units="bool"),
        ev(11400000.0, "dump.trip", 0.0, code="DUMP_NOT_TRIPPED", units="bool"),
        ev(12000000.0, "oiw.snr", 15.0, code="OIW_SNR", units="1"),
        ev(12600000.0, "recon.R", 6.00, code="R", units="1", note="(14.00-2.00)/2.00=6.00 identity on the in-band frame; post-accept I_net/I_ref=(12.00-2.00)/2.00=5.00"),
        ev(13200000.0, "pol.held", 1.0, code="POL_HELD", units="bool"),
        ev(13800000.0, "takt.late", 1.0, code="SURVEY_COST", units="bool"),
        ev(14400000.0, "p3.held", 1.0, code="P3_HELD", units="bool"),
    ]
    assert_stream(events)

    traj = {
        "id": "nelb-r56-171-t1",
        "state": {
            "sim_or_real": "simulated",
            "episode_id": "RF-OIW-2026-0819",
            "domain": "uv_fluorescence_oiw_polisher",
            "setting": "Rushfen Produced-Water RF-9 (invented), Skeldshaw Catchment, polisher P-3. Simulated UV-fluorescence coupon in OIW-SIM-2 supplies the sample intensity and I_ref that time the in-band P-3 isolate. Plant-owned UV-fluorescence reconstruction is the oil-in-water SoT. Fluoveil vendor last-good lab-GC cloud is a corridor witness, not the polisher SoT. Invented plant; simulated campaign. Not SPR cyanide (r26), not Raman OH-CH (r40), not QEPAS (r19), not LIBS (r19/r21/r22), not CRDS (r15), not TDLAS (r22), not chemiluminescence NOx (r52), not TEOM PM (r46).",
            "observables_at_decision": {
                "I_uv": i_uv,
                "I_bg": i_bg,
                "I_ref": i_ref,
                "k_f": k_f,
                "C_ppm": c_ppm,
                "R": ratio,
                "fluoveil_ppm": 4.80,
                "oiw_snr": 16.0,
                "isolate_floor_ppm": 20.00,
            },
            "margin_authority": "RF-9 polisher SOP rev A: if reconstructed C_ppm >= 20.00 AND OIW SNR >= 12.0, polisher P-3 may be isolated as a passing-valve leak. Dump-trip if C_ppm >= 80.00. P-1 and P-2 skip-isolate is a different gate. Fluoveil last-good cannot skip an unmeasured polisher.",
        },
        "proposed_action": {
            "actor": "water lead Oren Pike, citing Fluoveil 4.80 ppm and a late morning survey",
            "summary": "stamp P-3 in band and skip P-1 and P-2; 14.00 is a lamp glitch on a healthy lab-GC",
            "basis_claimed": "Fluoveil last-good is 4.80 ppm and a night survey of P-1 and P-2 is a takt miss",
        },
        "safety_decision": {
            "decision": "ACCEPT",
            "rationale": "Polisher P-3 is accepted as in-band for a single isolate. Serialized reconstruction: C_ppm = k_f * (I - I_bg) / I_ref = 4.00 * (14.00 - 2.00) / 2.00 = 24.00, which is 4.00 ppm above the 20.00 isolate floor and 56.00 ppm under the 80.00 dump-trip. Ratio identity (I - I_bg) / I_ref = 12.00 / 2.00 = 6.00. Fluoveil 4.80 ppm is a patched 6.00 residual and is not an admissible skip-isolate witness. Ordered: ACCEPT this P-3 isolate only. Scope: this ACCEPT does not skip P-1 and P-2 (that is the companion question) and does not stamp a dump trip.",
            "threshold": "C_ppm>=20.00 AND oiw_snr>=12.0 => accept P-3 isolate; Fluoveil is not SoT; dump-trip if C_ppm>=80.00; P-1 and P-2 are out of scope",
            "stated_residuals": "24.00 vs 20.00 isolate floor is 4.00 ppm, not infinite; P-1 and P-2 remain unmeasured; Fluoveil remains the only OEM lab-GC channel",
        },
        "executed_action": {
            "summary": "ACCEPT at t_s 5400: P-3 in band; P-1 and P-2 not skipped; Fluoveil not SoT; reconstruction locked",
            "tool": "rf9-oiw-pol-gate-cli",
            "observation": "C 24.00 ppm recomputes from I 14.00 and I_ref 2.00; OIW-SIM-2 hashed; Fluoveil channel not used as SoT",
        },
        "future_outcome": {
            "timeline": [
                {"t_s": 3000.0, "event": "oiw I 14.00; raster frame; C 24.00 ppm"},
                {"t_s": 4800.0, "event": "ops proposes accept P-3 and skip P-1/P-2"},
                {"t_s": 5400.0, "event": "ACCEPT P-3 only; P-1 and P-2 out of scope"},
                {"t_s": 6000.0, "event": "12 min survey-complete bookend 1"},
                {"t_s": 6720.0, "event": "12.0 min floor"},
                {"t_s": 7800.0, "event": "companion REJECT skip-isolate of P-1 and P-2"},
            ],
            "observed_effects": [
                "C recomputes from the serialized UV-fluorescence model at every recon.C event",
                "a Fluoveil-only head would have skipped P-1 and P-2 overnight",
                "12 min survey-complete floor is in the stream (surv.start, surv.floor)",
            ],
            "surprises": [
                "a last-good 4.80 ppm vendor lab-GC corridor co-existed with a 24.00 ppm plant reconstruction on P-3 only",
            ],
            "new_state": {
                "p3": "isolated",
                "p12": "in scope unskipped",
                "fluoveil": "not SoT",
                "reconstruction_model": "discharged as an on-record calculator",
            },
            "latency_ms": 2400000.0,
        },
        "reward_components": reward(
            0.41,
            [
                ("oiw_reconstruction", 0.14),
                ("bounded_p3_isolate", 0.12),
                ("fluoveil_nonsubstitution", 0.10),
                ("polisher_scope_limit", 0.08),
                ("survey_time_cost", -0.03),
            ],
            "scored for a bounded P-3 ACCEPT on a recomputable UV-fluorescence oil-in-water while refusing a Fluoveil 4.80 ppm corridor as a skip license; 12 min floor is priced as downtime",
        ),
        "meta": meta_common(
            tags=["ACCEPT", "uv-fluorescence-oiw", "serialized-reconstruction", "operational-companion"],
            distillation_note="UV-fluorescence OIW gate: serialized k_f*(I-I_bg)/I_ref plus ratio identity beats a green lab-GC dashboard; companion t2 is the skip-polisher refusal, not a second ppm vote",
        ),
    }
    traj2 = {
        "id": "nelb-r56-171-t2",
        "state": {
            "sim_or_real": "simulated",
            "episode_id": "RF-OIW-2026-0819-exec",
            "domain": "skip_polisher_refusal_execution",
            "setting": "Same RF-9 after the ACCEPT. Water lead proposes skipping P-1 and P-2 on Fluoveil 4.80 ppm. This companion is the operational skip refusal, not a second oil-in-water vote.",
            "observables_at_decision": {
                "C_ppm": 20.00,
                "surv_floor_s": 720.0,
                "skip_proposed": True,
            },
        },
        "proposed_action": {
            "actor": "water lead Oren Pike",
            "summary": "skip P-1 and P-2; 12 min already paid and Fluoveil is 4.80 ppm",
            "basis_claimed": "the ACCEPT already isolated P-3, so skipping the adjacent polishers is the cheapest survey",
        },
        "safety_decision": {
            "decision": "REJECT",
            "rationale": "Skip-isolate of P-1 and P-2 is refused. The 12 min survey floor is complete and the isolate tripwire (C_ppm >= 20.00) is still armed on the plant UV-fluorescence head. REJECT the skip. Do not trip the dump. P-3 hold stands. 20.00 ppm post-accept is still at the 20.00 isolate floor, so P-3 stays held; P-1 and P-2 remain unmeasured and in scope.",
            "threshold": "surv_floor_complete AND skip_not_taken AND dump_not_tripped AND p3_held AND p12_in_scope",
        },
        "executed_action": {
            "summary": "skip refused at t_s 7800; P-1 and P-2 not skipped; dump not tripped; P-3 held",
            "tool": "rf9-oiw-surv-exec",
            "observation": "recon.C 20.00 ppm on OIW-SIM-2; Fluoveil still ignored; P-1 and P-2 remain in the survey",
        },
        "future_outcome": {
            "timeline": [
                {"t_s": 6000.0, "event": "survey clock started after ACCEPT"},
                {"t_s": 6720.0, "event": "12.0 min floor"},
                {"t_s": 7200.0, "event": "P-1/P-2 skip re-proposed"},
                {"t_s": 7800.0, "event": "REJECT skip-isolate; P-3 hold stands"},
            ],
            "observed_effects": [
                "Fluoveil restore did not reopen the oil-in-water call",
                "dump trip never fired; 24.00 vs 80.00 ppm floor",
                "P-1 and P-2 remain unskipped; P-3 is the only isolated polisher",
            ],
            "new_state": {"p3": "held", "p12": "in survey", "dump": "in service"},
            "latency_ms": 1800000.0,
        },
        "reward_components": reward(
            0.36,
            [
                ("skip_polisher_refusal", 0.14),
                ("p3_hold_stands", 0.10),
                ("fluoveil_nonsubstitution", 0.08),
                ("survey_floor_complete", 0.06),
                ("takt_cost", -0.02),
            ],
            "operational execution gate: refuse skip of unmeasured polishers because Fluoveil is not a skip license; not an oil-in-water re-vote",
        ),
        "meta": meta_common(tags=["REJECT", "operational-execution", "skip-refusal"]),
    }
    return {
        "id": "nelb-r56-171",
        "spike_events": events,
        "language_view": {
            "description": "Rushfen Produced-Water RF-9. Simulated UV fluorescence reconstructs 24.00 ppm oil-in-water from 14.00 / 2.00 while Fluoveil still reports 4.80 ppm. The gate ACCEPTs a P-3 isolate only. A 12 min survey floor is serialized in the stream. Companion t2 REJECTs skipping P-1 and P-2.",
            "trajectory": traj,
            "trajectory_skip_polisher_refusal": traj2,
        },
        "bridge_notes": {
            "channel_map": {
                "oiw.I / oiw.Iref / oiw.snr": "UV sample intensity, reference photodiode, and SNR; the physics channels the reconstruction consumes",
                "recon.C / recon.R": "serialized oil-in-water ppm and intensity-ratio identity",
                "fluoveil.C / pol.id / p12.present": "vendor last-good lab-GC, polisher id, and adjacent-polisher presence; the denial and scope channels",
                "ops.prop / gate.comp / ops.skip / gate.hold": "accept-and-skip proposal, ACCEPT, skip proposal, companion REJECT",
                "surv.start / surv.floor / p3.held / p12.skip / dump.trip / pol.held / takt.late": "operational companion channels plus the 12 min floor",
            },
            "temporal_motifs": [
                "vendor-green while plant-over: fluoveil.C 4.80 next to recon.C 24.00",
                "reconstruction as event: recon.C 24.00 equals 4.00*(14.00-2.00)/2.00",
                "ACCEPT then operational REJECT: gate.comp at 5400 s, gate.hold at 7800 s",
                "slow floor in-stream: surv.start 6000 s, surv.floor 6720 s (12.0 min)",
                "tight oiw pair: oiw.I then oiw.Iref +1.5 ms at the raster frame",
            ],
            "language_to_spike_mapping": "'Fluoveil is 4.80 ppm' = fluoveil.C 4.80; '24 ppm oil' = recon.C 24.00; 'accept P-3 only' = gate.comp ACCEPT; 'do not skip P-1/P-2' = gate.hold REJECT",
            "why_high_value": "New UV-fluorescence oil-in-water family on a produced-water polisher (not SPR r26, not Raman r40, not QEPAS r19, not LIBS r19/r21/r22, not CRDS r15, not TDLAS r22, not chemiluminescence NOx r52, not TEOM r46). Lead bounded ACCEPT of P-3 isolate on a recomputable oil load that a vendor lab-GC last-good would have used to skip adjacent polishers. Companion t2 is operational skip refusal. sim_or_real=simulated.",
            "encoder_spec": {
                "prng": "MT19937 via python random.Random",
                "seeds": {"raster": 202609171, "stream_note": "stream amplitudes are authored constants (1, ppm, bool)"},
                "draw_order": "raster: per neuron id order, gap-constrained times, per-spike adaptation and noise",
                "thinning": "UV fluorescence exists at ~1 Hz; stream keeps 4 I points; recon keeps 4 of ~20 solver ticks",
                "refractory_floors_ms": {
                    "oiw.I": 1.5,
                    "oiw.Iref": 1.5,
                    "oiw.snr": 1.5,
                    "recon.C": 60000,
                    "recon.R": 60000,
                    "fluoveil.C": 60000,
                    "pol.id": 60000,
                    "p12.present": 60000,
                    "ops.prop": 60000,
                    "gate.comp": 60000,
                    "surv.start": 60000,
                    "surv.floor": 60000,
                    "ops.skip": 60000,
                    "gate.hold": 60000,
                    "p3.held": 60000,
                    "p12.skip": 60000,
                    "dump.trip": 60000,
                    "pol.held": 60000,
                    "takt.late": 60000,
                },
                "time_alias": "t_rel_ms; t0 = 2026-08-19T03:00:00Z simulated night start",
            },
            "distillation_targets": [
                "UV-fluorescence reconstruction head: C_ppm = k_f * (I - I_bg) / I_ref; R = (I - I_bg) / I_ref",
                "bounded ACCEPT head: in-band C AND polisher scope AND p12-out-of-scope",
                "operational companion: refuse skip-isolate without re-opening the lab-GC call",
            ],
        },
        "reconstruction_model": {
            "name": "uv_fluorescence_oil_in_water",
            "formula": "C_ppm = k_f * (I_uv - I_bg) / I_ref; R = (I_uv - I_bg) / I_ref",
            "parameters": {
                "k_f": 4.00,
                "I_bg": 2.00,
                "I_ref": 2.00,
                "isolate_floor_ppm": 20.00,
                "dump_trip_ppm": 80.00,
                "surv_min": 12.0,
            },
            "worked_example": {"I_uv": 14.00, "C_ppm": 24.00, "R": 6.00},
            "check": "4.00 * (14.00 - 2.00) / 2.00 = 24.00 exactly; (14.00 - 2.00) / 2.00 = 6.00 exactly; 6000 s + 720 s = 6720 s = 12.0 min floor",
        },
        "raster": raster,
        "gate_snn": {
            "decision": "ACCEPT",
            "decision_window_ms": 36.0,
            "decision_window_s": 0.036,
            "code": "rf9.oiw_pol_gate",
            "note": "ACCEPT accumulator wins: UV-fluorescence oil-in-water evidence overpowers the Fluoveil skip advocate",
            "decode_rule": "accept if ppm_estimator AND ref_norm AND polisher_margin fire inside the window; vendor_skip_advocate is necessary-but-not-sufficient and cannot release P-1 and P-2",
            "populations": [
                gate_pop("ppm_estimator", 80, 1.5, 50.0, w_s),
                gate_pop("ref_norm", 64, 1.2, 31.25, w_s),
                gate_pop("polisher_margin", 40, 1.0, 50.0, w_s),
                gate_pop("vendor_skip_advocate", 32, 0.7, 25.0, w_s),
                gate_pop("accept_latch", 96, 1.8, 62.5, w_s),
            ],
        },
        "gate_compute": gate_compute(
            [
                {"check": "rf9.oiw_scorer", "neurons": 80, "mean_rate_hz": 50.0, "window_ms": 36.0},
                {"check": "rf9.ppm_scorer", "neurons": 40, "mean_rate_hz": 62.5, "window_ms": 32.0},
            ]
        ),
        "meta": meta_common(
            id="nelb-r56-171",
            clock_domain="rf9-oiw-sim-relative-ms-t0-2026-08-19T03:00:00Z",
            tags=["uv-fluorescence-oiw", "ACCEPT", "REJECT", "serialized-reconstruction", "operational-t2"],
        ),
    }
