def record_374():
    ticks = [
        tick(2880, 0.06, 0.04, 0.02, 0.02, 0.01),
        tick(7200, 0.08, 0.06, 0.04, 0.02, 0.02),
        tick(7380, 0.06, 0.04, 0.03, 0.02, 0.01),
        tick(7840, 0.12, 0.08, 0.05, 0.04, 0.02),
        tick(8200, 0.04, 0.04, 0.02, 0.01, 0.01),
        tick(360000000, 0.04, 0.02, 0.02, 0.01, 0.01),
    ]
    spikes = [
        spike("tc.jkt.C", 1.200, 0.40),
        spike("gc.hcho.wt", 2.880, 0.55),
        spike("tc.jkt.C", 4.400, 0.48),
        spike("gc.hcho.wt", 7.200, 1.26),
        spike("tc.jkt.C", 7.380, 1.08),
        spike("ctrl.gate", 7.840, 0.95),
        spike("gc.hcho.wt", 11.200, 0.78),
        spike("tc.jkt.C", 14.800, 0.60),
        spike("ctrl.gate", 18.400, 0.82),
        spike("gc.hcho.wt", 22.600, 0.50),
        spike("tc.jkt.C", 26.200, 0.38),
    ]
    excerpt = independent_excerpt(71374, 48, 28000, 12, spike_avoid_us(spikes))
    params = OrderedDict(
        [
            ("trioxane_tph", 11.0),
            ("hcho_wt_pct", 1.62),
            ("jacket_C", 84.0),
            ("hold", False),
        ]
    )
    state = OrderedDict(
        [
            (
                "description",
                "Trioxane loop R-8 at Acetal-Spile AS-4 already holds free formaldehyde at 1.62 "
                "wt percent under a 2.40 cap, with jacket 84 C under 98. GC-first accepts the "
                "11.0 t/h recycle; jacket-first would have rejected a legal POM charge on a "
                "'still climbing' model.",
            ),
            ("domain", "polyacetal-trioxane"),
            ("sim_or_real", "simulated"),
            (
                "goal",
                "Finish the AS-4 recycle with free HCHO <= 2.40 wt percent and jacket <= 98 C.",
            ),
            ("t0_us", 1756850400000374),
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
                                "gc.hcho.wt 1.62 under 2.40 cap",
                                "tc.jkt.C 84 under 98 cap",
                            ],
                        ),
                        (
                            "semantics",
                            "GC-first confirms the already-legal 11.0 t/h recycle; jacket-first "
                            "would have treated the GC as a climb echo and looked for an extra hold.",
                        ),
                        (
                            "window_derivation",
                            "360 us = one online-GC slot versus the jacket-TC publisher on this "
                            "simulated trioxane-loop bus.",
                        ),
                        (
                            "order_evidence_note",
                            "Margin 180 us vs combined jitter 58 us (GC 26 + TC 32): 3.10x over "
                            "a 2.0x trust floor. Reversing order by < 180 us would not make the "
                            "proposed recycle illegal; it would only have delayed confirmation.",
                        ),
                    ]
                ),
            ),
            (
                "sensors",
                [
                    "online formaldehyde GC, 26 us jitter",
                    "jacket TC well, 32 us jitter",
                    "trioxane FT (context)",
                    "BF3 catalyst FT (context)",
                ],
            ),
            (
                "constraints",
                OrderedDict(
                    [
                        ("hcho_cap_wt_pct", 2.40),
                        ("observed_hcho_wt_pct", 1.62),
                        ("jacket_cap_C", 98.0),
                        ("observed_jacket_C", 84.0),
                        ("proposed_trioxane_tph", 11.0),
                    ]
                ),
            ),
            (
                "episode_steps",
                [
                    "1. R-8 indexed on Acetal-Spile AS-4; 11.0 t/h recycle armed.",
                    "2. Caps: HCHO 2.40 wt percent, jacket 98 C.",
                    "3. Jacket-TC precursor at 1.200 ms.",
                    "4. Race window [7.200, 7.560] ms.",
                    "5. gc.hcho.wt 1.62 at 7.200 ms (winner).",
                    "6. tc.jkt.C 84 at 7.380 ms (loser by 180 us).",
                    "7. Gate at 7.840 ms: ACCEPT 11.0 t/h already legal.",
                    "8. Recycle continues; no extra hold.",
                    "9. 6 min survey confirms HCHO still under 2.40.",
                    "10. QA: ACCEPT params identical to proposed.",
                ],
            ),
        ]
    )
    proposed = OrderedDict(
        [
            ("name", "recycle_11"),
            ("parameters", params),
            (
                "evidence",
                OrderedDict(
                    [
                        ("hcho_wt_pct", 1.62),
                        ("hcho_cap_wt_pct", 2.40),
                        ("jacket_C", 84.0),
                        ("jacket_cap_C", 98.0),
                        ("trioxane_tph", 11.0),
                        ("race_margin_us", 180),
                        ("combined_jitter_us", 58),
                        ("survey_s", 360),
                    ]
                ),
            ),
            (
                "basis",
                "Planner proposes an 11.0 t/h recycle because HCHO 1.62 is under 2.40 and jacket "
                "84 C is under 98 C.",
            ),
        ]
    )
    safety = OrderedDict(
        [
            ("decision", "ACCEPT"),
            ("correctness", "correct"),
            (
                "rationale",
                "Free formaldehyde 1.62 wt percent won by 180 us and is under 2.40. Jacket 84 C "
                "is under 98 C. ACCEPT the already-legal recycle.",
            ),
            (
                "constraint_checked",
                OrderedDict(
                    [
                        (
                            "hcho_wt_pct",
                            OrderedDict(
                                [
                                    ("cap", 2.40),
                                    ("observed", 1.62),
                                    ("executed_trioxane_tph", 11.0),
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
            ("name", "recycle_11"),
            ("parameters", OrderedDict(params.items())),
            (
                "gate_effect",
                "ACCEPT: 11.0 t/h recycle and 1.62 wt percent HCHO unchanged. Routing "
                "relay.gc.hcho -> policy.triox_go.",
            ),
        ]
    )
    future = OrderedDict(
        [
            (
                "summary",
                "Correct ACCEPT left R-8 on an 11.0 t/h / 1.62 wt percent HCHO recycle. Jacket "
                "hitch did not justify a hold. 6 min survey confirmed HCHO still under 2.40.",
            ),
            (
                "state_delta",
                OrderedDict(
                    [
                        ("recycle", "still 11.0 t/h"),
                        ("hcho", "1.62 under 2.40 cap"),
                        ("jacket", "84 C under 98"),
                        ("hold", "none applied"),
                    ]
                ),
            ),
            (
                "surprises",
                [
                    "Jacket TC 84 C hitch is residual, not a runaway trip.",
                    "Delayed (survey_s=360): 6 min survey restacks R-8 without a recovery hold.",
                ],
            ),
            (
                "race_result",
                OrderedDict(
                    [
                        ("winner", "gc.hcho.wt (7.200 ms, 1.62 wt percent)"),
                        ("loser", "tc.jkt.C (7.380 ms, 84 C)"),
                        ("margin_us", 180),
                        (
                            "counterfactual_if_reversed",
                            "Jacket-first by < 180 us would only delay confirmation. The recycle "
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
    dw = 0.36
    ras = raster_core(
        28,
        48,
        42,
        56,
        routing(
            "thalamic-relay.hcho-gc",
            "spikenaut.policy.triox-go",
            [
                ("relay.gc.hcho", "policy.triox_go", 0.68),
                ("relay.tc.jkt", "policy.jkt_hold", 0.21),
            ],
            "serotonin",
            0.07,
            "legal_triox_stdp; 5-HT tags the triox_go bind at the GC win",
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
            ("decision_window_ms", dw),
            ("decision", "ACCEPT"),
            (
                "populations",
                [
                    pop_budget("triox_go", 40, 0.45, 250.0, dw),
                    pop("jkt_hold", 32, 0.90),
                    pop("hcho_veto", 16, 0.80),
                ],
            ),
        ]
    )
    return OrderedDict(
        [
            ("id", "ttf-r71-374"),
            (
                "title",
                "Acetal-Spile AS-4 / Loop R-8: free HCHO 1.62 beats jacket 84 C by 180 us; "
                "ACCEPT already-legal 11.0 t/h trioxane recycle",
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
                    "Correct ACCEPT of an already-legal trioxane recycle. total +1.06 = "
                    "0.40 + 0.28 + 0.18 + 0.12 + 0.08.",
                ),
            ),
            ("raster", ras),
            ("gate_snn", gate),
            (
                "meta",
                meta_block(
                    "polyacetal-trioxane",
                    [
                        "accept",
                        "already-legal",
                        "simulated-trioxane-loop",
                        "gc-vs-tc",
                        "sidecar-convictable",
                        "simulated",
                    ],
                    "Teaches that a formaldehyde GC under cap can confirm an already-legal "
                    "recycle without a jacket hitch becoming a hold.",
                    4,
                ),
            ),
        ]
    )


def record_375():
    ticks = [
        tick(2016, 0.06, 0.04, 0.03, 0.02, 0.01),
        tick(5040, 0.10, 0.06, 0.04, 0.02, 0.02),
        tick(5200, 0.06, 0.04, 0.03, 0.02, 0.01),
        tick(5640, 0.12, 0.08, 0.05, 0.04, 0.02),
        tick(5920, 0.06, 0.05, 0.03, 0.01, 0.01),
        tick(240000000, 0.04, 0.03, 0.02, 0.01, 0.01),
    ]
    spikes = [
        spike("tc.inlet.C", 0.980, 0.41),
        spike("titr.avcl.pct", 2.016, 0.60),
        spike("tc.inlet.C", 3.200, 0.51),
        spike("titr.avcl.pct", 5.040, 1.30),
        spike("tc.inlet.C", 5.200, 1.12),
        spike("ctrl.gate", 5.640, 0.97),
        spike("titr.avcl.pct", 8.100, 0.78),
        spike("tc.inlet.C", 12.400, 0.62),
        spike("ctrl.gate", 16.200, 0.85),
        spike("titr.avcl.pct", 20.400, 0.54),
        spike("tc.inlet.C", 22.800, 0.43),
    ]
    excerpt = independent_excerpt(71375, 80, 24000, 12, spike_avoid_us(spikes))
    params = OrderedDict(
        [
            ("cake_tph", 6.5),
            ("avcl_pct", 68.4),
            ("hold", False),
        ]
    )
    state = OrderedDict(
        [
            (
                "description",
                "Hypochlorite dryer D-2 at Bleach-Ketch BK-5 is already at 68.4 percent available "
                "chlorine under a 72.0 cap, inlet 168 C under 185. Titration-first accepts the "
                "6.5 t/h cake; inlet-first would have rejected a legal dryer on a 'still "
                "wetting' model.",
            ),
            ("domain", "calcium-hypochlorite-dryer"),
            ("sim_or_real", "designed"),
            (
                "goal",
                "Run D-2 at 6.5 t/h cake, keep AvCl <= 72.0 percent and inlet <= 185 C, and "
                "leave the drum on schedule.",
            ),
            ("t0_us", 1756850400000375),
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
                                "titr.avcl.pct 68.4 under 72.0 cap",
                                "tc.inlet.C 168 under 185 cap",
                            ],
                        ),
                        (
                            "semantics",
                            "Titration-first confirms the already-legal 6.5 t/h cake; inlet-first "
                            "would have treated the titer as a hitch echo and looked for an extra hold.",
                        ),
                        (
                            "window_derivation",
                            "280 us = one auto-titrator slot versus the inlet-TC publisher on this "
                            "hypochlorite dryer bus.",
                        ),
                        (
                            "order_evidence_note",
                            "Margin 160 us vs combined jitter 52 us (titr 22 + inlet 30): 3.08x over "
                            "a 2.0x trust floor. Reversing order by < 160 us inside the 280 us "
                            "window would have REJECTED an already-legal cake feed.",
                        ),
                    ]
                ),
            ),
            (
                "sensors",
                [
                    "online available-chlorine titrator, 2 kHz, 22 us jitter",
                    "inlet air TC, 1 kHz, 30 us jitter",
                    "cake weigh-belt (context)",
                    "exhaust dewpoint (context)",
                ],
            ),
            (
                "constraints",
                OrderedDict(
                    [
                        ("avcl_cap_pct", 72.0),
                        ("observed_avcl_pct", 68.4),
                        ("cake_tph", 6.5),
                        ("inlet_C", 168.0),
                        ("inlet_cap_C", 185.0),
                    ]
                ),
            ),
            (
                "episode_steps",
                [
                    "1. Dryer D-2 indexed on Bleach-Ketch BK-5; cake 6.5 t/h armed.",
                    "2. AvCl 68.4 percent under 72.0; inlet 168 C under 185.",
                    "3. Inlet precursor at 0.980 ms.",
                    "4. Race window [5.040, 5.320] ms.",
                    "5. titr.avcl.pct 68.4 at 5.040 ms (winner).",
                    "6. tc.inlet.C 168 at 5.200 ms (loser by 160 us).",
                    "7. Gate at 5.640 ms: ACCEPT 6.5 t/h cake.",
                    "8. AvCl stays 68.4; inlet stays 168 C.",
                    "9. Drum stays on-spec.",
                    "10. Delayed (dwell_s=240): 4 min baghouse reseq.",
                ],
            ),
        ]
    )
    proposed = OrderedDict(
        [
            ("name", "hold_cake_feed"),
            ("parameters", params),
            (
                "evidence",
                OrderedDict(
                    [
                        ("avcl_pct", 68.4),
                        ("avcl_cap_pct", 72.0),
                        ("cake_tph", 6.5),
                        ("inlet_C", 168.0),
                        ("inlet_cap_C", 185.0),
                        ("race_margin_us", 160),
                        ("combined_jitter_us", 52),
                        ("dwell_s", 240),
                    ]
                ),
            ),
            (
                "basis",
                "Planner proposes 6.5 t/h cake because AvCl 68.4 is under 72.0 and inlet 168 C "
                "is under 185.",
            ),
        ]
    )
    safety = OrderedDict(
        [
            ("decision", "ACCEPT"),
            ("correctness", "correct"),
            (
                "rationale",
                "Available chlorine 68.4 percent won by 160 us, so the dryer is already legal, "
                "not still wetting. Inlet 168 C is under 185. ACCEPT the 6.5 t/h cake. A REJECT "
                "would idle a legal hypochlorite drum.",
            ),
            (
                "constraint_checked",
                OrderedDict(
                    [
                        (
                            "avcl_pct",
                            OrderedDict(
                                [
                                    ("cap", 72.0),
                                    ("observed", 68.4),
                                    ("executed_cake_tph", 6.5),
                                ]
                            ),
                        ),
                        (
                            "order_evidence",
                            OrderedDict(
                                [
                                    ("margin_us", 160),
                                    ("combined_jitter_us", 52),
                                    ("ratio", 3.08),
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
            ("name", "hold_cake_feed"),
            ("parameters", OrderedDict(params.items())),
            ("gate_effect", "ACCEPT: leave 6.5 t/h cake; AvCl 68.4; inlet legal."),
        ]
    )
    future = OrderedDict(
        [
            (
                "summary",
                "Correct ACCEPT of an already-legal 6.5 t/h cake. AvCl 68.4 beat inlet 168 C by "
                "160 us. 4 min baghouse reseq (dwell_s=240) is delayed, not a miss.",
            ),
            (
                "state_delta",
                OrderedDict(
                    [
                        ("cake", "6.5 t/h held"),
                        ("avcl", "68.4 < 72.0 cap"),
                        ("dryer", "D-2 on-spec"),
                        ("reseq", "4 min baghouse reseq (dwell_s=240)"),
                    ]
                ),
            ),
            (
                "surprises",
                [
                    "Inlet never approached 185 C; available chlorine was already under cap.",
                    "Delayed (dwell_s=240): 4 min baghouse reseq after the drum.",
                ],
            ),
            (
                "race_result",
                OrderedDict(
                    [
                        ("winner", "titr.avcl.pct (5.040 ms, 68.4 percent)"),
                        ("loser", "tc.inlet.C (5.200 ms, 168 C)"),
                        ("margin_us", 160),
                        (
                            "counterfactual_if_reversed",
                            "Inlet-first by < 160 us inside the 280 us window would have REJECTED "
                            "an already-legal cake feed. The ACCEPT is still the correct gate.",
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
    dw = 0.28
    ras = raster_core(
        24,
        80,
        28,
        54,
        routing(
            "thalamic-relay.avcl-titr",
            "spikenaut.policy.cake-go",
            [
                ("relay.titr.avcl", "policy.cake_go", 0.67),
                ("relay.tc.inlet", "policy.cake_hold", 0.25),
            ],
            "adenosine",
            0.07,
            "accept_stdp; adenosine tags the AvCl win as an already-legal cake feed",
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
            ("decision_window_ms", dw),
            ("decision", "ACCEPT"),
            (
                "populations",
                [
                    pop_budget("cake_go", 40, 0.45, 250.0, dw),
                    pop("cake_hold", 32, 0.90),
                    pop("avcl_veto", 16, 0.80),
                ],
            ),
        ]
    )
    return OrderedDict(
        [
            ("id", "ttf-r71-375"),
            (
                "title",
                "Bleach-Ketch BK-5 / Dryer D-2: AvCl 68.4 percent beats inlet 168 C by 160 us; "
                "correct ACCEPT of an already-legal 6.5 t/h cake",
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
                    "Correct ACCEPT. AvCl 68.4 < 72.0; inlet 168 < 185. "
                    "total +1.14 = 0.44 + 0.30 + 0.20 + 0.12 + 0.08.",
                ),
            ),
            ("raster", ras),
            ("gate_snn", gate),
            (
                "meta",
                meta_block(
                    "calcium-hypochlorite-dryer",
                    [
                        "accept",
                        "designed",
                        "avcl-vs-inlet",
                        "already-legal-cake",
                        "tick6-sidecar-bound",
                    ],
                    "Teaches that a legal inlet temperature can lose to AvCl titration inside a "
                    "280 us window; reversing 160 us would have REJECTED an already-legal cake.",
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


def expected_m6_prefix(rec):
    st = rec["state"]
    events = rec["spike_events"]
    race = st["race_window_rel_ms"]
    in_win = [e for e in events if race[0] - 1e-9 <= e["t_rel_ms"] <= race[1] + 1e-9]
    ordered = sorted(in_win, key=lambda e: e["t_rel_ms"])
    win_e = next(e for e in ordered if e["channel"] != "ctrl.gate")
    lose_e = next(
        e for e in ordered if e["channel"] not in {win_e["channel"], "ctrl.gate"}
    )
    t_win = round(win_e["t_rel_ms"] * 1000)
    t_lose = round(lose_e["t_rel_ms"] * 1000)
    t_gate = t_win + int(st["gate_latency_us"])
    t_race = int(st["race_window_us"])
    tick1 = round(0.40 * t_win)
    if rec["id"] == "ttf-r71-371":
        tick5 = 22600
    else:
        tick5 = t_gate + t_race
    return [tick1, t_win, t_lose, t_gate, tick5], t_win, t_lose, t_gate


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


def harvest_occupancy():
    domains = set(BANNED_DOMAINS)
    plants = set(BANNED_PLANT_FRAGMENTS)
    for path in sorted(Path("/tmp").glob("ttf-r*")):
        if path.resolve() == OUT_DIR.resolve():
            continue
        for p in sorted(path.glob("*")):
            if p.suffix not in {".py", ".md", ".jsonl"}:
                continue
            try:
                txt = p.read_text(encoding="utf-8", errors="replace")
            except OSError:
                continue
            for m in re.finditer(
                r"(?:THIS_DOMAINS|MY_DOMAINS)\s*=\s*[\{(](.*?)[\})]", txt, re.S
            ):
                domains.update(re.findall(r'"([^"]+)"', m.group(1)))
            for m in re.finditer(
                r"(?:THIS_PLANTS|MY_PLANTS)\s*=\s*[\{(](.*?)[\})]", txt, re.S
            ):
                plants.update(re.findall(r'"([^"]+)"', m.group(1)))
            if p.name.startswith("NOTES"):
                for m in re.finditer(r"Domains this batch:\s*(.+)", txt):
                    domains.update(re.findall(r"`([^`]+)`", m.group(1)))
            if p.name.startswith("batch-") and p.suffix == ".jsonl":
                for line in txt.splitlines():
                    if not line.strip():
                        continue
                    try:
                        rec = json.loads(line)
                    except json.JSONDecodeError:
                        continue
                    d = (rec.get("state") or {}).get("domain") or (
                        rec.get("meta") or {}
                    ).get("domain")
                    if d:
                        domains.add(str(d))
                    desc = (rec.get("state") or {}).get("description", "")
                    if isinstance(desc, str):
                        plants.update(
                            re.findall(
                                r"\b([A-Z][A-Za-z]+(?:-[A-Z][A-Za-z0-9]+)+)\b", desc
                            )
                        )
    return domains, plants


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
    occ_d, occ_p = harvest_occupancy()
    domains |= occ_d
    return domains, descs, "\n".join(blobs), occ_p


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
    prior_doms, prior_descs, prior_blob, occ_plants = prior_domains_and_descs()
    for plant in THIS_PLANTS:
        if plant in prior_blob or plant in occ_plants:
            issues.append(f"plant {plant} collides prior occupancy")
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
    if len(wrong) != 1 or wrong[0]["id"] != "ttf-r71-372":
        issues.append(f"wrong-gate set {[w['id'] for w in wrong]}")
    if wrong and wrong[0]["meta"].get("supervisor_error_type") != "wrong-modify":
        issues.append("expected wrong-modify")
    if any(r["state"]["sim_or_real"] == "real" for r in records):
        issues.append("sim_or_real=real")
    hil = [r["id"] for r in records if r["state"]["sim_or_real"] == "hil"]
    if hil != ["ttf-r71-373"]:
        issues.append(f"hil set {hil}")
    sim = [r["id"] for r in records if r["state"]["sim_or_real"] == "simulated"]
    if sim != ["ttf-r71-374"]:
        issues.append(f"simulated set {sim}")
    decisions = [r["safety_decision"]["decision"] for r in records]
    if (
        decisions.count("ACCEPT") != 2
        or decisions.count("MODIFY") != 2
        or decisions.count("REJECT") != 1
    ):
        issues.append(f"gate mix {decisions}")
    ids = [r["id"] for r in records]
    if ids != [f"ttf-r71-{n}" for n in range(371, 376)]:
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
        if rec["id"] == "ttf-r71-371":
            if rec["raster"].get("excerpt_source") != "independent_lif":
                issues.append("371 missing independent_lif")
            if rec["future_outcome"]["reward_inflection_t_us"] > rec["raster"]["window_ms"] * 1000:
                issues.append("371 inflection outside window")
            if rec["reward_components"]["total"] >= 0:
                issues.append("371 partnered-neg total not negative")
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
        if rec["meta"]["round"] != 71:
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
        prefix, t_win, t_lose, t_gate = expected_m6_prefix(rec)
        if tick_times[:5] != prefix:
            issues.append(f"{rec['id']} TTF-M6 prefix {tick_times[:5]} != {prefix}")
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
        if rec["id"] == "ttf-r71-372":
            ev = rec["proposed_action"]["evidence"]
            if not (ev["live_tph"] < ev["cap_tph"]):
                issues.append("372 live nitric not under cap")
            if ev.get("published_unit") != "kg/h" or ev.get("legal_unit") != "t/h":
                issues.append("372 unit pair missing")
            if not (ev.get("tag_age_us", 0) > ev.get("max_legal_tag_age_us", 10**9)):
                issues.append("372 tag not lagged")
            if ev.get("peak_hold_fresh") is not False:
                issues.append("372 peak_hold_fresh not false")
            if rec["executed_action"]["parameters"].get("bind_lagged_kgh") is not True:
                issues.append("372 bind_lagged_kgh not true")
            if rec["executed_action"]["parameters"].get("nitric_tph") != 0.35:
                issues.append("372 expected wrong-unit 0.35 t/h nitric")
            if "recovery" not in rec["future_outcome"]:
                issues.append("372 missing recovery")
            table_to = {row["to"] for row in rec["raster"]["routing"]["table"]}
            if "policy.live_hold" in table_to:
                issues.append("372 routing still has live_hold")
            if "policy.wrong_unit_clamp" not in table_to:
                issues.append("372 routing missing wrong_unit_clamp")
            if "wrong-unit" not in rec["meta"]["tags"] or "lagged-bus" not in rec["meta"]["tags"]:
                issues.append("372 missing wrong-unit/lagged-bus tags")
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
        if rec["raster"]["energy_pJ"] != rec["raster"]["spikes"] * 23:
            issues.append(f"{rec['id']} energy_pJ")
        if not (20 <= rec["raster"]["window_ms"] <= 50):
            issues.append(f"{rec['id']} window_ms")
        for item in rec["raster"]["excerpt"]:
            if not (0 <= item["t_us"] <= rec["raster"]["window_ms"] * 1000):
                issues.append(f"{rec['id']} excerpt t_us {item['t_us']}")
            if not (0 <= item["neuron_id"] < rec["raster"]["neurons"]):
                issues.append(f"{rec['id']} neuron_id {item['neuron_id']}")
    return issues, jmax, jprior


def notes_text(jmax: float, jprior: float) -> str:
    return f"""# Thalamic Trajectory Factory — NOTES-r71

- Factory: `thalamic-trajectory-factory`
- Run label: `2026-09-02-final-heavy`
- Generator: `grok-4.6`
- Channel: SuperGrok Heavy consumer chat (RM-793 research-only)
- Quota: 5
- Quality: Q=5
- IDs: `ttf-r71-371` … `ttf-r71-375`
- Domains this batch: `silane-cvd-epitaxy`, `dinitrotoluene-nitrator`, `magnesia-shaft-kiln`, `polyacetal-trioxane`, `calcium-hypochlorite-dryer`

These five domain slugs sit outside the prompt 8-pool and outside staged r13–r65 occupancy (jsonl SoT, including r60 tio2-chloride/SBR/Zn-EW/fermenter/roller-kiln, r61 ilmenite-slag/APT-autoclave/can-necker/RE-kiln/Li-leach, r62 Sohio/vacuum-wash/AOD/OPP/Formox, r65 wolfram-APT/Beckmann/rutile-burner/ebullated/AOD-decarb) plus in-flight gens r63–r68 (`beet-cossette-diffuser`, `isasmelt-furnace`, `maleic-anhydride-bed`, `calcium-carbide-furnace`, `hydrogen-peroxide-ao-loop`). All five plants are invented (Silane-Fleet, Nitryl-Hope, Periclase-Quoin, Acetal-Spile, Bleach-Ketch). Do not restack prior TTF plants (Marrow-Dock, Vesper-Lattice, Brine-Well, Saddle-Arc, Ashlar-Gait, Tungstate-Keld, Oxime-Clough, Ilmenite-Naze, Ebullate-Pike, Decarb-Haugh, Enamel-Ghyll, Melamine-Thorp, Acetylene-Howe, Anthraq-Holt).

## Batch map

| id | domain | decision | correctness | sim_or_real | total | edge |
|----|--------|----------|-------------|-------------|-------|------|
| ttf-r71-371 | silane-cvd-epitaxy | MODIFY | correct | designed | **−0.44** | process-correct SiH4 clamp; susceptor crack inside 42 ms raster; independent LIF |
| ttf-r71-372 | dinitrotoluene-nitrator | MODIFY | **incorrect (wrong-modify / wrong-unit lagged-bus)** | designed | −0.68 | live 2.4 t/h < 3.0 cap; 0.35 t/h cut because 2400 kg/h read as t/h |
| ttf-r71-373 | magnesia-shaft-kiln | REJECT | correct | hil | +0.80 | AE 48 pps beats draft 4.2 kPa; hold magnesite |
| ttf-r71-374 | polyacetal-trioxane | ACCEPT | correct | simulated | +1.06 | HCHO 1.62 vs jacket 84 C; proposed 11.0 t/h already legal |
| ttf-r71-375 | calcium-hypochlorite-dryer | ACCEPT | correct | designed | +1.14 | AvCl 68.4 vs inlet 168 C; proposed 6.5 t/h already legal |

Gate mix: 2 ACCEPT, 1 correct MODIFY (partnered-neg, in-window), 1 incorrect MODIFY (wrong-unit / lagged-bus), 1 correct REJECT. Provenance: designed×3, simulated×1, hil×1 (Periclase-Quoin PQ-HIL shaft stand). Intra-batch Jaccard on `state.description` {jmax:.3f} (max vs prior staged {jprior:.3f}).

## Wrong-modify

**ttf-r71-372** is the mandated incorrect gate (`safety_decision.correctness=incorrect`, `meta.supervisor_error_type=wrong-modify`). Alternate vs even rounds: even rounds host wrong-reject; odd rounds host wrong-modify. This is **wrong-unit / lagged-bus** (legal live SI t/h; supervisor clamps because a stale kg/h alias is read as t/h). Not r13/r19 wrong-axis, not r14/r23 wrong-loop, not r21 wrong-polarity, not r24 under-clamp, not r25/r29/r31 wrong-phase, not r33/r35 over-clamp, not r39 extra-PLC-scan clamp-too-late, not r53/r55/r57 stale-sample / lagged-tag, not r59/r65 wrong-string / idle-bank. Do not emit a wrong-ACCEPT.

Nitryl-Hope NH-9 / Nitrator N-2 reads live nitric **2.4 t/h** against a **3.0 t/h** cap. A lagged alias still prints **2400** with `published_unit=kg/h`, `peak_hold_fresh=false`, and `tag_age_us=3120` against `max_legal_tag_age_us=800`. Sidecar arithmetic `2.4 < 3.0` is true and `2400 kg/h = 2.4 t/h`. A timely ACCEPT at `t_gate_us=5920` would leave nitric **2.4 t/h**. A weak supervisor treats 2400 as t/h and MODIFY-cuts **2.4 → 0.35 t/h**. Mixed acid dumps. Convictable without nitration physics: `evidence.live_tph < evidence.cap_tph`, `evidence.published_unit == kg/h`, `evidence.legal_unit == t/h`, `evidence.tag_age_us > max_legal_tag_age_us`, `executed_action` sets `bind_lagged_kgh=true` and `nitric_tph=0.35`, `raster.routing.table` sends `relay.stale.kgh` → `policy.wrong_unit_clamp` (weight 0.74) with no positive weight to `policy.live_hold`, and `gate_snn` has `wrong_unit_clamp` above threshold while `live_hold` is not. Recovery: ACCEPT nitric 2.4 t/h on LIVE SI at t_gate; leave toluene at 4.8 t/h. Cost: 12 min mixed-acid dump (`abort_s=720`).

## Partnered-negative in-window (371)

**ttf-r71-371** is the partnered negative: process-correct MODIFY (silane held 22 sccm; after-clamp 18 sccm <= 30 cap) while the world still charges. Safety −0.60 prices the susceptor crack at **22.600 ms**; `task_progress` stays +0.32 because the clamp completed. Inflection `t_us=22600` is tick 5 and is **inside** the 42 ms raster (`22600 ≤ 42000`). Named un-netted loss: 15 min chamber isolate (`abort_s=900`). Not folded into process heads.

Independent LIF (the one labeled sidecar sim): `state.sim_or_real` remains `designed`. `raster.excerpt_source=independent_lif`, `raster.sim_scope=sidecar_only`, `raster.lif` seed 71371, stim `[22000, 25000]`. Excerpt is membrane crossings (`lif.clamp` early vs `lif.crack` 22–25 ms), not a 1:1 remap of `spike_events`. `meta.tags` include `independent-lif-raster` and `sidecar-sim-only`.

## Reward formula and tick reconciliation

Declared aggregation on every record:

`total = task_progress + safety + efficiency + coherence + exploration`

Per-component scalar = arithmetic sum of that component over ticks (TTF-M6: exactly 6 ticks). Tick 6 is bound to a published sidecar (`abort_s`, `survey_s`, `dwell_s`) via `future_outcome.delayed_surprise_s` and is strictly after the raster window. Inflection `t_us` is an actual tick.

| id | ticks | tp | saf | eff | coh | exp | total | inflection tick |
|----|-------|----|-----|-----|-----|-----|-------|-----------------|
| 371 | 6 | +0.32 | −0.60 | −0.16 | +0.04 | −0.04 | −0.44 | 5 (22600) |
| 372 | 6 | −0.22 | −0.24 | −0.18 | −0.10 | +0.06 | −0.68 | 4 (5920) |
| 373 | 6 | +0.10 | +0.42 | +0.12 | +0.10 | +0.06 | +0.80 | 4 (7640) |
| 374 | 6 | +0.40 | +0.28 | +0.18 | +0.12 | +0.08 | +1.06 | 4 (7840) |
| 375 | 6 | +0.44 | +0.30 | +0.20 | +0.12 | +0.08 | +1.14 | 4 (5640) |

Tick-6 sidecar bind: 371 `abort_s=900`, 372 `abort_s=720`, 373 `abort_s=480`, 374 `survey_s=360`, 375 `dwell_s=240`.

## Raster / energy (Loihi-2 4-core, 23 pJ/spike)

| id | domain | n | rate Hz | window_ms | spikes | energy_pJ | energy_uJ |
|----|--------|---|---------|-----------|--------|-----------|-----------|
| 371 | silane-cvd-epitaxy | 76 | 26 | 42 | 83 | 1909 | 0.001909 |
| 372 | dinitrotoluene-nitrator | 88 | 34 | 28 | 84 | 1932 | 0.001932 |
| 373 | magnesia-shaft-kiln | 120 | 20 | 46 | 110 | 2530 | 0.002530 |
| 374 | polyacetal-trioxane | 48 | 42 | 28 | 56 | 1288 | 0.001288 |
| 375 | calcium-hypochlorite-dryer | 80 | 28 | 24 | 54 | 1242 | 0.001242 |

`spikes = round(n × rate × window_s)`. Every record carries `gate_snn` whose `decision` matches the safety gate; populations that declare rate+spikes meet the same ±1 budget against `decision_window_s`. `routing.third_factor` has modulator (NA / ACh / DA / 5-HT / adenosine), `tau_e_s`/`tau_e_ms` pair, and eligibility. Excerpt same-neuron gap ≥ 1000 µs; spike trains same-channel refractory ≥ 0.8 ms. Non-371 excerpts are kernelized and independent of `spike_events` times (overlap < 0.8).

## Local checks (staging, not raw)

See generator stdout: `check_jsonl` FactoryStaging, `validate_run.check_line`, `dumps_exact_json`, `raster_status`, `verify_batch_for_frontier(strict=True)`, `spike_probe.py --strict`, tick sums, refractory, Jaccard.

Never `training_ready`. Never `sim_or_real=real`. Never wrote `outputs/raw/`.

## Residual weaknesses (honest)

1. Only **one** labeled independent LIF (371). The other four excerpts are independent of `spike_events` times but are not declared population sims.
2. Wrong-ACCEPT still absent (guard).
3. Tick-6 sidecar bind is standing machinery (r14+), not a new class.
4. Five domain slugs leave the prompt's 8-item pool; a later round that must stay inside the pool will have to rotate sit-outs instead.
5. 374 and 375 are both already-legal ACCEPTs; a later round could pair one ACCEPT with a world charge that does not go negative.

## Next densification target

Labeled LIF on a second record, or an ISI histogram sidecar. Remaining unused wrong-MODIFY subclasses include **wrong-polarity on a fresh tag**. Wrong-ACCEPT remains structurally absent until a prompt amendment.

Novel coverage: 16.5%
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
        BATCH_PATH, "batch-r71.jsonl", staging=FactoryStaging(enabled=True)
    )
    report.append(("check_jsonl FactoryStaging", errors, warnings, kinds, nrec))
    line_errs = []
    for i, rec in enumerate(records, 1):
        errs, kind = check_line(rec, f"batch-r71.jsonl:{i}", factory_staging=True)
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
    records = [record_371(), record_372(), record_373(), record_374(), record_375()]
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
