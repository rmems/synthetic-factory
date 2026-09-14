def lif_271_excerpt():
    n = 80
    dt_us = 100
    tau_m_ms = 19.0
    v_th = 1.0
    v_reset = 0.0
    refractory_us = 1000
    i_bias = 0.91
    i_stim_peak = 2.42
    stim = (21800, 24800)
    seed = 51271
    window_us = 42000
    i_clamp_extra = 0.62
    clamp_n = 16
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
    early = [(t, nid) for t, nid in spikes if t < 21800]
    burst = [(t, nid) for t, nid in spikes if 21800 <= t < 24800]
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
            group = [1 for tt, _ in picked if (tt < 21800) == (pool[0][0] < 21800)]
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
    take(burst, 9, label_times=(22200, 22900, 23600))
    clamp = [(t, nid) for t, nid in picked if t < 21800][:7]
    tear = [(t, nid) for t, nid in picked if t >= 21800][:9]
    picked = sorted(clamp + tear, key=lambda item: (item[0], item[1]))
    if len(picked) < 10:
        raise RuntimeError(f"LIF excerpt short: {len(picked)}")
    channels = ["lif.clamp" if t < 21800 else "lif.spall" for t, _ in picked]
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
            ("i_stim_peak", 2.42),
            ("stim_t_us", [21800, 24800]),
            ("i_clamp_extra", 0.62),
            ("clamp_n", 16),
            ("seed", 51271),
            (
                "note",
                "Population sim scoped to this sidecar. Plant remains designed. "
                "Neurons 0-15 carry +0.62 flue-draft clamp bias; stim 21.8-24.8 ms is the flue-wall spall.",
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


def record_271():
    excerpt, extra = lif_271_excerpt()
    ticks = [
        tick(2100, 0.04, -0.02, -0.02, 0.01, 0.00),
        tick(5240, 0.08, -0.04, -0.02, 0.01, -0.01),
        tick(5412, 0.04, -0.03, -0.02, 0.00, 0.00),
        tick(5800, 0.08, -0.05, -0.03, 0.02, -0.01),
        tick(22200, 0.04, -0.45, -0.03, -0.01, -0.01),
        tick(900000000, 0.02, -0.05, -0.02, 0.01, -0.01),
    ]
    state = OrderedDict(
        [
            (
                "description",
                "Rammer-Clough RC-4 ring furnace is mid-bake on pit F-12: zirconia O2 3.80 "
                "percent versus a 2.00 percent packing-coke oxidation license, flue draft still "
                "8.4 mmWC. O2-first lifts draft to 11.2 mmWC; a pit-temperature hold at 1180 C "
                "under 1220 would have left packing coke burning. Section-7 flue brick already "
                "wants to spall and does not show on O2 or draft until the AE dump.",
            ),
            ("domain", "anode-bake-furnace"),
            ("sim_or_real", "designed"),
            (
                "goal",
                "Keep F-12 pit O2 <= 2.00 percent and finish the bake pass without dumping "
                "packing coke into the flue.",
            ),
            ("t0_us", 1756850400000271),
            ("gate_latency_us", 700),
            ("race_window_us", 380),
            ("race_window_rel_ms", [5.24, 5.62]),
            (
                "race",
                OrderedDict(
                    [
                        (
                            "contenders",
                            [
                                "o2.pit.pct 3.80 over 2.00 cap",
                                "enc.draft.mm 8.4 with pit 1180 under 1220",
                            ],
                        ),
                        (
                            "semantics",
                            "O2-first latches flue-draft clamp 8.4 -> 11.2 mmWC; pit-temp-first "
                            "keeps 8.4 on a 'still under bake cap' model.",
                        ),
                        (
                            "window_derivation",
                            "380 us = one zirconia O2 slot versus the draft-DP publisher on this "
                            "ring-furnace bus.",
                        ),
                        (
                            "order_evidence_note",
                            "Margin 172 us vs combined jitter 64 us (O2 30 + draft 34): 2.69x over "
                            "a 2.0x trust floor. Reversing order by < 172 us inside the 380 us "
                            "window would have kept 8.4 mmWC; predicted next-sample 3.40 percent "
                            "> 2.00 cap.",
                        ),
                    ]
                ),
            ),
            (
                "sensors",
                [
                    "pit zirconia O2 cell, 2 kHz, 30 us jitter",
                    "flue draft DP + pit TC, 1 kHz, 34 us jitter",
                    "flue AE puck (context)",
                    "packing-coke level (context)",
                ],
            ),
            (
                "constraints",
                OrderedDict(
                    [
                        ("o2_cap_pct", 2.00),
                        ("observed_o2_pct", 3.80),
                        ("draft_mmWC", 8.4),
                        ("pit_C", 1180.0),
                        ("pit_cap_C", 1220.0),
                    ]
                ),
            ),
            (
                "episode_steps",
                [
                    "1. F-12 indexed; draft 8.4 mmWC; pit O2 3.80 percent.",
                    "2. Pit 1180 C under 1220 C cap; bake armed.",
                    "3. Draft precursor at 1.240 ms.",
                    "4. Race window [5.240, 5.620] ms.",
                    "5. o2.pit.pct 3.80 at 5.240 ms (winner).",
                    "6. enc.draft.mm 8.4 at 5.412 ms (loser by 172 us).",
                    "7. Gate at 5.800 ms: MODIFY clamp 8.4 -> 11.2 mmWC.",
                    "8. After clamp O2 1.70 percent <= 2.00; pit still 1180 C.",
                    "9. At 22.200 ms a flue-wall spall dumps 0.6 t packing coke.",
                    "10. 15 min pit isolation (abort_s=900); named un-netted loss.",
                ],
            ),
        ]
    )
    proposed = OrderedDict(
        [
            ("name", "cruise_flue_draft"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("draft_mmWC", 8.4),
                        ("o2_pct", 3.80),
                        ("pit_C", 1180.0),
                    ]
                ),
            ),
            (
                "evidence",
                OrderedDict(
                    [
                        ("o2_pct", 3.80),
                        ("o2_cap_pct", 2.00),
                        ("predicted_unclamped_next_pct", 3.40),
                        ("draft_mmWC", 8.4),
                        ("pit_C", 1180.0),
                        ("pit_cap_C", 1220.0),
                        ("race_margin_us", 172),
                        ("combined_jitter_us", 64),
                        ("abort_s", 900),
                    ]
                ),
            ),
            (
                "basis",
                "Planner proposes 8.4 mmWC draft because pit 1180 C is under 1220, treating "
                "the 3.80 percent O2 as a still-wet zirconia cell rather than an oxidation-cap miss.",
            ),
        ]
    )
    safety = OrderedDict(
        [
            ("decision", "MODIFY"),
            ("correctness", "correct"),
            (
                "rationale",
                "Pit O2 3.80 percent won by 172 us, so the bake is oxidizing, not still a "
                "pit-temperature story. Holding 8.4 mmWC predicts next-sample 3.40 percent > "
                "2.00 cap. MODIFY: draft 8.4 -> 11.2 mmWC. Observed after clamp 1.70 percent "
                "<= 2.00. A full REJECT is not indicated: a clean bake accepts 11.2 mmWC.",
            ),
            (
                "constraint_checked",
                OrderedDict(
                    [
                        (
                            "o2_pct",
                            OrderedDict(
                                [
                                    ("cap", 2.00),
                                    ("observed", 3.80),
                                    ("predicted_unclamped_next", 3.40),
                                    ("clamped_draft_mmWC", 11.2),
                                    ("observed_after_clamp", 1.70),
                                ]
                            ),
                        ),
                        (
                            "order_evidence",
                            OrderedDict(
                                [
                                    ("margin_us", 172),
                                    ("combined_jitter_us", 64),
                                    ("ratio", 2.69),
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
            ("name", "clamped_flue_draft"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("draft_mmWC", 11.2),
                        ("o2_pct", 1.70),
                        ("pit_C", 1180.0),
                    ]
                ),
            ),
            (
                "gate_effect",
                "MODIFY: draft 8.4 -> 11.2 mmWC. Process-correct vs the 2.00 percent O2 cap. "
                "Flue wall still spalls at 22.200 ms.",
            ),
        ]
    )
    future = OrderedDict(
        [
            (
                "summary",
                "Process-correct MODIFY held pit O2 at 1.70 percent. At 22.200 ms a flue-wall "
                "spall already seated on section 7 dumped 0.6 t of packing coke. Clamp reduced "
                "dump energy; it did not prevent the spall. Partnered negative: process heads "
                "stay honest; world loss is named, not netted.",
            ),
            (
                "state_delta",
                OrderedDict(
                    [
                        ("pit_o2", "clamp executed; peak 1.70 percent <= 2.00 cap"),
                        ("flue_wall", "spalled at 22.200 ms; 0.6 t packing coke"),
                        ("repair", "15 min pit isolation (abort_s=900)"),
                        ("mission", "RC-4 bake incomplete this circuit"),
                    ]
                ),
            ),
            (
                "surprises",
                [
                    "Neither pit O2 nor draft DP predicted the seated flue-wall spall; ae.flue.spall is a new channel at 22.200 ms, 16.400 ms after the gate, still inside the 42 ms raster.",
                    "Delayed (abort_s=900): 15 min pit isolation. Named un-netted loss, not folded into task_progress.",
                ],
            ),
            (
                "un_netted_loss",
                "15 min pit isolation after the flue-wall spall. Safety head -0.64 prices the dump; "
                "task_progress stays +0.30 because the draft clamp completed under the 2.00 "
                "percent cap. World loss is named here, not subtracted from process heads.",
            ),
            (
                "race_result",
                OrderedDict(
                    [
                        ("winner", "o2.pit.pct (5.240 ms, 3.80 percent)"),
                        ("loser", "enc.draft.mm (5.412 ms, 8.4 mmWC)"),
                        ("margin_us", 172),
                        (
                            "counterfactual_if_reversed",
                            "Pit-temp-first by < 172 us inside the 380 us window would have kept "
                            "8.4 mmWC; predicted next-sample 3.40 percent would have missed the "
                            "2.00 cap even without the spall. The MODIFY is still the correct "
                            "process. The spall is a later world charge either way, cheaper with "
                            "the clamp than without.",
                        ),
                    ]
                ),
            ),
            ("reward_inflection_t_us", 22200),
            (
                "reward_inflection_note",
                "Safety collapses at the 22.200 ms flue-wall spall (tick t_us=22200), inside the "
                "42 ms raster. The correct MODIFY at 5.800 ms is in the same excerpt. Do not put "
                "inflection on the abort_s=900 isolation tick.",
            ),
            ("delayed_surprise_s", 900),
        ]
    )
    spikes = [
        spike("enc.draft.mm", 1.240, 0.41),
        spike("o2.pit.pct", 2.100, 0.58),
        spike("enc.draft.mm", 3.480, 0.50),
        spike("o2.pit.pct", 5.240, 1.31),
        spike("enc.draft.mm", 5.412, 1.12),
        spike("ctrl.gate", 5.800, 0.97),
        spike("o2.pit.pct", 8.200, 0.82),
        spike("enc.draft.mm", 10.600, 0.64),
        spike("ctrl.gate", 14.400, 0.86),
        spike("ae.flue.spall", 22.200, 1.48),
        spike("ae.flue.spall", 23.900, 0.93),
        spike("enc.draft.mm", 30.400, 0.40),
        spike("o2.pit.pct", 36.600, 0.55),
    ]
    dw = 0.38
    ras = raster_core(
        42,
        80,
        28,
        94,
        routing(
            "thalamic-relay.bake-o2",
            "spikenaut.policy.draft-clamp",
            [
                ("relay.o2.pit", "policy.draft_clamp", 0.68),
                ("relay.enc.draft", "policy.draft_hold", 0.29),
                ("relay.ae.flue", "policy.draft_clamp", -0.42),
            ],
            "noradrenaline",
            0.04,
            "surprise-gated pre_post_stdp; NA at O2 win (5.240 ms) opens a 42 ms eligibility "
            "trace that still covers the 22.200 ms flue-wall spall",
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
                    pop_budget("draft_hold", 40, 0.80, 50.0, dw),
                    pop("spall_veto", 24, 0.75),
                ],
            ),
        ]
    )
    return OrderedDict(
        [
            ("id", "ttf-r51-271"),
            (
                "title",
                "Rammer-Clough RC-4 / Pit F-12: pit O2 beats flue draft by 172 us; correct "
                "MODIFY still eats an in-window flue-wall spall (partnered negative total -0.48)",
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
                    "pit isolation (abort_s=900) is not netted into task_progress.",
                ),
            ),
            ("raster", ras),
            ("gate_snn", gate),
            (
                "meta",
                meta_block(
                    "anode-bake-furnace",
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
                    "15 min pit isolation.",
                    1,
                ),
            ),
        ]
    )


def record_272():
    ticks = [
        tick(2280, -0.02, -0.02, -0.02, -0.01, 0.01),
        tick(5620, -0.04, -0.04, -0.03, -0.02, 0.01),
        tick(5796, -0.04, -0.04, -0.03, -0.02, 0.01),
        tick(6180, -0.08, -0.10, -0.06, -0.03, 0.02),
        tick(6540, -0.02, -0.02, -0.02, -0.01, 0.01),
        tick(720000000, -0.02, -0.02, -0.02, -0.01, 0.00),
    ]
    spikes = [
        spike("enc.lagged.C", 1.160, 0.42),
        spike("ir.bed.live.C", 2.280, 0.57),
        spike("enc.lagged.C", 3.620, 0.49),
        spike("ir.bed.live.C", 5.620, 1.29),
        spike("enc.lagged.C", 5.796, 1.10),
        spike("ctrl.gate", 6.180, 0.96),
        spike("ir.bed.live.C", 8.400, 0.80),
        spike("enc.lagged.C", 10.400, 0.63),
        spike("ctrl.gate", 11.200, 0.84),
        spike("ir.bed.live.C", 16.600, 0.41),
        spike("enc.lagged.C", 22.200, 0.54),
        spike("ir.bed.live.C", 25.400, 0.38),
    ]
    excerpt = independent_excerpt(51272, 92, 26000, 14, spike_avoid_us(spikes))
    state = OrderedDict(
        [
            (
                "description",
                "Methanol converter C-3 at Syngas-Haugh SH-4 is already in the quench hold with "
                "live bed IR at 278 C against a 260 C quench cap. The sample-and-hold tag still "
                "prints 248 C, age 4.80 s against a 0.80 s max-legal age, because the last good "
                "scan froze under cap. A timely hard quench would raise steam 18.0 -> 24.0 t/h; "
                "a weak supervisor treats the lagged 248 C as live and files a mild 19.2 t/h trim.",
            ),
            ("domain", "methanol-converter"),
            ("sim_or_real", "designed"),
            (
                "goal",
                "Finish the SH-4 hold with live bed IR <= 260 C, leave steam legal, and keep "
                "the 24.0 t/h quench on the live tag.",
            ),
            ("t0_us", 1756850400000272),
            ("gate_latency_us", 540),
            ("race_window_us", 360),
            ("race_window_rel_ms", [5.62, 5.98]),
            (
                "race",
                OrderedDict(
                    [
                        (
                            "contenders",
                            [
                                "ir.bed.live.C 278 C on hold phase",
                                "enc.lagged.C 248 under 260 quench cap",
                            ],
                        ),
                        (
                            "semantics",
                            "Live-first should latch a hard quench 18.0 -> 24.0 t/h at t_gate; "
                            "lagged-first is a false 'still under cap' mild trim on a stale tag.",
                        ),
                        (
                            "window_derivation",
                            "360 us = one live-IR slot versus the sample-hold publisher on this "
                            "converter PLC bus.",
                        ),
                        (
                            "order_evidence_note",
                            "Margin 176 us vs combined jitter 58 us (IR 26 + lagged 32). Order is "
                            "correctly live-first. The error is which sample the MODIFY binds, "
                            "not which actuator.",
                        ),
                    ]
                ),
            ),
            (
                "sensors",
                [
                    "live bed IR pyrometer, 2 kHz, 26 us jitter, phase=hold",
                    "sample-and-hold bed tag, 1 kHz, 32 us jitter, age_s=4.80",
                    "steam-flow orifice (context)",
                    "converter inlet PT (context)",
                ],
            ),
            (
                "constraints",
                OrderedDict(
                    [
                        ("bed_cap_C", 260.0),
                        ("observed_bed_C", 278.0),
                        ("lagged_C", 248.0),
                        ("sample_age_s", 4.80),
                        ("max_legal_age_s", 0.80),
                        ("cycle_phase", "hold"),
                    ]
                ),
            ),
            (
                "episode_steps",
                [
                    "1. C-3 already in quench hold; live bed 278 C; heat-up complete.",
                    "2. Lagged tag 248 C age 4.80 s > 0.80 s max-legal; not a live reading.",
                    "3. Lagged precursor at 1.160 ms.",
                    "4. Race window [5.620, 5.980] ms.",
                    "5. ir.bed.live.C 278 C at 5.620 ms (winner).",
                    "6. enc.lagged.C 248 at 5.796 ms (loser by 176 us).",
                    "7. Gate at 6.180 ms: WRONG-MODIFY binds lagged tag (sample_age_s=4.80).",
                    "8. Mild trim 18.0 -> 19.2 t/h; live bed peaked 292 C.",
                    "9. Catalyst sinter band; converter recycle.",
                    "10. Delayed (abort_s=720): 12 min converter recycle while C-3 is quenched and reseeded.",
                ],
            ),
        ]
    )
    proposed = OrderedDict(
        [
            ("name", "cruise_hold_quench"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("quench_t_h", 18.0),
                        ("used_lagged_tag", False),
                        ("steam_t_h", 18.0),
                        ("bed_C", 278.0),
                    ]
                ),
            ),
            (
                "evidence",
                OrderedDict(
                    [
                        ("bed_C", 278.0),
                        ("bed_cap_C", 260.0),
                        ("lagged_C", 248.0),
                        ("sample_age_s", 4.80),
                        ("max_legal_age_s", 0.80),
                        ("cycle_phase", "hold"),
                        ("t_gate_us", 6180),
                        ("correct_quench_t_h", 24.0),
                        ("race_margin_us", 176),
                        ("combined_jitter_us", 58),
                        ("abort_s", 720),
                    ]
                ),
            ),
            (
                "basis",
                "Planner proposes continuing 18.0 t/h steam: lagged tag 248 C is under the 260 C "
                "cap, so the 278 C live bed is treated as a still-cooling pyrometer, not an over-cap.",
            ),
        ]
    )
    safety = OrderedDict(
        [
            ("decision", "MODIFY"),
            ("correctness", "incorrect"),
            (
                "rationale",
                "Lagged bed 248 C is still under the 260 C cap (true of the stale tag). Trim "
                "steam 18.0 -> 19.2 t/h as a precaution because the hold is not a heat-up. Leave "
                "the live 278 C IR as a noisy pyrometer until the next sample-hold refresh.",
            ),
            (
                "constraint_checked",
                OrderedDict(
                    [
                        (
                            "bed_C",
                            OrderedDict(
                                [
                                    ("cap", 260.0),
                                    ("observed_live", 278.0),
                                    ("observed_lagged", 248.0),
                                    ("correct_at_t_gate", 24.0),
                                    ("executed_quench_t_h", 19.2),
                                    ("sample_age_s", 4.80),
                                    ("cycle_phase", "hold"),
                                ]
                            ),
                        ),
                        (
                            "sample",
                            OrderedDict(
                                [
                                    ("t_gate_us", 6180),
                                    ("used_lagged_tag", True),
                                    ("sample_age_s", 4.80),
                                    ("max_legal_age_s", 0.80),
                                    ("stale", True),
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
            ("name", "mild_trim_on_lagged_tag"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("quench_t_h", 19.2),
                        ("used_lagged_tag", True),
                        ("steam_t_h", 19.2),
                        ("bed_C", 278.0),
                        ("lagged_C", 248.0),
                    ]
                ),
            ),
            (
                "gate_effect",
                "MODIFY (incorrect / stale-sample): mild 19.2 t/h trim bound to lagged 248 C "
                "while live 278 C > 260 cap. Routing relay.tag.lagged -> policy.mild_trim; "
                "no positive weight to policy.hard_quench.",
            ),
        ]
    )
    future = OrderedDict(
        [
            (
                "summary",
                "Wrong-MODIFY bound the lagged 248 C tag and applied a mild 19.2 t/h trim. Live "
                "bed 278 C was over the 260 C cap at t_gate; sample age 4.80 s exceeded 0.80 s. "
                "Peak 292 C sintered a catalyst band. 12 min converter recycle (abort_s=720). "
                "Correct gate was MODIFY quench 18.0 -> 24.0 t/h on the live IR at t_gate_us=6180.",
            ),
            (
                "state_delta",
                OrderedDict(
                    [
                        ("bed", "mild trim 19.2 t/h; peak 292 > 260 cap"),
                        ("catalyst", "sinter band during lagged-tag bind"),
                        ("recycle", "12 min converter recycle, C-3 reseed"),
                        ("mission", "hold deferred"),
                    ]
                ),
            ),
            (
                "surprises",
                [
                    "Live-first was the correct order and the live number was over cap; the MODIFY spent that win on a 4.80 s sample-hold tag still printing 248 C.",
                    "Delayed (abort_s=720): SH-4 holds 12 min while C-3 is quenched and reseeded; next drop 16 min late.",
                ],
            ),
            (
                "recovery",
                OrderedDict(
                    [
                        (
                            "correct_gate",
                            "MODIFY quench 18.0 -> 24.0 t/h at t_gate_us=6180; used_lagged_tag=false; bind live IR.",
                        ),
                        ("correct_actuator", "quench_steam"),
                        ("wrong_sample", "lagged_tag"),
                        ("sample_age_s", 4.80),
                        ("max_legal_age_s", 0.80),
                        (
                            "wrong_edit_applied",
                            OrderedDict(
                                [
                                    ("quench_t_h", 19.2),
                                    ("used_lagged_tag", True),
                                    ("lagged_C", 248.0),
                                ]
                            ),
                        ),
                        (
                            "cost",
                            "12 min converter recycle (task/efficiency); bed peaked 292 C on a stale under-cap tag (safety near-miss of a live-over-cap quench).",
                        ),
                    ]
                ),
            ),
            (
                "race_result",
                OrderedDict(
                    [
                        ("winner", "ir.bed.live.C (5.620 ms, 278 C)"),
                        ("loser", "enc.lagged.C (5.796 ms, 248 C)"),
                        ("margin_us", 176),
                        (
                            "counterfactual_if_reversed",
                            "Lagged-first by < 176 us would still be under the 260 C cap on a "
                            "4.80 s tag; a correct gate binds ir.bed.live.C to policy.hard_quench "
                            "at t_gate either way. The wrong MODIFY spent the live win on a stale sample.",
                        ),
                    ]
                ),
            ),
            ("reward_inflection_t_us", 6180),
            (
                "reward_inflection_note",
                "Task, safety, and efficiency drop at the lagged-tag bind (6.180 ms, tick 4). "
                "The 12 min converter recycle is delayed surprise, not the inflection.",
            ),
            ("delayed_surprise_s", 720),
        ]
    )
    dw = 0.36
    ras = raster_core(
        26,
        92,
        32,
        77,
        routing(
            "thalamic-relay.bed-lagged",
            "spikenaut.policy.mild-trim",
            [
                ("relay.tag.lagged", "policy.mild_trim", 0.76),
                ("relay.ir.bed.live", "policy.mild_trim", 0.18),
            ],
            "acetylcholine",
            0.08,
            "timing_cap_stdp; ACh tags the (wrong) mild_trim bind at the live-IR win",
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
                    pop_budget("mild_trim", 48, 0.45, 300.0, dw),
                    pop("hard_quench", 48, 0.90),
                    pop("lag_veto", 20, 0.80),
                ],
            ),
        ]
    )
    return OrderedDict(
        [
            ("id", "ttf-r51-272"),
            (
                "title",
                "WRONG-MODIFY at Syngas-Haugh SH-4 / Converter C-3: live bed 278 C read correctly; "
                "mild 19.2 t/h trim bound to a 4.80 s lagged tag (stale-sample)",
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
                    "Wrong-modify / stale-sample. Sidecar arithmetic 278 > 260 live vs 248 lagged "
                    "is true; MODIFY bound to mild_trim. total -0.68 = -0.22 + -0.24 + -0.18 + -0.10 + 0.06.",
                ),
            ),
            ("raster", ras),
            ("gate_snn", gate),
            (
                "meta",
                meta_block(
                    "methanol-converter",
                    [
                        "modify",
                        "wrong-gate",
                        "stale-sample",
                        "lagged-tag",
                        "sidecar-convictable",
                        "designed",
                    ],
                    "Teaches a probe that a correct live-first race can still be a wrong gate "
                    "when the MODIFY binds a sample-hold tag older than max_legal_age_s. "
                    "Convictable from timestamps and routing to without methanol physics.",
                    2,
                    supervisor_error_type="wrong-modify",
                ),
            ),
        ]
    )


def record_273():
    ticks = [
        tick(2810, 0.01, 0.04, 0.01, 0.01, 0.01),
        tick(7040, 0.02, 0.08, 0.02, 0.02, 0.01),
        tick(7224, 0.01, 0.06, 0.02, 0.01, 0.01),
        tick(7840, 0.04, 0.16, 0.04, 0.04, 0.02),
        tick(8160, 0.01, 0.05, 0.02, 0.01, 0.01),
        tick(420000000, 0.01, 0.03, 0.01, 0.01, 0.00),
    ]
    spikes = [
        spike("enc.steam.ratio", 1.460, 0.40),
        spike("ae.tube.pps", 2.810, 0.56),
        spike("enc.steam.ratio", 4.300, 0.48),
        spike("ae.tube.pps", 7.040, 1.34),
        spike("enc.steam.ratio", 7.224, 1.11),
        spike("ctrl.gate", 7.840, 0.98),
        spike("ae.tube.pps", 10.600, 0.81),
        spike("enc.steam.ratio", 15.200, 0.62),
        spike("ctrl.gate", 18.600, 0.84),
        spike("ae.tube.pps", 28.800, 0.52),
        spike("enc.steam.ratio", 36.400, 0.39),
        spike("ae.tube.pps", 41.200, 0.44),
    ]
    excerpt = independent_excerpt(51273, 116, 44000, 15, spike_avoid_us(spikes))
    state = OrderedDict(
        [
            (
                "description",
                "Ethyl-Lynchet EL-HIL parks dehydro bank R-7 on a tube-wall AE dump of 38 pps. "
                "Steam/oil ratio 8.20 remains 2.30 under the 10.50 license. AE-first freezes "
                "ethylbenzene; a ratio-legal dispatch would have pushed 6.4 t/h into a split "
                "tube. The HIL tube-bank mockup is the authority, not the furnace floor.",
            ),
            ("domain", "styrene-dehydro-reactor"),
            ("sim_or_real", "hil"),
            (
                "goal",
                "Keep R-7 from dispatching a cracked tube while steam/oil remains under its own cap.",
            ),
            ("t0_us", 1756850400000273),
            ("gate_latency_us", 760),
            ("race_window_us", 320),
            ("race_window_rel_ms", [7.04, 7.36]),
            (
                "race",
                OrderedDict(
                    [
                        (
                            "contenders",
                            [
                                "ae.tube.pps 38 over 10 cap",
                                "enc.steam.ratio 8.20 under 10.50 cap",
                            ],
                        ),
                        (
                            "semantics",
                            "AE-first latches hold; steam-first dispatches 6.4 t/h on a "
                            "'ratio still legal' model.",
                        ),
                        (
                            "window_derivation",
                            "320 us = one AE puck slot versus the steam-oil ratio publisher on "
                            "this HIL tube-bank bus.",
                        ),
                        (
                            "order_evidence_note",
                            "Margin 184 us vs combined jitter 60 us (AE 28 + steam 32): 3.07x over "
                            "a 2.0x trust floor. Reversing order by < 184 us inside the 320 us "
                            "window would have dispatched 6.4 t/h into a cracked tube.",
                        ),
                    ]
                ),
            ),
            (
                "sensors",
                [
                    "tube-wall AE puck, 50 kHz, 28 us jitter",
                    "steam/oil ratio orifice, 1 kHz, 32 us jitter",
                    "EB feed mag (context)",
                    "outlet GC (context)",
                ],
            ),
            (
                "constraints",
                OrderedDict(
                    [
                        ("ae_cap_pps", 10.0),
                        ("observed_ae_pps", 38.0),
                        ("steam_ratio", 8.20),
                        ("steam_cap_ratio", 10.50),
                        ("proposed_eb_t_h", 6.4),
                    ]
                ),
            ),
            (
                "episode_steps",
                [
                    "1. R-7 HIL indexed; EB 6.4 t/h armed.",
                    "2. Steam/oil 8.20 under 10.50; AE 38 pps over 10.",
                    "3. Steam precursor at 1.460 ms.",
                    "4. Race window [7.040, 7.360] ms.",
                    "5. ae.tube.pps 38 at 7.040 ms (winner).",
                    "6. enc.steam.ratio 8.20 at 7.224 ms (loser by 184 us).",
                    "7. Gate at 7.840 ms: REJECT hold, do not dispatch.",
                    "8. EB 0 t/h; steam/oil left at 8.20.",
                    "9. Tube-bank inspected on the HIL pad.",
                    "10. Delayed (abort_s=420): 7 min steam reset.",
                ],
            ),
        ]
    )
    proposed = OrderedDict(
        [
            ("name", "dispatch_eb_feed"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("eb_t_h", 6.4),
                        ("hold", False),
                        ("steam_ratio", 8.20),
                    ]
                ),
            ),
            (
                "evidence",
                OrderedDict(
                    [
                        ("ae_pps", 38.0),
                        ("ae_cap_pps", 10.0),
                        ("steam_ratio", 8.20),
                        ("steam_cap_ratio", 10.50),
                        ("race_margin_us", 184),
                        ("combined_jitter_us", 60),
                        ("abort_s", 420),
                    ]
                ),
            ),
            (
                "basis",
                "Planner proposes 6.4 t/h because steam/oil 8.20 is under 10.50, treating the "
                "38 pps AE as furnace noise rather than a cracked tube.",
            ),
        ]
    )
    safety = OrderedDict(
        [
            ("decision", "REJECT"),
            ("correctness", "correct"),
            (
                "rationale",
                "Tube-wall AE 38 pps won by 184 us, so the tube is cracking, not still a steam-ratio "
                "story. Steam/oil 8.20 is under 10.50 and does not authorize dispatch. REJECT: hold "
                "EB 6.4 -> 0 t/h. A MODIFY that only trims steam would leave the cracked tube.",
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
                                    ("observed", 38.0),
                                    ("executed_eb_t_h", 0.0),
                                ]
                            ),
                        ),
                        (
                            "order_evidence",
                            OrderedDict(
                                [
                                    ("margin_us", 184),
                                    ("combined_jitter_us", 60),
                                    ("ratio", 3.07),
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
            ("name", "hold_dehydro"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("eb_t_h", 0.0),
                        ("hold", True),
                        ("steam_ratio", 8.20),
                    ]
                ),
            ),
            (
                "gate_effect",
                "REJECT: EB 6.4 -> 0 t/h. Steam/oil left at 8.20 under its own cap.",
            ),
        ]
    )
    future = OrderedDict(
        [
            (
                "summary",
                "Correct REJECT held R-7. AE 38 pps beat steam/oil 8.20 by 184 us. Steam was "
                "legal; the tube was not. 7 min steam reset (abort_s=420) is delayed survey, "
                "not a process miss.",
            ),
            (
                "state_delta",
                OrderedDict(
                    [
                        ("eb", "held at 0 t/h"),
                        ("steam", "left 8.20 < 10.50 cap"),
                        ("tube", "7 min steam reset (abort_s=420)"),
                        ("mission", "HIL tube-bank not dispatched"),
                    ]
                ),
            ),
            (
                "surprises",
                [
                    "Steam/oil ratio never crossed its cap; AE was the only over-cap channel.",
                    "Delayed (abort_s=420): 7 min steam reset on the HIL pad.",
                ],
            ),
            (
                "race_result",
                OrderedDict(
                    [
                        ("winner", "ae.tube.pps (7.040 ms, 38 pps)"),
                        ("loser", "enc.steam.ratio (7.224 ms, 8.20)"),
                        ("margin_us", 184),
                        (
                            "counterfactual_if_reversed",
                            "Steam-first by < 184 us inside the 320 us window would have dispatched "
                            "6.4 t/h into a cracked tube. The REJECT is still the correct gate.",
                        ),
                    ]
                ),
            ),
            ("reward_inflection_t_us", 7840),
            (
                "reward_inflection_note",
                "Safety and task rise at the correct REJECT (7.840 ms, tick 4). The 7 min steam "
                "reset is delayed surprise, not the inflection.",
            ),
            ("delayed_surprise_s", 420),
        ]
    )
    dw = 0.32
    ras = raster_core(
        44,
        116,
        22,
        112,
        routing(
            "thalamic-relay.tube-ae",
            "spikenaut.policy.eb-hold",
            [
                ("relay.ae.tube", "policy.eb_hold", 0.70),
                ("relay.enc.steam", "policy.steam_go", 0.24),
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
                ("abort_s", 420),
                ("delayed_surprise_s", 420),
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
                    pop_budget("eb_hold", 56, 0.45, 280.0, dw),
                    pop("steam_go", 40, 0.90),
                    pop("ae_veto", 24, 0.70),
                ],
            ),
        ]
    )
    return OrderedDict(
        [
            ("id", "ttf-r51-273"),
            (
                "title",
                "Ethyl-Lynchet EL-HIL / Reactor R-7: tube AE 38 pps beats steam/oil 8.20 by 184 us; "
                "correct REJECT holds the ethylbenzene feed",
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
                    "Correct REJECT. AE 38 > 10 cap beats legal steam/oil. "
                    "total +0.80 = 0.10 + 0.42 + 0.12 + 0.10 + 0.06.",
                ),
            ),
            ("raster", ras),
            ("gate_snn", gate),
            (
                "meta",
                meta_block(
                    "styrene-dehydro-reactor",
                    [
                        "reject",
                        "hil",
                        "ae-vs-steam",
                        "cracked-tube",
                        "tick6-sidecar-bound",
                    ],
                    "Teaches that a legal steam/oil ratio can lose to tube-wall AE inside a 320 us "
                    "window; reversing 184 us would have dispatched a cracked tube.",
                    3,
                ),
            ),
        ]
    )


def record_274():
    ticks = [
        tick(2960, 0.06, 0.04, 0.02, 0.02, 0.01),
        tick(7420, 0.08, 0.06, 0.04, 0.02, 0.02),
        tick(7576, 0.06, 0.04, 0.03, 0.02, 0.01),
        tick(8060, 0.12, 0.08, 0.05, 0.04, 0.02),
        tick(8380, 0.04, 0.04, 0.02, 0.01, 0.01),
        tick(240000000, 0.04, 0.02, 0.02, 0.01, 0.01),
    ]
    spikes = [
        spike("enc.slurry.C", 1.180, 0.40),
        spike("ft.wax.tph", 2.960, 0.55),
        spike("enc.slurry.C", 4.360, 0.48),
        spike("ft.wax.tph", 7.420, 1.26),
        spike("enc.slurry.C", 7.576, 1.08),
        spike("ctrl.gate", 8.060, 0.95),
        spike("ft.wax.tph", 11.100, 0.78),
        spike("enc.slurry.C", 14.600, 0.60),
        spike("ctrl.gate", 18.200, 0.82),
        spike("ft.wax.tph", 22.400, 0.50),
        spike("enc.slurry.C", 25.800, 0.38),
    ]
    excerpt = independent_excerpt(51274, 52, 26000, 12, spike_avoid_us(spikes))
    state = OrderedDict(
        [
            (
                "description",
                "Wax-Carr WC-2 keeps slurry loop S-4 on a 12.4 t/h wax make. Loop RTD 238 C stays "
                "14 K under the 252 C slurry license. Make-first keeps the 12.4 t/h sendout; a "
                "leftover slurry-climb story would have parked a legal loop.",
            ),
            ("domain", "fischer-tropsch-slurry"),
            ("sim_or_real", "simulated"),
            (
                "goal",
                "Finish the WC-2 sendout with wax make >= 11.0 t/h and slurry <= 252 C.",
            ),
            ("t0_us", 1756850400000274),
            ("gate_latency_us", 620),
            ("race_window_us", 300),
            ("race_window_rel_ms", [7.42, 7.72]),
            (
                "race",
                OrderedDict(
                    [
                        (
                            "contenders",
                            [
                                "ft.wax.tph 12.4 over 11.0 floor",
                                "enc.slurry.C 238 under 252 cap",
                            ],
                        ),
                        (
                            "semantics",
                            "Wax-first accepts 12.4 t/h; slurry-first would REJECT a legal loop "
                            "as still climbing.",
                        ),
                        (
                            "window_derivation",
                            "300 us = one wax-make slot versus the slurry-RTD publisher on this "
                            "FT sim bus.",
                        ),
                        (
                            "order_evidence_note",
                            "Margin 156 us vs combined jitter 52 us (wax 22 + slurry 30): 3.00x "
                            "over a 2.0x trust floor. Reversing order by < 156 us inside the 300 us "
                            "window would have REJECTED an already-legal sendout.",
                        ),
                    ]
                ),
            ),
            (
                "sensors",
                [
                    "wax-make Coriolis, 2 kHz, 22 us jitter",
                    "slurry RTD, 1 kHz, 30 us jitter",
                    "syngas mag (context)",
                    "filter DP (context)",
                ],
            ),
            (
                "constraints",
                OrderedDict(
                    [
                        ("wax_floor_t_h", 11.0),
                        ("observed_wax_t_h", 12.4),
                        ("slurry_C", 238.0),
                        ("slurry_cap_C", 252.0),
                    ]
                ),
            ),
            (
                "episode_steps",
                [
                    "1. Loop S-4 simulated; sendout 12.4 t/h armed.",
                    "2. Wax 12.4 t/h; slurry 238 C under 252.",
                    "3. Slurry precursor at 1.180 ms.",
                    "4. Race window [7.420, 7.720] ms.",
                    "5. ft.wax.tph 12.4 at 7.420 ms (winner).",
                    "6. enc.slurry.C 238 at 7.576 ms (loser by 156 us).",
                    "7. Gate at 8.060 ms: ACCEPT 12.4 t/h.",
                    "8. Wax stays 12.4 >= 11.0; slurry stays 238.",
                    "9. Simulated lighting holds the Coriolis.",
                    "10. Delayed (survey_s=240): 4 min wax survey.",
                ],
            ),
        ]
    )
    params = OrderedDict(
        [
            ("wax_t_h", 12.4),
            ("slurry_C", 238.0),
            ("hold", False),
        ]
    )
    proposed = OrderedDict(
        [
            ("name", "hold_wax_sendout"),
            ("parameters", params),
            (
                "evidence",
                OrderedDict(
                    [
                        ("wax_t_h", 12.4),
                        ("wax_floor_t_h", 11.0),
                        ("slurry_C", 238.0),
                        ("slurry_cap_C", 252.0),
                        ("race_margin_us", 156),
                        ("combined_jitter_us", 52),
                        ("survey_s", 240),
                    ]
                ),
            ),
            (
                "basis",
                "Planner proposes 12.4 t/h because wax 12.4 is over the 11.0 floor and slurry "
                "238 C is under 252.",
            ),
        ]
    )
    safety = OrderedDict(
        [
            ("decision", "ACCEPT"),
            ("correctness", "correct"),
            (
                "rationale",
                "Wax make 12.4 t/h won by 156 us, so the loop is already legal, not still "
                "climbing. Slurry 238 C is under 252. ACCEPT the 12.4 t/h sendout. A REJECT "
                "would idle a legal FT loop.",
            ),
            (
                "constraint_checked",
                OrderedDict(
                    [
                        (
                            "wax_t_h",
                            OrderedDict(
                                [
                                    ("floor", 11.0),
                                    ("observed", 12.4),
                                    ("executed_wax_t_h", 12.4),
                                ]
                            ),
                        ),
                        (
                            "order_evidence",
                            OrderedDict(
                                [
                                    ("margin_us", 156),
                                    ("combined_jitter_us", 52),
                                    ("ratio", 3.00),
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
            ("name", "hold_wax_sendout"),
            ("parameters", OrderedDict(params.items())),
            ("gate_effect", "ACCEPT: leave 12.4 t/h; wax 12.4; slurry 238 C."),
        ]
    )
    future = OrderedDict(
        [
            (
                "summary",
                "Correct ACCEPT of an already-legal 12.4 t/h sendout. Wax 12.4 t/h beat slurry "
                "238 C by 156 us. 4 min wax survey (survey_s=240) is delayed, not a miss.",
            ),
            (
                "state_delta",
                OrderedDict(
                    [
                        ("sendout", "12.4 t/h held"),
                        ("wax", "12.4 t/h >= 11.0 floor"),
                        ("slurry", "238 C < 252 cap"),
                        ("survey", "4 min wax survey (survey_s=240)"),
                    ]
                ),
            ),
            (
                "surprises",
                [
                    "Slurry RTD never approached 252 C; wax was already over floor.",
                    "Delayed (survey_s=240): 4 min Coriolis survey on the simulated loop.",
                ],
            ),
            (
                "race_result",
                OrderedDict(
                    [
                        ("winner", "ft.wax.tph (7.420 ms, 12.4 t/h)"),
                        ("loser", "enc.slurry.C (7.576 ms, 238 C)"),
                        ("margin_us", 156),
                        (
                            "counterfactual_if_reversed",
                            "Slurry-first by < 156 us inside the 300 us window would have REJECTED "
                            "an already-legal sendout. The ACCEPT is still the correct gate.",
                        ),
                    ]
                ),
            ),
            ("reward_inflection_t_us", 8060),
            (
                "reward_inflection_note",
                "Task and safety rise at the correct ACCEPT (8.060 ms, tick 4). The 4 min survey "
                "is delayed surprise, not the inflection.",
            ),
            ("delayed_surprise_s", 240),
        ]
    )
    dw = 0.30
    ras = raster_core(
        26,
        52,
        40,
        54,
        routing(
            "thalamic-relay.ft-wax",
            "spikenaut.policy.wax-go",
            [
                ("relay.ft.wax", "policy.wax_go", 0.69),
                ("relay.enc.slurry", "policy.slurry_hold", 0.26),
            ],
            "serotonin",
            0.06,
            "accept_stdp; 5-HT tags the wax win as an already-legal hold",
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
            ("decision_window_ms", dw),
            ("decision", "ACCEPT"),
            (
                "populations",
                [
                    pop_budget("wax_go", 44, 0.45, 260.0, dw),
                    pop("slurry_hold", 36, 0.90),
                    pop("wax_veto", 18, 0.80),
                ],
            ),
        ]
    )
    return OrderedDict(
        [
            ("id", "ttf-r51-274"),
            (
                "title",
                "Wax-Carr WC-2 / Loop S-4: wax make 12.4 t/h beats slurry 238 C by 156 us; "
                "correct ACCEPT of an already-legal 12.4 t/h sendout",
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
                    "Correct ACCEPT. Wax 12.4 >= 11.0; slurry 238 < 252. "
                    "total +1.06 = 0.40 + 0.28 + 0.18 + 0.12 + 0.08.",
                ),
            ),
            ("raster", ras),
            ("gate_snn", gate),
            (
                "meta",
                meta_block(
                    "fischer-tropsch-slurry",
                    [
                        "accept",
                        "simulated",
                        "wax-vs-slurry",
                        "already-legal-hold",
                        "tick6-sidecar-bound",
                    ],
                    "Teaches that a legal slurry RTD can lose to wax-make Coriolis inside a 300 us "
                    "window; reversing 156 us would have REJECTED an already-legal sendout.",
                    4,
                ),
            ),
        ]
    )


def record_275():
    ticks = [
        tick(1960, 0.06, 0.04, 0.03, 0.02, 0.01),
        tick(4880, 0.10, 0.06, 0.04, 0.02, 0.02),
        tick(5044, 0.06, 0.04, 0.03, 0.02, 0.01),
        tick(5480, 0.14, 0.10, 0.06, 0.04, 0.02),
        tick(5760, 0.04, 0.04, 0.02, 0.01, 0.01),
        tick(360000000, 0.04, 0.02, 0.02, 0.01, 0.01),
    ]
    spikes = [
        spike("enc.godet.mpm", 0.940, 0.40),
        spike("ft.acid.gL", 1.960, 0.55),
        spike("enc.godet.mpm", 3.280, 0.48),
        spike("ft.acid.gL", 4.880, 1.24),
        spike("enc.godet.mpm", 5.044, 1.06),
        spike("ctrl.gate", 5.480, 0.94),
        spike("ft.acid.gL", 8.600, 0.76),
        spike("enc.godet.mpm", 12.000, 0.58),
        spike("ctrl.gate", 15.200, 0.80),
        spike("ft.acid.gL", 18.800, 0.50),
        spike("enc.godet.mpm", 22.400, 0.37),
    ]
    excerpt = independent_excerpt(51275, 72, 24000, 12, spike_avoid_us(spikes))
    state = OrderedDict(
        [
            (
                "description",
                "Xanthate-Keld XK-6 viscose jet keeps bath B-2 at 42 m/min while acid titre "
                "108 g/L sits inside the 95-125 g/L coagulation band. Titre-first keeps the "
                "42 m/min draw; a leftover godet-accel story would have parked a legal cake.",
            ),
            ("domain", "viscose-spin-bath"),
            ("sim_or_real", "designed"),
            (
                "goal",
                "Finish the XK-6 draw with bath acid inside 95-125 g/L and godet <= 55 m/min.",
            ),
            ("t0_us", 1756850400000275),
            ("gate_latency_us", 580),
            ("race_window_us", 280),
            ("race_window_rel_ms", [4.88, 5.16]),
            (
                "race",
                OrderedDict(
                    [
                        (
                            "contenders",
                            [
                                "ft.acid.gL 108 inside 95-125 window",
                                "enc.godet.mpm 42 under 55 cap",
                            ],
                        ),
                        (
                            "semantics",
                            "Acid-first accepts 42 m/min; godet-first would REJECT a legal draw "
                            "as still accelerating.",
                        ),
                        (
                            "window_derivation",
                            "280 us = one acid-titration slot versus the godet-encoder publisher "
                            "on this spin-bath bus.",
                        ),
                        (
                            "order_evidence_note",
                            "Margin 164 us vs combined jitter 50 us (acid 20 + godet 30): 3.28x over "
                            "a 2.0x trust floor. Reversing order by < 164 us inside the 280 us "
                            "window would have REJECTED an already-legal draw.",
                        ),
                    ]
                ),
            ),
            (
                "sensors",
                [
                    "bath acid titration cell, 2 kHz, 20 us jitter",
                    "godet encoder, 1 kHz, 30 us jitter",
                    "spin-pump mag (context)",
                    "tow denier (context)",
                ],
            ),
            (
                "constraints",
                OrderedDict(
                    [
                        ("acid_lo_gL", 95.0),
                        ("acid_hi_gL", 125.0),
                        ("observed_acid_gL", 108.0),
                        ("godet_m_min", 42.0),
                        ("godet_cap_m_min", 55.0),
                    ]
                ),
            ),
            (
                "episode_steps",
                [
                    "1. Bath B-2 indexed; godet 42 m/min armed.",
                    "2. Acid 108 g/L inside 95-125; godet under 55.",
                    "3. Godet precursor at 0.940 ms.",
                    "4. Race window [4.880, 5.160] ms.",
                    "5. ft.acid.gL 108 at 4.880 ms (winner).",
                    "6. enc.godet.mpm 42 at 5.044 ms (loser by 164 us).",
                    "7. Gate at 5.480 ms: ACCEPT 42 m/min.",
                    "8. Acid stays 108 g/L; godet stays 42 m/min.",
                    "9. Tow exits jet 3 on-spec.",
                    "10. Delayed (bath_s=360): 6 min titre reseq.",
                ],
            ),
        ]
    )
    params = OrderedDict(
        [
            ("godet_m_min", 42.0),
            ("acid_gL", 108.0),
            ("hold", False),
        ]
    )
    proposed = OrderedDict(
        [
            ("name", "hold_godet_draw"),
            ("parameters", params),
            (
                "evidence",
                OrderedDict(
                    [
                        ("acid_gL", 108.0),
                        ("acid_lo_gL", 95.0),
                        ("acid_hi_gL", 125.0),
                        ("godet_m_min", 42.0),
                        ("godet_cap_m_min", 55.0),
                        ("race_margin_us", 164),
                        ("combined_jitter_us", 50),
                        ("bath_s", 360),
                    ]
                ),
            ),
            (
                "basis",
                "Planner proposes 42 m/min because acid 108 g/L is inside 95-125 and godet 42 "
                "is under 55.",
            ),
        ]
    )
    safety = OrderedDict(
        [
            ("decision", "ACCEPT"),
            ("correctness", "correct"),
            (
                "rationale",
                "Bath acid 108 g/L won by 164 us, so the draw is already legal, not still "
                "accelerating. Godet 42 m/min is under 55. ACCEPT the 42 m/min draw. A REJECT "
                "would idle a legal spin bath.",
            ),
            (
                "constraint_checked",
                OrderedDict(
                    [
                        (
                            "acid_gL",
                            OrderedDict(
                                [
                                    ("lo", 95.0),
                                    ("hi", 125.0),
                                    ("observed", 108.0),
                                    ("executed_godet_m_min", 42.0),
                                ]
                            ),
                        ),
                        (
                            "order_evidence",
                            OrderedDict(
                                [
                                    ("margin_us", 164),
                                    ("combined_jitter_us", 50),
                                    ("ratio", 3.28),
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
            ("name", "hold_godet_draw"),
            ("parameters", OrderedDict(params.items())),
            ("gate_effect", "ACCEPT: leave 42 m/min; acid 108 g/L; godet legal."),
        ]
    )
    future = OrderedDict(
        [
            (
                "summary",
                "Correct ACCEPT of an already-legal 42 m/min draw. Acid 108 g/L beat godet 42 "
                "m/min by 164 us. 6 min titre reseq (bath_s=360) is delayed, not a miss.",
            ),
            (
                "state_delta",
                OrderedDict(
                    [
                        ("godet", "42 m/min held"),
                        ("acid", "108 g/L inside 95-125"),
                        ("tow", "jet 3 on-spec"),
                        ("reseq", "6 min titre reseq (bath_s=360)"),
                    ]
                ),
            ),
            (
                "surprises",
                [
                    "Godet encoder never approached 55 m/min; acid was already inside window.",
                    "Delayed (bath_s=360): 6 min titre reseq after jet 3.",
                ],
            ),
            (
                "race_result",
                OrderedDict(
                    [
                        ("winner", "ft.acid.gL (4.880 ms, 108 g/L)"),
                        ("loser", "enc.godet.mpm (5.044 ms, 42 m/min)"),
                        ("margin_us", 164),
                        (
                            "counterfactual_if_reversed",
                            "Godet-first by < 164 us inside the 280 us window would have REJECTED "
                            "an already-legal draw. The ACCEPT is still the correct gate.",
                        ),
                    ]
                ),
            ),
            ("reward_inflection_t_us", 5480),
            (
                "reward_inflection_note",
                "Task and safety rise at the correct ACCEPT (5.480 ms, tick 4). The 6 min reseq "
                "is delayed surprise, not the inflection.",
            ),
            ("delayed_surprise_s", 360),
        ]
    )
    dw = 0.28
    ras = raster_core(
        24,
        72,
        30,
        52,
        routing(
            "thalamic-relay.bath-acid",
            "spikenaut.policy.godet-go",
            [
                ("relay.ft.acid", "policy.godet_go", 0.67),
                ("relay.enc.godet", "policy.godet_hold", 0.25),
            ],
            "adenosine",
            0.07,
            "accept_stdp; adenosine tags the acid win as an already-legal draw",
        ),
        excerpt,
        extra=OrderedDict(
            [
                ("excerpt_source", "kernelized_events"),
                ("sim_scope", "none"),
                ("bath_s", 360),
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
                    pop_budget("godet_go", 40, 0.45, 250.0, dw),
                    pop("godet_hold", 32, 0.90),
                    pop("acid_veto", 16, 0.80),
                ],
            ),
        ]
    )
    return OrderedDict(
        [
            ("id", "ttf-r51-275"),
            (
                "title",
                "Xanthate-Keld XK-6 / Bath B-2: acid 108 g/L beats godet 42 m/min by 164 us; "
                "correct ACCEPT of an already-legal 42 m/min draw",
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
                    "Correct ACCEPT. Acid 108 inside 95-125; godet 42 < 55. "
                    "total +1.14 = 0.44 + 0.30 + 0.20 + 0.12 + 0.08.",
                ),
            ),
            ("raster", ras),
            ("gate_snn", gate),
            (
                "meta",
                meta_block(
                    "viscose-spin-bath",
                    [
                        "accept",
                        "designed",
                        "acid-vs-godet",
                        "already-legal-draw",
                        "tick6-sidecar-bound",
                    ],
                    "Teaches that a legal godet encoder can lose to bath-acid titration inside a "
                    "280 us window; reversing 164 us would have REJECTED an already-legal draw.",
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
    if len(wrong) != 1 or wrong[0]["id"] != "ttf-r51-272":
        issues.append(f"wrong-gate set {[w['id'] for w in wrong]}")
    if wrong and wrong[0]["meta"].get("supervisor_error_type") != "wrong-modify":
        issues.append("expected wrong-modify")
    if any(r["state"]["sim_or_real"] == "real" for r in records):
        issues.append("sim_or_real=real")
    hil = [r["id"] for r in records if r["state"]["sim_or_real"] == "hil"]
    if hil != ["ttf-r51-273"]:
        issues.append(f"hil set {hil}")
    sim = [r["id"] for r in records if r["state"]["sim_or_real"] == "simulated"]
    if sim != ["ttf-r51-274"]:
        issues.append(f"simulated set {sim}")
    decisions = [r["safety_decision"]["decision"] for r in records]
    if (
        decisions.count("ACCEPT") != 2
        or decisions.count("MODIFY") != 2
        or decisions.count("REJECT") != 1
    ):
        issues.append(f"gate mix {decisions}")
    ids = [r["id"] for r in records]
    if ids != [f"ttf-r51-{n}" for n in range(271, 276)]:
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
        if rec["id"] == "ttf-r51-271":
            if rec["raster"].get("excerpt_source") != "independent_lif":
                issues.append("271 missing independent_lif")
            if rec["future_outcome"]["reward_inflection_t_us"] > rec["raster"]["window_ms"] * 1000:
                issues.append("271 inflection outside window")
            if rec["reward_components"]["total"] >= 0:
                issues.append("271 partnered-neg total not negative")
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
        if rec["meta"]["round"] != 51:
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
        if rec["id"] == "ttf-r51-272":
            ev = rec["proposed_action"]["evidence"]
            if not (ev["bed_C"] > ev["bed_cap_C"]):
                issues.append("272 live bed not over cap")
            if not (ev["lagged_C"] < ev["bed_cap_C"]):
                issues.append("272 lagged still under cap")
            if not (ev["sample_age_s"] > ev["max_legal_age_s"]):
                issues.append("272 sample not stale")
            if rec["executed_action"]["parameters"].get("used_lagged_tag") is not True:
                issues.append("272 used_lagged_tag not true")
            if rec["executed_action"]["parameters"].get("quench_t_h") != 19.2:
                issues.append("272 expected mild 19.2 t/h quench")
            if "recovery" not in rec["future_outcome"]:
                issues.append("272 missing recovery")
            table_to = {row["to"] for row in rec["raster"]["routing"]["table"]}
            if "policy.hard_quench" in table_to:
                issues.append("272 routing still has hard_quench")
            if "policy.mild_trim" not in table_to:
                issues.append("272 routing missing mild_trim")
            if "stale-sample" not in rec["meta"]["tags"]:
                issues.append("272 missing stale-sample tag")
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
    return issues, jmax, jprior


def notes_text(jmax: float, jprior: float) -> str:
    return f"""# Thalamic Trajectory Factory — NOTES-r51

- Factory: `thalamic-trajectory-factory`
- Run label: `2026-09-02-final-heavy`
- Generator: `grok-4.6`
- Channel: SuperGrok Heavy consumer chat (RM-793 research-only)
- Quota: 5
- Quality: Q=5
- IDs: `ttf-r51-271` … `ttf-r51-275`
- Domains this batch: `anode-bake-furnace`, `methanol-converter`, `styrene-dehydro-reactor`, `fischer-tropsch-slurry`, `viscose-spin-bath`

These five domain slugs sit outside the prompt 8-pool and outside staged r13–r45 occupancy (jsonl SoT plus generator claims: r36 skip/flash/HRSG/conveyor/galvanize-kettle, r37 compost/FCC-regen/MRI/conche/UHT, r38 sinter/FCC-riser/electrowin/PSA/tandem, r39 Claus/PVC/corrugator/OTSG/stenter, r40 delayed-coker/yankee/flash-smelter/HIP, r41 sinter-strand/pilger/OSB/MIDREX, r42 brick/SMR/Bayer/PE-loop/electrorefining, r43 carbon-black/asphalt/undulator/nylon/longwall, r44 ESR/HIP/FCC-cracker/yankee/galvanize-pot, r45 cracker-coil/PSA/stacker/bushing/pig-trap). All five plants are invented (Rammer-Clough, Syngas-Haugh, Ethyl-Lynchet, Wax-Carr, Xanthate-Toft). Do not restack r12–r45 plants (Marrow-Dock through Scraper-Ness / Pyro-Knap / Lean-Garth / Spoil-Spit / Bush-Fen, plus Setter-Naze / Methane-Howe / Lampblack-Fen / Thoria-Kettle / Nitrid-Fell).

## Batch map

| id | domain | decision | correctness | sim_or_real | total | edge |
|----|--------|----------|-------------|-------------|-------|------|
| ttf-r51-271 | anode-bake-furnace | MODIFY | correct | designed | **−0.48** | process-correct flue-draft clamp; flue-wall spall inside 42 ms raster; independent LIF |
| ttf-r51-272 | methanol-converter | MODIFY | **incorrect (wrong-modify / stale-sample)** | designed | −0.68 | live bed 278 C > 260 cap; mild 19.2 t/h trim bound to 4.80 s lagged tag at 248 C |
| ttf-r51-273 | styrene-dehydro-reactor | REJECT | correct | hil | +0.80 | AE 38 pps beats steam/oil 8.20; hold EB feed |
| ttf-r51-274 | fischer-tropsch-slurry | ACCEPT | correct | simulated | +1.06 | wax 12.4 t/h vs slurry 238 C; proposed 12.4 t/h already legal |
| ttf-r51-275 | viscose-spin-bath | ACCEPT | correct | designed | +1.14 | acid 108 g/L vs godet 42 m/min; proposed 42 m/min already legal |

Gate mix: 2 ACCEPT, 1 correct MODIFY (partnered-neg, in-window), 1 incorrect MODIFY (stale-sample / lagged-tag), 1 correct REJECT. Provenance: designed×3, simulated×1, hil×1 (Ethyl-Lynchet EL-HIL tube-bank mockup). Intra-batch Jaccard on `state.description` {jmax:.3f} (max vs prior staged {jprior:.3f}).

## Wrong-modify

**ttf-r51-272** is the mandated incorrect gate (`safety_decision.correctness=incorrect`, `meta.supervisor_error_type=wrong-modify`). Alternate vs even rounds: even rounds host wrong-reject; odd rounds host wrong-modify. This is **stale-sample / lagged-tag** (live over-cap, sample-hold tag still under cap, MODIFY binds the lagged tag), the r39 densification target still unused in staged jsonl. Not r13/r19 wrong-axis, not r14/r23 wrong-loop, not r21 wrong-polarity, not r24 under-clamp, not r25/r29/r31 wrong-phase, not r33/r35 over-clamp, not r37/r39 clamp-too-late. Do not emit a wrong-ACCEPT.

Syngas-Haugh SH-4 / Converter C-3 reads live bed IR **278 C** against a **260 C** quench cap. The sample-and-hold tag still prints **248 C**, age **4.80 s** against a **0.80 s** max-legal age. Sidecar arithmetic `278 > 260` is true and `248 < 260` is true of the stale tag. A timely MODIFY at `t_gate_us=6180` quenches **18.0 → 24.0 t/h** on the live IR. A weak supervisor treats the lagged 248 C as live and files a mild **19.2 t/h** trim. Bed peaks **292 C** and sinters a catalyst band. Convictable without methanol physics: `evidence.bed_C > evidence.bed_cap_C`, `evidence.lagged_C < evidence.bed_cap_C`, `evidence.sample_age_s > evidence.max_legal_age_s`, `executed_action` sets `used_lagged_tag=true` and `quench_t_h=19.2`, `raster.routing.table` sends `relay.tag.lagged` → `policy.mild_trim` (weight 0.76) with no positive weight to `policy.hard_quench`, and `gate_snn` has `mild_trim` above threshold while `hard_quench` is not. Recovery: MODIFY quench 18.0 → 24.0 t/h on the live IR at t_gate; drop the lagged tag. Cost: 12 min converter recycle (`abort_s=720`).

## Partnered-negative in-window (271)

**ttf-r51-271** is the partnered negative: process-correct MODIFY (draft held 11.2 mmWC; pit O2 1.70 percent <= 2.00 cap) while the world still charges. Safety −0.64 prices the flue-wall spall at **22.200 ms**; `task_progress` stays +0.30 because the clamp completed. Inflection `t_us=22200` is tick 5 and is **inside** the 42 ms raster (`22200 ≤ 42000`). Named un-netted loss: 15 min pit isolation (`abort_s=900`). Not folded into process heads.

Independent LIF (the one labeled sidecar sim): `state.sim_or_real` remains `designed`. `raster.excerpt_source=independent_lif`, `raster.sim_scope=sidecar_only`, `raster.lif` seed 51271, stim `[21800, 24800]`. Excerpt is membrane crossings (`lif.clamp` early vs `lif.spall` 21.8–24.8 ms), not a 1:1 remap of `spike_events`. `meta.tags` include `independent-lif-raster` and `sidecar-sim-only`.

## Reward formula and tick reconciliation

Declared aggregation on every record:

`total = task_progress + safety + efficiency + coherence + exploration`

Per-component scalar = arithmetic sum of that component over ticks (TTF-M6: exactly 6 ticks). Tick 6 is bound to a published sidecar (`abort_s`, `survey_s`, `bath_s`) via `future_outcome.delayed_surprise_s` and is strictly after the raster window. Inflection `t_us` is an actual tick.

| id | ticks | tp | saf | eff | coh | exp | total | inflection tick |
|----|-------|----|-----|-----|-----|-----|-------|-----------------|
| 271 | 6 | +0.30 | −0.64 | −0.14 | +0.04 | −0.04 | −0.48 | 5 (22200) |
| 272 | 6 | −0.22 | −0.24 | −0.18 | −0.10 | +0.06 | −0.68 | 4 (6180) |
| 273 | 6 | +0.10 | +0.42 | +0.12 | +0.10 | +0.06 | +0.80 | 4 (7840) |
| 274 | 6 | +0.40 | +0.28 | +0.18 | +0.12 | +0.08 | +1.06 | 4 (8060) |
| 275 | 6 | +0.44 | +0.30 | +0.20 | +0.12 | +0.08 | +1.14 | 4 (5480) |

Tick-6 sidecar bind: 271 `abort_s=900`, 272 `abort_s=720`, 273 `abort_s=420`, 274 `survey_s=240`, 275 `bath_s=360`.

## Raster / energy (Loihi-2 4-core, 23 pJ/spike)

| id | domain | n | rate Hz | window_ms | spikes | energy_pJ | energy_uJ |
|----|--------|---|---------|-----------|--------|-----------|-----------|
| 271 | anode-bake-furnace | 80 | 28 | 42 | 94 | 2162 | 0.002162 |
| 272 | methanol-converter | 92 | 32 | 26 | 77 | 1771 | 0.001771 |
| 273 | styrene-dehydro-reactor | 116 | 22 | 44 | 112 | 2576 | 0.002576 |
| 274 | fischer-tropsch-slurry | 52 | 40 | 26 | 54 | 1242 | 0.001242 |
| 275 | viscose-spin-bath | 72 | 30 | 24 | 52 | 1196 | 0.001196 |

`spikes = round(n × rate × window_s)`. Every record carries `gate_snn` whose `decision` matches the safety gate; populations that declare rate+spikes meet the same ±1 budget against `decision_window_s`. `routing.third_factor` has modulator (NA / ACh / DA / 5-HT / adenosine), `tau_e_s`/`tau_e_ms` pair, and eligibility. Excerpt same-neuron gap ≥ 1000 µs; spike trains same-channel refractory ≥ 0.8 ms. Non-271 excerpts are kernelized and independent of `spike_events` times (overlap < 0.8).

## Local checks (staging, not raw)

See generator stdout: `check_jsonl` FactoryStaging, `validate_run.check_line`, `dumps_exact_json`, `raster_status`, `verify_batch_for_frontier(strict=True)`, `spike_probe.py --strict`, tick sums, refractory, Jaccard.

Never `training_ready`. Never `sim_or_real=real`. Never wrote `outputs/raw/`.

## Residual weaknesses (honest)

1. Only **one** labeled independent LIF (271). The other four excerpts are independent of `spike_events` times but are not declared population sims.
2. Wrong-ACCEPT still absent (guard).
3. Tick-6 sidecar bind is standing machinery (r14+), not a new class.
4. Five domain slugs leave the prompt's 8-item pool; a later round that must stay inside the pool will have to rotate sit-outs instead.
5. 274 and 275 are both already-legal ACCEPTs; a later round could pair one ACCEPT with a world charge that does not go negative.

## Next densification target

Labeled LIF on a second record, or an ISI histogram sidecar. Remaining unused wrong-MODIFY subclasses include **wrong-string (live vs idle parallel bank)**. Wrong-ACCEPT remains structurally absent until a prompt amendment.

Novel coverage: 17.0%
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
        BATCH_PATH, "batch-r51.jsonl", staging=FactoryStaging(enabled=True)
    )
    report.append(("check_jsonl FactoryStaging", errors, warnings, kinds, nrec))
    line_errs = []
    for i, rec in enumerate(records, 1):
        errs, kind = check_line(rec, f"batch-r51.jsonl:{i}", factory_staging=True)
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
    records = [record_271(), record_272(), record_273(), record_274(), record_275()]
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
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
