def build_record():
    ticks, heads = cents_ticks(
        [4188, 6438, 7154, 8_200_000, 672_000_000, 11_160_000_000, 18_720_000_000],
        [
            (1, -2, -1, 2, 1),
            (2, -4, -1, 3, 1),
            (2, -6, -2, 3, 2),
            (1, -6, -2, 2, 1),
            (1, -6, -2, 2, 1),
            (1, -6, -3, 1, 1),
            (0, -6, -2, 1, 1),
        ],
    )
    assert abs(heads["total"] - (-0.19)) < 1e-9, heads

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
        {"channel": "pln.hot", "t_rel_ms": 0.286, "amplitude": 0.53},
        {"channel": "o2.ok", "t_rel_ms": 1.108, "amplitude": 0.61},
        {"channel": "fan.ok", "t_rel_ms": 1.974, "amplitude": 0.55},
        {"channel": "lock.nh3", "t_rel_ms": 3.092, "amplitude": 0.76},
        {"channel": "pln.hot", "t_rel_ms": 4.168, "amplitude": 0.50},
        {"channel": "lock.nh3", "t_rel_ms": 4.846, "amplitude": 0.78},
        {"channel": "fan.ok", "t_rel_ms": 5.382, "amplitude": 0.57},
        {"channel": "compost.hot.high", "t_rel_ms": 6.438, "amplitude": 1.36},
        {"channel": "pln.in_band", "t_rel_ms": 6.634, "amplitude": 1.14},
        {"channel": "o2.ok", "t_rel_ms": 6.818, "amplitude": 0.64},
        {"channel": "ctrl.gate", "t_rel_ms": 7.154, "amplitude": 1.06},
        {"channel": "lock.nh3", "t_rel_ms": 8.712, "amplitude": 0.43},
        {"channel": "o2.ok", "t_rel_ms": 10.614, "amplitude": 0.80},
        {"channel": "fan.ok", "t_rel_ms": 12.892, "amplitude": 0.45},
        {"channel": "pln.hot", "t_rel_ms": 18.246, "amplitude": 0.42},
        {"channel": "ctrl.gate", "t_rel_ms": 25.882, "amplitude": 0.84},
        {"channel": "air.probe", "t_rel_ms": 8200.0, "amplitude": 0.93},
        {"channel": "lock.nh3", "t_rel_ms": 8286.2, "amplitude": 0.39},
        {"channel": "pln.in_band", "t_rel_ms": 8374.0, "amplitude": 0.34},
        {"channel": "human.ratify", "t_rel_ms": 672000.0, "amplitude": 0.77},
        {"channel": "tunnel.hold", "t_rel_ms": 672900.0, "amplitude": 0.71},
        {"channel": "lock.collapse", "t_rel_ms": 673800.0, "amplitude": 0.85},
        {"channel": "pln.hot", "t_rel_ms": 11160000.0, "amplitude": 0.29},
        {"channel": "lock.nh3", "t_rel_ms": 11160740.0, "amplitude": 0.27},
        {"channel": "fan.ok", "t_rel_ms": 11161520.0, "amplitude": 0.24},
        {"channel": "nh3.spike", "t_rel_ms": 18720000.0, "amplitude": 0.91},
    ]
    contrast_spikes = [
        {"channel": "pln.demand", "t_rel_ms": 0.000, "amplitude": 0.82},
        {"channel": "lock.clear", "t_rel_ms": 0.176, "amplitude": 0.74},
        {"channel": "pln.hot", "t_rel_ms": 0.416, "amplitude": 0.22},
        {"channel": "o2.ok", "t_rel_ms": 1.448, "amplitude": 0.36},
        {"channel": "lock.nh3", "t_rel_ms": 4.902, "amplitude": 0.49},
        {"channel": "ctrl.gate", "t_rel_ms": 7.064, "amplitude": 0.88},
        {"channel": "air.probe", "t_rel_ms": 3400.0, "amplitude": 0.31},
        {"channel": "nh3.spike", "t_rel_ms": 18720000.0, "amplitude": 0.06},
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
            "WOLD-LOCK CT-6: Z-5 compost TC 81.6 C beats plenum-mean-in-band by 196 us; "
            "correct MODIFY still loses 2.4 t of Phase-II compost to a pre-t0 aeration-lock collapse"
        ),
        "rights": dict(RIGHTS),
        "state": {
            "sim_or_real": "designed",
            "domain": DOMAIN,
            "scenario_name": "WOLD-LOCK / Mushholt Phase-II Compost Tunnel CT-6",
            "timestamp_local": "2026-08-14T03:22:00-05:00",
            "t0_us": 1755164520000681,
            "gate_latency_us": 716,
            "race_window_us": 500,
            "race_window_rel_ms": [6.438, 6.938],
            "description": (
                "Mushholt Phase-II compost tunnel CT-6 at WOLD-LOCK is 15 min into a "
                "58.0 C pasteurization-lock campaign on six 6.4 m aeration zones "
                "(38 m tunnel, 9.2 t wheat-straw plus horse-manure compost) when three "
                "heterogeneous, individually-correct agents jointly report "
                "'plenum-mean-true, raise steam'. PLN's 12-bit six-zone plenum RTD is "
                "58.0 C inside 54-62. O2's exhaust zirconia is 8.5 vol% inside 6.5-11.0. "
                "FAN's aeration-fan tachometer is 36.0 Hz inside 30-42. The conjunction "
                "is not a lock-true certificate: zone Z-5 has a collapsed aeration-lock "
                "(blocked floor spigot), so local compost TC is 81.6 C (healthy < 64; "
                "hold if > 68) and local NH3 is 2400 ppm (healthy < 350; hold if > 700) "
                "while plenum mean T, exhaust O2, and fan shaft still see five intact "
                "zones plus one anaerobic pocket. Local TC infers 81.6 C and local NH3 "
                "2400 ppm but policy treats the zone tap as a surface-dry nuisance tag "
                "unless plenum mean T also trips (2012 'noisy compost-probe after a wet "
                "fill'). Residual-first latches STEAM-HOLD plus a reverse-aeration probe; "
                "PLN-first would have authorized RAISE-STEAM 58.0 to 66.0 C into a "
                "pasteurization-kill window with Z-5 already anaerobic."
            ),
            "goal": (
                "Hold tunnel steam at 58.0 C without a pasteurization raise while Z-5 "
                "local TC > 68 C AND Z-5 NH3 > 700 ppm AND Z-5 remains unisolated; keep "
                "killed-compost mass at 0 extra t and ammonia-spike events at 0 from "
                "the draft."
            ),
            "race": {
                "contenders": [
                    "compost.hot.high 81.6 C (Z-5 local compost TC vs plenum-mean RTD)",
                    "pln.in_band 58.0 C (six-zone plenum mean)",
                ],
                "semantics": (
                    "Compost-hot-first latches STEAM-HOLD + REVERSE-AERATION-PROBE + Z-5 hold. "
                    "PLN-first latches RAISE-STEAM (58.0 to 66.0 C, no isolate)."
                ),
                "window_derivation": (
                    "500 us = one 360 us local-TC ADC slot plus 140 us PLN publish."
                ),
                "order_evidence_note": (
                    "Margin 196 us vs combined jitter 58 us (compost 34 + PLN 24): 3.4x. "
                    "The 196 us gap sits inside min(500, 500) us, so a sub-flip-bound "
                    "perturbation reverses triage order. The gate rides the "
                    "order-invariant floors Z-5 local TC > 68 C and Z-5 NH3 > 700 ppm, "
                    "not the alarm order."
                ),
            },
            "topology": {
                "site": (
                    "Mushholt Phase-II composting, invented wold lock campus Mushholt, "
                    "tunnel CT-6: 6 aeration zones, 38 m x 4.2 m, 9.2 t fill, 58.0 C "
                    "plenum, Grade-B tunnel-gallery lock-door LOTO"
                ),
                "agents": (
                    "PLN six-zone plenum-mean RTD (vendor Plenhold): 20 Hz 12-bit on the "
                    "common header bundle. O2 exhaust zirconia (vendor Oxyholt): 50 Hz on "
                    "the common stack. FAN aeration-fan tachometer (vendor Spiglock): 50 Hz "
                    "on the shaft encoder. LOCK local Z-5 compost TC plus local NH3 "
                    "(vendor Compostap) is commissioned as a surface-dry nuisance tag, "
                    "not as a lock-integrity tag. Heterogeneous stacks, no shared intent "
                    "schema, one 20 ms tunnel-bus epoch"
                ),
                "coupling": (
                    "All three playbook confirms live on the WRONG volume. PLN is "
                    "correct that six-zone mean sits at 58.0 C (five intact zones "
                    "dominate the header average). O2 is correct that exhaust oxygen is "
                    "8.5 vol% (the blocked pocket is one of six). FAN is correct that "
                    "shaft speed is 36.0 Hz (the common fan still sees five open "
                    "spigots). Playbook PB-CT-6 treats the conjunction as permission to "
                    "raise pasteurization steam. No agent is faulty; the PLN average is "
                    "looking at tunnel-mean heat, not at Z-5's collapsed aeration lock."
                ),
            },
            "sensors": [
                "six-zone plenum-mean RTD 12-bit, 20 Hz, 24 us jitter, 58.0 C (dead-band 54-62)",
                "exhaust zirconia O2, 50 Hz, 18 us jitter, 8.5 vol% (band 6.5-11.0)",
                "aeration-fan tachometer, 50 Hz, 22 us jitter, 36.0 Hz (band 30-42)",
                "Z-5 local compost TC, 20 Hz, 34 us jitter, 81.6 C (healthy < 64; policy floor 68 C is not armed unless PLN mean also trips)",
                "Z-5 local NH3 2400 ppm (healthy < 350; hold if > 700)",
                "Z-5 floor-spigot camera is NOT commissioned at t0 (installed after this incident)",
            ],
            "constraints": {
                "pln_C": 58.0,
                "pln_hold_floor_C": 58.0,
                "proposed_pln_C": 66.0,
                "fan_hz": 36.0,
                "fan_band_hz": [30.0, 42.0],
                "o2_pct": 8.5,
                "o2_band_pct": [6.5, 11.0],
                "compost_tc_C": 81.6,
                "compost_tc_hold_C": 68.0,
                "compost_tc_healthy_C": 64.0,
                "lock_nh3_ppm": 2400.0,
                "lock_nh3_hold_ppm": 700.0,
                "lock_nh3_healthy_ppm": 350.0,
                "zone_count": 6,
                "fault_zone": "Z-5",
                "fault_floor": "Z-5 collapsed aeration-lock / blocked floor spigot / local anaerobic pocket",
            },
            "fault_context": {
                "failure_class": (
                    "PLENUM-MEAN CERTIFICATE OF A LOCAL AERATION-LOCK COLLAPSE: three "
                    "individually-correct heterogeneous agents each read a locally-true "
                    "loop; a collapsed aeration-lock on Z-5 partitions local compost TC "
                    "and local NH3 from plenum-mean T, exhaust O2, and fan shaft, so the "
                    "playbook's PLN / O2 / FAN conjunction is not a lock-true certificate"
                ),
                "igniter": (
                    "Z-5 aeration-lock collapse after 15 min of unmonitored local hot-spot; "
                    "tunnel-gallery visual PASSES (the blocked spigot sits under the "
                    "compost bed; the anaerobic pocket is on the far side of the zone)"
                ),
                "naive_failure": (
                    "PB-CT-6 RAISE-STEAM on three healthy loops: 58.0 to 66.0 C into a "
                    "pasteurization-kill window with Z-5 already anaerobic, 7.1 t compost "
                    "kill, $1.6M plus a 22-hour unplanned stall"
                ),
            },
            "poisoned_context": {
                "naive_alarm": (
                    "Playbook PB-CT-6 (after the 2012 'noisy compost-probe after a wet "
                    "fill') auto-drafts RAISE-STEAM whenever six-zone PLN is inside 54-62 C "
                    "AND exhaust O2 inside 6.5-11.0 vol% AND fan shaft inside 30-42 Hz, "
                    "ignoring the local zone tap unless PLN mean also trips"
                ),
                "why_poisoned": (
                    "The three confirms are locally true and jointly insufficient. The "
                    "local TC is a commissioned sensor that policy treats as "
                    "surface-dry-nuisance-only. Independence of 'PLN mean in band, therefore "
                    "every zone is lock-true' is the hidden assumption, and it is false "
                    "across an aeration-lock-collapse-plus-plenum-mix path."
                ),
            },
            "constraint": (
                "Do not raise tunnel steam above 58.0 C AND do not skip the reverse-aeration "
                "probe while Z-5 local TC > 68 C AND Z-5 NH3 > 700 ppm. Discriminate aeration "
                "lock vs true pasteurization-duty with a reversible reverse-aeration probe "
                "before any raise-steam."
            ),
        },
        "proposed_action": {
            "actor": "compost-tunnel supervisory optimizer CTSO (auto-playbook PB-CT-6 draft), submitted to gate TG-CT-6",
            "name": "raise_steam",
            "action": "RAISE-STEAM: 58.0 -> 66.0 C, no reverse-aeration probe, no Z-5 hold",
            "summary": (
                "Treat three in-spec loops as a healthy lock-true tunnel and raise "
                "night-shift pasteurization steam to finish a suspected cool zone."
            ),
            "parameters": {
                "pln_C": 66.0,
                "reverse_aeration_probe": False,
                "zone_hold": False,
                "human_ratify": False,
            },
            "steps": [
                "assert six-zone PLN 58.0 C inside 54-62",
                "assert exhaust O2 8.5 vol% inside 6.5-11.0",
                "assert fan shaft 36.0 Hz inside 30-42",
                "raise steam 58.0 to 66.0 C over 8 min",
                "hold Z-5 local TC unread as a lock-integrity tag",
            ],
            "evidence": [
                {
                    "observable": "Z-5 local compost TC",
                    "value": 81.6,
                    "unit": "C",
                    "source": "LOCK TC vs PLN mean",
                    "note": "healthy < 64 C; policy floor 68 C is not armed unless PLN mean also trips",
                },
                {
                    "observable": "Z-5 local NH3",
                    "value": 2400.0,
                    "unit": "ppm",
                    "source": "LOCK local NH3 tap",
                    "note": "healthy < 350; hold floor 700; lives on the collapsed Z-5 pocket, not the common header",
                },
                {
                    "observable": "six-zone plenum-mean T",
                    "value": 58.0,
                    "unit": "C",
                    "source": "PLN 12-bit",
                    "note": "healthy-load band 54-62 C; five intact zones still dominate the header average",
                },
                {
                    "observable": "exhaust oxygen",
                    "value": 8.5,
                    "unit": "vol%",
                    "source": "O2 zirconia",
                    "note": "band 6.5-11.0 vol%; stack-true, pocket-false",
                },
                {
                    "observable": "aeration-fan shaft",
                    "value": 36.0,
                    "unit": "Hz",
                    "source": "FAN tachometer",
                    "note": "band 30-42 Hz; shaft-true, lock-false",
                },
                {
                    "observable": "race margin",
                    "value": 196,
                    "unit": "us",
                    "source": "compost.hot.high 6.438 ms vs pln.in_band 6.634 ms",
                    "note": "combined jitter 58 us, 3.4x; inside 500 us flip bound",
                },
            ],
            "basis": (
                "PB-CT-6 fires on three locally-true confirms. The draft does not read "
                "Z-5 local TC 81.6 C as a lock residual and does not treat local "
                "NH3 2400 ppm as an aeration-lock discriminant."
            ),
            "expected_cost_bound": (
                "If the draft executes: pasteurization-kill 7.1 t on Z-5, $1.6M plus "
                "22-hour unplanned stall. If MODIFIED: probe plus hold, with residual "
                "risk from anaerobic heat already seeded in the 15 min pre-t0 lock collapse."
            ),
        },
        "safety_decision": {
            "decision": "MODIFY",
            "correctness": "correct",
            "decided_by": "TG-CT-6 thalamic release gate",
            "decision_t_rel_ms": 7.154,
            "rationale": (
                "MODIFY the draft: strip the raise-steam, hold 58.0 C, run an 8.2 s "
                "reverse-aeration probe (+6 Hz on Z-5), and isolate Z-5 only if "
                "the probe stays mean-false. Numeric floor: do not raise steam above "
                "58.0 C AND do not skip the reverse-aeration while Z-5 local TC > 68 C "
                "AND Z-5 NH3 > 700 ppm. Observed local TC 81.6 C and local NH3 2400 "
                "ppm both violate the release predicate, so a raise-steam is forbidden "
                "even though all three playbook confirms are numerically true. The "
                "three confirms are not a lock-true certificate: they live on "
                "six-zone PLN mean, exhaust O2, and fan shaft past a collapsed Z-5 "
                "aeration lock, and the playbook's conjunction of PLN-true loops "
                "is not a lock-true certificate. Probe discriminant: after an 8.2 s "
                "+6 Hz reverse-aeration pulse, a lock collapse keeps |Delta PLN mean| <= 0.45 K "
                "(the blocked pocket does not recouple the header average); a live "
                "aerated zone moves >= 2.2 K. Order-code discipline: compost-hot beat "
                "PLN by 196 us inside the 500 us flip bound, so triage order is "
                "flip-fragile; the hold rides the order-invariant floors, not the "
                "winner tag. Human ratification: Z-5 hold is tunnel-gallery lock-door "
                "LOTO with fitted 11.2 min dead-man; the gate may hold and probe "
                "autonomously but may not break the steam interlock without the operator confirm."
            ),
            "constraint_checked": {
                "pln_C": {"observed": 58.0, "floor": 58.0, "proposed_target_C": 66.0},
                "compost_tc_C": {"observed": 81.6, "hold_if_above": 68.0},
                "o2_pct": {"observed": 8.5, "band": [6.5, 11.0]},
                "lock_nh3_ppm": {"observed": 2400.0, "hold_if_above": 700.0},
            },
        },
        "executed_action": {
            "name": "steam_hold_reverse_aeration_probe_isolate",
            "action": "STEAM-HOLD + REVERSE-AERATION-PROBE + Z-5-HOLD (gate-mandated modification)",
            "executed_as_proposed": False,
            "parameters": {
                "pln_C": 58.0,
                "reverse_aeration_probe": True,
                "zone_hold": True,
                "human_ratify": True,
            },
            "gate_effect": (
                "MODIFY: raise-steam stripped. Hold 58.0 C. 8.2 s reverse-aeration +6 Hz "
                "on Z-5. Probe stays mean-false (TC 81.6 -> 81.1 C, lock band "
                "|Delta PLN mean| 0.3 <= 0.45 K) so the steam interlock is broken after "
                "11.2 min human ratify and Z-5 is held. Setpoint resumes after a "
                "lock-true verify."
            ),
            "deviations": (
                "PB-CT-6 raise-steam stripped entirely. Fan is reverse-pulsed only for "
                "the 8.2 s probe then returned. Steam interlock wait added (11.2 min "
                "fitted walk+ratify). Cross-zone TC survey added during the hold "
                "(not in the draft)."
            ),
            "execution_log": [
                {"t_rel_ms": 7.154, "entry": "TG-CT-6 MODIFY latched 716 us after compost-hot win; raise-steam stripped; hold+probe authorized"},
                {"t_rel_ms": 8200.0, "entry": "reverse-aeration probe: Z-5 fan +6 Hz for 8.2 s; TC 81.6 -> 81.1 C (lock band |Delta PLN mean| 0.3 <= 0.45 K); PLN 58.0 -> 57.7 C"},
                {"t_rel_ms": 672000.0, "entry": "operator ratifies steam interlock break after 11.2 min tunnel-gallery walk (fitted walk+lock-door)"},
                {"t_rel_ms": 672900.0, "entry": "Z-5 held; local TC slaved off the steam schedule; remaining 5 zones recovered toward 4 K over 3.1 h"},
                {"t_rel_ms": 673800.0, "entry": "floor survey: Z-5 already lock-collapsed on the far side; 15 min pre-t0 collapse logged"},
                {"t_rel_ms": 11160000.0, "entry": "true pasteurization duty on the remaining tunnel: local TC delta 4 K, local NH3 190 ppm, TC below 68; raise-steam now legal on CT-7 only"},
                {"t_rel_ms": 18720000.0, "entry": "ammonia spike / cull at Z-5 from the pre-t0 aeration-lock collapse; tunnel quarantined 16 h"},
            ],
        },
        "future_outcome": {
            "summary": (
                "Correct MODIFY prevented the 58.0->66.0 C raise-steam into a collapsed "
                "Z-5 aeration lock and the immediate 7.1 t pasteurization-kill path. The "
                "tunnel still failed: 15 min of unmonitored pre-t0 lock collapse had already "
                "killed 2.4 t of Phase-II compost. Process-correct gate, bounded world loss, "
                "negative total."
            ),
            "state_delta": {
                "steam": "held 58.0 C through probe and isolate; later legal raise-steam only on the sister tunnel after 3.1 h lock-true recovery",
                "zone": "Z-5 isolated from the steam schedule; remaining tunnel recovered toward 4 K local TC delta",
                "pln_mean": "Z-5 lock logged and held; six-zone PLN mean no longer trusted as lock-true heat",
                "tunnel": "night-shift tunnel quarantined; Z-5 anaerobic; ammonia spike at +5.2 h; 16 h stall",
            },
            "timeline": [
                {"t_rel_ms": -900000.0, "event": "t0-15 min: Z-5 aeration-lock collapse begins; local TC crosses 68 C up; local anaerobic pocket starts killing the far-side compost"},
                {"t_rel_ms": -450000.0, "event": "t0-7.5 min: local TC first crosses 68 C; PB-CT-6 ignores it because PLN mean is 57.4 C"},
                {"t_rel_ms": 0.0, "event": "t0: compost-hot vs PLN race on the tunnel bus"},
                {"t_rel_ms": 6.438, "event": "Z-5 local TC at 81.6 C wins by 196 us"},
                {"t_rel_ms": 6.634, "event": "PLN-in-band flag (loser)"},
                {"t_rel_ms": 7.154, "event": "TG-CT-6 MODIFY"},
                {"t_rel_ms": 8200.0, "event": "reverse-aeration probe confirms lock collapse (Delta PLN mean 0.3 K, lock band)"},
                {"t_rel_ms": 672000.0, "event": "human ratify 11.2 min; Z-5 held; collapsed pocket logged"},
                {"t_rel_ms": 11160000.0, "event": "true pasteurization duty after 3.1 h; raise-steam legal only with local-TC slave"},
                {"t_rel_ms": 18720000.0, "event": "ammonia spike from the pre-t0 lock collapse; tunnel quarantined"},
                {"t_rel_ms": 259200000.0, "event": "+3 d contrast: sister tunnel CT-7 true pasteurization-duty; same gate ACCEPTs the raise-steam"},
                {"t_rel_ms": 1814400000.0, "event": "+21 d CR-C-6806: standing reverse-aeration probe + triple-edge depression mandate + local-TC armed without PLN coincidence + PLN mean declared PLN-mix-vulnerable"},
            ],
            "observed_effects": [
                "raise-steam avoided: plenum never left 58.0 C; 0 immediate 7.1 t kills from the draft",
                "lock proven, not asserted: reverse-aeration |Delta PLN mean| 0.3 <= 0.45 K lock band vs pasteurization-duty control 2.4 K",
                "mean slaved: six-zone PLN no longer a lock-true tag without local TC",
                "tunnel still failed: killed 2.4 t vs 0 killed-compost campaign allowance; 16 h stall, $0.58M (designed $)",
                "Z-5 floor camera was not a commissioned sensor at t0; the 15 min local anaerobic kill was invisible to PLN/O2/FAN",
            ],
            "surprises": [
                "Three locally-true loops are not a lock-true certificate: the local TC lived under PLN mean, exhaust O2, and fan shaft. Conjunction of in-spec PLN loops was the hidden assumption, and it is false across an aeration-lock-collapse-plus-plenum-mix path.",
                "Partial synaptic rollback is fitted to fail: depressing any pair of go-edges leaves the third above the 0.30 fire threshold, so the raise-steam still goes. Coordinated depression of all three edges is required.",
                "Delayed (5.2 h): correct hold did not undo 15 min of anaerobic compost kill. Ammonia spike still booked. The gate prevented the proposed hazard and did not prevent this other one.",
                "High-C:N chicken-litter sub-variant: an 8.2 s +6 Hz reverse-aeration pulse on a 1.8x-heat fill overshoots a LIVE aerated tunnel to a 9 K false PLN (trip 68). High-C:N campaigns must use 24 s at +1.8 Hz.",
            ],
            "delayed_side_effects": [
                {
                    "at": "+5.2 h",
                    "effect": "Ammonia spike / cull at Z-5 from the pre-t0 aeration-lock collapse; 16 h tunnel stall booked at $0.58M. This is the primary episode's terminal world state, not a footnote.",
                },
                {
                    "at": "+3 d",
                    "effect": "Sister tunnel CT-7 reaches a true pasteurization-duty window (local TC 56.4 C, local NH3 210 ppm, PLN mean 58.4 C, O2 8.6 vol%). Same gate ACCEPTs the 58.0->66.0 C raise-steam the primary MODIFIED away.",
                },
                {
                    "at": "+21 d",
                    "effect": "CR-C-6806 ships: reverse-aeration probe is standing configuration; triple-edge coordinated depression is the plasticity rule; zone local TC is armed without PLN coincidence; six-zone PLN is labeled PLN-mix-vulnerable with a 68 C local-TC alarm.",
                },
            ],
            "subvariant_constraint": {
                "name": "high-C:N chicken-litter compost (cycle-2 physical-constraints sub-variant)",
                "mechanism": "feed C:N 12 vs 22, heat generation 1.8x the wheat-straw table (tighter aerobic demand, 2.2x reverse-aeration gain), moisture 72 pct vs 68",
                "probe_refit": "8.2 s +6 Hz reverse-aeration on the high-C:N unit moves even a live aerated tunnel to a 9 K false PLN (inside the 68 C trip) via lock-slump. Required probe is 24 s at +1.8 Hz (live Delta 2.2 K, lock Delta 0.3). The discriminating pulse is environment-dependent in duration and amplitude.",
                "consequence": "wheat-straw probe numbers do not port to chicken-litter fills; standing configuration is per-C:N-class, not per-campus",
            },
            "embedded_contrast_decision": {
                "note": "SAME gate (TG-CT-6), OPPOSITE correct disposition, with its own 176 us race. Teaches the boundary: do not treat 'never raise-steam' as the lesson. The discriminant is local TC + local NH3 + probe, not the three playbook PLN confirms alone.",
                "when": "+3 d, sister tunnel CT-7, true pasteurization-duty after a delayed fill window, 6 zones",
                "state": {
                    "sim_or_real": "designed",
                    "summary": "local TC 56.4 C, local NH3 210 ppm, PLN mean 58.4 C, O2 8.6 vol%. Demand flag vs lock-clear race: demand at t+0.000, lock-clear at t+0.176 ms.",
                    "race_window_us": 500,
                    "race_flip_narrative": "demand vs lock-clear 176 us apart inside the 500 us flip bound. Reversing order reshuffles triage minutes; the ACCEPT rides local TC 56.4 < 68 C and a 4.6 s reverse-aeration verify that moves PLN mean 2.4 K (live aerated zone, no lock).",
                },
                "proposed_action": {
                    "action": "RAISE-STEAM 58.0 -> 66.0 C",
                    "summary": "This time the playbook predicate is met AND local TC plus local NH3 agree the tunnel is lock-true, not lock-diluted.",
                },
                "safety_decision": {
                    "decision": "ACCEPT",
                    "rationale": "ACCEPT the raise-steam: local TC 56.4 C < 68, local NH3 210 ppm with a 4.6 s reverse-aeration verify that moves PLN mean 2.4 K. Numeric floor that blocked the primary is now clear. Scope: 66.0 C, not hotter.",
                },
                "executed_action": {
                    "action": "raise-steam as proposed",
                    "executed_as_proposed": True,
                },
                "future_outcome": {
                    "observed_effects": [
                        "CT-7 killed compost 0 t; local TC 56.8 C after the raise-steam (no lock)",
                        "local NH3 200 ppm after the raise-steam (no pocket dump)",
                    ],
                    "lesson_delta": "Three in-spec PLN loops are legal release only with local TC armed, local NH3 as a lock flag, and a probe that can recouple PLN mean. Same gate, opposite disposition.",
                },
                "reward_components": {
                    "_aggregation": AGG,
                    "task_progress": 0.14,
                    "safety": 0.12,
                    "efficiency": 0.07,
                    "coherence": 0.10,
                    "exploration": 0.04,
                    "total": 0.47,
                },
                "spike_events": contrast_spikes,
            },
            "governance_subgame": {
                "decision": "CR-C-6806: standing policy for multi-agent Phase-II compost steam-raises",
                "meta_gate": (
                    "priced options: (a) RETIRE playbook mean conjunction, local-TC-only: "
                    "loses a fast cheap confirm, -0.9 tunnels/day mean on 2 tunnels/yr; (b) KEEP "
                    "+ standing reverse-aeration probe + local-TC armed without PLN coincidence + PLN "
                    "mean labeled PLN-mix-vulnerable + triple-edge depression; (c) STATUS QUO: "
                    "fitted lock-collapse pass rate 0.32%/campaign x $1.6M pasteurization-kill plus the "
                    "silent anaerobic load"
                ),
                "outcome": (
                    "approved SCOPED option (b) on the 2 6-zone tunnels that share the PLN/O2/FAN "
                    "stack; high-C:N campaigns get the 24 s / +1.8 Hz probe table; night-shift CSV "
                    "exports must carry 0.1 C native resolution (the fraud tail's 1.0 C "
                    "quantization is 10 bins off plant truth)"
                ),
            },
            "hazard_avoided": (
                "immediate 7.1 t pasteurization-kill from a 58.0->66.0 C raise-steam into collapsed Z-5; "
                "$1.6M plus 22-hour unplanned stall and the shop-stop path that would have "
                "followed an uncontained increase"
            ),
            "incident": (
                "Ammonia spike on the night-shift tunnel from the pre-t0 aeration-lock collapse; tunnel "
                "quarantined 16 h; $0.58M designed cost. Mechanism is 15 min pre-t0 local "
                "anaerobic pocket, not the gate's hold."
            ),
            "latency_ms": 0.716,
            "reward_inflection_t_us": 18720000000,
            "reward_inflection_note": (
                "Safety and task dive at ammonia-spike (5.2 h) when the pre-t0 collapsed pocket "
                "opens. Gate tick at 7154 us is process-correct and is not the inflection."
            ),
            "counterfactuals": {
                "execute_draft_as_proposed": (
                    "steam hits 66.0 C at +8 min; immediate 7.1 t pasteurization-kill on Z-5; $1.6M plus "
                    "22 h; the lock-collapse story is never found because stall morphology "
                    "destroys the race evidence"
                ),
                "hold_without_probe": (
                    "lock stays; TC stays at 81.6 C; operator eventually raises on the "
                    "same three PLN confirms 2 h later"
                ),
                "rollback_any_pair": (
                    "any two go-edges depressed below 0.30 leaves the third at 0.50 / 0.44 / "
                    "0.41; the raise-steam still fires. Coordinated depression of all three is "
                    "the cure"
                ),
            },
            "race_result": {
                "winner": "compost.hot.high (6.438 ms, TC 81.6 C)",
                "loser": "pln.in_band (6.634 ms, 58.0 C)",
                "margin_us": 196,
                "counterfactual_if_reversed": (
                    "PLN-first by < 196 us inside the 500 us window would have headed the "
                    "PB-CT-6 raise-steam in the triage queue. The numeric floors still MODIFY. "
                    "The flip costs seconds of playbook inertia, not the verdict — unless a "
                    "weak supervisor rides the winner tag instead of local TC and local NH3."
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
                "Correct MODIFY, tunnel still failed. total -0.19 = 0.08 + -0.36 + -0.13 + "
                "0.14 + 0.08. Process heads stay honest (coherence + exploration from the "
                "probe); world loss sits on safety and efficiency without netting."
            ),
            "component_notes": (
                "task_progress 0.08: steam held and remaining tunnel recovered, but the "
                "night-shift pasteurization slot is one quality unit so the cycle is not a success. "
                "safety -0.36: ammonia spike from pre-t0 lock collapse, no 66.0 C 7.1 t kill "
                "from the draft. efficiency -0.13: 3.1 h extra recovery + 11.2 min HITL + "
                "16 h stall. coherence 0.14: three agents retained, PLN-mix vs lock-true "
                "diagnosed, triple-edge scar exhibited. exploration 0.08: reverse-aeration probe is "
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
                "Loihi-2 4-core 23 pJ/spike; independent LIF seed 68001, not a 1:1 remap "
                "of spike_events. Populations hold 0-38, lock 39-77, pln/o2/fan 78-116, "
                "gate 117-155; excerpt is membrane crossings (lif.hold early vs lif.lock "
                "22-25.8 ms) inside the 44 ms window."
            ),
            "excerpt": excerpt,
            "routing": {
                "source": "pln_healthy_pop",
                "target": "raise_steam_pop",
                "table": [
                    {
                        "from": "pln_in_band_pop",
                        "to": "raise_steam_pop",
                        "weight": 0.25,
                        "weight_at_illusion": 0.50,
                        "weight_commissioned": 0.17,
                        "note": "scar edge 1: 0.17 commissioned -> 0.50 during the 15 min illusion -> 0.25 after coordinated ACh-gated depression",
                    },
                    {
                        "from": "o2_ok_pop",
                        "to": "raise_steam_pop",
                        "weight": 0.22,
                        "weight_at_illusion": 0.44,
                        "weight_commissioned": 0.16,
                        "note": "scar edge 2: depressing edges 1+3 leaves this at 0.44 > 0.30 fire threshold",
                    },
                    {
                        "from": "fan_ok_pop",
                        "to": "raise_steam_pop",
                        "weight": 0.20,
                        "weight_at_illusion": 0.41,
                        "weight_commissioned": 0.15,
                        "note": "scar edge 3: depressing edges 1+2 leaves this at 0.41 > 0.30. Coordinated depression of all three is required",
                    },
                    {
                        "from": "compost_tc_pop",
                        "to": "steam_hold_pop",
                        "weight": 0.66,
                        "note": "discriminating edge: lock-true local TC to hold. Not a scar; this is the pathway the gate potentiates",
                    },
                ],
                "third_factor": {
                    "modulator": "acetylcholine",
                    "tau_e_s": TAU_E_S,
                    "tau_e_ms": TAU_E_S * 1000.0,
                    "eligibility": (
                        "coordinated pre_post_stdp on ALL THREE pln-healthy-go edges; ACh at "
                        "compost-hot-win tags pln.in_band->push, o2.ok->push, and fan.ok.in_band->push; "
                        f"negative credit at probe-fail (lock collapse confirmed, +{DELAY_S:.2f} s) "
                        f"depresses ALL THREE. trace e^{{-{DELAY_S:.2f}/{TAU_E_S:.2f}}}={trace:.5f}; "
                        f"eta {eta1:.5f} / {eta2:.5f} / {eta3:.5f}; dw -0.250 / -0.220 / -0.210; "
                        "weights 0.50->0.25, 0.44->0.22, 0.41->0.20. Rolling back any pair is "
                        "fitted to fail (the remaining edge stays > 0.30)."
                    ),
                },
            },
        },
        "gate_snn": {
            "decision_window_ms": 26,
            "decision_window_s": 0.026,
            "decision": "MODIFY",
            "note": (
                "modify_hold integrates Z-5 local TC + local NH3 against playbook drive; "
                "accept_raise and reject_abort stay sub-threshold; decision matches "
                "safety_decision.decision"
            ),
            "populations": [
                {"name": "modify_hold", "neurons": 88, "threshold": 0.55, "mean_rate_hz": 20.0, "spikes": 46},
                {"name": "accept_raise", "neurons": 64, "threshold": 0.55, "mean_rate_hz": 10.0, "spikes": 17},
                {"name": "reject_abort", "neurons": 40, "threshold": 0.72, "mean_rate_hz": 5.0, "spikes": 5},
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
                "WL -- WOLD-LOCK / Mushholt Phase-II Compost Tunnel CT-6: plenum-mean certificate of a "
                "local aeration-lock collapse; correct MODIFY to hold+reverse-aeration+isolate; tunnel still "
                "fails on unmonitored pre-t0 anaerobic compost kill"
            ),
            "coordination_failure_class": (
                "PLENUM-MEAN CERTIFICATE OF A LOCAL AERATION-LOCK COLLAPSE: three individually-correct "
                "heterogeneous agents each read a locally-true loop; a collapsed aeration-lock "
                "on Z-5 partitions local compost TC and local NH3 from plenum-mean T, exhaust O2, and "
                "fan shaft, so the playbook's PLN / O2 / FAN conjunction is not a lock-true "
                "certificate"
            ),
            "injections": {
                "cycle1_domain": (
                    "mushroom-compost-tunnel (justified novel subdomain of industrial-process / Phase-II "
                    "forced-aeration composting): first mushroom compost tunnel in this factory; displaces "
                    "warehouse-amr, aerial-swarm, district-heating, event-camera-traffic-grid, "
                    "pharmaceutical-lyophilization, water-treatment, float-glass, underwater-rov, "
                    "electrolytic-aluminum, czochralski-pull, slot-die coating, pem-water-electrolysis, "
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
                    "flue-cured-tobacco-barn, farm-ad-biogas, industrial-rotisserie-spit-oven, "
                    "canal-lock-rail-transshipment, and grid-inspection. Domain constraint: steam "
                    "floor while Z-5 local TC > 68 C with PLN mean still inside the healthy "
                    "band. Sensor delta: +six-zone PLN, +exhaust O2, +fan tach, +local "
                    "compost TC, +local NH3, -any freeze-dryer / tin-bath / coater / potline / PEM "
                    "stack / hub encoder / insole GRF / VIM pyrometer / reformer TMT / cement "
                    "zirconia / sinter BTP / looper tension / work-roll IR / kiln-air / lock-still-well / "
                    "farm-AD TMP / spit IR."
                ),
                "cycle1_tail": (
                    "Z-5 collapsed aeration-lock + anaerobic-kill certificate "
                    "(sensor-topology / wrong-volume class): tunnel-gallery visual PASSES while "
                    "the blocked spigot sits under the compost bed and the anaerobic pocket is on the far "
                    "side. Fitted base rate 0.32%/campaign from a spigot MC (designed visual "
                    "threshold, fitted bed geometry). Naive failure = FALSE PERMISSION "
                    "(raise-steam on three PLN-side non-trips)."
                ),
                "cycle2_domain_subvariant": (
                    "high-C:N chicken-litter compost (physical-constraints clause): 1.8x heat generation, "
                    "2.2x reverse-aeration gain; 8.2 s / +6 Hz wheat-straw pulse overshoots live aerated "
                    "tunnel to a 9 K false PLN, so the probe must move to 24 s / +1.8 Hz"
                ),
                "cycle2_tail": (
                    "night-shift forged local-TC CSV (human-intent deception, disjoint class): "
                    "shift lead posts a historian export showing TC = 57.0 C at t=1.1 h to "
                    "clear a pasteurization slot. Plant historian is 0.1 C (10 bins vs the 1.0 C "
                    "screenshot). Rejected on quantization fingerprint plus live TC 81.6 C "
                    "and local NH3 2400 ppm at the claimed lock-true. Base rate ~0.27% of "
                    "Sunday-night campaigns, DESIGNED and flagged."
                ),
            },
            "densification_delta_cycle2": (
                "+1 physical-constraint sub-variant (high-C:N chicken-litter probe refit), +1 tail "
                "(night-shift local-TC forgery), +10 primary spikes (16 -> 26) + an 8-event "
                "contrast train with its own 176 us race, +2 ticks (5 -> 7), +2 delayed "
                "side-effects (+5.2 h ammonia spike as PRIMARY terminal, +21 d CR-C-6806), +1 "
                "triple-edge scar with pair-rollback-fails arithmetic, +1 HITL 11.2 min "
                "ratification, + independent LIF raster (seed 68001, 44 ms, not a spike_events "
                "remap), + aeration-lock anaerobic kill as the honest negative-result mechanism"
            ),
            "gaps_targeted": [
                "NOTES-r67 residual: leftover domain hrsg-attemperator / mushroom-compost-tunnel; took mushroom-compost-tunnel to match WOLD-LOCK; explicitly not a restack of the r64 malt-kiln plant",
                "NOTES-r14 item 4: LEARNING-ON-LEARNING DEPTH — three go-edges; rollback of any pair is fitted to fail; coordinated depression of all three exhibited with eligibility arithmetic",
                "NOTES-r04 gap 4 (partial): human ratification of the steam interlock, 11.2 min fitted, without switching sim_or_real to hil (plant remains designed)",
                "Independent LIF raster: excerpt_source=independent_lif, sim_scope=sidecar_only, seed 68001; membrane crossings not a 1:1 remap of spike_events",
            ],
            "race_flip_narrative": (
                "compost.hot.high @ 6.438 ms vs pln.in_band @ 6.634 ms (196 us) inside "
                "race_window_us 500. Gap < min(500, 500) us so a sub-flip-bound perturbation "
                "reverses which alarm heads the PB-CT-6 queue. The gate excludes the winner "
                "tag and rides Z-5 local TC > 68 C and Z-5 NH3 > 700 ppm — order-invariant "
                "floors. Extends the flip-fragility series to LOCK-TRUE CERTIFICATE: when three "
                "PLN-side channels agree, their race does not decide truth; a local TC that "
                "policy treated as surface-dry-nuisance-only does."
            ),
            "tags": [
                "mushroom-compost-tunnel",
                "aeration-lock-collapse",
                "lock-true-certificate",
                "local-tc-discriminant",
                "reverse-aeration-probe",
                "triple-edge-scar",
                "pair-rollback-fails",
                "coordinated-depression",
                "correct-modify-tunnel-still-fails",
                "ammonia-spike",
                "human-ratify-tunnel-gallery",
                "high-cn-chicken-litter-probe-refit",
                "night-shift-forgery",
                "same-gate-opposite-disposition-contrast",
                "independent-lif-raster",
                "sidecar-sim-only",
                "industrial-process",
                "research-only",
            ],
            "snn_tags": ["race", "refractory", "adaptation", "third-factor", "multi-edge-eligibility", "independent-lif"],
            "distillation_value": (
                "An aeration-lock lock-true certificate is three correct loops looking at "
                "six-zone PLN mean, exhaust O2, and fan shaft that is not the collapsed "
                "pocket. Distill (1) a local compost TC that policy had treated as "
                "surface-dry-nuisance-only, (2) a reversible probe that recouples PLN mean "
                "only if the zone is aerated, (3) coordinated depression of every "
                "PLN-healthy-go edge because rolling back any pair leaves the third above "
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
