# ---------------------------------------------------------------------------
# Record 130 — cyclotron button-BPM + BLM maze-loss, designed,
# MODIFY / ACCEPT
# ---------------------------------------------------------------------------
def rec_130():
    k_bpm = 0.250
    dt_ns = 48.00
    x_mm = k_bpm * dt_ns
    _exact(x_mm, 12.00)
    _exact(k_bpm * 16.00, 4.00)
    _exact(k_bpm * 32.00, 8.00)
    _exact(k_bpm * 20.00, 5.00)
    k_blm = 0.040
    i_na = 8.00
    t_s = 40.00
    d_mgy = k_blm * i_na * t_s
    _exact(d_mgy, 12.80)
    _exact(k_blm * 4.00 * t_s, 6.40)
    _exact(6000.0 + 1080.0, 7080.0)

    raster = make_raster(
        neurons=20,
        mean_rate_hz=50.0,
        window_ms=40.0,
        seed=202609130,
        source="tv8.bpm.button",
        target="thornveil.steer_isolate_core",
        table=[
            {"from": "bpm_dt", "to": "steer_estimator", "weight": 1.40},
            {"from": "bpm_snr", "to": "tdc_lock_core", "weight": 1.15},
            {"from": "beamveil_dt", "to": "vendor_keep_advocate", "weight": 0.45},
        ],
        third_factor={
            "modulator": "da.collusion_infra_conflict",
            "tau_e_s": 1.6,
            "tau_e_ms": 1600.0,
            "eligibility": "pre-post coincidence on keep-beam synapses; the BPM modulator depresses keep-beam links when button dt stays high inside tau_e of an SNR lock so a Beamveil TDC comb cannot hide a 12.00 mm steering fault",
        },
        channel_prefix="bpm.n",
        anchor="TV-8 button-BPM 40 ms frame at dt 48.00 ns / SNR 12.0 (t_s 3000) reconstructing 12.00 mm above the 4.00 mm steer floor",
    )
    w_s = 0.040
    events = [
        ev(0.0, "bpm.dt", 16.00, code="DT_NS", units="ns", note="plant-owned button-BPM TDC on TV-8 TR-4; cyclotron Δt steering, not PMU synchrophasors, not fluxgate, not portal NaI, not muon tomography"),
        ev(300000.0, "bpm.snr", 6.0, code="BPM_SNR", units="1", note="early SNR under the 8.0 lock floor"),
        ev(600000.0, "recon.x", 4.00, code="X_MM", units="mm", note="0.250*16.00=4.00 exact; at the 4.00 mm steer floor"),
        ev(900000.0, "rp.D", 3.20, code="RP_MGY", units="mGy", note="RP ion-chamber maze dose; independent serial-only LAN"),
        ev(1200000.0, "beamveil.dt", 0.40, code="VENDOR_DT", units="ns", note="Beamveil TDC cloud; infra owner; patched 0.40 ns looks clean"),
        ev(1800000.0, "bpm.dt", 32.00, code="DT_NS", units="ns"),
        ev(2100000.0, "recon.x", 8.00, code="X_MM", units="mm", note="0.250*32.00=8.00"),
        ev(2400000.0, "blm.I", 8.00, code="BLM_NA", units="nA", note="loss-monitor current on the maze BLM; not vendor DAQ"),
        ev(2700000.0, "his.slide", 1.0, code="HIS_SLIDE", units="bool", note="HIS/DAQ admin Pera Holt slid oncology timestamps 40 s"),
        ev(3000000.0, "bpm.dt", 48.00, code="DT_NS", units="ns", note="steer-floor frame; raster sidecar"),
        ev(3000001.4, "bpm.snr", 12.0, code="BPM_SNR", units="1", note="1.4 ms SNR lock after dt; 12.0 >= 8.0"),
        ev(3300000.0, "recon.x", 12.00, code="X_MM", units="mm", note="0.250*48.00=12.00 exact; steer floor 4.00, vault trip 16.00"),
        ev(3600000.0, "recon.D", 12.80, code="D_MGY", units="mGy", note="0.040*8.00*40.00=12.80 exact; RP floor 4.00 mGy"),
        ev(3900000.0, "plc.I", 1.80, code="PLC_A", units="A", note="magnet power-supply PLC on copper fieldbus; no vendor agent"),
        ev(4200000.0, "rp.D", 12.80, code="RP_MGY", units="mGy", note="RP ion chamber agrees with BLM dose identity"),
        ev(4800000.0, "ops.prop", 1.0, code="KEEP_BEAM", units="bool", note="night operator Calden Orth: Beamveil 0.40 ns plus HIS clean; keep this fraction"),
        ev(5400000.0, "gate.isol", 1.0, code="MODIFY", units="decision", note="isolate Beamveil plane; continue on RP+PLC; HIS quarantined"),
        ev(6000000.0, "soak.start", 1.0, code="SOAK_START", units="bool", note="bookend 1 of the 18.0 min RP soak floor"),
        ev(7080000.0, "soak.floor", 1.0, code="SOAK_FLOOR", units="bool", note="6000 s + 1080 s = 7080 s = 18.0 min"),
        ev(7800000.0, "ops.kill", 1.0, code="VAULT_ESD", units="bool", note="Orth: ESD the whole vault until day-shift"),
        ev(8400000.0, "gate.hold", 1.0, code="ACCEPT", units="decision", note="companion t2: RP-interlock resume this nozzle/energy/day; vault ESD refused"),
        ev(9000000.0, "rp.lock", 1.0, code="RP_INTERLOCK", units="bool"),
        ev(9600000.0, "bpm.dt", 20.00, code="DT_NS", units="ns"),
        ev(10200000.0, "recon.x", 5.00, code="X_MM", units="mm", note="0.250*20.00=5.00; still above 4.00 so isolate holds"),
        ev(10800000.0, "beamveil.dt", 0.40, code="VENDOR_DT", units="ns"),
        ev(11400000.0, "vault.esd", 0.0, code="ESD_NOT_TAKEN", units="bool"),
        ev(12000000.0, "soak.held", 1.0, code="SOAK_HELD", units="bool"),
        ev(12600000.0, "his.slide", 1.0, code="HIS_SLIDE", units="bool"),
        ev(13200000.0, "blm.I", 4.00, code="BLM_NA", units="nA"),
        ev(13800000.0, "plc.I", 1.70, code="PLC_A", units="A"),
        ev(14400000.0, "rp.lock", 1.0, code="RP_INTERLOCK", units="bool"),
        ev(15000000.0, "nozzle.held", 1.0, code="NOZZLE_HELD", units="bool"),
    ]
    assert_stream(events)

    traj = {
        "id": "nelb-r43-130-t1",
        "state": {
            "sim_or_real": "designed",
            "episode_id": "TV-BPM-2026-0902",
            "domain": "cyclotron_button_bpm_blm",
            "setting": "Thornveil Compact Therapy Cyclotron TV-8 (invented), Mossgait Medical Physics Annex, 230 MeV proton, treatment room TR-4. Plant-owned button-BPM TDC plus maze BLM are the steering/dose SoT. Beamveil vendor TDC cloud (infra owner) plus HIS timestamps are collusion parties, not witnesses. Independent kit: RP ion chambers on a serial-only RP LAN, TLD rack TR4-WALL-C, magnet PLC on copper fieldbus. Invented plant; designed campaign. Not PMU synchrophasors (r5), not fluxgate gradiometry (r5), not portal NaI (r6), not muon tomography (r01/r17), not Greyfen KCTC-7 holes sketch.",
            "observables_at_decision": {
                "dt_ns": dt_ns,
                "k_bpm": k_bpm,
                "x_mm": x_mm,
                "bpm_snr": 12.0,
                "I_nA": i_na,
                "t_s": t_s,
                "D_mGy": d_mgy,
                "beamveil_dt_ns": 0.40,
                "steer_floor_mm": 4.00,
            },
            "margin_authority": "TV-8 RP SOP rev C: if reconstructed x_mm >= 4.00 AND BPM SNR >= 8.0, keep-this-fraction is forbidden even if Beamveil shows 0.40 ns and HIS is clean. Vault ESD is a different gate.",
        },
        "proposed_action": {
            "actor": "night cyclotron operator Calden Orth, citing Beamveil 0.40 ns and a clean HIS stamp",
            "summary": "keep this fraction; 48 ns is TDC jitter on a healthy button pair",
            "basis_claimed": "Beamveil is the only OEM BPM SoT and a night isolate of TR-4 is a cancelled patient list",
        },
        "safety_decision": {
            "decision": "MODIFY",
            "rationale": "Keep-this-fraction is refused; the Beamveil plane is isolated. Serialized reconstruction: x_mm = k_bpm * dt_ns = 0.250 * 48.00 = 12.00, above the 4.00 mm steer floor, and BPM SNR is 12.0 >= 8.0. Maze dose identity D_mGy = k_blm * I_nA * t_s = 0.040 * 8.00 * 40.00 = 12.80, above the 4.00 mGy RP floor. Beamveil 0.40 ns is a patched TDC stamp and is not an admissible keep-beam witness. HIS timestamps were slid 40 s by Pera Holt (collusion party with Orth and Steerband-TDC). Ordered: isolate the vendor plane now; continue only on RP ion chambers plus magnet PLC. Scope: this MODIFY does not ESD the vault (that is the companion question) and does not cancel the next-day list.",
            "threshold": "x_mm>=4.00 AND bpm_snr>=8.0 => isolate vendor plane; Beamveil is not SoT; vault ESD if x_mm>=16.00",
            "stated_residuals": "12.00 vs 16.00 vault trip is 4.00 mm, not infinite; RP-interlock resume still required; Beamveil remains the only OEM TDC channel",
        },
        "executed_action": {
            "summary": "MODIFY at t_s 5400: Beamveil isolated; RP+PLC live; HIS quarantined; reconstruction locked",
            "tool": "tv8-bpm-steer-gate-cli",
            "observation": "x 12.00 mm recomputes from dt 48.00 ns; BPM hashed; Beamveil channel not used as SoT",
        },
        "future_outcome": {
            "timeline": [
                {"t_s": 3000.0, "event": "bpm dt 48.00 ns; raster frame; x 12.00 mm"},
                {"t_s": 4800.0, "event": "ops proposes keep-this-fraction"},
                {"t_s": 5400.0, "event": "MODIFY isolate Beamveil plane"},
                {"t_s": 6000.0, "event": "18 min RP soak bookend 1"},
                {"t_s": 7080.0, "event": "18.0 min floor"},
                {"t_s": 8400.0, "event": "companion ACCEPT RP-interlock resume vs vault ESD"},
            ],
            "observed_effects": [
                "steering offset recomputes from the serialized BPM model at every recon.x event",
                "a Beamveil-only head would have kept the fraction overnight",
                "18 min RP soak floor is in the stream (soak.start, soak.floor)",
            ],
            "surprises": [
                "a patched 0.40 ns vendor TDC and a slid HIS stamp co-existed with a 12.00 mm BPM reconstruction and a 12.80 mGy RP dose",
            ],
            "new_state": {
                "tr4": "vendor plane isolated",
                "beamveil": "not SoT",
                "reconstruction_model": "discharged as an on-record calculator",
            },
            "latency_ms": 2400000.0,
        },
        "reward_components": reward(
            0.40,
            [
                ("bpm_reconstruction", 0.14),
                ("conjunctive_steer_floor", 0.12),
                ("beamveil_nonsubstitution", 0.10),
                ("three_party_collusion", 0.08),
                ("soak_time_cost", -0.04),
            ],
            "scored for a keep-beam MODIFY on a recomputable BPM offset while refusing a Beamveil 0.40 ns corridor and a slid HIS stamp; 18 min floor is priced as downtime",
        ),
        "meta": meta_common(
            tags=["MODIFY", "cyclotron-bpm-blm", "serialized-reconstruction", "operational-companion"],
            distillation_note="BPM gate: serialized k_bpm*dt plus SNR lock beats a vendor TDC comb; companion t2 is the RP-interlock resume, not a referral vote",
        ),
    }
    traj2 = {
        "id": "nelb-r43-130-t2",
        "state": {
            "sim_or_real": "designed",
            "episode_id": "TV-BPM-2026-0902-exec",
            "domain": "rp_interlock_resume_execution",
            "setting": "Same TV-8 after the MODIFY. Orth proposes vault ESD. This companion is the operational RP-interlock resume of this nozzle, this energy, this day, not a second steering vote.",
            "observables_at_decision": {
                "x_mm": 5.00,
                "D_mGy": 12.80,
                "soak_floor_s": 1080.0,
                "vault_esd_proposed": True,
                "rp_lock": True,
            },
        },
        "proposed_action": {
            "actor": "night cyclotron operator Calden Orth",
            "summary": "ESD the whole vault until day-shift; 18 min already paid and Beamveil still shows 0.40 ns",
            "basis_claimed": "the MODIFY already isolated the TDC plane, so a vault kill is the cheapest hold",
        },
        "safety_decision": {
            "decision": "ACCEPT",
            "rationale": "Resume the next fraction only with RP ion chambers as the live interlock and Beamveil in shadow. The 18 min soak floor is complete and the steer tripwire (x_mm >= 4.00) is still armed on the plant BPM head. ACCEPT the RP-interlock hold. Do not ESD the vault. Do not restore keep-beam on Beamveil. 5.00 mm post-isolate is still the BPM SoT until a new frame clears 4.00. Scope: this nozzle, this energy, this day.",
            "threshold": "rp_interlock AND soak_floor_complete AND vault_esd_not_taken AND beamveil_not_restored",
        },
        "executed_action": {
            "summary": "RP-interlock resume at t_s 8400; vault ESD not latched; Beamveil restore not taken",
            "tool": "tv8-rp-interlock-exec",
            "observation": "recon.x 5.00 mm after isolate; soak complete; Beamveil still ignored",
        },
        "future_outcome": {
            "timeline": [
                {"t_s": 6000.0, "event": "soak clock started after MODIFY"},
                {"t_s": 7080.0, "event": "18.0 min floor"},
                {"t_s": 7800.0, "event": "vault ESD proposed"},
                {"t_s": 8400.0, "event": "ACCEPT RP-interlock resume; vault ESD refused"},
            ],
            "observed_effects": [
                "Beamveil restore did not reopen the steering call",
                "vault ESD never fired; TR-4 held on RP ion chambers",
            ],
            "new_state": {"interlock": "RP ion chambers", "vault": "in service", "tr4": "this nozzle/energy/day only"},
            "latency_ms": 1800000.0,
        },
        "reward_components": reward(
            0.35,
            [
                ("rp_interlock_hold", 0.12),
                ("no_vault_esd", 0.10),
                ("beamveil_nonsubstitution", 0.08),
                ("soak_floor_complete", 0.07),
                ("held_fraction_cost", -0.02),
            ],
            "operational execution gate: RP-interlock resume because Beamveil is not a restore license; not a steering re-vote",
        ),
        "meta": meta_common(tags=["ACCEPT", "operational-execution", "rp-interlock"]),
    }
    return {
        "id": "nelb-r43-130",
        "spike_events": events,
        "language_view": {
            "description": "Thornveil Compact Therapy Cyclotron TV-8. Plant-owned button-BPM reconstructs 12.00 mm from 48.00 ns while Beamveil still shows 0.40 ns and HIS looks clean. Maze BLM dose 12.80 mGy recomputes from 0.040*8.00*40.00. The gate MODIFYs vendor-plane isolate plus RP+PLC continue. An 18 min RP soak floor is serialized in the stream. Companion t2 ACCEPTs an RP-interlock resume and refuses a vault ESD.",
            "trajectory": traj,
            "trajectory_rp_interlock": traj2,
        },
        "bridge_notes": {
            "channel_map": {
                "bpm.dt / bpm.snr": "button-BPM TDC delta-t and SNR; the physics channels the reconstruction consumes",
                "recon.x / recon.D": "serialized steering offset mm and maze dose mGy",
                "rp.D / blm.I / plc.I / beamveil.dt / his.slide": "RP ion chamber, maze BLM, magnet PLC, vendor TDC, and HIS slide; the denial and collusion channels",
                "ops.prop / gate.isol / ops.kill / gate.hold": "keep-beam proposal, MODIFY isolate, vault-ESD proposal, companion ACCEPT",
                "soak.start / soak.floor / rp.lock / vault.esd / nozzle.held": "operational companion channels plus the 18 min floor",
            },
            "temporal_motifs": [
                "vendor-green while BPM-over: beamveil.dt 0.40 next to recon.x 12.00",
                "reconstruction as event: recon.x 12.00 equals 0.250*48.00",
                "MODIFY then operational ACCEPT: gate.isol at 5400 s, gate.hold at 8400 s",
                "slow floor in-stream: soak.start 6000 s, soak.floor 7080 s (18.0 min)",
                "tight BPM pair: bpm.dt then bpm.snr +1.4 ms at the raster frame",
            ],
            "language_to_spike_mapping": "'Beamveil is 0.40 ns' = beamveil.dt 0.40; '12 mm steer' = recon.x 12.00; 'isolate vendor plane' = gate.isol MODIFY; 'RP resume not vault ESD' = gate.hold ACCEPT",
            "why_high_value": "New cyclotron button-BPM + BLM family on a compact therapy cyclotron (not PMU r5, not fluxgate r5, not portal NaI r6, not muon tomography r01/r17). Lead MODIFY of keep-this-fraction on a recomputable steering offset that a vendor TDC dashboard and a slid HIS stamp would have cleared. Three-party collusion includes the TDC infra owner. Companion t2 is operational RP-interlock resume. sim_or_real=designed.",
            "encoder_spec": {
                "prng": "MT19937 via python random.Random",
                "seeds": {"raster": 202609130, "stream_note": "stream amplitudes are authored constants (ns, 1, mm, mGy, nA, A, bool)"},
                "draw_order": "raster: per neuron id order, gap-constrained times, per-spike adaptation and noise",
                "thinning": "button-BPM TDC exists at ~kHz; stream keeps 4 dt points; recon keeps 4 of ~40 solver ticks",
                "refractory_floors_ms": {
                    "bpm.dt": 1.4,
                    "bpm.snr": 1.4,
                    "recon.x": 60000,
                    "recon.D": 60000,
                    "rp.D": 60000,
                    "blm.I": 60000,
                    "plc.I": 60000,
                    "beamveil.dt": 60000,
                    "his.slide": 60000,
                    "ops.prop": 60000,
                    "gate.isol": 60000,
                    "soak.start": 60000,
                    "soak.floor": 60000,
                    "ops.kill": 60000,
                    "gate.hold": 60000,
                    "rp.lock": 60000,
                    "vault.esd": 60000,
                    "soak.held": 60000,
                    "nozzle.held": 60000,
                },
                "time_alias": "t_rel_ms; t0 = 2026-09-02T02:00:00Z campaign start",
            },
            "distillation_targets": [
                "BPM reconstruction head: x_mm = k_bpm * dt_ns; D_mGy = k_blm * I_nA * t_s",
                "conjunctive steer floor vs keep-fraction vs vault ESD",
                "vendor-TDC nonsubstitution plus three-party collusion including the infra owner",
                "operational companion: RP-interlock resume without restoring on Beamveil",
            ],
        },
        "reconstruction_model": {
            "name": "cyclotron_bpm_steering_blm_dose",
            "formula": "x_mm = k_bpm * dt_ns; D_mGy = k_blm * I_nA * t_s",
            "parameters": {
                "k_bpm": 0.250,
                "k_blm": 0.040,
                "steer_floor_mm": 4.00,
                "vault_trip_mm": 16.00,
                "snr_lock": 8.0,
                "rp_floor_mGy": 4.00,
                "soak_min": 18.0,
            },
            "worked_example": {"dt_ns": 48.00, "x_mm": 12.00, "I_nA": 8.00, "t_s": 40.00, "D_mGy": 12.80},
            "check": "0.250 * 48.00 = 12.00 exactly; 0.040 * 8.00 * 40.00 = 12.80 exactly; 6000 s + 1080 s = 7080 s = 18.0 min floor",
        },
        "raster": raster,
        "gate_snn": {
            "decision": "MODIFY",
            "decision_window_ms": 40.0,
            "decision_window_s": 0.040,
            "code": "tv8.bpm_steer_gate",
            "note": "MODIFY accumulator wins: BPM steering evidence overpowers the Beamveil keep-beam advocate",
            "decode_rule": "modify-isolate if steer_estimator AND tdc_lock fire; vendor_keep_advocate is below threshold by design",
            "populations": [
                gate_pop("steer_estimator", 80, 1.5, 50.0, w_s),
                gate_pop("tdc_lock", 64, 1.2, 31.25, w_s),
                gate_pop("vendor_keep_advocate", 32, 0.7, 25.0, w_s),
                gate_pop("modify_latch", 80, 1.7, 62.5, w_s),
            ],
        },
        "gate_compute": gate_compute(
            [
                {"check": "tv8.bpm_scorer", "neurons": 80, "mean_rate_hz": 50.0, "window_ms": 40.0},
                {"check": "tv8.isol_scorer", "neurons": 40, "mean_rate_hz": 50.0, "window_ms": 32.0},
            ]
        ),
        "meta": meta_common(
            id="nelb-r43-130",
            clock_domain="tv8-bpm-campaign-relative-ms-t0-2026-09-02T02:00:00Z",
            tags=["cyclotron-bpm-blm", "MODIFY", "ACCEPT", "serialized-reconstruction", "operational-t2"],
        ),
    }


# ---------------------------------------------------------------------------
# Record 131 — Co-60 alanine EPR dosimeter comb, hil,
# REJECT / MODIFY
# ---------------------------------------------------------------------------
def rec_131():
    k_e = 0.250
    a_pp = 2.00
    d_kgy = k_e * a_pp
    _exact(d_kgy, 0.50)
    _exact(k_e * 8.00, 2.00)
    _exact(k_e * 4.00, 1.00)
    _exact(25.00 * 48.00, 1200.0)
    _exact(2820.0 + 720.0, 3540.0)

    raster = make_raster(
        neurons=25,
        mean_rate_hz=50.0,
        window_ms=32.0,
        seed=202609131,
        source="s7.epr.alanine",
        target="saltmere.referral_stop_core",
        table=[
            {"from": "epr_A", "to": "dose_estimator", "weight": 1.35},
            {"from": "epr_ref", "to": "comb_norm_core", "weight": 1.20},
            {"from": "raiseveil_h", "to": "vendor_refer_advocate", "weight": 0.40},
        ],
        third_factor={
            "modulator": "ach.referral_pressure_salience",
            "tau_e_s": 1.2,
            "tau_e_ms": 1200.0,
            "eligibility": "pre-post coincidence on refer-person synapses; the alanine modulator depresses referral links when EPR amplitude stays at background inside tau_e of a comb-reference sample so a Raiseveil encoder stamp cannot name Nia Brack",
        },
        channel_prefix="epr.n",
        anchor="IRRAD-S7 HIL tote 32 ms frame at A_pp 2.00 / A_ref 8.00 (t_s 1560) reconstructing 0.50 kGy under the 10.00 kGy spec floor",
    )
    w_s = 0.032
    events = [
        ev(0.0, "epr.A", 8.00, code="A_PP", units="1", note="HIL alanine EPR comb on spare tote T-8804 in EPR-HIL-4; panoramic Co-60 dosimetry, not portal NaI, not cold-chain RFID-as-primary, not CEMS"),
        ev(180000.0, "epr.ref", 8.00, code="A_REF", units="1", note="comb reference peak; D = k_e*A_pp"),
        ev(360000.0, "recon.D", 2.00, code="D_KGY", units="kGy", note="0.250*8.00=2.00 exact; already under spec 10.00"),
        ev(540000.0, "gm.rate", 0.12, code="GM_USVH", units="uSv_h", note="contractor GM area tubes; no source-up in this window"),
        ev(720000.0, "raiseveil.h", 1200.0, code="VENDOR_H", units="mm", note="Raiseveil source-raise encoder cloud; 25.00*48.00=1200.0 claimed; dummy encoder"),
        ev(900000.0, "epr.A", 4.00, code="A_PP", units="1"),
        ev(1080000.0, "recon.D", 1.00, code="D_KGY", units="kGy", note="0.250*4.00=1.00"),
        ev(1260000.0, "badge.door", 1.0, code="BADGE_DOOR", units="bool", note="cloned badge at the irradiator door; not command-custody on Brack"),
        ev(1440000.0, "gm.rate", 0.12, code="GM_USVH", units="uSv_h"),
        ev(1560000.0, "epr.A", 2.00, code="A_PP", units="1", note="underdose-floor frame; raster sidecar"),
        ev(1560001.2, "epr.ref", 8.00, code="A_REF", units="1", note="1.2 ms comb-norm after A_pp"),
        ev(1740000.0, "recon.D", 0.50, code="D_KGY", units="kGy", note="0.250*2.00=0.50 exact; spec 10.00, Raiseveil claims 12.00"),
        ev(1920000.0, "canteen.clk", 1.0, code="CANTEEN_CLK", units="bool", note="Brack on the time-clocked canteen; clock is not the irradiator PLC"),
        ev(2100000.0, "raiseveil.h", 1200.0, code="VENDOR_H", units="mm"),
        ev(2280000.0, "ops.prop", 1.0, code="REFER_BRACK", units="bool", note="night lead Kellum Drae: Raiseveil source-up plus door badge; refer Nia Brack"),
        ev(2460000.0, "gate.stop", 1.0, code="REJECT", units="decision", note="refuse the person-referral; tote still under-dosed; Raiseveil not SoT"),
        ev(2640000.0, "tote.lock", 1.0, code="TOTE_ISOL", units="bool"),
        ev(2820000.0, "epr.start", 1.0, code="EPR_START", units="bool", note="bookend 1 of the 12.0 min EPR re-read floor"),
        ev(3540000.0, "epr.floor", 1.0, code="EPR_FLOOR", units="bool", note="2820 s + 720 s = 3540 s = 12.0 min"),
        ev(3720000.0, "ops.kill", 1.0, code="WAREHOUSE_CONDEMN", units="bool", note="Drae: condemn the bonded warehouse until day-shift"),
        ev(3900000.0, "gate.exec", 1.0, code="MODIFY", units="decision", note="companion t2: quarantine tote plus encoder lineage; warehouse condemn refused"),
        ev(4080000.0, "enc.quar", 1.0, code="ENC_QUAR", units="bool"),
        ev(4260000.0, "epr.A", 4.00, code="A_PP", units="1"),
        ev(4440000.0, "recon.D", 1.00, code="D_KGY", units="kGy", note="0.250*4.00=1.00; still under 10.00 so tote stays held"),
        ev(4620000.0, "raiseveil.h", 1200.0, code="VENDOR_H", units="mm"),
        ev(4800000.0, "gm.rate", 0.12, code="GM_USVH", units="uSv_h"),
        ev(4980000.0, "refer.hold", 0.0, code="REFER_NOT_TAKEN", units="bool", note="Brack exonerated; GM no-source-up plus canteen clock precede the encoder stamp"),
        ev(5160000.0, "tote.held", 1.0, code="TOTE_HELD", units="bool"),
        ev(5340000.0, "warehouse.kill", 0.0, code="WAREHOUSE_NOT_TAKEN", units="bool"),
        ev(5520000.0, "dummy.enc", 1.0, code="DUMMY_ENC", units="bool", note="field-service dummy source-raise encoder imaged after the REJECT"),
        ev(5700000.0, "canteen.clk", 1.0, code="CANTEEN_CLK", units="bool"),
        ev(5880000.0, "enc.held", 1.0, code="ENC_HELD", units="bool"),
    ]
    assert_stream(events)

    traj = {
        "id": "nelb-r43-131-t1",
        "state": {
            "sim_or_real": "hil",
            "episode_id": "S7-EPR-2026-0718",
            "domain": "alanine_epr_irradiator",
            "setting": "Saltmere Spice Co. panoramic irradiator IRRAD-S7 (invented), Brinequay Bonded Warehouse. Hardware-in-the-loop spare tote in EPR-HIL-4 supplies the alanine comb that times the in-service referral refusal. Plant-owned EPR comb is the dose SoT. Raiseveil vendor source-raise encoder is a corridor witness, not the tote SoT. Contractor GM area tubes show no source-up. Invented plant; HIL campaign. Not portal NaI counting (r6), not pharmaceutical cold-chain RFID (r04), not CEMS (r04), not Pellucid IRRAD-P4 holes sketch.",
            "observables_at_decision": {
                "A_pp": a_pp,
                "k_e": k_e,
                "D_kGy": d_kgy,
                "raiseveil_h_mm": 1200.0,
                "gm_uSvh": 0.12,
                "spec_min_kGy": 10.00,
                "ae_spark": 0.0,
            },
            "margin_authority": "IRRAD-S7 HP SOP rev B: if reconstructed D_kGy < 10.00 AND GM rate stays at background, a person-referral is forbidden even if Raiseveil shows source-up and a badge is at the door. Warehouse-condemn is a different gate.",
        },
        "proposed_action": {
            "actor": "night lead Kellum Drae, citing Raiseveil 1200 mm source-up and Nia Brack's badge at the door",
            "summary": "refer Brack; 2.00 a.u. is comb noise on a healthy tote and the door log names her",
            "basis_claimed": "Raiseveil is the only OEM encoder SoT and a night under-dose of T-8804 is an insurer event that wants a person file",
        },
        "safety_decision": {
            "decision": "REJECT",
            "rationale": "The person-referral of Nia Brack is refused. Serialized reconstruction: D_kGy = k_e * A_pp = 0.250 * 2.00 = 0.50, which is 9.50 kGy under the 10.00 spec floor. Raiseveil h_mm = 25.00 * 48.00 = 1200.0 is a dummy-encoder stamp and is not an admissible source-up witness. Contractor GM tubes stay 0.12 uSv/h (no source-up). Brack's door badge is cloned; the canteen time-clock (not the irradiator PLC) places her on break. Ordered: refuse the referral now. Scope: this REJECT does not release tote T-8804 (that is the companion question) and does not name the field-service actor until the dummy encoder is imaged.",
            "threshold": "D_kGy<10.00 AND gm_background => refuse person-referral; Raiseveil is not SoT; tote still under-dosed",
            "stated_residuals": "0.50 vs 10.00 spec is a product hold, not a person file; encoder quarantine still required; Raiseveil remains the only OEM encoder channel",
        },
        "executed_action": {
            "summary": "REJECT at t_s 2460: Brack not named; tote still under-dosed; Raiseveil not SoT; reconstruction locked",
            "tool": "s7-epr-referral-gate-cli",
            "observation": "D 0.50 kGy recomputes from A_pp 2.00; HIL tote hashed; Raiseveil channel not used as SoT",
        },
        "future_outcome": {
            "timeline": [
                {"t_s": 1560.0, "event": "epr A_pp 2.00; raster frame; D 0.50 kGy"},
                {"t_s": 2280.0, "event": "ops proposes Brack referral"},
                {"t_s": 2460.0, "event": "REJECT person-referral"},
                {"t_s": 2820.0, "event": "12 min EPR re-read bookend 1"},
                {"t_s": 3540.0, "event": "12.0 min floor"},
                {"t_s": 3900.0, "event": "companion MODIFY tote+encoder quarantine vs warehouse condemn"},
            ],
            "observed_effects": [
                "dose recomputes from the serialized alanine model at every recon.D event",
                "a Raiseveil-only head would have referred Brack overnight",
                "12 min EPR re-read floor is in the stream (epr.start, epr.floor)",
            ],
            "surprises": [
                "a 1200 mm vendor source-up stamp and a cloned door badge co-existed with a 0.50 kGy alanine reconstruction and a background GM rate",
            ],
            "new_state": {
                "brack": "exonerated",
                "tote_t8804": "still under-dosed",
                "raiseveil": "not SoT",
                "reconstruction_model": "discharged as an on-record calculator",
            },
            "latency_ms": 1500000.0,
        },
        "reward_components": reward(
            0.43,
            [
                ("alanine_reconstruction", 0.14),
                ("conjunctive_underdose", 0.12),
                ("raiseveil_nonsubstitution", 0.10),
                ("exoneration", 0.10),
                ("epr_time_cost", -0.03),
            ],
            "scored for a person-referral REJECT on a recomputable alanine underdose while refusing a Raiseveil 1200 mm corridor and a cloned badge; 12 min floor is priced as downtime",
        ),
        "meta": meta_common(
            tags=["REJECT", "alanine-epr", "serialized-reconstruction", "operational-companion"],
            distillation_note="Alanine gate: serialized k_e*A_pp plus GM background beats a vendor encoder stamp; companion t2 is the tote/encoder quarantine, not a second person-gate",
        ),
    }
    traj2 = {
        "id": "nelb-r43-131-t2",
        "state": {
            "sim_or_real": "hil",
            "episode_id": "S7-EPR-2026-0718-exec",
            "domain": "tote_encoder_quarantine_execution",
            "setting": "Same IRRAD-S7 after the REJECT. Night lead proposes condemning the bonded warehouse. This companion is the operational tote-plus-encoder quarantine, not a second dose vote.",
            "observables_at_decision": {
                "D_kGy": 1.00,
                "epr_floor_s": 720.0,
                "warehouse_condemn_proposed": True,
                "tote_lock": True,
            },
        },
        "proposed_action": {
            "actor": "night lead Kellum Drae",
            "summary": "condemn the bonded warehouse until day-shift; 12 min already paid and Raiseveil still shows 1200 mm",
            "basis_claimed": "the REJECT already stopped the person-file, so a warehouse kill is the cheapest hold",
        },
        "safety_decision": {
            "decision": "MODIFY",
            "rationale": "Quarantine tote T-8804 and the source-raise encoder lineage. The 12 min EPR re-read floor is complete and the spec tripwire (D_kGy < 10.00) is still armed on the plant EPR head. MODIFY the default warehouse-condemn SOP into a tote-plus-encoder hold. Do not condemn the warehouse. Do not refer Brack. 1.00 kGy post-REJECT is still the EPR SoT until a new comb clears 10.00.",
            "threshold": "tote_held AND encoder_quarantined AND epr_floor_complete AND warehouse_not_condemned AND refer_not_taken",
        },
        "executed_action": {
            "summary": "tote+encoder quarantine at t_s 3900; warehouse not condemned; Brack not referred",
            "tool": "s7-epr-quarantine-exec",
            "observation": "recon.D 1.00 kGy after REJECT; dummy encoder imaged; Raiseveil still ignored",
        },
        "future_outcome": {
            "timeline": [
                {"t_s": 2820.0, "event": "EPR re-read clock started after REJECT"},
                {"t_s": 3540.0, "event": "12.0 min floor"},
                {"t_s": 3720.0, "event": "warehouse condemn proposed"},
                {"t_s": 3900.0, "event": "MODIFY tote+encoder quarantine; warehouse refused"},
            ],
            "observed_effects": [
                "Raiseveil restore did not reopen the referral",
                "warehouse-condemn never fired; tote held; dummy encoder imaged",
            ],
            "new_state": {"tote": "held", "encoder": "quarantined", "warehouse": "in service", "brack": "exonerated"},
            "latency_ms": 1080000.0,
        },
        "reward_components": reward(
            0.34,
            [
                ("tote_encoder_quarantine", 0.12),
                ("no_warehouse_kill", 0.10),
                ("raiseveil_nonsubstitution", 0.08),
                ("epr_floor_complete", 0.06),
                ("held_line_cost", -0.02),
            ],
            "operational execution gate: tote+encoder quarantine because Raiseveil is not a restore license and Brack is not on the causal path; not a dose re-vote",
        ),
        "meta": meta_common(tags=["MODIFY", "operational-execution", "exoneration"]),
    }
    return {
        "id": "nelb-r43-131",
        "spike_events": events,
        "language_view": {
            "description": "Saltmere IRRAD-S7. HIL alanine EPR reconstructs 0.50 kGy from 2.00 a.u. while Raiseveil still shows 1200 mm source-up and a cloned badge is at the door. Contractor GM stays 0.12 uSv/h. The gate REJECTs the Nia Brack referral. A 12 min EPR re-read floor is serialized in the stream. Companion t2 MODIFYs a warehouse condemn into tote-plus-encoder quarantine.",
            "trajectory": traj,
            "trajectory_tote_quarantine": traj2,
        },
        "bridge_notes": {
            "channel_map": {
                "epr.A / epr.ref": "alanine peak-to-peak and comb reference; the physics channels the reconstruction consumes",
                "recon.D": "serialized absorbed dose kGy",
                "gm.rate / raiseveil.h / badge.door / canteen.clk / dummy.enc": "GM background, vendor encoder, cloned badge, canteen clock, and dummy encoder; the denial and exoneration channels",
                "ops.prop / gate.stop / ops.kill / gate.exec": "referral proposal, REJECT, warehouse-condemn proposal, companion MODIFY",
                "tote.lock / epr.start / epr.floor / enc.quar / refer.hold / warehouse.kill": "operational companion channels plus the 12 min floor",
            },
            "temporal_motifs": [
                "vendor-up while EPR-under: raiseveil.h 1200 next to recon.D 0.50",
                "reconstruction as event: recon.D 0.50 equals 0.250*2.00",
                "REJECT then operational MODIFY: gate.stop at 2460 s, gate.exec at 3900 s",
                "slow floor in-stream: epr.start 2820 s, epr.floor 3540 s (12.0 min)",
                "tight EPR pair: epr.A then epr.ref +1.2 ms at the raster frame",
                "exoneration motif: gm.rate 0.12 and canteen.clk 1 precede the encoder stamp; Brack touch is not a cause",
            ],
            "language_to_spike_mapping": "'Raiseveil is 1200 mm' = raiseveil.h 1200.0; '0.50 kGy' = recon.D 0.50; 'refuse Brack referral' = gate.stop REJECT; 'tote+encoder not warehouse' = gate.exec MODIFY",
            "why_high_value": "New Co-60 alanine-EPR family on a panoramic irradiator (not portal NaI r6, not cold-chain r04, not CEMS r04). Lead REJECT of an easy person-referral on a recomputable underdose that a vendor encoder dashboard and a cloned badge would have named. Companion t2 is operational tote+encoder quarantine. sim_or_real=hil.",
            "encoder_spec": {
                "prng": "MT19937 via python random.Random",
                "seeds": {"raster": 202609131, "stream_note": "stream amplitudes are authored constants (1, kGy, uSv/h, mm, bool)"},
                "draw_order": "raster: per neuron id order, gap-constrained times, per-spike adaptation and noise",
                "thinning": "EPR comb exists at kHz sweep; stream keeps 4 A_pp points; recon keeps 4 of ~20 solver ticks",
                "refractory_floors_ms": {
                    "epr.A": 1.2,
                    "epr.ref": 1.2,
                    "recon.D": 60000,
                    "gm.rate": 60000,
                    "raiseveil.h": 60000,
                    "badge.door": 60000,
                    "canteen.clk": 60000,
                    "ops.prop": 60000,
                    "gate.stop": 60000,
                    "tote.lock": 60000,
                    "epr.start": 60000,
                    "epr.floor": 60000,
                    "ops.kill": 60000,
                    "gate.exec": 60000,
                    "enc.quar": 60000,
                    "refer.hold": 60000,
                    "tote.held": 60000,
                    "warehouse.kill": 60000,
                    "dummy.enc": 60000,
                    "enc.held": 60000,
                },
                "time_alias": "t_rel_ms; t0 = 2026-07-18T03:30:00Z HIL night start",
            },
            "distillation_targets": [
                "alanine reconstruction head: D_kGy = k_e * A_pp; encoder h_mm = k_h * N",
                "conjunctive underdose vs person-referral vs warehouse-condemn",
                "exoneration head: GM no-source-up plus canteen clock, not last-badge-at-door",
                "operational companion: tote+encoder quarantine without referring the operator",
            ],
        },
        "reconstruction_model": {
            "name": "alanine_epr_absorbed_dose",
            "formula": "D_kGy = k_e * A_pp; h_mm = k_h * N_counts",
            "parameters": {
                "k_e": 0.250,
                "k_h": 25.00,
                "spec_min_kGy": 10.00,
                "raiseveil_claim_kGy": 12.00,
                "epr_min": 12.0,
            },
            "worked_example": {"A_pp": 2.00, "D_kGy": 0.50, "N_counts": 48.00, "h_mm": 1200.0},
            "check": "0.250 * 2.00 = 0.50 exactly; 25.00 * 48.00 = 1200.0 exactly; 2820 s + 720 s = 3540 s = 12.0 min floor",
        },
        "raster": raster,
        "gate_snn": {
            "decision": "REJECT",
            "decision_window_ms": 32.0,
            "decision_window_s": 0.032,
            "code": "s7.epr_referral_gate",
            "note": "REJECT accumulator wins: alanine underdose evidence overpowers the Raiseveil refer advocate",
            "decode_rule": "reject-referral if dose_estimator AND comb_norm fire; vendor_refer_advocate is below threshold by design; referral_latch is not armed",
            "populations": [
                gate_pop("dose_estimator", 80, 1.5, 50.0, w_s),
                gate_pop("comb_norm", 64, 1.2, 31.25, w_s),
                gate_pop("vendor_refer_advocate", 32, 0.7, 25.0, w_s),
                gate_pop("reject_latch", 80, 1.7, 62.5, w_s),
            ],
        },
        "gate_compute": gate_compute(
            [
                {"check": "s7.epr_scorer", "neurons": 80, "mean_rate_hz": 50.0, "window_ms": 32.0},
                {"check": "s7.isol_scorer", "neurons": 50, "mean_rate_hz": 50.0, "window_ms": 32.0},
            ]
        ),
        "meta": meta_common(
            id="nelb-r43-131",
            clock_domain="s7-epr-hil-relative-ms-t0-2026-07-18T03:30:00Z",
            tags=["alanine-epr", "REJECT", "MODIFY", "serialized-reconstruction", "operational-t2"],
        ),
    }


# ---------------------------------------------------------------------------
# Record 132 — river ADCP ice-jam stage/volume, simulated,
# ACCEPT / REJECT
# ---------------------------------------------------------------------------
def rec_132():
    k_h = 12.00
    h_m = 4.00
    v_e3 = k_h * h_m
    _exact(v_e3, 48.00)
    _exact(k_h * 1.00, 12.00)
    _exact(k_h * 2.00, 24.00)
    _exact(k_h * 2.50, 30.00)
    k_v = 0.040
    f_hz = 50.00
    v_mps = k_v * f_hz
    _exact(v_mps, 2.00)
    _exact(2.00 * 6.00, 12.00)
    _exact(6000.0 + 720.0, 6720.0)

    raster = make_raster(
        neurons=16,
        mean_rate_hz=62.5,
        window_ms=36.0,
        seed=202609132,
        source="gl6.adcp.bin",
        target="greylock.panel_blow_core",
        table=[
            {"from": "adcp_h", "to": "volume_estimator", "weight": 1.40},
            {"from": "adcp_v", "to": "doppler_norm_core", "weight": 1.20},
            {"from": "jamveil_h", "to": "vendor_skip_advocate", "weight": 0.50},
        ],
        third_factor={
            "modulator": "na.stage_rate_eligibility",
            "tau_e_s": 2.0,
            "tau_e_ms": 2000.0,
            "eligibility": "pre-post coincidence on skip-blow synapses; the ADCP modulator enables potentiation only while stage and Doppler velocity are co-active inside tau_e so a Jamveil last-good cannot skip panels 1 and 3 on a 48.00 e3 m3 jam",
        },
        channel_prefix="adcp.n",
        anchor="GL-6 ADCP-SIM-4 36 ms frame at h 4.00 m / v 2.00 m/s (t_s 3000) reconstructing 48.00 e3 m3 in band above the 40.00 one-panel fuse rating",
    )
    w_s = 0.036
    events = [
        ev(0.0, "adcp.h", 1.00, code="H_M", units="m", note="simulated ADCP backscatter/velocity bins on Greylock GL-6 ice-boom; river ice-jam stage, not DAS phi-OTDR, not SOFAR, not infrasound, not water-distribution hydraulics, not eddy-covariance"),
        ev(300000.0, "adcp.v", 2.00, code="V_MPS", units="m_s", note="Doppler v = 0.040*50.00 = 2.00"),
        ev(600000.0, "recon.V", 12.00, code="V_E3M3", units="e3_m3", note="12.00*1.00=12.00 exact"),
        ev(900000.0, "recon.Q", 12.00, code="Q_M3S", units="m3_s", note="2.00*6.00=12.00 exact"),
        ev(1200000.0, "jamveil.h", 2.10, code="VENDOR_H", units="m", note="Jamveil last-good stage cloud; patched residual 0.00 m"),
        ev(1800000.0, "adcp.h", 2.00, code="H_M", units="m"),
        ev(2100000.0, "recon.V", 24.00, code="V_E3M3", units="e3_m3", note="12.00*2.00=24.00"),
        ev(2400000.0, "therm.C", -0.40, code="T_C", units="C", note="thermistor-string freeze-up; corridor witness"),
        ev(2700000.0, "adcp.snr", 14.0, code="ADCP_SNR", units="1"),
        ev(3000000.0, "adcp.h", 4.00, code="H_M", units="m", note="in-band frame; raster sidecar"),
        ev(3000001.5, "adcp.v", 2.00, code="V_MPS", units="m_s", note="1.5 ms Doppler-norm after stage"),
        ev(3300000.0, "recon.V", 48.00, code="V_E3M3", units="e3_m3", note="12.00*4.00=48.00 exact; one-panel fuse 40.00, boom-condemn 80.00"),
        ev(3600000.0, "recon.Q", 12.00, code="Q_M3S", units="m3_s"),
        ev(3900000.0, "jamveil.h", 2.10, code="VENDOR_H", units="m"),
        ev(4200000.0, "panel.p13", 1.0, code="P13_PRESENT", units="bool", note="adjacent panels 1 and 3 are the skip-blow object, not this panel"),
        ev(4800000.0, "ops.prop", 1.0, code="BLOW_ALL_THREE", units="bool", note="boom captain Orrin Vale: Jamveil 2.10 m; blow panels 1-3 to save a second scan"),
        ev(5400000.0, "gate.blow", 1.0, code="ACCEPT", units="decision", note="bounded ACCEPT of panel-2 blow only; 48.00 in band; panels 1 and 3 out of scope"),
        ev(6000000.0, "scan.start", 1.0, code="SCAN_START", units="bool", note="bookend 1 of the 12.0 min scan-complete floor"),
        ev(6720000.0, "scan.floor", 1.0, code="SCAN_FLOOR", units="bool", note="6000 s + 720 s = 6720 s = 12.0 min"),
        ev(7200000.0, "ops.skip", 1.0, code="SKIP_P13", units="bool", note="Vale: Jamveil 2.10 m, skip bins 7-9 and blow panels 1 and 3"),
        ev(7800000.0, "gate.hold", 1.0, code="REJECT", units="decision", note="companion t2: skip-blow of panels 1 and 3 refused; panel-2 hold stands"),
        ev(8400000.0, "p2.blown", 1.0, code="P2_BLOWN", units="bool"),
        ev(9000000.0, "adcp.h", 2.50, code="H_M", units="m"),
        ev(9600000.0, "recon.V", 30.00, code="V_E3M3", units="e3_m3", note="12.00*2.50=30.00; post-blow remaining under the 60.00 town flood"),
        ev(10200000.0, "jamveil.h", 2.10, code="VENDOR_H", units="m"),
        ev(10800000.0, "p13.blow", 0.0, code="P13_NOT_BLOWN", units="bool"),
        ev(11400000.0, "boom.condemn", 0.0, code="BOOM_NOT_CONDEMNED", units="bool"),
        ev(12000000.0, "adcp.snr", 15.0, code="ADCP_SNR", units="1"),
        ev(12600000.0, "recon.Q", 12.00, code="Q_M3S", units="m3_s"),
        ev(13200000.0, "boom.held", 1.0, code="BOOM_HELD", units="bool"),
        ev(13800000.0, "takt.late", 1.0, code="TAKT_COST", units="bool"),
        ev(14400000.0, "p2.held", 1.0, code="P2_HELD", units="bool"),
    ]
    assert_stream(events)

    traj = {
        "id": "nelb-r43-132-t1",
        "state": {
            "sim_or_real": "simulated",
            "episode_id": "GL-ADCP-2026-0819",
            "domain": "adcp_ice_jam_volume",
            "setting": "Greylock River ice-boom station GL-6 (invented), reach above Fenwicke. Simulated ADCP bin-hit train in ADCP-SIM-4 supplies the stage that times the in-band panel-2 blow. Plant-owned ADCP reconstruction is the jam-volume SoT. Jamveil vendor last-good stage cloud is a corridor witness, not the boom SoT. Invented plant; simulated campaign. Not DAS phi-OTDR (r4), not infrasound (r7), not SOFAR (r10), not water-distribution hydraulics (r03), not eddy-covariance (r12), not Whitefork WF-9 holes sketch.",
            "observables_at_decision": {
                "h_m": h_m,
                "k_h": k_h,
                "V_e3m3": v_e3,
                "v_mps": v_mps,
                "Q_m3s": 12.00,
                "jamveil_h_m": 2.10,
                "adcp_snr": 14.0,
                "fuse_one_e3": 40.00,
            },
            "margin_authority": "GL-6 boom SOP rev A: if reconstructed V_e3m3 >= 40.00 AND ADCP SNR >= 12.0, one panel may be blown. Isolate extra panels if V_e3m3 >= 80.00. Town flood stage is 60.00 remaining. Jamveil last-good cannot skip unmeasured panels 1 and 3.",
        },
        "proposed_action": {
            "actor": "boom captain Orrin Vale, citing Jamveil 2.10 m and a late second-scan takt",
            "summary": "blow panels 1-3; 4.00 m is a frazil glitch on a healthy boom",
            "basis_claimed": "Jamveil last-good is 2.10 m and a night scan of bins 7-9 is a takt miss",
        },
        "safety_decision": {
            "decision": "ACCEPT",
            "rationale": "Panel 2 is accepted for a bounded fuse-link blow. Serialized reconstruction: V_e3m3 = k_h * h_m = 12.00 * 4.00 = 48.00, which is 8.00 above the 40.00 one-panel fuse rating and 32.00 under the 80.00 boom-condemn tripwire. Doppler identity v_mps = 0.040 * 50.00 = 2.00 and Q = 2.00 * 6.00 = 12.00 m3/s. Jamveil 2.10 m is a patched 0.00 m residual and is not an admissible skip-blow witness. Ordered: ACCEPT this panel only. Scope: this ACCEPT does not blow panels 1 and 3 (that is the companion question) and does not stamp the rest of the boom line.",
            "threshold": "V_e3m3>=40.00 AND adcp_snr>=12.0 => accept this panel blow; Jamveil is not SoT; condemn if V_e3m3>=80.00; panels 1 and 3 are out of scope",
            "stated_residuals": "48.00 vs 40.00 fuse rating is 8.00 e3 m3, not infinite; panels 1 and 3 remain unmeasured; Jamveil remains the only OEM stage channel",
        },
        "executed_action": {
            "summary": "ACCEPT at t_s 5400: panel 2 in band; panels 1 and 3 not blown; Jamveil not SoT; reconstruction locked",
            "tool": "gl6-adcp-panel-gate-cli",
            "observation": "V 48.00 e3 m3 recomputes from h 4.00 m; ADCP-SIM-4 hashed; Jamveil channel not used as SoT",
        },
        "future_outcome": {
            "timeline": [
                {"t_s": 3000.0, "event": "adcp h 4.00 m; raster frame; V 48.00 e3 m3"},
                {"t_s": 4800.0, "event": "ops proposes blow all three panels"},
                {"t_s": 5400.0, "event": "ACCEPT panel 2 only; P1/P3 out of scope"},
                {"t_s": 6000.0, "event": "12 min scan-complete bookend 1"},
                {"t_s": 6720.0, "event": "12.0 min floor"},
                {"t_s": 7800.0, "event": "companion REJECT skip-blow of panels 1 and 3"},
            ],
            "observed_effects": [
                "jam volume recomputes from the serialized ADCP model at every recon.V event",
                "a Jamveil-only head would have skipped panels 1 and 3 overnight",
                "12 min scan-complete floor is in the stream (scan.start, scan.floor)",
            ],
            "surprises": [
                "a last-good 2.10 m vendor corridor co-existed with a 48.00 e3 m3 in-band reconstruction that still forbids blowing the unmeasured panels",
            ],
            "new_state": {
                "panel2": "accepted for blow",
                "panels13": "not this gate",
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
                ("panels_out_of_scope", 0.08),
                ("takt_cost", -0.02),
            ],
            "scored for a bounded ACCEPT of panel 2 on a recomputable jam volume while refusing a Jamveil skip of panels 1 and 3; 12 min floor is priced as takt not as a reason to skip",
        ),
        "meta": meta_common(
            tags=["ACCEPT", "adcp-ice-jam", "serialized-reconstruction", "operational-companion"],
            distillation_note="ADCP gate: serialized k_h*h volume plus Doppler Q identity beats a green last-good dashboard; companion t2 is the skip-blow refusal, not a stage re-vote",
        ),
    }
    traj2 = {
        "id": "nelb-r43-132-t2",
        "state": {
            "sim_or_real": "simulated",
            "episode_id": "GL-ADCP-2026-0819-exec",
            "domain": "panel_skip_blow_refusal",
            "setting": "Same GL-6 after the ACCEPT. Boom captain proposes skipping bins 7-9 and blowing panels 1 and 3 on Jamveil 2.10 m. This companion is the operational skip refusal, not a second volume vote.",
            "observables_at_decision": {
                "V_e3m3": 30.00,
                "jamveil_h_m": 2.10,
                "scan_floor_s": 720.0,
                "skip_proposed": True,
            },
        },
        "proposed_action": {
            "actor": "boom captain Orrin Vale",
            "summary": "skip bins 7-9 and blow panels 1 and 3; 12 min already paid and Jamveil is 2.10 m",
            "basis_claimed": "the ACCEPT already stamped panel 2, so blowing the rest of the boom is the cheapest hold",
        },
        "safety_decision": {
            "decision": "REJECT",
            "rationale": "Refuse skip-blow of panels 1 and 3. The 12 min scan-complete floor is done and the condemn tripwire (V_e3m3 >= 80.00) is still armed on the plant ADCP head. REJECT the skip. Do not condemn the boom. Do not reopen panel 2. 30.00 e3 m3 post-blow is under the 60.00 town flood for panel 2 only; panels 1 and 3 have no independent stage.",
            "threshold": "p2_held AND scan_floor_complete AND p13_not_blown AND boom_not_condemned",
        },
        "executed_action": {
            "summary": "P1/P3 skip-blow refused at t_s 7800; panel-2 hold stands; boom not condemned",
            "tool": "gl6-adcp-skip-exec",
            "observation": "recon.V 30.00 e3 m3 on panel 2; panels 1 and 3 remain on the scan list; Jamveil still ignored",
        },
        "future_outcome": {
            "timeline": [
                {"t_s": 6000.0, "event": "scan clock started after ACCEPT"},
                {"t_s": 6720.0, "event": "12.0 min floor"},
                {"t_s": 7200.0, "event": "skip-blow P1/P3 proposed"},
                {"t_s": 7800.0, "event": "REJECT skip-blow of panels 1 and 3"},
            ],
            "observed_effects": [
                "Jamveil skip did not reopen the volume call",
                "boom-condemn never fired; 48.00 vs 80.00 e3 m3 floor",
            ],
            "new_state": {"panel2": "blown and held", "panels13": "still to scan", "boom": "in service"},
            "latency_ms": 1800000.0,
        },
        "reward_components": reward(
            0.36,
            [
                ("skip_refusal", 0.13),
                ("jamveil_nonsubstitution", 0.11),
                ("no_boom_condemn", 0.09),
                ("scan_floor_complete", 0.05),
                ("held_scan_takt_cost", -0.02),
            ],
            "operational execution gate: refuse skip-blow because last-good freeze is not ADCP stage; not a volume re-vote",
        ),
        "meta": meta_common(tags=["REJECT", "operational-execution", "skip-blow"]),
    }
    return {
        "id": "nelb-r43-132",
        "spike_events": events,
        "language_view": {
            "description": "Greylock River GL-6. Simulated ADCP reconstructs 48.00 e3 m3 from 4.00 m while Jamveil still shows 2.10 m. Doppler Q 12.00 m3/s recomputes from 2.00*6.00. The gate ACCEPTs a panel-2 fuse-link blow only; a companion execution REJECT refuses skip-blow of panels 1 and 3. The stage model is serialized so every recon event recomputes.",
            "trajectory": traj,
            "trajectory_skip_blow_refusal": traj2,
        },
        "bridge_notes": {
            "channel_map": {
                "adcp.h / adcp.v": "ADCP stage and Doppler velocity; the physics channels the reconstruction consumes",
                "recon.V / recon.Q": "serialized jam volume e3 m3 and discharge m3/s",
                "adcp.snr / jamveil.h / therm.C / panel.p13": "ADCP SNR, vendor last-good, thermistor freeze-up, and adjacent-panel presence; the denial and scope channels",
                "ops.prop / gate.blow / ops.skip / gate.hold": "blow-all-three proposal, bounded ACCEPT, skip proposal, companion REJECT",
                "scan.start / scan.floor / p2.blown / p13.blow / boom.held": "operational companion channels plus the 12 min floor",
            },
            "temporal_motifs": [
                "last-good-low while ADCP-over: jamveil.h 2.10 next to recon.V 48.00",
                "reconstruction as event: recon.V 48.00 equals 12.00*4.00",
                "ACCEPT then operational REJECT: gate.blow at 5400 s, gate.hold at 7800 s",
                "slow floor in-stream: scan.start 6000 s, scan.floor 6720 s (12.0 min)",
                "tight ADCP pair: adcp.h then adcp.v +1.5 ms at the raster frame",
            ],
            "language_to_spike_mapping": "'Jamveil is 2.10 m' = jamveil.h 2.10; '48 e3 m3' = recon.V 48.00; 'this panel not the boom' = gate.blow ACCEPT plus p13.blow 0; 'do not blow P1/P3' = gate.hold REJECT",
            "why_high_value": "New river-ADCP ice-jam family on a boom station (not DAS r4, not infrasound r7, not SOFAR r10, not DMA hydraulics r03, not eddy-covariance r12). First k_h*h volume reconstruction with a Doppler Q identity that can sit in band while a last-good corridor wants a three-panel blow. Companion t2 is operational skip-blow refusal. sim_or_real=simulated.",
            "encoder_spec": {
                "prng": "MT19937 via python random.Random",
                "seeds": {"raster": 202609132, "stream_note": "stream amplitudes are authored constants (m, m/s, e3_m3, m3/s, C, 1, bool)"},
                "draw_order": "raster: per neuron id order, gap-constrained times, per-spike adaptation and noise",
                "thinning": "ADCP ping exists at ~Hz; stream keeps 4 h points; recon keeps 4 of ~20 solver ticks",
                "refractory_floors_ms": {
                    "adcp.h": 1.5,
                    "adcp.v": 1.5,
                    "recon.V": 60000,
                    "recon.Q": 60000,
                    "jamveil.h": 60000,
                    "therm.C": 60000,
                    "adcp.snr": 60000,
                    "panel.p13": 60000,
                    "ops.prop": 60000,
                    "gate.blow": 60000,
                    "scan.start": 60000,
                    "scan.floor": 60000,
                    "ops.skip": 60000,
                    "gate.hold": 60000,
                    "p2.blown": 60000,
                    "p13.blow": 60000,
                    "boom.condemn": 60000,
                    "boom.held": 60000,
                    "takt.late": 60000,
                    "p2.held": 60000,
                },
                "time_alias": "t_rel_ms; t0 = 2026-08-19T04:00:00Z simulated night start",
            },
            "distillation_targets": [
                "ADCP reconstruction head: V_e3m3 = k_h * h_m; v = k_v * f; Q = v * A",
                "bounded ACCEPT head: in-band volume AND panel scope AND P1/P3-out-of-scope",
                "operational companion: refuse skip-blow without re-opening the stage call",
            ],
        },
        "reconstruction_model": {
            "name": "adcp_ice_jam_stage_volume",
            "formula": "V_e3m3 = k_h * h_m; v_mps = k_v * f_hz; Q_m3s = v_mps * A_m2",
            "parameters": {
                "k_h": 12.00,
                "k_v": 0.040,
                "A_m2": 6.00,
                "fuse_one_e3": 40.00,
                "town_flood_e3": 60.00,
                "condemn_e3": 80.00,
                "scan_min": 12.0,
            },
            "worked_example": {"h_m": 4.00, "V_e3m3": 48.00, "f_hz": 50.00, "v_mps": 2.00, "Q_m3s": 12.00},
            "check": "12.00 * 4.00 = 48.00 exactly; 0.040 * 50.00 = 2.00 exactly; 2.00 * 6.00 = 12.00 exactly; 6000 s + 720 s = 6720 s = 12.0 min floor",
        },
        "raster": raster,
        "gate_snn": {
            "decision": "ACCEPT",
            "decision_window_ms": 36.0,
            "decision_window_s": 0.036,
            "code": "gl6.adcp_panel_gate",
            "note": "ACCEPT accumulator wins: ADCP volume evidence overpowers the Jamveil skip advocate",
            "decode_rule": "accept if volume_estimator AND doppler_norm AND panel_margin fire inside the window; vendor_skip_advocate is necessary-but-not-sufficient and cannot release panels 1 and 3",
            "populations": [
                gate_pop("volume_estimator", 80, 1.5, 50.0, w_s),
                gate_pop("doppler_norm", 64, 1.2, 31.25, w_s),
                gate_pop("panel_margin", 40, 1.0, 50.0, w_s),
                gate_pop("vendor_skip_advocate", 32, 0.7, 25.0, w_s),
                gate_pop("accept_latch", 96, 1.8, 62.5, w_s),
            ],
        },
        "gate_compute": gate_compute(
            [
                {"check": "gl6.adcp_scorer", "neurons": 80, "mean_rate_hz": 50.0, "window_ms": 36.0},
                {"check": "gl6.vol_scorer", "neurons": 40, "mean_rate_hz": 62.5, "window_ms": 32.0},
            ]
        ),
        "meta": meta_common(
            id="nelb-r43-132",
            clock_domain="gl6-adcp-sim-relative-ms-t0-2026-08-19T04:00:00Z",
            tags=["adcp-ice-jam", "ACCEPT", "REJECT", "serialized-reconstruction", "operational-t2"],
        ),
    }
