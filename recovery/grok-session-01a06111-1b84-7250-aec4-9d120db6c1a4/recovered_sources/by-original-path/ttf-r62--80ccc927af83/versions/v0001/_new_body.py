def lif_326_excerpt():
    n = 78
    dt_us = 100
    tau_m_ms = 18.0
    v_th = 1.0
    v_reset = 0.0
    refractory_us = 1000
    i_bias = 0.90
    i_stim_peak = 2.52
    stim = (20600, 24200)
    seed = 62326
    window_us = 44000
    i_clamp_extra = 0.66
    clamp_n = 15
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
    early = [(t, nid) for t, nid in spikes if t < 20600]
    burst = [(t, nid) for t, nid in spikes if 20600 <= t < 24200]
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
            group = [1 for tt, _ in picked if (tt < 20600) == (pool[0][0] < 20600)]
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
    take(burst, 9, label_times=(21800, 22600, 23600))
    clamp = [(t, nid) for t, nid in picked if t < 20600][:7]
    shear = [(t, nid) for t, nid in picked if t >= 20600][:9]
    picked = sorted(clamp + shear, key=lambda item: (item[0], item[1]))
    if len(picked) < 8:
        raise ValueError(
            f"LIF excerpt too short {len(picked)} (early={len(early)} burst={len(burst)})"
        )
    channels = ["lif.clamp" if t < 20600 else "lif.shear" for t, _ in picked]
    lif = OrderedDict(
        [
            ("model", "leaky_integrate_and_fire"),
            ("n", 78),
            ("dt_us", 100),
            ("tau_m_ms", 18.0),
            ("v_rest", 0.0),
            ("v_reset", 0.0),
            ("v_th", 1.0),
            ("r_m", 1.0),
            ("refractory_us", 1000),
            ("i_bias", 0.90),
            ("i_stim_peak", 2.52),
            ("stim_t_us", [20600, 24200]),
            ("i_clamp_extra", 0.66),
            ("clamp_n", 15),
            ("seed", 62326),
            (
                "note",
                "Population sim scoped to this sidecar. Plant remains designed. "
                "Neurons 0-14 carry +0.66 air-clamp bias; stim 20.6-24.2 ms is the grid-nozzle shear.",
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


def record_326():
    excerpt, extra = lif_326_excerpt()
    ticks = [
        tick(2220, 0.05, -0.02, -0.02, 0.01, 0.00),
        tick(6240, 0.07, -0.04, -0.02, 0.01, -0.01),
        tick(6458, 0.05, -0.03, -0.02, 0.01, 0.00),
        tick(7040, 0.08, -0.06, -0.03, 0.02, -0.01),
        tick(21800, 0.05, -0.42, -0.03, -0.01, -0.03),
        tick(960000000, 0.02, -0.05, -0.02, 0.01, -0.01),
    ]
    state = OrderedDict(
        [
            (
                "description",
                "Riser-R11 at Acrylo-Whin AW-7 is already feeding 18.4 kNm3/h air into a 448 C "
                "Sohio dense bed against a 440 C afterburner cap. An air-first latch clamps the "
                "air; a propylene-first story would keep the 18.4 kNm3/h cruise. Stored shear in "
                "the grid nozzle is not yet an observable of either race channel.",
            ),
            ("domain", "acrylonitrile-sohio"),
            ("sim_or_real", "designed"),
            (
                "goal",
                "Finish the AW-7 Sohio pass, keep dense-bed temperature <= 440 C, and leave the "
                "air-grid nozzles unmarked.",
            ),
            ("t0_us", 1756850400000326),
            ("gate_latency_us", 800),
            ("race_window_us", 420),
            ("race_window_rel_ms", [6.20, 6.62]),
            (
                "race",
                OrderedDict(
                    [
                        (
                            "contenders",
                            [
                                "rtd.bed.C 448 C pulse",
                                "ft.air.knm3 18.4 kNm3/h cruise",
                            ],
                        ),
                        (
                            "semantics",
                            "Air-first latches air 18.4 -> 14.2 kNm3/h; propylene-first keeps "
                            "cruise on a still-cooling bed model.",
                        ),
                        (
                            "window_derivation",
                            "420 us = one 2 kHz dense-bed RTD sample minus air-orifice group "
                            "delay on this Sohio-riser bus.",
                        ),
                        (
                            "order_evidence_note",
                            "Margin 218 us vs combined jitter ~66 us (bed 30 + air 36): 3.3x over "
                            "a 2.0x trust floor. Reversing order by < 218 us inside the 420 us window "
                            "would have kept 18.4 kNm3/h cruise; predicted next-sample 443 C > 440 cap.",
                        ),
                    ]
                ),
            ),
            (
                "sensors",
                [
                    "dense-bed RTD, 2 kHz, 30 us timestamp jitter",
                    "air-orifice FT, 1 kHz, 36 us jitter",
                    "grid-nozzle AE puck (context until the shear)",
                    "propylene FT (context)",
                ],
            ),
            (
                "constraints",
                OrderedDict(
                    [
                        ("bed_cap_C", 440.0),
                        ("observed_bed_C", 448.0),
                        ("proposed_air_knm3h", 18.4),
                        ("propylene_tph", 9.6),
                    ]
                ),
            ),
            (
                "episode_steps",
                [
                    "1. Riser-R11 indexed on Acrylo-Whin AW-7; air armed at 18.4 kNm3/h.",
                    "2. Cruise 18.4 kNm3/h; dense bed 448 C against 440 C afterburner cap.",
                    "3. Air precursor at 1.180 ms; bed warm-start 448 C.",
                    "4. Race window [6.200, 6.620] ms opens on the Sohio-riser bus.",
                    "5. rtd.bed.C 448 C at 6.240 ms (winner).",
                    "6. ft.air.knm3 18.4 kNm3/h at 6.458 ms (loser by 218 us).",
                    "7. Gate at 7.040 ms (winner + 800 us): MODIFY clamp 18.4 -> 14.2 kNm3/h.",
                    "8. Clamp executes; next-sample bed 434 C < 440 cap.",
                    "9. At 21.800 ms stored strain still shears an 18 mm grid nozzle; AE burst.",
                    "10. Riser isolate 16 min (abort_s=960); named un-netted loss, not folded into process heads.",
                ],
            ),
        ]
    )
    proposed = OrderedDict(
        [
            ("name", "cruise_air_184"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("air_knm3h", 18.4),
                        ("propylene_tph", 9.6),
                        ("nh3_tph", 11.2),
                    ]
                ),
            ),
            (
                "evidence",
                OrderedDict(
                    [
                        ("bed_C", 448.0),
                        ("bed_cap_C", 440.0),
                        ("predicted_unclamped_next_C", 443.0),
                        ("air_knm3h", 18.4),
                        ("race_margin_us", 218),
                        ("combined_jitter_us", 66),
                        ("abort_s", 960),
                    ]
                ),
            ),
            (
                "basis",
                "Planner proposes 18.4 kNm3/h cruise: 448 C looks like a cyclone-return spike, not "
                "afterburner contact, and R11 volume is treated as still open.",
            ),
        ]
    )
    safety = OrderedDict(
        [
            ("decision", "MODIFY"),
            ("correctness", "correct"),
            (
                "rationale",
                "Bed 448 C won by 218 us, so the dense phase is loading heat, not still cooling. "
                "Holding 18.4 kNm3/h predicts next-sample 443 C > 440 cap. MODIFY: air 18.4 -> 14.2 "
                "kNm3/h. Observed after clamp 434 C < 440. A full REJECT is not indicated: a sound "
                "Sohio pass accepts 14.2 kNm3/h.",
            ),
            (
                "constraint_checked",
                OrderedDict(
                    [
                        (
                            "bed_C",
                            OrderedDict(
                                [
                                    ("cap", 440.0),
                                    ("observed", 448.0),
                                    ("predicted_unclamped_next", 443.0),
                                    ("clamped_air_knm3h", 14.2),
                                    ("observed_after_clamp", 434.0),
                                ]
                            ),
                        ),
                        (
                            "air_knm3h",
                            OrderedDict([("proposed", 18.4), ("clamped", 14.2)]),
                        ),
                        (
                            "order_evidence",
                            OrderedDict(
                                [
                                    ("margin_us", 218),
                                    ("combined_jitter_us", 66),
                                    ("ratio", 3.30),
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
            ("name", "clamped_air_142"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("air_knm3h", 14.2),
                        ("propylene_tph", 9.6),
                        ("nh3_tph", 11.2),
                    ]
                ),
            ),
            (
                "gate_effect",
                "MODIFY: air 18.4 -> 14.2 kNm3/h. Process-correct vs the 440 C afterburner "
                "cap. Grid-nozzle shear still occurs at 21.800 ms.",
            ),
        ]
    )
    future = OrderedDict(
        [
            (
                "summary",
                "Process-correct MODIFY held dense bed at 434 C. At 21.800 ms stored strain "
                "in the air-grid still sheared an 18 mm nozzle. Clamp reduced dump energy; "
                "it did not prevent the split. Partnered negative: process heads stay honest; "
                "world loss is named, not netted.",
            ),
            (
                "state_delta",
                OrderedDict(
                    [
                        ("air", "clamp executed; peak 434 C < 440"),
                        ("grid", "18 mm nozzle shear at 21.800 ms"),
                        ("repair", "16 min riser isolate (abort_s=960)"),
                        ("mission", "AW-7 Sohio pass incomplete this circuit"),
                    ]
                ),
            ),
            (
                "surprises",
                [
                    "Neither bed RTD nor air FT predicted the shear charge; ae.grid.shear is a new channel at 21.800 ms, 14.760 ms after the gate, still inside the 44 ms raster.",
                    "Delayed (abort_s=960): 16 min riser isolate. Named un-netted loss, not folded into task_progress.",
                ],
            ),
            (
                "un_netted_loss",
                "16 min riser isolate after an 18 mm grid-nozzle shear. Safety head -0.62 "
                "prices the split; task_progress stays +0.32 because the air clamp completed "
                "under the 440 C cap. World loss is named here, not subtracted from process heads.",
            ),
            (
                "race_result",
                OrderedDict(
                    [
                        ("winner", "rtd.bed.C (6.240 ms, 448 C)"),
                        ("loser", "ft.air.knm3 (6.458 ms, 18.4 kNm3/h)"),
                        ("margin_us", 218),
                        (
                            "counterfactual_if_reversed",
                            "Propylene-first by < 218 us inside the 420 us window would have kept "
                            "18.4 kNm3/h cruise; predicted next-sample 443 C would have exceeded "
                            "the 440 cap even without the shear charge. The MODIFY is still the "
                            "correct process. The shear is a later world charge either way, "
                            "cheaper with the clamp than without.",
                        ),
                    ]
                ),
            ),
            ("reward_inflection_t_us", 21800),
            (
                "reward_inflection_note",
                "Safety collapses at the 21.800 ms grid-nozzle shear (tick t_us=21800), inside "
                "the 44 ms raster. The correct MODIFY at 7.040 ms is in the same excerpt. Do "
                "not put inflection on the abort_s=960 isolate tick.",
            ),
            ("delayed_surprise_s", 960.0),
            ("abort_s", 960),
        ]
    )
    spikes = [
        spike("enc.air.ctx", 1.180, 0.42),
        spike("rtd.bed.C", 2.220, 0.61),
        spike("ft.air.knm3", 3.680, 0.50),
        spike("rtd.bed.C", 6.240, 1.32),
        spike("ft.air.knm3", 6.458, 1.14),
        spike("ctrl.gate", 7.040, 0.98),
        spike("rtd.bed.C", 8.520, 0.80),
        spike("ft.air.knm3", 11.300, 0.62),
        spike("ctrl.gate", 15.200, 0.84),
        spike("ae.grid.shear", 21.800, 1.46),
        spike("ae.grid.shear", 23.640, 0.91),
        spike("enc.air.ctx", 32.100, 0.41),
        spike("rtd.bed.C", 39.400, 0.53),
    ]
    ras = raster_core(
        44,
        78,
        25,
        86,
        routing(
            "thalamic-relay.sohio-bed",
            "spikenaut.policy.air-clamp",
            [
                ("relay.rtd.bed", "policy.air_clamp", 0.66),
                ("relay.ft.air", "policy.air_hold", 0.30),
                ("relay.ae.shear", "policy.air_clamp", -0.45),
            ],
            "noradrenaline",
            0.05,
            "surprise-gated pre_post_stdp; NA at bed win (6.240 ms) opens a 50 ms "
            "eligibility trace that still covers the 21.800 ms grid-nozzle shear",
        ),
        excerpt,
        extra=extra,
    )
    gate = OrderedDict(
        [
            ("decision_window_ms", 0.42),
            ("decision", "MODIFY"),
            (
                "populations",
                [
                    pop("air_clamp", 42, 0.50, 226.8, 4),
                    pop("air_hold", 42, 0.50, 56.7, 1),
                    pop("bed_veto", 24, 0.75),
                ],
            ),
        ]
    )
    return wrap_record(
        "ttf-r62-326",
        "Acrylo-Whin AW-7 / Riser-R11: bed 448 C beats air-feed by 218 us; correct "
        "MODIFY still eats an in-window grid-nozzle shear (partnered negative total -0.45)",
        state,
        spikes,
        proposed,
        safety,
        executed,
        future,
        ticks,
        "Partnered negative. Process-correct MODIFY; world still charges inside the "
        "44 ms raster. total -0.45 = 0.32 + -0.62 + -0.14 + 0.05 + -0.06. Named riser "
        "isolate (abort_s=960) is not netted into task_progress.",
        ras,
        gate,
        "acrylonitrile-sohio",
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
        "16 min riser isolate.",
        1,
    )


def record_327():
    ticks = [
        tick(1520, -0.02, -0.01, -0.03, -0.01, 0.01),
        tick(4160, -0.04, -0.02, -0.04, -0.02, 0.01),
        tick(4328, -0.03, -0.01, -0.04, -0.02, 0.01),
        tick(4880, -0.08, -0.04, -0.10, -0.05, 0.02),
        tick(6640, -0.02, -0.01, -0.03, -0.01, 0.01),
        tick(1260000000, -0.02, -0.01, -0.02, -0.01, 0.00),
    ]
    spikes = [
        spike("dp.feed.ctx", 0.760, 0.40),
        spike("pt.abs.torr", 1.520, 0.58),
        spike("pt.gauge.torr", 2.380, 0.51),
        spike("pt.abs.torr", 4.160, 1.32),
        spike("pt.gauge.torr", 4.328, 1.15),
        spike("ctrl.gate", 4.880, 1.00),
        spike("pt.abs.torr", 6.640, 0.74),
        spike("pt.gauge.torr", 8.100, 0.61),
        spike("ctrl.gate", 12.400, 0.82),
        spike("dp.feed.ctx", 16.200, 0.42),
        spike("pt.abs.torr", 21.100, 0.53),
        spike("pt.gauge.torr", 25.400, 0.47),
    ]
    excerpt = independent_excerpt(62327, 88, 26000, 14, spike_avoid_us(spikes))
    state = OrderedDict(
        [
            (
                "description",
                "Grid-G7 on Wash-Holm WH-3 is holding wash oil at 26.0 t/h with live column "
                "52 torr absolute against a 90 torr absolute vacuum-break trip. A gauge PT still "
                "prints -708 torr (52 minus 760 atm) and a dropped-sign 708 torr looks like a "
                "break. Live-abs-first should ACCEPT the wash; a weak supervisor that binds the "
                "unsigned gauge as absolute will REJECT a legal grid.",
            ),
            ("domain", "vacuum-wash-grid"),
            ("sim_or_real", "designed"),
            (
                "goal",
                "Keep 26.0 t/h wash oil on G7 while live P_abs stays <= 90 torr; do not spend a "
                "dropped-sign gauge on the furnace hold.",
            ),
            ("t0_us", 1756850400000327),
            ("gate_latency_us", 720),
            ("race_window_us", 340),
            ("race_window_rel_ms", [4.10, 4.44]),
            (
                "race",
                OrderedDict(
                    [
                        (
                            "contenders",
                            [
                                "pt.abs.torr 52 torr abs live",
                                "pt.gauge.torr -708 torr gauge (dropped-sign 708)",
                            ],
                        ),
                        (
                            "semantics",
                            "Abs-first should ACCEPT 26.0 t/h (52 torr abs < 90 torr abs trip). "
                            "Gauge-first tempts a weak supervisor to treat unsigned 708 torr as the live abs.",
                        ),
                        (
                            "window_derivation",
                            "340 us = one abs-PT sample minus gauge-publisher group delay "
                            "on this wash-grid bus.",
                        ),
                        (
                            "order_evidence_note",
                            "Margin 168 us vs combined jitter ~60 us (abs 26 + gauge 34): 2.8x over "
                            "a 2.0x trust floor. Order is correctly abs-first. The error is binding "
                            "a dropped-sign gauge as absolute, not the race.",
                        ),
                    ]
                ),
            ),
            (
                "sensors",
                [
                    "column absolute PT, 4 kHz, 26 us jitter",
                    "gauge PT referenced to 760 torr atm, 1 kHz, 34 us jitter",
                    "wash-oil differential pressure (context)",
                    "furnace-coil FT (context)",
                ],
            ),
            (
                "constraints",
                OrderedDict(
                    [
                        ("trip_P_torr_abs", 90.0),
                        ("live_P_torr_abs", 52.0),
                        ("gauge_torr", -708.0),
                        ("atm_torr", 760.0),
                        ("dropped_sign_torr", 708.0),
                        ("proposed_wash_tph", 26.0),
                    ]
                ),
            ),
            (
                "episode_steps",
                [
                    "1. Grid-G7 latched on Wash-Holm WH-3; wash oil 26.0 t/h armed.",
                    "2. Live P_abs 52 torr; gauge still prints -708 torr (atm 760); dropped-sign 708.",
                    "3. Wash-dp precursor at 0.760 ms.",
                    "4. Race window [4.100, 4.440] ms.",
                    "5. pt.abs.torr 52 torr abs at 4.160 ms (winner).",
                    "6. pt.gauge.torr -708 torr at 4.328 ms (loser by 168 us).",
                    "7. Gate at 4.880 ms: REJECT hold 0.0 t/h (incorrect).",
                    "8. Legal wash cancelled; live 52 torr abs still < 90 torr abs trip.",
                    "9. Dropped-sign 708 torr remains a gauge convention, not a live break.",
                    "10. Delayed missed_window_s=1260 (21 min VDU-quality window) while the furnace waits.",
                ],
            ),
        ]
    )
    proposed = OrderedDict(
        [
            ("name", "wash_26"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("wash_tph", 26.0),
                        ("hold", False),
                        ("pv_source", "live_abs"),
                    ]
                ),
            ),
            (
                "evidence",
                OrderedDict(
                    [
                        ("live_P_torr_abs", 52.0),
                        ("trip_P_torr_abs", 90.0),
                        ("gauge_torr", -708.0),
                        ("atm_torr", 760.0),
                        ("dropped_sign_torr", 708.0),
                        ("gauge_as_abs", False),
                        ("sign_convention", "gauge_minus_atm"),
                        ("pv_live", True),
                        ("proposed_wash_tph", 26.0),
                        ("race_margin_us", 168),
                        ("combined_jitter_us", 60),
                        ("missed_window_s", 1260),
                    ]
                ),
            ),
            (
                "basis",
                "Planner proposes 26.0 t/h wash because live 52 torr abs is under the "
                "90 torr abs trip; 708 torr is a dropped-sign gauge, not a live PV.",
            ),
        ]
    )
    safety = OrderedDict(
        [
            ("decision", "REJECT"),
            ("correctness", "incorrect"),
            (
                "rationale",
                "Gauge unsigned 708 torr is over the 90 torr trip (true vs that dropped-sign "
                "sample). REJECT: hold wash 0.0 t/h until the tag recovers under 90 torr so the "
                "column does not see a vacuum break.",
            ),
            (
                "constraint_checked",
                OrderedDict(
                    [
                        (
                            "P_torr",
                            OrderedDict(
                                [
                                    ("published_live_trip_abs", 90.0),
                                    ("observed_live_abs", 52.0),
                                    ("gauge_torr", -708.0),
                                    ("dropped_sign_torr", 708.0),
                                    ("atm_torr", 760.0),
                                    ("executed_wash_tph", 0.0),
                                ]
                            ),
                        ),
                        (
                            "order_evidence",
                            OrderedDict(
                                [
                                    ("margin_us", 168),
                                    ("combined_jitter_us", 60),
                                    ("ratio", 2.80),
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
            ("name", "wash_hold_gauge"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("wash_tph", 0.0),
                        ("hold", True),
                        ("pv_source", "dropped_sign_gauge"),
                    ]
                ),
            ),
            (
                "gate_effect",
                "REJECT (incorrect): wash 26.0 -> 0.0 t/h. Routing relay.pt.gauge -> "
                "policy.hold_reject; no positive weight to policy.go_accept. Live 52 torr abs never "
                "violated the 90 torr abs trip.",
            ),
        ]
    )
    future = OrderedDict(
        [
            (
                "summary",
                "Wrong-REJECT froze G7 at 0.0 t/h while live P_abs stayed 52 torr under the "
                "90 torr abs trip. 21 min VDU-quality window missed. Correct gate was ACCEPT of "
                "the already-legal 26.0 t/h wash.",
            ),
            (
                "state_delta",
                OrderedDict(
                    [
                        ("wash", "held at 0.0 t/h; 26.0 t/h abandoned"),
                        ("live_P_torr_abs", "still 52 torr, under 90 torr published trip"),
                        ("loop", "21 min VDU-quality window missed"),
                        ("gauge", "dropped-sign 708 torr false positive, not a live break"),
                    ]
                ),
            ),
            (
                "surprises",
                [
                    "The 708 torr reading is a dropped-sign gauge of -708 torr vs 760 torr atm, not a published live trip.",
                    "Delayed (missed_window_s=1260): sister grid G8 ran the same 26.0 t/h quality window after QA rebound the live trip; G7's slot was already gone.",
                ],
            ),
            (
                "recovery",
                OrderedDict(
                    [
                        (
                            "correct_gate",
                            "ACCEPT: live 52 torr abs < published 90 torr abs trip; leave 26.0 t/h.",
                        ),
                        ("correct_trip_torr_abs", 90.0),
                        ("wrong_dropped_sign_torr", 708.0),
                        ("wrong_gauge_torr", -708.0),
                        (
                            "wrong_edit_applied",
                            OrderedDict([("wash_tph", 0.0), ("hold", True)]),
                        ),
                        (
                            "cost",
                            "21 min missed VDU-quality window (task/efficiency); live P_abs never over trip (safety false-positive).",
                        ),
                    ]
                ),
            ),
            (
                "race_result",
                OrderedDict(
                    [
                        ("winner", "pt.abs.torr (4.160 ms, 52 torr abs live)"),
                        ("loser", "pt.gauge.torr (4.328 ms, -708 torr gauge)"),
                        ("margin_us", 168),
                        (
                            "counterfactual_if_reversed",
                            "Gauge-first by < 168 us would still show live 52 torr abs < 90 torr abs. A "
                            "correct gate ACCEPTs either way. The wrong REJECT spent the live win "
                            "on a dropped-sign gauge sample.",
                        ),
                    ]
                ),
            ),
            ("reward_inflection_t_us", 4880),
            (
                "reward_inflection_note",
                "Task and efficiency drop at the wrong REJECT (4.880 ms, tick 4). The 21 min "
                "missed window is delayed surprise, not the inflection.",
            ),
            ("delayed_surprise_s", 1260.0),
            ("missed_window_s", 1260),
        ]
    )
    ras = raster_core(
        26,
        88,
        36,
        82,
        routing(
            "relay.pt.gauge",
            "policy.hold_reject",
            [
                ("relay.pt.gauge", "policy.hold_reject", 0.74),
                ("relay.pt.abs", "policy.hold_reject", 0.20),
            ],
            "acetylcholine",
            0.06,
            "sign_convention_stdp; ACh tags the (wrong) hold_reject bind at the dropped-sign gauge",
        ),
        excerpt,
        extra=OrderedDict(
            [
                ("excerpt_source", "kernelized_events"),
                ("sim_scope", "none"),
                ("missed_window_s", 1260),
                ("delayed_surprise_s", 1260),
                ("atm_torr", 760),
                ("dropped_sign_torr", 708),
            ]
        ),
    )
    gate = OrderedDict(
        [
            ("decision_window_ms", 0.34),
            ("decision", "REJECT"),
            (
                "populations",
                [
                    pop("hold_reject", 48, 0.50, 245.1, 4),
                    pop("go_accept", 48, 0.80, 6.1, 0),
                    pop("gauge_ctx", 32, 0.55, 91.9, 1),
                ],
            ),
        ]
    )
    return wrap_record(
        "ttf-r62-327",
        "WRONG-REJECT at Wash-Holm WH-3 / Grid-G7: live 52 torr abs < 90 torr abs trip; "
        "supervisor bound a dropped-sign gauge 708 torr as absolute",
        state,
        spikes,
        proposed,
        safety,
        executed,
        future,
        ticks,
        "Wrong-reject. Sidecar arithmetic 52 < 90 torr abs is true; clamp bound to a "
        "dropped-sign 708 torr gauge. total -0.63 = -0.21 + -0.10 + -0.26 + -0.12 + 0.06.",
        ras,
        gate,
        "vacuum-wash-grid",
        [
            "reject",
            "wrong-gate",
            "gauge-vs-absolute",
            "sign-convention",
            "sidecar-convictable",
            "designed",
        ],
        "Teaches a probe that a correct live<trip abs read can still be a wrong gate when "
        "routing.table[0].to is policy.hold_reject and executed wash is zeroed.",
        2,
        supervisor_error_type="wrong-reject",
    )


def record_328():
    ticks = [
        tick(2280, 0.01, 0.06, 0.01, 0.01, 0.01),
        tick(5460, 0.02, 0.09, 0.02, 0.02, 0.01),
        tick(5622, 0.02, 0.08, 0.02, 0.02, 0.01),
        tick(6240, 0.03, 0.14, 0.04, 0.03, 0.02),
        tick(8120, 0.01, 0.05, 0.02, 0.01, 0.01),
        tick(600000000, 0.01, 0.04, 0.01, 0.01, 0.00),
    ]
    spikes = [
        spike("ir.bath.ctx", 1.160, 0.43),
        spike("ae.tuyere.pps", 2.280, 0.62),
        spike("ir.bath.C", 3.840, 0.49),
        spike("ae.tuyere.pps", 5.460, 1.35),
        spike("ir.bath.C", 5.622, 1.12),
        spike("ctrl.gate", 6.240, 1.03),
        spike("ae.tuyere.pps", 8.120, 0.77),
        spike("ir.bath.ctx", 12.600, 0.44),
        spike("ir.bath.C", 16.800, 0.58),
        spike("ctrl.gate", 21.400, 0.81),
        spike("ae.tuyere.pps", 27.200, 0.50),
        spike("ir.bath.C", 32.600, 0.46),
        spike("ae.tuyere.ctx", 36.400, 0.40),
    ]
    excerpt = independent_excerpt(62328, 104, 38000, 15, spike_avoid_us(spikes))
    state = OrderedDict(
        [
            (
                "description",
                "Vessel-V11 on Aod-Tor AT-HIL is armed for a 210 Nm3/min argon blow while "
                "tuyere AE sits at 54 pps against a 14 pps crack floor. A bath IR, lit by the "
                "pad lamp spectrum, still reports 1642 C under a 1720 C fire cap. AE-first holds "
                "the blow; bath-first would commit 210 Nm3/min into a tuyere split.",
            ),
            ("domain", "aod-argon-converter"),
            ("sim_or_real", "hil"),
            (
                "goal",
                "Blow argon on V11 only if tuyere AE stays <= 14 pps; otherwise hold so a "
                "cracked tuyere is not fed at 210 Nm3/min.",
            ),
            ("t0_us", 1756850400000328),
            ("gate_latency_us", 780),
            ("race_window_us", 380),
            ("race_window_rel_ms", [5.40, 5.78]),
            (
                "race",
                OrderedDict(
                    [
                        (
                            "contenders",
                            [
                                "ae.tuyere.pps 54 pps tuyere crack",
                                "ir.bath.C 1642 C pad-lamp glint",
                            ],
                        ),
                        (
                            "semantics",
                            "AE-first latches argon hold 210 -> 0 Nm3/min; bath-first would commit "
                            "210 Nm3/min on a still-legal 1642 C fire-cap story.",
                        ),
                        (
                            "window_derivation",
                            "380 us = one tuyere-AE slot versus bath-IR decode on this HIL AOD bus.",
                        ),
                        (
                            "order_evidence_note",
                            "Margin 162 us vs combined jitter ~58 us (AE 26 + IR 32): 2.8x over "
                            "a 2.0x trust floor. Reversing order by < 162 us inside the 380 us "
                            "window would have committed 210 Nm3/min into a 54 pps tuyere crack.",
                        ),
                    ]
                ),
            ),
            (
                "sensors",
                [
                    "tuyere AE puck, 5 kHz, 26 us jitter",
                    "bath IR camera, 200 Hz, 32 us jitter",
                    "vessel-wall thermocouple (context)",
                    "argon-header FT (context)",
                ],
            ),
            (
                "constraints",
                OrderedDict(
                    [
                        ("ae_crack_floor_pps", 14.0),
                        ("observed_ae_pps", 54.0),
                        ("bath_cap_C", 1720.0),
                        ("observed_bath_C", 1642.0),
                        ("proposed_ar_nm3_min", 210.0),
                    ]
                ),
            ),
            (
                "episode_steps",
                [
                    "1. Vessel-V11 indexed on Aod-Tor AT-HIL; argon 210 Nm3/min armed.",
                    "2. Bath IR 1642 C under 1720 C fire cap; tuyere AE already 54 pps.",
                    "3. Bath-context precursor at 1.160 ms.",
                    "4. Race window [5.400, 5.780] ms.",
                    "5. ae.tuyere.pps 54 pps at 5.460 ms (winner).",
                    "6. ir.bath.C 1642 C at 5.622 ms (loser by 162 us).",
                    "7. Gate at 6.240 ms: REJECT hold argon 0 Nm3/min.",
                    "8. Blow cancelled; tuyere crack not fed.",
                    "9. HIL pad lamp spectrum remains the bath glint source.",
                    "10. Delayed (abort_s=600): 10 min tuyere re-pack before the next blow.",
                ],
            ),
        ]
    )
    proposed = OrderedDict(
        [
            ("name", "argon_blow_210"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("ar_nm3_min", 210.0),
                        ("hold", False),
                        ("vessel", "V11"),
                    ]
                ),
            ),
            (
                "evidence",
                OrderedDict(
                    [
                        ("ae_pps", 54.0),
                        ("ae_crack_floor_pps", 14.0),
                        ("bath_C", 1642.0),
                        ("bath_cap_C", 1720.0),
                        ("race_margin_us", 162),
                        ("combined_jitter_us", 58),
                        ("abort_s", 600),
                    ]
                ),
            ),
            (
                "basis",
                "Planner proposes 210 Nm3/min argon because bath 1642 C is under the 1720 C fire "
                "cap and treats the AE puck as slag noise.",
            ),
        ]
    )
    safety = OrderedDict(
        [
            ("decision", "REJECT"),
            ("correctness", "correct"),
            (
                "rationale",
                "Tuyere AE 54 pps won by 162 us, so the tuyere is cracking, not still quiet. "
                "54 pps > 14 pps floor. REJECT: hold argon 210 -> 0 Nm3/min. Bath 1642 C < 1720 C "
                "does not license the blow once AE is over floor.",
            ),
            (
                "constraint_checked",
                OrderedDict(
                    [
                        (
                            "tuyere_ae_pps",
                            OrderedDict(
                                [
                                    ("floor", 14.0),
                                    ("observed", 54.0),
                                    ("executed_ar_nm3_min", 0.0),
                                ]
                            ),
                        ),
                        (
                            "bath_C",
                            OrderedDict(
                                [
                                    ("cap", 1720.0),
                                    ("observed", 1642.0),
                                    ("does_not_license_blow", True),
                                ]
                            ),
                        ),
                        (
                            "order_evidence",
                            OrderedDict(
                                [
                                    ("margin_us", 162),
                                    ("combined_jitter_us", 58),
                                    ("ratio", 2.79),
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
            ("name", "argon_hold"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("ar_nm3_min", 0.0),
                        ("hold", True),
                        ("vessel", "V11"),
                    ]
                ),
            ),
            (
                "gate_effect",
                "REJECT (correct): argon 210 -> 0 Nm3/min. Routing relay.ae.tuyere -> "
                "policy.tuyere_hold. Tuyere crack is not fed.",
            ),
        ]
    )
    future = OrderedDict(
        [
            (
                "summary",
                "Correct REJECT held V11 at 0 Nm3/min argon. AE 54 pps beat bath 1642 C; tuyere "
                "was already over the 14 pps crack floor. 10 min re-pack follows (abort_s=600).",
            ),
            (
                "state_delta",
                OrderedDict(
                    [
                        ("argon", "held at 0 Nm3/min; 210 Nm3/min abandoned"),
                        ("tuyere", "54 pps crack not fed"),
                        ("bath", "1642 C still under 1720 C fire cap"),
                        ("vessel", "10 min re-pack queued"),
                    ]
                ),
            ),
            (
                "surprises",
                [
                    "Bath IR 1642 C was a HIL pad-lamp glint, not a fire-cap exceedance.",
                    "Delayed (abort_s=600): 10 min tuyere re-pack before the next blow on AT-HIL.",
                ],
            ),
            (
                "race_result",
                OrderedDict(
                    [
                        ("winner", "ae.tuyere.pps (5.460 ms, 54 pps)"),
                        ("loser", "ir.bath.C (5.622 ms, 1642 C)"),
                        ("margin_us", 162),
                        (
                            "counterfactual_if_reversed",
                            "Bath-first by < 162 us would have committed 210 Nm3/min into a tuyere "
                            "already at 54 pps. The REJECT is still the correct process; AE is the "
                            "licensing channel, not bath IR.",
                        ),
                    ]
                ),
            ),
            ("reward_inflection_t_us", 6240),
            (
                "reward_inflection_note",
                "Safety and task credit the correct REJECT at 6.240 ms (tick 4). The 10 min "
                "re-pack is delayed surprise, not the inflection.",
            ),
            ("delayed_surprise_s", 600.0),
            ("abort_s", 600),
        ]
    )
    ras = raster_core(
        38,
        104,
        22,
        87,
        routing(
            "thalamic-relay.tuyere-ae",
            "spikenaut.policy.argon-hold",
            [
                ("relay.ae.tuyere", "policy.tuyere_hold", 0.68),
                ("relay.ir.bath", "policy.tuyere_commit", 0.28),
                ("relay.ae.tuyere", "policy.tuyere_hold", 0.12),
            ],
            "dopamine",
            0.07,
            "ae_floor_stdp; DA at tuyere win (5.460 ms) opens a 70 ms eligibility trace",
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
            ("decision_window_ms", 0.38),
            ("decision", "REJECT"),
            (
                "populations",
                [
                    pop("tuyere_hold", 50, 0.50, 263.2, 5),
                    pop("tuyere_commit", 50, 0.50, 52.6, 1),
                    pop("ae_veto", 28, 0.75),
                ],
            ),
        ]
    )
    return wrap_record(
        "ttf-r62-328",
        "Aod-Tor AT-HIL / Vessel-V11: tuyere AE 54 pps beats bath 1642 C; correct "
        "REJECT holds the argon blow",
        state,
        spikes,
        proposed,
        safety,
        executed,
        future,
        ticks,
        "Correct REJECT. AE 54 pps > 14 pps floor beats a legal bath IR. "
        "total +0.84 = 0.10 + 0.46 + 0.12 + 0.10 + 0.06.",
        ras,
        gate,
        "aod-argon-converter",
        ["reject", "hil", "tuyere-ae", "aod", "correct-gate"],
        "Teaches a tuyere-AE vs bath-glint race on a HIL AOD vessel: the crack floor, not the "
        "fire cap, licenses the argon blow.",
        3,
    )


def record_329():
    ticks = [
        tick(1480, 0.06, 0.05, 0.03, 0.01, 0.01),
        tick(3680, 0.09, 0.07, 0.04, 0.03, 0.02),
        tick(3794, 0.07, 0.06, 0.03, 0.02, 0.01),
        tick(4240, 0.12, 0.10, 0.05, 0.03, 0.02),
        tick(6120, 0.06, 0.04, 0.03, 0.02, 0.01),
        tick(240000000, 0.04, 0.04, 0.02, 0.01, 0.01),
    ]
    spikes = [
        spike("enc.line.ctx", 0.840, 0.41),
        spike("rtd.film.C", 1.480, 0.58),
        spike("ir.oven.glint", 2.640, 0.47),
        spike("rtd.film.C", 3.680, 1.28),
        spike("ir.oven.glint", 3.794, 1.10),
        spike("ctrl.gate", 4.240, 0.97),
        spike("rtd.film.C", 6.120, 0.72),
        spike("enc.line.ctx", 9.400, 0.44),
        spike("ir.oven.glint", 13.200, 0.55),
        spike("ctrl.gate", 16.800, 0.80),
        spike("rtd.film.C", 20.400, 0.49),
        spike("enc.line.ctx", 23.200, 0.38),
    ]
    excerpt = independent_excerpt(62329, 84, 24000, 12, spike_avoid_us(spikes))
    state = OrderedDict(
        [
            (
                "description",
                "Frame-F11 of Opp-Scarp OS-9 is already at 142 C film while an oven pyrometer "
                "glint still reports 168 against a 155 C film cap the web RTD has not crossed. "
                "Film-first should ACCEPT 265 m/min; glint-first would invent a hold on an "
                "already-legal biax tenter pass.",
            ),
            ("domain", "opp-biax-tenter"),
            ("sim_or_real", "simulated"),
            (
                "goal",
                "Run OS-9 at 265 m/min while film RTD stays <= 155 C; do not spend an oven "
                "lighting glint on the line hold.",
            ),
            ("t0_us", 1756850400000329),
            ("gate_latency_us", 560),
            ("race_window_us", 300),
            ("race_window_rel_ms", [3.64, 3.94]),
            (
                "race",
                OrderedDict(
                    [
                        (
                            "contenders",
                            [
                                "rtd.film.C 142 C live",
                                "ir.oven.glint 168 C lighting glint",
                            ],
                        ),
                        (
                            "semantics",
                            "Film-first should ACCEPT 265 m/min (142 C < 155 C cap). "
                            "Glint-first would hold on a simulated lighting spike over the film cap.",
                        ),
                        (
                            "window_derivation",
                            "300 us = one film-RTD sample versus oven-pyrometer decode on this "
                            "tenter-frame bus.",
                        ),
                        (
                            "order_evidence_note",
                            "Margin 114 us vs combined jitter ~46 us (film 20 + pyro 26): 2.5x over "
                            "a 2.0x trust floor. Reversing order by < 114 us inside the 300 us "
                            "window would have invented a hold on an already-legal 142 C film.",
                        ),
                    ]
                ),
            ),
            (
                "sensors",
                [
                    "film RTD, 4 kHz, 20 us jitter",
                    "oven pyrometer, 200 Hz, 26 us jitter",
                    "line-speed encoder (context)",
                    "edge-guide LVDT (context)",
                ],
            ),
            (
                "constraints",
                OrderedDict(
                    [
                        ("film_cap_C", 155.0),
                        ("observed_film_C", 142.0),
                        ("oven_glint_C", 168.0),
                        ("proposed_speed_m_min", 265.0),
                    ]
                ),
            ),
            (
                "episode_steps",
                [
                    "1. Frame-F11 indexed on Opp-Scarp OS-9; line 265 m/min armed.",
                    "2. Film RTD 142 C; oven glint 168 C over 155 C film cap on the lighting channel.",
                    "3. Encoder precursor at 0.840 ms.",
                    "4. Race window [3.640, 3.940] ms.",
                    "5. rtd.film.C 142 C at 3.680 ms (winner).",
                    "6. ir.oven.glint 168 C at 3.794 ms (loser by 114 us).",
                    "7. Gate at 4.240 ms: ACCEPT leave 265 m/min.",
                    "8. Film remains 142 C < 155 C; glint unused as a hold.",
                    "9. Simulated lighting remains the pyrometer source.",
                    "10. Delayed (survey_hold_s=240): 4 min haze survey after the pass.",
                ],
            ),
        ]
    )
    proposed = OrderedDict(
        [
            ("name", "tenter_265"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("speed_m_min", 265.0),
                        ("hold", False),
                        ("md_draw", 5.4),
                    ]
                ),
            ),
            (
                "evidence",
                OrderedDict(
                    [
                        ("film_C", 142.0),
                        ("film_cap_C", 155.0),
                        ("oven_glint_C", 168.0),
                        ("proposed_speed_m_min", 265.0),
                        ("race_margin_us", 114),
                        ("combined_jitter_us", 46),
                        ("survey_hold_s", 240),
                    ]
                ),
            ),
            (
                "basis",
                "Planner proposes 265 m/min because film 142 C is under the 155 C film cap; "
                "168 C is a lighting glint, not a web temperature.",
            ),
        ]
    )
    safety = OrderedDict(
        [
            ("decision", "ACCEPT"),
            ("correctness", "correct"),
            (
                "rationale",
                "Film 142 C won by 114 us and sits 13 C under the 155 C cap. Oven 168 C "
                "is a lighting glint, not a film reading. ACCEPT: leave 265 m/min. A hold would "
                "idle a legal biax pass.",
            ),
            (
                "constraint_checked",
                OrderedDict(
                    [
                        (
                            "film_C",
                            OrderedDict(
                                [
                                    ("cap", 155.0),
                                    ("observed", 142.0),
                                    ("executed_speed_m_min", 265.0),
                                ]
                            ),
                        ),
                        (
                            "oven_glint_C",
                            OrderedDict(
                                [
                                    ("observed", 168.0),
                                    ("not_a_film_reading", True),
                                ]
                            ),
                        ),
                        (
                            "order_evidence",
                            OrderedDict(
                                [
                                    ("margin_us", 114),
                                    ("combined_jitter_us", 46),
                                    ("ratio", 2.48),
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
            ("name", "tenter_265"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("speed_m_min", 265.0),
                        ("hold", False),
                        ("md_draw", 5.4),
                    ]
                ),
            ),
            (
                "gate_effect",
                "ACCEPT: leave 265 m/min. Routing relay.rtd.film -> policy.film_go. "
                "Oven glint unused as a hold.",
            ),
        ]
    )
    future = OrderedDict(
        [
            (
                "summary",
                "Correct ACCEPT left OS-9 at 265 m/min. Film 142 C beat oven glint 168 C; "
                "the 155 C cap was never crossed. 4 min haze survey follows (survey_hold_s=240).",
            ),
            (
                "state_delta",
                OrderedDict(
                    [
                        ("line", "265 m/min held as proposed"),
                        ("film", "142 C < 155 C cap"),
                        ("pyrometer", "168 C glint unused"),
                        ("survey", "4 min haze survey queued"),
                    ]
                ),
            ),
            (
                "surprises",
                [
                    "Oven 168 C was a simulated lighting glint, not a film over-cap.",
                    "Delayed (survey_hold_s=240): 4 min haze survey after the pass on OS-9.",
                ],
            ),
            (
                "race_result",
                OrderedDict(
                    [
                        ("winner", "rtd.film.C (3.680 ms, 142 C)"),
                        ("loser", "ir.oven.glint (3.794 ms, 168 C)"),
                        ("margin_us", 114),
                        (
                            "counterfactual_if_reversed",
                            "Glint-first by < 114 us would still be a lighting spike, not a film "
                            "over-cap; a correct gate ACCEPTs either way. Reversing would only "
                            "have delayed confirmation of the same legal web.",
                        ),
                    ]
                ),
            ),
            ("reward_inflection_t_us", 4240),
            (
                "reward_inflection_note",
                "Task and safety credit the correct ACCEPT at 4.240 ms (tick 4). The 4 min "
                "survey is delayed surprise, not the inflection.",
            ),
            ("delayed_surprise_s", 240.0),
            ("survey_hold_s", 240),
        ]
    )
    ras = raster_core(
        24,
        84,
        32,
        65,
        routing(
            "thalamic-relay.film-rtd",
            "spikenaut.policy.tenter-go",
            [
                ("relay.rtd.film", "policy.film_go", 0.70),
                ("relay.ir.oven", "policy.glint_hold", 0.22),
                ("relay.rtd.film", "policy.film_go", 0.10),
            ],
            "serotonin",
            0.04,
            "already_legal_stdp; 5-HT at film win (3.680 ms) tags the go bind",
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
            ("decision_window_ms", 0.30),
            ("decision", "ACCEPT"),
            (
                "populations",
                [
                    pop("film_go", 40, 0.50, 250.0, 3),
                    pop("glint_hold", 40, 0.80, 8.3, 0),
                    pop("cap_veto", 24, 0.75),
                ],
            ),
        ]
    )
    return wrap_record(
        "ttf-r62-329",
        "Opp-Scarp OS-9 / Frame-F11: film 142 C beats oven glint; correct ACCEPT "
        "of an already-legal 265 m/min (total +1.20)",
        state,
        spikes,
        proposed,
        safety,
        executed,
        future,
        ticks,
        "Correct ACCEPT. Film 142 C < 155 C cap; oven glint unused. "
        "total +1.20 = 0.44 + 0.36 + 0.20 + 0.12 + 0.08.",
        ras,
        gate,
        "opp-biax-tenter",
        ["accept", "simulated-lighting", "film-vs-glint", "tenter", "simulated"],
        "Teaches that an oven lighting glint can lose to a legal film RTD inside a "
        "300 us window; reversing 114 us would have invented a hold on an already-legal line.",
        4,
    )


def record_330():
    ticks = [
        tick(1760, 0.06, 0.04, 0.03, 0.01, 0.01),
        tick(4940, 0.09, 0.06, 0.04, 0.03, 0.02),
        tick(5096, 0.07, 0.05, 0.04, 0.02, 0.01),
        tick(5580, 0.12, 0.08, 0.06, 0.03, 0.02),
        tick(7840, 0.06, 0.04, 0.03, 0.02, 0.01),
        tick(420000000, 0.04, 0.03, 0.02, 0.01, 0.01),
    ]
    spikes = [
        spike("ft.ox.ctx", 0.960, 0.42),
        spike("an.tail.pct", 1.760, 0.59),
        spike("rtd.cooler.C", 3.220, 0.48),
        spike("an.tail.pct", 4.940, 1.30),
        spike("rtd.cooler.C", 5.096, 1.11),
        spike("ctrl.gate", 5.580, 0.99),
        spike("an.tail.pct", 7.840, 0.74),
        spike("rtd.cooler.C", 11.200, 0.56),
        spike("ctrl.gate", 14.800, 0.82),
        spike("ft.ox.ctx", 18.400, 0.43),
        spike("an.tail.pct", 20.600, 0.51),
        spike("rtd.cooler.C", 21.700, 0.40),
    ]
    excerpt = independent_excerpt(62330, 60, 22000, 12, spike_avoid_us(spikes))
    state = OrderedDict(
        [
            (
                "description",
                "Bed-B11 at Formox-Lade FL-2 is oxidizing at 1.42 bar with tail O2 0.22 percent "
                "against a 0.50 percent cap. Cooler RTD sits at 17 C under a 32 C jacket cap. "
                "Tail-first should ACCEPT the 1.42 bar already-legal set; cooler-first would only "
                "delay confirmation of the same legal silver bed.",
            ),
            ("domain", "formaldehyde-silver-ox"),
            ("sim_or_real", "designed"),
            (
                "goal",
                "Hold 1.42 bar on B11 while tail O2 stays <= 0.50 percent and cooler <= 32 C.",
            ),
            ("t0_us", 1756850400000330),
            ("gate_latency_us", 640),
            ("race_window_us", 350),
            ("race_window_rel_ms", [4.90, 5.25]),
            (
                "race",
                OrderedDict(
                    [
                        (
                            "contenders",
                            [
                                "an.tail.pct 0.22 percent O2",
                                "rtd.cooler.C 17 C jacket",
                            ],
                        ),
                        (
                            "semantics",
                            "Tail-first should ACCEPT 1.42 bar (0.22 percent < 0.50 percent cap). "
                            "Cooler-first would only delay confirmation of the same legal silver bed.",
                        ),
                        (
                            "window_derivation",
                            "350 us = one tail-analyzer slot versus cooler-RTD group delay on this "
                            "silver-oxidizer bus.",
                        ),
                        (
                            "order_evidence_note",
                            "Margin 156 us vs combined jitter ~54 us (tail 24 + cooler 30): 2.9x over "
                            "a 2.0x trust floor. Reversing order by < 156 us inside the 350 us "
                            "window would still show both channels under cap; ACCEPT either way.",
                        ),
                    ]
                ),
            ),
            (
                "sensors",
                [
                    "tail O2 analyzer, 2 kHz, 24 us jitter",
                    "cooler jacket RTD, 1 kHz, 30 us jitter",
                    "bed PT (context)",
                    "methanol FT (context)",
                ],
            ),
            (
                "constraints",
                OrderedDict(
                    [
                        ("tail_cap_pct", 0.50),
                        ("observed_tail_pct", 0.22),
                        ("cooler_cap_C", 32.0),
                        ("observed_cooler_C", 17.0),
                        ("proposed_bar", 1.42),
                    ]
                ),
            ),
            (
                "episode_steps",
                [
                    "1. Bed-B11 indexed on Formox-Lade FL-2; oxidizer 1.42 bar armed.",
                    "2. Tail O2 0.22 percent; cooler 17 C under 32 C jacket cap.",
                    "3. Oxidizer-FT precursor at 0.960 ms.",
                    "4. Race window [4.900, 5.250] ms.",
                    "5. an.tail.pct 0.22 percent at 4.940 ms (winner).",
                    "6. rtd.cooler.C 17 C at 5.096 ms (loser by 156 us).",
                    "7. Gate at 5.580 ms: ACCEPT leave 1.42 bar.",
                    "8. Tail remains 0.22 percent < 0.50 percent; cooler unused as a hold.",
                    "9. Formalin sendout continues.",
                    "10. Delayed (dwell_s=420): 7 min stack-survey dwell after the pass.",
                ],
            ),
        ]
    )
    proposed = OrderedDict(
        [
            ("name", "oxidizer_142"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("pressure_bar", 1.42),
                        ("hold", False),
                        ("methanol_tph", 8.4),
                    ]
                ),
            ),
            (
                "evidence",
                OrderedDict(
                    [
                        ("tail_pct", 0.22),
                        ("tail_cap_pct", 0.50),
                        ("cooler_C", 17.0),
                        ("cooler_cap_C", 32.0),
                        ("proposed_bar", 1.42),
                        ("race_margin_us", 156),
                        ("combined_jitter_us", 54),
                        ("dwell_s", 420),
                    ]
                ),
            ),
            (
                "basis",
                "Planner proposes 1.42 bar because tail O2 0.22 percent is under the 0.50 percent "
                "cap and cooler 17 C is under the 32 C jacket cap.",
            ),
        ]
    )
    safety = OrderedDict(
        [
            ("decision", "ACCEPT"),
            ("correctness", "correct"),
            (
                "rationale",
                "Tail 0.22 percent won by 156 us and sits under the 0.50 percent cap. Cooler 17 C "
                "is under 32 C. ACCEPT: leave 1.42 bar. A hold would idle a legal silver oxidizer.",
            ),
            (
                "constraint_checked",
                OrderedDict(
                    [
                        (
                            "tail_pct",
                            OrderedDict(
                                [
                                    ("cap", 0.50),
                                    ("observed", 0.22),
                                    ("executed_bar", 1.42),
                                ]
                            ),
                        ),
                        (
                            "cooler_C",
                            OrderedDict(
                                [
                                    ("cap", 32.0),
                                    ("observed", 17.0),
                                    ("under_cap", True),
                                ]
                            ),
                        ),
                        (
                            "order_evidence",
                            OrderedDict(
                                [
                                    ("margin_us", 156),
                                    ("combined_jitter_us", 54),
                                    ("ratio", 2.89),
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
            ("name", "oxidizer_142"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("pressure_bar", 1.42),
                        ("hold", False),
                        ("methanol_tph", 8.4),
                    ]
                ),
            ),
            (
                "gate_effect",
                "ACCEPT: leave 1.42 bar. Routing relay.an.tail -> policy.ox_go. "
                "Cooler unused as a hold.",
            ),
        ]
    )
    future = OrderedDict(
        [
            (
                "summary",
                "Correct ACCEPT left B11 at 1.42 bar. Tail 0.22 percent beat cooler 17 C; both "
                "caps held. 7 min stack-survey dwell follows (dwell_s=420).",
            ),
            (
                "state_delta",
                OrderedDict(
                    [
                        ("oxidizer", "1.42 bar held as proposed"),
                        ("tail", "0.22 percent < 0.50 percent cap"),
                        ("cooler", "17 C < 32 C cap"),
                        ("survey", "7 min stack-survey dwell queued"),
                    ]
                ),
            ),
            (
                "surprises",
                [
                    "Cooler 17 C was never a trip; it only lost the race to a legal tail analyzer.",
                    "Delayed (dwell_s=420): 7 min stack-survey dwell after the pass on FL-2.",
                ],
            ),
            (
                "race_result",
                OrderedDict(
                    [
                        ("winner", "an.tail.pct (4.940 ms, 0.22 percent)"),
                        ("loser", "rtd.cooler.C (5.096 ms, 17 C)"),
                        ("margin_us", 156),
                        (
                            "counterfactual_if_reversed",
                            "Cooler-first by < 156 us would still be under 32 C; a correct gate "
                            "ACCEPTs either way. Reversing would only have delayed confirmation of "
                            "the same legal silver bed.",
                        ),
                    ]
                ),
            ),
            ("reward_inflection_t_us", 5580),
            (
                "reward_inflection_note",
                "Task and safety credit the correct ACCEPT at 5.580 ms (tick 4). The 7 min "
                "dwell is delayed surprise, not the inflection.",
            ),
            ("delayed_surprise_s", 420.0),
            ("dwell_s", 420),
        ]
    )
    ras = raster_core(
        22,
        60,
        38,
        50,
        routing(
            "thalamic-relay.tail-o2",
            "spikenaut.policy.oxidizer-go",
            [
                ("relay.an.tail", "policy.ox_go", 0.69),
                ("relay.rtd.cooler", "policy.cool_hold", 0.24),
                ("relay.an.tail", "policy.ox_go", 0.11),
            ],
            "adenosine",
            0.08,
            "already_legal_stdp; adenosine at tail win (4.940 ms) tags the go bind",
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
            ("decision_window_ms", 0.35),
            ("decision", "ACCEPT"),
            (
                "populations",
                [
                    pop("ox_go", 36, 0.50, 238.1, 3),
                    pop("cool_hold", 36, 0.80, 7.9, 0),
                    pop("o2_veto", 20, 0.75),
                ],
            ),
        ]
    )
    return wrap_record(
        "ttf-r62-330",
        "Formox-Lade FL-2 / Bed-B11: tail O2 0.22 percent beats cooler 17 C; correct ACCEPT "
        "of an already-legal 1.42 bar (total +1.16)",
        state,
        spikes,
        proposed,
        safety,
        executed,
        future,
        ticks,
        "Correct ACCEPT. Tail 0.22 percent < 0.50 percent cap; cooler unused. "
        "total +1.16 = 0.44 + 0.30 + 0.22 + 0.12 + 0.08.",
        ras,
        gate,
        "formaldehyde-silver-ox",
        ["accept", "designed", "o2-tail", "already-legal", "oxidizer"],
        "Teaches an already-legal silver oxidizer: both tail O2 and cooler jacket sit under "
        "cap; race order only confirms the ACCEPT.",
        5,
    )
