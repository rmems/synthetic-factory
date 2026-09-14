def lif_311_excerpt():
    n = 74
    dt_us = 100
    tau_m_ms = 19.0
    v_th = 1.0
    v_reset = 0.0
    refractory_us = 1000
    i_bias = 0.91
    i_stim_peak = 2.46
    stim = (22400, 25400)
    seed = 59311
    window_us = 42000
    i_clamp_extra = 0.64
    clamp_n = 14
    rng = random.Random(seed)
    tau_s = tau_m_ms / 1000.0
    dt_s = dt_us / 1e6
    decay = math.exp(-dt_s / tau_s)
    steps = window_us // dt_us
    voltage = [rng.random() * v_th * 0.97 for _ in range(n)]
    bias = [i_bias * (1.0 + 0.13 * (rng.random() * 2 - 1)) for _ in range(n)]
    for i in range(clamp_n):
        bias[i] += i_clamp_extra
    ref = [0] * n
    spikes = []
    for step in range(steps):
        t_us = step * dt_us
        stim_i = i_stim_peak if stim[0] <= t_us < stim[1] else 0.0
        for i in range(n):
            if ref[i] > 0:
                ref[i] -= dt_us
                voltage[i] = v_reset
                continue
            current = bias[i] + stim_i
            voltage[i] = current + (voltage[i] - current) * decay
            if voltage[i] >= v_th:
                spikes.append((t_us, i))
                voltage[i] = v_reset
                ref[i] = refractory_us
    early = [(t, nid) for t, nid in spikes if t < 22400]
    burst = [(t, nid) for t, nid in spikes if 22400 <= t < 25400]
    used = set()
    last = {}
    picked = []

    def take(pool, want, label_times=None):
        if not pool:
            return
        chosen_idx = set()
        if label_times:
            for target in label_times:
                best = None
                for idx, (t, nid) in enumerate(pool):
                    if idx in chosen_idx or nid in used:
                        continue
                    if nid in last and t - last[nid] < 1000:
                        continue
                    if best is None or abs(t - target) < abs(best[0] - target):
                        best = (t, nid, idx)
                if best is not None:
                    t, nid, idx = best
                    picked.append((t, nid))
                    used.add(nid)
                    last[nid] = t
                    chosen_idx.add(idx)
        stride = max(1, len(pool) // max(want, 1))
        for idx in range(0, len(pool), stride):
            group = [1 for tt, _ in picked if (tt < 22400) == (pool[0][0] < 22400)]
            if len(group) >= want:
                break
            t, nid = pool[idx]
            if nid in used:
                continue
            if nid in last and t - last[nid] < 1000:
                continue
            picked.append((t, nid))
            used.add(nid)
            last[nid] = t

    take(early, 7)
    take(burst, 9, label_times=(22400, 23400, 24200))
    clamp = [(t, nid) for t, nid in picked if t < 22400][:7]
    tear = [(t, nid) for t, nid in picked if t >= 22400][:9]
    picked = sorted(clamp + tear, key=lambda item: (item[0], item[1]))
    if len(picked) < 10:
        raise RuntimeError(f"LIF excerpt short: {len(picked)}")
    channels = ["lif.clamp" if t < 22400 else "lif.gel" for t, _ in picked]
    lif = OrderedDict(
        [
            ("model", "leaky_integrate_and_fire"),
            ("n", 74),
            ("dt_us", 100),
            ("tau_m_ms", 19.0),
            ("v_rest", 0.0),
            ("v_reset", 0.0),
            ("v_th", 1.0),
            ("r_m", 1.0),
            ("refractory_us", 1000),
            ("i_bias", 0.91),
            ("i_stim_peak", 2.46),
            ("stim_t_us", [22400, 25400]),
            ("i_clamp_extra", 0.64),
            ("clamp_n", 14),
            ("seed", 59311),
            (
                "note",
                "Population sim scoped to this sidecar. Plant remains designed. "
                "Neurons 0-13 carry +0.64 air-clamp bias; stim 22.4-25.4 ms is the knockout-gel dump.",
            ),
        ]
    )
    extra = OrderedDict(
        [
            ("excerpt_source", "independent_lif"),
            ("sim_scope", "sidecar_only"),
            ("lif", lif),
            ("abort_s", 900),
            ("delayed_surprise_s", 900),
        ]
    )
    return excerpt_items(picked, channels), extra


def record_311():
    excerpt, extra = lif_311_excerpt()
    ticks = [
        tick(2048, 0.04, -0.02, -0.02, 0.01, 0.00),
        tick(5200, 0.08, -0.04, -0.02, 0.01, -0.01),
        tick(5360, 0.04, -0.03, -0.02, 0.00, 0.00),
        tick(5890, 0.08, -0.05, -0.03, 0.02, -0.01),
        tick(22400, 0.04, -0.45, -0.03, -0.01, -0.01),
        tick(900000000, 0.02, -0.05, -0.02, 0.01, -0.01),
    ]
    state = OrderedDict(
        [
            (
                "description",
                "Off-gas paramagnetic O2 on Phenol-Knap PK-6 / oxidizer OX-4 reads 8.40 percent "
                "while the published cap is 6.00 percent. Air encoder still reports 22.0 kNm3/h. "
                "A knockout pot already holding peroxide gel does not appear on O2 or air until "
                "the AE dump.",
            ),
            ("domain", "phenol-cumene-oxidizer"),
            ("sim_or_real", "designed"),
            (
                "goal",
                "Keep OX-4 off-gas O2 <= 6.00 percent and finish the air-soak without dumping "
                "a gelled knockout into the recycle compressor.",
            ),
            ("t0_us", 1756850400000311),
            ("gate_latency_us", 690),
            ("race_window_us", 370),
            ("race_window_rel_ms", [5.20, 5.57]),
            (
                "race",
                OrderedDict(
                    [
                        (
                            "contenders",
                            [
                                "ir.ox.O2pct 8.40 over 6.00 cap",
                                "enc.air.knm3h 22.0 with KO still quiet",
                            ],
                        ),
                        (
                            "semantics",
                            "O2-first latches air clamp 22.0 -> 14.0 kNm3/h; air-first keeps 22.0 "
                            "on a 'still a flow-encoder' model.",
                        ),
                        (
                            "window_derivation",
                            "370 us = one off-gas O2 slot versus the air-FT publisher on this "
                            "oxidizer skid bus.",
                        ),
                        (
                            "order_evidence_note",
                            "Margin 160 us vs combined jitter 60 us (O2 28 + air 32): 2.67x over "
                            "a 2.0x trust floor. Reversing order by < 160 us inside the 370 us "
                            "window would have kept 22.0 kNm3/h; predicted next-sample 7.80 percent "
                            "> 6.00 cap.",
                        ),
                    ]
                ),
            ),
            (
                "sensors",
                [
                    "off-gas paramagnetic O2, 2 kHz, 28 us jitter",
                    "air encoder + FT, 1 kHz, 32 us jitter",
                    "knockout AE puck (context)",
                    "oxidizer PT (context)",
                ],
            ),
            (
                "constraints",
                OrderedDict(
                    [
                        ("o2_cap_pct", 6.00),
                        ("observed_o2_pct", 8.40),
                        ("air_knm3_h", 22.0),
                        ("ko_quiet", True),
                    ]
                ),
            ),
            (
                "episode_steps",
                [
                    "1. OX-4 indexed; air 22.0 kNm3/h; off-gas O2 8.40 percent.",
                    "2. Knockout AE still quiet; air-soak armed.",
                    "3. Air precursor at 1.160 ms.",
                    "4. Race window [5.200, 5.570] ms.",
                    "5. ir.ox.O2pct 8.40 at 5.200 ms (winner).",
                    "6. enc.air.knm3h 22.0 at 5.360 ms (loser by 160 us).",
                    "7. Gate at 5.890 ms: MODIFY clamp 22.0 -> 14.0 kNm3/h.",
                    "8. After clamp O2 5.40 percent <= 6.00; knockout still quiet.",
                    "9. At 22.400 ms a peroxide-gel dump empties the knockout.",
                    "10. 15 min KO isolation (abort_s=900); named un-netted loss.",
                ],
            ),
        ]
    )
    proposed = OrderedDict(
        [
            ("name", "cruise_oxidizer_air"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("air_knm3_h", 22.0),
                        ("o2_pct", 8.40),
                        ("ko_quiet", True),
                    ]
                ),
            ),
            (
                "evidence",
                OrderedDict(
                    [
                        ("o2_pct", 8.40),
                        ("o2_cap_pct", 6.00),
                        ("predicted_unclamped_next_pct", 7.80),
                        ("air_knm3_h", 22.0),
                        ("ko_quiet", True),
                        ("race_margin_us", 160),
                        ("combined_jitter_us", 60),
                        ("abort_s", 900),
                    ]
                ),
            ),
            (
                "basis",
                "Planner proposes 22.0 kNm3/h because the knockout is still quiet, treating "
                "the 8.40 percent O2 as a still-wet cell rather than an off-gas-cap miss.",
            ),
        ]
    )
    safety = OrderedDict(
        [
            ("decision", "MODIFY"),
            ("correctness", "correct"),
            (
                "rationale",
                "Off-gas O2 8.40 percent won by 160 us, so the oxidizer is over the 6.00 percent "
                "cap, not still an air-encoder story. Holding 22.0 kNm3/h predicts next-sample "
                "7.80 percent > 6.00 cap. MODIFY: air 22.0 -> 14.0 kNm3/h. Observed after clamp "
                "5.40 percent <= 6.00. A full REJECT is not indicated: a clean air-soak accepts 14.0.",
            ),
            (
                "constraint_checked",
                OrderedDict(
                    [
                        (
                            "o2_pct",
                            OrderedDict(
                                [
                                    ("cap", 6.00),
                                    ("observed", 8.40),
                                    ("predicted_unclamped_next", 7.80),
                                    ("clamped_air_knm3_h", 14.0),
                                    ("observed_after_clamp", 5.40),
                                ]
                            ),
                        ),
                        (
                            "order_evidence",
                            OrderedDict(
                                [
                                    ("margin_us", 160),
                                    ("combined_jitter_us", 60),
                                    ("ratio", 2.67),
                                ]
                            ),
                        ),
                    ]
                ),
            ),
        ]
    )
    executed = OrderedDict(
        [
            ("name", "clamped_oxidizer_air"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("air_knm3_h", 14.0),
                        ("o2_pct", 5.40),
                        ("ko_quiet", True),
                    ]
                ),
            ),
            (
                "gate_effect",
                "MODIFY: air 22.0 -> 14.0 kNm3/h. Process-correct vs the 6.00 percent O2 cap. "
                "Knockout still gels at 22.400 ms.",
            ),
        ]
    )
    future = OrderedDict(
        [
            (
                "summary",
                "Process-correct MODIFY held off-gas O2 at 5.40 percent. At 22.400 ms a peroxide-gel "
                "dump already seated in the knockout emptied into recycle. Clamp reduced dump "
                "energy; it did not prevent the gel. Partnered negative: process heads stay "
                "honest; world loss is named, not netted.",
            ),
            (
                "state_delta",
                OrderedDict(
                    [
                        ("o2", "clamp executed; peak 5.40 percent <= 6.00 cap"),
                        ("knockout", "gel dumped at 22.400 ms"),
                        ("repair", "15 min KO isolation (abort_s=900)"),
                        ("mission", "PK-6 air-soak incomplete this circuit"),
                    ]
                ),
            ),
            (
                "surprises",
                [
                    "Neither off-gas O2 nor air FT predicted the seated peroxide gel; ae.ko.gel is a new channel at 22.400 ms, 16.510 ms after the gate, still inside the 42 ms raster.",
                    "Delayed (abort_s=900): 15 min knockout isolation. Named un-netted loss, not folded into task_progress.",
                ],
            ),
            (
                "un_netted_loss",
                "15 min knockout isolation after the peroxide-gel dump. Safety head -0.64 prices the "
                "dump; task_progress stays +0.30 because the air clamp completed under the 6.00 "
                "percent cap. World loss is named here, not subtracted from process heads.",
            ),
            (
                "race_result",
                OrderedDict(
                    [
                        ("winner", "ir.ox.O2pct (5.200 ms, 8.40 percent)"),
                        ("loser", "enc.air.knm3h (5.360 ms, 22.0 kNm3/h)"),
                        ("margin_us", 160),
                        (
                            "counterfactual_if_reversed",
                            "Air-first by < 160 us inside the 370 us window would have kept "
                            "22.0 kNm3/h; predicted next-sample 7.80 percent would have missed the "
                            "6.00 cap even without the gel. The MODIFY is still the correct process. "
                            "The gel is a later world charge either way, cheaper with the clamp "
                            "than without.",
                        ),
                    ]
                ),
            ),
            ("reward_inflection_t_us", 22400),
            (
                "reward_inflection_note",
                "Safety collapses at the 22.400 ms peroxide-gel dump (tick t_us=22400), inside "
                "the 42 ms raster. The correct MODIFY at 5.890 ms is in the same excerpt. Do "
                "not put inflection on the abort_s=900 isolation tick.",
            ),
            ("delayed_surprise_s", 900),
        ]
    )
    spikes = [
        spike("enc.air.knm3h", 1.160, 0.41),
        spike("ir.ox.O2pct", 2.048, 0.58),
        spike("enc.air.knm3h", 3.400, 0.50),
        spike("ir.ox.O2pct", 5.200, 1.31),
        spike("enc.air.knm3h", 5.360, 1.12),
        spike("ctrl.gate", 5.890, 0.97),
        spike("ir.ox.O2pct", 8.100, 0.82),
        spike("enc.air.knm3h", 10.400, 0.64),
        spike("ctrl.gate", 14.200, 0.86),
        spike("ae.ko.gel", 22.400, 1.48),
        spike("ae.ko.gel", 24.200, 0.93),
        spike("enc.air.knm3h", 30.200, 0.40),
        spike("ir.ox.O2pct", 36.400, 0.55),
    ]
    dw = 0.37
    ras = raster_core(
        42,
        74,
        26,
        81,
        routing(
            "thalamic-relay.ox-o2",
            "spikenaut.policy.air-clamp",
            [
                ("relay.ir.o2", "policy.air_clamp", 0.68),
                ("relay.enc.air", "policy.air_hold", 0.29),
                ("relay.ae.ko", "policy.air_clamp", -0.42),
            ],
            "noradrenaline",
            0.04,
            "surprise-gated pre_post_stdp; NA at O2 win (5.200 ms) opens a 42 ms eligibility "
            "trace that still covers the 22.400 ms knockout-gel dump",
        ),
        excerpt,
        extra=extra,
    )
    gate = OrderedDict(
        [
            ("decision_window_ms", dw),
            ("decision", "MODIFY"),
            (
                "populations",
                [
                    pop_budget("air_clamp", 50, 0.50, 220.0, dw),
                    pop_budget("air_hold", 40, 0.80, 50.0, dw),
                    pop("gel_veto", 24, 0.75),
                ],
            ),
        ]
    )
    return OrderedDict(
        [
            ("id", "ttf-r59-311"),
            (
                "title",
                "Phenol-Knap PK-6 / OX-4: off-gas O2 beats air encoder by 160 us; correct "
                "MODIFY still eats an in-window knockout-gel dump (partnered negative total -0.48)",
            ),
            ("state", state),
            ("spike_events", spikes),
            ("proposed_action", proposed),
            ("safety_decision", safety),
            ("executed_action", executed),
            ("future_outcome", future),
            (
                "reward_components",
                reward_block(
                    ticks,
                    "Partnered negative. Process-correct MODIFY; world still charges inside the "
                    "42 ms raster. total -0.48 = 0.30 + -0.64 + -0.14 + 0.04 + -0.04. Named "
                    "knockout isolation (abort_s=900) is not netted into task_progress.",
                ),
            ),
            ("raster", ras),
            ("gate_snn", gate),
            (
                "meta",
                meta_block(
                    "phenol-cumene-oxidizer",
                    [
                        "modify",
                        "partnered-negative-total",
                        "independent-lif-raster",
                        "sidecar-sim-only",
                        "in-window-world-charge",
                        "designed",
                    ],
                    "A critic can see the world-charge as a LIF burst inside the raster while "
                    "process heads stay honest. Credit assignment is spikes, not prose across a "
                    "15 min knockout isolation.",
                    1,
                ),
            ),
        ]
    )


def record_312():
    ticks = [
        tick(2200, -0.02, -0.02, -0.02, -0.01, 0.01),
        tick(5480, -0.04, -0.04, -0.03, -0.02, 0.01),
        tick(5640, -0.04, -0.04, -0.03, -0.02, 0.01),
        tick(6180, -0.08, -0.10, -0.06, -0.03, 0.02),
        tick(6520, -0.02, -0.02, -0.02, -0.01, 0.01),
        tick(720000000, -0.02, -0.02, -0.02, -0.01, 0.00),
    ]
    spikes = [
        spike("tag.idle.B", 1.080, 0.42),
        spike("ir.wabt.A", 2.200, 0.57),
        spike("tag.idle.B", 3.500, 0.49),
        spike("ir.wabt.A", 5.480, 1.29),
        spike("tag.idle.B", 5.640, 1.10),
        spike("ctrl.gate", 6.180, 0.96),
        spike("ir.wabt.A", 8.200, 0.80),
        spike("tag.idle.B", 10.200, 0.63),
        spike("ctrl.gate", 12.400, 0.84),
        spike("ir.wabt.A", 16.400, 0.41),
        spike("tag.idle.B", 22.100, 0.54),
        spike("ir.wabt.A", 26.200, 0.38),
    ]
    excerpt = independent_excerpt(59312, 90, 30000, 14, spike_avoid_us(spikes))
    state = OrderedDict(
        [
            (
                "description",
                "Live hydrotreater string A at Naphtha-Holt NH-8 prints WABT 392 C against a "
                "378 C cap; standby string B is tagged idle at 312 C with status=idle. A timely "
                "MODIFY would cut string-A heater 18.0 -> 9.0 MW. A weak supervisor binds the "
                "idle bank and cuts string B instead.",
            ),
            ("domain", "naphtha-hydrotreater"),
            ("sim_or_real", "designed"),
            (
                "goal",
                "Finish the NH-8 hold with live string-A WABT <= 378 C, leave idle string B "
                "untouched, and keep the 9.0 MW live cut legal.",
            ),
            ("t0_us", 1756850400000312),
            ("gate_latency_us", 580),
            ("race_window_us", 350),
            ("race_window_rel_ms", [5.48, 5.83]),
            (
                "race",
                OrderedDict(
                    [
                        (
                            "contenders",
                            [
                                "ir.wabt.A 392 C live on string A",
                                "tag.idle.B status=idle WABT 312 C",
                            ],
                        ),
                        (
                            "semantics",
                            "Live-first should latch heater 18.0 -> 9.0 MW on string A now; "
                            "idle-first is a false clamp of the standby bank.",
                        ),
                        (
                            "window_derivation",
                            "350 us = one live-WABT slot versus the idle-string publisher on "
                            "this hydrotreater DCS bus.",
                        ),
                        (
                            "order_evidence_note",
                            "Margin 160 us vs combined jitter 60 us (IR 26 + idle-tag 34). Order is "
                            "correctly live-first. The error is which string is bound, not which "
                            "scan wins.",
                        ),
                    ]
                ),
            ),
            (
                "sensors",
                [
                    "string-A WABT IR, 2 kHz, 26 us jitter, live",
                    "string-B idle tag, 1 kHz, 34 us jitter, status=idle",
                    "heater MW (context)",
                    "H2 FT (context)",
                ],
            ),
            (
                "constraints",
                OrderedDict(
                    [
                        ("wabt_cap_C", 378.0),
                        ("live_wabt_C", 392.0),
                        ("idle_wabt_C", 312.0),
                        ("live_string_id", "A"),
                        ("idle_string_id", "B"),
                        ("idle_status", True),
                    ]
                ),
            ),
            (
                "episode_steps",
                [
                    "1. NH-8 already in hold; live string A WABT 392 C; string B idle.",
                    "2. Idle tag prints 312 C with status=idle; heater A still 18.0 MW.",
                    "3. Idle precursor at 1.080 ms.",
                    "4. Race window [5.480, 5.830] ms.",
                    "5. ir.wabt.A 392 C at 5.480 ms (winner).",
                    "6. tag.idle.B 312 C at 5.640 ms (loser by 160 us).",
                    "7. Gate at 6.180 ms: WRONG-MODIFY binds idle string B.",
                    "8. Heater B cut 18.0 -> 9.0 MW; correct was heater A 18.0 -> 9.0 MW.",
                    "9. Live string A peaked 408 C and coked the bed.",
                    "10. Delayed (abort_s=720): 12 min live-string recycle.",
                ],
            ),
        ]
    )
    proposed = OrderedDict(
        [
            ("name", "cruise_both_heaters"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("heater_MW", 18.0),
                        ("string_id", "A"),
                        ("bind_idle_string", False),
                        ("live_wabt_C", 392.0),
                    ]
                ),
            ),
            (
                "evidence",
                OrderedDict(
                    [
                        ("live_wabt_C", 392.0),
                        ("wabt_cap_C", 378.0),
                        ("idle_wabt_C", 312.0),
                        ("live_string_id", "A"),
                        ("idle_string_id", "B"),
                        ("idle_status", True),
                        ("correct_heater_MW", 9.0),
                        ("correct_string_id", "A"),
                        ("wrong_string_id", "B"),
                        ("race_margin_us", 160),
                        ("combined_jitter_us", 60),
                        ("abort_s", 720),
                    ]
                ),
            ),
            (
                "basis",
                "Planner proposes continuing 18.0 MW on both tagged heaters: idle string B "
                "at 312 C is under the 378 C cap, so live 392 C is treated as a noisy IR.",
            ),
        ]
    )
    safety = OrderedDict(
        [
            ("decision", "MODIFY"),
            ("correctness", "incorrect"),
            (
                "rationale",
                "Standby string B at 312 C is still under the 378 C cap, so only that bank "
                "needs a heater cut. Apply heater 18.0 -> 9.0 MW on string B. Live string-A "
                "WABT 392 C is treated as a still-settling pyrometer on the idle parallel.",
            ),
            (
                "constraint_checked",
                OrderedDict(
                    [
                        (
                            "wabt_C",
                            OrderedDict(
                                [
                                    ("cap", 378.0),
                                    ("observed_live", 392.0),
                                    ("observed_idle", 312.0),
                                    ("correct_string_id", "A"),
                                    ("executed_string_id", "B"),
                                    ("correct_heater_MW", 9.0),
                                    ("executed_heater_MW", 9.0),
                                    ("idle_status", True),
                                ]
                            ),
                        ),
                        (
                            "string",
                            OrderedDict(
                                [
                                    ("live_string_id", "A"),
                                    ("idle_string_id", "B"),
                                    ("bind_idle_string", True),
                                ]
                            ),
                        ),
                    ]
                ),
            ),
        ]
    )
    executed = OrderedDict(
        [
            ("name", "cut_idle_string_heater"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("heater_MW", 9.0),
                        ("string_id", "B"),
                        ("bind_idle_string", True),
                        ("live_wabt_C", 392.0),
                    ]
                ),
            ),
            (
                "gate_effect",
                "MODIFY (incorrect / wrong-string): heater 18.0 -> 9.0 MW bound to idle string B "
                "while live string A WABT 392 C > 378 C cap. Routing relay.idle.B -> "
                "policy.heater_idle_cut; no positive weight to policy.heater_live_cut.",
            ),
        ]
    )
    future = OrderedDict(
        [
            (
                "summary",
                "Wrong-MODIFY bound idle string B and cut that heater to 9.0 MW. Live string A "
                "WABT 392 C was over the 378 C cap at t_gate. Peak 408 C coked the bed. 12 min "
                "live-string recycle (abort_s=720). Correct gate was MODIFY heater 18.0 -> 9.0 MW "
                "on live string A.",
            ),
            (
                "state_delta",
                OrderedDict(
                    [
                        ("live", "idle-string cut; peak 408 C > 378 cap"),
                        ("coke", "string-A bed coked during wrong-string bind"),
                        ("recycle", "12 min live-string recycle"),
                        ("mission", "hold deferred"),
                    ]
                ),
            ),
            (
                "surprises",
                [
                    "Live-first was the correct order and the live number was over cap; the MODIFY spent that win on an idle parallel bank whose status=idle.",
                    "Delayed (abort_s=720): NH-8 holds 12 min while string A is cooled and recoked; next drop 16 min late.",
                ],
            ),
            (
                "recovery",
                OrderedDict(
                    [
                        (
                            "correct_gate",
                            "MODIFY heater 18.0 -> 9.0 MW on live string A; leave idle string B untouched; idle_status remains a discarded tag.",
                        ),
                        ("correct_actuator", "heater_A"),
                        ("wrong_bind", "idle_string_B_as_live"),
                        ("live_string_id", "A"),
                        ("idle_string_id", "B"),
                        (
                            "wrong_edit_applied",
                            OrderedDict(
                                [
                                    ("heater_MW", 9.0),
                                    ("string_id", "B"),
                                    ("bind_idle_string", True),
                                ]
                            ),
                        ),
                        (
                            "cost",
                            "12 min live-string recycle (task/efficiency); WABT peaked 408 C while the idle bank was treated as live (safety near-miss of a wrong-string bind).",
                        ),
                    ]
                ),
            ),
            (
                "race_result",
                OrderedDict(
                    [
                        ("winner", "ir.wabt.A (5.480 ms, 392 C)"),
                        ("loser", "tag.idle.B (5.640 ms, idle 312 C)"),
                        ("margin_us", 160),
                        (
                            "counterfactual_if_reversed",
                            "Idle-first by < 160 us would still be a standby 312 C under the "
                            "378 C cap; a correct gate binds ir.wabt.A to policy.heater_live_cut "
                            "either way. The wrong MODIFY spent the live win on an idle string.",
                        ),
                    ]
                ),
            ),
            ("reward_inflection_t_us", 6180),
            (
                "reward_inflection_note",
                "Task, safety, and efficiency drop at the wrong-string bind (6.180 ms, tick 4). "
                "The 12 min live-string recycle is delayed surprise, not the inflection.",
            ),
            ("delayed_surprise_s", 720),
        ]
    )
    dw = 0.35
    ras = raster_core(
        30,
        90,
        32,
        86,
        routing(
            "thalamic-relay.wabt-live",
            "spikenaut.policy.heater-idle-cut",
            [
                ("relay.idle.B", "policy.heater_idle_cut", 0.73),
                ("relay.ir.wabt.A", "policy.heater_idle_cut", 0.21),
            ],
            "acetylcholine",
            0.08,
            "timing_cap_stdp; ACh tags the (wrong) heater_idle_cut bind at the live-WABT win",
        ),
        excerpt,
        extra=OrderedDict(
            [
                ("excerpt_source", "kernelized_events"),
                ("sim_scope", "none"),
                ("abort_s", 720),
                ("delayed_surprise_s", 720),
                ("idle_status", True),
                ("live_string_id", "A"),
                ("idle_string_id", "B"),
            ]
        ),
    )
    gate = OrderedDict(
        [
            ("decision_window_ms", dw),
            ("decision", "MODIFY"),
            (
                "populations",
                [
                    pop_budget("heater_idle_cut", 48, 0.45, 300.0, dw),
                    pop("heater_live_cut", 48, 0.90),
                    pop("idle_veto", 20, 0.80),
                ],
            ),
        ]
    )
    return OrderedDict(
        [
            ("id", "ttf-r59-312"),
            (
                "title",
                "WRONG-MODIFY at Naphtha-Holt NH-8 / string A: live WABT 392 C read correctly; "
                "heater cut bound to idle string B (wrong-string / live-vs-idle parallel bank)",
            ),
            ("state", state),
            ("spike_events", spikes),
            ("proposed_action", proposed),
            ("safety_decision", safety),
            ("executed_action", executed),
            ("future_outcome", future),
            (
                "reward_components",
                reward_block(
                    ticks,
                    "Wrong-modify / wrong-string. Sidecar arithmetic 392 > 378 on live string A is "
                    "true; MODIFY bound to heater_idle_cut. total -0.68 = -0.22 + -0.24 + -0.18 + -0.10 + 0.06.",
                ),
            ),
            ("raster", ras),
            ("gate_snn", gate),
            (
                "meta",
                meta_block(
                    "naphtha-hydrotreater",
                    [
                        "modify",
                        "wrong-gate",
                        "wrong-string",
                        "live-vs-idle",
                        "sidecar-convictable",
                        "designed",
                    ],
                    "Teaches a probe that a correct live-WABT-first race can still be a wrong gate "
                    "when the MODIFY binds an idle parallel bank. Convictable from tags and routing "
                    "without hydrotreater physics.",
                    2,
                    supervisor_error_type="wrong-modify",
                ),
            ),
        ]
    )


def record_313():
    ticks = [
        tick(2768, 0.01, 0.04, 0.01, 0.01, 0.01),
        tick(6960, 0.02, 0.08, 0.02, 0.02, 0.01),
        tick(7140, 0.01, 0.06, 0.02, 0.01, 0.01),
        tick(7740, 0.04, 0.16, 0.04, 0.04, 0.02),
        tick(8140, 0.01, 0.05, 0.02, 0.01, 0.01),
        tick(540000000, 0.01, 0.03, 0.01, 0.01, 0.00),
    ]
    spikes = [
        spike("enc.mw.furnace", 1.380, 0.40),
        spike("ae.break.pps", 2.768, 0.56),
        spike("enc.mw.furnace", 4.200, 0.48),
        spike("ae.break.pps", 6.960, 1.34),
        spike("enc.mw.furnace", 7.140, 1.11),
        spike("ctrl.gate", 7.740, 0.98),
        spike("ae.break.pps", 10.400, 0.81),
        spike("enc.mw.furnace", 14.800, 0.62),
        spike("ctrl.gate", 18.200, 0.84),
        spike("ae.break.pps", 28.400, 0.52),
        spike("enc.mw.furnace", 36.100, 0.39),
        spike("ae.break.pps", 42.200, 0.44),
    ]
    excerpt = independent_excerpt(59313, 116, 46000, 15, spike_avoid_us(spikes))
    state = OrderedDict(
        [
            (
                "description",
                "HCl synthesis burner B-2 on the Burner-Gill BG-HIL pad reports graphite-nozzle AE "
                "at 44 pulses/s while furnace load is 6.80 MW, below the 8.00 MW trip. Acoustic-first "
                "freezes H2/Cl2; load-first would command 7.40 MW because power looks in-spec. "
                "Authority is the HIL burner mockup, not the chlorine header.",
            ),
            ("domain", "hcl-synthesis-furnace"),
            ("sim_or_real", "hil"),
            (
                "goal",
                "Keep B-2 from ramping through a cracked graphite nozzle while furnace load remains "
                "under its own MW cap.",
            ),
            ("t0_us", 1756850400000313),
            ("gate_latency_us", 760),
            ("race_window_us", 340),
            ("race_window_rel_ms", [6.96, 7.30]),
            (
                "race",
                OrderedDict(
                    [
                        (
                            "contenders",
                            [
                                "ae.break.pps 44 over 12 cap",
                                "enc.mw.furnace 6.80 under 8.00 cap",
                            ],
                        ),
                        (
                            "semantics",
                            "AE-first latches hold; load-first ramps 7.40 MW on a "
                            "'furnace still legal' model.",
                        ),
                        (
                            "window_derivation",
                            "340 us = one AE puck slot versus the MW-encoder publisher on this "
                            "HIL burner bus.",
                        ),
                        (
                            "order_evidence_note",
                            "Margin 180 us vs combined jitter 58 us (AE 26 + MW 32): 3.10x over "
                            "a 2.0x trust floor. Reversing order by < 180 us inside the 340 us "
                            "window would have ramped 7.40 MW through a cracked nozzle.",
                        ),
                    ]
                ),
            ),
            (
                "sensors",
                [
                    "graphite-nozzle AE puck, 50 kHz, 26 us jitter",
                    "furnace MW encoder, 1 kHz, 32 us jitter",
                    "H2 FT (context)",
                    "Cl2 FT (context)",
                ],
            ),
            (
                "constraints",
                OrderedDict(
                    [
                        ("ae_cap_pps", 12.0),
                        ("observed_ae_pps", 44.0),
                        ("furnace_MW", 6.80),
                        ("furnace_cap_MW", 8.00),
                        ("proposed_MW", 7.40),
                    ]
                ),
            ),
            (
                "episode_steps",
                [
                    "1. B-2 HIL indexed; ramp 7.40 MW armed.",
                    "2. Load 6.80 MW under 8.00; AE 44 pps over 12.",
                    "3. MW precursor at 1.380 ms.",
                    "4. Race window [6.960, 7.300] ms.",
                    "5. ae.break.pps 44 at 6.960 ms (winner).",
                    "6. enc.mw.furnace 6.80 at 7.140 ms (loser by 180 us).",
                    "7. Gate at 7.740 ms: REJECT hold, do not ramp.",
                    "8. Load left 6.80 MW; H2/Cl2 held.",
                    "9. Nozzle inspected on the HIL pad.",
                    "10. Delayed (abort_s=540): 9 min nozzle reset.",
                ],
            ),
        ]
    )
    proposed = OrderedDict(
        [
            ("name", "ramp_hcl_burner"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("furnace_MW", 7.40),
                        ("hold", False),
                        ("ae_pps", 44.0),
                    ]
                ),
            ),
            (
                "evidence",
                OrderedDict(
                    [
                        ("ae_pps", 44.0),
                        ("ae_cap_pps", 12.0),
                        ("furnace_MW", 6.80),
                        ("furnace_cap_MW", 8.00),
                        ("race_margin_us", 180),
                        ("combined_jitter_us", 58),
                        ("abort_s", 540),
                    ]
                ),
            ),
            (
                "basis",
                "Planner proposes 7.40 MW because furnace 6.80 MW is under 8.00, treating the "
                "44 pps AE as nozzle-weld noise rather than a cracked graphite nozzle.",
            ),
        ]
    )
    safety = OrderedDict(
        [
            ("decision", "REJECT"),
            ("correctness", "correct"),
            (
                "rationale",
                "Graphite-nozzle AE 44 pps won by 180 us, so the nozzle is cracked, not still a "
                "furnace-load story. Load 6.80 MW is under 8.00 and does not authorize a ramp. "
                "REJECT: hold 6.80 MW, do not go to 7.40. A MODIFY that only trims Cl2 would "
                "leave the cracked nozzle.",
            ),
            (
                "constraint_checked",
                OrderedDict(
                    [
                        (
                            "ae_pps",
                            OrderedDict(
                                [
                                    ("cap", 12.0),
                                    ("observed", 44.0),
                                    ("executed_furnace_MW", 6.80),
                                ]
                            ),
                        ),
                        (
                            "order_evidence",
                            OrderedDict(
                                [
                                    ("margin_us", 180),
                                    ("combined_jitter_us", 58),
                                    ("ratio", 3.10),
                                ]
                            ),
                        ),
                    ]
                ),
            ),
        ]
    )
    executed = OrderedDict(
        [
            ("name", "hold_hcl_burner"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("furnace_MW", 6.80),
                        ("hold", True),
                        ("ae_pps", 44.0),
                    ]
                ),
            ),
            (
                "gate_effect",
                "REJECT: load left 6.80 MW, do not ramp 7.40. Nozzle left on the HIL pad.",
            ),
        ]
    )
    future = OrderedDict(
        [
            (
                "summary",
                "Correct REJECT held B-2. AE 44 pps beat furnace 6.80 MW by 180 us. Load was "
                "legal; the nozzle was not. 9 min nozzle reset (abort_s=540) is delayed survey, "
                "not a process miss.",
            ),
            (
                "state_delta",
                OrderedDict(
                    [
                        ("load", "held at 6.80 MW"),
                        ("furnace", "left 6.80 MW < 8.00 cap"),
                        ("nozzle", "9 min nozzle reset (abort_s=540)"),
                        ("mission", "HIL ramp not pulled"),
                    ]
                ),
            ),
            (
                "surprises",
                [
                    "MW encoder never crossed its cap; AE was the only over-cap channel.",
                    "Delayed (abort_s=540): 9 min nozzle reset on the HIL pad.",
                ],
            ),
            (
                "race_result",
                OrderedDict(
                    [
                        ("winner", "ae.break.pps (6.960 ms, 44 pps)"),
                        ("loser", "enc.mw.furnace (7.140 ms, 6.80 MW)"),
                        ("margin_us", 180),
                        (
                            "counterfactual_if_reversed",
                            "Load-first by < 180 us inside the 340 us window would have ramped "
                            "7.40 MW through a cracked nozzle. The REJECT is still the correct gate.",
                        ),
                    ]
                ),
            ),
            ("reward_inflection_t_us", 7740),
            (
                "reward_inflection_note",
                "Safety and task rise at the correct REJECT (7.740 ms, tick 4). The 9 min nozzle "
                "reset is delayed surprise, not the inflection.",
            ),
            ("delayed_surprise_s", 540),
        ]
    )
    dw = 0.34
    ras = raster_core(
        46,
        116,
        22,
        117,
        routing(
            "thalamic-relay.nozzle-ae",
            "spikenaut.policy.burner-hold",
            [
                ("relay.ae.break", "policy.burner_hold", 0.70),
                ("relay.enc.mw", "policy.burner_go", 0.24),
            ],
            "dopamine",
            0.05,
            "hold_stdp; DA tags the AE win as a reject-hold bind",
        ),
        excerpt,
        extra=OrderedDict(
            [
                ("excerpt_source", "kernelized_events"),
                ("sim_scope", "none"),
                ("abort_s", 540),
                ("delayed_surprise_s", 540),
            ]
        ),
    )
    gate = OrderedDict(
        [
            ("decision_window_ms", dw),
            ("decision", "REJECT"),
            (
                "populations",
                [
                    pop_budget("burner_hold", 56, 0.45, 280.0, dw),
                    pop("burner_go", 40, 0.90),
                    pop("ae_veto", 24, 0.70),
                ],
            ),
        ]
    )
    return OrderedDict(
        [
            ("id", "ttf-r59-313"),
            (
                "title",
                "Burner-Gill BG-HIL / B-2: nozzle AE 44 pps beats furnace 6.80 MW by 180 us; "
                "correct REJECT holds the HCl burner",
            ),
            ("state", state),
            ("spike_events", spikes),
            ("proposed_action", proposed),
            ("safety_decision", safety),
            ("executed_action", executed),
            ("future_outcome", future),
            (
                "reward_components",
                reward_block(
                    ticks,
                    "Correct REJECT. AE 44 > 12 cap beats legal furnace load. "
                    "total +0.80 = 0.10 + 0.42 + 0.12 + 0.10 + 0.06.",
                ),
            ),
            ("raster", ras),
            ("gate_snn", gate),
            (
                "meta",
                meta_block(
                    "hcl-synthesis-furnace",
                    [
                        "reject",
                        "hil",
                        "ae-vs-mw",
                        "cracked-nozzle",
                        "tick6-sidecar-bound",
                    ],
                    "Teaches that a legal furnace load can lose to graphite-nozzle AE inside a "
                    "340 us window; reversing 180 us would have ramped through a crack.",
                    3,
                ),
            ),
        ]
    )


def record_314():
    ticks = [
        tick(2992, 0.06, 0.04, 0.02, 0.02, 0.01),
        tick(7520, 0.08, 0.06, 0.04, 0.02, 0.02),
        tick(7680, 0.06, 0.04, 0.03, 0.02, 0.01),
        tick(8120, 0.12, 0.08, 0.05, 0.04, 0.02),
        tick(8580, 0.04, 0.04, 0.02, 0.01, 0.01),
        tick(420000000, 0.04, 0.02, 0.02, 0.01, 0.01),
    ]
    spikes = [
        spike("enc.feed.tph", 1.220, 0.40),
        spike("ir.magma.sg", 2.992, 0.55),
        spike("enc.feed.tph", 4.400, 0.48),
        spike("ir.magma.sg", 7.520, 1.26),
        spike("enc.feed.tph", 7.680, 1.08),
        spike("ctrl.gate", 8.120, 0.95),
        spike("ir.magma.sg", 11.200, 0.78),
        spike("enc.feed.tph", 14.800, 0.60),
        spike("ctrl.gate", 18.400, 0.82),
        spike("ir.magma.sg", 22.600, 0.50),
        spike("enc.feed.tph", 26.200, 0.38),
    ]
    excerpt = independent_excerpt(59314, 50, 28000, 12, spike_avoid_us(spikes))
    params = OrderedDict(
        [
            ("feed_t_h", 12.0),
            ("magma_sg", 1.32),
            ("hold", False),
        ]
    )
    state = OrderedDict(
        [
            (
                "description",
                "Oslo crystallizer CR-5 inside Glauber-Fen GF-9 simulation holds magma specific "
                "gravity 1.32, below the 1.45 cap, with feed 12.0 t/h under the 16.0 t/h limit. "
                "Magma-first keeps 12.0 t/h; feed-first would idle a classified bed that already "
                "meets both limits on a climbing-density story.",
            ),
            ("domain", "oslo-crystallizer"),
            ("sim_or_real", "simulated"),
            (
                "goal",
                "Finish the GF-9 hold with magma SG <= 1.45 and feed <= 16.0 t/h.",
            ),
            ("t0_us", 1756850400000314),
            ("gate_latency_us", 650),
            ("race_window_us", 310),
            ("race_window_rel_ms", [7.52, 7.83]),
            (
                "race",
                OrderedDict(
                    [
                        (
                            "contenders",
                            [
                                "ir.magma.sg 1.32 under 1.45 cap",
                                "enc.feed.tph 12.0 under 16.0 cap",
                            ],
                        ),
                        (
                            "semantics",
                            "Magma-first accepts 12.0 t/h; feed-first would REJECT a legal hold "
                            "as still climbing.",
                        ),
                        (
                            "window_derivation",
                            "310 us = one magma-SG slot versus the feed-FT publisher on this "
                            "Oslo sim bus.",
                        ),
                        (
                            "order_evidence_note",
                            "Margin 160 us vs combined jitter 54 us (SG 24 + feed 30): 2.96x "
                            "over a 2.0x trust floor. Reversing order by < 160 us inside the 310 us "
                            "window would have REJECTED an already-legal hold.",
                        ),
                    ]
                ),
            ),
            (
                "sensors",
                [
                    "magma densitometer, 2 kHz, 24 us jitter",
                    "feed FT, 1 kHz, 30 us jitter",
                    "elutriation FT (context)",
                    "vessel PT (context)",
                ],
            ),
            (
                "constraints",
                OrderedDict(
                    [
                        ("magma_cap_sg", 1.45),
                        ("observed_magma_sg", 1.32),
                        ("feed_t_h", 12.0),
                        ("feed_cap_t_h", 16.0),
                    ]
                ),
            ),
            (
                "episode_steps",
                [
                    "1. CR-5 simulated; hold 12.0 t/h armed.",
                    "2. Magma SG 1.32; feed 12.0 t/h under 16.0.",
                    "3. Feed precursor at 1.220 ms.",
                    "4. Race window [7.520, 7.830] ms.",
                    "5. ir.magma.sg 1.32 at 7.520 ms (winner).",
                    "6. enc.feed.tph 12.0 at 7.680 ms (loser by 160 us).",
                    "7. Gate at 8.120 ms: ACCEPT 12.0 t/h.",
                    "8. Magma stays 1.32; feed stays 12.0.",
                    "9. Simulated lighting holds the densitometer.",
                    "10. Delayed (survey_s=420): 7 min classified-bed survey.",
                ],
            ),
        ]
    )
    proposed = OrderedDict(
        [
            ("name", "hold_oslo_feed"),
            ("parameters", params),
            (
                "evidence",
                OrderedDict(
                    [
                        ("magma_sg", 1.32),
                        ("magma_cap_sg", 1.45),
                        ("feed_t_h", 12.0),
                        ("feed_cap_t_h", 16.0),
                        ("race_margin_us", 160),
                        ("combined_jitter_us", 54),
                        ("survey_s", 420),
                    ]
                ),
            ),
            (
                "basis",
                "Planner proposes 12.0 t/h because magma 1.32 is under the 1.45 cap "
                "and feed 12.0 t/h is under 16.0.",
            ),
        ]
    )
    safety = OrderedDict(
        [
            ("decision", "ACCEPT"),
            ("correctness", "correct"),
            (
                "rationale",
                "Magma SG 1.32 won by 160 us, so the hold is already legal, not still "
                "climbing. Feed 12.0 t/h is under 16.0. ACCEPT the 12.0 t/h hold. A REJECT "
                "would idle a legal Oslo bed.",
            ),
            (
                "constraint_checked",
                OrderedDict(
                    [
                        (
                            "magma_sg",
                            OrderedDict(
                                [
                                    ("cap", 1.45),
                                    ("observed", 1.32),
                                    ("executed_feed_t_h", 12.0),
                                ]
                            ),
                        ),
                        (
                            "order_evidence",
                            OrderedDict(
                                [
                                    ("margin_us", 160),
                                    ("combined_jitter_us", 54),
                                    ("ratio", 2.96),
                                ]
                            ),
                        ),
                    ]
                ),
            ),
        ]
    )
    executed = OrderedDict(
        [
            ("name", "hold_oslo_feed"),
            ("parameters", OrderedDict(params.items())),
            ("gate_effect", "ACCEPT: leave 12.0 t/h; magma 1.32; feed legal."),
        ]
    )
    future = OrderedDict(
        [
            (
                "summary",
                "Correct ACCEPT of an already-legal 12.0 t/h hold. Magma 1.32 beat feed 12.0 "
                "t/h by 160 us. 7 min classified-bed survey (survey_s=420) is delayed, not a miss.",
            ),
            (
                "state_delta",
                OrderedDict(
                    [
                        ("feed", "12.0 t/h held"),
                        ("magma", "1.32 < 1.45 cap"),
                        ("elutriation", "on-spec"),
                        ("survey", "7 min classified-bed survey (survey_s=420)"),
                    ]
                ),
            ),
            (
                "surprises",
                [
                    "Feed FT never approached 16.0 t/h; magma was already under cap.",
                    "Delayed (survey_s=420): 7 min densitometer survey on the simulated bed.",
                ],
            ),
            (
                "race_result",
                OrderedDict(
                    [
                        ("winner", "ir.magma.sg (7.520 ms, 1.32)"),
                        ("loser", "enc.feed.tph (7.680 ms, 12.0 t/h)"),
                        ("margin_us", 160),
                        (
                            "counterfactual_if_reversed",
                            "Feed-first by < 160 us inside the 310 us window would have REJECTED "
                            "an already-legal hold. The ACCEPT is still the correct gate.",
                        ),
                    ]
                ),
            ),
            ("reward_inflection_t_us", 8120),
            (
                "reward_inflection_note",
                "Task and safety rise at the correct ACCEPT (8.120 ms, tick 4). The 7 min survey "
                "is delayed surprise, not the inflection.",
            ),
            ("delayed_surprise_s", 420),
        ]
    )
    dw = 0.31
    ras = raster_core(
        28,
        50,
        40,
        56,
        routing(
            "thalamic-relay.magma-sg",
            "spikenaut.policy.feed-go",
            [
                ("relay.ir.magma", "policy.feed_go", 0.69),
                ("relay.enc.feed", "policy.feed_hold", 0.26),
            ],
            "serotonin",
            0.06,
            "accept_stdp; 5-HT tags the magma-SG win as an already-legal hold",
        ),
        excerpt,
        extra=OrderedDict(
            [
                ("excerpt_source", "kernelized_events"),
                ("sim_scope", "none"),
                ("survey_s", 420),
                ("delayed_surprise_s", 420),
            ]
        ),
    )
    gate = OrderedDict(
        [
            ("decision_window_ms", dw),
            ("decision", "ACCEPT"),
            (
                "populations",
                [
                    pop_budget("feed_go", 44, 0.45, 260.0, dw),
                    pop("feed_hold", 36, 0.90),
                    pop("sg_veto", 18, 0.80),
                ],
            ),
        ]
    )
    return OrderedDict(
        [
            ("id", "ttf-r59-314"),
            (
                "title",
                "Glauber-Fen GF-9 / CR-5: magma SG 1.32 beats feed 12.0 t/h by 160 us; "
                "correct ACCEPT of an already-legal 12.0 t/h hold",
            ),
            ("state", state),
            ("spike_events", spikes),
            ("proposed_action", proposed),
            ("safety_decision", safety),
            ("executed_action", executed),
            ("future_outcome", future),
            (
                "reward_components",
                reward_block(
                    ticks,
                    "Correct ACCEPT. Magma 1.32 < 1.45; feed 12.0 < 16.0. "
                    "total +1.06 = 0.40 + 0.28 + 0.18 + 0.12 + 0.08.",
                ),
            ),
            ("raster", ras),
            ("gate_snn", gate),
            (
                "meta",
                meta_block(
                    "oslo-crystallizer",
                    [
                        "accept",
                        "simulated",
                        "magma-vs-feed",
                        "already-legal-hold",
                        "tick6-sidecar-bound",
                    ],
                    "Teaches that a legal feed FT can lose to magma SG inside a 310 us "
                    "window; reversing 160 us would have REJECTED an already-legal hold.",
                    4,
                ),
            ),
        ]
    )


def record_315():
    ticks = [
        tick(2016, 0.06, 0.04, 0.03, 0.02, 0.01),
        tick(5040, 0.10, 0.06, 0.04, 0.02, 0.02),
        tick(5200, 0.06, 0.04, 0.03, 0.02, 0.01),
        tick(5640, 0.14, 0.10, 0.06, 0.04, 0.02),
        tick(5840, 0.04, 0.04, 0.02, 0.01, 0.01),
        tick(240000000, 0.04, 0.02, 0.02, 0.01, 0.01),
    ]
    spikes = [
        spike("enc.belt.mpm", 0.960, 0.40),
        spike("ir.pu.zone", 2.016, 0.55),
        spike("enc.belt.mpm", 3.400, 0.48),
        spike("ir.pu.zone", 5.040, 1.24),
        spike("enc.belt.mpm", 5.200, 1.06),
        spike("ctrl.gate", 5.640, 0.94),
        spike("ir.pu.zone", 8.800, 0.76),
        spike("enc.belt.mpm", 12.200, 0.58),
        spike("ctrl.gate", 15.400, 0.80),
        spike("ir.pu.zone", 19.200, 0.50),
        spike("enc.belt.mpm", 22.600, 0.37),
    ]
    excerpt = independent_excerpt(59315, 82, 24000, 12, spike_avoid_us(spikes))
    params = OrderedDict(
        [
            ("belt_m_min", 4.80),
            ("pu", 42.0),
            ("hold", False),
        ]
    )
    state = OrderedDict(
        [
            (
                "description",
                "Pasteurizer zone Z-3 on Cask-Wold CW-7 carries 42 pasteurization units against "
                "an 80 PU ceiling, belt 4.80 m/min under the 6.40 m/min cap. PU-first keeps the "
                "4.80 m/min dwell; belt-first would idle a zone that already meets both ceilings "
                "on a ramping-chain story.",
            ),
            ("domain", "tunnel-pasteurizer"),
            ("sim_or_real", "designed"),
            (
                "goal",
                "Finish the CW-7 dwell with PU <= 80 and belt <= 6.40 m/min.",
            ),
            ("t0_us", 1756850400000315),
            ("gate_latency_us", 590),
            ("race_window_us", 270),
            ("race_window_rel_ms", [5.04, 5.31]),
            (
                "race",
                OrderedDict(
                    [
                        (
                            "contenders",
                            [
                                "ir.pu.zone 42 under 80 cap",
                                "enc.belt.mpm 4.80 under 6.40 cap",
                            ],
                        ),
                        (
                            "semantics",
                            "PU-first accepts 4.80 m/min; belt-first would REJECT a legal dwell "
                            "as still accelerating.",
                        ),
                        (
                            "window_derivation",
                            "270 us = one PU-integrator slot versus the belt-encoder publisher on "
                            "this pasteurizer bus.",
                        ),
                        (
                            "order_evidence_note",
                            "Margin 160 us vs combined jitter 52 us (PU 22 + belt 30): 3.08x over "
                            "a 2.0x trust floor. Reversing order by < 160 us inside the 270 us "
                            "window would have REJECTED an already-legal dwell.",
                        ),
                    ]
                ),
            ),
            (
                "sensors",
                [
                    "zone PU integrator, 2 kHz, 22 us jitter",
                    "belt encoder, 1 kHz, 30 us jitter",
                    "spray FT (context)",
                    "can-temp TC (context)",
                ],
            ),
            (
                "constraints",
                OrderedDict(
                    [
                        ("pu_cap", 80.0),
                        ("observed_pu", 42.0),
                        ("belt_m_min", 4.80),
                        ("belt_cap_m_min", 6.40),
                    ]
                ),
            ),
            (
                "episode_steps",
                [
                    "1. Z-3 indexed; belt 4.80 m/min armed.",
                    "2. PU 42 under 80; belt under 6.40.",
                    "3. Belt precursor at 0.960 ms.",
                    "4. Race window [5.040, 5.310] ms.",
                    "5. ir.pu.zone 42 at 5.040 ms (winner).",
                    "6. enc.belt.mpm 4.80 at 5.200 ms (loser by 160 us).",
                    "7. Gate at 5.640 ms: ACCEPT 4.80 m/min.",
                    "8. PU stays 42; belt stays 4.80 m/min.",
                    "9. Zone exits on-spec.",
                    "10. Delayed (dwell_s=240): 4 min can reseq.",
                ],
            ),
        ]
    )
    proposed = OrderedDict(
        [
            ("name", "hold_pasteur_dwell"),
            ("parameters", params),
            (
                "evidence",
                OrderedDict(
                    [
                        ("pu", 42.0),
                        ("pu_cap", 80.0),
                        ("belt_m_min", 4.80),
                        ("belt_cap_m_min", 6.40),
                        ("race_margin_us", 160),
                        ("combined_jitter_us", 52),
                        ("dwell_s", 240),
                    ]
                ),
            ),
            (
                "basis",
                "Planner proposes 4.80 m/min because PU 42 is under 80 and belt 4.80 is "
                "under 6.40.",
            ),
        ]
    )
    safety = OrderedDict(
        [
            ("decision", "ACCEPT"),
            ("correctness", "correct"),
            (
                "rationale",
                "Zone PU 42 won by 160 us, so the dwell is already legal, not still "
                "accelerating. Belt 4.80 m/min is under 6.40. ACCEPT the 4.80 m/min dwell. A "
                "REJECT would idle a legal pasteurizer zone.",
            ),
            (
                "constraint_checked",
                OrderedDict(
                    [
                        (
                            "pu",
                            OrderedDict(
                                [
                                    ("cap", 80.0),
                                    ("observed", 42.0),
                                    ("executed_belt_m_min", 4.80),
                                ]
                            ),
                        ),
                        (
                            "order_evidence",
                            OrderedDict(
                                [
                                    ("margin_us", 160),
                                    ("combined_jitter_us", 52),
                                    ("ratio", 3.08),
                                ]
                            ),
                        ),
                    ]
                ),
            ),
        ]
    )
    executed = OrderedDict(
        [
            ("name", "hold_pasteur_dwell"),
            ("parameters", OrderedDict(params.items())),
            ("gate_effect", "ACCEPT: leave 4.80 m/min; PU 42; belt legal."),
        ]
    )
    future = OrderedDict(
        [
            (
                "summary",
                "Correct ACCEPT of an already-legal 4.80 m/min dwell. PU 42 beat belt 4.80 "
                "m/min by 160 us. 4 min can reseq (dwell_s=240) is delayed, not a miss.",
            ),
            (
                "state_delta",
                OrderedDict(
                    [
                        ("belt", "4.80 m/min held"),
                        ("pu", "42 < 80 cap"),
                        ("cans", "zone on-spec"),
                        ("reseq", "4 min can reseq (dwell_s=240)"),
                    ]
                ),
            ),
            (
                "surprises",
                [
                    "Belt encoder never approached 6.40 m/min; PU was already under cap.",
                    "Delayed (dwell_s=240): 4 min can reseq after the zone.",
                ],
            ),
            (
                "race_result",
                OrderedDict(
                    [
                        ("winner", "ir.pu.zone (5.040 ms, 42 PU)"),
                        ("loser", "enc.belt.mpm (5.200 ms, 4.80 m/min)"),
                        ("margin_us", 160),
                        (
                            "counterfactual_if_reversed",
                            "Belt-first by < 160 us inside the 270 us window would have REJECTED "
                            "an already-legal dwell. The ACCEPT is still the correct gate.",
                        ),
                    ]
                ),
            ),
            ("reward_inflection_t_us", 5640),
            (
                "reward_inflection_note",
                "Task and safety rise at the correct ACCEPT (5.640 ms, tick 4). The 4 min reseq "
                "is delayed surprise, not the inflection.",
            ),
            ("delayed_surprise_s", 240),
        ]
    )
    dw = 0.27
    ras = raster_core(
        24,
        82,
        28,
        55,
        routing(
            "thalamic-relay.pu-zone",
            "spikenaut.policy.belt-go",
            [
                ("relay.ir.pu", "policy.belt_go", 0.67),
                ("relay.enc.belt", "policy.belt_hold", 0.25),
            ],
            "adenosine",
            0.07,
            "accept_stdp; adenosine tags the PU win as an already-legal dwell",
        ),
        excerpt,
        extra=OrderedDict(
            [
                ("excerpt_source", "kernelized_events"),
                ("sim_scope", "none"),
                ("dwell_s", 240),
                ("delayed_surprise_s", 240),
            ]
        ),
    )
    gate = OrderedDict(
        [
            ("decision_window_ms", dw),
            ("decision", "ACCEPT"),
            (
                "populations",
                [
                    pop_budget("belt_go", 40, 0.45, 250.0, dw),
                    pop("belt_hold", 32, 0.90),
                    pop("pu_veto", 16, 0.80),
                ],
            ),
        ]
    )
    return OrderedDict(
        [
            ("id", "ttf-r59-315"),
            (
                "title",
                "Cask-Wold CW-7 / Z-3: PU 42 beats belt 4.80 m/min by 160 us; "
                "correct ACCEPT of an already-legal 4.80 m/min dwell",
            ),
            ("state", state),
            ("spike_events", spikes),
            ("proposed_action", proposed),
            ("safety_decision", safety),
            ("executed_action", executed),
            ("future_outcome", future),
            (
                "reward_components",
                reward_block(
                    ticks,
                    "Correct ACCEPT. PU 42 < 80; belt 4.80 < 6.40. "
                    "total +1.14 = 0.44 + 0.30 + 0.20 + 0.12 + 0.08.",
                ),
            ),
            ("raster", ras),
            ("gate_snn", gate),
            (
                "meta",
                meta_block(
                    "tunnel-pasteurizer",
                    [
                        "accept",
                        "designed",
                        "pu-vs-belt",
                        "already-legal-dwell",
                        "tick6-sidecar-bound",
                    ],
                    "Teaches that a legal belt encoder can lose to zone PU inside a 270 us "
                    "window; reversing 160 us would have REJECTED an already-legal dwell.",
                    5,
                ),
            ),
        ]
    )
