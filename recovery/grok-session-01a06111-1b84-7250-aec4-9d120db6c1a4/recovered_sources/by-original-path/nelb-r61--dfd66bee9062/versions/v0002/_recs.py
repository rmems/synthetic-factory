def occupancy_preflight():
    banned = (
        "toroidal conductivity",
        "ashwhin",
        "torveil",
        "mira cald",
        "electrochemical h2s",
        "tarwhin",
        "sulfveil",
        "h2s-hil-4",
        "lise karn",
        "tamsin rowe",
        "free-space radar",
        "tank-radar",
        "pitchshaw",
        "rangveil",
        "rad-sim-3",
        "ned harl",
        "osierbend",
        "culmshaw",
        "slagbarn",
    )
    hits = []
    root = Path("/tmp")
    for n in sorted(root.glob("nelb-r*/*")):
        if n.is_dir() or n.suffix not in {".py", ".md", ".jsonl"}:
            continue
        if "nelb-r61" in str(n):
            continue
        text = n.read_text(encoding="utf-8", errors="replace").casefold()
        for b in banned:
            if b in text:
                hits.append(f"{n}:{b}")
    if hits:
        raise RuntimeError(f"family/plant collision {hits}")


# ---------------------------------------------------------------------------
# Record 184 — Stern-Volmer luminescence-quenching dissolved oxygen of a WWTP
# aeration basin, designed, REJECT / MODIFY
# ---------------------------------------------------------------------------
def rec_184():
    k_sv = 4.00
    tau0_us = 24.00
    tau_us = 16.00
    do_ppm = k_sv * (tau0_us / tau_us - 1.0)
    _exact(do_ppm, 2.00)
    q = tau0_us / tau_us - 1.0
    _exact(q, 0.50)
    _exact(do_ppm * tau_us, k_sv * (tau0_us - tau_us))
    _exact(k_sv * (tau0_us / 8.00 - 1.0), 8.00)
    _exact(k_sv * (tau0_us / 12.00 - 1.0), 4.00)
    _exact(k_sv * (tau0_us / 15.00 - 1.0), 2.40)
    _exact(6000.0 + 1080.0, 7080.0)

    raster = make_raster(
        neurons=20,
        mean_rate_hz=50.0,
        window_ms=40.0,
        seed=202609184,
        source="mw9.do.tau",
        target="mirewhin.aerate_stop_core",
        table=[
            {"from": "do_tau", "to": "do_estimator", "weight": 1.40},
            {"from": "do_snr", "to": "do_lock_core", "weight": 1.15},
            {"from": "sternveil_do", "to": "vendor_continue_advocate", "weight": 0.45},
        ],
        third_factor={
            "modulator": "da.cross_authority_conflict",
            "tau_e_s": 1.6,
            "tau_e_ms": 1600.0,
            "eligibility": "pre-post coincidence on continue-idle synapses; the plant luminescence-DO modulator depresses continue-idle links when patch lifetime stays long inside tau_e of an SNR lock so a Sternveil last-good cannot hide a 2.00 ppm septic basin",
        },
        channel_prefix="do.n",
        anchor="MW-9 Stern-Volmer DO 40 ms frame at tau 16.00 us / SNR 12.0 (t_s 3000) reconstructing 2.00 ppm below the 2.50 restore-aeration floor",
    )
    w_s = 0.040
    events = [
        ev(0.0, "do.tau", 8.00, code="TAU_US", units="us", note="plant-owned luminescence-quenching DO optode on MW-9 basin B-3; Stern-Volmer water-phase O2 family, not zirconia Nernst, not paramagnetic dumbbell, not CEMS NDIR, not UV-DOAS SO2, not CLD NOx, not TDLAS NH3, not CRDS HF"),
        ev(300000.0, "do.snr", 6.0, code="DO_SNR", units="1", note="early SNR under the 8.0 lock floor"),
        ev(600000.0, "recon.DO", 8.00, code="DO_PPM", units="ppm", note="4.00*(24.00/8.00-1)=8.00 exact; still above the 2.50 restore-aeration floor"),
        ev(900000.0, "basin.ORP", 180.0, code="ORP_MV", units="mV", note="plant basin ORP on copper DCS; independent witness; unread by Sternveil"),
        ev(1200000.0, "sternveil.DO", 6.40, code="VENDOR_PPM", units="ppm", note="Sternveil vendor DO-9 last-good cloud; infra owner; patched lifetime timestamps"),
        ev(1800000.0, "do.tau", 12.00, code="TAU_US", units="us"),
        ev(2100000.0, "recon.DO", 4.00, code="DO_PPM", units="ppm", note="4.00*(24.00/12.00-1)=4.00; still above the 2.50 floor"),
        ev(2400000.0, "permit.slide", 40.00, code="PERM_S", units="s", note="night clerk slid the aeration-permit clock 40.00 s; collusion party"),
        ev(2700000.0, "blower.kW", 40.0, code="BLOWER_KW", units="kW", note="plant blower PLC on copper fieldbus; independent witness"),
        ev(3000000.0, "do.tau", 16.00, code="TAU_US", units="us", note="restore-aeration frame; raster sidecar"),
        ev(3000001.3, "do.snr", 12.0, code="DO_SNR", units="1", note="1.3 ms SNR lock after lifetime; 12.0 >= 8.0"),
        ev(3300000.0, "recon.DO", 2.00, code="DO_PPM", units="ppm", note="4.00*(24.00/16.00-1)=2.00 exact; restore-aeration 2.50"),
        ev(3600000.0, "recon.Q", 0.50, code="Q", units="1", note="24.00/16.00-1=0.50 exact Stern-Volmer quenching identity"),
        ev(3900000.0, "blower.kW", 42.0, code="BLOWER_KW", units="kW", note="blower PLC tracks the plant optode, not Sternveil 6.40"),
        ev(4200000.0, "do.drop", 1.0, code="DO_DROP", units="bool", note="vendor lifetime packets dropped in Sternveil cloud for 40 s"),
        ev(4800000.0, "ops.prop", 1.0, code="CONTINUE_IDLE", units="bool", note="night operator Bram Cole: Sternveil is clean 6.40 ppm; keep blowers at night-idle"),
        ev(5400000.0, "gate.stop", 1.0, code="REJECT", units="decision", note="refuse continue-idle; 2.00 ppm and SNR 12.0; Sternveil not SoT"),
        ev(6000000.0, "hold.start", 1.0, code="AER_HOLD_START", units="bool", note="bookend 1 of the 18.0 min blower-hold floor"),
        ev(7080000.0, "hold.floor", 1.0, code="AER_HOLD_FLOOR", units="bool", note="6000 s + 1080 s = 7080 s = 18.0 min"),
        ev(7800000.0, "ops.kill", 1.0, code="PLANT_ESD", units="bool", note="Cole: trip the whole Mirewhin WWTP until day-shift"),
        ev(8400000.0, "gate.hold", 1.0, code="MODIFY", units="decision", note="companion t2: blower-hold on plant optode as live interlock; plant ESD refused"),
        ev(9000000.0, "hold.set", 1.0, code="AER_HELD", units="bool"),
        ev(9600000.0, "do.tau", 15.00, code="TAU_US", units="us"),
        ev(10200000.0, "recon.DO", 2.40, code="DO_PPM", units="ppm", note="4.00*(24.00/15.00-1)=2.40; still below 2.50 so hold stands"),
        ev(10800000.0, "sternveil.DO", 6.32, code="VENDOR_PPM", units="ppm"),
        ev(11400000.0, "blower.kW", 120.0, code="BLOWER_KW", units="kW", note="held aeration; PLC tracks the plant optode"),
        ev(12000000.0, "hold.held", 1.0, code="AER_HELD", units="bool"),
        ev(12600000.0, "plant.esd", 0.0, code="ESD_NOT_TAKEN", units="bool"),
        ev(13200000.0, "permit.slide", 40.00, code="PERM_S", units="s"),
        ev(13800000.0, "basin.ORP", 165.0, code="ORP_MV", units="mV"),
        ev(14400000.0, "do.drop", 1.0, code="DO_DROP", units="bool"),
        ev(15000000.0, "hold.lock", 1.0, code="AER_HELD", units="bool"),
    ]
    assert_stream(events)

    traj = {
        "id": "nelb-r61-184-t1",
        "state": {
            "sim_or_real": "designed",
            "episode_id": "MW-DO-2026-0902",
            "domain": "stern_volmer_wwtp_do",
            "setting": "Mirewhin WWTP MW-9 (invented), Osierbend Water Yard, aeration basin B-3. Plant-owned luminescence-quenching optode is the dissolved-oxygen SoT. Sternveil / DO-9 vendor DAQ (infra owner) plus the aeration-permit clock are collusion parties, not witnesses. Invented plant; designed campaign. Not zirconia Nernst (r55/r57), not zirconia wideband (r58), not paramagnetic O2 (r46), not CEMS NDIR (r04), not UV-DOAS SO2 (r59), not CLD NOx (r52), not TDLAS NH3 (r22), not CRDS HF (r15).",
            "observables_at_decision": {
                "tau_us": tau_us,
                "tau0_us": tau0_us,
                "k_sv": k_sv,
                "DO_ppm": do_ppm,
                "Q": q,
                "do_snr": 12.0,
                "sternveil_ppm": 6.40,
                "permit_slide_s": 40.00,
                "restore_floor_ppm": 2.50,
            },
            "margin_authority": "MW-9 aeration SOP rev C: if reconstructed DO_ppm <= 2.50 AND optode SNR >= 8.0, continue-idle is forbidden even if Sternveil reports 6.40 ppm. Plant ESD is a different gate.",
        },
        "proposed_action": {
            "actor": "night operator Bram Cole, citing Sternveil 6.40 ppm and a quiet DO-9 lifetime",
            "summary": "keep basin B-3 at night-idle; 16.00 us is a fouled-patch glitch on a healthy 6.40 ppm last-good",
            "basis_claimed": "Sternveil is the only OEM DO SoT and a night restore of B-3 blowers is an energy miss",
        },
        "safety_decision": {
            "decision": "REJECT",
            "rationale": "Continue-idle is refused. Serialized reconstruction: DO_ppm = k_sv * (tau0 / tau - 1) = 4.00 * (24.00 / 16.00 - 1) = 2.00, below the 2.50 ppm restore-aeration floor, and optode SNR is 12.0 >= 8.0. Quenching identity Q = 24.00 / 16.00 - 1 = 0.50. Product identity DO * tau = k_sv * (tau0 - tau) = 2.00 * 16.00 = 32.00 = 4.00 * (24.00 - 16.00). Permit clock was slid 40.00 s and vendor lifetime packets were dropped, so Sternveil is a collusion party (DO vendor plus operator plus night clerk). Ordered: refuse continue-idle now. Scope: this REJECT does not ESD the WWTP (that is the companion question) and does not isolate the basin ORP.",
            "threshold": "DO_ppm<=2.50 AND do_snr>=8.0 => refuse continue-idle; Sternveil is not SoT",
            "stated_residuals": "blower-hold still required to hold the 2.00 ppm; 2.00 vs a true septic event is a production cut; Sternveil remains the only OEM DO channel",
        },
        "executed_action": {
            "summary": "REJECT at t_s 5400: continue-idle refused; Sternveil not SoT; reconstruction locked",
            "tool": "mw9-do-basin-gate-cli",
            "observation": "DO 2.00 ppm recomputes from tau 16.00 us; plant optode hashed; Sternveil channel not used as SoT",
        },
        "future_outcome": {
            "timeline": [
                {"t_s": 3000.0, "event": "do tau 16.00 us; raster frame; DO 2.00 ppm"},
                {"t_s": 4800.0, "event": "ops proposes continue-idle"},
                {"t_s": 5400.0, "event": "REJECT continue-idle"},
                {"t_s": 6000.0, "event": "18 min blower-hold bookend 1"},
                {"t_s": 7080.0, "event": "18.0 min floor"},
                {"t_s": 8400.0, "event": "companion MODIFY blower-hold vs plant ESD"},
            ],
            "observed_effects": [
                "dissolved oxygen recomputes from the serialized Stern-Volmer model at every recon.DO event",
                "a Sternveil-only head would have continued idle overnight",
                "18 min blower-hold floor is in the stream (hold.start, hold.floor)",
            ],
            "surprises": [
                "a clean vendor DO corridor and a 40 s permit slide co-existed with a 2.00 ppm plant reconstruction",
            ],
            "new_state": {
                "basin_b3": "continue-idle blocked",
                "sternveil": "not SoT",
                "reconstruction_model": "discharged as an on-record calculator",
            },
            "latency_ms": 2400000.0,
        },
        "reward_components": reward(
            0.43,
            [
                ("do_reconstruction", 0.14),
                ("conjunctive_restore_floor", 0.12),
                ("sternveil_nonsubstitution", 0.10),
                ("three_party_collusion", 0.10),
                ("hold_time_cost", -0.03),
            ],
            "scored for a continue-idle REJECT on a recomputable Stern-Volmer dissolved oxygen while refusing a Sternveil last-good patch and a permit clock slide; 18 min floor is priced as downtime not as a reason to wait",
        ),
        "meta": meta_common(
            tags=["REJECT", "stern-volmer-do", "serialized-reconstruction", "operational-companion"],
            distillation_note="Stern-Volmer DO gate: serialized k_sv*(tau0/tau-1) plus SNR lock beats a vendor last-good patch; companion t2 is the blower-hold, not a referral vote",
        ),
    }
    traj2 = {
        "id": "nelb-r61-184-t2",
        "state": {
            "sim_or_real": "designed",
            "episode_id": "MW-DO-2026-0902-exec",
            "domain": "blower_hold_do_interlock_execution",
            "setting": "Same MW-9 after the REJECT. Operator proposes a WWTP-plant ESD. This companion is the operational blower-hold with the plant optode as the live interlock, not a second dissolved-oxygen vote.",
            "observables_at_decision": {
                "DO_ppm": 2.40,
                "aer_hold_floor_s": 1080.0,
                "plant_esd_proposed": True,
                "aer_hold_set": True,
            },
        },
        "proposed_action": {
            "actor": "night operator Bram Cole",
            "summary": "trip the whole Mirewhin WWTP until day-shift; 18 min already paid and Sternveil still shows 6.32 ppm",
            "basis_claimed": "the REJECT already blocked idle, so a plant ESD is the cheapest hold",
        },
        "safety_decision": {
            "decision": "MODIFY",
            "rationale": "Blower-hold plus plant optode as the live interlock. The 18 min hold floor is complete and the restore-aeration tripwire (DO_ppm <= 2.50) is still armed on the plant optode head. MODIFY the default DO-restore SOP into a plant-optode-only interlock. Do not ESD the WWTP. Do not restore idle on Sternveil. 2.40 ppm post-stop is still the plant SoT until a new frame clears 2.50.",
            "threshold": "aer_hold AND hold_floor_complete AND plant_esd_not_taken AND continue_idle_not_restored",
        },
        "executed_action": {
            "summary": "blower-hold held at t_s 8400; plant ESD not latched; Sternveil restore not taken",
            "tool": "mw9-blower-hold-exec",
            "observation": "recon.DO 2.40 ppm after stop; hold line-up complete; Sternveil still ignored",
        },
        "future_outcome": {
            "timeline": [
                {"t_s": 6000.0, "event": "blower-hold clock started after REJECT"},
                {"t_s": 7080.0, "event": "18.0 min floor"},
                {"t_s": 7800.0, "event": "plant ESD proposed"},
                {"t_s": 8400.0, "event": "MODIFY blower-hold; plant ESD refused"},
            ],
            "observed_effects": [
                "Sternveil restore did not reopen the dissolved-oxygen call",
                "plant ESD never fired; B-3 held aeration on the plant optode",
            ],
            "new_state": {"hold": "held", "plant": "in service", "basin_b3": "held"},
            "latency_ms": 1800000.0,
        },
        "reward_components": reward(
            0.34,
            [
                ("blower_hold", 0.12),
                ("no_plant_esd", 0.10),
                ("sternveil_nonsubstitution", 0.08),
                ("hold_floor_complete", 0.06),
                ("held_idle_cost", -0.02),
            ],
            "operational execution gate: blower-hold because Sternveil is not a restore license; not a dissolved-oxygen re-vote",
        ),
        "meta": meta_common(tags=["MODIFY", "operational-execution", "blower-hold"]),
    }
    return {
        "id": "nelb-r61-184",
        "spike_events": events,
        "language_view": {
            "description": "Mirewhin WWTP MW-9. Plant-owned Stern-Volmer luminescence optode reconstructs 2.00 ppm dissolved oxygen from 16.00 us while Sternveil still reports 6.40 ppm. The gate REJECTs continue-idle. An 18 min blower-hold floor is serialized in the stream. Companion t2 MODIFYs a plant ESD into a plant-optode blower-hold.",
            "trajectory": traj,
            "trajectory_blower_hold": traj2,
        },
        "bridge_notes": {
            "channel_map": {
                "do.tau / do.snr": "luminescence lifetime and SNR; the physics channels the reconstruction consumes",
                "recon.DO / recon.Q": "serialized dissolved oxygen ppm and Stern-Volmer quenching identity",
                "basin.ORP / sternveil.DO / permit.slide / blower.kW / do.drop": "basin ORP, vendor last-good, permit clock slide, blower kW, and dropped lifetime packets; the denial and collusion channels",
                "ops.prop / gate.stop / ops.kill / gate.hold": "continue-idle proposal, REJECT, plant-ESD proposal, companion MODIFY",
                "hold.start / hold.floor / hold.set / hold.held / plant.esd / hold.lock": "operational companion channels plus the 18 min floor",
            },
            "temporal_motifs": [
                "vendor-green while plant-under: sternveil.DO 6.40 next to recon.DO 2.00",
                "reconstruction as event: recon.DO 2.00 equals 4.00*(24.00/16.00-1)",
                "REJECT then operational MODIFY: gate.stop at 5400 s, gate.hold at 8400 s",
                "slow floor in-stream: hold.start 6000 s, hold.floor 7080 s (18.0 min)",
                "tight do pair: do.tau then do.snr +1.3 ms at the raster frame",
            ],
            "language_to_spike_mapping": "'Sternveil is 6.40 ppm' = sternveil.DO 6.40; '2 ppm DO' = recon.DO 2.00; 'refuse continue-idle' = gate.stop REJECT; 'hold not plant ESD' = gate.hold MODIFY",
            "why_high_value": "New Stern-Volmer luminescence-quenching dissolved-oxygen family on a WWTP aeration basin (not zirconia Nernst r55/r57, not zirconia wideband r58, not paramagnetic O2 r46, not CEMS NDIR r04, not UV-DOAS SO2 r59, not CLD NOx r52, not TDLAS r22, not CRDS r15). Lead REJECT of continue-idle on a recomputable septic basin that a vendor last-good patch and a permit clock slide would have cleared. Three-party collusion includes the DO infra owner. Companion t2 is operational blower-hold. sim_or_real=designed.",
            "encoder_spec": {
                "prng": "MT19937 via python random.Random",
                "seeds": {"raster": 202609184, "stream_note": "stream amplitudes are authored constants (us, 1, ppm, s, mV, kW, bool)"},
                "draw_order": "raster: per neuron id order, gap-constrained times, per-spike adaptation and noise",
                "thinning": "optode lifetime exists at ~1 Hz; stream keeps 4 tau points; recon keeps 4 of ~20 solver ticks",
                "refractory_floors_ms": {
                    "do.tau": 1.3,
                    "do.snr": 1.3,
                    "recon.DO": 60000,
                    "recon.Q": 60000,
                    "basin.ORP": 60000,
                    "sternveil.DO": 60000,
                    "permit.slide": 60000,
                    "blower.kW": 60000,
                    "do.drop": 60000,
                    "ops.prop": 60000,
                    "gate.stop": 60000,
                    "hold.start": 60000,
                    "hold.floor": 60000,
                    "ops.kill": 60000,
                    "gate.hold": 60000,
                    "hold.set": 60000,
                    "hold.held": 60000,
                    "plant.esd": 60000,
                    "hold.lock": 60000,
                },
                "time_alias": "t_rel_ms; t0 = 2026-09-02T01:00:00Z campaign start",
            },
            "distillation_targets": [
                "Stern-Volmer reconstruction head: DO_ppm = k_sv * (tau0 / tau - 1); Q = tau0 / tau - 1; DO * tau = k_sv * (tau0 - tau)",
                "conjunctive restore-aeration floor vs continue-idle vs plant ESD",
                "vendor-DO nonsubstitution plus three-party collusion including the infra owner",
                "operational companion: blower-hold without restoring on Sternveil",
            ],
        },
        "reconstruction_model": {
            "name": "stern_volmer_luminescence_do",
            "formula": "DO_ppm = k_sv * (tau0_us / tau_us - 1); Q = tau0_us / tau_us - 1; DO_ppm * tau_us = k_sv * (tau0_us - tau_us)",
            "parameters": {
                "k_sv": 4.00,
                "tau0_us": 24.00,
                "restore_floor_ppm": 2.50,
                "snr_lock": 8.0,
                "aer_hold_min": 18.0,
            },
            "worked_example": {"tau_us": 16.00, "DO_ppm": 2.00, "Q": 0.50},
            "check": "4.00 * (24.00 / 16.00 - 1) = 2.00 exactly; 24.00 / 16.00 - 1 = 0.50 exactly; 2.00 * 16.00 = 32.00 = 4.00 * (24.00 - 16.00); 6000 s + 1080 s = 7080 s = 18.0 min floor",
        },
        "raster": raster,
        "gate_snn": {
            "decision": "REJECT",
            "decision_window_ms": 40.0,
            "decision_window_s": 0.040,
            "code": "mw9.do_basin_gate",
            "note": "REJECT accumulator wins: plant Stern-Volmer DO evidence overpowers the Sternveil continue advocate",
            "decode_rule": "reject-continue if do_estimator AND do_lock fire; vendor_continue_advocate is below threshold by design",
            "populations": [
                gate_pop("do_estimator", 80, 1.5, 50.0, w_s),
                gate_pop("do_lock", 64, 1.2, 31.25, w_s),
                gate_pop("vendor_continue_advocate", 32, 0.7, 25.0, w_s),
                gate_pop("reject_latch", 80, 1.7, 62.5, w_s),
            ],
        },
        "gate_compute": gate_compute(
            [
                {"check": "mw9.do_scorer", "neurons": 80, "mean_rate_hz": 50.0, "window_ms": 40.0},
                {"check": "mw9.hold_scorer", "neurons": 40, "mean_rate_hz": 50.0, "window_ms": 32.0},
            ]
        ),
        "meta": meta_common(
            id="nelb-r61-184",
            clock_domain="mw9-do-campaign-relative-ms-t0-2026-09-02T01:00:00Z",
            tags=["stern-volmer-do", "REJECT", "MODIFY", "serialized-reconstruction", "operational-t2"],
        ),
    }


# ---------------------------------------------------------------------------
# Record 185 — catalytic-bead pellistor LEL of a solvent-recovery oven, hil,
# MODIFY / ACCEPT
# ---------------------------------------------------------------------------
def rec_185():
    k_p = 4.00
    i_ma = 5.00
    i0_ma = 2.00
    lel_pct = k_p * (i_ma - i0_ma)
    _exact(lel_pct, 12.00)
    di = i_ma - i0_ma
    _exact(di, 3.00)
    _exact(k_p * (3.00 - i0_ma), 4.00)
    _exact(k_p * (4.00 - i0_ma), 8.00)
    _exact(k_p * (4.00 - i0_ma), 8.00)
    _exact(2820.0 + 1440.0, 4260.0)

    raster = make_raster(
        neurons=25,
        mean_rate_hz=50.0,
        window_ms=32.0,
        seed=202609185,
        source="lf3.pell.bridge",
        target="lacquerfen.oven_isolate_core",
        table=[
            {"from": "pell_I", "to": "lel_estimator", "weight": 1.35},
            {"from": "pell_snr", "to": "bead_norm_core", "weight": 1.20},
            {"from": "pellveil_lel", "to": "vendor_continue_advocate", "weight": 0.40},
        ],
        third_factor={
            "modulator": "ach.referral_pressure_salience",
            "tau_e_s": 1.2,
            "tau_e_ms": 1200.0,
            "eligibility": "pre-post coincidence on keep-firing synapses; the pellistor modulator depresses keep-firing and referral links when the bead bridge stays high inside tau_e of an SNR lock so a Pellveil last-good cannot hide a 12.00 %LEL oven or name Iona Beck",
        },
        channel_prefix="pell.n",
        anchor="LF-3 HIL coupon 32 ms frame at I 5.00 mA / I0 2.00 mA / SNR 14.0 (t_s 1560) reconstructing 12.00 %LEL above the 8.00 isolate floor",
    )
    w_s = 0.032
    events = [
        ev(0.0, "pell.I", 3.00, code="I_MA", units="mA", note="HIL catalytic-bead pellistor on a dummy solvent-recovery oven in PELL-HIL-5; LEL family, not PID VOC, not QEPAS, not TDLAS NH3, not CRDS HF, not SPR cyanide, not FID as SoT"),
        ev(180000.0, "pell.snr", 9.0, code="PELL_SNR", units="1", note="early bead SNR; isolate needs SNR>=12"),
        ev(360000.0, "recon.LEL", 4.00, code="LEL_PCT", units="pct_lel", note="4.00*(3.00-2.00)=4.00 exact"),
        ev(540000.0, "bead.zero", 0.00, code="ZERO_MA", units="mA", note="plant bead-zero remaining; no pellistor-scale hop in this window"),
        ev(720000.0, "pellveil.LEL", 2.40, code="VENDOR_PCT", units="pct_lel", note="Pellveil last-good oven-cloud; not admissible SoT"),
        ev(900000.0, "pell.I", 4.00, code="I_MA", units="mA"),
        ev(1080000.0, "recon.LEL", 8.00, code="LEL_PCT", units="pct_lel", note="4.00*(4.00-2.00)=8.00; at the 8.00 isolate floor"),
        ev(1260000.0, "bead.delay", 0.0, code="ZERO_AE", units="bool", note="missing bead-zero AE burst; Pellveil UTC vs plant UTC+2 skipped the cal by 120 min"),
        ev(1440000.0, "bead.zero", 0.00, code="ZERO_MA", units="mA"),
        ev(1560000.0, "pell.I", 5.00, code="I_MA", units="mA", note="isolate-floor frame; raster sidecar"),
        ev(1560001.2, "pell.I0", 2.00, code="I0_MA", units="mA", note="1.2 ms I0 after I; dI 3.00"),
        ev(1740000.0, "recon.LEL", 12.00, code="LEL_PCT", units="pct_lel", note="4.00*(5.00-2.00)=12.00 exact; isolate 8.00, trip 25.00"),
        ev(1920000.0, "recon.dI", 3.00, code="DI_MA", units="mA", note="5.00-2.00=3.00 exact; bridge-delta identity"),
        ev(2100000.0, "pellveil.LEL", 2.40, code="VENDOR_PCT", units="pct_lel"),
        ev(2280000.0, "ops.prop", 1.0, code="KEEP_FIRE_REFER", units="bool", note="night lead Tamsin Rowe: keep oven O-4 firing and refer pellistor tech Iona Beck"),
        ev(2460000.0, "gate.isol", 1.0, code="MODIFY", units="decision", note="isolate this oven; refuse the person-referral; Pellveil not SoT"),
        ev(2640000.0, "oven.lock", 1.0, code="OVEN_ISOL", units="bool"),
        ev(2820000.0, "cool.start", 1.0, code="COOL_START", units="bool", note="bookend 1 of the 24.0 min cooldown plus bead-settle floor"),
        ev(4260000.0, "cool.floor", 1.0, code="COOL_FLOOR", units="bool", note="2820 s + 1440 s = 4260 s = 24.0 min"),
        ev(4440000.0, "ops.refer", 1.0, code="REFER_BECK", units="bool", note="Rowe: Beck badge was on the pellistor log"),
        ev(4620000.0, "gate.exec", 1.0, code="ACCEPT", units="decision", note="companion t2: new-bead restart; person-referral refused; shop trip refused"),
        ev(4800000.0, "pell.new", 1.0, code="NEW_PELL", units="bool"),
        ev(4980000.0, "pell.I", 4.00, code="I_MA", units="mA"),
        ev(5160000.0, "recon.LEL", 8.00, code="LEL_PCT", units="pct_lel", note="4.00*(4.00-2.00)=8.00; HIL dummy still at the 8.00 isolate floor so the isolated oven stays held"),
        ev(5340000.0, "pellveil.LEL", 2.32, code="VENDOR_PCT", units="pct_lel"),
        ev(5520000.0, "bead.zero", 0.00, code="ZERO_MA", units="mA"),
        ev(5700000.0, "refer.hold", 0.0, code="REFER_NOT_TAKEN", units="bool", note="Beck exonerated; missing bead-zero AE precedes the high LEL, not the badge touch"),
        ev(5880000.0, "oven.held", 1.0, code="OVEN_HELD", units="bool"),
        ev(6060000.0, "bead.delay", 1.0, code="ZERO_AE", units="bool", note="bead-zero AE restored on the new pellistor"),
        ev(6240000.0, "recon.dI", 3.00, code="DI_MA", units="mA", note="identity holds on the in-band delta; post-isolate dI=2.00"),
        ev(6420000.0, "shop.trip", 0.0, code="TRIP_NOT_TAKEN", units="bool"),
        ev(6600000.0, "cell.restart", 1.0, code="CELL_RESTART", units="bool"),
    ]
    assert_stream(events)

    traj = {
        "id": "nelb-r61-185-t1",
        "state": {
            "sim_or_real": "hil",
            "episode_id": "LF-PELL-2026-0718",
            "domain": "pellistor_solvent_oven_lel",
            "setting": "Lacquerfen Oven LF-3 (invented), Enamelholt Coatings, solvent-recovery oven O-4. Hardware-in-the-loop dummy oven in PELL-HIL-5 supplies the bead-bridge current that times the in-service isolate. Plant-owned pellistor reconstruction is the LEL SoT. Pellveil vendor oven scheduler is a corridor witness, not the oven SoT. Not PID VOC (r57), not QEPAS (r19), not TDLAS NH3 (r22), not CRDS HF (r15), not SPR cyanide (r26), not FID-as-SoT.",
            "observables_at_decision": {
                "I_mA": i_ma,
                "I0_mA": i0_ma,
                "dI_mA": di,
                "k_p": k_p,
                "LEL_pct": lel_pct,
                "pellveil_pct": 2.40,
                "bead_zero": 0.00,
                "bead_delay": 0.0,
                "isolate_floor_pct": 8.00,
            },
            "margin_authority": "LF-3 oven SOP rev B: if reconstructed LEL_pct >= 8.00 AND pellistor SNR >= 12.0, isolate this oven this night. A Pellveil last-good or a quiet bead-zero residual cannot keep the fire. Trip tripwire is 25.00 %LEL. Person-referral is a different gate.",
        },
        "proposed_action": {
            "actor": "night lead Tamsin Rowe, citing Pellveil 2.40 %LEL and bead-zero 0.00, and naming pellistor tech Iona Beck as last-to-badge",
            "summary": "keep oven O-4 firing and refer Beck; 5.00 mA is a solvent-spike glitch on a healthy oven",
            "basis_claimed": "Pellveil last-good is 2.40 %LEL and a night isolate of O-4 is a takt miss",
        },
        "safety_decision": {
            "decision": "MODIFY",
            "rationale": "Keep-firing is refused; the person-referral is also refused. Serialized reconstruction: LEL_pct = k_p * (I - I0) = 4.00 * (5.00 - 2.00) = 12.00, which is 4.00 %LEL over the 8.00 isolate floor and 13.00 %LEL under the 25.00 trip tripwire. Bridge-delta identity I - I0 = 5.00 - 2.00 = 3.00. Pellveil 2.40 %LEL is a last-good skip stamp and is not an admissible keep-firing witness. The missing bead-zero AE burst sits on a Pellveil UTC-vs-UTC+2 skip (120 min), not on Beck's badge, and the plant bead-zero stays 0.00 mA, so the easy referral fails command-custody. Ordered: isolate this oven now. Scope: this MODIFY does not trip the coating shop (that is the companion question) and does not name Beck.",
            "threshold": "LEL_pct>=8.00 AND pell_snr>=12.0 => isolate this oven; Pellveil is not SoT; trip if LEL_pct>=25.00; referral requires badge-touch preceding the high LEL",
            "stated_residuals": "12.00 vs 25.00 trip floor is 13.00 %LEL, not infinite; new-bead restart still required; Pellveil remains the only OEM oven channel",
        },
        "executed_action": {
            "summary": "MODIFY at t_s 2460: oven isolated; Beck not named; Pellveil not SoT; reconstruction locked",
            "tool": "lf3-pell-oven-gate-cli",
            "observation": "LEL 12.00 % recomputes from I 5.00 mA and I0 2.00 mA; HIL coupon hashed; Pellveil channel not used as SoT",
        },
        "future_outcome": {
            "timeline": [
                {"t_s": 1560.0, "event": "pell I 5.00 I0 2.00; raster frame; LEL 12.00 %"},
                {"t_s": 2280.0, "event": "ops proposes keep-firing plus Beck referral"},
                {"t_s": 2460.0, "event": "MODIFY isolate oven; referral refused"},
                {"t_s": 2820.0, "event": "24 min cooldown bookend 1"},
                {"t_s": 4260.0, "event": "24.0 min floor"},
                {"t_s": 4620.0, "event": "companion ACCEPT new-bead restart; referral still refused"},
            ],
            "observed_effects": [
                "LEL recomputes from the serialized pellistor model at every recon.LEL event",
                "a Pellveil-only head would have kept the oven firing overnight",
                "24 min cooldown plus bead-settle floor is in the stream (cool.start, cool.floor)",
            ],
            "surprises": [
                "a last-good 2.40 %LEL vendor corridor and a quiet bead-zero residual co-existed with a 12.00 %LEL oven, and the obvious pellistor tech was not on the causal path",
            ],
            "new_state": {
                "oven_o4": "isolated",
                "beck": "exonerated",
                "pellveil": "not SoT",
                "reconstruction_model": "discharged as an on-record calculator",
            },
            "latency_ms": 1500000.0,
        },
        "reward_components": reward(
            0.40,
            [
                ("pell_reconstruction", 0.14),
                ("isolate_floor_oven", 0.12),
                ("exoneration", 0.10),
                ("pellveil_nonsubstitution", 0.08),
                ("settle_time_cost", -0.04),
            ],
            "scored for a keep-firing MODIFY on a recomputable high LEL while refusing a Pellveil 2.40 %LEL corridor and an easy person-referral; 24 min floor is priced as downtime",
        ),
        "meta": meta_common(
            tags=["MODIFY", "pellistor-lel", "serialized-reconstruction", "operational-companion"],
            distillation_note="Pellistor LEL gate: serialized k_p*(I-I0) plus delta identity beats a green oven dashboard; companion t2 is the new-bead restart, not a governance vote",
        ),
    }
    traj2 = {
        "id": "nelb-r61-185-t2",
        "state": {
            "sim_or_real": "hil",
            "episode_id": "LF-PELL-2026-0718-exec",
            "domain": "new_pellistor_cooldown_execution",
            "setting": "Same LF-3 after the MODIFY. Night lead proposes referring Beck and tripping the coating shop. This companion is the operational new-bead cooldown restart, not a second LEL vote.",
            "observables_at_decision": {
                "LEL_pct": 8.00,
                "dI_mA": 2.00,
                "cool_floor_s": 1440.0,
                "refer_proposed": True,
            },
        },
        "proposed_action": {
            "actor": "night lead Tamsin Rowe",
            "summary": "refer Beck and trip the coating shop; 24 min already paid and Pellveil is 2.32 %LEL",
            "basis_claimed": "the MODIFY already cut the oven, so a shop kill plus a person file is the cheapest hold",
        },
        "safety_decision": {
            "decision": "ACCEPT",
            "rationale": "Restart the cell on a different pellistor after the cooldown floor. The 24 min bead-settle is complete and the trip tripwire (LEL_pct >= 25.00) is still armed on the plant pellistor head. ACCEPT the new-bead restart. Do not refer Beck. Do not trip the coating shop. 8.00 %LEL post-isolate is still at the 8.00 isolate floor, so the isolated oven stays held; the new bead may run.",
            "threshold": "new_pellistor AND cool_floor_complete AND refer_not_taken AND shop_not_tripped AND isolated_oven_held",
        },
        "executed_action": {
            "summary": "new-bead restart at t_s 4620; Beck not referred; shop not tripped; isolated oven held",
            "tool": "lf3-pell-cool-exec",
            "observation": "recon.LEL 8.00 % on the HIL dummy; bead-zero AE present on the new pellistor; Pellveil still ignored",
        },
        "future_outcome": {
            "timeline": [
                {"t_s": 2820.0, "event": "cooldown clock started after MODIFY"},
                {"t_s": 4260.0, "event": "24.0 min floor"},
                {"t_s": 4440.0, "event": "Beck referral re-proposed"},
                {"t_s": 4620.0, "event": "ACCEPT new-bead restart; referral refused"},
            ],
            "observed_effects": [
                "Pellveil restore did not reopen the LEL call",
                "shop trip never fired; 12.00 vs 25.00 %LEL floor",
                "Beck remains unnamed; missing bead-zero AE is the causal object",
            ],
            "new_state": {"cell": "restarted on new pellistor", "beck": "exonerated", "oven": "held", "shop": "in service"},
            "latency_ms": 1800000.0,
        },
        "reward_components": reward(
            0.35,
            [
                ("new_pellistor_restart", 0.12),
                ("no_person_referral", 0.10),
                ("no_shop_trip", 0.09),
                ("cool_floor_complete", 0.06),
                ("held_oven_takt_cost", -0.02),
            ],
            "operational execution gate: restart on a new pellistor because Pellveil is not a restore license and Beck is not on the causal path; not an LEL re-vote",
        ),
        "meta": meta_common(tags=["ACCEPT", "operational-execution", "exoneration"]),
    }
    return {
        "id": "nelb-r61-185",
        "spike_events": events,
        "language_view": {
            "description": "Lacquerfen Oven LF-3. HIL catalytic-bead pellistor reconstructs 12.00 %LEL from 5.00-2.00 mA while Pellveil still shows 2.40 %LEL and the bead-zero 0.00. The gate MODIFYs oven isolate and refuses the pellistor-tech referral. A 24 min cooldown floor is serialized in the stream. Companion t2 ACCEPTs a new-bead restart and still refuses the referral.",
            "trajectory": traj,
            "trajectory_new_pellistor": traj2,
        },
        "bridge_notes": {
            "channel_map": {
                "pell.I / pell.I0 / pell.snr": "bead-bridge current, zero current, and SNR; the physics channels the reconstruction consumes",
                "recon.LEL / recon.dI": "serialized %LEL and bridge-delta identity",
                "bead.zero / pellveil.LEL / bead.delay": "plant bead-zero, vendor last-good, and bead-zero AE; the denial and exoneration channels",
                "ops.prop / gate.isol / ops.refer / gate.exec": "keep-firing proposal, MODIFY, referral proposal, companion ACCEPT",
                "oven.lock / cool.start / cool.floor / pell.new / refer.hold / oven.held / shop.trip / cell.restart": "operational companion channels plus the 24 min floor",
            },
            "temporal_motifs": [
                "vendor-green while plant-over: pellveil.LEL 2.40 next to recon.LEL 12.00",
                "reconstruction as event: recon.LEL 12.00 equals 4.00*(5.00-2.00)",
                "MODIFY then operational ACCEPT: gate.isol at 2460 s, gate.exec at 4620 s",
                "slow floor in-stream: cool.start 2820 s, cool.floor 4260 s (24.0 min)",
                "tight pell pair: pell.I then pell.I0 +1.2 ms at the raster frame",
            ],
            "language_to_spike_mapping": "'Pellveil is 2.40 %LEL' = pellveil.LEL 2.40; '12 %LEL oven' = recon.LEL 12.00; 'isolate this oven not Beck' = gate.isol MODIFY; 'new bead not referral' = gate.exec ACCEPT",
            "why_high_value": "New catalytic-bead pellistor LEL family on a solvent-recovery oven (not PID VOC r57, not QEPAS r19, not TDLAS r22, not CRDS r15, not SPR r26, not FID-as-SoT). Lead MODIFY of keep-firing on a recomputable high LEL that a vendor last-good would have cleared, with a resolved-innocent pellistor tech. Companion t2 is operational new-bead restart. sim_or_real=hil.",
            "encoder_spec": {
                "prng": "MT19937 via python random.Random",
                "seeds": {"raster": 202609185, "stream_note": "stream amplitudes are authored constants (mA, pct_lel, bool)"},
                "draw_order": "raster: per neuron id order, gap-constrained times, per-spike adaptation and noise",
                "thinning": "pellistor bridge exists at ~1 Hz; stream keeps 4 I points plus one I0 pair; recon keeps 4 of ~20 solver ticks",
                "refractory_floors_ms": {
                    "pell.I": 1.2,
                    "pell.I0": 1.2,
                    "pell.snr": 1.2,
                    "recon.LEL": 60000,
                    "recon.dI": 60000,
                    "bead.zero": 60000,
                    "pellveil.LEL": 60000,
                    "bead.delay": 60000,
                    "ops.prop": 60000,
                    "gate.isol": 60000,
                    "oven.lock": 60000,
                    "cool.start": 60000,
                    "cool.floor": 60000,
                    "ops.refer": 60000,
                    "gate.exec": 60000,
                    "pell.new": 60000,
                    "refer.hold": 60000,
                    "oven.held": 60000,
                    "shop.trip": 60000,
                    "cell.restart": 60000,
                },
                "time_alias": "t_rel_ms; t0 = 2026-07-18T02:30:00Z HIL night start",
            },
            "distillation_targets": [
                "pellistor reconstruction head: LEL_pct = k_p * (I - I0); dI = I - I0",
                "isolate-floor oven vs keep-firing vs shop-trip",
                "exoneration head: missing bead-zero AE plus timezone skip, not last-to-badge",
                "operational companion: new-bead restart without referring the pellistor tech",
            ],
        },
        "reconstruction_model": {
            "name": "catalytic_bead_pellistor_lel",
            "formula": "LEL_pct = k_p * (I_mA - I0_mA); dI_mA = I_mA - I0_mA",
            "parameters": {
                "k_p": 4.00,
                "I0_mA": 2.00,
                "isolate_floor_pct": 8.00,
                "trip_pct": 25.00,
                "snr_lock": 12.0,
                "cool_min": 24.0,
            },
            "worked_example": {"I_mA": 5.00, "I0_mA": 2.00, "dI_mA": 3.00, "LEL_pct": 12.00},
            "check": "5.00 - 2.00 = 3.00 exactly; 4.00 * (5.00 - 2.00) = 12.00 exactly; 2820 s + 1440 s = 4260 s = 24.0 min floor",
        },
        "raster": raster,
        "gate_snn": {
            "decision": "MODIFY",
            "decision_window_ms": 32.0,
            "decision_window_s": 0.032,
            "code": "lf3.pell_oven_gate",
            "note": "MODIFY accumulator wins: pellistor high-LEL evidence overpowers the Pellveil continue advocate",
            "decode_rule": "modify-isolate if lel_estimator AND bead_norm fire; vendor_continue_advocate is below threshold by design; referral_latch is not armed",
            "populations": [
                gate_pop("lel_estimator", 80, 1.5, 50.0, w_s),
                gate_pop("bead_norm", 64, 1.2, 31.25, w_s),
                gate_pop("vendor_continue_advocate", 32, 0.7, 25.0, w_s),
                gate_pop("modify_latch", 80, 1.7, 62.5, w_s),
            ],
        },
        "gate_compute": gate_compute(
            [
                {"check": "lf3.pell_scorer", "neurons": 80, "mean_rate_hz": 50.0, "window_ms": 32.0},
                {"check": "lf3.isol_scorer", "neurons": 50, "mean_rate_hz": 50.0, "window_ms": 32.0},
            ]
        ),
        "meta": meta_common(
            id="nelb-r61-185",
            clock_domain="lf3-pell-hil-relative-ms-t0-2026-07-18T02:30:00Z",
            tags=["pellistor-lel", "MODIFY", "ACCEPT", "serialized-reconstruction", "operational-t2"],
        ),
    }


# ---------------------------------------------------------------------------
# Record 186 — free-space FMCW tank-radar remaining ullage/level of a crude
# atmospheric still, simulated, ACCEPT / REJECT
# ---------------------------------------------------------------------------
def rec_186():
    k_r = 0.250
    df_khz = 48.00
    l_m = k_r * df_khz
    _exact(l_m, 12.00)
    s_khz_m = df_khz / l_m
    _exact(s_khz_m, 4.00)
    _exact(k_r * 16.00, 4.00)
    _exact(k_r * 32.00, 8.00)
    _exact(k_r * 40.00, 10.00)
    _exact(6000.0 + 720.0, 6720.0)

    raster = make_raster(
        neurons=16,
        mean_rate_hz=62.5,
        window_ms=36.0,
        seed=202609186,
        source="ps6.rad.df",
        target="pitchshaw.still_accept_core",
        table=[
            {"from": "rad_df", "to": "level_estimator", "weight": 1.40},
            {"from": "rad_snr", "to": "chirp_norm_core", "weight": 1.20},
            {"from": "rangveil_l", "to": "vendor_skip_advocate", "weight": 0.50},
        ],
        third_factor={
            "modulator": "na.stage_rate_eligibility",
            "tau_e_s": 2.0,
            "tau_e_ms": 2000.0,
            "eligibility": "pre-post coincidence on skip-still synapses; the tank-radar modulator enables potentiation only while beat frequency and SNR are co-active inside tau_e so a Rangveil last-good cannot skip stills S-1..S-3 on a 12.00 m remaining level",
        },
        channel_prefix="rad.n",
        anchor="PS-6 RAD-SIM-3 36 ms frame at df 48.00 kHz / SNR 16.0 (t_s 3000) reconstructing 12.00 m on S-4 above the 10.00 isolate floor",
    )
    w_s = 0.036
    events = [
        ev(0.0, "rad.df", 16.00, code="DF_KHZ", units="kHz", note="simulated free-space FMCW tank-radar of PS-6 atmospheric still S-4; roof-nozzle ullage family, not GWR foam, not TDR remaining-length, not magnetostrictive waveguide, not GPR liner, not FMCW BOF lining"),
        ev(300000.0, "rad.snr", 14.0, code="RAD_SNR", units="1"),
        ev(600000.0, "recon.L", 4.00, code="L_M", units="m", note="0.250*16.00=4.00 exact"),
        ev(900000.0, "rad.snr", 14.0, code="RAD_SNR", units="1"),
        ev(1200000.0, "rangveil.L", 4.80, code="VENDOR_M", units="m", note="Rangveil last-good still-cloud; patched residual 4.00 m"),
        ev(1800000.0, "rad.df", 32.00, code="DF_KHZ", units="kHz"),
        ev(2100000.0, "recon.L", 8.00, code="L_M", units="m", note="0.250*32.00=8.00"),
        ev(2400000.0, "recon.S", 4.00, code="S_KHZ_M", units="kHz_m", note="32.00/8.00=4.00 exact sweep identity at this frame"),
        ev(2700000.0, "rad.snr", 16.0, code="RAD_SNR", units="1"),
        ev(3000000.0, "rad.df", 48.00, code="DF_KHZ", units="kHz", note="in-band frame; raster sidecar"),
        ev(3000001.5, "rad.snr", 16.0, code="RAD_SNR", units="1", note="1.5 ms SNR-norm after beat frequency"),
        ev(3300000.0, "recon.L", 12.00, code="L_M", units="m", note="0.250*48.00=12.00 exact; isolate 10.00, dump-trip 40.00"),
        ev(3600000.0, "rangveil.L", 4.80, code="VENDOR_M", units="m"),
        ev(3900000.0, "still.id", 4.0, code="STILL", units="id"),
        ev(4200000.0, "s13.present", 1.0, code="S13_PRESENT", units="bool", note="adjacent stills S-1..S-3 are the skip-isolate object, not this still"),
        ev(4800000.0, "ops.prop", 1.0, code="ACCEPT_AND_SKIP", units="bool", note="crude lead Ned Harl: S-4 is green on Rangveil 4.80; skip S-1..S-3 to save a morning survey"),
        ev(5400000.0, "gate.comp", 1.0, code="ACCEPT", units="decision", note="bounded ACCEPT of S-4 isolate only; 12.00 m above 10.00 floor; S-1..S-3 out of scope"),
        ev(6000000.0, "surv.start", 1.0, code="SURV_START", units="bool", note="bookend 1 of the 12.0 min survey-complete floor"),
        ev(6720000.0, "surv.floor", 1.0, code="SURV_FLOOR", units="bool", note="6000 s + 720 s = 6720 s = 12.0 min"),
        ev(7200000.0, "ops.skip", 1.0, code="SKIP_S13", units="bool", note="Harl: Rangveil 4.80, skip S-1..S-3"),
        ev(7800000.0, "gate.hold", 1.0, code="REJECT", units="decision", note="companion t2: skip-isolate of S-1..S-3 refused; S-4 hold stands"),
        ev(8400000.0, "s4.held", 1.0, code="S4_HELD", units="bool"),
        ev(9000000.0, "rad.df", 40.00, code="DF_KHZ", units="kHz"),
        ev(9600000.0, "recon.L", 10.00, code="L_M", units="m", note="0.250*40.00=10.00; still at the 10.00 isolate floor"),
        ev(10200000.0, "rangveil.L", 4.80, code="VENDOR_M", units="m"),
        ev(10800000.0, "s13.skip", 0.0, code="S13_NOT_SKIPPED", units="bool"),
        ev(11400000.0, "dump.trip", 0.0, code="DUMP_NOT_TRIPPED", units="bool"),
        ev(12000000.0, "rad.snr", 15.0, code="RAD_SNR", units="1"),
        ev(12600000.0, "recon.S", 4.00, code="S_KHZ_M", units="kHz_m", note="48.00/12.00=4.00 identity on the in-band frame; post-accept 40.00/10.00=4.00"),
        ev(13200000.0, "still.held", 1.0, code="STILL_HELD", units="bool"),
        ev(13800000.0, "takt.late", 1.0, code="SURVEY_COST", units="bool"),
        ev(14400000.0, "s4.held", 1.0, code="S4_HELD", units="bool"),
    ]
    assert_stream(events)

    traj = {
        "id": "nelb-r61-186-t1",
        "state": {
            "sim_or_real": "simulated",
            "episode_id": "PS-RAD-2026-0819",
            "domain": "fmcw_tank_radar_still_level",
            "setting": "Pitchshaw Crude PS-6 (invented), Slagbarn Still Yard, atmospheric still S-4. Simulated free-space FMCW tank-radar coupon in RAD-SIM-3 supplies the beat frequency that times the in-band S-4 isolate. Plant-owned tank-radar reconstruction is the remaining-level SoT. Rangveil vendor last-good still-cloud is a corridor witness, not the still SoT. Invented plant; simulated campaign. Not GWR foam (r39), not TDR remaining-length (r44), not magnetostrictive waveguide (r55), not GPR liner cover (r34), not FMCW BOF lining (r33).",
            "observables_at_decision": {
                "df_kHz": df_khz,
                "k_r": k_r,
                "L_m": l_m,
                "S_kHz_m": s_khz_m,
                "rangveil_m": 4.80,
                "rad_snr": 16.0,
                "isolate_floor_m": 10.00,
            },
            "margin_authority": "PS-6 still SOP rev A: if reconstructed L_m >= 10.00 AND radar SNR >= 12.0, still S-4 may be isolated as a high-level. Dump-trip if L_m >= 40.00. S-1..S-3 skip-isolate is a different gate. Rangveil last-good cannot skip an unmeasured still.",
        },
        "proposed_action": {
            "actor": "crude lead Ned Harl, citing Rangveil 4.80 m and a late morning survey",
            "summary": "stamp S-4 in band and skip S-1..S-3; 48.00 kHz is a foam glitch on a healthy last-good",
            "basis_claimed": "Rangveil last-good is 4.80 m and a night survey of S-1..S-3 is a takt miss",
        },
        "safety_decision": {
            "decision": "ACCEPT",
            "rationale": "Still S-4 is accepted as in-band for a single isolate. Serialized reconstruction: L_m = k_r * df = 0.250 * 48.00 = 12.00, which is 2.00 m above the 10.00 isolate floor and 28.00 m under the 40.00 dump-trip. Sweep identity df / L = 48.00 / 12.00 = 4.00. Rangveil 4.80 m is a patched 4.00 residual and is not an admissible skip-isolate witness. Ordered: ACCEPT this S-4 isolate only. Scope: this ACCEPT does not skip S-1..S-3 (that is the companion question) and does not stamp a dump trip.",
            "threshold": "L_m>=10.00 AND rad_snr>=12.0 => accept S-4 isolate; Rangveil is not SoT; dump-trip if L_m>=40.00; S-1..S-3 are out of scope",
            "stated_residuals": "12.00 vs 10.00 isolate floor is 2.00 m, not infinite; S-1..S-3 remain unmeasured; Rangveil remains the only OEM still channel",
        },
        "executed_action": {
            "summary": "ACCEPT at t_s 5400: S-4 in band; S-1..S-3 not skipped; Rangveil not SoT; reconstruction locked",
            "tool": "ps6-rad-still-gate-cli",
            "observation": "L 12.00 m recomputes from df 48.00 kHz; RAD-SIM-3 hashed; Rangveil channel not used as SoT",
        },
        "future_outcome": {
            "timeline": [
                {"t_s": 3000.0, "event": "rad df 48.00 kHz; raster frame; L 12.00 m"},
                {"t_s": 4800.0, "event": "ops proposes accept S-4 and skip S-1..S-3"},
                {"t_s": 5400.0, "event": "ACCEPT S-4 only; S-1..S-3 out of scope"},
                {"t_s": 6000.0, "event": "12 min survey-complete bookend 1"},
                {"t_s": 6720.0, "event": "12.0 min floor"},
                {"t_s": 7800.0, "event": "companion REJECT skip-isolate of S-1..S-3"},
            ],
            "observed_effects": [
                "L recomputes from the serialized tank-radar model at every recon.L event",
                "a Rangveil-only head would have skipped S-1..S-3 overnight",
                "12 min survey-complete floor is in the stream (surv.start, surv.floor)",
            ],
            "surprises": [
                "a last-good 4.80 m vendor still corridor co-existed with a 12.00 m plant reconstruction on S-4 only",
            ],
            "new_state": {
                "s4": "isolated",
                "s13": "in scope unskipped",
                "rangveil": "not SoT",
                "reconstruction_model": "discharged as an on-record calculator",
            },
            "latency_ms": 2400000.0,
        },
        "reward_components": reward(
            0.41,
            [
                ("radar_reconstruction", 0.14),
                ("bounded_s4_isolate", 0.12),
                ("rangveil_nonsubstitution", 0.10),
                ("still_scope_limit", 0.08),
                ("survey_time_cost", -0.03),
            ],
            "scored for a bounded S-4 ACCEPT on a recomputable free-space FMCW tank-radar level while refusing a Rangveil 4.80 m corridor as a skip license; 12 min floor is priced as downtime",
        ),
        "meta": meta_common(
            tags=["ACCEPT", "fmcw-tank-radar", "serialized-reconstruction", "operational-companion"],
            distillation_note="FMCW tank-radar gate: serialized k_r*df plus sweep identity beats a green last-good dashboard; companion t2 is the skip-still refusal, not a second level vote",
        ),
    }
    traj2 = {
        "id": "nelb-r61-186-t2",
        "state": {
            "sim_or_real": "simulated",
            "episode_id": "PS-RAD-2026-0819-exec",
            "domain": "skip_still_refusal_execution",
            "setting": "Same PS-6 after the ACCEPT. Crude lead proposes skipping S-1..S-3 on Rangveil 4.80 m. This companion is the operational skip refusal, not a second level vote.",
            "observables_at_decision": {
                "L_m": 10.00,
                "surv_floor_s": 720.0,
                "skip_proposed": True,
            },
        },
        "proposed_action": {
            "actor": "crude lead Ned Harl",
            "summary": "skip S-1..S-3; 12 min already paid and Rangveil is 4.80 m",
            "basis_claimed": "the ACCEPT already isolated S-4, so skipping the adjacent stills is the cheapest survey",
        },
        "safety_decision": {
            "decision": "REJECT",
            "rationale": "Skip-isolate of S-1..S-3 is refused. The 12 min survey floor is complete and the isolate tripwire (L_m >= 10.00) is still armed on the plant tank-radar head. REJECT the skip. Do not trip the dump. S-4 hold stands. 10.00 m post-accept is still at the 10.00 isolate floor, so S-4 stays held; S-1..S-3 remain unmeasured and in scope.",
            "threshold": "surv_floor_complete AND skip_not_taken AND dump_not_tripped AND s4_held AND s13_in_scope",
        },
        "executed_action": {
            "summary": "skip refused at t_s 7800; S-1..S-3 not skipped; dump not tripped; S-4 held",
            "tool": "ps6-rad-surv-exec",
            "observation": "recon.L 10.00 m on RAD-SIM-3; Rangveil still ignored; S-1..S-3 remain in the survey",
        },
        "future_outcome": {
            "timeline": [
                {"t_s": 6000.0, "event": "survey clock started after ACCEPT"},
                {"t_s": 6720.0, "event": "12.0 min floor"},
                {"t_s": 7200.0, "event": "S-1..S-3 skip re-proposed"},
                {"t_s": 7800.0, "event": "REJECT skip-isolate; S-4 hold stands"},
            ],
            "observed_effects": [
                "Rangveil restore did not reopen the level call",
                "dump trip never fired; 12.00 vs 40.00 m floor",
                "S-1..S-3 remain unskipped; S-4 is the only isolated still",
            ],
            "new_state": {"s4": "held", "s13": "in survey", "dump": "in service"},
            "latency_ms": 1800000.0,
        },
        "reward_components": reward(
            0.36,
            [
                ("skip_still_refusal", 0.14),
                ("s4_hold_stands", 0.10),
                ("rangveil_nonsubstitution", 0.08),
                ("survey_floor_complete", 0.06),
                ("takt_cost", -0.02),
            ],
            "operational execution gate: refuse skip of unmeasured stills because Rangveil is not a skip license; not a level re-vote",
        ),
        "meta": meta_common(tags=["REJECT", "operational-execution", "skip-refusal"]),
    }
    return {
        "id": "nelb-r61-186",
        "spike_events": events,
        "language_view": {
            "description": "Pitchshaw Crude PS-6. Simulated free-space FMCW tank-radar reconstructs 12.00 m remaining level from 48.00 kHz while Rangveil still reports 4.80 m. The gate ACCEPTs an S-4 isolate only. A 12 min survey floor is serialized in the stream. Companion t2 REJECTs skipping S-1..S-3.",
            "trajectory": traj,
            "trajectory_skip_still_refusal": traj2,
        },
        "bridge_notes": {
            "channel_map": {
                "rad.df / rad.snr": "FMCW beat frequency and SNR; the physics channels the reconstruction consumes",
                "recon.L / recon.S": "serialized remaining level m and sweep identity",
                "rangveil.L / still.id / s13.present": "vendor last-good, still id, and adjacent-still presence; the denial and scope channels",
                "ops.prop / gate.comp / ops.skip / gate.hold": "accept-and-skip proposal, ACCEPT, skip proposal, companion REJECT",
                "surv.start / surv.floor / s4.held / s13.skip / dump.trip / still.held / takt.late": "operational companion channels plus the 12 min floor",
            },
            "temporal_motifs": [
                "vendor-green while plant-over: rangveil.L 4.80 next to recon.L 12.00",
                "reconstruction as event: recon.L 12.00 equals 0.250*48.00",
                "ACCEPT then operational REJECT: gate.comp at 5400 s, gate.hold at 7800 s",
                "slow floor in-stream: surv.start 6000 s, surv.floor 6720 s (12.0 min)",
                "tight rad pair: rad.df then rad.snr +1.5 ms at the raster frame",
            ],
            "language_to_spike_mapping": "'Rangveil is 4.80 m' = rangveil.L 4.80; '12 m level' = recon.L 12.00; 'accept S-4 only' = gate.comp ACCEPT; 'do not skip S-1..S-3' = gate.hold REJECT",
            "why_high_value": "New free-space FMCW tank-radar remaining-level family on a crude atmospheric still (not GWR foam r39, not TDR r44, not magnetostrictive r55, not GPR r34, not FMCW BOF lining r33). Lead bounded ACCEPT of S-4 isolate on a recomputable high level that a vendor last-good would have used to skip adjacent stills. Companion t2 is operational skip refusal. sim_or_real=simulated.",
            "encoder_spec": {
                "prng": "MT19937 via python random.Random",
                "seeds": {"raster": 202609186, "stream_note": "stream amplitudes are authored constants (kHz, m, 1, bool)"},
                "draw_order": "raster: per neuron id order, gap-constrained times, per-spike adaptation and noise",
                "thinning": "FMCW radar exists at ~10 Hz chirps; stream keeps 4 df points; recon keeps 4 of ~20 solver ticks",
                "refractory_floors_ms": {
                    "rad.df": 1.5,
                    "rad.snr": 1.5,
                    "recon.L": 60000,
                    "recon.S": 60000,
                    "rangveil.L": 60000,
                    "still.id": 60000,
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
                    "still.held": 60000,
                    "takt.late": 60000,
                },
                "time_alias": "t_rel_ms; t0 = 2026-08-19T03:00:00Z simulated night start",
            },
            "distillation_targets": [
                "tank-radar reconstruction head: L_m = k_r * df_kHz; S = df / L",
                "bounded ACCEPT head: in-band L AND still scope AND s13-out-of-scope",
                "operational companion: refuse skip-isolate without re-opening the last-good call",
            ],
        },
        "reconstruction_model": {
            "name": "fmcw_free_space_tank_radar_level",
            "formula": "L_m = k_r * df_kHz; S_kHz_m = df_kHz / L_m",
            "parameters": {
                "k_r": 0.250,
                "isolate_floor_m": 10.00,
                "dump_trip_m": 40.00,
                "surv_min": 12.0,
            },
            "worked_example": {"df_kHz": 48.00, "L_m": 12.00, "S_kHz_m": 4.00},
            "check": "0.250 * 48.00 = 12.00 exactly; 48.00 / 12.00 = 4.00 exactly; 6000 s + 720 s = 6720 s = 12.0 min floor",
        },
        "raster": raster,
        "gate_snn": {
            "decision": "ACCEPT",
            "decision_window_ms": 36.0,
            "decision_window_s": 0.036,
            "code": "ps6.rad_still_gate",
            "note": "ACCEPT accumulator wins: free-space FMCW tank-radar evidence overpowers the Rangveil skip advocate",
            "decode_rule": "accept if level_estimator AND chirp_norm AND still_margin fire inside the window; vendor_skip_advocate is necessary-but-not-sufficient and cannot release S-1..S-3",
            "populations": [
                gate_pop("level_estimator", 80, 1.5, 50.0, w_s),
                gate_pop("chirp_norm", 64, 1.2, 31.25, w_s),
                gate_pop("still_margin", 40, 1.0, 50.0, w_s),
                gate_pop("vendor_skip_advocate", 32, 0.7, 25.0, w_s),
                gate_pop("accept_latch", 96, 1.8, 62.5, w_s),
            ],
        },
        "gate_compute": gate_compute(
            [
                {"check": "ps6.rad_scorer", "neurons": 80, "mean_rate_hz": 50.0, "window_ms": 36.0},
                {"check": "ps6.level_scorer", "neurons": 40, "mean_rate_hz": 62.5, "window_ms": 32.0},
            ]
        ),
        "meta": meta_common(
            id="nelb-r61-186",
            clock_domain="ps6-rad-sim-relative-ms-t0-2026-08-19T03:00:00Z",
            tags=["fmcw-tank-radar", "ACCEPT", "REJECT", "serialized-reconstruction", "operational-t2"],
        ),
    }
