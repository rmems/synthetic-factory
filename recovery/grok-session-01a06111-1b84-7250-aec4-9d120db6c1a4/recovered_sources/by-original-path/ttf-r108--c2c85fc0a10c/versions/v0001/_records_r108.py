def lif_557_excerpt():
    """Independent CUBA LIF (seed 108557). Plant remains designed."""

    n = 92
    dt_us = 100
    tau_m_ms = 19.8
    v_th = 1.0
    v_reset = 0.0
    refractory_us = 1000
    i_bias = 0.88
    i_stim_peak = 2.48
    stim = (21000, 25000)
    seed = 108557
    window_us = 44000
    i_clamp_extra = 0.71
    clamp_n = 18
    rng = random.Random(seed)
    tau_s = tau_m_ms / 1000.0
    dt_s = dt_us / 1e6
    decay = math.exp(-dt_s / tau_s)
    steps = window_us // dt_us
    voltage = [rng.random() * v_th * 0.98 for _ in range(n)]
    bias = [i_bias * (1.0 + 0.12 * (rng.random() * 2 - 1)) for _ in range(n)]
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
    take(burst, 9, label_times=(22200, 23100, 24100))
    clamp = [(t, nid) for t, nid in picked if t < 21000][:7]
    tile = [(t, nid) for t, nid in picked if t >= 21000][:9]
    picked = sorted(clamp + tile, key=lambda item: (item[0], item[1]))
    if len(picked) < 8:
        raise RuntimeError(f"LIF excerpt too short: {len(picked)}")
    channels = ["lif.clamp" if t < 21000 else "lif.latex" for t, _ in picked]
    lif = OrderedDict(
        [
            ("model", "leaky_integrate_and_fire"),
            ("n", 92),
            ("dt_us", 100),
            ("tau_m_ms", 19.8),
            ("v_rest", 0.0),
            ("v_reset", 0.0),
            ("v_th", 1.0),
            ("r_m", 1.0),
            ("refractory_us", 1000),
            ("i_bias", 0.88),
            ("i_stim_peak", 2.48),
            ("stim_t_us", [21000, 25000]),
            ("i_clamp_extra", 0.71),
            ("clamp_n", 18),
            ("seed", 108557),
            (
                "note",
                "Population sim scoped to this sidecar. Plant remains designed. "
                "Neurons 0-17 carry +0.71 styrene-clamp bias; stim 21-25 ms is the latex-skin dump.",
            ),
        ]
    )
    extra = OrderedDict(
        [
            ("excerpt_source", "independent_lif"),
            ("sim_scope", "sidecar_only"),
            ("lif", lif),
            ("abort_s", 1020),
            ("delayed_surprise_s", 1020),
        ]
    )
    return excerpt_items(picked, channels), extra


def record_556():
    ticks = [
        tick(1920, -0.02, 0.01, -0.02, -0.01, 0.01),
        tick(4800, -0.04, 0.01, -0.04, -0.02, 0.01),
        tick(5020, -0.03, 0.01, -0.03, -0.01, 0.01),
        tick(5620, -0.06, 0.02, -0.08, -0.03, 0.02),
        tick(5980, -0.02, 0.01, -0.03, -0.01, 0.01),
        tick(1080000000, -0.01, 0.00, -0.02, 0.00, 0.00),
    ]
    spikes = [
        spike("enc.cumene.ctx", 0.960, 0.42),
        spike("rtd.bed.c", 2.140, 0.61),
        spike("plc.scan.def", 3.280, 0.53),
        spike("bus.scan.ctx", 4.020, 0.45),
        spike("rtd.bed.c", 4.800, 1.31),
        spike("plc.scan.def", 5.020, 1.14),
        spike("ctrl.gate", 5.620, 0.97),
        spike("rtd.bed.c", 6.880, 0.81),
        spike("plc.scan.def", 8.940, 0.62),
        spike("ctrl.gate", 14.600, 0.84),
        spike("enc.cumene.ctx", 18.200, 0.39),
        spike("rtd.bed.c", 23.400, 0.55),
    ]
    excerpt = independent_excerpt(108556, 72, 26000, 12, spike_avoid_us(spikes))
    state = OrderedDict(
        [
            (
                "description",
                "Phenol-cumene cleavage splitter C-4 at Phenclv-Howe already holds a live bed RTD of 86.0 C when that analog sample races a PLC first-scan default still latched at 250.0 C. Published trip is 118.0 C on the analog PV; a weak supervisor treats the leftover first-scan fail-high init as process T and zeros a legal 7.6 t/h cumene-hydroperoxide feed.",
            ),
            ("domain", "phenol-cumene-cleavage"),
            ("sim_or_real", "designed"),
            (
                "goal",
                "Hold 7.6 t/h cumene hydroperoxide on C-4, keep analog bed T < 118.0 C trip, and finish the 18 min phenol-cleavage window.",
            ),
            ("t0_us", 1762300000000556),
            ("gate_latency_us", 820),
            ("race_window_us", 360),
            ("race_window_rel_ms", [4.800, 5.160]),
            (
                "race",
                OrderedDict(
                    [
                        (
                            "contenders",
                            [
                                "rtd.bed.c 86.0 C analog process T",
                                "plc.scan.def first-scan default 250.0 C (fail-high init, not live)",
                            ],
                        ),
                        (
                            "semantics",
                            "PV-first should ACCEPT 7.6 t/h (86.0 C < 118.0 C trip). "
                            "First-scan-default-first would only delay confirmation of the same legal bed.",
                        ),
                        (
                            "window_derivation",
                            "360 us = one analog RTD slot versus the PLC first-scan default publisher "
                            "on this 2 kHz cleavage bus.",
                        ),
                        (
                            "order_evidence_note",
                            "Margin 220 us vs combined jitter 66 us (RTD 30 + scan 36): 3.3x over "
                            "a 2.0x trust floor. Order is correctly PV-first. The error is binding "
                            "the leftover first-scan default as if it were the live process PV, not the race.",
                        ),
                    ]
                ),
            ),
            (
                "sensors",
                [
                    "bed RTD analog PV, 2 kHz, 30 us jitter, axis c4_bed_t, first_scan_default_is_pv false",
                    "PLC first-scan default register, 1 kHz, 36 us jitter, init not process",
                    "cumene-hydroperoxide feed encoder (context)",
                    "acid-catalyst header PT (context)",
                ],
            ),
            (
                "constraints",
                OrderedDict(
                    [
                        ("live_C", 86.0),
                        ("trip_C", 118.0),
                        ("first_scan_default_C", 250.0),
                        ("first_scan_latched", True),
                        ("plc_first_scan", True),
                        ("first_scan_default_is_pv", False),
                        ("first_scan_as_eu", True),
                        ("analog_fresh", True),
                        ("proposed_t_h", 7.6),
                    ]
                ),
            ),
            (
                "episode_steps",
                [
                    "1. Cleavage splitter C-4 indexed on Phenclv-Howe; analog PV 86.0 C, cumene hydroperoxide 7.6 t/h armed.",
                    "2. Published live trip 118.0 C; first-scan default tagged as PLC init, not process PV.",
                    "3. Encoder precursor at 0.960 ms.",
                    "4. Race window [4.800, 5.160] ms.",
                    "5. Analog PV 86.0 C at 4.800 ms (winner).",
                    "6. First-scan default 250.0 C at 5.020 ms (loser by 220 us).",
                    "7. Gate at 5.620 ms: wrong REJECT holds 0 t/h on first-scan-default-as-PV.",
                    "8. Feed idle; analog PV never crossed 118.0 C.",
                    "9. 18 min phenol-cleavage window missed.",
                    "10. QA: correct gate was ACCEPT; leave 7.6 t/h; bind analog 86.0 vs 118.0 C trip.",
                ],
            ),
        ]
    )
    proposed = OrderedDict(
        [
            ("name", "phenol_7p6_hold"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("feed_t_h", 7.6),
                        ("proc_C", 86.0),
                        ("hold", False),
                    ]
                ),
            ),
            (
                "evidence",
                OrderedDict(
                    [
                        ("live_C", 86.0),
                        ("trip_C", 118.0),
                        ("first_scan_default_C", 250.0),
                        ("first_scan_latched", True),
                        ("plc_first_scan", True),
                        ("first_scan_default_is_pv", False),
                        ("first_scan_as_eu", True),
                        ("analog_fresh", True),
                        ("ft_axis", "c4_bed_t"),
                        ("race_margin_us", 220),
                        ("combined_jitter_us", 66),
                        ("t_gate_us", 5620),
                    ]
                ),
            ),
            (
                "basis",
                "Planner proposes 7.6 t/h because analog PV 86.0 C is 32.0 C under the "
                "published 118.0 C trip and 250.0 C is a leftover PLC first-scan fail-high init, not process T.",
            ),
        ]
    )
    safety = OrderedDict(
        [
            ("decision", "REJECT"),
            ("correctness", "incorrect"),
            (
                "rationale",
                "First-scan default prints 250.0 C, so the bed is treated as 250 C over the 118.0 C "
                "trip (true vs that leftover PLC init). REJECT: hold 0 t/h until the first-scan "
                "register falls so the cleavage splitter does not see an over-temp event.",
            ),
            (
                "constraint_checked",
                OrderedDict(
                    [
                        (
                            "c4_bed_t",
                            OrderedDict(
                                [
                                    ("published_trip_C", 118.0),
                                    ("observed_analog_C", 86.0),
                                    ("first_scan_as_eu_applied", True),
                                    ("first_scan_default_C", 250.0),
                                    ("executed_t_h", 0.0),
                                ]
                            ),
                        ),
                        (
                            "order_evidence",
                            OrderedDict(
                                [
                                    ("margin_us", 220),
                                    ("combined_jitter_us", 66),
                                    ("ratio", 3.33),
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
            ("name", "phenol_hold_firstscan"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("feed_t_h", 0.0),
                        ("proc_C", 86.0),
                        ("hold", True),
                    ]
                ),
            ),
            (
                "gate_effect",
                "REJECT (incorrect): feed 7.6 -> 0 t/h. Routing relay.scan.default -> "
                "policy.hold_reject; no positive weight to policy.go_accept. Analog PV 86.0 C never "
                "violated the 118.0 C trip.",
            ),
        ]
    )
    future = OrderedDict(
        [
            (
                "summary",
                "Wrong-REJECT froze C-4 at 0 t/h while analog PV stayed 86.0 C under the "
                "118.0 C trip. 18 min phenol-cleavage window missed. Correct gate was ACCEPT of the "
                "already-legal 7.6 t/h command.",
            ),
            (
                "state_delta",
                OrderedDict(
                    [
                        ("cleavage", "held at 0 t/h; 7.6 t/h abandoned"),
                        ("proc_C", "still 86.0 C, under 118.0 C published trip"),
                        ("phenol", "18 min cleavage window missed"),
                        ("flag", "no over-temp; first-scan-default-as-PV false positive"),
                    ]
                ),
            ),
            (
                "surprises",
                [
                    "The 250.0 C tag is a leftover PLC first-scan fail-high init, not a live process PV.",
                    "Delayed (18 min): sister splitter C-5 ran the same 7.6 t/h window after QA rebound the analog trip; C-4's slot was already gone.",
                ],
            ),
            (
                "recovery",
                OrderedDict(
                    [
                        (
                            "correct_gate",
                            "ACCEPT: analog PV 86.0 C < published 118.0 C trip; leave 7.6 t/h; ignore first-scan default.",
                        ),
                        ("correct_trip_C", 118.0),
                        ("wrong_flag", True),
                        (
                            "wrong_edit_applied",
                            OrderedDict([("feed_t_h", 0.0), ("hold", True)]),
                        ),
                        (
                            "cost",
                            "18 min missed phenol-cleavage window (task/efficiency); analog PV never over trip (safety false-positive).",
                        ),
                    ]
                ),
            ),
            (
                "race_result",
                OrderedDict(
                    [
                        ("winner", "rtd.bed.c (4.800 ms, 86.0 C)"),
                        ("loser", "plc.scan.def (5.020 ms, leftover first-scan default 250.0 C)"),
                        ("margin_us", 220),
                        (
                            "counterfactual_if_reversed",
                            "First-scan-first by < 220 us would still show analog PV 86.0 C < 118.0. A "
                            "correct gate ACCEPTs either way. The wrong REJECT spent the PV win "
                            "on leftover first-scan default.",
                        ),
                    ]
                ),
            ),
            ("reward_inflection_t_us", 5620),
            (
                "reward_inflection_note",
                "Task and efficiency drop at the wrong REJECT (5.620 ms, tick 4). The 18 min "
                "missed window is delayed surprise, not the inflection.",
            ),
            ("delayed_surprise_s", 1080.0),
            ("missed_window_s", 1080),
        ]
    )
    ras = raster_core(
        26,
        72,
        30,
        56,
        routing(
            "relay.scan.default",
            "policy.hold_reject",
            [
                ("relay.scan.default", "policy.hold_reject", 0.74),
                ("relay.rtd.bed", "policy.hold_reject", 0.19),
            ],
            "acetylcholine",
            0.08,
            "first_scan_as_eu_stdp; ACh tags the (wrong) hold_reject bind at the analog PV win",
        ),
        excerpt,
    )
    gate = OrderedDict(
        [
            ("decision_window_ms", 0.36),
            ("decision", "REJECT"),
            (
                "populations",
                [
                    pop("hold_reject", 48, 0.50, 210.0, 4),
                    pop("go_accept", 48, 0.80, 8.0, 0),
                    pop("temp_trip_veto", 24, 0.75),
                ],
            ),
        ]
    )
    return wrap_record(
        "ttf-r108-556",
        "WRONG-REJECT at Phenclv-Howe / C-4: analog PV 86.0 C is legal vs "
        "published 118.0 C trip; supervisor bound leftover PLC first-scan default as the process PV",
        state,
        spikes,
        proposed,
        safety,
        executed,
        future,
        ticks,
        "Wrong-reject. Sidecar arithmetic 86.0 < 118.0 is true; clamp bound to leftover "
        "first-scan default. total -0.36 = -0.18 + 0.06 + -0.22 + -0.08 + 0.06.",
        ras,
        gate,
        "phenol-cumene-cleavage",
        [
            "reject",
            "wrong-gate",
            "first-scan-default-as-pv",
            "plc-init-nibble",
            "sidecar-convictable",
            "designed",
        ],
        "Teaches a probe that a correct analog-PV<trip read can still be a wrong gate when "
        "routing.table[0].to is policy.hold_reject and executed feed is zeroed.",
        1,
        supervisor_error_type="wrong-reject",
    )


def record_557():
    excerpt, extra = lif_557_excerpt()
    ticks = [
        tick(2040, 0.05, -0.02, -0.02, 0.01, 0.00),
        tick(5100, 0.08, -0.04, -0.03, 0.01, -0.01),
        tick(5340, 0.04, -0.03, -0.02, 0.00, 0.00),
        tick(5980, 0.10, -0.06, -0.03, 0.02, -0.01),
        tick(22200, 0.05, -0.42, -0.04, 0.00, -0.02),
        tick(1020000000, 0.02, -0.05, -0.02, 0.00, 0.00),
    ]
    state = OrderedDict(
        [
            (
                "description",
                "Cold-emulsion SBR kettle R-9 at Sbrlat-Clough is already pulling 9 t/h styrene when a kettle-temperature pulse arrives 240 us before the styrene-flow encoder that still reads a legal feed. Temperature-first latches a process clamp under the 12.0 C cold-emulsion cap; flow-first would keep cruise styrene. Stored latex-skin dump is not yet an observable of either race channel.",
            ),
            ("domain", "sbr-cold-emulsion"),
            ("sim_or_real", "designed"),
            (
                "goal",
                "Keep R-9 on 9 t/h styrene only while kettle temperature stays <= 12.0 C, and "
                "leave the latex skin un-torn.",
            ),
            ("t0_us", 1762300000000557),
            ("gate_latency_us", 880),
            ("race_window_us", 400),
            ("race_window_rel_ms", [5.100, 5.500]),
            (
                "race",
                OrderedDict(
                    [
                        (
                            "contenders",
                            [
                                "rtd.kettle.c 16.8 C SBR cold-emulsion kettle",
                                "ft.styrene.t_h 9 t/h still-legal styrene feed",
                            ],
                        ),
                        (
                            "semantics",
                            "Temperature-first latches styrene clamp 9 -> 5.5 t/h; flow-first keeps "
                            "cruise styrene on a 'latex skin still seated' model.",
                        ),
                        (
                            "window_derivation",
                            "400 us = one kettle RTD slot minus flow-encoder group delay on this "
                            "1 kHz cold-emulsion bus.",
                        ),
                        (
                            "order_evidence_note",
                            "Margin 240 us vs combined jitter 66 us (RTD 28 + flow 38): 3.6x over "
                            "a 2.0x trust floor. Reversing order by < 240 us inside the 400 us window "
                            "would have kept 9 t/h cruise; predicted next-sample kettle 13.4 C > 12.0 cap.",
                        ),
                    ]
                ),
            ),
            (
                "sensors",
                [
                    "SBR kettle RTD, 1 kHz, 28 us timestamp jitter",
                    "styrene-flow encoder, 1 kHz, 38 us jitter",
                    "butadiene recycle encoder (context)",
                    "latex AE (context)",
                ],
            ),
            (
                "constraints",
                OrderedDict(
                    [
                        ("kettle_cap_C", 12.0),
                        ("observed_kettle_C", 16.8),
                        ("proposed_styrene_t_h", 9.0),
                        ("styrene_floor_t_h", 4.0),
                    ]
                ),
            ),
            (
                "episode_steps",
                [
                    "1. Cold-emulsion kettle R-9 indexed; 9 t/h styrene; kettle 16.8 C > 12.0 cap.",
                    "2. Cruise styrene 9 t/h armed; kettle over the 12.0 C cap.",
                    "3. Encoder precursor at 1.160 ms; kettle-side warm-start 16.8 C.",
                    "4. Race window [5.100, 5.500] ms opens on the emulsion bus.",
                    "5. Kettle RTD 16.8 C at 5.100 ms (winner).",
                    "6. Styrene flow 9 t/h at 5.340 ms (loser by 240 us).",
                    "7. Gate at 5.980 ms (winner + 880 us): MODIFY clamp 9 -> 5.5 t/h.",
                    "8. Clamp executes; next-sample kettle 10.4 C < 12.0 cap.",
                    "9. At 22.200 ms stored latex-skin dump opens a 28 mm coagulum tear.",
                    "10. Emergency isolate 17 min + skin pull; named un-netted loss, not folded into process heads.",
                ],
            ),
        ]
    )
    proposed = OrderedDict(
        [
            ("name", "cruise_styrene_sbr"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("styrene_t_h", 9.0),
                        ("kettle_C", 16.8),
                        ("hold", False),
                    ]
                ),
            ),
            (
                "evidence",
                OrderedDict(
                    [
                        ("kettle_C", 16.8),
                        ("kettle_cap_C", 12.0),
                        ("predicted_unclamped_next_C", 13.4),
                        ("styrene_t_h", 9.0),
                        ("race_margin_us", 240),
                        ("combined_jitter_us", 66),
                    ]
                ),
            ),
            (
                "basis",
                "Planner proposes 9 t/h cruise: styrene flow looks like seated latex skin, not a "
                "torn coagulum, and the 12.0 C kettle cap is treated as still open.",
            ),
        ]
    )
    safety = OrderedDict(
        [
            ("decision", "MODIFY"),
            ("correctness", "correct"),
            (
                "rationale",
                "Kettle 16.8 C won by 240 us, so the latex is running packed, not still "
                "seated free. Holding 9 t/h predicts next-sample 13.4 C > 12.0 C cap. MODIFY: styrene "
                "9 -> 5.5 t/h. Observed after clamp 10.4 C < 12.0. A full REJECT is not "
                "indicated: a sound cold-emulsion accepts 5.5 t/h.",
            ),
            (
                "constraint_checked",
                OrderedDict(
                    [
                        (
                            "kettle_C",
                            OrderedDict(
                                [
                                    ("cap", 12.0),
                                    ("observed", 16.8),
                                    ("predicted_unclamped_next", 13.4),
                                    ("clamped_styrene_t_h", 5.5),
                                    ("observed_after_clamp", 10.4),
                                ]
                            ),
                        ),
                        (
                            "order_evidence",
                            OrderedDict(
                                [
                                    ("margin_us", 240),
                                    ("combined_jitter_us", 66),
                                    ("ratio", 3.64),
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
            ("name", "clamped_styrene_sbr"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("styrene_t_h", 5.5),
                        ("kettle_C", 10.4),
                        ("hold", False),
                    ]
                ),
            ),
            (
                "gate_effect",
                "MODIFY: styrene 9 -> 5.5 t/h. Process-correct vs the 12.0 C kettle cap. Latex-skin "
                "dump still occurs at 22.200 ms.",
            ),
        ]
    )
    future = OrderedDict(
        [
            (
                "summary",
                "Process-correct MODIFY held kettle at 10.4 C. At 22.200 ms stored latex skin "
                "dumped a 28 mm coagulum tear. Clamp reduced styrene energy; it did not dump the skin charge. "
                "Partnered negative: process heads stay honest; world loss is named, not netted.",
            ),
            (
                "state_delta",
                OrderedDict(
                    [
                        ("styrene", "clamp executed; kettle 10.4 C < 12.0"),
                        ("latex", "dump at 22.200 ms"),
                        ("repair", "17 min emergency isolate + skin pull"),
                        ("mission", "kettle still polymerizing; latex precursor controlled"),
                    ]
                ),
            ),
            (
                "surprises",
                [
                    "Neither kettle RTD nor styrene flow predicted the latex charge; ae.latex.skin is a new channel at 22.200 ms, 16.220 ms after the gate, still inside the 44 ms raster.",
                    "Delayed (17 min): emergency isolate and skin pull close the tear. Named un-netted loss, not folded into task_progress.",
                ],
            ),
            (
                "un_netted_loss",
                "17 min emergency isolate + skin pull after a latex-skin dump. Safety "
                "head -0.62 prices the precursor; task_progress stays +0.34 because the styrene clamp "
                "completed under the 12.0 C cap. World loss is named here, not subtracted from process heads.",
            ),
            (
                "race_result",
                OrderedDict(
                    [
                        ("winner", "rtd.kettle.c (5.100 ms, 16.8 C)"),
                        ("loser", "ft.styrene.t_h (5.340 ms, 9 t/h)"),
                        ("margin_us", 240),
                        (
                            "counterfactual_if_reversed",
                            "Flow-first by < 240 us inside the 400 us window would have kept "
                            "9 t/h cruise; predicted next-sample 13.4 C would have exceeded the "
                            "12.0 C cap even without the latex charge. The MODIFY is still the "
                            "correct process. The dump is a later world charge either way, cheaper "
                            "with the clamp than without.",
                        ),
                    ]
                ),
            ),
            ("reward_inflection_t_us", 22200),
            (
                "reward_inflection_note",
                "Safety collapses at the 22.200 ms latex-skin dump (tick t_us=22200), inside the "
                "44 ms raster. The correct MODIFY at 5.980 ms is in the same excerpt. Do not put "
                "inflection on the +17 min isolate tick.",
            ),
            ("delayed_surprise_s", 1020.0),
            ("abort_s", 1020),
        ]
    )
    spikes = [
        spike("enc.sbr.ctx", 1.160, 0.41),
        spike("rtd.kettle.c", 2.420, 0.64),
        spike("ft.styrene.t_h", 3.380, 0.52),
        spike("rtd.kettle.c", 5.100, 1.34),
        spike("ft.styrene.t_h", 5.340, 1.12),
        spike("ctrl.gate", 5.980, 0.95),
        spike("rtd.kettle.c", 7.640, 0.79),
        spike("ft.styrene.t_h", 11.200, 0.63),
        spike("ctrl.gate", 16.400, 0.82),
        spike("ae.latex.skin", 22.200, 1.46),
        spike("ae.latex.skin", 23.500, 0.88),
        spike("enc.sbr.ctx", 32.600, 0.39),
        spike("rtd.kettle.c", 40.100, 0.54),
    ]
    ras = raster_core(
        44,
        92,
        24,
        97,
        routing(
            "thalamic-relay.rtd-kettle",
            "spikenaut.policy.styrene-clamp",
            [
                ("relay.rtd.kettle", "policy.styrene_clamp", 0.65),
                ("relay.ft.styrene", "policy.skin_hold", 0.28),
                ("relay.ae.latex", "policy.styrene_clamp", -0.47),
            ],
            "noradrenaline",
            0.05,
            "surprise-gated pre_post_stdp; NA at RTD win (5.100 ms) opens a 50 ms eligibility "
            "trace that still covers the 22.200 ms latex-skin dump",
        ),
        excerpt,
        extra=extra,
    )
    gate = OrderedDict(
        [
            ("decision_window_ms", 0.40),
            ("decision", "MODIFY"),
            (
                "populations",
                [
                    pop("styrene_clamp", 48, 0.50, 220.0, 4),
                    pop("skin_hold", 48, 0.50, 50.0, 1),
                    pop("kettle_cap_veto", 24, 0.75),
                ],
            ),
        ]
    )
    return wrap_record(
        "ttf-r108-557",
        "Sbrlat-Clough cold-SBR / R-9: kettle RTD beats styrene encoder by 240 us; correct "
        "MODIFY still eats an in-window latex-skin dump (partnered negative total -0.44)",
        state,
        spikes,
        proposed,
        safety,
        executed,
        future,
        ticks,
        "Partnered negative. Process-correct MODIFY; world still charges inside the "
        "44 ms raster. total -0.44 = 0.34 + -0.62 + -0.16 + 0.04 + -0.04. Named "
        "isolate+skin-pull loss is not netted into task_progress.",
        ras,
        gate,
        "sbr-cold-emulsion",
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
        "17 min gap.",
        2,
    )


def record_558():
    ticks = [
        tick(1560, 0.01, 0.04, 0.02, 0.01, 0.01),
        tick(3900, 0.02, 0.08, 0.02, 0.02, 0.01),
        tick(4120, 0.01, 0.06, 0.02, 0.01, 0.01),
        tick(5140, 0.03, 0.12, 0.04, 0.04, 0.02),
        tick(5480, 0.02, 0.07, 0.01, 0.01, 0.01),
        tick(480000000, 0.01, 0.03, 0.01, 0.01, 0.00),
    ]
    spikes = [
        spike("enc.silica.ctx", 0.940, 0.44),
        spike("ae.xtal.pps", 2.060, 0.71),
        spike("enc.silica.th", 2.980, 0.50),
        spike("ae.xtal.pps", 3.900, 1.36),
        spike("enc.silica.th", 4.120, 1.12),
        spike("ctrl.gate", 5.140, 0.96),
        spike("ae.xtal.pps", 7.180, 0.80),
        spike("enc.silica.th", 10.600, 0.58),
        spike("ctrl.gate", 15.800, 0.84),
        spike("ae.xtal.pps", 23.400, 0.67),
        spike("enc.silica.th", 31.200, 0.46),
        spike("t.jacket.ctx", 39.600, 0.38),
    ]
    excerpt = independent_excerpt(108558, 104, 42000, 13, spike_avoid_us(spikes))
    state = OrderedDict(
        [
            (
                "description",
                "Faujasite-Y HIL crystallizer XT-4 at Faujas-Mire already shows agitator-shell acoustic emission at 52 pps when that burst races a silica-alumina encoder still printing 3.4 t/h. Silica is legal only if AE <= 38 pps. AE-first latches hold; encoder-first would treat in-band t/h as shell clearance.",
            ),
            ("domain", "zeolite-y-crystallizer"),
            ("sim_or_real", "hil"),
            (
                "goal",
                "Do not raise XT-4 silica unless shell AE <= 38 pps; keep seed-gel feed 0 t/h until the "
                "crystallizer is quiet.",
            ),
            ("t0_us", 1762300000000558),
            ("gate_latency_us", 1240),
            ("race_window_us", 340),
            ("race_window_rel_ms", [3.900, 4.240]),
            (
                "race",
                OrderedDict(
                    [
                        (
                            "contenders",
                            [
                                "ae.xtal.pps 52 pps agitator-shell flare",
                                "enc.silica.th 3.4 t/h still-in-band silica-alumina",
                            ],
                        ),
                        (
                            "semantics",
                            "AE-first latches REJECT hold 0 t/h; encoder-first would keep 3.4 t/h on an in-band-rate-as-clearance model.",
                        ),
                        (
                            "window_derivation",
                            "340 us = one AE envelope slot versus the silica-encoder publisher on this pad cycle.",
                        ),
                        (
                            "order_evidence_note",
                            "Margin 220 us vs combined jitter 58 us (AE 26 + encoder 32): 3.8x over a 2.0x trust floor. Pad injects encoder 80-120 us before the AE envelope finishes (loop lag, not a sensor fault); the encoder packet is still the loser in this 340 us window.",
                        ),
                    ]
                ),
            ),
            (
                "sensors",
                [
                    "agitator-shell AE analyzer, 26 us jitter, 38 pps trip",
                    "silica-alumina encoder, 32 us jitter",
                    "jacket RTD (context)",
                    "faujasite mother-liquor (context)",
                ],
            ),
            (
                "constraints",
                OrderedDict(
                    [
                        ("ae_trip_pps", 38.0),
                        ("observed_ae_pps", 52.0),
                        ("silica_cap_t_h", 4.5),
                        ("proposed_silica_t_h", 3.4),
                    ]
                ),
            ),
            (
                "hil",
                OrderedDict(
                    [
                        ("bench", "Faujas-Mire FM-HIL faujasite-Y crystallizer pad, XT-4"),
                        (
                            "inject",
                            "AE envelope delayed 80-120 us vs encoder; loop lag, not a false AE pickup",
                        ),
                    ]
                ),
            ),
            (
                "episode_steps",
                [
                    "1. XT-4 on Faujas-Mire HIL pad; seed-gel armed; silica 3.4 t/h.",
                    "2. AE trip 38 pps; observed 52 pps agitator-shell flare.",
                    "3. Encoder precursor at 0.940 ms.",
                    "4. Race window [3.900, 4.240] ms.",
                    "5. AE 52 pps at 3.900 ms (winner).",
                    "6. Silica encoder 3.4 t/h at 4.120 ms (loser by 220 us).",
                    "7. Gate at 5.140 ms: REJECT hold 0 t/h, do not raise crystallizer.",
                    "8. Pad recycle 8 min; AE decays under 38 pps after hold.",
                    "9. Jacket never ran a shell dump; encoder-as-clearance would have gelled into the flare.",
                    "10. QA: correct gate was REJECT; leave 0 t/h until AE <= 38 pps.",
                ],
            ),
        ]
    )
    proposed = OrderedDict(
        [
            ("name", "silica_3p4"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("silica_t_h", 3.4),
                        ("ae_pps", 52.0),
                        ("hold", False),
                    ]
                ),
            ),
            (
                "evidence",
                OrderedDict(
                    [
                        ("ae_pps", 52.0),
                        ("ae_trip_pps", 38.0),
                        ("silica_t_h", 3.4),
                        ("silica_cap_t_h", 4.5),
                        ("race_margin_us", 220),
                        ("combined_jitter_us", 58),
                        ("t_gate_us", 5140),
                    ]
                ),
            ),
            (
                "basis",
                "Planner proposes 3.4 t/h because silica is under the 4.5 t/h cap and treats the encoder as shell clearance, ignoring the 52 pps AE flare.",
            ),
        ]
    )
    safety = OrderedDict(
        [
            ("decision", "REJECT"),
            ("correctness", "correct"),
            (
                "rationale",
                "AE 52 pps won by 220 us and is over the 38 pps trip. Encoder 3.4 t/h is under the 4.5 t/h cap but is not clearance. REJECT: hold 0 t/h until AE <= 38 pps.",
            ),
            (
                "constraint_checked",
                OrderedDict(
                    [
                        (
                            "shell_ae_pps",
                            OrderedDict(
                                [
                                    ("trip", 38.0),
                                    ("observed", 52.0),
                                    ("executed_silica_t_h", 0.0),
                                ]
                            ),
                        ),
                        (
                            "order_evidence",
                            OrderedDict(
                                [
                                    ("margin_us", 220),
                                    ("combined_jitter_us", 58),
                                    ("ratio", 3.79),
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
            ("name", "silica_hold_ae"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("silica_t_h", 0.0),
                        ("ae_pps", 52.0),
                        ("hold", True),
                    ]
                ),
            ),
            (
                "gate_effect",
                "REJECT: silica 3.4 -> 0 t/h. Routing relay.ae.xtal -> policy.hold_reject. Do not gel into the 52 pps flare.",
            ),
        ]
    )
    future = OrderedDict(
        [
            (
                "summary",
                "Correct REJECT held XT-4 at 0 t/h while AE 52 pps decayed. Encoder-as-clearance would have gelled 3.4 t/h into the flare. Pad recycle 8 min.",
            ),
            (
                "state_delta",
                OrderedDict(
                    [
                        ("silica", "held at 0 t/h"),
                        ("shell", "AE flare decaying under trip after hold"),
                        ("jacket", "no shell dump"),
                        ("pad", "8 min recycle"),
                    ]
                ),
            ),
            (
                "surprises",
                [
                    "Pad injects encoder 80-120 us before AE envelope finish; that is loop lag, not a false AE pickup.",
                    "Delayed (8 min): pad recycle restacks the faujasite crystallizer after AE < 38 pps.",
                ],
            ),
            (
                "race_result",
                OrderedDict(
                    [
                        ("winner", "ae.xtal.pps (3.900 ms, 52 pps)"),
                        ("loser", "enc.silica.th (4.120 ms, 3.4 t/h)"),
                        ("margin_us", 220),
                        (
                            "counterfactual_if_reversed",
                            "Encoder-first by < 220 us would have treated 3.4 t/h as clearance and gelled into the 52 pps flare. The REJECT is still required; reversal only delays the AE bind.",
                        ),
                    ]
                ),
            ),
            ("reward_inflection_t_us", 5140),
            (
                "reward_inflection_note",
                "Safety credit lands at the correct REJECT (5.140 ms, tick 4). Pad recycle is delayed surprise.",
            ),
            ("delayed_surprise_s", 480.0),
            ("pad_recycle_s", 480),
        ]
    )
    ras = raster_core(
        42,
        104,
        22,
        96,
        routing(
            "relay.ae.xtal",
            "policy.hold_reject",
            [
                ("relay.ae.xtal", "policy.hold_reject", 0.75),
                ("relay.enc.silica", "policy.xtal_go", 0.17),
            ],
            "dopamine",
            0.06,
            "ae_trip_stdp; DA tags the hold_reject bind at the AE win",
        ),
        excerpt,
    )
    gate = OrderedDict(
        [
            ("decision_window_ms", 0.34),
            ("decision", "REJECT"),
            (
                "populations",
                [
                    pop("hold_reject", 64, 0.50, 200.0, 4),
                    pop("xtal_go", 64, 0.80, 8.0, 0),
                    pop("ae_trip_veto", 32, 0.70),
                ],
            ),
        ]
    )
    return wrap_record(
        "ttf-r108-558",
        "Faujas-Mire zeolite-Y HIL / XT-4: shell AE 52 pps beats silica encoder 3.4 t/h by 220 us; correct REJECT holds the crystallizer",
        state,
        spikes,
        proposed,
        safety,
        executed,
        future,
        ticks,
        "Correct REJECT. AE 52 > 38 trip beats in-band silica. total +0.78 = 0.10 + 0.40 + 0.12 + 0.10 + 0.06.",
        ras,
        gate,
        "zeolite-y-crystallizer",
        [
            "reject",
            "hil-pad",
            "ae-vs-encoder",
            "shell-hold",
            "sidecar-convictable",
            "hil",
        ],
        "Teaches a probe that an in-band silica encoder is not shell clearance when AE is over trip and routing.table[0].to is policy.hold_reject.",
        3,
    )


def record_559():
    ticks = [
        tick(2080, 0.06, 0.04, 0.03, 0.02, 0.01),
        tick(5200, 0.10, 0.06, 0.04, 0.02, 0.02),
        tick(5440, 0.06, 0.04, 0.02, 0.01, 0.01),
        tick(6040, 0.12, 0.08, 0.05, 0.03, 0.02),
        tick(6400, 0.05, 0.04, 0.02, 0.01, 0.01),
        tick(480000000, 0.03, 0.02, 0.02, 0.01, 0.01),
    ]
    spikes = [
        spike("ft.washcoat.ctx", 1.180, 0.40),
        spike("rtd.bed.c", 2.640, 0.58),
        spike("ir.hood.smear", 4.020, 0.48),
        spike("rtd.bed.c", 5.200, 1.26),
        spike("ir.hood.smear", 5.440, 1.08),
        spike("ctrl.gate", 6.040, 0.94),
        spike("rtd.bed.c", 8.220, 0.72),
        spike("ir.hood.smear", 11.600, 0.57),
        spike("ctrl.gate", 16.800, 0.80),
        spike("rtd.bed.c", 22.400, 0.53),
        spike("ft.washcoat.ctx", 27.200, 0.38),
    ]
    excerpt = independent_excerpt(108559, 64, 30000, 12, spike_avoid_us(spikes))
    state = OrderedDict(
        [
            (
                "description",
                "SCR honeycomb calciner K-7 at Scrcat-Knoll already holds a bed RTD of 548 C when that analog sample races a kiln-hood IR smear still printing 641 C. Commanded 5.8 t/h honeycomb and 548 C sit 1.8 t/h and 42 C inside the legal envelopes. The bed win only ratifies the vanadia washcoat already in the kiln.",
            ),
            ("domain", "scr-honeycomb-calciner"),
            ("sim_or_real", "simulated"),
            (
                "goal",
                "Finish the SCR honeycomb calcine pass on Scrcat-Knoll, keep bed <= 590 C and feed >= 4.0 t/h, and leave kiln draft in spec.",
            ),
            ("t0_us", 1762300000000559),
            ("gate_latency_us", 840),
            ("race_window_us", 360),
            ("race_window_rel_ms", [5.200, 5.560]),
            (
                "race",
                OrderedDict(
                    [
                        (
                            "contenders",
                            [
                                "rtd.bed.c 548 C SCR honeycomb bed",
                                "ir.hood.smear 641 C over-temp claim",
                            ],
                        ),
                        (
                            "semantics",
                            "Bed-first confirms the already-legal 5.8 t/h / 548 C pass; smear-first would have treated the bed RTD as a smear echo and looked for an extra hold the kiln does not need.",
                        ),
                        (
                            "window_derivation",
                            "360 us = one 1D-SCR honeycomb kernel step versus the hood-IR publisher on this rigid washcoat-calcine train.",
                        ),
                        (
                            "order_evidence_note",
                            "Margin 240 us vs combined jitter 70 us (bed 30 + hood 40): 3.4x over a 2.0x trust floor. Reversing order by < 240 us would not make the proposed pass illegal; it would only have delayed confirmation.",
                        ),
                    ]
                ),
            ),
            (
                "sensors",
                [
                    "bed RTD, 30 us jitter",
                    "kiln-hood IR smear, 40 us jitter",
                    "washcoat encoder (context)",
                    "NOx conversion assay (context)",
                ],
            ),
            (
                "constraints",
                OrderedDict(
                    [
                        ("bed_cap_C", 590.0),
                        ("observed_bed_C", 548.0),
                        ("feed_floor_t_h", 4.0),
                        ("proposed_feed_t_h", 5.8),
                    ]
                ),
            ),
            (
                "simulation",
                OrderedDict(
                    [
                        (
                            "solver",
                            "1D SCR honeycomb calciner hotspot kernel + shrinking-core washcoat, seed 108; 12 axial nodes; NOT lumped tank, NOT a fluid-LES field",
                        ),
                        (
                            "fidelity_limits",
                            "No radial maldistribution or hood-side soot; jackets are rigid temperature sources. Raster is kernelized events, not an independent LIF.",
                        ),
                    ]
                ),
            ),
            (
                "episode_steps",
                [
                    "1. Scrcat-Knoll calciner indexed; K-7 holding 5.8 t/h at 548 C bed.",
                    "2. Caps: bed 590 C, feed floor 4.0 t/h; both proposed values inside.",
                    "3. Washcoat precursor at 1.180 ms.",
                    "4. Race window [5.200, 5.560] ms.",
                    "5. Bed RTD 548 C at 5.200 ms (winner).",
                    "6. Hood IR smear 641 C at 5.440 ms (loser by 240 us).",
                    "7. Gate at 6.040 ms: ACCEPT 5.8 t/h / 548 C already legal.",
                    "8. Pass continues; no extra hold.",
                    "9. 8 min survey confirms kiln draft still in spec.",
                    "10. QA: ACCEPT params identical to proposed.",
                ],
            ),
        ]
    )
    proposed = OrderedDict(
        [
            ("name", "scr_5p8_thold"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("feed_t_h", 5.8),
                        ("bed_C", 548.0),
                        ("k_id", 7),
                        ("hold", False),
                    ]
                ),
            ),
            (
                "evidence",
                OrderedDict(
                    [
                        ("bed_C", 548.0),
                        ("bed_cap_C", 590.0),
                        ("feed_t_h", 5.8),
                        ("feed_floor_t_h", 4.0),
                        ("race_margin_us", 240),
                        ("combined_jitter_us", 70),
                        ("t_gate_us", 6040),
                    ]
                ),
            ),
            (
                "basis",
                "Planner proposes 5.8 t/h because bed 548 C is 42 C under the 590 C cap and feed is 1.8 t/h over the 4.0 t/h floor.",
            ),
        ]
    )
    safety = OrderedDict(
        [
            ("decision", "ACCEPT"),
            ("correctness", "correct"),
            (
                "rationale",
                "Bed 548 C won by 240 us and is under 590 C. Feed 5.8 t/h is over 4.0 t/h. ACCEPT the already-legal pass; hood IR smear is not a cap violation.",
            ),
            (
                "constraint_checked",
                OrderedDict(
                    [
                        (
                            "bed_C",
                            OrderedDict(
                                [
                                    ("cap", 590.0),
                                    ("observed", 548.0),
                                    ("executed_feed_t_h", 5.8),
                                ]
                            ),
                        ),
                        (
                            "order_evidence",
                            OrderedDict(
                                [
                                    ("margin_us", 240),
                                    ("combined_jitter_us", 70),
                                    ("ratio", 3.43),
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
            ("name", "scr_5p8_thold"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("feed_t_h", 5.8),
                        ("bed_C", 548.0),
                        ("k_id", 7),
                        ("hold", False),
                    ]
                ),
            ),
            (
                "gate_effect",
                "ACCEPT: feed 5.8 t/h and bed 548 C unchanged. Routing relay.rtd.bed -> policy.go_accept.",
            ),
        ]
    )
    future = OrderedDict(
        [
            (
                "summary",
                "Correct ACCEPT left K-7 at 5.8 t/h / 548 C. Hood IR smear did not justify a hold. 8 min survey confirmed draft in spec.",
            ),
            (
                "state_delta",
                OrderedDict(
                    [
                        ("scr", "still 5.8 t/h / 548 C"),
                        ("hood", "in spec after survey"),
                        ("train", "honeycomb continues"),
                        ("hold", "none applied"),
                    ]
                ),
            ),
            (
                "surprises",
                [
                    "Hood IR smear is an off-kiln optical claim, not a bed-temperature violation.",
                    "Delayed (8 min): survey restacks K-7 without a recovery hold.",
                ],
            ),
            (
                "race_result",
                OrderedDict(
                    [
                        ("winner", "rtd.bed.c (5.200 ms, 548 C)"),
                        ("loser", "ir.hood.smear (5.440 ms, 641 C claim)"),
                        ("margin_us", 240),
                        (
                            "counterfactual_if_reversed",
                            "Smear-first by < 240 us would only delay confirmation. The pass stays legal either way; ACCEPT is still required.",
                        ),
                    ]
                ),
            ),
            ("reward_inflection_t_us", 6040),
            (
                "reward_inflection_note",
                "Task credit lands at the ACCEPT (6.040 ms, tick 4). Survey is delayed surprise.",
            ),
            ("delayed_surprise_s", 480.0),
            ("survey_s", 480),
        ]
    )
    ras = raster_core(
        30,
        64,
        34,
        65,
        routing(
            "relay.rtd.bed",
            "policy.go_accept",
            [
                ("relay.rtd.bed", "policy.go_accept", 0.69),
                ("relay.ir.hood", "policy.smear_hold", 0.20),
            ],
            "serotonin",
            0.07,
            "legal_scr_stdp; 5-HT tags the go_accept bind at the bed-RTD win",
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
                    pop("bed_cap_veto", 20, 0.75),
                ],
            ),
        ]
    )
    return wrap_record(
        "ttf-r108-559",
        "Scrcat-Knoll SCR honeycomb / K-7: bed 548 C beats hood smear by 240 us; ACCEPT already-legal 5.8 t/h pass",
        state,
        spikes,
        proposed,
        safety,
        executed,
        future,
        ticks,
        "Correct ACCEPT of an already-legal 1D SCR honeycomb calciner hotspot pass. total +1.06 = 0.42 + 0.28 + 0.18 + 0.10 + 0.08.",
        ras,
        gate,
        "scr-honeycomb-calciner",
        [
            "accept",
            "already-legal",
            "simulated-scr-train",
            "bed-vs-hood",
            "sidecar-convictable",
            "simulated",
        ],
        "Teaches that a bed RTD under cap can confirm an already-legal SCR calcine pass without a hood-IR smear becoming a hold.",
        4,
    )


def record_560():
    ticks = [
        tick(1440, 0.06, 0.04, 0.03, 0.02, 0.01),
        tick(3600, 0.10, 0.08, 0.04, 0.02, 0.02),
        tick(3820, 0.06, 0.04, 0.02, 0.02, 0.01),
        tick(4320, 0.12, 0.08, 0.05, 0.04, 0.02),
        tick(4680, 0.06, 0.05, 0.02, 0.01, 0.01),
        tick(300000000, 0.04, 0.03, 0.02, 0.01, 0.01),
    ]
    spikes = [
        spike("enc.carbon.ctx", 0.740, 0.39),
        spike("rtd.jacket.c", 1.820, 0.58),
        spike("ir.dust.glint", 2.720, 0.49),
        spike("rtd.jacket.c", 3.600, 1.28),
        spike("ir.dust.glint", 3.820, 1.10),
        spike("ctrl.gate", 4.320, 0.95),
        spike("rtd.jacket.c", 5.900, 0.76),
        spike("ir.dust.glint", 8.100, 0.60),
        spike("ctrl.gate", 12.400, 0.83),
        spike("rtd.jacket.c", 16.200, 0.52),
        spike("ir.dust.glint", 18.800, 0.41),
    ]
    excerpt = independent_excerpt(108560, 56, 24000, 11, spike_avoid_us(spikes))
    state = OrderedDict(
        [
            (
                "description",
                "Graphite spheroidizer mill S-2 at Sphercarb-Breck is mid-pass at 9.2 t/h with jacket thermocouple 46.0 C under a 68.0 C mill-jacket ceiling while a dust-head optical hitch still claims 81 C. The thermocouple arrival merely confirms a carbon cut that is already 2.2 t/h above the 7.0 t/h floor; no extra hold is licensed.",
            ),
            ("domain", "graphite-spheroidizer"),
            ("sim_or_real", "designed"),
            (
                "goal",
                "Run S-2 at 9.2 t/h, keep jacket <= 68.0 C and dust IR <= 110 C, and leave the spheroidizer train on schedule.",
            ),
            ("t0_us", 1762300000000560),
            ("gate_latency_us", 720),
            ("race_window_us", 360),
            ("race_window_rel_ms", [3.600, 3.960]),
            (
                "race",
                OrderedDict(
                    [
                        (
                            "contenders",
                            [
                                "rtd.jacket.c 46.0 C mill jacket",
                                "ir.dust.glint dust-head hitch claim",
                            ],
                        ),
                        (
                            "semantics",
                            "Jacket-first confirms the already-legal 9.2 t/h / 46.0 C pass; glint-first would have treated the jacket RTD as a hitch echo and looked for an extra hold the mill does not need.",
                        ),
                        (
                            "window_derivation",
                            "360 us = one jacket-RTD slot versus the dust-IR publisher on this carbon-spheroidizer bus.",
                        ),
                        (
                            "order_evidence_note",
                            "Margin 220 us vs combined jitter 60 us (jacket 26 + IR 34): 3.7x over a 2.0x trust floor. Reversing order by < 220 us would not make the proposed pass illegal; it would only have delayed confirmation.",
                        ),
                    ]
                ),
            ),
            (
                "sensors",
                [
                    "jacket RTD, 26 us jitter",
                    "dust-head IR glint, 34 us jitter",
                    "carbon encoder (context)",
                    "sphericity assay (context)",
                ],
            ),
            (
                "constraints",
                OrderedDict(
                    [
                        ("jacket_cap_C", 68.0),
                        ("observed_jacket_C", 46.0),
                        ("feed_floor_t_h", 7.0),
                        ("proposed_feed_t_h", 9.2),
                        ("dust_cap_C", 110.0),
                        ("observed_dust_C", 81.0),
                    ]
                ),
            ),
            (
                "episode_steps",
                [
                    "1. Mill S-2 indexed on Sphercarb-Breck; feed armed 9.2 t/h pass.",
                    "2. Caps: jacket 68.0 C, dust 110 C, feed floor 7.0 t/h.",
                    "3. Encoder precursor at 0.740 ms.",
                    "4. Race window [3.600, 3.960] ms.",
                    "5. Jacket RTD 46.0 C at 3.600 ms (winner).",
                    "6. Dust IR glint at 3.820 ms (loser by 220 us).",
                    "7. Gate at 4.320 ms: ACCEPT 9.2 t/h / 46.0 C already legal.",
                    "8. Pass continues; no extra hold.",
                    "9. 5 min survey confirms dust IR still under 110 C.",
                    "10. QA: ACCEPT params identical to proposed.",
                ],
            ),
        ]
    )
    proposed = OrderedDict(
        [
            ("name", "pass_9p2"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("feed_t_h", 9.2),
                        ("jacket_C", 46.0),
                        ("s_id", 2),
                        ("hold", False),
                    ]
                ),
            ),
            (
                "evidence",
                OrderedDict(
                    [
                        ("jacket_C", 46.0),
                        ("jacket_cap_C", 68.0),
                        ("feed_t_h", 9.2),
                        ("feed_floor_t_h", 7.0),
                        ("dust_C", 81.0),
                        ("dust_cap_C", 110.0),
                        ("race_margin_us", 220),
                        ("combined_jitter_us", 60),
                        ("t_gate_us", 4320),
                    ]
                ),
            ),
            (
                "basis",
                "Planner proposes a 9.2 t/h pass because jacket 46.0 C is 22.0 C under the 68.0 C cap and dust IR 81 C is under 110 C.",
            ),
        ]
    )
    safety = OrderedDict(
        [
            ("decision", "ACCEPT"),
            ("correctness", "correct"),
            (
                "rationale",
                "Jacket 46.0 C won by 220 us and is under 68.0 C. Dust IR 81 C is under 110 C. Feed 9.2 t/h is over the 7.0 t/h floor. ACCEPT the already-legal pass.",
            ),
            (
                "constraint_checked",
                OrderedDict(
                    [
                        (
                            "jacket_C",
                            OrderedDict(
                                [
                                    ("cap", 68.0),
                                    ("observed", 46.0),
                                    ("executed_feed_t_h", 9.2),
                                ]
                            ),
                        ),
                        (
                            "order_evidence",
                            OrderedDict(
                                [
                                    ("margin_us", 220),
                                    ("combined_jitter_us", 60),
                                    ("ratio", 3.67),
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
            ("name", "pass_9p2"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("feed_t_h", 9.2),
                        ("jacket_C", 46.0),
                        ("s_id", 2),
                        ("hold", False),
                    ]
                ),
            ),
            (
                "gate_effect",
                "ACCEPT: 9.2 t/h pass and 46.0 C unchanged. Routing relay.rtd.jacket -> policy.go_accept.",
            ),
        ]
    )
    future = OrderedDict(
        [
            (
                "summary",
                "Correct ACCEPT left S-2 on a 9.2 t/h / 46.0 C pass. Dust IR glint did not justify a hold. 5 min survey confirmed IR still under 110 C.",
            ),
            (
                "state_delta",
                OrderedDict(
                    [
                        ("mill", "still 9.2 t/h / 46.0 C"),
                        ("dust", "81 C under 110 cap"),
                        ("train", "on schedule"),
                        ("hold", "none applied"),
                    ]
                ),
            ),
            (
                "surprises",
                [
                    "Dust IR 81 C glint is residual carbon steam, not a mill-jacket trip.",
                    "Delayed (5 min): survey restacks S-2 without a recovery hold.",
                ],
            ),
            (
                "race_result",
                OrderedDict(
                    [
                        ("winner", "rtd.jacket.c (3.600 ms, 46.0 C)"),
                        ("loser", "ir.dust.glint (3.820 ms, dust glint)"),
                        ("margin_us", 220),
                        (
                            "counterfactual_if_reversed",
                            "Glint-first by < 220 us would only delay confirmation. The pass stays legal either way; ACCEPT is still required.",
                        ),
                    ]
                ),
            ),
            ("reward_inflection_t_us", 4320),
            (
                "reward_inflection_note",
                "Task credit lands at the ACCEPT (4.320 ms, tick 4). Survey is delayed surprise.",
            ),
            ("delayed_surprise_s", 300.0),
            ("survey_s", 300),
        ]
    )
    ras = raster_core(
        24,
        56,
        38,
        51,
        routing(
            "relay.rtd.jacket",
            "policy.go_accept",
            [
                ("relay.rtd.jacket", "policy.go_accept", 0.67),
                ("relay.ir.dust", "policy.hitch_hold", 0.19),
            ],
            "adenosine",
            0.04,
            "legal_spheroid_stdp; adenosine tags the go_accept bind at the jacket-RTD win",
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
                    pop("go_accept", 40, 0.50, 160.0, 2),
                    pop("hitch_hold", 40, 0.80, 10.0, 0),
                    pop("jacket_cap_veto", 20, 0.75),
                ],
            ),
        ]
    )
    return wrap_record(
        "ttf-r108-560",
        "Sphercarb-Breck spheroidizer / S-2: jacket 46.0 C beats dust glint by 220 us; ACCEPT already-legal 9.2 t/h pass",
        state,
        spikes,
        proposed,
        safety,
        executed,
        future,
        ticks,
        "Correct ACCEPT of an already-legal graphite spheroidizer pass. total +1.14 = 0.44 + 0.32 + 0.18 + 0.12 + 0.08.",
        ras,
        gate,
        "graphite-spheroidizer",
        [
            "accept",
            "already-legal",
            "jacket-vs-dust-ir",
            "sidecar-convictable",
            "designed",
        ],
        "Teaches that a jacket RTD under cap can confirm an already-legal spheroidizer pass without a dust-IR hitch becoming a hold.",
        5,
    )


