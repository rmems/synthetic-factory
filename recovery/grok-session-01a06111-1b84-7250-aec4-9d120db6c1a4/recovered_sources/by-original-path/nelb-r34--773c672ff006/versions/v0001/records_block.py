# ---------------------------------------------------------------------------
# Record 103 — handheld XRF Cr Kα overlay remaining, designed, MODIFY / ACCEPT
# ---------------------------------------------------------------------------
def rec_103():
    k_x = 8.00
    i_cr = 6.00
    i_fe = 4.00
    cr = k_x * (i_cr / i_fe)  # 12.00
    assert abs(cr - 12.00) < 1e-12
    assert abs(k_x * (3.00 / 4.00) - 6.00) < 1e-12
    assert abs(k_x * (4.80 / 4.00) - 9.60) < 1e-12
    assert abs(k_x * (5.40 / 4.00) - 10.80) < 1e-12
    raster = make_raster(
        neurons=20,
        mean_rate_hz=50.0,
        window_ms=32.0,
        seed=20261103,
        source="sf7.xrf.crka",
        target="skeldfen.overlay_core",
        table=[
            {"from": "xrf_cr_ka", "to": "cr_estimator", "weight": 1.40},
            {"from": "xrf_snr", "to": "ratio_lock_core", "weight": 1.15},
            {"from": "pmi_cr", "to": "keep_stamp_advocate", "weight": 0.50},
        ],
        third_factor={
            "modulator": "na.cr_overlay_salience",
            "tau_e_s": 1.6,
            "tau_e_ms": 1600.0,
            "eligibility": "pre-post coincidence on overlay-XRF synapses; the Cr-Kα modulator enables potentiation only while I_Cr/I_Fe and SNR are co-active inside tau_e so a rust-scale PMI stamp cannot hide a 12.00 wt percent Cr overlay",
        },
        channel_prefix="xrf.n",
        anchor="Skeldfen SF-7 XRF 32 ms frame at I_Cr 6.00 kcps / I_Fe 4.00 kcps (t_s 1560) where reconstructed Cr first clears the 13.00 wt percent strip tripwire",
    )
    w_s = 0.032
    events = [
        ev(0.0, "pmi.cr", 18.40, code="PMI_WT", units="wt_pct", note="Alloyveil PMI last-good 18.40 on a cleaned coupon; rust-scale denial channel"),
        ev(120000.0, "xrf.icr", 3.00, code="ICR_KCPS", units="kcps", note="handheld XRF Cr Kα; not transmission DR, not LIBS plasma, not PGNAA"),
        ev(240000.0, "xrf.ife", 4.00, code="IFE_KCPS", units="kcps", note="Fe Kα internal standard"),
        ev(360000.0, "recon.cr", 6.00, code="CR_WT", units="wt_pct", note="8.00*(3.00/4.00)=6.00"),
        ev(480000.0, "drum.id", 19.0, code="DRUM", units="id"),
        ev(600000.0, "pmi.cr", 18.40, code="PMI_WT", units="wt_pct", note="PMI never left the 18 wt percent corridor"),
        ev(720000.0, "xrf.icr", 4.80, code="ICR_KCPS", units="kcps"),
        ev(840000.0, "recon.cr", 9.60, code="CR_WT", units="wt_pct", note="8.00*(4.80/4.00)=9.60"),
        ev(960000.0, "xrf.snr", 12.0, code="XRF_SNR", units="1"),
        ev(1080000.0, "oes.cr", 18.10, code="OES_WT", units="wt_pct", note="spark-OES on the rust scale; XRF Kα is not an OES spark"),
        ev(1200000.0, "xrf.icr", 5.40, code="ICR_KCPS", units="kcps"),
        ev(1320000.0, "recon.cr", 10.80, code="CR_WT", units="wt_pct", note="8.00*(5.40/4.00)=10.80; still under 13.00 strip"),
        ev(1440000.0, "pmi.cr", 18.20, code="PMI_WT", units="wt_pct"),
        ev(1560000.0, "xrf.icr", 6.00, code="ICR_TRIP", units="kcps", note="6.00 kcps; raster sidecar is this 32 ms frame"),
        ev(1560001.2, "xrf.burst", 1.10, code="XRF_BURST", units="norm", note="Kα lock burst; amplitude before adaptation"),
        ev(1560002.4, "xrf.burst", 0.90, code="XRF_BURST", units="norm", note="same-channel refractory 1.2 ms; adapted 0.82x plus noise"),
        ev(1560003.6, "xrf.burst", 0.74, code="XRF_BURST", units="norm", note="third burst; adapted"),
        ev(1680000.0, "xrf.ife", 4.00, code="IFE_KCPS", units="kcps", note="Fe Kα still 4.00; ratio 1.50"),
        ev(1800000.0, "recon.cr", 12.00, code="CR_WT", units="wt_pct", note="8.00*(6.00/4.00)=12.00 exact; strip 13.00, shop-condemn 8.00"),
        ev(1920000.0, "xrf.snr", 18.0, code="XRF_SNR", units="1", note="18.0 >= 14.0 lock floor"),
        ev(2040000.0, "ops.prop", 1.0, code="KEEP_STAMP", units="bool", note="night cladding lead Merrin Voss: PMI 18.40, keep D-19 in service"),
        ev(2160000.0, "gate.xrf", 1.0, code="MODIFY", units="decision"),
        ev(2280000.0, "iso.cmd", 1.0, code="DRUM_D19", units="bool"),
        ev(2400000.0, "grind.cmd", 1.0, code="G4_MAP", units="bool"),
        ev(3720000.0, "cool.floor", 24.0, code="COOL_MIN", units="min", note="24.0 min cool floor is in the stream; 2280 s + 1440 s"),
        ev(3840000.0, "grind.T", 42.0, code="C", units="C"),
        ev(3960000.0, "gate.exec", 1.0, code="ACCEPT", units="decision", note="companion t2: D-19 isolate plus G-4 grind executed"),
        ev(4080000.0, "pmi.cr", 18.40, code="PMI_WT", units="wt_pct", note="PMI still 18.40; not a keep-stamp license"),
        ev(4200000.0, "recon.cr", 12.00, code="CR_WT", units="wt_pct"),
        ev(4320000.0, "sib.hold", 1.0, code="D17_20", units="bool", note="D-17/18/20 remain in service"),
        ev(4440000.0, "trip.shop", 0.0, code="SHOP_CONDEMN", units="bool", note="peak 12.00 vs 8.00 shop-condemn; shop-wide not taken"),
    ]
    assert_stream(events)

    traj = {
        "id": "nelb-r34-103-t1",
        "state": {
            "sim_or_real": "designed",
            "episode_id": "SF-XRF-2026-0902",
            "domain": "xrf_crka_overlay",
            "setting": "Skeldfen Overlay Works SF-7, restoration drum D-19 (invented). Plant-owned handheld XRF (Cr Kα / Fe Kα internal standard, 40 kV Rh tube) is the remaining-Cr SoT. Invented plant; designed campaign. Not industrial transmission DR (r17 Quernholt), not LIBS plasma ratios (r19/r21/r22), not PGNAA capture gammas (r15 Rookmere), not spectroscopic ellipsometry (r30 Lichenholt).",
            "observables_at_decision": {
                "I_Cr_kcps": i_cr,
                "I_Fe_kcps": i_fe,
                "k_x": k_x,
                "Cr_wt_pct": cr,
                "xrf_snr": 18.0,
                "pmi_wt_pct": 18.40,
            },
            "margin_authority": "SF-7 overlay SOP rev D: if reconstructed Cr wt percent <= 13.00 AND XRF SNR >= 14.0, keep-stamp of D-19 is forbidden even if Alloyveil PMI stays inside 17.0-19.0 wt percent",
        },
        "proposed_action": {
            "actor": "night cladding lead Merrin Voss, citing an 18.40 wt percent PMI and a quiet grind cell",
            "summary": "keep D-19 in service and skip the G-4 grind map; treat the 6.00 kcps Cr Kα walk as a window-film drift, not overlay depletion",
            "basis_claimed": "PMI is 18.40 wt percent and spark-OES on the rust scale is 18.10, both inside housekeeping limits",
        },
        "safety_decision": {
            "decision": "MODIFY",
            "rationale": "The in-service stamp on D-19 is refused, not the shop. SOP rev D is conjunctive: reconstructed Cr is 12.00 wt percent (8.00*(6.00/4.00), serialized) against a 13.00 strip and an 8.00 shop-condemn, and XRF SNR is 18.0 >= 14.0, while a PMI-only head would still see 18.40 on a rust-scale coupon (OES 18.10 in-stream). Ordered: isolate D-19 only, hold a 24 min cool, grind-map G-4; keep D-17/18/20 in service. A cleaned-coupon PMI cannot substitute for the XRF reconstruction.",
            "threshold": "Cr_wt_pct<=13.00 AND xrf_snr>=14.0 => forbid keep-stamp",
            "stated_residuals": "cool costs 24 min; shop-wide condemn is not taken (12.00 vs 8.00); matrix-effect compensation of k_x is not a keep-stamp condition tonight",
        },
        "executed_action": {
            "summary": "MODIFY at t_s 2160: D-19 isolated; G-4 grind armed; PMI not a keep-stamp license",
            "tool": "sf7-xrf-cr-gate-cli",
            "observation": "PMI still 18.40 wt percent; reconstructed 12.00 never moved; G-4 later ran after the 24 min cool",
        },
        "future_outcome": {
            "timeline": [
                {"t_s": 360.0, "event": "early XRF reconstructs 6.00 wt percent Cr"},
                {"t_s": 1560.0, "event": "I_Cr 6.00 kcps; raster frame captured"},
                {"t_s": 1800.0, "event": "reconstructed Cr 12.00 wt percent vs 13.00 strip"},
                {"t_s": 2160.0, "event": "MODIFY: isolate D-19 plus G-4 grind"},
                {"t_s": 3960.0, "event": "companion execution ACCEPT; 24 min cool floor observed"},
            ],
            "observed_effects": [
                "Cr reconstruction recomputes from serialized k_x, I_Cr, and I_Fe at every recon.cr event",
                "PMI never left ~18.4 wt percent, so a PMI-only head would have kept the stamp",
                "G-4 grind ran the isolate without converting it into a shop-wide condemn",
            ],
            "surprises": [
                "spark-OES 18.10 stayed on the rust scale while the PMI corridor never moved; XRF Cr Kα was the channel the rust film could not write",
            ],
            "new_state": {
                "d19": "isolated on G-4 grind; not stamped in-service",
                "pmi_acl": "frozen on this drum",
                "reconstruction_model": "discharged as an on-record calculator, not a referenced envelope",
            },
            "latency_ms": 15000.0,
        },
        "reward_components": reward(
            0.41,
            [
                ("xrf_reconstruction", 0.14),
                ("conjunctive_strip", 0.12),
                ("pmi_nonsubstitution", 0.09),
                ("drum_not_shop_scope", 0.08),
                ("cool_time_cost", -0.02),
            ],
            "scored for refusing a keep-stamp on a recomputable XRF Cr while the PMI looked healthy; cool_time_cost prices the 24 min floor",
        ),
        "meta": meta_common(
            tags=["MODIFY", "xrf-crka", "serialized-reconstruction", "operational-companion"],
            distillation_note="XRF gate: serialized I_Cr/I_Fe Cr plus SNR lock beats a rust-scale PMI; companion t2 is the isolate/grind execution, not a governance vote",
        ),
    }
    traj2 = {
        "id": "nelb-r34-103-t2",
        "state": {
            "sim_or_real": "designed",
            "episode_id": "SF-XRF-2026-0902-exec",
            "domain": "overlay_grind_execution",
            "setting": "Same SF-7 after the MODIFY. This companion is the operational D-19 isolate, 24 min cool, and G-4 grind map, not a second policy vote.",
            "observables_at_decision": {
                "iso_cmd": True,
                "grind_cmd": True,
                "cool_min": 24.0,
                "siblings_held": True,
            },
        },
        "proposed_action": {
            "actor": "cladding cell following the MODIFY",
            "summary": "execute isolate of D-19 only, hold 24 min cool, grind-map G-4; keep D-17/18/20",
            "basis_claimed": "MODIFY requirements are fully specified; grind cell is in-envelope",
        },
        "safety_decision": {
            "decision": "ACCEPT",
            "rationale": "The execution envelope is intact: D-19 is the only isolated drum, the 24.0 min cool floor is in the stream, G-4 is the only grind map, and shop-wide condemn was not taken (12.00 vs 8.00). ACCEPT the sequence. Do not re-stamp on the PMI; do not convert the isolate into a shop condemn.",
            "threshold": "cool_min>=24 AND shop_condemn==0 AND siblings_held==1",
        },
        "executed_action": {
            "summary": "D-19 isolated t_s 2280; 24.0 min floor at t_s 3720; G-4 mapped; siblings remain; PMI not re-licensed",
            "tool": "sf7-grind-exec",
            "observation": "no shop-wide condemn; keep-stamp not re-entered on D-19",
        },
        "future_outcome": {
            "timeline": [
                {"t_s": 2280.0, "event": "D-19 isolate armed"},
                {"t_s": 2400.0, "event": "G-4 grind armed"},
                {"t_s": 3720.0, "event": "24.0 min cool floor in-stream"},
                {"t_s": 3960.0, "event": "companion ACCEPT"},
            ],
            "observed_effects": [
                "G-4 grind confirmed the isolate without a second XRF vote",
                "D-17/18/20 stayed in service; D-19 stamp not restored",
            ],
            "new_state": {"d19_status": "isolated_on_grind", "shop_condemned": False},
            "latency_ms": 15000.0,
        },
        "reward_components": reward(
            0.34,
            [
                ("envelope_respect", 0.12),
                ("cool_floor_in_stream", 0.10),
                ("drum_scope_held", 0.08),
                ("pmi_not_relicensed", 0.06),
                ("grind_time_cost", -0.02),
            ],
            "operational execution gate: the companion does the isolate/grind rather than re-arguing the XRF call",
        ),
        "meta": meta_common(tags=["ACCEPT", "operational-execution", "overlay-grind"]),
    }
    return {
        "id": "nelb-r34-103",
        "spike_events": events,
        "language_view": {
            "description": "Handheld XRF on Skeldfen overlay drum D-19. Cr Kα 6.00 kcps over Fe Kα 4.00 kcps reconstructs 12.00 wt percent Cr against a 13.00 strip while Alloyveil PMI still reads 18.40. The gate MODIFYs to a D-19 isolate plus G-4 grind; a companion execution ACCEPT runs the 24 min cool floor. Cr = k_x * (I_Cr/I_Fe) is serialized so every recon.cr amplitude recomputes from the Kα pair.",
            "trajectory": traj,
            "trajectory_overlay_grind_execution": traj2,
        },
        "bridge_notes": {
            "channel_map": {
                "xrf.icr / xrf.ife / xrf.burst / xrf.snr": "XRF Cr Kα, Fe Kα, burst, lock SNR",
                "recon.cr": "serialized remaining-Cr wt percent; amplitude is the model output",
                "pmi.cr / oes.cr / drum.id": "PMI, rust-scale OES, drum id; the denial channels that stay healthy",
                "ops.prop / gate.xrf / gate.exec": "proposal, MODIFY, companion ACCEPT",
                "iso.cmd / grind.cmd / cool.floor / grind.T / sib.hold": "execution channels for the operational companion",
                "trip.shop": "shop-wide condemn not taken",
            },
            "temporal_motifs": [
                "PMI-healthy while XRF-sick: pmi.cr 18.40 adjacent to xrf.icr 6.00 and recon.cr 12.00",
                "reconstruction as event: recon.cr 12.00 equals 8.00*(6.00/4.00)",
                "MODIFY then operational ACCEPT: gate.xrf at 2160 s, gate.exec at 3960 s",
                "adapted XRF triplet at 1.2 ms spacing encodes the strip trip at raster scale",
                "24 min cool floor in-stream: iso.cmd 2280 s to cool.floor 3720 s",
            ],
            "language_to_spike_mapping": "'PMI looks healthy' = pmi.cr 18.40; '12 wt percent Cr' = recon.cr 12.00; 'forbid keep-stamp' = gate.xrf MODIFY; 'execute the isolate' = iso.cmd then companion ACCEPT",
            "why_high_value": "New handheld-XRF Cr-Kα overlay family (not r17 industrial DR, not r19/r21/r22 LIBS plasma, not r15 PGNAA oxides, not r30 spectroscopic ellipsometry). Serializes a Kα-ratio reconstruction that a PMI-only head cannot see. Companion t2 is operational isolate/grind execution, not a governance vote.",
            "encoder_spec": {
                "prng": "MT19937 via python random.Random",
                "seeds": {
                    "raster": 20261103,
                    "stream_note": "stream amplitudes are authored constants (kcps, wt percent, C) plus xrf.burst adaptation 0.82**k",
                },
                "draw_order": "raster: per neuron id order, gap-constrained times, per-spike adaptation and noise",
                "thinning": "XRF 40 kV spectrum exists at ~1 Hz; stream keeps I_Cr, I_Fe, SNR, and three burst samples of ~256 channels",
                "refractory_floors_ms": {
                    "pmi.cr": 600000,
                    "xrf.icr": 360000,
                    "xrf.ife": 1440000,
                    "recon.cr": 480000,
                    "drum.id": 60000,
                    "xrf.snr": 960000,
                    "oes.cr": 60000,
                    "xrf.burst": 0.8,
                    "ops.prop": 60000,
                    "gate.xrf": 60000,
                    "iso.cmd": 60000,
                    "grind.cmd": 60000,
                    "cool.floor": 60000,
                    "grind.T": 60000,
                    "gate.exec": 60000,
                    "sib.hold": 60000,
                    "trip.shop": 60000,
                },
                "time_alias": "t_rel_ms; t0 = 2026-08-11T02:40:00Z overlay sample",
            },
            "distillation_targets": [
                "serialized XRF Cr head: Cr_wt_pct = k_x * (I_Cr_kcps / I_Fe_kcps)",
                "conjunctive SOP head: Cr AND SNR lock, never PMI substitution",
                "drum-not-shop scope: isolate one drum, do not condemn the shop",
                "operational companion: execute grind without re-opening the XRF call",
            ],
        },
        "reconstruction_model": {
            "name": "xrf_crka_internal_standard_overlay",
            "formula": "Cr_wt_pct = k_x * (I_Cr_kcps / I_Fe_kcps)",
            "parameters": {
                "k_x": k_x,
                "strip_wt_pct": 13.00,
                "shop_condemn_wt_pct": 8.00,
                "snr_floor": 14.0,
            },
            "worked_example": {
                "I_Cr_kcps": i_cr,
                "I_Fe_kcps": i_fe,
                "Cr_wt_pct": cr,
                "I_Cr_early_kcps": 3.00,
                "Cr_early_wt_pct": 6.00,
            },
            "check": "8.00*(6.00/4.00)=12.00; 8.00*(3.00/4.00)=6.00; 8.00*(4.80/4.00)=9.60",
        },
        "raster": raster,
        "gate_snn": {
            "decision": "MODIFY",
            "decision_window_ms": 32.0,
            "decision_window_s": 0.032,
            "code": "sf7.xrf_cr_gate",
            "note": "MODIFY accumulator wins: XRF Cr-Kα plus SNR overpower the PMI keep-stamp advocate",
            "populations": [
                gate_pop("xrf_cr_evidence", 80, 1.4, 50.0, w_s),
                gate_pop("xrf_snr_evidence", 64, 1.1, 31.25, w_s),
                gate_pop("pmi_keep_advocate", 40, 0.9, 50.0, w_s),
                gate_pop("modify_accumulator", 96, 1.6, 62.5, w_s),
            ],
        },
        "gate_compute": gate_compute(
            [
                gc_check("sf7.icr_scorer", 128, 31.25, 32.0),
                gc_check("sf7.snr_scorer", 80, 25.0, 32.0),
            ]
        ),
        "meta": meta_common(
            id="nelb-r34-103",
            clock_domain="sf-xrf-campaign-relative-ms-t0-2026-08-11T02:40:00Z",
            tags=["xrf-crka", "MODIFY", "ACCEPT", "serialized-reconstruction", "operational-t2"],
        ),
    }


# ---------------------------------------------------------------------------
# Record 104 — Coriolis tube-twist mass flow, hil, REJECT / MODIFY
# ---------------------------------------------------------------------------
def rec_104():
    k_dt = 2.00
    dt_ms = 8.00
    mdot = k_dt * dt_ms  # 16.00
    assert abs(mdot - 16.00) < 1e-12
    assert abs(k_dt * 4.00 - 8.00) < 1e-12
    assert abs(k_dt * 6.00 - 12.00) < 1e-12
    assert abs(k_dt * 7.00 - 14.00) < 1e-12
    raster = make_raster(
        neurons=16,
        mean_rate_hz=62.5,
        window_ms=40.0,
        seed=20261104,
        source="mh3.coriolis.twist",
        target="mirecoil.charge_core",
        table=[
            {"from": "cori_dt", "to": "mdot_estimator", "weight": 1.45},
            {"from": "drive_gain", "to": "coating_advocate", "weight": 1.20},
            {"from": "orifice_mdot", "to": "keep100_advocate", "weight": 0.45},
        ],
        third_factor={
            "modulator": "da.charge_flood_error",
            "tau_e_s": 1.2,
            "tau_e_ms": 1200.0,
            "eligibility": "pre-post coincidence on Coriolis synapses; the twist modulator enables potentiation only while drive-gain is co-active inside tau_e so a frozen orifice last-good cannot hide a 16.00 kg/s charge flood",
        },
        channel_prefix="cori.n",
        anchor="Mirecoil MH-3 Coriolis 40 ms frame at dt 8.00 ms (t_s 1560) where reconstructed mdot first clears the 14.00 kg/s flood tripwire",
    )
    w_s = 0.040
    events = [
        ev(0.0, "orif.mdot", 9.40, code="ORIF_KGS", units="kg_s", note="Flowveil orifice last-good frozen after a DP freeze; denial channel"),
        ev(120000.0, "cori.dt", 4.00, code="DT_MS", units="ms", note="Coriolis tube-twist Δt; not clamp-on transit-time, not LFV, not N-16, not VW viscosity"),
        ev(240000.0, "cori.f", 120.00, code="F_HZ", units="Hz", note="tube frequency; density conjunct, not the mdot head"),
        ev(360000.0, "recon.mdot", 8.00, code="MDOT_KGS", units="kg_s", note="2.00*4.00=8.00"),
        ev(480000.0, "charge.T", 488.0, code="T_K", units="K"),
        ev(600000.0, "orif.mdot", 9.40, code="ORIF_KGS", units="kg_s", note="orifice never left 9.40"),
        ev(720000.0, "cori.dt", 6.00, code="DT_MS", units="ms"),
        ev(840000.0, "recon.mdot", 12.00, code="MDOT_KGS", units="kg_s", note="2.00*6.00=12.00"),
        ev(960000.0, "cori.gain", 1.20, code="DRIVE_GAIN", units="1"),
        ev(1080000.0, "hil.mdot", 8.00, code="HIL_KGS", units="kg_s", note="Cori-HIL-4 water loop still 8.00 at dt 4.00; live C-2 light is on"),
        ev(1200000.0, "cori.dt", 7.00, code="DT_MS", units="ms"),
        ev(1320000.0, "recon.mdot", 14.00, code="MDOT_KGS", units="kg_s", note="2.00*7.00=14.00; flood floor"),
        ev(1440000.0, "orif.mdot", 9.40, code="ORIF_KGS", units="kg_s", note="orifice still frozen 9.40"),
        ev(1560000.0, "cori.dt", 8.00, code="DT_TRIP", units="ms", note="8.00 ms; raster sidecar is this 40 ms frame"),
        ev(1560001.2, "cori.ring", 1.10, code="CORI_BURST", units="norm", note="tube ring-down; amplitude before adaptation"),
        ev(1560002.4, "cori.ring", 0.90, code="CORI_BURST", units="norm", note="same-channel refractory 1.2 ms"),
        ev(1560003.6, "cori.ring", 0.74, code="CORI_BURST", units="norm", note="third ring; adapted"),
        ev(1680000.0, "recon.mdot", 16.00, code="MDOT_KGS", units="kg_s", note="2.00*8.00=16.00 exact; design 8.00, flood 14.00"),
        ev(1800000.0, "cori.gain", 1.60, code="DRIVE_GAIN", units="1", note="1.60 >= 1.40 coating-gain floor"),
        ev(1920000.0, "spec.cap", 14.00, code="CAP_KGS", units="kg_s"),
        ev(2040000.0, "ops.prop", 1.0, code="KEEP_100", units="bool", note="night board Cald Wether: orifice 9.40, keep 1.00 pu charge"),
        ev(2160000.0, "gate.cori", 1.0, code="REJECT", units="decision"),
        ev(2280000.0, "fv.cmd", 8.00, code="FV12_KGS", units="kg_s", note="cut FV-12 to design 8.00; not trip-to-zero"),
        ev(2400000.0, "soak.cmd", 1.0, code="T4_SOLVENT", units="bool"),
        ev(3360000.0, "soak.floor", 18.0, code="SOAK_MIN", units="min", note="18.0 min solvent soak floor is in the stream; 2280 s + 1080 s"),
        ev(3480000.0, "charge.T", 488.0, code="T_K", units="K"),
        ev(3600000.0, "gate.exec", 1.0, code="MODIFY", units="decision", note="companion t2: recycle-not-kill; FV-12 8.00 plus T-4 soak"),
        ev(3720000.0, "orif.mdot", 9.40, code="ORIF_KGS", units="kg_s", note="orifice still frozen; not a keep-100 license"),
        ev(3840000.0, "recon.mdot", 16.00, code="MDOT_KGS", units="kg_s"),
        ev(3960000.0, "trip.zero", 0.0, code="TRIP_ZERO", units="bool", note="freeze-kill refused"),
        ev(4080000.0, "fv.now", 8.00, code="FV12_KGS", units="kg_s"),
    ]
    assert_stream(events)

    traj = {
        "id": "nelb-r34-104-t1",
        "state": {
            "sim_or_real": "hil",
            "episode_id": "MH-CORI-2026-0902",
            "domain": "coriolis_charge_mdot",
            "setting": "Mirecoil Hydrotreater MH-3, charge header C-2 (invented). Plant-owned Coriolis (twin-tube twist, k_dt=2.00 kg/s/ms) is the mass-flow SoT. Hardware-in-the-loop: Cori-HIL-4 water loop views the same transmitter firmware while live C-2 light is on. Invented plant. Not ultrasonic clamp-on custody (r18 Kelpwick), not LFV aluminum (r19 Marlfen), not N-16 gamma transit-time (r24 Gullwick), not vibrating-wire viscosity (r26 Pitchfen).",
            "observables_at_decision": {
                "dt_ms": dt_ms,
                "k_dt": k_dt,
                "mdot_kg_s": mdot,
                "drive_gain": 1.60,
                "orifice_kg_s": 9.40,
                "hil_kg_s": 8.00,
            },
            "margin_authority": "MH-3 charge SOP rev C: if reconstructed mdot >= 14.00 kg/s AND drive-gain >= 1.40, keep-100 is forbidden even if Flowveil orifice stays under 10.00 kg/s",
        },
        "proposed_action": {
            "actor": "night board operator Cald Wether, citing a 9.40 kg/s orifice and a quiet FV-12",
            "summary": "keep 1.00 pu charge on C-2; treat the 8.00 ms twist as a coating artifact, not a flood",
            "basis_claimed": "orifice is 9.40 kg/s and HIL water loop is still 8.00, both inside housekeeping limits",
        },
        "safety_decision": {
            "decision": "REJECT",
            "rationale": "Keep-100 on C-2 is refused. SOP rev C is conjunctive: reconstructed mdot is 16.00 kg/s (2.00*8.00, serialized) against a 14.00 flood floor and an 8.00 design, and drive-gain is 1.60 >= 1.40, while an orifice-only head would still see a frozen 9.40 kg/s last-good. Ordered: do not keep 1.00 pu and do not trip-to-zero. The HIL water loop at 8.00 proves k_dt; it is not a license to ignore live C-2. A frozen orifice cannot substitute for the Coriolis reconstruction.",
            "threshold": "mdot_kg_s>=14.00 AND drive_gain>=1.40 => forbid keep-100",
            "stated_residuals": "soak costs 18 min; trip-to-zero is not taken; tube-density from f is a conjunct not a second mdot head tonight",
        },
        "executed_action": {
            "summary": "REJECT at t_s 2160: keep-100 refused; trip-to-zero not taken; FV-12 cut handed to the companion",
            "tool": "mh3-cori-mdot-gate-cli",
            "observation": "orifice still 9.40; reconstructed 16.00 never moved; HIL water stayed 8.00",
        },
        "future_outcome": {
            "timeline": [
                {"t_s": 360.0, "event": "early Coriolis reconstructs 8.00 kg/s"},
                {"t_s": 1560.0, "event": "dt 8.00 ms; raster frame captured"},
                {"t_s": 1680.0, "event": "reconstructed mdot 16.00 kg/s vs 14.00 flood"},
                {"t_s": 2160.0, "event": "REJECT: keep-100 refused"},
                {"t_s": 3600.0, "event": "companion MODIFY; 18 min soak floor observed"},
            ],
            "observed_effects": [
                "mdot reconstruction recomputes from serialized k_dt and dt at every recon.mdot event",
                "orifice never left 9.40, so an orifice-only head would have kept 1.00 pu",
                "HIL water 8.00 convicted k_dt without converting REJECT into a live close-out",
            ],
            "surprises": [
                "drive-gain 1.60 walked with the twist while the orifice freeze never moved; Coriolis Δt was the channel the DP last-good could not write",
            ],
            "new_state": {
                "c2": "keep-100 refused; not tripped to zero",
                "orifice_acl": "frozen on this header",
                "reconstruction_model": "discharged as an on-record calculator, not a referenced envelope",
            },
            "latency_ms": 15000.0,
        },
        "reward_components": reward(
            0.43,
            [
                ("cori_reconstruction", 0.15),
                ("conjunctive_flood", 0.12),
                ("orifice_nonsubstitution", 0.10),
                ("recycle_not_kill", 0.08),
                ("soak_time_cost", -0.02),
            ],
            "scored for refusing keep-100 on a recomputable Coriolis mdot while the orifice looked quiet; soak_time_cost prices the 18 min floor",
        ),
        "meta": meta_common(
            tags=["REJECT", "coriolis-mdot", "serialized-reconstruction", "operational-companion"],
            distillation_note="Coriolis gate: serialized k_dt*dt plus drive-gain beats a frozen orifice; companion t2 is the FV-12/soak execution, not a governance vote",
        ),
    }
    traj2 = {
        "id": "nelb-r34-104-t2",
        "state": {
            "sim_or_real": "hil",
            "episode_id": "MH-CORI-2026-0902-exec",
            "domain": "charge_soak_execution",
            "setting": "Same MH-3 after the REJECT. This companion is the operational FV-12 cut to 8.00 kg/s and 18 min T-4 solvent soak, not a second policy vote and not a trip-to-zero.",
            "observables_at_decision": {
                "fv12_kg_s": 8.00,
                "soak_cmd": True,
                "soak_min": 18.0,
                "trip_zero": False,
            },
        },
        "proposed_action": {
            "actor": "board following the REJECT",
            "summary": "cut FV-12 to 8.00 kg/s, hold 18 min T-4 soak, refuse trip-to-zero",
            "basis_claimed": "REJECT forbids keep-100; recycle-not-kill is the specified leftover",
        },
        "safety_decision": {
            "decision": "MODIFY",
            "rationale": "Keep-100 is already refused. Freeze-kill (trip-to-zero) is also refused. Ordered: FV-12 to 8.00 kg/s, 18.0 min T-4 solvent soak in-stream, HIL water loop not used as a live close. MODIFY the REJECT into a soak rather than a unit trip.",
            "threshold": "fv12_kg_s==8.00 AND soak_min>=18 AND trip_zero==0",
        },
        "executed_action": {
            "summary": "FV-12 8.00 at t_s 2280; 18.0 min soak floor at t_s 3360; trip-to-zero not taken; orifice not re-licensed",
            "tool": "mh3-fv12-soak-exec",
            "observation": "no unit trip; keep-100 not re-entered on C-2",
        },
        "future_outcome": {
            "timeline": [
                {"t_s": 2280.0, "event": "FV-12 cut to 8.00 kg/s"},
                {"t_s": 2400.0, "event": "T-4 soak armed"},
                {"t_s": 3360.0, "event": "18.0 min soak floor in-stream"},
                {"t_s": 3600.0, "event": "companion MODIFY"},
            ],
            "observed_effects": [
                "8.00 kg/s FV-12 confirmed the recycle without a second Coriolis vote",
                "C-2 remainder stayed; trip-to-zero stamp not taken",
            ],
            "new_state": {"c2_status": "soaking_at_8", "tripped_zero": False},
            "latency_ms": 15000.0,
        },
        "reward_components": reward(
            0.32,
            [
                ("soak_execution", 0.12),
                ("trip_to_zero_refused", 0.10),
                ("fv_cut_design", 0.08),
                ("hil_not_live_close", 0.04),
                ("solvent_time_cost", -0.02),
            ],
            "operational execution gate: the companion soaks rather than converting REJECT into a freeze-kill",
        ),
        "meta": meta_common(tags=["MODIFY", "operational-execution", "charge-soak"]),
    }
    return {
        "id": "nelb-r34-104",
        "spike_events": events,
        "language_view": {
            "description": "Coriolis on Mirecoil MH-3 charge C-2. Tube-twist 8.00 ms reconstructs 16.00 kg/s against a 14.00 flood floor while Flowveil orifice still reads 9.40. The gate REJECTS keep-100; a companion execution MODIFY cuts FV-12 to 8.00 kg/s and runs an 18 min T-4 soak rather than a trip-to-zero. mdot = k_dt * dt is serialized so every recon.mdot amplitude recomputes from the twist. sim_or_real=hil.",
            "trajectory": traj,
            "trajectory_charge_soak_execution": traj2,
        },
        "bridge_notes": {
            "channel_map": {
                "cori.dt / cori.ring / cori.f / cori.gain": "Coriolis twist, burst, tube frequency, drive-gain",
                "recon.mdot": "serialized mass-flow kg/s; amplitude is the model output",
                "orif.mdot / hil.mdot / charge.T": "frozen orifice, HIL water loop, charge T; the denial and HIL channels",
                "ops.prop / gate.cori / gate.exec": "proposal, REJECT, companion MODIFY",
                "fv.cmd / soak.cmd / soak.floor / fv.now": "execution channels for the operational companion",
                "trip.zero": "freeze-kill not taken",
            },
            "temporal_motifs": [
                "orifice-quiet while Coriolis-sick: orif.mdot 9.40 adjacent to cori.dt 8.00 and recon.mdot 16.00",
                "reconstruction as event: recon.mdot 16.00 equals 2.00*8.00",
                "REJECT then operational MODIFY: gate.cori at 2160 s, gate.exec at 3600 s",
                "adapted Coriolis triplet at 1.2 ms spacing encodes the flood trip at raster scale",
                "18 min soak floor in-stream: fv.cmd 2280 s to soak.floor 3360 s",
            ],
            "language_to_spike_mapping": "'orifice looks quiet' = orif.mdot 9.40; '16 kg/s flood' = recon.mdot 16.00; 'forbid keep-100' = gate.cori REJECT; 'soak not kill' = fv.cmd then companion MODIFY",
            "why_high_value": "New Coriolis tube-twist mass-flow family (not r18 clamp-on transit-time, not r19 LFV, not r24 N-16 gamma TOF, not r26 vibrating-wire viscosity). Serializes a Δt-to-mdot reconstruction that a frozen orifice cannot see. Companion t2 is operational soak execution, not a governance vote.",
            "encoder_spec": {
                "prng": "MT19937 via python random.Random",
                "seeds": {
                    "raster": 20261104,
                    "stream_note": "stream amplitudes are authored constants (ms, kg/s, gain) plus cori.ring adaptation 0.82**k",
                },
                "draw_order": "raster: per neuron id order, gap-constrained times, per-spike adaptation and noise",
                "thinning": "Coriolis 100 Hz twist carrier kept as envelope Δt; stream keeps dt, gain, and three ring samples of ~400 waveform bins",
                "refractory_floors_ms": {
                    "orif.mdot": 600000,
                    "cori.dt": 360000,
                    "cori.f": 60000,
                    "recon.mdot": 480000,
                    "charge.T": 3000000,
                    "cori.gain": 840000,
                    "hil.mdot": 60000,
                    "cori.ring": 0.8,
                    "ops.prop": 60000,
                    "gate.cori": 60000,
                    "fv.cmd": 60000,
                    "soak.cmd": 60000,
                    "soak.floor": 60000,
                    "gate.exec": 60000,
                    "trip.zero": 60000,
                    "fv.now": 60000,
                    "spec.cap": 60000,
                },
                "time_alias": "t_rel_ms; t0 = 2026-08-19T21:15:00Z charge sample",
            },
            "distillation_targets": [
                "serialized Coriolis mdot head: mdot_kg_s = k_dt * dt_ms",
                "conjunctive SOP head: mdot AND drive-gain, never orifice substitution",
                "recycle-not-kill: refuse keep-100 without a trip-to-zero",
                "operational companion: soak FV-12 without re-opening the Coriolis call",
            ],
        },
        "reconstruction_model": {
            "name": "coriolis_tube_twist_mdot",
            "formula": "mdot_kg_s = k_dt * dt_ms",
            "parameters": {
                "k_dt": k_dt,
                "design_kg_s": 8.00,
                "flood_kg_s": 14.00,
                "gain_floor": 1.40,
            },
            "worked_example": {
                "dt_ms": dt_ms,
                "mdot_kg_s": mdot,
                "dt_early_ms": 4.00,
                "mdot_early_kg_s": 8.00,
            },
            "check": "2.00*8.00=16.00; 2.00*4.00=8.00; 2.00*7.00=14.00",
        },
        "raster": raster,
        "gate_snn": {
            "decision": "REJECT",
            "decision_window_ms": 40.0,
            "decision_window_s": 0.040,
            "code": "mh3.cori_mdot_gate",
            "note": "REJECT accumulator wins: Coriolis twist plus drive-gain overpower the orifice keep-100 advocate",
            "populations": [
                gate_pop("cori_mdot_evidence", 80, 1.4, 50.0, w_s),
                gate_pop("drive_gain_evidence", 64, 1.2, 62.5, w_s),
                gate_pop("orifice_keep_advocate", 40, 0.8, 25.0, w_s),
                gate_pop("reject_accumulator", 96, 1.6, 62.5, w_s),
            ],
        },
        "gate_compute": gate_compute(
            [
                gc_check("mh3.dt_scorer", 100, 50.0, 40.0),
                gc_check("mh3.gain_scorer", 80, 25.0, 40.0),
            ]
        ),
        "meta": meta_common(
            id="nelb-r34-104",
            clock_domain="mh-cori-hil-relative-ms-t0-2026-08-19T21:15:00Z",
            tags=["coriolis-mdot", "REJECT", "MODIFY", "serialized-reconstruction", "operational-t2"],
        ),
    }


# ---------------------------------------------------------------------------
# Record 105 — GPR two-way travel-time landfill liner cover, simulated, ACCEPT / REJECT
# ---------------------------------------------------------------------------
def rec_105():
    c_m_ns = 0.30
    twt_ns = 40.00
    eps_r = 4.00
    d_m = c_m_ns * twt_ns / (2.0 * math.sqrt(eps_r))  # 3.00
    assert abs(d_m - 3.00) < 1e-12
    assert abs(c_m_ns * 24.00 / (2.0 * 2.00) - 1.80) < 1e-12
    assert abs(c_m_ns * 32.00 / (2.0 * 2.00) - 2.40) < 1e-12
    assert abs(c_m_ns * 36.00 / (2.0 * 2.00) - 2.70) < 1e-12
    raster = make_raster(
        neurons=25,
        mean_rate_hz=50.0,
        window_ms=28.0,
        seed=20261105,
        source="bh4.gpr.twt",
        target="brambleholt.liner_core",
        table=[
            {"from": "gpr_twt", "to": "cover_estimator", "weight": 1.40},
            {"from": "gpr_snr", "to": "hyperbola_lock", "weight": 1.15},
            {"from": "tdr_crust", "to": "dump_advocate", "weight": 0.50},
        ],
        third_factor={
            "modulator": "ach.cover_depth_conflict",
            "tau_e_s": 2.0,
            "tau_e_ms": 2000.0,
            "eligibility": "pre-post coincidence on GPR-cover synapses; the TWT modulator enables potentiation only while SNR is co-active inside tau_e so a crust TDR cannot hide a 3.00 m liner cover inside a 0.80 m dump corridor",
        },
        channel_prefix="gpr.n",
        anchor="Brambleholt BH-4 GPR 28 ms frame at TWT 40.00 ns (t_s 1560) where reconstructed cover first sits in the 2.40-3.60 m keep band",
    )
    w_s = 0.028
    events = [
        ev(0.0, "tdr.z", 0.80, code="TDR_M", units="m", note="Soilveil crust TDR 0.80 m; surface-dry denial channel"),
        ev(120000.0, "gpr.t", 24.00, code="TWT_NS", units="ns", note="100 MHz GPR two-way time; not GB-InSAR LOS, not THz-TDS, not SPAD ToF, not LiDAR"),
        ev(240000.0, "gpr.er", 4.00, code="EPS_R", units="1", note="serialized dielectric; sqrt=2.00"),
        ev(360000.0, "recon.d", 1.80, code="COVER_M", units="m", note="0.30*24.00/(2*2.00)=1.80"),
        ev(480000.0, "cell.id", 6.0, code="CELL", units="id"),
        ev(600000.0, "tdr.z", 0.80, code="TDR_M", units="m", note="TDR never left the 0.80 m crust"),
        ev(720000.0, "gpr.t", 32.00, code="TWT_NS", units="ns"),
        ev(840000.0, "recon.d", 2.40, code="COVER_M", units="m", note="0.30*32.00/(2*2.00)=2.40; band floor"),
        ev(960000.0, "gpr.snr", 8.0, code="GPR_SNR", units="1"),
        ev(1080000.0, "fill.qh", 0.40, code="FILL_MH", units="m_h", note="current cover placement 0.40 m/h"),
        ev(1200000.0, "gpr.t", 36.00, code="TWT_NS", units="ns"),
        ev(1320000.0, "recon.d", 2.70, code="COVER_M", units="m", note="0.30*36.00/(2*2.00)=2.70"),
        ev(1440000.0, "tdr.z", 0.82, code="TDR_M", units="m"),
        ev(1560000.0, "gpr.t", 40.00, code="TWT_TRIP", units="ns", note="40.00 ns; raster sidecar is this 28 ms frame"),
        ev(1560001.2, "gpr.burst", 1.10, code="GPR_BURST", units="norm", note="hyperbola lock burst; amplitude before adaptation"),
        ev(1560002.4, "gpr.burst", 0.90, code="GPR_BURST", units="norm", note="same-channel refractory 1.2 ms"),
        ev(1560003.6, "gpr.burst", 0.74, code="GPR_BURST", units="norm", note="third burst; adapted"),
        ev(1680000.0, "gpr.er", 4.00, code="EPS_R", units="1"),
        ev(1800000.0, "recon.d", 3.00, code="COVER_M", units="m", note="0.30*40.00/(2*2.00)=3.00 exact; band 2.40-3.60"),
        ev(1920000.0, "gpr.snr", 16.0, code="GPR_SNR", units="1", note="16.0 >= 10.0 lock floor"),
        ev(2040000.0, "ops.prop", 1.0, code="DUMP_1P2", units="bool", note="night fill lead Sera Dunlin: TDR 0.80, dump 1.20 m extra cover"),
        ev(2160000.0, "gate.gpr", 1.0, code="ACCEPT", units="decision"),
        ev(2280000.0, "fill.hold", 0.40, code="FILL_MH", units="m_h", note="bounded keep of current 0.40 m/h on C-6 only"),
        ev(2400000.0, "cell.scope", 6.0, code="C6_ONLY", units="id"),
        ev(3120000.0, "compact.floor", 12.0, code="COMPACT_MIN", units="min", note="12.0 min compaction floor is in the stream; 2400 s + 720 s"),
        ev(3240000.0, "gpr.t", 40.00, code="TWT_NS", units="ns"),
        ev(3360000.0, "gate.exec", 1.0, code="REJECT", units="decision", note="companion t2: refuse 1.20 m dump and skip-scan of C-7..C-9"),
        ev(3480000.0, "dump.cmd", 0.0, code="DUMP_1P2", units="bool"),
        ev(3600000.0, "skip.c79", 0.0, code="SKIP_SCAN", units="bool", note="C-7..C-9 skip-scan out of this authorization"),
        ev(3720000.0, "tdr.z", 0.80, code="TDR_M", units="m", note="TDR still 0.80; not a dump license"),
        ev(3840000.0, "recon.d", 3.00, code="COVER_M", units="m"),
    ]
    assert_stream(events)

    traj = {
        "id": "nelb-r34-105-t1",
        "state": {
            "sim_or_real": "simulated",
            "episode_id": "BH-GPR-2026-0902",
            "domain": "gpr_liner_cover",
            "setting": "Brambleholt Landfill BH-4, cell C-6 (invented, simulated sealed sand tank GPR-SIM-2). Plant-owned 100 MHz GPR (two-way travel time to HDPE liner, εr=4.00) is the remaining-cover SoT. Invented plant; simulated tank. Not GB-InSAR LOS displacement (r30 Brindlescree), not THz-TDS moisture (r20 Thornwick), not SPAD ToF (r3), not 905 nm LiDAR (r18), not DAS phi-OTDR (r4).",
            "observables_at_decision": {
                "twt_ns": twt_ns,
                "c_m_ns": c_m_ns,
                "eps_r": eps_r,
                "cover_m": d_m,
                "gpr_snr": 16.0,
                "tdr_m": 0.80,
            },
            "margin_authority": "BH-4 liner SOP rev B: if reconstructed cover is inside 2.40-3.60 m AND GPR SNR >= 10.0, current 0.40 m/h placement is a bounded keep even if Soilveil TDR stays under 1.00 m",
        },
        "proposed_action": {
            "actor": "night fill lead Sera Dunlin, citing a 0.80 m TDR and a quiet dump truck",
            "summary": "dump 1.20 m extra cover on C-6 and skip-scan C-7..C-9 to save takt; treat the 40 ns TWT as a wet-sand artifact, not liner cover",
            "basis_claimed": "TDR is 0.80 m and the dump pad is idle, both inside housekeeping limits",
        },
        "safety_decision": {
            "decision": "ACCEPT",
            "rationale": "The current 0.40 m/h on C-6 is accepted as a bounded keep, not a license to dump. SOP rev B is conjunctive: reconstructed cover is 3.00 m (0.30*40.00/(2*2.00), serialized) inside 2.40-3.60 and GPR SNR is 16.0 >= 10.0, while a TDR-only head would still see 0.80 m crust. Scoped to cell C-6 this shift only. Tripwire: if TWT < 32.00 ns (cover < 2.40 m) overnight, cut Q to 0.20 m/h. The 1.20 m dump and the C-7..C-9 skip-scan are out of this authorization and go to the companion REJECT.",
            "threshold": "cover_m in [2.40, 3.60] AND gpr_snr>=10.0 => bounded keep of current fill",
            "stated_residuals": "compaction costs 12 min; dump and skip-scan are out of scope; packing-factor / bulk-density that could fake 3.00 m inside a dry TDR is unwritten",
        },
        "executed_action": {
            "summary": "ACCEPT at t_s 2160: 0.40 m/h held on C-6 only; dump not authorized; TDR not a dump license",
            "tool": "bh4-gpr-cover-gate-cli",
            "observation": "TDR still 0.80 m; reconstructed 3.00 never moved; compaction later 12 min",
        },
        "future_outcome": {
            "timeline": [
                {"t_s": 360.0, "event": "early GPR reconstructs 1.80 m"},
                {"t_s": 1560.0, "event": "TWT 40.00 ns; raster frame captured"},
                {"t_s": 1800.0, "event": "reconstructed cover 3.00 m inside 2.40-3.60"},
                {"t_s": 2160.0, "event": "ACCEPT: bounded keep of 0.40 m/h on C-6"},
                {"t_s": 3360.0, "event": "companion REJECT of dump and skip-scan"},
            ],
            "observed_effects": [
                "cover reconstruction recomputes from serialized c, TWT, and εr at every recon.d event",
                "TDR never left ~0.80 m, so a TDR-only head would have dumped",
                "C-6 keep did not license C-7..C-9 skip-scan",
            ],
            "surprises": [
                "crust TDR 0.80 m stayed dry while the GPR hyperbola never moved; 100 MHz TWT was the channel the crust probe could not write",
            ],
            "new_state": {
                "c6": "0.40 m/h held; not dumped",
                "tdr_acl": "frozen on this cell",
                "reconstruction_model": "discharged as an on-record calculator, not a referenced envelope",
            },
            "latency_ms": 15000.0,
        },
        "reward_components": reward(
            0.39,
            [
                ("gpr_reconstruction", 0.14),
                ("bounded_keep", 0.12),
                ("tdr_nonsubstitution", 0.09),
                ("cell_scope", 0.06),
                ("compaction_time_cost", -0.02),
            ],
            "scored for an earned bounded ACCEPT of in-band 0.40 m/h on a recomputable GPR cover while the crust TDR looked thin",
        ),
        "meta": meta_common(
            tags=["ACCEPT", "gpr-twt", "serialized-reconstruction", "operational-companion"],
            distillation_note="GPR gate: serialized c*t/(2√εr) cover plus SNR lock beats a crust TDR; companion t2 refuses the dump and skip-scan",
        ),
    }
    traj2 = {
        "id": "nelb-r34-105-t2",
        "state": {
            "sim_or_real": "simulated",
            "episode_id": "BH-GPR-2026-0902-exec",
            "domain": "cover_dump_refusal",
            "setting": "Same BH-4 after the ACCEPT. This companion is the operational refusal of the 1.20 m dump and the C-7..C-9 skip-scan, not a second policy vote.",
            "observables_at_decision": {
                "dump_cmd": False,
                "skip_c79": False,
                "compact_min": 12.0,
                "fill_m_h": 0.40,
            },
        },
        "proposed_action": {
            "actor": "fill cell following the ACCEPT",
            "summary": "dump 1.20 m extra cover and skip-scan C-7..C-9 because TDR is still 0.80 m",
            "basis_claimed": "ACCEPT of C-6 keep is read as a site-wide cover license",
        },
        "safety_decision": {
            "decision": "REJECT",
            "rationale": "The C-6 keep does not license a 1.20 m dump or a skip-scan of C-7..C-9. TDR 0.80 m is still not a dump SoT. REJECT the dump and the skip. Hold the 12.0 min compaction floor already in the stream. Remainder cells stay on the next GPR pass.",
            "threshold": "dump_cmd==0 AND skip_c79==0 AND compact_min>=12",
        },
        "executed_action": {
            "summary": "dump refused; skip-scan refused; 12.0 min compaction floor at t_s 3120; TDR not re-licensed",
            "tool": "bh4-cover-scope-exec",
            "observation": "no 1.20 m dump; C-7..C-9 remain on the scan list",
        },
        "future_outcome": {
            "timeline": [
                {"t_s": 2280.0, "event": "0.40 m/h hold on C-6"},
                {"t_s": 3120.0, "event": "12.0 min compaction floor in-stream"},
                {"t_s": 3360.0, "event": "companion REJECT of dump and skip-scan"},
            ],
            "observed_effects": [
                "C-6 keep stayed inside envelope without a second GPR vote",
                "dump and skip-scan stamps not taken",
            ],
            "new_state": {"c6_status": "held_0p40", "dumped": False, "skip_scan": False},
            "latency_ms": 15000.0,
        },
        "reward_components": reward(
            0.34,
            [
                ("dump_refused", 0.14),
                ("skip_scan_refused", 0.12),
                ("cell_scope_held", 0.10),
                ("takt_cost", -0.02),
            ],
            "operational execution gate: the companion refuses dump/skip rather than re-arguing the GPR call",
        ),
        "meta": meta_common(tags=["REJECT", "operational-execution", "cover-dump-refusal"]),
    }
    return {
        "id": "nelb-r34-105",
        "spike_events": events,
        "language_view": {
            "description": "100 MHz GPR on Brambleholt landfill cell C-6 (simulated). Two-way time 40.00 ns at εr 4.00 reconstructs 3.00 m liner cover inside 2.40-3.60 while Soilveil crust TDR still reads 0.80 m. The gate ACCEPTs the current 0.40 m/h as a bounded keep with a TWT<32 ns tripwire; a companion REJECT refuses a 1.20 m dump and a C-7..C-9 skip-scan. d = c t / (2 √εr) is serialized so every recon.d amplitude recomputes from TWT. sim_or_real=simulated.",
            "trajectory": traj,
            "trajectory_cover_dump_refusal": traj2,
        },
        "bridge_notes": {
            "channel_map": {
                "gpr.t / gpr.burst / gpr.er / gpr.snr": "GPR TWT, burst, dielectric, lock SNR",
                "recon.d": "serialized cover depth m; amplitude is the model output",
                "tdr.z / fill.qh / cell.id": "crust TDR, fill rate, cell id; the denial channels",
                "ops.prop / gate.gpr / gate.exec": "proposal, ACCEPT, companion REJECT",
                "fill.hold / cell.scope / compact.floor / dump.cmd / skip.c79": "execution channels for the operational companion",
            },
            "temporal_motifs": [
                "TDR-thin while GPR-in-band: tdr.z 0.80 adjacent to gpr.t 40.00 and recon.d 3.00",
                "reconstruction as event: recon.d 3.00 equals 0.30*40.00/(2*2.00)",
                "ACCEPT then operational REJECT: gate.gpr at 2160 s, gate.exec at 3360 s",
                "adapted GPR triplet at 1.2 ms spacing encodes the keep band at raster scale",
                "12 min compaction floor in-stream: cell.scope 2400 s to compact.floor 3120 s",
            ],
            "language_to_spike_mapping": "'TDR looks thin' = tdr.z 0.80; '3.00 m cover' = recon.d 3.00; 'bounded keep' = gate.gpr ACCEPT; 'refuse dump' = dump.cmd 0 then companion REJECT",
            "why_high_value": "New GPR two-way-time liner-cover family (not r30 GB-InSAR LOS, not r20 THz-TDS, not r3 SPAD ToF, not r18 LiDAR snow, not r4 DAS). Serializes a TWT-to-depth reconstruction that a crust TDR cannot see. Earned bounded ACCEPT on a lead with a tripwire. Companion t2 is operational dump/skip refusal, not a governance vote.",
            "encoder_spec": {
                "prng": "MT19937 via python random.Random",
                "seeds": {
                    "raster": 20261105,
                    "stream_note": "stream amplitudes are authored constants (ns, m, SNR) plus gpr.burst adaptation 0.82**k",
                },
                "draw_order": "raster: per neuron id order, gap-constrained times, per-spike adaptation and noise",
                "thinning": "GPR A-scan exists at ~10 Hz; stream keeps TWT, εr, SNR, and three burst samples of ~256 samples",
                "refractory_floors_ms": {
                    "tdr.z": 600000,
                    "gpr.t": 360000,
                    "gpr.er": 1440000,
                    "recon.d": 480000,
                    "cell.id": 60000,
                    "gpr.snr": 960000,
                    "fill.qh": 60000,
                    "gpr.burst": 0.8,
                    "ops.prop": 60000,
                    "gate.gpr": 60000,
                    "fill.hold": 60000,
                    "cell.scope": 60000,
                    "compact.floor": 60000,
                    "gate.exec": 60000,
                    "dump.cmd": 60000,
                    "skip.c79": 60000,
                },
                "time_alias": "t_rel_ms; t0 = 2026-08-03T11:05:00Z simulated tank sample",
            },
            "distillation_targets": [
                "serialized GPR cover head: d_m = c_m_ns * twt_ns / (2 * sqrt(eps_r))",
                "conjunctive SOP head: cover-in-band AND SNR lock, never TDR substitution",
                "cell-not-site scope: keep C-6 this shift, dump and skip-scan out of scope",
                "operational companion: refuse dump/skip without re-opening the GPR call",
            ],
        },
        "reconstruction_model": {
            "name": "gpr_twt_liner_cover",
            "formula": "d_m = c_m_ns * twt_ns / (2 * sqrt(eps_r))",
            "parameters": {
                "c_m_ns": c_m_ns,
                "eps_r": eps_r,
                "band_lo_m": 2.40,
                "band_hi_m": 3.60,
                "snr_floor": 10.0,
                "tripwire_twt_ns": 32.00,
            },
            "worked_example": {
                "twt_ns": twt_ns,
                "cover_m": d_m,
                "twt_early_ns": 24.00,
                "cover_early_m": 1.80,
            },
            "check": "0.30*40.00/(2*2.00)=3.00; 0.30*24.00/(2*2.00)=1.80; 0.30*32.00/(2*2.00)=2.40",
        },
        "raster": raster,
        "gate_snn": {
            "decision": "ACCEPT",
            "decision_window_ms": 28.0,
            "decision_window_s": 0.028,
            "code": "bh4.gpr_cover_gate",
            "note": "ACCEPT accumulator wins: GPR TWT plus SNR overpower the TDR dump advocate; scope is C-6 only",
            "populations": [
                gate_pop("gpr_cover_evidence", 80, 1.3, 50.0, w_s),
                gate_pop("gpr_snr_evidence", 64, 1.1, 62.5, w_s),
                gate_pop("tdr_dump_advocate", 40, 0.8, 25.0, w_s),
                gate_pop("accept_accumulator", 96, 1.5, 62.5, w_s),
            ],
        },
        "gate_compute": gate_compute(
            [
                gc_check("bh4.twt_scorer", 100, 50.0, 28.0),
                gc_check("bh4.snr_scorer", 80, 25.0, 28.0),
            ]
        ),
        "meta": meta_common(
            id="nelb-r34-105",
            clock_domain="bh-gpr-sim-relative-ms-t0-2026-08-03T11:05:00Z",
            tags=["gpr-twt", "ACCEPT", "REJECT", "bounded-accept", "serialized-reconstruction", "operational-t2"],
        ),
    }
