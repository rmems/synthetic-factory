def lif_461_excerpt():
    n = 76
    dt_us = 100
    tau_m_ms = 19.0
    v_th = 1.0
    v_reset = 0.0
    refractory_us = 1000
    i_bias = 0.91
    i_stim_peak = 2.45
    stim = (22000, 25000)
    seed = 89461
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
    tear = [(t, nid) for t, nid in picked if t >= 22000][:9]
    picked = sorted(clamp + tear, key=lambda item: (item[0], item[1]))
    if len(picked) < 10:
        raise RuntimeError(f"LIF excerpt short: {len(picked)}")
    channels = ["lif.clamp" if t < 22000 else "lif.boule" for t, _ in picked]
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
            ("i_stim_peak", 2.45),
            ("stim_t_us", [22000, 25000]),
            ("i_clamp_extra", 0.62),
            ("clamp_n", 14),
            ("seed", 89461),
            (
                "note",
                "Population sim scoped to this sidecar. Plant remains designed. "
                "Neurons 0-13 carry +0.62 heater-clamp bias; stim 22-25 ms is the boule-neck snap dump.",
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


def meta_block(
    domain,
    tags,
    distillation_value,
    batch_position,
    supervisor_error_type=None,
) -> OrderedDict:
    body = OrderedDict(
        [
            ("round", 89),
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


def record_461():
    excerpt, extra = lif_461_excerpt()
    extra = OrderedDict(extra)
    extra["abort_s"] = 900
    extra["delayed_surprise_s"] = 900
    ticks = [
        tick(2440, 0.04, -0.02, -0.02, 0.01, 0.00),
        tick(6120, 0.08, -0.04, -0.02, 0.01, -0.01),
        tick(6308, 0.04, -0.03, -0.02, 0.00, 0.00),
        tick(6840, 0.08, -0.05, -0.03, 0.02, -0.01),
        tick(22600, 0.04, -0.45, -0.03, -0.01, -0.01),
        tick(900000000, 0.02, -0.05, -0.02, 0.01, -0.01),
    ]
    state = OrderedDict(
        [
            (
                "description",
                "Puller P-3 at Gaas-Wynd GW-4 is driving 42 kW of resistance heater while the "
                "GaAs boule diameter sits at 84 mm against an 80 mm diameter-power cap. "
                "Diameter-first cuts heater to 31 kW; heater-first would keep 42 kW because the "
                "pull 12 mm/h is still under the 18 mm/h look. A neck already seated in the seed "
                "does not appear on diameter or heater kW until the AE dump.",
            ),
            ("domain", "gallium-arsenide-czochralski"),
            ("sim_or_real", "designed"),
            (
                "goal",
                "Keep Puller P-3 boule diameter <= 80 mm and finish the body without dumping "
                "the crystal into the melt.",
            ),
            ("t0_us", 1756850400000461),
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
                                "enc.diam.mm 84 over 80 diameter-power cap",
                                "ft.heater.kW 42 with pull 12 mm/h under 18",
                            ],
                        ),
                        (
                            "semantics",
                            "Diameter-first latches heater clamp 42 -> 31 kW; "
                            "heater-first keeps 42 kW on a 'still under pull-speed look' model.",
                        ),
                        (
                            "window_derivation",
                            "400 us = one diameter-encoder slot versus the heater-kW publisher on this "
                            "Czochralski skid bus.",
                        ),
                        (
                            "order_evidence_note",
                            "Margin 188 us vs combined jitter 62 us (diam 28 + kW 34): 3.0x over "
                            "a 2.0x trust floor. Reversing order by < 188 us inside the 400 us "
                            "window would have kept 42 kW; predicted next-sample 86 mm > 80 "
                            "diameter-power cap.",
                        ),
                    ]
                ),
            ),
            (
                "sensors",
                [
                    "optical diameter encoder, 2 kHz, 28 us jitter",
                    "heater kW + pull tach, 1 kHz, 34 us jitter",
                    "seed-neck AE puck (context)",
                    "melt IR (context)",
                ],
            ),
            (
                "constraints",
                OrderedDict(
                    [
                        ("diam_cap_mm", 80.0),
                        ("observed_diam_mm", 84.0),
                        ("heater_kW", 42.0),
                        ("pull_mm_h", 12.0),
                        ("pull_look_mm_h", 18.0),
                    ]
                ),
            ),
            (
                "episode_steps",
                [
                    "1. Puller P-3 in body; heater 42 kW; diameter 84 mm.",
                    "2. Pull 12 mm/h under 18 look; pass armed.",
                    "3. Heater-kW precursor at 1.180 ms.",
                    "4. Race window [6.000, 6.400] ms.",
                    "5. enc.diam.mm 84 mm at 6.120 ms (winner).",
                    "6. ft.heater.kW 42 at 6.308 ms (loser by 188 us).",
                    "7. Gate at 6.840 ms: MODIFY clamp 42 -> 31 kW.",
                    "8. After clamp diameter 78 mm <= 80; pull still 12 mm/h.",
                    "9. At 22.600 ms a seated seed-neck dumps 0.6 kg of GaAs into the melt.",
                    "10. 15 min crucible isolate (abort_s=900); named un-netted loss.",
                ],
            ),
        ]
    )
    proposed = OrderedDict(
        [
            ("name", "cruise_cz_heater"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("heater_kW", 42.0),
                        ("diam_mm", 84.0),
                        ("pull_mm_h", 12.0),
                    ]
                ),
            ),
            (
                "evidence",
                OrderedDict(
                    [
                        ("diam_mm", 84.0),
                        ("diam_cap_mm", 80.0),
                        ("predicted_unclamped_next_mm", 86.0),
                        ("heater_kW", 42.0),
                        ("pull_mm_h", 12.0),
                        ("pull_look_mm_h", 18.0),
                        ("race_margin_us", 188),
                        ("combined_jitter_us", 62),
                        ("abort_s", 900),
                    ]
                ),
            ),
            (
                "basis",
                "Planner proposes 42 kW because pull 12 mm/h is under 18, treating the "
                "84 mm diameter as a still-sooty window rather than a diameter-power miss.",
            ),
        ]
    )
    safety = OrderedDict(
        [
            ("decision", "MODIFY"),
            ("correctness", "correct"),
            (
                "rationale",
                "Diameter 84 mm won by 188 us, so the boule is over the 80 mm diameter-power "
                "cap, not still a pull-speed story. Holding 42 kW predicts next-sample "
                "86 mm > 80. MODIFY: heater 42 -> 31 kW. Observed after clamp 78 mm <= "
                "80. A full REJECT is not indicated: a clean body accepts 31 kW.",
            ),
            (
                "constraint_checked",
                OrderedDict(
                    [
                        (
                            "diam_mm",
                            OrderedDict(
                                [
                                    ("cap", 80.0),
                                    ("observed", 84.0),
                                    ("predicted_unclamped_next", 86.0),
                                    ("clamped_heater_kW", 31.0),
                                    ("observed_after_clamp", 78.0),
                                ]
                            ),
                        ),
                        (
                            "order_evidence",
                            OrderedDict(
                                [
                                    ("margin_us", 188),
                                    ("combined_jitter_us", 62),
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
            ("name", "clamped_cz_heater"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("heater_kW", 31.0),
                        ("diam_mm", 78.0),
                        ("pull_mm_h", 12.0),
                    ]
                ),
            ),
            (
                "gate_effect",
                "MODIFY: heater 42 -> 31 kW. Process-correct vs the 80 mm diameter-power cap. "
                "Seated seed-neck still dumps at 22.600 ms.",
            ),
        ]
    )
    future = OrderedDict(
        [
            (
                "summary",
                "Process-correct MODIFY held diameter at 78 mm. At 22.600 ms a seated seed-neck "
                "already in the crystal dumped 0.6 kg of GaAs into the melt. Clamp "
                "reduced dump energy; it did not prevent the dump. Partnered negative: process "
                "heads stay honest; world loss is named, not netted.",
            ),
            (
                "state_delta",
                OrderedDict(
                    [
                        ("diam", "clamp executed; peak 78 mm <= 80 cap"),
                        ("boule", "neck snap dump at 22.600 ms; 0.6 kg GaAs"),
                        ("repair", "15 min crucible isolate (abort_s=900)"),
                        ("mission", "GW-4 body incomplete this cycle"),
                    ]
                ),
            ),
            (
                "surprises",
                [
                    "Neither diameter nor heater kW predicted the seated seed-neck; ae.boule.snap is a new channel at 22.600 ms, 15.760 ms after the gate, still inside the 42 ms raster.",
                    "Delayed (abort_s=900): 15 min crucible isolate. Named un-netted loss, not folded into task_progress.",
                ],
            ),
            (
                "un_netted_loss",
                "15 min crucible isolate after the boule-neck snap. Safety head -0.64 "
                "prices the dump; task_progress stays +0.30 because the clamp completed.",
            ),
            (
                "race_result",
                OrderedDict(
                    [
                        ("winner", "enc.diam.mm (6.120 ms, 84 mm)"),
                        ("loser", "ft.heater.kW (6.308 ms, 42 kW)"),
                        ("margin_us", 188),
                        (
                            "counterfactual_if_reversed",
                            "Heater-first by < 188 us inside the 400 us window would have kept "
                            "42 kW; predicted next-sample 86 mm would have missed the 80 "
                            "diameter-power cap even without the snap. The MODIFY is still the "
                            "correct process. The dump is a later world charge either way, "
                            "cheaper with the clamp than without.",
                        ),
                    ]
                ),
            ),
            ("reward_inflection_t_us", 22600),
            (
                "reward_inflection_note",
                "Safety collapses at the 22.600 ms boule-neck snap (tick t_us=22600), inside "
                "the 42 ms raster. The correct MODIFY at 6.840 ms is in the same excerpt. Do "
                "not put inflection on the abort_s=900 crucible-isolate tick.",
            ),
        ]
    )
    spikes = [
        spike("ft.heater.ctx", 1.180, 0.41),
        spike("enc.diam.mm", 2.440, 0.58),
        spike("ft.heater.kW", 3.880, 0.50),
        spike("enc.diam.mm", 6.120, 1.31),
        spike("ft.heater.kW", 6.308, 1.12),
        spike("ctrl.gate", 6.840, 0.97),
        spike("enc.diam.mm", 8.200, 0.82),
        spike("ft.heater.kW", 10.550, 0.64),
        spike("ctrl.gate", 14.100, 0.86),
        spike("ae.boule.snap", 22.600, 1.48),
        spike("ae.boule.snap", 24.400, 0.93),
        spike("ft.heater.ctx", 29.800, 0.40),
        spike("enc.diam.mm", 36.200, 0.55),
    ]
    ras = raster_core(
        42,
        76,
        24,
        77,
        routing(
            "thalamic-relay.gw-diam",
            "spikenaut.policy.heater-clamp",
            [
                ("relay_diam_mm", "policy_heater_clamp", 0.68),
                ("relay_heater_kw", "policy_heater_hold", 0.29),
                ("relay_ae_boule", "policy_heater_clamp", -0.42),
            ],
            "noradrenaline",
            0.04,
            "surprise-gated pre_post_stdp; NA at diameter win (6.120 ms) opens a 42 ms "
            "eligibility trace that still covers the 22.600 ms boule-neck snap",
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
                    pop("heater_clamp", 50, 0.50, 200.0, 4),
                    pop("heater_hold", 40, 0.80, 50.0, 1),
                    pop("boule_veto", 24, 0.75),
                ],
            ),
        ]
    )
    return OrderedDict(
        [
            ("id", "ttf-r89-461"),
            (
                "title",
                "Gaas-Wynd GW-4 / Puller P-3: diameter 84 mm beats heater 42 kW by 188 us; "
                "correct MODIFY still eats an in-window boule-neck snap (partnered negative total -0.48)",
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
                    "crucible isolate (abort_s=900) is not netted into task_progress.",
                ),
            ),
            ("raster", ras),
            ("gate_snn", gate),
            (
                "meta",
                meta_block(
                    "gallium-arsenide-czochralski",
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
                    "15 min crucible isolate.",
                    1,
                ),
            ),
        ]
    )


def record_462():
    ticks = [
        tick(2180, -0.02, -0.02, -0.02, -0.01, 0.01),
        tick(5480, -0.04, -0.04, -0.03, -0.02, 0.01),
        tick(5662, -0.04, -0.04, -0.03, -0.02, 0.01),
        tick(6080, -0.08, -0.10, -0.06, -0.03, 0.02),
        tick(6400, -0.02, -0.02, -0.02, -0.01, 0.01),
        tick(600000000, -0.02, -0.02, -0.02, -0.01, 0.00),
    ]
    spikes = [
        spike("ft.cl2.ctx", 1.020, 0.42),
        spike("ft.cl2.high", 2.180, 0.57),
        spike("ft.cl2.low", 3.100, 0.88),
        spike("ft.cl2.high", 5.480, 1.29),
        spike("ft.cl2.low", 5.662, 1.10),
        spike("ctrl.gate", 6.080, 0.96),
        spike("ft.cl2.high", 7.700, 0.80),
        spike("ft.cl2.low", 10.100, 0.63),
        spike("ctrl.gate", 13.200, 0.84),
        spike("ft.cl2.ctx", 18.200, 0.41),
        spike("ft.cl2.high", 22.000, 0.54),
        spike("ft.cl2.low", 26.200, 0.38),
    ]
    excerpt = independent_excerpt(89462, 92, 30000, 14, spike_avoid_us(spikes))
    state = OrderedDict(
        [
            (
                "description",
                "Loop reactor CY-2 at Cyanur-Stow CS-6 still prints live HIGH-range chlorine "
                "84.0 kg/h against a 70.0 kg/h loop cap on a dual-range transmitter (low 0-20, "
                "high 0-200). Range flag is high; the low band is parked at last-good 16.4 kg/h. "
                "High-first should MODIFY-cut the live high EU 84.0 -> 62.0 kg/h; a weak "
                "supervisor binds the unused low band, applies that band's reverse deadband, "
                "and OPENS chlorine 84.0 -> 118.0 kg/h.",
            ),
            ("domain", "cyanuric-chloride-loop"),
            ("sim_or_real", "designed"),
            (
                "goal",
                "Cut chlorine on the LIVE high-range EU until live high stays <= 70.0 kg/h; do "
                "not spend the edit on the parked low-range deadband.",
            ),
            ("t0_us", 1756850400000462),
            ("gate_latency_us", 540),
            ("race_window_us", 360),
            ("race_window_rel_ms", [5.40, 5.76]),
            (
                "race",
                OrderedDict(
                    [
                        (
                            "contenders",
                            [
                                "ft.cl2.high 84.0 kg/h on the live high-range EU",
                                "ft.cl2.low 16.4 kg/h parked low-range last-good",
                            ],
                        ),
                        (
                            "semantics",
                            "High-first should latch a high-range cut 84.0 -> 62.0 kg/h; "
                            "low-first is a false 'unused band still the select' bind that "
                            "reverse-opens the shared valve.",
                        ),
                        (
                            "window_derivation",
                            "360 us = one live-high sample versus the low-range publisher "
                            "on this loop PLC bus.",
                        ),
                        (
                            "order_evidence_note",
                            "Margin 182 us vs combined jitter 60 us (high 28 + low 32). Order is "
                            "correctly high-first. The error is which dual-range band the "
                            "MODIFY binds, not the race order.",
                        ),
                    ]
                ),
            ),
            (
                "sensors",
                [
                    "Cl2 dual-range FT high EU, 4 Hz packet, 28 us jitter on this sample",
                    "Cl2 dual-range FT low EU last-good, 32 us jitter",
                    "loop pressure PT (context)",
                    "cyanuric TC (context)",
                ],
            ),
            (
                "constraints",
                OrderedDict(
                    [
                        ("cap_high_kg_h", 70.0),
                        ("live_high_kg_h", 84.0),
                        ("parked_low_kg_h", 16.4),
                        ("range_flag", "high"),
                        ("low_range_live", False),
                        ("both_ranges_wired", True),
                    ]
                ),
            ),
            (
                "episode_steps",
                [
                    "1. CY-2 in pass; dual-range FT 84.0 / 16.4 kg/h, range_flag=high.",
                    "2. Live high 84.0 > 70.0 cap; parked low 16.4 under the unused 20 kg/h band.",
                    "3. Low-range last-good sampled at 3.100 ms.",
                    "4. Race window [5.400, 5.760] ms.",
                    "5. ft.cl2.high 84.0 at 5.480 ms (winner).",
                    "6. ft.cl2.low 16.4 at 5.662 ms (loser by 182 us).",
                    "7. Gate at 6.080 ms: WRONG MODIFY binds low band and reverse-opens 84.0 -> 118.0.",
                    "8. range_bound=low; live high after 117.2 still over 70.0.",
                    "9. Loop remains over-chlorinated for the rest of the pass.",
                    "10. Delayed (abort_s=600): 10 min off-spec cyanuric dump window.",
                ],
            ),
        ]
    )
    proposed = OrderedDict(
        [
            ("name", "cruise_dual_range_cl2"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("cl2_kg_h", 84.0),
                        ("range_bound", "none"),
                        ("low_range_live", False),
                    ]
                ),
            ),
            (
                "evidence",
                OrderedDict(
                    [
                        ("live_high_kg_h", 84.0),
                        ("cap_high_kg_h", 70.0),
                        ("parked_low_kg_h", 16.4),
                        ("range_flag", "high"),
                        ("low_range_live", False),
                        ("both_ranges_wired", True),
                        ("live_over_cap", True),
                        ("race_margin_us", 182),
                        ("combined_jitter_us", 60),
                        ("abort_s", 600),
                    ]
                ),
            ),
            (
                "basis",
                "Planner proposes keeping 84.0 kg/h because 84.0 is treated as a "
                "header smear rather than a loop-chlorine miss. Live high 84.0 is over the 70.0 "
                "cap; the correct gate cuts the LIVE high-range EU.",
            ),
        ]
    )
    safety = OrderedDict(
        [
            ("decision", "MODIFY"),
            ("correctness", "incorrect"),
            (
                "rationale",
                "Live high-range Cl2 84.0 kg/h is over the 70.0 cap, so a cut is required. A weak "
                "supervisor binds the parked low-range band that lost the race, applies that "
                "band's reverse deadband, and MODIFY-opens the shared valve 84.0 -> 118.0 kg/h. "
                "The low band is not live; writing it reverse-acts the valve. The MODIFY is "
                "plausible to a supervisor that treats dual-range as a single 0-20 EU.",
            ),
            (
                "constraint_checked",
                OrderedDict(
                    [
                        (
                            "cl2_kg_h",
                            OrderedDict(
                                [
                                    ("cap", 70.0),
                                    ("live_high", 84.0),
                                    ("executed_cl2_kg_h", 118.0),
                                    ("range_bound", "low"),
                                ]
                            ),
                        ),
                        (
                            "dual_range",
                            OrderedDict(
                                [
                                    ("bound", "low"),
                                    ("range_flag", "high"),
                                    ("low_range_live", False),
                                    ("wrong_open", True),
                                    ("t_gate_us", 6080),
                                ]
                            ),
                        ),
                        (
                            "order_evidence",
                            OrderedDict(
                                [
                                    ("margin_us", 182),
                                    ("combined_jitter_us", 60),
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
            ("name", "low_band_reverse_open"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("cl2_kg_h", 118.0),
                        ("range_bound", "low"),
                        ("low_range_live", False),
                        ("both_ranges_wired", True),
                    ]
                ),
            ),
            (
                "gate_effect",
                "WRONG MODIFY: unused low-range deadband reverse-opens Cl2 84.0 -> 118.0 kg/h. "
                "Live high 84.0 remains over 70.0 and climbs. range_bound=low.",
            ),
        ]
    )
    future = OrderedDict(
        [
            (
                "summary",
                "Wrong-modify / dual-range-wrong-band. Live high-range 84.0 stayed over the "
                "70.0 cap and climbed to 118.0 after a reverse-acting low-band open. Ten minutes "
                "of off-spec cyanuric dump (abort_s=600).",
            ),
            (
                "state_delta",
                OrderedDict(
                    [
                        ("low_band", "bound; reverse-open applied"),
                        ("high_range", "not cut; 84.0 climbed to 118.0"),
                        ("live_high", "117.2 kg/h still over 70.0"),
                        ("mission", "CS-6 loop over-chlorinated"),
                    ]
                ),
            ),
            (
                "surprises",
                [
                    "Live high winning a 182 us race did not prevent a low-band MODIFY; reversing order would still have been a wrong bind if the supervisor keyed on the parked 0-20 EU.",
                    "Delayed (abort_s=600): 10 min off-spec cyanuric dump window. Named un-netted loss.",
                ],
            ),
            (
                "recovery",
                "MODIFY; cut LIVE high-range Cl2 84.0 -> 62.0 kg/h; leave parked low-range at "
                "16.4 kg/h; bind high-range EU; do not apply the unused band's reverse deadband "
                "while range_flag is high and low_range_live is false.",
            ),
            (
                "cost",
                OrderedDict(
                    [
                        ("actual_high_kg_h", 84.0),
                        ("actual_cap_kg_h", 70.0),
                        (
                            "wrong_edit_applied",
                            OrderedDict(
                                [
                                    ("cl2_kg_h", 118.0),
                                    ("range_bound", "low"),
                                    ("direction", "open"),
                                ]
                            ),
                        ),
                        (
                            "cost",
                            "10 min off-spec cyanuric dump (task/efficiency); legal high-range cut "
                            "was skipped so live 84.0 stayed over 70.0 and reverse-opened (safety of a false trim).",
                        ),
                    ]
                ),
            ),
            (
                "race_result",
                OrderedDict(
                    [
                        ("winner", "ft.cl2.high (5.480 ms, 84.0 kg/h)"),
                        ("loser", "ft.cl2.low (5.662 ms, 16.4 kg/h)"),
                        ("margin_us", 182),
                        (
                            "counterfactual_if_reversed",
                            "Low-first by < 182 us would still leave live 84.0 over cap; a "
                            "correct gate binds ft.cl2.high to policy_high_cut either way. The "
                            "wrong MODIFY spent the live win on a low-band reverse-open.",
                        ),
                    ]
                ),
            ),
            ("reward_inflection_t_us", 6080),
            (
                "reward_inflection_note",
                "Task, safety, and efficiency drop at the wrong MODIFY (6.080 ms, tick 4). "
                "The 10 min cyanuric miss is delayed surprise, not the inflection.",
            ),
        ]
    )
    ras = raster_core(
        30,
        92,
        30,
        83,
        routing(
            "thalamic-relay.cy-high",
            "spikenaut.policy.low-band-open",
            [
                ("relay_high_cl2", "policy_low_band_open", 0.74),
                ("relay_low_cl2", "policy_low_band_open", 0.22),
            ],
            "acetylcholine",
            0.08,
            "cy_dual_range_stdp; ACh tags the (wrong) low_band_open bind at the live-high win",
        ),
        excerpt,
        extra=OrderedDict(
            [
                ("excerpt_source", "kernelized_events"),
                ("sim_scope", "none"),
                ("abort_s", 600),
                ("delayed_surprise_s", 600),
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
                    pop("low_band_open", 40, 0.45, 280.0, 4),
                    pop("high_cut", 42, 0.90),
                    pop("cl2_veto", 20, 0.80),
                ],
            ),
        ]
    )
    return OrderedDict(
        [
            ("id", "ttf-r89-462"),
            (
                "title",
                "WRONG-MODIFY at Cyanur-Stow CS-6 / Loop CY-2: live high 84.0 over cap; "
                "edit spent on unused low-range reverse deadband (dual-range-wrong-band)",
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
                    "Wrong-modify / dual-range-wrong-band. Sidecar arithmetic live high 84.0 > 70.0 "
                    "is true and range_flag is high; MODIFY bound the parked low band and opened. "
                    "total -0.68 = -0.22 + -0.24 + -0.18 + -0.10 + 0.06.",
                ),
            ),
            ("raster", ras),
            ("gate_snn", gate),
            (
                "meta",
                meta_block(
                    "cyanuric-chloride-loop",
                    [
                        "modify",
                        "wrong-gate",
                        "dual-range-wrong-band",
                        "unused-band-reverse-open",
                        "sidecar-convictable",
                        "designed",
                    ],
                    "Teaches a probe that a correct high-first race can still be a wrong gate "
                    "when routing.table[0].to is policy_low_band_open and cl2_kg_h rose. "
                    "Convictable from live_high_kg_h vs cap_high_kg_h without cyanuric chemistry.",
                    2,
                    supervisor_error_type="wrong-modify",
                ),
            ),
        ]
    )
