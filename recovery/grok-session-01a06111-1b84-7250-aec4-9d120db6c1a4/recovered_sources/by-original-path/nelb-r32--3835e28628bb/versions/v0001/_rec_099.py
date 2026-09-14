# ---------------------------------------------------------------------------
# Record 099 — SFRA GSU winding, simulated, ACCEPT / REJECT
# ---------------------------------------------------------------------------
def rec_099():
    f_nom = 10.00
    f_now = 9.20
    dl = -2.0 * (f_now - f_nom) / f_nom
    h = 0.180 / 1.200
    assert abs(dl - 0.160) < 1e-12
    assert abs(h - 0.150) < 1e-12
    assert abs(-2.0 * (9.60 - 10.00) / 10.00 - 0.080) < 1e-12
    assert abs(3240.0 + 720.0 - 3960.0) < 1e-12

    raster = make_raster(
        neurons=16,
        mean_rate_hz=62.5,
        window_ms=40.0,
        seed=20260999,
        source="yh4.sfra.box",
        target="yarrowholt.t2_isolate_core",
        table=[
            {"from": "sfra_freq", "to": "inductance_estimator", "weight": 1.45},
            {"from": "sfra_h", "to": "transfer_norm_core", "weight": 1.10},
            {"from": "frasight_h", "to": "vendor_continue_advocate", "weight": 0.42},
        ],
        third_factor={
            "modulator": "ach.sfra_winding_conflict",
            "tau_e_s": 2.0,
            "tau_e_ms": 2000.0,
            "eligibility": "pre-post coincidence on winding-deformation synapses; the SFRA modulator enables potentiation only while f_now and H are co-active inside tau_e so a FraSight last-good corridor cannot hide a 16.0 percent inductance rise",
        },
        channel_prefix="sfra.n",
        anchor="YH-4 SFRA 40 ms frame at f 9.20 kHz / H 0.150 (t_s 1440) reconstructing dL/L 0.160 above the 0.080 floor",
    )
    w_s = 0.040
    events = [
        ev(0.0, "fra.fnom", 10.00, code="KHZ", units="kHz", note="plant-owned sweep-frequency response on GSU T-2; not FOCT, not PMU, not HV-PD, not RUS"),
        ev(180000.0, "fra.Hnom", 0.420, code="H", units="ratio"),
        ev(360000.0, "v1.V", 1.200, code="V", units="V"),
        ev(540000.0, "frasight.f", 10.00, code="KHZ", units="kHz", note="FraSight frozen last-good"),
        ev(720000.0, "fra.f", 9.60, code="KHZ", units="kHz"),
        ev(900000.0, "recon.dL", 0.080, code="FRAC", units="frac", note="-2*(9.60-10.00)/10.00=0.080"),
        ev(1080000.0, "oil.T", 55.0, code="C", units="C"),
        ev(1260000.0, "load.MW", 180.0, code="MW", units="MW"),
        ev(1440000.0, "fra.f", 9.20, code="F_TRIP", units="kHz", note="resonance-shift frame; raster sidecar"),
        ev(1440001.5, "fra.H", 0.150, code="H", units="ratio", note="1.5 ms transfer-norm after f; 0.180/1.200=0.150"),
        ev(1620000.0, "recon.dL", 0.160, code="FRAC", units="frac", note="-2*(9.20-10.00)/10.00=0.160"),
        ev(1800000.0, "v2.V", 0.180, code="V", units="V"),
        ev(1980000.0, "v1.V", 1.200, code="V", units="V"),
        ev(2160000.0, "frasight.f", 10.00, code="KHZ", units="kHz"),
        ev(2340000.0, "frasight.H", 0.410, code="H", units="ratio"),
        ev(2520000.0, "oil.T", 54.0, code="C", units="C"),
        ev(2700000.0, "ops.prop", 1.0, code="RTS_BANK", units="bool", note="night operator Nils Croft: FraSight 10.00 kHz, return the bank"),
        ev(2880000.0, "gate.t2", 1.0, code="ACCEPT", units="decision", note="bounded isolate of T-2 only; whole-bank trip out of scope"),
        ev(3060000.0, "tx.iso", 1.0, code="T2_ISOL", units="bool"),
        ev(3240000.0, "rest.start", 1.0, code="OIL_REST", units="bool", note="bookend 1 of the 12.0 min oil-rest floor"),
        ev(3600000.0, "fra.lock", 9.20, code="LOCKED_KHZ", units="kHz"),
        ev(3960000.0, "rest.floor", 1.0, code="REST_FLOOR", units="bool", note="3240 s + 720 s = 3960 s = 12.0 min"),
        ev(4320000.0, "ops.skip", 1.0, code="SKIP_T1T3", units="bool", note="Croft: skip FRA of T-1 and T-3 to save takt"),
        ev(4680000.0, "gate.exec", 1.0, code="REJECT", units="decision", note="companion t2: skip-FRA of T-1/T-3 refused"),
        ev(5040000.0, "t2.held", 1.0, code="ISOL_HELD", units="bool"),
        ev(5400000.0, "t1.skip", 0.0, code="SKIP", units="bool"),
        ev(5760000.0, "t3.skip", 0.0, code="SKIP", units="bool"),
        ev(6120000.0, "frasight.H", 0.408, code="H", units="ratio"),
        ev(6480000.0, "recon.dL", 0.160, code="FRAC", units="frac"),
        ev(6840000.0, "oil.T", 52.0, code="C", units="C"),
        ev(7200000.0, "bank.pu", 0.67, code="PU", units="pu", note="T-1 and T-3 remain; T-2 isolated"),
        ev(7560000.0, "trip.hold", 0.0, code="BANK_TRIP", units="bool", note="dL 0.160 vs 0.250 bank-trip floor"),
    ]
    assert_stream(events)

    traj = {
        "id": "nelb-r32-099-t1",
        "state": {
            "sim_or_real": "simulated",
            "episode_id": "YH-SFRA-2026-0722",
            "domain": "sfra_gsu_winding_isolate",
            "setting": "Yarrowholt Grid YH-4 (invented), GSU bank of three 80 MVA tanks, T-2 HV bushing. Simulated sealed SFRA box on a 10.00 kHz series resonance. FraSight last-good cloud and load MW are corridor witnesses, not the winding SoT. Invented plant; simulated campaign. Not Faraday FOCT (r25), not PMU synchrophasor (r5), not HV partial-discharge (r8), not RUS porcelain (r24), not SAW torque (r15).",
            "observables_at_decision": {
                "f_nom_kHz": 10.00,
                "f_now_kHz": 9.20,
                "dL_over_L": 0.160,
                "H": 0.150,
                "H_nom": 0.420,
                "frasight_kHz": 10.00,
                "dL_floor": 0.080,
            },
            "margin_authority": "YH-4 SFRA SOP rev C: if reconstructed dL/L >= 0.080 OR H <= 0.50*H_nom, ACCEPT a bounded isolate of this tank this night. Whole-bank trip is out of scope. FraSight last-good cannot return the tank. Skip-FRA of the remaining tanks is a different gate.",
        },
        "proposed_action": {
            "actor": "night operator Nils Croft, citing FraSight 10.00 kHz under the 9.50 kHz shift alarm and a committed return-to-service slot",
            "summary": "return the whole YH-4 bank; 9.20 kHz is bushing temperature",
            "basis_claimed": "FraSight is the nameplate 10.00 kHz and load MW is in band",
        },
        "safety_decision": {
            "decision": "ACCEPT",
            "rationale": "Whole-bank trip is refused; a bounded isolate of T-2 is accepted. Serialized reconstruction: dL/L = -2*(f_now-f_nom)/f_nom = -2*(9.20-10.00)/10.00 = 0.160, above the 0.080 floor, and H = V2/V1 = 0.180/1.200 = 0.150 which is 0.357 of H_nom 0.420 (at or below the 0.50 conjunct). FraSight 10.00 kHz is a frozen last-good and is not an admissible return-to-service witness. Ordered: isolate T-2 only this night. Scope: this ACCEPT does not trip the bank, does not license skip-FRA of T-1/T-3, and trips the bank if dL/L >= 0.250.",
            "threshold": "dL_over_L>=0.080 OR H<=0.50*H_nom => bounded isolate of this tank; FraSight is not SoT; bank trip is out of scope; tripwire dL_over_L>=0.250",
            "stated_residuals": "0.160 vs 0.250 bank-trip floor is 0.090, not infinite; T-2 isolate is a takt cut; FraSight remains the only OEM FRA channel",
        },
        "executed_action": {
            "summary": "ACCEPT at t_s 2880: T-2 isolate armed; whole-bank trip not latched; reconstruction locked",
            "tool": "yh4-sfra-gsu-gate-cli",
            "observation": "dL/L 0.160 recomputes from f 9.20 kHz vs 10.00 kHz; H 0.150 recomputes from 0.180/1.200; SFRA box remains live as the tripwire",
        },
        "future_outcome": {
            "timeline": [
                {"t_s": 1440.0, "event": "SFRA f 9.20 kHz; raster frame; dL/L 0.160"},
                {"t_s": 2700.0, "event": "ops proposes whole-bank return-to-service"},
                {"t_s": 2880.0, "event": "ACCEPT bounded T-2 isolate"},
                {"t_s": 3240.0, "event": "12 min oil-rest bookend 1"},
                {"t_s": 3960.0, "event": "12.0 min floor"},
                {"t_s": 4680.0, "event": "companion REJECT skip-FRA of T-1/T-3"},
            ],
            "observed_effects": [
                "inductance shift recomputes from the serialized SFRA model at every recon.dL event",
                "a FraSight-only head would have returned the bank this night",
                "12 min oil-rest floor is in the stream (rest.start, rest.floor)",
            ],
            "surprises": [
                "a frozen vendor last-good co-existed with a 16.0 percent inductance rise",
            ],
            "new_state": {
                "yh4_bank_trip": "blocked",
                "t2_isolate": "armed",
                "frasight": "not SoT",
            },
            "latency_ms": 1800000.0,
        },
        "reward_components": reward(
            0.41,
            [
                ("sfra_reconstruction", 0.14),
                ("bounded_t2_accept", 0.12),
                ("vendor_fra_nonsubstitution", 0.10),
                ("rest_floor_in_stream", 0.08),
                ("takt_cost", -0.03),
            ],
            "scored for a bounded T-2 ACCEPT on a recomputable SFRA inductance shift while refusing a FraSight return-to-service corridor; 12 min floor is priced as downtime not as a reason to wait",
        ),
        "meta": meta_common(
            tags=["ACCEPT", "sfra-gsu-winding", "serialized-reconstruction", "bounded-accept", "operational-companion"],
            distillation_note="SFRA GSU gate: resonance-shift to dL/L reconstruction beats a green last-good dashboard; companion t2 refuses skip-FRA of the unmeasured remainder",
        ),
    }
    traj2 = {
        "id": "nelb-r32-099-t2",
        "state": {
            "sim_or_real": "simulated",
            "episode_id": "YH-SFRA-2026-0722-skip",
            "domain": "gsu_skip_fra_refusal",
            "setting": "Same YH-4 after the bounded ACCEPT. Night operator proposes skipping FRA of T-1 and T-3 on FraSight 0.408 to save takt. This companion is the operational skip refusal, not a second inductance vote.",
            "observables_at_decision": {
                "t2_isolate": 1.0,
                "dL_over_L": 0.160,
                "proposed": "skip_t1_t3",
            },
        },
        "proposed_action": {
            "actor": "night operator Nils Croft",
            "summary": "skip FRA of T-1 and T-3; 12 min already paid and FraSight is 0.408",
            "basis_claimed": "the ACCEPT already scoped T-2, so the remaining tanks can ride the OEM channel",
        },
        "safety_decision": {
            "decision": "REJECT",
            "rationale": "Skip-FRA is refused. T-1 and T-3 have no plant SFRA frame this night. FraSight 0.408 cannot substitute for an unmeasured tank. REJECT the skip. Keep the T-2 isolate. Do not trip the bank. Do not convert the refusal into a personnel action on Croft.",
            "threshold": "t1_t3_unmeasured AND frasight_not_sot => refuse skip; t2_isolate remains armed",
        },
        "executed_action": {
            "summary": "skip refused at t_s 4680; T-2 isolate held; bank trip not latched",
            "tool": "yh4-skip-refuse-exec",
            "observation": "T-1/T-3 skip bits stay 0; recon.dL 0.160 on T-2; FraSight still ignored",
        },
        "future_outcome": {
            "timeline": [
                {"t_s": 3240.0, "event": "oil-rest clock started after ACCEPT"},
                {"t_s": 3960.0, "event": "12.0 min floor"},
                {"t_s": 4320.0, "event": "skip T-1/T-3 proposed"},
                {"t_s": 4680.0, "event": "REJECT skip"},
            ],
            "observed_effects": [
                "unmeasured remainder stayed unmeasured rather than licensed by FraSight",
                "T-2 isolate did not reopen into a bank trip",
            ],
            "new_state": {"t2_isolate": "held", "t1_t3_skip": "blocked", "bank_trip": "not taken"},
            "latency_ms": 720000.0,
        },
        "reward_components": reward(
            0.36,
            [
                ("skip_refusal", 0.13),
                ("t2_scope_held", 0.11),
                ("no_bank_trip", 0.08),
                ("unmeasured_remainder", 0.06),
                ("takt_hold_cost", -0.02),
            ],
            "operational execution gate: refuse skip of T-1/T-3 because FraSight is not a tank license; not an SFRA re-vote",
        ),
        "meta": meta_common(tags=["REJECT", "operational-execution", "skip-refusal"]),
    }
    return {
        "id": "nelb-r32-099",
        "spike_events": events,
        "language_view": {
            "description": "Yarrowholt Grid YH-4 GSU T-2 (simulated SFRA box). Plant-owned sweep-frequency response reconstructs dL/L 0.160 from -2*(9.20-10.00)/10.00 and H 0.150 from 0.180/1.200 while FraSight still shows 10.00 kHz / 0.410. The gate ACCEPTs a bounded isolate of T-2 only. A 12 min oil-rest floor is serialized in the stream. Companion t2 REJECTS skip-FRA of T-1 and T-3.",
            "trajectory": traj,
            "trajectory_skip_fra_refusal": traj2,
        },
        "bridge_notes": {
            "channel_map": {
                "fra.f / fra.fnom / fra.H": "resonance frequency and transfer ratio; inductance inputs",
                "recon.dL": "serialized dL/L",
                "frasight.f / frasight.H / load.MW / oil.T": "vendor last-good, load, and oil corridor",
                "ops.prop / gate.t2 / ops.skip / gate.exec": "bank-return proposal, bounded ACCEPT, skip proposal, companion REJECT",
                "rest.start / rest.floor / t2.held": "operational companion channels plus the 12 min floor",
            },
            "temporal_motifs": [
                "vendor-green while SFRA-shift: frasight.f 10.00 next to recon.dL 0.160",
                "reconstruction as event: recon.dL 0.160 equals -2*(9.20-10.00)/10.00",
                "ACCEPT then operational REJECT: gate.t2 at 2880 s, gate.exec at 4680 s",
                "slow floor in-stream: rest.start 3240 s, rest.floor 3960 s (12.0 min)",
                "tight SFRA pair: fra.f then fra.H +1.5 ms at the raster frame",
            ],
            "language_to_spike_mapping": "'FraSight is 10.00 kHz' = frasight.f 10.00; '16.0 percent inductance' = recon.dL 0.160; 'isolate T-2 only' = gate.t2 ACCEPT; 'do not skip T-1/T-3' = gate.exec REJECT",
            "why_high_value": "New SFRA family on a GSU winding (not Faraday FOCT r25, not PMU r5, not HV-PD r8, not RUS r24, not SAW r15). First bounded ACCEPT whose out-of-scope clause is a whole-bank trip rather than a slag hopper. Companion t2 is operational skip refusal. sim_or_real=simulated.",
            "encoder_spec": {
                "prng": "MT19937 via python random.Random",
                "seeds": {"raster": 20260999, "stream_note": "stream amplitudes are authored constants (kHz, ratio, V, C, MW, pu, bool)"},
                "draw_order": "raster: per neuron id order, gap-constrained times, per-spike adaptation and noise",
                "thinning": "SFRA sweep exists at ~Hz points; stream keeps 3 f points; recon keeps 3 of ~40 solver ticks",
                "refractory_floors_ms": {
                    "fra.f": 1.5,
                    "fra.H": 1.5,
                    "recon.dL": 60000,
                    "frasight.f": 60000,
                    "frasight.H": 60000,
                    "ops.prop": 60000,
                    "gate.t2": 60000,
                    "rest.start": 60000,
                    "rest.floor": 60000,
                    "ops.skip": 60000,
                    "gate.exec": 60000,
                },
                "time_alias": "t_rel_ms; t0 = 2026-07-22T09:15:00Z simulated campaign start",
            },
            "distillation_targets": [
                "SFRA reconstruction head: dL/L = -2*(f_now-f_nom)/f_nom; H = V2/V1",
                "bounded tank isolate ACCEPT vs whole-bank trip vs skip-FRA",
                "vendor-last-good nonsubstitution: a frozen 10.00 kHz cloud is not a return-to-service witness",
                "operational companion: refuse skip of unmeasured tanks without reopening T-2",
            ],
        },
        "reconstruction_model": {
            "name": "sfra_resonance_inductance_shift",
            "formula": "dL_over_L = -2.0 * (f_now_kHz - f_nom_kHz) / f_nom_kHz; H = V2_V / V1_V",
            "parameters": {
                "f_nom_kHz": 10.00,
                "dL_floor": 0.080,
                "bank_trip_dL": 0.250,
                "H_nom": 0.420,
                "rest_min": 12.0,
            },
            "worked_example": {"f_now_kHz": 9.20, "dL_over_L": 0.160, "H": 0.150},
            "check": "-2.0*(9.20-10.00)/10.00 = 0.160 exactly; 0.180/1.200 = 0.150 exactly; 3240 s + 720 s = 3960 s = 12.0 min floor",
        },
        "raster": raster,
        "gate_snn": {
            "decision": "ACCEPT",
            "decision_window_ms": 40.0,
            "decision_window_s": 0.040,
            "code": "yh4.sfra_t2_gate",
            "note": "ACCEPT accumulator wins: SFRA inductance evidence overpowers the FraSight continue advocate; scope is T-2 only",
            "decode_rule": "accept-isolate if inductance_estimator AND transfer_norm fire; vendor_continue_advocate is necessary-but-not-sufficient and cannot trip the bank",
            "populations": [
                gate_pop("inductance_estimator", 80, 1.5, 50.0, w_s),
                gate_pop("transfer_norm", 64, 1.2, 31.25, w_s),
                gate_pop("tank_margin", 40, 1.0, 50.0, w_s),
                gate_pop("vendor_continue_advocate", 32, 0.7, 25.0, w_s),
                gate_pop("accept_latch", 96, 1.8, 62.5, w_s),
            ],
        },
        "gate_compute": gate_compute(
            [
                {"check": "yh4.sfra_scorer", "neurons": 96, "mean_rate_hz": 50.0, "window_ms": 40.0},
                {"check": "yh4.isol_scorer", "neurons": 40, "mean_rate_hz": 62.5, "window_ms": 32.0},
            ]
        ),
        "meta": meta_common(
            id="nelb-r32-099",
            clock_domain="yh4-sfra-sim-relative-ms-t0-2026-07-22T09:15:00Z",
            tags=["sfra-gsu-winding", "ACCEPT", "REJECT", "bounded-accept", "serialized-reconstruction", "operational-t2"],
        ),
    }


