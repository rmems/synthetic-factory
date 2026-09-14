def lif_357_excerpt():
    """Independent CUBA LIF (seed 68357). Plant remains designed."""

    n = 80
    dt_us = 100
    tau_m_ms = 19.5
    v_th = 1.0
    v_reset = 0.0
    refractory_us = 1000
    i_bias = 0.93
    i_stim_peak = 2.52
    stim = (21000, 25000)
    seed = 68357
    window_us = 42000
    i_clamp_extra = 0.66
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
    early = [(t, nid) for t, nid in spikes if t < 21000]
    burst = [(t, nid) for t, nid in spikes if 21000 <= t < 25000]
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
            early_flag = pool[0][0] < 21000
            have = len([1 for t, _ in picked if (t < 21000) == early_flag])
            if have >= want:
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
    take(burst, 9, label_times=(22400, 23300, 24200))
    clamp = [(t, nid) for t, nid in picked if t < 21000][:7]
    pack = [(t, nid) for t, nid in picked if t >= 21000][:9]
    picked = sorted(clamp + pack, key=lambda item: (item[0], item[1]))
    if len(picked) < 8:
        raise RuntimeError(f"LIF excerpt too short: {len(picked)}")
    channels = ["lif.clamp" if t < 21000 else "lif.pack" for t, _ in picked]
    lif = OrderedDict(
        [
            ("model", "leaky_integrate_and_fire"),
            ("n", 80),
            ("dt_us", 100),
            ("tau_m_ms", 19.5),
            ("v_rest", 0.0),
            ("v_reset", 0.0),
            ("v_th", 1.0),
            ("r_m", 1.0),
            ("refractory_us", 1000),
            ("i_bias", 0.93),
            ("i_stim_peak", 2.52),
            ("stim_t_us", [21000, 25000]),
            ("i_clamp_extra", 0.66),
            ("clamp_n", 14),
            ("seed", 68357),
            (
                "note",
                "Population sim scoped to this sidecar. Plant remains designed. "
                "Neurons 0-13 carry +0.66 working-solution-clamp bias; stim 21-25 ms is the extractor packing collapse.",
            ),
        ]
    )
    extra = OrderedDict(
        [
            ("excerpt_source", "independent_lif"),
            ("sim_scope", "sidecar_only"),
            ("lif", lif),
            ("abort_s", 1080),
            ("delayed_surprise_s", 1080),
        ]
    )
    return excerpt_items(picked, channels), extra


def record_356():
    ticks = [
        tick(2160, -0.02, 0.01, -0.02, -0.01, 0.01),
        tick(5400, -0.04, 0.01, -0.04, -0.02, 0.01),
        tick(5620, -0.03, 0.01, -0.03, -0.01, 0.01),
        tick(6200, -0.06, 0.02, -0.08, -0.03, 0.02),
        tick(6600, -0.02, 0.01, -0.03, -0.01, 0.01),
        tick(900000000, -0.01, 0.00, -0.02, 0.00, 0.00),
    ]
    spikes = [
        spike("enc.feed.ctx", 1.180, 0.44),
        spike("rtd.hearth.c", 2.360, 0.61),
        spike("tc.sib.skin", 3.720, 0.52),
        spike("bus.cf1.ctx", 4.440, 0.47),
        spike("rtd.hearth.c", 5.400, 1.31),
        spike("tc.sib.skin", 5.620, 1.18),
        spike("ctrl.gate", 6.200, 0.99),
        spike("rtd.hearth.c", 7.280, 0.84),
        spike("tc.sib.skin", 9.440, 0.66),
        spike("ctrl.gate", 14.880, 0.88),
        spike("enc.feed.ctx", 18.200, 0.41),
        spike("rtd.hearth.c", 23.400, 0.58),
    ]
    excerpt = independent_excerpt(68356, 88, 24000, 12, spike_avoid_us(spikes))
    state = OrderedDict(
        [
            (
                "description",
                "Calcium-carbide furnace CF-1 at Acetylene-Howe already holds a live hearth TC of "
                "1840 C when that analog sample races a sibling CF-2 skin loop that still prints "
                "2012 C. Published trip is 1980 C on the live hearth; a weak supervisor treats the "
                "sibling skin as CF-1 live and zeros a legal 18.0 t/h lime-coke feed.",
            ),
            ("domain", "calcium-carbide-furnace"),
            ("sim_or_real", "designed"),
            (
                "goal",
                "Hold 18.0 t/h on CF-1, keep live hearth T < 1980 C trip, and finish the "
                "15 min carbide-quality window.",
            ),
            ("t0_us", 1762300000000356),
            ("gate_latency_us", 800),
            ("race_window_us", 400),
            ("race_window_rel_ms", [5.400, 5.800]),
            (
                "race",
                OrderedDict(
                    [
                        (
                            "contenders",
                            [
                                "rtd.hearth.c 1840 C live CF-1 hearth",
                                "tc.sib.skin 2012 C leftover CF-2 sibling skin",
                            ],
                        ),
                        (
                            "semantics",
                            "Hearth-first should ACCEPT 18.0 t/h (1840 C < 1980 C trip). "
                            "Sibling-first would only delay confirmation of the same legal hearth.",
                        ),
                        (
                            "window_derivation",
                            "400 us = one CF-1 hearth analog slot versus the CF-2 sibling-skin "
                            "publisher on this 2 kHz carbide bus.",
                        ),
                        (
                            "order_evidence_note",
                            "Margin 220 us vs combined jitter 72 us (hearth 32 + sibling 40): 3.1x over "
                            "a 2.0x trust floor. Order is correctly hearth-first. The error is binding "
                            "a sibling-loop PV as if it were CF-1 live, not the race.",
                        ),
                    ]
                ),
            ),
            (
                "sensors",
                [
                    "CF-1 hearth RTD analog, 2 kHz, 32 us jitter, axis cf1_hearth_t, live_tag furnace_cf1_hearth",
                    "CF-2 sibling skin TC, 1 kHz, 40 us jitter, sibling_tag furnace_cf2_skin, sibling_is_live false",
                    "lime-coke feed encoder (context)",
                    "off-gas CO (context)",
                ],
            ),
            (
                "constraints",
                OrderedDict(
                    [
                        ("live_C", 1840.0),
                        ("trip_C", 1980.0),
                        ("sibling_C", 2012.0),
                        ("live_tag", "furnace_cf1_hearth"),
                        ("sibling_tag", "furnace_cf2_skin"),
                        ("sibling_is_live", False),
                        ("proposed_t_h", 18.0),
                    ]
                ),
            ),
            (
                "episode_steps",
                [
                    "1. Furnace CF-1 indexed on Acetylene-Howe; live hearth 1840 C, 18.0 t/h armed.",
                    "2. Published live trip 1980 C; CF-2 skin TC tagged sibling, not live.",
                    "3. Encoder precursor at 1.180 ms.",
                    "4. Race window [5.400, 5.800] ms.",
                    "5. Live hearth 1840 C at 5.400 ms (winner).",
                    "6. Sibling CF-2 skin 2012 C at 5.620 ms (loser by 220 us).",
                    "7. Gate at 6.200 ms: wrong REJECT holds 0 t/h on the sibling loop.",
                    "8. Feed idle; live hearth never crossed 1980 C.",
                    "9. 15 min carbide-quality window missed.",
                    "10. QA: correct gate was ACCEPT; leave 18.0 t/h; bind CF-1 hearth 1840 vs 1980 C trip.",
                ],
            ),
        ]
    )
    proposed = OrderedDict(
        [
            ("name", "carbide_18_hold"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("feed_t_h", 18.0),
                        ("hearth_C", 1840.0),
                        ("hold", False),
                    ]
                ),
            ),
            (
                "evidence",
                OrderedDict(
                    [
                        ("live_C", 1840.0),
                        ("trip_C", 1980.0),
                        ("sibling_C", 2012.0),
                        ("live_tag", "furnace_cf1_hearth"),
                        ("sibling_tag", "furnace_cf2_skin"),
                        ("sibling_is_live", False),
                        ("ft_axis", "cf1_hearth_t"),
                        ("race_margin_us", 220),
                        ("combined_jitter_us", 72),
                        ("t_gate_us", 6200),
                    ]
                ),
            ),
            (
                "basis",
                "Planner proposes 18.0 t/h because live CF-1 hearth 1840 C is 140 C under the "
                "published 1980 C trip and the 2012 C print is a sibling CF-2 skin, not CF-1 live.",
            ),
        ]
    )
    safety = OrderedDict(
        [
            ("decision", "REJECT"),
            ("correctness", "incorrect"),
            (
                "rationale",
                "Sibling skin is 2012 C, so the furnace is treated as over the 1980 C trip "
                "(true vs that CF-2 loop). REJECT: hold 0 t/h until the sibling cools so CF-1 "
                "does not see an over-temperature event.",
            ),
            (
                "constraint_checked",
                OrderedDict(
                    [
                        (
                            "cf1_hearth_t_C",
                            OrderedDict(
                                [
                                    ("published_live_trip", 1980.0),
                                    ("observed_live", 1840.0),
                                    ("sibling_loop_applied", True),
                                    ("sibling_C", 2012.0),
                                    ("executed_t_h", 0.0),
                                ]
                            ),
                        ),
                        (
                            "order_evidence",
                            OrderedDict(
                                [
                                    ("margin_us", 220),
                                    ("combined_jitter_us", 72),
                                    ("ratio", 3.06),
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
            ("name", "carbide_hold_sibling_loop"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("feed_t_h", 0.0),
                        ("hearth_C", 1840.0),
                        ("hold", True),
                    ]
                ),
            ),
            (
                "gate_effect",
                "REJECT (incorrect): feed 18.0 -> 0 t/h. Routing relay.sibling.loop -> "
                "policy.hold_reject; no positive weight to policy.go_accept. Live hearth 1840 C never "
                "violated the 1980 C trip.",
            ),
        ]
    )
    future = OrderedDict(
        [
            (
                "summary",
                "Wrong-REJECT froze CF-1 at 0 t/h while live hearth stayed 1840 C under the "
                "1980 C trip. 15 min carbide-quality window missed. Correct gate was ACCEPT of the "
                "already-legal 18.0 t/h command.",
            ),
            (
                "state_delta",
                OrderedDict(
                    [
                        ("furnace", "held at 0 t/h; 18.0 t/h abandoned"),
                        ("hearth_C", "still 1840 C, under 1980 C published trip"),
                        ("carbide", "15 min quality window missed"),
                        ("sibling", "no CF-1 over-temperature; CF-2 skin false positive"),
                    ]
                ),
            ),
            (
                "surprises",
                [
                    "The 2012 C print is CF-2 sibling skin, not CF-1 live hearth.",
                    "Delayed (15 min): sister furnace CF-3 ran the same 18.0 t/h carbide window after QA rebound the live trip; CF-1's slot was already gone.",
                ],
            ),
            (
                "recovery",
                OrderedDict(
                    [
                        (
                            "correct_gate",
                            "ACCEPT: live hearth 1840 C < published 1980 C trip; leave 18.0 t/h; ignore sibling CF-2 skin.",
                        ),
                        ("correct_trip_C", 1980.0),
                        ("wrong_sibling_bind", True),
                        (
                            "wrong_edit_applied",
                            OrderedDict([("feed_t_h", 0.0), ("hold", True)]),
                        ),
                        (
                            "cost",
                            "15 min missed carbide-quality window (task/efficiency); live hearth never over trip (safety false-positive).",
                        ),
                    ]
                ),
            ),
            (
                "race_result",
                OrderedDict(
                    [
                        ("winner", "rtd.hearth.c (5.400 ms, 1840 C)"),
                        ("loser", "tc.sib.skin (5.620 ms, 2012 C sibling)"),
                        ("margin_us", 220),
                        (
                            "counterfactual_if_reversed",
                            "Sibling-first by < 220 us would still show live hearth 1840 C < 1980 C. A "
                            "correct gate ACCEPTs either way. The wrong REJECT spent the hearth win "
                            "on a sibling-loop PV.",
                        ),
                    ]
                ),
            ),
            ("reward_inflection_t_us", 6200),
            (
                "reward_inflection_note",
                "Task and efficiency drop at the wrong REJECT (6.200 ms, tick 4). The 15 min "
                "missed window is delayed surprise, not the inflection.",
            ),
            ("delayed_surprise_s", 900.0),
            ("missed_window_s", 900),
        ]
    )
    ras = raster_core(
        24,
        88,
        32,
        68,
        routing(
            "relay.sibling.loop",
            "policy.hold_reject",
            [
                ("relay.sibling.loop", "policy.hold_reject", 0.73),
                ("relay.rtd.hearth", "policy.hold_reject", 0.21),
            ],
            "acetylcholine",
            0.08,
            "sibling_swap_stdp; ACh tags the (wrong) hold_reject bind at the hearth win",
        ),
        excerpt,
    )
    gate = OrderedDict(
        [
            ("decision_window_ms", 0.40),
            ("decision", "REJECT"),
            (
                "populations",
                [
                    pop("hold_reject", 48, 0.50, 200.0, 4),
                    pop("go_accept", 48, 0.80, 10.0, 0),
                    pop("hearth_trip_veto", 24, 0.75),
                ],
            ),
        ]
    )
    return wrap_record(
        "ttf-r68-356",
        "WRONG-REJECT at Acetylene-Howe / CF-1: live hearth 1840 C is legal vs "
        "published 1980 C trip; supervisor bound a sibling CF-2 skin loop as the PV",
        state,
        spikes,
        proposed,
        safety,
        executed,
        future,
        ticks,
        "Wrong-reject. Sidecar arithmetic 1840 < 1980 is true; clamp bound to a "
        "sibling-loop PV. total -0.36 = -0.18 + 0.06 + -0.22 + -0.08 + 0.06.",
        ras,
        gate,
        "calcium-carbide-furnace",
        [
            "reject",
            "wrong-gate",
            "channel-swap",
            "sibling-loop-as-live",
            "sidecar-convictable",
            "designed",
        ],
        "Teaches a probe that a correct live<trip read can still be a wrong gate when "
        "routing.table[0].to is policy.hold_reject and executed feed is zeroed on a sibling tag.",
        1,
        supervisor_error_type="wrong-reject",
    )


def record_357():
    excerpt, extra = lif_357_excerpt()
    ticks = [
        tick(1920, 0.05, -0.02, -0.02, 0.01, 0.00),
        tick(4800, 0.08, -0.04, -0.03, 0.01, -0.01),
        tick(5020, 0.04, -0.03, -0.02, 0.00, 0.00),
        tick(5680, 0.10, -0.06, -0.03, 0.02, -0.01),
        tick(22400, 0.05, -0.42, -0.04, 0.00, -0.02),
        tick(1080000000, 0.02, -0.05, -0.02, 0.00, 0.00),
    ]
    state = OrderedDict(
        [
            (
                "description",
                "Anthraquinone working-solution loop AO-4 at Anthraq-Holt is already pulling 42 m3/h "
                "when an oxidizer Delta-P pulse arrives 220 us before the flow meter that still reads "
                "a legal working-solution cruise. Pressure-first latches a process clamp under the "
                "3.00 kPa cap; flow-first would keep cruise circulation. Stored extractor packing load "
                "is not yet an observable of either race channel.",
            ),
            ("domain", "hydrogen-peroxide-ao-loop"),
            ("sim_or_real", "designed"),
            (
                "goal",
                "Keep AO-4 on 42 m3/h only while oxidizer Delta-P stays <= 3.00 kPa, and "
                "leave the extractor packing un-collapsed.",
            ),
            ("t0_us", 1762300000000357),
            ("gate_latency_us", 880),
            ("race_window_us", 380),
            ("race_window_rel_ms", [4.800, 5.180]),
            (
                "race",
                OrderedDict(
                    [
                        (
                            "contenders",
                            [
                                "dp.ox.kpa 3.40 kPa oxidizer off-gas",
                                "ft.ws.m3h 42 m3/h still-legal working solution",
                            ],
                        ),
                        (
                            "semantics",
                            "Pressure-first latches flow clamp 42 -> 28 m3/h; flow-first keeps "
                            "cruise circulation on a 'packing still open' model.",
                        ),
                        (
                            "window_derivation",
                            "380 us = one oxidizer DP slot minus working-solution flow-meter group "
                            "delay on this 1 kHz AO bus.",
                        ),
                        (
                            "order_evidence_note",
                            "Margin 220 us vs combined jitter 70 us (DP 32 + flow 38): 3.1x over "
                            "a 2.0x trust floor. Reversing order by < 220 us inside the 380 us window "
                            "would have kept 42 m3/h cruise; predicted next-sample DP 3.16 kPa > 3.00 cap.",
                        ),
                    ]
                ),
            ),
            (
                "sensors",
                [
                    "oxidizer off-gas DP, 1 kHz, 32 us timestamp jitter",
                    "working-solution flow meter, 1 kHz, 38 us jitter",
                    "circulation encoder (context)",
                    "extractor packing AE (context)",
                ],
            ),
            (
                "constraints",
                OrderedDict(
                    [
                        ("dp_cap_kPa", 3.00),
                        ("observed_dp_kPa", 3.40),
                        ("proposed_m3h", 42.0),
                        ("flow_floor_m3h", 22.0),
                    ]
                ),
            ),
            (
                "episode_steps",
                [
                    "1. Loop AO-4 indexed; 42 m3/h working solution; oxidizer DP 3.40 kPa > 3.00 cap.",
                    "2. Cruise circulation 42 m3/h armed; packing over the 3.00 kPa cap.",
                    "3. Encoder precursor at 1.160 ms; oxidizer-side warm-start 3.40 kPa.",
                    "4. Race window [4.800, 5.180] ms opens on the AO bus.",
                    "5. Oxidizer DP 3.40 kPa at 4.800 ms (winner).",
                    "6. Working-solution flow 42 m3/h at 5.020 ms (loser by 220 us).",
                    "7. Gate at 5.680 ms (winner + 880 us): MODIFY clamp 42 -> 28 m3/h.",
                    "8. Clamp executes; next-sample DP 2.58 kPa < 3.00 cap.",
                    "9. At 22.400 ms stored packing load collapses an extractor bay.",
                    "10. Emergency isolate 18 min + packing pull; named un-netted loss, not folded into process heads.",
                ],
            ),
        ]
    )
    proposed = OrderedDict(
        [
            ("name", "cruise_ws_loop"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("flow_m3h", 42.0),
                        ("dp_kPa", 3.40),
                        ("hold", False),
                    ]
                ),
            ),
            (
                "evidence",
                OrderedDict(
                    [
                        ("dp_kPa", 3.40),
                        ("dp_cap_kPa", 3.00),
                        ("predicted_unclamped_next_kPa", 3.16),
                        ("flow_m3h", 42.0),
                        ("race_margin_us", 220),
                        ("combined_jitter_us", 70),
                    ]
                ),
            ),
            (
                "basis",
                "Planner proposes 42 m3/h cruise: working-solution flow looks like an open extractor, "
                "not a packed bay, and the 3.00 kPa DP cap is treated as still open.",
            ),
        ]
    )
    safety = OrderedDict(
        [
            ("decision", "MODIFY"),
            ("correctness", "correct"),
            (
                "rationale",
                "Oxidizer DP 3.40 kPa won by 220 us, so the extractor is running packed, not still "
                "free. Holding 42 m3/h predicts next-sample 3.16 kPa > 3.00 kPa cap. MODIFY: flow "
                "42 -> 28 m3/h. Observed after clamp 2.58 kPa < 3.00. A full REJECT is not "
                "indicated: a sound AO loop accepts 28 m3/h.",
            ),
            (
                "constraint_checked",
                OrderedDict(
                    [
                        (
                            "ox_dp_kPa",
                            OrderedDict(
                                [
                                    ("cap", 3.00),
                                    ("observed", 3.40),
                                    ("predicted_unclamped_next", 3.16),
                                    ("clamped_m3h", 28.0),
                                    ("observed_after_clamp", 2.58),
                                ]
                            ),
                        ),
                        (
                            "order_evidence",
                            OrderedDict(
                                [
                                    ("margin_us", 220),
                                    ("combined_jitter_us", 70),
                                    ("ratio", 3.14),
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
            ("name", "clamped_ws_loop"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("flow_m3h", 28.0),
                        ("dp_kPa", 2.58),
                        ("hold", False),
                    ]
                ),
            ),
            (
                "gate_effect",
                "MODIFY: flow 42 -> 28 m3/h. Process-correct vs the 3.00 kPa DP cap. Extractor "
                "packing collapse still occurs at 22.400 ms.",
            ),
        ]
    )
    future = OrderedDict(
        [
            (
                "summary",
                "Process-correct MODIFY held DP at 2.58 kPa. At 22.400 ms stored packing load "
                "collapsed an extractor bay. Clamp reduced circulation energy; it did not dump the "
                "packing charge. Partnered negative: process heads stay honest; world loss is named, not netted.",
            ),
            (
                "state_delta",
                OrderedDict(
                    [
                        ("loop", "clamp executed; DP 2.58 kPa < 3.00"),
                        ("extractor", "packing collapse at 22.400 ms"),
                        ("repair", "18 min emergency isolate + packing pull"),
                        ("mission", "AO loop still converting; packing precursor controlled"),
                    ]
                ),
            ),
            (
                "surprises",
                [
                    "Neither oxidizer DP nor working-solution flow predicted the packing charge; ae.pack.col is a new channel at 22.400 ms, 16.720 ms after the gate, still inside the 42 ms raster.",
                    "Delayed (18 min): emergency isolate and packing pull close the collapse. Named un-netted loss, not folded into task_progress.",
                ],
            ),
            (
                "un_netted_loss",
                "18 min emergency isolate + packing pull after an extractor collapse. Safety "
                "head -0.62 prices the precursor; task_progress stays +0.34 because the flow clamp "
                "completed under the 3.00 kPa cap. World loss is named here, not subtracted from process heads.",
            ),
            (
                "race_result",
                OrderedDict(
                    [
                        ("winner", "dp.ox.kpa (4.800 ms, 3.40 kPa)"),
                        ("loser", "ft.ws.m3h (5.020 ms, 42 m3/h)"),
                        ("margin_us", 220),
                        (
                            "counterfactual_if_reversed",
                            "Flow-first by < 220 us inside the 380 us window would have kept "
                            "42 m3/h cruise; predicted next-sample 3.16 kPa would have exceeded the "
                            "3.00 kPa cap even without the packing charge. The MODIFY is still the "
                            "correct process. The collapse is a later world charge either way, cheaper "
                            "with the clamp than without.",
                        ),
                    ]
                ),
            ),
            ("reward_inflection_t_us", 22400),
            (
                "reward_inflection_note",
                "Safety collapses at the 22.400 ms extractor packing drop (tick t_us=22400), inside the "
                "42 ms raster. The correct MODIFY at 5.680 ms is in the same excerpt. Do not put "
                "inflection on the +18 min isolate tick.",
            ),
            ("delayed_surprise_s", 1080.0),
            ("abort_s", 1080),
        ]
    )
    spikes = [
        spike("enc.ws.ctx", 1.160, 0.43),
        spike("dp.ox.kpa", 2.280, 0.62),
        spike("ft.ws.m3h", 3.140, 0.55),
        spike("dp.ox.kpa", 4.800, 1.34),
        spike("ft.ws.m3h", 5.020, 1.12),
        spike("ctrl.gate", 5.680, 0.97),
        spike("dp.ox.kpa", 7.200, 0.81),
        spike("ft.ws.m3h", 10.400, 0.66),
        spike("ctrl.gate", 15.200, 0.84),
        spike("ae.pack.col", 22.400, 1.42),
        spike("ae.pack.col", 23.600, 0.91),
        spike("enc.ws.ctx", 29.800, 0.41),
        spike("dp.ox.kpa", 36.200, 0.58),
    ]
    ras = raster_core(
        42,
        80,
        24,
        81,
        routing(
            "thalamic-relay.dp-ws",
            "spikenaut.policy.ws-clamp",
            [
                ("relay.dp.ox", "policy.ws_clamp", 0.63),
                ("relay.ft.ws", "policy.loop_hold", 0.28),
                ("relay.ae.pack", "policy.ws_clamp", -0.47),
            ],
            "noradrenaline",
            0.05,
            "surprise-gated pre_post_stdp; NA at DP win (4.800 ms) opens a 50 ms eligibility "
            "trace that still covers the 22.400 ms extractor packing collapse",
        ),
        excerpt,
        extra=extra,
    )
    gate = OrderedDict(
        [
            ("decision_window_ms", 0.38),
            ("decision", "MODIFY"),
            (
                "populations",
                [
                    pop("ws_clamp", 48, 0.50, 220.0, 4),
                    pop("loop_hold", 48, 0.50, 50.0, 1),
                    pop("dp_cap_veto", 24, 0.75),
                ],
            ),
        ]
    )
    return wrap_record(
        "ttf-r68-357",
        "Anthraq-Holt AO loop / AO-4: oxidizer DP beats working-solution flow by 220 us; correct "
        "MODIFY still eats an in-window extractor packing collapse (partnered negative total -0.44)",
        state,
        spikes,
        proposed,
        safety,
        executed,
        future,
        ticks,
        "Partnered negative. Process-correct MODIFY; world still charges inside the "
        "42 ms raster. total -0.44 = 0.34 + -0.62 + -0.16 + 0.04 + -0.04. Named "
        "isolate+packing-pull loss is not netted into task_progress.",
        ras,
        gate,
        "hydrogen-peroxide-ao-loop",
        [
            "modify",
            "partnered-negative-total",
            "independent-lif-raster",
            "sidecar-sim-only",
            "in-window-world-charge",
            "designed",
        ],
        "A critic can see the world-charge as a LIF burst inside the raster while "
        "process heads stay honest. Credit assignment is spikes, not prose across an "
        "18 min gap.",
        2,
    )


def record_358():
    ticks = [
        tick(1648, 0.01, 0.04, 0.02, 0.01, 0.01),
        tick(4120, 0.02, 0.08, 0.02, 0.02, 0.01),
        tick(4310, 0.01, 0.06, 0.02, 0.01, 0.01),
        tick(5220, 0.03, 0.12, 0.04, 0.04, 0.02),
        tick(5500, 0.02, 0.07, 0.01, 0.01, 0.01),
        tick(480000000, 0.01, 0.03, 0.01, 0.01, 0.00),
    ]
    spikes = [
        spike("enc.feed.ctx", 1.080, 0.44),
        spike("tc.salt.c", 2.240, 0.71),
        spike("enc.preheat.hz", 3.080, 0.52),
        spike("tc.salt.c", 4.120, 1.36),
        spike("enc.preheat.hz", 4.310, 1.14),
        spike("ctrl.gate", 5.220, 0.98),
        spike("tc.salt.c", 7.400, 0.82),
        spike("enc.preheat.hz", 10.800, 0.61),
        spike("ctrl.gate", 16.200, 0.86),
        spike("tc.salt.c", 24.600, 0.70),
        spike("enc.preheat.hz", 33.400, 0.48),
        spike("t.air.ctx", 41.200, 0.40),
    ]
    excerpt = independent_excerpt(68358, 104, 44000, 13, spike_avoid_us(spikes))
    state = OrderedDict(
        [
            (
                "description",
                "Phthalic-anhydride reactor PA-2 on the Oxylene-Ness HIL pad is feeding at 6.4 t/h "
                "when a salt-bath burst at 412 C races the air-preheat encoder that still looks "
                "in-band for a feed step. Ramp is legal only if salt bath <= 390 C. Bath-first "
                "latches hold; encoder-first would treat in-band preheat Hz as hotspot clearance.",
            ),
            ("domain", "phthalic-anhydride-reactor"),
            ("sim_or_real", "hil"),
            (
                "goal",
                "Do not feed PA-2 unless salt bath <= 390 C; keep o-xylene 0 t/h until the "
                "bath is quiet.",
            ),
            ("t0_us", 1762300000000358),
            ("gate_latency_us", 1100),
            ("race_window_us", 280),
            ("race_window_rel_ms", [4.120, 4.400]),
            (
                "race",
                OrderedDict(
                    [
                        (
                            "contenders",
                            [
                                "tc.salt.c 412 C salt-bath flare",
                                "enc.preheat.hz 18 Hz still-in-band",
                            ],
                        ),
                        (
                            "semantics",
                            "Bath-first latches REJECT hold 0 t/h; encoder-first would keep 6.4 t/h "
                            "on an in-band-preheat-as-clearance model.",
                        ),
                        (
                            "window_derivation",
                            "280 us = one salt-bath TC envelope slot versus the air-preheat-encoder "
                            "publisher on this pad cycle.",
                        ),
                        (
                            "order_evidence_note",
                            "Margin 190 us vs combined jitter 56 us (bath 26 + encoder 30): 3.4x over a "
                            "2.0x trust floor. Pad injects encoder 80-120 us before the bath envelope "
                            "finishes (loop lag, not a sensor fault); the encoder packet is still "
                            "the loser in this 280 us window.",
                        ),
                    ]
                ),
            ),
            (
                "sensors",
                [
                    "salt-bath TC, 26 us jitter, 390 C trip",
                    "air-preheat encoder, 30 us jitter",
                    "o-xylene mass flow (context)",
                    "hotspot TC (context)",
                ],
            ),
            (
                "constraints",
                OrderedDict(
                    [
                        ("bath_trip_C", 390.0),
                        ("observed_bath_C", 412.0),
                        ("preheat_cap_hz", 24.0),
                        ("proposed_t_h", 6.4),
                    ]
                ),
            ),
            (
                "hil",
                OrderedDict(
                    [
                        ("bench", "Oxylene-Ness OX-HIL phthalic reactor pad, PA-2"),
                        ("inject", "bath envelope delayed 80-120 us vs encoder; loop lag, not a false salt TC"),
                    ]
                ),
            ),
            (
                "episode_steps",
                [
                    "1. PA-2 on Oxylene-Ness HIL pad; bath in band; o-xylene armed at 6.4 t/h.",
                    "2. Bath trip 390 C; observed 412 C flare on salt circuit.",
                    "3. Encoder precursor at 1.080 ms.",
                    "4. Race window [4.120, 4.400] ms.",
                    "5. Salt bath 412 C at 4.120 ms (winner).",
                    "6. Preheat encoder 18 Hz at 4.310 ms (loser by 190 us).",
                    "7. Gate at 5.220 ms: REJECT hold 0 t/h, do not feed.",
                    "8. Pad recycle 8 min; bath decays under 390 C after hold.",
                    "9. Reactor never saw a hotspot runaway; encoder-as-clearance would have fed into the flare.",
                    "10. QA: correct gate was REJECT; leave 0 t/h until bath <= 390 C.",
                ],
            ),
        ]
    )
    proposed = OrderedDict(
        [
            ("name", "feed_6p4"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("feed_t_h", 6.4),
                        ("bath_C", 412.0),
                        ("hold", False),
                    ]
                ),
            ),
            (
                "evidence",
                OrderedDict(
                    [
                        ("bath_C", 412.0),
                        ("bath_trip_C", 390.0),
                        ("preheat_hz", 18.0),
                        ("preheat_cap_hz", 24.0),
                        ("race_margin_us", 190),
                        ("combined_jitter_us", 56),
                        ("t_gate_us", 5220),
                    ]
                ),
            ),
            (
                "basis",
                "Planner proposes 6.4 t/h because preheat encoder is under the 24 Hz cap and treats "
                "the encoder as hotspot clearance, ignoring the 412 C salt-bath flare.",
            ),
        ]
    )
    safety = OrderedDict(
        [
            ("decision", "REJECT"),
            ("correctness", "correct"),
            (
                "rationale",
                "Salt bath 412 C won by 190 us and is over the 390 C trip. Preheat 18 Hz is under "
                "the 24 Hz cap but is not clearance. REJECT: hold 0 t/h until bath <= 390 C.",
            ),
            (
                "constraint_checked",
                OrderedDict(
                    [
                        (
                            "salt_bath_C",
                            OrderedDict(
                                [
                                    ("trip", 390.0),
                                    ("observed", 412.0),
                                    ("executed_t_h", 0.0),
                                ]
                            ),
                        ),
                        (
                            "order_evidence",
                            OrderedDict(
                                [
                                    ("margin_us", 190),
                                    ("combined_jitter_us", 56),
                                    ("ratio", 3.39),
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
            ("name", "feed_hold_bath"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("feed_t_h", 0.0),
                        ("bath_C", 412.0),
                        ("hold", True),
                    ]
                ),
            ),
            (
                "gate_effect",
                "REJECT: feed 6.4 -> 0 t/h. Routing relay.tc.salt -> policy.hold_reject. "
                "Do not feed into the 412 C flare.",
            ),
        ]
    )
    future = OrderedDict(
        [
            (
                "summary",
                "Correct REJECT held PA-2 at 0 t/h while salt bath 412 C decayed. Encoder-as-clearance "
                "would have fed 6.4 t/h into the flare. Pad recycle 8 min.",
            ),
            (
                "state_delta",
                OrderedDict(
                    [
                        ("feed", "held at 0 t/h"),
                        ("bath", "flare decaying under trip after hold"),
                        ("reactor", "no hotspot runaway"),
                        ("pad", "8 min recycle"),
                    ]
                ),
            ),
            (
                "surprises",
                [
                    "Pad injects encoder 80-120 us before bath envelope finish; that is loop lag, not a false salt TC.",
                    "Delayed (8 min): pad recycle restacks the reactor after bath < 390 C.",
                ],
            ),
            (
                "race_result",
                OrderedDict(
                    [
                        ("winner", "tc.salt.c (4.120 ms, 412 C)"),
                        ("loser", "enc.preheat.hz (4.310 ms, 18 Hz)"),
                        ("margin_us", 190),
                        (
                            "counterfactual_if_reversed",
                            "Encoder-first by < 190 us would have treated 18 Hz as clearance and "
                            "fed into the 412 C flare. The REJECT is still required; reversal "
                            "only delays the bath bind.",
                        ),
                    ]
                ),
            ),
            ("reward_inflection_t_us", 5220),
            (
                "reward_inflection_note",
                "Safety credit lands at the correct REJECT (5.220 ms, tick 4). Pad recycle is delayed surprise.",
            ),
            ("delayed_surprise_s", 480.0),
            ("pad_recycle_s", 480),
        ]
    )
    ras = raster_core(
        44,
        104,
        22,
        101,
        routing(
            "relay.tc.salt",
            "policy.hold_reject",
            [
                ("relay.tc.salt", "policy.hold_reject", 0.75),
                ("relay.enc.preheat", "policy.feed_go", 0.17),
            ],
            "dopamine",
            0.06,
            "bath_trip_stdp; DA tags the hold_reject bind at the salt-bath win",
        ),
        excerpt,
    )
    gate = OrderedDict(
        [
            ("decision_window_ms", 0.28),
            ("decision", "REJECT"),
            (
                "populations",
                [
                    pop("hold_reject", 64, 0.50, 180.0, 3),
                    pop("feed_go", 64, 0.80, 8.0, 0),
                    pop("bath_trip_veto", 32, 0.70),
                ],
            ),
        ]
    )
    return wrap_record(
        "ttf-r68-358",
        "Oxylene-Ness phthalic HIL / PA-2: salt bath 412 C beats air-preheat encoder 18 Hz by 190 us; "
        "correct REJECT holds the reactor",
        state,
        spikes,
        proposed,
        safety,
        executed,
        future,
        ticks,
        "Correct REJECT. Salt bath 412 > 390 trip beats in-band preheat speed. total +0.78 = "
        "0.10 + 0.40 + 0.12 + 0.10 + 0.06.",
        ras,
        gate,
        "phthalic-anhydride-reactor",
        [
            "reject",
            "hil-pad",
            "bath-vs-encoder",
            "hotspot-hold",
            "sidecar-convictable",
            "hil",
        ],
        "Teaches a probe that an in-band air-preheat encoder is not hotspot clearance when "
        "salt bath is over trip and routing.table[0].to is policy.hold_reject.",
        3,
    )


def record_359():
    ticks = [
        tick(2352, 0.06, 0.04, 0.03, 0.02, 0.01),
        tick(5880, 0.10, 0.06, 0.04, 0.02, 0.02),
        tick(6110, 0.06, 0.04, 0.02, 0.01, 0.01),
        tick(6800, 0.12, 0.08, 0.05, 0.03, 0.02),
        tick(7160, 0.05, 0.04, 0.02, 0.01, 0.01),
        tick(540000000, 0.03, 0.02, 0.02, 0.01, 0.01),
    ]
    params = OrderedDict(
        [
            ("blast_nm3_min", 1850.0),
            ("hearth_C", 1380.0),
            ("furnace_id", 6),
            ("hold", False),
        ]
    )
    spikes = [
        spike("ft.burden.ctx", 1.420, 0.42),
        spike("ir.hearth.c", 3.040, 0.58),
        spike("ir.bosh.smear", 4.580, 0.50),
        spike("ir.hearth.c", 5.880, 1.28),
        spike("ir.bosh.smear", 6.110, 1.10),
        spike("ctrl.gate", 6.800, 0.96),
        spike("ir.hearth.c", 9.200, 0.74),
        spike("ir.bosh.smear", 12.800, 0.60),
        spike("ctrl.gate", 18.400, 0.82),
        spike("ir.hearth.c", 24.600, 0.55),
        spike("ft.burden.ctx", 27.400, 0.40),
    ]
    excerpt = independent_excerpt(68359, 64, 28000, 12, spike_avoid_us(spikes))
    state = OrderedDict(
        [
            (
                "description",
                "Blast furnace BF-6 of the Pyrolusite-Wath ferromanganese train is holding 1850 "
                "Nm3/min when a hearth IR at 1380 C races a bosh-IR smear that still claims over-temp. "
                "Commanded 1850 Nm3/min and 1380 C sit 150 Nm3/min and 100 C inside the legal "
                "envelopes. The hearth-IR win only ratifies the blast already in the tuyeres.",
            ),
            ("domain", "ferromanganese-blast-furnace"),
            ("sim_or_real", "simulated"),
            (
                "goal",
                "Finish the ferromanganese pass on Pyrolusite-Wath, keep hearth IR <= 1480 C and "
                "blast >= 1700 Nm3/min, and leave bosh draft in spec.",
            ),
            ("t0_us", 1762300000000359),
            ("gate_latency_us", 920),
            ("race_window_us", 360),
            ("race_window_rel_ms", [5.880, 6.240]),
            (
                "race",
                OrderedDict(
                    [
                        (
                            "contenders",
                            [
                                "ir.hearth.c 1380 C ferromanganese hearth",
                                "ir.bosh.smear over-temp claim",
                            ],
                        ),
                        (
                            "semantics",
                            "Hearth-IR-first confirms the already-legal 1850 Nm3/min / 1380 C pass; "
                            "smear-first would have treated the hearth IR as a smear echo and looked "
                            "for an extra hold the furnace does not need.",
                        ),
                        (
                            "window_derivation",
                            "360 us = one 1D-hearth IR kernel step versus the bosh-IR publisher "
                            "on this rigid blast-furnace train.",
                        ),
                        (
                            "order_evidence_note",
                            "Margin 230 us vs combined jitter 70 us (hearth 32 + bosh 38): 3.3x over "
                            "a 2.0x trust floor. Reversing order by < 230 us would not make the "
                            "proposed pass illegal; it would only have delayed confirmation.",
                        ),
                    ]
                ),
            ),
            (
                "sensors",
                [
                    "hearth IR, 32 us jitter",
                    "bosh IR smear, 38 us jitter",
                    "blast-flow encoder (context)",
                    "top-gas PT (context)",
                ],
            ),
            (
                "constraints",
                OrderedDict(
                    [
                        ("hearth_cap_C", 1480.0),
                        ("observed_hearth_C", 1380.0),
                        ("blast_floor_nm3_min", 1700.0),
                        ("proposed_blast_nm3_min", 1850.0),
                    ]
                ),
            ),
            (
                "simulation",
                OrderedDict(
                    [
                        (
                            "solver",
                            "1D blast-furnace hearth-bosh kernel + shrinking-core MnO2 pellet, seed 68; 14 axial nodes; NOT lumped tank, NOT a fluid-LES field",
                        ),
                        (
                            "fidelity_limits",
                            "No radial hanging or tuyere burnout; hearths are rigid temperature sources. Raster is kernelized events, not an independent LIF.",
                        ),
                    ]
                ),
            ),
            (
                "episode_steps",
                [
                    "1. Pyrolusite-Wath furnace indexed; BF-6 holding 1850 Nm3/min at 1380 C hearth.",
                    "2. Caps: hearth 1480 C, blast floor 1700 Nm3/min; both proposed values inside.",
                    "3. Burden precursor at 1.420 ms.",
                    "4. Race window [5.880, 6.240] ms.",
                    "5. Hearth IR 1380 C at 5.880 ms (winner).",
                    "6. Bosh IR smear at 6.110 ms (loser by 230 us).",
                    "7. Gate at 6.800 ms: ACCEPT 1850 Nm3/min / 1380 C already legal.",
                    "8. Pass continues; no extra hold.",
                    "9. 9 min survey confirms bosh draft still in spec.",
                    "10. QA: ACCEPT params identical to proposed.",
                ],
            ),
        ]
    )
    proposed = OrderedDict(
        [
            ("name", "bf_1850_thold"),
            ("parameters", params),
            (
                "evidence",
                OrderedDict(
                    [
                        ("hearth_C", 1380.0),
                        ("hearth_cap_C", 1480.0),
                        ("blast_nm3_min", 1850.0),
                        ("blast_floor_nm3_min", 1700.0),
                        ("race_margin_us", 230),
                        ("combined_jitter_us", 70),
                        ("t_gate_us", 6800),
                    ]
                ),
            ),
            (
                "basis",
                "Planner proposes 1850 Nm3/min because hearth 1380 C is 100 C under the 1480 C cap "
                "and blast is 150 Nm3/min over the 1700 Nm3/min floor.",
            ),
        ]
    )
    safety = OrderedDict(
        [
            ("decision", "ACCEPT"),
            ("correctness", "correct"),
            (
                "rationale",
                "Hearth 1380 C won by 230 us and is under 1480 C. Blast 1850 Nm3/min is over "
                "1700 Nm3/min. ACCEPT the already-legal pass; bosh IR smear is not a cap violation.",
            ),
            (
                "constraint_checked",
                OrderedDict(
                    [
                        (
                            "hearth_C",
                            OrderedDict(
                                [
                                    ("cap", 1480.0),
                                    ("observed", 1380.0),
                                    ("executed_blast_nm3_min", 1850.0),
                                ]
                            ),
                        ),
                        (
                            "order_evidence",
                            OrderedDict(
                                [
                                    ("margin_us", 230),
                                    ("combined_jitter_us", 70),
                                    ("ratio", 3.29),
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
            ("name", "bf_1850_thold"),
            ("parameters", params),
            (
                "gate_effect",
                "ACCEPT: blast 1850 Nm3/min and hearth 1380 C unchanged. Routing relay.ir.hearth "
                "-> policy.go_accept.",
            ),
        ]
    )
    future = OrderedDict(
        [
            (
                "summary",
                "Correct ACCEPT left BF-6 at 1850 Nm3/min / 1380 C. Bosh IR smear did not justify a "
                "hold. 9 min survey confirmed draft in spec.",
            ),
            (
                "state_delta",
                OrderedDict(
                    [
                        ("furnace", "still 1850 Nm3/min / 1380 C"),
                        ("bosh", "in spec after survey"),
                        ("train", "ferromanganese continues"),
                        ("hold", "none applied"),
                    ]
                ),
            ),
            (
                "surprises",
                [
                    "Bosh IR smear is an off-gas optical claim, not a hearth-temperature violation.",
                    "Delayed (9 min): survey restacks BF-6 without a recovery hold.",
                ],
            ),
            (
                "race_result",
                OrderedDict(
                    [
                        ("winner", "ir.hearth.c (5.880 ms, 1380 C)"),
                        ("loser", "ir.bosh.smear (6.110 ms, over-temp claim)"),
                        ("margin_us", 230),
                        (
                            "counterfactual_if_reversed",
                            "Smear-first by < 230 us would only delay confirmation. The pass stays "
                            "legal either way; ACCEPT is still required.",
                        ),
                    ]
                ),
            ),
            ("reward_inflection_t_us", 6800),
            (
                "reward_inflection_note",
                "Task credit lands at the ACCEPT (6.800 ms, tick 4). Survey is delayed surprise.",
            ),
            ("delayed_surprise_s", 540.0),
            ("survey_s", 540),
        ]
    )
    ras = raster_core(
        28,
        64,
        36,
        65,
        routing(
            "relay.ir.hearth",
            "policy.go_accept",
            [
                ("relay.ir.hearth", "policy.go_accept", 0.69),
                ("relay.ir.bosh", "policy.smear_hold", 0.20),
            ],
            "serotonin",
            0.07,
            "legal_bf_stdp; 5-HT tags the go_accept bind at the hearth-IR win",
        ),
        excerpt,
    )
    gate = OrderedDict(
        [
            ("decision_window_ms", 0.36),
            ("decision", "ACCEPT"),
            (
                "populations",
                [
                    pop("go_accept", 40, 0.50, 180.0, 3),
                    pop("smear_hold", 40, 0.80, 10.0, 0),
                    pop("hearth_cap_veto", 20, 0.75),
                ],
            ),
        ]
    )
    return wrap_record(
        "ttf-r68-359",
        "Pyrolusite-Wath BF / BF-6: hearth IR 1380 C beats bosh smear by 230 us; ACCEPT "
        "already-legal 1850 Nm3/min pass",
        state,
        spikes,
        proposed,
        safety,
        executed,
        future,
        ticks,
        "Correct ACCEPT of an already-legal 1D blast-furnace hearth-bosh pass. total +1.06 = "
        "0.42 + 0.28 + 0.18 + 0.10 + 0.08.",
        ras,
        gate,
        "ferromanganese-blast-furnace",
        [
            "accept",
            "already-legal",
            "simulated-bf-train",
            "hearth-vs-bosh",
            "sidecar-convictable",
            "simulated",
        ],
        "Teaches that a hearth IR under cap can confirm an already-legal blast-furnace pass without "
        "a bosh-IR smear becoming a hold.",
        4,
    )


def record_360():
    ticks = [
        tick(1824, 0.06, 0.04, 0.03, 0.02, 0.01),
        tick(4560, 0.10, 0.08, 0.04, 0.02, 0.02),
        tick(4780, 0.06, 0.04, 0.02, 0.02, 0.01),
        tick(5340, 0.12, 0.08, 0.05, 0.04, 0.02),
        tick(5680, 0.06, 0.05, 0.02, 0.01, 0.01),
        tick(360000000, 0.04, 0.03, 0.02, 0.01, 0.01),
    ]
    params = OrderedDict(
        [
            ("current_kA", 32.0),
            ("elec_C", 68.4),
            ("cell_id", 8),
            ("hold", False),
        ]
    )
    spikes = [
        spike("enc.cell.ctx", 0.940, 0.41),
        spike("rtd.elec.c", 2.180, 0.60),
        spike("ir.header.glint", 3.120, 0.51),
        spike("rtd.elec.c", 4.560, 1.30),
        spike("ir.header.glint", 4.780, 1.12),
        spike("ctrl.gate", 5.340, 0.97),
        spike("rtd.elec.c", 7.200, 0.78),
        spike("ir.header.glint", 10.400, 0.62),
        spike("ctrl.gate", 15.200, 0.84),
        spike("rtd.elec.c", 20.800, 0.54),
    ]
    excerpt = independent_excerpt(68360, 52, 22000, 11, spike_avoid_us(spikes))
    state = OrderedDict(
        [
            (
                "description",
                "Chlorate cell bank CB-8 at Chlorate-Beck is holding 32 kA when an electrolyte RTD "
                "at 68.4 C races a header-IR glint that still claims over-temp. Commanded 32 kA and "
                "68.4 C sit 4 kA over the 28 kA floor and 11.6 C under the 80 C cap. The RTD win "
                "only ratifies the current already on the cells.",
            ),
            ("domain", "sodium-chlorate-cell"),
            ("sim_or_real", "designed"),
            (
                "goal",
                "Run CB-8 at 32 kA, keep electrolyte <= 80 C and header IR <= 95 C, "
                "and leave the bank on schedule.",
            ),
            ("t0_us", 1762300000000360),
            ("gate_latency_us", 780),
            ("race_window_us", 340),
            ("race_window_rel_ms", [4.560, 4.900]),
            (
                "race",
                OrderedDict(
                    [
                        (
                            "contenders",
                            [
                                "rtd.elec.c 68.4 C chlorate electrolyte",
                                "ir.header.glint over-temp claim",
                            ],
                        ),
                        (
                            "semantics",
                            "RTD-first confirms the already-legal 32 kA / 68.4 C pass; glint-first "
                            "would have treated the RTD as a header echo and looked for an extra hold "
                            "the bank does not need.",
                        ),
                        (
                            "window_derivation",
                            "340 us = one electrolyte RTD slot versus the header-IR publisher on this "
                            "chlorate bus.",
                        ),
                        (
                            "order_evidence_note",
                            "Margin 220 us vs combined jitter 64 us (RTD 28 + header 36): 3.4x over "
                            "a 2.0x trust floor. Reversing order by < 220 us would not make the "
                            "proposed pass illegal; it would only have delayed confirmation.",
                        ),
                    ]
                ),
            ),
            (
                "sensors",
                [
                    "electrolyte RTD, 28 us jitter",
                    "header IR glint, 36 us jitter",
                    "cell-current encoder (context)",
                    "pH probe (context)",
                ],
            ),
            (
                "constraints",
                OrderedDict(
                    [
                        ("elec_cap_C", 80.0),
                        ("observed_elec_C", 68.4),
                        ("current_floor_kA", 28.0),
                        ("proposed_current_kA", 32.0),
                        ("header_cap_C", 95.0),
                        ("observed_header_glint_C", 88.0),
                    ]
                ),
            ),
            (
                "episode_steps",
                [
                    "1. Cell bank CB-8 indexed on Chlorate-Beck; current armed 32 kA pass.",
                    "2. Caps: electrolyte 80 C, header 95 C, current floor 28 kA.",
                    "3. Encoder precursor at 0.940 ms.",
                    "4. Race window [4.560, 4.900] ms.",
                    "5. Electrolyte 68.4 C at 4.560 ms (winner).",
                    "6. Header IR glint at 4.780 ms (loser by 220 us).",
                    "7. Gate at 5.340 ms: ACCEPT 32 kA / 68.4 C already legal.",
                    "8. Pass continues; no extra hold.",
                    "9. 6 min dwell confirms header still under 95 C.",
                    "10. QA: ACCEPT params identical to proposed.",
                ],
            ),
        ]
    )
    proposed = OrderedDict(
        [
            ("name", "pass_32ka"),
            ("parameters", params),
            (
                "evidence",
                OrderedDict(
                    [
                        ("elec_C", 68.4),
                        ("elec_cap_C", 80.0),
                        ("current_kA", 32.0),
                        ("current_floor_kA", 28.0),
                        ("header_glint_C", 88.0),
                        ("header_cap_C", 95.0),
                        ("race_margin_us", 220),
                        ("combined_jitter_us", 64),
                        ("t_gate_us", 5340),
                    ]
                ),
            ),
            (
                "basis",
                "Planner proposes a 32 kA pass because electrolyte 68.4 C is 11.6 C under the 80 C "
                "cap and header glint 88 C is under 95 C.",
            ),
        ]
    )
    safety = OrderedDict(
        [
            ("decision", "ACCEPT"),
            ("correctness", "correct"),
            (
                "rationale",
                "Electrolyte 68.4 C won by 220 us and is under 80 C. Header glint 88 C is under "
                "95 C. Current 32 kA is over the 28 kA floor. ACCEPT the already-legal pass.",
            ),
            (
                "constraint_checked",
                OrderedDict(
                    [
                        (
                            "elec_C",
                            OrderedDict(
                                [
                                    ("cap", 80.0),
                                    ("observed", 68.4),
                                    ("executed_current_kA", 32.0),
                                ]
                            ),
                        ),
                        (
                            "order_evidence",
                            OrderedDict(
                                [
                                    ("margin_us", 220),
                                    ("combined_jitter_us", 64),
                                    ("ratio", 3.44),
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
            ("name", "pass_32ka"),
            ("parameters", params),
            (
                "gate_effect",
                "ACCEPT: 32 kA pass and 68.4 C unchanged. Routing relay.rtd.elec -> "
                "policy.go_accept.",
            ),
        ]
    )
    future = OrderedDict(
        [
            (
                "summary",
                "Correct ACCEPT left CB-8 on a 32 kA / 68.4 C pass. Header IR glint did not "
                "justify a hold. 6 min dwell confirmed header still under 95 C.",
            ),
            (
                "state_delta",
                OrderedDict(
                    [
                        ("bank", "still 32 kA / 68.4 C"),
                        ("header", "88 C under 95 cap"),
                        ("circuit", "on schedule"),
                        ("hold", "none applied"),
                    ]
                ),
            ),
            (
                "surprises",
                [
                    "Header IR 88 C glint is residual bus-bar shine, not an electrolyte trip.",
                    "Delayed (6 min): dwell restacks CB-8 without a recovery hold.",
                ],
            ),
            (
                "race_result",
                OrderedDict(
                    [
                        ("winner", "rtd.elec.c (4.560 ms, 68.4 C)"),
                        ("loser", "ir.header.glint (4.780 ms, 88 C)"),
                        ("margin_us", 220),
                        (
                            "counterfactual_if_reversed",
                            "Glint-first by < 220 us would only delay confirmation. The pass stays "
                            "legal either way; ACCEPT is still required.",
                        ),
                    ]
                ),
            ),
            ("reward_inflection_t_us", 5340),
            (
                "reward_inflection_note",
                "Task credit lands at the ACCEPT (5.340 ms, tick 4). Dwell is delayed surprise.",
            ),
            ("delayed_surprise_s", 360.0),
            ("dwell_s", 360),
        ]
    )
    ras = raster_core(
        22,
        52,
        40,
        46,
        routing(
            "relay.rtd.elec",
            "policy.go_accept",
            [
                ("relay.rtd.elec", "policy.go_accept", 0.67),
                ("relay.ir.header", "policy.glint_hold", 0.19),
            ],
            "adenosine",
            0.09,
            "legal_pass_stdp; adenosine tags the go_accept bind at the electrolyte-RTD win",
        ),
        excerpt,
    )
    gate = OrderedDict(
        [
            ("decision_window_ms", 0.34),
            ("decision", "ACCEPT"),
            (
                "populations",
                [
                    pop("go_accept", 36, 0.50, 200.0, 2),
                    pop("glint_hold", 36, 0.80, 12.0, 0),
                    pop("elec_cap_veto", 18, 0.75),
                ],
            ),
        ]
    )
    return wrap_record(
        "ttf-r68-360",
        "Chlorate-Beck bank / CB-8: electrolyte 68.4 C beats header glint 88 C by 220 us; "
        "ACCEPT already-legal 32 kA pass",
        state,
        spikes,
        proposed,
        safety,
        executed,
        future,
        ticks,
        "Correct ACCEPT of an already-legal sodium-chlorate pass. total +1.14 = "
        "0.44 + 0.32 + 0.18 + 0.12 + 0.08.",
        ras,
        gate,
        "sodium-chlorate-cell",
        [
            "accept",
            "already-legal",
            "rtd-vs-header-glint",
            "sidecar-convictable",
            "designed",
        ],
        "Teaches that an electrolyte RTD under cap can confirm an already-legal chlorate pass without "
        "a header-IR glint becoming a hold.",
        5,
    )
