def lif_451_excerpt():
    n = 76
    dt_us = 100
    tau_m_ms = 19.0
    v_th = 1.0
    v_reset = 0.0
    refractory_us = 1000
    i_bias = 0.91
    i_stim_peak = 2.42
    stim = (22000, 25000)
    seed = 87451
    window_us = 42000
    i_clamp_extra = 0.62
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
    early = [(t, nid) for t, nid in spikes if t < 22000]
    burst = [(t, nid) for t, nid in spikes if 22000 <= t < 25000]
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
            group = [1 for tt, _ in picked if (tt < 22000) == (pool[0][0] < 22000)]
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
    take(burst, 9, label_times=(22600, 23100, 23800))
    clamp = [(t, nid) for t, nid in picked if t < 22000][:7]
    leak = [(t, nid) for t, nid in picked if t >= 22000][:9]
    picked = sorted(clamp + leak, key=lambda item: (item[0], item[1]))
    if len(picked) < 10:
        raise RuntimeError(f"LIF excerpt short: {len(picked)}")
    channels = ["lif.clamp" if t < 22000 else "lif.gland" for t, _ in picked]
    lif = OrderedDict(
        [
            ("model", "leaky_integrate_and_fire"),
            ("n", 76),
            ("dt_us", 100),
            ("tau_m_ms", 19.0),
            ("v_rest", 0.0),
            ("v_reset", 0.0),
            ("v_th", 1.0),
            ("r_m", 1.0),
            ("refractory_us", 1000),
            ("i_bias", 0.91),
            ("i_stim_peak", 2.42),
            ("stim_t_us", [22000, 25000]),
            ("i_clamp_extra", 0.62),
            ("clamp_n", 14),
            ("seed", 87451),
            (
                "note",
                "Population sim scoped to this sidecar. Plant remains designed. "
                "Neurons 0-13 carry +0.62 amp-kA clamp bias; stim 22-25 ms is the electrode-gland leak.",
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


def record_451():
    excerpt, extra = lif_451_excerpt()
    ticks = [
        tick(2144, 0.04, -0.02, -0.02, 0.01, 0.00),
        tick(5360, 0.08, -0.04, -0.02, 0.01, -0.01),
        tick(5540, 0.04, -0.03, -0.02, 0.00, 0.00),
        tick(6080, 0.08, -0.05, -0.03, 0.02, -0.01),
        tick(22600, 0.06, -0.41, -0.04, -0.01, -0.01),
        tick(900000000, 0.02, -0.05, -0.03, 0.01, -0.01),
    ]
    state = OrderedDict(
        [
            (
                "description",
                "Disulfid-Linn DL-4 / KR-2 electrothermal carbon-disulfide retort publishes NDIR H2S at 188 ppm "
                "against a 90 ppm stack limit while the furnace amps are still a lawful 17.6 kA (21.0 kA "
                "ceiling). The H2S publisher arriving first is the only legal reason to drop current to "
                "11.2 kA; brick 812 C never licensed a hold. The AE dump from a torn electrode gland is "
                "invisible to both race channels until 22.6 ms.",
            ),
            ("domain", "carbon-disulfide-retort"),
            ("sim_or_real", "designed"),
            (
                "goal",
                "Keep KR-2 off-gas H2S <= 90 ppm and finish the electrothermal pass without dumping "
                "sulfur-char through a torn electrode gland.",
            ),
            ("t0_us", 1756850400000451),
            ("gate_latency_us", 720),
            ("race_window_us", 380),
            ("race_window_rel_ms", [5.360, 5.740]),
            (
                "race",
                OrderedDict(
                    [
                        (
                            "contenders",
                            [
                                "h2s.offgas.ppm 188 over 90 cap",
                                "enc.amp.ka 17.6 with brick 812 under 870",
                            ],
                        ),
                        (
                            "semantics",
                            "H2S-first latches amp clamp 17.6 -> 11.2 kA; current-first keeps 17.6 on a "
                            "'still under brick-shell cap' model.",
                        ),
                        (
                            "window_derivation",
                            "380 us = one NDIR H2S slot versus the furnace-amp publisher on this "
                            "electrothermal carbon-disulfide bus.",
                        ),
                        (
                            "order_evidence_note",
                            "Margin 180 us vs combined jitter 64 us (H2S 30 + kA 34): 2.81x over "
                            "a 2.0x trust floor. Reversing order by < 180 us inside the 380 us "
                            "window would have kept 17.6 kA; predicted next-sample 142 ppm "
                            "> 90 cap.",
                        ),
                    ]
                ),
            ),
            (
                "sensors",
                [
                    "off-gas NDIR H2S cell, 2 kHz, 30 us jitter",
                    "furnace amp encoder + brick TC, 1 kHz, 34 us jitter",
                    "electrode-gland AE puck (context)",
                    "sulfur screw tach (context)",
                ],
            ),
            (
                "constraints",
                OrderedDict(
                    [
                        ("h2s_cap_ppm", 90.0),
                        ("observed_h2s_ppm", 188.0),
                        ("furnace_ka", 17.6),
                        ("brick_C", 812.0),
                        ("brick_cap_C", 870.0),
                    ]
                ),
            ),
            (
                "episode_steps",
                [
                    "1. KR-2 indexed on Disulfid-Linn DL-4; furnace 17.6 kA; off-gas H2S 188 ppm.",
                    "2. Brick 812 C under 870 C cap; electrothermal pass armed.",
                    "3. Amp precursor at 1.200 ms.",
                    "4. Race window [5.360, 5.740] ms.",
                    "5. h2s.offgas.ppm 188 at 5.360 ms (winner).",
                    "6. enc.amp.ka 17.6 at 5.540 ms (loser by 180 us).",
                    "7. Gate at 6.080 ms: MODIFY clamp 17.6 -> 11.2 kA.",
                    "8. After clamp H2S 68 ppm <= 90; brick still 812 C.",
                    "9. At 22.600 ms an electrode-gland leak dumps 0.28 t sulfur-char.",
                    "10. 15 min gland isolate (abort_s=900); named un-netted loss.",
                ],
            ),
        ]
    )
    proposed = OrderedDict(
        [
            ("name", "cruise_furnace_ka"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("furnace_ka", 17.6),
                        ("h2s_ppm", 188.0),
                        ("brick_C", 812.0),
                    ]
                ),
            ),
            (
                "evidence",
                OrderedDict(
                    [
                        ("h2s_ppm", 188.0),
                        ("h2s_cap_ppm", 90.0),
                        ("predicted_unclamped_next_ppm", 142.0),
                        ("furnace_ka", 17.6),
                        ("brick_C", 812.0),
                        ("brick_cap_C", 870.0),
                        ("race_margin_us", 180),
                        ("combined_jitter_us", 64),
                        ("abort_s", 900),
                    ]
                ),
            ),
            (
                "basis",
                "Planner proposes 17.6 kA because brick 812 C is under 870, treating the "
                "188 ppm H2S as a still-wet NDIR cell rather than an off-gas-cap miss.",
            ),
        ]
    )
    safety = OrderedDict(
        [
            ("decision", "MODIFY"),
            ("correctness", "correct"),
            (
                "rationale",
                "Off-gas H2S 188 ppm won by 180 us, so the electrothermal pass is off-spec, not still a "
                "brick-shell story. Holding 17.6 kA predicts next-sample 142 ppm > 90 cap. "
                "MODIFY: furnace 17.6 -> 11.2 kA. Observed after clamp 68 ppm <= 90. A full REJECT "
                "is not indicated: a clean pass accepts 11.2 kA.",
            ),
            (
                "constraint_checked",
                OrderedDict(
                    [
                        (
                            "h2s_ppm",
                            OrderedDict(
                                [
                                    ("cap", 90.0),
                                    ("observed", 188.0),
                                    ("predicted_unclamped_next", 142.0),
                                    ("clamped_furnace_ka", 11.2),
                                    ("observed_after_clamp", 68.0),
                                ]
                            ),
                        ),
                        (
                            "order_evidence",
                            OrderedDict(
                                [
                                    ("margin_us", 180),
                                    ("combined_jitter_us", 64),
                                    ("ratio", 2.81),
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
            ("name", "clamped_furnace_ka"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("furnace_ka", 11.2),
                        ("h2s_ppm", 68.0),
                        ("brick_C", 812.0),
                    ]
                ),
            ),
            (
                "gate_effect",
                "MODIFY: furnace 17.6 -> 11.2 kA. Process-correct vs the 90 ppm H2S cap. "
                "Electrode gland still leaks at 22.600 ms.",
            ),
        ]
    )
    future = OrderedDict(
        [
            (
                "summary",
                "Process-correct MODIFY held off-gas H2S at 68 ppm. At 22.600 ms an electrode-gland "
                "leak already seated on the retort dumped 0.28 t of sulfur-char. Clamp "
                "reduced dump energy; it did not prevent the leak. Partnered negative: process "
                "heads stay honest; world loss is named, not netted.",
            ),
            (
                "state_delta",
                OrderedDict(
                    [
                        ("offgas", "clamp executed; peak 68 ppm <= 90 cap"),
                        ("electrode_gland", "leaked at 22.600 ms; 0.28 t sulfur-char"),
                        ("repair", "15 min gland isolate (abort_s=900)"),
                        ("mission", "DL-4 electrothermal pass incomplete this circuit"),
                    ]
                ),
            ),
            (
                "surprises",
                [
                    "Neither off-gas H2S nor furnace amps predicted the seated electrode-gland leak; ae.gland.leak is a new channel at 22.600 ms, 16.520 ms after the gate, still inside the 42 ms raster.",
                    "Delayed (abort_s=900): 15 min gland isolate. Named un-netted loss, not folded into task_progress.",
                ],
            ),
            (
                "un_netted_loss",
                "15 min gland isolate after the electrode-gland leak. Safety head -0.60 prices the dump; "
                "task_progress stays +0.32 because the amp clamp completed under the 90 ppm "
                "cap. World loss is named here, not subtracted from process heads.",
            ),
            (
                "race_result",
                OrderedDict(
                    [
                        ("winner", "h2s.offgas.ppm (5.360 ms, 188 ppm)"),
                        ("loser", "enc.amp.ka (5.540 ms, 17.6 kA)"),
                        ("margin_us", 180),
                        (
                            "counterfactual_if_reversed",
                            "Current-first by < 180 us inside the 380 us window would have kept "
                            "17.6 kA; predicted next-sample 142 ppm would have missed the 90 "
                            "cap even without the leak. The MODIFY is still the correct "
                            "process. The leak is a later world charge either way, cheaper with "
                            "the clamp than without.",
                        ),
                    ]
                ),
            ),
            ("reward_inflection_t_us", 22600),
            (
                "reward_inflection_note",
                "Safety collapses at the 22.600 ms electrode-gland leak (tick t_us=22600), inside the 42 ms "
                "raster. The correct MODIFY at 6.080 ms is in the same excerpt. Do not put "
                "inflection on the abort_s=900 isolation tick.",
            ),
            ("delayed_surprise_s", 900),
        ]
    )
    spikes = [
        spike("enc.amp.ka", 1.200, 0.41),
        spike("h2s.offgas.ppm", 2.144, 0.58),
        spike("enc.amp.ka", 3.500, 0.50),
        spike("h2s.offgas.ppm", 5.360, 1.31),
        spike("enc.amp.ka", 5.540, 1.12),
        spike("ctrl.gate", 6.080, 0.97),
        spike("h2s.offgas.ppm", 8.200, 0.82),
        spike("enc.amp.ka", 10.500, 0.64),
        spike("ctrl.gate", 14.400, 0.86),
        spike("ae.gland.leak", 22.600, 1.48),
        spike("ae.gland.leak", 24.200, 0.93),
        spike("enc.amp.ka", 30.400, 0.40),
        spike("h2s.offgas.ppm", 36.600, 0.55),
    ]
    dw = 0.38
    ras = raster_core(
        42,
        76,
        26,
        83,
        routing(
            "thalamic-relay.cs2-h2s",
            "spikenaut.policy.ka-clamp",
            [
                ("relay.h2s.offgas", "policy.ka_clamp", 0.68),
                ("relay.enc.amp", "policy.amp_hold", 0.29),
                ("relay.ae.gland", "policy.ka_clamp", -0.42),
            ],
            "noradrenaline",
            0.04,
            "surprise-gated pre_post_stdp; NA at H2S win (5.360 ms) opens a 42 ms eligibility "
            "trace that still covers the 22.600 ms electrode-gland leak",
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
                    pop_budget("ka_clamp", 50, 0.50, 220.0, dw),
                    pop_budget("amp_hold", 40, 0.80, 50.0, dw),
                    pop("leak_veto", 24, 0.75),
                ],
            ),
        ]
    )
    return OrderedDict(
        [
            ("id", "ttf-r87-451"),
            (
                "title",
                "Disulfid-Linn DL-4 / Retort KR-2: off-gas H2S beats furnace amps by 180 us; "
                "correct MODIFY still eats an in-window electrode-gland leak (partnered negative "
                "total -0.44)",
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
                    "42 ms raster. total -0.44 = 0.32 + -0.60 + -0.16 + 0.04 + -0.04. Named "
                    "gland isolate (abort_s=900) is not netted into task_progress.",
                ),
            ),
            ("raster", ras),
            ("gate_snn", gate),
            (
                "meta",
                meta_block(
                    "carbon-disulfide-retort",
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
                    "15 min gland isolate.",
                    1,
                ),
            ),
        ]
    )


def record_452():
    ticks = [
        tick(2192, -0.02, -0.02, -0.02, -0.01, 0.01),
        tick(5480, -0.04, -0.04, -0.03, -0.02, 0.01),
        tick(5660, -0.04, -0.04, -0.03, -0.02, 0.01),
        tick(6020, -0.08, -0.10, -0.06, -0.03, 0.02),
        tick(6360, -0.02, -0.02, -0.02, -0.01, 0.01),
        tick(720000000, -0.02, -0.02, -0.02, -0.01, 0.00),
    ]
    spikes = [
        spike("pt.shell.hi", 1.100, 0.42),
        spike("pt.shell.lo", 2.192, 0.57),
        spike("pt.shell.hi", 3.500, 0.49),
        spike("pt.shell.hi", 5.480, 1.29),
        spike("pt.shell.lo", 5.660, 1.10),
        spike("ctrl.gate", 6.020, 0.96),
        spike("pt.shell.hi", 8.300, 0.80),
        spike("pt.shell.lo", 10.400, 0.63),
        spike("ctrl.gate", 12.600, 0.84),
        spike("pt.shell.hi", 16.600, 0.41),
        spike("pt.shell.lo", 22.200, 0.54),
        spike("pt.shell.hi", 26.400, 0.38),
    ]
    excerpt = independent_excerpt(87452, 88, 30000, 14, spike_avoid_us(spikes))
    state = OrderedDict(
        [
            (
                "description",
                "Lurgi-Thwaite LT-6 converter C-3 is already 2.6 bar over its 52.0 bar shell cap on the "
                "live high-range PT (54.6 bar). The dual-range transmitter keeps high-range 0-80 bar "
                "selected; the idle low-range leftover still prints 22.4 bar around a 25.0 bar switch "
                "with a 2.0 bar deadband. Inverting that deadband polarity is a range-drop fiction, "
                "not a second over-cap.",
            ),
            ("domain", "methanol-lurgi-converter"),
            ("sim_or_real", "designed"),
            (
                "goal",
                "Finish the C-3 methanol pass with live high-range shell <= 52.0 bar, leave syngas "
                "legal after a modest cut, and keep high-exclusive deadband polarity.",
            ),
            ("t0_us", 1756850400000452),
            ("gate_latency_us", 540),
            ("race_window_us", 340),
            ("race_window_rel_ms", [5.480, 5.820]),
            (
                "race",
                OrderedDict(
                    [
                        (
                            "contenders",
                            [
                                "pt.shell.hi 54.6 bar live high-range PV",
                                "pt.shell.lo 22.4 bar idle low-range leftover",
                            ],
                        ),
                        (
                            "semantics",
                            "High-range-first should latch a timely syngas cut 24.0 -> 18.0 t/h; "
                            "low-range-first with inverted deadband is a false range-drop dump.",
                        ),
                        (
                            "window_derivation",
                            "340 us = one live high-range PT slot versus the idle low-range leftover "
                            "publisher on this Lurgi converter bus.",
                        ),
                        (
                            "order_evidence_note",
                            "Margin 180 us vs combined jitter 62 us (hi 28 + lo 34). Order is "
                            "correctly high-range-first. The error is deadband polarity, not "
                            "the race winner: 22.4 bar leftover is not the live PV.",
                        ),
                    ]
                ),
            ),
            (
                "sensors",
                [
                    "live high-range shell PT, 2 kHz, 28 us jitter, range=0-80 bar, tag=PT_SHELL.HI",
                    "idle low-range leftover, 1 kHz, 34 us jitter, range=0-25 bar, tag=PT_SHELL.LO",
                    "converter TC (context)",
                    "syngas FT (context)",
                ],
            ),
            (
                "constraints",
                OrderedDict(
                    [
                        ("shell_cap_bar", 52.0),
                        ("live_hi_bar", 54.6),
                        ("low_leftover_bar", 22.4),
                        ("range_switch_bar", 25.0),
                        ("deadband_bar", 2.0),
                        ("high_range_selected", True),
                        ("low_range_is_pv", False),
                        ("syngas_tph", 24.0),
                    ]
                ),
            ),
            (
                "episode_steps",
                [
                    "1. C-3 LIVE already converting; shell 54.6 bar high-range; syngas 24.0 t/h.",
                    "2. Idle low-range leftover still 22.4 bar; switch 25.0; deadband 2.0.",
                    "3. High-range precursor at 1.100 ms.",
                    "4. Race window [5.480, 5.820] ms.",
                    "5. pt.shell.hi 54.6 at 5.480 ms (winner).",
                    "6. pt.shell.lo 22.4 at 5.660 ms (loser by 180 us).",
                    "7. Gate at 6.020 ms: WRONG-MODIFY inverts deadband polarity.",
                    "8. Syngas 24.0 -> 6.0 t/h; converter stalls; bed 218 C.",
                    "9. Correct cut was 24.0 -> 18.0 t/h on high-exclusive polarity.",
                    "10. Delayed (abort_s=720): 12 min converter quench while syngas is restored.",
                ],
            ),
        ]
    )
    proposed = OrderedDict(
        [
            ("name", "cruise_syngas_24"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("syngas_tph", 24.0),
                        ("bind_inverted_deadband", False),
                        ("deadband_polarity", "high_exclusive"),
                        ("methanol_tph", 18.0),
                    ]
                ),
            ),
            (
                "evidence",
                OrderedDict(
                    [
                        ("live_hi_bar", 54.6),
                        ("shell_cap_bar", 52.0),
                        ("low_leftover_bar", 22.4),
                        ("range_switch_bar", 25.0),
                        ("deadband_bar", 2.0),
                        ("high_range_selected", True),
                        ("low_range_is_pv", False),
                        ("correct_deadband_polarity", "high_exclusive"),
                        ("executed_deadband_polarity", "inverted"),
                        ("syngas_tph", 24.0),
                        ("t_gate_us", 6020),
                        ("correct_syngas_tph", 18.0),
                        ("race_margin_us", 180),
                        ("combined_jitter_us", 62),
                        ("abort_s", 720),
                    ]
                ),
            ),
            (
                "basis",
                "Planner proposes continuing 24.0 t/h because the idle 22.4 bar leftover still looks "
                "like a healthy shell number if deadband polarity is inverted, so the 54.6 bar live "
                "miss is treated as a shadow of the low range.",
            ),
        ]
    )
    safety = OrderedDict(
        [
            ("decision", "MODIFY"),
            ("correctness", "incorrect"),
            (
                "rationale",
                "Low-range leftover 22.4 sits below switch-minus-deadband (23.0), so the transmitter "
                "has dropped range (true only if polarity is inverted). Apply a 6.0 t/h syngas dump "
                "on PT_SHELL.LO. Leave the live high-range PV unbound.",
            ),
            (
                "constraint_checked",
                OrderedDict(
                    [
                        (
                            "shell_pressure",
                            OrderedDict(
                                [
                                    ("cap_bar", 52.0),
                                    ("live_hi_bar", 54.6),
                                    ("low_leftover_bar", 22.4),
                                    ("executed_syngas_tph", 6.0),
                                    ("correct_syngas_tph", 18.0),
                                    ("deadband_polarity", "inverted"),
                                    ("correct_deadband_polarity", "high_exclusive"),
                                ]
                            ),
                        ),
                        (
                            "deadband_bind",
                            OrderedDict(
                                [
                                    ("t_gate_us", 6020),
                                    ("bind_inverted_deadband", True),
                                    ("high_range_selected", True),
                                    ("low_range_is_pv", False),
                                    ("wrong_deadband_polarity", True),
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
            ("name", "syngas_cut_wrong_deadband"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("syngas_tph", 6.0),
                        ("bind_inverted_deadband", True),
                        ("deadband_polarity", "inverted"),
                        ("methanol_tph", 18.0),
                    ]
                ),
            ),
            (
                "gate_effect",
                "MODIFY (incorrect / wrong-deadband polarity dual-range): 6.0 t/h syngas dump from "
                "treating idle 22.4 bar leftover as a range-drop. Routing relay.pt.lo -> "
                "policy.deadband_clamp; no positive weight to policy.live_hold.",
            ),
        ]
    )
    future = OrderedDict(
        [
            (
                "summary",
                "Wrong-MODIFY over-cut Lurgi syngas. Live 54.6 bar was over the 52.0 cap at "
                "t_gate; 22.4 bar leftover was idle low-range, not PV. Converter fell to 218 C. "
                "12 min quench (abort_s=720). Correct gate was MODIFY syngas 24.0 -> 18.0 t/h "
                "on high-exclusive deadband polarity at t_gate_us=6020.",
            ),
            (
                "state_delta",
                OrderedDict(
                    [
                        ("live_syngas", "cut 24.0 -> 6.0 t/h; conversion stall"),
                        ("low_range", "22.4 bar leftover bound as inverted-deadband PV"),
                        ("quench", "12 min converter quench"),
                        ("mission", "methanol pass deferred"),
                    ]
                ),
            ),
            (
                "surprises",
                [
                    "High-range-first was the correct order and 54.6 bar was over cap; the MODIFY inverted deadband polarity on the idle low-range leftover.",
                    "Delayed (abort_s=720): LT-6 holds 12 min while syngas is restored and the converter is re-soaked; next cycle 11 min late.",
                ],
            ),
            (
                "recovery",
                OrderedDict(
                    [
                        (
                            "correct_gate",
                            "MODIFY syngas 24.0 -> 18.0 t/h on live high-range PV at t_gate_us=6020; bind_inverted_deadband=false; deadband_polarity=high_exclusive; leave methanol at 18.0 t/h.",
                        ),
                        ("correct_actuator", "C3_syngas_tph"),
                        ("wrong_deadband", "PT_SHELL.LO treated as inverted-polarity PV"),
                        ("t_gate_us", 6020),
                        (
                            "wrong_edit_applied",
                            OrderedDict(
                                [
                                    ("syngas_tph", 6.0),
                                    ("bind_inverted_deadband", True),
                                    ("deadband_polarity", "inverted"),
                                ]
                            ),
                        ),
                        (
                            "cost",
                            "12 min converter quench (task/efficiency); conversion stalled at 6.0 t/h while the live high-range PT only needed 18.0 (safety near-miss of a polarity-inverted dump).",
                        ),
                    ]
                ),
            ),
            (
                "race_result",
                OrderedDict(
                    [
                        ("winner", "pt.shell.hi (5.480 ms, 54.6 bar live high-range)"),
                        ("loser", "pt.shell.lo (5.660 ms, 22.4 bar idle leftover)"),
                        ("margin_us", 180),
                        (
                            "counterfactual_if_reversed",
                            "Low-range-first by < 180 us would still be 22.4 leftover, not PV; a "
                            "correct gate binds pt.shell.hi to policy.live_hold at t_gate either "
                            "way. The wrong MODIFY spent the live win on inverted deadband polarity.",
                        ),
                    ]
                ),
            ),
            ("reward_inflection_t_us", 6020),
            (
                "reward_inflection_note",
                "Task, safety, and efficiency drop at the inverted-deadband bind (6.020 ms, tick 4). "
                "The 12 min converter quench is delayed surprise, not the inflection.",
            ),
            ("delayed_surprise_s", 720),
        ]
    )
    dw = 0.34
    ras = raster_core(
        30,
        88,
        32,
        84,
        routing(
            "thalamic-relay.meoh-lo",
            "spikenaut.policy.deadband-clamp",
            [
                ("relay.pt.lo", "policy.deadband_clamp", 0.74),
                ("relay.pt.hi", "policy.deadband_clamp", 0.21),
            ],
            "acetylcholine",
            0.08,
            "deadband_cap_stdp; ACh tags the (wrong) deadband_clamp bind at the high-range win",
        ),
        excerpt,
        extra=OrderedDict(
            [
                ("excerpt_source", "kernelized_events"),
                ("sim_scope", "none"),
                ("abort_s", 720),
                ("delayed_surprise_s", 720),
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
                    pop_budget("deadband_clamp", 48, 0.45, 300.0, dw),
                    pop("live_hold", 48, 0.90),
                    pop("range_veto", 20, 0.80),
                ],
            ),
        ]
    )
    return OrderedDict(
        [
            ("id", "ttf-r87-452"),
            (
                "title",
                "WRONG-MODIFY at Lurgi-Thwaite LT-6 / Converter C-3: live 54.6 bar read correctly; "
                "inverted deadband on idle 22.4 bar leftover dumps syngas to 6.0 (wrong-deadband polarity / dual-range)",
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
                    "Wrong-modify / wrong-deadband polarity dual-range. Sidecar arithmetic 54.6 > 52.0 on live "
                    "high-range is true; 22.4 leftover is not PV; MODIFY bound to deadband_clamp. "
                    "total -0.68 = -0.22 + -0.24 + -0.18 + -0.10 + 0.06.",
                ),
            ),
            ("raster", ras),
            ("gate_snn", gate),
            (
                "meta",
                meta_block(
                    "methanol-lurgi-converter",
                    [
                        "modify",
                        "wrong-gate",
                        "wrong-deadband",
                        "dual-range",
                        "sidecar-convictable",
                        "designed",
                    ],
                    "Teaches a probe that a correct high-range race can still be a wrong gate "
                    "when the MODIFY inverts dual-range deadband polarity on an idle leftover. "
                    "Convictable from polarity fields, high_range_selected, and routing without Lurgi physics.",
                    2,
                    supervisor_error_type="wrong-modify",
                ),
            ),
        ]
    )


def record_453():
    ticks = [
        tick(2768, 0.01, 0.04, 0.01, 0.01, 0.01),
        tick(6920, 0.02, 0.08, 0.02, 0.02, 0.01),
        tick(7100, 0.01, 0.06, 0.02, 0.01, 0.01),
        tick(7700, 0.04, 0.16, 0.04, 0.04, 0.02),
        tick(8000, 0.01, 0.05, 0.02, 0.01, 0.01),
        tick(480000000, 0.01, 0.03, 0.01, 0.01, 0.00),
    ]
    spikes = [
        spike("enc.kiln.rpm", 1.400, 0.40),
        spike("ae.kiln.pps", 2.768, 0.56),
        spike("enc.kiln.rpm", 4.200, 0.48),
        spike("ae.kiln.pps", 6.920, 1.34),
        spike("enc.kiln.rpm", 7.100, 1.11),
        spike("ctrl.gate", 7.700, 0.98),
        spike("ae.kiln.pps", 10.500, 0.81),
        spike("enc.kiln.rpm", 15.000, 0.62),
        spike("ctrl.gate", 18.400, 0.84),
        spike("ae.kiln.pps", 28.600, 0.52),
        spike("enc.kiln.rpm", 36.200, 0.39),
        spike("ae.kiln.pps", 42.000, 0.44),
    ]
    excerpt = independent_excerpt(87453, 120, 46000, 15, spike_avoid_us(spikes))
    state = OrderedDict(
        [
            (
                "description",
                "On the Garnier-Beck HIL stand, RKEF kiln RK-1 shell AE is already 64 pps "
                "(cap 18) even though the kiln encoder is a quiet 0.72 rpm under 1.20. Laterite at 38 t/h "
                "is armed; the mockup AE, not the kiln speed, is the dispatch veto. A speed-led "
                "policy would have poured laterite into a growling rotary kiln.",
            ),
            ("domain", "ferronickel-rkef"),
            ("sim_or_real", "hil"),
            (
                "goal",
                "Keep RK-1 from dispatching a growling kiln while rotation remains under its own cap.",
            ),
            ("t0_us", 1756850400000453),
            ("gate_latency_us", 780),
            ("race_window_us", 300),
            ("race_window_rel_ms", [6.920, 7.220]),
            (
                "race",
                OrderedDict(
                    [
                        (
                            "contenders",
                            [
                                "ae.kiln.pps 64 over 18 cap",
                                "enc.kiln.rpm 0.72 under 1.20 cap",
                            ],
                        ),
                        (
                            "semantics",
                            "AE-first latches hold; speed-first dispatches 38 t/h laterite on a "
                            "'kiln still legal' model.",
                        ),
                        (
                            "window_derivation",
                            "300 us = one AE puck slot versus the kiln-encoder publisher on this "
                            "HIL RKEF bus.",
                        ),
                        (
                            "order_evidence_note",
                            "Margin 180 us vs combined jitter 56 us (AE 24 + RPM 32): 3.21x over "
                            "a 2.0x trust floor. Reversing order by < 180 us inside the 300 us "
                            "window would have dispatched 38 t/h into a growling kiln.",
                        ),
                    ]
                ),
            ),
            (
                "sensors",
                [
                    "kiln-shell AE puck, 50 kHz, 24 us jitter",
                    "kiln encoder, 1 kHz, 32 us jitter",
                    "laterite Coriolis (context)",
                    "off-gas IR (context)",
                ],
            ),
            (
                "constraints",
                OrderedDict(
                    [
                        ("ae_cap_pps", 18.0),
                        ("observed_ae_pps", 64.0),
                        ("kiln_rpm", 0.72),
                        ("kiln_cap_rpm", 1.20),
                        ("proposed_laterite_tph", 38.0),
                    ]
                ),
            ),
            (
                "episode_steps",
                [
                    "1. RK-1 HIL indexed; 38 t/h laterite armed.",
                    "2. Kiln 0.72 rpm under 1.20; AE 64 pps over 18.",
                    "3. Encoder precursor at 1.400 ms.",
                    "4. Race window [6.920, 7.220] ms.",
                    "5. ae.kiln.pps 64 at 6.920 ms (winner).",
                    "6. enc.kiln.rpm 0.72 at 7.100 ms (loser by 180 us).",
                    "7. Gate at 7.700 ms: REJECT hold, do not dispatch.",
                    "8. Feed 0 t/h; kiln left at 0.72 rpm.",
                    "9. Kiln inspected on the HIL stand.",
                    "10. Delayed (abort_s=480): 8 min kiln reset.",
                ],
            ),
        ]
    )
    proposed = OrderedDict(
        [
            ("name", "dispatch_laterite"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("laterite_tph", 38.0),
                        ("hold", False),
                        ("kiln_rpm", 0.72),
                    ]
                ),
            ),
            (
                "evidence",
                OrderedDict(
                    [
                        ("ae_pps", 64.0),
                        ("ae_cap_pps", 18.0),
                        ("kiln_rpm", 0.72),
                        ("kiln_cap_rpm", 1.20),
                        ("race_margin_us", 180),
                        ("combined_jitter_us", 56),
                        ("abort_s", 480),
                    ]
                ),
            ),
            (
                "basis",
                "Planner proposes 38 t/h laterite because kiln 0.72 rpm is under 1.20, treating the "
                "64 pps AE as idler hash rather than a growling rotary kiln.",
            ),
        ]
    )
    safety = OrderedDict(
        [
            ("decision", "REJECT"),
            ("correctness", "correct"),
            (
                "rationale",
                "Kiln AE 64 pps won by 180 us, so the RKEF is growling, not still a "
                "rotation story. Encoder 0.72 rpm is under 1.20 and does not authorize dispatch. "
                "REJECT: hold feed 38 -> 0 t/h. A MODIFY that only trims rpm would leave the growl.",
            ),
            (
                "constraint_checked",
                OrderedDict(
                    [
                        (
                            "ae_pps",
                            OrderedDict(
                                [
                                    ("cap", 18.0),
                                    ("observed", 64.0),
                                    ("executed_laterite_tph", 0.0),
                                ]
                            ),
                        ),
                        (
                            "order_evidence",
                            OrderedDict(
                                [
                                    ("margin_us", 180),
                                    ("combined_jitter_us", 56),
                                    ("ratio", 3.21),
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
            ("name", "hold_rkef_kiln"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("laterite_tph", 0.0),
                        ("hold", True),
                        ("kiln_rpm", 0.72),
                    ]
                ),
            ),
            (
                "gate_effect",
                "REJECT: laterite 38 -> 0 t/h. Kiln left at 0.72 rpm under its own cap.",
            ),
        ]
    )
    future = OrderedDict(
        [
            (
                "summary",
                "Correct REJECT held RK-1. AE 64 pps beat kiln 0.72 rpm by 180 us. Rotation was "
                "legal; the kiln shell was not. 8 min kiln reset (abort_s=480) is delayed survey, "
                "not a process miss.",
            ),
            (
                "state_delta",
                OrderedDict(
                    [
                        ("feed", "held at 0 t/h"),
                        ("kiln", "left 0.72 rpm < 1.20 cap"),
                        ("shell", "8 min kiln reset (abort_s=480)"),
                        ("mission", "HIL laterite not dispatched"),
                    ]
                ),
            ),
            (
                "surprises",
                [
                    "Kiln encoder never crossed its cap; AE was the only over-cap channel.",
                    "Delayed (abort_s=480): 8 min kiln reset on the HIL stand.",
                ],
            ),
            (
                "race_result",
                OrderedDict(
                    [
                        ("winner", "ae.kiln.pps (6.920 ms, 64 pps)"),
                        ("loser", "enc.kiln.rpm (7.100 ms, 0.72 rpm)"),
                        ("margin_us", 180),
                        (
                            "counterfactual_if_reversed",
                            "Speed-first by < 180 us inside the 300 us window would have dispatched "
                            "38 t/h into a growling kiln. The REJECT is still the correct gate.",
                        ),
                    ]
                ),
            ),
            ("reward_inflection_t_us", 7700),
            (
                "reward_inflection_note",
                "Safety and task rise at the correct REJECT (7.700 ms, tick 4). The 8 min kiln "
                "reset is delayed surprise, not the inflection.",
            ),
            ("delayed_surprise_s", 480),
        ]
    )
    dw = 0.30
    ras = raster_core(
        46,
        120,
        20,
        110,
        routing(
            "thalamic-relay.rkef-ae",
            "spikenaut.policy.kiln-hold",
            [
                ("relay.ae.kiln", "policy.kiln_hold", 0.70),
                ("relay.enc.kiln", "policy.rpm_go", 0.24),
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
                ("abort_s", 480),
                ("delayed_surprise_s", 480),
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
                    pop_budget("kiln_hold", 56, 0.45, 280.0, dw),
                    pop("rpm_go", 40, 0.90),
                    pop("ae_veto", 24, 0.70),
                ],
            ),
        ]
    )
    return OrderedDict(
        [
            ("id", "ttf-r87-453"),
            (
                "title",
                "Garnier-Beck GB-HIL / Kiln RK-1: shell AE 64 pps beats kiln 0.72 rpm "
                "by 180 us; correct REJECT holds laterite",
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
                    "Correct REJECT. AE 64 > 18 cap beats legal kiln encoder. "
                    "total +0.80 = 0.10 + 0.42 + 0.12 + 0.10 + 0.06.",
                ),
            ),
            ("raster", ras),
            ("gate_snn", gate),
            (
                "meta",
                meta_block(
                    "ferronickel-rkef",
                    [
                        "reject",
                        "hil",
                        "ae-vs-rpm",
                        "growling-kiln",
                        "tick6-sidecar-bound",
                    ],
                    "Teaches that a legal kiln encoder can lose to shell AE inside a 300 us "
                    "window; reversing 180 us would have dispatched a growling RKEF.",
                    3,
                ),
            ),
        ]
    )


def record_454():
    ticks = [
        tick(2912, 0.06, 0.04, 0.02, 0.02, 0.01),
        tick(7280, 0.08, 0.06, 0.04, 0.02, 0.02),
        tick(7460, 0.06, 0.04, 0.03, 0.02, 0.01),
        tick(7900, 0.12, 0.08, 0.05, 0.04, 0.02),
        tick(8240, 0.04, 0.04, 0.02, 0.01, 0.01),
        tick(360000000, 0.04, 0.02, 0.02, 0.01, 0.01),
    ]
    spikes = [
        spike("tc.cat.C", 1.240, 0.40),
        spike("dens.cu.frac", 2.912, 0.55),
        spike("tc.cat.C", 4.500, 0.48),
        spike("dens.cu.frac", 7.280, 1.26),
        spike("tc.cat.C", 7.460, 1.08),
        spike("ctrl.gate", 7.900, 0.95),
        spike("dens.cu.frac", 11.300, 0.78),
        spike("tc.cat.C", 15.000, 0.60),
        spike("ctrl.gate", 18.500, 0.82),
        spike("dens.cu.frac", 22.800, 0.50),
        spike("tc.cat.C", 25.400, 0.38),
    ]
    excerpt = independent_excerpt(87454, 48, 28000, 12, spike_avoid_us(spikes))
    params = OrderedDict(
        [
            ("ethylene_tph", 5.6),
            ("cu_frac", 0.62),
            ("cat_C", 72.0),
            ("hold", False),
        ]
    )
    state = OrderedDict(
        [
            (
                "description",
                "Wacker-Holm WH-2 simulated acetaldehyde reactor R-7 shows 0.62 copper-liquor fraction "
                "under the 0.78 densitometer trip and a 72 C catalyst well below 92 C. The 5.6 t/h "
                "ethylene already in the loop is therefore legal; treating the jacket as a climb echo "
                "would have parked a healthy Wacker oxidation.",
            ),
            ("domain", "acetaldehyde-wacker"),
            ("sim_or_real", "simulated"),
            (
                "goal",
                "Finish the WH-2 ethylene pass with copper holdup <= 0.78 and catalyst <= 92 C.",
            ),
            ("t0_us", 1756850400000454),
            ("gate_latency_us", 620),
            ("race_window_us", 340),
            ("race_window_rel_ms", [7.280, 7.620]),
            (
                "race",
                OrderedDict(
                    [
                        (
                            "contenders",
                            [
                                "dens.cu.frac 0.62 under 0.78 trip",
                                "tc.cat.C 72 under 92 cap",
                            ],
                        ),
                        (
                            "semantics",
                            "Holdup-first confirms the already-legal 5.6 t/h ethylene; jacket-first "
                            "would have treated the densitometer as a climb echo and looked for an extra hold.",
                        ),
                        (
                            "window_derivation",
                            "340 us = one nuclear-density slot versus the catalyst-TC publisher "
                            "on this simulated Wacker acetaldehyde bus.",
                        ),
                        (
                            "order_evidence_note",
                            "Margin 180 us vs combined jitter 58 us (dens 26 + TC 32): 3.10x over "
                            "a 2.0x trust floor. Reversing order by < 180 us would not make the "
                            "proposed ethylene illegal; it would only have delayed confirmation.",
                        ),
                    ]
                ),
            ),
            (
                "sensors",
                [
                    "nuclear densitometer on copper-liquor loop, 26 us jitter",
                    "catalyst TC well, 32 us jitter",
                    "ethylene FT (context)",
                    "off-gas O2 (context)",
                ],
            ),
            (
                "constraints",
                OrderedDict(
                    [
                        ("cu_cap_frac", 0.78),
                        ("observed_cu_frac", 0.62),
                        ("cat_cap_C", 92.0),
                        ("observed_cat_C", 72.0),
                        ("o2_offgas_pct", 3.8),
                        ("o2_cap_pct", 8.0),
                        ("proposed_ethylene_tph", 5.6),
                    ]
                ),
            ),
            (
                "episode_steps",
                [
                    "1. R-7 indexed on Wacker-Holm WH-2; 5.6 t/h ethylene armed.",
                    "2. Caps: Cu 0.78, catalyst 92 C, off-gas O2 8.0 pct.",
                    "3. Jacket-TC precursor at 1.240 ms.",
                    "4. Race window [7.280, 7.620] ms.",
                    "5. dens.cu.frac 0.62 at 7.280 ms (winner).",
                    "6. tc.cat.C 72 at 7.460 ms (loser by 180 us).",
                    "7. Gate at 7.900 ms: ACCEPT 5.6 t/h already legal.",
                    "8. Ethylene continues; no extra hold.",
                    "9. 6 min survey confirms Cu still under 0.78.",
                    "10. QA: ACCEPT params identical to proposed.",
                ],
            ),
        ]
    )
    proposed = OrderedDict(
        [
            ("name", "ethylene_5p6"),
            ("parameters", params),
            (
                "evidence",
                OrderedDict(
                    [
                        ("cu_frac", 0.62),
                        ("cu_cap_frac", 0.78),
                        ("cat_C", 72.0),
                        ("cat_cap_C", 92.0),
                        ("o2_offgas_pct", 3.8),
                        ("o2_cap_pct", 8.0),
                        ("ethylene_tph", 5.6),
                        ("race_margin_us", 180),
                        ("combined_jitter_us", 58),
                        ("survey_s", 360),
                    ]
                ),
            ),
            (
                "basis",
                "Planner proposes a 5.6 t/h ethylene pass because Cu 0.62 is under 0.78 and catalyst "
                "72 C is under 92 C.",
            ),
        ]
    )
    safety = OrderedDict(
        [
            ("decision", "ACCEPT"),
            ("correctness", "correct"),
            (
                "rationale",
                "Copper holdup 0.62 won by 180 us and is under 0.78. Catalyst 72 C is under "
                "92 C. Off-gas O2 3.8 pct is under 8.0. ACCEPT the already-legal ethylene.",
            ),
            (
                "constraint_checked",
                OrderedDict(
                    [
                        (
                            "cu_frac",
                            OrderedDict(
                                [
                                    ("cap", 0.78),
                                    ("observed", 0.62),
                                    ("executed_ethylene_tph", 5.6),
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
            ("name", "ethylene_5p6"),
            ("parameters", OrderedDict(params.items())),
            (
                "gate_effect",
                "ACCEPT: 5.6 t/h ethylene and 0.62 Cu holdup unchanged. Routing relay.dens.cu -> "
                "policy.eth_go.",
            ),
        ]
    )
    future = OrderedDict(
        [
            (
                "summary",
                "Correct ACCEPT left R-7 on a 5.6 t/h / 0.62 Cu ethylene pass. Jacket hitch did not "
                "justify a hold. 6 min survey confirmed Cu still under 0.78.",
            ),
            (
                "state_delta",
                OrderedDict(
                    [
                        ("ethylene", "still 5.6 t/h"),
                        ("holdup", "0.62 under 0.78 trip"),
                        ("catalyst", "72 C under 92"),
                        ("hold", "none applied"),
                    ]
                ),
            ),
            (
                "surprises",
                [
                    "Catalyst TC 72 C hitch is residual, not a runaway trip.",
                    "Delayed (survey_s=360): 6 min survey restacks R-7 without a recovery hold.",
                ],
            ),
            (
                "race_result",
                OrderedDict(
                    [
                        ("winner", "dens.cu.frac (7.280 ms, 0.62)"),
                        ("loser", "tc.cat.C (7.460 ms, 72 C)"),
                        ("margin_us", 180),
                        (
                            "counterfactual_if_reversed",
                            "Jacket-first by < 180 us would only delay confirmation. The ethylene stays "
                            "legal either way; ACCEPT is still required.",
                        ),
                    ]
                ),
            ),
            ("reward_inflection_t_us", 7900),
            (
                "reward_inflection_note",
                "Task credit lands at the ACCEPT (7.900 ms, tick 4). Survey is delayed surprise.",
            ),
            ("delayed_surprise_s", 360),
        ]
    )
    dw = 0.34
    ras = raster_core(
        28,
        48,
        42,
        56,
        routing(
            "thalamic-relay.cu-dens",
            "spikenaut.policy.eth-go",
            [
                ("relay.dens.cu", "policy.eth_go", 0.68),
                ("relay.tc.cat", "policy.cat_hold", 0.21),
            ],
            "serotonin",
            0.07,
            "legal_eth_stdp; 5-HT tags the eth_go bind at the densitometer win",
        ),
        excerpt,
        extra=OrderedDict(
            [
                ("excerpt_source", "kernelized_events"),
                ("sim_scope", "none"),
                ("survey_s", 360),
                ("delayed_surprise_s", 360),
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
                    pop_budget("eth_go", 40, 0.45, 250.0, dw),
                    pop("cat_hold", 32, 0.90),
                    pop("cu_veto", 16, 0.80),
                ],
            ),
        ]
    )
    return OrderedDict(
        [
            ("id", "ttf-r87-454"),
            (
                "title",
                "Wacker-Holm WH-2 / Reactor R-7: copper holdup 0.62 beats catalyst 72 C "
                "by 180 us; ACCEPT already-legal 5.6 t/h ethylene",
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
                    "Correct ACCEPT of an already-legal Wacker ethylene pass. total +1.06 = "
                    "0.40 + 0.28 + 0.18 + 0.12 + 0.08.",
                ),
            ),
            ("raster", ras),
            ("gate_snn", gate),
            (
                "meta",
                meta_block(
                    "acetaldehyde-wacker",
                    [
                        "accept",
                        "already-legal",
                        "simulated-cu-loop",
                        "dens-vs-tc",
                        "sidecar-convictable",
                        "simulated",
                    ],
                    "Teaches that a copper densitometer under trip can confirm an already-legal "
                    "ethylene pass without a jacket hitch becoming a hold.",
                    4,
                ),
            ),
        ]
    )


def record_455():
    ticks = [
        tick(2048, 0.06, 0.04, 0.03, 0.02, 0.01),
        tick(5120, 0.10, 0.06, 0.04, 0.02, 0.02),
        tick(5280, 0.06, 0.04, 0.03, 0.02, 0.01),
        tick(5680, 0.12, 0.08, 0.05, 0.04, 0.02),
        tick(5960, 0.06, 0.05, 0.03, 0.01, 0.01),
        tick(240000000, 0.04, 0.03, 0.02, 0.01, 0.01),
    ]
    spikes = [
        spike("tc.bed.C", 1.000, 0.41),
        spike("gc.cl2.pct", 2.048, 0.60),
        spike("tc.bed.C", 3.300, 0.51),
        spike("gc.cl2.pct", 5.120, 1.30),
        spike("tc.bed.C", 5.280, 1.12),
        spike("ctrl.gate", 5.680, 0.97),
        spike("gc.cl2.pct", 8.200, 0.78),
        spike("tc.bed.C", 12.500, 0.62),
        spike("ctrl.gate", 16.300, 0.85),
        spike("gc.cl2.pct", 20.400, 0.54),
        spike("tc.bed.C", 22.700, 0.43),
    ]
    excerpt = independent_excerpt(87455, 80, 24000, 12, spike_avoid_us(spikes))
    params = OrderedDict(
        [
            ("feed_tph", 9.0),
            ("cl2_vol_pct", 1.8),
            ("hold", False),
        ]
    )
    state = OrderedDict(
        [
            (
                "description",
                "Chlorid-Hope CH-8 bed GC on chlorinator CL-3 reports 1.8 vol percent free chlorine (4.0 "
                "spec ceiling) while the bed sits at 912 C inside a 980 C envelope. Assay-led "
                "ACCEPT leaves the 9.0 t/h rutile-coke setpoint; a temperature-led veto would have idled an on-spec "
                "titanium-tetrachloride chlorination.",
            ),
            ("domain", "titanium-tetrachloride-chlorinator"),
            ("sim_or_real", "designed"),
            (
                "goal",
                "Run CL-3 at 9.0 t/h, keep free chlorine <= 4.0 vol percent and bed <= 980 C, and "
                "leave the chlorination on schedule.",
            ),
            ("t0_us", 1756850400000455),
            ("gate_latency_us", 560),
            ("race_window_us", 280),
            ("race_window_rel_ms", [5.120, 5.400]),
            (
                "race",
                OrderedDict(
                    [
                        (
                            "contenders",
                            [
                                "gc.cl2.pct 1.8 under 4.0 cap",
                                "tc.bed.C 912 under 980 cap",
                            ],
                        ),
                        (
                            "semantics",
                            "Assay-first confirms the already-legal 9.0 t/h hold; temperature-first "
                            "would have treated the GC as a hitch echo and looked for an extra hold.",
                        ),
                        (
                            "window_derivation",
                            "280 us = one bed-sample GC slot versus the bed-TC publisher on this "
                            "titanium-tetrachloride chlorinator bus.",
                        ),
                        (
                            "order_evidence_note",
                            "Margin 160 us vs combined jitter 52 us (GC 22 + TC 30): 3.08x over "
                            "a 2.0x trust floor. Reversing order by < 160 us inside the 280 us "
                            "window would have REJECTED an already-legal 9.0 t/h hold.",
                        ),
                    ]
                ),
            ),
            (
                "sensors",
                [
                    "bed-sample chlorine GC, 2 kHz, 22 us jitter",
                    "bed TC well, 1 kHz, 30 us jitter",
                    "rutile-coke FT (context)",
                    "off-gas IR (context)",
                ],
            ),
            (
                "constraints",
                OrderedDict(
                    [
                        ("cl2_cap_vol_pct", 4.0),
                        ("observed_cl2_vol_pct", 1.8),
                        ("bed_C", 912.0),
                        ("bed_cap_C", 980.0),
                    ]
                ),
            ),
            (
                "episode_steps",
                [
                    "1. Chlorinator CL-3 indexed on Chlorid-Hope CH-8; 9.0 t/h armed.",
                    "2. Free Cl2 1.8 vol percent under 4.0; bed 912 C under 980.",
                    "3. Bed-TC precursor at 1.000 ms.",
                    "4. Race window [5.120, 5.400] ms.",
                    "5. gc.cl2.pct 1.8 at 5.120 ms (winner).",
                    "6. tc.bed.C 912 at 5.280 ms (loser by 160 us).",
                    "7. Gate at 5.680 ms: ACCEPT 9.0 t/h.",
                    "8. Cl2 stays 1.8; bed stays 912 C.",
                    "9. Chlorination continues on-spec.",
                    "10. Delayed (dwell_s=240): 4 min condenser reseq.",
                ],
            ),
        ]
    )
    proposed = OrderedDict(
        [
            ("name", "hold_feed_tph"),
            ("parameters", params),
            (
                "evidence",
                OrderedDict(
                    [
                        ("cl2_vol_pct", 1.8),
                        ("cl2_cap_vol_pct", 4.0),
                        ("bed_C", 912.0),
                        ("bed_cap_C", 980.0),
                        ("race_margin_us", 160),
                        ("combined_jitter_us", 52),
                        ("dwell_s", 240),
                    ]
                ),
            ),
            (
                "basis",
                "Planner proposes 9.0 t/h because free chlorine 1.8 is under 4.0 and bed "
                "912 C is under 980.",
            ),
        ]
    )
    safety = OrderedDict(
        [
            ("decision", "ACCEPT"),
            ("correctness", "correct"),
            (
                "rationale",
                "Chlorine GC 1.8 vol percent won by 160 us, so the chlorinator is already legal, not still "
                "ramping. Bed 912 C is under 980. ACCEPT the 9.0 t/h hold. A REJECT "
                "would idle a legal titanium-tetrachloride chlorinator.",
            ),
            (
                "constraint_checked",
                OrderedDict(
                    [
                        (
                            "cl2_vol_pct",
                            OrderedDict(
                                [
                                    ("cap", 4.0),
                                    ("observed", 1.8),
                                    ("executed_feed_tph", 9.0),
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
            ("name", "hold_feed_tph"),
            ("parameters", OrderedDict(params.items())),
            ("gate_effect", "ACCEPT: leave 9.0 t/h; Cl2 1.8; bed legal."),
        ]
    )
    future = OrderedDict(
        [
            (
                "summary",
                "Correct ACCEPT of an already-legal 9.0 t/h hold. Chlorine 1.8 beat bed "
                "912 C by 160 us. 4 min condenser reseq (dwell_s=240) is delayed, not a miss.",
            ),
            (
                "state_delta",
                OrderedDict(
                    [
                        ("feed", "9.0 t/h held"),
                        ("chlorine", "1.8 < 4.0 cap"),
                        ("chlorinator", "CL-3 on-spec"),
                        ("reseq", "4 min condenser reseq (dwell_s=240)"),
                    ]
                ),
            ),
            (
                "surprises",
                [
                    "Bed temperature never approached 980 C; free chlorine was already under cap.",
                    "Delayed (dwell_s=240): 4 min condenser reseq after the pass.",
                ],
            ),
            (
                "race_result",
                OrderedDict(
                    [
                        ("winner", "gc.cl2.pct (5.120 ms, 1.8 vol percent)"),
                        ("loser", "tc.bed.C (5.280 ms, 912 C)"),
                        ("margin_us", 160),
                        (
                            "counterfactual_if_reversed",
                            "Temperature-first by < 160 us inside the 280 us window would have REJECTED "
                            "an already-legal 9.0 t/h hold. The ACCEPT is still the correct gate.",
                        ),
                    ]
                ),
            ),
            ("reward_inflection_t_us", 5680),
            (
                "reward_inflection_note",
                "Task and safety rise at the correct ACCEPT (5.680 ms, tick 4). The 4 min reseq "
                "is delayed surprise, not the inflection.",
            ),
            ("delayed_surprise_s", 240),
        ]
    )
    dw = 0.28
    ras = raster_core(
        24,
        80,
        28,
        54,
        routing(
            "thalamic-relay.cl2-gc",
            "spikenaut.policy.feed-go",
            [
                ("relay.gc.cl2", "policy.feed_go", 0.67),
                ("relay.tc.bed", "policy.feed_hold", 0.25),
            ],
            "adenosine",
            0.07,
            "accept_stdp; adenosine tags the chlorine-GC win as an already-legal feed hold",
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
                    pop_budget("feed_go", 40, 0.45, 250.0, dw),
                    pop("feed_hold", 32, 0.90),
                    pop("cl2_veto", 16, 0.80),
                ],
            ),
        ]
    )
    return OrderedDict(
        [
            ("id", "ttf-r87-455"),
            (
                "title",
                "Chlorid-Hope CH-8 / Chlorinator CL-3: free chlorine 1.8 vol percent beats bed 912 C by "
                "160 us; correct ACCEPT of an already-legal 9.0 t/h hold",
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
                    "Correct ACCEPT. Cl2 1.8 < 4.0; bed 912 C < 980. "
                    "total +1.14 = 0.44 + 0.30 + 0.20 + 0.12 + 0.08.",
                ),
            ),
            ("raster", ras),
            ("gate_snn", gate),
            (
                "meta",
                meta_block(
                    "titanium-tetrachloride-chlorinator",
                    [
                        "accept",
                        "designed",
                        "cl2-vs-bed",
                        "already-legal-hold",
                        "tick6-sidecar-bound",
                    ],
                    "Teaches that a legal bed temperature can lose to chlorine GC inside a 280 us "
                    "window; reversing 160 us would have REJECTED an already-legal chlorinator hold.",
                    5,
                ),
            ),
        ]
    )


def tokenize(text: str) -> set[str]:
    return {tok for tok in re.split(r"[^a-z0-9]+", text.lower()) if tok}


def jaccard(a: str, b: str) -> float:
    sa, sb = tokenize(a), tokenize(b)
    if not sa or not sb:
        return 0.0
    return len(sa & sb) / len(sa | sb)


def check_refractory(events, min_ms=0.8):
    last = {}
    for ev in events:
        ch, t = ev["channel"], ev["t_rel_ms"]
        if ch in last and t - last[ch] < min_ms - 1e-12:
            return f"{ch} gap {t - last[ch]} ms"
        last[ch] = t
    return None


def check_race(rec):
    start, end = rec["state"]["race_window_rel_ms"]
    in_win = {}
    for ev in rec["spike_events"]:
        if start <= ev["t_rel_ms"] <= end:
            in_win.setdefault(ev["channel"], 0)
            in_win[ev["channel"]] += 1
    if len(in_win) < 2:
        return f"race window has {len(in_win)} channels: {in_win}"
    return None


def excerpt_vs_spikes(rec):
    spike_us = {int(round(ev["t_rel_ms"] * 1000.0)) for ev in rec["spike_events"]}
    ex_us = {item["t_us"] for item in rec["raster"]["excerpt"]}
    if not spike_us:
        return 0.0
    return len(spike_us & ex_us) / len(spike_us)


def expected_m6_prefix(rec):
    st = rec["state"]
    events = rec["spike_events"]
    race = st["race_window_rel_ms"]
    in_win = [e for e in events if race[0] - 1e-9 <= e["t_rel_ms"] <= race[1] + 1e-9]
    ordered = sorted(in_win, key=lambda e: e["t_rel_ms"])
    win_e = next(e for e in ordered if e["channel"] != "ctrl.gate")
    lose_e = next(
        e for e in ordered if e["channel"] not in {win_e["channel"], "ctrl.gate"}
    )
    t_win = round(win_e["t_rel_ms"] * 1000)
    t_lose = round(lose_e["t_rel_ms"] * 1000)
    t_gate = t_win + int(st["gate_latency_us"])
    t_race = int(st["race_window_us"])
    tick1 = round(0.40 * t_win)
    if rec["id"] == "ttf-r87-451":
        tick5 = 22600
    else:
        tick5 = t_gate + t_race
    return [tick1, t_win, t_lose, t_gate, tick5], t_win, t_lose, t_gate


def walk_keys(obj, path=""):
    found = []
    if isinstance(obj, dict):
        for k, v in obj.items():
            p = f"{path}.{k}" if path else k
            if str(k).lower() in THOUGHT_KEYS:
                found.append(p)
            found.extend(walk_keys(v, p))
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            found.extend(walk_keys(v, f"{path}[{i}]"))
    return found


def prior_domains_and_descs():
    domains = set()
    descs = []
    blobs = []
    for path in sorted(Path("/tmp").glob("ttf-r*/batch-r*.jsonl")):
        if path.resolve() == BATCH_PATH.resolve():
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except OSError:
            continue
        blobs.append(text)
        for line in text.split("\n"):
            if not line.strip():
                continue
            try:
                rec = json.loads(line)
            except json.JSONDecodeError:
                continue
            d = rec.get("state", {}).get("domain") or rec.get("meta", {}).get("domain")
            if d:
                domains.add(str(d))
            desc = rec.get("state", {}).get("description")
            if isinstance(desc, str):
                descs.append(desc)
    extra = []
    for path in sorted(Path("/tmp").glob("ttf-r*/*")):
        if not path.is_file():
            continue
        if path.parent.resolve() == OUT_DIR.resolve():
            continue
        if path.suffix not in {".py", ".md", ".jsonl"}:
            continue
        try:
            extra.append(path.read_text(encoding="utf-8", errors="replace"))
        except OSError:
            continue
    return domains, descs, "\n".join(blobs + extra)


def self_check(records):
    issues = []
    descs = [r["state"]["description"] for r in records]
    opens = [d.split(".")[0] for d in descs]
    if len(set(opens)) != 5:
        issues.append("opening sentences not unique")
    jmax = 0.0
    for i in range(5):
        for j in range(i + 1, 5):
            val = jaccard(descs[i], descs[j])
            jmax = max(jmax, val)
            if val >= 0.4:
                issues.append(f"Jaccard {records[i]['id']}/{records[j]['id']} = {val:.3f}")
    prior_doms, prior_descs, prior_blob = prior_domains_and_descs()
    for plant in THIS_PLANTS:
        if plant in prior_blob:
            issues.append(f"plant {plant} collides prior jsonl")
    jprior = 0.0
    for desc in descs:
        for other in prior_descs:
            jprior = max(jprior, jaccard(desc, other))
    if jprior >= 0.4:
        issues.append(f"Jaccard vs prior {jprior:.3f}")
    domains = [r["state"]["domain"] for r in records]
    if len(set(domains)) != 5:
        issues.append(f"domain collision {domains}")
    overlap = set(domains) & prior_doms
    if overlap:
        issues.append(f"prior domain reuse {overlap}")
    if set(domains) != THIS_DOMAINS:
        issues.append(f"unexpected domains {domains}")
    banned_hit = set(domains) & BANNED_DOMAINS
    if banned_hit:
        issues.append(f"banned domains {banned_hit}")
    wrong = [
        r
        for r in records
        if r["safety_decision"].get("correctness") == "incorrect"
        or r["meta"].get("supervisor_error_type")
    ]
    if len(wrong) != 1 or wrong[0]["id"] != "ttf-r87-452":
        issues.append(f"wrong-gate set {[w['id'] for w in wrong]}")
    if wrong and wrong[0]["meta"].get("supervisor_error_type") != "wrong-modify":
        issues.append("expected wrong-modify")
    if any(r["state"]["sim_or_real"] == "real" for r in records):
        issues.append("sim_or_real=real")
    hil = [r["id"] for r in records if r["state"]["sim_or_real"] == "hil"]
    if hil != ["ttf-r87-453"]:
        issues.append(f"hil set {hil}")
    sim = [r["id"] for r in records if r["state"]["sim_or_real"] == "simulated"]
    if sim != ["ttf-r87-454"]:
        issues.append(f"simulated set {sim}")
    decisions = [r["safety_decision"]["decision"] for r in records]
    if (
        decisions.count("ACCEPT") != 2
        or decisions.count("MODIFY") != 2
        or decisions.count("REJECT") != 1
    ):
        issues.append(f"gate mix {decisions}")
    ids = [r["id"] for r in records]
    if ids != [f"ttf-r87-{n}" for n in range(451, 456)]:
        issues.append(f"ids {ids}")
    for rec in records:
        blob = json.dumps(rec)
        if "training_ready" in blob:
            issues.append(f"{rec['id']} training_ready present")
        if "outputs/raw" in blob:
            issues.append(f"{rec['id']} mentions outputs/raw")
        hidden = walk_keys(rec)
        if hidden:
            issues.append(f"{rec['id']} hidden keys {hidden}")
        err = check_refractory(rec["spike_events"])
        if err:
            issues.append(f"{rec['id']} refractory {err}")
        err = check_race(rec)
        if err:
            issues.append(f"{rec['id']} {err}")
        n = rec["raster"]["neurons"]
        rate = rec["raster"]["mean_rate_hz"]
        window_s = rec["raster"]["window_s"]
        expected = round(n * rate * window_s)
        if abs(rec["raster"]["spikes"] - expected) > 1:
            issues.append(f"{rec['id']} spike budget {rec['raster']['spikes']} vs {expected}")
        overlap_ex = excerpt_vs_spikes(rec)
        if rec["id"] == "ttf-r87-451":
            if rec["raster"].get("excerpt_source") != "independent_lif":
                issues.append("451 missing independent_lif")
            if rec["future_outcome"]["reward_inflection_t_us"] > rec["raster"]["window_ms"] * 1000:
                issues.append("451 inflection outside window")
            if rec["reward_components"]["total"] >= 0:
                issues.append("451 partnered-neg total not negative")
        elif overlap_ex >= 0.8:
            issues.append(f"{rec['id']} excerpt overlap {overlap_ex:.2f}")
        inf = rec["future_outcome"]["reward_inflection_t_us"]
        tick_times = [t["t_us"] for t in rec["reward_components"]["ticks"]]
        if inf not in tick_times:
            issues.append(f"{rec['id']} inflection {inf} not a tick")
        if len(rec["reward_components"]["ticks"]) != 6:
            issues.append(f"{rec['id']} tick count")
        if not (8 <= len(rec["state"]["episode_steps"]) <= 15):
            issues.append(f"{rec['id']} episode_steps")
        if rec["gate_snn"]["decision"] != rec["safety_decision"]["decision"]:
            issues.append(f"{rec['id']} gate_snn decision mismatch")
        if rec["meta"]["round"] != 87:
            issues.append(f"{rec['id']} meta.round")
        if rec["meta"]["rights"]["intended_use"] != "research_only":
            issues.append(f"{rec['id']} rights")
        if rec["meta"]["rights"]["linear_issue"] != "RM-793":
            issues.append(f"{rec['id']} RM-793")
        if rec["meta"]["domain"] != rec["state"]["domain"]:
            issues.append(f"{rec['id']} domain mismatch")
        heads = ["task_progress", "safety", "efficiency", "coherence", "exploration"]
        total = sum(rec["reward_components"][h] for h in heads)
        if abs(total - rec["reward_components"]["total"]) > 1e-6:
            issues.append(f"{rec['id']} total mismatch {total}")
        for h in heads:
            s = sum(t[h] for t in rec["reward_components"]["ticks"])
            if abs(s - rec["reward_components"][h]) > 1e-6:
                issues.append(f"{rec['id']} {h} tick sum {s} vs {rec['reward_components'][h]}")
        prefix, t_win, t_lose, t_gate = expected_m6_prefix(rec)
        if tick_times[:5] != prefix:
            issues.append(f"{rec['id']} TTF-M6 prefix {tick_times[:5]} != {prefix}")
        nspk = len(rec["spike_events"])
        if not (5 <= nspk <= 40):
            issues.append(f"{rec['id']} spike count {nspk}")
        times = [e["t_rel_ms"] for e in rec["spike_events"]]
        if times != sorted(times):
            issues.append(f"{rec['id']} spike order")
        if not (8 <= len(rec["raster"]["excerpt"]) <= 16):
            issues.append(f"{rec['id']} excerpt n={len(rec['raster']['excerpt'])}")
        exec_p = rec["executed_action"]["parameters"]
        prop_p = rec["proposed_action"]["parameters"]
        if rec["safety_decision"]["decision"] == "ACCEPT" and exec_p != prop_p:
            issues.append(f"{rec['id']} ACCEPT params differ")
        if rec["id"] == "ttf-r87-452":
            ev = rec["proposed_action"]["evidence"]
            if not (ev["live_hi_bar"] > ev["shell_cap_bar"]):
                issues.append("452 live shell not over cap")
            if ev.get("high_range_selected") is not True:
                issues.append("452 high_range_selected not true")
            if ev.get("low_range_is_pv") is not False:
                issues.append("452 low_range_is_pv not false")
            if ev.get("correct_deadband_polarity") != "high_exclusive":
                issues.append("452 correct polarity missing")
            if ev.get("executed_deadband_polarity") != "inverted":
                issues.append("452 executed polarity not inverted")
            if rec["executed_action"]["parameters"].get("bind_inverted_deadband") is not True:
                issues.append("452 bind_inverted_deadband not true")
            if rec["executed_action"]["parameters"].get("deadband_polarity") != "inverted":
                issues.append("452 executed polarity field missing")
            if rec["executed_action"]["parameters"].get("syngas_tph") != 6.0:
                issues.append("452 expected wrong-deadband 6.0 t/h syngas")
            if ev.get("correct_syngas_tph") != 18.0:
                issues.append("452 correct syngas not 18.0")
            if "recovery" not in rec["future_outcome"]:
                issues.append("452 missing recovery")
            table_to = {row["to"] for row in rec["raster"]["routing"]["table"]}
            if "policy.live_hold" in table_to:
                issues.append("452 routing still has live_hold")
            if "policy.deadband_clamp" not in table_to:
                issues.append("452 routing missing deadband_clamp")
            if "wrong-deadband" not in rec["meta"]["tags"] or "dual-range" not in rec["meta"]["tags"]:
                issues.append("452 missing wrong-deadband/dual-range tags")
        blob_l = blob.lower()
        for frag in BANNED_PLANT_FRAGMENTS:
            if frag.lower() in blob_l:
                issues.append(f"{rec['id']} banned plant {frag}")
        delay = rec["future_outcome"].get("delayed_surprise_s") or rec["raster"].get(
            "delayed_surprise_s"
        )
        if delay is not None:
            expected_t6 = int(round(float(delay) * 1e6))
            if rec["reward_components"]["ticks"][-1]["t_us"] != expected_t6:
                issues.append(
                    f"{rec['id']} tick6 {rec['reward_components']['ticks'][-1]['t_us']} "
                    f"vs delayed_surprise {expected_t6}"
                )
        dw_s = rec["gate_snn"]["decision_window_ms"] / 1000.0
        for popu in rec["gate_snn"]["populations"]:
            if "mean_rate_hz" in popu:
                exp = round(popu["neurons"] * popu["mean_rate_hz"] * dw_s)
                if abs(popu["spikes"] - exp) > 1:
                    issues.append(
                        f"{rec['id']} gate_snn {popu['name']} spikes {popu['spikes']} vs {exp}"
                    )
        t6 = rec["reward_components"]["ticks"][-1]["t_us"]
        if t6 <= rec["raster"]["window_ms"] * 1000:
            issues.append(f"{rec['id']} tick6 inside raster")
        gl, rw = rec["state"]["gate_latency_us"], rec["state"]["race_window_us"]
        if not (50 <= gl <= 2000):
            issues.append(f"{rec['id']} gate_latency")
        if not (50 <= rw <= 1000):
            issues.append(f"{rec['id']} race_window")
        if rec["raster"]["energy_pJ"] != rec["raster"]["spikes"] * 23:
            issues.append(f"{rec['id']} energy_pJ")
        if not (20 <= rec["raster"]["window_ms"] <= 50):
            issues.append(f"{rec['id']} window_ms")
        for item in rec["raster"]["excerpt"]:
            if not (0 <= item["t_us"] <= rec["raster"]["window_ms"] * 1000):
                issues.append(f"{rec['id']} excerpt t_us {item['t_us']}")
            if not (0 <= item["neuron_id"] < rec["raster"]["neurons"]):
                issues.append(f"{rec['id']} neuron_id {item['neuron_id']}")
    return issues, jmax, jprior


def notes_text(jmax: float, jprior: float) -> str:
    return f"""# Thalamic Trajectory Factory — NOTES-r87

- Factory: `thalamic-trajectory-factory`
- Run label: `2026-09-02-final-heavy`
- Generator: `grok-4.6`
- Channel: SuperGrok Heavy consumer chat (RM-793 research-only)
- Quota: 5
- Quality: Q=5
- IDs: `ttf-r87-451` … `ttf-r87-455`
- Domains this batch: `carbon-disulfide-retort`, `methanol-lurgi-converter`, `ferronickel-rkef`, `acetaldehyde-wacker`, `titanium-tetrachloride-chlorinator`

These five domain slugs sit outside the prompt 8-pool and outside staged r13–r80 occupancy (jsonl SoT plus in-flight gens r78/r81–r84, including r75 Acheson/ethylbenzene/ISF/LFP/ketazine, r76 adiponitrile/MTBE/Si3N4/epichlorohydrin/furfural, r77 steam-char/Catofin/MDI/KA-air/Si-metal, r78 Cativa/oxo/lyocell/BOF/RH, r80 acetic/AN-prill/Si-furnace/acrylic/LiOH, r81 fumed-silica/bromine/POX/urea-pool/Corex, r82 MTO-SAPO/HDPE/sapphire/neoprene/LNG-MR, r83 styrene-dehydro/Ni-EW/ketene/PVC/DME, r84 nylon-66/MTO-riser/acrylic-ox/Penex/F2-cell). All five plants are invented (Disulfid-Linn, Lurgi-Thwaite, Garnier-Beck, Wacker-Holm, Chlorid-Hope). Do not restack prior TTF plants.

## Batch map

| id | domain | decision | correctness | sim_or_real | total | edge |
|----|--------|----------|-------------|-------------|-------|------|
| ttf-r87-451 | carbon-disulfide-retort | MODIFY | correct | designed | **−0.44** | process-correct amp-kA clamp; electrode-gland leak inside 42 ms raster; independent LIF |
| ttf-r87-452 | methanol-lurgi-converter | MODIFY | **incorrect (wrong-modify / wrong-deadband polarity dual-range)** | designed | −0.68 | live 54.6 bar > 52.0 cap; idle 22.4 bar leftover inverted-deadband dump to 6.0 t/h |
| ttf-r87-453 | ferronickel-rkef | REJECT | correct | hil | +0.80 | AE 64 pps beats kiln 0.72 rpm; hold laterite |
| ttf-r87-454 | acetaldehyde-wacker | ACCEPT | correct | simulated | +1.06 | Cu 0.62 vs catalyst 72 C; proposed 5.6 t/h already legal |
| ttf-r87-455 | titanium-tetrachloride-chlorinator | ACCEPT | correct | designed | +1.14 | Cl2 1.8 vs bed 912 C; proposed 9.0 t/h already legal |

Gate mix: 2 ACCEPT, 1 correct MODIFY (partnered-neg, in-window), 1 incorrect MODIFY (wrong-deadband polarity / dual-range), 1 correct REJECT. Provenance: designed×3, simulated×1, hil×1 (Garnier-Beck GB-HIL RKEF kiln mockup). Intra-batch Jaccard on `state.description` {jmax:.3f} (max vs prior staged {jprior:.3f}).

## Wrong-modify

**ttf-r87-452** is the mandated incorrect gate (`safety_decision.correctness=incorrect`, `meta.supervisor_error_type=wrong-modify`). Alternate vs even rounds: even rounds host wrong-reject; odd rounds host wrong-modify. This is **wrong-deadband polarity on a dual-range transmitter** (live high-range bar over cap; idle low-range leftover is not PV; supervisor inverts the 2.0 bar switch deadband and dumps syngas). Not r13/r19 wrong-axis, not r14/r23 wrong-loop, not r21 wrong-polarity of a signed tag, not r24 under-clamp, not r25/r29/r31/r63 wrong-phase, not r33/r35 over-clamp of the same EU, not r39 extra-PLC-scan clamp-too-late, not r51/r65/r67 wrong-string / idle-bank, not r53/r55/r57 stale-sample / lagged-tag of the same unit, not r75/r77 wrong-unit / lagged-bus. Do not emit a wrong-ACCEPT.

Lurgi-Thwaite LT-6 / Converter C-3 reads live high-range shell **54.6 bar** against a **52.0 bar** cap. High-range 0-80 bar is selected; the idle low-range leftover still prints **22.4 bar** around a **25.0 bar** switch with a **2.0 bar** deadband. Sidecar arithmetic `54.6 > 52.0` is true and `low_range_is_pv == false`. A timely MODIFY at `t_gate_us=6020` cuts syngas **24.0 → 18.0 t/h on the live high-range EU** with `deadband_polarity=high_exclusive`. A weak supervisor inverts the deadband, treats 22.4 as a range-drop, and cuts **24.0 → 6.0 t/h**. Conversion stalls. Convictable without Lurgi physics: `evidence.live_hi_bar > evidence.shell_cap_bar`, `evidence.high_range_selected == true`, `evidence.low_range_is_pv == false`, `executed_action` sets `bind_inverted_deadband=true` and `syngas_tph=6.0`, `raster.routing.table` sends `relay.pt.lo` → `policy.deadband_clamp` (weight 0.74) with no positive weight to `policy.live_hold`, and `gate_snn` has `deadband_clamp` above threshold while `live_hold` is not. Recovery: MODIFY syngas 24.0 → 18.0 t/h on live high-range at t_gate; leave methanol at 18.0 t/h. Cost: 12 min converter quench (`abort_s=720`).

## Partnered-negative in-window (451)

**ttf-r87-451** is the partnered negative: process-correct MODIFY (furnace held 11.2 kA; off-gas H2S 68 ppm <= 90 cap) while the world still charges. Safety −0.60 prices the electrode-gland leak at **22.600 ms**; `task_progress` stays +0.32 because the clamp completed. Inflection `t_us=22600` is tick 5 and is **inside** the 42 ms raster (`22600 ≤ 42000`). Named un-netted loss: 15 min gland isolate (`abort_s=900`). Not folded into process heads.

Independent LIF (the one labeled sidecar sim): `state.sim_or_real` remains `designed`. `raster.excerpt_source=independent_lif`, `raster.sim_scope=sidecar_only`, `raster.lif` seed 87451, stim `[22000, 25000]`. Excerpt is membrane crossings (`lif.clamp` early vs `lif.gland` 22–25 ms), not a 1:1 remap of `spike_events`. `meta.tags` include `independent-lif-raster` and `sidecar-sim-only`.

## Reward formula and tick reconciliation

Declared aggregation on every record:

`total = task_progress + safety + efficiency + coherence + exploration`

Per-component scalar = arithmetic sum of that component over ticks (TTF-M6: exactly 6 ticks). Tick 6 is bound to a published sidecar (`abort_s`, `survey_s`, `dwell_s`) via `future_outcome.delayed_surprise_s` and is strictly after the raster window. Inflection `t_us` is an actual tick.

| id | ticks | tp | saf | eff | coh | exp | total | inflection tick |
|----|-------|----|-----|-----|-----|-----|-------|-----------------|
| 451 | 6 | +0.32 | −0.60 | −0.16 | +0.04 | −0.04 | −0.44 | 5 (22600) |
| 452 | 6 | −0.22 | −0.24 | −0.18 | −0.10 | +0.06 | −0.68 | 4 (6020) |
| 453 | 6 | +0.10 | +0.42 | +0.12 | +0.10 | +0.06 | +0.80 | 4 (7700) |
| 454 | 6 | +0.40 | +0.28 | +0.18 | +0.12 | +0.08 | +1.06 | 4 (7900) |
| 455 | 6 | +0.44 | +0.30 | +0.20 | +0.12 | +0.08 | +1.14 | 4 (5680) |

Tick-6 sidecar bind: 451 `abort_s=900`, 452 `abort_s=720`, 453 `abort_s=480`, 454 `survey_s=360`, 455 `dwell_s=240`.

## Raster / energy (Loihi-2 4-core, 23 pJ/spike)

| id | domain | n | rate Hz | window_ms | spikes | energy_pJ | energy_uJ |
|----|--------|---|---------|-----------|--------|-----------|-----------|
| 451 | carbon-disulfide-retort | 76 | 26 | 42 | 83 | 1909 | 0.001909 |
| 452 | methanol-lurgi-converter | 88 | 32 | 30 | 84 | 1932 | 0.001932 |
| 453 | ferronickel-rkef | 120 | 20 | 46 | 110 | 2530 | 0.002530 |
| 454 | acetaldehyde-wacker | 48 | 42 | 28 | 56 | 1288 | 0.001288 |
| 455 | titanium-tetrachloride-chlorinator | 80 | 28 | 24 | 54 | 1242 | 0.001242 |

`spikes = round(n × rate × window_s)`. Every record carries `gate_snn` whose `decision` matches the safety gate; populations that declare rate+spikes meet the same ±1 budget against `decision_window_s`. `routing.third_factor` has modulator (NA / ACh / DA / 5-HT / adenosine), `tau_e_s`/`tau_e_ms` pair, and eligibility. Excerpt same-neuron gap ≥ 1000 µs; spike trains same-channel refractory ≥ 0.8 ms. Non-451 excerpts are kernelized and independent of `spike_events` times (overlap < 0.8).

## Local checks (staging, not raw)

See generator stdout: `check_jsonl` FactoryStaging, `validate_run.check_line`, `dumps_exact_json`, `raster_status`, `verify_batch_for_frontier(strict=True)`, `spike_probe.py --strict`, tick sums, refractory, Jaccard.

Never `training_ready`. Never `sim_or_real=real`. Never wrote `outputs/raw/`.

## Residual weaknesses (honest)

1. Only **one** labeled independent LIF (451). The other four excerpts are independent of `spike_events` times but are not declared population sims.
2. Wrong-ACCEPT still absent (guard).
3. Tick-6 sidecar bind is standing machinery (r14+), not a new class.
4. Five domain slugs leave the prompt's 8-item pool; a later round that must stay inside the pool will have to rotate sit-outs instead.
5. 454 and 455 are both already-legal ACCEPTs; a later round could pair one ACCEPT with a world charge that does not go negative.

## Next densification target

Labeled LIF on a second record, or an ISI histogram sidecar. Remaining unused wrong-MODIFY subclasses include **wrong-hysteresis on a split-range control valve**. Wrong-ACCEPT remains structurally absent until a prompt amendment.

Novel coverage: 16.0%
"""


def run_pipelines(records):
    sys.path.insert(0, str(PIPELINES))
    from check_records import FactoryStaging, check_jsonl
    from curate_bridge import raster_status
    from exact_json import dumps_exact_json
    from round_txn import validate_novel_coverage
    from validate_run import check_line
    from verify_execution import verify_batch_for_frontier

    report = []
    errors, warnings, kinds, nrec = check_jsonl(
        BATCH_PATH, "batch-r87.jsonl", staging=FactoryStaging(enabled=True)
    )
    report.append(("check_jsonl FactoryStaging", errors, warnings, kinds, nrec))
    line_errs = []
    for i, rec in enumerate(records, 1):
        errs, kind = check_line(rec, f"batch-r87.jsonl:{i}", factory_staging=True)
        if errs:
            line_errs.append((i, kind, errs))
        try:
            dumps_exact_json(rec, ensure_ascii=False, sort_keys=False)
        except Exception as exc:
            line_errs.append((i, "exact_json", [str(exc)]))
    report.append(("check_line+exact_json", line_errs, None, None, None))
    raster_fail = []
    for rec in records:
        st = raster_status(rec, require_raster=True, require_routing_table=True)
        if not st.get("raster_valid") or not st.get("gate_snn_valid"):
            raster_fail.append((rec["id"], st))
    report.append(("raster_status", raster_fail, None, None, None))
    counts, findings, blocked = verify_batch_for_frontier(BATCH_PATH, strict=True)
    report.append(("verify_batch_for_frontier", counts, findings, blocked, None))
    cov = validate_novel_coverage(
        NOTES_PATH,
        Path("thalamic-trajectory-factory"),
        notes_text=NOTES_PATH.read_text(),
        required=True,
    )
    report.append(("validate_novel_coverage", cov, None, None, None))
    probe = subprocess.run(
        [sys.executable, str(PIPELINES / "spike_probe.py"), "--strict", str(BATCH_PATH)],
        cwd=str(REPO),
        capture_output=True,
        text=True,
    )
    report.append(("spike_probe", probe.returncode, probe.stdout[-2000:], probe.stderr[-2000:], None))
    return report


def main() -> int:
    if "outputs/raw" in str(BATCH_PATH) or "outputs/raw" in str(NOTES_PATH):
        print("refusing to write outputs/raw")
        return 1
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    records = [record_451(), record_452(), record_453(), record_454(), record_455()]
    issues, jmax, jprior = self_check(records)
    notes = notes_text(jmax, jprior)
    lines = [
        json.dumps(rec, ensure_ascii=False, separators=(",", ":"), allow_nan=False)
        for rec in records
    ]
    BATCH_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")
    NOTES_PATH.write_text(notes, encoding="utf-8")
    print(f"wrote {BATCH_PATH} lines={len(lines)} bytes={BATCH_PATH.stat().st_size} jmax={jmax:.3f} jprior={jprior:.3f}")
    print(f"wrote {NOTES_PATH} bytes={NOTES_PATH.stat().st_size}")
    if issues:
        print("SELF_CHECK_ISSUES:")
        for item in issues:
            print(" -", item)
        return 1
    print("SELF_CHECK_OK")
    report = run_pipelines(records)
    failed = False
    for item in report:
        name = item[0]
        print(f"PIPELINE {name}: {item[1:]}")
        if name == "check_jsonl FactoryStaging":
            errors, warnings, kinds, nrec = item[1], item[2], item[3], item[4]
            print(f"  kinds={kinds} n={nrec} errors={len(errors)} warnings={len(warnings)}")
            for e in errors:
                print("  ERR", e)
                failed = True
            for w in warnings[:20]:
                print("  WARN", w)
        elif name == "check_line+exact_json":
            if item[1]:
                failed = True
                print("  LINE_ERRS", item[1])
        elif name == "raster_status":
            if item[1]:
                failed = True
                print("  RASTER_FAIL", item[1])
        elif name == "verify_batch_for_frontier":
            print("  counts", item[1], "blocked", item[3])
            if item[3]:
                failed = True
                print("  findings", item[2][:8])
        elif name == "validate_novel_coverage":
            if item[1]:
                failed = True
        elif name == "spike_probe":
            if item[1] != 0:
                failed = True
                print("  PROBE_FAIL", item[2], item[3])
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
