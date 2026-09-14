def harvest_occupancy() -> tuple[set[str], set[str]]:
    domains: set[str] = set()
    plants: set[str] = set()
    for path in sorted(Path("/tmp").glob("ttf-r*/batch-r*.jsonl")):
        if path.parent.name == "ttf-r66":
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except OSError:
            continue
        if not text.strip():
            continue
        for line in text.splitlines():
            if not line.strip():
                continue
            rec = json.loads(line)
            st = rec.get("state") or {}
            meta = rec.get("meta") or {}
            if isinstance(st.get("domain"), str):
                domains.add(st["domain"])
            if isinstance(meta.get("domain"), str):
                domains.add(meta["domain"])
            plants.update(PLANT_RE.findall(json.dumps(rec)))
    for path in sorted(Path("/tmp").glob("ttf-r*/NOTES-r*.md")):
        if path.parent.name == "ttf-r66":
            continue
        try:
            txt = path.read_text(encoding="utf-8")
        except OSError:
            continue
        plants.update(PLANT_RE.findall(txt))
        match = re.search(r"Domains this batch:\s*(.*)", txt)
        if match:
            domains.update(re.findall(r"`([^`]+)`", match.group(1)))
    for glob_name in (
        "ttf-r*/gen_r*.py",
        "ttf-r*/_records.py",
        "ttf-r*/_records_r*.py",
        "ttf-r*/_head.py",
        "ttf-r*/_tail.py",
    ):
        for path in Path("/tmp").glob(glob_name):
            if path.parent.name == "ttf-r66":
                continue
            try:
                txt = path.read_text(encoding="utf-8", errors="ignore")
            except OSError:
                continue
            domains.update(re.findall(r'\("domain",\s*"([^"]+)"\)', txt))
            match = re.search(
                r"(THIS_DOMAINS|MY_DOMAINS)\s*=\s*[\{(](.*?)[\})]", txt, re.S
            )
            if match:
                domains.update(re.findall(r'"([^"]+)"', match.group(2)))
            match = re.search(
                r"(THIS_PLANTS|MY_PLANTS)\s*=\s*[\{(](.*?)[\})]", txt, re.S
            )
            if match:
                plants.update(re.findall(r'"([^"]+)"', match.group(2)))
            plants.update(PLANT_RE.findall(txt))
    return domains, plants


def meta_block(
    domain,
    tags,
    distillation_value,
    batch_position,
    supervisor_error_type=None,
) -> OrderedDict:
    body = OrderedDict(
        [
            ("round", 66),
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


def lif_346_excerpt():
    n = 76
    dt_us = 100
    tau_m_ms = 18.5
    v_th = 1.0
    v_reset = 0.0
    refractory_us = 1000
    i_bias = 0.90
    i_stim_peak = 2.50
    stim = (21400, 25600)
    seed = 66346
    window_us = 42000
    i_clamp_extra = 0.64
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
    early = [(t, nid) for t, nid in spikes if t < 21400]
    burst = [(t, nid) for t, nid in spikes if 21400 <= t < 25600]
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
            group = [1 for tt, _ in picked if (tt < 21400) == (pool[0][0] < 21400)]
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
    take(burst, 9, label_times=(22400, 23200, 24400))
    clamp = [(t, nid) for t, nid in picked if t < 21400][:7]
    blow = [(t, nid) for t, nid in picked if t >= 21400][:9]
    picked = sorted(clamp + blow, key=lambda item: (item[0], item[1]))
    if len(picked) < 8:
        raise ValueError(
            f"LIF excerpt too short {len(picked)} (early={len(early)} burst={len(burst)})"
        )
    channels = ["lif.clamp" if t < 21400 else "lif.blow" for t, _ in picked]
    lif = OrderedDict(
        [
            ("model", "leaky_integrate_and_fire"),
            ("n", 76),
            ("dt_us", 100),
            ("tau_m_ms", 18.5),
            ("v_rest", 0.0),
            ("v_reset", 0.0),
            ("v_th", 1.0),
            ("r_m", 1.0),
            ("refractory_us", 1000),
            ("i_bias", 0.90),
            ("i_stim_peak", 2.50),
            ("stim_t_us", [21400, 25600]),
            ("i_clamp_extra", 0.64),
            ("clamp_n", 14),
            ("seed", 66346),
            (
                "note",
                "Population sim scoped to this sidecar. Plant remains designed. "
                "Neurons 0-13 carry +0.64 air-clamp bias; stim 21.4-25.6 ms is the tube-sheet gasket blow.",
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


def record_346():
    excerpt, extra = lif_346_excerpt()
    ticks = [
        tick(2520, 0.05, -0.02, -0.02, 0.01, 0.00),
        tick(6280, 0.07, -0.04, -0.03, 0.01, -0.01),
        tick(6496, 0.04, -0.03, -0.02, 0.00, 0.00),
        tick(7160, 0.08, -0.06, -0.03, 0.02, -0.02),
        tick(22400, 0.06, -0.38, -0.04, -0.02, -0.02),
        tick(900000000, 0.02, -0.05, -0.02, 0.00, -0.01),
    ]
    state = OrderedDict(
        [
            (
                "description",
                "Vanadium-molybdate tubes on Skarn-Holt SH-7 / Bed-Deck BD-3 show a 442 C "
                "hotspot over the 430 C trip even though the air orifice still prints a legal "
                "18.4 kNm3/h. Binding the thermocouple first cuts air; binding the orifice first "
                "would ride the cruise. Tube-sheet gasket strain stays invisible to both "
                "contenders until the AE dump.",
            ),
            ("domain", "maleic-anhydride-bed"),
            ("sim_or_real", "designed"),
            (
                "goal",
                "Finish the SH-7 n-butane pass, keep bed hotspot <= 430 C, and leave the "
                "tube-sheet gasket unmarked.",
            ),
            ("t0_us", 1756850400000346),
            ("gate_latency_us", 880),
            ("race_window_us", 400),
            ("race_window_rel_ms", [6.28, 6.68]),
            (
                "race",
                OrderedDict(
                    [
                        (
                            "contenders",
                            [
                                "tc.bed.C 442 C pulse",
                                "ft.air.knm3h 18.4 kNm3/h cruise",
                            ],
                        ),
                        (
                            "semantics",
                            "Hotspot-first latches air 18.4 -> 12.6 kNm3/h; feed-first keeps "
                            "cruise on a still-cooling bed model.",
                        ),
                        (
                            "window_derivation",
                            "400 us = one 2 kHz bed-TC sample minus air-orifice group delay on "
                            "this maleic fixed-bed bus.",
                        ),
                        (
                            "order_evidence_note",
                            "Margin 216 us vs combined jitter ~66 us (bed 30 + air 36): 3.3x over "
                            "a 2.0x trust floor. Reversing order by < 216 us inside the 400 us "
                            "window would have kept 18.4 kNm3/h; predicted next-sample 436 C > 430 cap.",
                        ),
                    ]
                ),
            ),
            (
                "sensors",
                [
                    "bed hotspot TC, 2 kHz, 30 us timestamp jitter",
                    "air-orifice FT, 1 kHz, 36 us jitter",
                    "tube-sheet AE puck (context until the blow)",
                    "butane-feed FT (context)",
                ],
            ),
            (
                "constraints",
                OrderedDict(
                    [
                        ("hotspot_cap_C", 430.0),
                        ("observed_bed_C", 442.0),
                        ("proposed_air_knm3h", 18.4),
                        ("butane_tph", 6.2),
                    ]
                ),
            ),
            (
                "episode_steps",
                [
                    "1. Bed-Deck BD-3 indexed on Skarn-Holt SH-7; air armed at 18.4 kNm3/h.",
                    "2. Cruise 18.4 kNm3/h; hotspot 442 C against 430 C cap.",
                    "3. Air precursor at 1.260 ms; bed warm-start 442 C.",
                    "4. Race window [6.280, 6.680] ms opens on the maleic bus.",
                    "5. tc.bed.C 442 C at 6.280 ms (winner).",
                    "6. ft.air.knm3h 18.4 at 6.496 ms (loser by 216 us).",
                    "7. Gate at 7.160 ms (winner + 880 us): MODIFY clamp 18.4 -> 12.6 kNm3/h.",
                    "8. Clamp executes; next-sample hotspot 424 C < 430 cap.",
                    "9. At 22.400 ms stored strain still blows an 18 mm tube-sheet gasket; AE burst.",
                    "10. Bed isolate 15 min (abort_s=900); named un-netted loss, not folded into process heads.",
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
                        ("butane_tph", 6.2),
                        ("salt_C", 390.0),
                    ]
                ),
            ),
            (
                "evidence",
                OrderedDict(
                    [
                        ("bed_C", 442.0),
                        ("hotspot_cap_C", 430.0),
                        ("predicted_unclamped_next_C", 436.0),
                        ("air_knm3h", 18.4),
                        ("race_margin_us", 216),
                        ("combined_jitter_us", 66),
                        ("abort_s", 900),
                    ]
                ),
            ),
            (
                "basis",
                "Planner proposes 18.4 kNm3/h cruise: 442 C looks like a salt-bath spike, not "
                "a hotspot, and BD-3 volume is treated as still open.",
            ),
        ]
    )
    safety = OrderedDict(
        [
            ("decision", "MODIFY"),
            ("correctness", "correct"),
            (
                "rationale",
                "Hotspot 442 C won by 216 us, so the bed is loading heat, not still cooling. "
                "Holding 18.4 kNm3/h predicts next-sample 436 C > 430 cap. MODIFY: air 18.4 -> "
                "12.6 kNm3/h. Observed after clamp 424 C < 430. A full REJECT is not indicated: "
                "a sound n-butane pass accepts 12.6 kNm3/h.",
            ),
            (
                "constraint_checked",
                OrderedDict(
                    [
                        (
                            "bed_C",
                            OrderedDict(
                                [
                                    ("cap", 430.0),
                                    ("observed", 442.0),
                                    ("predicted_unclamped_next", 436.0),
                                    ("clamped_air_knm3h", 12.6),
                                    ("observed_after_clamp", 424.0),
                                ]
                            ),
                        ),
                        (
                            "air_knm3h",
                            OrderedDict([("proposed", 18.4), ("clamped", 12.6)]),
                        ),
                        (
                            "order_evidence",
                            OrderedDict(
                                [
                                    ("margin_us", 216),
                                    ("combined_jitter_us", 66),
                                    ("ratio", 3.27),
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
            ("name", "clamped_air_126"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("air_knm3h", 12.6),
                        ("butane_tph", 6.2),
                        ("salt_C", 390.0),
                    ]
                ),
            ),
            (
                "gate_effect",
                "MODIFY: air 18.4 -> 12.6 kNm3/h. Process-correct vs the 430 C hotspot cap. "
                "Tube-sheet gasket still blows at 22.400 ms.",
            ),
        ]
    )
    future = OrderedDict(
        [
            (
                "summary",
                "Process-correct MODIFY held hotspot at 424 C. At 22.400 ms stored strain "
                "in the tube-sheet gasket still blew an 18 mm patch. Clamp reduced dump energy; "
                "it did not prevent the blow. Partnered negative: process heads stay honest; "
                "world loss is named, not netted.",
            ),
            (
                "state_delta",
                OrderedDict(
                    [
                        ("air", "clamp executed; peak 424 C < 430"),
                        ("gasket", "18 mm blow at 22.400 ms"),
                        ("repair", "15 min bed isolate (abort_s=900)"),
                        ("mission", "SH-7 n-butane pass incomplete this circuit"),
                    ]
                ),
            ),
            (
                "surprises",
                [
                    "Neither bed TC nor air FT predicted the gasket charge; ae.gasket.blow is a new channel at 22.400 ms, 15.240 ms after the gate, still inside the 42 ms raster.",
                    "Delayed (abort_s=900): 15 min bed isolate. Named un-netted loss, not folded into task_progress.",
                ],
            ),
            (
                "un_netted_loss",
                "15 min bed isolate after an 18 mm tube-sheet gasket blow. Safety head -0.58 "
                "prices the split; task_progress stays +0.32 because the air clamp completed "
                "under the 430 C cap. World loss is named here, not subtracted from process heads.",
            ),
            (
                "race_result",
                OrderedDict(
                    [
                        ("winner", "tc.bed.C (6.280 ms, 442 C)"),
                        ("loser", "ft.air.knm3h (6.496 ms, 18.4 kNm3/h)"),
                        ("margin_us", 216),
                        (
                            "counterfactual_if_reversed",
                            "Feed-first by < 216 us inside the 400 us window would have kept "
                            "18.4 kNm3/h cruise; predicted next-sample 436 C would have exceeded "
                            "the 430 cap even without the gasket charge. The MODIFY is still the "
                            "correct process. The blow is a later world charge either way, "
                            "cheaper with the clamp than without.",
                        ),
                    ]
                ),
            ),
            ("reward_inflection_t_us", 22400),
            (
                "reward_inflection_note",
                "Safety collapses at the 22.400 ms tube-sheet gasket blow (tick t_us=22400), inside "
                "the 42 ms raster. The correct MODIFY at 7.160 ms is in the same excerpt. Do "
                "not put inflection on the abort_s=900 isolate tick.",
            ),
            ("delayed_surprise_s", 900.0),
            ("abort_s", 900),
        ]
    )
    spikes = [
        spike("enc.air.ctx", 1.260, 0.42),
        spike("tc.bed.C", 2.520, 0.61),
        spike("ft.air.knm3h", 3.840, 0.50),
        spike("tc.bed.C", 6.280, 1.32),
        spike("ft.air.knm3h", 6.496, 1.14),
        spike("ctrl.gate", 7.160, 0.98),
        spike("tc.bed.C", 8.620, 0.80),
        spike("ft.air.knm3h", 11.400, 0.62),
        spike("ctrl.gate", 15.080, 0.84),
        spike("ae.gasket.blow", 22.400, 1.46),
        spike("ae.gasket.blow", 24.210, 0.91),
        spike("enc.air.ctx", 31.400, 0.41),
        spike("tc.bed.C", 38.200, 0.53),
    ]
    ras = raster_core(
        42,
        76,
        26,
        83,
        routing(
            "thalamic-relay.man-hotspot",
            "spikenaut.policy.air-clamp",
            [
                ("relay.tc.bed", "policy.air_clamp", 0.66),
                ("relay.ft.air", "policy.air_hold", 0.30),
                ("relay.ae.gasket", "policy.air_clamp", -0.45),
            ],
            "noradrenaline",
            0.05,
            "surprise-gated pre_post_stdp; NA at hotspot win (6.280 ms) opens a 50 ms "
            "eligibility trace that still covers the 22.400 ms tube-sheet gasket blow",
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
                    pop("air_clamp", 40, 0.50, 250.0, 4),
                    pop("air_hold", 40, 0.50, 62.5, 1),
                    pop("gasket_veto", 24, 0.75),
                ],
            ),
        ]
    )
    return OrderedDict(
        [
            ("id", "ttf-r66-346"),
            (
                "title",
                "Skarn-Holt SH-7 / Bed-Deck BD-3: hotspot 442 C beats air-feed by 216 us; "
                "correct MODIFY still eats an in-window tube-sheet gasket blow (partnered "
                "negative total -0.46)",
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
                    "42 ms raster. total -0.46 = 0.32 + -0.58 + -0.16 + 0.02 + -0.06. Named bed "
                    "isolate (abort_s=900) is not netted into task_progress.",
                ),
            ),
            ("raster", ras),
            ("gate_snn", gate),
            (
                "meta",
                meta_block(
                    "maleic-anhydride-bed",
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
                    "15 min bed isolate.",
                    1,
                ),
            ),
        ]
    )


def record_347():
    ticks = [
        tick(1760, -0.02, -0.01, -0.02, -0.01, 0.01),
        tick(4180, -0.04, -0.02, -0.04, -0.02, 0.01),
        tick(4332, -0.03, -0.01, -0.03, -0.02, 0.01),
        tick(4920, -0.07, -0.04, -0.09, -0.05, 0.02),
        tick(6410, -0.02, -0.01, -0.02, -0.01, 0.01),
        tick(1320000000, -0.02, -0.01, -0.02, -0.01, 0.00),
    ]
    spikes = [
        spike("dp.slurry.ctx", 0.880, 0.40),
        spike("pt.live.A", 1.760, 0.58),
        spike("pt.idle.B", 2.520, 0.51),
        spike("pt.live.A", 4.180, 1.32),
        spike("pt.idle.B", 4.332, 1.15),
        spike("ctrl.gate", 4.920, 1.00),
        spike("pt.live.A", 6.410, 0.74),
        spike("pt.idle.B", 8.100, 0.61),
        spike("ctrl.gate", 12.000, 0.82),
        spike("dp.slurry.ctx", 16.200, 0.42),
        spike("pt.live.A", 20.600, 0.53),
        spike("pt.idle.B", 23.200, 0.47),
    ]
    excerpt = independent_excerpt(66347, 92, 24000, 14, spike_avoid_us(spikes))
    state = OrderedDict(
        [
            (
                "description",
                "Crystallizer CX-4 on Woad-Ness WN-2 is armed for a 2.8 t/h PTA slurry with "
                "live string-A 4.60 bar against a 6.00 bar mother-liquor cap. Isolated idle "
                "string-B still reports 6.80 bar with quality IDLE. Live-first should ACCEPT "
                "the slurry; a weak supervisor that binds the idle twin onto the trip will "
                "REJECT a legal move.",
            ),
            ("domain", "pta-crystallizer"),
            ("sim_or_real", "designed"),
            (
                "goal",
                "Execute the 2.8 t/h PTA slurry while live string-A stays <= 6.00 bar; do "
                "not spend an IDLE twin string on the crystallizer hold.",
            ),
            ("t0_us", 1756850400000347),
            ("gate_latency_us", 740),
            ("race_window_us", 320),
            ("race_window_rel_ms", [4.12, 4.44]),
            (
                "race",
                OrderedDict(
                    [
                        (
                            "contenders",
                            [
                                "pt.live.A 4.60 bar LIVE",
                                "pt.idle.B 6.80 bar IDLE twin",
                            ],
                        ),
                        (
                            "semantics",
                            "Live-first should ACCEPT 2.8 t/h (4.60 bar < 6.00 bar cap). "
                            "Idle-first tempts a weak supervisor to treat 6.80 bar IDLE as the live string.",
                        ),
                        (
                            "window_derivation",
                            "320 us = one live-A sample minus idle-B group delay on this "
                            "parallel-bank PTA bus.",
                        ),
                        (
                            "order_evidence_note",
                            "Margin 152 us vs combined jitter ~54 us (live 24 + idle 30): 2.8x over "
                            "a 2.0x trust floor. Order is correctly live-first. The error is which "
                            "string the REJECT is bound to, not the race.",
                        ),
                    ]
                ),
            ),
            (
                "sensors",
                [
                    "string-A mother-liquor PT, 4 kHz, 24 us jitter",
                    "string-B idle PT, 4 kHz, 30 us jitter",
                    "slurry differential pressure (context)",
                    "agitator torque (context)",
                ],
            ),
            (
                "constraints",
                OrderedDict(
                    [
                        ("live_cap_bar", 6.00),
                        ("live_bar", 4.60),
                        ("idle_bar", 6.80),
                        ("live_quality", "LIVE"),
                        ("idle_quality", "IDLE"),
                        ("proposed_slurry_tph", 2.8),
                    ]
                ),
            ),
            (
                "episode_steps",
                [
                    "1. CX-4 crystallizer latched; slurry 2.8 t/h armed on WN-2.",
                    "2. Live string-A 4.60 bar LIVE; idle string-B 6.80 bar IDLE, blocked-in and steamed-out.",
                    "3. Slurry-dp precursor at 0.880 ms.",
                    "4. Race window [4.120, 4.440] ms.",
                    "5. pt.live.A 4.60 bar at 4.180 ms (winner).",
                    "6. pt.idle.B 6.80 bar at 4.332 ms (loser by 152 us).",
                    "7. Gate at 4.920 ms: REJECT hold 0.00 t/h (incorrect).",
                    "8. Legal slurry cancelled; live A still 4.60 bar < 6.00 cap.",
                    "9. 6.80 bar remains an IDLE twin, not a live mother-liquor PV.",
                    "10. Delayed missed_window_s=1320 (22 min crystal-size window) while CX-4 waits.",
                ],
            ),
        ]
    )
    proposed = OrderedDict(
        [
            ("name", "slurry_28"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("slurry_tph", 2.8),
                        ("hold", False),
                        ("quality", "LIVE"),
                    ]
                ),
            ),
            (
                "evidence",
                OrderedDict(
                    [
                        ("live_bar", 4.60),
                        ("live_cap_bar", 6.00),
                        ("live_quality", "LIVE"),
                        ("idle_bar", 6.80),
                        ("idle_quality", "IDLE"),
                        ("idle_is_live", False),
                        ("proposed_slurry_tph", 2.8),
                        ("race_margin_us", 152),
                        ("combined_jitter_us", 54),
                        ("missed_window_s", 1320),
                    ]
                ),
            ),
            (
                "basis",
                "Planner proposes 2.8 t/h PTA slurry because live string-A 4.60 bar LIVE is "
                "under the 6.00 bar cap; 6.80 bar is an IDLE twin, not the live PV.",
            ),
        ]
    )
    safety = OrderedDict(
        [
            ("decision", "REJECT"),
            ("correctness", "incorrect"),
            (
                "rationale",
                "Idle twin 6.80 bar looks like a mother-liquor excursion over a 6.00 bar cap "
                "once the supervisor treats IDLE string-B as live. Live-first is treated as a "
                "noisy echo of the same bank. Over-caution on a parallel PTA train is the "
                "stated doctrine.",
            ),
            (
                "constraint_checked",
                OrderedDict(
                    [
                        (
                            "live_bar",
                            OrderedDict(
                                [
                                    ("cap", 6.00),
                                    ("observed", 4.60),
                                    ("executed_slurry_tph", 0.0),
                                    ("quality", "LIVE"),
                                ]
                            ),
                        ),
                        (
                            "idle_bar",
                            OrderedDict(
                                [
                                    ("observed", 6.80),
                                    ("misbound_as", "live_string"),
                                    ("quality", "IDLE"),
                                ]
                            ),
                        ),
                        (
                            "order_evidence",
                            OrderedDict(
                                [
                                    ("margin_us", 152),
                                    ("combined_jitter_us", 54),
                                    ("ratio", 2.81),
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
            ("name", "pta_hold_wrong_idle"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("slurry_tph", 0.0),
                        ("hold", True),
                        ("quality", "LIVE"),
                    ]
                ),
            ),
            (
                "gate_effect",
                "REJECT (incorrect): slurry 2.8 -> 0.00 t/h. Routing relay.idle.B -> "
                "policy.pta_hold; live 4.60 bar left unused as a go signal.",
            ),
        ]
    )
    future = OrderedDict(
        [
            (
                "summary",
                "Wrong-REJECT held CX-4 at 0.00 t/h. Live string-A 4.60 bar LIVE was under "
                "the 6.00 bar cap; 6.80 bar was an IDLE twin, not live. 22 min crystal-size "
                "window missed (missed_window_s=1320). Correct gate was ACCEPT of the 2.8 t/h slurry.",
            ),
            (
                "state_delta",
                OrderedDict(
                    [
                        ("crystallizer", "held; slurry 0.00 t/h; live A still 4.60 bar < 6.00"),
                        ("idle_twin", "6.80 bar unused, still IDLE not a live PV"),
                        ("deck", "22 min crystal-size window missed"),
                        ("mission", "slurry deferred"),
                    ]
                ),
            ),
            (
                "surprises",
                [
                    "Live-first was the correct order and the live number was legal; the REJECT spent that win on the IDLE twin.",
                    "Delayed (missed_window_s=1320): WN-2 loses the 22 min crystal-size window; next window 5.8 h.",
                ],
            ),
            (
                "recovery",
                OrderedDict(
                    [
                        (
                            "correct_gate",
                            "ACCEPT the 2.8 t/h PTA slurry; leave 6.80 bar IDLE string-B to its own bank.",
                        ),
                        ("correct_quality", "LIVE"),
                        ("wrong_quality", "IDLE"),
                        (
                            "wrong_edit_applied",
                            OrderedDict([("slurry_tph", 0.0), ("hold", True)]),
                        ),
                        (
                            "cost",
                            "Missed 22 min crystal-size window (task/efficiency); live A never exceeded 4.60 bar (safety near-miss of a false hold).",
                        ),
                    ]
                ),
            ),
            (
                "race_result",
                OrderedDict(
                    [
                        ("winner", "pt.live.A (4.180 ms, 4.60 bar LIVE)"),
                        ("loser", "pt.idle.B (4.332 ms, 6.80 bar IDLE)"),
                        ("margin_us", 152),
                        (
                            "counterfactual_if_reversed",
                            "Idle-first by < 152 us would still be an IDLE twin, not live 6.80 bar; "
                            "a correct gate binds pt.live.A to pta_go either way. The wrong "
                            "REJECT spent the live win on the wrong string.",
                        ),
                    ]
                ),
            ),
            ("reward_inflection_t_us", 4920),
            (
                "reward_inflection_note",
                "Task, efficiency, and coherence drop at the wrong REJECT (4.920 ms, tick 4). "
                "The 22 min missed window is delayed surprise, not the inflection.",
            ),
            ("delayed_surprise_s", 1320.0),
            ("missed_window_s", 1320),
        ]
    )
    ras = raster_core(
        24,
        92,
        34,
        75,
        routing(
            "relay.idle.B",
            "policy.pta_hold",
            [
                ("relay.idle.B", "policy.pta_hold", 0.74),
                ("relay.live.A", "policy.pta_hold", 0.18),
            ],
            "acetylcholine",
            0.06,
            "string_cap_stdp; ACh tags the (wrong) pta_hold bind at the IDLE twin string",
        ),
        excerpt,
        extra=OrderedDict(
            [
                ("excerpt_source", "kernelized_events"),
                ("sim_scope", "none"),
                ("missed_window_s", 1320),
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
                    pop("pta_hold", 48, 0.50, 260.4, 4),
                    pop("pta_go", 48, 0.80, 6.5, 0),
                    pop("idle_ctx", 32, 0.55, 97.7, 1),
                ],
            ),
        ]
    )
    return OrderedDict(
        [
            ("id", "ttf-r66-347"),
            (
                "title",
                "WRONG-REJECT at Woad-Ness WN-2 / Crystallizer CX-4: live string-A 4.60 bar "
                "LIVE < 6.00 bar cap; supervisor treats 6.80 bar IDLE twin as live",
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
                    "Wrong-reject. Sidecar arithmetic 4.60 < 6.00 on live LIVE is true; REJECT bound "
                    "to IDLE twin. total -0.58 = -0.20 + -0.10 + -0.22 + -0.12 + 0.06.",
                ),
            ),
            ("raster", ras),
            ("gate_snn", gate),
            (
                "meta",
                meta_block(
                    "pta-crystallizer",
                    [
                        "reject",
                        "wrong-gate",
                        "idle-twin-string-as-live",
                        "sidecar-convictable",
                        "designed",
                    ],
                    "Teaches a probe that a correct live-first race can still be a wrong gate "
                    "when the REJECT binds an IDLE parallel-bank twin onto the crystallizer hold. "
                    "Convictable from quality IDs and caps without PTA physics.",
                    2,
                    supervisor_error_type="wrong-reject",
                ),
            ),
        ]
    )


def record_348():
    ticks = [
        tick(2680, 0.01, 0.05, 0.01, 0.01, 0.01),
        tick(5760, 0.02, 0.08, 0.02, 0.02, 0.01),
        tick(5931, 0.02, 0.07, 0.02, 0.02, 0.01),
        tick(6860, 0.03, 0.12, 0.04, 0.03, 0.02),
        tick(9020, 0.01, 0.05, 0.02, 0.01, 0.01),
        tick(480000000, 0.01, 0.03, 0.01, 0.01, 0.00),
    ]
    spikes = [
        spike("tc.bed.ctx", 1.380, 0.43),
        spike("rtd.bed.C", 2.680, 0.62),
        spike("ir.wall.glint", 4.180, 0.49),
        spike("rtd.bed.C", 5.760, 1.35),
        spike("ir.wall.glint", 5.931, 1.12),
        spike("ctrl.gate", 6.860, 1.03),
        spike("rtd.bed.C", 9.020, 0.77),
        spike("tc.bed.ctx", 13.200, 0.44),
        spike("ir.wall.glint", 17.100, 0.58),
        spike("ctrl.gate", 23.400, 0.81),
        spike("rtd.bed.C", 30.000, 0.54),
        spike("tc.bed.ctx", 36.600, 0.38),
        spike("ir.wall.glint", 39.100, 0.46),
    ]
    excerpt = independent_excerpt(66348, 108, 40000, 15, spike_avoid_us(spikes))
    state = OrderedDict(
        [
            (
                "description",
                "Reactor RX-5 is frozen on Grit-Staith GS-HIL's oxychlorination pad while a "
                "bed RTD reports 248 C against a 255 C light-off floor. A wall pyrometer, lit "
                "by the pad spectrum, still reads 271 C apparent. Bed-first latches REJECT hold; "
                "glint-first would commit a 4.2 t/h ethylene walk on an under-floor bed.",
            ),
            ("domain", "vcm-oxychlorination"),
            ("sim_or_real", "hil"),
            (
                "goal",
                "Do not walk ethylene unless bed >= 255 C; keep C2H4 0.0 t/h until the "
                "injected cold-packet drops.",
            ),
            ("t0_us", 1756850400000348),
            ("gate_latency_us", 1100),
            ("race_window_us", 380),
            ("race_window_rel_ms", [5.7, 6.08]),
            (
                "race",
                OrderedDict(
                    [
                        (
                            "contenders",
                            [
                                "rtd.bed.C 248 C",
                                "ir.wall.glint 271 C apparent",
                            ],
                        ),
                        (
                            "semantics",
                            "Bed-first latches REJECT hold 0.0 t/h; glint-first would commit "
                            "4.2 t/h on an apparent 271 C under-read of a cold-packet.",
                        ),
                        (
                            "window_derivation",
                            "380 us = one bed-RTD slot versus wall-IR integration on this "
                            "oxychlorination HIL bus.",
                        ),
                        (
                            "order_evidence_note",
                            "Margin 171 us vs combined jitter ~58 us (bed 26 + IR 32): 2.9x "
                            "over a 2.0x trust floor. Pad injects the wall 110-150 us before the "
                            "bed RTD (geometric lag, not a sensor fault); the apparent "
                            "271 C packet is still the loser in this 380 us window.",
                        ),
                    ]
                ),
            ),
            (
                "sensors",
                [
                    "bed RTD, 5 kHz burst, 26 us jitter",
                    "wall pyrometer, 200 Hz, 32 us jitter",
                    "HCl thermocouple (context)",
                    "HIL wall-spectrum monitor (context)",
                ],
            ),
            (
                "constraints",
                OrderedDict(
                    [
                        ("lightoff_floor_C", 255.0),
                        ("observed_bed_C", 248.0),
                        ("wall_apparent_C", 271.0),
                        ("proposed_c2h4_tph", 4.2),
                        ("wall_inject_lead_us", [110, 150]),
                    ]
                ),
            ),
            (
                "hil",
                OrderedDict(
                    [
                        ("pad", "Grit-Staith GS-HIL oxychlorination mockup"),
                        ("injected", "cold-bed packet + wall-spectrum"),
                        (
                            "note",
                            "Hardware-in-the-loop oxychlorination. Invented plant; not a live VCM reactor.",
                        ),
                    ]
                ),
            ),
            (
                "episode_steps",
                [
                    "1. Reactor RX-5 on the GS-HIL pad; ethylene 4.2 t/h armed.",
                    "2. Wall injected 110-150 us before bed RTD sees the cold packet.",
                    "3. HCl precursor at 1.380 ms.",
                    "4. Race window [5.700, 6.080] ms.",
                    "5. rtd.bed.C 248 C at 5.760 ms (winner).",
                    "6. ir.wall.glint 271 C at 5.931 ms (loser by 171 us).",
                    "7. Gate at 6.860 ms: REJECT hold 0.0 t/h; do not walk 4.2 t/h.",
                    "8. Bed remains under floor this cycle; light-off floor held.",
                    "9. Seed recycle queued on the pad.",
                    "10. Delayed (abort_s=480): 8 min pad retune and wall-spectrum retune.",
                ],
            ),
        ]
    )
    proposed = OrderedDict(
        [
            ("name", "walk_c2_42"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("c2h4_tph", 4.2),
                        ("hold", False),
                        ("wall_authoritative", True),
                    ]
                ),
            ),
            (
                "evidence",
                OrderedDict(
                    [
                        ("bed_C", 248.0),
                        ("lightoff_floor_C", 255.0),
                        ("wall_apparent_C", 271.0),
                        ("race_margin_us", 171),
                        ("combined_jitter_us", 58),
                        ("abort_s", 480),
                    ]
                ),
            ),
            (
                "basis",
                "Planner proposes 4.2 t/h ethylene because wall apparent 271 C looks "
                "over the 255 C floor, treating bed 248 C as a noisy sheath echo.",
            ),
        ]
    )
    safety = OrderedDict(
        [
            ("decision", "REJECT"),
            ("correctness", "correct"),
            (
                "rationale",
                "Bed 248 C is under the 255 C light-off floor. Wall apparent 271 C is a HIL "
                "wall under-read of a cold packet, not a clearance. REJECT: hold 0.0 t/h; do "
                "not commit 4.2 t/h across the oxychlorination bed.",
            ),
            (
                "constraint_checked",
                OrderedDict(
                    [
                        (
                            "bed_C",
                            OrderedDict(
                                [
                                    ("floor", 255.0),
                                    ("observed_bed", 248.0),
                                    ("wall_apparent", 271.0),
                                ]
                            ),
                        ),
                        (
                            "c2h4_tph",
                            OrderedDict(
                                [
                                    ("proposed", 4.2),
                                    ("executed", 0.0),
                                ]
                            ),
                        ),
                        (
                            "order_evidence",
                            OrderedDict(
                                [
                                    ("margin_us", 171),
                                    ("combined_jitter_us", 58),
                                    ("ratio", 2.95),
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
            ("name", "hold_for_lightoff"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("c2h4_tph", 0.0),
                        ("hold", True),
                        ("wall_authoritative", False),
                    ]
                ),
            ),
            (
                "gate_effect",
                "REJECT: hold 0.0 t/h; 4.2 t/h ethylene cancelled. Bed 248 < 255 floor.",
            ),
        ]
    )
    future = OrderedDict(
        [
            (
                "summary",
                "Correct REJECT held Reactor RX-5 at 0.0 t/h. Bed under floor this cycle; "
                "light-off floor held. Wall apparent was not treated as a bed clearance.",
            ),
            (
                "state_delta",
                OrderedDict(
                    [
                        ("reactor", "held; C2H4 0.0 t/h"),
                        ("bed", "still under 255 C this cycle"),
                        ("wall_ir", "271 C unused as clearance"),
                        ("mission", "ethylene walk deferred"),
                    ]
                ),
            ),
            (
                "surprises",
                [
                    "Geometric lag: wall was injected 110-150 us before the bed RTD, yet bed still won the 380 us race.",
                    "Delayed (abort_s=480): pad policy update forbids treating wall apparent as a bed substitute after an 8 min retune.",
                ],
            ),
            (
                "race_result",
                OrderedDict(
                    [
                        ("winner", "rtd.bed.C (5.760 ms, 248 C)"),
                        ("loser", "ir.wall.glint (5.931 ms, 271 C apparent)"),
                        ("margin_us", 171),
                        (
                            "counterfactual_if_reversed",
                            "Glint-first by < 171 us inside the 380 us window would have committed "
                            "4.2 t/h with bed 248 < 255 floor. Order, not amplitude, selected the hold.",
                        ),
                    ]
                ),
            ),
            ("reward_inflection_t_us", 6860),
            (
                "reward_inflection_note",
                "Safety and coherence step up at the REJECT gate (6.860 ms, tick 4) as the hold "
                "locks in over the illegal ethylene walk.",
            ),
            ("delayed_surprise_s", 480.0),
            ("abort_s", 480),
        ]
    )
    ras = raster_core(
        40,
        108,
        21,
        91,
        routing(
            "thalamic-relay.vcm-bed",
            "spikenaut.policy.c2-hold",
            [
                ("relay.rtd.bed", "policy.c2_hold", 0.69),
                ("relay.ir.wall", "policy.c2_commit", 0.27),
                ("relay.tc.bed", "policy.c2_hold", 0.11),
            ],
            "dopamine",
            0.09,
            "lightoff_stdp; DA at bed win (5.760 ms) tags c2_hold over c2_commit",
        ),
        excerpt,
        extra=OrderedDict(
            [
                ("excerpt_source", "kernelized_events"),
                ("sim_scope", "none"),
                ("abort_s", 480),
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
                    pop("c2_hold", 52, 0.50, 253.0, 5),
                    pop("c2_commit", 40, 0.50, 65.8, 1),
                    pop("bed_veto", 32, 0.75),
                ],
            ),
        ]
    )
    return OrderedDict(
        [
            ("id", "ttf-r66-348"),
            (
                "title",
                "Grit-Staith GS-HIL / Reactor RX-5: bed 248 C beats wall 271; "
                "correct REJECT holds the oxychlorination ethylene walk",
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
                    "Correct REJECT. Bed under floor; wall under-read unused as clearance. "
                    "total +0.78 = 0.10 + 0.40 + 0.12 + 0.10 + 0.06.",
                ),
            ),
            ("raster", ras),
            ("gate_snn", gate),
            (
                "meta",
                meta_block(
                    "vcm-oxychlorination",
                    [
                        "reject",
                        "hil-zone",
                        "bed-vs-wall",
                        "lightoff-floor",
                        "hil",
                    ],
                    "Teaches that a HIL wall under-read can lose to bed RTD inside a "
                    "380 us window; reversing 171 us would have selected an illegal ethylene walk.",
                    3,
                ),
            ),
        ]
    )


def record_349():
    ticks = [
        tick(3040, 0.04, 0.03, 0.02, 0.01, 0.00),
        tick(6840, 0.08, 0.07, 0.03, 0.02, 0.01),
        tick(7058, 0.05, 0.05, 0.02, 0.02, 0.01),
        tick(7280, 0.11, 0.09, 0.04, 0.03, 0.01),
        tick(9480, 0.04, 0.04, 0.02, 0.01, 0.01),
        tick(360000000, 0.02, 0.02, 0.01, 0.01, 0.00),
    ]
    spikes = [
        spike("pt.regen.ctx", 1.540, 0.42),
        spike("an.cl.ppm", 3.040, 0.59),
        spike("ir.regen.glint", 4.980, 0.48),
        spike("an.cl.ppm", 6.840, 1.31),
        spike("ir.regen.glint", 7.058, 1.09),
        spike("ctrl.gate", 7.280, 0.96),
        spike("an.cl.ppm", 9.480, 0.73),
        spike("pt.regen.ctx", 13.700, 0.45),
        spike("ir.regen.glint", 18.200, 0.57),
        spike("ctrl.gate", 22.500, 0.80),
        spike("an.cl.ppm", 26.700, 0.51),
        spike("pt.regen.ctx", 29.200, 0.38),
    ]
    excerpt = independent_excerpt(66349, 64, 30000, 13, spike_avoid_us(spikes))
    state = OrderedDict(
        [
            (
                "description",
                "Regen-Deck RG-2 at Flake-Howe FH-5 still holds 18 ppm chloride while a 12 ppm "
                "CCR cap is already live on the gas. A regen IR on the same canopy still claims "
                "6 ppm cool-glint. Analyzer-first latches a chloride clamp; glint-first would "
                "keep 18 ppm into a close-out surge.",
            ),
            ("domain", "ccr-platformer"),
            ("sim_or_real", "designed"),
            (
                "goal",
                "Step RG-2 only if chloride <= 12 ppm; otherwise clamp injection so the "
                "oxychlorination of the coke is not made at 18 ppm.",
            ),
            ("t0_us", 1756850400000349),
            ("gate_latency_us", 440),
            ("race_window_us", 520),
            ("race_window_rel_ms", [6.75, 7.27]),
            (
                "race",
                OrderedDict(
                    [
                        (
                            "contenders",
                            [
                                "an.cl.ppm 18 ppm",
                                "ir.regen.glint 6 ppm cool-glint",
                            ],
                        ),
                        (
                            "semantics",
                            "Analyzer-first latches chloride clamp 18 -> 9 ppm; glint-first keeps "
                            "18 ppm on a false-cool regen IR.",
                        ),
                        (
                            "window_derivation",
                            "520 us = one 2 kHz chloride-analyzer sample versus regen-IR decode on "
                            "this CCR bus.",
                        ),
                        (
                            "order_evidence_note",
                            "Margin 218 us vs combined jitter ~71 us (Cl 33 + regen 38): 3.1x over "
                            "a 2.0x trust floor. Reversing order by < 218 us inside the 520 us "
                            "window would have kept 18 ppm into a 12 ppm cap miss.",
                        ),
                    ]
                ),
            ),
            (
                "sensors",
                [
                    "gas chloride analyzer, 2 kHz, 33 us jitter",
                    "regen IR camera, 200 Hz, 38 us jitter",
                    "regen-air PT (context)",
                    "lock-hopper load cell (context)",
                ],
            ),
            (
                "constraints",
                OrderedDict(
                    [
                        ("cl_cap_ppm", 12.0),
                        ("observed_cl_ppm", 18.0),
                        ("proposed_cl_ppm", 18.0),
                        ("regen_glint_ppm", 6.0),
                    ]
                ),
            ),
            (
                "episode_steps",
                [
                    "1. Regen-Deck indexed onto FH-5 CCR; RG-2 armed at 18 ppm chloride.",
                    "2. Regen IR reports 6 ppm cool-glint; analyzer already sees 18 ppm.",
                    "3. Regen-PT precursor at 1.540 ms.",
                    "4. Race window [6.750, 7.270] ms.",
                    "5. an.cl.ppm 18 at 6.840 ms (winner).",
                    "6. ir.regen.glint 6 ppm at 7.058 ms (loser by 218 us).",
                    "7. Gate at 7.280 ms: MODIFY chloride 18 -> 9 ppm.",
                    "8. Injection applies; next-sample Cl 10.4 ppm < 12 cap.",
                    "9. Catalyst occupies; next lock-hopper queued.",
                    "10. Delayed (ccr_reseq_s=360): dispatcher resequences the following hopper +6 min.",
                ],
            ),
        ]
    )
    proposed = OrderedDict(
        [
            ("name", "cl_18"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("cl_ppm", 18.0),
                        ("n2_tph", 8.4),
                        ("regen_id", 2),
                    ]
                ),
            ),
            (
                "evidence",
                OrderedDict(
                    [
                        ("cl_ppm", 18.0),
                        ("cl_cap_ppm", 12.0),
                        ("regen_cool", True),
                        ("race_margin_us", 218),
                        ("combined_jitter_us", 71),
                        ("ccr_reseq_s", 360),
                    ]
                ),
            ),
            (
                "basis",
                "Planner proposes 18 ppm chloride because the regen IR claims the canopy "
                "is cool, treating analyzer 18 ppm as a sidelobe.",
            ),
        ]
    )
    safety = OrderedDict(
        [
            ("decision", "MODIFY"),
            ("correctness", "correct"),
            (
                "rationale",
                "Chloride 18 ppm won by 218 us, so the pulse is inside the 12 ppm CCR cap. "
                "Regen-IR cool-glint is not a gas chloride. MODIFY: Cl 18 -> 9 ppm. "
                "A full REJECT (kill the hopper) is not indicated: 9 ppm is a legal catch-and-pass.",
            ),
            (
                "constraint_checked",
                OrderedDict(
                    [
                        (
                            "cl_ppm",
                            OrderedDict(
                                [
                                    ("cap", 12.0),
                                    ("observed", 18.0),
                                    ("regen_cool", True),
                                    ("observed_after_clamp", 10.4),
                                ]
                            ),
                        ),
                        (
                            "cl_ppm_set",
                            OrderedDict(
                                [
                                    ("proposed", 18.0),
                                    ("clamped", 9.0),
                                ]
                            ),
                        ),
                        (
                            "order_evidence",
                            OrderedDict(
                                [
                                    ("margin_us", 218),
                                    ("combined_jitter_us", 71),
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
            ("name", "clamped_cl_9"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("cl_ppm", 9.0),
                        ("n2_tph", 8.4),
                        ("regen_id", 2),
                    ]
                ),
            ),
            (
                "gate_effect",
                "MODIFY: chloride 18 -> 9 ppm. Process-correct vs the 12 ppm CCR cap.",
            ),
        ]
    )
    future = OrderedDict(
        [
            (
                "summary",
                "Correct MODIFY held RG-2 at 9 ppm. Next-sample chloride 10.4 ppm under the "
                "12 ppm cap. Regen 6 ppm cool-glint was not treated as a gas clearance.",
            ),
            (
                "state_delta",
                OrderedDict(
                    [
                        ("chloride", "clamped 18 -> 9 ppm"),
                        ("analyzer", "10.4 ppm < 12 cap after clamp"),
                        ("ir", "6 ppm unused as clearance"),
                        ("mission", "hopper completed under cap"),
                    ]
                ),
            ),
            (
                "surprises",
                [
                    "Regen-IR cool-glint lagged the chloride pulse by 218 us; order, not amplitude, selected the clamp.",
                    "Delayed (ccr_reseq_s=360): dispatcher resequences the following hopper +6 min. Not a safety inflection.",
                ],
            ),
            (
                "race_result",
                OrderedDict(
                    [
                        ("winner", "an.cl.ppm (6.840 ms, 18 ppm)"),
                        ("loser", "ir.regen.glint (7.058 ms, 6 ppm)"),
                        ("margin_us", 218),
                        (
                            "counterfactual_if_reversed",
                            "Glint-first by < 218 us inside the 520 us window would have kept "
                            "18 ppm into a 12 ppm cap miss. The MODIFY is the correct process "
                            "either way once the analyzer is bound.",
                        ),
                    ]
                ),
            ),
            ("reward_inflection_t_us", 7280),
            (
                "reward_inflection_note",
                "Task and safety step up at the MODIFY gate (7.280 ms, tick 4). Tick 6 is "
                "ccr_reseq_s=360.",
            ),
            ("delayed_surprise_s", 360.0),
            ("ccr_reseq_s", 360),
        ]
    )
    ras = raster_core(
        30,
        64,
        42,
        81,
        routing(
            "thalamic-relay.ccr-cl",
            "spikenaut.policy.cl-clamp",
            [
                ("relay.an.cl", "policy.cl_clamp", 0.64),
                ("relay.ir.regen", "policy.glint_hold", 0.29),
                ("relay.pt.regen", "policy.cl_clamp", 0.12),
            ],
            "serotonin",
            0.07,
            "chloride_stdp; 5-HT at analyzer win (6.840 ms) tags cl_clamp over glint_hold",
        ),
        excerpt,
        extra=OrderedDict(
            [
                ("excerpt_source", "kernelized_events"),
                ("sim_scope", "none"),
                ("ccr_reseq_s", 360),
            ]
        ),
    )
    gate = OrderedDict(
        [
            ("decision_window_ms", 0.52),
            ("decision", "MODIFY"),
            (
                "populations",
                [
                    pop("cl_clamp", 30, 0.50, 256.4, 4),
                    pop("glint_hold", 30, 0.50, 64.1, 1),
                    pop("cl_veto", 20, 0.75),
                ],
            ),
        ]
    )
    return OrderedDict(
        [
            ("id", "ttf-r66-349"),
            (
                "title",
                "Flake-Howe FH-5 / Regen-Deck RG-2: chloride 18 ppm beats regen cool-glint; "
                "correct MODIFY clamps Cl 18 -> 9 ppm",
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
                    "Correct MODIFY. Chloride over cap; regen cool-glint unused. total +0.92 = "
                    "0.34 + 0.30 + 0.14 + 0.10 + 0.04.",
                ),
            ),
            ("raster", ras),
            ("gate_snn", gate),
            (
                "meta",
                meta_block(
                    "ccr-platformer",
                    [
                        "modify",
                        "designed",
                        "cl-vs-regen",
                        "ccr-cap",
                    ],
                    "Teaches that a cool-glint regen IR can lose to a legal chloride analyzer "
                    "inside a 520 us window; reversing 218 us would have kept an illegal 18 ppm injection.",
                    4,
                ),
            ),
        ]
    )


def record_350():
    ticks = [
        tick(1580, 0.05, 0.04, 0.02, 0.01, 0.01),
        tick(3740, 0.10, 0.08, 0.04, 0.03, 0.02),
        tick(3858, 0.06, 0.05, 0.03, 0.02, 0.01),
        tick(4300, 0.14, 0.10, 0.05, 0.04, 0.02),
        tick(6120, 0.06, 0.04, 0.02, 0.01, 0.01),
        tick(300000000, 0.03, 0.03, 0.02, 0.01, 0.01),
    ]
    spikes = [
        spike("pt.liquor.ctx", 0.700, 0.39),
        spike("rtd.liquor.C", 1.580, 0.57),
        spike("ir.tower.glint", 2.400, 0.48),
        spike("rtd.liquor.C", 3.740, 1.29),
        spike("ir.tower.glint", 3.858, 1.10),
        spike("ctrl.gate", 4.300, 0.97),
        spike("rtd.liquor.C", 6.120, 0.76),
        spike("ir.tower.glint", 8.800, 0.61),
        spike("ctrl.gate", 12.200, 0.83),
        spike("pt.liquor.ctx", 15.900, 0.41),
        spike("rtd.liquor.C", 19.400, 0.54),
        spike("ir.tower.glint", 21.200, 0.46),
    ]
    excerpt = independent_excerpt(66350, 80, 22000, 12, spike_avoid_us(spikes))
    state = OrderedDict(
        [
            (
                "description",
                "Carbonating-Tower CT-1 at Brash-Gill BG-3 is already at 38.2 C liquor while a "
                "tower-top pyrometer glint still reports 61 against a 52 C scale cap that the "
                "liquor RTD has not crossed. Liquor-first should ACCEPT the already-legal "
                "6.4 t/h brine; glint-first would hold a legal Solvay tower on lighting.",
            ),
            ("domain", "soda-ash-solvay"),
            ("sim_or_real", "simulated"),
            (
                "goal",
                "Run CT-1 when liquor RTD is <= 52 C; do not spend a tower-top pyrometer "
                "glint on a hold.",
            ),
            ("t0_us", 1756850400000350),
            ("gate_latency_us", 560),
            ("race_window_us", 240),
            ("race_window_rel_ms", [3.7, 3.94]),
            (
                "race",
                OrderedDict(
                    [
                        (
                            "contenders",
                            [
                                "rtd.liquor.C 38.2 C",
                                "ir.tower.glint 61 lighting",
                            ],
                        ),
                        (
                            "semantics",
                            "Liquor-first ACCEPTS the already-legal 38.2 C feed. Glint-first "
                            "would REJECT a legal Solvay tower on a 61 C lighting.",
                        ),
                        (
                            "window_derivation",
                            "240 us = one liquor-RTD sample minus tower-pyrometer integration on "
                            "this Solvay simulation.",
                        ),
                        (
                            "order_evidence_note",
                            "Margin 118 us vs combined jitter ~50 us (RTD 22 + IR 28): 2.4x over "
                            "a 2.0x trust floor. Reversing order by < 118 us inside the 240 us "
                            "window would have invented a scale hold on an already-legal 38.2 C liquor.",
                        ),
                    ]
                ),
            ),
            (
                "sensors",
                [
                    "liquor RTD, 2 kHz, 22 us jitter",
                    "tower-top pyrometer, 200 Hz, 28 us jitter",
                    "liquor PT (context)",
                    "CO2 orifice (context)",
                ],
            ),
            (
                "constraints",
                OrderedDict(
                    [
                        ("scale_cap_C", 52.0),
                        ("observed_liquor_C", 38.2),
                        ("tower_glint_C", 61.0),
                        ("proposed_brine_t_h", 6.4),
                    ]
                ),
            ),
            (
                "episode_steps",
                [
                    "1. CT-1 seeded; liquor at 38.2 C under 52 scale cap.",
                    "2. Tower-top pyrometer glint 61 from lighting, not bicarbonate scale.",
                    "3. Liquor-PT precursor at 0.700 ms.",
                    "4. Race window [3.700, 3.940] ms.",
                    "5. rtd.liquor.C 38.2 C at 3.740 ms (winner).",
                    "6. ir.tower.glint 61 at 3.858 ms (loser by 118 us).",
                    "7. Gate at 4.300 ms: ACCEPT 6.4 t/h as proposed.",
                    "8. Brine executes; liquor remains 38.2 C < 52.",
                    "9. Charge emptied; next pass queued.",
                    "10. Delayed (survey_hold_s=300): 5 min bicarbonate survey. Not a safety inflection.",
                ],
            ),
        ]
    )
    proposed = OrderedDict(
        [
            ("name", "brine_64"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("brine_t_h", 6.4),
                        ("hold", False),
                        ("liquor_kPa", 22.0),
                    ]
                ),
            ),
            (
                "evidence",
                OrderedDict(
                    [
                        ("liquor_C", 38.2),
                        ("scale_cap_C", 52.0),
                        ("tower_glint_C", 61.0),
                        ("race_margin_us", 118),
                        ("combined_jitter_us", 50),
                        ("survey_hold_s", 300),
                    ]
                ),
            ),
            (
                "basis",
                "Planner proposes 6.4 t/h because liquor RTD 38.2 C is under the 52 C "
                "scale cap; tower 61 C is lighting, not scale.",
            ),
        ]
    )
    safety = OrderedDict(
        [
            ("decision", "ACCEPT"),
            ("correctness", "correct"),
            (
                "rationale",
                "Liquor RTD 38.2 C is under the 52 C scale cap. Tower 61 C is a lighting "
                "glint, not bicarbonate load. ACCEPT the proposed 6.4 t/h; do not invent a hold.",
            ),
            (
                "constraint_checked",
                OrderedDict(
                    [
                        (
                            "liquor_C",
                            OrderedDict(
                                [
                                    ("cap", 52.0),
                                    ("observed", 38.2),
                                    ("tower_glint_C", 61.0),
                                ]
                            ),
                        ),
                        (
                            "brine_t_h",
                            OrderedDict(
                                [
                                    ("proposed", 6.4),
                                    ("executed", 6.4),
                                ]
                            ),
                        ),
                        (
                            "order_evidence",
                            OrderedDict(
                                [
                                    ("margin_us", 118),
                                    ("combined_jitter_us", 50),
                                    ("ratio", 2.36),
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
            ("name", "brine_64"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("brine_t_h", 6.4),
                        ("hold", False),
                        ("liquor_kPa", 22.0),
                    ]
                ),
            ),
            (
                "gate_effect",
                "ACCEPT: proposed 6.4 t/h executed unchanged. Liquor 38.2 C < 52; tower glint unused.",
            ),
        ]
    )
    future = OrderedDict(
        [
            (
                "summary",
                "Correct ACCEPT ran CT-1 at 38.2 C liquor. Tower 61 C was lighting, not scale. "
                "The proposal was already legal; reversing 118 us would have invented a hold.",
            ),
            (
                "state_delta",
                OrderedDict(
                    [
                        ("tower", "brine executed; liquor 38.2 C < 52"),
                        ("tower_ir", "61 C glint unused as scale"),
                        ("liquor", "held 22.0 kPa through the pass"),
                        ("mission", "brine committed"),
                    ]
                ),
            ),
            (
                "surprises",
                [
                    "Tower 61 C is a legal lighting glint, not a high-liquor alarm; liquor-first discarded a false hold.",
                    "Delayed (5 min / survey_hold_s=300): bicarbonate survey. Not a safety inflection.",
                ],
            ),
            (
                "race_result",
                OrderedDict(
                    [
                        ("winner", "rtd.liquor.C (3.740 ms, 38.2 C)"),
                        ("loser", "ir.tower.glint (3.858 ms, 61 lighting)"),
                        ("margin_us", 118),
                        (
                            "counterfactual_if_reversed",
                            "Glint-first by < 118 us inside the 240 us window would have held "
                            "the Solvay tower on a false high-liquor story. The proposal was already "
                            "under the 52 cap, so the correct gate is still ACCEPT.",
                        ),
                    ]
                ),
            ),
            ("reward_inflection_t_us", 4300),
            (
                "reward_inflection_note",
                "Task and safety step up at the ACCEPT gate (4.300 ms, tick 4). Tick 6 is "
                "survey_hold_s=300.",
            ),
            ("delayed_surprise_s", 300.0),
            ("survey_hold_s", 300),
        ]
    )
    ras = raster_core(
        22,
        80,
        34,
        60,
        routing(
            "thalamic-relay.liquor-rtd",
            "spikenaut.policy.brine-accept",
            [
                ("relay.rtd.liquor", "policy.brine_go", 0.62),
                ("relay.ir.tower", "policy.glint_hold", 0.28),
                ("relay.pt.liquor", "policy.brine_go", 0.14),
            ],
            "adenosine",
            0.16,
            "pre_post_stdp; adenosine at liquor win (3.740 ms) opens 160 ms eligibility covering the 4.300 ms accept",
        ),
        excerpt,
        extra=OrderedDict(
            [
                ("excerpt_source", "kernelized_events"),
                ("sim_scope", "none"),
                ("survey_hold_s", 300),
            ]
        ),
    )
    gate = OrderedDict(
        [
            ("decision_window_ms", 0.24),
            ("decision", "ACCEPT"),
            (
                "populations",
                [
                    pop("brine_go", 42, 0.50, 297.6, 3),
                    pop("glint_hold", 42, 0.50, 19.8, 0),
                    pop("scale_veto", 20, 0.80),
                ],
            ),
        ]
    )
    return OrderedDict(
        [
            ("id", "ttf-r66-350"),
            (
                "title",
                "Brash-Gill BG-3 / Carbonating-Tower CT-1: liquor 38.2 C beats tower glint; "
                "correct ACCEPT of an already-legal 6.4 t/h (total +1.16)",
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
                    "Correct ACCEPT. Liquor 38.2 C < 52; tower glint is lighting, not scale. "
                    "total +1.16 = 0.44 + 0.34 + 0.18 + 0.12 + 0.08.",
                ),
            ),
            ("raster", ras),
            ("gate_snn", gate),
            (
                "meta",
                meta_block(
                    "soda-ash-solvay",
                    [
                        "accept",
                        "simulated-lighting",
                        "liquor-vs-tower",
                        "brine",
                        "simulated",
                    ],
                    "Teaches that a tower lighting glint can lose to a legal liquor RTD "
                    "inside a 240 us window; reversing 118 us would have invented a hold on an "
                    "already-legal brine feed.",
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
            if str(k).lower() in THOUGHT_KEYS or str(k).lower() in {
                "chain_of_thought",
                "hidden_reasoning",
            }:
                found.append(p)
            found.extend(walk_keys(v, p))
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            found.extend(walk_keys(v, f"{path}[{i}]"))
    return found


def prior_descriptions():
    descs = []
    for path in sorted(Path("/tmp").glob("ttf-r*/batch-r*.jsonl")):
        if path.parent.name == "ttf-r66":
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except OSError:
            continue
        for line in text.splitlines():
            if not line.strip():
                continue
            rec = json.loads(line)
            d = (rec.get("state") or {}).get("description")
            if isinstance(d, str):
                descs.append(d)
    return descs


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
    jprior = 0.0
    for d in prior_descriptions():
        for mine in descs:
            jprior = max(jprior, jaccard(d, mine))
    if jprior >= 0.4:
        issues.append(f"prior Jaccard {jprior:.3f}")
    domains = [r["state"]["domain"] for r in records]
    if tuple(domains) != THIS_DOMAINS:
        issues.append(f"domain set {domains}")
    if set(domains) & BANNED_DOMAINS:
        issues.append(f"banned domains {set(domains) & BANNED_DOMAINS}")
    occ_d, occ_p = harvest_occupancy()
    if set(domains) & occ_d:
        issues.append(f"live occupancy collision {set(domains) & occ_d}")
    blob_all = "\n".join(json.dumps(r) for r in records)
    for plant in THIS_PLANTS:
        if plant not in blob_all:
            issues.append(f"missing plant {plant}")
        if plant in occ_p:
            issues.append(f"restacked occupancy plant {plant}")
    for frag in BANNED_PLANT_FRAGMENTS:
        if frag in blob_all:
            issues.append(f"restacked plant {frag}")
    wrong = [
        r
        for r in records
        if r["safety_decision"].get("correctness") == "incorrect"
        or r["meta"].get("supervisor_error_type")
    ]
    if len(wrong) != 1 or wrong[0]["id"] != "ttf-r66-347":
        issues.append(f"wrong-gate set {[w['id'] for w in wrong]}")
    if wrong and wrong[0]["meta"].get("supervisor_error_type") != "wrong-reject":
        issues.append("expected wrong-reject")
    if any(r["state"]["sim_or_real"] == "real" for r in records):
        issues.append("sim_or_real=real")
    hil = [r["id"] for r in records if r["state"]["sim_or_real"] == "hil"]
    if hil != ["ttf-r66-348"]:
        issues.append(f"hil set {hil}")
    decisions = [r["safety_decision"]["decision"] for r in records]
    if decisions.count("ACCEPT") != 1 or decisions.count("MODIFY") != 2 or decisions.count("REJECT") != 2:
        issues.append(f"gate mix {decisions}")
    if [r["id"] for r in records] != IDS:
        issues.append(f"ids {[r['id'] for r in records]}")
    for rec in records:
        blob = json.dumps(rec)
        if "training_ready" in blob:
            issues.append(f"{rec['id']} training_ready present")
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
        overlap = excerpt_vs_spikes(rec)
        if rec["id"] == "ttf-r66-346":
            if rec["raster"].get("excerpt_source") != "independent_lif":
                issues.append("346 missing independent_lif")
            if rec["future_outcome"]["reward_inflection_t_us"] > rec["raster"]["window_ms"] * 1000:
                issues.append("346 inflection outside window")
            if rec["reward_components"]["total"] >= 0:
                issues.append("346 partnered-neg total not negative")
        elif overlap >= 0.8:
            issues.append(f"{rec['id']} excerpt overlap {overlap:.2f}")
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
        if rec["meta"]["round"] != 66:
            issues.append(f"{rec['id']} meta.round")
        if rec["meta"]["rights"]["intended_use"] != "research_only":
            issues.append(f"{rec['id']} rights")
        if rec["meta"]["rights"]["linear_issue"] != "RM-793":
            issues.append(f"{rec['id']} RM-793")
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
        exec_p = rec["executed_action"]["parameters"]
        prop_p = rec["proposed_action"]["parameters"]
        if rec["safety_decision"]["decision"] == "ACCEPT" and exec_p != prop_p:
            issues.append(f"{rec['id']} ACCEPT params differ")
        dw_s = rec["gate_snn"]["decision_window_ms"] / 1000.0
        for popu in rec["gate_snn"]["populations"]:
            if "mean_rate_hz" in popu:
                exp = round(popu["neurons"] * popu["mean_rate_hz"] * dw_s)
                if abs(popu["spikes"] - exp) > 1:
                    issues.append(
                        f"{rec['id']} gate_snn {popu['name']} spikes {popu['spikes']} vs {exp}"
                    )
        if not (8 <= len(rec["raster"]["excerpt"]) <= 16):
            issues.append(f"{rec['id']} excerpt n={len(rec['raster']['excerpt'])}")
        if rec["state"]["sim_or_real"] not in {"designed", "simulated", "hil"}:
            issues.append(f"{rec['id']} provenance")
        table_tos = {row["to"] for row in rec["raster"]["routing"]["table"]}
        if rec["id"] == "ttf-r66-347":
            if "policy.pta_go" in table_tos:
                issues.append("347 routing has pta_go")
            if "policy.pta_hold" not in table_tos:
                issues.append("347 missing pta_hold routing")
        win_ms = rec["raster"]["window_ms"]
        if not (20 <= win_ms <= 50):
            issues.append(f"{rec['id']} window_ms {win_ms}")
        for item in rec["raster"]["excerpt"]:
            if not (0 <= item["t_us"] <= win_ms * 1000):
                issues.append(f"{rec['id']} excerpt t_us {item['t_us']}")
            if not (0 <= item["neuron_id"] < rec["raster"]["neurons"]):
                issues.append(f"{rec['id']} neuron_id {item['neuron_id']}")
    return issues, jmax, jprior


def notes_text(jmax: float, jprior: float) -> str:
    return f"""# Thalamic Trajectory Factory — NOTES-r66

- Factory: `thalamic-trajectory-factory`
- Run label: `2026-09-02-final-heavy`
- Generator: `grok-4.6`
- Channel: SuperGrok Heavy consumer chat (RM-793 research-only)
- Quota: 5
- Quality: Q=5
- IDs: `ttf-r66-346` … `ttf-r66-350`
- Domains this batch: `maleic-anhydride-bed`, `pta-crystallizer`, `vcm-oxychlorination`, `ccr-platformer`, `soda-ash-solvay`

These five domain slugs sit outside the prompt 8-pool and outside staged r13–r65 occupancy (jsonl + generator SoT, including r50 DTB/merox, r54 Kroll/alumina-calciner, r55 Sendzimir-Z/flexo, r62 Sohio/AOD/OPP). All five plants are invented. Do not restack prior TTF plants (Marrow-Dock, Vesper-Lattice, Brine-Well, Saddle-Arc, Ashlar-Gait, Thoria-Kettle, Nitrid-Fell, Riser-Wold, Crepe-Noll, Zinc-Fen, Sponge-Holt, Gibbsite-Howe, Tungstate-Keld). Skarn-Holt / Woad-Ness / Grit-Staith / Flake-Howe / Brash-Gill are this round only.

## Batch map

| id | domain | decision | correctness | sim_or_real | total | edge |
|----|--------|----------|-------------|-------------|-------|------|
| ttf-r66-346 | maleic-anhydride-bed | MODIFY | correct | designed | **−0.46** | process-correct air clamp; tube-sheet gasket blow inside 42 ms raster; independent LIF |
| ttf-r66-347 | pta-crystallizer | REJECT | **incorrect (wrong-reject / idle-twin-string-as-live)** | designed | −0.58 | live A 4.60 bar LIVE < 6.00 cap; supervisor treats 6.80 bar IDLE twin as live |
| ttf-r66-348 | vcm-oxychlorination | REJECT | correct | hil | +0.78 | bed 248 C beats wall 271; hold, do not walk ethylene |
| ttf-r66-349 | ccr-platformer | MODIFY | correct | designed | +0.92 | Cl 18 ppm vs regen cool-glint; clamp 18 → 9 ppm |
| ttf-r66-350 | soda-ash-solvay | ACCEPT | correct | simulated | +1.16 | liquor 38.2 C vs tower glint 61; proposed 6.4 t/h already legal |

Gate mix: 1 ACCEPT, 2 MODIFY, 1 correct REJECT, 1 incorrect REJECT (wrong-reject). Provenance: designed×3, simulated×1, hil×1 (Grit-Staith GS-HIL oxychlorination mockup). Intra-batch Jaccard on `state.description` {jmax:.3f} (max vs prior staged {jprior:.3f}).

## Wrong-reject

**ttf-r66-347** is the mandated incorrect gate (`safety_decision.correctness=incorrect`, `meta.supervisor_error_type=wrong-reject`). Alternate vs odd rounds: even rounds host wrong-reject (r12/r14/…/r54/r66); odd rounds host wrong-modify. Do not emit a wrong-ACCEPT. Error *class* is **idle-twin-string-as-live / parallel-bank mixup**, not r16/r28 wrong-stage/drum, not r32 stale-peak-hold, not r34 wrong-bus, not r36 leftover-bar, not r38 loop-test-inject, not r40 SP-echo-as-PV, not r42 leftover-SP-as-trip, not r44 wrong-unit-shadow, not r50 raw-mA-as-EU, not r52 gauge-vs-absolute, not r54 bad-quality-sub-as-live.

Woad-Ness WN-2 / Crystallizer CX-4 reads live string-A `4.60 bar` LIVE against a **6.00 bar** mother-liquor cap. Isolated idle string-B still reports **6.80 bar** with quality **IDLE**. Sidecar arithmetic `4.60 < 6.00` is true. A weak supervisor treats “the PTA bank” as one string, REJECTs the 2.8 t/h slurry, and holds CX-4. Convictable without PTA physics: `evidence.live_bar < evidence.live_cap_bar`, `live_quality == LIVE`, `idle_quality == IDLE`, `idle_is_live == false`, `executed_action` sets `slurry_tph=0` without a live over-cap, `raster.routing.table` sends `relay.idle.B` → `policy.pta_hold` (weight 0.74) with no positive weight to `policy.pta_go`, and `gate_snn` has `pta_hold` above threshold while `pta_go` is not (`spikes=0`). Recovery: ACCEPT the 2.8 t/h slurry; leave 6.80 bar IDLE to its own bank. Cost: missed 22 min crystal-size window (`missed_window_s=1320`).

## Partnered-negative in-window (346)

**ttf-r66-346** is the partnered negative: process-correct MODIFY (hotspot held 424 C < 430 cap) while the world still charges. Safety −0.58 prices the 18 mm tube-sheet gasket blow at **22.400 ms**; `task_progress` stays +0.32 because the clamp completed. Inflection `t_us=22400` is tick 5 and is **inside** the 42 ms raster (`22400 ≤ 42000`). Named un-netted loss: 15 min bed isolate (`abort_s=900`). Not folded into process heads.

Independent LIF (the one labeled sidecar sim): `state.sim_or_real` remains `designed`. `raster.excerpt_source=independent_lif`, `raster.sim_scope=sidecar_only`, `raster.lif` seed 66346, stim `[21400, 25600]`. Excerpt is membrane crossings (`lif.clamp` early vs `lif.blow` 21.4–25.6 ms), not a 1:1 remap of `spike_events`. `meta.tags` include `independent-lif-raster` and `sidecar-sim-only`.

## Reward formula and tick reconciliation

Declared aggregation on every record:

`total = task_progress + safety + efficiency + coherence + exploration`

Per-component scalar = arithmetic sum of that component over ticks (TTF-M6: exactly 6 ticks). Tick 6 is bound to a published sidecar (`abort_s`, `missed_window_s`, `ccr_reseq_s`, `survey_hold_s`) and is strictly after the raster window. Inflection `t_us` is an actual tick.

| id | ticks | tp | saf | eff | coh | exp | total | inflection tick |
|----|-------|----|-----|-----|-----|-----|-------|-----------------|
| 346 | 6 | +0.32 | −0.58 | −0.16 | +0.02 | −0.06 | −0.46 | 5 (22400) |
| 347 | 6 | −0.20 | −0.10 | −0.22 | −0.12 | +0.06 | −0.58 | 4 (4920) |
| 348 | 6 | +0.10 | +0.40 | +0.12 | +0.10 | +0.06 | +0.78 | 4 (6860) |
| 349 | 6 | +0.34 | +0.30 | +0.14 | +0.10 | +0.04 | +0.92 | 4 (7280) |
| 350 | 6 | +0.44 | +0.34 | +0.18 | +0.12 | +0.08 | +1.16 | 4 (4300) |

Tick-6 sidecar bind: 346 `abort_s=900`, 347 `missed_window_s=1320`, 348 `abort_s=480`, 349 `ccr_reseq_s=360`, 350 `survey_hold_s=300`.

## Raster / energy (Loihi-2 4-core, 23 pJ/spike)

| id | domain | n | rate Hz | window_ms | spikes | energy_pJ | energy_uJ |
|----|--------|---|---------|-----------|--------|-----------|-----------|
| 346 | maleic-anhydride-bed | 76 | 26 | 42 | 83 | 1909 | 0.001909 |
| 347 | pta-crystallizer | 92 | 34 | 24 | 75 | 1725 | 0.001725 |
| 348 | vcm-oxychlorination | 108 | 21 | 40 | 91 | 2093 | 0.002093 |
| 349 | ccr-platformer | 64 | 42 | 30 | 81 | 1863 | 0.001863 |
| 350 | soda-ash-solvay | 80 | 34 | 22 | 60 | 1380 | 0.001380 |

`spikes = round(n × rate × window_s)`. Every record carries `gate_snn` whose `decision` matches the safety gate; populations that declare rate+spikes meet the same ±1 budget against `decision_window_s`. `routing.third_factor` has modulator (NA / ACh / DA / 5-HT / adenosine), `tau_e_s`/`tau_e_ms` pair, and eligibility. Excerpt same-neuron gap ≥ 1000 µs; spike trains same-channel refractory ≥ 0.8 ms. Non-346 excerpts are kernelized and independent of `spike_events` times (overlap < 0.8).

## Local checks (staging, not raw)

See generator stdout: `check_jsonl` FactoryStaging, `validate_run.check_line`, `dumps_exact_json`, `raster_status`, `verify_batch_for_frontier(strict=True)`, `spike_probe.py --strict`, tick sums, refractory, Jaccard.

Never `training_ready`. Never `sim_or_real=real`. Never wrote `outputs/raw/`.

## Residual weaknesses (honest)

1. Only **one** labeled independent LIF (346). The other four excerpts are independent of `spike_events` times but are not declared population sims.
2. Wrong-ACCEPT still absent (guard).
3. Tick-6 sidecar bind is a densification of r14/r16, not a new class.
4. Five domain slugs leave the prompt's 8-item pool; a later round that must stay inside the pool will have to rotate sit-outs instead.
5. 347 wrong-reject is sidecar-convictable (routing `to` / quality IDs) as a **new** error class (idle-twin-string-as-live) vs r50 raw-mA, r52 gauge-vs-absolute, r54 bad-quality-sub.
6. 350 ACCEPT is an already-legal proposal confirmed by race order; a later round could pair an ACCEPT with a world charge that does not go negative.

## Next densification target

Labeled LIF on a second record, or an ISI histogram sidecar. Remaining unused even-round wrong-REJECT subclasses include **HART SV-as-PV** and **NAMUR NE43 fail-high as live**. Wrong-ACCEPT remains structurally absent until a prompt amendment.

{NOVEL_COVERAGE_LINE}
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
        BATCH_PATH, "batch-r66.jsonl", staging=FactoryStaging(enabled=True)
    )
    report.append(("check_jsonl FactoryStaging", errors, warnings, kinds, nrec))
    line_errs = []
    for i, rec in enumerate(records, 1):
        errs, kind = check_line(rec, f"batch-r66.jsonl:{i}", factory_staging=True)
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
    records = [record_346(), record_347(), record_348(), record_349(), record_350()]
    issues, jmax, jprior = self_check(records)
    notes = notes_text(jmax, jprior)
    cov_hits = [ln for ln in notes.splitlines() if ln.strip().lower().startswith("novel coverage")]
    if cov_hits != [NOVEL_COVERAGE_LINE]:
        issues.append(f"novel coverage lines {cov_hits}")
    lines = [
        json.dumps(rec, ensure_ascii=False, separators=(",", ":"), allow_nan=False)
        for rec in records
    ]
    BATCH_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")
    NOTES_PATH.write_text(notes, encoding="utf-8")
    print(
        f"wrote {BATCH_PATH} lines={len(lines)} bytes={BATCH_PATH.stat().st_size} "
        f"jmax={jmax:.3f} jprior={jprior:.3f}"
    )
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
