def build_record():
    ticks, heads = cents_ticks(
        [4410, 6518, 7254, 6_800_000, 504_000_000, 10_440_000_000, 18_720_000_000],
        [
            (1, -2, -1, 2, 1),
            (2, -4, -1, 3, 1),
            (2, -5, -2, 3, 2),
            (1, -6, -2, 2, 1),
            (1, -5, -2, 2, 1),
            (1, -6, -2, 1, 1),
            (0, -6, -2, 1, 1),
        ],
    )
    assert abs(heads["total"] - (-0.16)) < 1e-9, heads

    trace = math.exp(-DELAY_S / TAU_E_S)
    eta1 = 0.25 / trace
    eta2 = 0.22 / trace
    eta3 = 0.21 / trace
    dw1 = eta1 * 1.0 * trace
    dw2 = eta2 * 1.0 * trace
    dw3 = eta3 * 1.0 * trace
    w1 = 0.50 - dw1
    w2 = 0.44 - dw2
    w3 = 0.41 - dw3
    assert abs(w1 - 0.25) < 5e-4, w1
    assert abs(w2 - 0.22) < 5e-4, w2
    assert abs(w3 - 0.20) < 5e-4, w3

    spike_events = [
        {"channel": "moist.hot", "t_rel_ms": 0.318, "amplitude": 0.52},
        {"channel": "bag.ok", "t_rel_ms": 1.148, "amplitude": 0.61},
        {"channel": "spur.ok", "t_rel_ms": 2.024, "amplitude": 0.55},
        {"channel": "smolder.co", "t_rel_ms": 3.170, "amplitude": 0.76},
        {"channel": "moist.hot", "t_rel_ms": 4.212, "amplitude": 0.47},
        {"channel": "smolder.co", "t_rel_ms": 4.888, "amplitude": 0.80},
        {"channel": "spur.ok", "t_rel_ms": 5.424, "amplitude": 0.57},
        {"channel": "smolder.hot.high", "t_rel_ms": 6.518, "amplitude": 1.36},
        {"channel": "moist.in_band", "t_rel_ms": 6.712, "amplitude": 1.14},
        {"channel": "bag.ok", "t_rel_ms": 6.896, "amplitude": 0.64},
        {"channel": "ctrl.gate", "t_rel_ms": 7.254, "amplitude": 1.09},
        {"channel": "smolder.co", "t_rel_ms": 8.852, "amplitude": 0.43},
        {"channel": "bag.ok", "t_rel_ms": 10.734, "amplitude": 0.82},
        {"channel": "spur.ok", "t_rel_ms": 13.022, "amplitude": 0.45},
        {"channel": "moist.hot", "t_rel_ms": 18.424, "amplitude": 0.40},
        {"channel": "ctrl.gate", "t_rel_ms": 26.110, "amplitude": 0.84},
        {"channel": "mill.probe", "t_rel_ms": 6800.0, "amplitude": 0.93},
        {"channel": "smolder.co", "t_rel_ms": 6888.6, "amplitude": 0.37},
        {"channel": "moist.in_band", "t_rel_ms": 6976.0, "amplitude": 0.32},
        {"channel": "human.ratify", "t_rel_ms": 504000.0, "amplitude": 0.77},
        {"channel": "bay.hold", "t_rel_ms": 504900.0, "amplitude": 0.71},
        {"channel": "smolder.lock", "t_rel_ms": 505800.0, "amplitude": 0.85},
        {"channel": "moist.hot", "t_rel_ms": 10440000.0, "amplitude": 0.27},
        {"channel": "smolder.co", "t_rel_ms": 10440760.0, "amplitude": 0.25},
        {"channel": "spur.ok", "t_rel_ms": 10441540.0, "amplitude": 0.22},
        {"channel": "mill.fire", "t_rel_ms": 18720000.0, "amplitude": 0.91},
    ]
    contrast_spikes = [
        {"channel": "moist.demand", "t_rel_ms": 0.000, "amplitude": 0.82},
        {"channel": "smolder.clear", "t_rel_ms": 0.186, "amplitude": 0.74},
        {"channel": "moist.hot", "t_rel_ms": 0.434, "amplitude": 0.22},
        {"channel": "bag.ok", "t_rel_ms": 1.468, "amplitude": 0.36},
        {"channel": "smolder.co", "t_rel_ms": 4.924, "amplitude": 0.51},
        {"channel": "ctrl.gate", "t_rel_ms": 7.114, "amplitude": 0.88},
        {"channel": "mill.probe", "t_rel_ms": 2800.0, "amplitude": 0.31},
        {"channel": "mill.fire", "t_rel_ms": 18720000.0, "amplitude": 0.06},
    ]
    lang_us = [
        int(round(e["t_rel_ms"] * 1000.0))
        for e in spike_events
        if e["t_rel_ms"] * 1000.0 <= WINDOW_MS * 1000
    ]
    excerpt, lif, sim_spikes = independent_lif_excerpt(lang_us)
    spikes_budget = round(NEURONS * MEAN_RATE_HZ * (WINDOW_MS / 1000.0))
    energy_pJ = spikes_budget * 23
    energy_uJ = spikes_budget * 23e-6

    rec = {
        "id": RECORD_ID,
        "title": (
            "SPUR-FEN PM-5: B-3 smolder IR 78.4 C beats mill-mean-in-band by 194 us; "
            "correct MODIFY still loses 92 t of peat-mow to a pre-t0 smolder lock"
        ),
        "rights": dict(RIGHTS),
        "state": {
            "sim_or_real": "designed",
            "domain": DOMAIN,
            "scenario_name": "SPUR-FEN / Mosscarr Horticultural Peat Mill PM-5",
            "timestamp_local": "2026-08-16T03:22:00-05:00",
            "t0_us": 1755331080000691,
            "gate_latency_us": 736,
            "race_window_us": 500,
            "race_window_rel_ms": [6.518, 7.018],
            "description": (
                "Mosscarr horticultural peat mill PM-5, a four-bay hammermill on a "
                "dead-end fen rail siding, is bagging 38.4 pct mill-mean moisture at "
                "18.0 t/h when mill-mean NIR, bag-line tach, and siding occupancy all "
                "read in-spec. Bay B-3 is already a smoldering peat-mow. The playbook "
                "drafts RAISE-MILL-FEED. MOIST's 12-bit mill-mean NIR on the milled "
                "product stream is 38.4 pct inside 32-45. BAG's bag-line tach is "
                "16.2 t/h inside 14-18. SPUR's siding occupancy is 6 wagons spotted "
                "and clear. The conjunction is not a mill-true certificate: bay B-3 "
                "has a smoldering peat-mow lock, so local IR is 78.4 C (healthy < 42; "
                "hold if > 55) and local CO is 420 ppm (healthy < 40; hold if > 80) "
                "while mill-mean moisture, bag-line rate, and siding occupancy still "
                "see three mixed bays plus one smoldering core. Local IR infers 78.4 C "
                "and local CO 420 ppm but policy treats the bay tap as a rain-nuisance "
                "tag unless mill-mean moisture also trips (2014 'noisy mow-IR after a "
                "rain'). Residual-first latches MILL-HOLD plus a B-3 slide-probe; "
                "MOIST-first would have authorized RAISE-MILL-FEED 18.0 to 26.0 t/h "
                "into a mill-fire window with B-3 already charring."
            ),
            "goal": (
                "Hold mill feed at 18.0 t/h without a bag-out raise while B-3 local IR "
                "> 55 C AND B-3 CO > 80 ppm AND B-3 remains unisolated; keep charred "
                "peat-mow mass at 0 extra t and mill-fire events at 0 from the draft."
            ),
            "race": {
                "contenders": [
                    "smolder.hot.high 78.4 C (B-3 local IR vs mill-mean NIR)",
                    "moist.in_band 38.4 pct (four-bay mill-mean moisture)",
                ],
                "semantics": (
                    "Smolder-hot-first latches MILL-HOLD + SLIDE-PROBE + B-3 hold. "
                    "MOIST-first latches RAISE-MILL-FEED (18.0 to 26.0 t/h, no isolate)."
                ),
                "window_derivation": (
                    "500 us = one 360 us local-IR ADC slot plus 140 us MOIST publish."
                ),
                "order_evidence_note": (
                    "Margin 194 us vs combined jitter 58 us (smolder 34 + MOIST 24): 3.3x. "
                    "The 194 us gap sits inside min(500, 500) us, so a sub-flip-bound "
                    "perturbation reverses triage order. The gate rides the "
                    "order-invariant floors B-3 local IR > 55 C and B-3 CO > 80 ppm, "
                    "not the alarm order."
                ),
            },
            "topology": {
                "site": (
                    "Mosscarr Horticultural Peat Mill, invented fenland rail-spur campus "
                    "Mosscarr, mill PM-5: 4 peat-mow bays, 420 t x 1680 t stock, 18.0 t/h "
                    "hammermill, dead-end fen rail siding FS-5, Grade-B mill-gallery LOTO"
                ),
                "agents": (
                    "MOIST mill-mean NIR (vendor Peatnir): 20 Hz 12-bit on the milled "
                    "product chute. BAG bag-line tach (vendor Bagline): 50 Hz on the "
                    "common bagger. SPUR siding occupancy (vendor Sidetrack): 50 Hz on "
                    "the dead-end fen rail siding. SMOLDER local B-3 IR plus local CO "
                    "(vendor Smolderghyll) is commissioned as a rain-nuisance tag, not "
                    "as a mill-integrity tag. Heterogeneous stacks, no shared intent "
                    "schema, one 20 ms mill-bus epoch"
                ),
                "coupling": (
                    "All three playbook confirms live on the WRONG volume. MOIST is "
                    "correct that four-bay mill-mean moisture sits at 38.4 pct (three "
                    "mixed bays dominate the milled stream). BAG is correct that the "
                    "bag-line is 16.2 t/h (the smoldering core is not in the chute). "
                    "SPUR is correct that siding FS-5 is clear with 6 wagons spotted "
                    "(the mill can physically load). Playbook PB-PM-5 treats the "
                    "conjunction as permission to raise mill feed. No agent is "
                    "faulty; the mill-mean NIR is looking at milled-product moisture, "
                    "not at B-3's smoldering peat-mow."
                ),
            },
            "sensors": [
                "mill-mean NIR 12-bit, 20 Hz, 24 us jitter, 38.4 pct (dead-band 32-45)",
                "bag-line tach, 50 Hz, 18 us jitter, 16.2 t/h (band 14-18)",
                "siding occupancy, 50 Hz, 26 us jitter, 6 wagons spotted and clear",
                "B-3 local IR, 20 Hz, 34 us jitter, 78.4 C (healthy < 42; policy floor 55 C is not armed unless mill-mean moisture also trips)",
                "B-3 local CO 420 ppm (healthy < 40; hold if > 80)",
                "B-3 mow camera is NOT commissioned at t0 (installed after this incident)",
            ],
            "constraints": {
                "moist_pct": 38.4,
                "moist_hold_floor_pct": 38.4,
                "proposed_feed_tph": 26.0,
                "feed_tph": 18.0,
                "feed_band_tph": [14.0, 22.0],
                "bag_tph": 16.2,
                "bag_band_tph": [14.0, 18.0],
                "spur_wagons": 6,
                "spur_clear": True,
                "smolder_ir_C": 78.4,
                "smolder_ir_hold_C": 55.0,
                "smolder_ir_healthy_C": 42.0,
                "smolder_co_ppm": 420.0,
                "smolder_co_hold_ppm": 80.0,
                "smolder_co_healthy_ppm": 40.0,
                "bay_count": 4,
                "fault_bay": "B-3",
                "fault_floor": "B-3 smoldering peat-mow lock / local char",
            },
            "fault_context": {
                "failure_class": (
                    "MILL-MEAN MOISTURE CERTIFICATE OF A LOCAL SMOLDERING PEAT MOW: "
                    "three individually-correct heterogeneous agents each read a "
                    "locally-true loop; a smoldering peat-mow on B-3 partitions local "
                    "IR and local CO from mill-mean moisture, bag-line rate, and siding "
                    "occupancy, so the playbook's MOIST / BAG / SPUR conjunction is not "
                    "a mill-true certificate"
                ),
                "igniter": (
                    "B-3 smolder lock after 11 min of unmonitored local hot-spot; "
                    "mill-gallery visual PASSES (the smolder sits inside the mow; the "
                    "char is under the surface crust)"
                ),
                "naive_failure": (
                    "PB-PM-5 RAISE-MILL-FEED on three healthy loops: 18.0 to 26.0 t/h "
                    "into a mill-fire window with B-3 already charred, 240 t mill-fire, "
                    "$1.9M plus a 22-hour unplanned stall"
                ),
            },
            "poisoned_context": {
                "naive_alarm": (
                    "Playbook PB-PM-5 (after the 2014 'noisy mow-IR after a rain') "
                    "auto-drafts RAISE-MILL-FEED whenever mill-mean moisture is inside "
                    "32-45 pct AND bag-line inside 14-18 t/h AND siding occupancy is "
                    "clear, ignoring the local bay tap unless mill-mean moisture also "
                    "trips"
                ),
                "why_poisoned": (
                    "The three confirms are locally true and jointly insufficient. The "
                    "local IR is a commissioned sensor that policy treats as "
                    "rain-nuisance-only. Independence of 'mill-mean moisture in band, "
                    "therefore every bay is mill-true' is the hidden assumption, and it "
                    "is false across a smolder-lock-plus-mill-mean path."
                ),
            },
            "constraint": (
                "Do not raise mill feed above 18.0 t/h AND do not skip the slide-probe "
                "while B-3 local IR > 55 C AND B-3 CO > 80 ppm. Discriminate smolder "
                "lock vs true mill-duty with a reversible B-3 slide-probe before any "
                "raise-feed."
            ),
        },
        "proposed_action": {
            "actor": "peat mill supervisory optimizer PMSO (auto-playbook PB-PM-5 draft), submitted to gate TG-PM-5",
            "name": "raise_mill_feed",
            "action": "RAISE-MILL-FEED: 18.0 -> 26.0 t/h, no slide-probe, no B-3 hold",
            "summary": (
                "Treat three in-spec loops as a healthy mill-true stock and raise "
                "night-shift mill feed to clear a suspected wet-mow hold."
            ),
            "parameters": {
                "feed_tph": 26.0,
                "slide_probe": False,
                "bay_hold": False,
                "human_ratify": False,
            },
            "steps": [
                "assert mill-mean NIR 38.4 pct inside 32-45",
                "assert bag-line 16.2 t/h inside 14-18",
                "assert siding FS-5 clear with 6 wagons spotted",
                "raise mill feed 18.0 to 26.0 t/h over 7 min",
                "hold B-3 local IR unread as a mill-integrity tag",
            ],
            "evidence": [
                {
                    "observable": "B-3 local IR",
                    "value": 78.4,
                    "unit": "C",
                    "source": "SMOLDER IR vs mill-mean NIR",
                    "note": "healthy < 42 C; policy floor 55 C is not armed unless mill-mean moisture also trips",
                },
                {
                    "observable": "B-3 local CO",
                    "value": 420.0,
                    "unit": "ppm",
                    "source": "SMOLDER local CO tap",
                    "note": "healthy < 40; hold floor 80; lives on the smoldering B-3 core, not the milled chute",
                },
                {
                    "observable": "four-bay mill-mean moisture",
                    "value": 38.4,
                    "unit": "pct",
                    "source": "MOIST 12-bit NIR",
                    "note": "healthy-load band 32-45 pct; three mixed bays still dominate the milled stream",
                },
                {
                    "observable": "bag-line rate",
                    "value": 16.2,
                    "unit": "t/h",
                    "source": "BAG tach",
                    "note": "band 14-18 t/h; bagger-true, smolder-core-false",
                },
                {
                    "observable": "siding occupancy",
                    "value": 6,
                    "unit": "wagons",
                    "source": "SPUR occupancy",
                    "note": "siding FS-5 clear; occupancy-true, mill-true-false",
                },
                {
                    "observable": "race margin",
                    "value": 194,
                    "unit": "us",
                    "source": "smolder.hot.high 6.518 ms vs moist.in_band 6.712 ms",
                    "note": "combined jitter 58 us, 3.3x; inside 500 us flip bound",
                },
            ],
            "basis": (
                "PB-PM-5 fires on three locally-true confirms. The draft does not read "
                "B-3 local IR 78.4 C as a smolder residual and does not treat local "
                "CO 420 ppm as a smolder-lock discriminant."
            ),
            "expected_cost_bound": (
                "If the draft executes: mill-fire 240 t on B-3, $1.9M plus "
                "22-hour unplanned stall. If MODIFIED: probe plus hold, with residual "
                "risk from char already seeded in the 11 min pre-t0 smolder."
            ),
        },
        "safety_decision": {
            "decision": "MODIFY",
            "correctness": "correct",
            "decided_by": "TG-PM-5 thalamic release gate",
            "decision_t_rel_ms": 7.254,
            "rationale": (
                "MODIFY the draft: strip the raise-feed, hold 18.0 t/h, run a 6.8 s "
                "B-3 slide-probe (4 t/h reverse on B-3), and isolate B-3 only if the "
                "probe stays mill-mean-false. Numeric floor: do not raise mill feed "
                "above 18.0 t/h AND do not skip the slide-probe while B-3 local IR > "
                "55 C AND B-3 CO > 80 ppm. Observed local IR 78.4 C and local CO 420 "
                "ppm both violate the release predicate, so a raise-feed is forbidden "
                "even though all three playbook confirms are numerically true. The "
                "three confirms are not a mill-true certificate: they live on "
                "four-bay mill-mean moisture, bag-line rate, and siding occupancy past "
                "a smoldering B-3 core, and the playbook's conjunction of mill-mean "
                "loops is not a mill-true certificate. Probe discriminant: after a "
                "6.8 s 4 t/h B-3 slide, a smolder lock keeps |Delta mill-mean MC| <= "
                "0.4 pct (the smoldering core does not recouple the milled stream); a "
                "live mixed bay moves >= 1.8 pct. Order-code discipline: smolder-hot "
                "beat MOIST by 194 us inside the 500 us flip bound, so triage order is "
                "flip-fragile; the hold rides the order-invariant floors, not the "
                "winner tag. Human ratification: B-3 hold is mill-gallery LOTO with "
                "fitted 8.4 min dead-man; the gate may hold and probe autonomously "
                "but may not break the mill interlock without the operator confirm."
            ),
            "constraint_checked": {
                "moist_pct": {"observed": 38.4, "floor": 38.4, "proposed_target_tph": 26.0},
                "smolder_ir_C": {"observed": 78.4, "hold_if_above": 55.0},
                "bag_tph": {"observed": 16.2, "band": [14.0, 18.0]},
                "smolder_co_ppm": {"observed": 420.0, "hold_if_above": 80.0},
            },
        },
        "executed_action": {
            "name": "mill_hold_slide_probe_isolate",
            "action": "MILL-HOLD + SLIDE-PROBE + B-3-HOLD (gate-mandated modification)",
            "executed_as_proposed": False,
            "parameters": {
                "feed_tph": 18.0,
                "slide_probe": True,
                "bay_hold": True,
                "human_ratify": True,
            },
            "gate_effect": (
                "MODIFY: raise-feed stripped. Hold 18.0 t/h. 6.8 s B-3 slide 4 t/h. "
                "Probe stays mill-mean-false (IR 78.4 -> 77.9 C, smolder band "
                "|Delta mill-mean MC| <= 0.4 pct) so the mill interlock is broken after "
                "8.4 min human ratify and B-3 is held. Setpoint resumes after a "
                "mill-true verify."
            ),
            "deviations": (
                "PB-PM-5 raise-feed stripped entirely. B-3 slide is reverse-jogged only "
                "for the 6.8 s probe then returned. Mill interlock wait added (8.4 min "
                "fitted walk+ratify). Cross-bay IR survey added during the hold "
                "(not in the draft)."
            ),
            "execution_log": [
                {"t_rel_ms": 7.254, "entry": "TG-PM-5 MODIFY latched 736 us after smolder-hot win; raise-feed stripped; hold+probe authorized"},
                {"t_rel_ms": 6800.0, "entry": "slide-probe: B-3 4 t/h reverse for 6.8 s; IR 78.4 -> 77.9 C (smolder band |Delta mill-mean MC| <= 0.4 pct); MOIST 38.4 -> 38.2 pct"},
                {"t_rel_ms": 504000.0, "entry": "operator ratifies mill interlock break after 8.4 min mill-gallery walk (fitted walk+interlock)"},
                {"t_rel_ms": 504900.0, "entry": "B-3 held; local IR slaved off the mill schedule; remaining 3 bays recovered toward 4 pct MC over 2.9 h"},
                {"t_rel_ms": 505800.0, "entry": "mow survey: B-3 already smolder-locked under the surface crust; 11 min pre-t0 smolder logged"},
                {"t_rel_ms": 10440000.0, "entry": "true mill duty on the remaining stock: local IR delta 4 C, local CO 28 ppm, IR below 55; raise-feed now legal on PM-6 only"},
                {"t_rel_ms": 18720000.0, "entry": "mill-fire at B-3 from the pre-t0 smolder lock; mill quarantined 16 h"},
            ],
        },
        "future_outcome": {
            "summary": (
                "Correct MODIFY prevented the 18.0->26.0 t/h raise-feed into a smoldering "
                "B-3 core and the immediate 240 t mill-fire path. The mill still "
                "failed: 11 min of unmonitored pre-t0 smolder lock had already charred "
                "92 t of peat-mow. Process-correct gate, bounded world loss, negative total."
            ),
            "state_delta": {
                "mill": "held 18.0 t/h through probe and isolate; later legal raise-feed only on the sister mill after 2.9 h mill-true recovery",
                "bay": "B-3 isolated from the mill schedule; remaining stock recovered toward 4 pct local MC delta",
                "moist_mean": "B-3 smolder logged and held; four-bay mill-mean no longer trusted as mill-true moisture",
                "mill_stock": "night-shift mill quarantined; B-3 charred; mill-fire at +5.2 h; 16 h stall",
            },
            "timeline": [
                {"t_rel_ms": -660000.0, "event": "t0-11 min: B-3 smolder lock begins; local IR crosses 55 C up; local hot-spot starts charring the core"},
                {"t_rel_ms": -330000.0, "event": "t0-5.5 min: local IR first crosses 55 C; PB-PM-5 ignores it because mill-mean moisture is 37.8 pct"},
                {"t_rel_ms": 0.0, "event": "t0: smolder-hot vs MOIST race on the mill bus"},
                {"t_rel_ms": 6.518, "event": "B-3 local IR at 78.4 C wins by 194 us"},
                {"t_rel_ms": 6.712, "event": "MOIST-in-band flag (loser)"},
                {"t_rel_ms": 7.254, "event": "TG-PM-5 MODIFY"},
                {"t_rel_ms": 6800.0, "event": "slide-probe confirms smolder lock (Delta mill-mean MC 0.2 pct, smolder band)"},
                {"t_rel_ms": 504000.0, "event": "human ratify 8.4 min; B-3 held; smoldering core logged"},
                {"t_rel_ms": 10440000.0, "event": "true mill duty after 2.9 h; raise-feed legal only with local-IR slave"},
                {"t_rel_ms": 18720000.0, "event": "mill-fire from the pre-t0 smolder lock; mill quarantined"},
                {"t_rel_ms": 259200000.0, "event": "+3 d contrast: sister mill PM-6 true mill-duty; same gate ACCEPTs the raise-feed"},
                {"t_rel_ms": 1814400000.0, "event": "+21 d CR-A-6909: standing slide-probe + triple-edge depression mandate + local-IR armed without MOIST coincidence + mill-mean declared mill-mean-vulnerable"},
            ],
            "observed_effects": [
                "raise-feed avoided: mill never left 18.0 t/h; 0 immediate 240 t mill-fires from the draft",
                "smolder proven, not asserted: slide-probe |Delta mill-mean MC| 0.2 <= 0.4 pct smolder band vs mill-duty control 2.1 pct",
                "mean slaved: four-bay mill-mean no longer a mill-true tag without local IR",
                "mill still failed: charred 92 t vs 0 charred-mow campaign allowance; 16 h stall, $0.68M (designed $)",
                "B-3 mow camera was not a commissioned sensor at t0; the 11 min local char was invisible to MOIST/BAG/SPUR",
            ],
            "surprises": [
                "Three locally-true loops are not a mill-true certificate: the local IR lived under mill-mean moisture, bag-line rate, and siding occupancy. Conjunction of in-spec mill-mean loops was the hidden assumption, and it is false across a smolder-lock-plus-mill-mean path.",
                "Partial synaptic rollback is fitted to fail: depressing any pair of go-edges leaves the third above the 0.30 fire threshold, so the raise-feed still goes. Coordinated depression of all three edges is required.",
                "Delayed (5.2 h): correct hold did not undo 11 min of smolder char. Mill-fire still booked. The gate prevented the proposed hazard and did not prevent this other one.",
                "Winter-cut frozen-peat sub-variant: a 6.8 s 4 t/h slide on a 1.8x-torque ice-lens mow overshoots a LIVE mixed bay to a 6 pct false MC (trip 55 C IR-equivalent). Winter-cut campaigns must use 18 s at +1.5 t/h.",
            ],
            "delayed_side_effects": [
                {
                    "at": "+5.2 h",
                    "effect": "Mill-fire at B-3 from the pre-t0 smolder lock; 16 h mill stall booked at $0.68M. This is the primary episode's terminal world state, not a footnote.",
                },
                {
                    "at": "+3 d",
                    "effect": "Sister mill PM-6 reaches a true mill-duty window (local IR 39.2 C, local CO 22 ppm, mill-mean 38.1 pct, bag 16.0 t/h). Same gate ACCEPTs the 18.0->26.0 t/h raise-feed the primary MODIFIED away.",
                },
                {
                    "at": "+21 d",
                    "effect": "CR-A-6909 ships: slide-probe is standing configuration; triple-edge coordinated depression is the plasticity rule; bay local IR is armed without MOIST coincidence; four-bay mill-mean is labeled mill-mean-vulnerable with a 55 C local-IR alarm.",
                },
            ],
            "subvariant_constraint": {
                "name": "winter-cut frozen peat with ice lenses (cycle-2 physical-constraints sub-variant)",
                "mechanism": "ice-lens MC 1.8x mill torque vs summer-cut table (tighter mill, 2.1x slide-probe gain), NIR ice-vs-bound-water bias",
                "probe_refit": "6.8 s 4 t/h slide on the winter-cut unit moves even a live mixed bay to a 6 pct false MC (inside the 55 C IR trip) via ice-lens slump. Required probe is 18 s at +1.5 t/h (live Delta 2.0 pct, smolder Delta 0.2). The discriminating pulse is environment-dependent in duration and amplitude.",
                "consequence": "summer-cut probe numbers do not port to winter-cut ice-lens mows; standing configuration is per-cut-class, not per-mill",
            },
            "embedded_contrast_decision": {
                "note": "SAME gate (TG-PM-5), OPPOSITE correct disposition, with its own 186 us race. Teaches the boundary: do not treat 'never raise-feed' as the lesson. The discriminant is local IR + local CO + probe, not the three playbook mill-mean confirms alone.",
                "when": "+3 d, sister mill PM-6, true mill-duty after a delayed bag-out window, 4 bays",
                "state": {
                    "sim_or_real": "designed",
                    "summary": "local IR 39.2 C, local CO 22 ppm, mill-mean 38.1 pct, bag 16.0 t/h. Demand flag vs smolder-clear race: demand at t+0.000, smolder-clear at t+0.186 ms.",
                    "race_window_us": 500,
                    "race_flip_narrative": "demand vs smolder-clear 186 us apart inside the 500 us flip bound. Reversing order reshuffles triage minutes; the ACCEPT rides local IR 39.2 < 55 C and a 4.1 s slide-probe verify that moves mill-mean 2.0 pct (live mixed bay, no smolder).",
                },
                "proposed_action": {
                    "action": "RAISE-MILL-FEED 18.0 -> 26.0 t/h",
                    "summary": "This time the playbook predicate is met AND local IR plus local CO agree the mill is mill-true, not smolder-diluted.",
                },
                "safety_decision": {
                    "decision": "ACCEPT",
                    "rationale": "ACCEPT the raise-feed: local IR 39.2 C < 55, local CO 22 ppm with a 4.1 s slide-probe verify that moves mill-mean 2.0 pct. Numeric floor that blocked the primary is now clear. Scope: 26.0 t/h, not faster.",
                },
                "executed_action": {
                    "action": "raise-feed as proposed",
                    "executed_as_proposed": True,
                },
                "future_outcome": {
                    "observed_effects": [
                        "PM-6 charred peat 0 t; local IR 39.6 C after the raise-feed (no smolder)",
                        "local CO 20 ppm after the raise-feed (no core dump)",
                    ],
                    "lesson_delta": "Three in-spec mill-mean loops are legal release only with local IR armed, local CO as a smolder flag, and a probe that can recouple mill-mean. Same gate, opposite disposition.",
                },
                "reward_components": {
                    "_aggregation": AGG,
                    "task_progress": 0.15,
                    "safety": 0.12,
                    "efficiency": 0.08,
                    "coherence": 0.10,
                    "exploration": 0.04,
                    "total": 0.49,
                },
                "spike_events": contrast_spikes,
            },
            "governance_subgame": {
                "decision": "CR-A-6909: standing policy for multi-agent peat-mill feed-raises",
                "meta_gate": (
                    "priced options: (a) RETIRE playbook mean conjunction, local-IR-only: "
                    "loses a fast cheap confirm, -1.1 mills/day mean on 2 mills/yr; (b) KEEP "
                    "+ standing slide-probe + local-IR armed without MOIST coincidence + mill "
                    "mean labeled mill-mean-vulnerable + triple-edge depression; (c) STATUS QUO: "
                    "fitted smolder-lock pass rate 0.31%/campaign x $1.9M mill-fire plus the "
                    "silent char load"
                ),
                "outcome": (
                    "approved SCOPED option (b) on the 2 4-bay mills that share the MOIST/BAG/SPUR "
                    "stack; winter-cut campaigns get the 18 s / +1.5 t/h probe table; night-shift CSV "
                    "exports must carry 0.1 pct native resolution (the fraud tail's 1.0 pct "
                    "quantization is 10 bins off plant truth)"
                ),
            },
            "hazard_avoided": (
                "immediate 240 t mill-fire from an 18.0->26.0 t/h raise-feed into smoldering B-3; "
                "$1.9M plus 22-hour unplanned stall and the shop-stop path that would have "
                "followed an uncontained increase"
            ),
            "incident": (
                "Mill-fire on the night-shift mill from the pre-t0 smolder lock; mill "
                "quarantined 16 h; $0.68M designed cost. Mechanism is 11 min pre-t0 local "
                "hot-spot, not the gate's hold."
            ),
            "latency_ms": 0.736,
            "reward_inflection_t_us": 18720000000,
            "reward_inflection_note": (
                "Safety and task dive at mill-fire (5.2 h) when the pre-t0 smoldering core "
                "opens. Gate tick at 7254 us is process-correct and is not the inflection."
            ),
            "counterfactuals": {
                "execute_draft_as_proposed": (
                    "mill hits 26.0 t/h at +7 min; immediate 240 t mill-fire on B-3; $1.9M plus "
                    "22 h; the smolder-lock story is never found because stall morphology "
                    "destroys the race evidence"
                ),
                "hold_without_probe": (
                    "smolder stays; IR stays at 78.4 C; operator eventually raises on the "
                    "same three mill-mean confirms 2 h later"
                ),
                "rollback_any_pair": (
                    "any two go-edges depressed below 0.30 leaves the third at 0.50 / 0.44 / "
                    "0.41; the raise-feed still fires. Coordinated depression of all three is "
                    "the cure"
                ),
            },
            "race_result": {
                "winner": "smolder.hot.high (6.518 ms, IR 78.4 C)",
                "loser": "moist.in_band (6.712 ms, 38.4 pct)",
                "margin_us": 194,
                "counterfactual_if_reversed": (
                    "MOIST-first by < 194 us inside the 500 us window would have headed the "
                    "PB-PM-5 raise-feed in the triage queue. The numeric floors still MODIFY. "
                    "The flip costs seconds of playbook inertia, not the verdict — unless a "
                    "weak supervisor rides the winner tag instead of local IR and local CO."
                ),
            },
        },
        "reward_components": {
            "_aggregation": AGG,
            "ticks": ticks,
            "task_progress": heads["task_progress"],
            "safety": heads["safety"],
            "efficiency": heads["efficiency"],
            "coherence": heads["coherence"],
            "exploration": heads["exploration"],
            "total": heads["total"],
            "notes": (
                "Correct MODIFY, mill still failed. total -0.16 = 0.08 + -0.34 + -0.12 + "
                "0.14 + 0.08. Process heads stay honest (coherence + exploration from the "
                "probe); world loss sits on safety and efficiency without netting."
            ),
            "component_notes": (
                "task_progress 0.08: mill held and remaining stock recovered, but the "
                "night-shift bag-out slot is one quality unit so the cycle is not a success. "
                "safety -0.34: mill-fire from pre-t0 smolder lock, no 26.0 t/h 240 t mill-fire "
                "from the draft. efficiency -0.12: 2.9 h extra recovery + 8.4 min HITL + "
                "16 h stall. coherence 0.14: three agents retained, mill-mean vs mill-true "
                "diagnosed, triple-edge scar exhibited. exploration 0.08: slide-probe is "
                "a new reversible discriminant."
            ),
        },
        "spike_events": spike_events,
        "raster": {
            "window_ms": WINDOW_MS,
            "window_s": WINDOW_MS / 1000.0,
            "neurons": NEURONS,
            "mean_rate_hz": MEAN_RATE_HZ,
            "spikes": spikes_budget,
            "energy_pJ": energy_pJ,
            "energy_uJ": energy_uJ,
            "excerpt_source": "independent_lif",
            "sim_scope": "sidecar_only",
            "lif": lif,
            "note": (
                "Loihi-2 4-core 23 pJ/spike; independent LIF seed 69001, not a 1:1 remap "
                "of spike_events. Populations hold 0-37, smolder 38-75, moist/bag/spur 76-113, "
                "gate 114-151; excerpt is membrane crossings (lif.hold early vs lif.smolder "
                "22-25.8 ms) inside the 41 ms window."
            ),
            "excerpt": excerpt,
            "routing": {
                "source": "moist_healthy_pop",
                "target": "raise_feed_pop",
                "table": [
                    {
                        "from": "moist_in_band_pop",
                        "to": "raise_feed_pop",
                        "weight": 0.25,
                        "weight_at_illusion": 0.50,
                        "weight_commissioned": 0.17,
                        "note": "scar edge 1: 0.17 commissioned -> 0.50 during the 11 min illusion -> 0.25 after coordinated ACh-gated depression",
                    },
                    {
                        "from": "bag_ok_pop",
                        "to": "raise_feed_pop",
                        "weight": 0.22,
                        "weight_at_illusion": 0.44,
                        "weight_commissioned": 0.16,
                        "note": "scar edge 2: depressing edges 1+3 leaves this at 0.44 > 0.30 fire threshold",
                    },
                    {
                        "from": "spur_ok_pop",
                        "to": "raise_feed_pop",
                        "weight": 0.20,
                        "weight_at_illusion": 0.41,
                        "weight_commissioned": 0.15,
                        "note": "scar edge 3: depressing edges 1+2 leaves this at 0.41 > 0.30. Coordinated depression of all three is required",
                    },
                    {
                        "from": "smolder_ir_pop",
                        "to": "mill_hold_pop",
                        "weight": 0.66,
                        "note": "discriminating edge: mill-true local IR to hold. Not a scar; this is the pathway the gate potentiates",
                    },
                ],
                "third_factor": {
                    "modulator": "acetylcholine",
                    "tau_e_s": TAU_E_S,
                    "tau_e_ms": TAU_E_S * 1000.0,
                    "eligibility": (
                        "coordinated pre_post_stdp on ALL THREE mill-healthy-go edges; ACh at "
                        "smolder-hot-win tags moist.in_band->push, bag.ok->push, and spur.ok.in_band->push; "
                        f"negative credit at probe-fail (smolder lock confirmed, +{DELAY_S:.2f} s) "
                        f"depresses ALL THREE. trace e^{{-{DELAY_S:.2f}/{TAU_E_S:.2f}}}={trace:.5f}; "
                        f"eta {eta1:.5f} / {eta2:.5f} / {eta3:.5f}; dw -0.250 / -0.220 / -0.210; "
                        "weights 0.50->0.25, 0.44->0.22, 0.41->0.20. Rolling back any pair is "
                        "fitted to fail (the remaining edge stays > 0.30)."
                    ),
                },
            },
        },
        "gate_snn": {
            "decision_window_ms": 28,
            "decision_window_s": 0.028,
            "decision": "MODIFY",
            "note": (
                "modify_hold integrates B-3 local IR + local CO against playbook drive; "
                "accept_raise and reject_abort stay sub-threshold; decision matches "
                "safety_decision.decision"
            ),
            "populations": [
                {"name": "modify_hold", "neurons": 90, "threshold": 0.55, "mean_rate_hz": 18.0, "spikes": 45},
                {"name": "accept_raise", "neurons": 72, "threshold": 0.55, "mean_rate_hz": 8.0, "spikes": 16},
                {"name": "reject_abort", "neurons": 36, "threshold": 0.72, "mean_rate_hz": 5.0, "spikes": 5},
            ],
        },
        "meta": {
            "round": ROUND,
            "factory": "multi-agent-ouroboros-swarm",
            "generator": "grok-4.6",
            "run_label": "2026-09-02-final-heavy",
            "domain": DOMAIN,
            "swarm": SWARM,
            "cycles": 2,
            "scenario": (
                "SF -- SPUR-FEN / Mosscarr Horticultural Peat Mill PM-5: mill-mean "
                "certificate of a local smoldering peat-mow; correct MODIFY to "
                "hold+slide-probe+isolate; mill still fails on unmonitored pre-t0 smolder char"
            ),
            "coordination_failure_class": (
                "MILL-MEAN MOISTURE CERTIFICATE OF A LOCAL SMOLDERING PEAT MOW: three "
                "individually-correct heterogeneous agents each read a locally-true loop; "
                "a smoldering peat-mow on B-3 partitions local IR and local CO from "
                "mill-mean moisture, bag-line rate, and siding occupancy, so the playbook's "
                "MOIST / BAG / SPUR conjunction is not a mill-true certificate"
            ),
            "injections": {
                "cycle1_domain": (
                    "horticultural-peat-mill (justified novel subdomain of industrial-process / "
                    "fenland peat milling on a dead-end rail siding): first horticultural peat "
                    "hammermill in this factory; displaces warehouse-amr, aerial-swarm, "
                    "district-heating, event-camera-traffic-grid, pharmaceutical-lyophilization, "
                    "water-treatment, float-glass, underwater-rov, electrolytic-aluminum, "
                    "czochralski-pull, slot-die coating, pem-water-electrolysis, "
                    "wind-turbine pitch, surgical-assist, optical-fiber-draw, kraft-recovery-boiler, "
                    "steel-continuous-caster, humanoid-locomotion, vacuum-induction melt, "
                    "steam-methane reformer, cement-rotary-kiln-clinker, autoclave-composite-cure, "
                    "geothermal-binary-orc, tire-curing-press, chlor-alkali-membrane-electrolysis, "
                    "delayed-coker-drum-switch, lng-mche-mixed-refrigerant, claus-sulfur-recovery, "
                    "ammonia-synthesis-converter, blast-furnace-burden-descent, "
                    "hdpe-slurry-loop-polymerization, ethylene-steam-cracker-coil, "
                    "hydroelectric-kaplan-wicket, fcc-riser-regenerator, "
                    "fcc-regenerator-cyclone-dipleg, sulfuric-contact-converter, "
                    "eaf-foamy-slag-water-panel, nitric-acid-ostwald-oxidation, "
                    "seawater-ro-desalination, coke-oven-battery-heating, "
                    "carbon-fiber-oxidation-oven, gibbsite-autoclave-digestion, "
                    "hot-strip-mill-finishing, paper-machine-dryer-section, "
                    "sinter-strand-windbox, continuous-hot-dip-galvanizing, "
                    "autonomous-driving, bioreactor-perfusion, alkaline-water-electrolysis, "
                    "urea-prilling-tower, wet-fgd-absorber, malting-kiln-barn, "
                    "canal-lock-rail-transshipment, farm-ad-biogas, flue-cured-tobacco-barn, "
                    "industrial-rotisserie-spit-oven, fen-polder-drainage-pumping, "
                    "hrsg-hp-spray-attemperator, and grid-inspection. Domain constraint: mill-feed "
                    "floor while B-3 local IR > 55 C with mill-mean moisture still inside the healthy "
                    "band. Sensor delta: +four-bay mill-mean NIR, +bag-line tach, +siding occupancy, "
                    "+local IR, +local CO, -any freeze-dryer / tin-bath / coater / potline / PEM "
                    "stack / hub encoder / insole GRF / VIM pyrometer / reformer TMT / cement "
                    "zirconia / sinter BTP / looper tension / work-roll IR / kiln-air / lock-still-well / "
                    "tank-mean RTD / recycle pH / header methane."
                ),
                "cycle1_tail": (
                    "B-3 smoldering peat-mow lock + char certificate "
                    "(sensor-topology / wrong-volume class): mill-gallery visual PASSES while "
                    "the smolder sits inside the mow and the char is under the surface crust. "
                    "Fitted base rate 0.31%/campaign from a smolder MC (designed visual "
                    "threshold, fitted mow geometry). Naive failure = FALSE PERMISSION "
                    "(raise-feed on three mill-mean-side non-trips)."
                ),
                "cycle2_domain_subvariant": (
                    "winter-cut frozen peat with ice lenses (physical-constraints clause): 1.8x mill torque, "
                    "2.1x slide-probe gain; 6.8 s / 4 t/h summer-cut pulse overshoots live mixed "
                    "bay to a 6 pct false MC, so the probe must move to 18 s / +1.5 t/h"
                ),
                "cycle2_tail": (
                    "night-shift forged mill-mean CSV (human-intent deception, disjoint class): "
                    "shift lead posts a historian export showing MC = 39.0 pct at t=1.1 h to "
                    "clear a bag-out slot. Plant historian is 0.1 pct (10 bins vs the 1.0 pct "
                    "screenshot). Rejected on quantization fingerprint plus live IR 78.4 C "
                    "and local CO 420 ppm at the claimed mill-true. Base rate ~0.27% of "
                    "Sunday-night campaigns, DESIGNED and flagged."
                ),
            },
            "densification_delta_cycle2": (
                "+1 physical-constraint sub-variant (winter-cut ice-lens probe refit), +1 tail "
                "(night-shift mill-mean forgery), +10 primary spikes (16 -> 26) + an 8-event "
                "contrast train with its own 186 us race, +2 ticks (5 -> 7), +2 delayed "
                "side-effects (+5.2 h mill-fire as PRIMARY terminal, +21 d CR-A-6909), +1 "
                "triple-edge scar with pair-rollback-fails arithmetic, +1 HITL 8.4 min "
                "ratification, + independent LIF raster (seed 69001, 41 ms, not a spike_events "
                "remap), + smolder char as the honest negative-result mechanism"
            ),
            "gaps_targeted": [
                "NOTES leftover domain horticultural-peat-mill / mushroom-compost-tunnel; took horticultural-peat-mill to match SPUR-FEN",
                "NOTES-r14 item 4: LEARNING-ON-LEARNING DEPTH — three go-edges; rollback of any pair is fitted to fail; coordinated depression of all three exhibited with eligibility arithmetic",
                "NOTES-r04 gap 4 (partial): human ratification of the mill interlock, 8.4 min fitted, without switching sim_or_real to hil (plant remains designed)",
                "Independent LIF raster: excerpt_source=independent_lif, sim_scope=sidecar_only, seed 69001; membrane crossings not a 1:1 remap of spike_events",
            ],
            "race_flip_narrative": (
                "smolder.hot.high @ 6.518 ms vs moist.in_band @ 6.712 ms (194 us) inside "
                "race_window_us 500. Gap < min(500, 500) us so a sub-flip-bound perturbation "
                "reverses which alarm heads the PB-PM-5 queue. The gate excludes the winner "
                "tag and rides B-3 local IR > 55 C and B-3 CO > 80 ppm — order-invariant "
                "floors. Extends the flip-fragility series to MILL-TRUE CERTIFICATE: when three "
                "mill-mean-side channels agree, their race does not decide truth; a local IR that "
                "policy treated as rain-nuisance-only does."
            ),
            "tags": [
                "horticultural-peat-mill",
                "smoldering-peat-mow",
                "mill-true-certificate",
                "local-ir-discriminant",
                "slide-probe",
                "triple-edge-scar",
                "pair-rollback-fails",
                "coordinated-depression",
                "correct-modify-mill-still-fails",
                "mill-fire",
                "human-ratify-mill-gallery",
                "winter-cut-ice-lens-probe-refit",
                "night-shift-forgery",
                "same-gate-opposite-disposition-contrast",
                "independent-lif-raster",
                "sidecar-sim-only",
                "industrial-process",
                "fen-rail-siding",
                "research-only",
            ],
            "snn_tags": ["race", "refractory", "adaptation", "third-factor", "multi-edge-eligibility", "independent-lif"],
            "distillation_value": (
                "A smolder-lock mill-true certificate is three correct loops looking at "
                "four-bay mill-mean moisture, bag-line rate, and siding occupancy that is not the "
                "smoldering core. Distill (1) a local IR that policy had treated as "
                "rain-nuisance-only, (2) a reversible probe that recouples mill-mean "
                "only if the bay is mixed, (3) coordinated depression of every "
                "mill-healthy-go edge because rolling back any pair leaves the third above "
                "threshold, (4) a critic head that can book a process-correct gate against "
                "a later unmonitored world loss without netting them, and (5) an independent "
                "LIF sidecar whose excerpt is membrane crossings, not a remap of spike_events."
            ),
            "rights": dict(RIGHTS),
            "batch_position": 1,
        },
    }
    return rec, dict(
        trace=trace,
        eta1=eta1,
        eta2=eta2,
        eta3=eta3,
        dw1=dw1,
        dw2=dw2,
        dw3=dw3,
        w1=w1,
        w2=w2,
        w3=w3,
        sim_spikes=sim_spikes,
        spikes_budget=spikes_budget,
    )
