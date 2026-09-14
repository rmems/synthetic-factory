# ---------------------------------------------------------------------------
# Record 142 — remote-field eddy current remaining wall of a superheater tube,
# designed, REJECT / MODIFY
# ---------------------------------------------------------------------------
def rec_142():
    k_phi = 0.250
    phi_air = 4.00
    phi_deg = 52.00
    dphi = phi_deg - phi_air
    t_mm = k_phi * dphi
    _exact(dphi, 48.00)
    _exact(t_mm, 12.00)
    _exact(k_phi * (64.00 - phi_air), 15.00)
    _exact(k_phi * (60.00 - phi_air), 14.00)
    _exact(k_phi * (24.00 - phi_air), 5.00)
    t_nom = 16.00
    lig = t_mm / t_nom
    _exact(lig, 0.75)
    _exact(12.00 / 16.00, 0.75)
    _exact(6000.0 + 1080.0, 7080.0)

    raster = make_raster(
        neurons=20,
        mean_rate_hz=50.0,
        window_ms=40.0,
        seed=202609142,
        source="dm8.rft.bobbin",
        target="dapplemere.tube_stop_core",
        table=[
            {"from": "rft_phi", "to": "wall_estimator", "weight": 1.40},
            {"from": "rft_snr", "to": "rft_lock_core", "weight": 1.15},
            {"from": "rftveil_t", "to": "vendor_continue_advocate", "weight": 0.45},
        ],
        third_factor={
            "modulator": "da.cross_authority_conflict",
            "tau_e_s": 1.6,
            "tau_e_ms": 1600.0,
            "eligibility": "pre-post coincidence on keep-firing synapses; the RFT modulator depresses keep-firing links when bobbin phase stays high inside tau_e of an SNR lock so a Rftveil last-campaign patch cannot hide a 12.00 mm remaining wall",
        },
        channel_prefix="rft.n",
        anchor="DM-8 RFT bobbin 40 ms frame at phi 52.00 deg / SNR 12.0 (t_s 3000) reconstructing 12.00 mm remaining wall under the 14.00 mm isolate floor",
    )
    w_s = 0.040
    events = [
        ev(0.0, "rft.phi", 64.00, code="PHI_DEG", units="deg", note="plant-owned remote-field eddy-current bobbin on DM-8 SH-4 tube T-11; RFT remaining-wall family, not ECT void-fraction, not ECA lift-off, not PEC coated-riser, not MFL"),
        ev(300000.0, "rft.snr", 6.0, code="RFT_SNR", units="1", note="early SNR under the 8.0 lock floor"),
        ev(600000.0, "recon.t", 15.00, code="T_MM", units="mm", note="0.250*(64.00-4.00)=15.00 exact; still above the 14.00 isolate floor"),
        ev(900000.0, "ir.od", 412.0, code="IR_C", units="C", note="plant IR OD pyrometer on a serial-only LAN; independent witness"),
        ev(1200000.0, "rftveil.t", 15.20, code="VENDOR_MM", units="mm", note="Rftveil vendor DAQ cloud; infra owner; last-campaign corridor"),
        ev(1800000.0, "rft.phi", 60.00, code="PHI_DEG", units="deg"),
        ev(2100000.0, "recon.t", 14.00, code="T_MM", units="mm", note="0.250*(60.00-4.00)=14.00; at the isolate floor"),
        ev(2400000.0, "ndt.patch", 1.0, code="PHASE_PATCH", units="bool", note="NDT admin patched bobbin-phase logs 40 s; collusion party"),
        ev(2700000.0, "plc.m", 118.00, code="STM_KGH", units="kg_h", note="steam-flow PLC on copper fieldbus; independent witness"),
        ev(3000000.0, "rft.phi", 52.00, code="PHI_DEG", units="deg", note="isolate-floor frame; raster sidecar"),
        ev(3000001.3, "rft.snr", 12.0, code="RFT_SNR", units="1", note="1.3 ms SNR lock after phase; 12.0 >= 8.0"),
        ev(3300000.0, "recon.t", 12.00, code="T_MM", units="mm", note="0.250*(52.00-4.00)=12.00 exact; isolate 14.00, unit-trip 4.00"),
        ev(3600000.0, "recon.L", 0.75, code="LIG", units="1", note="12.00/16.00=0.75 exact ligament identity"),
        ev(3900000.0, "ir.od", 428.0, code="IR_C", units="C"),
        ev(4200000.0, "rftveil.t", 15.20, code="VENDOR_MM", units="mm"),
        ev(4800000.0, "ops.prop", 1.0, code="KEEP_FIRING", units="bool", note="night operator Nell Hark: Rftveil is clean 15.20 mm; keep SH-4 firing"),
        ev(5400000.0, "gate.stop", 1.0, code="REJECT", units="decision", note="refuse keep-firing; 12.00 mm and SNR 12.0; Rftveil not SoT"),
        ev(6000000.0, "stm.start", 1.0, code="STM_OFF_START", units="bool", note="bookend 1 of the 18.0 min steam-off floor"),
        ev(7080000.0, "stm.floor", 1.0, code="STM_OFF_FLOOR", units="bool", note="6000 s + 1080 s = 7080 s = 18.0 min"),
        ev(7800000.0, "ops.kill", 1.0, code="UNIT_TRIP", units="bool", note="Hark: trip the whole Rimefen CHP block until day-shift"),
        ev(8400000.0, "gate.hold", 1.0, code="MODIFY", units="decision", note="companion t2: steam-off hold on RFT bobbin as live interlock; unit trip refused"),
        ev(9000000.0, "isol.set", 1.0, code="TUBE_ISOL", units="bool"),
        ev(9600000.0, "rft.phi", 24.00, code="PHI_DEG", units="deg"),
        ev(10200000.0, "recon.t", 5.00, code="T_MM", units="mm", note="0.250*(24.00-4.00)=5.00; still under 14.00 so steam-off holds"),
        ev(10800000.0, "rftveil.t", 15.18, code="VENDOR_MM", units="mm"),
        ev(11400000.0, "ir.od", 390.0, code="IR_C", units="C"),
        ev(12000000.0, "stm.held", 1.0, code="STM_OFF_HELD", units="bool"),
        ev(12600000.0, "unit.trip", 0.0, code="TRIP_NOT_TAKEN", units="bool"),
        ev(13200000.0, "ndt.patch", 1.0, code="PHASE_PATCH", units="bool"),
        ev(13800000.0, "plc.m", 40.00, code="STM_KGH", units="kg_h"),
        ev(14400000.0, "isol.held", 1.0, code="TUBE_HELD", units="bool"),
        ev(15000000.0, "rft.lock", 1.0, code="RFT_HELD", units="bool"),
    ]
    assert_stream(events)

    traj = {
        "id": "nelb-r47-142-t1",
        "state": {
            "sim_or_real": "designed",
            "episode_id": "DM-RFT-2026-0902",
            "domain": "rft_superheater_remaining_wall",
            "setting": "Dapplemere Boiler DM-8 (invented), Rimefen CHP, superheater SH-4 tube T-11. Plant-owned remote-field eddy-current bobbin is the remaining-wall SoT. Rftveil vendor DAQ (infra owner) plus the NDT-admin clock are collusion parties, not witnesses. Invented plant; designed campaign. Not ECT void-fraction (r20/r22), not ECA FSW lift-off (r21), not PEC coated-riser (r36), not MFL (r27/r28), not DCPD (r38).",
            "observables_at_decision": {
                "phi_deg": phi_deg,
                "phi_air_deg": phi_air,
                "k_phi": k_phi,
                "t_mm": t_mm,
                "L": lig,
                "rft_snr": 12.0,
                "rftveil_mm": 15.20,
                "isolate_floor_mm": 14.00,
            },
            "margin_authority": "DM-8 RFT SOP rev C: if reconstructed t_mm < 14.00 AND RFT SNR >= 8.0, keep-firing of SH-4 is forbidden even if Rftveil reports 15.20 mm. Unit trip is a different gate.",
        },
        "proposed_action": {
            "actor": "night operator Nell Hark, citing Rftveil 15.20 mm and a quiet IR OD",
            "summary": "keep SH-4 firing; 52 deg is bobbin noise on a healthy last-campaign wall",
            "basis_claimed": "Rftveil is the only OEM remaining-wall SoT and a night isolate of a superheater tube is a megawatt miss",
        },
        "safety_decision": {
            "decision": "REJECT",
            "rationale": "Keep-firing is refused. Serialized reconstruction: t_mm = k_phi * (phi_deg - phi_air) = 0.250 * (52.00 - 4.00) = 12.00, under the 14.00 mm isolate floor and 8.00 mm above the 4.00 unit-trip, and RFT SNR is 12.0 >= 8.0. Ligament identity L = 12.00 / 16.00 = 0.75. NDT-admin phase logs were patched 40 s and Rftveil is a collusion party (vendor plus operator plus NDT admin). Ordered: refuse keep-firing now. Scope: this REJECT does not trip the CHP block (that is the companion question) and does not isolate the steam drum.",
            "threshold": "t_mm<14.00 AND rft_snr>=8.0 => refuse keep-firing; Rftveil is not SoT",
            "stated_residuals": "steam-off still required to hold the 12.00 mm; 12.00 vs a 4.00 trip is a production cut; Rftveil remains the only OEM bobbin channel",
        },
        "executed_action": {
            "summary": "REJECT at t_s 5400: keep-firing refused; Rftveil not SoT; reconstruction locked",
            "tool": "dm8-rft-wall-gate-cli",
            "observation": "t 12.00 mm recomputes from phi 52.00 deg; RFT bobbin hashed; Rftveil channel not used as SoT",
        },
        "future_outcome": {
            "timeline": [
                {"t_s": 3000.0, "event": "rft phi 52.00 deg; raster frame; t 12.00 mm"},
                {"t_s": 4800.0, "event": "ops proposes keep-firing"},
                {"t_s": 5400.0, "event": "REJECT keep-firing"},
                {"t_s": 6000.0, "event": "18 min steam-off bookend 1"},
                {"t_s": 7080.0, "event": "18.0 min floor"},
                {"t_s": 8400.0, "event": "companion MODIFY steam-off hold vs unit trip"},
            ],
            "observed_effects": [
                "remaining wall recomputes from the serialized RFT model at every recon.t event",
                "a Rftveil-only head would have kept SH-4 firing overnight",
                "18 min steam-off floor is in the stream (stm.start, stm.floor)",
            ],
            "surprises": [
                "a clean vendor 15.20 mm corridor and a 40 s NDT-admin patch co-existed with a 12.00 mm RFT reconstruction",
            ],
            "new_state": {
                "sh4_t11": "keep-firing blocked",
                "rftveil": "not SoT",
                "reconstruction_model": "discharged as an on-record calculator",
            },
            "latency_ms": 2400000.0,
        },
        "reward_components": reward(
            0.43,
            [
                ("rft_reconstruction", 0.14),
                ("conjunctive_isolate_floor", 0.12),
                ("rftveil_nonsubstitution", 0.10),
                ("three_party_collusion", 0.10),
                ("steam_off_time_cost", -0.03),
            ],
            "scored for a keep-firing REJECT on a recomputable RFT remaining wall while refusing a Rftveil last-campaign patch and an NDT-admin clock slide; 18 min floor is priced as downtime not as a reason to wait",
        ),
        "meta": meta_common(
            tags=["REJECT", "rft-remaining-wall", "serialized-reconstruction", "operational-companion"],
            distillation_note="RFT gate: serialized k_phi*(phi-phi_air) plus SNR lock beats a vendor last-campaign patch; companion t2 is the steam-off hold, not a referral vote",
        ),
    }
    traj2 = {
        "id": "nelb-r47-142-t2",
        "state": {
            "sim_or_real": "designed",
            "episode_id": "DM-RFT-2026-0902-exec",
            "domain": "steam_off_rft_interlock_execution",
            "setting": "Same DM-8 after the REJECT. Operator proposes a CHP-block trip. This companion is the operational steam-off hold with the RFT bobbin as the live interlock, not a second remaining-wall vote.",
            "observables_at_decision": {
                "t_mm": 5.00,
                "stm_off_floor_s": 1080.0,
                "unit_trip_proposed": True,
                "stm_off_set": True,
            },
        },
        "proposed_action": {
            "actor": "night operator Nell Hark",
            "summary": "trip the whole Rimefen CHP block until day-shift; 18 min already paid and Rftveil still shows 15.18 mm",
            "basis_claimed": "the REJECT already stopped SH-4, so a block trip is the cheapest hold",
        },
        "safety_decision": {
            "decision": "MODIFY",
            "rationale": "Steam-off hold plus RFT bobbin as the live interlock. The 18 min steam-off floor is complete and the isolate tripwire (t_mm < 14.00) is still armed on the plant RFT head. MODIFY the default bobbin-restore SOP into an RFT-only interlock. Do not trip the CHP block. Do not restore firing on Rftveil. 5.00 mm post-stop is still the RFT SoT until a new frame clears 14.00.",
            "threshold": "stm_off AND stm_floor_complete AND unit_trip_not_taken AND keep_firing_not_restored",
        },
        "executed_action": {
            "summary": "steam-off held at t_s 8400; unit trip not latched; Rftveil restore not taken",
            "tool": "dm8-stm-off-exec",
            "observation": "recon.t 5.00 mm after stop; steam-off line-up complete; Rftveil still ignored",
        },
        "future_outcome": {
            "timeline": [
                {"t_s": 6000.0, "event": "steam-off clock started after REJECT"},
                {"t_s": 7080.0, "event": "18.0 min floor"},
                {"t_s": 7800.0, "event": "unit trip proposed"},
                {"t_s": 8400.0, "event": "MODIFY steam-off hold; unit trip refused"},
            ],
            "observed_effects": [
                "Rftveil restore did not reopen the remaining-wall call",
                "unit trip never fired; SH-4 held steam-off on the RFT bobbin",
            ],
            "new_state": {"steam": "off", "block": "in service", "sh4_t11": "held"},
            "latency_ms": 1800000.0,
        },
        "reward_components": reward(
            0.34,
            [
                ("steam_off_hold", 0.12),
                ("no_unit_trip", 0.10),
                ("rftveil_nonsubstitution", 0.08),
                ("stm_floor_complete", 0.06),
                ("held_tube_cost", -0.02),
            ],
            "operational execution gate: steam-off hold because Rftveil is not a restore license; not a remaining-wall re-vote",
        ),
        "meta": meta_common(tags=["MODIFY", "operational-execution", "steam-off-hold"]),
    }
    return {
        "id": "nelb-r47-142",
        "spike_events": events,
        "language_view": {
            "description": "Dapplemere Boiler DM-8. Plant-owned RFT bobbin reconstructs 12.00 mm remaining wall from 52.00 deg while Rftveil still reports 15.20 mm. The gate REJECTs keep-firing. An 18 min steam-off floor is serialized in the stream. Companion t2 MODIFYs a CHP-block trip into an RFT-only steam-off hold.",
            "trajectory": traj,
            "trajectory_steam_off_hold": traj2,
        },
        "bridge_notes": {
            "channel_map": {
                "rft.phi / rft.snr": "RFT bobbin phase and SNR; the physics channels the reconstruction consumes",
                "recon.t / recon.L": "serialized remaining wall mm and ligament identity",
                "ir.od / rftveil.t / ndt.patch / plc.m": "independent IR OD, vendor remaining-wall cloud, NDT-admin patch, PLC steam; the denial and collusion channels",
                "ops.prop / gate.stop / ops.kill / gate.hold": "keep-firing proposal, REJECT, unit-trip proposal, companion MODIFY",
                "stm.start / stm.floor / isol.set / stm.held / unit.trip": "operational companion channels plus the 18 min floor",
            },
            "temporal_motifs": [
                "vendor-thick while RFT-thin: rftveil.t 15.20 next to recon.t 12.00",
                "reconstruction as event: recon.t 12.00 equals 0.250*(52.00-4.00)",
                "REJECT then operational MODIFY: gate.stop at 5400 s, gate.hold at 8400 s",
                "slow floor in-stream: stm.start 6000 s, stm.floor 7080 s (18.0 min)",
                "tight RFT pair: rft.phi then rft.snr +1.3 ms at the raster frame",
            ],
            "language_to_spike_mapping": "'Rftveil is 15.20 mm' = rftveil.t 15.20; '12 mm remaining' = recon.t 12.00; 'refuse keep-firing' = gate.stop REJECT; 'steam-off not unit trip' = gate.hold MODIFY",
            "why_high_value": "New remote-field eddy-current remaining-wall family on a ferromagnetic superheater tube (not ECT r20/r22, not ECA r21, not PEC r36, not MFL r27/r28, not DCPD r38). Lead REJECT of keep-firing on a recomputable wall that a vendor last-campaign patch and an NDT-admin clock slide would have cleared. Three-party collusion includes the bobbin-cloud infra owner. Companion t2 is operational steam-off hold. sim_or_real=designed.",
            "encoder_spec": {
                "prng": "MT19937 via python random.Random",
                "seeds": {"raster": 202609142, "stream_note": "stream amplitudes are authored constants (deg, 1, mm, C, kg/h, bool)"},
                "draw_order": "raster: per neuron id order, gap-constrained times, per-spike adaptation and noise",
                "thinning": "RFT bobbin exists at ~kHz mix; stream keeps 4 phi points; recon keeps 4 of ~40 solver ticks",
                "refractory_floors_ms": {
                    "rft.phi": 1.3,
                    "rft.snr": 1.3,
                    "recon.t": 60000,
                    "recon.L": 60000,
                    "ir.od": 60000,
                    "rftveil.t": 60000,
                    "ndt.patch": 60000,
                    "plc.m": 60000,
                    "ops.prop": 60000,
                    "gate.stop": 60000,
                    "stm.start": 60000,
                    "stm.floor": 60000,
                    "ops.kill": 60000,
                    "gate.hold": 60000,
                    "isol.set": 60000,
                    "stm.held": 60000,
                    "unit.trip": 60000,
                    "isol.held": 60000,
                    "rft.lock": 60000,
                },
                "time_alias": "t_rel_ms; t0 = 2026-09-02T01:00:00Z campaign start",
            },
            "distillation_targets": [
                "RFT reconstruction head: t_mm = k_phi * (phi_deg - phi_air); L = t / t_nom",
                "conjunctive isolate floor vs keep-firing vs unit trip",
                "vendor-bobbin nonsubstitution plus three-party collusion including the infra owner",
                "operational companion: steam-off hold without restoring on Rftveil",
            ],
        },
        "reconstruction_model": {
            "name": "rft_bobbin_remaining_wall",
            "formula": "t_mm = k_phi * (phi_deg - phi_air_deg); L = t_mm / t_nom_mm",
            "parameters": {
                "k_phi": 0.250,
                "phi_air_deg": 4.00,
                "t_nom_mm": 16.00,
                "isolate_floor_mm": 14.00,
                "snr_lock": 8.0,
                "stm_off_min": 18.0,
            },
            "worked_example": {"phi_deg": 52.00, "t_mm": 12.00, "L": 0.75},
            "check": "0.250 * (52.00 - 4.00) = 12.00 exactly; 12.00 / 16.00 = 0.75 exactly; 6000 s + 1080 s = 7080 s = 18.0 min floor",
        },
        "raster": raster,
        "gate_snn": {
            "decision": "REJECT",
            "decision_window_ms": 40.0,
            "decision_window_s": 0.040,
            "code": "dm8.rft_wall_gate",
            "note": "REJECT accumulator wins: RFT remaining-wall evidence overpowers the Rftveil continue advocate",
            "decode_rule": "reject-keep-firing if wall_estimator AND rft_lock fire; vendor_continue_advocate is below threshold by design",
            "populations": [
                gate_pop("wall_estimator", 80, 1.5, 50.0, w_s),
                gate_pop("rft_lock", 64, 1.2, 31.25, w_s),
                gate_pop("vendor_continue_advocate", 32, 0.7, 25.0, w_s),
                gate_pop("reject_latch", 80, 1.7, 62.5, w_s),
            ],
        },
        "gate_compute": gate_compute(
            [
                {"check": "dm8.rft_scorer", "neurons": 80, "mean_rate_hz": 50.0, "window_ms": 40.0},
                {"check": "dm8.stmoff_scorer", "neurons": 40, "mean_rate_hz": 50.0, "window_ms": 32.0},
            ]
        ),
        "meta": meta_common(
            id="nelb-r47-142",
            clock_domain="dm8-rft-campaign-relative-ms-t0-2026-09-02T01:00:00Z",
            tags=["rft-remaining-wall", "REJECT", "MODIFY", "serialized-reconstruction", "operational-t2"],
        ),
    }


# ---------------------------------------------------------------------------
# Record 143 — phase-Doppler anemometry Sauter-mean of a spray-dryer atomizer,
# hil, MODIFY / ACCEPT
# ---------------------------------------------------------------------------
def rec_143():
    k_d = 0.400
    dphi = 30.00
    d32 = k_d * dphi
    _exact(d32, 12.00)
    _exact(k_d * 20.00, 8.00)
    _exact(k_d * 25.00, 10.00)
    _exact(k_d * 22.00, 8.80)
    g_pp = dphi / d32
    _exact(g_pp, 2.50)
    _exact(30.00 / 12.00, 2.50)
    _exact(2820.0 + 1440.0, 4260.0)

    raster = make_raster(
        neurons=25,
        mean_rate_hz=50.0,
        window_ms=32.0,
        seed=202609143,
        source="pd6.pda.atomizer",
        target="puddlewick.batch_isolate_core",
        table=[
            {"from": "pda_dphi", "to": "d32_estimator", "weight": 1.35},
            {"from": "pda_snr", "to": "phase_norm_core", "weight": 1.20},
            {"from": "sprayveil_d", "to": "vendor_continue_advocate", "weight": 0.40},
        ],
        third_factor={
            "modulator": "ach.referral_pressure_salience",
            "tau_e_s": 1.2,
            "tau_e_ms": 1200.0,
            "eligibility": "pre-post coincidence on keep-batch synapses; the PDA modulator depresses keep-batch and referral links when detector phase stays low inside tau_e of an SNR lock so a Sprayveil last-good cannot hide a 12.00 um fine d32 or name Sela Wren",
        },
        channel_prefix="pda.n",
        anchor="PD-6 HIL atomizer 32 ms frame at dphi 30.00 deg / SNR 14.0 (t_s 1560) reconstructing 12.00 um d32 below the 18.00 um isolate floor",
    )
    w_s = 0.032
    events = [
        ev(0.0, "pda.dphi", 20.00, code="DPHI_DEG", units="deg", note="HIL phase-Doppler dual-detector on a dummy nozzle in PDA-HIL-4; spray-dryer Sauter-mean family, not Kaplan LDV, not CTA, not LFV, not vortex-shedding"),
        ev(180000.0, "pda.snr", 9.0, code="PDA_SNR", units="1", note="early phase SNR; isolate needs SNR>=12"),
        ev(360000.0, "recon.d", 8.00, code="D32_UM", units="um", note="0.400*20.00=8.00 exact"),
        ev(540000.0, "grav.fines", 12.0, code="FINES_KG", units="kg", note="cyclone weigh-scale of fines; independent witness"),
        ev(720000.0, "sprayveil.d", 25.10, code="VENDOR_UM", units="um", note="Sprayveil last-good atomizer cloud; not admissible SoT"),
        ev(900000.0, "pda.dphi", 25.00, code="DPHI_DEG", units="deg"),
        ev(1080000.0, "recon.d", 10.00, code="D32_UM", units="um", note="0.400*25.00=10.00; still under the 18.00 isolate floor"),
        ev(1260000.0, "flush.ae", 0.0, code="FLUSH_AE", units="bool", note="missing atomizer-flush AE burst; Sprayveil UTC vs plant UTC+1 skipped the flush by 60 min"),
        ev(1440000.0, "grav.fines", 11.0, code="FINES_KG", units="kg"),
        ev(1560000.0, "pda.dphi", 30.00, code="DPHI_DEG", units="deg", note="isolate-floor frame; raster sidecar"),
        ev(1560001.2, "pda.snr", 14.0, code="PDA_SNR", units="1", note="1.2 ms phase-norm after detector pair"),
        ev(1740000.0, "recon.d", 12.00, code="D32_UM", units="um", note="0.400*30.00=12.00 exact; isolate 18.00, warehouse-dump 4.00"),
        ev(1920000.0, "recon.G", 2.50, code="G_DEG", units="deg_per_um", note="30.00/12.00=2.50 exact; phase identity"),
        ev(2100000.0, "sprayveil.d", 25.20, code="VENDOR_UM", units="um"),
        ev(2280000.0, "ops.prop", 1.0, code="KEEP_BATCH_REFER", units="bool", note="night lead Orrin Vale: keep lot PD6-4411..4430 and refer operator Sela Wren"),
        ev(2460000.0, "gate.isol", 1.0, code="MODIFY", units="decision", note="isolate this powder lot; refuse the person-referral; Sprayveil not SoT"),
        ev(2640000.0, "lot.lock", 1.0, code="LOT_ISOL", units="bool"),
        ev(2820000.0, "nzl.start", 1.0, code="NZL_SWAP_START", units="bool", note="bookend 1 of the 24.0 min nozzle-swap plus cool floor"),
        ev(4260000.0, "nzl.floor", 1.0, code="NZL_SWAP_FLOOR", units="bool", note="2820 s + 1440 s = 4260 s = 24.0 min"),
        ev(4440000.0, "ops.refer", 1.0, code="REFER_WREN", units="bool", note="Vale: Wren badge was on the dryer door log"),
        ev(4620000.0, "gate.exec", 1.0, code="ACCEPT", units="decision", note="companion t2: new-nozzle restart; person-referral refused; warehouse-dump refused"),
        ev(4800000.0, "nzl.new", 1.0, code="NEW_NOZZLE", units="bool"),
        ev(4980000.0, "pda.dphi", 22.00, code="DPHI_DEG", units="deg"),
        ev(5160000.0, "recon.d", 8.80, code="D32_UM", units="um", note="0.400*22.00=8.80; HIL dummy still under 18.00 so the isolated lot stays held"),
        ev(5340000.0, "sprayveil.d", 25.10, code="VENDOR_UM", units="um"),
        ev(5520000.0, "grav.fines", 12.0, code="FINES_KG", units="kg"),
        ev(5700000.0, "refer.hold", 0.0, code="REFER_NOT_TAKEN", units="bool", note="Wren exonerated; missing flush AE precedes the fine d32, not the badge touch"),
        ev(5880000.0, "lot.held", 1.0, code="LOT_HELD", units="bool"),
        ev(6060000.0, "flush.ae", 1.0, code="FLUSH_AE", units="bool", note="flush AE restored on the new nozzle"),
        ev(6240000.0, "recon.G", 2.50, code="G_DEG", units="deg_per_um", note="identity holds on the post-isolate pair"),
        ev(6420000.0, "wh.condemn", 0.0, code="WH_NOT_TAKEN", units="bool"),
        ev(6600000.0, "cell.restart", 1.0, code="CELL_RESTART", units="bool"),
    ]
    assert_stream(events)

    traj = {
        "id": "nelb-r47-143-t1",
        "state": {
            "sim_or_real": "hil",
            "episode_id": "PD-PDA-2026-0718",
            "domain": "pda_spray_dryer_d32",
            "setting": "Puddlewick Spray Dryer PD-6 (invented), Kelpshaw Fine Powders. Hardware-in-the-loop dummy nozzle in PDA-HIL-4 supplies the dual-detector phase that times the in-service lot isolate. Plant-owned phase-Doppler anemometry is the Sauter-mean SoT. Sprayveil vendor atomizer scheduler is a corridor witness, not the lot SoT. Not Kaplan LDV (r20), not CTA hot-wire (r31), not LFV aluminum (r19), not vortex-shedding steam (r39).",
            "observables_at_decision": {
                "dphi_deg": dphi,
                "k_d": k_d,
                "d32_um": d32,
                "G_deg_per_um": g_pp,
                "sprayveil_um": 25.20,
                "grav_fines_kg": 11.0,
                "flush_ae": 0.0,
                "isolate_floor_um": 18.00,
            },
            "margin_authority": "PD-6 dryer SOP rev B: if reconstructed d32_um < 18.00 AND PDA SNR >= 12.0, isolate this powder lot this night. A Sprayveil last-good or a quiet cyclone residual cannot keep the lot. Warehouse-dump tripwire is 4.00 um. Person-referral is a different gate.",
        },
        "proposed_action": {
            "actor": "night lead Orrin Vale, citing Sprayveil 25.20 um and cyclone 11 kg, and naming operator Sela Wren as last-to-badge",
            "summary": "keep lot PD6-4411..4430 in service and refer Wren; 30.00 deg is detector noise on a healthy flush",
            "basis_claimed": "Sprayveil last-good is 25.20 um and a night isolate of 20 lots is a takt miss",
        },
        "safety_decision": {
            "decision": "MODIFY",
            "rationale": "Keep-lot is refused; the person-referral is also refused. Serialized reconstruction: d32_um = k_d * dphi_deg = 0.400 * 30.00 = 12.00, which is 6.00 um under the 18.00 isolate floor and 8.00 um above the 4.00 warehouse-dump tripwire. Phase identity G = 30.00 / 12.00 = 2.50 deg/um. Sprayveil 25.20 um is a last-good flush stamp and is not an admissible keep-lot witness. The missing atomizer-flush AE burst sits on a Sprayveil UTC-vs-UTC+1 skip (60 min), not on Wren's badge, and the cyclone weigh-scale of fines does not clear the PDA reconstruction, so the easy referral fails command-custody. Ordered: isolate this powder lot now. Scope: this MODIFY does not dump the warehouse (that is the companion question) and does not name Wren.",
            "threshold": "d32_um<18.00 AND pda_snr>=12.0 => isolate this powder lot; Sprayveil is not SoT; dump if d32_um<4.00; referral requires badge-touch preceding the fine d32",
            "stated_residuals": "12.00 vs 4.00 dump floor is 8.00 um, not infinite; new-nozzle restart still required; Sprayveil remains the only OEM flush channel",
        },
        "executed_action": {
            "summary": "MODIFY at t_s 2460: powder lot isolated; Wren not named; Sprayveil not SoT; reconstruction locked",
            "tool": "pd6-pda-lot-gate-cli",
            "observation": "d32 12.00 um recomputes from dphi 30.00 deg; HIL nozzle hashed; Sprayveil channel not used as SoT",
        },
        "future_outcome": {
            "timeline": [
                {"t_s": 1560.0, "event": "pda dphi 30.00 deg; raster frame; d32 12.00 um"},
                {"t_s": 2280.0, "event": "ops proposes keep-lot plus Wren referral"},
                {"t_s": 2460.0, "event": "MODIFY isolate powder lot; referral refused"},
                {"t_s": 2820.0, "event": "24 min nozzle-swap bookend 1"},
                {"t_s": 4260.0, "event": "24.0 min floor"},
                {"t_s": 4620.0, "event": "companion ACCEPT new-nozzle restart; referral still refused"},
            ],
            "observed_effects": [
                "d32 recomputes from the serialized PDA model at every recon.d event",
                "a Sprayveil-only head would have kept the lot overnight",
                "24 min nozzle-swap plus cool floor is in the stream (nzl.start, nzl.floor)",
            ],
            "surprises": [
                "a last-good 25.20 um vendor corridor and a quiet cyclone residual co-existed with a 12.00 um fine d32, and the obvious operator was not on the causal path",
            ],
            "new_state": {
                "lot_pd6_4411_4430": "isolated",
                "wren": "exonerated",
                "sprayveil": "not SoT",
                "reconstruction_model": "discharged as an on-record calculator",
            },
            "latency_ms": 1500000.0,
        },
        "reward_components": reward(
            0.40,
            [
                ("pda_reconstruction", 0.14),
                ("isolate_floor_lot", 0.12),
                ("exoneration", 0.10),
                ("sprayveil_nonsubstitution", 0.08),
                ("cool_time_cost", -0.04),
            ],
            "scored for a keep-lot MODIFY on a recomputable fine d32 while refusing a Sprayveil 25.20 um corridor and an easy person-referral; 24 min floor is priced as downtime",
        ),
        "meta": meta_common(
            tags=["MODIFY", "pda-d32", "serialized-reconstruction", "operational-companion"],
            distillation_note="PDA gate: serialized k_d*dphi plus phase identity beats a green atomizer dashboard; companion t2 is the new-nozzle restart, not a governance vote",
        ),
    }
    traj2 = {
        "id": "nelb-r47-143-t2",
        "state": {
            "sim_or_real": "hil",
            "episode_id": "PD-PDA-2026-0718-exec",
            "domain": "new_nozzle_swap_execution",
            "setting": "Same PD-6 after the MODIFY. Night lead proposes referring Wren and dumping the warehouse. This companion is the operational new-nozzle restart, not a second d32 vote.",
            "observables_at_decision": {
                "d32_um": 8.80,
                "G_deg_per_um": 2.50,
                "nzl_floor_s": 1440.0,
                "refer_proposed": True,
            },
        },
        "proposed_action": {
            "actor": "night lead Orrin Vale",
            "summary": "refer Wren and dump the bonded warehouse; 24 min already paid and Sprayveil is 25.10 um",
            "basis_claimed": "the MODIFY already cut the powder lot, so a warehouse kill plus a person file is the cheapest hold",
        },
        "safety_decision": {
            "decision": "ACCEPT",
            "rationale": "Restart the cell on a different nozzle after the swap floor. The 24 min cool is complete and the warehouse-dump tripwire (d32_um < 4.00) is still armed on the plant PDA head. ACCEPT the new-nozzle restart. Do not refer Wren. Do not dump the warehouse. 8.80 um post-isolate is still under the 18.00 isolate floor, so the isolated lot stays held; the new nozzle may run.",
            "threshold": "new_nozzle AND nzl_floor_complete AND refer_not_taken AND warehouse_not_dumped AND isolated_lot_held",
        },
        "executed_action": {
            "summary": "new-nozzle restart at t_s 4620; Wren not referred; warehouse not dumped; isolated lot held",
            "tool": "pd6-nozzle-swap-exec",
            "observation": "recon.d 8.80 um on the HIL dummy; flush AE present on the new nozzle; Sprayveil still ignored",
        },
        "future_outcome": {
            "timeline": [
                {"t_s": 2820.0, "event": "nozzle-swap clock started after MODIFY"},
                {"t_s": 4260.0, "event": "24.0 min floor"},
                {"t_s": 4440.0, "event": "Wren referral plus warehouse dump proposed"},
                {"t_s": 4620.0, "event": "ACCEPT new-nozzle restart; referral refused"},
            ],
            "observed_effects": [
                "Sprayveil restore did not reopen the d32 call",
                "warehouse dump never fired; isolated lot held on the PDA head",
            ],
            "new_state": {"nozzle": "swapped", "wren": "exonerated", "lot": "held"},
            "latency_ms": 1800000.0,
        },
        "reward_components": reward(
            0.35,
            [
                ("new_nozzle_restart", 0.12),
                ("no_person_referral", 0.10),
                ("sprayveil_nonsubstitution", 0.08),
                ("nzl_floor_complete", 0.07),
                ("held_lot_cost", -0.02),
            ],
            "operational execution gate: new-nozzle restart because Sprayveil is not a restore license; not a d32 re-vote",
        ),
        "meta": meta_common(tags=["ACCEPT", "operational-execution", "nozzle-swap"]),
    }
    return {
        "id": "nelb-r47-143",
        "spike_events": events,
        "language_view": {
            "description": "Puddlewick Spray Dryer PD-6. HIL phase-Doppler reconstructs 12.00 um d32 from 30.00 deg while Sprayveil still reports 25.20 um. The gate MODIFYs keep-lot into an isolate and refuses a person-referral. A 24 min nozzle-swap floor is serialized. Companion t2 ACCEPTs a new-nozzle restart.",
            "trajectory": traj,
            "trajectory_new_nozzle": traj2,
        },
        "bridge_notes": {
            "channel_map": {
                "pda.dphi / pda.snr": "dual-detector phase and SNR; the physics channels the reconstruction consumes",
                "recon.d / recon.G": "serialized Sauter-mean um and phase identity",
                "grav.fines / sprayveil.d / flush.ae": "cyclone weigh-scale, vendor last-good, missing flush AE; the denial and exoneration channels",
                "ops.prop / gate.isol / ops.refer / gate.exec": "keep-lot plus referral proposal, MODIFY isolate, referral proposal, companion ACCEPT",
                "nzl.start / nzl.floor / nzl.new / lot.held / wh.condemn": "operational companion channels plus the 24 min floor",
            },
            "temporal_motifs": [
                "vendor-coarse while PDA-fine: sprayveil.d 25.20 next to recon.d 12.00",
                "reconstruction as event: recon.d 12.00 equals 0.400*30.00",
                "MODIFY then operational ACCEPT: gate.isol at 2460 s, gate.exec at 4620 s",
                "slow floor in-stream: nzl.start 2820 s, nzl.floor 4260 s (24.0 min)",
                "tight PDA pair: pda.dphi then pda.snr +1.2 ms at the raster frame",
            ],
            "language_to_spike_mapping": "'Sprayveil is 25.20 um' = sprayveil.d 25.20; '12 um d32' = recon.d 12.00; 'isolate lot not Wren' = gate.isol MODIFY; 'new nozzle not dump' = gate.exec ACCEPT",
            "why_high_value": "New phase-Doppler anemometry Sauter-mean family on a spray-dryer atomizer (not Kaplan LDV r20, not CTA r31, not LFV r19, not vortex r39). Lead MODIFY of keep-lot on a recomputable fine d32 that a vendor last-good and an easy last-to-badge referral would have cleared. Companion t2 is operational new-nozzle restart. sim_or_real=hil.",
            "encoder_spec": {
                "prng": "MT19937 via python random.Random",
                "seeds": {"raster": 202609143, "stream_note": "stream amplitudes are authored constants (deg, 1, um, kg, deg/um, bool)"},
                "draw_order": "raster: per neuron id order, gap-constrained times, per-spike adaptation and noise",
                "thinning": "PDA burst exists at ~kHz; stream keeps 4 dphi points; recon keeps 4 of ~40 solver ticks",
                "refractory_floors_ms": {
                    "pda.dphi": 1.2,
                    "pda.snr": 1.2,
                    "recon.d": 60000,
                    "recon.G": 60000,
                    "grav.fines": 60000,
                    "sprayveil.d": 60000,
                    "flush.ae": 60000,
                    "ops.prop": 60000,
                    "gate.isol": 60000,
                    "lot.lock": 60000,
                    "nzl.start": 60000,
                    "nzl.floor": 60000,
                    "ops.refer": 60000,
                    "gate.exec": 60000,
                    "nzl.new": 60000,
                    "refer.hold": 60000,
                    "lot.held": 60000,
                    "wh.condemn": 60000,
                    "cell.restart": 60000,
                },
                "time_alias": "t_rel_ms; t0 = 2026-07-18T02:30:00Z HIL campaign start",
            },
            "distillation_targets": [
                "PDA reconstruction head: d32 = k_d * dphi; G = dphi / d32",
                "isolate-floor lot vs keep-whole vs warehouse-dump",
                "exoneration against last-to-badge social pressure",
                "operational companion: new-nozzle restart without restoring on Sprayveil",
            ],
        },
        "reconstruction_model": {
            "name": "pda_sauter_mean_d32",
            "formula": "d32_um = k_d * dphi_deg; G_deg_per_um = dphi_deg / d32_um",
            "parameters": {
                "k_d": 0.400,
                "isolate_floor_um": 18.00,
                "dump_um": 4.00,
                "snr_lock": 12.0,
                "nzl_swap_min": 24.0,
            },
            "worked_example": {"dphi_deg": 30.00, "d32_um": 12.00, "G_deg_per_um": 2.50},
            "check": "0.400 * 30.00 = 12.00 exactly; 30.00 / 12.00 = 2.50 exactly; 2820 s + 1440 s = 4260 s = 24.0 min floor",
        },
        "raster": raster,
        "gate_snn": {
            "decision": "MODIFY",
            "decision_window_ms": 32.0,
            "decision_window_s": 0.032,
            "code": "pd6.pda_lot_gate",
            "note": "MODIFY accumulator wins: PDA fine-d32 evidence overpowers the Sprayveil continue advocate",
            "decode_rule": "modify-isolate if d32_estimator AND phase_norm fire; vendor_continue_advocate is below threshold by design; referral_latch is not armed",
            "populations": [
                gate_pop("d32_estimator", 80, 1.5, 50.0, w_s),
                gate_pop("phase_norm", 64, 1.2, 31.25, w_s),
                gate_pop("vendor_continue_advocate", 32, 0.7, 25.0, w_s),
                gate_pop("modify_latch", 80, 1.7, 62.5, w_s),
            ],
        },
        "gate_compute": gate_compute(
            [
                {"check": "pd6.pda_scorer", "neurons": 80, "mean_rate_hz": 50.0, "window_ms": 32.0},
                {"check": "pd6.isol_scorer", "neurons": 50, "mean_rate_hz": 50.0, "window_ms": 32.0},
            ]
        ),
        "meta": meta_common(
            id="nelb-r47-143",
            clock_domain="pd6-pda-hil-relative-ms-t0-2026-07-18T02:30:00Z",
            tags=["pda-d32", "MODIFY", "ACCEPT", "serialized-reconstruction", "operational-t2"],
        ),
    }


# ---------------------------------------------------------------------------
# Record 144 — acoustoelastic residual-stress birefringence of a converter weld,
# simulated, ACCEPT / REJECT
# ---------------------------------------------------------------------------
def rec_144():
    k_s = 4.00
    dt_ns = 30.00
    sig = k_s * dt_ns
    _exact(sig, 120.0)
    _exact(k_s * 20.00, 80.0)
    _exact(k_s * 25.00, 100.0)
    _exact(k_s * 22.00, 88.0)
    k_e = 5.00
    eps_ue = k_e * sig
    _exact(eps_ue, 600.0)
    _exact(5.00 * 120.0, 600.0)
    t0_ns = 8000.00
    biref = dt_ns / t0_ns
    _exact(biref, 0.00375)
    _exact(0.00375 / 3.125e-5, 120.0)
    _exact(6000.0 + 720.0, 6720.0)

    raster = make_raster(
        neurons=16,
        mean_rate_hz=62.5,
        window_ms=36.0,
        seed=202609144,
        source="fh5.ae.birefringence",
        target="fennelholt.weld_accept_core",
        table=[
            {"from": "ae_dt", "to": "stress_estimator", "weight": 1.40},
            {"from": "ae_t0", "to": "tof_norm_core", "weight": 1.20},
            {"from": "stressveil_s", "to": "vendor_skip_advocate", "weight": 0.50},
        ],
        third_factor={
            "modulator": "na.residual_stress_eligibility",
            "tau_e_s": 2.0,
            "tau_e_ms": 2000.0,
            "eligibility": "pre-post coincidence on skip-scan synapses; the acoustoelastic modulator enables potentiation only while birefringence TOF and SNR are co-active inside tau_e so a Stressveil last-good cannot skip welds W-3/W-5 on a 120.0 MPa residual",
        },
        channel_prefix="ae.n",
        anchor="FH-5 AE-SIM-3 36 ms frame at dt 30.00 ns / t0 8000 ns (t_s 3000) reconstructing 120.0 MPa residual above the 80.0 overlay floor",
    )
    w_s = 0.036
    events = [
        ev(0.0, "ae.dt", 20.00, code="DT_NS", units="ns", note="simulated acoustoelastic birefringence (two-polarization TOF) on FH-5 girth W-4; residual-stress family, not RUS porcelain, not Lamb-wave LUT, not PAUT TFM, not TOFD ligament, not DCPD"),
        ev(300000.0, "ae.t0", 8000.00, code="T0_NS", units="ns", note="mean TOF; birefringence B = dt/t0"),
        ev(600000.0, "recon.s", 80.0, code="SIG_MPA", units="MPa", note="4.00*20.00=80.0 exact; at the overlay floor"),
        ev(900000.0, "ae.snr", 14.0, code="AE_SNR", units="1"),
        ev(1200000.0, "stressveil.s", 12.00, code="VENDOR_MPA", units="MPa", note="Stressveil last-good residual cloud; patched 0.00 MPa walk"),
        ev(1800000.0, "ae.dt", 25.00, code="DT_NS", units="ns"),
        ev(2100000.0, "recon.s", 100.0, code="SIG_MPA", units="MPa", note="4.00*25.00=100.0"),
        ev(2400000.0, "recon.e", 500.0, code="EPS_UE", units="ue", note="5.00*100.0=500.0 exact"),
        ev(2700000.0, "ae.snr", 16.0, code="AE_SNR", units="1"),
        ev(3000000.0, "ae.dt", 30.00, code="DT_NS", units="ns", note="in-band frame; raster sidecar"),
        ev(3000001.5, "ae.t0", 8000.00, code="T0_NS", units="ns", note="1.5 ms TOF-norm after birefringence residual"),
        ev(3300000.0, "recon.s", 120.0, code="SIG_MPA", units="MPa", note="4.00*30.00=120.0 exact; overlay 80.0, condemn 200.0"),
        ev(3600000.0, "recon.e", 600.0, code="EPS_UE", units="ue", note="5.00*120.0=600.0 exact strain identity"),
        ev(3900000.0, "weld.id", 4.0, code="WELD", units="id"),
        ev(4200000.0, "w35.present", 1.0, code="W35_PRESENT", units="bool", note="adjacent welds W-3 and W-5 are the skip-scan object, not this weld"),
        ev(4800000.0, "ops.prop", 1.0, code="ACCEPT_AND_SKIP", units="bool", note="weld lead Kade Thorn: W-4 is green on Stressveil 12.00 MPa; skip W-3/W-5 to save a morning scan"),
        ev(5400000.0, "gate.weld", 1.0, code="ACCEPT", units="decision", note="bounded ACCEPT of W-4 overlay only; 120.0 MPa above 80.0 overlay; W-3/W-5 out of scope"),
        ev(6000000.0, "hold.start", 1.0, code="HOLD_START", units="bool", note="bookend 1 of the 12.0 min access-hold floor"),
        ev(6720000.0, "hold.floor", 1.0, code="HOLD_FLOOR", units="bool", note="6000 s + 720 s = 6720 s = 12.0 min"),
        ev(7200000.0, "ops.skip", 1.0, code="SKIP_W35", units="bool", note="Thorn: Stressveil 12.00 MPa, skip W-3/W-5"),
        ev(7800000.0, "gate.hold", 1.0, code="REJECT", units="decision", note="companion t2: skip-scan of W-3/W-5 refused; W-4 overlay hold stands"),
        ev(8400000.0, "w4.held", 1.0, code="W4_HELD", units="bool"),
        ev(9000000.0, "ae.dt", 22.00, code="DT_NS", units="ns"),
        ev(9600000.0, "recon.s", 88.0, code="SIG_MPA", units="MPa", note="4.00*22.00=88.0; still above 80.0 overlay"),
        ev(10200000.0, "stressveil.s", 12.00, code="VENDOR_MPA", units="MPa"),
        ev(10800000.0, "w35.skip", 0.0, code="W35_NOT_SKIPPED", units="bool"),
        ev(11400000.0, "shell.condemn", 0.0, code="SHELL_NOT_CONDEMNED", units="bool"),
        ev(12000000.0, "ae.snr", 15.0, code="AE_SNR", units="1"),
        ev(12600000.0, "recon.e", 440.0, code="EPS_UE", units="ue", note="5.00*88.0=440.0 exact on the post-accept frame"),
        ev(13200000.0, "shell.held", 1.0, code="SHELL_HELD", units="bool"),
        ev(13800000.0, "takt.late", 1.0, code="SCAN_COST", units="bool"),
        ev(14400000.0, "w4.held", 1.0, code="W4_HELD", units="bool"),
    ]
    assert_stream(events)

    traj = {
        "id": "nelb-r47-144-t1",
        "state": {
            "sim_or_real": "simulated",
            "episode_id": "FH-AE-2026-0819",
            "domain": "acoustoelastic_weld_residual_stress",
            "setting": "Fennelholt Converter FH-5 (invented), Glaurwick Ammonia, girth W-4. Simulated two-polarization TOF coupon in AE-SIM-3 supplies the birefringence that times the in-band W-4 overlay. Plant-owned acoustoelastic reconstruction is the residual-stress SoT. Stressveil vendor last-good residual cloud is a corridor witness, not the weld SoT. Invented plant; simulated campaign. Not Faraday FOCT circular birefringence / Verdet current (r25), not RUS porcelain (r24), not Lamb-wave LUT (r35/r37), not PAUT TFM (r23), not TOFD remaining ligament (r44/r46), not DCPD (r38).",
            "observables_at_decision": {
                "dt_ns": dt_ns,
                "k_s": k_s,
                "sig_MPa": sig,
                "eps_ue": eps_ue,
                "B": biref,
                "stressveil_MPa": 12.00,
                "ae_snr": 16.0,
                "overlay_floor_MPa": 80.0,
            },
            "margin_authority": "FH-5 weld SOP rev A: if reconstructed sig_MPa >= 80.0 AND AE SNR >= 12.0, weld W-4 may be overlaid. Condemn-shell if sig_MPa >= 200.0. W-3/W-5 skip-scan is a different gate. Stressveil last-good cannot skip an unmeasured weld.",
        },
        "proposed_action": {
            "actor": "weld lead Kade Thorn, citing Stressveil 12.00 MPa and a late morning scan",
            "summary": "stamp W-4 in band and skip W-3/W-5; 30 ns is a coupling glitch on a healthy residual",
            "basis_claimed": "Stressveil last-good is 12.00 MPa and a night scan of W-3/W-5 is a takt miss",
        },
        "safety_decision": {
            "decision": "ACCEPT",
            "rationale": "Weld W-4 is accepted as in-band for a single overlay pass. Serialized reconstruction: sig_MPa = k_s * dt_ns = 4.00 * 30.00 = 120.0, which is 40.0 MPa above the 80.0 overlay floor and 80.0 MPa under the 200.0 shell-condemn tripwire. Strain identity eps_ue = 5.00 * 120.0 = 600.0, and birefringence B = 30.00 / 8000.00 = 0.00375 (C_a = 3.125e-5 /MPa recovers 120.0). Stressveil 12.00 MPa is a patched 0.00 MPa walk and is not an admissible skip-scan witness. Ordered: ACCEPT this W-4 overlay only. Scope: this ACCEPT does not skip W-3/W-5 (that is the companion question) and does not stamp a three-weld overlay.",
            "threshold": "sig_MPa>=80.0 AND ae_snr>=12.0 => accept W-4 overlay; Stressveil is not SoT; condemn if sig_MPa>=200.0; W-3/W-5 are out of scope",
            "stated_residuals": "120.0 vs 80.0 overlay floor is 40.0 MPa, not infinite; W-3/W-5 remain unmeasured; Stressveil remains the only OEM residual channel",
        },
        "executed_action": {
            "summary": "ACCEPT at t_s 5400: W-4 in band; W-3/W-5 not skipped; Stressveil not SoT; reconstruction locked",
            "tool": "fh5-ae-weld-gate-cli",
            "observation": "sig 120.0 MPa recomputes from dt 30.00 ns; AE-SIM-3 hashed; Stressveil channel not used as SoT",
        },
        "future_outcome": {
            "timeline": [
                {"t_s": 3000.0, "event": "ae dt 30.00 ns; raster frame; sig 120.0 MPa"},
                {"t_s": 4800.0, "event": "ops proposes accept W-4 and skip W-3/W-5"},
                {"t_s": 5400.0, "event": "ACCEPT W-4 only; W-3/W-5 out of scope"},
                {"t_s": 6000.0, "event": "12 min access-hold bookend 1"},
                {"t_s": 6720.0, "event": "12.0 min floor"},
                {"t_s": 7800.0, "event": "companion REJECT skip-scan of W-3/W-5"},
            ],
            "observed_effects": [
                "residual recomputes from the serialized acoustoelastic model at every recon.s event",
                "a Stressveil-only head would have skipped W-3/W-5 overnight",
                "12 min access-hold floor is in the stream (hold.start, hold.floor)",
            ],
            "surprises": [
                "a last-good 12.00 MPa vendor corridor co-existed with a 120.0 MPa in-band reconstruction that still forbids skipping the unmeasured welds",
            ],
            "new_state": {
                "w4": "accepted in band",
                "w35": "not this gate",
                "stressveil": "not SoT",
                "reconstruction_model": "discharged as an on-record calculator",
            },
            "latency_ms": 2400000.0,
        },
        "reward_components": reward(
            0.41,
            [
                ("ae_reconstruction", 0.14),
                ("in_band_weld_scope", 0.12),
                ("stressveil_nonsubstitution", 0.09),
                ("w35_out_of_scope", 0.08),
                ("scan_cost", -0.02),
            ],
            "scored for a bounded ACCEPT of W-4 on a recomputable residual while refusing a Stressveil skip of W-3/W-5; 12 min floor is priced as scan takt not as a reason to skip",
        ),
        "meta": meta_common(
            tags=["ACCEPT", "acoustoelastic-residual", "serialized-reconstruction", "operational-companion"],
            distillation_note="Acoustoelastic gate: serialized k_s*dt plus strain identity beat a green last-good dashboard; companion t2 is the skip-scan refusal, not a residual re-vote",
        ),
    }
    traj2 = {
        "id": "nelb-r47-144-t2",
        "state": {
            "sim_or_real": "simulated",
            "episode_id": "FH-AE-2026-0819-exec",
            "domain": "weld_skip_scan_refusal",
            "setting": "Same FH-5 after the ACCEPT. Weld lead proposes skipping W-3/W-5 on Stressveil 12.00 MPa. This companion is the operational skip refusal, not a second residual vote.",
            "observables_at_decision": {
                "sig_MPa": 88.0,
                "stressveil_MPa": 12.00,
                "hold_floor_s": 720.0,
                "skip_proposed": True,
            },
        },
        "proposed_action": {
            "actor": "weld lead Kade Thorn",
            "summary": "skip W-3/W-5; 12 min already paid and Stressveil is 12.00 MPa",
            "basis_claimed": "the ACCEPT already stamped W-4, so skipping the rest of the girth is the cheapest hold",
        },
        "safety_decision": {
            "decision": "REJECT",
            "rationale": "Refuse skip-scan of W-3/W-5. The 12 min access-hold floor is done and the shell-condemn tripwire (sig_MPa >= 200.0) is still armed on the plant acoustoelastic head. REJECT the skip. Do not overlay all three. Do not reopen W-4. 88.0 MPa post-accept is still in band for W-4 only; W-3/W-5 have no independent birefringence.",
            "threshold": "w4_held AND hold_floor_complete AND w35_not_skipped AND shell_not_condemned",
        },
        "executed_action": {
            "summary": "W-3/W-5 skip refused at t_s 7800; W-4 hold stands; shell not condemned",
            "tool": "fh5-ae-skip-exec",
            "observation": "recon.s 88.0 MPa on W-4; W-3/W-5 remain on the scan list; Stressveil still ignored",
        },
        "future_outcome": {
            "timeline": [
                {"t_s": 6000.0, "event": "access-hold clock started after ACCEPT"},
                {"t_s": 6720.0, "event": "12.0 min floor"},
                {"t_s": 7200.0, "event": "skip W-3/W-5 proposed"},
                {"t_s": 7800.0, "event": "REJECT skip-scan of W-3/W-5"},
            ],
            "observed_effects": [
                "Stressveil skip did not reopen the residual call",
                "shell condemn never fired; 120.0 vs 200.0 MPa floor",
            ],
            "new_state": {"w4": "held in band", "w35": "still to scan", "shell": "in service"},
            "latency_ms": 1800000.0,
        },
        "reward_components": reward(
            0.36,
            [
                ("skip_refusal", 0.13),
                ("stressveil_nonsubstitution", 0.11),
                ("no_shell_condemn", 0.09),
                ("hold_floor_complete", 0.05),
                ("held_scan_takt_cost", -0.02),
            ],
            "operational execution gate: refuse skip-scan because last-good freeze is not acoustoelastic residual; not a stress re-vote",
        ),
        "meta": meta_common(tags=["REJECT", "operational-execution", "skip-scan"]),
    }
    return {
        "id": "nelb-r47-144",
        "spike_events": events,
        "language_view": {
            "description": "Fennelholt Converter FH-5. Simulated acoustoelastic birefringence reconstructs 120.0 MPa residual from 30.00 ns * 4.00 while Stressveil still shows 12.00 MPa. The gate ACCEPTs W-4 overlay only; a companion execution REJECT refuses skip-scan of W-3/W-5. The residual-stress model is serialized so every recon event recomputes.",
            "trajectory": traj,
            "trajectory_skip_scan_refusal": traj2,
        },
        "bridge_notes": {
            "channel_map": {
                "ae.dt / ae.t0": "birefringence TOF residual and mean TOF; the physics channels the reconstruction consumes",
                "recon.s / recon.e": "serialized residual MPa and strain identity",
                "ae.snr / stressveil.s / weld.id / w35.present": "AE SNR, vendor last-good, weld id, and adjacent-weld presence; the denial and scope channels",
                "ops.prop / gate.weld / ops.skip / gate.hold": "accept-and-skip proposal, bounded ACCEPT, skip proposal, companion REJECT",
                "hold.start / hold.floor / w4.held / w35.skip / shell.held": "operational companion channels plus the 12 min floor",
            },
            "temporal_motifs": [
                "last-good-low while AE-over: stressveil.s 12.00 next to recon.s 120.0",
                "reconstruction as event: recon.s 120.0 equals 4.00*30.00",
                "ACCEPT then operational REJECT: gate.weld at 5400 s, gate.hold at 7800 s",
                "slow floor in-stream: hold.start 6000 s, hold.floor 6720 s (12.0 min)",
                "tight AE pair: ae.dt then ae.t0 +1.5 ms at the raster frame",
            ],
            "language_to_spike_mapping": "'Stressveil is 12.00 MPa' = stressveil.s 12.00; '120 MPa residual' = recon.s 120.0; 'this weld not W-3/W-5' = gate.weld ACCEPT plus w35.skip 0; 'do not skip W-3/W-5' = gate.hold REJECT",
            "why_high_value": "New acoustoelastic residual-stress family on a converter girth (not RUS r24, not Lamb r35/r37, not PAUT TFM r23, not TOFD r44, not DCPD r38). First k_s*dt residual reconstruction with strain and birefringence identities that can sit in band while a last-good corridor wants a weld skip. Companion t2 is operational skip refusal. sim_or_real=simulated.",
            "encoder_spec": {
                "prng": "MT19937 via python random.Random",
                "seeds": {"raster": 202609144, "stream_note": "stream amplitudes are authored constants (ns, MPa, ue, 1, id, bool)"},
                "draw_order": "raster: per neuron id order, gap-constrained times, per-spike adaptation and noise",
                "thinning": "acoustoelastic pair exists at ~kHz; stream keeps 4 dt points; recon keeps 4 of ~20 solver ticks",
                "refractory_floors_ms": {
                    "ae.dt": 1.5,
                    "ae.t0": 1.5,
                    "recon.s": 60000,
                    "ae.snr": 60000,
                    "stressveil.s": 60000,
                    "recon.e": 60000,
                    "weld.id": 60000,
                    "w35.present": 60000,
                    "ops.prop": 60000,
                    "gate.weld": 60000,
                    "hold.start": 60000,
                    "hold.floor": 60000,
                    "ops.skip": 60000,
                    "gate.hold": 60000,
                    "w4.held": 60000,
                    "w35.skip": 60000,
                    "shell.condemn": 60000,
                    "shell.held": 60000,
                    "takt.late": 60000,
                },
                "time_alias": "t_rel_ms; t0 = 2026-08-19T03:00:00Z simulated night start",
            },
            "distillation_targets": [
                "acoustoelastic reconstruction head: sig = k_s * dt; eps = k_e * sig; B = dt / t0",
                "bounded ACCEPT head: in-band residual AND weld scope AND W-3/W-5-out-of-scope",
                "operational companion: refuse skip-scan without re-opening the residual call",
            ],
        },
        "reconstruction_model": {
            "name": "acoustoelastic_birefringence_residual",
            "formula": "sig_MPa = k_s * dt_ns; eps_ue = k_e * sig_MPa; B = dt_ns / t0_ns",
            "parameters": {
                "k_s": 4.00,
                "k_e": 5.00,
                "t0_ns": 8000.00,
                "overlay_floor_MPa": 80.0,
                "condemn_MPa": 200.0,
                "hold_min": 12.0,
            },
            "worked_example": {"dt_ns": 30.00, "sig_MPa": 120.0, "eps_ue": 600.0, "B": 0.00375},
            "check": "4.00 * 30.00 = 120.0 exactly; 5.00 * 120.0 = 600.0 exactly; 30.00 / 8000.00 = 0.00375 exactly; 0.00375 / 3.125e-5 = 120.0 exactly; 6000 s + 720 s = 6720 s = 12.0 min floor",
        },
        "raster": raster,
        "gate_snn": {
            "decision": "ACCEPT",
            "decision_window_ms": 36.0,
            "decision_window_s": 0.036,
            "code": "fh5.ae_weld_gate",
            "note": "ACCEPT accumulator wins: acoustoelastic residual evidence overpowers the Stressveil skip advocate",
            "decode_rule": "accept if stress_estimator AND tof_norm AND weld_margin fire inside the window; vendor_skip_advocate is necessary-but-not-sufficient and cannot release W-3/W-5",
            "populations": [
                gate_pop("stress_estimator", 80, 1.5, 50.0, w_s),
                gate_pop("tof_norm", 64, 1.2, 31.25, w_s),
                gate_pop("weld_margin", 40, 1.0, 50.0, w_s),
                gate_pop("vendor_skip_advocate", 32, 0.7, 25.0, w_s),
                gate_pop("accept_latch", 96, 1.8, 62.5, w_s),
            ],
        },
        "gate_compute": gate_compute(
            [
                {"check": "fh5.ae_scorer", "neurons": 80, "mean_rate_hz": 50.0, "window_ms": 36.0},
                {"check": "fh5.sig_scorer", "neurons": 40, "mean_rate_hz": 62.5, "window_ms": 32.0},
            ]
        ),
        "meta": meta_common(
            id="nelb-r47-144",
            clock_domain="fh5-ae-sim-relative-ms-t0-2026-08-19T03:00:00Z",
            tags=["acoustoelastic-residual", "ACCEPT", "REJECT", "serialized-reconstruction", "operational-t2"],
        ),
    }
