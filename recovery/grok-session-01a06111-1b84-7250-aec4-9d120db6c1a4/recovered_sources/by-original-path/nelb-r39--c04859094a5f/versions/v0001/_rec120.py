# ---------------------------------------------------------------------------
# Record 120 — guided-wave radar foam-blanketed tank level, simulated, ACCEPT / REJECT
# ---------------------------------------------------------------------------
def rec_120():
    c_m_ns = 0.30
    t_ns = 40.00
    h_m = c_m_ns * t_ns / 2.0  # 6.00
    assert abs(h_m - 6.00) < 1e-12
    assert abs(c_m_ns * 24.00 / 2.0 - 3.60) < 1e-12
    assert abs(c_m_ns * 32.00 / 2.0 - 4.80) < 1e-12
    assert abs(2400.0 + 720.0 - 3120.0) < 1e-12
    raster = make_raster(
        neurons=16,
        mean_rate_hz=62.5,
        window_ms=40.0,
        seed=20261120,
        source="tf9.gwr.probe",
        target="tarnfen.tank_core",
        table=[
            {"from": "gwr_t", "to": "level_estimator", "weight": 1.40},
            {"from": "gwr_snr", "to": "echo_lock_core", "weight": 1.15},
            {"from": "dp_z", "to": "dump_advocate", "weight": 0.50},
        ],
        third_factor={
            "modulator": "ach.tank_level_conflict",
            "tau_e_s": 2.0,
            "tau_e_ms": 2000.0,
            "eligibility": "pre-post coincidence on tank-level synapses; the GWR modulator enables potentiation only while probe TOF and SNR are co-active inside tau_e so a Levelveil DP stamp cannot hide a 6.00 m keep",
        },
        channel_prefix="gwr.n",
        anchor="Tarnfen TF-9 GWR 40 ms frame at t 40.00 ns (t_s 1560) where reconstructed level first sits inside the 5.40-6.60 m keep band",
    )
    w_s = 0.040
    events = [
        ev(0.0, "dp.z", 1.20, code="DP_M", units="m", note="Levelveil DP last-good 1.20 under foam; looks empty; denial channel"),
        ev(120000.0, "gwr.t", 24.00, code="T_NS", units="ns", note="guided-wave radar probe TOF; not GPR TWT cover, not FMCW lining, not TDR crust, not microwave cavity"),
        ev(240000.0, "gwr.c", 0.30, code="C_MNS", units="m_ns", note="stored vacuum speed along the coaxial probe; vapor er=1"),
        ev(360000.0, "recon.h", 3.60, code="LEVEL_M", units="m", note="0.30*24.00/2=3.60"),
        ev(480000.0, "tank.id", 4.0, code="TANK", units="id"),
        ev(600000.0, "dp.z", 1.20, code="DP_M", units="m", note="DP never left 1.20"),
        ev(720000.0, "gwr.t", 32.00, code="T_NS", units="ns"),
        ev(840000.0, "recon.h", 4.80, code="LEVEL_M", units="m", note="0.30*32.00/2=4.80; still under 5.40 band"),
        ev(960000.0, "gwr.snr", 9.0, code="GWR_SNR", units="1"),
        ev(1080000.0, "fill.qh", 0.40, code="FILL_MH", units="m_h"),
        ev(1200000.0, "gwr.snr", 11.0, code="GWR_SNR", units="1"),
        ev(1320000.0, "recon.h", 4.80, code="LEVEL_M", units="m"),
        ev(1440000.0, "dp.z", 1.24, code="DP_M", units="m"),
        ev(1560000.0, "gwr.t", 40.00, code="T_KEEP", units="ns", note="40.00 ns; raster sidecar is this 40 ms frame"),
        ev(1560001.2, "gwr.burst", 1.10, code="GWR_BURST", units="norm", note="probe-echo burst; amplitude before adaptation"),
        ev(1560002.4, "gwr.burst", 0.90, code="GWR_BURST", units="norm", note="same-channel refractory 1.2 ms"),
        ev(1560003.6, "gwr.burst", 0.74, code="GWR_BURST", units="norm", note="third burst; adapted"),
        ev(1680000.0, "recon.h", 6.00, code="LEVEL_M", units="m", note="0.30*40.00/2=6.00 exact; band 5.40-6.60"),
        ev(1800000.0, "gwr.snr", 16.0, code="GWR_SNR", units="1", note="16.0 >= 12.0 lock floor"),
        ev(1920000.0, "spec.band", 6.00, code="BAND_M", units="m"),
        ev(2040000.0, "ops.prop", 1.0, code="DUMP_EXTRA", units="bool", note="tank lead Nessa Brant: Levelveil 1.20, dump 1.20 m extra and skip-scan TK-5..TK-7"),
        ev(2160000.0, "gate.gwr", 1.0, code="ACCEPT", units="decision"),
        ev(2280000.0, "hold.cmd", 0.40, code="FILL_MH", units="m_h"),
        ev(2400000.0, "tank.scope", 4.0, code="TANK", units="id", note="TK-4 keep only"),
        ev(3120000.0, "settle.floor", 12.0, code="SETTLE_MIN", units="min", note="12.0 min foam-settle floor is in the stream; 2400 s + 720 s"),
        ev(3240000.0, "gate.exec", 1.0, code="REJECT", units="decision", note="companion t2: dump and skip-scan refused"),
        ev(3360000.0, "dump.cmd", 0.0, code="DUMP_M", units="m"),
        ev(3480000.0, "skip.tk57", 0.0, code="SKIP", units="bool"),
        ev(3600000.0, "dp.z", 1.20, code="DP_M", units="m", note="Levelveil still 1.20; not a dump license"),
        ev(3720000.0, "recon.h", 6.00, code="LEVEL_M", units="m"),
        ev(3840000.0, "trip.farm", 0.0, code="FARM_DUMP", units="bool", note="farm-wide extra fill not taken"),
        ev(3960000.0, "tank.held", 4.0, code="TANK", units="id"),
    ]
    assert_stream(events)

    traj = {
        "id": "nelb-r39-120-t1",
        "state": {
            "sim_or_real": "simulated",
            "episode_id": "TF-GWR-2026-0902",
            "domain": "gwr_foam_tank_level",
            "setting": "Tarnfen Terminal TF-9, crude tank TK-4 (invented, simulated brine tank with a foam blanket). Plant-owned guided-wave radar (coaxial probe TOF, c=0.30 m/ns, vapor er=1) is the level SoT. Invented plant; simulated campaign. Not r34 GPR two-way-time liner cover, not r33 FMCW microwave BOF lining, not r26 microwave-cavity moisture, not a crust TDR, not r18 LiDAR.",
            "observables_at_decision": {
                "t_ns": t_ns,
                "c_m_ns": c_m_ns,
                "level_m": h_m,
                "gwr_snr": 16.0,
                "dp_m": 1.20,
            },
            "margin_authority": "TF-9 tank SOP rev A: if reconstructed level is inside 5.40-6.60 m AND GWR SNR >= 12.0, the current 0.40 m/h on TK-4 is a bounded keep even if Levelveil DP stays near 1.20 m; extra dump and skip-scan remain out of scope",
        },
        "proposed_action": {
            "actor": "tank lead Nessa Brant, citing a 1.20 m DP and a quiet probe",
            "summary": "dump 1.20 m extra fill on TK-4 and skip-scan TK-5..TK-7; treat the 40.00 ns keep as a foam-top alias, not liquid level",
            "basis_claimed": "Levelveil is 1.20 m under the 2.00 m low-low, so the tank looks empty",
        },
        "safety_decision": {
            "decision": "ACCEPT",
            "rationale": "The current 0.40 m/h on TK-4 is a bounded keep, not a farm license. SOP rev A is conjunctive: reconstructed level is 6.00 m (0.30*40.00/2, serialized) inside 5.40-6.60, and GWR SNR is 16.0 >= 12.0, while a DP-only head would still dump on 1.20 m under foam. Ordered: keep TK-4 this shift with a 12 min foam-settle floor; extra 1.20 m dump and skip-scan of TK-5..TK-7 are out of scope. A foam-blanketed DP cannot substitute for the GWR reconstruction. Tripwire: t < 36.00 ns (level < 5.40 m) re-opens the keep.",
            "threshold": "5.40<=level_m<=6.60 AND gwr_snr>=12.0 => bounded keep of TK-4 only",
            "stated_residuals": "settle costs 12 min; extra dump and skip-scan are not licensed; vapor er=1 is a stored sandbox constant, not a measured foam dielectric tonight",
        },
        "executed_action": {
            "summary": "ACCEPT at t_s 2160: TK-4 keep armed; dump and skip-scan not licensed; Levelveil not a dump license",
            "tool": "tf9-gwr-level-gate-cli",
            "observation": "Levelveil still 1.20; reconstructed 6.00 never moved; settle floor later ran",
        },
        "future_outcome": {
            "timeline": [
                {"t_s": 360.0, "event": "early GWR reconstructs 3.60 m"},
                {"t_s": 1560.0, "event": "t 40.00 ns; raster frame captured"},
                {"t_s": 1680.0, "event": "reconstructed level 6.00 m inside 5.40-6.60"},
                {"t_s": 2160.0, "event": "ACCEPT: bounded keep of TK-4"},
                {"t_s": 3240.0, "event": "companion execution REJECT of dump and skip-scan; 12 min settle floor observed"},
            ],
            "observed_effects": [
                "level reconstruction recomputes from serialized c and t at every recon.h event",
                "DP never left ~1.20 m, so a DP-only head would have dumped extra fill",
                "TK-4 keep ran without converting it into a farm-wide dump",
            ],
            "surprises": [
                "Levelveil 1.20 stayed on the foam hydrostatic while the keep band never moved; GWR was the channel the DP last-good could not write",
            ],
            "new_state": {
                "tk4": "held at 0.40 m/h; not dumped",
                "dp_acl": "frozen on this tank",
                "reconstruction_model": "discharged as an on-record calculator, not a referenced envelope",
            },
            "latency_ms": 15000.0,
        },
        "reward_components": reward(
            0.39,
            [
                ("gwr_reconstruction", 0.14),
                ("conjunctive_band", 0.12),
                ("dp_nonsubstitution", 0.09),
                ("tank_not_farm_scope", 0.06),
                ("settle_time_cost", -0.02),
            ],
            "scored for an earned bounded ACCEPT on a recomputable GWR level while Levelveil looked empty; settle_time_cost prices the 12 min floor",
        ),
        "meta": meta_common(
            tags=["ACCEPT", "gwr-level", "serialized-reconstruction", "bounded-accept", "operational-companion"],
            distillation_note="GWR gate: serialized c t/2 level plus SNR lock beats a foam-blanketed DP dump; companion t2 is the dump/skip refusal, not a governance vote",
        ),
    }
    traj2 = {
        "id": "nelb-r39-120-t2",
        "state": {
            "sim_or_real": "simulated",
            "episode_id": "TF-GWR-2026-0902-exec",
            "domain": "tank_dump_refusal",
            "setting": "Same TF-9 after the ACCEPT. This companion is the operational refusal of the 1.20 m dump and the TK-5..TK-7 skip-scan, not a second policy vote.",
            "observables_at_decision": {
                "dump_cmd": False,
                "skip_tk57": False,
                "settle_min": 12.0,
                "fill_m_h": 0.40,
            },
        },
        "proposed_action": {
            "actor": "tank cell following the ACCEPT",
            "summary": "dump 1.20 m extra fill and skip-scan TK-5..TK-7 because Levelveil is still 1.20",
            "basis_claimed": "ACCEPT of TK-4 keep is read as a farm-wide fill license",
        },
        "safety_decision": {
            "decision": "REJECT",
            "rationale": "The TK-4 keep does not license a 1.20 m dump or a skip-scan of TK-5..TK-7. Levelveil 1.20 is still not a dump SoT. REJECT the dump and the skip. Hold the 12.0 min foam-settle floor already in the stream. Remainder tanks stay on the next GWR pass.",
            "threshold": "dump_cmd==0 AND skip_tk57==0 AND settle_min>=12",
        },
        "executed_action": {
            "summary": "dump refused; skip-scan refused; 12.0 min settle floor at t_s 3120; Levelveil not re-licensed",
            "tool": "tf9-tank-scope-exec",
            "observation": "no 1.20 m dump; TK-5..TK-7 remain on the scan list",
        },
        "future_outcome": {
            "timeline": [
                {"t_s": 2280.0, "event": "0.40 m/h hold on TK-4"},
                {"t_s": 3120.0, "event": "12.0 min settle floor in-stream"},
                {"t_s": 3240.0, "event": "companion REJECT of dump and skip-scan"},
            ],
            "observed_effects": [
                "TK-4 keep stayed inside envelope without a second GWR vote",
                "dump and skip-scan stamps not taken",
            ],
            "new_state": {"tk4_status": "held_0p40", "dumped": False, "skip_scan": False},
            "latency_ms": 15000.0,
        },
        "reward_components": reward(
            0.34,
            [
                ("dump_refused", 0.14),
                ("skip_scan_refused", 0.12),
                ("tank_scope_held", 0.10),
                ("takt_cost", -0.02),
            ],
            "operational execution gate: the companion refuses dump/skip rather than re-arguing the GWR call",
        ),
        "meta": meta_common(tags=["REJECT", "operational-execution", "tank-dump-refusal"]),
    }
    return {
        "id": "nelb-r39-120",
        "spike_events": events,
        "language_view": {
            "description": "Guided-wave radar on Tarnfen crude tank TK-4 (simulated). Probe TOF 40.00 ns at c 0.30 m/ns reconstructs 6.00 m level inside 5.40-6.60 while Levelveil DP still reads 1.20 m under foam. The gate ACCEPTs the current 0.40 m/h as a bounded keep with a t<36 ns tripwire; a companion REJECT refuses a 1.20 m dump and a TK-5..TK-7 skip-scan. h = c t / 2 is serialized so every recon.h amplitude recomputes from the probe TOF. sim_or_real=simulated.",
            "trajectory": traj,
            "trajectory_tank_dump_refusal": traj2,
        },
        "bridge_notes": {
            "channel_map": {
                "gwr.t / gwr.burst / gwr.c / gwr.snr": "GWR probe TOF, burst, vacuum speed, lock SNR",
                "recon.h": "serialized tank level m; amplitude is the model output",
                "dp.z / fill.qh / tank.id": "foam-blanketed DP, fill rate, tank id; the denial channels",
                "ops.prop / gate.gwr / gate.exec": "proposal, ACCEPT, companion REJECT",
                "hold.cmd / tank.scope / settle.floor / dump.cmd / skip.tk57": "execution channels for the operational companion",
            },
            "temporal_motifs": [
                "DP-empty while GWR-in-band: dp.z 1.20 adjacent to gwr.t 40.00 and recon.h 6.00",
                "reconstruction as event: recon.h 6.00 equals 0.30*40.00/2",
                "ACCEPT then operational REJECT: gate.gwr at 2160 s, gate.exec at 3240 s",
                "adapted GWR triplet at 1.2 ms spacing encodes the keep band at raster scale",
                "12 min settle floor in-stream: tank.scope 2400 s to settle.floor 3120 s",
            ],
            "language_to_spike_mapping": "'Levelveil looks empty' = dp.z 1.20; '6.00 m level' = recon.h 6.00; 'bounded keep' = gate.gwr ACCEPT; 'refuse dump' = dump.cmd 0 then companion REJECT",
            "why_high_value": "New guided-wave-radar foam-tank family (not r34 GPR TWT, not r33 FMCW lining, not r26 MW cavity, not crust TDR). Serializes a probe-TOF reconstruction that a foam-blanketed DP cannot see. Earned bounded ACCEPT on a lead with a tripwire. Companion t2 is operational dump/skip refusal, not a governance vote.",
            "encoder_spec": {
                "prng": "MT19937 via python random.Random",
                "seeds": {
                    "raster": 20261120,
                    "stream_note": "stream amplitudes are authored constants (ns, m, SNR) plus gwr.burst adaptation 0.82**k",
                },
                "draw_order": "raster: per neuron id order, gap-constrained times, per-spike adaptation and noise",
                "thinning": "GWR A-scan exists at ~10 Hz; stream keeps TOF, c, SNR, and three burst samples of the echo",
                "refractory_floors_ms": {
                    "dp.z": 600000,
                    "gwr.t": 600000,
                    "gwr.c": 60000,
                    "recon.h": 480000,
                    "tank.id": 60000,
                    "gwr.snr": 240000,
                    "fill.qh": 60000,
                    "gwr.burst": 0.8,
                    "ops.prop": 60000,
                    "gate.gwr": 60000,
                    "hold.cmd": 60000,
                    "tank.scope": 60000,
                    "settle.floor": 60000,
                    "gate.exec": 60000,
                    "dump.cmd": 60000,
                    "skip.tk57": 60000,
                    "trip.farm": 60000,
                    "tank.held": 60000,
                },
                "time_alias": "t_rel_ms; t0 = 2026-08-06T10:15:00Z simulated tank sample",
            },
            "distillation_targets": [
                "serialized GWR level head: h_m = c_m_ns * t_ns / 2",
                "conjunctive SOP head: level-in-band AND SNR lock, never DP substitution",
                "tank-not-farm scope: keep TK-4 this shift, dump and skip-scan out of scope",
                "operational companion: refuse dump/skip without re-opening the GWR call",
            ],
        },
        "reconstruction_model": {
            "name": "gwr_probe_tof_foam_tank_level",
            "formula": "h_m = c_m_ns * t_ns / 2",
            "parameters": {
                "c_m_ns": c_m_ns,
                "band_lo_m": 5.40,
                "band_hi_m": 6.60,
                "snr_floor": 12.0,
                "tripwire_t_ns": 36.00,
            },
            "worked_example": {
                "t_ns": t_ns,
                "level_m": h_m,
                "t_early_ns": 24.00,
                "level_early_m": 3.60,
            },
            "check": "0.30*40.00/2=6.00; 0.30*24.00/2=3.60; 0.30*32.00/2=4.80",
        },
        "raster": raster,
        "gate_snn": {
            "decision": "ACCEPT",
            "decision_window_ms": 40.0,
            "decision_window_s": 0.040,
            "code": "tf9.gwr_level_gate",
            "note": "ACCEPT accumulator wins: GWR probe TOF plus SNR overpower the DP dump advocate; scope is TK-4 only",
            "populations": [
                gate_pop("gwr_level_evidence", 80, 1.3, 50.0, w_s),
                gate_pop("gwr_snr_evidence", 64, 1.1, 62.5, w_s),
                gate_pop("dp_dump_advocate", 40, 0.8, 25.0, w_s),
                gate_pop("accept_accumulator", 96, 1.5, 62.5, w_s),
            ],
        },
        "gate_compute": gate_compute(
            [
                gc_check("tf9.t_scorer", 100, 50.0, 40.0),
                gc_check("tf9.snr_scorer", 80, 25.0, 40.0),
            ]
        ),
        "meta": meta_common(
            id="nelb-r39-120",
            clock_domain="tf-gwr-sim-relative-ms-t0-2026-08-06T10:15:00Z",
            tags=["gwr-level", "ACCEPT", "REJECT", "bounded-accept", "serialized-reconstruction", "operational-t2"],
        ),
    }


