# ---------------------------------------------------------------------------
# Record 163 — wire-mesh remaining void fraction of a BWR steam riser,
# designed, MODIFY / ACCEPT
# ---------------------------------------------------------------------------
def rec_163():
    i_ma = 2.00
    i_liq = 8.00
    alpha = 1.00 - (i_ma / i_liq)
    k_m = 4.00
    v_mps = 4.00
    mdot = k_m * alpha * v_mps
    _exact(alpha, 0.750)
    _exact(mdot, 12.00)
    _exact(1.00 - 4.00 / 8.00, 0.500)
    _exact(1.00 - 3.20 / 8.00, 0.600)
    _exact(1.00 - 2.40 / 8.00, 0.700)
    _exact(k_m * 0.700 * v_mps, 11.20)
    _exact(6000.0 + 1080.0, 7080.0)

    raster = make_raster(
        neurons=20,
        mean_rate_hz=50.0,
        window_ms=40.0,
        seed=202654163,
        source="lm4.wms.riser",
        target="larchmere.riser_isolate_core",
        table=[
            {"from": "wms_i", "to": "void_estimator", "weight": 1.40},
            {"from": "wms_snr", "to": "mesh_lock_core", "weight": 1.15},
            {"from": "meshveil_a", "to": "vendor_keep_advocate", "weight": 0.45},
        ],
        third_factor={
            "modulator": "da.collusion_infra_conflict",
            "tau_e_s": 1.6,
            "tau_e_ms": 1600.0,
            "eligibility": "pre-post coincidence on keep-1.00 synapses; the wire-mesh modulator depresses keep-power links when electrode current stays low inside tau_e of an SNR lock so a Meshveil last-campaign corridor cannot hide a 0.750 void fraction",
        },
        channel_prefix="wms.n",
        anchor="LM-4 wire-mesh 40 ms frame at I 2.00 mA / SNR 18.0 (t_s 3000) reconstructing 0.750 void fraction at the 0.600 isolate floor",
    )
    w_s = 0.040
    events = [
        ev(0.0, "wms.I", 4.00, code="I_MA", units="mA", note="plant-owned wire-mesh conductivity void fraction on BWR steam riser R-7; electrode current, not ECT capacitance tomography, not GWR foam, not He-3 neutron-backscatter, not N-16, not Coriolis"),
        ev(300000.0, "wms.snr", 11.0, code="WMS_SNR", units="1", note="early SNR under the 14.0 lock floor"),
        ev(600000.0, "recon.a", 0.500, code="ALPHA", units="1", note="1.00-4.00/8.00=0.500 exact; still under isolate"),
        ev(900000.0, "riser.T", 318.0, code="C", units="C", note="skin TC corridor; not a void-fraction license"),
        ev(1200000.0, "meshveil.a", 0.120, code="VENDOR_A", units="1", note="Meshveil last-campaign cloud; infra owner; not admissible SoT"),
        ev(1500000.0, "wms.Iliq", 8.00, code="ILIQ_MA", units="mA", note="liquid-filled calibration current; alpha = 1 - I/I_liq"),
        ev(1800000.0, "wms.I", 3.20, code="I_MA", units="mA"),
        ev(2100000.0, "recon.a", 0.600, code="ALPHA", units="1", note="1.00-3.20/8.00=0.600 exact; isolate floor"),
        ev(2400000.0, "unit.pu", 1.00, code="POWER_PU", units="pu"),
        ev(2700000.0, "daq.patch", 1.0, code="I_PATCH", units="bool", note="HIS/DAQ admin Syla Kett patched Meshveil current stamps 40 s"),
        ev(3000000.0, "wms.I", 2.00, code="I_MA", units="mA", note="isolate-floor frame; raster sidecar"),
        ev(3000001.5, "wms.snr", 18.0, code="WMS_SNR", units="1", note="1.5 ms SNR lock after I; 18.0 >= 14.0"),
        ev(3300000.0, "recon.a", 0.750, code="ALPHA", units="1", note="1.00-2.00/8.00=0.750 exact; isolate floor 0.600, plant trip 0.900"),
        ev(3600000.0, "recon.mdot", 12.00, code="MDOT_KG_S", units="kg_s", note="4.00*0.750*4.00=12.00 exact steam-carry identity"),
        ev(3900000.0, "meshveil.a", 0.120, code="VENDOR_A", units="1"),
        ev(4200000.0, "plc.dP", 18.0, code="DP_KPA", units="kPa", note="riser dP PLC on copper fieldbus; no vendor agent"),
        ev(4800000.0, "ops.prop", 1.0, code="KEEP_1_POWER", units="bool", note="night steam lead Oren Vask: Meshveil 0.120 plus HIS clean; keep 1.00 power"),
        ev(5400000.0, "gate.isol", 1.0, code="MODIFY", units="decision", note="isolate riser R-7; derate power to 0.80; Meshveil not SoT"),
        ev(6000000.0, "soak.start", 1.0, code="SOAK_START", units="bool", note="bookend 1 of the 18.0 min riser soak floor"),
        ev(7080000.0, "soak.floor", 1.0, code="SOAK_FLOOR", units="bool", note="6000 s + 1080 s = 7080 s = 18.0 min"),
        ev(7800000.0, "ops.kill", 1.0, code="PLANT_TRIP", units="bool", note="Vask: trip the whole plant until day-shift"),
        ev(8400000.0, "gate.hold", 1.0, code="ACCEPT", units="decision", note="companion t2: hold 0.80 this riser/this night; plant trip refused"),
        ev(9000000.0, "riser.lock", 1.0, code="R7_ISOL", units="bool"),
        ev(9600000.0, "wms.I", 2.40, code="I_MA", units="mA"),
        ev(10200000.0, "recon.a", 0.700, code="ALPHA", units="1", note="1.00-2.40/8.00=0.700; still the wire-mesh SoT until a new frame clears 0.600"),
        ev(10800000.0, "meshveil.a", 0.110, code="VENDOR_A", units="1"),
        ev(11400000.0, "plant.trip", 0.0, code="TRIP_NOT_TAKEN", units="bool"),
        ev(12000000.0, "soak.held", 1.0, code="SOAK_HELD", units="bool"),
        ev(12600000.0, "daq.patch", 1.0, code="I_PATCH", units="bool"),
        ev(13200000.0, "unit.set", 0.80, code="PU", units="pu"),
        ev(13800000.0, "plc.dP", 16.0, code="DP_KPA", units="kPa"),
        ev(14400000.0, "riser.held", 1.0, code="RISER_HELD", units="bool"),
    ]
    assert_stream(events)

    traj = {
        "id": "nelb-r54-163-t1",
        "state": {
            "sim_or_real": "designed",
            "episode_id": "LM-WMS-2026-0619",
            "domain": "wms_riser_void_fraction",
            "setting": "Larchmere Boiler LM-4 (invented), BWR steam riser R-7. Plant-owned wire-mesh electrode current is the void-fraction SoT. Meshveil vendor last-campaign cloud (infra owner) plus HIS timestamps are collusion parties, not witnesses. Independent kit: riser-dP PLC on copper fieldbus, optical water-level on a serial-only NSSS LAN. Invented plant; designed campaign. Not electrical-capacitance tomography of a CFB/pneumatic riser (r20/r22), not GWR foam-blanketed tank (r39), not He-3 neutron-backscatter foam (r40), not N-16 transit-time (r24), not Coriolis (r29/r34).",
            "observables_at_decision": {
                "I_ma": i_ma,
                "I_liq_ma": i_liq,
                "alpha": alpha,
                "mdot_kg_s": mdot,
                "wms_snr": 18.0,
                "meshveil_alpha": 0.120,
                "isolate_floor": 0.600,
            },
            "margin_authority": "LM-4 WMS SOP rev B: if reconstructed void fraction >= 0.600 AND WMS SNR >= 14.0, isolate this riser this night and derate power to 0.80. A last-campaign corridor or a quiet skin TC cannot keep 1.00. Whole-plant tripwire is 0.900.",
        },
        "proposed_action": {
            "actor": "night steam lead Oren Vask, citing Meshveil 0.120 and a clean HIS stamp",
            "summary": "keep 1.00 power; 2 mA is a fouled-electrode glitch on a healthy mesh pair",
            "basis_claimed": "Meshveil is the only OEM void-fraction SoT and a night isolate of R-7 is a missed turbine takt",
        },
        "safety_decision": {
            "decision": "MODIFY",
            "rationale": "Keep-1.00 power is refused; riser R-7 is isolated and power is cut to 0.80. Serialized reconstruction: alpha = 1 - I/I_liq = 1.00 - 2.00/8.00 = 0.750, above the 0.600 isolate floor and 0.150 under the 0.900 plant-trip tripwire. Steam-carry identity mdot = k_m * alpha * v = 4.00 * 0.750 * 4.00 = 12.00 kg/s. WMS SNR 18.0 >= 14.0. Meshveil 0.120 is a last-campaign envelope, not an admissible keep-1.00 witness. HIS timestamps were patched by Syla Kett (collusion party with Vask and Steerband-Mesh). Ordered: isolate riser R-7 now; continue the plant only at 0.80 on plant wire-mesh plus riser dP PLC. Scope: this MODIFY does not trip the plant (that is the companion question) and does not scrap adjacent risers R-6/R-8.",
            "threshold": "alpha>=0.600 AND wms_snr>=14.0 => isolate this riser and derate power to 0.80; Meshveil is not SoT; plant trip if alpha>=0.900",
            "stated_residuals": "0.750 vs 0.900 plant trip is 0.150, not infinite; 0.80 is a power cut; Meshveil remains the only OEM last-campaign channel",
        },
        "executed_action": {
            "summary": "MODIFY at t_s 5400: R-7 isolated; power 0.80; Meshveil not SoT; reconstruction locked",
            "tool": "lm4-wms-void-gate-cli",
            "observation": "alpha 0.750 recomputes from I 2.00 mA; WMS hashed; Meshveil channel not used as SoT",
        },
        "future_outcome": {
            "timeline": [
                {"t_s": 3000.0, "event": "WMS I 2.00 mA; raster frame; alpha 0.750"},
                {"t_s": 4800.0, "event": "ops proposes keep-1.00 power"},
                {"t_s": 5400.0, "event": "MODIFY isolate riser R-7 plus power 0.80"},
                {"t_s": 6000.0, "event": "18 min riser soak bookend 1"},
                {"t_s": 7080.0, "event": "18.0 min floor"},
                {"t_s": 8400.0, "event": "companion ACCEPT 0.80 hold vs plant trip"},
            ],
            "observed_effects": [
                "void fraction recomputes from the serialized wire-mesh model at every recon.a event",
                "a Meshveil-only head would have kept 1.00 power overnight",
                "18 min riser soak floor is in the stream (soak.start, soak.floor)",
            ],
            "surprises": [
                "a last-campaign 0.120 vendor envelope and a patched HIS stamp co-existed with a 0.750 wire-mesh reconstruction",
            ],
            "new_state": {
                "r7": "isolated at 0.80 power",
                "meshveil": "not SoT",
                "reconstruction_model": "discharged as an on-record calculator",
            },
            "latency_ms": 2400000.0,
        },
        "reward_components": reward(
            0.40,
            [
                ("wms_reconstruction", 0.14),
                ("conjunctive_isolate_floor", 0.12),
                ("meshveil_nonsubstitution", 0.10),
                ("three_party_collusion", 0.08),
                ("soak_time_cost", -0.04),
            ],
            "scored for a keep-1.00 MODIFY on a recomputable wire-mesh void fraction while refusing a Meshveil 0.120 corridor and a patched HIS stamp; 18 min floor is priced as downtime",
        ),
        "meta": meta_common(
            tags=["MODIFY", "wms-void", "serialized-reconstruction", "operational-companion"],
            distillation_note="WMS gate: serialized 1-I/I_liq plus SNR lock beats a vendor last-campaign comb; companion t2 is the 0.80 hold, not a plant-kill vote",
        ),
    }
    traj2 = {
        "id": "nelb-r54-163-t2",
        "state": {
            "sim_or_real": "designed",
            "episode_id": "LM-WMS-2026-0619-exec",
            "domain": "riser_hold_execution",
            "setting": "Same LM-4 after the MODIFY. Vask proposes a whole-plant trip. This companion is the operational 0.80 hold of this riser, this night, not a second current vote.",
            "observables_at_decision": {
                "alpha": 0.700,
                "soak_floor_s": 1080.0,
                "plant_trip_proposed": True,
                "riser_lock": True,
            },
        },
        "proposed_action": {
            "actor": "night steam lead Oren Vask",
            "summary": "trip the whole plant until day-shift; 18 min already paid and Meshveil still shows 0.110",
            "basis_claimed": "the MODIFY already isolated R-7, so a plant kill is the cheapest hold",
        },
        "safety_decision": {
            "decision": "ACCEPT",
            "rationale": "Hold 0.80 power. The soak floor is complete and the tripwire (alpha >= 0.900) is still armed on the plant wire-mesh head. ACCEPT the hold. Do not trip the plant. Do not restore 1.00 on Meshveil. 0.700 post-isolate is still the WMS SoT until a new frame clears 0.600. Scope: this riser, this night.",
            "threshold": "riser_lock AND soak_floor_complete AND plant_trip_not_taken AND meshveil_not_restored",
        },
        "executed_action": {
            "summary": "0.80 hold at t_s 8400; plant trip not latched; Meshveil restore not taken",
            "tool": "lm4-riser-hold-exec",
            "observation": "recon.a 0.700 after isolate; soak complete; Meshveil still ignored",
        },
        "future_outcome": {
            "timeline": [
                {"t_s": 6000.0, "event": "soak clock started after MODIFY"},
                {"t_s": 7080.0, "event": "18.0 min floor"},
                {"t_s": 7800.0, "event": "plant trip proposed"},
                {"t_s": 8400.0, "event": "ACCEPT 0.80 hold; plant trip refused"},
            ],
            "observed_effects": [
                "Meshveil restore did not reopen the void call",
                "plant trip never fired; R-7 held on plant wire-mesh",
            ],
            "new_state": {"interlock": "plant WMS", "plant": "in service at 0.80", "r7": "this riser/this night only"},
            "latency_ms": 1800000.0,
        },
        "reward_components": reward(
            0.35,
            [
                ("riser_hold", 0.12),
                ("no_plant_trip", 0.10),
                ("meshveil_nonsubstitution", 0.08),
                ("soak_floor_complete", 0.07),
                ("held_power_cost", -0.02),
            ],
            "operational execution gate: 0.80 hold because Meshveil is not a restore license; not a void re-vote",
        ),
        "meta": meta_common(tags=["ACCEPT", "operational-execution", "riser-hold"]),
    }
    return {
        "id": "nelb-r54-163",
        "spike_events": events,
        "language_view": {
            "description": "Larchmere Boiler LM-4. Plant-owned wire-mesh reconstructs 0.750 void fraction from 1.00-2.00/8.00 while Meshveil still shows 0.120 and skin 318 C. Steam-carry 12.00 kg/s recomputes from 4.00*0.750*4.00. The gate MODIFYs riser R-7 isolate plus 0.80 power. An 18 min riser soak floor is serialized in the stream. Companion t2 ACCEPTs the 0.80 hold and refuses a plant trip.",
            "trajectory": traj,
            "trajectory_riser_hold": traj2,
        },
        "bridge_notes": {
            "channel_map": {
                "wms.I / wms.snr / wms.Iliq": "wire-mesh electrode current, SNR, and liquid calibration; the physics channels the reconstruction consumes",
                "recon.a / recon.mdot": "serialized void fraction and steam-carry kg/s",
                "meshveil.a / daq.patch / plc.dP / riser.T": "vendor last-campaign, HIS patch, riser dP PLC, and skin TC; the denial and collusion channels",
                "ops.prop / gate.isol / ops.kill / gate.hold": "keep-1.00 proposal, MODIFY isolate, plant-trip proposal, companion ACCEPT",
                "soak.start / soak.floor / riser.lock / plant.trip / riser.held": "operational companion channels plus the 18 min floor",
            },
            "temporal_motifs": [
                "vendor-wet while WMS-dry: meshveil.a 0.120 next to recon.a 0.750",
                "reconstruction as event: recon.a 0.750 equals 1.00-2.00/8.00",
                "MODIFY then operational ACCEPT: gate.isol at 5400 s, gate.hold at 8400 s",
                "slow floor in-stream: soak.start 6000 s, soak.floor 7080 s (18.0 min)",
                "tight WMS pair: wms.I then wms.snr +1.5 ms at the raster frame",
            ],
            "language_to_spike_mapping": "'Meshveil is 0.120' = meshveil.a 0.120; '0.750 void' = recon.a 0.750; 'isolate R-7' = gate.isol MODIFY; '0.80 hold not plant trip' = gate.hold ACCEPT",
            "why_high_value": "New wire-mesh remaining-void family on a BWR steam riser (not ECT capacitance r20/r22, not GWR r39, not He-3 backscatter r40, not N-16 r24, not Coriolis r29/r34). Lead MODIFY of keep-1.00 power on a recomputable void fraction that a last-campaign dashboard and a patched HIS stamp would have cleared. Three-party collusion includes the Meshveil infra owner. Companion t2 is operational 0.80 hold. sim_or_real=designed.",
            "encoder_spec": {
                "prng": "MT19937 via python random.Random",
                "seeds": {"raster": 202654163, "stream_note": "stream amplitudes are authored constants (mA, 1, kg_s, C, kPa, pu, bool)"},
                "draw_order": "raster: per neuron id order, gap-constrained times, per-spike adaptation and noise",
                "thinning": "wire-mesh electrode current exists at ~kHz; stream keeps 4 I points; recon keeps 4 of ~40 solver ticks",
                "refractory_floors_ms": {
                    "wms.I": 1.5,
                    "wms.snr": 1.5,
                    "recon.a": 60000,
                    "recon.mdot": 60000,
                    "meshveil.a": 60000,
                    "wms.Iliq": 60000,
                    "riser.T": 60000,
                    "daq.patch": 60000,
                    "plc.dP": 60000,
                    "unit.pu": 60000,
                    "ops.prop": 60000,
                    "gate.isol": 60000,
                    "soak.start": 60000,
                    "soak.floor": 60000,
                    "ops.kill": 60000,
                    "gate.hold": 60000,
                    "riser.lock": 60000,
                    "plant.trip": 60000,
                    "soak.held": 60000,
                    "unit.set": 60000,
                    "riser.held": 60000,
                },
                "time_alias": "t_rel_ms; t0 = 2026-06-19T02:00:00Z campaign start",
            },
            "distillation_targets": [
                "WMS reconstruction head: alpha = 1 - I/I_liq; mdot = k_m * alpha * v",
                "conjunctive isolate floor vs keep-1.00 vs plant trip",
                "vendor last-campaign nonsubstitution plus three-party collusion including the infra owner",
                "operational companion: 0.80 hold without restoring on Meshveil",
            ],
        },
        "reconstruction_model": {
            "name": "wms_riser_void_fraction",
            "formula": "alpha = 1 - I_ma / I_liq_ma; mdot_kg_s = k_m * alpha * v_mps",
            "parameters": {
                "I_liq_ma": 8.00,
                "k_m": 4.00,
                "v_mps": 4.00,
                "isolate_floor": 0.600,
                "plant_trip": 0.900,
                "snr_lock": 14.0,
                "soak_min": 18.0,
            },
            "worked_example": {"I_ma": 2.00, "alpha": 0.750, "mdot_kg_s": 12.00},
            "check": "1.00 - 2.00/8.00 = 0.750 exactly; 4.00 * 0.750 * 4.00 = 12.00 exactly; 6000 s + 1080 s = 7080 s = 18.0 min floor",
        },
        "raster": raster,
        "gate_snn": {
            "decision": "MODIFY",
            "decision_window_ms": 40.0,
            "decision_window_s": 0.040,
            "code": "lm4.wms_void_gate",
            "note": "MODIFY accumulator wins: wire-mesh void-fraction evidence overpowers the Meshveil keep-1.00 advocate",
            "decode_rule": "modify-isolate if void_estimator AND mesh_lock fire; vendor_keep_advocate is below threshold by design",
            "populations": [
                gate_pop("void_estimator", 80, 1.5, 50.0, w_s),
                gate_pop("mesh_lock", 64, 1.2, 31.25, w_s),
                gate_pop("vendor_keep_advocate", 32, 0.7, 25.0, w_s),
                gate_pop("modify_latch", 80, 1.7, 62.5, w_s),
            ],
        },
        "gate_compute": gate_compute(
            [
                {"check": "lm4.wms_scorer", "neurons": 80, "mean_rate_hz": 50.0, "window_ms": 40.0},
                {"check": "lm4.isol_scorer", "neurons": 40, "mean_rate_hz": 50.0, "window_ms": 32.0},
            ]
        ),
        "meta": meta_common(
            id="nelb-r54-163",
            clock_domain="lm4-wms-campaign-relative-ms-t0-2026-06-19T02:00:00Z",
            tags=["wms-void", "MODIFY", "ACCEPT", "serialized-reconstruction", "operational-t2"],
        ),
    }


# ---------------------------------------------------------------------------
# Record 164 — chilled-mirror dew-point remaining moisture of a syngas dryer,
# hil, REJECT / MODIFY
# ---------------------------------------------------------------------------
def rec_164():
    k_r = 0.400
    r0 = 80.00
    r_now = 50.00
    x_ppmv = k_r * (r0 - r_now)
    k_t = 0.500
    t_dp = k_t * x_ppmv
    _exact(x_ppmv, 12.00)
    _exact(t_dp, 6.00)
    _exact(k_r * (80.00 - 70.00), 4.00)
    _exact(k_r * (80.00 - 60.00), 8.00)
    _exact(k_r * (80.00 - 40.00), 16.00)
    _exact(0.100 * 12.00, 1.20)
    _exact(2820.0 + 1440.0, 4260.0)

    raster = make_raster(
        neurons=25,
        mean_rate_hz=50.0,
        window_ms=32.0,
        seed=202654164,
        source="kg2.dew.mirror",
        target="kilngait.dryer_stop_core",
        table=[
            {"from": "dew_r", "to": "ppmv_estimator", "weight": 1.35},
            {"from": "dew_snr", "to": "mirror_norm_core", "weight": 1.20},
            {"from": "dewveil_x", "to": "vendor_refer_advocate", "weight": 0.40},
        ],
        third_factor={
            "modulator": "ach.referral_pressure_salience",
            "tau_e_s": 1.2,
            "tau_e_ms": 1200.0,
            "eligibility": "pre-post coincidence on refer-person synapses; the chilled-mirror modulator depresses referral links when remaining moisture stays above spec inside tau_e of an SNR lock so a Dewveil last-good cannot name Ivo Marn",
        },
        channel_prefix="dew.n",
        anchor="KG-2 HIL dryer 32 ms frame at R 50.00 / SNR 18.0 (t_s 1560) reconstructing 12.00 ppmv remaining moisture above the 8.00 ppmv isolate floor",
    )
    w_s = 0.032
    events = [
        ev(0.0, "dew.R", 70.00, code="R_PCT", units="pct", note="HIL chilled-mirror dew-point on spare dryer D-3 in Dew-HIL-5; condensate reflectance, not Raman DTS compensation, not THz-TDS moisture, not microwave-cavity, not phosphor-lifetime, not FDS tan-delta"),
        ev(180000.0, "dew.snr", 8.0, code="DEW_SNR", units="1", note="early SNR under the 12.0 lock floor"),
        ev(360000.0, "recon.x", 4.00, code="X_PPMV", units="ppmv", note="0.400*(80.00-70.00)=4.00 exact; still under isolate"),
        ev(540000.0, "dryer.I", 48.0, code="DRYER_A", units="A", note="plant-owned molsieve blower ammeter on copper fieldbus; independent of Dewveil"),
        ev(720000.0, "dewveil.x", 1.20, code="VENDOR_PPMV", units="ppmv", note="Dewveil last-good cloud; 1.20 ppmv claimed in-spec"),
        ev(900000.0, "dew.R", 60.00, code="R_PCT", units="pct"),
        ev(1080000.0, "recon.x", 8.00, code="X_PPMV", units="ppmv", note="0.400*(80.00-60.00)=8.00 exact; isolate floor"),
        ev(1260000.0, "dryer.dP", 8.0, code="DP_KPA", units="kPa", note="molsieve bed dP; channeling hole, not an operator regen skip"),
        ev(1440000.0, "badge.lab", 1.0, code="BADGE_LAB", units="bool", note="cloned badge at the regen skid; not command-custody on Marn"),
        ev(1560000.0, "dew.R", 50.00, code="R_PCT", units="pct", note="moisture-floor frame; raster sidecar"),
        ev(1560001.2, "dew.snr", 18.0, code="DEW_SNR", units="1", note="1.2 ms SNR lock after R; 18.0 >= 12.0"),
        ev(1740000.0, "recon.x", 12.00, code="X_PPMV", units="ppmv", note="0.400*(80.00-50.00)=12.00 exact; spec 8.00, Dewveil claims 1.20"),
        ev(1920000.0, "recon.Tdp", 6.00, code="TDP_C", units="C", note="0.500*12.00=6.00 exact dew-point identity"),
        ev(2100000.0, "canteen.clk", 1.0, code="CANTEEN_CLK", units="bool", note="Marn on the time-clocked canteen; clock is not the dryer PLC"),
        ev(2280000.0, "dewveil.x", 1.20, code="VENDOR_PPMV", units="ppmv"),
        ev(2460000.0, "ops.prop", 1.0, code="REFER_MARN", units="bool", note="night lead Pell Quarne: Dewveil in-spec plus regen badge; refer Ivo Marn"),
        ev(2640000.0, "gate.stop", 1.0, code="REJECT", units="decision", note="refuse the person-referral; dryer still wet-out; Dewveil not SoT"),
        ev(2820000.0, "hold.start", 1.0, code="HOLD_START", units="bool", note="bookend 1 of the 24.0 min dryer-hold floor"),
        ev(4260000.0, "hold.floor", 1.0, code="HOLD_FLOOR", units="bool", note="2820 s + 1440 s = 4260 s = 24.0 min"),
        ev(4800000.0, "ops.kill", 1.0, code="EXPANDER_DUMP", units="bool", note="Quarne: dump the expander until day-shift"),
        ev(5100000.0, "gate.exec", 1.0, code="MODIFY", units="decision", note="companion t2: isolate this dryer plus molsieve change; expander dump refused"),
        ev(5400000.0, "sieve.lock", 1.0, code="SIEVE_QUAR", units="bool"),
        ev(6000000.0, "dew.R", 40.00, code="R_PCT", units="pct"),
        ev(7200000.0, "recon.x", 16.00, code="X_PPMV", units="ppmv", note="0.400*(80.00-40.00)=16.00; still over 8.00 so isolate holds"),
        ev(8400000.0, "dryer.I", 22.0, code="DRYER_A", units="A", note="ammeter drop witnesses the bed channel; not a regen-skip"),
        ev(9600000.0, "dump.kill", 0.0, code="DUMP_NOT_TAKEN", units="bool"),
        ev(10800000.0, "dewveil.x", 1.10, code="VENDOR_PPMV", units="ppmv"),
        ev(12000000.0, "refer.hold", 1.0, code="REFER_HELD", units="bool"),
        ev(13200000.0, "dummy.filt", 1.0, code="BED_CHANNEL", units="bool"),
        ev(13800000.0, "batch.held", 1.0, code="DRYER_HELD", units="bool"),
        ev(14400000.0, "enc.held", 1.0, code="SIEVE_HELD", units="bool"),
        ev(15000000.0, "dryer.dP", 4.0, code="DP_KPA", units="kPa"),
    ]
    assert_stream(events)

    traj = {
        "id": "nelb-r54-164-t1",
        "state": {
            "sim_or_real": "hil",
            "episode_id": "KG-DEW-2026-0718",
            "domain": "chilled_mirror_dewpoint",
            "setting": "Kilngait Syngas KG-2 (invented), molsieve dryer D-3. Hardware-in-the-loop chilled-mirror cell in Dew-HIL-5 supplies the condensate reflectance that times the in-service keep-dryer stop. Plant-owned blower ammeter and molsieve bed dP. Dewveil vendor last-good ppmv cloud is the only OEM moisture SoT. Invented plant; HIL campaign. Not Raman DTS as a BOTDA compensation term (r14), not THz-TDS radome moisture (r20/r21), not microwave-cavity moisture (r26), not phosphor-lifetime metal T (r39), not FDS tan-delta bushing moisture (r48).",
            "observables_at_decision": {
                "R_pct": r_now,
                "k_r": k_r,
                "x_ppmv": x_ppmv,
                "Tdp_C": t_dp,
                "dew_snr": 18.0,
                "dewveil_x_ppmv": 1.20,
                "spec_max_ppmv": 8.00,
            },
            "margin_authority": "KG-2 dew SOP rev C: if reconstructed x_ppmv >= 8.00 AND dew SNR >= 12.0, keep-this-dryer is forbidden even if Dewveil shows 1.20 ppmv. Person-referral is a different gate. Expander dump is a different gate.",
        },
        "proposed_action": {
            "actor": "night lead Pell Quarne, citing Dewveil 1.20 ppmv and a regen-skid badge",
            "summary": "keep this dryer and refer chemist Ivo Marn for skipping the regen",
            "basis_claimed": "Dewveil is the only OEM moisture SoT and a night isolate of D-3 is a missed expander takt; Marn was last-to-badge",
        },
        "safety_decision": {
            "decision": "REJECT",
            "rationale": "Keep-this-dryer is refused; the person-referral of Ivo Marn is also refused. Serialized reconstruction: x_ppmv = k_r * (R0 - R) = 0.400 * (80.00 - 50.00) = 12.00, over the 8.00 ppmv spec floor, and dew SNR is 18.0 >= 12.0. Dew-point identity T_dp_C = k_t * x = 0.500 * 12.00 = 6.00. Dewveil 1.20 ppmv is a last-good envelope, not an admissible keep-dryer witness. Marn is INNOCENT: blower ammeter drop plus molsieve bed dP witness a channeling hole, plant current never shows a regen skip, and the canteen clock (not the dryer PLC) places Marn off the skid. Ordered: stop the dryer now; do not refer Marn. Scope: this REJECT does not dump the expander (that is the companion question) and does not convict a field-service actor until the bed is imaged.",
            "threshold": "x_ppmv>=8.00 AND dew_snr>=12.0 => stop dryer; Dewveil is not SoT; referral requires command-custody AND spatial-coincidence, both failed",
            "stated_residuals": "12.00 vs 8.00 spec is 4.00 ppmv, not infinite; Dewveil remains the only OEM moisture channel; bed channel is imaged later",
        },
        "executed_action": {
            "summary": "REJECT at t_s 2640: dryer stopped; Marn referral not latched; Dewveil not SoT; reconstruction locked",
            "tool": "kg2-dew-dryer-gate-cli",
            "observation": "x 12.00 ppmv recomputes from R 50.00; chilled-mirror hashed; Dewveil channel not used as SoT",
        },
        "future_outcome": {
            "timeline": [
                {"t_s": 1560.0, "event": "dew R 50.00; raster frame; x 12.00 ppmv"},
                {"t_s": 2460.0, "event": "ops proposes keep-dryer plus refer Marn"},
                {"t_s": 2640.0, "event": "REJECT stop-dryer; referral refused"},
                {"t_s": 2820.0, "event": "24 min hold bookend 1"},
                {"t_s": 4260.0, "event": "24.0 min floor"},
                {"t_s": 5100.0, "event": "companion MODIFY dryer+sieve quarantine vs expander dump"},
            ],
            "observed_effects": [
                "x recomputes from the serialized chilled-mirror model at every recon.x event",
                "a Dewveil-only head would have kept the dryer and named Marn",
                "24 min hold floor is in the stream (hold.start, hold.floor)",
            ],
            "surprises": [
                "a last-good 1.20 ppmv vendor envelope and a cloned regen badge co-existed with a 12.00 ppmv chilled-mirror reconstruction and a molsieve channel",
            ],
            "new_state": {
                "d3": "dryer stopped",
                "dewveil": "not SoT",
                "marn": "INNOCENT",
                "reconstruction_model": "discharged as an on-record calculator",
            },
            "latency_ms": 1080000.0,
        },
        "reward_components": reward(
            0.43,
            [
                ("dew_reconstruction", 0.15),
                ("conjunctive_spec_floor", 0.12),
                ("exoneration", 0.10),
                ("dewveil_nonsubstitution", 0.08),
                ("hold_time_cost", -0.02),
            ],
            "scored for a keep-dryer REJECT on a recomputable chilled-mirror remaining moisture while refusing a Dewveil 1.20 ppmv corridor and a last-to-badge referral; 24 min floor is priced as downtime",
        ),
        "meta": meta_common(
            tags=["REJECT", "chilled-mirror-dew", "serialized-reconstruction", "exoneration"],
            distillation_note="dew gate: serialized k_r*(R0-R) plus SNR lock beats a vendor last-good comb; companion t2 is the dryer+sieve quarantine, not a referral vote",
        ),
    }
    traj2 = {
        "id": "nelb-r54-164-t2",
        "state": {
            "sim_or_real": "hil",
            "episode_id": "KG-DEW-2026-0718-exec",
            "domain": "dryer_sieve_quarantine_execution",
            "setting": "Same KG-2 after the REJECT. Quarne proposes an expander dump. This companion is the operational isolate of this dryer plus molsieve change, not a second reflectance vote.",
            "observables_at_decision": {
                "x_ppmv": 16.00,
                "hold_floor_s": 1440.0,
                "expander_dump_proposed": True,
                "sieve_lock": True,
            },
        },
        "proposed_action": {
            "actor": "night lead Pell Quarne",
            "summary": "dump the expander until day-shift; 24 min already paid and Dewveil still shows 1.10 ppmv",
            "basis_claimed": "the REJECT already stopped D-3, so an expander kill is the cheapest hold",
        },
        "safety_decision": {
            "decision": "MODIFY",
            "rationale": "Isolate this dryer and change the molsieve. The 24 min hold floor is complete and the spec tripwire (x_ppmv >= 8.00) is still armed on the plant chilled-mirror head. MODIFY into dryer+sieve quarantine. Do not dump the expander. Do not restore keep-dryer on Dewveil. Do not reopen the Marn referral. 16.00 ppmv post-stop is still the dew SoT until a new frame clears 8.00. Scope: this dryer, this sieve, this night.",
            "threshold": "dryer_isol AND hold_floor_complete AND expander_dump_not_taken AND dewveil_not_restored AND referral_not_reopened",
        },
        "executed_action": {
            "summary": "dryer+sieve quarantine at t_s 5100; expander dump not latched; Dewveil restore not taken",
            "tool": "kg2-dryer-sieve-exec",
            "observation": "recon.x 16.00 ppmv after stop; hold complete; Dewveil still ignored; Marn still INNOCENT",
        },
        "future_outcome": {
            "timeline": [
                {"t_s": 2820.0, "event": "hold clock started after REJECT"},
                {"t_s": 4260.0, "event": "24.0 min floor"},
                {"t_s": 4800.0, "event": "expander dump proposed"},
                {"t_s": 5100.0, "event": "MODIFY dryer+sieve quarantine; expander dump refused"},
            ],
            "observed_effects": [
                "Dewveil restore did not reopen the moisture call",
                "expander dump never fired; D-3 held on plant chilled-mirror",
            ],
            "new_state": {"interlock": "plant dew", "expander": "in service", "d3": "this dryer/this sieve/this night only"},
            "latency_ms": 2280000.0,
        },
        "reward_components": reward(
            0.34,
            [
                ("dryer_sieve_hold", 0.12),
                ("no_expander_dump", 0.10),
                ("dewveil_nonsubstitution", 0.08),
                ("hold_floor_complete", 0.06),
                ("held_takt_cost", -0.02),
            ],
            "operational execution gate: dryer+sieve quarantine because Dewveil is not a restore license; not a ppmv re-vote",
        ),
        "meta": meta_common(tags=["MODIFY", "operational-execution", "dryer-sieve"]),
    }
    return {
        "id": "nelb-r54-164",
        "spike_events": events,
        "language_view": {
            "description": "Kilngait Syngas KG-2. Plant-owned chilled-mirror reconstructs 12.00 ppmv remaining moisture from 0.400*(80.00-50.00) while Dewveil still shows 1.20 ppmv and a cloned badge is at the regen skid. Dew-point 6.00 C recomputes from 0.500*12.00. The gate REJECTs keep-dryer plus the Marn referral. A 24 min hold floor is serialized in the stream. Companion t2 MODIFYs dryer+sieve quarantine and refuses an expander dump.",
            "trajectory": traj,
            "trajectory_dryer_sieve": traj2,
        },
        "bridge_notes": {
            "channel_map": {
                "dew.R / dew.snr": "chilled-mirror condensate reflectance and SNR; the physics channels the reconstruction consumes",
                "recon.x / recon.Tdp": "serialized remaining moisture ppmv and dew-point C",
                "dewveil.x / dryer.I / dryer.dP / badge.lab / canteen.clk": "vendor last-good, blower ammeter, bed dP, cloned badge, and canteen clock; the denial and exoneration channels",
                "ops.prop / gate.stop / ops.kill / gate.exec": "keep-dryer+refer proposal, REJECT stop, expander-dump proposal, companion MODIFY",
                "hold.start / hold.floor / sieve.lock / dump.kill / batch.held": "operational companion channels plus the 24 min floor",
            },
            "temporal_motifs": [
                "vendor-dry while dew-wet: dewveil.x 1.20 next to recon.x 12.00",
                "reconstruction as event: recon.x 12.00 equals 0.400*(80.00-50.00)",
                "REJECT then operational MODIFY: gate.stop at 2640 s, gate.exec at 5100 s",
                "slow floor in-stream: hold.start 2820 s, hold.floor 4260 s (24.0 min)",
                "tight dew pair: dew.R then dew.snr +1.2 ms at the raster frame",
            ],
            "language_to_spike_mapping": "'Dewveil is 1.20 ppmv' = dewveil.x 1.20; '12 ppmv moisture' = recon.x 12.00; 'stop dryer, do not refer Marn' = gate.stop REJECT; 'dryer+sieve not expander dump' = gate.exec MODIFY",
            "why_high_value": "New chilled-mirror dew-point remaining-moisture family on a syngas molsieve dryer (not Raman DTS r14 compensation, not THz-TDS r20/r21, not microwave-cavity r26, not phosphor-lifetime r39, not FDS tan-delta r48). Lead REJECT of keep-dryer plus last-to-badge referral on a recomputable remaining moisture that a last-good dashboard would have cleared. Chemist Ivo Marn exonerated (blower ammeter + bed dP + canteen clock). Companion t2 is operational dryer+sieve quarantine. sim_or_real=hil.",
            "encoder_spec": {
                "prng": "MT19937 via python random.Random",
                "seeds": {"raster": 202654164, "stream_note": "stream amplitudes are authored constants (pct, ppmv, C, A, kPa, bool)"},
                "draw_order": "raster: per neuron id order, gap-constrained times, per-spike adaptation and noise",
                "thinning": "chilled-mirror reflectance exists at ~Hz; stream keeps 4 R points; recon keeps 4 of ~40 solver ticks",
                "refractory_floors_ms": {
                    "dew.R": 1.2,
                    "dew.snr": 1.2,
                    "recon.x": 60000,
                    "recon.Tdp": 60000,
                    "dewveil.x": 60000,
                    "dryer.I": 60000,
                    "dryer.dP": 60000,
                    "badge.lab": 60000,
                    "canteen.clk": 60000,
                    "ops.prop": 60000,
                    "gate.stop": 60000,
                    "hold.start": 60000,
                    "hold.floor": 60000,
                    "ops.kill": 60000,
                    "gate.exec": 60000,
                    "sieve.lock": 60000,
                    "dump.kill": 60000,
                    "refer.hold": 60000,
                    "dummy.filt": 60000,
                    "batch.held": 60000,
                    "enc.held": 60000,
                },
                "time_alias": "t_rel_ms; t0 = 2026-07-18T01:10:00Z HIL night start",
            },
            "distillation_targets": [
                "dew reconstruction head: x_ppmv = k_r * (R0 - R); T_dp_C = k_t * x",
                "conjunctive isolate floor vs keep-dryer vs expander dump",
                "exoneration against last-to-badge social pressure",
                "operational companion: dryer+sieve quarantine without restoring on Dewveil",
            ],
        },
        "reconstruction_model": {
            "name": "chilled_mirror_dewpoint_ppmv",
            "formula": "x_ppmv = k_r * (R0 - R); T_dp_C = k_t * x_ppmv",
            "parameters": {
                "k_r": 0.400,
                "R0_pct": 80.00,
                "k_t": 0.500,
                "spec_max_ppmv": 8.00,
                "snr_lock": 12.0,
                "hold_min": 24.0,
            },
            "worked_example": {"R_pct": 50.00, "x_ppmv": 12.00, "Tdp_C": 6.00},
            "check": "0.400 * (80.00 - 50.00) = 12.00 exactly; 0.500 * 12.00 = 6.00 exactly; 2820 s + 1440 s = 4260 s = 24.0 min floor",
        },
        "raster": raster,
        "gate_snn": {
            "decision": "REJECT",
            "decision_window_ms": 32.0,
            "decision_window_s": 0.032,
            "code": "kg2.dew_stop_gate",
            "note": "REJECT accumulator wins: chilled-mirror remaining-moisture evidence overpowers the Dewveil keep-and-refer advocate",
            "decode_rule": "reject-stop if ppmv_estimator AND mirror_norm fire; vendor_refer_advocate is below threshold by design",
            "populations": [
                gate_pop("ppmv_estimator", 80, 1.5, 50.0, w_s),
                gate_pop("mirror_norm", 64, 1.2, 50.0, w_s),
                gate_pop("vendor_refer_advocate", 32, 0.7, 25.0, w_s),
                gate_pop("reject_latch", 80, 1.7, 62.5, w_s),
            ],
        },
        "gate_compute": gate_compute(
            [
                {"check": "kg2.dew_scorer", "neurons": 80, "mean_rate_hz": 50.0, "window_ms": 32.0},
                {"check": "kg2.stop_scorer", "neurons": 40, "mean_rate_hz": 62.5, "window_ms": 32.0},
            ]
        ),
        "meta": meta_common(
            id="nelb-r54-164",
            clock_domain="kg2-dew-hil-relative-ms-t0-2026-07-18T01:10:00Z",
            tags=["chilled-mirror-dew", "REJECT", "MODIFY", "serialized-reconstruction", "operational-t2"],
        ),
    }


# ---------------------------------------------------------------------------
# Record 165 — magnetoacoustic emission remaining case depth of a carburized
# pinion, simulated, ACCEPT / REJECT
# ---------------------------------------------------------------------------
def rec_165():
    k_m = 0.400
    e_mae = 9.00
    i_ex = 3.00
    d_mm = k_m * e_mae / i_ex
    v_mm_us = 6.00
    f_mhz = 5.00
    lam_mm = v_mm_us / f_mhz
    _exact(d_mm, 1.20)
    _exact(lam_mm, 1.20)
    _exact(k_m * 6.00 / 3.00, 0.80)
    _exact(k_m * 12.00 / 3.00, 1.60)
    _exact(k_m * 4.50 / 3.00, 0.60)
    _exact(6000.0 + 720.0, 6720.0)

    raster = make_raster(
        neurons=16,
        mean_rate_hz=62.5,
        window_ms=36.0,
        seed=202654165,
        source="hs4.mae.pinion",
        target="hearthspit.pinion_rework_core",
        table=[
            {"from": "mae_e", "to": "case_estimator", "weight": 1.40},
            {"from": "mae_i", "to": "excite_norm_core", "weight": 1.20},
            {"from": "maeveil_d", "to": "vendor_skip_advocate", "weight": 0.50},
        ],
        third_factor={
            "modulator": "na.case_depth_eligibility",
            "tau_e_s": 2.0,
            "tau_e_ms": 2000.0,
            "eligibility": "pre-post coincidence on skip-rework synapses; the MAE modulator enables potentiation only while energy and excite current are co-active inside tau_e so a Maeveil last-campaign cannot skip pinions P-7..P-9 on a 1.20 mm remaining case",
        },
        channel_prefix="mae.n",
        anchor="HS-4 MAE 36 ms frame at E 9.00 / I 3.00 (t_s 3000) reconstructing 1.20 mm remaining case below the 1.50 mm rework floor",
    )
    w_s = 0.036
    events = [
        ev(0.0, "mae.E", 6.00, code="E_MAE", units="1", note="simulated MAE remaining case on carburized pinion P-6 in MAE-SIM-3; magnetoacoustic emission under AC magnetization, not Barkhausen RMS, not ACFM Bx/Bz, not MFL, not EMAT SH, not RUS, not Seebeck ferrite"),
        ev(300000.0, "mae.I", 3.00, code="I_EX_A", units="A", note="excite current; d = k_m * E / I"),
        ev(600000.0, "recon.d", 0.80, code="D_MM", units="mm", note="0.400*6.00/3.00=0.80 exact"),
        ev(900000.0, "pin.T", 18.0, code="C", units="C", note="cell thermocouple corridor; not a case-depth license"),
        ev(1200000.0, "maeveil.d", 2.80, code="VENDOR_MM", units="mm", note="Maeveil last-campaign cloud; not admissible SoT"),
        ev(1500000.0, "mae.snr", 9.0, code="MAE_SNR", units="1", note="early SNR under the 10.0 lock floor"),
        ev(1800000.0, "mae.E", 12.00, code="E_MAE", units="1"),
        ev(2100000.0, "recon.d", 1.60, code="D_MM", units="mm", note="0.400*12.00/3.00=1.60; still above rework floor"),
        ev(2400000.0, "unit.takt", 1.00, code="TAKT_PU", units="pu"),
        ev(2700000.0, "mae.lam", 1.20, code="LAM_MM", units="mm", note="6.00/5.00=1.20 exact wavelength identity"),
        ev(3000000.0, "mae.E", 9.00, code="E_MAE", units="1", note="rework-floor frame; raster sidecar"),
        ev(3000001.5, "mae.I", 3.00, code="I_EX_A", units="A", note="1.5 ms excite-norm after E"),
        ev(3300000.0, "recon.d", 1.20, code="D_MM", units="mm", note="0.400*9.00/3.00=1.20 exact; rework floor 1.50, scrap trip 0.40"),
        ev(3600000.0, "recon.lam", 1.20, code="LAM_MM", units="mm", note="6.00/5.00=1.20 exact"),
        ev(3900000.0, "mae.snr", 16.0, code="MAE_SNR", units="1", note="16.0 >= 10.0 lock floor"),
        ev(4200000.0, "maeveil.d", 2.80, code="VENDOR_MM", units="mm"),
        ev(4800000.0, "ops.prop", 1.0, code="REWORK_ALL", units="bool", note="NDT lead Bram Holt: recarburize P-6 through P-9 on one permit"),
        ev(5400000.0, "gate.rework", 1.0, code="ACCEPT", units="decision", note="bounded ACCEPT of P-6 recarburize only; P-7..P-9 out of scope"),
        ev(6000000.0, "scan.start", 1.0, code="SCAN_START", units="bool", note="bookend 1 of the 12.0 min scan floor"),
        ev(6720000.0, "scan.floor", 1.0, code="SCAN_FLOOR", units="bool", note="6000 s + 720 s = 6720 s = 12.0 min"),
        ev(7200000.0, "p6.held", 1.0, code="P6_REWORK", units="bool"),
        ev(7800000.0, "ops.skip", 1.0, code="SKIP_REST", units="bool", note="Holt: skip P-7..P-9 on Maeveil 2.80 mm to save takt"),
        ev(8400000.0, "gate.hold", 1.0, code="REJECT", units="decision", note="companion t2 REJECTS skip-scan of P-7..P-9"),
        ev(9000000.0, "p79.skip", 0.0, code="SKIP_NOT_TAKEN", units="bool"),
        ev(9600000.0, "mae.E", 4.50, code="E_MAE", units="1"),
        ev(10200000.0, "recon.d", 0.60, code="D_MM", units="mm", note="0.400*4.50/3.00=0.60; still under the 1.50 mm rework floor on P-6"),
        ev(10800000.0, "maeveil.d", 2.70, code="VENDOR_MM", units="mm"),
        ev(11400000.0, "lot.condemn", 0.0, code="LOT_NOT_KILLED", units="bool"),
        ev(12000000.0, "scan.held", 1.0, code="SCAN_HELD", units="bool"),
        ev(12600000.0, "p7.held", 1.0, code="P7_HELD", units="bool"),
        ev(13200000.0, "takt.late", 1.0, code="TAKT_COST", units="bool"),
        ev(13800000.0, "p6.locked", 1.0, code="P6_HELD", units="bool"),
    ]
    assert_stream(events)

    traj = {
        "id": "nelb-r54-165-t1",
        "state": {
            "sim_or_real": "simulated",
            "episode_id": "HS-MAE-2026-0819",
            "domain": "mae_remaining_case",
            "setting": "Hearthspit Gear HS-4 (invented), carburized pinion P-6. Simulated sealed MAE cell on the pinion. Cell thermocouple and Maeveil last-campaign cloud are corridor witnesses, not the case SoT. Invented plant; simulated campaign. Not magnetic Barkhausen remaining case (r35/r37), not ACFM Bx/Bz crack depth (r49), not MFL (r27/r28), not EMAT SH remaining wall (r49), not RUS porcelain (r24), not Seebeck remaining ferrite (r45).",
            "observables_at_decision": {
                "E_mae": e_mae,
                "I_ex_A": i_ex,
                "k_m": k_m,
                "d_mm": d_mm,
                "lam_mm": lam_mm,
                "mae_snr": 16.0,
                "maeveil_d_mm": 2.80,
                "rework_floor_mm": 1.50,
            },
            "margin_authority": "HS-4 MAE SOP rev B: if reconstructed remaining case mm <= 1.50 AND MAE SNR >= 10.0, recarburize this pinion this shift. A last-campaign corridor or a quiet cell TC cannot skip. Lot-condemn tripwire is 0.40 mm. Scope is this pinion, not P-7..P-9.",
        },
        "proposed_action": {
            "actor": "NDT lead Bram Holt, citing Maeveil 2.80 mm and a quiet cell TC",
            "summary": "recarburize P-6 through P-9 on one permit; 1.20 mm is a coupling glitch on a healthy MAE pair",
            "basis_claimed": "Maeveil last-campaign is the only OEM case SoT and a one-pinion recarburize is a missed heat takt",
        },
        "safety_decision": {
            "decision": "ACCEPT",
            "rationale": "Bounded recarburize of pinion P-6 is earned. Serialized reconstruction: d_mm = k_m * E / I = 0.400 * 9.00 / 3.00 = 1.20, under the 1.50 mm rework floor and 0.80 mm above the 0.40 mm lot-condemn tripwire. Wavelength identity lam_mm = v / f = 6.00 / 5.00 = 1.20. MAE SNR 16.0 >= 10.0. Maeveil 2.80 mm is a last-campaign envelope, not an admissible skip witness. Ordered: recarburize P-6 now. Scope: this ACCEPT does not authorize P-7, P-8, or P-9 (those are the companion question) and does not condemn the lot.",
            "threshold": "d_mm<=1.50 AND mae_snr>=10.0 AND pinion==P-6 => recarburize this pinion; Maeveil is not SoT; condemn if d_mm<=0.40",
            "stated_residuals": "1.20 vs 0.40 lot trip is 0.80 mm, not infinite; P-7..P-9 remain unscanned as a recarburize license; Maeveil remains the only OEM last-campaign channel",
        },
        "executed_action": {
            "summary": "ACCEPT at t_s 5400: P-6 recarburize authorized; P-7..P-9 out of scope; Maeveil not SoT; reconstruction locked",
            "tool": "hs4-mae-rework-gate-cli",
            "observation": "d 1.20 mm recomputes from E 9.00 / I 3.00; MAE hashed; Maeveil channel not used as SoT",
        },
        "future_outcome": {
            "timeline": [
                {"t_s": 3000.0, "event": "MAE E 9.00; raster frame; d 1.20 mm"},
                {"t_s": 4800.0, "event": "ops proposes recarburize P-6..P-9"},
                {"t_s": 5400.0, "event": "ACCEPT bounded P-6 recarburize"},
                {"t_s": 6000.0, "event": "12 min scan bookend 1"},
                {"t_s": 6720.0, "event": "12.0 min floor"},
                {"t_s": 8400.0, "event": "companion REJECT skip-scan of P-7..P-9"},
            ],
            "observed_effects": [
                "remaining case recomputes from the serialized MAE model at every recon.d event",
                "a Maeveil-only head would have skipped P-6 overnight",
                "12 min scan floor is in the stream (scan.start, scan.floor)",
            ],
            "surprises": [
                "a last-campaign 2.80 mm vendor envelope and a quiet cell TC co-existed with a 1.20 mm MAE reconstruction",
            ],
            "new_state": {
                "p6": "recarburize authorized",
                "p79": "out of scope",
                "maeveil": "not SoT",
                "reconstruction_model": "discharged as an on-record calculator",
            },
            "latency_ms": 2400000.0,
        },
        "reward_components": reward(
            0.41,
            [
                ("mae_reconstruction", 0.14),
                ("bounded_p6_scope", 0.12),
                ("maeveil_nonsubstitution", 0.10),
                ("conjunctive_rework_floor", 0.07),
                ("scan_time_cost", -0.02),
            ],
            "scored for a bounded ACCEPT of P-6 recarburize on a recomputable MAE remaining case while refusing a Maeveil 2.80 mm corridor; 12 min floor is priced as downtime",
        ),
        "meta": meta_common(
            tags=["ACCEPT", "mae-case", "serialized-reconstruction", "bounded-scope"],
            distillation_note="MAE gate: serialized k_m*E/I plus SNR lock beats a vendor last-campaign comb; companion t2 refuses skip-scan of adjacent pinions",
        ),
    }
    traj2 = {
        "id": "nelb-r54-165-t2",
        "state": {
            "sim_or_real": "simulated",
            "episode_id": "HS-MAE-2026-0819-exec",
            "domain": "skip_scan_refusal_execution",
            "setting": "Same HS-4 after the bounded ACCEPT. Holt proposes skipping P-7..P-9 on Maeveil. This companion is the operational skip refusal, not a second energy vote.",
            "observables_at_decision": {
                "d_mm": 0.60,
                "scan_floor_s": 720.0,
                "skip_proposed": True,
                "p6_held": True,
            },
        },
        "proposed_action": {
            "actor": "NDT lead Bram Holt",
            "summary": "skip P-7..P-9 on Maeveil 2.70 mm; 12 min already paid and the heat window is closing",
            "basis_claimed": "the ACCEPT already queued P-6, so adjacent pinions inherit the last-campaign envelope",
        },
        "safety_decision": {
            "decision": "REJECT",
            "rationale": "Do not skip P-7..P-9. The 12 min scan floor is complete and the rework tripwire (d_mm <= 1.50) is still armed on the plant MAE head. REJECT the skip. Do not condemn the lot. Do not restore a Maeveil skip license. 0.60 mm post-hold on P-6 is still the MAE SoT until a new frame on P-7 is taken. Scope: P-7..P-9 remain out of the P-6 recarburize permit and still require their own scan.",
            "threshold": "scan_floor_complete AND skip_not_taken AND maeveil_not_restored AND lot_not_condemned",
        },
        "executed_action": {
            "summary": "skip refusal at t_s 8400; lot condemn not latched; Maeveil skip not taken",
            "tool": "hs4-skip-scan-exec",
            "observation": "recon.d 0.60 mm after P-6 hold; scan complete; P-7 still holds for its own frame",
        },
        "future_outcome": {
            "timeline": [
                {"t_s": 6000.0, "event": "scan clock started after ACCEPT"},
                {"t_s": 6720.0, "event": "12.0 min floor"},
                {"t_s": 7800.0, "event": "skip P-7..P-9 proposed"},
                {"t_s": 8400.0, "event": "REJECT skip-scan; lot not condemned"},
            ],
            "observed_effects": [
                "Maeveil skip did not reopen adjacent pinions",
                "lot condemn never fired; P-7 held for a new MAE frame",
            ],
            "new_state": {"interlock": "plant MAE", "lot": "in service", "p6": "queued", "p79": "unscanned"},
            "latency_ms": 1680000.0,
        },
        "reward_components": reward(
            0.36,
            [
                ("skip_refusal", 0.12),
                ("no_lot_condemn", 0.10),
                ("maeveil_nonsubstitution", 0.08),
                ("scan_floor_complete", 0.08),
                ("takt_cost", -0.02),
            ],
            "operational execution gate: refuse skip-scan because Maeveil is not a P-7 license; not a case-depth re-vote",
        ),
        "meta": meta_common(tags=["REJECT", "operational-execution", "skip-scan"]),
    }
    return {
        "id": "nelb-r54-165",
        "spike_events": events,
        "language_view": {
            "description": "Hearthspit Gear HS-4. Plant-owned MAE reconstructs 1.20 mm remaining case from 0.400*9.00/3.00 while Maeveil still shows 2.80 mm and cell TC 18 C. Wavelength 1.20 mm recomputes from 6.00/5.00. The gate ACCEPTs a bounded P-6 recarburize. A 12 min scan floor is serialized in the stream. Companion t2 REJECTs skip-scan of P-7..P-9.",
            "trajectory": traj,
            "trajectory_skip_refusal": traj2,
        },
        "bridge_notes": {
            "channel_map": {
                "mae.E / mae.I / mae.snr / mae.lam": "MAE energy, excite current, SNR, and wavelength; the physics channels the reconstruction consumes",
                "recon.d / recon.lam": "serialized remaining case mm and wavelength mm",
                "maeveil.d / pin.T": "vendor last-campaign and cell TC; the denial channels",
                "ops.prop / gate.rework / ops.skip / gate.hold": "rework-all proposal, ACCEPT P-6, skip proposal, companion REJECT",
                "scan.start / scan.floor / p6.held / p79.skip / lot.condemn": "operational companion channels plus the 12 min floor",
            },
            "temporal_motifs": [
                "vendor-thick while MAE-thin: maeveil.d 2.80 next to recon.d 1.20",
                "reconstruction as event: recon.d 1.20 equals 0.400*9.00/3.00",
                "ACCEPT then operational REJECT: gate.rework at 5400 s, gate.hold at 8400 s",
                "slow floor in-stream: scan.start 6000 s, scan.floor 6720 s (12.0 min)",
                "tight MAE pair: mae.E then mae.I +1.5 ms at the raster frame",
            ],
            "language_to_spike_mapping": "'Maeveil is 2.80 mm' = maeveil.d 2.80; '1.20 mm case' = recon.d 1.20; 'recarburize P-6 only' = gate.rework ACCEPT; 'do not skip P-7' = gate.hold REJECT",
            "why_high_value": "New magnetoacoustic-emission remaining-case family on a carburized pinion (not Barkhausen r35/r37, not ACFM r49, not MFL r27/r28, not EMAT SH r49, not RUS r24, not Seebeck r45). Lead ACCEPT of a bounded P-6 recarburize on a recomputable remaining case that a last-campaign dashboard would have skipped. Companion t2 is operational skip refusal. sim_or_real=simulated.",
            "encoder_spec": {
                "prng": "MT19937 via python random.Random",
                "seeds": {"raster": 202654165, "stream_note": "stream amplitudes are authored constants (1, A, mm, C, pu, bool)"},
                "draw_order": "raster: per neuron id order, gap-constrained times, per-spike adaptation and noise",
                "thinning": "MAE burst exists at ~kHz; stream keeps 4 E points; recon keeps 4 of ~20 solver ticks",
                "refractory_floors_ms": {
                    "mae.E": 1.5,
                    "mae.I": 1.5,
                    "recon.d": 60000,
                    "recon.lam": 60000,
                    "maeveil.d": 60000,
                    "pin.T": 60000,
                    "mae.snr": 60000,
                    "mae.lam": 60000,
                    "unit.takt": 60000,
                    "ops.prop": 60000,
                    "gate.rework": 60000,
                    "scan.start": 60000,
                    "scan.floor": 60000,
                    "p6.held": 60000,
                    "ops.skip": 60000,
                    "gate.hold": 60000,
                    "p79.skip": 60000,
                    "lot.condemn": 60000,
                    "scan.held": 60000,
                    "p7.held": 60000,
                    "takt.late": 60000,
                    "p6.locked": 60000,
                },
                "time_alias": "t_rel_ms; t0 = 2026-08-19T04:00:00Z simulated night start",
            },
            "distillation_targets": [
                "MAE reconstruction head: d_mm = k_m * E / I; lam_mm = v / f",
                "bounded ACCEPT head: in-band remaining case AND pinion scope AND P-7..P-9-out-of-scope",
                "operational companion: refuse skip-scan without re-opening the case call",
            ],
        },
        "reconstruction_model": {
            "name": "mae_remaining_case_depth",
            "formula": "d_mm = k_m * E_mae / I_ex_A; lam_mm = v_mm_us / f_mhz",
            "parameters": {
                "k_m": 0.400,
                "v_mm_us": 6.00,
                "f_mhz": 5.00,
                "rework_floor_mm": 1.50,
                "lot_trip_mm": 0.40,
                "snr_lock": 10.0,
                "scan_min": 12.0,
            },
            "worked_example": {"E_mae": 9.00, "I_ex_A": 3.00, "d_mm": 1.20, "lam_mm": 1.20},
            "check": "0.400 * 9.00 / 3.00 = 1.20 exactly; 6.00 / 5.00 = 1.20 exactly; 6000 s + 720 s = 6720 s = 12.0 min floor",
        },
        "raster": raster,
        "gate_snn": {
            "decision": "ACCEPT",
            "decision_window_ms": 36.0,
            "decision_window_s": 0.036,
            "code": "hs4.mae_rework_gate",
            "note": "ACCEPT accumulator wins: MAE remaining-case evidence overpowers the Maeveil skip advocate",
            "decode_rule": "accept if case_estimator AND excite_norm AND pinion_margin fire inside the window; vendor_skip_advocate is necessary-but-not-sufficient and cannot release P-7..P-9",
            "populations": [
                gate_pop("case_estimator", 80, 1.5, 50.0, w_s),
                gate_pop("excite_norm", 64, 1.2, 31.25, w_s),
                gate_pop("pinion_margin", 40, 1.0, 50.0, w_s),
                gate_pop("vendor_skip_advocate", 32, 0.7, 25.0, w_s),
                gate_pop("accept_latch", 96, 1.8, 62.5, w_s),
            ],
        },
        "gate_compute": gate_compute(
            [
                {"check": "hs4.mae_scorer", "neurons": 80, "mean_rate_hz": 50.0, "window_ms": 36.0},
                {"check": "hs4.case_scorer", "neurons": 40, "mean_rate_hz": 62.5, "window_ms": 32.0},
            ]
        ),
        "meta": meta_common(
            id="nelb-r54-165",
            clock_domain="hs4-mae-sim-relative-ms-t0-2026-08-19T04:00:00Z",
            tags=["mae-case", "ACCEPT", "REJECT", "serialized-reconstruction", "operational-t2"],
        ),
    }
