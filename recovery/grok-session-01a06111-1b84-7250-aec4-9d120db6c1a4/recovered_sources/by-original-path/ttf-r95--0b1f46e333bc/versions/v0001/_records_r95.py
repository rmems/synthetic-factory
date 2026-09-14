def lif_491_excerpt():
    n = 76
    dt_us = 100
    tau_m_ms = 19.0
    v_th = 1.0
    v_reset = 0.0
    refractory_us = 1000
    i_bias = 0.91
    i_stim_peak = 2.42
    stim = (22000, 25000)
    seed = 95491
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
    leak = [(t, nid) for t, nid in picked if t >= 22000][:9]
    picked = sorted(clamp + leak, key=lambda item: (item[0], item[1]))
    if len(picked) < 10:
        raise RuntimeError(f"LIF excerpt short: {len(picked)}")
    channels = ["lif.clamp" if t < 22000 else "lif.shell" for t, _ in picked]
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
            ("seed", 95491),
            (
                "note",
                "Population sim scoped to this sidecar. Plant remains designed. "
                "Neurons 0-13 carry +0.62 air-cut clamp bias; stim 22-25 ms is the retort-shell crack.",
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


def record_491():
    excerpt, extra = lif_491_excerpt()
    ticks = [
        tick(2080, 0.04, -0.02, -0.02, 0.01, 0.00),
        tick(5200, 0.08, -0.04, -0.02, 0.01, -0.01),
        tick(5380, 0.04, -0.03, -0.02, 0.00, 0.00),
        tick(5900, 0.08, -0.05, -0.03, 0.02, -0.01),
        tick(22400, 0.06, -0.41, -0.04, -0.01, -0.01),
        tick(900000000, 0.02, -0.05, -0.03, 0.01, -0.01),
    ]
    spikes = [
        spike("pt.air.bar", 1.040, 0.41),
        spike("as.vapor.gNm3", 2.080, 0.58),
        spike("pt.air.bar", 3.400, 0.50),
        spike("as.vapor.gNm3", 5.200, 1.31),
        spike("pt.air.bar", 5.380, 1.12),
        spike("ctrl.gate", 5.900, 0.97),
        spike("as.vapor.gNm3", 8.100, 0.82),
        spike("pt.air.bar", 10.400, 0.64),
        spike("ctrl.gate", 14.200, 0.86),
        spike("ae.shell.crack", 22.400, 1.48),
        spike("ae.shell.crack", 24.100, 0.93),
        spike("pt.air.bar", 30.200, 0.40),
        spike("as.vapor.gNm3", 36.400, 0.55),
    ]
    state = OrderedDict(
        [
            (
                "description",
                "White-arsenic retort S-3 on Arsenolite-Gair AG-7 already prints 8.8 g/Nm3 As2O3 "
                "vapor against a 6.0 ceiling while the combustion header is only 3.8 bar under 5.0. "
                "The vapor cell should latch a 16.0-to-9.2 t/h air cut; trusting the header would "
                "leave 16.0 t/h running. A seated retort-shell crack on the condenser boot stays "
                "invisible to both publishers until AE fires.",
            ),
            ("domain", "arsenic-trioxide-sublimer"),
            ("sim_or_real", "designed"),
            (
                "goal",
                "Keep S-3 As2O3 vapor <= 6.0 g/Nm3 and finish the sublimer pass without "
                "dumping white-arsenic dust through a torn retort shell.",
            ),
            ("t0_us", 1756850400000491),
            ("gate_latency_us", 700),
            ("race_window_us", 360),
            ("race_window_rel_ms", [5.200, 5.560]),
            (
                "race",
                OrderedDict(
                    [
                        (
                            "contenders",
                            [
                                "as.vapor.gNm3 8.8 over 6.0 cap",
                                "pt.air.bar 3.8 with header under 5.0",
                            ],
                        ),
                        (
                            "semantics",
                            "Vapor-first latches air clamp 16.0 -> 9.2 t/h; header-first keeps 16.0 "
                            "on a 'still under compressor-cap' model.",
                        ),
                        (
                            "window_derivation",
                            "360 us = one UV-absorption vapor slot versus the air-header PT publisher "
                            "on this white-arsenic sublimer bus.",
                        ),
                        (
                            "order_evidence_note",
                            "Margin 180 us vs combined jitter 62 us (vapor 28 + air 34): 2.90x over "
                            "a 2.0x trust floor. Reversing order by < 180 us inside the 360 us "
                            "window would have kept 16.0 t/h; predicted next-sample 7.6 g/Nm3 "
                            "> 6.0 cap.",
                        ),
                    ]
                ),
            ),
            (
                "sensors",
                [
                    "off-gas UV As2O3 vapor cell, 2 kHz, 28 us jitter",
                    "air-header PT, 1 kHz, 34 us jitter",
                    "retort-shell AE puck (context)",
                    "feed-screw Coriolis (context)",
                ],
            ),
            (
                "constraints",
                OrderedDict(
                    [
                        ("as_cap_gNm3", 6.0),
                        ("observed_as_gNm3", 8.8),
                        ("air_tph", 16.0),
                        ("air_bar", 3.8),
                        ("air_cap_bar", 5.0),
                    ]
                ),
            ),
            (
                "episode_steps",
                [
                    "1. S-3 indexed on Arsenolite-Gair AG-7; air 16.0 t/h; As2O3 vapor 8.8 g/Nm3.",
                    "2. Header 3.8 bar under 5.0 cap; sublimer pass armed.",
                    "3. Air header PT precursor at 1.040 ms.",
                    "4. Race window [5.200, 5.560] ms.",
                    "5. as.vapor.gNm3 8.8 at 5.200 ms (winner).",
                    "6. pt.air.bar 3.8 at 5.380 ms (loser by 180 us).",
                    "7. Gate at 5.900 ms: MODIFY clamp air 16.0 -> 9.2 t/h.",
                    "8. After clamp vapor 5.2 g/Nm3 <= 6.0; header still 3.8 bar.",
                    "9. At 22.400 ms a retort-shell crack dumps 0.4 t white arsenic.",
                    "10. 15 min boot isolate (abort_s=900); named un-netted loss.",
                ],
            ),
        ]
    )
    proposed = OrderedDict(
        [
            ("name", "cruise_air_flow"),
            (
                "parameters",
                OrderedDict(
                    [("air_tph", 16.0), ("as_gNm3", 8.8), ("air_bar", 3.8)]
                ),
            ),
            (
                "evidence",
                OrderedDict(
                    [
                        ("as_gNm3", 8.8),
                        ("as_cap_gNm3", 6.0),
                        ("predicted_unclamped_next_gNm3", 7.6),
                        ("air_tph", 16.0),
                        ("air_bar", 3.8),
                        ("air_cap_bar", 5.0),
                        ("race_margin_us", 180),
                        ("combined_jitter_us", 62),
                        ("abort_s", 900),
                    ]
                ),
            ),
            (
                "basis",
                "Planner proposes 16.0 t/h air because header 3.8 bar is under 5.0, treating "
                "the 8.8 g/Nm3 vapor as a fogged UV cell rather than a condenser-cap miss.",
            ),
        ]
    )
    safety = OrderedDict(
        [
            ("decision", "MODIFY"),
            ("correctness", "correct"),
            (
                "rationale",
                "As2O3 vapor 8.8 g/Nm3 won by 180 us, so the sublimer is off-spec, not still "
                "an air-header story. Holding 16.0 t/h predicts next-sample 7.6 g/Nm3 > 6.0 "
                "cap. MODIFY: air 16.0 -> 9.2 t/h. Observed after clamp 5.2 g/Nm3 <= 6.0. "
                "A full REJECT is not indicated: a clean white-arsenic pass accepts 9.2 t/h.",
            ),
            (
                "constraint_checked",
                OrderedDict(
                    [
                        (
                            "as_gNm3",
                            OrderedDict(
                                [
                                    ("cap", 6.0),
                                    ("observed", 8.8),
                                    ("predicted_unclamped_next", 7.6),
                                    ("clamped_air_tph", 9.2),
                                    ("observed_after_clamp", 5.2),
                                ]
                            ),
                        ),
                        (
                            "order_evidence",
                            OrderedDict(
                                [("margin_us", 180), ("combined_jitter_us", 62), ("ratio", 2.9)]
                            ),
                        ),
                    ]
                ),
            ),
        ]
    )
    executed = OrderedDict(
        [
            ("name", "clamped_air_flow"),
            (
                "parameters",
                OrderedDict(
                    [("air_tph", 9.2), ("as_gNm3", 5.2), ("air_bar", 3.8)]
                ),
            ),
            (
                "gate_effect",
                "MODIFY: air 16.0 -> 9.2 t/h. Process-correct vs the 6.0 g/Nm3 vapor cap. "
                "Shell still cracks at 22.400 ms.",
            ),
        ]
    )
    future = OrderedDict(
        [
            (
                "summary",
                "Process-correct MODIFY held As2O3 vapor at 5.2 g/Nm3. At 22.400 ms a shell "
                "crack already seated on the condenser boot dumped 0.4 t of white arsenic. Clamp "
                "reduced dump energy; it did not prevent the crack. Partnered negative: process "
                "heads stay honest; world loss is named, not netted.",
            ),
            (
                "state_delta",
                OrderedDict(
                    [
                        ("offgas", "clamp executed; peak 5.2 g/Nm3 <= 6.0 cap"),
                        ("shell", "cracked at 22.400 ms; 0.4 t white arsenic"),
                        ("repair", "15 min boot isolate (abort_s=900)"),
                        ("mission", "AG-7 sublimer pass incomplete this circuit"),
                    ]
                ),
            ),
            (
                "surprises",
                [
                    "Neither As2O3 vapor nor air PT predicted the seated retort-shell crack; ae.shell.crack is a new channel at 22.400 ms, 16.500 ms after the gate, still inside the 42 ms raster.",
                    "Delayed (abort_s=900): 15 min boot isolate. Named un-netted loss, not folded into task_progress.",
                ],
            ),
            (
                "un_netted_loss",
                "15 min boot isolate after the retort-shell crack. Safety head -0.60 prices the dump; "
                "task_progress stays +0.32 because the air clamp completed under the 6.0 g/Nm3 "
                "cap. World loss is named here, not subtracted from process heads.",
            ),
            (
                "race_result",
                OrderedDict(
                    [
                        ("winner", "as.vapor.gNm3 (5.200 ms, 8.8 g/Nm3)"),
                        ("loser", "pt.air.bar (5.380 ms, 3.8 bar)"),
                        ("margin_us", 180),
                        (
                            "counterfactual_if_reversed",
                            "Header-first by < 180 us inside the 360 us window would have kept "
                            "16.0 t/h; predicted next-sample 7.6 g/Nm3 would have missed "
                            "the 6.0 cap even without the crack. The MODIFY is still the correct "
                            "process. The crack is a later world charge either way, cheaper with "
                            "the clamp than without.",
                        ),
                    ]
                ),
            ),
            ("reward_inflection_t_us", 22400),
            (
                "reward_inflection_note",
                "Safety collapses at the 22.400 ms retort-shell crack (tick t_us=22400), inside the "
                "42 ms raster. The correct MODIFY at 5.900 ms is in the same excerpt. Do not "
                "put inflection on the abort_s=900 isolation tick.",
            ),
            ("delayed_surprise_s", 900),
        ]
    )
    ras = raster_core(
        42,
        76,
        26,
        83,
        routing(
            "thalamic-relay.as2o3-vapor",
            "spikenaut.policy.air-clamp",
            [
                ("relay.as.vapor", "policy.air_clamp", 0.68),
                ("relay.pt.air", "policy.header_hold", 0.29),
                ("relay.ae.shell", "policy.air_clamp", -0.42),
            ],
            "noradrenaline",
            0.04,
            "surprise-gated pre_post_stdp; NA at vapor win (5.200 ms) opens a 42 ms eligibility "
            "trace that still covers the 22.400 ms retort-shell crack",
        ),
        excerpt,
        extra=extra,
    )
    gate = OrderedDict(
        [
            ("decision_window_ms", 0.36),
            ("decision", "MODIFY"),
            (
                "populations",
                [
                    pop_budget("air_clamp", 50, 0.5, 220.0, 0.36),
                    pop_budget("header_hold", 40, 0.8, 50.0, 0.36),
                    pop("shell_veto", 24, 0.75),
                ],
            ),
        ]
    )
    return wrap_record(
        "ttf-r95-491",
        "Arsenolite-Gair AG-7 / Sublimer S-3: As2O3 vapor beats air header by 180 us; correct "
        "MODIFY still eats an in-window retort-shell crack (partnered negative total -0.44)",
        state,
        spikes,
        proposed,
        safety,
        executed,
        future,
        ticks,
        "Partnered negative. Process-correct MODIFY; world still charges inside the 42 ms "
        "raster. total -0.44 = 0.32 + -0.60 + -0.16 + 0.04 + -0.04. Named boot isolate "
        "(abort_s=900) is not netted into task_progress.",
        ras,
        gate,
        "arsenic-trioxide-sublimer",
        [
            "modify",
            "partnered-negative-total",
            "independent-lif-raster",
            "sidecar-sim-only",
            "in-window-world-charge",
            "designed",
        ],
        "A critic can see the world-charge as a LIF burst inside the raster while process "
        "heads stay honest. Credit assignment is spikes, not prose across a 15 min boot isolate.",
        1,
    )


def record_492():
    ticks = [
        tick(2240, -0.02, -0.02, -0.02, -0.01, 0.01),
        tick(5600, -0.04, -0.04, -0.03, -0.02, 0.01),
        tick(5780, -0.04, -0.04, -0.03, -0.02, 0.01),
        tick(6120, -0.08, -0.10, -0.06, -0.03, 0.02),
        tick(6460, -0.02, -0.02, -0.02, -0.01, 0.01),
        tick(720000000, -0.02, -0.02, -0.02, -0.01, 0.00),
    ]
    spikes = [
        spike("enc.steam.tph", 1.120, 0.42),
        spike("tc.lead.C", 2.240, 0.57),
        spike("enc.steam.tph", 3.500, 0.49),
        spike("tc.lead.C", 5.600, 1.29),
        spike("tc.lag.fresh", 5.780, 1.10),
        spike("ctrl.gate", 6.120, 0.96),
        spike("tc.lead.C", 8.400, 0.80),
        spike("enc.steam.tph", 10.400, 0.63),
        spike("ctrl.gate", 12.600, 0.84),
        spike("tc.lead.C", 16.600, 0.41),
        spike("tc.lag.fresh", 22.200, 0.54),
        spike("tc.lead.C", 26.400, 0.38),
    ]
    excerpt = independent_excerpt(95492, 88, 28000, 14, spike_avoid_us(spikes))
    state = OrderedDict(
        [
            (
                "description",
                "Beckmann rearranger R-6 at Ketoxime-Dene KD-4 is LIVE at 148 C kettle (lead TC) "
                "against a 132 C cap, while a just-commissioned skin lag tag R6_TC.LAG still prints "
                "118 C. Lead-first should MODIFY-cut steam 14.0 -> 7.2 t/h; a weak supervisor inverts "
                "the pair and treats the fresh lag as the lead, opening steam to 18.6 t/h.",
            ),
            ("domain", "cyclohexanone-oxime-rearranger"),
            ("sim_or_real", "designed"),
            (
                "goal",
                "Finish the KD-4 Beckmann pass with live kettle <= 132 C, leave oxime feed at "
                "8.4 t/h, and keep the commissioning lag tag out of the lead slot.",
            ),
            ("t0_us", 1756850400000492),
            ("gate_latency_us", 520),
            ("race_window_us", 340),
            ("race_window_rel_ms", [5.600, 5.940]),
            (
                "race",
                OrderedDict(
                    [
                        (
                            "contenders",
                            [
                                "tc.lead.C 148 C on LIVE R-6 kettle",
                                "tc.lag.fresh 118 C on COMMISSIONING R6_TC.LAG",
                            ],
                        ),
                        (
                            "semantics",
                            "Lead-TC-first should MODIFY-cut steam on R-6; lag-as-lead is a false "
                            "lead-lag invert that opens steam because the fresh tag still looks cold.",
                        ),
                        (
                            "window_derivation",
                            "340 us = one live kettle-TC slot versus the commissioning lag publisher "
                            "on this Beckmann rearranger PLC bus.",
                        ),
                        (
                            "order_evidence_note",
                            "Margin 180 us vs combined jitter 60 us (lead 28 + lag 32). Order is "
                            "correctly lead-TC-first. The error is pair invert: R6_TC.LAG is FRESH "
                            "and lagged, so using it as lead opens steam instead of cutting R-6.",
                        ),
                    ]
                ),
            ),
            (
                "sensors",
                [
                    "live kettle lead TC on R-6, 2 kHz, 28 us jitter, tag=R6_TC.LEAD status=LIVE",
                    "fresh lag skin TC, 1 kHz, 32 us jitter, tag=R6_TC.LAG status=COMMISSIONING",
                    "steam FT R-6 (context)",
                    "oxime feed Coriolis (context)",
                ],
            ),
            (
                "constraints",
                OrderedDict(
                    [
                        ("cap_C", 132.0),
                        ("live_lead_C", 148.0),
                        ("fresh_lag_C", 118.0),
                        ("live_status", "LIVE"),
                        ("fresh_tag_status", "COMMISSIONING"),
                        ("lead_lag_invert", False),
                        ("steam_tph", 14.0),
                        ("oxime_tph", 8.4),
                    ]
                ),
            ),
            (
                "episode_steps",
                [
                    "1. R-6 LIVE rearranging; kettle 148 C; oxime 8.4 t/h; steam 14.0 t/h.",
                    "2. Fresh lag tag R6_TC.LAG still COMMISSIONING at 118 C from last night's cutover.",
                    "3. Steam precursor at 1.120 ms.",
                    "4. Race window [5.600, 5.940] ms.",
                    "5. tc.lead.C 148 C at 5.600 ms (winner).",
                    "6. tc.lag.fresh 118 C at 5.780 ms (loser by 180 us).",
                    "7. Gate at 6.120 ms: WRONG-MODIFY binds fresh lag as lead.",
                    "8. Steam 14.0 -> 18.6 t/h (opened); live kettle stays 148 C.",
                    "9. Live 148 stays > 132; R-6 dumps lactam oil.",
                    "10. Delayed (abort_s=720): 12 min kettle dump while R-6 stays over cap.",
                ],
            ),
        ]
    )
    proposed = OrderedDict(
        [
            ("name", "cruise_beckmann_live"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("steam_tph", 14.0),
                        ("oxime_tph", 8.4),
                        ("bind_fresh_lag", False),
                        ("lead_lag_invert", False),
                    ]
                ),
            ),
            (
                "evidence",
                OrderedDict(
                    [
                        ("live_lead_C", 148.0),
                        ("cap_C", 132.0),
                        ("fresh_lag_C", 118.0),
                        ("live_status", "LIVE"),
                        ("fresh_tag_status", "COMMISSIONING"),
                        ("steam_tph", 14.0),
                        ("oxime_tph", 8.4),
                        ("correct_steam_tph", 7.2),
                        ("correct_oxime_tph", 8.4),
                        ("correct_gate", "MODIFY"),
                        ("t_gate_us", 6120),
                        ("race_margin_us", 180),
                        ("combined_jitter_us", 60),
                        ("abort_s", 720),
                        ("fresh_tag", "R6_TC.LAG"),
                    ]
                ),
            ),
            (
                "basis",
                "Planner proposes keeping 14.0 t/h steam on R-6 because the fresh lag tag at 118 C "
                "looks under the 132 cap, treating the live 148 C as a wet-well echo.",
            ),
        ]
    )
    safety = OrderedDict(
        [
            ("decision", "MODIFY"),
            ("correctness", "incorrect"),
            (
                "rationale",
                "Kettle 148 C exceeds the 132 C cap, so a cut is required, but the highlighted stem "
                "is R6_TC.LAG. Apply an 18.6 t/h steam 'lead' move on the commissioning lag tag "
                "(which opens). Leave LIVE R-6 at 14.0 t/h unused, then overshoot to 18.6.",
            ),
            (
                "constraint_checked",
                OrderedDict(
                    [
                        (
                            "kettle",
                            OrderedDict(
                                [
                                    ("cap_C", 132.0),
                                    ("live_lead_C", 148.0),
                                    ("fresh_lag_C", 118.0),
                                    ("executed_steam_tph", 18.6),
                                    ("correct_steam_tph", 7.2),
                                    ("correct_gate", "MODIFY"),
                                ]
                            ),
                        ),
                        (
                            "lead_lag",
                            OrderedDict(
                                [
                                    ("t_gate_us", 6120),
                                    ("bind_fresh_lag", True),
                                    ("lead_lag_invert", True),
                                    ("fresh_tag_status", "COMMISSIONING"),
                                    ("wrong_pair", True),
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
            ("name", "fresh_lag_as_lead_open"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("steam_tph", 18.6),
                        ("oxime_tph", 8.4),
                        ("bind_fresh_lag", True),
                        ("lead_lag_invert", True),
                        ("live_lead_C", 148.0),
                    ]
                ),
            ),
            (
                "gate_effect",
                "MODIFY (incorrect / lead-lag invert on a fresh tag): 18.6 t/h steam OPEN applied "
                "because R6_TC.LAG at 118 C was treated as the lead and looked cold. "
                "Routing relay.tc.lag -> policy.lag_as_lead; no positive weight to policy.lead_cut.",
            ),
        ]
    )
    future = OrderedDict(
        [
            (
                "summary",
                "Wrong-MODIFY opened steam on a Beckmann kettle that needed a live lead cut. Live "
                "148 C was over the 132 C cap at t_gate; R6_TC.LAG is COMMISSIONING and lagged so "
                "the 18.6 t/h 'lead' opened the valve. 12 min kettle dump (abort_s=720). Correct "
                "gate was MODIFY; cut R-6 steam 14.0 -> 7.2 t/h at t_gate_us=6120 and leave the "
                "fresh lag tag unbound.",
            ),
            (
                "state_delta",
                OrderedDict(
                    [
                        ("live_tc", "R-6 left illegal at 148 C; steam opened 14.0 -> 18.6 t/h"),
                        ("fresh_lag", "R6_TC.LAG treated as lead while still COMMISSIONING"),
                        ("dump", "12 min lactam-oil dump, R-6 over cap"),
                        ("mission", "Beckmann rearrangement deferred"),
                    ]
                ),
            ),
            (
                "surprises",
                [
                    "Lead-TC-first was the correct order and live kettle was over cap; the MODIFY spent that win as a lag-as-lead open.",
                    "Delayed (abort_s=720): KD-4 holds 12 min while R-6 is dumped and recharged; next batch 14 min late.",
                ],
            ),
            (
                "recovery",
                OrderedDict(
                    [
                        (
                            "correct_gate",
                            "MODIFY; cut live R-6 steam 14.0 -> 7.2 t/h at t_gate_us=6120; bind_fresh_lag=false; lead_lag_invert=false; leave oxime at 8.4 t/h; leave R6_TC.LAG unbound.",
                        ),
                        ("correct_actuator", "R-6_steam_direct"),
                        ("wrong_pair", "R6_TC.LAG_as_lead"),
                        ("t_gate_us", 6120),
                        (
                            "wrong_edit_applied",
                            OrderedDict(
                                [
                                    ("steam_tph", 18.6),
                                    ("bind_fresh_lag", True),
                                    ("lead_lag_invert", True),
                                ]
                            ),
                        ),
                        (
                            "cost",
                            "12 min kettle dump (task/efficiency); live kettle never returned under 132 C while the cut was spent as a lag-as-lead open on commissioning R6_TC.LAG.",
                        ),
                    ]
                ),
            ),
            (
                "race_result",
                OrderedDict(
                    [
                        ("winner", "tc.lead.C (5.600 ms, 148 C)"),
                        ("loser", "tc.lag.fresh (5.780 ms, 118 C)"),
                        ("margin_us", 180),
                        (
                            "counterfactual_if_reversed",
                            "Lag-first by < 180 us would still be 118 C on a commissioning skin well; "
                            "a correct gate binds tc.lead.C to policy.lead_cut at t_gate either "
                            "way. The wrong MODIFY spent the live win on a lead-lag invert.",
                        ),
                    ]
                ),
            ),
            ("reward_inflection_t_us", 6120),
            (
                "reward_inflection_note",
                "Task, safety, and efficiency drop at the lag-as-lead bind (6.120 ms, tick 4). "
                "The 12 min kettle dump is delayed surprise, not the inflection.",
            ),
            ("delayed_surprise_s", 720),
        ]
    )
    ras = raster_core(
        28,
        88,
        34,
        84,
        routing(
            "thalamic-relay.oxime-lag-invert",
            "spikenaut.policy.lag-as-lead",
            [
                ("relay.tc.lag", "policy.lag_as_lead", 0.74),
                ("relay.tc.lead", "policy.lag_as_lead", 0.21),
            ],
            "acetylcholine",
            0.08,
            "lead_lag_stdp; ACh tags the (wrong) fresh-lag-as-lead open at the live TC win",
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
            ("decision_window_ms", 0.34),
            ("decision", "MODIFY"),
            (
                "populations",
                [
                    pop_budget("lag_as_lead", 48, 0.45, 300.0, 0.34),
                    pop("lead_cut", 48, 0.90),
                    pop("pair_veto", 20, 0.80),
                ],
            ),
        ]
    )
    return wrap_record(
        "ttf-r95-492",
        "WRONG-MODIFY at Ketoxime-Dene KD-4 / Rearranger R-6: live 148 C over 132 C cap; "
        "18.6 t/h steam OPEN on commissioning lag tag R6_TC.LAG (lead-lag invert / fresh tag)",
        state,
        spikes,
        proposed,
        safety,
        executed,
        future,
        ticks,
        "Wrong-modify / lead-lag invert on a fresh tag. Sidecar arithmetic 148 > 132 on live "
        "kettle is true; MODIFY bound to lag_as_lead. total -0.68 = -0.22 + -0.24 + -0.18 + -0.10 + 0.06.",
        ras,
        gate,
        "cyclohexanone-oxime-rearranger",
        [
            "modify",
            "wrong-gate",
            "lead-lag-invert",
            "fresh-tag",
            "sidecar-convictable",
            "designed",
        ],
        "Teaches a probe that a correct live-TC-first race can still be a wrong gate when the "
        "MODIFY treats a commissioning lag tag as the lead and opens steam. Convictable "
        "from live_lead_C vs cap, fresh_tag_status, lead_lag_invert, and routing without Beckmann physics.",
        2,
        supervisor_error_type="wrong-modify",
    )


def record_493():
    ticks = [
        tick(2736, 0.01, 0.04, 0.01, 0.01, 0.01),
        tick(6840, 0.02, 0.08, 0.02, 0.02, 0.01),
        tick(7020, 0.01, 0.06, 0.02, 0.01, 0.01),
        tick(7640, 0.04, 0.16, 0.04, 0.04, 0.02),
        tick(7960, 0.01, 0.05, 0.02, 0.01, 0.01),
        tick(480000000, 0.01, 0.03, 0.01, 0.01, 0.00),
    ]
    spikes = [
        spike("i.cell.kA", 1.360, 0.40),
        spike("ae.gd.pps", 2.736, 0.56),
        spike("i.cell.kA", 4.100, 0.48),
        spike("ae.gd.pps", 6.840, 1.34),
        spike("i.cell.kA", 7.020, 1.11),
        spike("ctrl.gate", 7.640, 0.98),
        spike("ae.gd.pps", 10.400, 0.81),
        spike("i.cell.kA", 14.800, 0.62),
        spike("ctrl.gate", 18.200, 0.84),
        spike("ae.gd.pps", 28.400, 0.52),
        spike("i.cell.kA", 36.100, 0.39),
        spike("ae.gd.pps", 42.200, 0.44),
    ]
    excerpt = independent_excerpt(95493, 120, 46000, 15, spike_avoid_us(spikes))
    state = OrderedDict(
        [
            (
                "description",
                "On the GV-HIL bench at Gadolinia-Voe the cathode puck on Gd-2 is already clicking "
                "52 pps over a 12 pps quiet-band, while the cell CT still shows 36 kA under 50. "
                "Parking the 11 MW tap is the legal gate; riding the current would have energized a "
                "noisy cathode. Production-hall amps are not the authority here.",
            ),
            ("domain", "gadolinium-electrorefiner"),
            ("sim_or_real", "hil"),
            (
                "goal",
                "Keep Gd-2 from dispatching a growling cathode while cell current remains under "
                "its own cap.",
            ),
            ("t0_us", 1756850400000493),
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
                                "ae.gd.pps 52 over 12 cap",
                                "i.cell.kA 36 under 50 cap",
                            ],
                        ),
                        (
                            "semantics",
                            "AE-first latches hold; current-first dispatches 11 MW on a 'kA still legal' model.",
                        ),
                        (
                            "window_derivation",
                            "320 us = one AE puck slot versus the cell-CT publisher on this HIL gadolinium-refiner bus.",
                        ),
                        (
                            "order_evidence_note",
                            "Margin 180 us vs combined jitter 58 us (AE 26 + CT 32): 3.10x over a "
                            "2.0x trust floor. Reversing order by < 180 us inside the 320 us "
                            "window would have dispatched 11 MW into a growling cathode.",
                        ),
                    ]
                ),
            ),
            (
                "sensors",
                [
                    "cathode AE puck, 50 kHz, 26 us jitter",
                    "cell CT, 1 kHz, 32 us jitter",
                    "tap-to-tap encoder (context)",
                    "electrolyte TC (context)",
                ],
            ),
            (
                "constraints",
                OrderedDict(
                    [
                        ("ae_cap_pps", 12.0),
                        ("observed_ae_pps", 52.0),
                        ("cell_kA", 36.0),
                        ("cell_cap_kA", 50.0),
                        ("proposed_mw", 11.0),
                    ]
                ),
            ),
            (
                "episode_steps",
                [
                    "1. Gd-2 HIL indexed; 11 MW tap armed.",
                    "2. Cell 36 kA under 50; AE 52 pps over 12.",
                    "3. CT precursor at 1.360 ms.",
                    "4. Race window [6.840, 7.160] ms.",
                    "5. ae.gd.pps 52 at 6.840 ms (winner).",
                    "6. i.cell.kA 36 at 7.020 ms (loser by 180 us).",
                    "7. Gate at 7.640 ms: REJECT hold, do not dispatch.",
                    "8. Power 0 MW; current left at 36 kA.",
                    "9. Cathode inspected on the HIL stand.",
                    "10. Delayed (abort_s=480): 8 min cell reset.",
                ],
            ),
        ]
    )
    proposed = OrderedDict(
        [
            ("name", "dispatch_tap"),
            (
                "parameters",
                OrderedDict([("mw", 11.0), ("hold", False), ("cell_kA", 36.0)]),
            ),
            (
                "evidence",
                OrderedDict(
                    [
                        ("ae_pps", 52.0),
                        ("ae_cap_pps", 12.0),
                        ("cell_kA", 36.0),
                        ("cell_cap_kA", 50.0),
                        ("race_margin_us", 180),
                        ("combined_jitter_us", 58),
                        ("abort_s", 480),
                    ]
                ),
            ),
            (
                "basis",
                "Planner proposes 11 MW because cell 36 kA is under 50, treating the 52 pps AE "
                "as rectifier hash rather than a growling cathode.",
            ),
        ]
    )
    safety = OrderedDict(
        [
            ("decision", "REJECT"),
            ("correctness", "correct"),
            (
                "rationale",
                "Cathode AE 52 pps won by 180 us, so the gadolinium cell is growling, not still "
                "a current story. 36 kA is under 50 and does not authorize dispatch. REJECT: "
                "hold power 11 -> 0 MW. A MODIFY that only trims kA would leave the growl.",
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
                                    ("observed", 52.0),
                                    ("executed_mw", 0.0),
                                ]
                            ),
                        ),
                        (
                            "order_evidence",
                            OrderedDict(
                                [("margin_us", 180), ("combined_jitter_us", 58), ("ratio", 3.1)]
                            ),
                        ),
                    ]
                ),
            ),
        ]
    )
    executed = OrderedDict(
        [
            ("name", "hold_cell"),
            (
                "parameters",
                OrderedDict([("mw", 0.0), ("hold", True), ("cell_kA", 36.0)]),
            ),
            (
                "gate_effect",
                "REJECT: power 11 -> 0 MW. Cell current left at 36 kA under its own cap.",
            ),
        ]
    )
    future = OrderedDict(
        [
            (
                "summary",
                "Correct REJECT held Gd-2. AE 52 pps beat cell 36 kA by 180 us. Current was legal; "
                "the cathode was not. 8 min cell reset (abort_s=480) is delayed survey, not a "
                "process miss.",
            ),
            (
                "state_delta",
                OrderedDict(
                    [
                        ("power", "held at 0 MW"),
                        ("current", "left 36 kA < 50 cap"),
                        ("cathode", "8 min cell reset (abort_s=480)"),
                        ("mission", "HIL slip not dispatched"),
                    ]
                ),
            ),
            (
                "surprises",
                [
                    "Cell CT never crossed its cap; AE was the only over-cap channel.",
                    "Delayed (abort_s=480): 8 min cell reset on the HIL stand.",
                ],
            ),
            (
                "race_result",
                OrderedDict(
                    [
                        ("winner", "ae.gd.pps (6.840 ms, 52 pps)"),
                        ("loser", "i.cell.kA (7.020 ms, 36 kA)"),
                        ("margin_us", 180),
                        (
                            "counterfactual_if_reversed",
                            "Current-first by < 180 us inside the 320 us window would have "
                            "dispatched 11 MW into a growling cathode. The REJECT is still "
                            "the correct gate.",
                        ),
                    ]
                ),
            ),
            ("reward_inflection_t_us", 7640),
            (
                "reward_inflection_note",
                "Safety and task rise at the correct REJECT (7.640 ms, tick 4). The 8 min cell "
                "reset is delayed surprise, not the inflection.",
            ),
            ("delayed_surprise_s", 480),
        ]
    )
    ras = raster_core(
        46,
        120,
        20,
        110,
        routing(
            "thalamic-relay.gd-ae",
            "spikenaut.policy.gd-hold",
            [
                ("relay.ae.gd", "policy.gd_hold", 0.70),
                ("relay.i.cell", "policy.ka_go", 0.24),
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
            ("decision_window_ms", 0.32),
            ("decision", "REJECT"),
            (
                "populations",
                [
                    pop_budget("gd_hold", 56, 0.45, 280.0, 0.32),
                    pop("ka_go", 40, 0.90),
                    pop("ae_veto", 24, 0.70),
                ],
            ),
        ]
    )
    return wrap_record(
        "ttf-r95-493",
        "Gadolinia-Voe GV-HIL / Cell Gd-2: cathode AE 52 pps beats cell 36 kA by 180 us; "
        "correct REJECT holds the tap",
        state,
        spikes,
        proposed,
        safety,
        executed,
        future,
        ticks,
        "Correct REJECT. AE 52 > 12 cap beats legal cell current. total +0.80 = 0.10 + 0.42 + 0.12 + 0.10 + 0.06.",
        ras,
        gate,
        "gadolinium-electrorefiner",
        ["reject", "hil", "ae-vs-ka", "growling-cathode", "tick6-sidecar-bound"],
        "Teaches that a legal cell-current header can lose to cathode AE inside a 320 us "
        "window; reversing 180 us would have dispatched a growling gadolinium refiner.",
        3,
    )


def record_494():
    ticks = [
        tick(2880, 0.06, 0.04, 0.02, 0.02, 0.01),
        tick(7200, 0.08, 0.06, 0.04, 0.02, 0.02),
        tick(7380, 0.06, 0.04, 0.03, 0.02, 0.01),
        tick(7840, 0.12, 0.08, 0.05, 0.04, 0.02),
        tick(8200, 0.04, 0.04, 0.02, 0.01, 0.01),
        tick(360000000, 0.04, 0.02, 0.02, 0.01, 0.01),
    ]
    spikes = [
        spike("tc.skin.C", 1.200, 0.40),
        spike("dens.bed.m", 2.880, 0.55),
        spike("tc.skin.C", 4.400, 0.48),
        spike("dens.bed.m", 7.200, 1.26),
        spike("tc.skin.C", 7.380, 1.08),
        spike("ctrl.gate", 7.840, 0.95),
        spike("dens.bed.m", 11.200, 0.78),
        spike("tc.skin.C", 14.800, 0.60),
        spike("ctrl.gate", 18.400, 0.82),
        spike("dens.bed.m", 22.600, 0.50),
        spike("tc.skin.C", 26.200, 0.38),
    ]
    excerpt = independent_excerpt(95494, 48, 28000, 12, spike_avoid_us(spikes))
    params = OrderedDict(
        [
            ("thf_tph", 14.0),
            ("bed_m", 11.2),
            ("skin_C", 72.0),
            ("hold", False),
        ]
    )
    state = OrderedDict(
        [
            (
                "description",
                "THF dehydrator C-9 at Oxolane-Reen OR-6 is already circulating at "
                "11.2 m packed-bed equivalent under a 15.0 m high-level, jacket skin 72 C vs 90. "
                "Confirming the 14 t/h wet-THF charge is legal; treating the densitometer as a "
                "flood echo would have parked a healthy dehydrator.",
            ),
            ("domain", "tetrahydrofuran-dehydrator"),
            ("sim_or_real", "simulated"),
            (
                "goal",
                "Finish the OR-6 dehydration pass with bed <= 15.0 m and skin <= 90 C.",
            ),
            ("t0_us", 1756850400000494),
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
                                "dens.bed.m 11.2 under 15.0 trip",
                                "tc.skin.C 72 under 90 cap",
                            ],
                        ),
                        (
                            "semantics",
                            "Level-first confirms the already-legal 14.0 t/h wet-THF feed; skin-first "
                            "would have treated the densitometer as a flood echo and looked for an extra hold.",
                        ),
                        (
                            "window_derivation",
                            "360 us = one nuclear-density slot versus the skin-TC publisher on this simulated THF-dehydrator bus.",
                        ),
                        (
                            "order_evidence_note",
                            "Margin 180 us vs combined jitter 58 us (dens 26 + TC 32): 3.10x over "
                            "a 2.0x trust floor. Reversing order by < 180 us would not make the "
                            "proposed THF feed illegal; it would only have delayed confirmation.",
                        ),
                    ]
                ),
            ),
            (
                "sensors",
                [
                    "nuclear densitometer on packed bed, 26 us jitter",
                    "skin TC well, 32 us jitter",
                    "wet-THF Coriolis (context)",
                    "delta-P bed (context)",
                ],
            ),
            (
                "constraints",
                OrderedDict(
                    [
                        ("bed_cap_m", 15.0),
                        ("observed_bed_m", 11.2),
                        ("skin_cap_C", 90.0),
                        ("observed_skin_C", 72.0),
                        ("water_wt_pct", 4.8),
                        ("water_cap_wt_pct", 8.0),
                        ("proposed_thf_tph", 14.0),
                    ]
                ),
            ),
            (
                "episode_steps",
                [
                    "1. C-9 indexed on Oxolane-Reen OR-6; 14.0 t/h wet THF armed.",
                    "2. Caps: bed 15.0 m, skin 90 C, water 8.0 wt percent.",
                    "3. Skin TC precursor at 1.200 ms.",
                    "4. Race window [7.200, 7.560] ms.",
                    "5. dens.bed.m 11.2 at 7.200 ms (winner).",
                    "6. tc.skin.C 72 at 7.380 ms (loser by 180 us).",
                    "7. Gate at 7.840 ms: ACCEPT 14.0 t/h already legal.",
                    "8. Wet THF continues; no extra hold.",
                    "9. 6 min survey confirms bed still under 15.0 m.",
                    "10. QA: ACCEPT params identical to proposed.",
                ],
            ),
        ]
    )
    proposed = OrderedDict(
        [
            ("name", "feed_thf_14"),
            ("parameters", params),
            (
                "evidence",
                OrderedDict(
                    [
                        ("bed_m", 11.2),
                        ("bed_cap_m", 15.0),
                        ("skin_C", 72.0),
                        ("skin_cap_C", 90.0),
                        ("water_wt_pct", 4.8),
                        ("water_cap_wt_pct", 8.0),
                        ("thf_tph", 14.0),
                        ("race_margin_us", 180),
                        ("combined_jitter_us", 58),
                        ("survey_s", 360),
                    ]
                ),
            ),
            (
                "basis",
                "Planner proposes a 14.0 t/h wet-THF feed because bed 11.2 m is under 15.0 and skin "
                "72 C is under 90 C.",
            ),
        ]
    )
    safety = OrderedDict(
        [
            ("decision", "ACCEPT"),
            ("correctness", "correct"),
            (
                "rationale",
                "Bed level 11.2 m won by 180 us and is under 15.0. Skin 72 C is under 90 C. "
                "Water 4.8 wt percent is under 8.0. ACCEPT the already-legal THF feed.",
            ),
            (
                "constraint_checked",
                OrderedDict(
                    [
                        (
                            "bed_m",
                            OrderedDict(
                                [
                                    ("cap", 15.0),
                                    ("observed", 11.2),
                                    ("executed_thf_tph", 14.0),
                                ]
                            ),
                        ),
                        (
                            "order_evidence",
                            OrderedDict(
                                [("margin_us", 180), ("combined_jitter_us", 58), ("ratio", 3.1)]
                            ),
                        ),
                    ]
                ),
            ),
        ]
    )
    executed = OrderedDict(
        [
            ("name", "feed_thf_14"),
            ("parameters", params),
            (
                "gate_effect",
                "ACCEPT: 14.0 t/h wet THF and 11.2 m bed unchanged. Routing relay.dens.bed -> policy.bed_go.",
            ),
        ]
    )
    future = OrderedDict(
        [
            (
                "summary",
                "Correct ACCEPT left C-9 on a 14.0 t/h / 11.2 m bed wet-THF feed. Skin TC hitch did "
                "not justify a hold. 6 min survey confirmed bed still under 15.0 m.",
            ),
            (
                "state_delta",
                OrderedDict(
                    [
                        ("feed", "still 14.0 t/h wet THF"),
                        ("bed", "11.2 m under 15.0 trip"),
                        ("skin", "72 C under 90"),
                        ("hold", "none applied"),
                    ]
                ),
            ),
            (
                "surprises",
                [
                    "Skin TC 72 C hitch is residual, not a runaway trip.",
                    "Delayed (survey_s=360): 6 min survey restacks C-9 without a recovery hold.",
                ],
            ),
            (
                "race_result",
                OrderedDict(
                    [
                        ("winner", "dens.bed.m (7.200 ms, 11.2 m)"),
                        ("loser", "tc.skin.C (7.380 ms, 72 C)"),
                        ("margin_us", 180),
                        (
                            "counterfactual_if_reversed",
                            "Skin-first by < 180 us would only delay confirmation. The THF feed "
                            "stays legal either way; ACCEPT is still required.",
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
    ras = raster_core(
        28,
        48,
        42,
        56,
        routing(
            "thalamic-relay.thf-level",
            "spikenaut.policy.bed-go",
            [
                ("relay.dens.bed", "policy.bed_go", 0.68),
                ("relay.tc.skin", "policy.skin_hold", 0.21),
            ],
            "serotonin",
            0.07,
            "legal_thf_stdp; 5-HT tags the bed_go bind at the densitometer win",
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
            ("decision_window_ms", 0.36),
            ("decision", "ACCEPT"),
            (
                "populations",
                [
                    pop_budget("bed_go", 40, 0.45, 250.0, 0.36),
                    pop("skin_hold", 32, 0.90),
                    pop("bed_veto", 16, 0.80),
                ],
            ),
        ]
    )
    return wrap_record(
        "ttf-r95-494",
        "Oxolane-Reen OR-6 / Column C-9: bed 11.2 m beats skin 72 C by 180 us; ACCEPT "
        "already-legal 14.0 t/h wet THF",
        state,
        spikes,
        proposed,
        safety,
        executed,
        future,
        ticks,
        "Correct ACCEPT of an already-legal wet-THF dehydration feed. total +1.06 = 0.40 + 0.28 + 0.18 + 0.12 + 0.08.",
        ras,
        gate,
        "tetrahydrofuran-dehydrator",
        [
            "accept",
            "already-legal",
            "simulated-thf-dehydrator",
            "dens-vs-tc",
            "sidecar-convictable",
            "simulated",
        ],
        "Teaches that a bed densitometer under trip can confirm an already-legal THF feed "
        "without a skin-TC hitch becoming a hold.",
        4,
    )


def record_495():
    ticks = [
        tick(2016, 0.06, 0.04, 0.03, 0.02, 0.01),
        tick(5040, 0.10, 0.06, 0.04, 0.02, 0.02),
        tick(5200, 0.06, 0.04, 0.03, 0.02, 0.01),
        tick(5640, 0.12, 0.08, 0.05, 0.04, 0.02),
        tick(5920, 0.06, 0.05, 0.03, 0.01, 0.01),
        tick(240000000, 0.04, 0.03, 0.02, 0.01, 0.01),
    ]
    spikes = [
        spike("flux.inp.MLs", 0.980, 0.41),
        spike("tc.sub.C", 2.016, 0.60),
        spike("flux.inp.MLs", 3.200, 0.51),
        spike("tc.sub.C", 5.040, 1.30),
        spike("flux.inp.MLs", 5.200, 1.12),
        spike("ctrl.gate", 5.640, 0.97),
        spike("tc.sub.C", 8.100, 0.78),
        spike("flux.inp.MLs", 12.400, 0.62),
        spike("ctrl.gate", 16.200, 0.85),
        spike("tc.sub.C", 20.400, 0.54),
        spike("flux.inp.MLs", 22.800, 0.43),
    ]
    excerpt = independent_excerpt(95495, 80, 24000, 12, spike_avoid_us(spikes))
    params = OrderedDict(
        [
            ("growth_MLs", 1.62),
            ("sub_C", 482.0),
            ("hold", False),
        ]
    )
    state = OrderedDict(
        [
            (
                "description",
                "MBE chamber M-2 on Phosphide-Cairn PC-4 already sits at 482 C substrate against a "
                "510 C cap with InP flux 1.62 ML/s under a 1.90 trip. Holding 1.62 ML/s is already "
                "legal; a flux-first veto would have idled a quiet epi run.",
            ),
            ("domain", "indium-phosphide-mbe"),
            ("sim_or_real", "designed"),
            (
                "goal",
                "Run M-2 at 1.62 ML/s, keep substrate <= 510 C and flux <= 1.90 ML/s, and leave "
                "the epi stack on schedule.",
            ),
            ("t0_us", 1756850400000495),
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
                                "tc.sub.C 482 under 510 cap",
                                "flux.inp.MLs 1.62 under 1.90 trip",
                            ],
                        ),
                        (
                            "semantics",
                            "Temp-first confirms the already-legal 1.62 ML/s run; flux-first would "
                            "have treated the substrate TC as a hitch echo and looked for an extra hold.",
                        ),
                        (
                            "window_derivation",
                            "280 us = one substrate-TC slot versus the beam-flux publisher on this MBE bus.",
                        ),
                        (
                            "order_evidence_note",
                            "Margin 160 us vs combined jitter 52 us (TC 22 + flux 30): 3.08x over a "
                            "2.0x trust floor. Reversing order by < 160 us inside the 280 us "
                            "window would have REJECTED an already-legal 1.62 ML/s run.",
                        ),
                    ]
                ),
            ),
            (
                "sensors",
                [
                    "substrate TC well, 2 kHz, 22 us jitter",
                    "InP beam-flux ion gauge, 1 kHz, 30 us jitter",
                    "RHEED streak camera (context)",
                    "cracker PT (context)",
                ],
            ),
            (
                "constraints",
                OrderedDict(
                    [
                        ("sub_cap_C", 510.0),
                        ("observed_sub_C", 482.0),
                        ("growth_MLs", 1.62),
                        ("flux_MLs", 1.62),
                        ("flux_cap_MLs", 1.90),
                    ]
                ),
            ),
            (
                "episode_steps",
                [
                    "1. Chamber M-2 indexed on Phosphide-Cairn PC-4; 1.62 ML/s armed.",
                    "2. Substrate 482 C under 510; flux 1.62 ML/s under 1.90.",
                    "3. Flux precursor at 0.980 ms.",
                    "4. Race window [5.040, 5.320] ms.",
                    "5. tc.sub.C 482 at 5.040 ms (winner).",
                    "6. flux.inp.MLs 1.62 at 5.200 ms (loser by 160 us).",
                    "7. Gate at 5.640 ms: ACCEPT 1.62 ML/s.",
                    "8. Substrate stays 482 C; flux stays 1.62 ML/s.",
                    "9. Epi stack on-spec.",
                    "10. Delayed (dwell_s=240): 4 min shutter reseq.",
                ],
            ),
        ]
    )
    proposed = OrderedDict(
        [
            ("name", "hold_growth_MLs"),
            ("parameters", params),
            (
                "evidence",
                OrderedDict(
                    [
                        ("sub_C", 482.0),
                        ("sub_cap_C", 510.0),
                        ("growth_MLs", 1.62),
                        ("flux_MLs", 1.62),
                        ("flux_cap_MLs", 1.90),
                        ("race_margin_us", 160),
                        ("combined_jitter_us", 52),
                        ("dwell_s", 240),
                    ]
                ),
            ),
            (
                "basis",
                "Planner proposes 1.62 ML/s because substrate 482 C is under 510 and InP flux "
                "1.62 ML/s is under 1.90.",
            ),
        ]
    )
    safety = OrderedDict(
        [
            ("decision", "ACCEPT"),
            ("correctness", "correct"),
            (
                "rationale",
                "Substrate TC 482 C won by 160 us, so the chamber is already legal, not still climbing. "
                "Flux 1.62 ML/s is under 1.90. ACCEPT the 1.62 ML/s run. A REJECT would idle a legal MBE stack.",
            ),
            (
                "constraint_checked",
                OrderedDict(
                    [
                        (
                            "sub_C",
                            OrderedDict(
                                [
                                    ("cap", 510.0),
                                    ("observed", 482.0),
                                    ("executed_growth_MLs", 1.62),
                                ]
                            ),
                        ),
                        (
                            "order_evidence",
                            OrderedDict(
                                [("margin_us", 160), ("combined_jitter_us", 52), ("ratio", 3.08)]
                            ),
                        ),
                    ]
                ),
            ),
        ]
    )
    executed = OrderedDict(
        [
            ("name", "hold_growth_MLs"),
            ("parameters", params),
            (
                "gate_effect",
                "ACCEPT: leave 1.62 ML/s; substrate 482 C; flux legal.",
            ),
        ]
    )
    future = OrderedDict(
        [
            (
                "summary",
                "Correct ACCEPT of an already-legal 1.62 ML/s MBE run. Substrate 482 C beat flux "
                "1.62 ML/s by 160 us. 4 min shutter reseq (dwell_s=240) is delayed, not a miss.",
            ),
            (
                "state_delta",
                OrderedDict(
                    [
                        ("growth", "1.62 ML/s held"),
                        ("substrate", "482 C < 510 cap"),
                        ("chamber", "M-2 on-spec"),
                        ("reseq", "4 min shutter reseq (dwell_s=240)"),
                    ]
                ),
            ),
            (
                "surprises",
                [
                    "InP flux never approached 1.90 ML/s; substrate was already under cap.",
                    "Delayed (dwell_s=240): 4 min shutter reseq after monolayer.",
                ],
            ),
            (
                "race_result",
                OrderedDict(
                    [
                        ("winner", "tc.sub.C (5.040 ms, 482 C)"),
                        ("loser", "flux.inp.MLs (5.200 ms, 1.62 ML/s)"),
                        ("margin_us", 160),
                        (
                            "counterfactual_if_reversed",
                            "Flux-first by < 160 us inside the 280 us window would have "
                            "REJECTED an already-legal 1.62 ML/s run. The ACCEPT is still the "
                            "correct gate.",
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
    ras = raster_core(
        24,
        80,
        28,
        54,
        routing(
            "thalamic-relay.inp-sub",
            "spikenaut.policy.mbe-go",
            [
                ("relay.tc.sub", "policy.mbe_go", 0.67),
                ("relay.flux.inp", "policy.mbe_hold", 0.25),
            ],
            "adenosine",
            0.07,
            "accept_stdp; adenosine tags the substrate-TC win as an already-legal MBE run",
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
            ("decision_window_ms", 0.28),
            ("decision", "ACCEPT"),
            (
                "populations",
                [
                    pop_budget("mbe_go", 40, 0.45, 250.0, 0.28),
                    pop("mbe_hold", 32, 0.90),
                    pop("sub_veto", 16, 0.80),
                ],
            ),
        ]
    )
    return wrap_record(
        "ttf-r95-495",
        "Phosphide-Cairn PC-4 / Chamber M-2: substrate 482 C beats InP flux 1.62 ML/s by 160 us; "
        "correct ACCEPT of an already-legal 1.62 ML/s run",
        state,
        spikes,
        proposed,
        safety,
        executed,
        future,
        ticks,
        "Correct ACCEPT. Substrate 482 < 510; flux 1.62 < 1.90. total +1.14 = 0.44 + 0.30 + 0.20 + 0.12 + 0.08.",
        ras,
        gate,
        "indium-phosphide-mbe",
        ["accept", "designed", "sub-vs-flux", "already-legal-growth", "tick6-sidecar-bound"],
        "Teaches that a legal beam-flux header can lose to substrate TC inside a 280 us window; "
        "reversing 160 us would have REJECTED an already-legal MBE run.",
        5,
    )

