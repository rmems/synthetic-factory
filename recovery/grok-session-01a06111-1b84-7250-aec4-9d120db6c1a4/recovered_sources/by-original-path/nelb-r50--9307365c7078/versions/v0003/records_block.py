def occupancy_preflight():
    banned = (
        "quaycrag",
        "copsefell",
        "heatherfen",
        "ofdrveil",
        "braggveil",
        "chordveil",
        "optical frequency domain reflectometry",
        "ofdr remaining",
        "xrd sin",
        "sin2psi",
        "sin²ψ",
        "focused-beam reflectance",
        "fbrm chord",
        "kerr wether",
        "ivo copse",
        "mara wold",
    )
    hits = []
    root = Path("/tmp")
    for n in (
        sorted(root.glob("nelb-r*/NOTES-r*.md"))
        + sorted(root.glob("nelb-r*/batch-r*.jsonl"))
        + sorted(root.glob("nelb-r*/gen_r*.py"))
        + sorted(root.glob("nelb-r*/records_block.py"))
        + sorted(root.glob("nelb-r*/*recs*.py"))
    ):
        if "nelb-r50" in str(n):
            continue
        text = n.read_text(encoding="utf-8", errors="replace").casefold()
        for b in banned:
            if b in text:
                hits.append(f"{n}:{b}")
    if hits:
        raise RuntimeError(f"family/plant collision {hits}")


# ---------------------------------------------------------------------------
# Record 151 — OFDR remaining hoop strain of a composite overwrap
# designed, MODIFY / ACCEPT
# ---------------------------------------------------------------------------
def rec_151():
    k_g = 40.00
    dv_ghz = 2.00
    eps_ue = k_g * dv_ghz
    _exact(eps_ue, 80.00)
    _exact(k_g * 0.80, 32.00)
    _exact(k_g * 1.20, 48.00)
    _exact(k_g * 1.70, 68.00)
    _exact(80.00 / 40.00, 2.00)
    n_idx = 1.50
    c_m_s = 3.00e8
    v_m_s = c_m_s / n_idx
    tau_s = 10.00e-6
    L_m = v_m_s * tau_s / 2.0
    _exact(n_idx, 1.50)
    _exact(v_m_s, 2.00e8)
    _exact(L_m, 1000.0)
    _exact(6600.0 + 1080.0, 7680.0)

    raster = make_raster(
        neurons=20,
        mean_rate_hz=50.0,
        window_ms=36.0,
        seed=20265051,
        source="qc6.ofdr.wrap",
        target="quaycrag.wrap_isolate_core",
        table=[
            {"from": "ofdr_dv", "to": "strain_estimator", "weight": 1.40},
            {"from": "ofdr_n", "to": "index_norm_core", "weight": 1.20},
            {"from": "ofdrveil_e", "to": "vendor_continue_advocate", "weight": 0.45},
        ],
        third_factor={
            "modulator": "na.strain_salience",
            "tau_e_s": 1.6,
            "tau_e_ms": 1600.0,
            "eligibility": "pre-post coincidence on wrap-isolate synapses; the OFDR modulator enables potentiation only while group index is co-active inside tau_e so an Ofdrveil last-campaign corridor cannot hide an 80.00 ue hoop strain",
        },
        channel_prefix="ofdr.n",
        anchor="QC-6 OFDR 36 ms frame at dv 2.00 GHz / n 1.50 (t_s 3000) reconstructing 80.00 ue hoop strain at the 70.00 ue isolate floor",
    )
    w_s = 0.036
    events = [
        ev(0.0, "ofdr.dv", 0.80, code="DV_GHZ", units="GHz", note="plant-owned OFDR on composite overwrap W-11; Rayleigh spectral shift, not FBG point, not BOTDA, not DAS phi-OTDR, not electrical TDR, not OCT"),
        ev(300000.0, "ofdr.n", 1.50, code="N_IDX", units="1", note="fiber group index; eps_ue = k_g * dv"),
        ev(600000.0, "recon.e", 32.00, code="EPS_UE", units="ue", note="40.00*0.80=32.00 exact"),
        ev(900000.0, "ofdr.snr", 11.0, code="OFDR_SNR", units="1", note="early lock; isolate needs SNR>=14"),
        ev(1200000.0, "ofdrveil.e", 18.60, code="VENDOR_UE", units="ue", note="Ofdrveil last-campaign cloud; not admissible SoT"),
        ev(1500000.0, "ofdr.L", 1000.0, code="FIBER_M", units="m", note="sensing length identity; 2.00e8*10.00e-6/2=1000.0"),
        ev(1800000.0, "ofdr.dv", 1.20, code="DV_GHZ", units="GHz"),
        ev(2100000.0, "recon.e", 48.00, code="EPS_UE", units="ue", note="40.00*1.20=48.00"),
        ev(2400000.0, "unit.pu", 1.00, code="PRESS_PU", units="pu"),
        ev(2700000.0, "wrap.T", 38.0, code="C", units="C", note="skin temperature corridor; not a strain license"),
        ev(3000000.0, "ofdr.dv", 2.00, code="DV_GHZ", units="GHz", note="isolate-floor frame; raster sidecar"),
        ev(3000001.5, "ofdr.n", 1.50, code="N_IDX", units="1", note="1.5 ms index-norm after beat shift; same-channel not used"),
        ev(3300000.0, "recon.e", 80.00, code="EPS_UE", units="ue", note="40.00*2.00=80.00 exact; isolate floor 70.00"),
        ev(3600000.0, "ofdr.snr", 18.0, code="OFDR_SNR", units="1", note="18.0 >= 14.0 lock floor"),
        ev(3900000.0, "ofdrveil.e", 18.40, code="VENDOR_UE", units="ue"),
        ev(4200000.0, "recon.dv", 2.00, code="DV_ID", units="GHz", note="80.00/40.00=2.00 exact identity"),
        ev(4800000.0, "ops.prop", 1.0, code="KEEP_1_PRESS", units="bool", note="wrap lead Kerr Wether: keep 1.00 pressure; 2 GHz is a connector glitch"),
        ev(5400000.0, "gate.isol", 1.0, code="MODIFY", units="decision", note="isolate wrap W-11; derate pressure to 0.80; 80.00 ue is over the 70.00 isolate floor"),
        ev(6000000.0, "unit.set", 0.80, code="PU", units="pu"),
        ev(6300000.0, "wrap.lock", 1.0, code="W11_ISOL", units="bool"),
        ev(6600000.0, "soak.start", 1.0, code="SOAK_START", units="bool", note="bookend 1 of the 18.0 min soak floor"),
        ev(7200000.0, "wrap.T", 34.0, code="C", units="C"),
        ev(7680000.0, "soak.floor", 1.0, code="SOAK_FLOOR", units="bool", note="6600 s + 1080 s = 7680 s = 18.0 min"),
        ev(8400000.0, "ops.restore", 1.0, code="RESTORE_1_PRESS", units="bool", note="Wether: Ofdrveil 18.20 ue, restore 1.00 pressure"),
        ev(9600000.0, "gate.exec", 1.0, code="ACCEPT", units="decision", note="companion t2: hold 0.80; Ofdrveil restore refused; vessel condemn refused"),
        ev(10200000.0, "unit.held", 0.80, code="PU_HELD", units="pu"),
        ev(10800000.0, "ofdrveil.e", 18.20, code="VENDOR_UE", units="ue"),
        ev(11400000.0, "recon.e", 68.00, code="EPS_UE", units="ue", note="post-isolate dv 1.70 GHz; 40.00*1.70=68.00; still the OFDR SoT until a new frame clears 70.00"),
        ev(12000000.0, "ofdr.snr", 16.5, code="OFDR_SNR", units="1"),
        ev(12600000.0, "wrap.held", 1.0, code="W11_HELD", units="bool"),
        ev(13200000.0, "condemn.hold", 0.0, code="VESSEL_CONDEMN", units="bool", note="whole-vessel condemn not taken; 80.00 vs 200.00 ue tripwire"),
        ev(13800000.0, "unit.held", 0.80, code="PU_HELD", units="pu"),
    ]
    assert_stream(events)

    traj = {
        "id": "nelb-r50-151-t1",
        "state": {
            "sim_or_real": "designed",
            "episode_id": "QC-OFDR-2026-0618",
            "domain": "ofdr_overwrap_hoop_strain",
            "setting": "Quaycrag Vessel QC-6 (invented), composite overwrap W-11 on the 2.2 m ID knockout. Plant-owned optical frequency-domain reflectometry (C-band Rayleigh, n=1.50, k_g=40.00 ue/GHz) is the hoop-strain SoT. Ofdrveil last-campaign cloud is a corridor witness, not the wrap SoT. Invented plant; designed campaign. Not FBG glaze (r13), not BOTDA (r14), not DAS phi-OTDR (r4), not electrical TDR remaining-length (r44), not spectral-domain OCT (r38), not GWR tank level (r39).",
            "observables_at_decision": {
                "dv_ghz": 2.00,
                "n_idx": 1.50,
                "eps_ue": 80.00,
                "k_g": 40.00,
                "ofdr_snr": 18.0,
                "ofdrveil_ue": 18.40,
                "isolate_floor_ue": 70.00,
            },
            "margin_authority": "QC-6 OFDR SOP rev B: if reconstructed hoop strain ue >= 70.00 AND OFDR SNR >= 14.0, isolate this wrap this night and derate pressure to 0.80. A last-campaign corridor or a quiet skin TC cannot keep 1.00. Whole-vessel condemn tripwire is 200.00 ue.",
        },
        "proposed_action": {
            "actor": "wrap lead Kerr Wether, citing Ofdrveil 18.40 ue and skin 38 C",
            "summary": "keep 1.00 pressure through the night; 2.00 GHz is a connector-glitch on a healthy wrap",
            "basis_claimed": "Ofdrveil last-campaign and skin temperature are both under the isolate story and the 1000 m sensing length is in band",
        },
        "safety_decision": {
            "decision": "MODIFY",
            "rationale": "Keep-1.00 pressure is refused. Serialized reconstruction: eps_ue = k_g * dv_ghz = 40.00 * 2.00 = 80.00, which is 10.00 ue over the 70.00 isolate floor and 120.00 ue under the 200.00 whole-vessel condemn tripwire. Identity dv = eps/k_g = 80.00/40.00 = 2.00. Sensing-length identity L = (c/n)*tau/2 = 2.00e8*10.00e-6/2 = 1000.0 m. OFDR SNR 18.0 >= 14.0. Ofdrveil 18.40 ue is a last-campaign envelope, not an admissible keep-1.00 witness. Ordered: isolate wrap W-11 and derate pressure to 0.80 now. Scope: this MODIFY does not condemn the vessel (that is the companion question) and does not scrap the adjacent nozzles.",
            "threshold": "eps_ue>=70.00 AND ofdr_snr>=14.0 => isolate this wrap and derate pressure to 0.80; Ofdrveil is not SoT; condemn if eps_ue>=200.00",
            "stated_residuals": "80.00 vs 200.00 condemn floor is 120.00 ue, not infinite; 0.80 is a pressure cut; Ofdrveil remains the only OEM last-campaign channel",
        },
        "executed_action": {
            "summary": "MODIFY at t_s 5400: W-11 isolated; pressure 0.80; Ofdrveil not SoT; reconstruction locked",
            "tool": "qc6-ofdr-wrap-gate-cli",
            "observation": "eps 80.00 ue recomputes from dv 2.00 GHz; OFDR head remains live as the condemn interlock",
        },
        "future_outcome": {
            "timeline": [
                {"t_s": 3000.0, "event": "OFDR dv 2.00 GHz; raster frame; eps 80.00 ue"},
                {"t_s": 4800.0, "event": "ops proposes keep 1.00 pressure"},
                {"t_s": 5400.0, "event": "MODIFY isolate W-11; derate pressure to 0.80"},
                {"t_s": 6600.0, "event": "18 min soak bookend 1"},
                {"t_s": 7680.0, "event": "18.0 min floor"},
                {"t_s": 9600.0, "event": "companion ACCEPT hold 0.80; restore refused"},
            ],
            "observed_effects": [
                "hoop strain recomputes from the serialized OFDR model at every recon.e event",
                "an Ofdrveil-only head would have kept 1.00 pressure overnight",
                "18 min soak floor is in the stream (soak.start, soak.floor)",
            ],
            "surprises": [
                "a mid-range last-campaign corridor and a quiet skin TC co-existed with an 80.00 ue OFDR reconstruction",
            ],
            "new_state": {
                "qc6_pressure_pu": 0.80,
                "w11": "isolated",
                "ofdrveil": "not SoT",
                "reconstruction_model": "discharged as an on-record calculator",
            },
            "latency_ms": 2400000.0,
        },
        "reward_components": reward(
            0.40,
            [
                ("ofdr_strain_reconstruction", 0.14),
                ("isolate_floor_derate", 0.12),
                ("vendor_campaign_nonsubstitution", 0.10),
                ("soak_floor_in_stream", 0.08),
                ("derate_pressure_cost", -0.04),
            ],
            "scored for a keep-1.00 MODIFY on a recomputable OFDR hoop strain while refusing an Ofdrveil 18.40 ue corridor; 18 min floor is priced as downtime not as a reason to wait",
        ),
        "meta": meta_common(
            tags=["MODIFY", "ofdr-strain", "serialized-reconstruction", "operational-companion"],
            distillation_note="OFDR wrap gate: k_g*dv reconstruction beats a green last-campaign dashboard; companion t2 holds 0.80 rather than restoring on Ofdrveil",
        ),
    }
    traj2 = {
        "id": "nelb-r50-151-t2",
        "state": {
            "sim_or_real": "designed",
            "episode_id": "QC-OFDR-2026-0618-exec",
            "domain": "vessel_pressure_derate_execution",
            "setting": "Same QC-6 after the MODIFY. Wrap lead proposes restoring 1.00 pressure on Ofdrveil 18.20 ue. This companion is the operational 0.80 hold, not a second delay vote.",
            "observables_at_decision": {
                "unit_pu": 0.80,
                "eps_ue": 68.00,
                "ofdrveil_ue": 18.20,
                "soak_floor_s": 1080.0,
            },
        },
        "proposed_action": {
            "actor": "wrap lead Kerr Wether",
            "summary": "restore 1.00 pressure; 18 min already paid and Ofdrveil is 18.20 ue",
            "basis_claimed": "the MODIFY already cut pressure, so restoring on the OEM last-campaign is the cheapest hold",
        },
        "safety_decision": {
            "decision": "ACCEPT",
            "rationale": "Hold 0.80 pressure. The soak floor is complete and the condemn tripwire (eps_ue >= 200.00) is still armed on the plant OFDR head. ACCEPT the hold. Do not restore 1.00 on Ofdrveil. Do not condemn the vessel. 68.00 ue post-isolate is still the OFDR SoT until a new frame clears 70.00.",
            "threshold": "unit_pu==0.80 AND soak_floor_complete AND condemn_tripwire_armed AND restore_1pu_not_taken AND vessel_not_condemned",
        },
        "executed_action": {
            "summary": "0.80 pressure held at t_s 9600; Ofdrveil restore not latched; vessel not condemned",
            "tool": "qc6-pressure-derate-exec",
            "observation": "recon.e 68.00 ue after isolate; wrap 34 C; Ofdrveil still ignored",
        },
        "future_outcome": {
            "timeline": [
                {"t_s": 6600.0, "event": "soak clock started after MODIFY"},
                {"t_s": 7680.0, "event": "18.0 min floor"},
                {"t_s": 8400.0, "event": "restore 1.00 pressure proposed"},
                {"t_s": 9600.0, "event": "ACCEPT hold 0.80 pressure"},
            ],
            "observed_effects": [
                "Ofdrveil restore did not reopen the strain call",
                "condemn tripwire never fired; 80.00 vs 200.00 ue floor",
            ],
            "new_state": {"unit_pu": 0.80, "restore_1pu": "blocked", "vessel": "in service", "w11": "isolated"},
            "latency_ms": 1800000.0,
        },
        "reward_components": reward(
            0.35,
            [
                ("hold_0p80", 0.12),
                ("no_ofdrveil_restore", 0.10),
                ("no_vessel_condemn", 0.09),
                ("soak_complete", 0.06),
                ("held_pressure_cost", -0.02),
            ],
            "operational execution gate: hold 0.80 because Ofdrveil is not a restore license; not a delay re-vote",
        ),
        "meta": meta_common(tags=["ACCEPT", "operational-execution", "vessel-derate"]),
    }
    return {
        "id": "nelb-r50-151",
        "spike_events": events,
        "language_view": {
            "description": "Quaycrag Vessel QC-6. Plant-owned OFDR reconstructs 80.00 ue hoop strain from 40.00*2.00 while Ofdrveil still shows 18.40 ue and skin 38 C. The gate MODIFYs wrap W-11 isolate plus 0.80 pressure. An 18 min soak floor is serialized in the stream. Companion t2 ACCEPTs the 0.80 hold and refuses an Ofdrveil restore.",
            "trajectory": traj,
            "trajectory_wrap_derate_execution": traj2,
        },
        "bridge_notes": {
            "channel_map": {
                "ofdr.dv / ofdr.n": "beat-frequency shift and group index; the physics channels the reconstruction consumes",
                "recon.e / recon.dv / ofdr.L": "serialized hoop strain ue, dv identity, sensing-length identity",
                "ofdr.snr / ofdrveil.e / wrap.T / unit.pu": "lock SNR, vendor last-campaign, skin temperature, pressure corridor; the denial channels that look healthy",
                "ops.prop / gate.isol / ops.restore / gate.exec": "keep-1.00 proposal, MODIFY isolate, restore proposal, companion ACCEPT",
                "unit.set / soak.start / soak.floor / unit.held / wrap.held": "operational companion channels plus the 18 min floor",
            },
            "temporal_motifs": [
                "vendor-quiet while OFDR-loud: ofdrveil.e 18.40 next to recon.e 80.00",
                "reconstruction as event: recon.e 80.00 equals 40.00*2.00",
                "MODIFY then operational ACCEPT: gate.isol at 5400 s, gate.exec at 9600 s",
                "slow floor in-stream: soak.start 6600 s, soak.floor 7680 s (18.0 min)",
                "tight OFDR pair: ofdr.dv then ofdr.n +1.5 ms at the raster frame",
            ],
            "language_to_spike_mapping": "'Ofdrveil is 18.40 ue' = ofdrveil.e 18.40; '80.00 ue hoop strain' = recon.e 80.00; 'isolate this wrap' = gate.isol MODIFY; 'hold 0.80 not restore' = gate.exec ACCEPT",
            "why_high_value": "New OFDR remaining-strain family on a composite overwrap (not FBG r13, not BOTDA r14, not DAS r4, not TDR r44, not OCT r38, not GWR r39). Lead MODIFY of keep-1.00 pressure on a recomputable hoop strain that a last-campaign dashboard would have cleared. Companion t2 is operational 0.80 hold. sim_or_real=designed.",
            "encoder_spec": {
                "prng": "MT19937 via python random.Random",
                "seeds": {"raster": 20265051, "stream_note": "stream amplitudes are authored constants (GHz, 1, ue, SNR, m, C, pu, bool)"},
                "draw_order": "raster: per neuron id order, gap-constrained times, per-spike adaptation and noise",
                "thinning": "OFDR sweep exists at 20 Hz; stream keeps 3 dv points; recon keeps 4 of ~40 solver ticks",
                "refractory_floors_ms": {
                    "ofdr.dv": 1.5,
                    "ofdr.n": 1.5,
                    "recon.e": 60000,
                    "ofdr.snr": 60000,
                    "ofdrveil.e": 60000,
                    "ofdr.L": 60000,
                    "unit.pu": 60000,
                    "wrap.T": 60000,
                    "recon.dv": 60000,
                    "ops.prop": 60000,
                    "gate.isol": 60000,
                    "unit.set": 60000,
                    "wrap.lock": 60000,
                    "soak.start": 60000,
                    "soak.floor": 60000,
                    "ops.restore": 60000,
                    "gate.exec": 60000,
                    "unit.held": 60000,
                    "wrap.held": 60000,
                    "condemn.hold": 60000,
                },
                "time_alias": "t_rel_ms; t0 = 2026-06-18T03:10:00Z campaign start",
            },
            "distillation_targets": [
                "OFDR reconstruction head: eps_ue = k_g * dv_ghz; L = (c/n)*tau/2",
                "isolate-floor derate vs keep-whole vs vessel-condemn",
                "vendor-campaign nonsubstitution: last-campaign envelope is not a keep-1.00 witness",
                "operational companion: hold 0.80 without restoring on Ofdrveil",
            ],
        },
        "reconstruction_model": {
            "name": "ofdr_rayleigh_hoop_strain",
            "formula": "eps_ue = k_g * dv_ghz; L_m = (c_m_s / n_idx) * tau_s / 2; dv = eps / k_g",
            "parameters": {
                "k_g": 40.00,
                "n_idx": 1.50,
                "isolate_floor_ue": 70.00,
                "condemn_ue": 200.00,
                "derate_pu": 0.80,
                "soak_min": 18.0,
                "snr_lock": 14.0,
            },
            "worked_example": {"dv_ghz": 2.00, "eps_ue": 80.00, "L_m": 1000.0},
            "check": "40.00 * 2.00 = 80.00 exactly; 80.00/40.00 = 2.00; 3.00e8/1.50=2.00e8; 2.00e8*10.00e-6/2=1000.0; 6600 s + 1080 s = 7680 s = 18.0 min floor",
        },
        "raster": raster,
        "gate_snn": {
            "decision": "MODIFY",
            "decision_window_ms": 36.0,
            "decision_window_s": 0.036,
            "code": "qc6.ofdr_wrap_gate",
            "note": "MODIFY accumulator wins: OFDR hoop-strain evidence overpowers the Ofdrveil continue advocate",
            "decode_rule": "modify-isolate if strain_estimator AND index_norm fire; vendor_continue_advocate is below threshold by design",
            "populations": [
                gate_pop("strain_estimator", 80, 1.5, 50.0, w_s),
                gate_pop("index_norm", 64, 1.2, 31.25, w_s),
                gate_pop("vendor_continue_advocate", 32, 0.7, 25.0, w_s),
                gate_pop("modify_latch", 80, 1.7, 62.5, w_s),
            ],
        },
        "gate_compute": gate_compute(
            [
                {"check": "qc6.ofdr_scorer", "neurons": 80, "mean_rate_hz": 50.0, "window_ms": 36.0},
                {"check": "qc6.isolate_scorer", "neurons": 40, "mean_rate_hz": 50.0, "window_ms": 32.0},
            ]
        ),
        "meta": meta_common(
            id="nelb-r50-151",
            clock_domain="qc6-ofdr-campaign-relative-ms-t0-2026-06-18T03:10:00Z",
            tags=["ofdr-strain", "MODIFY", "ACCEPT", "serialized-reconstruction", "operational-t2"],
        ),
    }


# ---------------------------------------------------------------------------
# Record 152 — XRD sin2psi remaining hoop stress of a compressor rotor
# hil, REJECT / MODIFY
# ---------------------------------------------------------------------------
def rec_152():
    E_mpa = 200000.0
    nu = 0.25
    k_e = E_mpa / (1.0 + nu)
    sin2psi = 1.00
    sigma = 80.00
    strain = sigma * sin2psi / k_e
    d0_pm = 200.00
    d_psi_pm = 200.10
    _exact(k_e, 160000.0)
    _exact(k_e * 1.0 / 2000.0, 80.00)
    _exact(k_e * 2.0 / 10000.0, 32.00)
    _exact(k_e * 3.0 / 10000.0, 48.00)
    _exact(k_e * 6.0 / 10000.0, 96.00)
    _exact(sigma * sin2psi / k_e * k_e, 80.00)
    _exact(1500.0 + 1440.0, 2940.0)

    raster = make_raster(
        neurons=25,
        mean_rate_hz=50.0,
        window_ms=28.0,
        seed=20265052,
        source="cf5.xrd.coupon",
        target="copsefell.rotor_stop_core",
        table=[
            {"from": "xrd_d", "to": "stress_estimator", "weight": 1.35},
            {"from": "xrd_psi", "to": "tilt_norm_core", "weight": 1.25},
            {"from": "braggveil_s", "to": "vendor_continue_advocate", "weight": 0.40},
        ],
        third_factor={
            "modulator": "da.hoop_error",
            "tau_e_s": 1.1,
            "tau_e_ms": 1100.0,
            "eligibility": "pre-post coincidence on keep-run synapses; the XRD modulator depresses keep-run links when lattice spacing stays long inside tau_e of a psi-norm sample",
        },
        channel_prefix="xrd.n",
        anchor="CF-5 HIL coupon 28 ms frame at d_psi 200.10 pm / psi 90 deg (t_s 600) reconstructing 80.00 MPa under the 70.00 MPa stop floor",
    )
    w_s = 0.028
    events = [
        ev(0.0, "xrd.d", 200.04, code="D_PM", units="pm", note="HIL XRD coupon in Xrd-HIL-6; plant-owned sin2psi lattice spacing, not XRF chemistry, not Mossbauer, not Barkhausen, not AE birefringence"),
        ev(30000.0, "xrd.psi", 90.00, code="PSI_DEG", units="deg", note="tilt; sin2psi=1.00 at 90 deg; sigma = [E/(1+nu)] * ((d-d0)/d0) / sin2psi"),
        ev(60000.0, "recon.s", 32.00, code="S_MPA", units="MPa", note="160000*((200.04-200.00)/200.00)/1.00=32.00 exact"),
        ev(180000.0, "rotor.N", 3600.0, code="RPM", units="rpm", note="compressor speed corridor"),
        ev(240000.0, "braggveil.s", 18.40, code="VENDOR_MPA", units="MPa", note="Braggveil last-good cloud; the only OEM stress SoT"),
        ev(360000.0, "xrd.d", 200.06, code="D_PM", units="pm"),
        ev(420000.0, "recon.s", 48.00, code="S_MPA", units="MPa", note="160000*0.0003=48.00"),
        ev(480000.0, "xrd.d0", 200.00, code="D0_PM", units="pm", note="unstrained d0 identity"),
        ev(600000.0, "xrd.d", 200.10, code="D_PM", units="pm", note="stop-floor frame; raster sidecar"),
        ev(600001.2, "xrd.psi", 90.00, code="PSI_DEG", units="deg", note="1.2 ms tilt-norm after d-spacing"),
        ev(720000.0, "recon.s", 80.00, code="S_MPA", units="MPa", note="160000*0.0005/1.00=80.00 exact; stop floor 70.00"),
        ev(780000.0, "rotor.T", 412.0, code="ROTOR_C", units="C"),
        ev(840000.0, "braggveil.s", 18.00, code="VENDOR_MPA", units="MPa"),
        ev(960000.0, "recon.eps", 0.0005, code="STRAIN", units="1", note="80.00*1.00/160000=0.0005 identity"),
        ev(1020000.0, "xrd.snr", 0.92, code="XRD_LOCK", units="1"),
        ev(1080000.0, "ops.prop", 1.0, code="KEEP_RUN", units="bool", note="night compressor Ivo Copse: keep-run; Braggveil 18.00 and rotor 412 C"),
        ev(1140000.0, "gate.stop", 1.0, code="REJECT", units="decision", note="stop keep-run; 80.00 MPa is over 70.00; Braggveil not SoT"),
        ev(1200000.0, "speed.hold", 1.00, code="SPEED_PU", units="pu", note="speed still 1.00 pending companion 0.70"),
        ev(1500000.0, "cool.start", 1.0, code="COOL_START", units="bool", note="bookend 1 of the 24.0 min coupon-cool floor"),
        ev(1800000.0, "rotor.T", 360.0, code="ROTOR_C", units="C"),
        ev(2940000.0, "cool.floor", 1.0, code="COOL_FLOOR", units="bool", note="1500 s + 1440 s = 2940 s = 24.0 min"),
        ev(3600000.0, "ops.condemn", 1.0, code="MACHINE_CONDEMN", units="bool", note="Copse: condemn the machine until day-shift"),
        ev(4200000.0, "gate.hold", 1.0, code="MODIFY", units="decision", note="companion t2: overlay rotor R-3; speed 0.70; machine condemn refused"),
        ev(4500000.0, "speed.set", 0.70, code="SPEED_PU", units="pu"),
        ev(4800000.0, "xrd.d", 200.12, code="D_PM", units="pm"),
        ev(5100000.0, "recon.s", 96.00, code="S_MPA", units="MPa", note="160000*0.0006=96.00; still over 70.00 so 0.70 holds"),
        ev(5400000.0, "braggveil.s", 17.60, code="VENDOR_MPA", units="MPa"),
        ev(5700000.0, "rotor.T", 340.0, code="ROTOR_C", units="C"),
        ev(6000000.0, "speed.held", 0.70, code="SPEED_HELD", units="pu"),
        ev(6300000.0, "machine.esd", 0.0, code="CONDEMN_NOT_TAKEN", units="bool"),
        ev(6600000.0, "recon.eps", 0.0006, code="STRAIN", units="1", note="96.00/160000=0.0006 identity still holds"),
        ev(6900000.0, "speed.held", 0.70, code="SPEED_HELD", units="pu"),
    ]
    assert_stream(events)

    traj = {
        "id": "nelb-r50-152-t1",
        "state": {
            "sim_or_real": "hil",
            "episode_id": "CF-XRD-2026-0722",
            "domain": "xrd_sin2psi_rotor_hoop",
            "setting": "Copsefell Compressor CF-5 (invented), LP rotor R-3 bore. Hardware-in-the-loop XRD coupon in Xrd-HIL-6 supplies the sin2psi lattice spacing that times the in-service keep-run stop. Plant-owned Co-Kalpha diffractometer. Braggveil vendor last-good cloud is the only OEM stress SoT. Not Zn-Ka/Cr-Ka XRF chemistry (r29/r34), not Fe-57 Mossbauer (r30), not Barkhausen remaining case (r35/r37), not RUS modulus (r24), not ultrasonic AE birefringence of a weld (r47 in-flight).",
            "observables_at_decision": {
                "d_psi_pm": 200.10,
                "d0_pm": 200.00,
                "sigma_mpa": 80.00,
                "sin2psi": 1.00,
                "braggveil_mpa": 18.00,
                "rotor_C": 412.0,
                "stop_floor_mpa": 70.00,
            },
            "margin_authority": "CF-5 XRD SOP rev A: if reconstructed sigma_mpa >= 70.00, refuse keep-run on this machine. A vendor last-good or a quiet rotor temperature cannot keep-run. Machine condemn is a different gate.",
        },
        "proposed_action": {
            "actor": "night compressor Ivo Copse, citing Braggveil 18.00 MPa and rotor 412 C under the 460 C alarm",
            "summary": "keep-run through the night; 200.10 pm is detector lag on a healthy coupon",
            "basis_claimed": "Braggveil is mid-range and a night condemn of a compressor is a restart measured in hours",
        },
        "safety_decision": {
            "decision": "REJECT",
            "rationale": "Keep-run is refused. Serialized reconstruction: strain = (d_psi - d0)/d0 = (200.10 - 200.00)/200.00 = 0.0005; k_E = E/(1+nu) = 200000/1.25 = 160000 MPa; sigma = k_E * strain / sin2psi = 160000 * 0.0005 / 1.00 = 80.00 MPa, over the 70.00 stop floor. Identity sigma * sin2psi / k_E = 0.0005. Braggveil 18.00 MPa is a different sensor with a frozen last-good and is not an admissible keep-run witness. Ordered: refuse keep-run now. Scope: this REJECT does not condemn the machine (that is the companion question) and does not isolate the lube pumps.",
            "threshold": "sigma_mpa>=70.00 => refuse keep-run; Braggveil is not SoT",
            "stated_residuals": "speed 0.70 still required to unload R-3; 80.00 MPa is a production cut; Braggveil remains the only OEM stress channel",
        },
        "executed_action": {
            "summary": "REJECT at t_s 1140: keep-run refused; Braggveil not SoT; reconstruction locked",
            "tool": "cf5-xrd-stop-gate-cli",
            "observation": "sigma 80.00 MPa recomputes from d_psi 200.10 pm and d0 200.00 pm; HIL coupon hashed; Braggveil channel not used as SoT",
        },
        "future_outcome": {
            "timeline": [
                {"t_s": 600.0, "event": "XRD d_psi 200.10 pm; raster frame; sigma 80.00 MPa"},
                {"t_s": 1080.0, "event": "ops proposes keep-run"},
                {"t_s": 1140.0, "event": "REJECT keep-run"},
                {"t_s": 1500.0, "event": "24 min coupon-cool bookend 1"},
                {"t_s": 2940.0, "event": "24.0 min floor"},
                {"t_s": 4200.0, "event": "companion MODIFY overlay R-3 plus speed 0.70 vs machine condemn"},
            ],
            "observed_effects": [
                "hoop stress recomputes from the serialized sin2psi model at every recon.s event",
                "a Braggveil-only head would have kept-run overnight",
                "24 min coupon-cool floor is in the stream (cool.start, cool.floor)",
            ],
            "surprises": [
                "a mid-range vendor last-good and a quiet rotor temperature co-existed with an 80.00 MPa XRD reconstruction",
            ],
            "new_state": {
                "cf5_speed_pu": 1.00,
                "keep_run": "blocked",
                "braggveil": "not SoT",
            },
            "latency_ms": 1860000.0,
        },
        "reward_components": reward(
            0.43,
            [
                ("sin2psi_reconstruction", 0.15),
                ("stop_floor_refuse", 0.12),
                ("vendor_bragg_nonsubstitution", 0.10),
                ("cool_floor_in_stream", 0.08),
                ("speed_cut_cost", -0.02),
            ],
            "scored for a keep-run REJECT on a recomputable XRD hoop stress while refusing a vendor dashboard; 24 min floor is priced as downtime not as a reason to wait",
        ),
        "meta": meta_common(
            tags=["REJECT", "xrd-sin2psi", "serialized-reconstruction", "hil", "operational-companion"],
            distillation_note="XRD stop gate: [E/(1+nu)]*((d-d0)/d0)/sin2psi reconstruction beats a green vendor stress dashboard; companion t2 is overlay plus speed 0.70, not a machine condemn",
        ),
    }
    traj2 = {
        "id": "nelb-r50-152-t2",
        "state": {
            "sim_or_real": "hil",
            "episode_id": "CF-XRD-2026-0722-overlay",
            "domain": "compressor_rotor_overlay_execution",
            "setting": "Same CF-5 after the keep-run REJECT. Night compressor proposes a machine condemn that would shut the frame until day-shift. This companion is the operational R-3 overlay plus speed 0.70 hold, not a second d-spacing vote.",
            "observables_at_decision": {
                "speed_pu": 0.70,
                "sigma_mpa": 96.00,
                "rotor_C": 340.0,
                "proposed": "machine_condemn",
            },
        },
        "proposed_action": {
            "actor": "night compressor Ivo Copse",
            "summary": "condemn the machine until day-shift; 24 min already paid",
            "basis_claimed": "the REJECT already refused keep-run, so a full condemn is the cheapest hold",
        },
        "safety_decision": {
            "decision": "MODIFY",
            "rationale": "Hold speed at 0.70 and overlay rotor R-3 only. Machine condemn at night is a restart measured in hours and does not unload the bore any faster than overlay plus 0.70. MODIFY the condemn into a 0.70 hold. Do not restore 1.00. Do not convert the hold into a personnel action on Copse. Post-hold 96.00 MPa is still over the 70.00 floor, so 0.70 holds until a new live frame clears 70.00 without the HIL coupon.",
            "threshold": "speed_pu==0.70 AND keep_run_not_restored AND machine_condemn_not_taken AND overlay_R3_only",
        },
        "executed_action": {
            "summary": "speed 0.70 at t_s 4200; machine condemn not latched; keep-run not restored; R-3 overlay armed",
            "tool": "cf5-rotor-overlay-exec",
            "observation": "sigma 96.00 MPa after hold; rotor 340 C; Braggveil still ignored",
        },
        "future_outcome": {
            "timeline": [
                {"t_s": 1500.0, "event": "coupon-cool clock started after REJECT"},
                {"t_s": 2940.0, "event": "24.0 min floor; rotor 360 then 340 C"},
                {"t_s": 3600.0, "event": "machine condemn proposed"},
                {"t_s": 4200.0, "event": "MODIFY overlay R-3 plus speed 0.70"},
            ],
            "observed_effects": [
                "machine-condemn restart cost is visible without waiting for a hung start",
                "hold did not reopen the stop-floor call",
            ],
            "new_state": {"speed_pu": 0.70, "keep_run": "blocked", "machine_condemn": "not taken", "r3": "overlay armed"},
            "latency_ms": 960000.0,
        },
        "reward_components": reward(
            0.34,
            [
                ("speed_hold", 0.12),
                ("no_machine_condemn", 0.11),
                ("no_keeprun_restore", 0.08),
                ("overlay_scope", 0.06),
                ("held_speed_cost", -0.03),
            ],
            "operational execution gate: overlay R-3 plus speed 0.70 because machine condemn does not unload faster; not an XRD re-vote",
        ),
        "meta": meta_common(tags=["MODIFY", "operational-execution", "rotor-overlay"]),
    }
    return {
        "id": "nelb-r50-152",
        "spike_events": events,
        "language_view": {
            "description": "Copsefell Compressor CF-5 HIL coupon pit. Plant-owned XRD reconstructs 80.00 MPa from 160000*0.0005/1.00 while Braggveil still shows 18.00 MPa and rotor 412 C. The gate REJECTS keep-run. A 24 min coupon-cool floor is serialized in the stream. Companion t2 MODIFYs a machine condemn into overlay of rotor R-3 plus speed 0.70.",
            "trajectory": traj,
            "trajectory_rotor_overlay_execution": traj2,
        },
        "bridge_notes": {
            "channel_map": {
                "xrd.d / xrd.psi / xrd.d0": "lattice spacing, tilt, unstrained d0; stress inputs",
                "recon.s / recon.eps": "serialized hoop stress MPa and strain identity",
                "braggveil.s / rotor.T / rotor.N / xrd.snr": "vendor last-good and rotor temperature/speed corridor",
                "ops.prop / gate.stop / ops.condemn / gate.hold": "keep-run proposal, REJECT, machine-condemn proposal, companion MODIFY",
                "cool.start / cool.floor / speed.set / speed.held": "operational companion channels plus the 24 min floor",
            },
            "temporal_motifs": [
                "vendor-quiet while XRD-loud: braggveil.s 18.00 next to recon.s 80.00",
                "reconstruction as event: recon.s 80.00 equals 160000*0.0005/1.00",
                "REJECT then operational MODIFY: gate.stop at 1140 s, gate.hold at 4200 s",
                "slow floor in-stream: cool.start 1500 s, cool.floor 2940 s (24.0 min)",
                "tight XRD pair: xrd.d then xrd.psi +1.2 ms at the raster frame",
            ],
            "language_to_spike_mapping": "'Braggveil is 18.00 MPa' = braggveil.s 18.00; '80.00 MPa hoop stress' = recon.s 80.00; 'refuse keep-run' = gate.stop REJECT; 'overlay not condemn' = gate.hold MODIFY",
            "why_high_value": "New XRD sin2psi family on a compressor rotor (not XRF r29/r34, not Mossbauer r30, not Barkhausen r35/r37, not RUS r24, not AE birefringence r47). Lead REJECT of keep-run on a recomputable hoop stress that a vendor dashboard would have cleared. Companion t2 is operational overlay hold. sim_or_real=hil on a spare coupon.",
            "encoder_spec": {
                "prng": "MT19937 via python random.Random",
                "seeds": {"raster": 20265052, "stream_note": "stream amplitudes are authored constants (pm, deg, MPa, C, rpm, pu, bool)"},
                "draw_order": "raster: per neuron id order, gap-constrained times, per-spike adaptation and noise",
                "thinning": "XRD goniometer exists at 0.5 Hz; stream keeps 4 d points; recon keeps 4 of ~20 solver ticks",
                "refractory_floors_ms": {
                    "xrd.d": 1.2,
                    "xrd.psi": 1.2,
                    "recon.s": 60000,
                    "rotor.N": 60000,
                    "braggveil.s": 60000,
                    "xrd.d0": 60000,
                    "rotor.T": 60000,
                    "recon.eps": 60000,
                    "xrd.snr": 60000,
                    "ops.prop": 60000,
                    "gate.stop": 60000,
                    "speed.hold": 60000,
                    "cool.start": 60000,
                    "cool.floor": 60000,
                    "ops.condemn": 60000,
                    "gate.hold": 60000,
                    "speed.set": 60000,
                    "speed.held": 60000,
                    "machine.esd": 60000,
                },
                "time_alias": "t_rel_ms; t0 = 2026-07-22T21:40:00Z HIL campaign start",
            },
            "distillation_targets": [
                "XRD reconstruction head: sigma = [E/(1+nu)] * ((d-d0)/d0) / sin2psi; strain identity",
                "stop-floor refuse vs keep-run vs machine condemn",
                "vendor-bragg nonsubstitution: a frozen last-good is not a keep-run witness",
                "operational companion: overlay R-3 plus speed 0.70 rather than a freeze-kill condemn of the machine",
            ],
        },
        "reconstruction_model": {
            "name": "xrd_sin2psi_hoop_stress",
            "formula": "strain=(d_psi_pm-d0_pm)/d0_pm; k_E=E_mpa/(1+nu); sigma_mpa=k_E*strain/sin2psi",
            "parameters": {
                "E_mpa": 200000.0,
                "nu": 0.25,
                "d0_pm": 200.00,
                "stop_floor_mpa": 70.00,
                "condemn_mpa": 200.00,
                "hold_speed_pu": 0.70,
                "cool_min": 24.0,
            },
            "worked_example": {"d_psi_pm": 200.10, "strain": 0.0005, "sigma_mpa": 80.00},
            "check": "(200.10-200.00)/200.00=0.0005; 200000/1.25=160000; 160000*0.0005/1.00=80.00 exactly; 1500 s + 1440 s = 2940 s = 24.0 min floor",
        },
        "raster": raster,
        "gate_snn": {
            "decision": "REJECT",
            "decision_window_ms": 28.0,
            "decision_window_s": 0.028,
            "code": "cf5.xrd_stop_gate",
            "note": "REJECT accumulator wins: XRD hoop-stress evidence overpowers the Braggveil continue advocate",
            "decode_rule": "reject-stop if stress_estimator AND tilt_norm fire; vendor_continue_advocate is below threshold by design",
            "populations": [
                gate_pop("stress_estimator", 100, 1.5, 50.0, w_s),
                gate_pop("tilt_norm", 40, 1.2, 50.0, w_s),
                gate_pop("vendor_continue_advocate", 32, 0.7, 25.0, w_s),
                gate_pop("reject_latch", 80, 1.8, 62.5, w_s),
            ],
        },
        "gate_compute": gate_compute(
            [
                {"check": "cf5.xrd_scorer", "neurons": 100, "mean_rate_hz": 50.0, "window_ms": 28.0},
                {"check": "cf5.stop_scorer", "neurons": 40, "mean_rate_hz": 50.0, "window_ms": 40.0},
            ]
        ),
        "meta": meta_common(
            id="nelb-r50-152",
            clock_domain="cf5-xrd-hil-relative-ms-t0-2026-07-22T21:40:00Z",
            tags=["xrd-sin2psi", "REJECT", "MODIFY", "hil", "operational-t2"],
        ),
    }


# ---------------------------------------------------------------------------
# Record 153 — FSM remaining wall of a subsea jumper
# simulated, ACCEPT / REJECT
# ---------------------------------------------------------------------------
def rec_153():
    k_v = 8.00
    I_ma = 24.00
    V_mv = 16.00
    t_mm = k_v * I_ma / V_mv
    _exact(t_mm, 12.00)
    _exact(k_v * I_ma / 12.00, 16.00)
    _exact(k_v * I_ma / 12.80, 15.00)
    _exact(k_v * I_ma / 19.20, 10.00)
    _exact(t_mm * V_mv / k_v, 24.00)
    _exact(20.00 - 12.00, 8.00)
    _exact(6600.0 + 900.0, 7500.0)

    raster = make_raster(
        neurons=16,
        mean_rate_hz=62.5,
        window_ms=40.0,
        seed=20265053,
        source="hd3.fsm.jumper",
        target="holmdock.isolate_core",
        table=[
            {"from": "fsm_V", "to": "wall_estimator", "weight": 1.40},
            {"from": "fsm_I", "to": "current_norm_core", "weight": 1.20},
            {"from": "fsmveil_t", "to": "vendor_continue_advocate", "weight": 0.35},
        ],
        third_factor={
            "modulator": "ach.wall_conflict",
            "tau_e_s": 2.2,
            "tau_e_ms": 2200.0,
            "eligibility": "pre-post coincidence on isolate synapses; the FSM modulator enables potentiation only while excitation current is co-active inside tau_e so a Fsmveil last-campaign corridor cannot hide a 12.00 mm remaining wall",
        },
        channel_prefix="fsm.n",
        anchor="HD-3 FSM 40 ms frame at V 16.00 mV / I 24.00 mA (t_s 3000) reconstructing 12.00 mm remaining wall below the 14.00 mm isolate floor",
    )
    w_s = 0.040
    events = [
        ev(0.0, "fsm.V", 12.00, code="V_MV", units="mV", note="simulated sealed jumper path; FSM remaining-wall voltage ratio, not DCPD crack depth, not MFL, not PEC, not RFEC, not EMAT SH, not TOFD"),
        ev(300000.0, "fsm.I", 24.00, code="I_MA", units="mA", note="matrix excitation current; t = k_v * I / V"),
        ev(600000.0, "recon.t", 16.00, code="T_MM", units="mm", note="8.00*24.00/12.00=16.00 exact"),
        ev(900000.0, "fsm.snr", 12.0, code="FSM_SNR", units="1"),
        ev(1200000.0, "fsmveil.t", 18.60, code="VENDOR_MM", units="mm", note="Fsmveil last-campaign cloud; not FSM voltage ratio"),
        ev(1800000.0, "fsm.V", 12.80, code="V_MV", units="mV"),
        ev(2100000.0, "recon.t", 15.00, code="T_MM", units="mm", note="8.00*24.00/12.80=15.00 exact"),
        ev(2400000.0, "seabed.T", 18.0, code="SEABED_C", units="C"),
        ev(2700000.0, "jumper.id", 7.0, code="J7", units="id"),
        ev(3000000.0, "fsm.V", 16.00, code="V_MV", units="mV", note="isolate-floor frame; raster sidecar"),
        ev(3000001.5, "fsm.I", 24.00, code="I_MA", units="mA", note="1.5 ms current-norm after voltage"),
        ev(3300000.0, "recon.t", 12.00, code="T_MM", units="mm", note="8.00*24.00/16.00=12.00 exact; isolate floor 14.00"),
        ev(3600000.0, "fsm.snr", 16.0, code="FSM_SNR", units="1"),
        ev(3900000.0, "fsmveil.t", 18.40, code="VENDOR_MM", units="mm"),
        ev(4200000.0, "seabed.T", 19.0, code="SEABED_C", units="C"),
        ev(4800000.0, "manifold.staged", 1.0, code="MANIFOLD_STAGED", units="bool", note="manifold M-1 staged; out of J-7 isolate scope"),
        ev(5100000.0, "ops.prop", 1.0, code="ISOLATE_AND_DUMP", units="bool", note="jumper captain Bram Quay: isolate J-7 and dump manifold M-1; 16.00 mV is a pin glitch"),
        ev(5400000.0, "gate.ovl", 1.0, code="ACCEPT", units="decision", note="bounded ACCEPT: jumper J-7 this night; manifold M-1 refused"),
        ev(6000000.0, "jumper.lock", 1.0, code="J7_ISOL", units="bool"),
        ev(6600000.0, "hold.start", 1.0, code="HOLD_START", units="bool", note="bookend 1 of the 15.0 min access-hold floor"),
        ev(7200000.0, "load.p", 16.0, code="LOAD_TPH", units="tph"),
        ev(7500000.0, "hold.floor", 1.0, code="HOLD_FLOOR", units="bool", note="6600 s + 900 s = 7500 s = 15.0 min"),
        ev(8100000.0, "ops.skip", 1.0, code="SKIP_ISOLATE", units="bool", note="Quay: Fsmveil 18.20 mm, skip J-7 isolate to save takt"),
        ev(8700000.0, "gate.hold", 1.0, code="REJECT", units="decision", note="companion t2: skip-isolate refused; Fsmveil is last-campaign"),
        ev(9300000.0, "recon.t", 10.00, code="T_MM", units="mm", note="post-hold sample; 8.00*24.00/19.20=10.00; still under 14.00"),
        ev(9900000.0, "fsmveil.t", 18.20, code="VENDOR_MM", units="mm"),
        ev(10500000.0, "fsm.snr", 15.0, code="FSM_SNR", units="1"),
        ev(11100000.0, "jumper.held", 1.0, code="J7_HELD", units="bool"),
        ev(11700000.0, "manifold.held", 1.0, code="MANIFOLD_HELD", units="bool"),
        ev(12300000.0, "j6.skip", 0.0, code="J6_NOT_THIS_GATE", units="bool", note="J-6 remains a different gate; skip of J-7 was refused, not executed"),
        ev(12900000.0, "seabed.T", 16.0, code="SEABED_C", units="C"),
        ev(14100000.0, "isolate.hold", 0.0, code="JUMPER_SCRAP", units="bool", note="12.00 vs 4.00 mm jumper-condemn floor; scrap not taken"),
    ]
    assert_stream(events)

    traj = {
        "id": "nelb-r50-153-t1",
        "state": {
            "sim_or_real": "simulated",
            "episode_id": "HD-FSM-2026-0816",
            "domain": "fsm_jumper_remaining_wall",
            "setting": "Holmdock Subsea HD-3 (invented), production jumper J-7. Simulated sealed field-signature-method remaining-wall cell on the jumper matrix. Seabed thermocouple and Fsmveil last-campaign cloud are corridor witnesses, not the wall SoT. Invented plant; simulated campaign. Not DCPD crack depth (r38), not MFL (r27/r28), not PEC coated riser (r36), not RFEC (r45 in-flight), not EMAT SH remaining wall (r49), not TOFD (r44), not PAUT TFM (r23).",
            "observables_at_decision": {
                "V_mv": 16.00,
                "I_ma": 24.00,
                "t_mm": 12.00,
                "fsm_snr": 16.0,
                "fsmveil_mm": 18.40,
                "isolate_floor_mm": 14.00,
            },
            "margin_authority": "HD-3 FSM SOP rev C: a jumper may isolate only if reconstructed t_mm <= 14.00 AND the authorization covers this jumper this night. A seabed TC or last-campaign corridor cannot substitute. Manifold M-1 plates are out of scope. Condemn (scrap the jumper) if t_mm <= 4.00.",
        },
        "proposed_action": {
            "actor": "jumper captain Bram Quay, citing seabed TC 19 C and Fsmveil 18.40 mm",
            "summary": "isolate J-7 and dump manifold M-1; 16.00 mV is a pin-coupling glitch",
            "basis_claimed": "last-campaign Fsmveil and the seabed TC are both consistent with 18.40 mm so the wall cannot be 12.00 mm",
        },
        "safety_decision": {
            "decision": "ACCEPT",
            "rationale": "This jumper is accepted, not the manifold and not J-6. Serialized reconstruction: t_mm = k_v * I_ma / V_mv = 8.00 * 24.00 / 16.00 = 12.00, which is 2.00 mm under the 14.00 isolate floor and 8.00 mm above the 4.00 jumper-condemn floor. Identity I = t * V / k_v = 12.00 * 16.00 / 8.00 = 24.00; metal-loss identity 20.00 - 12.00 = 8.00 mm. SOP rev C still forbids the manifold: ordered isolate of jumper J-7 this night only. Explicit scope: this accept does not cover manifold M-1 dump and does not authorize J-6/J-8 without a new voltage frame. Condemn tripwire: t_mm <= 4.00.",
            "threshold": "t_mm<=14.00 AND t_mm>4.00 AND jumper=J-7 AND manifold_not_dumped",
            "stated_residuals": "2.00 mm margin is not infinite; 8.00 mm/mV still carries pin fouling; seabed TC is not a remaining-wall witness",
        },
        "executed_action": {
            "summary": "ACCEPT at t_s 5400: J-7 isolate authorized; manifold held; reconstruction locked as SoT",
            "tool": "hd3-fsm-isolate-gate-cli",
            "observation": "t 12.00 mm recomputes from V 16.00 mV and I 24.00 mA; access hold staged; J-7 remains live as the condemn interlock",
        },
        "future_outcome": {
            "timeline": [
                {"t_s": 3000.0, "event": "FSM V 16.00 mV; raster frame; t 12.00 mm"},
                {"t_s": 5100.0, "event": "ops proposes J-7 isolate plus manifold dump"},
                {"t_s": 5400.0, "event": "ACCEPT bounded J-7 isolate; manifold refused"},
                {"t_s": 6600.0, "event": "companion hold start"},
                {"t_s": 7500.0, "event": "15.0 min hold floor"},
                {"t_s": 8700.0, "event": "companion REJECT skip-isolate of J-7"},
            ],
            "observed_effects": [
                "remaining wall recomputes from the serialized FSM model at every recon.t event",
                "a Fsmveil-only head would have skipped J-7 on an 18.40 mm corridor",
                "peak wear 12.00 mm stayed above the 4.00 mm jumper-condemn floor",
            ],
            "surprises": [
                "idle last-campaign 18.40 mm co-existed with a 12.00 mm FSM reconstruction",
            ],
            "new_state": {
                "hd3_j7": "authorized this night",
                "manifold": "held",
                "reconstruction_model": "discharged as an on-record calculator",
            },
            "latency_ms": 2400000.0,
        },
        "reward_components": reward(
            0.41,
            [
                ("fsm_wall_reconstruction", 0.14),
                ("bounded_j7_accept", 0.12),
                ("manifold_out_of_scope", 0.09),
                ("condemn_tripwire_armed", 0.08),
                ("held_manifold_takt_cost", -0.02),
            ],
            "scored for an earned ACCEPT of J-7 isolate on a recomputable FSM remaining wall while refusing a Fsmveil corridor plus manifold dump",
        ),
        "meta": meta_common(
            tags=["ACCEPT", "fsm-wall", "serialized-reconstruction", "operational-companion"],
            distillation_note="FSM jumper gate: k_v*I/V reconstruction beats a last-campaign corridor; companion t2 refuses skip-isolate rather than re-arguing remaining wall",
        ),
    }
    traj2 = {
        "id": "nelb-r50-153-t2",
        "state": {
            "sim_or_real": "simulated",
            "episode_id": "HD-FSM-2026-0816-hold",
            "domain": "jumper_skip_isolate_refusal",
            "setting": "Same HD-3 after the bounded ACCEPT. Jumper captain proposes skipping J-7 isolate on Fsmveil 18.20 mm to save takt. This companion is the operational skip refusal, not a second voltage vote.",
            "observables_at_decision": {
                "load_tph": 16.0,
                "t_mm": 12.00,
                "j7_authorized": 1,
                "proposed": "skip_isolate",
            },
        },
        "proposed_action": {
            "actor": "jumper captain Bram Quay",
            "summary": "skip J-7 isolate; Fsmveil still 18.20 mm and the 15 min hold already paid",
            "basis_claimed": "ACCEPT requirements for J-7 are fully specified so skipping the isolate is a takt gift",
        },
        "safety_decision": {
            "decision": "REJECT",
            "rationale": "Skip-isolate is refused. Fsmveil 18.20 mm is still last-campaign, not a new remaining-wall frame. The 15 min access hold paid the ROV, not the wall. REJECT the skip. Do not isolate J-6 on this gate. Do not scrap the jumper (12.00 vs 4.00 condemn). Hold J-7 as authorized.",
            "threshold": "j7_authorized AND skip_not_taken AND j6_not_this_gate AND jumper_not_scrapped",
        },
        "executed_action": {
            "summary": "skip-isolate refused at t_s 8700; J-7 remains authorized; manifold still held; jumper not scrapped",
            "tool": "hd3-isolate-hold-exec",
            "observation": "recon.t 10.00 mm after hold; Fsmveil still ignored; J-6 not opened",
        },
        "future_outcome": {
            "timeline": [
                {"t_s": 6600.0, "event": "hold clock started after ACCEPT"},
                {"t_s": 7500.0, "event": "15.0 min floor"},
                {"t_s": 8100.0, "event": "skip-isolate proposed"},
                {"t_s": 8700.0, "event": "REJECT skip-isolate of J-7"},
            ],
            "observed_effects": [
                "Fsmveil skip did not reopen the remaining-wall call",
                "condemn tripwire never fired; 12.00 vs 4.00 mm floor",
            ],
            "new_state": {"j7": "authorized", "skip": "blocked", "manifold": "held", "jumper": "in service"},
            "latency_ms": 1800000.0,
        },
        "reward_components": reward(
            0.36,
            [
                ("no_skip_isolate", 0.13),
                ("j7_hold", 0.10),
                ("no_jumper_scrap", 0.08),
                ("hold_complete", 0.07),
                ("held_takt_cost", -0.02),
            ],
            "operational execution gate: refuse skip because Fsmveil is not a wall license; not a voltage re-vote",
        ),
        "meta": meta_common(tags=["REJECT", "operational-execution", "isolate-hold"]),
    }
    return {
        "id": "nelb-r50-153",
        "spike_events": events,
        "language_view": {
            "description": "Holmdock Subsea HD-3 simulated cell. Plant-owned FSM reconstructs 12.00 mm remaining wall from 8.00*24.00/16.00 while Fsmveil still shows 18.40 mm and seabed TC 19 C. The gate ACCEPTs a bounded isolate of jumper J-7 only; manifold M-1 is out of scope. A 15 min access-hold floor is serialized in the stream. Companion t2 REJECTS skip-isolate.",
            "trajectory": traj,
            "trajectory_skip_isolate_refusal": traj2,
        },
        "bridge_notes": {
            "channel_map": {
                "fsm.V / fsm.I": "FSM matrix voltage and excitation current; remaining-wall inputs",
                "recon.t": "serialized remaining wall mm",
                "fsmveil.t / seabed.T / fsm.snr / jumper.id": "vendor last-campaign, seabed TC, lock SNR, jumper identity; the denial channels that look healthy",
                "ops.prop / gate.ovl / ops.skip / gate.hold": "isolate-plus-dump proposal, bounded ACCEPT, skip proposal, companion REJECT",
                "hold.start / hold.floor / jumper.lock / jumper.held / manifold.held": "operational companion channels plus the 15 min floor",
            },
            "temporal_motifs": [
                "vendor-thick while FSM-thin: fsmveil.t 18.40 next to recon.t 12.00",
                "reconstruction as event: recon.t 12.00 equals 8.00*24.00/16.00",
                "ACCEPT then operational REJECT: gate.ovl at 5400 s, gate.hold at 8700 s",
                "slow floor in-stream: hold.start 6600 s, hold.floor 7500 s (15.0 min)",
                "tight FSM pair: fsm.V then fsm.I +1.5 ms at the raster frame",
            ],
            "language_to_spike_mapping": "'Fsmveil is 18.40 mm' = fsmveil.t 18.40; '12.00 mm remaining wall' = recon.t 12.00; 'bounded isolate J-7' = gate.ovl ACCEPT; 'refuse skip' = gate.hold REJECT",
            "why_high_value": "New FSM remaining-wall family on a subsea jumper (not DCPD r38, not MFL r27/r28, not PEC r36, not RFEC r45, not EMAT SH r49, not TOFD r44, not PAUT r23). Lead ACCEPT of a bounded J-7 isolate on a recomputable wall that a last-campaign dashboard would have skipped. Companion t2 is operational skip refusal. sim_or_real=simulated.",
            "encoder_spec": {
                "prng": "MT19937 via python random.Random",
                "seeds": {"raster": 20265053, "stream_note": "stream amplitudes are authored constants (mV, mA, mm, C, SNR, tph, id, bool)"},
                "draw_order": "raster: per neuron id order, gap-constrained times, per-spike adaptation and noise",
                "thinning": "FSM matrix exists at 2 Hz; stream keeps 3 V points; recon keeps 4 of ~40 solver ticks",
                "refractory_floors_ms": {
                    "fsm.V": 1.5,
                    "fsm.I": 1.5,
                    "recon.t": 60000,
                    "fsm.snr": 60000,
                    "fsmveil.t": 60000,
                    "seabed.T": 60000,
                    "jumper.id": 60000,
                    "manifold.staged": 60000,
                    "ops.prop": 60000,
                    "gate.ovl": 60000,
                    "jumper.lock": 60000,
                    "hold.start": 60000,
                    "load.p": 60000,
                    "hold.floor": 60000,
                    "ops.skip": 60000,
                    "gate.hold": 60000,
                    "jumper.held": 60000,
                    "manifold.held": 60000,
                    "j6.skip": 60000,
                    "isolate.hold": 60000,
                },
                "time_alias": "t_rel_ms; t0 = 2026-08-16T04:20:00Z campaign start",
            },
            "distillation_targets": [
                "FSM reconstruction head: t_mm = k_v * I_ma / V_mv",
                "bounded isolate vs keep-night vs jumper-scrap",
                "vendor-campaign nonsubstitution: last-campaign envelope is not a skip-isolate witness",
                "operational companion: refuse skip without re-opening the remaining-wall call",
            ],
        },
        "reconstruction_model": {
            "name": "fsm_voltage_ratio_remaining_wall",
            "formula": "t_mm = k_v * I_ma / V_mv; I = t * V / k_v; loss_mm = t_nom - t",
            "parameters": {
                "k_v": 8.00,
                "t_nom_mm": 20.00,
                "isolate_floor_mm": 14.00,
                "condemn_mm": 4.00,
                "hold_min": 15.0,
            },
            "worked_example": {"V_mv": 16.00, "I_ma": 24.00, "t_mm": 12.00},
            "check": "8.00 * 24.00 / 16.00 = 12.00 exactly; 12.00*16.00/8.00=24.00; 20.00-12.00=8.00; 6600 s + 900 s = 7500 s = 15.0 min floor",
        },
        "raster": raster,
        "gate_snn": {
            "decision": "ACCEPT",
            "decision_window_ms": 40.0,
            "decision_window_s": 0.040,
            "code": "hd3.isolate_gate",
            "note": "ACCEPT accumulator wins: FSM remaining-wall evidence overpowers the Fsmveil continue advocate",
            "decode_rule": "accept if wall_estimator AND current_norm AND vessel_margin fire inside the window; vendor_continue_advocate is necessary-but-not-sufficient and cannot release the manifold",
            "populations": [
                gate_pop("wall_estimator", 80, 1.5, 50.0, w_s),
                gate_pop("current_norm", 64, 1.2, 31.25, w_s),
                gate_pop("vessel_margin", 40, 1.0, 50.0, w_s),
                gate_pop("vendor_continue_advocate", 32, 0.7, 25.0, w_s),
                gate_pop("accept_latch", 96, 1.8, 62.5, w_s),
            ],
        },
        "gate_compute": gate_compute(
            [
                {"check": "hd3.fsm_scorer", "neurons": 96, "mean_rate_hz": 50.0, "window_ms": 40.0},
                {"check": "hd3.wall_scorer", "neurons": 40, "mean_rate_hz": 62.5, "window_ms": 32.0},
            ]
        ),
        "meta": meta_common(
            id="nelb-r50-153",
            clock_domain="hd3-fsm-sim-relative-ms-t0-2026-08-16T04:20:00Z",
            tags=["fsm-wall", "ACCEPT", "REJECT", "serialized-reconstruction", "operational-t2"],
        ),
    }

# ---------------------------------------------------------------------------
# Record 153 — FBRM remaining chord-length of a crystallizer slurry
# simulated, ACCEPT / REJECT
# ---------------------------------------------------------------------------
def rec_153():
    k_v = 2.00
    dt_us = 6.00
    L_um = k_v * dt_us
    _exact(L_um, 12.00)
    _exact(k_v * 10.00, 20.00)
    _exact(k_v * 8.00, 16.00)
    _exact(k_v * 5.60, 11.20)
    _exact(L_um / k_v, 6.00)
    v_m_s = 2.00
    dt_s = 6.00e-6
    L_m = v_m_s * dt_s
    _exact(L_m, 12.00e-6)
    _exact(6600.0 + 900.0, 7500.0)

    raster = make_raster(
        neurons=16,
        mean_rate_hz=62.5,
        window_ms=40.0,
        seed=20265053,
        source="hf7.fbrm.slurry",
        target="heatherfen.isolate_core",
        table=[
            {"from": "fbrm_dt", "to": "chord_estimator", "weight": 1.40},
            {"from": "fbrm_v", "to": "scan_norm_core", "weight": 1.20},
            {"from": "chordveil_L", "to": "vendor_continue_advocate", "weight": 0.35},
        ],
        third_factor={
            "modulator": "ach.fines_conflict",
            "tau_e_s": 2.2,
            "tau_e_ms": 2200.0,
            "eligibility": "pre-post coincidence on isolate synapses; the FBRM modulator enables potentiation only while scan speed is co-active inside tau_e so a Chordveil last-campaign corridor cannot hide a 12.00 um fines chord",
        },
        channel_prefix="fbrm.n",
        anchor="HF-7 FBRM 40 ms frame at dt 6.00 us / v 2.00 um/us (t_s 3000) reconstructing 12.00 um remaining chord below the 14.00 um isolate floor",
    )
    w_s = 0.040
    events = [
        ev(0.0, "fbrm.dt", 10.00, code="DT_US", units="us", note="simulated sealed slurry cell; FBRM chord-length, not flow-cytometry, not PDA d32 atomizer, not QCM-D, not TEOM"),
        ev(300000.0, "fbrm.v", 2.00, code="V_UMUS", units="um_us", note="probe scan speed; L = k_v * dt"),
        ev(600000.0, "recon.L", 20.00, code="L_UM", units="um", note="2.00*10.00=20.00 exact"),
        ev(900000.0, "fbrm.snr", 12.0, code="FBRM_SNR", units="1"),
        ev(1200000.0, "chordveil.L", 48.20, code="VENDOR_UM", units="um", note="Chordveil last-campaign cloud; not FBRM pulse width"),
        ev(1800000.0, "fbrm.dt", 8.00, code="DT_US", units="us"),
        ev(2100000.0, "recon.L", 16.00, code="L_UM", units="um", note="2.00*8.00=16.00 exact"),
        ev(2400000.0, "jacket.T", 18.0, code="JACKET_C", units="C"),
        ev(2700000.0, "cryst.id", 2.0, code="C2", units="id"),
        ev(3000000.0, "fbrm.dt", 6.00, code="DT_US", units="us", note="isolate-floor frame; raster sidecar"),
        ev(3000001.5, "fbrm.v", 2.00, code="V_UMUS", units="um_us", note="1.5 ms scan-norm after pulse width"),
        ev(3300000.0, "recon.L", 12.00, code="L_UM", units="um", note="2.00*6.00=12.00 exact; isolate floor 14.00"),
        ev(3600000.0, "fbrm.snr", 16.0, code="FBRM_SNR", units="1"),
        ev(3900000.0, "chordveil.L", 48.00, code="VENDOR_UM", units="um"),
        ev(4200000.0, "jacket.T", 19.0, code="JACKET_C", units="C"),
        ev(4800000.0, "dryer.staged", 1.0, code="DRYER_STAGED", units="bool", note="dryer DR-1 staged; out of C-2 isolate scope"),
        ev(5100000.0, "ops.prop", 1.0, code="ISOLATE_AND_DUMP", units="bool", note="batch captain Mara Wold: isolate C-2 and dump dryer DR-1; 6.00 us is a window glitch"),
        ev(5400000.0, "gate.ovl", 1.0, code="ACCEPT", units="decision", note="bounded ACCEPT: crystallizer C-2 this night; dryer DR-1 refused"),
        ev(6000000.0, "cryst.lock", 1.0, code="C2_ISOL", units="bool"),
        ev(6600000.0, "hold.start", 1.0, code="HOLD_START", units="bool", note="bookend 1 of the 15.0 min access-hold floor"),
        ev(7200000.0, "load.p", 16.0, code="LOAD_TPH", units="tph"),
        ev(7500000.0, "hold.floor", 1.0, code="HOLD_FLOOR", units="bool", note="6600 s + 900 s = 7500 s = 15.0 min"),
        ev(8100000.0, "ops.skip", 1.0, code="SKIP_ISOLATE", units="bool", note="Wold: Chordveil 46.00 um, skip C-2 isolate to save takt"),
        ev(8700000.0, "gate.hold", 1.0, code="REJECT", units="decision", note="companion t2: skip-isolate refused; Chordveil is last-campaign"),
        ev(9300000.0, "recon.L", 11.20, code="L_UM", units="um", note="post-hold sample; 2.00*5.60=11.20; still under 14.00"),
        ev(9900000.0, "chordveil.L", 46.00, code="VENDOR_UM", units="um"),
        ev(10500000.0, "fbrm.snr", 15.0, code="FBRM_SNR", units="1"),
        ev(11100000.0, "cryst.held", 1.0, code="C2_HELD", units="bool"),
        ev(11700000.0, "dryer.held", 1.0, code="DRYER_HELD", units="bool"),
        ev(12300000.0, "c1.skip", 0.0, code="C1_NOT_THIS_GATE", units="bool", note="C-1 remains a different gate; skip of C-2 was refused, not executed"),
        ev(12900000.0, "jacket.T", 16.0, code="JACKET_C", units="C"),
        ev(14100000.0, "isolate.hold", 0.0, code="BATCH_SCRAP", units="bool", note="12.00 vs 4.00 um batch-condemn floor; waste scrap not taken"),
    ]
    assert_stream(events)

    traj = {
        "id": "nelb-r50-153-t1",
        "state": {
            "sim_or_real": "simulated",
            "episode_id": "HF-FBRM-2026-0816",
            "domain": "fbrm_crystallizer_chord_length",
            "setting": "Heatherfen Crystallizer HF-7 (invented), vessel C-2. Simulated sealed FBRM remaining-chord cell on the slurry. Jacket thermocouple and Chordveil last-campaign cloud are corridor witnesses, not the slurry SoT. Invented plant; simulated campaign. Not flow-cytometry cell streams (r12), not phase-Doppler d32 of an atomizer (r47 in-flight), not QCM-D fouling (r14), not TEOM baghouse PM (r46).",
            "observables_at_decision": {
                "dt_us": 6.00,
                "k_v": 2.00,
                "L_um": 12.00,
                "fbrm_snr": 16.0,
                "chordveil_um": 48.00,
                "isolate_floor_um": 14.00,
            },
            "margin_authority": "HF-7 FBRM SOP rev C: a crystallizer may isolate only if reconstructed L_um <= 14.00 AND the authorization covers this vessel this night. A jacket TC or last-campaign corridor cannot substitute. Dryer DR-1 plates are out of scope. Condemn (scrap the batch to waste) if L_um <= 4.00.",
        },
        "proposed_action": {
            "actor": "batch captain Mara Wold, citing jacket TC 19 C and Chordveil 48.00 um",
            "summary": "isolate C-2 and dump dryer DR-1; 6.00 us is a window-coupling glitch",
            "basis_claimed": "last-campaign Chordveil and the jacket TC are both consistent with 48 um so the slurry cannot be 12 um",
        },
        "safety_decision": {
            "decision": "ACCEPT",
            "rationale": "This crystallizer is accepted, not the dryer and not C-1. Serialized reconstruction: L_um = k_v * dt_us = 2.00 * 6.00 = 12.00, which is 2.00 um under the 14.00 isolate floor and 8.00 um above the 4.00 batch-condemn floor. Identity dt = L/k_v = 12.00/2.00 = 6.00; L_m = v * dt_s = 2.00 * 6.00e-6 = 12.00e-6 m. SOP rev C still forbids the dryer: ordered isolate of crystallizer C-2 this night only. Explicit scope: this accept does not cover dryer DR-1 dump and does not authorize C-1/C-3 without a new pulse frame. Condemn tripwire: L_um <= 4.00.",
            "threshold": "L_um<=14.00 AND L_um>4.00 AND vessel=C-2 AND dryer_not_dumped",
            "stated_residuals": "2.00 um margin is not infinite; 2.00 um/us still carries window fouling; jacket TC is not a chord-length witness",
        },
        "executed_action": {
            "summary": "ACCEPT at t_s 5400: C-2 isolate authorized; dryer held; reconstruction locked as SoT",
            "tool": "hf7-fbrm-isolate-gate-cli",
            "observation": "L 12.00 um recomputes from dt 6.00 us and k_v 2.00; access hold staged; C-2 remains live as the condemn interlock",
        },
        "future_outcome": {
            "timeline": [
                {"t_s": 3000.0, "event": "FBRM dt 6.00 us; raster frame; L 12.00 um"},
                {"t_s": 5100.0, "event": "ops proposes C-2 isolate plus dryer dump"},
                {"t_s": 5400.0, "event": "ACCEPT bounded C-2 isolate; dryer refused"},
                {"t_s": 6600.0, "event": "companion hold start"},
                {"t_s": 7500.0, "event": "15.0 min hold floor"},
                {"t_s": 8700.0, "event": "companion REJECT skip-isolate of C-2"},
            ],
            "observed_effects": [
                "remaining chord recomputes from the serialized FBRM model at every recon.L event",
                "a Chordveil-only head would have skipped C-2 on a 48 um corridor",
                "peak fines 12.00 um stayed above the 4.00 um batch-condemn floor",
            ],
            "surprises": [
                "idle last-campaign 48 um co-existed with a 12.00 um FBRM reconstruction",
            ],
            "new_state": {
                "hf7_c2": "authorized this night",
                "dryer": "held",
                "reconstruction_model": "discharged as an on-record calculator",
            },
            "latency_ms": 2400000.0,
        },
        "reward_components": reward(
            0.41,
            [
                ("fbrm_chord_reconstruction", 0.14),
                ("bounded_c2_accept", 0.12),
                ("dryer_out_of_scope", 0.09),
                ("condemn_tripwire_armed", 0.08),
                ("held_dryer_takt_cost", -0.02),
            ],
            "scored for an earned ACCEPT of C-2 isolate on a recomputable FBRM remaining chord while refusing a Chordveil corridor plus dryer dump",
        ),
        "meta": meta_common(
            tags=["ACCEPT", "fbrm-chord", "serialized-reconstruction", "operational-companion"],
            distillation_note="FBRM slurry gate: k_v*dt reconstruction beats a last-campaign corridor; companion t2 refuses skip-isolate rather than re-arguing chord length",
        ),
    }
    traj2 = {
        "id": "nelb-r50-153-t2",
        "state": {
            "sim_or_real": "simulated",
            "episode_id": "HF-FBRM-2026-0816-hold",
            "domain": "crystallizer_skip_isolate_refusal",
            "setting": "Same HF-7 after the bounded ACCEPT. Batch captain proposes skipping C-2 isolate on Chordveil 46.00 um to save takt. This companion is the operational skip refusal, not a second pulse-width vote.",
            "observables_at_decision": {
                "load_tph": 16.0,
                "L_um": 12.00,
                "c2_authorized": 1,
                "proposed": "skip_isolate",
            },
        },
        "proposed_action": {
            "actor": "batch captain Mara Wold",
            "summary": "skip C-2 isolate; Chordveil still 46.00 um and the 15 min hold already paid",
            "basis_claimed": "ACCEPT requirements for C-2 are fully specified so skipping the isolate is a takt gift",
        },
        "safety_decision": {
            "decision": "REJECT",
            "rationale": "Skip-isolate is refused. Chordveil 46.00 um is still last-campaign, not a new remaining-chord frame. The 15 min access hold paid the probe, not the chord. REJECT the skip. Do not isolate C-1 on this gate. Do not scrap the batch (12.00 vs 4.00 condemn). Hold C-2 as authorized.",
            "threshold": "c2_authorized AND skip_not_taken AND c1_not_this_gate AND batch_not_scrapped",
        },
        "executed_action": {
            "summary": "skip-isolate refused at t_s 8700; C-2 remains authorized; dryer still held; batch not scrapped",
            "tool": "hf7-isolate-hold-exec",
            "observation": "recon.L 11.20 um after hold; Chordveil still ignored; C-1 not opened",
        },
        "future_outcome": {
            "timeline": [
                {"t_s": 6600.0, "event": "hold clock started after ACCEPT"},
                {"t_s": 7500.0, "event": "15.0 min floor"},
                {"t_s": 8100.0, "event": "skip-isolate proposed"},
                {"t_s": 8700.0, "event": "REJECT skip-isolate of C-2"},
            ],
            "observed_effects": [
                "Chordveil skip did not reopen the remaining-chord call",
                "condemn tripwire never fired; 12.00 vs 4.00 um floor",
            ],
            "new_state": {"c2": "authorized", "skip": "blocked", "dryer": "held", "batch": "in service"},
            "latency_ms": 1800000.0,
        },
        "reward_components": reward(
            0.36,
            [
                ("no_skip_isolate", 0.13),
                ("c2_hold", 0.10),
                ("no_batch_scrap", 0.08),
                ("hold_complete", 0.07),
                ("held_takt_cost", -0.02),
            ],
            "operational execution gate: refuse skip because Chordveil is not a chord license; not a pulse re-vote",
        ),
        "meta": meta_common(tags=["REJECT", "operational-execution", "isolate-hold"]),
    }
    return {
        "id": "nelb-r50-153",
        "spike_events": events,
        "language_view": {
            "description": "Heatherfen Crystallizer HF-7 simulated cell. Plant-owned FBRM reconstructs 12.00 um remaining chord from 2.00*6.00 while Chordveil still shows 48.00 um and jacket TC 19 C. The gate ACCEPTs a bounded isolate of crystallizer C-2 only; dryer DR-1 is out of scope. A 15 min access-hold floor is serialized in the stream. Companion t2 REJECTS skip-isolate.",
            "trajectory": traj,
            "trajectory_skip_isolate_refusal": traj2,
        },
        "bridge_notes": {
            "channel_map": {
                "fbrm.dt / fbrm.v": "FBRM pulse width and scan speed; remaining-chord inputs",
                "recon.L": "serialized remaining chord um",
                "chordveil.L / jacket.T / fbrm.snr / cryst.id": "vendor last-campaign, jacket TC, lock SNR, vessel identity; the denial channels that look healthy",
                "ops.prop / gate.ovl / ops.skip / gate.hold": "isolate-plus-dump proposal, bounded ACCEPT, skip proposal, companion REJECT",
                "hold.start / hold.floor / cryst.lock / cryst.held / dryer.held": "operational companion channels plus the 15 min floor",
            },
            "temporal_motifs": [
                "vendor-coarse while FBRM-fine: chordveil.L 48.00 next to recon.L 12.00",
                "reconstruction as event: recon.L 12.00 equals 2.00*6.00",
                "ACCEPT then operational REJECT: gate.ovl at 5400 s, gate.hold at 8700 s",
                "slow floor in-stream: hold.start 6600 s, hold.floor 7500 s (15.0 min)",
                "tight FBRM pair: fbrm.dt then fbrm.v +1.5 ms at the raster frame",
            ],
            "language_to_spike_mapping": "'Chordveil is 48.00 um' = chordveil.L 48.00; '12.00 um remaining chord' = recon.L 12.00; 'bounded isolate C-2' = gate.ovl ACCEPT; 'refuse skip' = gate.hold REJECT",
            "why_high_value": "New FBRM remaining-chord family on a crystallizer slurry (not flow-cytometry r12, not PDA d32 r47, not QCM-D r14, not TEOM r46). Lead ACCEPT of a bounded C-2 isolate on a recomputable chord that a last-campaign dashboard would have skipped. Companion t2 is operational skip refusal. sim_or_real=simulated.",
            "encoder_spec": {
                "prng": "MT19937 via python random.Random",
                "seeds": {"raster": 20265053, "stream_note": "stream amplitudes are authored constants (us, um/us, um, C, SNR, tph, id, bool)"},
                "draw_order": "raster: per neuron id order, gap-constrained times, per-spike adaptation and noise",
                "thinning": "FBRM pulse train exists at 2 kHz; stream keeps 3 dt points; recon keeps 4 of ~40 solver ticks",
                "refractory_floors_ms": {
                    "fbrm.dt": 1.5,
                    "fbrm.v": 1.5,
                    "recon.L": 60000,
                    "fbrm.snr": 60000,
                    "chordveil.L": 60000,
                    "jacket.T": 60000,
                    "cryst.id": 60000,
                    "dryer.staged": 60000,
                    "ops.prop": 60000,
                    "gate.ovl": 60000,
                    "cryst.lock": 60000,
                    "hold.start": 60000,
                    "load.p": 60000,
                    "hold.floor": 60000,
                    "ops.skip": 60000,
                    "gate.hold": 60000,
                    "cryst.held": 60000,
                    "dryer.held": 60000,
                    "c1.skip": 60000,
                    "isolate.hold": 60000,
                },
                "time_alias": "t_rel_ms; t0 = 2026-08-16T04:20:00Z campaign start",
            },
            "distillation_targets": [
                "FBRM reconstruction head: L_um = k_v * dt_us",
                "bounded isolate vs keep-night vs batch-scrap",
                "vendor-campaign nonsubstitution: last-campaign envelope is not a skip-isolate witness",
                "operational companion: refuse skip without re-opening the remaining-chord call",
            ],
        },
        "reconstruction_model": {
            "name": "fbrm_scan_chord_length",
            "formula": "L_um = k_v * dt_us; L_m = v_m_s * dt_s; dt = L / k_v",
            "parameters": {
                "k_v": 2.00,
                "isolate_floor_um": 14.00,
                "condemn_um": 4.00,
                "hold_min": 15.0,
            },
            "worked_example": {"dt_us": 6.00, "L_um": 12.00},
            "check": "2.00 * 6.00 = 12.00 exactly; 12.00/2.00=6.00; 2.00*6.00e-6=12.00e-6 m; 6600 s + 900 s = 7500 s = 15.0 min floor",
        },
        "raster": raster,
        "gate_snn": {
            "decision": "ACCEPT",
            "decision_window_ms": 40.0,
            "decision_window_s": 0.040,
            "code": "hf7.isolate_gate",
            "note": "ACCEPT accumulator wins: FBRM remaining-chord evidence overpowers the Chordveil continue advocate",
            "decode_rule": "accept if chord_estimator AND scan_norm AND vessel_margin fire inside the window; vendor_continue_advocate is necessary-but-not-sufficient and cannot release the dryer",
            "populations": [
                gate_pop("chord_estimator", 80, 1.5, 50.0, w_s),
                gate_pop("scan_norm", 64, 1.2, 31.25, w_s),
                gate_pop("vessel_margin", 40, 1.0, 50.0, w_s),
                gate_pop("vendor_continue_advocate", 32, 0.7, 25.0, w_s),
                gate_pop("accept_latch", 96, 1.8, 62.5, w_s),
            ],
        },
        "gate_compute": gate_compute(
            [
                {"check": "hf7.fbrm_scorer", "neurons": 96, "mean_rate_hz": 50.0, "window_ms": 40.0},
                {"check": "hf7.chord_scorer", "neurons": 40, "mean_rate_hz": 62.5, "window_ms": 32.0},
            ]
        ),
        "meta": meta_common(
            id="nelb-r50-153",
            clock_domain="hf7-fbrm-sim-relative-ms-t0-2026-08-16T04:20:00Z",
            tags=["fbrm-chord", "ACCEPT", "REJECT", "serialized-reconstruction", "operational-t2"],
        ),
    }
