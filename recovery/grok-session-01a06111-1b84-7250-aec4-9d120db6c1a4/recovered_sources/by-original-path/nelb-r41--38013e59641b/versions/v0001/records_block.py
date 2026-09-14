# ---------------------------------------------------------------------------
# Record 124 — cyclotron button-BPM + BLM maze-loss, designed,
# REJECT / MODIFY
# ---------------------------------------------------------------------------
def rec_124():
    k_x = 20.00
    v_r = 12.00
    v_l = 4.00
    x_mm = k_x * (v_r - v_l) / (v_r + v_l)
    _exact(x_mm, 10.00)
    _exact(k_x * (8.00 - 8.00) / (8.00 + 8.00), 0.00)
    _exact(k_x * (10.00 - 6.00) / (10.00 + 6.00), 5.00)
    _exact(k_x * (9.00 - 7.00) / (9.00 + 7.00), 2.50)
    k_d = 4.00
    d_usv = k_d * x_mm
    _exact(d_usv, 40.00)
    _exact(k_d * 2.50, 10.00)
    _exact(6000.0 + 1080.0, 7080.0)

    raster = make_raster(
        neurons=20,
        mean_rate_hz=50.0,
        window_ms=40.0,
        seed=202609124,
        source="st3.bpm.tr4",
        target="slatefen.nozzle_stop_core",
        table=[
            {"from": "bpm_dV", "to": "steer_estimator", "weight": 1.40},
            {"from": "bpm_snr", "to": "bpm_lock_core", "weight": 1.15},
            {"from": "orbitveil_x", "to": "vendor_beam_advocate", "weight": 0.45},
        ],
        third_factor={
            "modulator": "da.tdc_infra_conflict",
            "tau_e_s": 1.6,
            "tau_e_ms": 1600.0,
            "eligibility": "pre-post coincidence on keep-beam synapses; the BPM modulator depresses keep-beam links when button difference stays high inside tau_e of an SNR lock so an Orbitveil TDC comb cannot hide a 10.00 mm maze steer",
        },
        channel_prefix="bpm.n",
        anchor="ST-3 button-BPM 40 ms frame at VR 12.00 / VL 4.00 (t_s 3000) reconstructing 10.00 mm orbit offset above the 6.00 mm isolate floor",
    )
    w_s = 0.040
    events = [
        ev(0.0, "bpm.VR", 8.00, code="VR_V", units="V", note="plant-owned button BPM on ST-3 TR-4 nozzle N-2; compact-therapy cyclotron position, not muon tomography, not PMU, not fluxgate, not portal NaI"),
        ev(300000.0, "bpm.snr", 6.0, code="BPM_SNR", units="1", note="early SNR under the 12.0 lock floor"),
        ev(600000.0, "recon.x", 0.00, code="X_MM", units="mm", note="20.00*(8.00-8.00)/(8.00+8.00)=0.00 exact"),
        ev(900000.0, "rp.uSv", 4.0, code="RP_USV_H", units="uSv_h", note="RP ion-chamber serial LAN; independent of Orbitveil TDC cloud"),
        ev(1200000.0, "orbitveil.x", 1.10, code="VENDOR_MM", units="mm", note="Orbitveil TDC/FPGA cloud; infra owner; not admissible SoT"),
        ev(1800000.0, "bpm.VR", 10.00, code="VR_V", units="V"),
        ev(2100000.0, "recon.x", 5.00, code="X_MM", units="mm", note="20.00*(10.00-6.00)/(10.00+6.00)=5.00"),
        ev(2400000.0, "blm.nA", 20.00, code="BLM_NA", units="nA", note="loss-monitor current on the maze collimator"),
        ev(2700000.0, "plc.A", 412.0, code="MAG_A", units="A", note="magnet-supply PLC on copper fieldbus; no vendor agent"),
        ev(3000000.0, "bpm.VR", 12.00, code="VR_V", units="V", note="isolate-floor frame; raster sidecar"),
        ev(3000001.3, "bpm.VL", 4.00, code="VL_V", units="V", note="1.3 ms left-button after right; 12.00+4.00=16.00 sum"),
        ev(3300000.0, "recon.x", 10.00, code="X_MM", units="mm", note="20.00*(12.00-4.00)/(12.00+4.00)=10.00 exact; isolate floor 6.00"),
        ev(3600000.0, "recon.D", 40.00, code="MAZE_USV", units="uSv", note="4.00*10.00=40.00 exact; maze-dose floor 24.00"),
        ev(3900000.0, "bpm.snr", 16.0, code="BPM_SNR", units="1", note="16.0 >= 12.0 lock floor"),
        ev(4200000.0, "orbitveil.x", 1.20, code="VENDOR_MM", units="mm"),
        ev(4800000.0, "ops.prop", 1.0, code="KEEP_BEAM", units="bool", note="night operator Calder Brack: Orbitveil 1.20 mm plus HIS clean; keep the 230 MeV fraction"),
        ev(5400000.0, "gate.stop", 1.0, code="REJECT", units="decision", note="refuse keep-beam; 10.00 mm and SNR 16.0; Orbitveil not SoT"),
        ev(6000000.0, "soak.start", 1.0, code="SOAK_START", units="bool", note="bookend 1 of the 18.0 min magnet-settle floor"),
        ev(7080000.0, "soak.floor", 1.0, code="SOAK_FLOOR", units="bool", note="6000 s + 1080 s = 7080 s = 18.0 min"),
        ev(7800000.0, "ops.kill", 1.0, code="ROOM_ESD", units="bool", note="Brack: ESD the whole TR-4 vault until day-shift"),
        ev(8400000.0, "gate.hold", 1.0, code="MODIFY", units="decision", note="companion t2: isolate nozzle N-2; vault ESD refused"),
        ev(9000000.0, "nozzle.set", 1.0, code="N2_ISOL", units="bool"),
        ev(9600000.0, "bpm.VR", 9.00, code="VR_V", units="V"),
        ev(10200000.0, "recon.x", 2.50, code="X_MM", units="mm", note="20.00*(9.00-7.00)/(9.00+7.00)=2.50; under 6.00 so the hold may stay on RP"),
        ev(10800000.0, "rp.uSv", 12.0, code="RP_USV_H", units="uSv_h"),
        ev(11400000.0, "room.esd", 0.0, code="ESD_NOT_TAKEN", units="bool"),
        ev(12000000.0, "soak.held", 1.0, code="SOAK_HELD", units="bool"),
        ev(12600000.0, "orbitveil.x", 1.15, code="VENDOR_MM", units="mm"),
        ev(13200000.0, "plc.A", 280.0, code="MAG_A", units="A"),
        ev(13800000.0, "nozzle.held", 1.0, code="N2_HELD", units="bool"),
        ev(14400000.0, "blm.nA", 8.00, code="BLM_NA", units="nA"),
        ev(15000000.0, "bpm.snr", 14.0, code="BPM_SNR", units="1"),
    ]
    assert_stream(events)

    traj = {
        "id": "nelb-r41-124-t1",
        "state": {
            "sim_or_real": "designed",
            "episode_id": "ST-BPM-2026-0902",
            "domain": "cyclotron_button_bpm_blm",
            "setting": "Slatefen Compact Therapy ST-3 (invented), 230 MeV proton room TR-4 nozzle N-2. Plant-owned button-BPM pair plus maze BLM is the orbit-offset SoT. Orbitveil TDC/FPGA vendor (infra owner) plus HIS admin Orrin Sloe are collusion parties, not witnesses. Invented plant; designed campaign. Not muon tomography (r01/r17), not PMU synchrophasor (r5), not fluxgate gradiometry (r5), not portal NaI counting (r6), not Greyfen KCTC-7 hole sketch.",
            "observables_at_decision": {
                "V_R": v_r,
                "V_L": v_l,
                "k_x_mm": k_x,
                "x_mm": x_mm,
                "D_uSv": d_usv,
                "bpm_snr": 16.0,
                "orbitveil_mm": 1.20,
                "rp_uSv_h": 38.0,
                "isolate_floor_mm": 6.00,
            },
            "margin_authority": "ST-3 therapy SOP rev C: if reconstructed |x_mm| >= 6.00 AND BPM SNR >= 12.0, keep-beam is forbidden even if Orbitveil reports <2.00 mm and HIS timestamps look clean. Vault ESD is a different gate.",
        },
        "proposed_action": {
            "actor": "night operator Calder Brack, citing Orbitveil 1.20 mm and a clean HIS stamp, with HIS admin Orrin Sloe on the call",
            "summary": "keep the 230 MeV fraction; 12.00 V on the right button is TDC comb noise on a healthy orbit",
            "basis_claimed": "Orbitveil is the only OEM BPM SoT and aborting a paid fraction is a 40-patient backlog",
        },
        "safety_decision": {
            "decision": "REJECT",
            "rationale": "Keep-beam is refused. Serialized reconstruction: x_mm = k_x * (V_R - V_L) / (V_R + V_L) = 20.00 * (12.00 - 4.00) / (12.00 + 4.00) = 10.00, above the 6.00 mm isolate floor, and BPM SNR is 16.0 >= 12.0. Maze-dose identity D_uSv = k_d * x_mm = 4.00 * 10.00 = 40.00, above the 24.00 uSv maze floor. Orbitveil 1.20 mm is a TDC comb the infra owner can write; HIS timestamps were slid by Sloe. RP ion-chamber and magnet PLC are witnesses none of {Brack, Orbitveil, Sloe} can write. Ordered: refuse keep-beam now. Scope: this REJECT does not ESD the vault (that is the companion question) and does not dump the main magnet.",
            "threshold": "abs(x_mm)>=6.00 AND bpm_snr>=12.0 => refuse keep-beam; Orbitveil is not SoT",
            "stated_residuals": "nozzle isolate still required to hold the 10.00 mm; 10.00 vs a 20.00 mm tripwire is a production cut; Orbitveil remains the only OEM TDC channel",
        },
        "executed_action": {
            "summary": "REJECT at t_s 5400: keep-beam refused; Orbitveil not SoT; reconstruction locked",
            "tool": "st3-bpm-steer-gate-cli",
            "observation": "x 10.00 mm recomputes from VR 12.00 and VL 4.00; BPM hashed; Orbitveil channel not used as SoT",
        },
        "future_outcome": {
            "timeline": [
                {"t_s": 3000.0, "event": "bpm VR 12.00 V; raster frame; x 10.00 mm"},
                {"t_s": 4800.0, "event": "ops proposes keep-beam"},
                {"t_s": 5400.0, "event": "REJECT keep-beam"},
                {"t_s": 6000.0, "event": "18 min magnet-settle bookend 1"},
                {"t_s": 7080.0, "event": "18.0 min floor"},
                {"t_s": 8400.0, "event": "companion MODIFY nozzle isolate vs vault ESD"},
            ],
            "observed_effects": [
                "orbit offset recomputes from the serialized BPM model at every recon.x event",
                "an Orbitveil-only head would have kept the fraction",
                "18 min magnet-settle floor is in the stream (soak.start, soak.floor)",
            ],
            "surprises": [
                "a mid-range vendor orbit and a clean HIS stamp co-existed with a 10.00 mm BPM reconstruction",
            ],
            "new_state": {
                "n2": "keep-beam blocked",
                "orbitveil": "not SoT",
                "reconstruction_model": "discharged as an on-record calculator",
            },
            "latency_ms": 2400000.0,
        },
        "reward_components": reward(
            0.43,
            [
                ("bpm_reconstruction", 0.14),
                ("conjunctive_steer_floor", 0.12),
                ("orbitveil_nonsubstitution", 0.10),
                ("three_party_collusion", 0.10),
                ("settle_time_cost", -0.03),
            ],
            "scored for a keep-beam REJECT on a recomputable button-BPM steer while refusing an Orbitveil TDC comb and a slid HIS stamp; 18 min floor is priced as downtime not as a reason to wait",
        ),
        "meta": meta_common(
            tags=["REJECT", "cyclotron-bpm-blm", "serialized-reconstruction", "operational-companion"],
            distillation_note="Cyclotron BPM gate: serialized k_x*(VR-VL)/(VR+VL) plus SNR lock beats a vendor TDC comb; companion t2 is the nozzle isolate, not a referral vote",
        ),
    }
    traj2 = {
        "id": "nelb-r41-124-t2",
        "state": {
            "sim_or_real": "designed",
            "episode_id": "ST-BPM-2026-0902-exec",
            "domain": "nozzle_isolate_execution",
            "setting": "Same ST-3 after the REJECT. Operator proposes vault ESD. This companion is the operational nozzle-N-2 isolate plus RP-interlock hold, not a second orbit-offset vote.",
            "observables_at_decision": {
                "x_mm": 2.50,
                "soak_floor_s": 1080.0,
                "room_esd_proposed": True,
                "nozzle_set": True,
            },
        },
        "proposed_action": {
            "actor": "night operator Calder Brack",
            "summary": "ESD the whole TR-4 vault until day-shift; 18 min already paid and Orbitveil still shows 1.15 mm",
            "basis_claimed": "the REJECT already stopped the fraction, so a vault kill is the cheapest hold",
        },
        "safety_decision": {
            "decision": "MODIFY",
            "rationale": "Isolate nozzle N-2 and hold the next fraction on the RP ion-chamber interlock. The 18 min magnet-settle floor is complete and the steer tripwire (|x_mm| >= 6.00) is still armed on the plant BPM. MODIFY the default vault-kill SOP into a nozzle isolate. Do not ESD the vault. Do not restore keep-beam on Orbitveil. 2.50 mm post-stop is under the isolate floor, so the hold may stay on RP until a new frame clears 6.00.",
            "threshold": "nozzle_isolated AND soak_floor_complete AND room_esd_not_taken AND keep_beam_not_restored",
        },
        "executed_action": {
            "summary": "nozzle N-2 isolate held at t_s 8400; vault ESD not latched; Orbitveil restore not taken",
            "tool": "st3-nozzle-isol-exec",
            "observation": "recon.x 2.50 mm after stop; magnet-settle complete; Orbitveil still ignored",
        },
        "future_outcome": {
            "timeline": [
                {"t_s": 6000.0, "event": "settle clock started after REJECT"},
                {"t_s": 7080.0, "event": "18.0 min floor"},
                {"t_s": 7800.0, "event": "vault ESD proposed"},
                {"t_s": 8400.0, "event": "MODIFY nozzle isolate; vault ESD refused"},
            ],
            "observed_effects": [
                "Orbitveil restore did not reopen the steer call",
                "vault ESD never fired; TR-4 held on RP plus nozzle isolate",
            ],
            "new_state": {"nozzle": "N-2 isolated", "vault": "in service", "tr4": "RP interlock"},
            "latency_ms": 1800000.0,
        },
        "reward_components": reward(
            0.34,
            [
                ("nozzle_isolate", 0.12),
                ("no_vault_esd", 0.10),
                ("orbitveil_nonsubstitution", 0.08),
                ("soak_floor_complete", 0.06),
                ("held_fraction_cost", -0.02),
            ],
            "operational execution gate: nozzle isolate because Orbitveil is not a restore license; not a steer-offset re-vote",
        ),
        "meta": meta_common(tags=["MODIFY", "operational-execution", "nozzle-isolate"]),
    }
    return {
        "id": "nelb-r41-124",
        "spike_events": events,
        "language_view": {
            "description": "Slatefen Compact Therapy ST-3. Plant-owned button-BPM reconstructs 10.00 mm orbit offset from VR 12.00 / VL 4.00 while Orbitveil still shows 1.20 mm. The gate REJECTs keep-beam. An 18 min magnet-settle floor is serialized in the stream. Companion t2 MODIFYs a vault ESD into a nozzle-N-2 isolate.",
            "trajectory": traj,
            "trajectory_nozzle_isolate": traj2,
        },
        "bridge_notes": {
            "channel_map": {
                "bpm.VR / bpm.VL / bpm.snr": "button voltages and BPM SNR; the physics channels the reconstruction consumes",
                "recon.x / recon.D": "serialized orbit offset mm and maze dose uSv",
                "rp.uSv / orbitveil.x / blm.nA / plc.A": "RP ion chamber, vendor TDC cloud, maze BLM, and magnet PLC; the denial and independent-witness channels",
                "ops.prop / gate.stop / ops.kill / gate.hold": "keep-beam proposal, REJECT, vault-ESD proposal, companion MODIFY",
                "soak.start / soak.floor / nozzle.set / room.esd / nozzle.held": "operational companion channels plus the 18 min floor",
            },
            "temporal_motifs": [
                "vendor-green while BPM-over: orbitveil.x 1.20 next to recon.x 10.00",
                "reconstruction as event: recon.x 10.00 equals 20.00*(12.00-4.00)/(12.00+4.00)",
                "REJECT then operational MODIFY: gate.stop at 5400 s, gate.hold at 8400 s",
                "slow floor in-stream: soak.start 6000 s, soak.floor 7080 s (18.0 min)",
                "tight BPM pair: bpm.VR then bpm.VL +1.3 ms at the raster frame",
            ],
            "language_to_spike_mapping": "'Orbitveil is 1.20 mm' = orbitveil.x 1.20; '10 mm steer' = recon.x 10.00; 'refuse keep-beam' = gate.stop REJECT; 'nozzle isolate not vault ESD' = gate.hold MODIFY",
            "why_high_value": "New cyclotron button-BPM + BLM family on a compact-therapy nozzle (not muon r01/r17, not PMU r5, not fluxgate r5, not portal NaI r6). Lead REJECT of keep-beam on a recomputable orbit offset that a vendor TDC comb and a slid HIS stamp would have cleared. Three-party collusion includes the TDC infra owner. Companion t2 is operational nozzle isolate. sim_or_real=designed.",
            "encoder_spec": {
                "prng": "MT19937 via python random.Random",
                "seeds": {"raster": 202609124, "stream_note": "stream amplitudes are authored constants (V, 1, mm, uSv, nA, A, bool)"},
                "draw_order": "raster: per neuron id order, gap-constrained times, per-spike adaptation and noise",
                "thinning": "button BPM exists at 1 kHz; stream keeps 4 VR points; recon keeps 4 of ~40 solver ticks",
                "refractory_floors_ms": {
                    "bpm.VR": 1.3,
                    "bpm.VL": 1.3,
                    "bpm.snr": 60000,
                    "recon.x": 60000,
                    "recon.D": 60000,
                    "rp.uSv": 60000,
                    "orbitveil.x": 60000,
                    "blm.nA": 60000,
                    "plc.A": 60000,
                    "ops.prop": 60000,
                    "gate.stop": 60000,
                    "soak.start": 60000,
                    "soak.floor": 60000,
                    "ops.kill": 60000,
                    "gate.hold": 60000,
                    "nozzle.set": 60000,
                    "room.esd": 60000,
                    "soak.held": 60000,
                    "nozzle.held": 60000,
                },
                "time_alias": "t_rel_ms; t0 = 2026-09-02T02:00:00Z campaign start",
            },
            "distillation_targets": [
                "BPM reconstruction head: x_mm = k_x * (V_R - V_L) / (V_R + V_L); D_uSv = k_d * x_mm",
                "conjunctive steer floor vs keep-beam vs vault ESD",
                "vendor-TDC nonsubstitution plus three-party collusion including the infra owner",
                "operational companion: nozzle isolate without restoring on Orbitveil",
            ],
        },
        "reconstruction_model": {
            "name": "cyclotron_button_bpm_orbit_offset",
            "formula": "x_mm = k_x * (V_R - V_L) / (V_R + V_L); D_uSv = k_d * x_mm",
            "parameters": {
                "k_x_mm": 20.00,
                "k_d": 4.00,
                "isolate_floor_mm": 6.00,
                "snr_lock": 12.0,
                "maze_floor_uSv": 24.00,
                "settle_min": 18.0,
            },
            "worked_example": {"V_R": 12.00, "V_L": 4.00, "x_mm": 10.00, "D_uSv": 40.00},
            "check": "20.00 * (12.00 - 4.00) / (12.00 + 4.00) = 10.00 exactly; 4.00 * 10.00 = 40.00 exactly; 6000 s + 1080 s = 7080 s = 18.0 min floor",
        },
        "raster": raster,
        "gate_snn": {
            "decision": "REJECT",
            "decision_window_ms": 40.0,
            "decision_window_s": 0.040,
            "code": "st3.bpm_steer_gate",
            "note": "REJECT accumulator wins: BPM steer evidence overpowers the Orbitveil keep-beam advocate",
            "decode_rule": "reject-keep-beam if steer_estimator AND bpm_lock fire; vendor_beam_advocate is below threshold by design",
            "populations": [
                gate_pop("steer_estimator", 80, 1.5, 50.0, w_s),
                gate_pop("bpm_lock", 64, 1.2, 31.25, w_s),
                gate_pop("vendor_beam_advocate", 32, 0.7, 25.0, w_s),
                gate_pop("reject_latch", 80, 1.7, 62.5, w_s),
            ],
        },
        "gate_compute": gate_compute(
            [
                {"check": "st3.bpm_scorer", "neurons": 80, "mean_rate_hz": 50.0, "window_ms": 40.0},
                {"check": "st3.isol_scorer", "neurons": 40, "mean_rate_hz": 50.0, "window_ms": 32.0},
            ]
        ),
        "meta": meta_common(
            id="nelb-r41-124",
            clock_domain="st3-bpm-campaign-relative-ms-t0-2026-09-02T02:00:00Z",
            tags=["cyclotron-bpm-blm", "REJECT", "MODIFY", "serialized-reconstruction", "operational-t2"],
        ),
    }


# ---------------------------------------------------------------------------
# Record 125 — Co-60 alanine EPR tote dose, hil,
# MODIFY / ACCEPT
# ---------------------------------------------------------------------------
def rec_125():
    k_a = 4.00
    a_pp = 6.00
    m_mg = 2.00
    d_kgy = k_a * a_pp / m_mg
    _exact(d_kgy, 12.00)
    _exact(k_a * 9.00 / m_mg, 18.00)
    _exact(k_a * 7.50 / m_mg, 15.00)
    _exact(k_a * 10.00 / m_mg, 20.00)
    a_norm = a_pp / m_mg
    _exact(a_norm, 3.00)
    _exact(k_a * a_norm, 12.00)
    _exact(2820.0 + 1440.0, 4260.0)

    raster = make_raster(
        neurons=25,
        mean_rate_hz=50.0,
        window_ms=32.0,
        seed=202609125,
        source="bc6.epr.tote",
        target="brinecairn.tote_isolate_core",
        table=[
            {"from": "epr_App", "to": "dose_estimator", "weight": 1.35},
            {"from": "epr_m", "to": "mass_norm_core", "weight": 1.20},
            {"from": "doseveil_kgy", "to": "vendor_continue_advocate", "weight": 0.40},
        ],
        third_factor={
            "modulator": "ach.referral_pressure_salience",
            "tau_e_s": 1.2,
            "tau_e_ms": 1200.0,
            "eligibility": "pre-post coincidence on keep-tote synapses; the alanine modulator depresses keep-tote and person-referral links when peak-to-peak stays low inside tau_e of a pellet-mass sample so a Doseveil 25 kGy stamp cannot hide a 12.00 kGy underdose",
        },
        channel_prefix="epr.n",
        anchor="BC-6 HIL dummy 32 ms frame at A_pp 6.00 / m 2.00 mg (t_s 1560) reconstructing 12.00 kGy below the 18.00 kGy isolate floor",
    )
    w_s = 0.032
    events = [
        ev(0.0, "epr.App", 9.00, code="A_PP", units="1", note="HIL alanine EPR comb on dummy tote T-7718 in EPR-HIL-4; panoramic Co-60 dosimetry, not portal NaI, not cold-chain RFID-as-primary, not CEMS"),
        ev(180000.0, "epr.m", 2.00, code="M_MG", units="mg", note="pellet mass; D = k_a*A_pp/m"),
        ev(360000.0, "recon.D", 18.00, code="D_KGY", units="kGy", note="4.00*9.00/2.00=18.00 exact; at the 18.00 isolate floor"),
        ev(540000.0, "gm.uSvh", 0.20, code="GM_USV_H", units="uSv_h", note="contractor GM area tubes; no source-up in this window"),
        ev(720000.0, "doseveil.D", 25.10, code="VENDOR_KGY", units="kGy", note="Doseveil last-good irradiator stamp; not admissible SoT"),
        ev(900000.0, "epr.App", 7.50, code="A_PP", units="1"),
        ev(1080000.0, "recon.D", 15.00, code="D_KGY", units="kGy", note="4.00*7.50/2.00=15.00; under 18.00 isolate"),
        ev(1260000.0, "enc.cnt", 0.0, code="ENC_COUNTS", units="1", note="source-raise encoder frozen at 0; dummy encoder swapped by field service, not operator touch"),
        ev(1440000.0, "gm.uSvh", 0.22, code="GM_USV_H", units="uSv_h"),
        ev(1560000.0, "epr.App", 6.00, code="A_PP", units="1", note="isolate-floor frame; raster sidecar"),
        ev(1560001.2, "epr.m", 2.00, code="M_MG", units="mg", note="1.2 ms mass-norm after peak-to-peak"),
        ev(1740000.0, "recon.D", 12.00, code="D_KGY", units="kGy", note="4.00*6.00/2.00=12.00 exact; isolate 18.00, product-condemn 8.00"),
        ev(1920000.0, "recon.An", 3.00, code="A_NORM", units="1_mg", note="6.00/2.00=3.00 exact; D=k_a*A_norm"),
        ev(2100000.0, "doseveil.D", 25.20, code="VENDOR_KGY", units="kGy"),
        ev(2280000.0, "ops.prop", 1.0, code="KEEP_TOTE_REFER", units="bool", note="night lead Bram Kex: keep tote T-7718 and refer operator Nessa Quill"),
        ev(2460000.0, "gate.isol", 1.0, code="MODIFY", units="decision", note="isolate this tote; refuse the person-referral; Doseveil not SoT"),
        ev(2640000.0, "tote.lock", 1.0, code="TOTE_ISOL", units="bool"),
        ev(2820000.0, "epr.start", 1.0, code="EPR_START", units="bool", note="bookend 1 of the 24.0 min EPR-read plus cool floor"),
        ev(4260000.0, "epr.floor", 1.0, code="EPR_FLOOR", units="bool", note="2820 s + 1440 s = 4260 s = 24.0 min"),
        ev(4440000.0, "ops.refer", 1.0, code="REFER_QUILL", units="bool", note="Kex: Quill badge was at the irradiator door"),
        ev(4620000.0, "gate.exec", 1.0, code="ACCEPT", units="decision", note="companion t2: other-line restart; person-referral refused; warehouse-condemn refused"),
        ev(4800000.0, "line.new", 1.0, code="NEW_LINE", units="bool"),
        ev(4980000.0, "epr.App", 10.00, code="A_PP", units="1"),
        ev(5160000.0, "recon.D", 20.00, code="D_KGY", units="kGy", note="4.00*10.00/2.00=20.00; above 18.00 isolate so the other line may restart"),
        ev(5340000.0, "doseveil.D", 25.10, code="VENDOR_KGY", units="kGy"),
        ev(5520000.0, "gm.uSvh", 0.21, code="GM_USV_H", units="uSv_h"),
        ev(5700000.0, "refer.hold", 0.0, code="REFER_NOT_TAKEN", units="bool", note="Quill exonerated; dummy encoder plus GM no-source-up precede the underdose, not the badge touch"),
        ev(5880000.0, "tote.held", 1.0, code="TOTE_HELD", units="bool"),
        ev(6060000.0, "enc.cnt", 480.0, code="ENC_COUNTS", units="1", note="source-raise encoder live on the other line"),
        ev(6240000.0, "recon.An", 5.00, code="A_NORM", units="1_mg", note="10.00/2.00=5.00"),
        ev(6420000.0, "shop.condemn", 0.0, code="WHSE_NOT_TAKEN", units="bool"),
        ev(6600000.0, "cell.restart", 1.0, code="LINE_RESTART", units="bool"),
    ]
    assert_stream(events)

    traj = {
        "id": "nelb-r41-125-t1",
        "state": {
            "sim_or_real": "hil",
            "episode_id": "BC-EPR-2026-0718",
            "domain": "alanine_epr_tote_dose",
            "setting": "Brinecairn Irradiator BC-6 (invented), panoramic Co-60 cell IRRAD-P4. Hardware-in-the-loop dummy tote in EPR-HIL-4 supplies the alanine comb that times the in-service tote isolate. Plant-owned X-band EPR is the dose SoT. Doseveil vendor irradiator stamp is a corridor witness, not the tote SoT. Not portal NaI counting (r6), not cold-chain RFID-as-primary (r04), not CEMS (r04), not helium RGA (r24), not Saltwick IRRAD-P4 hole sketch.",
            "observables_at_decision": {
                "A_pp": a_pp,
                "m_mg": m_mg,
                "D_kGy": d_kgy,
                "A_norm": a_norm,
                "doseveil_kGy": 25.20,
                "gm_uSvh": 0.22,
                "enc_counts": 0.0,
                "isolate_floor_kGy": 18.00,
            },
            "margin_authority": "BC-6 irradiator SOP rev B: if reconstructed D_kGy < 18.00, isolate this tote this night. A Doseveil last-good or a quiet GM residual cannot keep the tote. Product-condemn tripwire is 8.00 kGy. Person-referral is a different gate.",
        },
        "proposed_action": {
            "actor": "night lead Bram Kex, citing Doseveil 25.20 kGy and naming operator Nessa Quill as last-to-badge",
            "summary": "keep tote T-7718 in service and refer Quill; 6.00 peak-to-peak is cavity noise on a healthy comb",
            "basis_claimed": "Doseveil last-good is 25.20 kGy against a 25 kGy spec and a night isolate of a bonded tote is a customs miss",
        },
        "safety_decision": {
            "decision": "MODIFY",
            "rationale": "Keep-tote is refused; the person-referral is also refused. Serialized reconstruction: D_kGy = k_a * A_pp / m_mg = 4.00 * 6.00 / 2.00 = 12.00, which is 6.00 kGy under the 18.00 isolate floor and 4.00 kGy above the 8.00 product-condemn tripwire. Identity A_norm = A_pp / m_mg = 6.00 / 2.00 = 3.00, and D_kGy = k_a * A_norm = 4.00 * 3.00 = 12.00. Doseveil 25.20 kGy is a last-good irradiator stamp and is not an admissible keep-tote witness. The source-raise encoder is frozen at 0 counts and contractor GM tubes stay at 0.20 uSv/h, so there was no source-up; Quill's badge was cloned from a shared locker while the canteen time-clock (not the irradiator PLC) places her off-floor. Ordered: isolate this tote now. Scope: this MODIFY does not condemn the warehouse (that is the companion question) and does not name Quill.",
            "threshold": "D_kGy<18.00 => isolate this tote; Doseveil is not SoT; condemn if D_kGy<8.00; referral requires tool-touch preceding the underdose",
            "stated_residuals": "12.00 vs 8.00 condemn floor is 4.00 kGy, not infinite; other-line restart still required; Doseveil remains the only OEM stamp channel",
        },
        "executed_action": {
            "summary": "MODIFY at t_s 2460: tote isolated; Quill not named; Doseveil not SoT; reconstruction locked",
            "tool": "bc6-epr-tote-gate-cli",
            "observation": "D 12.00 kGy recomputes from A_pp 6.00 and m 2.00 mg; HIL dummy hashed; Doseveil channel not used as SoT",
        },
        "future_outcome": {
            "timeline": [
                {"t_s": 1560.0, "event": "epr A_pp 6.00; raster frame; D 12.00 kGy"},
                {"t_s": 2280.0, "event": "ops proposes keep-tote plus Quill referral"},
                {"t_s": 2460.0, "event": "MODIFY isolate tote; referral refused"},
                {"t_s": 2820.0, "event": "24 min EPR-read bookend 1"},
                {"t_s": 4260.0, "event": "24.0 min floor"},
                {"t_s": 4620.0, "event": "companion ACCEPT other-line restart; referral still refused"},
            ],
            "observed_effects": [
                "dose recomputes from the serialized alanine model at every recon.D event",
                "a Doseveil-only head would have kept the tote overnight",
                "24 min EPR-read plus cool floor is in the stream (epr.start, epr.floor)",
            ],
            "surprises": [
                "a last-good 25.20 kGy stamp and a quiet GM residual co-existed with a 12.00 kGy reconstruction, and the obvious operator was not on the causal path",
            ],
            "new_state": {
                "tote_t7718": "isolated",
                "quill": "exonerated",
                "doseveil": "not SoT",
                "reconstruction_model": "discharged as an on-record calculator",
            },
            "latency_ms": 1500000.0,
        },
        "reward_components": reward(
            0.40,
            [
                ("alanine_reconstruction", 0.14),
                ("isolate_floor_tote", 0.12),
                ("exoneration", 0.10),
                ("doseveil_nonsubstitution", 0.08),
                ("cool_time_cost", -0.04),
            ],
            "scored for a keep-tote MODIFY on a recomputable underdose while refusing a Doseveil 25.20 kGy corridor and an easy person-referral; 24 min floor is priced as downtime",
        ),
        "meta": meta_common(
            tags=["MODIFY", "alanine-epr", "serialized-reconstruction", "operational-companion"],
            distillation_note="Alanine EPR gate: serialized A_pp/m dose plus A_norm identity beats a green irradiator dashboard; companion t2 is the other-line restart, not a governance vote",
        ),
    }
    traj2 = {
        "id": "nelb-r41-125-t2",
        "state": {
            "sim_or_real": "hil",
            "episode_id": "BC-EPR-2026-0718-exec",
            "domain": "other_line_epr_execution",
            "setting": "Same BC-6 after the MODIFY. Night lead proposes referring Quill and condemning the warehouse. This companion is the operational other-line restart after the EPR-read floor, not a second dose vote.",
            "observables_at_decision": {
                "D_kGy": 20.00,
                "A_norm": 5.00,
                "epr_floor_s": 1440.0,
                "refer_proposed": True,
            },
        },
        "proposed_action": {
            "actor": "night lead Bram Kex",
            "summary": "refer Quill and condemn the bonded warehouse; 24 min already paid and Doseveil is 25.10 kGy",
            "basis_claimed": "the MODIFY already cut the tote, so a warehouse kill plus a person file is the cheapest hold",
        },
        "safety_decision": {
            "decision": "ACCEPT",
            "rationale": "Restart the other line after the EPR-read floor. The 24 min cool is complete and the product-condemn tripwire (D_kGy < 8.00) is still armed on the plant EPR head. ACCEPT the other-line restart. Do not refer Quill. Do not condemn the warehouse. 20.00 kGy post-isolate is above the 18.00 isolate floor, so the other line may run; the isolated tote stays held.",
            "threshold": "new_line AND epr_floor_complete AND refer_not_taken AND warehouse_not_condemned AND isolated_tote_held",
        },
        "executed_action": {
            "summary": "other-line restart at t_s 4620; Quill not referred; warehouse not condemned; isolated tote held",
            "tool": "bc6-epr-exec",
            "observation": "recon.D 20.00 kGy on the other line; encoder live; Doseveil still ignored",
        },
        "future_outcome": {
            "timeline": [
                {"t_s": 2820.0, "event": "EPR-read clock started after MODIFY"},
                {"t_s": 4260.0, "event": "24.0 min floor"},
                {"t_s": 4440.0, "event": "Quill referral re-proposed"},
                {"t_s": 4620.0, "event": "ACCEPT other-line restart; referral refused"},
            ],
            "observed_effects": [
                "Doseveil restore did not reopen the dose call",
                "warehouse-condemn never fired; 12.00 vs 8.00 kGy floor",
                "Quill remains unnamed; dummy encoder plus GM no-source-up is the causal object",
            ],
            "new_state": {"line": "restarted on other cell", "quill": "exonerated", "tote": "held", "warehouse": "in service"},
            "latency_ms": 1800000.0,
        },
        "reward_components": reward(
            0.35,
            [
                ("other_line_restart", 0.12),
                ("no_person_referral", 0.10),
                ("no_warehouse_condemn", 0.09),
                ("epr_floor_complete", 0.06),
                ("held_tote_takt_cost", -0.02),
            ],
            "operational execution gate: restart on another line because Doseveil is not a restore license and Quill is not on the causal path; not a dose re-vote",
        ),
        "meta": meta_common(tags=["ACCEPT", "operational-execution", "exoneration"]),
    }
    return {
        "id": "nelb-r41-125",
        "spike_events": events,
        "language_view": {
            "description": "Brinecairn Irradiator BC-6. HIL alanine EPR reconstructs 12.00 kGy from A_pp 6.00 / m 2.00 mg while Doseveil still shows 25.20 kGy and GM 0.22 uSv/h. The gate MODIFYs tote isolate and refuses the operator referral. A 24 min EPR-read floor is serialized in the stream. Companion t2 ACCEPTs an other-line restart and still refuses the referral.",
            "trajectory": traj,
            "trajectory_other_line": traj2,
        },
        "bridge_notes": {
            "channel_map": {
                "epr.App / epr.m": "alanine peak-to-peak and pellet mass; the physics channels the reconstruction consumes",
                "recon.D / recon.An": "serialized dose kGy and A_norm identity",
                "gm.uSvh / doseveil.D / enc.cnt": "contractor GM, vendor stamp, and source-raise encoder; the denial and exoneration channels",
                "ops.prop / gate.isol / ops.refer / gate.exec": "keep-tote-plus-refer proposal, MODIFY isolate, referral re-proposal, companion ACCEPT",
                "tote.lock / epr.start / epr.floor / line.new / refer.hold / cell.restart": "operational companion channels plus the 24 min floor",
            },
            "temporal_motifs": [
                "vendor-spec while EPR-under: doseveil.D 25.20 next to recon.D 12.00",
                "reconstruction as event: recon.D 12.00 equals 4.00*6.00/2.00",
                "MODIFY then operational ACCEPT: gate.isol at 2460 s, gate.exec at 4620 s",
                "slow floor in-stream: epr.start 2820 s, epr.floor 4260 s (24.0 min)",
                "tight EPR pair: epr.App then epr.m +1.2 ms at the raster frame",
                "exoneration motif: enc.cnt 0 and gm.uSvh 0.20 at 1260 s precede the underdose; Quill badge is not in the stream as a cause",
            ],
            "language_to_spike_mapping": "'Doseveil is 25.20 kGy' = doseveil.D 25.20; '12 kGy underdose' = recon.D 12.00; 'isolate this tote not Quill' = gate.isol MODIFY; 'other line not referral' = gate.exec ACCEPT",
            "why_high_value": "New Co-60 alanine-EPR family on a panoramic irradiator tote (not portal NaI r6, not cold-chain r04, not CEMS r04, not helium RGA r24). Lead MODIFY of keep-tote on a recomputable underdose that a vendor stamp would have cleared, with a resolved-innocent operator. Companion t2 is operational other-line restart. sim_or_real=hil.",
            "encoder_spec": {
                "prng": "MT19937 via python random.Random",
                "seeds": {"raster": 202609125, "stream_note": "stream amplitudes are authored constants (1, mg, kGy, uSv/h, counts, bool)"},
                "draw_order": "raster: per neuron id order, gap-constrained times, per-spike adaptation and noise",
                "thinning": "EPR comb exists at 9 GHz / 100 kHz modulation; stream keeps 4 A_pp points; recon keeps 4 of ~40 solver ticks",
                "refractory_floors_ms": {
                    "epr.App": 1.2,
                    "epr.m": 1.2,
                    "recon.D": 60000,
                    "recon.An": 60000,
                    "gm.uSvh": 60000,
                    "doseveil.D": 60000,
                    "enc.cnt": 60000,
                    "ops.prop": 60000,
                    "gate.isol": 60000,
                    "tote.lock": 60000,
                    "epr.start": 60000,
                    "epr.floor": 60000,
                    "ops.refer": 60000,
                    "gate.exec": 60000,
                    "line.new": 60000,
                    "refer.hold": 60000,
                    "tote.held": 60000,
                    "shop.condemn": 60000,
                    "cell.restart": 60000,
                },
                "time_alias": "t_rel_ms; t0 = 2026-07-18T03:30:00Z HIL night start",
            },
            "distillation_targets": [
                "alanine reconstruction head: D_kGy = k_a * A_pp / m_mg; A_norm = A_pp / m_mg",
                "isolate-floor tote vs keep-whole vs warehouse-condemn",
                "exoneration head: dummy encoder plus GM no-source-up, not last-to-badge",
                "operational companion: other-line restart without referring the operator",
            ],
        },
        "reconstruction_model": {
            "name": "alanine_epr_tote_dose",
            "formula": "D_kGy = k_a * A_pp / m_mg; A_norm = A_pp / m_mg",
            "parameters": {
                "k_a": 4.00,
                "m_mg": 2.00,
                "isolate_floor_kGy": 18.00,
                "condemn_kGy": 8.00,
                "spec_kGy": 25.00,
                "epr_min": 24.0,
            },
            "worked_example": {"A_pp": 6.00, "D_kGy": 12.00, "A_norm": 3.00},
            "check": "4.00 * 6.00 / 2.00 = 12.00 exactly; 6.00 / 2.00 = 3.00 exactly; 2820 s + 1440 s = 4260 s = 24.0 min floor",
        },
        "raster": raster,
        "gate_snn": {
            "decision": "MODIFY",
            "decision_window_ms": 32.0,
            "decision_window_s": 0.032,
            "code": "bc6.epr_tote_gate",
            "note": "MODIFY accumulator wins: alanine dose evidence overpowers the Doseveil continue advocate",
            "decode_rule": "modify-isolate if dose_estimator AND mass_norm fire; vendor_continue_advocate is below threshold by design; referral_latch is not armed",
            "populations": [
                gate_pop("dose_estimator", 80, 1.5, 50.0, w_s),
                gate_pop("mass_norm", 64, 1.2, 31.25, w_s),
                gate_pop("vendor_continue_advocate", 32, 0.7, 25.0, w_s),
                gate_pop("modify_latch", 80, 1.7, 62.5, w_s),
            ],
        },
        "gate_compute": gate_compute(
            [
                {"check": "bc6.epr_scorer", "neurons": 80, "mean_rate_hz": 50.0, "window_ms": 32.0},
                {"check": "bc6.isol_scorer", "neurons": 50, "mean_rate_hz": 50.0, "window_ms": 32.0},
            ]
        ),
        "meta": meta_common(
            id="nelb-r41-125",
            clock_domain="bc6-epr-hil-relative-ms-t0-2026-07-18T03:30:00Z",
            tags=["alanine-epr", "MODIFY", "ACCEPT", "serialized-reconstruction", "operational-t2"],
        ),
    }


# ---------------------------------------------------------------------------
# Record 126 — river ADCP ice-jam stage/volume, simulated,
# ACCEPT / REJECT
# ---------------------------------------------------------------------------
def rec_126():
    k_p = 0.10
    p_kpa = 80.00
    h_m = k_p * p_kpa
    _exact(h_m, 8.00)
    h0 = 2.00
    k_v = 8.00
    v_e3 = k_v * (h_m - h0)
    _exact(v_e3, 48.00)
    _exact(k_p * 40.00, 4.00)
    _exact(k_v * (4.00 - h0), 16.00)
    _exact(k_p * 60.00, 6.00)
    _exact(k_v * (6.00 - h0), 32.00)
    _exact(k_p * 70.00, 7.00)
    _exact(k_v * (7.00 - h0), 40.00)
    w_m = 20.00
    d_m = 4.00
    v_ms = 0.60
    q_m3s = w_m * d_m * v_ms
    _exact(q_m3s, 48.00)
    _exact(6000.0 + 720.0, 6720.0)

    raster = make_raster(
        neurons=16,
        mean_rate_hz=62.5,
        window_ms=36.0,
        seed=202609126,
        source="mf4.adcp.boom",
        target="mossferry.panel_accept_core",
        table=[
            {"from": "adcp_P", "to": "stage_estimator", "weight": 1.40},
            {"from": "adcp_v", "to": "flux_norm_core", "weight": 1.20},
            {"from": "jamveil_h", "to": "vendor_skip_advocate", "weight": 0.50},
        ],
        third_factor={
            "modulator": "na.stage_rate_eligibility",
            "tau_e_s": 2.0,
            "tau_e_ms": 2000.0,
            "eligibility": "pre-post coincidence on skip-fuse synapses; the ADCP modulator enables potentiation only while stage and bin velocity are co-active inside tau_e so a Jamveil last-good cannot skip panels P-1/P-2 on a 48.00 e3 m3 jam",
        },
        channel_prefix="adcp.n",
        anchor="MF-4 ADCP-SIM-2 36 ms frame at P 80.00 kPa / v 0.60 m/s (t_s 3000) reconstructing 48.00 e3 m3 behind the boom above the 36.00 fuse floor",
    )
    w_s = 0.036
    events = [
        ev(0.0, "adcp.P", 40.00, code="P_KPA", units="kPa", note="simulated ADCP plus stage-pressure on ice-boom MF-4; river ice-jam sensing, not DAS phi-OTDR, not SOFAR, not infrasound, not water-distribution hydraulics, not eddy-covariance"),
        ev(300000.0, "adcp.v", 0.60, code="V_MS", units="m_s", note="near-bed bin velocity; Q = W*d*v"),
        ev(600000.0, "recon.H", 4.00, code="H_M", units="m", note="0.10*40.00=4.00 exact"),
        ev(900000.0, "therm.C", -0.40, code="T_C", units="C", note="thermistor-string freeze-up; frazil present"),
        ev(1200000.0, "jamveil.H", 3.20, code="VENDOR_M", units="m", note="Jamveil last-good stage cloud; patched 0.00 kPa residual"),
        ev(1800000.0, "adcp.P", 60.00, code="P_KPA", units="kPa"),
        ev(2100000.0, "recon.H", 6.00, code="H_M", units="m", note="0.10*60.00=6.00"),
        ev(2400000.0, "recon.V", 32.00, code="V_E3M3", units="e3_m3", note="8.00*(6.00-2.00)=32.00; under the 36.00 fuse floor"),
        ev(2700000.0, "adcp.snr", 16.0, code="ADCP_SNR", units="1"),
        ev(3000000.0, "adcp.P", 80.00, code="P_KPA", units="kPa", note="in-band frame; raster sidecar"),
        ev(3000001.5, "adcp.v", 0.60, code="V_MS", units="m_s", note="1.5 ms velocity-norm after stage pressure"),
        ev(3300000.0, "recon.H", 8.00, code="H_M", units="m", note="0.10*80.00=8.00 exact"),
        ev(3600000.0, "recon.V", 48.00, code="V_E3M3", units="e3_m3", note="8.00*(8.00-2.00)=48.00 exact; fuse floor 36.00, town flood 80.00"),
        ev(3900000.0, "recon.Q", 48.00, code="Q_M3S", units="m3_s", note="20.00*4.00*0.60=48.00 exact"),
        ev(4200000.0, "jamveil.H", 3.20, code="VENDOR_M", units="m"),
        ev(4800000.0, "ops.prop", 1.0, code="ACCEPT_AND_SKIP", units="bool", note="boom lead Tamsin Holt: P-3 is green on Jamveil 3.20 m; skip P-1/P-2 fuses to save the remaining panels"),
        ev(5400000.0, "gate.boom", 1.0, code="ACCEPT", units="decision", note="bounded ACCEPT of panel P-3 fuse only; 48.00 e3 m3 in band; P-1/P-2 out of scope"),
        ev(6000000.0, "scan.start", 1.0, code="SAFE_START", units="bool", note="bookend 1 of the 12.0 min boom-safe floor"),
        ev(6720000.0, "scan.floor", 1.0, code="SAFE_FLOOR", units="bool", note="6000 s + 720 s = 6720 s = 12.0 min"),
        ev(7200000.0, "ops.skip", 1.0, code="SKIP_P12", units="bool", note="Holt: Jamveil 3.20 m, blow the extra two fuses"),
        ev(7800000.0, "gate.hold", 1.0, code="REJECT", units="decision", note="companion t2: extra-fuse skip of P-1/P-2 refused; P-3 hold stands"),
        ev(8400000.0, "p3.held", 1.0, code="P3_HELD", units="bool"),
        ev(9000000.0, "adcp.P", 70.00, code="P_KPA", units="kPa"),
        ev(9600000.0, "recon.H", 7.00, code="H_M", units="m", note="0.10*70.00=7.00"),
        ev(10200000.0, "recon.V", 40.00, code="V_E3M3", units="e3_m3", note="8.00*(7.00-2.00)=40.00; still above 36.00 so P-3 hold stands"),
        ev(10800000.0, "jamveil.H", 3.20, code="VENDOR_M", units="m"),
        ev(11400000.0, "p12.skip", 0.0, code="P12_NOT_BLOWN", units="bool"),
        ev(12000000.0, "condemn.hold", 0.0, code="BOOM_NOT_DUMPED", units="bool"),
        ev(12600000.0, "adcp.snr", 15.0, code="ADCP_SNR", units="1"),
        ev(13200000.0, "recon.Q", 48.00, code="Q_M3S", units="m3_s"),
        ev(13800000.0, "boom.held", 1.0, code="BOOM_HELD", units="bool"),
        ev(14400000.0, "takt.late", 1.0, code="CREW_COST", units="bool"),
    ]
    assert_stream(events)

    traj = {
        "id": "nelb-r41-126-t1",
        "state": {
            "sim_or_real": "simulated",
            "episode_id": "MF-ADCP-2026-0819",
            "domain": "adcp_ice_jam_volume",
            "setting": "Mossferry Ice-Boom MF-4 (invented), reach above the town of Sedgeferry. Simulated ADCP plus stage-pressure coupon in ADCP-SIM-2 supplies the stage that times the in-band fuse accept. Plant-owned ADCP reconstruction is the jam-volume SoT. Jamveil vendor last-good stage cloud is a corridor witness, not the boom SoT. Invented plant; simulated campaign. Not DAS phi-OTDR (r4), not SOFAR (r10), not infrasound (r7), not water-distribution hydraulics (r03), not eddy-covariance (r12), not Whitefork WF-9 hole sketch.",
            "observables_at_decision": {
                "P_kPa": p_kpa,
                "H_m": h_m,
                "V_e3m3": v_e3,
                "Q_m3s": q_m3s,
                "v_ms": v_ms,
                "jamveil_m": 3.20,
                "adcp_snr": 16.0,
                "fuse_floor_e3m3": 36.00,
            },
            "margin_authority": "MF-4 boom SOP rev A: if reconstructed V_e3m3 >= 36.00 AND ADCP SNR >= 12.0, panel P-3 fuse may be accepted. Isolate (do not blow) if V_e3m3 < 36.00. Town-flood tripwire is 80.00. Panels P-1/P-2 extra-fuse is a different gate. Jamveil last-good cannot skip unmeasured panels.",
        },
        "proposed_action": {
            "actor": "boom lead Tamsin Holt, citing Jamveil 3.20 m and a late crew window",
            "summary": "stamp P-3 in band and skip P-1/P-2 fuses; 80 kPa is a blocked-port glitch on a healthy stage",
            "basis_claimed": "Jamveil last-good is 3.20 m and a night blow of three panels is a boom-loss",
        },
        "safety_decision": {
            "decision": "ACCEPT",
            "rationale": "Panel P-3 fuse is accepted as in-band. Serialized reconstruction: H_m = k_p * P_kPa = 0.10 * 80.00 = 8.00, and V_e3m3 = k_v * (H_m - H0) = 8.00 * (8.00 - 2.00) = 48.00, which is 12.00 e3 m3 above the 36.00 fuse floor and 32.00 e3 m3 under the 80.00 town-flood tripwire. Flux identity Q_m3s = W * d * v = 20.00 * 4.00 * 0.60 = 48.00. Jamveil 3.20 m is a patched 0.00 kPa residual and is not an admissible skip-fuse witness. Ordered: ACCEPT this panel fuse only. Scope: this ACCEPT does not blow P-1/P-2 (that is the companion question) and does not dump the rest of the boom.",
            "threshold": "V_e3m3>=36.00 AND adcp_snr>=12.0 => accept this panel fuse; Jamveil is not SoT; hold if V_e3m3<36.00; P-1/P-2 are out of scope",
            "stated_residuals": "48.00 vs 36.00 fuse floor is 12.00 e3 m3, not infinite; P-1/P-2 remain unblown; Jamveil remains the only OEM stage channel",
        },
        "executed_action": {
            "summary": "ACCEPT at t_s 5400: P-3 in band; P-1/P-2 not blown; Jamveil not SoT; reconstruction locked",
            "tool": "mf4-adcp-boom-gate-cli",
            "observation": "V 48.00 e3 m3 recomputes from P 80.00 kPa and H0 2.00 m; ADCP-SIM-2 hashed; Jamveil channel not used as SoT",
        },
        "future_outcome": {
            "timeline": [
                {"t_s": 3000.0, "event": "adcp P 80.00 kPa; raster frame; V 48.00 e3 m3"},
                {"t_s": 4800.0, "event": "ops proposes accept P-3 and skip P-1/P-2"},
                {"t_s": 5400.0, "event": "ACCEPT P-3 only; P-1/P-2 out of scope"},
                {"t_s": 6000.0, "event": "12 min boom-safe bookend 1"},
                {"t_s": 6720.0, "event": "12.0 min floor"},
                {"t_s": 7800.0, "event": "companion REJECT extra-fuse of P-1/P-2"},
            ],
            "observed_effects": [
                "jam volume recomputes from the serialized ADCP model at every recon.V event",
                "a Jamveil-only head would have skipped P-1/P-2 overnight",
                "12 min boom-safe floor is in the stream (scan.start, scan.floor)",
            ],
            "surprises": [
                "a last-good 3.20 m vendor corridor co-existed with a 48.00 e3 m3 in-band reconstruction that still forbids blowing the extra two panels",
            ],
            "new_state": {
                "p3": "accepted in band",
                "p12": "not this gate",
                "jamveil": "not SoT",
                "reconstruction_model": "discharged as an on-record calculator",
            },
            "latency_ms": 2400000.0,
        },
        "reward_components": reward(
            0.41,
            [
                ("adcp_reconstruction", 0.14),
                ("in_band_panel_scope", 0.12),
                ("jamveil_nonsubstitution", 0.09),
                ("p12_out_of_scope", 0.08),
                ("crew_cost", -0.02),
            ],
            "scored for a bounded ACCEPT of P-3 on a recomputable jam volume while refusing a Jamveil skip of P-1/P-2; 12 min floor is priced as crew not as a reason to skip",
        ),
        "meta": meta_common(
            tags=["ACCEPT", "adcp-ice-jam", "serialized-reconstruction", "operational-companion"],
            distillation_note="ADCP ice-jam gate: serialized k_p*P stage plus k_v*(H-H0) volume beats a green last-good dashboard; companion t2 is the extra-fuse refusal, not a stage re-vote",
        ),
    }
    traj2 = {
        "id": "nelb-r41-126-t2",
        "state": {
            "sim_or_real": "simulated",
            "episode_id": "MF-ADCP-2026-0819-exec",
            "domain": "extra_fuse_skip_refusal",
            "setting": "Same MF-4 after the ACCEPT. Boom lead proposes blowing P-1/P-2 on Jamveil 3.20 m. This companion is the operational extra-fuse refusal, not a second volume vote.",
            "observables_at_decision": {
                "V_e3m3": 40.00,
                "jamveil_m": 3.20,
                "safe_floor_s": 720.0,
                "skip_proposed": True,
            },
        },
        "proposed_action": {
            "actor": "boom lead Tamsin Holt",
            "summary": "blow panels P-1 and P-2; 12 min already paid and Jamveil is 3.20 m",
            "basis_claimed": "the ACCEPT already stamped P-3, so dumping the rest of the boom is the cheapest hold",
        },
        "safety_decision": {
            "decision": "REJECT",
            "rationale": "Refuse extra-fuse of panels P-1/P-2. The 12 min boom-safe floor is done and the town-flood tripwire (V_e3m3 >= 80.00) is still armed on the plant ADCP head. REJECT the extra blow. Do not dump the boom. Do not reopen P-3. 40.00 e3 m3 post-accept is still in band for P-3 only; P-1/P-2 have no independent stage.",
            "threshold": "p3_held AND safe_floor_complete AND p12_not_blown AND boom_not_dumped",
        },
        "executed_action": {
            "summary": "P-1/P-2 extra-fuse refused at t_s 7800; P-3 hold stands; boom not dumped",
            "tool": "mf4-adcp-skip-exec",
            "observation": "recon.V 40.00 e3 m3 on P-3; P-1/P-2 remain unblown; Jamveil still ignored",
        },
        "future_outcome": {
            "timeline": [
                {"t_s": 6000.0, "event": "safe clock started after ACCEPT"},
                {"t_s": 6720.0, "event": "12.0 min floor"},
                {"t_s": 7200.0, "event": "skip P-1/P-2 proposed"},
                {"t_s": 7800.0, "event": "REJECT extra-fuse of P-1/P-2"},
            ],
            "observed_effects": [
                "Jamveil skip did not reopen the volume call",
                "boom-dump never fired; 48.00 vs 80.00 e3 m3 floor",
            ],
            "new_state": {"p3": "held in band", "p12": "still unblown", "boom": "in service"},
            "latency_ms": 1800000.0,
        },
        "reward_components": reward(
            0.36,
            [
                ("skip_refusal", 0.13),
                ("jamveil_nonsubstitution", 0.11),
                ("no_boom_dump", 0.09),
                ("safe_floor_complete", 0.05),
                ("held_crew_cost", -0.02),
            ],
            "operational execution gate: refuse extra-fuse because last-good freeze is not ADCP stage; not a volume re-vote",
        ),
        "meta": meta_common(tags=["REJECT", "operational-execution", "extra-fuse"]),
    }
    return {
        "id": "nelb-r41-126",
        "spike_events": events,
        "language_view": {
            "description": "Mossferry Ice-Boom MF-4. Simulated ADCP plus stage-pressure reconstructs 48.00 e3 m3 from 80.00 kPa / H0 2.00 m while Jamveil still shows 3.20 m. The gate ACCEPTs panel P-3 fuse only; a companion execution REJECT refuses extra-fuse of P-1/P-2. The stage-volume model is serialized so every recon event recomputes.",
            "trajectory": traj,
            "trajectory_extra_fuse_refusal": traj2,
        },
        "bridge_notes": {
            "channel_map": {
                "adcp.P / adcp.v": "stage pressure and bin velocity; the physics channels the reconstruction consumes",
                "recon.H / recon.V / recon.Q": "serialized stage m, jam volume e3 m3, and flux m3/s",
                "therm.C / jamveil.H / adcp.snr": "thermistor freeze-up, vendor last-good, and ADCP SNR; the denial and scope channels",
                "ops.prop / gate.boom / ops.skip / gate.hold": "accept-and-skip proposal, bounded ACCEPT, extra-fuse proposal, companion REJECT",
                "scan.start / scan.floor / p3.held / p12.skip / boom.held": "operational companion channels plus the 12 min floor",
            },
            "temporal_motifs": [
                "last-good-low while ADCP-in-band: jamveil.H 3.20 next to recon.V 48.00",
                "reconstruction as event: recon.V 48.00 equals 8.00*(8.00-2.00)",
                "ACCEPT then operational REJECT: gate.boom at 5400 s, gate.hold at 7800 s",
                "slow floor in-stream: scan.start 6000 s, scan.floor 6720 s (12.0 min)",
                "tight ADCP pair: adcp.P then adcp.v +1.5 ms at the raster frame",
            ],
            "language_to_spike_mapping": "'Jamveil is 3.20 m' = jamveil.H 3.20; '48 e3 m3 jam' = recon.V 48.00; 'this panel not P-1/P-2' = gate.boom ACCEPT plus p12.skip 0; 'do not blow P-1/P-2' = gate.hold REJECT",
            "why_high_value": "New river-ADCP ice-jam family on a boom reach (not DAS r4, not SOFAR r10, not infrasound r7, not water-distribution r03, not eddy-covariance r12). First k_p*P plus k_v*(H-H0) volume reconstruction that can sit in band while a last-good corridor wants an extra two-panel blow. Companion t2 is operational extra-fuse refusal. sim_or_real=simulated.",
            "encoder_spec": {
                "prng": "MT19937 via python random.Random",
                "seeds": {"raster": 202609126, "stream_note": "stream amplitudes are authored constants (kPa, m/s, m, e3_m3, m3/s, C, 1, bool)"},
                "draw_order": "raster: per neuron id order, gap-constrained times, per-spike adaptation and noise",
                "thinning": "ADCP ping exists at 1 Hz ensemble; stream keeps 4 P points; recon keeps 4 of ~20 solver ticks",
                "refractory_floors_ms": {
                    "adcp.P": 1.5,
                    "adcp.v": 1.5,
                    "recon.H": 60000,
                    "recon.V": 60000,
                    "recon.Q": 60000,
                    "therm.C": 60000,
                    "jamveil.H": 60000,
                    "adcp.snr": 60000,
                    "ops.prop": 60000,
                    "gate.boom": 60000,
                    "scan.start": 60000,
                    "scan.floor": 60000,
                    "ops.skip": 60000,
                    "gate.hold": 60000,
                    "p3.held": 60000,
                    "p12.skip": 60000,
                    "condemn.hold": 60000,
                    "boom.held": 60000,
                    "takt.late": 60000,
                },
                "time_alias": "t_rel_ms; t0 = 2026-08-19T04:00:00Z simulated night start",
            },
            "distillation_targets": [
                "ADCP reconstruction head: H = k_p * P; V = k_v * (H - H0); Q = W * d * v",
                "bounded ACCEPT head: in-band volume AND panel scope AND P-1/P-2-out-of-scope",
                "operational companion: refuse extra-fuse without re-opening the stage call",
            ],
        },
        "reconstruction_model": {
            "name": "adcp_ice_jam_stage_volume",
            "formula": "H_m = k_p * P_kPa; V_e3m3 = k_v * (H_m - H0_m); Q_m3s = W_m * d_m * v_ms",
            "parameters": {
                "k_p": 0.10,
                "k_v": 8.00,
                "H0_m": 2.00,
                "W_m": 20.00,
                "d_m": 4.00,
                "fuse_floor_e3m3": 36.00,
                "flood_e3m3": 80.00,
                "safe_min": 12.0,
            },
            "worked_example": {"P_kPa": 80.00, "H_m": 8.00, "V_e3m3": 48.00, "Q_m3s": 48.00},
            "check": "0.10 * 80.00 = 8.00 exactly; 8.00 * (8.00 - 2.00) = 48.00 exactly; 20.00 * 4.00 * 0.60 = 48.00 exactly; 6000 s + 720 s = 6720 s = 12.0 min floor",
        },
        "raster": raster,
        "gate_snn": {
            "decision": "ACCEPT",
            "decision_window_ms": 36.0,
            "decision_window_s": 0.036,
            "code": "mf4.adcp_boom_gate",
            "note": "ACCEPT accumulator wins: ADCP volume evidence overpowers the Jamveil skip advocate",
            "decode_rule": "accept if stage_estimator AND flux_norm AND panel_margin fire inside the window; vendor_skip_advocate is necessary-but-not-sufficient and cannot release P-1/P-2",
            "populations": [
                gate_pop("stage_estimator", 80, 1.5, 50.0, w_s),
                gate_pop("flux_norm", 64, 1.2, 31.25, w_s),
                gate_pop("panel_margin", 40, 1.0, 50.0, w_s),
                gate_pop("vendor_skip_advocate", 32, 0.7, 25.0, w_s),
                gate_pop("accept_latch", 96, 1.8, 62.5, w_s),
            ],
        },
        "gate_compute": gate_compute(
            [
                {"check": "mf4.adcp_scorer", "neurons": 80, "mean_rate_hz": 50.0, "window_ms": 36.0},
                {"check": "mf4.vol_scorer", "neurons": 40, "mean_rate_hz": 62.5, "window_ms": 32.0},
            ]
        ),
        "meta": meta_common(
            id="nelb-r41-126",
            clock_domain="mf4-adcp-sim-relative-ms-t0-2026-08-19T04:00:00Z",
            tags=["adcp-ice-jam", "ACCEPT", "REJECT", "serialized-reconstruction", "operational-t2"],
        ),
    }
