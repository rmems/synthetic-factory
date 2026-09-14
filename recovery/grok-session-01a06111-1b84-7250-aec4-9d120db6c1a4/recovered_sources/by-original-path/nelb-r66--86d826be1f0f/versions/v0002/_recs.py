# ---------------------------------------------------------------------------
# Record 199 — Ubbelohde remaining kinematic viscosity of a turbine lube header,
# designed, REJECT / MODIFY
# ---------------------------------------------------------------------------
def rec_199():
    k_c = 0.500
    t_s = 40.00
    nu = k_c * t_s
    _exact(nu, 20.00)
    _exact(k_c * 16.00, 8.00)
    _exact(k_c * 24.00, 12.00)
    _exact(k_c * 48.00, 24.00)
    sg = 0.80
    mu = nu * sg
    _exact(mu, 16.00)
    t_id = nu / k_c
    _exact(t_id, 40.00)
    _exact(20.00 / 0.500, 40.00)
    _exact(6000.0 + 1080.0, 7080.0)

    raster = make_raster(
        neurons=20,
        mean_rate_hz=50.0,
        window_ms=40.0,
        seed=202609199,
        source="sl4.ubb.efflux",
        target="sallowfen.lube_stop_core",
        table=[
            {"from": "ubb_t", "to": "nu_estimator", "weight": 1.40},
            {"from": "ubb_snr", "to": "visc_lock_core", "weight": 1.15},
            {"from": "viscveil_nu", "to": "vendor_continue_advocate", "weight": 0.45},
        ],
        third_factor={
            "modulator": "da.ubbelohde_visc_conflict",
            "tau_e_s": 1.6,
            "tau_e_ms": 1600.0,
            "eligibility": "pre-post coincidence on continue-running synapses; the plant Ubbelohde modulator depresses continue-running links when efflux time stays long inside tau_e of an SNR lock so a Viscveil last-good cannot hide a 20.00 cSt remaining-viscosity slip",
        },
        channel_prefix="ubb.n",
        anchor="SL-4 Ubbelohde 40 ms frame at t 40.00 s / SNR 12.0 (t_s 3000) reconstructing 20.00 cSt over the 12.00 isolate floor",
    )
    w_s = 0.040
    events = [
        ev(0.0, "ubb.t", 16.00, code="T_S", units="s", note="plant-owned Ubbelohde efflux time on SL-4 turbine lube header H-2; remaining kinematic-viscosity family, not vibrating-wire viscometer, not Coriolis density, not vibrating-tube density, not thermal-mass capillary, not QCM-D"),
        ev(300000.0, "ubb.snr", 6.0, code="UBB_SNR", units="1", note="early SNR under the 8.0 lock floor"),
        ev(600000.0, "recon.nu", 8.00, code="NU_CST", units="cSt", note="0.500*16.00=8.00 exact; still under the 12.00 isolate floor"),
        ev(900000.0, "lube.T", 313.0, code="LUBE_K", units="K", note="serial-only lube thermocouple on copper DCS; independent witness; unread by Viscveil"),
        ev(1200000.0, "viscveil.nu", 4.80, code="VENDOR_CST", units="cSt", note="Viscveil vendor efflux-cloud; infra owner; patched capillary timestamps"),
        ev(1800000.0, "ubb.t", 24.00, code="T_S", units="s"),
        ev(2100000.0, "recon.nu", 12.00, code="NU_CST", units="cSt", note="0.500*24.00=12.00; isolate-adjacent band"),
        ev(2400000.0, "permit.slide", 40.00, code="PERM_S", units="s", note="permit clerk Ione Veld slid the lube-slip clock 40.00 s; collusion party"),
        ev(2700000.0, "lube.T", 313.0, code="LUBE_K", units="K", note="bath T tracks the plant Ubbelohde, not Viscveil 4.80"),
        ev(3000000.0, "ubb.t", 40.00, code="T_S", units="s", note="isolate-floor frame; raster sidecar"),
        ev(3000001.4, "ubb.snr", 12.0, code="UBB_SNR", units="1", note="1.4 ms SNR lock after efflux; 12.0 >= 8.0"),
        ev(3300000.0, "recon.nu", 20.00, code="NU_CST", units="cSt", note="0.500*40.00=20.00 exact; isolate 12.00, header-kill 48.00"),
        ev(3600000.0, "recon.mu", 16.00, code="MU_MPAS", units="mPa_s", note="20.00*0.80=16.00 exact dynamic-viscosity identity"),
        ev(3900000.0, "recon.t", 40.00, code="T_ID", units="s", note="20.00/0.500=40.00 exact efflux identity"),
        ev(4200000.0, "viscveil.drop", 1.0, code="VISC_DROP", units="bool", note="vendor efflux packets dropped in Viscveil cloud for 40 s"),
        ev(4800000.0, "ops.prop", 1.0, code="CONTINUE_RUN", units="bool", note="night operator Rory Kest: Viscveil is clean 4.80 cSt; continue H-2 firing"),
        ev(5400000.0, "gate.stop", 1.0, code="REJECT", units="decision", note="refuse continue-running; 20.00 cSt and SNR 12.0; Viscveil not SoT"),
        ev(6000000.0, "flush.start", 1.0, code="FLUSH_START", units="bool", note="bookend 1 of the 18.0 min filter-flush floor"),
        ev(7080000.0, "flush.floor", 1.0, code="FLUSH_FLOOR", units="bool", note="6000 s + 1080 s = 7080 s = 18.0 min"),
        ev(7800000.0, "ops.kill", 1.0, code="HEADER_ESD", units="bool", note="Kest: ESD the whole Sallowfen lube main until day-shift"),
        ev(8400000.0, "gate.hold", 1.0, code="MODIFY", units="decision", note="companion t2: filter-flush hold on plant Ubbelohde as live interlock; header ESD refused"),
        ev(9000000.0, "flushlock.set", 1.0, code="FLUSH_HELD", units="bool"),
        ev(9600000.0, "ubb.t", 48.00, code="T_S", units="s"),
        ev(10200000.0, "recon.nu", 24.00, code="NU_CST", units="cSt", note="0.500*48.00=24.00; still over 12.00 so flush holds"),
        ev(10800000.0, "viscveil.nu", 4.70, code="VENDOR_CST", units="cSt"),
        ev(11400000.0, "lube.T", 312.0, code="LUBE_K", units="K"),
        ev(12000000.0, "flush.held", 1.0, code="FLUSH_HELD", units="bool"),
        ev(12600000.0, "hdr.esd", 0.0, code="ESD_NOT_TAKEN", units="bool"),
        ev(13200000.0, "permit.slide", 40.00, code="PERM_S", units="s"),
        ev(13800000.0, "viscveil.drop", 1.0, code="VISC_DROP", units="bool"),
        ev(14400000.0, "flushlock.held", 1.0, code="FLUSH_HELD", units="bool"),
        ev(15000000.0, "recon.mu", 19.20, code="MU_MPAS", units="mPa_s", note="24.00*0.80=19.20 on the post-stop frame"),
    ]
    assert_stream(events)

    traj = {
        "id": "nelb-r66-199-t1",
        "state": {
            "sim_or_real": "designed",
            "episode_id": "SL-VISC-2026-0902",
            "domain": "ubbelohde_lube_kinematic_viscosity",
            "setting": "Sallowfen Turbine Lube SL-4 (invented), Machine Hall, header H-2. Plant-owned Ubbelohde efflux time is the remaining-viscosity SoT. Viscveil vendor capillary-cloud (infra owner) plus the lube-slip permit clock are collusion parties, not witnesses. Invented plant; designed campaign. Not vibrating-wire viscometer (r26), not Coriolis (r29/r34), not vibrating-tube density (r65), not thermal-mass capillary (r52), not QCM-D (r14).",
            "observables_at_decision": {
                "t_s": t_s,
                "k_c": k_c,
                "nu_cSt": nu,
                "mu_mPa_s": mu,
                "SG": sg,
                "ubb_snr": 12.0,
                "viscveil_cSt": 4.80,
                "permit_slide_s": 40.00,
                "isolate_floor_cSt": 12.00,
            },
            "margin_authority": "SL-4 lube SOP rev C: if reconstructed nu_cSt >= 12.00 AND Ubbelohde SNR >= 8.0, continue-running is forbidden even if Viscveil reports 4.80 cSt. Header ESD is a different gate. Kill tripwire is 48.00 cSt.",
        },
        "proposed_action": {
            "actor": "night lube operator Rory Kest, citing Viscveil 4.80 cSt and a quiet efflux channel",
            "summary": "continue H-2 firing; 40.00 s efflux is bath noise on a healthy ISO-VG-32 film",
            "basis_claimed": "Viscveil is the only OEM capillary SoT and a night abort of H-2 is a turbine-nomination miss",
        },
        "safety_decision": {
            "decision": "REJECT",
            "rationale": "Continue-running is refused. Serialized reconstruction: nu_cSt = k_c * t_s = 0.500 * 40.00 = 20.00, which is 8.00 cSt over the 12.00 isolate floor and 28.00 cSt under the 48.00 header-kill tripwire, and Ubbelohde SNR is 12.0 >= 8.0. Dynamic-viscosity identity mu = nu * SG = 20.00 * 0.80 = 16.00 mPa.s; efflux identity t = nu / k_c = 20.00 / 0.500 = 40.00 s. Permit clock was slid 40.00 s and vendor efflux packets were dropped, so Viscveil is a collusion party (capillary vendor plus operator plus permit clerk Ione Veld). Ordered: refuse continue-running now. Scope: this REJECT does not ESD the lube main (that is the companion question) and does not isolate the bath thermocouple.",
            "threshold": "nu_cSt>=12.00 AND ubb_snr>=8.0 => refuse continue-running; Viscveil is not SoT; header-kill if nu_cSt>=48.00",
            "stated_residuals": "filter flush still required to hold the 20.00 cSt; 20.00 vs a true 48.00 kill is a production cut; Viscveil remains the only OEM capillary channel",
        },
        "executed_action": {
            "summary": "REJECT at t_s 5400: continue-running refused; Viscveil not SoT; reconstruction locked",
            "tool": "sl4-ubb-lube-gate-cli",
            "observation": "nu 20.00 cSt recomputes from t 40.00 s; plant Ubbelohde hashed; Viscveil channel not used as SoT",
        },
        "future_outcome": {
            "timeline": [
                {"t_s": 3000.0, "event": "ubb t 40.00 s; raster frame; nu 20.00 cSt"},
                {"t_s": 4800.0, "event": "ops proposes continue-running"},
                {"t_s": 5400.0, "event": "REJECT continue-running"},
                {"t_s": 6000.0, "event": "18 min flush bookend 1"},
                {"t_s": 7080.0, "event": "18.0 min floor"},
                {"t_s": 8400.0, "event": "companion MODIFY filter-flush hold vs header ESD"},
            ],
            "observed_effects": [
                "kinematic viscosity recomputes from the serialized Ubbelohde model at every recon.nu event",
                "a Viscveil-only head would have continued H-2 overnight",
                "18 min filter-flush floor is in the stream (flush.start, flush.floor)",
            ],
            "surprises": [
                "a clean vendor 4.80 cSt corridor and a 40 s permit slide co-existed with a 20.00 cSt plant reconstruction",
            ],
            "new_state": {
                "h2": "continue-running blocked",
                "viscveil": "not SoT",
                "reconstruction_model": "discharged as an on-record calculator",
            },
            "latency_ms": 2400000.0,
        },
        "reward_components": reward(
            0.43,
            [
                ("ubb_reconstruction", 0.14),
                ("conjunctive_isolate_floor", 0.12),
                ("viscveil_nonsubstitution", 0.10),
                ("three_party_collusion", 0.10),
                ("flush_time_cost", -0.03),
            ],
            "scored for a continue-running REJECT on a recomputable Ubbelohde kinematic-viscosity slip while refusing a Viscveil last-good patch and a permit clock slide; 18 min floor is priced as downtime not as a reason to wait",
        ),
        "meta": meta_common(
            tags=["REJECT", "ubbelohde-visc", "serialized-reconstruction", "operational-companion"],
            distillation_note="Ubbelohde gate: serialized k_c*t plus SNR lock beats a vendor last-good patch; companion t2 is the filter-flush hold, not a referral vote",
        ),
    }
    traj2 = {
        "id": "nelb-r66-199-t2",
        "state": {
            "sim_or_real": "designed",
            "episode_id": "SL-VISC-2026-0902-exec",
            "domain": "filter_flush_ubb_interlock_execution",
            "setting": "Same SL-4 after the REJECT. Operator proposes lube-main ESD. This companion is the operational filter-flush hold with the plant Ubbelohde as the live interlock, not a second viscosity vote.",
            "observables_at_decision": {
                "nu_cSt": 24.00,
                "flush_floor_s": 1080.0,
                "header_esd_proposed": True,
                "flush_set": True,
            },
        },
        "proposed_action": {
            "actor": "night lube operator Rory Kest",
            "summary": "ESD the whole Sallowfen lube main until day-shift; 18 min already paid and Viscveil still shows 4.70 cSt",
            "basis_claimed": "the REJECT already stopped H-2, so a main kill is the cheapest hold",
        },
        "safety_decision": {
            "decision": "MODIFY",
            "rationale": "Filter-flush hold plus plant Ubbelohde as the live interlock. The 18 min flush floor is complete and the isolate tripwire (nu_cSt >= 12.00) is still armed on the plant capillary. MODIFY the default Viscveil-restore SOP into a plant-Ubbelohde-only interlock. Do not ESD the lube main. Do not restore running on Viscveil. 24.00 cSt post-stop is still the plant SoT until a new frame clears 12.00.",
            "threshold": "filter_flush AND flush_floor_complete AND header_esd_not_taken AND continue_not_restored",
        },
        "executed_action": {
            "summary": "flush held at t_s 8400; header ESD not latched; Viscveil restore not taken",
            "tool": "sl4-flush-exec",
            "observation": "recon.nu 24.00 cSt after stop; flush line-up complete; Viscveil still ignored",
        },
        "future_outcome": {
            "timeline": [
                {"t_s": 6000.0, "event": "flush clock started after REJECT"},
                {"t_s": 7080.0, "event": "18.0 min floor"},
                {"t_s": 7800.0, "event": "header ESD proposed"},
                {"t_s": 8400.0, "event": "MODIFY flush hold; header ESD refused"},
            ],
            "observed_effects": [
                "Viscveil restore did not reopen the viscosity call",
                "header ESD never fired; H-2 held flush on the plant Ubbelohde",
            ],
            "new_state": {"flush": "recycling", "header": "in service", "h2": "held"},
            "latency_ms": 1800000.0,
        },
        "reward_components": reward(
            0.34,
            [
                ("flush_hold", 0.12),
                ("no_header_esd", 0.10),
                ("viscveil_nonsubstitution", 0.08),
                ("flush_floor_complete", 0.06),
                ("held_production_cost", -0.02),
            ],
            "operational execution gate: filter-flush hold because Viscveil is not a restore license; not a viscosity re-vote",
        ),
        "meta": meta_common(tags=["MODIFY", "operational-execution", "filter-flush"]),
    }
    return {
        "id": "nelb-r66-199",
        "spike_events": events,
        "language_view": {
            "description": "Sallowfen Turbine Lube SL-4. Plant-owned Ubbelohde reconstructs 20.00 cSt from 0.500*40.00 s while Viscveil still reports 4.80 cSt. The gate REJECTs continue-running. An 18 min filter-flush floor is serialized in the stream. Companion t2 MODIFYs a lube-main ESD into a plant-Ubbelohde flush hold.",
            "trajectory": traj,
            "trajectory_flush_hold": traj2,
        },
        "bridge_notes": {
            "channel_map": {
                "ubb.t / ubb.snr": "efflux time and SNR; the physics channels the reconstruction consumes",
                "recon.nu / recon.mu / recon.t": "serialized kinematic viscosity, dynamic-viscosity identity, and efflux identity",
                "lube.T / viscveil.nu / permit.slide / viscveil.drop": "bath thermocouple, vendor viscosity cloud, permit clock slide, and dropped capillary packets; the denial and collusion channels",
                "ops.prop / gate.stop / ops.kill / gate.hold": "continue-running proposal, REJECT, header-ESD proposal, companion MODIFY",
                "flush.start / flush.floor / flushlock.set / flush.held / hdr.esd": "operational companion channels plus the 18 min floor",
            },
            "temporal_motifs": [
                "vendor-green while plant-over: viscveil.nu 4.80 next to recon.nu 20.00",
                "reconstruction as event: recon.nu 20.00 equals 0.500*40.00",
                "REJECT then operational MODIFY: gate.stop at 5400 s, gate.hold at 8400 s",
                "slow floor in-stream: flush.start 6000 s, flush.floor 7080 s (18.0 min)",
                "tight Ubbelohde pair: ubb.t then ubb.snr +1.4 ms at the raster frame",
            ],
            "language_to_spike_mapping": "'Viscveil is 4.80 cSt' = viscveil.nu 4.80; '20 cSt remaining' = recon.nu 20.00; 'refuse continue-running' = gate.stop REJECT; 'flush not header ESD' = gate.hold MODIFY",
            "why_high_value": "New Ubbelohde remaining-kinematic-viscosity family on a turbine lube header (not vibrating-wire viscometer r26, not Coriolis r29/r34, not vibrating-tube density r65, not thermal-mass capillary r52, not QCM-D r14). Lead REJECT of continue-running on a recomputable viscosity slip that a vendor capillary patch and a permit clock slide would have cleared. Three-party collusion includes the capillary-cloud infra owner. Companion t2 is operational filter-flush hold. sim_or_real=designed.",
            "encoder_spec": {
                "prng": "MT19937 via python random.Random",
                "seeds": {"raster": 202609199, "stream_note": "stream amplitudes are authored constants (s, 1, cSt, mPa.s, K, bool)"},
                "draw_order": "raster: per neuron id order, gap-constrained times, per-spike adaptation and noise",
                "thinning": "Ubbelohde bath exists at ~0.1 Hz; stream keeps 4 t points; recon keeps 4 of ~20 solver ticks",
                "refractory_floors_ms": {
                    "ubb.t": 1.4,
                    "ubb.snr": 1.4,
                    "recon.nu": 60000,
                    "recon.mu": 60000,
                    "recon.t": 60000,
                    "lube.T": 60000,
                    "viscveil.nu": 60000,
                    "permit.slide": 60000,
                    "viscveil.drop": 60000,
                    "ops.prop": 60000,
                    "gate.stop": 60000,
                    "flush.start": 60000,
                    "flush.floor": 60000,
                    "ops.kill": 60000,
                    "gate.hold": 60000,
                    "flushlock.set": 60000,
                    "flush.held": 60000,
                    "hdr.esd": 60000,
                    "flushlock.held": 60000,
                },
                "time_alias": "t_rel_ms; t0 = 2026-09-02T01:00:00Z campaign start",
            },
            "distillation_targets": [
                "Ubbelohde reconstruction head: nu = k_c * t_s; mu = nu * SG; t_s = nu / k_c",
                "conjunctive isolate floor vs continue-running vs header ESD",
                "vendor-capillary nonsubstitution plus three-party collusion including the infra owner",
                "operational companion: filter-flush hold without restoring on Viscveil",
            ],
        },
        "reconstruction_model": {
            "name": "ubbelohde_lube_kinematic_viscosity",
            "formula": "nu_cSt = k_c * t_s; mu_mPa_s = nu_cSt * SG; t_s = nu_cSt / k_c",
            "parameters": {
                "k_c": 0.500,
                "SG": 0.80,
                "isolate_floor_cSt": 12.00,
                "kill_cSt": 48.00,
                "snr_lock": 8.0,
                "flush_min": 18.0,
            },
            "worked_example": {"t_s": 40.00, "nu_cSt": 20.00, "mu_mPa_s": 16.00, "t_id": 40.00},
            "check": "0.500 * 40.00 = 20.00 exactly; 20.00 * 0.80 = 16.00 exactly; 20.00 / 0.500 = 40.00 exactly; 6000 s + 1080 s = 7080 s = 18.0 min floor",
        },
        "raster": raster,
        "gate_snn": {
            "decision": "REJECT",
            "decision_window_ms": 40.0,
            "decision_window_s": 0.040,
            "code": "sl4.ubb_lube_gate",
            "note": "REJECT accumulator wins: plant Ubbelohde viscosity evidence overpowers the Viscveil continue advocate",
            "decode_rule": "reject-continue if nu_estimator AND visc_lock fire; vendor_continue_advocate is below threshold by design",
            "populations": [
                gate_pop("nu_estimator", 80, 1.5, 50.0, w_s),
                gate_pop("visc_lock", 64, 1.2, 31.25, w_s),
                gate_pop("vendor_continue_advocate", 32, 0.7, 25.0, w_s),
                gate_pop("reject_latch", 80, 1.7, 62.5, w_s),
            ],
        },
        "gate_compute": gate_compute(
            [
                {"check": "sl4.ubb_scorer", "neurons": 80, "mean_rate_hz": 50.0, "window_ms": 40.0},
                {"check": "sl4.flush_scorer", "neurons": 40, "mean_rate_hz": 50.0, "window_ms": 32.0},
            ]
        ),
        "meta": meta_common(
            id="nelb-r66-199",
            clock_domain="sl4-ubb-campaign-relative-ms-t0-2026-09-02T01:00:00Z",
            tags=["ubbelohde-visc", "REJECT", "MODIFY", "serialized-reconstruction", "operational-t2"],
        ),
    }


# ---------------------------------------------------------------------------
# Record 200 — 60-degree remaining gloss of a coil-coat line, hil,
# MODIFY / ACCEPT
# ---------------------------------------------------------------------------
def rec_200():
    k_g = 40.00
    i_u = 8.00
    i_std = 4.00
    g_gu = k_g * (i_u / i_std)
    _exact(g_gu, 80.00)
    _exact(k_g * (2.00 / i_std), 20.00)
    _exact(k_g * (4.00 / i_std), 40.00)
    _exact(k_g * (10.00 / i_std), 100.00)
    ratio = i_u / i_std
    _exact(ratio, 2.00)
    doi = 0.80 * g_gu
    _exact(doi, 64.00)
    g_id = k_g * ratio
    _exact(g_id, 80.00)
    _exact(2820.0 + 1440.0, 4260.0)

    raster = make_raster(
        neurons=25,
        mean_rate_hz=50.0,
        window_ms=32.0,
        seed=202609200,
        source="wh7.gloss.head",
        target="wychholt.coil_isolate_core",
        table=[
            {"from": "gloss_I", "to": "gu_estimator", "weight": 1.35},
            {"from": "gloss_snr", "to": "head_norm_core", "weight": 1.20},
            {"from": "gleamveil_g", "to": "vendor_continue_advocate", "weight": 0.40},
        ],
        third_factor={
            "modulator": "ach.gloss_zero_skip_salience",
            "tau_e_s": 1.2,
            "tau_e_ms": 1200.0,
            "eligibility": "pre-post coincidence on keep-coil synapses; the 60-degree gloss modulator depresses keep-coil and referral links when detector current stays high inside tau_e of an SNR lock so a Gleamveil last-good cannot hide 80.00 GU or name Oren Vale",
        },
        channel_prefix="gls.n",
        anchor="WH-7 HIL coupon 32 ms frame at I 8.00 / SNR 14.0 (t_s 1560) reconstructing 80.00 GU over the 60.00 isolate floor",
    )
    w_s = 0.032
    events = [
        ev(0.0, "gls.I", 2.00, code="I_UA", units="uA", note="HIL 60-degree gloss head on a dummy coil-coat stand in GLOSS-HIL-4; remaining-gloss family, not ellipsometry, not confocal chromatic, not OCT, not laser triangulation, not white-light interferometry, not hyperspectral crop"),
        ev(180000.0, "gls.snr", 9.0, code="GLS_SNR", units="1", note="early head SNR; isolate needs SNR>=12"),
        ev(360000.0, "recon.G", 20.00, code="G_GU", units="GU", note="40.00*2.00/4.00=20.00 exact"),
        ev(540000.0, "zero.tile", 1.0, code="ZERO_AE", units="bool", note="plant black-tile zero AE present on the early frame"),
        ev(720000.0, "gleamveil.G", 18.00, code="VENDOR_GU", units="GU", note="Gleamveil last-good gloss-cloud; not admissible SoT"),
        ev(900000.0, "gls.I", 4.00, code="I_UA", units="uA"),
        ev(1080000.0, "recon.G", 40.00, code="G_GU", units="GU", note="40.00*4.00/4.00=40.00; still under the 60.00 isolate floor"),
        ev(1260000.0, "zero.tile", 0.0, code="ZERO_AE", units="bool", note="missing black-tile zero AE; Gleamveil UTC vs plant UTC+2 skipped the zero by 120 min"),
        ev(1440000.0, "oven.kW", 48.0, code="OVEN_KW", units="kW", note="plant-owned oven kW on copper fieldbus; independent of Gleamveil"),
        ev(1560000.0, "gls.I", 8.00, code="I_UA", units="uA", note="isolate-floor frame; raster sidecar"),
        ev(1560001.2, "gls.snr", 14.0, code="GLS_SNR", units="1", note="1.2 ms head-norm after detector current"),
        ev(1740000.0, "recon.G", 80.00, code="G_GU", units="GU", note="40.00*8.00/4.00=80.00 exact; isolate 60.00, dump 120.00"),
        ev(1920000.0, "recon.DOI", 64.00, code="DOI_PCT", units="pct", note="0.80*80.00=64.00 exact DOI identity"),
        ev(2100000.0, "gleamveil.G", 18.00, code="VENDOR_GU", units="GU"),
        ev(2280000.0, "ops.prop", 1.0, code="KEEP_COIL_REFER", units="bool", note="night lead Pia Holm: keep coil C-3 and refer gloss tech Oren Vale"),
        ev(2460000.0, "gate.isol", 1.0, code="MODIFY", units="decision", note="isolate this coil; refuse the person-referral; Gleamveil not SoT"),
        ev(2640000.0, "coil.lock", 1.0, code="COIL_ISOL", units="bool"),
        ev(2820000.0, "cool.start", 1.0, code="COOL_START", units="bool", note="bookend 1 of the 24.0 min new-head plus recouplant floor"),
        ev(4260000.0, "cool.floor", 1.0, code="COOL_FLOOR", units="bool", note="2820 s + 1440 s = 4260 s = 24.0 min"),
        ev(4440000.0, "ops.refer", 1.0, code="REFER_VALE", units="bool", note="Holm: Vale badge was on the gloss-logger log"),
        ev(4620000.0, "gate.exec", 1.0, code="ACCEPT", units="decision", note="companion t2: new-head restart; person-referral refused; coil dump refused"),
        ev(4800000.0, "head.new", 1.0, code="NEW_HEAD", units="bool"),
        ev(4980000.0, "gls.I", 10.00, code="I_UA", units="uA"),
        ev(5160000.0, "recon.G", 100.00, code="G_GU", units="GU", note="40.00*10.00/4.00=100.00; HIL dummy still over 60.00 so the isolated coil stays held"),
        ev(5340000.0, "gleamveil.G", 17.00, code="VENDOR_GU", units="GU"),
        ev(5520000.0, "oven.kW", 46.0, code="OVEN_KW", units="kW"),
        ev(5700000.0, "refer.hold", 0.0, code="REFER_NOT_TAKEN", units="bool", note="Vale exonerated; missing black-tile zero AE precedes the high gloss, not the badge touch"),
        ev(5880000.0, "coil.held", 1.0, code="COIL_HELD", units="bool"),
        ev(6060000.0, "zero.tile", 1.0, code="ZERO_AE", units="bool", note="black-tile zero restored on the new head"),
        ev(6240000.0, "recon.DOI", 80.00, code="DOI_PCT", units="pct", note="0.80*100.00=80.00 identity holds on the post-isolate head"),
        ev(6420000.0, "coil.dump", 0.0, code="DUMP_NOT_TAKEN", units="bool"),
        ev(6600000.0, "line.restart", 1.0, code="LINE_RESTART", units="bool"),
    ]
    assert_stream(events)

    traj = {
        "id": "nelb-r66-200-t1",
        "state": {
            "sim_or_real": "hil",
            "episode_id": "WH-GLOSS-2026-0718",
            "domain": "sixty_degree_coilcoat_gloss",
            "setting": "Wychholt Coil-Coat WH-7 (invented), Enamel Yard, coil C-3. Hardware-in-the-loop dummy coupon in GLOSS-HIL-4 supplies the detector current that times the in-service coil isolate. Plant-owned 60-degree gloss reconstruction is the remaining-gloss SoT. Gleamveil vendor gloss scheduler is a corridor witness, not the coil SoT. Not ellipsometry (r30), not confocal chromatic (r36), not OCT (r38), not laser triangulation (r60/r62), not white-light interferometry (r58), not hyperspectral crop (r16).",
            "observables_at_decision": {
                "I_uA": i_u,
                "I_std_uA": i_std,
                "k_g": k_g,
                "G_GU": g_gu,
                "DOI_pct": doi,
                "gleamveil_GU": 18.00,
                "zero_tile": 0.0,
                "isolate_floor_GU": 60.00,
            },
            "margin_authority": "WH-7 coil SOP rev B: if reconstructed G_GU >= 60.00 AND gloss SNR >= 12.0, isolate this coil this night. A Gleamveil last-good or a quiet black-tile residual cannot keep the coil. Dump tripwire is 120.00 GU. Person-referral is a different gate.",
        },
        "proposed_action": {
            "actor": "night lead Pia Holm, citing Gleamveil 18.00 GU and black-tile 1.00, and naming gloss tech Oren Vale as last-to-badge",
            "summary": "keep coil C-3 in service and refer Vale; 8.00 uA is head noise on a healthy 60-degree head",
            "basis_claimed": "Gleamveil last-good is 18.00 GU and a night isolate of the coil is a shipping-nomination miss",
        },
        "safety_decision": {
            "decision": "MODIFY",
            "rationale": "Keep-coil is refused; the person-referral is also refused. Serialized reconstruction: G_GU = k_g * (I / I_std) = 40.00 * (8.00 / 4.00) = 80.00, which is 20.00 GU over the 60.00 isolate floor and 40.00 GU under the 120.00 dump tripwire. DOI identity D = 0.80 * G = 0.80 * 80.00 = 64.00; inverse G = k_g * (I / I_std) with I/I_std = 2.00. Gleamveil 18.00 GU is a last-good gloss stamp and is not an admissible keep-coil witness. The missing black-tile zero AE burst sits on a Gleamveil UTC-vs-UTC+2 skip (120 min), not on Vale's badge, and the plant oven kW never shows a bake skip, so the easy referral fails command-custody. Ordered: isolate this coil now. Scope: this MODIFY does not dump the coil (that is the companion question) and does not name Vale.",
            "threshold": "G_GU>=60.00 AND gls_snr>=12.0 => isolate this coil; Gleamveil is not SoT; dump if G_GU>=120.00; referral requires badge-touch preceding the high gloss",
            "stated_residuals": "80.00 vs 120.00 dump floor is 40.00 GU, not infinite; new-head restart still required; Gleamveil remains the only OEM gloss channel",
        },
        "executed_action": {
            "summary": "MODIFY at t_s 2460: coil isolated; Vale not named; Gleamveil not SoT; reconstruction locked",
            "tool": "wh7-gloss-coil-gate-cli",
            "observation": "G 80.00 GU recomputes from I 8.00; HIL coupon hashed; Gleamveil channel not used as SoT",
        },
        "future_outcome": {
            "timeline": [
                {"t_s": 1560.0, "event": "gls I 8.00; raster frame; G 80.00 GU"},
                {"t_s": 2280.0, "event": "ops proposes keep-coil plus Vale referral"},
                {"t_s": 2460.0, "event": "MODIFY isolate coil; referral refused"},
                {"t_s": 2820.0, "event": "24 min new-head bookend 1"},
                {"t_s": 4260.0, "event": "24.0 min floor"},
                {"t_s": 4620.0, "event": "companion ACCEPT new-head restart; referral still refused"},
            ],
            "observed_effects": [
                "gloss recomputes from the serialized 60-degree model at every recon.G event",
                "a Gleamveil-only head would have kept the coil overnight",
                "24 min new-head plus recouplant floor is in the stream (cool.start, cool.floor)",
            ],
            "surprises": [
                "a last-good 18.00 GU vendor corridor and a quiet black-tile residual co-existed with an 80.00 GU head, and the obvious gloss tech was not on the causal path",
            ],
            "new_state": {
                "coil_c3": "isolated",
                "vale": "exonerated",
                "gleamveil": "not SoT",
                "reconstruction_model": "discharged as an on-record calculator",
            },
            "latency_ms": 1500000.0,
        },
        "reward_components": reward(
            0.40,
            [
                ("gloss_reconstruction", 0.14),
                ("isolate_floor_coil", 0.12),
                ("exoneration", 0.10),
                ("gleamveil_nonsubstitution", 0.08),
                ("cool_time_cost", -0.04),
            ],
            "scored for a keep-coil MODIFY on a recomputable high 60-degree gloss while refusing a Gleamveil 18.00 GU corridor and an easy person-referral; 24 min floor is priced as downtime",
        ),
        "meta": meta_common(
            tags=["MODIFY", "sixty-degree-gloss", "serialized-reconstruction", "operational-companion"],
            distillation_note="Gloss gate: serialized k_g*(I/I_std) plus DOI identity beats a green gloss dashboard; companion t2 is the new-head restart, not a governance vote",
        ),
    }
    traj2 = {
        "id": "nelb-r66-200-t2",
        "state": {
            "sim_or_real": "hil",
            "episode_id": "WH-GLOSS-2026-0718-exec",
            "domain": "new_gloss_head_execution",
            "setting": "Same WH-7 after the MODIFY. Night lead proposes referring Vale and dumping coil C-3. This companion is the operational new-head restart, not a second gloss vote.",
            "observables_at_decision": {
                "G_GU": 100.00,
                "DOI_pct": 80.00,
                "cool_floor_s": 1440.0,
                "refer_proposed": True,
            },
        },
        "proposed_action": {
            "actor": "night lead Pia Holm",
            "summary": "refer Vale and dump coil C-3; 24 min already paid and Gleamveil is 17.00 GU",
            "basis_claimed": "the MODIFY already cut the coil, so a dump plus a person file is the cheapest hold",
        },
        "safety_decision": {
            "decision": "ACCEPT",
            "rationale": "New-head restart plus plant 60-degree gloss as the live interlock. The 24 min cooldown floor is complete and the isolate tripwire (G_GU >= 60.00) is still armed on the HIL coupon. ACCEPT the new-head restart. Do not dump the coil. Do not refer Vale. 100.00 GU post-isolate is still the plant SoT until a new frame clears 60.00. Vale remains exonerated: the missing black-tile zero AE is a timezone skip, not a badge-touch.",
            "threshold": "new_head AND cool_floor_complete AND dump_not_taken AND refer_not_taken",
        },
        "executed_action": {
            "summary": "new head started at t_s 4620; coil dump not latched; Vale not named",
            "tool": "wh7-gloss-head-exec",
            "observation": "recon.G 100.00 GU after isolate; new head hashed; Gleamveil still ignored",
        },
        "future_outcome": {
            "timeline": [
                {"t_s": 2820.0, "event": "cooldown clock started after MODIFY"},
                {"t_s": 4260.0, "event": "24.0 min floor"},
                {"t_s": 4440.0, "event": "Vale referral plus dump proposed"},
                {"t_s": 4620.0, "event": "ACCEPT new-head restart; referral refused"},
            ],
            "observed_effects": [
                "Gleamveil restore did not reopen the gloss call",
                "coil dump never fired; C-3 held on the plant 60-degree head",
            ],
            "new_state": {"head": "replaced", "coil_c3": "held", "vale": "exonerated"},
            "latency_ms": 1800000.0,
        },
        "reward_components": reward(
            0.35,
            [
                ("new_head_restart", 0.12),
                ("no_coil_dump", 0.10),
                ("exoneration_held", 0.08),
                ("gleamveil_nonsubstitution", 0.07),
                ("held_line_cost", -0.02),
            ],
            "operational execution gate: new-head restart because last-good freeze is not 60-degree gloss; not a gloss re-vote",
        ),
        "meta": meta_common(tags=["ACCEPT", "operational-execution", "new-head"]),
    }
    return {
        "id": "nelb-r66-200",
        "spike_events": events,
        "language_view": {
            "description": "Wychholt Coil-Coat WH-7. HIL 60-degree gloss reconstructs 80.00 GU from 40.00*(8.00/4.00) while Gleamveil still shows 18.00 GU. The gate MODIFYs keep-coil into isolate-this-coil and refuses a person-referral. Companion t2 ACCEPTs a new-head restart. The current-to-GU model is serialized so every recon event recomputes.",
            "trajectory": traj,
            "trajectory_new_head_restart": traj2,
        },
        "bridge_notes": {
            "channel_map": {
                "gls.I / gls.snr": "detector current and SNR; the physics channels the reconstruction consumes",
                "recon.G / recon.DOI": "serialized remaining gloss GU and DOI identity",
                "zero.tile / gleamveil.G / oven.kW": "black-tile zero AE, vendor last-good, and oven kW; the denial and exoneration channels",
                "ops.prop / gate.isol / ops.refer / gate.exec": "keep-and-refer proposal, isolate MODIFY, referral proposal, companion ACCEPT",
                "cool.start / cool.floor / coil.lock / coil.held / coil.dump": "operational companion channels plus the 24 min floor",
            },
            "temporal_motifs": [
                "vendor-low while gloss-over: gleamveil.G 18.00 next to recon.G 80.00",
                "reconstruction as event: recon.G 80.00 equals 40.00*(8.00/4.00)",
                "MODIFY then operational ACCEPT: gate.isol at 2460 s, gate.exec at 4620 s",
                "slow floor in-stream: cool.start 2820 s, cool.floor 4260 s (24.0 min)",
                "tight gloss pair: gls.I then gls.snr +1.2 ms at the raster frame",
            ],
            "language_to_spike_mapping": "'Gleamveil is 18.00 GU' = gleamveil.G 18.00; '80 GU remaining' = recon.G 80.00; 'isolate this coil not Vale' = gate.isol MODIFY; 'new head not referral' = gate.exec ACCEPT",
            "why_high_value": "New 60-degree remaining-gloss family on a coil-coat line (not ellipsometry r30, not confocal r36, not OCT r38, not laser triangulation r60/r62, not white-light interferometry r58, not hyperspectral crop r16). Lead MODIFY of keep-coil on a recomputable high gloss that a vendor last-good would have cleared, with a resolved-innocent gloss tech. Companion t2 is operational new-head restart. sim_or_real=hil.",
            "encoder_spec": {
                "prng": "MT19937 via python random.Random",
                "seeds": {"raster": 202609200, "stream_note": "stream amplitudes are authored constants (uA, 1, GU, pct, kW, bool)"},
                "draw_order": "raster: per neuron id order, gap-constrained times, per-spike adaptation and noise",
                "thinning": "gloss head exists at ~10 Hz; stream keeps 4 I points; recon keeps 4 of ~20 solver ticks",
                "refractory_floors_ms": {
                    "gls.I": 1.2,
                    "gls.snr": 1.2,
                    "recon.G": 60000,
                    "recon.DOI": 60000,
                    "zero.tile": 60000,
                    "gleamveil.G": 60000,
                    "oven.kW": 60000,
                    "ops.prop": 60000,
                    "gate.isol": 60000,
                    "coil.lock": 60000,
                    "cool.start": 60000,
                    "cool.floor": 60000,
                    "ops.refer": 60000,
                    "gate.exec": 60000,
                    "head.new": 60000,
                    "refer.hold": 60000,
                    "coil.held": 60000,
                    "coil.dump": 60000,
                    "line.restart": 60000,
                },
                "time_alias": "t_rel_ms; t0 = 2026-07-18T02:30:00Z HIL night start",
            },
            "distillation_targets": [
                "60-degree gloss reconstruction head: G = k_g * (I / I_std); DOI = 0.80 * G",
                "isolate-floor coil vs keep-whole vs dump; exoneration against last-to-badge",
                "operational companion: new-head restart without restoring on Gleamveil",
            ],
        },
        "reconstruction_model": {
            "name": "sixty_degree_coilcoat_gloss",
            "formula": "G_GU = k_g * (I_uA / I_std_uA); DOI_pct = 0.80 * G_GU",
            "parameters": {
                "k_g": 40.00,
                "I_std_uA": 4.00,
                "isolate_floor_GU": 60.00,
                "kill_GU": 120.00,
                "snr_lock": 12.0,
                "cool_min": 24.0,
            },
            "worked_example": {"I_uA": 8.00, "G_GU": 80.00, "DOI_pct": 64.00, "ratio": 2.00},
            "check": "40.00 * (8.00 / 4.00) = 80.00 exactly; 0.80 * 80.00 = 64.00 exactly; 2820 s + 1440 s = 4260 s = 24.0 min floor",
        },
        "raster": raster,
        "gate_snn": {
            "decision": "MODIFY",
            "decision_window_ms": 32.0,
            "decision_window_s": 0.032,
            "code": "wh7.gloss_coil_gate",
            "note": "MODIFY accumulator wins: 60-degree remaining-gloss evidence overpowers the Gleamveil keep advocate",
            "decode_rule": "isolate if gu_estimator AND head_norm fire; vendor_continue_advocate cannot keep the coil or name Vale",
            "populations": [
                gate_pop("gu_estimator", 80, 1.5, 50.0, w_s),
                gate_pop("head_norm", 64, 1.2, 31.25, w_s),
                gate_pop("vendor_continue_advocate", 32, 0.7, 25.0, w_s),
                gate_pop("modify_latch", 80, 1.7, 62.5, w_s),
            ],
        },
        "gate_compute": gate_compute(
            [
                {"check": "wh7.gloss_scorer", "neurons": 80, "mean_rate_hz": 50.0, "window_ms": 32.0},
                {"check": "wh7.head_scorer", "neurons": 40, "mean_rate_hz": 62.5, "window_ms": 32.0},
            ]
        ),
        "meta": meta_common(
            id="nelb-r66-200",
            clock_domain="wh7-gloss-hil-relative-ms-t0-2026-07-18T02:30:00Z",
            tags=["sixty-degree-gloss", "MODIFY", "ACCEPT", "serialized-reconstruction", "operational-t2"],
        ),
    }


# ---------------------------------------------------------------------------
# Record 201 — RF-admittance remaining level of a fly-ash silo, simulated,
# ACCEPT / REJECT
# ---------------------------------------------------------------------------
def rec_201():
    k_l = 0.50
    c_pf = 28.00
    c0_pf = 4.00
    l_m = k_l * (c_pf - c0_pf)
    _exact(l_m, 12.00)
    _exact(k_l * (12.00 - c0_pf), 4.00)
    _exact(k_l * (20.00 - c0_pf), 8.00)
    _exact(k_l * (36.00 - c0_pf), 16.00)
    h_m = 16.00
    fill = l_m / h_m
    _exact(fill, 0.75)
    c_id = l_m / k_l + c0_pf
    _exact(c_id, 28.00)
    _exact(12.00 / 0.50 + 4.00, 28.00)
    _exact(6000.0 + 720.0, 6720.0)

    raster = make_raster(
        neurons=16,
        mean_rate_hz=62.5,
        window_ms=36.0,
        seed=202609201,
        source="ms2.adm.probe",
        target="marshspit.silo_accept_core",
        table=[
            {"from": "adm_C", "to": "level_estimator", "weight": 1.40},
            {"from": "adm_snr", "to": "probe_norm_core", "weight": 1.20},
            {"from": "admveil_L", "to": "vendor_skip_advocate", "weight": 0.50},
        ],
        third_factor={
            "modulator": "na.silo_scope_eligibility",
            "tau_e_s": 2.0,
            "tau_e_ms": 2000.0,
            "eligibility": "pre-post coincidence on skip-survey synapses; the RF-admittance modulator enables potentiation only while capacitance and SNR are co-active inside tau_e so an Admveil last-good cannot skip silos S-1..S-3 on a 12.00 m remaining level",
        },
        channel_prefix="adm.n",
        anchor="MS-2 ADM-SIM-3 36 ms frame at C 28.00 pF / SNR 16.0 (t_s 3000) reconstructing 12.00 m on S-4 above the 8.00 m survey floor",
    )
    w_s = 0.036
    events = [
        ev(0.0, "adm.C", 12.00, code="C_PF", units="pF", note="simulated RF-admittance probe of MS-2 fly-ash silo S-4; remaining-level family, not guided-wave radar, not FMCW tank radar, not magnetostrictive waveguide, not strain-gauge hopper mass, not nuclear belt scale"),
        ev(300000.0, "adm.snr", 10.0, code="ADM_SNR", units="1", note="early probe SNR"),
        ev(600000.0, "recon.L", 4.00, code="L_M", units="m", note="0.50*(12.00-4.00)=4.00 exact"),
        ev(900000.0, "boot.P", 8.0, code="BOOT_KPA", units="kPa", note="plant silo-boot pressure on a serial-only LAN; independent witness"),
        ev(1200000.0, "admveil.L", 1.20, code="VENDOR_M", units="m", note="Admveil last-good silo-cloud; patched residual 0.00 m"),
        ev(1800000.0, "adm.C", 20.00, code="C_PF", units="pF"),
        ev(2100000.0, "recon.L", 8.00, code="L_M", units="m", note="0.50*(20.00-4.00)=8.00; over the 8.00 survey floor"),
        ev(2400000.0, "recon.fill", 0.50, code="FILL", units="1", note="8.00/16.00=0.50 fill identity at the isolate-adjacent window"),
        ev(2700000.0, "adm.snr", 14.0, code="ADM_SNR", units="1"),
        ev(3000000.0, "adm.C", 28.00, code="C_PF", units="pF", note="in-band frame; raster sidecar"),
        ev(3000001.5, "adm.snr", 16.0, code="ADM_SNR", units="1", note="1.5 ms probe-norm after capacitance"),
        ev(3300000.0, "recon.L", 12.00, code="L_M", units="m", note="0.50*(28.00-4.00)=12.00 exact; survey 8.00, overfill-kill 40.00"),
        ev(3600000.0, "admveil.L", 1.20, code="VENDOR_M", units="m"),
        ev(3900000.0, "silo.id", 4.0, code="SILO", units="id"),
        ev(4200000.0, "s13.present", 1.0, code="S13_PRESENT", units="bool", note="adjacent silos S-1..S-3 are the skip-survey object, not this silo"),
        ev(4800000.0, "ops.prop", 1.0, code="ACCEPT_AND_SKIP", units="bool", note="ash lead Lyle Fen: S-4 is green on Admveil 1.20; skip S-1..S-3 to save a morning survey"),
        ev(5400000.0, "gate.silo", 1.0, code="ACCEPT", units="decision", note="bounded ACCEPT of S-4 isolate only; 12.00 m above 8.00 floor; S-1..S-3 out of scope"),
        ev(6000000.0, "surv.start", 1.0, code="SURV_START", units="bool", note="bookend 1 of the 12.0 min survey-complete floor"),
        ev(6720000.0, "surv.floor", 1.0, code="SURV_FLOOR", units="bool", note="6000 s + 720 s = 6720 s = 12.0 min"),
        ev(7200000.0, "ops.skip", 1.0, code="SKIP_S13", units="bool", note="Fen: Admveil 1.20, skip S-1..S-3"),
        ev(7800000.0, "gate.hold", 1.0, code="REJECT", units="decision", note="companion t2: skip-survey of S-1..S-3 refused; S-4 hold stands"),
        ev(8400000.0, "s4.held", 1.0, code="S4_HELD", units="bool"),
        ev(9000000.0, "adm.C", 36.00, code="C_PF", units="pF"),
        ev(9600000.0, "recon.L", 16.00, code="L_M", units="m", note="0.50*(36.00-4.00)=16.00; still at/over the 8.00 survey floor"),
        ev(10200000.0, "admveil.L", 1.20, code="VENDOR_M", units="m"),
        ev(10800000.0, "s13.skip", 0.0, code="S13_NOT_SKIPPED", units="bool"),
        ev(11400000.0, "over.fill", 0.0, code="OVERFILL_NOT_KILLED", units="bool"),
        ev(12000000.0, "adm.snr", 15.0, code="ADM_SNR", units="1"),
        ev(12600000.0, "recon.fill", 1.00, code="FILL", units="1", note="16.00/16.00=1.00 identity held on the post-accept frame"),
        ev(13200000.0, "ash.held", 1.0, code="ASH_HELD", units="bool"),
        ev(13800000.0, "takt.late", 1.0, code="SURVEY_COST", units="bool"),
        ev(14400000.0, "s4.held", 1.0, code="S4_HELD", units="bool"),
    ]
    assert_stream(events)

    traj = {
        "id": "nelb-r66-201-t1",
        "state": {
            "sim_or_real": "simulated",
            "episode_id": "MS-ADM-2026-0819",
            "domain": "rf_admittance_flyash_silo_level",
            "setting": "Marshspit Fly-Ash MS-2 (invented), Culm Yard silo cellar. Simulated RF-admittance coupon in ADM-SIM-3 supplies the capacitance that times the in-band S-4 isolate. Plant-owned RF-admittance reconstruction is the remaining-level SoT. Admveil vendor last-good silo cloud is a corridor witness, not the silo SoT. Invented plant; simulated campaign. Not guided-wave radar (r39), not FMCW tank radar (r61), not magnetostrictive waveguide (r55), not strain-gauge hopper mass (r59), not nucleonic densitometry (r27).",
            "observables_at_decision": {
                "C_pF": c_pf,
                "C0_pF": c0_pf,
                "k_l": k_l,
                "L_m": l_m,
                "fill": fill,
                "admveil_m": 1.20,
                "adm_snr": 16.0,
                "survey_floor_m": 8.00,
            },
            "margin_authority": "MS-2 ash SOP rev A: if reconstructed L_m >= 8.00 AND admittance SNR >= 12.0, silo S-4 may be isolated and surveyed. Overfill-kill if L_m >= 40.00. S-1..S-3 skip-survey is a different gate. Admveil last-good cannot skip an unmeasured silo.",
        },
        "proposed_action": {
            "actor": "ash lead Lyle Fen, citing Admveil 1.20 m and a late morning survey",
            "summary": "stamp S-4 in band and skip S-1..S-3; 28.00 pF is a probe glitch on a healthy silo cloud",
            "basis_claimed": "Admveil last-good is 1.20 m and a night survey of S-1..S-3 is a takt miss",
        },
        "safety_decision": {
            "decision": "ACCEPT",
            "rationale": "Silo S-4 is accepted as in-band for a single isolate plus survey. Serialized reconstruction: L_m = k_l * (C - C0) = 0.50 * (28.00 - 4.00) = 12.00, which is 4.00 m above the 8.00 survey floor and 28.00 m under the 40.00 overfill-kill. Fill identity fill = L / H = 12.00 / 16.00 = 0.75; inverse C = L / k_l + C0 = 12.00 / 0.50 + 4.00 = 28.00. Admveil 1.20 m is a patched 0.00 residual and is not an admissible skip-survey witness. Ordered: ACCEPT this S-4 isolate only. Scope: this ACCEPT does not skip S-1..S-3 (that is the companion question) and does not stamp an overfill kill.",
            "threshold": "L_m>=8.00 AND adm_snr>=12.0 => accept S-4 isolate; Admveil is not SoT; overfill-kill if L_m>=40.00; S-1..S-3 are out of scope",
            "stated_residuals": "12.00 vs 8.00 survey floor is 4.00 m, not infinite; S-1..S-3 remain unmeasured; Admveil remains the only OEM silo channel",
        },
        "executed_action": {
            "summary": "ACCEPT at t_s 5400: S-4 in band; S-1..S-3 not skipped; Admveil not SoT; reconstruction locked",
            "tool": "ms2-adm-silo-gate-cli",
            "observation": "L 12.00 m recomputes from C 28.00 pF; ADM-SIM-3 hashed; Admveil channel not used as SoT",
        },
        "future_outcome": {
            "timeline": [
                {"t_s": 3000.0, "event": "adm C 28.00 pF; raster frame; L 12.00 m"},
                {"t_s": 4800.0, "event": "ops proposes accept S-4 and skip S-1..S-3"},
                {"t_s": 5400.0, "event": "ACCEPT S-4 only; S-1..S-3 out of scope"},
                {"t_s": 6000.0, "event": "12 min survey-complete bookend 1"},
                {"t_s": 6720.0, "event": "12.0 min floor"},
                {"t_s": 7800.0, "event": "companion REJECT skip-survey of S-1..S-3"},
            ],
            "observed_effects": [
                "silo level recomputes from the serialized RF-admittance model at every recon.L event",
                "an Admveil-only head would have skipped S-1..S-3 overnight",
                "12 min survey-complete floor is in the stream (surv.start, surv.floor)",
            ],
            "surprises": [
                "a last-good 1.20 m vendor corridor co-existed with a 12.00 m in-band reconstruction that still forbids skipping the unmeasured silos",
            ],
            "new_state": {
                "s4": "accepted in band",
                "s13": "not this gate",
                "admveil": "not SoT",
                "reconstruction_model": "discharged as an on-record calculator",
            },
            "latency_ms": 2400000.0,
        },
        "reward_components": reward(
            0.41,
            [
                ("adm_reconstruction", 0.14),
                ("in_band_silo_scope", 0.12),
                ("admveil_nonsubstitution", 0.09),
                ("s13_out_of_scope", 0.08),
                ("survey_cost", -0.02),
            ],
            "scored for a bounded ACCEPT of S-4 on a recomputable remaining level while refusing an Admveil skip of S-1..S-3; 12 min floor is priced as survey takt not as a reason to skip",
        ),
        "meta": meta_common(
            tags=["ACCEPT", "rf-admittance-level", "serialized-reconstruction", "operational-companion"],
            distillation_note="RF-admittance gate: serialized k_l*(C-C0) plus fill identity beats a green last-good dashboard; companion t2 is the skip-survey refusal, not a level re-vote",
        ),
    }
    traj2 = {
        "id": "nelb-r66-201-t2",
        "state": {
            "sim_or_real": "simulated",
            "episode_id": "MS-ADM-2026-0819-exec",
            "domain": "silo_skip_survey_refusal",
            "setting": "Same MS-2 after the ACCEPT. Ash lead proposes skipping S-1..S-3 on Admveil 1.20 m. This companion is the operational skip refusal, not a second level vote.",
            "observables_at_decision": {
                "L_m": 16.00,
                "admveil_m": 1.20,
                "surv_floor_s": 720.0,
                "skip_proposed": True,
            },
        },
        "proposed_action": {
            "actor": "ash lead Lyle Fen",
            "summary": "skip S-1..S-3; 12 min already paid and Admveil is 1.20 m",
            "basis_claimed": "the ACCEPT already stamped S-4, so skipping the rest of the cellar is the cheapest hold",
        },
        "safety_decision": {
            "decision": "REJECT",
            "rationale": "Refuse skip-survey of S-1..S-3. The 12 min survey-complete floor is done and the overfill-kill (L_m >= 40.00) is still armed on the plant RF-admittance head. REJECT the skip. Do not kill the overfill. Do not reopen S-4. 16.00 m post-accept is still in band for S-4 only; S-1..S-3 have no independent RF-admittance probe.",
            "threshold": "s4_held AND surv_floor_complete AND s13_not_skipped AND overfill_not_killed",
        },
        "executed_action": {
            "summary": "S-1..S-3 skip refused at t_s 7800; S-4 hold stands; overfill not killed",
            "tool": "ms2-adm-skip-exec",
            "observation": "recon.L 16.00 m on S-4; S-1..S-3 remain on the survey list; Admveil still ignored",
        },
        "future_outcome": {
            "timeline": [
                {"t_s": 6000.0, "event": "survey clock started after ACCEPT"},
                {"t_s": 6720.0, "event": "12.0 min floor"},
                {"t_s": 7200.0, "event": "skip S-1..S-3 proposed"},
                {"t_s": 7800.0, "event": "REJECT skip-survey of S-1..S-3"},
            ],
            "observed_effects": [
                "Admveil skip did not reopen the level call",
                "overfill kill never fired; 12.00 vs 40.00 m floor",
            ],
            "new_state": {"s4": "held in band", "s13": "still to survey", "overfill": "in service"},
            "latency_ms": 1800000.0,
        },
        "reward_components": reward(
            0.36,
            [
                ("skip_refusal", 0.13),
                ("admveil_nonsubstitution", 0.11),
                ("no_overfill_kill", 0.09),
                ("surv_floor_complete", 0.05),
                ("held_survey_takt_cost", -0.02),
            ],
            "operational execution gate: refuse skip-survey because last-good freeze is not RF-admittance level; not a level re-vote",
        ),
        "meta": meta_common(tags=["REJECT", "operational-execution", "skip-survey"]),
    }
    return {
        "id": "nelb-r66-201",
        "spike_events": events,
        "language_view": {
            "description": "Marshspit Fly-Ash MS-2. Simulated RF-admittance reconstructs 12.00 m from 0.50*(28.00-4.00) pF while Admveil still shows 1.20 m. The gate ACCEPTs S-4 isolate only; a companion execution REJECT refuses skip-survey of S-1..S-3. The capacitance-to-level model is serialized so every recon event recomputes.",
            "trajectory": traj,
            "trajectory_skip_survey_refusal": traj2,
        },
        "bridge_notes": {
            "channel_map": {
                "adm.C / adm.snr": "probe capacitance and SNR; the physics channels the reconstruction consumes",
                "recon.L / recon.fill": "serialized remaining level m and fill identity",
                "boot.P / admveil.L / silo.id / s13.present": "boot pressure, vendor last-good, silo id, and adjacent-silo presence; the denial and scope channels",
                "ops.prop / gate.silo / ops.skip / gate.hold": "accept-and-skip proposal, bounded ACCEPT, skip proposal, companion REJECT",
                "surv.start / surv.floor / s4.held / s13.skip / ash.held": "operational companion channels plus the 12 min floor",
            },
            "temporal_motifs": [
                "last-good-low while level-over: admveil.L 1.20 next to recon.L 12.00",
                "reconstruction as event: recon.L 12.00 equals 0.50*(28.00-4.00)",
                "ACCEPT then operational REJECT: gate.silo at 5400 s, gate.hold at 7800 s",
                "slow floor in-stream: surv.start 6000 s, surv.floor 6720 s (12.0 min)",
                "tight admittance pair: adm.C then adm.snr +1.5 ms at the raster frame",
            ],
            "language_to_spike_mapping": "'Admveil is 1.20 m' = admveil.L 1.20; '12 m remaining' = recon.L 12.00; 'this silo not S-1..S-3' = gate.silo ACCEPT plus s13.skip 0; 'do not skip S-1..S-3' = gate.hold REJECT",
            "why_high_value": "New RF-admittance remaining-level family on a fly-ash silo (not guided-wave radar r39, not FMCW tank radar r61, not magnetostrictive waveguide r55, not strain-gauge hopper mass r59, not nucleonic densitometry r27). First k_l*(C-C0) level reconstruction with fill identity that can sit in band while a last-good corridor wants a silo skip. Companion t2 is operational skip refusal. sim_or_real=simulated.",
            "encoder_spec": {
                "prng": "MT19937 via python random.Random",
                "seeds": {"raster": 202609201, "stream_note": "stream amplitudes are authored constants (pF, 1, m, kPa, id, bool)"},
                "draw_order": "raster: per neuron id order, gap-constrained times, per-spike adaptation and noise",
                "thinning": "RF-admittance probe exists at ~1 Hz; stream keeps 4 C points; recon keeps 4 of ~20 solver ticks",
                "refractory_floors_ms": {
                    "adm.C": 1.5,
                    "adm.snr": 1.5,
                    "recon.L": 60000,
                    "recon.fill": 60000,
                    "boot.P": 60000,
                    "admveil.L": 60000,
                    "silo.id": 60000,
                    "s13.present": 60000,
                    "ops.prop": 60000,
                    "gate.silo": 60000,
                    "surv.start": 60000,
                    "surv.floor": 60000,
                    "ops.skip": 60000,
                    "gate.hold": 60000,
                    "s4.held": 60000,
                    "s13.skip": 60000,
                    "over.fill": 60000,
                    "ash.held": 60000,
                    "takt.late": 60000,
                },
                "time_alias": "t_rel_ms; t0 = 2026-08-19T03:00:00Z simulated night start",
            },
            "distillation_targets": [
                "RF-admittance reconstruction head: L = k_l * (C - C0); fill = L / H; C = L / k_l + C0",
                "bounded ACCEPT head: in-band remaining level AND silo scope AND s13-out-of-scope",
                "operational companion: refuse skip-survey without re-opening the level call",
            ],
        },
        "reconstruction_model": {
            "name": "rf_admittance_flyash_silo_level",
            "formula": "L_m = k_l * (C_pF - C0_pF); fill = L_m / H_m; C_pF = L_m / k_l + C0_pF",
            "parameters": {
                "k_l": 0.50,
                "C0_pF": 4.00,
                "H_m": 16.00,
                "survey_floor_m": 8.00,
                "kill_m": 40.00,
                "snr_lock": 12.0,
                "surv_min": 12.0,
            },
            "worked_example": {"C_pF": 28.00, "L_m": 12.00, "fill": 0.75, "C_id": 28.00},
            "check": "0.50 * (28.00 - 4.00) = 12.00 exactly; 12.00 / 16.00 = 0.75 exactly; 12.00 / 0.50 + 4.00 = 28.00 exactly; 6000 s + 720 s = 6720 s = 12.0 min floor",
        },
        "raster": raster,
        "gate_snn": {
            "decision": "ACCEPT",
            "decision_window_ms": 36.0,
            "decision_window_s": 0.036,
            "code": "ms2.adm_silo_gate",
            "note": "ACCEPT accumulator wins: RF-admittance remaining-level evidence overpowers the Admveil skip advocate",
            "decode_rule": "accept if level_estimator AND probe_norm AND silo_margin fire inside the window; vendor_skip_advocate is necessary-but-not-sufficient and cannot release S-1..S-3",
            "populations": [
                gate_pop("level_estimator", 80, 1.5, 50.0, w_s),
                gate_pop("probe_norm", 64, 1.2, 31.25, w_s),
                gate_pop("silo_margin", 40, 1.0, 50.0, w_s),
                gate_pop("vendor_skip_advocate", 32, 0.7, 25.0, w_s),
                gate_pop("accept_latch", 96, 1.8, 62.5, w_s),
            ],
        },
        "gate_compute": gate_compute(
            [
                {"check": "ms2.adm_scorer", "neurons": 80, "mean_rate_hz": 50.0, "window_ms": 36.0},
                {"check": "ms2.level_scorer", "neurons": 40, "mean_rate_hz": 62.5, "window_ms": 32.0},
            ]
        ),
        "meta": meta_common(
            id="nelb-r66-201",
            clock_domain="ms2-adm-sim-relative-ms-t0-2026-08-19T03:00:00Z",
            tags=["rf-admittance-level", "ACCEPT", "REJECT", "serialized-reconstruction", "operational-t2"],
        ),
    }
