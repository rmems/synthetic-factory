# ---------------------------------------------------------------------------
# Record 202 — coulometric Karl Fischer remaining water of a transformer
# conservator, designed, REJECT / MODIFY
# ---------------------------------------------------------------------------
def rec_202():
    k_f = 2.50
    q_c = 8.00
    m_g = 2.00
    w_ppm = k_f * q_c / m_g
    _exact(w_ppm, 10.00)
    _exact(k_f * 2.00 / m_g, 2.50)
    _exact(k_f * 4.00 / m_g, 5.00)
    _exact(k_f * 12.00 / m_g, 15.00)
    q_id = w_ppm * m_g / k_f
    _exact(q_id, 8.00)
    i_ma = 2.00
    t_tit_s = 4000.0
    q_i = i_ma * t_tit_s / 1000.0
    _exact(q_i, 8.00)
    _exact(6000.0 + 1080.0, 7080.0)

    raster = make_raster(
        neurons=20,
        mean_rate_hz=50.0,
        window_ms=40.0,
        seed=202609202,
        source="wh4.kf.coulomb",
        target="wetherholt.conservator_stop_core",
        table=[
            {"from": "kf_Q", "to": "water_estimator", "weight": 1.40},
            {"from": "kf_snr", "to": "kf_lock_core", "weight": 1.15},
            {"from": "karlveil_w", "to": "vendor_continue_advocate", "weight": 0.45},
        ],
        third_factor={
            "modulator": "da.kf_water_conflict",
            "tau_e_s": 1.6,
            "tau_e_ms": 1600.0,
            "eligibility": "pre-post coincidence on continue-energize synapses; the plant coulometric-KF modulator depresses continue-energize links when titration charge stays high inside tau_e of an SNR lock so a Karlveil last-good cannot hide a 10.00 ppm remaining-water slip",
        },
        channel_prefix="kf.n",
        anchor="WH-4 coulometric KF 40 ms frame at Q 8.00 C / SNR 12.0 (t_s 3000) reconstructing 10.00 ppm over the 6.00 ppm isolate floor",
    )
    w_s = 0.040
    events = [
        ev(0.0, "kf.Q", 2.00, code="Q_C", units="C", note="plant-owned coulometric Karl Fischer titration charge on WH-4 transformer conservator C-2; remaining-water family, not Al2O3 moisture, not chilled-mirror dew-point, not MW-cavity moisture, not THz-TDS, not QCM-D, not CRNS"),
        ev(300000.0, "kf.snr", 6.0, code="KF_SNR", units="1", note="early SNR under the 8.0 lock floor"),
        ev(600000.0, "recon.w", 2.50, code="W_PPM", units="ppm", note="2.50*2.00/2.00=2.50 exact; still under the 6.00 isolate floor"),
        ev(900000.0, "oil.T", 313.0, code="OIL_K", units="K", note="serial-only conservator thermocouple on copper DCS; independent witness; unread by Karlveil"),
        ev(1200000.0, "karlveil.w", 1.80, code="VENDOR_PPM", units="ppm", note="Karlveil vendor KF-cloud; infra owner; patched titration timestamps"),
        ev(1800000.0, "kf.Q", 4.00, code="Q_C", units="C"),
        ev(2100000.0, "recon.w", 5.00, code="W_PPM", units="ppm", note="2.50*4.00/2.00=5.00; still under the 6.00 isolate floor"),
        ev(2400000.0, "permit.slide", 40.00, code="PERM_S", units="s", note="permit clerk slid conservator clock 40.00 s; collusion party"),
        ev(2700000.0, "oil.T", 313.0, code="OIL_K", units="K", note="T/T0=1.000; no thermal hop in this window"),
        ev(3000000.0, "kf.Q", 8.00, code="Q_C", units="C", note="isolate-floor frame; raster sidecar"),
        ev(3000001.4, "kf.snr", 12.0, code="KF_SNR", units="1", note="1.4 ms SNR lock after Q; 12.0 >= 8.0"),
        ev(3300000.0, "recon.w", 10.00, code="W_PPM", units="ppm", note="2.50*8.00/2.00=10.00 exact; isolate 6.00, unit-kill 24.00"),
        ev(3600000.0, "recon.Qid", 8.00, code="Q_ID_C", units="C", note="10.00*2.00/2.50=8.00 exact charge identity"),
        ev(3900000.0, "oil.T", 312.0, code="OIL_K", units="K", note="oil TC tracks the plant KF head, not Karlveil 1.80 ppm"),
        ev(4200000.0, "karlveil.drop", 1.0, code="KF_DROP", units="bool", note="vendor titration packets dropped in Karlveil cloud for 40 s"),
        ev(4800000.0, "ops.prop", 1.0, code="CONTINUE_ENERGIZE", units="bool", note="night operator Rooke Venn: Karlveil is clean 1.80 ppm; continue C-2 conservator"),
        ev(5400000.0, "gate.stop", 1.0, code="REJECT", units="decision", note="refuse continue-energize; 10.00 ppm and SNR 12.0; Karlveil not SoT"),
        ev(6000000.0, "dry.start", 1.0, code="DRY_START", units="bool", note="bookend 1 of the 18.0 min vacuum dry-out floor"),
        ev(7080000.0, "dry.floor", 1.0, code="DRY_FLOOR", units="bool", note="6000 s + 1080 s = 7080 s = 18.0 min"),
        ev(7800000.0, "ops.kill", 1.0, code="BANK_ESD", units="bool", note="Venn: ESD the whole Wetherholt 132 kV bank until day-shift"),
        ev(8400000.0, "gate.hold", 1.0, code="MODIFY", units="decision", note="companion t2: vacuum dry-out hold on plant KF as live interlock; bank ESD refused"),
        ev(9000000.0, "drylock.set", 1.0, code="DRY_HELD", units="bool"),
        ev(9600000.0, "kf.Q", 12.00, code="Q_C", units="C"),
        ev(10200000.0, "recon.w", 15.00, code="W_PPM", units="ppm", note="2.50*12.00/2.00=15.00; still over 6.00 so dry-out holds"),
        ev(10800000.0, "karlveil.w", 1.70, code="VENDOR_PPM", units="ppm"),
        ev(11400000.0, "oil.T", 311.0, code="OIL_K", units="K"),
        ev(12000000.0, "dry.held", 1.0, code="DRY_HELD", units="bool"),
        ev(12600000.0, "bank.esd", 0.0, code="ESD_NOT_TAKEN", units="bool"),
        ev(13200000.0, "permit.slide", 40.00, code="PERM_S", units="s"),
        ev(13800000.0, "karlveil.drop", 1.0, code="KF_DROP", units="bool"),
        ev(14400000.0, "drylock.held", 1.0, code="DRY_HELD", units="bool"),
        ev(15000000.0, "recon.Qid", 12.00, code="Q_ID_C", units="C", note="15.00*2.00/2.50=12.00 on the post-stop frame"),
    ]
    assert_stream(events)

    traj = {
        "id": "nelb-r67-202-t1",
        "state": {
            "sim_or_real": "designed",
            "episode_id": "WH-KF-2026-0902",
            "domain": "coulometric_kf_transformer_water",
            "setting": "Wetherholt Transformer WH-4 (invented), Furzeholt Grid, conservator C-2. Plant-owned coulometric Karl Fischer titration charge is the remaining-water SoT. Karlveil vendor KF-cloud (infra owner) plus the conservator permit clock are collusion parties, not witnesses. Invented plant; designed campaign. Not Al2O3 moisture (r59), not chilled-mirror dew-point (r51), not MW-cavity moisture (r26), not THz-TDS (r20/r21), not QCM-D (r14), not CRNS (r28), not sodium-ion condensate (r65).",
            "observables_at_decision": {
                "Q_C": q_c,
                "m_g": m_g,
                "k_f": k_f,
                "w_ppm": w_ppm,
                "Q_id_C": q_id,
                "I_mA": i_ma,
                "kf_snr": 12.0,
                "karlveil_ppm": 1.80,
                "permit_slide_s": 40.00,
                "isolate_floor_ppm": 6.00,
            },
            "margin_authority": "WH-4 conservator SOP rev C: if reconstructed w_ppm >= 6.00 AND KF SNR >= 8.0, continue-energize is forbidden even if Karlveil reports 1.80 ppm. Bank ESD is a different gate. Kill tripwire is 24.00 ppm.",
        },
        "proposed_action": {
            "actor": "night conservator operator Rooke Venn, citing Karlveil 1.80 ppm and a quiet titration channel",
            "summary": "continue C-2 conservator; 8.00 C is reagent noise on a healthy remaining-water slip",
            "basis_claimed": "Karlveil is the only OEM KF SoT and a night abort of C-2 is a 132 kV nomination miss",
        },
        "safety_decision": {
            "decision": "REJECT",
            "rationale": "Continue-energize is refused. Serialized reconstruction: w_ppm = k_f * Q / m = 2.50 * 8.00 / 2.00 = 10.00, which is 4.00 ppm over the 6.00 isolate floor and 14.00 ppm under the 24.00 bank-kill tripwire, and KF SNR is 12.0 >= 8.0. Charge identity Q = w * m / k_f = 10.00 * 2.00 / 2.50 = 8.00; I*t identity 2.00 mA * 4000 s / 1000 = 8.00 C. Oil T is 313 K so no thermal hop is available as an excuse. Permit clock was slid 40.00 s and vendor titration packets were dropped, so Karlveil is a collusion party (KF vendor plus operator plus permit clerk Odel Marr). Ordered: refuse continue-energize now. Scope: this REJECT does not ESD the 132 kV bank (that is the companion question) and does not isolate the oil thermocouple.",
            "threshold": "w_ppm>=6.00 AND kf_snr>=8.0 => refuse continue-energize; Karlveil is not SoT; bank-kill if w_ppm>=24.00",
            "stated_residuals": "vacuum dry-out still required to hold the 10.00 ppm; 10.00 vs a true 24.00 kill is a production cut; Karlveil remains the only OEM KF channel",
        },
        "executed_action": {
            "summary": "REJECT at t_s 5400: continue-energize refused; Karlveil not SoT; reconstruction locked",
            "tool": "wh4-kf-conservator-gate-cli",
            "observation": "w 10.00 ppm recomputes from Q 8.00 C and m 2.00 g; plant KF hashed; Karlveil channel not used as SoT",
        },
        "future_outcome": {
            "timeline": [
                {"t_s": 3000.0, "event": "kf Q 8.00 C; raster frame; w 10.00 ppm"},
                {"t_s": 4800.0, "event": "ops proposes continue-energize"},
                {"t_s": 5400.0, "event": "REJECT continue-energize"},
                {"t_s": 6000.0, "event": "18 min dry-out bookend 1"},
                {"t_s": 7080.0, "event": "18.0 min floor"},
                {"t_s": 8400.0, "event": "companion MODIFY dry-out hold vs bank ESD"},
            ],
            "observed_effects": [
                "remaining water recomputes from the serialized coulometric-KF model at every recon.w event",
                "a Karlveil-only head would have continued the conservator overnight",
                "18 min vacuum dry-out floor is in the stream (dry.start, dry.floor)",
            ],
            "surprises": [
                "a clean vendor 1.80 ppm corridor and a 40 s permit slide co-existed with a 10.00 ppm plant reconstruction",
            ],
            "new_state": {
                "c2": "continue-energize blocked",
                "karlveil": "not SoT",
                "reconstruction_model": "discharged as an on-record calculator",
            },
            "latency_ms": 2400000.0,
        },
        "reward_components": reward(
            0.43,
            [
                ("kf_reconstruction", 0.14),
                ("conjunctive_isolate_floor", 0.12),
                ("karlveil_nonsubstitution", 0.10),
                ("three_party_collusion", 0.10),
                ("dryout_time_cost", -0.03),
            ],
            "scored for a continue-energize REJECT on a recomputable coulometric-KF remaining-water slip while refusing a Karlveil last-good patch and a permit clock slide; 18 min floor is priced as downtime not as a reason to wait",
        ),
        "meta": meta_common(
            tags=["REJECT", "coulometric-kf-water", "serialized-reconstruction", "operational-companion"],
            distillation_note="Coulometric-KF gate: serialized k_f*Q/m plus charge identity beats a vendor last-good patch; companion t2 is the vacuum dry-out hold, not a referral vote",
        ),
    }
    traj2 = {
        "id": "nelb-r67-202-t2",
        "state": {
            "sim_or_real": "designed",
            "episode_id": "WH-KF-2026-0902-exec",
            "domain": "vacuum_dryout_kf_interlock_execution",
            "setting": "Same WH-4 after the REJECT. Operator proposes 132 kV-bank ESD. This companion is the operational vacuum dry-out hold with the plant coulometric KF as the live interlock, not a second water vote.",
            "observables_at_decision": {
                "w_ppm": 15.00,
                "dry_floor_s": 1080.0,
                "bank_esd_proposed": True,
                "dry_set": True,
            },
        },
        "proposed_action": {
            "actor": "night conservator operator Rooke Venn",
            "summary": "ESD the whole Wetherholt 132 kV bank until day-shift; 18 min already paid and Karlveil still shows 1.70 ppm",
            "basis_claimed": "the REJECT already stopped C-2, so a bank kill is the cheapest hold",
        },
        "safety_decision": {
            "decision": "MODIFY",
            "rationale": "Vacuum dry-out hold plus plant coulometric KF as the live interlock. The 18 min dry-out floor is complete and the isolate tripwire (w_ppm >= 6.00) is still armed on the plant KF head. MODIFY the default Karlveil-restore SOP into a plant-KF-only interlock. Do not ESD the 132 kV bank. Do not restore energize on Karlveil. 15.00 ppm post-stop is still the plant SoT until a new frame clears 6.00.",
            "threshold": "vacuum_dryout AND dry_floor_complete AND bank_esd_not_taken AND continue_not_restored",
        },
        "executed_action": {
            "summary": "dry-out held at t_s 8400; bank ESD not latched; Karlveil restore not taken",
            "tool": "wh4-kf-dry-exec",
            "observation": "recon.w 15.00 ppm after stop; dry-out line-up complete; Karlveil still ignored",
        },
        "future_outcome": {
            "timeline": [
                {"t_s": 6000.0, "event": "dry-out clock started after REJECT"},
                {"t_s": 7080.0, "event": "18.0 min floor"},
                {"t_s": 7800.0, "event": "bank ESD proposed"},
                {"t_s": 8400.0, "event": "MODIFY dry-out hold; bank ESD refused"},
            ],
            "observed_effects": [
                "Karlveil restore did not reopen the remaining-water call",
                "bank ESD never fired; C-2 held vacuum dry-out on the plant KF",
            ],
            "new_state": {"dryout": "running", "bank": "in service", "c2": "held"},
            "latency_ms": 1800000.0,
        },
        "reward_components": reward(
            0.34,
            [
                ("dryout_hold", 0.12),
                ("no_bank_esd", 0.10),
                ("karlveil_nonsubstitution", 0.08),
                ("dry_floor_complete", 0.06),
                ("held_production_cost", -0.02),
            ],
            "operational execution gate: vacuum dry-out hold because Karlveil is not a restore license; not a water re-vote",
        ),
        "meta": meta_common(tags=["MODIFY", "operational-execution", "dryout-hold"]),
    }
    return {
        "id": "nelb-r67-202",
        "spike_events": events,
        "language_view": {
            "description": "Wetherholt Transformer WH-4. Plant-owned coulometric Karl Fischer reconstructs 10.00 ppm remaining water from 2.50*8.00/2.00 while Karlveil still reports 1.80 ppm. The gate REJECTs continue-energize. An 18 min vacuum dry-out floor is serialized in the stream. Companion t2 MODIFYs a 132 kV-bank ESD into a plant-KF dry-out hold.",
            "trajectory": traj,
            "trajectory_dryout_hold": traj2,
        },
        "bridge_notes": {
            "channel_map": {
                "kf.Q / kf.snr": "titration charge and SNR; the physics channels the reconstruction consumes",
                "recon.w / recon.Qid": "serialized remaining-water ppm and charge identity",
                "oil.T / karlveil.w / permit.slide / karlveil.drop": "oil thermocouple, vendor KF cloud, permit clock slide, and dropped KF packets; the denial and collusion channels",
                "ops.prop / gate.stop / ops.kill / gate.hold": "continue-energize proposal, REJECT, bank-ESD proposal, companion MODIFY",
                "dry.start / dry.floor / drylock.set / dry.held / bank.esd": "operational companion channels plus the 18 min floor",
            },
            "temporal_motifs": [
                "vendor-green while plant-over: karlveil.w 1.80 next to recon.w 10.00",
                "reconstruction as event: recon.w 10.00 equals 2.50*8.00/2.00",
                "REJECT then operational MODIFY: gate.stop at 5400 s, gate.hold at 8400 s",
                "slow floor in-stream: dry.start 6000 s, dry.floor 7080 s (18.0 min)",
                "tight KF pair: kf.Q then kf.snr +1.4 ms at the raster frame",
            ],
            "language_to_spike_mapping": "'Karlveil is 1.80 ppm' = karlveil.w 1.80; '10 ppm water' = recon.w 10.00; 'refuse continue-energize' = gate.stop REJECT; 'dry-out not bank ESD' = gate.hold MODIFY",
            "why_high_value": "New coulometric Karl Fischer remaining-water family on a transformer conservator (not Al2O3 moisture r59, not chilled-mirror r51, not MW-cavity r26, not THz-TDS r20/r21, not QCM-D r14, not CRNS r28, not sodium-ion condensate r65). Lead REJECT of continue-energize on a recomputable remaining-water slip that a vendor KF patch and a permit clock slide would have cleared. Three-party collusion includes the KF-cloud infra owner. Companion t2 is operational vacuum dry-out hold. sim_or_real=designed.",
            "encoder_spec": {
                "prng": "MT19937 via python random.Random",
                "seeds": {"raster": 202609202, "stream_note": "stream amplitudes are authored constants (C, 1, ppm, K, s, bool)"},
                "draw_order": "raster: per neuron id order, gap-constrained times, per-spike adaptation and noise",
                "thinning": "coulometric KF exists at ~1 Hz titration ticks; stream keeps 4 Q points; recon keeps 4 of ~20 solver ticks",
                "refractory_floors_ms": {
                    "kf.Q": 1.4,
                    "kf.snr": 1.4,
                    "recon.w": 60000,
                    "recon.Qid": 60000,
                    "oil.T": 60000,
                    "karlveil.w": 60000,
                    "permit.slide": 60000,
                    "karlveil.drop": 60000,
                    "ops.prop": 60000,
                    "gate.stop": 60000,
                    "dry.start": 60000,
                    "dry.floor": 60000,
                    "ops.kill": 60000,
                    "gate.hold": 60000,
                    "drylock.set": 60000,
                    "dry.held": 60000,
                    "bank.esd": 60000,
                    "drylock.held": 60000,
                },
                "time_alias": "t_rel_ms; t0 = 2026-09-02T01:00:00Z campaign start",
            },
            "distillation_targets": [
                "coulometric-KF reconstruction head: w_ppm = k_f * Q_C / m_g; Q = w * m / k_f; Q = I_mA * t_s / 1000",
                "conjunctive isolate floor vs continue-energize vs bank ESD",
                "vendor-KF nonsubstitution plus three-party collusion including the infra owner",
                "operational companion: vacuum dry-out hold without restoring on Karlveil",
            ],
        },
        "reconstruction_model": {
            "name": "coulometric_kf_transformer_water",
            "formula": "w_ppm = k_f * Q_C / m_g; Q_C = w_ppm * m_g / k_f; Q_C = I_mA * t_s / 1000",
            "parameters": {
                "k_f": 2.50,
                "m_g": 2.00,
                "I_mA": 2.00,
                "isolate_floor_ppm": 6.00,
                "kill_ppm": 24.00,
                "snr_lock": 8.0,
                "dry_min": 18.0,
            },
            "worked_example": {"Q_C": 8.00, "w_ppm": 10.00, "Q_id_C": 8.00, "I_mA": 2.00},
            "check": "2.50 * 8.00 / 2.00 = 10.00 exactly; 10.00 * 2.00 / 2.50 = 8.00 exactly; 2.00 mA * 4000 s / 1000 = 8.00 C; 6000 s + 1080 s = 7080 s = 18.0 min floor",
        },
        "raster": raster,
        "gate_snn": {
            "decision": "REJECT",
            "decision_window_ms": 40.0,
            "decision_window_s": 0.040,
            "code": "wh4.kf_conservator_gate",
            "note": "REJECT accumulator wins: plant coulometric-KF remaining-water evidence overpowers the Karlveil continue advocate",
            "decode_rule": "reject-continue if water_estimator AND kf_lock fire; vendor_continue_advocate is below threshold by design",
            "populations": [
                gate_pop("water_estimator", 80, 1.5, 50.0, w_s),
                gate_pop("kf_lock", 64, 1.2, 31.25, w_s),
                gate_pop("vendor_continue_advocate", 32, 0.7, 25.0, w_s),
                gate_pop("reject_latch", 80, 1.7, 62.5, w_s),
            ],
        },
        "gate_compute": gate_compute(
            [
                {"check": "wh4.kf_scorer", "neurons": 80, "mean_rate_hz": 50.0, "window_ms": 40.0},
                {"check": "wh4.dry_scorer", "neurons": 40, "mean_rate_hz": 50.0, "window_ms": 32.0},
            ]
        ),
        "meta": meta_common(
            id="nelb-r67-202",
            clock_domain="wh4-kf-campaign-relative-ms-t0-2026-09-02T01:00:00Z",
            tags=["coulometric-kf-water", "REJECT", "MODIFY", "serialized-reconstruction", "operational-t2"],
        ),
    }
