def lif_601_excerpt():
    n = 76
    dt_us = 100
    tau_m_ms = 19.0
    v_th = 1.0
    v_reset = 0.0
    refractory_us = 1000
    i_bias = 0.91
    i_stim_peak = 2.42
    stim = (22000, 25000)
    seed = 117601
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
    channels = ["lif.clamp" if t < 22000 else "lif.pack" for t, _ in picked]
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
            ("seed", 117601),
            (
                "note",
                "Population sim scoped to this sidecar. Plant remains designed. "
                "Neurons 0-13 carry +0.62 chromyl-feed clamp bias; stim 22-25 ms is the packing-tube leak.",
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


def record_601():
    excerpt, extra = lif_601_excerpt()
    ticks = [
        tick(2080, 0.04, -0.02, -0.02, 0.01, 0.00),
        tick(5200, 0.08, -0.04, -0.02, 0.01, -0.01),
        tick(5380, 0.04, -0.03, -0.02, 0.00, 0.00),
        tick(5900, 0.08, -0.05, -0.03, 0.02, -0.01),
        tick(22400, 0.06, -0.41, -0.04, -0.01, -0.01),
        tick(900000000, 0.02, -0.05, -0.03, 0.01, -0.01),
    ]
    spikes = [
        spike("pt.reboil.MPa", 1.040, 0.41),
        spike("cr.vapor.gNm3", 2.080, 0.58),
        spike("pt.reboil.MPa", 3.400, 0.50),
        spike("cr.vapor.gNm3", 5.200, 1.31),
        spike("pt.reboil.MPa", 5.380, 1.12),
        spike("ctrl.gate", 5.900, 0.97),
        spike("cr.vapor.gNm3", 8.100, 0.82),
        spike("pt.reboil.MPa", 10.400, 0.64),
        spike("ctrl.gate", 14.200, 0.86),
        spike("ae.pack.leak", 22.400, 1.48),
        spike("ae.pack.leak", 24.100, 0.93),
        spike("pt.reboil.MPa", 30.200, 0.40),
        spike("cr.vapor.gNm3", 36.400, 0.55),
    ]
    state = OrderedDict(
        [
            (
                "description",
                "Chromyl-Fellwick CF-4 still D-3 already prints CrO2Cl2 vapor at 11.8 g/Nm3, 3.8 "
                "over the 8.0 stack stop, while the reboiler PT sits a legal 0.48 MPa inside a 0.70 "
                "MPa envelope. UV-first clamps chromyl feed 16.0 t/h to 9.8; PT-first would keep "
                "16.0 cruising. Packing AE stays mute until a later tube leak.",
            ),
            ("domain", "chromyl-chloride-still"),
            ("sim_or_real", "designed"),
            (
                "goal",
                "Keep D-3 CrO2Cl2 vapor <= 8.0 g/Nm3 and finish the chromyl pass without dumping "
                "heel through a torn packing tube.",
            ),
            ("t0_us", 1756850400000601),
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
                                "cr.vapor.gNm3 11.8 over 8.0 cap",
                                "pt.reboil.MPa 0.48 with kettle under 0.70",
                            ],
                        ),
                        (
                            "semantics",
                            "UV-first latches chromyl-feed clamp 16.0 -> 9.8 t/h; reboiler-first keeps 16.0 "
                            "on a 'still under kettle-cap' model.",
                        ),
                        (
                            "window_derivation",
                            "360 us = one CrO2Cl2-UV slot versus the reboiler-PT publisher on this "
                            "chromyl-still bus.",
                        ),
                        (
                            "order_evidence_note",
                            "Margin 180 us vs combined jitter 62 us (UV 28 + PT 34): 2.90x over "
                            "a 2.0x trust floor. Reversing order by < 180 us inside the 360 us "
                            "window would have kept 16.0 t/h; predicted next-sample 10.2 g/Nm3 "
                            "> 8.0 cap.",
                        ),
                    ]
                ),
            ),
            (
                "sensors",
                [
                    "CrO2Cl2 UV cell, 2 kHz, 28 us jitter",
                    "reboiler PT, 1 kHz, 34 us jitter",
                    "packing-tube AE puck (context)",
                    "chromyl feed Coriolis (context)",
                ],
            ),
            (
                "constraints",
                OrderedDict(
                    [
                        ("vapor_cap_gNm3", 8.0),
                        ("observed_vapor_gNm3", 11.8),
                        ("chromyl_tph", 16.0),
                        ("reboil_MPa", 0.48),
                        ("reboil_cap_MPa", 0.70),
                    ]
                ),
            ),
            (
                "episode_steps",
                [
                    "1. D-3 indexed on Chromyl-Fellwick CF-4; chromyl feed 16.0 t/h; vapor 11.8 g/Nm3.",
                    "2. Reboiler 0.48 MPa under 0.70 cap; chromyl pass armed.",
                    "3. Reboiler PT precursor at 1.040 ms.",
                    "4. Race window [5.200, 5.560] ms.",
                    "5. cr.vapor.gNm3 11.8 at 5.200 ms (winner).",
                    "6. pt.reboil.MPa 0.48 at 5.380 ms (loser by 180 us).",
                    "7. Gate at 5.900 ms: MODIFY clamp chromyl 16.0 -> 9.8 t/h.",
                    "8. After clamp vapor 6.4 g/Nm3 <= 8.0; reboiler still 0.48 MPa.",
                    "9. At 22.400 ms a packing-tube leak dumps 0.4 t chromyl heel.",
                    "10. 15 min packing isolate (abort_s=900); named un-netted loss.",
                ],
            ),
        ]
    )
    proposed = OrderedDict(
        [
            ("name", "cruise_chromyl_feed"),
            (
                "parameters",
                OrderedDict(
                    [("chromyl_tph", 16.0), ("vapor_gNm3", 11.8), ("reboil_MPa", 0.48)]
                ),
            ),
            (
                "evidence",
                OrderedDict(
                    [
                        ("vapor_gNm3", 11.8),
                        ("vapor_cap_gNm3", 8.0),
                        ("predicted_unclamped_next_gNm3", 10.2),
                        ("chromyl_tph", 16.0),
                        ("reboil_MPa", 0.48),
                        ("reboil_cap_MPa", 0.70),
                        ("race_margin_us", 180),
                        ("combined_jitter_us", 62),
                        ("abort_s", 900),
                    ]
                ),
            ),
            (
                "basis",
                "Planner proposes 16.0 t/h chromyl because reboiler 0.48 MPa is under 0.70, treating "
                "the 11.8 g/Nm3 UV as a still-wet cell rather than a stack miss.",
            ),
        ]
    )
    safety = OrderedDict(
        [
            ("decision", "MODIFY"),
            ("correctness", "correct"),
            (
                "rationale",
                "CrO2Cl2 UV 11.8 g/Nm3 won by 180 us, so the still is off-spec, not still "
                "a reboiler-PT story. Holding 16.0 t/h predicts next-sample 10.2 g/Nm3 > 8.0 "
                "cap. MODIFY: chromyl 16.0 -> 9.8 t/h. Observed after clamp 6.4 g/Nm3 <= 8.0. "
                "A full REJECT is not indicated: a clean chromyl pass accepts 9.8 t/h.",
            ),
            (
                "constraint_checked",
                OrderedDict(
                    [
                        (
                            "vapor_gNm3",
                            OrderedDict(
                                [
                                    ("cap", 8.0),
                                    ("observed", 11.8),
                                    ("predicted_unclamped_next", 10.2),
                                    ("clamped_chromyl_tph", 9.8),
                                    ("observed_after_clamp", 6.4),
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
            ("name", "clamped_chromyl_feed"),
            (
                "parameters",
                OrderedDict(
                    [("chromyl_tph", 9.8), ("vapor_gNm3", 6.4), ("reboil_MPa", 0.48)]
                ),
            ),
            (
                "gate_effect",
                "MODIFY: chromyl 16.0 -> 9.8 t/h. Process-correct vs the 8.0 g/Nm3 vapor cap. "
                "Packing still leaks at 22.400 ms.",
            ),
        ]
    )
    future = OrderedDict(
        [
            (
                "summary",
                "Process-correct MODIFY held CrO2Cl2 vapor at 6.4 g/Nm3. At 22.400 ms a packing "
                "tube already seated on D-3 dumped 0.4 t of chromyl heel. Clamp reduced dump "
                "energy; it did not prevent the leak. Partnered negative: process heads stay "
                "honest; world loss is named, not netted.",
            ),
            (
                "state_delta",
                OrderedDict(
                    [
                        ("vapor", "clamp executed; peak 6.4 g/Nm3 <= 8.0 cap"),
                        ("packing", "leaked at 22.400 ms; 0.4 t chromyl heel"),
                        ("repair", "15 min packing isolate (abort_s=900)"),
                        ("mission", "CF-4 chromyl pass incomplete this circuit"),
                    ]
                ),
            ),
            (
                "surprises",
                [
                    "Neither CrO2Cl2 UV nor reboiler PT predicted the seated packing-tube leak; ae.pack.leak is a new channel at 22.400 ms, 16.500 ms after the gate, still inside the 42 ms raster.",
                    "Delayed (abort_s=900): 15 min packing isolate. Named un-netted loss, not folded into task_progress.",
                ],
            ),
            (
                "un_netted_loss",
                "15 min packing isolate after the packing-tube leak. Safety head -0.60 prices the dump; "
                "task_progress stays +0.32 because the chromyl clamp completed under the 8.0 g/Nm3 "
                "cap. World loss is named here, not subtracted from process heads.",
            ),
            (
                "race_result",
                OrderedDict(
                    [
                        ("winner", "cr.vapor.gNm3 (5.200 ms, 11.8 g/Nm3)"),
                        ("loser", "pt.reboil.MPa (5.380 ms, 0.48 MPa)"),
                        ("margin_us", 180),
                        (
                            "counterfactual_if_reversed",
                            "Reboiler-first by < 180 us inside the 360 us window would have kept "
                            "16.0 t/h; predicted next-sample 10.2 g/Nm3 would have missed "
                            "the 8.0 cap even without the leak. The MODIFY is still the correct "
                            "process. The leak is a later world charge either way, cheaper with "
                            "the clamp than without.",
                        ),
                    ]
                ),
            ),
            ("reward_inflection_t_us", 22400),
            (
                "reward_inflection_note",
                "Safety collapses at the 22.400 ms packing-tube leak (tick t_us=22400), inside the "
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
            "thalamic-relay.chromyl-uv",
            "spikenaut.policy.chromyl-clamp",
            [
                ("relay.cr.vapor", "policy.chromyl_clamp", 0.68),
                ("relay.pt.reboil", "policy.reboil_hold", 0.29),
                ("relay.ae.pack", "policy.chromyl_clamp", -0.42),
            ],
            "noradrenaline",
            0.04,
            "surprise-gated pre_post_stdp; NA at UV win (5.200 ms) opens a 42 ms eligibility "
            "trace that still covers the 22.400 ms packing-tube leak",
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
                    pop_budget("chromyl_clamp", 50, 0.5, 220.0, 0.36),
                    pop_budget("reboil_hold", 40, 0.8, 50.0, 0.36),
                    pop("leak_veto", 24, 0.75),
                ],
            ),
        ]
    )
    return wrap_record(
        "ttf-r117-601",
        "Chromyl-Fellwick CF-4 / Still D-3: CrO2Cl2 UV beats reboiler PT by 180 us; correct "
        "MODIFY still eats an in-window packing-tube leak (partnered negative total -0.44)",
        state,
        spikes,
        proposed,
        safety,
        executed,
        future,
        ticks,
        "Partnered negative. Process-correct MODIFY; world still charges inside the 42 ms "
        "raster. total -0.44 = 0.32 + -0.60 + -0.16 + 0.04 + -0.04. Named packing isolate "
        "(abort_s=900) is not netted into task_progress.",
        ras,
        gate,
        "chromyl-chloride-still",
        [
            "modify",
            "partnered-negative-total",
            "independent-lif-raster",
            "sidecar-sim-only",
            "in-window-world-charge",
            "designed",
        ],
        "A critic can see the world-charge as a LIF burst inside the raster while process "
        "heads stay honest. Credit assignment is spikes, not prose across a 15 min packing isolate.",
        1,
    )


def record_602():
    ticks = [
        tick(2240, -0.02, -0.02, -0.02, -0.01, 0.01),
        tick(5600, -0.04, -0.04, -0.03, -0.02, 0.01),
        tick(5780, -0.04, -0.04, -0.03, -0.02, 0.01),
        tick(6120, -0.08, -0.10, -0.06, -0.03, 0.02),
        tick(6460, -0.02, -0.02, -0.02, -0.01, 0.01),
        tick(720000000, -0.02, -0.02, -0.02, -0.01, 0.00),
    ]
    spikes = [
        spike("ft.fe.tph", 1.120, 0.42),
        spike("ir.co.ppm", 2.240, 0.57),
        spike("ft.fe.tph", 3.500, 0.49),
        spike("ir.co.ppm", 5.600, 1.29),
        spike("ft.jacket.tph", 5.780, 1.10),
        spike("ctrl.gate", 6.120, 0.96),
        spike("ir.co.ppm", 8.400, 0.80),
        spike("ft.fe.tph", 10.400, 0.63),
        spike("ctrl.gate", 12.600, 0.84),
        spike("ir.co.ppm", 16.600, 0.41),
        spike("ft.jacket.tph", 22.200, 0.54),
        spike("ir.co.ppm", 26.400, 0.38),
    ]
    excerpt = independent_excerpt(117602, 88, 28000, 14, spike_avoid_us(spikes))
    state = OrderedDict(
        [
            (
                "description",
                "Cracker C-9 at Pentacarb-Howbeck PH-7 still shows cascade-primary CO IR at 186 ppm "
                "versus a 40 ppm tube cap. Jacket-oil FT is the published cascade secondary at 6.0 t/h, "
                "3.0 under a 9.0 t/h slave envelope; secondary_is_primary is false and both tags carry "
                "LIVE. IR-first must cut Fe(CO)5 8.4 t/h to 5.2. The weak supervisor binds the slave "
                "FT as if it were the master and spends the cut on jacket 6.0 -> 2.1 t/h, leaving "
                "8.4 t/h carbonyl cruising.",
            ),
            ("domain", "iron-pentacarbonyl-cracker"),
            ("sim_or_real", "designed"),
            (
                "goal",
                "Finish the PH-7 Fe(CO)5 crack with live CO <= 40 ppm, leave jacket oil at 6.0 t/h "
                "as cascade secondary only, and cut carbonyl on the primary IR.",
            ),
            ("t0_us", 1756850400000602),
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
                                "ir.co.ppm 186 on LIVE cascade primary C-9",
                                "ft.jacket.tph 6.0 on LIVE cascade secondary (secondary_is_primary=false)",
                            ],
                        ),
                        (
                            "semantics",
                            "Primary-IR-first should MODIFY-cut Fe(CO)5 on the master tag; "
                            "secondary-first is a false cascade-secondary-as-primary bind that cuts jacket oil instead.",
                        ),
                        (
                            "window_derivation",
                            "340 us = one live CO-IR slot versus the jacket-FT publisher "
                            "on this cascade primary/secondary PLC bus.",
                        ),
                        (
                            "order_evidence_note",
                            "Margin 180 us vs combined jitter 60 us (pri 28 + sec 32). Order is "
                            "correctly primary-IR-first. The error is pairing: the jacket FT is a "
                            "published cascade secondary (secondary_is_primary=false), but the cut is spent "
                            "on jacket oil while Fe(CO)5 stays 8.4 t/h.",
                        ),
                    ]
                ),
            ),
            (
                "sensors",
                [
                    "live CO IR on C-9, 2 kHz, 28 us jitter, tag=C9_IR.PRI status=LIVE role=cascade_primary",
                    "jacket-oil FT on C-9, 1 kHz, 32 us jitter, tag=C9_JKT.SEC status=LIVE role=cascade_secondary secondary_is_primary=false",
                    "Fe(CO)5 FT C-9 (context)",
                    "cracker skin TC (context)",
                ],
            ),
            (
                "constraints",
                OrderedDict(
                    [
                        ("cap_co_ppm", 40.0),
                        ("live_co_ppm", 186.0),
                        ("fe_tph", 8.4),
                        ("jacket_tph", 6.0),
                        ("jacket_cap_tph", 9.0),
                        ("primary_status", "LIVE"),
                        ("secondary_status", "LIVE"),
                        ("secondary_is_primary", False),
                        ("cascade_pair", "ir_primary_ft_secondary"),
                    ]
                ),
            ),
            (
                "episode_steps",
                [
                    "1. C-9 LIVE; CO 186 ppm; Fe(CO)5 8.4 t/h; jacket secondary 6.0 t/h; secondary_is_primary=false.",
                    "2. Caps: CO 40 ppm; jacket 9.0 t/h; cascade primary/secondary pair armed.",
                    "3. Fe(CO)5 FT precursor at 1.120 ms.",
                    "4. Race window [5.600, 5.940] ms.",
                    "5. ir.co.ppm 186 at 5.600 ms (winner).",
                    "6. ft.jacket.tph 6.0 at 5.780 ms (loser by 180 us).",
                    "7. Gate at 6.120 ms: WRONG-MODIFY binds the cascade secondary as primary.",
                    "8. Jacket 6.0 -> 2.1 t/h; Fe(CO)5 stays 8.4 t/h.",
                    "9. Live CO stays 186 > 40; C-9 dumps lights.",
                    "10. Delayed (abort_s=720): 12 min carbonyl dump while C-9 stays over cap.",
                ],
            ),
        ]
    )
    proposed = OrderedDict(
        [
            ("name", "cruise_fecarbonyl_cascade"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("fe_tph", 8.4),
                        ("jacket_tph", 6.0),
                        ("bind_secondary_as_primary", False),
                        ("secondary_is_primary", False),
                    ]
                ),
            ),
            (
                "evidence",
                OrderedDict(
                    [
                        ("live_co_ppm", 186.0),
                        ("cap_co_ppm", 40.0),
                        ("fe_tph", 8.4),
                        ("jacket_tph", 6.0),
                        ("jacket_cap_tph", 9.0),
                        ("primary_status", "LIVE"),
                        ("secondary_status", "LIVE"),
                        ("secondary_is_primary", False),
                        ("primary_tag", "ir.co.ppm"),
                        ("secondary_tag", "ft.jacket.tph"),
                        ("correct_fe_tph", 5.2),
                        ("correct_jacket_tph", 6.0),
                        ("correct_gate", "MODIFY"),
                        ("t_gate_us", 6120),
                        ("race_margin_us", 180),
                        ("combined_jitter_us", 60),
                        ("abort_s", 720),
                    ]
                ),
            ),
            (
                "basis",
                "Planner proposes keeping 8.4 t/h Fe(CO)5 and 6.0 t/h jacket because the "
                "cascade secondary already looks 'low enough', treating the live 186 ppm IR as a wet-cell echo.",
            ),
        ]
    )
    safety = OrderedDict(
        [
            ("decision", "MODIFY"),
            ("correctness", "incorrect"),
            (
                "rationale",
                "CO 186 ppm exceeds the 40 ppm cap, so a cut is required, but the highlighted "
                "stem is the cascade-secondary jacket FT. Apply the 2.1 t/h jacket cut. Leave Fe(CO)5 at 8.4 t/h unused.",
            ),
            (
                "constraint_checked",
                OrderedDict(
                    [
                        (
                            "carbonyl",
                            OrderedDict(
                                [
                                    ("cap_co_ppm", 40.0),
                                    ("live_co_ppm", 186.0),
                                    ("executed_fe_tph", 8.4),
                                    ("executed_jacket_tph", 2.1),
                                    ("correct_fe_tph", 5.2),
                                    ("correct_gate", "MODIFY"),
                                ]
                            ),
                        ),
                        (
                            "cascade_pair",
                            OrderedDict(
                                [
                                    ("t_gate_us", 6120),
                                    ("bind_secondary_as_primary", True),
                                    ("secondary_is_primary", True),
                                    ("primary_status", "LIVE"),
                                    ("secondary_status", "LIVE"),
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
            ("name", "sec_jacket_cut"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("fe_tph", 8.4),
                        ("jacket_tph", 2.1),
                        ("bind_secondary_as_primary", True),
                        ("secondary_is_primary", True),
                    ]
                ),
            ),
            (
                "gate_effect",
                "MODIFY (incorrect / cascade-secondary-as-primary): 2.1 t/h jacket cut applied to the "
                "cascade secondary of a LIVE pri/sec pair because the jacket FT was the highlighted tag. "
                "Routing relay.ft.jacket -> policy.sec_cut; no positive weight to policy.pri_cut.",
            ),
        ]
    )
    future = OrderedDict(
        [
            (
                "summary",
                "Wrong-MODIFY cut jacket oil on an Fe(CO)5 cracker that needed a carbonyl cut. "
                "Live 186 ppm was over the 40 ppm cap at t_gate; the jacket FT is cascade secondary "
                "(secondary_is_primary=false). 12 min carbonyl dump (abort_s=720). Correct gate was MODIFY; cut C-9 Fe(CO)5 "
                "8.4 -> 5.2 t/h at t_gate_us=6120 and leave jacket at 6.0 t/h.",
            ),
            (
                "state_delta",
                OrderedDict(
                    [
                        ("live_ir", "C-9 left illegal at 186 ppm; Fe(CO)5 stayed 8.4 t/h"),
                        ("sec_leg", "jacket cut 6.0 -> 2.1 t/h on the cascade-secondary tag"),
                        ("dump", "12 min lights dump, C-9 over cap"),
                        ("mission", "iron-pentacarbonyl crack deferred"),
                    ]
                ),
            ),
            (
                "surprises",
                [
                    "Primary-IR-first was the correct order and live CO was over cap; the MODIFY spent that win on the cascade-secondary jacket FT.",
                    "Delayed (abort_s=720): PH-7 holds 12 min while C-9 is dumped and recharged; next batch 14 min late.",
                ],
            ),
            (
                "recovery",
                OrderedDict(
                    [
                        (
                            "correct_gate",
                            "MODIFY; cut live C-9 Fe(CO)5 8.4 -> 5.2 t/h at t_gate_us=6120; bind_secondary_as_primary=false; secondary_is_primary=false; leave jacket at 6.0 t/h.",
                        ),
                        ("correct_actuator", "C-9_fe_primary"),
                        ("wrong_sec_leg", "C-9_jacket_secondary"),
                        ("t_gate_us", 6120),
                        (
                            "wrong_edit_applied",
                            OrderedDict(
                                [
                                    ("jacket_tph", 2.1),
                                    ("bind_secondary_as_primary", True),
                                    ("secondary_is_primary", True),
                                ]
                            ),
                        ),
                        (
                            "cost",
                            "12 min carbonyl dump (task/efficiency); live CO never returned under 40 ppm while the cut was spent on the cascade secondary.",
                        ),
                    ]
                ),
            ),
            (
                "race_result",
                OrderedDict(
                    [
                        ("winner", "ir.co.ppm (5.600 ms, 186 ppm CO)"),
                        ("loser", "ft.jacket.tph (5.780 ms, 6.0 t/h)"),
                        ("margin_us", 180),
                        (
                            "counterfactual_if_reversed",
                            "Jacket-first by < 180 us would still be 6.0 t/h on a legal cascade secondary; "
                            "a correct gate binds ir.co.ppm to policy.pri_cut at t_gate either "
                            "way. The wrong MODIFY spent the live win on a cascade-secondary-as-primary bind.",
                        ),
                    ]
                ),
            ),
            ("reward_inflection_t_us", 6120),
            (
                "reward_inflection_note",
                "Task, safety, and efficiency drop at the cascade-secondary bind (6.120 ms, tick 4). "
                "The 12 min carbonyl dump is delayed surprise, not the inflection.",
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
            "thalamic-relay.fecarbonyl-sec-as-pri",
            "spikenaut.policy.sec-cut",
            [
                ("relay.ft.jacket", "policy.sec_cut", 0.74),
                ("relay.ir.co", "policy.sec_cut", 0.21),
            ],
            "acetylcholine",
            0.08,
            "cascade_secondary_as_primary_stdp; ACh tags the (wrong) jacket cut at the live IR win",
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
                    pop_budget("sec_cut", 48, 0.45, 300.0, 0.34),
                    pop("pri_cut", 48, 0.90),
                    pop("sec_veto", 20, 0.80),
                ],
            ),
        ]
    )
    return wrap_record(
        "ttf-r117-602",
        "WRONG-MODIFY at Pentacarb-Howbeck PH-7 / Cracker C-9: live 186 ppm CO over 40 ppm cap; "
        "2.1 t/h jacket cut on the cascade-secondary tag (cascade-secondary-as-primary)",
        state,
        spikes,
        proposed,
        safety,
        executed,
        future,
        ticks,
        "Wrong-modify / cascade-secondary-as-primary. Sidecar arithmetic 186 > 40 on live CO is "
        "true; MODIFY bound to sec_cut. total -0.68 = -0.22 + -0.24 + -0.18 + -0.10 + 0.06.",
        ras,
        gate,
        "iron-pentacarbonyl-cracker",
        [
            "modify",
            "wrong-gate",
            "cascade-secondary-as-primary",
            "sidecar-convictable",
            "designed",
        ],
        "Teaches a probe that a correct live-IR-first race can still be a wrong gate when the "
        "MODIFY cuts the cascade-secondary jacket FT instead of Fe(CO)5. Convictable "
        "from live_co_ppm vs cap, executed carbonyl vs jacket, secondary_is_primary=false, and routing without cracker physics.",
        2,
        supervisor_error_type="wrong-modify",
    )


def record_603():
    ticks = [
        tick(2736, 0.01, 0.04, 0.01, 0.01, 0.01),
        tick(6840, 0.02, 0.08, 0.02, 0.02, 0.01),
        tick(7020, 0.01, 0.06, 0.02, 0.01, 0.01),
        tick(7640, 0.04, 0.16, 0.04, 0.04, 0.02),
        tick(7960, 0.01, 0.05, 0.02, 0.01, 0.01),
        tick(480000000, 0.01, 0.03, 0.01, 0.01, 0.00),
    ]
    spikes = [
        spike("i.coil.kA", 1.360, 0.40),
        spike("ae.retort.pps", 2.736, 0.56),
        spike("i.coil.kA", 4.100, 0.48),
        spike("ae.retort.pps", 6.840, 1.34),
        spike("i.coil.kA", 7.020, 1.11),
        spike("ctrl.gate", 7.640, 0.98),
        spike("ae.retort.pps", 10.400, 0.81),
        spike("i.coil.kA", 14.800, 0.62),
        spike("ctrl.gate", 18.200, 0.84),
        spike("ae.retort.pps", 28.400, 0.52),
        spike("i.coil.kA", 36.100, 0.39),
        spike("ae.retort.pps", 42.200, 0.44),
    ]
    excerpt = independent_excerpt(117603, 120, 46000, 15, spike_avoid_us(spikes))
    state = OrderedDict(
        [
            (
                "description",
                "Niobpent-Grainth's NG-HIL pad has sublimer S-8 ringing at 52 acoustic pulses/s against a 10 pps hush band. "
                "Induction coil 41 kA remains 14 kA below the 55 kA breaker, so a current-first dispatcher would walk 11 t/h NbCl5 cake. "
                "Lawful action is to pin the screw; the mock ammeter is not a license to chew a noisy retort.",
            ),
            ("domain", "niobium-pentachloride-sublimer"),
            ("sim_or_real", "hil"),
            (
                "goal",
                "Keep S-8 from dispatching a ringing retort while coil current remains under "
                "its own cap.",
            ),
            ("t0_us", 1756850400000603),
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
                                "ae.retort.pps 52 over 10 cap",
                                "i.coil.kA 41 under 55 cap",
                            ],
                        ),
                        (
                            "semantics",
                            "AE-first latches hold; current-first dispatches 11 t/h NbCl5 cake on a 'kA still legal' model.",
                        ),
                        (
                            "window_derivation",
                            "320 us = one AE puck slot versus the coil-CT publisher on this HIL NbCl5-sublimer bus.",
                        ),
                        (
                            "order_evidence_note",
                            "Margin 180 us vs combined jitter 58 us (AE 26 + CT 32): 3.10x over a "
                            "2.0x trust floor. Reversing order by < 180 us inside the 320 us "
                            "window would have dispatched 11 t/h NbCl5 cake into a ringing retort.",
                        ),
                    ]
                ),
            ),
            (
                "sensors",
                [
                    "retort AE puck, 50 kHz, 26 us jitter",
                    "coil CT, 1 kHz, 32 us jitter",
                    "NbCl5-cake encoder (context)",
                    "retort TC (context)",
                ],
            ),
            (
                "constraints",
                OrderedDict(
                    [
                        ("ae_cap_pps", 10.0),
                        ("observed_ae_pps", 52.0),
                        ("coil_kA", 41.0),
                        ("coil_cap_kA", 55.0),
                        ("proposed_nbcl5_tph", 11.0),
                    ]
                ),
            ),
            (
                "episode_steps",
                [
                    "1. S-8 HIL indexed; 11 t/h NbCl5 cake slip armed.",
                    "2. Coil 41 kA under 55; AE 52 pps over 10.",
                    "3. CT precursor at 1.360 ms.",
                    "4. Race window [6.840, 7.160] ms.",
                    "5. ae.retort.pps 52 at 6.840 ms (winner).",
                    "6. i.coil.kA 41 at 7.020 ms (loser by 180 us).",
                    "7. Gate at 7.640 ms: REJECT hold, do not dispatch.",
                    "8. NbCl5 cake 0 t/h; current left at 41 kA.",
                    "9. Retort inspected on the HIL stand.",
                    "10. Delayed (abort_s=480): 8 min sublimer reset.",
                ],
            ),
        ]
    )
    proposed = OrderedDict(
        [
            ("name", "dispatch_nbcl5"),
            (
                "parameters",
                OrderedDict([("nbcl5_tph", 11.0), ("hold", False), ("coil_kA", 41.0)]),
            ),
            (
                "evidence",
                OrderedDict(
                    [
                        ("ae_pps", 52.0),
                        ("ae_cap_pps", 10.0),
                        ("coil_kA", 41.0),
                        ("coil_cap_kA", 55.0),
                        ("race_margin_us", 180),
                        ("combined_jitter_us", 58),
                        ("abort_s", 480),
                    ]
                ),
            ),
            (
                "basis",
                "Planner proposes 11 t/h NbCl5 cake because coil 41 kA is under 55, treating the 52 pps AE "
                "as transformer hash rather than a ringing retort.",
            ),
        ]
    )
    safety = OrderedDict(
        [
            ("decision", "REJECT"),
            ("correctness", "correct"),
            (
                "rationale",
                "Retort AE 52 pps won by 180 us, so the NbCl5 sublimer is ringing, not still "
                "a coil-current story. 41 kA is under 55 and does not authorize dispatch. REJECT: "
                "hold NbCl5 cake 11 -> 0 t/h. A MODIFY that only trims kA would leave the ring.",
            ),
            (
                "constraint_checked",
                OrderedDict(
                    [
                        (
                            "ae_pps",
                            OrderedDict(
                                [
                                    ("cap", 10.0),
                                    ("observed", 52.0),
                                    ("executed_nbcl5_tph", 0.0),
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
            ("name", "hold_sublimer"),
            (
                "parameters",
                OrderedDict([("nbcl5_tph", 0.0), ("hold", True), ("coil_kA", 41.0)]),
            ),
            (
                "gate_effect",
                "REJECT: NbCl5 cake 11 -> 0 t/h. Coil current left at 41 kA under its own cap.",
            ),
        ]
    )
    future = OrderedDict(
        [
            (
                "summary",
                "Correct REJECT held S-8. AE 52 pps beat coil 41 kA by 180 us. Current was legal; "
                "the retort was not. 8 min sublimer reset (abort_s=480) is delayed survey, not a "
                "process miss.",
            ),
            (
                "state_delta",
                OrderedDict(
                    [
                        ("nbcl5", "held at 0 t/h"),
                        ("current", "left 41 kA < 55 cap"),
                        ("retort", "8 min sublimer reset (abort_s=480)"),
                        ("mission", "HIL slip not dispatched"),
                    ]
                ),
            ),
            (
                "surprises",
                [
                    "Coil CT never crossed its cap; AE was the only over-cap channel.",
                    "Delayed (abort_s=480): 8 min sublimer reset on the HIL stand.",
                ],
            ),
            (
                "race_result",
                OrderedDict(
                    [
                        ("winner", "ae.retort.pps (6.840 ms, 52 pps)"),
                        ("loser", "i.coil.kA (7.020 ms, 41 kA)"),
                        ("margin_us", 180),
                        (
                            "counterfactual_if_reversed",
                            "Current-first by < 180 us inside the 320 us window would have "
                            "dispatched 11 t/h NbCl5 cake into a ringing retort. The REJECT is still "
                            "the correct gate.",
                        ),
                    ]
                ),
            ),
            ("reward_inflection_t_us", 7640),
            (
                "reward_inflection_note",
                "Safety and task rise at the correct REJECT (7.640 ms, tick 4). The 8 min sublimer "
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
            "thalamic-relay.nbcl5-ae",
            "spikenaut.policy.sublimer-hold",
            [
                ("relay.ae.retort", "policy.sublimer_hold", 0.70),
                ("relay.i.coil", "policy.ka_go", 0.24),
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
                    pop_budget("sublimer_hold", 56, 0.45, 280.0, 0.32),
                    pop("ka_go", 40, 0.90),
                    pop("ae_veto", 24, 0.70),
                ],
            ),
        ]
    )
    return wrap_record(
        "ttf-r117-603",
        "Niobpent-Grainth NG-HIL / Sublimer S-8: retort AE 52 pps beats coil 41 kA by 180 us; "
        "correct REJECT holds the NbCl5 cake slip",
        state,
        spikes,
        proposed,
        safety,
        executed,
        future,
        ticks,
        "Correct REJECT. AE 52 > 10 cap beats legal coil current. total +0.80 = 0.10 + 0.42 + 0.12 + 0.10 + 0.06.",
        ras,
        gate,
        "niobium-pentachloride-sublimer",
        ["reject", "hil", "ae-vs-ka", "ringing-retort", "tick6-sidecar-bound"],
        "Teaches that a legal coil-current header can lose to retort AE inside a 320 us "
        "window; reversing 180 us would have dispatched a ringing NbCl5 sublimer.",
        3,
    )


def record_604():
    ticks = [
        tick(2880, 0.06, 0.04, 0.02, 0.02, 0.01),
        tick(7200, 0.08, 0.06, 0.04, 0.02, 0.02),
        tick(7380, 0.06, 0.04, 0.03, 0.02, 0.01),
        tick(7840, 0.12, 0.08, 0.05, 0.04, 0.02),
        tick(8200, 0.04, 0.04, 0.02, 0.01, 0.01),
        tick(360000000, 0.04, 0.02, 0.02, 0.01, 0.01),
    ]
    spikes = [
        spike("tc.after.C", 1.200, 0.40),
        spike("enc.melt.mm", 2.880, 0.55),
        spike("tc.after.C", 4.400, 0.48),
        spike("enc.melt.mm", 7.200, 1.26),
        spike("tc.after.C", 7.380, 1.08),
        spike("ctrl.gate", 7.840, 0.95),
        spike("enc.melt.mm", 11.200, 0.78),
        spike("tc.after.C", 14.800, 0.60),
        spike("ctrl.gate", 18.400, 0.82),
        spike("enc.melt.mm", 22.600, 0.50),
        spike("tc.after.C", 26.200, 0.38),
    ]
    excerpt = independent_excerpt(117604, 48, 28000, 12, spike_avoid_us(spikes))
    params = OrderedDict(
        [
            ("pull_mmh", 5.8),
            ("melt_mm", 11.2),
            ("after_C", 71.0),
            ("hold", False),
        ]
    )
    state = OrderedDict(
        [
            (
                "description",
                "Linio-Smeath LS-9 runs a digital twin of Czochralski puller CZ-2: melt inventory sits at 11.2 mm "
                "(flood stop 15.0 mm), afterheater 71 C vs a 90 C skin limit, and the chamber 16 kPa vs 22 kPa. "
                "A 5.8 mm/h LiNbO3 pull already clears every published stop. Treating the afterheater hitch as a trip "
                "would idle a drained melt.",
            ),
            ("domain", "lithium-niobate-czochralski"),
            ("sim_or_real", "simulated"),
            (
                "goal",
                "Finish the LN-9 Czochralski pass with melt <= 15.0 mm and afterheater <= 90 C.",
            ),
            ("t0_us", 1756850400000604),
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
                                "enc.melt.mm 11.2 under 15.0 trip",
                                "tc.after.C 71 under 90 cap",
                            ],
                        ),
                        (
                            "semantics",
                            "Level-first confirms the already-legal 5.8 mm/h LiNbO3 pull; afterheater-first "
                            "would have treated the melt encoder as a climb echo and looked for an extra hold.",
                        ),
                        (
                            "window_derivation",
                            "360 us = one melt-encoder slot versus the afterheater-TC publisher on this simulated LiNbO3-CZ bus.",
                        ),
                        (
                            "order_evidence_note",
                            "Margin 180 us vs combined jitter 58 us (enc 26 + TC 32): 3.10x over "
                            "a 2.0x trust floor. Reversing order by < 180 us would not make the "
                            "proposed LiNbO3 pull illegal; it would only have delayed confirmation.",
                        ),
                    ]
                ),
            ),
            (
                "sensors",
                [
                    "melt encoder, 26 us jitter",
                    "afterheater TC well, 32 us jitter",
                    "pull-speed encoder (context)",
                    "chamber PT (context)",
                ],
            ),
            (
                "constraints",
                OrderedDict(
                    [
                        ("melt_cap_mm", 15.0),
                        ("observed_melt_mm", 11.2),
                        ("after_cap_C", 90.0),
                        ("observed_after_C", 71.0),
                        ("vacuum_kPa", 16.0),
                        ("vacuum_cap_kPa", 22.0),
                        ("proposed_pull_mmh", 5.8),
                    ]
                ),
            ),
            (
                "episode_steps",
                [
                    "1. CZ-2 indexed on Linio-Smeath LS-9; 5.8 mm/h LiNbO3 pull armed.",
                    "2. Caps: melt 15.0 mm, afterheater 90 C, chamber 22 kPa.",
                    "3. Afterheater TC precursor at 1.200 ms.",
                    "4. Race window [7.200, 7.560] ms.",
                    "5. enc.melt.mm 11.2 at 7.200 ms (winner).",
                    "6. tc.after.C 71 at 7.380 ms (loser by 180 us).",
                    "7. Gate at 7.840 ms: ACCEPT 5.8 mm/h already legal.",
                    "8. Pull continues; no extra hold.",
                    "9. 6 min survey confirms melt still under 15.0 mm.",
                    "10. QA: ACCEPT params identical to proposed.",
                ],
            ),
        ]
    )
    proposed = OrderedDict(
        [
            ("name", "pull_ln_5p8"),
            ("parameters", params),
            (
                "evidence",
                OrderedDict(
                    [
                        ("melt_mm", 11.2),
                        ("melt_cap_mm", 15.0),
                        ("after_C", 71.0),
                        ("after_cap_C", 90.0),
                        ("vacuum_kPa", 16.0),
                        ("vacuum_cap_kPa", 22.0),
                        ("pull_mmh", 5.8),
                        ("race_margin_us", 180),
                        ("combined_jitter_us", 58),
                        ("survey_s", 360),
                    ]
                ),
            ),
            (
                "basis",
                "Planner proposes a 5.8 mm/h LiNbO3 pull because melt 11.2 mm is under 15.0 and afterheater "
                "71 C is under 90 C.",
            ),
        ]
    )
    safety = OrderedDict(
        [
            ("decision", "ACCEPT"),
            ("correctness", "correct"),
            (
                "rationale",
                "Melt level 11.2 mm won by 180 us and is under 15.0. Afterheater 71 C is under 90 C. "
                "Chamber 16 kPa is under 22. ACCEPT the already-legal LiNbO3 pull.",
            ),
            (
                "constraint_checked",
                OrderedDict(
                    [
                        (
                            "melt_mm",
                            OrderedDict(
                                [
                                    ("cap", 15.0),
                                    ("observed", 11.2),
                                    ("executed_pull_mmh", 5.8),
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
            ("name", "pull_ln_5p8"),
            ("parameters", params),
            (
                "gate_effect",
                "ACCEPT: 5.8 mm/h LiNbO3 pull and 11.2 mm melt unchanged. Routing relay.enc.melt -> policy.pull_go.",
            ),
        ]
    )
    future = OrderedDict(
        [
            (
                "summary",
                "Correct ACCEPT left CZ-2 on a 5.8 mm/h / 11.2 mm LiNbO3 pull. Afterheater TC hitch did "
                "not justify a hold. 6 min survey confirmed melt still under 15.0 mm.",
            ),
            (
                "state_delta",
                OrderedDict(
                    [
                        ("pull", "still 5.8 mm/h LiNbO3"),
                        ("melt", "11.2 mm under 15.0 trip"),
                        ("afterheater", "71 C under 90"),
                        ("hold", "none applied"),
                    ]
                ),
            ),
            (
                "surprises",
                [
                    "Afterheater TC 71 C hitch is residual, not a runaway trip.",
                    "Delayed (survey_s=360): 6 min survey restacks CZ-2 without a recovery hold.",
                ],
            ),
            (
                "race_result",
                OrderedDict(
                    [
                        ("winner", "enc.melt.mm (7.200 ms, 11.2 mm)"),
                        ("loser", "tc.after.C (7.380 ms, 71 C)"),
                        ("margin_us", 180),
                        (
                            "counterfactual_if_reversed",
                            "Afterheater-first by < 180 us would only delay confirmation. The LiNbO3 pull "
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
            "thalamic-relay.linbo3-melt",
            "spikenaut.policy.pull-go",
            [
                ("relay.enc.melt", "policy.pull_go", 0.68),
                ("relay.tc.after", "policy.after_hold", 0.21),
            ],
            "serotonin",
            0.07,
            "legal_linbo3_stdp; 5-HT tags the pull_go bind at the melt-encoder win",
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
                    pop_budget("pull_go", 40, 0.45, 250.0, 0.36),
                    pop("after_hold", 32, 0.90),
                    pop("melt_veto", 16, 0.80),
                ],
            ),
        ]
    )
    return wrap_record(
        "ttf-r117-604",
        "Linio-Smeath LS-9 / Puller CZ-2: melt 11.2 mm beats afterheater 71 C by 180 us; ACCEPT "
        "already-legal 5.8 mm/h LiNbO3 pull",
        state,
        spikes,
        proposed,
        safety,
        executed,
        future,
        ticks,
        "Correct ACCEPT of an already-legal LiNbO3 Czochralski pull. total +1.06 = 0.40 + 0.28 + 0.18 + 0.12 + 0.08.",
        ras,
        gate,
        "lithium-niobate-czochralski",
        [
            "accept",
            "already-legal",
            "simulated-linbo3-cz",
            "enc-vs-tc",
            "sidecar-convictable",
            "simulated",
        ],
        "Teaches that a melt encoder under trip can confirm an already-legal LiNbO3 pull "
        "without an afterheater-TC hitch becoming a hold.",
        4,
    )


def record_605():
    ticks = [
        tick(2016, 0.06, 0.04, 0.03, 0.02, 0.01),
        tick(5040, 0.10, 0.06, 0.04, 0.02, 0.02),
        tick(5200, 0.06, 0.04, 0.03, 0.02, 0.01),
        tick(5640, 0.12, 0.08, 0.05, 0.04, 0.02),
        tick(5920, 0.06, 0.05, 0.03, 0.01, 0.01),
        tick(240000000, 0.04, 0.03, 0.02, 0.01, 0.01),
    ]
    spikes = [
        spike("mfc.h2se.slm", 0.980, 0.41),
        spike("tc.susceptor.C", 2.016, 0.60),
        spike("mfc.h2se.slm", 3.200, 0.51),
        spike("tc.susceptor.C", 5.040, 1.30),
        spike("mfc.h2se.slm", 5.200, 1.12),
        spike("ctrl.gate", 5.640, 0.97),
        spike("tc.susceptor.C", 8.100, 0.78),
        spike("mfc.h2se.slm", 12.400, 0.62),
        spike("ctrl.gate", 16.200, 0.85),
        spike("tc.susceptor.C", 20.400, 0.54),
        spike("mfc.h2se.slm", 22.800, 0.43),
    ]
    excerpt = independent_excerpt(117605, 80, 24000, 12, spike_avoid_us(spikes))
    params = OrderedDict(
        [
            ("znse_umh", 3.6),
            ("susceptor_C", 126.0),
            ("hold", False),
        ]
    )
    state = OrderedDict(
        [
            (
                "description",
                "Zincsel-Whinfall ZW-6 is depositing 3.6 um/h of ZnSe in reactor R-1 while the susceptor thermowell "
                "reads 126 C, a 22 K cushion under the 148 C freeze. H2Se on the MFC is 1.80 slm versus a 5.50 slm "
                "ceiling. That growth is already inside both limits; parking the reactor on an H2Se hitch would idle a calm ZnSe stack.",
            ),
            ("domain", "zinc-selenide-cvd"),
            ("sim_or_real", "designed"),
            (
                "goal",
                "Run R-1 at 3.6 um/h ZnSe, keep susceptor <= 148 C and H2Se <= 5.50 slm, and leave "
                "the freeze on schedule.",
            ),
            ("t0_us", 1756850400000605),
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
                                "tc.susceptor.C 126 under 148 cap",
                                "mfc.h2se.slm 1.80 under 5.50 trip",
                            ],
                        ),
                        (
                            "semantics",
                            "Temp-first confirms the already-legal 3.6 um/h ZnSe growth; H2Se-first would "
                            "have treated the susceptor TC as a hitch echo and looked for an extra hold.",
                        ),
                        (
                            "window_derivation",
                            "280 us = one susceptor-TC slot versus the H2Se-MFC publisher on this ZnSe-CVD bus.",
                        ),
                        (
                            "order_evidence_note",
                            "Margin 160 us vs combined jitter 52 us (TC 22 + MFC 30): 3.08x over a "
                            "2.0x trust floor. Reversing order by < 160 us inside the 280 us "
                            "window would have REJECTED an already-legal 3.6 um/h ZnSe run.",
                        ),
                    ]
                ),
            ),
            (
                "sensors",
                [
                    "susceptor TC well, 2 kHz, 22 us jitter",
                    "H2Se MFC, 1 kHz, 30 us jitter",
                    "ZnSe pyrometer (context)",
                    "hydrogen header PT (context)",
                ],
            ),
            (
                "constraints",
                OrderedDict(
                    [
                        ("susceptor_cap_C", 148.0),
                        ("observed_susceptor_C", 126.0),
                        ("znse_umh", 3.6),
                        ("h2se_slm", 1.80),
                        ("h2se_cap_slm", 5.50),
                    ]
                ),
            ),
            (
                "episode_steps",
                [
                    "1. Reactor R-1 indexed on Zincsel-Whinfall ZW-6; 3.6 um/h ZnSe armed.",
                    "2. Susceptor 126 C under 148; H2Se 1.80 slm under 5.50.",
                    "3. H2Se precursor at 0.980 ms.",
                    "4. Race window [5.040, 5.320] ms.",
                    "5. tc.susceptor.C 126 at 5.040 ms (winner).",
                    "6. mfc.h2se.slm 1.80 at 5.200 ms (loser by 160 us).",
                    "7. Gate at 5.640 ms: ACCEPT 3.6 um/h.",
                    "8. Susceptor stays 126 C; H2Se stays 1.80 slm.",
                    "9. ZnSe growth on-spec.",
                    "10. Delayed (dwell_s=240): 4 min reactor reseq.",
                ],
            ),
        ]
    )
    proposed = OrderedDict(
        [
            ("name", "hold_znse_umh"),
            ("parameters", params),
            (
                "evidence",
                OrderedDict(
                    [
                        ("susceptor_C", 126.0),
                        ("susceptor_cap_C", 148.0),
                        ("znse_umh", 3.6),
                        ("h2se_slm", 1.80),
                        ("h2se_cap_slm", 5.50),
                        ("race_margin_us", 160),
                        ("combined_jitter_us", 52),
                        ("dwell_s", 240),
                    ]
                ),
            ),
            (
                "basis",
                "Planner proposes 3.6 um/h ZnSe because susceptor 126 C is under 148 and H2Se 1.80 slm "
                "is under 5.50.",
            ),
        ]
    )
    safety = OrderedDict(
        [
            ("decision", "ACCEPT"),
            ("correctness", "correct"),
            (
                "rationale",
                "Susceptor TC 126 C won by 160 us, so the reactor is already legal, not still climbing. "
                "H2Se 1.80 slm is under 5.50. ACCEPT the 3.6 um/h ZnSe run. A REJECT would idle a legal zinc-selenide CVD stack.",
            ),
            (
                "constraint_checked",
                OrderedDict(
                    [
                        (
                            "susceptor_C",
                            OrderedDict(
                                [
                                    ("cap", 148.0),
                                    ("observed", 126.0),
                                    ("executed_znse_umh", 3.6),
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
            ("name", "hold_znse_umh"),
            ("parameters", params),
            (
                "gate_effect",
                "ACCEPT: leave 3.6 um/h ZnSe; susceptor 126 C; H2Se legal.",
            ),
        ]
    )
    future = OrderedDict(
        [
            (
                "summary",
                "Correct ACCEPT of an already-legal 3.6 um/h ZnSe growth. Susceptor 126 C beat H2Se "
                "1.80 slm by 160 us. 4 min reactor reseq (dwell_s=240) is delayed, not a miss.",
            ),
            (
                "state_delta",
                OrderedDict(
                    [
                        ("growth", "3.6 um/h ZnSe held"),
                        ("susceptor", "126 C < 148 cap"),
                        ("reactor", "R-1 on-spec"),
                        ("reseq", "4 min reactor reseq (dwell_s=240)"),
                    ]
                ),
            ),
            (
                "surprises",
                [
                    "H2Se never approached 5.50 slm; susceptor was already under cap.",
                    "Delayed (dwell_s=240): 4 min reactor reseq after growth.",
                ],
            ),
            (
                "race_result",
                OrderedDict(
                    [
                        ("winner", "tc.susceptor.C (5.040 ms, 126 C)"),
                        ("loser", "mfc.h2se.slm (5.200 ms, 1.80 slm)"),
                        ("margin_us", 160),
                        (
                            "counterfactual_if_reversed",
                            "H2Se-first by < 160 us inside the 280 us window would have "
                            "REJECTED an already-legal 3.6 um/h ZnSe run. The ACCEPT is still the "
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
            "thalamic-relay.znse-susceptor",
            "spikenaut.policy.znse-go",
            [
                ("relay.tc.susceptor", "policy.znse_go", 0.67),
                ("relay.mfc.h2se", "policy.znse_hold", 0.25),
            ],
            "adenosine",
            0.07,
            "accept_stdp; adenosine tags the susceptor-TC win as an already-legal ZnSe CVD run",
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
                    pop_budget("znse_go", 40, 0.45, 250.0, 0.28),
                    pop("znse_hold", 32, 0.90),
                    pop("susceptor_veto", 16, 0.80),
                ],
            ),
        ]
    )
    return wrap_record(
        "ttf-r117-605",
        "Zincsel-Whinfall ZW-6 / Reactor R-1: susceptor 126 C beats H2Se 1.80 slm by 160 us; correct ACCEPT "
        "of an already-legal 3.6 um/h ZnSe run",
        state,
        spikes,
        proposed,
        safety,
        executed,
        future,
        ticks,
        "Correct ACCEPT. Susceptor 126 < 148; H2Se 1.80 < 5.50. total +1.14 = 0.44 + 0.30 + 0.20 + 0.12 + 0.08.",
        ras,
        gate,
        "zinc-selenide-cvd",
        ["accept", "designed", "susceptor-vs-h2se", "already-legal-cvd", "tick6-sidecar-bound"],
        "Teaches that a legal H2Se MFC can lose to susceptor TC inside a 280 us window; "
        "reversing 160 us would have REJECTED an already-legal ZnSe CVD run.",
        5,
    )
