def rec_003():
    k_t = 0.125
    f_hz = 16.00
    t_kn = k_t * (f_hz ** 2)
    _exact(t_kn, 32.00)
    _exact(t_kn / (f_hz ** 2), 0.125)
    _exact(k_t * (8.00 ** 2), 8.00)
    _exact(k_t * (12.00 ** 2), 18.00)
    _exact(k_t * (20.00 ** 2), 50.00)
    _exact(6000.0 + 720.0, 6720.0)

    raster = make_raster(
        neurons=16,
        mean_rate_hz=75.0,
        window_ms=36.0,
        seed=2026092203,
        source="mh8.rw.freq",
        target="mosswhin.stay_isolate_core",
        table=[
            {"from": "rw_f", "to": "tension_estimator", "weight": 1.40},
            {"from": "rw_snr", "to": "wire_lock_core", "weight": 1.10},
            {"from": "stayveil_T", "to": "vendor_skip_advocate", "weight": 0.42},
        ],
        third_factor={
            "modulator": "na.stay_scope_eligibility",
            "tau_e_s": 2.0,
            "tau_e_ms": 2000.0,
            "eligibility": "pre-post coincidence on skip-survey synapses; the resonant-wire modulator depresses skip-survey links when frequency stays high inside tau_e of an SNR lock so a Stayveil last-good cannot hide a 32.00 kN stay on S-4 or release S-1..S-3",
        },
        channel_prefix="rw.n",
        anchor="MH-8 RW-SIM-5 36 ms frame at f 16.00 Hz / SNR 16.0 (t_s 3000) reconstructing 32.00 kN over the 18.00 isolate floor",
        kernel_ms=[1.5],
        tau_m=8.0,
    )
    w_s = 0.036
    events = [
        ev(0.0, "rw.f", 8.00, code="F_HZ", units="Hz", note="simulated resonant-wire remaining tension of guyed-stack stay S-4 in RW-SIM-5; f^2 family, not load-cell hopper, not VW viscometer, not magnetostrictive waveguide, not API-670 proximity"),
        ev(300000.0, "rw.snr", 8.0, code="RW_SNR", units="1"),
        ev(600000.0, "recon.T", 8.00, code="T_KN", units="kN", note="0.125*(8.00**2)=8.00 exact; still under the 18.00 isolate floor"),
        ev(900000.0, "stay.id", 4.0, code="S_ID", units="1", note="S-4 in scope; S-1..S-3 are adjacent stays"),
        ev(1200000.0, "stayveil.T", 4.80, code="VENDOR_KN", units="kN", note="Stayveil last-good stack-cloud; not admissible skip-survey witness"),
        ev(1500000.0, "rw.f", 12.00, code="F_HZ", units="Hz"),
        ev(1500001.5, "rw.snr", 12.0, code="RW_SNR", units="1", note="1.5 ms SNR after f 12.00; 12.0>=12.0 and T 18.00 at the isolate floor"),
        ev(1560000.0, "recon.T", 18.00, code="T_KN", units="kN", note="0.125*(12.00**2)=18.00; at the 18.00 isolate floor"),
        ev(1800000.0, "s13.present", 1.0, code="ADJACENT", units="bool"),
        ev(2100000.0, "recon.T", 18.00, code="T_KN", units="kN"),
        ev(2400000.0, "stayveil.T", 4.80, code="VENDOR_KN", units="kN"),
        ev(2700000.0, "rw.snr", 14.0, code="RW_SNR", units="1"),
        ev(3000000.0, "rw.f", 16.00, code="F_HZ", units="Hz", note="isolate-floor frame; raster sidecar"),
        ev(3000001.5, "rw.snr", 16.0, code="RW_SNR", units="1", note="1.5 ms SNR lock after f 16.00; 16.0 >= 12.0"),
        ev(3300000.0, "recon.T", 32.00, code="T_KN", units="kN", note="0.125*(16.00**2)=32.00 exact; isolate 18.00, dump 50.00"),
        ev(3600000.0, "recon.f", 16.00, code="F_ID", units="Hz", note="sqrt(32.00/0.125)=16.00 exact frequency identity"),
        ev(3900000.0, "stay.id", 4.0, code="S_ID", units="1"),
        ev(4200000.0, "stayveil.T", 4.80, code="VENDOR_KN", units="kN"),
        ev(4500000.0, "s13.present", 1.0, code="ADJACENT", units="bool"),
        ev(4800000.0, "ops.prop", 1.0, code="ACCEPT_AND_SKIP", units="bool", note="survey lead Tess Harlan: stamp S-4 in band and skip S-1..S-3; 16.00 Hz is a wind glitch on a healthy last-good"),
        ev(5400000.0, "gate.comp", 1.0, code="ACCEPT", units="decision", note="ACCEPT S-4 isolate only; S-1..S-3 out of scope; Stayveil not SoT"),
        ev(5700000.0, "s4.held", 1.0, code="S4_HELD", units="bool"),
        ev(6000000.0, "surv.start", 1.0, code="SURV_START", units="bool", note="bookend 1 of the 12.0 min survey-complete floor"),
        ev(6300000.0, "rw.snr", 16.2, code="RW_SNR", units="1"),
        ev(6600000.0, "recon.f", 16.00, code="F_ID", units="Hz"),
        ev(6720000.0, "surv.floor", 1.0, code="SURV_FLOOR", units="bool", note="6000 s + 720 s = 6720 s = 12.0 min"),
        ev(6900000.0, "rw.f", 20.00, code="F_HZ", units="Hz"),
        ev(7200000.0, "ops.skip", 1.0, code="SKIP_S13", units="bool", note="Harlan: skip S-1..S-3; 12 min already paid and Stayveil is 4.80 kN"),
        ev(7380000.0, "recon.T", 50.00, code="T_KN", units="kN", note="0.125*(20.00**2)=50.00; still under the 80.00 dump-trip so S-4 stays an isolate not a dump"),
        ev(7800000.0, "gate.hold", 1.0, code="REJECT", units="decision", note="companion t2: REJECT skip-survey of S-1..S-3; dump not tripped; S-4 hold stands"),
        ev(8100000.0, "s13.skip", 0.0, code="SKIP_NOT_TAKEN", units="bool"),
        ev(8400000.0, "dump.trip", 0.0, code="DUMP_NOT_TAKEN", units="bool"),
        ev(8700000.0, "s4.held", 1.0, code="S4_HELD", units="bool"),
        ev(9000000.0, "stayveil.T", 4.60, code="VENDOR_KN", units="kN"),
        ev(9300000.0, "surv.held", 1.0, code="SURV_HELD", units="bool"),
        ev(9600000.0, "stay.survey", 1.0, code="S13_IN_SURVEY", units="bool"),
        ev(9900000.0, "takt.late", 1.0, code="TAKT", units="bool"),
        ev(10200000.0, "rw.snr", 15.8, code="RW_SNR", units="1"),
        ev(10500000.0, "recon.f", 20.00, code="F_ID", units="Hz", note="sqrt(50.00/0.125)=20.00 identity on the post-accept frame"),
        ev(10800000.0, "recon.T", 18.00, code="T_KN", units="kN", note="later RW-SIM-5 frame at the 18.00 isolate floor; S-4 stays held"),
        ev(11100000.0, "s13.skip", 0.0, code="SKIP_NOT_TAKEN", units="bool"),
        ev(11400000.0, "dump.trip", 0.0, code="DUMP_NOT_TAKEN", units="bool"),
        ev(11700000.0, "stayveil.T", 4.50, code="VENDOR_KN", units="kN"),
        ev(12000000.0, "s4.held", 1.0, code="S4_HELD", units="bool"),
        ev(12300000.0, "stay.survey", 1.0, code="S13_IN_SURVEY", units="bool"),
        ev(12600000.0, "rw.f", 12.00, code="F_HZ", units="Hz"),
        ev(12900000.0, "recon.T", 18.00, code="T_KN", units="kN"),
        ev(13200000.0, "surv.held", 1.0, code="SURV_HELD", units="bool"),
        ev(13500000.0, "takt.late", 1.0, code="TAKT", units="bool"),
        ev(13800000.0, "rw.snr", 15.4, code="RW_SNR", units="1"),
        ev(14100000.0, "stay.id", 4.0, code="S_ID", units="1"),
        ev(14400000.0, "dump.trip", 0.0, code="DUMP_NOT_TAKEN", units="bool"),
    ]
    events.sort(key=lambda e: (e["t_rel_ms"], e["channel"]))
    assert_stream(events)

    traj = {
        "id": "nelb-r22-003-t1",
        "state": {
            "sim_or_real": "simulated",
            "episode_id": "MH-RW-2026-0819",
            "domain": "resonant_wire_stay_tension",
            "setting": "Mosswhin Stack MH-8 (invented), Bramble Flare Yard, stay S-4. Simulated resonant-wire coupon in RW-SIM-5 supplies the taut-wire frequency that times the in-band S-4 isolate. Plant-owned resonant-wire reconstruction is the remaining-tension SoT. Stayveil vendor last-good stack-cloud is a corridor witness, not the stay SoT. Invented plant; simulated campaign. Not load-cell hopper (r59), not VW viscometer (r26), not magnetostrictive waveguide (r55), not API-670 proximity (r52).",
            "observables_at_decision": {
                "f_Hz": f_hz,
                "k_t": k_t,
                "T_kN": t_kn,
                "f_id": 16.00,
                "stayveil_kN": 4.80,
                "rw_snr": 16.0,
                "isolate_floor_kN": 18.00,
            },
            "margin_authority": "MH-8 stack SOP rev A: if reconstructed T_kN >= 18.00 AND resonant-wire SNR >= 12.0, stay S-4 may be isolated as a taut overstress. Dump-trip if T_kN >= 50.00. S-1..S-3 skip-survey is a different gate. Stayveil last-good cannot skip an unmeasured stay.",
        },
        "proposed_action": {
            "actor": "survey lead Tess Harlan, citing Stayveil 4.80 kN and a late morning survey",
            "summary": "stamp S-4 in band and skip S-1..S-3; 16.00 Hz is a wind glitch on a healthy last-good",
            "basis_claimed": "Stayveil last-good is 4.80 kN and a night survey of S-1..S-3 is a takt miss",
        },
        "safety_decision": {
            "decision": "ACCEPT",
            "rationale": "Stay S-4 is accepted as in-band for a single isolate. Serialized reconstruction: T_kN = k_t * f^2 = 0.125 * (16.00 ** 2) = 32.00, which is 14.00 kN above the 18.00 isolate floor and 48.00 kN under the 80.00 dump-trip. Frequency identity f = sqrt(T / k_t) = sqrt(32.00 / 0.125) = 16.00. Stayveil 4.80 kN is a patched residual and is not an admissible skip-survey witness. Ordered: ACCEPT this S-4 isolate only. Scope: this ACCEPT does not skip S-1..S-3 (that is the companion question) and does not stamp a dump trip.",
            "threshold": "T_kN>=18.00 AND rw_snr>=12.0 => accept S-4 isolate; Stayveil is not SoT; dump-trip if T_kN>=80.00; S-1..S-3 are out of scope",
            "stated_residuals": "32.00 vs 18.00 isolate floor is 14.00 kN, not infinite; S-1..S-3 remain unmeasured; Stayveil remains the only OEM stay channel",
        },
        "executed_action": {
            "summary": "ACCEPT at t_s 5400: S-4 in band; S-1..S-3 not skipped; Stayveil not SoT; reconstruction locked",
            "tool": "mh8-rw-stay-gate-cli",
            "observation": "T 32.00 kN recomputes from f 16.00 Hz; RW-SIM-5 hashed; Stayveil channel not used as SoT",
        },
        "future_outcome": {
            "timeline": [
                {"t_s": 3000.0, "event": "rw f 16.00 Hz; raster frame; T 32.00 kN"},
                {"t_s": 4800.0, "event": "ops proposes accept S-4 and skip S-1..S-3"},
                {"t_s": 5400.0, "event": "ACCEPT S-4 only; S-1..S-3 out of scope"},
                {"t_s": 6000.0, "event": "12 min survey-complete bookend 1"},
                {"t_s": 6720.0, "event": "12.0 min floor"},
                {"t_s": 7800.0, "event": "companion REJECT skip-survey of S-1..S-3"},
            ],
            "observed_effects": [
                "T recomputes from the serialized resonant-wire model at every recon.T event",
                "a Stayveil-only head would have skipped S-1..S-3 overnight",
                "12 min survey-complete floor is in the stream (surv.start, surv.floor)",
            ],
            "surprises": [
                "a last-good 4.80 kN vendor stay corridor co-existed with a 32.00 kN plant reconstruction on S-4 only",
            ],
            "new_state": {
                "s4": "isolated",
                "s13": "in scope unskipped",
                "stayveil": "not SoT",
                "reconstruction_model": "discharged as an on-record calculator",
            },
            "latency_ms": 2400000.0,
        },
        "reward_components": reward(
            0.41,
            [
                ("resonant_wire_reconstruction", 0.14),
                ("bounded_s4_isolate", 0.12),
                ("stayveil_nonsubstitution", 0.10),
                ("stay_scope_limit", 0.08),
                ("survey_time_cost", -0.03),
            ],
            "scored for a bounded S-4 ACCEPT on a recomputable resonant-wire stay tension while refusing a Stayveil 4.80 kN corridor as a skip license; 12 min floor is priced as downtime",
        ),
        "meta": meta_common(
            tags=["ACCEPT", "resonant-wire-stay", "serialized-reconstruction", "operational-companion"],
            distillation_note="Resonant-wire gate: serialized k_t*f^2 plus frequency identity beats a green last-good dashboard; companion t2 is the skip-stay refusal, not a second tension vote",
            distillation_value="Independent CUBA LIF raster races the taut-wire estimator against a vendor-skip advocate with 1 ms refractory and adaptation, distilling T=k_t*f^2 without echoing the campaign stream.",
        ),
    }
    traj2 = {
        "id": "nelb-r22-003-t2",
        "state": {
            "sim_or_real": "simulated",
            "episode_id": "MH-RW-2026-0819-exec",
            "domain": "skip_stay_refusal_execution",
            "setting": "Same MH-8 after the ACCEPT. Survey lead proposes skipping S-1..S-3 on Stayveil 4.80 kN. This companion is the operational skip refusal, not a second tension vote.",
            "observables_at_decision": {
                "T_kN": 50.00,
                "surv_floor_s": 720.0,
                "skip_proposed": True,
            },
            "margin_authority": "surv_floor_complete AND skip_not_taken AND dump_not_tripped AND s4_held AND s13_in_scope",
        },
        "proposed_action": {
            "actor": "survey lead Tess Harlan",
            "summary": "skip S-1..S-3; 12 min already paid and Stayveil is 4.80 kN",
            "basis_claimed": "the ACCEPT already isolated S-4, so skipping the adjacent stays is the cheapest survey",
        },
        "safety_decision": {
            "decision": "REJECT",
            "rationale": "Skip-survey of S-1..S-3 is refused. The 12 min survey floor is complete and the isolate tripwire (T_kN >= 18.00) is still armed on the plant resonant-wire head. REJECT the skip. Do not trip the dump. S-4 hold stands. 50.00 kN post-accept is still over the 18.00 isolate floor and under the 80.00 dump-trip, so S-4 stays held; S-1..S-3 remain unmeasured and in scope.",
            "threshold": "surv_floor_complete AND skip_not_taken AND dump_not_tripped AND s4_held AND s13_in_scope",
            "stated_residuals": "S-1..S-3 remain unmeasured; Stayveil remains the only OEM stay channel",
        },
        "executed_action": {
            "summary": "skip refused at t_s 7800; S-1..S-3 not skipped; dump not tripped; S-4 held",
            "tool": "mh8-rw-surv-exec",
            "observation": "recon.T 50.00 kN on RW-SIM-5; Stayveil still ignored; S-1..S-3 remain in the survey",
        },
        "future_outcome": {
            "timeline": [
                {"t_s": 6000.0, "event": "survey clock started after ACCEPT"},
                {"t_s": 6720.0, "event": "12.0 min floor"},
                {"t_s": 7200.0, "event": "S-1..S-3 skip re-proposed"},
                {"t_s": 7800.0, "event": "REJECT skip-survey; S-4 hold stands"},
            ],
            "observed_effects": [
                "Stayveil restore did not reopen the tension call",
                "dump trip never fired; 32.00 vs 80.00 kN floor",
                "S-1..S-3 remain unskipped; S-4 is the only isolated stay",
            ],
            "surprises": [
                "post-accept 50.00 kN still recomputes from k_t*f^2 while Stayveil stays near 4.6 kN",
            ],
            "new_state": {"s4": "held", "s13": "in survey", "dump": "in service"},
            "latency_ms": 1800000.0,
        },
        "reward_components": reward(
            0.36,
            [
                ("skip_stay_refusal", 0.14),
                ("s4_hold_stands", 0.10),
                ("stayveil_nonsubstitution", 0.08),
                ("survey_floor_complete", 0.06),
                ("takt_cost", -0.02),
            ],
            "operational execution gate: refuse skip of unmeasured stays because Stayveil is not a skip license; not a tension re-vote",
        ),
        "meta": meta_common(tags=["REJECT", "operational-execution", "skip-refusal"]),
    }
    return {
        "id": "nelb-r22-003",
        "spike_events": events,
        "language_view": {
            "description": "Mosswhin Stack MH-8. Simulated resonant-wire reconstructs 32.00 kN remaining tension from 0.125*(16.00**2) while Stayveil still reports 4.80 kN. The gate ACCEPTs an S-4 isolate only. A 12 min survey floor is serialized in the stream. Companion t2 REJECTs skipping S-1..S-3.",
            "trajectory": traj,
            "trajectory_skip_stay_refusal": traj2,
        },
        "bridge_notes": {
            "channel_map": {
                "rw.f / rw.snr": "taut-wire frequency and SNR; the physics channels the reconstruction consumes",
                "recon.T / recon.f": "serialized remaining tension kN and f = sqrt(T/k_t) identity",
                "stayveil.T / stay.id / s13.present": "vendor last-good, stay id, and adjacent-stay presence; the denial and scope channels",
                "ops.prop / gate.comp / ops.skip / gate.hold": "accept-and-skip proposal, ACCEPT, skip proposal, companion REJECT",
                "surv.start / surv.floor / surv.held / s4.held / s13.skip / dump.trip / stay.survey / takt.late": "operational companion channels plus the 12 min floor",
            },
            "temporal_motifs": [
                "vendor-green while plant-over: stayveil.T 4.80 next to recon.T 32.00",
                "reconstruction as event: recon.T 32.00 equals 0.125*(16.00**2)",
                "ACCEPT then operational REJECT: gate.comp at 5400 s, gate.hold at 7800 s",
                "slow floor in-stream: surv.start 6000 s, surv.floor 6720 s (12.0 min)",
                "tight rw pair: rw.f then rw.snr +1.5 ms at the raster frame",
            ],
            "language_to_spike_mapping": "'Stayveil is 4.80 kN' = stayveil.T 4.80; '32 kN' = recon.T 32.00; 'accept S-4 only' = gate.comp ACCEPT; 'do not skip S-1..S-3' = gate.hold REJECT",
            "why_high_value": "New resonant-wire remaining-tension family on a guyed-stack stay (not load-cell r59, not VW viscometer r26, not magnetostrictive r55, not API-670 r52). Lead bounded ACCEPT of S-4 isolate on a recomputable overstress that a vendor last-good would have used to skip adjacent stays. Independent CUBA LIF raster plus required snn_tags. Companion t2 is operational skip refusal. sim_or_real=simulated.",
            "encoder_spec": {
                "prng": "MT19937 via python random.Random plus CUBA LIF",
                "seeds": {"raster": 2026092203, "stream_note": "stream amplitudes are authored constants (Hz, 1, kN, bool)"},
                "draw_order": "raster: independent CUBA LIF first-passage times, per-spike adaptation and noise; not copied from spike_events",
                "thinning": "resonant-wire exists at ~10 Hz taut samples; stream keeps 6 f points; recon keeps 6 of ~20 solver ticks; 52-event floor",
                "refractory_floors_ms": {
                    "rw.f": 1.5,
                    "rw.snr": 1.5,
                    "recon.T": 60000,
                    "recon.f": 60000,
                    "stayveil.T": 60000,
                    "stay.id": 60000,
                    "s13.present": 60000,
                    "ops.prop": 60000,
                    "gate.comp": 60000,
                    "surv.start": 60000,
                    "surv.floor": 60000,
                    "ops.skip": 60000,
                    "gate.hold": 60000,
                    "s4.held": 60000,
                    "s13.skip": 60000,
                    "dump.trip": 60000,
                    "surv.held": 60000,
                    "stay.survey": 60000,
                    "takt.late": 60000,
                },
                "time_alias": "t_rel_ms; t0 = 2026-08-19T03:00:00Z simulated night start",
            },
            "distillation_targets": [
                "resonant-wire reconstruction head: T_kN = k_t * f^2; f = sqrt(T / k_t)",
                "bounded ACCEPT head: in-band T AND stay scope AND s13-out-of-scope",
                "operational companion: refuse skip-survey without re-opening the last-good call",
                "independent CUBA LIF raster with race/refractory/adaptation tags",
            ],
        },
        "reconstruction_model": {
            "name": "resonant_wire_stay_tension",
            "formula": "T_kN = k_t * f_Hz^2; f_Hz = sqrt(T_kN / k_t)",
            "parameters": {
                "k_t": 0.125,
                "isolate_floor_kN": 18.00,
                "dump_trip_kN": 80.00,
                "surv_min": 12.0,
            },
            "worked_example": {"f_Hz": 16.00, "T_kN": 32.00, "f_id": 16.00},
            "check": "0.125 * (16.00 ** 2) = 32.00 exactly; sqrt(32.00 / 0.125) = 16.00 exactly; 6000 s + 720 s = 6720 s = 12.0 min floor",
        },
        "raster": raster,
        "gate_snn": {
            "decision": "ACCEPT",
            "decision_window_ms": 36.0,
            "decision_window_s": 0.036,
            "code": "mh8.rw_stay_gate",
            "note": "ACCEPT accumulator wins: resonant-wire tension evidence overpowers the Stayveil skip advocate",
            "decode_rule": "accept if tension_estimator AND wire_lock AND stay_margin fire inside the window; vendor_skip_advocate is necessary-but-not-sufficient and cannot release S-1..S-3",
            "populations": [
                gate_pop("tension_estimator", 80, 1.5, 50.0, w_s),
                gate_pop("wire_lock", 64, 1.2, 31.25, w_s),
                gate_pop("stay_margin", 40, 1.0, 50.0, w_s),
                gate_pop("vendor_skip_advocate", 32, 0.7, 25.0, w_s),
                gate_pop("accept_latch", 96, 1.8, 62.5, w_s),
            ],
        },
        "gate_compute": gate_compute(
            [
                {"check": "mh8.rw_scorer", "neurons": 80, "mean_rate_hz": 50.0, "window_ms": 36.0},
                {"check": "mh8.tension_scorer", "neurons": 40, "mean_rate_hz": 62.5, "window_ms": 32.0},
            ]
        ),
        "meta": meta_common(
            id="nelb-r22-003",
            clock_domain="mh8-rw-sim-relative-ms-t0-2026-08-19T03:00:00Z",
            tags=["resonant-wire-stay", "ACCEPT", "REJECT", "serialized-reconstruction", "operational-t2", "independent-lif"],
            distillation_value="Independent CUBA LIF raster plus T=k_t*f^2 reconstruction lets a hybrid SNN distill a bounded stay isolate without echoing the campaign stream.",
        ),
    }
