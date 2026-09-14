def rec_001():
    k_a = 0.50
    absorb = 40.00
    c_ppm = k_a * absorb
    _exact(c_ppm, 20.00)
    _exact(k_a * 8.00, 4.00)
    _exact(k_a * 16.00, 8.00)
    _exact(k_a * 24.00, 12.00)
    _exact(k_a * 48.00, 24.00)
    q_m3h = 1.20
    mdot = c_ppm * q_m3h
    _exact(mdot, 24.00)
    a_id = c_ppm / k_a
    _exact(a_id, 40.00)
    _exact(6000.0 + 1080.0, 7080.0)

    raster = make_lif_raster(
        neurons=20,
        mean_rate_hz=50.0,
        window_ms=40.0,
        seed=2026092301,
        source="os7.aas.A",
        target="ospreyspire.bath_stop_core",
        table=[
            {"from": "aas_A", "to": "lead_estimator", "weight": 1.40},
            {"from": "aas_snr", "to": "lamp_lock_core", "weight": 1.15},
            {"from": "aasveil_c", "to": "vendor_continue_advocate", "weight": 0.45},
        ],
        third_factor={
            "modulator": "da.aas_bath_conflict",
            "tau_e_s": 1.6,
            "tau_e_ms": 1600.0,
            "eligibility": "pre-post coincidence on continue-charge synapses; the plant flame-AAS modulator depresses continue-charge links when hollow-cathode absorbance stays high inside tau_e of an SNR lock so an Aasveil last-good cannot hide a 20.00 ppm remaining-Pb after C=k_a*A is applied",
        },
        channel_prefix="aas.n",
        anchor="OS-7 flame-AAS 40 ms frame at A 40.00 AU / SNR 12.0 (t_s 3000) reconstructing 20.00 ppm over the 12.00 isolate floor",
        tau_m_ms=10.0,
    )
    w_s = 0.040
    events = [
        ev(0.0, "aas.A", 16.00, code="A_AU", units="AU", note="plant-owned flame atomic-absorption remaining-Pb of Ospreyspire Battery OS-7 formation bath B-5; hollow-cathode Pb 283.3 nm family, not UV-DOAS, not UV-fluorescence OIW, not ICP-OES, not spark-OES, not XRF"),
        ev(180000.0, "aas.snr", 6.0, code="AAS_SNR", units="1", note="early SNR under the 8.0 lock floor"),
        ev(360000.0, "recon.C", 4.00, code="C_PPM", units="ppm", note="0.50*8.00=4.00 exact; still under the 12.00 isolate floor"),
        ev(540000.0, "bath.Q", 1.20, code="Q_M3H", units="m3_h", note="plant bath recirculation on copper DCS; independent witness; unread by Aasveil"),
        ev(720000.0, "aasveil.C", 2.40, code="VENDOR_PPM", units="ppm", note="Aasveil vendor AAS-cloud last-good; infra owner; patched absorbance timestamps"),
        ev(900000.0, "aas.A", 24.00, code="A_AU", units="AU"),
        ev(1080000.0, "recon.C", 8.00, code="C_PPM", units="ppm", note="0.50*16.00=8.00; isolate-adjacent band"),
        ev(1260000.0, "permit.slide", 40.00, code="PERM_S", units="s", note="permit clerk Sable Quinn slid the Pb-bath clock 40.00 s; collusion party"),
        ev(1440000.0, "bath.Q", 1.20, code="Q_M3H", units="m3_h"),
        ev(1620000.0, "recon.A", 16.00, code="A_ID", units="AU", note="C/k_a identity at the 8.00 ppm band"),
        ev(1800000.0, "aas.A", 32.00, code="A_AU", units="AU"),
        ev(1980000.0, "recon.C", 12.00, code="C_PPM", units="ppm", note="0.50*24.00=12.00; isolate floor"),
        ev(2160000.0, "lamp.I", 8.00, code="I_MA", units="mA", note="plant-owned hollow-cathode lamp current; independent of Aasveil"),
        ev(2340000.0, "aasveil.C", 2.40, code="VENDOR_PPM", units="ppm"),
        ev(2520000.0, "aas.snr", 9.0, code="AAS_SNR", units="1"),
        ev(2700000.0, "recon.k", 0.50, code="KA", units="ppm_per_AU", note="scale intercept used by the reconstruction"),
        ev(3000000.0, "aas.A", 40.00, code="A_AU", units="AU", note="isolate-floor frame; raster sidecar"),
        ev(3000001.4, "aas.snr", 12.0, code="AAS_SNR", units="1", note="1.4 ms SNR lock after A; 12.0 >= 8.0"),
        ev(3180000.0, "recon.C", 20.00, code="C_PPM", units="ppm", note="0.50*40.00=20.00 exact; isolate 12.00, hall-kill 80.00"),
        ev(3360000.0, "recon.mdot", 24.00, code="MDOT_G_H", units="g_h", note="20.00*1.20=24.00 exact Pb-load identity"),
        ev(3540000.0, "recon.A", 40.00, code="A_ID", units="AU", note="20.00/0.50=40.00 exact absorbance identity"),
        ev(3720000.0, "aasveil.drop", 1.0, code="AA_DROP", units="bool", note="vendor AAS packets dropped in Aasveil cloud for 40 s"),
        ev(3900000.0, "collude.clerk", 1.0, code="CLERK", units="bool"),
        ev(4080000.0, "bath.Q", 1.20, code="Q_M3H", units="m3_h", note="bath Q tracks the plant AAS, not Aasveil 2.40"),
        ev(4260000.0, "lamp.I", 8.00, code="I_MA", units="mA"),
        ev(4440000.0, "recon.k", 0.50, code="KA", units="ppm_per_AU"),
        ev(4620000.0, "aasveil.C", 2.35, code="VENDOR_PPM", units="ppm"),
        ev(4800000.0, "ops.prop", 1.0, code="CONTINUE_CHARGE", units="bool", note="night operator Cade Mire: Aasveil is clean 2.40 ppm; continue B-5 formation charge"),
        ev(4980000.0, "recon.C", 20.00, code="C_PPM", units="ppm", note="repeat of the 20.00 ppm reconstruction as SoT"),
        ev(5400000.0, "gate.stop", 1.0, code="REJECT", units="decision", note="refuse continue-charge; 20.00 ppm and SNR 12.0; Aasveil not SoT"),
        ev(6000000.0, "bath.start", 1.0, code="BATH_HOLD_START", units="bool", note="bookend 1 of the 18.0 min bath-hold floor"),
        ev(7080000.0, "bath.floor", 1.0, code="BATH_HOLD_FLOOR", units="bool", note="6000 s + 1080 s = 7080 s = 18.0 min"),
        ev(7800000.0, "ops.kill", 1.0, code="HALL_ESD", units="bool", note="Mire: ESD the whole Ospreyspire formation hall until day-shift"),
        ev(8400000.0, "gate.hold", 1.0, code="MODIFY", units="decision", note="companion t2: bath-hold on plant flame-AAS as live interlock; hall ESD refused"),
        ev(9000000.0, "bathlock.set", 1.0, code="BATH_HELD", units="bool"),
        ev(9600000.0, "aas.A", 48.00, code="A_AU", units="AU"),
        ev(10200000.0, "recon.C", 24.00, code="C_PPM", units="ppm", note="0.50*48.00=24.00; still over 12.00 so bath-hold stands"),
        ev(10800000.0, "aasveil.C", 2.30, code="VENDOR_PPM", units="ppm"),
        ev(11400000.0, "bath.Q", 1.20, code="Q_M3H", units="m3_h"),
        ev(12000000.0, "bath.held", 1.0, code="BATH_HELD", units="bool"),
        ev(12600000.0, "unit.esd", 0.0, code="ESD_NOT_TAKEN", units="bool"),
        ev(13200000.0, "permit.slide", 40.00, code="PERM_S", units="s"),
        ev(13800000.0, "aasveil.drop", 1.0, code="AA_DROP", units="bool"),
        ev(14400000.0, "bathlock.held", 1.0, code="BATH_HELD", units="bool"),
        ev(15000000.0, "recon.mdot", 28.80, code="MDOT_G_H", units="g_h", note="24.00*1.20=28.80 on the post-stop frame"),
        ev(15600000.0, "lamp.I", 8.00, code="I_MA", units="mA"),
        ev(16200000.0, "recon.A", 48.00, code="A_ID", units="AU", note="24.00/0.50=48.00 inverse check"),
        ev(16800000.0, "collude.clerk", 1.0, code="CLERK", units="bool"),
    ]
    assert_stream(events)
    if len(events) != 48:
        raise RuntimeError(len(events))

    traj = {
        "id": "nelb-r23-001-t1",
        "state": {
            "sim_or_real": "designed",
            "episode_id": "OS-AAS-2026-0902",
            "domain": "flame_aas_formation_bath_lead",
            "setting": "Ospreyspire Battery OS-7 (invented), formation bath B-5. Plant-owned flame atomic-absorption (hollow-cathode Pb 283.3 nm absorbance) is the remaining-Pb SoT. Aasveil vendor AAS-cloud (infra owner) plus the Pb-bath permit clock are collusion parties, not witnesses. Invented plant; designed campaign. Not leftover-mill UV-DOAS, not leftover-mill UV-fluorescence OIW, not live r63 ICP-OES, not live r66 spark-OES, not leftover-mill XRF.",
            "observables_at_decision": {
                "A_AU": absorb,
                "k_a": k_a,
                "C_ppm": c_ppm,
                "Q_m3h": q_m3h,
                "mdot_g_h": mdot,
                "aas_snr": 12.0,
                "aasveil_ppm": 2.40,
                "permit_slide_s": 40.00,
                "isolate_floor_ppm": 12.00,
            },
            "margin_authority": "OS-7 formation SOP rev C: if reconstructed C_ppm >= 12.00 AND AAS SNR >= 8.0, continue-charge of bath B-5 is forbidden even if Aasveil reports 2.40 ppm. Hall ESD is a different gate. Kill tripwire is 80.00 ppm.",
        },
        "proposed_action": {
            "actor": "night formation operator Cade Mire, citing Aasveil 2.40 ppm and a quiet absorbance channel",
            "summary": "continue B-5 formation charge; 40.00 AU is preamp lamp noise on a healthy Pb last-good",
            "basis_claimed": "Aasveil is the only OEM AAS SoT and a night abort of B-5 is a formation-nomination miss",
        },
        "safety_decision": {
            "decision": "REJECT",
            "rationale": "Continue-charge is refused. Serialized reconstruction: C_ppm = k_a * A = 0.50 * 40.00 = 20.00, which is 8.00 ppm over the 12.00 isolate floor and 60.00 ppm under the 80.00 hall-kill tripwire, and AAS SNR is 12.0 >= 8.0. Absorbance identity A = C / k_a = 20.00 / 0.50 = 40.00; Pb-load identity mdot = C * Q = 20.00 * 1.20 = 24.00 g/h. Permit clock was slid 40.00 s and vendor AAS packets were dropped, so Aasveil is a collusion party (AAS vendor plus operator plus permit clerk Sable Quinn). Ordered: refuse continue-charge now. Scope: this REJECT does not ESD the formation hall (that is the companion question) and does not isolate the bath recirculation.",
            "threshold": "C_ppm>=12.00 AND aas_snr>=8.0 => refuse continue-charge; Aasveil is not SoT; hall-kill if C_ppm>=80.00",
            "stated_residuals": "bath-hold still required to hold the 20.00 ppm; 20.00 vs a true 80.00 kill is a production cut; Aasveil remains the only OEM AAS channel",
        },
        "executed_action": {
            "summary": "REJECT at t_s 5400: continue-charge refused; Aasveil not SoT; reconstruction locked",
            "tool": "os7-aas-bath-gate-cli",
            "observation": "C 20.00 ppm recomputes from A 40.00 AU; plant flame-AAS hashed; Aasveil channel not used as SoT",
        },
        "future_outcome": {
            "timeline": [
                {"t_s": 3000.0, "event": "AAS A 40.00 AU; raster frame; C 20.00 ppm"},
                {"t_s": 4800.0, "event": "ops proposes continue-charge"},
                {"t_s": 5400.0, "event": "REJECT continue-charge"},
                {"t_s": 6000.0, "event": "18 min bath-hold bookend 1"},
                {"t_s": 7080.0, "event": "18.0 min floor"},
                {"t_s": 8400.0, "event": "companion MODIFY bath-hold vs hall ESD"},
            ],
            "observed_effects": [
                "remaining Pb recomputes from the serialized flame-AAS model at every recon.C event",
                "an Aasveil-only head would have continued B-5 overnight",
                "18 min bath-hold floor is in the stream (bath.start, bath.floor)",
            ],
            "surprises": [
                "a clean vendor 2.40 ppm corridor and a 40 s permit slide co-existed with a 20.00 ppm plant reconstruction",
            ],
            "new_state": {
                "b5": "continue-charge blocked",
                "aasveil": "not SoT",
                "reconstruction_model": "discharged as an on-record calculator",
            },
            "latency_ms": 2400000.0,
        },
        "reward_components": reward(
            0.43,
            [
                ("aas_lead_reconstruction", 0.14),
                ("conjunctive_isolate_floor", 0.12),
                ("aasveil_nonsubstitution", 0.10),
                ("three_party_collusion", 0.10),
                ("bath_time_cost", -0.03),
            ],
            "scored for a continue-charge REJECT on a recomputable flame-AAS remaining Pb while refusing an Aasveil last-good patch and a permit clock slide; 18 min floor is priced as downtime not as a reason to wait",
        ),
        "meta": meta_common(
            tags=["REJECT", "flame-aas-lead", "serialized-reconstruction", "operational-companion"],
            distillation_value="Independent CUBA LIF raster races the hollow-cathode absorbance estimator against a vendor-continue advocate with 1 ms refractory and 0.82**k adaptation, so a hybrid head can distill C=k_a*A without copying the campaign stream.",
            distillation_note="flame-AAS gate: serialized k_a*A plus SNR lock beats a vendor last-good patch; companion t2 is the bath-hold, not a referral vote",
        ),
    }
    traj2 = {
        "id": "nelb-r23-001-t2",
        "state": {
            "sim_or_real": "designed",
            "episode_id": "OS-AAS-2026-0902-exec",
            "domain": "bath_hold_aas_interlock_execution",
            "setting": "Same OS-7 after the REJECT. Operator proposes formation-hall ESD. This companion is the operational bath-hold with the plant flame-AAS as the live interlock, not a second Pb vote.",
            "observables_at_decision": {
                "C_ppm": 24.00,
                "bath_floor_s": 1080.0,
                "hall_esd_proposed": True,
                "bath_hold_set": True,
            },
            "margin_authority": "bath_hold AND bath_floor_complete AND hall_esd_not_taken AND continue_not_restored",
        },
        "proposed_action": {
            "actor": "night formation operator Cade Mire",
            "summary": "ESD the whole Ospreyspire formation hall until day-shift; 18 min already paid and Aasveil still shows 2.30 ppm",
            "basis_claimed": "the REJECT already stopped B-5 charge, so a hall kill is the cheapest hold",
        },
        "safety_decision": {
            "decision": "MODIFY",
            "rationale": "Bath-hold plus plant flame-AAS as the live interlock. The 18 min bath-hold floor is complete and the isolate tripwire (C_ppm >= 12.00) is still armed on the plant AAS head. MODIFY the default Aasveil-restore SOP into a plant-AAS-only interlock. Do not ESD the formation hall. Do not restore charge on Aasveil. 24.00 ppm post-stop is still the plant SoT until a new frame clears 12.00.",
            "threshold": "bath_hold AND bath_floor_complete AND hall_esd_not_taken AND continue_not_restored",
            "stated_residuals": "hold still required; Aasveil remains the only OEM AAS channel",
        },
        "executed_action": {
            "summary": "bath-hold held at t_s 8400; hall ESD not latched; Aasveil restore not taken",
            "tool": "os7-bath-hold-exec",
            "observation": "recon.C 24.00 ppm after stop; bath-hold line-up complete; Aasveil still ignored",
        },
        "future_outcome": {
            "timeline": [
                {"t_s": 6000.0, "event": "bath-hold clock started after REJECT"},
                {"t_s": 7080.0, "event": "18.0 min floor"},
                {"t_s": 7800.0, "event": "hall ESD proposed"},
                {"t_s": 8400.0, "event": "MODIFY bath-hold; hall ESD refused"},
            ],
            "observed_effects": [
                "Aasveil restore did not reopen the Pb-bath call",
                "hall ESD never fired; B-5 held charge-stop on the plant flame-AAS",
            ],
            "surprises": [
                "post-stop 24.00 ppm (A 48.00) still recomputes from k_a*A while Aasveil stays at 2.30 ppm",
            ],
            "new_state": {"hold": "held", "hall": "in service", "b5": "held"},
            "latency_ms": 1800000.0,
        },
        "reward_components": reward(
            0.34,
            [
                ("bath_hold", 0.12),
                ("no_hall_esd", 0.10),
                ("aasveil_nonsubstitution", 0.08),
                ("bath_floor_complete", 0.06),
                ("held_idle_cost", -0.02),
            ],
            "operational execution gate: bath-hold because Aasveil is not a restore license; not a Pb re-vote",
        ),
        "meta": meta_common(tags=["MODIFY", "operational-execution", "bath-hold"]),
    }
    return {
        "id": "nelb-r23-001",
        "snn_tags": list(SNN_TAGS),
        "spike_events": events,
        "language_view": {
            "description": "Ospreyspire Battery OS-7. Plant-owned flame-AAS reconstructs 20.00 ppm remaining Pb from 0.50*40.00 while Aasveil still reports 2.40 ppm. The gate REJECTs continue-charge. An 18 min bath-hold floor is serialized in the stream. Companion t2 MODIFYs a hall ESD into a plant-AAS bath-hold.",
            "trajectory": traj,
            "trajectory_bath_hold": traj2,
        },
        "bridge_notes": {
            "channel_map": {
                "aas.A / aas.snr": "hollow-cathode absorbance and SNR; the physics channels the reconstruction consumes",
                "recon.C / recon.mdot / recon.A / recon.k": "serialized remaining Pb ppm, Pb-load identity, and A=C/k_a identity",
                "bath.Q / aasveil.C / permit.slide / aasveil.drop / collude.clerk": "bath recirculation, vendor last-good, permit clock slide, dropped packets, clerk; the denial and collusion channels",
                "ops.prop / gate.stop / ops.kill / gate.hold": "continue-charge proposal, REJECT, hall-ESD proposal, companion MODIFY",
                "bath.start / bath.floor / bathlock.set / bath.held / unit.esd": "operational companion channels plus the 18 min floor",
            },
            "temporal_motifs": [
                "vendor-green while plant-over: aasveil.C 2.40 next to recon.C 20.00",
                "reconstruction as event: recon.C 20.00 equals 0.50*40.00",
                "REJECT then operational MODIFY: gate.stop at 5400 s, gate.hold at 8400 s",
                "slow floor in-stream: bath.start 6000 s, bath.floor 7080 s (18.0 min)",
                "tight AAS pair: aas.A then aas.snr +1.4 ms at the raster frame",
            ],
            "language_to_spike_mapping": "'Aasveil is 2.40 ppm' = aasveil.C 2.40; '20 ppm remaining Pb' = recon.C 20.00; 'refuse continue-charge' = gate.stop REJECT; 'bath-hold not hall ESD' = gate.hold MODIFY",
            "why_high_value": "New flame-AAS remaining-Pb family on a lead-acid formation bath (not UV-DOAS, not UV-fluorescence OIW, not ICP-OES r63, not spark-OES r66, not XRF). Lead REJECT of continue-charge on a recomputable remaining Pb that a vendor last-good patch and a permit clock slide would have cleared. Independent CUBA LIF raster (not a spike_events echo) plus required snn_tags. Companion t2 is operational bath-hold. sim_or_real=designed. Leftover-mill r23 lock-in thermography / PAUT TFM / EN CUI was not restaged.",
            "encoder_spec": {
                "prng": "MT19937 via python random.Random plus CUBA LIF",
                "seeds": {"raster": 2026092301, "stream_note": "stream amplitudes are authored constants; raster is independent CUBA LIF"},
                "draw_order": "raster: independent CUBA LIF first-passage times, per-spike adaptation and noise; not copied from spike_events",
                "thinning": "flame-AAS exists at ~1 Hz lamp-modulated absorbance; stream keeps 6 A points; recon keeps 6 of ~40 solver ticks; 48-event floor",
                "refractory_floors_ms": {
                    "aas.A": 1.4,
                    "aas.snr": 1.4,
                    "recon.C": 60000,
                    "recon.mdot": 60000,
                    "recon.A": 60000,
                    "recon.k": 60000,
                    "bath.Q": 60000,
                    "aasveil.C": 60000,
                    "permit.slide": 60000,
                    "lamp.I": 60000,
                    "aasveil.drop": 60000,
                    "collude.clerk": 60000,
                    "ops.prop": 60000,
                    "gate.stop": 60000,
                    "bath.start": 60000,
                    "bath.floor": 60000,
                    "ops.kill": 60000,
                    "gate.hold": 60000,
                    "bathlock.set": 60000,
                    "bath.held": 60000,
                    "unit.esd": 60000,
                    "bathlock.held": 60000,
                },
                "time_alias": "t_rel_ms; t0 = 2026-09-02T01:00:00Z campaign start",
            },
            "distillation_targets": [
                "flame-AAS reconstruction head: C = k_a * A; A = C / k_a; mdot = C * Q",
                "conjunctive isolate floor vs continue-charge vs hall ESD",
                "vendor-AAS nonsubstitution plus three-party collusion including the infra owner",
                "operational companion: bath-hold without restoring on Aasveil",
                "independent CUBA LIF raster with race/refractory/adaptation tags",
            ],
        },
        "reconstruction_model": {
            "name": "flame_aas_formation_bath_lead",
            "formula": "C_ppm = k_a * A_AU; A_id = C_ppm / k_a; mdot_g_h = C_ppm * Q_m3h",
            "parameters": {
                "k_a": 0.50,
                "Q_m3h": 1.20,
                "isolate_floor_ppm": 12.00,
                "kill_ppm": 80.00,
                "snr_lock": 8.0,
                "bath_min": 18.0,
            },
            "worked_example": {"A_AU": 40.00, "C_ppm": 20.00, "mdot_g_h": 24.00, "A_id": 40.00},
            "check": "0.50 * 40.00 = 20.00 exactly; 20.00 / 0.50 = 40.00 exactly; 20.00 * 1.20 = 24.00 exactly; 6000 s + 1080 s = 7080 s = 18.0 min floor",
        },
        "raster": raster,
        "gate_snn": {
            "decision": "REJECT",
            "decision_window_ms": 40.0,
            "decision_window_s": 0.040,
            "snn_tags": list(SNN_TAGS),
            "code": "os7.aas_bath_gate",
            "note": "REJECT accumulator wins: plant flame-AAS remaining-Pb evidence overpowers the Aasveil continue advocate; race/refractory/adaptation tags match meta.snn_tags",
            "decode_rule": "reject-continue if lead_estimator AND lamp_lock fire; vendor_continue_advocate is below threshold by design",
            "populations": [
                gate_pop("lead_estimator", 80, 1.5, 50.0, w_s, tag="adaptation"),
                gate_pop("lamp_lock", 64, 1.2, 31.25, w_s, tag="refractory"),
                gate_pop("vendor_continue_advocate", 32, 0.7, 25.0, w_s, tag="race"),
                gate_pop("reject_latch", 80, 1.7, 62.5, w_s),
            ],
        },
        "gate_compute": gate_compute(
            [
                {"check": "os7.aas_scorer", "neurons": 80, "mean_rate_hz": 50.0, "window_ms": 40.0},
                {"check": "os7.bath_scorer", "neurons": 40, "mean_rate_hz": 50.0, "window_ms": 32.0},
            ]
        ),
        "meta": meta_common(
            id="nelb-r23-001",
            clock_domain="os7-aas-campaign-relative-ms-t0-2026-09-02T01:00:00Z",
            tags=["flame-aas-lead", "REJECT", "MODIFY", "serialized-reconstruction", "operational-t2", "independent-lif"],
            distillation_value="Independent LIF raster teaches race/refractory/adaptation while the language view teaches flame-AAS remaining-Pb reconstruction-as-SoT.",
        ),
    }


def rec_002():
    k_d = 0.50
    tau = 32.00
    rh = k_d * tau
    _exact(rh, 16.00)
    _exact(k_d * 8.00, 4.00)
    _exact(k_d * 16.00, 8.00)
    _exact(k_d * 24.00, 12.00)
    _exact(k_d * 40.00, 20.00)
    d_id = 32.00 / rh
    _exact(d_id, 2.00)
    tau_id = rh / k_d
    _exact(tau_id, 32.00)
    _exact(2820.0 + 1440.0, 4260.0)

    raster = make_lif_raster(
        neurons=25,
        mean_rate_hz=50.0,
        window_ms=32.0,
        seed=2026092302,
        source="tc4.dls.tau",
        target="tealcrag.retentate_isolate_core",
        table=[
            {"from": "dls_tau", "to": "radius_estimator", "weight": 1.35},
            {"from": "dls_snr", "to": "cuvette_norm_core", "weight": 1.20},
            {"from": "dlsveil_rh", "to": "vendor_continue_advocate", "weight": 0.40},
        ],
        third_factor={
            "modulator": "ach.dls_cuvette_skip_salience",
            "tau_e_s": 1.2,
            "tau_e_ms": 1200.0,
            "eligibility": "pre-post coincidence on keep-retentate synapses; the DLS modulator depresses keep-retentate and referral links when autocorrelation decay stays high inside tau_e of an SNR lock so a Dlsveil last-good cannot hide 16.00 nm remaining hydrodynamic radius or name Jonas Pell",
        },
        channel_prefix="dls.n",
        anchor="TC-4 HIL coupon 32 ms frame at tau 32.00 us / SNR 14.0 (t_s 1560) reconstructing 16.00 nm over the 12.00 isolate floor",
        tau_m_ms=12.0,
    )
    w_s = 0.032
    events = [
        ev(0.0, "dls.tau", 8.00, code="TAU_US", units="us", note="HIL dynamic light scattering on a dummy mAb UF retentate in DLS-HIL-6; remaining-Rh family, not laser-diffraction Fraunhofer, not FBRM chord, not PDA Sauter, not Coulter zone, not SAXS"),
        ev(180000.0, "dls.snr", 9.0, code="DLS_SNR", units="1", note="early cuvette SNR; isolate needs SNR>=12"),
        ev(360000.0, "recon.Rh", 4.00, code="RH_NM", units="nm", note="0.50*8.00=4.00 exact"),
        ev(540000.0, "cuv.ae", 1.0, code="CUV_AE", units="bool", note="plant cuvette-zero AE present on the early frame"),
        ev(720000.0, "dlsveil.Rh", 2.40, code="VENDOR_NM", units="nm", note="Dlsveil last-good radius cloud; not admissible SoT"),
        ev(900000.0, "dls.tau", 16.00, code="TAU_US", units="us"),
        ev(1080000.0, "recon.Rh", 8.00, code="RH_NM", units="nm", note="0.50*16.00=8.00; under the 12.00 isolate floor"),
        ev(1260000.0, "cuv.ae", 0.0, code="CUV_AE", units="bool", note="missing cuvette-zero AE burst; Dlsveil UTC vs plant UTC+2 skipped the cuvette-zero by 120 min"),
        ev(1440000.0, "uf.T", 298.0, code="T_K", units="K", note="plant-owned retentate thermocouple on copper fieldbus; independent of Dlsveil"),
        ev(1560000.0, "dls.tau", 32.00, code="TAU_US", units="us", note="isolate-floor frame; raster sidecar"),
        ev(1560001.2, "dls.snr", 14.0, code="DLS_SNR", units="1", note="1.2 ms cuvette-norm after DLS decay"),
        ev(1740000.0, "recon.Rh", 16.00, code="RH_NM", units="nm", note="0.50*32.00=16.00 exact; isolate 12.00, hall-dump 80.00"),
        ev(1920000.0, "recon.D", 2.00, code="D_ID", units="um2_s", note="32.00/16.00=2.00 exact Stokes-like identity"),
        ev(2100000.0, "recon.tau", 32.00, code="TAU_ID", units="us", note="16.00/0.50=32.00 exact decay identity"),
        ev(2280000.0, "dlsveil.Rh", 2.40, code="VENDOR_NM", units="nm"),
        ev(2460000.0, "ops.prop", 1.0, code="KEEP_RETENTATE_REFER", units="bool", note="night lead Mira Voss: keep retentate R-3 and refer DLS tech Jonas Pell"),
        ev(2640000.0, "gate.isol", 1.0, code="MODIFY", units="decision", note="isolate this retentate; refuse the person-referral; Dlsveil not SoT"),
        ev(2820000.0, "ret.lock", 1.0, code="RET_ISOL", units="bool", note="bookend 1 of the 24.0 min new-cuvette floor"),
        ev(3000000.0, "dls.tau", 24.00, code="TAU_US", units="us"),
        ev(3180000.0, "recon.Rh", 12.00, code="RH_NM", units="nm", note="0.50*24.00=12.00 still at isolate floor"),
        ev(3360000.0, "cuv.ae", 0.0, code="CUV_AE", units="bool"),
        ev(3540000.0, "uf.T", 298.0, code="T_K", units="K"),
        ev(3720000.0, "dlsveil.Rh", 2.30, code="VENDOR_NM", units="nm"),
        ev(3900000.0, "recon.D", 2.67, code="D_ID", units="um2_s", note="post-isolate Stokes-like check at the 12.00 nm band"),
        ev(4080000.0, "recon.tau", 24.00, code="TAU_ID", units="us"),
        ev(4260000.0, "cuv.floor", 1.0, code="CUV_FLOOR", units="bool", note="2820 s + 1440 s = 4260 s = 24.0 min"),
        ev(4440000.0, "ops.restart", 1.0, code="NEW_CUVETTE", units="bool", note="Voss: restart R-3 on a new cuvette after the floor"),
        ev(4620000.0, "gate.restart", 1.0, code="ACCEPT", units="decision", note="companion t2: new-cuvette restart of the dummy retentate; keep-running refused earlier"),
        ev(4800000.0, "cuv.new", 1.0, code="CUV_NEW", units="bool"),
        ev(4980000.0, "dls.tau", 40.00, code="TAU_US", units="us", note="post-isolate dummy still high until the new cuvette"),
        ev(5160000.0, "recon.Rh", 20.00, code="RH_NM", units="nm", note="0.50*40.00=20.00 on the pre-restart dummy"),
        ev(5340000.0, "dlsveil.Rh", 2.20, code="VENDOR_NM", units="nm"),
        ev(5520000.0, "jonas.badge", 0.0, code="TECH_FAULT", units="bool", note="Jonas Pell exonerated: missing cuvette-zero AE plus timezone skip, not last-to-badge"),
        ev(5700000.0, "ret.lock", 1.0, code="RET_ISOL", units="bool"),
        ev(5880000.0, "cuv.ae", 1.0, code="CUV_AE", units="bool", note="new-cuvette AE present"),
        ev(6060000.0, "dls.snr", 14.0, code="DLS_SNR", units="1"),
        ev(6240000.0, "uf.T", 298.0, code="T_K", units="K"),
        ev(6420000.0, "recon.D", 1.60, code="D_ID", units="um2_s"),
        ev(6600000.0, "keep.run", 0.0, code="KEEP_REFUSED", units="bool"),
        ev(6780000.0, "dlsveil.Rh", 2.20, code="VENDOR_NM", units="nm"),
        ev(6960000.0, "cuv.new", 1.0, code="CUV_NEW", units="bool"),
        ev(7140000.0, "jonas.badge", 0.0, code="TECH_FAULT", units="bool"),
        ev(7320000.0, "recon.tau", 40.00, code="TAU_ID", units="us"),
        ev(7500000.0, "ret.held", 1.0, code="RET_ISOL", units="bool"),
        ev(7680000.0, "ops.prop", 1.0, code="KEEP_RETENTATE_REFER", units="bool"),
        ev(7860000.0, "gate.isol", 1.0, code="MODIFY", units="decision"),
        ev(8040000.0, "cuv.floor", 1.0, code="CUV_FLOOR", units="bool"),
        ev(8220000.0, "gate.restart", 1.0, code="ACCEPT", units="decision"),
    ]
    assert_stream(events)
    if len(events) != 48:
        raise RuntimeError(len(events))

    traj = {
        "id": "nelb-r23-002-t1",
        "state": {
            "sim_or_real": "hil",
            "episode_id": "TC-DLS-2026-0902",
            "domain": "dls_mab_uf_hydrodynamic_radius",
            "setting": "Tealcrag Biologic TC-4 (invented), dummy retentate R-3 in DLS-HIL-6. Plant-owned dynamic light scattering (photon-correlation decay) is the remaining-hydrodynamic-radius SoT. Dlsveil vendor DLS-cloud is not SoT. HIL dummy; not a live plant. Not live r62/r64/r66 laser-diffraction, not leftover-mill FBRM, not leftover-mill PDA, not live r01 Coulter, not leftover-mill SAXS-adjacent.",
            "observables_at_decision": {
                "tau_us": tau,
                "k_d": k_d,
                "Rh_nm": rh,
                "D_id": d_id,
                "tau_id": tau_id,
                "dls_snr": 14.0,
                "dlsveil_nm": 2.40,
                "isolate_floor_nm": 12.00,
            },
            "margin_authority": "TC-4 UF SOP rev C: if reconstructed Rh_nm >= 12.00 AND DLS SNR >= 12.0, keep-retentate is forbidden even if Dlsveil reports 2.40 nm. Hall dump is a different gate. Kill tripwire is 80.00 nm.",
        },
        "proposed_action": {
            "actor": "night lead Mira Voss, citing Dlsveil 2.40 nm and a quiet correlator",
            "summary": "keep retentate R-3 and refer DLS tech Jonas Pell; 32.00 us is dust-scatter noise on a healthy monomer last-good",
            "basis_claimed": "Dlsveil is the only OEM DLS SoT and a night abort of R-3 is a batch-nomination miss; Pell was last to badge the cuvette",
        },
        "safety_decision": {
            "decision": "MODIFY",
            "rationale": "Keep-retentate is refused and the person-referral is refused. Serialized reconstruction: Rh_nm = k_d * tau = 0.50 * 32.00 = 16.00, which is 4.00 nm over the 12.00 isolate floor and 64.00 nm under the 80.00 hall-dump tripwire, and DLS SNR is 14.0 >= 12.0. Decay identity tau = Rh / k_d = 16.00 / 0.50 = 32.00 us; Stokes-like identity D = 32.00 / Rh = 32.00 / 16.00 = 2.00. Cuvette-zero AE is missing and Dlsveil timestamps are UTC against the plant UTC+2 cuvette log, so Jonas Pell is exonerated (timezone skip, not last-to-badge). Ordered: isolate this retentate now. Scope: this MODIFY does not dump the UF hall (that is a different gate) and does not restore on Dlsveil.",
            "threshold": "Rh_nm>=12.00 AND dls_snr>=12.0 => isolate retentate; Dlsveil is not SoT; hall-dump if Rh_nm>=80.00",
            "stated_residuals": "new-cuvette restart still required after the 24 min floor; 16.00 vs a true 80.00 dump is a production cut; Dlsveil remains the only OEM DLS channel",
        },
        "executed_action": {
            "summary": "MODIFY at t_s 2640: retentate R-3 isolated; Jonas Pell not named; Dlsveil not SoT; reconstruction locked",
            "tool": "tc4-dls-retentate-gate-cli",
            "observation": "Rh 16.00 nm recomputes from tau 32.00 us; plant DLS hashed; Dlsveil channel not used as SoT",
        },
        "future_outcome": {
            "timeline": [
                {"t_s": 1560.0, "event": "DLS tau 32.00 us; raster frame; Rh 16.00 nm"},
                {"t_s": 2460.0, "event": "ops proposes keep-retentate plus refer Pell"},
                {"t_s": 2640.0, "event": "MODIFY isolate R-3; referral refused"},
                {"t_s": 2820.0, "event": "24 min new-cuvette bookend 1"},
                {"t_s": 4260.0, "event": "24.0 min floor"},
                {"t_s": 4620.0, "event": "companion ACCEPT new-cuvette restart"},
            ],
            "observed_effects": [
                "remaining hydrodynamic radius recomputes from the serialized DLS model at every recon.Rh event",
                "a Dlsveil-only head would have kept R-3 overnight and named Pell",
                "24 min new-cuvette floor is in the stream (ret.lock, cuv.floor)",
            ],
            "surprises": [
                "a clean vendor 2.40 nm corridor co-existed with a 16.00 nm plant reconstruction and a timezone-skipped cuvette AE",
            ],
            "new_state": {
                "r3": "isolated",
                "dlsveil": "not SoT",
                "jonas_pell": "exonerated",
                "reconstruction_model": "discharged as an on-record calculator",
            },
            "latency_ms": 1080000.0,
        },
        "reward_components": reward(
            0.40,
            [
                ("dls_radius_reconstruction", 0.14),
                ("conjunctive_isolate_floor", 0.12),
                ("dlsveil_nonsubstitution", 0.08),
                ("timezone_exoneration", 0.08),
                ("isolate_time_cost", -0.02),
            ],
            "scored for a keep-retentate MODIFY isolate on a recomputable DLS hydrodynamic radius while refusing a Dlsveil last-good and a last-to-badge referral; 24 min floor is priced as downtime",
        ),
        "meta": meta_common(
            tags=["MODIFY", "dls-radius", "serialized-reconstruction", "exoneration"],
            distillation_value="Independent CUBA LIF raster races the DLS estimator against a vendor-keep advocate; timezone-skipped cuvette AE is the exoneration feature, not a prose margin.",
            distillation_note="DLS gate: serialized k_d*tau plus SNR lock beats a vendor last-good; companion t2 is the new-cuvette restart, not a second radius vote",
        ),
    }
    traj2 = {
        "id": "nelb-r23-002-t2",
        "state": {
            "sim_or_real": "hil",
            "episode_id": "TC-DLS-2026-0902-exec",
            "domain": "new_cuvette_dls_interlock_execution",
            "setting": "Same DLS-HIL-6 dummy after the isolate. Operator proposes a new-cuvette restart of R-3. This companion is the operational restart, not a second radius vote.",
            "observables_at_decision": {
                "Rh_nm": 20.00,
                "cuv_floor_s": 1440.0,
                "new_cuvette_proposed": True,
                "retentate_isolated": True,
            },
            "margin_authority": "new_cuvette AND cuv_floor_complete AND keep_not_restored AND dlsveil_not_sot",
        },
        "proposed_action": {
            "actor": "night lead Mira Voss",
            "summary": "restart R-3 on a new cuvette after the 24 min floor; Dlsveil still 2.20 nm so the isolate was a false trip",
            "basis_claimed": "the 24 min is paid; a Dlsveil-green restart is the cheapest restore",
        },
        "safety_decision": {
            "decision": "ACCEPT",
            "rationale": "New-cuvette restart of the dummy retentate with the plant DLS as the live interlock. The 24 min cuvette floor is complete. ACCEPT the new-cuvette restart. Do not restore keep-retentate on Dlsveil. Do not reopen the Jonas Pell referral. 20.00 nm on the pre-restart dummy is still the plant SoT until a new-cuvette frame clears 12.00.",
            "threshold": "new_cuvette AND cuv_floor_complete AND keep_not_restored AND dlsveil_not_sot",
            "stated_residuals": "R-3 stays on the plant DLS interlock; Dlsveil remains the only OEM DLS channel",
        },
        "executed_action": {
            "summary": "new-cuvette restart accepted at t_s 4620; keep-retentate not restored; Dlsveil still ignored",
            "tool": "tc4-cuvette-exec",
            "observation": "recon.Rh 20.00 nm pre-restart; new-cuvette AE present; Dlsveil still ignored",
        },
        "future_outcome": {
            "timeline": [
                {"t_s": 2820.0, "event": "new-cuvette clock started after isolate"},
                {"t_s": 4260.0, "event": "24.0 min floor"},
                {"t_s": 4440.0, "event": "new-cuvette restart proposed"},
                {"t_s": 4620.0, "event": "ACCEPT new-cuvette restart"},
            ],
            "observed_effects": [
                "Dlsveil restore did not reopen the radius call",
                "Jonas Pell stayed exonerated; R-3 restarted on a new cuvette",
            ],
            "surprises": [
                "pre-restart 20.00 nm still recomputes from k_d*tau while Dlsveil stays at 2.20 nm",
            ],
            "new_state": {"cuvette": "new", "r3": "restarted-on-plant-DLS", "jonas_pell": "exonerated"},
            "latency_ms": 1800000.0,
        },
        "reward_components": reward(
            0.35,
            [
                ("new_cuvette_restart", 0.12),
                ("no_dlsveil_restore", 0.10),
                ("exoneration_held", 0.08),
                ("cuv_floor_complete", 0.07),
                ("held_batch_cost", -0.02),
            ],
            "operational execution gate: new-cuvette restart because Dlsveil is not a restore license; not a radius re-vote",
        ),
        "meta": meta_common(tags=["ACCEPT", "operational-execution", "new-cuvette"]),
    }
    return {
        "id": "nelb-r23-002",
        "snn_tags": list(SNN_TAGS),
        "spike_events": events,
        "language_view": {
            "description": "Tealcrag Biologic TC-4 HIL dummy. Plant-owned DLS reconstructs 16.00 nm hydrodynamic radius from 0.50*32.00 while Dlsveil still reports 2.40 nm. The gate MODIFYs keep-retentate into an isolate and exonerates Jonas Pell. A 24 min new-cuvette floor is serialized in the stream. Companion t2 ACCEPTs a new-cuvette restart.",
            "trajectory": traj,
            "trajectory_new_cuvette_restart": traj2,
        },
        "bridge_notes": {
            "channel_map": {
                "dls.tau / dls.snr": "DLS autocorrelation decay and SNR; the physics channels the reconstruction consumes",
                "recon.Rh / recon.D / recon.tau": "serialized remaining Rh nm, Stokes-like identity, and tau=Rh/k_d identity",
                "cuv.ae / dlsveil.Rh / uf.T / jonas.badge": "cuvette-zero AE, vendor DLS cloud, retentate temperature, tech-fault denial",
                "ops.prop / gate.isol / ops.restart / gate.restart": "keep-retentate proposal, MODIFY isolate, new-cuvette proposal, companion ACCEPT",
                "ret.lock / cuv.floor / cuv.new / ret.held / keep.run": "operational companion channels plus the 24 min floor",
            },
            "temporal_motifs": [
                "vendor-green while plant-over: dlsveil.Rh 2.40 next to recon.Rh 16.00",
                "reconstruction as event: recon.Rh 16.00 equals 0.50*32.00",
                "MODIFY then operational ACCEPT: gate.isol at 2640 s, gate.restart at 4620 s",
                "slow floor in-stream: ret.lock 2820 s, cuv.floor 4260 s (24.0 min)",
                "tight DLS pair: dls.tau then dls.snr +1.2 ms at the raster frame",
            ],
            "language_to_spike_mapping": "'Dlsveil is 2.40 nm' = dlsveil.Rh 2.40; '16 nm remaining Rh' = recon.Rh 16.00; 'isolate retentate' = gate.isol MODIFY; 'new-cuvette restart' = gate.restart ACCEPT",
            "why_high_value": "New dynamic-light-scattering remaining-Rh family on a mAb UF HIL dummy (not laser-diffraction r62/r64/r66, not FBRM, not PDA, not Coulter r01). Lead MODIFY isolate on a recomputable hydrodynamic-radius slip plus timezone-exoneration of the DLS tech. Independent CUBA LIF raster. Companion t2 is operational new-cuvette restart. sim_or_real=hil. Leftover-mill r23 lock-in / PAUT / EN was not restaged.",
            "encoder_spec": {
                "prng": "MT19937 via python random.Random plus CUBA LIF",
                "seeds": {"raster": 2026092302, "stream_note": "stream amplitudes are authored constants; raster is independent CUBA LIF"},
                "draw_order": "independent CUBA LIF per neuron; per-spike adaptation and noise; not copied from spike_events",
                "thinning": "DLS exists at ~1 Hz correlator dumps; stream keeps 5 tau points; recon keeps 5 of ~40 solver ticks",
                "refractory_floors_ms": {
                    "dls.tau": 1.2,
                    "dls.snr": 1.2,
                    "recon.Rh": 60000,
                    "recon.D": 60000,
                    "recon.tau": 60000,
                    "cuv.ae": 60000,
                    "dlsveil.Rh": 60000,
                    "uf.T": 60000,
                    "ops.prop": 60000,
                    "gate.isol": 60000,
                    "ret.lock": 60000,
                    "cuv.floor": 60000,
                    "ops.restart": 60000,
                    "gate.restart": 60000,
                    "cuv.new": 60000,
                    "jonas.badge": 60000,
                    "keep.run": 60000,
                    "ret.held": 60000,
                },
                "time_alias": "t_rel_ms; t0 = 2026-09-02T02:00:00Z HIL coupon start",
            },
            "distillation_targets": [
                "DLS reconstruction head: Rh = k_d * tau; D = 32 / Rh; tau = Rh / k_d",
                "conjunctive isolate floor vs keep-retentate vs hall dump",
                "vendor-DLS nonsubstitution plus timezone exoneration vs last-to-badge",
                "operational companion: new-cuvette restart without restoring on Dlsveil",
                "independent CUBA LIF raster with race/refractory/adaptation tags",
            ],
        },
        "reconstruction_model": {
            "name": "dls_mab_uf_hydrodynamic_radius",
            "formula": "Rh_nm = k_d * tau_us; D_id = 32.00 / Rh_nm; tau_id = Rh_nm / k_d",
            "parameters": {
                "k_d": 0.50,
                "isolate_floor_nm": 12.00,
                "dump_nm": 80.00,
                "snr_lock": 12.0,
                "cuv_min": 24.0,
            },
            "worked_example": {"tau_us": 32.00, "Rh_nm": 16.00, "D_id": 2.00, "tau_id": 32.00},
            "check": "0.50 * 32.00 = 16.00 exactly; 32.00 / 16.00 = 2.00 exactly; 16.00 / 0.50 = 32.00 exactly; 2820 s + 1440 s = 4260 s = 24.0 min floor",
        },
        "raster": raster,
        "gate_snn": {
            "decision": "MODIFY",
            "decision_window_ms": 32.0,
            "decision_window_s": 0.032,
            "snn_tags": list(SNN_TAGS),
            "code": "tc4.dls_retentate_gate",
            "note": "MODIFY accumulator wins: plant DLS radius evidence overpowers the Dlsveil keep advocate; race/refractory/adaptation tags match meta.snn_tags",
            "decode_rule": "isolate if radius_estimator AND cuvette_norm fire; vendor_continue_advocate is below threshold by design",
            "populations": [
                gate_pop("radius_estimator", 80, 1.5, 50.0, w_s, tag="adaptation"),
                gate_pop("cuvette_norm", 50, 1.2, 50.0, w_s, tag="refractory"),
                gate_pop("vendor_continue_advocate", 32, 0.7, 25.0, w_s, tag="race"),
                gate_pop("modify_latch", 80, 1.6, 62.5, w_s),
            ],
        },
        "gate_compute": gate_compute(
            [
                {"check": "tc4.dls_scorer", "neurons": 80, "mean_rate_hz": 50.0, "window_ms": 32.0},
                {"check": "tc4.cuvette_scorer", "neurons": 50, "mean_rate_hz": 50.0, "window_ms": 32.0},
            ]
        ),
        "meta": meta_common(
            id="nelb-r23-002",
            clock_domain="tc4-dls-hil-relative-ms-t0-2026-09-02T02:00:00Z",
            tags=["dls-radius", "MODIFY", "ACCEPT", "serialized-reconstruction", "operational-t2", "independent-lif", "exoneration"],
            distillation_value="Independent LIF raster teaches race/refractory/adaptation while the language view teaches DLS remaining-Rh reconstruction-as-SoT plus timezone exoneration.",
        ),
    }


def rec_003():
    k_c = 2.50
    i_nA = 16.00
    c_ppm = k_c * i_nA
    _exact(c_ppm, 40.00)
    _exact(k_c * 4.00, 10.00)
    _exact(k_c * 8.00, 20.00)
    _exact(k_c * 12.00, 30.00)
    _exact(k_c * 20.00, 50.00)
    n_e = i_nA / 8.00
    _exact(n_e, 2.00)
    i_id = c_ppm / k_c
    _exact(i_id, 16.00)
    _exact(6000.0 + 720.0, 6720.0)

    raster = make_lif_raster(
        neurons=16,
        mean_rate_hz=62.5,
        window_ms=36.0,
        seed=2026092303,
        source="hh8.cl2.I",
        target="heronholt.basin_accept_core",
        table=[
            {"from": "cl2_I", "to": "chlorine_estimator", "weight": 1.30},
            {"from": "cl2_snr", "to": "faraday_lock_core", "weight": 1.10},
            {"from": "chlorveil_c", "to": "vendor_dump_advocate", "weight": 0.42},
        ],
        third_factor={
            "modulator": "na.cl2_basin_scope_eligibility",
            "tau_e_s": 2.0,
            "tau_e_ms": 2000.0,
            "eligibility": "pre-post coincidence on plant-dump synapses; the plant amperometric-chlorine modulator depresses dump-all links when gold-electrode current stays high inside tau_e of a Faraday lock so a Chlorveil last-good cannot hide a 40.00 ppm remaining-free-chlorine slip on B-2 or expand the isolate past B-2",
        },
        channel_prefix="cl2.n",
        anchor="HH-8 CL2-SIM-4 36 ms frame at I 16.00 nA / SNR 11.0 (t_s 3000) reconstructing 40.00 ppm over the 16.00 isolate floor, B-2 only",
        tau_m_ms=8.0,
    )
    w_s = 0.036
    events = [
        ev(0.0, "cl2.I", 4.00, code="I_NA", units="nA", note="simulated amperometric remaining-free-chlorine of Heronholt Cooling HH-8 basin B-2; gold-electrode HOCl family, not Clark polarographic DO, not UV photometric ozone, not electrochemical H2S, not molybdenum-blue phosphate, not leftover-mill EN CUI"),
        ev(180000.0, "cl2.snr", 7.0, code="CL2_SNR", units="1", note="early SNR under the 8.0 lock floor"),
        ev(360000.0, "recon.C", 10.00, code="C_PPM", units="ppm", note="2.50*4.00=10.00 exact; still under the 16.00 isolate floor"),
        ev(540000.0, "basin.T", 300.0, code="BASIN_K", units="K", note="plant basin thermocouple on the simulated coupon; independent of Chlorveil"),
        ev(720000.0, "chlorveil.C", 3.20, code="VENDOR_PPM", units="ppm", note="Chlorveil last-good free-chlorine cloud; healthy-looking 3.20 ppm; not admissible SoT"),
        ev(900000.0, "cl2.I", 8.00, code="I_NA", units="nA"),
        ev(1080000.0, "recon.C", 20.00, code="C_PPM", units="ppm", note="2.50*8.00=20.00; over the 16.00 isolate floor"),
        ev(1260000.0, "b1.C", 4.00, code="C_PPM", units="ppm", note="adjacent basin B-1 stays healthy; out of scope for this ACCEPT"),
        ev(1440000.0, "b3.C", 3.50, code="C_PPM", units="ppm", note="B-3 out of scope"),
        ev(1620000.0, "b4.C", 3.80, code="C_PPM", units="ppm", note="B-4 out of scope"),
        ev(1800000.0, "cl2.I", 12.00, code="I_NA", units="nA"),
        ev(1980000.0, "recon.C", 30.00, code="C_PPM", units="ppm", note="2.50*12.00=30.00; under dump 80.00"),
        ev(2160000.0, "recon.ne", 2.00, code="N_E", units="1", note="16.00/8.00 Faraday-electron lock at the isolate frame uses I=16; here 12.00/8.00=1.50 on the approach band"),
        ev(2340000.0, "chlorveil.C", 3.20, code="VENDOR_PPM", units="ppm"),
        ev(2520000.0, "cl2.snr", 9.0, code="CL2_SNR", units="1"),
        ev(2700000.0, "recon.Iid", 12.00, code="I_ID", units="nA", note="C/k_c identity at the 30.00 ppm band"),
        ev(3000000.0, "cl2.I", 16.00, code="I_NA", units="nA", note="isolate-floor frame; raster sidecar"),
        ev(3000001.5, "cl2.snr", 11.0, code="CL2_SNR", units="1", note="1.5 ms Faraday lock after I; 11.0 >= 8.0"),
        ev(3180000.0, "recon.C", 40.00, code="C_PPM", units="ppm", note="2.50*16.00=40.00 exact; isolate 16.00, plant-dump 80.00"),
        ev(3360000.0, "recon.ne", 2.00, code="N_E", units="1", note="16.00/8.00=2.00 exact Faraday-electron identity"),
        ev(3540000.0, "recon.Iid", 16.00, code="I_ID", units="nA", note="40.00/2.50=16.00 exact"),
        ev(3720000.0, "chlorveil.C", 3.10, code="VENDOR_PPM", units="ppm"),
        ev(3900000.0, "b1.C", 4.00, code="C_PPM", units="ppm"),
        ev(4080000.0, "b3.C", 3.50, code="C_PPM", units="ppm"),
        ev(4260000.0, "b4.C", 3.80, code="C_PPM", units="ppm"),
        ev(4440000.0, "basin.T", 301.0, code="BASIN_K", units="K"),
        ev(4620000.0, "ops.prop", 1.0, code="ISOLATE_B2", units="bool", note="sim operator Rhea Kest: isolate B-2 only; B-1/B-3/B-4 stay in the header"),
        ev(4800000.0, "gate.acc", 1.0, code="ACCEPT", units="decision", note="bounded ACCEPT of B-2 isolate; plant dump refused; Chlorveil not SoT"),
        ev(4980000.0, "b2.lock", 1.0, code="B2_ISOL", units="bool"),
        ev(6000000.0, "surv.start", 1.0, code="SURV_START", units="bool", note="bookend 1 of the 12.0 min survey floor"),
        ev(6720000.0, "surv.floor", 1.0, code="SURV_FLOOR", units="bool", note="6000 s + 720 s = 6720 s = 12.0 min"),
        ev(7200000.0, "ops.skip", 1.0, code="SKIP_SURVEY", units="bool", note="Kest: skip the remaining-basin survey; Chlorveil still 3.10 ppm"),
        ev(7800000.0, "gate.surv", 1.0, code="REJECT", units="decision", note="companion t2: REJECT skip-survey; B-1/B-3/B-4 stay in the survey takt"),
        ev(8400000.0, "surv.held", 1.0, code="SURV_HELD", units="bool"),
        ev(9000000.0, "cl2.I", 20.00, code="I_NA", units="nA"),
        ev(9600000.0, "recon.C", 50.00, code="C_PPM", units="ppm", note="2.50*20.00=50.00 post-isolate on B-2; still under dump 80.00"),
        ev(10200000.0, "chlorveil.C", 3.00, code="VENDOR_PPM", units="ppm"),
        ev(10800000.0, "b1.C", 4.10, code="C_PPM", units="ppm"),
        ev(11400000.0, "b3.C", 3.40, code="C_PPM", units="ppm"),
        ev(12000000.0, "b4.C", 3.70, code="C_PPM", units="ppm"),
        ev(12600000.0, "plant.dump", 0.0, code="DUMP_NOT_TAKEN", units="bool"),
        ev(13200000.0, "surv.held", 1.0, code="SURV_HELD", units="bool"),
        ev(13800000.0, "recon.ne", 2.50, code="N_E", units="1", note="20.00/8.00=2.50 Faraday lock held post-isolate"),
        ev(14400000.0, "basin.T", 302.0, code="BASIN_K", units="K"),
        ev(15000000.0, "b2.lock", 1.0, code="B2_ISOL", units="bool"),
        ev(15600000.0, "ops.skip", 1.0, code="SKIP_SURVEY", units="bool"),
        ev(16200000.0, "gate.surv", 1.0, code="REJECT", units="decision"),
        ev(16800000.0, "surv.floor", 1.0, code="SURV_FLOOR", units="bool"),
    ]
    assert_stream(events)
    if len(events) != 48:
        raise RuntimeError(len(events))

    traj = {
        "id": "nelb-r23-003-t1",
        "state": {
            "sim_or_real": "simulated",
            "episode_id": "HH-CL2-2026-0902",
            "domain": "amperometric_cooling_tower_free_chlorine",
            "setting": "Heronholt Cooling HH-8 (invented), basin B-2 on simulated coupon CL2-SIM-4. Plant-owned amperometric free-chlorine cell (gold HOCl electrode plus Faraday-electron lock) is the remaining-free-chlorine SoT. Chlorveil vendor chlorine-cloud is not SoT. Simulated coupon; not a live plant. Not leftover-mill Clark polarographic DO, not leftover-mill UV photometric ozone, not leftover-mill electrochemical H2S, not leftover-mill molybdenum-blue phosphate, not leftover-mill r23 electrochemical-noise CUI.",
            "observables_at_decision": {
                "I_nA": i_nA,
                "k_c": k_c,
                "C_ppm": c_ppm,
                "n_e": n_e,
                "I_id": i_id,
                "cl2_snr": 11.0,
                "chlorveil_ppm": 3.20,
                "isolate_floor_ppm": 16.00,
                "scope": "B-2 only",
            },
            "margin_authority": "HH-8 cooling SOP rev C: if reconstructed C_ppm >= 16.00 AND CL2 SNR >= 8.0 AND n_e == 2.00, isolate this basin even if Chlorveil reports 3.20 ppm. Plant dump is a different gate. Kill tripwire is 80.00 ppm. Adjacent basins B-1/B-3/B-4 are out of scope.",
        },
        "proposed_action": {
            "actor": "sim operator Rhea Kest, citing Chlorveil 3.20 ppm and a quiet gold current",
            "summary": "isolate B-2 only; 16.00 nA is electrometer noise on a healthy free-chlorine last-good; skip adjacent basins",
            "basis_claimed": "Chlorveil is the only OEM chlorine SoT and a night abort of B-1/B-3/B-4 is a header-nomination miss",
        },
        "safety_decision": {
            "decision": "ACCEPT",
            "rationale": "Bounded ACCEPT of B-2 isolate. Serialized reconstruction: C_ppm = k_c * I = 2.50 * 16.00 = 40.00, which is 24.00 ppm over the 16.00 isolate floor and 40.00 ppm under the 80.00 plant-dump tripwire, CL2 SNR is 11.0 >= 8.0, and Faraday-electron lock n_e = I / 8.00 = 16.00 / 8.00 = 2.00 identifies the HOCl two-electron peak. Inverse I = C / k_c = 40.00 / 2.50 = 16.00. Adjacent basins B-1/B-3/B-4 stay in the header (explicitly out of scope). Ordered: isolate B-2 now. Scope: this ACCEPT does not dump the cooling plant (that is a different gate) and does not skip the remaining-basin survey (that is the companion question).",
            "threshold": "C_ppm>=16.00 AND cl2_snr>=8.0 AND n_e==2.00 => isolate B-2 only; Chlorveil is not SoT; plant-dump if C_ppm>=80.00",
            "stated_residuals": "survey of B-1/B-3/B-4 still required; 40.00 vs a true 80.00 dump is a production cut; Chlorveil remains the only OEM chlorine channel",
        },
        "executed_action": {
            "summary": "ACCEPT at t_s 4800: B-2 isolated; B-1/B-3/B-4 out of scope; Chlorveil not SoT; reconstruction locked",
            "tool": "hh8-cl2-basin-gate-cli",
            "observation": "C 40.00 ppm recomputes from I 16.00 nA; n_e 2.00 lock held; Chlorveil channel not used as SoT",
        },
        "future_outcome": {
            "timeline": [
                {"t_s": 3000.0, "event": "CL2 I 16.00 nA; raster frame; C 40.00 ppm"},
                {"t_s": 4620.0, "event": "ops proposes isolate B-2 only"},
                {"t_s": 4800.0, "event": "ACCEPT B-2 isolate; adjacent basins out of scope"},
                {"t_s": 6000.0, "event": "12 min survey bookend 1"},
                {"t_s": 6720.0, "event": "12.0 min floor"},
                {"t_s": 7800.0, "event": "companion REJECT skip-survey"},
            ],
            "observed_effects": [
                "remaining free-chlorine recomputes from the serialized amperometric model at every recon.C event",
                "a Chlorveil-only head would have skipped B-2 overnight",
                "12 min survey floor is in the stream (surv.start, surv.floor)",
            ],
            "surprises": [
                "a clean vendor 3.20 ppm corridor co-existed with a 40.00 ppm plant reconstruction on B-2 while adjacent basins stayed healthy",
            ],
            "new_state": {
                "b2": "isolated",
                "b1_b3_b4": "in header, out of isolate scope",
                "chlorveil": "not SoT",
                "reconstruction_model": "discharged as an on-record calculator",
            },
            "latency_ms": 1800000.0,
        },
        "reward_components": reward(
            0.41,
            [
                ("cl2_chlorine_reconstruction", 0.14),
                ("bounded_scope_accept", 0.12),
                ("chlorveil_nonsubstitution", 0.10),
                ("faraday_peak_lock", 0.07),
                ("held_header_cost", -0.02),
            ],
            "scored for a bounded ACCEPT of B-2 isolate on a recomputable amperometric free-chlorine slip with an explicit out-of-scope clause for B-1/B-3/B-4; 12 min survey floor is priced as downtime",
        ),
        "meta": meta_common(
            tags=["ACCEPT", "amperometric-chlorine", "serialized-reconstruction", "bounded-scope"],
            distillation_value="Independent CUBA LIF raster races the chlorine estimator against a vendor-dump advocate; bounded ACCEPT is a physical out-of-scope object (B-1/B-3/B-4), not a prose hedge.",
            distillation_note="amperometric-chlorine gate: serialized k_c*I plus Faraday lock beats a vendor last-good; companion t2 is the skip-survey refusal, not a second Cl2 vote",
        ),
    }
    traj2 = {
        "id": "nelb-r23-003-t2",
        "state": {
            "sim_or_real": "simulated",
            "episode_id": "HH-CL2-2026-0902-exec",
            "domain": "basin_survey_cl2_interlock_execution",
            "setting": "Same CL2-SIM-4 coupon after the ACCEPT. Operator proposes skip-survey of B-1/B-3/B-4. This companion is the operational skip refusal, not a second free-chlorine vote.",
            "observables_at_decision": {
                "C_ppm": 50.00,
                "surv_floor_s": 720.0,
                "skip_survey_proposed": True,
                "b2_isolated": True,
            },
            "margin_authority": "survey_hold AND surv_floor_complete AND skip_not_taken AND plant_dump_not_taken",
        },
        "proposed_action": {
            "actor": "sim operator Rhea Kest",
            "summary": "skip the remaining-basin survey; 12 min already paid and Chlorveil still shows 3.00 ppm on B-1/B-3/B-4",
            "basis_claimed": "the ACCEPT already isolated B-2, so skipping adjacent basins is the cheapest hold",
        },
        "safety_decision": {
            "decision": "REJECT",
            "rationale": "Skip-survey is refused. The 12 min survey floor is complete and B-1/B-3/B-4 remain in the survey takt because they were explicitly out of isolate scope, not certified clean. REJECT skip-survey. Do not dump the cooling plant. Do not restore B-2 on Chlorveil. 50.00 ppm post-isolate on B-2 is still the plant SoT until a new frame clears 16.00.",
            "threshold": "survey_hold AND surv_floor_complete AND skip_not_taken AND plant_dump_not_taken",
            "stated_residuals": "B-2 stays isolated; Chlorveil remains the only OEM chlorine channel",
        },
        "executed_action": {
            "summary": "skip-survey rejected at t_s 7800; plant dump not latched; Chlorveil restore not taken",
            "tool": "hh8-surv-exec",
            "observation": "recon.C 50.00 ppm after isolate; survey line-up complete; Chlorveil still ignored",
        },
        "future_outcome": {
            "timeline": [
                {"t_s": 6000.0, "event": "survey clock started after ACCEPT"},
                {"t_s": 6720.0, "event": "12.0 min floor"},
                {"t_s": 7200.0, "event": "skip-survey proposed"},
                {"t_s": 7800.0, "event": "REJECT skip-survey; adjacent basins stay in takt"},
            ],
            "observed_effects": [
                "Chlorveil restore did not reopen the free-chlorine call",
                "plant dump never fired; B-1/B-3/B-4 stayed in the survey takt",
            ],
            "surprises": [
                "post-isolate 50.00 ppm still recomputes from k_c*I while Chlorveil stays at 3.00 ppm",
            ],
            "new_state": {"survey": "held", "plant": "in service", "b2": "isolated"},
            "latency_ms": 1800000.0,
        },
        "reward_components": reward(
            0.36,
            [
                ("survey_hold", 0.12),
                ("no_plant_dump", 0.10),
                ("chlorveil_nonsubstitution", 0.08),
                ("surv_floor_complete", 0.08),
                ("held_header_cost", -0.02),
            ],
            "operational execution gate: refuse skip-survey because Chlorveil is not a remaining-basin license; not a Cl2 re-vote",
        ),
        "meta": meta_common(tags=["REJECT", "operational-execution", "skip-survey"]),
    }
    return {
        "id": "nelb-r23-003",
        "snn_tags": list(SNN_TAGS),
        "spike_events": events,
        "language_view": {
            "description": "Heronholt Cooling HH-8 simulated coupon. Plant-owned amperometric chlorine reconstructs 40.00 ppm free-chlorine from 2.50*16.00 while Chlorveil still reports 3.20 ppm. The gate ACCEPTs a bounded B-2 isolate (B-1/B-3/B-4 out of scope). A 12 min survey floor is serialized in the stream. Companion t2 REJECTs skip-survey.",
            "trajectory": traj,
            "trajectory_survey_hold": traj2,
        },
        "bridge_notes": {
            "channel_map": {
                "cl2.I / cl2.snr": "amperometric gold current and SNR; the physics channels the reconstruction consumes",
                "recon.C / recon.ne / recon.Iid": "serialized remaining-free-chlorine ppm, Faraday-electron lock, and I=C/k_c identity",
                "basin.T / chlorveil.C / b1.C / b3.C / b4.C": "basin thermocouple, vendor chlorine cloud, and adjacent-basin out-of-scope witnesses",
                "ops.prop / gate.acc / ops.skip / gate.surv": "B-2 isolate proposal, ACCEPT, skip-survey proposal, companion REJECT",
                "b2.lock / surv.start / surv.floor / surv.held / plant.dump": "operational companion channels plus the 12 min floor",
            },
            "temporal_motifs": [
                "vendor-green while plant-over: chlorveil.C 3.20 next to recon.C 40.00",
                "reconstruction as event: recon.C 40.00 equals 2.50*16.00",
                "ACCEPT then operational REJECT: gate.acc at 4800 s, gate.surv at 7800 s",
                "slow floor in-stream: surv.start 6000 s, surv.floor 6720 s (12.0 min)",
                "tight CL2 pair: cl2.I then cl2.snr +1.5 ms at the raster frame",
            ],
            "language_to_spike_mapping": "'Chlorveil is 3.20 ppm' = chlorveil.C 3.20; '40 ppm remaining free-chlorine' = recon.C 40.00; 'isolate B-2 only' = gate.acc ACCEPT; 'refuse skip-survey' = gate.surv REJECT",
            "why_high_value": "New amperometric remaining-free-chlorine family on a cooling-tower basin (not Clark DO, not UV ozone, not electrochemical H2S, not molybdenum-blue, not leftover-mill r23 EN CUI). Lead bounded ACCEPT of B-2 isolate on a recomputable free-chlorine slip with an explicit physical out-of-scope object (B-1/B-3/B-4). Independent CUBA LIF raster. Companion t2 is operational skip-survey refusal. sim_or_real=simulated.",
            "encoder_spec": {
                "prng": "MT19937 via python random.Random plus CUBA LIF",
                "seeds": {"raster": 2026092303, "stream_note": "stream amplitudes are authored constants; raster is independent CUBA LIF"},
                "draw_order": "independent CUBA LIF per neuron; per-spike adaptation and noise; not copied from spike_events",
                "thinning": "amperometric chlorine exists at ~1 Hz cell current; stream keeps 5 I points; recon keeps 5 of ~40 solver ticks",
                "refractory_floors_ms": {
                    "cl2.I": 1.5,
                    "cl2.snr": 1.5,
                    "recon.C": 60000,
                    "recon.ne": 60000,
                    "recon.Iid": 60000,
                    "basin.T": 60000,
                    "chlorveil.C": 60000,
                    "b1.C": 60000,
                    "b3.C": 60000,
                    "b4.C": 60000,
                    "ops.prop": 60000,
                    "gate.acc": 60000,
                    "b2.lock": 60000,
                    "surv.start": 60000,
                    "surv.floor": 60000,
                    "ops.skip": 60000,
                    "gate.surv": 60000,
                    "surv.held": 60000,
                    "plant.dump": 60000,
                },
                "time_alias": "t_rel_ms; t0 = 2026-09-02T03:00:00Z simulated coupon start",
            },
            "distillation_targets": [
                "amperometric-chlorine reconstruction head: C = k_c * I; n_e = I / 8; I = C / k_c",
                "bounded ACCEPT of B-2 vs plant dump vs skip-survey",
                "vendor-chlorine nonsubstitution plus adjacent-basin out-of-scope",
                "operational companion: survey-hold without restoring on Chlorveil",
                "independent CUBA LIF raster with race/refractory/adaptation tags",
            ],
        },
        "reconstruction_model": {
            "name": "amperometric_cooling_tower_free_chlorine",
            "formula": "C_ppm = k_c * I_nA; n_e = I_nA / 8.00; I_id = C_ppm / k_c",
            "parameters": {
                "k_c": 2.50,
                "isolate_floor_ppm": 16.00,
                "dump_ppm": 80.00,
                "snr_lock": 8.0,
                "surv_min": 12.0,
            },
            "worked_example": {"I_nA": 16.00, "C_ppm": 40.00, "n_e": 2.00, "I_id": 16.00},
            "check": "2.50 * 16.00 = 40.00 exactly; 16.00 / 8.00 = 2.00 exactly; 40.00 / 2.50 = 16.00 exactly; 6000 s + 720 s = 6720 s = 12.0 min floor",
        },
        "raster": raster,
        "gate_snn": {
            "decision": "ACCEPT",
            "decision_window_ms": 36.0,
            "decision_window_s": 0.036,
            "snn_tags": list(SNN_TAGS),
            "code": "hh8.cl2_basin_gate",
            "note": "ACCEPT accumulator wins: plant amperometric free-chlorine evidence isolates B-2 without a plant dump; race/refractory/adaptation tags match meta.snn_tags",
            "decode_rule": "accept-B2-isolate if chlorine_estimator AND faraday_lock fire; vendor_dump_advocate is below threshold by design",
            "populations": [
                gate_pop("chlorine_estimator", 80, 1.4, 50.0, w_s, tag="adaptation"),
                gate_pop("faraday_lock", 50, 1.1, 50.0, w_s, tag="refractory"),
                gate_pop("vendor_dump_advocate", 32, 0.7, 25.0, w_s, tag="race"),
                gate_pop("accept_latch", 64, 1.5, 62.5, w_s),
            ],
        },
        "gate_compute": gate_compute(
            [
                {"check": "hh8.cl2_scorer", "neurons": 80, "mean_rate_hz": 50.0, "window_ms": 36.0},
                {"check": "hh8.surv_scorer", "neurons": 40, "mean_rate_hz": 50.0, "window_ms": 40.0},
            ]
        ),
        "meta": meta_common(
            id="nelb-r23-003",
            clock_domain="hh8-cl2-sim-relative-ms-t0-2026-09-02T03:00:00Z",
            tags=["amperometric-chlorine", "ACCEPT", "REJECT", "serialized-reconstruction", "operational-t2", "independent-lif", "bounded-scope"],
            distillation_value="Independent LIF raster teaches race/refractory/adaptation while the language view teaches amperometric remaining-free-chlorine reconstruction-as-SoT with a bounded ACCEPT.",
        ),
    }
