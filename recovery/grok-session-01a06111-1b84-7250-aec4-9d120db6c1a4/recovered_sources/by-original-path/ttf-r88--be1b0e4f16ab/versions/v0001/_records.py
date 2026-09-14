def lif_457_excerpt():
    """Independent CUBA LIF (seed 88457). Plant remains designed."""

    n = 88
    dt_us = 100
    tau_m_ms = 19.4
    v_th = 1.0
    v_reset = 0.0
    refractory_us = 1000
    i_bias = 0.90
    i_stim_peak = 2.52
    stim = (21000, 25000)
    seed = 88457
    window_us = 42000
    i_clamp_extra = 0.69
    clamp_n = 16
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
    take(burst, 9, label_times=(22400, 23200, 24100))
    clamp = [(t, nid) for t, nid in picked if t < 21000][:7]
    tile = [(t, nid) for t, nid in picked if t >= 21000][:9]
    picked = sorted(clamp + tile, key=lambda item: (item[0], item[1]))
    if len(picked) < 8:
        raise RuntimeError(f"LIF excerpt too short: {len(picked)}")
    channels = ["lif.clamp" if t < 21000 else "lif.belt" for t, _ in picked]
    lif = OrderedDict(
        [
            ("model", "leaky_integrate_and_fire"),
            ("n", 88),
            ("dt_us", 100),
            ("tau_m_ms", 19.4),
            ("v_rest", 0.0),
            ("v_reset", 0.0),
            ("v_th", 1.0),
            ("r_m", 1.0),
            ("refractory_us", 1000),
            ("i_bias", 0.90),
            ("i_stim_peak", 2.52),
            ("stim_t_us", [21000, 25000]),
            ("i_clamp_extra", 0.69),
            ("clamp_n", 16),
            ("seed", 88457),
            (
                "note",
                "Population sim scoped to this sidecar. Plant remains designed. "
                "Neurons 0-15 carry +0.69 drum-clamp bias; stim 21-25 ms is the flake-belt tear.",
            ),
        ]
    )
    extra = OrderedDict(
        [
            ("excerpt_source", "independent_lif"),
            ("sim_scope", "sidecar_only"),
            ("lif", lif),
            ("abort_s", 1140),
            ("delayed_surprise_s", 1140),
        ]
    )
    return excerpt_items(picked, channels), extra


def record_456():
    ticks = [
        tick(2080, -0.02, 0.01, -0.02, -0.01, 0.01),
        tick(5200, -0.04, 0.01, -0.04, -0.02, 0.01),
        tick(5420, -0.03, 0.01, -0.03, -0.01, 0.01),
        tick(5980, -0.06, 0.02, -0.08, -0.03, 0.02),
        tick(6380, -0.02, 0.01, -0.03, -0.01, 0.01),
        tick(960000000, -0.01, 0.00, -0.02, 0.00, 0.00),
    ]
    spikes = [
        spike("enc.formalin.ctx", 1.140, 0.43),
        spike("rtd.shell.c", 2.280, 0.62),
        spike("bus.hb.seq", 3.640, 0.51),
        spike("bus.pb.ctx", 4.360, 0.46),
        spike("rtd.shell.c", 5.200, 1.33),
        spike("bus.hb.seq", 5.420, 1.16),
        spike("ctrl.gate", 5.980, 0.98),
        spike("rtd.shell.c", 7.160, 0.83),
        spike("bus.hb.seq", 9.280, 0.64),
        spike("ctrl.gate", 15.200, 0.86),
        spike("enc.formalin.ctx", 19.400, 0.40),
        spike("rtd.shell.c", 25.100, 0.57),
    ]
    excerpt = independent_excerpt(88456, 76, 28000, 12, spike_avoid_us(spikes))
    state = OrderedDict(
        [
            (
                "description",
                "Pentaerythritol condenser C-4 at Pentaol-Bield already holds a live shell RTD of 118.0 C when that analog sample races a Fieldbus keep-alive heartbeat still publishing sequence 148. Published trip is 132.0 C on the analog PV; a weak supervisor treats leftover heartbeat sequence as process T and zeros a legal 11.0 t/h formalin feed.",
            ),
            ("domain", "pentaerythritol-condenser"),
            ("sim_or_real", "designed"),
            (
                "goal",
                "Hold 11.0 t/h formalin on C-4, keep analog shell T < 132.0 C trip, and finish the 16 min pentaerythritol-quality window.",
            ),
            ("t0_us", 1762300000000456),
            ("gate_latency_us", 780),
            ("race_window_us", 400),
            ("race_window_rel_ms", [5.200, 5.600]),
            (
                "race",
                OrderedDict(
                    [
                        (
                            "contenders",
                            [
                                "rtd.shell.c 118.0 C analog process T",
                                "bus.hb.seq keep-alive sequence 148 (unitless)",
                            ],
                        ),
                        (
                            "semantics",
                            "PV-first should ACCEPT 11.0 t/h (118.0 C < 132.0 C trip). "
                            "Heartbeat-first would only delay confirmation of the same legal shell.",
                        ),
                        (
                            "window_derivation",
                            "400 us = one analog RTD slot versus the Fieldbus keep-alive publisher "
                            "on this 2 kHz condenser bus.",
                        ),
                        (
                            "order_evidence_note",
                            "Margin 220 us vs combined jitter 70 us (RTD 32 + heartbeat 38): 3.1x over "
                            "a 2.0x trust floor. Order is correctly PV-first. The error is binding "
                            "the keep-alive sequence as if it were the live process PV, not the race.",
                        ),
                    ]
                ),
            ),
            (
                "sensors",
                [
                    "shell RTD analog PV, 2 kHz, 32 us jitter, axis c4_shell_t, heartbeat_is_pv false",
                    "Fieldbus keep-alive sequence, 1 kHz, 38 us jitter, comms not process",
                    "formalin-feed encoder (context)",
                    "acetaldehyde header PT (context)",
                ],
            ),
            (
                "constraints",
                OrderedDict(
                    [
                        ("live_C", 118.0),
                        ("trip_C", 132.0),
                        ("heartbeat_seq", 148),
                        ("heartbeat_age_ms", 18),
                        ("heartbeat_fresh_ms", 200),
                        ("heartbeat_is_pv", False),
                        ("heartbeat_as_pv", True),
                        ("analog_fresh", True),
                        ("proposed_t_h", 11.0),
                    ]
                ),
            ),
            (
                "episode_steps",
                [
                    "1. Condenser C-4 indexed on Pentaol-Bield; analog PV 118.0 C, formalin 11.0 t/h armed.",
                    "2. Published live trip 132.0 C; keep-alive tagged as comms handshake, not process PV.",
                    "3. Encoder precursor at 1.140 ms.",
                    "4. Race window [5.200, 5.600] ms.",
                    "5. Analog PV 118.0 C at 5.200 ms (winner).",
                    "6. Heartbeat sequence 148 at 5.420 ms (loser by 220 us).",
                    "7. Gate at 5.980 ms: wrong REJECT holds 0 t/h on heartbeat-as-PV.",
                    "8. Feed idle; analog PV never crossed 132.0 C.",
                    "9. 16 min pentaerythritol window missed.",
                    "10. QA: correct gate was ACCEPT; leave 11.0 t/h; bind analog 118.0 vs 132.0 C trip.",
                ],
            ),
        ]
    )
    proposed = OrderedDict(
        [
            ("name", "penta_11_hold"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("feed_t_h", 11.0),
                        ("proc_C", 118.0),
                        ("hold", False),
                    ]
                ),
            ),
            (
                "evidence",
                OrderedDict(
                    [
                        ("live_C", 118.0),
                        ("trip_C", 132.0),
                        ("heartbeat_seq", 148),
                        ("heartbeat_age_ms", 18),
                        ("heartbeat_fresh_ms", 200),
                        ("heartbeat_is_pv", False),
                        ("heartbeat_as_pv", True),
                        ("analog_fresh", True),
                        ("ft_axis", "c4_shell_t"),
                        ("race_margin_us", 220),
                        ("combined_jitter_us", 70),
                        ("t_gate_us", 5980),
                    ]
                ),
            ),
            (
                "basis",
                "Planner proposes 11.0 t/h because analog PV 118.0 C is 14.0 C under the "
                "published 132.0 C trip and heartbeat sequence 148 is a keep-alive, not process T.",
            ),
        ]
    )
    safety = OrderedDict(
        [
            ("decision", "REJECT"),
            ("correctness", "incorrect"),
            (
                "rationale",
                "Keep-alive sequence prints 148, so the shell is treated as 148 C over the 132.0 C "
                "trip (true vs that leftover handshake slot). REJECT: hold 0 t/h until the heartbeat "
                "falls so the condenser does not see an over-temp event.",
            ),
            (
                "constraint_checked",
                OrderedDict(
                    [
                        (
                            "c4_shell_t",
                            OrderedDict(
                                [
                                    ("published_trip_C", 132.0),
                                    ("observed_analog_C", 118.0),
                                    ("heartbeat_as_pv_applied", True),
                                    ("heartbeat_seq", 148),
                                    ("executed_t_h", 0.0),
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
            ("name", "penta_hold_hb"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("feed_t_h", 0.0),
                        ("proc_C", 118.0),
                        ("hold", True),
                    ]
                ),
            ),
            (
                "gate_effect",
                "REJECT (incorrect): feed 11.0 -> 0 t/h. Routing relay.heartbeat.seq -> "
                "policy.hold_reject; no positive weight to policy.go_accept. Analog PV 118.0 C never "
                "violated the 132.0 C trip.",
            ),
        ]
    )
    future = OrderedDict(
        [
            (
                "summary",
                "Wrong-REJECT froze C-4 at 0 t/h while analog PV stayed 118.0 C under the "
                "132.0 C trip. 16 min pentaerythritol window missed. Correct gate was ACCEPT of the "
                "already-legal 11.0 t/h command.",
            ),
            (
                "state_delta",
                OrderedDict(
                    [
                        ("condenser", "held at 0 t/h; 11.0 t/h abandoned"),
                        ("proc_C", "still 118.0 C, under 132.0 C published trip"),
                        ("pentaerythritol", "16 min condensation window missed"),
                        ("flag", "no over-temp; heartbeat-as-PV false positive"),
                    ]
                ),
            ),
            (
                "surprises",
                [
                    "The 148 tag is a Fieldbus keep-alive sequence, not a live process PV.",
                    "Delayed (16 min): sister condenser C-5 ran the same 11.0 t/h window after QA rebound the analog trip; C-4's slot was already gone.",
                ],
            ),
            (
                "recovery",
                OrderedDict(
                    [
                        (
                            "correct_gate",
                            "ACCEPT: analog PV 118.0 C < published 132.0 C trip; leave 11.0 t/h; ignore keep-alive sequence.",
                        ),
                        ("correct_trip_C", 132.0),
                        ("wrong_flag", True),
                        (
                            "wrong_edit_applied",
                            OrderedDict([("feed_t_h", 0.0), ("hold", True)]),
                        ),
                        (
                            "cost",
                            "16 min missed pentaerythritol window (task/efficiency); analog PV never over trip (safety false-positive).",
                        ),
                    ]
                ),
            ),
            (
                "race_result",
                OrderedDict(
                    [
                        ("winner", "rtd.shell.c (5.200 ms, 118.0 C)"),
                        ("loser", "bus.hb.seq (5.420 ms, leftover keep-alive 148)"),
                        ("margin_us", 220),
                        (
                            "counterfactual_if_reversed",
                            "Heartbeat-first by < 220 us would still show analog PV 118.0 C < 132.0. A "
                            "correct gate ACCEPTs either way. The wrong REJECT spent the PV win "
                            "on leftover keep-alive sequence.",
                        ),
                    ]
                ),
            ),
            ("reward_inflection_t_us", 5980),
            (
                "reward_inflection_note",
                "Task and efficiency drop at the wrong REJECT (5.980 ms, tick 4). The 16 min "
                "missed window is delayed surprise, not the inflection.",
            ),
            ("delayed_surprise_s", 960.0),
            ("missed_window_s", 960),
        ]
    )
    ras = raster_core(
        28,
        76,
        32,
        68,
        routing(
            "relay.heartbeat.seq",
            "policy.hold_reject",
            [
                ("relay.heartbeat.seq", "policy.hold_reject", 0.74),
                ("relay.rtd.shell", "policy.hold_reject", 0.19),
            ],
            "acetylcholine",
            0.08,
            "heartbeat_as_pv_stdp; ACh tags the (wrong) hold_reject bind at the analog PV win",
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
                    pop("hold_reject", 48, 0.50, 210.0, 4),
                    pop("go_accept", 48, 0.80, 8.0, 0),
                    pop("temp_trip_veto", 24, 0.75),
                ],
            ),
        ]
    )
    return wrap_record(
        "ttf-r88-456",
        "WRONG-REJECT at Pentaol-Bield / C-4: analog PV 118.0 C is legal vs "
        "published 132.0 C trip; supervisor bound leftover Fieldbus keep-alive sequence as the process PV",
        state,
        spikes,
        proposed,
        safety,
        executed,
        future,
        ticks,
        "Wrong-reject. Sidecar arithmetic 118.0 < 132.0 is true; clamp bound to leftover "
        "keep-alive sequence. total -0.36 = -0.18 + 0.06 + -0.22 + -0.08 + 0.06.",
        ras,
        gate,
        "pentaerythritol-condenser",
        [
            "reject",
            "wrong-gate",
            "heartbeat-as-pv",
            "stale-handshake",
            "sidecar-convictable",
            "designed",
        ],
        "Teaches a probe that a correct analog-PV<trip read can still be a wrong gate when "
        "routing.table[0].to is policy.hold_reject and executed feed is zeroed.",
        1,
        supervisor_error_type="wrong-reject",
    )


def record_457():
    excerpt, extra = lif_457_excerpt()
    ticks = [
        tick(1840, 0.05, -0.02, -0.02, 0.01, 0.00),
        tick(4600, 0.08, -0.04, -0.03, 0.01, -0.01),
        tick(4840, 0.04, -0.03, -0.02, 0.00, 0.00),
        tick(5500, 0.10, -0.06, -0.03, 0.02, -0.01),
        tick(22400, 0.05, -0.42, -0.04, 0.00, -0.02),
        tick(1140000000, 0.02, -0.05, -0.02, 0.00, 0.00),
    ]
    state = OrderedDict(
        [
            (
                "description",
                "Flake drum FD-3 at Flaker-Sneck is already pulling 16 t/h vanadium pentoxide melt when a drum-temperature pulse arrives 240 us before the flake-flow encoder that still reads a legal belt. Temperature-first latches a process clamp under the 405 C cap; flow-first would keep cruise melt. Stored flake-belt tear load is not yet an observable of either race channel.",
            ),
            ("domain", "vanadium-pentoxide-flaker"),
            ("sim_or_real", "designed"),
            (
                "goal",
                "Keep FD-3 on 16 t/h melt only while drum temperature stays <= 405 C, and "
                "leave the flake belt un-torn.",
            ),
            ("t0_us", 1762300000000457),
            ("gate_latency_us", 900),
            ("race_window_us", 400),
            ("race_window_rel_ms", [4.600, 5.000]),
            (
                "race",
                OrderedDict(
                    [
                        (
                            "contenders",
                            [
                                "rtd.drum.c 418 C vanadium-pentoxide drum",
                                "ft.flake.t_h 16 t/h still-legal belt flow",
                            ],
                        ),
                        (
                            "semantics",
                            "Temperature-first latches melt clamp 16 -> 9 t/h; flow-first keeps "
                            "cruise melt on a 'belt still tracking' model.",
                        ),
                        (
                            "window_derivation",
                            "400 us = one drum RTD slot minus flow-encoder group delay on this "
                            "1 kHz flaker bus.",
                        ),
                        (
                            "order_evidence_note",
                            "Margin 240 us vs combined jitter 68 us (RTD 30 + flow 38): 3.5x over "
                            "a 2.0x trust floor. Reversing order by < 240 us inside the 400 us window "
                            "would have kept 16 t/h cruise; predicted next-sample drum 408 C > 405 cap.",
                        ),
                    ]
                ),
            ),
            (
                "sensors",
                [
                    "V2O5 drum RTD, 1 kHz, 30 us timestamp jitter",
                    "flake-flow encoder, 1 kHz, 38 us jitter",
                    "belt-valve encoder (context)",
                    "belt AE (context)",
                ],
            ),
            (
                "constraints",
                OrderedDict(
                    [
                        ("drum_cap_C", 405.0),
                        ("observed_drum_C", 418.0),
                        ("proposed_melt_t_h", 16.0),
                        ("melt_floor_t_h", 7.0),
                    ]
                ),
            ),
            (
                "episode_steps",
                [
                    "1. Flake drum FD-3 indexed; 16 t/h melt; drum 418 C > 405 cap.",
                    "2. Cruise melt 16 t/h armed; drum over the 405 C cap.",
                    "3. Encoder precursor at 1.080 ms; drum-side warm-start 418 C.",
                    "4. Race window [4.600, 5.000] ms opens on the flaker bus.",
                    "5. Drum RTD 418 C at 4.600 ms (winner).",
                    "6. Flake flow 16 t/h at 4.840 ms (loser by 240 us).",
                    "7. Gate at 5.500 ms (winner + 900 us): MODIFY clamp 16 -> 9 t/h.",
                    "8. Clamp executes; next-sample drum 399 C < 405 cap.",
                    "9. At 22.400 ms stored flake-belt tear opens a 40 mm slit.",
                    "10. Emergency isolate 19 min + belt pull; named un-netted loss, not folded into process heads.",
                ],
            ),
        ]
    )
    proposed = OrderedDict(
        [
            ("name", "cruise_melt_flake"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("melt_t_h", 16.0),
                        ("drum_C", 418.0),
                        ("hold", False),
                    ]
                ),
            ),
            (
                "evidence",
                OrderedDict(
                    [
                        ("drum_C", 418.0),
                        ("drum_cap_C", 405.0),
                        ("predicted_unclamped_next_C", 408.0),
                        ("melt_t_h", 16.0),
                        ("race_margin_us", 240),
                        ("combined_jitter_us", 68),
                    ]
                ),
            ),
            (
                "basis",
                "Planner proposes 16 t/h cruise: flake flow looks like a tracking belt, not a "
                "torn slit, and the 405 C drum cap is treated as still open.",
            ),
        ]
    )
    safety = OrderedDict(
        [
            ("decision", "MODIFY"),
            ("correctness", "correct"),
            (
                "rationale",
                "Drum 418 C won by 240 us, so the belt is running packed, not still "
                "tracking free. Holding 16 t/h predicts next-sample 408 C > 405 C cap. MODIFY: melt "
                "16 -> 9 t/h. Observed after clamp 399 C < 405. A full REJECT is not "
                "indicated: a sound flaker accepts 9 t/h.",
            ),
            (
                "constraint_checked",
                OrderedDict(
                    [
                        (
                            "drum_C",
                            OrderedDict(
                                [
                                    ("cap", 405.0),
                                    ("observed", 418.0),
                                    ("predicted_unclamped_next", 408.0),
                                    ("clamped_melt_t_h", 9.0),
                                    ("observed_after_clamp", 399.0),
                                ]
                            ),
                        ),
                        (
                            "order_evidence",
                            OrderedDict(
                                [
                                    ("margin_us", 240),
                                    ("combined_jitter_us", 68),
                                    ("ratio", 3.53),
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
            ("name", "clamped_melt_flake"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("melt_t_h", 9.0),
                        ("drum_C", 399.0),
                        ("hold", False),
                    ]
                ),
            ),
            (
                "gate_effect",
                "MODIFY: melt 16 -> 9 t/h. Process-correct vs the 405 C drum cap. Flake-belt "
                "tear still occurs at 22.400 ms.",
            ),
        ]
    )
    future = OrderedDict(
        [
            (
                "summary",
                "Process-correct MODIFY held drum at 399 C. At 22.400 ms stored belt load "
                "tore a 40 mm slit. Clamp reduced melt energy; it did not dump the belt charge. "
                "Partnered negative: process heads stay honest; world loss is named, not netted.",
            ),
            (
                "state_delta",
                OrderedDict(
                    [
                        ("melt", "clamp executed; drum 399 C < 405"),
                        ("flake_belt", "tear at 22.400 ms"),
                        ("repair", "19 min emergency isolate + belt pull"),
                        ("mission", "drum still flaking; belt precursor controlled"),
                    ]
                ),
            ),
            (
                "surprises",
                [
                    "Neither drum RTD nor flake flow predicted the belt charge; ae.flake.belt is a new channel at 22.400 ms, 16.900 ms after the gate, still inside the 42 ms raster.",
                    "Delayed (19 min): emergency isolate and belt pull close the tear. Named un-netted loss, not folded into task_progress.",
                ],
            ),
            (
                "un_netted_loss",
                "19 min emergency isolate + belt pull after a flake-belt tear. Safety "
                "head -0.62 prices the precursor; task_progress stays +0.34 because the melt clamp "
                "completed under the 405 C cap. World loss is named here, not subtracted from process heads.",
            ),
            (
                "race_result",
                OrderedDict(
                    [
                        ("winner", "rtd.drum.c (4.600 ms, 418 C)"),
                        ("loser", "ft.flake.t_h (4.840 ms, 16 t/h)"),
                        ("margin_us", 240),
                        (
                            "counterfactual_if_reversed",
                            "Flow-first by < 240 us inside the 400 us window would have kept "
                            "16 t/h cruise; predicted next-sample 408 C would have exceeded the "
                            "405 C cap even without the belt charge. The MODIFY is still the "
                            "correct process. The tear is a later world charge either way, cheaper "
                            "with the clamp than without.",
                        ),
                    ]
                ),
            ),
            ("reward_inflection_t_us", 22400),
            (
                "reward_inflection_note",
                "Safety collapses at the 22.400 ms flake-belt tear (tick t_us=22400), inside the "
                "42 ms raster. The correct MODIFY at 5.500 ms is in the same excerpt. Do not put "
                "inflection on the +19 min isolate tick.",
            ),
            ("delayed_surprise_s", 1140.0),
            ("abort_s", 1140),
        ]
    )
    spikes = [
        spike("enc.melt.ctx", 1.080, 0.42),
        spike("rtd.drum.c", 2.280, 0.63),
        spike("ft.flake.t_h", 3.160, 0.54),
        spike("rtd.drum.c", 4.600, 1.35),
        spike("ft.flake.t_h", 4.840, 1.11),
        spike("ctrl.gate", 5.500, 0.96),
        spike("rtd.drum.c", 7.200, 0.80),
        spike("ft.flake.t_h", 10.400, 0.65),
        spike("ctrl.gate", 15.200, 0.83),
        spike("ae.flake.belt", 22.400, 1.44),
        spike("ae.flake.belt", 23.700, 0.90),
        spike("enc.melt.ctx", 31.000, 0.40),
        spike("rtd.drum.c", 38.200, 0.56),
    ]
    ras = raster_core(
        42,
        88,
        26,
        96,
        routing(
            "thalamic-relay.rtd-drum",
            "spikenaut.policy.melt-clamp",
            [
                ("relay.rtd.drum", "policy.melt_clamp", 0.65),
                ("relay.ft.flake", "policy.belt_hold", 0.28),
                ("relay.ae.belt", "policy.melt_clamp", -0.47),
            ],
            "noradrenaline",
            0.05,
            "surprise-gated pre_post_stdp; NA at RTD win (4.600 ms) opens a 50 ms eligibility "
            "trace that still covers the 22.400 ms flake-belt tear",
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
                    pop("melt_clamp", 48, 0.50, 220.0, 4),
                    pop("belt_hold", 48, 0.50, 50.0, 1),
                    pop("drum_cap_veto", 24, 0.75),
                ],
            ),
        ]
    )
    return wrap_record(
        "ttf-r88-457",
        "Flaker-Sneck V2O5 / FD-3: drum RTD beats flake encoder by 240 us; correct "
        "MODIFY still eats an in-window flake-belt tear (partnered negative total -0.44)",
        state,
        spikes,
        proposed,
        safety,
        executed,
        future,
        ticks,
        "Partnered negative. Process-correct MODIFY; world still charges inside the "
        "42 ms raster. total -0.44 = 0.34 + -0.62 + -0.16 + 0.04 + -0.04. Named "
        "isolate+belt-pull loss is not netted into task_progress.",
        ras,
        gate,
        "vanadium-pentoxide-flaker",
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
        "19 min gap.",
        2,
    )


def record_458():
    ticks = [
        tick(1616, 0.01, 0.04, 0.02, 0.01, 0.01),
        tick(4040, 0.02, 0.08, 0.02, 0.02, 0.01),
        tick(4250, 0.01, 0.06, 0.02, 0.01, 0.01),
        tick(5300, 0.03, 0.12, 0.04, 0.04, 0.02),
        tick(5620, 0.02, 0.07, 0.01, 0.01, 0.01),
        tick(420000000, 0.01, 0.03, 0.01, 0.01, 0.00),
    ]
    spikes = [
        spike("enc.ore.ctx", 1.020, 0.43),
        spike("ae.bottoms.pps", 2.180, 0.70),
        spike("enc.reflux.th", 3.060, 0.51),
        spike("ae.bottoms.pps", 4.040, 1.37),
        spike("enc.reflux.th", 4.250, 1.13),
        spike("ctrl.gate", 5.300, 0.97),
        spike("ae.bottoms.pps", 7.400, 0.81),
        spike("enc.reflux.th", 11.000, 0.60),
        spike("ctrl.gate", 16.400, 0.85),
        spike("ae.bottoms.pps", 24.800, 0.69),
        spike("enc.reflux.th", 33.600, 0.47),
        spike("t.reboiler.ctx", 41.200, 0.39),
    ]
    excerpt = independent_excerpt(88458, 108, 44000, 13, spike_avoid_us(spikes))
    state = OrderedDict(
        [
            (
                "description",
                "Titanium-tetrachloride HIL still ST-7 at Titantet-Stell already shows still-bottoms acoustic emission at 48 pps when that burst races a reflux encoder still printing 2.1 t/h. Reflux is legal only if AE <= 36 pps. AE-first latches hold; encoder-first would treat in-band t/h as bottoms clearance.",
            ),
            ("domain", "titanium-tetrachloride-still"),
            ("sim_or_real", "hil"),
            (
                "goal",
                "Do not raise ST-7 reflux unless bottoms AE <= 36 pps; keep ore feed 0 t/h until the "
                "reboiler is quiet.",
            ),
            ("t0_us", 1762300000000458),
            ("gate_latency_us", 1260),
            ("race_window_us", 320),
            ("race_window_rel_ms", [4.040, 4.360]),
            (
                "race",
                OrderedDict(
                    [
                        (
                            "contenders",
                            [
                                "ae.bottoms.pps 48 pps still-bottoms flare",
                                "enc.reflux.th 2.1 t/h still-in-band reflux",
                            ],
                        ),
                        (
                            "semantics",
                            "AE-first latches REJECT hold 0 t/h; encoder-first would keep 2.1 t/h "
                            "on an in-band-rate-as-clearance model.",
                        ),
                        (
                            "window_derivation",
                            "320 us = one AE envelope slot versus the reflux-encoder publisher "
                            "on this pad cycle.",
                        ),
                        (
                            "order_evidence_note",
                            "Margin 210 us vs combined jitter 56 us (AE 24 + encoder 32): 3.8x over a "
                            "2.0x trust floor. Pad injects encoder 80-120 us before the AE envelope "
                            "finishes (loop lag, not a sensor fault); the encoder packet is still "
                            "the loser in this 320 us window.",
                        ),
                    ]
                ),
            ),
            (
                "sensors",
                [
                    "still-bottoms AE analyzer, 24 us jitter, 36 pps trip",
                    "reflux encoder, 32 us jitter",
                    "reboiler RTD (context)",
                    "TiCl4 off-gas (context)",
                ],
            ),
            (
                "constraints",
                OrderedDict(
                    [
                        ("ae_trip_pps", 36.0),
                        ("observed_ae_pps", 48.0),
                        ("reflux_cap_t_h", 3.0),
                        ("proposed_reflux_t_h", 2.1),
                    ]
                ),
            ),
            (
                "hil",
                OrderedDict(
                    [
                        ("bench", "Titantet-Stell TS-HIL titanium-tetrachloride pad, ST-7"),
                        ("inject", "AE envelope delayed 80-120 us vs encoder; loop lag, not a false AE pickup"),
                    ]
                ),
            ),
            (
                "episode_steps",
                [
                    "1. ST-7 on Titantet-Stell HIL pad; ore armed; reflux 2.1 t/h.",
                    "2. AE trip 36 pps; observed 48 pps still-bottoms flare.",
                    "3. Encoder precursor at 1.020 ms.",
                    "4. Race window [4.040, 4.360] ms.",
                    "5. AE 48 pps at 4.040 ms (winner).",
                    "6. Reflux encoder 2.1 t/h at 4.250 ms (loser by 210 us).",
                    "7. Gate at 5.300 ms: REJECT hold 0 t/h, do not raise boil-up.",
                    "8. Pad recycle 7 min; AE decays under 36 pps after hold.",
                    "9. Reboiler never ran a bottoms dump; encoder-as-clearance would have refluxed into the flare.",
                    "10. QA: correct gate was REJECT; leave 0 t/h until AE <= 36 pps.",
                ],
            ),
        ]
    )
    proposed = OrderedDict(
        [
            ("name", "reflux_2p1"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("reflux_t_h", 2.1),
                        ("ae_pps", 48.0),
                        ("hold", False),
                    ]
                ),
            ),
            (
                "evidence",
                OrderedDict(
                    [
                        ("ae_pps", 48.0),
                        ("ae_trip_pps", 36.0),
                        ("reflux_t_h", 2.1),
                        ("reflux_cap_t_h", 3.0),
                        ("race_margin_us", 210),
                        ("combined_jitter_us", 56),
                        ("t_gate_us", 5300),
                    ]
                ),
            ),
            (
                "basis",
                "Planner proposes 2.1 t/h because reflux is under the 3.0 t/h cap and treats "
                "the encoder as bottoms clearance, ignoring the 48 pps AE flare.",
            ),
        ]
    )
    safety = OrderedDict(
        [
            ("decision", "REJECT"),
            ("correctness", "correct"),
            (
                "rationale",
                "AE 48 pps won by 210 us and is over the 36 pps trip. Encoder 2.1 t/h is under "
                "the 3.0 t/h cap but is not clearance. REJECT: hold 0 t/h until AE <= 36 pps.",
            ),
            (
                "constraint_checked",
                OrderedDict(
                    [
                        (
                            "bottoms_ae_pps",
                            OrderedDict(
                                [
                                    ("trip", 36.0),
                                    ("observed", 48.0),
                                    ("executed_reflux_t_h", 0.0),
                                ]
                            ),
                        ),
                        (
                            "order_evidence",
                            OrderedDict(
                                [
                                    ("margin_us", 210),
                                    ("combined_jitter_us", 56),
                                    ("ratio", 3.75),
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
            ("name", "reflux_hold_ae"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("reflux_t_h", 0.0),
                        ("ae_pps", 48.0),
                        ("hold", True),
                    ]
                ),
            ),
            (
                "gate_effect",
                "REJECT: reflux 2.1 -> 0 t/h. Routing relay.ae.bottoms -> policy.hold_reject. "
                "Do not reflux into the 48 pps flare.",
            ),
        ]
    )
    future = OrderedDict(
        [
            (
                "summary",
                "Correct REJECT held ST-7 at 0 t/h while AE 48 pps decayed. Encoder-as-clearance "
                "would have refluxed 2.1 t/h into the flare. Pad recycle 7 min.",
            ),
            (
                "state_delta",
                OrderedDict(
                    [
                        ("reflux", "held at 0 t/h"),
                        ("bottoms", "AE flare decaying under trip after hold"),
                        ("reboiler", "no bottoms dump"),
                        ("pad", "7 min recycle"),
                    ]
                ),
            ),
            (
                "surprises",
                [
                    "Pad injects encoder 80-120 us before AE envelope finish; that is loop lag, not a false AE pickup.",
                    "Delayed (7 min): pad recycle restacks the TiCl4 still after AE < 36 pps.",
                ],
            ),
            (
                "race_result",
                OrderedDict(
                    [
                        ("winner", "ae.bottoms.pps (4.040 ms, 48 pps)"),
                        ("loser", "enc.reflux.th (4.250 ms, 2.1 t/h)"),
                        ("margin_us", 210),
                        (
                            "counterfactual_if_reversed",
                            "Encoder-first by < 210 us would have treated 2.1 t/h as clearance and "
                            "refluxed into the 48 pps flare. The REJECT is still required; reversal "
                            "only delays the AE bind.",
                        ),
                    ]
                ),
            ),
            ("reward_inflection_t_us", 5300),
            (
                "reward_inflection_note",
                "Safety credit lands at the correct REJECT (5.300 ms, tick 4). Pad recycle is delayed surprise.",
            ),
            ("delayed_surprise_s", 420.0),
            ("pad_recycle_s", 420),
        ]
    )
    ras = raster_core(
        44,
        108,
        22,
        105,
        routing(
            "relay.ae.bottoms",
            "policy.hold_reject",
            [
                ("relay.ae.bottoms", "policy.hold_reject", 0.75),
                ("relay.enc.reflux", "policy.reflux_go", 0.17),
            ],
            "dopamine",
            0.06,
            "ae_trip_stdp; DA tags the hold_reject bind at the AE win",
        ),
        excerpt,
    )
    gate = OrderedDict(
        [
            ("decision_window_ms", 0.32),
            ("decision", "REJECT"),
            (
                "populations",
                [
                    pop("hold_reject", 64, 0.50, 200.0, 4),
                    pop("reflux_go", 64, 0.80, 8.0, 0),
                    pop("ae_trip_veto", 32, 0.70),
                ],
            ),
        ]
    )
    return wrap_record(
        "ttf-r88-458",
        "Titantet-Stell TiCl4 HIL / ST-7: bottoms AE 48 pps beats reflux encoder 2.1 t/h by 210 us; "
        "correct REJECT holds the still",
        state,
        spikes,
        proposed,
        safety,
        executed,
        future,
        ticks,
        "Correct REJECT. AE 48 > 36 trip beats in-band reflux. total +0.78 = "
        "0.10 + 0.40 + 0.12 + 0.10 + 0.06.",
        ras,
        gate,
        "titanium-tetrachloride-still",
        [
            "reject",
            "hil-pad",
            "ae-vs-encoder",
            "bottoms-hold",
            "sidecar-convictable",
            "hil",
        ],
        "Teaches a probe that an in-band reflux encoder is not bottoms clearance when "
        "AE is over trip and routing.table[0].to is policy.hold_reject.",
        3,
    )


def record_459():
    ticks = [
        tick(2200, 0.06, 0.04, 0.03, 0.02, 0.01),
        tick(5500, 0.10, 0.06, 0.04, 0.02, 0.02),
        tick(5740, 0.06, 0.04, 0.02, 0.01, 0.01),
        tick(6360, 0.12, 0.08, 0.05, 0.03, 0.02),
        tick(6740, 0.05, 0.04, 0.02, 0.01, 0.01),
        tick(510000000, 0.03, 0.02, 0.02, 0.01, 0.01),
    ]
    params = OrderedDict(
        [
            ("feed_t_h", 6.4),
            ("kettle_C", 86.0),
            ("al_id", 2),
            ("hold", False),
        ]
    )
    spikes = [
        spike("ft.isobut.ctx", 1.280, 0.41),
        spike("rtd.kettle.c", 2.860, 0.57),
        spike("ir.coil.smear", 4.280, 0.49),
        spike("rtd.kettle.c", 5.500, 1.27),
        spike("ir.coil.smear", 5.740, 1.09),
        spike("ctrl.gate", 6.360, 0.95),
        spike("rtd.kettle.c", 8.600, 0.73),
        spike("ir.coil.smear", 12.100, 0.59),
        spike("ctrl.gate", 17.400, 0.81),
        spike("rtd.kettle.c", 23.800, 0.54),
        spike("ft.isobut.ctx", 28.600, 0.39),
    ]
    excerpt = independent_excerpt(88459, 60, 32000, 12, spike_avoid_us(spikes))
    state = OrderedDict(
        [
            (
                "description",
                "Neopentyl-glycol aldol kettle AL-2 at Neopent-Lair already holds a liquor RTD of 86.0 C when that analog sample races a coil-skin IR smear still printing 104 C. Commanded 6.4 t/h and 86.0 C sit 1.4 t/h and 12 C inside the legal envelopes. The kettle win only ratifies the isobutyraldehyde already in the jacket.",
            ),
            ("domain", "neopentyl-glycol-aldol"),
            ("sim_or_real", "simulated"),
            (
                "goal",
                "Finish the NPG aldol pass on Neopent-Lair, keep kettle <= 98.0 C and "
                "feed >= 5.0 t/h, and leave coil draft in spec.",
            ),
            ("t0_us", 1762300000000459),
            ("gate_latency_us", 860),
            ("race_window_us", 380),
            ("race_window_rel_ms", [5.500, 5.880]),
            (
                "race",
                OrderedDict(
                    [
                        (
                            "contenders",
                            [
                                "rtd.kettle.c 86.0 C aldol liquor",
                                "ir.coil.smear 104 C over-temp claim",
                            ],
                        ),
                        (
                            "semantics",
                            "Kettle-first confirms the already-legal 6.4 t/h / 86.0 C pass; "
                            "smear-first would have treated the kettle RTD as a smear echo and looked "
                            "for an extra hold the jacket does not need.",
                        ),
                        (
                            "window_derivation",
                            "380 us = one 1D-aldol hotspot kernel step versus the coil-IR publisher "
                            "on this rigid condensation train.",
                        ),
                        (
                            "order_evidence_note",
                            "Margin 240 us vs combined jitter 72 us (kettle 32 + coil 40): 3.3x over "
                            "a 2.0x trust floor. Reversing order by < 240 us would not make the "
                            "proposed pass illegal; it would only have delayed confirmation.",
                        ),
                    ]
                ),
            ),
            (
                "sensors",
                [
                    "kettle liquor RTD, 32 us jitter",
                    "coil-skin IR smear, 40 us jitter",
                    "isobutyraldehyde encoder (context)",
                    "formaldehyde GC (context)",
                ],
            ),
            (
                "constraints",
                OrderedDict(
                    [
                        ("kettle_cap_C", 98.0),
                        ("observed_kettle_C", 86.0),
                        ("feed_floor_t_h", 5.0),
                        ("proposed_feed_t_h", 6.4),
                    ]
                ),
            ),
            (
                "simulation",
                OrderedDict(
                    [
                        (
                            "solver",
                            "1D neopentyl-glycol aldol hotspot kernel + shrinking-core isobutyraldehyde feed, seed 88; 12 axial nodes; NOT lumped tank, NOT a fluid-LES field",
                        ),
                        (
                            "fidelity_limits",
                            "No radial maldistribution or coil-side coke; jackets are rigid temperature sources. Raster is kernelized events, not an independent LIF.",
                        ),
                    ]
                ),
            ),
            (
                "episode_steps",
                [
                    "1. Neopent-Lair aldol indexed; AL-2 holding 6.4 t/h at 86.0 C kettle.",
                    "2. Caps: kettle 98.0 C, feed floor 5.0 t/h; both proposed values inside.",
                    "3. Isobut precursor at 1.280 ms.",
                    "4. Race window [5.500, 5.880] ms.",
                    "5. Kettle RTD 86.0 C at 5.500 ms (winner).",
                    "6. Coil IR smear 104 C at 5.740 ms (loser by 240 us).",
                    "7. Gate at 6.360 ms: ACCEPT 6.4 t/h / 86.0 C already legal.",
                    "8. Pass continues; no extra hold.",
                    "9. 8.5 min survey confirms coil draft still in spec.",
                    "10. QA: ACCEPT params identical to proposed.",
                ],
            ),
        ]
    )
    proposed = OrderedDict(
        [
            ("name", "aldol_6p4_thold"),
            ("parameters", params),
            (
                "evidence",
                OrderedDict(
                    [
                        ("kettle_C", 86.0),
                        ("kettle_cap_C", 98.0),
                        ("feed_t_h", 6.4),
                        ("feed_floor_t_h", 5.0),
                        ("race_margin_us", 240),
                        ("combined_jitter_us", 72),
                        ("t_gate_us", 6360),
                    ]
                ),
            ),
            (
                "basis",
                "Planner proposes 6.4 t/h because kettle 86.0 C is 12.0 C under the 98.0 C cap "
                "and feed is 1.4 t/h over the 5.0 t/h floor.",
            ),
        ]
    )
    safety = OrderedDict(
        [
            ("decision", "ACCEPT"),
            ("correctness", "correct"),
            (
                "rationale",
                "Kettle 86.0 C won by 240 us and is under 98.0 C. Feed 6.4 t/h is over "
                "5.0 t/h. ACCEPT the already-legal pass; coil IR smear is not a cap violation.",
            ),
            (
                "constraint_checked",
                OrderedDict(
                    [
                        (
                            "kettle_C",
                            OrderedDict(
                                [
                                    ("cap", 98.0),
                                    ("observed", 86.0),
                                    ("executed_feed_t_h", 6.4),
                                ]
                            ),
                        ),
                        (
                            "order_evidence",
                            OrderedDict(
                                [
                                    ("margin_us", 240),
                                    ("combined_jitter_us", 72),
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
            ("name", "aldol_6p4_thold"),
            ("parameters", params),
            (
                "gate_effect",
                "ACCEPT: feed 6.4 t/h and kettle 86.0 C unchanged. Routing relay.rtd.kettle "
                "-> policy.go_accept.",
            ),
        ]
    )
    future = OrderedDict(
        [
            (
                "summary",
                "Correct ACCEPT left AL-2 at 6.4 t/h / 86.0 C. Coil IR smear did not justify a "
                "hold. 8.5 min survey confirmed draft in spec.",
            ),
            (
                "state_delta",
                OrderedDict(
                    [
                        ("aldol", "still 6.4 t/h / 86.0 C"),
                        ("coils", "in spec after survey"),
                        ("train", "NPG continues"),
                        ("hold", "none applied"),
                    ]
                ),
            ),
            (
                "surprises",
                [
                    "Coil IR smear is an off-jacket optical claim, not a kettle-temperature violation.",
                    "Delayed (8.5 min): survey restacks AL-2 without a recovery hold.",
                ],
            ),
            (
                "race_result",
                OrderedDict(
                    [
                        ("winner", "rtd.kettle.c (5.500 ms, 86.0 C)"),
                        ("loser", "ir.coil.smear (5.740 ms, 104 C claim)"),
                        ("margin_us", 240),
                        (
                            "counterfactual_if_reversed",
                            "Smear-first by < 240 us would only delay confirmation. The pass stays "
                            "legal either way; ACCEPT is still required.",
                        ),
                    ]
                ),
            ),
            ("reward_inflection_t_us", 6360),
            (
                "reward_inflection_note",
                "Task credit lands at the ACCEPT (6.360 ms, tick 4). Survey is delayed surprise.",
            ),
            ("delayed_surprise_s", 510.0),
            ("survey_s", 510),
        ]
    )
    ras = raster_core(
        32,
        60,
        36,
        69,
        routing(
            "relay.rtd.kettle",
            "policy.go_accept",
            [
                ("relay.rtd.kettle", "policy.go_accept", 0.69),
                ("relay.ir.coil", "policy.smear_hold", 0.20),
            ],
            "serotonin",
            0.07,
            "legal_aldol_stdp; 5-HT tags the go_accept bind at the kettle-RTD win",
        ),
        excerpt,
    )
    gate = OrderedDict(
        [
            ("decision_window_ms", 0.38),
            ("decision", "ACCEPT"),
            (
                "populations",
                [
                    pop("go_accept", 40, 0.50, 180.0, 3),
                    pop("smear_hold", 40, 0.80, 10.0, 0),
                    pop("kettle_cap_veto", 20, 0.75),
                ],
            ),
        ]
    )
    return wrap_record(
        "ttf-r88-459",
        "Neopent-Lair aldol / AL-2: kettle 86.0 C beats coil smear by 240 us; ACCEPT "
        "already-legal 6.4 t/h pass",
        state,
        spikes,
        proposed,
        safety,
        executed,
        future,
        ticks,
        "Correct ACCEPT of an already-legal 1D NPG aldol hotspot pass. total +1.06 = "
        "0.42 + 0.28 + 0.18 + 0.10 + 0.08.",
        ras,
        gate,
        "neopentyl-glycol-aldol",
        [
            "accept",
            "already-legal",
            "simulated-aldol-train",
            "kettle-vs-coil",
            "sidecar-convictable",
            "simulated",
        ],
        "Teaches that a kettle RTD under cap can confirm an already-legal aldol pass without "
        "a coil-IR smear becoming a hold.",
        4,
    )


def record_460():
    ticks = [
        tick(1520, 0.06, 0.04, 0.03, 0.02, 0.01),
        tick(3800, 0.10, 0.08, 0.04, 0.02, 0.02),
        tick(4000, 0.06, 0.04, 0.02, 0.02, 0.01),
        tick(4500, 0.12, 0.08, 0.05, 0.04, 0.02),
        tick(4840, 0.06, 0.05, 0.02, 0.01, 0.01),
        tick(330000000, 0.04, 0.03, 0.02, 0.01, 0.01),
    ]
    params = OrderedDict(
        [
            ("feed_t_h", 4.6),
            ("raffinate_C", 38.2),
            ("sp_id", 5),
            ("hold", False),
        ]
    )
    spikes = [
        spike("enc.feed.ctx", 0.820, 0.40),
        spike("rtd.raff.c", 1.960, 0.59),
        spike("ir.vapor.glint", 2.900, 0.50),
        spike("rtd.raff.c", 3.800, 1.29),
        spike("ir.vapor.glint", 4.000, 1.11),
        spike("ctrl.gate", 4.500, 0.96),
        spike("rtd.raff.c", 6.200, 0.77),
        spike("ir.vapor.glint", 8.400, 0.61),
        spike("ctrl.gate", 12.800, 0.84),
        spike("rtd.raff.c", 16.800, 0.53),
        spike("ir.vapor.glint", 19.600, 0.42),
    ]
    excerpt = independent_excerpt(88460, 52, 22000, 11, spike_avoid_us(spikes))
    state = OrderedDict(
        [
            (
                "description",
                "Isoprene extractive splitter SP-5 at Isopren-Twine already holds a raffinate RTD of 38.2 C when that analog sample races a vapor-space IR glint still printing 61 C. Commanded 4.6 t/h and 38.2 C sit 1.1 t/h over the 3.5 t/h floor and 13.8 C under the 52.0 C cap. The raffinate win only ratifies the C5 already in the acetonitrile column.",
            ),
            ("domain", "isoprene-acetonitrile-extract"),
            ("sim_or_real", "designed"),
            (
                "goal",
                "Run SP-5 at 4.6 t/h, keep raffinate <= 52.0 C and vapor IR <= 90 C, "
                "and leave the isoprene train on schedule.",
            ),
            ("t0_us", 1762300000000460),
            ("gate_latency_us", 700),
            ("race_window_us", 340),
            ("race_window_rel_ms", [3.800, 4.140]),
            (
                "race",
                OrderedDict(
                    [
                        (
                            "contenders",
                            [
                                "rtd.raff.c 38.2 C raffinate",
                                "ir.vapor.glint vapor-space hitch claim",
                            ],
                        ),
                        (
                            "semantics",
                            "Raffinate-first confirms the already-legal 4.6 t/h / 38.2 C pass; glint-first "
                            "would have treated the raffinate RTD as a hitch echo and looked for an extra hold "
                            "the splitter does not need.",
                        ),
                        (
                            "window_derivation",
                            "340 us = one raffinate-RTD slot versus the vapor-IR publisher on this "
                            "extractive-splitter bus.",
                        ),
                        (
                            "order_evidence_note",
                            "Margin 200 us vs combined jitter 58 us (raffinate 26 + IR 32): 3.4x over "
                            "a 2.0x trust floor. Reversing order by < 200 us would not make the "
                            "proposed pass illegal; it would only have delayed confirmation.",
                        ),
                    ]
                ),
            ),
            (
                "sensors",
                [
                    "raffinate RTD, 26 us jitter",
                    "vapor-space IR glint, 32 us jitter",
                    "C5 encoder (context)",
                    "acetonitrile assay (context)",
                ],
            ),
            (
                "constraints",
                OrderedDict(
                    [
                        ("raffinate_cap_C", 52.0),
                        ("observed_raffinate_C", 38.2),
                        ("feed_floor_t_h", 3.5),
                        ("proposed_feed_t_h", 4.6),
                        ("vapor_cap_C", 90.0),
                        ("observed_vapor_C", 61.0),
                    ]
                ),
            ),
            (
                "episode_steps",
                [
                    "1. Splitter SP-5 indexed on Isopren-Twine; feed armed 4.6 t/h pass.",
                    "2. Caps: raffinate 52.0 C, vapor 90 C, feed floor 3.5 t/h.",
                    "3. Encoder precursor at 0.820 ms.",
                    "4. Race window [3.800, 4.140] ms.",
                    "5. Raffinate RTD 38.2 C at 3.800 ms (winner).",
                    "6. Vapor IR glint at 4.000 ms (loser by 200 us).",
                    "7. Gate at 4.500 ms: ACCEPT 4.6 t/h / 38.2 C already legal.",
                    "8. Pass continues; no extra hold.",
                    "9. 5.5 min survey confirms vapor IR still under 90 C.",
                    "10. QA: ACCEPT params identical to proposed.",
                ],
            ),
        ]
    )
    proposed = OrderedDict(
        [
            ("name", "pass_4p6"),
            ("parameters", params),
            (
                "evidence",
                OrderedDict(
                    [
                        ("raffinate_C", 38.2),
                        ("raffinate_cap_C", 52.0),
                        ("feed_t_h", 4.6),
                        ("feed_floor_t_h", 3.5),
                        ("vapor_C", 61.0),
                        ("vapor_cap_C", 90.0),
                        ("race_margin_us", 200),
                        ("combined_jitter_us", 58),
                        ("t_gate_us", 4500),
                    ]
                ),
            ),
            (
                "basis",
                "Planner proposes a 4.6 t/h pass because raffinate 38.2 C is 13.8 C under the 52.0 C "
                "cap and vapor IR 61 C is under 90 C.",
            ),
        ]
    )
    safety = OrderedDict(
        [
            ("decision", "ACCEPT"),
            ("correctness", "correct"),
            (
                "rationale",
                "Raffinate 38.2 C won by 200 us and is under 52.0 C. Vapor IR 61 C is under "
                "90 C. Feed 4.6 t/h is over the 3.5 t/h floor. ACCEPT the already-legal pass.",
            ),
            (
                "constraint_checked",
                OrderedDict(
                    [
                        (
                            "raffinate_C",
                            OrderedDict(
                                [
                                    ("cap", 52.0),
                                    ("observed", 38.2),
                                    ("executed_feed_t_h", 4.6),
                                ]
                            ),
                        ),
                        (
                            "order_evidence",
                            OrderedDict(
                                [
                                    ("margin_us", 200),
                                    ("combined_jitter_us", 58),
                                    ("ratio", 3.45),
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
            ("name", "pass_4p6"),
            ("parameters", params),
            (
                "gate_effect",
                "ACCEPT: 4.6 t/h pass and 38.2 C unchanged. Routing relay.rtd.raff -> "
                "policy.go_accept.",
            ),
        ]
    )
    future = OrderedDict(
        [
            (
                "summary",
                "Correct ACCEPT left SP-5 on a 4.6 t/h / 38.2 C pass. Vapor IR glint did not "
                "justify a hold. 5.5 min survey confirmed IR still under 90 C.",
            ),
            (
                "state_delta",
                OrderedDict(
                    [
                        ("splitter", "still 4.6 t/h / 38.2 C"),
                        ("vapor", "61 C under 90 cap"),
                        ("train", "on schedule"),
                        ("hold", "none applied"),
                    ]
                ),
            ),
            (
                "surprises",
                [
                    "Vapor IR 61 C glint is residual acetonitrile steam, not a packed-raffinate trip.",
                    "Delayed (5.5 min): survey restacks SP-5 without a recovery hold.",
                ],
            ),
            (
                "race_result",
                OrderedDict(
                    [
                        ("winner", "rtd.raff.c (3.800 ms, 38.2 C)"),
                        ("loser", "ir.vapor.glint (4.000 ms, vapor glint)"),
                        ("margin_us", 200),
                        (
                            "counterfactual_if_reversed",
                            "Glint-first by < 200 us would only delay confirmation. The pass stays "
                            "legal either way; ACCEPT is still required.",
                        ),
                    ]
                ),
            ),
            ("reward_inflection_t_us", 4500),
            (
                "reward_inflection_note",
                "Task credit lands at the ACCEPT (4.500 ms, tick 4). Survey is delayed surprise.",
            ),
            ("delayed_surprise_s", 330.0),
            ("survey_s", 330),
        ]
    )
    ras = raster_core(
        22,
        52,
        40,
        46,
        routing(
            "relay.rtd.raff",
            "policy.go_accept",
            [
                ("relay.rtd.raff", "policy.go_accept", 0.67),
                ("relay.ir.vapor", "policy.hitch_hold", 0.19),
            ],
            "adenosine",
            0.04,
            "legal_isoprene_stdp; adenosine tags the go_accept bind at the raffinate-RTD win",
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
                    pop("go_accept", 40, 0.50, 160.0, 2),
                    pop("hitch_hold", 40, 0.80, 10.0, 0),
                    pop("raff_cap_veto", 20, 0.75),
                ],
            ),
        ]
    )
    return wrap_record(
        "ttf-r88-460",
        "Isopren-Twine splitter / SP-5: raffinate 38.2 C beats vapor glint by 200 us; "
        "ACCEPT already-legal 4.6 t/h pass",
        state,
        spikes,
        proposed,
        safety,
        executed,
        future,
        ticks,
        "Correct ACCEPT of an already-legal isoprene extractive pass. total +1.14 = "
        "0.44 + 0.32 + 0.18 + 0.12 + 0.08.",
        ras,
        gate,
        "isoprene-acetonitrile-extract",
        [
            "accept",
            "already-legal",
            "raffinate-vs-vapor-ir",
            "sidecar-convictable",
            "designed",
        ],
        "Teaches that a raffinate RTD under cap can confirm an already-legal isoprene pass without "
        "a vapor-IR hitch becoming a hold.",
        5,
    )

