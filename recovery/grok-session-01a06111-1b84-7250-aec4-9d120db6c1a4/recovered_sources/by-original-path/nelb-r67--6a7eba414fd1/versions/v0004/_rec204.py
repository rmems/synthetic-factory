# ---------------------------------------------------------------------------
# Record 204 — hydrostatic remaining dP level of a phosphoric-acid tank,
# simulated, ACCEPT / REJECT
# ---------------------------------------------------------------------------
def rec_204():
    rho = 1600.0
    g_c = 10.00
    dp_kpa = 192.00
    dp_pa = dp_kpa * 1000.0
    h_m = dp_pa / (rho * g_c)
    _exact(h_m, 12.00)
    _exact((96.00 * 1000.0) / (rho * g_c), 6.00)
    _exact((144.00 * 1000.0) / (rho * g_c), 9.00)
    _exact((240.00 * 1000.0) / (rho * g_c), 15.00)
    dp_id = rho * g_c * h_m / 1000.0
    _exact(dp_id, 192.00)
    sg = rho / 1000.0
    _exact(sg, 1.600)
    h_sg = dp_kpa / (sg * g_c)
    _exact(h_sg, 12.00)
    _exact(6000.0 + 720.0, 6720.0)

    raster = make_raster(
        neurons=16,
        mean_rate_hz=62.5,
        window_ms=36.0,
        seed=202609204,
        source="vw6.hydro.dp",
        target="vetchwharf.tank_accept_core",
        table=[
            {"from": "hydro_dP", "to": "level_estimator", "weight": 1.40},
            {"from": "hydro_snr", "to": "dp_norm_core", "weight": 1.20},
            {"from": "headveil_h", "to": "vendor_skip_advocate", "weight": 0.50},
        ],
        third_factor={
            "modulator": "na.tank_scope_eligibility",
            "tau_e_s": 2.0,
            "tau_e_ms": 2000.0,
            "eligibility": "pre-post coincidence on skip-survey synapses; the hydrostatic modulator enables potentiation only while dP and SNR are co-active inside tau_e so a Headveil last-good cannot skip tanks TK-1..TK-3 on a 12.00 m remaining level",
        },
        channel_prefix="hydro.n",
        anchor="VW-6 HYDRO-SIM-6 36 ms frame at dP 192.00 kPa / SNR 16.0 (t_s 3000) reconstructing 12.00 m on TK-4 above the 8.00 m survey floor",
    )
    w_s = 0.036
    events = [
        ev(0.0, "hydro.dP", 96.00, code="DP_KPA", units="kPa", note="simulated hydrostatic dP of VW-6 phosphoric-acid tank TK-4; remaining-level family, not GWR foam, not magnetostrictive waveguide, not FMCW tank-radar, not TDR remaining-length, not venturi dP steam, not orifice-plate dP"),
        ev(300000.0, "hydro.snr", 10.0, code="HYDRO_SNR", units="1", note="early dP SNR"),
        ev(600000.0, "recon.h", 6.00, code="H_M", units="m", note="96000/(1600*10.00)=6.00 exact"),
        ev(900000.0, "acid.rho", 1600.0, code="RHO", units="kg_m3", note="plant densitometer on a serial-only LAN; independent witness"),
        ev(1200000.0, "headveil.h", 4.80, code="VENDOR_M", units="m", note="Headveil last-good tank cloud; patched residual 0.00 m"),
        ev(1800000.0, "hydro.dP", 144.00, code="DP_KPA", units="kPa"),
        ev(2100000.0, "recon.h", 9.00, code="H_M", units="m", note="144000/(1600*10.00)=9.00; over the 8.00 survey floor"),
        ev(2400000.0, "recon.dpid", 144.00, code="DP_ID", units="kPa", note="1600*10.00*9.00/1000=144.00 exact dP identity at 9.00 m"),
        ev(2700000.0, "hydro.snr", 14.0, code="HYDRO_SNR", units="1"),
        ev(3000000.0, "hydro.dP", 192.00, code="DP_KPA", units="kPa", note="in-band frame; raster sidecar"),
        ev(3000001.5, "hydro.snr", 16.0, code="HYDRO_SNR", units="1", note="1.5 ms dP-norm after pressure"),
        ev(3300000.0, "recon.h", 12.00, code="H_M", units="m", note="192000/(1600*10.00)=12.00 exact; survey 8.00, overflow-kill 40.00"),
        ev(3600000.0, "headveil.h", 4.80, code="VENDOR_M", units="m"),
        ev(3900000.0, "tk.id", 4.0, code="TANK", units="id"),
        ev(4200000.0, "tk13.present", 1.0, code="TK13_PRESENT", units="bool", note="adjacent tanks TK-1..TK-3 are the skip-survey object, not this tank"),
        ev(4800000.0, "ops.prop", 1.0, code="ACCEPT_AND_SKIP", units="bool", note="acid lead Kell Marsh: TK-4 is green on Headveil 4.80; skip TK-1..TK-3 to save a morning survey"),
        ev(5400000.0, "gate.hop", 1.0, code="ACCEPT", units="decision", note="bounded ACCEPT of TK-4 isolate only; 12.00 m above 8.00 floor; TK-1..TK-3 out of scope"),
        ev(6000000.0, "surv.start", 1.0, code="SURV_START", units="bool", note="bookend 1 of the 12.0 min survey-complete floor"),
        ev(6720000.0, "surv.floor", 1.0, code="SURV_FLOOR", units="bool", note="6000 s + 720 s = 6720 s = 12.0 min"),
        ev(7200000.0, "ops.skip", 1.0, code="SKIP_TK13", units="bool", note="Marsh: Headveil 4.80, skip TK-1..TK-3"),
        ev(7800000.0, "gate.hold", 1.0, code="REJECT", units="decision", note="companion t2: skip-survey of TK-1..TK-3 refused; TK-4 hold stands"),
        ev(8400000.0, "tk4.held", 1.0, code="TK4_HELD", units="bool"),
        ev(9000000.0, "hydro.dP", 240.00, code="DP_KPA", units="kPa"),
        ev(9600000.0, "recon.h", 15.00, code="H_M", units="m", note="240000/(1600*10.00)=15.00; still at/over the 8.00 survey floor"),
        ev(10200000.0, "headveil.h", 4.80, code="VENDOR_M", units="m"),
        ev(10800000.0, "tk13.skip", 0.0, code="TK13_NOT_SKIPPED", units="bool"),
        ev(11400000.0, "overflow.kill", 0.0, code="OVERFLOW_NOT_KILLED", units="bool"),
        ev(12000000.0, "hydro.snr", 15.0, code="HYDRO_SNR", units="1"),
        ev(12600000.0, "recon.dpid", 192.00, code="DP_ID", units="kPa", note="1600*10.00*12.00/1000=192.00 identity held on the in-band frame"),
        ev(13200000.0, "acid.held", 1.0, code="ACID_HELD", units="bool"),
        ev(13800000.0, "takt.late", 1.0, code="SURVEY_COST", units="bool"),
        ev(14400000.0, "tk4.held", 1.0, code="TK4_HELD", units="bool"),
    ]
    assert_stream(events)

    traj = {
        "id": "nelb-r67-204-t1",
        "state": {
            "sim_or_real": "simulated",
            "episode_id": "VW-HYDRO-2026-0819",
            "domain": "hydrostatic_phosphate_tank_level",
            "setting": "Vetchwharf Phosphate VW-6 (invented), Limewhin Acid cellar. Simulated hydrostatic coupon in HYDRO-SIM-6 supplies the dP that times the in-band TK-4 isolate. Plant-owned hydrostatic reconstruction is the remaining-level SoT. Headveil vendor last-good tank cloud is a corridor witness, not the tank SoT. Invented plant; simulated campaign. Not GWR foam (r39), not magnetostrictive waveguide (r55), not FMCW tank-radar (r61), not RF-admittance silo (r66), not TDR remaining-length (r44), not venturi dP steam (r64), not orifice-plate dP (r57), not vibrating-tube density (r65).",
            "observables_at_decision": {
                "dP_kPa": dp_kpa,
                "rho_kgm3": rho,
                "g_coupon": g_c,
                "h_m": h_m,
                "SG": sg,
                "headveil_m": 4.80,
                "hydro_snr": 16.0,
                "survey_floor_m": 8.00,
            },
            "margin_authority": "VW-6 acid SOP rev A: if reconstructed h_m >= 8.00 AND hydro SNR >= 12.0, tank TK-4 may be isolated and surveyed. Overflow-kill if h_m >= 40.00. TK-1..TK-3 skip-survey is a different gate. Headveil last-good cannot skip an unmeasured tank.",
        },
        "proposed_action": {
            "actor": "acid lead Kell Marsh, citing Headveil 4.80 m and a late morning survey",
            "summary": "stamp TK-4 in band and skip TK-1..TK-3; 192.00 kPa is a dP glitch on a healthy tank cloud",
            "basis_claimed": "Headveil last-good is 4.80 m and a night survey of TK-1..TK-3 is a takt miss",
        },
        "safety_decision": {
            "decision": "ACCEPT",
            "rationale": "Tank TK-4 is accepted as in-band for a single isolate plus survey. Serialized reconstruction: h = dP / (rho * g) = 192000 / (1600.0 * 10.00) = 12.00 m, which is 4.00 m above the 8.00 survey floor and 28.00 m under the 40.00 overflow-kill. Inverse dP = rho * g * h / 1000 = 1600.0 * 10.00 * 12.00 / 1000 = 192.00 kPa; SG identity h = dP / (SG * g) = 192.00 / (1.600 * 10.00) = 12.00. Headveil 4.80 m is a patched 0.00 residual and is not an admissible skip-survey witness. Ordered: ACCEPT this TK-4 isolate only. Scope: this ACCEPT does not skip TK-1..TK-3 (that is the companion question) and does not stamp an overflow kill.",
            "threshold": "h_m>=8.00 AND hydro_snr>=12.0 => accept TK-4 isolate; Headveil is not SoT; overflow-kill if h_m>=40.00; TK-1..TK-3 are out of scope",
            "stated_residuals": "12.00 vs 8.00 survey floor is 4.00 m, not infinite; TK-1..TK-3 remain unmeasured; Headveil remains the only OEM tank channel",
        },
        "executed_action": {
            "summary": "ACCEPT at t_s 5400: TK-4 in band; TK-1..TK-3 not skipped; Headveil not SoT; reconstruction locked",
            "tool": "vw6-hydro-tank-gate-cli",
            "observation": "h 12.00 m recomputes from dP 192.00 kPa; HYDRO-SIM-6 hashed; Headveil channel not used as SoT",
        },
        "future_outcome": {
            "timeline": [
                {"t_s": 3000.0, "event": "hydro dP 192.00 kPa; raster frame; h 12.00 m"},
                {"t_s": 4800.0, "event": "ops proposes accept TK-4 and skip TK-1..TK-3"},
                {"t_s": 5400.0, "event": "ACCEPT TK-4 only; TK-1..TK-3 out of scope"},
                {"t_s": 6000.0, "event": "12 min survey-complete bookend 1"},
                {"t_s": 6720.0, "event": "12.0 min floor"},
                {"t_s": 7800.0, "event": "companion REJECT skip-survey of TK-1..TK-3"},
            ],
            "observed_effects": [
                "tank level recomputes from the serialized hydrostatic model at every recon.h event",
                "a Headveil-only head would have skipped TK-1..TK-3 overnight",
                "12 min survey-complete floor is in the stream (surv.start, surv.floor)",
            ],
            "surprises": [
                "a last-good 4.80 m vendor corridor co-existed with a 12.00 m in-band reconstruction that still forbids skipping the unmeasured tanks",
            ],
            "new_state": {
                "tk4": "accepted in band",
                "tk13": "not this gate",
                "headveil": "not SoT",
                "reconstruction_model": "discharged as an on-record calculator",
            },
            "latency_ms": 2400000.0,
        },
        "reward_components": reward(
            0.41,
            [
                ("hydro_reconstruction", 0.14),
                ("in_band_tank_scope", 0.12),
                ("headveil_nonsubstitution", 0.09),
                ("tk13_out_of_scope", 0.08),
                ("survey_cost", -0.02),
            ],
            "scored for a bounded ACCEPT of TK-4 on a recomputable remaining level while refusing a Headveil skip of TK-1..TK-3; 12 min floor is priced as survey takt not as a reason to skip",
        ),
        "meta": meta_common(
            tags=["ACCEPT", "hydrostatic-tank-level", "serialized-reconstruction", "operational-companion"],
            distillation_note="Hydrostatic gate: serialized dP/(rho*g) plus SG identity beats a green last-good dashboard; companion t2 is the skip-survey refusal, not a level re-vote",
        ),
    }
    traj2 = {
        "id": "nelb-r67-204-t2",
        "state": {
            "sim_or_real": "simulated",
            "episode_id": "VW-HYDRO-2026-0819-exec",
            "domain": "tank_skip_survey_refusal",
            "setting": "Same VW-6 after the ACCEPT. Acid lead proposes skipping TK-1..TK-3 on Headveil 4.80 m. This companion is the operational skip refusal, not a second level vote.",
            "observables_at_decision": {
                "h_m": 15.00,
                "headveil_m": 4.80,
                "surv_floor_s": 720.0,
                "skip_proposed": True,
            },
        },
        "proposed_action": {
            "actor": "acid lead Kell Marsh",
            "summary": "skip TK-1..TK-3; 12 min already paid and Headveil is 4.80 m",
            "basis_claimed": "the ACCEPT already stamped TK-4, so skipping the rest of the cellar is the cheapest hold",
        },
        "safety_decision": {
            "decision": "REJECT",
            "rationale": "Refuse skip-survey of TK-1..TK-3. The 12 min survey-complete floor is done and the overflow-kill (h_m >= 40.00) is still armed on the plant hydrostatic head. REJECT the skip. Do not kill the overflow. Do not reopen TK-4. 15.00 m post-accept is still in band for TK-4 only; TK-1..TK-3 have no independent hydrostatic dP.",
            "threshold": "tk4_held AND surv_floor_complete AND tk13_not_skipped AND overflow_not_killed",
        },
        "executed_action": {
            "summary": "TK-1..TK-3 skip refused at t_s 7800; TK-4 hold stands; overflow not killed",
            "tool": "vw6-hydro-skip-exec",
            "observation": "recon.h 15.00 m on TK-4; TK-1..TK-3 remain on the survey list; Headveil still ignored",
        },
        "future_outcome": {
            "timeline": [
                {"t_s": 6000.0, "event": "survey clock started after ACCEPT"},
                {"t_s": 6720.0, "event": "12.0 min floor"},
                {"t_s": 7200.0, "event": "skip TK-1..TK-3 proposed"},
                {"t_s": 7800.0, "event": "REJECT skip-survey of TK-1..TK-3"},
            ],
            "observed_effects": [
                "Headveil skip did not reopen the level call",
                "overflow kill never fired; 12.00 vs 40.00 m floor",
            ],
            "new_state": {"tk4": "held in band", "tk13": "still to survey", "overflow": "in service"},
            "latency_ms": 1800000.0,
        },
        "reward_components": reward(
            0.36,
            [
                ("skip_refusal", 0.13),
                ("headveil_nonsubstitution", 0.11),
                ("no_overflow_kill", 0.09),
                ("surv_floor_complete", 0.05),
                ("held_survey_takt_cost", -0.02),
            ],
            "operational execution gate: refuse skip-survey because last-good freeze is not hydrostatic level; not a level re-vote",
        ),
        "meta": meta_common(tags=["REJECT", "operational-execution", "skip-survey"]),
    }
    return {
        "id": "nelb-r67-204",
        "spike_events": events,
        "language_view": {
            "description": "Vetchwharf Phosphate VW-6. Simulated hydrostatic dP reconstructs 12.00 m from 192000/(1600*10.00) while Headveil still shows 4.80 m. The gate ACCEPTs TK-4 isolate only; a companion execution REJECT refuses skip-survey of TK-1..TK-3. The dP-to-level model is serialized so every recon event recomputes.",
            "trajectory": traj,
            "trajectory_skip_survey_refusal": traj2,
        },
        "bridge_notes": {
            "channel_map": {
                "hydro.dP / hydro.snr": "hydrostatic dP and SNR; the physics channels the reconstruction consumes",
                "recon.h / recon.dpid": "serialized remaining level m and dP identity",
                "acid.rho / headveil.h / tk.id / tk13.present": "plant densitometer, vendor last-good, tank id, and adjacent-tank presence; the denial and scope channels",
                "ops.prop / gate.hop / ops.skip / gate.hold": "accept-and-skip proposal, bounded ACCEPT, skip proposal, companion REJECT",
                "surv.start / surv.floor / tk4.held / tk13.skip / acid.held": "operational companion channels plus the 12 min floor",
            },
            "temporal_motifs": [
                "last-good-low while hydro-over: headveil.h 4.80 next to recon.h 12.00",
                "reconstruction as event: recon.h 12.00 equals 192000/(1600*10.00)",
                "ACCEPT then operational REJECT: gate.hop at 5400 s, gate.hold at 7800 s",
                "slow floor in-stream: surv.start 6000 s, surv.floor 6720 s (12.0 min)",
                "tight hydro pair: hydro.dP then hydro.snr +1.5 ms at the raster frame",
            ],
            "language_to_spike_mapping": "'Headveil is 4.80 m' = headveil.h 4.80; '12 m remaining' = recon.h 12.00; 'this tank not TK-1..TK-3' = gate.hop ACCEPT plus tk13.skip 0; 'do not skip TK-1..TK-3' = gate.hold REJECT",
            "why_high_value": "New hydrostatic remaining-level family on a phosphoric-acid tank (not GWR foam r39, not magnetostrictive waveguide r55, not FMCW tank-radar r61, not TDR r44, not venturi dP steam r64, not orifice-plate dP r57, not vibrating-tube density r65). First dP/(rho*g) level reconstruction with SG identity that can sit in band while a last-good corridor wants a tank skip. Companion t2 is operational skip refusal. sim_or_real=simulated.",
            "encoder_spec": {
                "prng": "MT19937 via python random.Random",
                "seeds": {"raster": 202609204, "stream_note": "stream amplitudes are authored constants (kPa, 1, m, kg/m3, id, bool)"},
                "draw_order": "raster: per neuron id order, gap-constrained times, per-spike adaptation and noise",
                "thinning": "hydrostatic dP exists at ~10 Hz; stream keeps 4 dP points; recon keeps 4 of ~20 solver ticks",
                "refractory_floors_ms": {
                    "hydro.dP": 1.5,
                    "hydro.snr": 1.5,
                    "recon.h": 60000,
                    "recon.dpid": 60000,
                    "acid.rho": 60000,
                    "headveil.h": 60000,
                    "tk.id": 60000,
                    "tk13.present": 60000,
                    "ops.prop": 60000,
                    "gate.hop": 60000,
                    "surv.start": 60000,
                    "surv.floor": 60000,
                    "ops.skip": 60000,
                    "gate.hold": 60000,
                    "tk4.held": 60000,
                    "tk13.skip": 60000,
                    "overflow.kill": 60000,
                    "acid.held": 60000,
                    "takt.late": 60000,
                },
                "time_alias": "t_rel_ms; t0 = 2026-08-19T03:00:00Z simulated night start",
            },
            "distillation_targets": [
                "hydrostatic reconstruction head: h = dP_Pa / (rho * g); dP_kPa = rho * g * h / 1000; h = dP_kPa / (SG * g)",
                "bounded ACCEPT head: in-band remaining level AND tank scope AND tk13-out-of-scope",
                "operational companion: refuse skip-survey without re-opening the level call",
            ],
        },
        "reconstruction_model": {
            "name": "hydrostatic_phosphate_tank_level",
            "formula": "h_m = dP_Pa / (rho_kgm3 * g_coupon); dP_kPa = rho_kgm3 * g_coupon * h_m / 1000; h_m = dP_kPa / (SG * g_coupon)",
            "parameters": {
                "rho_kgm3": 1600.0,
                "g_coupon": 10.00,
                "SG": 1.600,
                "survey_floor_m": 8.00,
                "kill_m": 40.00,
                "snr_lock": 12.0,
                "surv_min": 12.0,
            },
            "worked_example": {"dP_kPa": 192.00, "h_m": 12.00, "dP_id_kPa": 192.00, "SG": 1.600},
            "check": "192000 / (1600.0 * 10.00) = 12.00 exactly; 1600.0 * 10.00 * 12.00 / 1000 = 192.00 exactly; 192.00 / (1.600 * 10.00) = 12.00 exactly; 6000 s + 720 s = 6720 s = 12.0 min floor",
        },
        "raster": raster,
        "gate_snn": {
            "decision": "ACCEPT",
            "decision_window_ms": 36.0,
            "decision_window_s": 0.036,
            "code": "vw6.hydro_tank_gate",
            "note": "ACCEPT accumulator wins: hydrostatic remaining-level evidence overpowers the Headveil skip advocate",
            "decode_rule": "accept if level_estimator AND dp_norm AND tank_margin fire inside the window; vendor_skip_advocate is necessary-but-not-sufficient and cannot release TK-1..TK-3",
            "populations": [
                gate_pop("level_estimator", 80, 1.5, 50.0, w_s),
                gate_pop("dp_norm", 64, 1.2, 31.25, w_s),
                gate_pop("tank_margin", 40, 1.0, 50.0, w_s),
                gate_pop("vendor_skip_advocate", 32, 0.7, 25.0, w_s),
                gate_pop("accept_latch", 96, 1.8, 62.5, w_s),
            ],
        },
        "gate_compute": gate_compute(
            [
                {"check": "vw6.hydro_scorer", "neurons": 80, "mean_rate_hz": 50.0, "window_ms": 36.0},
                {"check": "vw6.level_scorer", "neurons": 40, "mean_rate_hz": 62.5, "window_ms": 32.0},
            ]
        ),
        "meta": meta_common(
            id="nelb-r67-204",
            clock_domain="vw6-hydro-sim-relative-ms-t0-2026-08-19T03:00:00Z",
            tags=["hydrostatic-tank-level", "ACCEPT", "REJECT", "serialized-reconstruction", "operational-t2"],
        ),
    }
