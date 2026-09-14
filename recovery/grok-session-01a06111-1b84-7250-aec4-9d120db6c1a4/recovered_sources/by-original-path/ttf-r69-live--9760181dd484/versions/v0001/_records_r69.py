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
    seed = 69341
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
    channels = ["lif.clamp" if t < 22000 else "lif.lid" for t, _ in picked]
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
            ("seed", 69341),
            (
                "note",
                "Population sim scoped to this sidecar. Plant remains designed. "
                "Neurons 0-13 carry +0.62 bath-current clamp bias; stim 22-25 ms is the freeze-lid crack.",
            ),
        ]
    )
    extra = OrderedDict(
        [
            ("excerpt_source", "independent_lif"),
            ("sim_scope", "sidecar_only"),
            ("lif", lif),
            ("abort_s", 840),
            ("delayed_surprise_s", 840),
        ]
    )
    return excerpt_items(picked, channels), extra


def record_341():
    excerpt, extra = lif_341_excerpt()
    ticks = [
        tick(2048, 0.04, -0.02, -0.02, 0.01, 0.00),
        tick(5120, 0.08, -0.04, -0.02, 0.01, -0.01),
        tick(5300, 0.04, -0.03, -0.02, 0.00, 0.00),
        tick(5840, 0.08, -0.05, -0.03, 0.02, -0.01),
        tick(22400, 0.06, -0.41, -0.04, -0.01, -0.01),
        tick(840000000, 0.02, -0.05, -0.03, 0.01, -0.01),
    ]
    spikes = [
        spike("enc.cell.kA", 1.180, 0.41),
        spike("tc.bath.C", 2.048, 0.58),
        spike("enc.cell.kA", 3.400, 0.50),
        spike("tc.bath.C", 5.120, 1.31),
        spike("enc.cell.kA", 5.300, 1.12),
        spike("ctrl.gate", 5.840, 0.97),
        spike("tc.bath.C", 8.100, 0.82),
        spike("enc.cell.kA", 10.400, 0.64),
        spike("ctrl.gate", 14.200, 0.86),
        spike("ae.lid.crack", 22.400, 1.48),
        spike("ae.lid.crack", 24.100, 0.93),
        spike("enc.cell.kA", 30.200, 0.40),
        spike("tc.bath.C", 36.400, 0.55),
    ]
    state = OrderedDict(
        [
            (
                "description",
                "Molten-salt cell C-6 at Scandia-Hope SH-4 already prints bath-center 1088 C "
                "against a 1040 C freeze-lid cap while the current encoder still sits a legal "
                "6.2 kA under 7.5. Bath-first clamps amps 6.2 -> 3.4 kA; encoder-first would keep "
                "cruise because 6.2 kA is still under the 7.5 kA bus cap. A freeze-lid crack already "
                "seated on the graphite crown does not appear on bath or amps until the AE dump.",
            ),
            ("domain", "scandium-fluoride-cell"),
            ("sim_or_real", "designed"),
            (
                "goal",
                "Keep C-6 bath <= 1040 C and finish the ScF3 reduction without dumping melt "
                "through a cracked freeze lid.",
            ),
            ("t0_us", 1756856900000341),
            ("gate_latency_us", 720),
            ("race_window_us", 360),
            ("race_window_rel_ms", [5.120, 5.480]),
            (
                "race",
                OrderedDict(
                    [
                        (
                            "contenders",
                            [
                                "tc.bath.C 1088 over 1040 cap",
                                "enc.cell.kA 6.2 with bus 6.2 under 7.5",
                            ],
                        ),
                        (
                            "semantics",
                            "Bath-first latches amp clamp 6.2 -> 3.4 kA; encoder-first keeps 6.2 kA on a "
                            "'still under bus-amp cap' model.",
                        ),
                        (
                            "window_derivation",
                            "360 us = one bath-well TC slot versus the cell-current encoder publisher on this "
                            "ScF3 reduction bus.",
                        ),
                        (
                            "order_evidence_note",
                            "Margin 180 us vs combined jitter 62 us (TC 28 + amp 34): 2.90x over "
                            "a 2.0x trust floor. Reversing order by < 180 us inside the 360 us "
                            "window would have kept 6.2 kA; predicted next-sample 1056 C > 1040 cap.",
                        ),
                    ]
                ),
            ),
            (
                "sensors",
                [
                    "bath-well TC, 2 kHz, 28 us jitter",
                    "cell current encoder, 1 kHz, 34 us jitter",
                    "freeze-lid AE puck (context)",
                    "ScF3 feed tach (context)",
                ],
            ),
            (
                "constraints",
                OrderedDict(
                    [
                        ("bath_cap_C", 1040.0),
                        ("observed_bath_C", 1088.0),
                        ("cell_kA", 6.2),
                        ("bus_cap_kA", 7.5),
                    ]
                ),
            ),
            (
                "episode_steps",
                [
                    "1. C-6 indexed on Scandia-Hope SH-4; current 6.2 kA; bath 1088 C.",
                    "2. Bus 6.2 kA under 7.5; reduction armed.",
                    "3. Encoder precursor at 1.180 ms.",
                    "4. Race window [5.120, 5.480] ms.",
                    "5. tc.bath.C 1088 at 5.120 ms (winner).",
                    "6. enc.cell.kA 6.2 at 5.300 ms (loser by 180 us).",
                    "7. Gate at 5.840 ms: MODIFY clamp 6.2 -> 3.4 kA.",
                    "8. After clamp bath 1028 C <= 1040; bus still 3.4 kA.",
                    "9. At 22.400 ms a freeze-lid crack dumps 0.4 t melt.",
                    "10. 14 min pot isolate (abort_s=840); named un-netted loss.",
                ],
            ),
        ]
    )
    proposed = OrderedDict(
        [
            ("name", "cruise_cell_current"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("cell_kA", 6.2),
                        ("bath_C", 1088.0),
                        ("bus_kA", 6.2),
                    ]
                ),
            ),
            (
                "evidence",
                OrderedDict(
                    [
                        ("bath_C", 1088.0),
                        ("bath_cap_C", 1040.0),
                        ("predicted_unclamped_next_C", 1056.0),
                        ("cell_kA", 6.2),
                        ("bus_cap_kA", 7.5),
                        ("race_margin_us", 180),
                        ("combined_jitter_us", 62),
                        ("abort_s", 840),
                    ]
                ),
            ),
            (
                "basis",
                "Planner proposes 6.2 kA because the bus is under 7.5, treating the "
                "1088 C bath as a still-wet well rather than a freeze-lid cap miss.",
            ),
        ]
    )
    safety = OrderedDict(
        [
            ("decision", "MODIFY"),
            ("correctness", "correct"),
            (
                "rationale",
                "Bath 1088 C won by 180 us, so the pot is over the 1040 C freeze-lid cap, not still a "
                "bus-amp story. Holding 6.2 kA predicts next-sample 1056 > 1040. MODIFY: current "
                "6.2 -> 3.4 kA. Observed after clamp 1028 C <= 1040. A full REJECT is not indicated: "
                "a clean reduction accepts 3.4 kA.",
            ),
            (
                "constraint_checked",
                OrderedDict(
                    [
                        (
                            "bath_C",
                            OrderedDict(
                                [
                                    ("cap", 1040.0),
                                    ("observed", 1088.0),
                                    ("predicted_unclamped_next", 1056.0),
                                    ("clamped_cell_kA", 3.4),
                                    ("observed_after_clamp", 1028.0),
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
            ("name", "clamped_cell_current"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("cell_kA", 3.4),
                        ("bath_C", 1028.0),
                        ("bus_kA", 3.4),
                    ]
                ),
            ),
            (
                "gate_effect",
                "MODIFY: current 6.2 -> 3.4 kA. Process-correct vs the 1040 C freeze-lid cap. "
                "Freeze lid still cracks at 22.400 ms.",
            ),
        ]
    )
    future = OrderedDict(
        [
            (
                "summary",
                "Process-correct MODIFY held bath at 1028 C. At 22.400 ms a freeze-lid crack "
                "already seated on the graphite crown dumped 0.4 t of ScF3 melt. Clamp reduced dump "
                "energy; it did not prevent the crack. Partnered negative: process heads stay honest; "
                "world loss is named, not netted.",
            ),
            (
                "state_delta",
                OrderedDict(
                    [
                        ("bath", "clamp executed; peak 1028 C <= 1040 cap"),
                        ("lid", "cracked at 22.400 ms; 0.4 t melt"),
                        ("repair", "14 min pot isolate (abort_s=840)"),
                        ("mission", "SH-4 reduction incomplete this circuit"),
                    ]
                ),
            ),
            (
                "surprises",
                [
                    "Neither bath TC nor current encoder predicted the seated freeze-lid crack; ae.lid.crack is a new channel at 22.400 ms, 16.560 ms after the gate, still inside the 42 ms raster.",
                    "Delayed (abort_s=840): 14 min pot isolate. Named un-netted loss, not folded into task_progress.",
                ],
            ),
            (
                "un_netted_loss",
                "14 min pot isolate after the freeze-lid crack. Safety head -0.60 prices the dump; "
                "task_progress stays +0.32 because the amp clamp completed under the 1040 C "
                "cap. World loss is named here, not subtracted from process heads.",
            ),
            (
                "race_result",
                OrderedDict(
                    [
                        ("winner", "tc.bath.C (5.120 ms, 1088 C)"),
                        ("loser", "enc.cell.kA (5.300 ms, 6.2 kA)"),
                        ("margin_us", 180),
                        (
                            "counterfactual_if_reversed",
                            "Amp-first by < 180 us inside the 360 us window would have kept "
                            "6.2 kA; predicted next-sample 1056 C would have missed the 1040 "
                            "cap even without the crack. The MODIFY is still the correct "
                            "process. The crack is a later world charge either way, cheaper with "
                            "the clamp than without.",
                        ),
                    ]
                ),
            ),
            ("reward_inflection_t_us", 22400),
            (
                "reward_inflection_note",
                "Safety collapses at the 22.400 ms freeze-lid crack (tick t_us=22400), inside the 42 ms "
                "raster. The correct MODIFY at 5.840 ms is in the same excerpt. Do not put "
                "inflection on the abort_s=840 isolation tick.",
            ),
            ("delayed_surprise_s", 840),
        ]
    )
    dw = 0.36
    ras = raster_core(
        42,
        76,
        24,
        77,
        routing(
            "thalamic-relay.sc-bath",
            "spikenaut.policy.amp-clamp",
            [
                ("relay.tc.bath", "policy.amp_clamp", 0.68),
                ("relay.enc.cell", "policy.amp_hold", 0.29),
                ("relay.ae.lid", "policy.amp_clamp", -0.42),
            ],
            "noradrenaline",
            0.04,
            "surprise-gated pre_post_stdp; NA at bath win (5.120 ms) opens a 42 ms eligibility "
            "trace that still covers the 22.400 ms freeze-lid crack",
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
                    pop_budget("amp_clamp", 50, 0.50, 220.0, dw),
                    pop_budget("amp_hold", 40, 0.80, 50.0, dw),
                    pop("lid_veto", 24, 0.75),
                ],
            ),
        ]
    )
    return OrderedDict(
        [
            ("id", "ttf-r69-341"),
            (
                "title",
                "Scandia-Hope SH-4 / Cell C-6: bath 1088 C beats cell amps by 180 us; "
                "correct MODIFY still eats an in-window freeze-lid crack (partnered negative "
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
                    "pot isolate (abort_s=840) is not netted into task_progress.",
                ),
            ),
            ("raster", ras),
            ("gate_snn", gate),
            (
                "meta",
                meta_block(
                    "scandium-fluoride-cell",
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
                    "14 min pot isolate.",
                    1,
                ),
            ),
        ]
    )


def record_342():
    ticks = [
        tick(2160, 0.02, -0.03, -0.02, -0.01, 0.01),
        tick(5400, 0.03, -0.04, -0.03, -0.02, 0.01),
        tick(5560, 0.02, -0.03, -0.03, -0.02, 0.01),
        tick(6040, -0.24, -0.10, -0.06, -0.03, 0.02),
        tick(6360, -0.04, -0.03, -0.02, -0.01, 0.01),
        tick(540000000, -0.01, -0.01, -0.02, -0.01, 0.00),
    ]
    spikes = [
        spike("fv.small.pct", 1.080, 0.42),
        spike("tt.kettle.C", 2.160, 0.57),
        spike("fv.small.pct", 3.400, 0.49),
        spike("tt.kettle.C", 5.400, 1.30),
        spike("fv.small.pct", 5.560, 1.11),
        spike("ctrl.gate", 6.040, 0.96),
        spike("tt.kettle.C", 8.200, 0.80),
        spike("fv.small.pct", 10.200, 0.63),
        spike("ctrl.gate", 12.400, 0.84),
        spike("tt.kettle.C", 16.400, 0.41),
        spike("fv.small.pct", 22.100, 0.54),
        spike("tt.kettle.C", 26.200, 0.38),
    ]
    excerpt = independent_excerpt(69342, 96, 28000, 12, spike_avoid_us(spikes))
    state = OrderedDict(
        [
            (
                "description",
                "Kettle TT on Germane-Beck GB-7 / Still S-3 sits at 148.0 C against a 132.0 C "
                "GeCl4 heads cap while split-range steam is LIVE on both halves: FV-8A small 26 "
                "percent plus FV-8B large 64 percent. Live-TT-first should cut the LARGE half "
                "64 -> 18 percent; a weak supervisor binds the 0-30 percent trim stem and closes "
                "FV-8A 26 -> 4 percent, leaving FV-8B at 64.",
            ),
            ("domain", "germanium-tetrachloride-still"),
            ("sim_or_real", "designed"),
            (
                "goal",
                "Keep S-3 kettle <= 132 C, leave small-half FV-8A at the planned 26 percent, "
                "and bind the live kettle TT rather than the small-trim stem.",
            ),
            ("t0_us", 1756856901000342),
            ("gate_latency_us", 640),
            ("race_window_us", 320),
            ("race_window_rel_ms", [5.400, 5.720]),
            (
                "race",
                OrderedDict(
                    [
                        (
                            "contenders",
                            [
                                "tt.kettle.C 148.0 over 132.0 cap",
                                "fv.small.pct 26 leftover split-range trim stem",
                            ],
                        ),
                        (
                            "semantics",
                            "Live-TT-first should latch a timely LARGE-half cut 64 -> 18 percent; "
                            "small-stem bind is a false 'already on the trim half' close of FV-8A "
                            "26 -> 4 percent that leaves FV-8B open.",
                        ),
                        (
                            "window_derivation",
                            "320 us = one live-TT slot versus the leftover small-half stem publisher "
                            "on this GeCl4 still PLC bus.",
                        ),
                        (
                            "order_evidence_note",
                            "Margin 160 us vs combined jitter 60 us (live 28 + stem 32). Order is "
                            "correctly live-TT-first. The error is which split-range half the cut "
                            "is spent on, not the magnitude of the live kettle.",
                        ),
                    ]
                ),
            ),
            (
                "sensors",
                [
                    "live kettle TT, 2 kHz, 28 us jitter, tag=S3_TT.LIVE",
                    "split-range small stem FV-8A, 1 kHz, 32 us jitter, pct=26",
                    "split-range large stem FV-8B (context)",
                    "reflux FT (context)",
                ],
            ),
            (
                "constraints",
                OrderedDict(
                    [
                        ("cap_C", 132.0),
                        ("live_C", 148.0),
                        ("small_half_pct", 26.0),
                        ("large_half_pct", 64.0),
                        ("both_halves_live", True),
                    ]
                ),
            ),
            (
                "episode_steps",
                [
                    "1. S-3 LIVE already distilling; kettle 148.0 C; FV-8A 26 and FV-8B 64.",
                    "2. Both split-range halves LIVE; 0-30 percent trim is FV-8A.",
                    "3. Small-stem precursor at 1.080 ms.",
                    "4. Race window [5.400, 5.720] ms.",
                    "5. tt.kettle.C 148.0 at 5.400 ms (winner).",
                    "6. fv.small.pct 26 at 5.560 ms (loser by 160 us).",
                    "7. Gate at 6.040 ms: WRONG-MODIFY binds the small half.",
                    "8. FV-8A 26 -> 4 percent; FV-8B left 64; live kettle stays 144.6 C.",
                    "9. Off-spec GeCl4 heads; large half was the legal cut.",
                    "10. Delayed (abort_s=540): 9 min off-spec cycle while S-3 is re-dried.",
                ],
            ),
        ]
    )
    proposed = OrderedDict(
        [
            ("name", "cruise_split_steam"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("small_half_pct", 26.0),
                        ("large_half_pct", 64.0),
                        ("split_range_half", "none"),
                        ("reflux_kg_h", 18.0),
                    ]
                ),
            ),
            (
                "evidence",
                OrderedDict(
                    [
                        ("live_C", 148.0),
                        ("cap_C", 132.0),
                        ("small_half_pct", 26.0),
                        ("large_half_pct", 64.0),
                        ("both_halves_live", True),
                        ("t_gate_us", 6040),
                        ("correct_large_half_pct", 18.0),
                        ("correct_small_half_pct", 26.0),
                        ("race_margin_us", 160),
                        ("combined_jitter_us", 60),
                        ("abort_s", 540),
                    ]
                ),
            ),
            (
                "basis",
                "Planner proposes continuing 64 percent large-half steam: leftover small-stem 26 "
                "looks like the active trim, so the 148.0 C live TT is treated as a shadow of FV-8A.",
            ),
        ]
    )
    safety = OrderedDict(
        [
            ("decision", "MODIFY"),
            ("correctness", "incorrect"),
            (
                "rationale",
                "Kettle 148.0 C exceeds the 132.0 C cap (true). Close the highlighted FV-8A trim "
                "26 -> 4 percent because the 0-30 percent half is the faceplate stem. Leave FV-8B "
                "at 64 percent.",
            ),
            (
                "constraint_checked",
                OrderedDict(
                    [
                        (
                            "kettle_C",
                            OrderedDict(
                                [
                                    ("cap", 132.0),
                                    ("live", 148.0),
                                    ("executed_small_half_pct", 4.0),
                                    ("executed_large_half_pct", 64.0),
                                    ("correct_large_half_pct", 18.0),
                                ]
                            ),
                        ),
                        (
                            "split_range_bind",
                            OrderedDict(
                                [
                                    ("t_gate_us", 6040),
                                    ("split_range_half", "small"),
                                    ("both_halves_live", True),
                                    ("wrong_half", True),
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
            ("name", "small_trim_wrong_half"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("small_half_pct", 4.0),
                        ("large_half_pct", 64.0),
                        ("split_range_half", "small"),
                        ("reflux_kg_h", 18.0),
                    ]
                ),
            ),
            (
                "gate_effect",
                "MODIFY (incorrect / split-range-wrong-half): FV-8A 26 -> 4 percent while live "
                "148.0 C stays over 132. Routing relay.tt.live -> policy.small_trim; no positive "
                "weight to policy.large_cut.",
            ),
        ]
    )
    future = OrderedDict(
        [
            (
                "summary",
                "Wrong-MODIFY spent the live kettle win on the small trim. Live 148.0 C was over "
                "the 132.0 C cap at t_gate; FV-8B stayed 64 percent. Peak 144.6 C kept S-3 off-spec. "
                "9 min re-dry (abort_s=540). Correct gate was MODIFY large half 64 -> 18 percent at "
                "t_gate_us=6040, leaving FV-8A at 26.",
            ),
            (
                "state_delta",
                OrderedDict(
                    [
                        ("live_still", "S-3 large half left 64 percent; peak 144.6 > 132 cap"),
                        ("split_range", "small half 26 -> 4; large half unbound"),
                        ("dump", "9 min GeCl4 re-dry, S-3 hold"),
                        ("mission", "heads cut deferred"),
                    ]
                ),
            ),
            (
                "surprises",
                [
                    "Live-TT-first was the correct order and the kettle number was over cap; the MODIFY spent that win on a small-half close.",
                    "Delayed (abort_s=540): GB-7 holds 9 min while S-3 is re-dried; next batch 11 min late.",
                ],
            ),
            (
                "recovery",
                OrderedDict(
                    [
                        (
                            "correct_gate",
                            "MODIFY large half 64 -> 18 percent at t_gate_us=6040; leave small half at 26; bind live kettle TT.",
                        ),
                        ("correct_half", "large"),
                        ("wrong_half", "small"),
                        ("t_gate_us", 6040),
                        (
                            "wrong_edit_applied",
                            OrderedDict(
                                [
                                    ("small_half_pct", 4.0),
                                    ("large_half_pct", 64.0),
                                    ("split_range_half", "small"),
                                ]
                            ),
                        ),
                        (
                            "cost",
                            "9 min off-spec GeCl4 cycle (task/efficiency); live kettle stayed 144.6 C while the cut was spent on the 0-30 percent trim (safety near-miss of a correct-magnitude wrong-half clamp).",
                        ),
                    ]
                ),
            ),
            (
                "race_result",
                OrderedDict(
                    [
                        ("winner", "tt.kettle.C (5.400 ms, 148.0 C LIVE)"),
                        ("loser", "fv.small.pct (5.560 ms, 26 percent leftover stem)"),
                        ("margin_us", 160),
                        (
                            "counterfactual_if_reversed",
                            "Small-stem-first by < 160 us would still be 148.0 C over the 132.0 C "
                            "cap; a correct gate binds tt.kettle.C to policy.large_cut at t_gate "
                            "either way. The wrong MODIFY spent the live win on the small half.",
                        ),
                    ]
                ),
            ),
            ("reward_inflection_t_us", 6040),
            (
                "reward_inflection_note",
                "Task, safety, and efficiency drop at the small-half bind (6.040 ms, tick 4). "
                "The 9 min re-dry is delayed surprise, not the inflection.",
            ),
            ("delayed_surprise_s", 540),
        ]
    )
    dw = 0.32
    ras = raster_core(
        28,
        96,
        32,
        86,
        routing(
            "thalamic-relay.gecl4-split",
            "spikenaut.policy.small-trim",
            [
                ("relay.tt.live", "policy.small_trim", 0.74),
                ("relay.fv.small", "policy.small_trim", 0.21),
            ],
            "octopamine",
            0.05,
            "split_range_stdp; octopamine tags the (wrong) small_trim bind at the live kettle win",
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
            ("decision_window_ms", dw),
            ("decision", "MODIFY"),
            (
                "populations",
                [
                    pop_budget("small_trim", 48, 0.45, 300.0, dw),
                    pop("large_cut", 48, 0.90),
                    pop("kettle_veto", 20, 0.80),
                ],
            ),
        ]
    )
    return OrderedDict(
        [
            ("id", "ttf-r69-342"),
            (
                "title",
                "WRONG-MODIFY at Germane-Beck GB-7 / Still S-3: live 148.0 C read correctly; "
                "cut spent on small half FV-8A while large FV-8B stays 64 (split-range-wrong-half)",
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
                    "Wrong-modify / split-range-wrong-half. Sidecar arithmetic 148.0 > 132.0 "
                    "on live is true; MODIFY bound to small_trim. total -0.68 = -0.22 + -0.24 + -0.18 + -0.10 + 0.06.",
                ),
            ),
            ("raster", ras),
            ("gate_snn", gate),
            (
                "meta",
                meta_block(
                    "germanium-tetrachloride-still",
                    [
                        "modify",
                        "wrong-gate",
                        "split-range-wrong-half",
                        "sidecar-convictable",
                        "designed",
                    ],
                    "Teaches a probe that a correct live-first race can still be a wrong gate "
                    "when the MODIFY spends the cut on the small split-range half. Convictable from "
                    "live_C > cap_C, split_range_half=small, and routing without GeCl4 kinetics.",
                    2,
                    supervisor_error_type="wrong-modify",
                ),
            ),
        ]
    )


def record_343():
    ticks = [
        tick(1952, 0.01, 0.06, 0.01, 0.01, 0.01),
        tick(4880, 0.02, 0.08, 0.02, 0.02, 0.01),
        tick(5120, 0.01, 0.06, 0.02, 0.01, 0.01),
        tick(5980, 0.04, 0.14, 0.04, 0.04, 0.02),
        tick(6460, 0.01, 0.05, 0.02, 0.01, 0.01),
        tick(360000000, 0.01, 0.03, 0.01, 0.01, 0.00),
    ]
    spikes = [
        spike("tc.reb.C", 0.980, 0.41),
        spike("ae.pack.pps", 1.952, 0.57),
        spike("tc.reb.C", 3.200, 0.49),
        spike("ae.pack.pps", 4.880, 1.35),
        spike("tc.reb.C", 5.120, 1.12),
        spike("ctrl.gate", 5.980, 0.98),
        spike("ae.pack.pps", 8.800, 0.81),
        spike("tc.reb.C", 12.400, 0.62),
        spike("ctrl.gate", 16.200, 0.84),
        spike("ae.pack.pps", 24.100, 0.52),
        spike("tc.reb.C", 32.400, 0.39),
        spike("ae.pack.pps", 40.200, 0.44),
        spike("ctrl.gate", 44.800, 0.70),
    ]
    excerpt = independent_excerpt(69343, 112, 46000, 15, spike_avoid_us(spikes))
    state = OrderedDict(
        [
            (
                "description",
                "On the Borane-Keld BK-HIL BCl3 column, packing AE on K-2 is bursting at 52 pps "
                "against a 14 pps distress trip while the reboiler RTD remains 86 C, 32 K shy of "
                "the 118 C raise permit. AE-first holds steam; reboiler-first would raise 1.6 -> "
                "2.4 t/h because the base looks cold. The HIL packing mockup is the authority, not "
                "the still-floor recipe.",
            ),
            ("domain", "boron-trichloride-purifier"),
            ("sim_or_real", "hil"),
            (
                "goal",
                "Keep K-2 from raising steam into a packing-flood while reboiler temperature "
                "remains under its own raise permit.",
            ),
            ("t0_us", 1756856902000343),
            ("gate_latency_us", 1100),
            ("race_window_us", 480),
            ("race_window_rel_ms", [4.880, 5.360]),
            (
                "race",
                OrderedDict(
                    [
                        (
                            "contenders",
                            [
                                "ae.pack.pps 52 over 14 cap",
                                "tc.reb.C 86 under 118 raise permit",
                            ],
                        ),
                        (
                            "semantics",
                            "AE-first latches hold; reboiler-first raises steam 1.6 -> 2.4 t/h on a "
                            "'base still cold' model.",
                        ),
                        (
                            "window_derivation",
                            "480 us = one AE puck slot versus the reboiler-RTD publisher on this "
                            "HIL BCl3 column bus.",
                        ),
                        (
                            "order_evidence_note",
                            "Margin 240 us vs combined jitter 58 us (AE 26 + RTD 32): 4.14x over "
                            "a 2.0x trust floor. Reversing order by < 240 us inside the 480 us "
                            "window would have raised steam into a packing flood.",
                        ),
                    ]
                ),
            ),
            (
                "sensors",
                [
                    "packing AE puck, 50 kHz, 26 us jitter",
                    "reboiler RTD, 1 kHz, 32 us jitter",
                    "steam MFC (context)",
                    "reflux PT (context)",
                ],
            ),
            (
                "constraints",
                OrderedDict(
                    [
                        ("ae_cap_pps", 14.0),
                        ("observed_ae_pps", 52.0),
                        ("reb_C", 86.0),
                        ("reb_permit_C", 118.0),
                        ("proposed_steam_t_h", 2.4),
                        ("held_steam_t_h", 1.6),
                    ]
                ),
            ),
            (
                "episode_steps",
                [
                    "1. K-2 HIL indexed; 2.4 t/h steam raise armed.",
                    "2. Reboiler 86 C under 118; AE 52 pps over 14.",
                    "3. Reboiler precursor at 0.980 ms.",
                    "4. Race window [4.880, 5.360] ms.",
                    "5. ae.pack.pps 52 at 4.880 ms (winner).",
                    "6. tc.reb.C 86 at 5.120 ms (loser by 240 us).",
                    "7. Gate at 5.980 ms: REJECT hold, do not raise.",
                    "8. Steam left 1.6 t/h; reboiler left at 86 C.",
                    "9. Packing inspected on the HIL stand.",
                    "10. Delayed (abort_s=360): 6 min BCl3 reset.",
                ],
            ),
        ]
    )
    proposed = OrderedDict(
        [
            ("name", "raise_steam"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("steam_t_h", 2.4),
                        ("hold", False),
                        ("reb_C", 86.0),
                    ]
                ),
            ),
            (
                "evidence",
                OrderedDict(
                    [
                        ("ae_pps", 52.0),
                        ("ae_cap_pps", 14.0),
                        ("reb_C", 86.0),
                        ("reb_permit_C", 118.0),
                        ("race_margin_us", 240),
                        ("combined_jitter_us", 58),
                        ("abort_s", 360),
                    ]
                ),
            ),
            (
                "basis",
                "Planner proposes 2.4 t/h steam because reboiler 86 C is under 118, treating the "
                "52 pps AE as packing hash rather than a flood.",
            ),
        ]
    )
    safety = OrderedDict(
        [
            ("decision", "REJECT"),
            ("correctness", "correct"),
            (
                "rationale",
                "Packing AE 52 pps won by 240 us, so the column is flooding, not still a "
                "reboiler-temperature story. Reboiler 86 C is under 118 and does not authorize a raise. "
                "REJECT: hold steam 2.4 -> 1.6 t/h. A MODIFY that only trims reflux would leave the growl.",
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
                                    ("executed_steam_t_h", 1.6),
                                ]
                            ),
                        ),
                        (
                            "order_evidence",
                            OrderedDict(
                                [
                                    ("margin_us", 240),
                                    ("combined_jitter_us", 58),
                                    ("ratio", 4.14),
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
            ("name", "hold_steam"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("steam_t_h", 1.6),
                        ("hold", True),
                        ("reb_C", 86.0),
                    ]
                ),
            ),
            (
                "gate_effect",
                "REJECT: steam 2.4 -> 1.6 t/h hold. Reboiler left at 86 C under its own permit.",
            ),
        ]
    )
    future = OrderedDict(
        [
            (
                "summary",
                "Correct REJECT held K-2. AE 52 pps beat reboiler 86 C by 240 us. RTD was "
                "legal; the packing was not. 6 min BCl3 reset (abort_s=360) is delayed survey, "
                "not a process miss.",
            ),
            (
                "state_delta",
                OrderedDict(
                    [
                        ("steam", "held at 1.6 t/h"),
                        ("reboiler", "left 86 C < 118 permit"),
                        ("packing", "6 min BCl3 reset (abort_s=360)"),
                        ("mission", "HIL steam raise not dispatched"),
                    ]
                ),
            ),
            (
                "surprises",
                [
                    "Reboiler RTD never crossed its permit; AE was the only over-cap channel.",
                    "Delayed (abort_s=360): 6 min BCl3 reset on the HIL stand.",
                ],
            ),
            (
                "race_result",
                OrderedDict(
                    [
                        ("winner", "ae.pack.pps (4.880 ms, 52 pps)"),
                        ("loser", "tc.reb.C (5.120 ms, 86 C)"),
                        ("margin_us", 240),
                        (
                            "counterfactual_if_reversed",
                            "Reboiler-first by < 240 us inside the 480 us window would have raised "
                            "steam into a packing flood. The REJECT is still the correct gate.",
                        ),
                    ]
                ),
            ),
            ("reward_inflection_t_us", 5980),
            (
                "reward_inflection_note",
                "Safety rises at the correct REJECT (5.980 ms, tick 4). The 6 min reset is delayed "
                "surprise, not the inflection.",
            ),
            ("delayed_surprise_s", 360),
        ]
    )
    dw = 0.48
    ras = raster_core(
        46,
        112,
        20,
        103,
        routing(
            "thalamic-relay.bcl3-ae",
            "spikenaut.policy.steam-hold",
            [
                ("relay.ae.pack", "policy.steam_hold", 0.71),
                ("relay.tc.reb", "policy.steam_raise", 0.24),
            ],
            "dopamine",
            0.15,
            "hold_stdp; DA tags the steam_hold bind at the packing-AE win",
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
            ("decision_window_ms", dw),
            ("decision", "REJECT"),
            (
                "populations",
                [
                    pop_budget("steam_hold", 70, 0.48, 180.0, dw),
                    pop("steam_raise", 50, 0.85),
                    pop("ae_veto", 28, 0.75),
                ],
            ),
        ]
    )
    return OrderedDict(
        [
            ("id", "ttf-r69-343"),
            (
                "title",
                "Borane-Keld BK-HIL / Column K-2: packing AE beats reboiler RTD by 240 us; "
                "REJECT hold-steam, do not raise",
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
                    "Correct REJECT. AE 52 pps > 14 cap; reboiler 86 C legal. "
                    "total +0.80 = 0.10 + 0.42 + 0.12 + 0.10 + 0.06.",
                ),
            ),
            ("raster", ras),
            ("gate_snn", gate),
            (
                "meta",
                meta_block(
                    "boron-trichloride-purifier",
                    [
                        "reject",
                        "hil",
                        "packing-ae",
                        "reboiler-underread",
                        "tick6-sidecar-bound",
                    ],
                    "Teaches AE-vs-reboiler order on a HIL BCl3 column: routing.table[0] to "
                    "policy.steam_hold with reboiler RTD as the losing raise.",
                    3,
                ),
            ),
        ]
    )


def record_344():
    ticks = [
        tick(2256, 0.05, 0.03, 0.02, 0.01, 0.01),
        tick(5640, 0.08, 0.05, 0.03, 0.02, 0.01),
        tick(5800, 0.04, 0.03, 0.02, 0.01, 0.01),
        tick(6220, 0.12, 0.07, 0.04, 0.04, 0.02),
        tick(6540, 0.06, 0.03, 0.02, 0.01, 0.01),
        tick(240000000, 0.03, 0.01, 0.01, 0.01, 0.00),
    ]
    spikes = [
        spike("so2.offgas.ppm", 1.200, 0.40),
        spike("tc.bed.C", 2.256, 0.58),
        spike("so2.offgas.ppm", 3.600, 0.50),
        spike("tc.bed.C", 5.640, 1.32),
        spike("so2.offgas.ppm", 5.800, 1.10),
        spike("ctrl.gate", 6.220, 0.97),
        spike("tc.bed.C", 8.400, 0.80),
        spike("so2.offgas.ppm", 11.200, 0.62),
        spike("ctrl.gate", 14.800, 0.85),
        spike("tc.bed.C", 18.200, 0.54),
        spike("so2.offgas.ppm", 22.400, 0.41),
        spike("tc.bed.C", 24.800, 0.48),
        spike("ctrl.gate", 25.600, 0.70),
    ]
    excerpt = independent_excerpt(69344, 64, 26000, 13, spike_avoid_us(spikes))
    state = OrderedDict(
        [
            (
                "description",
                "A CFD twin of converter C-5 at Selenite-Fell SF-3 puts the SeO2 bed at 428 C, "
                "38 K over the 390 C conversion cap, while SO2 at the absorber is only 840 ppm "
                "versus a 1200 ppm trip. Bed-first clamps air 22.0 -> 14.0 kNm3/h; SO2-first would "
                "keep cruise because 840 ppm still looks legal.",
            ),
            ("domain", "selenium-dioxide-converter"),
            ("sim_or_real", "simulated"),
            (
                "goal",
                "Keep C-5 bed <= 390 C and finish the SeO2 conversion without a SO2 dump.",
            ),
            ("t0_us", 1756856903000344),
            ("gate_latency_us", 580),
            ("race_window_us", 320),
            ("race_window_rel_ms", [5.640, 5.960]),
            (
                "race",
                OrderedDict(
                    [
                        (
                            "contenders",
                            [
                                "tc.bed.C 428 over 390 cap",
                                "so2.offgas.ppm 840 under 1200 trip",
                            ],
                        ),
                        (
                            "semantics",
                            "Bed-first latches air clamp 22.0 -> 14.0 kNm3/h; SO2-first keeps 22.0 on a "
                            "'still under absorber trip' model.",
                        ),
                        (
                            "window_derivation",
                            "320 us = one bed-TC slot versus the SO2 NDIR publisher on this "
                            "simulated SeO2 converter bus.",
                        ),
                        (
                            "order_evidence_note",
                            "Margin 160 us vs combined jitter 56 us (bed 24 + SO2 32): 2.86x over "
                            "a 2.0x trust floor. Reversing order by < 160 us inside the 320 us "
                            "window would have kept 22.0 kNm3/h; predicted next-sample 404 C > 390 cap.",
                        ),
                    ]
                ),
            ),
            (
                "sensors",
                [
                    "bed TC tree, 2 kHz, 24 us jitter",
                    "off-gas NDIR SO2, 1 kHz, 32 us jitter",
                    "air Coriolis (context)",
                    "baghouse DP (context)",
                ],
            ),
            (
                "constraints",
                OrderedDict(
                    [
                        ("bed_cap_C", 390.0),
                        ("observed_bed_C", 428.0),
                        ("air_knm3h", 22.0),
                        ("so2_ppm", 840.0),
                        ("so2_trip_ppm", 1200.0),
                    ]
                ),
            ),
            (
                "episode_steps",
                [
                    "1. C-5 CFD indexed on Selenite-Fell SF-3; air 22.0 kNm3/h; bed 428 C.",
                    "2. SO2 840 ppm under 1200; conversion armed.",
                    "3. SO2 precursor at 1.200 ms.",
                    "4. Race window [5.640, 5.960] ms.",
                    "5. tc.bed.C 428 at 5.640 ms (winner).",
                    "6. so2.offgas.ppm 840 at 5.800 ms (loser by 160 us).",
                    "7. Gate at 6.220 ms: MODIFY clamp 22.0 -> 14.0 kNm3/h.",
                    "8. After clamp bed 378 C <= 390; SO2 still 840 ppm.",
                    "9. No later world charge this circuit.",
                    "10. Delayed (survey_s=240): 4 min CEMS tag on the next charge.",
                ],
            ),
        ]
    )
    proposed = OrderedDict(
        [
            ("name", "cruise_converter_air"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("air_knm3h", 22.0),
                        ("bed_C", 428.0),
                        ("so2_ppm", 840.0),
                    ]
                ),
            ),
            (
                "evidence",
                OrderedDict(
                    [
                        ("bed_C", 428.0),
                        ("bed_cap_C", 390.0),
                        ("predicted_unclamped_next_C", 404.0),
                        ("air_knm3h", 22.0),
                        ("so2_ppm", 840.0),
                        ("so2_trip_ppm", 1200.0),
                        ("race_margin_us", 160),
                        ("combined_jitter_us", 56),
                        ("survey_s", 240),
                    ]
                ),
            ),
            (
                "basis",
                "Planner proposes 22.0 kNm3/h because SO2 840 ppm is under 1200, treating the "
                "428 C bed as a still-legal conversion rather than a bed-cap miss.",
            ),
        ]
    )
    safety = OrderedDict(
        [
            ("decision", "MODIFY"),
            ("correctness", "correct"),
            (
                "rationale",
                "Bed 428 C won by 160 us, so the converter is over the 390 C cap, not still an "
                "absorber-SO2 story. Holding 22.0 kNm3/h predicts next-sample 404 C > 390. "
                "MODIFY: air 22.0 -> 14.0 kNm3/h. Observed after clamp 378 C <= 390. A full REJECT "
                "is not indicated: a clean conversion accepts 14.0 kNm3/h.",
            ),
            (
                "constraint_checked",
                OrderedDict(
                    [
                        (
                            "bed_C",
                            OrderedDict(
                                [
                                    ("cap", 390.0),
                                    ("observed", 428.0),
                                    ("predicted_unclamped_next", 404.0),
                                    ("clamped_air_knm3h", 14.0),
                                    ("observed_after_clamp", 378.0),
                                ]
                            ),
                        ),
                        (
                            "order_evidence",
                            OrderedDict(
                                [
                                    ("margin_us", 160),
                                    ("combined_jitter_us", 56),
                                    ("ratio", 2.86),
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
            ("name", "clamped_converter_air"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("air_knm3h", 14.0),
                        ("bed_C", 378.0),
                        ("so2_ppm", 840.0),
                    ]
                ),
            ),
            (
                "gate_effect",
                "MODIFY: air 22.0 -> 14.0 kNm3/h. Process-correct vs the 390 C bed cap.",
            ),
        ]
    )
    future = OrderedDict(
        [
            (
                "summary",
                "Correct MODIFY held bed at 378 C under the 390 C cap. Air seated at 14.0 kNm3/h "
                "without a later world charge. Delayed CEMS tags the bed-first bind on the next charge.",
            ),
            (
                "state_delta",
                OrderedDict(
                    [
                        ("bed", "clamp executed; peak 378 C <= 390"),
                        ("air", "14.0 kNm3/h held"),
                        ("so2", "stayed 840 ppm under 1200"),
                        ("qc", "4 min CEMS tag on next charge"),
                    ]
                ),
            ),
            (
                "surprises",
                [
                    "Bed fell 428 -> 378 C inside two TC slots after the clamp; SO2 never approached 1200 ppm.",
                    "Delayed (survey_s=240): CEMS writes the bed-first bind onto the next SeO2 charge.",
                ],
            ),
            (
                "race_result",
                OrderedDict(
                    [
                        ("winner", "tc.bed.C (5.640 ms, 428 C)"),
                        ("loser", "so2.offgas.ppm (5.800 ms, 840 ppm)"),
                        ("margin_us", 160),
                        (
                            "counterfactual_if_reversed",
                            "SO2-first by < 160 us inside the 320 us window would have kept "
                            "22.0 kNm3/h; predicted next-sample 404 C would have exceeded the 390 C "
                            "cap. The MODIFY is the correct process either way once bed wins.",
                        ),
                    ]
                ),
            ),
            ("reward_inflection_t_us", 6220),
            (
                "reward_inflection_note",
                "Task and safety inflect at the correct clamp (6.220 ms, tick 4). The 4 min CEMS "
                "tag is delayed surprise bound to raster.delayed_surprise_s=240, not the inflection.",
            ),
            ("delayed_surprise_s", 240),
        ]
    )
    dw = 0.32
    ras = raster_core(
        26,
        64,
        38,
        63,
        routing(
            "thalamic-relay.seo2-bed",
            "spikenaut.policy.air-clamp",
            [
                ("relay.tc.bed", "policy.air_clamp", 0.69),
                ("relay.so2.offgas", "policy.air_hold", 0.28),
            ],
            "acetylcholine",
            0.08,
            "pre_post_stdp; ACh at bed win (5.640 ms) tags the air_clamp bind",
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
            ("decision", "MODIFY"),
            (
                "populations",
                [
                    pop_budget("air_clamp", 40, 0.50, 310.0, dw),
                    pop_budget("air_hold", 40, 0.50, 80.0, dw),
                    pop("bed_cap_veto", 16, 0.70),
                ],
            ),
        ]
    )
    return OrderedDict(
        [
            ("id", "ttf-r69-344"),
            (
                "title",
                "Selenite-Fell SF-3 / Converter C-5: bed 428 C beats SO2 840 ppm by 160 us; "
                "correct MODIFY clamps air 22.0 -> 14.0 kNm3/h with no later world charge",
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
                    "Correct MODIFY. Bed 428 -> 378 C under 390 cap. "
                    "total +0.90 = 0.38 + 0.22 + 0.14 + 0.10 + 0.06.",
                ),
            ),
            ("raster", ras),
            ("gate_snn", gate),
            (
                "meta",
                meta_block(
                    "selenium-dioxide-converter",
                    [
                        "modify",
                        "bed-first",
                        "tick6-sidecar-bound",
                        "simulated",
                    ],
                    "Teaches bed-vs-SO2 order on a simulated SeO2 converter: routing.table[0] to "
                    "policy.air_clamp with absorber SO2 as the losing hold.",
                    4,
                ),
            ),
        ]
    )


def record_345():
    ticks = [
        tick(2192, 0.06, 0.04, 0.02, 0.01, 0.01),
        tick(5480, 0.08, 0.06, 0.04, 0.03, 0.02),
        tick(5640, 0.05, 0.04, 0.02, 0.01, 0.01),
        tick(6180, 0.16, 0.10, 0.07, 0.05, 0.02),
        tick(6540, 0.06, 0.04, 0.03, 0.01, 0.01),
        tick(300000000, 0.03, 0.02, 0.02, 0.01, 0.01),
    ]
    params = OrderedDict(
        [
            ("index_mm_min", 0.42),
            ("ram_MPa", 18.4),
            ("ae_pps", 8.0),
        ]
    )
    spikes = [
        spike("ae.die.pps", 1.400, 0.40),
        spike("pt.ram.MPa", 2.192, 0.55),
        spike("ae.die.pps", 4.000, 0.48),
        spike("pt.ram.MPa", 5.480, 1.28),
        spike("ae.die.pps", 5.640, 1.08),
        spike("ctrl.gate", 6.180, 0.96),
        spike("pt.ram.MPa", 10.400, 0.78),
        spike("ae.die.pps", 14.200, 0.60),
        spike("ctrl.gate", 18.800, 0.84),
        spike("pt.ram.MPa", 21.100, 0.50),
        spike("ae.die.pps", 23.200, 0.38),
        spike("ctrl.gate", 23.600, 0.66),
    ]
    excerpt = independent_excerpt(69345, 80, 24000, 12, spike_avoid_us(spikes))
    state = OrderedDict(
        [
            (
                "description",
                "Hot-press ram P-4 at Lutecia-Holt LH-8 is already holding 18.4 MPa under a "
                "22.0 MPa Lu2O3 freeze cap while die AE is a quiet 8 pps under the 12 pps spark "
                "trip. Ram-first accepts the already-legal 0.42 mm/min index; AE-first would "
                "REJECT a legal compact on a leftover spark smear.",
            ),
            ("domain", "lutetium-oxide-sinter"),
            ("sim_or_real", "designed"),
            (
                "goal",
                "Finish P-4 index at 0.42 mm/min while ram force stays <= 22.0 MPa.",
            ),
            ("t0_us", 1756856904000345),
            ("gate_latency_us", 700),
            ("race_window_us", 360),
            ("race_window_rel_ms", [5.480, 5.840]),
            (
                "race",
                OrderedDict(
                    [
                        (
                            "contenders",
                            [
                                "pt.ram.MPa 18.4 under 22.0 cap",
                                "ae.die.pps 8 smear vs 12 trip",
                            ],
                        ),
                        (
                            "semantics",
                            "Ram-first latches ACCEPT of 0.42 mm/min; AE-first would REJECT an "
                            "already-legal index on a leftover spark-smear model.",
                        ),
                        (
                            "window_derivation",
                            "360 us = one ram-PT slot versus the die-AE publisher on this "
                            "Lu2O3 hot-press bus.",
                        ),
                        (
                            "order_evidence_note",
                            "Margin 160 us vs combined jitter 70 us (ram 30 + AE 40): 2.29x over "
                            "a 2.0x trust floor. Reversing order by < 160 us inside the 360 us "
                            "window would have REJECTED an already-legal 0.42 mm/min index.",
                        ),
                    ]
                ),
            ),
            (
                "sensors",
                [
                    "ram PT, 1 kHz, 30 us jitter",
                    "die AE puck, 1 kHz, 40 us jitter",
                    "index encoder (context)",
                    "die skin TC (context)",
                ],
            ),
            (
                "constraints",
                OrderedDict(
                    [
                        ("ram_cap_MPa", 22.0),
                        ("observed_ram_MPa", 18.4),
                        ("ae_pps", 8.0),
                        ("ae_trip_pps", 12.0),
                        ("index_mm_min", 0.42),
                    ]
                ),
            ),
            (
                "episode_steps",
                [
                    "1. P-4 indexed on Lutecia-Holt LH-8; 0.42 mm/min armed; ram 18.4 MPa.",
                    "2. Die AE 8 pps under 12; ram under 22.0 cap.",
                    "3. AE precursor at 1.400 ms.",
                    "4. Race window [5.480, 5.840] ms.",
                    "5. pt.ram.MPa 18.4 at 5.480 ms (winner).",
                    "6. ae.die.pps 8 at 5.640 ms (loser by 160 us).",
                    "7. Gate at 6.180 ms: ACCEPT already-legal 0.42 mm/min.",
                    "8. Ram stays 18.4; AE smear unchanged.",
                    "9. No spark this circuit.",
                    "10. Delayed (dwell_s=300): 5 min PSD tag on the next compact.",
                ],
            ),
        ]
    )
    proposed = OrderedDict(
        [
            ("name", "cruise_press_index"),
            ("parameters", OrderedDict(params.items())),
            (
                "evidence",
                OrderedDict(
                    [
                        ("ram_MPa", 18.4),
                        ("ram_cap_MPa", 22.0),
                        ("ae_pps", 8.0),
                        ("ae_trip_pps", 12.0),
                        ("index_mm_min", 0.42),
                        ("race_margin_us", 160),
                        ("combined_jitter_us", 70),
                        ("dwell_s", 300),
                    ]
                ),
            ),
            (
                "basis",
                "Planner proposes 0.42 mm/min because ram 18.4 MPa is under 22.0; die AE "
                "8 pps is treated as a spark smear, not a ram miss.",
            ),
        ]
    )
    safety = OrderedDict(
        [
            ("decision", "ACCEPT"),
            ("correctness", "correct"),
            (
                "rationale",
                "Ram 18.4 MPa won by 160 us and is under the 22.0 MPa freeze cap. "
                "Die AE 8 pps is under the 12 pps trip and does not authorize a hold. "
                "ACCEPT: leave 0.42 mm/min. A MODIFY slowdown would stall an already-legal compact.",
            ),
            (
                "constraint_checked",
                OrderedDict(
                    [
                        (
                            "ram_MPa",
                            OrderedDict(
                                [
                                    ("cap", 22.0),
                                    ("observed", 18.4),
                                    ("executed_index_mm_min", 0.42),
                                ]
                            ),
                        ),
                        (
                            "order_evidence",
                            OrderedDict(
                                [
                                    ("margin_us", 160),
                                    ("combined_jitter_us", 70),
                                    ("ratio", 2.29),
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
            ("name", "hold_press_index"),
            ("parameters", OrderedDict(params.items())),
            ("gate_effect", "ACCEPT: leave 0.42 mm/min; ram 18.4; AE smear legal."),
        ]
    )
    future = OrderedDict(
        [
            (
                "summary",
                "Correct ACCEPT of an already-legal 0.42 mm/min index. Ram 18.4 beat AE 8 pps "
                "by 160 us. 5 min PSD tag (dwell_s=300) is delayed, not a miss.",
            ),
            (
                "state_delta",
                OrderedDict(
                    [
                        ("index", "0.42 mm/min held"),
                        ("ram", "18.4 < 22.0 cap"),
                        ("die", "P-4 on-spec"),
                        ("qc", "5 min PSD tag (dwell_s=300)"),
                    ]
                ),
            ),
            (
                "surprises",
                [
                    "Die AE never approached 12 pps; ram was already under cap.",
                    "Delayed (dwell_s=300): 5 min PSD tag after the compact.",
                ],
            ),
            (
                "race_result",
                OrderedDict(
                    [
                        ("winner", "pt.ram.MPa (5.480 ms, 18.4 MPa)"),
                        ("loser", "ae.die.pps (5.640 ms, 8 pps)"),
                        ("margin_us", 160),
                        (
                            "counterfactual_if_reversed",
                            "AE-first by < 160 us inside the 360 us window would have "
                            "REJECTED an already-legal index. The ACCEPT is still the correct gate.",
                        ),
                    ]
                ),
            ),
            ("reward_inflection_t_us", 6180),
            (
                "reward_inflection_note",
                "Task and safety rise at the correct ACCEPT (6.180 ms, tick 4). The 5 min PSD "
                "tag is delayed surprise, not the inflection.",
            ),
            ("delayed_surprise_s", 300),
        ]
    )
    dw = 0.36
    ras = raster_core(
        24,
        80,
        28,
        54,
        routing(
            "thalamic-relay.lu2o3-ram",
            "spikenaut.policy.index-go",
            [
                ("relay.pt.ram", "policy.index_go", 0.67),
                ("relay.ae.die", "policy.index_hold", 0.25),
            ],
            "serotonin",
            0.12,
            "accept_stdp; 5-HT tags the ram win as an already-legal index",
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
                    pop_budget("index_go", 50, 0.45, 160.0, dw),
                    pop("index_hold", 32, 0.90),
                    pop("ram_veto", 16, 0.80),
                ],
            ),
        ]
    )
    return OrderedDict(
        [
            ("id", "ttf-r69-345"),
            (
                "title",
                "Lutecia-Holt LH-8 / Press P-4: ram 18.4 MPa beats die AE 8 pps by 160 us; "
                "correct ACCEPT of an already-legal 0.42 mm/min index",
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
                    "Correct ACCEPT. Ram 18.4 < 22.0; AE 8 < 12. "
                    "total +1.14 = 0.44 + 0.30 + 0.20 + 0.12 + 0.08.",
                ),
            ),
            ("raster", ras),
            ("gate_snn", gate),
            (
                "meta",
                meta_block(
                    "lutetium-oxide-sinter",
                    [
                        "accept",
                        "designed",
                        "ram-vs-ae",
                        "index-legal",
                        "tick6-sidecar-bound",
                    ],
                    "Teaches that a legal die-AE smear can lose to ram force inside a 360 us "
                    "window; reversing 160 us would have REJECTED an already-legal index.",
                    5,
                ),
            ),
        ]
    )


