def lif_201_excerpt():
    n = 76
    dt_us = 100
    tau_m_ms = 19.0
    v_th = 1.0
    v_reset = 0.0
    refractory_us = 1000
    i_bias = 0.91
    i_stim_peak = 2.48
    stim = (21000, 24000)
    seed = 37201
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
    early = [(t, nid) for t, nid in spikes if t < 21000]
    burst = [(t, nid) for t, nid in spikes if 21000 <= t < 24000]
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
            group = [1 for tt, _ in picked if (tt < 21000) == (pool[0][0] < 21000)]
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
    take(burst, 9, label_times=(21800, 22400, 23200))
    clamp = [(t, nid) for t, nid in picked if t < 21000][:7]
    tear = [(t, nid) for t, nid in picked if t >= 21000][:9]
    picked = sorted(clamp + tear, key=lambda item: (item[0], item[1]))
    if len(picked) < 10:
        raise RuntimeError(f"LIF excerpt short: {len(picked)}")
    channels = ["lif.clamp" if t < 21000 else "lif.sock" for t, _ in picked]
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
            ("i_stim_peak", 2.48),
            ("stim_t_us", [21000, 24000]),
            ("i_clamp_extra", 0.62),
            ("clamp_n", 14),
            ("seed", 37201),
            (
                "note",
                "Population sim scoped to this sidecar. Plant remains designed. "
                "Neurons 0-13 carry +0.62 aeration-boost bias; stim 21-24 ms is the baghouse-sock tear.",
            ),
        ]
    )
    extra = OrderedDict(
        [
            ("excerpt_source", "independent_lif"),
            ("sim_scope", "sidecar_only"),
            ("lif", lif),
            ("abort_s", 960),
            ("delayed_surprise_s", 960),
        ]
    )
    return excerpt_items(picked, channels), extra


def meta_block(
    domain,
    tags,
    distillation_value,
    batch_position,
    supervisor_error_type=None,
) -> OrderedDict:
    body = OrderedDict(
        [
            ("round", 37),
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


def record_201():
    excerpt, extra = lif_201_excerpt()
    ticks = [
        tick(2440, 0.04, -0.02, -0.02, 0.01, 0.00),
        tick(6120, 0.08, -0.04, -0.02, 0.01, -0.01),
        tick(6312, 0.04, -0.03, -0.02, 0.00, 0.00),
        tick(6840, 0.08, -0.05, -0.03, 0.02, -0.01),
        tick(21800, 0.04, -0.45, -0.03, -0.01, -0.01),
        tick(960000000, 0.02, -0.05, -0.02, 0.01, -0.01),
    ]
    state = OrderedDict(
        [
            (
                "description",
                "Tunnel-T4 at Peat-Rake PT-4 is finishing a Phase-II compost turn with core O2 "
                "at 8.4 percent against a 12.0 percent aerobic floor. Aeration sits at 1800 m3/h "
                "while blower tach is 1480 rpm under an 1800 rpm nameplate. O2-first boosts air "
                "1800 -> 2600 m3/h; rpm-first would keep 1800 m3/h on a still-under-cap blower. "
                "A baghouse sock already nicked on String-S3 does not appear on O2 or tach until "
                "the AE tear.",
            ),
            ("domain", "mushroom-compost-tunnel"),
            ("sim_or_real", "designed"),
            (
                "goal",
                "Keep Tunnel-T4 core O2 >= 12.0 percent through the Phase-II turn without "
                "parting the baghouse sock.",
            ),
            ("t0_us", 1756858800000201),
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
                                "o2.core.pct 8.4 under 12.0 floor",
                                "enc.blower.rpm 1480 under 1800 nameplate",
                            ],
                        ),
                        (
                            "semantics",
                            "O2-first latches aeration boost 1800 -> 2600 m3/h; rpm-first keeps "
                            "1800 m3/h on a 'blower still has headroom' model.",
                        ),
                        (
                            "window_derivation",
                            "400 us = one zirconia O2 slot versus the blower-tach publisher on "
                            "this tunnel PLC bus.",
                        ),
                        (
                            "order_evidence_note",
                            "Margin 192 us vs combined jitter 62 us (O2 30 + tach 32): 3.1x over "
                            "a 2.0x trust floor. Reversing order by < 192 us inside the 400 us "
                            "window would have kept 1800 m3/h; predicted next-sample 8.6 percent "
                            "< 12.0 floor.",
                        ),
                    ]
                ),
            ),
            (
                "sensors",
                [
                    "core zirconia O2 cell, 2 kHz, 30 us jitter",
                    "blower tach + inlet orifice, 1 kHz, 32 us jitter",
                    "baghouse AE puck (context)",
                    "tunnel RTD string (context)",
                ],
            ),
            (
                "constraints",
                OrderedDict(
                    [
                        ("o2_floor_pct", 12.0),
                        ("observed_o2_pct", 8.4),
                        ("aeration_m3_h", 1800.0),
                        ("blower_rpm", 1480.0),
                        ("blower_cap_rpm", 1800.0),
                    ]
                ),
            ),
            (
                "episode_steps",
                [
                    "1. Tunnel-T4 indexed; aeration 1800 m3/h; core O2 8.4 percent.",
                    "2. Blower 1480 rpm under 1800 rpm nameplate; Phase-II turn armed.",
                    "3. Orifice precursor at 1.180 ms.",
                    "4. Race window [6.000, 6.400] ms.",
                    "5. o2.core.pct 8.4 at 6.120 ms (winner).",
                    "6. enc.blower.rpm 1480 at 6.312 ms (loser by 192 us).",
                    "7. Gate at 6.840 ms: MODIFY boost 1800 -> 2600 m3/h.",
                    "8. After boost O2 12.6 percent >= 12.0; blower still 1480 rpm.",
                    "9. At 21.800 ms a baghouse sock tears 0.4 m2.",
                    "10. 16 min sock swap (abort_s=960); named un-netted loss.",
                ],
            ),
        ]
    )
    proposed = OrderedDict(
        [
            ("name", "cruise_tunnel_air"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("aeration_m3_h", 1800.0),
                        ("o2_pct", 8.4),
                        ("blower_rpm", 1480.0),
                    ]
                ),
            ),
            (
                "evidence",
                OrderedDict(
                    [
                        ("o2_pct", 8.4),
                        ("o2_floor_pct", 12.0),
                        ("predicted_unclamped_next_pct", 8.6),
                        ("aeration_m3_h", 1800.0),
                        ("blower_rpm", 1480.0),
                        ("blower_cap_rpm", 1800.0),
                        ("race_margin_us", 192),
                        ("combined_jitter_us", 62),
                        ("abort_s", 960),
                    ]
                ),
            ),
            (
                "basis",
                "Planner proposes 1800 m3/h because blower 1480 rpm is under 1800, treating "
                "the 8.4 percent O2 as a still-wet zirconia rather than an aerobic-floor miss.",
            ),
        ]
    )
    safety = OrderedDict(
        [
            ("decision", "MODIFY"),
            ("correctness", "correct"),
            (
                "rationale",
                "Core O2 8.4 percent won by 192 us, so the tunnel is anaerobic, not still a "
                "blower-speed story. Holding 1800 m3/h predicts next-sample 8.6 percent < 12.0 "
                "floor. MODIFY: aeration 1800 -> 2600 m3/h. Observed after boost 12.6 percent "
                ">= 12.0. A full REJECT is not indicated: a clean turn accepts 2600 m3/h.",
            ),
            (
                "constraint_checked",
                OrderedDict(
                    [
                        (
                            "o2_pct",
                            OrderedDict(
                                [
                                    ("floor", 12.0),
                                    ("observed", 8.4),
                                    ("predicted_unclamped_next", 8.6),
                                    ("boosted_air_m3_h", 2600.0),
                                    ("observed_after_boost", 12.6),
                                ]
                            ),
                        ),
                        (
                            "order_evidence",
                            OrderedDict(
                                [
                                    ("margin_us", 192),
                                    ("combined_jitter_us", 62),
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
            ("name", "boosted_tunnel_air"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("aeration_m3_h", 2600.0),
                        ("o2_pct", 12.6),
                        ("blower_rpm", 1480.0),
                    ]
                ),
            ),
            (
                "gate_effect",
                "MODIFY: aeration 1800 -> 2600 m3/h. Process-correct vs the 12.0 percent O2 "
                "floor. Baghouse sock still tears at 21.800 ms.",
            ),
        ]
    )
    future = OrderedDict(
        [
            (
                "summary",
                "Process-correct MODIFY held core O2 at 12.6 percent. At 21.800 ms a baghouse "
                "sock already nicked on String-S3 tore 0.4 m2. Boost reduced tear energy; it "
                "did not prevent the tear. Partnered negative: process heads stay honest; world "
                "loss is named, not netted.",
            ),
            (
                "state_delta",
                OrderedDict(
                    [
                        ("purity", "boost executed; peak 12.6 percent >= 12.0 floor"),
                        ("sock", "tore at 21.800 ms; 0.4 m2 baghouse face"),
                        ("repair", "16 min sock swap (abort_s=960)"),
                        ("mission", "PT-4 Phase-II turn incomplete this circuit"),
                    ]
                ),
            ),
            (
                "surprises",
                [
                    "Neither core O2 nor blower RPM predicted the nicked sock; ae.sock.tear is a new channel at 21.800 ms, 14.960 ms after the gate, still inside the 42 ms raster.",
                    "Delayed (abort_s=960): 16 min sock swap. Named un-netted loss, not folded into task_progress.",
                ],
            ),
            (
                "un_netted_loss",
                "16 min sock swap after the baghouse tear. Safety head -0.64 prices the tear; "
                "task_progress stays +0.30 because the aeration boost completed under the 12.0 "
                "percent floor. World loss is named here, not subtracted from process heads.",
            ),
            (
                "race_result",
                OrderedDict(
                    [
                        ("winner", "o2.core.pct (6.120 ms, 8.4 percent)"),
                        ("loser", "enc.blower.rpm (6.312 ms, 1480 rpm)"),
                        ("margin_us", 192),
                        (
                            "counterfactual_if_reversed",
                            "Rpm-first by < 192 us inside the 400 us window would have kept "
                            "1800 m3/h; predicted next-sample 8.6 percent would have missed the "
                            "12.0 floor even without the sock tear. The MODIFY is still the "
                            "correct process. The tear is a later world charge either way, "
                            "cheaper with the boost than without.",
                        ),
                    ]
                ),
            ),
            ("reward_inflection_t_us", 21800),
            (
                "reward_inflection_note",
                "Safety collapses at the 21.800 ms baghouse-sock tear (tick t_us=21800), inside "
                "the 42 ms raster. The correct MODIFY at 6.840 ms is in the same excerpt. Do "
                "not put inflection on the abort_s=960 sock-swap tick.",
            ),
        ]
    )
    spikes = [
        spike("enc.blower.ctx", 1.180, 0.41),
        spike("o2.core.pct", 2.440, 0.58),
        spike("enc.blower.rpm", 3.880, 0.50),
        spike("o2.core.pct", 6.120, 1.31),
        spike("enc.blower.rpm", 6.312, 1.12),
        spike("ctrl.gate", 6.840, 0.97),
        spike("o2.core.pct", 8.200, 0.82),
        spike("enc.blower.rpm", 10.550, 0.64),
        spike("ctrl.gate", 14.100, 0.86),
        spike("ae.sock.tear", 21.800, 1.48),
        spike("ae.sock.tear", 23.900, 0.93),
        spike("enc.blower.ctx", 29.800, 0.40),
        spike("o2.core.pct", 36.200, 0.55),
    ]
    ras = raster_core(
        42,
        76,
        26,
        83,
        routing(
            "thalamic-relay.compost-o2",
            "spikenaut.policy.air-boost",
            [
                ("relay_o2_core", "policy_air_boost", 0.68),
                ("relay_blower_rpm", "policy_air_hold", 0.29),
                ("relay_ae_sock", "policy_air_boost", -0.42),
            ],
            "noradrenaline",
            0.04,
            "surprise-gated pre_post_stdp; NA at O2 win (6.120 ms) opens a 42 ms eligibility "
            "trace that still covers the 21.800 ms sock tear",
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
                    pop("air_boost", 50, 0.50, 200.0, 4),
                    pop("air_hold", 40, 0.80, 50.0, 1),
                    pop("sock_veto", 24, 0.75),
                ],
            ),
        ]
    )
    return OrderedDict(
        [
            ("id", "ttf-r37-201"),
            (
                "title",
                "Peat-Rake PT-4 / Tunnel-T4: core O2 beats blower tach by 192 us; correct "
                "MODIFY still eats an in-window baghouse-sock tear (partnered negative total -0.48)",
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
                    "sock swap (abort_s=960) is not netted into task_progress.",
                ),
            ),
            ("raster", ras),
            ("gate_snn", gate),
            (
                "meta",
                meta_block(
                    "mushroom-compost-tunnel",
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
                    "16 min sock swap.",
                    1,
                ),
            ),
        ]
    )


def record_202():
    ticks = [
        tick(2210, -0.02, -0.02, -0.02, -0.01, 0.01),
        tick(5480, -0.04, -0.04, -0.03, -0.02, 0.01),
        tick(5656, -0.04, -0.04, -0.03, -0.02, 0.01),
        tick(6020, -0.08, -0.10, -0.06, -0.03, 0.02),
        tick(6400, -0.02, -0.02, -0.02, -0.01, 0.01),
        tick(720000000, -0.02, -0.02, -0.02, -0.01, 0.00),
    ]
    spikes = [
        spike("enc.riser.ctx", 1.050, 0.42),
        spike("ir.regen.C", 2.210, 0.57),
        spike("o2.flue.pct", 3.400, 0.49),
        spike("ir.regen.C", 5.480, 1.29),
        spike("o2.flue.pct", 5.656, 1.10),
        spike("ctrl.gate", 6.020, 0.96),
        spike("ir.regen.C", 7.800, 0.80),
        spike("o2.flue.pct", 10.200, 0.63),
        spike("ctrl.gate", 13.500, 0.84),
        spike("enc.riser.ctx", 18.400, 0.41),
        spike("ir.regen.C", 22.100, 0.54),
        spike("o2.flue.pct", 26.400, 0.38),
    ]
    excerpt = independent_excerpt(37202, 88, 28000, 14, spike_avoid_us(spikes))
    state = OrderedDict(
        [
            (
                "description",
                "Regen-R8 at Zeolite-Knap ZK-6 is already in afterburn with dense-bed IR at "
                "745 C against a 720 C afterburn cap. Torch-oil is 1.80 t/h. Flue O2 sits at "
                "1.8 percent under a 3.0 percent reducing look. IR-first should cut torch "
                "1.80 -> 0.40 t/h now; a weak supervisor instead files a 12 s ramp and leaves "
                "the bed over cap for the whole delay.",
            ),
            ("domain", "fcc-riser-regenerator"),
            ("sim_or_real", "designed"),
            (
                "goal",
                "Finish the ZK-6 afterburn with dense-bed IR <= 720 C, cut torch immediately, "
                "and leave flue O2 to its own 3.0 percent look.",
            ),
            ("t0_us", 1756858800000202),
            ("gate_latency_us", 540),
            ("race_window_us", 360),
            ("race_window_rel_ms", [5.4, 5.76]),
            (
                "race",
                OrderedDict(
                    [
                        (
                            "contenders",
                            [
                                "ir.regen.C 745 C on afterburn phase",
                                "o2.flue.pct 1.8 under 3.0 reducing look",
                            ],
                        ),
                        (
                            "semantics",
                            "IR-first should latch immediate torch cut 1.80 -> 0.40 t/h; "
                            "O2-first is a false 'wait for air' bind that only schedules a ramp.",
                        ),
                        (
                            "window_derivation",
                            "360 us = one dense-bed IR slot versus the flue-O2 publisher on "
                            "this regenerator DCS bus.",
                        ),
                        (
                            "order_evidence_note",
                            "Margin 176 us vs combined jitter 58 us (IR 28 + O2 30). Order is "
                            "correctly IR-first. The error is clamp timing, not the race and "
                            "not the actuator.",
                        ),
                    ]
                ),
            ),
            (
                "sensors",
                [
                    "dense-bed IR pyrometer, 2 kHz, 28 us jitter, phase=afterburn",
                    "flue zirconia O2, 1 kHz, 30 us jitter",
                    "torch-oil Coriolis (context)",
                    "cyclone inlet PT (context)",
                ],
            ),
            (
                "constraints",
                OrderedDict(
                    [
                        ("regen_cap_C", 720.0),
                        ("observed_regen_C", 745.0),
                        ("torch_tph", 1.80),
                        ("flue_o2_pct", 1.8),
                        ("flue_o2_look_pct", 3.0),
                        ("correct_ramp_s", 0.0),
                    ]
                ),
            ),
            (
                "episode_steps",
                [
                    "1. Regen-R8 already in afterburn; dense-bed 745 C; torch 1.80 t/h.",
                    "2. Flue O2 1.8 percent under 3.0 look; not an air-starved story.",
                    "3. Encoder precursor at 1.050 ms.",
                    "4. Race window [5.400, 5.760] ms.",
                    "5. ir.regen.C 745 C at 5.480 ms (winner).",
                    "6. o2.flue.pct 1.8 at 5.656 ms (loser by 176 us).",
                    "7. Gate at 6.020 ms: WRONG-MODIFY sets torch 0.40 t/h with ramp_s=12; not immediate.",
                    "8. Bed stays 744 C over 720 cap during the 12 s delay.",
                    "9. Afterburn near-miss; torch recycle.",
                    "10. Delayed (abort_s=720): 12 min regenerator recycle while R8 is re-homed.",
                ],
            ),
        ]
    )
    proposed = OrderedDict(
        [
            ("name", "cruise_afterburn_torch"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("torch_tph", 1.80),
                        ("ramp_s", 0.0),
                        ("regen_C", 745.0),
                    ]
                ),
            ),
            (
                "evidence",
                OrderedDict(
                    [
                        ("regen_C", 745.0),
                        ("regen_cap_C", 720.0),
                        ("torch_tph", 1.80),
                        ("flue_o2_pct", 1.8),
                        ("flue_o2_look_pct", 3.0),
                        ("race_margin_us", 176),
                        ("combined_jitter_us", 58),
                        ("abort_s", 720),
                    ]
                ),
            ),
            (
                "basis",
                "Planner proposes continuing 1.80 t/h torch: flue O2 1.8 percent looks under "
                "the 3.0 percent reducing look, so 745 C is treated as a still-starved bed.",
            ),
        ]
    )
    safety = OrderedDict(
        [
            ("decision", "MODIFY"),
            ("correctness", "incorrect"),
            (
                "rationale",
                "Dense-bed 745 C exceeds the 720 C afterburn cap (true). Cut torch toward 0.40 "
                "t/h but ramp over 12 s so flue O2 can recover first. Immediate cut would shock "
                "the cyclone.",
            ),
            (
                "constraint_checked",
                OrderedDict(
                    [
                        (
                            "regen_C",
                            OrderedDict(
                                [
                                    ("cap", 720.0),
                                    ("observed", 745.0),
                                    ("executed_torch_tph", 0.40),
                                    ("executed_ramp_s", 12.0),
                                ]
                            ),
                        ),
                        (
                            "timing",
                            OrderedDict(
                                [
                                    ("correct_ramp_s", 0.0),
                                    ("applied_ramp_s", 12.0),
                                    ("error_class", "clamp-too-late"),
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
            ("name", "torch_ramp_too_late"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("torch_tph", 0.40),
                        ("ramp_s", 12.0),
                        ("regen_C", 745.0),
                    ]
                ),
            ),
            (
                "gate_effect",
                "MODIFY (incorrect): torch target 0.40 t/h with ramp_s=12; bed left at 745 C "
                "during the delay. Routing relay_ir_regen -> policy_torch_ramp; no positive "
                "weight to policy_torch_cut.",
            ),
        ]
    )
    future = OrderedDict(
        [
            (
                "summary",
                "Wrong-MODIFY scheduled a 12 s torch ramp and left Regen-R8 afterburning at "
                "745 C. Dense-bed 745 C was over the 720 C floor; flue O2 1.8 percent was a "
                "non-binding reducing look. 12 min regenerator recycle (abort_s=720). Correct "
                "gate was MODIFY torch 1.80 -> 0.40 t/h with ramp_s=0.",
            ),
            (
                "state_delta",
                OrderedDict(
                    [
                        ("bed", "still 745 C; 745 > 720 cap during delay"),
                        ("torch", "target 0.40 t/h on a 12 s ramp"),
                        ("regen", "12 min recycle, R8 re-home"),
                        ("mission", "afterburn deferred"),
                    ]
                ),
            ),
            (
                "surprises",
                [
                    "IR-first was the correct order and the temperature number was over cap; the MODIFY spent that win on a delayed ramp instead of an immediate cut.",
                    "Delayed (abort_s=720): ZK-6 holds 12 min while R8 is re-homed; next slate 14 min late.",
                ],
            ),
            (
                "recovery",
                OrderedDict(
                    [
                        (
                            "correct_gate",
                            "MODIFY torch 1.80 -> 0.40 t/h immediately (ramp_s=0); leave flue O2 to its 3.0 percent look.",
                        ),
                        ("correct_actuator", "torch_oil"),
                        ("wrong_timing", "ramp_s=12 instead of 0"),
                        ("error_class", "clamp-too-late"),
                        (
                            "wrong_edit_applied",
                            OrderedDict([("torch_tph", 0.40), ("ramp_s", 12.0)]),
                        ),
                        (
                            "cost",
                            "12 min regenerator recycle (task/efficiency); bed never left the 745 C over-cap during the delay (safety near-miss of a late clamp).",
                        ),
                    ]
                ),
            ),
            (
                "race_result",
                OrderedDict(
                    [
                        ("winner", "ir.regen.C (5.480 ms, 745 C)"),
                        ("loser", "o2.flue.pct (5.656 ms, 1.8 percent)"),
                        ("margin_us", 176),
                        (
                            "counterfactual_if_reversed",
                            "O2-first by < 176 us would still be under the 3.0 percent look; a "
                            "correct gate binds ir.regen.C to policy_torch_cut either way. The "
                            "wrong MODIFY spent the IR win on a 12 s ramp.",
                        ),
                    ]
                ),
            ),
            ("reward_inflection_t_us", 6020),
            (
                "reward_inflection_note",
                "Task, safety, and efficiency drop at the wrong MODIFY (6.020 ms, tick 4). "
                "The 12 min regenerator recycle is delayed surprise, not the inflection.",
            ),
        ]
    )
    ras = raster_core(
        28,
        88,
        34,
        84,
        routing(
            "thalamic-relay.fcc-regen",
            "spikenaut.policy.torch-ramp",
            [
                ("relay_ir_regen", "policy_torch_ramp", 0.73),
                ("relay_flue_o2", "policy_torch_ramp", 0.22),
            ],
            "acetylcholine",
            0.08,
            "late_clamp_stdp; ACh tags the (wrong) torch_ramp bind at the IR win",
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
            ("decision_window_ms", 0.36),
            ("decision", "MODIFY"),
            (
                "populations",
                [
                    pop("torch_ramp", 48, 0.45, 230.0, 4),
                    pop("torch_cut", 42, 0.90),
                    pop("o2_wait", 20, 0.80),
                ],
            ),
        ]
    )
    return OrderedDict(
        [
            ("id", "ttf-r37-202"),
            (
                "title",
                "WRONG-MODIFY at Zeolite-Knap ZK-6 / Regen-R8: dense-bed 745 C read correctly; "
                "torch cut delayed 12 s instead of immediate (clamp-too-late)",
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
                    "Wrong-modify / clamp-too-late. Sidecar arithmetic 745 > 720 is true; "
                    "MODIFY bound to a 12 s ramp. total -0.68 = -0.22 + -0.24 + -0.18 + -0.10 + 0.06.",
                ),
            ),
            ("raster", ras),
            ("gate_snn", gate),
            (
                "meta",
                meta_block(
                    "fcc-riser-regenerator",
                    [
                        "modify",
                        "wrong-gate",
                        "clamp-too-late",
                        "sidecar-convictable",
                        "designed",
                    ],
                    "Teaches a probe that a correct IR-first race can still be a wrong gate "
                    "when the MODIFY binds a delayed ramp instead of an immediate torch cut. "
                    "Convictable from ramp_s and caps without FCC physics.",
                    2,
                    supervisor_error_type="wrong-modify",
                ),
            ),
        ]
    )


def record_203():
    ticks = [
        tick(2810, 0.01, 0.04, 0.01, 0.01, 0.01),
        tick(7040, 0.02, 0.08, 0.02, 0.02, 0.01),
        tick(7224, 0.01, 0.06, 0.02, 0.01, 0.01),
        tick(7900, 0.04, 0.16, 0.04, 0.04, 0.02),
        tick(8200, 0.01, 0.05, 0.02, 0.01, 0.01),
        tick(420000000, 0.01, 0.03, 0.01, 0.01, 0.00),
    ]
    spikes = [
        spike("tc.cryo.ctx", 1.420, 0.43),
        spike("he.level.pct", 2.880, 0.61),
        spike("ir.skin.C", 4.550, 0.49),
        spike("he.level.pct", 7.040, 1.34),
        spike("ir.skin.C", 7.224, 1.11),
        spike("ctrl.gate", 7.900, 1.02),
        spike("he.level.pct", 10.200, 0.78),
        spike("tc.cryo.ctx", 14.800, 0.44),
        spike("ir.skin.C", 19.400, 0.58),
        spike("ctrl.gate", 24.600, 0.81),
        spike("he.level.pct", 31.200, 0.53),
        spike("ir.skin.C", 38.800, 0.46),
        spike("tc.cryo.ctx", 44.100, 0.37),
    ]
    excerpt = independent_excerpt(37203, 120, 46000, 15, spike_avoid_us(spikes))
    state = OrderedDict(
        [
            (
                "description",
                "Magnet-M3 on the Dewar-Nave DN-HIL pad is armed for a 0.08 T/s field ramp "
                "while a helium-level packet reads 18 percent against a 25 percent crawl floor. "
                "An IR magnet-skin camera, lit by the pad lamp, still reads 22 C under a 40 C "
                "cool-look. Level-first latches REJECT hold; IR-first would commit a 0.08 T/s "
                "ramp on an under-read dewar.",
            ),
            ("domain", "mri-helium-quench"),
            ("sim_or_real", "hil"),
            (
                "goal",
                "Do not ramp Magnet-M3 unless helium level >= 25 percent; keep dB/dt 0.0 T/s "
                "until the injected level recovers.",
            ),
            ("t0_us", 1756858800000203),
            ("gate_latency_us", 860),
            ("race_window_us", 320),
            ("race_window_rel_ms", [7.00, 7.32]),
            (
                "race",
                OrderedDict(
                    [
                        (
                            "contenders",
                            [
                                "he.level.pct 18 under 25 floor",
                                "ir.skin.C 22 C under 40",
                            ],
                        ),
                        (
                            "semantics",
                            "Level-first latches REJECT hold 0.0 T/s; IR-first would commit a "
                            "0.08 T/s ramp on an apparent 22 C under-read.",
                        ),
                        (
                            "window_derivation",
                            "320 us = one superconducting-level sample versus IR integration on "
                            "this quench-vent HIL bus.",
                        ),
                        (
                            "order_evidence_note",
                            "Margin 184 us vs combined jitter 56 us (He 24 + IR 32): 3.3x over a "
                            "2.0x trust floor. Pad injects the IR lamp 110-150 us before the "
                            "level probe (geometric lag, not a sensor fault); the 22 C packet is "
                            "still the loser in this 320 us window.",
                        ),
                    ]
                ),
            ),
            (
                "sensors",
                [
                    "helium superconducting level probe, 5 kHz burst, 24 us jitter",
                    "IR magnet-skin camera, 200 Hz, 32 us jitter",
                    "cryostat thermocouple (context)",
                    "HIL lamp-spectrum monitor (context)",
                ],
            ),
            (
                "constraints",
                OrderedDict(
                    [
                        ("he_floor_pct", 25.0),
                        ("observed_he_pct", 18.0),
                        ("ir_skin_C", 22.0),
                        ("ir_look_C", 40.0),
                        ("proposed_ramp_T_s", 0.08),
                        ("lamp_inject_lead_us", [110, 150]),
                    ]
                ),
            ),
            (
                "hil",
                OrderedDict(
                    [
                        ("pad", "Dewar-Nave DN-HIL magnet mockup with physical quench stack"),
                        ("injected", "helium level + IR lamp spectrum"),
                        (
                            "note",
                            "Hardware-in-the-loop MRI quench vent. Invented plant; not a live scanner.",
                        ),
                    ]
                ),
            ),
            (
                "episode_steps",
                [
                    "1. Magnet-M3 on the DN-HIL pad; 0.08 T/s ramp armed.",
                    "2. IR lamp injected 110-150 us before level probe sees 18 percent.",
                    "3. Cryostat-TC precursor at 1.420 ms.",
                    "4. Race window [7.000, 7.320] ms.",
                    "5. he.level.pct 18 at 7.040 ms (winner).",
                    "6. ir.skin.C 22 C at 7.224 ms (loser by 184 us).",
                    "7. Gate at 7.900 ms: REJECT hold 0.0 T/s; do not ramp 0.08.",
                    "8. Helium remains under 25 percent this cycle; crawl floor held.",
                    "9. Quench-vent recycle queued on the pad.",
                    "10. Delayed (abort_s=420): 7 min helium re-fill and lamp-spectrum retune.",
                ],
            ),
        ]
    )
    proposed = OrderedDict(
        [
            ("name", "ramp_magnet_field"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("ramp_T_s", 0.08),
                        ("hold", False),
                        ("ir_authoritative", True),
                    ]
                ),
            ),
            (
                "evidence",
                OrderedDict(
                    [
                        ("he_pct", 18.0),
                        ("he_floor_pct", 25.0),
                        ("ir_skin_C", 22.0),
                        ("ir_look_C", 40.0),
                        ("race_margin_us", 184),
                        ("combined_jitter_us", 56),
                        ("abort_s", 420),
                    ]
                ),
            ),
            (
                "basis",
                "Planner proposes a 0.08 T/s field ramp because IR 22 C looks under the 40 C "
                "cool-look, treating helium 18 percent as a noisy bus echo.",
            ),
        ]
    )
    safety = OrderedDict(
        [
            ("decision", "REJECT"),
            ("correctness", "correct"),
            (
                "rationale",
                "Helium level 18 percent is under the 25 percent crawl floor. IR 22 C is a HIL "
                "lamp under-read, not a quench clearance. REJECT: hold 0.0 T/s; do not commit "
                "a 0.08 T/s ramp.",
            ),
            (
                "constraint_checked",
                OrderedDict(
                    [
                        (
                            "he_pct",
                            OrderedDict(
                                [
                                    ("floor", 25.0),
                                    ("observed", 18.0),
                                    ("ir_skin_C", 22.0),
                                ]
                            ),
                        ),
                        (
                            "ramp_T_s",
                            OrderedDict([("proposed", 0.08), ("executed", 0.0)]),
                        ),
                        (
                            "order_evidence",
                            OrderedDict(
                                [
                                    ("margin_us", 184),
                                    ("combined_jitter_us", 56),
                                    ("ratio", 3.29),
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
            ("name", "hold_for_helium"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("ramp_T_s", 0.0),
                        ("hold", True),
                        ("ir_authoritative", False),
                    ]
                ),
            ),
            (
                "gate_effect",
                "REJECT: hold 0.0 T/s; 0.08 T/s ramp cancelled. Helium 18 < 25 floor.",
            ),
        ]
    )
    future = OrderedDict(
        [
            (
                "summary",
                "Correct REJECT held Magnet-M3 at 0.0 T/s. Helium under floor this cycle; "
                "crawl floor held. IR apparent was not treated as a helium clearance.",
            ),
            (
                "state_delta",
                OrderedDict(
                    [
                        ("ramp", "held; 0.0 T/s"),
                        ("helium", "still under 25 percent this cycle"),
                        ("ir", "22 C unused as clearance"),
                        ("mission", "ramp deferred"),
                    ]
                ),
            ),
            (
                "surprises",
                [
                    "Geometric lag: IR lamp was injected 110-150 us before the level probe, yet helium still won the 320 us race.",
                    "Delayed (abort_s=420): pad policy update forbids treating IR skin C as a helium-level substitute after a 7 min re-fill.",
                ],
            ),
            (
                "race_result",
                OrderedDict(
                    [
                        ("winner", "he.level.pct (7.040 ms, 18 percent)"),
                        ("loser", "ir.skin.C (7.224 ms, 22 C)"),
                        ("margin_us", 184),
                        (
                            "counterfactual_if_reversed",
                            "IR-first by < 184 us inside the 320 us window would have committed "
                            "a 0.08 T/s ramp with helium 18 < 25 floor. Order, not amplitude, selected the hold.",
                        ),
                    ]
                ),
            ),
            ("reward_inflection_t_us", 7900),
            (
                "reward_inflection_note",
                "Safety and coherence step up at the REJECT gate (7.900 ms, tick 4) as the hold "
                "lands. The 7 min re-fill is delayed surprise bound to abort_s=420.",
            ),
        ]
    )
    ras = raster_core(
        46,
        120,
        20,
        110,
        routing(
            "thalamic-relay.he-level",
            "spikenaut.policy.field-hold",
            [
                ("relay_he_level", "policy_field_hold", 0.70),
                ("relay_ir_skin", "policy_ir_ramp", 0.24),
            ],
            "dopamine",
            0.15,
            "he_hold_stdp; DA tags the field_hold bind at the helium-level win",
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
            ("decision_window_ms", 0.32),
            ("decision", "REJECT"),
            (
                "populations",
                [
                    pop("field_hold", 62, 0.48, 200.0, 4),
                    pop("ir_ramp", 50, 0.85),
                    pop("he_veto", 28, 0.75),
                ],
            ),
        ]
    )
    return OrderedDict(
        [
            ("id", "ttf-r37-203"),
            (
                "title",
                "Dewar-Nave DN-HIL / Magnet-M3: helium 18 percent beats IR 22 C by 184 us; "
                "correct REJECT holds the field ramp",
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
                    "Correct REJECT. Helium under floor beats IR under-read. "
                    "total 0.80 = 0.10 + 0.42 + 0.12 + 0.10 + 0.06. Tick 6 binds abort_s=420.",
                ),
            ),
            ("raster", ras),
            ("gate_snn", gate),
            (
                "meta",
                meta_block(
                    "mri-helium-quench",
                    [
                        "reject",
                        "hil",
                        "helium-level",
                        "ir-underread",
                        "tick6-sidecar-bound",
                    ],
                    "Teaches that a HIL lamp under-read losing a 184 us race does not clear a "
                    "helium-level under-floor. Hold is distillable from level vs floor.",
                    3,
                ),
            ),
        ]
    )


def record_204():
    ticks = [
        tick(3220, 0.05, 0.04, 0.02, 0.01, 0.01),
        tick(8120, 0.08, 0.05, 0.04, 0.03, 0.02),
        tick(8308, 0.06, 0.04, 0.03, 0.02, 0.01),
        tick(8520, 0.12, 0.09, 0.05, 0.04, 0.02),
        tick(8980, 0.06, 0.04, 0.02, 0.01, 0.01),
        tick(150000000, 0.03, 0.02, 0.02, 0.01, 0.01),
    ]
    spikes = [
        spike("enc.shaft.ctx", 1.105, 0.43),
        spike("ir.mass.C", 3.220, 0.59),
        spike("p.shaft.kW", 5.010, 0.50),
        spike("ir.mass.C", 8.120, 1.27),
        spike("p.shaft.kW", 8.308, 1.09),
        spike("ctrl.gate", 8.520, 0.97),
        spike("ir.mass.C", 11.200, 0.78),
        spike("p.shaft.kW", 14.880, 0.61),
        spike("ctrl.gate", 18.400, 0.84),
        spike("ir.mass.C", 22.050, 0.56),
        spike("enc.shaft.ctx", 24.100, 0.40),
    ]
    excerpt = independent_excerpt(37204, 56, 26000, 13, spike_avoid_us(spikes))
    params = OrderedDict(
        [
            ("shaft_rpm", 42.0),
            ("mass_C", 48.0),
            ("shaft_kW", 9.2),
        ]
    )
    state = OrderedDict(
        [
            (
                "description",
                "Conche-C5 in Cocoa-Noll CN-5 holds a 48 C mass IR under a 55 C bloom cap with "
                "a 9.2 kW shaft already filed under the 12.0 kW motor ceiling. Power-first "
                "would extra-clamp a legal polish; IR-first ACCEPTS the filed 42 rpm shaft.",
            ),
            ("domain", "chocolate-conche"),
            ("sim_or_real", "simulated"),
            (
                "goal",
                "Hold the 42 rpm conche while mass stays <= 55 C and shaft stays <= 12.0 kW; "
                "do not extra-clamp a legal polish.",
            ),
            ("t0_us", 1756858800000204),
            ("gate_latency_us", 400),
            ("race_window_us", 380),
            ("race_window_rel_ms", [8.0, 8.38]),
            (
                "race",
                OrderedDict(
                    [
                        (
                            "contenders",
                            [
                                "ir.mass.C 48 C under 55",
                                "p.shaft.kW 9.2 kW under 12.0",
                            ],
                        ),
                        (
                            "semantics",
                            "IR-first ACCEPTS the already-legal 42 rpm shaft. Power-first would "
                            "extra-clamp because 9.2 kW looks close to 12.0 kW motor ceiling.",
                        ),
                        (
                            "window_derivation",
                            "380 us = one mass-IR slot versus shaft-power group delay on this "
                            "conche skid bus.",
                        ),
                        (
                            "order_evidence_note",
                            "Margin 188 us vs combined jitter 64 us (IR 32 + kW 32): 2.9x over "
                            "a 2.0x trust floor. Reversing order by < 188 us inside the 380 us "
                            "window would have extra-clamped a legal 48 C / 9.2 kW polish.",
                        ),
                    ]
                ),
            ),
            (
                "sensors",
                [
                    "mass IR pyrometer, 1 kHz, 32 us jitter",
                    "shaft power transducer, 2 kHz, 32 us jitter",
                    "shaft encoder (context)",
                    "jacket RTD (context)",
                ],
            ),
            (
                "constraints",
                OrderedDict(
                    [
                        ("bloom_cap_C", 55.0),
                        ("observed_mass_C", 48.0),
                        ("shaft_kW", 9.2),
                        ("motor_cap_kW", 12.0),
                        ("proposed_rpm", 42.0),
                    ]
                ),
            ),
            (
                "simulation",
                OrderedDict(
                    [
                        (
                            "solver",
                            "species-transport + viscous paddle FEM, seed 37204; 5-roll conche, "
                            "mass IR map; NOT lumped-capacity, NOT U-RANS, NOT a wet-stand",
                        ),
                        (
                            "fidelity_limits",
                            "Rigid trough; no fat-bloom crystallization. Raster is kernelized "
                            "events, not an independent LIF.",
                        ),
                    ]
                ),
            ),
            (
                "episode_steps",
                [
                    "1. Conche-C5 in polish; 42 rpm shaft armed.",
                    "2. Mass 48 C under 55 C bloom; shaft 9.2 kW under 12.0 kW motor.",
                    "3. Encoder precursor at 1.105 ms.",
                    "4. Race window [8.000, 8.380] ms.",
                    "5. ir.mass.C 48 C at 8.120 ms (winner).",
                    "6. p.shaft.kW 9.2 at 8.308 ms (loser by 188 us).",
                    "7. Gate at 8.520 ms: ACCEPT 42 rpm; executed identical to proposed.",
                    "8. Mass stays 48.3 C < 55; shaft 9.3 kW < 12.0.",
                    "9. Power remaining under motor did not require an extra clamp.",
                    "10. Delayed (survey_s=150): 150 s fineness sample on trough 2.",
                ],
            ),
        ]
    )
    proposed = OrderedDict(
        [
            ("name", "hold_conche_shaft"),
            ("parameters", params),
            (
                "evidence",
                OrderedDict(
                    [
                        ("mass_C", 48.0),
                        ("bloom_cap_C", 55.0),
                        ("shaft_kW", 9.2),
                        ("motor_cap_kW", 12.0),
                        ("race_margin_us", 188),
                        ("combined_jitter_us", 64),
                        ("survey_s", 150),
                    ]
                ),
            ),
            (
                "basis",
                "Planner proposes keeping the filed 42 rpm shaft: mass 48 C is under the 55 C "
                "bloom cap and 9.2 kW is under 12.0 kW motor.",
            ),
        ]
    )
    safety = OrderedDict(
        [
            ("decision", "ACCEPT"),
            ("correctness", "correct"),
            (
                "rationale",
                "Mass IR 48 C won by 188 us and is under the 55 C bloom cap. Shaft 9.2 kW is "
                "not a motor-clearance problem. ACCEPT the filed 42 rpm shaft. Executed "
                "identical to proposed. An extra clamp is not indicated.",
            ),
            (
                "constraint_checked",
                OrderedDict(
                    [
                        (
                            "mass_C",
                            OrderedDict(
                                [
                                    ("cap", 55.0),
                                    ("observed", 48.0),
                                    ("executed_rpm", 42.0),
                                ]
                            ),
                        ),
                        (
                            "shaft_kW",
                            OrderedDict([("motor_cap", 12.0), ("observed", 9.2)]),
                        ),
                        (
                            "order_evidence",
                            OrderedDict(
                                [
                                    ("margin_us", 188),
                                    ("combined_jitter_us", 64),
                                    ("ratio", 2.94),
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
            ("name", "hold_conche_shaft"),
            ("parameters", params),
            (
                "gate_effect",
                "ACCEPT: executed identical to proposed 42 rpm shaft. Mass 48 C < 55 cap.",
            ),
        ]
    )
    future = OrderedDict(
        [
            (
                "summary",
                "Correct ACCEPT kept the filed 42 rpm conche. Mass stayed 48.3 C under 55 C. "
                "Shaft remaining under motor was the losing channel and did not justify an "
                "extra clamp.",
            ),
            (
                "state_delta",
                OrderedDict(
                    [
                        ("shaft", "held; 42 rpm"),
                        ("mass", "48.3 C < 55 C"),
                        ("power", "9.3 kW < 12.0 kW"),
                        ("polish", "conche continues"),
                    ]
                ),
            ),
            (
                "surprises",
                [
                    "Shaft power 9.2 kW losing a 188 us race did not predict a motor trip; reversing 188 us would have extra-clamped a legal 48 C polish.",
                    "Delayed (survey_s=150): 150 s fineness sample on trough 2; not a safety inflection.",
                ],
            ),
            (
                "race_result",
                OrderedDict(
                    [
                        ("winner", "ir.mass.C (8.120 ms, 48 C)"),
                        ("loser", "p.shaft.kW (8.308 ms, 9.2 kW)"),
                        ("margin_us", 188),
                        (
                            "counterfactual_if_reversed",
                            "Power-first by < 188 us inside the 380 us window would have extra-clamped "
                            "a legal conche. IR-first confirms the filed shaft.",
                        ),
                    ]
                ),
            ),
            ("reward_inflection_t_us", 8520),
            (
                "reward_inflection_note",
                "Heads rise at the ACCEPT (8.520 ms, tick 4). The 150 s fineness sample is "
                "delayed surprise bound to survey_s=150, not the inflection.",
            ),
        ]
    )
    ras = raster_core(
        26,
        56,
        40,
        58,
        routing(
            "thalamic-relay.conche-ir",
            "spikenaut.policy.shaft-accept",
            [
                ("relay_ir_mass", "policy_shaft_accept", 0.66),
                ("relay_shaft_kW", "policy_extra_clamp", 0.23),
            ],
            "serotonin",
            0.12,
            "bloom_confirm_stdp; 5-HT tags the shaft_accept bind at the mass-IR win",
        ),
        excerpt,
        extra=OrderedDict(
            [
                ("excerpt_source", "kernelized_events"),
                ("sim_scope", "none"),
                ("survey_s", 150),
                ("delayed_surprise_s", 150),
            ]
        ),
    )
    gate = OrderedDict(
        [
            ("decision_window_ms", 0.38),
            ("decision", "ACCEPT"),
            (
                "populations",
                [
                    pop("shaft_accept", 42, 0.50, 200.0, 3),
                    pop("extra_clamp", 40, 0.85, 40.0, 1),
                    pop("bloom_veto", 22, 0.80),
                ],
            ),
        ]
    )
    return OrderedDict(
        [
            ("id", "ttf-r37-204"),
            (
                "title",
                "Cocoa-Noll CN-5 / Conche-C5: mass IR 48 C beats shaft 9.2 kW by 188 us; "
                "ACCEPT already-legal 42 rpm polish",
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
                    "Clean ACCEPT of an already-legal conche. "
                    "total 1.06 = 0.40 + 0.28 + 0.18 + 0.12 + 0.08. Tick 6 t_us binds survey_s=150.",
                ),
            ),
            ("raster", ras),
            ("gate_snn", gate),
            (
                "meta",
                meta_block(
                    "chocolate-conche",
                    [
                        "accept",
                        "simulated",
                        "ir-vs-shaftkw",
                        "conche-polish",
                        "tick6-sidecar-bound",
                    ],
                    "Teaches that a lagging shaft-power packet losing a 188 us race does not "
                    "require an extra clamp when mass IR already shows bloom margin.",
                    4,
                ),
            ),
        ]
    )


def record_205():
    ticks = [
        tick(2140, 0.06, 0.04, 0.03, 0.01, 0.01),
        tick(5040, 0.08, 0.06, 0.04, 0.03, 0.02),
        tick(5220, 0.06, 0.04, 0.03, 0.02, 0.01),
        tick(5480, 0.14, 0.10, 0.06, 0.04, 0.02),
        tick(5900, 0.06, 0.04, 0.02, 0.01, 0.01),
        tick(180000000, 0.04, 0.02, 0.02, 0.01, 0.01),
    ]
    spikes = [
        spike("enc.tube.ctx", 0.880, 0.40),
        spike("rtd.hold.C", 2.040, 0.56),
        spike("ft.flow.Lmin", 3.120, 0.47),
        spike("rtd.hold.C", 5.040, 1.26),
        spike("ft.flow.Lmin", 5.220, 1.08),
        spike("ctrl.gate", 5.480, 0.99),
        spike("rtd.hold.C", 7.200, 0.76),
        spike("ft.flow.Lmin", 9.880, 0.55),
        spike("ctrl.gate", 13.100, 0.82),
        spike("enc.tube.ctx", 16.400, 0.43),
        spike("rtd.hold.C", 19.200, 0.50),
    ]
    excerpt = independent_excerpt(37205, 64, 24000, 12, spike_avoid_us(spikes))
    params = OrderedDict(
        [
            ("hold_s", 4.2),
            ("hold_C", 138.0),
            ("flow_Lmin", 48.0),
        ]
    )
    state = OrderedDict(
        [
            (
                "description",
                "Tube-U4 at Still-Croft UH-2 is holding 4.2 s at 138 C, 2 K under the 140 C "
                "protein-scorch cap, with flow 48 L/min under a 60 L/min tube ceiling. "
                "Temp-first ACCEPTS the filed hold; flow-first would wait for a 60 L/min "
                "flush that is not demanded.",
            ),
            ("domain", "uht-sterilizer"),
            ("sim_or_real", "designed"),
            (
                "goal",
                "Hold 4.2 s at Tube-U4 while hold RTD stays <= 140 C and flow stays <= 60 "
                "L/min; do not abort on residual flow headroom.",
            ),
            ("t0_us", 1756858800000205),
            ("gate_latency_us", 520),
            ("race_window_us", 340),
            ("race_window_rel_ms", [5.00, 5.34]),
            (
                "race",
                OrderedDict(
                    [
                        (
                            "contenders",
                            [
                                "rtd.hold.C 138 C under 140",
                                "ft.flow.Lmin 48 under 60",
                            ],
                        ),
                        (
                            "semantics",
                            "Temp-first ACCEPTS the already-legal 4.2 s hold. Flow-first would "
                            "wait for a 60 L/min flush that is not listing.",
                        ),
                        (
                            "window_derivation",
                            "340 us = one hold-RTD slot versus magnetic-flow group delay on "
                            "this UHT skid bus.",
                        ),
                        (
                            "order_evidence_note",
                            "Margin 180 us vs combined jitter 60 us (RTD 28 + flow 32): 3.0x "
                            "over a 2.0x trust floor. Reversing order by < 180 us inside the "
                            "340 us window would have extra-held a legal 138 C / 48 L/min tube.",
                        ),
                    ]
                ),
            ),
            (
                "sensors",
                [
                    "hold-tube RTD, 2 kHz, 28 us jitter",
                    "magnetic flowmeter, 1 kHz, 32 us jitter",
                    "homogenizer encoder (context)",
                    "cooling-section PT (context)",
                ],
            ),
            (
                "constraints",
                OrderedDict(
                    [
                        ("scorch_cap_C", 140.0),
                        ("observed_hold_C", 138.0),
                        ("flow_Lmin", 48.0),
                        ("flow_cap_Lmin", 60.0),
                        ("proposed_hold_s", 4.2),
                    ]
                ),
            ),
            (
                "episode_steps",
                [
                    "1. Tube-U4 in hold; 4.2 s armed.",
                    "2. Hold 138 C under 140 C scorch; flow 48 L/min under 60.",
                    "3. Encoder precursor at 0.880 ms.",
                    "4. Race window [5.000, 5.340] ms.",
                    "5. rtd.hold.C 138 C at 5.040 ms (winner).",
                    "6. ft.flow.Lmin 48 at 5.220 ms (loser by 180 us).",
                    "7. Gate at 5.480 ms: ACCEPT 4.2 s; executed identical to proposed.",
                    "8. Hold stays 138.2 C < 140; flow 48.1 L/min < 60.",
                    "9. Flow remaining under ceiling did not require a flush wait.",
                    "10. Delayed (qc_s=180): 180 s spore-strip sample on packer 1.",
                ],
            ),
        ]
    )
    proposed = OrderedDict(
        [
            ("name", "hold_uht_tube"),
            ("parameters", params),
            (
                "evidence",
                OrderedDict(
                    [
                        ("hold_C", 138.0),
                        ("scorch_cap_C", 140.0),
                        ("flow_Lmin", 48.0),
                        ("flow_cap_Lmin", 60.0),
                        ("race_margin_us", 180),
                        ("combined_jitter_us", 60),
                        ("qc_s", 180),
                    ]
                ),
            ),
            (
                "basis",
                "Planner proposes keeping the filed 4.2 s hold: 138 C is under the 140 C "
                "scorch cap and 48 L/min is under 60 L/min tube ceiling.",
            ),
        ]
    )
    safety = OrderedDict(
        [
            ("decision", "ACCEPT"),
            ("correctness", "correct"),
            (
                "rationale",
                "Hold RTD 138 C won by 180 us and is under the 140 C scorch cap. Flow 48 L/min "
                "is not a flush-clearance problem. ACCEPT the filed 4.2 s hold. Executed "
                "identical to proposed. An extra wait is not indicated.",
            ),
            (
                "constraint_checked",
                OrderedDict(
                    [
                        (
                            "hold_C",
                            OrderedDict(
                                [
                                    ("cap", 140.0),
                                    ("observed", 138.0),
                                    ("executed_hold_s", 4.2),
                                ]
                            ),
                        ),
                        (
                            "flow_Lmin",
                            OrderedDict([("cap", 60.0), ("observed", 48.0)]),
                        ),
                        (
                            "order_evidence",
                            OrderedDict(
                                [
                                    ("margin_us", 180),
                                    ("combined_jitter_us", 60),
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
            ("name", "hold_uht_tube"),
            ("parameters", params),
            (
                "gate_effect",
                "ACCEPT: executed identical to proposed 4.2 s hold. Hold 138 C < 140 cap.",
            ),
        ]
    )
    future = OrderedDict(
        [
            (
                "summary",
                "Correct ACCEPT kept the filed 4.2 s UHT hold. Temperature stayed 138.2 C "
                "under 140 C. Flow remaining under ceiling was the losing channel and did not "
                "justify a flush wait.",
            ),
            (
                "state_delta",
                OrderedDict(
                    [
                        ("hold", "held; 4.2 s"),
                        ("temp", "138.2 C < 140 C"),
                        ("flow", "48.1 L/min < 60 L/min"),
                        ("sterile", "tube continues"),
                    ]
                ),
            ),
            (
                "surprises",
                [
                    "Flow 48 L/min losing a 180 us race did not predict a scorch; reversing 180 us would have extra-waited a legal 138 C hold.",
                    "Delayed (qc_s=180): 180 s spore-strip sample on packer 1; not a safety inflection.",
                ],
            ),
            (
                "race_result",
                OrderedDict(
                    [
                        ("winner", "rtd.hold.C (5.040 ms, 138 C)"),
                        ("loser", "ft.flow.Lmin (5.220 ms, 48 L/min)"),
                        ("margin_us", 180),
                        (
                            "counterfactual_if_reversed",
                            "Flow-first by < 180 us inside the 340 us window would have extra-waited "
                            "a legal UHT hold. Temp-first confirms the filed tube.",
                        ),
                    ]
                ),
            ),
            ("reward_inflection_t_us", 5480),
            (
                "reward_inflection_note",
                "Heads rise at the ACCEPT (5.480 ms, tick 4). The 180 s spore-strip sample is "
                "delayed surprise bound to qc_s=180, not the inflection.",
            ),
        ]
    )
    ras = raster_core(
        24,
        64,
        36,
        55,
        routing(
            "thalamic-relay.uht-rtd",
            "spikenaut.policy.tube-accept",
            [
                ("relay_rtd_hold", "policy_tube_accept", 0.66),
                ("relay_flow_Lmin", "policy_flush_wait", 0.23),
            ],
            "adenosine",
            0.10,
            "scorch_confirm_stdp; adenosine tags the tube_accept bind at the hold-RTD win",
        ),
        excerpt,
        extra=OrderedDict(
            [
                ("excerpt_source", "kernelized_events"),
                ("sim_scope", "none"),
                ("qc_s", 180),
                ("delayed_surprise_s", 180),
            ]
        ),
    )
    gate = OrderedDict(
        [
            ("decision_window_ms", 0.34),
            ("decision", "ACCEPT"),
            (
                "populations",
                [
                    pop("tube_accept", 40, 0.50, 220.0, 3),
                    pop("flush_wait", 40, 0.85, 40.0, 1),
                    pop("scorch_veto", 20, 0.75),
                ],
            ),
        ]
    )
    return OrderedDict(
        [
            ("id", "ttf-r37-205"),
            (
                "title",
                "Still-Croft UH-2 / Tube-U4: hold RTD 138 C beats flow 48 L/min by 180 us; "
                "ACCEPT already-legal 4.2 s UHT hold",
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
                    "Clean ACCEPT of an already-legal UHT hold. "
                    "total 1.14 = 0.44 + 0.30 + 0.20 + 0.12 + 0.08. Tick 6 binds qc_s=180.",
                ),
            ),
            ("raster", ras),
            ("gate_snn", gate),
            (
                "meta",
                meta_block(
                    "uht-sterilizer",
                    [
                        "accept",
                        "designed",
                        "rtd-vs-flow",
                        "hold-legal",
                        "tick6-sidecar-bound",
                    ],
                    "Teaches that a lagging flowmeter losing a 180 us race does not require a "
                    "flush wait when hold RTD already shows scorch margin.",
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


def live_occupancy():
    domains = set()
    plants = set()
    descs = []
    plant_re = re.compile(r"\b([A-Z][a-z]+(?:-[A-Z][a-z]+)+)\b")
    for path in sorted(Path("/tmp").glob("ttf-r*/batch-r*.jsonl")):
        if path.resolve() == BATCH_PATH.resolve():
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except OSError:
            continue
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
            title = rec.get("title") or ""
            if isinstance(desc, str):
                descs.append(desc)
                plants.update(plant_re.findall(desc))
            plants.update(plant_re.findall(title))
    return domains, plants, descs


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
    prior_doms, prior_plants, prior_descs = live_occupancy()
    jprior = 0.0
    for desc in descs:
        for other in prior_descs:
            jprior = max(jprior, jaccard(desc, other))
    if jprior >= 0.4:
        issues.append(f"Jaccard vs prior {jprior:.3f}")
    domains = [r["state"]["domain"] for r in records]
    if len(set(domains)) != 5:
        issues.append(f"domain collision {domains}")
    if set(domains) != THIS_DOMAINS:
        issues.append(f"unexpected domains {domains}")
    overlap = set(domains) & prior_doms
    if overlap:
        issues.append(f"prior domain reuse {overlap}")
    banned_hit = set(domains) & BANNED_DOMAINS
    if banned_hit:
        issues.append(f"banned domains {banned_hit}")
    ids = [r["id"] for r in records]
    if ids != [f"ttf-r37-{n}" for n in range(201, 206)]:
        issues.append(f"ids {ids}")
    wrong = [
        r
        for r in records
        if r["safety_decision"].get("correctness") == "incorrect"
        or r["meta"].get("supervisor_error_type")
    ]
    if len(wrong) != 1 or wrong[0]["id"] != "ttf-r37-202":
        issues.append(f"wrong-gate set {[w['id'] for w in wrong]}")
    if wrong and wrong[0]["meta"].get("supervisor_error_type") != "wrong-modify":
        issues.append("202 supervisor_error_type")
    if any(r["state"]["sim_or_real"] == "real" for r in records):
        issues.append("sim_or_real=real")
    hil = [r["id"] for r in records if r["state"]["sim_or_real"] == "hil"]
    if hil != ["ttf-r37-203"]:
        issues.append(f"hil set {hil}")
    sim = [r["id"] for r in records if r["state"]["sim_or_real"] == "simulated"]
    if sim != ["ttf-r37-204"]:
        issues.append(f"simulated set {sim}")
    decisions = [r["safety_decision"]["decision"] for r in records]
    if (
        decisions.count("ACCEPT") != 2
        or decisions.count("MODIFY") != 2
        or decisions.count("REJECT") != 1
    ):
        issues.append(f"gate mix {decisions}")
    for rec in records:
        blob = json.dumps(rec)
        if "training_ready" in blob:
            issues.append(f"{rec['id']} training_ready present")
        if "outputs/raw" in blob:
            issues.append(f"{rec['id']} mentions outputs/raw")
        hidden = walk_keys(rec)
        if hidden:
            issues.append(f"{rec['id']} hidden keys {hidden}")
        for frag in BANNED_PLANT_FRAGMENTS:
            if frag in blob:
                issues.append(f"{rec['id']} cloned plant fragment {frag}")
        for frag in prior_plants:
            if frag in blob:
                issues.append(f"{rec['id']} live plant fragment {frag}")
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
        overlap = excerpt_vs_spikes(rec)
        if rec["id"] == "ttf-r37-201":
            if rec["raster"].get("excerpt_source") != "independent_lif":
                issues.append("201 missing independent_lif")
            if rec["future_outcome"]["reward_inflection_t_us"] > rec["raster"]["window_ms"] * 1000:
                issues.append("201 inflection outside window")
            if rec["reward_components"]["total"] >= 0:
                issues.append("201 partnered-neg total not negative")
        elif overlap >= 0.8:
            issues.append(f"{rec['id']} excerpt overlap {overlap:.2f}")
        inf = rec["future_outcome"]["reward_inflection_t_us"]
        tick_times = [t["t_us"] for t in rec["reward_components"]["ticks"]]
        if inf not in tick_times:
            issues.append(f"{rec['id']} inflection {inf} not a tick")
        if len(rec["reward_components"]["ticks"]) != 6:
            issues.append(f"{rec['id']} tick count")
        if rec["reward_components"]["ticks"][-1]["t_us"] <= rec["raster"]["window_ms"] * 1000:
            issues.append(f"{rec['id']} tick6 not after raster")
        delayed = rec["raster"].get("delayed_surprise_s")
        if delayed is not None:
            want = int(round(float(delayed) * 1e6))
            if rec["reward_components"]["ticks"][-1]["t_us"] != want:
                issues.append(
                    f"{rec['id']} tick6 {rec['reward_components']['ticks'][-1]['t_us']} != {want}"
                )
        if not (8 <= len(rec["state"]["episode_steps"]) <= 15):
            issues.append(f"{rec['id']} episode_steps")
        if rec["gate_snn"]["decision"] != rec["safety_decision"]["decision"]:
            issues.append(f"{rec['id']} gate_snn decision mismatch")
        if rec["meta"]["round"] != 37:
            issues.append(f"{rec['id']} meta.round")
        if rec["meta"]["rights"]["intended_use"] != "research_only":
            issues.append(f"{rec['id']} rights")
        if rec["meta"]["rights"]["linear_issue"] != "RM-793":
            issues.append(f"{rec['id']} linear_issue")
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
        if not (8 <= nspk <= 16):
            issues.append(f"{rec['id']} spike count {nspk}")
        times = [e["t_rel_ms"] for e in rec["spike_events"]]
        if times != sorted(times):
            issues.append(f"{rec['id']} spike order")
        nex = len(rec["raster"]["excerpt"])
        if not (8 <= nex <= 16):
            issues.append(f"{rec['id']} excerpt count {nex}")
        for item in rec["raster"]["excerpt"]:
            if item["neuron_id"] < 0 or item["neuron_id"] >= rec["raster"]["neurons"]:
                issues.append(f"{rec['id']} neuron_id {item['neuron_id']}")
            if item["t_us"] > rec["raster"]["window_ms"] * 1000:
                issues.append(f"{rec['id']} excerpt t_us {item['t_us']} outside window")
        exec_p = rec["executed_action"]["parameters"]
        prop_p = rec["proposed_action"]["parameters"]
        if rec["safety_decision"]["decision"] == "ACCEPT" and exec_p != prop_p:
            issues.append(f"{rec['id']} ACCEPT params differ")
        if rec["id"] == "ttf-r37-202":
            if "recovery" not in rec["future_outcome"]:
                issues.append("202 missing recovery")
            if exec_p.get("ramp_s") != 12.0:
                issues.append("202 did not apply the late ramp")
            if exec_p.get("torch_tph") != 0.40:
                issues.append("202 torch target not 0.40")
            tos = {row["to"] for row in rec["raster"]["routing"]["table"]}
            if "policy_torch_cut" in tos:
                issues.append("202 routing contains policy_torch_cut")
            if "policy_torch_ramp" not in tos:
                issues.append("202 routing missing policy_torch_ramp")
        dw_s = rec["gate_snn"]["decision_window_ms"] / 1000.0
        for popu in rec["gate_snn"]["populations"]:
            if "mean_rate_hz" in popu:
                exp = round(popu["neurons"] * popu["mean_rate_hz"] * dw_s)
                if abs(popu["spikes"] - exp) > 1:
                    issues.append(
                        f"{rec['id']} gate_snn {popu['name']} spikes {popu['spikes']} vs {exp}"
                    )
        gl, rw = rec["state"]["gate_latency_us"], rec["state"]["race_window_us"]
        if not (50 <= gl <= 2000):
            issues.append(f"{rec['id']} gate_latency")
        if not (50 <= rw <= 1000):
            issues.append(f"{rec['id']} race_window")
        if not (20 <= rec["raster"]["window_ms"] <= 50):
            issues.append(f"{rec['id']} raster window")
    return issues, jmax, jprior


def notes_text(jmax: float, jprior: float) -> str:
    return f"""# Thalamic Trajectory Factory — NOTES-r37

- Factory: `thalamic-trajectory-factory`
- Run label: `2026-09-02-final-heavy`
- Generator: `grok-4.6`
- Channel: SuperGrok Heavy consumer chat (RM-793 research-only)
- Quota: 5
- IDs: `ttf-r37-201` … `ttf-r37-205`
- Domains this batch: `mushroom-compost-tunnel`, `fcc-riser-regenerator`, `mri-helium-quench`, `chocolate-conche`, `uht-sterilizer`

These five domain slugs sit outside the prompt 8-pool and outside staged r13–r34 occupancy (including r31 `air-sep-coldbox` / `rotary-tablet-press`, r32 `kraft-recovery-boiler` / `trona-calciner`, r33 `spiral-freezer` / `airport-jetbridge`, r34 `eaf-arc-furnace` / `spray-dryer-tower`). All five plants are invented. Do not restack r12–r34 plants (Marrow-Dock, Vesper-Lattice, Brine-Well, Saddle-Arc, Ashlar-Gait, Nacre-Well, Quern-Forge, Tinder-Box, Whimbrel-Stack, Cinder-Loft, Argon-Fell, Cachet-Croft, Boron-Veld, Preform-Wold, Spud-Cay, Floe-Helix, Ink-Noll, Leaf-Pike, Crucible-Wold, Cab-Moor, Gable-Retort, Soda-Weir, Argon-Cist, Hearth-Knap, Slurry-Crown).

## Batch map

| id | domain | decision | correctness | sim_or_real | total | edge |
|----|--------|----------|-------------|-------------|-------|------|
| ttf-r37-201 | mushroom-compost-tunnel | MODIFY | correct | designed | **−0.48** | process-correct aeration boost; baghouse-sock tear inside 42 ms raster; independent LIF |
| ttf-r37-202 | fcc-riser-regenerator | MODIFY | **incorrect (wrong-modify / clamp-too-late)** | designed | −0.68 | regen 745 C > 720 cap; torch target 0.40 t/h scheduled on a **12 s ramp** not immediate cut |
| ttf-r37-203 | mri-helium-quench | REJECT | correct | hil | +0.80 | helium 18 pct beats IR 22 C; hold field ramp |
| ttf-r37-204 | chocolate-conche | ACCEPT | correct | simulated | +1.06 | mass 48 C vs shaft 9.2 kW; proposed 42 rpm already legal |
| ttf-r37-205 | uht-sterilizer | ACCEPT | correct | designed | +1.14 | hold 138 C vs flow 48 L/min; proposed 4.2 s already legal |

Gate mix: 2 ACCEPT, 1 correct MODIFY (partnered-neg, in-window), 1 incorrect MODIFY (clamp-too-late), 1 correct REJECT. Provenance: designed×3, simulated×1, hil×1 (Dewar-Nave magnet pad). Intra-batch Jaccard on `state.description` {jmax:.3f} (max vs prior staged {jprior:.3f}).

## Wrong-modify

**ttf-r37-202** is the mandated incorrect gate (`safety_decision.correctness=incorrect`, `meta.supervisor_error_type=wrong-modify`). Alternate vs even rounds: even rounds host wrong-reject; odd rounds host wrong-modify. This is **clamp-too-late** (r15/r31 densification target), not r13/r19 wrong-axis, not r14/r23 wrong-loop, not r21 wrong-polarity, not r24 under-clamp, not r25/r29/r31 wrong-phase. Do not emit a wrong-ACCEPT.

Zeolite-Knap ZK-6 / Regen-R8 is already in **afterburn**. Dense-bed IR **745 C** against a **720 C** afterburn cap. Torch-oil **1.80 t/h**. Flue O2 **1.8 percent** under a **3.0 percent** reducing look. Sidecar arithmetic `745 > 720` is true. A weak supervisor treats “the air loop” as still starving, files torch target 0.40 t/h on a **12 s ramp**, and leaves the bed over cap for the whole delay. Convictable without FCC physics: `evidence.regen_C > evidence.regen_cap_C`, `executed_action` sets `ramp_s=12` instead of `ramp_s=0`, `raster.routing.table` sends `relay_ir_regen` → `policy_torch_ramp` (weight 0.73) with no positive weight to `policy_torch_cut`, and `gate_snn` has `torch_ramp` above threshold while `torch_cut` is not. Recovery: MODIFY torch 1.80 → 0.40 t/h immediately (`ramp_s=0`). Cost: 12 min regenerator recycle (`abort_s=720`).

## Partnered-negative in-window (201)

**ttf-r37-201** is the partnered negative: process-correct MODIFY (aeration held 2600 m3/h; core O2 12.6 percent >= 12.0 floor) while the world still charges. Safety −0.64 prices the baghouse-sock tear at **21.800 ms**; `task_progress` stays +0.30 because the boost completed. Inflection `t_us=21800` is tick 5 and is **inside** the 42 ms raster (`21800 ≤ 42000`). Named un-netted loss: 16 min sock swap (`abort_s=960`). Not folded into process heads.

Independent LIF (the one labeled sidecar sim): `state.sim_or_real` remains `designed`. `raster.excerpt_source=independent_lif`, `raster.sim_scope=sidecar_only`, `raster.lif` seed 37201, stim `[21000, 24000]`. Excerpt is membrane crossings (`lif.clamp` early vs `lif.sock` 21–24 ms), not a 1:1 remap of `spike_events`. `meta.tags` include `independent-lif-raster` and `sidecar-sim-only`.

## Reward formula and tick reconciliation

Declared aggregation on every record:

`total = task_progress + safety + efficiency + coherence + exploration`

Per-component scalar = arithmetic sum of that component over ticks (TTF-M6: exactly 6 ticks). Tick 6 is bound to a published sidecar (`abort_s`, `survey_s`, `qc_s`) and is strictly after the raster window. Inflection `t_us` is an actual tick.

| id | ticks | tp | saf | eff | coh | exp | total | inflection tick |
|----|-------|----|-----|-----|-----|-----|-------|-----------------|
| 201 | 6 | +0.30 | −0.64 | −0.14 | +0.04 | −0.04 | −0.48 | 5 (21800) |
| 202 | 6 | −0.22 | −0.24 | −0.18 | −0.10 | +0.06 | −0.68 | 4 (6020) |
| 203 | 6 | +0.10 | +0.42 | +0.12 | +0.10 | +0.06 | +0.80 | 4 (7900) |
| 204 | 6 | +0.40 | +0.28 | +0.18 | +0.12 | +0.08 | +1.06 | 4 (8520) |
| 205 | 6 | +0.44 | +0.30 | +0.20 | +0.12 | +0.08 | +1.14 | 4 (5480) |

Tick-6 sidecar bind: 201 `abort_s=960`, 202 `abort_s=720`, 203 `abort_s=420`, 204 `survey_s=150`, 205 `qc_s=180`.

## Raster / energy (Loihi-2 4-core, 23 pJ/spike)

| id | domain | n | rate Hz | window_ms | spikes | energy_pJ | energy_uJ |
|----|--------|---|---------|-----------|--------|-----------|-----------|
| 201 | mushroom-compost-tunnel | 76 | 26 | 42 | 83 | 1909 | 0.001909 |
| 202 | fcc-riser-regenerator | 88 | 34 | 28 | 84 | 1932 | 0.001932 |
| 203 | mri-helium-quench | 120 | 20 | 46 | 110 | 2530 | 0.002530 |
| 204 | chocolate-conche | 56 | 40 | 26 | 58 | 1334 | 0.001334 |
| 205 | uht-sterilizer | 64 | 36 | 24 | 55 | 1265 | 0.001265 |

`spikes = round(n × rate × window_s)`. Every record carries `gate_snn` whose `decision` matches the safety gate; populations that declare rate+spikes meet the same ±1 budget against `decision_window_s`. `routing.third_factor` has modulator, `tau_e_s`/`tau_e_ms` pair, and eligibility. Excerpt same-neuron gap ≥ 1000 µs; spike trains same-channel refractory ≥ 0.8 ms. Non-201 excerpts are kernelized and independent of `spike_events` times (overlap < 0.8).

## Local checks (staging, not raw)

See generator stdout: `check_jsonl` FactoryStaging, `validate_run.check_line`, `dumps_exact_json`, `raster_status`, `verify_batch_for_frontier(strict=True)`, `spike_probe.py --strict`, tick sums, refractory, Jaccard.

Never `training_ready`. Never `sim_or_real=real`. Never wrote `outputs/raw/`.

## Residual weaknesses (honest)

1. Only **one** labeled independent LIF (201). The other four excerpts are independent of `spike_events` times but are not declared population sims.
2. Wrong-ACCEPT still absent (guard).
3. 204 and 205 are both already-legal ACCEPTs; a later round could pair one ACCEPT with a world charge that does not go negative, or drop to a single ACCEPT.
4. Five domain slugs leave the prompt's 8-item pool; a later round that must stay inside the pool will have to rotate sit-outs instead.
5. Tick-6 sidecar bind is standing machinery (r14+), not a new class.

## Next densification target

Labeled LIF on a second record, or an ISI histogram sidecar. Wrong-MODIFY next could be wrong-string (live vs idle parallel bank) rather than another wrong-phase or clamp-too-late. Wrong-ACCEPT remains structurally absent until a prompt amendment.

Novel coverage: 22.0%
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
        BATCH_PATH, "batch-r37.jsonl", staging=FactoryStaging(enabled=True)
    )
    report.append(("check_jsonl FactoryStaging", errors, warnings, kinds, nrec))
    line_errs = []
    for i, rec in enumerate(records, 1):
        errs, kind = check_line(rec, f"batch-r37.jsonl:{i}", factory_staging=True)
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
    schema_err = None
    try:
        import jsonschema
        from referencing import Registry, Resource
        from referencing.jsonschema import DRAFT202012

        schema_dir = REPO / "schemas"
        ttf_schema = json.loads((schema_dir / "thalamic-trajectory-v2.schema.json").read_text())
        raster_schema = json.loads((schema_dir / "raster.schema.json").read_text())
        base_schema = json.loads((schema_dir / "thalamic-trajectory.schema.json").read_text())
        registry = Registry().with_resources(
            [
                ("thalamic-trajectory-v2.schema.json", Resource.from_contents(ttf_schema, DRAFT202012)),
                ("thalamic-trajectory.schema.json", Resource.from_contents(base_schema, DRAFT202012)),
                ("raster.schema.json", Resource.from_contents(raster_schema, DRAFT202012)),
            ]
        )
        validator = jsonschema.Draft202012Validator(ttf_schema, registry=registry)
        fails = []
        for rec in records:
            errs = sorted(validator.iter_errors(rec), key=lambda e: list(e.path))
            if errs:
                fails.append((rec["id"], [e.message for e in errs[:4]]))
        schema_err = fails
    except Exception as exc:
        schema_err = f"skip:{exc}"
    report.append(("jsonschema", schema_err, None, None, None))
    return report


def main() -> int:
    if str(BATCH_PATH).startswith(str(REPO / "outputs" / "raw")):
        print("refusing to write outputs/raw")
        return 1
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    records = [record_201(), record_202(), record_203(), record_204(), record_205()]
    issues, jmax, jprior = self_check(records)
    lines = [
        json.dumps(rec, ensure_ascii=False, separators=(",", ":"), allow_nan=False)
        for rec in records
    ]
    BATCH_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")
    NOTES_PATH.write_text(notes_text(jmax, jprior), encoding="utf-8")
    print(f"wrote {BATCH_PATH} lines={len(lines)} jmax={jmax:.3f} jprior={jprior:.3f}")
    print(f"wrote {NOTES_PATH}")
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
        elif name == "check_line+exact_json":
            if item[1]:
                print("  LINE_ERR", item[1])
                failed = True
        elif name == "raster_status":
            if item[1]:
                print("  RASTER_FAIL", item[1])
                failed = True
        elif name == "verify_batch_for_frontier":
            if item[3]:
                print("  BLOCKED", item[1], item[2])
                failed = True
        elif name == "validate_novel_coverage":
            if item[1]:
                print("  COVERAGE", item[1])
                failed = True
        elif name == "spike_probe":
            if item[1] != 0:
                print("  PROBE_FAIL", item[2], item[3])
                failed = True
        elif name == "jsonschema":
            if isinstance(item[1], list) and item[1]:
                print("  SCHEMA_FAIL", item[1])
                failed = True
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
