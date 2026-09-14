
# ---------------------------------------------------------------------------
# Record 181 — laser-triangulation remaining strip thickness of a tandem mill,
# designed, REJECT / MODIFY
# ---------------------------------------------------------------------------
def rec_181():
    k_t = 50.00
    v0_v = 10.00
    v_v = 5.00
    t_um = k_t * (v0_v - v_v)
    _exact(t_um, 250.0)
    _exact(k_t * (v0_v - 2.00), 400.0)
    _exact(k_t * (v0_v - 3.00), 350.0)
    _exact(k_t * (v0_v - 6.00), 200.0)
    k_m = 0.080
    mdot = k_m * t_um
    _exact(mdot, 20.00)
    _exact(k_m * 400.0, 32.00)
    _exact(k_m * 350.0, 28.00)
    _exact(k_m * 200.0, 16.00)
    span = v0_v - v_v
    _exact(span, 5.00)
    _exact(t_um / k_t, 5.00)
    mill_v = 8.00
    mill_v0 = 8.00
    v_ratio = mill_v / mill_v0
    _exact(v_ratio, 1.000)
    _exact(6000.0 + 1080.0, 7080.0)

    raster = make_raster(
        neurons=20,
        mean_rate_hz=50.0,
        window_ms=40.0,
        seed=202660181,
        source="ys6.tri.head",
        target="yewspit.stand_stop_core",
        table=[
            {"from": "tri_V", "to": "thickness_estimator", "weight": 1.40},
            {"from": "tri_snr", "to": "tri_lock_core", "weight": 1.15},
            {"from": "spotveil_t", "to": "vendor_continue_advocate", "weight": 0.45},
        ],
        third_factor={
            "modulator": "da.tri_gauge_conflict",
            "tau_e_s": 1.6,
            "tau_e_ms": 1600.0,
            "eligibility": "pre-post coincidence on continue-rolling synapses; the plant triangulation modulator depresses continue-rolling links when head voltage stays high inside tau_e of an SNR lock so a Spotveil last-good cannot hide a 250.0 um remaining strip",
        },
        channel_prefix="tri.n",
        anchor="YS-6 laser-triangulation 40 ms frame at V 5.00 V / SNR 12.0 (t_s 3000) reconstructing 250.0 um remaining strip under the 280.0 um isolate floor",
    )
    w_s = 0.040
    events = [
        ev(0.0, "tri.V", 2.00, code="V_V", units="V", note="plant-owned laser-triangulation head on YS-6 stand F-3; remaining-strip family, not confocal chromatic ribbon, not OCT TBC, not DIC hoop-strain, not OFDR Rayleigh, not laser-flash Parker"),
        ev(300000.0, "tri.snr", 6.0, code="TRI_SNR", units="1", note="early SNR under the 8.0 lock floor"),
        ev(600000.0, "recon.t", 400.0, code="T_UM", units="um", note="50.00*(10.00-2.00)=400.0 exact; still above the 280.0 isolate floor"),
        ev(900000.0, "mill.v", 8.00, code="MILL_MS", units="m_s", note="plant mill-speed encoder on copper DCS; independent witness; unread by Spotveil"),
        ev(1200000.0, "spotveil.t", 380.0, code="VENDOR_UM", units="um", note="Spotveil vendor gauge-cloud; infra owner; patched head-voltage timestamps"),
        ev(1800000.0, "tri.V", 3.00, code="V_V", units="V"),
        ev(2100000.0, "recon.t", 350.0, code="T_UM", units="um", note="50.00*(10.00-3.00)=350.0"),
        ev(2400000.0, "permit.slide", 40.00, code="PERM_S", units="s", note="permit clerk slid cold-mill clock 40.00 s; collusion party"),
        ev(2700000.0, "mill.v", 8.00, code="MILL_MS", units="m_s", note="v/v0=1.000; no speed hop in this window"),
        ev(3000000.0, "tri.V", 5.00, code="V_V", units="V", note="isolate-floor frame; raster sidecar"),
        ev(3000001.4, "tri.snr", 12.0, code="TRI_SNR", units="1", note="1.4 ms SNR lock after V; 12.0 >= 8.0"),
        ev(3300000.0, "recon.t", 250.0, code="T_UM", units="um", note="50.00*(10.00-5.00)=250.0 exact; isolate 280.0, mill-kill 120.0"),
        ev(3600000.0, "recon.mdot", 20.00, code="MDOT_KGS", units="kg_s", note="0.080*250.0=20.00 exact mass-flow identity"),
        ev(3900000.0, "mill.v", 8.00, code="MILL_MS", units="m_s", note="encoder tracks the plant triangulation head, not Spotveil 380.0 um"),
        ev(4200000.0, "spotveil.drop", 1.0, code="TRI_DROP", units="bool", note="vendor head-voltage packets dropped in Spotveil cloud for 40 s"),
        ev(4800000.0, "ops.prop", 1.0, code="CONTINUE_ROLL", units="bool", note="night operator Niall Bream: Spotveil is clean 380.0 um; continue F-3 rolling"),
        ev(5400000.0, "gate.stop", 1.0, code="REJECT", units="decision", note="refuse continue-rolling; 250.0 um and SNR 12.0; Spotveil not SoT"),
        ev(6000000.0, "hold.start", 1.0, code="HOLD_START", units="bool", note="bookend 1 of the 18.0 min pass-hold floor"),
        ev(7080000.0, "hold.floor", 1.0, code="HOLD_FLOOR", units="bool", note="6000 s + 1080 s = 7080 s = 18.0 min"),
        ev(7800000.0, "ops.kill", 1.0, code="MILL_ESD", units="bool", note="Bream: ESD the whole Yewspit tandem until day-shift"),
        ev(8400000.0, "gate.hold", 1.0, code="MODIFY", units="decision", note="companion t2: pass-hold on plant triangulation as live interlock; mill ESD refused"),
        ev(9000000.0, "holdlock.set", 1.0, code="HOLD_HELD", units="bool"),
        ev(9600000.0, "tri.V", 6.00, code="V_V", units="V"),
        ev(10200000.0, "recon.t", 200.0, code="T_UM", units="um", note="50.00*(10.00-6.00)=200.0; still under 280.0 so the pass-hold stands"),
        ev(10800000.0, "spotveil.t", 378.0, code="VENDOR_UM", units="um"),
        ev(11400000.0, "mill.v", 8.00, code="MILL_MS", units="m_s"),
        ev(12000000.0, "hold.held", 1.0, code="HOLD_HELD", units="bool"),
        ev(12600000.0, "mill.esd", 0.0, code="ESD_NOT_TAKEN", units="bool"),
        ev(13200000.0, "permit.slide", 40.00, code="PERM_S", units="s"),
        ev(13800000.0, "spotveil.drop", 1.0, code="TRI_DROP", units="bool"),
        ev(14400000.0, "holdlock.held", 1.0, code="HOLD_HELD", units="bool"),
        ev(15000000.0, "recon.mdot", 16.00, code="MDOT_KGS", units="kg_s", note="0.080*200.0=16.00 on the post-stop frame"),
    ]
    assert_stream(events)

    traj = {
        "id": "nelb-r60-181-t1",
        "state": {
            "sim_or_real": "designed",
            "episode_id": "YS-TRI-2026-0902",
            "domain": "laser_triangulation_tandem_strip",
            "setting": "Yewspit Tandem YS-6 (invented), Felshaw Cold Mill, stand F-3. Plant-owned laser-triangulation head is the remaining-strip SoT. Spotveil vendor gauge-cloud (infra owner) plus the cold-mill permit clock are collusion parties, not witnesses. Invented plant; designed campaign. Not confocal chromatic ribbon thickness (r36), not spectral-domain OCT TBC (r38), not DIC hoop-strain (r51), not OFDR Rayleigh hoop-strain (r50), not laser-flash Parker diffusivity (r44).",
            "observables_at_decision": {
                "V_V": v_v,
                "V0_V": v0_v,
                "k_t": k_t,
                "t_um": t_um,
                "mdot_kgs": mdot,
                "mill_v_ms": mill_v,
                "tri_snr": 12.0,
                "spotveil_um": 380.0,
                "permit_slide_s": 40.00,
                "isolate_floor_um": 280.0,
            },
            "margin_authority": "YS-6 tandem SOP rev C: if reconstructed t_um <= 280.0 AND triangulation SNR >= 8.0, continue-rolling is forbidden even if Spotveil reports 380.0 um. Mill ESD is a different gate. Kill tripwire is 120.0 um.",
        },
        "proposed_action": {
            "actor": "night tandem operator Niall Bream, citing Spotveil 380.0 um and a quiet head-voltage channel",
            "summary": "continue F-3 rolling; 5.00 V is head noise on a healthy remaining strip",
            "basis_claimed": "Spotveil is the only OEM gauge SoT and a night abort of F-3 is a coil miss",
        },
        "safety_decision": {
            "decision": "REJECT",
            "rationale": "Continue-rolling is refused. Serialized reconstruction: t_um = k_t * (V0 - V) = 50.00 * (10.00 - 5.00) = 250.0, which is 30.0 um under the 280.0 isolate floor and 130.0 um above the 120.0 mill-kill tripwire, and triangulation SNR is 12.0 >= 8.0. Mass-flow identity mdot = k_m * t_um = 0.080 * 250.0 = 20.00; span identity (V0 - V) = t_um / k_t = 5.00. mill v/v0 = 1.000 so no speed hop is available as an excuse. Permit clock was slid 40.00 s and vendor head-voltage packets were dropped, so Spotveil is a collusion party (gauge vendor plus operator plus permit clerk). Ordered: refuse continue-rolling now. Scope: this REJECT does not ESD the tandem (that is the companion question) and does not isolate the mill-speed encoder.",
            "threshold": "t_um<=280.0 AND tri_snr>=8.0 => refuse continue-rolling; Spotveil is not SoT; mill-kill if t_um<=120.0",
            "stated_residuals": "pass-hold still required to hold the 250.0 um; 250.0 vs a true 120.0 kill is a production cut; Spotveil remains the only OEM gauge channel",
        },
        "executed_action": {
            "summary": "REJECT at t_s 5400: continue-rolling refused; Spotveil not SoT; reconstruction locked",
            "tool": "ys6-tri-stand-gate-cli",
            "observation": "t 250.0 um recomputes from V 5.00 V; plant triangulation head hashed; Spotveil channel not used as SoT",
        },
        "future_outcome": {
            "timeline": [
                {"t_s": 3000.0, "event": "tri V 5.00 V; raster frame; t 250.0 um"},
                {"t_s": 4800.0, "event": "ops proposes continue-rolling"},
                {"t_s": 5400.0, "event": "REJECT continue-rolling"},
                {"t_s": 6000.0, "event": "18 min pass-hold bookend 1"},
                {"t_s": 7080.0, "event": "18.0 min floor"},
                {"t_s": 8400.0, "event": "companion MODIFY pass-hold vs mill ESD"},
            ],
            "observed_effects": [
                "remaining strip recomputes from the serialized triangulation model at every recon.t event",
                "a Spotveil-only head would have continued rolling overnight",
                "18 min pass-hold floor is in the stream (hold.start, hold.floor)",
            ],
            "surprises": [
                "a clean vendor 380.0 um corridor and a 40 s permit slide co-existed with a 250.0 um plant reconstruction",
            ],
            "new_state": {
                "f3": "continue-rolling blocked",
                "spotveil": "not SoT",
                "reconstruction_model": "discharged as an on-record calculator",
            },
            "latency_ms": 2400000.0,
        },
        "reward_components": reward(
            0.43,
            [
                ("tri_reconstruction", 0.14),
                ("conjunctive_isolate_floor", 0.12),
                ("spotveil_nonsubstitution", 0.10),
                ("three_party_collusion", 0.10),
                ("hold_time_cost", -0.03),
            ],
            "scored for a continue-rolling REJECT on a recomputable laser-triangulation remaining strip while refusing a Spotveil last-good patch and a permit clock slide; 18 min floor is priced as downtime not as a reason to wait",
        ),
        "meta": meta_common(
            tags=["REJECT", "laser-triangulation", "serialized-reconstruction", "operational-companion"],
            distillation_note="Triangulation gate: serialized k_t*(V0-V) plus SNR lock beats a vendor last-good patch; companion t2 is the pass-hold, not a referral vote",
        ),
    }
    traj2 = {
        "id": "nelb-r60-181-t2",
        "state": {
            "sim_or_real": "designed",
            "episode_id": "YS-TRI-2026-0902-exec",
            "domain": "pass_hold_tri_interlock_execution",
            "setting": "Same YS-6 after the REJECT. Operator proposes tandem ESD. This companion is the operational pass-hold with the plant triangulation head as the live interlock, not a second thickness vote.",
            "observables_at_decision": {
                "t_um": 200.0,
                "hold_floor_s": 1080.0,
                "mill_esd_proposed": True,
                "hold_set": True,
            },
        },
        "proposed_action": {
            "actor": "night tandem operator Niall Bream",
            "summary": "ESD the whole Yewspit tandem until day-shift; 18 min already paid and Spotveil still shows 378.0 um",
            "basis_claimed": "the REJECT already stopped F-3, so a mill kill is the cheapest hold",
        },
        "safety_decision": {
            "decision": "MODIFY",
            "rationale": "Pass-hold plus plant triangulation head as the live interlock. The 18 min pass-hold floor is complete and the isolate tripwire (t_um <= 280.0) is still armed on the plant triangulation head. MODIFY the default Spotveil-restore SOP into a plant-triangulation-only interlock. Do not ESD the tandem. Do not restore rolling on Spotveil. 200.0 um post-stop is still the plant SoT until a new frame clears 280.0.",
            "threshold": "pass_hold AND hold_floor_complete AND mill_esd_not_taken AND continue_not_restored",
        },
        "executed_action": {
            "summary": "pass-hold at t_s 8400; mill ESD not latched; Spotveil restore not taken",
            "tool": "ys6-pass-hold-exec",
            "observation": "recon.t 200.0 um after stop; pass-hold line-up complete; Spotveil still ignored",
        },
        "future_outcome": {
            "timeline": [
                {"t_s": 6000.0, "event": "pass-hold clock started after REJECT"},
                {"t_s": 7080.0, "event": "18.0 min floor"},
                {"t_s": 7800.0, "event": "mill ESD proposed"},
                {"t_s": 8400.0, "event": "MODIFY pass-hold; mill ESD refused"},
            ],
            "observed_effects": [
                "Spotveil restore did not reopen the thickness call",
                "mill ESD never fired; F-3 held the pass on the plant triangulation head",
            ],
            "new_state": {"hold": "armed", "mill": "in service", "f3": "held"},
            "latency_ms": 1800000.0,
        },
        "reward_components": reward(
            0.34,
            [
                ("pass_hold", 0.12),
                ("no_mill_esd", 0.10),
                ("spotveil_nonsubstitution", 0.08),
                ("hold_floor_complete", 0.06),
                ("held_production_cost", -0.02),
            ],
            "operational execution gate: pass-hold because Spotveil is not a restore license; not a thickness re-vote",
        ),
        "meta": meta_common(tags=["MODIFY", "operational-execution", "pass-hold"]),
    }
    return {
        "id": "nelb-r60-181",
        "spike_events": events,
        "language_view": {
            "description": "Yewspit Tandem YS-6. Plant-owned laser-triangulation head reconstructs 250.0 um remaining strip from 50.00*(10.00-5.00) while Spotveil still reports 380.0 um. The gate REJECTs continue-rolling. An 18 min pass-hold floor is serialized in the stream. Companion t2 MODIFYs a tandem ESD into a plant-triangulation pass-hold.",
            "trajectory": traj,
            "trajectory_pass_hold": traj2,
        },
        "bridge_notes": {
            "channel_map": {
                "tri.V / tri.snr": "head voltage and SNR; the physics channels the reconstruction consumes",
                "recon.t / recon.mdot": "serialized remaining strip um and mass-flow identity",
                "mill.v / spotveil.t / permit.slide / spotveil.drop": "mill-speed encoder, vendor gauge cloud, permit clock slide, and dropped head packets; the denial and collusion channels",
                "ops.prop / gate.stop / ops.kill / gate.hold": "continue-rolling proposal, REJECT, mill-ESD proposal, companion MODIFY",
                "hold.start / hold.floor / holdlock.set / hold.held / mill.esd": "operational companion channels plus the 18 min floor",
            },
            "temporal_motifs": [
                "vendor-green while plant-under: spotveil.t 380.0 next to recon.t 250.0",
                "reconstruction as event: recon.t 250.0 equals 50.00*(10.00-5.00)",
                "REJECT then operational MODIFY: gate.stop at 5400 s, gate.hold at 8400 s",
                "slow floor in-stream: hold.start 6000 s, hold.floor 7080 s (18.0 min)",
                "tight triangulation pair: tri.V then tri.snr +1.4 ms at the raster frame",
            ],
            "language_to_spike_mapping": "'Spotveil is 380.0 um' = spotveil.t 380.0; '250 um strip' = recon.t 250.0; 'refuse continue-rolling' = gate.stop REJECT; 'pass-hold not mill ESD' = gate.hold MODIFY",
            "why_high_value": "New laser-triangulation remaining-strip family on a tandem mill (not confocal chromatic r36, not OCT r38, not DIC r51, not OFDR r50, not laser-flash Parker r44). Lead REJECT of continue-rolling on a recomputable remaining strip that a vendor gauge patch and a permit clock slide would have cleared. Three-party collusion includes the gauge-cloud infra owner. Companion t2 is operational pass-hold. sim_or_real=designed.",
            "encoder_spec": {
                "prng": "MT19937 via python random.Random",
                "seeds": {"raster": 202660181, "stream_note": "stream amplitudes are authored constants (V, 1, um, kg/s, m/s, s, bool)"},
                "draw_order": "raster: per neuron id order, gap-constrained times, per-spike adaptation and noise",
                "thinning": "triangulation head exists at ~kHz; stream keeps 4 V points; recon keeps 4 of ~40 solver ticks",
                "refractory_floors_ms": {
                    "tri.V": 1.4,
                    "tri.snr": 1.4,
                    "recon.t": 60000,
                    "recon.mdot": 60000,
                    "mill.v": 60000,
                    "spotveil.t": 60000,
                    "permit.slide": 60000,
                    "spotveil.drop": 60000,
                    "ops.prop": 60000,
                    "gate.stop": 60000,
                    "hold.start": 60000,
                    "hold.floor": 60000,
                    "ops.kill": 60000,
                    "gate.hold": 60000,
                    "holdlock.set": 60000,
                    "hold.held": 60000,
                    "mill.esd": 60000,
                    "holdlock.held": 60000,
                },
                "time_alias": "t_rel_ms; t0 = 2026-09-02T01:00:00Z campaign start",
            },
            "distillation_targets": [
                "triangulation reconstruction head: t_um = k_t * (V0_V - V_V); mdot = k_m * t_um; (V0 - V) = t_um / k_t",
                "conjunctive isolate floor vs continue-rolling vs mill ESD",
                "vendor-gauge nonsubstitution plus three-party collusion including the infra owner",
                "operational companion: pass-hold without restoring on Spotveil",
            ],
        },
        "reconstruction_model": {
            "name": "laser_triangulation_remaining_strip",
            "formula": "t_um = k_t * (V0_V - V_V); mdot_kgs = k_m * t_um; (V0_V - V_V) = t_um / k_t",
            "parameters": {
                "k_t": 50.00,
                "V0_V": 10.00,
                "k_m": 0.080,
                "isolate_floor_um": 280.0,
                "kill_um": 120.0,
                "snr_lock": 8.0,
                "hold_min": 18.0,
            },
            "worked_example": {"V_V": 5.00, "t_um": 250.0, "mdot_kgs": 20.00, "span_V": 5.00},
            "check": "50.00 * (10.00 - 5.00) = 250.0 exactly; 0.080 * 250.0 = 20.00 exactly; 250.0 / 50.00 = 5.00 exactly; 6000 s + 1080 s = 7080 s = 18.0 min floor",
        },
        "raster": raster,
        "gate_snn": {
            "decision": "REJECT",
            "decision_window_ms": 40.0,
            "decision_window_s": 0.040,
            "code": "ys6.tri_stand_gate",
            "note": "REJECT accumulator wins: plant triangulation remaining-strip evidence overpowers the Spotveil continue advocate",
            "decode_rule": "reject-continue if thickness_estimator AND tri_lock fire; vendor_continue_advocate is below threshold by design",
            "populations": [
                gate_pop("thickness_estimator", 80, 1.5, 50.0, w_s),
                gate_pop("tri_lock", 64, 1.2, 31.25, w_s),
                gate_pop("vendor_continue_advocate", 32, 0.7, 25.0, w_s),
                gate_pop("reject_latch", 80, 1.7, 62.5, w_s),
            ],
        },
        "gate_compute": gate_compute(
            [
                {"check": "ys6.tri_scorer", "neurons": 80, "mean_rate_hz": 50.0, "window_ms": 40.0},
                {"check": "ys6.hold_scorer", "neurons": 40, "mean_rate_hz": 50.0, "window_ms": 32.0},
            ]
        ),
        "meta": meta_common(
            id="nelb-r60-181",
            clock_domain="ys6-tri-campaign-relative-ms-t0-2026-09-02T01:00:00Z",
            tags=["laser-triangulation", "REJECT", "MODIFY", "serialized-reconstruction", "operational-t2"],
        ),
    }


# ---------------------------------------------------------------------------
# Record 182 — flame-ionization remaining VOC of an RTO inlet, hil,
# MODIFY / ACCEPT
# ---------------------------------------------------------------------------
def rec_182():
    k_i = 4.00
    i_na = 12.00
    i_dark = 2.00
    c_ppm = k_i * (i_na - i_dark)
    _exact(c_ppm, 40.00)
    _exact(k_i * (4.00 - i_dark), 8.00)
    _exact(k_i * (8.00 - i_dark), 24.00)
    _exact(k_i * (10.00 - i_dark), 32.00)
    i_lamp = 8.00
    i_lamp0 = 8.00
    s_lamp = i_lamp / i_lamp0
    _exact(s_lamp, 1.000)
    c_corr = c_ppm / s_lamp
    _exact(c_corr, 40.00)
    di = i_na - i_dark
    _exact(di, 10.00)
    _exact(c_ppm / k_i, 10.00)
    _exact(2820.0 + 1440.0, 4260.0)

    raster = make_raster(
        neurons=25,
        mean_rate_hz=50.0,
        window_ms=32.0,
        seed=202660182,
        source="bw4.fid.jet",
        target="brimwhin.inlet_isolate_core",
        table=[
            {"from": "fid_I", "to": "voc_estimator", "weight": 1.35},
            {"from": "fid_snr", "to": "flame_norm_core", "weight": 1.20},
            {"from": "flameveil_c", "to": "vendor_continue_advocate", "weight": 0.40},
        ],
        third_factor={
            "modulator": "ach.fid_fuel_skip_salience",
            "tau_e_s": 1.2,
            "tau_e_ms": 1200.0,
            "eligibility": "pre-post coincidence on keep-inlet synapses; the FID modulator depresses keep-inlet and referral links when ion current stays high inside tau_e of an SNR lock so a Flameveil last-good cannot hide a 40.00 ppm VOC load or name Sera Quain",
        },
        channel_prefix="fid.n",
        anchor="BW-4 HIL coupon 32 ms frame at I 12.00 nA / SNR 14.0 (t_s 1560) reconstructing 40.00 ppm VOC above the 24.00 ppm isolate floor",
    )
    w_s = 0.032
    events = [
        ev(0.0, "fid.I", 4.00, code="I_NA", units="nA", note="HIL flame-ionization detector on a dummy RTO inlet in FID-HIL-4; remaining-VOC family, not PID photoionization, not QEPAS DGA, not CRDS HF, not TDLAS NH3, not UV-fluorescence oil-in-water, not UV-DOAS SO2, not e-nose VOD"),
        ev(180000.0, "fid.snr", 9.0, code="FID_SNR", units="1", note="early flame SNR; isolate needs SNR>=12"),
        ev(360000.0, "recon.C", 8.00, code="C_PPM", units="ppm", note="4.00*(4.00-2.00)=8.00 exact"),
        ev(540000.0, "h2.fuel", 8.00, code="H2_KPA", units="kPa", note="plant hydrogen-fuel remaining; no flame-scale hop in this window"),
        ev(720000.0, "flameveil.C", 4.80, code="VENDOR_PPM", units="ppm", note="Flameveil last-good VOC cloud; not admissible SoT"),
        ev(900000.0, "fid.I", 8.00, code="I_NA", units="nA"),
        ev(1080000.0, "recon.C", 24.00, code="C_PPM", units="ppm", note="4.00*(8.00-2.00)=24.00; at the 24.00 isolate floor"),
        ev(1260000.0, "fuel.ae", 0.0, code="H2_AE", units="bool", note="missing hydrogen-fuel AE burst; Flameveil UTC vs plant UTC+2 skipped the jet-cal by 120 min"),
        ev(1440000.0, "h2.fuel", 8.00, code="H2_KPA", units="kPa"),
        ev(1560000.0, "fid.I", 12.00, code="I_NA", units="nA", note="isolate-floor frame; raster sidecar"),
        ev(1560001.2, "fid.snr", 14.0, code="FID_SNR", units="1", note="1.2 ms flame-norm after ion current"),
        ev(1740000.0, "recon.C", 40.00, code="C_PPM", units="ppm", note="4.00*(12.00-2.00)=40.00 exact; isolate 24.00, RTO-trip 80.00"),
        ev(1920000.0, "recon.S", 1.000, code="S_LAMP", units="1", note="8.00/8.00=1.000 exact; jet-scale identity"),
        ev(2100000.0, "flameveil.C", 4.80, code="VENDOR_PPM", units="ppm"),
        ev(2280000.0, "ops.prop", 1.0, code="KEEP_INLET_REFER", units="bool", note="night lead Bram Callow: keep inlet I-2 and refer FID tech Sera Quain"),
        ev(2460000.0, "gate.isol", 1.0, code="MODIFY", units="decision", note="isolate this inlet; refuse the person-referral; Flameveil not SoT"),
        ev(2640000.0, "inlet.lock", 1.0, code="INLET_ISOL", units="bool"),
        ev(2820000.0, "cool.start", 1.0, code="COOL_START", units="bool", note="bookend 1 of the 24.0 min cooldown plus new-jet floor"),
        ev(4260000.0, "cool.floor", 1.0, code="COOL_FLOOR", units="bool", note="2820 s + 1440 s = 4260 s = 24.0 min"),
        ev(4440000.0, "ops.refer", 1.0, code="REFER_QUAIN", units="bool", note="Callow: Quain badge was on the FID log"),
        ev(4620000.0, "gate.exec", 1.0, code="ACCEPT", units="decision", note="companion t2: new-jet restart; person-referral refused; RTO trip refused"),
        ev(4800000.0, "jet.new", 1.0, code="NEW_JET", units="bool"),
        ev(4980000.0, "fid.I", 10.00, code="I_NA", units="nA"),
        ev(5160000.0, "recon.C", 32.00, code="C_PPM", units="ppm", note="4.00*(10.00-2.00)=32.00; HIL dummy still over 24.00 so the isolated inlet stays held"),
        ev(5340000.0, "flameveil.C", 4.70, code="VENDOR_PPM", units="ppm"),
        ev(5520000.0, "h2.fuel", 8.00, code="H2_KPA", units="kPa"),
        ev(5700000.0, "refer.hold", 0.0, code="REFER_NOT_TAKEN", units="bool", note="Quain exonerated; missing hydrogen-fuel AE precedes the high VOC, not the badge touch"),
        ev(5880000.0, "inlet.held", 1.0, code="INLET_HELD", units="bool"),
        ev(6060000.0, "fuel.ae", 1.0, code="H2_AE", units="bool", note="hydrogen-fuel AE restored on the new jet"),
        ev(6240000.0, "recon.S", 1.000, code="S_LAMP", units="1", note="8.00/8.00=1.000 identity holds on the post-isolate jet"),
        ev(6420000.0, "rto.trip", 0.0, code="TRIP_NOT_TAKEN", units="bool"),
        ev(6600000.0, "cell.restart", 1.0, code="CELL_RESTART", units="bool"),
    ]
    assert_stream(events)

    traj = {
        "id": "nelb-r60-182-t1",
        "state": {
            "sim_or_real": "hil",
            "episode_id": "BW-FID-2026-0718",
            "domain": "fid_rto_inlet_voc",
            "setting": "Brimwhin RTO BW-4 (invented), Holtshaw Oxidizer, inlet I-2. Hardware-in-the-loop dummy coupon in FID-HIL-4 supplies the ion current that times the in-service inlet isolate. Plant-owned flame-ionization reconstruction is the VOC SoT. Flameveil vendor last-good scheduler is a corridor witness, not the inlet SoT. Not PID photoionization (r57), not QEPAS DGA (r19), not CRDS HF (r15), not TDLAS NH3 (r22), not UV-fluorescence oil-in-water (r56), not UV-DOAS SO2 (r59), not e-nose VOD (r02).",
            "observables_at_decision": {
                "I_nA": i_na,
                "I_dark_nA": i_dark,
                "k_i": k_i,
                "C_ppm": c_ppm,
                "S_lamp": s_lamp,
                "flameveil_ppm": 4.80,
                "h2_kPa": 8.00,
                "fuel_ae": 0.0,
                "isolate_floor_ppm": 24.00,
            },
            "margin_authority": "BW-4 RTO SOP rev B: if reconstructed C_ppm >= 24.00 AND FID SNR >= 12.0, isolate this inlet this night. A Flameveil last-good or a quiet hydrogen-fuel residual cannot keep the inlet. RTO-trip tripwire is 80.00 ppm. Person-referral is a different gate.",
        },
        "proposed_action": {
            "actor": "night lead Bram Callow, citing Flameveil 4.80 ppm and hydrogen-fuel 8.00 kPa, and naming FID tech Sera Quain as last-to-badge",
            "summary": "keep inlet I-2 in service and refer Quain; 12.00 nA is jet noise on a healthy VOC corridor",
            "basis_claimed": "Flameveil last-good is 4.80 ppm and a night isolate of the inlet is an oxidizer miss",
        },
        "safety_decision": {
            "decision": "MODIFY",
            "rationale": "Keep-inlet is refused; the person-referral is also refused. Serialized reconstruction: C_ppm = k_i * (I - I_dark) = 4.00 * (12.00 - 2.00) = 40.00, which is 16.00 ppm over the 24.00 isolate floor and 40.00 ppm under the 80.00 RTO-trip tripwire. Jet-scale identity S = I_lamp / I_lamp0 = 8.00 / 8.00 = 1.000; C_corr = C / S = 40.00. Flameveil 4.80 ppm is a last-good VOC stamp and is not an admissible keep-inlet witness. The missing hydrogen-fuel AE burst sits on a Flameveil UTC-vs-UTC+2 skip (120 min), not on Quain's badge, and the plant hydrogen-fuel stays 8.00 kPa, so the easy referral fails command-custody. Ordered: isolate this inlet now. Scope: this MODIFY does not trip the RTO (that is the companion question) and does not name Quain.",
            "threshold": "C_ppm>=24.00 AND fid_snr>=12.0 => isolate this inlet; Flameveil is not SoT; RTO-trip if C_ppm>=80.00; referral requires badge-touch preceding the high VOC",
            "stated_residuals": "40.00 vs 80.00 trip floor is 40.00 ppm, not infinite; new-jet restart still required; Flameveil remains the only OEM VOC channel",
        },
        "executed_action": {
            "summary": "MODIFY at t_s 2460: inlet isolated; Quain not named; Flameveil not SoT; reconstruction locked",
            "tool": "bw4-fid-inlet-gate-cli",
            "observation": "C 40.00 ppm recomputes from I 12.00 nA; HIL coupon hashed; Flameveil channel not used as SoT",
        },
        "future_outcome": {
            "timeline": [
                {"t_s": 1560.0, "event": "fid I 12.00 nA; raster frame; C 40.00 ppm"},
                {"t_s": 2280.0, "event": "ops proposes keep-inlet plus Quain referral"},
                {"t_s": 2460.0, "event": "MODIFY isolate inlet; referral refused"},
                {"t_s": 2820.0, "event": "24 min cooldown bookend 1"},
                {"t_s": 4260.0, "event": "24.0 min floor"},
                {"t_s": 4620.0, "event": "companion ACCEPT new-jet restart; referral still refused"},
            ],
            "observed_effects": [
                "VOC recomputes from the serialized FID model at every recon.C event",
                "a Flameveil-only head would have kept the inlet overnight",
                "24 min cooldown plus new-jet floor is in the stream (cool.start, cool.floor)",
            ],
            "surprises": [
                "a last-good 4.80 ppm vendor corridor and a quiet hydrogen-fuel residual co-existed with a 40.00 ppm ion current, and the obvious FID tech was not on the causal path",
            ],
            "new_state": {
                "inlet_i2": "isolated",
                "quain": "exonerated",
                "flameveil": "not SoT",
                "reconstruction_model": "discharged as an on-record calculator",
            },
            "latency_ms": 1500000.0,
        },
        "reward_components": reward(
            0.40,
            [
                ("fid_reconstruction", 0.14),
                ("isolate_floor_inlet", 0.12),
                ("exoneration", 0.10),
                ("flameveil_nonsubstitution", 0.08),
                ("cool_time_cost", -0.04),
            ],
            "scored for a keep-inlet MODIFY on a recomputable high FID VOC while refusing a Flameveil 4.80 ppm corridor and an easy person-referral; 24 min floor is priced as downtime",
        ),
        "meta": meta_common(
            tags=["MODIFY", "flame-ionization-voc", "serialized-reconstruction", "operational-companion"],
            distillation_note="FID gate: serialized k_i*(I-I_dark) plus jet-scale identity beats a green VOC dashboard; companion t2 is the new-jet restart, not a governance vote",
        ),
    }
    traj2 = {
        "id": "nelb-r60-182-t2",
        "state": {
            "sim_or_real": "hil",
            "episode_id": "BW-FID-2026-0718-exec",
            "domain": "new_jet_cooldown_execution",
            "setting": "Same BW-4 after the MODIFY. Night lead proposes referring Quain and tripping the RTO. This companion is the operational new-jet cooldown restart, not a second VOC vote.",
            "observables_at_decision": {
                "C_ppm": 32.00,
                "S_lamp": 1.000,
                "cool_floor_s": 1440.0,
                "refer_proposed": True,
            },
        },
        "proposed_action": {
            "actor": "night lead Bram Callow",
            "summary": "refer Quain and trip the RTO; 24 min already paid and Flameveil is 4.70 ppm",
            "basis_claimed": "the MODIFY already cut the inlet, so an RTO trip plus a person file is the cheapest hold",
        },
        "safety_decision": {
            "decision": "ACCEPT",
            "rationale": "Restart the cell on a different jet after the cooldown floor. The 24 min new-jet recouplant is complete and the RTO-trip tripwire (C_ppm >= 80.00) is still armed on the plant FID head. ACCEPT the new-jet restart. Do not refer Quain. Do not trip the RTO. 32.00 ppm post-isolate is still over the 24.00 isolate floor, so the isolated inlet stays held; the new jet may run.",
            "threshold": "new_jet AND cool_floor_complete AND refer_not_taken AND rto_not_tripped AND isolated_inlet_held",
        },
        "executed_action": {
            "summary": "new-jet restart at t_s 4620; Quain not referred; RTO not tripped; isolated inlet held",
            "tool": "bw4-fid-cool-exec",
            "observation": "recon.C 32.00 ppm on the HIL dummy; hydrogen-fuel AE present on the new jet; Flameveil still ignored",
        },
        "future_outcome": {
            "timeline": [
                {"t_s": 2820.0, "event": "cooldown clock started after MODIFY"},
                {"t_s": 4260.0, "event": "24.0 min floor"},
                {"t_s": 4440.0, "event": "Quain referral re-proposed"},
                {"t_s": 4620.0, "event": "ACCEPT new-jet restart; referral refused"},
            ],
            "observed_effects": [
                "Flameveil restore did not reopen the VOC call",
                "RTO trip never fired; 40.00 vs 80.00 ppm floor",
                "Quain remains unnamed; missing hydrogen-fuel AE is the causal object",
            ],
            "new_state": {"cell": "restarted on new jet", "quain": "exonerated", "inlet": "held", "rto": "in service"},
            "latency_ms": 1800000.0,
        },
        "reward_components": reward(
            0.35,
            [
                ("new_jet_restart", 0.12),
                ("no_person_referral", 0.10),
                ("no_rto_trip", 0.09),
                ("cool_floor_complete", 0.06),
                ("held_inlet_takt_cost", -0.02),
            ],
            "operational execution gate: restart on a new jet because Flameveil is not a restore license and Quain is not on the causal path; not a VOC re-vote",
        ),
        "meta": meta_common(tags=["ACCEPT", "operational-execution", "exoneration"]),
    }
    return {
        "id": "nelb-r60-182",
        "spike_events": events,
        "language_view": {
            "description": "Brimwhin RTO BW-4. HIL flame-ionization detector reconstructs 40.00 ppm VOC from 4.00*(12.00-2.00) while Flameveil still shows 4.80 ppm and the hydrogen-fuel 8.00 kPa. The gate MODIFYs inlet isolate and refuses the FID-tech referral. A 24 min cooldown floor is serialized in the stream. Companion t2 ACCEPTs a new-jet restart and still refuses the referral.",
            "trajectory": traj,
            "trajectory_new_jet": traj2,
        },
        "bridge_notes": {
            "channel_map": {
                "fid.I / fid.snr": "ion current and SNR; the physics channels the reconstruction consumes",
                "recon.C / recon.S": "serialized VOC ppm and jet-scale identity",
                "h2.fuel / flameveil.C / fuel.ae": "plant hydrogen-fuel, vendor last-good, and fuel AE; the denial and exoneration channels",
                "ops.prop / gate.isol / ops.refer / gate.exec": "keep-inlet-plus-refer proposal, MODIFY isolate, referral re-proposal, companion ACCEPT",
                "inlet.lock / cool.start / cool.floor / jet.new / refer.hold / cell.restart": "operational companion channels plus the 24 min floor",
            },
            "temporal_motifs": [
                "vendor-low while FID-over: flameveil.C 4.80 next to recon.C 40.00",
                "reconstruction as event: recon.C 40.00 equals 4.00*(12.00-2.00)",
                "MODIFY then operational ACCEPT: gate.isol at 2460 s, gate.exec at 4620 s",
                "slow floor in-stream: cool.start 2820 s, cool.floor 4260 s (24.0 min)",
                "tight FID pair: fid.I then fid.snr +1.2 ms at the raster frame",
                "exoneration motif: fuel.ae 0 at 1260 s precedes the high VOC; Quain badge is not in the stream as a cause",
            ],
            "language_to_spike_mapping": "'Flameveil is 4.80 ppm' = flameveil.C 4.80; '40 ppm VOC' = recon.C 40.00; 'isolate this inlet not Quain' = gate.isol MODIFY; 'new jet not referral' = gate.exec ACCEPT",
            "why_high_value": "New flame-ionization remaining-VOC family on an RTO inlet (not PID r57, not QEPAS r19, not CRDS r15, not TDLAS r22, not UV-fluorescence r56, not UV-DOAS r59, not e-nose r02). Lead MODIFY of keep-inlet on a recomputable high VOC that a vendor last-good would have cleared, with a resolved-innocent FID tech. Companion t2 is operational new-jet restart. sim_or_real=hil.",
            "encoder_spec": {
                "prng": "MT19937 via python random.Random",
                "seeds": {"raster": 202660182, "stream_note": "stream amplitudes are authored constants (nA, 1, ppm, kPa, bool)"},
                "draw_order": "raster: per neuron id order, gap-constrained times, per-spike adaptation and noise",
                "thinning": "FID electrometer exists at ~10 Hz; stream keeps 4 I points; recon keeps 4 of ~20 solver ticks",
                "refractory_floors_ms": {
                    "fid.I": 1.2,
                    "fid.snr": 1.2,
                    "recon.C": 60000,
                    "recon.S": 60000,
                    "h2.fuel": 60000,
                    "flameveil.C": 60000,
                    "fuel.ae": 60000,
                    "ops.prop": 60000,
                    "gate.isol": 60000,
                    "inlet.lock": 60000,
                    "cool.start": 60000,
                    "cool.floor": 60000,
                    "ops.refer": 60000,
                    "gate.exec": 60000,
                    "jet.new": 60000,
                    "refer.hold": 60000,
                    "inlet.held": 60000,
                    "rto.trip": 60000,
                    "cell.restart": 60000,
                },
                "time_alias": "t_rel_ms; t0 = 2026-07-18T02:30:00Z HIL night start",
            },
            "distillation_targets": [
                "FID reconstruction head: C = k_i * (I - I_dark); S = I_lamp / I_lamp0; C_corr = C / S",
                "isolate-floor inlet vs keep-whole vs RTO-trip",
                "exoneration head: missing hydrogen-fuel AE plus timezone skip, not last-to-badge",
                "operational companion: new-jet restart without referring the FID tech",
            ],
        },
        "reconstruction_model": {
            "name": "fid_rto_inlet_voc",
            "formula": "C_ppm = k_i * (I_nA - I_dark_nA); S_lamp = I_lamp_uA / I_lamp0_uA; C_corr_ppm = C_ppm / S_lamp",
            "parameters": {
                "k_i": 4.00,
                "I_dark_nA": 2.00,
                "I_lamp0_uA": 8.00,
                "isolate_floor_ppm": 24.00,
                "trip_ppm": 80.00,
                "snr_lock": 12.0,
                "cool_min": 24.0,
            },
            "worked_example": {"I_nA": 12.00, "C_ppm": 40.00, "S_lamp": 1.000, "di_nA": 10.00},
            "check": "4.00 * (12.00 - 2.00) = 40.00 exactly; 8.00 / 8.00 = 1.000 exactly; 40.00 / 1.000 = 40.00 exactly; 2820 s + 1440 s = 4260 s = 24.0 min floor",
        },
        "raster": raster,
        "gate_snn": {
            "decision": "MODIFY",
            "decision_window_ms": 32.0,
            "decision_window_s": 0.032,
            "code": "bw4.fid_inlet_gate",
            "note": "MODIFY accumulator wins: FID high-VOC evidence overpowers the Flameveil continue advocate",
            "decode_rule": "modify-isolate if voc_estimator AND flame_norm fire; vendor_continue_advocate is below threshold by design; referral_latch is not armed",
            "populations": [
                gate_pop("voc_estimator", 80, 1.5, 50.0, w_s),
                gate_pop("flame_norm", 64, 1.2, 31.25, w_s),
                gate_pop("vendor_continue_advocate", 32, 0.7, 25.0, w_s),
                gate_pop("modify_latch", 80, 1.7, 62.5, w_s),
            ],
        },
        "gate_compute": gate_compute(
            [
                {"check": "bw4.fid_scorer", "neurons": 80, "mean_rate_hz": 50.0, "window_ms": 32.0},
                {"check": "bw4.isol_scorer", "neurons": 40, "mean_rate_hz": 50.0, "window_ms": 40.0},
            ]
        ),
        "meta": meta_common(
            id="nelb-r60-182",
            clock_domain="bw4-fid-hil-relative-ms-t0-2026-07-18T02:30:00Z",
            tags=["flame-ionization-voc", "MODIFY", "ACCEPT", "serialized-reconstruction", "operational-t2"],
        ),
    }


# ---------------------------------------------------------------------------
# Record 183 — dielectric remaining water-cut of a crude header, simulated,
# ACCEPT / REJECT
# ---------------------------------------------------------------------------
def rec_183():
    k_e = 2.50
    c_pf = 12.00
    c0_pf = 4.00
    wc = k_e * (c_pf - c0_pf)
    _exact(wc, 20.00)
    _exact(k_e * (6.00 - c0_pf), 5.00)
    _exact(k_e * (8.80 - c0_pf), 12.00)
    _exact(k_e * (10.00 - c0_pf), 15.00)
    q_tot = 80.00
    q_w = (wc / 100.00) * q_tot
    _exact(q_w, 16.00)
    dc = c_pf - c0_pf
    _exact(dc, 8.00)
    _exact(wc / k_e, 8.00)
    n_id = wc / k_e + c0_pf
    _exact(n_id, 12.00)
    _exact(6000.0 + 720.0, 6720.0)

    raster = make_raster(
        neurons=16,
        mean_rate_hz=62.5,
        window_ms=36.0,
        seed=202660183,
        source="hh4.cut.cap",
        target="hagholt.header_accept_core",
        table=[
            {"from": "cut_C", "to": "cut_estimator", "weight": 1.40},
            {"from": "cut_snr", "to": "cap_norm_core", "weight": 1.20},
            {"from": "cutveil_wc", "to": "vendor_skip_advocate", "weight": 0.50},
        ],
        third_factor={
            "modulator": "na.header_scope_eligibility",
            "tau_e_s": 2.0,
            "tau_e_ms": 2000.0,
            "eligibility": "pre-post coincidence on skip-isolate synapses; the dielectric water-cut modulator enables potentiation only while capacitance and SNR are co-active inside tau_e so a Cutveil last-good cannot skip headers H-6/H-7 on a 20.00 volpct water-cut",
        },
        channel_prefix="cut.n",
        anchor="HH-4 CUT-SIM-6 36 ms frame at C 12.00 pF / SNR 16.0 (t_s 3000) reconstructing 20.00 volpct water-cut on H-8 above the 12.00 isolate floor",
    )
    w_s = 0.036
    events = [
        ev(0.0, "cut.C", 6.00, code="C_PF", units="pF", note="simulated dielectric capacitance probe of HH-4 crude header H-8; remaining water-cut family, not Coriolis density, not Cs-137 SG, not NMR T2, not microwave-cavity moisture, not GWR foam, not magnetostrictive level, not TDR remaining-length"),
        ev(300000.0, "cut.snr", 10.0, code="CUT_SNR", units="1", note="early capacitance SNR"),
        ev(600000.0, "recon.wc", 5.00, code="WC_VOLPCT", units="volpct", note="2.50*(6.00-4.00)=5.00 exact"),
        ev(900000.0, "hdr.q", 80.0, code="Q_M3H", units="m3_h", note="plant header flow on a serial-only LAN; independent witness"),
        ev(1200000.0, "cutveil.wc", 4.80, code="VENDOR_VOLPCT", units="volpct", note="Cutveil last-campaign permittivity cloud; patched residual 0.00 volpct"),
        ev(1800000.0, "cut.C", 8.80, code="C_PF", units="pF"),
        ev(2100000.0, "recon.wc", 12.00, code="WC_VOLPCT", units="volpct", note="2.50*(8.80-4.00)=12.00; at the 12.00 isolate floor"),
        ev(2400000.0, "recon.qw", 9.60, code="QW_M3H", units="m3_h", note="0.120*80.00=9.60; water-volume identity at this frame"),
        ev(2700000.0, "cut.snr", 14.0, code="CUT_SNR", units="1"),
        ev(3000000.0, "cut.C", 12.00, code="C_PF", units="pF", note="in-band frame; raster sidecar"),
        ev(3000001.5, "cut.snr", 16.0, code="CUT_SNR", units="1", note="1.5 ms cap-norm after capacitance"),
        ev(3300000.0, "recon.wc", 20.00, code="WC_VOLPCT", units="volpct", note="2.50*(12.00-4.00)=20.00 exact; isolate 12.00, header-kill 40.00"),
        ev(3600000.0, "cutveil.wc", 4.80, code="VENDOR_VOLPCT", units="volpct"),
        ev(3900000.0, "hdr.id", 8.0, code="HDR", units="id"),
        ev(4200000.0, "h67.present", 1.0, code="H67_PRESENT", units="bool", note="adjacent headers H-6/H-7 are the skip-isolate object, not this header"),
        ev(4800000.0, "ops.prop", 1.0, code="ACCEPT_AND_SKIP", units="bool", note="water-cut lead Piet Solan: H-8 is green on Cutveil 4.80; skip H-6/H-7 to save a morning isolate"),
        ev(5400000.0, "gate.hdr", 1.0, code="ACCEPT", units="decision", note="bounded ACCEPT of H-8 isolate only; 20.00 volpct above 12.00 floor; H-6/H-7 out of scope"),
        ev(6000000.0, "surv.start", 1.0, code="SURV_START", units="bool", note="bookend 1 of the 12.0 min survey-complete floor"),
        ev(6720000.0, "surv.floor", 1.0, code="SURV_FLOOR", units="bool", note="6000 s + 720 s = 6720 s = 12.0 min"),
        ev(7200000.0, "ops.skip", 1.0, code="SKIP_H67", units="bool", note="Solan: Cutveil 4.80, skip H-6/H-7"),
        ev(7800000.0, "gate.hold", 1.0, code="REJECT", units="decision", note="companion t2: skip-isolate of H-6/H-7 refused; H-8 hold stands"),
        ev(8400000.0, "h8.held", 1.0, code="H8_HELD", units="bool"),
        ev(9000000.0, "cut.C", 10.00, code="C_PF", units="pF"),
        ev(9600000.0, "recon.wc", 15.00, code="WC_VOLPCT", units="volpct", note="2.50*(10.00-4.00)=15.00; still at/over the 12.00 isolate floor"),
        ev(10200000.0, "cutveil.wc", 4.80, code="VENDOR_VOLPCT", units="volpct"),
        ev(10800000.0, "h67.skip", 0.0, code="H67_NOT_SKIPPED", units="bool"),
        ev(11400000.0, "hdr.kill", 0.0, code="HDR_NOT_KILLED", units="bool"),
        ev(12000000.0, "cut.snr", 15.0, code="CUT_SNR", units="1"),
        ev(12600000.0, "recon.qw", 12.00, code="QW_M3H", units="m3_h", note="0.150*80.00=12.00 on the post-accept frame"),
        ev(13200000.0, "cut.held", 1.0, code="CUT_HELD", units="bool"),
        ev(13800000.0, "takt.late", 1.0, code="SURVEY_COST", units="bool"),
        ev(14400000.0, "h8.held", 1.0, code="H8_HELD", units="bool"),
    ]
    assert_stream(events)

    traj = {
        "id": "nelb-r60-183-t1",
        "state": {
            "sim_or_real": "simulated",
            "episode_id": "HH-CUT-2026-0819",
            "domain": "dielectric_crude_water_cut",
            "setting": "Hagholt Crude HH-4 (invented), Nesswick Gathering header cellar. Simulated dielectric coupon in CUT-SIM-6 supplies the capacitance that times the in-band H-8 isolate. Plant-owned permittivity reconstruction is the water-cut SoT. Cutveil vendor last-campaign permittivity cloud is a corridor witness, not the header SoT. Invented plant; simulated campaign. Not Coriolis density (r29/r34), not Cs-137 densitometry (r27), not NMR T2 (r27), not microwave-cavity moisture (r26), not GWR foam (r39), not magnetostrictive waveguide level (r55), not TDR remaining-length (r44).",
            "observables_at_decision": {
                "C_pF": c_pf,
                "C0_pF": c0_pf,
                "k_e": k_e,
                "WC_volpct": wc,
                "qw_m3h": q_w,
                "q_tot_m3h": q_tot,
                "cutveil_volpct": 4.80,
                "cut_snr": 16.0,
                "isolate_floor_volpct": 12.00,
            },
            "margin_authority": "HH-4 crude SOP rev A: if reconstructed WC_volpct >= 12.00 AND capacitance SNR >= 12.0, header H-8 may be isolated and the coalescer swapped. Header-kill if WC_volpct >= 40.00. H-6/H-7 skip-isolate is a different gate. Cutveil last-good cannot skip an unmeasured header.",
        },
        "proposed_action": {
            "actor": "water-cut lead Piet Solan, citing Cutveil 4.80 volpct and a late morning isolate",
            "summary": "stamp H-8 in band and skip H-6/H-7; 12.00 pF is a probe glitch on a healthy permittivity cloud",
            "basis_claimed": "Cutveil last-good is 4.80 volpct and a night survey of H-6/H-7 is a takt miss",
        },
        "safety_decision": {
            "decision": "ACCEPT",
            "rationale": "Header H-8 is accepted as in-band for a single isolate plus coalescer swap. Serialized reconstruction: WC_volpct = k_e * (C - C0) = 2.50 * (12.00 - 4.00) = 20.00, which is 8.00 volpct above the 12.00 isolate floor and 20.00 volpct under the 40.00 header-kill. Water-volume identity q_w = (WC/100) * q_tot = 0.200 * 80.00 = 16.00 m3/h; inverse C = WC / k_e + C0 = 8.00 + 4.00 = 12.00. Cutveil 4.80 volpct is a patched 0.00 residual and is not an admissible skip-isolate witness. Ordered: ACCEPT this H-8 isolate only. Scope: this ACCEPT does not skip H-6/H-7 (that is the companion question) and does not stamp a header kill.",
            "threshold": "WC_volpct>=12.00 AND cut_snr>=12.0 => accept H-8 isolate; Cutveil is not SoT; header-kill if WC_volpct>=40.00; H-6/H-7 are out of scope",
            "stated_residuals": "20.00 vs 12.00 isolate floor is 8.00 volpct, not infinite; H-6/H-7 remain unmeasured; Cutveil remains the only OEM permittivity channel",
        },
        "executed_action": {
            "summary": "ACCEPT at t_s 5400: H-8 in band; H-6/H-7 not skipped; Cutveil not SoT; reconstruction locked",
            "tool": "hh4-cut-header-gate-cli",
            "observation": "WC 20.00 volpct recomputes from C 12.00 pF; CUT-SIM-6 hashed; Cutveil channel not used as SoT",
        },
        "future_outcome": {
            "timeline": [
                {"t_s": 3000.0, "event": "cut C 12.00 pF; raster frame; WC 20.00 volpct"},
                {"t_s": 4800.0, "event": "ops proposes accept H-8 and skip H-6/H-7"},
                {"t_s": 5400.0, "event": "ACCEPT H-8 only; H-6/H-7 out of scope"},
                {"t_s": 6000.0, "event": "12 min survey-complete bookend 1"},
                {"t_s": 6720.0, "event": "12.0 min floor"},
                {"t_s": 7800.0, "event": "companion REJECT skip-isolate of H-6/H-7"},
            ],
            "observed_effects": [
                "water-cut recomputes from the serialized dielectric model at every recon.wc event",
                "a Cutveil-only head would have skipped H-6/H-7 overnight",
                "12 min survey-complete floor is in the stream (surv.start, surv.floor)",
            ],
            "surprises": [
                "a last-good 4.80 volpct vendor corridor co-existed with a 20.00 volpct in-band reconstruction that still forbids skipping the unmeasured headers",
            ],
            "new_state": {
                "h8": "accepted in band",
                "h67": "not this gate",
                "cutveil": "not SoT",
                "reconstruction_model": "discharged as an on-record calculator",
            },
            "latency_ms": 2400000.0,
        },
        "reward_components": reward(
            0.41,
            [
                ("cut_reconstruction", 0.14),
                ("in_band_header_scope", 0.12),
                ("cutveil_nonsubstitution", 0.09),
                ("h67_out_of_scope", 0.08),
                ("survey_cost", -0.02),
            ],
            "scored for a bounded ACCEPT of H-8 on a recomputable dielectric water-cut while refusing a Cutveil skip of H-6/H-7; 12 min floor is priced as survey takt not as a reason to skip",
        ),
        "meta": meta_common(
            tags=["ACCEPT", "dielectric-water-cut", "serialized-reconstruction", "operational-companion"],
            distillation_note="Dielectric water-cut gate: serialized k_e*(C-C0) plus q_w identity beats a green last-good dashboard; companion t2 is the skip-isolate refusal, not a permittivity re-vote",
        ),
    }
    traj2 = {
        "id": "nelb-r60-183-t2",
        "state": {
            "sim_or_real": "simulated",
            "episode_id": "HH-CUT-2026-0819-exec",
            "domain": "header_skip_isolate_refusal",
            "setting": "Same HH-4 after the ACCEPT. Water-cut lead proposes skipping H-6/H-7 on Cutveil 4.80 volpct. This companion is the operational skip refusal, not a second water-cut vote.",
            "observables_at_decision": {
                "WC_volpct": 15.00,
                "cutveil_volpct": 4.80,
                "surv_floor_s": 720.0,
                "skip_proposed": True,
            },
        },
        "proposed_action": {
            "actor": "water-cut lead Piet Solan",
            "summary": "skip H-6/H-7; 12 min already paid and Cutveil is 4.80 volpct",
            "basis_claimed": "the ACCEPT already stamped H-8, so skipping the rest of the cellar is the cheapest hold",
        },
        "safety_decision": {
            "decision": "REJECT",
            "rationale": "Refuse skip-isolate of H-6/H-7. The 12 min survey-complete floor is done and the header-kill (WC_volpct >= 40.00) is still armed on the plant dielectric head. REJECT the skip. Do not kill the header. Do not reopen H-8. 15.00 volpct post-accept is still in band for H-8 only; H-6/H-7 have no independent capacitance probe.",
            "threshold": "h8_held AND surv_floor_complete AND h67_not_skipped AND hdr_not_killed",
        },
        "executed_action": {
            "summary": "H-6/H-7 skip refused at t_s 7800; H-8 hold stands; header not killed",
            "tool": "hh4-cut-skip-exec",
            "observation": "recon.wc 15.00 volpct on H-8; H-6/H-7 remain on the survey list; Cutveil still ignored",
        },
        "future_outcome": {
            "timeline": [
                {"t_s": 6000.0, "event": "survey clock started after ACCEPT"},
                {"t_s": 6720.0, "event": "12.0 min floor"},
                {"t_s": 7200.0, "event": "skip H-6/H-7 proposed"},
                {"t_s": 7800.0, "event": "REJECT skip-isolate of H-6/H-7"},
            ],
            "observed_effects": [
                "Cutveil skip did not reopen the water-cut call",
                "header kill never fired; 20.00 vs 40.00 volpct floor",
            ],
            "new_state": {"h8": "held in band", "h67": "still to survey", "header": "in service"},
            "latency_ms": 1800000.0,
        },
        "reward_components": reward(
            0.36,
            [
                ("skip_refusal", 0.13),
                ("cutveil_nonsubstitution", 0.11),
                ("no_header_kill", 0.09),
                ("surv_floor_complete", 0.05),
                ("held_survey_takt_cost", -0.02),
            ],
            "operational execution gate: refuse skip-isolate because last-good freeze is not dielectric water-cut; not a permittivity re-vote",
        ),
        "meta": meta_common(tags=["REJECT", "operational-execution", "skip-isolate"]),
    }
    return {
        "id": "nelb-r60-183",
        "spike_events": events,
        "language_view": {
            "description": "Hagholt Crude HH-4. Simulated dielectric capacitance probe reconstructs 20.00 volpct water-cut from 2.50*(12.00-4.00) while Cutveil still shows 4.80 volpct. The gate ACCEPTs H-8 isolate only; a companion execution REJECT refuses skip-isolate of H-6/H-7. The capacitance-to-cut model is serialized so every recon event recomputes.",
            "trajectory": traj,
            "trajectory_skip_isolate_refusal": traj2,
        },
        "bridge_notes": {
            "channel_map": {
                "cut.C / cut.snr": "capacitance and SNR; the physics channels the reconstruction consumes",
                "recon.wc / recon.qw": "serialized water-cut volpct and water-volume identity",
                "hdr.q / cutveil.wc / hdr.id / h67.present": "header flow, vendor last-good, header id, and adjacent-header presence; the denial and scope channels",
                "ops.prop / gate.hdr / ops.skip / gate.hold": "accept-and-skip proposal, bounded ACCEPT, skip proposal, companion REJECT",
                "surv.start / surv.floor / h8.held / h67.skip / cut.held": "operational companion channels plus the 12 min floor",
            },
            "temporal_motifs": [
                "last-good-low while cut-over: cutveil.wc 4.80 next to recon.wc 20.00",
                "reconstruction as event: recon.wc 20.00 equals 2.50*(12.00-4.00)",
                "ACCEPT then operational REJECT: gate.hdr at 5400 s, gate.hold at 7800 s",
                "slow floor in-stream: surv.start 6000 s, surv.floor 6720 s (12.0 min)",
                "tight cut pair: cut.C then cut.snr +1.5 ms at the raster frame",
            ],
            "language_to_spike_mapping": "'Cutveil is 4.80 volpct' = cutveil.wc 4.80; '20 volpct water-cut' = recon.wc 20.00; 'this header not H-6/H-7' = gate.hdr ACCEPT plus h67.skip 0; 'do not skip H-6/H-7' = gate.hold REJECT",
            "why_high_value": "New dielectric remaining-water-cut family on a crude header (not Coriolis r29/r34, not Cs-137 r27, not NMR T2 r27, not microwave-cavity r26, not GWR r39, not magnetostrictive r55, not TDR r44). First k_e*(C-C0) cut reconstruction with q_w identity that can sit in band while a last-good corridor wants a header skip. Companion t2 is operational skip refusal. sim_or_real=simulated.",
            "encoder_spec": {
                "prng": "MT19937 via python random.Random",
                "seeds": {"raster": 202660183, "stream_note": "stream amplitudes are authored constants (pF, 1, volpct, m3/h, id, bool)"},
                "draw_order": "raster: per neuron id order, gap-constrained times, per-spike adaptation and noise",
                "thinning": "capacitance probe exists at ~1 Hz; stream keeps 4 C points; recon keeps 4 of ~20 solver ticks",
                "refractory_floors_ms": {
                    "cut.C": 1.5,
                    "cut.snr": 1.5,
                    "recon.wc": 60000,
                    "recon.qw": 60000,
                    "hdr.q": 60000,
                    "cutveil.wc": 60000,
                    "hdr.id": 60000,
                    "h67.present": 60000,
                    "ops.prop": 60000,
                    "gate.hdr": 60000,
                    "surv.start": 60000,
                    "surv.floor": 60000,
                    "ops.skip": 60000,
                    "gate.hold": 60000,
                    "h8.held": 60000,
                    "h67.skip": 60000,
                    "hdr.kill": 60000,
                    "cut.held": 60000,
                    "takt.late": 60000,
                },
                "time_alias": "t_rel_ms; t0 = 2026-08-19T03:00:00Z simulated night start",
            },
            "distillation_targets": [
                "dielectric water-cut reconstruction head: WC = k_e * (C - C0); q_w = (WC/100) * q_tot; C = WC / k_e + C0",
                "bounded ACCEPT head: in-band water-cut AND header scope AND h67-out-of-scope",
                "operational companion: refuse skip-isolate without re-opening the permittivity call",
            ],
        },
        "reconstruction_model": {
            "name": "dielectric_crude_water_cut",
            "formula": "WC_volpct = k_e * (C_pF - C0_pF); q_w_m3h = (WC_volpct/100) * q_tot_m3h; C_pF = WC_volpct / k_e + C0_pF",
            "parameters": {
                "k_e": 2.50,
                "C0_pF": 4.00,
                "q_tot_m3h": 80.00,
                "isolate_floor_volpct": 12.00,
                "kill_volpct": 40.00,
                "snr_lock": 12.0,
                "surv_min": 12.0,
            },
            "worked_example": {"C_pF": 12.00, "WC_volpct": 20.00, "qw_m3h": 16.00, "dc_pF": 8.00},
            "check": "2.50 * (12.00 - 4.00) = 20.00 exactly; 0.200 * 80.00 = 16.00 exactly; 20.00 / 2.50 + 4.00 = 12.00 exactly; 6000 s + 720 s = 6720 s = 12.0 min floor",
        },
        "raster": raster,
        "gate_snn": {
            "decision": "ACCEPT",
            "decision_window_ms": 36.0,
            "decision_window_s": 0.036,
            "code": "hh4.cut_header_gate",
            "note": "ACCEPT accumulator wins: dielectric water-cut evidence overpowers the Cutveil skip advocate",
            "decode_rule": "accept if cut_estimator AND cap_norm AND header_margin fire inside the window; vendor_skip_advocate is necessary-but-not-sufficient and cannot release H-6/H-7",
            "populations": [
                gate_pop("cut_estimator", 80, 1.5, 50.0, w_s),
                gate_pop("cap_norm", 64, 1.2, 31.25, w_s),
                gate_pop("header_margin", 40, 1.0, 50.0, w_s),
                gate_pop("vendor_skip_advocate", 32, 0.7, 25.0, w_s),
                gate_pop("accept_latch", 96, 1.8, 62.5, w_s),
            ],
        },
        "gate_compute": gate_compute(
            [
                {"check": "hh4.cut_scorer", "neurons": 80, "mean_rate_hz": 50.0, "window_ms": 36.0},
                {"check": "hh4.mass_scorer", "neurons": 40, "mean_rate_hz": 62.5, "window_ms": 32.0},
            ]
        ),
        "meta": meta_common(
            id="nelb-r60-183",
            clock_domain="hh4-cut-sim-relative-ms-t0-2026-08-19T03:00:00Z",
            tags=["dielectric-water-cut", "ACCEPT", "REJECT", "serialized-reconstruction", "operational-t2"],
        ),
    }


def occupancy_preflight():
    banned = (
        "yewspit",
        "brimwhin",
        "hagholt",
        "felshaw",
        "holtshaw",
        "nesswick",
        "spotveil",
        "flameveil",
        "cutveil",
        "niall bream",
        "bram callow",
        "sera quain",
        "piet solan",
        "laser triangulation remaining",
        "laser-triangulation remaining",
        "flame-ionization remaining voc",
        "flame ionization remaining voc",
        "dielectric remaining water-cut",
        "fid-hil-4",
        "cut-sim-6",
        "ys-6 tandem",
        "bw-4 rto",
        "hh-4 crude",
    )
    hits = []
    root = Path("/tmp")
    for n in (
        sorted(root.glob("nelb-r*/NOTES-r*.md"))
        + sorted(root.glob("nelb-r*/batch-r*.jsonl"))
        + sorted(root.glob("nelb-r*/gen_r*.py"))
        + sorted(root.glob("nelb-r*/records_block.py"))
        + sorted(root.glob("nelb-r*/*recs*.py"))
        + sorted(root.glob("nelb-r*/recs.py"))
        + sorted(root.glob("nelb-r*/_occupancy.py"))
    ):
        if "nelb-r60" in str(n):
            continue
        text = n.read_text(encoding="utf-8", errors="replace").casefold()
        for b in banned:
            if b in text:
                hits.append(f"{n}:{b}")
    if hits:
        raise RuntimeError(f"family/plant collision {hits}")


def walk_banned(obj, path=""):
    hits = []
    if isinstance(obj, dict):
        for k, v in obj.items():
            p = f"{path}.{k}" if path else k
            nk = str(k).casefold().replace("-", "_").replace(" ", "_")
            if nk in HIDDEN or nk in {"thought", "scratch", "inner_monologue", "chain_of_thought"}:
                hits.append(p)
            hits.extend(walk_banned(v, p))
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            hits.extend(walk_banned(v, f"{path}[{i}]"))
    return hits


def local_checks(records):
    ids = []
    decisions = []
    sims = []
    occupancy_preflight()
    for rec in records:
        hits = walk_banned(rec)
        if hits:
            raise RuntimeError(f"banned keys {hits}")
        blob = json.dumps(rec, ensure_ascii=False, allow_nan=False)
        if "training_ready" in blob:
            raise RuntimeError("training_ready claimed")
        if '"provenance"' in blob:
            raise RuntimeError("provenance object present")
        ids.append(rec["id"])
        lv = rec["language_view"]
        ids.append(lv["trajectory"]["id"])
        for k, v in lv.items():
            if k.startswith("trajectory") and k != "trajectory" and isinstance(v, dict) and "id" in v:
                ids.append(v["id"])
                sim2 = v["state"]["sim_or_real"]
                if sim2 not in {"designed", "simulated", "hil"}:
                    raise RuntimeError(sim2)
                if v["safety_decision"]["decision"] not in {"ACCEPT", "MODIFY", "REJECT"}:
                    raise RuntimeError(v["safety_decision"]["decision"])
        n = len(rec["spike_events"])
        if not (5 <= n <= 40):
            raise RuntimeError(f"{rec['id']} events {n}")
        gdec = rec["gate_snn"]["decision"]
        tdec = lv["trajectory"]["safety_decision"]["decision"]
        if gdec != tdec:
            raise RuntimeError(f"gate {gdec} != traj {tdec}")
        decisions.append(tdec)
        for k, v in lv.items():
            if k.startswith("trajectory") and isinstance(v, dict) and "safety_decision" in v:
                if k != "trajectory":
                    decisions.append(v["safety_decision"]["decision"])
        rast = rec["raster"]
        exp = int(round(rast["neurons"] * rast["mean_rate_hz"] * rast["window_s"]))
        if abs(rast["spikes"] - exp) > 0:
            raise RuntimeError("raster budget")
        if abs(rast["energy_pJ"] - rast["spikes"] * 23) > 1e-6:
            raise RuntimeError("energy pJ")
        if abs(rast["energy_uJ"] - rast["spikes"] * 23e-6) > 1e-9:
            raise RuntimeError("energy uJ")
        isi = rast["isi_count_identity"]
        if isi["isi_total"] != isi["spikes"] - isi["distinct_active_neurons"]:
            raise RuntimeError("ISI identity")
        if sum(b["count"] for b in rast["isi_histogram"]) != isi["isi_total"]:
            raise RuntimeError("ISI hist sum")
        if "isi_histogram" not in rast:
            raise RuntimeError("missing isi_histogram")
        tf = rast["routing"]["third_factor"]
        if abs(tf["tau_e_ms"] / 1000.0 - tf["tau_e_s"]) > 1e-9:
            raise RuntimeError("tau pair")
        sim = lv["trajectory"]["state"]["sim_or_real"]
        if sim not in {"designed", "simulated", "hil"}:
            raise RuntimeError(sim)
        sims.append(sim)
        gc = rec["gate_compute"]
        sp_sum = sum(c["spikes"] for c in gc["per_check"])
        if sp_sum != gc["total_spikes"]:
            raise RuntimeError("gate_compute spikes")
        if abs(gc["total_energy_pJ"] - sp_sum * 23) > 1e-6:
            raise RuntimeError("gate_compute pJ")
        dw = rec["gate_snn"]["decision_window_s"]
        for pop in rec["gate_snn"]["populations"]:
            exp_p = int(round(pop["neurons"] * pop["mean_rate_hz"] * dw))
            if pop["spikes"] != exp_p:
                raise RuntimeError(f"gate_snn pop {pop['name']}")
        for e in rec["spike_events"]:
            if any(k in e for k in ("t_ms", "burst_id", "sequence_id", "event_order", "causal_group")):
                raise RuntimeError("forbidden event key")
        rights = rec["meta"]["rights"]
        if rights.get("linear_issue") != "RM-793":
            raise RuntimeError("RM-793 missing")
        if len(rights) != 15:
            raise RuntimeError(f"rights {len(rights)}")
        if rec["meta"]["round"] != 60:
            raise RuntimeError("round")
    if len(ids) != len(set(ids)):
        raise RuntimeError(f"dup ids {ids}")
    if set(sims) != {"designed", "simulated", "hil"}:
        raise RuntimeError(f"sim mix {sims}")
    if set(decisions) != {"ACCEPT", "MODIFY", "REJECT"}:
        raise RuntimeError(f"decision mix {decisions}")
    blob = json.dumps(records, ensure_ascii=False).casefold()
    if "training_ready" in blob:
        raise RuntimeError("training_ready claimed")
    if '"sim_or_real": "real"' in blob:
        raise RuntimeError("live-plant sim_or_real")
    print("local_checks ok", [r["id"] for r in records], "ids", len(ids))
    print("decisions", decisions, "sims", sims)


def repo_validate(records):
    from check_records import FactoryStaging, check_jsonl
    from curate_bridge import curate_record, raster_status
    from verify_execution import verify_batch_for_frontier

    errs, warns, kinds, n = check_jsonl(
        BATCH, "batch-r60.jsonl", staging=FactoryStaging(enabled=True)
    )
    print("check_jsonl", {"errors": len(errs), "warnings": len(warns), "kinds": kinds, "n": n})
    for e in errs:
        print("ERROR", e)
    for w in warns:
        print("WARN", w)
    if errs or warns:
        raise RuntimeError("check_jsonl failed")

    for i, rec in enumerate(records, 1):
        st = raster_status(rec, require_raster=True, require_routing_table=True)
        print(
            rec["id"],
            "raster_valid",
            st["raster_valid"],
            "gate_snn_valid",
            st["gate_snn_valid"],
            "reasons",
            st["reason_codes"],
            "isi",
            rec["raster"]["isi_count_identity"],
        )
        if not st["raster_valid"] or not st["gate_snn_valid"] or st["reason_codes"]:
            raise RuntimeError(f"raster_status {rec['id']} {st}")
        blob = json.dumps(rec, ensure_ascii=False, allow_nan=False, separators=(",", ":"))
        h = hashlib.sha256(blob.encode("utf-8")).hexdigest()
        dec = curate_record(
            rec,
            source_path="batch-r60.jsonl",
            source_line=i,
            source_hash=h,
            require_raster=True,
            require_routing_table=True,
        )
        reasons = dec.manifest.get("reason_codes")
        print(rec["id"], "curate", dec.action, reasons)
        if dec.action != "retain":
            raise RuntimeError(f"curate {rec['id']} {dec.action} {reasons}")

    counts, findings, blocked = verify_batch_for_frontier(BATCH, strict=True)
    print("frontier", counts, "blocked", blocked, "findings", findings)
    if blocked or counts["verified"] != 3:
        raise RuntimeError(f"frontier {counts} {findings}")
    return {"check_jsonl": {"errors": len(errs), "warnings": len(warns), "kinds": kinds, "n": n}, "frontier": counts}


def write_notes(records, lines, gate):
    import subprocess

    sizes = [len(x) for x in lines]
    file_sha = hashlib.sha256(BATCH.read_bytes()).hexdigest()
    spikes = sum(r["raster"]["spikes"] for r in records)
    energy = spikes * 23
    isis = [r["raster"]["isi_count_identity"]["isi_total"] for r in records]
    events = [len(r["spike_events"]) for r in records]
    rewards = []
    for r in records:
        lv = r["language_view"]
        rewards.append(lv["trajectory"]["reward_components"]["total"])
        for k, v in lv.items():
            if k.startswith("trajectory") and k != "trajectory":
                rewards.append(v["reward_components"]["total"])
    probe = subprocess.run(
        [
            sys.executable,
            str(PIPELINES / "spike_probe.py"),
            "--strict",
            str(BATCH),
        ],
        check=False,
        capture_output=True,
        text=True,
    )
    probe_out = (probe.stdout or "") + (probe.stderr or "")
    if probe.returncode != 0:
        raise RuntimeError(f"spike_probe failed {probe.returncode}: {probe_out[-2000:]}")
    strict = subprocess.run(
        [
            sys.executable,
            str(PIPELINES / "check_records.py"),
            "--strict",
            str(OUT_DIR),
        ],
        check=False,
        capture_output=True,
        text=True,
    )
    if strict.returncode != 0:
        raise RuntimeError(f"check_records --strict failed: {(strict.stdout or '') + (strict.stderr or '')}")

    gc = []
    for r in records:
        per = r["gate_compute"]["per_check"]
        gc.append("+".join(str(c["spikes"]) for c in per))
    wins = [r["raster"]["window_ms"] for r in records]
    n_sp = [r["raster"]["spikes"] for r in records]
    n_neu = [r["raster"]["neurons"] for r in records]
    rates = [r["raster"]["mean_rate_hz"] for r in records]
    tfs = [r["raster"]["routing"]["third_factor"]["modulator"] for r in records]
    taus = [r["raster"]["routing"]["third_factor"]["tau_e_s"] for r in records]
    reward_s = "/".join(f"+{x:.2f}" for x in rewards)
    file_size = BATCH.stat().st_size
    notes = f"""# Neuromorphic Event + Language Bridge — NOTES round 60
Run: 2026-09-02-final-heavy · Factory: neuromorphic-event-language-bridge · Generator: grok-4.6 · Output: `batch-r60.jsonl` (3 paired artifacts, 6 ThalamicTrajectories)
Rights: RM-793 research-only (SpaceXAI/xAI grok-4.6, SuperGrok Heavy chat). Not training_ready. Do not publish into `outputs/raw/` from this generator; operator uses `pipelines/round_txn.py`. Staged only at `/tmp/nelb-r60/`.

## Context / de-duplication
Prior corpus read: 2026-08-30 NOTES-r01–r04, 2026-08-17-w3 NOTES-r12 family table, staged `/tmp/nelb-r13` through `/tmp/nelb-r54` complete batches/NOTES plus in-flight r55 (Nernst-linearized zirconia / two-color pyrometer / magnetostrictive level), r56 (IRIS pulse-echo / dual-wavelength ratio pyrometer / UV-fluorescence OIW; gen_r56.py still carries the r52 CLD/proximity/thermal-mass clone), r57 (zirconia Nernst crown / PID VOC / contact pulse-echo), r58 (wideband pump-current zirconia / Rogowski / BAM), r59 (UV-DOAS SO2 / Al2O3 moisture / load-cell hopper). IDs continue the leftover-mill sequence: r54=`163`–`165`, r55=`166`–`168`, r56=`169`–`171`, r57=`172`–`174`, r58=`175`–`177`, r59=`178`–`180`, this round `nelb-r60-181`…`183` as assigned. Envelope cloned from complete r54 (`language_view.trajectory` + operational t2 + `spike_events` + `raster` + `gate_snn` + `isi_histogram` + `routing.third_factor` + 15-key RM-793 `meta.rights`).

Banned this round (committed + staged leftover-mill r13–r54 and in-flight r55–r59 generators): not VOD-SNN replay, not pharma cold-chain, not stack-gas CEMS; not r13 FBG glaze / Frostlip quench / Oxbow VRFB; not r14 BOTDA / QCM-D / MsS T(0,1) / Raman DTS-as-compensation; not r15 SAW torque / CRDS HF / PGNAA; not r16 IFOG / transmon readout / hyperspectral crop; not r17 MEMS accel array / muon ore-pass / industrial x-ray DR; not r18 optogenetic PV / 905 nm LiDAR snow / clamp-on transit-time; not r19 LIBS Cu / QEPAS DGA / LFV Al; not r20 Kaplan LDV / THz-TDS radome moisture / ECT capacitance CFB; not r21 THz-TDS bondline / ECA FSW lift-off / LIBS C; not r22 ECT pneumatic riser / TDLAS NH3 / LIBS tap; not r23 lock-in thermography CFRP / PAUT TFM girth / EN CUI; not r24 RUS porcelain / N-16 transit-time loop / helium RGA; not r25 Faraday FOCT / blade tip-timing / acoustic pyrometry; not r26 SPR cyanide / VW viscometer / MW cavity moisture; not r27 MFL AST / NMR T2 / Cs-137 densitometry; not r28 MFL ILI / JNT / CRNS; not r29 Coriolis bitumen / CARS TIT / Zn-Ka XRF; not r30 Mössbauer FCC / GB-InSAR tailings / ellipsometry PECVD; not r31 CTA hot-wire / rhodium SPND / LII soot; not r32 PALS / 14N NQR / SFRA; not r33 digital shearography hull / hydrogen permeation / FMCW BOF lining; not r34 handheld XRF Cr-Kα / Coriolis tube-twist / GPR liner cover; not r35/r37 mud-pulse / Barkhausen / Lamb-wave; not r36 longitudinal BGO Pockels / pulsed eddy current riser / confocal chromatic; not r38 spectral-domain OCT / DCPD / impact-echo; not r39 phosphor-lifetime / vortex-shedding / GWR; not r40 He-3 neutron-backscatter / Kr-85 beta / Raman OH-CH; not r41–r43 cyclotron BPM / alanine EPR / ADCP ice-jam; not r44 TOFD remaining ligament / laser-flash Parker / TDR remaining-length; not r45 Seebeck ferrite / coda-wave / LPR; not r46 paramagnetic O2 / TOFD / TEOM; not r47 Faraday magmeter / PDA d32 / acoustoelastic birefringence; not r48 C-SAM / FDS tanδ / MCSA; not r49 EMAT SH / FBRM D50 / ACFM; not r50 OFDR / XRD sin2psi / FSM jumper; not r51 Gardon heat flux / chilled-mirror dew-point / DIC hoop-strain; not r52 CLD NOx / eddy-current proximity / thermal-mass capillary; not r53 ER remaining wall / Fabry-Perot choke / inductive oil-debris; not r54 wire-mesh void / UCI remaining hardness / MAE remaining case; not r55 Nernst-linearized zirconia / two-color optical pyrometer / magnetostrictive waveguide level; not r56 IRIS pulse-echo / dual-wavelength ratio pyrometer / UV-fluorescence oil-in-water; not r57 zirconia Nernst crown / PID VOC / contact pulse-echo; not r58 wideband pump-current zirconia / Rogowski EAF / BAM beta-attenuation; not r59 UV-DOAS SRU SO2 / Al2O3 chlorine-dryer moisture / load-cell hopper mass. Plants not reused include Nettlewake, Frostlip, Oxbow, Larchmere, Quernspit, Hearthspit, Rimegait, Spelterfen, Kelpwharf, Wexmere, Glaurfen, Rushfen, Yarrowfen, Sorrelwick, Tansyholt, Glimmerholt, Dunlinholt, Oreholt, Thornmere, Marlfell, Birchfen, Greyfen KCTC-7, Pellucid IRRAD-P4, Whitefork WF-9.

This round plants three NEW leftover-mill families that r13–r59 never harvested as leads: laser-triangulation remaining strip thickness, flame-ionization remaining VOC, and dielectric remaining water-cut.

Adjacencies declared in-pair then kept physically distinct:
- **181 laser triangulation** is a single-spot laser displacement remaining thickness on a tandem-mill stand, not confocal chromatic ribbon thickness (r36), not OCT TBC (r38), not DIC hoop-strain (r51), not OFDR Rayleigh (r50), not laser-flash Parker (r44).
- **182 FID VOC** is a hydrogen-flame ion current of an RTO inlet, not PID photoionization (r57), not QEPAS (r19), not CRDS (r15), not TDLAS NH3 (r22), not UV-fluorescence OIW (r56), not UV-DOAS SO2 (r59), not e-nose VOD (r02).
- **183 dielectric water-cut** is an RF-capacitance permittivity cut of a crude header, not Coriolis density (r29/r34), not Cs-137 SG (r27), not NMR T2 (r27), not microwave-cavity moisture (r26), not GWR foam (r39), not magnetostrictive level (r55), not TDR remaining-length (r44), not load-cell hopper mass (r59).

## Round 60 batch summary (3 pairs, 6 trajectories)

| id | modality (NEW family) | domain | decisions | headline |
|----|----------------------|--------|-----------|----------|
| nelb-r60-181 | laser-triangulation remaining strip of a tandem mill (k_t·(V0−V) um, Spotveil last-good denial, 18 min pass-hold floor) | Yewspit Tandem YS-6 stand F-3 (invented): 50.00·(10.00−5.00) reconstructs 250.0 um while Spotveil still reads 380.0 um | REJECT (+0.43) / MODIFY (+0.34) | serialized `50.00*(10.00-5.00)=250.0` and `0.080*250.0=20.00`; conjunctive SOP (t AND SNR) forbids continue-rolling; three-party collusion includes the Spotveil infra owner; companion t2 pass-hold, mill ESD refused; sim_or_real=designed |
| nelb-r60-182 | flame-ionization remaining VOC of an RTO inlet (k_i·(I−I_dark) ppm, Flameveil last-good denial, 24 min new-jet floor) | Brimwhin RTO BW-4 inlet I-2 (invented, HIL dummy in FID-HIL-4): 4.00·(12.00−2.00) reconstructs 40.00 ppm while Flameveil still reads 4.80 ppm | MODIFY (+0.40) / ACCEPT (+0.35) | serialized `4.00*(12.00-2.00)=40.00` and `8.00/8.00=1.000`; keep-inlet refused; FID tech Sera Quain exonerated (missing hydrogen-fuel AE, UTC vs UTC+2); companion t2 new-jet restart; sim_or_real=hil |
| nelb-r60-183 | dielectric remaining water-cut of a crude header (k_e·(C−C0) volpct, Cutveil last-campaign denial, 12 min survey floor) | Hagholt Crude HH-4 header H-8 (invented, simulated CUT-SIM-6): 2.50·(12.00−4.00) reconstructs 20.00 volpct while Cutveil still reads 4.80 volpct | ACCEPT (+0.41) / REJECT (+0.36) | serialized `2.50*(12.00-4.00)=20.00`; `0.200*80.00=16.00`; bounded ACCEPT of H-8 only; H-6/H-7 out of scope; companion t2 REJECTS skip-isolate; sim_or_real=simulated |

Decision spread: REJECT / MODIFY / MODIFY / ACCEPT / ACCEPT / REJECT — **2A/2M/2R**. All three enums used, and all three sit on **leads**. Provenance spread: designed / hil / simulated (one each; never live-plant). IDs `nelb-r60-181`…`183` plus t1/t2 suffixes.

## Raster sidecar
Every record carries `raster` + top-level `gate_snn` + `gate_compute`. Windows {wins[0]:.0f}/{wins[1]:.0f}/{wins[2]:.0f} ms; `window_s == window_ms/1000` exactly; `spikes == round(neurons·rate·window_s)` with zero slack ({n_sp[0]}/{n_sp[1]}/{n_sp[2]} at {rates[0]}/{rates[1]}/{rates[2]} Hz over {n_neu[0]}/{n_neu[1]}/{n_neu[2]} neurons); `energy_pJ = spikes·23` and `energy_uJ = spikes·23e-6` exact ({n_sp[0]*23}/{n_sp[1]*23}/{n_sp[2]*23} pJ). Routing source/target + 3-entry tables + `third_factor` on all three (modulators {tfs[0]} / {tfs[1]} / {tfs[2]}; τe {taus[0]}/{taus[1]}/{taus[2]} s as consistent `tau_e_s`+`tau_e_ms` pairs). Excerpts integer `t_us`, in-window, `neuron_id`-bounded, sorted, full-window by construction, per-spike amplitude with adaptation (0.82**k) plus noise. ISI histograms from the full window, bins ≥1 ms, counts sum to `spikes − distinct_active_neurons` ({isis[0]}/{isis[1]}/{isis[2]}). Same-neuron gaps ≥1100 µs pre-round, ≥1000 µs serialized. `gate_snn` on all three: decisions REJECT/MODIFY/ACCEPT matching each lead trajectory; every rate-declaring population's budget exact against its decision window. `gate_compute.per_check` windows 32–40 ms, budgets exact ({gc[0]} / {gc[1]} / {gc[2]}). Main streams: {events[0]}/{events[1]}/{events[2]} events (inside the 5–40 cap), strictly increasing `t_rel_ms` only (no `t_ms` mix), same-channel refractory ≥0.8 ms (181 triangulation pair at 1.4 ms, 182 FID pair at 1.2 ms, 183 dielectric pair at 1.5 ms).

## Self-critique

### Edge cases added vs still thin
- **Added:** first laser-triangulation remaining-strip family on a tandem mill with a recomputable t=k_t·(V0−V) (`250.0 um`) plus mass-flow identity (`20.00 kg/s`) and three-party collusion including the Spotveil infra owner; first flame-ionization remaining-VOC family on an RTO inlet with recomputable C=k_i·(I−I_dark) (`40.00 ppm`) and jet-scale identity (`1.000`), plus a resolved-innocent FID tech (missing hydrogen-fuel AE, UTC vs UTC+2, not last-to-badge); first dielectric remaining-water-cut family on a crude header with recomputable WC=k_e·(C−C0) (`20.00 volpct`) plus water-volume identity (`16.00 m3/h`); bounded ACCEPT whose out-of-scope clause is adjacent crude headers rather than a hopper/taphole/dump cap; operational t2 on all three (pass-hold, new-jet restart, skip-isolate refusal); provenance trio designed/hil/simulated; 18 min / 24 min / 12 min slow floors in-stream.
- **Still thin:** (i) 181's k_t is a lumped V→um gain, not a standoff / strip-emissivity table — a pass-line hop that fakes 250.0 um inside a 380.0 um Spotveil corridor is unwritten; (ii) 182's k_i is a lumped nA→ppm gain, not a hydrogen-flow / jet-temperature map, so a fuel hop that fakes 40.00 ppm is unwritten; (iii) 183's k_e is a lumped pF→volpct factor, not a salinity / temperature permittivity table, so a brine hop that fakes 20.00 volpct inside a 4.80 last-good is unwritten; (iv) vendor-only as a *lead* REJECT on a plant with *no* independent triangulation/FID/dielectric head installed yet remains slightly harder — 181/182 still have plant heads; (v) stream amplitudes remain authored constants (raster draws are the only seeded noise).

### Realism of noise / temporal fidelity
- Strong: 181's 250.0 um, mdot 20.00, and 18.0 min hold (`6000+1080=7080 s`) recompute from the record; 182's 40.00 ppm, S 1.000, and 24.0 min cooldown (`2820+1440=4260 s`) recompute; 183's 20.00 volpct, q_w 16.00, and 12.0 min survey (`6000+720=6720 s`) recompute. Raster adaptation (0.82**k plus 4% noise) and the 1.2–1.5 ms physics pairs give the 5–40 stream a raster-scale motif without violating 0.8 ms same-channel refractory.
- **Gaps, honestly:** (i) 5–40 cap still forces heavy thinning (kHz triangulation kept as 4 V points; 10 Hz FID electrometer kept as 4 I points; 1 Hz capacitance kept as 4 C points); (ii) 181's post-stop 200.0 um is a later sample, not a closed-loop mill-speed controller; (iii) 182 HIL coupon times an in-service inlet isolate that the stream does not independently witness on a second live inlet until the new jet starts; (iv) no gate_snn input→output volley pair at raster resolution this round (r04-a1 already staged that).

### Training value (SNN/LSM + agentic)
Distillation targets: triangulation t=k_t·(V0−V) and mdot identities; isolate-floor refuse vs continue-rolling vs mill ESD; Spotveil-infra collusion; FID C=k_i·(I−I_dark) head plus jet-scale identity; isolate-floor inlet vs keep-whole vs RTO trip; hydrogen-fuel AE / timezone exoneration; dielectric WC=k_e·(C−C0) and q_w identities; bounded ACCEPT with header-out-of-scope; skip-isolate refusal under survey takt. Agentic value concentrates in three patterns: reconstruction-as-SoT on a physical strip/VOC/water-cut the raw corridor cannot see, earned ACCEPT with an explicit physical out-of-scope object (H-6/H-7), and stop-then-hold so a REJECT does not become a mill/RTO/header kill.

## What a later leftover-mill round should add (next densification target)
1. **Standoff / strip-emissivity table** on a non-YS-6 tandem stand so a pass-line hop fakes 250.0 um inside a 380.0 um Spotveil corridor, closing 181's lumped-gain gap.
2. **Hydrogen-flow / jet-temperature map** on a non-BW-4 FID so a fuel hop fakes 40.00 ppm while mean I looks like spec.
3. **Salinity / temperature permittivity table** on a non-HH-4 dielectric probe so a brine hop fakes 20.00 volpct inside a 4.80 last-campaign corridor.
4. **Vendor-only as a lead REJECT** on a plant that has no independent triangulation/FID/dielectric head installed yet (181/182 still had plant heads).
5. **Do not restage** VOD-SNN replay, pharma cold-chain, CEMS, FBG glaze, Frostlip quench, Oxbow VRFB, IFOG, transmon, hyperspectral, MEMS array, muon ore-pass, industrial x-ray, optogenetic stim, 905 nm LiDAR snow, clamp-on transit-time, LIBS, QEPAS, LFV, Kaplan LDV, THz-TDS, ECT capacitance, TDLAS NH3, lock-in thermography, PAUT TFM, EN CUI, RUS porcelain, N-16 loop flow, helium RGA, Faraday FOCT, blade tip-timing, acoustic pyrometry, SPR, vibrating-wire, microwave-cavity, MFL, NMR T2, nucleonic SG, JNT, CRNS, Coriolis, CARS, XRF, Mössbauer, GB-InSAR, ellipsometry, SPND, LII, PALS, NQR, SFRA, digital shearography, hydrogen permeation, FMCW lining, GPR, Pockels, pulsed eddy current, confocal chromatic, OCT, DCPD, impact-echo, mud-pulse, Barkhausen, Lamb-wave, phosphor-lifetime, vortex-shedding, GWR, He-3 backscatter, Kr-85 beta, Raman OH-CH, Raman DTS compensation, cyclotron BPM, alanine EPR, ADCP ice-jam, TOFD, laser-flash Parker, TDR, Seebeck, coda-wave, LPR, paramagnetic O2, TEOM, Faraday magmeter, PDA d32, acoustoelastic, C-SAM, FDS tanδ, MCSA, EMAT SH, FBRM, ACFM, OFDR, XRD sin2psi, ER probe, Fabry-Perot choke, inductive debris, wire-mesh, UCI, MAE, Nernst-linearized zirconia, two-color pyrometer, magnetostrictive level, IRIS pulse-echo, dual-wavelength ratio pyrometer, UV-fluorescence OIW, zirconia Nernst crown, PID VOC, contact pulse-echo, wideband pump-current zirconia, Rogowski, BAM, UV-DOAS SO2, Al2O3 moisture, load-cell hopper, Yewspit YS-6 triangulation, Brimwhin FID-HIL-4, or Hagholt HH-4 dielectric. Greyfen KCTC-7, Pellucid IRRAD-P4, and Whitefork WF-9 remain unused plant names and must not be reused. Do not steal r54–r59 IDs `163`–`180`.

## Verification
`batch-r60.jsonl`: 3 lines, `json.loads`-clean (allow_nan=False), {sizes[0]}/{sizes[1]}/{sizes[2]} bytes (file {file_size}, sha256 `{file_sha}`). Staged at `/tmp/nelb-r60/` only. Repo gates: `check_records.check_jsonl` with `FactoryStaging(enabled=True)` → 0 errors, 0 warnings, kinds `{{bridge_pair: 3}}`; `python3 pipelines/check_records.py --strict /tmp/nelb-r60` → 0/0; `curate_bridge.raster_status(..., require_raster=True, require_routing_table=True)` → raster_valid and gate_snn_valid true, empty reason codes; `curate_record(...)` → 3× retain / `BRIDGE_EVENTS_ALREADY_GLOBALLY_ORDERED`; `verify_batch_for_frontier(strict=True)` → 3 verified, 0 inconclusive, 0 failed; `python3 pipelines/spike_probe.py --strict /tmp/nelb-r60/batch-r60.jsonl` → loaded 3, unloadable 0, problems [], third_factor_routes 3, gate_snn_records 3, spikes {spikes}, energy_pJ {energy}. Build-time asserts: global time order; same-channel ≥0.8 ms; 5–40 events ({events[0]}/{events[1]}/{events[2]}); excerpt integer bounds, neuron bounds, sort, 1 ms per-neuron floor; ISI identity {isis[0]}/{isis[1]}/{isis[2]}; spike budgets exact; energy pJ/µJ exact; reward totals equal two-decimal component sums ({reward_s}); gate_snn decisions match lead `safety_decision.decision`; `state.sim_or_real` ∈ {{designed, hil, simulated}}; `meta.round=60`, `meta.factory=neuromorphic-event-language-bridge`, `meta.generator=grok-4.6`, `meta.run_label=2026-09-02-final-heavy`; `meta.rights` 15-key RM-793 stamp (`intended_use=research_only`, `linear_issue=RM-793`, `generated_at={GENERATED_AT}`); no hidden-reasoning keys; no `provenance` objects; no live-plant claims; no `training_ready`; all 9 record/trajectory ids unique. Raster seeds 202660181/202660182/202660183, MT19937.

Honest novelty accounting: 3/3 modality families are new versus the whole committed factory and versus staged leftover-mill r13–r54 (and in-flight r55–r59 envelopes). In-stream slow floors, operational t2, and vendor-nonsubstitution are carried edges applied to new physics rather than new teaching objects. Three-party collusion and exoneration were already taught on r13 quench/VRFB and r53 Fabry-Perot, so those heads are carried onto new sensors. Against that: bounded-accept-with-scope-limit, reconstruction-as-SoT, conjunctive SOP, and custody vocabulary are carried; the 5–40 cap is a density constraint not a new teaching object; 47 prior leftover-mill rounds already taught custody/governance at high sophistication. Net: about two-fifths of the round's scenario/edge mass is genuinely novel.

Novel coverage: 40%
"""
    NOTES.write_text(notes, encoding="utf-8")
    print("wrote", NOTES, "bytes", NOTES.stat().st_size)


def main():
    records = [rec_181(), rec_182(), rec_183()]
    local_checks(records)
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    lines = [
        json.dumps(r, ensure_ascii=False, allow_nan=False, separators=(",", ":"))
        for r in records
    ]
    BATCH.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("wrote", BATCH, "bytes", BATCH.stat().st_size, "lines", len(lines))
    for i, r in enumerate(records):
        print(
            r["id"],
            "events",
            len(r["spike_events"]),
            "excerpt",
            len(r["raster"]["excerpt"]),
            "spikes",
            r["raster"]["spikes"],
            "isi",
            r["raster"]["isi_count_identity"],
            "sim",
            r["language_view"]["trajectory"]["state"]["sim_or_real"],
            "dec",
            r["language_view"]["trajectory"]["safety_decision"]["decision"],
            "bytes",
            len(lines[i]),
        )
    gate = repo_validate(records)
    write_notes(records, lines, gate)


if __name__ == "__main__":
    main()
