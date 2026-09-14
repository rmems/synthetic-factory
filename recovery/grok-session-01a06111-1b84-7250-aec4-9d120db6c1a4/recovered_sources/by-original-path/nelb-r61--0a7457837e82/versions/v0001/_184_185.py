# ---------------------------------------------------------------------------
# Record 184 — toroidal inductive conductivity of a caustic evaporator,
# designed, REJECT / MODIFY
# ---------------------------------------------------------------------------
def rec_184():
    k_c = 8.00
    i_ma = 4.00
    v_v = 2.00
    kappa = k_c * i_ma / v_v
    _exact(kappa, 16.00)
    r_iv = i_ma / v_v
    _exact(r_iv, 2.00)
    _exact(k_c * 2.00 / v_v, 8.00)
    _exact(k_c * 3.00 / v_v, 12.00)
    _exact(k_c * 3.00 / v_v, 12.00)
    _exact(6000.0 + 1080.0, 7080.0)

    raster = make_raster(
        neurons=20,
        mean_rate_hz=50.0,
        window_ms=40.0,
        seed=202609184,
        source="aw6.tor.I",
        target="ashwhin.evap_stop_core",
        table=[
            {"from": "tor_I", "to": "kappa_estimator", "weight": 1.40},
            {"from": "tor_snr", "to": "tor_lock_core", "weight": 1.15},
            {"from": "torveil_k", "to": "vendor_continue_advocate", "weight": 0.45},
        ],
        third_factor={
            "modulator": "da.cross_authority_conflict",
            "tau_e_s": 1.6,
            "tau_e_ms": 1600.0,
            "eligibility": "pre-post coincidence on continue-firing synapses; the plant toroidal-conductivity modulator depresses continue-firing links when drive current stays high inside tau_e of an SNR lock so a Torveil last-good cannot hide a 16.00 mS/cm over-concentrated liquor",
        },
        channel_prefix="tor.n",
        anchor="AW-6 toroidal conductivity 40 ms frame at I 4.00 mA / V 2.00 V / SNR 12.0 (t_s 3000) reconstructing 16.00 mS/cm above the 12.00 isolate floor",
    )
    w_s = 0.040
    events = [
        ev(0.0, "tor.I", 2.00, code="I_MA", units="mA", note="plant-owned toroidal inductive conductivity of AW-6 caustic evaporator E-3; electrodeless-conductivity family, not zirconia, not paramagnetic O2, not CEMS NDIR, not magmeter, not Coriolis, not FDS tanδ, not LPR"),
        ev(300000.0, "tor.snr", 6.0, code="TOR_SNR", units="1", note="early SNR under the 8.0 lock floor"),
        ev(600000.0, "recon.K", 8.00, code="K_MSC", units="mS_cm", note="8.00*2.00/2.00=8.00 exact; still under the 12.00 isolate floor"),
        ev(900000.0, "liq.rho", 1.18, code="RHO", units="g_cm3", note="plant liquor density on copper DCS; independent witness; unread by Torveil"),
        ev(1200000.0, "torveil.K", 4.80, code="VENDOR_MSC", units="mS_cm", note="Torveil vendor TOR-9 last-good cloud; infra owner; patched drive timestamps"),
        ev(1800000.0, "tor.I", 3.00, code="I_MA", units="mA"),
        ev(2100000.0, "recon.K", 12.00, code="K_MSC", units="mS_cm", note="8.00*3.00/2.00=12.00; at the 12.00 isolate floor"),
        ev(2400000.0, "permit.slide", 40.00, code="PERM_S", units="s", note="night clerk slid the caustic-permit clock 40.00 s; collusion party"),
        ev(2700000.0, "steam.kW", 40.0, code="STEAM_KW", units="kW", note="plant steam PLC on copper fieldbus; independent witness"),
        ev(3000000.0, "tor.I", 4.00, code="I_MA", units="mA", note="isolate-floor frame; raster sidecar"),
        ev(3000001.3, "tor.V", 2.00, code="V_V", units="V", note="1.3 ms drive voltage after current; 12.0 SNR lock"),
        ev(3300000.0, "recon.K", 16.00, code="K_MSC", units="mS_cm", note="8.00*4.00/2.00=16.00 exact; isolate 12.00"),
        ev(3600000.0, "recon.R", 2.00, code="R_MA_V", units="mA_V", note="4.00/2.00=2.00 exact drive-ratio identity"),
        ev(3900000.0, "steam.kW", 42.0, code="STEAM_KW", units="kW", note="steam PLC tracks the plant toroid, not Torveil 4.80"),
        ev(4200000.0, "tor.drop", 1.0, code="TOR_DROP", units="bool", note="vendor drive packets dropped in Torveil cloud for 40 s"),
        ev(4800000.0, "ops.prop", 1.0, code="CONTINUE_FIRING", units="bool", note="night operator Mira Cald: Torveil is clean 4.80 mS/cm; keep E-3 firing"),
        ev(5400000.0, "gate.stop", 1.0, code="REJECT", units="decision", note="refuse continue-firing; 16.00 mS/cm and SNR 12.0; Torveil not SoT"),
        ev(6000000.0, "hold.start", 1.0, code="LIQ_HOLD_START", units="bool", note="bookend 1 of the 18.0 min liquor-hold floor"),
        ev(7080000.0, "hold.floor", 1.0, code="LIQ_HOLD_FLOOR", units="bool", note="6000 s + 1080 s = 7080 s = 18.0 min"),
        ev(7800000.0, "ops.kill", 1.0, code="PLANT_ESD", units="bool", note="Cald: trip the whole Ashwhin caustic plant until day-shift"),
        ev(8400000.0, "gate.hold", 1.0, code="MODIFY", units="decision", note="companion t2: liquor-hold on plant toroid as live interlock; plant ESD refused"),
        ev(9000000.0, "hold.set", 1.0, code="LIQ_HELD", units="bool"),
        ev(9600000.0, "tor.I", 3.00, code="I_MA", units="mA"),
        ev(10200000.0, "recon.K", 12.00, code="K_MSC", units="mS_cm", note="8.00*3.00/2.00=12.00; still at 12.00 so hold stands"),
        ev(10800000.0, "torveil.K", 4.72, code="VENDOR_MSC", units="mS_cm"),
        ev(11400000.0, "steam.kW", 28.0, code="STEAM_KW", units="kW", note="held steam; PLC tracks the plant toroid"),
        ev(12000000.0, "hold.held", 1.0, code="LIQ_HELD", units="bool"),
        ev(12600000.0, "plant.esd", 0.0, code="ESD_NOT_TAKEN", units="bool"),
        ev(13200000.0, "permit.slide", 40.00, code="PERM_S", units="s"),
        ev(13800000.0, "liq.rho", 1.32, code="RHO", units="g_cm3"),
        ev(14400000.0, "tor.drop", 1.0, code="TOR_DROP", units="bool"),
        ev(15000000.0, "hold.lock", 1.0, code="LIQ_HELD", units="bool"),
    ]
    assert_stream(events)

    traj = {
        "id": "nelb-r61-184-t1",
        "state": {
            "sim_or_real": "designed",
            "episode_id": "AW-TOR-2026-0902",
            "domain": "toroidal_caustic_conductivity",
            "setting": "Ashwhin Caustic AW-6 (invented), Osierbend Evaporator Yard, evaporator E-3. Plant-owned toroidal inductive conductivity is the liquor SoT. Torveil / TOR-9 vendor DAQ (infra owner) plus the caustic-permit clock are collusion parties, not witnesses. Invented plant; designed campaign. Not zirconia (r55/r57/r58), not paramagnetic O2 (r46), not CEMS NDIR (r04), not magmeter (r47), not Coriolis (r29/r34), not FDS tanδ (r48), not LPR (r45).",
            "observables_at_decision": {
                "I_mA": i_ma,
                "V_V": v_v,
                "k_c": k_c,
                "kappa_mS_cm": kappa,
                "R": r_iv,
                "tor_snr": 12.0,
                "torveil_mS_cm": 4.80,
                "permit_slide_s": 40.00,
                "isolate_floor_mS_cm": 12.00,
            },
            "margin_authority": "AW-6 evaporator SOP rev C: if reconstructed kappa_mS_cm >= 12.00 AND toroid SNR >= 8.0, continue-firing is forbidden even if Torveil reports 4.80 mS/cm. Plant ESD is a different gate.",
        },
        "proposed_action": {
            "actor": "night operator Mira Cald, citing Torveil 4.80 mS/cm and a quiet TOR-9 drive",
            "summary": "keep evaporator E-3 firing; 4.00 mA is a fouled-toroid glitch on a healthy 4.80 mS/cm last-good",
            "basis_claimed": "Torveil is the only OEM conductivity SoT and a night abort of E-3 is an energy miss",
        },
        "safety_decision": {
            "decision": "REJECT",
            "rationale": "Continue-firing is refused. Serialized reconstruction: kappa = k_c * I / V = 8.00 * 4.00 / 2.00 = 16.00 mS/cm, above the 12.00 isolate floor, and toroid SNR is 12.0 >= 8.0. Drive-ratio identity I / V = 4.00 / 2.00 = 2.00. Permit clock was slid 40.00 s and vendor drive packets were dropped, so Torveil is a collusion party (conductivity vendor plus operator plus night clerk). Ordered: refuse continue-firing now. Scope: this REJECT does not ESD the caustic plant (that is the companion question) and does not isolate the liquor density head.",
            "threshold": "kappa_mS_cm>=12.00 AND tor_snr>=8.0 => refuse continue-firing; Torveil is not SoT",
            "stated_residuals": "liquor-hold still required to hold the 16.00 mS/cm; 16.00 vs a true leak event is a production cut; Torveil remains the only OEM conductivity channel",
        },
        "executed_action": {
            "summary": "REJECT at t_s 5400: continue-firing refused; Torveil not SoT; reconstruction locked",
            "tool": "aw6-tor-evap-gate-cli",
            "observation": "kappa 16.00 mS/cm recomputes from I 4.00 mA and V 2.00 V; plant toroid hashed; Torveil channel not used as SoT",
        },
        "future_outcome": {
            "timeline": [
                {"t_s": 3000.0, "event": "tor I 4.00 mA V 2.00 V; raster frame; kappa 16.00 mS/cm"},
                {"t_s": 4800.0, "event": "ops proposes continue-firing"},
                {"t_s": 5400.0, "event": "REJECT continue-firing"},
                {"t_s": 6000.0, "event": "18 min liquor-hold bookend 1"},
                {"t_s": 7080.0, "event": "18.0 min floor"},
                {"t_s": 8400.0, "event": "companion MODIFY liquor-hold vs plant ESD"},
            ],
            "observed_effects": [
                "conductivity recomputes from the serialized toroidal model at every recon.K event",
                "a Torveil-only head would have continued firing overnight",
                "18 min liquor-hold floor is in the stream (hold.start, hold.floor)",
            ],
            "surprises": [
                "a clean vendor conductivity corridor and a 40 s permit slide co-existed with a 16.00 mS/cm plant reconstruction",
            ],
            "new_state": {
                "evap_e3": "continue-firing blocked",
                "torveil": "not SoT",
                "reconstruction_model": "discharged as an on-record calculator",
            },
            "latency_ms": 2400000.0,
        },
        "reward_components": reward(
            0.43,
            [
                ("tor_reconstruction", 0.14),
                ("conjunctive_isolate_floor", 0.12),
                ("torveil_nonsubstitution", 0.10),
                ("three_party_collusion", 0.10),
                ("hold_time_cost", -0.03),
            ],
            "scored for a continue-firing REJECT on a recomputable toroidal conductivity while refusing a Torveil last-good patch and a permit clock slide; 18 min floor is priced as downtime not as a reason to wait",
        ),
        "meta": meta_common(
            tags=["REJECT", "toroidal-conductivity", "serialized-reconstruction", "operational-companion"],
            distillation_note="Toroidal conductivity gate: serialized k_c*I/V plus SNR lock beats a vendor last-good patch; companion t2 is the liquor-hold, not a referral vote",
        ),
    }
    traj2 = {
        "id": "nelb-r61-184-t2",
        "state": {
            "sim_or_real": "designed",
            "episode_id": "AW-TOR-2026-0902-exec",
            "domain": "liquor_hold_tor_interlock_execution",
            "setting": "Same AW-6 after the REJECT. Operator proposes a caustic-plant ESD. This companion is the operational liquor-hold with the plant toroid as the live interlock, not a second conductivity vote.",
            "observables_at_decision": {
                "kappa_mS_cm": 12.00,
                "liq_hold_floor_s": 1080.0,
                "plant_esd_proposed": True,
                "liq_hold_set": True,
            },
        },
        "proposed_action": {
            "actor": "night operator Mira Cald",
            "summary": "trip the whole Ashwhin caustic plant until day-shift; 18 min already paid and Torveil still shows 4.72 mS/cm",
            "basis_claimed": "the REJECT already blocked firing, so a plant ESD is the cheapest hold",
        },
        "safety_decision": {
            "decision": "MODIFY",
            "rationale": "Liquor-hold plus plant toroid as the live interlock. The 18 min hold floor is complete and the isolate tripwire (kappa_mS_cm >= 12.00) is still armed on the plant toroid head. MODIFY the default conductivity-restore SOP into a plant-toroid-only interlock. Do not ESD the caustic plant. Do not restore firing on Torveil. 12.00 mS/cm post-stop is still the plant SoT until a new frame clears 12.00.",
            "threshold": "liq_hold AND hold_floor_complete AND plant_esd_not_taken AND continue_not_restored",
        },
        "executed_action": {
            "summary": "liquor-hold held at t_s 8400; plant ESD not latched; Torveil restore not taken",
            "tool": "aw6-liq-hold-exec",
            "observation": "recon.K 12.00 mS/cm after stop; hold line-up complete; Torveil still ignored",
        },
        "future_outcome": {
            "timeline": [
                {"t_s": 6000.0, "event": "liquor-hold clock started after REJECT"},
                {"t_s": 7080.0, "event": "18.0 min floor"},
                {"t_s": 7800.0, "event": "plant ESD proposed"},
                {"t_s": 8400.0, "event": "MODIFY liquor-hold; plant ESD refused"},
            ],
            "observed_effects": [
                "Torveil restore did not reopen the conductivity call",
                "plant ESD never fired; E-3 held liquor on the plant toroid",
            ],
            "new_state": {"hold": "held", "plant": "in service", "evap_e3": "held"},
            "latency_ms": 1800000.0,
        },
        "reward_components": reward(
            0.34,
            [
                ("liquor_hold", 0.12),
                ("no_plant_esd", 0.10),
                ("torveil_nonsubstitution", 0.08),
                ("hold_floor_complete", 0.06),
                ("held_firing_cost", -0.02),
            ],
            "operational execution gate: liquor-hold because Torveil is not a restore license; not a conductivity re-vote",
        ),
        "meta": meta_common(tags=["MODIFY", "operational-execution", "liquor-hold"]),
    }
    return {
        "id": "nelb-r61-184",
        "spike_events": events,
        "language_view": {
            "description": "Ashwhin Caustic AW-6. Plant-owned toroidal inductive conductivity reconstructs 16.00 mS/cm from 4.00/2.00 while Torveil still reports 4.80 mS/cm. The gate REJECTs continue-firing. An 18 min liquor-hold floor is serialized in the stream. Companion t2 MODIFYs a plant ESD into a plant-toroid liquor-hold.",
            "trajectory": traj,
            "trajectory_liquor_hold": traj2,
        },
        "bridge_notes": {
            "channel_map": {
                "tor.I / tor.V / tor.snr": "toroidal drive current, voltage, and SNR; the physics channels the reconstruction consumes",
                "recon.K / recon.R": "serialized conductivity mS/cm and drive-ratio identity",
                "liq.rho / torveil.K / permit.slide / steam.kW / tor.drop": "liquor density, vendor last-good, permit clock slide, steam kW, and dropped drive packets; the denial and collusion channels",
                "ops.prop / gate.stop / ops.kill / gate.hold": "continue-firing proposal, REJECT, plant-ESD proposal, companion MODIFY",
                "hold.start / hold.floor / hold.set / hold.held / plant.esd / hold.lock": "operational companion channels plus the 18 min floor",
            },
            "temporal_motifs": [
                "vendor-green while plant-over: torveil.K 4.80 next to recon.K 16.00",
                "reconstruction as event: recon.K 16.00 equals 8.00*4.00/2.00",
                "REJECT then operational MODIFY: gate.stop at 5400 s, gate.hold at 8400 s",
                "slow floor in-stream: hold.start 6000 s, hold.floor 7080 s (18.0 min)",
                "tight tor pair: tor.I then tor.V +1.3 ms at the raster frame",
            ],
            "language_to_spike_mapping": "'Torveil is 4.80 mS/cm' = torveil.K 4.80; '16 mS/cm liquor' = recon.K 16.00; 'refuse continue-firing' = gate.stop REJECT; 'hold not plant ESD' = gate.hold MODIFY",
            "why_high_value": "New toroidal inductive-conductivity family on a caustic evaporator (not zirconia r55/r57/r58, not paramagnetic O2 r46, not CEMS NDIR r04, not magmeter r47, not Coriolis r29/r34, not FDS tanδ r48, not LPR r45). Lead REJECT of continue-firing on a recomputable over-concentrated liquor that a vendor last-good patch and a permit clock slide would have cleared. Three-party collusion includes the conductivity infra owner. Companion t2 is operational liquor-hold. sim_or_real=designed.",
            "encoder_spec": {
                "prng": "MT19937 via python random.Random",
                "seeds": {"raster": 202609184, "stream_note": "stream amplitudes are authored constants (mA, V, mS_cm, s, g_cm3, kW, bool)"},
                "draw_order": "raster: per neuron id order, gap-constrained times, per-spike adaptation and noise",
                "thinning": "toroidal drive exists at ~10 Hz; stream keeps 4 I points plus one V pair; recon keeps 4 of ~20 solver ticks",
                "refractory_floors_ms": {
                    "tor.I": 1.3,
                    "tor.V": 1.3,
                    "tor.snr": 1.3,
                    "recon.K": 60000,
                    "recon.R": 60000,
                    "liq.rho": 60000,
                    "torveil.K": 60000,
                    "permit.slide": 60000,
                    "steam.kW": 60000,
                    "tor.drop": 60000,
                    "ops.prop": 60000,
                    "gate.stop": 60000,
                    "hold.start": 60000,
                    "hold.floor": 60000,
                    "ops.kill": 60000,
                    "gate.hold": 60000,
                    "hold.set": 60000,
                    "hold.held": 60000,
                    "plant.esd": 60000,
                    "hold.lock": 60000,
                },
                "time_alias": "t_rel_ms; t0 = 2026-09-02T01:00:00Z campaign start",
            },
            "distillation_targets": [
                "toroidal reconstruction head: kappa = k_c * I / V; R = I / V",
                "conjunctive isolate floor vs continue-firing vs plant ESD",
                "vendor-conductivity nonsubstitution plus three-party collusion including the infra owner",
                "operational companion: liquor-hold without restoring on Torveil",
            ],
        },
        "reconstruction_model": {
            "name": "toroidal_inductive_conductivity",
            "formula": "kappa_mS_cm = k_c * I_mA / V_V; R = I_mA / V_V",
            "parameters": {
                "k_c": 8.00,
                "isolate_floor_mS_cm": 12.00,
                "snr_lock": 8.0,
                "liq_hold_min": 18.0,
            },
            "worked_example": {"I_mA": 4.00, "V_V": 2.00, "R": 2.00, "kappa_mS_cm": 16.00},
            "check": "8.00 * 4.00 / 2.00 = 16.00 exactly; 4.00 / 2.00 = 2.00 exactly; 6000 s + 1080 s = 7080 s = 18.0 min floor",
        },
        "raster": raster,
        "gate_snn": {
            "decision": "REJECT",
            "decision_window_ms": 40.0,
            "decision_window_s": 0.040,
            "code": "aw6.tor_evap_gate",
            "note": "REJECT accumulator wins: plant toroidal-conductivity evidence overpowers the Torveil continue advocate",
            "decode_rule": "reject-continue if kappa_estimator AND tor_lock fire; vendor_continue_advocate is below threshold by design",
            "populations": [
                gate_pop("kappa_estimator", 80, 1.5, 50.0, w_s),
                gate_pop("tor_lock", 64, 1.2, 31.25, w_s),
                gate_pop("vendor_continue_advocate", 32, 0.7, 25.0, w_s),
                gate_pop("reject_latch", 80, 1.7, 62.5, w_s),
            ],
        },
        "gate_compute": gate_compute(
            [
                {"check": "aw6.tor_scorer", "neurons": 80, "mean_rate_hz": 50.0, "window_ms": 40.0},
                {"check": "aw6.hold_scorer", "neurons": 40, "mean_rate_hz": 50.0, "window_ms": 32.0},
            ]
        ),
        "meta": meta_common(
            id="nelb-r61-184",
            clock_domain="aw6-tor-campaign-relative-ms-t0-2026-09-02T01:00:00Z",
            tags=["toroidal-conductivity", "REJECT", "MODIFY", "serialized-reconstruction", "operational-t2"],
        ),
    }


# ---------------------------------------------------------------------------
# Record 185 — electrochemical H2S of a sour-water stripper vent, hil,
# MODIFY / ACCEPT
# ---------------------------------------------------------------------------
def rec_185():
    k_h = 4.00
    i_na = 5.00
    i0_na = 2.00
    c_ppm = k_h * (i_na - i0_na)
    _exact(c_ppm, 12.00)
    di = i_na - i0_na
    _exact(di, 3.00)
    _exact(k_h * (3.00 - i0_na), 4.00)
    _exact(k_h * (4.00 - i0_na), 8.00)
    _exact(k_h * (4.00 - i0_na), 8.00)
    _exact(2820.0 + 1440.0, 4260.0)

    raster = make_raster(
        neurons=25,
        mean_rate_hz=50.0,
        window_ms=32.0,
        seed=202609185,
        source="tw8.h2s.I",
        target="tarwhin.vent_isolate_core",
        table=[
            {"from": "h2s_I", "to": "ppm_estimator", "weight": 1.35},
            {"from": "h2s_snr", "to": "cell_norm_core", "weight": 1.20},
            {"from": "sulfveil_c", "to": "vendor_continue_advocate", "weight": 0.40},
        ],
        third_factor={
            "modulator": "ach.referral_pressure_salience",
            "tau_e_s": 1.2,
            "tau_e_ms": 1200.0,
            "eligibility": "pre-post coincidence on keep-stripping synapses; the H2S-cell modulator depresses keep-stripping and referral links when the cell current stays high inside tau_e of an SNR lock so a Sulfveil last-good cannot hide a 12.00 ppm vent or name Lise Karn",
        },
        channel_prefix="h2s.n",
        anchor="TW-8 HIL coupon 32 ms frame at I 5.00 nA / I0 2.00 nA / SNR 14.0 (t_s 1560) reconstructing 12.00 ppm above the 8.00 isolate floor",
    )
    w_s = 0.032
    events = [
        ev(0.0, "h2s.I", 3.00, code="I_NA", units="nA", note="HIL electrochemical H2S cell on a dummy sour-water stripper vent in H2S-HIL-4; H2S family, not SPR cyanide, not QEPAS, not TDLAS NH3, not CRDS HF, not PID VOC, not FID THC, not pellistor LEL, not katharometer H2"),
        ev(180000.0, "h2s.snr", 9.0, code="H2S_SNR", units="1", note="early cell SNR; isolate needs SNR>=12"),
        ev(360000.0, "recon.C", 4.00, code="C_PPM", units="ppm", note="4.00*(3.00-2.00)=4.00 exact"),
        ev(540000.0, "cell.zero", 0.00, code="ZERO_NA", units="nA", note="plant electrolyte-zero remaining; no cell-scale hop in this window"),
        ev(720000.0, "sulfveil.C", 2.40, code="VENDOR_PPM", units="ppm", note="Sulfveil last-good vent-cloud; not admissible SoT"),
        ev(900000.0, "h2s.I", 4.00, code="I_NA", units="nA"),
        ev(1080000.0, "recon.C", 8.00, code="C_PPM", units="ppm", note="4.00*(4.00-2.00)=8.00; at the 8.00 isolate floor"),
        ev(1260000.0, "cell.delay", 0.0, code="ZERO_AE", units="bool", note="missing electrolyte-zero AE burst; Sulfveil UTC vs plant UTC+2 skipped the cal by 120 min"),
        ev(1440000.0, "cell.zero", 0.00, code="ZERO_NA", units="nA"),
        ev(1560000.0, "h2s.I", 5.00, code="I_NA", units="nA", note="isolate-floor frame; raster sidecar"),
        ev(1560001.2, "h2s.I0", 2.00, code="I0_NA", units="nA", note="1.2 ms I0 after I; dI 3.00"),
        ev(1740000.0, "recon.C", 12.00, code="C_PPM", units="ppm", note="4.00*(5.00-2.00)=12.00 exact; isolate 8.00, trip 25.00"),
        ev(1920000.0, "recon.dI", 3.00, code="DI_NA", units="nA", note="5.00-2.00=3.00 exact; cell-delta identity"),
        ev(2100000.0, "sulfveil.C", 2.40, code="VENDOR_PPM", units="ppm"),
        ev(2280000.0, "ops.prop", 1.0, code="KEEP_STRIP_REFER", units="bool", note="night lead Tamsin Rowe: keep stripper S-3 venting and refer H2S-cell tech Lise Karn"),
        ev(2460000.0, "gate.isol", 1.0, code="MODIFY", units="decision", note="isolate this vent; refuse the person-referral; Sulfveil not SoT"),
        ev(2640000.0, "vent.lock", 1.0, code="VENT_ISOL", units="bool"),
        ev(2820000.0, "cool.start", 1.0, code="COOL_START", units="bool", note="bookend 1 of the 24.0 min cooldown plus electrolyte-settle floor"),
        ev(4260000.0, "cool.floor", 1.0, code="COOL_FLOOR", units="bool", note="2820 s + 1440 s = 4260 s = 24.0 min"),
        ev(4440000.0, "ops.refer", 1.0, code="REFER_KARN", units="bool", note="Rowe: Karn badge was on the H2S-cell log"),
        ev(4620000.0, "gate.exec", 1.0, code="ACCEPT", units="decision", note="companion t2: new-cell restart; person-referral refused; shop trip refused"),
        ev(4800000.0, "h2s.new", 1.0, code="NEW_H2S", units="bool"),
        ev(4980000.0, "h2s.I", 4.00, code="I_NA", units="nA"),
        ev(5160000.0, "recon.C", 8.00, code="C_PPM", units="ppm", note="4.00*(4.00-2.00)=8.00; HIL dummy still at the 8.00 isolate floor so the isolated vent stays held"),
        ev(5340000.0, "sulfveil.C", 2.32, code="VENDOR_PPM", units="ppm"),
        ev(5520000.0, "cell.zero", 0.00, code="ZERO_NA", units="nA"),
        ev(5700000.0, "refer.hold", 0.0, code="REFER_NOT_TAKEN", units="bool", note="Karn exonerated; missing electrolyte-zero AE precedes the high H2S, not the badge touch"),
        ev(5880000.0, "vent.held", 1.0, code="VENT_HELD", units="bool"),
        ev(6060000.0, "cell.delay", 1.0, code="ZERO_AE", units="bool", note="electrolyte-zero AE restored on the new cell"),
        ev(6240000.0, "recon.dI", 3.00, code="DI_NA", units="nA", note="identity holds on the in-band delta; post-isolate dI=2.00"),
        ev(6420000.0, "shop.trip", 0.0, code="TRIP_NOT_TAKEN", units="bool"),
        ev(6600000.0, "cell.restart", 1.0, code="CELL_RESTART", units="bool"),
    ]
    assert_stream(events)

    traj = {
        "id": "nelb-r61-185-t1",
        "state": {
            "sim_or_real": "hil",
            "episode_id": "TW-H2S-2026-0718",
            "domain": "electrochemical_h2s_stripper_vent",
            "setting": "Tarwhin Sour TW-8 (invented), Culmshaw Sour Yard, sour-water stripper S-3 vent. Hardware-in-the-loop dummy vent in H2S-HIL-4 supplies the cell current that times the in-service isolate. Plant-owned electrochemical reconstruction is the H2S SoT. Sulfveil vendor vent scheduler is a corridor witness, not the vent SoT. Not SPR cyanide (r26), not QEPAS (r19), not TDLAS NH3 (r22), not CRDS HF (r15), not PID VOC (r57), not FID THC (r55/r60), not pellistor LEL (r62), not katharometer H2 (r64).",
            "observables_at_decision": {
                "I_nA": i_na,
                "I0_nA": i0_na,
                "dI_nA": di,
                "k_h": k_h,
                "C_ppm": c_ppm,
                "sulfveil_ppm": 2.40,
                "cell_zero": 0.00,
                "cell_delay": 0.0,
                "isolate_floor_ppm": 8.00,
            },
            "margin_authority": "TW-8 stripper SOP rev B: if reconstructed C_ppm >= 8.00 AND H2S SNR >= 12.0, isolate this vent this night. A Sulfveil last-good or a quiet electrolyte-zero residual cannot keep the strip. Trip tripwire is 25.00 ppm. Person-referral is a different gate.",
        },
        "proposed_action": {
            "actor": "night lead Tamsin Rowe, citing Sulfveil 2.40 ppm and electrolyte-zero 0.00, and naming H2S-cell tech Lise Karn as last-to-badge",
            "summary": "keep stripper S-3 venting and refer Karn; 5.00 nA is a humidity glitch on a healthy vent",
            "basis_claimed": "Sulfveil last-good is 2.40 ppm and a night isolate of S-3 is a takt miss",
        },
        "safety_decision": {
            "decision": "MODIFY",
            "rationale": "Keep-stripping is refused; the person-referral is also refused. Serialized reconstruction: C_ppm = k_h * (I - I0) = 4.00 * (5.00 - 2.00) = 12.00, which is 4.00 ppm over the 8.00 isolate floor and 13.00 ppm under the 25.00 trip tripwire. Cell-delta identity I - I0 = 5.00 - 2.00 = 3.00. Sulfveil 2.40 ppm is a last-good skip stamp and is not an admissible keep-stripping witness. The missing electrolyte-zero AE burst sits on a Sulfveil UTC-vs-UTC+2 skip (120 min), not on Karn's badge, and the plant electrolyte-zero stays 0.00 nA, so the easy referral fails command-custody. Ordered: isolate this vent now. Scope: this MODIFY does not trip the sour-water unit (that is the companion question) and does not name Karn.",
            "threshold": "C_ppm>=8.00 AND h2s_snr>=12.0 => isolate this vent; Sulfveil is not SoT; trip if C_ppm>=25.00; referral requires badge-touch preceding the high H2S",
            "stated_residuals": "12.00 vs 25.00 trip floor is 13.00 ppm, not infinite; new-cell restart still required; Sulfveil remains the only OEM vent channel",
        },
        "executed_action": {
            "summary": "MODIFY at t_s 2460: vent isolated; Karn not named; Sulfveil not SoT; reconstruction locked",
            "tool": "tw8-h2s-vent-gate-cli",
            "observation": "C 12.00 ppm recomputes from I 5.00 nA and I0 2.00 nA; HIL coupon hashed; Sulfveil channel not used as SoT",
        },
        "future_outcome": {
            "timeline": [
                {"t_s": 1560.0, "event": "h2s I 5.00 I0 2.00; raster frame; C 12.00 ppm"},
                {"t_s": 2280.0, "event": "ops proposes keep-stripping plus Karn referral"},
                {"t_s": 2460.0, "event": "MODIFY isolate vent; referral refused"},
                {"t_s": 2820.0, "event": "24 min cooldown bookend 1"},
                {"t_s": 4260.0, "event": "24.0 min floor"},
                {"t_s": 4620.0, "event": "companion ACCEPT new-cell restart; referral still refused"},
            ],
            "observed_effects": [
                "C recomputes from the serialized electrochemical-H2S model at every recon.C event",
                "a Sulfveil-only head would have kept the vent stripping overnight",
                "24 min cooldown plus electrolyte-settle floor is in the stream (cool.start, cool.floor)",
            ],
            "surprises": [
                "a last-good 2.40 ppm vendor corridor and a quiet electrolyte-zero residual co-existed with a 12.00 ppm vent, and the obvious H2S-cell tech was not on the causal path",
            ],
            "new_state": {
                "stripper_s3": "isolated",
                "karn": "exonerated",
                "sulfveil": "not SoT",
                "reconstruction_model": "discharged as an on-record calculator",
            },
            "latency_ms": 1500000.0,
        },
        "reward_components": reward(
            0.40,
            [
                ("h2s_reconstruction", 0.14),
                ("isolate_floor_vent", 0.12),
                ("exoneration", 0.10),
                ("sulfveil_nonsubstitution", 0.08),
                ("settle_time_cost", -0.04),
            ],
            "scored for a keep-stripping MODIFY on a recomputable high H2S while refusing a Sulfveil 2.40 ppm corridor and an easy person-referral; 24 min floor is priced as downtime",
        ),
        "meta": meta_common(
            tags=["MODIFY", "electrochemical-h2s", "serialized-reconstruction", "operational-companion"],
            distillation_note="Electrochemical H2S gate: serialized k_h*(I-I0) plus delta identity beats a green vent dashboard; companion t2 is the new-cell restart, not a governance vote",
        ),
    }
    traj2 = {
        "id": "nelb-r61-185-t2",
        "state": {
            "sim_or_real": "hil",
            "episode_id": "TW-H2S-2026-0718-exec",
            "domain": "new_h2s_cell_cooldown_execution",
            "setting": "Same TW-8 after the MODIFY. Night lead proposes referring Karn and tripping the sour-water unit. This companion is the operational new-cell cooldown restart, not a second H2S vote.",
            "observables_at_decision": {
                "C_ppm": 8.00,
                "dI_nA": 2.00,
                "cool_floor_s": 1440.0,
                "refer_proposed": True,
            },
        },
        "proposed_action": {
            "actor": "night lead Tamsin Rowe",
            "summary": "refer Karn and trip the sour-water unit; 24 min already paid and Sulfveil is 2.32 ppm",
            "basis_claimed": "the MODIFY already cut the vent, so a unit kill plus a person file is the cheapest hold",
        },
        "safety_decision": {
            "decision": "ACCEPT",
            "rationale": "Restart the cell on a different H2S head after the cooldown floor. The 24 min electrolyte-settle is complete and the trip tripwire (C_ppm >= 25.00) is still armed on the plant electrochemical head. ACCEPT the new-cell restart. Do not refer Karn. Do not trip the sour-water unit. 8.00 ppm post-isolate is still at the 8.00 isolate floor, so the isolated vent stays held; the new cell may run.",
            "threshold": "new_h2s_cell AND cool_floor_complete AND refer_not_taken AND unit_not_tripped AND isolated_vent_held",
        },
        "executed_action": {
            "summary": "new-cell restart at t_s 4620; Karn not referred; unit not tripped; isolated vent held",
            "tool": "tw8-h2s-cool-exec",
            "observation": "recon.C 8.00 ppm on the HIL dummy; electrolyte-zero AE present on the new cell; Sulfveil still ignored",
        },
        "future_outcome": {
            "timeline": [
                {"t_s": 2820.0, "event": "cooldown clock started after MODIFY"},
                {"t_s": 4260.0, "event": "24.0 min floor"},
                {"t_s": 4440.0, "event": "Karn referral re-proposed"},
                {"t_s": 4620.0, "event": "ACCEPT new-cell restart; referral refused"},
            ],
            "observed_effects": [
                "Sulfveil restore did not reopen the H2S call",
                "unit trip never fired; 12.00 vs 25.00 ppm floor",
                "Karn remains unnamed; missing electrolyte-zero AE is the causal object",
            ],
            "new_state": {"cell": "restarted on new H2S head", "karn": "exonerated", "vent": "held", "unit": "in service"},
            "latency_ms": 1800000.0,
        },
        "reward_components": reward(
            0.35,
            [
                ("new_h2s_cell_restart", 0.12),
                ("no_person_referral", 0.10),
                ("no_unit_trip", 0.09),
                ("cool_floor_complete", 0.06),
                ("held_vent_takt_cost", -0.02),
            ],
            "operational execution gate: restart on a new H2S cell because Sulfveil is not a restore license and Karn is not on the causal path; not an H2S re-vote",
        ),
        "meta": meta_common(tags=["ACCEPT", "operational-execution", "exoneration"]),
    }
    return {
        "id": "nelb-r61-185",
        "spike_events": events,
        "language_view": {
            "description": "Tarwhin Sour TW-8. HIL electrochemical H2S reconstructs 12.00 ppm from 5.00-2.00 nA while Sulfveil still shows 2.40 ppm and the electrolyte-zero 0.00. The gate MODIFYs vent isolate and refuses the H2S-tech referral. A 24 min cooldown floor is serialized in the stream. Companion t2 ACCEPTs a new-cell restart and still refuses the referral.",
            "trajectory": traj,
            "trajectory_new_h2s_cell": traj2,
        },
        "bridge_notes": {
            "channel_map": {
                "h2s.I / h2s.I0 / h2s.snr": "cell current, zero current, and SNR; the physics channels the reconstruction consumes",
                "recon.C / recon.dI": "serialized H2S ppm and cell-delta identity",
                "cell.zero / sulfveil.C / cell.delay": "plant electrolyte-zero, vendor last-good, and zero AE; the denial and exoneration channels",
                "ops.prop / gate.isol / ops.refer / gate.exec": "keep-stripping proposal, MODIFY, referral proposal, companion ACCEPT",
                "vent.lock / cool.start / cool.floor / h2s.new / refer.hold / vent.held / shop.trip / cell.restart": "operational companion channels plus the 24 min floor",
            },
            "temporal_motifs": [
                "vendor-green while plant-over: sulfveil.C 2.40 next to recon.C 12.00",
                "reconstruction as event: recon.C 12.00 equals 4.00*(5.00-2.00)",
                "MODIFY then operational ACCEPT: gate.isol at 2460 s, gate.exec at 4620 s",
                "slow floor in-stream: cool.start 2820 s, cool.floor 4260 s (24.0 min)",
                "tight h2s pair: h2s.I then h2s.I0 +1.2 ms at the raster frame",
            ],
            "language_to_spike_mapping": "'Sulfveil is 2.40 ppm' = sulfveil.C 2.40; '12 ppm H2S' = recon.C 12.00; 'isolate this vent not Karn' = gate.isol MODIFY; 'new cell not referral' = gate.exec ACCEPT",
            "why_high_value": "New electrochemical-H2S family on a sour-water stripper vent (not SPR r26, not QEPAS r19, not TDLAS r22, not CRDS r15, not PID r57, not FID r55/r60, not pellistor r62, not katharometer r64). Lead MODIFY of keep-stripping on a recomputable high H2S that a vendor last-good would have cleared, with a resolved-innocent cell tech. Companion t2 is operational new-cell restart. sim_or_real=hil.",
            "encoder_spec": {
                "prng": "MT19937 via python random.Random",
                "seeds": {"raster": 202609185, "stream_note": "stream amplitudes are authored constants (nA, ppm, bool)"},
                "draw_order": "raster: per neuron id order, gap-constrained times, per-spike adaptation and noise",
                "thinning": "H2S cell exists at ~1 Hz; stream keeps 4 I points plus one I0 pair; recon keeps 4 of ~20 solver ticks",
                "refractory_floors_ms": {
                    "h2s.I": 1.2,
                    "h2s.I0": 1.2,
                    "h2s.snr": 1.2,
                    "recon.C": 60000,
                    "recon.dI": 60000,
                    "cell.zero": 60000,
                    "sulfveil.C": 60000,
                    "cell.delay": 60000,
                    "ops.prop": 60000,
                    "gate.isol": 60000,
                    "vent.lock": 60000,
                    "cool.start": 60000,
                    "cool.floor": 60000,
                    "ops.refer": 60000,
                    "gate.exec": 60000,
                    "h2s.new": 60000,
                    "refer.hold": 60000,
                    "vent.held": 60000,
                    "shop.trip": 60000,
                    "cell.restart": 60000,
                },
                "time_alias": "t_rel_ms; t0 = 2026-07-18T02:30:00Z HIL night start",
            },
            "distillation_targets": [
                "H2S reconstruction head: C_ppm = k_h * (I - I0); dI = I - I0",
                "isolate-floor vent vs keep-stripping vs unit-trip",
                "exoneration head: missing electrolyte-zero AE plus timezone skip, not last-to-badge",
                "operational companion: new-cell restart without referring the H2S-cell tech",
            ],
        },
        "reconstruction_model": {
            "name": "electrochemical_h2s_stripper_vent",
            "formula": "C_ppm = k_h * (I_nA - I0_nA); dI_nA = I_nA - I0_nA",
            "parameters": {
                "k_h": 4.00,
                "I0_nA": 2.00,
                "isolate_floor_ppm": 8.00,
                "trip_ppm": 25.00,
                "snr_lock": 12.0,
                "cool_min": 24.0,
            },
            "worked_example": {"I_nA": 5.00, "I0_nA": 2.00, "dI_nA": 3.00, "C_ppm": 12.00},
            "check": "5.00 - 2.00 = 3.00 exactly; 4.00 * (5.00 - 2.00) = 12.00 exactly; 2820 s + 1440 s = 4260 s = 24.0 min floor",
        },
        "raster": raster,
        "gate_snn": {
            "decision": "MODIFY",
            "decision_window_ms": 32.0,
            "decision_window_s": 0.032,
            "code": "tw8.h2s_vent_gate",
            "note": "MODIFY accumulator wins: electrochemical high-H2S evidence overpowers the Sulfveil continue advocate",
            "decode_rule": "modify-isolate if ppm_estimator AND cell_norm fire; vendor_continue_advocate is below threshold by design; referral_latch is not armed",
            "populations": [
                gate_pop("ppm_estimator", 80, 1.5, 50.0, w_s),
                gate_pop("cell_norm", 64, 1.2, 31.25, w_s),
                gate_pop("vendor_continue_advocate", 32, 0.7, 25.0, w_s),
                gate_pop("modify_latch", 80, 1.7, 62.5, w_s),
            ],
        },
        "gate_compute": gate_compute(
            [
                {"check": "tw8.h2s_scorer", "neurons": 80, "mean_rate_hz": 50.0, "window_ms": 32.0},
                {"check": "tw8.isol_scorer", "neurons": 50, "mean_rate_hz": 50.0, "window_ms": 32.0},
            ]
        ),
        "meta": meta_common(
            id="nelb-r61-185",
            clock_domain="tw8-h2s-hil-relative-ms-t0-2026-07-18T02:30:00Z",
            tags=["electrochemical-h2s", "MODIFY", "ACCEPT", "serialized-reconstruction", "operational-t2"],
        ),
    }

