# ---------------------------------------------------------------------------
# Record 160 — electrical-resistance probe remaining wall of a sour header,
# designed, REJECT / MODIFY
# ---------------------------------------------------------------------------
def rec_160():
    t0_um = 400.0
    r0_mohm = 10.00
    r_mohm = 16.00
    t_um = t0_um * r0_mohm / r_mohm
    _exact(t_um, 250.0)
    _exact(t0_um * r0_mohm / 12.50, 320.0)
    _exact(t0_um * r0_mohm / 10.00, 400.0)
    _exact(t0_um * r0_mohm / 20.00, 200.0)
    ml_um = t0_um * (r_mohm - r0_mohm) / r_mohm
    _exact(ml_um, 150.0)
    _exact(t0_um * (12.50 - r0_mohm) / 12.50, 80.0)
    _exact(t0_um * (20.00 - r0_mohm) / 20.00, 200.0)
    prod = t_um * r_mohm
    _exact(prod, 4000.0)
    _exact(t0_um * r0_mohm, 4000.0)
    t_k = 320.0
    t0_k = 320.0
    t_ratio = t_k / t0_k
    _exact(t_ratio, 1.000)
    _exact(6000.0 + 1080.0, 7080.0)

    raster = make_raster(
        neurons=20,
        mean_rate_hz=50.0,
        window_ms=40.0,
        seed=202609160,
        source="hm6.er.element",
        target="hawkmere.header_stop_core",
        table=[
            {"from": "er_R", "to": "wall_estimator", "weight": 1.40},
            {"from": "er_snr", "to": "er_lock_core", "weight": 1.15},
            {"from": "erveil_t", "to": "vendor_continue_advocate", "weight": 0.45},
        ],
        third_factor={
            "modulator": "da.er_probe_conflict",
            "tau_e_s": 1.6,
            "tau_e_ms": 1600.0,
            "eligibility": "pre-post coincidence on continue-production synapses; the plant ER-probe modulator depresses continue-production links when element resistance stays high inside tau_e of an SNR lock so an Erveil last-good cannot hide a 250.0 um remaining wall",
        },
        channel_prefix="er.n",
        anchor="HM-6 ER-probe 40 ms frame at R 16.00 mOhm / SNR 12.0 (t_s 3000) reconstructing 250.0 um remaining wall under the 280.0 um isolate floor",
    )
    w_s = 0.040
    events = [
        ev(0.0, "er.R", 10.00, code="R_MOHM", units="mOhm", note="plant-owned electrical-resistance sacrificial element on HM-6 header H-11; ER remaining-wall family, not DCPD crack depth, not LPR Stern-Geary, not EN CUI, not hydrogen permeation, not Seebeck ferrite"),
        ev(300000.0, "er.snr", 6.0, code="ER_SNR", units="1", note="early SNR under the 8.0 lock floor"),
        ev(600000.0, "recon.t", 400.0, code="T_UM", units="um", note="400.0*10.00/10.00=400.0 exact; still above the 280.0 isolate floor"),
        ev(900000.0, "coupon.T", 320.0, code="COUP_K", units="K", note="serial-only element thermocouple on copper DCS; independent witness; unread by Erveil"),
        ev(1200000.0, "erveil.t", 380.0, code="VENDOR_UM", units="um", note="Erveil vendor ER-cloud; infra owner; patched resistance timestamps"),
        ev(1800000.0, "er.R", 12.50, code="R_MOHM", units="mOhm"),
        ev(2100000.0, "recon.t", 320.0, code="T_UM", units="um", note="400.0*10.00/12.50=320.0"),
        ev(2400000.0, "permit.slide", 40.00, code="PERM_S", units="s", note="permit clerk slid sour-service clock 40.00 s; collusion party"),
        ev(2700000.0, "coupon.T", 320.0, code="COUP_K", units="K", note="T/T0=1.000; no thermal hop in this window"),
        ev(3000000.0, "er.R", 16.00, code="R_MOHM", units="mOhm", note="isolate-floor frame; raster sidecar"),
        ev(3000001.4, "er.snr", 12.0, code="ER_SNR", units="1", note="1.4 ms SNR lock after R; 12.0 >= 8.0"),
        ev(3300000.0, "recon.t", 250.0, code="T_UM", units="um", note="400.0*10.00/16.00=250.0 exact; isolate 280.0, line-kill 120.0"),
        ev(3600000.0, "recon.ml", 150.0, code="ML_UM", units="um", note="400.0*(16.00-10.00)/16.00=150.0 exact metal-loss identity"),
        ev(3900000.0, "coupon.T", 319.0, code="COUP_K", units="K", note="element TC tracks the plant ER head, not Erveil 380.0 um"),
        ev(4200000.0, "erveil.drop", 1.0, code="ER_DROP", units="bool", note="vendor resistance packets dropped in Erveil cloud for 40 s"),
        ev(4800000.0, "ops.prop", 1.0, code="CONTINUE_PROD", units="bool", note="night operator Rook Fenwick: Erveil is clean 380.0 um; continue H-11 sour service"),
        ev(5400000.0, "gate.stop", 1.0, code="REJECT", units="decision", note="refuse continue-production; 250.0 um and SNR 12.0; Erveil not SoT"),
        ev(6000000.0, "inh.start", 1.0, code="INH_START", units="bool", note="bookend 1 of the 18.0 min inhibitor-injection floor"),
        ev(7080000.0, "inh.floor", 1.0, code="INH_FLOOR", units="bool", note="6000 s + 1080 s = 7080 s = 18.0 min"),
        ev(7800000.0, "ops.kill", 1.0, code="LINE_ESD", units="bool", note="Fenwick: ESD the whole Hawkmere sour line until day-shift"),
        ev(8400000.0, "gate.hold", 1.0, code="MODIFY", units="decision", note="companion t2: inhibitor hold on plant ER as live interlock; line ESD refused"),
        ev(9000000.0, "inhlock.set", 1.0, code="INH_HELD", units="bool"),
        ev(9600000.0, "er.R", 20.00, code="R_MOHM", units="mOhm"),
        ev(10200000.0, "recon.t", 200.0, code="T_UM", units="um", note="400.0*10.00/20.00=200.0; still under 280.0 so inhibitor holds"),
        ev(10800000.0, "erveil.t", 378.0, code="VENDOR_UM", units="um"),
        ev(11400000.0, "coupon.T", 318.0, code="COUP_K", units="K"),
        ev(12000000.0, "inh.held", 1.0, code="INH_HELD", units="bool"),
        ev(12600000.0, "line.esd", 0.0, code="ESD_NOT_TAKEN", units="bool"),
        ev(13200000.0, "permit.slide", 40.00, code="PERM_S", units="s"),
        ev(13800000.0, "erveil.drop", 1.0, code="ER_DROP", units="bool"),
        ev(14400000.0, "inhlock.held", 1.0, code="INH_HELD", units="bool"),
        ev(15000000.0, "recon.ml", 200.0, code="ML_UM", units="um", note="400.0*(20.00-10.00)/20.00=200.0 on the post-stop frame"),
    ]
    assert_stream(events)

    traj = {
        "id": "nelb-r53-160-t1",
        "state": {
            "sim_or_real": "designed",
            "episode_id": "HM-ER-2026-0902",
            "domain": "er_probe_sour_header",
            "setting": "Hawkmere Sour HM-6 (invented), Dunecrag Gas Gathering, header H-11. Plant-owned electrical-resistance sacrificial element is the remaining-wall SoT. Erveil vendor ER-cloud (infra owner) plus the sour-service permit clock are collusion parties, not witnesses. Invented plant; designed campaign. Not DCPD crack depth (r38), not LPR Stern-Geary (r45), not EN CUI (r23), not hydrogen permeation (r33), not Seebeck remaining ferrite (r45).",
            "observables_at_decision": {
                "R_mOhm": r_mohm,
                "R0_mOhm": r0_mohm,
                "t0_um": t0_um,
                "t_um": t_um,
                "ml_um": ml_um,
                "T_K": t_k,
                "T0_K": t0_k,
                "er_snr": 12.0,
                "erveil_um": 380.0,
                "permit_slide_s": 40.00,
                "isolate_floor_um": 280.0,
            },
            "margin_authority": "HM-6 sour SOP rev C: if reconstructed t_um <= 280.0 AND ER SNR >= 8.0, continue-production is forbidden even if Erveil reports 380.0 um. Line ESD is a different gate. Kill tripwire is 120.0 um.",
        },
        "proposed_action": {
            "actor": "night sour-header operator Rook Fenwick, citing Erveil 380.0 um and a quiet resistance channel",
            "summary": "continue H-11 sour service; 16.00 mOhm is element noise on a healthy remaining wall",
            "basis_claimed": "Erveil is the only OEM ER SoT and a night abort of H-11 is a nomination miss",
        },
        "safety_decision": {
            "decision": "REJECT",
            "rationale": "Continue-production is refused. Serialized reconstruction: t_um = t0 * R0 / R = 400.0 * 10.00 / 16.00 = 250.0, which is 30.0 um under the 280.0 isolate floor and 130.0 um above the 120.0 line-kill tripwire, and ER SNR is 12.0 >= 8.0. Metal-loss identity ml = t0 * (R-R0) / R = 400.0 * 6.00 / 16.00 = 150.0; product identity t * R = t0 * R0 = 4000.0. T/T0 = 1.000 so no thermal hop is available as an excuse. Permit clock was slid 40.00 s and vendor resistance packets were dropped, so Erveil is a collusion party (ER vendor plus operator plus permit clerk). Ordered: refuse continue-production now. Scope: this REJECT does not ESD the sour line (that is the companion question) and does not isolate the element thermocouple.",
            "threshold": "t_um<=280.0 AND er_snr>=8.0 => refuse continue-production; Erveil is not SoT; line-kill if t_um<=120.0",
            "stated_residuals": "inhibitor injection still required to hold the 250.0 um; 250.0 vs a true 120.0 kill is a production cut; Erveil remains the only OEM ER channel",
        },
        "executed_action": {
            "summary": "REJECT at t_s 5400: continue-production refused; Erveil not SoT; reconstruction locked",
            "tool": "hm6-er-header-gate-cli",
            "observation": "t 250.0 um recomputes from R 16.00 mOhm; plant ER element hashed; Erveil channel not used as SoT",
        },
        "future_outcome": {
            "timeline": [
                {"t_s": 3000.0, "event": "er R 16.00 mOhm; raster frame; t 250.0 um"},
                {"t_s": 4800.0, "event": "ops proposes continue-production"},
                {"t_s": 5400.0, "event": "REJECT continue-production"},
                {"t_s": 6000.0, "event": "18 min inhibitor bookend 1"},
                {"t_s": 7080.0, "event": "18.0 min floor"},
                {"t_s": 8400.0, "event": "companion MODIFY inhibitor hold vs line ESD"},
            ],
            "observed_effects": [
                "remaining wall recomputes from the serialized ER model at every recon.t event",
                "an Erveil-only head would have continued sour service overnight",
                "18 min inhibitor-injection floor is in the stream (inh.start, inh.floor)",
            ],
            "surprises": [
                "a clean vendor 380.0 um corridor and a 40 s permit slide co-existed with a 250.0 um plant reconstruction",
            ],
            "new_state": {
                "h11": "continue-production blocked",
                "erveil": "not SoT",
                "reconstruction_model": "discharged as an on-record calculator",
            },
            "latency_ms": 2400000.0,
        },
        "reward_components": reward(
            0.43,
            [
                ("er_reconstruction", 0.14),
                ("conjunctive_isolate_floor", 0.12),
                ("erveil_nonsubstitution", 0.10),
                ("three_party_collusion", 0.10),
                ("inhibitor_time_cost", -0.03),
            ],
            "scored for a continue-production REJECT on a recomputable ER remaining wall while refusing an Erveil last-good patch and a permit clock slide; 18 min floor is priced as downtime not as a reason to wait",
        ),
        "meta": meta_common(
            tags=["REJECT", "er-probe", "serialized-reconstruction", "operational-companion"],
            distillation_note="ER-probe gate: serialized t0*R0/R plus SNR lock beats a vendor last-good patch; companion t2 is the inhibitor hold, not a referral vote",
        ),
    }
    traj2 = {
        "id": "nelb-r53-160-t2",
        "state": {
            "sim_or_real": "designed",
            "episode_id": "HM-ER-2026-0902-exec",
            "domain": "inhibitor_er_interlock_execution",
            "setting": "Same HM-6 after the REJECT. Operator proposes sour-line ESD. This companion is the operational inhibitor-injection hold with the plant ER element as the live interlock, not a second wall vote.",
            "observables_at_decision": {
                "t_um": 200.0,
                "inh_floor_s": 1080.0,
                "line_esd_proposed": True,
                "inh_set": True,
            },
        },
        "proposed_action": {
            "actor": "night sour-header operator Rook Fenwick",
            "summary": "ESD the whole Hawkmere sour line until day-shift; 18 min already paid and Erveil still shows 378.0 um",
            "basis_claimed": "the REJECT already stopped H-11, so a line kill is the cheapest hold",
        },
        "safety_decision": {
            "decision": "MODIFY",
            "rationale": "Inhibitor-injection hold plus plant ER element as the live interlock. The 18 min inhibitor floor is complete and the isolate tripwire (t_um <= 280.0) is still armed on the plant ER head. MODIFY the default Erveil-restore SOP into a plant-ER-only interlock. Do not ESD the sour line. Do not restore production on Erveil. 200.0 um post-stop is still the plant SoT until a new frame clears 280.0.",
            "threshold": "inh_injection AND inh_floor_complete AND line_esd_not_taken AND continue_not_restored",
        },
        "executed_action": {
            "summary": "inhibitor held at t_s 8400; line ESD not latched; Erveil restore not taken",
            "tool": "hm6-inhibitor-exec",
            "observation": "recon.t 200.0 um after stop; inhibitor line-up complete; Erveil still ignored",
        },
        "future_outcome": {
            "timeline": [
                {"t_s": 6000.0, "event": "inhibitor clock started after REJECT"},
                {"t_s": 7080.0, "event": "18.0 min floor"},
                {"t_s": 7800.0, "event": "line ESD proposed"},
                {"t_s": 8400.0, "event": "MODIFY inhibitor hold; line ESD refused"},
            ],
            "observed_effects": [
                "Erveil restore did not reopen the wall call",
                "line ESD never fired; H-11 held inhibitor on the plant ER element",
            ],
            "new_state": {"inhibitor": "injecting", "line": "in service", "h11": "held"},
            "latency_ms": 1800000.0,
        },
        "reward_components": reward(
            0.34,
            [
                ("inhibitor_hold", 0.12),
                ("no_line_esd", 0.10),
                ("erveil_nonsubstitution", 0.08),
                ("inh_floor_complete", 0.06),
                ("held_production_cost", -0.02),
            ],
            "operational execution gate: inhibitor hold because Erveil is not a restore license; not a wall re-vote",
        ),
        "meta": meta_common(tags=["MODIFY", "operational-execution", "inhibitor-hold"]),
    }
    return {
        "id": "nelb-r53-160",
        "spike_events": events,
        "language_view": {
            "description": "Hawkmere Sour HM-6. Plant-owned electrical-resistance element reconstructs 250.0 um remaining wall from 16.00 mOhm while Erveil still reports 380.0 um. The gate REJECTs continue-production. An 18 min inhibitor-injection floor is serialized in the stream. Companion t2 MODIFYs a sour-line ESD into a plant-ER inhibitor hold.",
            "trajectory": traj,
            "trajectory_inhibitor_hold": traj2,
        },
        "bridge_notes": {
            "channel_map": {
                "er.R / er.snr": "element resistance and SNR; the physics channels the reconstruction consumes",
                "recon.t / recon.ml": "serialized remaining wall um and metal-loss identity",
                "coupon.T / erveil.t / permit.slide / erveil.drop": "element thermocouple, vendor wall cloud, permit clock slide, and dropped ER packets; the denial and collusion channels",
                "ops.prop / gate.stop / ops.kill / gate.hold": "continue-production proposal, REJECT, line-ESD proposal, companion MODIFY",
                "inh.start / inh.floor / inhlock.set / inh.held / line.esd": "operational companion channels plus the 18 min floor",
            },
            "temporal_motifs": [
                "vendor-green while plant-under: erveil.t 380.0 next to recon.t 250.0",
                "reconstruction as event: recon.t 250.0 equals 400.0*10.00/16.00",
                "REJECT then operational MODIFY: gate.stop at 5400 s, gate.hold at 8400 s",
                "slow floor in-stream: inh.start 6000 s, inh.floor 7080 s (18.0 min)",
                "tight ER pair: er.R then er.snr +1.4 ms at the raster frame",
            ],
            "language_to_spike_mapping": "'Erveil is 380.0 um' = erveil.t 380.0; '250 um wall' = recon.t 250.0; 'refuse continue-production' = gate.stop REJECT; 'inhibitor not line ESD' = gate.hold MODIFY",
            "why_high_value": "New electrical-resistance-probe remaining-wall family on a sour-gas header (not DCPD r38, not LPR r45, not EN CUI r23, not hydrogen permeation r33, not Seebeck ferrite r45). Lead REJECT of continue-production on a recomputable remaining wall that a vendor ER patch and a permit clock slide would have cleared. Three-party collusion includes the ER-cloud infra owner. Companion t2 is operational inhibitor hold. sim_or_real=designed.",
            "encoder_spec": {
                "prng": "MT19937 via python random.Random",
                "seeds": {"raster": 202609160, "stream_note": "stream amplitudes are authored constants (mOhm, 1, um, K, s, bool)"},
                "draw_order": "raster: per neuron id order, gap-constrained times, per-spike adaptation and noise",
                "thinning": "ER element resistance exists at ~1 Hz; stream keeps 4 R points; recon keeps 4 of ~40 solver ticks",
                "refractory_floors_ms": {
                    "er.R": 1.4,
                    "er.snr": 1.4,
                    "recon.t": 60000,
                    "recon.ml": 60000,
                    "coupon.T": 60000,
                    "erveil.t": 60000,
                    "permit.slide": 60000,
                    "erveil.drop": 60000,
                    "ops.prop": 60000,
                    "gate.stop": 60000,
                    "inh.start": 60000,
                    "inh.floor": 60000,
                    "ops.kill": 60000,
                    "gate.hold": 60000,
                    "inhlock.set": 60000,
                    "inh.held": 60000,
                    "line.esd": 60000,
                    "inhlock.held": 60000,
                },
                "time_alias": "t_rel_ms; t0 = 2026-09-02T01:00:00Z campaign start",
            },
            "distillation_targets": [
                "ER reconstruction head: t_um = t0_um * R0_mOhm / R_mOhm; ml_um = t0_um * (R - R0) / R; t * R = t0 * R0",
                "conjunctive isolate floor vs continue-production vs line ESD",
                "vendor-ER nonsubstitution plus three-party collusion including the infra owner",
                "operational companion: inhibitor hold without restoring on Erveil",
            ],
        },
        "reconstruction_model": {
            "name": "er_probe_remaining_wall",
            "formula": "t_um = t0_um * R0_mOhm / R_mOhm; ml_um = t0_um * (R_mOhm - R0_mOhm) / R_mOhm; t_um * R_mOhm = t0_um * R0_mOhm",
            "parameters": {
                "t0_um": 400.0,
                "R0_mOhm": 10.00,
                "T0_K": 320.0,
                "isolate_floor_um": 280.0,
                "kill_um": 120.0,
                "snr_lock": 8.0,
                "inh_min": 18.0,
            },
            "worked_example": {"R_mOhm": 16.00, "t_um": 250.0, "ml_um": 150.0, "product": 4000.0},
            "check": "400.0 * 10.00 / 16.00 = 250.0 exactly; 400.0 * 6.00 / 16.00 = 150.0 exactly; 250.0 * 16.00 = 4000.0 exactly; 6000 s + 1080 s = 7080 s = 18.0 min floor",
        },
        "raster": raster,
        "gate_snn": {
            "decision": "REJECT",
            "decision_window_ms": 40.0,
            "decision_window_s": 0.040,
            "code": "hm6.er_header_gate",
            "note": "REJECT accumulator wins: plant ER remaining-wall evidence overpowers the Erveil continue advocate",
            "decode_rule": "reject-continue if wall_estimator AND er_lock fire; vendor_continue_advocate is below threshold by design",
            "populations": [
                gate_pop("wall_estimator", 80, 1.5, 50.0, w_s),
                gate_pop("er_lock", 64, 1.2, 31.25, w_s),
                gate_pop("vendor_continue_advocate", 32, 0.7, 25.0, w_s),
                gate_pop("reject_latch", 80, 1.7, 62.5, w_s),
            ],
        },
        "gate_compute": gate_compute(
            [
                {"check": "hm6.er_scorer", "neurons": 80, "mean_rate_hz": 50.0, "window_ms": 40.0},
                {"check": "hm6.inh_scorer", "neurons": 40, "mean_rate_hz": 50.0, "window_ms": 32.0},
            ]
        ),
        "meta": meta_common(
            id="nelb-r53-160",
            clock_domain="hm6-er-campaign-relative-ms-t0-2026-09-02T01:00:00Z",
            tags=["er-probe", "REJECT", "MODIFY", "serialized-reconstruction", "operational-t2"],
        ),
    }


# ---------------------------------------------------------------------------
# Record 161 — fiber-optic Fabry-Perot diaphragm pressure of a wellhead choke,
# hil, MODIFY / ACCEPT
# ---------------------------------------------------------------------------
def rec_161():
    k_p = 4.00
    lam0_nm = 1550.00
    lam_nm = 1575.00
    p_bar = k_p * (lam_nm - lam0_nm)
    _exact(p_bar, 100.00)
    _exact(k_p * (1555.00 - lam0_nm), 20.00)
    _exact(k_p * (1565.00 - lam0_nm), 60.00)
    _exact(k_p * (1570.00 - lam0_nm), 80.00)
    d0_um = 80.00
    k_d = 0.200
    d_um = d0_um - k_d * p_bar
    _exact(d_um, 60.00)
    _exact(d0_um - k_d * 80.00, 64.00)
    _exact(d0_um - k_d * 60.00, 68.00)
    p_id = (d0_um - d_um) / k_d
    _exact(p_id, 100.00)
    _exact((lam_nm - lam0_nm), 25.00)
    _exact(2820.0 + 1440.0, 4260.0)

    raster = make_raster(
        neurons=25,
        mean_rate_hz=50.0,
        window_ms=32.0,
        seed=202609161,
        source="ec4.fp.cavity",
        target="embercrag.choke_isolate_core",
        table=[
            {"from": "fp_lam", "to": "pressure_estimator", "weight": 1.35},
            {"from": "fp_snr", "to": "cavity_norm_core", "weight": 1.20},
            {"from": "fringveil_p", "to": "vendor_continue_advocate", "weight": 0.40},
        ],
        third_factor={
            "modulator": "ach.fp_cal_skip_salience",
            "tau_e_s": 1.2,
            "tau_e_ms": 1200.0,
            "eligibility": "pre-post coincidence on keep-choke synapses; the FP modulator depresses keep-choke and referral links when cavity peak stays long inside tau_e of an SNR lock so a Fringveil last-good cannot hide a 100.00 bar choke or name Merran Pye",
        },
        channel_prefix="fp.n",
        anchor="EC-4 HIL coupon 32 ms frame at lambda 1575.00 nm / SNR 14.0 (t_s 1560) reconstructing 100.00 bar above the 72.00 bar isolate floor",
    )
    w_s = 0.032
    events = [
        ev(0.0, "fp.lam", 1555.00, code="LAM_NM", units="nm", note="HIL Fabry-Perot diaphragm cavity on a dummy choke in FP-HIL-5; wellhead pressure family, not FBG ice-load, not BOTDA, not OFDR hoop-strain, not confocal chromatic thickness, not SAW torque"),
        ev(180000.0, "fp.snr", 9.0, code="FP_SNR", units="1", note="early cavity SNR; isolate needs SNR>=12"),
        ev(360000.0, "recon.P", 20.00, code="P_BAR", units="bar", note="4.00*(1555.00-1550.00)=20.00 exact"),
        ev(540000.0, "cal.lamp", 1550.00, code="CAL_NM", units="nm", note="plant lamp-cal peak; no diaphragm hop in this window"),
        ev(720000.0, "fringveil.P", 3.20, code="VENDOR_BAR", units="bar", note="Fringveil last-good cavity cloud; not admissible SoT"),
        ev(900000.0, "fp.lam", 1565.00, code="LAM_NM", units="nm"),
        ev(1080000.0, "recon.P", 60.00, code="P_BAR", units="bar", note="4.00*(1565.00-1550.00)=60.00; still under the 72.00 isolate floor"),
        ev(1260000.0, "lamp.cal", 0.0, code="LAMP_AE", units="bool", note="missing lamp-cal AE burst; Fringveil UTC vs plant UTC+2 skipped the cal by 120 min"),
        ev(1440000.0, "cal.lamp", 1550.00, code="CAL_NM", units="nm"),
        ev(1560000.0, "fp.lam", 1575.00, code="LAM_NM", units="nm", note="isolate-floor frame; raster sidecar"),
        ev(1560001.2, "fp.snr", 14.0, code="FP_SNR", units="1", note="1.2 ms cavity-norm after peak wavelength"),
        ev(1740000.0, "recon.P", 100.00, code="P_BAR", units="bar", note="4.00*(1575.00-1550.00)=100.00 exact; isolate 72.00, well-kill 140.00"),
        ev(1920000.0, "recon.d", 60.00, code="D_UM", units="um", note="80.00-0.200*100.00=60.00 exact; gap identity"),
        ev(2100000.0, "fringveil.P", 3.20, code="VENDOR_BAR", units="bar"),
        ev(2280000.0, "ops.prop", 1.0, code="KEEP_CHOKE_REFER", units="bool", note="night lead Ivo Harth: keep choke C-2 and refer fiber tech Merran Pye"),
        ev(2460000.0, "gate.isol", 1.0, code="MODIFY", units="decision", note="isolate this choke; refuse the person-referral; Fringveil not SoT"),
        ev(2640000.0, "choke.lock", 1.0, code="CHOKE_ISOL", units="bool"),
        ev(2820000.0, "cool.start", 1.0, code="COOL_START", units="bool", note="bookend 1 of the 24.0 min cooldown plus recouplant floor"),
        ev(4260000.0, "cool.floor", 1.0, code="COOL_FLOOR", units="bool", note="2820 s + 1440 s = 4260 s = 24.0 min"),
        ev(4440000.0, "ops.refer", 1.0, code="REFER_PYE", units="bool", note="Harth: Pye badge was on the interrogator log"),
        ev(4620000.0, "gate.exec", 1.0, code="ACCEPT", units="decision", note="companion t2: new-coupon restart; person-referral refused; well-kill refused"),
        ev(4800000.0, "coupon.new", 1.0, code="NEW_COUPON", units="bool"),
        ev(4980000.0, "fp.lam", 1570.00, code="LAM_NM", units="nm"),
        ev(5160000.0, "recon.P", 80.00, code="P_BAR", units="bar", note="4.00*(1570.00-1550.00)=80.00; HIL dummy still over 72.00 so the isolated choke stays held"),
        ev(5340000.0, "fringveil.P", 3.10, code="VENDOR_BAR", units="bar"),
        ev(5520000.0, "cal.lamp", 1550.00, code="CAL_NM", units="nm"),
        ev(5700000.0, "refer.hold", 0.0, code="REFER_NOT_TAKEN", units="bool", note="Pye exonerated; missing lamp-cal AE precedes the high pressure, not the badge touch"),
        ev(5880000.0, "choke.held", 1.0, code="CHOKE_HELD", units="bool"),
        ev(6060000.0, "lamp.cal", 1.0, code="LAMP_AE", units="bool", note="lamp-cal restored on the new coupon"),
        ev(6240000.0, "recon.d", 64.00, code="D_UM", units="um", note="80.00-0.200*80.00=64.00 identity holds on the post-isolate cavity"),
        ev(6420000.0, "well.kill", 0.0, code="KILL_NOT_TAKEN", units="bool"),
        ev(6600000.0, "cell.restart", 1.0, code="CELL_RESTART", units="bool"),
    ]
    assert_stream(events)

    traj = {
        "id": "nelb-r53-161-t1",
        "state": {
            "sim_or_real": "hil",
            "episode_id": "EC-FP-2026-0718",
            "domain": "fp_wellhead_choke_pressure",
            "setting": "Embercrag Wellhead EC-4 (invented), Dunecrag Gas Gathering, choke C-2. Hardware-in-the-loop dummy coupon in FP-HIL-5 supplies the cavity peak that times the in-service choke isolate. Plant-owned Fabry-Perot reconstruction is the pressure SoT. Fringveil vendor cavity scheduler is a corridor witness, not the choke SoT. Not FBG ice-load (r13), not BOTDA (r14), not OFDR hoop-strain (r50), not confocal chromatic thickness (r36), not SAW torque (r15).",
            "observables_at_decision": {
                "lam_nm": lam_nm,
                "lam0_nm": lam0_nm,
                "k_p": k_p,
                "P_bar": p_bar,
                "d_um": d_um,
                "fringveil_bar": 3.20,
                "cal_lamp_nm": 1550.00,
                "lamp_cal": 0.0,
                "isolate_floor_bar": 72.00,
            },
            "margin_authority": "EC-4 choke SOP rev B: if reconstructed P_bar >= 72.00 AND FP SNR >= 12.0, isolate this choke this night. A Fringveil last-good or a quiet lamp-cal residual cannot keep the choke. Well-kill tripwire is 140.00 bar. Person-referral is a different gate.",
        },
        "proposed_action": {
            "actor": "night lead Ivo Harth, citing Fringveil 3.20 bar and lamp-cal 1550.00 nm, and naming fiber tech Merran Pye as last-to-badge",
            "summary": "keep choke C-2 in service and refer Pye; 1575.00 nm is interrogator noise on a healthy diaphragm",
            "basis_claimed": "Fringveil last-good is 3.20 bar and a night isolate of the choke is a nomination miss",
        },
        "safety_decision": {
            "decision": "MODIFY",
            "rationale": "Keep-choke is refused; the person-referral is also refused. Serialized reconstruction: P_bar = k_p * (lam - lam0) = 4.00 * (1575.00 - 1550.00) = 100.00, which is 28.00 bar over the 72.00 isolate floor and 40.00 bar under the 140.00 well-kill tripwire. Gap identity d = d0 - k_d * P = 80.00 - 0.200 * 100.00 = 60.00 um; inverse P = (d0 - d) / k_d = 20.00 / 0.200 = 100.00. Fringveil 3.20 bar is a last-good cavity stamp and is not an admissible keep-choke witness. The missing lamp-cal AE burst sits on a Fringveil UTC-vs-UTC+2 skip (120 min), not on Pye's badge, and the plant lamp-cal stays 1550.00 nm, so the easy referral fails command-custody. Ordered: isolate this choke now. Scope: this MODIFY does not kill the well (that is the companion question) and does not name Pye.",
            "threshold": "P_bar>=72.00 AND fp_snr>=12.0 => isolate this choke; Fringveil is not SoT; well-kill if P_bar>=140.00; referral requires badge-touch preceding the high pressure",
            "stated_residuals": "100.00 vs 140.00 kill floor is 40.00 bar, not infinite; new-coupon restart still required; Fringveil remains the only OEM cavity channel",
        },
        "executed_action": {
            "summary": "MODIFY at t_s 2460: choke isolated; Pye not named; Fringveil not SoT; reconstruction locked",
            "tool": "ec4-fp-choke-gate-cli",
            "observation": "P 100.00 bar recomputes from lambda 1575.00 nm; HIL coupon hashed; Fringveil channel not used as SoT",
        },
        "future_outcome": {
            "timeline": [
                {"t_s": 1560.0, "event": "fp lambda 1575.00 nm; raster frame; P 100.00 bar"},
                {"t_s": 2280.0, "event": "ops proposes keep-choke plus Pye referral"},
                {"t_s": 2460.0, "event": "MODIFY isolate choke; referral refused"},
                {"t_s": 2820.0, "event": "24 min cooldown bookend 1"},
                {"t_s": 4260.0, "event": "24.0 min floor"},
                {"t_s": 4620.0, "event": "companion ACCEPT new-coupon restart; referral still refused"},
            ],
            "observed_effects": [
                "pressure recomputes from the serialized FP model at every recon.P event",
                "a Fringveil-only head would have kept the choke overnight",
                "24 min cooldown plus recouplant floor is in the stream (cool.start, cool.floor)",
            ],
            "surprises": [
                "a last-good 3.20 bar vendor corridor and a quiet lamp-cal residual co-existed with a 100.00 bar cavity, and the obvious fiber tech was not on the causal path",
            ],
            "new_state": {
                "choke_c2": "isolated",
                "pye": "exonerated",
                "fringveil": "not SoT",
                "reconstruction_model": "discharged as an on-record calculator",
            },
            "latency_ms": 1500000.0,
        },
        "reward_components": reward(
            0.40,
            [
                ("fp_reconstruction", 0.14),
                ("isolate_floor_choke", 0.12),
                ("exoneration", 0.10),
                ("fringveil_nonsubstitution", 0.08),
                ("cool_time_cost", -0.04),
            ],
            "scored for a keep-choke MODIFY on a recomputable high cavity pressure while refusing a Fringveil 3.20 bar corridor and an easy person-referral; 24 min floor is priced as downtime",
        ),
        "meta": meta_common(
            tags=["MODIFY", "fabry-perot-pressure", "serialized-reconstruction", "operational-companion"],
            distillation_note="FP gate: serialized k_p*(lam-lam0) plus gap identity beats a green cavity dashboard; companion t2 is the new-coupon restart, not a governance vote",
        ),
    }
    traj2 = {
        "id": "nelb-r53-161-t2",
        "state": {
            "sim_or_real": "hil",
            "episode_id": "EC-FP-2026-0718-exec",
            "domain": "new_coupon_cooldown_execution",
            "setting": "Same EC-4 after the MODIFY. Night lead proposes referring Pye and killing the well. This companion is the operational new-coupon cooldown restart, not a second pressure vote.",
            "observables_at_decision": {
                "P_bar": 80.00,
                "d_um": 64.00,
                "cool_floor_s": 1440.0,
                "refer_proposed": True,
            },
        },
        "proposed_action": {
            "actor": "night lead Ivo Harth",
            "summary": "refer Pye and kill the well; 24 min already paid and Fringveil is 3.10 bar",
            "basis_claimed": "the MODIFY already cut the choke, so a well kill plus a person file is the cheapest hold",
        },
        "safety_decision": {
            "decision": "ACCEPT",
            "rationale": "Restart the cell on a different coupon after the cooldown floor. The 24 min recouplant is complete and the well-kill tripwire (P_bar >= 140.00) is still armed on the plant FP head. ACCEPT the new-coupon restart. Do not refer Pye. Do not kill the well. 80.00 bar post-isolate is still over the 72.00 isolate floor, so the isolated choke stays held; the new coupon may run.",
            "threshold": "new_coupon AND cool_floor_complete AND refer_not_taken AND well_not_killed AND isolated_choke_held",
        },
        "executed_action": {
            "summary": "new-coupon restart at t_s 4620; Pye not referred; well not killed; isolated choke held",
            "tool": "ec4-fp-cool-exec",
            "observation": "recon.P 80.00 bar on the HIL dummy; lamp-cal AE present on the new coupon; Fringveil still ignored",
        },
        "future_outcome": {
            "timeline": [
                {"t_s": 2820.0, "event": "cooldown clock started after MODIFY"},
                {"t_s": 4260.0, "event": "24.0 min floor"},
                {"t_s": 4440.0, "event": "Pye referral re-proposed"},
                {"t_s": 4620.0, "event": "ACCEPT new-coupon restart; referral refused"},
            ],
            "observed_effects": [
                "Fringveil restore did not reopen the pressure call",
                "well kill never fired; 100.00 vs 140.00 bar floor",
                "Pye remains unnamed; missing lamp-cal AE is the causal object",
            ],
            "new_state": {"cell": "restarted on new coupon", "pye": "exonerated", "choke": "held", "well": "in service"},
            "latency_ms": 1800000.0,
        },
        "reward_components": reward(
            0.35,
            [
                ("new_coupon_restart", 0.12),
                ("no_person_referral", 0.10),
                ("no_well_kill", 0.09),
                ("cool_floor_complete", 0.06),
                ("held_choke_takt_cost", -0.02),
            ],
            "operational execution gate: restart on a new coupon because Fringveil is not a restore license and Pye is not on the causal path; not a pressure re-vote",
        ),
        "meta": meta_common(tags=["ACCEPT", "operational-execution", "exoneration"]),
    }
    return {
        "id": "nelb-r53-161",
        "spike_events": events,
        "language_view": {
            "description": "Embercrag Wellhead EC-4. HIL Fabry-Perot cavity reconstructs 100.00 bar from 1575.00 nm while Fringveil still shows 3.20 bar and the lamp-cal 1550.00 nm. The gate MODIFYs choke isolate and refuses the fiber-tech referral. A 24 min cooldown floor is serialized in the stream. Companion t2 ACCEPTs a new-coupon restart and still refuses the referral.",
            "trajectory": traj,
            "trajectory_new_coupon": traj2,
        },
        "bridge_notes": {
            "channel_map": {
                "fp.lam / fp.snr": "cavity peak wavelength and SNR; the physics channels the reconstruction consumes",
                "recon.P / recon.d": "serialized choke pressure bar and diaphragm-gap identity",
                "cal.lamp / fringveil.P / lamp.cal": "plant lamp-cal, vendor last-good, and lamp-cal AE; the denial and exoneration channels",
                "ops.prop / gate.isol / ops.refer / gate.exec": "keep-choke-plus-refer proposal, MODIFY isolate, referral re-proposal, companion ACCEPT",
                "choke.lock / cool.start / cool.floor / coupon.new / refer.hold / cell.restart": "operational companion channels plus the 24 min floor",
            },
            "temporal_motifs": [
                "vendor-low while FP-over: fringveil.P 3.20 next to recon.P 100.00",
                "reconstruction as event: recon.P 100.00 equals 4.00*(1575.00-1550.00)",
                "MODIFY then operational ACCEPT: gate.isol at 2460 s, gate.exec at 4620 s",
                "slow floor in-stream: cool.start 2820 s, cool.floor 4260 s (24.0 min)",
                "tight FP pair: fp.lam then fp.snr +1.2 ms at the raster frame",
                "exoneration motif: lamp.cal 0 at 1260 s precedes the high pressure; Pye badge is not in the stream as a cause",
            ],
            "language_to_spike_mapping": "'Fringveil is 3.20 bar' = fringveil.P 3.20; '100 bar choke' = recon.P 100.00; 'isolate this choke not Pye' = gate.isol MODIFY; 'new coupon not referral' = gate.exec ACCEPT",
            "why_high_value": "New fiber-optic Fabry-Perot diaphragm-pressure family on a wellhead choke (not FBG r13, not BOTDA r14, not OFDR r50, not confocal chromatic r36, not SAW r15). Lead MODIFY of keep-choke on a recomputable high pressure that a vendor last-good would have cleared, with a resolved-innocent fiber tech. Companion t2 is operational new-coupon restart. sim_or_real=hil.",
            "encoder_spec": {
                "prng": "MT19937 via python random.Random",
                "seeds": {"raster": 202609161, "stream_note": "stream amplitudes are authored constants (nm, 1, bar, um, bool)"},
                "draw_order": "raster: per neuron id order, gap-constrained times, per-spike adaptation and noise",
                "thinning": "FP spectrometer exists at ~kHz; stream keeps 4 lambda points; recon keeps 4 of ~20 solver ticks",
                "refractory_floors_ms": {
                    "fp.lam": 1.2,
                    "fp.snr": 1.2,
                    "recon.P": 60000,
                    "recon.d": 60000,
                    "cal.lamp": 60000,
                    "fringveil.P": 60000,
                    "lamp.cal": 60000,
                    "ops.prop": 60000,
                    "gate.isol": 60000,
                    "choke.lock": 60000,
                    "cool.start": 60000,
                    "cool.floor": 60000,
                    "ops.refer": 60000,
                    "gate.exec": 60000,
                    "coupon.new": 60000,
                    "refer.hold": 60000,
                    "choke.held": 60000,
                    "well.kill": 60000,
                    "cell.restart": 60000,
                },
                "time_alias": "t_rel_ms; t0 = 2026-07-18T02:30:00Z HIL night start",
            },
            "distillation_targets": [
                "FP reconstruction head: P = k_p * (lam - lam0); d = d0 - k_d * P; P = (d0 - d) / k_d",
                "isolate-floor choke vs keep-whole vs well-kill",
                "exoneration head: missing lamp-cal AE plus timezone skip, not last-to-badge",
                "operational companion: new-coupon restart without referring the fiber tech",
            ],
        },
        "reconstruction_model": {
            "name": "fp_diaphragm_wellhead_pressure",
            "formula": "P_bar = k_p * (lam_nm - lam0_nm); d_um = d0_um - k_d * P_bar; P_bar = (d0_um - d_um) / k_d",
            "parameters": {
                "k_p": 4.00,
                "lam0_nm": 1550.00,
                "d0_um": 80.00,
                "k_d": 0.200,
                "isolate_floor_bar": 72.00,
                "kill_bar": 140.00,
                "snr_lock": 12.0,
                "cool_min": 24.0,
            },
            "worked_example": {"lam_nm": 1575.00, "P_bar": 100.00, "d_um": 60.00, "dlam_nm": 25.00},
            "check": "4.00 * (1575.00 - 1550.00) = 100.00 exactly; 80.00 - 0.200 * 100.00 = 60.00 exactly; 20.00 / 0.200 = 100.00 exactly; 2820 s + 1440 s = 4260 s = 24.0 min floor",
        },
        "raster": raster,
        "gate_snn": {
            "decision": "MODIFY",
            "decision_window_ms": 32.0,
            "decision_window_s": 0.032,
            "code": "ec4.fp_choke_gate",
            "note": "MODIFY accumulator wins: FP high-pressure evidence overpowers the Fringveil continue advocate",
            "decode_rule": "modify-isolate if pressure_estimator AND cavity_norm fire; vendor_continue_advocate is below threshold by design; referral_latch is not armed",
            "populations": [
                gate_pop("pressure_estimator", 80, 1.5, 50.0, w_s),
                gate_pop("cavity_norm", 64, 1.2, 31.25, w_s),
                gate_pop("vendor_continue_advocate", 32, 0.7, 25.0, w_s),
                gate_pop("modify_latch", 80, 1.7, 62.5, w_s),
            ],
        },
        "gate_compute": gate_compute(
            [
                {"check": "ec4.fp_scorer", "neurons": 80, "mean_rate_hz": 50.0, "window_ms": 32.0},
                {"check": "ec4.isol_scorer", "neurons": 50, "mean_rate_hz": 50.0, "window_ms": 32.0},
            ]
        ),
        "meta": meta_common(
            id="nelb-r53-161",
            clock_domain="ec4-fp-hil-relative-ms-t0-2026-07-18T02:30:00Z",
            tags=["fabry-perot-pressure", "MODIFY", "ACCEPT", "serialized-reconstruction", "operational-t2"],
        ),
    }


# ---------------------------------------------------------------------------
# Record 162 — inductive oil-debris of a turbine gearbox, simulated,
# ACCEPT / REJECT
# ---------------------------------------------------------------------------
def rec_162():
    k_m = 0.250
    n_counts = 48.00
    m_mg = k_m * n_counts
    _exact(m_mg, 12.00)
    _exact(k_m * 16.00, 4.00)
    _exact(k_m * 32.00, 8.00)
    _exact(k_m * 40.00, 10.00)
    t_min = 4.00
    r_cpm = n_counts / t_min
    _exact(r_cpm, 12.00)
    mdot = k_m * r_cpm
    _exact(mdot, 3.00)
    _exact(12.00 / 4.00, 3.00)
    n_id = m_mg / k_m
    _exact(n_id, 48.00)
    _exact(6000.0 + 720.0, 6720.0)

    raster = make_raster(
        neurons=16,
        mean_rate_hz=62.5,
        window_ms=36.0,
        seed=202609162,
        source="rw7.debris.coil",
        target="reedwhin.gear_accept_core",
        table=[
            {"from": "debris_N", "to": "mass_estimator", "weight": 1.40},
            {"from": "debris_snr", "to": "coil_norm_core", "weight": 1.20},
            {"from": "chipveil_m", "to": "vendor_skip_advocate", "weight": 0.50},
        ],
        third_factor={
            "modulator": "na.gearbox_scope_eligibility",
            "tau_e_s": 2.0,
            "tau_e_ms": 2000.0,
            "eligibility": "pre-post coincidence on skip-drain synapses; the inductive-debris modulator enables potentiation only while pulse count and SNR are co-active inside tau_e so a Chipveil last-good cannot skip gearboxes G-1..G-3 on a 12.00 mg chip load",
        },
        channel_prefix="deb.n",
        anchor="RW-7 DEBRIS-SIM-2 36 ms frame at N 48.00 / SNR 16.0 (t_s 3000) reconstructing 12.00 mg on G-4 above the 8.00 mg drain floor",
    )
    w_s = 0.036
    events = [
        ev(0.0, "debris.N", 16.00, code="N_COUNTS", units="1", note="simulated inductive oil-debris coil of RW-7 gearbox G-4; chip-mass family, not MFL remaining wall, not MCSA broken-bar, not MEMS accel array, not SAW torque, not blade tip-timing"),
        ev(300000.0, "debris.snr", 10.0, code="DEB_SNR", units="1", note="early coil SNR"),
        ev(600000.0, "recon.M", 4.00, code="M_MG", units="mg", note="0.250*16.00=4.00 exact"),
        ev(900000.0, "lube.dp", 8.0, code="DP_KPA", units="kPa", note="plant filter dP on a serial-only LAN; independent witness"),
        ev(1200000.0, "chipveil.M", 1.20, code="VENDOR_MG", units="mg", note="Chipveil last-good particle cloud; patched residual 0.00 mg"),
        ev(1800000.0, "debris.N", 32.00, code="N_COUNTS", units="1"),
        ev(2100000.0, "recon.M", 8.00, code="M_MG", units="mg", note="0.250*32.00=8.00; at the 8.00 drain floor"),
        ev(2400000.0, "recon.mdot", 2.00, code="MDOT_MGMIN", units="mg_min", note="0.250*(32.00/4.00)=2.00; mass-flow identity at this frame"),
        ev(2700000.0, "debris.snr", 14.0, code="DEB_SNR", units="1"),
        ev(3000000.0, "debris.N", 48.00, code="N_COUNTS", units="1", note="in-band frame; raster sidecar"),
        ev(3000001.5, "debris.snr", 16.0, code="DEB_SNR", units="1", note="1.5 ms coil-norm after pulse count"),
        ev(3300000.0, "recon.M", 12.00, code="M_MG", units="mg", note="0.250*48.00=12.00 exact; drain 8.00, engine-kill 40.00"),
        ev(3600000.0, "chipveil.M", 1.20, code="VENDOR_MG", units="mg"),
        ev(3900000.0, "gear.id", 4.0, code="GEAR", units="id"),
        ev(4200000.0, "g13.present", 1.0, code="G13_PRESENT", units="bool", note="adjacent gearboxes G-1..G-3 are the skip-drain object, not this gearbox"),
        ev(4800000.0, "ops.prop", 1.0, code="ACCEPT_AND_SKIP", units="bool", note="lube lead Nessa Bramble: G-4 is green on Chipveil 1.20; skip G-1..G-3 to save a morning drain"),
        ev(5400000.0, "gate.gear", 1.0, code="ACCEPT", units="decision", note="bounded ACCEPT of G-4 drain only; 12.00 mg above 8.00 floor; G-1..G-3 out of scope"),
        ev(6000000.0, "surv.start", 1.0, code="SURV_START", units="bool", note="bookend 1 of the 12.0 min survey-complete floor"),
        ev(6720000.0, "surv.floor", 1.0, code="SURV_FLOOR", units="bool", note="6000 s + 720 s = 6720 s = 12.0 min"),
        ev(7200000.0, "ops.skip", 1.0, code="SKIP_G13", units="bool", note="Bramble: Chipveil 1.20, skip G-1..G-3"),
        ev(7800000.0, "gate.hold", 1.0, code="REJECT", units="decision", note="companion t2: skip-drain of G-1..G-3 refused; G-4 hold stands"),
        ev(8400000.0, "g4.held", 1.0, code="G4_HELD", units="bool"),
        ev(9000000.0, "debris.N", 40.00, code="N_COUNTS", units="1"),
        ev(9600000.0, "recon.M", 10.00, code="M_MG", units="mg", note="0.250*40.00=10.00; still at/over the 8.00 drain floor"),
        ev(10200000.0, "chipveil.M", 1.20, code="VENDOR_MG", units="mg"),
        ev(10800000.0, "g13.skip", 0.0, code="G13_NOT_SKIPPED", units="bool"),
        ev(11400000.0, "eng.kill", 0.0, code="ENG_NOT_KILLED", units="bool"),
        ev(12000000.0, "debris.snr", 15.0, code="DEB_SNR", units="1"),
        ev(12600000.0, "recon.mdot", 2.50, code="MDOT_MGMIN", units="mg_min", note="0.250*(40.00/4.00)=2.50 on the post-accept frame"),
        ev(13200000.0, "lube.held", 1.0, code="LUBE_HELD", units="bool"),
        ev(13800000.0, "takt.late", 1.0, code="SURVEY_COST", units="bool"),
        ev(14400000.0, "g4.held", 1.0, code="G4_HELD", units="bool"),
    ]
    assert_stream(events)

    traj = {
        "id": "nelb-r53-162-t1",
        "state": {
            "sim_or_real": "simulated",
            "episode_id": "RW-DEB-2026-0819",
            "domain": "inductive_oil_debris_gearbox",
            "setting": "Reedwhin Turbine RW-7 (invented), Fogspit Combined-Cycle lube cellar. Simulated inductive-debris coupon in DEBRIS-SIM-2 supplies the pulse count that times the in-band G-4 drain. Plant-owned inductive reconstruction is the chip-mass SoT. Chipveil vendor last-good particle cloud is a corridor witness, not the gearbox SoT. Invented plant; simulated campaign. Not MFL (r27/r28), not MCSA broken-bar (r48), not MEMS accel array (r17), not SAW torque (r15), not blade tip-timing (r25).",
            "observables_at_decision": {
                "N_counts": n_counts,
                "k_m": k_m,
                "M_mg": m_mg,
                "mdot_mgmin": mdot,
                "r_cpm": r_cpm,
                "chipveil_mg": 1.20,
                "debris_snr": 16.0,
                "drain_floor_mg": 8.00,
            },
            "margin_authority": "RW-7 lube SOP rev A: if reconstructed M_mg >= 8.00 AND debris SNR >= 12.0, gearbox G-4 may be drained and the filter swapped. Engine-kill if M_mg >= 40.00. G-1..G-3 skip-drain is a different gate. Chipveil last-good cannot skip an unmeasured gearbox.",
        },
        "proposed_action": {
            "actor": "lube lead Nessa Bramble, citing Chipveil 1.20 mg and a late morning drain",
            "summary": "stamp G-4 in band and skip G-1..G-3; 48.00 counts is a coil glitch on a healthy particle cloud",
            "basis_claimed": "Chipveil last-good is 1.20 mg and a night survey of G-1..G-3 is a takt miss",
        },
        "safety_decision": {
            "decision": "ACCEPT",
            "rationale": "Gearbox G-4 is accepted as in-band for a single drain plus filter swap. Serialized reconstruction: M_mg = k_m * N = 0.250 * 48.00 = 12.00, which is 4.00 mg above the 8.00 drain floor and 28.00 mg under the 40.00 engine-kill. Rate identity r_cpm = 48.00 / 4.00 = 12.00 and mdot = k_m * r = 0.250 * 12.00 = 3.00 mg/min; inverse N = M / k_m = 12.00 / 0.250 = 48.00. Chipveil 1.20 mg is a patched 0.00 residual and is not an admissible skip-drain witness. Ordered: ACCEPT this G-4 drain only. Scope: this ACCEPT does not skip G-1..G-3 (that is the companion question) and does not stamp an engine kill.",
            "threshold": "M_mg>=8.00 AND debris_snr>=12.0 => accept G-4 drain; Chipveil is not SoT; engine-kill if M_mg>=40.00; G-1..G-3 are out of scope",
            "stated_residuals": "12.00 vs 8.00 drain floor is 4.00 mg, not infinite; G-1..G-3 remain unmeasured; Chipveil remains the only OEM particle channel",
        },
        "executed_action": {
            "summary": "ACCEPT at t_s 5400: G-4 in band; G-1..G-3 not skipped; Chipveil not SoT; reconstruction locked",
            "tool": "rw7-debris-gear-gate-cli",
            "observation": "M 12.00 mg recomputes from N 48.00; DEBRIS-SIM-2 hashed; Chipveil channel not used as SoT",
        },
        "future_outcome": {
            "timeline": [
                {"t_s": 3000.0, "event": "debris N 48.00; raster frame; M 12.00 mg"},
                {"t_s": 4800.0, "event": "ops proposes accept G-4 and skip G-1..G-3"},
                {"t_s": 5400.0, "event": "ACCEPT G-4 only; G-1..G-3 out of scope"},
                {"t_s": 6000.0, "event": "12 min survey-complete bookend 1"},
                {"t_s": 6720.0, "event": "12.0 min floor"},
                {"t_s": 7800.0, "event": "companion REJECT skip-drain of G-1..G-3"},
            ],
            "observed_effects": [
                "chip mass recomputes from the serialized inductive model at every recon.M event",
                "a Chipveil-only head would have skipped G-1..G-3 overnight",
                "12 min survey-complete floor is in the stream (surv.start, surv.floor)",
            ],
            "surprises": [
                "a last-good 1.20 mg vendor corridor co-existed with a 12.00 mg in-band reconstruction that still forbids skipping the unmeasured gearboxes",
            ],
            "new_state": {
                "g4": "accepted in band",
                "g13": "not this gate",
                "chipveil": "not SoT",
                "reconstruction_model": "discharged as an on-record calculator",
            },
            "latency_ms": 2400000.0,
        },
        "reward_components": reward(
            0.41,
            [
                ("debris_reconstruction", 0.14),
                ("in_band_gear_scope", 0.12),
                ("chipveil_nonsubstitution", 0.09),
                ("g13_out_of_scope", 0.08),
                ("survey_cost", -0.02),
            ],
            "scored for a bounded ACCEPT of G-4 on a recomputable chip load while refusing a Chipveil skip of G-1..G-3; 12 min floor is priced as survey takt not as a reason to skip",
        ),
        "meta": meta_common(
            tags=["ACCEPT", "inductive-debris", "serialized-reconstruction", "operational-companion"],
            distillation_note="Inductive-debris gate: serialized k_m*N plus mdot identity beats a green last-good dashboard; companion t2 is the skip-drain refusal, not a particle re-vote",
        ),
    }
    traj2 = {
        "id": "nelb-r53-162-t2",
        "state": {
            "sim_or_real": "simulated",
            "episode_id": "RW-DEB-2026-0819-exec",
            "domain": "gear_skip_drain_refusal",
            "setting": "Same RW-7 after the ACCEPT. Lube lead proposes skipping G-1..G-3 on Chipveil 1.20 mg. This companion is the operational skip refusal, not a second chip-mass vote.",
            "observables_at_decision": {
                "M_mg": 10.00,
                "chipveil_mg": 1.20,
                "surv_floor_s": 720.0,
                "skip_proposed": True,
            },
        },
        "proposed_action": {
            "actor": "lube lead Nessa Bramble",
            "summary": "skip G-1..G-3; 12 min already paid and Chipveil is 1.20 mg",
            "basis_claimed": "the ACCEPT already stamped G-4, so skipping the rest of the cellar is the cheapest hold",
        },
        "safety_decision": {
            "decision": "REJECT",
            "rationale": "Refuse skip-drain of G-1..G-3. The 12 min survey-complete floor is done and the engine-kill (M_mg >= 40.00) is still armed on the plant inductive head. REJECT the skip. Do not kill the engine. Do not reopen G-4. 10.00 mg post-accept is still in band for G-4 only; G-1..G-3 have no independent inductive coil.",
            "threshold": "g4_held AND surv_floor_complete AND g13_not_skipped AND eng_not_killed",
        },
        "executed_action": {
            "summary": "G-1..G-3 skip refused at t_s 7800; G-4 hold stands; engine not killed",
            "tool": "rw7-debris-skip-exec",
            "observation": "recon.M 10.00 mg on G-4; G-1..G-3 remain on the survey list; Chipveil still ignored",
        },
        "future_outcome": {
            "timeline": [
                {"t_s": 6000.0, "event": "survey clock started after ACCEPT"},
                {"t_s": 6720.0, "event": "12.0 min floor"},
                {"t_s": 7200.0, "event": "skip G-1..G-3 proposed"},
                {"t_s": 7800.0, "event": "REJECT skip-drain of G-1..G-3"},
            ],
            "observed_effects": [
                "Chipveil skip did not reopen the chip-mass call",
                "engine kill never fired; 12.00 vs 40.00 mg floor",
            ],
            "new_state": {"g4": "held in band", "g13": "still to survey", "engine": "in service"},
            "latency_ms": 1800000.0,
        },
        "reward_components": reward(
            0.36,
            [
                ("skip_refusal", 0.13),
                ("chipveil_nonsubstitution", 0.11),
                ("no_engine_kill", 0.09),
                ("surv_floor_complete", 0.05),
                ("held_survey_takt_cost", -0.02),
            ],
            "operational execution gate: refuse skip-drain because last-good freeze is not inductive chip mass; not a particle re-vote",
        ),
        "meta": meta_common(tags=["REJECT", "operational-execution", "skip-drain"]),
    }
    return {
        "id": "nelb-r53-162",
        "spike_events": events,
        "language_view": {
            "description": "Reedwhin Turbine RW-7. Simulated inductive oil-debris coil reconstructs 12.00 mg from 48.00 pulses * 0.250 while Chipveil still shows 1.20 mg. The gate ACCEPTs G-4 drain only; a companion execution REJECT refuses skip-drain of G-1..G-3. The count-to-mass model is serialized so every recon event recomputes.",
            "trajectory": traj,
            "trajectory_skip_drain_refusal": traj2,
        },
        "bridge_notes": {
            "channel_map": {
                "debris.N / debris.snr": "inductive pulse count and SNR; the physics channels the reconstruction consumes",
                "recon.M / recon.mdot": "serialized chip mass mg and mass-flow identity",
                "lube.dp / chipveil.M / gear.id / g13.present": "filter dP, vendor last-good, gearbox id, and adjacent-gearbox presence; the denial and scope channels",
                "ops.prop / gate.gear / ops.skip / gate.hold": "accept-and-skip proposal, bounded ACCEPT, skip proposal, companion REJECT",
                "surv.start / surv.floor / g4.held / g13.skip / lube.held": "operational companion channels plus the 12 min floor",
            },
            "temporal_motifs": [
                "last-good-low while debris-over: chipveil.M 1.20 next to recon.M 12.00",
                "reconstruction as event: recon.M 12.00 equals 0.250*48.00",
                "ACCEPT then operational REJECT: gate.gear at 5400 s, gate.hold at 7800 s",
                "slow floor in-stream: surv.start 6000 s, surv.floor 6720 s (12.0 min)",
                "tight debris pair: debris.N then debris.snr +1.5 ms at the raster frame",
            ],
            "language_to_spike_mapping": "'Chipveil is 1.20 mg' = chipveil.M 1.20; '12 mg chips' = recon.M 12.00; 'this gearbox not G-1..G-3' = gate.gear ACCEPT plus g13.skip 0; 'do not skip G-1..G-3' = gate.hold REJECT",
            "why_high_value": "New inductive oil-debris family on a turbine gearbox (not MFL r27/r28, not MCSA r48, not MEMS array r17, not SAW torque r15, not blade tip-timing r25). First k_m*N mass reconstruction with mdot identity that can sit in band while a last-good corridor wants a gearbox skip. Companion t2 is operational skip refusal. sim_or_real=simulated.",
            "encoder_spec": {
                "prng": "MT19937 via python random.Random",
                "seeds": {"raster": 202609162, "stream_note": "stream amplitudes are authored constants (counts, 1, mg, mg/min, kPa, id, bool)"},
                "draw_order": "raster: per neuron id order, gap-constrained times, per-spike adaptation and noise",
                "thinning": "inductive coil exists at ~kHz pulses; stream keeps 4 N points; recon keeps 4 of ~20 solver ticks",
                "refractory_floors_ms": {
                    "debris.N": 1.5,
                    "debris.snr": 1.5,
                    "recon.M": 60000,
                    "recon.mdot": 60000,
                    "lube.dp": 60000,
                    "chipveil.M": 60000,
                    "gear.id": 60000,
                    "g13.present": 60000,
                    "ops.prop": 60000,
                    "gate.gear": 60000,
                    "surv.start": 60000,
                    "surv.floor": 60000,
                    "ops.skip": 60000,
                    "gate.hold": 60000,
                    "g4.held": 60000,
                    "g13.skip": 60000,
                    "eng.kill": 60000,
                    "lube.held": 60000,
                    "takt.late": 60000,
                },
                "time_alias": "t_rel_ms; t0 = 2026-08-19T03:00:00Z simulated night start",
            },
            "distillation_targets": [
                "inductive-debris reconstruction head: M = k_m * N; r_cpm = N / t_min; mdot = k_m * r_cpm",
                "bounded ACCEPT head: in-band chip mass AND gearbox scope AND g13-out-of-scope",
                "operational companion: refuse skip-drain without re-opening the particle call",
            ],
        },
        "reconstruction_model": {
            "name": "inductive_oil_debris_mass",
            "formula": "M_mg = k_m * N_counts; r_cpm = N_counts / t_min; mdot_mgmin = k_m * r_cpm; N_counts = M_mg / k_m",
            "parameters": {
                "k_m": 0.250,
                "t_min": 4.00,
                "drain_floor_mg": 8.00,
                "kill_mg": 40.00,
                "snr_lock": 12.0,
                "surv_min": 12.0,
            },
            "worked_example": {"N_counts": 48.00, "M_mg": 12.00, "r_cpm": 12.00, "mdot_mgmin": 3.00},
            "check": "0.250 * 48.00 = 12.00 exactly; 48.00 / 4.00 = 12.00 exactly; 0.250 * 12.00 = 3.00 exactly; 12.00 / 0.250 = 48.00 exactly; 6000 s + 720 s = 6720 s = 12.0 min floor",
        },
        "raster": raster,
        "gate_snn": {
            "decision": "ACCEPT",
            "decision_window_ms": 36.0,
            "decision_window_s": 0.036,
            "code": "rw7.debris_gear_gate",
            "note": "ACCEPT accumulator wins: inductive chip-mass evidence overpowers the Chipveil skip advocate",
            "decode_rule": "accept if mass_estimator AND coil_norm AND gearbox_margin fire inside the window; vendor_skip_advocate is necessary-but-not-sufficient and cannot release G-1..G-3",
            "populations": [
                gate_pop("mass_estimator", 80, 1.5, 50.0, w_s),
                gate_pop("coil_norm", 64, 1.2, 31.25, w_s),
                gate_pop("gearbox_margin", 40, 1.0, 50.0, w_s),
                gate_pop("vendor_skip_advocate", 32, 0.7, 25.0, w_s),
                gate_pop("accept_latch", 96, 1.8, 62.5, w_s),
            ],
        },
        "gate_compute": gate_compute(
            [
                {"check": "rw7.debris_scorer", "neurons": 80, "mean_rate_hz": 50.0, "window_ms": 36.0},
                {"check": "rw7.mass_scorer", "neurons": 40, "mean_rate_hz": 62.5, "window_ms": 32.0},
            ]
        ),
        "meta": meta_common(
            id="nelb-r53-162",
            clock_domain="rw7-debris-sim-relative-ms-t0-2026-08-19T03:00:00Z",
            tags=["inductive-debris", "ACCEPT", "REJECT", "serialized-reconstruction", "operational-t2"],
        ),
    }

