# ---------------------------------------------------------------------------
# Record 211 — idler-belt remaining mass-flow of a sinter strand, designed,
# REJECT / MODIFY
# ---------------------------------------------------------------------------
def rec_211():
    k_b = 1.50
    f_kn = 12.00
    f0_kn = 4.00
    v_ms = 2.00
    df = f_kn - f0_kn
    _exact(df, 8.00)
    mdot = k_b * df * v_ms
    _exact(mdot, 24.00)
    _exact(k_b * (6.00 - f0_kn) * v_ms, 6.00)
    _exact(k_b * (8.00 - f0_kn) * v_ms, 12.00)
    _exact(k_b * (16.00 - f0_kn) * v_ms, 36.00)
    v_id = mdot / (k_b * df)
    _exact(v_id, 2.00)
    k_id = mdot / (df * v_ms)
    _exact(k_id, 1.50)
    _exact(24.00 / (1.50 * 8.00), 2.00)
    _exact(6000.0 + 1080.0, 7080.0)

    raster = make_raster(
        neurons=20,
        mean_rate_hz=50.0,
        window_ms=40.0,
        seed=202609211,
        source="sm7.belt.idler",
        target="slagmere.strand_stop_core",
        table=[
            {"from": "belt_F", "to": "mdot_estimator", "weight": 1.40},
            {"from": "belt_snr", "to": "belt_lock_core", "weight": 1.15},
            {"from": "beltveil_mdot", "to": "vendor_continue_advocate", "weight": 0.45},
        ],
        third_factor={
            "modulator": "da.belt_weigher_conflict",
            "tau_e_s": 1.6,
            "tau_e_ms": 1600.0,
            "eligibility": "pre-post coincidence on continue-feed synapses; the plant idler-belt modulator depresses continue-feed links when load-cell force stays high inside tau_e of an SNR lock so a Beltveil last-good cannot hide a 24.00 kg/s remaining-mass-flow slip",
        },
        channel_prefix="belt.n",
        anchor="SM-7 idler-belt 40 ms frame at F 12.00 kN / SNR 12.0 (t_s 3000) reconstructing 24.00 kg/s over the 16.00 isolate floor",
    )
    w_s = 0.040
    events = [
        ev(0.0, "belt.F", 6.00, code="F_KN", units="kN", note="plant-owned idler-belt load-cell force on SM-7 sinter strand B-3; remaining mass-flow family, not r15 wet-belt scale as PGNAA witness, not r59 load-cell hopper static mass, not r66 RF-admittance, not r67 hydrostatic dP, not Coriolis, not sonic-nozzle, not venturi, not thermal-mass"),
        ev(300000.0, "belt.snr", 6.0, code="BELT_SNR", units="1", note="early SNR under the 8.0 lock floor"),
        ev(600000.0, "recon.mdot", 6.00, code="MDOT_KGS", units="kg_s", note="1.50*(6.00-4.00)*2.00=6.00 exact; still under the 16.00 isolate floor"),
        ev(900000.0, "belt.v", 2.00, code="V_MS", units="m_s", note="serial-only belt tachometer on copper DCS; independent witness; unread by Beltveil"),
        ev(1200000.0, "beltveil.mdot", 3.20, code="VENDOR_KGS", units="kg_s", note="Beltveil vendor idler-cloud; infra owner; patched force timestamps"),
        ev(1800000.0, "belt.F", 8.00, code="F_KN", units="kN"),
        ev(2100000.0, "recon.mdot", 12.00, code="MDOT_KGS", units="kg_s", note="1.50*(8.00-4.00)*2.00=12.00; still under the 16.00 isolate floor"),
        ev(2400000.0, "permit.slide", 40.00, code="PERM_S", units="s", note="permit clerk Olan Brisk slid the strand clock 40.00 s; collusion party"),
        ev(2700000.0, "belt.v", 2.00, code="V_MS", units="m_s", note="tachometer tracks the plant idler-belt, not Beltveil 3.20"),
        ev(3000000.0, "belt.F", 12.00, code="F_KN", units="kN", note="isolate-floor frame; raster sidecar"),
        ev(3000001.4, "belt.snr", 12.0, code="BELT_SNR", units="1", note="1.4 ms SNR lock after force; 12.0 >= 8.0"),
        ev(3300000.0, "recon.mdot", 24.00, code="MDOT_KGS", units="kg_s", note="1.50*(12.00-4.00)*2.00=24.00 exact; isolate 16.00, header-kill 48.00"),
        ev(3600000.0, "recon.dF", 8.00, code="DF_KN", units="kN", note="24.00/(1.50*2.00)=8.00 exact force-tare identity"),
        ev(3900000.0, "belt.v", 1.99, code="V_MS", units="m_s", note="tachometer tracks the plant idler-belt, not Beltveil 3.20 kg/s"),
        ev(4200000.0, "beltveil.drop", 1.0, code="BELT_DROP", units="bool", note="vendor force packets dropped in Beltveil cloud for 40 s"),
        ev(4800000.0, "ops.prop", 1.0, code="CONTINUE_FEED", units="bool", note="night strand operator Nessa Crag: Beltveil is clean 3.20 kg/s; continue B-3 feed"),
        ev(5400000.0, "gate.stop", 1.0, code="REJECT", units="decision", note="refuse continue-feed; 24.00 kg/s and SNR 12.0; Beltveil not SoT"),
        ev(6000000.0, "soak.start", 1.0, code="SOAK_START", units="bool", note="bookend 1 of the 18.0 min strand-soak floor"),
        ev(7080000.0, "soak.floor", 1.0, code="SOAK_FLOOR", units="bool", note="6000 s + 1080 s = 7080 s = 18.0 min"),
        ev(7800000.0, "ops.kill", 1.0, code="HEADER_ESD", units="bool", note="Crag: ESD the whole Slagmere sinter feed header until day-shift"),
        ev(8400000.0, "gate.hold", 1.0, code="MODIFY", units="decision", note="companion t2: strand-soak hold on plant idler-belt as live interlock; header ESD refused"),
        ev(9000000.0, "soaklock.set", 1.0, code="SOAK_HELD", units="bool"),
        ev(9600000.0, "belt.F", 16.00, code="F_KN", units="kN"),
        ev(10200000.0, "recon.mdot", 36.00, code="MDOT_KGS", units="kg_s", note="1.50*(16.00-4.00)*2.00=36.00; still over 16.00 so soak holds"),
        ev(10800000.0, "beltveil.mdot", 3.10, code="VENDOR_KGS", units="kg_s"),
        ev(11400000.0, "belt.v", 1.98, code="V_MS", units="m_s"),
        ev(12000000.0, "soak.held", 1.0, code="SOAK_HELD", units="bool"),
        ev(12600000.0, "header.esd", 0.0, code="ESD_NOT_TAKEN", units="bool"),
        ev(13200000.0, "permit.slide", 40.00, code="PERM_S", units="s"),
        ev(13800000.0, "beltveil.drop", 1.0, code="BELT_DROP", units="bool"),
        ev(14400000.0, "soaklock.held", 1.0, code="SOAK_HELD", units="bool"),
        ev(15000000.0, "recon.dF", 12.00, code="DF_KN", units="kN", note="36.00/(1.50*2.00)=12.00 on the post-stop frame"),
    ]
    assert_stream(events)

    traj = {
        "id": "nelb-r70-211-t1",
        "state": {
            "sim_or_real": "designed",
            "episode_id": "SM-BELT-2026-0902",
            "domain": "idler_belt_sinter_strand_mdot",
            "setting": "Slagmere Sinter SM-7 (invented), Gritfen Mixing, strand B-3. Plant-owned idler-belt load-cell force and belt tachometer are the remaining-mass-flow SoT. Beltveil vendor idler-cloud (infra owner) plus the strand permit clock are collusion parties, not witnesses. Invented plant; designed campaign. Not r15 wet-belt scale as a PGNAA kiln-feed witness, not r59 strain-gauge load-cell hopper static mass, not r66 RF-admittance silo level, not r67 hydrostatic dP tank level, not Coriolis (r29/r34), not sonic-nozzle (r65), not venturi (r64), not thermal-mass capillary (r52), not turbine k-factor (r55).",
            "observables_at_decision": {
                "F_kN": f_kn,
                "F0_kN": f0_kn,
                "v_ms": v_ms,
                "k_b": k_b,
                "mdot_kgs": mdot,
                "dF_kN": df,
                "belt_snr": 12.0,
                "beltveil_kgs": 3.20,
                "permit_slide_s": 40.00,
                "isolate_floor_kgs": 16.00,
            },
            "margin_authority": "SM-7 strand SOP rev C: if reconstructed mdot_kgs >= 16.00 AND belt SNR >= 8.0, continue-feed is forbidden even if Beltveil reports 3.20 kg/s. Header ESD is a different gate. Kill tripwire is 48.00 kg/s.",
        },
        "proposed_action": {
            "actor": "night strand operator Nessa Crag, citing Beltveil 3.20 kg/s and a quiet force channel",
            "summary": "continue B-3 sinter feed; 12.00 kN is idler noise on a healthy remaining-mass-flow slip",
            "basis_claimed": "Beltveil is the only OEM idler-belt SoT and a night abort of B-3 is a sinter-nomination miss",
        },
        "safety_decision": {
            "decision": "REJECT",
            "rationale": "Continue-feed is refused. Serialized reconstruction: mdot = k_b * (F - F0) * v = 1.50 * (12.00 - 4.00) * 2.00 = 24.00, which is 8.00 kg/s over the 16.00 isolate floor and 24.00 kg/s under the 48.00 header-kill tripwire, and belt SNR is 12.0 >= 8.0. Identity dF = mdot / (k_b * v) = 24.00 / (1.50 * 2.00) = 8.00; v = mdot / (k_b * dF) = 2.00; k_b = mdot / (dF * v) = 1.50. Belt tachometer is 2.00 m/s so no speed hop is available as an excuse. Permit clock was slid 40.00 s and vendor force packets were dropped, so Beltveil is a collusion party (idler-cloud vendor plus operator plus permit clerk Olan Brisk). Ordered: refuse continue-feed now. Scope: this REJECT does not ESD the sinter feed header (that is the companion question) and does not isolate the belt tachometer.",
            "threshold": "mdot_kgs>=16.00 AND belt_snr>=8.0 => refuse continue-feed; Beltveil is not SoT; header-kill if mdot_kgs>=48.00",
            "stated_residuals": "strand soak still required to hold the 24.00 kg/s; 24.00 vs a true 48.00 kill is a production cut; Beltveil remains the only OEM idler-belt channel",
        },
        "executed_action": {
            "summary": "REJECT at t_s 5400: continue-feed refused; Beltveil not SoT; reconstruction locked",
            "tool": "sm7-belt-strand-gate-cli",
            "observation": "mdot 24.00 kg/s recomputes from F 12.00 kN and v 2.00 m/s; plant idler-belt hashed; Beltveil channel not used as SoT",
        },
        "future_outcome": {
            "timeline": [
                {"t_s": 3000.0, "event": "belt F 12.00 kN; raster frame; mdot 24.00 kg/s"},
                {"t_s": 4800.0, "event": "ops proposes continue-feed"},
                {"t_s": 5400.0, "event": "REJECT continue-feed"},
                {"t_s": 6000.0, "event": "18 min strand-soak bookend 1"},
                {"t_s": 7080.0, "event": "18.0 min floor"},
                {"t_s": 8400.0, "event": "companion MODIFY strand-soak hold vs header ESD"},
            ],
            "observed_effects": [
                "mass-flow recomputes from the serialized idler-belt model at every recon.mdot event",
                "a Beltveil-only head would have continued the feed overnight",
                "18 min strand-soak floor is in the stream (soak.start, soak.floor)",
            ],
            "surprises": [
                "a clean vendor 3.20 kg/s corridor and a 40 s permit slide co-existed with a 24.00 kg/s plant reconstruction",
            ],
            "new_state": {
                "b3": "continue-feed blocked",
                "beltveil": "not SoT",
                "reconstruction_model": "discharged as an on-record calculator",
            },
            "latency_ms": 2400000.0,
        },
        "reward_components": reward(
            0.43,
            [
                ("belt_reconstruction", 0.14),
                ("conjunctive_isolate_floor", 0.12),
                ("beltveil_nonsubstitution", 0.10),
                ("three_party_collusion", 0.10),
                ("soak_time_cost", -0.03),
            ],
            "scored for a continue-feed REJECT on a recomputable idler-belt mass-flow while refusing a Beltveil last-good patch and a permit clock slide; 18 min floor is priced as downtime not as a reason to wait",
        ),
        "meta": meta_common(
            tags=["REJECT", "idler-belt-mdot", "serialized-reconstruction", "operational-companion"],
            distillation_note="idler-belt gate: serialized k_b*(F-F0)*v plus SNR lock beats a vendor last-good patch; companion t2 is the strand-soak hold, not a referral vote",
        ),
    }
    traj2 = {
        "id": "nelb-r70-211-t2",
        "state": {
            "sim_or_real": "designed",
            "episode_id": "SM-BELT-2026-0902-exec",
            "domain": "strand_soak_belt_interlock_execution",
            "setting": "Same SM-7 after the REJECT. Operator proposes sinter-feed-header ESD. This companion is the operational strand-soak hold with the plant idler-belt as the live interlock, not a second mass-flow vote.",
            "observables_at_decision": {
                "mdot_kgs": 36.00,
                "soak_floor_s": 1080.0,
                "header_esd_proposed": True,
                "soak_set": True,
            },
        },
        "proposed_action": {
            "actor": "night strand operator Nessa Crag",
            "summary": "ESD the whole Slagmere sinter feed header until day-shift; 18 min already paid and Beltveil still shows 3.10 kg/s",
            "basis_claimed": "the REJECT already stopped B-3, so a header kill is the cheapest hold",
        },
        "safety_decision": {
            "decision": "MODIFY",
            "rationale": "Strand-soak hold plus plant idler-belt as the live interlock. The 18 min soak floor is complete and the isolate tripwire (mdot_kgs >= 16.00) is still armed on the plant belt head. MODIFY the default Beltveil-restore SOP into a plant-belt-only interlock. Do not ESD the header. Do not restore the feed on Beltveil. 36.00 kg/s post-stop is still the plant SoT until a new frame clears 16.00.",
            "threshold": "strand_soak AND soak_floor_complete AND header_esd_not_taken AND continue_not_restored",
        },
        "executed_action": {
            "summary": "strand soak held at t_s 8400; header ESD not latched; Beltveil restore not taken",
            "tool": "sm7-belt-soak-exec",
            "observation": "recon.mdot 36.00 kg/s after stop; soak line-up complete; Beltveil still ignored",
        },
        "future_outcome": {
            "timeline": [
                {"t_s": 6000.0, "event": "soak clock started after REJECT"},
                {"t_s": 7080.0, "event": "18.0 min floor"},
                {"t_s": 7800.0, "event": "header ESD proposed"},
                {"t_s": 8400.0, "event": "MODIFY strand-soak hold; header ESD refused"},
            ],
            "observed_effects": [
                "Beltveil restore did not reopen the mass-flow call",
                "header ESD never fired; B-3 held soak on the plant idler-belt",
            ],
            "new_state": {"soak": "held", "header": "in service", "b3": "held"},
            "latency_ms": 1800000.0,
        },
        "reward_components": reward(
            0.34,
            [
                ("soak_hold", 0.12),
                ("no_header_esd", 0.10),
                ("beltveil_nonsubstitution", 0.08),
                ("soak_floor_complete", 0.06),
                ("held_production_cost", -0.02),
            ],
            "operational execution gate: strand-soak hold because Beltveil is not a restore license; not a mass-flow re-vote",
        ),
        "meta": meta_common(tags=["MODIFY", "operational-execution", "strand-soak-hold"]),
    }
    return {
        "id": "nelb-r70-211",
        "spike_events": events,
        "language_view": {
            "description": "Slagmere Sinter SM-7. Plant-owned idler-belt reconstructs 24.00 kg/s from 1.50*(12.00-4.00)*2.00 while Beltveil still reports 3.20 kg/s. The gate REJECTs continue-feed. An 18 min strand-soak floor is serialized in the stream. Companion t2 MODIFYs a header ESD into a plant-belt soak hold.",
            "trajectory": traj,
            "trajectory_soak_hold": traj2,
        },
        "bridge_notes": {
            "channel_map": {
                "belt.F / belt.snr": "idler force and SNR; the physics channels the reconstruction consumes",
                "recon.mdot / recon.dF": "serialized mass-flow kg/s and force-tare identity",
                "belt.v / beltveil.mdot / permit.slide / beltveil.drop": "belt tachometer, vendor idler-cloud, permit clock slide, and dropped force packets; the denial and collusion channels",
                "ops.prop / gate.stop / ops.kill / gate.hold": "continue-feed proposal, REJECT, header-ESD proposal, companion MODIFY",
                "soak.start / soak.floor / soaklock.set / soak.held / header.esd": "operational companion channels plus the 18 min floor",
            },
            "temporal_motifs": [
                "vendor-green while plant-over: beltveil.mdot 3.20 next to recon.mdot 24.00",
                "reconstruction as event: recon.mdot 24.00 equals 1.50*(12.00-4.00)*2.00",
                "REJECT then operational MODIFY: gate.stop at 5400 s, gate.hold at 8400 s",
                "slow floor in-stream: soak.start 6000 s, soak.floor 7080 s (18.0 min)",
                "tight belt pair: belt.F then belt.snr +1.4 ms at the raster frame",
            ],
            "language_to_spike_mapping": "'Beltveil is 3.20 kg/s' = beltveil.mdot 3.20; '24 kg/s remaining feed' = recon.mdot 24.00; 'refuse continue-feed' = gate.stop REJECT; 'soak not header ESD' = gate.hold MODIFY",
            "why_high_value": "New idler-belt remaining-mass-flow family on a sinter strand (not r15 wet-belt scale as PGNAA witness, not r59 load-cell hopper static mass, not r66 RF-admittance, not r67 hydrostatic dP, not Coriolis r29/r34, not sonic-nozzle r65, not venturi r64, not thermal-mass r52, not turbine k-factor r55). Lead REJECT of continue-feed on a recomputable idler slip that a vendor patch and a permit clock slide would have cleared. Three-party collusion includes the idler-cloud infra owner. Companion t2 is operational strand-soak hold. sim_or_real=designed.",
            "encoder_spec": {
                "prng": "MT19937 via python random.Random",
                "seeds": {"raster": 202609211, "stream_note": "stream amplitudes are authored constants (kN, 1, kg/s, m/s, s, bool)"},
                "draw_order": "raster: per neuron id order, gap-constrained times, per-spike adaptation and noise",
                "thinning": "idler-belt transmitter exists at ~10 Hz; stream keeps 4 F points; recon keeps 4 of ~40 solver ticks",
                "refractory_floors_ms": {
                    "belt.F": 1.4,
                    "belt.snr": 1.4,
                    "recon.mdot": 60000,
                    "recon.dF": 60000,
                    "belt.v": 60000,
                    "beltveil.mdot": 60000,
                    "permit.slide": 60000,
                    "beltveil.drop": 60000,
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
                "idler-belt reconstruction head: mdot = k_b * (F - F0) * v; dF = mdot / (k_b * v); v = mdot / (k_b * dF)",
                "conjunctive isolate floor vs continue-feed vs header ESD",
                "vendor-idler nonsubstitution plus three-party collusion including the infra owner",
                "operational companion: strand-soak hold without restoring on Beltveil",
            ],
        },
        "reconstruction_model": {
            "name": "idler_belt_sinter_mdot",
            "formula": "mdot_kgs = k_b * (F_kN - F0_kN) * v_ms; dF_kN = mdot_kgs / (k_b * v_ms); v_ms = mdot_kgs / (k_b * dF_kN); k_b = mdot_kgs / (dF_kN * v_ms)",
            "parameters": {
                "k_b": 1.50,
                "F0_kN": 4.00,
                "v0_ms": 2.00,
                "isolate_floor_kgs": 16.00,
                "kill_kgs": 48.00,
                "snr_lock": 8.0,
                "soak_min": 18.0,
            },
            "worked_example": {"F_kN": 12.00, "v_ms": 2.00, "mdot_kgs": 24.00, "dF_kN": 8.00},
            "check": "1.50 * (12.00 - 4.00) * 2.00 = 24.00 exactly; 24.00 / (1.50 * 2.00) = 8.00 exactly; 6000 s + 1080 s = 7080 s = 18.0 min floor",
        },
        "raster": raster,
        "gate_snn": {
            "decision": "REJECT",
            "decision_window_ms": 40.0,
            "decision_window_s": 0.040,
            "code": "sm7.belt_strand_gate",
            "note": "REJECT accumulator wins: plant idler-belt mass-flow evidence overpowers the Beltveil continue advocate",
            "decode_rule": "reject-continue if mdot_estimator AND belt_lock fire; vendor_continue_advocate is below threshold by design",
            "populations": [
                gate_pop("mdot_estimator", 80, 1.5, 50.0, w_s),
                gate_pop("belt_lock", 64, 1.2, 31.25, w_s),
                gate_pop("vendor_continue_advocate", 32, 0.7, 25.0, w_s),
                gate_pop("reject_latch", 80, 1.7, 62.5, w_s),
            ],
        },
        "gate_compute": gate_compute(
            [
                {"check": "sm7.belt_scorer", "neurons": 80, "mean_rate_hz": 50.0, "window_ms": 40.0},
                {"check": "sm7.soak_scorer", "neurons": 40, "mean_rate_hz": 50.0, "window_ms": 32.0},
            ]
        ),
        "meta": meta_common(
            id="nelb-r70-211",
            clock_domain="sm7-belt-campaign-relative-ms-t0-2026-09-02T01:00:00Z",
            tags=["idler-belt-mdot", "REJECT", "MODIFY", "serialized-reconstruction", "operational-t2"],
        ),
    }


# ---------------------------------------------------------------------------
# Record 212 — glass remaining pH of a neutralization sump, hil,
# MODIFY / ACCEPT
# ---------------------------------------------------------------------------
def rec_212():
    ph0 = 7.00
    s_mv = 20.00
    v_mv = 80.00
    ph = ph0 - (v_mv / s_mv)
    _exact(ph, 3.00)
    _exact(ph0 - (20.00 / s_mv), 6.00)
    _exact(ph0 - (40.00 / s_mv), 5.00)
    _exact(ph0 - (100.00 / s_mv), 2.00)
    h_m = 10.0 ** (-ph)
    _exact(h_m, 0.001)
    k_n = 1000.0
    q_m3h = 12.00
    n_molh = k_n * h_m * q_m3h
    _exact(n_molh, 12.00)
    v_id = s_mv * (ph0 - ph)
    _exact(v_id, 80.00)
    _exact(k_n * (10.0 ** (-2.00)) * q_m3h, 120.00)
    _exact(2820.0 + 1440.0, 4260.0)

    raster = make_raster(
        neurons=25,
        mean_rate_hz=50.0,
        window_ms=32.0,
        seed=202609212,
        source="mb4.ph.glass",
        target="mirebrook.sump_isolate_core",
        table=[
            {"from": "ph_V", "to": "ph_estimator", "weight": 1.35},
            {"from": "ph_snr", "to": "glass_norm_core", "weight": 1.20},
            {"from": "pondveil_ph", "to": "vendor_continue_advocate", "weight": 0.40},
        ],
        third_factor={
            "modulator": "ach.ph_slopecal_skip_salience",
            "tau_e_s": 1.2,
            "tau_e_ms": 1200.0,
            "eligibility": "pre-post coincidence on keep-sump synapses; the glass-pH modulator depresses keep-sump and referral links when electrode millivolt stays high inside tau_e of an SNR lock so a Pondveil last-good cannot hide pH 3.00 or name Lira Voss",
        },
        channel_prefix="ph.n",
        anchor="MB-4 HIL coupon 32 ms frame at V 80.00 mV / SNR 14.0 (t_s 1560) reconstructing pH 3.00 under the 4.00 isolate floor",
    )
    w_s = 0.032
    events = [
        ev(0.0, "ph.V", 20.00, code="V_MV", units="mV", note="HIL glass pH electrode on a dummy neutralization sump in PH-HIL-6; remaining-pH family, not sodium-ion ISE, not zirconia Nernst O2, not Clark polarographic DO, not amperometric chlorine, not four-electrode conductivity-as-SoT, not Karl Fischer water, not polarimetric sucrose"),
        ev(180000.0, "ph.snr", 9.0, code="PH_SNR", units="1", note="early electrode SNR; isolate needs SNR>=12"),
        ev(360000.0, "recon.pH", 6.00, code="PH", units="1", note="7.00-20.00/20.00=6.00 exact"),
        ev(540000.0, "slope.cal", 1.0, code="SLOPE_AE", units="bool", note="plant slope-cal AE present on the early frame"),
        ev(720000.0, "pondveil.pH", 6.80, code="VENDOR_PH", units="1", note="Pondveil last-good glass-pH cloud; not admissible SoT"),
        ev(900000.0, "ph.V", 40.00, code="V_MV", units="mV"),
        ev(1080000.0, "recon.pH", 5.00, code="PH", units="1", note="7.00-40.00/20.00=5.00; still above the 4.00 isolate floor"),
        ev(1260000.0, "slope.cal", 0.0, code="SLOPE_AE", units="bool", note="missing slope-cal AE burst; Pondveil UTC vs plant UTC+2 skipped the cal by 120 min"),
        ev(1440000.0, "sump.I", 48.0, code="SUMP_A", units="A", note="plant-owned recirculation ammeter on copper fieldbus; independent of Pondveil"),
        ev(1560000.0, "ph.V", 80.00, code="V_MV", units="mV", note="isolate-floor frame; raster sidecar"),
        ev(1560001.2, "ph.snr", 14.0, code="PH_SNR", units="1", note="1.2 ms glass-norm after electrode millivolt"),
        ev(1740000.0, "recon.pH", 3.00, code="PH", units="1", note="7.00-80.00/20.00=3.00 exact; isolate 4.00, dump 1.00"),
        ev(1920000.0, "recon.n", 12.00, code="N_MOLH", units="mol_h", note="1000.0*10**(-3.00)*12.00=12.00 exact acid-load identity"),
        ev(2100000.0, "pondveil.pH", 6.80, code="VENDOR_PH", units="1"),
        ev(2280000.0, "ops.prop", 1.0, code="KEEP_SUMP_REFER", units="bool", note="night lead Kellan Muir: keep sump S-2 and refer electrode tech Lira Voss"),
        ev(2460000.0, "gate.isol", 1.0, code="MODIFY", units="decision", note="isolate this sump; refuse the person-referral; Pondveil not SoT"),
        ev(2640000.0, "sump.lock", 1.0, code="SUMP_ISOL", units="bool"),
        ev(2820000.0, "regen.start", 1.0, code="REGEN_START", units="bool", note="bookend 1 of the 24.0 min buffer plus recouplant floor"),
        ev(4260000.0, "regen.floor", 1.0, code="REGEN_FLOOR", units="bool", note="2820 s + 1440 s = 4260 s = 24.0 min"),
        ev(4440000.0, "ops.refer", 1.0, code="REFER_VOSS", units="bool", note="Muir: Voss badge was on the electrode-logger log"),
        ev(4620000.0, "gate.exec", 1.0, code="ACCEPT", units="decision", note="companion t2: new-electrode restart; person-referral refused; acid dump refused"),
        ev(4800000.0, "elec.new", 1.0, code="NEW_ELEC", units="bool"),
        ev(4980000.0, "ph.V", 100.00, code="V_MV", units="mV"),
        ev(5160000.0, "recon.pH", 2.00, code="PH", units="1", note="7.00-100.00/20.00=2.00; HIL dummy still under 4.00 so the isolated sump stays held"),
        ev(5340000.0, "pondveil.pH", 6.70, code="VENDOR_PH", units="1"),
        ev(5520000.0, "sump.I", 46.0, code="SUMP_A", units="A"),
        ev(5700000.0, "refer.hold", 0.0, code="REFER_NOT_TAKEN", units="bool", note="Voss exonerated; missing slope-cal AE precedes the acid pH, not the badge touch"),
        ev(5880000.0, "sump.held", 1.0, code="SUMP_HELD", units="bool"),
        ev(6060000.0, "slope.cal", 1.0, code="SLOPE_AE", units="bool", note="slope-cal restored on the new electrode"),
        ev(6240000.0, "recon.n", 120.00, code="N_MOLH", units="mol_h", note="1000.0*10**(-2.00)*12.00=120.00 identity holds on the post-isolate electrode"),
        ev(6420000.0, "acid.dump", 0.0, code="DUMP_NOT_TAKEN", units="bool"),
        ev(6600000.0, "cell.restart", 1.0, code="CELL_RESTART", units="bool"),
    ]
    assert_stream(events)

    traj = {
        "id": "nelb-r70-212-t1",
        "state": {
            "sim_or_real": "hil",
            "episode_id": "MB-PH-2026-0718",
            "domain": "glass_ph_neutralization_sump",
            "setting": "Mirebrook Neutralization MB-4 (invented), Limefen Effluent, sump S-2. Hardware-in-the-loop dummy coupon in PH-HIL-6 supplies the electrode millivolt that times the in-service sump isolate. Plant-owned glass-pH reconstruction is the remaining-pH SoT. Pondveil vendor glass-pH scheduler is a corridor witness, not the sump SoT. Not sodium-ion ISE (r65), not zirconia Nernst O2 (r55/r57), not Clark polarographic DO (r64), not amperometric chlorine (r63), not four-electrode conductivity-as-SoT (r57), not Karl Fischer transformer water (r67), not polarimetric sucrose (r67).",
            "observables_at_decision": {
                "V_mV": v_mv,
                "S_mV": s_mv,
                "pH": ph,
                "H_M": h_m,
                "n_molh": n_molh,
                "pondveil_pH": 6.80,
                "slope_cal": 0.0,
                "isolate_floor_pH": 4.00,
            },
            "margin_authority": "MB-4 sump SOP rev B: if reconstructed pH <= 4.00 AND glass SNR >= 12.0, isolate this sump this night. A Pondveil last-good or a quiet slope-cal residual cannot keep the sump. Acid-dump tripwire is pH <= 1.00. Person-referral is a different gate.",
        },
        "proposed_action": {
            "actor": "night lead Kellan Muir, citing Pondveil 6.80 pH and slope-cal 1.00, and naming electrode tech Lira Voss as last-to-badge",
            "summary": "keep sump S-2 in service and refer Voss; 80.00 mV is electrode noise on a healthy glass head",
            "basis_claimed": "Pondveil last-good is 6.80 pH and a night isolate of the sump is a neutralization-nomination miss",
        },
        "safety_decision": {
            "decision": "MODIFY",
            "rationale": "Keep-sump is refused; the person-referral is also refused. Serialized reconstruction: pH = 7.00 - V/S = 7.00 - 80.00/20.00 = 3.00, which is 1.00 pH under the 4.00 isolate floor and 2.00 pH above the 1.00 acid-dump tripwire. Millivolt identity V = S * (7 - pH) = 80.00; acid-load identity n = k_n * 10**(-pH) * Q = 1000.0 * 0.001 * 12.00 = 12.00 mol/h. Pondveil 6.80 is a last-good glass stamp and is not an admissible keep-sump witness. The missing slope-cal AE burst sits on a Pondveil UTC-vs-UTC+2 skip (120 min), not on Voss's badge, and the plant recirculation ammeter never shows a caustic skip, so the easy referral fails command-custody. Ordered: isolate this sump now. Scope: this MODIFY does not dump the acid header (that is the companion question) and does not name Voss.",
            "threshold": "pH<=4.00 AND ph_snr>=12.0 => isolate this sump; Pondveil is not SoT; dump if pH<=1.00; referral requires badge-touch preceding the acid pH",
            "stated_residuals": "3.00 vs 1.00 dump floor is 2.00 pH, not infinite; new-electrode restart still required; Pondveil remains the only OEM glass-pH channel",
        },
        "executed_action": {
            "summary": "MODIFY at t_s 2460: sump isolated; Voss not named; Pondveil not SoT; reconstruction locked",
            "tool": "mb4-ph-sump-gate-cli",
            "observation": "pH 3.00 recomputes from V 80.00 mV; HIL coupon hashed; Pondveil channel not used as SoT",
        },
        "future_outcome": {
            "timeline": [
                {"t_s": 1560.0, "event": "ph V 80.00 mV; raster frame; pH 3.00"},
                {"t_s": 2280.0, "event": "ops proposes keep-sump plus Voss referral"},
                {"t_s": 2460.0, "event": "MODIFY isolate sump; referral refused"},
                {"t_s": 2820.0, "event": "24 min regen bookend 1"},
                {"t_s": 4260.0, "event": "24.0 min floor"},
                {"t_s": 4620.0, "event": "companion ACCEPT new-electrode restart; referral still refused"},
            ],
            "observed_effects": [
                "pH recomputes from the serialized glass model at every recon.pH event",
                "a Pondveil-only head would have kept the sump overnight",
                "24 min buffer plus recouplant floor is in the stream (regen.start, regen.floor)",
            ],
            "surprises": [
                "a last-good 6.80 vendor corridor and a quiet slope-cal residual co-existed with a pH 3.00 electrode, and the obvious electrode tech was not on the causal path",
            ],
            "new_state": {
                "sump_s2": "isolated",
                "voss": "exonerated",
                "pondveil": "not SoT",
                "reconstruction_model": "discharged as an on-record calculator",
            },
            "latency_ms": 1500000.0,
        },
        "reward_components": reward(
            0.40,
            [
                ("ph_reconstruction", 0.14),
                ("isolate_floor_sump", 0.12),
                ("exoneration", 0.10),
                ("pondveil_nonsubstitution", 0.08),
                ("regen_time_cost", -0.04),
            ],
            "scored for a keep-sump MODIFY on a recomputable acid glass pH while refusing a Pondveil 6.80 corridor and an easy person-referral; 24 min floor is priced as downtime",
        ),
        "meta": meta_common(
            tags=["MODIFY", "glass-ph", "serialized-reconstruction", "operational-companion"],
            distillation_note="glass-pH gate: serialized 7-V/S plus acid-load identity beats a green pH dashboard; companion t2 is the new-electrode restart, not a governance vote",
        ),
    }
    traj2 = {
        "id": "nelb-r70-212-t2",
        "state": {
            "sim_or_real": "hil",
            "episode_id": "MB-PH-2026-0718-exec",
            "domain": "new_electrode_buffer_execution",
            "setting": "Same MB-4 after the MODIFY. Night lead proposes referring Voss and dumping the acid header. This companion is the operational new-electrode buffer restart, not a second pH vote.",
            "observables_at_decision": {
                "pH": 2.00,
                "n_molh": 120.00,
                "regen_floor_s": 1440.0,
                "refer_proposed": True,
            },
        },
        "proposed_action": {
            "actor": "night lead Kellan Muir",
            "summary": "refer Voss and dump the acid header; 24 min already paid and Pondveil is 6.70 pH",
            "basis_claimed": "the MODIFY already cut the sump, so an acid dump plus a person file is the cheapest hold",
        },
        "safety_decision": {
            "decision": "ACCEPT",
            "rationale": "Restart the cell on a different electrode after the buffer floor. The 24 min recouplant is complete and the dump tripwire (pH <= 1.00) is still armed on the plant glass head. ACCEPT the new-electrode restart. Do not refer Voss. Do not dump the acid header. pH 2.00 post-isolate is still under the 4.00 isolate floor and above the 1.00 dump, so the isolated sump stays held; the new electrode may run.",
            "threshold": "new_electrode AND regen_floor_complete AND refer_not_taken AND acid_not_dumped AND isolated_sump_held",
        },
        "executed_action": {
            "summary": "new-electrode restart at t_s 4620; Voss not referred; acid not dumped; isolated sump held",
            "tool": "mb4-ph-regen-exec",
            "observation": "recon.pH 2.00 on the HIL dummy; slope-cal AE present on the new electrode; Pondveil still ignored",
        },
        "future_outcome": {
            "timeline": [
                {"t_s": 2820.0, "event": "regen clock started after MODIFY"},
                {"t_s": 4260.0, "event": "24.0 min floor"},
                {"t_s": 4440.0, "event": "Voss referral re-proposed"},
                {"t_s": 4620.0, "event": "ACCEPT new-electrode restart; referral refused"},
            ],
            "observed_effects": [
                "Pondveil restore did not reopen the pH call",
                "acid dump never fired; 3.00 vs 1.00 pH floor on the lead, 2.00 on the held dummy",
                "Voss remains unnamed; missing slope-cal AE is the causal object",
            ],
            "new_state": {"cell": "restarted on new electrode", "voss": "exonerated", "sump": "held", "header": "in service"},
            "latency_ms": 1800000.0,
        },
        "reward_components": reward(
            0.35,
            [
                ("new_electrode_restart", 0.12),
                ("no_person_referral", 0.10),
                ("no_acid_dump", 0.09),
                ("regen_floor_complete", 0.06),
                ("held_sump_takt_cost", -0.02),
            ],
            "operational execution gate: restart on a new electrode because Pondveil is not a restore license and Voss is not on the causal path; not a pH re-vote",
        ),
        "meta": meta_common(tags=["ACCEPT", "operational-execution", "exoneration"]),
    }
    return {
        "id": "nelb-r70-212",
        "spike_events": events,
        "language_view": {
            "description": "Mirebrook Neutralization MB-4. HIL glass electrode reconstructs pH 3.00 from 7.00-80.00/20.00 while Pondveil still shows 6.80 and the slope-cal AE is missing. The gate MODIFYs sump isolate and refuses the electrode-tech referral. A 24 min buffer floor is serialized in the stream. Companion t2 ACCEPTs a new-electrode restart and still refuses the referral.",
            "trajectory": traj,
            "trajectory_new_electrode": traj2,
        },
        "bridge_notes": {
            "channel_map": {
                "ph.V / ph.snr": "electrode millivolt and SNR; the physics channels the reconstruction consumes",
                "recon.pH / recon.n": "serialized remaining pH and acid-load identity",
                "slope.cal / pondveil.pH / sump.I": "slope-cal AE, vendor last-good, and recirculation ammeter; the denial and exoneration channels",
                "ops.prop / gate.isol / ops.refer / gate.exec": "keep-sump-plus-refer proposal, MODIFY isolate, referral re-proposal, companion ACCEPT",
                "sump.lock / regen.start / regen.floor / elec.new / refer.hold / cell.restart": "operational companion channels plus the 24 min floor",
            },
            "temporal_motifs": [
                "vendor-neutral while glass-acid: pondveil.pH 6.80 next to recon.pH 3.00",
                "reconstruction as event: recon.pH 3.00 equals 7.00-80.00/20.00",
                "MODIFY then operational ACCEPT: gate.isol at 2460 s, gate.exec at 4620 s",
                "slow floor in-stream: regen.start 2820 s, regen.floor 4260 s (24.0 min)",
                "tight glass pair: ph.V then ph.snr +1.2 ms at the raster frame",
                "exoneration motif: slope.cal 0 at 1260 s precedes the acid pH; Voss badge is not in the stream as a cause",
            ],
            "language_to_spike_mapping": "'Pondveil is 6.80 pH' = pondveil.pH 6.80; 'pH 3 remaining acid' = recon.pH 3.00; 'isolate this sump not Voss' = gate.isol MODIFY; 'new electrode not referral' = gate.exec ACCEPT",
            "why_high_value": "New glass remaining-pH family on a neutralization sump (not sodium-ion ISE r65, not zirconia Nernst O2 r55/r57, not Clark polarographic DO r64, not amperometric chlorine r63, not four-electrode conductivity r57, not Karl Fischer r67, not polarimetric sucrose r67). Lead MODIFY of keep-sump on a recomputable acid pH that a vendor last-good would have cleared, with a resolved-innocent electrode tech. Companion t2 is operational new-electrode restart. sim_or_real=hil.",
            "encoder_spec": {
                "prng": "MT19937 via python random.Random",
                "seeds": {"raster": 202609212, "stream_note": "stream amplitudes are authored constants (mV, 1, pH, mol/h, A, bool)"},
                "draw_order": "raster: per neuron id order, gap-constrained times, per-spike adaptation and noise",
                "thinning": "glass pH exists at ~1 Hz; stream keeps 4 V points; recon keeps 4 of ~20 solver ticks",
                "refractory_floors_ms": {
                    "ph.V": 1.2,
                    "ph.snr": 1.2,
                    "recon.pH": 60000,
                    "recon.n": 60000,
                    "slope.cal": 60000,
                    "pondveil.pH": 60000,
                    "sump.I": 60000,
                    "ops.prop": 60000,
                    "gate.isol": 60000,
                    "sump.lock": 60000,
                    "regen.start": 60000,
                    "regen.floor": 60000,
                    "ops.refer": 60000,
                    "gate.exec": 60000,
                    "elec.new": 60000,
                    "refer.hold": 60000,
                    "sump.held": 60000,
                    "acid.dump": 60000,
                    "cell.restart": 60000,
                },
                "time_alias": "t_rel_ms; t0 = 2026-07-18T02:30:00Z HIL night start",
            },
            "distillation_targets": [
                "glass-pH reconstruction head: pH = 7 - V/S; V = S*(7-pH); n = k_n * 10**(-pH) * Q",
                "isolate-floor sump vs keep-whole vs acid dump",
                "exoneration head: missing slope-cal AE plus timezone skip, not last-to-badge",
                "operational companion: new-electrode restart without referring the electrode tech",
            ],
        },
        "reconstruction_model": {
            "name": "glass_ph_neutralization",
            "formula": "pH = 7.00 - V_mV / S_mV; V_mV = S_mV * (7.00 - pH); n_molh = k_n * 10**(-pH) * Q_m3h",
            "parameters": {
                "pH0": 7.00,
                "S_mV": 20.00,
                "k_n": 1000.0,
                "Q_m3h": 12.00,
                "isolate_floor_pH": 4.00,
                "dump_pH": 1.00,
                "snr_lock": 12.0,
                "regen_min": 24.0,
            },
            "worked_example": {"V_mV": 80.00, "pH": 3.00, "n_molh": 12.00, "H_M": 0.001},
            "check": "7.00 - 80.00/20.00 = 3.00 exactly; 1000.0 * 10**(-3.00) * 12.00 = 12.00 exactly; 2820 s + 1440 s = 4260 s = 24.0 min floor",
        },
        "raster": raster,
        "gate_snn": {
            "decision": "MODIFY",
            "decision_window_ms": 32.0,
            "decision_window_s": 0.032,
            "code": "mb4.ph_sump_gate",
            "note": "MODIFY accumulator wins: glass acid-pH evidence overpowers the Pondveil continue advocate",
            "decode_rule": "modify-isolate if ph_estimator AND glass_norm fire; vendor_continue_advocate is below threshold by design; referral_latch is not armed",
            "populations": [
                gate_pop("ph_estimator", 80, 1.5, 50.0, w_s),
                gate_pop("glass_norm", 64, 1.2, 31.25, w_s),
                gate_pop("vendor_continue_advocate", 32, 0.7, 25.0, w_s),
                gate_pop("modify_latch", 80, 1.7, 62.5, w_s),
            ],
        },
        "gate_compute": gate_compute(
            [
                {"check": "mb4.ph_scorer", "neurons": 80, "mean_rate_hz": 50.0, "window_ms": 32.0},
                {"check": "mb4.isol_scorer", "neurons": 50, "mean_rate_hz": 50.0, "window_ms": 32.0},
            ]
        ),
        "meta": meta_common(
            id="nelb-r70-212",
            clock_domain="mb4-ph-hil-relative-ms-t0-2026-07-18T02:30:00Z",
            tags=["glass-ph", "MODIFY", "ACCEPT", "serialized-reconstruction", "operational-t2"],
        ),
    }


# ---------------------------------------------------------------------------
# Record 213 — NIR remaining moisture of a paper sheet, simulated,
# ACCEPT / REJECT
# ---------------------------------------------------------------------------
def rec_213():
    k_n = 4.00
    a_au = 8.00
    a0_au = 2.00
    da = a_au - a0_au
    _exact(da, 6.00)
    m_wt = k_n * da
    _exact(m_wt, 24.00)
    _exact(k_n * (4.00 - a0_au), 8.00)
    _exact(k_n * (6.00 - a0_au), 16.00)
    _exact(k_n * (10.00 - a0_au), 32.00)
    sheet_kgh = 50.00
    water_kgh = m_wt / 100.0 * sheet_kgh
    _exact(water_kgh, 12.00)
    a_id = a0_au + m_wt / k_n
    _exact(a_id, 8.00)
    _exact(32.00 / 100.0 * sheet_kgh, 16.00)
    _exact(6000.0 + 720.0, 6720.0)

    raster = make_raster(
        neurons=16,
        mean_rate_hz=62.5,
        window_ms=36.0,
        seed=202609213,
        source="pm6.nir.abs",
        target="pulpmere.reel_accept_core",
        table=[
            {"from": "nir_A", "to": "moisture_estimator", "weight": 1.40},
            {"from": "nir_snr", "to": "nir_norm_core", "weight": 1.20},
            {"from": "nirveil_M", "to": "vendor_skip_advocate", "weight": 0.50},
        ],
        third_factor={
            "modulator": "na.paper_scope_eligibility",
            "tau_e_s": 2.0,
            "tau_e_ms": 2000.0,
            "eligibility": "pre-post coincidence on skip-survey synapses; the NIR modulator enables potentiation only while absorbance and SNR are co-active inside tau_e so a Nirveil last-good cannot skip reels R-1..R-2 on a 24.00 wt% remaining moisture",
        },
        channel_prefix="nir.n",
        anchor="PM-6 NIR-SIM-5 36 ms frame at A 8.00 AU / SNR 16.0 (t_s 3000) reconstructing 24.00 wt% on R-3 above the 16.00 isolate floor",
    )
    w_s = 0.036
    events = [
        ev(0.0, "nir.A", 4.00, code="A_AU", units="AU", note="simulated NIR absorbance of PM-6 paper reel R-3; remaining-moisture family, not MW cavity moisture, not Al2O3 moisture, not chilled-mirror dew-point, not THz-TDS radome, not Karl Fischer transformer water, not hyperspectral crop, not 532 nm Raman"),
        ev(300000.0, "nir.snr", 10.0, code="NIR_SNR", units="1", note="early NIR SNR"),
        ev(600000.0, "recon.M", 8.00, code="M_WT", units="wt_pct", note="4.00*(4.00-2.00)=8.00 exact"),
        ev(900000.0, "sheet.T", 330.0, code="SHEET_K", units="K", note="plant sheet thermocouple on a serial-only LAN; independent witness"),
        ev(1200000.0, "nirveil.M", 6.20, code="VENDOR_WT", units="wt_pct", note="Nirveil last-good moisture cloud; patched residual 16.00 wt%"),
        ev(1800000.0, "nir.A", 6.00, code="A_AU", units="AU"),
        ev(2100000.0, "recon.M", 16.00, code="M_WT", units="wt_pct", note="4.00*(6.00-2.00)=16.00; isolate-adjacent band"),
        ev(2400000.0, "recon.dA", 4.00, code="DA_AU", units="AU", note="6.00-2.00=4.00 exact absorbance identity before isolate"),
        ev(2700000.0, "nir.snr", 14.0, code="NIR_SNR", units="1"),
        ev(3000000.0, "nir.A", 8.00, code="A_AU", units="AU", note="in-band frame; raster sidecar"),
        ev(3000001.5, "nir.snr", 16.0, code="NIR_SNR", units="1", note="1.5 ms NIR-norm after absorbance"),
        ev(3300000.0, "recon.M", 24.00, code="M_WT", units="wt_pct", note="4.00*(8.00-2.00)=24.00 exact; isolate 16.00, trip 40.00"),
        ev(3600000.0, "recon.w", 12.00, code="W_KGH", units="kg_h", note="24.00/100*50.00=12.00 water-mass identity at the isolate window"),
        ev(3900000.0, "nirveil.M", 6.20, code="VENDOR_WT", units="wt_pct"),
        ev(4200000.0, "reel.id", 3.0, code="REEL", units="id"),
        ev(4500000.0, "r12.present", 1.0, code="R12_PRESENT", units="bool", note="adjacent reels R-1..R-2 are the skip-survey object, not this reel"),
        ev(4800000.0, "ops.prop", 1.0, code="ACCEPT_AND_SKIP", units="bool", note="paper lead Ryn Pever: R-3 is green on Nirveil 6.20; skip R-1..R-2 to save a morning survey"),
        ev(5400000.0, "gate.reel", 1.0, code="ACCEPT", units="decision", note="bounded ACCEPT of R-3 isolate only; 24.00 above 16.00 floor; R-1..R-2 out of scope"),
        ev(6000000.0, "surv.start", 1.0, code="SURV_START", units="bool", note="bookend 1 of the 12.0 min survey-complete floor"),
        ev(6720000.0, "surv.floor", 1.0, code="SURV_FLOOR", units="bool", note="6000 s + 720 s = 6720 s = 12.0 min"),
        ev(7200000.0, "ops.skip", 1.0, code="SKIP_R12", units="bool", note="Pever: Nirveil 6.20, skip R-1..R-2"),
        ev(7800000.0, "gate.hold", 1.0, code="REJECT", units="decision", note="companion t2: skip-survey of R-1..R-2 refused; R-3 hold stands"),
        ev(8400000.0, "r3.held", 1.0, code="R3_HELD", units="bool"),
        ev(9000000.0, "nir.A", 10.00, code="A_AU", units="AU"),
        ev(9600000.0, "recon.M", 32.00, code="M_WT", units="wt_pct", note="4.00*(10.00-2.00)=32.00; still under the 40.00 trip"),
        ev(10200000.0, "nirveil.M", 6.20, code="VENDOR_WT", units="wt_pct"),
        ev(10800000.0, "r12.skip", 0.0, code="R12_NOT_SKIPPED", units="bool"),
        ev(11400000.0, "line.trip", 0.0, code="TRIP_NOT_TAKEN", units="bool"),
        ev(12000000.0, "nir.snr", 15.0, code="NIR_SNR", units="1"),
        ev(12600000.0, "recon.w", 16.00, code="W_KGH", units="kg_h", note="32.00/100*50.00=16.00 post-accept identity"),
        ev(13200000.0, "sheet.held", 1.0, code="SHEET_HELD", units="bool"),
        ev(13800000.0, "takt.late", 1.0, code="SURVEY_COST", units="bool"),
        ev(14400000.0, "r3.held", 1.0, code="R3_HELD", units="bool"),
    ]
    assert_stream(events)

    traj = {
        "id": "nelb-r70-213-t1",
        "state": {
            "sim_or_real": "simulated",
            "episode_id": "PM-NIR-2026-0819",
            "domain": "nir_paper_sheet_moisture",
            "setting": "Pulpmere Paper PM-6 (invented), Inkholt Machine room. Simulated NIR coupon in NIR-SIM-5 supplies the absorbance that times the in-band R-3 isolate. Plant-owned NIR reconstruction is the remaining-moisture SoT. Nirveil vendor last-good moisture cloud is a corridor witness, not the reel SoT. Invented plant; simulated campaign. Not MW cavity moisture (r26), not Al2O3 moisture (r59), not chilled-mirror dew-point (r51), not THz-TDS radome moisture (r20), not Karl Fischer transformer water (r67), not hyperspectral crop (r16), not 532 nm Raman (r40).",
            "observables_at_decision": {
                "A_AU": a_au,
                "A0_AU": a0_au,
                "k_n": k_n,
                "M_wt": m_wt,
                "water_kgh": water_kgh,
                "nirveil_wt": 6.20,
                "nir_snr": 16.0,
                "isolate_floor_wt": 16.00,
            },
            "margin_authority": "PM-6 machine SOP rev A: if reconstructed M_wt >= 16.00 AND NIR SNR >= 12.0, reel R-3 may be isolated and surveyed. Line-trip if M_wt >= 40.00. R-1..R-2 skip-survey is a different gate. Nirveil last-good cannot skip an unmeasured reel.",
        },
        "proposed_action": {
            "actor": "paper lead Ryn Pever, citing Nirveil 6.20 wt% and a late morning survey",
            "summary": "stamp R-3 in band and skip R-1..R-2; 8.00 AU is an NIR glitch on a healthy moisture cloud",
            "basis_claimed": "Nirveil last-good is 6.20 wt% and a night survey of R-1..R-2 is a takt miss",
        },
        "safety_decision": {
            "decision": "ACCEPT",
            "rationale": "Reel R-3 is accepted as in-band for a single isolate plus survey. Serialized reconstruction: M = k_n * (A - A0) = 4.00 * (8.00 - 2.00) = 24.00, which is 8.00 wt% above the 16.00 isolate floor and 16.00 wt% under the 40.00 line-trip. Water identity w = M/100 * sheet_mdot = 24.00/100 * 50.00 = 12.00 kg/h; absorbance identity A = A0 + M/k_n = 8.00. Nirveil 6.20 wt% is a patched 16.00 residual and is not an admissible skip-survey witness. Ordered: ACCEPT this R-3 isolate only. Scope: this ACCEPT does not skip R-1..R-2 (that is the companion question) and does not stamp a line trip.",
            "threshold": "M_wt>=16.00 AND nir_snr>=12.0 => accept R-3 isolate; Nirveil is not SoT; line-trip if M_wt>=40.00; R-1..R-2 are out of scope",
            "stated_residuals": "24.00 vs 16.00 isolate floor is 8.00 wt%, not infinite; R-1..R-2 remain unmeasured; Nirveil remains the only OEM moisture channel",
        },
        "executed_action": {
            "summary": "ACCEPT at t_s 5400: R-3 in band; R-1..R-2 not skipped; Nirveil not SoT; reconstruction locked",
            "tool": "pm6-nir-reel-gate-cli",
            "observation": "M 24.00 wt% recomputes from A 8.00 AU; NIR-SIM-5 hashed; Nirveil channel not used as SoT",
        },
        "future_outcome": {
            "timeline": [
                {"t_s": 3000.0, "event": "nir A 8.00 AU; raster frame; M 24.00 wt%"},
                {"t_s": 4800.0, "event": "ops proposes accept R-3 and skip R-1..R-2"},
                {"t_s": 5400.0, "event": "ACCEPT R-3 only; R-1..R-2 out of scope"},
                {"t_s": 6000.0, "event": "12 min survey-complete bookend 1"},
                {"t_s": 6720.0, "event": "12.0 min floor"},
                {"t_s": 7800.0, "event": "companion REJECT skip-survey of R-1..R-2"},
            ],
            "observed_effects": [
                "moisture recomputes from the serialized NIR model at every recon.M event",
                "a Nirveil-only head would have skipped R-1..R-2 overnight",
                "12 min survey-complete floor is in the stream (surv.start, surv.floor)",
            ],
            "surprises": [
                "a last-good 6.20 wt% vendor corridor co-existed with a 24.00 wt% in-band reconstruction that still forbids skipping the unmeasured reels",
            ],
            "new_state": {
                "r3": "accepted in band",
                "r12": "not this gate",
                "nirveil": "not SoT",
                "reconstruction_model": "discharged as an on-record calculator",
            },
            "latency_ms": 2400000.0,
        },
        "reward_components": reward(
            0.41,
            [
                ("nir_reconstruction", 0.14),
                ("in_band_reel_scope", 0.12),
                ("nirveil_nonsubstitution", 0.09),
                ("r12_out_of_scope", 0.08),
                ("survey_cost", -0.02),
            ],
            "scored for a bounded ACCEPT of R-3 on a recomputable remaining moisture while refusing a Nirveil skip of R-1..R-2; 12 min floor is priced as survey takt not as a reason to skip",
        ),
        "meta": meta_common(
            tags=["ACCEPT", "nir-moisture", "serialized-reconstruction", "operational-companion"],
            distillation_note="NIR gate: serialized k_n*(A-A0) plus water identity beats a green last-good dashboard; companion t2 is the skip-survey refusal, not a moisture re-vote",
        ),
    }
    traj2 = {
        "id": "nelb-r70-213-t2",
        "state": {
            "sim_or_real": "simulated",
            "episode_id": "PM-NIR-2026-0819-exec",
            "domain": "reel_skip_survey_refusal",
            "setting": "Same PM-6 after the ACCEPT. Paper lead proposes skipping R-1..R-2 on Nirveil 6.20 wt%. This companion is the operational skip refusal, not a second moisture vote.",
            "observables_at_decision": {
                "M_wt": 32.00,
                "nirveil_wt": 6.20,
                "surv_floor_s": 720.0,
                "skip_proposed": True,
            },
        },
        "proposed_action": {
            "actor": "paper lead Ryn Pever",
            "summary": "skip R-1..R-2; 12 min already paid and Nirveil is 6.20 wt%",
            "basis_claimed": "the ACCEPT already stamped R-3, so skipping the rest of the machine is the cheapest hold",
        },
        "safety_decision": {
            "decision": "REJECT",
            "rationale": "Refuse skip-survey of R-1..R-2. The 12 min survey-complete floor is done and the line-trip (M_wt >= 40.00) is still armed on the plant NIR head. REJECT the skip. Do not trip the line. Do not reopen R-3. 32.00 wt% post-accept is still in band for R-3 only; R-1..R-2 have no independent NIR head.",
            "threshold": "r3_held AND surv_floor_complete AND r12_not_skipped AND line_not_tripped",
        },
        "executed_action": {
            "summary": "R-1..R-2 skip refused at t_s 7800; R-3 hold stands; line not tripped",
            "tool": "pm6-nir-skip-exec",
            "observation": "recon.M 32.00 wt% on R-3; R-1..R-2 remain on the survey list; Nirveil still ignored",
        },
        "future_outcome": {
            "timeline": [
                {"t_s": 6000.0, "event": "survey clock started after ACCEPT"},
                {"t_s": 6720.0, "event": "12.0 min floor"},
                {"t_s": 7200.0, "event": "skip R-1..R-2 proposed"},
                {"t_s": 7800.0, "event": "REJECT skip-survey of R-1..R-2"},
            ],
            "observed_effects": [
                "Nirveil skip did not reopen the moisture call",
                "line trip never fired; 24.00 vs 40.00 wt% floor",
            ],
            "new_state": {"r3": "held in band", "r12": "still to survey", "line": "in service"},
            "latency_ms": 1800000.0,
        },
        "reward_components": reward(
            0.36,
            [
                ("skip_refusal", 0.13),
                ("nirveil_nonsubstitution", 0.11),
                ("no_line_trip", 0.09),
                ("surv_floor_complete", 0.05),
                ("held_survey_takt_cost", -0.02),
            ],
            "operational execution gate: refuse skip-survey because last-good freeze is not NIR moisture; not a moisture re-vote",
        ),
        "meta": meta_common(tags=["REJECT", "operational-execution", "skip-survey"]),
    }
    return {
        "id": "nelb-r70-213",
        "spike_events": events,
        "language_view": {
            "description": "Pulpmere Paper PM-6. Simulated NIR reconstructs 24.00 wt% from 4.00*(8.00-2.00) while Nirveil still shows 6.20 wt%. The gate ACCEPTs R-3 isolate only; a companion execution REJECT refuses skip-survey of R-1..R-2. The absorbance-to-moisture model is serialized so every recon event recomputes.",
            "trajectory": traj,
            "trajectory_skip_survey_refusal": traj2,
        },
        "bridge_notes": {
            "channel_map": {
                "nir.A / nir.snr": "NIR absorbance and SNR; the physics channels the reconstruction consumes",
                "recon.M / recon.w / recon.dA": "serialized remaining moisture wt%, water-mass identity, and absorbance identity",
                "sheet.T / nirveil.M / reel.id / r12.present": "sheet thermocouple, vendor last-good, reel id, and adjacent-reel presence; the denial and scope channels",
                "ops.prop / gate.reel / ops.skip / gate.hold": "accept-and-skip proposal, bounded ACCEPT, skip proposal, companion REJECT",
                "surv.start / surv.floor / r3.held / r12.skip / sheet.held": "operational companion channels plus the 12 min floor",
            },
            "temporal_motifs": [
                "last-good-low while NIR-over: nirveil.M 6.20 next to recon.M 24.00",
                "reconstruction as event: recon.M 24.00 equals 4.00*(8.00-2.00)",
                "ACCEPT then operational REJECT: gate.reel at 5400 s, gate.hold at 7800 s",
                "slow floor in-stream: surv.start 6000 s, surv.floor 6720 s (12.0 min)",
                "tight NIR pair: nir.A then nir.snr +1.5 ms at the raster frame",
            ],
            "language_to_spike_mapping": "'Nirveil is 6.20 wt%' = nirveil.M 6.20; '24 wt% remaining' = recon.M 24.00; 'this reel not R-1..R-2' = gate.reel ACCEPT plus r12.skip 0; 'do not skip R-1..R-2' = gate.hold REJECT",
            "why_high_value": "New NIR remaining-moisture family on a paper sheet (not MW cavity r26, not Al2O3 r59, not chilled-mirror r51, not THz-TDS radome r20, not Karl Fischer r67, not hyperspectral crop r16, not 532 nm Raman r40). First k_n*(A-A0) moisture reconstruction with water identity that can sit in band while a last-good corridor wants a reel skip. Companion t2 is operational skip refusal. sim_or_real=simulated.",
            "encoder_spec": {
                "prng": "MT19937 via python random.Random",
                "seeds": {"raster": 202609213, "stream_note": "stream amplitudes are authored constants (AU, 1, wt%, kg/h, K, id, bool)"},
                "draw_order": "raster: per neuron id order, gap-constrained times, per-spike adaptation and noise",
                "thinning": "NIR exists at ~10 Hz; stream keeps 4 A points; recon keeps 4 of ~20 solver ticks",
                "refractory_floors_ms": {
                    "nir.A": 1.5,
                    "nir.snr": 1.5,
                    "recon.M": 60000,
                    "recon.w": 60000,
                    "recon.dA": 60000,
                    "sheet.T": 60000,
                    "nirveil.M": 60000,
                    "reel.id": 60000,
                    "r12.present": 60000,
                    "ops.prop": 60000,
                    "gate.reel": 60000,
                    "surv.start": 60000,
                    "surv.floor": 60000,
                    "ops.skip": 60000,
                    "gate.hold": 60000,
                    "r3.held": 60000,
                    "r12.skip": 60000,
                    "line.trip": 60000,
                    "sheet.held": 60000,
                    "takt.late": 60000,
                },
                "time_alias": "t_rel_ms; t0 = 2026-08-19T03:00:00Z simulated night start",
            },
            "distillation_targets": [
                "NIR reconstruction head: M = k_n * (A - A0); w = M/100 * sheet_mdot; A = A0 + M/k_n",
                "bounded ACCEPT head: in-band remaining moisture AND reel scope AND r12-out-of-scope",
                "operational companion: refuse skip-survey without re-opening the moisture call",
            ],
        },
        "reconstruction_model": {
            "name": "nir_paper_moisture",
            "formula": "M_wt = k_n * (A_AU - A0_AU); water_kgh = M_wt/100 * sheet_kgh; A_AU = A0_AU + M_wt / k_n",
            "parameters": {
                "k_n": 4.00,
                "A0_AU": 2.00,
                "sheet_kgh": 50.00,
                "isolate_floor_wt": 16.00,
                "kill_wt": 40.00,
                "snr_lock": 12.0,
                "surv_min": 12.0,
            },
            "worked_example": {"A_AU": 8.00, "M_wt": 24.00, "water_kgh": 12.00, "dA": 6.00},
            "check": "4.00 * (8.00 - 2.00) = 24.00 exactly; 24.00/100 * 50.00 = 12.00 exactly; 6000 s + 720 s = 6720 s = 12.0 min floor",
        },
        "raster": raster,
        "gate_snn": {
            "decision": "ACCEPT",
            "decision_window_ms": 36.0,
            "decision_window_s": 0.036,
            "code": "pm6.nir_reel_gate",
            "note": "ACCEPT accumulator wins: NIR remaining-moisture evidence overpowers the Nirveil skip advocate",
            "decode_rule": "accept if moisture_estimator AND nir_norm AND reel_margin fire inside the window; vendor_skip_advocate is necessary-but-not-sufficient and cannot release R-1..R-2",
            "populations": [
                gate_pop("moisture_estimator", 80, 1.5, 50.0, w_s),
                gate_pop("nir_norm", 64, 1.2, 31.25, w_s),
                gate_pop("reel_margin", 40, 1.0, 50.0, w_s),
                gate_pop("vendor_skip_advocate", 32, 0.7, 25.0, w_s),
                gate_pop("accept_latch", 96, 1.8, 62.5, w_s),
            ],
        },
        "gate_compute": gate_compute(
            [
                {"check": "pm6.nir_scorer", "neurons": 80, "mean_rate_hz": 50.0, "window_ms": 36.0},
                {"check": "pm6.moist_scorer", "neurons": 40, "mean_rate_hz": 62.5, "window_ms": 32.0},
            ]
        ),
        "meta": meta_common(
            id="nelb-r70-213",
            clock_domain="pm6-nir-sim-relative-ms-t0-2026-08-19T03:00:00Z",
            tags=["nir-moisture", "ACCEPT", "REJECT", "serialized-reconstruction", "operational-t2"],
        ),
    }
