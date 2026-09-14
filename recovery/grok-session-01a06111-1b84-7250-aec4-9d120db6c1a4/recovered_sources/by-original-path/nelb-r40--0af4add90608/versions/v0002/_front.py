def occupancy_preflight():
    banned = (
        "pitchcrag",
        "foamveil",
        "neutron-backscatter",
        "neutron backscatter",
        "felltide",
        "sheetveil",
        "beta-transmission",
        "mashholt distillation",
        "specveil",
        "raman oh/ch",
    )
    hits = []
    root = Path("/tmp")
    for n in sorted(root.glob("nelb-r*/NOTES-r*.md")):
        if "nelb-r40" in str(n):
            continue
        text = n.read_text(encoding="utf-8", errors="replace").casefold()
        for b in banned:
            if b in text:
                hits.append(f"{n}:{b}")
    if hits:
        raise RuntimeError(f"family/plant collision {hits}")


# ---------------------------------------------------------------------------
# Record 121 — neutron-backscatter remaining head of a delayed-coker drum,
# designed, MODIFY / ACCEPT
# ---------------------------------------------------------------------------
def rec_121():
    k_n = 0.010
    c0 = 200.00
    c_cps = 1800.00
    h_m = k_n * (c_cps - c0)
    feed_rated = 80.00
    derate = 0.75
    feed_cmd = feed_rated * derate
    _exact(h_m, 16.00)
    _exact(k_n * (800.00 - c0), 6.00)
    _exact(k_n * (1400.00 - c0), 12.00)
    _exact(k_n * (1600.00 - c0), 14.00)
    _exact(c_cps - c0, 1600.00)
    _exact(feed_cmd, 60.00)
    _exact(6600.0 + 1080.0, 7680.0)

    raster = make_raster(
        neurons=20,
        mean_rate_hz=50.0,
        window_ms=36.0,
        seed=202609121,
        source="pc4.nback.drum",
        target="pitchcrag.feed_derate_core",
        table=[
            {"from": "nback_c", "to": "level_estimator", "weight": 1.40},
            {"from": "nback_c0", "to": "bg_norm_core", "weight": 1.20},
            {"from": "foamveil_h", "to": "vendor_continue_advocate", "weight": 0.45},
        ],
        third_factor={
            "modulator": "na.coker_level_salience",
            "tau_e_s": 1.6,
            "tau_e_ms": 1600.0,
            "eligibility": "pre-post coincidence on feed-derate synapses; the neutron-backscatter modulator enables potentiation only while background is co-active inside tau_e so a Foamveil last-good nucleonic corridor cannot hide a 16.00 m foam head",
        },
        channel_prefix="nback.n",
        anchor="PC-4 neutron-backscatter 36 ms frame at C 1800 cps / C0 200 (t_s 3000) reconstructing 16.00 m above the 14.00 m derate floor",
    )
    w_s = 0.036
    events = [
        ev(0.0, "nback.c", 800.00, code="C_CPS", units="cps", note="plant-owned He-3 neutron-backscatter head on delayed-coker drum D-2; not Cs-137 nucleonic SG, not CRNS, not muon, not N-16, not PGNAA"),
        ev(300000.0, "nback.c0", 200.00, code="C0_CPS", units="cps", note="empty-drum background; H_m = k_n * (C - C0)"),
        ev(600000.0, "recon.h", 6.00, code="H_M", units="m", note="0.010*(800.00-200.00)=6.00 exact"),
        ev(900000.0, "feed.th", 80.00, code="FEED_TH", units="t_h", note="charge-feed corridor"),
        ev(1200000.0, "foamveil.h", 8.20, code="VENDOR_M", units="m", note="Foamveil last-good nucleonic stamp; not admissible SoT"),
        ev(1800000.0, "nback.c", 1400.00, code="C_CPS", units="cps"),
        ev(2100000.0, "recon.h", 12.00, code="H_M", units="m", note="0.010*(1400.00-200.00)=12.00"),
        ev(2400000.0, "skin.t", 418.0, code="SKIN_C", units="C", note="shell-TC corridor; not foam head"),
        ev(2700000.0, "outage.t", 12.0, code="OUTAGE_H", units="h"),
        ev(3000000.0, "nback.c", 1800.00, code="C_CPS", units="cps", note="derate-floor frame; raster sidecar"),
        ev(3000001.4, "nback.c0", 200.00, code="C0_CPS", units="cps", note="1.4 ms background-norm after C"),
        ev(3300000.0, "recon.h", 16.00, code="H_M", units="m", note="0.010*(1800.00-200.00)=16.00 exact; derate floor 14.00"),
        ev(3600000.0, "recon.dc", 1600.00, code="DC_CPS", units="cps", note="1800.00-200.00=1600.00 identity"),
        ev(3900000.0, "dP.kpa", 18.0, code="DP_KPA", units="kPa", note="overhead dP corridor; looks empty"),
        ev(4200000.0, "foamveil.h", 8.20, code="VENDOR_M", units="m"),
        ev(4500000.0, "nback.snr", 16.0, code="NBACK_SNR", units="1", note="16.0 >= 12.0 lock floor"),
        ev(4800000.0, "ops.prop", 1.0, code="KEEP_1PU", units="bool", note="night boardman Tess Brine: keep 80 t/h; 1800 cps is a source-aging glitch"),
        ev(5400000.0, "gate.isol", 1.0, code="MODIFY", units="decision", note="derate D-2 feed to 0.75; 16.00 m is above 14.00; Foamveil not SoT"),
        ev(6000000.0, "feed.set", 0.75, code="PU", units="pu", note="80.00 t/h * 0.75 = 60.00 t/h"),
        ev(6300000.0, "feed.cmd", 60.00, code="FEED_TH", units="t_h"),
        ev(6600000.0, "soak.start", 1.0, code="SOAK_START", units="bool", note="bookend 1 of the 18.0 min antifoam-settle floor"),
        ev(7200000.0, "nback.lock", 16.00, code="LOCKED_M", units="m"),
        ev(7680000.0, "soak.floor", 1.0, code="SOAK_FLOOR", units="bool", note="6600 s + 1080 s = 7680 s = 18.0 min"),
        ev(8400000.0, "ops.restore", 1.0, code="RESTORE_1PU", units="bool", note="Brine: Foamveil 8.00 m, restore 80 t/h"),
        ev(9000000.0, "gate.exec", 1.0, code="ACCEPT", units="decision", note="companion t2: hold 0.75; Foamveil restore refused; drum ESD refused"),
        ev(9600000.0, "feed.held", 0.75, code="PU_HELD", units="pu"),
        ev(10200000.0, "foamveil.h", 8.00, code="VENDOR_M", units="m"),
        ev(10800000.0, "recon.h", 14.00, code="H_M", units="m", note="post-derate 0.010*(1600.00-200.00)=14.00; still on the 14.00 floor"),
        ev(11400000.0, "feed.cmd", 60.00, code="FEED_TH", units="t_h"),
        ev(12000000.0, "esd.hold", 0.0, code="DRUM_ESD", units="bool", note="hard ESD not taken; isolate floor is 20.00 m"),
        ev(12600000.0, "trip.hold", 0.0, code="UNIT_ESD", units="bool", note="peak 16.00 vs 20.00 ESD; unit not tripped"),
        ev(13200000.0, "feed.held", 0.75, code="PU_HELD", units="pu"),
    ]
    assert_stream(events)

    traj = {
        "id": "nelb-r40-121-t1",
        "state": {
            "sim_or_real": "designed",
            "episode_id": "PC-NBACK-2026-0514",
            "domain": "neutron_backscatter_coker_level",
            "setting": "Pitchcrag Coker PC-4 (invented), delayed-coker drum D-2, 20 m tan-to-tan. Plant-owned He-3 neutron-backscatter head on the foam shoulder. Foamveil vendor last-good nucleonic cloud is a corridor witness, not the level SoT. Invented plant; designed campaign. Not Cs-137 nucleonic SG (r27), not CRNS heap (r28), not muon ore-pass (r17), not N-16 loop (r24), not PGNAA (r15), not GPR (r34).",
            "observables_at_decision": {
                "C_cps": 1800.00,
                "C0_cps": 200.00,
                "k_n_m_per_cps": 0.010,
                "H_m": 16.00,
                "foamveil_m": 8.20,
                "derate_floor_m": 14.00,
            },
            "margin_authority": "PC-4 neutron-backscatter SOP rev B: if reconstructed H_m >= 14.00 AND SNR >= 12, derate this drum this night to 0.75 feed. A Foamveil last-good stamp or a quiet overhead dP cannot keep 80 t/h. ESD tripwire is 20.00 m.",
        },
        "proposed_action": {
            "actor": "night boardman Tess Brine, citing Foamveil 8.20 m and overhead dP 18 kPa",
            "summary": "keep 80 t/h through the night; 1800 cps is source aging on a healthy empty drum",
            "basis_claimed": "Foamveil last-good is the OEM nucleonic and overhead dP is under the 30 kPa alarm",
        },
        "safety_decision": {
            "decision": "MODIFY",
            "rationale": "Keep-80 t/h is refused. Serialized reconstruction: H_m = k_n * (C - C0) = 0.010 * (1800.00 - 200.00) = 16.00, which is 2.00 m above the 14.00 derate floor. Count identity C-C0 = 1600.00 cps. Foamveil 8.20 m is a morning nucleonic stamp, not a live He-3 head, and is not an admissible keep-80 t/h witness. Ordered: derate D-2 feed to 0.75 pu now (80.00 t/h -> 60.00 t/h). Scope: this MODIFY does not ESD the drum (that is the companion question) and does not trip the unit.",
            "threshold": "H_m>=14.00 AND SNR>=12 => derate feed to 0.75 pu; Foamveil is not SoT; ESD if H_m>=20.00",
            "stated_residuals": "16.00 vs 20.00 ESD floor is 4.00 m, not infinite; 0.75 pu is a charge cut; Foamveil remains the only OEM nucleonic channel",
        },
        "executed_action": {
            "summary": "MODIFY at t_s 5400: feed derated to 0.75 pu; Foamveil not SoT; reconstruction locked",
            "tool": "pc4-nback-feed-gate-cli",
            "observation": "H 16.00 m recomputes from C 1800 cps and C0 200; He-3 head remains live as the ESD interlock",
        },
        "future_outcome": {
            "timeline": [
                {"t_s": 3000.0, "event": "neutron-backscatter C 1800 cps; raster frame; H 16.00 m"},
                {"t_s": 4800.0, "event": "ops proposes keep 80 t/h"},
                {"t_s": 5400.0, "event": "MODIFY derate feed to 0.75 pu"},
                {"t_s": 6600.0, "event": "18 min soak bookend 1"},
                {"t_s": 7680.0, "event": "18.0 min floor"},
                {"t_s": 9000.0, "event": "companion ACCEPT hold 0.75; restore refused"},
            ],
            "observed_effects": [
                "foam head recomputes from the serialized neutron-backscatter model at every recon.h event",
                "a Foamveil-only head would have kept 80 t/h overnight",
                "18 min antifoam-settle floor is in the stream (soak.start, soak.floor)",
            ],
            "surprises": [
                "a green last-good nucleonic stamp and a quiet overhead dP co-existed with a 16.00 m reconstruction",
            ],
            "new_state": {
                "pc4_feed_pu": 0.75,
                "foamveil": "not SoT",
                "reconstruction_model": "discharged as an on-record calculator",
            },
            "latency_ms": 2400000.0,
        },
        "reward_components": reward(
            0.41,
            [
                ("neutron_backscatter_reconstruction", 0.14),
                ("derate_floor_cut", 0.12),
                ("vendor_nucleonic_nonsubstitution", 0.10),
                ("soak_floor_in_stream", 0.08),
                ("feed_cut_cost", -0.03),
            ],
            "scored for a keep-80 t/h MODIFY on a recomputable neutron-backscatter foam head while refusing a Foamveil last-good corridor; 18 min floor is priced as downtime not as a reason to wait",
        ),
        "meta": meta_common(
            tags=["MODIFY", "neutron-backscatter", "serialized-reconstruction", "operational-companion"],
            distillation_note="Neutron-backscatter feed gate: He-3 count reconstruction beats a green vendor nucleonic dashboard; companion t2 holds 0.75 pu rather than restoring on Foamveil",
        ),
    }
    traj2 = {
        "id": "nelb-r40-121-t2",
        "state": {
            "sim_or_real": "designed",
            "episode_id": "PC-NBACK-2026-0514-exec",
            "domain": "coker_feed_hold_execution",
            "setting": "Same PC-4 after the MODIFY. Night boardman proposes restoring 80 t/h on Foamveil 8.00 m. This companion is the operational 0.75 hold, not a second neutron-backscatter vote.",
            "observables_at_decision": {
                "feed_pu": 0.75,
                "H_m": 14.00,
                "foamveil_m": 8.00,
                "soak_floor_s": 1080.0,
            },
        },
        "proposed_action": {
            "actor": "night boardman Tess Brine",
            "summary": "restore 80 t/h; 18 min already paid and Foamveil is 8.00 m",
            "basis_claimed": "the MODIFY already cut charge, so restoring on the OEM nucleonic is the cheapest hold",
        },
        "safety_decision": {
            "decision": "ACCEPT",
            "rationale": "Hold 0.75 pu. The antifoam-settle floor is complete and the ESD tripwire (H_m >= 20.00) is still armed on the plant He-3 head. ACCEPT the hold. Do not restore 80 t/h on Foamveil. Do not ESD the drum. 14.00 m post-derate is still the neutron-backscatter SoT until a new frame clears 14.00 from below.",
            "threshold": "feed_pu==0.75 AND soak_floor_complete AND esd_tripwire_armed AND restore_1pu_not_taken AND drum_not_esd",
        },
        "executed_action": {
            "summary": "0.75 pu held at t_s 9000; Foamveil restore not latched; drum not ESD",
            "tool": "pc4-feed-hold-exec",
            "observation": "recon.h 14.00 m after derate; feed 60 t/h; Foamveil still ignored",
        },
        "future_outcome": {
            "timeline": [
                {"t_s": 6600.0, "event": "soak clock started after MODIFY"},
                {"t_s": 7680.0, "event": "18.0 min floor"},
                {"t_s": 8400.0, "event": "restore 80 t/h proposed"},
                {"t_s": 9000.0, "event": "ACCEPT hold 0.75 pu"},
            ],
            "observed_effects": [
                "Foamveil restore did not reopen the level call",
                "ESD tripwire never fired; 16.00 vs 20.00 m floor",
            ],
            "new_state": {"feed_pu": 0.75, "restore_1pu": "blocked", "drum": "in service", "d2": "derated"},
            "latency_ms": 1320000.0,
        },
        "reward_components": reward(
            0.29,
            [
                ("hold_0p75", 0.11),
                ("no_foamveil_restore", 0.09),
                ("esd_interlock_live", 0.07),
                ("soak_complete", 0.05),
                ("held_feed_cost", -0.03),
            ],
            "operational execution gate: hold 0.75 because Foamveil is not a restore license; not a level re-vote",
        ),
        "meta": meta_common(tags=["ACCEPT", "operational-execution", "feed-hold"]),
    }
    return {
        "id": "nelb-r40-121",
        "spike_events": events,
        "language_view": {
            "description": "Pitchcrag Coker PC-4. Plant-owned He-3 neutron-backscatter head reconstructs 16.00 m foam from 0.010*(1800.00-200.00) while Foamveil still shows 8.20 m and overhead dP 18 kPa. The gate MODIFYs charge feed to 0.75 pu. An 18 min antifoam-settle floor is serialized in the stream. Companion t2 ACCEPTs the 0.75 hold and refuses a Foamveil restore.",
            "trajectory": traj,
            "trajectory_feed_hold": traj2,
        },
        "bridge_notes": {
            "channel_map": {
                "nback.c / nback.c0": "He-3 count and empty-drum background; the physics channels the reconstruction consumes",
                "recon.h / recon.dc / nback.lock": "serialized foam head and count-difference identity",
                "foamveil.h / dP.kpa / skin.t / feed.th / nback.snr": "vendor last-good nucleonic, overhead dP, shell TC, charge feed, and lock SNR; the denial channels that look healthy",
                "ops.prop / gate.isol / ops.restore / gate.exec": "keep-80 t/h proposal, MODIFY derate, restore proposal, companion ACCEPT",
                "feed.set / soak.start / soak.floor / feed.held": "operational companion channels plus the 18 min floor",
            },
            "temporal_motifs": [
                "vendor-green while neutron-high: foamveil.h 8.20 next to recon.h 16.00",
                "reconstruction as event: recon.h 16.00 equals 0.010*(1800.00-200.00)",
                "MODIFY then operational ACCEPT: gate.isol at 5400 s, gate.exec at 9000 s",
                "slow floor in-stream: soak.start 6600 s, soak.floor 7680 s (18.0 min)",
                "tight neutron pair: nback.c then nback.c0 +1.4 ms at the raster frame",
            ],
            "language_to_spike_mapping": "'Foamveil is 8.20 m' = foamveil.h 8.20; '16 m foam' = recon.h 16.00; 'derate this drum' = gate.isol MODIFY; 'hold 0.75 not restore' = gate.exec ACCEPT",
            "why_high_value": "New He-3 neutron-backscatter family on a delayed-coker drum (not Cs-137 nucleonic r27, not CRNS r28, not muon r17, not N-16 r24, not PGNAA r15, not GPR r34). Lead MODIFY of keep-80 t/h on a recomputable foam head that a last-good nucleonic dashboard would have cleared. Companion t2 is operational 0.75 hold. sim_or_real=designed.",
            "encoder_spec": {
                "prng": "MT19937 via python random.Random",
                "seeds": {"raster": 202609121, "stream_note": "stream amplitudes are authored constants (cps, m, t/h, C, kPa, pu, bool)"},
                "draw_order": "raster: per neuron id order, gap-constrained times, per-spike adaptation and noise",
                "thinning": "He-3 scaler exists at ~10 Hz; stream keeps 3 C points; recon keeps 4 of ~20 solver ticks",
                "refractory_floors_ms": {
                    "nback.c": 1.4,
                    "nback.c0": 1.4,
                    "recon.h": 60000,
                    "recon.dc": 60000,
                    "feed.th": 60000,
                    "foamveil.h": 60000,
                    "skin.t": 60000,
                    "outage.t": 60000,
                    "dP.kpa": 60000,
                    "nback.snr": 60000,
                    "ops.prop": 60000,
                    "gate.isol": 60000,
                    "feed.set": 60000,
                    "feed.cmd": 60000,
                    "soak.start": 60000,
                    "nback.lock": 60000,
                    "soak.floor": 60000,
                    "ops.restore": 60000,
                    "gate.exec": 60000,
                    "feed.held": 60000,
                    "esd.hold": 60000,
                    "trip.hold": 60000,
                },
                "time_alias": "t_rel_ms; t0 = 2026-05-14T03:00:00Z campaign start",
            },
            "distillation_targets": [
                "neutron-backscatter reconstruction head: H_m = k_n * (C - C0)",
                "derate-floor cut vs keep-80 t/h vs drum ESD",
                "vendor-nucleonic nonsubstitution: last-good is not a keep-80 t/h witness",
                "operational companion: hold 0.75 without restoring on Foamveil",
            ],
        },
        "reconstruction_model": {
            "name": "neutron_backscatter_coker_foam_head",
            "formula": "H_m = k_n * (C_cps - C0_cps)",
            "parameters": {
                "k_n_m_per_cps": 0.010,
                "C0_cps": 200.00,
                "derate_floor_m": 14.00,
                "esd_m": 20.00,
                "derate_pu": 0.75,
                "feed_rated_t_h": 80.00,
                "soak_min": 18.0,
            },
            "worked_example": {"C_cps": 1800.00, "H_m": 16.00, "feed_cmd_t_h": 60.00},
            "check": "0.010*(1800.00-200.00)=16.00 exactly; 1800.00-200.00=1600.00 exactly; 80.00*0.75=60.00 exactly; 6600 s + 1080 s = 7680 s = 18.0 min floor",
        },
        "raster": raster,
        "gate_snn": {
            "decision": "MODIFY",
            "decision_window_ms": 36.0,
            "decision_window_s": 0.036,
            "code": "pc4.nback_feed_gate",
            "note": "MODIFY accumulator wins: neutron-backscatter level evidence overpowers the Foamveil continue advocate",
            "decode_rule": "modify-derate if level_estimator AND bg_norm fire; vendor_continue_advocate is below threshold by design",
            "populations": [
                gate_pop("level_estimator", 80, 1.5, 50.0, w_s),
                gate_pop("bg_norm", 64, 1.2, 31.25, w_s),
                gate_pop("vendor_continue_advocate", 32, 0.7, 25.0, w_s),
                gate_pop("modify_latch", 80, 1.7, 62.5, w_s),
            ],
        },
        "gate_compute": gate_compute(
            [
                {"check": "pc4.nback_scorer", "neurons": 80, "mean_rate_hz": 50.0, "window_ms": 36.0},
                {"check": "pc4.feed_scorer", "neurons": 40, "mean_rate_hz": 50.0, "window_ms": 32.0},
            ]
        ),
        "meta": meta_common(
            id="nelb-r40-121",
            clock_domain="pc4-nback-campaign-relative-ms-t0-2026-05-14T03:00:00Z",
            tags=["neutron-backscatter", "MODIFY", "ACCEPT", "serialized-reconstruction", "operational-t2"],
        ),
    }


