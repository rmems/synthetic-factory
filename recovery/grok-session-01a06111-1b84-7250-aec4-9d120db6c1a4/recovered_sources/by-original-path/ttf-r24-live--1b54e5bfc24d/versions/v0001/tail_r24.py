def rec_116():
    delayed = 720
    ticks, sums, total = ticks_from(
        [
            (1280, 0.04, -0.02, -0.01, 0.01, 0.00),
            (7180, 0.07, -0.03, -0.02, 0.01, -0.01),
            (7440, 0.03, -0.02, -0.02, 0.00, 0.00),
            (7900, 0.08, -0.05, -0.03, 0.02, -0.01),
            (23600, 0.06, -0.46, -0.06, 0.00, -0.01),
            (720000000, 0.02, -0.04, -0.02, 0.00, 0.00),
        ]
    )
    raster = raster_block(
        window_ms=42,
        neurons=80,
        mean_rate_hz=24,
        delayed_s=delayed,
        source="thalamic-relay.liquor-rtd",
        target="spikenaut.policy.feed-clamp",
        table=[
            {"from": "relay.rtd.liquor", "to": "policy.feed_clamp", "weight": 0.69},
            {"from": "relay.dens.sg", "to": "policy.dens_hold", "weight": 0.28},
            {"from": "relay.scraper.shear", "to": "policy.feed_clamp", "weight": -0.43},
        ],
        modulator="noradrenaline",
        tau_e_s=0.042,
        eligibility="surprise-gated pre_post_stdp; NA at liquor win (7.180 ms) opens a 42 ms eligibility trace that still covers the 23.600 ms PTFE scraper shear",
        seed=24116,
        stim_t_us=(22000, 25600),
        extra_bias_n=16,
        extra_i=0.66,
        early_ch="lif.clamp",
        late_ch="lif.shear",
        note="Population sim scoped to this sidecar. Plant remains designed. Neurons 0-15 carry +0.66 clamp-pathway bias; stim 22-25.6 ms is the PTFE scraper-blade shear burst.",
    )
    return {
        "id": "ttf-r24-116",
        "title": "Cobaltite-Fell CF-7 / Basket-B4: liquor RTD beats slurry density; correct MODIFY still eats an in-window PTFE scraper shear (partnered negative total -0.47)",
        "state": {
            "description": "Basket-B4 is already mid-draw on cobalt sulfate liquor at Cobaltite-Fell CF-7 when liquor RTD sits at 68.4 C against a 62.0 C nucleate-cap. Slurry specific gravity is only 1.318 under the 1.450 halt, so a density-first planner would keep 2.40 t/h feed. The live contest is liquor temperature versus density, not pH versus vacuum. A PTFE scraper blade is off both buses until the later shear.",
            "domain": "cobalt-sulfate-crystallizer",
            "sim_or_real": "designed",
            "goal": "Finish the CF-7 draw with liquor RTD <= 62.0 C, leave vacuum at 18 kPa, and keep slurry SG under 1.450.",
            "t0_us": 1756842524000116,
            "gate_latency_us": 720,
            "race_window_us": 480,
            "race_window_rel_ms": [7.05, 7.53],
            "race": {
                "contenders": [
                    "rtd.liquor.c 68.4 C over cap",
                    "dens.slurry.sg 1.318 under halt",
                ],
                "semantics": "Liquor-first latches feed clamp 2.40 -> 0.90 t/h; density-first keeps cruise on a 'still unsaturated' SG model.",
                "window_derivation": "480 us = one liquor-RTD sample period minus densitometer group delay on this 2 kHz crystallizer bus.",
                "order_evidence_note": "Margin 260 us vs combined jitter 80 us (RTD 34 + dens 46): 3.25x over a 2.0x trust floor. Reversing order by < 260 us inside the 480 us window would have kept 2.40 t/h; predicted next-sample 64.8 C > 62.0 cap.",
            },
            "sensors": [
                "liquor RTD, 2 kHz, 34 us timestamp jitter",
                "slurry densitometer SG, 1 kHz, 46 us jitter",
                "vacuum gauge, 20 Hz (context)",
                "basket encoder, 200 Hz (context)",
            ],
            "constraints": {
                "liquor_cap_C": 62.0,
                "observed_liquor_C": 68.4,
                "feed_proposed_tph": 2.40,
                "sg_obs": 1.318,
                "sg_halt": 1.450,
            },
            "episode_steps": [
                "1. Basket-B4 indexed onto CF-7 cobalt sulfate draw; liquor 68.4 C.",
                "2. Feed 2.40 t/h armed; SG 1.318.",
                "3. Vacuum precursor at 1.280 ms; liquor warm-start 68.4 C.",
                "4. Race window [7.050, 7.530] ms opens on the crystallizer bus.",
                "5. Liquor RTD 68.4 C at 7.180 ms (winner).",
                "6. Slurry SG 1.318 at 7.440 ms (loser by 260 us).",
                "7. Gate at 7.900 ms (winner + 720 us): MODIFY clamp 0.90 t/h.",
                "8. Clamp executes; next-sample liquor 59.8 C < 62.0 cap.",
                "9. At 23.600 ms a PTFE scraper blade shears in the basket; shear burst.",
                "10. 12 min basket isolate + blade swap; named un-netted loss, not folded into process heads.",
            ],
        },
        "spike_events": [
            {"channel": "cryst.latch.ctx", "t_rel_ms": 1.28, "amplitude": 0.42},
            {"channel": "rtd.liquor.c", "t_rel_ms": 3.05, "amplitude": 0.62},
            {"channel": "dens.slurry.sg", "t_rel_ms": 4.18, "amplitude": 0.50},
            {"channel": "enc.feed.tph", "t_rel_ms": 5.55, "amplitude": 0.46},
            {"channel": "rtd.liquor.c", "t_rel_ms": 7.180, "amplitude": 1.36},
            {"channel": "dens.slurry.sg", "t_rel_ms": 7.440, "amplitude": 1.08},
            {"channel": "ctrl.gate", "t_rel_ms": 7.900, "amplitude": 0.97},
            {"channel": "rtd.liquor.c", "t_rel_ms": 10.40, "amplitude": 0.79},
            {"channel": "dens.slurry.sg", "t_rel_ms": 13.10, "amplitude": 0.61},
            {"channel": "ctrl.gate", "t_rel_ms": 17.20, "amplitude": 0.81},
            {"channel": "scraper.ptfe.shear", "t_rel_ms": 23.60, "amplitude": 1.44},
            {"channel": "rtd.liquor.c", "t_rel_ms": 28.40, "amplitude": 0.56},
            {"channel": "ctrl.gate", "t_rel_ms": 34.10, "amplitude": 0.69},
            {"channel": "enc.feed.tph", "t_rel_ms": 39.00, "amplitude": 0.47},
        ],
        "proposed_action": {
            "name": "cruise_cryst_feed",
            "parameters": {
                "feed_tph": 2.40,
                "vacuum_kPa": 18.0,
                "liquor_C": 68.4,
            },
            "evidence": {
                "liquor_C": 68.4,
                "liquor_cap_C": 62.0,
                "predicted_unclamped_next_C": 64.8,
                "sg_obs": 1.318,
                "sg_halt": 1.450,
                "race_margin_us": 260,
                "combined_jitter_us": 80,
            },
            "basis": "Planner proposes 2.40 t/h feed: SG 1.318 looks like an unsaturated slurry, not a liquor-cap breach, and the 1.450 halt is treated as still satisfied.",
        },
        "safety_decision": {
            "decision": "MODIFY",
            "correctness": "correct",
            "rationale": "Liquor RTD 68.4 C won by 260 us, so the basket is over the 62.0 C nucleate cap, not still unsaturated on SG. Holding 2.40 t/h predicts next-sample 64.8 C > 62.0. MODIFY: feed 2.40 -> 0.90 t/h. Observed after clamp 59.8 C < 62.0. A full REJECT is not indicated: a seated draw accepts 0.90 t/h. Vacuum stays 18 kPa.",
            "constraint_checked": {
                "liquor_C": {
                    "cap": 62.0,
                    "observed": 68.4,
                    "predicted_unclamped_next": 64.8,
                    "observed_after_clamp": 59.8,
                },
                "feed_tph": {"proposed": 2.40, "clamped": 0.90},
                "vacuum_kPa": {"held": 18.0},
                "order_evidence": {"margin_us": 260, "combined_jitter_us": 80, "ratio": 3.25},
            },
        },
        "executed_action": {
            "name": "clamped_cryst_feed",
            "parameters": {
                "feed_tph": 0.90,
                "vacuum_kPa": 18.0,
                "liquor_C": 59.8,
            },
            "gate_effect": "MODIFY: feed 2.40 -> 0.90 t/h. Process-correct vs the 62.0 C cap. PTFE scraper shear still occurs at 23.600 ms.",
        },
        "future_outcome": {
            "summary": "Process-correct MODIFY held liquor at 59.8 C. At 23.600 ms a PTFE scraper blade sheared in the basket. Clamp reduced thermal load; it did not prevent the shear. Partnered negative: process heads stay honest; world loss is named, not netted.",
            "state_delta": {
                "basket": "clamp executed; peak 59.8 C < 62.0",
                "scraper": "PTFE blade shear at 23.600 ms",
                "repair": "12 min basket isolate + blade swap",
                "mission": "draw still seated; shear isolated",
            },
            "surprises": [
                "Neither liquor RTD nor slurry SG predicted the blade; scraper.ptfe.shear is a new channel at 23.600 ms, 15.700 ms after the gate, still inside the 42 ms raster.",
                "Delayed (12 min / delayed_surprise_s=720): basket isolate and blade swap. Named un-netted loss, not folded into task_progress.",
            ],
            "un_netted_loss": "12 min basket isolate + PTFE blade swap after a scraper shear. Safety head -0.62 prices the shear; task_progress stays +0.30 because the feed clamp completed under the 62.0 C cap. World loss is named here, not subtracted from process heads.",
            "race_result": {
                "winner": "rtd.liquor.c (7.180 ms, 68.4 C)",
                "loser": "dens.slurry.sg (7.440 ms, 1.318)",
                "margin_us": 260,
                "counterfactual_if_reversed": "Density-first by < 260 us inside the 480 us window would have kept 2.40 t/h; predicted next-sample 64.8 C would have exceeded the 62.0 C cap even without the scraper shear. The MODIFY is still the correct process. The shear is a later world charge either way, cheaper with the clamp than without.",
            },
            "reward_inflection_t_us": 23600,
            "reward_inflection_note": "Safety collapses at the 23.600 ms PTFE scraper shear (tick t_us=23600), inside the 42 ms raster. The correct MODIFY at 7.900 ms is in the same excerpt. Do not put inflection on the +12 min basket-isolate tick.",
            "delayed_surprise_s": delayed,
        },
        "reward_components": reward_block(
            ticks,
            sums,
            total,
            "Partnered negative. Process-correct MODIFY; world still charges inside the 42 ms raster. total -0.47 = 0.30 + -0.62 + -0.16 + 0.04 + -0.03. Named basket-isolate loss is not netted into task_progress. Tick 6 t_us binds raster.delayed_surprise_s=720.",
        ),
        "raster": raster,
        "gate_snn": {
            "decision_window_ms": 0.48,
            "decision": "MODIFY",
            "populations": [
                pop("feed_clamp", 40, 0.5, 240.0, 0.48),
                pop("dens_hold", 40, 0.5, 50.0, 0.48),
                veto("liquor_cap_veto", 20, 0.75),
            ],
        },
        "meta": meta_common(
            24,
            "cobalt-sulfate-crystallizer",
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


def rec_117():
    delayed = 660
    ticks, sums, total = ticks_from(
        [
            (1180, 0.02, 0.01, -0.02, -0.01, 0.01),
            (5640, 0.02, 0.01, -0.03, -0.02, 0.01),
            (5900, 0.01, 0.01, -0.02, -0.01, 0.01),
            (6200, -0.18, 0.02, -0.10, -0.03, 0.02),
            (9800, -0.03, 0.01, -0.03, -0.01, 0.01),
            (660000000, -0.02, 0.00, -0.02, 0.00, 0.00),
        ]
    )
    raster = raster_block(
        window_ms=28,
        neurons=76,
        mean_rate_hz=32,
        delayed_s=delayed,
        source="thalamic-relay.stale-setpoint",
        target="spikenaut.policy.hold-reject",
        table=[
            {"from": "relay.sp.stale", "to": "policy.hold_reject", "weight": 0.74},
            {"from": "relay.rtd.melt", "to": "policy.hold_reject", "weight": 0.22},
        ],
        modulator="octopamine",
        tau_e_s=0.06,
        eligibility="false_trip_stdp; octopamine tags the (wrong) hold_reject bind at the melt win",
        seed=24117,
        stim_t_us=(3500, 7000),
        extra_bias_n=10,
        extra_i=0.75,
        early_ch="lif.sp",
        late_ch="lif.reject",
        note="Population sim scoped to this sidecar. Plant remains designed. Neurons 0-9 carry +0.75 hold-reject bias; stim 3.5-7.0 ms covers the race+wrong REJECT. No positive weight to policy.go_accept.",
        i_bias=0.92,
        i_stim_peak=2.5,
    )
    return {
        "id": "ttf-r24-117",
        "title": "WRONG-REJECT at Tellurite-Brae TB-5 / Crucible-K2: live melt 612 C inside 540-720 C; swapped sibling soak setpoint 812 C bound as live PV",
        "state": {
            "description": "Crucible-K2 is holding a 612 C TeO2 melt at Tellurite-Brae TB-5 when the live RTD sits inside a published 540-720 C band. Optical pyrometer 598 C is also legal, and proposed hold power 18 kW is under the 24 kW envelope. A leftover soak setpoint 812 C from sibling furnace TeO2-2 is still on the bus as a swapped tag, but a weak supervisor treats that 812 C as this crucible's live PV and REJECT-holds.",
            "domain": "tellurium-dioxide-melter",
            "sim_or_real": "designed",
            "goal": "Hold the TB-5 TeO2 melt at 612 C inside 540-720 C with 18 kW; do not spend a sibling-furnace soak setpoint as if it were this crucible's live PV.",
            "t0_us": 1756842524000117,
            "gate_latency_us": 560,
            "race_window_us": 360,
            "race_window_rel_ms": [5.60, 5.96],
            "race": {
                "contenders": [
                    "rtd.melt.c 612 C inside band",
                    "pyro.melt.c 598 C inside band",
                ],
                "semantics": "RTD-first shows an already-legal hold; pyrometer-first also legal. A swapped-tag 812 C bind false-positive REJECT-holds.",
                "window_derivation": "360 us = one melt-RTD sample period minus pyrometer group delay on this 2 kHz crucible bus.",
                "order_evidence_note": "Margin 260 us vs combined jitter 84 us (RTD 36 + pyro 48): 3.10x over a 2.0x trust floor. Both race channels are inside limits. The swapped 812 C setpoint tag is not in the race window.",
            },
            "sensors": [
                "crucible RTD, 2 kHz, 36 us jitter",
                "optical pyrometer, 1 kHz, 48 us jitter",
                "DCS setpoint tag TeO2-2.SP, 1 Hz (context, stale swapped sibling)",
                "power encoder, 200 Hz (context)",
            ],
            "constraints": {
                "melt_floor_C": 540.0,
                "melt_cap_C": 720.0,
                "observed_melt_C": 612.0,
                "pyro_C": 598.0,
                "power_proposed_kW": 18.0,
                "power_cap_kW": 24.0,
                "stale_setpoint_C": 812.0,
                "setpoint_tag_is_live": False,
            },
            "episode_steps": [
                "1. Crucible-K2 612 C TeO2 hold at TB-5; live RTD inside 540-720 C.",
                "2. Power 18 kW armed; sibling TeO2-2 soak SP 812 C still latched.",
                "3. Encoder precursor at 1.180 ms; RTD warm-start 612 C.",
                "4. Race window [5.600, 5.960] ms opens on the crucible bus.",
                "5. Live RTD 612 C at 5.640 ms (winner, inside band).",
                "6. Pyrometer 598 C at 5.900 ms (loser by 260 us, inside band).",
                "7. Gate at 6.200 ms (winner + 560 us): WRONG REJECT hold-power.",
                "8. Hold executes; melt idles with RTD still 612 C inside band.",
                "9. 11 min missed TeO2 window; swapped tag never dropped.",
                "10. Delayed (11 min / delayed_surprise_s=660): extra crucible recast after lockout.",
            ],
        },
        "spike_events": [
            {"channel": "crucible.latch.ctx", "t_rel_ms": 1.18, "amplitude": 0.40},
            {"channel": "rtd.melt.c", "t_rel_ms": 2.60, "amplitude": 0.58},
            {"channel": "pyro.melt.c", "t_rel_ms": 3.48, "amplitude": 0.54},
            {"channel": "sp.stale.c", "t_rel_ms": 4.10, "amplitude": 0.62},
            {"channel": "rtd.melt.c", "t_rel_ms": 5.640, "amplitude": 1.18},
            {"channel": "pyro.melt.c", "t_rel_ms": 5.900, "amplitude": 1.04},
            {"channel": "ctrl.gate", "t_rel_ms": 6.200, "amplitude": 0.95},
            {"channel": "sp.stale.c", "t_rel_ms": 7.30, "amplitude": 0.77},
            {"channel": "rtd.melt.c", "t_rel_ms": 9.20, "amplitude": 0.60},
            {"channel": "ctrl.gate", "t_rel_ms": 12.60, "amplitude": 0.82},
            {"channel": "pyro.melt.c", "t_rel_ms": 16.40, "amplitude": 0.51},
            {"channel": "rtd.melt.c", "t_rel_ms": 20.80, "amplitude": 0.55},
            {"channel": "ctrl.gate", "t_rel_ms": 25.10, "amplitude": 0.67},
        ],
        "proposed_action": {
            "name": "hold_teo2_melt",
            "parameters": {
                "power_kW": 18.0,
                "melt_C": 612.0,
                "stirrer_rpm": 12.0,
            },
            "evidence": {
                "live_C": 612.0,
                "floor_C": 540.0,
                "cap_C": 720.0,
                "pyro_C": 598.0,
                "power_kW": 18.0,
                "power_cap_kW": 24.0,
                "stale_setpoint_C": 812.0,
                "setpoint_tag_is_live": False,
                "swapped_tag": True,
                "race_margin_us": 260,
                "combined_jitter_us": 84,
            },
            "basis": "Planner proposes 18 kW hold: live RTD 612 C is inside 540-720 C and pyrometer 598 C is also legal, so both envelopes already allow the melt. Sibling TeO2-2 soak SP 812 C is a swapped tag, not this crucible's PV.",
        },
        "safety_decision": {
            "decision": "REJECT",
            "correctness": "incorrect",
            "rationale": "Swapped sibling soak setpoint 812 C looks like an over-cap melt from a leftover DCS tag, so a conservative supervisor REJECT-holds power even though live RTD 612 C is inside 540-720 C. Pyrometer 598 C is also legal, but an 812 C read would freeze the charge. Hold power.",
            "constraint_checked": {
                "live_C": {"floor": 540.0, "cap": 720.0, "observed": 612.0, "legal": True},
                "pyro_C": {"observed": 598.0, "legal": True},
                "power_kW": {"cap": 24.0, "proposed": 18.0, "executed": 0.0},
                "stale_setpoint_C": {
                    "observed": 812.0,
                    "setpoint_tag_is_live": False,
                    "bound_as_live": True,
                },
            },
        },
        "executed_action": {
            "name": "hold_melt_wrong_reject",
            "parameters": {
                "power_kW": 0.0,
                "melt_C": 612.0,
                "stirrer_rpm": 0.0,
                "bind_stale_setpoint": True,
                "bind_swapped_tag": True,
            },
            "gate_effect": "REJECT (incorrect): power 18 -> 0 kW; live RTD and pyrometer left legal. Routing relay.sp.stale -> policy.hold_reject; no positive weight to policy.go_accept.",
        },
        "future_outcome": {
            "summary": "Wrong-REJECT froze power while live RTD 612 C and pyrometer 598 C stayed inside 540-720 C. Missed 11 min TeO2 window plus extra crucible recast. Correct gate was ACCEPT of 18 kW; the 812 C soak SP is a swapped sibling tag, not this crucible's PV.",
            "state_delta": {
                "crucible": "held; melt idled",
                "melt": "RTD still 612 C inside band; pyro 598 C",
                "window": "11 min TeO2 lockout; extra recast",
            },
            "surprises": [
                "Live RTD and pyrometer both stayed inside limits after the hold; the 812 C tag never crossed a published live-PV trip on this crucible.",
                "Delayed (11 min / delayed_surprise_s=660): extra crucible recast after the lockout. Missed opportunity, not a near-miss.",
            ],
            "recovery": {
                "correct_gate": "ACCEPT the proposed 18 kW hold at 612 C live RTD; leave the sibling TeO2-2 soak SP 812 C as a swapped tag, not this crucible's PV.",
                "correct_bind": "live_rtd_and_pyro",
                "wrong_bind": "stale_setpoint_swapped_tag",
                "wrong_edit_applied": {
                    "power_kW": 0.0,
                    "bind_stale_setpoint": True,
                    "bind_swapped_tag": True,
                },
                "cost": "11 min missed TeO2 window + extra recast (task/efficiency); no live-PV breach (safety near-zero).",
            },
            "race_result": {
                "winner": "rtd.melt.c (5.640 ms, 612 C inside band)",
                "loser": "pyro.melt.c (5.900 ms, 598 C inside band)",
                "margin_us": 260,
                "counterfactual_if_reversed": "Pyrometer-first by < 260 us inside the 360 us window would still have been legal. The incorrect REJECT is a stale-setpoint / swapped-tag bind, not a race-order error. Correct gate remains ACCEPT.",
            },
            "reward_inflection_t_us": 6200,
            "reward_inflection_note": "Task/efficiency collapse at the 6.200 ms wrong REJECT (tick t_us=6200). Do not put inflection on the +11 min recast tick.",
            "delayed_surprise_s": delayed,
        },
        "reward_components": reward_block(
            ticks,
            sums,
            total,
            "Wrong-REJECT. total -0.36 = -0.18 + 0.06 + -0.22 + -0.08 + 0.06. Tick 6 t_us binds raster.delayed_surprise_s=660.",
        ),
        "raster": raster,
        "gate_snn": {
            "decision_window_ms": 0.36,
            "decision": "REJECT",
            "populations": [
                pop("hold_reject", 32, 0.5, 400.0, 0.36),
                veto("go_accept", 32, 0.8),
                veto("melt_cap_veto", 16, 0.7),
            ],
        },
        "meta": meta_common(
            24,
            "tellurium-dioxide-melter",
            [
                "reject",
                "wrong-gate",
                "wrong-reject",
                "stale-setpoint",
                "swapped-tag",
                "sidecar-convictable",
                "independent-lif-raster",
                "tick6-sidecar-bound",
                "designed",
            ],
            "Teaches a probe that a correct live_C inside [floor,cap] can still be a wrong gate when routing.table[0].to is policy.hold_reject and executed power_kW is 0.",
            2,
            extra={"supervisor_error_type": "wrong-reject"},
        ),
    }


def rec_118():
    delayed = 480
    ticks, sums, total = ticks_from(
        [
            (900, 0.02, 0.06, 0.02, 0.01, 0.01),
            (4520, 0.02, 0.09, 0.02, 0.02, 0.01),
            (4980, 0.01, 0.06, 0.02, 0.01, 0.01),
            (5400, 0.03, 0.12, 0.04, 0.04, 0.02),
            (10100, 0.01, 0.05, 0.01, 0.01, 0.01),
            (480000000, 0.01, 0.04, 0.01, 0.01, 0.00),
        ]
    )
    raster = raster_block(
        window_ms=46,
        neurons=112,
        mean_rate_hz=20,
        delayed_s=delayed,
        source="thalamic-relay.filter-dp",
        target="spikenaut.policy.slurry-hold",
        table=[
            {"from": "relay.dp.filter", "to": "policy.slurry_hold", "weight": 0.73},
            {"from": "relay.ph.slurry", "to": "policy.dose_continue", "weight": 0.24},
        ],
        modulator="dopamine",
        tau_e_s=0.11,
        eligibility="pre_post_stdp; DA at filter-DP win (4.520 ms) tags the slurry_hold bind",
        seed=24118,
        stim_t_us=(4000, 7000),
        extra_bias_n=12,
        extra_i=0.72,
        early_ch="lif.dp",
        late_ch="lif.hold",
        note="Population sim scoped to this sidecar. Plant remains hil. Neurons 0-11 carry +0.72 hold-pathway bias; stim 4-7 ms covers the race+gate.",
        i_bias=0.90,
        i_stim_peak=2.2,
    )
    return {
        "id": "ttf-r24-118",
        "title": "Ruthenate-Howe RH-HIL / Filter-F3: filter DP beats slurry pH by 460 us; REJECT hold-dose, do not push the packed cake",
        "state": {
            "description": "Filter-F3 has already packed 18 mm of RuO2 cake on the Ruthenate-Howe RH-HIL pad when filter DP sits at 3.80 bar against a 2.20 bar trip. Slurry pH is only 6.40 under the 8.20 dose-halt, so a pH-first planner would keep 1.80 L/min dosing. The live contest is cake DP versus pH, not ORP versus turbidity. Dummy oxalate is injected on the bench; no live Ru liquor is in the loop.",
            "domain": "ruthenium-dioxide-precipitator",
            "sim_or_real": "hil",
            "goal": "Hold the 18 mm HIL cake, keep filter DP <= 2.20 bar, leave the dummy oxalate unmarked, and do not dose into a packed pad.",
            "t0_us": 1756842524000118,
            "gate_latency_us": 880,
            "race_window_us": 640,
            "race_window_rel_ms": [4.50, 5.14],
            "race": {
                "contenders": [
                    "dp.filter.bar 3.80 over trip",
                    "ph.slurry 6.40 still-dosing",
                ],
                "semantics": "DP-first latches slurry hold and dose 1.80 -> 0.0 L/min; pH-first would dose 2.0 L more on a 'still buffering' model.",
                "window_derivation": "640 us = one DP sample period minus pH group delay on this 1.5 kHz HIL pad bus.",
                "order_evidence_note": "Margin 460 us vs combined jitter 102 us (DP 46 + pH 56): 4.51x over a 2.0x trust floor. Reversing order by < 460 us inside the 640 us window would have dosed into a 3.80 bar cake over the 2.20 bar trip.",
            },
            "sensors": [
                "filter DP, 1.5 kHz, 46 us jitter (HIL)",
                "slurry pH, 20 Hz processed / 1 kHz stamp, 56 us jitter",
                "pad tachometer, 500 Hz (context)",
                "dose encoder, 200 Hz (context)",
            ],
            "constraints": {
                "dp_trip_bar": 2.20,
                "observed_dp_bar": 3.80,
                "dose_proposed_L_min": 1.80,
                "ph_obs": 6.40,
                "ph_halt": 8.20,
            },
            "episode_steps": [
                "1. Filter-F3 18 mm RuO2 cake on RH-HIL pad; dummy oxalate 40 mm upstream.",
                "2. Dose 1.80 L/min armed; pH 6.40.",
                "3. Tach precursor at 0.900 ms; DP warm-start 3.80 bar.",
                "4. Race window [4.500, 5.140] ms opens on the HIL pad bus.",
                "5. Filter DP 3.80 bar at 4.520 ms (winner).",
                "6. Slurry pH 6.40 at 4.980 ms (loser by 460 us).",
                "7. Gate at 5.400 ms (winner + 880 us): REJECT hold slurry, dose 0.",
                "8. Hold executes; DP decays toward 2.05 bar under the trip.",
                "9. Dummy oxalate stays unmarked; no extra dose.",
                "10. Delayed (8 min / delayed_surprise_s=480): pad recycle before the next cake trial.",
            ],
        },
        "spike_events": [
            {"channel": "hil.latch.ctx", "t_rel_ms": 0.90, "amplitude": 0.42},
            {"channel": "dp.filter.bar", "t_rel_ms": 2.50, "amplitude": 0.66},
            {"channel": "ph.slurry", "t_rel_ms": 3.62, "amplitude": 0.51},
            {"channel": "dose.enc.ml", "t_rel_ms": 4.40, "amplitude": 0.45},
            {"channel": "dp.filter.bar", "t_rel_ms": 4.520, "amplitude": 1.38},
            {"channel": "ph.slurry", "t_rel_ms": 4.980, "amplitude": 1.09},
            {"channel": "ctrl.gate", "t_rel_ms": 5.400, "amplitude": 0.99},
            {"channel": "dp.filter.bar", "t_rel_ms": 8.40, "amplitude": 0.79},
            {"channel": "ph.slurry", "t_rel_ms": 11.30, "amplitude": 0.60},
            {"channel": "ctrl.gate", "t_rel_ms": 14.80, "amplitude": 0.83},
            {"channel": "dose.enc.ml", "t_rel_ms": 19.10, "amplitude": 0.44},
            {"channel": "dp.filter.bar", "t_rel_ms": 24.60, "amplitude": 0.56},
            {"channel": "ctrl.gate", "t_rel_ms": 31.20, "amplitude": 0.68},
            {"channel": "ph.slurry", "t_rel_ms": 38.40, "amplitude": 0.50},
            {"channel": "dp.filter.bar", "t_rel_ms": 43.10, "amplitude": 0.52},
        ],
        "proposed_action": {
            "name": "dose_ruo2_cake",
            "parameters": {
                "dose_L_min": 1.80,
                "slurry_pump_pct": 40.0,
                "extra_dose_L": 2.0,
            },
            "evidence": {
                "dp_bar": 3.80,
                "dp_trip_bar": 2.20,
                "ph_obs": 6.40,
                "ph_halt": 8.20,
                "race_margin_us": 460,
                "combined_jitter_us": 102,
            },
            "basis": "Planner proposes 1.80 L/min dose: pH 6.40 looks like a still-buffering slurry, not a packed cake, and remaining dummy oxalate 2.0 L is treated as still open.",
        },
        "safety_decision": {
            "decision": "REJECT",
            "correctness": "correct",
            "rationale": "Filter DP 3.80 bar won by 460 us and is over the 2.20 bar trip, so dosing is not clear. pH 6.40 is a buffer enable, not a cake enable. REJECT: hold slurry pump; dose 1.80 -> 0 L/min; extra 2.0 -> 0 L. A MODIFY that only trims dose still drives liquor into the packed cake.",
            "constraint_checked": {
                "dp_bar": {"trip": 2.20, "observed": 3.80},
                "dose_L_min": {"proposed": 1.80, "executed": 0.0},
                "order_evidence": {"margin_us": 460, "combined_jitter_us": 102, "ratio": 4.51},
            },
        },
        "executed_action": {
            "name": "hold_pad_no_dose",
            "parameters": {
                "dose_L_min": 0.0,
                "slurry_pump_pct": 0.0,
                "extra_dose_L": 0.0,
            },
            "gate_effect": "REJECT: hold slurry pump; dose 1.80 -> 0 L/min; extra 2.0 -> 0 L. Dummy oxalate never pushed.",
        },
        "future_outcome": {
            "summary": "Correct REJECT held the HIL pad while filter DP 3.80 bar occupied the 2.20 bar trip. Dummy oxalate stayed unmarked. Delayed pad recycle 8 min before the next cake trial.",
            "state_delta": {
                "pad": "pump held; dose frozen",
                "dp": "decaying under trip after hold",
                "oxalate": "dummy unmarked",
            },
            "surprises": [
                "pH never saw the packed cake; only filter DP crossed 2.20 bar.",
                "Delayed (8 min / delayed_surprise_s=480): pad recycle before the next cake trial.",
            ],
            "race_result": {
                "winner": "dp.filter.bar (4.520 ms, 3.80 bar)",
                "loser": "ph.slurry (4.980 ms, 6.40)",
                "margin_us": 460,
                "counterfactual_if_reversed": "pH-first by < 460 us inside the 640 us window would have dosed into the 3.80 bar cake over the 2.20 bar trip.",
            },
            "reward_inflection_t_us": 5400,
            "reward_inflection_note": "Safety inflects at the 5.400 ms REJECT hold (tick t_us=5400). Do not put inflection on the +8 min pad-recycle tick.",
            "delayed_surprise_s": delayed,
        },
        "reward_components": reward_block(
            ticks,
            sums,
            total,
            "Correct REJECT. total +0.80 = 0.10 + 0.42 + 0.12 + 0.10 + 0.06. Tick 6 t_us binds raster.delayed_surprise_s=480.",
        ),
        "raster": raster,
        "gate_snn": {
            "decision_window_ms": 0.64,
            "decision": "REJECT",
            "populations": [
                pop("slurry_hold", 32, 0.45, 220.0, 0.64),
                pop("dose_continue", 32, 0.8, 40.0, 0.64),
                veto("dp_trip_veto", 16, 0.7),
            ],
        },
        "meta": meta_common(
            24,
            "ruthenium-dioxide-precipitator",
            ["reject", "hil", "dp-first", "independent-lif-raster", "tick6-sidecar-bound"],
            "Teaches a HIL filter-DP-vs-pH race where cake over-trip vetoes a still-buffering dose. gate_snn.slurry_hold fires; dose_continue stays subthreshold.",
            3,
        ),
    }


def rec_119():
    delayed = 240
    ticks, sums, total = ticks_from(
        [
            (1100, 0.05, 0.03, 0.02, 0.01, 0.01),
            (6740, 0.08, 0.05, 0.03, 0.02, 0.01),
            (7120, 0.04, 0.03, 0.02, 0.02, 0.01),
            (7840, 0.12, 0.06, 0.04, 0.03, 0.02),
            (12800, 0.06, 0.03, 0.02, 0.01, 0.01),
            (240000000, 0.03, 0.02, 0.01, 0.01, 0.00),
        ]
    )
    raster = raster_block(
        window_ms=26,
        neurons=64,
        mean_rate_hz=38,
        delayed_s=delayed,
        source="thalamic-relay.target-voltage",
        target="spikenaut.policy.power-clamp",
        table=[
            {"from": "relay.v.target", "to": "policy.power_clamp", "weight": 0.70},
            {"from": "relay.p.chamber", "to": "policy.pressure_hold", "weight": 0.27},
        ],
        modulator="acetylcholine",
        tau_e_s=0.09,
        eligibility="pre_post_stdp; ACh at target-voltage win (6.740 ms) tags the power_clamp bind",
        seed=24119,
        stim_t_us=(6000, 9000),
        extra_bias_n=18,
        extra_i=0.62,
        early_ch="lif.voltage",
        late_ch="lif.clamp",
        note="Population sim scoped to this sidecar. Plant remains simulated. Neurons 0-17 carry +0.62 clamp-pathway bias; stim 6-9 ms covers the race+gate.",
        i_bias=0.86,
        i_stim_peak=2.1,
    )
    return {
        "id": "ttf-r24-119",
        "title": "ITOS-Fen IF-3 sim / Magnetron-M6: target voltage beats chamber pressure by 380 us; correct MODIFY clamps power 4.80 -> 2.20 kW",
        "state": {
            "description": "Magnetron-M6 is 40 mm into the ITO target race-track on the ITOS-Fen IF-3 simulated chamber when target voltage sits at 640 V against a 520 V arc-cap. Chamber pressure is only 0.42 Pa under the 0.80 Pa halt, so a pressure-first planner would keep 4.80 kW. The live contest is target voltage versus chamber pressure, not QCM versus residual gas. No live fab tool is in the loop.",
            "domain": "indium-tin-oxide-sputter",
            "sim_or_real": "simulated",
            "goal": "Finish the IF-3 race-track with target voltage <= 520 V, leave Ar/O2 at 18/2 sccm, and keep chamber pressure under 0.80 Pa.",
            "t0_us": 1756842524000119,
            "gate_latency_us": 1100,
            "race_window_us": 520,
            "race_window_rel_ms": [6.70, 7.22],
            "race": {
                "contenders": [
                    "v.target.v 640 V over cap",
                    "p.chamber.pa 0.42 under halt",
                ],
                "semantics": "Voltage-first latches power clamp 4.80 -> 2.20 kW; pressure-first keeps cruise on a 'still quiet' Pa model.",
                "window_derivation": "520 us = one magnetron sample period minus capacitance-manometer group delay on this 2 kHz sim bus.",
                "order_evidence_note": "Margin 380 us vs combined jitter 86 us (V 38 + P 48): 4.42x over a 2.0x trust floor. Reversing order by < 380 us inside the 520 us window would have kept 4.80 kW into a 520 V cap.",
            },
            "sensors": [
                "target voltage, 2 kHz, 38 us jitter (sim)",
                "chamber capacitance manometer, 1 kHz, 48 us jitter",
                "QCM rate, 10 Hz (context)",
                "sim plasma solver, 2 kHz (context)",
            ],
            "constraints": {
                "v_cap_V": 520.0,
                "observed_v_V": 640.0,
                "power_proposed_kW": 4.80,
                "p_obs_Pa": 0.42,
                "p_halt_Pa": 0.80,
            },
            "episode_steps": [
                "1. Magnetron-M6 40 mm into IF-3 ITO race-track; target 640 V.",
                "2. Power 4.80 kW armed; chamber 0.42 Pa.",
                "3. Solver precursor at 1.100 ms; voltage warm-start 640 V.",
                "4. Race window [6.700, 7.220] ms opens on the sim bus.",
                "5. Target voltage 640 V at 6.740 ms (winner).",
                "6. Chamber 0.42 Pa at 7.120 ms (loser by 380 us).",
                "7. Gate at 7.840 ms (winner + 1100 us): MODIFY 2.20 kW, 470 V.",
                "8. Clamp executes; next-sample 488 V < 520 cap.",
                "9. Ar/O2 held 18/2 sccm; no live tool.",
                "10. Delayed (4 min / delayed_surprise_s=240): sim survey tags the voltage-first bind on the next pass.",
            ],
        },
        "spike_events": [
            {"channel": "sim.latch.ctx", "t_rel_ms": 1.10, "amplitude": 0.41},
            {"channel": "v.target.v", "t_rel_ms": 2.94, "amplitude": 0.64},
            {"channel": "p.chamber.pa", "t_rel_ms": 4.02, "amplitude": 0.52},
            {"channel": "qcm.nm_s", "t_rel_ms": 4.88, "amplitude": 0.47},
            {"channel": "v.target.v", "t_rel_ms": 6.740, "amplitude": 1.33},
            {"channel": "p.chamber.pa", "t_rel_ms": 7.120, "amplitude": 1.08},
            {"channel": "ctrl.gate", "t_rel_ms": 7.840, "amplitude": 0.96},
            {"channel": "v.target.v", "t_rel_ms": 9.90, "amplitude": 0.78},
            {"channel": "p.chamber.pa", "t_rel_ms": 12.40, "amplitude": 0.61},
            {"channel": "ctrl.gate", "t_rel_ms": 16.10, "amplitude": 0.81},
            {"channel": "qcm.nm_s", "t_rel_ms": 19.80, "amplitude": 0.49},
            {"channel": "v.target.v", "t_rel_ms": 23.20, "amplitude": 0.58},
            {"channel": "ctrl.gate", "t_rel_ms": 25.40, "amplitude": 0.69},
        ],
        "proposed_action": {
            "name": "cruise_ito_sputter",
            "parameters": {
                "power_kW": 4.80,
                "target_V": 640.0,
                "ar_sccm": 18.0,
                "o2_sccm": 2.0,
            },
            "evidence": {
                "target_V": 640.0,
                "v_cap_V": 520.0,
                "p_obs_Pa": 0.42,
                "p_halt_Pa": 0.80,
                "race_margin_us": 380,
                "combined_jitter_us": 86,
            },
            "basis": "Planner proposes 4.80 kW: chamber 0.42 Pa looks like a quiet plasma, not a voltage-cap breach, and the 0.80 Pa halt is treated as still satisfied.",
        },
        "safety_decision": {
            "decision": "MODIFY",
            "correctness": "correct",
            "rationale": "Target voltage 640 V won by 380 us and is over the 520 V arc-cap. Holding 4.80 kW keeps loading the simulated race-track. MODIFY: power 4.80 -> 2.20 kW (predicted 470 V). Observed after clamp 488 V < 520. Ar/O2 stays 18/2 sccm. A full REJECT is not indicated: a 2.20 kW pass still deposits on this sim chamber.",
            "constraint_checked": {
                "target_V": {
                    "cap": 520.0,
                    "observed": 640.0,
                    "clamped": 470.0,
                    "observed_after_clamp": 488.0,
                },
                "power_kW": {"proposed": 4.80, "clamped": 2.20},
                "order_evidence": {"margin_us": 380, "combined_jitter_us": 86, "ratio": 4.42},
            },
        },
        "executed_action": {
            "name": "clamped_ito_sputter",
            "parameters": {
                "power_kW": 2.20,
                "target_V": 470.0,
                "ar_sccm": 18.0,
                "o2_sccm": 2.0,
            },
            "gate_effect": "MODIFY: power 4.80 -> 2.20 kW and target 640 -> 470 V. Process-correct vs the 520 V arc-cap.",
        },
        "future_outcome": {
            "summary": "Correct MODIFY held next-sample target voltage at 488 V under the 520 V cap. Delayed sim survey tags the voltage-first bind on the next pass.",
            "state_delta": {
                "magnetron": "clamp executed; 488 V < 520",
                "chamber": "0.42 Pa quiet; no arc star",
                "survey": "4 min sim race-track tag",
            },
            "surprises": [
                "Chamber pressure stayed 0.42 Pa through the pass; only target voltage saw the 640 V over-cap.",
                "Delayed (4 min / delayed_surprise_s=240): sim survey tags voltage-first on the next programmed pass.",
            ],
            "race_result": {
                "winner": "v.target.v (6.740 ms, 640 V)",
                "loser": "p.chamber.pa (7.120 ms, 0.42 Pa)",
                "margin_us": 380,
                "counterfactual_if_reversed": "Pressure-first by < 380 us inside the 520 us window would have kept 4.80 kW; simulated target would have stayed over the 520 V cap.",
            },
            "reward_inflection_t_us": 7840,
            "reward_inflection_note": "Safety and efficiency inflect at the 7.840 ms power clamp (tick t_us=7840). Do not put inflection on the +4 min survey tick.",
            "delayed_surprise_s": delayed,
        },
        "reward_components": reward_block(
            ticks,
            sums,
            total,
            "Correct MODIFY. total +0.90 = 0.38 + 0.22 + 0.14 + 0.10 + 0.06. Tick 6 t_us binds raster.delayed_surprise_s=240.",
        ),
        "raster": raster,
        "gate_snn": {
            "decision_window_ms": 0.52,
            "decision": "MODIFY",
            "populations": [
                pop("power_clamp", 48, 0.5, 260.0, 0.52),
                pop("pressure_hold", 48, 0.5, 55.0, 0.52),
                veto("v_cap_veto", 24, 0.7),
            ],
        },
        "meta": meta_common(
            24,
            "indium-tin-oxide-sputter",
            ["modify", "simulated", "voltage-first", "independent-lif-raster", "tick6-sidecar-bound"],
            "Teaches a simulated magnetron voltage-vs-pressure race: routing.table[0] to policy.power_clamp with chamber pressure as the losing hold.",
            4,
        ),
    }


def rec_120():
    delayed = 300
    ticks, sums, total = ticks_from(
        [
            (1640, 0.06, 0.04, 0.03, 0.02, 0.01),
            (4040, 0.08, 0.06, 0.03, 0.02, 0.02),
            (4320, 0.05, 0.04, 0.03, 0.02, 0.01),
            (4600, 0.14, 0.10, 0.05, 0.04, 0.02),
            (9800, 0.07, 0.05, 0.02, 0.01, 0.01),
            (300000000, 0.04, 0.03, 0.02, 0.01, 0.01),
        ]
    )
    raster = raster_block(
        window_ms=24,
        neurons=80,
        mean_rate_hz=28,
        delayed_s=delayed,
        source="thalamic-relay.ampoule-rtd",
        target="spikenaut.policy.pull-accept",
        table=[
            {"from": "relay.rtd.ampoule", "to": "policy.go_accept", "weight": 0.66},
            {"from": "relay.cam.meniscus", "to": "policy.hold_reject", "weight": 0.26},
        ],
        modulator="serotonin",
        tau_e_s=0.16,
        eligibility="pre_post_stdp; 5-HT at ampoule win (4.040 ms) tags the already-legal go_accept",
        seed=24120,
        stim_t_us=(3000, 6000),
        extra_bias_n=15,
        extra_i=0.58,
        early_ch="lif.rtd",
        late_ch="lif.accept",
        note="Population sim scoped to this sidecar. Plant remains designed. Neurons 0-14 carry +0.58 accept-pathway bias; stim 3-6 ms covers the race+gate.",
        i_bias=0.84,
        i_stim_peak=1.9,
    )
    params = {
        "pull_mm_h": 1.20,
        "ampoule_C": 612.0,
        "rotate_rpm": 4.0,
    }
    return {
        "id": "ttf-r24-120",
        "title": "Cesiumide-Fen CI-8 / Puller-Cs4: ampoule RTD 612 C beats meniscus 0.18 mm by 280 us; ACCEPT already-legal 1.20 mm/h Bridgman pull",
        "state": {
            "description": "Puller-Cs4 is 18 mm into the CsI ampoule freeze at Cesiumide-Fen CI-8 when ampoule RTD is already 612 C under a 680 C trip and meniscus camera 0.18 mm is under a 0.40 mm freeze floor. Proposed pull 1.20 mm/h is under the 1.80 mm/h envelope. The live contest is a quiet RTD versus a quiet meniscus, not a leftover soak tag versus a live-empty ampoule. Both envelopes already allow the pull.",
            "domain": "cesium-iodide-bridgman",
            "sim_or_real": "designed",
            "goal": "Complete the CI-8 Bridgman pull at 1.20 mm/h with ampoule RTD < 680 C and meniscus <= 0.40 mm, and leave the freeze front unquenched.",
            "t0_us": 1756842524000120,
            "gate_latency_us": 560,
            "race_window_us": 400,
            "race_window_rel_ms": [4.00, 4.40],
            "race": {
                "contenders": [
                    "rtd.ampoule.c 612 C under trip",
                    "cam.meniscus.mm 0.18 under freeze floor",
                ],
                "semantics": "RTD-first latches already-legal accept of 1.20 mm/h; meniscus-first would also accept, but a false 0.50 mm freeze would halt.",
                "window_derivation": "400 us = one ampoule-RTD sample period minus meniscus group delay on this 2 kHz puller bus.",
                "order_evidence_note": "Margin 280 us vs combined jitter 84 us (RTD 36 + cam 48): 3.33x over a 2.0x trust floor. Reversing order by < 280 us inside the 400 us window would still be legal unless meniscus were a false 0.50 mm freeze.",
            },
            "sensors": [
                "ampoule RTD, 2 kHz, 36 us jitter",
                "meniscus camera, 50 Hz processed / 1 kHz stamp, 48 us jitter",
                "pull encoder, 200 Hz (context)",
                "furnace zone, 10 Hz (context)",
            ],
            "constraints": {
                "ampoule_trip_C": 680.0,
                "observed_ampoule_C": 612.0,
                "meniscus_floor_mm": 0.40,
                "observed_meniscus_mm": 0.18,
                "pull_proposed_mm_h": 1.20,
                "pull_cap_mm_h": 1.80,
            },
            "episode_steps": [
                "1. Puller-Cs4 18 mm into CI-8 CsI freeze; ampoule 612 C.",
                "2. Pull 1.20 mm/h armed; meniscus 0.18 mm.",
                "3. Encoder precursor at 1.640 ms; RTD warm-start 612 C.",
                "4. Race window [4.000, 4.400] ms opens on the puller bus.",
                "5. Ampoule RTD 612 C at 4.040 ms (winner).",
                "6. Meniscus 0.18 mm at 4.320 ms (loser by 280 us).",
                "7. Gate at 4.600 ms (winner + 560 us): ACCEPT 1.20 mm/h.",
                "8. Pull completes; freeze unquenched; peak 614 C < 680 trip.",
                "9. Meniscus stays 0.17-0.18 mm.",
                "10. Delayed (5 min / delayed_surprise_s=300): log tags the already-legal bind on the next ampoule.",
            ],
        },
        "spike_events": [
            {"channel": "puller.latch.ctx", "t_rel_ms": 1.64, "amplitude": 0.44},
            {"channel": "rtd.ampoule.c", "t_rel_ms": 2.20, "amplitude": 0.59},
            {"channel": "cam.meniscus.mm", "t_rel_ms": 3.10, "amplitude": 0.53},
            {"channel": "enc.pull.um", "t_rel_ms": 3.50, "amplitude": 0.46},
            {"channel": "rtd.ampoule.c", "t_rel_ms": 4.040, "amplitude": 1.21},
            {"channel": "cam.meniscus.mm", "t_rel_ms": 4.320, "amplitude": 1.05},
            {"channel": "ctrl.gate", "t_rel_ms": 4.600, "amplitude": 0.94},
            {"channel": "rtd.ampoule.c", "t_rel_ms": 7.40, "amplitude": 0.74},
            {"channel": "cam.meniscus.mm", "t_rel_ms": 10.30, "amplitude": 0.60},
            {"channel": "ctrl.gate", "t_rel_ms": 13.90, "amplitude": 0.80},
            {"channel": "enc.pull.um", "t_rel_ms": 17.60, "amplitude": 0.48},
            {"channel": "rtd.ampoule.c", "t_rel_ms": 20.10, "amplitude": 0.55},
            {"channel": "ctrl.gate", "t_rel_ms": 23.20, "amplitude": 0.67},
        ],
        "proposed_action": {
            "name": "cruise_bridgman_pull",
            "parameters": dict(params),
            "evidence": {
                "ampoule_C": 612.0,
                "ampoule_trip_C": 680.0,
                "meniscus_mm": 0.18,
                "meniscus_floor_mm": 0.40,
                "pull_mm_h": 1.20,
                "pull_cap_mm_h": 1.80,
                "race_margin_us": 280,
                "combined_jitter_us": 84,
            },
            "basis": "Planner proposes 1.20 mm/h pull: ampoule 612 C is under the 680 C trip and meniscus 0.18 mm is under the 0.40 mm freeze floor, so both envelopes already allow the Bridgman advance.",
        },
        "safety_decision": {
            "decision": "ACCEPT",
            "correctness": "correct",
            "rationale": "Ampoule RTD 612 C won by 280 us and is under the 680 C trip. Meniscus 0.18 mm is under the 0.40 mm freeze floor. Proposed 1.20 mm/h is under the 1.80 mm/h envelope. ACCEPT: executed equals proposed.",
            "constraint_checked": {
                "ampoule_C": {"trip": 680.0, "observed": 612.0, "legal": True},
                "meniscus_mm": {"floor": 0.40, "observed": 0.18, "legal": True},
                "pull_mm_h": {"cap": 1.80, "proposed": 1.20},
                "order_evidence": {"margin_us": 280, "combined_jitter_us": 84, "ratio": 3.33},
            },
        },
        "executed_action": {
            "name": "cruise_bridgman_pull",
            "parameters": dict(params),
            "gate_effect": "ACCEPT: executed equals proposed 1.20 mm/h Bridgman pull at 612 C.",
        },
        "future_outcome": {
            "summary": "Correct ACCEPT completed the CsI pull under RTD and meniscus floors. Delayed log tags the already-legal bind on the next ampoule.",
            "state_delta": {
                "puller": "pull complete; peak 614 C < 680",
                "freeze": "unquenched",
                "log": "5 min tag on next ampoule",
            },
            "surprises": [
                "Meniscus stayed 0.17-0.18 mm through the pull; no freeze bulge.",
                "Delayed (5 min / delayed_surprise_s=300): log tags the already-legal RTD-first bind.",
            ],
            "race_result": {
                "winner": "rtd.ampoule.c (4.040 ms, 612 C under trip)",
                "loser": "cam.meniscus.mm (4.320 ms, 0.18 mm)",
                "margin_us": 280,
                "counterfactual_if_reversed": "Meniscus-first by < 280 us inside the 400 us window would still accept unless the envelope were a false 0.50 mm freeze. Both channels are inside limits.",
            },
            "reward_inflection_t_us": 4600,
            "reward_inflection_note": "Task progress inflects at the 4.600 ms ACCEPT (tick t_us=4600). Do not put inflection on the +5 min log tick.",
            "delayed_surprise_s": delayed,
        },
        "reward_components": reward_block(
            ticks,
            sums,
            total,
            "Correct ACCEPT already-legal. total +1.14 = 0.44 + 0.32 + 0.18 + 0.12 + 0.08. Tick 6 t_us binds raster.delayed_surprise_s=300.",
        ),
        "raster": raster,
        "gate_snn": {
            "decision_window_ms": 0.40,
            "decision": "ACCEPT",
            "populations": [
                pop("go_accept", 44, 0.45, 150.0, 0.40),
                pop("hold_reject", 32, 0.8, 25.0, 0.40),
                veto("ampoule_cap_veto", 16, 0.75),
            ],
        },
        "meta": meta_common(
            24,
            "cesium-iodide-bridgman",
            ["accept", "already-legal", "designed", "independent-lif-raster", "tick6-sidecar-bound"],
            "Teaches an already-legal Bridgman pull: ampoule under trip and meniscus inside limits; gate_snn.go_accept fires and hold_reject stays subthreshold.",
            5,
        ),
    }


MY_DOMAINS = {
    "cobalt-sulfate-crystallizer",
    "tellurium-dioxide-melter",
    "ruthenium-dioxide-precipitator",
    "indium-tin-oxide-sputter",
    "cesium-iodide-bridgman",
}
MY_PLANTS = (
    "Cobaltite-Fell",
    "Tellurite-Brae",
    "Ruthenate-Howe",
    "ITOS-Fen",
    "Cesiumide-Fen",
    "Basket-B4",
    "Crucible-K2",
    "Filter-F3",
    "Magnetron-M6",
    "Puller-Cs4",
)


def hidden_thoughts(obj, path=""):
    found = []
    extra = {
        "thought",
        "reasoning",
        "chain_of_thought",
        "hidden_reasoning",
        "inner_monologue",
        "scratch",
        "internal_reasoning",
        "thinking",
        "cot",
        "thoughts",
    }
    banned = set(HIDDEN_THOUGHT_KEYS) | extra
    if isinstance(obj, dict):
        for k, v in obj.items():
            child = f"{path}.{k}" if path else k
            norm = re.sub(
                r"[^a-z0-9]+",
                "_",
                re.sub(r"(?<=[a-z0-9])(?=[A-Z])", "_", str(k)).casefold(),
            ).strip("_")
            if norm in banned or "thought" in norm:
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
        if p.name.startswith("batch-r24"):
            continue
        for line in p.read_text().splitlines():
            if not line.strip():
                continue
            rec = json.loads(line)
            descs.append((rec["id"], rec["state"]["description"]))
    return descs


def occupancy_collisions():
    hits = []
    plant_re = re.compile(r"\b(" + "|".join(re.escape(p) for p in MY_PLANTS) + r")\b")
    for p in sorted(LIVE.glob("batch-r*.jsonl")):
        if p.name.startswith("batch-r24"):
            continue
        blob = p.read_text()
        for rec_line in blob.splitlines():
            if not rec_line.strip():
                continue
            rec = json.loads(rec_line)
            d = rec.get("state", {}).get("domain")
            if d in MY_DOMAINS:
                hits.append(f"domain {d} in {rec['id']}")
            found = plant_re.findall(json.dumps(rec))
            if found:
                hits.append(f"plant {found} in {rec['id']}")
            if rec.get("id", "").startswith("ttf-r24-"):
                hits.append(f"id collision {rec['id']}")
    return hits


def validate_records(records):
    errors = []
    errors.extend(occupancy_collisions())
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
    if set(domains) != MY_DOMAINS:
        errors.append(f"unexpected domains {domains}")

    sims = [r["state"]["sim_or_real"] for r in records]
    if sims.count("designed") != 3 or sims.count("simulated") != 1 or sims.count("hil") != 1:
        errors.append(f"provenance mix {sims}")
    if "real" in sims:
        errors.append("sim_or_real real")

    decisions = [(r["id"], r["safety_decision"]["decision"], r["safety_decision"]["correctness"]) for r in records]
    correct_a = sum(1 for _, d, c in decisions if d == "ACCEPT" and c == "correct")
    correct_m = sum(1 for _, d, c in decisions if d == "MODIFY" and c == "correct")
    correct_r = sum(1 for _, d, c in decisions if d == "REJECT" and c == "correct")
    wrong_r = sum(1 for _, d, c in decisions if d == "REJECT" and c == "incorrect")
    wrong_a = sum(1 for _, d, c in decisions if d == "ACCEPT" and c == "incorrect")
    if (correct_a, correct_m, correct_r, wrong_r) != (1, 2, 1, 1):
        errors.append(f"gate mix {decisions}")
    if wrong_a:
        errors.append("wrong-ACCEPT present")

    ids = [r["id"] for r in records]
    if ids != [f"ttf-r24-{n}" for n in range(116, 121)]:
        errors.append(f"ids {ids}")

    totals = [r["reward_components"]["total"] for r in records]
    if all(t > 0 for t in totals):
        errors.append("all-positive totals")
    if records[0]["reward_components"]["total"] >= 0:
        errors.append("partnered-neg not negative")

    wr_table = records[1]["raster"]["routing"]["table"]
    if any(row.get("to") == "policy.go_accept" and row.get("weight", 0) > 0 for row in wr_table):
        errors.append("wrong-reject has positive go_accept weight")

    for rec in records:
        where = rec["id"]
        if rec["meta"]["round"] != 24:
            errors.append(f"{where} meta.round")
        if rec["gate_snn"]["decision"] != rec["safety_decision"]["decision"]:
            errors.append(f"{where} gate_snn mismatch")
        ht = hidden_thoughts(rec)
        if ht:
            errors.append(f"{where} thought keys {ht}")
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
        if rec["id"] == "ttf-r24-116" and not (0 <= inf <= win_us):
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
        if rec["safety_decision"]["correctness"] == "incorrect":
            if "recovery" not in rec["future_outcome"]:
                errors.append(f"{where} missing recovery")
            if rec["meta"].get("supervisor_error_type") != "wrong-reject":
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
        blob = json.dumps(rec)
        if '"sim_or_real": "real"' in blob or '"sim_or_real":"real"' in blob:
            errors.append(f"{where} nested real")
        if rec["meta"]["rights"]["intended_use"] != "research_only":
            errors.append(f"{where} rights")
        if rec["meta"].get("training_ready"):
            errors.append(f"{where} training_ready")
        for ch in rec["spike_events"]:
            if len(ch["channel"]) > 32:
                errors.append(f"{where} channel too long {ch['channel']}")
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
    worst = f"{worst_prior[0]} vs {worst_prior[1]}" if worst_prior else "n/a"
    return f"""# Thalamic Trajectory Factory — NOTES-r24

- Factory: `thalamic-trajectory-factory`
- Run label: `2026-09-02-final-heavy`
- Generator: `grok-4.6`
- Channel: SuperGrok Heavy consumer chat (RM-793 research-only)
- Quota: 5
- Quality: Q=5
- IDs: `ttf-r24-116` … `ttf-r24-120`
- Domains this batch: `cobalt-sulfate-crystallizer`, `tellurium-dioxide-melter`, `ruthenium-dioxide-precipitator`, `indium-tin-oxide-sputter`, `cesium-iodide-bridgman`

These five domain slugs sit outside the prompt 8-pool and outside live-tree occupancy plus staged `/tmp/ttf-r24` IDs `ttf-r24-136`…`140` (electrolyzer / HVDC / autoclave / solar-trough / OLTC). All five plants are invented (Cobaltite-Fell, Tellurite-Brae, Ruthenate-Howe, ITOS-Fen, Cesiumide-Fen). Do not restack prior TTF plants. Scratch r24 wrong-modify mix is not restacked.

## Batch map

| id | domain | decision | correctness | sim_or_real | total | edge |
|----|--------|----------|-------------|-------------|-------|------|
| ttf-r24-116 | cobalt-sulfate-crystallizer | MODIFY | correct | designed | **-0.47** | process-correct feed clamp; PTFE scraper shear inside 42 ms raster; independent LIF |
| ttf-r24-117 | tellurium-dioxide-melter | REJECT | **incorrect (wrong-reject / stale-setpoint-swapped-tag)** | designed | -0.36 | live 612 C inside 540-720 C; sibling soak SP 812 C bound as live PV |
| ttf-r24-118 | ruthenium-dioxide-precipitator | REJECT | correct | hil | +0.80 | filter DP 3.80 bar beats pH 6.40; hold dose |
| ttf-r24-119 | indium-tin-oxide-sputter | MODIFY | correct | simulated | +0.90 | target 640 V > 520 cap; power 4.80 -> 2.20 kW |
| ttf-r24-120 | cesium-iodide-bridgman | ACCEPT | correct | designed | +1.14 | ampoule 612 C vs meniscus 0.18 mm; proposed 1.20 mm/h already legal |

Gate mix: 1 ACCEPT, 2 correct MODIFY (one partnered-neg, in-window), 1 correct REJECT, 1 incorrect REJECT (stale-setpoint / swapped-tag). Provenance: designed×3, simulated×1, hil×1 (Ruthenate-Howe RH-HIL pad). Intra-batch Jaccard on `state.description` {max_intra:.3f} (top pairs {intra_s}). All < 0.4. Max Jaccard vs prior committed rounds in this factory dir {max_prior:.3f} ({worst}). Totals not all-positive (116 −0.47, 117 −0.36).

## Wrong-reject

**ttf-r24-117** is the mandated incorrect gate (`safety_decision.correctness=incorrect`, `meta.supervisor_error_type=wrong-reject`). Round 24 is even, so wrong-reject (odd rounds host wrong-modify). This is **stale-setpoint / swapped-tag**: live RTD and pyrometer already legal; supervisor binds a leftover sibling-furnace soak setpoint (812 C) as if it were this crucible's live PV. Not r02 humidity-as-trip, not r04 px-as-si, not r22 stale-interlock / ghost occupancy, not r42 burst-mode-status-as-EU, not original r42 leftover-SP-as-trip, not r62 leftover-kelvin-offset, not r64 decade-shift, not r66 NAMUR fail-high, not r68 open-TC burnout, not r70 3-wire RTD lead-ohms-as-C, not a wrong-ACCEPT. Do not emit a wrong-ACCEPT.

Tellurite-Brae TB-5 / Crucible-K2 reads live RTD **612 C** against a published **540 C** floor and **720 C** cap. Optical pyrometer **598 C** is also legal. A leftover soak setpoint from sibling TeO2-2 still prints **812 C** (`setpoint_tag_is_live=false`, `swapped_tag=true`). Sidecar arithmetic `540 < 612 < 720` is true. A timely ACCEPT at `t_gate_us=6200` keeps 18 kW. A weak supervisor binds 812 C as live PV and REJECT-holds power **18 -> 0**. Live RTD stays **612 C**. Convictable without TeO2 kinetics: `evidence.floor_C < evidence.live_C < evidence.cap_C`, `evidence.setpoint_tag_is_live == false`, `executed_action.bind_stale_setpoint == true` and `power_kW == 0.0`, `raster.routing.table` sends `relay.sp.stale` → `policy.hold_reject` (weight 0.74) with no positive weight to `policy.go_accept`, and `gate_snn` has `hold_reject` above threshold while `go_accept` is not. Recovery: ACCEPT 18 kW at t_gate; leave the sibling soak SP unbound as this crucible's PV. Cost: 11 min missed TeO2 window (`abort_s=660`).

## Partnered-negative in-window (116)

**ttf-r24-116** is the partnered negative: process-correct MODIFY (feed held 0.90 t/h; liquor 59.8 C <= 62.0 cap) while the world still charges. Safety −0.62 prices the PTFE scraper shear at **23.600 ms**; `task_progress` stays +0.30 because the clamp completed. Inflection `t_us=23600` is tick 5 and is **inside** the 42 ms raster (`23600 ≤ 42000`). Named un-netted loss: 12 min basket isolate (`abort_s=720`). Not folded into process heads.

Independent LIF (labeled sidecar sim on every record this round): `state.sim_or_real` remains `designed` on 116. `raster.excerpt_source=independent_lif`, `raster.sim_scope=sidecar_only`, `raster.lif` seed 24116, stim `[22000, 25600]`. Excerpt is membrane crossings (`lif.clamp` early vs `lif.shear` 22–25.6 ms), not a 1:1 remap of `spike_events`. `meta.tags` include `independent-lif-raster` and `sidecar-sim-only`. 117–120 also carry independent LIF excerpts (seeds 24117–24120).

## Reward formula and tick reconciliation

Declared aggregation on every record:

`total = task_progress + safety + efficiency + coherence + exploration`

Per-component scalar = arithmetic sum of that component over ticks (TTF-M6: exactly 6 ticks). Tick 6 is bound to a published sidecar (`abort_s`, `survey_s`) via `future_outcome.delayed_surprise_s` and is strictly after the raster window. Inflection `t_us` is an actual tick.

| id | ticks | tp | saf | eff | coh | exp | total | inflection tick |
|----|-------|----|-----|-----|-----|-----|-------|-----------------|
{chr(10).join(rew_rows)}

Tick-6 sidecar bind: 116 `abort_s=720`, 117 `abort_s=660`, 118 `abort_s=480`, 119 `survey_s=240`, 120 `survey_s=300`.

## Raster / energy (Loihi-2 4-core, 23 pJ/spike)

| id | domain | n | rate Hz | window_ms | spikes | energy_pJ | energy_uJ |
|----|--------|---|---------|-----------|--------|-----------|-----------|
{chr(10).join(ras_rows)}

`spikes = round(n × rate × window_s)`. Every record carries `gate_snn` whose `decision` matches the safety gate; populations that declare rate+spikes meet the same ±1 budget against `decision_window_s`. `routing.third_factor` has modulator (NA / ACh / DA / 5-HT / octopamine), `tau_e_s`/`tau_e_ms` pair, and eligibility. Excerpt same-neuron gap ≥ 1000 µs; spike trains same-channel refractory ≥ 0.8 ms. Excerpts are independent LIF membrane crossings, not a 1:1 remap of `spike_events` times (overlap < 0.8).

## Gaps this round fixes vs r23 / r70 NOTES

r23 (odd) hosted wrong-modify on 8-pool plants. This even round leaves the 8-pool, plants five unused chemical domains, and densifies the **stale-setpoint / swapped-tag** wrong-REJECT subclass called out after r04/r62/r70. Independent LIF is labeled on all five records. Partnered-neg sits on a crystallizer scraper shear (not r01 surgical CSF / r23 Descemet). HIL sits on a RuO2 filter pad (not r23 Kelp-Brae wet stand). Wrong-ACCEPT remains absent (guard).

## Local checks (this window)

Generator stdout: self_check (Jaccard, refractory, race, spike budget, energy, tick6 bind, gate_snn budget, rights). Then `json.loads` every line, `validate_run.check_line`, `raster_status`, `verify_batch_for_frontier(strict=True)`, `spike_probe.py --strict`.

Never `training_ready`. Never `sim_or_real=real`. Never wrong-ACCEPT. Never thought keys. Create-only into the assigned live path; did not clobber 2026-08-17 / 2026-08-30; did not overwrite existing r24 files (c-suffix if occupied).

## Residual weaknesses (honest)

1. Five domain slugs leave the prompt's 8-item pool; a later round that must stay inside the pool will have to rotate sit-outs instead.
2. Wrong-ACCEPT still absent (guard).
3. Tick-6 sidecar bind is standing machinery (r14+), not a new class.
4. 117 swapped-tag is a false-positive REJECT; a later even round could densify leftover-SP-echo-as-PV if that subclass is still open.
5. 118 HIL dummy oxalate never tears; a partnered HIL near-miss where REJECT is correct but a delayed cake slump still occurs would densify the HIL class.

## Next densification target

Labeled LIF on a second world-charge, or an ISI histogram sidecar on the ACCEPT. Remaining unused wrong-REJECT subclasses include **SP-echo-as-PV** if not already planted in a later even round. Wrong-ACCEPT remains structurally absent until a prompt amendment.

Novel coverage: 23.5%
"""


def exclusive_write(path: Path, data: str):
    flags = os.O_CREAT | os.O_EXCL | os.O_WRONLY
    fd = os.open(str(path), flags, 0o644)
    with os.fdopen(fd, "w", encoding="utf-8") as f:
        f.write(data)


def main():
    records = [rec_116(), rec_117(), rec_118(), rec_119(), rec_120()]
    errors, max_intra, max_prior, worst_prior, intra = validate_records(records)
    if errors:
        print("SELF-CHECK FAIL", file=sys.stderr)
        for e in errors:
            print(" ", e, file=sys.stderr)
        sys.exit(1)

    staging = Path("/tmp/ttf-r24-live")
    staging.mkdir(parents=True, exist_ok=True)
    jsonl = "\n".join(json.dumps(r, ensure_ascii=False, separators=(",", ":")) for r in records) + "\n"
    notes = notes_text(records, max_intra, max_prior, worst_prior, intra)
    (staging / "batch-r24.jsonl").write_text(jsonl, encoding="utf-8")
    (staging / "NOTES-r24.md").write_text(notes, encoding="utf-8")

    counts, findings, blocked = verify_batch_for_frontier(staging / "batch-r24.jsonl", strict=True)
    print("verify_batch", counts, "blocked", blocked)
    if findings:
        print("findings", findings)
    if blocked:
        sys.exit(2)

    from spike_probe import load_rasters

    rasters, problems = load_rasters([staging / "batch-r24.jsonl"])
    print("spike_probe rasters", len(rasters), "problems", problems)
    if problems:
        sys.exit(3)
    if len(rasters) != 5:
        print("expected 5 rasters", len(rasters))
        sys.exit(3)

    live_batch = LIVE / "batch-r24.jsonl"
    live_notes = LIVE / "NOTES-r24.md"
    if live_batch.exists() or live_notes.exists():
        live_batch = LIVE / "batch-r24c.jsonl"
        live_notes = LIVE / "NOTES-r24c.md"
        if live_batch.exists() or live_notes.exists():
            print("collision: r24 and r24c exist", file=sys.stderr)
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
