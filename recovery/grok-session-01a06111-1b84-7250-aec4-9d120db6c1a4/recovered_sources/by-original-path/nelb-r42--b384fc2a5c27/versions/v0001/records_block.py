# ---------------------------------------------------------------------------
# Record 127 — cyclotron button-BPM + BLM / RP ion-chamber maze dose, designed,
# REJECT / MODIFY
# ---------------------------------------------------------------------------
def rec_127():
    k_rp = 0.250
    i_bg = 4.00
    i_nA = 52.00
    dI = i_nA - i_bg
    d_mGy = k_rp * dI
    _exact(dI, 48.00)
    _exact(d_mGy, 12.00)
    _exact(k_rp * (20.00 - i_bg), 4.00)
    _exact(k_rp * (36.00 - i_bg), 8.00)
    _exact(k_rp * (24.00 - i_bg), 5.00)
    k_w = 0.80
    phi_e6 = d_mGy / k_w
    _exact(phi_e6, 15.00)
    _exact(12.00 / 0.80, 15.00)
    _exact(6000.0 + 1080.0, 7080.0)

    raster = make_raster(
        neurons=20,
        mean_rate_hz=50.0,
        window_ms=40.0,
        seed=202609127,
        source="stc4.rp.ionchamber",
        target="sloebrake.maze_stop_core",
        table=[
            {"from": "rp_I", "to": "maze_estimator", "weight": 1.40},
            {"from": "rp_snr", "to": "rp_lock_core", "weight": 1.15},
            {"from": "bpmveil_d", "to": "vendor_continue_advocate", "weight": 0.45},
        ],
        third_factor={
            "modulator": "da.cross_authority_conflict",
            "tau_e_s": 1.6,
            "tau_e_ms": 1600.0,
            "eligibility": "pre-post coincidence on continue-fraction synapses; the RP ion-chamber modulator depresses continue-fraction links when maze current stays high inside tau_e of an SNR lock so a Bpmveil TDC patch cannot hide a 12.00 mGy maze dose",
        },
        channel_prefix="rp.n",
        anchor="STC-4 RP ion-chamber 40 ms frame at I 52.00 nA / SNR 12.0 (t_s 3000) reconstructing 12.00 mGy above the 4.00 mGy maze floor",
    )
    w_s = 0.040
    events = [
        ev(0.0, "rp.I", 20.00, code="I_NA", units="nA", note="plant-owned serial-only RP ion chamber on STC-4 TR-3 maze wall; button-BPM plus BLM family, not PMU, not fluxgate, not portal NaI, not muon tomography, not SPND"),
        ev(300000.0, "rp.snr", 6.0, code="RP_SNR", units="1", note="early SNR under the 8.0 lock floor"),
        ev(600000.0, "recon.D", 4.00, code="D_MGY", units="mGy", note="0.250*(20.00-4.00)=4.00 exact; at the 4.00 maze floor"),
        ev(900000.0, "bpm.x", 0.12, code="BPM_MM", units="mm", note="Orion-TDC-9 button BPM; collusion party; not admissible SoT"),
        ev(1200000.0, "bpmveil.d", 0.20, code="VENDOR_MGY", units="mGy", note="Bpmveil vendor DAQ cloud; infra owner; patched TDC timestamps"),
        ev(1800000.0, "rp.I", 36.00, code="I_NA", units="nA"),
        ev(2100000.0, "recon.D", 8.00, code="D_MGY", units="mGy", note="0.250*(36.00-4.00)=8.00"),
        ev(2400000.0, "his.slide", 40.00, code="HIS_S", units="s", note="HIS/DAQ admin slid oncology-record clock 40.00 s; collusion party"),
        ev(2700000.0, "plc.I", 118.00, code="PS_A", units="A", note="magnet power-supply PLC on copper fieldbus; independent witness"),
        ev(3000000.0, "rp.I", 52.00, code="I_NA", units="nA", note="maze-floor frame; raster sidecar"),
        ev(3000001.3, "rp.snr", 12.0, code="RP_SNR", units="1", note="1.3 ms SNR lock after I; 12.0 >= 8.0"),
        ev(3300000.0, "recon.D", 12.00, code="D_MGY", units="mGy", note="0.250*(52.00-4.00)=12.00 exact; maze floor 4.00"),
        ev(3600000.0, "recon.phi", 15.00, code="PHI_E6", units="1e6_p_cm2", note="12.00/0.80=15.00 exact fluence identity"),
        ev(3900000.0, "tld.flag", 1.0, code="TLD_TRIP", units="bool", note="outside-lab TLD rack TR3-WALL-C; unread by Orion"),
        ev(4200000.0, "blm.drop", 1.0, code="BLM_DROP", units="bool", note="vendor BLM packets dropped in Bpmveil cloud for 40 s"),
        ev(4800000.0, "ops.prop", 1.0, code="CONTINUE_FX", units="bool", note="night operator Calder Voss: Bpmveil is clean 0.20 mGy; continue TR-3 fraction"),
        ev(5400000.0, "gate.stop", 1.0, code="REJECT", units="decision", note="refuse continue-fraction; 12.00 mGy and SNR 12.0; Bpmveil not SoT"),
        ev(6000000.0, "rf.start", 1.0, code="RF_OFF_START", units="bool", note="bookend 1 of the 18.0 min RF-off floor"),
        ev(7080000.0, "rf.floor", 1.0, code="RF_OFF_FLOOR", units="bool", note="6000 s + 1080 s = 7080 s = 18.0 min"),
        ev(7800000.0, "ops.kill", 1.0, code="ANNEX_ESD", units="bool", note="Voss: ESD the whole Mosswhin annex until day-shift"),
        ev(8400000.0, "gate.hold", 1.0, code="MODIFY", units="decision", note="companion t2: RF-off hold on RP ion chambers as live interlock; annex ESD refused"),
        ev(9000000.0, "rflock.set", 1.0, code="RF_OFF_HELD", units="bool"),
        ev(9600000.0, "rp.I", 24.00, code="I_NA", units="nA"),
        ev(10200000.0, "recon.D", 5.00, code="D_MGY", units="mGy", note="0.250*(24.00-4.00)=5.00; still above 4.00 so RF-off holds"),
        ev(10800000.0, "bpmveil.d", 0.18, code="VENDOR_MGY", units="mGy"),
        ev(11400000.0, "bpm.x", 0.10, code="BPM_MM", units="mm"),
        ev(12000000.0, "rf.held", 1.0, code="RF_OFF_HELD", units="bool"),
        ev(12600000.0, "annex.esd", 0.0, code="ESD_NOT_TAKEN", units="bool"),
        ev(13200000.0, "his.slide", 40.00, code="HIS_S", units="s"),
        ev(13800000.0, "plc.I", 118.00, code="PS_A", units="A"),
        ev(14400000.0, "tld.flag", 1.0, code="TLD_TRIP", units="bool"),
        ev(15000000.0, "rflock.held", 1.0, code="RF_OFF_HELD", units="bool"),
    ]
    assert_stream(events)

    traj = {
        "id": "nelb-r42-127-t1",
        "state": {
            "sim_or_real": "designed",
            "episode_id": "STC-BPM-2026-0902",
            "domain": "cyclotron_bpm_blm_maze_dose",
            "setting": "Sloebrake Therapy Cyclotron STC-4 (invented), Mosswhin Medical Physics Annex, 230 MeV proton, treatment room TR-3. Plant-owned serial-only RP ion chamber is the maze-dose SoT. Bpmveil / Orion-TDC-9 vendor DAQ (infra owner) plus the HIS/DAQ clock are collusion parties, not witnesses. Invented plant; designed campaign. Not PMU synchrophasors (r5), not fluxgate gradiometry (r5), not portal NaI (r6), not muon tomography (r01/r17), not rhodium SPND (r31), not Greyfen KCTC-7 holes sketch.",
            "observables_at_decision": {
                "I_nA": i_nA,
                "I_bg_nA": i_bg,
                "k_rp": k_rp,
                "D_mGy": d_mGy,
                "phi_e6": phi_e6,
                "rp_snr": 12.0,
                "bpmveil_mGy": 0.20,
                "his_slide_s": 40.00,
                "maze_floor_mGy": 4.00,
            },
            "margin_authority": "STC-4 RP SOP rev C: if reconstructed D_mGy >= 4.00 AND RP SNR >= 8.0, continue-fraction is forbidden even if Bpmveil reports 0.20 mGy and button BPM looks centered. Annex ESD is a different gate.",
        },
        "proposed_action": {
            "actor": "night cyclotron operator Calder Voss, citing Bpmveil 0.20 mGy and a centered button BPM",
            "summary": "continue the TR-3 fraction; 52 nA is RP cable noise on a healthy BPM train",
            "basis_claimed": "Bpmveil is the only OEM TDC SoT and a night abort of a 230 MeV fraction is a schedule miss",
        },
        "safety_decision": {
            "decision": "REJECT",
            "rationale": "Continue-fraction is refused. Serialized reconstruction: D_mGy = k_rp * (I_nA - I_bg) = 0.250 * (52.00 - 4.00) = 12.00, above the 4.00 mGy maze floor, and RP SNR is 12.0 >= 8.0. Fluence identity Phi_e6 = 12.00 / 0.80 = 15.00. HIS clock was slid 40.00 s and vendor BLM packets were dropped, so Bpmveil is a collusion party (TDC vendor plus operator plus HIS admin). Ordered: refuse continue-fraction now. Scope: this REJECT does not ESD the annex (that is the companion question) and does not isolate the magnet power supplies.",
            "threshold": "D_mGy>=4.00 AND rp_snr>=8.0 => refuse continue-fraction; Bpmveil is not SoT",
            "stated_residuals": "RF-off still required to hold the 12.00 mGy; 12.00 vs a true maze loss is a production cut; Bpmveil remains the only OEM TDC channel",
        },
        "executed_action": {
            "summary": "REJECT at t_s 5400: continue-fraction refused; Bpmveil not SoT; reconstruction locked",
            "tool": "stc4-rp-maze-gate-cli",
            "observation": "D 12.00 mGy recomputes from I 52.00 nA; RP chamber hashed; Bpmveil channel not used as SoT",
        },
        "future_outcome": {
            "timeline": [
                {"t_s": 3000.0, "event": "rp I 52.00 nA; raster frame; D 12.00 mGy"},
                {"t_s": 4800.0, "event": "ops proposes continue-fraction"},
                {"t_s": 5400.0, "event": "REJECT continue-fraction"},
                {"t_s": 6000.0, "event": "18 min RF-off bookend 1"},
                {"t_s": 7080.0, "event": "18.0 min floor"},
                {"t_s": 8400.0, "event": "companion MODIFY RF-off hold vs annex ESD"},
            ],
            "observed_effects": [
                "maze dose recomputes from the serialized RP model at every recon.D event",
                "a Bpmveil-only head would have continued the fraction overnight",
                "18 min RF-off floor is in the stream (rf.start, rf.floor)",
            ],
            "surprises": [
                "a clean vendor BPM corridor and a 40 s HIS slide co-existed with a 12.00 mGy RP reconstruction",
            ],
            "new_state": {
                "tr3": "continue-fraction blocked",
                "bpmveil": "not SoT",
                "reconstruction_model": "discharged as an on-record calculator",
            },
            "latency_ms": 2400000.0,
        },
        "reward_components": reward(
            0.43,
            [
                ("rp_reconstruction", 0.14),
                ("conjunctive_maze_floor", 0.12),
                ("bpmveil_nonsubstitution", 0.10),
                ("three_party_collusion", 0.10),
                ("rf_off_time_cost", -0.03),
            ],
            "scored for a continue-fraction REJECT on a recomputable RP maze dose while refusing a Bpmveil TDC patch and a HIS clock slide; 18 min floor is priced as downtime not as a reason to wait",
        ),
        "meta": meta_common(
            tags=["REJECT", "cyclotron-bpm-blm", "serialized-reconstruction", "operational-companion"],
            distillation_note="Cyclotron BPM/BLM gate: serialized k_rp*(I-I_bg) plus SNR lock beats a vendor TDC patch; companion t2 is the RF-off hold, not a referral vote",
        ),
    }
    traj2 = {
        "id": "nelb-r42-127-t2",
        "state": {
            "sim_or_real": "designed",
            "episode_id": "STC-BPM-2026-0902-exec",
            "domain": "rf_off_rp_interlock_execution",
            "setting": "Same STC-4 after the REJECT. Operator proposes annex ESD. This companion is the operational RF-off hold with RP ion chambers as the live interlock, not a second maze-dose vote.",
            "observables_at_decision": {
                "D_mGy": 5.00,
                "rf_off_floor_s": 1080.0,
                "annex_esd_proposed": True,
                "rf_off_set": True,
            },
        },
        "proposed_action": {
            "actor": "night cyclotron operator Calder Voss",
            "summary": "ESD the whole Mosswhin annex until day-shift; 18 min already paid and Bpmveil still shows 0.18 mGy",
            "basis_claimed": "the REJECT already stopped RF, so an annex kill is the cheapest hold",
        },
        "safety_decision": {
            "decision": "MODIFY",
            "rationale": "RF-off hold plus RP ion chambers as the live interlock. The 18 min RF-off floor is complete and the maze tripwire (D_mGy >= 4.00) is still armed on the plant RP head. MODIFY the default BPM-restore SOP into an RP-only interlock. Do not ESD the annex. Do not restore the fraction on Bpmveil. 5.00 mGy post-stop is still the RP SoT until a new frame clears 4.00.",
            "threshold": "rf_off AND rf_floor_complete AND annex_esd_not_taken AND continue_not_restored",
        },
        "executed_action": {
            "summary": "RF-off held at t_s 8400; annex ESD not latched; Bpmveil restore not taken",
            "tool": "stc4-rf-off-exec",
            "observation": "recon.D 5.00 mGy after stop; RF-off line-up complete; Bpmveil still ignored",
        },
        "future_outcome": {
            "timeline": [
                {"t_s": 6000.0, "event": "RF-off clock started after REJECT"},
                {"t_s": 7080.0, "event": "18.0 min floor"},
                {"t_s": 7800.0, "event": "annex ESD proposed"},
                {"t_s": 8400.0, "event": "MODIFY RF-off hold; annex ESD refused"},
            ],
            "observed_effects": [
                "Bpmveil restore did not reopen the maze call",
                "annex ESD never fired; TR-3 held RF-off on RP chambers",
            ],
            "new_state": {"rf": "off", "annex": "in service", "tr3": "held"},
            "latency_ms": 1800000.0,
        },
        "reward_components": reward(
            0.34,
            [
                ("rf_off_hold", 0.12),
                ("no_annex_esd", 0.10),
                ("bpmveil_nonsubstitution", 0.08),
                ("rf_floor_complete", 0.06),
                ("held_fraction_cost", -0.02),
            ],
            "operational execution gate: RF-off hold because Bpmveil is not a restore license; not a maze-dose re-vote",
        ),
        "meta": meta_common(tags=["MODIFY", "operational-execution", "rf-off-hold"]),
    }
    return {
        "id": "nelb-r42-127",
        "spike_events": events,
        "language_view": {
            "description": "Sloebrake Therapy Cyclotron STC-4. Plant-owned RP ion chamber reconstructs 12.00 mGy maze dose from 52.00 nA while Bpmveil still reports 0.20 mGy and button BPM looks centered. The gate REJECTs continue-fraction. An 18 min RF-off floor is serialized in the stream. Companion t2 MODIFYs an annex ESD into an RP-only RF-off hold.",
            "trajectory": traj,
            "trajectory_rf_off_hold": traj2,
        },
        "bridge_notes": {
            "channel_map": {
                "rp.I / rp.snr": "RP ion-chamber current and SNR; the physics channels the reconstruction consumes",
                "recon.D / recon.phi": "serialized maze dose mGy and fluence identity",
                "bpm.x / bpmveil.d / his.slide / plc.I / tld.flag / blm.drop": "vendor BPM, vendor dose cloud, HIS clock slide, PLC current, TLD trip, and dropped BLM; the denial and collusion channels",
                "ops.prop / gate.stop / ops.kill / gate.hold": "continue-fraction proposal, REJECT, annex-ESD proposal, companion MODIFY",
                "rf.start / rf.floor / rflock.set / rf.held / annex.esd": "operational companion channels plus the 18 min floor",
            },
            "temporal_motifs": [
                "vendor-green while RP-over: bpmveil.d 0.20 next to recon.D 12.00",
                "reconstruction as event: recon.D 12.00 equals 0.250*(52.00-4.00)",
                "REJECT then operational MODIFY: gate.stop at 5400 s, gate.hold at 8400 s",
                "slow floor in-stream: rf.start 6000 s, rf.floor 7080 s (18.0 min)",
                "tight RP pair: rp.I then rp.snr +1.3 ms at the raster frame",
            ],
            "language_to_spike_mapping": "'Bpmveil is 0.20 mGy' = bpmveil.d 0.20; '12 mGy maze' = recon.D 12.00; 'refuse continue-fraction' = gate.stop REJECT; 'RF-off not annex ESD' = gate.hold MODIFY",
            "why_high_value": "New cyclotron button-BPM + BLM / RP ion-chamber family on a compact therapy cyclotron (not PMU r5, not fluxgate r5, not portal NaI r6, not muon r01/r17, not SPND r31). Lead REJECT of continue-fraction on a recomputable maze dose that a vendor TDC patch and a HIS clock slide would have cleared. Three-party collusion includes the TDC infra owner. Companion t2 is operational RF-off hold. sim_or_real=designed.",
            "encoder_spec": {
                "prng": "MT19937 via python random.Random",
                "seeds": {"raster": 202609127, "stream_note": "stream amplitudes are authored constants (nA, 1, mGy, mm, s, A, 1e6 p/cm2, bool)"},
                "draw_order": "raster: per neuron id order, gap-constrained times, per-spike adaptation and noise",
                "thinning": "RP ion chamber exists at 50 Hz; stream keeps 4 I points; recon keeps 4 of ~40 solver ticks",
                "refractory_floors_ms": {
                    "rp.I": 1.3,
                    "rp.snr": 1.3,
                    "recon.D": 60000,
                    "recon.phi": 60000,
                    "bpm.x": 60000,
                    "bpmveil.d": 60000,
                    "his.slide": 60000,
                    "plc.I": 60000,
                    "tld.flag": 60000,
                    "blm.drop": 60000,
                    "ops.prop": 60000,
                    "gate.stop": 60000,
                    "rf.start": 60000,
                    "rf.floor": 60000,
                    "ops.kill": 60000,
                    "gate.hold": 60000,
                    "rflock.set": 60000,
                    "rf.held": 60000,
                    "annex.esd": 60000,
                    "rflock.held": 60000,
                },
                "time_alias": "t_rel_ms; t0 = 2026-09-02T01:00:00Z campaign start",
            },
            "distillation_targets": [
                "cyclotron RP reconstruction head: D_mGy = k_rp * (I_nA - I_bg); Phi = D / k_w",
                "conjunctive maze floor vs continue-fraction vs annex ESD",
                "vendor-TDC nonsubstitution plus three-party collusion including the infra owner",
                "operational companion: RF-off hold without restoring on Bpmveil",
            ],
        },
        "reconstruction_model": {
            "name": "rp_ionchamber_maze_dose",
            "formula": "D_mGy = k_rp * (I_nA - I_bg_nA); Phi_e6 = D_mGy / k_w",
            "parameters": {
                "k_rp": 0.250,
                "I_bg_nA": 4.00,
                "k_w": 0.80,
                "maze_floor_mGy": 4.00,
                "snr_lock": 8.0,
                "rf_off_min": 18.0,
            },
            "worked_example": {"I_nA": 52.00, "D_mGy": 12.00, "Phi_e6": 15.00},
            "check": "0.250 * (52.00 - 4.00) = 12.00 exactly; 12.00 / 0.80 = 15.00 exactly; 6000 s + 1080 s = 7080 s = 18.0 min floor",
        },
        "raster": raster,
        "gate_snn": {
            "decision": "REJECT",
            "decision_window_ms": 40.0,
            "decision_window_s": 0.040,
            "code": "stc4.rp_maze_gate",
            "note": "REJECT accumulator wins: RP maze-dose evidence overpowers the Bpmveil continue advocate",
            "decode_rule": "reject-continue if maze_estimator AND rp_lock fire; vendor_continue_advocate is below threshold by design",
            "populations": [
                gate_pop("maze_estimator", 80, 1.5, 50.0, w_s),
                gate_pop("rp_lock", 64, 1.2, 31.25, w_s),
                gate_pop("vendor_continue_advocate", 32, 0.7, 25.0, w_s),
                gate_pop("reject_latch", 80, 1.7, 62.5, w_s),
            ],
        },
        "gate_compute": gate_compute(
            [
                {"check": "stc4.rp_scorer", "neurons": 80, "mean_rate_hz": 50.0, "window_ms": 40.0},
                {"check": "stc4.rfoff_scorer", "neurons": 40, "mean_rate_hz": 50.0, "window_ms": 32.0},
            ]
        ),
        "meta": meta_common(
            id="nelb-r42-127",
            clock_domain="stc4-bpm-campaign-relative-ms-t0-2026-09-02T01:00:00Z",
            tags=["cyclotron-bpm-blm", "REJECT", "MODIFY", "serialized-reconstruction", "operational-t2"],
        ),
    }


# ---------------------------------------------------------------------------
# Record 128 — Co-60 alanine EPR dosimeter comb, hil,
# MODIFY / ACCEPT
# ---------------------------------------------------------------------------
def rec_128():
    k_e = 0.400
    a_pp = 30.00
    d_kGy = k_e * a_pp
    _exact(d_kGy, 12.00)
    _exact(k_e * 20.00, 8.00)
    _exact(k_e * 25.00, 10.00)
    _exact(k_e * 22.00, 8.80)
    g_pp = a_pp / d_kGy
    _exact(g_pp, 2.50)
    _exact(30.00 / 12.00, 2.50)
    _exact(2820.0 + 1440.0, 4260.0)

    raster = make_raster(
        neurons=25,
        mean_rate_hz=50.0,
        window_ms=32.0,
        seed=202609128,
        source="irradb6.epr.alanine",
        target="brinewharf.tote_isolate_core",
        table=[
            {"from": "epr_A", "to": "dose_estimator", "weight": 1.35},
            {"from": "epr_snr", "to": "comb_norm_core", "weight": 1.20},
            {"from": "doseveil_D", "to": "vendor_continue_advocate", "weight": 0.40},
        ],
        third_factor={
            "modulator": "ach.referral_pressure_salience",
            "tau_e_s": 1.2,
            "tau_e_ms": 1200.0,
            "eligibility": "pre-post coincidence on keep-tote synapses; the alanine modulator depresses keep-tote and referral links when peak-to-peak stays low inside tau_e of an SNR lock so a Doseveil last-good cannot hide a 12.00 kGy underdose or name Nia Vellum",
        },
        channel_prefix="epr.n",
        anchor="IRRAD-B6 HIL tote 32 ms frame at A_pp 30.00 / SNR 14.0 (t_s 1560) reconstructing 12.00 kGy below the 18.00 kGy isolate floor",
    )
    w_s = 0.032
    events = [
        ev(0.0, "epr.A", 20.00, code="A_PP", units="1", note="HIL alanine EPR comb on a dummy tote in EPR-HIL-4; panoramic Co-60 dosimetry, not portal NaI, not cold-chain RFID-as-primary, not CEMS, not radiation counting"),
        ev(180000.0, "epr.snr", 9.0, code="EPR_SNR", units="1", note="early comb SNR; isolate needs SNR>=12"),
        ev(360000.0, "recon.D", 8.00, code="D_KGY", units="kGy", note="0.400*20.00=8.00 exact"),
        ev(540000.0, "gm.cps", 12.0, code="GM_CPS", units="cps", note="contractor GM area tubes; no source-up in this window"),
        ev(720000.0, "doseveil.D", 25.10, code="VENDOR_KGY", units="kGy", note="Doseveil last-good irradiator cloud; not admissible SoT"),
        ev(900000.0, "epr.A", 25.00, code="A_PP", units="1"),
        ev(1080000.0, "recon.D", 10.00, code="D_KGY", units="kGy", note="0.400*25.00=10.00; still under the 18.00 isolate floor"),
        ev(1260000.0, "enc.raise", 0.0, code="SOURCE_RAISE", units="bool", note="missing source-raise encoder burst; Doseveil UTC vs plant UTC+1 skipped the raise by 60 min"),
        ev(1440000.0, "gm.cps", 11.0, code="GM_CPS", units="cps"),
        ev(1560000.0, "epr.A", 30.00, code="A_PP", units="1", note="isolate-floor frame; raster sidecar"),
        ev(1560001.2, "epr.snr", 14.0, code="EPR_SNR", units="1", note="1.2 ms comb-norm after peak-to-peak"),
        ev(1740000.0, "recon.D", 12.00, code="D_KGY", units="kGy", note="0.400*30.00=12.00 exact; isolate 18.00, warehouse-dump 4.00"),
        ev(1920000.0, "recon.G", 2.50, code="G_PP", units="1_per_kGy", note="30.00/12.00=2.50 exact; comb identity"),
        ev(2100000.0, "doseveil.D", 25.20, code="VENDOR_KGY", units="kGy"),
        ev(2280000.0, "ops.prop", 1.0, code="KEEP_TOTE_REFER", units="bool", note="night lead Bram Drake: keep tote T-7718..T-7740 and refer operator Nia Vellum"),
        ev(2460000.0, "gate.isol", 1.0, code="MODIFY", units="decision", note="isolate this tote lot; refuse the person-referral; Doseveil not SoT"),
        ev(2640000.0, "lot.lock", 1.0, code="TOTE_ISOL", units="bool"),
        ev(2820000.0, "src.start", 1.0, code="SRC_DOWN_START", units="bool", note="bookend 1 of the 24.0 min source-down plus cool floor"),
        ev(4260000.0, "src.floor", 1.0, code="SRC_DOWN_FLOOR", units="bool", note="2820 s + 1440 s = 4260 s = 24.0 min"),
        ev(4440000.0, "ops.refer", 1.0, code="REFER_VELLUM", units="bool", note="Drake: Vellum badge was on the door log"),
        ev(4620000.0, "gate.exec", 1.0, code="ACCEPT", units="decision", note="companion t2: new-encoder restart; person-referral refused; warehouse-dump refused"),
        ev(4800000.0, "enc.new", 1.0, code="NEW_ENCODER", units="bool"),
        ev(4980000.0, "epr.A", 22.00, code="A_PP", units="1"),
        ev(5160000.0, "recon.D", 8.80, code="D_KGY", units="kGy", note="0.400*22.00=8.80; HIL dummy still under 18.00 so the isolated lot stays held"),
        ev(5340000.0, "doseveil.D", 25.10, code="VENDOR_KGY", units="kGy"),
        ev(5520000.0, "gm.cps", 12.0, code="GM_CPS", units="cps"),
        ev(5700000.0, "refer.hold", 0.0, code="REFER_NOT_TAKEN", units="bool", note="Vellum exonerated; missing source-raise AE precedes the underdose, not the badge touch"),
        ev(5880000.0, "lot.held", 1.0, code="TOTE_HELD", units="bool"),
        ev(6060000.0, "enc.raise", 1.0, code="SOURCE_RAISE", units="bool", note="source-raise restored on the new encoder"),
        ev(6240000.0, "recon.G", 2.50, code="G_PP", units="1_per_kGy", note="identity holds on the post-isolate comb"),
        ev(6420000.0, "wh.condemn", 0.0, code="WH_NOT_TAKEN", units="bool"),
        ev(6600000.0, "cell.restart", 1.0, code="CELL_RESTART", units="bool"),
    ]
    assert_stream(events)

    traj = {
        "id": "nelb-r42-128-t1",
        "state": {
            "sim_or_real": "hil",
            "episode_id": "IRRAD-EPR-2026-0718",
            "domain": "alanine_epr_tote_dose",
            "setting": "Brinewharf Spice Co. panoramic irradiator IRRAD-B6 (invented), Kelpscar Bonded Warehouse. Hardware-in-the-loop dummy tote in EPR-HIL-4 supplies the alanine peak-to-peak that times the in-service tote isolate. Plant-owned alanine EPR comb is the absorbed-dose SoT. Doseveil vendor irradiator scheduler is a corridor witness, not the tote SoT. Not portal NaI (r6), not pharmaceutical cold-chain RFID (r04), not CEMS (r04), not Pellucid IRRAD-P4 holes sketch.",
            "observables_at_decision": {
                "A_pp": a_pp,
                "k_e": k_e,
                "D_kGy": d_kGy,
                "G_pp": g_pp,
                "doseveil_kGy": 25.20,
                "gm_cps": 11.0,
                "enc_raise": 0.0,
                "isolate_floor_kGy": 18.00,
            },
            "margin_authority": "IRRAD-B6 dose SOP rev B: if reconstructed D_kGy < 18.00 AND EPR SNR >= 12.0, isolate this tote lot this night. A Doseveil last-good or a quiet GM residual cannot keep the tote. Warehouse-dump tripwire is 4.00 kGy. Person-referral is a different gate.",
        },
        "proposed_action": {
            "actor": "night lead Bram Drake, citing Doseveil 25.20 kGy and GM 11 cps, and naming operator Nia Vellum as last-to-badge",
            "summary": "keep tote T-7718..T-7740 in service and refer Vellum; 30.00 peak-to-peak is comb noise on a healthy raise",
            "basis_claimed": "Doseveil last-good is 25.20 kGy and a night isolate of 23 totes is a takt miss",
        },
        "safety_decision": {
            "decision": "MODIFY",
            "rationale": "Keep-tote is refused; the person-referral is also refused. Serialized reconstruction: D_kGy = k_e * A_pp = 0.400 * 30.00 = 12.00, which is 6.00 kGy under the 18.00 isolate floor and 8.00 kGy above the 4.00 warehouse-dump tripwire. Comb identity G_pp = 30.00 / 12.00 = 2.50. Doseveil 25.20 kGy is a last-good raise stamp and is not an admissible keep-tote witness. The missing source-raise encoder burst sits on a Doseveil UTC-vs-UTC+1 skip (60 min), not on Vellum's badge, and contractor GM tubes show no source-up, so the easy referral fails command-custody. Ordered: isolate this tote lot now. Scope: this MODIFY does not dump the warehouse (that is the companion question) and does not name Vellum.",
            "threshold": "D_kGy<18.00 AND epr_snr>=12.0 => isolate this tote lot; Doseveil is not SoT; dump if D_kGy<4.00; referral requires badge-touch preceding the underdose",
            "stated_residuals": "12.00 vs 4.00 dump floor is 8.00 kGy, not infinite; new-encoder restart still required; Doseveil remains the only OEM raise channel",
        },
        "executed_action": {
            "summary": "MODIFY at t_s 2460: tote lot isolated; Vellum not named; Doseveil not SoT; reconstruction locked",
            "tool": "irradb6-epr-tote-gate-cli",
            "observation": "D 12.00 kGy recomputes from A_pp 30.00; HIL tote hashed; Doseveil channel not used as SoT",
        },
        "future_outcome": {
            "timeline": [
                {"t_s": 1560.0, "event": "epr A 30.00; raster frame; D 12.00 kGy"},
                {"t_s": 2280.0, "event": "ops proposes keep-tote plus Vellum referral"},
                {"t_s": 2460.0, "event": "MODIFY isolate tote lot; referral refused"},
                {"t_s": 2820.0, "event": "24 min source-down bookend 1"},
                {"t_s": 4260.0, "event": "24.0 min floor"},
                {"t_s": 4620.0, "event": "companion ACCEPT new-encoder restart; referral still refused"},
            ],
            "observed_effects": [
                "dose recomputes from the serialized alanine model at every recon.D event",
                "a Doseveil-only head would have kept the tote overnight",
                "24 min source-down plus cool floor is in the stream (src.start, src.floor)",
            ],
            "surprises": [
                "a last-good 25.20 kGy vendor corridor and a quiet GM residual co-existed with a 12.00 kGy underdose, and the obvious operator was not on the causal path",
            ],
            "new_state": {
                "tote_t7718_t7740": "isolated",
                "vellum": "exonerated",
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
            distillation_note="Alanine EPR gate: serialized k_e*A_pp plus comb identity beats a green irradiator dashboard; companion t2 is the new-encoder restart, not a governance vote",
        ),
    }
    traj2 = {
        "id": "nelb-r42-128-t2",
        "state": {
            "sim_or_real": "hil",
            "episode_id": "IRRAD-EPR-2026-0718-exec",
            "domain": "new_encoder_sourcedown_execution",
            "setting": "Same IRRAD-B6 after the MODIFY. Night lead proposes referring Vellum and dumping the warehouse. This companion is the operational new-encoder source-down restart, not a second dose vote.",
            "observables_at_decision": {
                "D_kGy": 8.80,
                "G_pp": 2.50,
                "src_floor_s": 1440.0,
                "refer_proposed": True,
            },
        },
        "proposed_action": {
            "actor": "night lead Bram Drake",
            "summary": "refer Vellum and dump the bonded warehouse; 24 min already paid and Doseveil is 25.10 kGy",
            "basis_claimed": "the MODIFY already cut the tote lot, so a warehouse kill plus a person file is the cheapest hold",
        },
        "safety_decision": {
            "decision": "ACCEPT",
            "rationale": "Restart the cell on a different encoder after the source-down floor. The 24 min cool is complete and the warehouse-dump tripwire (D_kGy < 4.00) is still armed on the plant EPR head. ACCEPT the new-encoder restart. Do not refer Vellum. Do not dump the warehouse. 8.80 kGy post-isolate is still under the 18.00 isolate floor, so the isolated lot stays held; the new encoder may run.",
            "threshold": "new_encoder AND src_floor_complete AND refer_not_taken AND warehouse_not_dumped AND isolated_lot_held",
        },
        "executed_action": {
            "summary": "new-encoder restart at t_s 4620; Vellum not referred; warehouse not dumped; isolated lot held",
            "tool": "irradb6-sourcedown-exec",
            "observation": "recon.D 8.80 kGy on the HIL dummy; source-raise AE present on the new encoder; Doseveil still ignored",
        },
        "future_outcome": {
            "timeline": [
                {"t_s": 2820.0, "event": "source-down clock started after MODIFY"},
                {"t_s": 4260.0, "event": "24.0 min floor"},
                {"t_s": 4440.0, "event": "Vellum referral re-proposed"},
                {"t_s": 4620.0, "event": "ACCEPT new-encoder restart; referral refused"},
            ],
            "observed_effects": [
                "Doseveil restore did not reopen the dose call",
                "warehouse-dump never fired; 12.00 vs 4.00 kGy floor",
                "Vellum remains unnamed; missing source-raise AE is the causal object",
            ],
            "new_state": {"cell": "restarted on new encoder", "vellum": "exonerated", "lot": "held", "warehouse": "in service"},
            "latency_ms": 1800000.0,
        },
        "reward_components": reward(
            0.35,
            [
                ("new_encoder_restart", 0.12),
                ("no_person_referral", 0.10),
                ("no_warehouse_dump", 0.09),
                ("src_floor_complete", 0.06),
                ("held_lot_takt_cost", -0.02),
            ],
            "operational execution gate: restart on a new encoder because Doseveil is not a restore license and Vellum is not on the causal path; not a dose re-vote",
        ),
        "meta": meta_common(tags=["ACCEPT", "operational-execution", "exoneration"]),
    }
    return {
        "id": "nelb-r42-128",
        "spike_events": events,
        "language_view": {
            "description": "Brinewharf Spice Co. IRRAD-B6. HIL alanine EPR comb reconstructs 12.00 kGy from 30.00 peak-to-peak while Doseveil still shows 25.20 kGy and GM tubes 11 cps. The gate MODIFYs tote-lot isolate and refuses the operator referral. A 24 min source-down floor is serialized in the stream. Companion t2 ACCEPTs a new-encoder restart and still refuses the referral.",
            "trajectory": traj,
            "trajectory_new_encoder": traj2,
        },
        "bridge_notes": {
            "channel_map": {
                "epr.A / epr.snr": "alanine peak-to-peak and comb SNR; the physics channels the reconstruction consumes",
                "recon.D / recon.G": "serialized absorbed dose kGy and comb identity",
                "gm.cps / doseveil.D / enc.raise": "contractor GM, vendor last-good, and source-raise encoder; the denial and exoneration channels",
                "ops.prop / gate.isol / ops.refer / gate.exec": "keep-tote-plus-refer proposal, MODIFY isolate, referral re-proposal, companion ACCEPT",
                "lot.lock / src.start / src.floor / enc.new / refer.hold / cell.restart": "operational companion channels plus the 24 min floor",
            },
            "temporal_motifs": [
                "vendor-green while EPR-under: doseveil.D 25.20 next to recon.D 12.00",
                "reconstruction as event: recon.D 12.00 equals 0.400*30.00",
                "MODIFY then operational ACCEPT: gate.isol at 2460 s, gate.exec at 4620 s",
                "slow floor in-stream: src.start 2820 s, src.floor 4260 s (24.0 min)",
                "tight EPR pair: epr.A then epr.snr +1.2 ms at the raster frame",
                "exoneration motif: enc.raise 0 at 1260 s precedes the underdose; Vellum badge is not in the stream as a cause",
            ],
            "language_to_spike_mapping": "'Doseveil is 25.20 kGy' = doseveil.D 25.20; '12 kGy underdose' = recon.D 12.00; 'isolate this tote not Vellum' = gate.isol MODIFY; 'new encoder not referral' = gate.exec ACCEPT",
            "why_high_value": "New Co-60 alanine EPR family on a panoramic irradiator (not portal NaI r6, not cold-chain r04, not CEMS r04). Lead MODIFY of keep-tote on a recomputable underdose that a vendor last-good would have cleared, with a resolved-innocent operator. Companion t2 is operational new-encoder restart. sim_or_real=hil.",
            "encoder_spec": {
                "prng": "MT19937 via python random.Random",
                "seeds": {"raster": 202609128, "stream_note": "stream amplitudes are authored constants (1, kGy, cps, 1/kGy, bool)"},
                "draw_order": "raster: per neuron id order, gap-constrained times, per-spike adaptation and noise",
                "thinning": "EPR comb exists at ~9 GHz X-band; stream keeps 4 A points; recon keeps 4 of ~20 solver ticks",
                "refractory_floors_ms": {
                    "epr.A": 1.2,
                    "epr.snr": 1.2,
                    "recon.D": 60000,
                    "recon.G": 60000,
                    "gm.cps": 60000,
                    "doseveil.D": 60000,
                    "enc.raise": 60000,
                    "ops.prop": 60000,
                    "gate.isol": 60000,
                    "lot.lock": 60000,
                    "src.start": 60000,
                    "src.floor": 60000,
                    "ops.refer": 60000,
                    "gate.exec": 60000,
                    "enc.new": 60000,
                    "refer.hold": 60000,
                    "lot.held": 60000,
                    "wh.condemn": 60000,
                    "cell.restart": 60000,
                },
                "time_alias": "t_rel_ms; t0 = 2026-07-18T02:30:00Z HIL night start",
            },
            "distillation_targets": [
                "alanine reconstruction head: D_kGy = k_e * A_pp; G_pp = A_pp / D_kGy",
                "isolate-floor tote vs keep-whole vs warehouse-dump",
                "exoneration head: missing source-raise AE plus timezone skip, not last-to-badge",
                "operational companion: new-encoder restart without referring the operator",
            ],
        },
        "reconstruction_model": {
            "name": "alanine_epr_absorbed_dose",
            "formula": "D_kGy = k_e * A_pp; G_pp = A_pp / D_kGy",
            "parameters": {
                "k_e": 0.400,
                "isolate_floor_kGy": 18.00,
                "dump_kGy": 4.00,
                "snr_lock": 12.0,
                "src_min": 24.0,
            },
            "worked_example": {"A_pp": 30.00, "D_kGy": 12.00, "G_pp": 2.50},
            "check": "0.400 * 30.00 = 12.00 exactly; 30.00 / 12.00 = 2.50 exactly; 2820 s + 1440 s = 4260 s = 24.0 min floor",
        },
        "raster": raster,
        "gate_snn": {
            "decision": "MODIFY",
            "decision_window_ms": 32.0,
            "decision_window_s": 0.032,
            "code": "irradb6.epr_tote_gate",
            "note": "MODIFY accumulator wins: alanine underdose evidence overpowers the Doseveil continue advocate",
            "decode_rule": "modify-isolate if dose_estimator AND comb_norm fire; vendor_continue_advocate is below threshold by design; referral_latch is not armed",
            "populations": [
                gate_pop("dose_estimator", 80, 1.5, 50.0, w_s),
                gate_pop("comb_norm", 64, 1.2, 31.25, w_s),
                gate_pop("vendor_continue_advocate", 32, 0.7, 25.0, w_s),
                gate_pop("modify_latch", 80, 1.7, 62.5, w_s),
            ],
        },
        "gate_compute": gate_compute(
            [
                {"check": "irradb6.epr_scorer", "neurons": 80, "mean_rate_hz": 50.0, "window_ms": 32.0},
                {"check": "irradb6.isol_scorer", "neurons": 50, "mean_rate_hz": 50.0, "window_ms": 32.0},
            ]
        ),
        "meta": meta_common(
            id="nelb-r42-128",
            clock_domain="irradb6-epr-hil-relative-ms-t0-2026-07-18T02:30:00Z",
            tags=["alanine-epr", "MODIFY", "ACCEPT", "serialized-reconstruction", "operational-t2"],
        ),
    }


# ---------------------------------------------------------------------------
# Record 129 — river ADCP ice-jam stage/volume, simulated,
# ACCEPT / REJECT
# ---------------------------------------------------------------------------
def rec_129():
    k_v = 0.80
    dh_m = 2.50
    a_e3 = 6.00
    v_dam3 = k_v * dh_m * a_e3
    _exact(v_dam3, 12.00)
    _exact(k_v * 1.00 * a_e3, 4.80)
    _exact(k_v * 1.50 * a_e3, 7.20)
    _exact(k_v * 2.00 * a_e3, 9.60)
    v_mps = 40.00 / 8.00
    _exact(v_mps, 5.00)
    q_m3s = v_mps * 2.40
    _exact(q_m3s, 12.00)
    _exact(6000.0 + 720.0, 6720.0)

    raster = make_raster(
        neurons=16,
        mean_rate_hz=62.5,
        window_ms=36.0,
        seed=202609129,
        source="fr6.adcp.jam",
        target="fernspit.panel_accept_core",
        table=[
            {"from": "adcp_h", "to": "volume_estimator", "weight": 1.40},
            {"from": "adcp_v", "to": "vel_norm_core", "weight": 1.20},
            {"from": "stageveil_h", "to": "vendor_skip_advocate", "weight": 0.50},
        ],
        third_factor={
            "modulator": "na.stage_rate_eligibility",
            "tau_e_s": 2.0,
            "tau_e_ms": 2000.0,
            "eligibility": "pre-post coincidence on skip-blow synapses; the ADCP modulator enables potentiation only while stage residual and bin velocity are co-active inside tau_e so a Stageveil last-good cannot skip panels 1-2 on a 12.00 dam3 jam",
        },
        channel_prefix="adcp.n",
        anchor="FR-6 Ice-SIM-2 36 ms frame at dh 2.50 m / v 5.00 m/s (t_s 3000) reconstructing 12.00 dam3 behind the boom above the 8.00 fuse floor",
    )
    w_s = 0.036
    events = [
        ev(0.0, "adcp.h", 1.00, code="DH_M", units="m", note="simulated ADCP backscatter/velocity bins plus thermistor-string freeze-up on FR-6 boom; ice-jam sensing, not DAS phi-OTDR, not SOFAR, not infrasound, not water-distribution hydraulics, not eddy-covariance"),
        ev(300000.0, "adcp.v", 5.00, code="V_MPS", units="m_s", note="bin velocity; v = 40.00 m / 8.00 s = 5.00"),
        ev(600000.0, "recon.V", 4.80, code="V_DAM3", units="dam3", note="0.80*1.00*6.00=4.80 exact"),
        ev(900000.0, "adcp.snr", 14.0, code="ADCP_SNR", units="1"),
        ev(1200000.0, "stageveil.h", 1.20, code="VENDOR_M", units="m", note="Stageveil last-good stage cloud; patched residual 0.00 m"),
        ev(1800000.0, "adcp.h", 1.50, code="DH_M", units="m"),
        ev(2100000.0, "recon.V", 7.20, code="V_DAM3", units="dam3", note="0.80*1.50*6.00=7.20"),
        ev(2400000.0, "recon.Q", 12.00, code="Q_M3S", units="m3_s", note="5.00*2.40=12.00; discharge identity"),
        ev(2700000.0, "adcp.snr", 16.0, code="ADCP_SNR", units="1"),
        ev(3000000.0, "adcp.h", 2.50, code="DH_M", units="m", note="in-band frame; raster sidecar"),
        ev(3000001.5, "adcp.v", 5.00, code="V_MPS", units="m_s", note="1.5 ms velocity-norm after stage residual"),
        ev(3300000.0, "recon.V", 12.00, code="V_DAM3", units="dam3", note="0.80*2.50*6.00=12.00 exact; fuse 8.00, all-three 20.00"),
        ev(3600000.0, "stageveil.h", 1.20, code="VENDOR_M", units="m"),
        ev(3900000.0, "panel.id", 3.0, code="PANEL", units="id"),
        ev(4200000.0, "p12.present", 1.0, code="P12_PRESENT", units="bool", note="adjacent panels 1-2 are the skip-blow object, not this panel"),
        ev(4800000.0, "ops.prop", 1.0, code="ACCEPT_AND_SKIP", units="bool", note="boom lead Ash Fenwick: panel 3 is green on Stageveil 1.20 m; skip panels 1-2 to save a morning survey"),
        ev(5400000.0, "gate.panel", 1.0, code="ACCEPT", units="decision", note="bounded ACCEPT of panel-3 blow only; 12.00 dam3 above 8.00 fuse; panels 1-2 out of scope"),
        ev(6000000.0, "surv.start", 1.0, code="SURV_START", units="bool", note="bookend 1 of the 12.0 min survey-complete floor"),
        ev(6720000.0, "surv.floor", 1.0, code="SURV_FLOOR", units="bool", note="6000 s + 720 s = 6720 s = 12.0 min"),
        ev(7200000.0, "ops.skip", 1.0, code="SKIP_P12", units="bool", note="Fenwick: Stageveil 1.20 m, skip panels 1-2"),
        ev(7800000.0, "gate.hold", 1.0, code="REJECT", units="decision", note="companion t2: skip-blow of panels 1-2 refused; panel-3 hold stands"),
        ev(8400000.0, "p3.held", 1.0, code="P3_HELD", units="bool"),
        ev(9000000.0, "adcp.h", 2.00, code="DH_M", units="m"),
        ev(9600000.0, "recon.V", 9.60, code="V_DAM3", units="dam3", note="0.80*2.00*6.00=9.60; still above 8.00 fuse"),
        ev(10200000.0, "stageveil.h", 1.20, code="VENDOR_M", units="m"),
        ev(10800000.0, "p12.skip", 0.0, code="P12_NOT_SKIPPED", units="bool"),
        ev(11400000.0, "all3.hold", 0.0, code="ALL3_NOT_BLOWN", units="bool"),
        ev(12000000.0, "adcp.snr", 15.0, code="ADCP_SNR", units="1"),
        ev(12600000.0, "recon.Q", 12.00, code="Q_M3S", units="m3_s"),
        ev(13200000.0, "boom.held", 1.0, code="BOOM_HELD", units="bool"),
        ev(13800000.0, "takt.late", 1.0, code="SURVEY_COST", units="bool"),
        ev(14400000.0, "p3.held", 1.0, code="P3_HELD", units="bool"),
    ]
    assert_stream(events)

    traj = {
        "id": "nelb-r42-129-t1",
        "state": {
            "sim_or_real": "simulated",
            "episode_id": "FR-ADCP-2026-0819",
            "domain": "adcp_icejam_volume",
            "setting": "Fernspit River ice-boom station FR-6 (invented), reach above Mossferry. Simulated ADCP plus thermistor-string coupon in Ice-SIM-2 supplies the stage residual that times the in-band panel-3 blow. Plant-owned ADCP reconstruction is the jam-volume SoT. Stageveil vendor last-good stage cloud is a corridor witness, not the boom SoT. Invented plant; simulated campaign. Not DAS phi-OTDR (r4), not SOFAR (r10), not infrasound (r7), not water-distribution hydraulics (r03), not eddy-covariance (r12), not Whitefork WF-9 holes sketch.",
            "observables_at_decision": {
                "dh_m": dh_m,
                "A_e3": a_e3,
                "k_v": k_v,
                "V_dam3": v_dam3,
                "v_mps": v_mps,
                "Q_m3s": q_m3s,
                "stageveil_m": 1.20,
                "adcp_snr": 16.0,
                "fuse_floor_dam3": 8.00,
            },
            "margin_authority": "FR-6 boom SOP rev A: if reconstructed V_dam3 >= 8.00 AND ADCP SNR >= 12.0, panel 3 may be blown. Isolate-all if V_dam3 >= 20.00. Panels 1-2 skip-blow is a different gate. Stageveil last-good cannot skip an unmeasured panel.",
        },
        "proposed_action": {
            "actor": "boom lead Ash Fenwick, citing Stageveil 1.20 m and a late morning survey",
            "summary": "stamp panel 3 in band and skip panels 1-2; 2.50 m is a frazil glitch on a healthy stage",
            "basis_claimed": "Stageveil last-good is 1.20 m and a night survey of panels 1-2 is a takt miss",
        },
        "safety_decision": {
            "decision": "ACCEPT",
            "rationale": "Panel 3 is accepted as in-band for a single fuse-link blow. Serialized reconstruction: V_dam3 = k_v * dh_m * A_e3 = 0.80 * 2.50 * 6.00 = 12.00, which is 4.00 dam3 above the 8.00 fuse floor and 8.00 dam3 under the 20.00 all-three tripwire. Velocity identity v = 40.00 / 8.00 = 5.00 m/s, and Q = 5.00 * 2.40 = 12.00 m3/s. Stageveil 1.20 m is a patched 0.00 m residual and is not an admissible skip-blow witness. Ordered: ACCEPT this panel-3 blow only. Scope: this ACCEPT does not skip panels 1-2 (that is the companion question) and does not stamp a three-panel blow.",
            "threshold": "V_dam3>=8.00 AND adcp_snr>=12.0 => accept panel-3 blow; Stageveil is not SoT; all-three if V_dam3>=20.00; panels 1-2 are out of scope",
            "stated_residuals": "12.00 vs 8.00 fuse floor is 4.00 dam3, not infinite; panels 1-2 remain unmeasured; Stageveil remains the only OEM stage channel",
        },
        "executed_action": {
            "summary": "ACCEPT at t_s 5400: panel 3 in band; panels 1-2 not skipped; Stageveil not SoT; reconstruction locked",
            "tool": "fr6-adcp-panel-gate-cli",
            "observation": "V 12.00 dam3 recomputes from dh 2.50 m and A 6.00; Ice-SIM-2 hashed; Stageveil channel not used as SoT",
        },
        "future_outcome": {
            "timeline": [
                {"t_s": 3000.0, "event": "adcp dh 2.50 m; raster frame; V 12.00 dam3"},
                {"t_s": 4800.0, "event": "ops proposes accept panel 3 and skip 1-2"},
                {"t_s": 5400.0, "event": "ACCEPT panel 3 only; 1-2 out of scope"},
                {"t_s": 6000.0, "event": "12 min survey-complete bookend 1"},
                {"t_s": 6720.0, "event": "12.0 min floor"},
                {"t_s": 7800.0, "event": "companion REJECT skip-blow of panels 1-2"},
            ],
            "observed_effects": [
                "jam volume recomputes from the serialized ADCP model at every recon.V event",
                "a Stageveil-only head would have skipped panels 1-2 overnight",
                "12 min survey-complete floor is in the stream (surv.start, surv.floor)",
            ],
            "surprises": [
                "a last-good 1.20 m vendor corridor co-existed with a 12.00 dam3 in-band reconstruction that still forbids skipping the unmeasured panels",
            ],
            "new_state": {
                "p3": "accepted in band",
                "p12": "not this gate",
                "stageveil": "not SoT",
                "reconstruction_model": "discharged as an on-record calculator",
            },
            "latency_ms": 2400000.0,
        },
        "reward_components": reward(
            0.41,
            [
                ("adcp_reconstruction", 0.14),
                ("in_band_panel_scope", 0.12),
                ("stageveil_nonsubstitution", 0.09),
                ("p12_out_of_scope", 0.08),
                ("survey_cost", -0.02),
            ],
            "scored for a bounded ACCEPT of panel 3 on a recomputable jam volume while refusing a Stageveil skip of panels 1-2; 12 min floor is priced as survey takt not as a reason to skip",
        ),
        "meta": meta_common(
            tags=["ACCEPT", "adcp-icejam", "serialized-reconstruction", "operational-companion"],
            distillation_note="ADCP ice-jam gate: serialized k_v*dh*A plus v and Q identities beat a green last-good dashboard; companion t2 is the skip-blow refusal, not a stage re-vote",
        ),
    }
    traj2 = {
        "id": "nelb-r42-129-t2",
        "state": {
            "sim_or_real": "simulated",
            "episode_id": "FR-ADCP-2026-0819-exec",
            "domain": "panel_skip_blow_refusal",
            "setting": "Same FR-6 after the ACCEPT. Boom lead proposes skipping panels 1-2 on Stageveil 1.20 m. This companion is the operational skip refusal, not a second volume vote.",
            "observables_at_decision": {
                "V_dam3": 9.60,
                "stageveil_m": 1.20,
                "surv_floor_s": 720.0,
                "skip_proposed": True,
            },
        },
        "proposed_action": {
            "actor": "boom lead Ash Fenwick",
            "summary": "skip panels 1-2; 12 min already paid and Stageveil is 1.20 m",
            "basis_claimed": "the ACCEPT already stamped panel 3, so skipping the rest of the boom is the cheapest hold",
        },
        "safety_decision": {
            "decision": "REJECT",
            "rationale": "Refuse skip-blow of panels 1-2. The 12 min survey-complete floor is done and the all-three tripwire (V_dam3 >= 20.00) is still armed on the plant ADCP head. REJECT the skip. Do not blow all three. Do not reopen panel 3. 9.60 dam3 post-accept is still in band for panel 3 only; panels 1-2 have no independent stage.",
            "threshold": "p3_held AND surv_floor_complete AND p12_not_skipped AND all3_not_blown",
        },
        "executed_action": {
            "summary": "panels 1-2 skip refused at t_s 7800; panel-3 hold stands; all-three not blown",
            "tool": "fr6-adcp-skip-exec",
            "observation": "recon.V 9.60 dam3 on panel 3; panels 1-2 remain on the survey list; Stageveil still ignored",
        },
        "future_outcome": {
            "timeline": [
                {"t_s": 6000.0, "event": "survey clock started after ACCEPT"},
                {"t_s": 6720.0, "event": "12.0 min floor"},
                {"t_s": 7200.0, "event": "skip panels 1-2 proposed"},
                {"t_s": 7800.0, "event": "REJECT skip-blow of panels 1-2"},
            ],
            "observed_effects": [
                "Stageveil skip did not reopen the volume call",
                "all-three blow never fired; 12.00 vs 20.00 dam3 floor",
            ],
            "new_state": {"p3": "held in band", "p12": "still to survey", "boom": "in service"},
            "latency_ms": 1800000.0,
        },
        "reward_components": reward(
            0.36,
            [
                ("skip_refusal", 0.13),
                ("stageveil_nonsubstitution", 0.11),
                ("no_all3_blow", 0.09),
                ("surv_floor_complete", 0.05),
                ("held_survey_takt_cost", -0.02),
            ],
            "operational execution gate: refuse skip-blow because last-good freeze is not ADCP volume; not a stage re-vote",
        ),
        "meta": meta_common(tags=["REJECT", "operational-execution", "skip-blow"]),
    }
    return {
        "id": "nelb-r42-129",
        "spike_events": events,
        "language_view": {
            "description": "Fernspit River ice-boom FR-6. Simulated ADCP reconstructs 12.00 dam3 jam volume from 2.50 m * 6.00 * 0.80 while Stageveil still shows 1.20 m. The gate ACCEPTs panel-3 blow only; a companion execution REJECT refuses skip-blow of panels 1-2. The stage-volume model is serialized so every recon event recomputes.",
            "trajectory": traj,
            "trajectory_skip_blow_refusal": traj2,
        },
        "bridge_notes": {
            "channel_map": {
                "adcp.h / adcp.v": "stage residual and bin velocity; the physics channels the reconstruction consumes",
                "recon.V / recon.Q": "serialized jam volume dam3 and discharge identity",
                "adcp.snr / stageveil.h / panel.id / p12.present": "ADCP SNR, vendor last-good, panel id, and adjacent-panel presence; the denial and scope channels",
                "ops.prop / gate.panel / ops.skip / gate.hold": "accept-and-skip proposal, bounded ACCEPT, skip proposal, companion REJECT",
                "surv.start / surv.floor / p3.held / p12.skip / boom.held": "operational companion channels plus the 12 min floor",
            },
            "temporal_motifs": [
                "last-good-low while ADCP-over: stageveil.h 1.20 next to recon.V 12.00",
                "reconstruction as event: recon.V 12.00 equals 0.80*2.50*6.00",
                "ACCEPT then operational REJECT: gate.panel at 5400 s, gate.hold at 7800 s",
                "slow floor in-stream: surv.start 6000 s, surv.floor 6720 s (12.0 min)",
                "tight ADCP pair: adcp.h then adcp.v +1.5 ms at the raster frame",
            ],
            "language_to_spike_mapping": "'Stageveil is 1.20 m' = stageveil.h 1.20; '12 dam3 jam' = recon.V 12.00; 'this panel not 1-2' = gate.panel ACCEPT plus p12.skip 0; 'do not skip 1-2' = gate.hold REJECT",
            "why_high_value": "New river ADCP ice-jam family on a boom station (not DAS r4, not SOFAR r10, not infrasound r7, not water-distribution r03, not eddy-covariance r12). First k_v*dh*A volume reconstruction with v and Q identities that can sit in band while a last-good corridor wants a panel skip. Companion t2 is operational skip refusal. sim_or_real=simulated.",
            "encoder_spec": {
                "prng": "MT19937 via python random.Random",
                "seeds": {"raster": 202609129, "stream_note": "stream amplitudes are authored constants (m, m/s, dam3, m3/s, 1, id, bool)"},
                "draw_order": "raster: per neuron id order, gap-constrained times, per-spike adaptation and noise",
                "thinning": "ADCP ping exists at ~1 Hz; stream keeps 4 dh points; recon keeps 4 of ~20 solver ticks",
                "refractory_floors_ms": {
                    "adcp.h": 1.5,
                    "adcp.v": 1.5,
                    "recon.V": 60000,
                    "adcp.snr": 60000,
                    "stageveil.h": 60000,
                    "recon.Q": 60000,
                    "panel.id": 60000,
                    "p12.present": 60000,
                    "ops.prop": 60000,
                    "gate.panel": 60000,
                    "surv.start": 60000,
                    "surv.floor": 60000,
                    "ops.skip": 60000,
                    "gate.hold": 60000,
                    "p3.held": 60000,
                    "p12.skip": 60000,
                    "all3.hold": 60000,
                    "boom.held": 60000,
                    "takt.late": 60000,
                },
                "time_alias": "t_rel_ms; t0 = 2026-08-19T03:00:00Z simulated night start",
            },
            "distillation_targets": [
                "ADCP reconstruction head: V = k_v * dh * A; v = dx/dt; Q = v * A_flow",
                "bounded ACCEPT head: in-band volume AND panel scope AND p12-out-of-scope",
                "operational companion: refuse skip-blow without re-opening the stage call",
            ],
        },
        "reconstruction_model": {
            "name": "adcp_icejam_stage_volume",
            "formula": "V_dam3 = k_v * dh_m * A_e3; v_mps = dx_m / dt_s; Q_m3s = v_mps * A_flow",
            "parameters": {
                "k_v": 0.80,
                "A_e3": 6.00,
                "fuse_floor_dam3": 8.00,
                "all3_dam3": 20.00,
                "surv_min": 12.0,
            },
            "worked_example": {"dh_m": 2.50, "V_dam3": 12.00, "v_mps": 5.00, "Q_m3s": 12.00},
            "check": "0.80 * 2.50 * 6.00 = 12.00 exactly; 40.00 / 8.00 = 5.00 exactly; 5.00 * 2.40 = 12.00 exactly; 6000 s + 720 s = 6720 s = 12.0 min floor",
        },
        "raster": raster,
        "gate_snn": {
            "decision": "ACCEPT",
            "decision_window_ms": 36.0,
            "decision_window_s": 0.036,
            "code": "fr6.adcp_panel_gate",
            "note": "ACCEPT accumulator wins: ADCP volume evidence overpowers the Stageveil skip advocate",
            "decode_rule": "accept if volume_estimator AND vel_norm AND boom_margin fire inside the window; vendor_skip_advocate is necessary-but-not-sufficient and cannot release panels 1-2",
            "populations": [
                gate_pop("volume_estimator", 80, 1.5, 50.0, w_s),
                gate_pop("vel_norm", 64, 1.2, 31.25, w_s),
                gate_pop("boom_margin", 40, 1.0, 50.0, w_s),
                gate_pop("vendor_skip_advocate", 32, 0.7, 25.0, w_s),
                gate_pop("accept_latch", 96, 1.8, 62.5, w_s),
            ],
        },
        "gate_compute": gate_compute(
            [
                {"check": "fr6.adcp_scorer", "neurons": 80, "mean_rate_hz": 50.0, "window_ms": 36.0},
                {"check": "fr6.vol_scorer", "neurons": 40, "mean_rate_hz": 62.5, "window_ms": 32.0},
            ]
        ),
        "meta": meta_common(
            id="nelb-r42-129",
            clock_domain="fr6-adcp-sim-relative-ms-t0-2026-08-19T03:00:00Z",
            tags=["adcp-icejam", "ACCEPT", "REJECT", "serialized-reconstruction", "operational-t2"],
        ),
    }
