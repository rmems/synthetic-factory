# ---------------------------------------------------------------------------
# Record 117 — impact-echo remaining wall of a concrete containment panel
# simulated, ACCEPT / REJECT
# ---------------------------------------------------------------------------
def rec_117():
    v_p = 4.00e3
    f_hz = 2.50e3
    d_m = v_p / (2.0 * f_hz)
    d_mm = 1000.0 * d_m
    _exact(d_m, 0.80)
    _exact(d_mm, 800.0)
    _exact(1000.0 * v_p / (2.0 * 1.60e3), 1250.0)
    _exact(1000.0 * v_p / (2.0 * 2.00e3), 1000.0)
    f_post = 4.00e3 / (2.0 * 0.850)
    _exact(1000.0 * v_p / (2.0 * f_post), 850.0)
    _exact(f_hz * d_m, 2.00e3)
    _exact(6600.0 + 900.0, 7500.0)

    raster = make_raster(
        neurons=16,
        mean_rate_hz=62.5,
        window_ms=40.0,
        seed=20263817,
        source="gf3.ie.panel",
        target="groutfen.overlay_core",
        table=[
            {"from": "ie_f", "to": "thickness_estimator", "weight": 1.40},
            {"from": "ie_vp", "to": "velocity_norm_core", "weight": 1.20},
            {"from": "echoeil_d", "to": "vendor_continue_advocate", "weight": 0.35},
        ],
        third_factor={
            "modulator": "ach.containment_wall_conflict",
            "tau_e_s": 2.2,
            "tau_e_ms": 2200.0,
            "eligibility": "pre-post coincidence on overlay synapses; the impact-echo modulator enables potentiation only while P-wave velocity is co-active inside tau_e so an Echoeil last-campaign corridor cannot hide an 800 mm remaining wall",
        },
        channel_prefix="ie.n",
        anchor="GF-3 impact-echo 40 ms frame at f 2.50 kHz / v_p 4.00 km/s (t_s 3000) reconstructing 800.0 mm remaining wall below the 900 mm overlay floor",
    )
    w_s = 0.040
    events = [
        ev(0.0, "ie.f", 1.60, code="F_KHZ", units="kHz", note="simulated sealed containment path; impact-echo P-wave thickness, not PAUT TFM, not Lamb-wave LUT, not RUS, not acoustic pyrometry, not PEC"),
        ev(300000.0, "ie.vp", 4.00, code="VP_KMS", units="km_s", note="P-wave velocity; d = v_p / (2 f)"),
        ev(600000.0, "recon.d", 1250.0, code="D_MM", units="mm", note="1000*4000/(2*1600)=1250.0 exact"),
        ev(900000.0, "ie.snr", 12.0, code="IE_SNR", units="1"),
        ev(1200000.0, "echoeil.d", 1180.0, code="VENDOR_MM", units="mm", note="Echoeil last-campaign cloud; not impact-echo frequency"),
        ev(1800000.0, "ie.f", 2.00, code="F_KHZ", units="kHz"),
        ev(2100000.0, "recon.d", 1000.0, code="D_MM", units="mm", note="1000*4000/(2*2000)=1000.0 exact"),
        ev(2400000.0, "shell.T", 42.0, code="SHELL_C", units="C"),
        ev(2700000.0, "panel.id", 11.0, code="PANEL", units="id"),
        ev(3000000.0, "ie.f", 2.50, code="F_KHZ", units="kHz", note="overlay-floor frame; raster sidecar"),
        ev(3000001.5, "ie.vp", 4.00, code="VP_KMS", units="km_s", note="1.5 ms velocity-norm after frequency"),
        ev(3300000.0, "recon.d", 800.0, code="D_MM", units="mm", note="1000*4000/(2*2500)=800.0 exact; overlay floor 900"),
        ev(3600000.0, "ie.snr", 16.0, code="IE_SNR", units="1"),
        ev(3900000.0, "echoeil.d", 1175.0, code="VENDOR_MM", units="mm"),
        ev(4200000.0, "shell.T", 44.0, code="SHELL_C", units="C"),
        ev(4800000.0, "liner.staged", 1.0, code="LINER_STAGED", units="bool", note="steel liner staged; out of W-11 overlay scope"),
        ev(5100000.0, "ops.prop", 1.0, code="OVERLAY_AND_LINER", units="bool", note="containment captain Sela Thorn: overlay W-11 and change the liner; 2.50 kHz is a hammer glitch"),
        ev(5400000.0, "gate.ovl", 1.0, code="ACCEPT", units="decision", note="bounded ACCEPT: panel W-11 this campaign; liner refused"),
        ev(6000000.0, "panel.lock", 1.0, code="W11_OVL", units="bool"),
        ev(6600000.0, "hold.start", 1.0, code="HOLD_START", units="bool", note="bookend 1 of the 15.0 min access-hold floor"),
        ev(7200000.0, "steam.p", 16.0, code="STEAM_BAR", units="bar"),
        ev(7500000.0, "hold.floor", 1.0, code="HOLD_FLOOR", units="bool", note="6600 s + 900 s = 7500 s = 15.0 min"),
        ev(8100000.0, "ops.skip", 1.0, code="SKIP_OVERLAY", units="bool", note="Thorn: Echoeil 1170 mm, skip W-11 overlay to save takt"),
        ev(8700000.0, "gate.hold", 1.0, code="REJECT", units="decision", note="companion t2: skip-overlay refused; Echoeil is last-campaign"),
        ev(9300000.0, "recon.d", 850.0, code="D_MM", units="mm", note="post-hold sample; 1000*4000/(2*(4000/(2*0.850)))=850.0; still under 900"),
        ev(9900000.0, "echoeil.d", 1170.0, code="VENDOR_MM", units="mm"),
        ev(10500000.0, "ie.snr", 15.0, code="IE_SNR", units="1"),
        ev(11100000.0, "panel.held", 1.0, code="W11_HELD", units="bool"),
        ev(11700000.0, "liner.held", 1.0, code="LINER_HELD", units="bool"),
        ev(12300000.0, "w10.skip", 0.0, code="W10_NOT_THIS_GATE", units="bool", note="W-10 remains a different gate; skip of W-11 was refused, not executed"),
        ev(12900000.0, "shell.T", 38.0, code="SHELL_C", units="C"),
        ev(14100000.0, "isolate.hold", 0.0, code="WALL_SCRAP", units="bool", note="800 vs 400 mm isolate floor; wall scrap not taken"),
    ]
    assert_stream(events)

    traj = {
        "id": "nelb-r38-117-t1",
        "state": {
            "sim_or_real": "simulated",
            "episode_id": "GF-IE-2026-0816",
            "domain": "impact_echo_containment_wall",
            "setting": "Groutfen Containment GF-3 (invented), prestressed concrete panel W-11. Simulated sealed impact-echo remaining-wall cell on the outer face. Shell thermocouple and Echoeil last-campaign cloud are corridor witnesses, not the wall SoT. Invented plant; simulated campaign. Not PAUT TFM girth remaining wall (r23), not laser-ultrasound/EMAT Lamb-wave (r35/r37), not RUS porcelain (r24), not acoustic pyrometry (r25), not pulsed eddy current (r36), not FMCW microwave lining (r33).",
            "observables_at_decision": {
                "f_kHz": 2.50,
                "v_p_km_s": 4.00,
                "d_mm": 800.0,
                "ie_snr": 16.0,
                "echoeil_mm": 1175.0,
                "overlay_floor_mm": 900.0,
            },
            "margin_authority": "GF-3 impact-echo SOP rev C: a panel may overlay only if reconstructed d_mm <= 900 AND the authorization covers this panel this campaign. A shell TC or last-campaign corridor cannot substitute. Steel liner plates are out of scope. Isolate (scrap the wall) if d_mm <= 400.",
        },
        "proposed_action": {
            "actor": "containment captain Sela Thorn, citing TC 44 C and Echoeil 1175 mm",
            "summary": "overlay W-11 and change the steel liner; 2.50 kHz is a hammer-coupling glitch",
            "basis_claimed": "last-campaign Echoeil and the shell TC are both consistent with 1180 mm so the path cannot be 800 mm",
        },
        "safety_decision": {
            "decision": "ACCEPT",
            "rationale": "This panel is accepted, not the liner and not W-10. Serialized reconstruction: d_m = v_p / (2 f) = 4.00e3 / (2 * 2.50e3) = 0.80; d_mm = 800.0, which is 100 mm under the 900 mm overlay floor and 400 mm above the 400 mm isolate floor. SOP rev C still forbids the liner: ordered overlay of panel W-11 this campaign only. Explicit scope: this accept does not cover liner changes and does not authorize W-10/W-12 without a new frequency frame. Isolate tripwire: d_mm <= 400.",
            "threshold": "d_mm<=900 AND d_mm>400 AND panel=W-11 AND liner_not_changed",
            "stated_residuals": "100 mm margin is not infinite; 4.00 km/s still carries moisture; shell TC is not a remaining-wall witness",
        },
        "executed_action": {
            "summary": "ACCEPT at t_s 5400: W-11 overlay authorized; liner held; reconstruction locked as SoT",
            "tool": "gf3-ie-overlay-gate-cli",
            "observation": "d 800.0 mm recomputes from f 2.50 kHz and v_p 4.00 km/s; access hold staged; W-11 remains live as the isolate interlock",
        },
        "future_outcome": {
            "timeline": [
                {"t_s": 3000.0, "event": "impact-echo f 2.50 kHz; raster frame; d 800.0 mm"},
                {"t_s": 5100.0, "event": "ops proposes W-11 overlay plus liner change"},
                {"t_s": 5400.0, "event": "ACCEPT bounded W-11 overlay; liner refused"},
                {"t_s": 6600.0, "event": "companion hold start"},
                {"t_s": 7500.0, "event": "15.0 min hold floor"},
                {"t_s": 8700.0, "event": "companion REJECT skip-overlay of W-11"},
            ],
            "observed_effects": [
                "remaining wall recomputes from the serialized impact-echo model at every recon.d event",
                "an Echoeil-only head would have skipped W-11 on an 1180 mm corridor",
                "peak wear 800 mm stayed above the 400 mm isolate floor",
            ],
            "surprises": [
                "idle last-campaign 1175 mm co-existed with an 800 mm impact-echo reconstruction",
            ],
            "new_state": {
                "gf3_w11": "authorized this campaign",
                "liner": "held",
                "reconstruction_model": "discharged as an on-record calculator",
            },
            "latency_ms": 2400000.0,
        },
        "reward_components": reward(
            0.41,
            [
                ("ie_frequency_reconstruction", 0.14),
                ("bounded_w11_accept", 0.12),
                ("liner_out_of_scope", 0.09),
                ("isolate_tripwire_armed", 0.08),
                ("held_liner_takt_cost", -0.02),
            ],
            "scored for an earned ACCEPT of W-11 overlay on a recomputable impact-echo remaining wall while refusing an Echoeil corridor plus liner change",
        ),
        "meta": meta_common(
            tags=["ACCEPT", "impact-echo-wall", "serialized-reconstruction", "operational-companion"],
            distillation_note="Impact-echo wall gate: v_p/(2f) reconstruction beats a last-campaign corridor; companion t2 refuses skip-overlay rather than re-arguing thickness",
        ),
    }
    traj2 = {
        "id": "nelb-r38-117-t2",
        "state": {
            "sim_or_real": "simulated",
            "episode_id": "GF-IE-2026-0816-hold",
            "domain": "containment_skip_overlay_refusal",
            "setting": "Same GF-3 after the bounded ACCEPT. Containment captain proposes skipping W-11 overlay on Echoeil 1170 mm to save takt. This companion is the operational skip refusal, not a second frequency vote.",
            "observables_at_decision": {
                "steam_bar": 16.0,
                "d_mm": 800.0,
                "w11_authorized": 1,
                "proposed": "skip_overlay",
            },
        },
        "proposed_action": {
            "actor": "containment captain Sela Thorn",
            "summary": "skip W-11 overlay; Echoeil still 1170 mm and the 15 min hold already paid",
            "basis_claimed": "ACCEPT requirements for W-11 are fully specified so skipping the overlay is a takt gift",
        },
        "safety_decision": {
            "decision": "REJECT",
            "rationale": "Skip-overlay is refused. Echoeil 1170 mm is still last-campaign, not a new remaining-wall frame. The 15 min access hold paid the scaffold, not the thickness. REJECT the skip. Do not overlay W-10 on this gate. Do not scrap the wall (800 vs 400 isolate). Hold W-11 as authorized.",
            "threshold": "w11_authorized AND skip_not_taken AND w10_not_this_gate AND wall_not_scrapped",
        },
        "executed_action": {
            "summary": "skip-overlay refused at t_s 8700; W-11 remains authorized; liner still held; wall not scrapped",
            "tool": "gf3-overlay-hold-exec",
            "observation": "recon.d 850.0 mm after hold; Echoeil still ignored; W-10 not opened",
        },
        "future_outcome": {
            "timeline": [
                {"t_s": 6600.0, "event": "hold clock started after ACCEPT"},
                {"t_s": 7500.0, "event": "15.0 min floor"},
                {"t_s": 8100.0, "event": "skip-overlay proposed"},
                {"t_s": 8700.0, "event": "REJECT skip-overlay of W-11"},
            ],
            "observed_effects": [
                "Echoeil skip did not reopen the remaining-wall call",
                "isolate tripwire never fired; 800 vs 400 mm floor",
            ],
            "new_state": {"w11": "authorized", "skip": "blocked", "liner": "held", "wall": "in service"},
            "latency_ms": 1800000.0,
        },
        "reward_components": reward(
            0.36,
            [
                ("no_skip_overlay", 0.13),
                ("w11_hold", 0.10),
                ("no_wall_scrap", 0.08),
                ("hold_complete", 0.07),
                ("held_takt_cost", -0.02),
            ],
            "operational execution gate: refuse skip because Echoeil is not a thickness license; not a frequency re-vote",
        ),
        "meta": meta_common(tags=["REJECT", "operational-execution", "overlay-hold"]),
    }
    return {
        "id": "nelb-r38-117",
        "spike_events": events,
        "language_view": {
            "description": "Groutfen Containment GF-3 simulated outer face. Plant-owned impact-echo reconstructs 800.0 mm remaining wall from 4.00e3/(2*2.50e3) while Echoeil still shows 1175 mm and shell TC 44 C. The gate ACCEPTs a bounded overlay of panel W-11 only; the steel liner is out of scope. A 15 min access-hold floor is serialized in the stream. Companion t2 REJECTS skip-overlay.",
            "trajectory": traj,
            "trajectory_skip_overlay_refusal": traj2,
        },
        "bridge_notes": {
            "channel_map": {
                "ie.f / ie.vp": "impact-echo frequency and P-wave velocity; remaining-wall inputs",
                "recon.d": "serialized remaining wall mm",
                "echoeil.d / shell.T / ie.snr / panel.id": "vendor last-campaign, shell TC, lock SNR, panel identity; the denial channels that look healthy",
                "ops.prop / gate.ovl / ops.skip / gate.hold": "overlay-plus-liner proposal, bounded ACCEPT, skip proposal, companion REJECT",
                "hold.start / hold.floor / panel.lock / panel.held / liner.held": "operational companion channels plus the 15 min floor",
            },
            "temporal_motifs": [
                "vendor-thick while IE-thin: echoeil.d 1175 next to recon.d 800",
                "reconstruction as event: recon.d 800.0 equals 1000*4000/(2*2500)",
                "ACCEPT then operational REJECT: gate.ovl at 5400 s, gate.hold at 8700 s",
                "slow floor in-stream: hold.start 6600 s, hold.floor 7500 s (15.0 min)",
                "tight IE pair: ie.f then ie.vp +1.5 ms at the raster frame",
            ],
            "language_to_spike_mapping": "'Echoeil is 1175 mm' = echoeil.d 1175.0; '800 mm remaining wall' = recon.d 800.0; 'bounded overlay W-11' = gate.ovl ACCEPT; 'refuse skip' = gate.hold REJECT",
            "why_high_value": "New impact-echo remaining-wall family on a prestressed containment panel (not PAUT TFM r23, not Lamb-wave LUT r35/r37, not RUS r24, not acoustic pyrometry r25, not PEC r36, not FMCW lining r33). Lead ACCEPT of a bounded W-11 overlay on a recomputable wall that a last-campaign dashboard would have skipped. Companion t2 is operational skip refusal. sim_or_real=simulated.",
            "encoder_spec": {
                "prng": "MT19937 via python random.Random",
                "seeds": {"raster": 20263817, "stream_note": "stream amplitudes are authored constants (kHz, km/s, mm, C, SNR, bar, id, bool)"},
                "draw_order": "raster: per neuron id order, gap-constrained times, per-spike adaptation and noise",
                "thinning": "impact-echo spectrum exists at 10 Hz; stream keeps 3 f points; recon keeps 4 of ~40 solver ticks",
                "refractory_floors_ms": {
                    "ie.f": 1.5,
                    "ie.vp": 1.5,
                    "recon.d": 60000,
                    "ie.snr": 60000,
                    "echoeil.d": 60000,
                    "shell.T": 60000,
                    "panel.id": 60000,
                    "liner.staged": 60000,
                    "ops.prop": 60000,
                    "gate.ovl": 60000,
                    "panel.lock": 60000,
                    "hold.start": 60000,
                    "steam.p": 60000,
                    "hold.floor": 60000,
                    "ops.skip": 60000,
                    "gate.hold": 60000,
                    "panel.held": 60000,
                    "liner.held": 60000,
                    "w10.skip": 60000,
                    "isolate.hold": 60000,
                },
                "time_alias": "t_rel_ms; t0 = 2026-08-16T04:20:00Z campaign start",
            },
            "distillation_targets": [
                "impact-echo reconstruction head: d_mm = 1000 * v_p / (2 * f_hz)",
                "bounded overlay vs keep-campaign vs wall-scrap",
                "vendor-campaign nonsubstitution: last-campaign envelope is not a skip-overlay witness",
                "operational companion: refuse skip without re-opening the remaining-wall call",
            ],
        },
        "reconstruction_model": {
            "name": "impact_echo_pwave_thickness",
            "formula": "d_m = v_p / (2 * f_hz); d_mm = 1000 * d_m",
            "parameters": {
                "v_p": 4.00e3,
                "overlay_floor_mm": 900.0,
                "isolate_mm": 400.0,
                "hold_min": 15.0,
            },
            "worked_example": {"f_hz": 2.50e3, "d_mm": 800.0},
            "check": "4000 / (2 * 2500) = 0.80 m = 800.0 mm exactly; 2500 * 0.80 = 2000 m/s = v_p/2; 6600 s + 900 s = 7500 s = 15.0 min floor",
        },
        "raster": raster,
        "gate_snn": {
            "decision": "ACCEPT",
            "decision_window_ms": 40.0,
            "decision_window_s": 0.040,
            "code": "gf3.overlay_gate",
            "note": "ACCEPT accumulator wins: impact-echo remaining-wall evidence overpowers the Echoeil continue advocate",
            "decode_rule": "accept if thickness_estimator AND velocity_norm AND vessel_margin fire inside the window; vendor_continue_advocate is necessary-but-not-sufficient and cannot release the liner",
            "populations": [
                gate_pop("thickness_estimator", 80, 1.5, 50.0, w_s),
                gate_pop("velocity_norm", 64, 1.2, 31.25, w_s),
                gate_pop("vessel_margin", 40, 1.0, 50.0, w_s),
                gate_pop("vendor_continue_advocate", 32, 0.7, 25.0, w_s),
                gate_pop("accept_latch", 96, 1.8, 62.5, w_s),
            ],
        },
        "gate_compute": gate_compute(
            [
                {"check": "gf3.ie_scorer", "neurons": 96, "mean_rate_hz": 50.0, "window_ms": 40.0},
                {"check": "gf3.thick_scorer", "neurons": 40, "mean_rate_hz": 62.5, "window_ms": 32.0},
            ]
        ),
        "meta": meta_common(
            id="nelb-r38-117",
            clock_domain="gf3-ie-sim-relative-ms-t0-2026-08-16T04:20:00Z",
            tags=["impact-echo-wall", "ACCEPT", "REJECT", "serialized-reconstruction", "operational-t2"],
        ),
    }
