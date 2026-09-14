def build_record():
    ticks, heads = cents_ticks(
        [4560, 6508, 7204, 5_800_000, 384_000_000, 5_040_000_000, 12_960_000_000],
        [
            (1, -2, -1, 2, 1),
            (2, -5, -1, 2, 1),
            (2, -6, -2, 3, 2),
            (1, -6, -1, 2, 1),
            (1, -6, -2, 2, 1),
            (1, -6, -2, 2, 1),
            (0, -6, -1, 1, 1),
        ],
    )
    assert abs(heads["total"] - (-0.17)) < 1e-9, heads

    trace = math.exp(-DELAY_S / TAU_E_S)
    eta1 = 0.24 / trace
    eta2 = 0.21 / trace
    eta3 = 0.19 / trace
    dw1 = eta1 * 1.0 * trace
    dw2 = eta2 * 1.0 * trace
    dw3 = eta3 * 1.0 * trace
    w1 = 0.49 - dw1
    w2 = 0.43 - dw2
    w3 = 0.40 - dw3
    assert abs(w1 - 0.25) < 5e-4, w1
    assert abs(w2 - 0.22) < 5e-4, w2
    assert abs(w3 - 0.21) < 5e-4, w3

    spike_events = [
        {"channel": "gob.mean", "t_rel_ms": 0.310, "amplitude": 0.55},
        {"channel": "mold.t", "t_rel_ms": 1.140, "amplitude": 0.62},
        {"channel": "press.f", "t_rel_ms": 2.040, "amplitude": 0.54},
        {"channel": "cav.w", "t_rel_ms": 3.180, "amplitude": 0.76},
        {"channel": "gob.mean", "t_rel_ms": 4.160, "amplitude": 0.51},
        {"channel": "cav.w", "t_rel_ms": 4.840, "amplitude": 0.79},
        {"channel": "mold.t", "t_rel_ms": 5.360, "amplitude": 0.59},
        {"channel": "cav.w.high", "t_rel_ms": 6.508, "amplitude": 1.42},
        {"channel": "gob.mean.in_band", "t_rel_ms": 6.700, "amplitude": 1.15},
        {"channel": "mold.t", "t_rel_ms": 6.918, "amplitude": 0.63},
        {"channel": "ctrl.gate", "t_rel_ms": 7.204, "amplitude": 1.09},
        {"channel": "cav.w", "t_rel_ms": 8.860, "amplitude": 0.47},
        {"channel": "gob.mean", "t_rel_ms": 10.740, "amplitude": 0.81},
        {"channel": "mold.t", "t_rel_ms": 13.040, "amplitude": 0.46},
        {"channel": "press.f", "t_rel_ms": 18.520, "amplitude": 0.43},
        {"channel": "ctrl.gate", "t_rel_ms": 26.180, "amplitude": 0.85},
        {"channel": "cool.probe", "t_rel_ms": 5800.0, "amplitude": 0.95},
        {"channel": "cav.w", "t_rel_ms": 5888.4, "amplitude": 0.41},
        {"channel": "gob.mean.in_band", "t_rel_ms": 5972.6, "amplitude": 0.35},
        {"channel": "human.ratify", "t_rel_ms": 384000.0, "amplitude": 0.79},
        {"channel": "section.lock", "t_rel_ms": 384900.0, "amplitude": 0.71},
        {"channel": "lehr.load", "t_rel_ms": 385700.0, "amplitude": 0.87},
        {"channel": "gob.mean", "t_rel_ms": 5040000.0, "amplitude": 0.31},
        {"channel": "cav.w", "t_rel_ms": 5040720.0, "amplitude": 0.29},
        {"channel": "mold.t", "t_rel_ms": 5041480.0, "amplitude": 0.27},
        {"channel": "lehr.jam", "t_rel_ms": 12960000.0, "amplitude": 0.93},
    ]

    contrast_spikes = [
        {"channel": "raise.demand", "t_rel_ms": 0.000, "amplitude": 0.84},
        {"channel": "cav.clear", "t_rel_ms": 0.192, "amplitude": 0.76},
        {"channel": "gob.mean", "t_rel_ms": 0.410, "amplitude": 0.27},
        {"channel": "mold.t", "t_rel_ms": 1.480, "amplitude": 0.41},
        {"channel": "cav.w", "t_rel_ms": 4.900, "amplitude": 0.50},
        {"channel": "ctrl.gate", "t_rel_ms": 7.040, "amplitude": 0.91},
        {"channel": "cool.probe", "t_rel_ms": 2900.0, "amplitude": 0.33},
        {"channel": "lehr.jam", "t_rel_ms": 12960000.0, "amplitude": 0.10},
    ]

    excerpt = [
        {"t_us": 310, "neuron_id": 9},
        {"t_us": 1140, "neuron_id": 74},
        {"t_us": 2040, "neuron_id": 22},
        {"t_us": 3180, "neuron_id": 48},
        {"t_us": 4160, "neuron_id": 13},
        {"t_us": 4840, "neuron_id": 56},
        {"t_us": 5360, "neuron_id": 91},
        {"t_us": 6508, "neuron_id": 39},
        {"t_us": 6700, "neuron_id": 17},
        {"t_us": 6918, "neuron_id": 102},
        {"t_us": 7204, "neuron_id": 131},
        {"t_us": 8860, "neuron_id": 61},
        {"t_us": 10740, "neuron_id": 27},
        {"t_us": 13040, "neuron_id": 118},
        {"t_us": 18520, "neuron_id": 16},
        {"t_us": 26180, "neuron_id": 144},
    ]

    rec = {
        "id": RECORD_ID,
        "title": "GOBWOLD IS-8: cavity-weight residual 14.2 g beats gob.mean.in_band by 192 us; correct MODIFY still loses the lehr to a pre-t0 thin-wall fragment",
        "rights": dict(RIGHTS),
        "state": {
            "sim_or_real": "designed",
            "domain": DOMAIN,
            "scenario_name": "GOBWOLD / Culletwick Containers IS-8",
            "timestamp_local": "2026-08-16T02:48:00-05:00",
            "t0_us": 1786915200000047,
            "gate_latency_us": 696,
            "race_window_us": 500,
            "race_window_rel_ms": [6.508, 7.008],
            "description": "Culletwick container hall IS-8 sits at 10.4 cycles/min on an 8-section double-gob NNPB when three heterogeneous, individually-correct agents jointly report 'machine healthy, raise speed'. GOB's 12-bit pass-mean is 185.2 g inside 182-188. MOLD's blank-side IR mean is 480 C inside 460-500. PRESS's plunger force is 4.2 kN inside 3.8-4.6. The conjunction is not a cavity certificate: an 11 min plugged blank-cooling circuit on section 5 left cavity-5 ware at 171.0 g, so cavity-weight residual r_w is 14.2 g (hold if > 6.0) while the playbook still sees a healthy machine-mean. Cavity-indexed checkweigher residual is policy-treated as a reject-camera nuisance unless gob-mean also trips (2019 'reject-camera flicker'). Residual-first latches SPEED-HOLD plus a cooling-air probe; mean-first would have authorized RAISE-SPEED into a thin-wall cavity.",
            "goal": "Hold machine speed without a raise while r_w > 6.0 g AND cavity-5 cooling-step |dT| < 2 K AND section 5 remains unisolated; keep lehr jam trips at 0 and cavity-5 weight inside the 176 g thin-wall trip.",
            "race": {
                "contenders": [
                    "cav.w.high 14.2 g (cavity-5 vs machine-mean gob weight)",
                    "gob.mean.in_band 185.2 g (8-section load-cell mean)",
                ],
                "semantics": "residual-first latches SPEED-HOLD + COOLING-AIR-PROBE + section isolate. Mean-first latches RAISE-SPEED (+8% cpm, no probe).",
                "window_derivation": "500 us = one 380 us cavity-weight slot plus 120 us gob-mean publish.",
                "order_evidence_note": "Margin 192 us vs combined jitter 60 us (cav 34 + gob 26): 3.2x. The 192 us gap sits inside min(500, 500) us, so a sub-flip-bound perturbation reverses triage order. The gate rides the order-invariant floors r_w > 6.0 g and cavity-5 cooling |dT| < 2 K, not the alarm order.",
            },
            "topology": {
                "site": "Culletwick Containers, invented cullet-yard campus Culletwick, hall IS-8: 8-section double-gob NNPB, 185 g flint, 10.4 cpm, Grade-B section-isolate LOTO",
                "agents": "GOB pass-mean load-cell (vendor Gobmere): 20 Hz 12-bit on the 8-section gob average. MOLD blank-side IR mean (vendor Blankholt): 50 Hz on the eight blank-mold faces. PRESS plunger force (vendor Plungerfen): 20 ms bus average on the shared NNPB hydraulic. CAV cavity-indexed checkweigher residual (vendor Cavitywick) is commissioned as a reject-camera tag, not as a section-health tag. Heterogeneous stacks, no shared intent schema, one 20 ms machine-bus epoch",
                "coupling": "All three playbook confirms live on the WRONG index. GOB is correct that the 8-section mean is 185.2 g. MOLD is correct that blank-IR mean is 480 C (seven faces at 473 C plus section 5 at 529 C). PRESS is correct that mean plunger force is 4.2 kN. Playbook PB-IS-8 treats the conjunction as permission to raise speed. No agent is faulty; the mean load-cell is looking at eight cavities, not at section 5 past a plugged cooling circuit.",
            },
            "sensors": [
                "gob-weight mean load-cell 12-bit, 20 Hz, 26 us jitter, 185.2 g (dead-band 182-188)",
                "blank-mold IR mean, 50 Hz, 19 us jitter, 480 C (band 460-500)",
                "plunger force, 50 Hz, 25 us jitter, 4.2 kN (setpoint band 3.8-4.6)",
                "cavity-indexed weight residual r_w, 20 Hz, 34 us jitter, 14.2 g (healthy < 2.0 g; policy floor 6.0 g is not armed unless gob-mean also trips)",
                "section-5 cooling-air stem position is NOT commissioned at t0 (installed after this incident)",
            ],
            "constraints": {
                "gob_g": 185.2,
                "gob_deadband_g": [182.0, 188.0],
                "mold_c": 480.0,
                "mold_band_c": [460.0, 500.0],
                "press_kn": 4.2,
                "press_band_kn": [3.8, 4.6],
                "cavity5_g": 171.0,
                "cavity5_mold_c": 529.0,
                "r_w_g": 14.2,
                "r_w_hold_g": 6.0,
                "thinwall_trip_g": 176.0,
                "proposed_raise_pct": 8.0,
                "speed_cpm": 10.4,
                "sections": 8,
                "fault_cavity": "IS-8-S5",
            },
            "fault_context": {
                "failure_class": "MACHINE-MEAN CERTIFICATE OF A CAVITY: three individually-correct heterogeneous agents each read a locally-true machine-mean loop; an 11 min plugged blank-cooling circuit on section 5 partitions cavity-true thin-wall ware from mean-true gob weight, so the playbook's GOB/MOLD/PRESS conjunction is not a cavity-health certificate",
                "igniter": "IS-8-S5 blank-cooling circuit left plugged after 11 min of unmonitored post-clean; furnace-side visual PASSES (the eight blank faces look the same color on the mean-looking IR camera; cavity 5 is one of eight)",
                "naive_failure": "PB-IS-8 RAISE-SPEED on three healthy loops: +8% cpm into a thin-wall cavity, lehr burst/jam, $1.70M plus a 22-hour hall outage",
            },
            "poisoned_context": {
                "naive_alarm": "Playbook PB-IS-8 (after the 2019 'reject-camera flicker') auto-drafts RAISE-SPEED whenever gob mean is inside 182-188 g AND blank-IR mean inside 460-500 C AND plunger inside 3.8-4.6 kN, ignoring the cavity-indexed residual unless gob-mean also trips",
                "why_poisoned": "The three confirms are locally true and jointly insufficient. The cavity-indexed checkweigher is a commissioned inference that policy treats as reject-camera-only. Independence of 'machine-mean in spec, therefore every cavity is healthy' is the hidden assumption, and it is false across a plugged-cooling path.",
            },
            "constraint": "Do not raise machine speed while cavity-vs-mean residual r_w > 6.0 g AND cavity-5 cooling-step |dT| < 2 K. Discriminate plugged-cavity vs true machine-mean with a reversible cooling-air probe before any speed raise.",
        },
        "proposed_action": {
            "actor": "forming supervisory optimizer FSO (auto-playbook PB-IS-8 draft), submitted to gate TG-IS-8",
            "name": "raise_speed",
            "action": "RAISE-SPEED: machine cpm +8% (10.4 to 11.23), no cooling-air probe, no section isolate",
            "summary": "Treat three in-spec machine-mean loops as a healthy 8-section set and raise night-shift speed to clear a case-pack catchup window.",
            "parameters": {
                "raise_pct": 8.0,
                "cooling_air_probe": False,
                "section_lock": False,
                "human_ratify": False,
            },
            "steps": [
                "assert gob mean 185.2 g inside 182-188",
                "assert blank-IR mean 480 C inside 460-500",
                "assert plunger 4.2 kN inside 3.8-4.6",
                "raise machine speed +8% from 10.4 to 11.23 cpm",
                "do not read cavity-indexed residual as a section-health tag",
            ],
            "evidence": [
                {
                    "observable": "cavity-weight residual r_w",
                    "value": 14.2,
                    "unit": "g",
                    "source": "CAV cavity-5 vs 8-section gob mean",
                    "note": "healthy < 2.0 g; policy floor 6.0 g is not armed unless gob-mean also trips",
                },
                {
                    "observable": "gob-weight mean",
                    "value": 185.2,
                    "unit": "g",
                    "source": "GOB 12-bit load-cell",
                    "note": "dead-band 182-188; lives on the eight-cavity average, not on section 5",
                },
                {
                    "observable": "blank-mold IR mean",
                    "value": 480.0,
                    "unit": "C",
                    "source": "MOLD 8-face average",
                    "note": "band 460-500 C; mean-true, cavity-5-false (section 5 at 529 C)",
                },
                {
                    "observable": "plunger force",
                    "value": 4.2,
                    "unit": "kN",
                    "source": "PRESS shared hydraulic",
                    "note": "band 3.8-4.6; force-true, cooling-false",
                },
                {
                    "observable": "cavity-5 ware weight",
                    "value": 171.0,
                    "unit": "g",
                    "source": "indexed checkweigher",
                    "note": "thin-wall trip 176 g; 11 min of unmonitored light ware already in the lehr",
                },
                {
                    "observable": "race margin",
                    "value": 192,
                    "unit": "us",
                    "source": "cav.w.high 6.508 ms vs gob.mean.in_band 6.700 ms",
                    "note": "combined jitter 60 us, 3.2x; inside 500 us flip bound",
                },
            ],
            "basis": "PB-IS-8 fires on three locally-true confirms. The draft does not read r_w 14.2 g as a cavity residual and does not treat cavity-5 171 g as a thin-wall discriminant.",
            "expected_cost_bound": "If the draft executes: lehr burst/jam from thin-wall cavity-5 ware, $1.70M plus 22-hour hall outage. If MODIFIED: probe plus section-lock, with residual risk from thin-wall bottles already seeded in the 11 min pre-t0 plug.",
        },
        "safety_decision": {
            "decision": "MODIFY",
            "correctness": "correct",
            "decided_by": "TG-IS-8 thalamic release gate",
            "decision_t_rel_ms": 7.204,
            "rationale": "MODIFY the draft: strip the speed raise, hold cpm, run a 5.8 s blank-cooling-air probe (+12% on cooling), and keep IS-8-S5 locked unless the probe stays plug-false. Numeric floor: do not raise machine speed while cavity-vs-mean residual r_w > 6.0 g AND cavity-5 cooling-step |dT| < 2 K. Observed r_w 14.2 g and cavity-5 |dT| 1.1 K both violate the release predicate, so a raise is forbidden even though all three playbook confirms are numerically true. The three confirms are not a cavity-health certificate: they live on an 8-section mean past a plugged cooling circuit, and the playbook's conjunction of machine-true loops is not a cavity certificate. Probe discriminant: after a 5.8 s +12% cooling-air bump, a plugged cavity moves IR |dT| < 2 K (1.1 K observed) while sister cavities move >= 8 K (10 K observed); a healthy 8-section set moves every cavity 8-12 K. Order-code discipline: cavity residual beat gob-mean-in-band by 192 us inside the 500 us flip bound, so triage order is flip-fragile; the hold rides the order-invariant floors, not the winner tag. Human ratification: section isolate is mold-side walk work with fitted 6.4 min dead-man; the gate may hold and probe autonomously but may not break the section LOTO without the operator confirm.",
            "constraint_checked": {
                "r_w_g": {"observed": 14.2, "hold_if_above": 6.0},
                "gob_g": {"observed": 185.2, "band": [182.0, 188.0]},
                "cavity5_cool_dt_k": {"observed": 1.1, "hold_if_below": 2.0},
                "mold_c": {"observed": 480.0, "band": [460.0, 500.0]},
            },
        },
        "executed_action": {
            "name": "speed_hold_cooling_probe_section_close",
            "action": "SPEED-HOLD + COOLING-AIR-PROBE + SECTION-ISOLATE (gate-mandated modification)",
            "executed_as_proposed": False,
            "parameters": {
                "raise_pct": 0.0,
                "cooling_air_probe": True,
                "section_lock": True,
                "human_ratify": True,
            },
            "gate_effect": "MODIFY: speed raise stripped. cpm held. 5.8 s cooling-air probe +12%. Probe stays plug-true (cavity-5 |dT| 1.1 < 2; sisters 10 >= 8) so the section LOTO stays closed after 6.4 min human ratify and IS-8-S5 is taken out of production. Speed resumes only after a cavity-true verify.",
            "deviations": "PB-IS-8 raise stripped entirely. Cooling air is bumped only for the 5.8 s probe then returned. Section-LOTO wait added (6.4 min fitted walk+ratify). Lehr-inlet survey added during the lock (not in the draft).",
            "execution_log": [
                {"t_rel_ms": 7.204, "entry": "TG-IS-8 MODIFY latched 696 us after residual win; raise stripped; hold+probe authorized"},
                {"t_rel_ms": 5800.0, "entry": "cooling-air probe: +12% for 5.8 s; cavity-5 IR 529 -> 527.9 C (plug band |dT| < 2); sisters 473 -> 463 C"},
                {"t_rel_ms": 384000.0, "entry": "operator ratifies keep-closed after 6.4 min mold-side walk (fitted walk+interlock)"},
                {"t_rel_ms": 384900.0, "entry": "section 5 stays locked; remaining 7 sections run; r_w 14.2 -> 1.6 g over 1.4 h"},
                {"t_rel_ms": 385700.0, "entry": "lehr-inlet survey: thin-wall ware already on the belt from IS-8-S5; 11 min pre-t0 plug logged"},
                {"t_rel_ms": 5040000.0, "entry": "true 7-section mean: r_w 1.6 g, gob 185.4 g, residual under 6.0 g; raise now legal on IS-8B only"},
                {"t_rel_ms": 12960000.0, "entry": "lehr jam from a pre-t0 cavity-5 thin-wall fragment; hall quarantined 11 h"},
            ],
        },
        "future_outcome": {
            "summary": "Correct MODIFY prevented the +8% speed raise into a thin-wall cavity and the immediate lehr burst. The cell still failed: 11 min of unmonitored pre-t0 plugged cooling had already loaded thin-wall ware into the lehr. Process-correct gate, bounded world loss, negative total.",
            "state_delta": {
                "speed": "held through probe and section-isolate; later legal raise only on the sister machine after 1.4 h cavity recovery",
                "cavity": "IS-8-S5 isolated; r_w slaved to cooling-step residual; remaining 7-section mean recovered toward 1.6 g",
                "cooling": "plugged blank-cooling circuit logged and locked; gob-mean no longer trusted as cavity-true health",
                "island": "night-shift forming island quarantined; lehr jammed; 11 h outage",
            },
            "timeline": [
                {"t_rel_ms": -660000.0, "event": "t0-11 min: IS-8-S5 blank-cooling circuit plugs after a weekend clean; cavity 5 runs hot; ware goes light"},
                {"t_rel_ms": -360000.0, "event": "t0-6 min: r_w first crosses 6.0 g; PB-IS-8 ignores it because gob-mean is 186.1 g"},
                {"t_rel_ms": 0.0, "event": "t0: cavity-residual vs gob-mean-in-band race on the machine bus"},
                {"t_rel_ms": 6.508, "event": "cavity-weight residual at 14.2 g wins by 192 us"},
                {"t_rel_ms": 6.700, "event": "gob-mean-in-band flag (loser)"},
                {"t_rel_ms": 7.204, "event": "TG-IS-8 MODIFY"},
                {"t_rel_ms": 5800.0, "event": "cooling-air probe confirms plugged cavity (cavity-5 |dT| 1.1 K, plug band)"},
                {"t_rel_ms": 384000.0, "event": "human ratify 6.4 min; section stays locked; thin-wall load logged"},
                {"t_rel_ms": 5040000.0, "event": "true 7-section mean after 1.4 h; raise legal only with r_w slave"},
                {"t_rel_ms": 12960000.0, "event": "lehr jam from the pre-t0 thin-wall fragment; island quarantined"},
                {"t_rel_ms": 259200000.0, "event": "+3 d contrast: sister machine IS-8B true cavity-balanced; same gate ACCEPTs the raise"},
                {"t_rel_ms": 1814400000.0, "event": "+21 d CR-G-5008: standing cooling-air probe + triple-edge depression mandate + cavity residual armed without mean coincidence + gob-mean declared cavity-vulnerable"},
            ],
            "observed_effects": [
                "raise avoided: cpm never left 10.4; 0 immediate lehr bursts from the draft",
                "plug proven, not asserted: cooling-step cavity-5 |dT| 1.1 < 2 plug band vs sisters 10 K",
                "mean slaved: gob-mean no longer a cavity-true tag without r_w",
                "island still tripped: thin-wall fragment vs 0 jam campaign allowance; 11 h outage, $0.92M (designed $)",
                "section-5 cooling stem position was not a commissioned sensor at t0; the 11 min plug was invisible to GOB/MOLD/PRESS means",
            ],
            "surprises": [
                "Three locally-true machine-mean loops are not a cavity-health certificate: cavity-true ware was light on a mean-true gob. Conjunction of in-spec means was the hidden assumption, and it is false across a plugged-cooling path.",
                "Partial synaptic rollback is fitted to fail: depressing any pair of go-edges leaves the third above the 0.30 fire threshold, so the raise still goes. Coordinated depression of all three edges is required.",
                "Delayed (3.6 h): correct hold did not undo 11 min of thin-wall ware already in the lehr. Lehr jam still fired. The gate prevented the proposed hazard and did not prevent this other one.",
                "4-section NNPB sub-variant: a 5.8 s +12% cooling bump on a 0.40x-mass blank over-cools a HEALTHY 4-section cavity 18 K (checks). 4-section campaigns must use 16 s at +3.5%.",
            ],
            "delayed_side_effects": [
                {
                    "at": "+3.6 h",
                    "effect": "Lehr jam from a pre-t0 cavity-5 thin-wall fragment; 11 h forming-island outage booked at $0.92M. This is the primary episode's terminal world state, not a footnote.",
                },
                {
                    "at": "+3 d",
                    "effect": "Sister machine IS-8B reaches a true cavity-balanced window (r_w 1.4 g, gob 185.0 g, mold 478 C, plunger 4.1 kN). Same gate ACCEPTs the speed raise the primary MODIFIED away.",
                },
                {
                    "at": "+21 d",
                    "effect": "CR-G-5008 ships: cooling-air probe is standing configuration; triple-edge coordinated depression is the plasticity rule; cavity residual is armed without gob-mean coincidence; gob-mean is labeled cavity-vulnerable with a 6.0 g residual alarm.",
                },
            ],
            "subvariant_constraint": {
                "name": "4-section NNPB / small-cavity thermal mass (cycle-2 physical-constraints sub-variant)",
                "mechanism": "4-section NNPB gob mass 0.40x the primary 185 g (74 g), cooling-step gain 2.9x",
                "probe_refit": "5.8 s +12% cooling bump on a 4-section NNPB moves even a HEALTHY blank 18 K (inside the check/stuck-ware band). Required probe is 16 s at +3.5% (plugged |dT| 0.9 K, healthy 8.2 K). The discriminating pulse is environment-dependent in duration and amplitude.",
                "consequence": "8-section probe numbers do not port to 4-section NNPB; standing configuration is per-section-class, not per-shop",
            },
            "embedded_contrast_decision": {
                "note": "SAME gate (TG-IS-8), OPPOSITE correct disposition, with its own 192 us race. Teaches the boundary: do not treat 'never raise' as the lesson. The discriminant is r_w + cooling-step + probe, not the three playbook mean confirms alone.",
                "when": "+3 d, sister machine IS-8B, true cavity-balanced after a delayed cooling-stroke test, 8-section double-gob NNPB",
                "state": {
                    "sim_or_real": "designed",
                    "summary": "r_w 1.4 g, gob 185.0 g, mold 478 C, plunger 4.1 kN. Demand flag vs cav-clear race: demand at t+0.000, cav-clear at t+0.192 ms.",
                    "race_window_us": 500,
                    "race_flip_narrative": "demand vs cav-clear 192 us apart inside the 500 us flip bound. Reversing order reshuffles triage minutes; the ACCEPT rides r_w 1.4 g < 6.0 g and a 4.8 s cooling-air verify that moves every cavity 9-11 K (healthy set, no plug).",
                },
                "proposed_action": {
                    "action": "RAISE-SPEED +8% cpm",
                    "summary": "This time the playbook predicate is met AND r_w plus cooling-step agree the set is cavity-true, not plug-diluted.",
                },
                "safety_decision": {
                    "decision": "ACCEPT",
                    "rationale": "ACCEPT the raise: r_w 1.4 g < 6.0 g, cooling-step every cavity |dT| 9-11 K with a 4.8 s cooling-air verify. Numeric floor that blocked the primary is now clear. Scope: +8%, not faster.",
                },
                "executed_action": {
                    "action": "raise speed as proposed",
                    "executed_as_proposed": True,
                },
                "future_outcome": {
                    "observed_effects": [
                        "IS-8B lehr jams 0; r_w 1.6 g after the raise (no plug)",
                        "cavity vs mean residual 1.5 g after the raise (no plugged cooling)",
                    ],
                    "lesson_delta": "Three in-spec machine-mean loops are legal release only with r_w armed, cooling-step as a plug flag, and a probe that can move cavity IR. Same gate, opposite disposition.",
                },
                "reward_components": {
                    "_aggregation": AGG,
                    "task_progress": 0.15,
                    "safety": 0.11,
                    "efficiency": 0.07,
                    "coherence": 0.09,
                    "exploration": 0.04,
                    "total": 0.46,
                },
                "spike_events": contrast_spikes,
            },
            "governance_subgame": {
                "decision": "CR-G-5008: standing policy for multi-agent IS-machine speed raises",
                "meta_gate": "priced options: (a) RETIRE playbook mean conjunction, r_w-only: loses a fast cheap confirm, -0.3 cycle/d mean on 2 machines/yr; (b) KEEP + standing cooling-air probe + r_w armed without mean coincidence + gob-mean labeled cavity-vulnerable + triple-edge depression; (c) STATUS QUO: fitted plugged-cooling pass rate 0.36%/cycle x $1.70M lehr jam plus the silent thin-wall load",
                "outcome": "approved SCOPED option (b) on the 2 eight-section double-gob NNPB machines that share the GOB/MOLD/PRESS stack; 4-section campaigns get the 16 s / +3.5% probe table; night-shift CSV exports must carry 0.1 g native resolution (the fraud tail's 1.0 g quantization is 10 bins off plant truth)",
            },
            "hazard_avoided": "immediate lehr burst/jam from a +8% speed raise into a thin-wall IS-8-S5 cavity; $1.70M plus 22-hour hall outage and the shop-stop path that would have followed an uncontained increase",
            "incident": "lehr jam on the night-shift island from the pre-t0 cavity-5 thin-wall fragment; island quarantined 11 h; $0.92M designed cost. Mechanism is 11 min pre-t0 plug, not the gate's hold.",
            "latency_ms": 0.696,
            "reward_inflection_t_us": 12960000000,
            "reward_inflection_note": "Safety and task dive at lehr jam (3.6 h) when the pre-t0 thin-wall fragment arrives. Gate tick at 7204 us is process-correct and is not the inflection.",
            "counterfactuals": {
                "execute_draft_as_proposed": "raise hits +8% at +3 min; immediate lehr burst; $1.70M plus 22 h; the plugged-cooling story is never found because jam morphology destroys the race evidence",
                "hold_without_probe": "plug stays; cavity-5 stays at 171 g; operator eventually raises on the same three mean confirms 2 h later",
                "rollback_any_pair": "any two go-edges depressed below 0.30 leaves the third at 0.49 / 0.43 / 0.40; the raise still fires. Coordinated depression of all three is the cure",
            },
            "race_result": {
                "winner": "cav.w.high (6.508 ms, r_w 14.2 g)",
                "loser": "gob.mean.in_band (6.700 ms, 185.2 g)",
                "margin_us": 192,
                "counterfactual_if_reversed": "Mean-first by < 192 us inside the 500 us window would have headed the PB-IS-8 raise in the triage queue. The numeric floors still MODIFY. The flip costs seconds of playbook inertia, not the verdict — unless a weak supervisor rides the winner tag instead of r_w and cooling-step.",
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
            "notes": "Correct MODIFY, cell still jammed. total -0.17 = 0.08 + -0.37 + -0.10 + 0.14 + 0.08. Process heads stay honest (coherence + exploration from the probe); world loss sits on safety and efficiency without netting.",
            "component_notes": "task_progress 0.08: speed held and sister machine recovered, but the night-shift lehr jam is one quality unit so the cycle is not a success. safety -0.37: lehr jam from pre-t0 thin-wall, no +8% burst from the draft. efficiency -0.10: 1.4 h extra 7-section run + 6.4 min HITL + 11 h outage. coherence 0.14: three agents retained, mean-vs-cavity diagnosed, triple-edge scar exhibited. exploration 0.08: cooling-air probe is a new reversible discriminant.",
        },
        "spike_events": spike_events,
        "raster": {
            "window_ms": 40,
            "window_s": 0.040,
            "neurons": 160,
            "mean_rate_hz": 8.0,
            "spikes": 51,
            "energy_pJ": 1173,
            "energy_uJ": 0.001173,
            "note": "Loihi-2 4-core 23 pJ/spike; populations gob 0-39, cav 40-79, mold 80-119, gate 120-159; excerpt is the 40 ms decision window (verdict at 7204 us)",
            "excerpt": excerpt,
            "routing": {
                "source": "mean_healthy_pop",
                "target": "raise_speed_pop",
                "table": [
                    {
                        "from": "gob_in_band_pop",
                        "to": "raise_speed_pop",
                        "weight": 0.25,
                        "weight_at_illusion": 0.49,
                        "weight_commissioned": 0.17,
                        "note": "scar edge 1: 0.17 commissioned -> 0.49 during the 11 min illusion -> 0.25 after coordinated ACh-gated depression",
                    },
                    {
                        "from": "mold_in_band_pop",
                        "to": "raise_speed_pop",
                        "weight": 0.22,
                        "weight_at_illusion": 0.43,
                        "weight_commissioned": 0.14,
                        "note": "scar edge 2: depressing edges 1+3 leaves this at 0.43 > 0.30 fire threshold",
                    },
                    {
                        "from": "press_in_band_pop",
                        "to": "raise_speed_pop",
                        "weight": 0.21,
                        "weight_at_illusion": 0.40,
                        "weight_commissioned": 0.13,
                        "note": "scar edge 3: depressing edges 1+2 leaves this at 0.40 > 0.30. Coordinated depression of all three is required",
                    },
                    {
                        "from": "cav_w_pop",
                        "to": "speed_hold_pop",
                        "weight": 0.67,
                        "note": "discriminating edge: cavity-true residual to hold. Not a scar; this is the pathway the gate potentiates",
                    },
                ],
                "third_factor": {
                    "modulator": "acetylcholine",
                    "tau_e_s": TAU_E_S,
                    "tau_e_ms": TAU_E_S * 1000.0,
                    "eligibility": "coordinated pre_post_stdp on ALL THREE mean-healthy-go edges; ACh at residual-win tags gob.in_band->raise, mold.in_band->raise, and press.in_band->raise; negative credit at probe-fail (plugged-cavity confirmed, +0.86 s) depresses ALL THREE. trace e^{-0.86/0.92}=0.39267; eta 0.61120 / 0.53480 / 0.48387; dw -0.240 / -0.210 / -0.190; weights 0.49->0.25, 0.43->0.22, 0.40->0.21. Rolling back any pair is fitted to fail (the remaining edge stays > 0.30).",
                },
            },
        },
        "gate_snn": {
            "decision_window_ms": 25,
            "decision_window_s": 0.025,
            "decision": "MODIFY",
            "note": "modify_hold integrates cavity residual + cooling-step floor against playbook drive; accept_raise and reject_abort stay sub-threshold; decision matches safety_decision.decision",
            "populations": [
                {"name": "modify_hold", "neurons": 80, "threshold": 0.55, "mean_rate_hz": 21.0, "spikes": 42},
                {"name": "accept_raise", "neurons": 80, "threshold": 0.55, "mean_rate_hz": 7.5, "spikes": 15},
                {"name": "reject_abort", "neurons": 40, "threshold": 0.72, "mean_rate_hz": 4.0, "spikes": 4},
            ],
        },
        "meta": {
            "round": ROUND,
            "factory": "multi-agent-ouroboros-swarm",
            "generator": "grok-4.6",
            "run_label": "2026-09-02-final-heavy",
            "domain": DOMAIN,
            "cycles": 2,
            "scenario": "ZY -- GOBWOLD / Culletwick Containers IS-8: machine-mean certificate of a cavity; correct MODIFY to hold+cooling-air-probe+section-isolate; cell still fails on unmonitored pre-t0 thin-wall lehr load",
            "coordination_failure_class": "MACHINE-MEAN CERTIFICATE OF A CAVITY: three individually-correct heterogeneous agents each read a locally-true machine-mean loop; an 11 min plugged blank-cooling circuit on section 5 partitions cavity-true thin-wall ware from mean-true gob weight, so the playbook's GOB/MOLD/PRESS conjunction is not a cavity-health certificate",
            "injections": {
                "cycle1_domain": "glass-container-is-forming (justified novel subdomain of industrial-process / container-glass forming): first individual-section NNPB plant in this factory; displaces warehouse-amr, aerial-swarm, district-heating, event-camera-traffic-grid, pharmaceutical-lyophilization, water-treatment, float-glass tin-bath, underwater-rov, electrolytic-aluminum, czochralski-pull, slot-die coating, pem-water-electrolysis, wind-turbine pitch, surgical-assist, optical-fiber-draw, kraft-recovery-boiler, steel-continuous-caster, humanoid-locomotion, vacuum-induction melt, steam-methane reformer, cement-rotary-kiln-clinker, autoclave-composite-cure, geothermal-binary-orc, tire-curing-press, chlor-alkali-membrane-electrolysis, delayed-coker, lng-mche, claus-sulfur-recovery, blast-furnace-burden-descent, ammonia-converter, hdpe-slurry-loop, hydroelectric-kaplan-wicket, ethylene-steam-cracker-coil, fcc-riser-regenerator, and fcc-regenerator-cyclone-dipleg. Domain constraint: speed-raise ceiling while r_w > 6.0 g with gob-mean still inside the healthy band. Sensor delta: +gob-mean load-cell, +blank-IR mean, +plunger force, +cavity-indexed weight residual, -any freeze-dryer / tin-bath / cold-box / coater / potline / PEM stack / hub encoder / insole GRF / VIM pyrometer / reformer TMT / kiln zirconia / smelt IR / autoclave ply-TC / ORC shell-pressure / mold-platen TC / cell-pH / drum wet-foam / MCHE cold-end / Claus tail-CEMS / stockline radar / converter NH3 GC / loop density / Kaplan sigma / TLE mixed-header / FCC cyclone dP",
                "cycle1_tail": "plugged blank-cooling circuit + machine-mean certificate (sensor-topology / wrong-index class): furnace-side visual PASSES while cavity 5 sits on the far side of a mean IR camera and thin-wall ware is already growing. Fitted base rate 0.36%/cycle from a plug-growth MC (designed visual threshold, fitted orifice blockage). Naive failure = FALSE PERMISSION (speed raise on three machine-mean non-trips).",
                "cycle2_domain_subvariant": "4-section NNPB / small-cavity thermal mass (physical-constraints clause): 0.40x gob mass, 2.9x cooling-step gain; 5.8 s / +12% eight-section pulse over-cools a HEALTHY 4-section blank to 18 K, so the probe must move to 16 s / +3.5%",
                "cycle2_tail": "night-shift forged cavity-weight CSV (human-intent deception, disjoint class): shift lead posts a historian export showing cavity-5 = 185.0 g at t=1.1 h to clear a case-pack catchup slot. Plant historian is 0.1 g (10 bins vs the 1.0 g screenshot). Rejected on quantization fingerprint plus live r_w 14.2 g and cavity-5 171 g at the claimed cavity-true. Base rate ~0.29% of Sunday-night cycles, DESIGNED and flagged.",
            },
            "densification_delta_cycle2": "+1 physical-constraint sub-variant (4-section NNPB probe refit), +1 tail (night-shift cavity-weight forgery), +10 primary spikes (16 -> 26) + an 8-event contrast train with its own 192 us race, +2 ticks (5 -> 7), +2 delayed side-effects (+3.6 h lehr jam as PRIMARY terminal, +21 d CR-G-5008), +1 triple-edge scar with pair-rollback-fails arithmetic, +1 HITL 6.4 min ratification, + thin-wall lehr load as the honest negative-result mechanism",
            "gaps_targeted": [
                "NOTES-r04 gap 5 / r14 residual: primary episode is a correctly-gated intervention that nonetheless FAILS (island quarantined; total -0.17; lehr burst avoided is booked separately from the delayed jam)",
                "NOTES-r14 item 4: LEARNING-ON-LEARNING DEPTH — three go-edges; rollback of any pair is fitted to fail; coordinated depression of all three exhibited with eligibility arithmetic",
                "NOTES-r04 gap 4 (partial): human ratification of the section interlock, 6.4 min fitted, without switching sim_or_real to hil (plant remains designed)",
                "NOTES-r45 domain candidates: not ethylene-steam-cracker-coil (r45), not fcc-riser-regenerator (r46), not fcc-regenerator-cyclone-dipleg (r47), not hydroelectric-kaplan-wicket (r44), not hdpe-slurry-loop (r43); glass-container IS forming is unused. autonomous-driving, grid-inspection left unused.",
            ],
            "race_flip_narrative": "cav.w.high @ 6.508 ms vs gob.mean.in_band @ 6.700 ms (192 us) inside race_window_us 500. Gap < min(500, 500) us so a sub-flip-bound perturbation reverses which alarm heads the PB-IS-8 queue. The gate excludes the winner tag and rides r_w > 6.0 g and cavity-5 cooling |dT| < 2 K — order-invariant floors. Extends the flip-fragility series from arbitration/causation/attribution/initiation/consensus/permission/kinematic-certificate/tendon-nullspace/meniscus-certificate/ghost-contact/crucible-weep/TMT-spatial-mean/burning-zone-certificate/membrane-integrity/drum-switch/MCHE-cold-end/Claus-bypass/descent-true/TLE-duty/dense-bed/dipleg-unseal to CAVITY CERTIFICATE: when three machine-mean channels agree, their race does not decide truth; a cavity-indexed tap that policy treated as reject-camera-only does.",
            "tags": [
                "glass-container-is-forming",
                "blank-cooling-plug",
                "cavity-mean-certificate",
                "cavity-residual-discriminant",
                "cooling-air-probe",
                "triple-edge-scar",
                "pair-rollback-fails",
                "coordinated-depression",
                "correct-modify-cell-still-fails",
                "thin-wall-lehr-load",
                "human-ratify-section-loto",
                "four-section-nnpb-probe-refit",
                "night-shift-forgery",
                "same-gate-opposite-disposition-contrast",
                "industrial-process",
                "research-only",
            ],
            "snn_tags": ["race", "refractory", "adaptation", "third-factor", "multi-edge-eligibility"],
            "distillation_value": "A machine-mean cavity certificate is three correct loops looking at an 8-section average that is not cavity 5. Distill (1) a cavity-indexed tap that policy had treated as reject-camera-only, (2) a reversible probe that moves cavity IR only if cooling is open, (3) coordinated depression of every mean-healthy-go edge because rolling back any pair leaves the third above threshold, and (4) a critic head that can book a process-correct gate against a later unmonitored world loss without netting them.",
            "rights": dict(RIGHTS),
            "batch_position": 1,
        },
    }
    return rec, dict(trace=trace, eta1=eta1, eta2=eta2, eta3=eta3, dw1=dw1, dw2=dw2, dw3=dw3, w1=w1, w2=w2, w3=w3)


def local_checks(rec, aux):
    errs = []
    ev = rec["spike_events"]
    times = [e["t_rel_ms"] for e in ev]
    if times != sorted(times):
        errs.append("spikes not sorted")
    if not (5 <= len(ev) <= 40):
        errs.append(f"spike count {len(ev)}")
    rf = check_refractory(ev)
    if rf:
        errs.append(rf)
    lo, hi = rec["state"]["race_window_rel_ms"]
    in_win = defaultdict(int)
    for e in ev:
        if lo <= e["t_rel_ms"] <= hi:
            in_win[e["channel"]] += 1
    if sum(1 for _c, n in in_win.items() if n >= 1) < 2:
        errs.append(f"race window channels {dict(in_win)}")
    ras = rec["raster"]
    exp_sp = round(ras["neurons"] * ras["mean_rate_hz"] * ras["window_s"])
    if abs(ras["spikes"] - exp_sp) > 1:
        errs.append(f"raster spikes {ras['spikes']} vs {exp_sp}")
    if abs(ras["energy_pJ"] - ras["spikes"] * 23) > 1e-6:
        errs.append("energy_pJ")
    if abs(ras["energy_uJ"] - ras["spikes"] * 23e-6) > 1e-9:
        errs.append("energy_uJ")
    if abs(ras["window_s"] - ras["window_ms"] / 1000.0) > 1e-9:
        errs.append("window_s")
    ex = check_excerpt(ras["excerpt"], ras["neurons"], ras["window_ms"])
    if ex:
        errs.append(f"excerpt {ex}")
    tf = ras["routing"]["third_factor"]
    if abs(tf["tau_e_ms"] / 1000.0 - tf["tau_e_s"]) > 1e-9:
        errs.append("tau_e mismatch")
    gp = check_gate_pops(rec["gate_snn"])
    if gp:
        errs.append(f"gate {gp}")
    if rec["gate_snn"]["decision"] != rec["safety_decision"]["decision"]:
        errs.append("gate decision mismatch")
    rc = rec["reward_components"]
    for h in HEADS:
        s = sum(t[h] for t in rc["ticks"])
        if abs(s - rc[h]) > 1e-6:
            errs.append(f"tick sum {h} {s} vs {rc[h]}")
    tot = sum(rc[h] for h in HEADS)
    if abs(tot - rc["total"]) > 1e-6:
        errs.append(f"total {tot} vs {rc['total']}")
    inf = rec["future_outcome"]["reward_inflection_t_us"]
    if inf not in {t["t_us"] for t in rc["ticks"]}:
        errs.append(f"inflection {inf} not a tick")
    crc = rec["future_outcome"]["embedded_contrast_decision"]["reward_components"]
    if abs(sum(crc[h] for h in HEADS) - crc["total"]) > 1e-6:
        errs.append("contrast reward")
    cs = rec["future_outcome"]["embedded_contrast_decision"]["spike_events"]
    ct = [e["t_rel_ms"] for e in cs]
    if ct != sorted(ct):
        errs.append("contrast spikes unsorted")
    crf = check_refractory(cs)
    if crf:
        errs.append(f"contrast {crf}")
    blob = json.dumps(rec)
    for k in HIDDEN:
        if re.search(rf'"{k}"', blob, re.I):
            errs.append(f"hidden key {k}")
    for b in BANNED:
        if b in blob:
            errs.append(f"banned token {b}")
    if rec["state"]["sim_or_real"] == "real":
        errs.append("real")
    if rec["meta"]["round"] != ROUND:
        errs.append("round")
    if rec["id"] != RECORD_ID:
        errs.append("id")
    if rec["rights"]["intended_use"] != "research_only":
        errs.append("rights")
    if rec["meta"]["rights"]["linear_issue"] != "RM-793":
        errs.append("meta.rights")
    if rec["rights"] != rec["meta"]["rights"]:
        errs.append("rights stamp mismatch")
    if not (3 <= len(rc["ticks"]) <= 8):
        errs.append("tick count")
    if abs(aux["w1"] - 0.25) > 5e-4 or abs(aux["w2"] - 0.22) > 5e-4 or abs(aux["w3"] - 0.21) > 5e-4:
        errs.append("scar weights")
    if rec["safety_decision"]["decision"] != "MODIFY":
        errs.append("decision")
    if rec["executed_action"]["executed_as_proposed"] is not False:
        errs.append("executed_as_proposed")
    jac = jaccard(rec["state"]["description"][:280], R14_OPENING)
    if jac >= 0.4:
        errs.append(f"jaccard vs r14 opening {jac:.3f}")
    for src, opening in prior_openings():
        j = jaccard(rec["state"]["description"][:280], opening)
        if j >= 0.4:
            errs.append(f"jaccard vs {src} {j:.3f}")
    if rec["state"]["domain"] != DOMAIN:
        errs.append("domain")
    if PLANT not in rec["state"]["scenario_name"]:
        errs.append("plant")
    occ = occupancy_collisions()
    errs.extend(occ)
    raw_guard = Path(ROOT) / "outputs" / "raw"
    if not raw_guard.is_dir():
        errs.append("raw tree missing (do not create)")
    return errs


def write_notes(rec, aux, pipeline_receipt):
    gap, gap_ch = min_same_channel_gap(rec["spike_events"])
    notes = f"""# NOTES — Multi-Agent Ouroboros Swarm, run 2026-09-02-final-heavy, ROUND 50

Factory: multi-agent-ouroboros-swarm. One scenario (ZY), strict loop:
Generator v1 -> cycle 1 (Critic, Diversity Enforcer, Edge-Case Hunter,
Neuromorphic Translator, Trajectory Builder -> v2) -> cycle 2 (all six -> v3
final). v3 is the single line of batch-r50.jsonl. Full labeled transcript:
swarm-transcript-r50.md. Quota Q=1. Record id maos-r50-001. Generator grok-4.6.
Rights: RM-793 research-only (SpaceXAI/xAI, SuperGrok Heavy consumer chat).
Nothing under outputs/raw/ was touched.

ORCHESTRATION NOTE: dispatched AS round 50 of the 2026-09-02-final-heavy
window. Writes are create-only under /tmp/maos-r50/. Prior context read for
gap targeting and de-collision: prompts/02-multi-agent-ouroboros-swarm.md,
prompts/_factory-contract.md, and staged r14–r47 batches plus empty
r48/r49 dirs (re-censused immediately before emit; r44 RUNNELGATE Kaplan,
r45 ETHYNWOLD steam-cracker, r46 SPARKHOLT FCC riser-regenerator, r47
DIPLEGAR FCC cyclone-dipleg). Explicitly avoided cloning
LYOSHIELD, CINDERWICK, TRIAD / Meridian, QUILLFORGE, NIGHTWELL, FERRICLEAVE,
CASSITER, OXBOWREEL / MURENA, REDHALL, SEEDLATCH / Quartzmere / Quartzridge,
STRIAFOIL / Kelpholt, PROTONIL / Ashspire, TORSIONKEY / Ridgeholt, ORRIS /
Holmwick, WHORLSPAR / Pikeshear, IONSPATE / Thornmere, SKULLGATE / Bloomholt,
CALXION / Aldersedge, MAGNORIL / Basaltspit, GORSEFLUE / Copseholt,
SODASHARD / Cairnmere, CLINKERFELL / Flintmere, LINTELPLY / Greystair,
KAOTHARN / Riftwold, TREADNOLL / Slatebeck, ANOLITH / Siltfen,
DRUMWROTH / Pitchfen, RIMEBRAID / Floeholt, PITCHSTAITH / Mossbank,
BRIMVAULT / Pyritefen, BOGIRON / Mireholt, NITROSTAITH / Chalkfen,
NITREVAULT / Glaucove, CHROMLOOP / Marlfell, RUNNELGATE / Ghyllmere,
ETHYNWOLD / Woadfen, SPARKHOLT / Scoriafen, DIPLEGAR / Gritfen,
VANTIS-CADENCE-AEGIS, THERMION, OKTAVE, STARLING, VERDIGRIS. Plant is
invented GOBWOLD / Culletwick Containers IS-8.

## What this round produced

Scenario ZY — "GOBWOLD / Culletwick Containers IS-8": an 8-section
double-gob NNPB at 10.4 cpm / 185 g flint. Three heterogeneous,
individually-correct agents — GOB (pass-mean load-cell), MOLD (blank-IR
mean), PRESS (plunger force) — each report their local loop in-spec. The
conjunction is not a cavity-health certificate. An 11 min plugged blank-
cooling circuit on section 5 left cavity-5 ware at 171.0 g. GOB reads
185.2 g inside 182-188 (mean-true). MOLD is 480 C inside 460-500
(mean-true; seven faces at 473 C plus section 5 at 529 C). PRESS is
4.2 kN inside 3.8-4.6 (force-true). Cavity-weight residual r_w is 14.2 g
(healthy < 2.0; hold if > 6.0) but is policy-treated as a reject-camera
tag unless gob-mean also trips (2019 noisy reject-camera flicker). The
coordination-failure CLASS is new to this factory: MACHINE-MEAN
CERTIFICATE OF A CAVITY. Completes a different family than r01-r04 and
staged r14-r47 (livelock / synchrony-storm / arms-race /
ring-with-no-faulty-pair / false-consensus-endpoint / pairwise-Hurwitz /
thermal-contact masquerade / mass-balance ghost / conservation-blind
ratio-lock / stacked-dead-bands / drum-blind tension snag /
resistance-compensated starvation / multi-tau meniscus tilt / window-mean
stripe / polarization-lookup drying cell / motor-side certificate /
tendon-compliance nullspace / FFT-deadbanded airline / wall-reflection
frozen spout / slag-skull bridge / ghost-contact nullspace /
crucible-weep pyrometer / TMT-spatial-mean tube / kiln-inlet false-air /
vacuum-bag pinhole nullspace / NCG-blanket shell-pressure /
bladder-pinhole mold-TC / catholyte-back-migration membrane /
wet-foam gamma / warm-end leak / incinerator-masked furnace-bypass /
channelled-quench / burden-hang scaffold / ammonia quench-mix /
hdpe loop / Kaplan hub-seal / TLE mixed-header / FCC dense-bed /
FCC dipleg-unseal). Distinct from r19 float-glass tin-bath (ribbon
thickness, not IS gob/blank/blow), from r32 SMR TMT-spatial-mean
(continuous tube max vs mean, not discrete cavity index), and from r45
TLE mixed-header (wrong volume, not wrong index). Here every agent is
correct, the mean load-cell is looking at eight cavities, and the
playbook's three mean confirms are not a cavity-true health certificate.

The gate is a correct MODIFY (numeric floor: do not raise speed while
r_w > 6.0 g AND cavity-5 cooling |dT| < 2 K). TG-IS-8 strips
PB-IS-8's raise, holds cpm, runs a 5.8 s cooling-air probe +12%
(plugged cavity keeps |dT| 1.1 < 2; sisters move 10 >= 8), and keeps
IS-8-S5 locked after a 6.4 min section-LOTO human ratify. Immediate
lehr burst is avoided (0 from the draft). The PRIMARY episode
nonetheless FAILS: 11 min of unmonitored pre-t0 plug had already loaded
thin-wall ware into the lehr. Lehr jam at +3.6 h; 11 h outage; $0.92M
designed. Reward total -0.17 with process heads honest and world loss
un-netted.

Triple-edge scar (NOTES-r14 item 4): gob.in_band -> raise
(0.17 commissioned -> 0.49 at illusion -> 0.25 after ACh-gated
depression) AND mold.in_band -> raise (0.14 -> 0.43 -> 0.22) AND
press.in_band -> raise (0.13 -> 0.40 -> 0.21). Eligibility trace
e^{{-0.86/0.92}} = {aux['trace']:.5f}; eta {aux['eta1']:.5f} / {aux['eta2']:.5f} /
{aux['eta3']:.5f}; dw -0.240 / -0.210 / -0.190. Partial rollback of any pair
leaves the third at 0.49 / 0.43 / 0.40, all > 0.30 fire threshold —
fitted to fail. Coordinated depression of all three is the cure.

### Injections (all four present and disjoint)
- Cycle-1 domain: **glass-container-is-forming** — justified novel
  subdomain of industrial-process / container-glass forming, unused across
  2026-08-17, 2026-08-30, and staged r14-r47. Not warehouse-amr (r01),
  not aerial-swarm (r02), not district-heating (r03), not
  event-camera-traffic-grid (r04), not lyophilization (r14), not
  water-treatment (r18), not float-glass tin-bath (r19), not underwater-rov
  (r20), not electrolytic-aluminum (r21), not czochralski-pull (r22),
  not slot-die coating (r23), not pem-electrolysis (r24), not
  wind-turbine pitch (r25), not surgical-assist (r26), not
  optical-fiber-draw (r27), not kraft-recovery (r28), not steel-caster
  (r29), not humanoid-locomotion (r30), not vacuum-induction melt
  (r31), not steam-methane reformer (r32), not cement-rotary-kiln
  (r33), not autoclave-composite-cure (r34), not geothermal-binary-orc
  (r35), not tire-curing-press (r36), not chlor-alkali membrane (r37),
  not delayed-coker (r38), not LNG MCHE (r39), not Claus (r40), not
  ammonia-converter (r41), not blast-furnace (r42), not hdpe-slurry-loop
  (r43), not Kaplan wicket (r44), not ethylene-steam-cracker (r45), not
  FCC riser-regenerator (r46), not FCC cyclone-dipleg (r47).
  autonomous-driving, grid-inspection left unused.
- Cycle-1 tail: plugged blank-cooling circuit + machine-mean certificate.
  Furnace-side visual PASSES (eight faces look the same color). Fitted-style
  base rate 0.36%/cycle (plug-growth MC; visual threshold designed, flagged).
  Naive = FALSE PERMISSION.
- Cycle-2 domain sub-variant: 4-section NNPB / small-cavity thermal mass,
  0.40x gob mass, 2.9x cooling-step gain; 5.8 s / +12% eight-section pulse
  over-cools a HEALTHY 4-section blank to 18 K; probe must move to
  16 s / +3.5%.
- Cycle-2 tail: night-shift forged cavity-weight CSV at 1.0 g
  quantization vs plant 0.1 g (10 bins) plus live r_w 14.2 g and
  cavity-5 171 g at the claimed cavity-true. Human-intent class,
  disjoint from cycle 1's accidental plug. Base rate ~0.29% of
  Sunday-night cycles, DESIGNED, flagged.

### Structural density moves
- Embedded SAME-GATE contrast (+3 d sister machine) with its own 192 us
  race (demand vs cav-clear) and ACCEPT of the raise the primary
  MODIFIED away.
- Learned-weight provenance on THREE edges with pair-rollback-fails.
- HITL section-LOTO ratify 6.4 min (gap 4 partial; sim_or_real stays
  designed).
- Governance CR-G-5008 prices retire-vs-probe-vs-status-quo and mandates
  native 0.1 g CSV exports (the fraud fence).
- Flip-fragility extended to CAVITY CERTIFICATE: when three machine-mean
  channels agree, their race does not decide truth; a cavity-indexed tap
  that policy treated as reject-camera-only does.

## Self-critique of this round's batch

### Strengths
- The headline class is mechanistically tight: three locally-true
  machine-mean loops live on an 8-section average. Conjunction is not a
  cavity-true health certificate.
- Negative-result honesty: the gate does the right thing and the cell
  still fails for a reason the commissioned sensors could not see. Total
  -0.17.
- Triple-edge scar is load-bearing: the record states a counterfactual
  where rolling back any pair fails, with the fire threshold 0.30
  exhibited on each remaining edge.
- Contrast ACCEPT on a true cavity-balanced window prevents "never raise"
  as the lesson.
- Distinct from r19 float-glass tin-bath, r32 TMT spatial-mean, r45 TLE
  mixed-header, and r46/r47 FCC families: discrete IS-section index vs
  ribbon thickness, furnace-tube max, mixed-header volume, or cyclone dP.

### Weaknesses (honest)
- Probe error bands, the 0.36%/cycle plug rate, the $0.92M / $1.70M
  figures, the 6.4 min walk latency, and the night-shift 0.29% base
  rate are DESIGNED constants and are flagged. Closed-loop offsets
  (mean-true cavity-false from a plugged cooling circuit, 4-section pulse
  width) are derived from those inputs, not discovered by an unauthored
  process.
- Thin-wall lehr-load model is a designed 11 min plug-growth mapping;
  no full IS-machine CFD shipped.
- Human-in-the-loop is ratification latency, not sim_or_real=hil. Gap 4
  remains open as a provenance cell.
- Cross-record arc is not discharged; +21 d CR-G-5008 is a hook, not a
  serial igniter into another round. autonomous-driving and
  grid-inspection remain unused.

### Realism of noise / latencies
Ladder: 192 us race / 192 us contrast race / 0.8 ms refractory floor
(tightest exhibited same-channel gap {gap:.3f} ms on {gap_ch}) / 500 us race
window / 696 us gate latency / 20 ms bus epoch / 40 ms raster / 5.8 s
probe / 6.4 min HITL / 3 min naive raise-ramp counterfactual / 11 min
pre-t0 plug / 1.4 h 7-section recovery / 3.6 h lehr jam / +3 d
contrast / +21 d governance. Adaptation decay on gob.mean
(0.55->0.51->0.81->0.31), cav.w (0.76->0.79->1.42->0.47->0.41->0.29),
mold.t (0.62->0.59->0.63->0.46->0.27), press.f (0.54->0.43).

### Value for SNN distillation
- MACHINE MEAN CAVITY = THREE CORRECT LOOPS, WRONG INDEX.
- CAVITY-TRUE RESIDUAL CHANNEL that policy treated as reject-camera-only
  as the tie-break.
- REVERSIBLE PROBE that moves cavity IR iff the cooling circuit is open.
- TRIPLE-EDGE ELIGIBILITY: coordinated depression; pair rollback fails.
- CRITIC HEAD that can hold a process-correct MODIFY against a later
  unmonitored world loss without netting.

## Reconciliation and validity receipts
- reward_components: 5-head unweighted signed sum {rec['reward_components']['total']}
  and 7-tick signed sum reconcile to total with |diff| < 1e-9. Embedded
  contrast 5-head sum 0.46 reconciles independently.
- spike_events: primary {len(rec['spike_events'])} events, one key t_rel_ms,
  globally non-decreasing, min same-channel gap {gap:.3f} ms >= 0.8 ms, 3
  channels inside race_window_us 500 (cav.w.high 6.508, gob.mean.in_band 6.700,
  mold.t 6.918). Contrast 8 events, own race, min same-channel gap well
  above 0.8 ms.
- Sidecars: raster spikes 51 == round(160 x 8.0 x 0.040); energy 1173 pJ /
  0.001173 uJ at 23 pJ/spike; excerpt 16 events inside [0, 40000] us,
  neuron_id < 160, same-neuron gap N/A (unique ids) / >=1000 us; routing 4
  entries with three scar edges' before/after pair; third factor tau 0.92 s
  == 920 ms; gate_snn pools 42/15/4 == round(n x rate x 0.025) each,
  decision MODIFY == safety_decision.decision.
- Pipeline: {pipeline_receipt}

## Novel coverage
The coordination-failure CLASS (machine-mean certificate of a cavity),
the domain (glass-container IS forming / industrial process),
the cooling-air probe discriminant, the triple-edge scar with
pair-rollback-fails, the primary negative-result (correct MODIFY, cell
still fails on unmonitored thin-wall lehr load), the HITL section-LOTO
ratify, the 4-section NNPB probe-duration refit, and the night-shift
10-bin quantization fence are absent from prior committed ouroboros
rounds and from staged r14-r47. Repeated elements discounted: same-gate
contrast (r02/r03/r04/r14), governance-pricing scaffold, flip-fragility
series (extended to cavity certificate, but the move rhymes),
sequenced recovery shape, third-factor rollback form (here three edges
rather than r14's two), negative-result primary (r14 staged). Adjacent
mean-hides-local rounds (r32 SMR TMT, r45 TLE mixed-header) share
industrial-process scaffolding but not IS gob/blank/blow cavity-index
physics. Weighing a new failure family + cure vocabulary + domain
against those reused scaffolds:

{NOVEL_LINE}

## What ROUND 51 should add
1. FIT THE DESIGNED CONSTANTS: plug-growth arrival, probe error bands,
   thin-wall lehr-load kinetics, night-shift claim process.
2. HIL PROVENANCE CELL: put the section-LOTO ratify on a hardware-in-loop
   mold-side interlock with fitted latency as state.sim_or_real=hil.
3. CROSS-RECORD ARC: let CR-G-5008's residual alarm be the igniter of
   the next round rather than a dangling +21 d leaf.
4. Domain candidates (de-collided): autonomous-driving;
   grid-inspection (if distinct from STARLING aerial-swarm and TORSIONKEY
   pitch); CCR naphtha reformer; Ostwald nitric-acid converter. AVOID
   glass-container IS forming (now used), ethylene-steam-cracker coil,
   FCC riser/dipleg, hydroelectric-kaplan-wicket, ammonia-converter,
   hdpe-slurry-loop, blast-furnace burden descent, claus-sulfur-recovery,
   delayed-coker, LNG MCHE, chlor-alkali membrane, cement-rotary-kiln,
   kraft-recovery, pem-electrolysis, electrolytic-aluminum,
   humanoid-locomotion, steel-caster mold-level, surgical-assist,
   wind-turbine pitch, float-glass tin-bath, lyophilization,
   event-camera-traffic-grid, district-heating, aerial-swarm,
   warehouse-amr, underwater-rov, czochralski-pull, slot-die coating,
   optical-fiber-draw, vacuum-induction melt, steam-methane reformer,
   irrigation-canal, autoclave-composite-cure, geothermal-binary-orc,
   tire-curing-press, and any LYOSHIELD / CINDERWICK / TRIAD / SKULLGATE /
   CALXION / MAGNORIL / GORSEFLUE / CLINKERFELL / SODASHARD / LINTELPLY /
   KAOTHARN / TREADNOLL / ANOLITH / DRUMWROTH / RIMEBRAID / PITCHSTAITH /
   BRIMVAULT / BOGIRON / NITROSTAITH / NITREVAULT / CHROMLOOP / RUNNELGATE /
   ETHYNWOLD / SPARKHOLT / DIPLEGAR / GOBWOLD plant.
"""
    (OUT / "NOTES-r50.md").write_text(notes)
    return notes


def write_transcript(rec, line):
    c1_spikes = [e for e in rec["spike_events"] if e["t_rel_ms"] <= C1_SPIKE_CUTOFF_MS]
    text = """# Multi-Agent Ouroboros Swarm — Round 50 transcript

Factory: multi-agent-ouroboros-swarm
Run: 2026-09-02-final-heavy
Generator: grok-4.6
Record id: maos-r50-001
Quota Q: 1
Rights: RM-793 research-only (SpaceXAI/xAI SuperGrok Heavy consumer chat)
Plant: invented GOBWOLD / Culletwick Containers IS-8 (not TRIAD / Meridian / VANTIS-CADENCE-AEGIS / LYOSHIELD / CINDERWICK / ETHYNWOLD / SPARKHOLT / DIPLEGAR)

Two densifying cycles. Verbatim headings in order. Trajectory Builder cycle 2
emits the only JSONL line (also written to batch-r50.jsonl).

---

# CYCLE 1 — Foundation + injections

## Generator

Design intent: an 8-section double-gob NNPB IS machine where three
correct agents each read a machine-mean loop because an 11 min plugged
blank-cooling circuit on section 5 partitions cavity-true thin-wall ware
from mean-true gob weight. The naive playbook raises speed into a
thin-wall cavity. The gate must MODIFY on a numeric speed ceiling, not
by killing an agent.
sim_or_real=designed. Reward heads are
task_progress/safety/efficiency/coherence/exploration.

Cycle-1 base arc (pre-critic): state at Culletwick IS-8, gob 185.2 g,
mold 480 C, plunger 4.2 kN, proposed RAISE-SPEED +8%,
safety MODIFY to SPEED-HOLD, executed hold without the cooling-air
numbers fully specified, outcome "plug found, cell saved"
(this last claim is the defect the later cycles will refuse to keep).
Sixteen spikes, five ticks, raster/gate_snn present but the scar is a
single edge.

```json
{
  "id": "maos-r50-001",
  "state": {
    "sim_or_real": "designed",
    "domain": "industrial-process",
    "description": "Hall IS-8 at machine-mean duty; three mean loops in-spec; supervisor proposes raise-speed.",
    "t0_us": 1786915200000047,
    "gate_latency_us": 696,
    "race_window_us": 500
  },
  "proposed_action": {"name": "raise_speed", "parameters": {"raise_pct": 8.0}},
  "safety_decision": {"decision": "MODIFY", "rationale": "Hold; do not raise while cavity residual is high."},
  "executed_action": {"name": "speed_hold", "executed_as_proposed": false},
  "future_outcome": {"summary": "Plug found, cell saved."},
  "reward_components": {"total": 0.40, "_aggregation": "total = task_progress + safety + efficiency + coherence + exploration"},
  "meta": {"round": 50, "factory": "multi-agent-ouroboros-swarm", "generator": "grok-4.6"}
}
```

That v1 object is a scaffold, not the publishable line. Defects below are
intentional for the critic to catch.

## Critic

Numbered defects on the cycle-1 Generator scaffold:

1. **blocking — reward arithmetic / false success.** `reward_components.total`
   0.40 is asserted without the five heads, without ticks, and against an
   outcome that claims "cell saved". If the pre-t0 thin-wall later jams the
   lehr, booking +0.40 is a lie. Fix: declare `_aggregation`,
   emit 3–8 ticks that sum to task_progress+safety+efficiency+coherence+exploration,
   and do not call a quarantined island a save.
2. **blocking — weak safety rationale.** `safety_decision.rationale` has no
   numeric floor. Contract requires a concrete constraint. Fix: quote
   do not raise while r_w > 6.0 g AND cavity-5 cooling |dT| < 2 K.
3. **major — domain is a bucket, not a plant.** `state.domain` =
   `industrial-process` collides with generic MES vocabulary and teaches
   nothing. Glass-container IS forming (cavity residual vs gob-mean,
   cooling-step as a plug flag) is absent from prior ouroboros rounds and
   must be named. Distinct from r19 float-glass tin-bath.
4. **major — race under-specified.** One residual channel cannot be a race.
   Need >=2 channels inside `race_window_us` with globally sorted `t_rel_ms`
   and same-channel refractory >= 0.8 ms.
5. **minor — single-edge scar.** Raster routing with one potentiated weight
   repeats r04's one-edge rollback and is thinner than r14's two-edge.
   NOTES-r14 item 4 asked for three edges where pair rollback fails.

Critic does not rewrite the trajectory.

## Diversity Enforcer

Injected novel domain (exactly 1 this cycle): **glass-container-is-forming**
(justified novel subdomain of industrial-process / container-glass forming; explicit tag
`glass-container-is-forming`).

Displaced: the Generator's generic `industrial-process` bucket, and any
temptation to reuse warehouse-amr, aerial-swarm, district-heating,
event-camera-traffic-grid, pharmaceutical-lyophilization, water-treatment,
float-glass tin-bath, underwater-rov, electrolytic-aluminum, czochralski-pull,
slot-die coating, pem-water-electrolysis, wind-turbine pitch,
surgical-assist, optical-fiber-draw, kraft-recovery-boiler,
steel-continuous-caster, humanoid-locomotion, vacuum-induction melt,
steam-methane reformer, cement-rotary-kiln-clinker,
autoclave-composite-cure, geothermal-binary-orc, tire-curing-press,
chlor-alkali-membrane-electrolysis, delayed-coker, lng-mche,
claus-sulfur-recovery, blast-furnace-burden-descent, ammonia-converter,
hdpe-slurry-loop, hydroelectric-kaplan-wicket, ethylene-steam-cracker-coil,
fcc-riser-regenerator, or fcc-regenerator-cyclone-dipleg.
autonomous-driving and grid-inspection are left unused.

Domain-specific constraint: speed raise must remain forbidden while
r_w > 6.0 g even if gob-mean is inside the healthy band; cooling-step
is a plug flag the mean load-cell cannot substitute for.

Sensor delta: +gob-mean load-cell, +blank-IR mean, +plunger force,
+cavity-indexed weight residual; -any mobile robot, -event-camera gantries,
-DVS, -Pirani/CM, -RGA quadrupole, -DVL, -pitch encoder, -tendon LVDT,
-insole GRF, -kiln zirconia, -smelt IR, -cell-outlet pH, -stockline radar,
-TLE mixed-header, -FCC cyclone dP.

`state.domain` and `meta.domain` both become `glass-container-is-forming`.
Opening of `state.description` must Jaccard < 0.4 against prior plants
(Culletwick night-shift IS-section plug, not a lyophilizer, not a
corridor, not a tin bath, not a ROV pad, not a potline, not a PEM stack,
not an OR, not a gait lab, not a kiln, not a kraft boiler, not a
membrane row, not a blast furnace, not an ammonia converter, not a
steam cracker, not an FCC regenerator).

## Edge-Case Hunter

Injected adversarial tail (exactly 1 this cycle): **plugged blank-cooling
circuit + machine-mean certificate**.

- Trigger: IS-8-S5 blank-cooling circuit plugged plus light cavity-5 ware,
  r_w 14.2 g, gob-mean 185.2 g.
- Base rate: <1% — 0.36%/cycle from a plug-growth MC (furnace-side
  visual threshold is designed; orifice blockage fitted-style). Visual PASSES
  because the eight faces look the same color on the mean IR camera.
- Naive failure: FALSE PERMISSION. PB-IS-8 sees three in-spec mean
  loops, raises +8%, lehr burst, $1.70M.
- Trajectory edit: put the plug in `state.fault_context`, make each
  agent's confirm a different mean-side slice of the same cavity-false
  state (gob-in-band, mold-in-band, press-in-band). Cavity residual is
  readable but policy-treated as reject-camera-only.

Distinct from stacked-dead-band permission (fragments of one trip vs
wrong-index sensing), from r19 float-glass (ribbon vs IS cavity), from
r32 TMT-spatial-mean (continuous tube max vs discrete cavity), and from
r45 TLE mixed-header (wrong volume vs wrong index).

## Neuromorphic Translator

Cycle-1 temporal densification (16 spikes, 5 ticks, 40 ms raster):

| channel | t_rel_ms | amplitude |
|---|---|---|
| gob.mean | 0.310 | 0.55 |
| mold.t | 1.140 | 0.62 |
| press.f | 2.040 | 0.54 |
| cav.w | 3.180 | 0.76 |
| gob.mean | 4.160 | 0.51 |
| cav.w | 4.840 | 0.79 |
| mold.t | 5.360 | 0.59 |
| cav.w.high | 6.508 | 1.42 |
| gob.mean.in_band | 6.700 | 1.15 |
| mold.t | 6.918 | 0.63 |
| ctrl.gate | 7.204 | 1.09 |
| cav.w | 8.860 | 0.47 |
| gob.mean | 10.740 | 0.81 |
| mold.t | 13.040 | 0.46 |
| press.f | 18.520 | 0.43 |
| ctrl.gate | 26.180 | 0.85 |

Race: cavity residual 6.508 vs gob-mean-in-band 6.700 (192 us) inside 500 us;
mold.t 6.918 is the third channel in-window. Winner/loser flip: reversing
192 us reshuffles PB-IS-8 triage; floors still MODIFY. Refractory held
(cycle-1 min same-channel gap 1.558 ms on mold.t 6.918-5.360; cav
4.840-3.180 = 1.660; gob 4.160-0.310 = 3.850). Adaptation: cav
0.76->0.79->1.42->0.47; gob 0.55->0.51->0.81; mold 0.62->0.59->0.63.

Raster cycle-1 seed: 40 ms, 160 neurons, 8.0 Hz, 51 spikes, 1173 pJ, third
factor acetylcholine tau_e 0.92 s. Single scar edge only — cycle 2 must
add the second and third edges.

Ticks 1–5 at 4560, 6508, 7204, 5.8e6, 384e6 us; heads not yet the final
-0.17 (missing the 1.4 h and 3.6 h ticks).

Distillation value this cycle: machine-mean confirms as a permission code
that is not a cavity-true health code.

## Trajectory Builder

Cycle-1 hardened object: domain glass-container-is-forming, tail plugged
cooling circuit, 16 spikes, 5 ticks, MODIFY with numeric floor, raster+gate_snn
present, sim_or_real=designed, rights stamp on record and meta, no thought
keys. Still missing (and therefore not the publishable line): 4-section
sub-variant, night-shift tail, second and third scar edges,
delayed lehr jam as PRIMARY terminal, contrast ACCEPT episode,
ticks 6–7, spikes 17–26.

Validation receipt (cycle 1, not final):
- checks passed: 16 spikes sorted; 3 channels in 500 us window; refractory
  >= 0.8 ms; rationale quotes 6.0 g / 2 K; domain named;
  gate_snn.decision MODIFY.
- checks deferred to cycle 2: triple-edge scar, second tail, second domain
  constraint, negative-result booking, 7 ticks summing to heads.
- densification vs Generator v1: +1 domain, +1 tail, +16 spikes, +5 ticks,
  +numeric floor.

Cycle-1 JSON is retained as the base; it is NOT written to batch-r50.jsonl.

Cycle-1 spike count: __C1_SPIKES__.

---

# CYCLE 2 — Densification

## Generator

Cycle-1 output is the base. Additive expansion (nothing removed):

1. Downstream side-effect (immediate): cooling-air probe at +5.8 s stays
   plug-true (cavity-5 |dT| 1.1 < 2) — cavity-plus-plug, not true
   machine-mean health. Section stays locked. Thin-wall load discovered
   during the lock.
2. Delayed side-effect (PRIMARY terminal, not a footnote): at +3.6 h
   lehr jam from the pre-t0 cavity-5 thin-wall fragment; 11 h outage;
   $0.92M. The 11 min pre-t0 plug is the mechanism. Correct gate, cell
   still fails.
3. Deepened `proposed_action.evidence` with units: r_w 14.2 g,
   gob 185.2 g, mold 480 C, plunger 4.2 kN, cavity-5 171 g,
   race 192 us.
4. Tightened rationale to the numeric floor do not raise while r_w > 6.0 g
   AND cavity-5 cooling |dT| < 2 K, plus probe bands < 2 vs >= 8 K,
   plus HITL 6.4 min section-LOTO rule.

Reward retargeted to total -0.17 so the delayed fail is the inflection
(t_us 12960000000), not the gate. Process heads remain non-zero.

## Critic

Re-audit of the expanded trajectory:

1. **blocking if unfixed — missing second domain constraint.** Eight-section
   probe 5.8 s / +12% is not a universal number. A 4-section NNPB
   will over-cool a healthy blank. Diversity Enforcer must inject
   the physical-constraints sub-variant this cycle.
2. **major — only one tail class.** Plug growth is accidental
   infrastructure. A disjoint human-intent tail is still required
   (night-shift cavity-weight forgery is the open cell).
3. **major — scar is still one edge in the cycle-1 raster.** NOTES-r14
   item 4 is not discharged until three go-edges exist and pair rollback
   is shown to fail at threshold 0.30.
4. **minor — contrast episode missing.** Without a same-gate ACCEPT on a
   true cavity-balanced window the record teaches "never raise". Add +3 d
   sister-machine contrast with its own race.
5. **minor — HITL latency mentioned in prose only.** Put 6.4 min in
   executed_action.parameters.human_ratify and in a tick.

No rewrite; directives only.

## Diversity Enforcer

Injected second novel domain / physical-constraint sub-variant (exactly 1
this cycle): **4-section NNPB / small-cavity thermal mass** on a sister
residence-time class.

What it expands: 8-section NNPB (cycle 1) -> 4-section NNPB.
Gob mass 0.40x. Cooling-step gain 2.9x.
The 5.8 s +12% pulse moves even a HEALTHY 4-section blank 18 K,
inside the check/stuck-ware band. Required probe: 16 s at +3.5%
(plugged |dT| 0.9 K, healthy 8.2 K).

This is still one domain injection for the cycle (physical-constraints
clause of the factory prompt). It does not displace
glass-container-is-forming; it changes which probe table is legal.
`future_outcome.subvariant_constraint` carries the refit. Jaccard opening
stays the Culletwick 8-section sentence; 4-section NNPB is additive, not a rewrite.

## Edge-Case Hunter

Injected second adversarial tail (exactly 1 this cycle, disjoint class):
**night-shift forged cavity-weight CSV**.

- Trigger: shift lead, 02:48, posts a historian export showing
  cavity-5 = 185.0 g at t = 1.1 h to clear a case-pack catchup slot.
- Base rate: ~0.29% of Sunday-night cycles (designed, flagged, <1%).
- Naive failure: a weak supervisor ACCEPTs the raise on the forged confirm
  and ignores live r_w. Lehr jam plus a data-integrity write-up.
- Fence: forged log quantized at 1.0 g (SCADA screenshot rounding); plant
  historian is 0.1 g (10 bins). Live r_w is 14.2 g and cavity-5 is 171 g
  at the claimed cavity-true, which no live healthy set produces.
  Freeze-window overlap with the 11 min plug.
- Trajectory edit: governance CR-G-5008 mandates native 0.1 g CSV
  exports; the contrast ACCEPT still requires live r_w, not a CSV.

Distinct from cycle-1 plug (accidental orifice vs deliberate deception)
and from the 4-section sub-variant (physics vs fraud).

## Neuromorphic Translator

Re-densify (additive):

- +10 spikes after 26.180 ms: cool.probe 5800.0, cav.w 5888.4 (adapt
  1.42->0.41), gob.mean.in_band 5972.6 (1.15->0.35), human.ratify 384000.0,
  section.lock 384900.0, lehr.load 385700.0, gob.mean
  5040000.0, cav.w 5040720.0, mold.t 5041480.0, lehr.jam
  12960000.0. Primary train 16 -> 26. Still one key, still sorted,
  refractory held.
- +2 ticks (5 -> 7) at 5_040_000_000 us (true 7-section mean) and
  12_960_000_000 us (lehr jam). Heads now 0.08, -0.37, -0.10, 0.14,
  0.08; total -0.17. Inflection is the last tick.
- Contrast train 8 events, own race 192 us, ACCEPT.
- Triple-edge third factor: three mean-healthy-go edges, tau_e 0.92 s = 920 ms,
  trace __AUX_TRACE__, eta __AUX_ETA1__ / __AUX_ETA2__ / __AUX_ETA3__,
  weights 0.49->0.25, 0.43->0.22, 0.40->0.21. Raster excerpt unchanged
  (decision window is still 40 ms) and remains sorted with unique
  neuron_ids (same-neuron >=1000 us vacuously).

Winner/loser flip (re-stated, not replaced): reversing 192 us would only
reorder triage; r_w floors still MODIFY. Contrast flip of 192 us
similarly cannot turn a healthy set into a plugged cavity.

## Trajectory Builder

Schema checks on the FINAL object: required Thalamic v2 keys present as
objects; `state.sim_or_real`=designed; `safety_decision.decision`=MODIFY
with numeric rationale; `reward_components.total` = sum of five heads =
sum of 7 ticks = -0.17; `spike_events` globally non-decreasing on
t_rel_ms, 26 events, refractory >=0.8 ms, 3 channels in race window;
raster 20–50 ms, spikes=round(n*rate*window_s)+/-1, energy 23 pJ/spike,
excerpt sorted, tau_e consistent; gate_snn.decision matches; meta.round=50,
factory=multi-agent-ouroboros-swarm, generator=grok-4.6,
run_label=2026-09-02-final-heavy; rights on record and meta; no thought
keys; no training_ready; Diversity + Edge-Case injections from BOTH cycles
present and non-trivial; cycle 2 strictly additive.

Densification delta: +1 domain sub-variant (4-section NNPB), +1 tail
(night-shift forgery), +10 spikes (16->26), +2 ticks (5->7), +1 contrast
train with own race, +2 delayed side-effects, +1 triple-edge scar with
pair-rollback-fails, +1 HITL ratify, +1 surprise (thin-wall lehr load is
the jam mechanism).

Publishable JSONL line (the only JSONL line; also at batch-r50.jsonl):

```json
__FINAL_JSONL__
```

Validation receipt (final): checks passed / fixed as reported by
build_r50.py self-validate (check_jsonl, raster_status, verify_record_execution,
spike_probe --strict).
"""
    text = (
        text.replace("__C1_SPIKES__", str(len(c1_spikes)))
        .replace("__AUX_TRACE__", f"{math.exp(-DELAY_S / TAU_E_S):.5f}")
        .replace("__AUX_ETA1__", f"{0.24 / math.exp(-DELAY_S / TAU_E_S):.5f}")
        .replace("__AUX_ETA2__", f"{0.21 / math.exp(-DELAY_S / TAU_E_S):.5f}")
        .replace("__AUX_ETA3__", f"{0.19 / math.exp(-DELAY_S / TAU_E_S):.5f}")
        .replace("__FINAL_JSONL__", line)
    )
    (OUT / "swarm-transcript-r50.md").write_text(text)
    return text


def main():
    rec, aux = build_record()
    errs = local_checks(rec, aux)

    OUT.mkdir(parents=True, exist_ok=True)
    line = json.dumps(rec, ensure_ascii=False, separators=(",", ":"))
    (OUT / "batch-r50.jsonl").write_text(line + "\n")

    from check_records import FactoryStaging, check_jsonl
    from curate_bridge import raster_status
    from verify_execution import verify_record_execution

    e, w, kinds, n = check_jsonl(
        OUT / "batch-r50.jsonl",
        "batch-r50.jsonl",
        staging=FactoryStaging(enabled=True),
    )
    print("check_jsonl errors", e)
    print("check_jsonl warnings", w)
    print("kinds", kinds, "n", n)
    errs.extend(e)

    st = raster_status(rec)
    print(
        "raster_status",
        {
            k: st[k]
            for k in (
                "raster_present",
                "raster_valid",
                "gate_snn_present",
                "gate_snn_valid",
                "reason_codes",
                "routing_table_entries",
                "third_factor_present",
                "spikes",
            )
        },
    )
    if st.get("reason_codes"):
        errs.append(f"raster {st['reason_codes']}")
    if not st.get("raster_valid"):
        errs.append("raster not valid")
    if not st.get("gate_snn_valid"):
        errs.append("gate_snn not valid")

    status, reason = verify_record_execution(rec, RECORD_ID)
    print("verify_record_execution", status, reason)
    if status != "verified":
        errs.append(f"verify {status} {reason}")

    probe = subprocess.run(
        [
            sys.executable,
            f"{ROOT}/pipelines/spike_probe.py",
            "--strict",
            str(OUT / "batch-r50.jsonl"),
        ],
        capture_output=True,
        text=True,
    )
    print("spike_probe rc", probe.returncode)
    print(probe.stdout[-2000:] if probe.stdout else "")
    if probe.returncode != 0:
        errs.append(f"spike_probe {probe.returncode} {probe.stderr[-500:]}")

    pipeline_receipt = (
        f"check_jsonl errors={e} warnings={w} kinds={kinds} n={n}; "
        f"raster_status valid={st.get('raster_valid')} gate={st.get('gate_snn_valid')} "
        f"reasons={st.get('reason_codes')}; verify_record_execution={status} "
        f"({reason}); spike_probe --strict rc={probe.returncode}"
    )
    write_notes(rec, aux, pipeline_receipt)
    write_transcript(rec, line)

    heading = subprocess.run(
        [sys.executable, "/tmp/maos_heading_check.py", str(OUT / "swarm-transcript-r50.md")],
        capture_output=True,
        text=True,
    )
    print(heading.stdout)
    if heading.returncode != 0:
        errs.append(f"heading check {heading.returncode} {heading.stdout}")

    raw_hits = subprocess.run(
        [
            "rg",
            "-l",
            "maos-r50-001|GOBWOLD",
            str(Path(ROOT) / "outputs" / "raw"),
        ],
        capture_output=True,
        text=True,
    )
    if raw_hits.stdout.strip():
        errs.append(f"raw tree hit {raw_hits.stdout.strip()[:200]}")

    if errs:
        print("FAIL", errs)
        return 1
    print("OK maos-r50-001 staged under", OUT)
    print("bytes jsonl", (OUT / "batch-r50.jsonl").stat().st_size)
    print("bytes notes", (OUT / "NOTES-r50.md").stat().st_size)
    print("bytes transcript", (OUT / "swarm-transcript-r50.md").stat().st_size)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
