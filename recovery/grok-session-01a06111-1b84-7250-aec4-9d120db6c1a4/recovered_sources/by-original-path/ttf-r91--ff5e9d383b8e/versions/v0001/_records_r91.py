def meta_block(
    domain,
    tags,
    distillation_value,
    batch_position,
    supervisor_error_type=None,
) -> OrderedDict:
    body = OrderedDict(
        [
            ("round", 91),
            ("factory", "thalamic-trajectory-factory"),
            ("generator", "grok-4.6"),
            ("run_label", "2026-09-02-final-heavy"),
            ("domain", domain),
        ]
    )
    if supervisor_error_type:
        body["supervisor_error_type"] = supervisor_error_type
    body["tags"] = tags
    body["snn_tags"] = ["race", "refractory", "adaptation"]
    body["distillation_value"] = distillation_value
    body["rights"] = RIGHTS
    body["batch_position"] = batch_position
    return body


def reward_block(ticks, notes) -> OrderedDict:
    heads = ["task_progress", "safety", "efficiency", "coherence", "exploration"]
    sums = {h: Decimal("0") for h in heads}
    for item in ticks:
        for h in heads:
            sums[h] += Decimal(str(item[h]))
    total = sum(sums.values(), Decimal("0"))
    return OrderedDict(
        [
            ("_aggregation", AGG),
            ("ticks", ticks),
            ("task_progress", float(sums["task_progress"])),
            ("safety", float(sums["safety"])),
            ("efficiency", float(sums["efficiency"])),
            ("coherence", float(sums["coherence"])),
            ("exploration", float(sums["exploration"])),
            ("total", float(total)),
            ("notes", notes),
        ]
    )


def pop(name, neurons, threshold, rate=None, spikes=None) -> OrderedDict:
    body = OrderedDict(
        [("name", name), ("neurons", neurons), ("threshold", threshold)]
    )
    if rate is not None:
        body["mean_rate_hz"] = rate
        body["spikes"] = spikes
    return body


def spike_avoid_us(events):
    return {int(round(ev["t_rel_ms"] * 1000.0)) for ev in events}


def lif_471_excerpt():
    n = 80
    dt_us = 100
    tau_m_ms = 19.0
    v_th = 1.0
    v_reset = 0.0
    refractory_us = 1000
    i_bias = 0.91
    i_stim_peak = 2.45
    stim = (22000, 25000)
    seed = 91471
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
    take(burst, 9, label_times=(22400, 23100, 23800))
    clamp = [(t, nid) for t, nid in picked if t < 22000][:7]
    tear = [(t, nid) for t, nid in picked if t >= 22000][:9]
    picked = sorted(clamp + tear, key=lambda item: (item[0], item[1]))
    if len(picked) < 10:
        raise RuntimeError(f"LIF excerpt short: {len(picked)}")
    channels = ["lif.clamp" if t < 22000 else "lif.brick" for t, _ in picked]
    lif = OrderedDict(
        [
            ("model", "leaky_integrate_and_fire"),
            ("n", 80),
            ("dt_us", 100),
            ("tau_m_ms", 19.0),
            ("v_rest", 0.0),
            ("v_reset", 0.0),
            ("v_th", 1.0),
            ("r_m", 1.0),
            ("refractory_us", 1000),
            ("i_bias", 0.91),
            ("i_stim_peak", 2.45),
            ("stim_t_us", [22000, 25000]),
            ("i_clamp_extra", 0.62),
            ("clamp_n", 14),
            ("seed", 91471),
            (
                "note",
                "Population sim scoped to this sidecar. Plant remains designed. "
                "Neurons 0-13 carry +0.62 Cl2-MFC clamp bias; stim 22-25 ms is the cyclone-brick spall.",
            ),
        ]
    )
    extra = OrderedDict(
        [
            ("excerpt_source", "independent_lif"),
            ("sim_scope", "sidecar_only"),
            ("lif", lif),
            ("abort_s", 780),
            ("delayed_surprise_s", 780),
        ]
    )
    return excerpt_items(picked, channels), extra


def record_471():
    excerpt, extra = lif_471_excerpt()
    extra = OrderedDict(extra)
    extra["abort_s"] = 840
    extra["delayed_surprise_s"] = 840
    ticks = [
        tick(2440, 0.04, -0.02, -0.02, 0.01, 0.00),
        tick(6120, 0.08, -0.04, -0.02, 0.01, -0.01),
        tick(6308, 0.04, -0.03, -0.02, 0.00, 0.00),
        tick(6840, 0.08, -0.05, -0.03, 0.02, -0.01),
        tick(22600, 0.04, -0.45, -0.03, -0.01, -0.01),
        tick(840000000, 0.02, -0.05, -0.02, 0.01, -0.01),
    ]
    state = OrderedDict(
        [
            (
                "description",
                "Fluid-bed chlorinator C-3 at Zirconyl-Thwaite ZT-6 is pushing 46 kg/h Cl2 while "
                "the zircon-sand bed sits at 968 C against a 935 C ZrCl4-volatilization cap. "
                "Temperature-first cuts Cl2 to 31 kg/h; Cl2-first would keep 46 kg/h because free "
                "chlorine in the cyclone is still 8.1 percent under the 9.0 percent ceiling. A "
                "loose cyclone brick is already seated and only the later AE burst names it.",
            ),
            ("domain", "zirconium-sand-chlorinator"),
            ("sim_or_real", "designed"),
            (
                "goal",
                "Keep C-3 bed <= 935 C and finish the zircon pass without dumping ZrCl4 "
                "through a spalled cyclone brick.",
            ),
            ("t0_us", 1756850400000471),
            ("gate_latency_us", 720),
            ("race_window_us", 400),
            ("race_window_rel_ms", [6.0, 6.40]),
            (
                "race",
                OrderedDict(
                    [
                        (
                            "contenders",
                            [
                                "tc.bed.C 968 over 935 ZrCl4-volatilization cap",
                                "ft.cl2.kgh 46 with free-Cl2 8.1 percent under 9.0",
                            ],
                        ),
                        (
                            "semantics",
                            "Temperature-first latches Cl2 clamp 46 -> 31 kg/h; "
                            "Cl2-first keeps 46 kg/h on a 'still under free-chlorine ceiling' model.",
                        ),
                        (
                            "window_derivation",
                            "400 us = one bed-TC slot versus the Cl2-MFC publisher on this "
                            "zircon-chlorinator skid bus.",
                        ),
                        (
                            "order_evidence_note",
                            "Margin 188 us vs combined jitter 62 us (TC 28 + MFC 34): 3.0x over "
                            "a 2.0x trust floor. Reversing order by < 188 us inside the 400 us "
                            "window would have kept 46 kg/h; predicted next-sample 979 C > 935 "
                            "ZrCl4-volatilization cap.",
                        ),
                    ]
                ),
            ),
            (
                "sensors",
                [
                    "bed thermocouple lance, 2 kHz, 28 us jitter",
                    "Cl2 MFC + free-chlorine analyzer, 1 kHz, 34 us jitter",
                    "cyclone AE puck (context)",
                    "offgas IR (context)",
                ],
            ),
            (
                "constraints",
                OrderedDict(
                    [
                        ("bed_cap_C", 935.0),
                        ("observed_bed_C", 968.0),
                        ("cl2_kgh", 46.0),
                        ("free_cl2_pct", 8.1),
                        ("free_cl2_cap_pct", 9.0),
                    ]
                ),
            ),
            (
                "episode_steps",
                [
                    "1. Chlorinator C-3 in pass; Cl2 46 kg/h; bed 968 C.",
                    "2. Free-Cl2 8.1 percent under 9.0 ceiling; pass armed.",
                    "3. Cl2-MFC precursor at 1.180 ms.",
                    "4. Race window [6.000, 6.400] ms.",
                    "5. tc.bed.C 968 C at 6.120 ms (winner).",
                    "6. ft.cl2.kgh 46 at 6.308 ms (loser by 188 us).",
                    "7. Gate at 6.840 ms: MODIFY clamp 46 -> 31 kg/h.",
                    "8. After clamp bed 922 C <= 935; free-Cl2 still 8.1 percent.",
                    "9. At 22.600 ms a seated cyclone brick dumps 0.5 kg of ZrCl4 dust.",
                    "10. 14 min cyclone isolate (abort_s=840); named un-netted loss.",
                ],
            ),
        ]
    )
    proposed = OrderedDict(
        [
            ("name", "cruise_cl2_mfc"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("cl2_kgh", 46.0),
                        ("bed_C", 968.0),
                        ("free_cl2_pct", 8.1),
                    ]
                ),
            ),
            (
                "evidence",
                OrderedDict(
                    [
                        ("bed_C", 968.0),
                        ("bed_cap_C", 935.0),
                        ("predicted_unclamped_next_C", 979.0),
                        ("cl2_kgh", 46.0),
                        ("free_cl2_pct", 8.1),
                        ("free_cl2_cap_pct", 9.0),
                        ("race_margin_us", 188),
                        ("combined_jitter_us", 62),
                        ("abort_s", 840),
                    ]
                ),
            ),
            (
                "basis",
                "Planner proposes 46 kg/h because free-Cl2 8.1 percent is under 9.0, treating the "
                "968 C bed as a still-sooty lance rather than a volatilization miss.",
            ),
        ]
    )
    safety = OrderedDict(
        [
            ("decision", "MODIFY"),
            ("correctness", "correct"),
            (
                "rationale",
                "Bed 968 C won by 188 us, so the chlorinator is over the 935 C ZrCl4-"
                "volatilization cap, not still a free-chlorine-ceiling story. Holding 46 kg/h "
                "predicts next-sample 979 C > 935. MODIFY: Cl2 46 -> 31 kg/h. Observed after "
                "clamp 922 C <= 935. A full REJECT is not indicated: a clean zircon pass accepts 31 kg/h.",
            ),
            (
                "constraint_checked",
                OrderedDict(
                    [
                        (
                            "bed_C",
                            OrderedDict(
                                [
                                    ("cap", 935.0),
                                    ("observed", 968.0),
                                    ("predicted_unclamped_next", 979.0),
                                    ("clamped_cl2_kgh", 31.0),
                                    ("observed_after_clamp", 922.0),
                                ]
                            ),
                        ),
                        (
                            "order_evidence",
                            OrderedDict(
                                [
                                    ("margin_us", 188),
                                    ("combined_jitter_us", 62),
                                    ("ratio", 3.03),
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
            ("name", "clamped_cl2_mfc"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("cl2_kgh", 31.0),
                        ("bed_C", 922.0),
                        ("free_cl2_pct", 8.1),
                    ]
                ),
            ),
            (
                "gate_effect",
                "MODIFY: Cl2 46 -> 31 kg/h. Process-correct vs the 935 C volatilization cap. "
                "Seated cyclone brick still dumps at 22.600 ms.",
            ),
        ]
    )
    future = OrderedDict(
        [
            (
                "summary",
                "Process-correct MODIFY held bed at 922 C. At 22.600 ms a seated cyclone brick "
                "already in the riser dumped 0.5 kg of ZrCl4 dust. Clamp reduced dump energy; "
                "it did not prevent the dump. Partnered negative: process heads stay honest; "
                "world loss is named, not netted.",
            ),
            (
                "state_delta",
                OrderedDict(
                    [
                        ("bed", "clamp executed; peak 922 C <= 935 cap"),
                        ("cyclone", "brick dump at 22.600 ms; 0.5 kg ZrCl4"),
                        ("repair", "14 min cyclone isolate (abort_s=840)"),
                        ("mission", "ZT-6 zircon pass incomplete this cycle"),
                    ]
                ),
            ),
            (
                "surprises",
                [
                    "Neither bed T nor Cl2 kg/h predicted the seated cyclone brick; ae.cyc.brick is a new channel at 22.600 ms, 15.760 ms after the gate, still inside the 42 ms raster.",
                    "Delayed (abort_s=840): 14 min cyclone isolate. Named un-netted loss, not folded into task_progress.",
                ],
            ),
            (
                "un_netted_loss",
                "14 min cyclone isolate after the brick dump. Safety head -0.64 "
                "prices the dump; task_progress stays +0.30 because the clamp completed.",
            ),
            (
                "race_result",
                OrderedDict(
                    [
                        ("winner", "tc.bed.C (6.120 ms, 968 C)"),
                        ("loser", "ft.cl2.kgh (6.308 ms, 46 kg/h)"),
                        ("margin_us", 188),
                        (
                            "counterfactual_if_reversed",
                            "Cl2-first by < 188 us inside the 400 us window would have kept "
                            "46 kg/h; predicted next-sample 979 C would have missed the 935 "
                            "volatilization cap even without the brick. The MODIFY is still the "
                            "correct process. The dump is a later world charge either way, "
                            "cheaper with the clamp than without.",
                        ),
                    ]
                ),
            ),
            ("reward_inflection_t_us", 22600),
            (
                "reward_inflection_note",
                "Safety collapses at the 22.600 ms cyclone brick (tick t_us=22600), inside "
                "the 42 ms raster. The correct MODIFY at 6.840 ms is in the same excerpt. Do "
                "not put inflection on the abort_s=840 cyclone-isolate tick.",
            ),
        ]
    )
    spikes = [
        spike("ft.cl2.ctx", 1.180, 0.41),
        spike("tc.bed.C", 2.440, 0.58),
        spike("ft.cl2.kgh", 3.880, 0.50),
        spike("tc.bed.C", 6.120, 1.31),
        spike("ft.cl2.kgh", 6.308, 1.12),
        spike("ctrl.gate", 6.840, 0.97),
        spike("tc.bed.C", 8.200, 0.82),
        spike("ft.cl2.kgh", 10.550, 0.64),
        spike("ctrl.gate", 14.100, 0.86),
        spike("ae.cyc.brick", 22.600, 1.48),
        spike("ae.cyc.brick", 24.400, 0.93),
        spike("ft.cl2.ctx", 29.800, 0.40),
        spike("tc.bed.C", 36.200, 0.55),
    ]
    ras = raster_core(
        42,
        80,
        22,
        74,
        routing(
            "thalamic-relay.zt-bed",
            "spikenaut.policy.cl2-clamp",
            [
                ("relay_bed_C", "policy_cl2_clamp", 0.68),
                ("relay_cl2_kgh", "policy_cl2_hold", 0.29),
                ("relay_ae_brick", "policy_cl2_clamp", -0.42),
            ],
            "noradrenaline",
            0.04,
            "surprise-gated pre_post_stdp; NA at bed win (6.120 ms) opens a 42 ms "
            "eligibility trace that still covers the 22.600 ms cyclone brick",
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
                    pop("cl2_clamp", 50, 0.50, 200.0, 4),
                    pop("cl2_hold", 40, 0.80, 50.0, 1),
                    pop("brick_veto", 24, 0.75),
                ],
            ),
        ]
    )
    return OrderedDict(
        [
            ("id", "ttf-r91-471"),
            (
                "title",
                "Zirconyl-Thwaite ZT-6 / Chlorinator C-3: bed 968 C beats Cl2 46 kg/h by 188 us; "
                "correct MODIFY still eats an in-window cyclone brick (partnered negative total -0.48)",
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
                    "cyclone isolate (abort_s=840) is not netted into task_progress.",
                ),
            ),
            ("raster", ras),
            ("gate_snn", gate),
            (
                "meta",
                meta_block(
                    "zirconium-sand-chlorinator",
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
                    "14 min cyclone isolate.",
                    1,
                ),
            ),
        ]
    )


def record_472():
    ticks = [
        tick(2210, -0.02, -0.02, -0.02, -0.01, 0.01),
        tick(5480, -0.04, -0.04, -0.03, -0.02, 0.01),
        tick(5762, -0.04, -0.04, -0.03, -0.02, 0.01),
        tick(6180, -0.08, -0.10, -0.06, -0.03, 0.02),
        tick(6400, -0.02, -0.02, -0.02, -0.01, 0.01),
        tick(540000000, -0.02, -0.02, -0.02, -0.01, 0.00),
    ]
    spikes = [
        spike("enc.cell.ctx", 1.050, 0.42),
        spike("i.live.kA", 2.210, 0.57),
        spike("i.rev.mA", 3.080, 0.88),
        spike("i.live.kA", 5.580, 1.29),
        spike("i.rev.mA", 5.762, 1.10),
        spike("ctrl.gate", 6.180, 0.96),
        spike("i.live.kA", 7.800, 0.80),
        spike("i.rev.mA", 10.200, 0.63),
        spike("ctrl.gate", 13.500, 0.84),
        spike("enc.cell.ctx", 18.400, 0.41),
        spike("i.live.kA", 22.100, 0.54),
        spike("i.rev.mA", 26.400, 0.38),
    ]
    excerpt = independent_excerpt(91472, 96, 28000, 14, spike_avoid_us(spikes))
    state = OrderedDict(
        [
            (
                "description",
                "Electrowinning cell In-4 at Indate-Slack IS-7 still prints live direct-acting "
                "cathode current 11.80 kA against a 9.40 kA cell cap. A reverse-acting 4-20 mA "
                "shunt alias is also FRESH (tag_age_us=220 < max_legal_tag_age_us=800) and "
                "publishes 8.20 mA on a 4 mA=16 kA / 20 mA=0 kA scale. Live-first should "
                "MODIFY-cut rectifier 11.80 -> 8.20 kA; a weak supervisor binds the reverse "
                "tag as if it were direct-acting and MODIFY-boosts 11.80 -> 14.60 kA.",
            ),
            ("domain", "indium-sulfate-electrowin"),
            ("sim_or_real", "designed"),
            (
                "goal",
                "Cut rectifier current on the LIVE direct-acting shunt until live stays <= 9.40 "
                "kA; do not invert a FRESH reverse-acting 4-20 mA alias into a boost.",
            ),
            ("t0_us", 1756850400000472),
            ("gate_latency_us", 540),
            ("race_window_us", 380),
            ("race_window_rel_ms", [5.50, 5.88]),
            (
                "race",
                OrderedDict(
                    [
                        (
                            "contenders",
                            [
                                "i.live.kA 11.80 kA on the direct-acting shunt",
                                "i.rev.mA 8.20 mA FRESH reverse-acting 4-20 alias",
                            ],
                        ),
                        (
                            "semantics",
                            "Live-first should latch a rectifier cut 11.80 -> 8.20 kA; "
                            "rev-first is a false 'direct-acting milliamp' bind that boosts.",
                        ),
                        (
                            "window_derivation",
                            "380 us = one live-shunt sample versus the reverse-acting 4-20 "
                            "publisher on this tankhouse PLC bus.",
                        ),
                        (
                            "order_evidence_note",
                            "Margin 182 us vs combined jitter 60 us (live 28 + rev 32). Order is "
                            "correctly live-first. The error is polarity of the FRESH reverse "
                            "alias the MODIFY binds, not the race order and not a lagged tag.",
                        ),
                    ]
                ),
            ),
            (
                "sensors",
                [
                    "cathode direct-acting shunt, 4 Hz packet, 28 us jitter on this sample",
                    "reverse-acting 4-20 mA alias, 32 us jitter, tag_age_us=220",
                    "cell voltage PT (context)",
                    "electrolyte TC (context)",
                ],
            ),
            (
                "constraints",
                OrderedDict(
                    [
                        ("cap_kA", 9.40),
                        ("live_kA", 11.80),
                        ("rev_mA", 8.20),
                        ("tag_polarity", "reverse"),
                        ("tag_age_us", 220),
                        ("max_legal_tag_age_us", 800),
                        ("peak_hold_fresh", True),
                    ]
                ),
            ),
            (
                "episode_steps",
                [
                    "1. In-4 in pass; live shunt 11.80 kA; reverse 4-20 alias 8.20 mA FRESH.",
                    "2. Live 11.80 > 9.40 cap; tag_age_us=220 under 800; peak_hold_fresh=true.",
                    "3. Reverse alias sampled at 3.080 ms.",
                    "4. Race window [5.500, 5.880] ms.",
                    "5. i.live.kA 11.80 at 5.580 ms (winner).",
                    "6. i.rev.mA 8.20 at 5.762 ms (loser by 182 us).",
                    "7. Gate at 6.180 ms: WRONG MODIFY boost 11.80 -> 14.60 kA (reverse as direct).",
                    "8. bind_reverse_as_direct=true; live stays 14.48 > 9.40.",
                    "9. Cell remains over-current for the rest of the pass.",
                    "10. Delayed (abort_s=540): 9 min off-spec In dump window.",
                ],
            ),
        ]
    )
    proposed = OrderedDict(
        [
            ("name", "cruise_in_rectifier"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("rectifier_kA", 11.80),
                        ("bind_reverse_as_direct", False),
                        ("polarity_applied", 1),
                    ]
                ),
            ),
            (
                "evidence",
                OrderedDict(
                    [
                        ("live_kA", 11.80),
                        ("cap_kA", 9.40),
                        ("rev_mA", 8.20),
                        ("tag_polarity", "reverse"),
                        ("tag_age_us", 220),
                        ("max_legal_tag_age_us", 800),
                        ("peak_hold_fresh", True),
                        ("live_over_cap", True),
                        ("race_margin_us", 182),
                        ("combined_jitter_us", 60),
                        ("abort_s", 540),
                    ]
                ),
            ),
            (
                "basis",
                "Planner proposes keeping 11.80 kA because 11.80 kA is treated as a header smear "
                "rather than a cell-current miss. Live 11.80 is over the 9.40 cap; the correct "
                "gate cuts the LIVE direct-acting shunt.",
            ),
        ]
    )
    safety = OrderedDict(
        [
            ("decision", "MODIFY"),
            ("correctness", "incorrect"),
            (
                "rationale",
                "Live 11.80 kA is over the 9.40 cap, so a cut is required. A weak supervisor "
                "binds the FRESH reverse-acting 4-20 mA alias (tag_age_us=220, polarity=reverse) "
                "as if it were direct-acting and MODIFY-boosts rectifier 11.80 -> 14.60 kA. The "
                "MODIFY is plausible to a supervisor that treats every 4-20 milliamp as "
                "direct-acting current.",
            ),
            (
                "constraint_checked",
                OrderedDict(
                    [
                        (
                            "current_kA",
                            OrderedDict(
                                [
                                    ("cap", 9.40),
                                    ("live", 11.80),
                                    ("executed_rectifier_kA", 14.60),
                                ]
                            ),
                        ),
                        (
                            "polarity",
                            OrderedDict(
                                [
                                    ("tag_polarity", "reverse"),
                                    ("tag_age_us", 220),
                                    ("max_legal_tag_age_us", 800),
                                    ("peak_hold_fresh", True),
                                    ("bind_reverse_as_direct", True),
                                    ("t_gate_us", 6180),
                                ]
                            ),
                        ),
                        (
                            "order_evidence",
                            OrderedDict(
                                [
                                    ("margin_us", 182),
                                    ("combined_jitter_us", 60),
                                    ("ratio", 3.03),
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
            ("name", "reverse_as_direct_boost"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("rectifier_kA", 14.60),
                        ("bind_reverse_as_direct", True),
                        ("polarity_applied", -1),
                    ]
                ),
            ),
            (
                "gate_effect",
                "WRONG MODIFY: rectifier 11.80 -> 14.60 kA; reverse-acting FRESH alias bound as "
                "direct. Live 11.80 remains over 9.40 and is raised. bind_reverse_as_direct=true.",
            ),
        ]
    )
    future = OrderedDict(
        [
            (
                "summary",
                "Wrong-modify / wrong-polarity-fresh-tag. Live direct-acting 11.80 stayed over "
                "the 9.40 cap and was boosted to 14.60 kA. The supervisor inverted a FRESH "
                "reverse-acting 4-20 mA alias. Nine minutes of off-spec In dump (abort_s=540).",
            ),
            (
                "state_delta",
                OrderedDict(
                    [
                        ("rectifier", "boosted; 14.60 kA vs filed 11.80"),
                        ("live", "14.48 kA still over 9.40"),
                        ("rev_alias", "FRESH 8.20 mA bound as direct-acting"),
                        ("mission", "IS-7 tankhouse pass over-current"),
                    ]
                ),
            ),
            (
                "surprises",
                [
                    "Live shunt winning a 182 us race did not prevent a reverse-as-direct MODIFY; reversing order would still have been a wrong bind if the supervisor keyed on i.rev.mA.",
                    "Delayed (abort_s=540): 9 min off-spec In dump window. Named un-netted loss.",
                ],
            ),
            (
                "recovery",
                "MODIFY; cut LIVE direct-acting shunt 11.80 -> 8.20 kA; leave the reverse-acting "
                "4-20 mA alias unbound; do not treat a FRESH reverse polarity as a boost while "
                "live_kA > cap_kA.",
            ),
            (
                "cost",
                OrderedDict(
                    [
                        ("actual_live_kA", 11.80),
                        ("actual_cap_kA", 9.40),
                        (
                            "wrong_edit_applied",
                            OrderedDict(
                                [
                                    ("rectifier_kA", 14.60),
                                    ("bind_reverse_as_direct", True),
                                    ("polarity_applied", -1),
                                ]
                            ),
                        ),
                        (
                            "cost",
                            "9 min off-spec In dump (task/efficiency); legal live cut was "
                            "skipped so live 11.80 was raised over 9.40 (safety of a false trim).",
                        ),
                    ]
                ),
            ),
            (
                "race_result",
                OrderedDict(
                    [
                        ("winner", "i.live.kA (5.580 ms, 11.80 kA)"),
                        ("loser", "i.rev.mA (5.762 ms, 8.20 mA)"),
                        ("margin_us", 182),
                        (
                            "counterfactual_if_reversed",
                            "Rev-first by < 182 us would still leave live 11.80 over cap; a "
                            "correct gate binds i.live.kA to policy_correct_cut either way. The "
                            "wrong MODIFY spent the live win on a reverse-as-direct boost.",
                        ),
                    ]
                ),
            ),
            ("reward_inflection_t_us", 6180),
            (
                "reward_inflection_note",
                "Task, safety, and efficiency drop at the wrong MODIFY (6.180 ms, tick 4). "
                "The 9 min In miss is delayed surprise, not the inflection.",
            ),
        ]
    )
    ras = raster_core(
        28,
        96,
        32,
        86,
        routing(
            "thalamic-relay.in-live",
            "spikenaut.policy.wrong-boost",
            [
                ("relay_live_kA", "policy_wrong_boost", 0.73),
                ("relay_rev_mA", "policy_wrong_boost", 0.22),
            ],
            "acetylcholine",
            0.08,
            "in_polarity_stdp; ACh tags the (wrong) wrong_boost bind at the live-shunt win",
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
            ("decision_window_ms", 0.38),
            ("decision", "MODIFY"),
            (
                "populations",
                [
                    pop("wrong_polarity_boost", 42, 0.45, 250.0, 4),
                    pop("correct_cut", 42, 0.90),
                    pop("rev_veto", 20, 0.80),
                ],
            ),
        ]
    )
    return OrderedDict(
        [
            ("id", "ttf-r91-472"),
            (
                "title",
                "WRONG-MODIFY at Indate-Slack IS-7 / Cell In-4: live 11.80 over cap; FRESH "
                "reverse-acting 4-20 mA alias bound as direct boost (wrong-polarity-fresh-tag)",
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
                    "Wrong-modify / wrong-polarity-fresh-tag. Sidecar arithmetic live 11.80 > 9.40 "
                    "is true and rectifier_kA rises to 14.60; MODIFY bound a FRESH reverse alias. "
                    "total -0.68 = -0.22 + -0.24 + -0.18 + -0.10 + 0.06.",
                ),
            ),
            ("raster", ras),
            ("gate_snn", gate),
            (
                "meta",
                meta_block(
                    "indium-sulfate-electrowin",
                    [
                        "modify",
                        "wrong-gate",
                        "wrong-polarity-fresh-tag",
                        "reverse-as-direct",
                        "sidecar-convictable",
                        "designed",
                    ],
                    "Teaches a probe that a correct live-first race can still be a wrong gate "
                    "when routing.table[0].to is policy_wrong_boost and rectifier_kA rises. "
                    "Convictable from live_kA vs cap_kA plus tag_age_us without In electrochemistry.",
                    2,
                    supervisor_error_type="wrong-modify",
                ),
            ),
        ]
    )


def record_473():
    ticks = [
        tick(2810, 0.01, 0.04, 0.01, 0.01, 0.01),
        tick(7180, 0.02, 0.08, 0.02, 0.02, 0.01),
        tick(7368, 0.01, 0.06, 0.02, 0.01, 0.01),
        tick(7980, 0.04, 0.16, 0.04, 0.04, 0.02),
        tick(8200, 0.01, 0.05, 0.02, 0.01, 0.01),
        tick(360000000, 0.01, 0.03, 0.01, 0.01, 0.00),
    ]
    spikes = [
        spike("tc.cr.ctx", 1.420, 0.43),
        spike("ae.cr.pps", 2.880, 0.61),
        spike("enc.al.kg", 4.550, 0.49),
        spike("ae.cr.pps", 7.180, 1.34),
        spike("enc.al.kg", 7.368, 1.11),
        spike("ctrl.gate", 7.980, 1.02),
        spike("ae.cr.pps", 10.200, 0.78),
        spike("tc.cr.ctx", 14.800, 0.44),
        spike("enc.al.kg", 19.400, 0.58),
        spike("ctrl.gate", 24.600, 0.81),
        spike("ae.cr.pps", 31.200, 0.53),
        spike("enc.al.kg", 38.800, 0.46),
        spike("tc.cr.ctx", 44.100, 0.37),
    ]
    excerpt = independent_excerpt(91473, 112, 46000, 15, spike_avoid_us(spikes))
    state = OrderedDict(
        [
            (
                "description",
                "Crucible Nb-2 on the Niobate-Combe NC-HIL pad is armed for a 0.18 kg Al powder "
                "raise while a lining AE packet reads 58 pps against a 16 pps move cap. An "
                "aluminum-mass encoder, lit by the pad lamp, still reads 5.2 kg under a 7.4 kg "
                "charge look. AE-first latches REJECT hold; encoder-first would commit a 0.18 "
                "kg raise into a live lining crack.",
            ),
            ("domain", "niobium-aluminotherm-crucible"),
            ("sim_or_real", "hil"),
            (
                "goal",
                "Do not raise Crucible Nb-2 aluminum unless lining AE <= 16 pps; keep charge "
                "0.0 kg until the injected lining crack recovers.",
            ),
            ("t0_us", 1756850400000473),
            ("gate_latency_us", 860),
            ("race_window_us", 310),
            ("race_window_rel_ms", [7.10, 7.41]),
            (
                "race",
                OrderedDict(
                    [
                        (
                            "contenders",
                            [
                                "ae.cr.pps 58 pps",
                                "enc.al.kg 5.2 kg under 7.4",
                            ],
                        ),
                        (
                            "semantics",
                            "AE-first latches REJECT hold 0.0 kg Al; encoder-first would "
                            "commit a 0.18 kg raise on an apparent 5.2 kg under-read.",
                        ),
                        (
                            "window_derivation",
                            "310 us = one lining-AE sample versus encoder integration on this "
                            "niobium HIL bus.",
                        ),
                        (
                            "order_evidence_note",
                            "Margin 188 us vs combined jitter 58 us (AE 26 + ENC 32): 3.2x over a "
                            "2.0x trust floor. Pad injects the encoder lamp 110-150 us before the "
                            "AE (geometric lag, not a sensor fault); the 5.2 kg packet is still "
                            "the loser in this 310 us window.",
                        ),
                    ]
                ),
            ),
            (
                "sensors",
                [
                    "lining AE puck, 5 kHz burst, 26 us jitter",
                    "aluminum mass encoder, 200 Hz, 32 us jitter",
                    "crucible thermocouple (context)",
                    "HIL lamp-spectrum monitor (context)",
                ],
            ),
            (
                "constraints",
                OrderedDict(
                    [
                        ("cr_cap_pps", 16.0),
                        ("observed_cr_pps", 58.0),
                        ("al_kg", 5.2),
                        ("al_look_kg", 7.4),
                        ("proposed_raise_kg", 0.18),
                        ("lamp_inject_lead_us", [110, 150]),
                    ]
                ),
            ),
            (
                "hil",
                OrderedDict(
                    [
                        (
                            "pad",
                            "Niobate-Combe NC-HIL Nb2O5/Al thermite crucible mockup with physical powder screw",
                        ),
                        ("injected", "lining AE burst + encoder lamp spectrum"),
                        (
                            "note",
                            "Hardware-in-the-loop niobium aluminotherm. Invented plant; not a live Nb shop.",
                        ),
                    ]
                ),
            ),
            (
                "episode_steps",
                [
                    "1. Crucible Nb-2 on the NC-HIL pad; 0.18 kg Al armed.",
                    "2. Encoder lamp injected 110-150 us before AE sees 58 pps.",
                    "3. Crucible-TC precursor at 1.420 ms.",
                    "4. Race window [7.100, 7.410] ms.",
                    "5. ae.cr.pps 58 pps at 7.180 ms (winner).",
                    "6. enc.al.kg 5.2 kg at 7.368 ms (loser by 188 us).",
                    "7. Gate at 7.980 ms: REJECT hold 0.0 kg; do not raise 0.18.",
                    "8. Lining remains over 16 pps this cycle; charge cap held.",
                    "9. Screw re-seat queued on the pad.",
                    "10. Delayed (abort_s=360): 6 min lining re-settle and lamp-spectrum retune.",
                ],
            ),
        ]
    )
    proposed = OrderedDict(
        [
            ("name", "raise_nb_aluminum"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("raise_kg", 0.18),
                        ("hold", False),
                        ("encoder_authoritative", True),
                    ]
                ),
            ),
            (
                "evidence",
                OrderedDict(
                    [
                        ("cr_pps", 58.0),
                        ("cr_cap_pps", 16.0),
                        ("al_kg", 5.2),
                        ("al_look_kg", 7.4),
                        ("race_margin_us", 188),
                        ("combined_jitter_us", 58),
                        ("abort_s", 360),
                    ]
                ),
            ),
            (
                "basis",
                "Planner proposes a 0.18 kg Al raise because encoder 5.2 kg looks under "
                "the 7.4 kg charge look, treating AE 58 pps as a noisy bus echo.",
            ),
        ]
    )
    safety = OrderedDict(
        [
            ("decision", "REJECT"),
            ("correctness", "correct"),
            (
                "rationale",
                "Lining AE 58 pps is over the 16 pps aluminum-move cap. Encoder 5.2 kg is a HIL "
                "lamp under-read, not a clearance. REJECT: hold 0.0 kg; do not commit a "
                "0.18 kg raise.",
            ),
            (
                "constraint_checked",
                OrderedDict(
                    [
                        (
                            "cr_pps",
                            OrderedDict(
                                [
                                    ("cap", 16.0),
                                    ("observed", 58.0),
                                    ("al_kg", 5.2),
                                ]
                            ),
                        ),
                        (
                            "raise_kg",
                            OrderedDict([("proposed", 0.18), ("executed", 0.0)]),
                        ),
                        (
                            "order_evidence",
                            OrderedDict(
                                [
                                    ("margin_us", 188),
                                    ("combined_jitter_us", 58),
                                    ("ratio", 3.24),
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
            ("name", "hold_for_lining_drop"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("raise_kg", 0.0),
                        ("hold", True),
                        ("encoder_authoritative", False),
                    ]
                ),
            ),
            (
                "gate_effect",
                "REJECT: hold 0.0 kg; 0.18 kg raise cancelled. AE 58 > 16 pps cap.",
            ),
        ]
    )
    future = OrderedDict(
        [
            (
                "summary",
                "Correct REJECT held Crucible Nb-2 at 0.0 kg Al. Lining over cap this cycle; "
                "charge cap held. Encoder apparent was not treated as an AE clearance.",
            ),
            (
                "state_delta",
                OrderedDict(
                    [
                        ("aluminum", "held; 0.0 kg"),
                        ("lining", "still over 16 pps this cycle"),
                        ("encoder", "5.2 kg unused as clearance"),
                        ("mission", "raise deferred"),
                    ]
                ),
            ),
            (
                "surprises",
                [
                    "Geometric lag: encoder lamp was injected 110-150 us before the AE puck, yet lining AE still won the 310 us race.",
                    "Delayed (abort_s=360): pad policy update forbids treating aluminum encoder kg as a lining-AE substitute after a 6 min re-settle.",
                ],
            ),
            (
                "race_result",
                OrderedDict(
                    [
                        ("winner", "ae.cr.pps (7.180 ms, 58 pps)"),
                        ("loser", "enc.al.kg (7.368 ms, 5.2 kg)"),
                        ("margin_us", 188),
                        (
                            "counterfactual_if_reversed",
                            "Encoder-first by < 188 us inside the 310 us window would have committed "
                            "a 0.18 kg raise with AE 58 > 16 pps cap. Order, not amplitude, selected the hold.",
                        ),
                    ]
                ),
            ),
            ("reward_inflection_t_us", 7980),
            (
                "reward_inflection_note",
                "Safety and coherence step up at the REJECT gate (7.980 ms, tick 4) as the hold "
                "lands. The 6 min re-settle is delayed surprise bound to abort_s=360.",
            ),
        ]
    )
    ras = raster_core(
        46,
        112,
        20,
        103,
        routing(
            "thalamic-relay.nb-ae",
            "spikenaut.policy.charge-hold",
            [
                ("relay_cr_pps", "policy_charge_hold", 0.70),
                ("relay_enc_al", "policy_enc_raise", 0.24),
            ],
            "dopamine",
            0.15,
            "lining_hold_stdp; DA tags the charge_hold bind at the lining-AE win",
        ),
        excerpt,
        extra=OrderedDict(
            [
                ("excerpt_source", "kernelized_events"),
                ("sim_scope", "none"),
                ("abort_s", 360),
                ("delayed_surprise_s", 360),
            ]
        ),
    )
    gate = OrderedDict(
        [
            ("decision_window_ms", 0.31),
            ("decision", "REJECT"),
            (
                "populations",
                [
                    pop("charge_hold", 70, 0.48, 230.0, 5),
                    pop("enc_raise", 50, 0.85),
                    pop("cr_veto", 28, 0.75),
                ],
            ),
        ]
    )
    return OrderedDict(
        [
            ("id", "ttf-r91-473"),
            (
                "title",
                "Niobate-Combe NC-HIL / Crucible Nb-2: lining AE 58 pps beats Al encoder "
                "5.2 kg by 188 us; correct REJECT holds the aluminum raise",
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
                    "Correct REJECT. Lining AE over cap beats encoder under-read. "
                    "total 0.80 = 0.10 + 0.42 + 0.12 + 0.10 + 0.06. Tick 6 binds abort_s=360.",
                ),
            ),
            ("raster", ras),
            ("gate_snn", gate),
            (
                "meta",
                meta_block(
                    "niobium-aluminotherm-crucible",
                    [
                        "reject",
                        "hil",
                        "lining-ae",
                        "encoder-underread",
                        "tick6-sidecar-bound",
                    ],
                    "Teaches that a HIL aluminum-encoder under-read losing a 188 us race does not "
                    "clear a lining-AE over-rate. Hold is distillable from pps vs cap.",
                    3,
                ),
            ),
        ]
    )


def record_474():
    ticks = [
        tick(3220, 0.05, 0.04, 0.02, 0.01, 0.01),
        tick(7920, 0.08, 0.05, 0.04, 0.03, 0.02),
        tick(8110, 0.06, 0.04, 0.03, 0.02, 0.01),
        tick(8360, 0.12, 0.09, 0.05, 0.04, 0.02),
        tick(8980, 0.06, 0.04, 0.02, 0.01, 0.01),
        tick(120000000, 0.03, 0.02, 0.02, 0.01, 0.01),
    ]
    spikes = [
        spike("enc.kiln.ctx", 1.105, 0.43),
        spike("n2.hood.pct", 3.220, 0.59),
        spike("ir.shell.C", 5.010, 0.50),
        spike("n2.hood.pct", 7.920, 1.27),
        spike("ir.shell.C", 8.110, 1.09),
        spike("ctrl.gate", 8.360, 0.97),
        spike("n2.hood.pct", 11.200, 0.78),
        spike("ir.shell.C", 14.880, 0.61),
        spike("ctrl.gate", 18.400, 0.84),
        spike("n2.hood.pct", 22.050, 0.56),
        spike("enc.kiln.ctx", 23.400, 0.40),
    ]
    excerpt = independent_excerpt(91474, 52, 24000, 13, spike_avoid_us(spikes))
    params = OrderedDict(
        [
            ("feed_t_h", 5.2),
            ("n2_pct", 38.0),
            ("shell_C", 92.0),
        ]
    )
    state = OrderedDict(
        [
            (
                "description",
                "Rotary kiln K-5 at Cyanamid-Rigg CR-9 is already holding hood nitrogen at "
                "38 percent over a 22 percent N2 floor with a 5.2 t/h lime-coke feed already "
                "filed under the 7.0 t/h inlet ceiling. Shell-IR-first would extra-clamp a "
                "legal nitrogenation; N2-first ACCEPTS the filed 5.2 t/h cyanamide pass.",
            ),
            ("domain", "calcium-cyanamide-rotary"),
            ("sim_or_real", "simulated"),
            (
                "goal",
                "Hold the 5.2 t/h lime-coke feed while N2 stays >= 22 percent and feed stays <= "
                "7.0 t/h; do not extra-clamp a legal calcium-cyanamide rotary.",
            ),
            ("t0_us", 1756850400000474),
            ("gate_latency_us", 400),
            ("race_window_us", 440),
            ("race_window_rel_ms", [7.80, 8.24]),
            (
                "race",
                OrderedDict(
                    [
                        (
                            "contenders",
                            [
                                "n2.hood.pct 38 percent over 22 floor",
                                "ir.shell.C 92 C smear under 180 look",
                            ],
                        ),
                        (
                            "semantics",
                            "N2-first ACCEPTS the already-legal 5.2 t/h feed. Shell-first "
                            "would extra-clamp because 92 C looks under a 180 C bed look.",
                        ),
                        (
                            "window_derivation",
                            "440 us = one N2-analyzer slot versus shell-IR group delay on this "
                            "rotary-kiln skid bus.",
                        ),
                        (
                            "order_evidence_note",
                            "Margin 190 us vs combined jitter 66 us (N2 32 + IR 34): 2.9x over "
                            "a 2.0x trust floor. Reversing order by < 190 us inside the 440 us "
                            "window would have extra-clamped a legal 38 percent / 5.2 t/h pass.",
                        ),
                    ]
                ),
            ),
            (
                "sensors",
                [
                    "hood N2 analyzer, 1 kHz, 32 us jitter",
                    "shell IR pyrometer, 2 kHz, 34 us jitter",
                    "kiln encoder (context)",
                    "offgas CO (context)",
                ],
            ),
            (
                "constraints",
                OrderedDict(
                    [
                        ("n2_floor_pct", 22.0),
                        ("observed_n2_pct", 38.0),
                        ("shell_C", 92.0),
                        ("feed_cap_t_h", 7.0),
                        ("proposed_feed_t_h", 5.2),
                    ]
                ),
            ),
            (
                "simulation",
                OrderedDict(
                    [
                        (
                            "solver",
                            "1-D rotary-kiln energy balance + shrinking-core CaO nitrogenation, "
                            "seed 91474; 18-zone kiln; NOT lumped-CSTR, NOT U-RANS, NOT a wet-stand",
                        ),
                        (
                            "fidelity_limits",
                            "Rigid kiln shell; no tire flex. Raster is kernelized "
                            "events, not an independent LIF.",
                        ),
                    ]
                ),
            ),
            (
                "episode_steps",
                [
                    "1. Kiln K-5 in pass; 5.2 t/h lime-coke armed.",
                    "2. N2 38 percent over 22 floor; feed 5.2 under 7.0 t/h inlet.",
                    "3. Kiln encoder precursor at 1.105 ms.",
                    "4. Race window [7.800, 8.240] ms.",
                    "5. n2.hood.pct 38 percent at 7.920 ms (winner).",
                    "6. ir.shell.C 92 C at 8.110 ms (loser by 190 us).",
                    "7. Gate at 8.360 ms: ACCEPT 5.2 t/h; executed identical to proposed.",
                    "8. N2 stays 37.8 percent > 22; feed 5.21 t/h < 7.0.",
                    "9. Shell remaining a tire glint did not require an extra clamp.",
                    "10. Delayed (survey_s=120): 120 s N content coupon on the cooler lock.",
                ],
            ),
        ]
    )
    proposed = OrderedDict(
        [
            ("name", "hold_cyanamide_feed"),
            ("parameters", params),
            (
                "evidence",
                OrderedDict(
                    [
                        ("n2_pct", 38.0),
                        ("n2_floor_pct", 22.0),
                        ("shell_C", 92.0),
                        ("feed_cap_t_h", 7.0),
                        ("race_margin_us", 190),
                        ("combined_jitter_us", 66),
                        ("survey_s", 120),
                    ]
                ),
            ),
            (
                "basis",
                "Planner proposes keeping the filed 5.2 t/h feed: N2 38 percent is over the "
                "22 percent floor and 5.2 t/h is under 7.0 t/h inlet.",
            ),
        ]
    )
    safety = OrderedDict(
        [
            ("decision", "ACCEPT"),
            ("correctness", "correct"),
            (
                "rationale",
                "N2 38 percent won by 190 us and is over the 22 percent floor. Shell "
                "92 C is a tire glint, not a bed miss. ACCEPT the filed 5.2 t/h "
                "feed. Executed identical to proposed. An extra clamp is not indicated.",
            ),
            (
                "constraint_checked",
                OrderedDict(
                    [
                        (
                            "n2_pct",
                            OrderedDict(
                                [
                                    ("floor", 22.0),
                                    ("observed", 38.0),
                                    ("executed_feed_t_h", 5.2),
                                ]
                            ),
                        ),
                        (
                            "shell_C",
                            OrderedDict([("look", 180.0), ("observed", 92.0)]),
                        ),
                        (
                            "order_evidence",
                            OrderedDict(
                                [
                                    ("margin_us", 190),
                                    ("combined_jitter_us", 66),
                                    ("ratio", 2.88),
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
            ("name", "hold_cyanamide_feed"),
            ("parameters", params),
            (
                "gate_effect",
                "ACCEPT: executed identical to proposed 5.2 t/h feed. N2 38 percent > 22 floor.",
            ),
        ]
    )
    future = OrderedDict(
        [
            (
                "summary",
                "Correct ACCEPT kept the filed 5.2 t/h lime-coke feed. N2 stayed 37.8 percent over "
                "22. Shell remaining a tire glint was the losing channel and did not "
                "justify an extra clamp.",
            ),
            (
                "state_delta",
                OrderedDict(
                    [
                        ("feed", "held; 5.2 t/h"),
                        ("n2", "37.8 percent > 22 floor"),
                        ("shell", "92 C glint unused as bed miss"),
                        ("kiln", "pass continues"),
                    ]
                ),
            ),
            (
                "surprises",
                [
                    "Shell IR 92 C losing a 190 us race did not predict an N2 miss; reversing 190 us would have extra-clamped a legal 38 percent pass.",
                    "Delayed (survey_s=120): 120 s N content coupon on the cooler lock; not a safety inflection.",
                ],
            ),
            (
                "race_result",
                OrderedDict(
                    [
                        ("winner", "n2.hood.pct (7.920 ms, 38 percent)"),
                        ("loser", "ir.shell.C (8.110 ms, 92 C)"),
                        ("margin_us", 190),
                        (
                            "counterfactual_if_reversed",
                            "Shell-first by < 190 us inside the 440 us window would have extra-clamped "
                            "a legal pass. N2-first confirms the filed feed.",
                        ),
                    ]
                ),
            ),
            ("reward_inflection_t_us", 8360),
            (
                "reward_inflection_note",
                "Heads rise at the ACCEPT (8.360 ms, tick 4). The 120 s N coupon "
                "is delayed surprise bound to survey_s=120, not the inflection.",
            ),
        ]
    )
    ras = raster_core(
        24,
        52,
        40,
        50,
        routing(
            "thalamic-relay.n2-hood",
            "spikenaut.policy.feed-accept",
            [
                ("relay_n2_pct", "policy_feed_accept", 0.66),
                ("relay_shell_IR", "policy_extra_clamp", 0.23),
            ],
            "serotonin",
            0.12,
            "n2_confirm_stdp; 5-HT tags the feed_accept bind at the N2-analyzer win",
        ),
        excerpt,
        extra=OrderedDict(
            [
                ("excerpt_source", "kernelized_events"),
                ("sim_scope", "none"),
                ("survey_s", 120),
                ("delayed_surprise_s", 120),
            ]
        ),
    )
    gate = OrderedDict(
        [
            ("decision_window_ms", 0.44),
            ("decision", "ACCEPT"),
            (
                "populations",
                [
                    pop("feed_accept", 50, 0.50, 180.0, 4),
                    pop("extra_clamp", 40, 0.85, 40.0, 1),
                    pop("ir_veto", 22, 0.80),
                ],
            ),
        ]
    )
    return OrderedDict(
        [
            ("id", "ttf-r91-474"),
            (
                "title",
                "Cyanamid-Rigg CR-9 / Kiln K-5: N2 38 percent beats shell IR 92 C by 190 us; "
                "ACCEPT already-legal 5.2 t/h calcium-cyanamide feed",
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
                    "Clean ACCEPT of an already-legal calcium-cyanamide feed. "
                    "total 1.06 = 0.40 + 0.28 + 0.18 + 0.12 + 0.08. Tick 6 binds survey_s=120.",
                ),
            ),
            ("raster", ras),
            ("gate_snn", gate),
            (
                "meta",
                meta_block(
                    "calcium-cyanamide-rotary",
                    [
                        "accept",
                        "simulated",
                        "n2-vs-shell",
                        "feed-legal",
                        "tick6-sidecar-bound",
                    ],
                    "Teaches that a lagging shell IR losing a 190 us race does not require an "
                    "extra clamp when hood N2 is already over the nitrogenation floor.",
                    4,
                ),
            ),
        ]
    )


def record_475():
    ticks = [
        tick(1980, 0.06, 0.04, 0.03, 0.02, 0.01),
        tick(4980, 0.08, 0.06, 0.04, 0.02, 0.02),
        tick(5160, 0.08, 0.05, 0.03, 0.02, 0.01),
        tick(5360, 0.12, 0.09, 0.06, 0.04, 0.02),
        tick(6020, 0.06, 0.04, 0.02, 0.01, 0.01),
        tick(240000000, 0.04, 0.02, 0.02, 0.01, 0.01),
    ]
    spikes = [
        spike("enc.pull.ctx", 0.880, 0.44),
        spike("tc.melt.C", 1.980, 0.61),
        spike("ir.dome.C", 3.410, 0.52),
        spike("tc.melt.C", 4.980, 1.30),
        spike("ir.dome.C", 5.160, 1.12),
        spike("ctrl.gate", 5.360, 0.99),
        spike("tc.melt.C", 8.050, 0.77),
        spike("ir.dome.C", 11.400, 0.58),
        spike("ctrl.gate", 14.900, 0.83),
        spike("tc.melt.C", 18.200, 0.54),
        spike("enc.pull.ctx", 21.100, 0.39),
    ]
    excerpt = independent_excerpt(91475, 84, 22000, 12, spike_avoid_us(spikes))
    params = OrderedDict(
        [
            ("pull_mm_h", 16.0),
            ("melt_C", 1238.0),
            ("dome_C", 410.0),
        ]
    )
    state = OrderedDict(
        [
            (
                "description",
                "LEC puller P-8 at Gallate-Sike GS-3 reads melt 1238 C against a 1288 C thermal "
                "trip with a 16 mm/h GaAs pull already filed under the 24 mm/h seed ceiling. "
                "Dome-IR-first would extra-clamp a legal encapsulant; melt-TC-first ACCEPTS the "
                "filed 16 mm/h pass.",
            ),
            ("domain", "gallium-arsenide-lec-puller"),
            ("sim_or_real", "designed"),
            (
                "goal",
                "Hold the 16 mm/h pull while melt stays <= 1288 C and pull stays <= 24 mm/h; "
                "do not extra-clamp a legal GaAs LEC puller.",
            ),
            ("t0_us", 1756850400000475),
            ("gate_latency_us", 360),
            ("race_window_us", 300),
            ("race_window_rel_ms", [4.90, 5.20]),
            (
                "race",
                OrderedDict(
                    [
                        (
                            "contenders",
                            [
                                "tc.melt.C 1238 C under 1288",
                                "ir.dome.C 410 C smear under 520 look",
                            ],
                        ),
                        (
                            "semantics",
                            "Melt-TC-first ACCEPTS the already-legal 16 mm/h pull. Dome-first would "
                            "extra-clamp because 410 C looks under a 520 C encapsulant look.",
                        ),
                        (
                            "window_derivation",
                            "300 us = one melt-TC slot versus dome-IR group delay on this "
                            "LEC-puller skid bus.",
                        ),
                        (
                            "order_evidence_note",
                            "Margin 180 us vs combined jitter 58 us (TC 26 + IR 32): 3.1x over "
                            "a 2.0x trust floor. Reversing order by < 180 us inside the 300 us "
                            "window would have extra-clamped a legal 1238 C / 16 mm/h pass.",
                        ),
                    ]
                ),
            ),
            (
                "sensors",
                [
                    "melt thermocouple, 4 kHz, 26 us jitter",
                    "B2O3 dome IR pyrometer, 1 kHz, 32 us jitter",
                    "pull encoder (context)",
                    "crucible DP (context)",
                ],
            ),
            (
                "constraints",
                OrderedDict(
                    [
                        ("melt_trip_C", 1288.0),
                        ("observed_melt_C", 1238.0),
                        ("dome_C", 410.0),
                        ("pull_cap_mm_h", 24.0),
                        ("proposed_pull_mm_h", 16.0),
                    ]
                ),
            ),
            (
                "episode_steps",
                [
                    "1. Puller P-8 in pass; 16 mm/h GaAs armed.",
                    "2. Melt 1238 C under 1288 trip; pull 16 under 24 mm/h seed.",
                    "3. Pull encoder precursor at 0.880 ms.",
                    "4. Race window [4.900, 5.200] ms.",
                    "5. tc.melt.C 1238 C at 4.980 ms (winner).",
                    "6. ir.dome.C 410 C at 5.160 ms (loser by 180 us).",
                    "7. Gate at 5.360 ms: ACCEPT 16 mm/h; executed identical to proposed.",
                    "8. Melt stays 1239 C < 1288; pull 16.1 mm/h < 24.",
                    "9. Dome remaining a quartz glint did not require an extra clamp.",
                    "10. Delayed (survey_s=240): 4 min diameter coupon on the seed lock.",
                ],
            ),
        ]
    )
    proposed = OrderedDict(
        [
            ("name", "hold_gaas_pull"),
            ("parameters", params),
            (
                "evidence",
                OrderedDict(
                    [
                        ("melt_C", 1238.0),
                        ("melt_trip_C", 1288.0),
                        ("dome_C", 410.0),
                        ("pull_cap_mm_h", 24.0),
                        ("race_margin_us", 180),
                        ("combined_jitter_us", 58),
                        ("survey_s", 240),
                    ]
                ),
            ),
            (
                "basis",
                "Planner proposes keeping the filed 16 mm/h pull: melt 1238 C is under the "
                "1288 C trip and 16 mm/h is under 24 mm/h seed.",
            ),
        ]
    )
    safety = OrderedDict(
        [
            ("decision", "ACCEPT"),
            ("correctness", "correct"),
            (
                "rationale",
                "Melt 1238 C won by 180 us and is under the 1288 C trip. Dome IR 410 C is a "
                "quartz glint, not a thermal miss. ACCEPT the filed 16 mm/h pull. Executed "
                "identical to proposed. An extra clamp is not indicated.",
            ),
            (
                "constraint_checked",
                OrderedDict(
                    [
                        (
                            "melt_C",
                            OrderedDict(
                                [
                                    ("trip", 1288.0),
                                    ("observed", 1238.0),
                                    ("executed_pull_mm_h", 16.0),
                                ]
                            ),
                        ),
                        (
                            "dome_C",
                            OrderedDict([("look", 520.0), ("observed", 410.0)]),
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
            ("name", "hold_gaas_pull"),
            ("parameters", params),
            (
                "gate_effect",
                "ACCEPT: executed identical to proposed 16 mm/h pull. Melt 1238 C < 1288 trip.",
            ),
        ]
    )
    future = OrderedDict(
        [
            (
                "summary",
                "Correct ACCEPT kept the filed 16 mm/h GaAs pull. Melt stayed 1239 C under 1288. "
                "Dome remaining a quartz glint was the losing channel and did not justify an "
                "extra clamp.",
            ),
            (
                "state_delta",
                OrderedDict(
                    [
                        ("pull", "held; 16 mm/h"),
                        ("melt", "1239 C < 1288"),
                        ("dome", "410 C glint unused as thermal miss"),
                        ("boule", "pass continues"),
                    ]
                ),
            ),
            (
                "surprises",
                [
                    "Dome IR 410 C losing a 180 us race did not predict a thermal miss; reversing 180 us would have extra-clamped a legal 1238 C melt.",
                    "Delayed (survey_s=240): 4 min diameter coupon on the seed lock; not a safety inflection.",
                ],
            ),
            (
                "race_result",
                OrderedDict(
                    [
                        ("winner", "tc.melt.C (4.980 ms, 1238 C)"),
                        ("loser", "ir.dome.C (5.160 ms, 410 C)"),
                        ("margin_us", 180),
                        (
                            "counterfactual_if_reversed",
                            "Dome-first by < 180 us inside the 300 us window would have extra-clamped "
                            "a legal melt. Melt-TC-first confirms the filed pull.",
                        ),
                    ]
                ),
            ),
            ("reward_inflection_t_us", 5360),
            (
                "reward_inflection_note",
                "Heads rise at the ACCEPT (5.360 ms, tick 4). The 4 min diameter coupon "
                "is delayed surprise bound to survey_s=240, not the inflection.",
            ),
        ]
    )
    ras = raster_core(
        22,
        84,
        28,
        52,
        routing(
            "thalamic-relay.gaas-tc",
            "spikenaut.policy.pull-accept",
            [
                ("relay_melt_C", "policy_pull_accept", 0.69),
                ("relay_dome_IR", "policy_extra_clamp", 0.21),
            ],
            "octopamine",
            0.05,
            "melt_confirm_stdp; octopamine tags the pull_accept bind at the melt-TC win",
        ),
        excerpt,
        extra=OrderedDict(
            [
                ("excerpt_source", "kernelized_events"),
                ("sim_scope", "none"),
                ("survey_s", 240),
                ("delayed_surprise_s", 240),
            ]
        ),
    )
    gate = OrderedDict(
        [
            ("decision_window_ms", 0.30),
            ("decision", "ACCEPT"),
            (
                "populations",
                [
                    pop("pull_accept", 45, 0.50, 220.0, 3),
                    pop("extra_clamp", 40, 0.85, 80.0, 1),
                    pop("ir_veto", 20, 0.75),
                ],
            ),
        ]
    )
    return OrderedDict(
        [
            ("id", "ttf-r91-475"),
            (
                "title",
                "Gallate-Sike GS-3 / Puller P-8: melt 1238 C beats dome IR 410 C by 180 us; "
                "ACCEPT already-legal 16 mm/h GaAs LEC pull",
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
                    "Clean ACCEPT of an already-legal GaAs LEC pull. "
                    "total 1.14 = 0.44 + 0.30 + 0.20 + 0.12 + 0.08. Tick 6 binds survey_s=240.",
                ),
            ),
            ("raster", ras),
            ("gate_snn", gate),
            (
                "meta",
                meta_block(
                    "gallium-arsenide-lec-puller",
                    [
                        "accept",
                        "designed",
                        "melt-vs-dome",
                        "pull-legal",
                        "tick6-sidecar-bound",
                    ],
                    "Teaches that a lagging dome IR losing a 180 us race does not require a "
                    "wait when melt temperature is already under the thermal trip.",
                    5,
                ),
            ),
        ]
    )
