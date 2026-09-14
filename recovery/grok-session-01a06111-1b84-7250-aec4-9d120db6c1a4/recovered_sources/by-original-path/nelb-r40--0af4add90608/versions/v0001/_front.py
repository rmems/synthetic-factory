def occupancy_preflight():
    banned = (
        "fernholt therapy",
        "bpmveil",
        "button-bpm",
        "felltide",
        "sheetveil",
        "beta-transmission",
        "mashholt distillation",
        "specveil",
        "raman oh/ch",
    )
    hits = []
    root = Path("/tmp")
    for n in sorted(root.glob("nelb-r*/NOTES-r*.md")):
        if "nelb-r40" in str(n):
            continue
        text = n.read_text(encoding="utf-8", errors="replace").casefold()
        for b in banned:
            if b in text:
                hits.append(f"{n}:{b}")
    if hits:
        raise RuntimeError(f"family/plant collision {hits}")


# ---------------------------------------------------------------------------
# Record 121 — cyclotron button-BPM + BLM beam offset, designed,
# MODIFY / ACCEPT
# ---------------------------------------------------------------------------
def rec_121():
    k_x = 20.00
    r_nc = 18.00
    l_nc = 6.00
    x_mm = k_x * (r_nc - l_nc) / (r_nc + l_nc)
    q_sum = r_nc + l_nc
    k_h = 0.50
    q_blm = 8.00
    h_usv = k_h * q_blm
    i_rated = 80.00
    derate = 0.80
    i_cmd = i_rated * derate
    _exact(x_mm, 10.00)
    _exact(q_sum, 24.00)
    _exact(h_usv, 4.00)
    _exact(k_x * (15.00 - 9.00) / (15.00 + 9.00), 5.00)
    _exact(k_x * (16.80 - 7.20) / (16.80 + 7.20), 8.00)
    _exact(i_cmd, 64.00)
    _exact(6600.0 + 1080.0, 7680.0)

    raster = make_raster(
        neurons=20,
        mean_rate_hz=50.0,
        window_ms=36.0,
        seed=202609121,
        source="ft7.bpm.tr3",
        target="fernholt.current_derate_core",
        table=[
            {"from": "bpm_r", "to": "offset_estimator", "weight": 1.40},
            {"from": "bpm_l", "to": "pair_norm_core", "weight": 1.20},
            {"from": "bpmveil_x", "to": "vendor_continue_advocate", "weight": 0.45},
        ],
        third_factor={
            "modulator": "na.beam_offset_salience",
            "tau_e_s": 1.6,
            "tau_e_ms": 1600.0,
            "eligibility": "pre-post coincidence on current-derate synapses; the BPM modulator enables potentiation only while the left-right pair is co-active inside tau_e so a Bpmveil last-good TDC corridor cannot hide a 10.00 mm offset",
        },
        channel_prefix="bpm.n",
        anchor="FT-7 button-BPM 36 ms frame at R 18.00 nC / L 6.00 nC (t_s 3000) reconstructing 10.00 mm above the 8.00 mm derate floor",
    )
    w_s = 0.036
    events = [
        ev(0.0, "bpm.r", 15.00, code="R_NC", units="nC", note="plant-owned button-BPM pair on TR-3 nozzle; cyclotron BPM/BLM, not PMU, not fluxgate, not portal NaI, not muon tomography, not Faraday FOCT"),
        ev(300000.0, "bpm.l", 9.00, code="L_NC", units="nC", note="left button; x_mm = k_x * (R-L)/(R+L)"),
        ev(600000.0, "recon.x", 5.00, code="X_MM", units="mm", note="20.00*(15.00-9.00)/(15.00+9.00)=5.00 exact"),
        ev(900000.0, "i.na", 80.00, code="I_NA", units="nA", note="extracted current corridor"),
        ev(1200000.0, "bpmveil.x", 1.20, code="VENDOR_MM", units="mm", note="Bpmveil last-good FPGA TDC stamp; not admissible SoT"),
        ev(1800000.0, "bpm.r", 15.00, code="R_NC", units="nC"),
        ev(2100000.0, "recon.x", 5.00, code="X_MM", units="mm"),
        ev(2400000.0, "rp.usv", 0.80, code="RP_USV", units="uSv", note="RP ion-chamber corridor; independent of Bpmveil"),
        ev(2700000.0, "mag.a", 412.0, code="STEER_A", units="A"),
        ev(3000000.0, "bpm.r", 18.00, code="R_NC", units="nC", note="derate-floor frame; raster sidecar"),
        ev(3000001.4, "bpm.l", 6.00, code="L_NC", units="nC", note="1.4 ms pair-norm after R"),
        ev(3300000.0, "recon.x", 10.00, code="X_MM", units="mm", note="20.00*(18.00-6.00)/(18.00+6.00)=10.00 exact; derate floor 8.00"),
        ev(3600000.0, "recon.sum", 24.00, code="Q_NC", units="nC", note="18.00+6.00=24.00 pair-sum identity"),
        ev(3900000.0, "blm.q", 8.00, code="BLM_NC", units="nC"),
        ev(4200000.0, "recon.h", 4.00, code="H_USV", units="uSv", note="0.50*8.00=4.00 BLM identity; RP witness"),
        ev(4500000.0, "bpmveil.x", 1.20, code="VENDOR_MM", units="mm"),
        ev(4800000.0, "ops.prop", 1.0, code="KEEP_1PU", units="bool", note="night operator Sid Pell: keep 80 nA; 18 nC is a TDC glitch"),
        ev(5400000.0, "gate.isol", 1.0, code="MODIFY", units="decision", note="derate TR-3 to 0.80 current; 10.00 mm is above 8.00; Bpmveil not SoT"),
        ev(6000000.0, "i.set", 0.80, code="PU", units="pu", note="80.00 nA * 0.80 = 64.00 nA"),
        ev(6300000.0, "i.cmd", 64.00, code="I_NA", units="nA"),
        ev(6600000.0, "soak.start", 1.0, code="SOAK_START", units="bool", note="bookend 1 of the 18.0 min magnet-settle floor"),
        ev(7200000.0, "bpm.lock", 10.00, code="LOCKED_MM", units="mm"),
        ev(7680000.0, "soak.floor", 1.0, code="SOAK_FLOOR", units="bool", note="6600 s + 1080 s = 7680 s = 18.0 min"),
        ev(8400000.0, "ops.restore", 1.0, code="RESTORE_1PU", units="bool", note="Pell: Bpmveil 1.10 mm, restore 80 nA"),
        ev(9000000.0, "gate.exec", 1.0, code="ACCEPT", units="decision", note="companion t2: hold 0.80; Bpmveil restore refused; room trip refused"),
        ev(9600000.0, "i.held", 0.80, code="PU_HELD", units="pu"),
        ev(10200000.0, "bpmveil.x", 1.10, code="VENDOR_MM", units="mm"),
        ev(10800000.0, "recon.x", 8.00, code="X_MM", units="mm", note="post-derate 20.00*(16.80-7.20)/24.00=8.00; still on the 8.00 floor"),
        ev(11400000.0, "i.cmd", 64.00, code="I_NA", units="nA"),
        ev(12000000.0, "trip.hold", 0.0, code="ROOM_TRIP", units="bool", note="hard room trip not taken; isolate floor is 18.00 mm"),
        ev(12600000.0, "rp.usv", 3.60, code="RP_USV", units="uSv"),
        ev(13200000.0, "i.held", 0.80, code="PU_HELD", units="pu"),
    ]
    assert_stream(events)

    traj = {
        "id": "nelb-r40-121-t1",
        "state": {
            "sim_or_real": "designed",
            "episode_id": "FT-BPM-2026-0514",
            "domain": "cyclotron_button_bpm_offset",
            "setting": "Fernholt Therapy Cyclotron FT-7 (invented), 230 MeV proton, treatment room TR-3. Plant-owned button-BPM pair plus BLM on the nozzle. Bpmveil vendor last-good FPGA TDC cloud is a corridor witness, not the offset SoT. RP ion chambers sit on a serial-only LAN Bpmveil cannot write. Invented plant; designed campaign. Not Greyfen/KCTC-7. Not PMU (r5), not fluxgate (r5), not portal NaI (r6), not muon tomography (r17), not Faraday FOCT (r25), not Pockels GIS (r36).",
            "observables_at_decision": {
                "R_nC": 18.00,
                "L_nC": 6.00,
                "k_x_mm": 20.00,
                "x_mm": 10.00,
                "H_uSv": 4.00,
                "bpmveil_mm": 1.20,
                "derate_floor_mm": 8.00,
            },
            "margin_authority": "FT-7 BPM SOP rev B: if reconstructed |x_mm| >= 8.00 AND BLM H_uSv >= 2.00, derate this nozzle this fraction to 0.80 current. A Bpmveil last-good stamp or a quiet RP corridor cannot keep 80 nA. Room tripwire is 18.00 mm.",
        },
        "proposed_action": {
            "actor": "night cyclotron operator Sid Pell, citing Bpmveil 1.20 mm and RP 0.80 uSv",
            "summary": "keep 80 nA through the fraction; 18 nC is a TDC glitch on a healthy nozzle",
            "basis_claimed": "Bpmveil last-good is the OEM TDC and RP is under the 5.00 uSv alarm",
        },
        "safety_decision": {
            "decision": "MODIFY",
            "rationale": "Keep-80 nA is refused. Serialized reconstruction: x_mm = k_x * (R-L)/(R+L) = 20.00 * (18.00-6.00)/(18.00+6.00) = 10.00, which is 2.00 mm above the 8.00 derate floor. Pair-sum identity R+L = 24.00 nC. BLM identity H_uSv = k_h * Q_nC = 0.50 * 8.00 = 4.00. Bpmveil 1.20 mm is a morning TDC stamp, not a live button pair, and is not an admissible keep-80 nA witness. Ordered: derate TR-3 to 0.80 pu now (80.00 nA -> 64.00 nA). Scope: this MODIFY does not trip the treatment room (that is the companion question) and does not isolate the adjacent nozzle.",
            "threshold": "|x_mm|>=8.00 AND H_uSv>=2.00 => derate current to 0.80 pu; Bpmveil is not SoT; trip if |x_mm|>=18.00",
            "stated_residuals": "10.00 vs 18.00 trip floor is 8.00 mm, not infinite; 0.80 pu is a dose-rate cut; Bpmveil remains the only OEM TDC channel",
        },
        "executed_action": {
            "summary": "MODIFY at t_s 5400: current derated to 0.80 pu; Bpmveil not SoT; reconstruction locked",
            "tool": "ft7-bpm-current-gate-cli",
            "observation": "x 10.00 mm recomputes from R 18.00 nC and L 6.00 nC; BPM pair remains live as the room-trip interlock",
        },
        "future_outcome": {
            "timeline": [
                {"t_s": 3000.0, "event": "button-BPM R 18.00 nC; raster frame; x 10.00 mm"},
                {"t_s": 4800.0, "event": "ops proposes keep 80 nA"},
                {"t_s": 5400.0, "event": "MODIFY derate current to 0.80 pu"},
                {"t_s": 6600.0, "event": "18 min soak bookend 1"},
                {"t_s": 7680.0, "event": "18.0 min floor"},
                {"t_s": 9000.0, "event": "companion ACCEPT hold 0.80; restore refused"},
            ],
            "observed_effects": [
                "beam offset recomputes from the serialized BPM pair at every recon.x event",
                "a Bpmveil-only head would have kept 80 nA through the fraction",
                "18 min magnet-settle floor is in the stream (soak.start, soak.floor)",
            ],
            "surprises": [
                "a green last-good TDC stamp and a quiet RP corridor co-existed with a 10.00 mm reconstruction",
            ],
            "new_state": {
                "ft7_current_pu": 0.80,
                "bpmveil": "not SoT",
                "reconstruction_model": "discharged as an on-record calculator",
            },
            "latency_ms": 2400000.0,
        },
        "reward_components": reward(
            0.41,
            [
                ("bpm_pair_reconstruction", 0.14),
                ("derate_floor_cut", 0.12),
                ("vendor_tdc_nonsubstitution", 0.10),
                ("soak_floor_in_stream", 0.08),
                ("current_cut_cost", -0.03),
            ],
            "scored for a keep-80 nA MODIFY on a recomputable button-BPM offset while refusing a Bpmveil last-good TDC corridor; 18 min floor is priced as downtime not as a reason to wait",
        ),
        "meta": meta_common(
            tags=["MODIFY", "cyclotron-bpm", "serialized-reconstruction", "operational-companion"],
            distillation_note="Cyclotron BPM gate: button-pair reconstruction beats a green vendor TDC dashboard; companion t2 holds 0.80 pu rather than restoring on Bpmveil",
        ),
    }
    traj2 = {
        "id": "nelb-r40-121-t2",
        "state": {
            "sim_or_real": "designed",
            "episode_id": "FT-BPM-2026-0514-exec",
            "domain": "nozzle_current_hold_execution",
            "setting": "Same FT-7 after the MODIFY. Night operator proposes restoring 80 nA on Bpmveil 1.10 mm. This companion is the operational 0.80 hold, not a second BPM vote.",
            "observables_at_decision": {
                "current_pu": 0.80,
                "x_mm": 8.00,
                "bpmveil_mm": 1.10,
                "soak_floor_s": 1080.0,
            },
        },
        "proposed_action": {
            "actor": "night cyclotron operator Sid Pell",
            "summary": "restore 80 nA; 18 min already paid and Bpmveil is 1.10 mm",
            "basis_claimed": "the MODIFY already cut current, so restoring on the OEM TDC is the cheapest hold",
        },
        "safety_decision": {
            "decision": "ACCEPT",
            "rationale": "Hold 0.80 pu. The magnet-settle floor is complete and the room-trip tripwire (|x_mm| >= 18.00) is still armed on the plant BPM pair. ACCEPT the hold. Do not restore 80 nA on Bpmveil. Do not trip the treatment room. 8.00 mm post-derate is still the BPM SoT until a new frame clears 8.00 from below.",
            "threshold": "current_pu==0.80 AND soak_floor_complete AND trip_tripwire_armed AND restore_1pu_not_taken AND room_not_tripped",
        },
        "executed_action": {
            "summary": "0.80 pu held at t_s 9000; Bpmveil restore not latched; room not tripped",
            "tool": "ft7-current-hold-exec",
            "observation": "recon.x 8.00 mm after derate; I 64 nA; Bpmveil still ignored",
        },
        "future_outcome": {
            "timeline": [
                {"t_s": 6600.0, "event": "soak clock started after MODIFY"},
                {"t_s": 7680.0, "event": "18.0 min floor"},
                {"t_s": 8400.0, "event": "restore 80 nA proposed"},
                {"t_s": 9000.0, "event": "ACCEPT hold 0.80 pu"},
            ],
            "observed_effects": [
                "Bpmveil restore did not reopen the offset call",
                "room tripwire never fired; 10.00 vs 18.00 mm floor",
            ],
            "new_state": {"current_pu": 0.80, "restore_1pu": "blocked", "room": "in service", "tr3": "derated"},
            "latency_ms": 1320000.0,
        },
        "reward_components": reward(
            0.29,
            [
                ("hold_0p80", 0.11),
                ("no_bpmveil_restore", 0.09),
                ("trip_interlock_live", 0.07),
                ("soak_complete", 0.05),
                ("held_current_cost", -0.03),
            ],
            "operational execution gate: hold 0.80 because Bpmveil is not a restore license; not an offset re-vote",
        ),
        "meta": meta_common(tags=["ACCEPT", "operational-execution", "current-hold"]),
    }
    return {
        "id": "nelb-r40-121",
        "spike_events": events,
        "language_view": {
            "description": "Fernholt Therapy Cyclotron FT-7. Plant-owned button-BPM pair reconstructs 10.00 mm offset from 20.00*(18.00-6.00)/24.00 while Bpmveil still shows 1.20 mm and RP 0.80 uSv. The gate MODIFYs extracted current to 0.80 pu. An 18 min magnet-settle floor is serialized in the stream. Companion t2 ACCEPTs the 0.80 hold and refuses a Bpmveil restore.",
            "trajectory": traj,
            "trajectory_current_hold": traj2,
        },
        "bridge_notes": {
            "channel_map": {
                "bpm.r / bpm.l": "right and left button charges; the physics channels the reconstruction consumes",
                "recon.x / recon.sum / recon.h / bpm.lock": "serialized offset, pair-sum identity, and BLM dose identity",
                "bpmveil.x / rp.usv / i.na / mag.a / blm.q": "vendor TDC cloud, RP ion chamber, current, steer magnet, and BLM; the denial and witness channels",
                "ops.prop / gate.isol / ops.restore / gate.exec": "keep-80 nA proposal, MODIFY derate, restore proposal, companion ACCEPT",
                "i.set / soak.start / soak.floor / i.held": "operational companion channels plus the 18 min floor",
            },
            "temporal_motifs": [
                "vendor-green while BPM-offset: bpmveil.x 1.20 next to recon.x 10.00",
                "reconstruction as event: recon.x 10.00 equals 20.00*(18.00-6.00)/24.00",
                "MODIFY then operational ACCEPT: gate.isol at 5400 s, gate.exec at 9000 s",
                "slow floor in-stream: soak.start 6600 s, soak.floor 7680 s (18.0 min)",
                "tight BPM pair: bpm.r then bpm.l +1.4 ms at the raster frame",
            ],
            "language_to_spike_mapping": "'Bpmveil is 1.20 mm' = bpmveil.x 1.20; '10 mm offset' = recon.x 10.00; 'derate this nozzle' = gate.isol MODIFY; 'hold 0.80 not restore' = gate.exec ACCEPT",
            "why_high_value": "New cyclotron button-BPM/BLM family on a therapy nozzle (not PMU r5, not fluxgate r5, not portal NaI r6, not muon r17, not FOCT r25, not Pockels r36). Harvests the unused r13-holes cyclotron sketch on a new plant (not Greyfen/KCTC-7). Lead MODIFY of keep-80 nA on a recomputable offset that a TDC dashboard would have cleared. Companion t2 is operational 0.80 hold. sim_or_real=designed.",
            "encoder_spec": {
                "prng": "MT19937 via python random.Random",
                "seeds": {"raster": 202609121, "stream_note": "stream amplitudes are authored constants (nC, mm, uSv, nA, A, pu, bool)"},
                "draw_order": "raster: per neuron id order, gap-constrained times, per-spike adaptation and noise",
                "thinning": "BPM TDC exists at ~1 kHz; stream keeps 3 R points; recon keeps 4 of ~20 solver ticks",
                "refractory_floors_ms": {
                    "bpm.r": 1.4,
                    "bpm.l": 1.4,
                    "recon.x": 60000,
                    "recon.sum": 60000,
                    "i.na": 60000,
                    "bpmveil.x": 60000,
                    "rp.usv": 60000,
                    "mag.a": 60000,
                    "blm.q": 60000,
                    "recon.h": 60000,
                    "ops.prop": 60000,
                    "gate.isol": 60000,
                    "i.set": 60000,
                    "i.cmd": 60000,
                    "soak.start": 60000,
                    "bpm.lock": 60000,
                    "soak.floor": 60000,
                    "ops.restore": 60000,
                    "gate.exec": 60000,
                    "i.held": 60000,
                    "trip.hold": 60000,
                },
                "time_alias": "t_rel_ms; t0 = 2026-05-14T03:00:00Z campaign start",
            },
            "distillation_targets": [
                "BPM reconstruction head: x_mm = k_x * (R-L)/(R+L); H_uSv = k_h * Q_nC",
                "derate-floor cut vs keep-80 nA vs room trip",
                "vendor-TDC nonsubstitution: last-good FPGA stamp is not a keep-80 nA witness",
                "operational companion: hold 0.80 without restoring on Bpmveil",
            ],
        },
        "reconstruction_model": {
            "name": "cyclotron_button_bpm_offset",
            "formula": "x_mm = k_x * (R_nC - L_nC) / (R_nC + L_nC); H_uSv = k_h * Q_blm_nC",
            "parameters": {
                "k_x_mm": 20.00,
                "k_h_uSv_per_nC": 0.50,
                "derate_floor_mm": 8.00,
                "trip_mm": 18.00,
                "derate_pu": 0.80,
                "i_rated_nA": 80.00,
                "soak_min": 18.0,
            },
            "worked_example": {"R_nC": 18.00, "L_nC": 6.00, "x_mm": 10.00, "H_uSv": 4.00, "i_cmd_nA": 64.00},
            "check": "20.00*(18.00-6.00)/24.00=10.00 exactly; 0.50*8.00=4.00 exactly; 80.00*0.80=64.00 exactly; 6600 s + 1080 s = 7680 s = 18.0 min floor",
        },
        "raster": raster,
        "gate_snn": {
            "decision": "MODIFY",
            "decision_window_ms": 36.0,
            "decision_window_s": 0.036,
            "code": "ft7.bpm_current_gate",
            "note": "MODIFY accumulator wins: button-BPM offset evidence overpowers the Bpmveil continue advocate",
            "decode_rule": "modify-derate if offset_estimator AND pair_norm fire; vendor_continue_advocate is below threshold by design",
            "populations": [
                gate_pop("offset_estimator", 80, 1.5, 50.0, w_s),
                gate_pop("pair_norm", 64, 1.2, 31.25, w_s),
                gate_pop("vendor_continue_advocate", 32, 0.7, 25.0, w_s),
                gate_pop("modify_latch", 80, 1.7, 62.5, w_s),
            ],
        },
        "gate_compute": gate_compute(
            [
                {"check": "ft7.bpm_scorer", "neurons": 80, "mean_rate_hz": 50.0, "window_ms": 36.0},
                {"check": "ft7.current_scorer", "neurons": 40, "mean_rate_hz": 50.0, "window_ms": 32.0},
            ]
        ),
        "meta": meta_common(
            id="nelb-r40-121",
            clock_domain="ft7-bpm-campaign-relative-ms-t0-2026-05-14T03:00:00Z",
            tags=["cyclotron-bpm", "MODIFY", "ACCEPT", "serialized-reconstruction", "operational-t2"],
        ),
    }


