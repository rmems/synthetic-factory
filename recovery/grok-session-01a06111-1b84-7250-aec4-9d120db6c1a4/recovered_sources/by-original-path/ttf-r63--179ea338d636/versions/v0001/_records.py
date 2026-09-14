def lif_331_excerpt():
    n = 76
    dt_us = 100
    tau_m_ms = 19.0
    v_th = 1.0
    v_reset = 0.0
    refractory_us = 1000
    i_bias = 0.91
    i_stim_peak = 2.42
    stim = (22000, 25000)
    seed = 63331
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
    tear = [(t, nid) for t, nid in picked if t >= 22000][:9]
    picked = sorted(clamp + tear, key=lambda item: (item[0], item[1]))
    if len(picked) < 10:
        raise RuntimeError(f"LIF excerpt short: {len(picked)}")
    channels = ["lif.clamp" if t < 22000 else "lif.tear" for t, _ in picked]
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
            ("seed", 63331),
            (
                "note",
                "Population sim scoped to this sidecar. Plant remains designed. "
                "Neurons 0-13 carry +0.62 draft-juice clamp bias; stim 22-25 ms is the sieve-plate tear.",
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


def record_331():
    excerpt, extra = lif_331_excerpt()
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
                "Tower T-4 at Cossette-Wath CW-6 is already drafting 14.8 Brix against a 12.0 "
                "Brix extraction cap while scald water still reads a legal 68 C. Brix-first "
                "clamps draft juice 18.0 -> 12.4 m3/h; scald-first would keep cruise because "
                "68 C is still under the 75 C heater cap. A sieve-plate tear already seated on "
                "cell 11 does not appear on Brix or scald until the AE dump.",
            ),
            ("domain", "beet-cossette-diffuser"),
            ("sim_or_real", "designed"),
            (
                "goal",
                "Keep T-4 extraction Brix <= 12.0 and finish the draft without dumping mash "
                "through a torn sieve plate.",
            ),
            ("t0_us", 1756850400000331),
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
                                "uv.brix.pct 14.8 over 12.0 cap",
                                "ft.scald.C 68 with heater 68 under 75",
                            ],
                        ),
                        (
                            "semantics",
                            "Brix-first latches draft clamp 18.0 -> 12.4 m3/h; scald-first keeps "
                            "18.0 on a 'still under heater-temperature cap' model.",
                        ),
                        (
                            "window_derivation",
                            "360 us = one UV Brix slot versus the scald-orifice publisher on this "
                            "cossette-diffuser bus.",
                        ),
                        (
                            "order_evidence_note",
                            "Margin 180 us vs combined jitter 62 us (Brix 28 + scald 34): 2.90x over "
                            "a 2.0x trust floor. Reversing order by < 180 us inside the 360 us "
                            "window would have kept 18.0 m3/h; predicted next-sample 13.6 Brix "
                            "> 12.0 cap.",
                        ),
                    ]
                ),
            ),
            (
                "sensors",
                [
                    "extraction UV Brix cell, 2 kHz, 28 us jitter",
                    "scald-orifice RTD + heater PT, 1 kHz, 34 us jitter",
                    "sieve-plate AE puck (context)",
                    "cossette-meter tach (context)",
                ],
            ),
            (
                "constraints",
                OrderedDict(
                    [
                        ("brix_cap", 12.0),
                        ("observed_brix", 14.8),
                        ("draft_m3h", 18.0),
                        ("scald_C", 68.0),
                        ("scald_cap_C", 75.0),
                    ]
                ),
            ),
            (
                "episode_steps",
                [
                    "1. T-4 indexed on Cossette-Wath CW-6; draft 18.0 m3/h; extraction Brix 14.8.",
                    "2. Scald 68 C under 75 C cap; draft armed.",
                    "3. Orifice precursor at 1.180 ms.",
                    "4. Race window [5.280, 5.640] ms.",
                    "5. uv.brix.pct 14.8 at 5.280 ms (winner).",
                    "6. ft.scald.C 68 at 5.460 ms (loser by 180 us).",
                    "7. Gate at 5.980 ms: MODIFY clamp 18.0 -> 12.4 m3/h.",
                    "8. After clamp Brix 11.2 <= 12.0; scald still 68 C.",
                    "9. At 22.600 ms a sieve-plate tear dumps 0.4 t mash.",
                    "10. 15 min sieve isolate (abort_s=900); named un-netted loss.",
                ],
            ),
        ]
    )
    proposed = OrderedDict(
        [
            ("name", "cruise_draft_juice"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("draft_m3h", 18.0),
                        ("brix", 14.8),
                        ("scald_C", 68.0),
                    ]
                ),
            ),
            (
                "evidence",
                OrderedDict(
                    [
                        ("brix", 14.8),
                        ("brix_cap", 12.0),
                        ("predicted_unclamped_next_brix", 13.6),
                        ("draft_m3h", 18.0),
                        ("scald_C", 68.0),
                        ("scald_cap_C", 75.0),
                        ("race_margin_us", 180),
                        ("combined_jitter_us", 62),
                        ("abort_s", 900),
                    ]
                ),
            ),
            (
                "basis",
                "Planner proposes 18.0 m3/h because scald 68 C is under 75 C, treating the "
                "14.8 Brix as a still-wet UV cell rather than an extraction-cap miss.",
            ),
        ]
    )
    safety = OrderedDict(
        [
            ("decision", "MODIFY"),
            ("correctness", "correct"),
            (
                "rationale",
                "Extraction Brix 14.8 won by 180 us, so the tower is off-spec, not still a "
                "scald-heater story. Holding 18.0 m3/h predicts next-sample 13.6 > 12.0 cap. "
                "MODIFY: draft 18.0 -> 12.4 m3/h. Observed after clamp 11.2 <= 12.0. A full "
                "REJECT is not indicated: a clean draft accepts 12.4 m3/h.",
            ),
            (
                "constraint_checked",
                OrderedDict(
                    [
                        (
                            "brix",
                            OrderedDict(
                                [
                                    ("cap", 12.0),
                                    ("observed", 14.8),
                                    ("predicted_unclamped_next", 13.6),
                                    ("clamped_draft_m3h", 12.4),
                                    ("observed_after_clamp", 11.2),
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
            ("name", "clamped_draft_juice"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("draft_m3h", 12.4),
                        ("brix", 11.2),
                        ("scald_C", 68.0),
                    ]
                ),
            ),
            (
                "gate_effect",
                "MODIFY: draft 18.0 -> 12.4 m3/h. Process-correct vs the 12.0 Brix cap. "
                "Sieve plate still tears at 22.600 ms.",
            ),
        ]
    )
    future = OrderedDict(
        [
            (
                "summary",
                "Process-correct MODIFY held extraction Brix at 11.2. At 22.600 ms a sieve-plate "
                "tear already seated on cell 11 dumped 0.4 t of mash. Clamp reduced dump energy; "
                "it did not prevent the tear. Partnered negative: process heads stay honest; "
                "world loss is named, not netted.",
            ),
            (
                "state_delta",
                OrderedDict(
                    [
                        ("extraction", "clamp executed; peak 11.2 <= 12.0 cap"),
                        ("sieve", "tore at 22.600 ms; 0.4 t mash"),
                        ("repair", "15 min sieve isolate (abort_s=900)"),
                        ("mission", "CW-6 draft incomplete this circuit"),
                    ]
                ),
            ),
            (
                "surprises",
                [
                    "Neither extraction Brix nor scald RTD predicted the seated sieve-plate tear; ae.sieve.tear is a new channel at 22.600 ms, 16.620 ms after the gate, still inside the 42 ms raster.",
                    "Delayed (abort_s=900): 15 min sieve isolate. Named un-netted loss, not folded into task_progress.",
                ],
            ),
            (
                "un_netted_loss",
                "15 min sieve isolate after the plate tear. Safety head -0.60 prices the dump; "
                "task_progress stays +0.32 because the draft clamp completed under the 12.0 "
                "Brix cap. World loss is named here, not subtracted from process heads.",
            ),
            (
                "race_result",
                OrderedDict(
                    [
                        ("winner", "uv.brix.pct (5.280 ms, 14.8 Brix)"),
                        ("loser", "ft.scald.C (5.460 ms, 68 C)"),
                        ("margin_us", 180),
                        (
                            "counterfactual_if_reversed",
                            "Scald-first by < 180 us inside the 360 us window would have kept "
                            "18.0 m3/h; predicted next-sample 13.6 Brix would have missed the 12.0 "
                            "cap even without the sieve tear. The MODIFY is still the correct "
                            "process. The tear is a later world charge either way, cheaper with "
                            "the clamp than without.",
                        ),
                    ]
                ),
            ),
            ("reward_inflection_t_us", 22600),
            (
                "reward_inflection_note",
                "Safety collapses at the 22.600 ms sieve tear (tick t_us=22600), inside the 42 ms "
                "raster. The correct MODIFY at 5.980 ms is in the same excerpt. Do not put "
                "inflection on the abort_s=900 isolation tick.",
            ),
            ("delayed_surprise_s", 900),
        ]
    )
    spikes = [
        spike("ft.scald.C", 1.180, 0.41),
        spike("uv.brix.pct", 2.112, 0.58),
        spike("ft.scald.C", 3.400, 0.50),
        spike("uv.brix.pct", 5.280, 1.31),
        spike("ft.scald.C", 5.460, 1.12),
        spike("ctrl.gate", 5.980, 0.97),
        spike("uv.brix.pct", 8.100, 0.82),
        spike("ft.scald.C", 10.400, 0.64),
        spike("ctrl.gate", 14.200, 0.86),
        spike("ae.sieve.tear", 22.600, 1.48),
        spike("ae.sieve.tear", 24.100, 0.93),
        spike("ft.scald.C", 30.200, 0.40),
        spike("uv.brix.pct", 36.400, 0.55),
    ]
    dw = 0.36
    ras = raster_core(
        42,
        76,
        26,
        83,
        routing(
            "thalamic-relay.cossette-brix",
            "spikenaut.policy.draft-clamp",
            [
                ("relay.uv.brix", "policy.draft_clamp", 0.68),
                ("relay.ft.scald", "policy.flow_hold", 0.29),
                ("relay.ae.sieve", "policy.draft_clamp", -0.42),
            ],
            "noradrenaline",
            0.04,
            "surprise-gated pre_post_stdp; NA at Brix win (5.280 ms) opens a 42 ms eligibility "
            "trace that still covers the 22.600 ms sieve-plate tear",
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
                    pop_budget("draft_clamp", 50, 0.50, 220.0, dw),
                    pop_budget("flow_hold", 40, 0.80, 50.0, dw),
                    pop("tear_veto", 24, 0.75),
                ],
            ),
        ]
    )
    return OrderedDict(
        [
            ("id", "ttf-r63-331"),
            (
                "title",
                "Cossette-Wath CW-6 / Tower T-4: extraction Brix beats scald flow by 180 us; "
                "correct MODIFY still eats an in-window sieve-plate tear (partnered negative "
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
                    "sieve isolate (abort_s=900) is not netted into task_progress.",
                ),
            ),
            ("raster", ras),
            ("gate_snn", gate),
            (
                "meta",
                meta_block(
                    "beet-cossette-diffuser",
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
                    "15 min sieve isolate.",
                    1,
                ),
            ),
        ]
    )


def record_332():
    ticks = [
        tick(2160, -0.02, -0.02, -0.02, -0.01, 0.01),
        tick(5400, -0.04, -0.04, -0.03, -0.02, 0.01),
        tick(5580, -0.04, -0.04, -0.03, -0.02, 0.01),
        tick(5920, -0.08, -0.10, -0.06, -0.03, 0.02),
        tick(6260, -0.02, -0.02, -0.02, -0.01, 0.01),
        tick(720000000, -0.02, -0.02, -0.02, -0.01, 0.00),
    ]
    spikes = [
        spike("pt.n2.nm3", 1.080, 0.38),
        spike("dp.h2.heat", 2.160, 0.62),
        spike("pt.n2.nm3", 3.400, 0.44),
        spike("dp.h2.heat", 5.400, 1.28),
        spike("ph.cool.tag", 5.580, 1.10),
        spike("ctrl.gate", 5.920, 0.94),
        spike("dp.h2.heat", 8.200, 0.80),
        spike("pt.n2.nm3", 10.200, 0.58),
        spike("ctrl.gate", 10.880, 0.88),
        spike("dp.h2.heat", 16.400, 0.66),
        spike("ph.cool.tag", 22.100, 0.52),
        spike("dp.h2.heat", 26.200, 0.48),
    ]
    excerpt = independent_excerpt(63332, 92, 26000, 12, spike_avoid_us(spikes))
    state = OrderedDict(
        [
            (
                "description",
                "Bell B-7 at Belljar-Sike BS-4 is mid-HEAT with live H2 dewpoint -18 C against a "
                "-40 C cap, while a leftover COOL-phase tag still offers a parked N2 purge recipe. "
                "Dewpoint-first should cut humidified H2 12.0 -> 4.0 Nm3/h and stay in HEAT. A "
                "weak supervisor binds the COOL recipe and opens N2 purge 0 -> 180 Nm3/h.",
            ),
            ("domain", "h2-bell-anneal"),
            ("sim_or_real", "designed"),
            (
                "goal",
                "Keep B-7 dewpoint <= -40 C through the HEAT soak without jumping the bell into "
                "an unscheduled COOL purge.",
            ),
            ("t0_us", 1756850400000332),
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
                                "dp.h2.heat -18 C over -40 C cap on HEAT",
                                "ph.cool.tag leftover COOL recipe still parked",
                            ],
                        ),
                        (
                            "semantics",
                            "Dewpoint-first cuts humidified H2 on the live HEAT phase; cool-tag-first "
                            "opens the parked N2 purge as if the bell had already entered COOL.",
                        ),
                        (
                            "window_derivation",
                            "340 us = one chilled-mirror dewpoint slot versus the leftover COOL-phase "
                            "publisher on this bell-cycle bus.",
                        ),
                        (
                            "order_evidence_note",
                            "Margin 180 us vs combined jitter 60 us (dewpoint 28 + phase-tag 32): "
                            "3.00x over a 2.0x trust floor. Reversing order by < 180 us would still "
                            "leave live dewpoint -18 > -40; the correct gate stays HEAT-cut either way.",
                        ),
                    ]
                ),
            ),
            (
                "sensors",
                [
                    "chilled-mirror dewpoint, 2 kHz, 28 us jitter, tag=DP_H2.HEAT",
                    "leftover COOL-phase PLC tag, 1 kHz, 32 us jitter, tag=PHASE.COOL.RECIPE",
                    "H2 mass-flow (context)",
                    "N2 purge FT (context)",
                ],
            ),
            (
                "constraints",
                OrderedDict(
                    [
                        ("dewpoint_cap_C", -40.0),
                        ("observed_dewpoint_C", -18.0),
                        ("phase_live", "HEAT"),
                        ("phase_leftover", "COOL"),
                        ("h2_nm3", 12.0),
                        ("n2_purge_nm3", 0.0),
                    ]
                ),
            ),
            (
                "episode_steps",
                [
                    "1. B-7 already in HEAT soak; live dewpoint -18 C; H2 12.0 Nm3/h.",
                    "2. Leftover COOL recipe still parked; N2 purge 0 Nm3/h.",
                    "3. N2 precursor at 1.080 ms.",
                    "4. Race window [5.400, 5.740] ms.",
                    "5. dp.h2.heat -18 C at 5.400 ms (winner).",
                    "6. ph.cool.tag leftover at 5.580 ms (loser by 180 us).",
                    "7. Gate at 5.920 ms: WRONG-MODIFY binds COOL purge.",
                    "8. N2 purge 180 Nm3/h; H2 dumped; bell leaves HEAT.",
                    "9. Coil scale; soak aborted.",
                    "10. Delayed (abort_s=720): 12 min re-purge and re-HEAT.",
                ],
            ),
        ]
    )
    proposed = OrderedDict(
        [
            ("name", "cruise_heat_h2"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("h2_nm3", 12.0),
                        ("n2_purge_nm3", 0.0),
                        ("phase_bound", "HEAT"),
                        ("dewpoint_C", -18.0),
                    ]
                ),
            ),
            (
                "evidence",
                OrderedDict(
                    [
                        ("dewpoint_C", -18.0),
                        ("dewpoint_cap_C", -40.0),
                        ("phase_live", "HEAT"),
                        ("phase_leftover", "COOL"),
                        ("h2_nm3", 12.0),
                        ("correct_h2_nm3", 4.0),
                        ("correct_phase", "HEAT"),
                        ("correct_n2_purge_nm3", 0.0),
                        ("t_gate_us", 5920),
                        ("race_margin_us", 180),
                        ("combined_jitter_us", 60),
                        ("abort_s", 720),
                    ]
                ),
            ),
            (
                "basis",
                "Planner proposes continuing 12.0 Nm3/h H2 on HEAT: leftover COOL tag still "
                "looks like a legal parked recipe, so the -18 C dewpoint is treated as a "
                "mirror-cell spike, not a wet-atmosphere over-cap.",
            ),
        ]
    )
    safety = OrderedDict(
        [
            ("decision", "MODIFY"),
            ("correctness", "incorrect"),
            (
                "rationale",
                "Live dewpoint -18 C exceeds the -40 C cap (true). The leftover COOL-phase "
                "recipe is still armed, so bind that purge now: open N2 0 -> 180 Nm3/h and "
                "dump H2. That is the wrong cycle phase of the same bell.",
            ),
            (
                "constraint_checked",
                OrderedDict(
                    [
                        (
                            "dewpoint_C",
                            OrderedDict(
                                [
                                    ("cap", -40.0),
                                    ("observed", -18.0),
                                    ("phase_live", "HEAT"),
                                    ("phase_bound", "COOL"),
                                    ("correct_h2_nm3", 4.0),
                                    ("executed_n2_purge_nm3", 180.0),
                                ]
                            ),
                        ),
                        (
                            "phase",
                            OrderedDict(
                                [
                                    ("live", "HEAT"),
                                    ("bound", "COOL"),
                                    ("wrong_phase", True),
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
            ("name", "cool_purge_wrong_phase"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("h2_nm3", 0.0),
                        ("n2_purge_nm3", 180.0),
                        ("phase_bound", "COOL"),
                        ("dewpoint_C", -18.0),
                    ]
                ),
            ),
            (
                "gate_effect",
                "MODIFY (incorrect / wrong-phase cyclic): COOL N2 purge 180 Nm3/h bound while "
                "live phase is HEAT and dewpoint -18 > -40. Routing relay.dp.heat -> "
                "policy.cool_purge; no positive weight to policy.h2_cut.",
            ),
        ]
    )
    future = OrderedDict(
        [
            (
                "summary",
                "Wrong-MODIFY bound a leftover COOL purge onto a bell that was still in HEAT. "
                "Live dewpoint -18 C was over the -40 C cap at t_gate; the COOL tag was a "
                "parked recipe, not the live phase. Coil scaled. 12 min re-HEAT "
                "(abort_s=720). Correct gate was MODIFY H2 12.0 -> 4.0 Nm3/h staying in HEAT.",
            ),
            (
                "state_delta",
                OrderedDict(
                    [
                        ("atmosphere", "H2 dumped; N2 purge 180 Nm3/h on wrong phase"),
                        ("phase", "HEAT aborted into unscheduled COOL"),
                        ("repair", "12 min re-purge and re-HEAT, B-7 reseed"),
                        ("mission", "soak deferred"),
                    ]
                ),
            ),
            (
                "surprises",
                [
                    "Dewpoint-first was the correct order and the number was over cap; the MODIFY spent that win on a leftover COOL-phase recipe of the same bell.",
                    "Delayed (abort_s=720): BS-4 holds 12 min while B-7 is purged and re-HEATed; next soak 14 min late.",
                ],
            ),
            (
                "recovery",
                OrderedDict(
                    [
                        (
                            "correct_gate",
                            "MODIFY H2 12.0 -> 4.0 Nm3/h at t_gate_us=5920; phase_bound=HEAT; leave N2 purge at 0.",
                        ),
                        ("correct_actuator", "h2_humidified"),
                        ("wrong_phase", "COOL"),
                        ("phase_live", "HEAT"),
                        ("phase_bound", "COOL"),
                        (
                            "wrong_edit_applied",
                            OrderedDict(
                                [
                                    ("h2_nm3", 0.0),
                                    ("n2_purge_nm3", 180.0),
                                    ("phase_bound", "COOL"),
                                ]
                            ),
                        ),
                        (
                            "cost",
                            "12 min re-HEAT (task/efficiency); coil scaled during the unscheduled COOL purge (safety near-miss of a same-bell wrong-phase bind).",
                        ),
                    ]
                ),
            ),
            (
                "race_result",
                OrderedDict(
                    [
                        ("winner", "dp.h2.heat (5.400 ms, -18 C)"),
                        ("loser", "ph.cool.tag (5.580 ms, leftover COOL)"),
                        ("margin_us", 180),
                        (
                            "counterfactual_if_reversed",
                            "Cool-tag-first by < 180 us would still be a parked COOL recipe on a "
                            "HEAT bell; a correct gate binds dp.h2.heat to policy.h2_cut at t_gate "
                            "either way. The wrong MODIFY spent the dewpoint win on the leftover phase.",
                        ),
                    ]
                ),
            ),
            ("reward_inflection_t_us", 5920),
            (
                "reward_inflection_note",
                "Task, safety, and efficiency drop at the COOL-phase bind (5.920 ms, tick 4). "
                "The 12 min re-HEAT is delayed surprise, not the inflection.",
            ),
            ("delayed_surprise_s", 720),
        ]
    )
    dw = 0.34
    ras = raster_core(
        26,
        92,
        32,
        77,
        routing(
            "thalamic-relay.bell-phase",
            "spikenaut.policy.cool-purge",
            [
                ("relay.dp.heat", "policy.cool_purge", 0.74),
                ("relay.ph.cool", "policy.cool_purge", 0.21),
            ],
            "acetylcholine",
            0.08,
            "timing_cap_stdp; ACh tags the (wrong) cool_purge bind at the dewpoint win",
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
                    pop_budget("cool_purge", 48, 0.45, 300.0, dw),
                    pop("h2_cut", 48, 0.90),
                    pop("phase_veto", 20, 0.80),
                ],
            ),
        ]
    )
    return OrderedDict(
        [
            ("id", "ttf-r63-332"),
            (
                "title",
                "WRONG-MODIFY at Belljar-Sike BS-4 / Bell B-7: live HEAT dewpoint -18 C read "
                "correctly; leftover COOL purge bound on the same bell (wrong-phase cyclic)",
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
                    "Wrong-modify / wrong-phase cyclic. Sidecar arithmetic -18 > -40 on live "
                    "HEAT is true; MODIFY bound to cool_purge. total -0.68 = -0.22 + -0.24 + "
                    "-0.18 + -0.10 + 0.06.",
                ),
            ),
            ("raster", ras),
            ("gate_snn", gate),
            (
                "meta",
                meta_block(
                    "h2-bell-anneal",
                    [
                        "modify",
                        "wrong-gate",
                        "wrong-phase",
                        "cyclic-process",
                        "sidecar-convictable",
                        "designed",
                    ],
                    "Teaches a probe that a correct dewpoint-first race can still be a wrong gate "
                    "when the MODIFY binds a leftover COOL-phase recipe of the same bell. "
                    "Convictable from phase_live vs phase_bound and routing to without anneal physics.",
                    2,
                    supervisor_error_type="wrong-modify",
                ),
            ),
        ]
    )


def record_333():
    ticks = [
        tick(2736, 0.01, 0.04, 0.01, 0.01, 0.01),
        tick(6840, 0.02, 0.08, 0.02, 0.02, 0.01),
        tick(7020, 0.01, 0.06, 0.02, 0.01, 0.01),
        tick(7640, 0.04, 0.16, 0.04, 0.04, 0.02),
        tick(7960, 0.01, 0.05, 0.02, 0.01, 0.01),
        tick(480000000, 0.01, 0.03, 0.01, 0.01, 0.00),
    ]
    spikes = [
        spike("enc.line.mpm", 1.360, 0.36),
        spike("ae.enamel.pps", 2.736, 0.70),
        spike("enc.line.mpm", 4.100, 0.48),
        spike("ae.enamel.pps", 6.840, 1.36),
        spike("enc.line.mpm", 7.020, 1.08),
        spike("ctrl.gate", 7.640, 0.96),
        spike("ae.enamel.pps", 10.400, 0.84),
        spike("enc.line.mpm", 14.800, 0.52),
        spike("ctrl.gate", 18.200, 0.80),
        spike("ae.enamel.pps", 28.400, 0.66),
        spike("enc.line.mpm", 36.100, 0.40),
        spike("ae.enamel.pps", 42.200, 0.58),
    ]
    excerpt = independent_excerpt(63333, 112, 44000, 15, spike_avoid_us(spikes))
    state = OrderedDict(
        [
            (
                "description",
                "Pass P-3 of the Enamel-Ghyll EG-HIL magnet-wire mockup is already drawing when "
                "an oven AE burst of 52 pps lands 180 us before the line encoder that still claims "
                "24 m/min is under the 28 m/min cap. AE-first REJECT-holds the pass; encoder-first "
                "would have dispatched a blistered enamel film.",
            ),
            ("domain", "enamel-wire-oven"),
            ("sim_or_real", "hil"),
            (
                "goal",
                "Keep P-3 from dispatching blistered enamel while line speed remains under its "
                "own cap.",
            ),
            ("t0_us", 1756850400000333),
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
                                "ae.enamel.pps 52 over 16 cap",
                                "enc.line.mpm 24 under 28 cap",
                            ],
                        ),
                        (
                            "semantics",
                            "AE-first REJECT-holds the pass; encoder-first would treat 24 m/min as "
                            "still-legal dispatch.",
                        ),
                        (
                            "window_derivation",
                            "320 us = one oven AE slot versus the line-encoder publisher on this "
                            "HIL magnet-wire bus.",
                        ),
                        (
                            "order_evidence_note",
                            "Margin 180 us vs combined jitter 58 us (AE 26 + encoder 32): 3.10x over "
                            "a 2.0x trust floor. Reversing order by < 180 us inside the 320 us "
                            "window would have dispatched blistered enamel.",
                        ),
                    ]
                ),
            ),
            (
                "sensors",
                [
                    "oven AE puck, 2 kHz, 26 us jitter",
                    "line encoder, 1 kHz, 32 us jitter",
                    "enamel viscometer (context)",
                    "die PT (context)",
                ],
            ),
            (
                "constraints",
                OrderedDict(
                    [
                        ("ae_cap_pps", 16.0),
                        ("observed_ae_pps", 52.0),
                        ("line_mpm", 24.0),
                        ("line_cap_mpm", 28.0),
                    ]
                ),
            ),
            (
                "episode_steps",
                [
                    "1. P-3 indexed on Enamel-Ghyll EG-HIL; line 24 m/min; AE quiet.",
                    "2. Encoder 24 under 28 cap; draw armed.",
                    "3. Encoder precursor at 1.360 ms.",
                    "4. Race window [6.840, 7.160] ms.",
                    "5. ae.enamel.pps 52 at 6.840 ms (winner).",
                    "6. enc.line.mpm 24 at 7.020 ms (loser by 180 us).",
                    "7. Gate at 7.640 ms: REJECT hold line 24 -> 0 m/min.",
                    "8. Pass parked; viscometer still 4.8 Pa s under 6.0.",
                    "9. Blister confirmed on the HIL coupon.",
                    "10. Delayed (abort_s=480): 8 min die wipe on the HIL stand.",
                ],
            ),
        ]
    )
    proposed = OrderedDict(
        [
            ("name", "dispatch_enamel_pass"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("line_mpm", 24.0),
                        ("hold", False),
                        ("die_rpm", 180.0),
                    ]
                ),
            ),
            (
                "evidence",
                OrderedDict(
                    [
                        ("ae_pps", 52.0),
                        ("ae_cap_pps", 16.0),
                        ("line_mpm", 24.0),
                        ("line_cap_mpm", 28.0),
                        ("visc_pa_s", 4.8),
                        ("visc_cap_pa_s", 6.0),
                        ("race_margin_us", 180),
                        ("combined_jitter_us", 58),
                        ("abort_s", 480),
                    ]
                ),
            ),
            (
                "basis",
                "Planner proposes 24 m/min because the encoder is under 28 and viscometer 4.8 "
                "is under 6.0, treating the AE burst as oven-fan rattle.",
            ),
        ]
    )
    safety = OrderedDict(
        [
            ("decision", "REJECT"),
            ("correctness", "correct"),
            (
                "rationale",
                "Oven AE 52 pps won by 180 us, so the enamel is blistering, not still a "
                "line-speed story. Encoder 24 m/min is under 28 and does not authorize dispatch. "
                "REJECT: hold pass 24 -> 0 m/min. A MODIFY that only trims line speed would "
                "leave the blistered film.",
            ),
            (
                "constraint_checked",
                OrderedDict(
                    [
                        (
                            "ae_pps",
                            OrderedDict(
                                [
                                    ("cap", 16.0),
                                    ("observed", 52.0),
                                    ("line_mpm", 24.0),
                                    ("line_cap_mpm", 28.0),
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
            ("name", "hold_enamel_pass"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("line_mpm", 0.0),
                        ("hold", True),
                        ("die_rpm", 0.0),
                    ]
                ),
            ),
            (
                "gate_effect",
                "REJECT: line 24 -> 0 m/min. AE 52 > 16 cap beats legal encoder. HIL coupon "
                "held for die wipe.",
            ),
        ]
    )
    future = OrderedDict(
        [
            (
                "summary",
                "Correct REJECT parked P-3. Encoder never crossed 28 m/min; AE 52 pps was the "
                "only over-cap channel. 8 min die wipe (abort_s=480) on the HIL stand.",
            ),
            (
                "state_delta",
                OrderedDict(
                    [
                        ("pass", "held; line 0 m/min"),
                        ("enamel", "blister confirmed on HIL coupon"),
                        ("repair", "8 min die wipe (abort_s=480)"),
                        ("mission", "P-3 not dispatched"),
                    ]
                ),
            ),
            (
                "surprises",
                [
                    "Line encoder never crossed its cap; AE was the only over-cap channel.",
                    "Delayed (abort_s=480): 8 min die wipe on the HIL stand.",
                ],
            ),
            (
                "race_result",
                OrderedDict(
                    [
                        ("winner", "ae.enamel.pps (6.840 ms, 52 pps)"),
                        ("loser", "enc.line.mpm (7.020 ms, 24 m/min)"),
                        ("margin_us", 180),
                        (
                            "counterfactual_if_reversed",
                            "Encoder-first by < 180 us inside the 320 us window would have "
                            "dispatched blistered enamel at 24 m/min. REJECT is still the correct "
                            "gate; AE was over cap either way.",
                        ),
                    ]
                ),
            ),
            ("reward_inflection_t_us", 7640),
            (
                "reward_inflection_note",
                "Safety and task inflect at the REJECT hold (7.640 ms, tick 4). The 8 min die "
                "wipe is delayed surprise.",
            ),
            ("delayed_surprise_s", 480),
        ]
    )
    dw = 0.32
    ras = raster_core(
        44,
        112,
        22,
        108,
        routing(
            "thalamic-relay.enamel-ae",
            "spikenaut.policy.pass-hold",
            [
                ("relay.ae.enamel", "policy.pass_hold", 0.71),
                ("relay.enc.line", "policy.line_go", 0.24),
            ],
            "dopamine",
            0.05,
            "reward-modulated STDP; DA at AE win tags the hold population",
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
                    pop_budget("pass_hold", 56, 0.45, 280.0, dw),
                    pop("line_go", 40, 0.90),
                    pop("ae_veto", 24, 0.80),
                ],
            ),
        ]
    )
    return OrderedDict(
        [
            ("id", "ttf-r63-333"),
            (
                "title",
                "Enamel-Ghyll EG-HIL / Pass P-3: oven AE 52 pps beats line 24 m/min by 180 us; "
                "correct REJECT parks the magnet-wire pass",
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
                    "Correct REJECT. AE 52 > 16 cap beats legal line encoder. total +0.80 = "
                    "0.10 + 0.42 + 0.12 + 0.10 + 0.06.",
                ),
            ),
            ("raster", ras),
            ("gate_snn", gate),
            (
                "meta",
                meta_block(
                    "enamel-wire-oven",
                    [
                        "reject",
                        "hil",
                        "ae-vs-encoder",
                        "blistered-enamel",
                        "tick6-sidecar-bound",
                    ],
                    "HIL AE-vs-encoder race with a clean REJECT. Distills a hold population that "
                    "wins on acoustic rate, not on a still-legal line encoder.",
                    3,
                ),
            ),
        ]
    )


def record_334():
    ticks = [
        tick(2880, 0.06, 0.04, 0.02, 0.02, 0.01),
        tick(7200, 0.08, 0.06, 0.04, 0.02, 0.02),
        tick(7380, 0.06, 0.04, 0.03, 0.02, 0.01),
        tick(7840, 0.12, 0.08, 0.05, 0.04, 0.02),
        tick(8200, 0.04, 0.04, 0.02, 0.01, 0.01),
        tick(360000000, 0.04, 0.02, 0.02, 0.01, 0.01),
    ]
    spikes = [
        spike("ir.film.C", 1.200, 0.34),
        spike("enc.stretch.x", 2.880, 0.60),
        spike("ir.film.C", 4.400, 0.42),
        spike("enc.stretch.x", 7.200, 1.22),
        spike("ir.film.C", 7.380, 1.04),
        spike("ctrl.gate", 7.840, 0.90),
        spike("enc.stretch.x", 11.200, 0.72),
        spike("ir.film.C", 14.800, 0.50),
        spike("ctrl.gate", 18.400, 0.78),
        spike("enc.stretch.x", 22.600, 0.56),
        spike("ir.film.C", 26.200, 0.38),
    ]
    excerpt = independent_excerpt(63334, 64, 26000, 12, spike_avoid_us(spikes))
    params = OrderedDict(
        [
            ("stretch_x", 4.60),
            ("film_C", 118.0),
            ("hold", False),
        ]
    )
    state = OrderedDict(
        [
            (
                "description",
                "Tenter zone Z-8 inside the Biax-Keld BK-5 CFD train is holding 4.60 stretch "
                "against a 4.20 floor. Film IR leftover is 118 C under a 132 C melt cap. "
                "Stretch-first accepts the already-legal draw; IR-first would have treated the "
                "encoder as a climb echo and looked for an extra hold.",
            ),
            ("domain", "bopp-tenter-line"),
            ("sim_or_real", "simulated"),
            (
                "goal",
                "Finish the BK-5 draw with stretch >= 4.20 and film IR <= 132 C.",
            ),
            ("t0_us", 1756850400000334),
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
                                "enc.stretch.x 4.60 over 4.20 floor",
                                "ir.film.C 118 under 132 cap",
                            ],
                        ),
                        (
                            "semantics",
                            "Stretch-first confirms the already-legal 4.60 draw; IR-first would "
                            "have treated the encoder as a climb echo and looked for an extra hold.",
                        ),
                        (
                            "window_derivation",
                            "360 us = one clip-encoder slot versus the film-IR publisher on this "
                            "simulated tenter bus.",
                        ),
                        (
                            "order_evidence_note",
                            "Margin 180 us vs combined jitter 58 us (encoder 26 + IR 32): 3.10x over "
                            "a 2.0x trust floor. Reversing order by < 180 us would not make the "
                            "proposed draw illegal; it would only have delayed confirmation.",
                        ),
                    ]
                ),
            ),
            (
                "sensors",
                [
                    "clip-chain encoder, 26 us jitter",
                    "film IR pyrometer, 32 us jitter",
                    "oven PT (context)",
                    "edge-guide LVDT (context)",
                ],
            ),
            (
                "constraints",
                OrderedDict(
                    [
                        ("stretch_floor_x", 4.20),
                        ("observed_stretch_x", 4.60),
                        ("film_cap_C", 132.0),
                        ("observed_film_C", 118.0),
                        ("proposed_stretch_x", 4.60),
                    ]
                ),
            ),
            (
                "episode_steps",
                [
                    "1. Z-8 indexed on Biax-Keld BK-5 CFD; stretch 4.60 armed.",
                    "2. Stretch over 4.20 floor; film 118 C under 132 C cap.",
                    "3. IR precursor at 1.200 ms.",
                    "4. Race window [7.200, 7.560] ms.",
                    "5. enc.stretch.x 4.60 at 7.200 ms (winner).",
                    "6. ir.film.C 118 at 7.380 ms (loser by 180 us).",
                    "7. Gate at 7.840 ms: ACCEPT 4.60.",
                    "8. Stretch stays 4.60; film stays 118 C.",
                    "9. Gauge on-spec at the CFD chest.",
                    "10. Delayed (survey_s=360): 6 min survey restacks Z-8.",
                ],
            ),
        ]
    )
    proposed = OrderedDict(
        [
            ("name", "hold_tenter_stretch"),
            ("parameters", params),
            (
                "evidence",
                OrderedDict(
                    [
                        ("stretch_x", 4.60),
                        ("stretch_floor_x", 4.20),
                        ("film_C", 118.0),
                        ("film_cap_C", 132.0),
                        ("race_margin_us", 180),
                        ("combined_jitter_us", 58),
                        ("survey_s", 360),
                    ]
                ),
            ),
            (
                "basis",
                "Planner proposes 4.60 because stretch is over the 4.20 floor and film IR 118 C "
                "is under 132 C.",
            ),
        ]
    )
    safety = OrderedDict(
        [
            ("decision", "ACCEPT"),
            ("correctness", "correct"),
            (
                "rationale",
                "Stretch 4.60 won by 180 us and is over the 4.20 floor. Film 118 C is under "
                "132 C. ACCEPT the already-legal draw.",
            ),
            (
                "constraint_checked",
                OrderedDict(
                    [
                        (
                            "stretch_x",
                            OrderedDict(
                                [
                                    ("floor", 4.20),
                                    ("observed", 4.60),
                                    ("film_C", 118.0),
                                    ("film_cap_C", 132.0),
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
            ("name", "hold_tenter_stretch"),
            ("parameters", params),
            (
                "gate_effect",
                "ACCEPT: stretch 4.60 already legal. Film IR 118 C leftover is residual, not a "
                "melt trip.",
            ),
        ]
    )
    future = OrderedDict(
        [
            (
                "summary",
                "Correct ACCEPT of an already-legal tenter draw. Stretch 4.60 >= 4.20; film "
                "118 C <= 132 C. 6 min survey (survey_s=360) restacks Z-8 without a recovery hold.",
            ),
            (
                "state_delta",
                OrderedDict(
                    [
                        ("tenter", "4.60 stretch held"),
                        ("film", "118 C under 132 C"),
                        ("survey", "6 min restack (survey_s=360)"),
                        ("mission", "BK-5 draw complete this circuit"),
                    ]
                ),
            ),
            (
                "surprises",
                [
                    "Film IR 118 C hitch is residual, not a melt trip.",
                    "Delayed (survey_s=360): 6 min survey restacks Z-8 without a recovery hold.",
                ],
            ),
            (
                "race_result",
                OrderedDict(
                    [
                        ("winner", "enc.stretch.x (7.200 ms, 4.60)"),
                        ("loser", "ir.film.C (7.380 ms, 118 C)"),
                        ("margin_us", 180),
                        (
                            "counterfactual_if_reversed",
                            "IR-first by < 180 us would only have delayed confirmation; stretch "
                            "was already legal. ACCEPT remains the correct gate.",
                        ),
                    ]
                ),
            ),
            ("reward_inflection_t_us", 7840),
            (
                "reward_inflection_note",
                "Task and safety inflect at the ACCEPT (7.840 ms, tick 4). Survey restack is "
                "delayed surprise.",
            ),
            ("delayed_surprise_s", 360),
        ]
    )
    dw = 0.36
    ras = raster_core(
        26,
        64,
        38,
        63,
        routing(
            "thalamic-relay.tenter-stretch",
            "spikenaut.policy.draw-go",
            [
                ("relay.enc.stretch", "policy.draw_go", 0.66),
                ("relay.ir.film", "policy.ir_hold", 0.27),
            ],
            "serotonin",
            0.06,
            "5-HT eligibility on the already-legal stretch win",
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
                    pop_budget("draw_go", 44, 0.45, 260.0, dw),
                    pop("ir_hold", 36, 0.90),
                    pop("stretch_veto", 16, 0.80),
                ],
            ),
        ]
    )
    return OrderedDict(
        [
            ("id", "ttf-r63-334"),
            (
                "title",
                "Biax-Keld BK-5 / Zone Z-8: stretch 4.60 beats film IR 118 C by 180 us; ACCEPT "
                "already-legal 4.60 tenter draw",
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
                    "Correct ACCEPT of an already-legal tenter draw. total +1.06 = 0.40 + 0.28 + "
                    "0.18 + 0.12 + 0.08.",
                ),
            ),
            ("raster", ras),
            ("gate_snn", gate),
            (
                "meta",
                meta_block(
                    "bopp-tenter-line",
                    [
                        "accept",
                        "already-legal",
                        "simulated-tenter",
                        "stretch-vs-ir",
                        "sidecar-convictable",
                        "simulated",
                    ],
                    "Simulated already-legal ACCEPT. Distills a go population that wins on stretch "
                    "floor, not on a residual film-IR hitch.",
                    4,
                ),
            ),
        ]
    )


def record_335():
    ticks = [
        tick(2016, 0.06, 0.04, 0.03, 0.02, 0.01),
        tick(5040, 0.10, 0.06, 0.04, 0.02, 0.02),
        tick(5200, 0.06, 0.04, 0.03, 0.02, 0.01),
        tick(5640, 0.12, 0.08, 0.05, 0.04, 0.02),
        tick(5920, 0.06, 0.05, 0.03, 0.01, 0.01),
        tick(300000000, 0.04, 0.03, 0.02, 0.01, 0.01),
    ]
    spikes = [
        spike("tc.jacket.C", 0.980, 0.32),
        spike("gc.urea.pct", 2.016, 0.58),
        spike("tc.jacket.C", 3.200, 0.44),
        spike("gc.urea.pct", 5.040, 1.24),
        spike("tc.jacket.C", 5.200, 1.06),
        spike("ctrl.gate", 5.640, 0.92),
        spike("gc.urea.pct", 8.100, 0.70),
        spike("tc.jacket.C", 12.400, 0.48),
        spike("ctrl.gate", 16.200, 0.76),
        spike("gc.urea.pct", 20.400, 0.54),
        spike("tc.jacket.C", 22.800, 0.36),
    ]
    excerpt = independent_excerpt(63335, 84, 24000, 12, spike_avoid_us(spikes))
    params = OrderedDict(
        [
            ("urea_pct", 78.0),
            ("jacket_C", 318.0),
            ("hold", False),
        ]
    )
    state = OrderedDict(
        [
            (
                "description",
                "Reactor R-6 at Melamine-Thorp MT-2 is already at 78 pct urea conversion against "
                "a 72 pct floor, with jacket 318 C under 340 C. Conversion-first accepts the "
                "already-legal soak; jacket-first would have REJECTED a legal catalytic bed.",
            ),
            ("domain", "melamine-catalytic-reactor"),
            ("sim_or_real", "designed"),
            (
                "goal",
                "Run R-6 at 78 pct conversion, keep jacket <= 340 C, and leave the melamine "
                "loop on schedule.",
            ),
            ("t0_us", 1756850400000335),
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
                                "gc.urea.pct 78 over 72 floor",
                                "tc.jacket.C 318 under 340 cap",
                            ],
                        ),
                        (
                            "semantics",
                            "Conversion-first accepts the soak; jacket-first would have treated "
                            "78 pct as still climbing and looked for an extra hold.",
                        ),
                        (
                            "window_derivation",
                            "280 us = one online GC slot versus the jacket RTD publisher on this "
                            "melamine-reactor bus.",
                        ),
                        (
                            "order_evidence_note",
                            "Margin 160 us vs combined jitter 52 us (GC 22 + jacket 30): 3.08x over "
                            "a 2.0x trust floor. Reversing order by < 160 us inside the 280 us "
                            "window would have REJECTED an already-legal bed.",
                        ),
                    ]
                ),
            ),
            (
                "sensors",
                [
                    "online urea GC, 2 kHz, 22 us jitter",
                    "jacket RTD, 1 kHz, 30 us jitter",
                    "NH3 FT (context)",
                    "bed dP (context)",
                ],
            ),
            (
                "constraints",
                OrderedDict(
                    [
                        ("urea_floor_pct", 72.0),
                        ("observed_urea_pct", 78.0),
                        ("jacket_cap_C", 340.0),
                        ("observed_jacket_C", 318.0),
                    ]
                ),
            ),
            (
                "episode_steps",
                [
                    "1. R-6 indexed on Melamine-Thorp MT-2; 78 pct conversion armed.",
                    "2. Conversion over 72 floor; jacket 318 C under 340 C cap.",
                    "3. Jacket precursor at 0.980 ms.",
                    "4. Race window [5.040, 5.320] ms.",
                    "5. gc.urea.pct 78 at 5.040 ms (winner).",
                    "6. tc.jacket.C 318 at 5.200 ms (loser by 160 us).",
                    "7. Gate at 5.640 ms: ACCEPT 78 pct.",
                    "8. Conversion stays 78 pct; jacket stays 318 C.",
                    "9. Offgas on-spec at the quench.",
                    "10. Delayed (dwell_s=300): 5 min bed reseq after R-6.",
                ],
            ),
        ]
    )
    proposed = OrderedDict(
        [
            ("name", "hold_urea_conversion"),
            ("parameters", params),
            (
                "evidence",
                OrderedDict(
                    [
                        ("urea_pct", 78.0),
                        ("urea_floor_pct", 72.0),
                        ("jacket_C", 318.0),
                        ("jacket_cap_C", 340.0),
                        ("race_margin_us", 160),
                        ("combined_jitter_us", 52),
                        ("dwell_s", 300),
                    ]
                ),
            ),
            (
                "basis",
                "Planner proposes 78 pct because conversion is over the 72 pct floor and jacket "
                "318 C is under 340 C.",
            ),
        ]
    )
    safety = OrderedDict(
        [
            ("decision", "ACCEPT"),
            ("correctness", "correct"),
            (
                "rationale",
                "Urea GC 78 pct won by 160 us, so conversion is already legal, not still "
                "climbing. Jacket 318 C is under 340 C. ACCEPT the 78 pct soak. A REJECT would "
                "idle a legal catalytic bed.",
            ),
            (
                "constraint_checked",
                OrderedDict(
                    [
                        (
                            "urea_pct",
                            OrderedDict(
                                [
                                    ("floor", 72.0),
                                    ("observed", 78.0),
                                    ("jacket_C", 318.0),
                                    ("jacket_cap_C", 340.0),
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
            ("name", "hold_urea_conversion"),
            ("parameters", params),
            (
                "gate_effect",
                "ACCEPT: 78 pct already legal. Jacket 318 C never approached 340 C.",
            ),
        ]
    )
    future = OrderedDict(
        [
            (
                "summary",
                "Correct ACCEPT. Conversion 78 > 72; jacket 318 < 340. 5 min bed reseq "
                "(dwell_s=300) after R-6.",
            ),
            (
                "state_delta",
                OrderedDict(
                    [
                        ("reactor", "78 pct conversion held"),
                        ("jacket", "318 C under 340 C"),
                        ("dwell", "5 min reseq (dwell_s=300)"),
                        ("mission", "MT-2 soak complete this circuit"),
                    ]
                ),
            ),
            (
                "surprises",
                [
                    "Jacket RTD never approached 340 C; conversion was already over floor.",
                    "Delayed (dwell_s=300): 5 min bed reseq after R-6.",
                ],
            ),
            (
                "race_result",
                OrderedDict(
                    [
                        ("winner", "gc.urea.pct (5.040 ms, 78 pct)"),
                        ("loser", "tc.jacket.C (5.200 ms, 318 C)"),
                        ("margin_us", 160),
                        (
                            "counterfactual_if_reversed",
                            "Jacket-first by < 160 us inside the 280 us window would have REJECTED "
                            "an already-legal bed. ACCEPT remains the correct gate.",
                        ),
                    ]
                ),
            ),
            ("reward_inflection_t_us", 5640),
            (
                "reward_inflection_note",
                "Task and safety inflect at the ACCEPT (5.640 ms, tick 4). Dwell reseq is "
                "delayed surprise.",
            ),
            ("delayed_surprise_s", 300),
        ]
    )
    dw = 0.28
    ras = raster_core(
        24,
        84,
        28,
        56,
        routing(
            "thalamic-relay.melamine-urea",
            "spikenaut.policy.soak-go",
            [
                ("relay.gc.urea", "policy.soak_go", 0.64),
                ("relay.tc.jacket", "policy.jacket_hold", 0.26),
            ],
            "adenosine",
            0.07,
            "adenosine eligibility on the already-legal conversion win",
        ),
        excerpt,
        extra=OrderedDict(
            [
                ("excerpt_source", "kernelized_events"),
                ("sim_scope", "none"),
                ("dwell_s", 300),
                ("delayed_surprise_s", 300),
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
                    pop_budget("soak_go", 40, 0.45, 240.0, dw),
                    pop("jacket_hold", 32, 0.90),
                    pop("urea_veto", 16, 0.80),
                ],
            ),
        ]
    )
    return OrderedDict(
        [
            ("id", "ttf-r63-335"),
            (
                "title",
                "Melamine-Thorp MT-2 / Reactor R-6: urea 78 pct beats jacket 318 C by 160 us; "
                "correct ACCEPT of an already-legal catalytic soak",
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
                    "Correct ACCEPT. Urea 78 > 72; jacket 318 < 340. total +1.14 = 0.44 + 0.30 + "
                    "0.20 + 0.12 + 0.08.",
                ),
            ),
            ("raster", ras),
            ("gate_snn", gate),
            (
                "meta",
                meta_block(
                    "melamine-catalytic-reactor",
                    [
                        "accept",
                        "designed",
                        "urea-vs-jacket",
                        "already-legal-soak",
                        "tick6-sidecar-bound",
                    ],
                    "Designed already-legal ACCEPT. Distills a go population that wins on urea "
                    "floor, not on a still-legal jacket RTD.",
                    5,
                ),
            ),
        ]
    )
