def lif_431_excerpt():
    n = 76
    dt_us = 100
    tau_m_ms = 19.0
    v_th = 1.0
    v_reset = 0.0
    refractory_us = 1000
    i_bias = 0.91
    i_stim_peak = 2.42
    stim = (22000, 25000)
    seed = 83431
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
    channels = ["lif.clamp" if t < 22000 else "lif.tube" for t, _ in picked]
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
            ("seed", 83431),
            (
                "note",
                "Population sim scoped to this sidecar. Plant remains designed. "
                "Neurons 0-13 carry +0.62 steam-diluent clamp bias; stim 22-25 ms is the tube leak.",
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


def record_431():
    excerpt, extra = lif_431_excerpt()
    ticks = [
        tick(2080, 0.04, -0.02, -0.02, 0.01, 0.00),
        tick(5200, 0.08, -0.04, -0.02, 0.01, -0.01),
        tick(5380, 0.04, -0.03, -0.02, 0.00, 0.00),
        tick(5900, 0.08, -0.05, -0.03, 0.02, -0.01),
        tick(22400, 0.06, -0.41, -0.04, -0.01, -0.01),
        tick(900000000, 0.02, -0.05, -0.03, 0.01, -0.01),
    ]
    spikes = [
        spike("pt.steam.bar", 1.040, 0.41),
        spike("tc.coil.C", 2.080, 0.58),
        spike("pt.steam.bar", 3.400, 0.50),
        spike("tc.coil.C", 5.200, 1.31),
        spike("pt.steam.bar", 5.380, 1.12),
        spike("ctrl.gate", 5.900, 0.97),
        spike("tc.coil.C", 8.100, 0.82),
        spike("pt.steam.bar", 10.400, 0.64),
        spike("ctrl.gate", 14.200, 0.86),
        spike("ae.tube.leak", 22.400, 1.48),
        spike("ae.tube.leak", 24.100, 0.93),
        spike("pt.steam.bar", 30.200, 0.40),
        spike("tc.coil.C", 36.400, 0.55),
    ]
    state = OrderedDict(
        [
            (
                "description",
                "Dehydro DH-6 on Styrol-Lache SL-4 is already at 648 C coil outlet against a "
                "620 C ceiling, even though diluent steam is only 3.8 bar under 5.0. The coil "
                "channel should latch a 16.0-to-9.5 t/h ethylbenzene cut; trusting the steam "
                "header would leave 16.0 t/h running. A torn catalyst tube on the first pass "
                "stays invisible to both publishers until AE fires.",
            ),
            ("domain", "styrene-ethylbenzene-dehydro"),
            ("sim_or_real", "designed"),
            (
                "goal",
                "Keep DH-6 coil outlet <= 620 C and finish the styrene pass without dumping "
                "ethylbenzene through a torn catalyst tube.",
            ),
            ("t0_us", 1756850400000431),
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
                                "tc.coil.C 648 over 620 cap",
                                "pt.steam.bar 3.8 with header under 5.0",
                            ],
                        ),
                        (
                            "semantics",
                            "Coil-first latches EB clamp 16.0 -> 9.5 t/h; steam-first keeps 16.0 "
                            "on a 'still under header-cap' model.",
                        ),
                        (
                            "window_derivation",
                            "360 us = one coil-TC slot versus the steam-header PT publisher "
                            "on this styrene dehydro bus.",
                        ),
                        (
                            "order_evidence_note",
                            "Margin 180 us vs combined jitter 62 us (coil 28 + steam 34): 2.90x over "
                            "a 2.0x trust floor. Reversing order by < 180 us inside the 360 us "
                            "window would have kept 16.0 t/h; predicted next-sample 636 C "
                            "> 620 cap.",
                        ),
                    ]
                ),
            ),
            (
                "sensors",
                [
                    "first-pass coil TC, 2 kHz, 28 us jitter",
                    "diluent-steam PT, 1 kHz, 34 us jitter",
                    "catalyst-tube AE puck (context)",
                    "ethylbenzene feed Coriolis (context)",
                ],
            ),
            (
                "constraints",
                OrderedDict(
                    [
                        ("coil_cap_C", 620.0),
                        ("observed_coil_C", 648.0),
                        ("eb_tph", 16.0),
                        ("steam_bar", 3.8),
                        ("steam_cap_bar", 5.0),
                    ]
                ),
            ),
            (
                "episode_steps",
                [
                    "1. DH-6 indexed on Styrol-Lache SL-4; EB 16.0 t/h; coil 648 C.",
                    "2. Steam 3.8 bar under 5.0 cap; styrene pass armed.",
                    "3. Steam-PT precursor at 1.040 ms.",
                    "4. Race window [5.200, 5.560] ms.",
                    "5. tc.coil.C 648 at 5.200 ms (winner).",
                    "6. pt.steam.bar 3.8 at 5.380 ms (loser by 180 us).",
                    "7. Gate at 5.900 ms: MODIFY clamp EB 16.0 -> 9.5 t/h.",
                    "8. After clamp coil 608 C <= 620; steam still 3.8 bar.",
                    "9. At 22.400 ms a catalyst tube dumps 0.4 t EB.",
                    "10. 15 min pass isolate (abort_s=900); named un-netted loss.",
                ],
            ),
        ]
    )
    proposed = OrderedDict(
        [
            ("name", "cruise_eb_feed"),
            (
                "parameters",
                OrderedDict(
                    [("eb_tph", 16.0), ("coil_C", 648.0), ("steam_bar", 3.8)]
                ),
            ),
            (
                "evidence",
                OrderedDict(
                    [
                        ("coil_C", 648.0),
                        ("coil_cap_C", 620.0),
                        ("predicted_unclamped_next_C", 636.0),
                        ("eb_tph", 16.0),
                        ("steam_bar", 3.8),
                        ("steam_cap_bar", 5.0),
                        ("race_margin_us", 180),
                        ("combined_jitter_us", 62),
                        ("abort_s", 900),
                    ]
                ),
            ),
            (
                "basis",
                "Planner proposes 16.0 t/h EB because steam 3.8 bar is under 5.0, treating "
                "the 648 C coil as a still-wet TC rather than an outlet-cap miss.",
            ),
        ]
    )
    safety = OrderedDict(
        [
            ("decision", "MODIFY"),
            ("correctness", "correct"),
            (
                "rationale",
                "Coil outlet 648 C won by 180 us, so the dehydro is off-spec, not still "
                "a steam-header story. Holding 16.0 t/h predicts next-sample 636 C > 620 "
                "cap. MODIFY: EB 16.0 -> 9.5 t/h. Observed after clamp 608 C <= 620. "
                "A full REJECT is not indicated: a clean styrene pass accepts 9.5 t/h.",
            ),
            (
                "constraint_checked",
                OrderedDict(
                    [
                        (
                            "coil_C",
                            OrderedDict(
                                [
                                    ("cap", 620.0),
                                    ("observed", 648.0),
                                    ("predicted_unclamped_next", 636.0),
                                    ("clamped_eb_tph", 9.5),
                                    ("observed_after_clamp", 608.0),
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
            ("name", "clamped_eb_feed"),
            (
                "parameters",
                OrderedDict(
                    [("eb_tph", 9.5), ("coil_C", 608.0), ("steam_bar", 3.8)]
                ),
            ),
            (
                "gate_effect",
                "MODIFY: EB 16.0 -> 9.5 t/h. Process-correct vs the 620 C coil cap. "
                "Tube still leaks at 22.400 ms.",
            ),
        ]
    )
    future = OrderedDict(
        [
            (
                "summary",
                "Process-correct MODIFY held coil outlet at 608 C. At 22.400 ms a catalyst "
                "tube already seated on the first pass dumped 0.4 t of ethylbenzene. Clamp "
                "reduced dump energy; it did not prevent the leak. Partnered negative: process "
                "heads stay honest; world loss is named, not netted.",
            ),
            (
                "state_delta",
                OrderedDict(
                    [
                        ("coil", "clamp executed; peak 608 C <= 620 cap"),
                        ("tube", "leaked at 22.400 ms; 0.4 t EB"),
                        ("repair", "15 min pass isolate (abort_s=900)"),
                        ("mission", "SL-4 styrene pass incomplete this circuit"),
                    ]
                ),
            ),
            (
                "surprises",
                [
                    "Neither coil TC nor steam PT predicted the seated tube leak; ae.tube.leak is a new channel at 22.400 ms, 16.500 ms after the gate, still inside the 42 ms raster.",
                    "Delayed (abort_s=900): 15 min pass isolate. Named un-netted loss, not folded into task_progress.",
                ],
            ),
            (
                "un_netted_loss",
                "15 min pass isolate after the tube leak. Safety head -0.60 prices the dump; "
                "task_progress stays +0.32 because the EB clamp completed under the 620 C "
                "cap. World loss is named here, not subtracted from process heads.",
            ),
            (
                "race_result",
                OrderedDict(
                    [
                        ("winner", "tc.coil.C (5.200 ms, 648 C)"),
                        ("loser", "pt.steam.bar (5.380 ms, 3.8 bar)"),
                        ("margin_us", 180),
                        (
                            "counterfactual_if_reversed",
                            "Steam-first by < 180 us inside the 360 us window would have kept "
                            "16.0 t/h; predicted next-sample 636 C would have missed "
                            "the 620 cap even without the leak. The MODIFY is still the correct "
                            "process. The leak is a later world charge either way, cheaper with "
                            "the clamp than without.",
                        ),
                    ]
                ),
            ),
            ("reward_inflection_t_us", 22400),
            (
                "reward_inflection_note",
                "Safety collapses at the 22.400 ms tube leak (tick t_us=22400), inside the "
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
            "thalamic-relay.styrol-coil",
            "spikenaut.policy.eb-clamp",
            [
                ("relay.tc.coil", "policy.eb_clamp", 0.68),
                ("relay.pt.steam", "policy.header_hold", 0.29),
                ("relay.ae.tube", "policy.eb_clamp", -0.42),
            ],
            "noradrenaline",
            0.04,
            "surprise-gated pre_post_stdp; NA at coil win (5.200 ms) opens a 42 ms eligibility "
            "trace that still covers the 22.400 ms tube leak",
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
                    pop_budget("eb_clamp", 50, 0.5, 220.0, 0.36),
                    pop_budget("header_hold", 40, 0.8, 50.0, 0.36),
                    pop("leak_veto", 24, 0.75),
                ],
            ),
        ]
    )
    return wrap_record(
        "ttf-r83-431",
        "Styrol-Lache SL-4 / Dehydro DH-6: coil 648 C beats steam header by 180 us; correct "
        "MODIFY still eats an in-window tube leak (partnered negative total -0.44)",
        state,
        spikes,
        proposed,
        safety,
        executed,
        future,
        ticks,
        "Partnered negative. Process-correct MODIFY; world still charges inside the 42 ms "
        "raster. total -0.44 = 0.32 + -0.60 + -0.16 + 0.04 + -0.04. Named pass isolate "
        "(abort_s=900) is not netted into task_progress.",
        ras,
        gate,
        "styrene-ethylbenzene-dehydro",
        [
            "modify",
            "partnered-negative-total",
            "independent-lif-raster",
            "sidecar-sim-only",
            "in-window-world-charge",
            "designed",
        ],
        "A critic can see the world-charge as a LIF burst inside the raster while process "
        "heads stay honest. Credit assignment is spikes, not prose across a 15 min pass isolate.",
        1,
    )


def record_432():
    ticks = [
        tick(2240, -0.02, -0.02, -0.02, -0.01, 0.01),
        tick(5600, -0.04, -0.04, -0.03, -0.02, 0.01),
        tick(5780, -0.04, -0.04, -0.03, -0.02, 0.01),
        tick(6120, -0.08, -0.10, -0.06, -0.03, 0.02),
        tick(6460, -0.02, -0.02, -0.02, -0.01, 0.01),
        tick(720000000, -0.02, -0.02, -0.02, -0.01, 0.00),
    ]
    spikes = [
        spike("enc.ka.cmd", 1.120, 0.42),
        spike("ct.ewa.live", 2.240, 0.57),
        spike("enc.ka.cmd", 3.500, 0.49),
        spike("ct.ewa.live", 5.600, 1.29),
        spike("ct.ewb.idle", 5.780, 1.10),
        spike("ctrl.gate", 6.120, 0.96),
        spike("ct.ewa.live", 8.400, 0.80),
        spike("enc.ka.cmd", 10.400, 0.63),
        spike("ctrl.gate", 12.600, 0.84),
        spike("ct.ewa.live", 16.600, 0.41),
        spike("ct.ewb.idle", 22.200, 0.54),
        spike("ct.ewa.live", 26.400, 0.38),
    ]
    excerpt = independent_excerpt(83432, 88, 28000, 14, spike_avoid_us(spikes))
    state = OrderedDict(
        [
            (
                "description",
                "Electrowin bank EW-A at Catholyte-Ingle CI-9 still reads a legal 14.2 kA "
                "under a 16.0 kA cap with cathode-negative polarity, while idle sibling EW-B "
                "prints a leftover -14.2 kA on a reversed CT. Live-bank-first should ACCEPT; "
                "a weak supervisor inverts EW-B polarity as if the idle mimic were the live bus.",
            ),
            ("domain", "nickel-electrowin-cell"),
            ("sim_or_real", "designed"),
            (
                "goal",
                "Finish the CI-9 nickel harvest with live EW-A <= 16.0 kA, leave polarity "
                "cathode-negative, and keep idle EW-B parked at 0 kA.",
            ),
            ("t0_us", 1756850400000432),
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
                                "ct.ewa.live 14.2 kA on LIVE bank EW-A",
                                "ct.ewb.idle -14.2 kA leftover on IDLE bank EW-B",
                            ],
                        ),
                        (
                            "semantics",
                            "Live-bank-first should ACCEPT the already-legal 14.2 kA; idle-mimic-first "
                            "is a false reverse-current invert on the parked bank.",
                        ),
                        (
                            "window_derivation",
                            "340 us = one live-CT slot versus the idle-bank leftover publisher on this "
                            "nickel tankhouse dual-bus.",
                        ),
                        (
                            "order_evidence_note",
                            "Margin 180 us vs combined jitter 60 us (live 28 + idle 32). Order is "
                            "correctly live-bank-first. The error is polarity invert on the idle "
                            "bank, not the live magnitude: 14.2 kA is under the 16.0 cap.",
                        ),
                    ]
                ),
            ),
            (
                "sensors",
                [
                    "live EW-A bus CT, 2 kHz, 28 us jitter, tag=EWA_CT.LIVE status=LIVE polarity=cathode_neg",
                    "idle EW-B leftover CT, 1 kHz, 32 us jitter, tag=EWB_CT.IDLE status=IDLE mimic_kA=-14.2",
                    "rectifier polarity encoder (context)",
                    "pregnant-liquor FT (context)",
                ],
            ),
            (
                "constraints",
                OrderedDict(
                    [
                        ("cap_kA", 16.0),
                        ("live_kA", 14.2),
                        ("idle_kA", 0.0),
                        ("idle_mimic_kA", -14.2),
                        ("live_status", "LIVE"),
                        ("idle_status", "IDLE"),
                        ("live_polarity", "cathode_neg"),
                    ]
                ),
            ),
            (
                "episode_steps",
                [
                    "1. EW-A already harvesting; live 14.2 kA cathode-neg; EW-B parked.",
                    "2. Idle mimic prints -14.2 kA; status=IDLE; leftover reverse CT.",
                    "3. Encoder precursor at 1.120 ms.",
                    "4. Race window [5.600, 5.940] ms.",
                    "5. ct.ewa.live 14.2 kA at 5.600 ms (winner).",
                    "6. ct.ewb.idle -14.2 leftover at 5.780 ms (loser by 180 us).",
                    "7. Gate at 6.120 ms: WRONG-MODIFY inverts EW-B polarity.",
                    "8. EW-B driven -12.0 kA; EW-A left 14.2 kA legal.",
                    "9. Idle cells blister; harvest stalls.",
                    "10. Delayed (abort_s=720): 12 min tankhouse dump while EW-B is reversed.",
                ],
            ),
        ]
    )
    proposed = OrderedDict(
        [
            ("name", "cruise_ew_a"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("bank_A_kA", 14.2),
                        ("bank_B_kA", 0.0),
                        ("invert_polarity", False),
                        ("bind_idle_bank", False),
                    ]
                ),
            ),
            (
                "evidence",
                OrderedDict(
                    [
                        ("live_kA", 14.2),
                        ("cap_kA", 16.0),
                        ("idle_kA", 0.0),
                        ("idle_mimic_kA", -14.2),
                        ("live_status", "LIVE"),
                        ("idle_status", "IDLE"),
                        ("live_polarity", "cathode_neg"),
                        ("t_gate_us", 6120),
                        ("correct_gate", "ACCEPT"),
                        ("correct_bank_A_kA", 14.2),
                        ("correct_bank_B_kA", 0.0),
                        ("race_margin_us", 180),
                        ("combined_jitter_us", 60),
                        ("abort_s", 720),
                    ]
                ),
            ),
            (
                "basis",
                "Planner proposes continuing 14.2 kA on EW-A because live current is under "
                "the 16.0 kA cap, treating the idle -14.2 leftover as a parked reverse-CT echo.",
            ),
        ]
    )
    safety = OrderedDict(
        [
            ("decision", "MODIFY"),
            ("correctness", "incorrect"),
            (
                "rationale",
                "Current -14.2 exceeds the 16.0 cap with reverse sign (true only if the idle "
                "mimic is the live bus). Invert EW-B polarity and drive -12.0 kA because "
                "EWB_CT.IDLE is the highlighted tag. Leave live EW-A unused.",
            ),
            (
                "constraint_checked",
                OrderedDict(
                    [
                        (
                            "current",
                            OrderedDict(
                                [
                                    ("cap_kA", 16.0),
                                    ("live_kA", 14.2),
                                    ("idle_mimic_kA", -14.2),
                                    ("executed_bank_B_kA", -12.0),
                                    ("correct_bank_B_kA", 0.0),
                                    ("correct_gate", "ACCEPT"),
                                ]
                            ),
                        ),
                        (
                            "polarity_bind",
                            OrderedDict(
                                [
                                    ("t_gate_us", 6120),
                                    ("invert_polarity", True),
                                    ("bind_idle_bank", True),
                                    ("wrong_bank", "EW-B"),
                                    ("live_status", "LIVE"),
                                    ("idle_status", "IDLE"),
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
            ("name", "invert_idle_bank"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("bank_A_kA", 14.2),
                        ("bank_B_kA", -12.0),
                        ("invert_polarity", True),
                        ("bind_idle_bank", True),
                    ]
                ),
            ),
            (
                "gate_effect",
                "MODIFY (incorrect / wrong-bank polarity invert): -12.0 kA reverse drive applied "
                "to IDLE EW-B because leftover -14.2 was treated as live reverse current. "
                "Routing relay.ct.idle -> policy.polarity_invert; no positive weight to policy.live_hold.",
            ),
        ]
    )
    future = OrderedDict(
        [
            (
                "summary",
                "Wrong-MODIFY inverted polarity on a parked nickel bank. Live 14.2 kA was under "
                "the 16.0 kA cap at t_gate; idle leftover -14.2 kA is not a live over-cap. "
                "12 min tankhouse dump (abort_s=720). Correct gate was ACCEPT; leave EW-A at "
                "14.2 kA cathode-neg and EW-B at 0 kA at t_gate_us=6120.",
            ),
            (
                "state_delta",
                OrderedDict(
                    [
                        ("live_bus", "EW-A left legal at 14.2 kA; EW-B slammed to -12.0 kA"),
                        ("idle_tag", "-14.2 leftover treated as live reverse; status=IDLE"),
                        ("dump", "12 min tankhouse dump, idle cells blistered"),
                        ("mission", "nickel harvest deferred"),
                    ]
                ),
            ),
            (
                "surprises",
                [
                    "Live-bank-first was the correct order and the live kA was under cap; the MODIFY spent that win on an idle-bank polarity invert.",
                    "Delayed (abort_s=720): CI-9 holds 12 min while EW-B is reversed and re-formed; next harvest 14 min late.",
                ],
            ),
            (
                "recovery",
                OrderedDict(
                    [
                        (
                            "correct_gate",
                            "ACCEPT; leave bank_A_kA=14.2 cathode_neg at t_gate_us=6120; invert_polarity=false; bind_idle_bank=false; leave bank_B_kA=0.",
                        ),
                        ("correct_actuator", "EW-A_rectifier"),
                        ("wrong_bank", "EW-B"),
                        ("t_gate_us", 6120),
                        (
                            "wrong_edit_applied",
                            OrderedDict(
                                [
                                    ("bank_B_kA", -12.0),
                                    ("invert_polarity", True),
                                    ("bind_idle_bank", True),
                                ]
                            ),
                        ),
                        (
                            "cost",
                            "12 min tankhouse dump (task/efficiency); live EW-A never crossed 16.0 kA while reverse current was spent on an idle bank.",
                        ),
                    ]
                ),
            ),
            (
                "race_result",
                OrderedDict(
                    [
                        ("winner", "ct.ewa.live (5.600 ms, 14.2 kA LIVE)"),
                        ("loser", "ct.ewb.idle (5.780 ms, -14.2 leftover IDLE)"),
                        ("margin_us", 180),
                        (
                            "counterfactual_if_reversed",
                            "Idle-first by < 180 us would still be a parked leftover CT; "
                            "a correct gate binds ct.ewa.live to policy.live_hold at t_gate either "
                            "way. The wrong MODIFY spent the live win on a polarity invert of EW-B.",
                        ),
                    ]
                ),
            ),
            ("reward_inflection_t_us", 6120),
            (
                "reward_inflection_note",
                "Task, safety, and efficiency drop at the idle-bank invert (6.120 ms, tick 4). "
                "The 12 min tankhouse dump is delayed surprise, not the inflection.",
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
            "thalamic-relay.ew-idle-polarity",
            "spikenaut.policy.polarity-invert",
            [
                ("relay.ct.idle", "policy.polarity_invert", 0.74),
                ("relay.ct.live", "policy.polarity_invert", 0.21),
            ],
            "acetylcholine",
            0.08,
            "polarity_stdp; ACh tags the (wrong) idle-bank invert at the live CT win",
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
                    pop_budget("polarity_invert", 48, 0.45, 300.0, 0.34),
                    pop("live_hold", 48, 0.90),
                    pop("invert_veto", 20, 0.80),
                ],
            ),
        ]
    )
    return wrap_record(
        "ttf-r83-432",
        "WRONG-MODIFY at Catholyte-Ingle CI-9 / Bank EW-A: live 14.2 kA read correctly; "
        "polarity invert of idle EW-B to -12.0 kA (wrong-bank / polarity-invert)",
        state,
        spikes,
        proposed,
        safety,
        executed,
        future,
        ticks,
        "Wrong-modify / wrong-bank polarity invert. Sidecar arithmetic 14.2 < 16.0 on live kA is "
        "true; MODIFY bound to polarity_invert. total -0.68 = -0.22 + -0.24 + -0.18 + -0.10 + 0.06.",
        ras,
        gate,
        "nickel-electrowin-cell",
        [
            "modify",
            "wrong-gate",
            "wrong-bank",
            "polarity-invert",
            "sidecar-convictable",
            "designed",
        ],
        "Teaches a probe that a correct live-bank-first race can still be a wrong gate when the "
        "MODIFY inverts polarity on an idle sibling. Convictable from live_kA vs cap_kA, "
        "idle_status, invert_polarity, and routing without tankhouse physics.",
        2,
        supervisor_error_type="wrong-modify",
    )
