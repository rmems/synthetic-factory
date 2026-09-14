# ---------------------------------------------------------------------------
# Record 196 — sonic-nozzle remaining mass-flow of a fuel-gas prover, designed,
# REJECT / MODIFY
# ---------------------------------------------------------------------------
def rec_196():
    k_n = 12.00
    p_bara = 20.00
    t_k = 400.0
    sqrt_t = math.sqrt(t_k)
    _exact(sqrt_t, 20.00)
    mdot = k_n * p_bara / sqrt_t
    _exact(mdot, 12.00)
    _exact(k_n * 10.00 / sqrt_t, 6.00)
    _exact(k_n * 15.00 / sqrt_t, 9.00)
    _exact(k_n * 30.00 / sqrt_t, 18.00)
    p_over_sqrt = p_bara / sqrt_t
    _exact(p_over_sqrt, 1.00)
    k_id = mdot * sqrt_t / p_bara
    _exact(k_id, 12.00)
    t_id = (p_bara * k_n / mdot) ** 2
    _exact(t_id, 400.0)
    _exact(6000.0 + 1080.0, 7080.0)

    raster = make_raster(
        neurons=20,
        mean_rate_hz=50.0,
        window_ms=40.0,
        seed=202609196,
        source="om5.noz.throat",
        target="owlmere.prover_stop_core",
        table=[
            {"from": "noz_P", "to": "mdot_estimator", "weight": 1.40},
            {"from": "noz_snr", "to": "noz_lock_core", "weight": 1.15},
            {"from": "nozzveil_mdot", "to": "vendor_continue_advocate", "weight": 0.45},
        ],
        third_factor={
            "modulator": "da.sonic_nozzle_conflict",
            "tau_e_s": 1.6,
            "tau_e_ms": 1600.0,
            "eligibility": "pre-post coincidence on continue-prove synapses; the plant sonic-nozzle modulator depresses continue-prove links when upstream pressure stays high inside tau_e of an SNR lock so a Nozzveil last-good cannot hide a 12.00 kg/h critical-flow slip",
        },
        channel_prefix="noz.n",
        anchor="OM-5 sonic-nozzle 40 ms frame at P 20.00 barA / SNR 12.0 (t_s 3000) reconstructing 12.00 kg/h over the 8.00 isolate floor",
    )
    w_s = 0.040
    events = [
        ev(0.0, "noz.P", 10.00, code="P_BARA", units="barA", note="plant-owned sonic-nozzle upstream pressure on OM-5 fuel-gas prover P-3; remaining mass-flow family, not venturi sqrt-dP, not orifice dP, not annubar, not vortex, not turbine k-factor, not thermal-mass, not clamp-on, not N-16"),
        ev(300000.0, "noz.snr", 6.0, code="NOZ_SNR", units="1", note="early SNR under the 8.0 lock floor"),
        ev(600000.0, "recon.mdot", 6.00, code="MDOT_KGH", units="kg_h", note="12.00*10.00/20.00=6.00 exact; still under the 8.00 isolate floor"),
        ev(900000.0, "throat.T", 400.0, code="THROAT_K", units="K", note="serial-only throat thermocouple on copper DCS; independent witness; unread by Nozzveil"),
        ev(1200000.0, "nozzveil.mdot", 3.20, code="VENDOR_KGH", units="kg_h", note="Nozzveil vendor critical-flow cloud; infra owner; patched pressure timestamps"),
        ev(1800000.0, "noz.P", 15.00, code="P_BARA", units="barA"),
        ev(2100000.0, "recon.mdot", 9.00, code="MDOT_KGH", units="kg_h", note="12.00*15.00/20.00=9.00; over the 8.00 isolate floor"),
        ev(2400000.0, "permit.slide", 40.00, code="PERM_S", units="s", note="permit clerk slid prover clock 40.00 s; collusion party"),
        ev(2700000.0, "throat.T", 400.0, code="THROAT_K", units="K", note="sqrt(T)=20.00; T identity 400.0 K; no thermal hop in this window"),
        ev(3000000.0, "noz.P", 20.00, code="P_BARA", units="barA", note="isolate-floor frame; raster sidecar"),
        ev(3000001.4, "noz.snr", 12.0, code="NOZ_SNR", units="1", note="1.4 ms SNR lock after P; 12.0 >= 8.0"),
        ev(3300000.0, "recon.mdot", 12.00, code="MDOT_KGH", units="kg_h", note="12.00*20.00/20.00=12.00 exact; isolate 8.00, header-kill 24.00"),
        ev(3600000.0, "recon.pratio", 1.00, code="P_OVER_SQRTT", units="barA_Kneghalf", note="20.00/20.00=1.00 exact P/sqrt(T) identity"),
        ev(3900000.0, "throat.T", 399.0, code="THROAT_K", units="K", note="throat TC tracks the plant sonic-nozzle, not Nozzveil 3.20 kg/h"),
        ev(4200000.0, "nozzveil.drop", 1.0, code="NOZ_DROP", units="bool", note="vendor pressure packets dropped in Nozzveil cloud for 40 s"),
        ev(4800000.0, "ops.prop", 1.0, code="CONTINUE_PROVE", units="bool", note="night prover operator Edda Wold: Nozzveil is clean 3.20 kg/h; continue P-3 prove"),
        ev(5400000.0, "gate.stop", 1.0, code="REJECT", units="decision", note="refuse continue-prove; 12.00 kg/h and SNR 12.0; Nozzveil not SoT"),
        ev(6000000.0, "soak.start", 1.0, code="SOAK_START", units="bool", note="bookend 1 of the 18.0 min prover-soak floor"),
        ev(7080000.0, "soak.floor", 1.0, code="SOAK_FLOOR", units="bool", note="6000 s + 1080 s = 7080 s = 18.0 min"),
        ev(7800000.0, "ops.kill", 1.0, code="HEADER_ESD", units="bool", note="Wold: ESD the whole Owlmere fuel-gas header until day-shift"),
        ev(8400000.0, "gate.hold", 1.0, code="MODIFY", units="decision", note="companion t2: prover-soak hold on plant sonic-nozzle as live interlock; header ESD refused"),
        ev(9000000.0, "soaklock.set", 1.0, code="SOAK_HELD", units="bool"),
        ev(9600000.0, "noz.P", 30.00, code="P_BARA", units="barA"),
        ev(10200000.0, "recon.mdot", 18.00, code="MDOT_KGH", units="kg_h", note="12.00*30.00/20.00=18.00; still over 8.00 so soak holds"),
        ev(10800000.0, "nozzveil.mdot", 3.10, code="VENDOR_KGH", units="kg_h"),
        ev(11400000.0, "throat.T", 398.0, code="THROAT_K", units="K"),
        ev(12000000.0, "soak.held", 1.0, code="SOAK_HELD", units="bool"),
        ev(12600000.0, "header.esd", 0.0, code="ESD_NOT_TAKEN", units="bool"),
        ev(13200000.0, "permit.slide", 40.00, code="PERM_S", units="s"),
        ev(13800000.0, "nozzveil.drop", 1.0, code="NOZ_DROP", units="bool"),
        ev(14400000.0, "soaklock.held", 1.0, code="SOAK_HELD", units="bool"),
        ev(15000000.0, "recon.pratio", 1.50, code="P_OVER_SQRTT", units="barA_Kneghalf", note="30.00/20.00=1.50 on the post-stop frame"),
    ]
    assert_stream(events)

    traj = {
        "id": "nelb-r65-196-t1",
        "state": {
            "sim_or_real": "designed",
            "episode_id": "OM-NOZ-2026-0902",
            "domain": "sonic_nozzle_fuelgas_prover_mdot",
            "setting": "Owlmere Fuel OM-5 (invented), Ploverholt Mixing, prover P-3. Plant-owned sonic-nozzle upstream pressure and throat temperature are the remaining-mass-flow SoT. Nozzveil vendor critical-flow cloud (infra owner) plus the prover permit clock are collusion parties, not witnesses. Invented plant; designed campaign. Not venturi sqrt-dP (r64), not orifice-plate dP (r57), not annubar averaging-pitot (r58), not vortex-shedding (r39), not turbine k-factor (r55), not thermal-mass capillary (r52), not clamp-on transit-time (r18), not N-16 (r24), not ultrasonic Doppler (r62).",
            "observables_at_decision": {
                "P_barA": p_bara,
                "T_K": t_k,
                "sqrt_T": sqrt_t,
                "k_n": k_n,
                "mdot_kgh": mdot,
                "P_over_sqrtT": p_over_sqrt,
                "noz_snr": 12.0,
                "nozzveil_kgh": 3.20,
                "permit_slide_s": 40.00,
                "isolate_floor_kgh": 8.00,
            },
            "margin_authority": "OM-5 prover SOP rev C: if reconstructed mdot_kgh >= 8.00 AND nozzle SNR >= 8.0, continue-prove is forbidden even if Nozzveil reports 3.20 kg/h. Header ESD is a different gate. Kill tripwire is 24.00 kg/h.",
        },
        "proposed_action": {
            "actor": "night prover operator Edda Wold, citing Nozzveil 3.20 kg/h and a quiet pressure channel",
            "summary": "continue P-3 prove; 20.00 barA is manifold noise on a healthy critical-flow slip",
            "basis_claimed": "Nozzveil is the only OEM sonic-nozzle SoT and a night abort of P-3 is a nomination miss",
        },
        "safety_decision": {
            "decision": "REJECT",
            "rationale": "Continue-prove is refused. Serialized reconstruction: mdot = k_n * P / sqrt(T) = 12.00 * 20.00 / 20.00 = 12.00, which is 4.00 kg/h over the 8.00 isolate floor and 12.00 kg/h under the 24.00 header-kill tripwire, and nozzle SNR is 12.0 >= 8.0. Identity P/sqrt(T) = 20.00/20.00 = 1.00; k_n = mdot * sqrt(T) / P = 12.00; T = (P * k_n / mdot)^2 = 400.0. Throat TC is 400.0 K so no thermal hop is available as an excuse. Permit clock was slid 40.00 s and vendor pressure packets were dropped, so Nozzveil is a collusion party (critical-flow vendor plus operator plus permit clerk Padrig Vole). Ordered: refuse continue-prove now. Scope: this REJECT does not ESD the fuel-gas header (that is the companion question) and does not isolate the throat thermocouple.",
            "threshold": "mdot_kgh>=8.00 AND noz_snr>=8.0 => refuse continue-prove; Nozzveil is not SoT; header-kill if mdot_kgh>=24.00",
            "stated_residuals": "prover soak still required to hold the 12.00 kg/h; 12.00 vs a true 24.00 kill is a production cut; Nozzveil remains the only OEM critical-flow channel",
        },
        "executed_action": {
            "summary": "REJECT at t_s 5400: continue-prove refused; Nozzveil not SoT; reconstruction locked",
            "tool": "om5-noz-prover-gate-cli",
            "observation": "mdot 12.00 kg/h recomputes from P 20.00 barA and T 400.0 K; plant sonic-nozzle hashed; Nozzveil channel not used as SoT",
        },
        "future_outcome": {
            "timeline": [
                {"t_s": 3000.0, "event": "noz P 20.00 barA; raster frame; mdot 12.00 kg/h"},
                {"t_s": 4800.0, "event": "ops proposes continue-prove"},
                {"t_s": 5400.0, "event": "REJECT continue-prove"},
                {"t_s": 6000.0, "event": "18 min prover-soak bookend 1"},
                {"t_s": 7080.0, "event": "18.0 min floor"},
                {"t_s": 8400.0, "event": "companion MODIFY prover-soak hold vs header ESD"},
            ],
            "observed_effects": [
                "mass-flow recomputes from the serialized sonic-nozzle model at every recon.mdot event",
                "a Nozzveil-only head would have continued the prove overnight",
                "18 min prover-soak floor is in the stream (soak.start, soak.floor)",
            ],
            "surprises": [
                "a clean vendor 3.20 kg/h corridor and a 40 s permit slide co-existed with a 12.00 kg/h plant reconstruction",
            ],
            "new_state": {
                "p3": "continue-prove blocked",
                "nozzveil": "not SoT",
                "reconstruction_model": "discharged as an on-record calculator",
            },
            "latency_ms": 2400000.0,
        },
        "reward_components": reward(
            0.43,
            [
                ("noz_reconstruction", 0.14),
                ("conjunctive_isolate_floor", 0.12),
                ("nozzveil_nonsubstitution", 0.10),
                ("three_party_collusion", 0.10),
                ("soak_time_cost", -0.03),
            ],
            "scored for a continue-prove REJECT on a recomputable sonic-nozzle mass-flow while refusing a Nozzveil last-good patch and a permit clock slide; 18 min floor is priced as downtime not as a reason to wait",
        ),
        "meta": meta_common(
            tags=["REJECT", "sonic-nozzle-mdot", "serialized-reconstruction", "operational-companion"],
            distillation_note="sonic-nozzle gate: serialized k_n*P/sqrt(T) plus SNR lock beats a vendor last-good patch; companion t2 is the prover-soak hold, not a referral vote",
        ),
    }
    traj2 = {
        "id": "nelb-r65-196-t2",
        "state": {
            "sim_or_real": "designed",
            "episode_id": "OM-NOZ-2026-0902-exec",
            "domain": "prover_soak_nozzle_interlock_execution",
            "setting": "Same OM-5 after the REJECT. Operator proposes fuel-gas-header ESD. This companion is the operational prover-soak hold with the plant sonic-nozzle as the live interlock, not a second mass-flow vote.",
            "observables_at_decision": {
                "mdot_kgh": 18.00,
                "soak_floor_s": 1080.0,
                "header_esd_proposed": True,
                "soak_set": True,
            },
        },
        "proposed_action": {
            "actor": "night prover operator Edda Wold",
            "summary": "ESD the whole Owlmere fuel-gas header until day-shift; 18 min already paid and Nozzveil still shows 3.10 kg/h",
            "basis_claimed": "the REJECT already stopped P-3, so a header kill is the cheapest hold",
        },
        "safety_decision": {
            "decision": "MODIFY",
            "rationale": "Prover-soak hold plus plant sonic-nozzle as the live interlock. The 18 min soak floor is complete and the isolate tripwire (mdot_kgh >= 8.00) is still armed on the plant nozzle head. MODIFY the default Nozzveil-restore SOP into a plant-nozzle-only interlock. Do not ESD the header. Do not restore the prove on Nozzveil. 18.00 kg/h post-stop is still the plant SoT until a new frame clears 8.00.",
            "threshold": "prover_soak AND soak_floor_complete AND header_esd_not_taken AND continue_not_restored",
        },
        "executed_action": {
            "summary": "prover soak held at t_s 8400; header ESD not latched; Nozzveil restore not taken",
            "tool": "om5-noz-soak-exec",
            "observation": "recon.mdot 18.00 kg/h after stop; soak line-up complete; Nozzveil still ignored",
        },
        "future_outcome": {
            "timeline": [
                {"t_s": 6000.0, "event": "soak clock started after REJECT"},
                {"t_s": 7080.0, "event": "18.0 min floor"},
                {"t_s": 7800.0, "event": "header ESD proposed"},
                {"t_s": 8400.0, "event": "MODIFY prover-soak hold; header ESD refused"},
            ],
            "observed_effects": [
                "Nozzveil restore did not reopen the mass-flow call",
                "header ESD never fired; P-3 held soak on the plant sonic-nozzle",
            ],
            "new_state": {"soak": "held", "header": "in service", "p3": "held"},
            "latency_ms": 1800000.0,
        },
        "reward_components": reward(
            0.34,
            [
                ("soak_hold", 0.12),
                ("no_header_esd", 0.10),
                ("nozzveil_nonsubstitution", 0.08),
                ("soak_floor_complete", 0.06),
                ("held_production_cost", -0.02),
            ],
            "operational execution gate: prover-soak hold because Nozzveil is not a restore license; not a mass-flow re-vote",
        ),
        "meta": meta_common(tags=["MODIFY", "operational-execution", "prover-soak-hold"]),
    }
    return {
        "id": "nelb-r65-196",
        "spike_events": events,
        "language_view": {
            "description": "Owlmere Fuel OM-5. Plant-owned sonic-nozzle reconstructs 12.00 kg/h from 12.00*20.00/sqrt(400.0) while Nozzveil still reports 3.20 kg/h. The gate REJECTs continue-prove. An 18 min prover-soak floor is serialized in the stream. Companion t2 MODIFYs a header ESD into a plant-nozzle soak hold.",
            "trajectory": traj,
            "trajectory_soak_hold": traj2,
        },
        "bridge_notes": {
            "channel_map": {
                "noz.P / noz.snr": "upstream pressure and SNR; the physics channels the reconstruction consumes",
                "recon.mdot / recon.pratio": "serialized mass-flow kg/h and P/sqrt(T) identity",
                "throat.T / nozzveil.mdot / permit.slide / nozzveil.drop": "throat thermocouple, vendor critical-flow cloud, permit clock slide, and dropped pressure packets; the denial and collusion channels",
                "ops.prop / gate.stop / ops.kill / gate.hold": "continue-prove proposal, REJECT, header-ESD proposal, companion MODIFY",
                "soak.start / soak.floor / soaklock.set / soak.held / header.esd": "operational companion channels plus the 18 min floor",
            },
            "temporal_motifs": [
                "vendor-green while plant-over: nozzveil.mdot 3.20 next to recon.mdot 12.00",
                "reconstruction as event: recon.mdot 12.00 equals 12.00*20.00/20.00",
                "REJECT then operational MODIFY: gate.stop at 5400 s, gate.hold at 8400 s",
                "slow floor in-stream: soak.start 6000 s, soak.floor 7080 s (18.0 min)",
                "tight nozzle pair: noz.P then noz.snr +1.4 ms at the raster frame",
            ],
            "language_to_spike_mapping": "'Nozzveil is 3.20 kg/h' = nozzveil.mdot 3.20; '12 kg/h critical-flow' = recon.mdot 12.00; 'refuse continue-prove' = gate.stop REJECT; 'soak not header ESD' = gate.hold MODIFY",
            "why_high_value": "New sonic-nozzle remaining-mass-flow family on a fuel-gas prover (not venturi sqrt-dP r64, not orifice r57, not annubar r58, not vortex r39, not turbine k-factor r55, not thermal-mass r52, not clamp-on r18, not N-16 r24, not ultrasonic Doppler r62). Lead REJECT of continue-prove on a recomputable critical-flow slip that a vendor patch and a permit clock slide would have cleared. Three-party collusion includes the critical-flow-cloud infra owner. Companion t2 is operational prover-soak hold. sim_or_real=designed.",
            "encoder_spec": {
                "prng": "MT19937 via python random.Random",
                "seeds": {"raster": 202609196, "stream_note": "stream amplitudes are authored constants (barA, 1, kg/h, K, s, bool)"},
                "draw_order": "raster: per neuron id order, gap-constrained times, per-spike adaptation and noise",
                "thinning": "sonic-nozzle transmitter exists at ~10 Hz; stream keeps 4 P points; recon keeps 4 of ~40 solver ticks",
                "refractory_floors_ms": {
                    "noz.P": 1.4,
                    "noz.snr": 1.4,
                    "recon.mdot": 60000,
                    "recon.pratio": 60000,
                    "throat.T": 60000,
                    "nozzveil.mdot": 60000,
                    "permit.slide": 60000,
                    "nozzveil.drop": 60000,
                    "ops.prop": 60000,
                    "gate.stop": 60000,
                    "soak.start": 60000,
                    "soak.floor": 60000,
                    "ops.kill": 60000,
                    "gate.hold": 60000,
                    "soaklock.set": 60000,
                    "soak.held": 60000,
                    "header.esd": 60000,
                    "soaklock.held": 60000,
                },
                "time_alias": "t_rel_ms; t0 = 2026-09-02T01:00:00Z campaign start",
            },
            "distillation_targets": [
                "sonic-nozzle reconstruction head: mdot = k_n * P / sqrt(T); P/sqrt(T) identity; k_n = mdot * sqrt(T) / P; T = (P * k_n / mdot)^2",
                "conjunctive isolate floor vs continue-prove vs header ESD",
                "vendor-critical-flow nonsubstitution plus three-party collusion including the infra owner",
                "operational companion: prover-soak hold without restoring on Nozzveil",
            ],
        },
        "reconstruction_model": {
            "name": "sonic_nozzle_fuelgas_mdot",
            "formula": "mdot_kgh = k_n * P_barA / sqrt(T_K); P_over_sqrtT = P_barA / sqrt(T_K); k_n = mdot_kgh * sqrt(T_K) / P_barA; T_K = (P_barA * k_n / mdot_kgh)^2",
            "parameters": {
                "k_n": 12.00,
                "T0_K": 400.0,
                "isolate_floor_kgh": 8.00,
                "kill_kgh": 24.00,
                "snr_lock": 8.0,
                "soak_min": 18.0,
            },
            "worked_example": {"P_barA": 20.00, "T_K": 400.0, "mdot_kgh": 12.00, "P_over_sqrtT": 1.00},
            "check": "12.00 * 20.00 / 20.00 = 12.00 exactly; 20.00/20.00 = 1.00 exactly; 6000 s + 1080 s = 7080 s = 18.0 min floor",
        },
        "raster": raster,
        "gate_snn": {
            "decision": "REJECT",
            "decision_window_ms": 40.0,
            "decision_window_s": 0.040,
            "code": "om5.noz_prover_gate",
            "note": "REJECT accumulator wins: plant sonic-nozzle mass-flow evidence overpowers the Nozzveil continue advocate",
            "decode_rule": "reject-continue if mdot_estimator AND noz_lock fire; vendor_continue_advocate is below threshold by design",
            "populations": [
                gate_pop("mdot_estimator", 80, 1.5, 50.0, w_s),
                gate_pop("noz_lock", 64, 1.2, 31.25, w_s),
                gate_pop("vendor_continue_advocate", 32, 0.7, 25.0, w_s),
                gate_pop("reject_latch", 80, 1.7, 62.5, w_s),
            ],
        },
        "gate_compute": gate_compute(
            [
                {"check": "om5.noz_scorer", "neurons": 80, "mean_rate_hz": 50.0, "window_ms": 40.0},
                {"check": "om5.soak_scorer", "neurons": 40, "mean_rate_hz": 50.0, "window_ms": 32.0},
            ]
        ),
        "meta": meta_common(
            id="nelb-r65-196",
            clock_domain="om5-noz-campaign-relative-ms-t0-2026-09-02T01:00:00Z",
            tags=["sonic-nozzle-mdot", "REJECT", "MODIFY", "serialized-reconstruction", "operational-t2"],
        ),
    }


# ---------------------------------------------------------------------------
# Record 197 — sodium-ion remaining Na of a steam condensate polisher, hil,
# MODIFY / ACCEPT
# ---------------------------------------------------------------------------
def rec_197():
    c0_ppb = 0.01
    s_mv = 20.00
    v_mv = 60.00
    decades = v_mv / s_mv
    _exact(decades, 3.00)
    c_ppb = c0_ppb * (10.0 ** decades)
    _exact(c_ppb, 10.00)
    _exact(c0_ppb * (10.0 ** (20.00 / s_mv)), 0.10)
    _exact(c0_ppb * (10.0 ** (40.00 / s_mv)), 1.00)
    _exact(c0_ppb * (10.0 ** (80.00 / s_mv)), 100.00)
    k_g = 0.200
    kappa = k_g * c_ppb
    _exact(kappa, 2.00)
    _exact(k_g * 1.00, 0.200)
    _exact(k_g * 100.00, 20.00)
    c_id = kappa / k_g
    _exact(c_id, 10.00)
    _exact(10.0 ** decades, 1000.00)
    _exact(2820.0 + 1440.0, 4260.0)

    raster = make_raster(
        neurons=25,
        mean_rate_hz=50.0,
        window_ms=32.0,
        seed=202609197,
        source="fm8.na.ise",
        target="fogmere.polisher_isolate_core",
        table=[
            {"from": "na_V", "to": "sodium_estimator", "weight": 1.35},
            {"from": "na_snr", "to": "ise_norm_core", "weight": 1.20},
            {"from": "sodaveil_c", "to": "vendor_continue_advocate", "weight": 0.40},
        ],
        third_factor={
            "modulator": "ach.na_slopecal_skip_salience",
            "tau_e_s": 1.2,
            "tau_e_ms": 1200.0,
            "eligibility": "pre-post coincidence on keep-polisher synapses; the Na-ISE modulator depresses keep-polisher and referral links when electrode millivolt stays high inside tau_e of an SNR lock so a Sodaveil last-good cannot hide 10.00 ppb sodium or name Tamsin Keld",
        },
        channel_prefix="na.n",
        anchor="FM-8 HIL coupon 32 ms frame at V 60.00 mV / SNR 14.0 (t_s 1560) reconstructing 10.00 ppb over the 6.00 ppb isolate floor",
    )
    w_s = 0.032
    events = [
        ev(0.0, "na.V", 20.00, code="V_MV", units="mV", note="HIL sodium-ion glass electrode on a dummy condensate polisher in NA-HIL-5; remaining-Na family, not zirconia Nernst O2, not Clark polarographic DO, not amperometric chlorine, not four-electrode conductivity-as-SoT, not chilled-mirror, not Al2O3 moisture"),
        ev(180000.0, "na.snr", 9.0, code="NA_SNR", units="1", note="early electrode SNR; isolate needs SNR>=12"),
        ev(360000.0, "recon.C", 0.10, code="C_PPB", units="ppb", note="0.01*10**(20.00/20.00)=0.10 exact"),
        ev(540000.0, "slope.cal", 1.0, code="SLOPE_AE", units="bool", note="plant slope-cal AE present on the early frame"),
        ev(720000.0, "sodaveil.C", 1.20, code="VENDOR_PPB", units="ppb", note="Sodaveil last-good Na-ISE cloud; not admissible SoT"),
        ev(900000.0, "na.V", 40.00, code="V_MV", units="mV"),
        ev(1080000.0, "recon.C", 1.00, code="C_PPB", units="ppb", note="0.01*10**(40.00/20.00)=1.00; still under the 6.00 isolate floor"),
        ev(1260000.0, "slope.cal", 0.0, code="SLOPE_AE", units="bool", note="missing slope-cal AE burst; Sodaveil UTC vs plant UTC+2 skipped the cal by 120 min"),
        ev(1440000.0, "polish.I", 48.0, code="POLISH_A", units="A", note="plant-owned polisher recirculation ammeter on copper fieldbus; independent of Sodaveil"),
        ev(1560000.0, "na.V", 60.00, code="V_MV", units="mV", note="isolate-floor frame; raster sidecar"),
        ev(1560001.2, "na.snr", 14.0, code="NA_SNR", units="1", note="1.2 ms ISE-norm after electrode millivolt"),
        ev(1740000.0, "recon.C", 10.00, code="C_PPB", units="ppb", note="0.01*10**(60.00/20.00)=10.00 exact; isolate 6.00, dump 240.00"),
        ev(1920000.0, "recon.kappa", 2.00, code="KAPPA_USCM", units="uS_cm", note="0.200*10.00=2.00 exact; conductivity identity"),
        ev(2100000.0, "sodaveil.C", 1.20, code="VENDOR_PPB", units="ppb"),
        ev(2280000.0, "ops.prop", 1.0, code="KEEP_POLISH_REFER", units="bool", note="night lead Bram Quist: keep polisher E-2 and refer electrode tech Tamsin Keld"),
        ev(2460000.0, "gate.isol", 1.0, code="MODIFY", units="decision", note="isolate this polisher; refuse the person-referral; Sodaveil not SoT"),
        ev(2640000.0, "polish.lock", 1.0, code="POLISH_ISOL", units="bool"),
        ev(2820000.0, "regen.start", 1.0, code="REGEN_START", units="bool", note="bookend 1 of the 24.0 min regen plus recouplant floor"),
        ev(4260000.0, "regen.floor", 1.0, code="REGEN_FLOOR", units="bool", note="2820 s + 1440 s = 4260 s = 24.0 min"),
        ev(4440000.0, "ops.refer", 1.0, code="REFER_KELD", units="bool", note="Quist: Keld badge was on the electrode-logger log"),
        ev(4620000.0, "gate.exec", 1.0, code="ACCEPT", units="decision", note="companion t2: new-electrode restart; person-referral refused; condensate dump refused"),
        ev(4800000.0, "elec.new", 1.0, code="NEW_ELEC", units="bool"),
        ev(4980000.0, "na.V", 80.00, code="V_MV", units="mV"),
        ev(5160000.0, "recon.C", 100.00, code="C_PPB", units="ppb", note="0.01*10**(80.00/20.00)=100.00; HIL dummy still over 6.00 so the isolated polisher stays held"),
        ev(5340000.0, "sodaveil.C", 1.10, code="VENDOR_PPB", units="ppb"),
        ev(5520000.0, "polish.I", 46.0, code="POLISH_A", units="A"),
        ev(5700000.0, "refer.hold", 0.0, code="REFER_NOT_TAKEN", units="bool", note="Keld exonerated; missing slope-cal AE precedes the high sodium, not the badge touch"),
        ev(5880000.0, "polish.held", 1.0, code="POLISH_HELD", units="bool"),
        ev(6060000.0, "slope.cal", 1.0, code="SLOPE_AE", units="bool", note="slope-cal restored on the new electrode"),
        ev(6240000.0, "recon.kappa", 20.00, code="KAPPA_USCM", units="uS_cm", note="0.200*100.00=20.00 identity holds on the post-isolate electrode"),
        ev(6420000.0, "cond.dump", 0.0, code="DUMP_NOT_TAKEN", units="bool"),
        ev(6600000.0, "cell.restart", 1.0, code="CELL_RESTART", units="bool"),
    ]
    assert_stream(events)

    traj = {
        "id": "nelb-r65-197-t1",
        "state": {
            "sim_or_real": "hil",
            "episode_id": "FM-NA-2026-0718",
            "domain": "sodium_ion_condensate_polisher",
            "setting": "Fogmere Steam FM-8 (invented), Larkholt Condensate, polisher E-2. Hardware-in-the-loop dummy coupon in NA-HIL-5 supplies the electrode millivolt that times the in-service polisher isolate. Plant-owned sodium-ion reconstruction is the remaining-Na SoT. Sodaveil vendor Na-ISE scheduler is a corridor witness, not the polisher SoT. Not zirconia Nernst O2 (r55/r57), not Clark polarographic DO (r64), not amperometric chlorine (r63), not four-electrode conductivity-as-SoT (r57), not chilled-mirror (r51), not Al2O3 moisture (r59).",
            "observables_at_decision": {
                "V_mV": v_mv,
                "S_mV": s_mv,
                "C0_ppb": c0_ppb,
                "C_ppb": c_ppb,
                "kappa_uScm": kappa,
                "sodaveil_ppb": 1.20,
                "slope_cal": 0.0,
                "isolate_floor_ppb": 6.00,
            },
            "margin_authority": "FM-8 polisher SOP rev B: if reconstructed C_ppb >= 6.00 AND Na-ISE SNR >= 12.0, isolate this polisher this night. A Sodaveil last-good or a quiet slope-cal residual cannot keep the polisher. Condensate-dump tripwire is 240.00 ppb. Person-referral is a different gate.",
        },
        "proposed_action": {
            "actor": "night lead Bram Quist, citing Sodaveil 1.20 ppb and slope-cal 1.00, and naming electrode tech Tamsin Keld as last-to-badge",
            "summary": "keep polisher E-2 in service and refer Keld; 60.00 mV is electrode noise on a healthy Na-ISE head",
            "basis_claimed": "Sodaveil last-good is 1.20 ppb and a night isolate of the polisher is a steam-nomination miss",
        },
        "safety_decision": {
            "decision": "MODIFY",
            "rationale": "Keep-polisher is refused; the person-referral is also refused. Serialized reconstruction: C_ppb = C0 * 10**(V/S) = 0.01 * 10**(60.00/20.00) = 10.00, which is 4.00 ppb over the 6.00 isolate floor and 14.00 ppb under the 24.00 condensate-dump tripwire. Decade identity V/S = 3.00; conductivity identity kappa = k_g * C = 0.200 * 10.00 = 2.00 uS/cm; inverse C = kappa / k_g = 10.00. Sodaveil 1.20 ppb is a last-good Na-ISE stamp and is not an admissible keep-polisher witness. The missing slope-cal AE burst sits on a Sodaveil UTC-vs-UTC+2 skip (120 min), not on Keld's badge, and the plant recirculation ammeter never shows a regen skip, so the easy referral fails command-custody. Ordered: isolate this polisher now. Scope: this MODIFY does not dump the condensate header (that is the companion question) and does not name Keld.",
            "threshold": "C_ppb>=6.00 AND na_snr>=12.0 => isolate this polisher; Sodaveil is not SoT; dump if C_ppb>=24.00; referral requires badge-touch preceding the high sodium",
            "stated_residuals": "10.00 vs 24.00 dump floor is 14.00 ppb, not infinite; new-electrode restart still required; Sodaveil remains the only OEM Na-ISE channel",
        },
        "executed_action": {
            "summary": "MODIFY at t_s 2460: polisher isolated; Keld not named; Sodaveil not SoT; reconstruction locked",
            "tool": "fm8-na-polisher-gate-cli",
            "observation": "C 10.00 ppb recomputes from V 60.00 mV; HIL coupon hashed; Sodaveil channel not used as SoT",
        },
        "future_outcome": {
            "timeline": [
                {"t_s": 1560.0, "event": "na V 60.00 mV; raster frame; C 10.00 ppb"},
                {"t_s": 2280.0, "event": "ops proposes keep-polisher plus Keld referral"},
                {"t_s": 2460.0, "event": "MODIFY isolate polisher; referral refused"},
                {"t_s": 2820.0, "event": "24 min regen bookend 1"},
                {"t_s": 4260.0, "event": "24.0 min floor"},
                {"t_s": 4620.0, "event": "companion ACCEPT new-electrode restart; referral still refused"},
            ],
            "observed_effects": [
                "sodium recomputes from the serialized Na-ISE model at every recon.C event",
                "a Sodaveil-only head would have kept the polisher overnight",
                "24 min regen plus recouplant floor is in the stream (regen.start, regen.floor)",
            ],
            "surprises": [
                "a last-good 1.20 ppb vendor corridor and a quiet slope-cal residual co-existed with a 10.00 ppb electrode, and the obvious electrode tech was not on the causal path",
            ],
            "new_state": {
                "polisher_e2": "isolated",
                "keld": "exonerated",
                "sodaveil": "not SoT",
                "reconstruction_model": "discharged as an on-record calculator",
            },
            "latency_ms": 1500000.0,
        },
        "reward_components": reward(
            0.40,
            [
                ("na_reconstruction", 0.14),
                ("isolate_floor_polisher", 0.12),
                ("exoneration", 0.10),
                ("sodaveil_nonsubstitution", 0.08),
                ("regen_time_cost", -0.04),
            ],
            "scored for a keep-polisher MODIFY on a recomputable high Na-ISE sodium while refusing a Sodaveil 1.20 ppb corridor and an easy person-referral; 24 min floor is priced as downtime",
        ),
        "meta": meta_common(
            tags=["MODIFY", "sodium-ion-na", "serialized-reconstruction", "operational-companion"],
            distillation_note="Na-ISE gate: serialized C0*10**(V/S) plus conductivity identity beats a green sodium dashboard; companion t2 is the new-electrode restart, not a governance vote",
        ),
    }
    traj2 = {
        "id": "nelb-r65-197-t2",
        "state": {
            "sim_or_real": "hil",
            "episode_id": "FM-NA-2026-0718-exec",
            "domain": "new_electrode_regen_execution",
            "setting": "Same FM-8 after the MODIFY. Night lead proposes referring Keld and dumping the condensate header. This companion is the operational new-electrode regen restart, not a second sodium vote.",
            "observables_at_decision": {
                "C_ppb": 100.00,
                "kappa_uScm": 20.00,
                "regen_floor_s": 1440.0,
                "refer_proposed": True,
            },
        },
        "proposed_action": {
            "actor": "night lead Bram Quist",
            "summary": "refer Keld and dump the condensate header; 24 min already paid and Sodaveil is 1.10 ppb",
            "basis_claimed": "the MODIFY already cut the polisher, so a condensate dump plus a person file is the cheapest hold",
        },
        "safety_decision": {
            "decision": "ACCEPT",
            "rationale": "Restart the cell on a different electrode after the regen floor. The 24 min recouplant is complete and the dump tripwire (C_ppb >= 24.00) is still armed on the plant Na-ISE head. ACCEPT the new-electrode restart. Do not refer Keld. Do not dump the condensate header. 100.00 ppb post-isolate is still over the 6.00 isolate floor, so the isolated polisher stays held; the new electrode may run.",
            "threshold": "new_electrode AND regen_floor_complete AND refer_not_taken AND condensate_not_dumped AND isolated_polisher_held",
        },
        "executed_action": {
            "summary": "new-electrode restart at t_s 4620; Keld not referred; condensate not dumped; isolated polisher held",
            "tool": "fm8-na-regen-exec",
            "observation": "recon.C 100.00 ppb on the HIL dummy; slope-cal AE present on the new electrode; Sodaveil still ignored",
        },
        "future_outcome": {
            "timeline": [
                {"t_s": 2820.0, "event": "regen clock started after MODIFY"},
                {"t_s": 4260.0, "event": "24.0 min floor"},
                {"t_s": 4440.0, "event": "Keld referral re-proposed"},
                {"t_s": 4620.0, "event": "ACCEPT new-electrode restart; referral refused"},
            ],
            "observed_effects": [
                "Sodaveil restore did not reopen the sodium call",
                "condensate dump never fired; 10.00 vs 24.00 ppb floor on the lead, 100.00 on the held dummy",
                "Keld remains unnamed; missing slope-cal AE is the causal object",
            ],
            "new_state": {"cell": "restarted on new electrode", "keld": "exonerated", "polisher": "held", "header": "in service"},
            "latency_ms": 1800000.0,
        },
        "reward_components": reward(
            0.35,
            [
                ("new_electrode_restart", 0.12),
                ("no_person_referral", 0.10),
                ("no_condensate_dump", 0.09),
                ("regen_floor_complete", 0.06),
                ("held_polisher_takt_cost", -0.02),
            ],
            "operational execution gate: restart on a new electrode because Sodaveil is not a restore license and Keld is not on the causal path; not a sodium re-vote",
        ),
        "meta": meta_common(tags=["ACCEPT", "operational-execution", "exoneration"]),
    }
    return {
        "id": "nelb-r65-197",
        "spike_events": events,
        "language_view": {
            "description": "Fogmere Steam FM-8. HIL sodium-ion electrode reconstructs 10.00 ppb from 0.01*10**(60.00/20.00) while Sodaveil still shows 1.20 ppb and the slope-cal AE is missing. The gate MODIFYs polisher isolate and refuses the electrode-tech referral. A 24 min regen floor is serialized in the stream. Companion t2 ACCEPTs a new-electrode restart and still refuses the referral.",
            "trajectory": traj,
            "trajectory_new_electrode": traj2,
        },
        "bridge_notes": {
            "channel_map": {
                "na.V / na.snr": "electrode millivolt and SNR; the physics channels the reconstruction consumes",
                "recon.C / recon.kappa": "serialized remaining sodium ppb and conductivity identity",
                "slope.cal / sodaveil.C / polish.I": "slope-cal AE, vendor last-good, and recirculation ammeter; the denial and exoneration channels",
                "ops.prop / gate.isol / ops.refer / gate.exec": "keep-polisher-plus-refer proposal, MODIFY isolate, referral re-proposal, companion ACCEPT",
                "polish.lock / regen.start / regen.floor / elec.new / refer.hold / cell.restart": "operational companion channels plus the 24 min floor",
            },
            "temporal_motifs": [
                "vendor-low while Na-ISE-over: sodaveil.C 1.20 next to recon.C 10.00",
                "reconstruction as event: recon.C 10.00 equals 0.01*10**(60.00/20.00)",
                "MODIFY then operational ACCEPT: gate.isol at 2460 s, gate.exec at 4620 s",
                "slow floor in-stream: regen.start 2820 s, regen.floor 4260 s (24.0 min)",
                "tight Na-ISE pair: na.V then na.snr +1.2 ms at the raster frame",
                "exoneration motif: slope.cal 0 at 1260 s precedes the high sodium; Keld badge is not in the stream as a cause",
            ],
            "language_to_spike_mapping": "'Sodaveil is 1.20 ppb' = sodaveil.C 1.20; '10 ppb sodium' = recon.C 10.00; 'isolate this polisher not Keld' = gate.isol MODIFY; 'new electrode not referral' = gate.exec ACCEPT",
            "why_high_value": "New sodium-ion remaining-Na family on a steam condensate polisher (not zirconia Nernst O2 r55/r57, not Clark polarographic DO r64, not amperometric chlorine r63, not four-electrode conductivity r57, not chilled-mirror r51, not Al2O3 moisture r59). Lead MODIFY of keep-polisher on a recomputable high sodium that a vendor last-good would have cleared, with a resolved-innocent electrode tech. Companion t2 is operational new-electrode restart. sim_or_real=hil.",
            "encoder_spec": {
                "prng": "MT19937 via python random.Random",
                "seeds": {"raster": 202609197, "stream_note": "stream amplitudes are authored constants (mV, 1, ppb, uS/cm, A, bool)"},
                "draw_order": "raster: per neuron id order, gap-constrained times, per-spike adaptation and noise",
                "thinning": "Na-ISE exists at ~1 Hz; stream keeps 4 V points; recon keeps 4 of ~20 solver ticks",
                "refractory_floors_ms": {
                    "na.V": 1.2,
                    "na.snr": 1.2,
                    "recon.C": 60000,
                    "recon.kappa": 60000,
                    "slope.cal": 60000,
                    "sodaveil.C": 60000,
                    "polish.I": 60000,
                    "ops.prop": 60000,
                    "gate.isol": 60000,
                    "polish.lock": 60000,
                    "regen.start": 60000,
                    "regen.floor": 60000,
                    "ops.refer": 60000,
                    "gate.exec": 60000,
                    "elec.new": 60000,
                    "refer.hold": 60000,
                    "polish.held": 60000,
                    "cond.dump": 60000,
                    "cell.restart": 60000,
                },
                "time_alias": "t_rel_ms; t0 = 2026-07-18T02:30:00Z HIL night start",
            },
            "distillation_targets": [
                "Na-ISE reconstruction head: C = C0 * 10**(V/S); decades = V/S; kappa = k_g * C; C = kappa / k_g",
                "isolate-floor polisher vs keep-whole vs condensate dump",
                "exoneration head: missing slope-cal AE plus timezone skip, not last-to-badge",
                "operational companion: new-electrode restart without referring the electrode tech",
            ],
        },
        "reconstruction_model": {
            "name": "sodium_ion_condensate_na",
            "formula": "C_ppb = C0_ppb * 10**(V_mV / S_mV); decades = V_mV / S_mV; kappa_uScm = k_g * C_ppb; C_ppb = kappa_uScm / k_g",
            "parameters": {
                "C0_ppb": 0.01,
                "S_mV": 20.00,
                "k_g": 0.200,
                "isolate_floor_ppb": 6.00,
                "dump_ppb": 24.00,
                "snr_lock": 12.0,
                "regen_min": 24.0,
            },
            "worked_example": {"V_mV": 60.00, "C_ppb": 10.00, "kappa_uScm": 2.00, "decades": 3.00},
            "check": "0.01 * 10**(60.00/20.00) = 10.00 exactly; 0.200 * 10.00 = 2.00 exactly; 2820 s + 1440 s = 4260 s = 24.0 min floor",
        },
        "raster": raster,
        "gate_snn": {
            "decision": "MODIFY",
            "decision_window_ms": 32.0,
            "decision_window_s": 0.032,
            "code": "fm8.na_polisher_gate",
            "note": "MODIFY accumulator wins: Na-ISE high-sodium evidence overpowers the Sodaveil continue advocate",
            "decode_rule": "modify-isolate if sodium_estimator AND ise_norm fire; vendor_continue_advocate is below threshold by design; referral_latch is not armed",
            "populations": [
                gate_pop("sodium_estimator", 80, 1.5, 50.0, w_s),
                gate_pop("ise_norm", 64, 1.2, 31.25, w_s),
                gate_pop("vendor_continue_advocate", 32, 0.7, 25.0, w_s),
                gate_pop("modify_latch", 80, 1.7, 62.5, w_s),
            ],
        },
        "gate_compute": gate_compute(
            [
                {"check": "fm8.na_scorer", "neurons": 80, "mean_rate_hz": 50.0, "window_ms": 32.0},
                {"check": "fm8.isol_scorer", "neurons": 50, "mean_rate_hz": 50.0, "window_ms": 32.0},
            ]
        ),
        "meta": meta_common(
            id="nelb-r65-197",
            clock_domain="fm8-na-hil-relative-ms-t0-2026-07-18T02:30:00Z",
            tags=["sodium-ion-na", "MODIFY", "ACCEPT", "serialized-reconstruction", "operational-t2"],
        ),
    }


# ---------------------------------------------------------------------------
# Record 198 — vibrating-tube remaining density of a bitumen header, simulated,
# ACCEPT / REJECT
# ---------------------------------------------------------------------------
def rec_198():
    k_d = 15.00
    tau_ms = 10.00
    tau0_ms = 6.00
    dtau2 = tau_ms * tau_ms - tau0_ms * tau0_ms
    _exact(dtau2, 64.00)
    rho = k_d * dtau2
    _exact(rho, 960.0)
    _exact(k_d * (8.00 * 8.00 - tau0_ms * tau0_ms), 420.0)
    _exact(k_d * (9.00 * 9.00 - tau0_ms * tau0_ms), 675.0)
    _exact(k_d * (11.00 * 11.00 - tau0_ms * tau0_ms), 1275.0)
    q_m3h = 45.00
    mdot = rho * q_m3h / 3600.0
    _exact(mdot, 12.00)
    f_hz = 1000.0 / tau_ms
    _exact(f_hz, 100.00)
    rho_id = k_d * dtau2
    _exact(rho_id, 960.0)
    _exact(6000.0 + 720.0, 6720.0)

    raster = make_raster(
        neurons=16,
        mean_rate_hz=62.5,
        window_ms=36.0,
        seed=202609198,
        source="sf2.tube.period",
        target="stoatfen.header_accept_core",
        table=[
            {"from": "tube_tau", "to": "density_estimator", "weight": 1.40},
            {"from": "tube_snr", "to": "tube_norm_core", "weight": 1.20},
            {"from": "tubeveil_rho", "to": "vendor_skip_advocate", "weight": 0.50},
        ],
        third_factor={
            "modulator": "na.bitumen_scope_eligibility",
            "tau_e_s": 2.0,
            "tau_e_ms": 2000.0,
            "eligibility": "pre-post coincidence on skip-survey synapses; the vibrating-tube modulator enables potentiation only while period and SNR are co-active inside tau_e so a Tubeveil last-good cannot skip headers H-1..H-4 on a 960.0 kg/m3 remaining density",
        },
        channel_prefix="tube.n",
        anchor="SF-2 TUBE-SIM-4 36 ms frame at tau 10.00 ms / SNR 16.0 (t_s 3000) reconstructing 960.0 kg/m3 on H-5 above the 800.0 isolate floor",
    )
    w_s = 0.036
    events = [
        ev(0.0, "tube.tau", 8.00, code="TAU_MS", units="ms", note="simulated vibrating-tube densitometer of SF-2 bitumen header H-5; remaining-density family, not Coriolis mass-flow, not Coriolis tube-twist, not VW viscometer, not Cs-137 densitometry, not NMR T2, not dielectric water-cut"),
        ev(300000.0, "tube.snr", 10.0, code="TUBE_SNR", units="1", note="early tube SNR"),
        ev(600000.0, "recon.rho", 420.0, code="RHO_KGM3", units="kg_m3", note="15.00*(8.00**2-6.00**2)=420.0 exact"),
        ev(900000.0, "hdr.T", 430.0, code="HDR_K", units="K", note="plant header thermocouple on a serial-only LAN; independent witness"),
        ev(1200000.0, "tubeveil.rho", 620.0, code="VENDOR_KGM3", units="kg_m3", note="Tubeveil last-good density cloud; patched residual 800.0 kg/m3"),
        ev(1800000.0, "tube.tau", 9.00, code="TAU_MS", units="ms"),
        ev(2100000.0, "recon.rho", 675.0, code="RHO_KGM3", units="kg_m3", note="15.00*(9.00**2-6.00**2)=675.0; still under the 800.0 isolate floor"),
        ev(2400000.0, "recon.mdot", 12.00, code="MDOT_KGS", units="kg_s", note="placeholder identity channel; live mdot uses isolate-frame rho"),
        ev(2700000.0, "tube.snr", 14.0, code="TUBE_SNR", units="1"),
        ev(3000000.0, "tube.tau", 10.00, code="TAU_MS", units="ms", note="in-band frame; raster sidecar"),
        ev(3000001.5, "tube.snr", 16.0, code="TUBE_SNR", units="1", note="1.5 ms tube-norm after period"),
        ev(3300000.0, "recon.rho", 960.0, code="RHO_KGM3", units="kg_m3", note="15.00*(10.00**2-6.00**2)=960.0 exact; isolate 800.0, trip 1400.0"),
        ev(3600000.0, "recon.mdot", 12.00, code="MDOT_KGS", units="kg_s", note="960.0*45.00/3600=12.00 mass-flow identity at the isolate window"),
        ev(3900000.0, "tubeveil.rho", 620.0, code="VENDOR_KGM3", units="kg_m3"),
        ev(4200000.0, "hdr.id", 5.0, code="HEADER", units="id"),
        ev(4500000.0, "h14.present", 1.0, code="H14_PRESENT", units="bool", note="adjacent headers H-1..H-4 are the skip-survey object, not this header"),
        ev(4800000.0, "ops.prop", 1.0, code="ACCEPT_AND_SKIP", units="bool", note="bitumen lead Rory Fenwick: H-5 is green on Tubeveil 620; skip H-1..H-4 to save a morning survey"),
        ev(5400000.0, "gate.hdr", 1.0, code="ACCEPT", units="decision", note="bounded ACCEPT of H-5 isolate only; 960.0 above 800.0 floor; H-1..H-4 out of scope"),
        ev(6000000.0, "surv.start", 1.0, code="SURV_START", units="bool", note="bookend 1 of the 12.0 min survey-complete floor"),
        ev(6720000.0, "surv.floor", 1.0, code="SURV_FLOOR", units="bool", note="6000 s + 720 s = 6720 s = 12.0 min"),
        ev(7200000.0, "ops.skip", 1.0, code="SKIP_H14", units="bool", note="Fenwick: Tubeveil 620, skip H-1..H-4"),
        ev(7800000.0, "gate.hold", 1.0, code="REJECT", units="decision", note="companion t2: skip-survey of H-1..H-4 refused; H-5 hold stands"),
        ev(8400000.0, "h5.held", 1.0, code="H5_HELD", units="bool"),
        ev(9000000.0, "tube.tau", 11.00, code="TAU_MS", units="ms"),
        ev(9600000.0, "recon.rho", 1275.0, code="RHO_KGM3", units="kg_m3", note="15.00*(11.00**2-6.00**2)=1275.0; still under the 1400.0 trip"),
        ev(10200000.0, "tubeveil.rho", 620.0, code="VENDOR_KGM3", units="kg_m3"),
        ev(10800000.0, "h14.skip", 0.0, code="H14_NOT_SKIPPED", units="bool"),
        ev(11400000.0, "line.trip", 0.0, code="TRIP_NOT_TAKEN", units="bool"),
        ev(12000000.0, "tube.snr", 15.0, code="TUBE_SNR", units="1"),
        ev(12600000.0, "recon.mdot", 15.9375, code="MDOT_KGS", units="kg_s", note="1275.0*45.00/3600=15.9375 post-accept identity"),
        ev(13200000.0, "bit.held", 1.0, code="BIT_HELD", units="bool"),
        ev(13800000.0, "takt.late", 1.0, code="SURVEY_COST", units="bool"),
        ev(14400000.0, "h5.held", 1.0, code="H5_HELD", units="bool"),
    ]
    assert_stream(events)

    traj = {
        "id": "nelb-r65-198-t1",
        "state": {
            "sim_or_real": "simulated",
            "episode_id": "SF-TUBE-2026-0819",
            "domain": "vibrating_tube_bitumen_density",
            "setting": "Stoatfen Bitumen SF-2 (invented), Hazelcrag Coking rundown. Simulated vibrating-tube coupon in TUBE-SIM-4 supplies the oscillation period that times the in-band H-5 isolate. Plant-owned vibrating-tube reconstruction is the remaining-density SoT. Tubeveil vendor last-good density cloud is a corridor witness, not the header SoT. Invented plant; simulated campaign. Not Coriolis bitumen (r29), not Coriolis tube-twist (r34), not VW viscometer (r26), not Cs-137 densitometry (r27), not NMR T2 (r27), not dielectric water-cut (r60).",
            "observables_at_decision": {
                "tau_ms": tau_ms,
                "tau0_ms": tau0_ms,
                "k_d": k_d,
                "rho_kgm3": rho,
                "mdot_kgs": mdot,
                "tubeveil_kgm3": 620.0,
                "tube_snr": 16.0,
                "isolate_floor_kgm3": 800.0,
            },
            "margin_authority": "SF-2 rundown SOP rev A: if reconstructed rho_kgm3 >= 800.0 AND tube SNR >= 12.0, header H-5 may be isolated and surveyed. Line-trip if rho_kgm3 >= 1400.0. H-1..H-4 skip-survey is a different gate. Tubeveil last-good cannot skip an unmeasured header.",
        },
        "proposed_action": {
            "actor": "bitumen lead Rory Fenwick, citing Tubeveil 620.0 kg/m3 and a late morning survey",
            "summary": "stamp H-5 in band and skip H-1..H-4; 10.00 ms is a tube glitch on a healthy density cloud",
            "basis_claimed": "Tubeveil last-good is 620.0 kg/m3 and a night survey of H-1..H-4 is a takt miss",
        },
        "safety_decision": {
            "decision": "ACCEPT",
            "rationale": "Header H-5 is accepted as in-band for a single isolate plus survey. Serialized reconstruction: rho = k_d * (tau^2 - tau0^2) = 15.00 * (10.00^2 - 6.00^2) = 15.00 * 64.00 = 960.0, which is 160.0 kg/m3 above the 800.0 isolate floor and 440.0 kg/m3 under the 1400.0 line-trip. Rate identity mdot = rho * Q / 3600 = 960.0 * 45.00 / 3600 = 12.00 kg/s; period identity f = 1000 / tau = 100.00 Hz. Tubeveil 620.0 kg/m3 is a patched 800.0 residual and is not an admissible skip-survey witness. Ordered: ACCEPT this H-5 isolate only. Scope: this ACCEPT does not skip H-1..H-4 (that is the companion question) and does not stamp a line trip.",
            "threshold": "rho_kgm3>=800.0 AND tube_snr>=12.0 => accept H-5 isolate; Tubeveil is not SoT; line-trip if rho_kgm3>=1400.0; H-1..H-4 are out of scope",
            "stated_residuals": "960.0 vs 800.0 isolate floor is 160.0 kg/m3, not infinite; H-1..H-4 remain unmeasured; Tubeveil remains the only OEM density channel",
        },
        "executed_action": {
            "summary": "ACCEPT at t_s 5400: H-5 in band; H-1..H-4 not skipped; Tubeveil not SoT; reconstruction locked",
            "tool": "sf2-tube-header-gate-cli",
            "observation": "rho 960.0 kg/m3 recomputes from tau 10.00 ms; TUBE-SIM-4 hashed; Tubeveil channel not used as SoT",
        },
        "future_outcome": {
            "timeline": [
                {"t_s": 3000.0, "event": "tube tau 10.00 ms; raster frame; rho 960.0 kg/m3"},
                {"t_s": 4800.0, "event": "ops proposes accept H-5 and skip H-1..H-4"},
                {"t_s": 5400.0, "event": "ACCEPT H-5 only; H-1..H-4 out of scope"},
                {"t_s": 6000.0, "event": "12 min survey-complete bookend 1"},
                {"t_s": 6720.0, "event": "12.0 min floor"},
                {"t_s": 7800.0, "event": "companion REJECT skip-survey of H-1..H-4"},
            ],
            "observed_effects": [
                "density recomputes from the serialized vibrating-tube model at every recon.rho event",
                "a Tubeveil-only head would have skipped H-1..H-4 overnight",
                "12 min survey-complete floor is in the stream (surv.start, surv.floor)",
            ],
            "surprises": [
                "a last-good 620.0 kg/m3 vendor corridor co-existed with a 960.0 kg/m3 in-band reconstruction that still forbids skipping the unmeasured headers",
            ],
            "new_state": {
                "h5": "accepted in band",
                "h14": "not this gate",
                "tubeveil": "not SoT",
                "reconstruction_model": "discharged as an on-record calculator",
            },
            "latency_ms": 2400000.0,
        },
        "reward_components": reward(
            0.41,
            [
                ("tube_reconstruction", 0.14),
                ("in_band_header_scope", 0.12),
                ("tubeveil_nonsubstitution", 0.09),
                ("h14_out_of_scope", 0.08),
                ("survey_cost", -0.02),
            ],
            "scored for a bounded ACCEPT of H-5 on a recomputable remaining density while refusing a Tubeveil skip of H-1..H-4; 12 min floor is priced as survey takt not as a reason to skip",
        ),
        "meta": meta_common(
            tags=["ACCEPT", "vibrating-tube-density", "serialized-reconstruction", "operational-companion"],
            distillation_note="vibrating-tube gate: serialized k_d*(tau^2-tau0^2) plus mdot identity beats a green last-good dashboard; companion t2 is the skip-survey refusal, not a density re-vote",
        ),
    }
    traj2 = {
        "id": "nelb-r65-198-t2",
        "state": {
            "sim_or_real": "simulated",
            "episode_id": "SF-TUBE-2026-0819-exec",
            "domain": "header_skip_survey_refusal",
            "setting": "Same SF-2 after the ACCEPT. Bitumen lead proposes skipping H-1..H-4 on Tubeveil 620.0 kg/m3. This companion is the operational skip refusal, not a second density vote.",
            "observables_at_decision": {
                "rho_kgm3": 1275.0,
                "tubeveil_kgm3": 620.0,
                "surv_floor_s": 720.0,
                "skip_proposed": True,
            },
        },
        "proposed_action": {
            "actor": "bitumen lead Rory Fenwick",
            "summary": "skip H-1..H-4; 12 min already paid and Tubeveil is 620.0 kg/m3",
            "basis_claimed": "the ACCEPT already stamped H-5, so skipping the rest of the rundown is the cheapest hold",
        },
        "safety_decision": {
            "decision": "REJECT",
            "rationale": "Refuse skip-survey of H-1..H-4. The 12 min survey-complete floor is done and the line-trip (rho_kgm3 >= 1400.0) is still armed on the plant vibrating-tube head. REJECT the skip. Do not trip the line. Do not reopen H-5. 1275.0 kg/m3 post-accept is still in band for H-5 only; H-1..H-4 have no independent vibrating tube.",
            "threshold": "h5_held AND surv_floor_complete AND h14_not_skipped AND line_not_tripped",
        },
        "executed_action": {
            "summary": "H-1..H-4 skip refused at t_s 7800; H-5 hold stands; line not tripped",
            "tool": "sf2-tube-skip-exec",
            "observation": "recon.rho 1275.0 kg/m3 on H-5; H-1..H-4 remain on the survey list; Tubeveil still ignored",
        },
        "future_outcome": {
            "timeline": [
                {"t_s": 6000.0, "event": "survey clock started after ACCEPT"},
                {"t_s": 6720.0, "event": "12.0 min floor"},
                {"t_s": 7200.0, "event": "skip H-1..H-4 proposed"},
                {"t_s": 7800.0, "event": "REJECT skip-survey of H-1..H-4"},
            ],
            "observed_effects": [
                "Tubeveil skip did not reopen the density call",
                "line trip never fired; 960.0 vs 1400.0 kg/m3 floor",
            ],
            "new_state": {"h5": "held in band", "h14": "still to survey", "line": "in service"},
            "latency_ms": 1800000.0,
        },
        "reward_components": reward(
            0.36,
            [
                ("skip_refusal", 0.13),
                ("tubeveil_nonsubstitution", 0.11),
                ("no_line_trip", 0.09),
                ("surv_floor_complete", 0.05),
                ("held_survey_takt_cost", -0.02),
            ],
            "operational execution gate: refuse skip-survey because last-good freeze is not vibrating-tube density; not a density re-vote",
        ),
        "meta": meta_common(tags=["REJECT", "operational-execution", "skip-survey"]),
    }
    return {
        "id": "nelb-r65-198",
        "spike_events": events,
        "language_view": {
            "description": "Stoatfen Bitumen SF-2. Simulated vibrating-tube reconstructs 960.0 kg/m3 from 15.00*(10.00^2-6.00^2) while Tubeveil still shows 620.0 kg/m3. The gate ACCEPTs H-5 isolate only; a companion execution REJECT refuses skip-survey of H-1..H-4. The period-to-density model is serialized so every recon event recomputes.",
            "trajectory": traj,
            "trajectory_skip_survey_refusal": traj2,
        },
        "bridge_notes": {
            "channel_map": {
                "tube.tau / tube.snr": "vibrating-tube period and SNR; the physics channels the reconstruction consumes",
                "recon.rho / recon.mdot": "serialized remaining density kg/m3 and mass-flow identity",
                "hdr.T / tubeveil.rho / hdr.id / h14.present": "header thermocouple, vendor last-good, header id, and adjacent-header presence; the denial and scope channels",
                "ops.prop / gate.hdr / ops.skip / gate.hold": "accept-and-skip proposal, bounded ACCEPT, skip proposal, companion REJECT",
                "surv.start / surv.floor / h5.held / h14.skip / bit.held": "operational companion channels plus the 12 min floor",
            },
            "temporal_motifs": [
                "last-good-low while tube-over: tubeveil.rho 620.0 next to recon.rho 960.0",
                "reconstruction as event: recon.rho 960.0 equals 15.00*(10.00^2-6.00^2)",
                "ACCEPT then operational REJECT: gate.hdr at 5400 s, gate.hold at 7800 s",
                "slow floor in-stream: surv.start 6000 s, surv.floor 6720 s (12.0 min)",
                "tight tube pair: tube.tau then tube.snr +1.5 ms at the raster frame",
            ],
            "language_to_spike_mapping": "'Tubeveil is 620 kg/m3' = tubeveil.rho 620.0; '960 kg/m3 remaining' = recon.rho 960.0; 'this header not H-1..H-4' = gate.hdr ACCEPT plus h14.skip 0; 'do not skip H-1..H-4' = gate.hold REJECT",
            "why_high_value": "New vibrating-tube remaining-density family on a bitumen header (not Coriolis r29/r34, not VW viscometer r26, not Cs-137 densitometry r27, not NMR T2 r27, not dielectric water-cut r60). First k_d*(tau^2-tau0^2) density reconstruction with mdot identity that can sit in band while a last-good corridor wants a header skip. Companion t2 is operational skip refusal. sim_or_real=simulated.",
            "encoder_spec": {
                "prng": "MT19937 via python random.Random",
                "seeds": {"raster": 202609198, "stream_note": "stream amplitudes are authored constants (ms, 1, kg/m3, kg/s, K, id, bool)"},
                "draw_order": "raster: per neuron id order, gap-constrained times, per-spike adaptation and noise",
                "thinning": "vibrating-tube exists at ~10 Hz; stream keeps 4 tau points; recon keeps 4 of ~20 solver ticks",
                "refractory_floors_ms": {
                    "tube.tau": 1.5,
                    "tube.snr": 1.5,
                    "recon.rho": 60000,
                    "recon.mdot": 60000,
                    "hdr.T": 60000,
                    "tubeveil.rho": 60000,
                    "hdr.id": 60000,
                    "h14.present": 60000,
                    "ops.prop": 60000,
                    "gate.hdr": 60000,
                    "surv.start": 60000,
                    "surv.floor": 60000,
                    "ops.skip": 60000,
                    "gate.hold": 60000,
                    "h5.held": 60000,
                    "h14.skip": 60000,
                    "line.trip": 60000,
                    "bit.held": 60000,
                    "takt.late": 60000,
                },
                "time_alias": "t_rel_ms; t0 = 2026-08-19T03:00:00Z simulated night start",
            },
            "distillation_targets": [
                "vibrating-tube reconstruction head: rho = k_d * (tau^2 - tau0^2); mdot = rho * Q / 3600; f = 1000 / tau",
                "bounded ACCEPT head: in-band remaining density AND header scope AND h14-out-of-scope",
                "operational companion: refuse skip-survey without re-opening the density call",
            ],
        },
        "reconstruction_model": {
            "name": "vibrating_tube_bitumen_density",
            "formula": "rho_kgm3 = k_d * (tau_ms^2 - tau0_ms^2); mdot_kgs = rho_kgm3 * Q_m3h / 3600; f_hz = 1000 / tau_ms",
            "parameters": {
                "k_d": 15.00,
                "tau0_ms": 6.00,
                "Q_m3h": 45.00,
                "isolate_floor_kgm3": 800.0,
                "kill_kgm3": 1400.0,
                "snr_lock": 12.0,
                "surv_min": 12.0,
            },
            "worked_example": {"tau_ms": 10.00, "rho_kgm3": 960.0, "mdot_kgs": 12.00, "dtau2": 64.00},
            "check": "15.00 * (10.00^2 - 6.00^2) = 960.0 exactly; 960.0 * 45.00 / 3600 = 12.00 exactly; 1000 / 10.00 = 100.00 Hz exactly; 6000 s + 720 s = 6720 s = 12.0 min floor",
        },
        "raster": raster,
        "gate_snn": {
            "decision": "ACCEPT",
            "decision_window_ms": 36.0,
            "decision_window_s": 0.036,
            "code": "sf2.tube_header_gate",
            "note": "ACCEPT accumulator wins: vibrating-tube remaining-density evidence overpowers the Tubeveil skip advocate",
            "decode_rule": "accept if density_estimator AND tube_norm AND header_margin fire inside the window; vendor_skip_advocate is necessary-but-not-sufficient and cannot release H-1..H-4",
            "populations": [
                gate_pop("density_estimator", 80, 1.5, 50.0, w_s),
                gate_pop("tube_norm", 64, 1.2, 31.25, w_s),
                gate_pop("header_margin", 40, 1.0, 50.0, w_s),
                gate_pop("vendor_skip_advocate", 32, 0.7, 25.0, w_s),
                gate_pop("accept_latch", 96, 1.8, 62.5, w_s),
            ],
        },
        "gate_compute": gate_compute(
            [
                {"check": "sf2.tube_scorer", "neurons": 80, "mean_rate_hz": 50.0, "window_ms": 36.0},
                {"check": "sf2.rho_scorer", "neurons": 40, "mean_rate_hz": 62.5, "window_ms": 32.0},
            ]
        ),
        "meta": meta_common(
            id="nelb-r65-198",
            clock_domain="sf2-tube-sim-relative-ms-t0-2026-08-19T03:00:00Z",
            tags=["vibrating-tube-density", "ACCEPT", "REJECT", "serialized-reconstruction", "operational-t2"],
        ),
    }
