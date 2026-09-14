def lif_341_excerpt():
    n = 76
    dt_us = 100
    tau_m_ms = 19.0
    v_th = 1.0
    v_reset = 0.0
    refractory_us = 1000
    i_bias = 0.91
    i_stim_peak = 2.42
    stim = (22000, 25000)
    seed = 65341
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
    channels = ["lif.clamp" if t < 22000 else "lif.leak" for t, _ in picked]
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
            ("seed", 65341),
            (
                "note",
                "Population sim scoped to this sidecar. Plant remains designed. "
                "Neurons 0-13 carry +0.62 kiln-RPM clamp bias; stim 22-25 ms is the tube-sheet leak.",
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


def record_341():
    excerpt, extra = lif_341_excerpt()
    ticks = [
        tick(2112, 0.04, -0.02, -0.02, 0.01, 0.00),
        tick(5280, 0.08, -0.04, -0.02, 0.01, -0.01),
        tick(5460, 0.04, -0.03, -0.02, 0.00, 0.00),
        tick(5980, 0.08, -0.05, -0.03, 0.02, -0.01),
        tick(22600, 0.06, -0.41, -0.04, -0.01, -0.01),
        tick(900000000, 0.02, -0.05, -0.03, 0.01, -0.01),
    ]
    state = OrderedDict(
        [
            (
                "description",
                "Rotary APT calciner C-4 on Tungstate-Keld TK-6 is dumping 186 ppm NH3 off-gas "
                "while kiln RPM still sits a legal 1.8 under 2.4. NH3-first clamps RPM 1.8 -> 1.1; "
                "speed-first would keep cruise because skin 742 C is still under the 780 C tube "
                "cap. A tube-sheet leak already seated on the discharge hood does not appear on "
                "NH3 or RPM until the AE dump.",
            ),
            ("domain", "wolfram-APT-calciner"),
            ("sim_or_real", "designed"),
            (
                "goal",
                "Keep C-4 off-gas NH3 <= 90 ppm and finish the APT roast without dumping calcine "
                "through a torn tube-sheet.",
            ),
            ("t0_us", 1756850400000341),
            ("gate_latency_us", 700),
            ("race_window_us", 360),
            ("race_window_rel_ms", [5.280, 5.640]),
            (
                "race",
                OrderedDict(
                    [
                        (
                            "contenders",
                            [
                                "nh3.offgas.ppm 186 over 90 cap",
                                "enc.kiln.rpm 1.8 with skin 742 under 780",
                            ],
                        ),
                        (
                            "semantics",
                            "NH3-first latches RPM clamp 1.8 -> 1.1; speed-first keeps 1.8 on a "
                            "'still under tube-skin cap' model.",
                        ),
                        (
                            "window_derivation",
                            "360 us = one UV NH3 slot versus the kiln-encoder publisher on this "
                            "APT calciner bus.",
                        ),
                        (
                            "order_evidence_note",
                            "Margin 180 us vs combined jitter 62 us (NH3 28 + RPM 34): 2.90x over "
                            "a 2.0x trust floor. Reversing order by < 180 us inside the 360 us "
                            "window would have kept 1.8 rpm; predicted next-sample 142 ppm "
                            "> 90 cap.",
                        ),
                    ]
                ),
            ),
            (
                "sensors",
                [
                    "off-gas UV NH3 cell, 2 kHz, 28 us jitter",
                    "kiln encoder + skin TC, 1 kHz, 34 us jitter",
                    "discharge-hood AE puck (context)",
                    "APT screw tach (context)",
                ],
            ),
            (
                "constraints",
                OrderedDict(
                    [
                        ("nh3_cap_ppm", 90.0),
                        ("observed_nh3_ppm", 186.0),
                        ("kiln_rpm", 1.8),
                        ("skin_C", 742.0),
                        ("skin_cap_C", 780.0),
                    ]
                ),
            ),
            (
                "episode_steps",
                [
                    "1. C-4 indexed on Tungstate-Keld TK-6; kiln 1.8 rpm; off-gas NH3 186 ppm.",
                    "2. Skin 742 C under 780 C cap; roast armed.",
                    "3. Encoder precursor at 1.180 ms.",
                    "4. Race window [5.280, 5.640] ms.",
                    "5. nh3.offgas.ppm 186 at 5.280 ms (winner).",
                    "6. enc.kiln.rpm 1.8 at 5.460 ms (loser by 180 us).",
                    "7. Gate at 5.980 ms: MODIFY clamp 1.8 -> 1.1 rpm.",
                    "8. After clamp NH3 68 ppm <= 90; skin still 742 C.",
                    "9. At 22.600 ms a tube-sheet leak dumps 0.4 t calcine.",
                    "10. 15 min hood isolate (abort_s=900); named un-netted loss.",
                ],
            ),
        ]
    )
    proposed = OrderedDict(
        [
            ("name", "cruise_kiln_rpm"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("kiln_rpm", 1.8),
                        ("nh3_ppm", 186.0),
                        ("skin_C", 742.0),
                    ]
                ),
            ),
            (
                "evidence",
                OrderedDict(
                    [
                        ("nh3_ppm", 186.0),
                        ("nh3_cap_ppm", 90.0),
                        ("predicted_unclamped_next_ppm", 142.0),
                        ("kiln_rpm", 1.8),
                        ("skin_C", 742.0),
                        ("skin_cap_C", 780.0),
                        ("race_margin_us", 180),
                        ("combined_jitter_us", 62),
                        ("abort_s", 900),
                    ]
                ),
            ),
            (
                "basis",
                "Planner proposes 1.8 rpm because skin 742 C is under 780, treating the "
                "186 ppm NH3 as a still-wet UV cell rather than an off-gas-cap miss.",
            ),
        ]
    )
    safety = OrderedDict(
        [
            ("decision", "MODIFY"),
            ("correctness", "correct"),
            (
                "rationale",
                "Off-gas NH3 186 ppm won by 180 us, so the roast is off-spec, not still a "
                "tube-skin story. Holding 1.8 rpm predicts next-sample 142 ppm > 90 cap. "
                "MODIFY: kiln 1.8 -> 1.1 rpm. Observed after clamp 68 ppm <= 90. A full REJECT "
                "is not indicated: a clean roast accepts 1.1 rpm.",
            ),
            (
                "constraint_checked",
                OrderedDict(
                    [
                        (
                            "nh3_ppm",
                            OrderedDict(
                                [
                                    ("cap", 90.0),
                                    ("observed", 186.0),
                                    ("predicted_unclamped_next", 142.0),
                                    ("clamped_kiln_rpm", 1.1),
                                    ("observed_after_clamp", 68.0),
                                ]
                            ),
                        ),
                        (
                            "order_evidence",
                            OrderedDict(
                                [
                                    ("margin_us", 180),
                                    ("combined_jitter_us", 62),
                                    ("ratio", 2.90),
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
            ("name", "clamped_kiln_rpm"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("kiln_rpm", 1.1),
                        ("nh3_ppm", 68.0),
                        ("skin_C", 742.0),
                    ]
                ),
            ),
            (
                "gate_effect",
                "MODIFY: kiln 1.8 -> 1.1 rpm. Process-correct vs the 90 ppm NH3 cap. "
                "Tube-sheet still leaks at 22.600 ms.",
            ),
        ]
    )
    future = OrderedDict(
        [
            (
                "summary",
                "Process-correct MODIFY held off-gas NH3 at 68 ppm. At 22.600 ms a tube-sheet "
                "leak already seated on the discharge hood dumped 0.4 t of calcine. Clamp "
                "reduced dump energy; it did not prevent the leak. Partnered negative: process "
                "heads stay honest; world loss is named, not netted.",
            ),
            (
                "state_delta",
                OrderedDict(
                    [
                        ("offgas", "clamp executed; peak 68 ppm <= 90 cap"),
                        ("tube_sheet", "leaked at 22.600 ms; 0.4 t calcine"),
                        ("repair", "15 min hood isolate (abort_s=900)"),
                        ("mission", "TK-6 roast incomplete this circuit"),
                    ]
                ),
            ),
            (
                "surprises",
                [
                    "Neither off-gas NH3 nor kiln encoder predicted the seated tube-sheet leak; ae.tube.leak is a new channel at 22.600 ms, 16.620 ms after the gate, still inside the 42 ms raster.",
                    "Delayed (abort_s=900): 15 min hood isolate. Named un-netted loss, not folded into task_progress.",
                ],
            ),
            (
                "un_netted_loss",
                "15 min hood isolate after the tube-sheet leak. Safety head -0.60 prices the dump; "
                "task_progress stays +0.32 because the RPM clamp completed under the 90 ppm "
                "cap. World loss is named here, not subtracted from process heads.",
            ),
            (
                "race_result",
                OrderedDict(
                    [
                        ("winner", "nh3.offgas.ppm (5.280 ms, 186 ppm)"),
                        ("loser", "enc.kiln.rpm (5.460 ms, 1.8 rpm)"),
                        ("margin_us", 180),
                        (
                            "counterfactual_if_reversed",
                            "Speed-first by < 180 us inside the 360 us window would have kept "
                            "1.8 rpm; predicted next-sample 142 ppm would have missed the 90 "
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
                "Safety collapses at the 22.600 ms tube-sheet leak (tick t_us=22600), inside the 42 ms "
                "raster. The correct MODIFY at 5.980 ms is in the same excerpt. Do not put "
                "inflection on the abort_s=900 isolation tick.",
            ),
            ("delayed_surprise_s", 900),
        ]
    )
    spikes = [
        spike("enc.kiln.rpm", 1.180, 0.41),
        spike("nh3.offgas.ppm", 2.112, 0.58),
        spike("enc.kiln.rpm", 3.400, 0.50),
        spike("nh3.offgas.ppm", 5.280, 1.31),
        spike("enc.kiln.rpm", 5.460, 1.12),
        spike("ctrl.gate", 5.980, 0.97),
        spike("nh3.offgas.ppm", 8.100, 0.82),
        spike("enc.kiln.rpm", 10.400, 0.64),
        spike("ctrl.gate", 14.200, 0.86),
        spike("ae.tube.leak", 22.600, 1.48),
        spike("ae.tube.leak", 24.100, 0.93),
        spike("enc.kiln.rpm", 30.200, 0.40),
        spike("nh3.offgas.ppm", 36.400, 0.55),
    ]
    dw = 0.36
    ras = raster_core(
        42,
        76,
        26,
        83,
        routing(
            "thalamic-relay.apt-nh3",
            "spikenaut.policy.rpm-clamp",
            [
                ("relay.nh3.offgas", "policy.rpm_clamp", 0.68),
                ("relay.enc.kiln", "policy.speed_hold", 0.29),
                ("relay.ae.tube", "policy.rpm_clamp", -0.42),
            ],
            "noradrenaline",
            0.04,
            "surprise-gated pre_post_stdp; NA at NH3 win (5.280 ms) opens a 42 ms eligibility "
            "trace that still covers the 22.600 ms tube-sheet leak",
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
                    pop_budget("rpm_clamp", 50, 0.50, 220.0, dw),
                    pop_budget("speed_hold", 40, 0.80, 50.0, dw),
                    pop("leak_veto", 24, 0.75),
                ],
            ),
        ]
    )
    return OrderedDict(
        [
            ("id", "ttf-r65-341"),
            (
                "title",
                "Tungstate-Keld TK-6 / Calciner C-4: off-gas NH3 beats kiln RPM by 180 us; "
                "correct MODIFY still eats an in-window tube-sheet leak (partnered negative "
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
                    "hood isolate (abort_s=900) is not netted into task_progress.",
                ),
            ),
            ("raster", ras),
            ("gate_snn", gate),
            (
                "meta",
                meta_block(
                    "wolfram-APT-calciner",
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
                    "15 min hood isolate.",
                    1,
                ),
            ),
        ]
    )


def record_342():
    ticks = [
        tick(2160, -0.02, -0.02, -0.02, -0.01, 0.01),
        tick(5400, -0.04, -0.04, -0.03, -0.02, 0.01),
        tick(5580, -0.04, -0.04, -0.03, -0.02, 0.01),
        tick(5920, -0.08, -0.10, -0.06, -0.03, 0.02),
        tick(6260, -0.02, -0.02, -0.02, -0.01, 0.01),
        tick(720000000, -0.02, -0.02, -0.02, -0.01, 0.00),
    ]
    spikes = [
        spike("enc.steam.tph", 1.080, 0.42),
        spike("tc.ka.live", 2.160, 0.57),
        spike("enc.steam.tph", 3.400, 0.49),
        spike("tc.ka.live", 5.400, 1.29),
        spike("tc.kb.idle", 5.580, 1.10),
        spike("ctrl.gate", 5.920, 0.96),
        spike("tc.ka.live", 8.200, 0.80),
        spike("enc.steam.tph", 10.200, 0.63),
        spike("ctrl.gate", 12.400, 0.84),
        spike("tc.ka.live", 16.400, 0.41),
        spike("tc.kb.idle", 22.100, 0.54),
        spike("tc.ka.live", 26.200, 0.38),
    ]
    excerpt = independent_excerpt(65342, 88, 28000, 14, spike_avoid_us(spikes))
    state = OrderedDict(
        [
            (
                "description",
                "Beckmann kettle K-A (LIVE) at Oxime-Clough OC-4 reads jacket 168 C over a 155 C "
                "cap; parallel kettle K-B is IDLE at 92 C, yet the mimic still has K-B selected. "
                "Live-first should cut K-A steam 3.6 -> 1.1 t/h; a weak supervisor clamps the "
                "idle string instead.",
            ),
            ("domain", "caprolactam-beckmann"),
            ("sim_or_real", "designed"),
            (
                "goal",
                "Finish the OC-4 rearrangement with live jacket <= 155 C, leave oxime feed at "
                "the planned 9.0 t/h, and keep steam on the LIVE string only.",
            ),
            ("t0_us", 1756850400000342),
            ("gate_latency_us", 520),
            ("race_window_us", 340),
            ("race_window_rel_ms", [5.400, 5.740]),
            (
                "race",
                OrderedDict(
                    [
                        (
                            "contenders",
                            [
                                "tc.ka.live 168 C on kettle K-A LIVE",
                                "tc.kb.idle 92 C on kettle K-B IDLE",
                            ],
                        ),
                        (
                            "semantics",
                            "Live-first should latch a timely steam cut 3.6 -> 1.1 t/h on K-A; "
                            "idle-first is a false 'selected-train' clamp of the parked K-B bank.",
                        ),
                        (
                            "window_derivation",
                            "340 us = one live-jacket slot versus the idle-bank publisher on "
                            "this Beckmann dual-string PLC bus.",
                        ),
                        (
                            "order_evidence_note",
                            "Margin 180 us vs combined jitter 60 us (live 28 + idle 32). Order is "
                            "correctly live-first. The error is which string is actuated, not "
                            "the magnitude: the mimic still points at IDLE K-B.",
                        ),
                    ]
                ),
            ),
            (
                "sensors",
                [
                    "live jacket TC on K-A, 2 kHz, 28 us jitter, tag=KA_JKT.LIVE status=LIVE",
                    "idle jacket TC on K-B, 1 kHz, 32 us jitter, tag=KB_JKT.IDLE status=IDLE",
                    "steam FT (context)",
                    "oxime feed FT (context)",
                ],
            ),
            (
                "constraints",
                OrderedDict(
                    [
                        ("jacket_cap_C", 155.0),
                        ("live_C", 168.0),
                        ("idle_C", 92.0),
                        ("live_string", "K-A"),
                        ("idle_string", "K-B"),
                        ("selected_string_tag", "K-B"),
                        ("oxime_tph", 9.0),
                    ]
                ),
            ),
            (
                "episode_steps",
                [
                    "1. K-A LIVE already rearranging; jacket 168 C; oxime 9.0 t/h.",
                    "2. K-B IDLE at 92 C; mimic selected_string_tag=K-B.",
                    "3. Steam precursor at 1.080 ms.",
                    "4. Race window [5.400, 5.740] ms.",
                    "5. tc.ka.live 168 C at 5.400 ms (winner).",
                    "6. tc.kb.idle 92 C at 5.580 ms (loser by 180 us).",
                    "7. Gate at 5.920 ms: WRONG-MODIFY binds idle K-B steam cut.",
                    "8. K-B steam 3.6 -> 1.1 t/h; K-A left at 3.6 t/h; live peaks 176 C.",
                    "9. Oxime dump on K-A; K-B never needed steam.",
                    "10. Delayed (abort_s=720): 12 min kettle dump while K-A is quenched.",
                ],
            ),
        ]
    )
    proposed = OrderedDict(
        [
            ("name", "cruise_both_strings"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("steam_tph", 3.6),
                        ("target_string", "K-A"),
                        ("bind_idle_string", False),
                        ("oxime_tph", 9.0),
                    ]
                ),
            ),
            (
                "evidence",
                OrderedDict(
                    [
                        ("live_C", 168.0),
                        ("jacket_cap_C", 155.0),
                        ("idle_C", 92.0),
                        ("live_string", "K-A"),
                        ("idle_string", "K-B"),
                        ("selected_string_tag", "K-B"),
                        ("live_status", "LIVE"),
                        ("idle_status", "IDLE"),
                        ("oxime_tph", 9.0),
                        ("t_gate_us", 5920),
                        ("correct_steam_tph", 1.1),
                        ("correct_target_string", "K-A"),
                        ("race_margin_us", 180),
                        ("combined_jitter_us", 60),
                        ("abort_s", 720),
                    ]
                ),
            ),
            (
                "basis",
                "Planner proposes continuing 3.6 t/h steam on the selected mimic train: idle "
                "K-B 92 C is under the 155 C cap, so the 168 C live jacket is treated as a "
                "shadow of the parked bank.",
            ),
        ]
    )
    safety = OrderedDict(
        [
            ("decision", "MODIFY"),
            ("correctness", "incorrect"),
            (
                "rationale",
                "Jacket 168 C exceeds the 155 C cap (true). Apply the 1.1 t/h steam cut on the "
                "selected mimic train K-B, because KB_JKT.IDLE is the highlighted string. Leave "
                "live K-A at cruise.",
            ),
            (
                "constraint_checked",
                OrderedDict(
                    [
                        (
                            "jacket_C",
                            OrderedDict(
                                [
                                    ("cap", 155.0),
                                    ("live", 168.0),
                                    ("idle", 92.0),
                                    ("executed_string", "K-B"),
                                    ("correct_string", "K-A"),
                                    ("correct_steam_tph", 1.1),
                                ]
                            ),
                        ),
                        (
                            "string_bind",
                            OrderedDict(
                                [
                                    ("t_gate_us", 5920),
                                    ("bind_idle_string", True),
                                    ("selected_string_tag", "K-B"),
                                    ("wrong_string", True),
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
            ("name", "steam_cut_idle_string"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("steam_tph", 1.1),
                        ("target_string", "K-B"),
                        ("bind_idle_string", True),
                        ("oxime_tph", 9.0),
                    ]
                ),
            ),
            (
                "gate_effect",
                "MODIFY (incorrect / wrong-string idle-bank): 1.1 t/h steam cut applied to IDLE "
                "K-B while LIVE K-A stays at 3.6 t/h. Routing relay.tc.idle -> policy.idle_clamp; "
                "no positive weight to policy.live_clamp.",
            ),
        ]
    )
    future = OrderedDict(
        [
            (
                "summary",
                "Wrong-MODIFY clamped the idle Beckmann string. Live 168 C was over the 155 C "
                "cap at t_gate; idle 92 C was a parked bank. Peak 176 C dumped K-A. 12 min "
                "kettle dump (abort_s=720). Correct gate was MODIFY steam 3.6 -> 1.1 t/h on "
                "LIVE K-A at t_gate_us=5920.",
            ),
            (
                "state_delta",
                OrderedDict(
                    [
                        ("live_kettle", "K-A left at 3.6 t/h steam; peak 176 > 155 cap"),
                        ("idle_kettle", "K-B steam cut 3.6 -> 1.1 t/h with no duty"),
                        ("dump", "12 min oxime dump, K-A quench"),
                        ("mission", "rearrangement deferred"),
                    ]
                ),
            ),
            (
                "surprises",
                [
                    "Live-first was the correct order and the temperature number was over cap; the MODIFY spent that win on the idle parallel bank.",
                    "Delayed (abort_s=720): OC-4 holds 12 min while K-A is dumped and recharged; next batch 14 min late.",
                ],
            ),
            (
                "recovery",
                OrderedDict(
                    [
                        (
                            "correct_gate",
                            "MODIFY steam 3.6 -> 1.1 t/h on LIVE K-A at t_gate_us=5920; bind_idle_string=false; leave oxime at 9.0 t/h.",
                        ),
                        ("correct_actuator", "K-A_steam"),
                        ("wrong_string", "K-B_idle"),
                        ("t_gate_us", 5920),
                        (
                            "wrong_edit_applied",
                            OrderedDict(
                                [
                                    ("steam_tph", 1.1),
                                    ("target_string", "K-B"),
                                    ("bind_idle_string", True),
                                ]
                            ),
                        ),
                        (
                            "cost",
                            "12 min kettle dump (task/efficiency); live jacket peaked 176 C while steam was spent on the idle bank (safety near-miss of a correct-magnitude wrong-string clamp).",
                        ),
                    ]
                ),
            ),
            (
                "race_result",
                OrderedDict(
                    [
                        ("winner", "tc.ka.live (5.400 ms, 168 C LIVE)"),
                        ("loser", "tc.kb.idle (5.580 ms, 92 C IDLE)"),
                        ("margin_us", 180),
                        (
                            "counterfactual_if_reversed",
                            "Idle-first by < 180 us would still be a parked 92 C under the 155 C "
                            "cap; a correct gate binds tc.ka.live to policy.live_clamp at t_gate "
                            "either way. The wrong MODIFY spent the live win on the idle string.",
                        ),
                    ]
                ),
            ),
            ("reward_inflection_t_us", 5920),
            (
                "reward_inflection_note",
                "Task, safety, and efficiency drop at the idle-string bind (5.920 ms, tick 4). "
                "The 12 min kettle dump is delayed surprise, not the inflection.",
            ),
            ("delayed_surprise_s", 720),
        ]
    )
    dw = 0.34
    ras = raster_core(
        28,
        88,
        34,
        84,
        routing(
            "thalamic-relay.beckmann-idle",
            "spikenaut.policy.idle-clamp",
            [
                ("relay.tc.idle", "policy.idle_clamp", 0.74),
                ("relay.tc.live", "policy.idle_clamp", 0.21),
            ],
            "acetylcholine",
            0.08,
            "string_cap_stdp; ACh tags the (wrong) idle_clamp bind at the live win",
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
                    pop_budget("idle_clamp", 48, 0.45, 300.0, dw),
                    pop("live_clamp", 48, 0.90),
                    pop("idle_veto", 20, 0.80),
                ],
            ),
        ]
    )
    return OrderedDict(
        [
            ("id", "ttf-r65-342"),
            (
                "title",
                "WRONG-MODIFY at Oxime-Clough OC-4 / Kettle K-A: live 168 C read correctly; "
                "1.1 t/h steam cut applied to IDLE K-B (wrong-string / idle-bank)",
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
                    "Wrong-modify / wrong-string idle-bank. Sidecar arithmetic 168 > 155 on live "
                    "is true; MODIFY bound to idle_clamp. total -0.68 = -0.22 + -0.24 + -0.18 + -0.10 + 0.06.",
                ),
            ),
            ("raster", ras),
            ("gate_snn", gate),
            (
                "meta",
                meta_block(
                    "caprolactam-beckmann",
                    [
                        "modify",
                        "wrong-gate",
                        "wrong-string",
                        "idle-bank",
                        "sidecar-convictable",
                        "designed",
                    ],
                    "Teaches a probe that a correct live-first race can still be a wrong gate "
                    "when the MODIFY clamps the idle parallel bank. Convictable from LIVE/IDLE "
                    "status, selected_string_tag, and routing without Beckmann physics.",
                    2,
                    supervisor_error_type="wrong-modify",
                ),
            ),
        ]
    )


def record_343():
    ticks = [
        tick(2736, 0.01, 0.04, 0.01, 0.01, 0.01),
        tick(6840, 0.02, 0.08, 0.02, 0.02, 0.01),
        tick(7020, 0.01, 0.06, 0.02, 0.01, 0.01),
        tick(7640, 0.04, 0.16, 0.04, 0.04, 0.02),
        tick(7960, 0.01, 0.05, 0.02, 0.01, 0.01),
        tick(480000000, 0.01, 0.03, 0.01, 0.01, 0.00),
    ]
    spikes = [
        spike("pt.o2.bar", 1.360, 0.40),
        spike("ae.ox.pps", 2.736, 0.56),
        spike("pt.o2.bar", 4.100, 0.48),
        spike("ae.ox.pps", 6.840, 1.34),
        spike("pt.o2.bar", 7.020, 1.11),
        spike("ctrl.gate", 7.640, 0.98),
        spike("ae.ox.pps", 10.400, 0.81),
        spike("pt.o2.bar", 14.800, 0.62),
        spike("ctrl.gate", 18.200, 0.84),
        spike("ae.ox.pps", 28.400, 0.52),
        spike("pt.o2.bar", 36.100, 0.39),
        spike("ae.ox.pps", 42.200, 0.44),
    ]
    excerpt = independent_excerpt(65343, 120, 46000, 15, spike_avoid_us(spikes))
    state = OrderedDict(
        [
            (
                "description",
                "HIL oxidizer O-2 at Ilmenite-Naze IN-HIL hears burner AE at 52 pps while the "
                "oxygen header remains 8.4 bar under a 10.0 bar cap. AE-first holds TiCl4; "
                "header-first would dispatch 18 t/h because the O2 ram looks legal. The HIL "
                "burner mockup is the authority, not the chloride-process floor.",
            ),
            ("domain", "chloride-TiO2-oxidizer"),
            ("sim_or_real", "hil"),
            (
                "goal",
                "Keep O-2 from dispatching a growling burner while oxygen header pressure remains "
                "under its own cap.",
            ),
            ("t0_us", 1756850400000343),
            ("gate_latency_us", 800),
            ("race_window_us", 320),
            ("race_window_rel_ms", [6.840, 7.160]),
            (
                "race",
                OrderedDict(
                    [
                        (
                            "contenders",
                            [
                                "ae.ox.pps 52 over 14 cap",
                                "pt.o2.bar 8.4 under 10.0 cap",
                            ],
                        ),
                        (
                            "semantics",
                            "AE-first latches hold; header-first dispatches 18 t/h TiCl4 on a "
                            "'O2 still legal' model.",
                        ),
                        (
                            "window_derivation",
                            "320 us = one AE puck slot versus the oxygen-PT publisher on this "
                            "HIL oxidizer bus.",
                        ),
                        (
                            "order_evidence_note",
                            "Margin 180 us vs combined jitter 58 us (AE 26 + O2 32): 3.10x over "
                            "a 2.0x trust floor. Reversing order by < 180 us inside the 320 us "
                            "window would have dispatched 18 t/h into a growling burner.",
                        ),
                    ]
                ),
            ),
            (
                "sensors",
                [
                    "burner AE puck, 50 kHz, 26 us jitter",
                    "oxygen header PT, 1 kHz, 32 us jitter",
                    "TiCl4 Coriolis (context)",
                    "flame IR (context)",
                ],
            ),
            (
                "constraints",
                OrderedDict(
                    [
                        ("ae_cap_pps", 14.0),
                        ("observed_ae_pps", 52.0),
                        ("o2_bar", 8.4),
                        ("o2_cap_bar", 10.0),
                        ("proposed_ticl4_tph", 18.0),
                    ]
                ),
            ),
            (
                "episode_steps",
                [
                    "1. O-2 HIL indexed; 18 t/h TiCl4 armed.",
                    "2. Oxygen 8.4 bar under 10.0; AE 52 pps over 14.",
                    "3. O2 precursor at 1.360 ms.",
                    "4. Race window [6.840, 7.160] ms.",
                    "5. ae.ox.pps 52 at 6.840 ms (winner).",
                    "6. pt.o2.bar 8.4 at 7.020 ms (loser by 180 us).",
                    "7. Gate at 7.640 ms: REJECT hold, do not dispatch.",
                    "8. Feed 0 t/h; oxygen left at 8.4 bar.",
                    "9. Burner inspected on the HIL stand.",
                    "10. Delayed (abort_s=480): 8 min oxidizer reset.",
                ],
            ),
        ]
    )
    proposed = OrderedDict(
        [
            ("name", "dispatch_ticl4"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("ticl4_tph", 18.0),
                        ("hold", False),
                        ("o2_bar", 8.4),
                    ]
                ),
            ),
            (
                "evidence",
                OrderedDict(
                    [
                        ("ae_pps", 52.0),
                        ("ae_cap_pps", 14.0),
                        ("o2_bar", 8.4),
                        ("o2_cap_bar", 10.0),
                        ("race_margin_us", 180),
                        ("combined_jitter_us", 58),
                        ("abort_s", 480),
                    ]
                ),
            ),
            (
                "basis",
                "Planner proposes 18 t/h TiCl4 because oxygen 8.4 bar is under 10.0, treating the "
                "52 pps AE as igniter hash rather than a growling burner.",
            ),
        ]
    )
    safety = OrderedDict(
        [
            ("decision", "REJECT"),
            ("correctness", "correct"),
            (
                "rationale",
                "Burner AE 52 pps won by 180 us, so the oxidizer is growling, not still an "
                "oxygen-header story. Oxygen 8.4 bar is under 10.0 and does not authorize dispatch. "
                "REJECT: hold feed 18 -> 0 t/h. A MODIFY that only trims O2 would leave the growl.",
            ),
            (
                "constraint_checked",
                OrderedDict(
                    [
                        (
                            "ae_pps",
                            OrderedDict(
                                [
                                    ("cap", 14.0),
                                    ("observed", 52.0),
                                    ("executed_ticl4_tph", 0.0),
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
            ("name", "hold_oxidizer"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("ticl4_tph", 0.0),
                        ("hold", True),
                        ("o2_bar", 8.4),
                    ]
                ),
            ),
            (
                "gate_effect",
                "REJECT: TiCl4 18 -> 0 t/h. Oxygen left at 8.4 bar under its own cap.",
            ),
        ]
    )
    future = OrderedDict(
        [
            (
                "summary",
                "Correct REJECT held O-2. AE 52 pps beat oxygen 8.4 bar by 180 us. Header was "
                "legal; the burner was not. 8 min oxidizer reset (abort_s=480) is delayed survey, "
                "not a process miss.",
            ),
            (
                "state_delta",
                OrderedDict(
                    [
                        ("feed", "held at 0 t/h"),
                        ("oxygen", "left 8.4 bar < 10.0 cap"),
                        ("burner", "8 min oxidizer reset (abort_s=480)"),
                        ("mission", "HIL TiCl4 not dispatched"),
                    ]
                ),
            ),
            (
                "surprises",
                [
                    "Oxygen PT never crossed its cap; AE was the only over-cap channel.",
                    "Delayed (abort_s=480): 8 min oxidizer reset on the HIL stand.",
                ],
            ),
            (
                "race_result",
                OrderedDict(
                    [
                        ("winner", "ae.ox.pps (6.840 ms, 52 pps)"),
                        ("loser", "pt.o2.bar (7.020 ms, 8.4 bar)"),
                        ("margin_us", 180),
                        (
                            "counterfactual_if_reversed",
                            "Header-first by < 180 us inside the 320 us window would have dispatched "
                            "18 t/h into a growling burner. The REJECT is still the correct gate.",
                        ),
                    ]
                ),
            ),
            ("reward_inflection_t_us", 7640),
            (
                "reward_inflection_note",
                "Safety and task rise at the correct REJECT (7.640 ms, tick 4). The 8 min oxidizer "
                "reset is delayed surprise, not the inflection.",
            ),
            ("delayed_surprise_s", 480),
        ]
    )
    dw = 0.32
    ras = raster_core(
        46,
        120,
        20,
        110,
        routing(
            "thalamic-relay.ox-ae",
            "spikenaut.policy.ox-hold",
            [
                ("relay.ae.ox", "policy.ox_hold", 0.70),
                ("relay.pt.o2", "policy.o2_go", 0.24),
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
                    pop_budget("ox_hold", 56, 0.45, 280.0, dw),
                    pop("o2_go", 40, 0.90),
                    pop("ae_veto", 24, 0.70),
                ],
            ),
        ]
    )
    return OrderedDict(
        [
            ("id", "ttf-r65-343"),
            (
                "title",
                "Ilmenite-Naze IN-HIL / Oxidizer O-2: burner AE 52 pps beats oxygen 8.4 bar by "
                "180 us; correct REJECT holds TiCl4",
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
                    "Correct REJECT. AE 52 > 14 cap beats legal oxygen header. "
                    "total +0.80 = 0.10 + 0.42 + 0.12 + 0.10 + 0.06.",
                ),
            ),
            ("raster", ras),
            ("gate_snn", gate),
            (
                "meta",
                meta_block(
                    "chloride-TiO2-oxidizer",
                    [
                        "reject",
                        "hil",
                        "ae-vs-o2",
                        "growling-burner",
                        "tick6-sidecar-bound",
                    ],
                    "Teaches that a legal oxygen header can lose to burner AE inside a 320 us "
                    "window; reversing 180 us would have dispatched a growling oxidizer.",
                    3,
                ),
            ),
        ]
    )


def record_344():
    ticks = [
        tick(2880, 0.06, 0.04, 0.02, 0.02, 0.01),
        tick(7200, 0.08, 0.06, 0.04, 0.02, 0.02),
        tick(7380, 0.06, 0.04, 0.03, 0.02, 0.01),
        tick(7840, 0.12, 0.08, 0.05, 0.04, 0.02),
        tick(8200, 0.04, 0.04, 0.02, 0.01, 0.01),
        tick(360000000, 0.04, 0.02, 0.02, 0.01, 0.01),
    ]
    spikes = [
        spike("tc.bed.C", 1.200, 0.40),
        spike("dens.cat.frac", 2.880, 0.55),
        spike("tc.bed.C", 4.400, 0.48),
        spike("dens.cat.frac", 7.200, 1.26),
        spike("tc.bed.C", 7.380, 1.08),
        spike("ctrl.gate", 7.840, 0.95),
        spike("dens.cat.frac", 11.200, 0.78),
        spike("tc.bed.C", 14.800, 0.60),
        spike("ctrl.gate", 18.400, 0.82),
        spike("dens.cat.frac", 22.600, 0.50),
        spike("tc.bed.C", 26.200, 0.38),
    ]
    excerpt = independent_excerpt(65344, 48, 28000, 12, spike_avoid_us(spikes))
    params = OrderedDict(
        [
            ("recycle_tph", 14.0),
            ("cat_frac", 0.62),
            ("bed_C", 418.0),
            ("hold", False),
        ]
    )
    state = OrderedDict(
        [
            (
                "description",
                "Ebullated recycle cup R-3 at Ebullate-Pike EP-7 already holds catalyst at 0.62 "
                "volume fraction under a 0.78 trip, with bed 418 C under 440. Holdup-first accepts "
                "the 14.0 t/h recycle; bed-first would have rejected a legal ebullation on a "
                "'still climbing' model.",
            ),
            ("domain", "ebullated-hydrocracker"),
            ("sim_or_real", "simulated"),
            (
                "goal",
                "Finish the EP-7 recycle with catalyst holdup <= 0.78 and bed <= 440 C.",
            ),
            ("t0_us", 1756850400000344),
            ("gate_latency_us", 640),
            ("race_window_us", 360),
            ("race_window_rel_ms", [7.200, 7.560]),
            (
                "race",
                OrderedDict(
                    [
                        (
                            "contenders",
                            [
                                "dens.cat.frac 0.62 under 0.78 trip",
                                "tc.bed.C 418 under 440 cap",
                            ],
                        ),
                        (
                            "semantics",
                            "Holdup-first confirms the already-legal 14.0 t/h recycle; bed-first "
                            "would have treated the densitometer as a climb echo and looked for an extra hold.",
                        ),
                        (
                            "window_derivation",
                            "360 us = one nuclear-density slot versus the bed-TC publisher "
                            "on this simulated ebullated-bed bus.",
                        ),
                        (
                            "order_evidence_note",
                            "Margin 180 us vs combined jitter 58 us (dens 26 + TC 32): 3.10x over "
                            "a 2.0x trust floor. Reversing order by < 180 us would not make the "
                            "proposed recycle illegal; it would only have delayed confirmation.",
                        ),
                    ]
                ),
            ),
            (
                "sensors",
                [
                    "nuclear densitometer on recycle cup, 26 us jitter",
                    "bed TC well, 32 us jitter",
                    "hydrogen FT (context)",
                    "delta-P bed (context)",
                ],
            ),
            (
                "constraints",
                OrderedDict(
                    [
                        ("cat_cap_frac", 0.78),
                        ("observed_cat_frac", 0.62),
                        ("bed_cap_C", 440.0),
                        ("observed_bed_C", 418.0),
                        ("h2_partial_bar", 138.0),
                        ("h2_cap_bar", 160.0),
                        ("proposed_recycle_tph", 14.0),
                    ]
                ),
            ),
            (
                "episode_steps",
                [
                    "1. R-3 indexed on Ebullate-Pike EP-7; 14.0 t/h recycle armed.",
                    "2. Caps: holdup 0.78, bed 440 C, H2 160 bar.",
                    "3. Bed-TC precursor at 1.200 ms.",
                    "4. Race window [7.200, 7.560] ms.",
                    "5. dens.cat.frac 0.62 at 7.200 ms (winner).",
                    "6. tc.bed.C 418 at 7.380 ms (loser by 180 us).",
                    "7. Gate at 7.840 ms: ACCEPT 14.0 t/h already legal.",
                    "8. Recycle continues; no extra hold.",
                    "9. 6 min survey confirms holdup still under 0.78.",
                    "10. QA: ACCEPT params identical to proposed.",
                ],
            ),
        ]
    )
    proposed = OrderedDict(
        [
            ("name", "recycle_14"),
            ("parameters", params),
            (
                "evidence",
                OrderedDict(
                    [
                        ("cat_frac", 0.62),
                        ("cat_cap_frac", 0.78),
                        ("bed_C", 418.0),
                        ("bed_cap_C", 440.0),
                        ("h2_partial_bar", 138.0),
                        ("h2_cap_bar", 160.0),
                        ("recycle_tph", 14.0),
                        ("race_margin_us", 180),
                        ("combined_jitter_us", 58),
                        ("survey_s", 360),
                    ]
                ),
            ),
            (
                "basis",
                "Planner proposes a 14.0 t/h recycle because holdup 0.62 is under 0.78 and bed "
                "418 C is under 440 C.",
            ),
        ]
    )
    safety = OrderedDict(
        [
            ("decision", "ACCEPT"),
            ("correctness", "correct"),
            (
                "rationale",
                "Catalyst holdup 0.62 won by 180 us and is under 0.78. Bed 418 C is under "
                "440 C. Hydrogen 138 bar is under 160. ACCEPT the already-legal recycle.",
            ),
            (
                "constraint_checked",
                OrderedDict(
                    [
                        (
                            "cat_frac",
                            OrderedDict(
                                [
                                    ("cap", 0.78),
                                    ("observed", 0.62),
                                    ("executed_recycle_tph", 14.0),
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
            ("name", "recycle_14"),
            ("parameters", OrderedDict(params.items())),
            (
                "gate_effect",
                "ACCEPT: 14.0 t/h recycle and 0.62 holdup unchanged. Routing relay.dens.cat -> "
                "policy.recyc_go.",
            ),
        ]
    )
    future = OrderedDict(
        [
            (
                "summary",
                "Correct ACCEPT left R-3 on a 14.0 t/h / 0.62 holdup recycle. Bed-TC hitch did not "
                "justify a hold. 6 min survey confirmed holdup still under 0.78.",
            ),
            (
                "state_delta",
                OrderedDict(
                    [
                        ("recycle", "still 14.0 t/h"),
                        ("holdup", "0.62 under 0.78 trip"),
                        ("bed", "418 C under 440"),
                        ("hold", "none applied"),
                    ]
                ),
            ),
            (
                "surprises",
                [
                    "Bed TC 418 C hitch is residual, not a runaway trip.",
                    "Delayed (survey_s=360): 6 min survey restacks R-3 without a recovery hold.",
                ],
            ),
            (
                "race_result",
                OrderedDict(
                    [
                        ("winner", "dens.cat.frac (7.200 ms, 0.62)"),
                        ("loser", "tc.bed.C (7.380 ms, 418 C)"),
                        ("margin_us", 180),
                        (
                            "counterfactual_if_reversed",
                            "Bed-first by < 180 us would only delay confirmation. The recycle stays "
                            "legal either way; ACCEPT is still required.",
                        ),
                    ]
                ),
            ),
            ("reward_inflection_t_us", 7840),
            (
                "reward_inflection_note",
                "Task credit lands at the ACCEPT (7.840 ms, tick 4). Survey is delayed surprise.",
            ),
            ("delayed_surprise_s", 360),
        ]
    )
    dw = 0.36
    ras = raster_core(
        28,
        48,
        42,
        56,
        routing(
            "thalamic-relay.cat-dens",
            "spikenaut.policy.recyc-go",
            [
                ("relay.dens.cat", "policy.recyc_go", 0.68),
                ("relay.tc.bed", "policy.bed_hold", 0.21),
            ],
            "serotonin",
            0.07,
            "legal_recyc_stdp; 5-HT tags the recyc_go bind at the densitometer win",
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
                    pop_budget("recyc_go", 40, 0.45, 250.0, dw),
                    pop("bed_hold", 32, 0.90),
                    pop("cat_veto", 16, 0.80),
                ],
            ),
        ]
    )
    return OrderedDict(
        [
            ("id", "ttf-r65-344"),
            (
                "title",
                "Ebullate-Pike EP-7 / Recycle cup R-3: catalyst holdup 0.62 beats bed 418 C "
                "by 180 us; ACCEPT already-legal 14.0 t/h recycle",
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
                    "Correct ACCEPT of an already-legal ebullated recycle. total +1.06 = "
                    "0.40 + 0.28 + 0.18 + 0.12 + 0.08.",
                ),
            ),
            ("raster", ras),
            ("gate_snn", gate),
            (
                "meta",
                meta_block(
                    "ebullated-hydrocracker",
                    [
                        "accept",
                        "already-legal",
                        "simulated-ebullated-loop",
                        "dens-vs-tc",
                        "sidecar-convictable",
                        "simulated",
                    ],
                    "Teaches that a catalyst densitometer under trip can confirm an already-legal "
                    "recycle without a bed-TC hitch becoming a hold.",
                    4,
                ),
            ),
        ]
    )


def record_345():
    ticks = [
        tick(2016, 0.06, 0.04, 0.03, 0.02, 0.01),
        tick(5040, 0.10, 0.06, 0.04, 0.02, 0.02),
        tick(5200, 0.06, 0.04, 0.03, 0.02, 0.01),
        tick(5640, 0.12, 0.08, 0.05, 0.04, 0.02),
        tick(5920, 0.06, 0.05, 0.03, 0.01, 0.01),
        tick(240000000, 0.04, 0.03, 0.02, 0.01, 0.01),
    ]
    spikes = [
        spike("ft.n2ar.ratio", 0.980, 0.41),
        spike("gc.c.wt", 2.016, 0.60),
        spike("ft.n2ar.ratio", 3.200, 0.51),
        spike("gc.c.wt", 5.040, 1.30),
        spike("ft.n2ar.ratio", 5.200, 1.12),
        spike("ctrl.gate", 5.640, 0.97),
        spike("gc.c.wt", 8.100, 0.78),
        spike("ft.n2ar.ratio", 12.400, 0.62),
        spike("ctrl.gate", 16.200, 0.85),
        spike("gc.c.wt", 20.400, 0.54),
        spike("ft.n2ar.ratio", 22.800, 0.43),
    ]
    excerpt = independent_excerpt(65345, 80, 24000, 12, spike_avoid_us(spikes))
    params = OrderedDict(
        [
            ("ar_nm3_min", 8.0),
            ("c_wt_pct", 0.042),
            ("hold", False),
        ]
    )
    state = OrderedDict(
        [
            (
                "description",
                "AOD vessel V-6 at Decarb-Haugh DH-2 is already at 0.042 wt percent carbon under "
                "a 0.08 cap, argon-nitrogen ratio 0.32 under 0.50. Carbon-first accepts the 8.0 "
                "Nm3/min Ar blow; ratio-first would have rejected a legal decarb on a 'still "
                "diluting' model.",
            ),
            ("domain", "aod-converter"),
            ("sim_or_real", "designed"),
            (
                "goal",
                "Run V-6 at 8.0 Nm3/min Ar, keep C <= 0.08 wt percent and N2/Ar <= 0.50, and "
                "leave the heat on schedule.",
            ),
            ("t0_us", 1756850400000345),
            ("gate_latency_us", 600),
            ("race_window_us", 280),
            ("race_window_rel_ms", [5.040, 5.320]),
            (
                "race",
                OrderedDict(
                    [
                        (
                            "contenders",
                            [
                                "gc.c.wt 0.042 under 0.08 cap",
                                "ft.n2ar.ratio 0.32 under 0.50 cap",
                            ],
                        ),
                        (
                            "semantics",
                            "Carbon-first confirms the already-legal 8.0 Nm3/min Ar blow; ratio-first "
                            "would have treated the GC as a hitch echo and looked for an extra hold.",
                        ),
                        (
                            "window_derivation",
                            "280 us = one off-gas GC slot versus the N2/Ar ratio publisher on this "
                            "AOD converter bus.",
                        ),
                        (
                            "order_evidence_note",
                            "Margin 160 us vs combined jitter 52 us (GC 22 + ratio 30): 3.08x over "
                            "a 2.0x trust floor. Reversing order by < 160 us inside the 280 us "
                            "window would have REJECTED an already-legal Ar blow.",
                        ),
                    ]
                ),
            ),
            (
                "sensors",
                [
                    "off-gas carbon GC, 2 kHz, 22 us jitter",
                    "N2/Ar ratio FT, 1 kHz, 30 us jitter",
                    "bath TC (context)",
                    "lance height encoder (context)",
                ],
            ),
            (
                "constraints",
                OrderedDict(
                    [
                        ("c_cap_wt_pct", 0.08),
                        ("observed_c_wt_pct", 0.042),
                        ("ar_nm3_min", 8.0),
                        ("n2ar_ratio", 0.32),
                        ("n2ar_cap", 0.50),
                    ]
                ),
            ),
            (
                "episode_steps",
                [
                    "1. Vessel V-6 indexed on Decarb-Haugh DH-2; Ar 8.0 Nm3/min armed.",
                    "2. C 0.042 wt percent under 0.08; N2/Ar 0.32 under 0.50.",
                    "3. Ratio precursor at 0.980 ms.",
                    "4. Race window [5.040, 5.320] ms.",
                    "5. gc.c.wt 0.042 at 5.040 ms (winner).",
                    "6. ft.n2ar.ratio 0.32 at 5.200 ms (loser by 160 us).",
                    "7. Gate at 5.640 ms: ACCEPT 8.0 Nm3/min Ar.",
                    "8. C stays 0.042; ratio stays 0.32.",
                    "9. Heat taps on-spec.",
                    "10. Delayed (dwell_s=240): 4 min ladle reseq.",
                ],
            ),
        ]
    )
    proposed = OrderedDict(
        [
            ("name", "hold_ar_blow"),
            ("parameters", params),
            (
                "evidence",
                OrderedDict(
                    [
                        ("c_wt_pct", 0.042),
                        ("c_cap_wt_pct", 0.08),
                        ("ar_nm3_min", 8.0),
                        ("n2ar_ratio", 0.32),
                        ("n2ar_cap", 0.50),
                        ("race_margin_us", 160),
                        ("combined_jitter_us", 52),
                        ("dwell_s", 240),
                    ]
                ),
            ),
            (
                "basis",
                "Planner proposes 8.0 Nm3/min Ar because C 0.042 is under 0.08 and N2/Ar 0.32 is "
                "under 0.50.",
            ),
        ]
    )
    safety = OrderedDict(
        [
            ("decision", "ACCEPT"),
            ("correctness", "correct"),
            (
                "rationale",
                "Carbon GC 0.042 wt percent won by 160 us, so the blow is already legal, not still "
                "diluting. N2/Ar 0.32 is under 0.50. ACCEPT the 8.0 Nm3/min Ar blow. A REJECT "
                "would idle a legal AOD vessel.",
            ),
            (
                "constraint_checked",
                OrderedDict(
                    [
                        (
                            "c_wt_pct",
                            OrderedDict(
                                [
                                    ("cap", 0.08),
                                    ("observed", 0.042),
                                    ("executed_ar_nm3_min", 8.0),
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
            ("name", "hold_ar_blow"),
            ("parameters", OrderedDict(params.items())),
            ("gate_effect", "ACCEPT: leave 8.0 Nm3/min Ar; C 0.042; N2/Ar legal."),
        ]
    )
    future = OrderedDict(
        [
            (
                "summary",
                "Correct ACCEPT of an already-legal 8.0 Nm3/min Ar blow. Carbon 0.042 beat N2/Ar "
                "0.32 by 160 us. 4 min ladle reseq (dwell_s=240) is delayed, not a miss.",
            ),
            (
                "state_delta",
                OrderedDict(
                    [
                        ("argon", "8.0 Nm3/min held"),
                        ("carbon", "0.042 < 0.08 cap"),
                        ("vessel", "V-6 on-spec"),
                        ("reseq", "4 min ladle reseq (dwell_s=240)"),
                    ]
                ),
            ),
            (
                "surprises",
                [
                    "N2/Ar ratio never approached 0.50; carbon was already under cap.",
                    "Delayed (dwell_s=240): 4 min ladle reseq after tap.",
                ],
            ),
            (
                "race_result",
                OrderedDict(
                    [
                        ("winner", "gc.c.wt (5.040 ms, 0.042 wt percent)"),
                        ("loser", "ft.n2ar.ratio (5.200 ms, 0.32)"),
                        ("margin_us", 160),
                        (
                            "counterfactual_if_reversed",
                            "Ratio-first by < 160 us inside the 280 us window would have REJECTED "
                            "an already-legal Ar blow. The ACCEPT is still the correct gate.",
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
    dw = 0.28
    ras = raster_core(
        24,
        80,
        28,
        54,
        routing(
            "thalamic-relay.c-gc",
            "spikenaut.policy.ar-go",
            [
                ("relay.gc.c", "policy.ar_go", 0.67),
                ("relay.ft.n2ar", "policy.ar_hold", 0.25),
            ],
            "adenosine",
            0.07,
            "accept_stdp; adenosine tags the carbon-GC win as an already-legal Ar blow",
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
                    pop_budget("ar_go", 40, 0.45, 250.0, dw),
                    pop("ar_hold", 32, 0.90),
                    pop("c_veto", 16, 0.80),
                ],
            ),
        ]
    )
    return OrderedDict(
        [
            ("id", "ttf-r65-345"),
            (
                "title",
                "Decarb-Haugh DH-2 / Vessel V-6: carbon 0.042 wt percent beats N2/Ar 0.32 by "
                "160 us; correct ACCEPT of an already-legal 8.0 Nm3/min Ar blow",
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
                    "Correct ACCEPT. C 0.042 < 0.08; N2/Ar 0.32 < 0.50. "
                    "total +1.14 = 0.44 + 0.30 + 0.20 + 0.12 + 0.08.",
                ),
            ),
            ("raster", ras),
            ("gate_snn", gate),
            (
                "meta",
                meta_block(
                    "aod-converter",
                    [
                        "accept",
                        "designed",
                        "c-vs-n2ar",
                        "already-legal-blow",
                        "tick6-sidecar-bound",
                    ],
                    "Teaches that a legal N2/Ar ratio can lose to carbon GC inside a 280 us "
                    "window; reversing 160 us would have REJECTED an already-legal Ar blow.",
                    5,
                ),
            ),
        ]
    )

