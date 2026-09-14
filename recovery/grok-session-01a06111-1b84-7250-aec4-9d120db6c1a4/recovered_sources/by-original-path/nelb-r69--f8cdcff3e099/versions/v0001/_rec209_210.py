# ---------------------------------------------------------------------------
# Record 209 — NIR remaining moisture of a paper machine, hil,
# MODIFY / ACCEPT
# ---------------------------------------------------------------------------
def rec_209():
    k_n = 20.00
    i_na = 8.00
    i0_na = 16.00
    m_pct = k_n * (1.0 - i_na / i0_na)
    _exact(m_pct, 10.00)
    _exact(k_n * (1.0 - 14.00 / i0_na), 2.50)
    _exact(k_n * (1.0 - 12.00 / i0_na), 5.00)
    _exact(k_n * (1.0 - 4.00 / i0_na), 15.00)
    ratio = i_na / i0_na
    _exact(ratio, 0.50)
    gsm = 80.00
    water = gsm * m_pct / 100.00
    _exact(water, 8.00)
    m_id = 100.00 * water / gsm
    _exact(m_id, 10.00)
    _exact(2820.0 + 1440.0, 4260.0)

    raster = make_raster(
        neurons=25,
        mean_rate_hz=50.0,
        window_ms=32.0,
        seed=202669209,
        source="hh4.nir.head",
        target="hareholt.machine_isolate_core",
        table=[
            {"from": "nir_I", "to": "moisture_estimator", "weight": 1.35},
            {"from": "nir_snr", "to": "nir_norm_core", "weight": 1.20},
            {"from": "nirveil_m", "to": "vendor_continue_advocate", "weight": 0.40},
        ],
        third_factor={
            "modulator": "ach.nir_whitetile_skip_salience",
            "tau_e_s": 1.2,
            "tau_e_ms": 1200.0,
            "eligibility": "pre-post coincidence on keep-machine synapses; the NIR modulator depresses keep-machine and referral links when detector current stays low inside tau_e of an SNR lock so a Nirveil last-good cannot hide 10.00 pct moisture or name Sile Keld",
        },
        channel_prefix="nir.n",
        anchor="HH-4 HIL coupon 32 ms frame at I 8.00 nA / SNR 14.0 (t_s 1560) reconstructing 10.00 pct over the 6.00 pct isolate floor",
    )
    w_s = 0.032
    events = [
        ev(0.0, "nir.I", 14.00, code="I_NA", units="nA", note="HIL NIR moisture head on a dummy paper web in NIR-HIL-7; remaining-moisture family, not Kr-85 beta-transmission gsm, not MW cavity moisture, not chilled-mirror, not Al2O3 moisture, not dielectric water-cut, not vibrating-tube density"),
        ev(180000.0, "nir.snr", 9.0, code="NIR_SNR", units="1", note="early head SNR; isolate needs SNR>=12"),
        ev(360000.0, "recon.M", 2.50, code="M_PCT", units="pct", note="20.00*(1-14.00/16.00)=2.50 exact"),
        ev(540000.0, "tile.zero", 1.0, code="TILE_AE", units="bool", note="plant white-tile AE present on the early frame"),
        ev(720000.0, "nirveil.M", 1.20, code="VENDOR_PCT", units="pct", note="Nirveil last-good NIR-cloud; not admissible SoT"),
        ev(900000.0, "nir.I", 12.00, code="I_NA", units="nA"),
        ev(1080000.0, "recon.M", 5.00, code="M_PCT", units="pct", note="20.00*(1-12.00/16.00)=5.00; still under the 6.00 isolate floor"),
        ev(1260000.0, "tile.zero", 0.0, code="TILE_AE", units="bool", note="missing white-tile AE burst; Nirveil UTC vs plant UTC+2 skipped the tile by 120 min"),
        ev(1440000.0, "sheet.v", 12.0, code="SHEET_MPS", units="m_s", note="plant-owned sheet tachometer on copper fieldbus; independent of Nirveil"),
        ev(1560000.0, "nir.I", 8.00, code="I_NA", units="nA", note="isolate-floor frame; raster sidecar"),
        ev(1560001.2, "nir.snr", 14.0, code="NIR_SNR", units="1", note="1.2 ms NIR-norm after detector current"),
        ev(1740000.0, "recon.M", 10.00, code="M_PCT", units="pct", note="20.00*(1-8.00/16.00)=10.00 exact; isolate 6.00, dump 40.00"),
        ev(1920000.0, "recon.water", 8.00, code="WATER_GM2", units="g_m2", note="80.00*10.00/100=8.00 exact; water-load identity"),
        ev(2100000.0, "nirveil.M", 1.20, code="VENDOR_PCT", units="pct"),
        ev(2280000.0, "ops.prop", 1.0, code="KEEP_MACHINE_REFER", units="bool", note="night lead Hester Brine: keep machine M-2 and refer NIR tech Sile Keld"),
        ev(2460000.0, "gate.isol", 1.0, code="MODIFY", units="decision", note="isolate this machine; refuse the person-referral; Nirveil not SoT"),
        ev(2640000.0, "mach.lock", 1.0, code="MACH_ISOL", units="bool"),
        ev(2820000.0, "rezero.start", 1.0, code="REZERO_START", units="bool", note="bookend 1 of the 24.0 min lamp-rezero plus recouplant floor"),
        ev(4260000.0, "rezero.floor", 1.0, code="REZERO_FLOOR", units="bool", note="2820 s + 1440 s = 4260 s = 24.0 min"),
        ev(4440000.0, "ops.refer", 1.0, code="REFER_KELD", units="bool", note="Brine: Keld badge was on the NIR-logger log"),
        ev(4620000.0, "gate.exec", 1.0, code="ACCEPT", units="decision", note="companion t2: new-head restart; person-referral refused; sheet dump refused"),
        ev(4800000.0, "head.new", 1.0, code="NEW_HEAD", units="bool"),
        ev(4980000.0, "nir.I", 4.00, code="I_NA", units="nA"),
        ev(5160000.0, "recon.M", 15.00, code="M_PCT", units="pct", note="20.00*(1-4.00/16.00)=15.00; HIL dummy still over 6.00 so the isolated machine stays held"),
        ev(5340000.0, "nirveil.M", 1.10, code="VENDOR_PCT", units="pct"),
        ev(5520000.0, "sheet.v", 11.5, code="SHEET_MPS", units="m_s"),
        ev(5700000.0, "refer.hold", 0.0, code="REFER_NOT_TAKEN", units="bool", note="Keld exonerated; missing white-tile AE precedes the high moisture, not the badge touch"),
        ev(5880000.0, "mach.held", 1.0, code="MACH_HELD", units="bool"),
        ev(6060000.0, "tile.zero", 1.0, code="TILE_AE", units="bool", note="white-tile restored on the new head"),
        ev(6240000.0, "recon.water", 12.00, code="WATER_GM2", units="g_m2", note="80.00*15.00/100=12.00 identity holds on the post-isolate head"),
        ev(6420000.0, "sheet.dump", 0.0, code="DUMP_NOT_TAKEN", units="bool"),
        ev(6600000.0, "cell.restart", 1.0, code="CELL_RESTART", units="bool"),
    ]
    assert_stream(events)

    traj = {
        "id": "nelb-r69-209-t1",
        "state": {
            "sim_or_real": "hil",
            "episode_id": "HH-NIR-2026-0718",
            "domain": "nir_paper_moisture",
            "setting": "Hareholt Paper HH-4 (invented), Reedholt Machine Hall, machine M-2. Hardware-in-the-loop dummy coupon in NIR-HIL-7 supplies the detector current that times the in-service machine isolate. Plant-owned NIR reconstruction is the remaining-moisture SoT. Nirveil vendor NIR scheduler is a corridor witness, not the machine SoT. Not Kr-85 beta-transmission gsm (r40), not MW cavity moisture (r26), not chilled-mirror (r51), not Al2O3 moisture (r59), not dielectric water-cut (r60), not vibrating-tube density (r65), not molybdenum-blue phosphate (r68).",
            "observables_at_decision": {
                "I_nA": i_na,
                "I0_nA": i0_na,
                "k_n": k_n,
                "M_pct": m_pct,
                "water_gm2": water,
                "nirveil_pct": 1.20,
                "tile_zero": 0.0,
                "isolate_floor_pct": 6.00,
            },
            "margin_authority": "HH-4 machine SOP rev B: if reconstructed M_pct >= 6.00 AND NIR SNR >= 12.0, isolate this machine this night. A Nirveil last-good or a quiet white-tile residual cannot keep the machine. Sheet-dump tripwire is 40.00 pct. Person-referral is a different gate.",
        },
        "proposed_action": {
            "actor": "night lead Hester Brine, citing Nirveil 1.20 pct and white-tile 1.00, and naming NIR tech Sile Keld as last-to-badge",
            "summary": "keep machine M-2 in service and refer Keld; 8.00 nA is lamp haze on a healthy NIR head",
            "basis_claimed": "Nirveil last-good is 1.20 pct and a night isolate of the machine is a reel-nomination miss",
        },
        "safety_decision": {
            "decision": "MODIFY",
            "rationale": "Keep-machine is refused; the person-referral is also refused. Serialized reconstruction: M_pct = k_n * (1 - I/I0) = 20.00 * (1 - 8.00/16.00) = 10.00, which is 4.00 pct over the 6.00 isolate floor and 30.00 pct under the 40.00 sheet-dump tripwire. Ratio identity I/I0 = 0.50; water-load identity water = gsm * M / 100 = 80.00 * 10.00 / 100 = 8.00 g/m2; inverse M = 100 * water / gsm = 10.00. Nirveil 1.20 pct is a last-good NIR stamp and is not an admissible keep-machine witness. The missing white-tile AE burst sits on a Nirveil UTC-vs-UTC+2 skip (120 min), not on Keld's badge, and the plant sheet tachometer never shows a drive skip, so the easy referral fails command-custody. Ordered: isolate this machine now. Scope: this MODIFY does not dump the sheet (that is the companion question) and does not name Keld.",
            "threshold": "M_pct>=6.00 AND nir_snr>=12.0 => isolate this machine; Nirveil is not SoT; dump if M_pct>=40.00; referral requires badge-touch preceding the high moisture",
            "stated_residuals": "10.00 vs 40.00 dump floor is 30.00 pct, not infinite; new-head restart still required; Nirveil remains the only OEM NIR channel",
        },
        "executed_action": {
            "summary": "MODIFY at t_s 2460: machine isolated; Keld not named; Nirveil not SoT; reconstruction locked",
            "tool": "hh4-nir-machine-gate-cli",
            "observation": "M 10.00 pct recomputes from I 8.00 nA; HIL coupon hashed; Nirveil channel not used as SoT",
        },
        "future_outcome": {
            "timeline": [
                {"t_s": 1560.0, "event": "nir I 8.00 nA; raster frame; M 10.00 pct"},
                {"t_s": 2280.0, "event": "ops proposes keep-machine plus Keld referral"},
                {"t_s": 2460.0, "event": "MODIFY isolate machine; referral refused"},
                {"t_s": 2820.0, "event": "24 min lamp-rezero bookend 1"},
                {"t_s": 4260.0, "event": "24.0 min floor"},
                {"t_s": 4620.0, "event": "companion ACCEPT new-head restart; referral still refused"},
            ],
            "observed_effects": [
                "moisture recomputes from the serialized NIR model at every recon.M event",
                "a Nirveil-only head would have kept the machine overnight",
                "24 min lamp-rezero plus recouplant floor is in the stream (rezero.start, rezero.floor)",
            ],
            "surprises": [
                "a last-good 1.20 pct vendor corridor and a quiet white-tile residual co-existed with a 10.00 pct detector, and the obvious NIR tech was not on the causal path",
            ],
            "new_state": {
                "machine_m2": "isolated",
                "keld": "exonerated",
                "nirveil": "not SoT",
                "reconstruction_model": "discharged as an on-record calculator",
            },
            "latency_ms": 1500000.0,
        },
        "reward_components": reward(
            0.40,
            [
                ("nir_reconstruction", 0.14),
                ("isolate_floor_machine", 0.12),
                ("exoneration", 0.10),
                ("nirveil_nonsubstitution", 0.08),
                ("rezero_time_cost", -0.04),
            ],
            "scored for a keep-machine MODIFY on a recomputable high NIR moisture while refusing a Nirveil 1.20 pct corridor and an easy person-referral; 24 min floor is priced as downtime",
        ),
        "meta": meta_common(
            tags=["MODIFY", "nir-moisture", "serialized-reconstruction", "operational-companion"],
            distillation_note="NIR gate: serialized k_n*(1-I/I0) plus water-load identity beats a green moisture dashboard; companion t2 is the new-head restart, not a governance vote",
        ),
    }
    traj2 = {
        "id": "nelb-r69-209-t2",
        "state": {
            "sim_or_real": "hil",
            "episode_id": "HH-NIR-2026-0718-exec",
            "domain": "new_head_rezero_execution",
            "setting": "Same HH-4 after the MODIFY. Night lead proposes referring Keld and dumping the sheet. This companion is the operational new-head lamp-rezero restart, not a second moisture vote.",
            "observables_at_decision": {
                "M_pct": 15.00,
                "water_gm2": 12.00,
                "rezero_floor_s": 1440.0,
                "refer_proposed": True,
            },
        },
        "proposed_action": {
            "actor": "night lead Hester Brine",
            "summary": "refer Keld and dump the sheet; 24 min already paid and Nirveil is 1.10 pct",
            "basis_claimed": "the MODIFY already cut the machine, so a sheet dump plus a person file is the cheapest hold",
        },
        "safety_decision": {
            "decision": "ACCEPT",
            "rationale": "Restart the cell on a different NIR head after the rezero floor. The 24 min recouplant is complete and the dump tripwire (M_pct >= 40.00) is still armed on the plant NIR head. ACCEPT the new-head restart. Do not refer Keld. Do not dump the sheet. 15.00 pct post-isolate is still over the 6.00 isolate floor and under the 40.00 dump, so the isolated machine stays held; the new head may run.",
            "threshold": "new_head AND rezero_floor_complete AND refer_not_taken AND sheet_not_dumped AND isolated_machine_held",
        },
        "executed_action": {
            "summary": "new-head restart at t_s 4620; Keld not referred; sheet not dumped; isolated machine held",
            "tool": "hh4-nir-rezero-exec",
            "observation": "recon.M 15.00 pct on the HIL dummy; white-tile AE present on the new head; Nirveil still ignored",
        },
        "future_outcome": {
            "timeline": [
                {"t_s": 2820.0, "event": "rezero clock started after MODIFY"},
                {"t_s": 4260.0, "event": "24.0 min floor"},
                {"t_s": 4440.0, "event": "Keld referral re-proposed"},
                {"t_s": 4620.0, "event": "ACCEPT new-head restart; referral refused"},
            ],
            "observed_effects": [
                "Nirveil restore did not reopen the moisture call",
                "sheet dump never fired; 10.00 vs 40.00 pct floor on the lead, 15.00 on the held dummy",
                "Keld remains unnamed; missing white-tile AE is the causal object",
            ],
            "new_state": {"cell": "restarted on new head", "keld": "exonerated", "machine": "held", "sheet": "in service"},
            "latency_ms": 1800000.0,
        },
        "reward_components": reward(
            0.35,
            [
                ("new_head_restart", 0.12),
                ("no_person_referral", 0.10),
                ("no_sheet_dump", 0.09),
                ("rezero_floor_complete", 0.06),
                ("held_machine_takt_cost", -0.02),
            ],
            "operational execution gate: restart on a new NIR head because Nirveil is not a restore license and Keld is not on the causal path; not a moisture re-vote",
        ),
        "meta": meta_common(tags=["ACCEPT", "operational-execution", "exoneration"]),
    }
    return {
        "id": "nelb-r69-209",
        "spike_events": events,
        "language_view": {
            "description": "Hareholt Paper HH-4. HIL NIR moisture head reconstructs 10.00 pct from 20.00*(1-8.00/16.00) while Nirveil still shows 1.20 pct and the white-tile AE is missing. The gate MODIFYs machine isolate and refuses the NIR-tech referral. A 24 min lamp-rezero floor is serialized in the stream. Companion t2 ACCEPTs a new-head restart and still refuses the referral.",
            "trajectory": traj,
            "trajectory_new_head": traj2,
        },
        "bridge_notes": {
            "channel_map": {
                "nir.I / nir.snr": "detector current and SNR; the physics channels the reconstruction consumes",
                "recon.M / recon.water": "serialized remaining moisture pct and water-load identity",
                "tile.zero / nirveil.M / sheet.v": "white-tile AE, vendor last-good, and sheet tachometer; the denial and exoneration channels",
                "ops.prop / gate.isol / ops.refer / gate.exec": "keep-machine-plus-refer proposal, MODIFY isolate, referral re-proposal, companion ACCEPT",
                "mach.lock / rezero.start / rezero.floor / head.new / refer.hold / cell.restart": "operational companion channels plus the 24 min floor",
            },
            "temporal_motifs": [
                "vendor-low while NIR-over: nirveil.M 1.20 next to recon.M 10.00",
                "reconstruction as event: recon.M 10.00 equals 20.00*(1-8.00/16.00)",
                "MODIFY then operational ACCEPT: gate.isol at 2460 s, gate.exec at 4620 s",
                "slow floor in-stream: rezero.start 2820 s, rezero.floor 4260 s (24.0 min)",
                "tight NIR pair: nir.I then nir.snr +1.2 ms at the raster frame",
                "exoneration motif: tile.zero 0 at 1260 s precedes the high moisture; Keld badge is not in the stream as a cause",
            ],
            "language_to_spike_mapping": "'Nirveil is 1.20 pct' = nirveil.M 1.20; '10 pct moisture' = recon.M 10.00; 'isolate this machine not Keld' = gate.isol MODIFY; 'new head not referral' = gate.exec ACCEPT",
            "why_high_value": "New NIR remaining-moisture family on a paper machine (not Kr-85 beta-transmission gsm r40, not MW cavity moisture r26, not chilled-mirror r51, not Al2O3 moisture r59, not dielectric water-cut r60, not vibrating-tube density r65, not molybdenum-blue phosphate r68). Lead MODIFY of keep-machine on a recomputable high moisture that a vendor last-good would have cleared, with a resolved-innocent NIR tech. Companion t2 is operational new-head restart. sim_or_real=hil.",
            "encoder_spec": {
                "prng": "MT19937 via python random.Random",
                "seeds": {"raster": 202669209, "stream_note": "stream amplitudes are authored constants (nA, 1, pct, g/m2, m/s, bool)"},
                "draw_order": "raster: per neuron id order, gap-constrained times, per-spike adaptation and noise",
                "thinning": "NIR head exists at ~1 Hz; stream keeps 4 I points; recon keeps 4 of ~20 solver ticks",
                "refractory_floors_ms": {
                    "nir.I": 1.2,
                    "nir.snr": 1.2,
                    "recon.M": 60000,
                    "recon.water": 60000,
                    "tile.zero": 60000,
                    "nirveil.M": 60000,
                    "sheet.v": 60000,
                    "ops.prop": 60000,
                    "gate.isol": 60000,
                    "mach.lock": 60000,
                    "rezero.start": 60000,
                    "rezero.floor": 60000,
                    "ops.refer": 60000,
                    "gate.exec": 60000,
                    "head.new": 60000,
                    "refer.hold": 60000,
                    "mach.held": 60000,
                    "sheet.dump": 60000,
                    "cell.restart": 60000,
                },
                "time_alias": "t_rel_ms; t0 = 2026-07-18T02:30:00Z HIL night start",
            },
            "distillation_targets": [
                "NIR reconstruction head: M = k_n * (1 - I/I0); ratio = I/I0; water = gsm * M / 100; M = 100 * water / gsm",
                "isolate-floor machine vs keep-whole vs sheet dump",
                "exoneration head: missing white-tile AE plus timezone skip, not last-to-badge",
                "operational companion: new-head restart without referring the NIR tech",
            ],
        },
        "reconstruction_model": {
            "name": "nir_paper_moisture",
            "formula": "M_pct = k_n * (1 - I_nA / I0_nA); ratio = I_nA / I0_nA; water_gm2 = gsm * M_pct / 100; M_pct = 100 * water_gm2 / gsm",
            "parameters": {
                "k_n": 20.00,
                "I0_nA": 16.00,
                "gsm": 80.00,
                "isolate_floor_pct": 6.00,
                "dump_pct": 40.00,
                "snr_lock": 12.0,
                "rezero_min": 24.0,
            },
            "worked_example": {"I_nA": 8.00, "M_pct": 10.00, "water_gm2": 8.00, "ratio": 0.50},
            "check": "20.00 * (1 - 8.00/16.00) = 10.00 exactly; 80.00 * 10.00 / 100 = 8.00 exactly; 2820 s + 1440 s = 4260 s = 24.0 min floor",
        },
        "raster": raster,
        "gate_snn": {
            "decision": "MODIFY",
            "decision_window_ms": 32.0,
            "decision_window_s": 0.032,
            "code": "hh4.nir_machine_gate",
            "note": "MODIFY accumulator wins: NIR high-moisture evidence overpowers the Nirveil continue advocate",
            "decode_rule": "modify-isolate if moisture_estimator AND nir_norm fire; vendor_continue_advocate is below threshold by design; referral_latch is not armed",
            "populations": [
                gate_pop("moisture_estimator", 80, 1.5, 50.0, w_s),
                gate_pop("nir_norm", 64, 1.2, 31.25, w_s),
                gate_pop("vendor_continue_advocate", 32, 0.7, 25.0, w_s),
                gate_pop("modify_latch", 80, 1.7, 62.5, w_s),
            ],
        },
        "gate_compute": gate_compute(
            [
                {"check": "hh4.nir_scorer", "neurons": 80, "mean_rate_hz": 50.0, "window_ms": 32.0},
                {"check": "hh4.isol_scorer", "neurons": 50, "mean_rate_hz": 50.0, "window_ms": 32.0},
            ]
        ),
        "meta": meta_common(
            id="nelb-r69-209",
            clock_domain="hh4-nir-hil-relative-ms-t0-2026-07-18T02:30:00Z",
            tags=["nir-moisture", "MODIFY", "ACCEPT", "serialized-reconstruction", "operational-t2"],
        ),
    }


# ---------------------------------------------------------------------------
# Record 210 — manganin-shunt remaining DC current of a potline rectifier, simulated,
# ACCEPT / REJECT
# ---------------------------------------------------------------------------
def rec_210():
    k_s = 4.00
    v_mv = 3.00
    i_ka = k_s * v_mv
    _exact(i_ka, 12.00)
    _exact(k_s * 1.50, 6.00)
    _exact(k_s * 2.00, 8.00)
    _exact(k_s * 4.00, 16.00)
    v_bus = 4.00
    p_mw = i_ka * v_bus
    _exact(p_mw, 48.00)
    v_id = i_ka / k_s
    _exact(v_id, 3.00)
    _exact(16.00 * 4.00, 64.00)
    _exact(6000.0 + 720.0, 6720.0)

    raster = make_raster(
        neurons=16,
        mean_rate_hz=62.5,
        window_ms=36.0,
        seed=202669210,
        source="mc5.shunt.mv",
        target="minkcrag.rectifier_accept_core",
        table=[
            {"from": "shunt_V", "to": "current_estimator", "weight": 1.40},
            {"from": "shunt_snr", "to": "shunt_norm_core", "weight": 1.20},
            {"from": "shuntveil_i", "to": "vendor_skip_advocate", "weight": 0.50},
        ],
        third_factor={
            "modulator": "na.shunt_scope_eligibility",
            "tau_e_s": 2.0,
            "tau_e_ms": 2000.0,
            "eligibility": "pre-post coincidence on skip-survey synapses; the manganin-shunt modulator enables potentiation only while millivolt and SNR are co-active inside tau_e so a Shuntveil last-good cannot skip rectifiers R-1..R-2 on a 12.00 kA remaining current",
        },
        channel_prefix="sh.n",
        anchor="MC-5 AMP-SIM-5 36 ms frame at V 3.00 mV / SNR 16.0 (t_s 3000) reconstructing 12.00 kA on R-3 above the 8.00 isolate floor",
    )
    w_s = 0.036
    events = [
        ev(0.0, "shunt.V", 1.50, code="V_MV", units="mV", note="simulated manganin shunt of MC-5 potline rectifier R-3; remaining-DC-current family, not Faraday FOCT, not Rogowski AC, not API-670 proximity, not fluxgate gradiometry, not Hall MFL remaining-wall, not Hallveil-24 ILI"),
        ev(300000.0, "shunt.snr", 10.0, code="SHUNT_SNR", units="1", note="early shunt SNR"),
        ev(600000.0, "recon.I", 6.00, code="I_KA", units="kA", note="4.00*1.50=6.00 exact"),
        ev(900000.0, "bus.V", 4.00, code="BUS_KV", units="kV", note="plant DC-bus PT on a serial-only LAN; independent witness"),
        ev(1200000.0, "shuntveil.I", 1.20, code="VENDOR_KA", units="kA", note="Shuntveil last-good current cloud; patched residual 8.00 kA"),
        ev(1800000.0, "shunt.V", 2.00, code="V_MV", units="mV"),
        ev(2100000.0, "recon.I", 8.00, code="I_KA", units="kA", note="4.00*2.00=8.00; isolate-adjacent band"),
        ev(2400000.0, "recon.k", 4.00, code="K_ID", units="kA_mV", note="8.00/2.00=4.00 exact gain identity before isolate"),
        ev(2700000.0, "shunt.snr", 14.0, code="SHUNT_SNR", units="1"),
        ev(3000000.0, "shunt.V", 3.00, code="V_MV", units="mV", note="in-band frame; raster sidecar"),
        ev(3000001.5, "shunt.snr", 16.0, code="SHUNT_SNR", units="1", note="1.5 ms shunt-norm after millivolt"),
        ev(3300000.0, "recon.I", 12.00, code="I_KA", units="kA", note="4.00*3.00=12.00 exact; isolate 8.00, trip 24.00"),
        ev(3600000.0, "recon.P", 48.00, code="P_MW", units="MW", note="12.00*4.00=48.00 DC-power identity at the isolate window"),
        ev(3900000.0, "shuntveil.I", 1.20, code="VENDOR_KA", units="kA"),
        ev(4200000.0, "hdr.id", 3.0, code="RECTIFIER", units="id"),
        ev(4500000.0, "r12.present", 1.0, code="R12_PRESENT", units="bool", note="adjacent rectifiers R-1 and R-2 are the skip-survey object, not this rectifier"),
        ev(4800000.0, "ops.prop", 1.0, code="ACCEPT_AND_SKIP", units="bool", note="potline lead Kerr Holt: R-3 is green on Shuntveil 1.20; skip R-1..R-2 to save a morning survey"),
        ev(5400000.0, "gate.hdr", 1.0, code="ACCEPT", units="decision", note="bounded ACCEPT of R-3 isolate only; 12.00 above 8.00 floor; R-1..R-2 out of scope"),
        ev(6000000.0, "surv.start", 1.0, code="SURV_START", units="bool", note="bookend 1 of the 12.0 min survey-complete floor"),
        ev(6720000.0, "surv.floor", 1.0, code="SURV_FLOOR", units="bool", note="6000 s + 720 s = 6720 s = 12.0 min"),
        ev(7200000.0, "ops.skip", 1.0, code="SKIP_R12", units="bool", note="Holt: Shuntveil 1.20, skip R-1..R-2"),
        ev(7800000.0, "gate.hold", 1.0, code="REJECT", units="decision", note="companion t2: skip-survey of R-1..R-2 refused; R-3 hold stands"),
        ev(8400000.0, "r3.held", 1.0, code="R3_HELD", units="bool"),
        ev(9000000.0, "shunt.V", 4.00, code="V_MV", units="mV"),
        ev(9600000.0, "recon.I", 16.00, code="I_KA", units="kA", note="4.00*4.00=16.00; still under the 24.00 trip"),
        ev(10200000.0, "shuntveil.I", 1.20, code="VENDOR_KA", units="kA"),
        ev(10800000.0, "r12.skip", 0.0, code="R12_NOT_SKIPPED", units="bool"),
        ev(11400000.0, "line.trip", 0.0, code="TRIP_NOT_TAKEN", units="bool"),
        ev(12000000.0, "shunt.snr", 15.0, code="SHUNT_SNR", units="1"),
        ev(12600000.0, "recon.P", 64.00, code="P_MW", units="MW", note="16.00*4.00=64.00 post-accept identity"),
        ev(13200000.0, "pot.held", 1.0, code="POT_HELD", units="bool"),
        ev(13800000.0, "takt.late", 1.0, code="SURVEY_COST", units="bool"),
        ev(14400000.0, "r3.held", 1.0, code="R3_HELD", units="bool"),
    ]
    assert_stream(events)

    traj = {
        "id": "nelb-r69-210-t1",
        "state": {
            "sim_or_real": "simulated",
            "episode_id": "MC-SHUNT-2026-0819",
            "domain": "manganin_shunt_potline_dc",
            "setting": "Minkcrag Smelter MC-5 (invented), Hazelcrag Potline, rectifier R-3. Simulated manganin-shunt coupon in AMP-SIM-5 supplies the millivolt that times the in-band R-3 isolate. Plant-owned shunt reconstruction is the remaining-DC-current SoT. Shuntveil vendor last-good current cloud is a corridor witness, not the rectifier SoT. Invented plant; simulated campaign. Not Faraday FOCT (r25), not Rogowski AC (r58 occupancy), not API-670 proximity (r52), not fluxgate gradiometry (r5), not Hall MFL remaining-wall (r27/r28), not Hallveil-24 ILI (r28), not coulometric Karl Fischer (r67).",
            "observables_at_decision": {
                "V_mV": v_mv,
                "k_s": k_s,
                "I_kA": i_ka,
                "P_MW": p_mw,
                "shuntveil_kA": 1.20,
                "shunt_snr": 16.0,
                "isolate_floor_kA": 8.00,
            },
            "margin_authority": "MC-5 potline SOP rev A: if reconstructed I_kA >= 8.00 AND shunt SNR >= 12.0, rectifier R-3 may be isolated and surveyed. Line-trip if I_kA >= 24.00. R-1..R-2 skip-survey is a different gate. Shuntveil last-good cannot skip an unmeasured rectifier.",
        },
        "proposed_action": {
            "actor": "potline lead Kerr Holt, citing Shuntveil 1.20 kA and a late morning survey",
            "summary": "stamp R-3 in band and skip R-1..R-2; 3.00 mV is a shunt glitch on a healthy current cloud",
            "basis_claimed": "Shuntveil last-good is 1.20 kA and a night survey of R-1..R-2 is a takt miss",
        },
        "safety_decision": {
            "decision": "ACCEPT",
            "rationale": "Rectifier R-3 is accepted as in-band for a single isolate plus survey. Serialized reconstruction: I_kA = k_s * V_mV = 4.00 * 3.00 = 12.00, which is 4.00 kA above the 8.00 isolate floor and 12.00 kA under the 24.00 line-trip. Power identity P = I * V_bus = 12.00 * 4.00 = 48.00 MW; gain identity k_s = I / V = 12.00 / 3.00 = 4.00. Shuntveil 1.20 kA is a patched 8.00 residual and is not an admissible skip-survey witness. Ordered: ACCEPT this R-3 isolate only. Scope: this ACCEPT does not skip R-1..R-2 (that is the companion question) and does not stamp a line trip.",
            "threshold": "I_kA>=8.00 AND shunt_snr>=12.0 => accept R-3 isolate; Shuntveil is not SoT; line-trip if I_kA>=24.00; R-1..R-2 are out of scope",
            "stated_residuals": "12.00 vs 8.00 isolate floor is 4.00 kA, not infinite; R-1..R-2 remain unmeasured; Shuntveil remains the only OEM current channel",
        },
        "executed_action": {
            "summary": "ACCEPT at t_s 5400: R-3 in band; R-1..R-2 not skipped; Shuntveil not SoT; reconstruction locked",
            "tool": "mc5-shunt-rectifier-gate-cli",
            "observation": "I 12.00 kA recomputes from V 3.00 mV; AMP-SIM-5 hashed; Shuntveil channel not used as SoT",
        },
        "future_outcome": {
            "timeline": [
                {"t_s": 3000.0, "event": "shunt V 3.00 mV; raster frame; I 12.00 kA"},
                {"t_s": 4800.0, "event": "ops proposes accept R-3 and skip R-1..R-2"},
                {"t_s": 5400.0, "event": "ACCEPT R-3 only; R-1..R-2 out of scope"},
                {"t_s": 6000.0, "event": "12 min survey-complete bookend 1"},
                {"t_s": 6720.0, "event": "12.0 min floor"},
                {"t_s": 7800.0, "event": "companion REJECT skip-survey of R-1..R-2"},
            ],
            "observed_effects": [
                "current recomputes from the serialized shunt model at every recon.I event",
                "a Shuntveil-only head would have skipped R-1..R-2 overnight",
                "12 min survey-complete floor is in the stream (surv.start, surv.floor)",
            ],
            "surprises": [
                "a last-good 1.20 kA vendor corridor co-existed with a 12.00 kA in-band reconstruction that still forbids skipping the unmeasured rectifiers",
            ],
            "new_state": {
                "r3": "accepted in band",
                "r12": "not this gate",
                "shuntveil": "not SoT",
                "reconstruction_model": "discharged as an on-record calculator",
            },
            "latency_ms": 2400000.0,
        },
        "reward_components": reward(
            0.41,
            [
                ("shunt_reconstruction", 0.14),
                ("in_band_rectifier_scope", 0.12),
                ("shuntveil_nonsubstitution", 0.09),
                ("r12_out_of_scope", 0.08),
                ("survey_cost", -0.02),
            ],
            "scored for a bounded ACCEPT of R-3 on a recomputable remaining DC current while refusing a Shuntveil skip of R-1..R-2; 12 min floor is priced as survey takt not as a reason to skip",
        ),
        "meta": meta_common(
            tags=["ACCEPT", "manganin-shunt-dc", "serialized-reconstruction", "operational-companion"],
            distillation_note="manganin-shunt gate: serialized k_s*V plus power identity beats a green last-good dashboard; companion t2 is the skip-survey refusal, not a current re-vote",
        ),
    }
    traj2 = {
        "id": "nelb-r69-210-t2",
        "state": {
            "sim_or_real": "simulated",
            "episode_id": "MC-SHUNT-2026-0819-exec",
            "domain": "rectifier_skip_survey_refusal",
            "setting": "Same MC-5 after the ACCEPT. Potline lead proposes skipping R-1..R-2 on Shuntveil 1.20 kA. This companion is the operational skip refusal, not a second current vote.",
            "observables_at_decision": {
                "I_kA": 16.00,
                "shuntveil_kA": 1.20,
                "surv_floor_s": 720.0,
                "skip_proposed": True,
            },
        },
        "proposed_action": {
            "actor": "potline lead Kerr Holt",
            "summary": "skip R-1..R-2; 12 min already paid and Shuntveil is 1.20 kA",
            "basis_claimed": "the ACCEPT already stamped R-3, so skipping the rest of the rectifier row is the cheapest hold",
        },
        "safety_decision": {
            "decision": "REJECT",
            "rationale": "Refuse skip-survey of R-1..R-2. The 12 min survey-complete floor is done and the line-trip (I_kA >= 24.00) is still armed on the plant shunt head. REJECT the skip. Do not trip the line. Do not reopen R-3. 16.00 kA post-accept is still in band for R-3 only; R-1..R-2 have no independent manganin shunt.",
            "threshold": "r3_held AND surv_floor_complete AND r12_not_skipped AND line_not_tripped",
        },
        "executed_action": {
            "summary": "R-1..R-2 skip refused at t_s 7800; R-3 hold stands; line not tripped",
            "tool": "mc5-shunt-skip-exec",
            "observation": "recon.I 16.00 kA on R-3; R-1..R-2 remain on the survey list; Shuntveil still ignored",
        },
        "future_outcome": {
            "timeline": [
                {"t_s": 6000.0, "event": "survey clock started after ACCEPT"},
                {"t_s": 6720.0, "event": "12.0 min floor"},
                {"t_s": 7200.0, "event": "skip R-1..R-2 proposed"},
                {"t_s": 7800.0, "event": "REJECT skip-survey of R-1..R-2"},
            ],
            "observed_effects": [
                "Shuntveil skip did not reopen the current call",
                "line trip never fired; 12.00 vs 24.00 kA floor",
            ],
            "new_state": {"r3": "held in band", "r12": "still to survey", "line": "in service"},
            "latency_ms": 1800000.0,
        },
        "reward_components": reward(
            0.36,
            [
                ("skip_refusal", 0.13),
                ("shuntveil_nonsubstitution", 0.11),
                ("no_line_trip", 0.09),
                ("surv_floor_complete", 0.05),
                ("held_survey_takt_cost", -0.02),
            ],
            "operational execution gate: refuse skip-survey because last-good freeze is not manganin-shunt DC current; not a current re-vote",
        ),
        "meta": meta_common(tags=["REJECT", "operational-execution", "skip-survey"]),
    }
    return {
        "id": "nelb-r69-210",
        "spike_events": events,
        "language_view": {
            "description": "Minkcrag Smelter MC-5. Simulated manganin shunt reconstructs 12.00 kA from 4.00*3.00 while Shuntveil still shows 1.20 kA. The gate ACCEPTs R-3 isolate only; a companion execution REJECT refuses skip-survey of R-1..R-2. The millivolt-to-current model is serialized so every recon event recomputes.",
            "trajectory": traj,
            "trajectory_skip_survey_refusal": traj2,
        },
        "bridge_notes": {
            "channel_map": {
                "shunt.V / shunt.snr": "shunt millivolt and SNR; the physics channels the reconstruction consumes",
                "recon.I / recon.P / recon.k": "serialized remaining current kA, DC-power identity, and gain identity",
                "bus.V / shuntveil.I / hdr.id / r12.present": "bus PT, vendor last-good, rectifier id, and adjacent-rectifier presence; the denial and scope channels",
                "ops.prop / gate.hdr / ops.skip / gate.hold": "accept-and-skip proposal, bounded ACCEPT, skip proposal, companion REJECT",
                "surv.start / surv.floor / r3.held / r12.skip / pot.held": "operational companion channels plus the 12 min floor",
            },
            "temporal_motifs": [
                "last-good-low while shunt-over: shuntveil.I 1.20 next to recon.I 12.00",
                "reconstruction as event: recon.I 12.00 equals 4.00*3.00",
                "ACCEPT then operational REJECT: gate.hdr at 5400 s, gate.hold at 7800 s",
                "slow floor in-stream: surv.start 6000 s, surv.floor 6720 s (12.0 min)",
                "tight shunt pair: shunt.V then shunt.snr +1.5 ms at the raster frame",
            ],
            "language_to_spike_mapping": "'Shuntveil is 1.20 kA' = shuntveil.I 1.20; '12 kA remaining' = recon.I 12.00; 'this rectifier not R-1..R-2' = gate.hdr ACCEPT plus r12.skip 0; 'do not skip R-1..R-2' = gate.hold REJECT",
            "why_high_value": "New manganin-shunt remaining-DC-current family on a potline rectifier (not Faraday FOCT r25, not Rogowski AC r58 occupancy, not API-670 proximity r52, not fluxgate gradiometry r5, not Hall MFL remaining-wall r27/r28, not Hallveil-24 ILI r28, not coulometric Karl Fischer r67). First k_s*V current reconstruction with power identity that can sit in band while a last-good corridor wants a rectifier skip. Companion t2 is operational skip refusal. sim_or_real=simulated.",
            "encoder_spec": {
                "prng": "MT19937 via python random.Random",
                "seeds": {"raster": 202669210, "stream_note": "stream amplitudes are authored constants (mV, 1, kA, MW, kV, id, bool)"},
                "draw_order": "raster: per neuron id order, gap-constrained times, per-spike adaptation and noise",
                "thinning": "shunt transmitter exists at ~10 Hz; stream keeps 4 V points; recon keeps 4 of ~20 solver ticks",
                "refractory_floors_ms": {
                    "shunt.V": 1.5,
                    "shunt.snr": 1.5,
                    "recon.I": 60000,
                    "recon.P": 60000,
                    "recon.k": 60000,
                    "bus.V": 60000,
                    "shuntveil.I": 60000,
                    "hdr.id": 60000,
                    "r12.present": 60000,
                    "ops.prop": 60000,
                    "gate.hdr": 60000,
                    "surv.start": 60000,
                    "surv.floor": 60000,
                    "ops.skip": 60000,
                    "gate.hold": 60000,
                    "r3.held": 60000,
                    "r12.skip": 60000,
                    "line.trip": 60000,
                    "pot.held": 60000,
                    "takt.late": 60000,
                },
                "time_alias": "t_rel_ms; t0 = 2026-08-19T03:00:00Z simulated night start",
            },
            "distillation_targets": [
                "manganin-shunt reconstruction head: I = k_s * V; P = I * V_bus; k_s = I / V",
                "bounded ACCEPT head: in-band remaining current AND rectifier scope AND r12-out-of-scope",
                "operational companion: refuse skip-survey without re-opening the current call",
            ],
        },
        "reconstruction_model": {
            "name": "manganin_shunt_potline_dc",
            "formula": "I_kA = k_s * V_mV; P_MW = I_kA * V_bus_kV; k_s = I_kA / V_mV",
            "parameters": {
                "k_s": 4.00,
                "V_bus_kV": 4.00,
                "isolate_floor_kA": 8.00,
                "kill_kA": 24.00,
                "snr_lock": 12.0,
                "surv_min": 12.0,
            },
            "worked_example": {"V_mV": 3.00, "I_kA": 12.00, "P_MW": 48.00, "k_s": 4.00},
            "check": "4.00 * 3.00 = 12.00 exactly; 12.00 * 4.00 = 48.00 exactly; 12.00 / 3.00 = 4.00 exactly; 6000 s + 720 s = 6720 s = 12.0 min floor",
        },
        "raster": raster,
        "gate_snn": {
            "decision": "ACCEPT",
            "decision_window_ms": 36.0,
            "decision_window_s": 0.036,
            "code": "mc5.shunt_rectifier_gate",
            "note": "ACCEPT accumulator wins: manganin remaining-DC-current evidence overpowers the Shuntveil skip advocate",
            "decode_rule": "accept if current_estimator AND shunt_norm AND rectifier_margin fire inside the window; vendor_skip_advocate is necessary-but-not-sufficient and cannot release R-1..R-2",
            "populations": [
                gate_pop("current_estimator", 80, 1.5, 50.0, w_s),
                gate_pop("shunt_norm", 64, 1.2, 31.25, w_s),
                gate_pop("rectifier_margin", 40, 1.0, 50.0, w_s),
                gate_pop("vendor_skip_advocate", 32, 0.7, 25.0, w_s),
                gate_pop("accept_latch", 96, 1.8, 62.5, w_s),
            ],
        },
        "gate_compute": gate_compute(
            [
                {"check": "mc5.shunt_scorer", "neurons": 80, "mean_rate_hz": 50.0, "window_ms": 36.0},
                {"check": "mc5.i_scorer", "neurons": 40, "mean_rate_hz": 62.5, "window_ms": 32.0},
            ]
        ),
        "meta": meta_common(
            id="nelb-r69-210",
            clock_domain="mc5-shunt-sim-relative-ms-t0-2026-08-19T03:00:00Z",
            tags=["manganin-shunt-dc", "ACCEPT", "REJECT", "serialized-reconstruction", "operational-t2"],
        ),
    }
