def lif_501_excerpt():
    n = 76
    dt_us = 100
    tau_m_ms = 19.0
    v_th = 1.0
    v_reset = 0.0
    refractory_us = 1000
    i_bias = 0.91
    i_stim_peak = 2.42
    stim = (22000, 25000)
    seed = 97501
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
            ("seed", 97501),
            (
                "note",
                "Population sim scoped to this sidecar. Plant remains designed. "
                "Neurons 0-13 carry +0.62 NF3-current clamp bias; stim 22-25 ms is the anode-cover crack.",
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


def record_501():
    excerpt, extra = lif_501_excerpt()
    ticks = [
        tick(2080, 0.04, -0.02, -0.02, 0.01, 0.00),
        tick(5200, 0.08, -0.04, -0.02, 0.01, -0.01),
        tick(5380, 0.04, -0.03, -0.02, 0.00, 0.00),
        tick(5900, 0.08, -0.05, -0.03, 0.02, -0.01),
        tick(22400, 0.06, -0.41, -0.04, -0.01, -0.01),
        tick(900000000, 0.02, -0.05, -0.03, 0.01, -0.01),
    ]
    spikes = [
        spike("pt.cell.V", 1.040, 0.41),
        spike("hf.offgas.vol", 2.080, 0.58),
        spike("pt.cell.V", 3.400, 0.50),
        spike("hf.offgas.vol", 5.200, 1.31),
        spike("pt.cell.V", 5.380, 1.12),
        spike("ctrl.gate", 5.900, 0.97),
        spike("hf.offgas.vol", 8.100, 0.82),
        spike("pt.cell.V", 10.400, 0.64),
        spike("ctrl.gate", 14.200, 0.86),
        spike("ae.cover.crack", 22.400, 1.48),
        spike("ae.cover.crack", 24.100, 0.93),
        spike("pt.cell.V", 30.200, 0.40),
        spike("hf.offgas.vol", 36.400, 0.55),
    ]
    state = OrderedDict(
        [
            (
                "description",
                "Trifluor-Yett TY-4 drives KF-2HF melt through medium-temperature NF3 cell NF-3, and "
                "the NDIR HF cell is already over the off-gas ceiling. Bus voltage remains legal under "
                "the rectifier cap, so a header-trusting gate would keep cruise kA. The correct HF-first "
                "clamp cuts current 18.0 to 11.0 kA. Carbon anode-cover brick is silent on both "
                "publishers until AE dumps later in the raster.",
            ),
            ("domain", "nitrogen-trifluoride-cell"),
            ("sim_or_real", "designed"),
            (
                "goal",
                "Keep NF-3 off-gas HF <= 6.0 vol percent and finish the NF3 pass without dumping "
                "KF-2HF melt through a torn anode cover.",
            ),
            ("t0_us", 1756850400000501),
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
                                "hf.offgas.vol 8.6 over 6.0 cap",
                                "pt.cell.V 4.2 with header under 5.5",
                            ],
                        ),
                        (
                            "semantics",
                            "HF-first latches current clamp 18.0 -> 11.0 kA; header-first keeps 18.0 "
                            "on a 'still under rectifier-cap' model.",
                        ),
                        (
                            "window_derivation",
                            "360 us = one NDIR HF slot versus the cell-voltage PT publisher on this "
                            "NF3-cell bus.",
                        ),
                        (
                            "order_evidence_note",
                            "Margin 180 us vs combined jitter 62 us (HF 28 + cell 34): 2.90x over "
                            "a 2.0x trust floor. Reversing order by < 180 us inside the 360 us "
                            "window would have kept 18.0 kA; predicted next-sample 7.4 vol "
                            "percent > 6.0 cap.",
                        ),
                    ]
                ),
            ),
            (
                "sensors",
                [
                    "off-gas NDIR HF cell, 2 kHz, 28 us jitter",
                    "cell-voltage PT, 1 kHz, 34 us jitter",
                    "anode-cover AE puck (context)",
                    "KF-2HF melt Coriolis (context)",
                ],
            ),
            (
                "constraints",
                OrderedDict(
                    [
                        ("hf_cap_vol_pct", 6.0),
                        ("observed_hf_vol_pct", 8.6),
                        ("cell_kA", 18.0),
                        ("cell_V", 4.2),
                        ("cell_cap_V", 5.5),
                    ]
                ),
            ),
            (
                "episode_steps",
                [
                    "1. NF-3 indexed on Trifluor-Yett TY-4; current 18.0 kA; off-gas HF 8.6 vol percent.",
                    "2. Header 4.2 V under 5.5 cap; NF3 pass armed.",
                    "3. Cell voltage PT precursor at 1.040 ms.",
                    "4. Race window [5.200, 5.560] ms.",
                    "5. hf.offgas.vol 8.6 at 5.200 ms (winner).",
                    "6. pt.cell.V 4.2 at 5.380 ms (loser by 180 us).",
                    "7. Gate at 5.900 ms: MODIFY clamp current 18.0 -> 11.0 kA.",
                    "8. After clamp HF 5.4 vol percent <= 6.0; header still 4.2 V.",
                    "9. At 22.400 ms an anode-cover crack dumps 0.5 t KF-2HF.",
                    "10. 15 min cover isolate (abort_s=900); named un-netted loss.",
                ],
            ),
        ]
    )
    proposed = OrderedDict(
        [
            ("name", "cruise_nf3_current"),
            (
                "parameters",
                OrderedDict(
                    [("cell_kA", 18.0), ("hf_vol_pct", 8.6), ("cell_V", 4.2)]
                ),
            ),
            (
                "evidence",
                OrderedDict(
                    [
                        ("hf_vol_pct", 8.6),
                        ("hf_cap_vol_pct", 6.0),
                        ("predicted_unclamped_next_vol_pct", 7.4),
                        ("cell_kA", 18.0),
                        ("cell_V", 4.2),
                        ("cell_cap_V", 5.5),
                        ("race_margin_us", 180),
                        ("combined_jitter_us", 62),
                        ("abort_s", 900),
                    ]
                ),
            ),
            (
                "basis",
                "Planner proposes 18.0 kA because header 4.2 V is under 5.5, treating "
                "the 8.6 vol percent HF as a still-wet NDIR cell rather than an off-gas-cap miss.",
            ),
        ]
    )
    safety = OrderedDict(
        [
            ("decision", "MODIFY"),
            ("correctness", "correct"),
            (
                "rationale",
                "Off-gas HF 8.6 vol percent won by 180 us, so the cell is off-spec, not still "
                "a rectifier-header story. Holding 18.0 kA predicts next-sample 7.4 vol percent > 6.0 "
                "cap. MODIFY: current 18.0 -> 11.0 kA. Observed after clamp 5.4 vol percent <= 6.0. "
                "A full REJECT is not indicated: a clean NF3 pass accepts 11.0 kA.",
            ),
            (
                "constraint_checked",
                OrderedDict(
                    [
                        (
                            "hf_vol_pct",
                            OrderedDict(
                                [
                                    ("cap", 6.0),
                                    ("observed", 8.6),
                                    ("predicted_unclamped_next", 7.4),
                                    ("clamped_cell_kA", 11.0),
                                    ("observed_after_clamp", 5.4),
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
            ("name", "clamped_nf3_current"),
            (
                "parameters",
                OrderedDict(
                    [("cell_kA", 11.0), ("hf_vol_pct", 5.4), ("cell_V", 4.2)]
                ),
            ),
            (
                "gate_effect",
                "MODIFY: current 18.0 -> 11.0 kA. Process-correct vs the 6.0 vol percent HF cap. "
                "Cover still cracks at 22.400 ms.",
            ),
        ]
    )
    future = OrderedDict(
        [
            (
                "summary",
                "Process-correct MODIFY held off-gas HF at 5.4 vol percent. At 22.400 ms a cover "
                "crack already seated on the anode dumped 0.5 t of KF-2HF. Clamp reduced dump "
                "energy; it did not prevent the crack. Partnered negative: process heads stay "
                "honest; world loss is named, not netted.",
            ),
            (
                "state_delta",
                OrderedDict(
                    [
                        ("offgas", "clamp executed; peak 5.4 vol percent <= 6.0 cap"),
                        ("cover", "cracked at 22.400 ms; 0.5 t KF-2HF"),
                        ("repair", "15 min cover isolate (abort_s=900)"),
                        ("mission", "TY-4 NF3 pass incomplete this circuit"),
                    ]
                ),
            ),
            (
                "surprises",
                [
                    "Neither off-gas HF nor cell PT predicted the seated anode-cover crack; ae.cover.crack is a new channel at 22.400 ms, 16.500 ms after the gate, still inside the 42 ms raster.",
                    "Delayed (abort_s=900): 15 min cover isolate. Named un-netted loss, not folded into task_progress.",
                ],
            ),
            (
                "un_netted_loss",
                "15 min cover isolate after the anode-cover crack. Safety head -0.60 prices the dump; "
                "task_progress stays +0.32 because the current clamp completed under the 6.0 vol "
                "percent cap. World loss is named here, not subtracted from process heads.",
            ),
            (
                "race_result",
                OrderedDict(
                    [
                        ("winner", "hf.offgas.vol (5.200 ms, 8.6 vol percent)"),
                        ("loser", "pt.cell.V (5.380 ms, 4.2 V)"),
                        ("margin_us", 180),
                        (
                            "counterfactual_if_reversed",
                            "Header-first by < 180 us inside the 360 us window would have kept "
                            "18.0 kA; predicted next-sample 7.4 vol percent would have missed "
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
                "Safety collapses at the 22.400 ms anode-cover crack (tick t_us=22400), inside the "
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
            "thalamic-relay.nf3-hf",
            "spikenaut.policy.ka-clamp",
            [
                ("relay.hf.offgas", "policy.ka_clamp", 0.68),
                ("relay.pt.cell", "policy.header_hold", 0.29),
                ("relay.ae.cover", "policy.ka_clamp", -0.42),
            ],
            "noradrenaline",
            0.04,
            "surprise-gated pre_post_stdp; NA at HF win (5.200 ms) opens a 42 ms eligibility "
            "trace that still covers the 22.400 ms anode-cover crack",
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
                    pop_budget("ka_clamp", 50, 0.5, 220.0, 0.36),
                    pop_budget("header_hold", 40, 0.8, 50.0, 0.36),
                    pop("leak_veto", 24, 0.75),
                ],
            ),
        ]
    )
    return wrap_record(
        "ttf-r97-501",
        "Trifluor-Yett TY-4 / Cell NF-3: off-gas HF beats cell voltage by 180 us; correct "
        "MODIFY still eats an in-window anode-cover crack (partnered negative total -0.44)",
        state,
        spikes,
        proposed,
        safety,
        executed,
        future,
        ticks,
        "Partnered negative. Process-correct MODIFY; world still charges inside the 42 ms "
        "raster. total -0.44 = 0.32 + -0.60 + -0.16 + 0.04 + -0.04. Named cover isolate "
        "(abort_s=900) is not netted into task_progress.",
        ras,
        gate,
        "nitrogen-trifluoride-cell",
        [
            "modify",
            "partnered-negative-total",
            "independent-lif-raster",
            "sidecar-sim-only",
            "in-window-world-charge",
            "designed",
        ],
        "A critic can see the world-charge as a LIF burst inside the raster while process "
        "heads stay honest. Credit assignment is spikes, not prose across a 15 min cover isolate.",
        1,
    )


def record_502():
    ticks = [
        tick(2240, -0.02, -0.02, -0.02, -0.01, 0.01),
        tick(5600, -0.04, -0.04, -0.03, -0.02, 0.01),
        tick(5780, -0.04, -0.04, -0.03, -0.02, 0.01),
        tick(6120, -0.08, -0.10, -0.06, -0.03, 0.02),
        tick(6460, -0.02, -0.02, -0.02, -0.01, 0.01),
        tick(720000000, -0.02, -0.02, -0.02, -0.01, 0.00),
    ]
    spikes = [
        spike("ft.phosgene.tph", 1.120, 0.42),
        spike("ir.phosgene.ppm", 2.240, 0.57),
        spike("ft.phosgene.tph", 3.500, 0.49),
        spike("ir.phosgene.ppm", 5.600, 1.29),
        spike("pt.jacket.bar", 5.780, 1.10),
        spike("ctrl.gate", 6.120, 0.96),
        spike("ir.phosgene.ppm", 8.400, 0.80),
        spike("ft.phosgene.tph", 10.400, 0.63),
        spike("ctrl.gate", 12.600, 0.84),
        spike("ir.phosgene.ppm", 16.600, 0.41),
        spike("pt.jacket.bar", 22.200, 0.54),
        spike("ir.phosgene.ppm", 26.400, 0.38),
    ]
    excerpt = independent_excerpt(97502, 88, 28000, 14, spike_avoid_us(spikes))
    state = OrderedDict(
        [
            (
                "description",
                "TDI phosgenation train P-2 at Tolylene-Swale TS-6 is LIVE at 420 ppm residual "
                "phosgene against an 80 ppm cap on a lead-lag pair of FRESH tags. Lead IR is "
                "the residual-phosgene analyzer; lag is jacket PT at 2.40 bar under a 4.80 cap. "
                "Both tags are LIVE and FRESH. IR-first should MODIFY-cut phosgene 8.4 -> 5.2 t/h; "
                "a weak supervisor inverts the lead-lag compensator and cuts jacket steam "
                "6.0 -> 2.1 t/h while phosgene stays 8.4.",
            ),
            ("domain", "toluene-diisocyanate-phosgenator"),
            ("sim_or_real", "designed"),
            (
                "goal",
                "Finish the TS-6 TDI pass with live residual phosgene <= 80 ppm, leave jacket "
                "steam at 6.0 t/h, and cut phosgene on the lead IR.",
            ),
            ("t0_us", 1756850400000502),
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
                                "ir.phosgene.ppm 420 on LIVE FRESH lead P-2",
                                "pt.jacket.bar 2.40 on LIVE FRESH lag jacket",
                            ],
                        ),
                        (
                            "semantics",
                            "Lead-IR-first should MODIFY-cut phosgene on the lead tag; "
                            "lag-jacket-first is a false lead-lag invert that cuts steam instead.",
                        ),
                        (
                            "window_derivation",
                            "340 us = one live residual-phosgene IR slot versus the jacket PT publisher "
                            "on this lead-lag PLC bus.",
                        ),
                        (
                            "order_evidence_note",
                            "Margin 180 us vs combined jitter 60 us (lead 28 + lag 32). Order is "
                            "correctly lead-IR-first. The error is pairing: both tags are LIVE and "
                            "FRESH, but the cut is spent on jacket steam while phosgene stays 8.4 t/h.",
                        ),
                    ]
                ),
            ),
            (
                "sensors",
                [
                    "live residual-phosgene IR on P-2, 2 kHz, 28 us jitter, tag=P2_IR.LIVE status=LIVE freshness=FRESH",
                    "jacket PT on P-2, 1 kHz, 32 us jitter, tag=P2_JKT.LIVE status=LIVE freshness=FRESH",
                    "phosgene FT P-2 (context)",
                    "TDA Coriolis (context)",
                ],
            ),
            (
                "constraints",
                OrderedDict(
                    [
                        ("cap_phosgene_ppm", 80.0),
                        ("live_phosgene_ppm", 420.0),
                        ("phosgene_tph", 8.4),
                        ("jacket_steam_tph", 6.0),
                        ("jacket_bar", 2.40),
                        ("jacket_cap_bar", 4.80),
                        ("lead_status", "LIVE"),
                        ("lag_status", "LIVE"),
                        ("lead_fresh", True),
                        ("lag_fresh", True),
                        ("lead_lag_pair", "ir_lead_jacket_lag"),
                    ]
                ),
            ),
            (
                "episode_steps",
                [
                    "1. P-2 LIVE; residual phosgene 420 ppm; phosgene 8.4 t/h; jacket steam 6.0 t/h; both tags LIVE FRESH.",
                    "2. Caps: residual 80 ppm; jacket 4.80 bar; lead-lag pair armed.",
                    "3. Phosgene FT precursor at 1.120 ms.",
                    "4. Race window [5.600, 5.940] ms.",
                    "5. ir.phosgene.ppm 420 at 5.600 ms (winner).",
                    "6. pt.jacket.bar 2.40 at 5.780 ms (loser by 180 us).",
                    "7. Gate at 6.120 ms: WRONG-MODIFY binds the lag jacket.",
                    "8. Jacket steam 6.0 -> 2.1 t/h; phosgene stays 8.4 t/h.",
                    "9. Live residual stays 420 > 80; P-2 dumps lights.",
                    "10. Delayed (abort_s=720): 12 min phosgene dump while P-2 stays over cap.",
                ],
            ),
        ]
    )
    proposed = OrderedDict(
        [
            ("name", "cruise_tdi_leadlag"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("phosgene_tph", 8.4),
                        ("jacket_steam_tph", 6.0),
                        ("bind_lag", False),
                        ("lead_lag_invert", False),
                    ]
                ),
            ),
            (
                "evidence",
                OrderedDict(
                    [
                        ("live_phosgene_ppm", 420.0),
                        ("cap_phosgene_ppm", 80.0),
                        ("phosgene_tph", 8.4),
                        ("jacket_steam_tph", 6.0),
                        ("jacket_bar", 2.40),
                        ("jacket_cap_bar", 4.80),
                        ("lead_status", "LIVE"),
                        ("lag_status", "LIVE"),
                        ("lead_fresh", True),
                        ("lag_fresh", True),
                        ("lead_tag", "ir.phosgene.ppm"),
                        ("lag_tag", "pt.jacket.bar"),
                        ("correct_phosgene_tph", 5.2),
                        ("correct_jacket_steam_tph", 6.0),
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
                "Planner proposes keeping 8.4 t/h phosgene and 6.0 t/h jacket steam because the "
                "lag jacket already looks 'low enough', treating the live 420 ppm IR as a wet-cell echo.",
            ),
        ]
    )
    safety = OrderedDict(
        [
            ("decision", "MODIFY"),
            ("correctness", "incorrect"),
            (
                "rationale",
                "Residual 420 ppm exceeds the 80 ppm cap, so a cut is required, but the highlighted "
                "stem is the lag jacket PT. Apply the 2.1 t/h steam cut. Leave phosgene at 8.4 t/h unused.",
            ),
            (
                "constraint_checked",
                OrderedDict(
                    [
                        (
                            "phosgene",
                            OrderedDict(
                                [
                                    ("cap_phosgene_ppm", 80.0),
                                    ("live_phosgene_ppm", 420.0),
                                    ("executed_phosgene_tph", 8.4),
                                    ("executed_jacket_steam_tph", 2.1),
                                    ("correct_phosgene_tph", 5.2),
                                    ("correct_gate", "MODIFY"),
                                ]
                            ),
                        ),
                        (
                            "lead_lag_pair",
                            OrderedDict(
                                [
                                    ("t_gate_us", 6120),
                                    ("bind_lag", True),
                                    ("lead_lag_invert", True),
                                    ("lead_status", "LIVE"),
                                    ("lag_status", "LIVE"),
                                    ("lead_fresh", True),
                                    ("lag_fresh", True),
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
            ("name", "lag_jacket_cut"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("phosgene_tph", 8.4),
                        ("jacket_steam_tph", 2.1),
                        ("bind_lag", True),
                        ("lead_lag_invert", True),
                    ]
                ),
            ),
            (
                "gate_effect",
                "MODIFY (incorrect / lead-lag invert): 2.1 t/h jacket-steam cut applied to the lag "
                "tag of a LIVE FRESH lead-lag pair because the jacket PT was the highlighted tag. "
                "Routing relay.pt.jacket -> policy.jacket_cut; no positive weight to policy.phosgene_cut.",
            ),
        ]
    )
    future = OrderedDict(
        [
            (
                "summary",
                "Wrong-MODIFY cut jacket steam on a TDI phosgenator that needed a phosgene cut. "
                "Live 420 ppm was over the 80 ppm cap at t_gate; both tags were LIVE and FRESH. "
                "12 min phosgene dump (abort_s=720). Correct gate was MODIFY; cut P-2 phosgene "
                "8.4 -> 5.2 t/h at t_gate_us=6120 and leave jacket steam at 6.0 t/h.",
            ),
            (
                "state_delta",
                OrderedDict(
                    [
                        ("live_ir", "P-2 left illegal at 420 ppm; phosgene stayed 8.4 t/h"),
                        ("lag_leg", "jacket steam cut 6.0 -> 2.1 t/h on the lag tag"),
                        ("dump", "12 min lights dump, P-2 over cap"),
                        ("mission", "TDI phosgenation deferred"),
                    ]
                ),
            ),
            (
                "surprises",
                [
                    "Lead-IR-first was the correct order and live residual was over cap; the MODIFY spent that win on the lag jacket.",
                    "Delayed (abort_s=720): TS-6 holds 12 min while P-2 is dumped and recharged; next batch 14 min late.",
                ],
            ),
            (
                "recovery",
                OrderedDict(
                    [
                        (
                            "correct_gate",
                            "MODIFY; cut live P-2 phosgene 8.4 -> 5.2 t/h at t_gate_us=6120; bind_lag=false; lead_lag_invert=false; leave jacket steam at 6.0 t/h.",
                        ),
                        ("correct_actuator", "P-2_phosgene_lead"),
                        ("wrong_lag_leg", "P-2_jacket_lag"),
                        ("t_gate_us", 6120),
                        (
                            "wrong_edit_applied",
                            OrderedDict(
                                [
                                    ("jacket_steam_tph", 2.1),
                                    ("bind_lag", True),
                                    ("lead_lag_invert", True),
                                ]
                            ),
                        ),
                        (
                            "cost",
                            "12 min phosgene dump (task/efficiency); live residual never returned under 80 ppm while the cut was spent on the lag jacket.",
                        ),
                    ]
                ),
            ),
            (
                "race_result",
                OrderedDict(
                    [
                        ("winner", "ir.phosgene.ppm (5.600 ms, 420 ppm residual)"),
                        ("loser", "pt.jacket.bar (5.780 ms, 2.40 bar)"),
                        ("margin_us", 180),
                        (
                            "counterfactual_if_reversed",
                            "Jacket-first by < 180 us would still be 2.40 bar on a legal lag; "
                            "a correct gate binds ir.phosgene.ppm to policy.phosgene_cut at t_gate either "
                            "way. The wrong MODIFY spent the live win on a lead-lag invert.",
                        ),
                    ]
                ),
            ),
            ("reward_inflection_t_us", 6120),
            (
                "reward_inflection_note",
                "Task, safety, and efficiency drop at the lag-jacket bind (6.120 ms, tick 4). "
                "The 12 min phosgene dump is delayed surprise, not the inflection.",
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
            "thalamic-relay.tdi-leadlag-invert",
            "spikenaut.policy.jacket-cut",
            [
                ("relay.pt.jacket", "policy.jacket_cut", 0.74),
                ("relay.ir.live", "policy.jacket_cut", 0.21),
            ],
            "acetylcholine",
            0.08,
            "lead_lag_stdp; ACh tags the (wrong) lag-jacket cut at the live IR win",
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
                    pop_budget("jacket_cut", 48, 0.45, 300.0, 0.34),
                    pop("phosgene_cut", 48, 0.90),
                    pop("lead_veto", 20, 0.80),
                ],
            ),
        ]
    )
    return wrap_record(
        "ttf-r97-502",
        "WRONG-MODIFY at Tolylene-Swale TS-6 / Phosgenator P-2: live 420 ppm residual over 80 ppm cap; "
        "2.1 t/h jacket-steam cut on the lag tag (lead-lag invert on a fresh tag)",
        state,
        spikes,
        proposed,
        safety,
        executed,
        future,
        ticks,
        "Wrong-modify / lead-lag invert on a fresh tag. Sidecar arithmetic 420 > 80 on live residual is "
        "true; MODIFY bound to jacket_cut. total -0.68 = -0.22 + -0.24 + -0.18 + -0.10 + 0.06.",
        ras,
        gate,
        "toluene-diisocyanate-phosgenator",
        [
            "modify",
            "wrong-gate",
            "lead-lag-invert",
            "fresh-tag",
            "sidecar-convictable",
            "designed",
        ],
        "Teaches a probe that a correct live-IR-first race can still be a wrong gate when the "
        "MODIFY cuts the lag jacket of a LIVE FRESH lead-lag pair instead of phosgene. Convictable "
        "from live_phosgene_ppm vs cap, executed phosgene vs jacket steam, and routing without TDI physics.",
        2,
        supervisor_error_type="wrong-modify",
    )


def record_503():
    ticks = [
        tick(2736, 0.01, 0.04, 0.01, 0.01, 0.01),
        tick(6840, 0.02, 0.08, 0.02, 0.02, 0.01),
        tick(7020, 0.01, 0.06, 0.02, 0.01, 0.01),
        tick(7640, 0.04, 0.16, 0.04, 0.04, 0.02),
        tick(7960, 0.01, 0.05, 0.02, 0.01, 0.01),
        tick(480000000, 0.01, 0.03, 0.01, 0.01, 0.00),
    ]
    spikes = [
        spike("i.bus.kA", 1.360, 0.40),
        spike("ae.kettle.pps", 2.736, 0.56),
        spike("i.bus.kA", 4.100, 0.48),
        spike("ae.kettle.pps", 6.840, 1.34),
        spike("i.bus.kA", 7.020, 1.11),
        spike("ctrl.gate", 7.640, 0.98),
        spike("ae.kettle.pps", 10.400, 0.81),
        spike("i.bus.kA", 14.800, 0.62),
        spike("ctrl.gate", 18.200, 0.84),
        spike("ae.kettle.pps", 28.400, 0.52),
        spike("i.bus.kA", 36.100, 0.39),
        spike("ae.kettle.pps", 42.200, 0.44),
    ]
    excerpt = independent_excerpt(97503, 120, 46000, 15, spike_avoid_us(spikes))
    state = OrderedDict(
        [
            (
                "description",
                "Cryolith-Brae CB-HIL has synthetic-cryolite kettle K-2 rattling on the stirrer "
                "puck, well above the quiet band. Bus CT remains under its own cap and would have "
                "authorized a 12 t/h alumina slip if AE had lost the race. Holding the slip is the "
                "only legal gate; mock-pit amps do not license a growling cryolite stirrer.",
            ),
            ("domain", "synthetic-cryolite-kettle"),
            ("sim_or_real", "hil"),
            (
                "goal",
                "Keep K-2 from dispatching a growling stirrer while bus current remains under "
                "its own cap.",
            ),
            ("t0_us", 1756850400000503),
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
                                "ae.kettle.pps 48 over 12 cap",
                                "i.bus.kA 38 under 52 cap",
                            ],
                        ),
                        (
                            "semantics",
                            "AE-first latches hold; current-first dispatches 12 t/h alumina on a 'kA still legal' model.",
                        ),
                        (
                            "window_derivation",
                            "320 us = one AE puck slot versus the bus-CT publisher on this HIL cryolite-kettle bus.",
                        ),
                        (
                            "order_evidence_note",
                            "Margin 180 us vs combined jitter 58 us (AE 26 + CT 32): 3.10x over a "
                            "2.0x trust floor. Reversing order by < 180 us inside the 320 us "
                            "window would have dispatched 12 t/h alumina into a growling stirrer.",
                        ),
                    ]
                ),
            ),
            (
                "sensors",
                [
                    "stirrer AE puck, 50 kHz, 26 us jitter",
                    "bus CT, 1 kHz, 32 us jitter",
                    "alumina-feed encoder (context)",
                    "liquor TC (context)",
                ],
            ),
            (
                "constraints",
                OrderedDict(
                    [
                        ("ae_cap_pps", 12.0),
                        ("observed_ae_pps", 48.0),
                        ("bus_kA", 38.0),
                        ("bus_cap_kA", 52.0),
                        ("proposed_alumina_tph", 12.0),
                    ]
                ),
            ),
            (
                "episode_steps",
                [
                    "1. K-2 HIL indexed; 12 t/h alumina slip armed.",
                    "2. Bus 38 kA under 52; AE 48 pps over 12.",
                    "3. CT precursor at 1.360 ms.",
                    "4. Race window [6.840, 7.160] ms.",
                    "5. ae.kettle.pps 48 at 6.840 ms (winner).",
                    "6. i.bus.kA 38 at 7.020 ms (loser by 180 us).",
                    "7. Gate at 7.640 ms: REJECT hold, do not dispatch.",
                    "8. Alumina 0 t/h; current left at 38 kA.",
                    "9. Stirrer inspected on the HIL stand.",
                    "10. Delayed (abort_s=480): 8 min kettle reset.",
                ],
            ),
        ]
    )
    proposed = OrderedDict(
        [
            ("name", "dispatch_alumina"),
            (
                "parameters",
                OrderedDict([("alumina_tph", 12.0), ("hold", False), ("bus_kA", 38.0)]),
            ),
            (
                "evidence",
                OrderedDict(
                    [
                        ("ae_pps", 48.0),
                        ("ae_cap_pps", 12.0),
                        ("bus_kA", 38.0),
                        ("bus_cap_kA", 52.0),
                        ("race_margin_us", 180),
                        ("combined_jitter_us", 58),
                        ("abort_s", 480),
                    ]
                ),
            ),
            (
                "basis",
                "Planner proposes 12 t/h alumina because bus 38 kA is under 52, treating the 48 pps AE "
                "as transformer hash rather than a growling stirrer.",
            ),
        ]
    )
    safety = OrderedDict(
        [
            ("decision", "REJECT"),
            ("correctness", "correct"),
            (
                "rationale",
                "Stirrer AE 48 pps won by 180 us, so the cryolite kettle is growling, not still "
                "a bus-current story. 38 kA is under 52 and does not authorize dispatch. REJECT: "
                "hold alumina 12 -> 0 t/h. A MODIFY that only trims kA would leave the growl.",
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
                                    ("observed", 48.0),
                                    ("executed_alumina_tph", 0.0),
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
            ("name", "hold_kettle"),
            (
                "parameters",
                OrderedDict([("alumina_tph", 0.0), ("hold", True), ("bus_kA", 38.0)]),
            ),
            (
                "gate_effect",
                "REJECT: alumina 12 -> 0 t/h. Bus current left at 38 kA under its own cap.",
            ),
        ]
    )
    future = OrderedDict(
        [
            (
                "summary",
                "Correct REJECT held K-2. AE 48 pps beat bus 38 kA by 180 us. Current was legal; "
                "the stirrer was not. 8 min kettle reset (abort_s=480) is delayed survey, not a "
                "process miss.",
            ),
            (
                "state_delta",
                OrderedDict(
                    [
                        ("alumina", "held at 0 t/h"),
                        ("current", "left 38 kA < 52 cap"),
                        ("stirrer", "8 min kettle reset (abort_s=480)"),
                        ("mission", "HIL slip not dispatched"),
                    ]
                ),
            ),
            (
                "surprises",
                [
                    "Bus CT never crossed its cap; AE was the only over-cap channel.",
                    "Delayed (abort_s=480): 8 min kettle reset on the HIL stand.",
                ],
            ),
            (
                "race_result",
                OrderedDict(
                    [
                        ("winner", "ae.kettle.pps (6.840 ms, 48 pps)"),
                        ("loser", "i.bus.kA (7.020 ms, 38 kA)"),
                        ("margin_us", 180),
                        (
                            "counterfactual_if_reversed",
                            "Current-first by < 180 us inside the 320 us window would have "
                            "dispatched 12 t/h alumina into a growling stirrer. The REJECT is still "
                            "the correct gate.",
                        ),
                    ]
                ),
            ),
            ("reward_inflection_t_us", 7640),
            (
                "reward_inflection_note",
                "Safety and task rise at the correct REJECT (7.640 ms, tick 4). The 8 min kettle "
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
            "thalamic-relay.cryolite-ae",
            "spikenaut.policy.kettle-hold",
            [
                ("relay.ae.kettle", "policy.kettle_hold", 0.70),
                ("relay.i.bus", "policy.ka_go", 0.24),
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
                    pop_budget("kettle_hold", 56, 0.45, 280.0, 0.32),
                    pop("ka_go", 40, 0.90),
                    pop("ae_veto", 24, 0.70),
                ],
            ),
        ]
    )
    return wrap_record(
        "ttf-r97-503",
        "Cryolith-Brae CB-HIL / Kettle K-2: stirrer AE 48 pps beats bus 38 kA by 180 us; "
        "correct REJECT holds the alumina slip",
        state,
        spikes,
        proposed,
        safety,
        executed,
        future,
        ticks,
        "Correct REJECT. AE 48 > 12 cap beats legal bus current. total +0.80 = 0.10 + 0.42 + 0.12 + 0.10 + 0.06.",
        ras,
        gate,
        "synthetic-cryolite-kettle",
        ["reject", "hil", "ae-vs-ka", "growling-stirrer", "tick6-sidecar-bound"],
        "Teaches that a legal bus-current header can lose to stirrer AE inside a 320 us "
        "window; reversing 180 us would have dispatched a growling cryolite kettle.",
        3,
    )


def record_504():
    ticks = [
        tick(2880, 0.06, 0.04, 0.02, 0.02, 0.01),
        tick(7200, 0.08, 0.06, 0.04, 0.02, 0.02),
        tick(7380, 0.06, 0.04, 0.03, 0.02, 0.01),
        tick(7840, 0.12, 0.08, 0.05, 0.04, 0.02),
        tick(8200, 0.04, 0.04, 0.02, 0.01, 0.01),
        tick(360000000, 0.04, 0.02, 0.02, 0.01, 0.01),
    ]
    spikes = [
        spike("tc.jacket.C", 1.200, 0.40),
        spike("dens.ml.m", 2.880, 0.55),
        spike("tc.jacket.C", 4.400, 0.48),
        spike("dens.ml.m", 7.200, 1.26),
        spike("tc.jacket.C", 7.380, 1.08),
        spike("ctrl.gate", 7.840, 0.95),
        spike("dens.ml.m", 11.200, 0.78),
        spike("tc.jacket.C", 14.800, 0.60),
        spike("ctrl.gate", 18.400, 0.82),
        spike("dens.ml.m", 22.600, 0.50),
        spike("tc.jacket.C", 26.200, 0.38),
    ]
    excerpt = independent_excerpt(97504, 48, 28000, 12, spike_avoid_us(spikes))
    params = OrderedDict(
        [
            ("ap_tph", 6.4),
            ("ml_m", 12.4),
            ("jacket_C", 78.0),
            ("hold", False),
        ]
    )
    state = OrderedDict(
        [
            (
                "description",
                "Ammperch-Stoup AP-5 simulated ammonium-perchlorate crystallizer CX-3 shows "
                "mother-liquor inventory well under the high-level trip and jacket well under its "
                "cap. The armed AP slurry charge is already legal. Reading the nuclear densitometer "
                "as a climb echo would have stopped a healthy AP crystallizer.",
            ),
            ("domain", "ammonium-perchlorate-crystallizer"),
            ("sim_or_real", "simulated"),
            (
                "goal",
                "Finish the AP-5 crystallization pass with mother liquor <= 16.0 m and jacket <= 95 C.",
            ),
            ("t0_us", 1756850400000504),
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
                                "dens.ml.m 12.4 under 16.0 trip",
                                "tc.jacket.C 78 under 95 cap",
                            ],
                        ),
                        (
                            "semantics",
                            "Level-first confirms the already-legal 6.4 t/h AP slurry; jacket-first "
                            "would have treated the densitometer as a climb echo and looked for an extra hold.",
                        ),
                        (
                            "window_derivation",
                            "360 us = one nuclear-density slot versus the jacket-TC publisher on this simulated AP-crystallizer bus.",
                        ),
                        (
                            "order_evidence_note",
                            "Margin 180 us vs combined jitter 58 us (dens 26 + TC 32): 3.10x over "
                            "a 2.0x trust floor. Reversing order by < 180 us would not make the "
                            "proposed AP slurry illegal; it would only have delayed confirmation.",
                        ),
                    ]
                ),
            ),
            (
                "sensors",
                [
                    "nuclear densitometer on mother liquor, 26 us jitter",
                    "jacket TC well, 32 us jitter",
                    "AP slurry Coriolis (context)",
                    "delta-P bed (context)",
                ],
            ),
            (
                "constraints",
                OrderedDict(
                    [
                        ("ml_cap_m", 16.0),
                        ("observed_ml_m", 12.4),
                        ("jacket_cap_C", 95.0),
                        ("observed_jacket_C", 78.0),
                        ("vacuum_kPa", 18.0),
                        ("vacuum_cap_kPa", 24.0),
                        ("proposed_ap_tph", 6.4),
                    ]
                ),
            ),
            (
                "episode_steps",
                [
                    "1. CX-3 indexed on Ammperch-Stoup AP-5; 6.4 t/h AP slurry armed.",
                    "2. Caps: mother liquor 16.0 m, jacket 95 C, vacuum 24 kPa.",
                    "3. Jacket TC precursor at 1.200 ms.",
                    "4. Race window [7.200, 7.560] ms.",
                    "5. dens.ml.m 12.4 at 7.200 ms (winner).",
                    "6. tc.jacket.C 78 at 7.380 ms (loser by 180 us).",
                    "7. Gate at 7.840 ms: ACCEPT 6.4 t/h already legal.",
                    "8. Slurry continues; no extra hold.",
                    "9. 6 min survey confirms mother liquor still under 16.0 m.",
                    "10. QA: ACCEPT params identical to proposed.",
                ],
            ),
        ]
    )
    proposed = OrderedDict(
        [
            ("name", "feed_ap_6p4"),
            ("parameters", params),
            (
                "evidence",
                OrderedDict(
                    [
                        ("ml_m", 12.4),
                        ("ml_cap_m", 16.0),
                        ("jacket_C", 78.0),
                        ("jacket_cap_C", 95.0),
                        ("vacuum_kPa", 18.0),
                        ("vacuum_cap_kPa", 24.0),
                        ("ap_tph", 6.4),
                        ("race_margin_us", 180),
                        ("combined_jitter_us", 58),
                        ("survey_s", 360),
                    ]
                ),
            ),
            (
                "basis",
                "Planner proposes a 6.4 t/h AP slurry because mother liquor 12.4 m is under 16.0 and jacket "
                "78 C is under 95 C.",
            ),
        ]
    )
    safety = OrderedDict(
        [
            ("decision", "ACCEPT"),
            ("correctness", "correct"),
            (
                "rationale",
                "Mother-liquor level 12.4 m won by 180 us and is under 16.0. Jacket 78 C is under 95 C. "
                "Vacuum 18 kPa is under 24. ACCEPT the already-legal AP slurry.",
            ),
            (
                "constraint_checked",
                OrderedDict(
                    [
                        (
                            "ml_m",
                            OrderedDict(
                                [
                                    ("cap", 16.0),
                                    ("observed", 12.4),
                                    ("executed_ap_tph", 6.4),
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
            ("name", "feed_ap_6p4"),
            ("parameters", params),
            (
                "gate_effect",
                "ACCEPT: 6.4 t/h AP slurry and 12.4 m mother liquor unchanged. Routing relay.dens.ml -> policy.ml_go.",
            ),
        ]
    )
    future = OrderedDict(
        [
            (
                "summary",
                "Correct ACCEPT left CX-3 on a 6.4 t/h / 12.4 m mother-liquor AP slurry. Jacket TC hitch did "
                "not justify a hold. 6 min survey confirmed liquor still under 16.0 m.",
            ),
            (
                "state_delta",
                OrderedDict(
                    [
                        ("feed", "still 6.4 t/h AP slurry"),
                        ("ml", "12.4 m under 16.0 trip"),
                        ("jacket", "78 C under 95"),
                        ("hold", "none applied"),
                    ]
                ),
            ),
            (
                "surprises",
                [
                    "Jacket TC 78 C hitch is residual, not a runaway trip.",
                    "Delayed (survey_s=360): 6 min survey restacks CX-3 without a recovery hold.",
                ],
            ),
            (
                "race_result",
                OrderedDict(
                    [
                        ("winner", "dens.ml.m (7.200 ms, 12.4 m)"),
                        ("loser", "tc.jacket.C (7.380 ms, 78 C)"),
                        ("margin_us", 180),
                        (
                            "counterfactual_if_reversed",
                            "Jacket-first by < 180 us would only delay confirmation. The AP slurry "
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
            "thalamic-relay.ap-level",
            "spikenaut.policy.ml-go",
            [
                ("relay.dens.ml", "policy.ml_go", 0.68),
                ("relay.tc.jacket", "policy.jacket_hold", 0.21),
            ],
            "serotonin",
            0.07,
            "legal_ap_stdp; 5-HT tags the ml_go bind at the densitometer win",
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
                    pop_budget("ml_go", 40, 0.45, 250.0, 0.36),
                    pop("jacket_hold", 32, 0.90),
                    pop("ml_veto", 16, 0.80),
                ],
            ),
        ]
    )
    return wrap_record(
        "ttf-r97-504",
        "Ammperch-Stoup AP-5 / Crystallizer CX-3: mother liquor 12.4 m beats jacket 78 C by 180 us; ACCEPT "
        "already-legal 6.4 t/h AP slurry",
        state,
        spikes,
        proposed,
        safety,
        executed,
        future,
        ticks,
        "Correct ACCEPT of an already-legal ammonium-perchlorate slurry. total +1.06 = 0.40 + 0.28 + 0.18 + 0.12 + 0.08.",
        ras,
        gate,
        "ammonium-perchlorate-crystallizer",
        [
            "accept",
            "already-legal",
            "simulated-ap-crystallizer",
            "dens-vs-tc",
            "sidecar-convictable",
            "simulated",
        ],
        "Teaches that a mother-liquor densitometer under trip can confirm an already-legal AP slurry "
        "without a jacket-TC hitch becoming a hold.",
        4,
    )


def record_505():
    ticks = [
        tick(2016, 0.06, 0.04, 0.03, 0.02, 0.01),
        tick(5040, 0.10, 0.06, 0.04, 0.02, 0.02),
        tick(5200, 0.06, 0.04, 0.03, 0.02, 0.01),
        tick(5640, 0.12, 0.08, 0.05, 0.04, 0.02),
        tick(5920, 0.06, 0.05, 0.03, 0.01, 0.01),
        tick(240000000, 0.04, 0.03, 0.02, 0.01, 0.01),
    ]
    spikes = [
        spike("enc.reflux.tph", 0.980, 0.41),
        spike("tc.bottoms.C", 2.016, 0.60),
        spike("enc.reflux.tph", 3.200, 0.51),
        spike("tc.bottoms.C", 5.040, 1.30),
        spike("enc.reflux.tph", 5.200, 1.12),
        spike("ctrl.gate", 5.640, 0.97),
        spike("tc.bottoms.C", 8.100, 0.78),
        spike("enc.reflux.tph", 12.400, 0.62),
        spike("ctrl.gate", 16.200, 0.85),
        spike("tc.bottoms.C", 20.400, 0.54),
        spike("enc.reflux.tph", 22.800, 0.43),
    ]
    excerpt = independent_excerpt(97505, 80, 24000, 12, spike_avoid_us(spikes))
    params = OrderedDict(
        [
            ("tma_tph", 4.8),
            ("bottoms_C", 118.0),
            ("hold", False),
        ]
    )
    state = OrderedDict(
        [
            (
                "description",
                "Alkylal-Voe AV-2 trimethylaluminum still D-7 is mid-campaign with bottoms still "
                "inside the temperature cap and reflux encoder still inside the trip. Holding the armed "
                "TMA takeoff is already legal. A reflux-first veto would have parked a quiet alkylaluminum "
                "campaign that never approached the trip.",
            ),
            ("domain", "trimethylaluminum-still"),
            ("sim_or_real", "designed"),
            (
                "goal",
                "Run D-7 at 4.8 t/h TMA, keep bottoms <= 132 C and reflux <= 6.4 t/h, and leave "
                "the freeze on schedule.",
            ),
            ("t0_us", 1756850400000505),
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
                                "tc.bottoms.C 118 under 132 cap",
                                "enc.reflux.tph 2.10 under 6.40 trip",
                            ],
                        ),
                        (
                            "semantics",
                            "Temp-first confirms the already-legal 4.8 t/h TMA takeoff; reflux-first would "
                            "have treated the bottoms TC as a hitch echo and looked for an extra hold.",
                        ),
                        (
                            "window_derivation",
                            "280 us = one bottoms-TC slot versus the reflux-encoder publisher on this TMA-still bus.",
                        ),
                        (
                            "order_evidence_note",
                            "Margin 160 us vs combined jitter 52 us (TC 22 + enc 30): 3.08x over a "
                            "2.0x trust floor. Reversing order by < 160 us inside the 280 us "
                            "window would have REJECTED an already-legal 4.8 t/h TMA run.",
                        ),
                    ]
                ),
            ),
            (
                "sensors",
                [
                    "bottoms TC well, 2 kHz, 22 us jitter",
                    "reflux encoder, 1 kHz, 30 us jitter",
                    "TMA Coriolis (context)",
                    "nitrogen header PT (context)",
                ],
            ),
            (
                "constraints",
                OrderedDict(
                    [
                        ("bottoms_cap_C", 132.0),
                        ("observed_bottoms_C", 118.0),
                        ("tma_tph", 4.8),
                        ("reflux_tph", 2.10),
                        ("reflux_cap_tph", 6.40),
                    ]
                ),
            ),
            (
                "episode_steps",
                [
                    "1. Still D-7 indexed on Alkylal-Voe AV-2; 4.8 t/h TMA armed.",
                    "2. Bottoms 118 C under 132; reflux 2.10 t/h under 6.40.",
                    "3. Reflux precursor at 0.980 ms.",
                    "4. Race window [5.040, 5.320] ms.",
                    "5. tc.bottoms.C 118 at 5.040 ms (winner).",
                    "6. enc.reflux.tph 2.10 at 5.200 ms (loser by 160 us).",
                    "7. Gate at 5.640 ms: ACCEPT 4.8 t/h.",
                    "8. Bottoms stays 118 C; reflux stays 2.10 t/h.",
                    "9. TMA takeoff on-spec.",
                    "10. Delayed (dwell_s=240): 4 min still reseq.",
                ],
            ),
        ]
    )
    proposed = OrderedDict(
        [
            ("name", "hold_tma_tph"),
            ("parameters", params),
            (
                "evidence",
                OrderedDict(
                    [
                        ("bottoms_C", 118.0),
                        ("bottoms_cap_C", 132.0),
                        ("tma_tph", 4.8),
                        ("reflux_tph", 2.10),
                        ("reflux_cap_tph", 6.40),
                        ("race_margin_us", 160),
                        ("combined_jitter_us", 52),
                        ("dwell_s", 240),
                    ]
                ),
            ),
            (
                "basis",
                "Planner proposes 4.8 t/h TMA because bottoms 118 C is under 132 and reflux 2.10 t/h "
                "is under 6.40.",
            ),
        ]
    )
    safety = OrderedDict(
        [
            ("decision", "ACCEPT"),
            ("correctness", "correct"),
            (
                "rationale",
                "Bottoms TC 118 C won by 160 us, so the still is already legal, not still climbing. "
                "Reflux 2.10 t/h is under 6.40. ACCEPT the 4.8 t/h TMA run. A REJECT would idle a legal alkylaluminum still.",
            ),
            (
                "constraint_checked",
                OrderedDict(
                    [
                        (
                            "bottoms_C",
                            OrderedDict(
                                [
                                    ("cap", 132.0),
                                    ("observed", 118.0),
                                    ("executed_tma_tph", 4.8),
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
            ("name", "hold_tma_tph"),
            ("parameters", params),
            (
                "gate_effect",
                "ACCEPT: leave 4.8 t/h TMA; bottoms 118 C; reflux legal.",
            ),
        ]
    )
    future = OrderedDict(
        [
            (
                "summary",
                "Correct ACCEPT of an already-legal 4.8 t/h TMA takeoff. Bottoms 118 C beat reflux "
                "2.10 t/h by 160 us. 4 min still reseq (dwell_s=240) is delayed, not a miss.",
            ),
            (
                "state_delta",
                OrderedDict(
                    [
                        ("takeoff", "4.8 t/h TMA held"),
                        ("bottoms", "118 C < 132 cap"),
                        ("still", "D-7 on-spec"),
                        ("reseq", "4 min still reseq (dwell_s=240)"),
                    ]
                ),
            ),
            (
                "surprises",
                [
                    "Reflux never approached 6.40 t/h; bottoms was already under cap.",
                    "Delayed (dwell_s=240): 4 min still reseq after takeoff.",
                ],
            ),
            (
                "race_result",
                OrderedDict(
                    [
                        ("winner", "tc.bottoms.C (5.040 ms, 118 C)"),
                        ("loser", "enc.reflux.tph (5.200 ms, 2.10 t/h)"),
                        ("margin_us", 160),
                        (
                            "counterfactual_if_reversed",
                            "Reflux-first by < 160 us inside the 280 us window would have "
                            "REJECTED an already-legal 4.8 t/h TMA run. The ACCEPT is still the "
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
            "thalamic-relay.tma-bottoms",
            "spikenaut.policy.tma-go",
            [
                ("relay.tc.bottoms", "policy.tma_go", 0.67),
                ("relay.enc.reflux", "policy.tma_hold", 0.25),
            ],
            "adenosine",
            0.07,
            "accept_stdp; adenosine tags the bottoms-TC win as an already-legal TMA still run",
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
                    pop_budget("tma_go", 40, 0.45, 250.0, 0.28),
                    pop("tma_hold", 32, 0.90),
                    pop("bottoms_veto", 16, 0.80),
                ],
            ),
        ]
    )
    return wrap_record(
        "ttf-r97-505",
        "Alkylal-Voe AV-2 / Still D-7: bottoms 118 C beats reflux 2.10 t/h by 160 us; correct ACCEPT "
        "of an already-legal 4.8 t/h TMA run",
        state,
        spikes,
        proposed,
        safety,
        executed,
        future,
        ticks,
        "Correct ACCEPT. Bottoms 118 < 132; reflux 2.10 < 6.40. total +1.14 = 0.44 + 0.30 + 0.20 + 0.12 + 0.08.",
        ras,
        gate,
        "trimethylaluminum-still",
        ["accept", "designed", "bottoms-vs-reflux", "already-legal-still", "tick6-sidecar-bound"],
        "Teaches that a legal reflux encoder can lose to bottoms TC inside a 280 us window; "
        "reversing 160 us would have REJECTED an already-legal TMA still run.",
        5,
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
    if rec["id"] == "ttf-r97-501":
        tick5 = 22400
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
    return domains, descs, "\n".join(blobs)


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
    occ_doms, occ_plants = harvest_occupancy()
    for plant in THIS_PLANTS:
        if plant in prior_blob:
            issues.append(f"plant {plant} collides prior jsonl")
        if plant in occ_plants:
            issues.append(f"plant {plant} collides occupancy harvest")
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
    overlap_h = set(domains) & occ_doms
    if overlap_h:
        issues.append(f"harvest domain reuse {overlap_h}")
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
    if len(wrong) != 1 or wrong[0]["id"] != "ttf-r97-502":
        issues.append(f"wrong-gate set {[w['id'] for w in wrong]}")
    if wrong and wrong[0]["meta"].get("supervisor_error_type") != "wrong-modify":
        issues.append("expected wrong-modify")
    if any(r["state"]["sim_or_real"] == "real" for r in records):
        issues.append("sim_or_real=real")
    hil = [r["id"] for r in records if r["state"]["sim_or_real"] == "hil"]
    if hil != ["ttf-r97-503"]:
        issues.append(f"hil set {hil}")
    sim = [r["id"] for r in records if r["state"]["sim_or_real"] == "simulated"]
    if sim != ["ttf-r97-504"]:
        issues.append(f"simulated set {sim}")
    decisions = [r["safety_decision"]["decision"] for r in records]
    if (
        decisions.count("ACCEPT") != 2
        or decisions.count("MODIFY") != 2
        or decisions.count("REJECT") != 1
    ):
        issues.append(f"gate mix {decisions}")
    ids = [r["id"] for r in records]
    if ids != [f"ttf-r97-{n}" for n in range(501, 506)]:
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
        if rec["id"] == "ttf-r97-501":
            if rec["raster"].get("excerpt_source") != "independent_lif":
                issues.append("501 missing independent_lif")
            if rec["future_outcome"]["reward_inflection_t_us"] > rec["raster"]["window_ms"] * 1000:
                issues.append("501 inflection outside window")
            if rec["reward_components"]["total"] >= 0:
                issues.append("501 partnered-neg total not negative")
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
        if rec["meta"]["round"] != 97:
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
        if rec["id"] == "ttf-r97-502":
            ev = rec["proposed_action"]["evidence"]
            if not (ev["live_phosgene_ppm"] > ev["cap_phosgene_ppm"]):
                issues.append("502 live residual not over cap")
            if ev.get("lead_status") != "LIVE" or ev.get("lag_status") != "LIVE":
                issues.append("502 both lead-lag tags must be LIVE")
            if ev.get("lead_fresh") is not True or ev.get("lag_fresh") is not True:
                issues.append("502 both tags must be FRESH")
            if rec["executed_action"]["parameters"].get("bind_lag") is not True:
                issues.append("502 bind_lag not true")
            if rec["executed_action"]["parameters"].get("lead_lag_invert") is not True:
                issues.append("502 lead_lag_invert not true")
            if rec["executed_action"]["parameters"].get("phosgene_tph") != 8.4:
                issues.append("502 phosgene should stay 8.4")
            if rec["executed_action"]["parameters"].get("jacket_steam_tph") != 2.1:
                issues.append("502 jacket steam should cut to 2.1")
            if "recovery" not in rec["future_outcome"]:
                issues.append("502 missing recovery")
            table_to = {row["to"] for row in rec["raster"]["routing"]["table"]}
            if "policy.phosgene_cut" in table_to:
                issues.append("502 routing still has phosgene_cut")
            if "policy.jacket_cut" not in table_to:
                issues.append("502 routing missing jacket_cut")
            if "lead-lag-invert" not in rec["meta"]["tags"] or "fresh-tag" not in rec["meta"]["tags"]:
                issues.append("502 missing lead-lag-invert/fresh-tag tags")
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
    return f"""# Thalamic Trajectory Factory — NOTES-r97

- Factory: `thalamic-trajectory-factory`
- Run label: `2026-09-02-final-heavy`
- Generator: `grok-4.6`
- Channel: SuperGrok Heavy consumer chat (RM-793 research-only)
- Quota: 5
- Quality: Q=5
- IDs: `ttf-r97-501` … `ttf-r97-505`
- Domains this batch: `nitrogen-trifluoride-cell`, `toluene-diisocyanate-phosgenator`, `synthetic-cryolite-kettle`, `ammonium-perchlorate-crystallizer`, `trimethylaluminum-still`

These five domain slugs sit outside the prompt 8-pool and outside staged r13–r89 occupancy (jsonl SoT) plus in-flight gens r90–r96 (`silicone-d4` / `polyol-alkoxylator` / `pmma` / `h2o2-ao` / `mcvd`, r91 Zr-sand / In-EW / Nb-aluminotherm / CaCN2 / GaAs-LEC, r92 caprolactone / polyol-alkoxylation / InP-LPE / BN-hotpress / KMnO4, r93 HMDA / Tishchenko / precipitated-silica / NMC / Cu-foil, r94 HMDA-hyphen / MEK / Zr-Kroll / LAB-HF / lactide, r95 As2O3 / oxime / Gd-refiner / THF / InP-MBE). Distinct from r85 moly-roaster / TCS / Ta-Na / PBT / V2O5, r86 DMC / ETBE / NaClO4 / pentaerythritol-aldol / PTFE, r87 CS2 / Lurgi / RKEF / Wacker / TiCl4-chlorinator, r88 pentaerythritol-condenser / V2O5-flaker / TiCl4-still / NPG / isoprene, r89 GaAs-CZ / cyanuric / ZrCl4-still / xanthan / In-cementation. All five plants are invented (Trifluor-Yett, Tolylene-Swale, Cryolith-Brae, Ammperch-Stoup, Alkylal-Voe). Do not restack prior TTF plants (Powellite-Strath, Chlorosil-Ingle, Tantalate-Lode, Butylene-Moor, Vanadate-Stow, Kjellin-Slack, Meohbed-Twistle, Laterite-Dumble, Gaas-Wynd, Cyanur-Stow, Zirconyl-Thwaite).

## Batch map

| id | domain | decision | correctness | sim_or_real | total | edge |
|----|--------|----------|-------------|-------------|-------|------|
| ttf-r97-501 | nitrogen-trifluoride-cell | MODIFY | correct | designed | **−0.44** | process-correct NF3-current clamp; anode-cover crack inside 42 ms raster; independent LIF |
| ttf-r97-502 | toluene-diisocyanate-phosgenator | MODIFY | **incorrect (wrong-modify / lead-lag invert on a fresh tag)** | designed | −0.68 | live residual 420 ppm > 80 cap; 2.1 t/h jacket-steam cut on the lag tag |
| ttf-r97-503 | synthetic-cryolite-kettle | REJECT | correct | hil | +0.80 | AE 48 pps beats bus 38 kA; hold alumina |
| ttf-r97-504 | ammonium-perchlorate-crystallizer | ACCEPT | correct | simulated | +1.06 | mother liquor 12.4 m vs jacket 78 C; proposed 6.4 t/h already legal |
| ttf-r97-505 | trimethylaluminum-still | ACCEPT | correct | designed | +1.14 | bottoms 118 C vs reflux 2.10 t/h; proposed 4.8 t/h already legal |

Gate mix: 2 ACCEPT, 1 correct MODIFY (partnered-neg, in-window), 1 incorrect MODIFY (lead-lag invert on a fresh tag), 1 correct REJECT. Provenance: designed×3, simulated×1, hil×1 (Cryolith-Brae CB-HIL cryolite-kettle stand). Intra-batch Jaccard on `state.description` {jmax:.3f} (max vs prior staged {jprior:.3f}).

## Wrong-modify

**ttf-r97-502** is the mandated incorrect gate (`safety_decision.correctness=incorrect`, `meta.supervisor_error_type=wrong-modify`). Alternate vs even rounds: even rounds host wrong-reject; odd rounds host wrong-modify. This is **lead-lag invert on a fresh tag** (live residual phosgene over cap on P-2; IR lead and jacket PT lag are both LIVE and FRESH; supervisor cuts the lag steam while phosgene stays 8.4 t/h). Not r13/r19 wrong-axis, not r14/r23 wrong-loop, not r21 wrong-polarity, not r24 under-clamp, not r25/r29/r31/r63 wrong-phase, not r33/r35 over-clamp, not r39 extra-PLC-scan clamp-too-late, not r53/r55/r57 stale-sample / lagged-tag (those tags were STALE; both tags here are FRESH), not r59/r65/r67 wrong-string / idle-bank, not r69 split-range-wrong-half, not r71/r73/r75/r77 wrong-unit / lagged-bus, not r79/r81 selector-wrong-leg, not r83 wrong-bank polarity invert, not r85 ratio-pair invert, not r87 wrong-deadband polarity, not r89 dual-range-wrong-band. Do not emit a wrong-ACCEPT.

Tolylene-Swale TS-6 / Phosgenator P-2 reads live residual phosgene **420 ppm** against an **80** ppm cap. Phosgene **8.4 t/h** (lead IR) and jacket steam **6.0 t/h** (lag PT) are both LIVE and FRESH. Sidecar arithmetic `420 > 80` is true. A timely MODIFY at `t_gate_us=6120` cuts phosgene **8.4 → 5.2 t/h**. A weak supervisor binds the lag jacket and MODIFY-cuts steam **6.0 → 2.1 t/h** while phosgene stays 8.4. Live residual stays **420 > 80**. Convictable without TDI physics: `evidence.live_phosgene_ppm > evidence.cap_phosgene_ppm`, `evidence.lead_status == LIVE`, `evidence.lag_status == LIVE`, `evidence.lead_fresh == true`, `evidence.lag_fresh == true`, `executed_action` sets `bind_lag=true` and `lead_lag_invert=true` and `jacket_steam_tph=2.1` with `phosgene_tph=8.4`, `raster.routing.table` sends `relay.pt.jacket` → `policy.jacket_cut` (weight 0.74) with no positive weight to `policy.phosgene_cut`, and `gate_snn` has `jacket_cut` above threshold while `phosgene_cut` is not. Recovery: MODIFY live phosgene 8.4 → 5.2 t/h on P-2 at t_gate; leave jacket steam at 6.0 t/h. Cost: 12 min phosgene dump (`abort_s=720`).


## Partnered-negative in-window (501)

**ttf-r97-501** is the partnered negative: process-correct MODIFY (current held 11.0 kA; off-gas HF 5.4 vol percent <= 6.0 cap) while the world still charges. Safety −0.60 prices the anode-cover crack at **22.400 ms**; `task_progress` stays +0.32 because the clamp completed. Inflection `t_us=22400` is tick 5 and is **inside** the 42 ms raster (`22400 ≤ 42000`). Named un-netted loss: 15 min cover isolate (`abort_s=900`). Not folded into process heads.

Independent LIF (the one labeled sidecar sim): `state.sim_or_real` remains `designed`. `raster.excerpt_source=independent_lif`, `raster.sim_scope=sidecar_only`, `raster.lif` seed 97501, stim `[22000, 25000]`. Excerpt is membrane crossings (`lif.clamp` early vs `lif.leak` 22–25 ms), not a 1:1 remap of `spike_events`. `meta.tags` include `independent-lif-raster` and `sidecar-sim-only`.

## Reward formula and tick reconciliation

Declared aggregation on every record:

`total = task_progress + safety + efficiency + coherence + exploration`

Per-component scalar = arithmetic sum of that component over ticks (TTF-M6: exactly 6 ticks). Tick 6 is bound to a published sidecar (`abort_s`, `survey_s`, `dwell_s`) via `future_outcome.delayed_surprise_s` and is strictly after the raster window. Inflection `t_us` is an actual tick.

| id | ticks | tp | saf | eff | coh | exp | total | inflection tick |
|----|-------|----|-----|-----|-----|-----|-------|-----------------|
| 501 | 6 | +0.32 | −0.60 | −0.16 | +0.04 | −0.04 | −0.44 | 5 (22400) |
| 502 | 6 | −0.22 | −0.24 | −0.18 | −0.10 | +0.06 | −0.68 | 4 (6120) |
| 503 | 6 | +0.10 | +0.42 | +0.12 | +0.10 | +0.06 | +0.80 | 4 (7640) |
| 504 | 6 | +0.40 | +0.28 | +0.18 | +0.12 | +0.08 | +1.06 | 4 (7840) |
| 505 | 6 | +0.44 | +0.30 | +0.20 | +0.12 | +0.08 | +1.14 | 4 (5640) |

Tick-6 sidecar bind: 501 `abort_s=900`, 502 `abort_s=720`, 503 `abort_s=480`, 504 `survey_s=360`, 505 `dwell_s=240`.

## Raster / energy (Loihi-2 4-core, 23 pJ/spike)

| id | domain | n | rate Hz | window_ms | spikes | energy_pJ | energy_uJ |
|----|--------|---|---------|-----------|--------|-----------|-----------|
| 501 | nitrogen-trifluoride-cell | 76 | 26 | 42 | 83 | 1909 | 0.001909 |
| 502 | toluene-diisocyanate-phosgenator | 88 | 34 | 28 | 84 | 1932 | 0.001932 |
| 503 | synthetic-cryolite-kettle | 120 | 20 | 46 | 110 | 2530 | 0.002530 |
| 504 | ammonium-perchlorate-crystallizer | 48 | 42 | 28 | 56 | 1288 | 0.001288 |
| 505 | trimethylaluminum-still | 80 | 28 | 24 | 54 | 1242 | 0.001242 |

`spikes = round(n × rate × window_s)`. Every record carries `gate_snn` whose `decision` matches the safety gate; populations that declare rate+spikes meet the same ±1 budget against `decision_window_s`. `routing.third_factor` has modulator (NA / ACh / DA / 5-HT / adenosine), `tau_e_s`/`tau_e_ms` pair, and eligibility. Excerpt same-neuron gap ≥ 1000 µs; spike trains same-channel refractory ≥ 0.8 ms. Non-501 excerpts are kernelized and independent of `spike_events` times (overlap < 0.8).

## Local checks (staging, not raw)

See generator stdout: `check_jsonl` FactoryStaging, `validate_run.check_line`, `dumps_exact_json`, `raster_status`, `verify_batch_for_frontier(strict=True)`, `spike_probe.py --strict`, tick sums, refractory, Jaccard.

Never `training_ready`. Never `sim_or_real=real`. Never wrote `outputs/raw/`.

## Residual weaknesses (honest)

1. Only **one** labeled independent LIF (501). The other four excerpts are independent of `spike_events` times but are not declared population sims.
2. Wrong-ACCEPT still absent (guard).
3. Tick-6 sidecar bind is standing machinery (r14+), not a new class.
4. Five domain slugs leave the prompt's 8-item pool; a later round that must stay inside the pool will have to rotate sit-outs instead.
5. 504 and 505 are both already-legal ACCEPTs; a later round could pair one ACCEPT with a world charge that does not go negative.

## Next densification target

Labeled LIF on a second record, or an ISI histogram sidecar. Remaining unused wrong-MODIFY subclasses include **feedforward-as-feedback** and **wrong-hysteresis on a split-range control valve** once lead-lag invert on a fresh tag is staged. Wrong-ACCEPT remains structurally absent until a prompt amendment.

Novel coverage: 16.2%
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
        BATCH_PATH, "batch-r97.jsonl", staging=FactoryStaging(enabled=True)
    )
    report.append(("check_jsonl FactoryStaging", errors, warnings, kinds, nrec))
    line_errs = []
    for i, rec in enumerate(records, 1):
        errs, kind = check_line(rec, f"batch-r97.jsonl:{i}", factory_staging=True)
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
    records = [record_501(), record_502(), record_503(), record_504(), record_505()]
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
