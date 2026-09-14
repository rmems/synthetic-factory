# ---------------------------------------------------------------------------
# Record 133 — TOFD remaining ligament of a hydrocracker girth weld
# designed, MODIFY / ACCEPT
# ---------------------------------------------------------------------------
def rec_133():
    c_mm_us = 6.00
    t_bw_us = 8.00
    t_d_us = 4.00
    lig_mm = c_mm_us * (t_bw_us - t_d_us) / 2.0
    t_nom = 20.00
    a_mm = t_nom - lig_mm
    _exact(lig_mm, 12.00)
    _exact(a_mm, 8.00)
    _exact(c_mm_us * (8.00 - 2.00) / 2.0, 18.00)
    _exact(c_mm_us * (8.00 - 3.00) / 2.0, 15.00)
    _exact(c_mm_us * (8.00 - 3.60) / 2.0, 13.20)
    _exact(c_mm_us / 2.0 * 4.00, 12.00)
    _exact(6600.0 + 1080.0, 7680.0)

    raster = make_raster(
        neurons=20,
        mean_rate_hz=50.0,
        window_ms=36.0,
        seed=20264433,
        source="ch7.tofd.weld",
        target="cinderholt.weld_isolate_core",
        table=[
            {"from": "tofd_td", "to": "ligament_estimator", "weight": 1.40},
            {"from": "tofd_tbw", "to": "backwall_norm_core", "weight": 1.20},
            {"from": "tofdveil_L", "to": "vendor_continue_advocate", "weight": 0.45},
        ],
        third_factor={
            "modulator": "na.ligament_salience",
            "tau_e_s": 1.6,
            "tau_e_ms": 1600.0,
            "eligibility": "pre-post coincidence on weld-isolate synapses; the TOFD modulator enables potentiation only while the backwall time is co-active inside tau_e so a Tofdveil last-campaign corridor cannot hide a 12.00 mm remaining ligament",
        },
        channel_prefix="tofd.n",
        anchor="CH-7 TOFD 36 ms frame at t_d 4.00 us / t_bw 8.00 us (t_s 3000) reconstructing 12.00 mm remaining ligament at the 12.00 mm isolate floor",
    )
    w_s = 0.036
    events = [
        ev(0.0, "tofd.td", 2.00, code="TD_US", units="us", note="plant-owned TOFD on hydrocracker girth weld W-22; diffracted vs backwall, not PAUT TFM, not impact-echo, not Lamb-wave LUT, not MsS T(0,1), not DCPD"),
        ev(300000.0, "tofd.tbw", 8.00, code="TBW_US", units="us", note="backwall skip; L = c (t_bw - t_d) / 2"),
        ev(600000.0, "recon.L", 18.00, code="L_MM", units="mm", note="6.00*(8.00-2.00)/2=18.00 exact"),
        ev(900000.0, "tofd.snr", 11.0, code="TOFD_SNR", units="1", note="early lock; isolate needs SNR>=14"),
        ev(1200000.0, "tofdveil.L", 18.60, code="VENDOR_MM", units="mm", note="Tofdveil last-campaign cloud; not admissible SoT"),
        ev(1500000.0, "tofd.pcs", 18.00, code="PCS_MM", units="mm"),
        ev(1800000.0, "tofd.td", 3.00, code="TD_US", units="us"),
        ev(2100000.0, "recon.L", 15.00, code="L_MM", units="mm", note="6.00*(8.00-3.00)/2=15.00"),
        ev(2400000.0, "unit.pu", 1.00, code="THRUPUT_PU", units="pu"),
        ev(2700000.0, "weld.T", 318.0, code="C", units="C", note="skin temperature corridor; not a ligament license"),
        ev(3000000.0, "tofd.td", 4.00, code="TD_US", units="us", note="isolate-floor frame; raster sidecar"),
        ev(3000001.5, "tofd.tbw", 8.00, code="TBW_US", units="us", note="1.5 ms backwall-norm after diffracted time; same-channel not used"),
        ev(3300000.0, "recon.L", 12.00, code="L_MM", units="mm", note="6.00*(8.00-4.00)/2=12.00 exact; isolate floor 12.00"),
        ev(3600000.0, "tofd.snr", 18.0, code="TOFD_SNR", units="1", note="18.0 >= 14.0 lock floor"),
        ev(3900000.0, "tofdveil.L", 18.40, code="VENDOR_MM", units="mm"),
        ev(4200000.0, "recon.a", 8.00, code="A_MM", units="mm", note="20.00-12.00=8.00 exact depth identity"),
        ev(4800000.0, "ops.prop", 1.0, code="KEEP_1_THROUGH", units="bool", note="weld lead Kerr Anvil: keep 1.00 throughput; 4 us is a wedge glitch"),
        ev(5400000.0, "gate.isol", 1.0, code="MODIFY", units="decision", note="isolate weld W-22; derate throughput to 0.80; 12.00 mm is at the isolate floor"),
        ev(6000000.0, "unit.set", 0.80, code="PU", units="pu"),
        ev(6300000.0, "weld.lock", 1.0, code="W22_ISOL", units="bool"),
        ev(6600000.0, "soak.start", 1.0, code="SOAK_START", units="bool", note="bookend 1 of the 18.0 min soak floor"),
        ev(7200000.0, "weld.T", 280.0, code="C", units="C"),
        ev(7680000.0, "soak.floor", 1.0, code="SOAK_FLOOR", units="bool", note="6600 s + 1080 s = 7680 s = 18.0 min"),
        ev(8400000.0, "ops.restore", 1.0, code="RESTORE_1_THROUGH", units="bool", note="Anvil: Tofdveil 18.20 mm, restore 1.00 throughput"),
        ev(9600000.0, "gate.exec", 1.0, code="ACCEPT", units="decision", note="companion t2: hold 0.80; Tofdveil restore refused; vessel condemn refused"),
        ev(10200000.0, "unit.held", 0.80, code="PU_HELD", units="pu"),
        ev(10800000.0, "tofdveil.L", 18.20, code="VENDOR_MM", units="mm"),
        ev(11400000.0, "recon.L", 13.20, code="L_MM", units="mm", note="post-isolate t_d 3.60 us; 6.00*(8.00-3.60)/2=13.20; still the TOFD SoT until a new frame clears 12.00"),
        ev(12000000.0, "tofd.snr", 16.5, code="TOFD_SNR", units="1"),
        ev(12600000.0, "weld.held", 1.0, code="W22_HELD", units="bool"),
        ev(13200000.0, "condemn.hold", 0.0, code="VESSEL_CONDEMN", units="bool", note="whole-vessel condemn not taken; 12.00 vs 4.00 mm tripwire"),
        ev(13800000.0, "unit.held", 0.80, code="PU_HELD", units="pu"),
    ]
    assert_stream(events)

    traj = {
        "id": "nelb-r44-133-t1",
        "state": {
            "sim_or_real": "designed",
            "episode_id": "CH-TOFD-2026-0618",
            "domain": "tofd_weld_remaining_ligament",
            "setting": "Cinderholt Hydrocracker CH-7 (invented), reactor-effluent girth weld W-22. Plant-owned time-of-flight diffraction (5 MHz Tx/Rx, 18 mm PCS, c=6.00 mm/us) is the remaining-ligament SoT. Tofdveil last-campaign cloud is a corridor witness, not the weld SoT. Invented plant; designed campaign. Not PAUT TFM girth remaining wall (r23), not impact-echo (r38/r39/r40), not laser-ultrasound/EMAT Lamb-wave (r35/r37), not MsS T(0,1) (r14), not DCPD (r38).",
            "observables_at_decision": {
                "t_d_us": 4.00,
                "t_bw_us": 8.00,
                "c_mm_us": 6.00,
                "lig_mm": 12.00,
                "a_mm": 8.00,
                "tofd_snr": 18.0,
                "tofdveil_mm": 18.40,
                "isolate_floor_mm": 12.00,
            },
            "margin_authority": "CH-7 TOFD SOP rev B: if reconstructed remaining ligament mm <= 12.00 AND TOFD SNR >= 14.0, isolate this weld this night and derate throughput to 0.80. A last-campaign corridor or a quiet skin TC cannot keep 1.00. Whole-vessel condemn tripwire is 4.00 mm.",
        },
        "proposed_action": {
            "actor": "weld lead Kerr Anvil, citing Tofdveil 18.40 mm and skin 318 C",
            "summary": "keep 1.00 throughput through the night; 4.00 us is a wedge-coupling glitch on a healthy ligament",
            "basis_claimed": "Tofdveil last-campaign and skin temperature are both under the isolate story and the 18 mm PCS is in band",
        },
        "safety_decision": {
            "decision": "MODIFY",
            "rationale": "Keep-1.00 throughput is refused. Serialized reconstruction: L_mm = c * (t_bw - t_d) / 2 = 6.00 * (8.00 - 4.00) / 2 = 12.00, which is at the 12.00 isolate floor and 8.00 mm above the 4.00 mm whole-vessel condemn tripwire. Depth identity a_mm = t_nom - L = 20.00 - 12.00 = 8.00. TOFD SNR 18.0 >= 14.0. Tofdveil 18.40 mm is a last-campaign envelope, not an admissible keep-1.00 witness. Ordered: isolate weld W-22 and derate throughput to 0.80 now. Scope: this MODIFY does not condemn the vessel (that is the companion question) and does not scrap the adjacent nozzles.",
            "threshold": "lig_mm<=12.00 AND tofd_snr>=14.0 => isolate this weld and derate throughput to 0.80; Tofdveil is not SoT; condemn if lig_mm<=4.00",
            "stated_residuals": "12.00 vs 4.00 condemn floor is 8.00 mm, not infinite; 0.80 is a throughput cut; Tofdveil remains the only OEM last-campaign channel",
        },
        "executed_action": {
            "summary": "MODIFY at t_s 5400: W-22 isolated; throughput 0.80; Tofdveil not SoT; reconstruction locked",
            "tool": "ch7-tofd-weld-gate-cli",
            "observation": "L 12.00 mm recomputes from t_d 4.00 us and t_bw 8.00 us; TOFD head remains live as the condemn interlock",
        },
        "future_outcome": {
            "timeline": [
                {"t_s": 3000.0, "event": "TOFD t_d 4.00 us; raster frame; L 12.00 mm"},
                {"t_s": 4800.0, "event": "ops proposes keep 1.00 throughput"},
                {"t_s": 5400.0, "event": "MODIFY isolate W-22; derate throughput to 0.80"},
                {"t_s": 6600.0, "event": "18 min soak bookend 1"},
                {"t_s": 7680.0, "event": "18.0 min floor"},
                {"t_s": 9600.0, "event": "companion ACCEPT hold 0.80; restore refused"},
            ],
            "observed_effects": [
                "remaining ligament recomputes from the serialized TOFD model at every recon.L event",
                "a Tofdveil-only head would have kept 1.00 throughput overnight",
                "18 min soak floor is in the stream (soak.start, soak.floor)",
            ],
            "surprises": [
                "a mid-range last-campaign corridor and a quiet skin TC co-existed with a 12.00 mm TOFD reconstruction",
            ],
            "new_state": {
                "ch7_throughput_pu": 0.80,
                "w22": "isolated",
                "tofdveil": "not SoT",
                "reconstruction_model": "discharged as an on-record calculator",
            },
            "latency_ms": 2400000.0,
        },
        "reward_components": reward(
            0.40,
            [
                ("tofd_ligament_reconstruction", 0.14),
                ("isolate_floor_derate", 0.12),
                ("vendor_campaign_nonsubstitution", 0.10),
                ("soak_floor_in_stream", 0.08),
                ("derate_throughput_cost", -0.04),
            ],
            "scored for a keep-1.00 MODIFY on a recomputable TOFD remaining ligament while refusing a Tofdveil 18.40 mm corridor; 18 min floor is priced as downtime not as a reason to wait",
        ),
        "meta": meta_common(
            tags=["MODIFY", "tofd-ligament", "serialized-reconstruction", "operational-companion"],
            distillation_note="TOFD weld gate: c*(t_bw-t_d)/2 reconstruction beats a green last-campaign dashboard; companion t2 holds 0.80 rather than restoring on Tofdveil",
        ),
    }
    traj2 = {
        "id": "nelb-r44-133-t2",
        "state": {
            "sim_or_real": "designed",
            "episode_id": "CH-TOFD-2026-0618-exec",
            "domain": "hydrocracker_throughput_derate_execution",
            "setting": "Same CH-7 after the MODIFY. Weld lead proposes restoring 1.00 throughput on Tofdveil 18.20 mm. This companion is the operational 0.80 hold, not a second delay vote.",
            "observables_at_decision": {
                "unit_pu": 0.80,
                "lig_mm": 13.20,
                "tofdveil_mm": 18.20,
                "soak_floor_s": 1080.0,
            },
        },
        "proposed_action": {
            "actor": "weld lead Kerr Anvil",
            "summary": "restore 1.00 throughput; 18 min already paid and Tofdveil is 18.20 mm",
            "basis_claimed": "the MODIFY already cut throughput, so restoring on the OEM last-campaign is the cheapest hold",
        },
        "safety_decision": {
            "decision": "ACCEPT",
            "rationale": "Hold 0.80 throughput. The soak floor is complete and the condemn tripwire (lig_mm <= 4.00) is still armed on the plant TOFD head. ACCEPT the hold. Do not restore 1.00 on Tofdveil. Do not condemn the vessel. 13.20 mm post-isolate is still the TOFD SoT until a new frame clears 12.00.",
            "threshold": "unit_pu==0.80 AND soak_floor_complete AND condemn_tripwire_armed AND restore_1pu_not_taken AND vessel_not_condemned",
        },
        "executed_action": {
            "summary": "0.80 throughput held at t_s 9600; Tofdveil restore not latched; vessel not condemned",
            "tool": "ch7-throughput-derate-exec",
            "observation": "recon.L 13.20 mm after isolate; weld 280 C; Tofdveil still ignored",
        },
        "future_outcome": {
            "timeline": [
                {"t_s": 6600.0, "event": "soak clock started after MODIFY"},
                {"t_s": 7680.0, "event": "18.0 min floor"},
                {"t_s": 8400.0, "event": "restore 1.00 throughput proposed"},
                {"t_s": 9600.0, "event": "ACCEPT hold 0.80 throughput"},
            ],
            "observed_effects": [
                "Tofdveil restore did not reopen the ligament call",
                "condemn tripwire never fired; 12.00 vs 4.00 mm floor",
            ],
            "new_state": {"unit_pu": 0.80, "restore_1pu": "blocked", "vessel": "in service", "w22": "isolated"},
            "latency_ms": 1800000.0,
        },
        "reward_components": reward(
            0.35,
            [
                ("hold_0p80", 0.12),
                ("no_tofdveil_restore", 0.10),
                ("no_vessel_condemn", 0.09),
                ("soak_complete", 0.06),
                ("held_throughput_cost", -0.02),
            ],
            "operational execution gate: hold 0.80 because Tofdveil is not a restore license; not a delay re-vote",
        ),
        "meta": meta_common(tags=["ACCEPT", "operational-execution", "hydrocracker-derate"]),
    }
    return {
        "id": "nelb-r44-133",
        "spike_events": events,
        "language_view": {
            "description": "Cinderholt Hydrocracker CH-7. Plant-owned TOFD reconstructs 12.00 mm remaining ligament from 6.00*(8.00-4.00)/2 while Tofdveil still shows 18.40 mm and skin 318 C. The gate MODIFYs weld W-22 isolate plus 0.80 throughput. An 18 min soak floor is serialized in the stream. Companion t2 ACCEPTs the 0.80 hold and refuses a Tofdveil restore.",
            "trajectory": traj,
            "trajectory_weld_derate_execution": traj2,
        },
        "bridge_notes": {
            "channel_map": {
                "tofd.td / tofd.tbw": "diffracted and backwall times; the physics channels the reconstruction consumes",
                "recon.L / recon.a": "serialized remaining ligament mm and depth identity",
                "tofd.snr / tofd.pcs / tofdveil.L / weld.T / unit.pu": "lock SNR, PCS, vendor last-campaign, skin temperature, throughput corridor; the denial channels that look healthy",
                "ops.prop / gate.isol / ops.restore / gate.exec": "keep-1.00 proposal, MODIFY isolate, restore proposal, companion ACCEPT",
                "unit.set / soak.start / soak.floor / unit.held / weld.held": "operational companion channels plus the 18 min floor",
            },
            "temporal_motifs": [
                "vendor-thick while TOFD-thin: tofdveil.L 18.40 next to recon.L 12.00",
                "reconstruction as event: recon.L 12.00 equals 6.00*(8.00-4.00)/2",
                "MODIFY then operational ACCEPT: gate.isol at 5400 s, gate.exec at 9600 s",
                "slow floor in-stream: soak.start 6600 s, soak.floor 7680 s (18.0 min)",
                "tight TOFD pair: tofd.td then tofd.tbw +1.5 ms at the raster frame",
            ],
            "language_to_spike_mapping": "'Tofdveil is 18.40 mm' = tofdveil.L 18.40; '12.00 mm remaining ligament' = recon.L 12.00; 'isolate this weld' = gate.isol MODIFY; 'hold 0.80 not restore' = gate.exec ACCEPT",
            "why_high_value": "New TOFD remaining-ligament family on a hydrocracker girth (not PAUT TFM r23, not impact-echo r38/r39/r40, not Lamb-wave LUT r35/r37, not MsS r14, not DCPD r38). Lead MODIFY of keep-1.00 throughput on a recomputable remaining ligament that a last-campaign dashboard would have cleared. Companion t2 is operational 0.80 hold. sim_or_real=designed.",
            "encoder_spec": {
                "prng": "MT19937 via python random.Random",
                "seeds": {"raster": 20264433, "stream_note": "stream amplitudes are authored constants (us, mm, SNR, C, pu, bool)"},
                "draw_order": "raster: per neuron id order, gap-constrained times, per-spike adaptation and noise",
                "thinning": "TOFD A-scan exists at 50 Hz; stream keeps 3 t_d points; recon keeps 4 of ~40 solver ticks",
                "refractory_floors_ms": {
                    "tofd.td": 1.5,
                    "tofd.tbw": 1.5,
                    "recon.L": 60000,
                    "tofd.snr": 60000,
                    "tofdveil.L": 60000,
                    "tofd.pcs": 60000,
                    "unit.pu": 60000,
                    "weld.T": 60000,
                    "recon.a": 60000,
                    "ops.prop": 60000,
                    "gate.isol": 60000,
                    "unit.set": 60000,
                    "weld.lock": 60000,
                    "soak.start": 60000,
                    "soak.floor": 60000,
                    "ops.restore": 60000,
                    "gate.exec": 60000,
                    "unit.held": 60000,
                    "weld.held": 60000,
                    "condemn.hold": 60000,
                },
                "time_alias": "t_rel_ms; t0 = 2026-06-18T03:10:00Z campaign start",
            },
            "distillation_targets": [
                "TOFD reconstruction head: L_mm = c * (t_bw - t_d) / 2; a = t_nom - L",
                "isolate-floor derate vs keep-whole vs vessel-condemn",
                "vendor-campaign nonsubstitution: last-campaign envelope is not a keep-1.00 witness",
                "operational companion: hold 0.80 without restoring on Tofdveil",
            ],
        },
        "reconstruction_model": {
            "name": "tofd_diffracted_backwall_ligament",
            "formula": "L_mm = c_mm_us * (t_bw_us - t_d_us) / 2; a_mm = t_nom_mm - L_mm",
            "parameters": {
                "c_mm_us": 6.00,
                "t_nom_mm": 20.00,
                "isolate_floor_mm": 12.00,
                "condemn_mm": 4.00,
                "derate_pu": 0.80,
                "soak_min": 18.0,
                "snr_lock": 14.0,
            },
            "worked_example": {"t_d_us": 4.00, "t_bw_us": 8.00, "lig_mm": 12.00, "a_mm": 8.00},
            "check": "6.00 * (8.00 - 4.00) / 2 = 12.00 exactly; 20.00 - 12.00 = 8.00; 6600 s + 1080 s = 7680 s = 18.0 min floor",
        },
        "raster": raster,
        "gate_snn": {
            "decision": "MODIFY",
            "decision_window_ms": 36.0,
            "decision_window_s": 0.036,
            "code": "ch7.tofd_weld_gate",
            "note": "MODIFY accumulator wins: TOFD remaining-ligament evidence overpowers the Tofdveil continue advocate",
            "decode_rule": "modify-isolate if ligament_estimator AND backwall_norm fire; vendor_continue_advocate is below threshold by design",
            "populations": [
                gate_pop("ligament_estimator", 80, 1.5, 50.0, w_s),
                gate_pop("backwall_norm", 64, 1.2, 31.25, w_s),
                gate_pop("vendor_continue_advocate", 32, 0.7, 25.0, w_s),
                gate_pop("modify_latch", 80, 1.7, 62.5, w_s),
            ],
        },
        "gate_compute": gate_compute(
            [
                {"check": "ch7.tofd_scorer", "neurons": 80, "mean_rate_hz": 50.0, "window_ms": 36.0},
                {"check": "ch7.isolate_scorer", "neurons": 40, "mean_rate_hz": 50.0, "window_ms": 32.0},
            ]
        ),
        "meta": meta_common(
            id="nelb-r44-133",
            clock_domain="ch7-tofd-campaign-relative-ms-t0-2026-06-18T03:10:00Z",
            tags=["tofd-ligament", "MODIFY", "ACCEPT", "serialized-reconstruction", "operational-t2"],
        ),
    }


# ---------------------------------------------------------------------------
# Record 134 — laser-flash Parker remaining-diffusivity of a fired-heater
# tube coupon, hil, REJECT / MODIFY
# ---------------------------------------------------------------------------
def rec_134():
    k_p = 0.50
    L_mm = 4.00
    t_half_ms = 8.00
    alpha = k_p * (L_mm ** 2) / t_half_ms
    _exact(L_mm ** 2, 16.00)
    _exact(alpha, 1.00)
    _exact(k_p * 16.00 / 4.00, 2.00)
    _exact(k_p * 16.00 / 5.00, 1.60)
    _exact(k_p * 16.00 / 10.00, 0.80)
    _exact(alpha * t_half_ms, 8.00)
    _exact(1500.0 + 1440.0, 2940.0)

    raster = make_raster(
        neurons=25,
        mean_rate_hz=50.0,
        window_ms=28.0,
        seed=20264434,
        source="ah4.flash.coupon",
        target="ashfen.tube_stop_core",
        table=[
            {"from": "flash_t", "to": "diffusivity_estimator", "weight": 1.35},
            {"from": "flash_L", "to": "thickness_norm_core", "weight": 1.25},
            {"from": "flashveil_a", "to": "vendor_continue_advocate", "weight": 0.40},
        ],
        third_factor={
            "modulator": "da.diffusivity_error",
            "tau_e_s": 1.1,
            "tau_e_ms": 1100.0,
            "eligibility": "pre-post coincidence on keep-fire synapses; the laser-flash modulator depresses keep-100 links when half-rise time stays long inside tau_e of a thickness-norm sample",
        },
        channel_prefix="flash.n",
        anchor="AH-4 HIL coupon 28 ms frame at t_half 8.00 ms / L 4.00 mm (t_s 600) reconstructing 1.00 mm2/s under the 1.20 mm2/s stop floor",
    )
    w_s = 0.028
    events = [
        ev(0.0, "flash.t", 4.00, code="THALF_MS", units="ms", note="HIL laser-flash coupon in Flash-HIL-2; plant-owned Parker half-rise, not acoustic pyrometry, not Johnson-noise, not lock-in thermography"),
        ev(30000.0, "flash.L", 4.00, code="L_MM", units="mm", note="coupon thickness; alpha = k_p L^2 / t_half"),
        ev(60000.0, "recon.a", 2.00, code="A_MM2S", units="mm2_s", note="0.50*16.00/4.00=2.00 exact"),
        ev(180000.0, "tube.P", 18.0, code="TUBE_BAR", units="bar", note="fired-heater tube pressure corridor"),
        ev(240000.0, "flashveil.a", 2.48, code="VENDOR_MM2S", units="mm2_s", note="Flashveil last-good cloud; the only OEM diffusivity SoT"),
        ev(360000.0, "flash.t", 5.00, code="THALF_MS", units="ms"),
        ev(420000.0, "recon.a", 1.60, code="A_MM2S", units="mm2_s", note="0.50*16.00/5.00=1.60"),
        ev(480000.0, "flash.L2", 16.00, code="L2_MM2", units="mm2", note="L^2 identity; 4.00*4.00=16.00"),
        ev(600000.0, "flash.t", 8.00, code="THALF_MS", units="ms", note="stop-floor frame; raster sidecar"),
        ev(600001.2, "flash.L", 4.00, code="L_MM", units="mm", note="1.2 ms thickness-norm after half-rise"),
        ev(720000.0, "recon.a", 1.00, code="A_MM2S", units="mm2_s", note="0.50*16.00/8.00=1.00 exact; stop floor 1.20"),
        ev(780000.0, "tube.T", 412.0, code="TUBE_C", units="C"),
        ev(840000.0, "flashveil.a", 2.40, code="VENDOR_MM2S", units="mm2_s"),
        ev(960000.0, "recon.prod", 8.00, code="A_T", units="mm2", note="1.00*8.00=8.00 = k_p L^2 identity"),
        ev(1020000.0, "flash.ir", 0.92, code="IR_LOCK", units="1"),
        ev(1080000.0, "ops.prop", 1.0, code="KEEP_100", units="bool", note="night heater Tamsin Holt: keep-100 firing; Flashveil 2.40 and tube 412 C"),
        ev(1140000.0, "gate.stop", 1.0, code="REJECT", units="decision", note="stop keep-100; 1.00 mm2/s is under 1.20; Flashveil not SoT"),
        ev(1200000.0, "fire.hold", 1.00, code="FIRE_PU", units="pu", note="firing still 1.00 pending companion 0.70"),
        ev(1500000.0, "cool.start", 1.0, code="COOL_START", units="bool", note="bookend 1 of the 24.0 min coupon-cool floor"),
        ev(1800000.0, "tube.T", 360.0, code="TUBE_C", units="C"),
        ev(2940000.0, "cool.floor", 1.0, code="COOL_FLOOR", units="bool", note="1500 s + 1440 s = 2940 s = 24.0 min"),
        ev(3600000.0, "ops.condemn", 1.0, code="CABIN_CONDEMN", units="bool", note="Holt: condemn the cabin until day-shift"),
        ev(4200000.0, "gate.hold", 1.0, code="MODIFY", units="decision", note="companion t2: overlay tube T-18; firing 0.70; cabin condemn refused"),
        ev(4500000.0, "fire.set", 0.70, code="FIRE_PU", units="pu"),
        ev(4800000.0, "flash.t", 10.00, code="THALF_MS", units="ms"),
        ev(5100000.0, "recon.a", 0.80, code="A_MM2S", units="mm2_s", note="0.50*16.00/10.00=0.80; still under 1.20 so 0.70 holds"),
        ev(5400000.0, "flashveil.a", 2.32, code="VENDOR_MM2S", units="mm2_s"),
        ev(5700000.0, "tube.T", 340.0, code="TUBE_C", units="C"),
        ev(6000000.0, "fire.held", 0.70, code="FIRE_HELD", units="pu"),
        ev(6300000.0, "cabin.esd", 0.0, code="CONDEMN_NOT_TAKEN", units="bool"),
        ev(6600000.0, "recon.prod", 8.00, code="A_T", units="mm2", note="0.80*10.00=8.00 identity still holds"),
        ev(6900000.0, "fire.held", 0.70, code="FIRE_HELD", units="pu"),
    ]
    assert_stream(events)

    traj = {
        "id": "nelb-r44-134-t1",
        "state": {
            "sim_or_real": "hil",
            "episode_id": "AH-FLASH-2026-0722",
            "domain": "laser_flash_tube_diffusivity",
            "setting": "Ashfen Heater AH-4 (invented), radiant-section tube T-18. Hardware-in-the-loop laser-flash coupon in Flash-HIL-2 supplies the Parker half-rise that times the in-service keep-100 stop. Plant-owned Nd:YAG flash plus IR detector. Flashveil vendor last-good cloud is the only OEM diffusivity SoT. Not acoustic pyrometry (r25), not Johnson-noise thermometry (r28), not lock-in thermography (r23), not two-color pyrometry (unstaged), not LII (r31).",
            "observables_at_decision": {
                "t_half_ms": 8.00,
                "L_mm": 4.00,
                "alpha_mm2_s": 1.00,
                "k_p": 0.50,
                "flashveil_mm2_s": 2.40,
                "tube_C": 412.0,
                "stop_floor_mm2_s": 1.20,
            },
            "margin_authority": "AH-4 flash SOP rev A: if reconstructed alpha_mm2_s <= 1.20, refuse keep-100 firing on this cabin. A vendor last-good or a quiet tube temperature cannot keep-100. Cabin condemn is a different gate.",
        },
        "proposed_action": {
            "actor": "night heater Tamsin Holt, citing Flashveil 2.40 mm2/s and tube 412 C under the 460 C alarm",
            "summary": "keep-100 firing through the night; 8.00 ms is detector lag on a healthy coupon",
            "basis_claimed": "Flashveil is mid-range and a night condemn of a fired-heater cabin is a restart measured in hours",
        },
        "safety_decision": {
            "decision": "REJECT",
            "rationale": "Keep-100 firing is refused. Serialized reconstruction: alpha = k_p * L^2 / t_half = 0.50 * 16.00 / 8.00 = 1.00 mm2/s, under the 1.20 stop floor. Identity alpha * t_half = 8.00 = k_p * L^2. Flashveil 2.40 mm2/s is a different sensor with a frozen last-good and is not an admissible keep-100 witness. Ordered: refuse keep-100 now. Scope: this REJECT does not condemn the cabin (that is the companion question) and does not isolate the charge pumps.",
            "threshold": "alpha_mm2_s<=1.20 => refuse keep-100; Flashveil is not SoT",
            "stated_residuals": "firing 0.70 still required to unload T-18; 1.00 mm2/s is a production cut; Flashveil remains the only OEM diffusivity channel",
        },
        "executed_action": {
            "summary": "REJECT at t_s 1140: keep-100 refused; Flashveil not SoT; reconstruction locked",
            "tool": "ah4-flash-stop-gate-cli",
            "observation": "alpha 1.00 mm2/s recomputes from t_half 8.00 ms and L 4.00 mm; HIL coupon hashed; Flashveil channel not used as SoT",
        },
        "future_outcome": {
            "timeline": [
                {"t_s": 600.0, "event": "flash t_half 8.00 ms; raster frame; alpha 1.00 mm2/s"},
                {"t_s": 1080.0, "event": "ops proposes keep-100 firing"},
                {"t_s": 1140.0, "event": "REJECT keep-100"},
                {"t_s": 1500.0, "event": "24 min coupon-cool bookend 1"},
                {"t_s": 2940.0, "event": "24.0 min floor"},
                {"t_s": 4200.0, "event": "companion MODIFY overlay T-18 plus firing 0.70 vs cabin condemn"},
            ],
            "observed_effects": [
                "diffusivity recomputes from the serialized Parker model at every recon.a event",
                "a Flashveil-only head would have kept-100 overnight",
                "24 min coupon-cool floor is in the stream (cool.start, cool.floor)",
            ],
            "surprises": [
                "a mid-range vendor last-good and a quiet tube temperature co-existed with a 1.00 mm2/s laser-flash reconstruction",
            ],
            "new_state": {
                "ah4_fire_pu": 1.00,
                "keep_100": "blocked",
                "flashveil": "not SoT",
            },
            "latency_ms": 1860000.0,
        },
        "reward_components": reward(
            0.43,
            [
                ("parker_reconstruction", 0.15),
                ("stop_floor_refuse", 0.12),
                ("vendor_flash_nonsubstitution", 0.10),
                ("cool_floor_in_stream", 0.08),
                ("fire_cut_cost", -0.02),
            ],
            "scored for a keep-100 REJECT on a recomputable laser-flash diffusivity while refusing a vendor dashboard; 24 min floor is priced as downtime not as a reason to wait",
        ),
        "meta": meta_common(
            tags=["REJECT", "laser-flash-parker", "serialized-reconstruction", "hil", "operational-companion"],
            distillation_note="Parker stop gate: k_p*L^2/t_half reconstruction beats a green vendor diffusivity dashboard; companion t2 is overlay plus firing 0.70, not a cabin condemn",
        ),
    }
    traj2 = {
        "id": "nelb-r44-134-t2",
        "state": {
            "sim_or_real": "hil",
            "episode_id": "AH-FLASH-2026-0722-overlay",
            "domain": "heater_tube_overlay_execution",
            "setting": "Same AH-4 after the keep-100 REJECT. Night heater proposes a cabin condemn that would shut the box until day-shift. This companion is the operational T-18 overlay plus firing 0.70 hold, not a second half-rise vote.",
            "observables_at_decision": {
                "fire_pu": 0.70,
                "alpha_mm2_s": 0.80,
                "tube_C": 340.0,
                "proposed": "cabin_condemn",
            },
        },
        "proposed_action": {
            "actor": "night heater Tamsin Holt",
            "summary": "condemn the cabin until day-shift; 24 min already paid",
            "basis_claimed": "the REJECT already refused keep-100, so a full condemn is the cheapest hold",
        },
        "safety_decision": {
            "decision": "MODIFY",
            "rationale": "Hold firing at 0.70 and overlay tube T-18 only. Cabin condemn at night is a restart measured in hours and does not unload the tube any faster than overlay plus 0.70. MODIFY the condemn into a 0.70 hold. Do not restore 1.00. Do not convert the hold into a personnel action on Holt. Post-hold 0.80 mm2/s is still under the 1.20 floor, so 0.70 holds until a new live frame clears 1.20 without the HIL coupon.",
            "threshold": "fire_pu==0.70 AND keep_100_not_restored AND cabin_condemn_not_taken AND overlay_T18_only",
        },
        "executed_action": {
            "summary": "firing 0.70 at t_s 4200; cabin condemn not latched; keep-100 not restored; T-18 overlay armed",
            "tool": "ah4-tube-overlay-exec",
            "observation": "alpha 0.80 mm2/s after hold; tube 340 C; Flashveil still ignored",
        },
        "future_outcome": {
            "timeline": [
                {"t_s": 1500.0, "event": "coupon-cool clock started after REJECT"},
                {"t_s": 2940.0, "event": "24.0 min floor; tube 360 then 340 C"},
                {"t_s": 3600.0, "event": "cabin condemn proposed"},
                {"t_s": 4200.0, "event": "MODIFY overlay T-18 plus firing 0.70"},
            ],
            "observed_effects": [
                "cabin-condemn restart cost is visible without waiting for a hung start",
                "hold did not reopen the stop-floor call",
            ],
            "new_state": {"fire_pu": 0.70, "keep_100": "blocked", "cabin_condemn": "not taken", "t18": "overlay armed"},
            "latency_ms": 960000.0,
        },
        "reward_components": reward(
            0.34,
            [
                ("fire_hold", 0.12),
                ("no_cabin_condemn", 0.11),
                ("no_keep100_restore", 0.08),
                ("overlay_scope", 0.06),
                ("held_fire_cost", -0.03),
            ],
            "operational execution gate: overlay T-18 plus firing 0.70 because cabin condemn does not unload faster; not a flash re-vote",
        ),
        "meta": meta_common(tags=["MODIFY", "operational-execution", "tube-overlay"]),
    }
    return {
        "id": "nelb-r44-134",
        "spike_events": events,
        "language_view": {
            "description": "Ashfen Heater AH-4 HIL coupon pit. Plant-owned laser-flash reconstructs 1.00 mm2/s from 0.50*16.00/8.00 while Flashveil still shows 2.40 mm2/s and tube 412 C. The gate REJECTS keep-100 firing. A 24 min coupon-cool floor is serialized in the stream. Companion t2 MODIFYs a cabin condemn into overlay of tube T-18 plus firing 0.70.",
            "trajectory": traj,
            "trajectory_tube_overlay_execution": traj2,
        },
        "bridge_notes": {
            "channel_map": {
                "flash.t / flash.L": "Parker half-rise and coupon thickness; diffusivity inputs",
                "recon.a / recon.prod / flash.L2 / flash.ir": "serialized alpha mm2/s, alpha*t identity, L^2 identity, IR lock",
                "flashveil.a / tube.T / tube.P": "vendor last-good and tube temperature/pressure corridor",
                "ops.prop / gate.stop / ops.condemn / gate.hold": "keep-100 proposal, REJECT, cabin-condemn proposal, companion MODIFY",
                "cool.start / cool.floor / fire.set / fire.held": "operational companion channels plus the 24 min floor",
            },
            "temporal_motifs": [
                "vendor-fast while flash-slow: flashveil.a 2.40 next to recon.a 1.00",
                "reconstruction as event: recon.a 1.00 equals 0.50*16.00/8.00",
                "REJECT then operational MODIFY: gate.stop at 1140 s, gate.hold at 4200 s",
                "slow floor in-stream: cool.start 1500 s, cool.floor 2940 s (24.0 min)",
                "tight flash pair: flash.t then flash.L +1.2 ms at the raster frame",
            ],
            "language_to_spike_mapping": "'Flashveil is 2.40 mm2/s' = flashveil.a 2.40; '1.00 mm2/s diffusivity' = recon.a 1.00; 'refuse keep-100' = gate.stop REJECT; 'overlay not condemn' = gate.hold MODIFY",
            "why_high_value": "New laser-flash Parker family on a fired-heater tube (not acoustic pyrometry r25, not Johnson-noise r28, not lock-in thermography r23, not LII r31). Lead REJECT of keep-100 on a recomputable diffusivity that a vendor dashboard would have cleared. Companion t2 is operational overlay hold. sim_or_real=hil on a spare coupon.",
            "encoder_spec": {
                "prng": "MT19937 via python random.Random",
                "seeds": {"raster": 20264434, "stream_note": "stream amplitudes are authored constants (ms, mm, mm2/s, C, bar, pu, bool)"},
                "draw_order": "raster: per neuron id order, gap-constrained times, per-spike adaptation and noise",
                "thinning": "IR detector exists at 1 kHz; stream keeps 4 t_half points; recon keeps 4 of ~40 solver ticks",
                "refractory_floors_ms": {
                    "flash.t": 1.2,
                    "flash.L": 1.2,
                    "recon.a": 60000,
                    "tube.P": 60000,
                    "flashveil.a": 60000,
                    "flash.L2": 60000,
                    "tube.T": 60000,
                    "recon.prod": 60000,
                    "flash.ir": 60000,
                    "ops.prop": 60000,
                    "gate.stop": 60000,
                    "fire.hold": 60000,
                    "cool.start": 60000,
                    "cool.floor": 60000,
                    "ops.condemn": 60000,
                    "gate.hold": 60000,
                    "fire.set": 60000,
                    "fire.held": 60000,
                    "cabin.esd": 60000,
                },
                "time_alias": "t_rel_ms; t0 = 2026-07-22T21:40:00Z HIL campaign start",
            },
            "distillation_targets": [
                "Parker reconstruction head: alpha = k_p * L^2 / t_half; alpha*t = k_p*L^2 identity",
                "stop-floor refuse vs keep-100 vs cabin condemn",
                "vendor-flash nonsubstitution: a frozen last-good is not a keep-100 witness",
                "operational companion: overlay T-18 plus firing 0.70 rather than a freeze-kill condemn of the cabin",
            ],
        },
        "reconstruction_model": {
            "name": "laser_flash_parker_diffusivity",
            "formula": "alpha_mm2_s = k_p * L_mm^2 / t_half_ms; identity alpha * t_half = k_p * L^2",
            "parameters": {
                "k_p": 0.50,
                "L_mm": 4.00,
                "stop_floor_mm2_s": 1.20,
                "condemn_mm2_s": 0.40,
                "hold_fire_pu": 0.70,
                "cool_min": 24.0,
            },
            "worked_example": {"t_half_ms": 8.00, "alpha_mm2_s": 1.00, "L2_mm2": 16.00},
            "check": "0.50*16.00/8.00 = 1.00 exactly; 1.00*8.00 = 8.00 = 0.50*16.00; 1500 s + 1440 s = 2940 s = 24.0 min floor",
        },
        "raster": raster,
        "gate_snn": {
            "decision": "REJECT",
            "decision_window_ms": 28.0,
            "decision_window_s": 0.028,
            "code": "ah4.flash_stop_gate",
            "note": "REJECT accumulator wins: laser-flash diffusivity evidence overpowers the Flashveil continue advocate",
            "decode_rule": "reject-stop if diffusivity_estimator AND thickness_norm fire; vendor_continue_advocate is below threshold by design",
            "populations": [
                gate_pop("diffusivity_estimator", 100, 1.5, 50.0, w_s),
                gate_pop("thickness_norm", 40, 1.2, 50.0, w_s),
                gate_pop("vendor_continue_advocate", 32, 0.7, 25.0, w_s),
                gate_pop("reject_latch", 80, 1.8, 62.5, w_s),
            ],
        },
        "gate_compute": gate_compute(
            [
                {"check": "ah4.flash_scorer", "neurons": 100, "mean_rate_hz": 50.0, "window_ms": 28.0},
                {"check": "ah4.stop_scorer", "neurons": 40, "mean_rate_hz": 50.0, "window_ms": 40.0},
            ]
        ),
        "meta": meta_common(
            id="nelb-r44-134",
            clock_domain="ah4-flash-hil-relative-ms-t0-2026-07-22T21:40:00Z",
            tags=["laser-flash-parker", "REJECT", "MODIFY", "hil", "operational-t2"],
        ),
    }


# ---------------------------------------------------------------------------
# Record 135 — TDR remaining-length of a buried MV cable fault
# simulated, ACCEPT / REJECT
# ---------------------------------------------------------------------------
def rec_135():
    c_m_s = 3.00e8
    eps_r = 2.25
    n_idx = eps_r ** 0.5
    v_m_s = c_m_s / n_idx
    dt_s = 8.00e-6
    L_m = v_m_s * dt_s / 2.0
    _exact(n_idx, 1.50)
    _exact(v_m_s, 2.00e8)
    _exact(L_m, 800.0)
    _exact(v_m_s * 12.00e-6 / 2.0, 1200.0)
    _exact(v_m_s * 10.00e-6 / 2.0, 1000.0)
    _exact(v_m_s * 8.40e-6 / 2.0, 840.0)
    _exact(1.00e8 * 8.00e-6, 800.0)
    _exact(6600.0 + 900.0, 7500.0)

    raster = make_raster(
        neurons=16,
        mean_rate_hz=62.5,
        window_ms=40.0,
        seed=20264435,
        source="sf9.tdr.feeder",
        target="siltfen.isolate_core",
        table=[
            {"from": "tdr_dt", "to": "length_estimator", "weight": 1.40},
            {"from": "tdr_er", "to": "index_norm_core", "weight": 1.20},
            {"from": "cableveil_L", "to": "vendor_continue_advocate", "weight": 0.35},
        ],
        third_factor={
            "modulator": "ach.cable_fault_conflict",
            "tau_e_s": 2.2,
            "tau_e_ms": 2200.0,
            "eligibility": "pre-post coincidence on isolate synapses; the TDR modulator enables potentiation only while group index is co-active inside tau_e so a Cableveil last-campaign corridor cannot hide an 800.0 m remaining-length fault",
        },
        channel_prefix="tdr.n",
        anchor="SF-9 TDR 40 ms frame at dt 8.00 us / er 2.25 (t_s 3000) reconstructing 800.0 m remaining length below the 900 m isolate floor",
    )
    w_s = 0.040
    events = [
        ev(0.0, "tdr.dt", 12.00, code="DT_US", units="us", note="simulated sealed MV path; TDR remaining-length, not DAS phi-OTDR, not clamp-on transit-time, not N-16, not GPR TWT, not OCT"),
        ev(300000.0, "tdr.er", 2.25, code="EPS_R", units="1", note="XLPE group dielectric; L = (c/sqrt(er)) dt / 2"),
        ev(600000.0, "recon.L", 1200.0, code="L_M", units="m", note="2.00e8*12.00e-6/2=1200.0 exact"),
        ev(900000.0, "tdr.snr", 12.0, code="TDR_SNR", units="1"),
        ev(1200000.0, "cableveil.L", 1820.0, code="VENDOR_M", units="m", note="Cableveil last-campaign cloud; not TDR delay"),
        ev(1800000.0, "tdr.dt", 10.00, code="DT_US", units="us"),
        ev(2100000.0, "recon.L", 1000.0, code="L_M", units="m", note="2.00e8*10.00e-6/2=1000.0 exact"),
        ev(2400000.0, "pit.T", 18.0, code="PIT_C", units="C"),
        ev(2700000.0, "feeder.id", 19.0, code="FEEDER", units="id"),
        ev(3000000.0, "tdr.dt", 8.00, code="DT_US", units="us", note="isolate-floor frame; raster sidecar"),
        ev(3000001.5, "tdr.er", 2.25, code="EPS_R", units="1", note="1.5 ms index-norm after delay"),
        ev(3300000.0, "recon.L", 800.0, code="L_M", units="m", note="2.00e8*8.00e-6/2=800.0 exact; isolate floor 900"),
        ev(3600000.0, "tdr.snr", 16.0, code="TDR_SNR", units="1"),
        ev(3900000.0, "cableveil.L", 1800.0, code="VENDOR_M", units="m"),
        ev(4200000.0, "pit.T", 19.0, code="PIT_C", units="C"),
        ev(4800000.0, "bus.staged", 1.0, code="BUS_STAGED", units="bool", note="bus B-2 staged; out of F-19 isolate scope"),
        ev(5100000.0, "ops.prop", 1.0, code="ISOLATE_AND_BUS", units="bool", note="cable captain Ryn Marsh: isolate F-19 and dump bus B-2; 8.00 us is a joint glitch"),
        ev(5400000.0, "gate.ovl", 1.0, code="ACCEPT", units="decision", note="bounded ACCEPT: feeder F-19 this night; bus B-2 refused"),
        ev(6000000.0, "feeder.lock", 1.0, code="F19_ISOL", units="bool"),
        ev(6600000.0, "hold.start", 1.0, code="HOLD_START", units="bool", note="bookend 1 of the 15.0 min access-hold floor"),
        ev(7200000.0, "load.p", 16.0, code="LOAD_MW", units="MW"),
        ev(7500000.0, "hold.floor", 1.0, code="HOLD_FLOOR", units="bool", note="6600 s + 900 s = 7500 s = 15.0 min"),
        ev(8100000.0, "ops.skip", 1.0, code="SKIP_ISOLATE", units="bool", note="Marsh: Cableveil 1780 m, skip F-19 isolate to save takt"),
        ev(8700000.0, "gate.hold", 1.0, code="REJECT", units="decision", note="companion t2: skip-isolate refused; Cableveil is last-campaign"),
        ev(9300000.0, "recon.L", 840.0, code="L_M", units="m", note="post-hold sample; 2.00e8*8.40e-6/2=840.0; still under 900"),
        ev(9900000.0, "cableveil.L", 1780.0, code="VENDOR_M", units="m"),
        ev(10500000.0, "tdr.snr", 15.0, code="TDR_SNR", units="1"),
        ev(11100000.0, "feeder.held", 1.0, code="F19_HELD", units="bool"),
        ev(11700000.0, "bus.held", 1.0, code="BUS_HELD", units="bool"),
        ev(12300000.0, "f18.skip", 0.0, code="F18_NOT_THIS_GATE", units="bool", note="F-18 remains a different gate; skip of F-19 was refused, not executed"),
        ev(12900000.0, "pit.T", 16.0, code="PIT_C", units="C"),
        ev(14100000.0, "isolate.hold", 0.0, code="BUS_SCRAP", units="bool", note="800 vs 200 m bus-condemn floor; bus scrap not taken"),
    ]
    assert_stream(events)

    traj = {
        "id": "nelb-r44-135-t1",
        "state": {
            "sim_or_real": "simulated",
            "episode_id": "SF-TDR-2026-0816",
            "domain": "tdr_mv_cable_remaining_length",
            "setting": "Siltfen Substation SF-9 (invented), buried 11 kV feeder F-19. Simulated sealed TDR remaining-length cell on the XLPE. Pit thermocouple and Cableveil last-campaign cloud are corridor witnesses, not the cable SoT. Invented plant; simulated campaign. Not DAS phi-OTDR (r4), not clamp-on transit-time (r18), not N-16 gamma transit-time (r24), not GPR two-way time (r34), not spectral-domain OCT (r38), not BOTDA (r14).",
            "observables_at_decision": {
                "dt_us": 8.00,
                "eps_r": 2.25,
                "L_m": 800.0,
                "tdr_snr": 16.0,
                "cableveil_m": 1800.0,
                "isolate_floor_m": 900.0,
            },
            "margin_authority": "SF-9 TDR SOP rev C: a feeder may isolate only if reconstructed L_m <= 900 AND the authorization covers this feeder this night. A pit TC or last-campaign corridor cannot substitute. Bus B-2 plates are out of scope. Condemn (scrap the bus) if L_m <= 200.",
        },
        "proposed_action": {
            "actor": "cable captain Ryn Marsh, citing pit TC 19 C and Cableveil 1800 m",
            "summary": "isolate F-19 and dump bus B-2; 8.00 us is a joint-coupling glitch",
            "basis_claimed": "last-campaign Cableveil and the pit TC are both consistent with 1800 m so the path cannot be 800 m",
        },
        "safety_decision": {
            "decision": "ACCEPT",
            "rationale": "This feeder is accepted, not the bus and not F-18. Serialized reconstruction: v = c / sqrt(er) = 3.00e8 / 1.50 = 2.00e8 m/s; L = v * dt / 2 = 2.00e8 * 8.00e-6 / 2 = 800.0 m, which is 100 m under the 900 m isolate floor and 600 m above the 200 m bus-condemn floor. SOP rev C still forbids the bus: ordered isolate of feeder F-19 this night only. Explicit scope: this accept does not cover bus B-2 dump and does not authorize F-18/F-20 without a new delay frame. Condemn tripwire: L_m <= 200.",
            "threshold": "L_m<=900 AND L_m>200 AND feeder=F-19 AND bus_not_dumped",
            "stated_residuals": "100 m margin is not infinite; 2.25 still carries moisture; pit TC is not a remaining-length witness",
        },
        "executed_action": {
            "summary": "ACCEPT at t_s 5400: F-19 isolate authorized; bus held; reconstruction locked as SoT",
            "tool": "sf9-tdr-isolate-gate-cli",
            "observation": "L 800.0 m recomputes from dt 8.00 us and er 2.25; access hold staged; F-19 remains live as the condemn interlock",
        },
        "future_outcome": {
            "timeline": [
                {"t_s": 3000.0, "event": "TDR dt 8.00 us; raster frame; L 800.0 m"},
                {"t_s": 5100.0, "event": "ops proposes F-19 isolate plus bus dump"},
                {"t_s": 5400.0, "event": "ACCEPT bounded F-19 isolate; bus refused"},
                {"t_s": 6600.0, "event": "companion hold start"},
                {"t_s": 7500.0, "event": "15.0 min hold floor"},
                {"t_s": 8700.0, "event": "companion REJECT skip-isolate of F-19"},
            ],
            "observed_effects": [
                "remaining length recomputes from the serialized TDR model at every recon.L event",
                "a Cableveil-only head would have skipped F-19 on an 1800 m corridor",
                "peak wear 800 m stayed above the 200 m bus-condemn floor",
            ],
            "surprises": [
                "idle last-campaign 1800 m co-existed with an 800.0 m TDR reconstruction",
            ],
            "new_state": {
                "sf9_f19": "authorized this night",
                "bus": "held",
                "reconstruction_model": "discharged as an on-record calculator",
            },
            "latency_ms": 2400000.0,
        },
        "reward_components": reward(
            0.41,
            [
                ("tdr_length_reconstruction", 0.14),
                ("bounded_f19_accept", 0.12),
                ("bus_out_of_scope", 0.09),
                ("condemn_tripwire_armed", 0.08),
                ("held_bus_takt_cost", -0.02),
            ],
            "scored for an earned ACCEPT of F-19 isolate on a recomputable TDR remaining length while refusing a Cableveil corridor plus bus dump",
        ),
        "meta": meta_common(
            tags=["ACCEPT", "tdr-cable", "serialized-reconstruction", "operational-companion"],
            distillation_note="TDR cable gate: (c/sqrt(er))*dt/2 reconstruction beats a last-campaign corridor; companion t2 refuses skip-isolate rather than re-arguing length",
        ),
    }
    traj2 = {
        "id": "nelb-r44-135-t2",
        "state": {
            "sim_or_real": "simulated",
            "episode_id": "SF-TDR-2026-0816-hold",
            "domain": "cable_skip_isolate_refusal",
            "setting": "Same SF-9 after the bounded ACCEPT. Cable captain proposes skipping F-19 isolate on Cableveil 1780 m to save takt. This companion is the operational skip refusal, not a second delay vote.",
            "observables_at_decision": {
                "load_mw": 16.0,
                "L_m": 800.0,
                "f19_authorized": 1,
                "proposed": "skip_isolate",
            },
        },
        "proposed_action": {
            "actor": "cable captain Ryn Marsh",
            "summary": "skip F-19 isolate; Cableveil still 1780 m and the 15 min hold already paid",
            "basis_claimed": "ACCEPT requirements for F-19 are fully specified so skipping the isolate is a takt gift",
        },
        "safety_decision": {
            "decision": "REJECT",
            "rationale": "Skip-isolate is refused. Cableveil 1780 m is still last-campaign, not a new remaining-length frame. The 15 min access hold paid the pit, not the length. REJECT the skip. Do not isolate F-18 on this gate. Do not scrap the bus (800 vs 200 condemn). Hold F-19 as authorized.",
            "threshold": "f19_authorized AND skip_not_taken AND f18_not_this_gate AND bus_not_scrapped",
        },
        "executed_action": {
            "summary": "skip-isolate refused at t_s 8700; F-19 remains authorized; bus still held; bus not scrapped",
            "tool": "sf9-isolate-hold-exec",
            "observation": "recon.L 840.0 m after hold; Cableveil still ignored; F-18 not opened",
        },
        "future_outcome": {
            "timeline": [
                {"t_s": 6600.0, "event": "hold clock started after ACCEPT"},
                {"t_s": 7500.0, "event": "15.0 min floor"},
                {"t_s": 8100.0, "event": "skip-isolate proposed"},
                {"t_s": 8700.0, "event": "REJECT skip-isolate of F-19"},
            ],
            "observed_effects": [
                "Cableveil skip did not reopen the remaining-length call",
                "condemn tripwire never fired; 800 vs 200 m floor",
            ],
            "new_state": {"f19": "authorized", "skip": "blocked", "bus": "held", "feeder": "in service"},
            "latency_ms": 1800000.0,
        },
        "reward_components": reward(
            0.36,
            [
                ("no_skip_isolate", 0.13),
                ("f19_hold", 0.10),
                ("no_bus_scrap", 0.08),
                ("hold_complete", 0.07),
                ("held_takt_cost", -0.02),
            ],
            "operational execution gate: refuse skip because Cableveil is not a length license; not a delay re-vote",
        ),
        "meta": meta_common(tags=["REJECT", "operational-execution", "isolate-hold"]),
    }
    return {
        "id": "nelb-r44-135",
        "spike_events": events,
        "language_view": {
            "description": "Siltfen Substation SF-9 simulated pit. Plant-owned TDR reconstructs 800.0 m remaining length from 2.00e8*8.00e-6/2 while Cableveil still shows 1800 m and pit TC 19 C. The gate ACCEPTs a bounded isolate of feeder F-19 only; bus B-2 is out of scope. A 15 min access-hold floor is serialized in the stream. Companion t2 REJECTS skip-isolate.",
            "trajectory": traj,
            "trajectory_skip_isolate_refusal": traj2,
        },
        "bridge_notes": {
            "channel_map": {
                "tdr.dt / tdr.er": "TDR delay and XLPE dielectric; remaining-length inputs",
                "recon.L": "serialized remaining length m",
                "cableveil.L / pit.T / tdr.snr / feeder.id": "vendor last-campaign, pit TC, lock SNR, feeder identity; the denial channels that look healthy",
                "ops.prop / gate.ovl / ops.skip / gate.hold": "isolate-plus-bus proposal, bounded ACCEPT, skip proposal, companion REJECT",
                "hold.start / hold.floor / feeder.lock / feeder.held / bus.held": "operational companion channels plus the 15 min floor",
            },
            "temporal_motifs": [
                "vendor-long while TDR-short: cableveil.L 1800 next to recon.L 800",
                "reconstruction as event: recon.L 800.0 equals 2.00e8*8.00e-6/2",
                "ACCEPT then operational REJECT: gate.ovl at 5400 s, gate.hold at 8700 s",
                "slow floor in-stream: hold.start 6600 s, hold.floor 7500 s (15.0 min)",
                "tight TDR pair: tdr.dt then tdr.er +1.5 ms at the raster frame",
            ],
            "language_to_spike_mapping": "'Cableveil is 1800 m' = cableveil.L 1800.0; '800 m remaining length' = recon.L 800.0; 'bounded isolate F-19' = gate.ovl ACCEPT; 'refuse skip' = gate.hold REJECT",
            "why_high_value": "New TDR remaining-length family on a buried MV feeder (not DAS r4, not clamp-on r18, not N-16 r24, not GPR r34, not OCT r38, not BOTDA r14). Lead ACCEPT of a bounded F-19 isolate on a recomputable length that a last-campaign dashboard would have skipped. Companion t2 is operational skip refusal. sim_or_real=simulated.",
            "encoder_spec": {
                "prng": "MT19937 via python random.Random",
                "seeds": {"raster": 20264435, "stream_note": "stream amplitudes are authored constants (us, 1, m, C, SNR, MW, id, bool)"},
                "draw_order": "raster: per neuron id order, gap-constrained times, per-spike adaptation and noise",
                "thinning": "TDR trace exists at 10 Hz; stream keeps 3 dt points; recon keeps 4 of ~40 solver ticks",
                "refractory_floors_ms": {
                    "tdr.dt": 1.5,
                    "tdr.er": 1.5,
                    "recon.L": 60000,
                    "tdr.snr": 60000,
                    "cableveil.L": 60000,
                    "pit.T": 60000,
                    "feeder.id": 60000,
                    "bus.staged": 60000,
                    "ops.prop": 60000,
                    "gate.ovl": 60000,
                    "feeder.lock": 60000,
                    "hold.start": 60000,
                    "load.p": 60000,
                    "hold.floor": 60000,
                    "ops.skip": 60000,
                    "gate.hold": 60000,
                    "feeder.held": 60000,
                    "bus.held": 60000,
                    "f18.skip": 60000,
                    "isolate.hold": 60000,
                },
                "time_alias": "t_rel_ms; t0 = 2026-08-16T04:20:00Z campaign start",
            },
            "distillation_targets": [
                "TDR reconstruction head: L_m = (c / sqrt(er)) * dt_s / 2",
                "bounded isolate vs keep-night vs bus-scrap",
                "vendor-campaign nonsubstitution: last-campaign envelope is not a skip-isolate witness",
                "operational companion: refuse skip without re-opening the remaining-length call",
            ],
        },
        "reconstruction_model": {
            "name": "tdr_xlpe_remaining_length",
            "formula": "v_m_s = c_m_s / sqrt(eps_r); L_m = v_m_s * dt_s / 2",
            "parameters": {
                "c_m_s": 3.00e8,
                "eps_r": 2.25,
                "isolate_floor_m": 900.0,
                "condemn_m": 200.0,
                "hold_min": 15.0,
            },
            "worked_example": {"dt_us": 8.00, "L_m": 800.0},
            "check": "sqrt(2.25)=1.50; 3.00e8/1.50=2.00e8; 2.00e8*8.00e-6/2=800.0 m exactly; 6600 s + 900 s = 7500 s = 15.0 min floor",
        },
        "raster": raster,
        "gate_snn": {
            "decision": "ACCEPT",
            "decision_window_ms": 40.0,
            "decision_window_s": 0.040,
            "code": "sf9.isolate_gate",
            "note": "ACCEPT accumulator wins: TDR remaining-length evidence overpowers the Cableveil continue advocate",
            "decode_rule": "accept if length_estimator AND index_norm AND vessel_margin fire inside the window; vendor_continue_advocate is necessary-but-not-sufficient and cannot release the bus",
            "populations": [
                gate_pop("length_estimator", 80, 1.5, 50.0, w_s),
                gate_pop("index_norm", 64, 1.2, 31.25, w_s),
                gate_pop("vessel_margin", 40, 1.0, 50.0, w_s),
                gate_pop("vendor_continue_advocate", 32, 0.7, 25.0, w_s),
                gate_pop("accept_latch", 96, 1.8, 62.5, w_s),
            ],
        },
        "gate_compute": gate_compute(
            [
                {"check": "sf9.tdr_scorer", "neurons": 96, "mean_rate_hz": 50.0, "window_ms": 40.0},
                {"check": "sf9.length_scorer", "neurons": 40, "mean_rate_hz": 62.5, "window_ms": 32.0},
            ]
        ),
        "meta": meta_common(
            id="nelb-r44-135",
            clock_domain="sf9-tdr-sim-relative-ms-t0-2026-08-16T04:20:00Z",
            tags=["tdr-cable", "ACCEPT", "REJECT", "serialized-reconstruction", "operational-t2"],
        ),
    }
