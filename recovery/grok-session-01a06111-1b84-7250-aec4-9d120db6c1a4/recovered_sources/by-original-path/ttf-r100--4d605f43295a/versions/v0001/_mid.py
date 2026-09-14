def lif_517_excerpt():
    """Independent CUBA LIF (seed 100517). Plant remains designed."""

    n = 92
    dt_us = 100
    tau_m_ms = 19.8
    v_th = 1.0
    v_reset = 0.0
    refractory_us = 1000
    i_bias = 0.88
    i_stim_peak = 2.48
    stim = (21000, 25000)
    seed = 100517
    window_us = 44000
    i_clamp_extra = 0.71
    clamp_n = 18
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
    take(burst, 9, label_times=(22200, 23100, 24100))
    clamp = [(t, nid) for t, nid in picked if t < 21000][:7]
    tile = [(t, nid) for t, nid in picked if t >= 21000][:9]
    picked = sorted(clamp + tile, key=lambda item: (item[0], item[1]))
    if len(picked) < 8:
        raise RuntimeError(f"LIF excerpt too short: {len(picked)}")
    channels = ["lif.clamp" if t < 21000 else "lif.pack" for t, _ in picked]
    lif = OrderedDict(
        [
            ("model", "leaky_integrate_and_fire"),
            ("n", 92),
            ("dt_us", 100),
            ("tau_m_ms", 19.8),
            ("v_rest", 0.0),
            ("v_reset", 0.0),
            ("v_th", 1.0),
            ("r_m", 1.0),
            ("refractory_us", 1000),
            ("i_bias", 0.88),
            ("i_stim_peak", 2.48),
            ("stim_t_us", [21000, 25000]),
            ("i_clamp_extra", 0.71),
            ("clamp_n", 18),
            ("seed", 100517),
            (
                "note",
                "Population sim scoped to this sidecar. Plant remains designed. "
                "Neurons 0-17 carry +0.71 BDO-clamp bias; stim 21-25 ms is the packing-ring dump.",
            ),
        ]
    )
    extra = OrderedDict(
        [
            ("excerpt_source", "independent_lif"),
            ("sim_scope", "sidecar_only"),
            ("lif", lif),
            ("abort_s", 1020),
            ("delayed_surprise_s", 1020),
        ]
    )
    return excerpt_items(picked, channels), extra


def record_516():
    ticks = [
        tick(1920, -0.02, 0.01, -0.02, -0.01, 0.01),
        tick(4800, -0.04, 0.01, -0.04, -0.02, 0.01),
        tick(5020, -0.03, 0.01, -0.03, -0.01, 0.01),
        tick(5620, -0.06, 0.02, -0.08, -0.03, 0.02),
        tick(5980, -0.02, 0.01, -0.03, -0.01, 0.01),
        tick(1080000000, -0.01, 0.00, -0.02, 0.00, 0.00),
    ]
    spikes = [
        spike("enc.mibk.ctx", 0.960, 0.42),
        spike("rtd.bed.c", 2.140, 0.61),
        spike("bus.burst.st", 3.280, 0.53),
        spike("bus.hart.ctx", 4.020, 0.45),
        spike("rtd.bed.c", 4.800, 1.31),
        spike("bus.burst.st", 5.020, 1.14),
        spike("ctrl.gate", 5.620, 0.97),
        spike("rtd.bed.c", 6.880, 0.81),
        spike("bus.burst.st", 8.940, 0.62),
        spike("ctrl.gate", 14.600, 0.84),
        spike("enc.mibk.ctx", 18.200, 0.39),
        spike("rtd.bed.c", 23.400, 0.55),
    ]
    excerpt = independent_excerpt(100516, 72, 26000, 12, spike_avoid_us(spikes))
    state = OrderedDict(
        [
            (
                "description",
                "MIBK hydrogenator H-6 at Mibket-Holme already holds a live bed RTD of 92.0 C when that analog sample races a HART burst-mode status word still publishing 148. Published trip is 118.0 C on the analog PV; a weak supervisor treats leftover burst-mode status as process T and zeros a legal 8.4 t/h mesityl-oxide feed.",
            ),
            ("domain", "mibk-hydrogenator"),
            ("sim_or_real", "designed"),
            (
                "goal",
                "Hold 8.4 t/h mesityl-oxide on H-6, keep analog bed T < 118.0 C trip, and finish the 18 min MIBK-quality window.",
            ),
            ("t0_us", 1762300000000516),
            ("gate_latency_us", 820),
            ("race_window_us", 360),
            ("race_window_rel_ms", [4.800, 5.160]),
            (
                "race",
                OrderedDict(
                    [
                        (
                            "contenders",
                            [
                                "rtd.bed.c 92.0 C analog process T",
                                "bus.burst.st burst-mode status 148 (unitless UPDATE_OK)",
                            ],
                        ),
                        (
                            "semantics",
                            "PV-first should ACCEPT 8.4 t/h (92.0 C < 118.0 C trip). "
                            "Burst-status-first would only delay confirmation of the same legal bed.",
                        ),
                        (
                            "window_derivation",
                            "360 us = one analog RTD slot versus the HART burst-mode status publisher "
                            "on this 2 kHz hydrogenator bus.",
                        ),
                        (
                            "order_evidence_note",
                            "Margin 220 us vs combined jitter 66 us (RTD 30 + burst 36): 3.3x over "
                            "a 2.0x trust floor. Order is correctly PV-first. The error is binding "
                            "the burst-mode status word as if it were the live process PV, not the race.",
                        ),
                    ]
                ),
            ),
            (
                "sensors",
                [
                    "bed RTD analog PV, 2 kHz, 30 us jitter, axis h6_bed_t, burst_status_is_pv false",
                    "HART burst-mode status word, 1 kHz, 36 us jitter, comms not process",
                    "mesityl-oxide feed encoder (context)",
                    "hydrogen header PT (context)",
                ],
            ),
            (
                "constraints",
                OrderedDict(
                    [
                        ("live_C", 92.0),
                        ("trip_C", 118.0),
                        ("burst_status", 148),
                        ("burst_status_hex", "0x94"),
                        ("hart_burst_mode", True),
                        ("burst_status_is_pv", False),
                        ("burst_status_as_eu", True),
                        ("analog_fresh", True),
                        ("proposed_t_h", 8.4),
                    ]
                ),
            ),
            (
                "episode_steps",
                [
                    "1. Hydrogenator H-6 indexed on Mibket-Holme; analog PV 92.0 C, mesityl-oxide 8.4 t/h armed.",
                    "2. Published live trip 118.0 C; burst-mode status tagged as HART comms, not process PV.",
                    "3. Encoder precursor at 0.960 ms.",
                    "4. Race window [4.800, 5.160] ms.",
                    "5. Analog PV 92.0 C at 4.800 ms (winner).",
                    "6. Burst-mode status 148 at 5.020 ms (loser by 220 us).",
                    "7. Gate at 5.620 ms: wrong REJECT holds 0 t/h on burst-mode-status-as-EU.",
                    "8. Feed idle; analog PV never crossed 118.0 C.",
                    "9. 18 min MIBK window missed.",
                    "10. QA: correct gate was ACCEPT; leave 8.4 t/h; bind analog 92.0 vs 118.0 C trip.",
                ],
            ),
        ]
    )
    proposed = OrderedDict(
        [
            ("name", "mibk_8p4_hold"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("feed_t_h", 8.4),
                        ("proc_C", 92.0),
                        ("hold", False),
                    ]
                ),
            ),
            (
                "evidence",
                OrderedDict(
                    [
                        ("live_C", 92.0),
                        ("trip_C", 118.0),
                        ("burst_status", 148),
                        ("burst_status_hex", "0x94"),
                        ("hart_burst_mode", True),
                        ("burst_status_is_pv", False),
                        ("burst_status_as_eu", True),
                        ("analog_fresh", True),
                        ("ft_axis", "h6_bed_t"),
                        ("race_margin_us", 220),
                        ("combined_jitter_us", 66),
                        ("t_gate_us", 5620),
                    ]
                ),
            ),
            (
                "basis",
                "Planner proposes 8.4 t/h because analog PV 92.0 C is 26.0 C under the "
                "published 118.0 C trip and burst-mode status 148 is a HART UPDATE_OK nibble, not process T.",
            ),
        ]
    )
    safety = OrderedDict(
        [
            ("decision", "REJECT"),
            ("correctness", "incorrect"),
            (
                "rationale",
                "Burst-mode status prints 148, so the bed is treated as 148 C over the 118.0 C "
                "trip (true vs that leftover HART nibble). REJECT: hold 0 t/h until the burst word "
                "falls so the hydrogenator does not see an over-temp event.",
            ),
            (
                "constraint_checked",
                OrderedDict(
                    [
                        (
                            "h6_bed_t",
                            OrderedDict(
                                [
                                    ("published_trip_C", 118.0),
                                    ("observed_analog_C", 92.0),
                                    ("burst_status_as_eu_applied", True),
                                    ("burst_status", 148),
                                    ("executed_t_h", 0.0),
                                ]
                            ),
                        ),
                        (
                            "order_evidence",
                            OrderedDict(
                                [
                                    ("margin_us", 220),
                                    ("combined_jitter_us", 66),
                                    ("ratio", 3.33),
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
            ("name", "mibk_hold_burst"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("feed_t_h", 0.0),
                        ("proc_C", 92.0),
                        ("hold", True),
                    ]
                ),
            ),
            (
                "gate_effect",
                "REJECT (incorrect): feed 8.4 -> 0 t/h. Routing relay.burst.status -> "
                "policy.hold_reject; no positive weight to policy.go_accept. Analog PV 92.0 C never "
                "violated the 118.0 C trip.",
            ),
        ]
    )
    future = OrderedDict(
        [
            (
                "summary",
                "Wrong-REJECT froze H-6 at 0 t/h while analog PV stayed 92.0 C under the "
                "118.0 C trip. 18 min MIBK window missed. Correct gate was ACCEPT of the "
                "already-legal 8.4 t/h command.",
            ),
            (
                "state_delta",
                OrderedDict(
                    [
                        ("hydrogenator", "held at 0 t/h; 8.4 t/h abandoned"),
                        ("proc_C", "still 92.0 C, under 118.0 C published trip"),
                        ("mibk", "18 min hydrogenation window missed"),
                        ("flag", "no over-temp; burst-mode-status-as-EU false positive"),
                    ]
                ),
            ),
            (
                "surprises",
                [
                    "The 148 tag is a HART burst-mode UPDATE_OK status word, not a live process PV.",
                    "Delayed (18 min): sister hydrogenator H-7 ran the same 8.4 t/h window after QA rebound the analog trip; H-6's slot was already gone.",
                ],
            ),
            (
                "recovery",
                OrderedDict(
                    [
                        (
                            "correct_gate",
                            "ACCEPT: analog PV 92.0 C < published 118.0 C trip; leave 8.4 t/h; ignore burst-mode status.",
                        ),
                        ("correct_trip_C", 118.0),
                        ("wrong_flag", True),
                        (
                            "wrong_edit_applied",
                            OrderedDict([("feed_t_h", 0.0), ("hold", True)]),
                        ),
                        (
                            "cost",
                            "18 min missed MIBK window (task/efficiency); analog PV never over trip (safety false-positive).",
                        ),
                    ]
                ),
            ),
            (
                "race_result",
                OrderedDict(
                    [
                        ("winner", "rtd.bed.c (4.800 ms, 92.0 C)"),
                        ("loser", "bus.burst.st (5.020 ms, leftover burst-mode status 148)"),
                        ("margin_us", 220),
                        (
                            "counterfactual_if_reversed",
                            "Burst-status-first by < 220 us would still show analog PV 92.0 C < 118.0. A "
                            "correct gate ACCEPTs either way. The wrong REJECT spent the PV win "
                            "on leftover burst-mode status.",
                        ),
                    ]
                ),
            ),
            ("reward_inflection_t_us", 5620),
            (
                "reward_inflection_note",
                "Task and efficiency drop at the wrong REJECT (5.620 ms, tick 4). The 18 min "
                "missed window is delayed surprise, not the inflection.",
            ),
            ("delayed_surprise_s", 1080.0),
            ("missed_window_s", 1080),
        ]
    )
    ras = raster_core(
        26,
        72,
        30,
        56,
        routing(
            "relay.burst.status",
            "policy.hold_reject",
            [
                ("relay.burst.status", "policy.hold_reject", 0.74),
                ("relay.rtd.bed", "policy.hold_reject", 0.19),
            ],
            "acetylcholine",
            0.08,
            "burst_status_as_eu_stdp; ACh tags the (wrong) hold_reject bind at the analog PV win",
        ),
        excerpt,
    )
    gate = OrderedDict(
        [
            ("decision_window_ms", 0.36),
            ("decision", "REJECT"),
            (
                "populations",
                [
                    pop("hold_reject", 48, 0.50, 210.0, 4),
                    pop("go_accept", 48, 0.80, 8.0, 0),
                    pop("temp_trip_veto", 24, 0.75),
                ],
            ),
        ]
    )
    return wrap_record(
        "ttf-r100-516",
        "WRONG-REJECT at Mibket-Holme / H-6: analog PV 92.0 C is legal vs "
        "published 118.0 C trip; supervisor bound leftover HART burst-mode status as the process PV",
        state,
        spikes,
        proposed,
        safety,
        executed,
        future,
        ticks,
        "Wrong-reject. Sidecar arithmetic 92.0 < 118.0 is true; clamp bound to leftover "
        "burst-mode status. total -0.36 = -0.18 + 0.06 + -0.22 + -0.08 + 0.06.",
        ras,
        gate,
        "mibk-hydrogenator",
        [
            "reject",
            "wrong-gate",
            "burst-mode-status-as-eu",
            "hart-burst-nibble",
            "sidecar-convictable",
            "designed",
        ],
        "Teaches a probe that a correct analog-PV<trip read can still be a wrong gate when "
        "routing.table[0].to is policy.hold_reject and executed feed is zeroed.",
        1,
        supervisor_error_type="wrong-reject",
    )


def record_517():
    excerpt, extra = lif_517_excerpt()
    ticks = [
        tick(2040, 0.05, -0.02, -0.02, 0.01, 0.00),
        tick(5100, 0.08, -0.04, -0.03, 0.01, -0.01),
        tick(5340, 0.04, -0.03, -0.02, 0.00, 0.00),
        tick(5980, 0.10, -0.06, -0.03, 0.02, -0.01),
        tick(22200, 0.05, -0.42, -0.04, 0.00, -0.02),
        tick(1020000000, 0.02, -0.05, -0.02, 0.00, 0.00),
    ]
    state = OrderedDict(
        [
            (
                "description",
                "Gamma-butyrolactone dehydro bed D-3 at Butyrol-Clough is already pulling 12 t/h 1,4-butanediol when a bed-temperature pulse arrives 240 us before the BDO-flow encoder that still reads a legal feed. Temperature-first latches a process clamp under the 298 C cap; flow-first would keep cruise BDO. Stored packing-ring dump is not yet an observable of either race channel.",
            ),
            ("domain", "gamma-butyrolactone-dehydro"),
            ("sim_or_real", "designed"),
            (
                "goal",
                "Keep D-3 on 12 t/h BDO only while bed temperature stays <= 298 C, and "
                "leave the packing rings un-dumped.",
            ),
            ("t0_us", 1762300000000517),
            ("gate_latency_us", 880),
            ("race_window_us", 400),
            ("race_window_rel_ms", [5.100, 5.500]),
            (
                "race",
                OrderedDict(
                    [
                        (
                            "contenders",
                            [
                                "rtd.bed.c 312 C GBL dehydro bed",
                                "ft.bdo.t_h 12 t/h still-legal BDO feed",
                            ],
                        ),
                        (
                            "semantics",
                            "Temperature-first latches BDO clamp 12 -> 7 t/h; flow-first keeps "
                            "cruise BDO on a 'rings still seated' model.",
                        ),
                        (
                            "window_derivation",
                            "400 us = one bed RTD slot minus flow-encoder group delay on this "
                            "1 kHz dehydro bus.",
                        ),
                        (
                            "order_evidence_note",
                            "Margin 240 us vs combined jitter 66 us (RTD 28 + flow 38): 3.6x over "
                            "a 2.0x trust floor. Reversing order by < 240 us inside the 400 us window "
                            "would have kept 12 t/h cruise; predicted next-sample bed 301 C > 298 cap.",
                        ),
                    ]
                ),
            ),
            (
                "sensors",
                [
                    "GBL dehydro bed RTD, 1 kHz, 28 us timestamp jitter",
                    "BDO-flow encoder, 1 kHz, 38 us jitter",
                    "hydrogen recycle encoder (context)",
                    "packing AE (context)",
                ],
            ),
            (
                "constraints",
                OrderedDict(
                    [
                        ("bed_cap_C", 298.0),
                        ("observed_bed_C", 312.0),
                        ("proposed_bdo_t_h", 12.0),
                        ("bdo_floor_t_h", 6.0),
                    ]
                ),
            ),
            (
                "episode_steps",
                [
                    "1. Dehydro bed D-3 indexed; 12 t/h BDO; bed 312 C > 298 cap.",
                    "2. Cruise BDO 12 t/h armed; bed over the 298 C cap.",
                    "3. Encoder precursor at 1.160 ms; bed-side warm-start 312 C.",
                    "4. Race window [5.100, 5.500] ms opens on the dehydro bus.",
                    "5. Bed RTD 312 C at 5.100 ms (winner).",
                    "6. BDO flow 12 t/h at 5.340 ms (loser by 240 us).",
                    "7. Gate at 5.980 ms (winner + 880 us): MODIFY clamp 12 -> 7 t/h.",
                    "8. Clamp executes; next-sample bed 291 C < 298 cap.",
                    "9. At 22.200 ms stored packing-ring dump opens a 28 mm void.",
                    "10. Emergency isolate 17 min + ring pull; named un-netted loss, not folded into process heads.",
                ],
            ),
        ]
    )
    proposed = OrderedDict(
        [
            ("name", "cruise_bdo_gbl"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("bdo_t_h", 12.0),
                        ("bed_C", 312.0),
                        ("hold", False),
                    ]
                ),
            ),
            (
                "evidence",
                OrderedDict(
                    [
                        ("bed_C", 312.0),
                        ("bed_cap_C", 298.0),
                        ("predicted_unclamped_next_C", 301.0),
                        ("bdo_t_h", 12.0),
                        ("race_margin_us", 240),
                        ("combined_jitter_us", 66),
                    ]
                ),
            ),
            (
                "basis",
                "Planner proposes 12 t/h cruise: BDO flow looks like seated packing, not a "
                "dumped void, and the 298 C bed cap is treated as still open.",
            ),
        ]
    )
    safety = OrderedDict(
        [
            ("decision", "MODIFY"),
            ("correctness", "correct"),
            (
                "rationale",
                "Bed 312 C won by 240 us, so the rings are running packed, not still "
                "seated free. Holding 12 t/h predicts next-sample 301 C > 298 C cap. MODIFY: BDO "
                "12 -> 7 t/h. Observed after clamp 291 C < 298. A full REJECT is not "
                "indicated: a sound dehydro accepts 7 t/h.",
            ),
            (
                "constraint_checked",
                OrderedDict(
                    [
                        (
                            "bed_C",
                            OrderedDict(
                                [
                                    ("cap", 298.0),
                                    ("observed", 312.0),
                                    ("predicted_unclamped_next", 301.0),
                                    ("clamped_bdo_t_h", 7.0),
                                    ("observed_after_clamp", 291.0),
                                ]
                            ),
                        ),
                        (
                            "order_evidence",
                            OrderedDict(
                                [
                                    ("margin_us", 240),
                                    ("combined_jitter_us", 66),
                                    ("ratio", 3.64),
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
            ("name", "clamped_bdo_gbl"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("bdo_t_h", 7.0),
                        ("bed_C", 291.0),
                        ("hold", False),
                    ]
                ),
            ),
            (
                "gate_effect",
                "MODIFY: BDO 12 -> 7 t/h. Process-correct vs the 298 C bed cap. Packing-ring "
                "dump still occurs at 22.200 ms.",
            ),
        ]
    )
    future = OrderedDict(
        [
            (
                "summary",
                "Process-correct MODIFY held bed at 291 C. At 22.200 ms stored packing load "
                "dumped a 28 mm void. Clamp reduced BDO energy; it did not dump the ring charge. "
                "Partnered negative: process heads stay honest; world loss is named, not netted.",
            ),
            (
                "state_delta",
                OrderedDict(
                    [
                        ("bdo", "clamp executed; bed 291 C < 298"),
                        ("packing", "dump at 22.200 ms"),
                        ("repair", "17 min emergency isolate + ring pull"),
                        ("mission", "bed still dehydrogenating; packing precursor controlled"),
                    ]
                ),
            ),
            (
                "surprises",
                [
                    "Neither bed RTD nor BDO flow predicted the packing charge; ae.pack.ring is a new channel at 22.200 ms, 16.220 ms after the gate, still inside the 44 ms raster.",
                    "Delayed (17 min): emergency isolate and ring pull close the void. Named un-netted loss, not folded into task_progress.",
                ],
            ),
            (
                "un_netted_loss",
                "17 min emergency isolate + ring pull after a packing-ring dump. Safety "
                "head -0.62 prices the precursor; task_progress stays +0.34 because the BDO clamp "
                "completed under the 298 C cap. World loss is named here, not subtracted from process heads.",
            ),
            (
                "race_result",
                OrderedDict(
                    [
                        ("winner", "rtd.bed.c (5.100 ms, 312 C)"),
                        ("loser", "ft.bdo.t_h (5.340 ms, 12 t/h)"),
                        ("margin_us", 240),
                        (
                            "counterfactual_if_reversed",
                            "Flow-first by < 240 us inside the 400 us window would have kept "
                            "12 t/h cruise; predicted next-sample 301 C would have exceeded the "
                            "298 C cap even without the packing charge. The MODIFY is still the "
                            "correct process. The dump is a later world charge either way, cheaper "
                            "with the clamp than without.",
                        ),
                    ]
                ),
            ),
            ("reward_inflection_t_us", 22200),
            (
                "reward_inflection_note",
                "Safety collapses at the 22.200 ms packing-ring dump (tick t_us=22200), inside the "
                "44 ms raster. The correct MODIFY at 5.980 ms is in the same excerpt. Do not put "
                "inflection on the +17 min isolate tick.",
            ),
            ("delayed_surprise_s", 1020.0),
            ("abort_s", 1020),
        ]
    )
    spikes = [
        spike("enc.bdo.ctx", 1.160, 0.41),
        spike("rtd.bed.c", 2.420, 0.64),
        spike("ft.bdo.t_h", 3.380, 0.52),
        spike("rtd.bed.c", 5.100, 1.34),
        spike("ft.bdo.t_h", 5.340, 1.12),
        spike("ctrl.gate", 5.980, 0.95),
        spike("rtd.bed.c", 7.640, 0.79),
        spike("ft.bdo.t_h", 11.200, 0.63),
        spike("ctrl.gate", 16.400, 0.82),
        spike("ae.pack.ring", 22.200, 1.46),
        spike("ae.pack.ring", 23.500, 0.88),
        spike("enc.bdo.ctx", 32.600, 0.39),
        spike("rtd.bed.c", 40.100, 0.54),
    ]
    ras = raster_core(
        44,
        92,
        24,
        97,
        routing(
            "thalamic-relay.rtd-bed",
            "spikenaut.policy.bdo-clamp",
            [
                ("relay.rtd.bed", "policy.bdo_clamp", 0.65),
                ("relay.ft.bdo", "policy.ring_hold", 0.28),
                ("relay.ae.pack", "policy.bdo_clamp", -0.47),
            ],
            "noradrenaline",
            0.05,
            "surprise-gated pre_post_stdp; NA at RTD win (5.100 ms) opens a 50 ms eligibility "
            "trace that still covers the 22.200 ms packing-ring dump",
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
                    pop("bdo_clamp", 48, 0.50, 220.0, 4),
                    pop("ring_hold", 48, 0.50, 50.0, 1),
                    pop("bed_cap_veto", 24, 0.75),
                ],
            ),
        ]
    )
    return wrap_record(
        "ttf-r100-517",
        "Butyrol-Clough GBL / D-3: bed RTD beats BDO encoder by 240 us; correct "
        "MODIFY still eats an in-window packing-ring dump (partnered negative total -0.44)",
        state,
        spikes,
        proposed,
        safety,
        executed,
        future,
        ticks,
        "Partnered negative. Process-correct MODIFY; world still charges inside the "
        "44 ms raster. total -0.44 = 0.34 + -0.62 + -0.16 + 0.04 + -0.04. Named "
        "isolate+ring-pull loss is not netted into task_progress.",
        ras,
        gate,
        "gamma-butyrolactone-dehydro",
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
        "17 min gap.",
        2,
    )


def record_518():
    ticks = [
        tick(1560, 0.01, 0.04, 0.02, 0.01, 0.01),
        tick(3900, 0.02, 0.08, 0.02, 0.02, 0.01),
        tick(4120, 0.01, 0.06, 0.02, 0.01, 0.01),
        tick(5140, 0.03, 0.12, 0.04, 0.04, 0.02),
        tick(5480, 0.02, 0.07, 0.01, 0.01, 0.01),
        tick(480000000, 0.01, 0.03, 0.01, 0.01, 0.00),
    ]
    spikes = [
        spike("enc.so2.ctx", 0.940, 0.44),
        spike("ae.ox.pps", 2.060, 0.71),
        spike("enc.so2.th", 2.980, 0.50),
        spike("ae.ox.pps", 3.900, 1.36),
        spike("enc.so2.th", 4.120, 1.12),
        spike("ctrl.gate", 5.140, 0.96),
        spike("ae.ox.pps", 7.180, 0.80),
        spike("enc.so2.th", 10.600, 0.58),
        spike("ctrl.gate", 15.800, 0.84),
        spike("ae.ox.pps", 23.400, 0.67),
        spike("enc.so2.th", 31.200, 0.46),
        spike("t.reboiler.ctx", 39.600, 0.38),
    ]
    excerpt = independent_excerpt(100518, 104, 42000, 13, spike_avoid_us(spikes))
    state = OrderedDict(
        [
            (
                "description",
                "Sulfolane HIL oxidizer OX-2 at Sulfol-Dumble already shows oxidizer-shell acoustic emission at 52 pps when that burst races a sulfur-dioxide encoder still printing 3.4 t/h. SO2 is legal only if AE <= 38 pps. AE-first latches hold; encoder-first would treat in-band t/h as shell clearance.",
            ),
            ("domain", "sulfolane-oxidizer"),
            ("sim_or_real", "hil"),
            (
                "goal",
                "Do not raise OX-2 SO2 unless shell AE <= 38 pps; keep butadiene feed 0 t/h until the "
                "oxidizer is quiet.",
            ),
            ("t0_us", 1762300000000518),
            ("gate_latency_us", 1240),
            ("race_window_us", 340),
            ("race_window_rel_ms", [3.900, 4.240]),
            (
                "race",
                OrderedDict(
                    [
                        (
                            "contenders",
                            [
                                "ae.ox.pps 52 pps oxidizer-shell flare",
                                "enc.so2.th 3.4 t/h still-in-band sulfur dioxide",
                            ],
                        ),
                        (
                            "semantics",
                            "AE-first latches REJECT hold 0 t/h; encoder-first would keep 3.4 t/h on an in-band-rate-as-clearance model.",
                        ),
                        (
                            "window_derivation",
                            "340 us = one AE envelope slot versus the SO2-encoder publisher on this pad cycle.",
                        ),
                        (
                            "order_evidence_note",
                            "Margin 220 us vs combined jitter 58 us (AE 26 + encoder 32): 3.8x over a 2.0x trust floor. Pad injects encoder 80-120 us before the AE envelope finishes (loop lag, not a sensor fault); the encoder packet is still the loser in this 340 us window.",
                        ),
                    ]
                ),
            ),
            (
                "sensors",
                [
                    "oxidizer-shell AE analyzer, 26 us jitter, 38 pps trip",
                    "SO2 encoder, 32 us jitter",
                    "reboiler RTD (context)",
                    "sulfolane off-gas (context)",
                ],
            ),
            (
                "constraints",
                OrderedDict(
                    [
                        ("ae_trip_pps", 38.0),
                        ("observed_ae_pps", 52.0),
                        ("so2_cap_t_h", 4.5),
                        ("proposed_so2_t_h", 3.4),
                    ]
                ),
            ),
            (
                "hil",
                OrderedDict(
                    [
                        ("bench", "Sulfol-Dumble SD-HIL sulfolane oxidizer pad, OX-2"),
                        (
                            "inject",
                            "AE envelope delayed 80-120 us vs encoder; loop lag, not a false AE pickup",
                        ),
                    ]
                ),
            ),
            (
                "episode_steps",
                [
                    "1. OX-2 on Sulfol-Dumble HIL pad; butadiene armed; SO2 3.4 t/h.",
                    "2. AE trip 38 pps; observed 52 pps oxidizer-shell flare.",
                    "3. Encoder precursor at 0.940 ms.",
                    "4. Race window [3.900, 4.240] ms.",
                    "5. AE 52 pps at 3.900 ms (winner).",
                    "6. SO2 encoder 3.4 t/h at 4.120 ms (loser by 220 us).",
                    "7. Gate at 5.140 ms: REJECT hold 0 t/h, do not raise oxidizer.",
                    "8. Pad recycle 8 min; AE decays under 38 pps after hold.",
                    "9. Reboiler never ran a shell dump; encoder-as-clearance would have oxidized into the flare.",
                    "10. QA: correct gate was REJECT; leave 0 t/h until AE <= 38 pps.",
                ],
            ),
        ]
    )
    proposed = OrderedDict(
        [
            ("name", "so2_3p4"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("so2_t_h", 3.4),
                        ("ae_pps", 52.0),
                        ("hold", False),
                    ]
                ),
            ),
            (
                "evidence",
                OrderedDict(
                    [
                        ("ae_pps", 52.0),
                        ("ae_trip_pps", 38.0),
                        ("so2_t_h", 3.4),
                        ("so2_cap_t_h", 4.5),
                        ("race_margin_us", 220),
                        ("combined_jitter_us", 58),
                        ("t_gate_us", 5140),
                    ]
                ),
            ),
            (
                "basis",
                "Planner proposes 3.4 t/h because SO2 is under the 4.5 t/h cap and treats the encoder as shell clearance, ignoring the 52 pps AE flare.",
            ),
        ]
    )
    safety = OrderedDict(
        [
            ("decision", "REJECT"),
            ("correctness", "correct"),
            (
                "rationale",
                "AE 52 pps won by 220 us and is over the 38 pps trip. Encoder 3.4 t/h is under the 4.5 t/h cap but is not clearance. REJECT: hold 0 t/h until AE <= 38 pps.",
            ),
            (
                "constraint_checked",
                OrderedDict(
                    [
                        (
                            "shell_ae_pps",
                            OrderedDict(
                                [
                                    ("trip", 38.0),
                                    ("observed", 52.0),
                                    ("executed_so2_t_h", 0.0),
                                ]
                            ),
                        ),
                        (
                            "order_evidence",
                            OrderedDict(
                                [
                                    ("margin_us", 220),
                                    ("combined_jitter_us", 58),
                                    ("ratio", 3.79),
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
            ("name", "so2_hold_ae"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("so2_t_h", 0.0),
                        ("ae_pps", 52.0),
                        ("hold", True),
                    ]
                ),
            ),
            (
                "gate_effect",
                "REJECT: SO2 3.4 -> 0 t/h. Routing relay.ae.ox -> policy.hold_reject. Do not oxidize into the 52 pps flare.",
            ),
        ]
    )
    future = OrderedDict(
        [
            (
                "summary",
                "Correct REJECT held OX-2 at 0 t/h while AE 52 pps decayed. Encoder-as-clearance would have oxidized 3.4 t/h into the flare. Pad recycle 8 min.",
            ),
            (
                "state_delta",
                OrderedDict(
                    [
                        ("so2", "held at 0 t/h"),
                        ("shell", "AE flare decaying under trip after hold"),
                        ("reboiler", "no shell dump"),
                        ("pad", "8 min recycle"),
                    ]
                ),
            ),
            (
                "surprises",
                [
                    "Pad injects encoder 80-120 us before AE envelope finish; that is loop lag, not a false AE pickup.",
                    "Delayed (8 min): pad recycle restacks the sulfolane oxidizer after AE < 38 pps.",
                ],
            ),
            (
                "race_result",
                OrderedDict(
                    [
                        ("winner", "ae.ox.pps (3.900 ms, 52 pps)"),
                        ("loser", "enc.so2.th (4.120 ms, 3.4 t/h)"),
                        ("margin_us", 220),
                        (
                            "counterfactual_if_reversed",
                            "Encoder-first by < 220 us would have treated 3.4 t/h as clearance and oxidized into the 52 pps flare. The REJECT is still required; reversal only delays the AE bind.",
                        ),
                    ]
                ),
            ),
            ("reward_inflection_t_us", 5140),
            (
                "reward_inflection_note",
                "Safety credit lands at the correct REJECT (5.140 ms, tick 4). Pad recycle is delayed surprise.",
            ),
            ("delayed_surprise_s", 480.0),
            ("pad_recycle_s", 480),
        ]
    )
    ras = raster_core(
        42,
        104,
        22,
        96,
        routing(
            "relay.ae.ox",
            "policy.hold_reject",
            [
                ("relay.ae.ox", "policy.hold_reject", 0.75),
                ("relay.enc.so2", "policy.ox_go", 0.17),
            ],
            "dopamine",
            0.06,
            "ae_trip_stdp; DA tags the hold_reject bind at the AE win",
        ),
        excerpt,
    )
    gate = OrderedDict(
        [
            ("decision_window_ms", 0.34),
            ("decision", "REJECT"),
            (
                "populations",
                [
                    pop("hold_reject", 64, 0.50, 200.0, 4),
                    pop("ox_go", 64, 0.80, 8.0, 0),
                    pop("ae_trip_veto", 32, 0.70),
                ],
            ),
        ]
    )
    return wrap_record(
        "ttf-r100-518",
        "Sulfol-Dumble sulfolane HIL / OX-2: shell AE 52 pps beats SO2 encoder 3.4 t/h by 220 us; correct REJECT holds the oxidizer",
        state,
        spikes,
        proposed,
        safety,
        executed,
        future,
        ticks,
        "Correct REJECT. AE 52 > 38 trip beats in-band SO2. total +0.78 = 0.10 + 0.40 + 0.12 + 0.10 + 0.06.",
        ras,
        gate,
        "sulfolane-oxidizer",
        [
            "reject",
            "hil-pad",
            "ae-vs-encoder",
            "shell-hold",
            "sidecar-convictable",
            "hil",
        ],
        "Teaches a probe that an in-band SO2 encoder is not shell clearance when AE is over trip and routing.table[0].to is policy.hold_reject.",
        3,
    )


def record_519():
    ticks = [
        tick(2080, 0.06, 0.04, 0.03, 0.02, 0.01),
        tick(5200, 0.10, 0.06, 0.04, 0.02, 0.02),
        tick(5440, 0.06, 0.04, 0.02, 0.01, 0.01),
        tick(6040, 0.12, 0.08, 0.05, 0.03, 0.02),
        tick(6400, 0.05, 0.04, 0.02, 0.01, 0.01),
        tick(480000000, 0.03, 0.02, 0.02, 0.01, 0.01),
    ]
    spikes = [
        spike("ft.gbl.ctx", 1.180, 0.40),
        spike("rtd.liquor.c", 2.640, 0.58),
        spike("ir.coil.smear", 4.020, 0.48),
        spike("rtd.liquor.c", 5.200, 1.26),
        spike("ir.coil.smear", 5.440, 1.08),
        spike("ctrl.gate", 6.040, 0.94),
        spike("rtd.liquor.c", 8.220, 0.72),
        spike("ir.coil.smear", 11.600, 0.57),
        spike("ctrl.gate", 16.800, 0.80),
        spike("rtd.liquor.c", 22.400, 0.53),
        spike("ft.gbl.ctx", 27.200, 0.38),
    ]
    excerpt = independent_excerpt(100519, 64, 30000, 12, spike_avoid_us(spikes))
    state = OrderedDict(
        [
            (
                "description",
                "NMP hydrogenator N-5 at Pyrrol-Knowe already holds a liquor RTD of 74.0 C when that analog sample races a coil-skin IR smear still printing 108 C. Commanded 5.8 t/h and 74.0 C sit 1.8 t/h and 22 C inside the legal envelopes. The liquor win only ratifies the gamma-butyrolactone already in the jacket.",
            ),
            ("domain", "nmp-hydrogenator"),
            ("sim_or_real", "simulated"),
            (
                "goal",
                "Finish the NMP hydrogenation pass on Pyrrol-Knowe, keep liquor <= 96.0 C and feed >= 4.0 t/h, and leave coil draft in spec.",
            ),
            ("t0_us", 1762300000000519),
            ("gate_latency_us", 840),
            ("race_window_us", 360),
            ("race_window_rel_ms", [5.200, 5.560]),
            (
                "race",
                OrderedDict(
                    [
                        (
                            "contenders",
                            [
                                "rtd.liquor.c 74.0 C NMP liquor",
                                "ir.coil.smear 108 C over-temp claim",
                            ],
                        ),
                        (
                            "semantics",
                            "Liquor-first confirms the already-legal 5.8 t/h / 74.0 C pass; smear-first would have treated the liquor RTD as a smear echo and looked for an extra hold the jacket does not need.",
                        ),
                        (
                            "window_derivation",
                            "360 us = one 1D-NMP hydrogenation kernel step versus the coil-IR publisher on this rigid GBL-to-NMP train.",
                        ),
                        (
                            "order_evidence_note",
                            "Margin 240 us vs combined jitter 70 us (liquor 30 + coil 40): 3.4x over a 2.0x trust floor. Reversing order by < 240 us would not make the proposed pass illegal; it would only have delayed confirmation.",
                        ),
                    ]
                ),
            ),
            (
                "sensors",
                [
                    "liquor RTD, 30 us jitter",
                    "coil-skin IR smear, 40 us jitter",
                    "GBL encoder (context)",
                    "methylamine GC (context)",
                ],
            ),
            (
                "constraints",
                OrderedDict(
                    [
                        ("liquor_cap_C", 96.0),
                        ("observed_liquor_C", 74.0),
                        ("feed_floor_t_h", 4.0),
                        ("proposed_feed_t_h", 5.8),
                    ]
                ),
            ),
            (
                "simulation",
                OrderedDict(
                    [
                        (
                            "solver",
                            "1D NMP hydrogenation hotspot kernel + shrinking-core GBL feed, seed 100; 12 axial nodes; NOT lumped tank, NOT a fluid-LES field",
                        ),
                        (
                            "fidelity_limits",
                            "No radial maldistribution or coil-side coke; jackets are rigid temperature sources. Raster is kernelized events, not an independent LIF.",
                        ),
                    ]
                ),
            ),
            (
                "episode_steps",
                [
                    "1. Pyrrol-Knowe hydrogenator indexed; N-5 holding 5.8 t/h at 74.0 C liquor.",
                    "2. Caps: liquor 96.0 C, feed floor 4.0 t/h; both proposed values inside.",
                    "3. GBL precursor at 1.180 ms.",
                    "4. Race window [5.200, 5.560] ms.",
                    "5. Liquor RTD 74.0 C at 5.200 ms (winner).",
                    "6. Coil IR smear 108 C at 5.440 ms (loser by 240 us).",
                    "7. Gate at 6.040 ms: ACCEPT 5.8 t/h / 74.0 C already legal.",
                    "8. Pass continues; no extra hold.",
                    "9. 8 min survey confirms coil draft still in spec.",
                    "10. QA: ACCEPT params identical to proposed.",
                ],
            ),
        ]
    )
    proposed = OrderedDict(
        [
            ("name", "nmp_5p8_thold"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("feed_t_h", 5.8),
                        ("liquor_C", 74.0),
                        ("n_id", 5),
                        ("hold", False),
                    ]
                ),
            ),
            (
                "evidence",
                OrderedDict(
                    [
                        ("liquor_C", 74.0),
                        ("liquor_cap_C", 96.0),
                        ("feed_t_h", 5.8),
                        ("feed_floor_t_h", 4.0),
                        ("race_margin_us", 240),
                        ("combined_jitter_us", 70),
                        ("t_gate_us", 6040),
                    ]
                ),
            ),
            (
                "basis",
                "Planner proposes 5.8 t/h because liquor 74.0 C is 22.0 C under the 96.0 C cap and feed is 1.8 t/h over the 4.0 t/h floor.",
            ),
        ]
    )
    safety = OrderedDict(
        [
            ("decision", "ACCEPT"),
            ("correctness", "correct"),
            (
                "rationale",
                "Liquor 74.0 C won by 240 us and is under 96.0 C. Feed 5.8 t/h is over 4.0 t/h. ACCEPT the already-legal pass; coil IR smear is not a cap violation.",
            ),
            (
                "constraint_checked",
                OrderedDict(
                    [
                        (
                            "liquor_C",
                            OrderedDict(
                                [
                                    ("cap", 96.0),
                                    ("observed", 74.0),
                                    ("executed_feed_t_h", 5.8),
                                ]
                            ),
                        ),
                        (
                            "order_evidence",
                            OrderedDict(
                                [
                                    ("margin_us", 240),
                                    ("combined_jitter_us", 70),
                                    ("ratio", 3.43),
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
            ("name", "nmp_5p8_thold"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("feed_t_h", 5.8),
                        ("liquor_C", 74.0),
                        ("n_id", 5),
                        ("hold", False),
                    ]
                ),
            ),
            (
                "gate_effect",
                "ACCEPT: feed 5.8 t/h and liquor 74.0 C unchanged. Routing relay.rtd.liquor -> policy.go_accept.",
            ),
        ]
    )
    future = OrderedDict(
        [
            (
                "summary",
                "Correct ACCEPT left N-5 at 5.8 t/h / 74.0 C. Coil IR smear did not justify a hold. 8 min survey confirmed draft in spec.",
            ),
            (
                "state_delta",
                OrderedDict(
                    [
                        ("nmp", "still 5.8 t/h / 74.0 C"),
                        ("coils", "in spec after survey"),
                        ("train", "NMP continues"),
                        ("hold", "none applied"),
                    ]
                ),
            ),
            (
                "surprises",
                [
                    "Coil IR smear is an off-jacket optical claim, not a liquor-temperature violation.",
                    "Delayed (8 min): survey restacks N-5 without a recovery hold.",
                ],
            ),
            (
                "race_result",
                OrderedDict(
                    [
                        ("winner", "rtd.liquor.c (5.200 ms, 74.0 C)"),
                        ("loser", "ir.coil.smear (5.440 ms, 108 C claim)"),
                        ("margin_us", 240),
                        (
                            "counterfactual_if_reversed",
                            "Smear-first by < 240 us would only delay confirmation. The pass stays legal either way; ACCEPT is still required.",
                        ),
                    ]
                ),
            ),
            ("reward_inflection_t_us", 6040),
            (
                "reward_inflection_note",
                "Task credit lands at the ACCEPT (6.040 ms, tick 4). Survey is delayed surprise.",
            ),
            ("delayed_surprise_s", 480.0),
            ("survey_s", 480),
        ]
    )
    ras = raster_core(
        30,
        64,
        34,
        65,
        routing(
            "relay.rtd.liquor",
            "policy.go_accept",
            [
                ("relay.rtd.liquor", "policy.go_accept", 0.69),
                ("relay.ir.coil", "policy.smear_hold", 0.20),
            ],
            "serotonin",
            0.07,
            "legal_nmp_stdp; 5-HT tags the go_accept bind at the liquor-RTD win",
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
                    pop("liquor_cap_veto", 20, 0.75),
                ],
            ),
        ]
    )
    return wrap_record(
        "ttf-r100-519",
        "Pyrrol-Knowe NMP / N-5: liquor 74.0 C beats coil smear by 240 us; ACCEPT already-legal 5.8 t/h pass",
        state,
        spikes,
        proposed,
        safety,
        executed,
        future,
        ticks,
        "Correct ACCEPT of an already-legal 1D NMP hydrogenation hotspot pass. total +1.06 = 0.42 + 0.28 + 0.18 + 0.10 + 0.08.",
        ras,
        gate,
        "nmp-hydrogenator",
        [
            "accept",
            "already-legal",
            "simulated-nmp-train",
            "liquor-vs-coil",
            "sidecar-convictable",
            "simulated",
        ],
        "Teaches that a liquor RTD under cap can confirm an already-legal NMP pass without a coil-IR smear becoming a hold.",
        4,
    )


def record_520():
    ticks = [
        tick(1440, 0.06, 0.04, 0.03, 0.02, 0.01),
        tick(3600, 0.10, 0.08, 0.04, 0.02, 0.02),
        tick(3820, 0.06, 0.04, 0.02, 0.02, 0.01),
        tick(4320, 0.12, 0.08, 0.05, 0.04, 0.02),
        tick(4680, 0.06, 0.05, 0.02, 0.01, 0.01),
        tick(300000000, 0.04, 0.03, 0.02, 0.01, 0.01),
    ]
    spikes = [
        spike("enc.acetone.ctx", 0.740, 0.39),
        spike("rtd.shell.c", 1.820, 0.58),
        spike("ir.vapor.glint", 2.720, 0.49),
        spike("rtd.shell.c", 3.600, 1.28),
        spike("ir.vapor.glint", 3.820, 1.10),
        spike("ctrl.gate", 4.320, 0.95),
        spike("rtd.shell.c", 5.900, 0.76),
        spike("ir.vapor.glint", 8.100, 0.60),
        spike("ctrl.gate", 12.400, 0.83),
        spike("rtd.shell.c", 16.200, 0.52),
        spike("ir.vapor.glint", 18.800, 0.41),
    ]
    excerpt = independent_excerpt(100520, 56, 24000, 11, spike_avoid_us(spikes))
    state = OrderedDict(
        [
            (
                "description",
                "Isophorone condenser C-8 at Isophor-Taing is mid-pass at 9.2 t/h with shell thermocouple 46.0 C under a 68.0 C packed-column ceiling while a vapor-head optical hitch still claims 81 C. The thermocouple arrival merely confirms an acetone cut that is already 2.2 t/h above the 7.0 t/h floor; no extra hold is licensed.",
            ),
            ("domain", "isophorone-condenser"),
            ("sim_or_real", "designed"),
            (
                "goal",
                "Run C-8 at 9.2 t/h, keep shell <= 68.0 C and vapor IR <= 110 C, and leave the isophorone train on schedule.",
            ),
            ("t0_us", 1762300000000520),
            ("gate_latency_us", 720),
            ("race_window_us", 360),
            ("race_window_rel_ms", [3.600, 3.960]),
            (
                "race",
                OrderedDict(
                    [
                        (
                            "contenders",
                            [
                                "rtd.shell.c 46.0 C condenser shell",
                                "ir.vapor.glint vapor-space hitch claim",
                            ],
                        ),
                        (
                            "semantics",
                            "Shell-first confirms the already-legal 9.2 t/h / 46.0 C pass; glint-first would have treated the shell RTD as a hitch echo and looked for an extra hold the condenser does not need.",
                        ),
                        (
                            "window_derivation",
                            "360 us = one shell-RTD slot versus the vapor-IR publisher on this acetone-condensation bus.",
                        ),
                        (
                            "order_evidence_note",
                            "Margin 220 us vs combined jitter 60 us (shell 26 + IR 34): 3.7x over a 2.0x trust floor. Reversing order by < 220 us would not make the proposed pass illegal; it would only have delayed confirmation.",
                        ),
                    ]
                ),
            ),
            (
                "sensors",
                [
                    "shell RTD, 26 us jitter",
                    "vapor-space IR glint, 34 us jitter",
                    "acetone encoder (context)",
                    "isophorone assay (context)",
                ],
            ),
            (
                "constraints",
                OrderedDict(
                    [
                        ("shell_cap_C", 68.0),
                        ("observed_shell_C", 46.0),
                        ("feed_floor_t_h", 7.0),
                        ("proposed_feed_t_h", 9.2),
                        ("vapor_cap_C", 110.0),
                        ("observed_vapor_C", 81.0),
                    ]
                ),
            ),
            (
                "episode_steps",
                [
                    "1. Condenser C-8 indexed on Isophor-Taing; feed armed 9.2 t/h pass.",
                    "2. Caps: shell 68.0 C, vapor 110 C, feed floor 7.0 t/h.",
                    "3. Encoder precursor at 0.740 ms.",
                    "4. Race window [3.600, 3.960] ms.",
                    "5. Shell RTD 46.0 C at 3.600 ms (winner).",
                    "6. Vapor IR glint at 3.820 ms (loser by 220 us).",
                    "7. Gate at 4.320 ms: ACCEPT 9.2 t/h / 46.0 C already legal.",
                    "8. Pass continues; no extra hold.",
                    "9. 5 min survey confirms vapor IR still under 110 C.",
                    "10. QA: ACCEPT params identical to proposed.",
                ],
            ),
        ]
    )
    proposed = OrderedDict(
        [
            ("name", "pass_9p2"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("feed_t_h", 9.2),
                        ("shell_C", 46.0),
                        ("c_id", 8),
                        ("hold", False),
                    ]
                ),
            ),
            (
                "evidence",
                OrderedDict(
                    [
                        ("shell_C", 46.0),
                        ("shell_cap_C", 68.0),
                        ("feed_t_h", 9.2),
                        ("feed_floor_t_h", 7.0),
                        ("vapor_C", 81.0),
                        ("vapor_cap_C", 110.0),
                        ("race_margin_us", 220),
                        ("combined_jitter_us", 60),
                        ("t_gate_us", 4320),
                    ]
                ),
            ),
            (
                "basis",
                "Planner proposes a 9.2 t/h pass because shell 46.0 C is 22.0 C under the 68.0 C cap and vapor IR 81 C is under 110 C.",
            ),
        ]
    )
    safety = OrderedDict(
        [
            ("decision", "ACCEPT"),
            ("correctness", "correct"),
            (
                "rationale",
                "Shell 46.0 C won by 220 us and is under 68.0 C. Vapor IR 81 C is under 110 C. Feed 9.2 t/h is over the 7.0 t/h floor. ACCEPT the already-legal pass.",
            ),
            (
                "constraint_checked",
                OrderedDict(
                    [
                        (
                            "shell_C",
                            OrderedDict(
                                [
                                    ("cap", 68.0),
                                    ("observed", 46.0),
                                    ("executed_feed_t_h", 9.2),
                                ]
                            ),
                        ),
                        (
                            "order_evidence",
                            OrderedDict(
                                [
                                    ("margin_us", 220),
                                    ("combined_jitter_us", 60),
                                    ("ratio", 3.67),
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
            ("name", "pass_9p2"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("feed_t_h", 9.2),
                        ("shell_C", 46.0),
                        ("c_id", 8),
                        ("hold", False),
                    ]
                ),
            ),
            (
                "gate_effect",
                "ACCEPT: 9.2 t/h pass and 46.0 C unchanged. Routing relay.rtd.shell -> policy.go_accept.",
            ),
        ]
    )
    future = OrderedDict(
        [
            (
                "summary",
                "Correct ACCEPT left C-8 on a 9.2 t/h / 46.0 C pass. Vapor IR glint did not justify a hold. 5 min survey confirmed IR still under 110 C.",
            ),
            (
                "state_delta",
                OrderedDict(
                    [
                        ("condenser", "still 9.2 t/h / 46.0 C"),
                        ("vapor", "81 C under 110 cap"),
                        ("train", "on schedule"),
                        ("hold", "none applied"),
                    ]
                ),
            ),
            (
                "surprises",
                [
                    "Vapor IR 81 C glint is residual acetone steam, not a packed-shell trip.",
                    "Delayed (5 min): survey restacks C-8 without a recovery hold.",
                ],
            ),
            (
                "race_result",
                OrderedDict(
                    [
                        ("winner", "rtd.shell.c (3.600 ms, 46.0 C)"),
                        ("loser", "ir.vapor.glint (3.820 ms, vapor glint)"),
                        ("margin_us", 220),
                        (
                            "counterfactual_if_reversed",
                            "Glint-first by < 220 us would only delay confirmation. The pass stays legal either way; ACCEPT is still required.",
                        ),
                    ]
                ),
            ),
            ("reward_inflection_t_us", 4320),
            (
                "reward_inflection_note",
                "Task credit lands at the ACCEPT (4.320 ms, tick 4). Survey is delayed surprise.",
            ),
            ("delayed_surprise_s", 300.0),
            ("survey_s", 300),
        ]
    )
    ras = raster_core(
        24,
        56,
        38,
        51,
        routing(
            "relay.rtd.shell",
            "policy.go_accept",
            [
                ("relay.rtd.shell", "policy.go_accept", 0.67),
                ("relay.ir.vapor", "policy.hitch_hold", 0.19),
            ],
            "adenosine",
            0.04,
            "legal_isophorone_stdp; adenosine tags the go_accept bind at the shell-RTD win",
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
                    pop("go_accept", 40, 0.50, 160.0, 2),
                    pop("hitch_hold", 40, 0.80, 10.0, 0),
                    pop("shell_cap_veto", 20, 0.75),
                ],
            ),
        ]
    )
    return wrap_record(
        "ttf-r100-520",
        "Isophor-Taing condenser / C-8: shell 46.0 C beats vapor glint by 220 us; ACCEPT already-legal 9.2 t/h pass",
        state,
        spikes,
        proposed,
        safety,
        executed,
        future,
        ticks,
        "Correct ACCEPT of an already-legal isophorone condensation pass. total +1.14 = 0.44 + 0.32 + 0.18 + 0.12 + 0.08.",
        ras,
        gate,
        "isophorone-condenser",
        [
            "accept",
            "already-legal",
            "shell-vs-vapor-ir",
            "sidecar-convictable",
            "designed",
        ],
        "Teaches that a shell RTD under cap can confirm an already-legal isophorone pass without a vapor-IR hitch becoming a hold.",
        5,
    )


