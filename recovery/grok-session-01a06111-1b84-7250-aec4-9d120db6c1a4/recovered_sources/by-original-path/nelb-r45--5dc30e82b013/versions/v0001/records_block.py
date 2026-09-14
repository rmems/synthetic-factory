def occupancy_preflight():
    banned = (
        "charkholt",
        "siltmere",
        "wickmere cooling",
        "phaseveil",
        "flashveil",
        "polarveil",
        "remote-field eddy",
        "remote field eddy",
        "laser-flash diffusivity",
        "laser flash diffusivity",
        "linear polarization resistance",
        "stern-geary i_corr",
        "tamsin wold",
        "lyle harbin",
        "edda pell",
    )
    hits = []
    root = Path("/tmp")
    for n in sorted(root.glob("nelb-r*/NOTES-r*.md")) + sorted(root.glob("nelb-r*/gen_r*.py")):
        if "nelb-r45" in str(n):
            continue
        text = n.read_text(encoding="utf-8", errors="replace").casefold()
        for b in banned:
            if b in text:
                hits.append(f"{n}:{b}")
    if hits:
        raise RuntimeError(f"family/plant collision {hits}")


# ---------------------------------------------------------------------------
# Record 136 — remote-field eddy current remaining wall of a boiler tube
# designed, MODIFY / ACCEPT
# ---------------------------------------------------------------------------
def rec_136():
    k_rf = 1.00
    sqrt_f = 4.00
    phi = 48.00
    d_mm = k_rf * phi / sqrt_f
    _exact(d_mm, 12.00)
    _exact(k_rf * 80.00 / sqrt_f, 20.00)
    _exact(k_rf * 64.00 / sqrt_f, 16.00)
    _exact(k_rf * 52.00 / sqrt_f, 13.00)
    _exact(phi, d_mm * sqrt_f / k_rf)
    _exact(16.00 ** 0.5, 4.00)
    _exact(6600.0 + 1080.0, 7680.0)

    raster = make_raster(
        neurons=20,
        mean_rate_hz=50.0,
        window_ms=36.0,
        seed=202645136,
        source="ch6.rfec.tube",
        target="charkholt.tube_isolate_core",
        table=[
            {"from": "rfec_phi", "to": "thickness_estimator", "weight": 1.40},
            {"from": "rfec_f", "to": "freq_norm_core", "weight": 1.20},
            {"from": "phaseveil_d", "to": "vendor_continue_advocate", "weight": 0.45},
        ],
        third_factor={
            "modulator": "na.tube_wall_salience",
            "tau_e_s": 1.6,
            "tau_e_ms": 1600.0,
            "eligibility": "pre-post coincidence on tube-isolate synapses; the RFEC modulator enables potentiation only while excitation frequency is co-active inside tau_e so a Phaseveil last-campaign corridor cannot hide a 12.00 mm remaining wall",
        },
        channel_prefix="rfec.n",
        anchor="CH-6 RFEC 36 ms frame at phi 48.00 deg / sqrt(f) 4.00 (t_s 3000) reconstructing 12.00 mm remaining wall below the 14.00 mm isolate floor",
    )
    w_s = 0.036
    events = [
        ev(0.0, "rfec.phi", 80.00, code="PHI_DEG", units="deg", note="plant-owned remote-field eddy current on CH-6 tube T-14; not PEC coated-riser, not ECT CFB/HDPE, not ECA FSW, not MFL, not DCPD"),
        ev(300000.0, "rfec.f", 16.00, code="F_KHZ", units="kHz", note="exciter frequency; d = k_rf * phi / sqrt(f)"),
        ev(600000.0, "recon.d", 20.00, code="D_MM", units="mm", note="1.00*80.00/4.00=20.00 exact"),
        ev(900000.0, "rfec.snr", 11.0, code="RFEC_SNR", units="1", note="early lock; isolate needs SNR>=14"),
        ev(1200000.0, "phaseveil.d", 19.60, code="VENDOR_MM", units="mm", note="Phaseveil last-campaign UT cloud; not admissible SoT"),
        ev(1500000.0, "rfec.coh", 0.91, code="COH", units="1"),
        ev(1800000.0, "rfec.phi", 64.00, code="PHI_DEG", units="deg"),
        ev(2100000.0, "recon.d", 16.00, code="D_MM", units="mm", note="1.00*64.00/4.00=16.00"),
        ev(2400000.0, "fire.pu", 1.00, code="FIRE_PU", units="pu"),
        ev(2700000.0, "tube.T", 412.0, code="C", units="C", note="metal temperature corridor; not a thickness license"),
        ev(3000000.0, "rfec.phi", 48.00, code="PHI_DEG", units="deg", note="isolate-floor frame; raster sidecar"),
        ev(3000001.5, "rfec.f", 16.00, code="F_KHZ", units="kHz", note="1.5 ms freq-norm after phase; same-channel not used"),
        ev(3300000.0, "recon.d", 12.00, code="D_MM", units="mm", note="1.00*48.00/4.00=12.00 exact; isolate floor 14.00"),
        ev(3600000.0, "rfec.snr", 18.0, code="RFEC_SNR", units="1", note="18.0 >= 14.0 lock floor"),
        ev(3900000.0, "phaseveil.d", 19.40, code="VENDOR_MM", units="mm"),
        ev(4200000.0, "egv.T", 388.0, code="EGV_C", units="C"),
        ev(4800000.0, "ops.prop", 1.0, code="KEEP_1_FIRE", units="bool", note="firing lead Tamsin Wold: keep 1.00 firing; 48 deg is a fill-factor wobble"),
        ev(5400000.0, "gate.isol", 1.0, code="MODIFY", units="decision", note="isolate tube T-14; derate firing to 0.80; 12.00 mm is under 14.00"),
        ev(6000000.0, "fire.set", 0.80, code="PU", units="pu"),
        ev(6300000.0, "tube.lock", 1.0, code="T14_ISOL", units="bool"),
        ev(6600000.0, "soak.start", 1.0, code="SOAK_START", units="bool", note="bookend 1 of the 18.0 min soak floor"),
        ev(7200000.0, "tube.T", 210.0, code="C", units="C"),
        ev(7680000.0, "soak.floor", 1.0, code="SOAK_FLOOR", units="bool", note="6600 s + 1080 s = 7680 s = 18.0 min"),
        ev(8400000.0, "ops.restore", 1.0, code="RESTORE_1_FIRE", units="bool", note="Wold: Phaseveil 19.20 mm, restore 1.00 firing"),
        ev(9600000.0, "gate.exec", 1.0, code="ACCEPT", units="decision", note="companion t2: hold 0.80; Phaseveil restore refused; bank condemn refused"),
        ev(10200000.0, "fire.held", 0.80, code="PU_HELD", units="pu"),
        ev(10800000.0, "phaseveil.d", 19.20, code="VENDOR_MM", units="mm"),
        ev(11400000.0, "recon.d", 13.00, code="D_MM", units="mm", note="post-isolate 52.00 deg; 1.00*52.00/4.00=13.00; still under 14.00"),
        ev(12000000.0, "rfec.snr", 16.5, code="RFEC_SNR", units="1"),
        ev(12600000.0, "tube.held", 1.0, code="T14_HELD", units="bool"),
        ev(13200000.0, "condemn.hold", 0.0, code="BANK_CONDEMN", units="bool", note="whole-bank condemn not taken; 12.00 vs 6.00 mm tripwire"),
        ev(13800000.0, "fire.held", 0.80, code="PU_HELD", units="pu"),
    ]
    assert_stream(events)

    traj = {
        "id": "nelb-r45-136-t1",
        "state": {
            "sim_or_real": "designed",
            "episode_id": "CH-RFEC-2026-0619",
            "domain": "rfec_boiler_tube_remaining",
            "setting": "Charkholt Boiler CH-6 (invented), convection-bank tube T-14. Plant-owned remote-field eddy current (exciter/pickup, 30D remote zone, k_rf=1.00) is the remaining-wall SoT. Phaseveil last-campaign UT cloud is a corridor witness, not the tube SoT. Invented plant; designed campaign. Not pulsed eddy current coated riser (r36), not electrical capacitance tomography CFB/HDPE (r20/r22), not eddy-current array FSW lift-off (r21), not MFL (r27/r28), not DCPD crack depth (r38).",
            "observables_at_decision": {
                "phi_deg": 48.00,
                "f_kHz": 16.00,
                "sqrt_f": 4.00,
                "d_mm": 12.00,
                "rfec_snr": 18.0,
                "phaseveil_mm": 19.40,
                "isolate_floor_mm": 14.00,
            },
            "margin_authority": "CH-6 RFEC SOP rev B: if reconstructed remaining wall mm <= 14.00 AND RFEC SNR >= 14.0, isolate this tube this night and derate firing to 0.80. A last-campaign corridor or a quiet metal TC cannot keep 1.00. Whole-bank condemn tripwire is 6.00 mm.",
        },
        "proposed_action": {
            "actor": "firing lead Tamsin Wold, citing Phaseveil 19.40 mm and tube metal 412 C",
            "summary": "keep 1.00 firing through the night; 48.00 deg is fill-factor wobble on a healthy tube",
            "basis_claimed": "Phaseveil last-campaign and tube metal temperature are both under the isolate story and EGV TC is in band",
        },
        "safety_decision": {
            "decision": "MODIFY",
            "rationale": "Keep-1.00 firing is refused. Serialized reconstruction: d_mm = k_rf * phi_deg / sqrt(f_kHz) = 1.00 * 48.00 / 4.00 = 12.00, which is 2.00 mm under the 14.00 isolate floor and 6.00 mm above the 6.00 mm whole-bank condemn tripwire. Identity phi = d * sqrt(f) / k_rf = 12.00 * 4.00 / 1.00 = 48.00. RFEC SNR 18.0 >= 14.0. Phaseveil 19.40 mm is a last-campaign envelope, not an admissible keep-1.00 witness. Ordered: isolate tube T-14 and derate firing to 0.80 now. Scope: this MODIFY does not condemn the bank (that is the companion question) and does not scrap the adjacent tubes.",
            "threshold": "d_mm<=14.00 AND rfec_snr>=14.0 => isolate this tube and derate firing to 0.80; Phaseveil is not SoT; condemn if d_mm<=6.00",
            "stated_residuals": "12.00 vs 6.00 condemn floor is 6.00 mm, not infinite; 0.80 is a firing cut; Phaseveil remains the only OEM last-campaign channel",
        },
        "executed_action": {
            "summary": "MODIFY at t_s 5400: T-14 isolated; firing 0.80; Phaseveil not SoT; reconstruction locked",
            "tool": "ch6-rfec-tube-gate-cli",
            "observation": "d 12.00 mm recomputes from phi 48.00 deg and sqrt(f) 4.00; RFEC head remains live as the condemn interlock",
        },
        "future_outcome": {
            "timeline": [
                {"t_s": 3000.0, "event": "RFEC phi 48.00 deg; raster frame; d 12.00 mm"},
                {"t_s": 4800.0, "event": "ops proposes keep 1.00 firing"},
                {"t_s": 5400.0, "event": "MODIFY isolate T-14; derate firing to 0.80"},
                {"t_s": 6600.0, "event": "18 min soak bookend 1"},
                {"t_s": 7680.0, "event": "18.0 min floor"},
                {"t_s": 9600.0, "event": "companion ACCEPT hold 0.80; restore refused"},
            ],
            "observed_effects": [
                "remaining wall recomputes from the serialized RFEC model at every recon.d event",
                "a Phaseveil-only head would have kept 1.00 firing overnight",
                "18 min soak floor is in the stream (soak.start, soak.floor)",
            ],
            "surprises": [
                "a mid-range last-campaign corridor and a quiet tube metal TC co-existed with a 12.00 mm RFEC reconstruction",
            ],
            "new_state": {
                "ch6_fire_pu": 0.80,
                "t14": "isolated",
                "phaseveil": "not SoT",
                "reconstruction_model": "discharged as an on-record calculator",
            },
            "latency_ms": 2400000.0,
        },
        "reward_components": reward(
            0.40,
            [
                ("rfec_phase_reconstruction", 0.14),
                ("isolate_floor_derate", 0.12),
                ("vendor_campaign_nonsubstitution", 0.10),
                ("soak_floor_in_stream", 0.08),
                ("derate_firing_cost", -0.04),
            ],
            "scored for a keep-1.00 MODIFY on a recomputable RFEC remaining wall while refusing a Phaseveil 19.40 mm corridor; 18 min floor is priced as downtime not as a reason to wait",
        ),
        "meta": meta_common(
            tags=["MODIFY", "rfec-wall", "serialized-reconstruction", "operational-companion"],
            distillation_note="RFEC remaining-wall gate: k*phi/sqrt(f) reconstruction beats a green last-campaign dashboard; companion t2 holds 0.80 rather than restoring on Phaseveil",
        ),
    }
    traj2 = {
        "id": "nelb-r45-136-t2",
        "state": {
            "sim_or_real": "designed",
            "episode_id": "CH-RFEC-2026-0619-exec",
            "domain": "boiler_firing_derate_execution",
            "setting": "Same CH-6 after the MODIFY. Firing lead proposes restoring 1.00 firing on Phaseveil 19.20 mm. This companion is the operational 0.80 hold, not a second delay vote.",
            "observables_at_decision": {
                "fire_pu": 0.80,
                "d_mm": 13.00,
                "phaseveil_mm": 19.20,
                "soak_floor_s": 1080.0,
            },
        },
        "proposed_action": {
            "actor": "firing lead Tamsin Wold",
            "summary": "restore 1.00 firing; 18 min already paid and Phaseveil is 19.20 mm",
            "basis_claimed": "the MODIFY already cut firing, so restoring on the OEM last-campaign is the cheapest hold",
        },
        "safety_decision": {
            "decision": "ACCEPT",
            "rationale": "Hold 0.80 firing. The soak floor is complete and the condemn tripwire (d_mm <= 6.00) is still armed on the plant RFEC head. ACCEPT the hold. Do not restore 1.00 on Phaseveil. Do not condemn the bank. 13.00 mm post-isolate is still the RFEC SoT until a new frame clears 14.00.",
            "threshold": "fire_pu==0.80 AND soak_floor_complete AND condemn_tripwire_armed AND restore_1pu_not_taken AND bank_not_condemned",
        },
        "executed_action": {
            "summary": "0.80 firing held at t_s 9600; Phaseveil restore not latched; bank not condemned",
            "tool": "ch6-fire-derate-exec",
            "observation": "recon.d 13.00 mm after isolate; tube 210 C; Phaseveil still ignored",
        },
        "future_outcome": {
            "timeline": [
                {"t_s": 6600.0, "event": "soak clock started after MODIFY"},
                {"t_s": 7680.0, "event": "18.0 min floor"},
                {"t_s": 8400.0, "event": "restore 1.00 firing proposed"},
                {"t_s": 9600.0, "event": "ACCEPT hold 0.80 firing"},
            ],
            "observed_effects": [
                "Phaseveil restore did not reopen the thickness call",
                "condemn tripwire never fired; 12.00 vs 6.00 mm floor",
            ],
            "new_state": {"fire_pu": 0.80, "restore_1pu": "blocked", "bank": "in service", "t14": "isolated"},
            "latency_ms": 1800000.0,
        },
        "reward_components": reward(
            0.35,
            [
                ("hold_0p80", 0.12),
                ("no_phaseveil_restore", 0.10),
                ("no_bank_condemn", 0.09),
                ("soak_complete", 0.06),
                ("held_firing_cost", -0.02),
            ],
            "operational execution gate: hold 0.80 because Phaseveil is not a restore license; not a delay re-vote",
        ),
        "meta": meta_common(tags=["ACCEPT", "operational-execution", "boiler-derate"]),
    }
    return {
        "id": "nelb-r45-136",
        "spike_events": events,
        "language_view": {
            "description": "Charkholt Boiler CH-6. Plant-owned remote-field eddy current reconstructs 12.00 mm remaining wall from 48.00 deg / sqrt(16.00 kHz)=4.00 while Phaseveil still shows 19.40 mm and tube metal 412 C. The gate MODIFYs tube T-14 isolate plus 0.80 firing. An 18 min soak floor is serialized in the stream. Companion t2 ACCEPTs the 0.80 hold and refuses a Phaseveil restore.",
            "trajectory": traj,
            "trajectory_tube_derate_execution": traj2,
        },
        "bridge_notes": {
            "channel_map": {
                "rfec.phi / rfec.f": "remote-field phase lag and exciter frequency; the physics channels the reconstruction consumes",
                "recon.d": "serialized remaining wall mm",
                "rfec.snr / rfec.coh / phaseveil.d / tube.T / egv.T / fire.pu": "lock SNR, coherence, vendor last-campaign, metal and EGV temperature, firing corridor; the denial channels that look healthy",
                "ops.prop / gate.isol / ops.restore / gate.exec": "keep-1.00 proposal, MODIFY isolate, restore proposal, companion ACCEPT",
                "fire.set / soak.start / soak.floor / fire.held / tube.held": "operational companion channels plus the 18 min floor",
            },
            "temporal_motifs": [
                "vendor-thick while RFEC-thin: phaseveil.d 19.40 next to recon.d 12.00",
                "reconstruction as event: recon.d 12.00 equals 1.00*48.00/4.00",
                "MODIFY then operational ACCEPT: gate.isol at 5400 s, gate.exec at 9600 s",
                "slow floor in-stream: soak.start 6600 s, soak.floor 7680 s (18.0 min)",
                "tight RFEC pair: rfec.phi then rfec.f +1.5 ms at the raster frame",
            ],
            "language_to_spike_mapping": "'Phaseveil is 19.40 mm' = phaseveil.d 19.40; '12.00 mm remaining wall' = recon.d 12.00; 'isolate this tube' = gate.isol MODIFY; 'hold 0.80 not restore' = gate.exec ACCEPT",
            "why_high_value": "New remote-field-eddy-current family on a coal-fired boiler tube (not PEC r36, not ECT r20/r22, not ECA r21, not MFL r27/r28, not DCPD r38). Lead MODIFY of keep-1.00 firing on a recomputable remaining thickness that a last-campaign dashboard would have cleared. Companion t2 is operational 0.80 hold. sim_or_real=designed.",
            "encoder_spec": {
                "prng": "MT19937 via python random.Random",
                "seeds": {"raster": 202645136, "stream_note": "stream amplitudes are authored constants (deg, kHz, mm, SNR, C, pu, bool)"},
                "draw_order": "raster: per neuron id order, gap-constrained times, per-spike adaptation and noise",
                "thinning": "RFEC phase exists at 40 Hz; stream keeps 3 phi points; recon keeps 4 of ~40 solver ticks",
                "refractory_floors_ms": {
                    "rfec.phi": 1.5,
                    "rfec.f": 1.5,
                    "recon.d": 60000,
                    "rfec.snr": 60000,
                    "rfec.coh": 60000,
                    "phaseveil.d": 60000,
                    "fire.pu": 60000,
                    "tube.T": 60000,
                    "egv.T": 60000,
                    "ops.prop": 60000,
                    "gate.isol": 60000,
                    "fire.set": 60000,
                    "tube.lock": 60000,
                    "soak.start": 60000,
                    "soak.floor": 60000,
                    "ops.restore": 60000,
                    "gate.exec": 60000,
                    "fire.held": 60000,
                    "tube.held": 60000,
                    "condemn.hold": 60000,
                },
                "time_alias": "t_rel_ms; t0 = 2026-06-19T03:20:00Z campaign start",
            },
            "distillation_targets": [
                "RFEC reconstruction head: d_mm = k_rf * phi_deg / sqrt(f_kHz)",
                "isolate-floor derate vs keep-whole vs bank-condemn",
                "vendor-campaign nonsubstitution: last-campaign envelope is not a keep-1.00 witness",
                "operational companion: hold 0.80 without restoring on Phaseveil",
            ],
        },
        "reconstruction_model": {
            "name": "rfec_phase_remaining_wall",
            "formula": "d_mm = k_rf * phi_deg / sqrt(f_kHz); equivalently phi_deg = d_mm * sqrt(f_kHz) / k_rf",
            "parameters": {
                "k_rf": 1.00,
                "f_kHz": 16.00,
                "sqrt_f": 4.00,
                "isolate_floor_mm": 14.00,
                "condemn_mm": 6.00,
                "derate_pu": 0.80,
                "soak_min": 18.0,
                "snr_lock": 14.0,
            },
            "worked_example": {"phi_deg": 48.00, "d_mm": 12.00},
            "check": "1.00 * 48.00 / 4.00 = 12.00 exactly; 12.00 * 4.00 / 1.00 = 48.00; 6600 s + 1080 s = 7680 s = 18.0 min floor",
        },
        "raster": raster,
        "gate_snn": {
            "decision": "MODIFY",
            "decision_window_ms": 36.0,
            "decision_window_s": 0.036,
            "code": "ch6.rfec_tube_gate",
            "note": "MODIFY accumulator wins: RFEC remaining-wall evidence overpowers the Phaseveil continue advocate",
            "decode_rule": "modify-isolate if thickness_estimator AND freq_norm fire; vendor_continue_advocate is below threshold by design",
            "populations": [
                gate_pop("thickness_estimator", 80, 1.5, 50.0, w_s),
                gate_pop("freq_norm", 64, 1.2, 31.25, w_s),
                gate_pop("vendor_continue_advocate", 32, 0.7, 25.0, w_s),
                gate_pop("modify_latch", 80, 1.7, 62.5, w_s),
            ],
        },
        "gate_compute": gate_compute(
            [
                {"check": "ch6.rfec_scorer", "neurons": 80, "mean_rate_hz": 50.0, "window_ms": 36.0},
                {"check": "ch6.isolate_scorer", "neurons": 40, "mean_rate_hz": 50.0, "window_ms": 32.0},
            ]
        ),
        "meta": meta_common(
            id="nelb-r45-136",
            clock_domain="ch6-rfec-campaign-relative-ms-t0-2026-06-19T03:20:00Z",
            tags=["rfec-wall", "MODIFY", "ACCEPT", "serialized-reconstruction", "operational-t2"],
        ),
    }


# ---------------------------------------------------------------------------
# Record 137 — laser-flash Parker diffusivity of a SiC HEX tile, hil,
# REJECT / MODIFY
# ---------------------------------------------------------------------------
def rec_137():
    k_p = 0.140
    l_mm = 10.00
    t_half = 7.00
    alpha = k_p * (l_mm ** 2) / t_half
    _exact(alpha, 2.00)
    _exact(k_p * 100.00 / 3.50, 4.00)
    _exact(k_p * 100.00 / 5.00, 2.80)
    _exact(k_p * 100.00 / 8.00, 1.75)
    rho = 3.20
    cp = 0.625
    k_th = alpha * rho * cp
    _exact(k_th, 4.00)
    _exact(2.00 * 3.20 * 0.625, 4.00)
    _exact(1500.0 + 1440.0, 2940.0)

    raster = make_raster(
        neurons=25,
        mean_rate_hz=50.0,
        window_ms=28.0,
        seed=202645137,
        source="sm7.flash.tile",
        target="siltmere.tile_stop_core",
        table=[
            {"from": "flash_t", "to": "diffusivity_estimator", "weight": 1.35},
            {"from": "flash_L", "to": "thickness_norm_core", "weight": 1.25},
            {"from": "flashveil_a", "to": "vendor_continue_advocate", "weight": 0.40},
        ],
        third_factor={
            "modulator": "da.diffusivity_error",
            "tau_e_s": 1.1,
            "tau_e_ms": 1100.0,
            "eligibility": "pre-post coincidence on keep-kiln synapses; the laser-flash modulator depresses keep-100 links when half-rise time stays long inside tau_e of a thickness-norm sample",
        },
        channel_prefix="flash.n",
        anchor="SM-7 HIL coupon 28 ms frame at t_half 7.00 ms / L 10.00 mm (t_s 600) reconstructing 2.00 mm2/s below the 2.40 stop floor",
    )
    w_s = 0.028
    events = [
        ev(0.0, "flash.t", 3.50, code="T_HALF_MS", units="ms", note="HIL laser-flash coupon in Flash-HIL-5; plant-owned Parker rear-face, not lock-in thermography, not acoustic pyrometry, not Johnson noise, not OCT TBC"),
        ev(30000.0, "flash.L", 10.00, code="L_MM", units="mm", note="tile thickness; alpha = k_p L^2 / t_half"),
        ev(60000.0, "recon.a", 4.00, code="ALPHA", units="mm2_s", note="0.140*100.00/3.50=4.00 exact"),
        ev(180000.0, "kiln.T", 1180.0, code="KILN_C", units="C", note="kiln temperature corridor"),
        ev(240000.0, "flashveil.a", 4.30, code="VENDOR_A", units="mm2_s", note="Flashveil last-good diffusivity cloud; the only OEM alpha SoT"),
        ev(360000.0, "flash.t", 5.00, code="T_HALF_MS", units="ms"),
        ev(420000.0, "recon.a", 2.80, code="ALPHA", units="mm2_s", note="0.140*100.00/5.00=2.80"),
        ev(480000.0, "flash.rho", 3.20, code="RHO", units="g_cm3", note="lumped density for k_th identity"),
        ev(600000.0, "flash.t", 7.00, code="T_HALF_MS", units="ms", note="stop-floor frame; raster sidecar"),
        ev(600001.2, "flash.L", 10.00, code="L_MM", units="mm", note="1.2 ms thickness-norm after half-rise"),
        ev(720000.0, "recon.a", 2.00, code="ALPHA", units="mm2_s", note="0.140*100.00/7.00=2.00 exact; stop floor 2.40"),
        ev(780000.0, "tile.T", 42.0, code="TILE_C", units="C"),
        ev(840000.0, "flashveil.a", 4.20, code="VENDOR_A", units="mm2_s"),
        ev(960000.0, "recon.k", 4.00, code="K_TH", units="W_mK", note="2.00*3.20*0.625=4.00"),
        ev(1020000.0, "flash.cp", 0.625, code="CP", units="J_gK"),
        ev(1080000.0, "ops.prop", 1.0, code="KEEP_100", units="bool", note="night tech Lyle Harbin: keep-100 kiln; Flashveil 4.20 and kiln 1180 C"),
        ev(1140000.0, "gate.stop", 1.0, code="REJECT", units="decision", note="stop keep-100; 2.00 mm2/s is under 2.40; Flashveil not SoT"),
        ev(1200000.0, "kiln.hold", 1.00, code="KILN_PU", units="pu", note="kiln still 1.00 pending companion 0.70"),
        ev(1500000.0, "cool.start", 1.0, code="COOL_START", units="bool", note="bookend 1 of the 24.0 min cooldown floor"),
        ev(1800000.0, "kiln.T", 940.0, code="KILN_C", units="C"),
        ev(2940000.0, "cool.floor", 1.0, code="COOL_FLOOR", units="bool", note="1500 s + 1440 s = 2940 s = 24.0 min"),
        ev(3600000.0, "ops.dump", 1.0, code="KILN_DUMP", units="bool", note="Harbin: dump the kiln until day-shift"),
        ev(4200000.0, "gate.hold", 1.0, code="MODIFY", units="decision", note="companion t2: isolate tile C-4; kiln 0.70; kiln dump refused"),
        ev(4500000.0, "kiln.set", 0.70, code="KILN_PU", units="pu"),
        ev(4800000.0, "flash.t", 8.00, code="T_HALF_MS", units="ms"),
        ev(5100000.0, "recon.a", 1.75, code="ALPHA", units="mm2_s", note="0.140*100.00/8.00=1.75; still under 2.40 after isolate arming"),
        ev(5400000.0, "flashveil.a", 4.10, code="VENDOR_A", units="mm2_s"),
        ev(5700000.0, "tile.T", 38.0, code="TILE_C", units="C"),
        ev(6000000.0, "kiln.held", 0.70, code="KILN_HELD", units="pu"),
        ev(6300000.0, "kiln.esd", 0.0, code="DUMP_NOT_TAKEN", units="bool"),
        ev(6600000.0, "recon.k", 3.50, code="K_TH", units="W_mK", note="1.75*3.20*0.625=3.50"),
        ev(6900000.0, "kiln.held", 0.70, code="KILN_HELD", units="pu"),
    ]
    assert_stream(events)

    traj = {
        "id": "nelb-r45-137-t1",
        "state": {
            "sim_or_real": "hil",
            "episode_id": "SM-FLASH-2026-0723",
            "domain": "laser_flash_hex_tile",
            "setting": "Siltmere Ceramics SM-7 (invented), SiC heat-exchanger tile C-4. Hardware-in-the-loop laser-flash coupon in Flash-HIL-5 supplies the Parker half-rise that times the in-service keep-100 stop. Plant-owned rear-face IR. Flashveil vendor last-good diffusivity cloud is the only OEM alpha SoT. Not lock-in thermography CFRP (r23), not acoustic pyrometry (r25), not Johnson-noise thermometry (r28), not spectral-domain OCT TBC (r38), not phosphor-lifetime metal temperature (r39 in-flight).",
            "observables_at_decision": {
                "t_half_ms": 7.00,
                "L_mm": 10.00,
                "alpha_mm2_s": 2.00,
                "k_p": 0.140,
                "flashveil_a": 4.20,
                "kiln_C": 1180.0,
                "stop_floor_a": 2.40,
                "k_th": 4.00,
            },
            "margin_authority": "SM-7 laser-flash SOP rev A: if reconstructed alpha_mm2_s <= 2.40, refuse keep-100 firing on this kiln. A vendor last-good or a quiet kiln temperature cannot keep-100. Kiln dump is a different gate.",
        },
        "proposed_action": {
            "actor": "night tech Lyle Harbin, citing Flashveil 4.20 mm2/s and kiln 1180 C under the 1250 C alarm",
            "summary": "keep-100 kiln through the night; 7.00 ms is rear-face convection on a healthy tile",
            "basis_claimed": "Flashveil is mid-range and a night dump of a SiC kiln is a restart measured in hours",
        },
        "safety_decision": {
            "decision": "REJECT",
            "rationale": "Keep-100 kiln is refused. Serialized reconstruction: alpha = k_p * L^2 / t_half = 0.140 * 10.00^2 / 7.00 = 2.00, under the 2.40 mm2/s stop floor. Identity k_th = alpha * rho * Cp = 2.00 * 3.20 * 0.625 = 4.00. Flashveil 4.20 is a different sensor with a frozen last-good and is not an admissible keep-100 witness. Ordered: refuse keep-100 now. Scope: this REJECT does not dump the kiln (that is the companion question) and does not isolate the burner train.",
            "threshold": "alpha<=2.40 => refuse keep-100; Flashveil is not SoT",
            "stated_residuals": "kiln 0.70 still required to unload the tile; 2.00 mm2/s is a production cut; Flashveil remains the only OEM diffusivity channel",
        },
        "executed_action": {
            "summary": "REJECT at t_s 1140: keep-100 refused; Flashveil not SoT; reconstruction locked",
            "tool": "sm7-flash-stop-gate-cli",
            "observation": "alpha 2.00 mm2/s recomputes from t_half 7.00 ms and L 10.00 mm; HIL coupon hashed; Flashveil channel not used as SoT",
        },
        "future_outcome": {
            "timeline": [
                {"t_s": 600.0, "event": "laser-flash t_half 7.00 ms; raster frame; alpha 2.00"},
                {"t_s": 1080.0, "event": "ops proposes keep-100 kiln"},
                {"t_s": 1140.0, "event": "REJECT keep-100"},
                {"t_s": 1500.0, "event": "24 min cooldown bookend 1"},
                {"t_s": 2940.0, "event": "24.0 min floor"},
                {"t_s": 4200.0, "event": "companion MODIFY isolate C-4 plus kiln 0.70 vs kiln dump"},
            ],
            "observed_effects": [
                "diffusivity recomputes from the serialized Parker model at every recon.a event",
                "a Flashveil-only head would have kept-100 overnight",
                "24 min cooldown floor is in the stream (cool.start, cool.floor)",
            ],
            "surprises": [
                "a mid-range vendor last-good and a quiet kiln temperature co-existed with a 2.00 mm2/s Parker reconstruction",
            ],
            "new_state": {
                "sm7_kiln_pu": 1.00,
                "keep_100": "blocked",
                "flashveil": "not SoT",
            },
            "latency_ms": 1860000.0,
        },
        "reward_components": reward(
            0.43,
            [
                ("parker_reconstruction", 0.15),
                ("stop_floor_refuse", 0.12),
                ("vendor_alpha_nonsubstitution", 0.10),
                ("cool_floor_in_stream", 0.08),
                ("kiln_cut_cost", -0.02),
            ],
            "scored for a keep-100 REJECT on a recomputable laser-flash diffusivity while refusing a vendor alpha dashboard; 24 min floor is priced as downtime not as a reason to wait",
        ),
        "meta": meta_common(
            tags=["REJECT", "laser-flash", "serialized-reconstruction", "hil", "operational-companion"],
            distillation_note="laser-flash stop gate: k_p*L^2/t_half reconstruction beats a green vendor dashboard; companion t2 is isolate plus kiln 0.70, not a kiln dump",
        ),
    }
    traj2 = {
        "id": "nelb-r45-137-t2",
        "state": {
            "sim_or_real": "hil",
            "episode_id": "SM-FLASH-2026-0723-isolate",
            "domain": "hex_tile_isolate_execution",
            "setting": "Same SM-7 after the keep-100 REJECT. Night tech proposes a kiln dump that would shut the HEX until day-shift. This companion is the operational C-4 isolate plus kiln 0.70 hold, not a second half-rise vote.",
            "observables_at_decision": {
                "kiln_pu": 0.70,
                "alpha_mm2_s": 1.75,
                "tile_C": 38.0,
                "proposed": "kiln_dump",
            },
        },
        "proposed_action": {
            "actor": "night tech Lyle Harbin",
            "summary": "dump the kiln until day-shift; 24 min already paid",
            "basis_claimed": "the REJECT already refused keep-100, so a full dump is the cheapest hold",
        },
        "safety_decision": {
            "decision": "MODIFY",
            "rationale": "Hold kiln at 0.70 and isolate tile C-4 only. Kiln dump at night is a restart measured in hours and does not unload the tile any faster than isolate plus 0.70. MODIFY the dump into a 0.70 hold. Do not restore 1.00. Do not convert the hold into a personnel action on Harbin. Post-hold 1.75 mm2/s is still under the 2.40 floor after isolate arming, but 0.70 holds until a new live frame clears 2.40 without the HIL coupon.",
            "threshold": "kiln_pu==0.70 AND keep_100_not_restored AND kiln_dump_not_taken AND isolate_C4_only",
        },
        "executed_action": {
            "summary": "kiln 0.70 at t_s 4200; kiln dump not latched; keep-100 not restored; C-4 isolate armed",
            "tool": "sm7-tile-isolate-exec",
            "observation": "alpha 1.75 mm2/s after hold; tile 38 C; Flashveil still ignored",
        },
        "future_outcome": {
            "timeline": [
                {"t_s": 1500.0, "event": "cooldown clock started after REJECT"},
                {"t_s": 2940.0, "event": "24.0 min floor; kiln 940 then tile 38 C"},
                {"t_s": 3600.0, "event": "kiln dump proposed"},
                {"t_s": 4200.0, "event": "MODIFY isolate C-4 plus kiln 0.70"},
            ],
            "observed_effects": [
                "kiln-dump restart cost is visible without waiting for a hung start",
                "hold did not reopen the stop-floor call",
            ],
            "new_state": {"kiln_pu": 0.70, "keep_100": "blocked", "kiln_dump": "not taken", "c4": "isolate armed"},
            "latency_ms": 960000.0,
        },
        "reward_components": reward(
            0.34,
            [
                ("isolate_tile_not_dump", 0.12),
                ("kiln_0p70", 0.10),
                ("no_personnel_action", 0.08),
                ("hold_complete", 0.06),
                ("held_kiln_cost", -0.02),
            ],
            "operational execution gate: isolate C-4 plus kiln 0.70 because Flashveil is not a dump license; not a half-rise re-vote",
        ),
        "meta": meta_common(tags=["MODIFY", "operational-execution", "tile-isolate"]),
    }
    return {
        "id": "nelb-r45-137",
        "spike_events": events,
        "language_view": {
            "description": "Siltmere Ceramics SM-7 HIL coupon. Plant-owned laser-flash reconstructs 2.00 mm2/s from 0.140*10.00^2/7.00 while Flashveil still shows 4.20 and kiln 1180 C. The gate REJECTs keep-100. A 24 min cooldown floor is serialized in the stream. Companion t2 MODIFYs a kiln dump into isolate C-4 plus kiln 0.70.",
            "trajectory": traj,
            "trajectory_tile_isolate_execution": traj2,
        },
        "bridge_notes": {
            "channel_map": {
                "flash.t / flash.L": "Parker half-rise and tile thickness; the physics channels the reconstruction consumes",
                "recon.a / recon.k": "serialized diffusivity and thermal-conductivity identity",
                "flashveil.a / kiln.T / tile.T / flash.rho / flash.cp": "vendor last-good, kiln and coupon temperature, density and heat capacity; the denial channels that look healthy",
                "ops.prop / gate.stop / ops.dump / gate.hold": "keep-100 proposal, REJECT stop, dump proposal, companion MODIFY",
                "kiln.hold / cool.start / cool.floor / kiln.set / kiln.held": "operational companion channels plus the 24 min floor",
            },
            "temporal_motifs": [
                "vendor-high while Parker-low: flashveil.a 4.20 next to recon.a 2.00",
                "reconstruction as event: recon.a 2.00 equals 0.140*100.00/7.00",
                "REJECT then operational MODIFY: gate.stop at 1140 s, gate.hold at 4200 s",
                "slow floor in-stream: cool.start 1500 s, cool.floor 2940 s (24.0 min)",
                "tight flash pair: flash.t then flash.L +1.2 ms at the raster frame",
            ],
            "language_to_spike_mapping": "'Flashveil is 4.20' = flashveil.a 4.20; '2.00 mm2/s' = recon.a 2.00; 'refuse keep-100' = gate.stop REJECT; 'isolate C-4 plus 0.70' = gate.hold MODIFY",
            "why_high_value": "New laser-flash Parker family on a SiC HEX tile (not lock-in thermography r23, not acoustic pyrometry r25, not Johnson noise r28, not OCT TBC r38, not phosphor-lifetime r39). Lead REJECT of keep-100 on a recomputable diffusivity that a last-good dashboard would have cleared. Companion t2 is operational isolate plus 0.70, not a kiln dump. sim_or_real=hil.",
            "encoder_spec": {
                "prng": "MT19937 via python random.Random",
                "seeds": {"raster": 202645137, "stream_note": "stream amplitudes are authored constants (ms, mm, mm2/s, C, pu, bool)"},
                "draw_order": "raster: per neuron id order, gap-constrained times, per-spike adaptation and noise",
                "thinning": "laser-flash trace exists at 1 kHz; stream keeps 4 t_half points; recon keeps 4 of ~40 solver ticks",
                "refractory_floors_ms": {
                    "flash.t": 1.2,
                    "flash.L": 1.2,
                    "recon.a": 60000,
                    "kiln.T": 60000,
                    "flashveil.a": 60000,
                    "flash.rho": 60000,
                    "tile.T": 60000,
                    "recon.k": 60000,
                    "flash.cp": 60000,
                    "ops.prop": 60000,
                    "gate.stop": 60000,
                    "kiln.hold": 60000,
                    "cool.start": 60000,
                    "cool.floor": 60000,
                    "ops.dump": 60000,
                    "gate.hold": 60000,
                    "kiln.set": 60000,
                    "kiln.held": 60000,
                    "kiln.esd": 60000,
                },
                "time_alias": "t_rel_ms; t0 = 2026-07-23T21:50:00Z HIL campaign start",
            },
            "distillation_targets": [
                "Parker reconstruction head: alpha = k_p * L^2 / t_half; k_th = alpha * rho * Cp identity",
                "stop-floor refuse vs keep-100 vs kiln dump",
                "vendor-alpha nonsubstitution: a frozen last-good is not a keep-100 witness",
                "operational companion: isolate C-4 plus kiln 0.70 rather than a freeze-kill dump of the kiln",
            ],
        },
        "reconstruction_model": {
            "name": "laser_flash_parker_diffusivity",
            "formula": "alpha_mm2_s = k_p * L_mm^2 / t_half_ms; k_th = alpha * rho * Cp",
            "parameters": {
                "k_p": 0.140,
                "L_mm": 10.00,
                "rho": 3.20,
                "Cp": 0.625,
                "stop_floor_a": 2.40,
                "hold_kiln_pu": 0.70,
                "cool_min": 24.0,
            },
            "worked_example": {"t_half_ms": 7.00, "alpha_mm2_s": 2.00, "k_th": 4.00},
            "check": "0.140*100.00/7.00 = 2.00 exactly; 2.00*3.20*0.625 = 4.00; 1500 s + 1440 s = 2940 s = 24.0 min floor",
        },
        "raster": raster,
        "gate_snn": {
            "decision": "REJECT",
            "decision_window_ms": 28.0,
            "decision_window_s": 0.028,
            "code": "sm7.flash_stop_gate",
            "note": "REJECT accumulator wins: laser-flash diffusivity evidence overpowers the Flashveil continue advocate",
            "decode_rule": "reject-stop if diffusivity_estimator AND thickness_norm fire; vendor_continue_advocate is below threshold by design",
            "populations": [
                gate_pop("diffusivity_estimator", 100, 1.5, 50.0, w_s),
                gate_pop("thickness_norm", 40, 1.2, 50.0, w_s),
                gate_pop("vendor_continue_advocate", 32, 0.7, 25.0, w_s),
                gate_pop("reject_latch", 80, 1.8, 62.5, w_s),
            ],
        },
        "gate_compute": gate_compute(
            [
                {"check": "sm7.flash_scorer", "neurons": 100, "mean_rate_hz": 50.0, "window_ms": 28.0},
                {"check": "sm7.stop_scorer", "neurons": 40, "mean_rate_hz": 50.0, "window_ms": 40.0},
            ]
        ),
        "meta": meta_common(
            id="nelb-r45-137",
            clock_domain="sm7-flash-hil-relative-ms-t0-2026-07-23T21:50:00Z",
            tags=["laser-flash", "REJECT", "MODIFY", "hil", "operational-t2"],
        ),
    }


# ---------------------------------------------------------------------------
# Record 138 — linear-polarization-resistance corrosion rate of a CW header
# simulated, ACCEPT / REJECT
# ---------------------------------------------------------------------------
def rec_138():
    dE = 16.00
    dI = 2.00
    rp = dE / dI
    _exact(rp, 8.00)
    b_sg = 24.00
    icorr = b_sg / rp
    _exact(icorr, 3.00)
    k_i = 4.00
    cr = k_i * icorr
    _exact(cr, 12.00)
    k_cr = 96.00
    _exact(k_cr / rp, 12.00)
    _exact(dE / 0.50, 32.00)
    _exact(k_cr / 32.00, 3.00)
    _exact(dE / 1.00, 16.00)
    _exact(k_cr / 16.00, 6.00)
    _exact(dE / 1.60, 10.00)
    _exact(k_cr / 10.00, 9.60)
    _exact(6600.0 + 900.0, 7500.0)

    raster = make_raster(
        neurons=16,
        mean_rate_hz=62.5,
        window_ms=40.0,
        seed=202645138,
        source="wm8.lpr.header",
        target="wickmere.isolate_core",
        table=[
            {"from": "lpr_dE", "to": "rp_estimator", "weight": 1.40},
            {"from": "lpr_dI", "to": "current_norm_core", "weight": 1.20},
            {"from": "polarveil_cr", "to": "vendor_continue_advocate", "weight": 0.35},
        ],
        third_factor={
            "modulator": "ach.corrosion_rate_conflict",
            "tau_e_s": 2.2,
            "tau_e_ms": 2200.0,
            "eligibility": "pre-post coincidence on isolate synapses; the LPR modulator enables potentiation only while dI is co-active inside tau_e so a Polarveil last-good corridor cannot hide a 12.00 mm/y corrosion rate",
        },
        channel_prefix="lpr.n",
        anchor="WM-8 LPR 40 ms frame at dE 16.00 mV / dI 2.00 uA (t_s 3000) reconstructing 12.00 mm/y above the 8.00 isolate floor",
    )
    w_s = 0.040
    events = [
        ev(0.0, "lpr.dE", 16.00, code="DE_MV", units="mV", note="simulated sealed coupon loop; linear polarization resistance, not electrochemical-noise CUI, not hydrogen permeation, not SPR cyanide"),
        ev(300000.0, "lpr.dI", 0.50, code="DI_UA", units="uA", note="perturbation current; Rp = dE / dI"),
        ev(600000.0, "recon.Rp", 32.00, code="RP_KOHM", units="kOhm", note="16.00/0.50=32.00 exact"),
        ev(900000.0, "recon.CR", 3.00, code="CR_MMPY", units="mm_y", note="96.00/32.00=3.00"),
        ev(1200000.0, "polarveil.CR", 1.30, code="VENDOR_CR", units="mm_y", note="Polarveil last-good coupon cloud; not LPR"),
        ev(1800000.0, "lpr.dI", 1.00, code="DI_UA", units="uA"),
        ev(2100000.0, "recon.Rp", 16.00, code="RP_KOHM", units="kOhm", note="16.00/1.00=16.00 exact"),
        ev(2400000.0, "recon.CR", 6.00, code="CR_MMPY", units="mm_y", note="96.00/16.00=6.00"),
        ev(2700000.0, "hdr.T", 38.0, code="HDR_C", units="C"),
        ev(3000000.0, "lpr.dE", 16.00, code="DE_MV", units="mV", note="isolate-floor frame; raster sidecar"),
        ev(3000001.5, "lpr.dI", 2.00, code="DI_UA", units="uA", note="1.5 ms current-norm after dE"),
        ev(3300000.0, "recon.Rp", 8.00, code="RP_KOHM", units="kOhm", note="16.00/2.00=8.00 exact"),
        ev(3600000.0, "recon.icorr", 3.00, code="ICORR_UA", units="uA", note="24.00/8.00=3.00 Stern-Geary"),
        ev(3900000.0, "recon.CR", 12.00, code="CR_MMPY", units="mm_y", note="4.00*3.00=12.00; 96.00/8.00=12.00; isolate floor 8.00"),
        ev(4200000.0, "lpr.snr", 16.0, code="LPR_SNR", units="1"),
        ev(4500000.0, "polarveil.CR", 1.20, code="VENDOR_CR", units="mm_y"),
        ev(4800000.0, "basin.staged", 1.0, code="BASIN_STAGED", units="bool", note="cooling-tower basin staged; out of H-3 isolate scope"),
        ev(5100000.0, "ops.prop", 1.0, code="ISOLATE_AND_DUMP", units="bool", note="chemist Edda Pell: isolate H-3 and dump the basin; 2.00 uA is a coupon glitch"),
        ev(5400000.0, "gate.iso", 1.0, code="ACCEPT", units="decision", note="bounded ACCEPT: header H-3 this shift; basin dump refused"),
        ev(6000000.0, "hdr.lock", 1.0, code="H3_ISO", units="bool"),
        ev(6600000.0, "hold.start", 1.0, code="HOLD_START", units="bool", note="bookend 1 of the 15.0 min access-hold floor"),
        ev(7200000.0, "hdr.T", 36.0, code="HDR_C", units="C"),
        ev(7500000.0, "hold.floor", 1.0, code="HOLD_FLOOR", units="bool", note="6600 s + 900 s = 7500 s = 15.0 min"),
        ev(8100000.0, "ops.skip", 1.0, code="SKIP_ISOLATE", units="bool", note="Pell: Polarveil 1.10 mm/y, skip H-3 isolate to save takt"),
        ev(8700000.0, "gate.hold", 1.0, code="REJECT", units="decision", note="companion t2: skip-isolate refused; Polarveil is last-good"),
        ev(9300000.0, "recon.CR", 9.60, code="CR_MMPY", units="mm_y", note="post-hold dI 1.60; 96.00/10.00=9.60; still over 8.00"),
        ev(9900000.0, "polarveil.CR", 1.10, code="VENDOR_CR", units="mm_y"),
        ev(10500000.0, "lpr.snr", 15.0, code="LPR_SNR", units="1"),
        ev(11100000.0, "hdr.held", 1.0, code="H3_HELD", units="bool"),
        ev(11700000.0, "basin.held", 1.0, code="BASIN_HELD", units="bool"),
        ev(12300000.0, "h2.skip", 0.0, code="H2_NOT_THIS_GATE", units="bool", note="H-2 remains a different gate; skip of H-3 was refused, not executed"),
        ev(12900000.0, "hdr.T", 34.0, code="HDR_C", units="C"),
    ]
    assert_stream(events)

    traj = {
        "id": "nelb-r45-138-t1",
        "state": {
            "sim_or_real": "simulated",
            "episode_id": "WM-LPR-2026-0817",
            "domain": "lpr_cooling_header",
            "setting": "Wickmere Cooling WM-8 (invented), circulating-water header H-3. Simulated sealed LPR coupon loop on the header ID. Header thermocouple and Polarveil last-good coupon cloud are corridor witnesses, not the corrosion-rate SoT. Invented plant; simulated campaign. Not electrochemical-noise CUI (r23), not hydrogen permeation Devanathan (r33), not Kretschmann SPR cyanide (r26), not vibrating-wire viscometer (r26).",
            "observables_at_decision": {
                "dE_mV": 16.00,
                "dI_uA": 2.00,
                "Rp_kOhm": 8.00,
                "i_corr_uA": 3.00,
                "CR_mmpy": 12.00,
                "lpr_snr": 16.0,
                "polarveil_mmpy": 1.20,
                "isolate_floor_mmpy": 8.00,
            },
            "margin_authority": "WM-8 LPR SOP rev C: a header may isolate only if reconstructed CR_mmpy >= 8.00 AND the authorization covers this header this shift. A header TC or last-good corridor cannot substitute. Cooling-tower basin dump is out of scope. Scrap the header if CR_mmpy >= 24.00.",
        },
        "proposed_action": {
            "actor": "chemist Edda Pell, citing Polarveil 1.20 mm/y and header 38 C",
            "summary": "isolate H-3 and dump the basin; 2.00 uA is a coupon glitch on a healthy header",
            "basis_claimed": "Polarveil last-good and header temperature are both under the isolate story and the basin is already staged",
        },
        "safety_decision": {
            "decision": "ACCEPT",
            "rationale": "Bounded isolate of header H-3 this shift is accepted. Serialized reconstruction: Rp = dE/dI = 16.00/2.00 = 8.00 kOhm; i_corr = B/Rp = 24.00/8.00 = 3.00 uA; CR = k_i * i_corr = 4.00*3.00 = 12.00 mm/y, equivalently CR = k_cr/Rp = 96.00/8.00 = 12.00, which is 4.00 mm/y over the 8.00 isolate floor and 12.00 mm/y under the 24.00 scrap tripwire. LPR SNR 16.0 >= 14.0. Polarveil 1.20 mm/y is a last-good envelope, not an admissible skip-isolate witness. Basin dump is out of scope. Ordered: isolate H-3 only. Scope: this ACCEPT does not dump the basin and does not scrap the header.",
            "threshold": "CR_mmpy>=8.00 AND lpr_snr>=14.0 => isolate this header this shift; Polarveil is not SoT; basin dump out of scope; scrap if CR>=24.00",
            "stated_residuals": "12.00 vs 24.00 scrap floor is 12.00 mm/y, not infinite; isolate is a takt cut; Polarveil remains the only OEM coupon channel",
        },
        "executed_action": {
            "summary": "ACCEPT at t_s 5400: H-3 isolated; basin not dumped; Polarveil not SoT; reconstruction locked",
            "tool": "wm8-lpr-header-gate-cli",
            "observation": "CR 12.00 mm/y recomputes from dE 16.00 mV and dI 2.00 uA; LPR head remains live as the scrap interlock",
        },
        "future_outcome": {
            "timeline": [
                {"t_s": 3000.0, "event": "LPR dI 2.00 uA; raster frame; CR 12.00 mm/y"},
                {"t_s": 5100.0, "event": "ops proposes isolate plus basin dump"},
                {"t_s": 5400.0, "event": "ACCEPT isolate H-3 only; basin refused"},
                {"t_s": 6600.0, "event": "15 min hold bookend 1"},
                {"t_s": 7500.0, "event": "15.0 min floor"},
                {"t_s": 8700.0, "event": "companion REJECT skip-isolate"},
            ],
            "observed_effects": [
                "corrosion rate recomputes from the serialized LPR model at every recon.CR event",
                "a Polarveil-only head would have skipped isolate overnight",
                "15 min hold floor is in the stream (hold.start, hold.floor)",
            ],
            "surprises": [
                "a mid-range last-good corridor and a quiet header TC co-existed with a 12.00 mm/y LPR reconstruction",
            ],
            "new_state": {
                "h3": "isolated",
                "basin": "held",
                "polarveil": "not SoT",
                "reconstruction_model": "discharged as an on-record calculator",
            },
            "latency_ms": 2400000.0,
        },
        "reward_components": reward(
            0.41,
            [
                ("lpr_reconstruction", 0.14),
                ("bounded_h3_isolate", 0.12),
                ("basin_out_of_scope", 0.09),
                ("hold_floor_in_stream", 0.08),
                ("isolate_takt_cost", -0.02),
            ],
            "scored for a bounded ACCEPT of H-3 isolate on a recomputable LPR corrosion rate while refusing a Polarveil 1.20 mm/y corridor and a basin dump; 15 min floor is priced as downtime not as a reason to wait",
        ),
        "meta": meta_common(
            tags=["ACCEPT", "lpr-corrosion", "serialized-reconstruction", "operational-companion"],
            distillation_note="LPR isolate gate: dE/dI plus Stern-Geary reconstruction beats a green last-good dashboard; companion t2 refuses skip rather than dumping the basin",
        ),
    }
    traj2 = {
        "id": "nelb-r45-138-t2",
        "state": {
            "sim_or_real": "simulated",
            "episode_id": "WM-LPR-2026-0817-hold",
            "domain": "header_isolate_hold_execution",
            "setting": "Same WM-8 after the bounded ACCEPT. Chemist proposes skipping the H-3 isolate on Polarveil 1.10 mm/y to save takt. This companion is the operational skip refusal, not a second Rp vote.",
            "observables_at_decision": {
                "h3": "isolated",
                "CR_mmpy": 9.60,
                "polarveil_mmpy": 1.10,
                "hold_floor_s": 900.0,
            },
        },
        "proposed_action": {
            "actor": "chemist Edda Pell",
            "summary": "skip H-3 isolate; 15 min already paid and Polarveil is 1.10 mm/y",
            "basis_claimed": "the ACCEPT already named H-3, so skipping on the OEM last-good is the cheapest hold",
        },
        "safety_decision": {
            "decision": "REJECT",
            "rationale": "Hold the H-3 isolate. The hold floor is complete and the scrap tripwire (CR >= 24.00) is still armed on the plant LPR head. REJECT the skip. Do not restore the header on Polarveil. Do not dump the basin. 9.60 mm/y post-hold is still the LPR SoT until a new frame clears 8.00.",
            "threshold": "h3_isolated AND hold_floor_complete AND scrap_tripwire_armed AND skip_not_taken AND basin_not_dumped",
        },
        "executed_action": {
            "summary": "H-3 isolate held at t_s 8700; Polarveil skip not latched; basin not dumped",
            "tool": "wm8-header-isolate-exec",
            "observation": "recon.CR 9.60 mm/y after isolate; header 36 C; Polarveil still ignored",
        },
        "future_outcome": {
            "timeline": [
                {"t_s": 6600.0, "event": "hold clock started after ACCEPT"},
                {"t_s": 7500.0, "event": "15.0 min floor"},
                {"t_s": 8100.0, "event": "skip-isolate proposed"},
                {"t_s": 8700.0, "event": "REJECT skip-isolate of H-3"},
            ],
            "observed_effects": [
                "Polarveil skip did not reopen the corrosion-rate call",
                "scrap tripwire never fired; 12.00 vs 24.00 mm/y floor",
            ],
            "new_state": {"h3": "isolated", "skip": "blocked", "basin": "held", "header": "in service"},
            "latency_ms": 1800000.0,
        },
        "reward_components": reward(
            0.36,
            [
                ("no_skip_isolate", 0.13),
                ("h3_hold", 0.10),
                ("no_header_scrap", 0.08),
                ("hold_complete", 0.07),
                ("held_takt_cost", -0.02),
            ],
            "operational execution gate: refuse skip because Polarveil is not a corrosion-rate license; not an Rp re-vote",
        ),
        "meta": meta_common(tags=["REJECT", "operational-execution", "isolate-hold"]),
    }
    return {
        "id": "nelb-r45-138",
        "spike_events": events,
        "language_view": {
            "description": "Wickmere Cooling WM-8 simulated coupon loop. Plant-owned linear polarization resistance reconstructs 12.00 mm/y from 16.00/2.00 kOhm and Stern-Geary 24.00/8.00 while Polarveil still shows 1.20 mm/y and header 38 C. The gate ACCEPTs a bounded isolate of header H-3 only; the cooling-tower basin is out of scope. A 15 min access-hold floor is serialized in the stream. Companion t2 REJECTS skip-isolate.",
            "trajectory": traj,
            "trajectory_skip_isolate_refusal": traj2,
        },
        "bridge_notes": {
            "channel_map": {
                "lpr.dE / lpr.dI": "polarization voltage and current; Rp inputs",
                "recon.Rp / recon.icorr / recon.CR": "serialized resistance, Stern-Geary current, corrosion rate",
                "polarveil.CR / hdr.T / lpr.snr / basin.staged": "vendor last-good, header TC, lock SNR, basin identity; the denial channels that look healthy",
                "ops.prop / gate.iso / ops.skip / gate.hold": "isolate-plus-dump proposal, bounded ACCEPT, skip proposal, companion REJECT",
                "hold.start / hold.floor / hdr.lock / hdr.held / basin.held": "operational companion channels plus the 15 min floor",
            },
            "temporal_motifs": [
                "vendor-low while LPR-high: polarveil.CR 1.20 next to recon.CR 12.00",
                "reconstruction as event: recon.CR 12.00 equals 96.00/8.00 and 4.00*3.00",
                "ACCEPT then operational REJECT: gate.iso at 5400 s, gate.hold at 8700 s",
                "slow floor in-stream: hold.start 6600 s, hold.floor 7500 s (15.0 min)",
                "tight LPR pair: lpr.dE then lpr.dI +1.5 ms at the raster frame",
            ],
            "language_to_spike_mapping": "'Polarveil is 1.20 mm/y' = polarveil.CR 1.20; '12.00 mm/y' = recon.CR 12.00; 'bounded isolate H-3' = gate.iso ACCEPT; 'refuse skip' = gate.hold REJECT",
            "why_high_value": "New linear-polarization-resistance family on a circulating-water header (not EN CUI r23, not hydrogen permeation r33, not SPR r26). Lead ACCEPT of a bounded H-3 isolate on a recomputable corrosion rate that a last-good dashboard would have skipped. Companion t2 is operational skip refusal. sim_or_real=simulated.",
            "encoder_spec": {
                "prng": "MT19937 via python random.Random",
                "seeds": {"raster": 202645138, "stream_note": "stream amplitudes are authored constants (mV, uA, kOhm, mm/y, C, SNR, bool)"},
                "draw_order": "raster: per neuron id order, gap-constrained times, per-spike adaptation and noise",
                "thinning": "LPR sweep exists at 1 Hz; stream keeps 3 dI points; recon keeps 4 of ~40 solver ticks",
                "refractory_floors_ms": {
                    "lpr.dE": 1.5,
                    "lpr.dI": 1.5,
                    "recon.Rp": 60000,
                    "recon.CR": 60000,
                    "polarveil.CR": 60000,
                    "hdr.T": 60000,
                    "recon.icorr": 60000,
                    "lpr.snr": 60000,
                    "basin.staged": 60000,
                    "ops.prop": 60000,
                    "gate.iso": 60000,
                    "hdr.lock": 60000,
                    "hold.start": 60000,
                    "hold.floor": 60000,
                    "ops.skip": 60000,
                    "gate.hold": 60000,
                    "hdr.held": 60000,
                    "basin.held": 60000,
                    "h2.skip": 60000,
                },
                "time_alias": "t_rel_ms; t0 = 2026-08-17T04:10:00Z campaign start",
            },
            "distillation_targets": [
                "LPR reconstruction head: Rp = dE/dI; i_corr = B/Rp; CR = k_i * i_corr = k_cr/Rp",
                "bounded isolate vs keep-campaign vs header-scrap",
                "vendor-campaign nonsubstitution: last-good envelope is not a skip-isolate witness",
                "operational companion: refuse skip without re-opening the corrosion-rate call",
            ],
        },
        "reconstruction_model": {
            "name": "lpr_stern_geary_corrosion_rate",
            "formula": "Rp_kOhm = dE_mV / dI_uA; i_corr_uA = B_mV / Rp_kOhm; CR_mmpy = k_i * i_corr_uA = k_cr / Rp_kOhm",
            "parameters": {
                "B_mV": 24.00,
                "k_i": 4.00,
                "k_cr": 96.00,
                "isolate_floor_mmpy": 8.00,
                "scrap_mmpy": 24.00,
                "hold_min": 15.0,
            },
            "worked_example": {"dE_mV": 16.00, "dI_uA": 2.00, "Rp_kOhm": 8.00, "CR_mmpy": 12.00},
            "check": "16.00/2.00 = 8.00 exactly; 24.00/8.00 = 3.00; 4.00*3.00 = 12.00; 96.00/8.00 = 12.00; 6600 s + 900 s = 7500 s = 15.0 min floor",
        },
        "raster": raster,
        "gate_snn": {
            "decision": "ACCEPT",
            "decision_window_ms": 40.0,
            "decision_window_s": 0.040,
            "code": "wm8.lpr_isolate_gate",
            "note": "ACCEPT accumulator wins: LPR corrosion-rate evidence overpowers the Polarveil continue advocate",
            "decode_rule": "accept if rp_estimator AND current_norm AND header_margin fire inside the window; vendor_continue_advocate is necessary-but-not-sufficient and cannot release the basin",
            "populations": [
                gate_pop("rp_estimator", 80, 1.5, 50.0, w_s),
                gate_pop("current_norm", 64, 1.2, 31.25, w_s),
                gate_pop("header_margin", 40, 1.0, 50.0, w_s),
                gate_pop("vendor_continue_advocate", 32, 0.7, 25.0, w_s),
                gate_pop("accept_latch", 96, 1.8, 62.5, w_s),
            ],
        },
        "gate_compute": gate_compute(
            [
                {"check": "wm8.lpr_scorer", "neurons": 96, "mean_rate_hz": 50.0, "window_ms": 40.0},
                {"check": "wm8.cr_scorer", "neurons": 40, "mean_rate_hz": 62.5, "window_ms": 32.0},
            ]
        ),
        "meta": meta_common(
            id="nelb-r45-138",
            clock_domain="wm8-lpr-sim-relative-ms-t0-2026-08-17T04:10:00Z",
            tags=["lpr-corrosion", "ACCEPT", "REJECT", "serialized-reconstruction", "operational-t2"],
        ),
    }
