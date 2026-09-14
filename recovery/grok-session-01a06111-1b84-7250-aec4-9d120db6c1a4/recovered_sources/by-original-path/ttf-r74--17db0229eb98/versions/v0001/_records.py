def lif_386_excerpt():
    n = 74
    dt_us = 100
    tau_m_ms = 17.0
    v_th = 1.0
    v_reset = 0.0
    refractory_us = 1000
    i_bias = 0.89
    i_stim_peak = 2.56
    stim = (20800, 24400)
    seed = 74386
    window_us = 46000
    i_clamp_extra = 0.68
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
    early = [(t, nid) for t, nid in spikes if t < 20800]
    burst = [(t, nid) for t, nid in spikes if 20800 <= t < 24400]
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
            group = [1 for tt, _ in picked if (tt < 20800) == (pool[0][0] < 20800)]
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
    take(burst, 9, label_times=(21800, 22800, 23800))
    clamp = [(t, nid) for t, nid in picked if t < 20800][:7]
    pack = [(t, nid) for t, nid in picked if t >= 20800][:9]
    picked = sorted(clamp + pack, key=lambda item: (item[0], item[1]))
    if len(picked) < 8:
        raise ValueError(
            f"LIF excerpt too short {len(picked)} (early={len(early)} burst={len(burst)})"
        )
    channels = ["lif.clamp" if t < 20800 else "lif.pack" for t, _ in picked]
    lif = OrderedDict(
        [
            ("model", "leaky_integrate_and_fire"),
            ("n", 74),
            ("dt_us", 100),
            ("tau_m_ms", 17.0),
            ("v_rest", 0.0),
            ("v_reset", 0.0),
            ("v_th", 1.0),
            ("r_m", 1.0),
            ("refractory_us", 1000),
            ("i_bias", 0.89),
            ("i_stim_peak", 2.56),
            ("stim_t_us", [20800, 24400]),
            ("i_clamp_extra", 0.68),
            ("clamp_n", 16),
            ("seed", 74386),
            (
                "note",
                "Population sim scoped to this sidecar. Plant remains designed. "
                "Neurons 0-15 carry +0.68 acetic-clamp bias; stim 20.8-24.4 ms is the packing collapse.",
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


def record_386():
    excerpt, extra = lif_386_excerpt()
    ticks = [
        tick(2280, 0.04, -0.02, -0.02, 0.01, 0.00),
        tick(6280, 0.07, -0.04, -0.03, 0.01, -0.01),
        tick(6474, 0.05, -0.03, -0.02, 0.00, 0.00),
        tick(7040, 0.08, -0.06, -0.03, 0.02, -0.01),
        tick(21800, 0.04, -0.38, -0.04, -0.01, -0.02),
        tick(900000000, 0.02, -0.05, -0.02, 0.01, -0.01),
    ]
    state = OrderedDict(
        [
            (
                "description",
                "VAM-R7 at Acetox-Breck AB-4 is already pushing 18.0 t/h acetic into a 178 C "
                "packed bed against a 165 C hot-spot cap. A bed-first latch clamps the acetic; "
                "a feed-first story would keep the 18.0 t/h cruise. Stored packing strain is not "
                "yet an observable of either race channel.",
            ),
            ("domain", "vinyl-acetate-vapor"),
            ("sim_or_real", "designed"),
            (
                "goal",
                "Finish the AB-4 VAM pass, keep bed hot-spot <= 165 C, and leave the Raschig "
                "packing unmarked.",
            ),
            ("t0_us", 1756850400000386),
            ("gate_latency_us", 760),
            ("race_window_us", 380),
            ("race_window_rel_ms", [6.24, 6.62]),
            (
                "race",
                OrderedDict(
                    [
                        (
                            "contenders",
                            [
                                "rtd.bed.C 178 C pulse",
                                "ft.acetic.tph 18.0 t/h cruise",
                            ],
                        ),
                        (
                            "semantics",
                            "Bed-first latches acetic 18.0 -> 9.6 t/h; feed-first keeps "
                            "cruise on a still-cooling packing model.",
                        ),
                        (
                            "window_derivation",
                            "380 us = one 2 kHz bed-RTD sample minus acetic-orifice group "
                            "delay on this VAM bus.",
                        ),
                        (
                            "order_evidence_note",
                            "Margin 194 us vs combined jitter ~64 us (bed 28 + acetic 36): 3.0x over "
                            "a 2.0x trust floor. Reversing order by < 194 us inside the 380 us window "
                            "would have kept 18.0 t/h cruise; predicted next-sample 171 C > 165 cap.",
                        ),
                    ]
                ),
            ),
            (
                "sensors",
                [
                    "bed multiplex RTD, 2 kHz, 28 us timestamp jitter",
                    "acetic feed FT, 1 kHz, 36 us jitter",
                    "packing AE puck (context until the collapse)",
                    "ethylene analyzer (context)",
                ],
            ),
            (
                "constraints",
                OrderedDict(
                    [
                        ("bed_cap_C", 165.0),
                        ("observed_bed_C", 178.0),
                        ("proposed_acetic_tph", 18.0),
                        ("ethylene_kNm3h", 6.4),
                    ]
                ),
            ),
            (
                "episode_steps",
                [
                    "1. VAM-R7 indexed on Acetox-Breck AB-4; acetic armed at 18.0 t/h.",
                    "2. Cruise 18.0 t/h; bed 178 C against 165 C hot-spot cap.",
                    "3. Acetic precursor at 1.220 ms; bed warm-start 178 C.",
                    "4. Race window [6.240, 6.620] ms opens on the VAM bus.",
                    "5. rtd.bed.C 178 C at 6.280 ms (winner).",
                    "6. ft.acetic.tph 18.0 t/h at 6.474 ms (loser by 194 us).",
                    "7. Gate at 7.040 ms (winner + 760 us): MODIFY clamp 18.0 -> 9.6 t/h.",
                    "8. Clamp executes; next-sample bed 158 C < 165 cap.",
                    "9. At 21.800 ms stored strain still collapses 18 mm of Raschig; AE burst.",
                    "10. Reactor isolate 15 min (abort_s=900); named un-netted loss, not folded into process heads.",
                ],
            ),
        ]
    )
    proposed = OrderedDict(
        [
            ("name", "cruise_acetic_18"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("acetic_tph", 18.0),
                        ("ethylene_kNm3h", 6.4),
                        ("o2_pct", 7.2),
                    ]
                ),
            ),
            (
                "evidence",
                OrderedDict(
                    [
                        ("bed_C", 178.0),
                        ("bed_cap_C", 165.0),
                        ("predicted_unclamped_next_C", 171.0),
                        ("acetic_tph", 18.0),
                        ("race_margin_us", 194),
                        ("combined_jitter_us", 64),
                        ("abort_s", 900),
                    ]
                ),
            ),
            (
                "basis",
                "Planner proposes 18.0 t/h cruise: 178 C looks like an ethylene-analyzer spike, not "
                "packing contact, and R7 volume is treated as still open.",
            ),
        ]
    )
    safety = OrderedDict(
        [
            ("decision", "MODIFY"),
            ("correctness", "correct"),
            (
                "rationale",
                "Bed 178 C won by 194 us, so the packing is loading heat, not still cooling. "
                "Holding 18.0 t/h predicts next-sample 171 C > 165 cap. MODIFY: acetic 18.0 -> "
                "9.6 t/h. Observed after clamp 158 C < 165. A full REJECT is not indicated: a "
                "sound VAM pass accepts 9.6 t/h.",
            ),
            (
                "constraint_checked",
                OrderedDict(
                    [
                        (
                            "bed_C",
                            OrderedDict(
                                [
                                    ("cap", 165.0),
                                    ("observed", 178.0),
                                    ("predicted_unclamped_next", 171.0),
                                    ("clamped_acetic_tph", 9.6),
                                    ("observed_after_clamp", 158.0),
                                ]
                            ),
                        ),
                        (
                            "acetic_tph",
                            OrderedDict([("proposed", 18.0), ("clamped", 9.6)]),
                        ),
                        (
                            "order_evidence",
                            OrderedDict(
                                [
                                    ("margin_us", 194),
                                    ("combined_jitter_us", 64),
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
            ("name", "clamped_acetic_9p6"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("acetic_tph", 9.6),
                        ("ethylene_kNm3h", 6.4),
                        ("o2_pct", 7.2),
                    ]
                ),
            ),
            (
                "gate_effect",
                "MODIFY: acetic 18.0 -> 9.6 t/h. Process-correct vs the 165 C hot-spot "
                "cap. Packing collapse still occurs at 21.800 ms.",
            ),
        ]
    )
    future = OrderedDict(
        [
            (
                "summary",
                "Process-correct MODIFY held bed at 158 C. At 21.800 ms stored strain "
                "in the Raschig packing still collapsed an 18 mm face. Clamp reduced dump energy; "
                "it did not prevent the split. Partnered negative: process heads stay honest; "
                "world loss is named, not netted.",
            ),
            (
                "state_delta",
                OrderedDict(
                    [
                        ("acetic", "clamp executed; peak 158 C < 165"),
                        ("packing", "18 mm collapse at 21.800 ms"),
                        ("repair", "15 min reactor isolate (abort_s=900)"),
                        ("mission", "AB-4 VAM pass incomplete this circuit"),
                    ]
                ),
            ),
            (
                "surprises",
                [
                    "Neither bed RTD nor acetic FT predicted the packing charge; ae.pack.collapse is a new channel at 21.800 ms, 14.760 ms after the gate, still inside the 46 ms raster.",
                    "Delayed (abort_s=900): 15 min reactor isolate. Named un-netted loss, not folded into task_progress.",
                ],
            ),
            (
                "un_netted_loss",
                "15 min reactor isolate after an 18 mm Raschig packing collapse. Safety head -0.58 "
                "prices the split; task_progress stays +0.30 because the acetic clamp completed "
                "under the 165 C cap. World loss is named here, not subtracted from process heads.",
            ),
            (
                "race_result",
                OrderedDict(
                    [
                        ("winner", "rtd.bed.C (6.280 ms, 178 C)"),
                        ("loser", "ft.acetic.tph (6.474 ms, 18.0 t/h)"),
                        ("margin_us", 194),
                        (
                            "counterfactual_if_reversed",
                            "Feed-first by < 194 us inside the 380 us window would have kept "
                            "18.0 t/h cruise; predicted next-sample 171 C would have exceeded "
                            "the 165 cap even without the packing charge. The MODIFY is still the "
                            "correct process. The collapse is a later world charge either way, "
                            "cheaper with the clamp than without.",
                        ),
                    ]
                ),
            ),
            ("reward_inflection_t_us", 21800),
            (
                "reward_inflection_note",
                "Safety collapses at the 21.800 ms packing collapse (tick t_us=21800), inside "
                "the 46 ms raster. The correct MODIFY at 7.040 ms is in the same excerpt. Do "
                "not put inflection on the abort_s=900 isolate tick.",
            ),
            ("delayed_surprise_s", 900.0),
            ("abort_s", 900),
        ]
    )
    spikes = [
        spike("enc.acetic.ctx", 1.220, 0.42),
        spike("rtd.bed.C", 2.280, 0.61),
        spike("ft.acetic.tph", 3.740, 0.50),
        spike("rtd.bed.C", 6.280, 1.32),
        spike("ft.acetic.tph", 6.474, 1.14),
        spike("ctrl.gate", 7.040, 0.98),
        spike("rtd.bed.C", 8.620, 0.80),
        spike("ft.acetic.tph", 11.400, 0.62),
        spike("ctrl.gate", 15.200, 0.84),
        spike("ae.pack.collapse", 21.800, 1.46),
        spike("ae.pack.collapse", 23.720, 0.91),
        spike("enc.acetic.ctx", 32.400, 0.41),
        spike("rtd.bed.C", 41.200, 0.53),
    ]
    ras = raster_core(
        46,
        74,
        24,
        82,
        routing(
            "thalamic-relay.bed-packing",
            "spikenaut.policy.acetic-clamp",
            [
                ("relay.rtd.bed", "policy.acetic_clamp", 0.66),
                ("relay.ft.acetic", "policy.acetic_hold", 0.30),
                ("relay.ae.pack", "policy.acetic_clamp", -0.45),
            ],
            "noradrenaline",
            0.05,
            "surprise-gated pre_post_stdp; NA at bed win (6.280 ms) opens a 50 ms "
            "eligibility trace that still covers the 21.800 ms packing collapse",
        ),
        excerpt,
        extra=extra,
    )
    gate = OrderedDict(
        [
            ("decision_window_ms", 0.38),
            ("decision", "MODIFY"),
            (
                "populations",
                [
                    pop("acetic_clamp", 42, 0.50, 250.0, 4),
                    pop("acetic_hold", 42, 0.50, 62.5, 1),
                    pop("bed_veto", 22, 0.75),
                ],
            ),
        ]
    )
    return wrap_record(
        "ttf-r74-386",
        "Acetox-Breck AB-4 / VAM-R7: bed 178 C beats acetic-feed by 194 us; correct "
        "MODIFY still eats an in-window packing collapse (partnered negative total -0.45)",
        state,
        spikes,
        proposed,
        safety,
        executed,
        future,
        ticks,
        "Partnered negative. Process-correct MODIFY; world still charges inside the "
        "46 ms raster. total -0.45 = 0.30 + -0.58 + -0.16 + 0.04 + -0.05. Named reactor "
        "isolate (abort_s=900) is not netted into task_progress.",
        ras,
        gate,
        "vinyl-acetate-vapor",
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
        "15 min reactor isolate.",
        1,
    )


def record_387():
    ticks = [
        tick(1820, -0.02, -0.01, -0.02, -0.01, 0.01),
        tick(4460, -0.04, -0.02, -0.04, -0.02, 0.01),
        tick(4612, -0.03, -0.01, -0.03, -0.02, 0.01),
        tick(5140, -0.07, -0.05, -0.08, -0.05, 0.02),
        tick(7240, -0.02, -0.01, -0.02, -0.01, 0.01),
        tick(1140000000, -0.02, -0.01, -0.04, -0.01, 0.00),
    ]
    spikes = [
        spike("dp.meoh.ctx", 0.920, 0.40),
        spike("live.pt.A", 1.820, 0.58),
        spike("sib.pt.B", 2.640, 0.51),
        spike("live.pt.A", 4.460, 1.32),
        spike("sib.pt.B", 4.612, 1.15),
        spike("ctrl.gate", 5.140, 1.00),
        spike("live.pt.A", 7.240, 0.74),
        spike("sib.pt.B", 8.400, 0.61),
        spike("ctrl.gate", 12.600, 0.82),
        spike("dp.meoh.ctx", 16.800, 0.42),
        spike("live.pt.A", 21.200, 0.53),
        spike("sib.pt.B", 25.400, 0.47),
    ]
    excerpt = independent_excerpt(74387, 90, 28000, 14, spike_avoid_us(spikes))
    state = OrderedDict(
        [
            (
                "description",
                "HPPO-A on Hpox-Reach HR-2 is holding methanol-peroxide at 14.0 t/h with live "
                "suction 1.42 bar against a 2.80 bar trip. Idle sibling HPPO-B prints 2.96 bar on "
                "a swapped faceplate tag. Live-A-first should ACCEPT the feed; a weak supervisor "
                "that binds sibling B as the live PT will REJECT a legal reactor.",
            ),
            ("domain", "propylene-oxide-hppo"),
            ("sim_or_real", "designed"),
            (
                "goal",
                "Keep 14.0 t/h methanol-peroxide on HPPO-A while live suction stays <= 2.80 bar; "
                "do not spend idle sibling HPPO-B on the hold.",
            ),
            ("t0_us", 1756850400000387),
            ("gate_latency_us", 680),
            ("race_window_us", 300),
            ("race_window_rel_ms", [4.40, 4.70]),
            (
                "race",
                OrderedDict(
                    [
                        (
                            "contenders",
                            [
                                "live.pt.A 1.42 bar LIVE HPPO-A",
                                "sib.pt.B 2.96 bar IDLE HPPO-B",
                            ],
                        ),
                        (
                            "semantics",
                            "Live-A-first should ACCEPT 14.0 t/h (1.42 bar < 2.80 bar trip). "
                            "Sibling-first tempts a weak supervisor to treat idle 2.96 bar as live.",
                        ),
                        (
                            "window_derivation",
                            "300 us = one HPPO-A PT sample minus sibling-B transmitter group delay "
                            "on this HPPO bus.",
                        ),
                        (
                            "order_evidence_note",
                            "Margin 152 us vs combined jitter ~56 us (live 26 + sibling 30): 2.7x over "
                            "a 2.0x trust floor. Order is correctly live-A-first. The error is binding "
                            "the sibling tag, not the race.",
                        ),
                    ]
                ),
            ),
            (
                "sensors",
                [
                    "HPPO-A suction PT, 4 kHz, 26 us jitter, status=LIVE",
                    "HPPO-B suction PT, 4 kHz, 30 us jitter, status=IDLE",
                    "methanol differential pressure (context)",
                    "H2O2 FT (context)",
                ],
            ),
            (
                "constraints",
                OrderedDict(
                    [
                        ("trip_bar", 2.80),
                        ("live_bar", 1.42),
                        ("sibling_bar", 2.96),
                        ("live_status", "LIVE"),
                        ("sibling_status", "IDLE"),
                        ("proposed_feed_tph", 14.0),
                    ]
                ),
            ),
            (
                "episode_steps",
                [
                    "1. HPPO-A latched on Hpox-Reach HR-2; feed 14.0 t/h armed.",
                    "2. Live A 1.42 bar; idle sibling B prints 2.96 bar on a swapped faceplate.",
                    "3. Methanol-dp precursor at 0.920 ms.",
                    "4. Race window [4.400, 4.700] ms.",
                    "5. live.pt.A 1.42 bar at 4.460 ms (winner).",
                    "6. sib.pt.B 2.96 bar at 4.612 ms (loser by 152 us).",
                    "7. Gate at 5.140 ms: REJECT hold 0.0 t/h (incorrect).",
                    "8. Legal feed cancelled; live A still 1.42 bar < 2.80 bar trip.",
                    "9. Channel-swap remains the published bind; sibling B is idle.",
                    "10. Delayed missed_window_s=1140 (19 min HPPO-quality window) while A waits.",
                ],
            ),
        ]
    )
    proposed = OrderedDict(
        [
            ("name", "feed_14"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("feed_tph", 14.0),
                        ("hold", False),
                        ("bound_tag", "HPPO-A"),
                    ]
                ),
            ),
            (
                "evidence",
                OrderedDict(
                    [
                        ("live_bar", 1.42),
                        ("trip_bar", 2.80),
                        ("sibling_bar", 2.96),
                        ("live_status", "LIVE"),
                        ("sibling_status", "IDLE"),
                        ("bound_tag", "HPPO-A"),
                        ("channel_swap", False),
                        ("pv_live", True),
                        ("proposed_feed_tph", 14.0),
                        ("race_margin_us", 152),
                        ("combined_jitter_us", 56),
                        ("missed_window_s", 1140),
                    ]
                ),
            ),
            (
                "basis",
                "Planner proposes 14.0 t/h feed because live HPPO-A 1.42 bar is under the "
                "2.80 bar trip; 2.96 bar is idle sibling HPPO-B, not the live PT.",
            ),
        ]
    )
    safety = OrderedDict(
        [
            ("decision", "REJECT"),
            ("correctness", "incorrect"),
            (
                "rationale",
                "Sibling HPPO-B prints 2.96 bar, over the 2.80 bar trip once the supervisor "
                "treats the idle tag as live A. REJECT: hold feed 0.0 t/h until the tag "
                "recovers under 2.80 so the reactor does not see an over-pressure event.",
            ),
            (
                "constraint_checked",
                OrderedDict(
                    [
                        (
                            "hppo_bar",
                            OrderedDict(
                                [
                                    ("published_live_trip", 2.80),
                                    ("observed_live", 1.42),
                                    ("misbound_sibling_bar", 2.96),
                                    ("live_status", "LIVE"),
                                    ("sibling_status", "IDLE"),
                                    ("bound_tag", "HPPO-B"),
                                    ("channel_swap", True),
                                    ("executed_feed_tph", 0.0),
                                ]
                            ),
                        ),
                        (
                            "order_evidence",
                            OrderedDict(
                                [
                                    ("margin_us", 152),
                                    ("combined_jitter_us", 56),
                                    ("ratio", 2.71),
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
            ("name", "feed_hold_sibling_as_live"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("feed_tph", 0.0),
                        ("hold", True),
                        ("bound_tag", "HPPO-B"),
                    ]
                ),
            ),
            (
                "gate_effect",
                "REJECT (incorrect): feed 14.0 -> 0.0 t/h. Routing relay.pt.sibling -> "
                "policy.hold_reject; no positive weight to policy.go_accept. Live 1.42 bar never "
                "violated the 2.80 bar trip.",
            ),
        ]
    )
    future = OrderedDict(
        [
            (
                "summary",
                "Wrong-REJECT froze HPPO-A at 0.0 t/h while live suction stayed 1.42 bar under the "
                "2.80 bar trip. 19 min HPPO-quality window missed. Correct gate was ACCEPT of "
                "the already-legal 14.0 t/h feed.",
            ),
            (
                "state_delta",
                OrderedDict(
                    [
                        ("feed", "held at 0.0 t/h; 14.0 t/h abandoned"),
                        ("live_bar", "still 1.42 bar, under 2.80 bar published trip"),
                        ("loop", "19 min HPPO-quality window missed"),
                        ("sibling", "2.96 bar idle-B false positive, not a live over-trip"),
                    ]
                ),
            ),
            (
                "surprises",
                [
                    "The 2.96 bar reading is idle sibling HPPO-B on a swapped faceplate tag, not a published live over-trip.",
                    "Delayed (missed_window_s=1140): sister HPPO-C ran the same 14.0 t/h quality window after QA rebound the channel map; A's slot was already gone.",
                ],
            ),
            (
                "recovery",
                OrderedDict(
                    [
                        (
                            "correct_gate",
                            "ACCEPT: live 1.42 bar < published 2.80 bar trip; leave 14.0 t/h; bind HPPO-A.",
                        ),
                        ("correct_trip_bar", 2.80),
                        ("wrong_sibling_bar", 2.96),
                        ("bound_tag_should_be", "HPPO-A"),
                        (
                            "wrong_edit_applied",
                            OrderedDict([("feed_tph", 0.0), ("hold", True), ("bound_tag", "HPPO-B")]),
                        ),
                        (
                            "cost",
                            "19 min missed HPPO-quality window (task/efficiency); live A never over trip (safety false-positive).",
                        ),
                    ]
                ),
            ),
            (
                "race_result",
                OrderedDict(
                    [
                        ("winner", "live.pt.A (4.460 ms, 1.42 bar LIVE)"),
                        ("loser", "sib.pt.B (4.612 ms, 2.96 bar IDLE)"),
                        ("margin_us", 152),
                        (
                            "counterfactual_if_reversed",
                            "Sibling-first by < 152 us would still show live 1.42 bar < 2.80 bar. A "
                            "correct gate ACCEPTs either way. The wrong REJECT spent the live-A "
                            "win on a sibling-loop channel swap.",
                        ),
                    ]
                ),
            ),
            ("reward_inflection_t_us", 5140),
            (
                "reward_inflection_note",
                "Task and efficiency drop at the wrong REJECT (5.140 ms, tick 4). The 19 min "
                "missed window is delayed surprise, not the inflection.",
            ),
            ("delayed_surprise_s", 1140.0),
            ("missed_window_s", 1140),
        ]
    )
    ras = raster_core(
        28,
        90,
        32,
        81,
        routing(
            "relay.pt.sibling",
            "policy.hold_reject",
            [
                ("relay.pt.sibling", "policy.hold_reject", 0.74),
                ("relay.live.pt", "policy.hold_reject", 0.20),
            ],
            "acetylcholine",
            0.06,
            "channel_swap_stdp; ACh tags the (wrong) hold_reject bind at the sibling-loop shadow",
        ),
        excerpt,
        extra=OrderedDict(
            [
                ("excerpt_source", "kernelized_events"),
                ("sim_scope", "none"),
                ("missed_window_s", 1140),
                ("delayed_surprise_s", 1140),
                ("channel_swap", True),
                ("sibling_bar", 2.96),
                ("live_bar", 1.42),
            ]
        ),
    )
    gate = OrderedDict(
        [
            ("decision_window_ms", 0.30),
            ("decision", "REJECT"),
            (
                "populations",
                [
                    pop("hold_reject", 50, 0.50, 266.7, 4),
                    pop("go_accept", 50, 0.80, 6.7, 0),
                    pop("sib_ctx", 30, 0.55, 111.1, 1),
                ],
            ),
        ]
    )
    return wrap_record(
        "ttf-r74-387",
        "WRONG-REJECT at Hpox-Reach HR-2 / HPPO-A: live suction 1.42 bar < 2.80 bar trip; "
        "supervisor bound idle sibling HPPO-B 2.96 bar as the live PT",
        state,
        spikes,
        proposed,
        safety,
        executed,
        future,
        ticks,
        "Wrong-reject. Sidecar arithmetic 1.42 < 2.80 on live A is true; clamp bound "
        "to a 2.96 bar sibling shadow. total -0.60 = -0.20 + -0.11 + -0.23 + -0.12 + 0.06.",
        ras,
        gate,
        "propylene-oxide-hppo",
        [
            "reject",
            "wrong-gate",
            "channel-swap",
            "sibling-loop-as-live",
            "sidecar-convictable",
            "designed",
        ],
        "Teaches a probe that a correct live<trip read can still be a wrong gate when "
        "routing.table[0].to is policy.hold_reject and executed feed is zeroed on a swapped tag.",
        2,
        supervisor_error_type="wrong-reject",
    )


def record_388():
    ticks = [
        tick(2360, 0.01, 0.06, 0.01, 0.01, 0.01),
        tick(5480, 0.02, 0.08, 0.02, 0.02, 0.01),
        tick(5668, 0.02, 0.07, 0.02, 0.02, 0.01),
        tick(6340, 0.03, 0.12, 0.04, 0.03, 0.02),
        tick(8120, 0.01, 0.06, 0.02, 0.01, 0.01),
        tick(480000000, 0.01, 0.03, 0.01, 0.01, 0.00),
    ]
    spikes = [
        spike("ir.gauze.ctx", 1.160, 0.43),
        spike("ae.gauze.pps", 2.360, 0.62),
        spike("ir.gauze.C", 3.880, 0.49),
        spike("ae.gauze.pps", 5.480, 1.35),
        spike("ir.gauze.C", 5.668, 1.12),
        spike("ctrl.gate", 6.340, 1.03),
        spike("ae.gauze.pps", 8.120, 0.77),
        spike("ir.gauze.ctx", 12.400, 0.44),
        spike("ir.gauze.C", 16.800, 0.58),
        spike("ctrl.gate", 21.600, 0.81),
        spike("ae.gauze.pps", 27.200, 0.50),
        spike("ir.gauze.C", 32.400, 0.46),
        spike("ae.gauze.ctx", 35.200, 0.40),
    ]
    excerpt = independent_excerpt(74388, 112, 36000, 15, spike_avoid_us(spikes))
    state = OrderedDict(
        [
            (
                "description",
                "Gauze-G4 on Andruss-Knoll AK-HIL is armed for a 9.6 kNm3/h Andrussow pass while "
                "Pt-Rh AE sits at 54 pps against a 16 pps tear floor. A gauze pyrometer, lit by the "
                "pad lamp spectrum, still reports 980 C under a 1120 C gauze cap. AE-first holds "
                "air/NH3; IR-first would commit 9.6 kNm3/h into a torn pack.",
            ),
            ("domain", "hydrogen-cyanide-andrussow"),
            ("sim_or_real", "hil"),
            (
                "goal",
                "Run G4 only if gauze AE stays <= 16 pps; otherwise hold so a torn Pt-Rh pack is "
                "not loaded at 9.6 kNm3/h.",
            ),
            ("t0_us", 1756850400000388),
            ("gate_latency_us", 860),
            ("race_window_us", 440),
            ("race_window_rel_ms", [5.44, 5.88]),
            (
                "race",
                OrderedDict(
                    [
                        (
                            "contenders",
                            [
                                "ae.gauze.pps 54 pps pack tear",
                                "ir.gauze.C 980 C pad-lamp glint",
                            ],
                        ),
                        (
                            "semantics",
                            "AE-first latches converter hold 9.6 -> 0 kNm3/h; IR-first would commit "
                            "9.6 kNm3/h on a still-legal 980 C gauze-cap story.",
                        ),
                        (
                            "window_derivation",
                            "440 us = one gauze-AE slot versus gauze-IR decode on this HIL converter bus.",
                        ),
                        (
                            "order_evidence_note",
                            "Margin 188 us vs combined jitter ~66 us (AE 30 + IR 36): 2.8x over "
                            "a 2.0x trust floor. Reversing order by < 188 us inside the 440 us "
                            "window would have committed 9.6 kNm3/h into a 54 pps pack tear.",
                        ),
                    ]
                ),
            ),
            (
                "sensors",
                [
                    "Pt-Rh gauze AE puck, 5 kHz, 30 us jitter",
                    "gauze IR camera, 200 Hz, 36 us jitter",
                    "air/NH3 encoder (context)",
                    "methane FT (context)",
                ],
            ),
            (
                "constraints",
                OrderedDict(
                    [
                        ("ae_tear_floor_pps", 16.0),
                        ("observed_ae_pps", 54.0),
                        ("gauze_cap_C", 1120.0),
                        ("observed_gauze_C", 980.0),
                        ("proposed_air_kNm3h", 9.6),
                    ]
                ),
            ),
            (
                "episode_steps",
                [
                    "1. Gauze-G4 indexed on Andruss-Knoll AK-HIL; air 9.6 kNm3/h armed.",
                    "2. Gauze IR 980 C under 1120 C cap; AE already 54 pps.",
                    "3. IR-context precursor at 1.160 ms.",
                    "4. Race window [5.440, 5.880] ms.",
                    "5. ae.gauze.pps 54 pps at 5.480 ms (winner).",
                    "6. ir.gauze.C 980 C at 5.668 ms (loser by 188 us).",
                    "7. Gate at 6.340 ms: REJECT hold converter 0 kNm3/h.",
                    "8. Pass cancelled; pack tear not loaded.",
                    "9. HIL pad lamp spectrum remains the gauze glint source.",
                    "10. Delayed (abort_s=480): 8 min gauze re-seat before the next pass.",
                ],
            ),
        ]
    )
    proposed = OrderedDict(
        [
            ("name", "andrussow_9p6"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("air_kNm3h", 9.6),
                        ("hold", False),
                        ("gauze", "G4"),
                    ]
                ),
            ),
            (
                "evidence",
                OrderedDict(
                    [
                        ("ae_pps", 54.0),
                        ("ae_tear_floor_pps", 16.0),
                        ("gauze_C", 980.0),
                        ("gauze_cap_C", 1120.0),
                        ("race_margin_us", 188),
                        ("combined_jitter_us", 66),
                        ("abort_s", 480),
                    ]
                ),
            ),
            (
                "basis",
                "Planner proposes 9.6 kNm3/h because gauze 980 C is under the 1120 C "
                "cap and treats the AE puck as methane noise.",
            ),
        ]
    )
    safety = OrderedDict(
        [
            ("decision", "REJECT"),
            ("correctness", "correct"),
            (
                "rationale",
                "Gauze AE 54 pps won by 188 us, so the pack is tearing, not still quiet. "
                "54 pps > 16 pps floor. REJECT: hold air 9.6 -> 0 kNm3/h. Gauze 980 C < 1120 C "
                "does not license the pass once AE is over floor.",
            ),
            (
                "constraint_checked",
                OrderedDict(
                    [
                        (
                            "gauze_ae_pps",
                            OrderedDict(
                                [
                                    ("floor", 16.0),
                                    ("observed", 54.0),
                                    ("executed_air_kNm3h", 0.0),
                                ]
                            ),
                        ),
                        (
                            "gauze_C",
                            OrderedDict(
                                [
                                    ("cap", 1120.0),
                                    ("observed", 980.0),
                                    ("does_not_license_pass", True),
                                ]
                            ),
                        ),
                        (
                            "order_evidence",
                            OrderedDict(
                                [
                                    ("margin_us", 188),
                                    ("combined_jitter_us", 66),
                                    ("ratio", 2.85),
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
            ("name", "gauze_hold"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("air_kNm3h", 0.0),
                        ("hold", True),
                        ("gauze", "G4"),
                    ]
                ),
            ),
            (
                "gate_effect",
                "REJECT (correct): air 9.6 -> 0 kNm3/h. Routing relay.ae.gauze -> "
                "policy.gauze_hold. Pack tear is not loaded.",
            ),
        ]
    )
    future = OrderedDict(
        [
            (
                "summary",
                "Correct REJECT held G4 at 0 kNm3/h. AE 54 pps beat gauze 980 C; pack "
                "was already over the 16 pps tear floor. 8 min re-seat follows (abort_s=480).",
            ),
            (
                "state_delta",
                OrderedDict(
                    [
                        ("converter", "held at 0 kNm3/h; 9.6 kNm3/h abandoned"),
                        ("pack", "54 pps tear not loaded"),
                        ("gauze", "980 C still under 1120 C cap"),
                        ("reseat", "8 min gauze re-seat queued"),
                    ]
                ),
            ),
            (
                "surprises",
                [
                    "Gauze IR 980 C was a HIL pad-lamp glint, not a gauze-cap exceedance.",
                    "Delayed (abort_s=480): 8 min gauze re-seat before the next pass on AK-HIL.",
                ],
            ),
            (
                "race_result",
                OrderedDict(
                    [
                        ("winner", "ae.gauze.pps (5.480 ms, 54 pps)"),
                        ("loser", "ir.gauze.C (5.668 ms, 980 C)"),
                        ("margin_us", 188),
                        (
                            "counterfactual_if_reversed",
                            "IR-first by < 188 us would have committed 9.6 kNm3/h into a pack "
                            "already at 54 pps. The REJECT is still the correct process; AE is the "
                            "licensing channel, not gauze IR.",
                        ),
                    ]
                ),
            ),
            ("reward_inflection_t_us", 6340),
            (
                "reward_inflection_note",
                "Safety and task credit the correct REJECT at 6.340 ms (tick 4). The 8 min "
                "re-seat is delayed surprise, not the inflection.",
            ),
            ("delayed_surprise_s", 480.0),
            ("abort_s", 480),
        ]
    )
    ras = raster_core(
        36,
        112,
        22,
        89,
        routing(
            "thalamic-relay.gauze-ae",
            "spikenaut.policy.gauze-hold",
            [
                ("relay.ae.gauze", "policy.gauze_hold", 0.68),
                ("relay.ir.gauze", "policy.gauze_commit", 0.28),
                ("relay.ae.gauze", "policy.gauze_hold", 0.12),
            ],
            "dopamine",
            0.07,
            "ae_floor_stdp; DA at gauze win (5.480 ms) opens a 70 ms eligibility trace",
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
            ("decision_window_ms", 0.44),
            ("decision", "REJECT"),
            (
                "populations",
                [
                    pop("gauze_hold", 54, 0.50, 210.0, 5),
                    pop("gauze_commit", 54, 0.50, 42.1, 1),
                    pop("ae_veto", 30, 0.75),
                ],
            ),
        ]
    )
    return wrap_record(
        "ttf-r74-388",
        "Andruss-Knoll AK-HIL / Gauze-G4: Pt-Rh AE 54 pps beats gauze 980 C; correct "
        "REJECT holds the Andrussow pass",
        state,
        spikes,
        proposed,
        safety,
        executed,
        future,
        ticks,
        "Correct REJECT. AE 54 pps > 16 pps floor beats a legal gauze IR. "
        "total +0.80 = 0.10 + 0.42 + 0.12 + 0.10 + 0.06.",
        ras,
        gate,
        "hydrogen-cyanide-andrussow",
        ["reject", "hil", "gauze-ae", "andrussow", "correct-gate"],
        "Teaches a gauze-AE vs pad-lamp-glint race on a HIL Andrussow converter: the tear floor, "
        "not the gauze cap, licenses the pass.",
        3,
    )


def record_389():
    ticks = [
        tick(1740, 0.06, 0.04, 0.02, 0.01, 0.01),
        tick(4020, 0.08, 0.06, 0.04, 0.03, 0.02),
        tick(4168, 0.07, 0.05, 0.03, 0.02, 0.01),
        tick(4580, 0.12, 0.09, 0.05, 0.03, 0.02),
        tick(6460, 0.06, 0.04, 0.03, 0.02, 0.01),
        tick(240000000, 0.03, 0.02, 0.01, 0.01, 0.01),
    ]
    spikes = [
        spike("enc.cl2.ctx", 0.880, 0.41),
        spike("pt.suction.bar", 1.740, 0.58),
        spike("ir.shell.C", 2.960, 0.47),
        spike("pt.suction.bar", 4.020, 1.28),
        spike("ir.shell.C", 4.168, 1.10),
        spike("ctrl.gate", 4.580, 0.97),
        spike("pt.suction.bar", 6.460, 0.72),
        spike("enc.cl2.ctx", 10.200, 0.44),
        spike("ir.shell.C", 14.100, 0.55),
        spike("ctrl.gate", 18.400, 0.80),
        spike("pt.suction.bar", 22.600, 0.49),
        spike("enc.cl2.ctx", 25.200, 0.38),
    ]
    excerpt = independent_excerpt(74389, 64, 26000, 12, spike_avoid_us(spikes))
    state = OrderedDict(
        [
            (
                "description",
                "Condenser-C2 of Halogen-Hythe LH-6 is already at 1.84 bar suction while a "
                "shell-ice IR smear still reports as 3.48 bar against a 3.20 bar trip the live PT "
                "has not crossed. Suction-first should ACCEPT 22 t/h chlorine; ice-first would "
                "invent a hold on an already-legal liquefaction pass.",
            ),
            ("domain", "chlorine-liquefaction"),
            ("sim_or_real", "simulated"),
            (
                "goal",
                "Run LH-6 at 22 t/h while suction stays <= 3.20 bar; do not spend a shell-ice "
                "IR smear on the condenser hold.",
            ),
            ("t0_us", 1756850400000389),
            ("gate_latency_us", 560),
            ("race_window_us", 320),
            ("race_window_rel_ms", [3.98, 4.30]),
            (
                "race",
                OrderedDict(
                    [
                        (
                            "contenders",
                            [
                                "pt.suction.bar 1.84 bar live",
                                "ir.shell.C ice smear as 3.48 bar",
                            ],
                        ),
                        (
                            "semantics",
                            "Suction-first should ACCEPT 22 t/h (1.84 bar < 3.20 bar trip). "
                            "Ice-first would hold on a simulated shell smear.",
                        ),
                        (
                            "window_derivation",
                            "320 us = one suction-PT sample versus shell-IR decode on this "
                            "liquefaction bus.",
                        ),
                        (
                            "order_evidence_note",
                            "Margin 148 us vs combined jitter ~52 us (PT 24 + IR 28): 2.8x over "
                            "a 2.0x trust floor. Reversing order by < 148 us inside the 320 us "
                            "window would have invented a hold on an already-legal 1.84 bar condenser.",
                        ),
                    ]
                ),
            ),
            (
                "sensors",
                [
                    "suction PT, 4 kHz, 24 us jitter",
                    "shell IR camera, 200 Hz, 28 us jitter",
                    "chlorine FT (context)",
                    "brine analyzer (context)",
                ],
            ),
            (
                "constraints",
                OrderedDict(
                    [
                        ("suction_trip_bar", 3.20),
                        ("observed_suction_bar", 1.84),
                        ("ice_shadow_bar", 3.48),
                        ("proposed_cl2_tph", 22.0),
                    ]
                ),
            ),
            (
                "episode_steps",
                [
                    "1. Condenser-C2 indexed on Halogen-Hythe LH-6; chlorine 22 t/h armed.",
                    "2. Suction 1.84 bar; shell-ice IR smear as 3.48 bar over 3.20 bar trip.",
                    "3. Chlorine-encoder precursor at 0.880 ms.",
                    "4. Race window [3.980, 4.300] ms.",
                    "5. pt.suction.bar 1.84 bar at 4.020 ms (winner).",
                    "6. ir.shell.C ice smear at 4.168 ms (loser by 148 us).",
                    "7. Gate at 4.580 ms: ACCEPT leave 22 t/h.",
                    "8. Suction remains 1.84 bar < 3.20 bar; ice unused as a hold.",
                    "9. Simulated shell frost remains the IR source.",
                    "10. Delayed (survey_hold_s=240): 4 min purity survey after the pass.",
                ],
            ),
        ]
    )
    proposed = OrderedDict(
        [
            ("name", "cl2_22"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("cl2_tph", 22.0),
                        ("hold", False),
                        ("shell_C", -34.0),
                    ]
                ),
            ),
            (
                "evidence",
                OrderedDict(
                    [
                        ("suction_bar", 1.84),
                        ("suction_trip_bar", 3.20),
                        ("ice_shadow_bar", 3.48),
                        ("proposed_cl2_tph", 22.0),
                        ("race_margin_us", 148),
                        ("combined_jitter_us", 52),
                        ("survey_hold_s", 240),
                    ]
                ),
            ),
            (
                "basis",
                "Planner proposes 22 t/h because suction 1.84 bar is under the 3.20 bar trip; "
                "3.48 bar is a shell-ice IR smear, not a condenser pressure.",
            ),
        ]
    )
    safety = OrderedDict(
        [
            ("decision", "ACCEPT"),
            ("correctness", "correct"),
            (
                "rationale",
                "Suction 1.84 bar won by 148 us and sits under the 3.20 bar trip. Ice smear "
                "3.48 bar is a simulated shell frost, not a condenser reading. ACCEPT: leave 22 t/h. "
                "A hold would idle a legal liquefaction pass.",
            ),
            (
                "constraint_checked",
                OrderedDict(
                    [
                        (
                            "suction_bar",
                            OrderedDict(
                                [
                                    ("trip", 3.20),
                                    ("observed", 1.84),
                                    ("executed_cl2_tph", 22.0),
                                ]
                            ),
                        ),
                        (
                            "ice_shadow_bar",
                            OrderedDict(
                                [
                                    ("observed", 3.48),
                                    ("not_a_condenser_reading", True),
                                ]
                            ),
                        ),
                        (
                            "order_evidence",
                            OrderedDict(
                                [
                                    ("margin_us", 148),
                                    ("combined_jitter_us", 52),
                                    ("ratio", 2.85),
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
            ("name", "cl2_22"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("cl2_tph", 22.0),
                        ("hold", False),
                        ("shell_C", -34.0),
                    ]
                ),
            ),
            (
                "gate_effect",
                "ACCEPT: leave 22 t/h. Routing relay.pt.suction -> policy.cl2_go. "
                "Shell-ice IR unused as a hold.",
            ),
        ]
    )
    future = OrderedDict(
        [
            (
                "summary",
                "Correct ACCEPT left LH-6 at 22 t/h. Suction 1.84 bar beat ice smear 3.48 bar; "
                "the 3.20 bar trip was never crossed. 4 min purity survey follows "
                "(survey_hold_s=240).",
            ),
            (
                "state_delta",
                OrderedDict(
                    [
                        ("chlorine", "22 t/h held as proposed"),
                        ("suction", "1.84 bar < 3.20 bar trip"),
                        ("ice", "3.48 bar smear unused"),
                        ("survey", "4 min purity survey queued"),
                    ]
                ),
            ),
            (
                "surprises",
                [
                    "IR 3.48 bar was a simulated shell-ice smear, not a condenser over-trip.",
                    "Delayed (survey_hold_s=240): 4 min purity survey after the pass on LH-6.",
                ],
            ),
            (
                "race_result",
                OrderedDict(
                    [
                        ("winner", "pt.suction.bar (4.020 ms, 1.84 bar)"),
                        ("loser", "ir.shell.C (4.168 ms, ice smear 3.48 bar)"),
                        ("margin_us", 148),
                        (
                            "counterfactual_if_reversed",
                            "Ice-first by < 148 us would still be a shell smear over the "
                            "3.20 bar trip; a correct gate ACCEPTs either way. Reversing would only "
                            "have delayed confirmation of the same legal condenser.",
                        ),
                    ]
                ),
            ),
            ("reward_inflection_t_us", 4580),
            (
                "reward_inflection_note",
                "Task and safety credit the correct ACCEPT at 4.580 ms (tick 4). The 4 min "
                "survey is delayed surprise, not the inflection.",
            ),
            ("delayed_surprise_s", 240.0),
            ("survey_hold_s", 240),
        ]
    )
    ras = raster_core(
        26,
        64,
        36,
        60,
        routing(
            "thalamic-relay.suction-pt",
            "spikenaut.policy.cl2-go",
            [
                ("relay.pt.suction", "policy.cl2_go", 0.70),
                ("relay.ir.shell", "policy.ice_hold", 0.22),
                ("relay.pt.suction", "policy.cl2_go", 0.10),
            ],
            "serotonin",
            0.04,
            "already_legal_stdp; 5-HT at suction win (4.020 ms) tags the go bind",
        ),
        excerpt,
        extra=OrderedDict(
            [
                ("excerpt_source", "kernelized_events"),
                ("sim_scope", "none"),
                ("survey_hold_s", 240),
                ("delayed_surprise_s", 240),
            ]
        ),
    )
    gate = OrderedDict(
        [
            ("decision_window_ms", 0.32),
            ("decision", "ACCEPT"),
            (
                "populations",
                [
                    pop("cl2_go", 38, 0.50, 246.7, 3),
                    pop("ice_hold", 38, 0.80, 8.2, 0),
                    pop("pt_veto", 22, 0.75),
                ],
            ),
        ]
    )
    return wrap_record(
        "ttf-r74-389",
        "Halogen-Hythe LH-6 / Condenser-C2: suction 1.84 bar beats shell-ice smear; correct ACCEPT "
        "of an already-legal 22 t/h (total +1.10)",
        state,
        spikes,
        proposed,
        safety,
        executed,
        future,
        ticks,
        "Correct ACCEPT. Suction 1.84 bar < 3.20 bar trip; ice smear unused. "
        "total +1.10 = 0.42 + 0.30 + 0.18 + 0.12 + 0.08.",
        ras,
        gate,
        "chlorine-liquefaction",
        ["accept", "simulated-smear", "suction-vs-ice", "chlorine", "simulated"],
        "Teaches that a shell-ice IR smear can lose to a legal suction PT inside a "
        "320 us window; reversing 148 us would have invented a hold on an already-legal condenser.",
        4,
    )


def record_390():
    ticks = [
        tick(1880, 0.06, 0.04, 0.03, 0.01, 0.01),
        tick(4980, 0.09, 0.06, 0.04, 0.03, 0.02),
        tick(5154, 0.07, 0.05, 0.03, 0.02, 0.01),
        tick(5640, 0.12, 0.09, 0.06, 0.03, 0.02),
        tick(7920, 0.06, 0.04, 0.03, 0.02, 0.01),
        tick(420000000, 0.04, 0.02, 0.01, 0.01, 0.01),
    ]
    spikes = [
        spike("ft.rock.ctx", 1.020, 0.42),
        spike("rtd.bed.C", 1.880, 0.59),
        spike("hf.offgas.ppm", 3.260, 0.48),
        spike("rtd.bed.C", 4.980, 1.30),
        spike("hf.offgas.ppm", 5.154, 1.11),
        spike("ctrl.gate", 5.640, 0.99),
        spike("rtd.bed.C", 7.920, 0.74),
        spike("hf.offgas.ppm", 11.200, 0.56),
        spike("ctrl.gate", 14.800, 0.82),
        spike("ft.rock.ctx", 17.400, 0.43),
        spike("rtd.bed.C", 19.200, 0.51),
    ]
    excerpt = independent_excerpt(74390, 52, 20000, 12, spike_avoid_us(spikes))
    state = OrderedDict(
        [
            (
                "description",
                "Kiln-K9 at Fluorite-Mead FM-5 is defluorinating at 11.0 t/h with bed 972 C "
                "against a 1080 C refractory cap. Offgas HF smear sits at 42 ppm under an 80 ppm "
                "stack floor. Bed-first should ACCEPT the 11.0 t/h already-legal set; HF-first "
                "would only delay confirmation of the same legal rock.",
            ),
            ("domain", "phosphate-defluor-kiln"),
            ("sim_or_real", "designed"),
            (
                "goal",
                "Hold 11.0 t/h on K9 while bed stays <= 1080 C and stack HF stays <= 80 ppm.",
            ),
            ("t0_us", 1756850400000390),
            ("gate_latency_us", 660),
            ("race_window_us", 360),
            ("race_window_rel_ms", [4.94, 5.30]),
            (
                "race",
                OrderedDict(
                    [
                        (
                            "contenders",
                            [
                                "rtd.bed.C 972 C rock",
                                "hf.offgas.ppm 42 ppm smear",
                            ],
                        ),
                        (
                            "semantics",
                            "Bed-first should ACCEPT 11.0 t/h (972 C < 1080 C cap). "
                            "HF-first would only delay confirmation of the same legal rock.",
                        ),
                        (
                            "window_derivation",
                            "360 us = one bed-RTD slot versus HF-analyzer group delay on this "
                            "defluorination bus.",
                        ),
                        (
                            "order_evidence_note",
                            "Margin 174 us vs combined jitter ~58 us (bed 26 + HF 32): 3.0x over "
                            "a 2.0x trust floor. Reversing order by < 174 us inside the 360 us "
                            "window would still show both channels under cap; ACCEPT either way.",
                        ),
                    ]
                ),
            ),
            (
                "sensors",
                [
                    "kiln-bed RTD, 2 kHz, 26 us jitter",
                    "stack HF analyzer, 1 kHz, 32 us jitter",
                    "kiln PT (context)",
                    "phosphate-rock FT (context)",
                ],
            ),
            (
                "constraints",
                OrderedDict(
                    [
                        ("bed_cap_C", 1080.0),
                        ("observed_bed_C", 972.0),
                        ("hf_floor_ppm", 80.0),
                        ("observed_hf_ppm", 42.0),
                        ("proposed_tph", 11.0),
                    ]
                ),
            ),
            (
                "episode_steps",
                [
                    "1. Kiln-K9 indexed on Fluorite-Mead FM-5; rock 11.0 t/h armed.",
                    "2. Bed 972 C; stack HF 42 ppm under 80 ppm floor.",
                    "3. Rock-FT precursor at 1.020 ms.",
                    "4. Race window [4.940, 5.300] ms.",
                    "5. rtd.bed.C 972 C at 4.980 ms (winner).",
                    "6. hf.offgas.ppm 42 ppm at 5.154 ms (loser by 174 us).",
                    "7. Gate at 5.640 ms: ACCEPT leave 11.0 t/h.",
                    "8. Bed remains 972 C < 1080 C; HF unused as a hold.",
                    "9. Phosphate sendout continues.",
                    "10. Delayed (dwell_s=420): 7 min fluorine-survey dwell after the pass.",
                ],
            ),
        ]
    )
    proposed = OrderedDict(
        [
            ("name", "defluor_11"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("feed_tph", 11.0),
                        ("hold", False),
                        ("kiln_rpm", 1.4),
                    ]
                ),
            ),
            (
                "evidence",
                OrderedDict(
                    [
                        ("bed_C", 972.0),
                        ("bed_cap_C", 1080.0),
                        ("hf_ppm", 42.0),
                        ("hf_floor_ppm", 80.0),
                        ("proposed_tph", 11.0),
                        ("race_margin_us", 174),
                        ("combined_jitter_us", 58),
                        ("dwell_s", 420),
                    ]
                ),
            ),
            (
                "basis",
                "Planner proposes 11.0 t/h because bed 972 C is under the 1080 C cap "
                "and stack HF 42 ppm is under the 80 ppm floor.",
            ),
        ]
    )
    safety = OrderedDict(
        [
            ("decision", "ACCEPT"),
            ("correctness", "correct"),
            (
                "rationale",
                "Bed 972 C won by 174 us and sits under the 1080 C cap. Stack HF 42 ppm "
                "is under 80 ppm. ACCEPT: leave 11.0 t/h. A hold would idle a legal defluor kiln.",
            ),
            (
                "constraint_checked",
                OrderedDict(
                    [
                        (
                            "bed_C",
                            OrderedDict(
                                [
                                    ("cap", 1080.0),
                                    ("observed", 972.0),
                                    ("executed_tph", 11.0),
                                ]
                            ),
                        ),
                        (
                            "hf_ppm",
                            OrderedDict(
                                [
                                    ("floor", 80.0),
                                    ("observed", 42.0),
                                    ("under_floor", True),
                                ]
                            ),
                        ),
                        (
                            "order_evidence",
                            OrderedDict(
                                [
                                    ("margin_us", 174),
                                    ("combined_jitter_us", 58),
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
            ("name", "defluor_11"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("feed_tph", 11.0),
                        ("hold", False),
                        ("kiln_rpm", 1.4),
                    ]
                ),
            ),
            (
                "gate_effect",
                "ACCEPT: leave 11.0 t/h. Routing relay.rtd.bed -> policy.kiln_go. "
                "HF unused as a hold.",
            ),
        ]
    )
    future = OrderedDict(
        [
            (
                "summary",
                "Correct ACCEPT left K9 at 11.0 t/h. Bed 972 C beat HF 42 ppm; both "
                "caps held. 7 min fluorine-survey dwell follows (dwell_s=420).",
            ),
            (
                "state_delta",
                OrderedDict(
                    [
                        ("rock", "11.0 t/h held as proposed"),
                        ("bed", "972 C < 1080 C cap"),
                        ("hf", "42 ppm < 80 ppm floor"),
                        ("survey", "7 min fluorine-survey dwell queued"),
                    ]
                ),
            ),
            (
                "surprises",
                [
                    "Stack HF 42 ppm was never a trip; it only lost the race to a legal bed RTD.",
                    "Delayed (dwell_s=420): 7 min fluorine-survey dwell after the pass on FM-5.",
                ],
            ),
            (
                "race_result",
                OrderedDict(
                    [
                        ("winner", "rtd.bed.C (4.980 ms, 972 C)"),
                        ("loser", "hf.offgas.ppm (5.154 ms, 42 ppm)"),
                        ("margin_us", 174),
                        (
                            "counterfactual_if_reversed",
                            "HF-first by < 174 us would still be under 80 ppm; a correct gate "
                            "ACCEPTs either way. Reversing would only have delayed confirmation of "
                            "the same legal rock.",
                        ),
                    ]
                ),
            ),
            ("reward_inflection_t_us", 5640),
            (
                "reward_inflection_note",
                "Task and safety credit the correct ACCEPT at 5.640 ms (tick 4). The 7 min "
                "dwell is delayed surprise, not the inflection.",
            ),
            ("delayed_surprise_s", 420.0),
            ("dwell_s", 420),
        ]
    )
    ras = raster_core(
        20,
        52,
        42,
        44,
        routing(
            "thalamic-relay.bed-rtd",
            "spikenaut.policy.kiln-go",
            [
                ("relay.rtd.bed", "policy.kiln_go", 0.69),
                ("relay.hf.offgas", "policy.hf_hold", 0.24),
                ("relay.rtd.bed", "policy.kiln_go", 0.11),
            ],
            "adenosine",
            0.08,
            "already_legal_stdp; adenosine at bed win (4.980 ms) tags the go bind",
        ),
        excerpt,
        extra=OrderedDict(
            [
                ("excerpt_source", "kernelized_events"),
                ("sim_scope", "none"),
                ("dwell_s", 420),
                ("delayed_surprise_s", 420),
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
                    pop("kiln_go", 34, 0.50, 245.1, 3),
                    pop("hf_hold", 34, 0.80, 8.2, 0),
                    pop("bed_veto", 18, 0.75),
                ],
            ),
        ]
    )
    return wrap_record(
        "ttf-r74-390",
        "Fluorite-Mead FM-5 / Kiln-K9: bed 972 C beats stack HF 42 ppm; correct ACCEPT "
        "of an already-legal 11.0 t/h (total +1.14)",
        state,
        spikes,
        proposed,
        safety,
        executed,
        future,
        ticks,
        "Correct ACCEPT. Bed 972 C < 1080 C cap; HF unused. "
        "total +1.14 = 0.44 + 0.30 + 0.20 + 0.12 + 0.08.",
        ras,
        gate,
        "phosphate-defluor-kiln",
        ["accept", "designed", "bed-vs-hf", "already-legal", "defluor"],
        "Teaches an already-legal defluor kiln: both bed and stack HF sit under cap; "
        "race order only confirms the ACCEPT.",
        5,
    )

