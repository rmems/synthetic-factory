def lif_227_excerpt():
    """Independent CUBA LIF (seed 42227). Plant remains designed."""

    n = 84
    dt_us = 100
    tau_m_ms = 20.0
    v_th = 1.0
    v_reset = 0.0
    refractory_us = 1000
    i_bias = 0.92
    i_stim_peak = 2.45
    stim = (21000, 25000)
    seed = 42227
    window_us = 40000
    i_clamp_extra = 0.68
    clamp_n = 14
    rng = random.Random(seed)
    tau_s = tau_m_ms / 1000.0
    dt_s = dt_us / 1e6
    decay = math.exp(-dt_s / tau_s)
    steps = window_us // dt_us
    voltage = [rng.random() * v_th * 0.98 for _ in range(n)]
    bias = [i_bias * (1.0 + 0.12 * (rng.random() * 2 - 1)) for _ in range(n)]
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
    burst = [(t, nid) for t, nid in spikes if 21000 <= t < 25000]
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
            early_flag = pool[0][0] < 21000
            have = len([1 for t, _ in picked if (t < 21000) == early_flag])
            if have >= want:
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
    clamp = [(t, nid) for t, nid in picked if t < 21000][:7]
    weep = [(t, nid) for t, nid in picked if t >= 21000][:9]
    picked = sorted(clamp + weep, key=lambda item: (item[0], item[1]))
    if len(picked) < 8:
        raise RuntimeError(f"LIF excerpt too short: {len(picked)}")
    channels = ["lif.clamp" if t < 21000 else "lif.weep" for t, _ in picked]
    lif = OrderedDict(
        [
            ("model", "leaky_integrate_and_fire"),
            ("n", 84),
            ("dt_us", 100),
            ("tau_m_ms", 20.0),
            ("v_rest", 0.0),
            ("v_reset", 0.0),
            ("v_th", 1.0),
            ("r_m", 1.0),
            ("refractory_us", 1000),
            ("i_bias", 0.92),
            ("i_stim_peak", 2.45),
            ("stim_t_us", [21000, 25000]),
            ("i_clamp_extra", 0.68),
            ("clamp_n", 14),
            ("seed", 42227),
            (
                "note",
                "Population sim scoped to this sidecar. Plant remains designed. "
                "Neurons 0-13 carry +0.68 fuel-clamp bias; stim 21-25 ms is the tube weep.",
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
            ("round", 42),
            ("factory", "thalamic-trajectory-factory"),
            ("generator", "grok-4.6"),
            ("run_label", "2026-09-02-final-heavy"),
            ("schema_version", "thalamic-trajectory-v2"),
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


def record_226():
    ticks = [
        tick(2112, -0.02, 0.01, -0.02, -0.01, 0.01),
        tick(5280, -0.04, 0.01, -0.04, -0.02, 0.01),
        tick(5510, -0.03, 0.01, -0.03, -0.01, 0.01),
        tick(6000, -0.06, 0.02, -0.08, -0.03, 0.02),
        tick(6400, -0.02, 0.01, -0.03, -0.01, 0.01),
        tick(780000000, -0.01, 0.00, -0.02, 0.00, 0.00),
    ]
    spikes = [
        spike("enc.strand.ctx", 1.205, 0.44),
        spike("live.t.windbox", 2.410, 0.61),
        spike("sp.operator.t", 3.880, 0.52),
        spike("enc.grate.ctx", 4.620, 0.47),
        spike("live.t.windbox", 5.280, 1.31),
        spike("sp.operator.t", 5.510, 1.18),
        spike("ctrl.gate", 6.000, 0.99),
        spike("live.t.windbox", 7.220, 0.84),
        spike("sp.operator.t", 9.440, 0.66),
        spike("ctrl.gate", 14.880, 0.88),
        spike("enc.strand.ctx", 18.400, 0.41),
        spike("live.t.windbox", 24.200, 0.58),
    ]
    excerpt = independent_excerpt(42176, 72, 26000, 12, spike_avoid_us(spikes))
    state = OrderedDict(
        [
            (
                "description",
                "Strand S-4 on the Pellet-Naze Dwight machine already holds a 2.40 m/min grate "
                "when a live windbox pyrometer at 412 C races a leftover operator setpoint that "
                "still prints 456 C from last night's idle. Published trip is 440 C on the live "
                "channel; a weak supervisor treats the leftover SP as the trip and zeros a legal strand.",
            ),
            ("domain", "sinter-strand"),
            ("sim_or_real", "designed"),
            (
                "goal",
                "Hold 2.40 m/min on Strand S-4, keep live windbox < 440 C trip, and finish the 13 min "
                "sinter-cake window.",
            ),
            ("t0_us", 1762300000000226),
            ("gate_latency_us", 720),
            ("race_window_us", 400),
            ("race_window_rel_ms", [5.280, 5.680]),
            (
                "race",
                OrderedDict(
                    [
                        (
                            "contenders",
                            [
                                "live.t.windbox 412 C live pyrometer",
                                "sp.operator.t 456 C leftover SP age 2460 s",
                            ],
                        ),
                        (
                            "semantics",
                            "Live-first should ACCEPT 2.40 m/min (412 C < 440 C trip). SP-first "
                            "would only delay confirmation of the same legal live windbox temperature.",
                        ),
                        (
                            "window_derivation",
                            "400 us = one pyrometer ADC slot versus the operator-SP publisher on this "
                            "2 kHz sinter bus.",
                        ),
                        (
                            "order_evidence_note",
                            "Margin 230 us vs combined jitter 76 us (live 34 + SP 42): 3.0x over "
                            "a 2.0x trust floor. Order is correctly live-first. The error is binding "
                            "a leftover operator setpoint as if it were the published trip, not the race.",
                        ),
                    ]
                ),
            ),
            (
                "sensors",
                [
                    "live windbox pyrometer, 2 kHz, 34 us jitter, axis windbox_t",
                    "operator-SP temperature latch, 1 kHz, 42 us jitter, age 2460 s",
                    "strand-speed encoder (context)",
                    "grate drive (context)",
                ],
            ),
            (
                "constraints",
                OrderedDict(
                    [
                        ("live_C", 412.0),
                        ("trip_C", 440.0),
                        ("leftover_sp_C", 456.0),
                        ("leftover_sp_age_s", 2460.0),
                        ("leftover_sp_max_s", 480.0),
                        ("proposed_strand_m_min", 2.40),
                    ]
                ),
            ),
            (
                "episode_steps",
                [
                    "1. Strand S-4 indexed on Pellet-Naze Dwight; live 412 C, 2.40 m/min armed.",
                    "2. Published live trip 440 C; leftover-SP max age 480 s; latch currently 2460 s stale.",
                    "3. Strand precursor at 1.205 ms.",
                    "4. Race window [5.280, 5.680] ms.",
                    "5. Live windbox 412 C at 5.280 ms (winner).",
                    "6. Leftover SP 456 C at 5.510 ms (loser by 230 us).",
                    "7. Gate at 6.000 ms: wrong REJECT holds 0 m/min on the leftover SP.",
                    "8. Strand idle; live windbox never crossed 440 C.",
                    "9. 13 min sinter-cake window missed.",
                    "10. QA: correct gate was ACCEPT; leave 2.40 m/min; bind live 412 C vs 440 C trip.",
                ],
            ),
        ]
    )
    proposed = OrderedDict(
        [
            ("name", "strand_2p40_hold"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("strand_m_min", 2.40),
                        ("live_C", 412.0),
                        ("hold", False),
                    ]
                ),
            ),
            (
                "evidence",
                OrderedDict(
                    [
                        ("live_C", 412.0),
                        ("trip_C", 440.0),
                        ("leftover_sp_C", 456.0),
                        ("leftover_sp_age_s", 2460.0),
                        ("leftover_sp_max_s", 480.0),
                        ("ft_axis", "windbox_t"),
                        ("race_margin_us", 230),
                        ("combined_jitter_us", 76),
                        ("t_gate_us", 6000),
                    ]
                ),
            ),
            (
                "basis",
                "Planner proposes 2.40 m/min because live windbox 412 C is 28 C under the "
                "published 440 C trip and the 456 C leftover SP is 2460 s stale (max age 480 s).",
            ),
        ]
    )
    safety = OrderedDict(
        [
            ("decision", "REJECT"),
            ("correctness", "incorrect"),
            (
                "rationale",
                "Leftover operator SP 456 C is over the 440 C trip (true vs that stale latch). REJECT: "
                "hold 0 m/min until the SP recovers under 440 C so the windbox does not "
                "see an over-temperature event.",
            ),
            (
                "constraint_checked",
                OrderedDict(
                    [
                        (
                            "windbox_temperature_C",
                            OrderedDict(
                                [
                                    ("published_live_trip", 440.0),
                                    ("observed_live", 412.0),
                                    ("leftover_sp_applied", 456.0),
                                    ("sp_age_s", 2460.0),
                                    ("executed_strand_m_min", 0.0),
                                ]
                            ),
                        ),
                        (
                            "order_evidence",
                            OrderedDict(
                                [
                                    ("margin_us", 230),
                                    ("combined_jitter_us", 76),
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
            ("name", "strand_hold_leftover_sp"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("strand_m_min", 0.0),
                        ("live_C", 412.0),
                        ("hold", True),
                    ]
                ),
            ),
            (
                "gate_effect",
                "REJECT (incorrect): strand 2.40 -> 0 m/min. Routing relay.live.t -> "
                "policy.hold_reject; no positive weight to policy.go_accept. Live 412 C never "
                "violated the 440 C trip.",
            ),
        ]
    )
    future = OrderedDict(
        [
            (
                "summary",
                "Wrong-REJECT froze Strand S-4 at 0 m/min while live windbox stayed 412 C under the "
                "440 C trip. 13 min sinter-cake window missed. Correct gate was ACCEPT of the "
                "already-legal 2.40 m/min command.",
            ),
            (
                "state_delta",
                OrderedDict(
                    [
                        ("strand", "held at 0 m/min; 2.40 m/min abandoned"),
                        ("live_C", "still 412 C, under 440 C published trip"),
                        ("machine", "13 min sinter-cake window missed"),
                        ("bed", "no over-temperature; leftover-SP false positive"),
                    ]
                ),
            ),
            (
                "surprises",
                [
                    "The 456 C leftover SP is 2460 s stale; leftover_sp_max_s is 480 s and the latch is not a published live trip.",
                    "Delayed (13 min): sister-strand S-5 ran the same 2.40 m/min sinter-cake window after QA rebound the live trip; S-4's slot was already gone.",
                ],
            ),
            (
                "recovery",
                OrderedDict(
                    [
                        (
                            "correct_gate",
                            "ACCEPT: live 412 C < published 440 C trip; leave 2.40 m/min.",
                        ),
                        ("correct_trip_C", 440.0),
                        ("wrong_sp_C", 456.0),
                        (
                            "wrong_edit_applied",
                            OrderedDict([("strand_m_min", 0.0), ("hold", True)]),
                        ),
                        (
                            "cost",
                            "13 min missed sinter-cake window (task/efficiency); live windbox never over trip (safety false-positive).",
                        ),
                    ]
                ),
            ),
            (
                "race_result",
                OrderedDict(
                    [
                        ("winner", "live.t.windbox (5.280 ms, 412 C)"),
                        ("loser", "sp.operator.t (5.510 ms, 456 C leftover SP)"),
                        ("margin_us", 230),
                        (
                            "counterfactual_if_reversed",
                            "SP-first by < 230 us would still show live 412 C < 440 C. A "
                            "correct gate ACCEPTs either way. The wrong REJECT spent the live win "
                            "on a leftover operator setpoint.",
                        ),
                    ]
                ),
            ),
            ("reward_inflection_t_us", 6000),
            (
                "reward_inflection_note",
                "Task and efficiency drop at the wrong REJECT (6.000 ms, tick 4). The 13 min "
                "missed window is delayed surprise, not the inflection.",
            ),
            ("delayed_surprise_s", 780.0),
            ("missed_window_s", 780),
        ]
    )
    ras = raster_core(
        26,
        72,
        32,
        60,
        routing(
            "relay.live.t",
            "policy.hold_reject",
            [
                ("relay.live.t", "policy.hold_reject", 0.71),
                ("relay.sp.operator", "policy.hold_reject", 0.22),
            ],
            "acetylcholine",
            0.08,
            "leftover_sp_stdp; ACh tags the (wrong) hold_reject bind at the live win",
        ),
        excerpt,
    )
    gate = OrderedDict(
        [
            ("decision_window_ms", 0.40),
            ("decision", "REJECT"),
            (
                "populations",
                [
                    pop("hold_reject", 48, 0.50, 200.0, 4),
                    pop("go_accept", 48, 0.80, 10.0, 0),
                    pop("live_trip_veto", 24, 0.75),
                ],
            ),
        ]
    )
    return OrderedDict(
        [
            ("id", "ttf-r42-226"),
            (
                "title",
                "WRONG-REJECT at Pellet-Naze / Strand S-4: live 412 C is legal vs "
                "published 440 C trip; supervisor bound a 2460 s leftover 456 C operator SP",
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
                    "Wrong-reject. Sidecar arithmetic 412 < 440 is true; clamp bound to a "
                    "leftover 456 C operator SP. total -0.36 = -0.18 + 0.06 + -0.22 + -0.08 + 0.06.",
                ),
            ),
            ("raster", ras),
            ("gate_snn", gate),
            (
                "meta",
                meta_block(
                    "sinter-strand",
                    [
                        "reject",
                        "wrong-gate",
                        "leftover-setpoint-as-trip",
                        "stale-sp-as-limit",
                        "sidecar-convictable",
                        "designed",
                    ],
                    "Teaches a probe that a correct live<trip read can still be a wrong gate when "
                    "routing.table[0].to is policy.hold_reject and executed strand is zeroed.",
                    1,
                    supervisor_error_type="wrong-reject",
                ),
            ),
        ]
    )


def record_227():
    excerpt, extra = lif_227_excerpt()
    ticks = [
        tick(1848, 0.05, -0.02, -0.02, 0.01, 0.00),
        tick(4620, 0.08, -0.04, -0.03, 0.01, -0.01),
        tick(4850, 0.04, -0.03, -0.02, 0.00, 0.00),
        tick(5500, 0.10, -0.06, -0.03, 0.02, -0.01),
        tick(22400, 0.05, -0.42, -0.04, 0.00, -0.02),
        tick(960000000, 0.02, -0.05, -0.02, 0.00, 0.00),
    ]
    state = OrderedDict(
        [
            (
                "description",
                "Reformer Bank B-6 is firing 4.2 kg/s mixed feed through the Methane-Howe tube nest "
                "when a tube-wall pyrometer pulse arrives 230 us before the fuel-flow meter that "
                "still reads a legal spout. Wall-first latches a process clamp under the 890 C cap; "
                "flow-first would keep cruise fuel. Stored condensate weep is not yet an observable "
                "of either race channel.",
            ),
            ("domain", "steam-methane-reformer"),
            ("sim_or_real", "designed"),
            (
                "goal",
                "Fire 4.2 kg/s mixed feed through Bank B-6, keep tube-wall <= 890 C, and leave the "
                "catalyst tubes unruptured.",
            ),
            ("t0_us", 1762300000000227),
            ("gate_latency_us", 880),
            ("race_window_us", 380),
            ("race_window_rel_ms", [4.620, 5.000]),
            (
                "race",
                OrderedDict(
                    [
                        (
                            "contenders",
                            [
                                "pyro.tube.c 912 C tube-wall",
                                "ft.fuel.kgs 4.2 kg/s still-legal spout",
                            ],
                        ),
                        (
                            "semantics",
                            "Wall-first latches fuel clamp 4.2 -> 2.8 kg/s; flow-first keeps cruise "
                            "fuel on a 'spout still open' model.",
                        ),
                        (
                            "window_derivation",
                            "380 us = one tube-pyrometer slot minus fuel-FT group delay on this "
                            "1 kHz reformer bus.",
                        ),
                        (
                            "order_evidence_note",
                            "Margin 230 us vs combined jitter 68 us (pyro 30 + FT 38): 3.4x over "
                            "a 2.0x trust floor. Reversing order by < 230 us inside the 380 us window "
                            "would have kept 4.2 kg/s cruise; predicted next-sample wall 898 C > 890 cap.",
                        ),
                    ]
                ),
            ),
            (
                "sensors",
                [
                    "tube-wall pyrometer, 1 kHz, 30 us timestamp jitter",
                    "fuel mass-flow, 1 kHz, 38 us jitter",
                    "arch IR (context)",
                    "furnace AE (context)",
                ],
            ),
            (
                "constraints",
                OrderedDict(
                    [
                        ("wall_cap_C", 890.0),
                        ("observed_wall_C", 912.0),
                        ("proposed_fuel_kg_s", 4.2),
                        ("fuel_floor_kg_s", 2.4),
                    ]
                ),
            ),
            (
                "episode_steps",
                [
                    "1. Bank B-6 indexed; 4.2 kg/s mixed feed; tube-wall 912 C > 890 cap.",
                    "2. Cruise fuel 4.2 kg/s armed; wall over the 890 C cap.",
                    "3. IR precursor at 1.848 ms; wall warm-start 912 C.",
                    "4. Race window [4.620, 5.000] ms opens on the reformer bus.",
                    "5. Tube-wall 912 C at 4.620 ms (winner).",
                    "6. Fuel FT 4.2 kg/s at 4.850 ms (loser by 230 us).",
                    "7. Gate at 5.500 ms (winner + 880 us): MODIFY clamp 4.2 -> 2.8 kg/s.",
                    "8. Clamp executes; next-sample wall 868 C < 890 cap.",
                    "9. At 22.400 ms stored condensate produces a tube weep / steam precursor.",
                    "10. Emergency dump 16 min + tube inspection; named un-netted loss, not folded into process heads.",
                ],
            ),
        ]
    )
    proposed = OrderedDict(
        [
            ("name", "cruise_fuel_fire"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("fuel_kg_s", 4.2),
                        ("wall_C", 912.0),
                        ("hold", False),
                    ]
                ),
            ),
            (
                "evidence",
                OrderedDict(
                    [
                        ("wall_C", 912.0),
                        ("wall_cap_C", 890.0),
                        ("predicted_unclamped_next_C", 898.0),
                        ("fuel_kg_s", 4.2),
                        ("race_margin_us", 230),
                        ("combined_jitter_us", 68),
                    ]
                ),
            ),
            (
                "basis",
                "Planner proposes 4.2 kg/s cruise: fuel flow looks like an open spout, not a "
                "plugged gun, and the 890 C wall cap is treated as still open.",
            ),
        ]
    )
    safety = OrderedDict(
        [
            ("decision", "MODIFY"),
            ("correctness", "correct"),
            (
                "rationale",
                "Tube-wall 912 C won by 230 us, so the nest is running hot, not still free. "
                "Holding 4.2 kg/s predicts next-sample 898 C > 890 C cap. MODIFY: fuel 4.2 -> "
                "2.8 kg/s. Observed after clamp 868 C < 890. A full REJECT is not indicated: a "
                "sound bank accepts 2.8 kg/s.",
            ),
            (
                "constraint_checked",
                OrderedDict(
                    [
                        (
                            "tube_wall_C",
                            OrderedDict(
                                [
                                    ("cap", 890.0),
                                    ("observed", 912.0),
                                    ("predicted_unclamped_next", 898.0),
                                    ("clamped_fuel_kg_s", 2.8),
                                    ("observed_after_clamp", 868.0),
                                ]
                            ),
                        ),
                        (
                            "order_evidence",
                            OrderedDict(
                                [
                                    ("margin_us", 230),
                                    ("combined_jitter_us", 68),
                                    ("ratio", 3.38),
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
            ("name", "clamped_fuel_fire"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("fuel_kg_s", 2.8),
                        ("wall_C", 868.0),
                        ("hold", False),
                    ]
                ),
            ),
            (
                "gate_effect",
                "MODIFY: fuel 4.2 -> 2.8 kg/s. Process-correct vs the 890 C wall cap. Tube weep "
                "still occurs at 22.400 ms.",
            ),
        ]
    )
    future = OrderedDict(
        [
            (
                "summary",
                "Process-correct MODIFY held wall at 868 C. At 22.400 ms stored condensate produced "
                "a tube weep / steam precursor. Clamp reduced fuel energy; it did not dump the "
                "catalyst charge. Partnered negative: process heads stay honest; world loss is named, "
                "not netted.",
            ),
            (
                "state_delta",
                OrderedDict(
                    [
                        ("fuel", "clamp executed; wall 868 C < 890"),
                        ("tubes", "condensate weep at 22.400 ms"),
                        ("repair", "16 min emergency dump + tube inspection"),
                        ("mission", "bank still firing; weep precursor controlled"),
                    ]
                ),
            ),
            (
                "surprises",
                [
                    "Neither wall pyro nor fuel FT predicted the condensate charge; ae.weep.steam is a new channel at 22.400 ms, 16.900 ms after the gate, still inside the 40 ms raster.",
                    "Delayed (16 min): emergency dump and tube inspection close the weep. Named un-netted loss, not folded into task_progress.",
                ],
            ),
            (
                "un_netted_loss",
                "16 min emergency dump + tube inspection after a condensate weep. Safety head "
                "-0.62 prices the steam precursor; task_progress stays +0.34 because the fuel "
                "clamp completed under the 890 C cap. World loss is named here, not subtracted from process heads.",
            ),
            (
                "race_result",
                OrderedDict(
                    [
                        ("winner", "pyro.tube.c (4.620 ms, 912 C)"),
                        ("loser", "ft.fuel.kgs (4.850 ms, 4.2 kg/s)"),
                        ("margin_us", 230),
                        (
                            "counterfactual_if_reversed",
                            "Flow-first by < 230 us inside the 380 us window would have kept "
                            "4.2 kg/s cruise; predicted next-sample 898 C would have exceeded the "
                            "890 C cap even without the weep charge. The MODIFY is still the "
                            "correct process. The weep is a later world charge either way, cheaper "
                            "with the clamp than without.",
                        ),
                    ]
                ),
            ),
            ("reward_inflection_t_us", 22400),
            (
                "reward_inflection_note",
                "Safety collapses at the 22.400 ms condensate weep (tick t_us=22400), inside the "
                "40 ms raster. The correct MODIFY at 5.500 ms is in the same excerpt. Do not put "
                "inflection on the +16 min dump tick.",
            ),
            ("delayed_surprise_s", 960.0),
            ("abort_s", 960),
        ]
    )
    spikes = [
        spike("ir.arch.ctx", 1.120, 0.43),
        spike("pyro.tube.c", 2.240, 0.62),
        spike("ft.fuel.kgs", 3.180, 0.55),
        spike("pyro.tube.c", 4.620, 1.34),
        spike("ft.fuel.kgs", 4.850, 1.12),
        spike("ctrl.gate", 5.500, 0.97),
        spike("pyro.tube.c", 7.200, 0.81),
        spike("ft.fuel.kgs", 10.400, 0.66),
        spike("ctrl.gate", 15.200, 0.84),
        spike("ae.weep.steam", 22.400, 1.42),
        spike("ae.weep.steam", 23.600, 0.91),
        spike("ir.arch.ctx", 29.800, 0.41),
        spike("pyro.tube.c", 36.200, 0.58),
    ]
    ras = raster_core(
        40,
        84,
        26,
        87,
        routing(
            "thalamic-relay.wall-fuel",
            "spikenaut.policy.fuel-clamp",
            [
                ("relay.pyro.tube", "policy.fuel_clamp", 0.64),
                ("relay.ft.fuel", "policy.spout_hold", 0.29),
                ("relay.ae.weep", "policy.fuel_clamp", -0.46),
            ],
            "noradrenaline",
            0.05,
            "surprise-gated pre_post_stdp; NA at wall win (4.620 ms) opens a 50 ms eligibility "
            "trace that still covers the 22.400 ms condensate weep",
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
                    pop("fuel_clamp", 48, 0.50, 220.0, 4),
                    pop("spout_hold", 48, 0.50, 50.0, 1),
                    pop("wall_cap_veto", 24, 0.75),
                ],
            ),
        ]
    )
    return OrderedDict(
        [
            ("id", "ttf-r42-227"),
            (
                "title",
                "Methane-Howe reformer / Bank B-6: tube-wall beats fuel FT by 230 us; correct "
                "MODIFY still eats an in-window condensate weep (partnered negative total -0.44)",
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
                    "40 ms raster. total -0.44 = 0.34 + -0.62 + -0.16 + 0.04 + -0.04. Named "
                    "dump+inspection loss is not netted into task_progress.",
                ),
            ),
            ("raster", ras),
            ("gate_snn", gate),
            (
                "meta",
                meta_block(
                    "steam-methane-reformer",
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
                    "16 min gap.",
                    2,
                ),
            ),
        ]
    )


def record_228():
    ticks = [
        tick(1568, 0.01, 0.04, 0.02, 0.01, 0.01),
        tick(3920, 0.02, 0.08, 0.02, 0.02, 0.01),
        tick(4110, 0.01, 0.06, 0.02, 0.01, 0.01),
        tick(5100, 0.03, 0.12, 0.04, 0.04, 0.02),
        tick(5380, 0.02, 0.07, 0.01, 0.01, 0.01),
        tick(540000000, 0.01, 0.03, 0.01, 0.01, 0.00),
    ]
    spikes = [
        spike("enc.bush.ctx", 1.040, 0.44),
        spike("ae.tip.pps", 2.180, 0.71),
        spike("enc.pull.kgh", 3.020, 0.52),
        spike("ae.tip.pps", 3.920, 1.36),
        spike("enc.pull.kgh", 4.110, 1.14),
        spike("ctrl.gate", 5.100, 0.98),
        spike("ae.tip.pps", 7.400, 0.82),
        spike("enc.pull.kgh", 10.800, 0.61),
        spike("ctrl.gate", 16.200, 0.86),
        spike("ae.tip.pps", 24.600, 0.70),
        spike("enc.pull.kgh", 33.400, 0.48),
        spike("ir.pad.ctx", 41.200, 0.40),
    ]
    excerpt = independent_excerpt(42178, 120, 44000, 13, spike_avoid_us(spikes))
    state = OrderedDict(
        [
            (
                "description",
                "Bushing B-7 on the Filament-Naze HIL pad is pulling 410 kg/h when an AE burst at "
                "58 pps on the tip plate races the pull-rate encoder that still looks in-band "
                "for a ram step. Ramp is legal only if AE <= 40 pps. AE-first latches hold; "
                "encoder-first would treat in-band pull-rate as orifice clearance.",
            ),
            ("domain", "glass-fiber-bushing"),
            ("sim_or_real", "hil"),
            (
                "goal",
                "Do not ramp Bushing B-7 unless AE <= 40 pps; keep pull rate 0 kg/h until the "
                "tip plate is quiet.",
            ),
            ("t0_us", 1762300000000228),
            ("gate_latency_us", 1180),
            ("race_window_us", 280),
            ("race_window_rel_ms", [3.920, 4.200]),
            (
                "race",
                OrderedDict(
                    [
                        (
                            "contenders",
                            [
                                "ae.tip.pps 58 pps flare",
                                "enc.pull.kgh 410 kg/h still-in-band",
                            ],
                        ),
                        (
                            "semantics",
                            "AE-first latches REJECT hold 0 kg/h; encoder-first would ramp 410 kg/h "
                            "on an in-band-rate-as-clearance model.",
                        ),
                        (
                            "window_derivation",
                            "280 us = one AE envelope slot versus the ram-encoder publisher on this "
                            "pad cycle.",
                        ),
                        (
                            "order_evidence_note",
                            "Margin 190 us vs combined jitter 54 us (AE 24 + encoder 30): 3.5x over a "
                            "2.0x trust floor. Pad injects encoder 90-130 us before the AE envelope "
                            "finishes (piezo lag, not a sensor fault); the encoder packet is still "
                            "the loser in this 280 us window.",
                        ),
                    ]
                ),
            ),
            (
                "sensors",
                [
                    "tip-plate AE, 24 us jitter, 40 pps trip",
                    "pull-rate ram encoder, 30 us jitter",
                    "bushing PT (context)",
                    "forehearth IR (context)",
                ],
            ),
            (
                "constraints",
                OrderedDict(
                    [
                        ("ae_trip_pps", 40.0),
                        ("observed_ae_pps", 58.0),
                        ("pull_cap_kg_h", 480.0),
                        ("proposed_pull_kg_h", 410.0),
                    ]
                ),
            ),
            (
                "episode_steps",
                [
                    "1. Bushing B-7 on Filament-Naze HIL pad; platinum in band; ram armed at 410 kg/h.",
                    "2. AE trip 40 pps; observed 58 pps flare on tip plate.",
                    "3. Encoder precursor at 1.040 ms.",
                    "4. Race window [3.920, 4.200] ms.",
                    "5. AE 58 pps at 3.920 ms (winner).",
                    "6. Pull encoder 410 kg/h at 4.110 ms (loser by 190 us).",
                    "7. Gate at 5.100 ms: REJECT hold 0 kg/h, do not ramp.",
                    "8. Pad recycle 9 min; tip AE decays under 40 pps after hold.",
                    "9. Platinum never broke; encoder-as-clearance would have ramped into the flare.",
                    "10. QA: correct gate was REJECT; leave 0 kg/h until AE <= 40 pps.",
                ],
            ),
        ]
    )
    proposed = OrderedDict(
        [
            ("name", "ramp_410kgh"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("pull_kg_h", 410.0),
                        ("ae_pps", 58.0),
                        ("hold", False),
                    ]
                ),
            ),
            (
                "evidence",
                OrderedDict(
                    [
                        ("ae_pps", 58.0),
                        ("ae_trip_pps", 40.0),
                        ("pull_kg_h", 410.0),
                        ("pull_cap_kg_h", 480.0),
                        ("race_margin_us", 190),
                        ("combined_jitter_us", 54),
                        ("t_gate_us", 5100),
                    ]
                ),
            ),
            (
                "basis",
                "Planner proposes 410 kg/h because pull-rate is under the 480 kg/h cap and treats "
                "the encoder as orifice clearance, ignoring the 58 pps AE flare.",
            ),
        ]
    )
    safety = OrderedDict(
        [
            ("decision", "REJECT"),
            ("correctness", "correct"),
            (
                "rationale",
                "AE 58 pps won by 190 us and is over the 40 pps trip. Encoder 410 kg/h is under "
                "the 480 kg/h cap but is not clearance. REJECT: hold 0 kg/h until AE <= 40 pps.",
            ),
            (
                "constraint_checked",
                OrderedDict(
                    [
                        (
                            "tip_ae_pps",
                            OrderedDict(
                                [
                                    ("trip", 40.0),
                                    ("observed", 58.0),
                                    ("executed_pull_kg_h", 0.0),
                                ]
                            ),
                        ),
                        (
                            "order_evidence",
                            OrderedDict(
                                [
                                    ("margin_us", 190),
                                    ("combined_jitter_us", 54),
                                    ("ratio", 3.52),
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
            ("name", "pull_hold_ae"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("pull_kg_h", 0.0),
                        ("ae_pps", 58.0),
                        ("hold", True),
                    ]
                ),
            ),
            (
                "gate_effect",
                "REJECT: pull 410 -> 0 kg/h. Routing relay.ae.tip -> policy.hold_reject. "
                "Do not ramp into the 58 pps flare.",
            ),
        ]
    )
    future = OrderedDict(
        [
            (
                "summary",
                "Correct REJECT held Bushing B-7 at 0 kg/h while AE 58 pps decayed. Encoder-as-clearance "
                "would have ramped 410 kg/h into the flare. Pad recycle 9 min.",
            ),
            (
                "state_delta",
                OrderedDict(
                    [
                        ("pull", "held at 0 kg/h"),
                        ("tip", "AE flare decaying under trip after hold"),
                        ("platinum", "unbroken"),
                        ("pad", "9 min recycle"),
                    ]
                ),
            ),
            (
                "surprises",
                [
                    "Pad injects encoder 90-130 us before AE envelope finish; that is piezo lag, not a false AE.",
                    "Delayed (9 min): pad recycle restacks the ram after AE < 40 pps.",
                ],
            ),
            (
                "race_result",
                OrderedDict(
                    [
                        ("winner", "ae.tip.pps (3.920 ms, 58 pps)"),
                        ("loser", "enc.pull.kgh (4.110 ms, 410 kg/h)"),
                        ("margin_us", 190),
                        (
                            "counterfactual_if_reversed",
                            "Encoder-first by < 190 us would have treated 410 kg/h as clearance and "
                            "ramped into the 58 pps flare. The REJECT is still required; reversal "
                            "only delays the AE bind.",
                        ),
                    ]
                ),
            ),
            ("reward_inflection_t_us", 5100),
            (
                "reward_inflection_note",
                "Safety credit lands at the correct REJECT (5.100 ms, tick 4). Pad recycle is delayed surprise.",
            ),
            ("delayed_surprise_s", 540.0),
            ("pad_recycle_s", 540),
        ]
    )
    ras = raster_core(
        44,
        120,
        18,
        95,
        routing(
            "relay.ae.tip",
            "policy.hold_reject",
            [
                ("relay.ae.tip", "policy.hold_reject", 0.74),
                ("relay.enc.pull", "policy.ramp_go", 0.18),
            ],
            "dopamine",
            0.06,
            "ae_trip_stdp; DA tags the hold_reject bind at the AE win",
        ),
        excerpt,
    )
    gate = OrderedDict(
        [
            ("decision_window_ms", 0.28),
            ("decision", "REJECT"),
            (
                "populations",
                [
                    pop("hold_reject", 64, 0.50, 180.0, 3),
                    pop("ramp_go", 64, 0.80, 8.0, 0),
                    pop("ae_trip_veto", 32, 0.70),
                ],
            ),
        ]
    )
    return OrderedDict(
        [
            ("id", "ttf-r42-228"),
            (
                "title",
                "Filament-Naze bushing HIL / Bushing B-7: AE 58 pps beats pull encoder 410 kg/h by 190 us; "
                "correct REJECT holds the ram",
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
                    "Correct REJECT. AE 58 > 40 trip beats in-band pull-rate. total +0.78 = "
                    "0.10 + 0.40 + 0.12 + 0.10 + 0.06.",
                ),
            ),
            ("raster", ras),
            ("gate_snn", gate),
            (
                "meta",
                meta_block(
                    "glass-fiber-bushing",
                    [
                        "reject",
                        "hil-pad",
                        "ae-vs-encoder",
                        "tip-flare-hold",
                        "sidecar-convictable",
                        "hil",
                    ],
                    "Teaches a probe that an in-band pull-rate encoder is not orifice clearance when "
                    "AE is over trip and routing.table[0].to is policy.hold_reject.",
                    3,
                ),
            ),
        ]
    )


def record_229():
    ticks = [
        tick(2496, 0.06, 0.04, 0.03, 0.02, 0.01),
        tick(6240, 0.10, 0.06, 0.04, 0.02, 0.02),
        tick(6470, 0.06, 0.04, 0.02, 0.01, 0.01),
        tick(7140, 0.12, 0.08, 0.05, 0.03, 0.02),
        tick(7500, 0.05, 0.04, 0.02, 0.01, 0.01),
        tick(600000000, 0.03, 0.02, 0.02, 0.01, 0.01),
    ]
    params = OrderedDict(
        [
            ("c2_t_h", 9.2),
            ("slurry_C", 68.4),
            ("zone_n", 12),
            ("loop_C", 68.4),
        ]
    )
    spikes = [
        spike("ft.feed.ctx", 1.480, 0.42),
        spike("rtd.slurry.C", 3.120, 0.58),
        spike("nir.feed.smear", 4.660, 0.50),
        spike("rtd.slurry.C", 6.240, 1.28),
        spike("nir.feed.smear", 6.470, 1.10),
        spike("ctrl.gate", 7.140, 0.96),
        spike("rtd.slurry.C", 9.200, 0.74),
        spike("nir.feed.smear", 12.800, 0.60),
        spike("ctrl.gate", 18.400, 0.82),
        spike("rtd.slurry.C", 24.600, 0.55),
        spike("ft.feed.ctx", 29.800, 0.40),
    ]
    excerpt = independent_excerpt(42179, 52, 32000, 12, spike_avoid_us(spikes))
    state = OrderedDict(
        [
            (
                "description",
                "Loop L-3 of the Olefin-Noll slurry train is circulating 9.2 t/h when a slurry RTD at "
                "68.4 C races a feed-NIR smear that still claims fouling. Commanded 9.2 t/h and "
                "68.4 C sit 1.3 t/h and 3.6 C inside the legal envelopes. The RTD win only "
                "ratifies the loop already on the reactor.",
            ),
            ("domain", "polyethylene-loop-reactor"),
            ("sim_or_real", "simulated"),
            (
                "goal",
                "Finish the 12-zone loop on Olefin-Noll, keep slurry <= 72.0 C and C2 "
                "<= 10.5 t/h, and leave fouling in spec.",
            ),
            ("t0_us", 1762300000000229),
            ("gate_latency_us", 900),
            ("race_window_us", 360),
            ("race_window_rel_ms", [6.240, 6.600]),
            (
                "race",
                OrderedDict(
                    [
                        (
                            "contenders",
                            [
                                "rtd.slurry.C 68.4 C loop-3 slurry",
                                "nir.feed.smear fouling claim",
                            ],
                        ),
                        (
                            "semantics",
                            "RTD-first confirms the already-legal 9.2 t/h / 68.4 C loop; "
                            "NIR-first would have treated the RTD as a smear echo and looked "
                            "for an extra clamp the train does not need.",
                        ),
                        (
                            "window_derivation",
                            "360 us = one 12-zone RTD kernel step versus the NIR publisher "
                            "on this rigid loop train.",
                        ),
                        (
                            "order_evidence_note",
                            "Margin 230 us vs combined jitter 70 us (RTD 32 + NIR 38): 3.3x over "
                            "a 2.0x trust floor. Reversing order by < 230 us would not make the "
                            "proposed loop illegal; it would only have delayed confirmation.",
                        ),
                    ]
                ),
            ),
            (
                "sensors",
                [
                    "slurry RTD, 12 zones, 32 us jitter",
                    "feed NIR smear, 38 us jitter",
                    "C2 FT (context)",
                    "loop pressure (context)",
                ],
            ),
            (
                "constraints",
                OrderedDict(
                    [
                        ("slurry_cap_C", 72.0),
                        ("observed_slurry_C", 68.4),
                        ("c2_cap_t_h", 10.5),
                        ("proposed_c2_t_h", 9.2),
                        ("zone_n", 12),
                    ]
                ),
            ),
            (
                "simulation",
                OrderedDict(
                    [
                        (
                            "solver",
                            "12-zone 1D slurry loop + RTD kernel, seed 42; 12 zones, 3 radial slurry bins; NOT lumped-CSTR, NOT CFD-LES",
                        ),
                        (
                            "fidelity_limits",
                            "No particle agglomeration or pump cavitation; zones are rigid pressure sources. Raster is kernelized events, not an independent LIF.",
                        ),
                    ]
                ),
            ),
            (
                "episode_steps",
                [
                    "1. Olefin-Noll slurry train indexed; Loop L-3 circulating 9.2 t/h at 68.4 C.",
                    "2. Caps: slurry 72.0 C, C2 10.5 t/h; both proposed values inside.",
                    "3. Feed precursor at 1.480 ms.",
                    "4. Race window [6.240, 6.600] ms.",
                    "5. Slurry RTD 68.4 C at 6.240 ms (winner).",
                    "6. NIR smear at 6.470 ms (loser by 230 us).",
                    "7. Gate at 7.140 ms: ACCEPT 9.2 t/h / 68.4 C already legal.",
                    "8. Loop continues; no extra clamp.",
                    "9. 10 min survey confirms fouling still in spec.",
                    "10. QA: ACCEPT params identical to proposed.",
                ],
            ),
        ]
    )
    proposed = OrderedDict(
        [
            ("name", "loop_9p2_thold"),
            ("parameters", params),
            (
                "evidence",
                OrderedDict(
                    [
                        ("slurry_C", 68.4),
                        ("slurry_cap_C", 72.0),
                        ("c2_t_h", 9.2),
                        ("c2_cap_t_h", 10.5),
                        ("race_margin_us", 230),
                        ("combined_jitter_us", 70),
                        ("t_gate_us", 7140),
                    ]
                ),
            ),
            (
                "basis",
                "Planner proposes 9.2 t/h because slurry 68.4 C is 3.6 C under the 72.0 C cap "
                "and C2 is 1.3 t/h under the 10.5 t/h envelope.",
            ),
        ]
    )
    safety = OrderedDict(
        [
            ("decision", "ACCEPT"),
            ("correctness", "correct"),
            (
                "rationale",
                "Slurry 68.4 C won by 230 us and is under 72.0 C. C2 9.2 t/h is under "
                "10.5 t/h. ACCEPT the already-legal loop; NIR smear is not a cap violation.",
            ),
            (
                "constraint_checked",
                OrderedDict(
                    [
                        (
                            "slurry_C",
                            OrderedDict(
                                [
                                    ("cap", 72.0),
                                    ("observed", 68.4),
                                    ("executed_c2_t_h", 9.2),
                                ]
                            ),
                        ),
                        (
                            "order_evidence",
                            OrderedDict(
                                [
                                    ("margin_us", 230),
                                    ("combined_jitter_us", 70),
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
            ("name", "loop_9p2_thold"),
            ("parameters", params),
            (
                "gate_effect",
                "ACCEPT: C2 9.2 t/h and slurry 68.4 C unchanged. Routing relay.rtd.slurry "
                "-> policy.go_accept.",
            ),
        ]
    )
    future = OrderedDict(
        [
            (
                "summary",
                "Correct ACCEPT left Loop L-3 at 9.2 t/h / 68.4 C. NIR smear did not justify a "
                "clamp. 10 min survey confirmed fouling in spec.",
            ),
            (
                "state_delta",
                OrderedDict(
                    [
                        ("loop", "still 9.2 t/h / 68.4 C"),
                        ("fouling", "in spec after survey"),
                        ("train", "12 zones continue"),
                        ("clamp", "none applied"),
                    ]
                ),
            ),
            (
                "surprises",
                [
                    "NIR smear is a feed-side optical claim, not a slurry-temperature violation.",
                    "Delayed (10 min): survey restacks Loop L-3 without a recovery clamp.",
                ],
            ),
            (
                "race_result",
                OrderedDict(
                    [
                        ("winner", "rtd.slurry.C (6.240 ms, 68.4 C)"),
                        ("loser", "nir.feed.smear (6.470 ms, fouling claim)"),
                        ("margin_us", 230),
                        (
                            "counterfactual_if_reversed",
                            "NIR-first by < 230 us would only delay confirmation. The loop stays "
                            "legal either way; ACCEPT is still required.",
                        ),
                    ]
                ),
            ),
            ("reward_inflection_t_us", 7140),
            (
                "reward_inflection_note",
                "Task credit lands at the ACCEPT (7.140 ms, tick 4). Survey is delayed surprise.",
            ),
            ("delayed_surprise_s", 600.0),
            ("survey_s", 600),
        ]
    )
    ras = raster_core(
        32,
        52,
        40,
        67,
        routing(
            "relay.rtd.slurry",
            "policy.go_accept",
            [
                ("relay.rtd.slurry", "policy.go_accept", 0.68),
                ("relay.nir.feed", "policy.smear_hold", 0.21),
            ],
            "serotonin",
            0.07,
            "legal_loop_stdp; 5-HT tags the go_accept bind at the RTD win",
        ),
        excerpt,
    )
    gate = OrderedDict(
        [
            ("decision_window_ms", 0.36),
            ("decision", "ACCEPT"),
            (
                "populations",
                [
                    pop("go_accept", 40, 0.50, 180.0, 3),
                    pop("smear_hold", 40, 0.80, 10.0, 0),
                    pop("slurry_cap_veto", 20, 0.75),
                ],
            ),
        ]
    )
    return OrderedDict(
        [
            ("id", "ttf-r42-229"),
            (
                "title",
                "Olefin-Noll slurry loop / Loop L-3: slurry RTD 68.4 C beats NIR smear by 230 us; ACCEPT "
                "already-legal 9.2 t/h loop",
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
                    "Correct ACCEPT of an already-legal 12-zone slurry loop. total +1.06 = "
                    "0.42 + 0.28 + 0.18 + 0.10 + 0.08.",
                ),
            ),
            ("raster", ras),
            ("gate_snn", gate),
            (
                "meta",
                meta_block(
                    "polyethylene-loop-reactor",
                    [
                        "accept",
                        "already-legal",
                        "simulated-loop-train",
                        "rtd-vs-nir",
                        "sidecar-convictable",
                        "simulated",
                    ],
                    "Teaches that a slurry RTD under cap can confirm an already-legal loop without "
                    "a fouling smear becoming a clamp.",
                    4,
                ),
            ),
        ]
    )


def record_230():
    ticks = [
        tick(1672, 0.06, 0.04, 0.03, 0.02, 0.01),
        tick(4180, 0.10, 0.08, 0.04, 0.02, 0.02),
        tick(4360, 0.06, 0.04, 0.02, 0.02, 0.01),
        tick(4940, 0.12, 0.08, 0.05, 0.04, 0.02),
        tick(5240, 0.06, 0.05, 0.02, 0.01, 0.01),
        tick(420000000, 0.04, 0.03, 0.02, 0.01, 0.01),
    ]
    params = OrderedDict(
        [
            ("density_A_m2", 280.0),
            ("electrolyte_C", 58.4),
            ("cell_id", 18),
            ("hold", False),
        ]
    )
    spikes = [
        spike("enc.cell.ctx", 0.920, 0.41),
        spike("rtd.elyte.c", 2.140, 0.60),
        spike("bus.v.smear", 3.080, 0.51),
        spike("rtd.elyte.c", 4.180, 1.30),
        spike("bus.v.smear", 4.360, 1.12),
        spike("ctrl.gate", 4.940, 0.97),
        spike("rtd.elyte.c", 6.800, 0.78),
        spike("bus.v.smear", 9.200, 0.62),
        spike("ctrl.gate", 13.600, 0.85),
        spike("rtd.elyte.c", 18.400, 0.54),
        spike("bus.v.smear", 21.200, 0.43),
    ]
    excerpt = independent_excerpt(42180, 64, 22000, 11, spike_avoid_us(spikes))
    state = OrderedDict(
        [
            (
                "description",
                "Cell C-18 at Cathode-Howe tankhouse is armed for a 280 A/m2 strip when an "
                "electrolyte RTD at 58.4 C races a bus-voltage smear that still claims a hitch. "
                "Commanded 280 A/m2 and 58.4 C sit 40 A/m2 under the 320 A/m2 cap and 6.6 C under "
                "the 65.0 C cap. The RTD win only ratifies the strip already on the cell.",
            ),
            ("domain", "copper-electrorefining"),
            ("sim_or_real", "designed"),
            (
                "goal",
                "Run Cell C-18 at 280 A/m2, keep electrolyte <= 65.0 C and bus smear <= 1.80 V, "
                "and leave the tankhouse on schedule.",
            ),
            ("t0_us", 1762300000000230),
            ("gate_latency_us", 760),
            ("race_window_us", 300),
            ("race_window_rel_ms", [4.180, 4.480]),
            (
                "race",
                OrderedDict(
                    [
                        (
                            "contenders",
                            [
                                "rtd.elyte.c 58.4 C electrolyte RTD",
                                "bus.v.smear 1.12 V hitch claim",
                            ],
                        ),
                        (
                            "semantics",
                            "RTD-first confirms the already-legal 280 A/m2 / 58.4 C strip; bus-first "
                            "would have treated the RTD as a hitch echo and looked for an extra hold "
                            "the cell does not need.",
                        ),
                        (
                            "window_derivation",
                            "300 us = one electrolyte-RTD slot versus the bus-smear publisher "
                            "on this tankhouse bus.",
                        ),
                        (
                            "order_evidence_note",
                            "Margin 180 us vs combined jitter 58 us (RTD 28 + bus 30): 3.1x over "
                            "a 2.0x trust floor. Reversing order by < 180 us would not make the "
                            "proposed strip illegal; it would only have delayed confirmation.",
                        ),
                    ]
                ),
            ),
            (
                "sensors",
                [
                    "electrolyte RTD, 28 us jitter",
                    "bus-voltage smear, 30 us jitter",
                    "cell encoder (context)",
                    "liberator PT (context)",
                ],
            ),
            (
                "constraints",
                OrderedDict(
                    [
                        ("elyte_cap_C", 65.0),
                        ("observed_elyte_C", 58.4),
                        ("density_cap_A_m2", 320.0),
                        ("proposed_density_A_m2", 280.0),
                        ("bus_cap_V", 1.80),
                        ("observed_bus_V", 1.12),
                    ]
                ),
            ),
            (
                "episode_steps",
                [
                    "1. Cell C-18 indexed on Cathode-Howe tankhouse; cell armed 280 A/m2.",
                    "2. Caps: electrolyte 65.0 C, bus 1.80 V, density 320 A/m2.",
                    "3. Encoder precursor at 0.920 ms.",
                    "4. Race window [4.180, 4.480] ms.",
                    "5. Electrolyte RTD 58.4 C at 4.180 ms (winner).",
                    "6. Bus smear 1.12 V at 4.360 ms (loser by 180 us).",
                    "7. Gate at 4.940 ms: ACCEPT 280 A/m2 / 58.4 C already legal.",
                    "8. Strip continues; no extra hold.",
                    "9. 7 min cooldown confirms bus still under 1.80 V.",
                    "10. QA: ACCEPT params identical to proposed.",
                ],
            ),
        ]
    )
    proposed = OrderedDict(
        [
            ("name", "strip_280Am2"),
            ("parameters", params),
            (
                "evidence",
                OrderedDict(
                    [
                        ("elyte_C", 58.4),
                        ("elyte_cap_C", 65.0),
                        ("density_A_m2", 280.0),
                        ("density_cap_A_m2", 320.0),
                        ("bus_V", 1.12),
                        ("bus_cap_V", 1.80),
                        ("race_margin_us", 180),
                        ("combined_jitter_us", 58),
                        ("t_gate_us", 4940),
                    ]
                ),
            ),
            (
                "basis",
                "Planner proposes a 280 A/m2 strip because electrolyte 58.4 C is 6.6 C under the 65.0 C "
                "cap and bus 1.12 V is under 1.80 V.",
            ),
        ]
    )
    safety = OrderedDict(
        [
            ("decision", "ACCEPT"),
            ("correctness", "correct"),
            (
                "rationale",
                "Electrolyte 58.4 C won by 180 us and is under 65.0 C. Bus 1.12 V is under "
                "1.80 V. Density 280 A/m2 is under 320 A/m2. ACCEPT the already-legal strip.",
            ),
            (
                "constraint_checked",
                OrderedDict(
                    [
                        (
                            "elyte_C",
                            OrderedDict(
                                [
                                    ("cap", 65.0),
                                    ("observed", 58.4),
                                    ("executed_density_A_m2", 280.0),
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
            ("name", "strip_280Am2"),
            ("parameters", params),
            (
                "gate_effect",
                "ACCEPT: 280 A/m2 strip and 58.4 C electrolyte unchanged. Routing relay.rtd.elyte -> "
                "policy.go_accept.",
            ),
        ]
    )
    future = OrderedDict(
        [
            (
                "summary",
                "Correct ACCEPT left Cell C-18 on a 280 A/m2 / 58.4 C strip. Bus hitch did not "
                "justify a hold. 7 min cooldown confirmed smear still under 1.80 V.",
            ),
            (
                "state_delta",
                OrderedDict(
                    [
                        ("cell", "still 280 A/m2 / 58.4 C"),
                        ("bus", "1.12 V under 1.80 cap"),
                        ("tankhouse", "on schedule"),
                        ("hold", "none applied"),
                    ]
                ),
            ),
            (
                "surprises",
                [
                    "Bus 1.12 V hitch is residual, not a voltage trip.",
                    "Delayed (7 min): cooldown restacks C-18 without a recovery hold.",
                ],
            ),
            (
                "race_result",
                OrderedDict(
                    [
                        ("winner", "rtd.elyte.c (4.180 ms, 58.4 C)"),
                        ("loser", "bus.v.smear (4.360 ms, 1.12 V)"),
                        ("margin_us", 180),
                        (
                            "counterfactual_if_reversed",
                            "Bus-first by < 180 us would only delay confirmation. The strip stays "
                            "legal either way; ACCEPT is still required.",
                        ),
                    ]
                ),
            ),
            ("reward_inflection_t_us", 4940),
            (
                "reward_inflection_note",
                "Task credit lands at the ACCEPT (4.940 ms, tick 4). Cooldown is delayed surprise.",
            ),
            ("delayed_surprise_s", 420.0),
            ("cooldown_s", 420),
        ]
    )
    ras = raster_core(
        22,
        64,
        36,
        51,
        routing(
            "relay.rtd.elyte",
            "policy.go_accept",
            [
                ("relay.rtd.elyte", "policy.go_accept", 0.66),
                ("relay.bus.smear", "policy.hitch_hold", 0.20),
            ],
            "dopamine",
            0.04,
            "legal_strip_stdp; DA tags the go_accept bind at the electrolyte win",
        ),
        excerpt,
    )
    gate = OrderedDict(
        [
            ("decision_window_ms", 0.30),
            ("decision", "ACCEPT"),
            (
                "populations",
                [
                    pop("go_accept", 40, 0.50, 160.0, 2),
                    pop("hitch_hold", 40, 0.80, 10.0, 0),
                    pop("elyte_cap_veto", 20, 0.75),
                ],
            ),
        ]
    )
    return OrderedDict(
        [
            ("id", "ttf-r42-230"),
            (
                "title",
                "Cathode-Howe tankhouse / Cell C-18: electrolyte 58.4 C beats bus smear 1.12 V by 180 us; "
                "ACCEPT already-legal 280 A/m2 strip",
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
                    "Correct ACCEPT of an already-legal electrorefining strip. total +1.14 = "
                    "0.44 + 0.32 + 0.18 + 0.12 + 0.08.",
                ),
            ),
            ("raster", ras),
            ("gate_snn", gate),
            (
                "meta",
                meta_block(
                    "copper-electrorefining",
                    [
                        "accept",
                        "already-legal",
                        "elyte-vs-bus",
                        "sidecar-convictable",
                        "designed",
                    ],
                    "Teaches that an electrolyte RTD under cap can confirm an already-legal strip without "
                    "a bus hitch becoming a hold.",
                    5,
                ),
            ),
        ]
    )

