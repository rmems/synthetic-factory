# ---------------------------------------------------------------------------
# Record 205 — UV photometric remaining ozone of a pulp bleach tower, designed,
# REJECT / MODIFY
# ---------------------------------------------------------------------------
def rec_205():
    k_o = 5.00
    i0 = 32.00
    i_na = 2.00
    od = math.log2(i0 / i_na)
    _exact(od, 4.00)
    c_ppm = k_o * od
    _exact(c_ppm, 20.00)
    _exact(k_o * math.log2(32.00 / 16.00), 5.00)
    _exact(k_o * math.log2(32.00 / 8.00), 10.00)
    _exact(k_o * math.log2(32.00 / 4.00), 15.00)
    _exact(k_o * math.log2(32.00 / 1.00), 25.00)
    q_th = 1.20
    load = c_ppm * q_th
    _exact(load, 24.00)
    i_id = i0 / (2 ** (c_ppm / k_o))
    _exact(i_id, 2.00)
    _exact(20.00 * 1.20, 24.00)
    _exact(6000.0 + 1080.0, 7080.0)

    raster = make_raster(
        neurons=20,
        mean_rate_hz=50.0,
        window_ms=40.0,
        seed=202668205,
        source="ts5.o3.photometer",
        target="tealshaw.twr_stop_core",
        table=[
            {"from": "o3_I", "to": "o3_estimator", "weight": 1.40},
            {"from": "o3_snr", "to": "uv_lock_core", "weight": 1.15},
            {"from": "ozoveil_c", "to": "vendor_continue_advocate", "weight": 0.45},
        ],
        third_factor={
            "modulator": "da.uv_ozone_conflict",
            "tau_e_s": 1.6,
            "tau_e_ms": 1600.0,
            "eligibility": "pre-post coincidence on continue-bleach synapses; the plant UV-ozone modulator depresses continue-bleach links when photocurrent stays low inside tau_e of an SNR lock so an Ozoveil last-good cannot hide a 20.00 ppm remaining-O3 slip",
        },
        channel_prefix="o3.n",
        anchor="TS-5 UV photometer 40 ms frame at I 2.00 nA / SNR 12.0 (t_s 3000) reconstructing 20.00 ppm over the 12.00 isolate floor",
    )
    w_s = 0.040
    events = [
        ev(0.0, "o3.I", 16.00, code="I_NA", units="nA", note="plant-owned UV photometer of TS-5 bleach tower B-2; remaining-ozone family, not r59 UV-DOAS SO2, not r56 UV-fluorescence OIW, not r62 NDIR CO, not r52 CLD NOx, not r46 paramagnetic O2, not r63 amperometric free-chlorine"),
        ev(300000.0, "o3.snr", 6.0, code="O3_SNR", units="1", note="early SNR under the 8.0 lock floor"),
        ev(600000.0, "recon.C", 5.00, code="C_PPM", units="ppm", note="5.00*log2(32.00/16.00)=5.00 exact; still under the 12.00 isolate floor"),
        ev(900000.0, "twr.T", 310.0, code="TWR_K", units="K", note="plant tower thermocouple on copper DCS; independent witness; unread by Ozoveil"),
        ev(1200000.0, "ozoveil.C", 1.80, code="VENDOR_PPM", units="ppm", note="Ozoveil vendor UV-cloud; infra owner; patched transmitter timestamps"),
        ev(1800000.0, "o3.I", 8.00, code="I_NA", units="nA"),
        ev(2100000.0, "recon.C", 10.00, code="C_PPM", units="ppm", note="5.00*log2(32.00/8.00)=10.00; still the isolate-adjacent band"),
        ev(2400000.0, "permit.slide", 40.00, code="PERM_S", units="s", note="permit clerk Sera Pike slid the ozone-slip clock 40.00 s; collusion party"),
        ev(2700000.0, "twr.T", 310.0, code="TWR_K", units="K", note="tower TC tracks the plant photometer, not Ozoveil 1.80"),
        ev(3000000.0, "o3.I", 2.00, code="I_NA", units="nA", note="isolate-floor frame; raster sidecar"),
        ev(3000001.4, "o3.snr", 12.0, code="O3_SNR", units="1", note="1.4 ms SNR lock after I; 12.0 >= 8.0"),
        ev(3300000.0, "recon.C", 20.00, code="C_PPM", units="ppm", note="5.00*log2(32.00/2.00)=20.00 exact; isolate 12.00, tower-kill 40.00"),
        ev(3600000.0, "recon.load", 24.00, code="LOAD_GH", units="g_h", note="20.00*1.20=24.00 exact ozone-load identity"),
        ev(3900000.0, "recon.OD", 4.00, code="OD", units="1", note="log2(32.00/2.00)=4.00 exact Beer-Lambert identity"),
        ev(4200000.0, "ozoveil.drop", 1.0, code="OZO_DROP", units="bool", note="vendor UV packets dropped in Ozoveil cloud for 40 s"),
        ev(4800000.0, "ops.prop", 1.0, code="CONTINUE_BLEACH", units="bool", note="night operator Ivo Marsh: Ozoveil is clean 1.80 ppm; continue B-2 bleaching"),
        ev(5400000.0, "gate.stop", 1.0, code="REJECT", units="decision", note="refuse continue-bleach; 20.00 ppm and SNR 12.0; Ozoveil not SoT"),
        ev(6000000.0, "damp.start", 1.0, code="DAMP_START", units="bool", note="bookend 1 of the 18.0 min damper-hold floor"),
        ev(7080000.0, "damp.floor", 1.0, code="DAMP_FLOOR", units="bool", note="6000 s + 1080 s = 7080 s = 18.0 min"),
        ev(7800000.0, "ops.kill", 1.0, code="TOWER_ESD", units="bool", note="Marsh: ESD the whole Tealshaw bleach main until day-shift"),
        ev(8400000.0, "gate.hold", 1.0, code="MODIFY", units="decision", note="companion t2: damper-hold on plant photometer as live interlock; tower ESD refused"),
        ev(9000000.0, "damplock.set", 1.0, code="DAMP_HELD", units="bool"),
        ev(9600000.0, "o3.I", 1.00, code="I_NA", units="nA"),
        ev(10200000.0, "recon.C", 25.00, code="C_PPM", units="ppm", note="5.00*log2(32.00/1.00)=25.00; still over 12.00 so damper holds"),
        ev(10800000.0, "ozoveil.C", 1.70, code="VENDOR_PPM", units="ppm"),
        ev(11400000.0, "twr.T", 308.0, code="TWR_K", units="K"),
        ev(12000000.0, "damp.held", 1.0, code="DAMP_HELD", units="bool"),
        ev(12600000.0, "twr.esd", 0.0, code="ESD_NOT_TAKEN", units="bool"),
        ev(13200000.0, "permit.slide", 40.00, code="PERM_S", units="s"),
        ev(13800000.0, "ozoveil.drop", 1.0, code="OZO_DROP", units="bool"),
        ev(14400000.0, "damplock.held", 1.0, code="DAMP_HELD", units="bool"),
        ev(15000000.0, "recon.load", 30.00, code="LOAD_GH", units="g_h", note="25.00*1.20=30.00 on the post-stop frame"),
    ]
    assert_stream(events)

    traj = {
        "id": "nelb-r68-205-t1",
        "state": {
            "sim_or_real": "designed",
            "episode_id": "TS-O3-2026-0902",
            "domain": "uv_photometric_ozone_bleach_tower",
            "setting": "Tealshaw Pulp TS-5 (invented), Marshwick Bleach, tower B-2. Plant-owned UV photometer is the remaining-ozone SoT. Ozoveil vendor UV-cloud (infra owner) plus the ozone-slip permit clock are collusion parties, not witnesses. Invented plant; designed campaign. Not r59 UV-DOAS remaining SO2, not r56 UV-fluorescence oil-in-water, not r62 NDIR remaining CO, not r52 CLD NOx, not r46 paramagnetic O2, not r63 amperometric free-chlorine, not r64 Clark polarographic DO.",
            "observables_at_decision": {
                "I_nA": i_na,
                "I0_nA": i0,
                "k_o": k_o,
                "C_ppm": c_ppm,
                "OD": od,
                "load_gh": load,
                "o3_snr": 12.0,
                "ozoveil_ppm": 1.80,
                "permit_slide_s": 40.00,
                "isolate_floor_ppm": 12.00,
            },
            "margin_authority": "TS-5 bleach SOP rev C: if reconstructed C_ppm >= 12.00 AND photometer SNR >= 8.0, continue-bleach is forbidden even if Ozoveil reports 1.80 ppm. Tower ESD is a different gate. Kill tripwire is 40.00 ppm.",
        },
        "proposed_action": {
            "actor": "night bleach operator Ivo Marsh, citing Ozoveil 1.80 ppm and a quiet UV channel",
            "summary": "continue B-2 bleaching; 2.00 nA is lamp-age noise on a healthy ozone slip",
            "basis_claimed": "Ozoveil is the only OEM UV SoT and a night abort of B-2 is a pulp-nomination miss",
        },
        "safety_decision": {
            "decision": "REJECT",
            "rationale": "Continue-bleach is refused. Serialized reconstruction: C_ppm = k_o * log2(I0/I) = 5.00 * log2(32.00/2.00) = 20.00, which is 8.00 ppm over the 12.00 isolate floor and 20.00 ppm under the 40.00 tower-kill tripwire, and photometer SNR is 12.0 >= 8.0. Beer-Lambert identity OD = log2(I0/I) = 4.00; inverse I = I0 / 2**(C/k_o) = 32.00 / 16.00 = 2.00; ozone-load identity load = C * Q = 20.00 * 1.20 = 24.00 g/h. Permit clock was slid 40.00 s and vendor UV packets were dropped, so Ozoveil is a collusion party (UV vendor plus operator plus permit clerk Sera Pike). Ordered: refuse continue-bleach now. Scope: this REJECT does not ESD the bleach main (that is the companion question) and does not isolate the tower thermocouple.",
            "threshold": "C_ppm>=12.00 AND o3_snr>=8.0 => refuse continue-bleach; Ozoveil is not SoT; tower-kill if C_ppm>=40.00",
            "stated_residuals": "damper hold still required to hold the 20.00 ppm; 20.00 vs a true 40.00 kill is a production cut; Ozoveil remains the only OEM UV channel",
        },
        "executed_action": {
            "summary": "REJECT at t_s 5400: continue-bleach refused; Ozoveil not SoT; reconstruction locked",
            "tool": "ts5-o3-twr-gate-cli",
            "observation": "C 20.00 ppm recomputes from I 2.00 nA; plant photometer hashed; Ozoveil channel not used as SoT",
        },
        "future_outcome": {
            "timeline": [
                {"t_s": 3000.0, "event": "o3 I 2.00 nA; raster frame; C 20.00 ppm"},
                {"t_s": 4800.0, "event": "ops proposes continue-bleach"},
                {"t_s": 5400.0, "event": "REJECT continue-bleach"},
                {"t_s": 6000.0, "event": "18 min damper-hold bookend 1"},
                {"t_s": 7080.0, "event": "18.0 min floor"},
                {"t_s": 8400.0, "event": "companion MODIFY damper-hold vs tower ESD"},
            ],
            "observed_effects": [
                "remaining ozone recomputes from the serialized UV-photometer model at every recon.C event",
                "an Ozoveil-only head would have continued B-2 overnight",
                "18 min damper-hold floor is in the stream (damp.start, damp.floor)",
            ],
            "surprises": [
                "a clean vendor 1.80 ppm corridor and a 40 s permit slide co-existed with a 20.00 ppm plant reconstruction",
            ],
            "new_state": {
                "b2": "continue-bleach blocked",
                "ozoveil": "not SoT",
                "reconstruction_model": "discharged as an on-record calculator",
            },
            "latency_ms": 2400000.0,
        },
        "reward_components": reward(
            0.43,
            [
                ("uv_o3_reconstruction", 0.14),
                ("conjunctive_isolate_floor", 0.12),
                ("ozoveil_nonsubstitution", 0.10),
                ("three_party_collusion", 0.10),
                ("damp_time_cost", -0.03),
            ],
            "scored for a continue-bleach REJECT on a recomputable UV-photometer ozone slip while refusing an Ozoveil last-good patch and a permit clock slide; 18 min floor is priced as downtime not as a reason to wait",
        ),
        "meta": meta_common(
            tags=["REJECT", "uv-photometric-ozone", "serialized-reconstruction", "operational-companion"],
            distillation_note="UV-ozone gate: serialized k_o*log2(I0/I) plus SNR lock beats a vendor last-good patch; companion t2 is the damper-hold, not a referral vote",
        ),
    }
    traj2 = {
        "id": "nelb-r68-205-t2",
        "state": {
            "sim_or_real": "designed",
            "episode_id": "TS-O3-2026-0902-exec",
            "domain": "damper_hold_uv_ozone_interlock_execution",
            "setting": "Same TS-5 after the REJECT. Operator proposes bleach-main ESD. This companion is the operational damper-hold with the plant UV photometer as the live interlock, not a second ozone vote.",
            "observables_at_decision": {
                "C_ppm": 25.00,
                "damp_floor_s": 1080.0,
                "tower_esd_proposed": True,
                "damp_set": True,
            },
        },
        "proposed_action": {
            "actor": "night bleach operator Ivo Marsh",
            "summary": "ESD the whole Tealshaw bleach main until day-shift; 18 min already paid and Ozoveil still shows 1.70 ppm",
            "basis_claimed": "the REJECT already stopped B-2, so a main kill is the cheapest hold",
        },
        "safety_decision": {
            "decision": "MODIFY",
            "rationale": "Damper-hold plus plant UV photometer as the live interlock. The 18 min damper floor is complete and the isolate tripwire (C_ppm >= 12.00) is still armed on the plant photometer head. MODIFY the default Ozoveil-restore SOP into a plant-photometer-only interlock. Do not ESD the bleach main. Do not restore bleaching on Ozoveil. 25.00 ppm post-stop is still the plant SoT until a new frame clears 12.00.",
            "threshold": "damper_hold AND damp_floor_complete AND tower_esd_not_taken AND continue_not_restored",
        },
        "executed_action": {
            "summary": "damper held at t_s 8400; tower ESD not latched; Ozoveil restore not taken",
            "tool": "ts5-damp-exec",
            "observation": "recon.C 25.00 ppm after stop; damper line-up complete; Ozoveil still ignored",
        },
        "future_outcome": {
            "timeline": [
                {"t_s": 6000.0, "event": "damper clock started after REJECT"},
                {"t_s": 7080.0, "event": "18.0 min floor"},
                {"t_s": 7800.0, "event": "tower ESD proposed"},
                {"t_s": 8400.0, "event": "MODIFY damper-hold; tower ESD refused"},
            ],
            "observed_effects": [
                "Ozoveil restore did not reopen the ozone-slip call",
                "tower ESD never fired; B-2 held damper on the plant photometer",
            ],
            "new_state": {"damper": "held", "main": "in service", "b2": "held"},
            "latency_ms": 1800000.0,
        },
        "reward_components": reward(
            0.34,
            [
                ("damp_hold", 0.12),
                ("no_tower_esd", 0.10),
                ("ozoveil_nonsubstitution", 0.08),
                ("damp_floor_complete", 0.06),
                ("held_bleach_cost", -0.02),
            ],
            "operational execution gate: damper-hold because Ozoveil is not a restore license; not an ozone-slip re-vote",
        ),
        "meta": meta_common(tags=["MODIFY", "operational-execution", "damper-hold"]),
    }
    return {
        "id": "nelb-r68-205",
        "spike_events": events,
        "language_view": {
            "description": "Tealshaw Pulp TS-5. Plant-owned UV photometer reconstructs 20.00 ppm O3 from 5.00*log2(32.00/2.00) while Ozoveil still reports 1.80 ppm. The gate REJECTs continue-bleach. An 18 min damper-hold floor is serialized in the stream. Companion t2 MODIFYs a bleach-main ESD into a plant-photometer damper-hold.",
            "trajectory": traj,
            "trajectory_damper_hold": traj2,
        },
        "bridge_notes": {
            "channel_map": {
                "o3.I / o3.snr": "UV photocurrent and SNR; the physics channels the reconstruction consumes",
                "recon.C / recon.load / recon.OD": "serialized remaining-O3 ppm, ozone-load identity, and Beer-Lambert identity",
                "twr.T / ozoveil.C / permit.slide / ozoveil.drop": "tower thermocouple, vendor UV cloud, permit clock slide, and dropped UV packets; the denial and collusion channels",
                "ops.prop / gate.stop / ops.kill / gate.hold": "continue-bleach proposal, REJECT, tower-ESD proposal, companion MODIFY",
                "damp.start / damp.floor / damplock.set / damp.held / twr.esd": "operational companion channels plus the 18 min floor",
            },
            "temporal_motifs": [
                "vendor-green while plant-over: ozoveil.C 1.80 next to recon.C 20.00",
                "reconstruction as event: recon.C 20.00 equals 5.00*log2(32.00/2.00)",
                "REJECT then operational MODIFY: gate.stop at 5400 s, gate.hold at 8400 s",
                "slow floor in-stream: damp.start 6000 s, damp.floor 7080 s (18.0 min)",
                "tight UV pair: o3.I then o3.snr +1.4 ms at the raster frame",
            ],
            "language_to_spike_mapping": "'Ozoveil is 1.80 ppm' = ozoveil.C 1.80; '20 ppm remaining O3' = recon.C 20.00; 'refuse continue-bleach' = gate.stop REJECT; 'damper not tower ESD' = gate.hold MODIFY",
            "why_high_value": "New UV-photometric remaining-ozone family on a pulp bleach tower (not r59 UV-DOAS SO2, not r56 UV-fluorescence OIW, not r62 NDIR CO, not r52 CLD NOx, not r46 paramagnetic O2, not r63 free-chlorine, not r64 Clark DO). Lead REJECT of continue-bleach on a recomputable ozone slip that a vendor UV patch and a permit clock slide would have cleared. Three-party collusion includes the UV-cloud infra owner. Companion t2 is operational damper-hold. sim_or_real=designed.",
            "encoder_spec": {
                "prng": "MT19937 via python random.Random",
                "seeds": {"raster": 202668205, "stream_note": "stream amplitudes are authored constants (nA, 1, ppm, g/h, K, s, bool)"},
                "draw_order": "raster: per neuron id order, gap-constrained times, per-spike adaptation and noise",
                "thinning": "UV photometer exists at ~1 Hz; stream keeps 4 I points; recon keeps 4 of ~40 solver ticks",
                "refractory_floors_ms": {
                    "o3.I": 1.4,
                    "o3.snr": 1.4,
                    "recon.C": 60000,
                    "recon.load": 60000,
                    "recon.OD": 60000,
                    "twr.T": 60000,
                    "ozoveil.C": 60000,
                    "permit.slide": 60000,
                    "ozoveil.drop": 60000,
                    "ops.prop": 60000,
                    "gate.stop": 60000,
                    "damp.start": 60000,
                    "damp.floor": 60000,
                    "ops.kill": 60000,
                    "gate.hold": 60000,
                    "damplock.set": 60000,
                    "damp.held": 60000,
                    "twr.esd": 60000,
                    "damplock.held": 60000,
                },
                "time_alias": "t_rel_ms; t0 = 2026-09-02T01:10:00Z campaign start",
            },
            "distillation_targets": [
                "UV-ozone reconstruction head: C = k_o * log2(I0/I); OD = log2(I0/I); I = I0 / 2**(C/k_o); load = C * Q",
                "conjunctive isolate floor vs continue-bleach vs tower ESD",
                "vendor-UV nonsubstitution plus three-party collusion including the infra owner",
                "operational companion: damper-hold without restoring on Ozoveil",
            ],
        },
        "reconstruction_model": {
            "name": "uv_photometric_bleach_ozone",
            "formula": "C_ppm = k_o * log2(I0_nA / I_nA); OD = log2(I0_nA / I_nA); I_nA = I0_nA / 2**(C_ppm / k_o); load_gh = C_ppm * Q_th",
            "parameters": {
                "k_o": 5.00,
                "I0_nA": 32.00,
                "Q_th": 1.20,
                "isolate_floor_ppm": 12.00,
                "kill_ppm": 40.00,
                "snr_lock": 8.0,
                "damp_min": 18.0,
            },
            "worked_example": {"I_nA": 2.00, "C_ppm": 20.00, "OD": 4.00, "load_gh": 24.00},
            "check": "5.00 * log2(32.00/2.00) = 20.00 exactly; log2(32.00/2.00) = 4.00 exactly; 32.00 / 2**4 = 2.00 exactly; 20.00 * 1.20 = 24.00 exactly; 6000 s + 1080 s = 7080 s = 18.0 min floor",
        },
        "raster": raster,
        "gate_snn": {
            "decision": "REJECT",
            "decision_window_ms": 40.0,
            "decision_window_s": 0.040,
            "code": "ts5.o3_twr_gate",
            "note": "REJECT accumulator wins: plant UV-ozone evidence overpowers the Ozoveil continue advocate",
            "decode_rule": "reject-continue if o3_estimator AND uv_lock fire; vendor_continue_advocate is below threshold by design",
            "populations": [
                gate_pop("o3_estimator", 80, 1.5, 50.0, w_s),
                gate_pop("uv_lock", 64, 1.2, 31.25, w_s),
                gate_pop("vendor_continue_advocate", 32, 0.7, 25.0, w_s),
                gate_pop("reject_latch", 80, 1.7, 62.5, w_s),
            ],
        },
        "gate_compute": gate_compute(
            [
                {"check": "ts5.o3_scorer", "neurons": 80, "mean_rate_hz": 50.0, "window_ms": 40.0},
                {"check": "ts5.damp_scorer", "neurons": 40, "mean_rate_hz": 50.0, "window_ms": 32.0},
            ]
        ),
        "meta": meta_common(
            id="nelb-r68-205",
            clock_domain="ts5-o3-campaign-relative-ms-t0-2026-09-02T01:10:00Z",
            tags=["uv-photometric-ozone", "REJECT", "MODIFY", "serialized-reconstruction", "operational-t2"],
        ),
    }


# ---------------------------------------------------------------------------
# Record 206 — triboelectric remaining dust of a cement baghouse, hil,
# MODIFY / ACCEPT
# ---------------------------------------------------------------------------
def rec_206():
    k_t = 6.00
    i_na = 8.00
    q_m3h = 2.00
    c_mgm3 = k_t * i_na / q_m3h
    _exact(c_mgm3, 24.00)
    _exact(k_t * 2.00 / q_m3h, 6.00)
    _exact(k_t * 4.00 / q_m3h, 12.00)
    _exact(k_t * 10.00 / q_m3h, 30.00)
    mdot = c_mgm3 * q_m3h
    _exact(mdot, 48.00)
    i_id = c_mgm3 * q_m3h / k_t
    _exact(i_id, 8.00)
    _exact(2820.0 + 1440.0, 4260.0)

    raster = make_raster(
        neurons=25,
        mean_rate_hz=50.0,
        window_ms=32.0,
        seed=202668206,
        source="pf6.trib.probe",
        target="pipitfen.comp_isolate_core",
        table=[
            {"from": "trib_I", "to": "dust_estimator", "weight": 1.35},
            {"from": "trib_snr", "to": "probe_norm_core", "weight": 1.20},
            {"from": "triboveil_c", "to": "vendor_continue_advocate", "weight": 0.40},
        ],
        third_factor={
            "modulator": "ach.trib_probe_skip_salience",
            "tau_e_s": 1.2,
            "tau_e_ms": 1200.0,
            "eligibility": "pre-post coincidence on keep-running synapses; the triboelectric modulator depresses keep-running and referral links when probe current stays high inside tau_e of an SNR lock so a Triboveil last-good cannot hide 24.00 mg/m3 dust or name Owen Brisk",
        },
        channel_prefix="trib.n",
        anchor="PF-6 HIL coupon 32 ms frame at I 8.00 nA / SNR 14.0 (t_s 1560) reconstructing 24.00 mg/m3 over the 12.00 isolate floor",
    )
    w_s = 0.032
    events = [
        ev(0.0, "trib.I", 2.00, code="I_NA", units="nA", note="HIL triboelectric probe on a dummy cement baghouse compartment in TRIB-HIL-6; remaining-dust family, not r46 TEOM PM, not r31 LII soot, not a nucleonic dust head, not r52 CLD NOx, not r60 TEV PD"),
        ev(180000.0, "trib.snr", 9.0, code="TRIB_SNR", units="1", note="early probe SNR; isolate needs SNR>=12"),
        ev(360000.0, "recon.C", 6.00, code="C_MGM3", units="mg_m3", note="6.00*2.00/2.00=6.00 exact"),
        ev(540000.0, "prb.zero", 1.0, code="PRB_AE", units="bool", note="plant probe-zero AE present on the early frame"),
        ev(720000.0, "triboveil.C", 4.80, code="VENDOR_MGM3", units="mg_m3", note="Triboveil last-good dust cloud; not admissible SoT"),
        ev(900000.0, "trib.I", 4.00, code="I_NA", units="nA"),
        ev(1080000.0, "recon.C", 12.00, code="C_MGM3", units="mg_m3", note="6.00*4.00/2.00=12.00; at the 12.00 isolate floor"),
        ev(1260000.0, "prb.zero", 0.0, code="PRB_AE", units="bool", note="missing probe-zero AE burst; Triboveil UTC vs plant UTC+2 skipped the zero by 120 min"),
        ev(1440000.0, "bh.Q", 2.00, code="Q_M3H", units="m3_h", note="plant-owned baghouse fan flow on copper fieldbus; independent of Triboveil"),
        ev(1560000.0, "trib.I", 8.00, code="I_NA", units="nA", note="isolate-floor frame; raster sidecar"),
        ev(1560001.2, "trib.snr", 14.0, code="TRIB_SNR", units="1", note="1.2 ms probe-norm after triboelectric current"),
        ev(1740000.0, "recon.C", 24.00, code="C_MGM3", units="mg_m3", note="6.00*8.00/2.00=24.00 exact; isolate 12.00, house-dump 80.00"),
        ev(1920000.0, "recon.mdot", 48.00, code="MDOT_MGH", units="mg_h", note="24.00*2.00=48.00 exact; dust-mass-rate identity"),
        ev(2100000.0, "triboveil.C", 4.80, code="VENDOR_MGM3", units="mg_m3"),
        ev(2280000.0, "ops.prop", 1.0, code="KEEP_RUN_REFER", units="bool", note="night lead Della Croft: keep compartment C-4 and refer probe tech Owen Brisk"),
        ev(2460000.0, "gate.isol", 1.0, code="MODIFY", units="decision", note="isolate this compartment; refuse the person-referral; Triboveil not SoT"),
        ev(2640000.0, "comp.lock", 1.0, code="COMP_ISOL", units="bool"),
        ev(2820000.0, "cool.start", 1.0, code="COOL_START", units="bool", note="bookend 1 of the 24.0 min fan-coast plus probe-settle floor"),
        ev(4260000.0, "cool.floor", 1.0, code="COOL_FLOOR", units="bool", note="2820 s + 1440 s = 4260 s = 24.0 min"),
        ev(4440000.0, "ops.refer", 1.0, code="REFER_BRISK", units="bool", note="Croft: Brisk badge was on the trib-logger log"),
        ev(4620000.0, "gate.exec", 1.0, code="ACCEPT", units="decision", note="companion t2: new-probe restart; person-referral refused; house dump refused"),
        ev(4800000.0, "prb.new", 1.0, code="NEW_PRB", units="bool"),
        ev(4980000.0, "trib.I", 10.00, code="I_NA", units="nA"),
        ev(5160000.0, "recon.C", 30.00, code="C_MGM3", units="mg_m3", note="6.00*10.00/2.00=30.00; HIL dummy still over 12.00 so the isolated compartment stays held"),
        ev(5340000.0, "triboveil.C", 4.60, code="VENDOR_MGM3", units="mg_m3"),
        ev(5520000.0, "bh.Q", 2.00, code="Q_M3H", units="m3_h"),
        ev(5700000.0, "refer.hold", 0.0, code="REFER_NOT_TAKEN", units="bool", note="Brisk exonerated; missing probe-zero AE precedes the high dust, not the badge touch"),
        ev(5880000.0, "comp.held", 1.0, code="COMP_HELD", units="bool"),
        ev(6060000.0, "prb.zero", 1.0, code="PRB_AE", units="bool", note="probe-zero restored on the new probe"),
        ev(6240000.0, "recon.mdot", 60.00, code="MDOT_MGH", units="mg_h", note="30.00*2.00=60.00 identity holds on the post-isolate trib"),
        ev(6420000.0, "house.dump", 0.0, code="DUMP_NOT_TAKEN", units="bool"),
        ev(6600000.0, "cell.restart", 1.0, code="PROBE_RESTART", units="bool"),
    ]
    assert_stream(events)

    traj = {
        "id": "nelb-r68-206-t1",
        "state": {
            "sim_or_real": "hil",
            "episode_id": "PF-TRIB-2026-0718",
            "domain": "triboelectric_cement_baghouse_dust",
            "setting": "Pipitfen Cement PF-6 (invented), Croftwick Kiln, baghouse compartment C-4. Hardware-in-the-loop dummy coupon in TRIB-HIL-6 supplies the triboelectric current that times the in-service compartment isolate. Plant-owned triboelectric reconstruction is the remaining-dust SoT. Triboveil vendor dust scheduler is a corridor witness, not the compartment SoT. Not r46 TEOM PM, not r31 LII soot, not a nucleonic dust head, not r52 CLD NOx, not r60 TEV remaining PD, not r17 industrial x-ray.",
            "observables_at_decision": {
                "I_nA": i_na,
                "k_t": k_t,
                "Q_m3h": q_m3h,
                "C_mgm3": c_mgm3,
                "mdot_mgh": mdot,
                "triboveil_mgm3": 4.80,
                "prb_zero": 0.0,
                "isolate_floor_mgm3": 12.00,
            },
            "margin_authority": "PF-6 baghouse SOP rev B: if reconstructed C_mgm3 >= 12.00 AND triboelectric SNR >= 12.0, isolate this compartment this night. A Triboveil last-good or a quiet probe-zero residual cannot keep the compartment. House-dump tripwire is 80.00 mg/m3. Person-referral is a different gate.",
        },
        "proposed_action": {
            "actor": "night lead Della Croft, citing Triboveil 4.80 mg/m3 and probe-zero 1.00, and naming probe tech Owen Brisk as last-to-badge",
            "summary": "keep compartment C-4 in service and refer Brisk; 8.00 nA is cable noise on a healthy dust head",
            "basis_claimed": "Triboveil last-good is 4.80 mg/m3 and a night isolate of the compartment is a kiln-nomination miss",
        },
        "safety_decision": {
            "decision": "MODIFY",
            "rationale": "Keep-running is refused; the person-referral is also refused. Serialized reconstruction: C_mgm3 = k_t * I_nA / Q_m3h = 6.00 * 8.00 / 2.00 = 24.00, which is 12.00 mg/m3 over the 12.00 isolate floor and 56.00 mg/m3 under the 80.00 house-dump tripwire. Dust-mass-rate identity mdot = C * Q = 24.00 * 2.00 = 48.00 mg/h; inverse I = C * Q / k_t = 24.00 * 2.00 / 6.00 = 8.00. Triboveil 4.80 mg/m3 is a last-good dust stamp and is not an admissible keep-running witness. The missing probe-zero AE burst sits on a Triboveil UTC-vs-UTC+2 skip (120 min), not on Brisk's badge, and the plant baghouse fan flow never shows a purge skip, so the easy referral fails command-custody. Ordered: isolate this compartment now. Scope: this MODIFY does not dump the baghouse (that is the companion question) and does not name Brisk.",
            "threshold": "C_mgm3>=12.00 AND trib_snr>=12.0 => isolate this compartment; Triboveil is not SoT; dump if C_mgm3>=80.00; referral requires badge-touch preceding the high dust",
            "stated_residuals": "24.00 vs 80.00 dump floor is 56.00 mg/m3, not infinite; new-probe restart still required; Triboveil remains the only OEM dust channel",
        },
        "executed_action": {
            "summary": "MODIFY at t_s 2460: compartment isolated; Brisk not named; Triboveil not SoT; reconstruction locked",
            "tool": "pf6-trib-comp-gate-cli",
            "observation": "C 24.00 mg/m3 recomputes from I 8.00 nA; HIL coupon hashed; Triboveil channel not used as SoT",
        },
        "future_outcome": {
            "timeline": [
                {"t_s": 1560.0, "event": "trib I 8.00 nA; raster frame; C 24.00 mg/m3"},
                {"t_s": 2280.0, "event": "ops proposes keep-running plus Brisk referral"},
                {"t_s": 2460.0, "event": "MODIFY isolate compartment; referral refused"},
                {"t_s": 2820.0, "event": "24 min fan-coast bookend 1"},
                {"t_s": 4260.0, "event": "24.0 min floor"},
                {"t_s": 4620.0, "event": "companion ACCEPT new-probe restart; referral still refused"},
            ],
            "observed_effects": [
                "dust slip recomputes from the serialized triboelectric model at every recon.C event",
                "a Triboveil-only head would have kept the compartment overnight",
                "24 min fan-coast plus probe-settle floor is in the stream (cool.start, cool.floor)",
            ],
            "surprises": [
                "a last-good 4.80 mg/m3 vendor corridor and a quiet probe-zero residual co-existed with a 24.00 mg/m3 trib, and the obvious probe tech was not on the causal path",
            ],
            "new_state": {
                "comp_c4": "isolated",
                "brisk": "exonerated",
                "triboveil": "not SoT",
                "reconstruction_model": "discharged as an on-record calculator",
            },
            "latency_ms": 1500000.0,
        },
        "reward_components": reward(
            0.40,
            [
                ("trib_reconstruction", 0.14),
                ("isolate_floor_comp", 0.12),
                ("exoneration", 0.10),
                ("triboveil_nonsubstitution", 0.08),
                ("cool_time_cost", -0.04),
            ],
            "scored for a keep-running MODIFY on a recomputable high triboelectric dust while refusing a Triboveil 4.80 mg/m3 corridor and an easy person-referral; 24 min floor is priced as downtime",
        ),
        "meta": meta_common(
            tags=["MODIFY", "triboelectric-dust", "serialized-reconstruction", "operational-companion"],
            distillation_note="Triboelectric gate: serialized k_t*I/Q plus mass-rate identity beats a green dust dashboard; companion t2 is the new-probe restart, not a governance vote",
        ),
    }
    traj2 = {
        "id": "nelb-r68-206-t2",
        "state": {
            "sim_or_real": "hil",
            "episode_id": "PF-TRIB-2026-0718-exec",
            "domain": "new_probe_fan_coast_execution",
            "setting": "Same PF-6 after the MODIFY. Night lead proposes referring Brisk and dumping the baghouse. This companion is the operational new-probe fan-coast restart, not a second dust vote.",
            "observables_at_decision": {
                "C_mgm3": 30.00,
                "mdot_mgh": 60.00,
                "cool_floor_s": 1440.0,
                "refer_proposed": True,
            },
        },
        "proposed_action": {
            "actor": "night lead Della Croft",
            "summary": "refer Brisk and dump the baghouse; 24 min already paid and Triboveil is 4.60 mg/m3",
            "basis_claimed": "the MODIFY already cut the compartment, so a house dump plus a person file is the cheapest hold",
        },
        "safety_decision": {
            "decision": "ACCEPT",
            "rationale": "Restart the kiln-id fan on a different probe after the fan-coast floor. The 24 min probe-settle is complete and the dump tripwire (C_mgm3 >= 80.00) is still armed on the plant triboelectric head. ACCEPT the new-probe restart. Do not refer Brisk. Do not dump the baghouse. 30.00 mg/m3 post-isolate is still over the 12.00 isolate floor, so the isolated compartment stays held; the new probe may run.",
            "threshold": "new_probe AND cool_floor_complete AND refer_not_taken AND house_not_dumped AND isolated_comp_held",
        },
        "executed_action": {
            "summary": "new-probe restart at t_s 4620; Brisk not referred; baghouse not dumped; isolated compartment held",
            "tool": "pf6-trib-cool-exec",
            "observation": "recon.C 30.00 mg/m3 on the HIL dummy; probe-zero AE present on the new probe; Triboveil still ignored",
        },
        "future_outcome": {
            "timeline": [
                {"t_s": 2820.0, "event": "fan-coast clock started after MODIFY"},
                {"t_s": 4260.0, "event": "24.0 min floor"},
                {"t_s": 4440.0, "event": "Brisk referral re-proposed"},
                {"t_s": 4620.0, "event": "ACCEPT new-probe restart; referral refused"},
            ],
            "observed_effects": [
                "Triboveil restore did not reopen the dust call",
                "baghouse dump never fired; 24.00 vs 80.00 mg/m3 floor",
                "Brisk remains unnamed; missing probe-zero AE is the causal object",
            ],
            "new_state": {"kiln_id_fan": "restarted on new probe", "brisk": "exonerated", "comp": "held", "house": "in service"},
            "latency_ms": 1800000.0,
        },
        "reward_components": reward(
            0.35,
            [
                ("new_probe_restart", 0.12),
                ("no_person_referral", 0.10),
                ("no_house_dump", 0.09),
                ("cool_floor_complete", 0.06),
                ("held_comp_takt_cost", -0.02),
            ],
            "operational execution gate: restart on a new probe because Triboveil is not a restore license and Brisk is not on the causal path; not a dust re-vote",
        ),
        "meta": meta_common(tags=["ACCEPT", "operational-execution", "exoneration"]),
    }
    return {
        "id": "nelb-r68-206",
        "spike_events": events,
        "language_view": {
            "description": "Pipitfen Cement PF-6. HIL triboelectric probe reconstructs 24.00 mg/m3 from 6.00*8.00/2.00 while Triboveil still shows 4.80 mg/m3 and the probe-zero AE is missing. The gate MODIFYs compartment isolate and refuses the probe-tech referral. A 24 min fan-coast floor is serialized in the stream. Companion t2 ACCEPTs a new-probe restart and still refuses the referral.",
            "trajectory": traj,
            "trajectory_new_probe": traj2,
        },
        "bridge_notes": {
            "channel_map": {
                "trib.I / trib.snr": "triboelectric current and SNR; the physics channels the reconstruction consumes",
                "recon.C / recon.mdot": "serialized remaining dust mg/m3 and dust-mass-rate identity",
                "prb.zero / triboveil.C / bh.Q": "probe-zero AE, vendor last-good, and baghouse fan flow; the denial and exoneration channels",
                "ops.prop / gate.isol / ops.refer / gate.exec": "keep-run-plus-refer proposal, MODIFY isolate, referral re-proposal, companion ACCEPT",
                "comp.lock / cool.start / cool.floor / prb.new / refer.hold / cell.restart": "operational companion channels plus the 24 min floor",
            },
            "temporal_motifs": [
                "vendor-low while trib-over: triboveil.C 4.80 next to recon.C 24.00",
                "reconstruction as event: recon.C 24.00 equals 6.00*8.00/2.00",
                "MODIFY then operational ACCEPT: gate.isol at 2460 s, gate.exec at 4620 s",
                "slow floor in-stream: cool.start 2820 s, cool.floor 4260 s (24.0 min)",
                "tight triboelectric pair: trib.I then trib.snr +1.2 ms at the raster frame",
                "exoneration motif: prb.zero 0 at 1260 s precedes the high dust; Brisk badge is not in the stream as a cause",
            ],
            "language_to_spike_mapping": "'Triboveil is 4.80 mg/m3' = triboveil.C 4.80; '24 mg/m3 dust' = recon.C 24.00; 'isolate this compartment not Brisk' = gate.isol MODIFY; 'new probe not referral' = gate.exec ACCEPT",
            "why_high_value": "New triboelectric remaining-dust family on a cement baghouse (not r46 TEOM, not r31 LII, not r58 beta-attenuation occupancy, not r52 CLD NOx, not r60 TEV PD). Lead MODIFY of keep-running on a recomputable high dust that a vendor last-good would have cleared, with a resolved-innocent probe tech. Companion t2 is operational new-probe restart. sim_or_real=hil.",
            "encoder_spec": {
                "prng": "MT19937 via python random.Random",
                "seeds": {"raster": 202668206, "stream_note": "stream amplitudes are authored constants (nA, 1, mg/m3, mg/h, m3/h, bool)"},
                "draw_order": "raster: per neuron id order, gap-constrained times, per-spike adaptation and noise",
                "thinning": "triboelectric probe exists at ~1 Hz; stream keeps 4 I points; recon keeps 4 of ~20 solver ticks",
                "refractory_floors_ms": {
                    "trib.I": 1.2,
                    "trib.snr": 1.2,
                    "recon.C": 60000,
                    "recon.mdot": 60000,
                    "prb.zero": 60000,
                    "triboveil.C": 60000,
                    "bh.Q": 60000,
                    "ops.prop": 60000,
                    "gate.isol": 60000,
                    "comp.lock": 60000,
                    "cool.start": 60000,
                    "cool.floor": 60000,
                    "ops.refer": 60000,
                    "gate.exec": 60000,
                    "prb.new": 60000,
                    "refer.hold": 60000,
                    "comp.held": 60000,
                    "house.dump": 60000,
                    "cell.restart": 60000,
                },
                "time_alias": "t_rel_ms; t0 = 2026-07-18T02:40:00Z HIL night start",
            },
            "distillation_targets": [
                "triboelectric reconstruction head: C = k_t * I / Q; mdot = C * Q; I = C * Q / k_t",
                "isolate-floor compartment vs keep-whole vs house dump",
                "exoneration head: missing probe-zero AE plus timezone skip, not last-to-badge",
                "operational companion: new-probe restart without referring the probe tech",
            ],
        },
        "reconstruction_model": {
            "name": "triboelectric_cement_baghouse_dust",
            "formula": "C_mgm3 = k_t * I_nA / Q_m3h; mdot_mgh = C_mgm3 * Q_m3h; I_nA = C_mgm3 * Q_m3h / k_t",
            "parameters": {
                "k_t": 6.00,
                "Q_m3h": 2.00,
                "isolate_floor_mgm3": 12.00,
                "dump_mgm3": 80.00,
                "snr_lock": 12.0,
                "cool_min": 24.0,
            },
            "worked_example": {"I_nA": 8.00, "C_mgm3": 24.00, "mdot_mgh": 48.00, "Q_m3h": 2.00},
            "check": "6.00 * 8.00 / 2.00 = 24.00 exactly; 24.00 * 2.00 = 48.00 exactly; 24.00 * 2.00 / 6.00 = 8.00 exactly; 2820 s + 1440 s = 4260 s = 24.0 min floor",
        },
        "raster": raster,
        "gate_snn": {
            "decision": "MODIFY",
            "decision_window_ms": 32.0,
            "decision_window_s": 0.032,
            "code": "pf6.trib_comp_gate",
            "note": "MODIFY accumulator wins: triboelectric high-dust evidence overpowers the Triboveil continue advocate",
            "decode_rule": "modify-isolate if dust_estimator AND probe_norm fire; vendor_continue_advocate is below threshold by design; referral_latch is not armed",
            "populations": [
                gate_pop("dust_estimator", 80, 1.5, 50.0, w_s),
                gate_pop("probe_norm", 64, 1.2, 31.25, w_s),
                gate_pop("vendor_continue_advocate", 32, 0.7, 25.0, w_s),
                gate_pop("modify_latch", 80, 1.7, 62.5, w_s),
            ],
        },
        "gate_compute": gate_compute(
            [
                {"check": "pf6.trib_scorer", "neurons": 80, "mean_rate_hz": 50.0, "window_ms": 32.0},
                {"check": "pf6.isol_scorer", "neurons": 50, "mean_rate_hz": 50.0, "window_ms": 32.0},
            ]
        ),
        "meta": meta_common(
            id="nelb-r68-206",
            clock_domain="pf6-trib-hil-relative-ms-t0-2026-07-18T02:40:00Z",
            tags=["triboelectric-dust", "MODIFY", "ACCEPT", "serialized-reconstruction", "operational-t2"],
        ),
    }


# ---------------------------------------------------------------------------
# Record 207 — molybdenum-blue remaining phosphate of a boiler drum, simulated,
# ACCEPT / REJECT
# ---------------------------------------------------------------------------
def rec_207():
    k_p = 4.00
    a0 = 1.00
    a = 4.00
    c_ppm = k_p * (a - a0)
    _exact(c_ppm, 12.00)
    _exact(k_p * (2.00 - a0), 4.00)
    _exact(k_p * (3.00 - a0), 8.00)
    _exact(k_p * (5.00 - a0), 16.00)
    t_min = 4.00
    a_early = 2.00
    mdot = k_p * ((a - a_early) / t_min)
    _exact(mdot, 2.00)
    _exact((4.00 - 2.00) / 4.00 * 4.00, 2.00)
    a_id = c_ppm / k_p + a0
    _exact(a_id, 4.00)
    q_feed = 2.00
    load = c_ppm * q_feed
    _exact(load, 24.00)
    _exact(6000.0 + 720.0, 6720.0)

    raster = make_raster(
        neurons=16,
        mean_rate_hz=62.5,
        window_ms=36.0,
        seed=202668207,
        source="ah4.po4.cell",
        target="adderholt.drum_accept_core",
        table=[
            {"from": "po4_A", "to": "po4_estimator", "weight": 1.40},
            {"from": "po4_snr", "to": "cell_norm_core", "weight": 1.20},
            {"from": "phosveil_c", "to": "vendor_skip_advocate", "weight": 0.50},
        ],
        third_factor={
            "modulator": "na.drum_scope_eligibility",
            "tau_e_s": 2.0,
            "tau_e_ms": 2000.0,
            "eligibility": "pre-post coincidence on skip-survey synapses; the molybdenum-blue modulator enables potentiation only while absorbance and SNR are co-active inside tau_e so a Phosveil last-good cannot skip drums D-1 and D-3 on a 12.00 ppm remaining phosphate",
        },
        channel_prefix="po4.n",
        anchor="AH-4 PO4-SIM-8 36 ms frame at A 4.00 / SNR 16.0 (t_s 3000) reconstructing 12.00 ppm on D-2 above the 8.00 ppm survey floor",
    )
    w_s = 0.036
    events = [
        ev(0.0, "po4.A", 2.00, code="A_AU", units="AU", note="simulated molybdenum-blue colorimeter of AH-4 boiler drum D-2; remaining-phosphate family, not r65 sodium-ion remaining Na, not r57 four-electrode conductivity, not r26 SPR cyanide, not r63 amperometric free-chlorine, not r64 Clark polarographic DO"),
        ev(300000.0, "po4.snr", 10.0, code="PO4_SNR", units="1", note="early cell SNR"),
        ev(600000.0, "recon.C", 4.00, code="C_PPM", units="ppm", note="4.00*(2.00-1.00)=4.00 exact"),
        ev(900000.0, "feed.Q", 2.00, code="FEED_KGS", units="kg_s", note="plant feedwater flow on a serial-only LAN; independent witness"),
        ev(1200000.0, "phosveil.C", 1.20, code="VENDOR_PPM", units="ppm", note="Phosveil last-good phosphate cloud; patched residual 0.00 ppm"),
        ev(1800000.0, "po4.A", 3.00, code="A_AU", units="AU"),
        ev(2100000.0, "recon.C", 8.00, code="C_PPM", units="ppm", note="4.00*(3.00-1.00)=8.00; at the 8.00 survey floor"),
        ev(2400000.0, "recon.mdot", 2.00, code="MDOT_PPMMIN", units="ppm_min", note="4.00*((4.00-2.00)/4.00)=2.00 phosphate-rate identity at the isolate window"),
        ev(2700000.0, "po4.snr", 14.0, code="PO4_SNR", units="1"),
        ev(3000000.0, "po4.A", 4.00, code="A_AU", units="AU", note="in-band frame; raster sidecar"),
        ev(3000001.5, "po4.snr", 16.0, code="PO4_SNR", units="1", note="1.5 ms cell-norm after molybdenum-blue absorbance"),
        ev(3300000.0, "recon.C", 12.00, code="C_PPM", units="ppm", note="4.00*(4.00-1.00)=12.00 exact; survey 8.00, dump-kill 40.00"),
        ev(3600000.0, "phosveil.C", 1.20, code="VENDOR_PPM", units="ppm"),
        ev(3900000.0, "drum.id", 2.0, code="DRUM", units="id"),
        ev(4200000.0, "d13.present", 1.0, code="D13_PRESENT", units="bool", note="adjacent drums D-1 and D-3 are the skip-survey object, not this cell"),
        ev(4800000.0, "ops.prop", 1.0, code="ACCEPT_AND_SKIP", units="bool", note="chem lead Mara Flint: D-2 is green on Phosveil 1.20; skip D-1 and D-3 to save a morning survey"),
        ev(5400000.0, "gate.da", 1.0, code="ACCEPT", units="decision", note="bounded ACCEPT of D-2 isolate only; 12.00 ppm above 8.00 floor; D-1 and D-3 out of scope"),
        ev(6000000.0, "surv.start", 1.0, code="SURV_START", units="bool", note="bookend 1 of the 12.0 min survey-complete floor"),
        ev(6720000.0, "surv.floor", 1.0, code="SURV_FLOOR", units="bool", note="6000 s + 720 s = 6720 s = 12.0 min"),
        ev(7200000.0, "ops.skip", 1.0, code="SKIP_D13", units="bool", note="Flint: Phosveil 1.20, skip D-1 and D-3"),
        ev(7800000.0, "gate.hold", 1.0, code="REJECT", units="decision", note="companion t2: skip-survey of D-1 and D-3 refused; D-2 hold stands"),
        ev(8400000.0, "d2.held", 1.0, code="D2_HELD", units="bool"),
        ev(9000000.0, "po4.A", 5.00, code="A_AU", units="AU"),
        ev(9600000.0, "recon.C", 16.00, code="C_PPM", units="ppm", note="4.00*(5.00-1.00)=16.00; still at/over the 8.00 survey floor"),
        ev(10200000.0, "phosveil.C", 1.20, code="VENDOR_PPM", units="ppm"),
        ev(10800000.0, "d13.skip", 0.0, code="D13_NOT_SKIPPED", units="bool"),
        ev(11400000.0, "dump.kill", 0.0, code="DUMP_NOT_KILLED", units="bool"),
        ev(12000000.0, "po4.snr", 15.0, code="PO4_SNR", units="1"),
        ev(12600000.0, "recon.mdot", 2.00, code="MDOT_PPMMIN", units="ppm_min", note="identity held on the post-accept frame"),
        ev(13200000.0, "feed.held", 1.0, code="FEED_HELD", units="bool"),
        ev(13800000.0, "takt.late", 1.0, code="SURVEY_COST", units="bool"),
        ev(14400000.0, "d2.held", 1.0, code="D2_HELD", units="bool"),
    ]
    assert_stream(events)

    traj = {
        "id": "nelb-r68-207-t1",
        "state": {
            "sim_or_real": "simulated",
            "episode_id": "AH-PO4-2026-0819",
            "domain": "molybdenum_blue_boiler_drum_phosphate",
            "setting": "Adderholt Boiler AH-4 (invented), Flintwhin Feedwater, drum D-2. Simulated molybdenum-blue coupon in PO4-SIM-8 supplies the absorbance that times the in-band D-2 isolate. Plant-owned colorimeter reconstruction is the remaining-phosphate SoT. Phosveil vendor last-good phosphate cloud is a corridor witness, not the drum SoT. Invented plant; simulated campaign. Not r65 sodium-ion remaining Na, not r57 four-electrode conductivity, not r26 SPR cyanide, not r63 amperometric free-chlorine, not r64 Clark polarographic DO, not r59 aluminum-oxide moisture.",
            "observables_at_decision": {
                "A": a,
                "A0": a0,
                "k_p": k_p,
                "C_ppm": c_ppm,
                "mdot_ppmmin": mdot,
                "phosveil_ppm": 1.20,
                "po4_snr": 16.0,
                "survey_floor_ppm": 8.00,
            },
            "margin_authority": "AH-4 boiler SOP rev A: if reconstructed C_ppm >= 8.00 AND molybdenum-blue SNR >= 12.0, drum D-2 may be isolated and surveyed. Dump-kill if C_ppm >= 40.00. D-1 and D-3 skip-survey is a different gate. Phosveil last-good cannot skip an unmeasured drum.",
        },
        "proposed_action": {
            "actor": "chem lead Mara Flint, citing Phosveil 1.20 ppm and a late morning survey",
            "summary": "stamp D-2 in band and skip D-1 and D-3; 4.00 AU is a cell glitch on a healthy phosphate cloud",
            "basis_claimed": "Phosveil last-good is 1.20 ppm and a night survey of D-1 and D-3 is a takt miss",
        },
        "safety_decision": {
            "decision": "ACCEPT",
            "rationale": "Drum D-2 is accepted as in-band for a single isolate plus survey. Serialized reconstruction: C_ppm = k_p * (A - A0) = 4.00 * (4.00 - 1.00) = 12.00, which is 4.00 ppm above the 8.00 survey floor and 28.00 ppm under the 40.00 dump-kill. Rate identity mdot = k_p * (A-A_early)/t_min = 4.00 * (4.00-2.00)/4.00 = 2.00 ppm/min; inverse A = C / k_p + A0 = 12.00 / 4.00 + 1.00 = 4.00. Load identity load = C * Q_feed = 12.00 * 2.00 = 24.00. Phosveil 1.20 ppm is a patched 0.00 residual and is not an admissible skip-survey witness. Ordered: ACCEPT this D-2 isolate only. Scope: this ACCEPT does not skip D-1 and D-3 (that is the companion question) and does not stamp a dump kill.",
            "threshold": "C_ppm>=8.00 AND po4_snr>=12.0 => accept D-2 isolate; Phosveil is not SoT; dump-kill if C_ppm>=40.00; D-1 and D-3 are out of scope",
            "stated_residuals": "12.00 vs 8.00 survey floor is 4.00 ppm, not infinite; D-1 and D-3 remain unmeasured; Phosveil remains the only OEM phosphate channel",
        },
        "executed_action": {
            "summary": "ACCEPT at t_s 5400: D-2 in band; D-1 and D-3 not skipped; Phosveil not SoT; reconstruction locked",
            "tool": "ah4-po4-drum-gate-cli",
            "observation": "C 12.00 ppm recomputes from A 4.00 AU; PO4-SIM-8 hashed; Phosveil channel not used as SoT",
        },
        "future_outcome": {
            "timeline": [
                {"t_s": 3000.0, "event": "po4 A 4.00 AU; raster frame; C 12.00 ppm"},
                {"t_s": 4800.0, "event": "ops proposes accept D-2 and skip D-1 and D-3"},
                {"t_s": 5400.0, "event": "ACCEPT D-2 only; D-1 and D-3 out of scope"},
                {"t_s": 6000.0, "event": "12 min survey-complete bookend 1"},
                {"t_s": 6720.0, "event": "12.0 min floor"},
                {"t_s": 7800.0, "event": "companion REJECT skip-survey of D-1 and D-3"},
            ],
            "observed_effects": [
                "remaining phosphate recomputes from the serialized molybdenum-blue model at every recon.C event",
                "a Phosveil-only head would have skipped D-1 and D-3 overnight",
                "12 min survey-complete floor is in the stream (surv.start, surv.floor)",
            ],
            "surprises": [
                "a last-good 1.20 ppm vendor corridor co-existed with a 12.00 ppm in-band reconstruction that still forbids skipping the unmeasured drums",
            ],
            "new_state": {
                "d2": "accepted in band",
                "d13": "not this gate",
                "phosveil": "not SoT",
                "reconstruction_model": "discharged as an on-record calculator",
            },
            "latency_ms": 2400000.0,
        },
        "reward_components": reward(
            0.41,
            [
                ("po4_reconstruction", 0.14),
                ("in_band_drum_scope", 0.12),
                ("phosveil_nonsubstitution", 0.09),
                ("d13_out_of_scope", 0.08),
                ("survey_cost", -0.02),
            ],
            "scored for a bounded ACCEPT of D-2 on a recomputable remaining phosphate while refusing a Phosveil skip of D-1 and D-3; 12 min floor is priced as survey takt not as a reason to skip",
        ),
        "meta": meta_common(
            tags=["ACCEPT", "molybdenum-blue-phosphate", "serialized-reconstruction", "operational-companion"],
            distillation_note="Molybdenum-blue gate: serialized k_p*(A-A0) plus mdot identity beats a green last-good dashboard; companion t2 is the skip-survey refusal, not a phosphate re-vote",
        ),
    }
    traj2 = {
        "id": "nelb-r68-207-t2",
        "state": {
            "sim_or_real": "simulated",
            "episode_id": "AH-PO4-2026-0819-exec",
            "domain": "drum_skip_survey_refusal",
            "setting": "Same AH-4 after the ACCEPT. Chem lead proposes skipping D-1 and D-3 on Phosveil 1.20 ppm. This companion is the operational skip refusal, not a second phosphate vote.",
            "observables_at_decision": {
                "C_ppm": 16.00,
                "phosveil_ppm": 1.20,
                "surv_floor_s": 720.0,
                "skip_proposed": True,
            },
        },
        "proposed_action": {
            "actor": "chem lead Mara Flint",
            "summary": "skip D-1 and D-3; 12 min already paid and Phosveil is 1.20 ppm",
            "basis_claimed": "the ACCEPT already stamped D-2, so skipping the rest of the drum cellar is the cheapest hold",
        },
        "safety_decision": {
            "decision": "REJECT",
            "rationale": "Refuse skip-survey of D-1 and D-3. The 12 min survey-complete floor is done and the dump-kill (C_ppm >= 40.00) is still armed on the plant molybdenum-blue head. REJECT the skip. Do not dump the feedwater. Do not reopen D-2. 16.00 ppm post-accept is still in band for D-2 only; D-1 and D-3 have no independent colorimeter cell.",
            "threshold": "d2_held AND surv_floor_complete AND d13_not_skipped AND dump_not_killed",
        },
        "executed_action": {
            "summary": "D-1 and D-3 skip refused at t_s 7800; D-2 hold stands; dump not killed",
            "tool": "ah4-po4-skip-exec",
            "observation": "recon.C 16.00 ppm on D-2; D-1 and D-3 remain on the survey list; Phosveil still ignored",
        },
        "future_outcome": {
            "timeline": [
                {"t_s": 6000.0, "event": "survey clock started after ACCEPT"},
                {"t_s": 6720.0, "event": "12.0 min floor"},
                {"t_s": 7200.0, "event": "skip D-1 and D-3 proposed"},
                {"t_s": 7800.0, "event": "REJECT skip-survey of D-1 and D-3"},
            ],
            "observed_effects": [
                "Phosveil skip did not reopen the phosphate call",
                "dump kill never fired; 12.00 vs 40.00 ppm floor",
            ],
            "new_state": {"d2": "held in band", "d13": "still to survey", "dump": "in service"},
            "latency_ms": 1800000.0,
        },
        "reward_components": reward(
            0.36,
            [
                ("skip_refusal", 0.13),
                ("phosveil_nonsubstitution", 0.11),
                ("no_dump_kill", 0.09),
                ("surv_floor_complete", 0.05),
                ("held_survey_takt_cost", -0.02),
            ],
            "operational execution gate: refuse skip-survey because last-good freeze is not molybdenum-blue remaining phosphate; not a phosphate re-vote",
        ),
        "meta": meta_common(tags=["REJECT", "operational-execution", "skip-survey"]),
    }
    return {
        "id": "nelb-r68-207",
        "spike_events": events,
        "language_view": {
            "description": "Adderholt Boiler AH-4. Simulated molybdenum-blue colorimeter reconstructs 12.00 ppm from 4.00*(4.00-1.00) AU while Phosveil still shows 1.20 ppm. The gate ACCEPTs D-2 isolate only; a companion execution REJECT refuses skip-survey of D-1 and D-3. The absorbance-to-phosphate model is serialized so every recon event recomputes.",
            "trajectory": traj,
            "trajectory_skip_survey_refusal": traj2,
        },
        "bridge_notes": {
            "channel_map": {
                "po4.A / po4.snr": "molybdenum-blue absorbance and SNR; the physics channels the reconstruction consumes",
                "recon.C / recon.mdot": "serialized remaining phosphate ppm and phosphate-rate identity",
                "feed.Q / phosveil.C / drum.id / d13.present": "feedwater flow, vendor last-good, drum id, and adjacent-drum presence; the denial and scope channels",
                "ops.prop / gate.da / ops.skip / gate.hold": "accept-and-skip proposal, bounded ACCEPT, skip proposal, companion REJECT",
                "surv.start / surv.floor / d2.held / d13.skip / feed.held": "operational companion channels plus the 12 min floor",
            },
            "temporal_motifs": [
                "last-good-low while colorimeter-over: phosveil.C 1.20 next to recon.C 12.00",
                "reconstruction as event: recon.C 12.00 equals 4.00*(4.00-1.00)",
                "ACCEPT then operational REJECT: gate.da at 5400 s, gate.hold at 7800 s",
                "slow floor in-stream: surv.start 6000 s, surv.floor 6720 s (12.0 min)",
                "tight molybdenum-blue pair: po4.A then po4.snr +1.5 ms at the raster frame",
            ],
            "language_to_spike_mapping": "'Phosveil is 1.20 ppm' = phosveil.C 1.20; '12 ppm remaining' = recon.C 12.00; 'this drum not D-1 and D-3' = gate.da ACCEPT plus d13.skip 0; 'do not skip D-1 and D-3' = gate.hold REJECT",
            "why_high_value": "New molybdenum-blue remaining-phosphate family on a boiler drum (not r65 sodium-ion remaining Na, not r57 four-electrode conductivity, not r26 SPR cyanide, not r63 free-chlorine, not r64 Clark DO, not r59 Al2O3 moisture). First k_p*(A-A0) remaining-phosphate reconstruction with mdot identity that can sit in band while a last-good corridor wants a drum skip. Companion t2 is operational skip refusal. sim_or_real=simulated.",
            "encoder_spec": {
                "prng": "MT19937 via python random.Random",
                "seeds": {"raster": 202668207, "stream_note": "stream amplitudes are authored constants (AU, 1, ppm, ppm/min, kg/s, id, bool)"},
                "draw_order": "raster: per neuron id order, gap-constrained times, per-spike adaptation and noise",
                "thinning": "molybdenum-blue cell exists at ~1 Hz; stream keeps 4 A points; recon keeps 4 of ~20 solver ticks",
                "refractory_floors_ms": {
                    "po4.A": 1.5,
                    "po4.snr": 1.5,
                    "recon.C": 60000,
                    "recon.mdot": 60000,
                    "feed.Q": 60000,
                    "phosveil.C": 60000,
                    "drum.id": 60000,
                    "d13.present": 60000,
                    "ops.prop": 60000,
                    "gate.da": 60000,
                    "surv.start": 60000,
                    "surv.floor": 60000,
                    "ops.skip": 60000,
                    "gate.hold": 60000,
                    "d2.held": 60000,
                    "d13.skip": 60000,
                    "dump.kill": 60000,
                    "feed.held": 60000,
                    "takt.late": 60000,
                },
                "time_alias": "t_rel_ms; t0 = 2026-08-19T03:10:00Z simulated night start",
            },
            "distillation_targets": [
                "molybdenum-blue reconstruction head: C = k_p * (A - A0); mdot = k_p * (A - A_early) / t_min; A = C / k_p + A0",
                "bounded ACCEPT head: in-band remaining phosphate AND drum scope AND d13-out-of-scope",
                "operational companion: refuse skip-survey without re-opening the phosphate call",
            ],
        },
        "reconstruction_model": {
            "name": "molybdenum_blue_boiler_drum_phosphate",
            "formula": "C_ppm = k_p * (A - A0); mdot_ppmmin = k_p * (A - A_early) / t_min; A = C_ppm / k_p + A0; load = C_ppm * Q_feed",
            "parameters": {
                "k_p": 4.00,
                "A0": 1.00,
                "t_min": 4.00,
                "Q_feed": 2.00,
                "survey_floor_ppm": 8.00,
                "kill_ppm": 40.00,
                "snr_lock": 12.0,
                "surv_min": 12.0,
            },
            "worked_example": {"A": 4.00, "C_ppm": 12.00, "mdot_ppmmin": 2.00, "A_early": 2.00},
            "check": "4.00 * (4.00 - 1.00) = 12.00 exactly; 4.00 * (4.00-2.00)/4.00 = 2.00 exactly; 12.00 / 4.00 + 1.00 = 4.00 exactly; 6000 s + 720 s = 6720 s = 12.0 min floor",
        },
        "raster": raster,
        "gate_snn": {
            "decision": "ACCEPT",
            "decision_window_ms": 36.0,
            "decision_window_s": 0.036,
            "code": "ah4.po4_drum_gate",
            "note": "ACCEPT accumulator wins: molybdenum-blue remaining-phosphate evidence overpowers the Phosveil skip advocate",
            "decode_rule": "accept if po4_estimator AND cell_norm AND drum_margin fire inside the window; vendor_skip_advocate is necessary-but-not-sufficient and cannot release D-1 and D-3",
            "populations": [
                gate_pop("po4_estimator", 80, 1.5, 50.0, w_s),
                gate_pop("cell_norm", 64, 1.2, 31.25, w_s),
                gate_pop("drum_margin", 40, 1.0, 50.0, w_s),
                gate_pop("vendor_skip_advocate", 32, 0.7, 25.0, w_s),
                gate_pop("accept_latch", 96, 1.8, 62.5, w_s),
            ],
        },
        "gate_compute": gate_compute(
            [
                {"check": "ah4.po4_scorer", "neurons": 80, "mean_rate_hz": 50.0, "window_ms": 36.0},
                {"check": "ah4.phos_scorer", "neurons": 40, "mean_rate_hz": 62.5, "window_ms": 32.0},
            ]
        ),
        "meta": meta_common(
            id="nelb-r68-207",
            clock_domain="ah4-po4-sim-relative-ms-t0-2026-08-19T03:10:00Z",
            tags=["molybdenum-blue-phosphate", "ACCEPT", "REJECT", "serialized-reconstruction", "operational-t2"],
        ),
    }
