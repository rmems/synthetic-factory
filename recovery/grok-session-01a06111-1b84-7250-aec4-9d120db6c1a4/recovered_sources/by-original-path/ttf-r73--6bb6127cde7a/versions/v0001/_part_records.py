def harvest_occupancy():
    """Prior staged batches + in-flight gens are global occupancy. r73 must not reuse them."""
    domains = set(BANNED_DOMAINS)
    plants = set(BANNED_PLANT_FRAGMENTS)
    skip = {"ttf-r73"}
    for path in sorted(Path("/tmp").glob("ttf-r*/batch-r*.jsonl")):
        if path.parent.name in skip:
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except OSError:
            continue
        for line in text.splitlines():
            if not line.strip():
                continue
            try:
                rec = json.loads(line)
            except json.JSONDecodeError:
                continue
            d = rec.get("state", {}).get("domain") or rec.get("meta", {}).get("domain")
            if d:
                domains.add(str(d))
            title = rec.get("title") or ""
            m = re.match(r"(?:WRONG-(?:MODIFY|REJECT) at )?([A-Za-z0-9-]+)", title)
            if m:
                plants.add(m.group(1))
            desc = rec.get("state", {}).get("description") or ""
            for frag in PLANT_RE.findall(title + " " + desc):
                plants.add(frag)
    for gpath in sorted(Path("/tmp").glob("ttf-r*/*.py")):
        if gpath.parent.name in skip:
            continue
        txt = gpath.read_text(encoding="utf-8", errors="ignore")
        for m in re.finditer(
            r"(?:THIS_DOMAINS|MY_DOMAINS)\s*=\s*[\{(]([^})]+)[\})]", txt
        ):
            domains.update(re.findall(r'"([^"]+)"', m.group(1)))
        for m in re.finditer(
            r"(?:THIS_PLANTS|MY_PLANTS)\s*=\s*\(([^)]+)\)", txt
        ):
            plants.update(re.findall(r'"([^"]+)"', m.group(1)))
        domains.update(re.findall(r'\("domain",\s*"([^"]+)"\)', txt))
        domains.update(re.findall(r'"domain":\s*"([^"]+)"', txt))
    for npath in sorted(Path("/tmp").glob("ttf-r*/NOTES-r*.md")):
        if npath.parent.name in skip:
            continue
        for line in npath.read_text(encoding="utf-8", errors="ignore").splitlines():
            if "Domains this batch" in line:
                for tok in re.findall(r"`([^`]+)`", line):
                    if not tok.startswith("ttf-"):
                        domains.add(tok)
    domains.discard("")
    plants.discard("")
    return domains, plants


def wrap_record(
    rid,
    title,
    state,
    spikes,
    proposed,
    safety,
    executed,
    future,
    ticks,
    notes,
    ras,
    gate,
    domain,
    tags,
    distillation,
    batch_position,
    supervisor_error_type=None,
):
    return OrderedDict(
        [
            ("id", rid),
            ("title", title),
            ("state", state),
            ("spike_events", spikes),
            ("proposed_action", proposed),
            ("safety_decision", safety),
            ("executed_action", executed),
            ("future_outcome", future),
            ("reward_components", reward_block(ticks, notes)),
            ("raster", ras),
            ("gate_snn", gate),
            (
                "meta",
                meta_block(
                    domain,
                    tags,
                    distillation,
                    batch_position,
                    supervisor_error_type=supervisor_error_type,
                ),
            ),
        ]
    )


def lif_381_excerpt():
    n = 76
    dt_us = 100
    tau_m_ms = 19.0
    v_th = 1.0
    v_reset = 0.0
    refractory_us = 1000
    i_bias = 0.91
    i_stim_peak = 2.42
    stim = (22000, 25000)
    seed = 73381
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
    channels = ["lif.clamp" if t < 22000 else "lif.leak" for t, _ in picked]
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
            ("seed", 73381),
            (
                "note",
                "Population sim scoped to this sidecar. Plant remains designed. "
                "Neurons 0-13 carry +0.62 air-flow clamp bias; stim 22-25 ms is the liner crack.",
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


def record_381():
    excerpt, extra = lif_381_excerpt()
    ticks = [
        tick(2080, 0.04, -0.02, -0.02, 0.01, 0.00),
        tick(5200, 0.08, -0.04, -0.02, 0.01, -0.01),
        tick(5380, 0.04, -0.03, -0.02, 0.00, 0.00),
        tick(5900, 0.08, -0.05, -0.03, 0.02, -0.01),
        tick(22400, 0.06, -0.41, -0.04, -0.01, -0.01),
        tick(900000000, 0.02, -0.05, -0.03, 0.01, -0.01),
    ]
    spikes = [
        spike("pt.air.bar", 1.040, 0.41),
        spike("o2.offgas.vol", 2.080, 0.58),
        spike("pt.air.bar", 3.400, 0.50),
        spike("o2.offgas.vol", 5.200, 1.31),
        spike("pt.air.bar", 5.380, 1.12),
        spike("ctrl.gate", 5.900, 0.97),
        spike("o2.offgas.vol", 8.100, 0.82),
        spike("pt.air.bar", 10.400, 0.64),
        spike("ctrl.gate", 14.200, 0.86),
        spike("ae.liner.crack", 22.400, 1.48),
        spike("ae.liner.crack", 24.100, 0.93),
        spike("pt.air.bar", 30.200, 0.40),
        spike("o2.offgas.vol", 36.400, 0.55),
    ]
    state = OrderedDict(
        [
            (
                "description",
                "Air-oxidizer X-3 on Oxane-Thwaite OT-7 is dumping 8.6 vol percent O2 off-gas "
                "while the air header still sits a legal 4.2 bar under 5.5. O2-first clamps air "
                "18.0 -> 11.0 t/h; header-first would keep cruise because 4.2 bar looks under the "
                "compressor cap. A liner crack already seated on the KA-oil boot does not appear "
                "on O2 or air PT until the AE dump.",
            ),
            ("domain", "cyclohexane-air-oxidizer"),
            ("sim_or_real", "designed"),
            (
                "goal",
                "Keep X-3 off-gas O2 <= 6.0 vol percent and finish the KA-oil pass without "
                "dumping cyclohexane through a torn liner.",
            ),
            ("t0_us", 1756850400000381),
            ("gate_latency_us", 700),
            ("race_window_us", 360),
            ("race_window_rel_ms", [5.200, 5.560]),
            (
                "race",
                OrderedDict(
                    [
                        (
                            "contenders",
                            [
                                "o2.offgas.vol 8.6 over 6.0 cap",
                                "pt.air.bar 4.2 with header under 5.5",
                            ],
                        ),
                        (
                            "semantics",
                            "O2-first latches air clamp 18.0 -> 11.0 t/h; header-first keeps 18.0 "
                            "on a 'still under compressor-cap' model.",
                        ),
                        (
                            "window_derivation",
                            "360 us = one paramagnetic O2 slot versus the air-header PT publisher "
                            "on this cyclohexane oxidizer bus.",
                        ),
                        (
                            "order_evidence_note",
                            "Margin 180 us vs combined jitter 62 us (O2 28 + air 34): 2.90x over "
                            "a 2.0x trust floor. Reversing order by < 180 us inside the 360 us "
                            "window would have kept 18.0 t/h; predicted next-sample 7.4 vol "
                            "percent > 6.0 cap.",
                        ),
                    ]
                ),
            ),
            (
                "sensors",
                [
                    "off-gas paramagnetic O2 cell, 2 kHz, 28 us jitter",
                    "air-header PT, 1 kHz, 34 us jitter",
                    "KA-oil boot AE puck (context)",
                    "cyclohexane feed Coriolis (context)",
                ],
            ),
            (
                "constraints",
                OrderedDict(
                    [
                        ("o2_cap_vol_pct", 6.0),
                        ("observed_o2_vol_pct", 8.6),
                        ("air_tph", 18.0),
                        ("air_bar", 4.2),
                        ("air_cap_bar", 5.5),
                    ]
                ),
            ),
            (
                "episode_steps",
                [
                    "1. X-3 indexed on Oxane-Thwaite OT-7; air 18.0 t/h; off-gas O2 8.6 vol percent.",
                    "2. Header 4.2 bar under 5.5 cap; KA-oil pass armed.",
                    "3. Air-PT precursor at 1.040 ms.",
                    "4. Race window [5.200, 5.560] ms.",
                    "5. o2.offgas.vol 8.6 at 5.200 ms (winner).",
                    "6. pt.air.bar 4.2 at 5.380 ms (loser by 180 us).",
                    "7. Gate at 5.900 ms: MODIFY clamp air 18.0 -> 11.0 t/h.",
                    "8. After clamp O2 5.4 vol percent <= 6.0; header still 4.2 bar.",
                    "9. At 22.400 ms a liner crack dumps 0.5 t KA oil.",
                    "10. 15 min boot isolate (abort_s=900); named un-netted loss.",
                ],
            ),
        ]
    )
    proposed = OrderedDict(
        [
            ("name", "cruise_air_flow"),
            (
                "parameters",
                OrderedDict(
                    [("air_tph", 18.0), ("o2_vol_pct", 8.6), ("air_bar", 4.2)]
                ),
            ),
            (
                "evidence",
                OrderedDict(
                    [
                        ("o2_vol_pct", 8.6),
                        ("o2_cap_vol_pct", 6.0),
                        ("predicted_unclamped_next_vol_pct", 7.4),
                        ("air_tph", 18.0),
                        ("air_bar", 4.2),
                        ("air_cap_bar", 5.5),
                        ("race_margin_us", 180),
                        ("combined_jitter_us", 62),
                        ("abort_s", 900),
                    ]
                ),
            ),
            (
                "basis",
                "Planner proposes 18.0 t/h air because header 4.2 bar is under 5.5, treating "
                "the 8.6 vol percent O2 as a still-wet paramagnetic cell rather than an off-gas-cap miss.",
            ),
        ]
    )
    safety = OrderedDict(
        [
            ("decision", "MODIFY"),
            ("correctness", "correct"),
            (
                "rationale",
                "Off-gas O2 8.6 vol percent won by 180 us, so the oxidizer is off-spec, not still "
                "an air-header story. Holding 18.0 t/h predicts next-sample 7.4 vol percent > 6.0 "
                "cap. MODIFY: air 18.0 -> 11.0 t/h. Observed after clamp 5.4 vol percent <= 6.0. "
                "A full REJECT is not indicated: a clean KA-oil pass accepts 11.0 t/h.",
            ),
            (
                "constraint_checked",
                OrderedDict(
                    [
                        (
                            "o2_vol_pct",
                            OrderedDict(
                                [
                                    ("cap", 6.0),
                                    ("observed", 8.6),
                                    ("predicted_unclamped_next", 7.4),
                                    ("clamped_air_tph", 11.0),
                                    ("observed_after_clamp", 5.4),
                                ]
                            ),
                        ),
                        (
                            "order_evidence",
                            OrderedDict(
                                [("margin_us", 180), ("combined_jitter_us", 62), ("ratio", 2.9)]
                            ),
                        ),
                    ]
                ),
            ),
        ]
    )
    executed = OrderedDict(
        [
            ("name", "clamped_air_flow"),
            (
                "parameters",
                OrderedDict(
                    [("air_tph", 11.0), ("o2_vol_pct", 5.4), ("air_bar", 4.2)]
                ),
            ),
            (
                "gate_effect",
                "MODIFY: air 18.0 -> 11.0 t/h. Process-correct vs the 6.0 vol percent O2 cap. "
                "Liner still cracks at 22.400 ms.",
            ),
        ]
    )
    future = OrderedDict(
        [
            (
                "summary",
                "Process-correct MODIFY held off-gas O2 at 5.4 vol percent. At 22.400 ms a liner "
                "crack already seated on the KA-oil boot dumped 0.5 t of cyclohexane. Clamp "
                "reduced dump energy; it did not prevent the crack. Partnered negative: process "
                "heads stay honest; world loss is named, not netted.",
            ),
            (
                "state_delta",
                OrderedDict(
                    [
                        ("offgas", "clamp executed; peak 5.4 vol percent <= 6.0 cap"),
                        ("liner", "cracked at 22.400 ms; 0.5 t KA oil"),
                        ("repair", "15 min boot isolate (abort_s=900)"),
                        ("mission", "OT-7 KA-oil pass incomplete this circuit"),
                    ]
                ),
            ),
            (
                "surprises",
                [
                    "Neither off-gas O2 nor air PT predicted the seated liner crack; ae.liner.crack is a new channel at 22.400 ms, 16.500 ms after the gate, still inside the 42 ms raster.",
                    "Delayed (abort_s=900): 15 min boot isolate. Named un-netted loss, not folded into task_progress.",
                ],
            ),
            (
                "un_netted_loss",
                "15 min boot isolate after the liner crack. Safety head -0.60 prices the dump; "
                "task_progress stays +0.32 because the air clamp completed under the 6.0 vol "
                "percent cap. World loss is named here, not subtracted from process heads.",
            ),
            (
                "race_result",
                OrderedDict(
                    [
                        ("winner", "o2.offgas.vol (5.200 ms, 8.6 vol percent)"),
                        ("loser", "pt.air.bar (5.380 ms, 4.2 bar)"),
                        ("margin_us", 180),
                        (
                            "counterfactual_if_reversed",
                            "Header-first by < 180 us inside the 360 us window would have kept "
                            "18.0 t/h; predicted next-sample 7.4 vol percent would have missed "
                            "the 6.0 cap even without the crack. The MODIFY is still the correct "
                            "process. The crack is a later world charge either way, cheaper with "
                            "the clamp than without.",
                        ),
                    ]
                ),
            ),
            ("reward_inflection_t_us", 22400),
            (
                "reward_inflection_note",
                "Safety collapses at the 22.400 ms liner crack (tick t_us=22400), inside the "
                "42 ms raster. The correct MODIFY at 5.900 ms is in the same excerpt. Do not "
                "put inflection on the abort_s=900 isolation tick.",
            ),
            ("delayed_surprise_s", 900),
        ]
    )
    ras = raster_core(
        42,
        76,
        26,
        83,
        routing(
            "thalamic-relay.oxane-o2",
            "spikenaut.policy.air-clamp",
            [
                ("relay.o2.offgas", "policy.air_clamp", 0.68),
                ("relay.pt.air", "policy.header_hold", 0.29),
                ("relay.ae.liner", "policy.air_clamp", -0.42),
            ],
            "noradrenaline",
            0.04,
            "surprise-gated pre_post_stdp; NA at O2 win (5.200 ms) opens a 42 ms eligibility "
            "trace that still covers the 22.400 ms liner crack",
        ),
        excerpt,
        extra=extra,
    )
    gate = OrderedDict(
        [
            ("decision_window_ms", 0.36),
            ("decision", "MODIFY"),
            (
                "populations",
                [
                    pop_budget("air_clamp", 50, 0.5, 220.0, 0.36),
                    pop_budget("header_hold", 40, 0.8, 50.0, 0.36),
                    pop("leak_veto", 24, 0.75),
                ],
            ),
        ]
    )
    return wrap_record(
        "ttf-r73-381",
        "Oxane-Thwaite OT-7 / Oxidizer X-3: off-gas O2 beats air header by 180 us; correct "
        "MODIFY still eats an in-window liner crack (partnered negative total -0.44)",
        state,
        spikes,
        proposed,
        safety,
        executed,
        future,
        ticks,
        "Partnered negative. Process-correct MODIFY; world still charges inside the 42 ms "
        "raster. total -0.44 = 0.32 + -0.60 + -0.16 + 0.04 + -0.04. Named boot isolate "
        "(abort_s=900) is not netted into task_progress.",
        ras,
        gate,
        "cyclohexane-air-oxidizer",
        [
            "modify",
            "partnered-negative-total",
            "independent-lif-raster",
            "sidecar-sim-only",
            "in-window-world-charge",
            "designed",
        ],
        "A critic can see the world-charge as a LIF burst inside the raster while process "
        "heads stay honest. Credit assignment is spikes, not prose across a 15 min boot isolate.",
        1,
    )


def record_382():
    ticks = [
        tick(2240, -0.02, -0.02, -0.02, -0.01, 0.01),
        tick(5600, -0.04, -0.04, -0.03, -0.02, 0.01),
        tick(5780, -0.04, -0.04, -0.03, -0.02, 0.01),
        tick(6120, -0.08, -0.10, -0.06, -0.03, 0.02),
        tick(6460, -0.02, -0.02, -0.02, -0.01, 0.01),
        tick(720000000, -0.02, -0.02, -0.02, -0.01, 0.00),
    ]
    spikes = [
        spike("enc.quench.tph", 1.120, 0.42),
        spike("pt.k2.live", 2.240, 0.57),
        spike("enc.quench.tph", 3.500, 0.49),
        spike("pt.k2.live", 5.600, 1.29),
        spike("pt.k2.lagged", 5.780, 1.10),
        spike("ctrl.gate", 6.120, 0.96),
        spike("pt.k2.live", 8.400, 0.80),
        spike("enc.quench.tph", 10.400, 0.63),
        spike("ctrl.gate", 12.600, 0.84),
        spike("pt.k2.live", 16.600, 0.41),
        spike("pt.k2.lagged", 22.200, 0.54),
        spike("pt.k2.live", 26.400, 0.38),
    ]
    excerpt = independent_excerpt(73382, 88, 28000, 14, spike_avoid_us(spikes))
    state = OrderedDict(
        [
            (
                "description",
                "BPA kettle K-2 at Bisphenol-Croft BC-4 already holds live SI pressure at 0.24 "
                "MPa under a 0.30 MPa cap, yet a lagged bar publisher still prints 2.4 with "
                "tag_age_us=2460. Live-SI-first should ACCEPT; a weak supervisor treats the "
                "lagged 2.4 bar as 2.4 MPa and dumps quench.",
            ),
            ("domain", "bisphenol-A-reactor"),
            ("sim_or_real", "designed"),
            (
                "goal",
                "Finish the BC-4 condensation with live SI <= 0.30 MPa, leave phenol at the "
                "planned 14.0 t/h, and keep quench at the 0.4 t/h seal.",
            ),
            ("t0_us", 1756850400000382),
            ("gate_latency_us", 520),
            ("race_window_us", 340),
            ("race_window_rel_ms", [5.600, 5.940]),
            (
                "race",
                OrderedDict(
                    [
                        (
                            "contenders",
                            [
                                "pt.k2.live 0.24 MPa on kettle K-2 SI",
                                "pt.k2.lagged 2.4 bar on lagged EU bus",
                            ],
                        ),
                        (
                            "semantics",
                            "Live-SI-first should ACCEPT the already-legal 0.24 MPa; lagged-bar-first "
                            "is a false '2.4 MPa over 0.30' quench dump.",
                        ),
                        (
                            "window_derivation",
                            "340 us = one live-SI MPa slot versus the lagged bar publisher on this "
                            "BPA dual-EU PLC bus.",
                        ),
                        (
                            "order_evidence_note",
                            "Margin 180 us vs combined jitter 60 us (live 28 + lagged 32). Order is "
                            "correctly live-SI-first. The error is engineering unit on the lagged "
                            "bus, not the magnitude: 2.4 bar is the same 0.24 MPa published late.",
                        ),
                    ]
                ),
            ),
            (
                "sensors",
                [
                    "live SI PT on K-2, 2 kHz, 28 us jitter, tag=K2_PT.LIVE unit=MPa eu_fresh=true",
                    "lagged bar PT on K-2, 1 kHz, 32 us jitter, tag=K2_PT.LAG unit=bar tag_age_us=2460",
                    "quench FT (context)",
                    "phenol feed FT (context)",
                ],
            ),
            (
                "constraints",
                OrderedDict(
                    [
                        ("cap_MPa", 0.30),
                        ("live_MPa", 0.24),
                        ("lagged_numeric", 2.4),
                        ("lagged_unit", "bar"),
                        ("policy_unit", "MPa"),
                        ("tag_age_us", 2460),
                        ("max_legal_tag_age_us", 800),
                        ("phenol_tph", 14.0),
                    ]
                ),
            ),
            (
                "episode_steps",
                [
                    "1. K-2 already condensing; live SI 0.24 MPa; phenol 14.0 t/h.",
                    "2. Lagged bar tag prints 2.4; tag_age_us=2460 > 800; unit=bar.",
                    "3. Quench precursor at 1.120 ms.",
                    "4. Race window [5.600, 5.940] ms.",
                    "5. pt.k2.live 0.24 MPa at 5.600 ms (winner).",
                    "6. pt.k2.lagged 2.4 bar at 5.780 ms (loser by 180 us).",
                    "7. Gate at 6.120 ms: WRONG-MODIFY binds lagged bar-as-MPa quench.",
                    "8. Quench 0.4 -> 6.8 t/h; live SI never crossed 0.30 MPa.",
                    "9. Conversion crash on K-2; phenol dumped.",
                    "10. Delayed (abort_s=720): 12 min kettle dump while K-2 is quenched.",
                ],
            ),
        ]
    )
    proposed = OrderedDict(
        [
            ("name", "cruise_bpa_kettle"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("quench_tph", 0.4),
                        ("phenol_tph", 14.0),
                        ("bind_lagged_eu", False),
                    ]
                ),
            ),
            (
                "evidence",
                OrderedDict(
                    [
                        ("live_MPa", 0.24),
                        ("cap_MPa", 0.30),
                        ("lagged_numeric", 2.4),
                        ("lagged_unit", "bar"),
                        ("policy_unit", "MPa"),
                        ("lagged_as_MPa", 2.4),
                        ("tag_age_us", 2460),
                        ("max_legal_tag_age_us", 800),
                        ("eu_fresh", False),
                        ("phenol_tph", 14.0),
                        ("t_gate_us", 6120),
                        ("correct_quench_tph", 0.4),
                        ("correct_gate", "ACCEPT"),
                        ("race_margin_us", 180),
                        ("combined_jitter_us", 60),
                        ("abort_s", 720),
                    ]
                ),
            ),
            (
                "basis",
                "Planner proposes continuing 0.4 t/h quench because live SI 0.24 MPa is under "
                "the 0.30 MPa cap, treating the lagged 2.4 bar as a stale EU echo of the same pressure.",
            ),
        ]
    )
    safety = OrderedDict(
        [
            ("decision", "MODIFY"),
            ("correctness", "incorrect"),
            (
                "rationale",
                "Pressure 2.4 exceeds the 0.30 cap (true only if the lagged bar number is MPa). "
                "Apply the 6.8 t/h quench dump on K-2 because K2_PT.LAG is the highlighted tag. "
                "Leave live SI unused.",
            ),
            (
                "constraint_checked",
                OrderedDict(
                    [
                        (
                            "pressure",
                            OrderedDict(
                                [
                                    ("cap_MPa", 0.30),
                                    ("live_MPa", 0.24),
                                    ("lagged_numeric", 2.4),
                                    ("lagged_unit", "bar"),
                                    ("policy_unit", "MPa"),
                                    ("executed_quench_tph", 6.8),
                                    ("correct_quench_tph", 0.4),
                                    ("correct_gate", "ACCEPT"),
                                ]
                            ),
                        ),
                        (
                            "eu_bind",
                            OrderedDict(
                                [
                                    ("t_gate_us", 6120),
                                    ("bind_lagged_eu", True),
                                    ("tag_age_us", 2460),
                                    ("max_legal_tag_age_us", 800),
                                    ("wrong_unit", True),
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
            ("name", "quench_dump_lagged_eu"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("quench_tph", 6.8),
                        ("phenol_tph", 14.0),
                        ("bind_lagged_eu", True),
                    ]
                ),
            ),
            (
                "gate_effect",
                "MODIFY (incorrect / wrong-unit lagged-bus): 6.8 t/h quench dump applied because "
                "lagged 2.4 bar was treated as 2.4 MPa. Routing relay.pt.lagged -> "
                "policy.wrong_eu_clamp; no positive weight to policy.live_hold.",
            ),
        ]
    )
    future = OrderedDict(
        [
            (
                "summary",
                "Wrong-MODIFY dumped quench on a legal BPA kettle. Live 0.24 MPa was under the "
                "0.30 MPa cap at t_gate; lagged 2.4 bar is the same pressure in the wrong EU. "
                "12 min kettle dump (abort_s=720). Correct gate was ACCEPT; leave quench 0.4 t/h "
                "on live SI at t_gate_us=6120.",
            ),
            (
                "state_delta",
                OrderedDict(
                    [
                        ("live_si", "K-2 left legal at 0.24 MPa; quench slammed to 6.8 t/h"),
                        ("lagged_tag", "2.4 bar treated as 2.4 MPa; tag_age_us=2460"),
                        ("dump", "12 min phenol dump, K-2 quench"),
                        ("mission", "condensation deferred"),
                    ]
                ),
            ),
            (
                "surprises",
                [
                    "Live-SI-first was the correct order and the SI number was under cap; the MODIFY spent that win on a lagged bar-as-MPa bind.",
                    "Delayed (abort_s=720): BC-4 holds 12 min while K-2 is dumped and recharged; next batch 14 min late.",
                ],
            ),
            (
                "recovery",
                OrderedDict(
                    [
                        (
                            "correct_gate",
                            "ACCEPT; leave quench 0.4 t/h on live SI at t_gate_us=6120; bind_lagged_eu=false; leave phenol at 14.0 t/h.",
                        ),
                        ("correct_actuator", "K-2_quench_seal"),
                        ("wrong_eu", "bar_as_MPa"),
                        ("t_gate_us", 6120),
                        (
                            "wrong_edit_applied",
                            OrderedDict(
                                [
                                    ("quench_tph", 6.8),
                                    ("bind_lagged_eu", True),
                                ]
                            ),
                        ),
                        (
                            "cost",
                            "12 min kettle dump (task/efficiency); live SI never crossed 0.30 MPa while quench was spent on a lagged bar-as-MPa bind.",
                        ),
                    ]
                ),
            ),
            (
                "race_result",
                OrderedDict(
                    [
                        ("winner", "pt.k2.live (5.600 ms, 0.24 MPa SI)"),
                        ("loser", "pt.k2.lagged (5.780 ms, 2.4 bar lagged)"),
                        ("margin_us", 180),
                        (
                            "counterfactual_if_reversed",
                            "Lagged-first by < 180 us would still be 2.4 bar of the same 0.24 MPa; "
                            "a correct gate binds pt.k2.live to policy.live_hold at t_gate either "
                            "way. The wrong MODIFY spent the live win on a lagged wrong-unit clamp.",
                        ),
                    ]
                ),
            ),
            ("reward_inflection_t_us", 6120),
            (
                "reward_inflection_note",
                "Task, safety, and efficiency drop at the lagged-EU bind (6.120 ms, tick 4). "
                "The 12 min kettle dump is delayed surprise, not the inflection.",
            ),
            ("delayed_surprise_s", 720),
        ]
    )
    ras = raster_core(
        28,
        88,
        34,
        84,
        routing(
            "thalamic-relay.bpa-lagged-eu",
            "spikenaut.policy.wrong-eu-clamp",
            [
                ("relay.pt.lagged", "policy.wrong_eu_clamp", 0.74),
                ("relay.pt.live", "policy.wrong_eu_clamp", 0.21),
            ],
            "acetylcholine",
            0.08,
            "eu_cap_stdp; ACh tags the (wrong) lagged bar-as-MPa bind at the live SI win",
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
            ("decision_window_ms", 0.34),
            ("decision", "MODIFY"),
            (
                "populations",
                [
                    pop_budget("wrong_eu_clamp", 48, 0.45, 300.0, 0.34),
                    pop("live_hold", 48, 0.90),
                    pop("eu_veto", 20, 0.80),
                ],
            ),
        ]
    )
    return wrap_record(
        "ttf-r73-382",
        "WRONG-MODIFY at Bisphenol-Croft BC-4 / Kettle K-2: live 0.24 MPa read correctly; "
        "6.8 t/h quench dump on lagged 2.4 bar-as-MPa (wrong-unit / lagged-bus)",
        state,
        spikes,
        proposed,
        safety,
        executed,
        future,
        ticks,
        "Wrong-modify / wrong-unit lagged-bus. Sidecar arithmetic 0.24 < 0.30 on live SI is "
        "true; MODIFY bound to wrong_eu_clamp. total -0.68 = -0.22 + -0.24 + -0.18 + -0.10 + 0.06.",
        ras,
        gate,
        "bisphenol-A-reactor",
        [
            "modify",
            "wrong-gate",
            "wrong-unit",
            "lagged-bus",
            "sidecar-convictable",
            "designed",
        ],
        "Teaches a probe that a correct live-SI-first race can still be a wrong gate when the "
        "MODIFY clamps on a lagged bar tag interpreted as MPa. Convictable from live_MPa vs "
        "cap_MPa, lagged_unit, tag_age_us, and routing without BPA physics.",
        2,
        supervisor_error_type="wrong-modify",
    )


def record_383():
    ticks = [
        tick(2736, 0.01, 0.04, 0.01, 0.01, 0.01),
        tick(6840, 0.02, 0.08, 0.02, 0.02, 0.01),
        tick(7020, 0.01, 0.06, 0.02, 0.01, 0.01),
        tick(7640, 0.04, 0.16, 0.04, 0.04, 0.02),
        tick(7960, 0.01, 0.05, 0.02, 0.01, 0.01),
        tick(480000000, 0.01, 0.03, 0.01, 0.01, 0.00),
    ]
    spikes = [
        spike("i.arc.kA", 1.360, 0.40),
        spike("ae.lf.pps", 2.736, 0.56),
        spike("i.arc.kA", 4.100, 0.48),
        spike("ae.lf.pps", 6.840, 1.34),
        spike("i.arc.kA", 7.020, 1.11),
        spike("ctrl.gate", 7.640, 0.98),
        spike("ae.lf.pps", 10.400, 0.81),
        spike("i.arc.kA", 14.800, 0.62),
        spike("ctrl.gate", 18.200, 0.84),
        spike("ae.lf.pps", 28.400, 0.52),
        spike("i.arc.kA", 36.100, 0.39),
        spike("ae.lf.pps", 42.200, 0.44),
    ]
    excerpt = independent_excerpt(73383, 120, 46000, 15, spike_avoid_us(spikes))
    state = OrderedDict(
        [
            (
                "description",
                "HIL ladle furnace LF-2 at Ladle-Staith LS-HIL hears electrode AE at 48 pps while "
                "arc current remains 38 kA under a 52 kA cap. AE-first holds the tap; current-first "
                "would dispatch 12 MW because the kA ram looks legal. The HIL electrode mockup is "
                "the authority, not the melt-shop floor.",
            ),
            ("domain", "ladle-furnace-arc"),
            ("sim_or_real", "hil"),
            (
                "goal",
                "Keep LF-2 from dispatching a growling electrode while arc current remains under "
                "its own cap.",
            ),
            ("t0_us", 1756850400000383),
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
                                "ae.lf.pps 48 over 12 cap",
                                "i.arc.kA 38 under 52 cap",
                            ],
                        ),
                        (
                            "semantics",
                            "AE-first latches hold; current-first dispatches 12 MW on a 'kA still legal' model.",
                        ),
                        (
                            "window_derivation",
                            "320 us = one AE puck slot versus the arc-CT publisher on this HIL ladle-furnace bus.",
                        ),
                        (
                            "order_evidence_note",
                            "Margin 180 us vs combined jitter 58 us (AE 26 + CT 32): 3.10x over a "
                            "2.0x trust floor. Reversing order by < 180 us inside the 320 us "
                            "window would have dispatched 12 MW into a growling electrode.",
                        ),
                    ]
                ),
            ),
            (
                "sensors",
                [
                    "electrode AE puck, 50 kHz, 26 us jitter",
                    "arc CT, 1 kHz, 32 us jitter",
                    "tap-to-tap encoder (context)",
                    "bath TC (context)",
                ],
            ),
            (
                "constraints",
                OrderedDict(
                    [
                        ("ae_cap_pps", 12.0),
                        ("observed_ae_pps", 48.0),
                        ("arc_kA", 38.0),
                        ("arc_cap_kA", 52.0),
                        ("proposed_mw", 12.0),
                    ]
                ),
            ),
            (
                "episode_steps",
                [
                    "1. LF-2 HIL indexed; 12 MW tap armed.",
                    "2. Arc 38 kA under 52; AE 48 pps over 12.",
                    "3. CT precursor at 1.360 ms.",
                    "4. Race window [6.840, 7.160] ms.",
                    "5. ae.lf.pps 48 at 6.840 ms (winner).",
                    "6. i.arc.kA 38 at 7.020 ms (loser by 180 us).",
                    "7. Gate at 7.640 ms: REJECT hold, do not dispatch.",
                    "8. Power 0 MW; current left at 38 kA.",
                    "9. Electrode inspected on the HIL stand.",
                    "10. Delayed (abort_s=480): 8 min ladle reset.",
                ],
            ),
        ]
    )
    proposed = OrderedDict(
        [
            ("name", "dispatch_tap"),
            (
                "parameters",
                OrderedDict([("mw", 12.0), ("hold", False), ("arc_kA", 38.0)]),
            ),
            (
                "evidence",
                OrderedDict(
                    [
                        ("ae_pps", 48.0),
                        ("ae_cap_pps", 12.0),
                        ("arc_kA", 38.0),
                        ("arc_cap_kA", 52.0),
                        ("race_margin_us", 180),
                        ("combined_jitter_us", 58),
                        ("abort_s", 480),
                    ]
                ),
            ),
            (
                "basis",
                "Planner proposes 12 MW because arc 38 kA is under 52, treating the 48 pps AE "
                "as transformer hash rather than a growling electrode.",
            ),
        ]
    )
    safety = OrderedDict(
        [
            ("decision", "REJECT"),
            ("correctness", "correct"),
            (
                "rationale",
                "Electrode AE 48 pps won by 180 us, so the ladle furnace is growling, not still "
                "an arc-current story. 38 kA is under 52 and does not authorize dispatch. REJECT: "
                "hold power 12 -> 0 MW. A MODIFY that only trims kA would leave the growl.",
            ),
            (
                "constraint_checked",
                OrderedDict(
                    [
                        (
                            "ae_pps",
                            OrderedDict(
                                [
                                    ("cap", 12.0),
                                    ("observed", 48.0),
                                    ("executed_mw", 0.0),
                                ]
                            ),
                        ),
                        (
                            "order_evidence",
                            OrderedDict(
                                [("margin_us", 180), ("combined_jitter_us", 58), ("ratio", 3.1)]
                            ),
                        ),
                    ]
                ),
            ),
        ]
    )
    executed = OrderedDict(
        [
            ("name", "hold_ladle"),
            (
                "parameters",
                OrderedDict([("mw", 0.0), ("hold", True), ("arc_kA", 38.0)]),
            ),
            (
                "gate_effect",
                "REJECT: power 12 -> 0 MW. Arc current left at 38 kA under its own cap.",
            ),
        ]
    )
    future = OrderedDict(
        [
            (
                "summary",
                "Correct REJECT held LF-2. AE 48 pps beat arc 38 kA by 180 us. Current was legal; "
                "the electrode was not. 8 min ladle reset (abort_s=480) is delayed survey, not a "
                "process miss.",
            ),
            (
                "state_delta",
                OrderedDict(
                    [
                        ("power", "held at 0 MW"),
                        ("current", "left 38 kA < 52 cap"),
                        ("electrode", "8 min ladle reset (abort_s=480)"),
                        ("mission", "HIL tap not dispatched"),
                    ]
                ),
            ),
            (
                "surprises",
                [
                    "Arc CT never crossed its cap; AE was the only over-cap channel.",
                    "Delayed (abort_s=480): 8 min ladle reset on the HIL stand.",
                ],
            ),
            (
                "race_result",
                OrderedDict(
                    [
                        ("winner", "ae.lf.pps (6.840 ms, 48 pps)"),
                        ("loser", "i.arc.kA (7.020 ms, 38 kA)"),
                        ("margin_us", 180),
                        (
                            "counterfactual_if_reversed",
                            "Current-first by < 180 us inside the 320 us window would have "
                            "dispatched 12 MW into a growling electrode. The REJECT is still "
                            "the correct gate.",
                        ),
                    ]
                ),
            ),
            ("reward_inflection_t_us", 7640),
            (
                "reward_inflection_note",
                "Safety and task rise at the correct REJECT (7.640 ms, tick 4). The 8 min ladle "
                "reset is delayed surprise, not the inflection.",
            ),
            ("delayed_surprise_s", 480),
        ]
    )
    ras = raster_core(
        46,
        120,
        20,
        110,
        routing(
            "thalamic-relay.lf-ae",
            "spikenaut.policy.lf-hold",
            [
                ("relay.ae.lf", "policy.lf_hold", 0.70),
                ("relay.i.arc", "policy.ka_go", 0.24),
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
                ("abort_s", 480),
                ("delayed_surprise_s", 480),
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
                    pop_budget("lf_hold", 56, 0.45, 280.0, 0.32),
                    pop("ka_go", 40, 0.90),
                    pop("ae_veto", 24, 0.70),
                ],
            ),
        ]
    )
    return wrap_record(
        "ttf-r73-383",
        "Ladle-Staith LS-HIL / Furnace LF-2: electrode AE 48 pps beats arc 38 kA by 180 us; "
        "correct REJECT holds the tap",
        state,
        spikes,
        proposed,
        safety,
        executed,
        future,
        ticks,
        "Correct REJECT. AE 48 > 12 cap beats legal arc current. total +0.80 = 0.10 + 0.42 + 0.12 + 0.10 + 0.06.",
        ras,
        gate,
        "ladle-furnace-arc",
        ["reject", "hil", "ae-vs-ka", "growling-electrode", "tick6-sidecar-bound"],
        "Teaches that a legal arc-current header can lose to electrode AE inside a 320 us "
        "window; reversing 180 us would have dispatched a growling ladle furnace.",
        3,
    )


def record_384():
    ticks = [
        tick(2880, 0.06, 0.04, 0.02, 0.02, 0.01),
        tick(7200, 0.08, 0.06, 0.04, 0.02, 0.02),
        tick(7380, 0.06, 0.04, 0.03, 0.02, 0.01),
        tick(7840, 0.12, 0.08, 0.05, 0.04, 0.02),
        tick(8200, 0.04, 0.04, 0.02, 0.01, 0.01),
        tick(360000000, 0.04, 0.02, 0.02, 0.01, 0.01),
    ]
    spikes = [
        spike("tc.skin.C", 1.200, 0.40),
        spike("dens.bed.m", 2.880, 0.55),
        spike("tc.skin.C", 4.400, 0.48),
        spike("dens.bed.m", 7.200, 1.26),
        spike("tc.skin.C", 7.380, 1.08),
        spike("ctrl.gate", 7.840, 0.95),
        spike("dens.bed.m", 11.200, 0.78),
        spike("tc.skin.C", 14.800, 0.60),
        spike("ctrl.gate", 18.400, 0.82),
        spike("dens.bed.m", 22.600, 0.50),
        spike("tc.skin.C", 26.200, 0.38),
    ]
    excerpt = independent_excerpt(73384, 48, 28000, 12, spike_avoid_us(spikes))
    params = OrderedDict(
        [
            ("c3_tph", 18.0),
            ("bed_m", 12.4),
            ("skin_C", 78.0),
            ("hold", False),
        ]
    )
    state = OrderedDict(
        [
            (
                "description",
                "Gas-phase PP reactor R-8 at Propene-Ghyll PG-5 already holds bed level at 12.4 m "
                "under a 16.0 m trip, with skin 78 C under 95. Level-first accepts the 18.0 t/h "
                "C3 feed; skin-first would have rejected a legal fluidized bed on a 'still climbing' model.",
            ),
            ("domain", "pp-gas-phase-reactor"),
            ("sim_or_real", "simulated"),
            (
                "goal",
                "Finish the PG-5 gas-phase pass with bed <= 16.0 m and skin <= 95 C.",
            ),
            ("t0_us", 1756850400000384),
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
                                "dens.bed.m 12.4 under 16.0 trip",
                                "tc.skin.C 78 under 95 cap",
                            ],
                        ),
                        (
                            "semantics",
                            "Level-first confirms the already-legal 18.0 t/h C3 feed; skin-first "
                            "would have treated the densitometer as a climb echo and looked for an extra hold.",
                        ),
                        (
                            "window_derivation",
                            "360 us = one nuclear-density slot versus the skin-TC publisher on this simulated Unipol-style bus.",
                        ),
                        (
                            "order_evidence_note",
                            "Margin 180 us vs combined jitter 58 us (dens 26 + TC 32): 3.10x over "
                            "a 2.0x trust floor. Reversing order by < 180 us would not make the "
                            "proposed C3 feed illegal; it would only have delayed confirmation.",
                        ),
                    ]
                ),
            ),
            (
                "sensors",
                [
                    "nuclear densitometer on bed, 26 us jitter",
                    "skin TC well, 32 us jitter",
                    "C3 Coriolis (context)",
                    "delta-P bed (context)",
                ],
            ),
            (
                "constraints",
                OrderedDict(
                    [
                        ("bed_cap_m", 16.0),
                        ("observed_bed_m", 12.4),
                        ("skin_cap_C", 95.0),
                        ("observed_skin_C", 78.0),
                        ("h2_partial_bar", 18.0),
                        ("h2_cap_bar", 24.0),
                        ("proposed_c3_tph", 18.0),
                    ]
                ),
            ),
            (
                "episode_steps",
                [
                    "1. R-8 indexed on Propene-Ghyll PG-5; 18.0 t/h C3 armed.",
                    "2. Caps: bed 16.0 m, skin 95 C, H2 24 bar.",
                    "3. Skin-TC precursor at 1.200 ms.",
                    "4. Race window [7.200, 7.560] ms.",
                    "5. dens.bed.m 12.4 at 7.200 ms (winner).",
                    "6. tc.skin.C 78 at 7.380 ms (loser by 180 us).",
                    "7. Gate at 7.840 ms: ACCEPT 18.0 t/h already legal.",
                    "8. C3 continues; no extra hold.",
                    "9. 6 min survey confirms bed still under 16.0 m.",
                    "10. QA: ACCEPT params identical to proposed.",
                ],
            ),
        ]
    )
    proposed = OrderedDict(
        [
            ("name", "feed_c3_18"),
            ("parameters", params),
            (
                "evidence",
                OrderedDict(
                    [
                        ("bed_m", 12.4),
                        ("bed_cap_m", 16.0),
                        ("skin_C", 78.0),
                        ("skin_cap_C", 95.0),
                        ("h2_partial_bar", 18.0),
                        ("h2_cap_bar", 24.0),
                        ("c3_tph", 18.0),
                        ("race_margin_us", 180),
                        ("combined_jitter_us", 58),
                        ("survey_s", 360),
                    ]
                ),
            ),
            (
                "basis",
                "Planner proposes an 18.0 t/h C3 feed because bed 12.4 m is under 16.0 and skin "
                "78 C is under 95 C.",
            ),
        ]
    )
    safety = OrderedDict(
        [
            ("decision", "ACCEPT"),
            ("correctness", "correct"),
            (
                "rationale",
                "Bed level 12.4 m won by 180 us and is under 16.0. Skin 78 C is under 95 C. "
                "Hydrogen 18 bar is under 24. ACCEPT the already-legal C3 feed.",
            ),
            (
                "constraint_checked",
                OrderedDict(
                    [
                        (
                            "bed_m",
                            OrderedDict(
                                [
                                    ("cap", 16.0),
                                    ("observed", 12.4),
                                    ("executed_c3_tph", 18.0),
                                ]
                            ),
                        ),
                        (
                            "order_evidence",
                            OrderedDict(
                                [("margin_us", 180), ("combined_jitter_us", 58), ("ratio", 3.1)]
                            ),
                        ),
                    ]
                ),
            ),
        ]
    )
    executed = OrderedDict(
        [
            ("name", "feed_c3_18"),
            ("parameters", params),
            (
                "gate_effect",
                "ACCEPT: 18.0 t/h C3 and 12.4 m bed unchanged. Routing relay.dens.bed -> policy.bed_go.",
            ),
        ]
    )
    future = OrderedDict(
        [
            (
                "summary",
                "Correct ACCEPT left R-8 on an 18.0 t/h / 12.4 m bed C3 feed. Skin-TC hitch did "
                "not justify a hold. 6 min survey confirmed bed still under 16.0 m.",
            ),
            (
                "state_delta",
                OrderedDict(
                    [
                        ("feed", "still 18.0 t/h C3"),
                        ("bed", "12.4 m under 16.0 trip"),
                        ("skin", "78 C under 95"),
                        ("hold", "none applied"),
                    ]
                ),
            ),
            (
                "surprises",
                [
                    "Skin TC 78 C hitch is residual, not a runaway trip.",
                    "Delayed (survey_s=360): 6 min survey restacks R-8 without a recovery hold.",
                ],
            ),
            (
                "race_result",
                OrderedDict(
                    [
                        ("winner", "dens.bed.m (7.200 ms, 12.4 m)"),
                        ("loser", "tc.skin.C (7.380 ms, 78 C)"),
                        ("margin_us", 180),
                        (
                            "counterfactual_if_reversed",
                            "Skin-first by < 180 us would only delay confirmation. The C3 feed "
                            "stays legal either way; ACCEPT is still required.",
                        ),
                    ]
                ),
            ),
            ("reward_inflection_t_us", 7840),
            (
                "reward_inflection_note",
                "Task credit lands at the ACCEPT (7.840 ms, tick 4). Survey is delayed surprise.",
            ),
            ("delayed_surprise_s", 360),
        ]
    )
    ras = raster_core(
        28,
        48,
        42,
        56,
        routing(
            "thalamic-relay.bed-dens",
            "spikenaut.policy.bed-go",
            [
                ("relay.dens.bed", "policy.bed_go", 0.68),
                ("relay.tc.skin", "policy.skin_hold", 0.21),
            ],
            "serotonin",
            0.07,
            "legal_c3_stdp; 5-HT tags the bed_go bind at the densitometer win",
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
            ("decision_window_ms", 0.36),
            ("decision", "ACCEPT"),
            (
                "populations",
                [
                    pop_budget("bed_go", 40, 0.45, 250.0, 0.36),
                    pop("skin_hold", 32, 0.90),
                    pop("bed_veto", 16, 0.80),
                ],
            ),
        ]
    )
    return wrap_record(
        "ttf-r73-384",
        "Propene-Ghyll PG-5 / Reactor R-8: bed 12.4 m beats skin 78 C by 180 us; ACCEPT "
        "already-legal 18.0 t/h C3",
        state,
        spikes,
        proposed,
        safety,
        executed,
        future,
        ticks,
        "Correct ACCEPT of an already-legal gas-phase C3 feed. total +1.06 = 0.40 + 0.28 + 0.18 + 0.12 + 0.08.",
        ras,
        gate,
        "pp-gas-phase-reactor",
        [
            "accept",
            "already-legal",
            "simulated-unipol-loop",
            "dens-vs-tc",
            "sidecar-convictable",
            "simulated",
        ],
        "Teaches that a bed densitometer under trip can confirm an already-legal C3 feed "
        "without a skin-TC hitch becoming a hold.",
        4,
    )


def record_385():
    ticks = [
        tick(2016, 0.06, 0.04, 0.03, 0.02, 0.01),
        tick(5040, 0.10, 0.06, 0.04, 0.02, 0.02),
        tick(5200, 0.06, 0.04, 0.03, 0.02, 0.01),
        tick(5640, 0.12, 0.08, 0.05, 0.04, 0.02),
        tick(5920, 0.06, 0.05, 0.03, 0.01, 0.01),
        tick(240000000, 0.04, 0.03, 0.02, 0.01, 0.01),
    ]
    spikes = [
        spike("v.cell.V", 0.980, 0.41),
        spike("tc.bath.C", 2.016, 0.60),
        spike("v.cell.V", 3.200, 0.51),
        spike("tc.bath.C", 5.040, 1.30),
        spike("v.cell.V", 5.200, 1.12),
        spike("ctrl.gate", 5.640, 0.97),
        spike("tc.bath.C", 8.100, 0.78),
        spike("v.cell.V", 12.400, 0.62),
        spike("ctrl.gate", 16.200, 0.85),
        spike("tc.bath.C", 20.400, 0.54),
        spike("v.cell.V", 22.800, 0.43),
    ]
    excerpt = independent_excerpt(73385, 80, 24000, 12, spike_avoid_us(spikes))
    params = OrderedDict(
        [
            ("cell_kA", 18.0),
            ("bath_C", 590.0),
            ("hold", False),
        ]
    )
    state = OrderedDict(
        [
            (
                "description",
                "Downs cell C-11 at Downs-Lynchet DL-3 is already at 590 C bath under a 620 C cap, "
                "cell voltage 6.8 V under 7.4. Temp-first accepts the 18.0 kA run; voltage-first "
                "would have rejected a legal sodium cell on a 'still climbing' model.",
            ),
            ("domain", "sodium-metal-downs-cell"),
            ("sim_or_real", "designed"),
            (
                "goal",
                "Run C-11 at 18.0 kA, keep bath <= 620 C and cell voltage <= 7.4 V, and leave "
                "the freeze on schedule.",
            ),
            ("t0_us", 1756850400000385),
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
                                "tc.bath.C 590 under 620 cap",
                                "v.cell.V 6.8 under 7.4 trip",
                            ],
                        ),
                        (
                            "semantics",
                            "Temp-first confirms the already-legal 18.0 kA run; voltage-first would "
                            "have treated the bath TC as a hitch echo and looked for an extra hold.",
                        ),
                        (
                            "window_derivation",
                            "280 us = one bath-TC slot versus the cell-voltage publisher on this Downs-cell bus.",
                        ),
                        (
                            "order_evidence_note",
                            "Margin 160 us vs combined jitter 52 us (TC 22 + V 30): 3.08x over a "
                            "2.0x trust floor. Reversing order by < 160 us inside the 280 us "
                            "window would have REJECTED an already-legal 18.0 kA run.",
                        ),
                    ]
                ),
            ),
            (
                "sensors",
                [
                    "bath TC well, 2 kHz, 22 us jitter",
                    "cell voltage PT, 1 kHz, 30 us jitter",
                    "anode current CT (context)",
                    "chlorine header PT (context)",
                ],
            ),
            (
                "constraints",
                OrderedDict(
                    [
                        ("bath_cap_C", 620.0),
                        ("observed_bath_C", 590.0),
                        ("cell_kA", 18.0),
                        ("cell_V", 6.8),
                        ("cell_cap_V", 7.4),
                    ]
                ),
            ),
            (
                "episode_steps",
                [
                    "1. Cell C-11 indexed on Downs-Lynchet DL-3; 18.0 kA armed.",
                    "2. Bath 590 C under 620; voltage 6.8 V under 7.4.",
                    "3. Voltage precursor at 0.980 ms.",
                    "4. Race window [5.040, 5.320] ms.",
                    "5. tc.bath.C 590 at 5.040 ms (winner).",
                    "6. v.cell.V 6.8 at 5.200 ms (loser by 160 us).",
                    "7. Gate at 5.640 ms: ACCEPT 18.0 kA.",
                    "8. Bath stays 590 C; voltage stays 6.8 V.",
                    "9. Freeze taps on-spec.",
                    "10. Delayed (dwell_s=240): 4 min ladle reseq.",
                ],
            ),
        ]
    )
    proposed = OrderedDict(
        [
            ("name", "hold_cell_kA"),
            ("parameters", params),
            (
                "evidence",
                OrderedDict(
                    [
                        ("bath_C", 590.0),
                        ("bath_cap_C", 620.0),
                        ("cell_kA", 18.0),
                        ("cell_V", 6.8),
                        ("cell_cap_V", 7.4),
                        ("race_margin_us", 160),
                        ("combined_jitter_us", 52),
                        ("dwell_s", 240),
                    ]
                ),
            ),
            (
                "basis",
                "Planner proposes 18.0 kA because bath 590 C is under 620 and cell voltage 6.8 V "
                "is under 7.4.",
            ),
        ]
    )
    safety = OrderedDict(
        [
            ("decision", "ACCEPT"),
            ("correctness", "correct"),
            (
                "rationale",
                "Bath TC 590 C won by 160 us, so the cell is already legal, not still climbing. "
                "Voltage 6.8 V is under 7.4. ACCEPT the 18.0 kA run. A REJECT would idle a legal Downs cell.",
            ),
            (
                "constraint_checked",
                OrderedDict(
                    [
                        (
                            "bath_C",
                            OrderedDict(
                                [
                                    ("cap", 620.0),
                                    ("observed", 590.0),
                                    ("executed_cell_kA", 18.0),
                                ]
                            ),
                        ),
                        (
                            "order_evidence",
                            OrderedDict(
                                [("margin_us", 160), ("combined_jitter_us", 52), ("ratio", 3.08)]
                            ),
                        ),
                    ]
                ),
            ),
        ]
    )
    executed = OrderedDict(
        [
            ("name", "hold_cell_kA"),
            ("parameters", params),
            (
                "gate_effect",
                "ACCEPT: leave 18.0 kA; bath 590 C; voltage legal.",
            ),
        ]
    )
    future = OrderedDict(
        [
            (
                "summary",
                "Correct ACCEPT of an already-legal 18.0 kA Downs run. Bath 590 C beat voltage "
                "6.8 V by 160 us. 4 min freeze reseq (dwell_s=240) is delayed, not a miss.",
            ),
            (
                "state_delta",
                OrderedDict(
                    [
                        ("current", "18.0 kA held"),
                        ("bath", "590 C < 620 cap"),
                        ("cell", "C-11 on-spec"),
                        ("reseq", "4 min freeze reseq (dwell_s=240)"),
                    ]
                ),
            ),
            (
                "surprises",
                [
                    "Cell voltage never approached 7.4 V; bath was already under cap.",
                    "Delayed (dwell_s=240): 4 min freeze reseq after tap.",
                ],
            ),
            (
                "race_result",
                OrderedDict(
                    [
                        ("winner", "tc.bath.C (5.040 ms, 590 C)"),
                        ("loser", "v.cell.V (5.200 ms, 6.8 V)"),
                        ("margin_us", 160),
                        (
                            "counterfactual_if_reversed",
                            "Voltage-first by < 160 us inside the 280 us window would have "
                            "REJECTED an already-legal 18.0 kA run. The ACCEPT is still the "
                            "correct gate.",
                        ),
                    ]
                ),
            ),
            ("reward_inflection_t_us", 5640),
            (
                "reward_inflection_note",
                "Task and safety rise at the correct ACCEPT (5.640 ms, tick 4). The 4 min reseq "
                "is delayed surprise, not the inflection.",
            ),
            ("delayed_surprise_s", 240),
        ]
    )
    ras = raster_core(
        24,
        80,
        28,
        54,
        routing(
            "thalamic-relay.bath-tc",
            "spikenaut.policy.downs-go",
            [
                ("relay.tc.bath", "policy.downs_go", 0.67),
                ("relay.v.cell", "policy.downs_hold", 0.25),
            ],
            "adenosine",
            0.07,
            "accept_stdp; adenosine tags the bath-TC win as an already-legal Downs run",
        ),
        excerpt,
        extra=OrderedDict(
            [
                ("excerpt_source", "kernelized_events"),
                ("sim_scope", "none"),
                ("dwell_s", 240),
                ("delayed_surprise_s", 240),
            ]
        ),
    )
    gate = OrderedDict(
        [
            ("decision_window_ms", 0.28),
            ("decision", "ACCEPT"),
            (
                "populations",
                [
                    pop_budget("downs_go", 40, 0.45, 250.0, 0.28),
                    pop("downs_hold", 32, 0.90),
                    pop("bath_veto", 16, 0.80),
                ],
            ),
        ]
    )
    return wrap_record(
        "ttf-r73-385",
        "Downs-Lynchet DL-3 / Cell C-11: bath 590 C beats cell 6.8 V by 160 us; correct ACCEPT "
        "of an already-legal 18.0 kA run",
        state,
        spikes,
        proposed,
        safety,
        executed,
        future,
        ticks,
        "Correct ACCEPT. Bath 590 < 620; voltage 6.8 < 7.4. total +1.14 = 0.44 + 0.30 + 0.20 + 0.12 + 0.08.",
        ras,
        gate,
        "sodium-metal-downs-cell",
        ["accept", "designed", "bath-vs-v", "already-legal-cell", "tick6-sidecar-bound"],
        "Teaches that a legal cell voltage can lose to bath TC inside a 280 us window; "
        "reversing 160 us would have REJECTED an already-legal Downs run.",
        5,
    )
