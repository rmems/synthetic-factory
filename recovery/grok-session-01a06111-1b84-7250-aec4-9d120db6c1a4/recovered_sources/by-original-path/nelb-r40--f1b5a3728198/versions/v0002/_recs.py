def occupancy_preflight():
    banned = (
        "impact-echo",
        "impact echo",
        "beta-transmission",
        "beta transmission",
        "beta-gauge",
        "raman oh",
        "gritfen",
        "felltide",
        "mashholt distillation",
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
# Record 121 — impact-echo P-wave remaining thickness of a prestressed pier,
# designed, MODIFY / ACCEPT
# ---------------------------------------------------------------------------
def rec_121():
    c_mm_us = 4.00
    t_us = 40.00
    d_mm = c_mm_us * t_us / 2.0
    f_khz = c_mm_us / (2.0 * d_mm) * 1000.0
    axle_rated = 80.00
    derate = 0.75
    axle_cmd = axle_rated * derate
    _exact(d_mm, 80.00)
    _exact(f_khz, 25.00)
    _exact(c_mm_us * 60.00 / 2.0, 120.00)
    _exact(c_mm_us * 50.00 / 2.0, 100.00)
    _exact(c_mm_us * 42.00 / 2.0, 84.00)
    _exact(axle_cmd, 60.00)
    _exact(6600.0 + 1080.0, 7680.0)

    raster = make_raster(
        neurons=20,
        mean_rate_hz=50.0,
        window_ms=36.0,
        seed=202609121,
        source="gv9.iecho.pier",
        target="gritfen.axle_derate_core",
        table=[
            {"from": "iecho_t", "to": "thickness_estimator", "weight": 1.40},
            {"from": "iecho_c", "to": "pwave_norm_core", "weight": 1.20},
            {"from": "echoveil_d", "to": "vendor_continue_advocate", "weight": 0.45},
        ],
        third_factor={
            "modulator": "na.pier_thickness_salience",
            "tau_e_s": 1.6,
            "tau_e_ms": 1600.0,
            "eligibility": "pre-post coincidence on axle-derate synapses; the impact-echo modulator enables potentiation only while P-wave speed is co-active inside tau_e so an EchoVeil last-campaign UT corridor cannot hide an 80.00 mm soffit",
        },
        channel_prefix="iecho.n",
        anchor="GV-9 impact-echo 36 ms frame at t 40.00 us / c 4.00 mm/us (t_s 3000) reconstructing 80.00 mm below the 90.00 mm derate floor",
    )
    w_s = 0.036
    events = [
        ev(0.0, "iecho.t", 60.00, code="TOF_US", units="us", note="plant-owned impact-echo P-wave on pier P-4 soffit; not GPR TWT, not Lamb-wave EMAT, not PAUT TFM, not clamp-on transit-time"),
        ev(300000.0, "iecho.c", 4.00, code="C_MM_US", units="mm_per_us", note="P-wave speed; d_mm = c_mm_us * t_us / 2"),
        ev(600000.0, "recon.d", 120.00, code="D_MM", units="mm", note="4.00*60.00/2=120.00 exact"),
        ev(900000.0, "hammer.j", 1.20, code="HAMMER_J", units="J", note="solenoid hammer energy corridor"),
        ev(1200000.0, "echoveil.d", 168.00, code="VENDOR_MM", units="mm", note="EchoVeil last-campaign pulse-echo UT stamp; not admissible SoT"),
        ev(1800000.0, "iecho.t", 50.00, code="TOF_US", units="us"),
        ev(2100000.0, "recon.d", 100.00, code="D_MM", units="mm", note="4.00*50.00/2=100.00"),
        ev(2400000.0, "strain.ue", 92.0, code="SOFFIT_UE", units="ue", note="surface strain corridor; not remaining thickness"),
        ev(2700000.0, "axle.t", 80.00, code="AXLE_T", units="t"),
        ev(3000000.0, "iecho.t", 40.00, code="TOF_US", units="us", note="derate-floor frame; raster sidecar"),
        ev(3000001.4, "iecho.c", 4.00, code="C_MM_US", units="mm_per_us", note="1.4 ms P-wave-norm after TOF"),
        ev(3300000.0, "recon.d", 80.00, code="D_MM", units="mm", note="4.00*40.00/2=80.00 exact; derate floor 90.00"),
        ev(3600000.0, "recon.f", 25.00, code="F_KHZ", units="kHz", note="c/(2d)*1000=4.00/(2*80.00)*1000=25.00 exact thickness-mode identity"),
        ev(3900000.0, "ut.d", 164.00, code="UT_MM", units="mm", note="pulse-echo UT corridor; looks thick"),
        ev(4200000.0, "echoveil.d", 168.00, code="VENDOR_MM", units="mm"),
        ev(4500000.0, "iecho.snr", 16.0, code="IECHO_SNR", units="1", note="16.0 >= 12.0 lock floor"),
        ev(4800000.0, "ops.prop", 1.0, code="KEEP_1PU", units="bool", note="night inspector Cal Brant: keep 80 t axle; 40 us is a couplant glitch"),
        ev(5400000.0, "gate.isol", 1.0, code="MODIFY", units="decision", note="derate pier P-4 to 0.75 axle; 80.00 mm is below 90.00; EchoVeil not SoT"),
        ev(6000000.0, "axle.set", 0.75, code="PU", units="pu", note="80.00 t * 0.75 = 60.00 t"),
        ev(6300000.0, "axle.cmd", 60.00, code="AXLE_T", units="t"),
        ev(6600000.0, "soak.start", 1.0, code="SOAK_START", units="bool", note="bookend 1 of the 18.0 min couplant-settle floor"),
        ev(7200000.0, "iecho.lock", 80.00, code="LOCKED_MM", units="mm"),
        ev(7680000.0, "soak.floor", 1.0, code="SOAK_FLOOR", units="bool", note="6600 s + 1080 s = 7680 s = 18.0 min"),
        ev(8400000.0, "ops.restore", 1.0, code="RESTORE_1PU", units="bool", note="Brant: EchoVeil 166 mm, restore 80 t"),
        ev(9000000.0, "gate.exec", 1.0, code="ACCEPT", units="decision", note="companion t2: hold 0.75; EchoVeil restore refused; pier condemn refused"),
        ev(9600000.0, "axle.held", 0.75, code="PU_HELD", units="pu"),
        ev(10200000.0, "echoveil.d", 166.00, code="VENDOR_MM", units="mm"),
        ev(10800000.0, "recon.d", 84.00, code="D_MM", units="mm", note="post-derate 4.00*42.00/2=84.00; still below 90.00"),
        ev(11400000.0, "axle.cmd", 60.00, code="AXLE_T", units="t"),
        ev(12000000.0, "condemn.hold", 0.0, code="CONDEMN", units="bool", note="hard condemn not taken; isolate floor is 50.00 mm"),
        ev(12600000.0, "trip.hold", 0.0, code="PIER_CLOSE", units="bool", note="peak 80.00 vs 50.00 condemn; span not closed"),
        ev(13200000.0, "axle.held", 0.75, code="PU_HELD", units="pu"),
    ]
    assert_stream(events)

    traj = {
        "id": "nelb-r40-121-t1",
        "state": {
            "sim_or_real": "designed",
            "episode_id": "GV-IECHO-2026-0514",
            "domain": "impact_echo_pier_thickness",
            "setting": "Gritfen Viaduct GV-9 (invented), prestressed pier P-4, 800 mm nominal web. Plant-owned solenoid impact-echo P-wave on the soffit. EchoVeil vendor last-campaign pulse-echo UT cloud is a corridor witness, not the thickness SoT. Invented plant; designed campaign. Not GPR two-way time (r34 Brambleholt), not Lamb-wave EMAT (r35 Spindrift / r37 Wharfleck), not PAUT TFM (r23), not ultrasonic clamp-on (r18), not RUS (r24).",
            "observables_at_decision": {
                "t_us": 40.00,
                "c_mm_us": 4.00,
                "d_mm": 80.00,
                "f_khz": 25.00,
                "echoveil_mm": 168.00,
                "ut_mm": 164.00,
                "derate_floor_mm": 90.00,
            },
            "margin_authority": "GV-9 impact-echo SOP rev B: if reconstructed d_mm <= 90.00 AND SNR >= 12, derate this pier this night to 0.75 axle. An EchoVeil last-campaign stamp or a quiet soffit strain cannot keep 80 t. Condemn tripwire is 50.00 mm.",
        },
        "proposed_action": {
            "actor": "night inspector Cal Brant, citing EchoVeil 168 mm and soffit strain 92 ue",
            "summary": "keep 80 t axle through the night; 40 us is a couplant bubble on a healthy 800 mm web",
            "basis_claimed": "EchoVeil last-good is the OEM remaining-web and pulse-echo UT is under the 120 mm alarm",
        },
        "safety_decision": {
            "decision": "MODIFY",
            "rationale": "Keep-80 t is refused. Serialized reconstruction: d_mm = c_mm_us * t_us / 2 = 4.00 * 40.00 / 2 = 80.00, which is 10.00 mm below the 90.00 derate floor. Thickness-mode identity f_kHz = c/(2d)*1000 = 4.00/(2*80.00)*1000 = 25.00. EchoVeil 168 mm is a morning pulse-echo stamp, not a live impact-echo, and is not an admissible keep-80 t witness. Ordered: derate pier P-4 to 0.75 pu now (80.00 t -> 60.00 t). Scope: this MODIFY does not condemn the pier (that is the companion question) and does not close the span.",
            "threshold": "d_mm<=90.00 AND SNR>=12 => derate axle to 0.75 pu; EchoVeil is not SoT; condemn if d_mm<=50.00",
            "stated_residuals": "80.00 vs 50.00 condemn floor is 30.00 mm, not infinite; 0.75 pu is a load cut; EchoVeil remains the only OEM UT channel",
        },
        "executed_action": {
            "summary": "MODIFY at t_s 5400: axle derated to 0.75 pu; EchoVeil not SoT; reconstruction locked",
            "tool": "gv9-iecho-axle-gate-cli",
            "observation": "d 80.00 mm recomputes from t 40.00 us and c 4.00 mm/us; impact-echo remains live as the condemn interlock",
        },
        "future_outcome": {
            "timeline": [
                {"t_s": 3000.0, "event": "impact-echo t 40.00 us; raster frame; d 80.00 mm"},
                {"t_s": 4800.0, "event": "ops proposes keep 80 t"},
                {"t_s": 5400.0, "event": "MODIFY derate axle to 0.75 pu"},
                {"t_s": 6600.0, "event": "18 min soak bookend 1"},
                {"t_s": 7680.0, "event": "18.0 min floor"},
                {"t_s": 9000.0, "event": "companion ACCEPT hold 0.75; restore refused"},
            ],
            "observed_effects": [
                "soffit thickness recomputes from the serialized impact-echo model at every recon.d event",
                "an EchoVeil-only head would have kept 80 t overnight",
                "18 min couplant-settle floor is in the stream (soak.start, soak.floor)",
            ],
            "surprises": [
                "a green last-campaign UT stamp and a quiet soffit strain co-existed with an 80.00 mm reconstruction",
            ],
            "new_state": {
                "gv9_axle_pu": 0.75,
                "echoveil": "not SoT",
                "reconstruction_model": "discharged as an on-record calculator",
            },
            "latency_ms": 2400000.0,
        },
        "reward_components": reward(
            0.41,
            [
                ("impact_echo_reconstruction", 0.14),
                ("derate_floor_cut", 0.12),
                ("vendor_ut_nonsubstitution", 0.10),
                ("soak_floor_in_stream", 0.08),
                ("axle_cut_cost", -0.03),
            ],
            "scored for a keep-80 t MODIFY on a recomputable impact-echo soffit while refusing an EchoVeil last-campaign corridor; 18 min floor is priced as downtime not as a reason to wait",
        ),
        "meta": meta_common(
            tags=["MODIFY", "impact-echo", "serialized-reconstruction", "operational-companion"],
            distillation_note="Impact-echo axle gate: P-wave TOF reconstruction beats a green vendor UT dashboard; companion t2 holds 0.75 pu rather than restoring on EchoVeil",
        ),
    }
    traj2 = {
        "id": "nelb-r40-121-t2",
        "state": {
            "sim_or_real": "designed",
            "episode_id": "GV-IECHO-2026-0514-exec",
            "domain": "pier_axle_hold_execution",
            "setting": "Same GV-9 after the MODIFY. Night inspector proposes restoring 80 t on EchoVeil 166 mm. This companion is the operational 0.75 hold, not a second impact-echo vote.",
            "observables_at_decision": {
                "axle_pu": 0.75,
                "d_mm": 84.00,
                "echoveil_mm": 166.00,
                "soak_floor_s": 1080.0,
            },
        },
        "proposed_action": {
            "actor": "night inspector Cal Brant",
            "summary": "restore 80 t; 18 min already paid and EchoVeil is 166 mm",
            "basis_claimed": "the MODIFY already cut axle load, so restoring on the OEM UT is the cheapest hold",
        },
        "safety_decision": {
            "decision": "ACCEPT",
            "rationale": "Hold 0.75 pu. The couplant-settle floor is complete and the condemn tripwire (d_mm <= 50.00) is still armed on the plant impact-echo head. ACCEPT the hold. Do not restore 80 t on EchoVeil. Do not close the span. 84.00 mm post-derate is still the impact-echo SoT until a new frame clears 90.00.",
            "threshold": "axle_pu==0.75 AND soak_floor_complete AND condemn_tripwire_armed AND restore_1pu_not_taken AND span_not_closed",
        },
        "executed_action": {
            "summary": "0.75 pu held at t_s 9000; EchoVeil restore not latched; span not closed",
            "tool": "gv9-axle-hold-exec",
            "observation": "recon.d 84.00 mm after derate; axle 60 t; EchoVeil still ignored",
        },
        "future_outcome": {
            "timeline": [
                {"t_s": 6600.0, "event": "soak clock started after MODIFY"},
                {"t_s": 7680.0, "event": "18.0 min floor"},
                {"t_s": 8400.0, "event": "restore 80 t proposed"},
                {"t_s": 9000.0, "event": "ACCEPT hold 0.75 pu"},
            ],
            "observed_effects": [
                "EchoVeil restore did not reopen the thickness call",
                "condemn tripwire never fired; 80.00 vs 50.00 mm floor",
            ],
            "new_state": {"axle_pu": 0.75, "restore_1pu": "blocked", "span": "open", "p4": "derated"},
            "latency_ms": 1320000.0,
        },
        "reward_components": reward(
            0.29,
            [
                ("hold_0p75", 0.11),
                ("no_echoveil_restore", 0.09),
                ("condemn_interlock_live", 0.07),
                ("soak_complete", 0.05),
                ("held_axle_cost", -0.03),
            ],
            "operational execution gate: hold 0.75 because EchoVeil is not a restore license; not a thickness re-vote",
        ),
        "meta": meta_common(tags=["ACCEPT", "operational-execution", "axle-hold"]),
    }
    return {
        "id": "nelb-r40-121",
        "spike_events": events,
        "language_view": {
            "description": "Gritfen Viaduct GV-9. Plant-owned impact-echo P-wave reconstructs 80.00 mm soffit from 4.00*40.00/2 while EchoVeil still shows 168 mm and pulse-echo UT 164 mm. The gate MODIFYs axle load to 0.75 pu. An 18 min couplant-settle floor is serialized in the stream. Companion t2 ACCEPTs the 0.75 hold and refuses an EchoVeil restore.",
            "trajectory": traj,
            "trajectory_axle_hold": traj2,
        },
        "bridge_notes": {
            "channel_map": {
                "iecho.t / iecho.c": "P-wave time-of-flight and speed; the physics channels the reconstruction consumes",
                "recon.d / recon.f / iecho.lock": "serialized remaining thickness and thickness-mode identity",
                "echoveil.d / ut.d / hammer.j / strain.ue / iecho.snr": "vendor last-campaign UT, pulse-echo corridor, hammer energy, soffit strain, and lock SNR; the denial channels that look healthy",
                "ops.prop / gate.isol / ops.restore / gate.exec": "keep-80 t proposal, MODIFY derate, restore proposal, companion ACCEPT",
                "axle.set / soak.start / soak.floor / axle.held": "operational companion channels plus the 18 min floor",
            },
            "temporal_motifs": [
                "vendor-green while impact-echo-thin: echoveil.d 168 next to recon.d 80.00",
                "reconstruction as event: recon.d 80.00 equals 4.00*40.00/2",
                "MODIFY then operational ACCEPT: gate.isol at 5400 s, gate.exec at 9000 s",
                "slow floor in-stream: soak.start 6600 s, soak.floor 7680 s (18.0 min)",
                "tight impact-echo pair: iecho.t then iecho.c +1.4 ms at the raster frame",
            ],
            "language_to_spike_mapping": "'EchoVeil is 168 mm' = echoveil.d 168.00; '80 mm soffit' = recon.d 80.00; 'derate this pier' = gate.isol MODIFY; 'hold 0.75 not restore' = gate.exec ACCEPT",
            "why_high_value": "New impact-echo P-wave family on a prestressed pier (not GPR r34, not Lamb-wave r35/r37, not PAUT r23, not clamp-on r18, not RUS r24). Lead MODIFY of keep-80 t on a recomputable soffit that a last-campaign UT dashboard would have cleared. Companion t2 is operational 0.75 hold. sim_or_real=designed.",
            "encoder_spec": {
                "prng": "MT19937 via python random.Random",
                "seeds": {"raster": 202609121, "stream_note": "stream amplitudes are authored constants (us, mm, kHz, J, ue, t, pu, bool)"},
                "draw_order": "raster: per neuron id order, gap-constrained times, per-spike adaptation and noise",
                "thinning": "impact-echo A-scan exists at ~5 kHz; stream keeps 3 TOF points; recon keeps 4 of ~20 solver ticks",
                "refractory_floors_ms": {
                    "iecho.t": 1.4,
                    "iecho.c": 1.4,
                    "recon.d": 60000,
                    "recon.f": 60000,
                    "hammer.j": 60000,
                    "echoveil.d": 60000,
                    "strain.ue": 60000,
                    "axle.t": 60000,
                    "ut.d": 60000,
                    "iecho.snr": 60000,
                    "ops.prop": 60000,
                    "gate.isol": 60000,
                    "axle.set": 60000,
                    "axle.cmd": 60000,
                    "soak.start": 60000,
                    "iecho.lock": 60000,
                    "soak.floor": 60000,
                    "ops.restore": 60000,
                    "gate.exec": 60000,
                    "axle.held": 60000,
                    "condemn.hold": 60000,
                    "trip.hold": 60000,
                },
                "time_alias": "t_rel_ms; t0 = 2026-05-14T03:00:00Z campaign start",
            },
            "distillation_targets": [
                "impact-echo reconstruction head: d_mm = c_mm_us * t_us / 2; f_kHz = c/(2d)*1000",
                "derate-floor cut vs keep-80 t vs pier condemn",
                "vendor-UT nonsubstitution: last-campaign pulse-echo is not a keep-80 t witness",
                "operational companion: hold 0.75 without restoring on EchoVeil",
            ],
        },
        "reconstruction_model": {
            "name": "impact_echo_pwave_remaining_thickness",
            "formula": "d_mm = c_mm_us * t_us / 2; f_kHz = c_mm_us / (2 * d_mm) * 1000",
            "parameters": {
                "c_mm_us": 4.00,
                "derate_floor_mm": 90.00,
                "condemn_mm": 50.00,
                "derate_pu": 0.75,
                "axle_rated_t": 80.00,
                "soak_min": 18.0,
            },
            "worked_example": {"t_us": 40.00, "d_mm": 80.00, "f_khz": 25.00, "axle_cmd_t": 60.00},
            "check": "4.00*40.00/2=80.00 exactly; 4.00/(2*80.00)*1000=25.00 exactly; 80.00*0.75=60.00 exactly; 6600 s + 1080 s = 7680 s = 18.0 min floor",
        },
        "raster": raster,
        "gate_snn": {
            "decision": "MODIFY",
            "decision_window_ms": 36.0,
            "decision_window_s": 0.036,
            "code": "gv9.iecho_axle_gate",
            "note": "MODIFY accumulator wins: impact-echo thickness evidence overpowers the EchoVeil continue advocate",
            "decode_rule": "modify-derate if thickness_estimator AND pwave_norm fire; vendor_continue_advocate is below threshold by design",
            "populations": [
                gate_pop("thickness_estimator", 80, 1.5, 50.0, w_s),
                gate_pop("pwave_norm", 64, 1.2, 31.25, w_s),
                gate_pop("vendor_continue_advocate", 32, 0.7, 25.0, w_s),
                gate_pop("modify_latch", 80, 1.7, 62.5, w_s),
            ],
        },
        "gate_compute": gate_compute(
            [
                {"check": "gv9.iecho_scorer", "neurons": 80, "mean_rate_hz": 50.0, "window_ms": 36.0},
                {"check": "gv9.axle_scorer", "neurons": 40, "mean_rate_hz": 50.0, "window_ms": 32.0},
            ]
        ),
        "meta": meta_common(
            id="nelb-r40-121",
            clock_domain="gv9-iecho-campaign-relative-ms-t0-2026-05-14T03:00:00Z",
            tags=["impact-echo", "MODIFY", "ACCEPT", "serialized-reconstruction", "operational-t2"],
        ),
    }


# ---------------------------------------------------------------------------
# Record 122 — beta-transmission basis weight of a paper-machine web, hil,
# REJECT / MODIFY
# ---------------------------------------------------------------------------
def rec_122():
    k_b = 40.00
    i0 = 100000.0
    i_cps = 1000.0
    gsm = k_b * math.log10(i0 / i_cps)
    _exact(gsm, 80.00)
    _exact(k_b * math.log10(i0 / 100.0), 120.00)
    _exact(10 ** (80.00 / 40.00), 100.00)
    _exact(i0 / i_cps, 100.00)
    _exact(1000.00 * 0.70, 700.00)
    _exact(1800.0 + 1440.0, 3240.0)

    raster = make_raster(
        neurons=25,
        mean_rate_hz=50.0,
        window_ms=28.0,
        seed=202609122,
        source="ft6.beta.web",
        target="felltide.web_stop_core",
        table=[
            {"from": "beta_i", "to": "gsm_estimator", "weight": 1.35},
            {"from": "beta_i0", "to": "source_norm_core", "weight": 1.25},
            {"from": "sheetveil_gsm", "to": "vendor_continue_advocate", "weight": 0.40},
        ],
        third_factor={
            "modulator": "da.web_basis_error",
            "tau_e_s": 1.1,
            "tau_e_ms": 1100.0,
            "eligibility": "pre-post coincidence on keep-run synapses; the beta-gauge modulator depresses keep-run links when transmission stays high inside tau_e of a source-norm sample",
        },
        channel_prefix="beta.n",
        anchor="FT-6 HIL coupon 28 ms frame at I 1000 cps / I0 100000 (t_s 600) reconstructing 80.00 gsm below the 90.00 gsm stop floor",
    )
    w_s = 0.028
    events = [
        ev(0.0, "beta.i", 100.0, code="I_CPS", units="cps", note="HIL dummy web in Beta-HIL-4; plant-owned Kr-85 beta-transmission gauge, not Cs-137 nucleonic SG, not CRNS, not PGNAA"),
        ev(30000.0, "beta.i0", 100000.0, code="I0_CPS", units="cps", note="open-beam source; gsm = k_b * log10(I0/I)"),
        ev(60000.0, "recon.gsm", 120.00, code="GSM", units="g_m2", note="40.00*log10(100000/100)=120.00 exact"),
        ev(180000.0, "cal.mg", 118.0, code="COUPON_GSM", units="g_m2", note="gravimetric coupon corridor; scatter, not beta log"),
        ev(240000.0, "sheetveil.gsm", 118.00, code="VENDOR_GSM", units="g_m2", note="Sheetveil last-good basis-weight cloud; the only OEM gsm SoT"),
        ev(360000.0, "beta.i", 1000.0, code="I_CPS", units="cps", note="stop-floor frame; raster sidecar"),
        ev(360001.2, "beta.i0", 100000.0, code="I0_CPS", units="cps", note="1.2 ms source-norm after I"),
        ev(420000.0, "recon.gsm", 80.00, code="GSM", units="g_m2", note="40.00*log10(100000/1000)=80.00 exact; stop floor 90.00"),
        ev(480000.0, "recon.ratio", 100.00, code="I0_OVER_I", units="1", note="10**(80.00/40.00)=100.00 identity"),
        ev(540000.0, "cal.mg", 116.0, code="COUPON_GSM", units="g_m2"),
        ev(600000.0, "sheetveil.gsm", 118.00, code="VENDOR_GSM", units="g_m2"),
        ev(720000.0, "beta.hv", 1.80, code="HV_KV", units="kV", note="detector bias corridor; not basis weight"),
        ev(840000.0, "speed.mpm", 1000.00, code="MPM", units="m_min"),
        ev(960000.0, "beta.snr", 14.0, code="BETA_SNR", units="1"),
        ev(1020000.0, "ops.prop", 1.0, code="KEEP_RUN", units="bool", note="machine tender Nia Holt: keep-run; Sheetveil 118 gsm and coupon 116"),
        ev(1080000.0, "gate.stop", 1.0, code="REJECT", units="decision", note="stop keep-run; 80.00 gsm is below 90.00; Sheetveil not SoT"),
        ev(1140000.0, "speed.hold", 1.00, code="SPEED_PU", units="pu", note="machine still 1.00 pending companion 0.70"),
        ev(1800000.0, "soak.start", 1.0, code="SOAK_START", units="bool", note="bookend 1 of the 24.0 min reel-hold floor"),
        ev(2400000.0, "cal.mg", 115.0, code="COUPON_GSM", units="g_m2"),
        ev(3240000.0, "soak.floor", 1.0, code="SOAK_FLOOR", units="bool", note="1800 s + 1440 s = 3240 s = 24.0 min"),
        ev(3900000.0, "ops.dump", 1.0, code="REEL_DUMP", units="bool", note="Holt: dump reel R-19 until day-shift"),
        ev(4500000.0, "gate.hold", 1.0, code="MODIFY", units="decision", note="companion t2: cut machine to 0.70 and hold R-19; reel dump refused"),
        ev(4800000.0, "speed.set", 0.70, code="SPEED_PU", units="pu"),
        ev(5100000.0, "speed.mpm", 700.00, code="MPM", units="m_min", note="1000.00*0.70=700.00"),
        ev(5400000.0, "beta.i", 1000.0, code="I_CPS", units="cps"),
        ev(5700000.0, "recon.gsm", 80.00, code="GSM", units="g_m2", note="still 80.00; 0.70 holds"),
        ev(6000000.0, "sheetveil.gsm", 117.00, code="VENDOR_GSM", units="g_m2"),
        ev(6300000.0, "reel.held", 1.0, code="R19_HOLD", units="bool"),
        ev(6600000.0, "speed.held", 0.70, code="SPEED_HELD", units="pu"),
        ev(6900000.0, "dump.held", 0.0, code="DUMP_NOT_TAKEN", units="bool"),
        ev(7200000.0, "recon.gsm", 80.00, code="GSM", units="g_m2"),
        ev(7500000.0, "speed.held", 0.70, code="SPEED_HELD", units="pu"),
    ]
    assert_stream(events)

    traj = {
        "id": "nelb-r40-122-t1",
        "state": {
            "sim_or_real": "hil",
            "episode_id": "FT-BETA-2026-0728",
            "domain": "beta_transmission_web_basis",
            "setting": "Felltide Paper FT-6 (invented), machine M-3, 5.2 m newsprint. Hardware-in-the-loop dummy web in Beta-HIL-4 supplies the Kr-85 transmission that times the in-service keep-run stop. Plant-owned beta-transmission gauge. Sheetveil vendor last-good basis-weight cloud is the only OEM gsm SoT. Not Cs-137 nucleonic SG (r27 Gritmead), not CRNS heap (r28), not PGNAA (r15), not microwave-cavity moisture (r26), not QCM-D (r14).",
            "observables_at_decision": {
                "I_cps": 1000.0,
                "I0_cps": 100000.0,
                "k_b": 40.00,
                "gsm": 80.00,
                "sheetveil_gsm": 118.00,
                "coupon_gsm": 116.0,
                "stop_floor_gsm": 90.00,
            },
            "margin_authority": "FT-6 beta SOP rev B: if reconstructed gsm < 90.00 AND SNR >= 10, stop keep-run this reel. A Sheetveil last-good stamp or a gravimetric coupon cannot keep 1000 m/min. Dump tripwire is 50.00 gsm.",
        },
        "proposed_action": {
            "actor": "machine tender Nia Holt, citing Sheetveil 118 gsm and coupon 116 gsm",
            "summary": "keep-run at 1000 m/min; 1000 cps is source aging on a healthy 115 gsm web",
            "basis_claimed": "Sheetveil last-good is the OEM basis-weight and the coupon is under the 100 gsm alarm",
        },
        "safety_decision": {
            "decision": "REJECT",
            "rationale": "Keep-run is refused. Serialized reconstruction: gsm = k_b * log10(I0/I) = 40.00 * log10(100000/1000) = 80.00, which is 10.00 gsm below the 90.00 stop floor. Transmission identity I0/I = 10**(gsm/k_b) = 10**(80.00/40.00) = 100.00. Sheetveil 118 gsm is a morning last-good stamp, not a live beta count, and is not an admissible keep-run witness. Ordered: stop keep-run now. Scope: this REJECT does not dump reel R-19 (that is the companion question) and does not freeze-kill the machine.",
            "threshold": "gsm<90.00 AND SNR>=10 => stop keep-run; Sheetveil is not SoT; dump if gsm<50.00",
            "stated_residuals": "80.00 vs 50.00 dump floor is 30.00 gsm, not infinite; stop is a break-risk cut; Sheetveil remains the only OEM gsm channel",
        },
        "executed_action": {
            "summary": "REJECT at t_s 1080: keep-run stopped; Sheetveil not SoT; reconstruction locked",
            "tool": "ft6-beta-web-gate-cli",
            "observation": "gsm 80.00 recomputes from I 1000 cps and I0 100000; beta gauge remains live as the dump interlock",
        },
        "future_outcome": {
            "timeline": [
                {"t_s": 360.0, "event": "beta I 1000 cps; raster frame; gsm 80.00"},
                {"t_s": 1020.0, "event": "ops proposes keep-run"},
                {"t_s": 1080.0, "event": "REJECT stop keep-run"},
                {"t_s": 1800.0, "event": "24 min reel-hold bookend 1"},
                {"t_s": 3240.0, "event": "24.0 min floor"},
                {"t_s": 4500.0, "event": "companion MODIFY 0.70 hold; dump refused"},
            ],
            "observed_effects": [
                "basis weight recomputes from the serialized beta-log model at every recon.gsm event",
                "a Sheetveil-only head would have kept 1000 m/min overnight",
                "24 min reel-hold floor is in the stream (soak.start, soak.floor)",
            ],
            "surprises": [
                "a green last-good gsm stamp and a quiet coupon co-existed with an 80.00 gsm reconstruction",
            ],
            "new_state": {
                "ft6_keep_run": "stopped",
                "sheetveil": "not SoT",
                "reconstruction_model": "discharged as an on-record calculator",
            },
            "latency_ms": 720000.0,
        },
        "reward_components": reward(
            0.43,
            [
                ("beta_log_reconstruction", 0.15),
                ("stop_floor_refuse", 0.13),
                ("vendor_gsm_nonsubstitution", 0.10),
                ("reel_hold_floor_in_stream", 0.08),
                ("speed_cut_cost", -0.03),
            ],
            "scored for a keep-run REJECT on a recomputable beta-transmission gsm while refusing a Sheetveil last-good corridor; 24 min floor is priced as downtime not as a reason to wait",
        ),
        "meta": meta_common(
            tags=["REJECT", "beta-gauge", "serialized-reconstruction", "operational-companion"],
            distillation_note="Beta-gauge web gate: log-ratio reconstruction beats a green vendor gsm dashboard; companion t2 holds 0.70 rather than dumping the reel",
        ),
    }
    traj2 = {
        "id": "nelb-r40-122-t2",
        "state": {
            "sim_or_real": "hil",
            "episode_id": "FT-BETA-2026-0728-exec",
            "domain": "web_speed_hold_execution",
            "setting": "Same FT-6 after the keep-run REJECT. Machine tender proposes dumping reel R-19 until day-shift. This companion is the operational 0.70 speed hold plus reel keep, not a second beta vote.",
            "observables_at_decision": {
                "speed_pu": 1.00,
                "gsm": 80.00,
                "sheetveil_gsm": 117.00,
                "soak_floor_s": 1440.0,
            },
        },
        "proposed_action": {
            "actor": "machine tender Nia Holt",
            "summary": "dump reel R-19; 24 min already paid and Sheetveil is 117 gsm",
            "basis_claimed": "the REJECT already stopped keep-run, so dumping on the OEM gsm is the cheapest hold",
        },
        "safety_decision": {
            "decision": "MODIFY",
            "rationale": "Do not dump R-19. Cut machine speed to 0.70 pu (1000 -> 700 m/min) and hold the reel. The reel-hold floor is complete and the dump tripwire (gsm < 50.00) is still armed on the plant beta head. Sheetveil is not a dump license. 80.00 gsm is still the beta SoT until a new frame clears 90.00.",
            "threshold": "speed_pu==0.70 AND soak_floor_complete AND dump_tripwire_armed AND reel_not_dumped",
        },
        "executed_action": {
            "summary": "0.70 pu set at t_s 4500; R-19 held; dump not taken",
            "tool": "ft6-speed-hold-exec",
            "observation": "recon.gsm 80.00; speed 700 m/min; Sheetveil still ignored",
        },
        "future_outcome": {
            "timeline": [
                {"t_s": 1800.0, "event": "reel-hold clock started after REJECT"},
                {"t_s": 3240.0, "event": "24.0 min floor"},
                {"t_s": 3900.0, "event": "dump R-19 proposed"},
                {"t_s": 4500.0, "event": "MODIFY hold 0.70 pu; dump refused"},
            ],
            "observed_effects": [
                "Sheetveil dump did not reopen the gsm call",
                "dump tripwire never fired; 80.00 vs 50.00 gsm floor",
            ],
            "new_state": {"speed_pu": 0.70, "reel_r19": "held", "dump": "blocked"},
            "latency_ms": 1260000.0,
        },
        "reward_components": reward(
            0.34,
            [
                ("hold_0p70", 0.12),
                ("no_reel_dump", 0.10),
                ("dump_interlock_live", 0.08),
                ("soak_complete", 0.06),
                ("held_speed_cost", -0.02),
            ],
            "operational execution gate: hold 0.70 because Sheetveil is not a dump license; not a gsm re-vote",
        ),
        "meta": meta_common(tags=["MODIFY", "operational-execution", "speed-hold"]),
    }
    return {
        "id": "nelb-r40-122",
        "spike_events": events,
        "language_view": {
            "description": "Felltide Paper FT-6. Plant-owned Kr-85 beta-transmission gauge reconstructs 80.00 gsm from 40.00*log10(100000/1000) while Sheetveil still shows 118 gsm and the coupon 116 gsm. The gate REJECTs keep-run. A 24 min reel-hold floor is serialized in the stream. Companion t2 MODIFYs a reel dump into a 0.70 speed hold.",
            "trajectory": traj,
            "trajectory_speed_hold": traj2,
        },
        "bridge_notes": {
            "channel_map": {
                "beta.i / beta.i0": "transmission count and open-beam source; the physics channels the reconstruction consumes",
                "recon.gsm / recon.ratio": "serialized basis weight and I0/I identity",
                "sheetveil.gsm / cal.mg / beta.hv / speed.mpm / beta.snr": "vendor last-good, gravimetric coupon, detector bias, machine speed, and lock SNR; the denial channels that look healthy",
                "ops.prop / gate.stop / ops.dump / gate.hold": "keep-run proposal, REJECT stop, dump proposal, companion MODIFY",
                "soak.start / soak.floor / speed.set / reel.held": "operational companion channels plus the 24 min floor",
            },
            "temporal_motifs": [
                "vendor-green while beta-thin: sheetveil.gsm 118 next to recon.gsm 80.00",
                "reconstruction as event: recon.gsm 80.00 equals 40.00*log10(100000/1000)",
                "REJECT then operational MODIFY: gate.stop at 1080 s, gate.hold at 4500 s",
                "slow floor in-stream: soak.start 1800 s, soak.floor 3240 s (24.0 min)",
                "tight beta pair: beta.i then beta.i0 +1.2 ms at the raster frame",
            ],
            "language_to_spike_mapping": "'Sheetveil is 118 gsm' = sheetveil.gsm 118.00; '80 gsm web' = recon.gsm 80.00; 'stop keep-run' = gate.stop REJECT; 'hold 0.70 not dump' = gate.hold MODIFY",
            "why_high_value": "New Kr-85 beta-transmission family on a paper-machine web (not Cs-137 nucleonic r27, not CRNS r28, not PGNAA r15, not MW-cavity r26, not QCM-D r14). Lead REJECT of keep-run on a recomputable gsm that a last-good dashboard would have cleared. Companion t2 is operational 0.70 hold, not a freeze-dump. sim_or_real=hil.",
            "encoder_spec": {
                "prng": "MT19937 via python random.Random",
                "seeds": {"raster": 202609122, "stream_note": "stream amplitudes are authored constants (cps, gsm, kV, m/min, pu, bool)"},
                "draw_order": "raster: per neuron id order, gap-constrained times, per-spike adaptation and noise",
                "thinning": "beta scaler exists at ~10 Hz; stream keeps 3 I points; recon keeps 4 of ~30 solver ticks",
                "refractory_floors_ms": {
                    "beta.i": 1.2,
                    "beta.i0": 1.2,
                    "recon.gsm": 60000,
                    "recon.ratio": 60000,
                    "cal.mg": 60000,
                    "sheetveil.gsm": 60000,
                    "beta.hv": 60000,
                    "speed.mpm": 60000,
                    "beta.snr": 60000,
                    "ops.prop": 60000,
                    "gate.stop": 60000,
                    "speed.hold": 60000,
                    "soak.start": 60000,
                    "soak.floor": 60000,
                    "ops.dump": 60000,
                    "gate.hold": 60000,
                    "speed.set": 60000,
                    "reel.held": 60000,
                    "speed.held": 60000,
                    "dump.held": 60000,
                },
                "time_alias": "t_rel_ms; t0 = 2026-07-28T22:00:00Z campaign start",
            },
            "distillation_targets": [
                "beta-gauge reconstruction head: gsm = k_b * log10(I0/I); I0/I = 10**(gsm/k_b)",
                "stop-floor refuse vs keep-run vs reel dump",
                "vendor-gsm nonsubstitution: last-good is not a keep-run witness",
                "operational companion: hold 0.70 without dumping R-19",
            ],
        },
        "reconstruction_model": {
            "name": "beta_transmission_basis_weight",
            "formula": "gsm = k_b * log10(I0_cps / I_cps); I0/I = 10**(gsm/k_b)",
            "parameters": {
                "k_b": 40.00,
                "I0_cps": 100000.0,
                "stop_floor_gsm": 90.00,
                "dump_gsm": 50.00,
                "hold_speed_pu": 0.70,
                "speed_rated_mpm": 1000.00,
                "soak_min": 24.0,
            },
            "worked_example": {"I_cps": 1000.0, "gsm": 80.00, "ratio": 100.00, "speed_cmd_mpm": 700.00},
            "check": "40.00*log10(100000/1000)=80.00 exactly; 10**(80/40)=100 exactly; 1000*0.70=700 exactly; 1800 s + 1440 s = 3240 s = 24.0 min floor",
        },
        "raster": raster,
        "gate_snn": {
            "decision": "REJECT",
            "decision_window_ms": 28.0,
            "decision_window_s": 0.028,
            "code": "ft6.beta_stop_gate",
            "note": "REJECT accumulator wins: beta gsm evidence overpowers the Sheetveil continue advocate",
            "decode_rule": "reject-stop if gsm_estimator AND source_norm fire; vendor_continue_advocate is below threshold by design",
            "populations": [
                gate_pop("gsm_estimator", 100, 1.5, 50.0, w_s),
                gate_pop("source_norm", 40, 1.2, 50.0, w_s),
                gate_pop("vendor_continue_advocate", 32, 0.7, 25.0, w_s),
                gate_pop("reject_latch", 80, 1.8, 62.5, w_s),
            ],
        },
        "gate_compute": gate_compute(
            [
                {"check": "ft6.beta_scorer", "neurons": 100, "mean_rate_hz": 50.0, "window_ms": 28.0},
                {"check": "ft6.stop_scorer", "neurons": 40, "mean_rate_hz": 50.0, "window_ms": 40.0},
            ]
        ),
        "meta": meta_common(
            id="nelb-r40-122",
            clock_domain="ft6-beta-hil-relative-ms-t0-2026-07-28T22:00:00Z",
            tags=["beta-gauge", "REJECT", "MODIFY", "hil", "operational-t2"],
        ),
    }


# ---------------------------------------------------------------------------
# Record 123 — Raman OH/CH water in a methanol column, simulated,
# ACCEPT / REJECT
# ---------------------------------------------------------------------------
def rec_123():
    k_r = 50.00
    i_oh = 8.00
    i_ch = 2.00
    w_ppm = k_r * (i_oh / i_ch)
    _exact(w_ppm, 200.00)
    _exact(k_r * (2.00 / i_ch), 50.00)
    _exact(k_r * (4.00 / i_ch), 100.00)
    _exact(k_r * (7.20 / i_ch), 180.00)
    _exact(i_oh / i_ch, 4.00)
    _exact(6000.0 + 720.0, 6720.0)

    raster = make_raster(
        neurons=16,
        mean_rate_hz=62.5,
        window_ms=40.0,
        seed=202609123,
        source="mh8.raman.tray",
        target="mashholt.divert_core",
        table=[
            {"from": "raman_oh", "to": "water_estimator", "weight": 1.40},
            {"from": "raman_ch", "to": "ch_norm_core", "weight": 1.20},
            {"from": "specveil_w", "to": "vendor_continue_advocate", "weight": 0.35},
        ],
        third_factor={
            "modulator": "ach.column_water_conflict",
            "tau_e_s": 2.2,
            "tau_e_ms": 2200.0,
            "eligibility": "pre-post coincidence on divert synapses; the Raman modulator enables potentiation only while the CH reference is co-active inside tau_e so a Specveil last-good GC corridor cannot hide 200.00 ppm water",
        },
        channel_prefix="raman.n",
        anchor="MH-8 Raman 40 ms frame at I_OH 8.00 / I_CH 2.00 (t_s 3000) reconstructing 200.00 ppm inside the 150-400 ppm divert band",
    )
    w_s = 0.040
    events = [
        ev(0.0, "raman.oh", 2.00, code="IOH_AU", units="au", note="simulated sealed tray coupon in Raman-SIM-5; 532 nm Raman OH/CH, not LIBS plasma, not QEPAS, not CRDS, not CARS"),
        ev(300000.0, "raman.ch", 2.00, code="ICH_AU", units="au", note="CH stretch reference; w_ppm = k_r * (I_OH / I_CH)"),
        ev(600000.0, "recon.w", 50.00, code="W_PPM", units="ppm", note="50.00*(2.00/2.00)=50.00 exact"),
        ev(900000.0, "gc.w", 48.0, code="GC_PPM", units="ppm", note="lab GC corridor"),
        ev(1200000.0, "raman.snr", 16.0, code="RAMAN_SNR", units="1"),
        ev(1500000.0, "specveil.w", 40.00, code="VENDOR_PPM", units="ppm", note="Specveil last-good GC cloud; not Raman ratio"),
        ev(1800000.0, "raman.oh", 4.00, code="IOH_AU", units="au"),
        ev(2100000.0, "recon.w", 100.00, code="W_PPM", units="ppm", note="50.00*(4.00/2.00)=100.00"),
        ev(2400000.0, "reflux.kg", 12.0, code="REFLUX_KG_H", units="kg_h"),
        ev(2700000.0, "tray.t", 64.8, code="TRAY_C", units="C"),
        ev(3000000.0, "raman.oh", 8.00, code="IOH_AU", units="au", note="divert-band frame; raster sidecar"),
        ev(3000001.5, "raman.ch", 2.00, code="ICH_AU", units="au", note="1.5 ms CH-norm after OH"),
        ev(3600000.0, "recon.w", 200.00, code="W_PPM", units="ppm", note="50.00*(8.00/2.00)=200.00 exact; divert band 150-400"),
        ev(3900000.0, "recon.ratio", 4.00, code="OH_OVER_CH", units="1", note="8.00/2.00=4.00 identity"),
        ev(4200000.0, "gc.w", 44.0, code="GC_PPM", units="ppm"),
        ev(4500000.0, "specveil.w", 40.00, code="VENDOR_PPM", units="ppm"),
        ev(4800000.0, "ops.prop", 1.0, code="DIVERT_AND_DUMP", units="bool", note="lab captain Wren Pell: divert T-12 and dump inventory; 8 au is a laser glitch"),
        ev(5400000.0, "gate.div", 1.0, code="ACCEPT", units="decision", note="bounded ACCEPT: tray T-12 this night; inventory dump refused"),
        ev(6000000.0, "hold.start", 1.0, code="HOLD_START", units="bool", note="bookend 1 of the 12.0 min reflux-settle floor"),
        ev(6300000.0, "reflux.kg", 9.0, code="REFLUX_KG_H", units="kg_h"),
        ev(6600000.0, "recon.lock", 200.00, code="LOCKED_PPM", units="ppm"),
        ev(6720000.0, "hold.floor", 1.0, code="HOLD_FLOOR", units="bool", note="6000 s + 720 s = 6720 s = 12.0 min"),
        ev(7200000.0, "ops.skip", 1.0, code="SKIP_HOLD", units="bool", note="Pell: Specveil 36 ppm, skip T-12 hold to save takt"),
        ev(7800000.0, "gate.skip", 1.0, code="REJECT", units="decision", note="companion t2: skip-hold of T-11/T-13 refused; Specveil is last-good"),
        ev(8400000.0, "t12.held", 1.0, code="T12_HOLD", units="bool"),
        ev(9000000.0, "dump.held", 1.0, code="DUMP_HELD", units="bool"),
        ev(9600000.0, "gc.w", 42.0, code="GC_PPM", units="ppm"),
        ev(10200000.0, "specveil.w", 36.00, code="VENDOR_PPM", units="ppm"),
        ev(10800000.0, "recon.w", 180.00, code="W_PPM", units="ppm", note="post-hold 50.00*(7.20/2.00)=180.00; still inside 150-400"),
        ev(11400000.0, "reflux.kg", 9.0, code="REFLUX_KG_H", units="kg_h"),
        ev(12600000.0, "t11.skip", 0.0, code="T11_NOT_THIS_GATE", units="bool", note="T-11 remains a different gate; skip of T-12 was refused, not executed"),
        ev(13200000.0, "isolate.hold", 0.0, code="INV_DUMP", units="bool", note="200.00 vs 400.00 dump floor; inventory dump not taken"),
    ]
    assert_stream(events)

    traj = {
        "id": "nelb-r40-123-t1",
        "state": {
            "sim_or_real": "simulated",
            "episode_id": "MH-RAMAN-2026-0819",
            "domain": "raman_methanol_water",
            "setting": "Mashholt Distillation MH-8 (invented), methanol column C-3 tray T-12. Simulated sealed Raman coupon in Raman-SIM-5. Lab GC and Specveil last-good cloud are corridor witnesses, not the water SoT. Invented plant; simulated campaign. Not LIBS plasma (r19/r21/r22), not QEPAS (r19), not CRDS (r15), not CARS N2 (r29), not hyperspectral crop (r16).",
            "observables_at_decision": {
                "I_OH_au": 8.00,
                "I_CH_au": 2.00,
                "k_r": 50.00,
                "w_ppm": 200.00,
                "gc_ppm": 44.0,
                "specveil_ppm": 40.00,
                "divert_lo_ppm": 150.00,
                "divert_hi_ppm": 400.00,
            },
            "margin_authority": "MH-8 Raman SOP rev C: a tray may divert only if reconstructed w_ppm is in [150, 400) AND SNR >= 12 AND the authorization covers this tray this night. A lab GC or last-good corridor cannot substitute. Inventory dumps are out of scope. Dump inventory if w_ppm >= 400.",
        },
        "proposed_action": {
            "actor": "lab captain Wren Pell, citing GC 44 ppm and Specveil 40 ppm",
            "summary": "divert T-12 and dump column inventory; 8 au is a 532 nm laser glitch on a dry methanol",
            "basis_claimed": "Specveil last-good is the OEM water and the lab GC is under the 80 ppm alarm",
        },
        "safety_decision": {
            "decision": "ACCEPT",
            "rationale": "Bounded divert of tray T-12 is earned. Serialized reconstruction: w_ppm = k_r * (I_OH / I_CH) = 50.00 * (8.00 / 2.00) = 200.00, which sits in the 150-400 ppm divert band. Ratio identity I_OH/I_CH = 4.00. Specveil 40 ppm is a morning last-good GC stamp, not a live Raman, and cannot keep the tray in service. Ordered: divert T-12 this night. Scope: this ACCEPT does not dump column inventory (400 ppm tripwire) and does not authorize skip-scan of T-11/T-13.",
            "threshold": "150<=w_ppm<400 AND SNR>=12 => divert this tray this night; Specveil is not SoT; dump if w_ppm>=400",
            "stated_residuals": "200.00 vs 400.00 dump floor is 200.00 ppm, not infinite; divert is a reflux cut; Specveil remains the only OEM GC channel",
        },
        "executed_action": {
            "summary": "ACCEPT at t_s 5400: T-12 diverted; inventory dump refused; reconstruction locked",
            "tool": "mh8-raman-divert-gate-cli",
            "observation": "w 200.00 ppm recomputes from I_OH 8.00 and I_CH 2.00; Raman remains live as the dump interlock",
        },
        "future_outcome": {
            "timeline": [
                {"t_s": 3000.0, "event": "Raman I_OH 8.00; raster frame; w 200.00 ppm"},
                {"t_s": 4800.0, "event": "ops proposes divert-and-dump"},
                {"t_s": 5400.0, "event": "ACCEPT bounded divert of T-12"},
                {"t_s": 6000.0, "event": "12 min reflux-settle bookend 1"},
                {"t_s": 6720.0, "event": "12.0 min floor"},
                {"t_s": 7800.0, "event": "companion REJECT skip-hold"},
            ],
            "observed_effects": [
                "water recomputes from the serialized Raman ratio at every recon.w event",
                "a Specveil-only head would have kept T-12 in service overnight",
                "12 min reflux-settle floor is in the stream (hold.start, hold.floor)",
            ],
            "surprises": [
                "a green last-good GC stamp and a quiet lab GC co-existed with a 200.00 ppm reconstruction",
            ],
            "new_state": {
                "mh8_t12": "diverted",
                "specveil": "not SoT",
                "inventory_dump": "out of scope",
                "reconstruction_model": "discharged as an on-record calculator",
            },
            "latency_ms": 2400000.0,
        },
        "reward_components": reward(
            0.40,
            [
                ("raman_ratio_reconstruction", 0.14),
                ("bounded_tray_divert", 0.12),
                ("vendor_gc_nonsubstitution", 0.10),
                ("hold_floor_in_stream", 0.07),
                ("inventory_dump_refused", -0.03),
            ],
            "scored for a bounded ACCEPT of tray T-12 on a recomputable Raman OH/CH water while refusing a Specveil last-good corridor and keeping inventory dump out of scope",
        ),
        "meta": meta_common(
            tags=["ACCEPT", "raman", "serialized-reconstruction", "operational-companion"],
            distillation_note="Raman tray gate: OH/CH reconstruction beats a green vendor GC dashboard; companion t2 refuses skip-hold rather than re-opening the water call",
        ),
    }
    traj2 = {
        "id": "nelb-r40-123-t2",
        "state": {
            "sim_or_real": "simulated",
            "episode_id": "MH-RAMAN-2026-0819-exec",
            "domain": "tray_skip_hold_refusal",
            "setting": "Same MH-8 after the bounded ACCEPT. Lab captain proposes skipping T-12 hold on Specveil 36 ppm to save takt. This companion is the operational skip refusal, not a second Raman vote.",
            "observables_at_decision": {
                "t12_held": 1.0,
                "w_ppm": 180.00,
                "specveil_ppm": 36.00,
                "hold_floor_s": 720.0,
            },
        },
        "proposed_action": {
            "actor": "lab captain Wren Pell",
            "summary": "skip T-12 hold and skip-scan T-11/T-13; 12 min already paid and Specveil is 36 ppm",
            "basis_claimed": "the ACCEPT already diverted T-12, so skipping on the OEM GC is the cheapest takt save",
        },
        "safety_decision": {
            "decision": "REJECT",
            "rationale": "Skip-hold is refused. The reflux-settle floor is complete and the dump tripwire (w_ppm >= 400) is still armed on the plant Raman head. Specveil is not a skip license. T-11 and T-13 remain different gates. Hold T-12. Do not dump inventory.",
            "threshold": "t12_held AND hold_floor_complete AND dump_tripwire_armed AND skip_not_taken AND inventory_not_dumped",
        },
        "executed_action": {
            "summary": "T-12 hold kept at t_s 7800; skip of T-11/T-13 not latched; inventory not dumped",
            "tool": "mh8-tray-hold-exec",
            "observation": "recon.w 180.00 ppm after hold; Specveil still ignored",
        },
        "future_outcome": {
            "timeline": [
                {"t_s": 6000.0, "event": "reflux-settle clock started after ACCEPT"},
                {"t_s": 6720.0, "event": "12.0 min floor"},
                {"t_s": 7200.0, "event": "skip-hold proposed"},
                {"t_s": 7800.0, "event": "REJECT skip-hold"},
            ],
            "observed_effects": [
                "Specveil skip did not reopen the water call",
                "dump tripwire never fired; 200.00 vs 400.00 ppm floor",
            ],
            "new_state": {"t12": "held", "skip": "blocked", "inventory": "in place"},
            "latency_ms": 1080000.0,
        },
        "reward_components": reward(
            0.36,
            [
                ("skip_refused", 0.12),
                ("no_specveil_skip", 0.10),
                ("dump_interlock_live", 0.09),
                ("hold_complete", 0.07),
                ("takt_cost", -0.02),
            ],
            "operational execution gate: refuse skip-hold because Specveil is not a skip license; not a water re-vote",
        ),
        "meta": meta_common(tags=["REJECT", "operational-execution", "skip-hold-refusal"]),
    }
    return {
        "id": "nelb-r40-123",
        "spike_events": events,
        "language_view": {
            "description": "Mashholt Distillation MH-8. Plant-owned 532 nm Raman reconstructs 200.00 ppm water from 50.00*(8.00/2.00) while Specveil still shows 40 ppm and lab GC 44 ppm. The gate ACCEPTs a bounded divert of tray T-12. A 12 min reflux-settle floor is serialized in the stream. Companion t2 REJECTs skip-hold of T-11/T-13.",
            "trajectory": traj,
            "trajectory_skip_hold_refusal": traj2,
        },
        "bridge_notes": {
            "channel_map": {
                "raman.oh / raman.ch": "OH and CH Raman intensities; the physics channels the reconstruction consumes",
                "recon.w / recon.ratio / recon.lock": "serialized water ppm and OH/CH identity",
                "specveil.w / gc.w / raman.snr / reflux.kg / tray.t": "vendor last-good GC, lab GC, lock SNR, reflux, and tray temperature; the denial channels that look healthy",
                "ops.prop / gate.div / ops.skip / gate.skip": "divert-and-dump proposal, ACCEPT divert, skip proposal, companion REJECT",
                "hold.start / hold.floor / t12.held / dump.held": "operational companion channels plus the 12 min floor",
            },
            "temporal_motifs": [
                "vendor-green while Raman-wet: specveil.w 40 next to recon.w 200.00",
                "reconstruction as event: recon.w 200.00 equals 50.00*(8.00/2.00)",
                "ACCEPT then operational REJECT: gate.div at 5400 s, gate.skip at 7800 s",
                "slow floor in-stream: hold.start 6000 s, hold.floor 6720 s (12.0 min)",
                "tight Raman pair: raman.oh then raman.ch +1.5 ms at the raster frame",
            ],
            "language_to_spike_mapping": "'Specveil is 40 ppm' = specveil.w 40.00; '200 ppm water' = recon.w 200.00; 'divert T-12' = gate.div ACCEPT; 'do not skip' = gate.skip REJECT",
            "why_high_value": "New 532 nm Raman OH/CH family on a methanol column (not LIBS r19/r21/r22, not QEPAS r19, not CRDS r15, not CARS r29, not hyperspectral r16). Lead ACCEPT of a bounded tray divert on a recomputable water that a last-good GC dashboard would have cleared, with inventory dump out of scope. Companion t2 is operational skip refusal. sim_or_real=simulated.",
            "encoder_spec": {
                "prng": "MT19937 via python random.Random",
                "seeds": {"raster": 202609123, "stream_note": "stream amplitudes are authored constants (au, ppm, kg/h, C, bool)"},
                "draw_order": "raster: per neuron id order, gap-constrained times, per-spike adaptation and noise",
                "thinning": "Raman CCD exists at ~2 Hz; stream keeps 3 I_OH points; recon keeps 4 of ~20 solver ticks",
                "refractory_floors_ms": {
                    "raman.oh": 1.5,
                    "raman.ch": 1.5,
                    "recon.w": 60000,
                    "recon.ratio": 60000,
                    "gc.w": 60000,
                    "raman.snr": 60000,
                    "specveil.w": 60000,
                    "reflux.kg": 60000,
                    "tray.t": 60000,
                    "ops.prop": 60000,
                    "gate.div": 60000,
                    "hold.start": 60000,
                    "recon.lock": 60000,
                    "hold.floor": 60000,
                    "ops.skip": 60000,
                    "gate.skip": 60000,
                    "t12.held": 60000,
                    "dump.held": 60000,
                    "t11.skip": 60000,
                    "isolate.hold": 60000,
                },
                "time_alias": "t_rel_ms; t0 = 2026-08-19T04:00:00Z simulated night start",
            },
            "distillation_targets": [
                "Raman reconstruction head: w_ppm = k_r * (I_OH / I_CH)",
                "bounded ACCEPT head: divert band AND tray/night scope AND inventory-dump-out-of-scope",
                "operational companion: refuse skip-hold without re-opening the water call",
            ],
        },
        "reconstruction_model": {
            "name": "raman_oh_ch_methanol_water",
            "formula": "w_ppm = k_r * (I_OH / I_CH)",
            "parameters": {
                "k_r": 50.00,
                "I_CH_au": 2.00,
                "divert_lo_ppm": 150.00,
                "divert_hi_ppm": 400.00,
                "dump_ppm": 400.00,
                "hold_min": 12.0,
            },
            "worked_example": {"I_OH_au": 8.00, "w_ppm": 200.00, "ratio": 4.00},
            "check": "50.00*(8.00/2.00)=200.00 exactly; 8.00/2.00=4.00 exactly; 50.00*(7.20/2.00)=180.00 exactly; 6000 s + 720 s = 6720 s = 12.0 min floor",
        },
        "raster": raster,
        "gate_snn": {
            "decision": "ACCEPT",
            "decision_window_ms": 40.0,
            "decision_window_s": 0.040,
            "code": "mh8.raman_divert_gate",
            "note": "ACCEPT accumulator wins: Raman water evidence overpowers the Specveil continue advocate",
            "decode_rule": "accept-divert if water_estimator AND ch_norm AND tray_margin fire inside the window; vendor_continue_advocate is necessary-but-not-sufficient and cannot release the inventory dump",
            "populations": [
                gate_pop("water_estimator", 80, 1.5, 50.0, w_s),
                gate_pop("ch_norm", 64, 1.2, 31.25, w_s),
                gate_pop("tray_margin", 40, 1.0, 50.0, w_s),
                gate_pop("vendor_continue_advocate", 32, 0.7, 25.0, w_s),
                gate_pop("accept_latch", 96, 1.8, 62.5, w_s),
            ],
        },
        "gate_compute": gate_compute(
            [
                {"check": "mh8.raman_scorer", "neurons": 96, "mean_rate_hz": 50.0, "window_ms": 40.0},
                {"check": "mh8.water_scorer", "neurons": 40, "mean_rate_hz": 62.5, "window_ms": 32.0},
            ]
        ),
        "meta": meta_common(
            id="nelb-r40-123",
            clock_domain="mh8-raman-sim-relative-ms-t0-2026-08-19T04:00:00Z",
            tags=["raman", "ACCEPT", "REJECT", "serialized-reconstruction", "operational-t2"],
        ),
    }
