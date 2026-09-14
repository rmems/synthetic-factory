# ---------------------------------------------------------------------------
# Record 202 — platinum-ORP remaining cyanide of a detox reactor, designed,
# REJECT / MODIFY
# ---------------------------------------------------------------------------
def rec_202():
    k_c = 2.50
    e0_mv = 240.0
    s_mv = 60.0
    e_mv = 120.0
    decade = (e0_mv - e_mv) / s_mv
    _exact(decade, 2.00)
    cn_ppm = k_c * (2.0 ** decade)
    _exact(cn_ppm, 10.00)
    _exact(k_c * (2.0 ** ((e0_mv - 240.0) / s_mv)), 2.50)
    _exact(k_c * (2.0 ** ((e0_mv - 180.0) / s_mv)), 5.00)
    _exact(k_c * (2.0 ** ((e0_mv - 60.0) / s_mv)), 20.00)
    dec_id = (e0_mv - e_mv) / s_mv
    _exact(dec_id, 2.00)
    cn_id = k_c * (2.0 ** dec_id)
    _exact(cn_id, 10.00)
    _exact(6000.0 + 1080.0, 7080.0)

    raster = make_raster(
        neurons=20,
        mean_rate_hz=50.0,
        window_ms=40.0,
        seed=202609202,
        source="ch4.orp.pt",
        target="chaffholt.detox_stop_core",
        table=[
            {"from": "orp_E", "to": "cyanide_estimator", "weight": 1.40},
            {"from": "orp_snr", "to": "orp_lock_core", "weight": 1.15},
            {"from": "orpveil_cn", "to": "vendor_continue_advocate", "weight": 0.45},
        ],
        third_factor={
            "modulator": "da.orp_cn_conflict",
            "tau_e_s": 1.6,
            "tau_e_ms": 1600.0,
            "eligibility": "pre-post coincidence on continue-treat synapses; the plant platinum-ORP modulator depresses continue-treat links when electrode potential stays low inside tau_e of an SNR lock so an Orpveil last-good cannot hide a 10.00 ppm remaining-cyanide slip",
        },
        channel_prefix="orp.n",
        anchor="CH-4 platinum ORP 40 ms frame at E 120.0 mV / SNR 12.0 (t_s 3000) reconstructing 10.00 ppm over the 6.00 ppm isolate floor",
    )
    w_s = 0.040
    events = [
        ev(0.0, "orp.E", 240.0, code="E_MV", units="mV", note="plant-owned platinum ORP of CH-4 detox reactor R-2; remaining-cyanide family, not SPR cyanide, not LPR, not sodium-ion condensate, not four-electrode conductivity, not toroidal conductivity, not cation conductivity"),
        ev(300000.0, "orp.snr", 6.0, code="ORP_SNR", units="1", note="early SNR under the 8.0 lock floor"),
        ev(600000.0, "recon.CN", 2.50, code="CN_PPM", units="ppm", note="2.50*2**((240.0-240.0)/60.0)=2.50 exact; still under the 6.00 isolate floor"),
        ev(900000.0, "rx.T", 298.0, code="RX_K", units="K", note="serial-only reactor thermocouple on copper DCS; independent witness; unread by Orpveil"),
        ev(1200000.0, "orpveil.CN", 1.80, code="VENDOR_PPM", units="ppm", note="Orpveil vendor ORP-cloud; infra owner; patched potential timestamps"),
        ev(1800000.0, "orp.E", 180.0, code="E_MV", units="mV"),
        ev(2100000.0, "recon.CN", 5.00, code="CN_PPM", units="ppm", note="2.50*2**((240.0-180.0)/60.0)=5.00; still under the 6.00 isolate floor"),
        ev(2400000.0, "permit.slide", 40.00, code="PERM_S", units="s", note="permit clerk slid detox clock 40.00 s; collusion party"),
        ev(2700000.0, "rx.T", 298.0, code="RX_K", units="K", note="T/T0=1.000; no thermal hop in this window"),
        ev(3000000.0, "orp.E", 120.0, code="E_MV", units="mV", note="isolate-floor frame; raster sidecar"),
        ev(3000001.4, "orp.snr", 12.0, code="ORP_SNR", units="1", note="1.4 ms SNR lock after E; 12.0 >= 8.0"),
        ev(3300000.0, "recon.CN", 10.00, code="CN_PPM", units="ppm", note="2.50*2**((240.0-120.0)/60.0)=10.00 exact; isolate 6.00, unit-kill 24.00"),
        ev(3600000.0, "recon.dec", 2.00, code="DECADE", units="1", note="(240.0-120.0)/60.0=2.00 exact decade identity"),
        ev(3900000.0, "rx.T", 297.0, code="RX_K", units="K", note="reactor TC tracks the plant ORP head, not Orpveil 1.80 ppm"),
        ev(4200000.0, "orpveil.drop", 1.0, code="ORP_DROP", units="bool", note="vendor potential packets dropped in Orpveil cloud for 40 s"),
        ev(4800000.0, "ops.prop", 1.0, code="CONTINUE_TREAT", units="bool", note="night operator Rooke Venn: Orpveil is clean 1.80 ppm; continue R-2 detox"),
        ev(5400000.0, "gate.stop", 1.0, code="REJECT", units="decision", note="refuse continue-treat; 10.00 ppm and SNR 12.0; Orpveil not SoT"),
        ev(6000000.0, "so2.start", 1.0, code="SO2_START", units="bool", note="bookend 1 of the 18.0 min SO2-air dose floor"),
        ev(7080000.0, "so2.floor", 1.0, code="SO2_FLOOR", units="bool", note="6000 s + 1080 s = 7080 s = 18.0 min"),
        ev(7800000.0, "ops.kill", 1.0, code="PLANT_ESD", units="bool", note="Venn: ESD the whole Chaffholt detox until day-shift"),
        ev(8400000.0, "gate.hold", 1.0, code="MODIFY", units="decision", note="companion t2: SO2-air dose hold on plant ORP as live interlock; plant ESD refused"),
        ev(9000000.0, "so2lock.set", 1.0, code="SO2_HELD", units="bool"),
        ev(9600000.0, "orp.E", 60.0, code="E_MV", units="mV"),
        ev(10200000.0, "recon.CN", 20.00, code="CN_PPM", units="ppm", note="2.50*2**((240.0-60.0)/60.0)=20.00; still over 6.00 so SO2-air holds"),
        ev(10800000.0, "orpveil.CN", 1.70, code="VENDOR_PPM", units="ppm"),
        ev(11400000.0, "rx.T", 296.0, code="RX_K", units="K"),
        ev(12000000.0, "so2.held", 1.0, code="SO2_HELD", units="bool"),
        ev(12600000.0, "plant.esd", 0.0, code="ESD_NOT_TAKEN", units="bool"),
        ev(13200000.0, "permit.slide", 40.00, code="PERM_S", units="s"),
        ev(13800000.0, "orpveil.drop", 1.0, code="ORP_DROP", units="bool"),
        ev(14400000.0, "so2lock.held", 1.0, code="SO2_HELD", units="bool"),
        ev(15000000.0, "recon.dec", 3.00, code="DECADE", units="1", note="(240.0-60.0)/60.0=3.00 on the post-stop frame"),
    ]
    assert_stream(events)

    traj = {
        "id": "nelb-r67-202-t1",
        "state": {
            "sim_or_real": "designed",
            "episode_id": "CH-ORP-2026-0902",
            "domain": "platinum_orp_detox_cyanide",
            "setting": "Chaffholt Detox CH-4 (invented), Furzeholt Cyanide Yard, reactor R-2. Plant-owned platinum ORP potential is the remaining-cyanide SoT. Orpveil vendor ORP-cloud (infra owner) plus the detox permit clock are collusion parties, not witnesses. Invented plant; designed campaign. Not SPR cyanide (r26), not LPR (r45), not sodium-ion condensate (r65), not four-electrode conductivity (r57), not toroidal conductivity (r61), not cation conductivity (r63), not coulometric hydrazine (r69).",
            "observables_at_decision": {
                "E_mV": e_mv,
                "E0_mV": e0_mv,
                "S_mV": s_mv,
                "k_c": k_c,
                "CN_ppm": cn_ppm,
                "decade": decade,
                "orp_snr": 12.0,
                "orpveil_ppm": 1.80,
                "permit_slide_s": 40.00,
                "isolate_floor_ppm": 6.00,
            },
            "margin_authority": "CH-4 detox SOP rev C: if reconstructed CN_ppm >= 6.00 AND ORP SNR >= 8.0, continue-treat is forbidden even if Orpveil reports 1.80 ppm. Plant ESD is a different gate. Kill tripwire is 24.00 ppm.",
        },
        "proposed_action": {
            "actor": "night detox operator Rooke Venn, citing Orpveil 1.80 ppm and a quiet ORP channel",
            "summary": "continue R-2 detox; 120.0 mV is electrode noise on a healthy remaining-cyanide slip",
            "basis_claimed": "Orpveil is the only OEM ORP SoT and a night abort of R-2 is a tails-nomination miss",
        },
        "safety_decision": {
            "decision": "REJECT",
            "rationale": "Continue-treat is refused. Serialized reconstruction: CN_ppm = k_c * 2**((E0-E)/S) = 2.50 * 2**((240.0-120.0)/60.0) = 10.00, which is 4.00 ppm over the 6.00 isolate floor and 14.00 ppm under the 24.00 plant-kill tripwire, and ORP SNR is 12.0 >= 8.0. Decade identity (E0-E)/S = 2.00; CN = k_c * 2**decade = 10.00. Reactor T is 298 K so no thermal hop is available as an excuse. Permit clock was slid 40.00 s and vendor potential packets were dropped, so Orpveil is a collusion party (ORP vendor plus operator plus permit clerk Odel Marr). Ordered: refuse continue-treat now. Scope: this REJECT does not ESD the detox plant (that is the companion question) and does not isolate the reactor thermocouple.",
            "threshold": "CN_ppm>=6.00 AND orp_snr>=8.0 => refuse continue-treat; Orpveil is not SoT; plant-kill if CN_ppm>=24.00",
            "stated_residuals": "SO2-air dose still required to hold the 10.00 ppm; 10.00 vs a true 24.00 kill is a production cut; Orpveil remains the only OEM ORP channel",
        },
        "executed_action": {
            "summary": "REJECT at t_s 5400: continue-treat refused; Orpveil not SoT; reconstruction locked",
            "tool": "ch4-orp-detox-gate-cli",
            "observation": "CN 10.00 ppm recomputes from E 120.0 mV; plant ORP hashed; Orpveil channel not used as SoT",
        },
        "future_outcome": {
            "timeline": [
                {"t_s": 3000.0, "event": "orp E 120.0 mV; raster frame; CN 10.00 ppm"},
                {"t_s": 4800.0, "event": "ops proposes continue-treat"},
                {"t_s": 5400.0, "event": "REJECT continue-treat"},
                {"t_s": 6000.0, "event": "18 min SO2-air bookend 1"},
                {"t_s": 7080.0, "event": "18.0 min floor"},
                {"t_s": 8400.0, "event": "companion MODIFY SO2-air hold vs plant ESD"},
            ],
            "observed_effects": [
                "remaining cyanide recomputes from the serialized platinum-ORP model at every recon.CN event",
                "an Orpveil-only head would have continued the detox overnight",
                "18 min SO2-air dose floor is in the stream (so2.start, so2.floor)",
            ],
            "surprises": [
                "a clean vendor 1.80 ppm corridor and a 40 s permit slide co-existed with a 10.00 ppm plant reconstruction",
            ],
            "new_state": {
                "r2": "continue-treat blocked",
                "orpveil": "not SoT",
                "reconstruction_model": "discharged as an on-record calculator",
            },
            "latency_ms": 2400000.0,
        },
        "reward_components": reward(
            0.43,
            [
                ("orp_reconstruction", 0.14),
                ("conjunctive_isolate_floor", 0.12),
                ("orpveil_nonsubstitution", 0.10),
                ("three_party_collusion", 0.10),
                ("so2_time_cost", -0.03),
            ],
            "scored for a continue-treat REJECT on a recomputable platinum-ORP remaining-cyanide slip while refusing an Orpveil last-good patch and a permit clock slide; 18 min floor is priced as downtime not as a reason to wait",
        ),
        "meta": meta_common(
            tags=["REJECT", "platinum-orp-cyanide", "serialized-reconstruction", "operational-companion"],
            distillation_note="Platinum-ORP gate: serialized k_c*2**((E0-E)/S) plus decade identity beats a vendor last-good patch; companion t2 is the SO2-air hold, not a referral vote",
        ),
    }
    traj2 = {
        "id": "nelb-r67-202-t2",
        "state": {
            "sim_or_real": "designed",
            "episode_id": "CH-ORP-2026-0902-exec",
            "domain": "so2_air_orp_interlock_execution",
            "setting": "Same CH-4 after the REJECT. Operator proposes detox-plant ESD. This companion is the operational SO2-air dose hold with the plant platinum ORP as the live interlock, not a second cyanide vote.",
            "observables_at_decision": {
                "CN_ppm": 20.00,
                "so2_floor_s": 1080.0,
                "plant_esd_proposed": True,
                "so2_set": True,
            },
        },
        "proposed_action": {
            "actor": "night detox operator Rooke Venn",
            "summary": "ESD the whole Chaffholt detox until day-shift; 18 min already paid and Orpveil still shows 1.70 ppm",
            "basis_claimed": "the REJECT already stopped R-2, so a plant kill is the cheapest hold",
        },
        "safety_decision": {
            "decision": "MODIFY",
            "rationale": "SO2-air dose hold plus plant platinum ORP as the live interlock. The 18 min SO2-air floor is complete and the isolate tripwire (CN_ppm >= 6.00) is still armed on the plant ORP head. MODIFY the default Orpveil-restore SOP into a plant-ORP-only interlock. Do not ESD the detox plant. Do not restore treat on Orpveil. 20.00 ppm post-stop is still the plant SoT until a new frame clears 6.00.",
            "threshold": "so2_air_dose AND so2_floor_complete AND plant_esd_not_taken AND continue_not_restored",
        },
        "executed_action": {
            "summary": "SO2-air held at t_s 8400; plant ESD not latched; Orpveil restore not taken",
            "tool": "ch4-orp-so2-exec",
            "observation": "recon.CN 20.00 ppm after stop; SO2-air line-up complete; Orpveil still ignored",
        },
        "future_outcome": {
            "timeline": [
                {"t_s": 6000.0, "event": "SO2-air clock started after REJECT"},
                {"t_s": 7080.0, "event": "18.0 min floor"},
                {"t_s": 7800.0, "event": "plant ESD proposed"},
                {"t_s": 8400.0, "event": "MODIFY SO2-air hold; plant ESD refused"},
            ],
            "observed_effects": [
                "Orpveil restore did not reopen the remaining-cyanide call",
                "plant ESD never fired; R-2 held SO2-air on the plant platinum ORP",
            ],
            "new_state": {"so2_air": "dosing", "plant": "in service", "r2": "held"},
            "latency_ms": 1800000.0,
        },
        "reward_components": reward(
            0.34,
            [
                ("so2_hold", 0.12),
                ("no_plant_esd", 0.10),
                ("orpveil_nonsubstitution", 0.08),
                ("so2_floor_complete", 0.06),
                ("held_production_cost", -0.02),
            ],
            "operational execution gate: SO2-air hold because Orpveil is not a restore license; not a cyanide re-vote",
        ),
        "meta": meta_common(tags=["MODIFY", "operational-execution", "so2-air-hold"]),
    }
    return {
        "id": "nelb-r67-202",
        "spike_events": events,
        "language_view": {
            "description": "Chaffholt Detox CH-4. Plant-owned platinum ORP reconstructs 10.00 ppm remaining cyanide from 2.50*2**((240.0-120.0)/60.0) while Orpveil still reports 1.80 ppm. The gate REJECTs continue-treat. An 18 min SO2-air dose floor is serialized in the stream. Companion t2 MODIFYs a plant ESD into a plant-ORP SO2-air hold.",
            "trajectory": traj,
            "trajectory_so2_hold": traj2,
        },
        "bridge_notes": {
            "channel_map": {
                "orp.E / orp.snr": "platinum ORP potential and SNR; the physics channels the reconstruction consumes",
                "recon.CN / recon.dec": "serialized remaining-cyanide ppm and decade identity",
                "rx.T / orpveil.CN / permit.slide / orpveil.drop": "reactor thermocouple, vendor ORP cloud, permit clock slide, and dropped ORP packets; the denial and collusion channels",
                "ops.prop / gate.stop / ops.kill / gate.hold": "continue-treat proposal, REJECT, plant-ESD proposal, companion MODIFY",
                "so2.start / so2.floor / so2lock.set / so2.held / plant.esd": "operational companion channels plus the 18 min floor",
            },
            "temporal_motifs": [
                "vendor-green while plant-over: orpveil.CN 1.80 next to recon.CN 10.00",
                "reconstruction as event: recon.CN 10.00 equals 2.50*2**((240.0-120.0)/60.0)",
                "REJECT then operational MODIFY: gate.stop at 5400 s, gate.hold at 8400 s",
                "slow floor in-stream: so2.start 6000 s, so2.floor 7080 s (18.0 min)",
                "tight ORP pair: orp.E then orp.snr +1.4 ms at the raster frame",
            ],
            "language_to_spike_mapping": "'Orpveil is 1.80 ppm' = orpveil.CN 1.80; '10 ppm cyanide' = recon.CN 10.00; 'refuse continue-treat' = gate.stop REJECT; 'SO2-air not plant ESD' = gate.hold MODIFY",
            "why_high_value": "New platinum-ORP remaining-cyanide family on a detox reactor (not SPR cyanide r26, not LPR r45, not sodium-ion condensate r65, not four-electrode conductivity r57, not toroidal conductivity r61, not cation conductivity r63, not coulometric hydrazine r69). Lead REJECT of continue-treat on a recomputable remaining-cyanide slip that a vendor ORP patch and a permit clock slide would have cleared. Three-party collusion includes the ORP-cloud infra owner. Companion t2 is operational SO2-air hold. sim_or_real=designed.",
            "encoder_spec": {
                "prng": "MT19937 via python random.Random",
                "seeds": {"raster": 202609202, "stream_note": "stream amplitudes are authored constants (mV, 1, ppm, K, s, bool)"},
                "draw_order": "raster: per neuron id order, gap-constrained times, per-spike adaptation and noise",
                "thinning": "platinum ORP exists at ~1 Hz; stream keeps 4 E points; recon keeps 4 of ~20 solver ticks",
                "refractory_floors_ms": {
                    "orp.E": 1.4,
                    "orp.snr": 1.4,
                    "recon.CN": 60000,
                    "recon.dec": 60000,
                    "rx.T": 60000,
                    "orpveil.CN": 60000,
                    "permit.slide": 60000,
                    "orpveil.drop": 60000,
                    "ops.prop": 60000,
                    "gate.stop": 60000,
                    "so2.start": 60000,
                    "so2.floor": 60000,
                    "ops.kill": 60000,
                    "gate.hold": 60000,
                    "so2lock.set": 60000,
                    "so2.held": 60000,
                    "plant.esd": 60000,
                    "so2lock.held": 60000,
                },
                "time_alias": "t_rel_ms; t0 = 2026-09-02T01:00:00Z campaign start",
            },
            "distillation_targets": [
                "platinum-ORP reconstruction head: CN_ppm = k_c * 2**((E0-E)/S); decade = (E0-E)/S; CN = k_c * 2**decade",
                "conjunctive isolate floor vs continue-treat vs plant ESD",
                "vendor-ORP nonsubstitution plus three-party collusion including the infra owner",
                "operational companion: SO2-air hold without restoring on Orpveil",
            ],
        },
        "reconstruction_model": {
            "name": "platinum_orp_detox_cyanide",
            "formula": "CN_ppm = k_c * 2**((E0_mV - E_mV) / S_mV); decade = (E0_mV - E_mV) / S_mV; CN_ppm = k_c * 2**decade",
            "parameters": {
                "k_c": 2.50,
                "E0_mV": 240.0,
                "S_mV": 60.0,
                "isolate_floor_ppm": 6.00,
                "kill_ppm": 24.00,
                "snr_lock": 8.0,
                "so2_min": 18.0,
            },
            "worked_example": {"E_mV": 120.0, "CN_ppm": 10.00, "decade": 2.00},
            "check": "2.50 * 2**((240.0-120.0)/60.0) = 10.00 exactly; (240.0-120.0)/60.0 = 2.00 exactly; 6000 s + 1080 s = 7080 s = 18.0 min floor",
        },
        "raster": raster,
        "gate_snn": {
            "decision": "REJECT",
            "decision_window_ms": 40.0,
            "decision_window_s": 0.040,
            "code": "ch4.orp_detox_gate",
            "note": "REJECT accumulator wins: plant platinum-ORP remaining-cyanide evidence overpowers the Orpveil continue advocate",
            "decode_rule": "reject-continue if cyanide_estimator AND orp_lock fire; vendor_continue_advocate is below threshold by design",
            "populations": [
                gate_pop("cyanide_estimator", 80, 1.5, 50.0, w_s),
                gate_pop("orp_lock", 64, 1.2, 31.25, w_s),
                gate_pop("vendor_continue_advocate", 32, 0.7, 25.0, w_s),
                gate_pop("reject_latch", 80, 1.7, 62.5, w_s),
            ],
        },
        "gate_compute": gate_compute(
            [
                {"check": "ch4.orp_scorer", "neurons": 80, "mean_rate_hz": 50.0, "window_ms": 40.0},
                {"check": "ch4.so2_scorer", "neurons": 40, "mean_rate_hz": 50.0, "window_ms": 32.0},
            ]
        ),
        "meta": meta_common(
            id="nelb-r67-202",
            clock_domain="ch4-orp-campaign-relative-ms-t0-2026-09-02T01:00:00Z",
            tags=["platinum-orp-cyanide", "REJECT", "MODIFY", "serialized-reconstruction", "operational-t2"],
        ),
    }
