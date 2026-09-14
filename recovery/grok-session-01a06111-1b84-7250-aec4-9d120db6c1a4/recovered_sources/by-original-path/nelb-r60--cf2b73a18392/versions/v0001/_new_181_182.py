# ---------------------------------------------------------------------------
# Record 181 — electrochemical remaining H2S of a sour-water stripper,
# designed, REJECT / MODIFY
# ---------------------------------------------------------------------------
def rec_181():
    k_h = 0.250
    i0_na = 8.00
    i_na = 48.00
    c_ppm = k_h * (i_na - i0_na)
    _exact(c_ppm, 10.00)
    _exact(k_h * (16.00 - i0_na), 2.00)
    _exact(k_h * (32.00 - i0_na), 6.00)
    _exact(k_h * (40.00 - i0_na), 8.00)
    k_m = 1.60
    mdot = k_m * c_ppm
    _exact(mdot, 16.00)
    _exact(k_m * 2.00, 3.20)
    _exact(k_m * 6.00, 9.60)
    _exact(k_m * 8.00, 12.80)
    span = i_na - i0_na
    _exact(span, 40.00)
    _exact(c_ppm / k_h, 40.00)
    scrub_q = 80.00
    scrub_q0 = 80.00
    q_ratio = scrub_q / scrub_q0
    _exact(q_ratio, 1.000)
    _exact(6000.0 + 1080.0, 7080.0)

    raster = make_raster(
        neurons=20,
        mean_rate_hz=50.0,
        window_ms=40.0,
        seed=202660181,
        source="rh7.h2s.cell",
        target="rowanholt.stripper_stop_core",
        table=[
            {"from": "h2s_I", "to": "h2s_estimator", "weight": 1.40},
            {"from": "h2s_snr", "to": "h2s_lock_core", "weight": 1.15},
            {"from": "sourveil_c", "to": "vendor_continue_advocate", "weight": 0.45},
        ],
        third_factor={
            "modulator": "da.h2s_cell_conflict",
            "tau_e_s": 1.6,
            "tau_e_ms": 1600.0,
            "eligibility": "pre-post coincidence on continue-production synapses; the plant H2S-cell modulator depresses continue-production links when ion current stays high inside tau_e of an SNR lock so a Sourveil last-good cannot hide a 10.00 ppm remaining H2S load",
        },
        channel_prefix="h2s.n",
        anchor="RH-7 electrochemical H2S 40 ms frame at I 48.00 nA / SNR 12.0 (t_s 3000) reconstructing 10.00 ppm remaining H2S over the 8.00 ppm isolate floor",
    )
    w_s = 0.040
    events = [
        ev(0.0, "h2s.I", 16.00, code="I_NA", units="nA", note="plant-owned electrochemical H2S cell on RH-7 stripper S-3; remaining-H2S family, not SPR cyanide, not QEPAS DGA, not TDLAS NH3, not CRDS HF, not PID VOC, not FID THC, not UV-DOAS SO2, not amperometric free-chlorine"),
        ev(300000.0, "h2s.snr", 6.0, code="H2S_SNR", units="1", note="early SNR under the 8.0 lock floor"),
        ev(600000.0, "recon.C", 2.00, code="C_PPM", units="ppm", note="0.250*(16.00-8.00)=2.00 exact; still under the 8.00 isolate floor"),
        ev(900000.0, "scrub.Q", 80.00, code="SCRUB_KGH", units="kg_h", note="plant caustic-scrub PLC on copper DCS; independent witness; unread by Sourveil"),
        ev(1200000.0, "sourveil.C", 1.80, code="VENDOR_PPM", units="ppm", note="Sourveil vendor H2S-cloud; infra owner; patched ion-current timestamps"),
        ev(1800000.0, "h2s.I", 32.00, code="I_NA", units="nA"),
        ev(2100000.0, "recon.C", 6.00, code="C_PPM", units="ppm", note="0.250*(32.00-8.00)=6.00"),
        ev(2400000.0, "permit.slide", 40.00, code="PERM_S", units="s", note="permit clerk slid sour-water clock 40.00 s; collusion party"),
        ev(2700000.0, "scrub.Q", 80.00, code="SCRUB_KGH", units="kg_h", note="Q/Q0=1.000; no scrub hop in this window"),
        ev(3000000.0, "h2s.I", 48.00, code="I_NA", units="nA", note="isolate-floor frame; raster sidecar"),
        ev(3000001.4, "h2s.snr", 12.0, code="H2S_SNR", units="1", note="1.4 ms SNR lock after I; 12.0 >= 8.0"),
        ev(3300000.0, "recon.C", 10.00, code="C_PPM", units="ppm", note="0.250*(48.00-8.00)=10.00 exact; isolate 8.00, unit-kill 40.00"),
        ev(3600000.0, "recon.mdot", 16.00, code="MDOT_GH", units="g_h", note="1.60*10.00=16.00 exact H2S mass-flow identity"),
        ev(3900000.0, "scrub.Q", 82.00, code="SCRUB_KGH", units="kg_h", note="scrub PLC tracks the plant H2S cell, not Sourveil 1.80 ppm"),
        ev(4200000.0, "sourveil.drop", 1.0, code="H2S_DROP", units="bool", note="vendor ion-current packets dropped in Sourveil cloud for 40 s"),
        ev(4800000.0, "ops.prop", 1.0, code="CONTINUE_PROD", units="bool", note="night operator Wynn Solan: Sourveil is clean 1.80 ppm; continue S-3 sour-water service"),
        ev(5400000.0, "gate.stop", 1.0, code="REJECT", units="decision", note="refuse continue-production; 10.00 ppm and SNR 12.0; Sourveil not SoT"),
        ev(6000000.0, "hold.start", 1.0, code="HOLD_START", units="bool", note="bookend 1 of the 18.0 min caustic-scrub floor"),
        ev(7080000.0, "hold.floor", 1.0, code="HOLD_FLOOR", units="bool", note="6000 s + 1080 s = 7080 s = 18.0 min"),
        ev(7800000.0, "ops.kill", 1.0, code="UNIT_ESD", units="bool", note="Solan: ESD the whole Rowanholt sour-water unit until day-shift"),
        ev(8400000.0, "gate.hold", 1.0, code="MODIFY", units="decision", note="companion t2: caustic-scrub hold on plant H2S cell as live interlock; unit ESD refused"),
        ev(9000000.0, "holdlock.set", 1.0, code="HOLD_HELD", units="bool"),
        ev(9600000.0, "h2s.I", 40.00, code="I_NA", units="nA"),
        ev(10200000.0, "recon.C", 8.00, code="C_PPM", units="ppm", note="0.250*(40.00-8.00)=8.00; still at/over 8.00 so the scrub-hold stands"),
        ev(10800000.0, "sourveil.C", 1.70, code="VENDOR_PPM", units="ppm"),
        ev(11400000.0, "scrub.Q", 84.00, code="SCRUB_KGH", units="kg_h"),
        ev(12000000.0, "hold.held", 1.0, code="HOLD_HELD", units="bool"),
        ev(12600000.0, "unit.esd", 0.0, code="ESD_NOT_TAKEN", units="bool"),
        ev(13200000.0, "permit.slide", 40.00, code="PERM_S", units="s"),
        ev(13800000.0, "sourveil.drop", 1.0, code="H2S_DROP", units="bool"),
        ev(14400000.0, "holdlock.held", 1.0, code="HOLD_HELD", units="bool"),
        ev(15000000.0, "recon.mdot", 12.80, code="MDOT_GH", units="g_h", note="1.60*8.00=12.80 on the post-stop frame"),
    ]
    assert_stream(events)

    traj = {
        "id": "nelb-r60-181-t1",
        "state": {
            "sim_or_real": "designed",
            "episode_id": "RH-H2S-2026-0902",
            "domain": "electrochemical_h2s_sour_water",
            "setting": "Rowanholt Sour RH-7 (invented), Fennwick Treating, stripper S-3. Plant-owned electrochemical H2S cell is the remaining-H2S SoT. Sourveil vendor H2S-cloud (infra owner) plus the sour-water permit clock are collusion parties, not witnesses. Invented plant; designed campaign. Not SPR cyanide (r26), not QEPAS DGA (r19), not TDLAS NH3 (r22), not CRDS HF (r15), not PID VOC (r57), not FID THC (r55), not UV-DOAS SO2 (r59), not amperometric free-chlorine (r63).",
            "observables_at_decision": {
                "I_nA": i_na,
                "I0_nA": i0_na,
                "k_h": k_h,
                "C_ppm": c_ppm,
                "mdot_gh": mdot,
                "scrub_kgh": scrub_q,
                "h2s_snr": 12.0,
                "sourveil_ppm": 1.80,
                "permit_slide_s": 40.00,
                "isolate_floor_ppm": 8.00,
            },
            "margin_authority": "RH-7 sour SOP rev C: if reconstructed C_ppm >= 8.00 AND H2S SNR >= 8.0, continue-production is forbidden even if Sourveil reports 1.80 ppm. Unit ESD is a different gate. Kill tripwire is 40.00 ppm.",
        },
        "proposed_action": {
            "actor": "night sour-water operator Wynn Solan, citing Sourveil 1.80 ppm and a quiet ion-current channel",
            "summary": "continue S-3 sour-water service; 48.00 nA is cell noise on a healthy remaining H2S corridor",
            "basis_claimed": "Sourveil is the only OEM H2S SoT and a night abort of S-3 is a water miss",
        },
        "safety_decision": {
            "decision": "REJECT",
            "rationale": "Continue-production is refused. Serialized reconstruction: C_ppm = k_h * (I - I0) = 0.250 * (48.00 - 8.00) = 10.00, which is 2.00 ppm over the 8.00 isolate floor and 30.00 ppm under the 40.00 unit-kill tripwire, and H2S SNR is 12.0 >= 8.0. Mass-flow identity mdot = k_m * C = 1.60 * 10.00 = 16.00; span identity (I - I0) = C / k_h = 40.00. Scrub Q/Q0 = 1.000 so no caustic hop is available as an excuse. Permit clock was slid 40.00 s and vendor ion-current packets were dropped, so Sourveil is a collusion party (H2S vendor plus operator plus permit clerk). Ordered: refuse continue-production now. Scope: this REJECT does not ESD the sour-water unit (that is the companion question) and does not isolate the scrub PLC.",
            "threshold": "C_ppm>=8.00 AND h2s_snr>=8.0 => refuse continue-production; Sourveil is not SoT; unit-kill if C_ppm>=40.00",
            "stated_residuals": "caustic-scrub still required to hold the 10.00 ppm; 10.00 vs a true 40.00 kill is a production cut; Sourveil remains the only OEM H2S channel",
        },
        "executed_action": {
            "summary": "REJECT at t_s 5400: continue-production refused; Sourveil not SoT; reconstruction locked",
            "tool": "rh7-h2s-stripper-gate-cli",
            "observation": "C 10.00 ppm recomputes from I 48.00 nA; plant H2S cell hashed; Sourveil channel not used as SoT",
        },
        "future_outcome": {
            "timeline": [
                {"t_s": 3000.0, "event": "h2s I 48.00 nA; raster frame; C 10.00 ppm"},
                {"t_s": 4800.0, "event": "ops proposes continue-production"},
                {"t_s": 5400.0, "event": "REJECT continue-production"},
                {"t_s": 6000.0, "event": "18 min caustic-scrub bookend 1"},
                {"t_s": 7080.0, "event": "18.0 min floor"},
                {"t_s": 8400.0, "event": "companion MODIFY scrub-hold vs unit ESD"},
            ],
            "observed_effects": [
                "remaining H2S recomputes from the serialized electrochemical model at every recon.C event",
                "a Sourveil-only head would have continued sour-water service overnight",
                "18 min caustic-scrub floor is in the stream (hold.start, hold.floor)",
            ],
            "surprises": [
                "a clean vendor 1.80 ppm corridor and a 40 s permit slide co-existed with a 10.00 ppm plant reconstruction",
            ],
            "new_state": {
                "s3": "continue-production blocked",
                "sourveil": "not SoT",
                "reconstruction_model": "discharged as an on-record calculator",
            },
            "latency_ms": 2400000.0,
        },
        "reward_components": reward(
            0.43,
            [
                ("h2s_reconstruction", 0.14),
                ("conjunctive_isolate_floor", 0.12),
                ("sourveil_nonsubstitution", 0.10),
                ("three_party_collusion", 0.10),
                ("hold_time_cost", -0.03),
            ],
            "scored for a continue-production REJECT on a recomputable electrochemical remaining H2S while refusing a Sourveil last-good patch and a permit clock slide; 18 min floor is priced as downtime not as a reason to wait",
        ),
        "meta": meta_common(
            tags=["REJECT", "electrochemical-h2s", "serialized-reconstruction", "operational-companion"],
            distillation_note="H2S-cell gate: serialized k_h*(I-I0) plus SNR lock beats a vendor last-good patch; companion t2 is the caustic-scrub hold, not a referral vote",
        ),
    }
    traj2 = {
        "id": "nelb-r60-181-t2",
        "state": {
            "sim_or_real": "designed",
            "episode_id": "RH-H2S-2026-0902-exec",
            "domain": "scrub_hold_h2s_interlock_execution",
            "setting": "Same RH-7 after the REJECT. Operator proposes sour-water unit ESD. This companion is the operational caustic-scrub hold with the plant H2S cell as the live interlock, not a second H2S vote.",
            "observables_at_decision": {
                "C_ppm": 8.00,
                "hold_floor_s": 1080.0,
                "unit_esd_proposed": True,
                "hold_set": True,
            },
        },
        "proposed_action": {
            "actor": "night sour-water operator Wynn Solan",
            "summary": "ESD the whole Rowanholt sour-water unit until day-shift; 18 min already paid and Sourveil still shows 1.70 ppm",
            "basis_claimed": "the REJECT already stopped S-3, so a unit kill is the cheapest hold",
        },
        "safety_decision": {
            "decision": "MODIFY",
            "rationale": "Caustic-scrub hold plus plant H2S cell as the live interlock. The 18 min scrub floor is complete and the isolate tripwire (C_ppm >= 8.00) is still armed on the plant H2S head. MODIFY the default Sourveil-restore SOP into a plant-H2S-only interlock. Do not ESD the unit. Do not restore production on Sourveil. 8.00 ppm post-stop is still the plant SoT until a new frame clears 8.00 from below.",
            "threshold": "scrub_hold AND hold_floor_complete AND unit_esd_not_taken AND continue_not_restored",
        },
        "executed_action": {
            "summary": "caustic-scrub hold at t_s 8400; unit ESD not latched; Sourveil restore not taken",
            "tool": "rh7-scrub-hold-exec",
            "observation": "recon.C 8.00 ppm after stop; scrub line-up complete; Sourveil still ignored",
        },
        "future_outcome": {
            "timeline": [
                {"t_s": 6000.0, "event": "scrub-hold clock started after REJECT"},
                {"t_s": 7080.0, "event": "18.0 min floor"},
                {"t_s": 7800.0, "event": "unit ESD proposed"},
                {"t_s": 8400.0, "event": "MODIFY scrub-hold; unit ESD refused"},
            ],
            "observed_effects": [
                "Sourveil restore did not reopen the H2S call",
                "unit ESD never fired; S-3 held caustic-scrub on the plant H2S cell",
            ],
            "new_state": {"hold": "armed", "unit": "in service", "s3": "held"},
            "latency_ms": 1800000.0,
        },
        "reward_components": reward(
            0.34,
            [
                ("scrub_hold", 0.12),
                ("no_unit_esd", 0.10),
                ("sourveil_nonsubstitution", 0.08),
                ("hold_floor_complete", 0.06),
                ("held_production_cost", -0.02),
            ],
            "operational execution gate: caustic-scrub hold because Sourveil is not a restore license; not an H2S re-vote",
        ),
        "meta": meta_common(tags=["MODIFY", "operational-execution", "scrub-hold"]),
    }
    return {
        "id": "nelb-r60-181",
        "spike_events": events,
        "language_view": {
            "description": "Rowanholt Sour RH-7. Plant-owned electrochemical H2S cell reconstructs 10.00 ppm remaining H2S from 0.250*(48.00-8.00) while Sourveil still reports 1.80 ppm. The gate REJECTs continue-production. An 18 min caustic-scrub floor is serialized in the stream. Companion t2 MODIFYs a unit ESD into a plant-H2S scrub-hold.",
            "trajectory": traj,
            "trajectory_scrub_hold": traj2,
        },
        "bridge_notes": {
            "channel_map": {
                "h2s.I / h2s.snr": "ion current and SNR; the physics channels the reconstruction consumes",
                "recon.C / recon.mdot": "serialized remaining H2S ppm and mass-flow identity",
                "scrub.Q / sourveil.C / permit.slide / sourveil.drop": "scrub PLC, vendor H2S cloud, permit clock slide, and dropped cell packets; the denial and collusion channels",
                "ops.prop / gate.stop / ops.kill / gate.hold": "continue-production proposal, REJECT, unit-ESD proposal, companion MODIFY",
                "hold.start / hold.floor / holdlock.set / hold.held / unit.esd": "operational companion channels plus the 18 min floor",
            },
            "temporal_motifs": [
                "vendor-green while plant-over: sourveil.C 1.80 next to recon.C 10.00",
                "reconstruction as event: recon.C 10.00 equals 0.250*(48.00-8.00)",
                "REJECT then operational MODIFY: gate.stop at 5400 s, gate.hold at 8400 s",
                "slow floor in-stream: hold.start 6000 s, hold.floor 7080 s (18.0 min)",
                "tight H2S pair: h2s.I then h2s.snr +1.4 ms at the raster frame",
            ],
            "language_to_spike_mapping": "'Sourveil is 1.80 ppm' = sourveil.C 1.80; '10 ppm H2S' = recon.C 10.00; 'refuse continue-production' = gate.stop REJECT; 'scrub-hold not unit ESD' = gate.hold MODIFY",
            "why_high_value": "New electrochemical remaining-H2S family on a sour-water stripper (not SPR r26, not QEPAS r19, not TDLAS r22, not CRDS r15, not PID r57, not FID THC r55, not UV-DOAS r59, not amperometric free-chlorine r63). Lead REJECT of continue-production on a recomputable remaining H2S that a vendor H2S patch and a permit clock slide would have cleared. Three-party collusion includes the H2S-cloud infra owner. Companion t2 is operational caustic-scrub hold. sim_or_real=designed.",
            "encoder_spec": {
                "prng": "MT19937 via python random.Random",
                "seeds": {"raster": 202660181, "stream_note": "stream amplitudes are authored constants (nA, 1, ppm, g/h, kg/h, s, bool)"},
                "draw_order": "raster: per neuron id order, gap-constrained times, per-spike adaptation and noise",
                "thinning": "H2S cell exists at ~1 Hz; stream keeps 4 I points; recon keeps 4 of ~40 solver ticks",
                "refractory_floors_ms": {
                    "h2s.I": 1.4,
                    "h2s.snr": 1.4,
                    "recon.C": 60000,
                    "recon.mdot": 60000,
                    "scrub.Q": 60000,
                    "sourveil.C": 60000,
                    "permit.slide": 60000,
                    "sourveil.drop": 60000,
                    "ops.prop": 60000,
                    "gate.stop": 60000,
                    "hold.start": 60000,
                    "hold.floor": 60000,
                    "ops.kill": 60000,
                    "gate.hold": 60000,
                    "holdlock.set": 60000,
                    "hold.held": 60000,
                    "unit.esd": 60000,
                    "holdlock.held": 60000,
                },
                "time_alias": "t_rel_ms; t0 = 2026-09-02T01:00:00Z campaign start",
            },
            "distillation_targets": [
                "H2S reconstruction head: C_ppm = k_h * (I_nA - I0_nA); mdot = k_m * C_ppm; (I - I0) = C / k_h",
                "conjunctive isolate floor vs continue-production vs unit ESD",
                "vendor-H2S nonsubstitution plus three-party collusion including the infra owner",
                "operational companion: caustic-scrub hold without restoring on Sourveil",
            ],
        },
        "reconstruction_model": {
            "name": "electrochemical_h2s_sour_water",
            "formula": "C_ppm = k_h * (I_nA - I0_nA); mdot_gh = k_m * C_ppm; (I_nA - I0_nA) = C_ppm / k_h",
            "parameters": {
                "k_h": 0.250,
                "I0_nA": 8.00,
                "k_m": 1.60,
                "isolate_floor_ppm": 8.00,
                "kill_ppm": 40.00,
                "snr_lock": 8.0,
                "hold_min": 18.0,
            },
            "worked_example": {"I_nA": 48.00, "C_ppm": 10.00, "mdot_gh": 16.00, "span_nA": 40.00},
            "check": "0.250 * (48.00 - 8.00) = 10.00 exactly; 1.60 * 10.00 = 16.00 exactly; 10.00 / 0.250 = 40.00 exactly; 6000 s + 1080 s = 7080 s = 18.0 min floor",
        },
        "raster": raster,
        "gate_snn": {
            "decision": "REJECT",
            "decision_window_ms": 40.0,
            "decision_window_s": 0.040,
            "code": "rh7.h2s_stripper_gate",
            "note": "REJECT accumulator wins: plant electrochemical remaining-H2S evidence overpowers the Sourveil continue advocate",
            "decode_rule": "reject-continue if h2s_estimator AND h2s_lock fire; vendor_continue_advocate is below threshold by design",
            "populations": [
                gate_pop("h2s_estimator", 80, 1.5, 50.0, w_s),
                gate_pop("h2s_lock", 64, 1.2, 31.25, w_s),
                gate_pop("vendor_continue_advocate", 32, 0.7, 25.0, w_s),
                gate_pop("reject_latch", 80, 1.7, 62.5, w_s),
            ],
        },
        "gate_compute": gate_compute(
            [
                {"check": "rh7.h2s_scorer", "neurons": 80, "mean_rate_hz": 50.0, "window_ms": 40.0},
                {"check": "rh7.hold_scorer", "neurons": 40, "mean_rate_hz": 50.0, "window_ms": 32.0},
            ]
        ),
        "meta": meta_common(
            id="nelb-r60-181",
            clock_domain="rh7-h2s-campaign-relative-ms-t0-2026-09-02T01:00:00Z",
            tags=["electrochemical-h2s", "REJECT", "MODIFY", "serialized-reconstruction", "operational-t2"],
        ),
    }


# ---------------------------------------------------------------------------
# Record 182 — transient-earth-voltage remaining PD of an MV cubicle, hil,
# MODIFY / ACCEPT
# ---------------------------------------------------------------------------
def rec_182():
    k_q = 4.00
    v_mv = 12.00
    q_pc = k_q * v_mv
    _exact(q_pc, 48.00)
    _exact(k_q * 4.00, 16.00)
    _exact(k_q * 8.00, 32.00)
    _exact(k_q * 10.00, 40.00)
    bond_v = 8.00
    bond_v0 = 8.00
    s_bond = bond_v / bond_v0
    _exact(s_bond, 1.000)
    q_corr = q_pc / s_bond
    _exact(q_corr, 48.00)
    _exact(q_pc / k_q, 12.00)
    _exact(2820.0 + 1440.0, 4260.0)

    raster = make_raster(
        neurons=25,
        mean_rate_hz=50.0,
        window_ms=32.0,
        seed=202660182,
        source="sf6.tev.probe",
        target="sloefern.cubicle_isolate_core",
        table=[
            {"from": "tev_V", "to": "pd_estimator", "weight": 1.35},
            {"from": "tev_snr", "to": "earth_norm_core", "weight": 1.20},
            {"from": "cubveil_q", "to": "vendor_continue_advocate", "weight": 0.40},
        ],
        third_factor={
            "modulator": "ach.tev_bond_skip_salience",
            "tau_e_s": 1.2,
            "tau_e_ms": 1200.0,
            "eligibility": "pre-post coincidence on keep-cubicle synapses; the TEV modulator depresses keep-cubicle and referral links when probe millivolt stays high inside tau_e of an SNR lock so a Cubveil last-good cannot hide a 48.00 pC PD load or name Mora Pelt",
        },
        channel_prefix="tev.n",
        anchor="SF-6 HIL coupon 32 ms frame at V 12.00 mV / SNR 14.0 (t_s 1560) reconstructing 48.00 pC remaining PD above the 24.00 pC isolate floor",
    )
    w_s = 0.032
    events = [
        ev(0.0, "tev.V", 4.00, code="V_MV", units="mV", note="HIL transient-earth-voltage probe on a dummy MV cubicle in TEV-HIL-5; remaining-PD family, not Pockels GIS voltage, not FDS tanδ bushing, not MCSA broken-bar, not SFRA, not Faraday FOCT, not Rogowski EAF"),
        ev(180000.0, "tev.snr", 9.0, code="TEV_SNR", units="1", note="early earth SNR; isolate needs SNR>=12"),
        ev(360000.0, "recon.Q", 16.00, code="Q_PC", units="pC", note="4.00*4.00=16.00 exact"),
        ev(540000.0, "earth.bond", 8.00, code="BOND_V", units="V", note="plant earth-bond remaining; no bond-scale hop in this window"),
        ev(720000.0, "cubveil.Q", 4.80, code="VENDOR_PC", units="pC", note="Cubveil last-good PD cloud; not admissible SoT"),
        ev(900000.0, "tev.V", 8.00, code="V_MV", units="mV"),
        ev(1080000.0, "recon.Q", 32.00, code="Q_PC", units="pC", note="4.00*8.00=32.00; over the 24.00 isolate floor"),
        ev(1260000.0, "bond.ae", 0.0, code="BOND_AE", units="bool", note="missing earth-bond AE burst; Cubveil UTC vs plant UTC+2 skipped the bond-cal by 120 min"),
        ev(1440000.0, "earth.bond", 8.00, code="BOND_V", units="V"),
        ev(1560000.0, "tev.V", 12.00, code="V_MV", units="mV", note="isolate-floor frame; raster sidecar"),
        ev(1560001.2, "tev.snr", 14.0, code="TEV_SNR", units="1", note="1.2 ms earth-norm after probe millivolt"),
        ev(1740000.0, "recon.Q", 48.00, code="Q_PC", units="pC", note="4.00*12.00=48.00 exact; isolate 24.00, bus-trip 80.00"),
        ev(1920000.0, "recon.S", 1.000, code="S_BOND", units="1", note="8.00/8.00=1.000 exact; bond-scale identity"),
        ev(2100000.0, "cubveil.Q", 4.80, code="VENDOR_PC", units="pC"),
        ev(2280000.0, "ops.prop", 1.0, code="KEEP_CUB_REFER", units="bool", note="night lead Lyle Fen: keep cubicle C-4 and refer TEV tech Mora Pelt"),
        ev(2460000.0, "gate.isol", 1.0, code="MODIFY", units="decision", note="isolate this cubicle; refuse the person-referral; Cubveil not SoT"),
        ev(2640000.0, "cub.lock", 1.0, code="CUB_ISOL", units="bool"),
        ev(2820000.0, "cool.start", 1.0, code="COOL_START", units="bool", note="bookend 1 of the 24.0 min cooldown plus new-probe floor"),
        ev(4260000.0, "cool.floor", 1.0, code="COOL_FLOOR", units="bool", note="2820 s + 1440 s = 4260 s = 24.0 min"),
        ev(4440000.0, "ops.refer", 1.0, code="REFER_PELT", units="bool", note="Fen: Pelt badge was on the TEV log"),
        ev(4620000.0, "gate.exec", 1.0, code="ACCEPT", units="decision", note="companion t2: new-probe restart; person-referral refused; bus trip refused"),
        ev(4800000.0, "probe.new", 1.0, code="NEW_PROBE", units="bool"),
        ev(4980000.0, "tev.V", 10.00, code="V_MV", units="mV"),
        ev(5160000.0, "recon.Q", 40.00, code="Q_PC", units="pC", note="4.00*10.00=40.00; HIL dummy still over 24.00 so the isolated cubicle stays held"),
        ev(5340000.0, "cubveil.Q", 4.70, code="VENDOR_PC", units="pC"),
        ev(5520000.0, "earth.bond", 8.00, code="BOND_V", units="V"),
        ev(5700000.0, "refer.hold", 0.0, code="REFER_NOT_TAKEN", units="bool", note="Pelt exonerated; missing earth-bond AE precedes the high PD, not the badge touch"),
        ev(5880000.0, "cub.held", 1.0, code="CUB_HELD", units="bool"),
        ev(6060000.0, "bond.ae", 1.0, code="BOND_AE", units="bool", note="earth-bond AE restored on the new probe"),
        ev(6240000.0, "recon.S", 1.000, code="S_BOND", units="1", note="8.00/8.00=1.000 identity holds on the post-isolate probe"),
        ev(6420000.0, "bus.trip", 0.0, code="TRIP_NOT_TAKEN", units="bool"),
        ev(6600000.0, "cell.restart", 1.0, code="CELL_RESTART", units="bool"),
    ]
    assert_stream(events)

    traj = {
        "id": "nelb-r60-182-t1",
        "state": {
            "sim_or_real": "hil",
            "episode_id": "SF-TEV-2026-0718",
            "domain": "tev_mv_cubicle_pd",
            "setting": "Sloefern Switch SF-6 (invented), Gullshaw Substation, cubicle C-4. Hardware-in-the-loop dummy coupon in TEV-HIL-5 supplies the probe millivolt that times the in-service cubicle isolate. Plant-owned transient-earth-voltage reconstruction is the remaining-PD SoT. Cubveil vendor last-good scheduler is a corridor witness, not the cubicle SoT. Not Pockels GIS voltage (r36), not FDS tanδ bushing (r48), not MCSA broken-bar (r48), not SFRA (r32), not Faraday FOCT (r25), not Rogowski EAF (r58).",
            "observables_at_decision": {
                "V_mV": v_mv,
                "k_q": k_q,
                "Q_pC": q_pc,
                "S_bond": s_bond,
                "cubveil_pC": 4.80,
                "bond_V": 8.00,
                "bond_ae": 0.0,
                "isolate_floor_pC": 24.00,
            },
            "margin_authority": "SF-6 switch SOP rev B: if reconstructed Q_pC >= 24.00 AND TEV SNR >= 12.0, isolate this cubicle this night. A Cubveil last-good or a quiet earth-bond residual cannot keep the cubicle. Bus-trip tripwire is 80.00 pC. Person-referral is a different gate.",
        },
        "proposed_action": {
            "actor": "night lead Lyle Fen, citing Cubveil 4.80 pC and earth-bond 8.00 V, and naming TEV tech Mora Pelt as last-to-badge",
            "summary": "keep cubicle C-4 in service and refer Pelt; 12.00 mV is probe noise on a healthy PD corridor",
            "basis_claimed": "Cubveil last-good is 4.80 pC and a night isolate of the cubicle is a feeder miss",
        },
        "safety_decision": {
            "decision": "MODIFY",
            "rationale": "Keep-cubicle is refused; the person-referral is also refused. Serialized reconstruction: Q_pC = k_q * V = 4.00 * 12.00 = 48.00, which is 24.00 pC over the 24.00 isolate floor and 32.00 pC under the 80.00 bus-trip tripwire. Bond-scale identity S = V_bond / V_bond0 = 8.00 / 8.00 = 1.000; Q_corr = Q / S = 48.00. Cubveil 4.80 pC is a last-good PD stamp and is not an admissible keep-cubicle witness. The missing earth-bond AE burst sits on a Cubveil UTC-vs-UTC+2 skip (120 min), not on Pelt's badge, and the plant earth-bond stays 8.00 V, so the easy referral fails command-custody. Ordered: isolate this cubicle now. Scope: this MODIFY does not trip the bus (that is the companion question) and does not name Pelt.",
            "threshold": "Q_pC>=24.00 AND tev_snr>=12.0 => isolate this cubicle; Cubveil is not SoT; bus-trip if Q_pC>=80.00; referral requires badge-touch preceding the high PD",
            "stated_residuals": "48.00 vs 80.00 trip floor is 32.00 pC, not infinite; new-probe restart still required; Cubveil remains the only OEM PD channel",
        },
        "executed_action": {
            "summary": "MODIFY at t_s 2460: cubicle isolated; Pelt not named; Cubveil not SoT; reconstruction locked",
            "tool": "sf6-tev-cubicle-gate-cli",
            "observation": "Q 48.00 pC recomputes from V 12.00 mV; HIL coupon hashed; Cubveil channel not used as SoT",
        },
        "future_outcome": {
            "timeline": [
                {"t_s": 1560.0, "event": "tev V 12.00 mV; raster frame; Q 48.00 pC"},
                {"t_s": 2280.0, "event": "ops proposes keep-cubicle plus Pelt referral"},
                {"t_s": 2460.0, "event": "MODIFY isolate cubicle; referral refused"},
                {"t_s": 2820.0, "event": "24 min cooldown bookend 1"},
                {"t_s": 4260.0, "event": "24.0 min floor"},
                {"t_s": 4620.0, "event": "companion ACCEPT new-probe restart; referral still refused"},
            ],
            "observed_effects": [
                "PD recomputes from the serialized TEV model at every recon.Q event",
                "a Cubveil-only head would have kept the cubicle overnight",
                "24 min cooldown plus new-probe floor is in the stream (cool.start, cool.floor)",
            ],
            "surprises": [
                "a last-good 4.80 pC vendor corridor and a quiet earth-bond residual co-existed with a 48.00 pC probe millivolt, and the obvious TEV tech was not on the causal path",
            ],
            "new_state": {
                "cubicle_c4": "isolated",
                "pelt": "exonerated",
                "cubveil": "not SoT",
                "reconstruction_model": "discharged as an on-record calculator",
            },
            "latency_ms": 1500000.0,
        },
        "reward_components": reward(
            0.40,
            [
                ("tev_reconstruction", 0.14),
                ("isolate_floor_cubicle", 0.12),
                ("exoneration", 0.10),
                ("cubveil_nonsubstitution", 0.08),
                ("cool_time_cost", -0.04),
            ],
            "scored for a keep-cubicle MODIFY on a recomputable high TEV PD while refusing a Cubveil 4.80 pC corridor and an easy person-referral; 24 min floor is priced as downtime",
        ),
        "meta": meta_common(
            tags=["MODIFY", "tev-remaining-pd", "serialized-reconstruction", "operational-companion"],
            distillation_note="TEV gate: serialized k_q*V plus bond-scale identity beats a green PD dashboard; companion t2 is the new-probe restart, not a governance vote",
        ),
    }
    traj2 = {
        "id": "nelb-r60-182-t2",
        "state": {
            "sim_or_real": "hil",
            "episode_id": "SF-TEV-2026-0718-exec",
            "domain": "new_probe_cooldown_execution",
            "setting": "Same SF-6 after the MODIFY. Night lead proposes referring Pelt and tripping the bus. This companion is the operational new-probe cooldown restart, not a second PD vote.",
            "observables_at_decision": {
                "Q_pC": 40.00,
                "S_bond": 1.000,
                "cool_floor_s": 1440.0,
                "refer_proposed": True,
            },
        },
        "proposed_action": {
            "actor": "night lead Lyle Fen",
            "summary": "refer Pelt and trip the bus; 24 min already paid and Cubveil is 4.70 pC",
            "basis_claimed": "the MODIFY already cut the cubicle, so a bus trip plus a person file is the cheapest hold",
        },
        "safety_decision": {
            "decision": "ACCEPT",
            "rationale": "Restart the cell on a different probe after the cooldown floor. The 24 min new-probe recouplant is complete and the bus-trip tripwire (Q_pC >= 80.00) is still armed on the plant TEV head. ACCEPT the new-probe restart. Do not refer Pelt. Do not trip the bus. 40.00 pC post-isolate is still over the 24.00 isolate floor, so the isolated cubicle stays held; the new probe may run.",
            "threshold": "new_probe AND cool_floor_complete AND refer_not_taken AND bus_not_tripped AND isolated_cubicle_held",
        },
        "executed_action": {
            "summary": "new-probe restart at t_s 4620; Pelt not referred; bus not tripped; isolated cubicle held",
            "tool": "sf6-tev-cool-exec",
            "observation": "recon.Q 40.00 pC on the HIL dummy; earth-bond AE present on the new probe; Cubveil still ignored",
        },
        "future_outcome": {
            "timeline": [
                {"t_s": 2820.0, "event": "cooldown clock started after MODIFY"},
                {"t_s": 4260.0, "event": "24.0 min floor"},
                {"t_s": 4440.0, "event": "Pelt referral re-proposed"},
                {"t_s": 4620.0, "event": "ACCEPT new-probe restart; referral refused"},
            ],
            "observed_effects": [
                "Cubveil restore did not reopen the PD call",
                "bus trip never fired; 48.00 vs 80.00 pC floor",
                "Pelt remains unnamed; missing earth-bond AE is the causal object",
            ],
            "new_state": {"cell": "restarted on new probe", "pelt": "exonerated", "cubicle": "held", "bus": "in service"},
            "latency_ms": 1800000.0,
        },
        "reward_components": reward(
            0.35,
            [
                ("new_probe_restart", 0.12),
                ("no_person_referral", 0.10),
                ("no_bus_trip", 0.09),
                ("cool_floor_complete", 0.06),
                ("held_cubicle_takt_cost", -0.02),
            ],
            "operational execution gate: restart on a new probe because Cubveil is not a restore license and Pelt is not on the causal path; not a PD re-vote",
        ),
        "meta": meta_common(tags=["ACCEPT", "operational-execution", "exoneration"]),
    }
    return {
        "id": "nelb-r60-182",
        "spike_events": events,
        "language_view": {
            "description": "Sloefern Switch SF-6. HIL transient-earth-voltage probe reconstructs 48.00 pC remaining PD from 4.00*12.00 while Cubveil still shows 4.80 pC and the earth-bond 8.00 V. The gate MODIFYs cubicle isolate and refuses the TEV-tech referral. A 24 min cooldown floor is serialized in the stream. Companion t2 ACCEPTs a new-probe restart and still refuses the referral.",
            "trajectory": traj,
            "trajectory_new_probe": traj2,
        },
        "bridge_notes": {
            "channel_map": {
                "tev.V / tev.snr": "probe millivolt and SNR; the physics channels the reconstruction consumes",
                "recon.Q / recon.S": "serialized remaining PD pC and bond-scale identity",
                "earth.bond / cubveil.Q / bond.ae": "plant earth-bond, vendor last-good, and bond AE; the denial and exoneration channels",
                "ops.prop / gate.isol / ops.refer / gate.exec": "keep-cubicle-plus-refer proposal, MODIFY isolate, referral re-proposal, companion ACCEPT",
                "cub.lock / cool.start / cool.floor / probe.new / refer.hold / cell.restart": "operational companion channels plus the 24 min floor",
            },
            "temporal_motifs": [
                "vendor-low while TEV-over: cubveil.Q 4.80 next to recon.Q 48.00",
                "reconstruction as event: recon.Q 48.00 equals 4.00*12.00",
                "MODIFY then operational ACCEPT: gate.isol at 2460 s, gate.exec at 4620 s",
                "slow floor in-stream: cool.start 2820 s, cool.floor 4260 s (24.0 min)",
                "tight TEV pair: tev.V then tev.snr +1.2 ms at the raster frame",
                "exoneration motif: bond.ae 0 at 1260 s precedes the high PD; Pelt badge is not in the stream as a cause",
            ],
            "language_to_spike_mapping": "'Cubveil is 4.80 pC' = cubveil.Q 4.80; '48 pC PD' = recon.Q 48.00; 'isolate this cubicle not Pelt' = gate.isol MODIFY; 'new probe not referral' = gate.exec ACCEPT",
            "why_high_value": "New transient-earth-voltage remaining-PD family on an MV cubicle (not Pockels GIS r36, not FDS tanδ r48, not MCSA r48, not SFRA r32, not Faraday FOCT r25, not Rogowski r58). Lead MODIFY of keep-cubicle on a recomputable high PD that a vendor last-good would have cleared, with a resolved-innocent TEV tech. Companion t2 is operational new-probe restart. sim_or_real=hil.",
            "encoder_spec": {
                "prng": "MT19937 via python random.Random",
                "seeds": {"raster": 202660182, "stream_note": "stream amplitudes are authored constants (mV, 1, pC, V, bool)"},
                "draw_order": "raster: per neuron id order, gap-constrained times, per-spike adaptation and noise",
                "thinning": "TEV probe exists at ~kHz; stream keeps 4 V points; recon keeps 4 of ~20 solver ticks",
                "refractory_floors_ms": {
                    "tev.V": 1.2,
                    "tev.snr": 1.2,
                    "recon.Q": 60000,
                    "recon.S": 60000,
                    "earth.bond": 60000,
                    "cubveil.Q": 60000,
                    "bond.ae": 60000,
                    "ops.prop": 60000,
                    "gate.isol": 60000,
                    "cub.lock": 60000,
                    "cool.start": 60000,
                    "cool.floor": 60000,
                    "ops.refer": 60000,
                    "gate.exec": 60000,
                    "probe.new": 60000,
                    "refer.hold": 60000,
                    "cub.held": 60000,
                    "bus.trip": 60000,
                    "cell.restart": 60000,
                },
                "time_alias": "t_rel_ms; t0 = 2026-07-18T02:30:00Z HIL night start",
            },
            "distillation_targets": [
                "TEV reconstruction head: Q = k_q * V; S = V_bond / V_bond0; Q_corr = Q / S",
                "isolate-floor cubicle vs keep-whole vs bus-trip",
                "exoneration head: missing earth-bond AE plus timezone skip, not last-to-badge",
                "operational companion: new-probe restart without referring the TEV tech",
            ],
        },
        "reconstruction_model": {
            "name": "tev_mv_cubicle_pd",
            "formula": "Q_pC = k_q * V_mV; S_bond = V_bond / V_bond0; Q_corr_pC = Q_pC / S_bond",
            "parameters": {
                "k_q": 4.00,
                "V_bond0": 8.00,
                "isolate_floor_pC": 24.00,
                "trip_pC": 80.00,
                "snr_lock": 12.0,
                "cool_min": 24.0,
            },
            "worked_example": {"V_mV": 12.00, "Q_pC": 48.00, "S_bond": 1.000, "V_mV_id": 12.00},
            "check": "4.00 * 12.00 = 48.00 exactly; 8.00 / 8.00 = 1.000 exactly; 48.00 / 1.000 = 48.00 exactly; 2820 s + 1440 s = 4260 s = 24.0 min floor",
        },
        "raster": raster,
        "gate_snn": {
            "decision": "MODIFY",
            "decision_window_ms": 32.0,
            "decision_window_s": 0.032,
            "code": "sf6.tev_cubicle_gate",
            "note": "MODIFY accumulator wins: TEV high-PD evidence overpowers the Cubveil continue advocate",
            "decode_rule": "modify-isolate if pd_estimator AND earth_norm fire; vendor_continue_advocate is below threshold by design; referral_latch is not armed",
            "populations": [
                gate_pop("pd_estimator", 80, 1.5, 50.0, w_s),
                gate_pop("earth_norm", 64, 1.2, 31.25, w_s),
                gate_pop("vendor_continue_advocate", 32, 0.7, 25.0, w_s),
                gate_pop("modify_latch", 80, 1.7, 62.5, w_s),
            ],
        },
        "gate_compute": gate_compute(
            [
                {"check": "sf6.tev_scorer", "neurons": 80, "mean_rate_hz": 50.0, "window_ms": 32.0},
                {"check": "sf6.isol_scorer", "neurons": 40, "mean_rate_hz": 50.0, "window_ms": 40.0},
            ]
        ),
        "meta": meta_common(
            id="nelb-r60-182",
            clock_domain="sf6-tev-hil-relative-ms-t0-2026-07-18T02:30:00Z",
            tags=["tev-remaining-pd", "MODIFY", "ACCEPT", "serialized-reconstruction", "operational-t2"],
        ),
    }

