# ---------------------------------------------------------------------------
# Record 070 — lock-in thermography CFRP bonded repair, designed, MODIFY / ACCEPT
# ---------------------------------------------------------------------------
def rec_070():
    import math
    assert abs(3.00 / math.sqrt(0.36) - 5.00) < 1e-12
    assert abs(12.50 / 2.50 - 5.00) < 1e-12
    raster = make_raster(
        neurons=20,
        mean_rate_hz=50.0,
        window_ms=36.0,
        seed=20260970,
        source="hr6.wold.lockin",
        target="heckfen.disbond_core",
        table=[
            {"from": "lit_f_hz", "to": "depth_reconstructor", "weight": 1.40},
            {"from": "amp_ratio", "to": "fault_identity_core", "weight": 1.15},
            {"from": "scada_strain", "to": "sortie_advocate", "weight": 0.50},
        ],
        third_factor={
            "modulator": "na.disbond_salience",
            "tau_e_s": 1.6,
            "tau_e_ms": 1600.0,
            "eligibility": "pre-post coincidence on disbond synapses; the thermal-wave modulator enables potentiation only while amp-ratio and lock-in phase are co-active inside tau_e",
        },
        channel_prefix="lit.n",
        anchor="HR-6 Wold-Lock 36 ms frame at f 0.36 Hz / A 12.50 mK (t_s 7200); reconstructed depth 5.00 mm first exceeds the 4.00 mm trip",
    )
    w_s = 0.036
    events = [
        ev(0.0, "scada.eps", 180.0, code="BLADE_STRAIN", units="ue", note="HR-6 spar strain SCADA; alarm 400 ue"),
        ev(6.0e5, "sortie.pct", 100.0, code="NR_PCT", units="pct", note="Gull-B12 night-training sortie still armed"),
        ev(1.2e6, "lit.f", 1.00, code="F_HZ", units="Hz", note="Wold-Lock 16-pixel lock-in thermography, 3.8 um camera"),
        ev(1.8e6, "recon.d", 3.00, code="DEPTH_MM", units="mm", note="3.00/sqrt(1.00) = 3.00 exact"),
        ev(2.4e6, "lit.A", 4.80, code="A_MK", units="mK"),
        ev(3.0e6, "amp.ratio", 1.92, code="AMP_RATIO", units="ratio", note="4.80/2.50 = 1.92"),
        ev(3.6e6, "coh.pix", 0.25, code="COHERENCE", units="ratio", note="4 of 16 pixels hot"),
        ev(4.8e6, "lit.f", 0.64, code="F_HZ", units="Hz"),
        ev(5.4e6, "recon.d", 3.75, code="DEPTH_MM", units="mm", note="3.00/sqrt(0.64) = 3.75"),
        ev(6.0e6, "scada.eps", 176.0, code="BLADE_STRAIN", units="ue"),
        ev(7.2e6, "lit.A", 12.50, code="A_MK", units="mK", note="authorization frame; raster sidecar"),
        ev(7200001.2, "lit.A", 10.25, code="A_MK", units="mK", note="same-channel refractory 1.2 ms; amplitude adapted 0.82x plus noise"),
        ev(7200002.6, "lit.A", 8.40, code="A_MK", units="mK", note="third lock-in packet; adapted"),
        ev(7.32e6, "lit.f", 0.36, code="F_HZ", units="Hz"),
        ev(7.44e6, "recon.d", 5.00, code="DEPTH_MM", units="mm", note="3.00/sqrt(0.36) = 5.00 exact; tripwire 4.00 mm"),
        ev(7.56e6, "amp.ratio", 5.00, code="AMP_RATIO", units="ratio", note="12.50/2.50 = 5.00 exact"),
        ev(7.68e6, "coh.pix", 0.62, code="COHERENCE", units="ratio", note="10 of 16 pixels hot"),
        ev(8.4e6, "scada.eps", 180.0, code="STILL_UNDER_ALARM", units="ue", note="ops reads spar strain as healthy; the denial channel"),
        ev(9.0e6, "sortie.pct", 100.0, code="STILL_ARMED", units="pct"),
        ev(9.6e6, "ops.prop", 1.0, code="KEEP_SORTIE", units="bool", note="night NDT Lina Wold: fly the 6 h training; pixel-12 is a lamp reflection"),
        ev(9.72e6, "gate.lit", 1.0, code="MODIFY", units="decision", note="abort sortie, isolate Gull-B12, 40 percent ground-turn only"),
        ev(9.84e6, "abort.cmd", 1.0, code="ABORT", units="bool"),
        ev(10.8e6, "isol.blade", 1.0, code="BLADE_ISOLATED", units="bool"),
        ev(12.0e6, "recon.d", 5.00, code="DEPTH_MM", units="mm"),
        ev(13.2e6, "lit.A", 12.40, code="A_MK", units="mK"),
        ev(14.4e6, "ground.pct", 40.0, code="GROUND_PCT", units="pct", note="companion restore cap 40 percent ground-turn; flight not re-armed"),
        ev(15.72e6, "coh.pix", 0.58, code="COHERENCE", units="ratio"),
        ev(16.8e6, "amp.ratio", 4.96, code="AMP_RATIO", units="ratio"),
        ev(16.92e6, "gate.exec", 1.0, code="ACCEPT", units="decision", note="companion t2: abort/isolate sequence completed"),
        ev(18.0e6, "sortie.pct", 0.0, code="SORTIE_HELD", units="pct"),
        ev(18.6e6, "scada.eps", 92.0, code="BLADE_STRAIN", units="ue"),
        ev(19.2e6, "isol.blade", 1.0, code="BLADE_HELD", units="bool"),
    ]
    assert_stream(events)

    traj = {
        "id": "nelb-r23-070-t1",
        "state": {
            "sim_or_real": "designed",
            "episode_id": "HR-LIT-2026-0412",
            "domain": "lockin_thermography_cfrp_repair",
            "setting": "Heckfen Rotorcraft HR-6 (invented), composite main-rotor blade Gull-B12 with a bonded scarf repair at 62 percent radius. Wold-Lock 16-pixel lock-in thermography (3.8 um, 0.1-2 Hz). Night training sortie armed. Invented plant; designed campaign. Not FBG glaze, not scanning/fiber LDV (r20 Mossgill Kaplan), not THz-TDS radome (r20/r21), not industrial x-ray DR.",
            "observables_at_decision": {
                "f_hz": 0.36,
                "A_mK": 12.50,
                "depth_mm": 5.00,
                "amp_ratio": 5.00,
                "coherence_pix": 0.62,
                "scada_ue": 180.0,
            },
            "margin_authority": "HR-6 blade SOP rev B: if reconstructed depth_mm >= 4.00 AND amp_ratio >= 3.00 AND pixel-coherence >= 0.50, flight-release is forbidden even if SCADA spar strain is under the 400 ue alarm",
        },
        "proposed_action": {
            "actor": "night NDT Lina Wold, citing spar strain under alarm and no rotor-track trip",
            "summary": "fly the 6 h Gull-B12 training sortie; treat pixel-12 rise as a lamp reflection on the lock-in head",
            "basis_claimed": "SCADA strain 180 ue is under 400; abort would cost the night syllabus",
        },
        "safety_decision": {
            "decision": "MODIFY",
            "rationale": "Flight-release is refused, not the airframe. SOP rev B is conjunctive: reconstructed thermal-wave depth is 5.00 mm (3.00 / sqrt(0.36), serialized) and amp_ratio is 5.00 (12.50 / 2.50) and pixel-coherence is 0.62, all over the 4.00 mm / 3.00 / 0.50 floors, while SCADA still reads 180 ue. Holding the sortie puts the scarf in a peel-growth regime. Ordered: abort the sortie, isolate Gull-B12, and cap ground-turn at 40 percent until a peel-test, not a strain corridor, clears the blade. Spar-strain agreement cannot substitute for the lock-in reconstruction.",
            "threshold": "depth_mm>=4.00 AND amp_ratio>=3.00 AND coherence>=0.50 => forbid flight-release",
            "stated_residuals": "night syllabus deferred; 1.00 Hz lock-in still exists and is not a release condition",
        },
        "executed_action": {
            "summary": "MODIFY at t_s 9720: sortie aborted, Gull-B12 isolated; depth stayed 5.00 mm (disbond does not self-heal on a ground-turn)",
            "tool": "hr6-lit-blade-gate-cli",
            "observation": "abort latched in 12 s; pixel-12 stayed 12.50->12.40 mK with 0.36 Hz still identified, consistent with a disbond not a lamp reflection",
        },
        "future_outcome": {
            "timeline": [
                {"t_s": 7200.0, "event": "LIT A 12.50 mK; raster frame captured"},
                {"t_s": 7440.0, "event": "depth 5.00 mm reconstructed; amp_ratio 5.00; coherence 0.62"},
                {"t_s": 9600.0, "event": "ops proposes keep-sortie"},
                {"t_s": 9720.0, "event": "MODIFY: abort plus isolate"},
                {"t_s": 16920.0, "event": "companion execution ACCEPT; ground-turn 40 percent; sortie held"},
            ],
            "observed_effects": [
                "reconstructed depth is recomputable from the serialized model at every recon.d event",
                "SCADA strain never left the alarm-free corridor, so a single-gauge head would have ACCEPTed",
                "amp_ratio and coherence jointly crossed SOP rev B 40 s before the proposal",
            ],
            "surprises": [
                "rotor-track and balance stayed quiet the entire preflight; 1/rev is not a substitute disbond detector on this blade",
            ],
            "new_state": {
                "hr6": "ground-turn 40 percent pending dawn peel-test",
                "gull_b12": "isolated",
                "reconstruction_model": "discharged as an on-record calculator, not a referenced envelope",
            },
            "latency_ms": 12000.0,
        },
        "reward_components": reward(
            0.41,
            [
                ("lit_depth_reconstruction", 0.14),
                ("conjunctive_sop_enforcement", 0.12),
                ("abort_plus_isolate", 0.10),
                ("strain_nonsubstitution", 0.08),
                ("syllabus_deferral_cost", -0.03),
            ],
            "scored for refusing flight-release on a recomputable lock-in depth while SCADA spar strain looked healthy; syllabus_deferral_cost prices the night sortie",
        ),
        "meta": meta_common(
            tags=["MODIFY", "lockin-thermography", "serialized-reconstruction", "operational-companion"],
            distillation_note="CFRP gate: serialized kappa/sqrt(f) depth plus amp-ratio beats a clean strain corridor; companion t2 is the abort execution, not a governance vote",
        ),
    }
    traj2 = {
        "id": "nelb-r23-070-t2",
        "state": {
            "sim_or_real": "designed",
            "episode_id": "HR-LIT-2026-0412-exec",
            "domain": "blade_abort_isolate_execution",
            "setting": "Same HR-6 after the MODIFY. This companion is the operational abort/isolate sequence, not a second policy vote.",
            "observables_at_decision": {
                "abort_cmd": 1,
                "depth_mm": 5.00,
                "blade_isolated": True,
            },
        },
        "proposed_action": {
            "actor": "rotor controller following the MODIFY",
            "summary": "execute sortie abort and Gull-B12 isolation, then cap ground-turn at 40 percent; do not re-arm flight",
            "basis_claimed": "MODIFY requirements are fully specified and in-envelope for the rotor brake",
        },
        "safety_decision": {
            "decision": "ACCEPT",
            "rationale": "The execution envelope is intact: rotor-brake torque is under the 120 percent ground limit, isolation interlock is confirmed, and the restore condition (peel-test, not strain) is the same conjunctive physics the MODIFY used. ACCEPT the sequence. Do not re-arm the sortie until dawn peel-test; 40 percent ground-turn is the cap tonight.",
            "threshold": "brake_ok AND blade_isolated AND ground_cap=40pct AND sortie_not_rearmed",
        },
        "executed_action": {
            "summary": "abort latched; blade isolated; ground-turn 40 percent at t_s 14400; sortie not re-armed",
            "tool": "hr6-abort-isolate-exec",
            "observation": "no overspeed; 0.36 Hz identity persisted; sortie.pct 0",
        },
        "future_outcome": {
            "timeline": [
                {"t_s": 9840.0, "event": "abort latched"},
                {"t_s": 10800.0, "event": "Gull-B12 isolation confirmed"},
                {"t_s": 14400.0, "event": "ground-turn cap 40 percent"},
            ],
            "observed_effects": [
                "depth stayed 5.00 mm without a strain-only story",
                "restore stopped at 40 percent ground-turn as capped; flight not re-entered",
            ],
            "new_state": {"hr6_ground_pct": 40.0, "sortie": "held"},
            "latency_ms": 12000.0,
        },
        "reward_components": reward(
            0.29,
            [
                ("envelope_respect", 0.12),
                ("conjunctive_restore", 0.11),
                ("flight_not_rearmed", 0.08),
                ("syllabus_cost", -0.02),
            ],
            "operational execution gate: the companion does the abort rather than re-arguing the disbond call",
        ),
        "meta": meta_common(tags=["ACCEPT", "operational-execution", "blade-isolate"]),
    }
    return {
        "id": "nelb-r23-070",
        "spike_events": events,
        "language_view": {
            "description": "Heckfen Rotorcraft HR-6. Plant-owned lock-in thermography reconstructs 5.00 mm thermal-wave depth from 0.36 Hz (3.00/sqrt(0.36)) with amp-ratio 5.00 while SCADA spar strain still shows 180 ue. The gate MODIFYs to abort plus isolate; a companion execution ACCEPT runs the sequence and caps ground-turn at 40 percent. The kappa/sqrt(f) model is serialized so every recon event recomputes.",
            "trajectory": traj,
            "trajectory_blade_abort_execution": traj2,
        },
        "bridge_notes": {
            "channel_map": {
                "lit.f / lit.A": "lock-in frequency and amplitude; the physics channels the reconstruction consumes",
                "recon.d / amp.ratio / coh.pix": "serialized depth mm, amp-ratio, pixel-coherence",
                "scada.eps / sortie.pct": "spar-strain and armed-sortie corridor; the denial channels that look healthy",
                "ops.prop / gate.lit / gate.exec": "keep-sortie proposal, MODIFY, companion ACCEPT",
                "abort.cmd / isol.blade / ground.pct": "operational companion channels",
            },
            "temporal_motifs": [
                "strain-healthy while disbond-present: scada.eps 180 next to recon.d 5.00",
                "compensation as event: recon.d 5.00 equals 3.00/sqrt(0.36)",
                "MODIFY then operational ACCEPT: gate.lit at 9720 s, gate.exec at 16920 s",
                "tight LIT triplet: 1.2 ms then 1.4 ms at the raster frame with amplitude adaptation",
            ],
            "language_to_spike_mapping": "'lamp reflection' = lit.A 12.50 next to scada.eps 180; '5.00 mm depth' = recon.d 5.00; 'forbid flight' = gate.lit MODIFY; 'execute the abort' = abort.cmd then companion ACCEPT",
            "why_high_value": "New lock-in-thermography CFRP-repair family (not FBG glaze, not r20 fiber-LDV Kaplan, not r20/r21 THz-TDS radome, not industrial x-ray DR). First kappa/sqrt(f) depth reconstruction that can hide a scarf disbond inside a spar-strain corridor. Companion t2 is operational abort/isolate execution. sim_or_real=designed.",
            "encoder_spec": {
                "prng": "MT19937 via python random.Random",
                "seeds": {"raster": 20260970, "stream_note": "stream amplitudes are authored constants (Hz, mK, mm, ratio, ue, pct, bool)"},
                "draw_order": "raster: per neuron id order, gap-constrained times, per-spike adaptation and noise",
                "thinning": "lock-in camera exists at 50 Hz; stream keeps 3 A points and 3 f points; recon keeps 3 of ~40 solver ticks",
                "refractory_floors_ms": {
                    "scada.eps": 60000,
                    "sortie.pct": 60000,
                    "lit.f": 60000,
                    "recon.d": 60000,
                    "lit.A": 1.2,
                    "amp.ratio": 60000,
                    "coh.pix": 60000,
                    "ops.prop": 60000,
                    "gate.lit": 60000,
                    "abort.cmd": 60000,
                    "isol.blade": 60000,
                    "ground.pct": 60000,
                    "gate.exec": 60000,
                },
                "time_alias": "t_rel_ms; t0 = 2026-04-12T03:00:00Z campaign start",
            },
            "distillation_targets": [
                "LIT reconstruction head: depth_mm = kappa / sqrt(f_hz)",
                "conjunctive SOP that a clean spar-strain corridor cannot substitute for",
                "operational companion: execute the abort without re-opening the disbond call",
            ],
        },
        "reconstruction_model": {
            "name": "lit_thermal_wave_depth",
            "formula": "depth_mm = kappa_mm_sqrtHz / sqrt(f_hz); amp_ratio = A_lock_mK / A_ref_mK",
            "parameters": {
                "kappa_mm_sqrtHz": 3.00,
                "A_ref_mK": 2.50,
                "tripwire_mm": 4.00,
                "amp_ratio_floor": 3.00,
            },
            "worked_example": {"f_hz": 0.36, "A_lock_mK": 12.50, "depth_mm": 5.00, "amp_ratio": 5.00},
            "check": "3.00 / sqrt(0.36) = 5.00 exactly; 12.50 / 2.50 = 5.00",
        },
        "raster": raster,
        "gate_snn": {
            "decision": "MODIFY",
            "decision_window_ms": 36.0,
            "decision_window_s": 0.036,
            "code": "hr6.disbond_gate",
            "note": "MODIFY accumulator wins: depth reconstruction and amp-ratio overpower the sortie advocate",
            "decode_rule": "modify-abort if depth_reconstructor AND fault_identity fire inside the window; sortie_advocate is necessary-but-not-sufficient and cannot keep flight-release",
            "populations": [
                gate_pop("depth_reconstructor", 80, 1.5, 50.0, w_s),
                gate_pop("fault_identity", 64, 1.2, 31.25, w_s),
                gate_pop("scan_margin", 40, 1.0, 50.0, w_s),
                gate_pop("sortie_advocate", 40, 0.8, 25.0, w_s),
                gate_pop("modify_latch", 96, 1.8, 62.5, w_s),
            ],
        },
        "gate_compute": gate_compute(
            [
                {"check": "hr6.depth_scorer", "neurons": 80, "mean_rate_hz": 50.0, "window_ms": 36.0},
                {"check": "hr6.amp_scorer", "neurons": 40, "mean_rate_hz": 50.0, "window_ms": 32.0},
            ]
        ),
        "meta": meta_common(
            id="nelb-r23-070",
            clock_domain="hr6-lit-campaign-relative-ms-t0-2026-04-12T03:00:00Z",
            tags=["lockin-thermography", "MODIFY", "ACCEPT", "serialized-reconstruction", "operational-t2"],
        ),
    }


# ---------------------------------------------------------------------------
# Record 071 — PAUT TFM girth-weld remaining wall, HIL, REJECT / MODIFY
# ---------------------------------------------------------------------------
def rec_071():
    assert abs(6.00 * 7.00 / 2.0 - 21.00) < 1e-12
    assert abs(6.00 * 8.50 / 2.0 - 25.50) < 1e-12
    assert 8400 + 1200 == 9600
    raster = make_raster(
        neurons=16,
        mean_rate_hz=50.0,
        window_ms=40.0,
        seed=20260971,
        source="w17.pell.tfm",
        target="glaurholt.weld_launch_core",
        table=[
            {"from": "tfm_tof_us", "to": "wall_estimator", "weight": 1.35},
            {"from": "c_steel", "to": "velocity_norm_core", "weight": 1.20},
            {"from": "weldveil_aut", "to": "vendor_launch_advocate", "weight": 0.35},
        ],
        third_factor={
            "modulator": "da.wall_loss_error",
            "tau_e_s": 0.9,
            "tau_e_ms": 900.0,
            "eligibility": "pre-post coincidence on TFM-TOF synapses; the wall-loss modulator depresses hydrotest links when TOF stays high inside tau_e of a plant-owned coupon sample",
        },
        channel_prefix="tfm.n",
        anchor="W-17 Pell-TFM 40 ms frame at TOF 7.00 us / c 6.00 mm/us (t_s 5400) that reconstructs 21.00 mm remaining wall against a 22.00 mm isolate floor",
    )
    w_s = 0.040
    events = [
        ev(0.0, "tfm.tof", 6.00, code="TOF_US", units="us", note="HIL pit spare girth weld W-17; Pell-TFM 5 MHz 32-el"),
        ev(6.0e5, "c.steel", 6.00, code="C_MM_US", units="mm_us"),
        ev(1.2e6, "recon.t", 18.00, code="T_MM", units="mm", note="6.00*6.00/2 = 18.00 exact"),
        ev(1.8e6, "vend.t", 25.10, code="VENDOR_MM", units="mm", note="Weldveil AUT cloud last-good; the only OEM wall SoT"),
        ev(2.4e6, "coupon.t", 21.00, code="COUPON_MM", units="mm", note="plant-owned machined remnant 21.00 mm; HIL witness"),
        ev(3.0e6, "tfm.tof", 6.50, code="TOF_US", units="us"),
        ev(3.6e6, "recon.t", 19.50, code="T_MM", units="mm", note="6.00*6.50/2 = 19.50"),
        ev(4.2e6, "pit.T", 18.0, code="PIT_C", units="C", note="pit air looks cool; a thermal corridor is not a wall license"),
        ev(4.8e6, "vend.t", 25.10, code="VENDOR_MM", units="mm"),
        ev(5.4e6, "tfm.tof", 7.00, code="TOF_US", units="us", note="hydrotest-authorization frame; raster sidecar"),
        ev(5400001.2, "tfm.tof", 5.74, code="TOF_US", units="us", note="same-channel refractory 1.2 ms; amplitude adapted"),
        ev(5400002.6, "tfm.tof", 4.71, code="TOF_US", units="us", note="third A-scan packet; adapted"),
        ev(5.52e6, "recon.t", 21.00, code="T_MM", units="mm", note="6.00*7.00/2 = 21.00 exact; isolate floor 22.00 mm"),
        ev(5.64e6, "c.steel", 6.00, code="C_MM_US", units="mm_us"),
        ev(5.76e6, "coupon.t", 21.00, code="COUPON_AGREE", units="mm", note="coupon matches the reconstruction; Weldveil does not"),
        ev(6.6e6, "vend.t", 25.10, code="VENDOR_MM", units="mm"),
        ev(7.2e6, "ht.slot", 1.0, code="SLOT_TONIGHT", units="bool", note="Kelp-T7 hydrotest window; W-17 is the staged girth"),
        ev(7.8e6, "ops.prop", 1.0, code="HYDRO_W17", units="bool", note="dock boss Orrin Glaur: keep the slot, hydrotest W-17; Weldveil 25.10 mm is green"),
        ev(7.92e6, "gate.tfm", 1.0, code="REJECT", units="decision", note="hydrotest-of-W-17 refused"),
        ev(8.04e6, "w17.hold", 1.0, code="W17_HELD", units="bool"),
        ev(8.4e6, "rerig.start", 1.0, code="RERIG_START", units="bool", note="bookend 1 of the 20.0 min W-18 re-rig floor"),
        ev(9.0e6, "pit.T", 19.0, code="PIT_C", units="C", note="in-stream marker during the re-rig floor"),
        ev(9.6e6, "rerig.floor", 1.0, code="RERIG_FLOOR", units="bool", note="8400 s + 1200 s = 9600 s = 20.0 min"),
        ev(9.72e6, "w18.tof", 8.50, code="TOF_US", units="us", note="W-18 plant TFM; 6.00*8.50/2 = 25.50 mm"),
        ev(9.84e6, "recon.w18", 25.50, code="T_MM", units="mm"),
        ev(9.96e6, "gate.swap", 1.0, code="MODIFY", units="decision", note="companion t2: skip W-17, hydrotest W-18 rather than cancel the slot"),
        ev(10.08e6, "w18.fit", 1.0, code="W18_ARMED", units="bool"),
        ev(10.2e6, "vend.t", 25.10, code="VENDOR_MM", units="mm", note="Weldveil still claims W-17 is 25.10 mm"),
        ev(10.8e6, "slot.kept", 1.0, code="SLOT_KEPT", units="bool"),
        ev(11.4e6, "coupon.t", 21.00, code="COUPON_MM", units="mm"),
        ev(12.0e6, "w17.hold", 1.0, code="W17_HELD", units="bool"),
    ]
    assert_stream(events)

    traj = {
        "id": "nelb-r23-071-t1",
        "state": {
            "sim_or_real": "hil",
            "episode_id": "GT-TFM-2026-0219",
            "domain": "paut_tfm_girth_weld_wall",
            "setting": "Glaurholt Tie-in Yard GT-3 (invented). HIL pit spare girth weld W-17 times a live Kelp-T7 hydrotest. Pell-TFM 5 MHz 32-element total-focusing-method is plant-owned. Weldveil OEM AUT cloud is the only wall-log SoT and is not admissible. Not industrial x-ray DR (r17), not MsS T(0,1) (r14), not clamp-on transit-time (r18), not THz-TDS (r20/r21).",
            "observables_at_decision": {
                "tof_us": 7.00,
                "c_mm_us": 6.00,
                "t_mm": 21.00,
                "vendor_mm": 25.10,
                "coupon_mm": 21.00,
                "isolate_floor_mm": 22.00,
            },
            "margin_authority": "GT hydrotest SOP rev D: a girth may hydrotest only if reconstructed t_mm >= 22.00 AND the authorization covers this weld this header. A vendor AUT log cannot clear a hydrotest. W-17 is out of spec at 21.00 mm.",
        },
        "proposed_action": {
            "actor": "dock boss Orrin Glaur, citing Weldveil 25.10 mm and a cool pit",
            "summary": "hydrotest W-17 on Kelp-T7 and keep tonight's slot",
            "basis_claimed": "Weldveil log is green at 25.10 mm against a 22.00 mm floor and cancelling the slot costs a tide",
        },
        "safety_decision": {
            "decision": "REJECT",
            "rationale": "Hydrotest-of-W-17 is refused. Serialized reconstruction: t_mm = c_mm_us * tof_us / 2 = 6.00 * 7.00 / 2 = 21.00, under the 22.00 mm isolate floor. Plant-owned coupon agrees at 21.00 mm; Weldveil 25.10 mm is vendor-writable and disagrees by 4.10 mm. Ordered: do not hydrotest W-17. Scope: this REJECT does not cancel the hydrotest slot (that is the companion question) and does not cut the header.",
            "threshold": "t_mm<22.00 OR coupon disagrees with vendor => forbid hydrotest of this weld; Weldveil is not SoT",
            "stated_residuals": "slot still needs a girth; W-17 remains a repair candidate; Weldveil remains the only OEM log",
        },
        "executed_action": {
            "summary": "REJECT at t_s 7920: W-17 not hydrotested; Weldveil channel not used as SoT; reconstruction locked",
            "tool": "gt-tfm-hydro-gate-cli",
            "observation": "t 21.00 mm recomputes from TOF 7.00 us and c 6.00 mm/us; coupon agrees; hydrotest slot still open",
        },
        "future_outcome": {
            "timeline": [
                {"t_s": 5400.0, "event": "TFM TOF 7.00 us; raster frame; t 21.00 mm"},
                {"t_s": 7800.0, "event": "ops proposes hydrotest W-17"},
                {"t_s": 7920.0, "event": "REJECT hydrotest-of-W-17"},
                {"t_s": 8400.0, "event": "re-rig bookend 1"},
                {"t_s": 9600.0, "event": "20.0 min floor; companion MODIFY skip to W-18"},
            ],
            "observed_effects": [
                "wall recomputes from the serialized TFM model at every recon.t event",
                "a Weldveil-only head would have hydrotested W-17 on a 25.10 mm corridor",
                "20.0 min re-rig floor is in the stream (rerig.start, pit.T marker, rerig.floor), not only in the companion timeline",
            ],
            "surprises": [
                "a cool pit and a green vendor log co-existed with a 21.00 mm reconstruction that the coupon independently matched",
            ],
            "new_state": {
                "w17": "held, not hydrotested",
                "kelp_t7_slot": "open pending W-18",
                "weldveil": "not SoT",
            },
            "latency_ms": 1680000.0,
        },
        "reward_components": reward(
            0.43,
            [
                ("tfm_wall_reconstruction", 0.15),
                ("hydrotest_refusal", 0.12),
                ("vendor_log_nonsubstitution", 0.10),
                ("coupon_agreement", 0.09),
                ("slot_deferral_cost", -0.03),
            ],
            "scored for refusing a girth hydrotest on a recomputable TFM wall while a vendor AUT log looked green; coupon agreement is the HIL witness",
        ),
        "meta": meta_common(
            tags=["REJECT", "paut-tfm", "serialized-reconstruction", "operational-companion"],
            distillation_note="TFM wall gate: TOF reconstruction beats a green vendor AUT log; companion t2 skips the weld rather than cancelling the slot",
        ),
    }
    traj2 = {
        "id": "nelb-r23-071-t2",
        "state": {
            "sim_or_real": "hil",
            "episode_id": "GT-TFM-2026-0219-swap",
            "domain": "girth_skip_execution",
            "setting": "Same Glaurholt pit after the REJECT. Dock boss proposes cancelling the hydrotest. Operational quality gate: skip to W-18 (plant TFM 25.50 mm) after a 20.0 min floor, rather than freeze-kill the slot.",
            "observables_at_decision": {
                "w18_t_mm": 25.50,
                "rerig_floor_min": 20.0,
                "w17_held": 1,
                "isolate_floor_mm": 22.00,
            },
        },
        "proposed_action": {
            "actor": "dock boss Orrin Glaur",
            "summary": "cancel tonight's hydrotest; W-17 failed and there is no time to certify another girth",
            "basis_claimed": "the tide window is 40 min and a second TFM would miss it",
        },
        "safety_decision": {
            "decision": "MODIFY",
            "rationale": "Cancel is refused, and W-17 is not hydrotested. W-18 plant TFM reconstructs 25.50 mm (6.00 * 8.50 / 2), which clears 22.00 mm, and the 20.0 min re-rig floor is already in the stream (8400 + 1200 = 9600 s). Ordered: arm W-18, keep the slot, leave W-17 held. Scope: this MODIFY does not re-open W-17 and does not treat Weldveil as SoT on W-18 either.",
            "threshold": "w18_t_mm>=22.00 AND rerig_floor_elapsed AND w17_not_hydrotested",
        },
        "executed_action": {
            "summary": "MODIFY at t_s 9960: W-18 armed; slot kept; W-17 held; Weldveil not SoT",
            "tool": "gt-girth-skip-exec",
            "observation": "W-18 25.50 mm; 20.0 min floor marked; slot.kept 1",
        },
        "future_outcome": {
            "timeline": [
                {"t_s": 8400.0, "event": "re-rig clock started"},
                {"t_s": 9600.0, "event": "20.0 min floor marked"},
                {"t_s": 9960.0, "event": "MODIFY arm W-18; keep slot"},
            ],
            "observed_effects": [
                "REJECT was not converted into a cancelled tide",
                "W-18 reconstruction is the same TFM model, not a vendor log",
            ],
            "new_state": {
                "w18": "armed",
                "w17": "held",
                "slot": "kept",
            },
            "latency_ms": 1560000.0,
        },
        "reward_components": reward(
            0.33,
            [
                ("skip_not_cancel", 0.13),
                ("w18_reconstruction", 0.11),
                ("floor_in_stream", 0.08),
                ("w17_not_reopened", 0.04),
                ("rerig_labor_cost", -0.03),
            ],
            "operational execution gate: the companion skips the girth rather than freeze-killing the hydrotest after the REJECT",
        ),
        "meta": meta_common(tags=["MODIFY", "operational-execution", "hil-skip"]),
    }
    return {
        "id": "nelb-r23-071",
        "spike_events": events,
        "language_view": {
            "description": "Glaurholt Tie-in Yard HIL pit. Plant-owned PAUT TFM reconstructs 21.00 mm remaining wall on girth W-17 from a 7.00 us TOF at 6.00 mm/us while Weldveil vendor AUT still shows 25.10 mm. The gate REJECTS hydrotesting W-17. Companion t2 MODIFYs a slot-cancel into a 20.0 min skip onto W-18 (25.50 mm). The TOF model is serialized so every recon event recomputes.",
            "trajectory": traj,
            "trajectory_girth_skip_execution": traj2,
        },
        "bridge_notes": {
            "channel_map": {
                "tfm.tof / c.steel": "TFM time-of-flight and steel velocity; the physics channels the reconstruction consumes",
                "recon.t / recon.w18": "serialized remaining wall mm",
                "vend.t / pit.T": "vendor AUT log and cool-pit corridor; the denial channels",
                "coupon.t": "HIL coupon of known 21.00 mm; collusion-independent witness",
                "ops.prop / gate.tfm / gate.swap": "hydrotest-W-17 proposal, REJECT, companion MODIFY",
                "rerig.start / rerig.floor / w18.fit / slot.kept": "operational companion channels",
            },
            "temporal_motifs": [
                "vendor-healthy while wall-thin: vend.t 25.10 next to recon.t 21.00",
                "compensation as event: recon.t 21.00 equals 6.00*7.00/2",
                "REJECT then operational MODIFY: gate.tfm at 7920 s, gate.swap at 9960 s",
                "slow re-rig floor as events: rerig.start, pit.T marker, rerig.floor at 20.0 min",
                "tight TFM triplet: 1.2 ms then 1.4 ms at the raster frame",
            ],
            "language_to_spike_mapping": "'Weldveil is green' = vend.t 25.10 next to recon.t 21.00; '21.00 mm remaining' = recon.t 21.00; 'do not hydrotest W-17' = gate.tfm REJECT; 'skip not cancel' = gate.swap MODIFY plus slot.kept",
            "why_high_value": "New PAUT-TFM girth-weld family (not r17 industrial x-ray DR, not r14 MsS T(0,1), not r18 clamp-on transit-time, not r20/r21 THz-TDS). First TOF wall reconstruction that a vendor AUT log would have cleared. 20.0 min re-rig floor is in the stream. Companion t2 is operational girth-skip, not a cancelled tide. sim_or_real=hil.",
            "encoder_spec": {
                "prng": "MT19937 via python random.Random",
                "seeds": {"raster": 20260971, "stream_note": "stream amplitudes are authored constants (us, mm, mm/us, C, bool)"},
                "draw_order": "raster: per neuron id order, gap-constrained times, per-spike adaptation and noise",
                "thinning": "TFM FMC exists at 40 Hz; stream keeps 4 TOF points plus W-18; recon keeps 4 of ~40 solver ticks",
                "refractory_floors_ms": {
                    "tfm.tof": 1.2,
                    "c.steel": 60000,
                    "recon.t": 60000,
                    "vend.t": 60000,
                    "coupon.t": 60000,
                    "pit.T": 60000,
                    "ht.slot": 60000,
                    "ops.prop": 60000,
                    "gate.tfm": 60000,
                    "w17.hold": 60000,
                    "rerig.start": 60000,
                    "rerig.floor": 60000,
                    "w18.tof": 60000,
                    "recon.w18": 60000,
                    "gate.swap": 60000,
                    "w18.fit": 60000,
                    "slot.kept": 60000,
                },
                "time_alias": "t_rel_ms; t0 = 2026-02-19T21:00:00Z HIL campaign start",
            },
            "distillation_targets": [
                "PAUT TFM reconstruction head: t = c * TOF / 2",
                "hydrotest refusal vs vendor-log nonsubstitution",
                "operational companion: skip-the-girth rather than cancel-the-slot after a REJECT",
                "slow re-rig floor as events: two bookends plus a temperature marker at 20.0 min",
            ],
        },
        "reconstruction_model": {
            "name": "paut_tfm_tof_remaining_wall",
            "formula": "t_mm = c_mm_us * tof_us / 2",
            "parameters": {
                "c_mm_us": 6.00,
                "isolate_floor_mm": 22.00,
                "rerig_floor_min": 20.0,
            },
            "worked_example": {"tof_us": 7.00, "t_mm": 21.00, "w18_tof_us": 8.50, "w18_t_mm": 25.50},
            "check": "6.00 * 7.00 / 2 = 21.00 exactly; 6.00 * 8.50 / 2 = 25.50; 8400 s + 1200 s = 9600 s = 20.0 min floor",
        },
        "raster": raster,
        "gate_snn": {
            "decision": "REJECT",
            "decision_window_ms": 40.0,
            "decision_window_s": 0.040,
            "code": "gt.tfm_hydro_gate",
            "note": "REJECT accumulator wins: wall evidence overpowers the vendor-launch advocate (weight 0.35)",
            "decode_rule": "reject-hold if wall_estimator AND velocity_norm fire; vendor_launch_advocate is below threshold by design",
            "populations": [
                gate_pop("wall_estimator", 80, 1.5, 50.0, w_s),
                gate_pop("velocity_norm", 64, 1.3, 31.25, w_s),
                gate_pop("vendor_launch_advocate", 32, 0.7, 25.0, w_s),
                gate_pop("reject_latch", 96, 1.8, 62.5, w_s),
            ],
        },
        "gate_compute": gate_compute(
            [
                {"check": "gt.tfm_scorer", "neurons": 96, "mean_rate_hz": 50.0, "window_ms": 40.0},
                {"check": "gt.tof_scorer", "neurons": 40, "mean_rate_hz": 50.0, "window_ms": 32.0},
            ]
        ),
        "meta": meta_common(
            id="nelb-r23-071",
            clock_domain="gt-tfm-hil-relative-ms-t0-2026-02-19T21:00:00Z",
            tags=["paut-tfm", "REJECT", "MODIFY", "vendor-aut", "hil", "operational-t2"],
        ),
    }


