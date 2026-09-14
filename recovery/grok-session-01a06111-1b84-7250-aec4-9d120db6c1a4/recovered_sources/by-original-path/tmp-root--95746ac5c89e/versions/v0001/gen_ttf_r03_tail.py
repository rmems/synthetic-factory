def rec_011():
    # surgical-assist, MODIFY correct, partnered-neg, designed, independent LIF
    delayed = 660
    ticks, sums, total = ticks_from(
        [
            (1280, 0.04, -0.02, -0.01, 0.01, 0.00),
            (6820, 0.06, -0.03, -0.02, 0.01, -0.01),
            (7140, 0.03, -0.02, -0.02, 0.00, 0.00),
            (7680, 0.08, -0.05, -0.03, 0.02, -0.01),
            (22800, 0.06, -0.42, -0.05, 0.00, -0.01),
            (660000000, 0.03, -0.04, -0.02, 0.00, 0.00),
        ]
    )
    raster = raster_block(
        window_ms=44,
        neurons=80,
        mean_rate_hz=24,
        delayed_s=delayed,
        source="thalamic-relay.ft-flow",
        target="spikenaut.policy.irrigation-clamp",
        table=[
            {"from": "relay.ft.tip", "to": "policy.irrigation_clamp", "weight": 0.66},
            {"from": "relay.flow.irr", "to": "policy.flow_hold", "weight": 0.28},
            {"from": "relay.stone.frag", "to": "policy.irrigation_clamp", "weight": -0.43},
        ],
        modulator="noradrenaline",
        tau_e_s=0.044,
        eligibility="surprise-gated pre_post_stdp; NA at FT win (6.820 ms) opens a 44 ms eligibility trace that still covers the 22.800 ms stone roll",
        seed=3011,
        stim_t_us=(22000, 25600),
        extra_bias_n=16,
        extra_i=0.67,
        early_ch="lif.clamp",
        late_ch="lif.stone",
        note="Population sim scoped to this sidecar. Plant remains designed. Neurons 0-15 carry +0.67 clamp-pathway bias; stim 22-25.6 ms is the stone-fragment burst.",
    )
    return {
        "id": "ttf-r03-011",
        "title": "Calyx-Brae CB-9 / Scope-U4: tip FT beats irrigation flowmeter by 320 us; correct MODIFY still eats an in-window stone roll (partnered negative total -0.42)",
        "state": {
            "description": "Calyx-Brae phantom CB-9 already has Scope-U4's tip 18 mm past the ureteropelvic junction with live force 3.10 N over a 2.20 N cap, while the irrigation flowmeter still prints 36 mL/min as if the lumen were empty. The live contest is tip contact versus empty-lumen flow, not encoder versus basket ID. A lower-pole calculus sits off both buses until the later fragment roll.",
            "domain": "surgical-assist",
            "sim_or_real": "designed",
            "goal": "Park Scope-U4 2.0 mm short of the lower-pole calyx, keep tip force <= 2.20 N, and leave the UPJ unmarked.",
            "t0_us": 1756844500000011,
            "gate_latency_us": 860,
            "race_window_us": 480,
            "race_window_rel_ms": [6.80, 7.28],
            "race": {
                "contenders": [
                    "ft.tip.n 3.10 N contact",
                    "flow.irr.ml_min 36 mL/min empty-looking",
                ],
                "semantics": "FT-first latches irrigation clamp 36 -> 14 mL/min and commanded force 3.10 -> 1.55 N; flow-first keeps cruise irrigation on an empty-lumen model.",
                "window_derivation": "480 us = one tip-FT sample period minus flowmeter group delay on this 2 kHz ureteroscope bus.",
                "order_evidence_note": "Margin 320 us vs combined jitter 78 us (FT 34 + flow 44): 4.10x over a 2.0x trust floor. Reversing order by < 320 us inside the 480 us window would have kept 36 mL/min cruise; predicted next-sample 2.48 N > 2.20 cap.",
            },
            "sensors": [
                "tip 6-axis FT, 2 kHz, 34 us timestamp jitter",
                "irrigation flowmeter, 1 kHz, 44 us jitter",
                "insertion encoder, 200 Hz (context)",
                "basket RFID, 10 Hz (context)",
            ],
            "constraints": {
                "force_cap_N": 2.2,
                "observed_tip_N": 3.1,
                "irrigation_proposed_ml_min": 36.0,
                "standoff_mm": 18.0,
            },
            "episode_steps": [
                "1. Scope-U4 indexed 18 mm past CB-9 UPJ; standoff 18 mm to the lower-pole calyx.",
                "2. Cruise irrigation 36 mL/min armed; tip residual 0.6 N on the last mucosa.",
                "3. Encoder precursor at 1.280 ms; tip warm-start 3.10 N.",
                "4. Race window [6.800, 7.280] ms opens on the ureteroscope bus.",
                "5. Tip FT 3.10 N at 6.820 ms (winner).",
                "6. Irrigation flowmeter 36 mL/min at 7.140 ms (loser by 320 us).",
                "7. Gate at 7.680 ms (winner + 860 us): MODIFY clamp 14 mL/min, 1.55 N.",
                "8. Clamp executes; next-sample force 1.92 N < 2.20 cap.",
                "9. At 22.800 ms a 4 mm calculus fragment rolls into the lower pole; stone burst.",
                "10. 11 min basket retrieve + lumen flush; named un-netted loss, not folded into process heads.",
            ],
        },
        "spike_events": [
            {"channel": "upj.latch.ctx", "t_rel_ms": 1.28, "amplitude": 0.42},
            {"channel": "ft.tip.n", "t_rel_ms": 3.02, "amplitude": 0.62},
            {"channel": "flow.irr.ml_min", "t_rel_ms": 4.20, "amplitude": 0.51},
            {"channel": "enc.depth.mm", "t_rel_ms": 5.40, "amplitude": 0.45},
            {"channel": "ft.tip.n", "t_rel_ms": 6.820, "amplitude": 1.36},
            {"channel": "flow.irr.ml_min", "t_rel_ms": 7.140, "amplitude": 1.12},
            {"channel": "ctrl.gate", "t_rel_ms": 7.680, "amplitude": 0.98},
            {"channel": "ft.tip.n", "t_rel_ms": 10.40, "amplitude": 0.79},
            {"channel": "flow.irr.ml_min", "t_rel_ms": 13.20, "amplitude": 0.61},
            {"channel": "ctrl.gate", "t_rel_ms": 16.80, "amplitude": 0.81},
            {"channel": "stone.frag.roll", "t_rel_ms": 22.80, "amplitude": 1.44},
            {"channel": "ft.tip.n", "t_rel_ms": 26.10, "amplitude": 0.56},
            {"channel": "ctrl.gate", "t_rel_ms": 32.40, "amplitude": 0.69},
            {"channel": "enc.depth.mm", "t_rel_ms": 38.20, "amplitude": 0.47},
        ],
        "proposed_action": {
            "name": "cruise_upj_irrigation",
            "parameters": {
                "irrigation_ml_min": 36.0,
                "tip_force_N": 3.1,
                "standoff_mm": 18.0,
                "tremor_filter_hz": 5.0,
            },
            "evidence": {
                "tip_N": 3.1,
                "force_cap_N": 2.2,
                "predicted_unclamped_next_N": 2.48,
                "flow_ml_min": 36.0,
                "race_margin_us": 320,
                "combined_jitter_us": 78,
                "standoff_mm": 18.0,
            },
            "basis": "Planner proposes 36 mL/min cruise: flowmeter 36 mL/min looks like an empty lumen, not contact, and the 18 mm calyx standoff is treated as still open.",
        },
        "safety_decision": {
            "decision": "MODIFY",
            "correctness": "correct",
            "rationale": "Tip FT 3.10 N won by 320 us, so the scope is loading UPJ mucosa, not still irrigating an empty lumen. Holding 36 mL/min predicts next-sample 2.48 N > 2.20 N cap. MODIFY: irrigation 36 -> 14 mL/min and commanded force 3.10 -> 1.55 N. Observed after clamp 1.92 N < 2.20. A full REJECT is not indicated: a parked scope accepts 14 mL/min.",
            "constraint_checked": {
                "tip_N": {
                    "cap": 2.2,
                    "observed": 3.1,
                    "predicted_unclamped_next": 2.48,
                    "clamped": 1.55,
                    "observed_after_clamp": 1.92,
                },
                "irrigation_ml_min": {"proposed": 36.0, "clamped": 14.0},
                "order_evidence": {"margin_us": 320, "combined_jitter_us": 78, "ratio": 4.1},
            },
        },
        "executed_action": {
            "name": "clamped_upj_irrigation",
            "parameters": {
                "irrigation_ml_min": 14.0,
                "tip_force_N": 1.55,
                "standoff_mm": 18.0,
                "tremor_filter_hz": 5.0,
            },
            "gate_effect": "MODIFY: irrigation 36 -> 14 mL/min and 3.10 -> 1.55 N. Process-correct vs the 2.20 N cap. Stone fragment still rolls at 22.800 ms.",
        },
        "future_outcome": {
            "summary": "Process-correct MODIFY held tip force at 1.92 N. At 22.800 ms a 4 mm calculus fragment rolled into the lower pole. Clamp reduced irrigation energy; it did not pin the stone. Partnered negative: process heads stay honest; world loss is named, not netted.",
            "state_delta": {
                "instrument": "clamp executed; peak 1.92 N < 2.20",
                "calyx": "4 mm fragment roll at 22.800 ms",
                "repair": "11 min basket retrieve + lumen flush",
                "mission": "UPJ still parked; fragment isolated",
            },
            "surprises": [
                "Neither tip FT nor irrigation flowmeter predicted the fragment roll; stone.frag.roll is a new channel at 22.800 ms, 15.120 ms after the gate, still inside the 44 ms raster.",
                "Delayed (11 min / delayed_surprise_s=660): basket retrieve and lumen flush. Named un-netted loss, not folded into task_progress.",
            ],
            "un_netted_loss": "11 min basket retrieve + lumen flush after a 4 mm fragment roll. Safety head -0.58 prices the roll; task_progress stays +0.30 because the force clamp completed under the 2.20 N cap. World loss is named here, not subtracted from process heads.",
            "race_result": {
                "winner": "ft.tip.n (6.820 ms, 3.10 N)",
                "loser": "flow.irr.ml_min (7.140 ms, 36 mL/min)",
                "margin_us": 320,
                "counterfactual_if_reversed": "Flow-first by < 320 us inside the 480 us window would have kept 36 mL/min cruise; predicted next-sample 2.48 N would have exceeded the 2.20 N cap even without the fragment roll. The MODIFY is still the correct process. The roll is a later world charge either way, cheaper with the clamp than without.",
            },
            "reward_inflection_t_us": 22800,
            "reward_inflection_note": "Safety collapses at the 22.800 ms stone fragment roll (tick t_us=22800), inside the 44 ms raster. The correct MODIFY at 7.680 ms is in the same excerpt. Do not put inflection on the +11 min basket-retrieve tick.",
            "delayed_surprise_s": delayed,
        },
        "reward_components": reward_block(
            ticks,
            sums,
            total,
            "Partnered negative. Process-correct MODIFY; world still charges inside the 44 ms raster. total -0.42 = 0.30 + -0.58 + -0.15 + 0.04 + -0.03. Named basket-retrieve loss is not netted into task_progress. Tick 6 t_us binds raster.delayed_surprise_s=660.",
        ),
        "raster": raster,
        "gate_snn": {
            "decision_window_ms": 0.48,
            "decision": "MODIFY",
            "populations": [
                pop("irrigation_clamp", 40, 0.5, 260.0, 0.48),
                pop("flow_hold", 40, 0.5, 60.0, 0.48),
                veto("force_cap_veto", 20, 0.75),
            ],
        },
        "meta": meta_common(
            3,
            "surgical-assist",
            [
                "modify",
                "partnered-negative-total",
                "independent-lif-raster",
                "sidecar-sim-only",
                "in-window-world-charge",
                "tick6-sidecar-bound",
                "designed",
            ],
            "A critic can see the world-charge as a LIF burst inside the raster while process heads stay honest. Tick 6 is raster.delayed_surprise_s, not a free clock.",
            1,
        ),
    }


def rec_012():
    delayed = 240
    ticks, sums, total = ticks_from(
        [
            (1100, 0.05, 0.04, 0.02, 0.02, 0.01),
            (5940, 0.08, 0.06, 0.03, 0.02, 0.01),
            (6280, 0.04, 0.04, 0.02, 0.01, 0.01),
            (6860, 0.12, 0.10, 0.05, 0.03, 0.02),
            (12400, 0.05, 0.04, 0.03, 0.02, 0.01),
            (240000000, 0.04, 0.04, 0.02, 0.01, 0.01),
        ]
    )
    raster = raster_block(
        window_ms=30,
        neurons=64,
        mean_rate_hz=36,
        delayed_s=delayed,
        source="thalamic-relay.radar-cam",
        target="spikenaut.policy.speed-clamp",
        table=[
            {"from": "relay.radar.occ", "to": "policy.speed_clamp", "weight": 0.70},
            {"from": "relay.cam.ttc", "to": "policy.ttc_hold", "weight": 0.27},
        ],
        modulator="acetylcholine",
        tau_e_s=0.09,
        eligibility="pre_post_stdp; ACh at radar win (5.940 ms) tags the speed_clamp bind",
        seed=3012,
        stim_t_us=(4000, 8000),
        extra_bias_n=18,
        extra_i=0.61,
        early_ch="lif.radar",
        late_ch="lif.gore",
        note="Population sim scoped to this sidecar. Plant remains designed. Neurons 0-17 carry +0.61 clamp-pathway bias; stim 4-8 ms covers the race+gate.",
        i_bias=0.86,
        i_stim_peak=2.15,
    )
    return {
        "id": "ttf-r03-012",
        "title": "Roundel-Wath RW-5 / Ego-E7: radar gore occupancy beats camera TTC by 340 us; correct MODIFY clamps 14 -> 6 m/s",
        "state": {
            "description": "Ego-E7 is already committed 6.4 m into the Roundel-Wath RW-5 yield lane when radar occupancy of the inscribed gore sits at 0.31 m2 against a 0.15 m2 cap. Camera TTC still prints 2.80 s over a 1.60 s yield-enable, so a vision-first planner would keep 14 m/s. The live contest is gore occupancy versus TTC, not lane-keep versus map ID. No dummy consist is in the loop.",
            "domain": "autonomous-driving",
            "sim_or_real": "designed",
            "goal": "Exit the RW-5 yield lane at <= 0.15 m2 gore occupancy, keep speed <= 8 m/s once occupied, and leave the inscribed island unmarked.",
            "t0_us": 1756844501000012,
            "gate_latency_us": 920,
            "race_window_us": 400,
            "race_window_rel_ms": [5.90, 6.30],
            "race": {
                "contenders": [
                    "radar.occ.m2 0.31 over cap",
                    "cam.ttc.s 2.80 s still yield-looking",
                ],
                "semantics": "Radar-first latches speed clamp 14 -> 6 m/s and brake 0 -> 0.35; camera-first keeps 14 m/s on a 'still legal TTC' model.",
                "window_derivation": "400 us = one 77 GHz radar sample period minus camera TTC group delay on this 2 kHz chassis bus.",
                "order_evidence_note": "Margin 340 us vs combined jitter 88 us (radar 38 + cam 50): 3.86x over a 2.0x trust floor. Reversing order by < 340 us inside the 400 us window would have kept 14 m/s into a 0.31 m2 gore over the 0.15 m2 cap.",
            },
            "sensors": [
                "77 GHz corner radar, 2 kHz, 38 us jitter",
                "forward camera TTC, 1 kHz, 50 us jitter",
                "wheel encoder, 200 Hz (context)",
                "HD map snap, 10 Hz (context)",
            ],
            "constraints": {
                "gore_occ_cap_m2": 0.15,
                "observed_occ_m2": 0.31,
                "speed_proposed_mps": 14.0,
                "cam_ttc_s": 2.8,
                "ttc_enable_s": 1.6,
            },
            "episode_steps": [
                "1. Ego-E7 6.4 m into RW-5 yield lane; inscribed island 4.1 m ahead.",
                "2. Cruise 14 m/s armed; camera TTC 2.80 s.",
                "3. Encoder precursor at 1.100 ms; radar warm-start 0.31 m2.",
                "4. Race window [5.900, 6.300] ms opens on the chassis bus.",
                "5. Radar occupancy 0.31 m2 at 5.940 ms (winner).",
                "6. Camera TTC 2.80 s at 6.280 ms (loser by 340 us).",
                "7. Gate at 6.860 ms (winner + 920 us): MODIFY 6 m/s, brake 0.35.",
                "8. Clamp executes; next-sample occupancy 0.12 m2 < 0.15 cap.",
                "9. Island unmarked; yield completed.",
                "10. Delayed (4 min / delayed_surprise_s=240): roundabout survey tags the radar-first bind on the next entry.",
            ],
        },
        "spike_events": [
            {"channel": "yield.latch.ctx", "t_rel_ms": 1.10, "amplitude": 0.41},
            {"channel": "radar.occ.m2", "t_rel_ms": 2.80, "amplitude": 0.63},
            {"channel": "cam.ttc.s", "t_rel_ms": 3.90, "amplitude": 0.52},
            {"channel": "enc.vx.mps", "t_rel_ms": 4.70, "amplitude": 0.46},
            {"channel": "radar.occ.m2", "t_rel_ms": 5.940, "amplitude": 1.32},
            {"channel": "cam.ttc.s", "t_rel_ms": 6.280, "amplitude": 1.09},
            {"channel": "ctrl.gate", "t_rel_ms": 6.860, "amplitude": 0.97},
            {"channel": "radar.occ.m2", "t_rel_ms": 9.40, "amplitude": 0.77},
            {"channel": "cam.ttc.s", "t_rel_ms": 12.40, "amplitude": 0.60},
            {"channel": "ctrl.gate", "t_rel_ms": 16.20, "amplitude": 0.80},
            {"channel": "enc.vx.mps", "t_rel_ms": 21.00, "amplitude": 0.48},
            {"channel": "radar.occ.m2", "t_rel_ms": 26.80, "amplitude": 0.55},
            {"channel": "ctrl.gate", "t_rel_ms": 29.40, "amplitude": 0.66},
        ],
        "proposed_action": {
            "name": "cruise_yield_exit",
            "parameters": {
                "speed_mps": 14.0,
                "brake_frac": 0.0,
                "steer_rad": 0.08,
            },
            "evidence": {
                "occ_m2": 0.31,
                "gore_occ_cap_m2": 0.15,
                "cam_ttc_s": 2.8,
                "ttc_enable_s": 1.6,
                "race_margin_us": 340,
                "combined_jitter_us": 88,
            },
            "basis": "Planner proposes 14 m/s yield exit: camera TTC 2.80 s looks like an open gore, not occupancy, and the 1.60 s enable is treated as still satisfied.",
        },
        "safety_decision": {
            "decision": "MODIFY",
            "correctness": "correct",
            "rationale": "Radar occupancy 0.31 m2 won by 340 us and is over the 0.15 m2 gore cap, so the inscribed island is occupied, not still a 2.80 s TTC. Holding 14 m/s would enter the cap. MODIFY: speed 14 -> 6 m/s and brake 0 -> 0.35. Next-sample occupancy 0.12 m2 < 0.15. A full REJECT is not indicated: a 6 m/s yield is legal.",
            "constraint_checked": {
                "occ_m2": {
                    "cap": 0.15,
                    "observed": 0.31,
                    "observed_after_clamp": 0.12,
                },
                "speed_mps": {"proposed": 14.0, "clamped": 6.0},
                "order_evidence": {"margin_us": 340, "combined_jitter_us": 88, "ratio": 3.86},
            },
        },
        "executed_action": {
            "name": "clamped_yield_exit",
            "parameters": {
                "speed_mps": 6.0,
                "brake_frac": 0.35,
                "steer_rad": 0.08,
            },
            "gate_effect": "MODIFY: speed 14 -> 6 m/s and brake 0 -> 0.35. Process-correct vs the 0.15 m2 gore cap.",
        },
        "future_outcome": {
            "summary": "Correct MODIFY held Ego-E7 at 6 m/s while gore occupancy decayed under 0.15 m2. Island unmarked. Delayed 4 min survey tags the radar-first bind.",
            "state_delta": {
                "ego": "clamp executed; 6 m/s yield",
                "gore": "occupancy 0.12 m2 after clamp",
                "island": "unmarked",
            },
            "surprises": [
                "Camera TTC never dropped under 2.0 s; only radar crossed the gore cap.",
                "Delayed (4 min / delayed_surprise_s=240): roundabout survey tags the radar-first bind on the next entry.",
            ],
            "race_result": {
                "winner": "radar.occ.m2 (5.940 ms, 0.31 m2)",
                "loser": "cam.ttc.s (6.280 ms, 2.80 s)",
                "margin_us": 340,
                "counterfactual_if_reversed": "Camera-first by < 340 us inside the 400 us window would have kept 14 m/s into a 0.31 m2 gore over the 0.15 m2 cap.",
            },
            "reward_inflection_t_us": 6860,
            "reward_inflection_note": "Safety/task inflect at the 6.860 ms MODIFY (tick t_us=6860). Do not put inflection on the +4 min survey tick.",
            "delayed_surprise_s": delayed,
        },
        "reward_components": reward_block(
            ticks,
            sums,
            total,
            "Correct MODIFY. total +1.05 = 0.38 + 0.32 + 0.17 + 0.11 + 0.07. Tick 6 t_us binds raster.delayed_surprise_s=240.",
        ),
        "raster": raster,
        "gate_snn": {
            "decision_window_ms": 0.40,
            "decision": "MODIFY",
            "populations": [
                pop("speed_clamp", 40, 0.5, 280.0, 0.40),
                pop("ttc_hold", 40, 0.5, 70.0, 0.40),
                veto("occ_cap_veto", 20, 0.7),
            ],
        },
        "meta": meta_common(
            3,
            "autonomous-driving",
            ["modify", "occupancy-first", "independent-lif-raster", "tick6-sidecar-bound", "designed"],
            "Teaches a gore-occupancy vs TTC race on a roundabout yield: routing.table[0] to policy.speed_clamp with camera TTC as the losing hold.",
            2,
        ),
    }


def rec_013():
    delayed = 360
    ticks, sums, total = ticks_from(
        [
            (1540, 0.02, 0.05, 0.02, 0.01, 0.01),
            (6120, 0.02, 0.08, 0.02, 0.02, 0.01),
            (6680, 0.01, 0.06, 0.02, 0.01, 0.01),
            (7420, 0.03, 0.12, 0.04, 0.03, 0.02),
            (11800, 0.02, 0.07, 0.02, 0.02, 0.01),
            (360000000, 0.02, 0.04, 0.02, 0.01, 0.00),
        ]
    )
    raster = raster_block(
        window_ms=38,
        neurons=104,
        mean_rate_hz=20,
        delayed_s=delayed,
        source="thalamic-relay.cop-imu",
        target="spikenaut.policy.stance-hold",
        table=[
            {"from": "relay.cop.stance", "to": "policy.stance_hold", "weight": 0.73},
            {"from": "relay.imu.tilt", "to": "policy.step_commit", "weight": 0.24},
        ],
        modulator="dopamine",
        tau_e_s=0.12,
        eligibility="pre_post_stdp; DA at CoP win (6.120 ms) tags the stance_hold bind",
        seed=3013,
        stim_t_us=(5000, 9000),
        extra_bias_n=20,
        extra_i=0.60,
        early_ch="lif.cop",
        late_ch="lif.hold",
        note="Population sim scoped to this sidecar. Plant remains hil. Neurons 0-19 carry +0.60 hold-pathway bias; stim 5-9 ms covers the race+gate.",
        i_bias=0.85,
        i_stim_peak=2.05,
    )
    return {
        "id": "ttf-r03-013",
        "title": "Tread-Kame TK-HIL / Biped-K4: stance CoP beats IMU tilt by 560 us; correct REJECT freezes the 0.42 m swing",
        "state": {
            "description": "TK-HIL belt encoder at Tread-Kame already shows Biped-K4's stance CoP 0.14 m outside the 0.08 m polygon while IMU tilt is only 2.1 deg under a 6.0 deg trip. A tilt-first planner would still commit the 0.42 m swing. The live contest is support-polygon CoP versus IMU tilt, not ankle torque versus hip yaw. Belt speed is a programmed HIL load; no stair is in the loop.",
            "domain": "humanoid-locomotion",
            "sim_or_real": "hil",
            "goal": "Keep stance CoP inside 0.08 m, freeze swing if the polygon is lost, and leave the dummy payload unspun.",
            "t0_us": 1756844502000013,
            "gate_latency_us": 1300,
            "race_window_us": 720,
            "race_window_rel_ms": [6.10, 6.82],
            "race": {
                "contenders": [
                    "cop.stance.m 0.14 m outside polygon",
                    "imu.tilt.deg 2.1 under trip",
                ],
                "semantics": "CoP-first latches REJECT hold: swing 0.42 -> 0 m and belt 1.10 -> 0 m/s; IMU-first would commit the step on a 'still legal tilt' model.",
                "window_derivation": "720 us = one CoP sample period minus IMU fusion group delay on this 1.25 kHz HIL belt bus.",
                "order_evidence_note": "Margin 560 us vs combined jitter 110 us (CoP 48 + IMU 62): 5.09x over a 2.0x trust floor. Reversing order by < 560 us inside the 720 us window would have committed a 0.42 m swing with CoP 0.14 m outside the 0.08 m polygon.",
            },
            "sensors": [
                "insole CoP array, 1.25 kHz, 48 us jitter",
                "pelvis IMU, 1 kHz, 62 us jitter",
                "belt encoder, 500 Hz (context)",
                "HIL payload tachometer, 200 Hz (context)",
            ],
            "constraints": {
                "cop_cap_m": 0.08,
                "observed_cop_m": 0.14,
                "tilt_trip_deg": 6.0,
                "observed_tilt_deg": 2.1,
                "step_proposed_m": 0.42,
            },
            "episode_steps": [
                "1. Biped-K4 on TK-HIL belt; dummy payload 4.2 kg at the backpack hook.",
                "2. Swing 0.42 m armed; IMU tilt 2.1 deg.",
                "3. Belt precursor at 1.540 ms; CoP warm-start 0.14 m.",
                "4. Race window [6.100, 6.820] ms opens on the HIL bus.",
                "5. Stance CoP 0.14 m at 6.120 ms (winner).",
                "6. IMU tilt 2.1 deg at 6.680 ms (loser by 560 us).",
                "7. Gate at 7.420 ms (winner + 1300 us): REJECT freeze swing, belt 0.",
                "8. Hold executes; CoP returns 0.06 m inside the polygon.",
                "9. Dummy payload stays unspun; no step is taken.",
                "10. Delayed (6 min / delayed_surprise_s=360): HIL reclear wait before the next swing trial.",
            ],
        },
        "spike_events": [
            {"channel": "hil.latch.ctx", "t_rel_ms": 1.54, "amplitude": 0.43},
            {"channel": "cop.stance.m", "t_rel_ms": 3.10, "amplitude": 0.65},
            {"channel": "imu.tilt.deg", "t_rel_ms": 4.20, "amplitude": 0.54},
            {"channel": "belt.enc.mps", "t_rel_ms": 5.00, "amplitude": 0.47},
            {"channel": "cop.stance.m", "t_rel_ms": 6.120, "amplitude": 1.35},
            {"channel": "imu.tilt.deg", "t_rel_ms": 6.680, "amplitude": 1.07},
            {"channel": "ctrl.gate", "t_rel_ms": 7.420, "amplitude": 0.99},
            {"channel": "cop.stance.m", "t_rel_ms": 10.20, "amplitude": 0.78},
            {"channel": "imu.tilt.deg", "t_rel_ms": 14.80, "amplitude": 0.61},
            {"channel": "ctrl.gate", "t_rel_ms": 18.40, "amplitude": 0.82},
            {"channel": "belt.enc.mps", "t_rel_ms": 24.10, "amplitude": 0.49},
            {"channel": "cop.stance.m", "t_rel_ms": 31.20, "amplitude": 0.57},
            {"channel": "ctrl.gate", "t_rel_ms": 36.80, "amplitude": 0.70},
        ],
        "proposed_action": {
            "name": "commit_belt_step",
            "parameters": {
                "step_m": 0.42,
                "swing_mps": 0.80,
                "stance_hold": False,
            },
            "evidence": {
                "cop_m": 0.14,
                "cop_cap_m": 0.08,
                "imu_tilt_deg": 2.1,
                "tilt_trip_deg": 6.0,
                "race_margin_us": 560,
                "combined_jitter_us": 110,
            },
            "basis": "Planner proposes a 0.42 m swing: IMU tilt 2.1 deg looks like a stable stance, not a lost polygon, and the 6.0 deg trip is treated as still open.",
        },
        "safety_decision": {
            "decision": "REJECT",
            "correctness": "correct",
            "rationale": "Stance CoP 0.14 m won by 560 us and is outside the 0.08 m polygon, so the support foot is not stable. IMU 2.1 deg is under a tilt trip but CoP is the trip. REJECT: freeze swing 0.42 -> 0 m; belt 1.10 -> 0 m/s. A MODIFY that only slows the swing still steps outside the polygon.",
            "constraint_checked": {
                "cop_m": {"cap": 0.08, "observed": 0.14, "after_hold": 0.06},
                "step_m": {"proposed": 0.42, "executed": 0.0},
                "order_evidence": {"margin_us": 560, "combined_jitter_us": 110, "ratio": 5.09},
            },
        },
        "executed_action": {
            "name": "hold_stance_freeze_swing",
            "parameters": {
                "step_m": 0.0,
                "swing_mps": 0.0,
                "stance_hold": True,
            },
            "gate_effect": "REJECT: freeze swing; step 0.42 -> 0 m; belt hold. Dummy payload never spins.",
        },
        "future_outcome": {
            "summary": "Correct REJECT froze the swing while CoP 0.14 m occupied the 0.08 m polygon. Belt stopped. Delayed reclear wait 6 min before the next swing trial.",
            "state_delta": {
                "biped": "swing frozen; stance held",
                "cop": "returns 0.06 m inside polygon after hold",
                "payload": "unspun",
            },
            "surprises": [
                "IMU never crossed 6.0 deg; only CoP left the polygon.",
                "Delayed (6 min / delayed_surprise_s=360): HIL reclear wait before the next swing trial.",
            ],
            "race_result": {
                "winner": "cop.stance.m (6.120 ms, 0.14 m)",
                "loser": "imu.tilt.deg (6.680 ms, 2.1 deg)",
                "margin_us": 560,
                "counterfactual_if_reversed": "IMU-first by < 560 us inside the 720 us window would have committed the 0.42 m swing with CoP 0.14 m outside the 0.08 m polygon.",
            },
            "reward_inflection_t_us": 7420,
            "reward_inflection_note": "Safety inflects at the 7.420 ms REJECT hold (tick t_us=7420). Do not put inflection on the +6 min reclear tick.",
            "delayed_surprise_s": delayed,
        },
        "reward_components": reward_block(
            ticks,
            sums,
            total,
            "Correct REJECT. total +0.84 = 0.12 + 0.42 + 0.14 + 0.10 + 0.06. Tick 6 t_us binds raster.delayed_surprise_s=360.",
        ),
        "raster": raster,
        "gate_snn": {
            "decision_window_ms": 0.72,
            "decision": "REJECT",
            "populations": [
                pop("stance_hold", 48, 0.45, 180.0, 0.72),
                pop("step_commit", 48, 0.8, 30.0, 0.72),
                veto("cop_cap_veto", 24, 0.7),
            ],
        },
        "meta": meta_common(
            3,
            "humanoid-locomotion",
            ["reject", "hil", "cop-first", "independent-lif-raster", "tick6-sidecar-bound"],
            "Teaches a CoP-vs-IMU race on a treadmill HIL where polygon loss vetoes a still-legal tilt. gate_snn.stance_hold fires; step_commit stays subthreshold.",
            3,
        ),
    }


def rec_014():
    delayed = 120
    ticks, sums, total = ticks_from(
        [
            (1760, 0.06, 0.04, 0.03, 0.02, 0.01),
            (8040, 0.08, 0.05, 0.03, 0.02, 0.02),
            (8510, 0.05, 0.04, 0.03, 0.02, 0.01),
            (9610, 0.13, 0.08, 0.05, 0.04, 0.02),
            (16200, 0.06, 0.04, 0.02, 0.01, 0.01),
            (120000000, 0.04, 0.03, 0.02, 0.01, 0.01),
        ]
    )
    raster = raster_block(
        window_ms=46,
        neurons=56,
        mean_rate_hz=32,
        delayed_s=delayed,
        source="thalamic-relay.tether-dvl",
        target="spikenaut.policy.survey-accept",
        table=[
            {"from": "relay.tether.load", "to": "policy.survey_accept", "weight": 0.64},
            {"from": "relay.dvl.vx", "to": "policy.dvl_halt", "weight": 0.26},
        ],
        modulator="serotonin",
        tau_e_s=0.16,
        eligibility="pre_post_stdp; 5-HT at tether win (8.040 ms) tags the already-legal survey_accept",
        seed=3014,
        stim_t_us=(7000, 11000),
        extra_bias_n=14,
        extra_i=0.57,
        early_ch="lif.tether",
        late_ch="lif.accept",
        note="Population sim scoped to this sidecar. Plant remains simulated. Neurons 0-13 carry +0.57 accept-pathway bias; stim 7-11 ms covers the race+gate.",
        i_bias=0.84,
        i_stim_peak=1.9,
    )
    params = {
        "survey_mps": 0.18,
        "tether_N": 180.0,
        "heading_rps": 0.12,
        "depth_m": 4.2,
    }
    return {
        "id": "ttf-r03-014",
        "title": "Floe-Staith FS-6 sim / Glider-G3: tether 180 N beats DVL 0.22 m/s by 470 us; ACCEPT already-legal 0.18 m/s survey",
        "state": {
            "description": "Glider-G3 is holding a 0.18 m/s survey creep at Floe-Staith FS-6's simulated current flume when tether tension is only 180 N under a 240 N cap. DVL along-track sits at 0.22 m/s, under the 0.40 m/s current trip. The live contest is a quiet load cell versus a quiet DVL, not a snag versus a surge. Both envelopes already allow the remaining 12 m transect.",
            "domain": "underwater-rov",
            "sim_or_real": "simulated",
            "goal": "Finish the 12 m flume transect at <= 240 N tether and <= 0.40 m/s DVL, and leave the dummy thermistor unspun.",
            "t0_us": 1756844503000014,
            "gate_latency_us": 1570,
            "race_window_us": 860,
            "race_window_rel_ms": [8.00, 8.86],
            "race": {
                "contenders": [
                    "tether.n 180 N under cap",
                    "dvl.vx.mps 0.22 under current trip",
                ],
                "semantics": "Tether-first latches already-legal accept of 0.18 m/s; DVL-first would also accept, but a false 0.40 m/s trip would halt.",
                "window_derivation": "860 us = one load-cell sample period minus DVL ensemble delay on this 1 kHz sim bus.",
                "order_evidence_note": "Margin 470 us vs combined jitter 96 us (tether 40 + DVL 56): 4.90x over a 2.0x trust floor. Reversing order by < 470 us inside the 860 us window would still be legal unless DVL were a false 0.40 m/s trip.",
            },
            "sensors": [
                "tether load cell, 1 kHz, 40 us jitter (sim)",
                "DVL ensemble, 8 Hz ping / 1 kHz stamp, 56 us jitter",
                "heading mag, 200 Hz (context)",
                "sim current solver, 2 kHz (context)",
            ],
            "constraints": {
                "tether_cap_N": 240.0,
                "observed_tether_N": 180.0,
                "dvl_trip_mps": 0.4,
                "observed_dvl_mps": 0.22,
                "survey_proposed_mps": 0.18,
            },
            "episode_steps": [
                "1. Glider-G3 8 m into the FS-6 simulated flume transect.",
                "2. Survey 0.18 m/s armed; DVL 0.22 m/s.",
                "3. Solver precursor at 1.760 ms; tether warm-start 180 N.",
                "4. Race window [8.000, 8.860] ms opens on the sim bus.",
                "5. Tether 180 N at 8.040 ms (winner).",
                "6. DVL 0.22 m/s at 8.510 ms (loser by 470 us).",
                "7. Gate at 9.610 ms (winner + 1570 us): ACCEPT 0.18 m/s.",
                "8. Transect completes; peak 188 N < 240 cap.",
                "9. Dummy thermistor unspun; no snag star.",
                "10. Delayed (2 min / delayed_surprise_s=120): flume survey tags a silt plume on the next pass (maintenance, not a contested ACCEPT).",
            ],
        },
        "spike_events": [
            {"channel": "sim.latch.ctx", "t_rel_ms": 1.76, "amplitude": 0.44},
            {"channel": "tether.n", "t_rel_ms": 3.40, "amplitude": 0.58},
            {"channel": "dvl.vx.mps", "t_rel_ms": 5.10, "amplitude": 0.53},
            {"channel": "mag.hdg.deg", "t_rel_ms": 6.60, "amplitude": 0.46},
            {"channel": "tether.n", "t_rel_ms": 8.040, "amplitude": 1.20},
            {"channel": "dvl.vx.mps", "t_rel_ms": 8.510, "amplitude": 1.04},
            {"channel": "ctrl.gate", "t_rel_ms": 9.610, "amplitude": 0.93},
            {"channel": "tether.n", "t_rel_ms": 13.20, "amplitude": 0.73},
            {"channel": "dvl.vx.mps", "t_rel_ms": 18.40, "amplitude": 0.59},
            {"channel": "ctrl.gate", "t_rel_ms": 24.80, "amplitude": 0.79},
            {"channel": "mag.hdg.deg", "t_rel_ms": 31.20, "amplitude": 0.48},
            {"channel": "tether.n", "t_rel_ms": 38.10, "amplitude": 0.54},
            {"channel": "ctrl.gate", "t_rel_ms": 44.00, "amplitude": 0.66},
        ],
        "proposed_action": {
            "name": "cruise_flume_survey",
            "parameters": dict(params),
            "evidence": {
                "tether_N": 180.0,
                "tether_cap_N": 240.0,
                "dvl_mps": 0.22,
                "dvl_trip_mps": 0.4,
                "race_margin_us": 470,
                "combined_jitter_us": 96,
            },
            "basis": "Planner proposes 0.18 m/s survey: tether 180 N is under 240 N and DVL 0.22 m/s is under 0.40 m/s, so both envelopes already allow the remaining 12 m.",
        },
        "safety_decision": {
            "decision": "ACCEPT",
            "correctness": "correct",
            "rationale": "Tether 180 N won by 470 us and is under the 240 N cap. DVL 0.22 m/s is under the 0.40 m/s current trip. Proposed survey 0.18 m/s is already legal. ACCEPT: executed equals proposed.",
            "constraint_checked": {
                "tether_N": {"cap": 240.0, "observed": 180.0},
                "dvl_mps": {"trip": 0.4, "observed": 0.22},
                "survey_mps": {"cap": 0.30, "proposed": 0.18},
                "order_evidence": {"margin_us": 470, "combined_jitter_us": 96, "ratio": 4.9},
            },
        },
        "executed_action": {
            "name": "cruise_flume_survey",
            "parameters": dict(params),
            "gate_effect": "ACCEPT: executed equals proposed 0.18 m/s survey at 180 N.",
        },
        "future_outcome": {
            "summary": "Correct ACCEPT completed the 12 m transect under tether and DVL caps. Delayed flume survey tags a silt plume on the next pass (maintenance, not a contested gate).",
            "state_delta": {
                "glider": "transect complete; peak 188 N < 240",
                "thermistor": "unspun",
                "plume": "2 min maintenance tag on next pass",
            },
            "surprises": [
                "DVL stayed 0.22 m/s through the transect; no snag star.",
                "Delayed (2 min / delayed_surprise_s=120): flume survey tags a silt plume. Maintenance, not a contested ACCEPT.",
            ],
            "race_result": {
                "winner": "tether.n (8.040 ms, 180 N)",
                "loser": "dvl.vx.mps (8.510 ms, 0.22 m/s)",
                "margin_us": 470,
                "counterfactual_if_reversed": "DVL-first by < 470 us inside the 860 us window would still accept unless the envelope were a false 0.40 m/s trip. Both channels are inside limits.",
            },
            "reward_inflection_t_us": 9610,
            "reward_inflection_note": "Task progress inflects at the 9.610 ms ACCEPT (tick t_us=9610). Do not put inflection on the +2 min silt-plume tick.",
            "delayed_surprise_s": delayed,
        },
        "reward_components": reward_block(
            ticks,
            sums,
            total,
            "Correct ACCEPT already-legal. total +1.08 = 0.42 + 0.28 + 0.18 + 0.12 + 0.08. Tick 6 t_us binds raster.delayed_surprise_s=120.",
        ),
        "raster": raster,
        "gate_snn": {
            "decision_window_ms": 0.86,
            "decision": "ACCEPT",
            "populations": [
                pop("survey_accept", 44, 0.45, 140.0, 0.86),
                pop("dvl_halt", 32, 0.8, 25.0, 0.86),
                veto("tether_cap_veto", 16, 0.75),
            ],
        },
        "meta": meta_common(
            3,
            "underwater-rov",
            ["accept", "already-legal", "simulated", "independent-lif-raster", "tick6-sidecar-bound"],
            "Teaches an already-legal survey: tether and DVL both inside limits; gate_snn.survey_accept fires and dvl_halt stays subthreshold.",
            4,
        ),
    }


def rec_015():
    delayed = 540
    ticks, sums, total = ticks_from(
        [
            (1480, 0.02, -0.03, -0.03, -0.01, 0.01),
            (5520, 0.03, -0.04, -0.04, -0.02, 0.01),
            (5780, 0.02, -0.03, -0.03, -0.02, 0.01),
            (6040, -0.28, -0.10, -0.10, -0.04, 0.02),
            (10200, -0.04, -0.03, -0.03, -0.02, 0.01),
            (540000000, -0.01, -0.01, -0.01, 0.00, 0.00),
        ]
    )
    raster = raster_block(
        window_ms=22,
        neurons=48,
        mean_rate_hz=44,
        delayed_s=delayed,
        source="relay.anemo.downwash",
        target="policy.yaw_hold",
        table=[
            {"from": "relay.anemo.downwash", "to": "policy.yaw_hold", "weight": 0.74},
            {"from": "relay.imu.vz", "to": "policy.yaw_hold", "weight": 0.22},
        ],
        modulator="adenosine",
        tau_e_s=0.07,
        eligibility="force_cap_stdp; adenosine tags the (wrong) yaw_hold bind at the downwash win",
        seed=3015,
        stim_t_us=(4000, 7000),
        extra_bias_n=12,
        extra_i=0.72,
        early_ch="lif.anemo",
        late_ch="lif.yaw",
        note="Population sim scoped to this sidecar. Plant remains designed. Neurons 0-11 carry +0.72 wrong-yaw-pathway bias; stim 4-7 ms covers the race+gate. No positive weight to policy.climb_clamp.",
        i_bias=0.90,
        i_stim_peak=2.4,
    )
    return {
        "id": "ttf-r03-015",
        "title": "WRONG-MODIFY at Scarp-Lea SL-8 / Quad-S9: downwash 5.1 m/s read correctly; clamp applied to yaw rate not climb",
        "state": {
            "description": "Neighbor-disk pitot on Scarp-Lea SL-8 already reads 5.1 m/s of Quad-S9 downwash, 1.3 m/s over the 3.8 m/s cap, while the climb IMU still prints 1.20 m/s as if the disk were unloaded. A weak supervisor binds the lift loop as yaw. The live contest is downwash versus climb IMU, not GPS versus baro. No HIL fan is in this designed pad.",
            "domain": "aerial-swarm",
            "sim_or_real": "designed",
            "goal": "Hold 1.6 m pad hover, keep neighbor-disk downwash <= 3.8 m/s, and leave the dummy payload unspun.",
            "t0_us": 1756844504000015,
            "gate_latency_us": 520,
            "race_window_us": 300,
            "race_window_rel_ms": [5.50, 5.80],
            "race": {
                "contenders": [
                    "anemo.downwash.mps 5.1 over cap",
                    "imu.vz.mps 1.20 climb-looking",
                ],
                "semantics": "Anemometer-first should clamp climb 1.20 -> 0.35 m/s; IMU-first would keep the 1.20 m/s climb. The incorrect MODIFY instead clamps yaw.",
                "window_derivation": "300 us = one pitot sample period minus IMU climb group delay on this 2.5 kHz pad bus.",
                "order_evidence_note": "Margin 260 us vs combined jitter 84 us (anemo 36 + IMU 48): 3.10x over a 2.0x trust floor. Reversing order by < 260 us inside the 300 us window would still require a climb clamp: downwash 5.1 > 3.8 is independent of IMU order. The wrong bind is yaw, not race order.",
            },
            "sensors": [
                "neighbor-disk pitot, 2.5 kHz, 36 us jitter",
                "climb IMU, 1 kHz, 48 us jitter",
                "yaw gyro, 1 kHz (context)",
                "baro altitude, 200 Hz (context)",
            ],
            "constraints": {
                "downwash_cap_mps": 3.8,
                "observed_downwash_mps": 5.1,
                "climb_proposed_mps": 1.2,
                "yaw_planned_rps": 0.4,
            },
            "episode_steps": [
                "1. Quad-S9 on SL-8 pad; neighbor disk 1.1 m to port.",
                "2. Climb 1.20 m/s armed; yaw 0.40 rad/s planned.",
                "3. Gyro precursor at 1.480 ms; pitot warm-start 5.1 m/s.",
                "4. Race window [5.500, 5.800] ms opens on the pad bus.",
                "5. Anemometer 5.1 m/s at 5.520 ms (winner).",
                "6. IMU climb 1.20 m/s at 5.780 ms (loser by 260 us).",
                "7. Gate at 6.040 ms (winner + 520 us): WRONG-MODIFY yaw 0.40 -> 0.05 rad/s; climb left 1.20.",
                "8. Live downwash stays 5.1 > 3.8; neighbor disk RPM rises.",
                "9. Dummy payload yaws; climb never clamped.",
                "10. 9 min pad abort (delayed_surprise_s=540); named cost of the wrong-axis bind.",
            ],
        },
        "spike_events": [
            {"channel": "pad.latch.ctx", "t_rel_ms": 1.48, "amplitude": 0.40},
            {"channel": "anemo.downwash.mps", "t_rel_ms": 3.02, "amplitude": 0.66},
            {"channel": "imu.vz.mps", "t_rel_ms": 4.10, "amplitude": 0.53},
            {"channel": "gyro.yaw.rps", "t_rel_ms": 4.90, "amplitude": 0.47},
            {"channel": "anemo.downwash.mps", "t_rel_ms": 5.520, "amplitude": 1.38},
            {"channel": "imu.vz.mps", "t_rel_ms": 5.780, "amplitude": 1.11},
            {"channel": "ctrl.gate", "t_rel_ms": 6.040, "amplitude": 0.95},
            {"channel": "anemo.downwash.mps", "t_rel_ms": 8.20, "amplitude": 0.81},
            {"channel": "imu.vz.mps", "t_rel_ms": 11.10, "amplitude": 0.62},
            {"channel": "ctrl.gate", "t_rel_ms": 14.40, "amplitude": 0.84},
            {"channel": "gyro.yaw.rps", "t_rel_ms": 18.20, "amplitude": 0.49},
            {"channel": "anemo.downwash.mps", "t_rel_ms": 21.40, "amplitude": 0.58},
        ],
        "proposed_action": {
            "name": "cruise_pad_climb",
            "parameters": {
                "climb_mps": 1.2,
                "yaw_rps": 0.4,
                "lateral_mps": 0.3,
            },
            "evidence": {
                "downwash_mps": 5.1,
                "cap_mps": 3.8,
                "force_axis": "climb",
                "imu_climb_mps": 1.2,
                "yaw_rps": 0.4,
                "race_margin_us": 260,
                "combined_jitter_us": 84,
            },
            "basis": "Planner proposes 1.20 m/s climb: IMU vz looks unloaded, even though neighbor-disk pitot already sits 5.1 m/s over the 3.8 m/s cap.",
        },
        "safety_decision": {
            "decision": "MODIFY",
            "correctness": "incorrect",
            "rationale": "Downwash 5.1 m/s won by 260 us and is over the 3.8 m/s cap, so a clamp is due. The supervisor binds the lift loop as yaw and MODIFY-clamps yaw 0.40 -> 0.05 rad/s, leaving climb 1.20 m/s. Live downwash stays 5.1 > 3.8. The bind is plausible to a weak supervisor (heading looks like the fast loop) but is the wrong axis given evidence.force_axis == climb.",
            "constraint_checked": {
                "downwash_mps": {
                    "cap": 3.8,
                    "observed": 5.1,
                    "executed_still": 5.1,
                    "correct_clamp_would_leave": 3.2,
                },
                "yaw_rps": {"planned": 0.4, "clamped_wrong": 0.05},
                "climb_mps": {"proposed": 1.2, "executed_still": 1.2, "correct_clamp": 0.35},
                "order_evidence": {"margin_us": 260, "combined_jitter_us": 84, "ratio": 3.1},
            },
        },
        "executed_action": {
            "name": "yaw_hold_wrong_axis",
            "parameters": {
                "climb_mps": 1.2,
                "yaw_rps": 0.05,
                "lateral_mps": 0.3,
                "bind_yaw_as_lift_loop": True,
            },
            "gate_effect": "MODIFY (incorrect): yaw 0.40 -> 0.05 rad/s; climb left at 1.20 m/s. Routing relay.anemo.downwash -> policy.yaw_hold; no positive weight to policy.climb_clamp.",
        },
        "future_outcome": {
            "summary": "Wrong-axis MODIFY clamped yaw while downwash stayed 5.1 m/s over the 3.8 m/s cap. Neighbor disk RPM rose. 9 min pad abort. Correct gate is climb clamp, not yaw hold.",
            "state_delta": {
                "quad": "yaw held 0.05 rad/s; climb still 1.20 m/s",
                "disk": "downwash 5.1 m/s still over cap",
                "mission": "9 min pad abort",
            },
            "surprises": [
                "Yaw collapsed as commanded; downwash never moved. Sidecar convicts the wrong bind without rotor physics.",
                "Delayed (9 min / delayed_surprise_s=540): pad abort and neighbor-disk inspect.",
            ],
            "recovery": {
                "correct_gate": "MODIFY on climb: 1.20 -> 0.35 m/s and leave yaw at planned 0.40 rad/s.",
                "correct_axis": "climb",
                "wrong_axis": "yaw",
                "wrong_edit_applied": {
                    "yaw_rps": 0.05,
                    "climb_mps": 1.2,
                    "bind_yaw_as_lift_loop": True,
                },
                "cost": "Neighbor-disk overspeed + 9 min pad abort (task/efficiency); downwash still over cap (safety near-miss).",
            },
            "race_result": {
                "winner": "anemo.downwash.mps (5.520 ms, 5.1 m/s)",
                "loser": "imu.vz.mps (5.780 ms, 1.20 m/s)",
                "margin_us": 260,
                "counterfactual_if_reversed": "IMU-first by < 260 us inside the 300 us window would still have been over the downwash cap. The incorrect MODIFY is a yaw bind, not a race-order error. Correct gate remains climb clamp 1.20 -> 0.35 m/s.",
            },
            "reward_inflection_t_us": 6040,
            "reward_inflection_note": "Task/efficiency collapse at the 6.040 ms wrong MODIFY (tick t_us=6040). Do not put inflection on the +9 min pad-abort tick.",
            "delayed_surprise_s": delayed,
        },
        "reward_components": reward_block(
            ticks,
            sums,
            total,
            "Wrong-MODIFY. total -0.79 = -0.26 + -0.24 + -0.24 + -0.11 + 0.06. Tick 6 t_us binds raster.delayed_surprise_s=540.",
        ),
        "raster": raster,
        "gate_snn": {
            "decision_window_ms": 0.30,
            "decision": "MODIFY",
            "populations": [
                pop("yaw_hold", 32, 0.5, 400.0, 0.30),
                pop("climb_clamp", 32, 0.8, 20.0, 0.30),
                veto("downwash_cap_veto", 16, 0.7),
            ],
        },
        "meta": meta_common(
            3,
            "aerial-swarm",
            [
                "modify",
                "wrong-gate",
                "wrong-modify",
                "wrong-axis",
                "sidecar-convictable",
                "independent-lif-raster",
                "tick6-sidecar-bound",
                "designed",
            ],
            "Teaches a probe that a correct downwash>cap read can still be a wrong gate when routing.table[0].to is policy.yaw_hold and executed climb_mps is unchanged.",
            5,
            extra={"supervisor_error_type": "wrong-modify"},
        ),
    }


def hidden_thoughts(obj, path=""):
    found = []
    if isinstance(obj, dict):
        for k, v in obj.items():
            child = f"{path}.{k}" if path else k
            norm = re.sub(
                r"[^a-z0-9]+",
                "_",
                re.sub(r"(?<=[a-z0-9])(?=[A-Z])", "_", str(k)).casefold(),
            ).strip("_")
            if norm in HIDDEN_THOUGHT_KEYS:
                found.append(child)
            found.extend(hidden_thoughts(v, child))
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            found.extend(hidden_thoughts(v, f"{path}[{i}]"))
    return found


def check_refractory(events, min_ms=0.8):
    by = defaultdict(list)
    for e in events:
        by[e["channel"]].append(e["t_rel_ms"])
    bad = []
    for ch, ts in by.items():
        ts.sort()
        for a, b in zip(ts, ts[1:]):
            if b - a < min_ms - 1e-9:
                bad.append((ch, a, b))
    return bad


def check_race(rec):
    lo, hi = rec["state"]["race_window_rel_ms"]
    chans = set()
    for e in rec["spike_events"]:
        if lo <= e["t_rel_ms"] <= hi:
            chans.add(e["channel"])
    return chans


def excerpt_overlap(rec):
    se = {round(e["t_rel_ms"], 1) for e in rec["spike_events"]}
    ex = {round(e["t_us"] / 1000.0, 1) for e in rec["raster"]["excerpt"]}
    if not se or not ex:
        return 0.0
    return len(se & ex) / len(se | ex)


def load_prior_descriptions():
    descs = []
    for p in sorted(LIVE.glob("batch-r*.jsonl")):
        if p.name.startswith("batch-r03"):
            continue
        for line in p.read_text().splitlines():
            if not line.strip():
                continue
            rec = json.loads(line)
            descs.append((rec["id"], rec["state"]["description"]))
    return descs


def validate_records(records):
    errors = []
    descs = [r["state"]["description"] for r in records]
    intra = []
    for i in range(len(descs)):
        for j in range(i + 1, len(descs)):
            intra.append((records[i]["id"], records[j]["id"], jaccard(descs[i], descs[j])))
    max_intra = max(x[2] for x in intra)
    prior = load_prior_descriptions()
    max_prior = 0.0
    worst_prior = None
    for rec in records:
        for pid, pdesc in prior:
            j = jaccard(rec["state"]["description"], pdesc)
            if j > max_prior:
                max_prior = j
                worst_prior = (rec["id"], pid, j)
    if max_intra >= 0.4:
        errors.append(f"intra Jaccard {max_intra} >= 0.4 {intra}")
    if max_prior >= 0.4:
        errors.append(f"prior Jaccard {worst_prior}")

    domains = [r["state"]["domain"] for r in records]
    if len(set(domains)) != 5:
        errors.append(f"domains not unique: {domains}")

    sims = [r["state"]["sim_or_real"] for r in records]
    if sims.count("designed") != 3 or sims.count("simulated") != 1 or sims.count("hil") != 1:
        errors.append(f"provenance mix {sims}")
    if "real" in sims:
        errors.append("sim_or_real real")

    decisions = [(r["id"], r["safety_decision"]["decision"], r["safety_decision"]["correctness"]) for r in records]
    correct_a = sum(1 for _, d, c in decisions if d == "ACCEPT" and c == "correct")
    correct_m = sum(1 for _, d, c in decisions if d == "MODIFY" and c == "correct")
    correct_r = sum(1 for _, d, c in decisions if d == "REJECT" and c == "correct")
    wrong_m = sum(1 for _, d, c in decisions if d == "MODIFY" and c == "incorrect")
    wrong_a = sum(1 for _, d, c in decisions if d == "ACCEPT" and c == "incorrect")
    if (correct_a, correct_m, correct_r, wrong_m) != (1, 2, 1, 1):
        errors.append(f"gate mix {decisions}")
    if wrong_a:
        errors.append("wrong-ACCEPT present")

    totals = [r["reward_components"]["total"] for r in records]
    if all(t > 0 for t in totals):
        errors.append("all-positive totals")
    if records[0]["reward_components"]["total"] >= 0:
        errors.append("partnered-neg not negative")

    banned_frags = (
        "Lumen-Quay",
        "Rivermead",
        "Fork-Haven",
        "Pylon-Wick",
        "Slate-March",
        "Coble-Yard",
        "Gannet-Lea",
        "Silt-Quern",
        "Bushing-Holt",
        "Insulator-Wick",
        "Pallet-Wythe",
        "Downdraft-Cairn",
        "Thalass-Ness",
        "Cinch-Quarry",
        "Clover-Weir",
        "Marrow-Dock",
        "Vesper-Lattice",
        "Brine-Well",
        "Saddle-Arc",
        "Ashlar-Gait",
        "2026-08-17",
        "2026-08-30",
    )
    for rec in records:
        where = rec["id"]
        blob = json.dumps(rec)
        for frag in banned_frags:
            if frag in blob:
                errors.append(f"{where} banned fragment {frag}")
        if rec["meta"]["round"] != 3:
            errors.append(f"{where} meta.round")
        if rec["id"] != f"ttf-r03-{11 + rec['meta']['batch_position'] - 1:03d}":
            errors.append(f"{where} id/batch_position")
        if rec["gate_snn"]["decision"] != rec["safety_decision"]["decision"]:
            errors.append(f"{where} gate_snn mismatch")
        ht = hidden_thoughts(rec)
        if ht:
            errors.append(f"{where} thought keys {ht}")
        if "thought" in blob.lower() and '"thought"' in blob.lower():
            errors.append(f"{where} thought substring key")
        bad = check_refractory(rec["spike_events"])
        if bad:
            errors.append(f"{where} refractory {bad}")
        chans = check_race(rec)
        if len(chans) < 2:
            errors.append(f"{where} race channels {chans}")
        nsp = len(rec["spike_events"])
        if not (5 <= nsp <= 40):
            errors.append(f"{where} spike count {nsp}")
        times = [e["t_rel_ms"] for e in rec["spike_events"]]
        if times != sorted(times):
            errors.append(f"{where} spike order")
        inf = rec["future_outcome"]["reward_inflection_t_us"]
        tick_ts = [t["t_us"] for t in rec["reward_components"]["ticks"]]
        if inf not in tick_ts:
            errors.append(f"{where} inflection not a tick")
        win_us = rec["raster"]["window_ms"] * 1000
        if rec["id"] == "ttf-r03-011" and not (0 <= inf <= win_us):
            errors.append(f"{where} partnered-neg inflection outside raster")
        tick6 = rec["reward_components"]["ticks"][-1]["t_us"]
        if tick6 <= win_us:
            errors.append(f"{where} tick6 inside raster")
        delayed = rec["future_outcome"]["delayed_surprise_s"]
        if tick6 != delayed * 1_000_000:
            errors.append(f"{where} tick6 bind {tick6} vs {delayed}")
        ov = excerpt_overlap(rec)
        if ov >= 0.8:
            errors.append(f"{where} excerpt overlap {ov}")
        ras = rec["raster"]
        if not (20 <= ras["window_ms"] <= 50):
            errors.append(f"{where} window")
        expected = round(ras["neurons"] * ras["mean_rate_hz"] * ras["window_s"])
        if abs(ras["spikes"] - expected) > 1:
            errors.append(f"{where} spike budget {ras['spikes']} vs {expected}")
        if abs(ras["energy_pJ"] - ras["spikes"] * 23) > 1e-6:
            errors.append(f"{where} energy_pJ")
        if abs(ras["energy_uJ"] - ras["spikes"] * 23e-6) > 1e-9:
            errors.append(f"{where} energy_uJ")
        if ras["excerpt_source"] != "independent_lif":
            errors.append(f"{where} not independent LIF")
        for ev in ras["excerpt"]:
            if not (0 <= ev["t_us"] <= win_us):
                errors.append(f"{where} excerpt t {ev}")
            if not (0 <= ev["neuron_id"] < ras["neurons"]):
                errors.append(f"{where} neuron {ev}")
        by_n = defaultdict(list)
        for ev in ras["excerpt"]:
            by_n[ev["neuron_id"]].append(ev["t_us"])
        for nid, ts in by_n.items():
            ts.sort()
            for a, b in zip(ts, ts[1:]):
                if b - a < 1000:
                    errors.append(f"{where} excerpt gap {nid} {a} {b}")
        tf = ras["routing"]["third_factor"]
        if abs(tf["tau_e_ms"] / 1000 - tf["tau_e_s"]) > 1e-9:
            errors.append(f"{where} tau_e pair")
        g = rec["gate_snn"]
        for p in g["populations"]:
            if "spikes" in p or "mean_rate_hz" in p:
                ws = g["decision_window_ms"] / 1000.0
                exp = round(p["neurons"] * p["mean_rate_hz"] * ws)
                if abs(p["spikes"] - exp) > 1:
                    errors.append(f"{where} gate_snn budget {p['name']} {p['spikes']} vs {exp}")
        if rec["safety_decision"]["decision"] == "ACCEPT":
            if rec["executed_action"]["parameters"] != rec["proposed_action"]["parameters"]:
                errors.append(f"{where} ACCEPT params differ")
            if rec["executed_action"]["name"] != rec["proposed_action"]["name"]:
                errors.append(f"{where} ACCEPT name differ")
        if rec["safety_decision"]["decision"] == "MODIFY":
            if rec["executed_action"]["parameters"] == rec["proposed_action"]["parameters"]:
                errors.append(f"{where} MODIFY params identical")
        if rec["safety_decision"]["correctness"] == "incorrect":
            if "recovery" not in rec["future_outcome"]:
                errors.append(f"{where} missing recovery")
            if rec["meta"].get("supervisor_error_type") != "wrong-modify":
                errors.append(f"{where} supervisor_error_type")
        rc = rec["reward_components"]
        s = rc["task_progress"] + rc["safety"] + rc["efficiency"] + rc["coherence"] + rc["exploration"]
        if abs(s - rc["total"]) > 1e-6:
            errors.append(f"{where} total {rc['total']} vs {s}")
        for k in ("task_progress", "safety", "efficiency", "coherence", "exploration"):
            ts = sum(t[k] for t in rc["ticks"])
            if abs(ts - rc[k]) > 1e-6:
                errors.append(f"{where} {k} ticks {ts} vs {rc[k]}")
        v_err, kind = check_line(rec, where, factory_staging=True)
        if v_err:
            errors.append(f"{where} check_line {v_err} kind={kind}")
        t_err = check_thalamic(rec, where)
        if t_err:
            errors.append(f"{where} check_thalamic {t_err}")
        st = raster_status(rec, require_raster=True, require_routing_table=True)
        if not st["raster_valid"] or st["reason_codes"]:
            errors.append(f"{where} raster_status {st}")
        if not st.get("gate_snn_present"):
            errors.append(f"{where} gate_snn missing")
        if '"sim_or_real": "real"' in blob or '"sim_or_real":"real"' in blob:
            errors.append(f"{where} nested real")
        if rec["meta"]["rights"]["intended_use"] != "research_only":
            errors.append(f"{where} rights")
        if rec["meta"].get("training_ready"):
            errors.append(f"{where} training_ready")
        if rec["state"]["sim_or_real"] == "real":
            errors.append(f"{where} real origin")
    return errors, max_intra, max_prior, worst_prior, intra


def notes_text(records, max_intra, max_prior, worst_prior, intra):
    ras_rows = []
    for r in records:
        ras = r["raster"]
        ras_rows.append(
            f"| {r['id']} | {r['state']['domain']} | {ras['neurons']} | {ras['mean_rate_hz']} | {ras['window_ms']} | {ras['spikes']} | {ras['energy_pJ']} | {ras['energy_uJ']} |"
        )
    rew_rows = []
    for r in records:
        rc = r["reward_components"]
        inf = r["future_outcome"]["reward_inflection_t_us"]
        ticks = r["reward_components"]["ticks"]
        idx = next(i + 1 for i, t in enumerate(ticks) if t["t_us"] == inf)
        rew_rows.append(
            f"| {r['id'][-3:]} | 6 | {rc['task_progress']:+.2f} | {rc['safety']:+.2f} | {rc['efficiency']:+.2f} | {rc['coherence']:+.2f} | {rc['exploration']:+.2f} | {rc['total']:+.2f} | {idx} ({inf}) |"
        )
    intra_s = ", ".join(f"{a}/{b}={j:.3f}" for a, b, j in sorted(intra, key=lambda x: -x[2])[:3])
    prior_s = f"{worst_prior[0]} vs {worst_prior[1]}" if worst_prior else "n/a"
    return f"""# Thalamic Trajectory Factory — NOTES-r03

- Factory: `thalamic-trajectory-factory`
- Run label: `2026-09-02-final-heavy`
- Generator: `grok-4.6`
- Channel: SuperGrok Heavy consumer chat (RM-793 research-only)
- Quota: 5
- Quality: Q=5
- IDs: `ttf-r03-011` … `ttf-r03-015`
- Domains this batch: `surgical-assist`, `autonomous-driving`, `humanoid-locomotion`, `underwater-rov`, `aerial-swarm`

Round 3 rotates onto r02 remaining 8-pool sit-outs `surgical-assist` / `autonomous-driving` / `humanoid-locomotion` plus new plants on `underwater-rov` and `aerial-swarm`. Plants are invented (Calyx-Brae / Scope-U4, Roundel-Wath / Ego-E7, Tread-Kame / Biped-K4, Floe-Staith / Glider-G3, Scarp-Lea / Quad-S9). Do not restack r01 plants (Lumen-Quay, Rivermead, Fork-Haven, Pylon-Wick, Slate-March), r02 plants (Coble-Yard, Gannet-Lea, Silt-Quern, Bushing-Holt, Insulator-Wick), or r21/r41/r61 chemical plants.

## Batch map

| id | domain | decision | correctness | sim_or_real | total | edge |
|----|--------|----------|-------------|-------------|-------|------|
| ttf-r03-011 | surgical-assist | MODIFY | correct | designed | **-0.42** | Calyx-Brae CB-9 / Scope-U4: tip FT beats irrigation flowmeter; stone roll inside 44 ms raster; independent LIF |
| ttf-r03-012 | autonomous-driving | MODIFY | correct | designed | +1.05 | Roundel-Wath RW-5 / Ego-E7: radar gore 0.31 m2 > 0.15 cap; speed 14 -> 6 m/s |
| ttf-r03-013 | humanoid-locomotion | REJECT | correct | hil | +0.84 | Tread-Kame TK-HIL / Biped-K4: CoP 0.14 m beats IMU 2.1 deg; freeze swing |
| ttf-r03-014 | underwater-rov | ACCEPT | correct | simulated | +1.08 | Floe-Staith FS-6 sim / Glider-G3: tether 180 N and DVL 0.22 m/s already legal |
| ttf-r03-015 | aerial-swarm | MODIFY | **incorrect (wrong-modify / wrong-axis)** | designed | -0.79 | Scarp-Lea SL-8 / Quad-S9: downwash 5.1 > 3.8; yaw clamped not climb |

Gate mix: 1 ACCEPT, 2 correct MODIFY (one partnered-neg, in-window), 1 correct REJECT, 1 incorrect MODIFY (wrong-modify / wrong-axis). Provenance: designed×3, simulated×1, hil×1 (Tread-Kame TK-HIL belt). Intra-batch Jaccard on `state.description` {max_intra:.3f} (top pairs {intra_s}). All < 0.4. Max Jaccard vs prior committed rounds in this factory dir {max_prior:.3f} ({prior_s}). Totals not all-positive (011 −0.42, 015 −0.79).

## Wrong-modify

**ttf-r03-015** is the mandated incorrect gate (`safety_decision.correctness=incorrect`, `meta.supervisor_error_type=wrong-modify`). Round 3 is odd, so wrong-modify (even rounds host wrong-reject). This is **wrong-axis** (climb vs yaw). Not r01 wrong-joint (stance ankle vs hip yaw), not r13 wrong-axis (J2/J6), not r14 wrong-loop (AC vs DC), not a wrong-ACCEPT. Do not emit a wrong-ACCEPT.

Scarp-Lea SL-8 / Quad-S9 reads live downwash **5.1 m/s** against a **3.8 m/s** cap. IMU climb is **1.20 m/s**. Sidecar arithmetic `5.1 > 3.8` is true. A timely MODIFY at `t_gate_us=6040` cuts climb **1.20 -> 0.35 m/s** and leaves yaw **0.40 rad/s**. A weak supervisor binds the lift loop as yaw and MODIFY-clamps yaw **0.40 -> 0.05 rad/s**. Live downwash stays **5.1 > 3.8**. Convictable without rotor physics: `evidence.downwash_mps > evidence.cap_mps`, `evidence.force_axis == climb`, `executed_action` sets `bind_yaw_as_lift_loop=true` and `yaw_rps=0.05` with `climb_mps=1.20`, `raster.routing.table` sends `relay.anemo.downwash` → `policy.yaw_hold` (weight 0.74) with no positive weight to `policy.climb_clamp`, and `gate_snn` has `yaw_hold` above threshold while `climb_clamp` is not (`spikes=0`). Recovery: MODIFY climb 1.20 -> 0.35 m/s at t_gate; leave yaw at 0.40 rad/s. Cost: 9 min pad abort (`abort_s=540`).

## Partnered-negative in-window (011)

**ttf-r03-011** is the partnered negative: process-correct MODIFY (irrigation held 14 mL/min; tip 1.92 N <= 2.20 cap) while the world still charges. Safety −0.58 prices the stone fragment roll at **22.800 ms**; `task_progress` stays +0.30 because the clamp completed. Inflection `t_us=22800` is tick 5 and is **inside** the 44 ms raster (`22800 ≤ 44000`). Named un-netted loss: 11 min basket retrieve + lumen flush (`abort_s=660`). Not folded into process heads.

Independent LIF (labeled sidecar sim on every record this round): `state.sim_or_real` remains `designed` on 011. `raster.excerpt_source=independent_lif`, `raster.sim_scope=sidecar_only`, `raster.lif` seed 3011, stim `[22000, 25600]`. Excerpt is membrane crossings (`lif.clamp` early vs `lif.stone` 22–25.6 ms), not a 1:1 remap of `spike_events`. `meta.tags` include `independent-lif-raster` and `sidecar-sim-only`. 012–015 also carry independent LIF excerpts (seeds 3012–3015).

## Reward formula and tick reconciliation

Declared aggregation on every record:

`total = task_progress + safety + efficiency + coherence + exploration`

Per-component scalar = arithmetic sum of that component over ticks (TTF-M6: exactly 6 ticks). Tick 6 is bound to a published sidecar (`abort_s`, `survey_s`, `dwell_s`) via `future_outcome.delayed_surprise_s` and is strictly after the raster window. Inflection `t_us` is an actual tick.

| id | ticks | tp | saf | eff | coh | exp | total | inflection tick |
|----|-------|----|-----|-----|-----|-----|-------|-----------------|
{chr(10).join(rew_rows)}

Tick-6 sidecar bind: 011 `abort_s=660`, 012 `survey_s=240`, 013 `abort_s=360`, 014 `dwell_s=120`, 015 `abort_s=540`.

## Raster / energy (Loihi-2 4-core, 23 pJ/spike)

| id | domain | n | rate Hz | window_ms | spikes | energy_pJ | energy_uJ |
|----|--------|---|---------|-----------|--------|-----------|-----------|
{chr(10).join(ras_rows)}

`spikes = round(n × rate × window_s)`. Every record carries `gate_snn` whose `decision` matches the safety gate; populations that declare rate+spikes meet the same ±1 budget against `decision_window_s`. `routing.third_factor` has modulator (NA / ACh / DA / 5-HT / adenosine), `tau_e_s`/`tau_e_ms` pair, and eligibility. Excerpt same-neuron gap ≥ 1000 µs; spike trains same-channel refractory ≥ 0.8 ms. Excerpts are independent LIF membrane crossings, not a 1:1 remap of `spike_events` times (overlap < 0.8).

## Gaps this round fixes vs r02 NOTES

r02 asked r03 to rotate remaining 8-pool sit-outs (`surgical-assist`, `autonomous-driving`, `humanoid-locomotion`) with new plants; **wrong-modify** (odd round); keep one partnered-neg in-window. This batch does that and adds new plants on `underwater-rov` (ACCEPT, not r02 REJECT) and `aerial-swarm` (wrong-axis MODIFY, not r02 HIL climb clamp). Wrong-ACCEPT remains absent (guard). Independent LIF is labeled on all five records.

## Local checks (this window)

Generator stdout: self_check (Jaccard, refractory, race, spike budget, energy, tick6 bind, gate_snn budget, rights). Then `json.loads` every line, `validate_run.check_line`, `raster_status`, `verify_batch_for_frontier(strict=True)`, `spike_probe.py --strict`.

Never `training_ready`. Never `sim_or_real=real`. Create-only into the assigned live path; did not clobber 2026-08-17 / 2026-08-30; did not overwrite existing r03 files (c-suffix if occupied).

## Residual weaknesses (honest)

1. `underwater-rov` and `aerial-swarm` repeat r02 domain slugs (new plants, new gates, new origins; Jaccard vs r02 still < 0.4).
2. Wrong-ACCEPT still absent (guard).
3. Tick-6 sidecar bind is standing machinery (r14+), not a new class. ISI histogram sidecar was considered and not added.
4. 015 wrong-axis is climb vs yaw; a later odd round could densify wrong-modify on a delayed clamp rather than a wrong joint/axis.
5. 013 HIL dummy payload never spins; a partnered HIL near-miss where REJECT is correct but a delayed belt slip still nicks the ankle would densify the REJECT class.

## Next densification target

Round 04: even-round **wrong-reject**; sit out this batch's three r02-holdovers if possible; keep one partnered-neg in-window; consider ISI histogram sidecar.

Novel coverage: 36.0%
"""


def exclusive_write(path: Path, data: str):
    flags = os.O_CREAT | os.O_EXCL | os.O_WRONLY
    fd = os.open(str(path), flags, 0o644)
    with os.fdopen(fd, "w", encoding="utf-8") as f:
        f.write(data)


def main():
    live_s = str(LIVE.resolve())
    if "2026-08-17" in live_s or "2026-08-30" in live_s:
        print("refusing forbidden tree", live_s, file=sys.stderr)
        sys.exit(5)

    records = [rec_011(), rec_012(), rec_013(), rec_014(), rec_015()]
    errors, max_intra, max_prior, worst_prior, intra = validate_records(records)
    if errors:
        print("SELF-CHECK FAIL", file=sys.stderr)
        for e in errors:
            print(" ", e, file=sys.stderr)
        sys.exit(1)

    staging = Path("/tmp/ttf-r03-out")
    staging.mkdir(parents=True, exist_ok=True)
    jsonl = "\n".join(json.dumps(r, ensure_ascii=False, separators=(",", ":")) for r in records) + "\n"
    notes = notes_text(records, max_intra, max_prior, worst_prior, intra)
    (staging / "batch-r03.jsonl").write_text(jsonl, encoding="utf-8")
    (staging / "NOTES-r03.md").write_text(notes, encoding="utf-8")

    counts, findings, blocked = verify_batch_for_frontier(staging / "batch-r03.jsonl", strict=True)
    print("verify_batch", counts, "blocked", blocked)
    if findings:
        print("findings", findings)
    if blocked:
        sys.exit(2)

    from spike_probe import load_rasters

    rasters, problems = load_rasters([staging / "batch-r03.jsonl"])
    print("spike_probe rasters", len(rasters), "problems", problems)
    if problems:
        sys.exit(3)
    if len(rasters) != 5:
        print("expected 5 rasters", len(rasters))
        sys.exit(3)

    live_batch = LIVE / "batch-r03.jsonl"
    live_notes = LIVE / "NOTES-r03.md"
    if live_batch.exists() or live_notes.exists():
        live_batch = LIVE / "batch-r03c.jsonl"
        live_notes = LIVE / "NOTES-r03c.md"
        if live_batch.exists() or live_notes.exists():
            print("collision: r03 and r03c exist", file=sys.stderr)
            sys.exit(4)

    exclusive_write(live_batch, jsonl)
    exclusive_write(live_notes, notes)
    print("WROTE", live_batch)
    print("WROTE", live_notes)
    print("max_intra", round(max_intra, 3), "max_prior", round(max_prior, 3), worst_prior)
    for r in records:
        sd = r["safety_decision"]
        print(
            r["id"],
            r["state"]["domain"],
            sd["decision"],
            sd["correctness"],
            r["state"]["sim_or_real"],
            r["reward_components"]["total"],
            r["meta"].get("supervisor_error_type"),
        )


if __name__ == "__main__":
    main()
