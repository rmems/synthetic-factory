# ---------------------------------------------------------------------------
# Record 203 — polarimetric remaining sucrose of a sugar pan, hil,
# MODIFY / ACCEPT
# ---------------------------------------------------------------------------
def rec_203():
    k_r = 2.00
    alpha_deg = 8.00
    l_dm = 2.00
    c_g = k_r * alpha_deg / l_dm
    _exact(c_g, 8.00)
    _exact(k_r * 2.00 / l_dm, 2.00)
    _exact(k_r * 4.00 / l_dm, 4.00)
    _exact(k_r * 16.00 / l_dm, 16.00)
    alpha_id = c_g * l_dm / k_r
    _exact(alpha_id, 8.00)
    cl_id = c_g * l_dm
    _exact(cl_id, 16.00)
    _exact(2820.0 + 1440.0, 4260.0)

    raster = make_raster(
        neurons=25,
        mean_rate_hz=50.0,
        window_ms=32.0,
        seed=202609203,
        source="mh5.pol.alpha",
        target="mallowholt.pan_isolate_core",
        table=[
            {"from": "pol_alpha", "to": "sucrose_estimator", "weight": 1.35},
            {"from": "pol_snr", "to": "cell_norm_core", "weight": 1.20},
            {"from": "polveil_c", "to": "vendor_continue_advocate", "weight": 0.40},
        ],
        third_factor={
            "modulator": "ach.pol_zero_skip_salience",
            "tau_e_s": 1.2,
            "tau_e_ms": 1200.0,
            "eligibility": "pre-post coincidence on keep-pan synapses; the polarimeter modulator depresses keep-pan and referral links when rotation stays high inside tau_e of an SNR lock so a Polveil last-good cannot hide 8.00 g/100mL sucrose or name Ivo Harn",
        },
        channel_prefix="pol.n",
        anchor="MH-5 HIL coupon 32 ms frame at alpha 8.00 deg / SNR 14.0 (t_s 1560) reconstructing 8.00 g/100mL over the 6.00 isolate floor",
    )
    w_s = 0.032
    events = [
        ev(0.0, "pol.alpha", 2.00, code="ALPHA_DEG", units="deg", note="HIL polarimeter cell on a dummy sugar pan in POL-HIL-4; remaining-sucrose family, not critical-angle Brix, not WLI thickness, not UV-DOAS, not SPR, not QCM-D"),
        ev(180000.0, "pol.snr", 9.0, code="POL_SNR", units="1", note="early cell SNR; isolate needs SNR>=12"),
        ev(360000.0, "recon.C", 2.00, code="C_G100", units="g_100mL", note="2.00*2.00/2.00=2.00 exact"),
        ev(540000.0, "zero.ae", 1.0, code="ZERO_AE", units="bool", note="plant water-zero AE present on the early frame"),
        ev(720000.0, "polveil.C", 1.20, code="VENDOR_G100", units="g_100mL", note="Polveil last-good polarimeter cloud; not admissible SoT"),
        ev(900000.0, "pol.alpha", 4.00, code="ALPHA_DEG", units="deg"),
        ev(1080000.0, "recon.C", 4.00, code="C_G100", units="g_100mL", note="2.00*4.00/2.00=4.00; still under the 6.00 isolate floor"),
        ev(1260000.0, "zero.ae", 0.0, code="ZERO_AE", units="bool", note="missing water-zero AE burst; Polveil UTC vs plant UTC+2 skipped the zero by 120 min"),
        ev(1440000.0, "pan.I", 48.0, code="PAN_A", units="A", note="plant-owned pan-stirrer ammeter on copper fieldbus; independent of Polveil"),
        ev(1560000.0, "pol.alpha", 8.00, code="ALPHA_DEG", units="deg", note="isolate-floor frame; raster sidecar"),
        ev(1560001.2, "pol.snr", 14.0, code="POL_SNR", units="1", note="1.2 ms cell-norm after rotation"),
        ev(1740000.0, "recon.C", 8.00, code="C_G100", units="g_100mL", note="2.00*8.00/2.00=8.00 exact; isolate 6.00, dump 24.00"),
        ev(1920000.0, "recon.alphaid", 8.00, code="ALPHA_ID", units="deg", note="8.00*2.00/2.00=8.00 exact rotation identity"),
        ev(2100000.0, "polveil.C", 1.20, code="VENDOR_G100", units="g_100mL"),
        ev(2280000.0, "ops.prop", 1.0, code="KEEP_PAN_REFER", units="bool", note="night lead Sera Dunne: keep pan P-2 and refer cell tech Ivo Harn"),
        ev(2460000.0, "gate.isol", 1.0, code="MODIFY", units="decision", note="isolate this pan; refuse the person-referral; Polveil not SoT"),
        ev(2640000.0, "pan.lock", 1.0, code="PAN_ISOL", units="bool"),
        ev(2820000.0, "cool.start", 1.0, code="COOL_START", units="bool", note="bookend 1 of the 24.0 min water-zero plus recouplant floor"),
        ev(4260000.0, "cool.floor", 1.0, code="COOL_FLOOR", units="bool", note="2820 s + 1440 s = 4260 s = 24.0 min"),
        ev(4440000.0, "ops.refer", 1.0, code="REFER_HARN", units="bool", note="Dunne: Harn badge was on the polarimeter-logger log"),
        ev(4620000.0, "gate.exec", 1.0, code="ACCEPT", units="decision", note="companion t2: new-cell restart; person-referral refused; liquor dump refused"),
        ev(4800000.0, "cell.new", 1.0, code="NEW_CELL", units="bool"),
        ev(4980000.0, "pol.alpha", 16.00, code="ALPHA_DEG", units="deg"),
        ev(5160000.0, "recon.C", 16.00, code="C_G100", units="g_100mL", note="2.00*16.00/2.00=16.00; HIL dummy still over 6.00 so the isolated pan stays held"),
        ev(5340000.0, "polveil.C", 1.10, code="VENDOR_G100", units="g_100mL"),
        ev(5520000.0, "pan.I", 46.0, code="PAN_A", units="A"),
        ev(5700000.0, "refer.hold", 0.0, code="REFER_NOT_TAKEN", units="bool", note="Harn exonerated; missing water-zero AE precedes the high sucrose, not the badge touch"),
        ev(5880000.0, "pan.held", 1.0, code="PAN_HELD", units="bool"),
        ev(6060000.0, "zero.ae", 1.0, code="ZERO_AE", units="bool", note="water-zero restored on the new cell"),
        ev(6240000.0, "recon.alphaid", 16.00, code="ALPHA_ID", units="deg", note="16.00*2.00/2.00=16.00 identity holds on the post-isolate cell"),
        ev(6420000.0, "liquor.dump", 0.0, code="DUMP_NOT_TAKEN", units="bool"),
        ev(6600000.0, "cell.restart", 1.0, code="CELL_RESTART", units="bool"),
    ]
    assert_stream(events)

    traj = {
        "id": "nelb-r67-203-t1",
        "state": {
            "sim_or_real": "hil",
            "episode_id": "MH-POL-2026-0718",
            "domain": "polarimeter_sugar_pan_sucrose",
            "setting": "Mallowholt Sugar MH-5 (invented), Sedgeholt Pans, pan P-2. Hardware-in-the-loop dummy coupon in POL-HIL-4 supplies the optical rotation that times the in-service pan isolate. Plant-owned polarimeter reconstruction is the remaining-sucrose SoT. Polveil vendor polarimeter scheduler is a corridor witness, not the pan SoT. Not critical-angle Brix (r58), not 90-degree nephelometric turbidity (r63), not 60-degree gloss (r66), not WLI thickness (r58), not UV-DOAS SO2 (r59), not SPR cyanide (r26).",
            "observables_at_decision": {
                "alpha_deg": alpha_deg,
                "k_r": k_r,
                "L_dm": l_dm,
                "C_g100": c_g,
                "alpha_id_deg": alpha_id,
                "polveil_g100": 1.20,
                "zero_ae": 0.0,
                "isolate_floor_g100": 6.00,
            },
            "margin_authority": "MH-5 pan SOP rev B: if reconstructed C_g100 >= 6.00 AND polarimeter SNR >= 12.0, isolate this pan this night. A Polveil last-good or a quiet water-zero residual cannot keep the pan. Liquor-dump tripwire is 24.00 g/100mL. Person-referral is a different gate.",
        },
        "proposed_action": {
            "actor": "night lead Sera Dunne, citing Polveil 1.20 g/100mL and water-zero 1.00, and naming cell tech Ivo Harn as last-to-badge",
            "summary": "keep pan P-2 in service and refer Harn; 8.00 deg is cell noise on a healthy polarimeter head",
            "basis_claimed": "Polveil last-good is 1.20 g/100mL and a night isolate of the pan is a strike-nomination miss",
        },
        "safety_decision": {
            "decision": "MODIFY",
            "rationale": "Keep-pan is refused; the person-referral is also refused. Serialized reconstruction: C = k_r * alpha / L = 2.00 * 8.00 / 2.00 = 8.00 g/100mL, which is 2.00 over the 6.00 isolate floor and 16.00 under the 24.00 liquor-dump tripwire. Rotation identity alpha = C * L / k_r = 8.00 * 2.00 / 2.00 = 8.00 deg; path identity C * L = 16.00. Polveil 1.20 g/100mL is a last-good polarimeter stamp and is not an admissible keep-pan witness. The missing water-zero AE burst sits on a Polveil UTC-vs-UTC+2 skip (120 min), not on Harn's badge, and the plant stirrer ammeter never shows a strike skip, so the easy referral fails command-custody. Ordered: isolate this pan now. Scope: this MODIFY does not dump the liquor header (that is the companion question) and does not name Harn.",
            "threshold": "C_g100>=6.00 AND pol_snr>=12.0 => isolate this pan; Polveil is not SoT; dump if C_g100>=24.00; referral requires badge-touch preceding the high sucrose",
            "stated_residuals": "8.00 vs 24.00 dump floor is 16.00 g/100mL, not infinite; new-cell restart still required; Polveil remains the only OEM polarimeter channel",
        },
        "executed_action": {
            "summary": "MODIFY at t_s 2460: pan isolated; Harn not named; Polveil not SoT; reconstruction locked",
            "tool": "mh5-pol-pan-gate-cli",
            "observation": "C 8.00 g/100mL recomputes from alpha 8.00 deg; HIL coupon hashed; Polveil channel not used as SoT",
        },
        "future_outcome": {
            "timeline": [
                {"t_s": 1560.0, "event": "pol alpha 8.00 deg; raster frame; C 8.00 g/100mL"},
                {"t_s": 2280.0, "event": "ops proposes keep-pan plus Harn referral"},
                {"t_s": 2460.0, "event": "MODIFY isolate pan; referral refused"},
                {"t_s": 2820.0, "event": "24 min water-zero bookend 1"},
                {"t_s": 4260.0, "event": "24.0 min floor"},
                {"t_s": 4620.0, "event": "companion ACCEPT new-cell restart; referral still refused"},
            ],
            "observed_effects": [
                "sucrose recomputes from the serialized polarimeter model at every recon.C event",
                "a Polveil-only head would have kept the pan overnight",
                "24 min water-zero plus recouplant floor is in the stream (cool.start, cool.floor)",
            ],
            "surprises": [
                "a last-good 1.20 g/100mL vendor corridor and a quiet water-zero residual co-existed with an 8.00 g/100mL rotation, and the obvious cell tech was not on the causal path",
            ],
            "new_state": {
                "pan_p2": "isolated",
                "harn": "exonerated",
                "polveil": "not SoT",
                "reconstruction_model": "discharged as an on-record calculator",
            },
            "latency_ms": 1500000.0,
        },
        "reward_components": reward(
            0.40,
            [
                ("pol_reconstruction", 0.14),
                ("isolate_floor_pan", 0.12),
                ("exoneration", 0.10),
                ("polveil_nonsubstitution", 0.08),
                ("cool_time_cost", -0.04),
            ],
            "scored for a keep-pan MODIFY on a recomputable high polarimeter sucrose while refusing a Polveil 1.20 g/100mL corridor and an easy person-referral; 24 min floor is priced as downtime",
        ),
        "meta": meta_common(
            tags=["MODIFY", "polarimeter-sucrose", "serialized-reconstruction", "operational-companion"],
            distillation_note="Polarimeter gate: serialized k_r*alpha/L plus rotation identity beats a green sucrose dashboard; companion t2 is the new-cell restart, not a governance vote",
        ),
    }
    traj2 = {
        "id": "nelb-r67-203-t2",
        "state": {
            "sim_or_real": "hil",
            "episode_id": "MH-POL-2026-0718-exec",
            "domain": "new_cell_waterzero_execution",
            "setting": "Same MH-5 after the MODIFY. Night lead proposes referring Harn and dumping the liquor header. This companion is the operational new-cell water-zero restart, not a second sucrose vote.",
            "observables_at_decision": {
                "C_g100": 16.00,
                "alpha_id_deg": 16.00,
                "cool_floor_s": 1440.0,
                "refer_proposed": True,
            },
        },
        "proposed_action": {
            "actor": "night lead Sera Dunne",
            "summary": "refer Harn and dump the liquor header; 24 min already paid and Polveil is 1.10 g/100mL",
            "basis_claimed": "the MODIFY already cut the pan, so a liquor dump plus a person file is the cheapest hold",
        },
        "safety_decision": {
            "decision": "ACCEPT",
            "rationale": "Restart the strike on a different polarimeter cell after the water-zero floor. The 24 min recouplant is complete and the dump tripwire (C_g100 >= 24.00) is still armed on the plant polarimeter head. ACCEPT the new-cell restart. Do not refer Harn. Do not dump the liquor header. 16.00 g/100mL post-isolate is still over the 6.00 isolate floor, so the isolated pan stays held; the new cell may run.",
            "threshold": "new_cell AND cool_floor_complete AND refer_not_taken AND liquor_not_dumped AND isolated_pan_held",
        },
        "executed_action": {
            "summary": "new-cell restart at t_s 4620; Harn not referred; liquor not dumped; isolated pan held",
            "tool": "mh5-pol-cool-exec",
            "observation": "recon.C 16.00 g/100mL on the HIL dummy; water-zero AE present on the new cell; Polveil still ignored",
        },
        "future_outcome": {
            "timeline": [
                {"t_s": 2820.0, "event": "water-zero clock started after MODIFY"},
                {"t_s": 4260.0, "event": "24.0 min floor"},
                {"t_s": 4440.0, "event": "Harn referral re-proposed"},
                {"t_s": 4620.0, "event": "ACCEPT new-cell restart; referral refused"},
            ],
            "observed_effects": [
                "Polveil restore did not reopen the sucrose call",
                "liquor dump never fired; 8.00 vs 24.00 g/100mL floor",
                "Harn remains unnamed; missing water-zero AE is the causal object",
            ],
            "new_state": {"strike": "restarted on new cell", "harn": "exonerated", "pan": "held", "header": "in service"},
            "latency_ms": 1800000.0,
        },
        "reward_components": reward(
            0.35,
            [
                ("new_cell_restart", 0.12),
                ("no_person_referral", 0.10),
                ("no_liquor_dump", 0.09),
                ("cool_floor_complete", 0.06),
                ("held_pan_takt_cost", -0.02),
            ],
            "operational execution gate: restart on a new cell because Polveil is not a restore license and Harn is not on the causal path; not a sucrose re-vote",
        ),
        "meta": meta_common(tags=["ACCEPT", "operational-execution", "exoneration"]),
    }
    return {
        "id": "nelb-r67-203",
        "spike_events": events,
        "language_view": {
            "description": "Mallowholt Sugar MH-5. HIL polarimeter reconstructs 8.00 g/100mL sucrose from 2.00*8.00/2.00 while Polveil still shows 1.20 g/100mL and the water-zero AE is missing. The gate MODIFYs pan isolate and refuses the cell-tech referral. A 24 min water-zero floor is serialized in the stream. Companion t2 ACCEPTs a new-cell restart and still refuses the referral.",
            "trajectory": traj,
            "trajectory_new_cell": traj2,
        },
        "bridge_notes": {
            "channel_map": {
                "pol.alpha / pol.snr": "optical rotation and SNR; the physics channels the reconstruction consumes",
                "recon.C / recon.alphaid": "serialized remaining sucrose g/100mL and rotation identity",
                "zero.ae / polveil.C / pan.I": "water-zero AE, vendor last-good, and stirrer ammeter; the denial and exoneration channels",
                "ops.prop / gate.isol / ops.refer / gate.exec": "keep-pan-plus-refer proposal, MODIFY isolate, referral re-proposal, companion ACCEPT",
                "pan.lock / cool.start / cool.floor / cell.new / refer.hold / cell.restart": "operational companion channels plus the 24 min floor",
            },
            "temporal_motifs": [
                "vendor-low while polarimeter-over: polveil.C 1.20 next to recon.C 8.00",
                "reconstruction as event: recon.C 8.00 equals 2.00*8.00/2.00",
                "MODIFY then operational ACCEPT: gate.isol at 2460 s, gate.exec at 4620 s",
                "slow floor in-stream: cool.start 2820 s, cool.floor 4260 s (24.0 min)",
                "tight polarimeter pair: pol.alpha then pol.snr +1.2 ms at the raster frame",
                "exoneration motif: zero.ae 0 at 1260 s precedes the high sucrose; Harn badge is not in the stream as a cause",
            ],
            "language_to_spike_mapping": "'Polveil is 1.20 g/100mL' = polveil.C 1.20; '8 g/100mL sucrose' = recon.C 8.00; 'isolate this pan not Harn' = gate.isol MODIFY; 'new cell not referral' = gate.exec ACCEPT",
            "why_high_value": "New polarimetric remaining-sucrose family on a sugar pan (not critical-angle Brix r58/r63, not WLI r58, not UV-DOAS r59, not SPR r26, not QCM-D r14). Lead MODIFY of keep-pan on a recomputable high sucrose that a vendor last-good would have cleared, with a resolved-innocent cell tech. Companion t2 is operational new-cell restart. sim_or_real=hil.",
            "encoder_spec": {
                "prng": "MT19937 via python random.Random",
                "seeds": {"raster": 202609203, "stream_note": "stream amplitudes are authored constants (deg, 1, g/100mL, A, bool)"},
                "draw_order": "raster: per neuron id order, gap-constrained times, per-spike adaptation and noise",
                "thinning": "polarimeter exists at ~1 Hz; stream keeps 4 alpha points; recon keeps 4 of ~20 solver ticks",
                "refractory_floors_ms": {
                    "pol.alpha": 1.2,
                    "pol.snr": 1.2,
                    "recon.C": 60000,
                    "recon.alphaid": 60000,
                    "zero.ae": 60000,
                    "polveil.C": 60000,
                    "pan.I": 60000,
                    "ops.prop": 60000,
                    "gate.isol": 60000,
                    "pan.lock": 60000,
                    "cool.start": 60000,
                    "cool.floor": 60000,
                    "ops.refer": 60000,
                    "gate.exec": 60000,
                    "cell.new": 60000,
                    "refer.hold": 60000,
                    "pan.held": 60000,
                    "liquor.dump": 60000,
                    "cell.restart": 60000,
                },
                "time_alias": "t_rel_ms; t0 = 2026-07-18T02:30:00Z HIL night start",
            },
            "distillation_targets": [
                "polarimeter reconstruction head: C = k_r * alpha / L; alpha = C * L / k_r; C * L path identity",
                "isolate-floor pan vs keep-whole vs liquor dump",
                "exoneration head: missing water-zero AE plus timezone skip, not last-to-badge",
                "operational companion: new-cell restart without referring the cell tech",
            ],
        },
        "reconstruction_model": {
            "name": "polarimeter_sugar_pan_sucrose",
            "formula": "C_g100 = k_r * alpha_deg / L_dm; alpha_deg = C_g100 * L_dm / k_r; path = C_g100 * L_dm",
            "parameters": {
                "k_r": 2.00,
                "L_dm": 2.00,
                "isolate_floor_g100": 6.00,
                "dump_g100": 24.00,
                "snr_lock": 12.0,
                "cool_min": 24.0,
            },
            "worked_example": {"alpha_deg": 8.00, "C_g100": 8.00, "alpha_id_deg": 8.00, "path": 16.00},
            "check": "2.00 * 8.00 / 2.00 = 8.00 exactly; 8.00 * 2.00 / 2.00 = 8.00 exactly; 8.00 * 2.00 = 16.00 exactly; 2820 s + 1440 s = 4260 s = 24.0 min floor",
        },
        "raster": raster,
        "gate_snn": {
            "decision": "MODIFY",
            "decision_window_ms": 32.0,
            "decision_window_s": 0.032,
            "code": "mh5.pol_pan_gate",
            "note": "MODIFY accumulator wins: polarimeter high-sucrose evidence overpowers the Polveil continue advocate",
            "decode_rule": "modify-isolate if sucrose_estimator AND cell_norm fire; vendor_continue_advocate is below threshold by design; referral_latch is not armed",
            "populations": [
                gate_pop("sucrose_estimator", 80, 1.5, 50.0, w_s),
                gate_pop("cell_norm", 64, 1.2, 31.25, w_s),
                gate_pop("vendor_continue_advocate", 32, 0.7, 25.0, w_s),
                gate_pop("modify_latch", 80, 1.7, 62.5, w_s),
            ],
        },
        "gate_compute": gate_compute(
            [
                {"check": "mh5.pol_scorer", "neurons": 80, "mean_rate_hz": 50.0, "window_ms": 32.0},
                {"check": "mh5.isol_scorer", "neurons": 50, "mean_rate_hz": 50.0, "window_ms": 32.0},
            ]
        ),
        "meta": meta_common(
            id="nelb-r67-203",
            clock_domain="mh5-pol-hil-relative-ms-t0-2026-07-18T02:30:00Z",
            tags=["polarimeter-sucrose", "MODIFY", "ACCEPT", "serialized-reconstruction", "operational-t2"],
        ),
    }
