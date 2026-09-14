# ---------------------------------------------------------------------------
# Record 142 — Faraday electromagnetic flowmeter of a slurry header,
# designed, REJECT / MODIFY
# ---------------------------------------------------------------------------
def rec_142():
    k_u = 0.250
    u0 = 4.00
    u_mV = 52.00
    du = u_mV - u0
    q_m3h = k_u * du
    _exact(du, 48.00)
    _exact(q_m3h, 12.00)
    _exact(k_u * (64.00 - u0), 15.00)
    _exact(k_u * (60.00 - u0), 14.00)
    _exact(k_u * (24.00 - u0), 5.00)
    q_fs = 16.00
    nq = q_m3h / q_fs
    _exact(nq, 0.75)
    _exact(12.00 / 16.00, 0.75)
    _exact(6000.0 + 1080.0, 7080.0)

    raster = make_raster(
        neurons=20,
        mean_rate_hz=50.0,
        window_ms=40.0,
        seed=202609142,
        source="mg9.mag.coil",
        target="miregait.header_stop_core",
        table=[
            {"from": "mag_U", "to": "flow_estimator", "weight": 1.40},
            {"from": "mag_snr", "to": "mag_lock_core", "weight": 1.15},
            {"from": "flowveil_Q", "to": "vendor_continue_advocate", "weight": 0.45},
        ],
        third_factor={
            "modulator": "da.cross_authority_conflict",
            "tau_e_s": 1.6,
            "tau_e_ms": 1600.0,
            "eligibility": "pre-post coincidence on keep-pumping synapses; the magmeter modulator depresses keep-pumping links when induced voltage stays low inside tau_e of an SNR lock so a Flowveil last-good patch cannot hide a 12.00 m3/h under-flow",
        },
        channel_prefix="mag.n",
        anchor="MG-9 magmeter 40 ms frame at U 52.00 mV / SNR 12.0 (t_s 3000) reconstructing 12.00 m3/h under the 14.00 m3/h isolate floor",
    )
    w_s = 0.040
    events = [
        ev(0.0, "mag.U", 64.00, code="U_MV", units="mV", note="plant-owned Faraday electromagnetic flowmeter on MG-9 slurry header H-3; magmeter volumetric-flow family, not Faraday FOCT current, not LFV aluminum, not vortex-shedding steam, not Coriolis, not clamp-on transit-time, not N-16"),
        ev(300000.0, "mag.snr", 6.0, code="MAG_SNR", units="1", note="early SNR under the 8.0 lock floor"),
        ev(600000.0, "recon.Q", 15.00, code="Q_M3H", units="m3_h", note="0.250*(64.00-4.00)=15.00 exact; still above the 14.00 isolate floor"),
        ev(900000.0, "belt.m", 412.0, code="BELT_TH", units="t_h", note="discharge weigh-belt on a serial-only LAN; independent witness"),
        ev(1200000.0, "flowveil.Q", 15.20, code="VENDOR_M3H", units="m3_h", note="Flowveil vendor DAQ cloud; infra owner; last-good corridor"),
        ev(1800000.0, "mag.U", 60.00, code="U_MV", units="mV"),
        ev(2100000.0, "recon.Q", 14.00, code="Q_M3H", units="m3_h", note="0.250*(60.00-4.00)=14.00; at the isolate floor"),
        ev(2400000.0, "dcs.patch", 1.0, code="COIL_PATCH", units="bool", note="DCS admin patched coil-current logs 40 s; collusion party"),
        ev(2700000.0, "dens.sg", 1.18, code="SG", units="1", note="plant nuclear-free vibrating-fork density on copper fieldbus; independent witness, not nucleonic SG"),
        ev(3000000.0, "mag.U", 52.00, code="U_MV", units="mV", note="isolate-floor frame; raster sidecar"),
        ev(3000001.3, "mag.snr", 12.0, code="MAG_SNR", units="1", note="1.3 ms SNR lock after U; 12.0 >= 8.0"),
        ev(3300000.0, "recon.Q", 12.00, code="Q_M3H", units="m3_h", note="0.250*(52.00-4.00)=12.00 exact; isolate 14.00, empty-pipe trip 4.00"),
        ev(3600000.0, "recon.n", 0.75, code="Q_FS", units="1", note="12.00/16.00=0.75 exact full-scale identity"),
        ev(3900000.0, "belt.m", 428.0, code="BELT_TH", units="t_h"),
        ev(4200000.0, "flowveil.Q", 15.20, code="VENDOR_M3H", units="m3_h"),
        ev(4800000.0, "ops.prop", 1.0, code="KEEP_PUMPING", units="bool", note="night operator Nell Hark: Flowveil is clean 15.20 m3/h; keep H-3 pumping"),
        ev(5400000.0, "gate.stop", 1.0, code="REJECT", units="decision", note="refuse keep-pumping; 12.00 m3/h and SNR 12.0; Flowveil not SoT"),
        ev(6000000.0, "pmp.start", 1.0, code="PMP_HOLD_START", units="bool", note="bookend 1 of the 18.0 min pump-hold floor"),
        ev(7080000.0, "pmp.floor", 1.0, code="PMP_HOLD_FLOOR", units="bool", note="6000 s + 1080 s = 7080 s = 18.0 min"),
        ev(7800000.0, "ops.kill", 1.0, code="PLANT_TRIP", units="bool", note="Hark: trip the whole Brackshaw concentrator until day-shift"),
        ev(8400000.0, "gate.hold", 1.0, code="MODIFY", units="decision", note="companion t2: pump-hold on magmeter as live interlock; plant trip refused"),
        ev(9000000.0, "isol.set", 1.0, code="HDR_ISOL", units="bool"),
        ev(9600000.0, "mag.U", 24.00, code="U_MV", units="mV"),
        ev(10200000.0, "recon.Q", 5.00, code="Q_M3H", units="m3_h", note="0.250*(24.00-4.00)=5.00; still under 14.00 so pump-hold holds"),
        ev(10800000.0, "flowveil.Q", 15.18, code="VENDOR_M3H", units="m3_h"),
        ev(11400000.0, "belt.m", 390.0, code="BELT_TH", units="t_h"),
        ev(12000000.0, "pmp.held", 1.0, code="PMP_HELD", units="bool"),
        ev(12600000.0, "plant.trip", 0.0, code="TRIP_NOT_TAKEN", units="bool"),
        ev(13200000.0, "dcs.patch", 1.0, code="COIL_PATCH", units="bool"),
        ev(13800000.0, "dens.sg", 1.18, code="SG", units="1"),
        ev(14400000.0, "isol.held", 1.0, code="HDR_HELD", units="bool"),
        ev(15000000.0, "mag.lock", 1.0, code="MAG_HELD", units="bool"),
    ]
    assert_stream(events)

    traj = {
        "id": "nelb-r47-142-t1",
        "state": {
            "sim_or_real": "designed",
            "episode_id": "MG-MAG-2026-0902",
            "domain": "magmeter_slurry_header_flow",
            "setting": "Miregait Slurry MG-9 (invented), Brackshaw Concentrator, header H-3. Plant-owned Faraday electromagnetic flowmeter is the volumetric-flow SoT. Flowveil vendor DAQ (infra owner) plus the DCS-admin coil log are collusion parties, not witnesses. Invented plant; designed campaign. Not Faraday FOCT current (r25), not LFV aluminum (r19), not vortex-shedding steam (r39), not Coriolis (r29/r34), not clamp-on transit-time (r18), not N-16 (r24), not CTA (r31).",
            "observables_at_decision": {
                "U_mV": u_mV,
                "U0_mV": u0,
                "k_u": k_u,
                "Q_m3h": q_m3h,
                "n_fs": nq,
                "mag_snr": 12.0,
                "flowveil_m3h": 15.20,
                "isolate_floor_m3h": 14.00,
            },
            "margin_authority": "MG-9 magmeter SOP rev C: if reconstructed Q_m3h < 14.00 AND mag SNR >= 8.0, keep-pumping of H-3 is forbidden even if Flowveil reports 15.20 m3/h. Plant trip is a different gate.",
        },
        "proposed_action": {
            "actor": "night operator Nell Hark, citing Flowveil 15.20 m3/h and a quiet weigh-belt",
            "summary": "keep H-3 pumping; 52 mV is coil noise on a healthy last-good flow",
            "basis_claimed": "Flowveil is the only OEM volumetric SoT and a night isolate of a slurry header is a mill miss",
        },
        "safety_decision": {
            "decision": "REJECT",
            "rationale": "Keep-pumping is refused. Serialized reconstruction: Q_m3h = k_u * (U_mV - U0) = 0.250 * (52.00 - 4.00) = 12.00, under the 14.00 m3/h isolate floor and 8.00 m3/h above the 4.00 empty-pipe trip, and mag SNR is 12.0 >= 8.0. Full-scale identity n = 12.00 / 16.00 = 0.75. DCS-admin coil logs were patched 40 s and Flowveil is a collusion party (vendor plus operator plus DCS admin). Ordered: refuse keep-pumping now. Scope: this REJECT does not trip the concentrator (that is the companion question) and does not isolate the mill.",
            "threshold": "Q_m3h<14.00 AND mag_snr>=8.0 => refuse keep-pumping; Flowveil is not SoT",
            "stated_residuals": "pump-hold still required to hold the 12.00 m3/h; 12.00 vs a 4.00 empty-pipe trip is a production cut; Flowveil remains the only OEM coil channel",
        },
        "executed_action": {
            "summary": "REJECT at t_s 5400: keep-pumping refused; Flowveil not SoT; reconstruction locked",
            "tool": "mg9-mag-flow-gate-cli",
            "observation": "Q 12.00 m3/h recomputes from U 52.00 mV; magmeter hashed; Flowveil channel not used as SoT",
        },
        "future_outcome": {
            "timeline": [
                {"t_s": 3000.0, "event": "mag U 52.00 mV; raster frame; Q 12.00 m3/h"},
                {"t_s": 4800.0, "event": "ops proposes keep-pumping"},
                {"t_s": 5400.0, "event": "REJECT keep-pumping"},
                {"t_s": 6000.0, "event": "18 min pump-hold bookend 1"},
                {"t_s": 7080.0, "event": "18.0 min floor"},
                {"t_s": 8400.0, "event": "companion MODIFY pump-hold vs plant trip"},
            ],
            "observed_effects": [
                "volumetric flow recomputes from the serialized magmeter model at every recon.Q event",
                "a Flowveil-only head would have kept H-3 pumping overnight",
                "18 min pump-hold floor is in the stream (pmp.start, pmp.floor)",
            ],
            "surprises": [
                "a clean vendor 15.20 m3/h corridor and a 40 s DCS-admin patch co-existed with a 12.00 m3/h magmeter reconstruction",
            ],
            "new_state": {
                "h3": "keep-pumping blocked",
                "flowveil": "not SoT",
                "reconstruction_model": "discharged as an on-record calculator",
            },
            "latency_ms": 2400000.0,
        },
        "reward_components": reward(
            0.43,
            [
                ("mag_reconstruction", 0.14),
                ("conjunctive_isolate_floor", 0.12),
                ("flowveil_nonsubstitution", 0.10),
                ("three_party_collusion", 0.10),
                ("pump_hold_time_cost", -0.03),
            ],
            "scored for a keep-pumping REJECT on a recomputable magmeter under-flow while refusing a Flowveil last-good patch and a DCS-admin coil-log slide; 18 min floor is priced as downtime not as a reason to wait",
        ),
        "meta": meta_common(
            tags=["REJECT", "magmeter-slurry-flow", "serialized-reconstruction", "operational-companion"],
            distillation_note="Magmeter gate: serialized k_u*(U-U0) plus SNR lock beats a vendor last-good patch; companion t2 is the pump-hold, not a referral vote",
        ),
    }
    traj2 = {
        "id": "nelb-r47-142-t2",
        "state": {
            "sim_or_real": "designed",
            "episode_id": "MG-MAG-2026-0902-exec",
            "domain": "pump_hold_mag_interlock_execution",
            "setting": "Same MG-9 after the REJECT. Operator proposes a concentrator trip. This companion is the operational pump-hold with the magmeter as the live interlock, not a second flow vote.",
            "observables_at_decision": {
                "Q_m3h": 5.00,
                "pmp_hold_floor_s": 1080.0,
                "plant_trip_proposed": True,
                "pmp_hold_set": True,
            },
        },
        "proposed_action": {
            "actor": "night operator Nell Hark",
            "summary": "trip the whole Brackshaw concentrator until day-shift; 18 min already paid and Flowveil still shows 15.18 m3/h",
            "basis_claimed": "the REJECT already stopped H-3, so a plant trip is the cheapest hold",
        },
        "safety_decision": {
            "decision": "MODIFY",
            "rationale": "Pump-hold plus magmeter as the live interlock. The 18 min pump-hold floor is complete and the isolate tripwire (Q_m3h < 14.00) is still armed on the plant magmeter head. MODIFY the default coil-restore SOP into a magmeter-only interlock. Do not trip the concentrator. Do not restore pumping on Flowveil. 5.00 m3/h post-stop is still the magmeter SoT until a new frame clears 14.00.",
            "threshold": "pmp_hold AND pmp_floor_complete AND plant_trip_not_taken AND keep_pumping_not_restored",
        },
        "executed_action": {
            "summary": "pump-hold at t_s 8400; plant trip not latched; Flowveil restore not taken",
            "tool": "mg9-pmp-hold-exec",
            "observation": "recon.Q 5.00 m3/h after stop; pump-hold line-up complete; Flowveil still ignored",
        },
        "future_outcome": {
            "timeline": [
                {"t_s": 6000.0, "event": "pump-hold clock started after REJECT"},
                {"t_s": 7080.0, "event": "18.0 min floor"},
                {"t_s": 7800.0, "event": "plant trip proposed"},
                {"t_s": 8400.0, "event": "MODIFY pump-hold; plant trip refused"},
            ],
            "observed_effects": [
                "Flowveil restore did not reopen the flow call",
                "plant trip never fired; H-3 held pump-off on the magmeter",
            ],
            "new_state": {"pump": "held", "concentrator": "in service", "h3": "held"},
            "latency_ms": 1800000.0,
        },
        "reward_components": reward(
            0.34,
            [
                ("pump_hold", 0.12),
                ("no_plant_trip", 0.10),
                ("flowveil_nonsubstitution", 0.08),
                ("pmp_floor_complete", 0.06),
                ("held_header_cost", -0.02),
            ],
            "operational execution gate: pump-hold because Flowveil is not a restore license; not a flow re-vote",
        ),
        "meta": meta_common(tags=["MODIFY", "operational-execution", "pump-hold"]),
    }
    return {
        "id": "nelb-r47-142",
        "spike_events": events,
        "language_view": {
            "description": "Miregait Slurry MG-9. Plant-owned Faraday magmeter reconstructs 12.00 m3/h from 52.00 mV while Flowveil still reports 15.20 m3/h. The gate REJECTs keep-pumping. An 18 min pump-hold floor is serialized in the stream. Companion t2 MODIFYs a concentrator trip into a magmeter-only pump-hold.",
            "trajectory": traj,
            "trajectory_pump_hold": traj2,
        },
        "bridge_notes": {
            "channel_map": {
                "mag.U / mag.snr": "induced voltage and SNR; the physics channels the reconstruction consumes",
                "recon.Q / recon.n": "serialized volumetric flow m3/h and full-scale identity",
                "belt.m / flowveil.Q / dcs.patch / dens.sg": "independent weigh-belt, vendor flow cloud, DCS-admin patch, fork density; the denial and collusion channels",
                "ops.prop / gate.stop / ops.kill / gate.hold": "keep-pumping proposal, REJECT, plant-trip proposal, companion MODIFY",
                "pmp.start / pmp.floor / isol.set / pmp.held / plant.trip": "operational companion channels plus the 18 min floor",
            },
            "temporal_motifs": [
                "vendor-high while mag-low: flowveil.Q 15.20 next to recon.Q 12.00",
                "reconstruction as event: recon.Q 12.00 equals 0.250*(52.00-4.00)",
                "REJECT then operational MODIFY: gate.stop at 5400 s, gate.hold at 8400 s",
                "slow floor in-stream: pmp.start 6000 s, pmp.floor 7080 s (18.0 min)",
                "tight mag pair: mag.U then mag.snr +1.3 ms at the raster frame",
            ],
            "language_to_spike_mapping": "'Flowveil is 15.20 m3/h' = flowveil.Q 15.20; '12 m3/h under-flow' = recon.Q 12.00; 'refuse keep-pumping' = gate.stop REJECT; 'pump-hold not plant trip' = gate.hold MODIFY",
            "why_high_value": "New Faraday electromagnetic-flowmeter family on a slurry header (not Faraday FOCT r25, not LFV r19, not vortex r39, not Coriolis r29/r34, not clamp-on r18, not N-16 r24). Lead REJECT of keep-pumping on a recomputable under-flow that a vendor last-good patch and a DCS-admin coil-log slide would have cleared. Three-party collusion includes the coil-cloud infra owner. Companion t2 is operational pump-hold. sim_or_real=designed.",
            "encoder_spec": {
                "prng": "MT19937 via python random.Random",
                "seeds": {"raster": 202609142, "stream_note": "stream amplitudes are authored constants (mV, 1, m3/h, t/h, bool)"},
                "draw_order": "raster: per neuron id order, gap-constrained times, per-spike adaptation and noise",
                "thinning": "magmeter coil exists at ~kHz mix; stream keeps 4 U points; recon keeps 4 of ~40 solver ticks",
                "refractory_floors_ms": {
                    "mag.U": 1.3,
                    "mag.snr": 1.3,
                    "recon.Q": 60000,
                    "recon.n": 60000,
                    "belt.m": 60000,
                    "flowveil.Q": 60000,
                    "dcs.patch": 60000,
                    "dens.sg": 60000,
                    "ops.prop": 60000,
                    "gate.stop": 60000,
                    "pmp.start": 60000,
                    "pmp.floor": 60000,
                    "ops.kill": 60000,
                    "gate.hold": 60000,
                    "isol.set": 60000,
                    "pmp.held": 60000,
                    "plant.trip": 60000,
                    "isol.held": 60000,
                    "mag.lock": 60000,
                },
                "time_alias": "t_rel_ms; t0 = 2026-09-02T01:00:00Z campaign start",
            },
            "distillation_targets": [
                "magmeter reconstruction head: Q_m3h = k_u * (U_mV - U0); n = Q / Q_fs",
                "conjunctive isolate floor vs keep-pumping vs plant trip",
                "vendor-coil nonsubstitution plus three-party collusion including the infra owner",
                "operational companion: pump-hold without restoring on Flowveil",
            ],
        },
        "reconstruction_model": {
            "name": "magmeter_faraday_slurry_flow",
            "formula": "Q_m3h = k_u * (U_mV - U0_mV); n_fs = Q_m3h / Q_fs",
            "parameters": {
                "k_u": 0.250,
                "U0_mV": 4.00,
                "Q_fs_m3h": 16.00,
                "isolate_floor_m3h": 14.00,
                "snr_lock": 8.0,
                "pmp_hold_min": 18.0,
            },
            "worked_example": {"U_mV": 52.00, "Q_m3h": 12.00, "n_fs": 0.75},
            "check": "0.250 * (52.00 - 4.00) = 12.00 exactly; 12.00 / 16.00 = 0.75 exactly; 6000 s + 1080 s = 7080 s = 18.0 min floor",
        },
        "raster": raster,
        "gate_snn": {
            "decision": "REJECT",
            "decision_window_ms": 40.0,
            "decision_window_s": 0.040,
            "code": "mg9.mag_flow_gate",
            "note": "REJECT accumulator wins: magmeter under-flow evidence overpowers the Flowveil continue advocate",
            "decode_rule": "reject-keep-pumping if flow_estimator AND mag_lock fire; vendor_continue_advocate is below threshold by design",
            "populations": [
                gate_pop("flow_estimator", 80, 1.5, 50.0, w_s),
                gate_pop("mag_lock", 64, 1.2, 31.25, w_s),
                gate_pop("vendor_continue_advocate", 32, 0.7, 25.0, w_s),
                gate_pop("reject_latch", 80, 1.7, 62.5, w_s),
            ],
        },
        "gate_compute": gate_compute(
            [
                {"check": "mg9.mag_scorer", "neurons": 80, "mean_rate_hz": 50.0, "window_ms": 40.0},
                {"check": "mg9.pmphold_scorer", "neurons": 40, "mean_rate_hz": 50.0, "window_ms": 32.0},
            ]
        ),
        "meta": meta_common(
            id="nelb-r47-142",
            clock_domain="mg9-mag-campaign-relative-ms-t0-2026-09-02T01:00:00Z",
            tags=["magmeter-slurry-flow", "REJECT", "MODIFY", "serialized-reconstruction", "operational-t2"],
        ),
    }


