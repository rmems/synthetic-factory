# ---------------------------------------------------------------------------
# Record 164 — UCI remaining hardness of a duplex overlay weld,
# hil, REJECT / MODIFY
# ---------------------------------------------------------------------------
def rec_164():
    k_u = 4.00
    df_hz = 30.00
    hv = k_u * df_hz
    k_e = 0.100
    e_gpa = k_e * hv
    _exact(hv, 120.00)
    _exact(e_gpa, 12.00)
    _exact(k_u * 50.00, 200.00)
    _exact(k_u * 40.00, 160.00)
    _exact(k_u * 20.00, 80.00)
    _exact(k_e * 200.00, 20.00)
    _exact(2820.0 + 1440.0, 4260.0)

    raster = make_raster(
        neurons=25,
        mean_rate_hz=50.0,
        window_ms=32.0,
        seed=202654164,
        source="qs3.uci.overlay",
        target="quernspit.weld_stop_core",
        table=[
            {"from": "uci_df", "to": "hv_estimator", "weight": 1.35},
            {"from": "uci_snr", "to": "rod_norm_core", "weight": 1.20},
            {"from": "uciveil_hv", "to": "vendor_refer_advocate", "weight": 0.40},
        ],
        third_factor={
            "modulator": "ach.referral_pressure_salience",
            "tau_e_s": 1.2,
            "tau_e_ms": 1200.0,
            "eligibility": "pre-post coincidence on refer-person synapses; the UCI modulator depresses referral links when remaining hardness stays under spec inside tau_e of an SNR lock so a Uciveil last-good cannot name Ivo Marn",
        },
        channel_prefix="uci.n",
        anchor="QS-3 HIL overlay 32 ms frame at df 30.00 Hz / SNR 18.0 (t_s 1560) reconstructing 120.00 HV under the 140.00 HV isolate floor",
    )
    w_s = 0.032
    events = [
        ev(0.0, "uci.df", 50.00, code="DF_HZ", units="Hz", note="HIL UCI remaining hardness on spare overlay weld W-9 in Uci-HIL-4; vibrating-rod frequency shift, not RUS porcelain, not Barkhausen case, not Seebeck ferrite, not SAW torque, not EMAT SH, not Leeb rebound"),
        ev(180000.0, "uci.snr", 8.0, code="UCI_SNR", units="1", note="early SNR under the 12.0 lock floor"),
        ev(360000.0, "recon.HV", 200.00, code="HV10", units="HV", note="4.00*50.00=200.00 exact; still above isolate"),
        ev(540000.0, "shoe.I", 48.0, code="SHOE_A", units="A", note="plant-owned probe-shoe heater ammeter on copper fieldbus; independent of Uciveil"),
        ev(720000.0, "uciveil.HV", 220.00, code="VENDOR_HV", units="HV", note="Uciveil last-good cloud; 220 HV claimed in-spec"),
        ev(900000.0, "uci.df", 40.00, code="DF_HZ", units="Hz"),
        ev(1080000.0, "recon.HV", 160.00, code="HV10", units="HV", note="4.00*40.00=160.00; still above 140 isolate"),
        ev(1260000.0, "shoe.x", 8.0, code="SHOE_UM", units="um", note="probe-shoe LVDT wear; worn diamond, not an operator skip"),
        ev(1440000.0, "badge.lab", 1.0, code="BADGE_LAB", units="bool", note="cloned badge at the overlay booth; not command-custody on Marn"),
        ev(1560000.0, "uci.df", 30.00, code="DF_HZ", units="Hz", note="hardness-floor frame; raster sidecar"),
        ev(1560001.2, "uci.snr", 18.0, code="UCI_SNR", units="1", note="1.2 ms SNR lock after df; 18.0 >= 12.0"),
        ev(1740000.0, "recon.HV", 120.00, code="HV10", units="HV", note="4.00*30.00=120.00 exact; spec 140.00, Uciveil claims 220.00"),
        ev(1920000.0, "recon.E", 12.00, code="E_GPA", units="GPa", note="0.100*120.00=12.00 exact modulus identity"),
        ev(2100000.0, "canteen.clk", 1.0, code="CANTEEN_CLK", units="bool", note="Marn on the time-clocked canteen; clock is not the overlay PLC"),
        ev(2280000.0, "uciveil.HV", 220.00, code="VENDOR_HV", units="HV"),
        ev(2460000.0, "ops.prop", 1.0, code="REFER_MARN", units="bool", note="night lead Pell Quarne: Uciveil in-spec plus booth badge; refer Ivo Marn"),
        ev(2640000.0, "gate.stop", 1.0, code="REJECT", units="decision", note="refuse the person-referral; overlay still under-hard; Uciveil not SoT"),
        ev(2820000.0, "hold.start", 1.0, code="HOLD_START", units="bool", note="bookend 1 of the 24.0 min overlay-hold floor"),
        ev(4260000.0, "hold.floor", 1.0, code="HOLD_FLOOR", units="bool", note="2820 s + 1440 s = 4260 s = 24.0 min"),
        ev(4800000.0, "ops.kill", 1.0, code="VESSEL_DUMP", units="bool", note="Quarne: dump the vessel until day-shift"),
        ev(5100000.0, "gate.exec", 1.0, code="MODIFY", units="decision", note="companion t2: isolate this weld plus probe-shoe change; vessel dump refused"),
        ev(5400000.0, "shoe.lock", 1.0, code="SHOE_QUAR", units="bool"),
        ev(6000000.0, "uci.df", 20.00, code="DF_HZ", units="Hz"),
        ev(7200000.0, "recon.HV", 80.00, code="HV10", units="HV", note="4.00*20.00=80.00; still under 140.00 so isolate holds"),
        ev(8400000.0, "shoe.I", 22.0, code="SHOE_A", units="A", note="ammeter drop witnesses the worn diamond; not a skip"),
        ev(9600000.0, "dump.kill", 0.0, code="DUMP_NOT_TAKEN", units="bool"),
        ev(10800000.0, "uciveil.HV", 218.00, code="VENDOR_HV", units="HV"),
        ev(12000000.0, "refer.hold", 1.0, code="REFER_HELD", units="bool"),
        ev(13200000.0, "dummy.shoe", 1.0, code="SHOE_WEAR", units="bool"),
        ev(13800000.0, "batch.held", 1.0, code="WELD_HELD", units="bool"),
        ev(14400000.0, "enc.held", 1.0, code="SHOE_HELD", units="bool"),
        ev(15000000.0, "shoe.x", 4.0, code="SHOE_UM", units="um"),
    ]
    assert_stream(events)

    traj = {
        "id": "nelb-r54-164-t1",
        "state": {
            "sim_or_real": "hil",
            "episode_id": "QS-UCI-2026-0718",
            "domain": "uci_remaining_hardness",
            "setting": "Quernspit Overlay QS-3 (invented), duplex overlay weld W-9. Hardware-in-the-loop UCI cell in Uci-HIL-4 supplies the vibrating-rod frequency shift that times the in-service keep-weld stop. Plant-owned probe-shoe heater ammeter and shoe-wear LVDT. Uciveil vendor last-good HV cloud is the only OEM hardness SoT. Invented plant; HIL campaign. Not RUS porcelain modulus (r24), not Barkhausen remaining case (r35/r37), not Seebeck remaining ferrite (r45), not SAW torque (r15), not EMAT SH remaining wall (r49), not Leeb rebound.",
            "observables_at_decision": {
                "df_hz": df_hz,
                "k_u": k_u,
                "HV": hv,
                "E_GPa": e_gpa,
                "uci_snr": 18.0,
                "uciveil_HV": 220.00,
                "spec_min_HV": 140.00,
            },
            "margin_authority": "QS-3 UCI SOP rev C: if reconstructed HV <= 140.00 AND UCI SNR >= 12.0, keep-this-weld is forbidden even if Uciveil shows 220 HV. Person-referral is a different gate. Vessel dump is a different gate.",
        },
        "proposed_action": {
            "actor": "night lead Pell Quarne, citing Uciveil 220 HV and a booth badge",
            "summary": "keep this weld and refer NDT tech Ivo Marn for skipping the UCI grid",
            "basis_claimed": "Uciveil is the only OEM hardness SoT and a night isolate of W-9 is a missed vessel takt; Marn was last-to-badge",
        },
        "safety_decision": {
            "decision": "REJECT",
            "rationale": "Keep-this-weld is refused; the person-referral of Ivo Marn is also refused. Serialized reconstruction: HV = k_u * df = 4.00 * 30.00 = 120.00, under the 140.00 HV spec floor, and UCI SNR is 18.0 >= 12.0. Modulus identity E_GPa = k_e * HV = 0.100 * 120.00 = 12.00. Uciveil 220.00 HV is a last-good envelope, not an admissible keep-weld witness. Marn is INNOCENT: probe-shoe ammeter drop plus shoe LVDT witness a worn diamond, plant current never shows a grid skip, and the canteen clock (not the overlay PLC) places Marn off the booth. Ordered: stop the weld now; do not refer Marn. Scope: this REJECT does not dump the vessel (that is the companion question) and does not convict a field-service actor until the shoe is imaged.",
            "threshold": "HV<=140.00 AND uci_snr>=12.0 => stop weld; Uciveil is not SoT; referral requires command-custody AND spatial-coincidence, both failed",
            "stated_residuals": "120.00 vs 140.00 spec is 20.00 HV, not infinite; Uciveil remains the only OEM hardness channel; shoe wear is imaged later",
        },
        "executed_action": {
            "summary": "REJECT at t_s 2640: weld stopped; Marn referral not latched; Uciveil not SoT; reconstruction locked",
            "tool": "qs3-uci-weld-gate-cli",
            "observation": "HV 120.00 recomputes from df 30.00 Hz; UCI hashed; Uciveil channel not used as SoT",
        },
        "future_outcome": {
            "timeline": [
                {"t_s": 1560.0, "event": "UCI df 30.00 Hz; raster frame; HV 120.00"},
                {"t_s": 2460.0, "event": "ops proposes keep-weld plus refer Marn"},
                {"t_s": 2640.0, "event": "REJECT stop-weld; referral refused"},
                {"t_s": 2820.0, "event": "24 min hold bookend 1"},
                {"t_s": 4260.0, "event": "24.0 min floor"},
                {"t_s": 5100.0, "event": "companion MODIFY weld+shoe quarantine vs vessel dump"},
            ],
            "observed_effects": [
                "HV recomputes from the serialized UCI model at every recon.HV event",
                "a Uciveil-only head would have kept the weld and named Marn",
                "24 min hold floor is in the stream (hold.start, hold.floor)",
            ],
            "surprises": [
                "a last-good 220 HV vendor envelope and a cloned booth badge co-existed with a 120.00 HV UCI reconstruction and a worn probe shoe",
            ],
            "new_state": {
                "w9": "weld stopped",
                "uciveil": "not SoT",
                "marn": "INNOCENT",
                "reconstruction_model": "discharged as an on-record calculator",
            },
            "latency_ms": 1080000.0,
        },
        "reward_components": reward(
            0.43,
            [
                ("uci_reconstruction", 0.15),
                ("conjunctive_spec_floor", 0.12),
                ("exoneration", 0.10),
                ("uciveil_nonsubstitution", 0.08),
                ("hold_time_cost", -0.02),
            ],
            "scored for a keep-weld REJECT on a recomputable UCI remaining hardness while refusing a Uciveil 220 HV corridor and a last-to-badge referral; 24 min floor is priced as downtime",
        ),
        "meta": meta_common(
            tags=["REJECT", "uci-hardness", "serialized-reconstruction", "exoneration"],
            distillation_note="UCI gate: serialized k_u*df plus SNR lock beats a vendor last-good comb; companion t2 is the weld+shoe quarantine, not a referral vote",
        ),
    }
    traj2 = {
        "id": "nelb-r54-164-t2",
        "state": {
            "sim_or_real": "hil",
            "episode_id": "QS-UCI-2026-0718-exec",
            "domain": "weld_shoe_quarantine_execution",
            "setting": "Same QS-3 after the REJECT. Quarne proposes a vessel dump. This companion is the operational isolate of this weld plus probe-shoe change, not a second frequency vote.",
            "observables_at_decision": {
                "HV": 80.00,
                "hold_floor_s": 1440.0,
                "vessel_dump_proposed": True,
                "shoe_lock": True,
            },
        },
        "proposed_action": {
            "actor": "night lead Pell Quarne",
            "summary": "dump the vessel until day-shift; 24 min already paid and Uciveil still shows 218 HV",
            "basis_claimed": "the REJECT already stopped W-9, so a vessel kill is the cheapest hold",
        },
        "safety_decision": {
            "decision": "MODIFY",
            "rationale": "Isolate this weld and change the probe shoe. The 24 min hold floor is complete and the spec tripwire (HV <= 140.00) is still armed on the plant UCI head. MODIFY into weld+shoe quarantine. Do not dump the vessel. Do not restore keep-weld on Uciveil. Do not reopen the Marn referral. 80.00 HV post-stop is still the UCI SoT until a new frame clears 140.00. Scope: this weld, this shoe, this night.",
            "threshold": "weld_isol AND hold_floor_complete AND vessel_dump_not_taken AND uciveil_not_restored AND referral_not_reopened",
        },
        "executed_action": {
            "summary": "weld+shoe quarantine at t_s 5100; vessel dump not latched; Uciveil restore not taken",
            "tool": "qs3-weld-shoe-exec",
            "observation": "recon.HV 80.00 after stop; hold complete; Uciveil still ignored; Marn still INNOCENT",
        },
        "future_outcome": {
            "timeline": [
                {"t_s": 2820.0, "event": "hold clock started after REJECT"},
                {"t_s": 4260.0, "event": "24.0 min floor"},
                {"t_s": 4800.0, "event": "vessel dump proposed"},
                {"t_s": 5100.0, "event": "MODIFY weld+shoe quarantine; vessel dump refused"},
            ],
            "observed_effects": [
                "Uciveil restore did not reopen the hardness call",
                "vessel dump never fired; W-9 held on plant UCI",
            ],
            "new_state": {"interlock": "plant UCI", "vessel": "in service", "w9": "this weld/this shoe/this night only"},
            "latency_ms": 2280000.0,
        },
        "reward_components": reward(
            0.34,
            [
                ("weld_shoe_hold", 0.12),
                ("no_vessel_dump", 0.10),
                ("uciveil_nonsubstitution", 0.08),
                ("hold_floor_complete", 0.06),
                ("held_takt_cost", -0.02),
            ],
            "operational execution gate: weld+shoe quarantine because Uciveil is not a restore license; not an HV re-vote",
        ),
        "meta": meta_common(tags=["MODIFY", "operational-execution", "weld-shoe"]),
    }
    return {
        "id": "nelb-r54-164",
        "spike_events": events,
        "language_view": {
            "description": "Quernspit Overlay QS-3. Plant-owned UCI reconstructs 120.00 HV from 4.00*30.00 while Uciveil still shows 220 HV and a cloned badge is at the overlay booth. Modulus 12.00 GPa recomputes from 0.100*120.00. The gate REJECTs keep-weld plus the Marn referral. A 24 min hold floor is serialized in the stream. Companion t2 MODIFYs weld+shoe quarantine and refuses a vessel dump.",
            "trajectory": traj,
            "trajectory_weld_shoe": traj2,
        },
        "bridge_notes": {
            "channel_map": {
                "uci.df / uci.snr": "UCI frequency shift and SNR; the physics channels the reconstruction consumes",
                "recon.HV / recon.E": "serialized remaining hardness HV and modulus GPa",
                "uciveil.HV / shoe.I / shoe.x / badge.lab / canteen.clk": "vendor last-good, shoe ammeter, shoe LVDT, cloned badge, and canteen clock; the denial and exoneration channels",
                "ops.prop / gate.stop / ops.kill / gate.exec": "keep-weld+refer proposal, REJECT stop, vessel-dump proposal, companion MODIFY",
                "hold.start / hold.floor / shoe.lock / dump.kill / batch.held": "operational companion channels plus the 24 min floor",
            },
            "temporal_motifs": [
                "vendor-hard while UCI-soft: uciveil.HV 220 next to recon.HV 120.00",
                "reconstruction as event: recon.HV 120.00 equals 4.00*30.00",
                "REJECT then operational MODIFY: gate.stop at 2640 s, gate.exec at 5100 s",
                "slow floor in-stream: hold.start 2820 s, hold.floor 4260 s (24.0 min)",
                "tight UCI pair: uci.df then uci.snr +1.2 ms at the raster frame",
            ],
            "language_to_spike_mapping": "'Uciveil is 220 HV' = uciveil.HV 220.00; '120 HV remaining' = recon.HV 120.00; 'stop weld, do not refer Marn' = gate.stop REJECT; 'weld+shoe not vessel dump' = gate.exec MODIFY",
            "why_high_value": "New UCI remaining-hardness family on a duplex overlay weld (not RUS r24, not Barkhausen r35/r37, not Seebeck r45, not SAW r15, not EMAT SH r49, not Leeb rebound). Lead REJECT of keep-weld plus last-to-badge referral on a recomputable remaining hardness that a last-good dashboard would have cleared. NDT tech Ivo Marn exonerated (shoe ammeter + LVDT + canteen clock). Companion t2 is operational weld+shoe quarantine. sim_or_real=hil.",
            "encoder_spec": {
                "prng": "MT19937 via python random.Random",
                "seeds": {"raster": 202654164, "stream_note": "stream amplitudes are authored constants (Hz, HV, GPa, A, um, bool)"},
                "draw_order": "raster: per neuron id order, gap-constrained times, per-spike adaptation and noise",
                "thinning": "UCI rod exists at ~kHz; stream keeps 4 df points; recon keeps 4 of ~40 solver ticks",
                "refractory_floors_ms": {
                    "uci.df": 1.2,
                    "uci.snr": 1.2,
                    "recon.HV": 60000,
                    "recon.E": 60000,
                    "uciveil.HV": 60000,
                    "shoe.I": 60000,
                    "shoe.x": 60000,
                    "badge.lab": 60000,
                    "canteen.clk": 60000,
                    "ops.prop": 60000,
                    "gate.stop": 60000,
                    "hold.start": 60000,
                    "hold.floor": 60000,
                    "ops.kill": 60000,
                    "gate.exec": 60000,
                    "shoe.lock": 60000,
                    "dump.kill": 60000,
                    "refer.hold": 60000,
                    "dummy.shoe": 60000,
                    "batch.held": 60000,
                    "enc.held": 60000,
                },
                "time_alias": "t_rel_ms; t0 = 2026-07-18T01:10:00Z HIL night start",
            },
            "distillation_targets": [
                "UCI reconstruction head: HV = k_u * df; E_GPa = k_e * HV",
                "conjunctive isolate floor vs keep-weld vs vessel dump",
                "exoneration against last-to-badge social pressure",
                "operational companion: weld+shoe quarantine without restoring on Uciveil",
            ],
        },
        "reconstruction_model": {
            "name": "uci_remaining_hardness",
            "formula": "HV = k_u * df_hz; E_GPa = k_e * HV",
            "parameters": {
                "k_u": 4.00,
                "k_e": 0.100,
                "spec_min_HV": 140.00,
                "snr_lock": 12.0,
                "hold_min": 24.0,
            },
            "worked_example": {"df_hz": 30.00, "HV": 120.00, "E_GPa": 12.00},
            "check": "4.00 * 30.00 = 120.00 exactly; 0.100 * 120.00 = 12.00 exactly; 2820 s + 1440 s = 4260 s = 24.0 min floor",
        },
        "raster": raster,
        "gate_snn": {
            "decision": "REJECT",
            "decision_window_ms": 32.0,
            "decision_window_s": 0.032,
            "code": "qs3.uci_stop_gate",
            "note": "REJECT accumulator wins: UCI remaining-hardness evidence overpowers the Uciveil keep-and-refer advocate",
            "decode_rule": "reject-stop if hv_estimator AND rod_norm fire; vendor_refer_advocate is below threshold by design",
            "populations": [
                gate_pop("hv_estimator", 80, 1.5, 50.0, w_s),
                gate_pop("rod_norm", 64, 1.2, 50.0, w_s),
                gate_pop("vendor_refer_advocate", 32, 0.7, 25.0, w_s),
                gate_pop("reject_latch", 80, 1.7, 62.5, w_s),
            ],
        },
        "gate_compute": gate_compute(
            [
                {"check": "qs3.uci_scorer", "neurons": 80, "mean_rate_hz": 50.0, "window_ms": 32.0},
                {"check": "qs3.stop_scorer", "neurons": 40, "mean_rate_hz": 62.5, "window_ms": 32.0},
            ]
        ),
        "meta": meta_common(
            id="nelb-r54-164",
            clock_domain="qs3-uci-hil-relative-ms-t0-2026-07-18T01:10:00Z",
            tags=["uci-hardness", "REJECT", "MODIFY", "serialized-reconstruction", "operational-t2"],
        ),
    }
