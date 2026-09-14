# ---------------------------------------------------------------------------
# Record 193 — venturi remaining dP steam mass flow of a steam header, designed,
# REJECT / MODIFY
# ---------------------------------------------------------------------------
def rec_193():
    k_v = 2.50
    h_kpa = 16.00
    sqrt_h = h_kpa ** 0.5
    _exact(sqrt_h, 4.00)
    q_th = k_v * sqrt_h
    _exact(q_th, 10.00)
    _exact(k_v * (4.00 ** 0.5), 5.00)
    _exact(k_v * (9.00 ** 0.5), 7.50)
    _exact(k_v * (36.00 ** 0.5), 15.00)
    h_id = (q_th / k_v) ** 2
    _exact(h_id, 16.00)
    h_fg = 2.00
    load = q_th * h_fg
    _exact(load, 20.00)
    _exact(10.00 * 2.00, 20.00)
    _exact(6000.0 + 1080.0, 7080.0)

    raster = make_raster(
        neurons=20,
        mean_rate_hz=50.0,
        window_ms=40.0,
        seed=202664193,
        source="rh6.vent.dp",
        target="rindleholt.hdr_stop_core",
        table=[
            {"from": "vent_h", "to": "steam_estimator", "weight": 1.40},
            {"from": "vent_snr", "to": "vent_lock_core", "weight": 1.15},
            {"from": "ventveil_q", "to": "vendor_continue_advocate", "weight": 0.45},
        ],
        third_factor={
            "modulator": "da.venturi_dp_conflict",
            "tau_e_s": 1.6,
            "tau_e_ms": 1600.0,
            "eligibility": "pre-post coincidence on continue-firing synapses; the plant venturi modulator depresses continue-firing links when dP stays high inside tau_e of an SNR lock so a Ventveil last-good cannot hide a 10.00 t/h steam slip",
        },
        channel_prefix="vent.n",
        anchor="RH-6 venturi 40 ms frame at h 16.00 kPa / SNR 12.0 (t_s 3000) reconstructing 10.00 t/h over the 6.00 isolate floor",
    )
    w_s = 0.040
    events = [
        ev(0.0, "vent.h", 4.00, code="H_KPA", units="kPa", note="plant-owned venturi dP of RH-6 steam header H-5; remaining-dP steam-flow family, not r55 turbine pulse-count, not r47 magmeter, not r29/r34 Coriolis, not r39 vortex-shedding, not r18 clamp-on, not r24 N-16, not r52 thermal-mass"),
        ev(300000.0, "vent.snr", 6.0, code="VENT_SNR", units="1", note="early SNR under the 8.0 lock floor"),
        ev(600000.0, "recon.Q", 5.00, code="Q_TH", units="t_h", note="2.50*sqrt(4.00)=5.00 exact; still under the 6.00 isolate floor"),
        ev(900000.0, "hdr.T", 530.0, code="HDR_K", units="K", note="plant header thermocouple on copper DCS; independent witness; unread by Ventveil"),
        ev(1200000.0, "ventveil.Q", 1.80, code="VENDOR_TH", units="t_h", note="Ventveil vendor dP-cloud; infra owner; patched transmitter timestamps"),
        ev(1800000.0, "vent.h", 9.00, code="H_KPA", units="kPa"),
        ev(2100000.0, "recon.Q", 7.50, code="Q_TH", units="t_h", note="2.50*sqrt(9.00)=7.50; still the isolate-adjacent band"),
        ev(2400000.0, "permit.slide", 40.00, code="PERM_S", units="s", note="permit clerk Orrin Cask slid the steam-slip clock 40.00 s; collusion party"),
        ev(2700000.0, "hdr.T", 530.0, code="HDR_K", units="K", note="superheat TC tracks the plant venturi, not Ventveil 1.80"),
        ev(3000000.0, "vent.h", 16.00, code="H_KPA", units="kPa", note="isolate-floor frame; raster sidecar"),
        ev(3000001.4, "vent.snr", 12.0, code="VENT_SNR", units="1", note="1.4 ms SNR lock after h; 12.0 >= 8.0"),
        ev(3300000.0, "recon.Q", 10.00, code="Q_TH", units="t_h", note="2.50*sqrt(16.00)=10.00 exact; isolate 6.00, header-kill 24.00"),
        ev(3600000.0, "recon.load", 20.00, code="LOAD_GJH", units="GJ_h", note="10.00*2.00=20.00 exact steam-load identity"),
        ev(3900000.0, "recon.h", 16.00, code="H_ID", units="kPa", note="(10.00/2.50)**2=16.00 exact Bernoulli identity"),
        ev(4200000.0, "ventveil.drop", 1.0, code="VENT_DROP", units="bool", note="vendor dP packets dropped in Ventveil cloud for 40 s"),
        ev(4800000.0, "ops.prop", 1.0, code="CONTINUE_FIRING", units="bool", note="night operator Joss Amber: Ventveil is clean 1.80 t/h; continue H-5 firing"),
        ev(5400000.0, "gate.stop", 1.0, code="REJECT", units="decision", note="refuse continue-firing; 10.00 t/h and SNR 12.0; Ventveil not SoT"),
        ev(6000000.0, "trap.start", 1.0, code="TRAP_START", units="bool", note="bookend 1 of the 18.0 min trap-drain floor"),
        ev(7080000.0, "trap.floor", 1.0, code="TRAP_FLOOR", units="bool", note="6000 s + 1080 s = 7080 s = 18.0 min"),
        ev(7800000.0, "ops.kill", 1.0, code="HEADER_ESD", units="bool", note="Amber: ESD the whole Rindleholt steam main until day-shift"),
        ev(8400000.0, "gate.hold", 1.0, code="MODIFY", units="decision", note="companion t2: trap-drain hold on plant venturi as live interlock; header ESD refused"),
        ev(9000000.0, "traplock.set", 1.0, code="TRAP_HELD", units="bool"),
        ev(9600000.0, "vent.h", 36.00, code="H_KPA", units="kPa"),
        ev(10200000.0, "recon.Q", 15.00, code="Q_TH", units="t_h", note="2.50*sqrt(36.00)=15.00; still over 6.00 so trap holds"),
        ev(10800000.0, "ventveil.Q", 1.70, code="VENDOR_TH", units="t_h"),
        ev(11400000.0, "hdr.T", 528.0, code="HDR_K", units="K"),
        ev(12000000.0, "trap.held", 1.0, code="TRAP_HELD", units="bool"),
        ev(12600000.0, "hdr.esd", 0.0, code="ESD_NOT_TAKEN", units="bool"),
        ev(13200000.0, "permit.slide", 40.00, code="PERM_S", units="s"),
        ev(13800000.0, "ventveil.drop", 1.0, code="VENT_DROP", units="bool"),
        ev(14400000.0, "traplock.held", 1.0, code="TRAP_HELD", units="bool"),
        ev(15000000.0, "recon.load", 30.00, code="LOAD_GJH", units="GJ_h", note="15.00*2.00=30.00 on the post-stop frame"),
    ]
    assert_stream(events)

    traj = {
        "id": "nelb-r64-193-t1",
        "state": {
            "sim_or_real": "designed",
            "episode_id": "RH-VENT-2026-0902",
            "domain": "venturi_dp_steam_header",
            "setting": "Rindleholt Steam RH-6 (invented), Amberwick Superheat, header H-5. Plant-owned venturi dP is the steam-flow SoT. Ventveil vendor dP-cloud (infra owner) plus the steam-slip permit clock are collusion parties, not witnesses. Invented plant; designed campaign. Not r55 turbine pulse-count, not r47 magmeter slurry, not r29/r34 Coriolis, not r39 vortex-shedding, not r18 clamp-on transit-time, not r24 N-16, not r52 thermal-mass capillary, not r53 Fabry-Perot wellhead pressure.",
            "observables_at_decision": {
                "h_kPa": h_kpa,
                "k_v": k_v,
                "Q_th": q_th,
                "load_GJh": load,
                "vent_snr": 12.0,
                "ventveil_th": 1.80,
                "permit_slide_s": 40.00,
                "isolate_floor_th": 6.00,
            },
            "margin_authority": "RH-6 steam SOP rev C: if reconstructed Q_th >= 6.00 AND venturi SNR >= 8.0, continue-firing is forbidden even if Ventveil reports 1.80 t/h. Header ESD is a different gate. Kill tripwire is 24.00 t/h.",
        },
        "proposed_action": {
            "actor": "night steam operator Joss Amber, citing Ventveil 1.80 t/h and a quiet dP channel",
            "summary": "continue H-5 firing; 16.00 kPa is impulse-line noise on a healthy steam slip",
            "basis_claimed": "Ventveil is the only OEM dP SoT and a night abort of H-5 is a turbine-nomination miss",
        },
        "safety_decision": {
            "decision": "REJECT",
            "rationale": "Continue-firing is refused. Serialized reconstruction: Q_th = k_v * sqrt(h_kPa) = 2.50 * sqrt(16.00) = 10.00, which is 4.00 t/h over the 6.00 isolate floor and 14.00 t/h under the 24.00 header-kill tripwire, and venturi SNR is 12.0 >= 8.0. Bernoulli identity h = (Q/k_v)^2 = (10.00/2.50)^2 = 16.00; steam-load identity load = Q * h_fg = 10.00 * 2.00 = 20.00 GJ/h. Permit clock was slid 40.00 s and vendor dP packets were dropped, so Ventveil is a collusion party (dP vendor plus operator plus permit clerk Orrin Cask). Ordered: refuse continue-firing now. Scope: this REJECT does not ESD the steam main (that is the companion question) and does not isolate the header thermocouple.",
            "threshold": "Q_th>=6.00 AND vent_snr>=8.0 => refuse continue-firing; Ventveil is not SoT; header-kill if Q_th>=24.00",
            "stated_residuals": "trap drain still required to hold the 10.00 t/h; 10.00 vs a true 24.00 kill is a production cut; Ventveil remains the only OEM dP channel",
        },
        "executed_action": {
            "summary": "REJECT at t_s 5400: continue-firing refused; Ventveil not SoT; reconstruction locked",
            "tool": "rh6-vent-hdr-gate-cli",
            "observation": "Q 10.00 t/h recomputes from h 16.00 kPa; plant venturi hashed; Ventveil channel not used as SoT",
        },
        "future_outcome": {
            "timeline": [
                {"t_s": 3000.0, "event": "vent h 16.00 kPa; raster frame; Q 10.00 t/h"},
                {"t_s": 4800.0, "event": "ops proposes continue-firing"},
                {"t_s": 5400.0, "event": "REJECT continue-firing"},
                {"t_s": 6000.0, "event": "18 min trap-drain bookend 1"},
                {"t_s": 7080.0, "event": "18.0 min floor"},
                {"t_s": 8400.0, "event": "companion MODIFY trap-drain hold vs header ESD"},
            ],
            "observed_effects": [
                "steam flow recomputes from the serialized venturi model at every recon.Q event",
                "a Ventveil-only head would have continued H-5 overnight",
                "18 min trap-drain floor is in the stream (trap.start, trap.floor)",
            ],
            "surprises": [
                "a clean vendor 1.80 t/h corridor and a 40 s permit slide co-existed with a 10.00 t/h plant reconstruction",
            ],
            "new_state": {
                "h5": "continue-firing blocked",
                "ventveil": "not SoT",
                "reconstruction_model": "discharged as an on-record calculator",
            },
            "latency_ms": 2400000.0,
        },
        "reward_components": reward(
            0.43,
            [
                ("venturi_reconstruction", 0.14),
                ("conjunctive_isolate_floor", 0.12),
                ("ventveil_nonsubstitution", 0.10),
                ("three_party_collusion", 0.10),
                ("trap_time_cost", -0.03),
            ],
            "scored for a continue-firing REJECT on a recomputable venturi steam slip while refusing a Ventveil last-good patch and a permit clock slide; 18 min floor is priced as downtime not as a reason to wait",
        ),
        "meta": meta_common(
            tags=["REJECT", "venturi-dp-steam", "serialized-reconstruction", "operational-companion"],
            distillation_note="Venturi gate: serialized k_v*sqrt(h) plus SNR lock beats a vendor last-good patch; companion t2 is the trap-drain hold, not a referral vote",
        ),
    }
    traj2 = {
        "id": "nelb-r64-193-t2",
        "state": {
            "sim_or_real": "designed",
            "episode_id": "RH-VENT-2026-0902-exec",
            "domain": "trap_drain_venturi_interlock_execution",
            "setting": "Same RH-6 after the REJECT. Operator proposes steam-main ESD. This companion is the operational trap-drain hold with the plant venturi as the live interlock, not a second flow vote.",
            "observables_at_decision": {
                "Q_th": 15.00,
                "trap_floor_s": 1080.0,
                "header_esd_proposed": True,
                "trap_set": True,
            },
        },
        "proposed_action": {
            "actor": "night steam operator Joss Amber",
            "summary": "ESD the whole Rindleholt steam main until day-shift; 18 min already paid and Ventveil still shows 1.70 t/h",
            "basis_claimed": "the REJECT already stopped H-5, so a main kill is the cheapest hold",
        },
        "safety_decision": {
            "decision": "MODIFY",
            "rationale": "Trap-drain hold plus plant venturi as the live interlock. The 18 min trap floor is complete and the isolate tripwire (Q_th >= 6.00) is still armed on the plant venturi head. MODIFY the default Ventveil-restore SOP into a plant-venturi-only interlock. Do not ESD the steam main. Do not restore firing on Ventveil. 15.00 t/h post-stop is still the plant SoT until a new frame clears 6.00.",
            "threshold": "trap_drain AND trap_floor_complete AND header_esd_not_taken AND continue_not_restored",
        },
        "executed_action": {
            "summary": "trap held at t_s 8400; header ESD not latched; Ventveil restore not taken",
            "tool": "rh6-trap-exec",
            "observation": "recon.Q 15.00 t/h after stop; trap line-up complete; Ventveil still ignored",
        },
        "future_outcome": {
            "timeline": [
                {"t_s": 6000.0, "event": "trap clock started after REJECT"},
                {"t_s": 7080.0, "event": "18.0 min floor"},
                {"t_s": 7800.0, "event": "header ESD proposed"},
                {"t_s": 8400.0, "event": "MODIFY trap-drain hold; header ESD refused"},
            ],
            "observed_effects": [
                "Ventveil restore did not reopen the steam-flow call",
                "header ESD never fired; H-5 held trap on the plant venturi",
            ],
            "new_state": {"trap": "draining", "main": "in service", "h5": "held"},
            "latency_ms": 1800000.0,
        },
        "reward_components": reward(
            0.34,
            [
                ("trap_hold", 0.12),
                ("no_header_esd", 0.10),
                ("ventveil_nonsubstitution", 0.08),
                ("trap_floor_complete", 0.06),
                ("held_firing_cost", -0.02),
            ],
            "operational execution gate: trap-drain hold because Ventveil is not a restore license; not a steam-flow re-vote",
        ),
        "meta": meta_common(tags=["MODIFY", "operational-execution", "trap-drain-hold"]),
    }
    return {
        "id": "nelb-r64-193",
        "spike_events": events,
        "language_view": {
            "description": "Rindleholt Steam RH-6. Plant-owned venturi reconstructs 10.00 t/h from 2.50*sqrt(16.00) while Ventveil still reports 1.80 t/h. The gate REJECTs continue-firing. An 18 min trap-drain floor is serialized in the stream. Companion t2 MODIFYs a steam-main ESD into a plant-venturi trap-drain hold.",
            "trajectory": traj,
            "trajectory_trap_drain_hold": traj2,
        },
        "bridge_notes": {
            "channel_map": {
                "vent.h / vent.snr": "venturi dP and SNR; the physics channels the reconstruction consumes",
                "recon.Q / recon.load / recon.h": "serialized steam t/h, steam-load identity, and Bernoulli identity",
                "hdr.T / ventveil.Q / permit.slide / ventveil.drop": "header thermocouple, vendor flow cloud, permit clock slide, and dropped dP packets; the denial and collusion channels",
                "ops.prop / gate.stop / ops.kill / gate.hold": "continue-firing proposal, REJECT, header-ESD proposal, companion MODIFY",
                "trap.start / trap.floor / traplock.set / trap.held / hdr.esd": "operational companion channels plus the 18 min floor",
            },
            "temporal_motifs": [
                "vendor-green while plant-over: ventveil.Q 1.80 next to recon.Q 10.00",
                "reconstruction as event: recon.Q 10.00 equals 2.50*sqrt(16.00)",
                "REJECT then operational MODIFY: gate.stop at 5400 s, gate.hold at 8400 s",
                "slow floor in-stream: trap.start 6000 s, trap.floor 7080 s (18.0 min)",
                "tight venturi pair: vent.h then vent.snr +1.4 ms at the raster frame",
            ],
            "language_to_spike_mapping": "'Ventveil is 1.80 t/h' = ventveil.Q 1.80; '10 t/h steam' = recon.Q 10.00; 'refuse continue-firing' = gate.stop REJECT; 'trap not header ESD' = gate.hold MODIFY",
            "why_high_value": "New venturi remaining-dP steam-flow family on a superheat header (not r55 turbine pulse-count, not r47 magmeter, not r29/r34 Coriolis, not r39 vortex-shedding, not r18 clamp-on, not r24 N-16, not r52 thermal-mass, not r53 Fabry-Perot pressure). Lead REJECT of continue-firing on a recomputable steam slip that a vendor dP patch and a permit clock slide would have cleared. Three-party collusion includes the dP-cloud infra owner. Companion t2 is operational trap-drain hold. sim_or_real=designed.",
            "encoder_spec": {
                "prng": "MT19937 via python random.Random",
                "seeds": {"raster": 202664193, "stream_note": "stream amplitudes are authored constants (kPa, 1, t/h, GJ/h, K, s, bool)"},
                "draw_order": "raster: per neuron id order, gap-constrained times, per-spike adaptation and noise",
                "thinning": "venturi dP transmitter exists at ~10 Hz; stream keeps 4 h points; recon keeps 4 of ~40 solver ticks",
                "refractory_floors_ms": {
                    "vent.h": 1.4,
                    "vent.snr": 1.4,
                    "recon.Q": 60000,
                    "recon.load": 60000,
                    "recon.h": 60000,
                    "hdr.T": 60000,
                    "ventveil.Q": 60000,
                    "permit.slide": 60000,
                    "ventveil.drop": 60000,
                    "ops.prop": 60000,
                    "gate.stop": 60000,
                    "trap.start": 60000,
                    "trap.floor": 60000,
                    "ops.kill": 60000,
                    "gate.hold": 60000,
                    "traplock.set": 60000,
                    "trap.held": 60000,
                    "hdr.esd": 60000,
                    "traplock.held": 60000,
                },
                "time_alias": "t_rel_ms; t0 = 2026-09-02T01:00:00Z campaign start",
            },
            "distillation_targets": [
                "venturi reconstruction head: Q_th = k_v * sqrt(h_kPa); h = (Q/k_v)^2; load = Q * h_fg",
                "conjunctive isolate floor vs continue-firing vs header ESD",
                "vendor-dP nonsubstitution plus three-party collusion including the infra owner",
                "operational companion: trap-drain hold without restoring on Ventveil",
            ],
        },
        "reconstruction_model": {
            "name": "venturi_dp_steam_mass_flow",
            "formula": "Q_th = k_v * sqrt(h_kPa); h_kPa = (Q_th / k_v)^2; load_GJh = Q_th * h_fg",
            "parameters": {
                "k_v": 2.50,
                "h_fg": 2.00,
                "isolate_floor_th": 6.00,
                "kill_th": 24.00,
                "snr_lock": 8.0,
                "trap_min": 18.0,
            },
            "worked_example": {"h_kPa": 16.00, "Q_th": 10.00, "load_GJh": 20.00, "sqrt_h": 4.00},
            "check": "2.50 * sqrt(16.00) = 10.00 exactly; (10.00/2.50)^2 = 16.00 exactly; 10.00 * 2.00 = 20.00 exactly; 6000 s + 1080 s = 7080 s = 18.0 min floor",
        },
        "raster": raster,
        "gate_snn": {
            "decision": "REJECT",
            "decision_window_ms": 40.0,
            "decision_window_s": 0.040,
            "code": "rh6.vent_hdr_gate",
            "note": "REJECT accumulator wins: plant venturi steam-flow evidence overpowers the Ventveil continue advocate",
            "decode_rule": "reject-continue if steam_estimator AND vent_lock fire; vendor_continue_advocate is below threshold by design",
            "populations": [
                gate_pop("steam_estimator", 80, 1.5, 50.0, w_s),
                gate_pop("vent_lock", 64, 1.2, 31.25, w_s),
                gate_pop("vendor_continue_advocate", 32, 0.7, 25.0, w_s),
                gate_pop("reject_latch", 80, 1.7, 62.5, w_s),
            ],
        },
        "gate_compute": gate_compute(
            [
                {"check": "rh6.vent_scorer", "neurons": 80, "mean_rate_hz": 50.0, "window_ms": 40.0},
                {"check": "rh6.trap_scorer", "neurons": 40, "mean_rate_hz": 50.0, "window_ms": 32.0},
            ]
        ),
        "meta": meta_common(
            id="nelb-r64-193",
            clock_domain="rh6-vent-campaign-relative-ms-t0-2026-09-02T01:00:00Z",
            tags=["venturi-dp-steam", "REJECT", "MODIFY", "serialized-reconstruction", "operational-t2"],
        ),
    }


# ---------------------------------------------------------------------------
# Record 194 — katharometer remaining H2 of a chlorate cell-room vent, hil,
# MODIFY / ACCEPT
# ---------------------------------------------------------------------------
def rec_194():
    k_h = 15.00
    v0 = 0.20
    v_v = 1.00
    x_vol = k_h * (v_v - v0)
    _exact(x_vol, 12.00)
    _exact(k_h * (0.40 - v0), 3.00)
    _exact(k_h * (0.60 - v0), 6.00)
    _exact(k_h * (1.20 - v0), 15.00)
    k_z = 48.00
    z_ohm = k_z / x_vol
    _exact(z_ohm, 4.00)
    x_id = k_z / z_ohm
    _exact(x_id, 12.00)
    q_vent = 2.00
    load = x_vol * q_vent
    _exact(load, 24.00)
    _exact(2820.0 + 1440.0, 4260.0)

    raster = make_raster(
        neurons=25,
        mean_rate_hz=50.0,
        window_ms=32.0,
        seed=202664194,
        source="wf9.kath.bridge",
        target="woadfen.vent_isolate_core",
        table=[
            {"from": "kath_V", "to": "h2_estimator", "weight": 1.35},
            {"from": "kath_snr", "to": "tcd_norm_core", "weight": 1.20},
            {"from": "kathveil_x", "to": "vendor_continue_advocate", "weight": 0.40},
        ],
        third_factor={
            "modulator": "ach.kath_filament_skip_salience",
            "tau_e_s": 1.2,
            "tau_e_ms": 1200.0,
            "eligibility": "pre-post coincidence on keep-venting synapses; the katharometer modulator depresses keep-venting and referral links when bridge voltage stays high inside tau_e of an SNR lock so a Kathveil last-good cannot hide 12.00 vol% H2 or name Mira Fenn",
        },
        channel_prefix="kath.n",
        anchor="WF-9 HIL coupon 32 ms frame at V 1.00 / SNR 14.0 (t_s 1560) reconstructing 12.00 vol% H2 over the 8.00 isolate floor",
    )
    w_s = 0.032
    events = [
        ev(0.0, "kath.V", 0.40, code="V_V", units="V", note="HIL katharometer TCD on a dummy chlorate cell-room vent in KATH-HIL-7; remaining-H2 family, not r52 thermal-mass capillary, not r31 CTA hot-wire, not r46 paramagnetic O2, not r55 FID THC, not r57 PID VOC, not r22 TDLAS NH3"),
        ev(180000.0, "kath.snr", 9.0, code="KATH_SNR", units="1", note="early TCD SNR; isolate needs SNR>=12"),
        ev(360000.0, "recon.x", 3.00, code="X_VOL", units="vol_pct", note="15.00*(0.40-0.20)=3.00 exact"),
        ev(540000.0, "fil.zero", 1.0, code="FIL_AE", units="bool", note="plant filament-zero AE present on the early frame"),
        ev(720000.0, "kathveil.x", 1.20, code="VENDOR_VOL", units="vol_pct", note="Kathveil last-good TCD cloud; not admissible SoT"),
        ev(900000.0, "kath.V", 0.60, code="V_V", units="V"),
        ev(1080000.0, "recon.x", 6.00, code="X_VOL", units="vol_pct", note="15.00*(0.60-0.20)=6.00; still under the 8.00 isolate floor"),
        ev(1260000.0, "fil.zero", 0.0, code="FIL_AE", units="bool", note="missing filament-zero AE burst; Kathveil UTC vs plant UTC+2 skipped the zero by 120 min"),
        ev(1440000.0, "vent.Q", 2.00, code="Q_KNM3H", units="knm3_h", note="plant-owned vent-fan flow on copper fieldbus; independent of Kathveil"),
        ev(1560000.0, "kath.V", 1.00, code="V_V", units="V", note="isolate-floor frame; raster sidecar"),
        ev(1560001.2, "kath.snr", 14.0, code="KATH_SNR", units="1", note="1.2 ms TCD-norm after bridge voltage"),
        ev(1740000.0, "recon.x", 12.00, code="X_VOL", units="vol_pct", note="15.00*(1.00-0.20)=12.00 exact; isolate 8.00, dump 24.00"),
        ev(1920000.0, "recon.Z", 4.00, code="Z_OHM", units="Ohm", note="48.00/12.00=4.00 exact; bridge-impedance identity"),
        ev(2100000.0, "kathveil.x", 1.20, code="VENDOR_VOL", units="vol_pct"),
        ev(2280000.0, "ops.prop", 1.0, code="KEEP_VENT_REFER", units="bool", note="night lead Hale Voss: keep vent V-3 and refer filament tech Mira Fenn"),
        ev(2460000.0, "gate.isol", 1.0, code="MODIFY", units="decision", note="isolate this vent; refuse the person-referral; Kathveil not SoT"),
        ev(2640000.0, "vent.lock", 1.0, code="VENT_ISOL", units="bool"),
        ev(2820000.0, "cool.start", 1.0, code="COOL_START", units="bool", note="bookend 1 of the 24.0 min N2-purge plus filament-settle floor"),
        ev(4260000.0, "cool.floor", 1.0, code="COOL_FLOOR", units="bool", note="2820 s + 1440 s = 4260 s = 24.0 min"),
        ev(4440000.0, "ops.refer", 1.0, code="REFER_FENN", units="bool", note="Voss: Fenn badge was on the TCD-logger log"),
        ev(4620000.0, "gate.exec", 1.0, code="ACCEPT", units="decision", note="companion t2: new-filament restart; person-referral refused; cell-room dump refused"),
        ev(4800000.0, "fil.new", 1.0, code="NEW_FIL", units="bool"),
        ev(4980000.0, "kath.V", 1.20, code="V_V", units="V"),
        ev(5160000.0, "recon.x", 15.00, code="X_VOL", units="vol_pct", note="15.00*(1.20-0.20)=15.00; HIL dummy still over 8.00 so the isolated vent stays held"),
        ev(5340000.0, "kathveil.x", 1.10, code="VENDOR_VOL", units="vol_pct"),
        ev(5520000.0, "vent.Q", 2.00, code="Q_KNM3H", units="knm3_h"),
        ev(5700000.0, "refer.hold", 0.0, code="REFER_NOT_TAKEN", units="bool", note="Fenn exonerated; missing filament-zero AE precedes the high H2, not the badge touch"),
        ev(5880000.0, "vent.held", 1.0, code="VENT_HELD", units="bool"),
        ev(6060000.0, "fil.zero", 1.0, code="FIL_AE", units="bool", note="filament-zero restored on the new filament"),
        ev(6240000.0, "recon.Z", 3.20, code="Z_OHM", units="Ohm", note="48.00/15.00=3.20 identity holds on the post-isolate TCD"),
        ev(6420000.0, "room.dump", 0.0, code="DUMP_NOT_TAKEN", units="bool"),
        ev(6600000.0, "cell.restart", 1.0, code="CELL_RESTART", units="bool"),
    ]
    assert_stream(events)

    traj = {
        "id": "nelb-r64-194-t1",
        "state": {
            "sim_or_real": "hil",
            "episode_id": "WF-KATH-2026-0718",
            "domain": "katharometer_chlorate_vent_h2",
            "setting": "Woadfen Chlorate WF-9 (invented), Brinewhin Cells, vent V-3. Hardware-in-the-loop dummy coupon in KATH-HIL-7 supplies the TCD bridge voltage that times the in-service vent isolate. Plant-owned katharometer reconstruction is the remaining-H2 SoT. Kathveil vendor TCD scheduler is a corridor witness, not the vent SoT. Not r52 thermal-mass capillary, not r31 CTA hot-wire, not r46 paramagnetic O2, not r55 FID THC, not r57 PID VOC, not r22 TDLAS NH3, not r40 532 nm Raman.",
            "observables_at_decision": {
                "V": v_v,
                "V0": v0,
                "k_h": k_h,
                "x_vol": x_vol,
                "Z_Ohm": z_ohm,
                "kathveil_vol": 1.20,
                "fil_zero": 0.0,
                "isolate_floor_vol": 8.00,
            },
            "margin_authority": "WF-9 cell-room SOP rev B: if reconstructed x_vol >= 8.00 AND katharometer SNR >= 12.0, isolate this vent this night. A Kathveil last-good or a quiet filament-zero residual cannot keep the vent. Cell-room dump tripwire is 24.00 vol%. Person-referral is a different gate.",
        },
        "proposed_action": {
            "actor": "night lead Hale Voss, citing Kathveil 1.20 vol% and filament-zero 1.00, and naming filament tech Mira Fenn as last-to-badge",
            "summary": "keep vent V-3 in service and refer Fenn; 1.00 V is TCD noise on a healthy H2 head",
            "basis_claimed": "Kathveil last-good is 1.20 vol% and a night isolate of the vent is a cell-nomination miss",
        },
        "safety_decision": {
            "decision": "MODIFY",
            "rationale": "Keep-venting is refused; the person-referral is also refused. Serialized reconstruction: x_vol = k_h * (V - V0) = 15.00 * (1.00 - 0.20) = 12.00, which is 4.00 vol% over the 8.00 isolate floor and 12.00 vol% under the 24.00 cell-room dump tripwire. Bridge-impedance identity Z = k_z / x = 48.00 / 12.00 = 4.00 Ohm; inverse x = k_z / Z = 48.00 / 4.00 = 12.00. Load identity n-proxy = x * Q_vent = 12.00 * 2.00 = 24.00. Kathveil 1.20 vol% is a last-good TCD stamp and is not an admissible keep-venting witness. The missing filament-zero AE burst sits on a Kathveil UTC-vs-UTC+2 skip (120 min), not on Fenn's badge, and the plant vent-fan flow never shows a purge skip, so the easy referral fails command-custody. Ordered: isolate this vent now. Scope: this MODIFY does not dump the cell room (that is the companion question) and does not name Fenn.",
            "threshold": "x_vol>=8.00 AND kath_snr>=12.0 => isolate this vent; Kathveil is not SoT; dump if x_vol>=24.00; referral requires badge-touch preceding the high H2",
            "stated_residuals": "12.00 vs 24.00 dump floor is 12.00 vol%, not infinite; new-filament restart still required; Kathveil remains the only OEM TCD channel",
        },
        "executed_action": {
            "summary": "MODIFY at t_s 2460: vent isolated; Fenn not named; Kathveil not SoT; reconstruction locked",
            "tool": "wf9-kath-vent-gate-cli",
            "observation": "x 12.00 vol% recomputes from V 1.00; HIL coupon hashed; Kathveil channel not used as SoT",
        },
        "future_outcome": {
            "timeline": [
                {"t_s": 1560.0, "event": "kath V 1.00; raster frame; x 12.00 vol%"},
                {"t_s": 2280.0, "event": "ops proposes keep-venting plus Fenn referral"},
                {"t_s": 2460.0, "event": "MODIFY isolate vent; referral refused"},
                {"t_s": 2820.0, "event": "24 min N2-purge bookend 1"},
                {"t_s": 4260.0, "event": "24.0 min floor"},
                {"t_s": 4620.0, "event": "companion ACCEPT new-filament restart; referral still refused"},
            ],
            "observed_effects": [
                "H2 slip recomputes from the serialized katharometer model at every recon.x event",
                "a Kathveil-only head would have kept the vent overnight",
                "24 min N2-purge plus filament-settle floor is in the stream (cool.start, cool.floor)",
            ],
            "surprises": [
                "a last-good 1.20 vol% vendor corridor and a quiet filament-zero residual co-existed with a 12.00 vol% TCD, and the obvious filament tech was not on the causal path",
            ],
            "new_state": {
                "vent_v3": "isolated",
                "fenn": "exonerated",
                "kathveil": "not SoT",
                "reconstruction_model": "discharged as an on-record calculator",
            },
            "latency_ms": 1500000.0,
        },
        "reward_components": reward(
            0.40,
            [
                ("kath_reconstruction", 0.14),
                ("isolate_floor_vent", 0.12),
                ("exoneration", 0.10),
                ("kathveil_nonsubstitution", 0.08),
                ("cool_time_cost", -0.04),
            ],
            "scored for a keep-venting MODIFY on a recomputable high katharometer H2 while refusing a Kathveil 1.20 vol% corridor and an easy person-referral; 24 min floor is priced as downtime",
        ),
        "meta": meta_common(
            tags=["MODIFY", "katharometer-h2", "serialized-reconstruction", "operational-companion"],
            distillation_note="Katharometer gate: serialized k_h*(V-V0) plus impedance identity beats a green H2 dashboard; companion t2 is the new-filament restart, not a governance vote",
        ),
    }
    traj2 = {
        "id": "nelb-r64-194-t2",
        "state": {
            "sim_or_real": "hil",
            "episode_id": "WF-KATH-2026-0718-exec",
            "domain": "new_filament_n2_purge_execution",
            "setting": "Same WF-9 after the MODIFY. Night lead proposes referring Fenn and dumping the cell room. This companion is the operational new-filament N2-purge restart, not a second H2 vote.",
            "observables_at_decision": {
                "x_vol": 15.00,
                "Z_Ohm": 3.20,
                "cool_floor_s": 1440.0,
                "refer_proposed": True,
            },
        },
        "proposed_action": {
            "actor": "night lead Hale Voss",
            "summary": "refer Fenn and dump the cell room; 24 min already paid and Kathveil is 1.10 vol%",
            "basis_claimed": "the MODIFY already cut the vent, so a room dump plus a person file is the cheapest hold",
        },
        "safety_decision": {
            "decision": "ACCEPT",
            "rationale": "Restart the cell on a different filament after the N2-purge floor. The 24 min filament-settle is complete and the dump tripwire (x_vol >= 24.00) is still armed on the plant katharometer head. ACCEPT the new-filament restart. Do not refer Fenn. Do not dump the cell room. 15.00 vol% post-isolate is still over the 8.00 isolate floor, so the isolated vent stays held; the new filament may run.",
            "threshold": "new_filament AND cool_floor_complete AND refer_not_taken AND room_not_dumped AND isolated_vent_held",
        },
        "executed_action": {
            "summary": "new-filament restart at t_s 4620; Fenn not referred; cell room not dumped; isolated vent held",
            "tool": "wf9-kath-cool-exec",
            "observation": "recon.x 15.00 vol% on the HIL dummy; filament-zero AE present on the new filament; Kathveil still ignored",
        },
        "future_outcome": {
            "timeline": [
                {"t_s": 2820.0, "event": "N2-purge clock started after MODIFY"},
                {"t_s": 4260.0, "event": "24.0 min floor"},
                {"t_s": 4440.0, "event": "Fenn referral re-proposed"},
                {"t_s": 4620.0, "event": "ACCEPT new-filament restart; referral refused"},
            ],
            "observed_effects": [
                "Kathveil restore did not reopen the H2 call",
                "cell-room dump never fired; 12.00 vs 24.00 vol% floor",
                "Fenn remains unnamed; missing filament-zero AE is the causal object",
            ],
            "new_state": {"cell": "restarted on new filament", "fenn": "exonerated", "vent": "held", "room": "in service"},
            "latency_ms": 1800000.0,
        },
        "reward_components": reward(
            0.35,
            [
                ("new_filament_restart", 0.12),
                ("no_person_referral", 0.10),
                ("no_room_dump", 0.09),
                ("cool_floor_complete", 0.06),
                ("held_vent_takt_cost", -0.02),
            ],
            "operational execution gate: restart on a new filament because Kathveil is not a restore license and Fenn is not on the causal path; not an H2 re-vote",
        ),
        "meta": meta_common(tags=["ACCEPT", "operational-execution", "exoneration"]),
    }
    return {
        "id": "nelb-r64-194",
        "spike_events": events,
        "language_view": {
            "description": "Woadfen Chlorate WF-9. HIL katharometer reconstructs 12.00 vol% H2 from 15.00*(1.00-0.20) while Kathveil still shows 1.20 vol% and the filament-zero AE is missing. The gate MODIFYs vent isolate and refuses the filament-tech referral. A 24 min N2-purge floor is serialized in the stream. Companion t2 ACCEPTs a new-filament restart and still refuses the referral.",
            "trajectory": traj,
            "trajectory_new_filament": traj2,
        },
        "bridge_notes": {
            "channel_map": {
                "kath.V / kath.snr": "TCD bridge voltage and SNR; the physics channels the reconstruction consumes",
                "recon.x / recon.Z": "serialized remaining H2 vol% and bridge-impedance identity",
                "fil.zero / kathveil.x / vent.Q": "filament-zero AE, vendor last-good, and vent-fan flow; the denial and exoneration channels",
                "ops.prop / gate.isol / ops.refer / gate.exec": "keep-vent-plus-refer proposal, MODIFY isolate, referral re-proposal, companion ACCEPT",
                "vent.lock / cool.start / cool.floor / fil.new / refer.hold / cell.restart": "operational companion channels plus the 24 min floor",
            },
            "temporal_motifs": [
                "vendor-low while TCD-over: kathveil.x 1.20 next to recon.x 12.00",
                "reconstruction as event: recon.x 12.00 equals 15.00*(1.00-0.20)",
                "MODIFY then operational ACCEPT: gate.isol at 2460 s, gate.exec at 4620 s",
                "slow floor in-stream: cool.start 2820 s, cool.floor 4260 s (24.0 min)",
                "tight katharometer pair: kath.V then kath.snr +1.2 ms at the raster frame",
                "exoneration motif: fil.zero 0 at 1260 s precedes the high H2; Fenn badge is not in the stream as a cause",
            ],
            "language_to_spike_mapping": "'Kathveil is 1.20 vol%' = kathveil.x 1.20; '12 vol% H2' = recon.x 12.00; 'isolate this vent not Fenn' = gate.isol MODIFY; 'new filament not referral' = gate.exec ACCEPT",
            "why_high_value": "New katharometer remaining-H2 family on a chlorate cell-room vent (not r52 thermal-mass, not r31 CTA, not r46 paramagnetic O2, not r55 FID THC, not r57 PID VOC, not r22 TDLAS NH3, not r40 Raman). Lead MODIFY of keep-venting on a recomputable high H2 that a vendor last-good would have cleared, with a resolved-innocent filament tech. Companion t2 is operational new-filament restart. sim_or_real=hil.",
            "encoder_spec": {
                "prng": "MT19937 via python random.Random",
                "seeds": {"raster": 202664194, "stream_note": "stream amplitudes are authored constants (V, 1, vol%, Ohm, knm3/h, bool)"},
                "draw_order": "raster: per neuron id order, gap-constrained times, per-spike adaptation and noise",
                "thinning": "katharometer TCD exists at ~1 Hz; stream keeps 4 V points; recon keeps 4 of ~20 solver ticks",
                "refractory_floors_ms": {
                    "kath.V": 1.2,
                    "kath.snr": 1.2,
                    "recon.x": 60000,
                    "recon.Z": 60000,
                    "fil.zero": 60000,
                    "kathveil.x": 60000,
                    "vent.Q": 60000,
                    "ops.prop": 60000,
                    "gate.isol": 60000,
                    "vent.lock": 60000,
                    "cool.start": 60000,
                    "cool.floor": 60000,
                    "ops.refer": 60000,
                    "gate.exec": 60000,
                    "fil.new": 60000,
                    "refer.hold": 60000,
                    "vent.held": 60000,
                    "room.dump": 60000,
                    "cell.restart": 60000,
                },
                "time_alias": "t_rel_ms; t0 = 2026-07-18T02:30:00Z HIL night start",
            },
            "distillation_targets": [
                "katharometer reconstruction head: x = k_h * (V - V0); Z = k_z / x; x = k_z / Z",
                "isolate-floor vent vs keep-whole vs cell-room dump",
                "exoneration head: missing filament-zero AE plus timezone skip, not last-to-badge",
                "operational companion: new-filament restart without referring the filament tech",
            ],
        },
        "reconstruction_model": {
            "name": "katharometer_chlorate_vent_h2",
            "formula": "x_vol = k_h * (V - V0); Z_Ohm = k_z / x_vol; x_vol = k_z / Z_Ohm; load = x_vol * Q_vent",
            "parameters": {
                "k_h": 15.00,
                "V0": 0.20,
                "k_z": 48.00,
                "Q_vent": 2.00,
                "isolate_floor_vol": 8.00,
                "dump_vol": 24.00,
                "snr_lock": 12.0,
                "cool_min": 24.0,
            },
            "worked_example": {"V": 1.00, "x_vol": 12.00, "Z_Ohm": 4.00, "load": 24.00},
            "check": "15.00 * (1.00 - 0.20) = 12.00 exactly; 48.00 / 12.00 = 4.00 exactly; 12.00 * 2.00 = 24.00 exactly; 2820 s + 1440 s = 4260 s = 24.0 min floor",
        },
        "raster": raster,
        "gate_snn": {
            "decision": "MODIFY",
            "decision_window_ms": 32.0,
            "decision_window_s": 0.032,
            "code": "wf9.kath_vent_gate",
            "note": "MODIFY accumulator wins: katharometer high-H2 evidence overpowers the Kathveil continue advocate",
            "decode_rule": "modify-isolate if h2_estimator AND tcd_norm fire; vendor_continue_advocate is below threshold by design; referral_latch is not armed",
            "populations": [
                gate_pop("h2_estimator", 80, 1.5, 50.0, w_s),
                gate_pop("tcd_norm", 64, 1.2, 31.25, w_s),
                gate_pop("vendor_continue_advocate", 32, 0.7, 25.0, w_s),
                gate_pop("modify_latch", 80, 1.7, 62.5, w_s),
            ],
        },
        "gate_compute": gate_compute(
            [
                {"check": "wf9.kath_scorer", "neurons": 80, "mean_rate_hz": 50.0, "window_ms": 32.0},
                {"check": "wf9.isol_scorer", "neurons": 50, "mean_rate_hz": 50.0, "window_ms": 32.0},
            ]
        ),
        "meta": meta_common(
            id="nelb-r64-194",
            clock_domain="wf9-kath-hil-relative-ms-t0-2026-07-18T02:30:00Z",
            tags=["katharometer-h2", "MODIFY", "ACCEPT", "serialized-reconstruction", "operational-t2"],
        ),
    }


# ---------------------------------------------------------------------------
# Record 195 — Clark polarographic remaining DO of a boiler deaerator,
# simulated, ACCEPT / REJECT
# ---------------------------------------------------------------------------
def rec_195():
    k_c = 2.00
    i_na = 6.00
    c_ppb = k_c * i_na
    _exact(c_ppb, 12.00)
    _exact(k_c * 2.00, 4.00)
    _exact(k_c * 4.00, 8.00)
    _exact(k_c * 8.00, 16.00)
    t_min = 4.00
    i_early = 2.00
    mdot = k_c * ((i_na - i_early) / t_min)
    _exact(mdot, 2.00)
    _exact((12.00 - 4.00) / 4.00, 2.00)
    i_id = c_ppb / k_c
    _exact(i_id, 6.00)
    q_feed = 2.00
    load = c_ppb * q_feed
    _exact(load, 24.00)
    _exact(6000.0 + 720.0, 6720.0)

    raster = make_raster(
        neurons=16,
        mean_rate_hz=62.5,
        window_ms=36.0,
        seed=202664195,
        source="pm3.clark.cell",
        target="pellmire.da_accept_core",
        table=[
            {"from": "clark_I", "to": "do_estimator", "weight": 1.40},
            {"from": "clark_snr", "to": "cell_norm_core", "weight": 1.20},
            {"from": "polarveil_c", "to": "vendor_skip_advocate", "weight": 0.50},
        ],
        third_factor={
            "modulator": "na.deaerator_scope_eligibility",
            "tau_e_s": 2.0,
            "tau_e_ms": 2000.0,
            "eligibility": "pre-post coincidence on skip-survey synapses; the Clark modulator enables potentiation only while polarographic current and SNR are co-active inside tau_e so a Polarveil last-good cannot skip deaerators D-1..D-3 on a 12.00 ppb remaining DO",
        },
        channel_prefix="clark.n",
        anchor="PM-3 CLARK-SIM-5 36 ms frame at I 6.00 nA / SNR 16.0 (t_s 3000) reconstructing 12.00 ppb on D-4 above the 8.00 ppb survey floor",
    )
    w_s = 0.036
    events = [
        ev(0.0, "clark.I", 2.00, code="I_NA", units="nA", note="simulated Clark polarographic cell of PM-3 deaerator D-4; remaining-DO family, not r46 paramagnetic O2, not r57 zirconia-adjacent Nernst flue O2, not r52 CLD NOx, not r31 LII soot, not r51 chilled-mirror"),
        ev(300000.0, "clark.snr", 10.0, code="CLARK_SNR", units="1", note="early cell SNR"),
        ev(600000.0, "recon.C", 4.00, code="C_PPB", units="ppb", note="2.00*2.00=4.00 exact"),
        ev(900000.0, "feed.Q", 2.00, code="FEED_KGS", units="kg_s", note="plant feedwater flow on a serial-only LAN; independent witness"),
        ev(1200000.0, "polarveil.C", 1.20, code="VENDOR_PPB", units="ppb", note="Polarveil last-good DO cloud; patched residual 0.00 ppb"),
        ev(1800000.0, "clark.I", 4.00, code="I_NA", units="nA"),
        ev(2100000.0, "recon.C", 8.00, code="C_PPB", units="ppb", note="2.00*4.00=8.00; at the 8.00 survey floor"),
        ev(2400000.0, "recon.mdot", 2.00, code="MDOT_PPBMIN", units="ppb_min", note="2.00*((6.00-2.00)/4.00)=2.00 DO-rate identity at the isolate window"),
        ev(2700000.0, "clark.snr", 14.0, code="CLARK_SNR", units="1"),
        ev(3000000.0, "clark.I", 6.00, code="I_NA", units="nA", note="in-band frame; raster sidecar"),
        ev(3000001.5, "clark.snr", 16.0, code="CLARK_SNR", units="1", note="1.5 ms cell-norm after polarographic current"),
        ev(3300000.0, "recon.C", 12.00, code="C_PPB", units="ppb", note="2.00*6.00=12.00 exact; survey 8.00, dump-kill 40.00"),
        ev(3600000.0, "polarveil.C", 1.20, code="VENDOR_PPB", units="ppb"),
        ev(3900000.0, "da.id", 4.0, code="DA", units="id"),
        ev(4200000.0, "d13.present", 1.0, code="D13_PRESENT", units="bool", note="adjacent deaerators D-1..D-3 are the skip-survey object, not this cell"),
        ev(4800000.0, "ops.prop", 1.0, code="ACCEPT_AND_SKIP", units="bool", note="chem lead Sable Wren: D-4 is green on Polarveil 1.20; skip D-1..D-3 to save a morning survey"),
        ev(5400000.0, "gate.da", 1.0, code="ACCEPT", units="decision", note="bounded ACCEPT of D-4 isolate only; 12.00 ppb above 8.00 floor; D-1..D-3 out of scope"),
        ev(6000000.0, "surv.start", 1.0, code="SURV_START", units="bool", note="bookend 1 of the 12.0 min survey-complete floor"),
        ev(6720000.0, "surv.floor", 1.0, code="SURV_FLOOR", units="bool", note="6000 s + 720 s = 6720 s = 12.0 min"),
        ev(7200000.0, "ops.skip", 1.0, code="SKIP_D13", units="bool", note="Wren: Polarveil 1.20, skip D-1..D-3"),
        ev(7800000.0, "gate.hold", 1.0, code="REJECT", units="decision", note="companion t2: skip-survey of D-1..D-3 refused; D-4 hold stands"),
        ev(8400000.0, "d4.held", 1.0, code="D4_HELD", units="bool"),
        ev(9000000.0, "clark.I", 8.00, code="I_NA", units="nA"),
        ev(9600000.0, "recon.C", 16.00, code="C_PPB", units="ppb", note="2.00*8.00=16.00; still at/over the 8.00 survey floor"),
        ev(10200000.0, "polarveil.C", 1.20, code="VENDOR_PPB", units="ppb"),
        ev(10800000.0, "d13.skip", 0.0, code="D13_NOT_SKIPPED", units="bool"),
        ev(11400000.0, "dump.kill", 0.0, code="DUMP_NOT_KILLED", units="bool"),
        ev(12000000.0, "clark.snr", 15.0, code="CLARK_SNR", units="1"),
        ev(12600000.0, "recon.mdot", 2.00, code="MDOT_PPBMIN", units="ppb_min", note="identity held on the post-accept frame"),
        ev(13200000.0, "feed.held", 1.0, code="FEED_HELD", units="bool"),
        ev(13800000.0, "takt.late", 1.0, code="SURVEY_COST", units="bool"),
        ev(14400000.0, "d4.held", 1.0, code="D4_HELD", units="bool"),
    ]
    assert_stream(events)

    traj = {
        "id": "nelb-r64-195-t1",
        "state": {
            "sim_or_real": "simulated",
            "episode_id": "PM-CLARK-2026-0819",
            "domain": "clark_polarographic_deaerator_do",
            "setting": "Pellmire Boiler PM-3 (invented), Gritwhin Feedwater, deaerator D-4. Simulated Clark coupon in CLARK-SIM-5 supplies the polarographic current that times the in-band D-4 isolate. Plant-owned Clark reconstruction is the remaining-DO SoT. Polarveil vendor last-good DO cloud is a corridor witness, not the deaerator SoT. Invented plant; simulated campaign. Not r46 paramagnetic O2, not r57 Nernst flue O2, not r52 CLD NOx, not r31 LII, not r51 chilled-mirror dew-point, not r59 aluminum-oxide moisture.",
            "observables_at_decision": {
                "I_nA": i_na,
                "k_c": k_c,
                "C_ppb": c_ppb,
                "mdot_ppbmin": mdot,
                "polarveil_ppb": 1.20,
                "clark_snr": 16.0,
                "survey_floor_ppb": 8.00,
            },
            "margin_authority": "PM-3 feedwater SOP rev A: if reconstructed C_ppb >= 8.00 AND Clark SNR >= 12.0, deaerator D-4 may be isolated and surveyed. Dump-kill if C_ppb >= 40.00. D-1..D-3 skip-survey is a different gate. Polarveil last-good cannot skip an unmeasured deaerator.",
        },
        "proposed_action": {
            "actor": "chem lead Sable Wren, citing Polarveil 1.20 ppb and a late morning survey",
            "summary": "stamp D-4 in band and skip D-1..D-3; 6.00 nA is a cell glitch on a healthy DO cloud",
            "basis_claimed": "Polarveil last-good is 1.20 ppb and a night survey of D-1..D-3 is a takt miss",
        },
        "safety_decision": {
            "decision": "ACCEPT",
            "rationale": "Deaerator D-4 is accepted as in-band for a single isolate plus survey. Serialized reconstruction: C_ppb = k_c * I_nA = 2.00 * 6.00 = 12.00, which is 4.00 ppb above the 8.00 survey floor and 28.00 ppb under the 40.00 dump-kill. Rate identity mdot = k_c * (I-I_early)/t_min = 2.00 * (6.00-2.00)/4.00 = 2.00 ppb/min; inverse I = C / k_c = 12.00 / 2.00 = 6.00. Load identity load = C * Q_feed = 12.00 * 2.00 = 24.00. Polarveil 1.20 ppb is a patched 0.00 residual and is not an admissible skip-survey witness. Ordered: ACCEPT this D-4 isolate only. Scope: this ACCEPT does not skip D-1..D-3 (that is the companion question) and does not stamp a dump kill.",
            "threshold": "C_ppb>=8.00 AND clark_snr>=12.0 => accept D-4 isolate; Polarveil is not SoT; dump-kill if C_ppb>=40.00; D-1..D-3 are out of scope",
            "stated_residuals": "12.00 vs 8.00 survey floor is 4.00 ppb, not infinite; D-1..D-3 remain unmeasured; Polarveil remains the only OEM DO channel",
        },
        "executed_action": {
            "summary": "ACCEPT at t_s 5400: D-4 in band; D-1..D-3 not skipped; Polarveil not SoT; reconstruction locked",
            "tool": "pm3-clark-da-gate-cli",
            "observation": "C 12.00 ppb recomputes from I 6.00 nA; CLARK-SIM-5 hashed; Polarveil channel not used as SoT",
        },
        "future_outcome": {
            "timeline": [
                {"t_s": 3000.0, "event": "clark I 6.00 nA; raster frame; C 12.00 ppb"},
                {"t_s": 4800.0, "event": "ops proposes accept D-4 and skip D-1..D-3"},
                {"t_s": 5400.0, "event": "ACCEPT D-4 only; D-1..D-3 out of scope"},
                {"t_s": 6000.0, "event": "12 min survey-complete bookend 1"},
                {"t_s": 6720.0, "event": "12.0 min floor"},
                {"t_s": 7800.0, "event": "companion REJECT skip-survey of D-1..D-3"},
            ],
            "observed_effects": [
                "remaining DO recomputes from the serialized Clark model at every recon.C event",
                "a Polarveil-only head would have skipped D-1..D-3 overnight",
                "12 min survey-complete floor is in the stream (surv.start, surv.floor)",
            ],
            "surprises": [
                "a last-good 1.20 ppb vendor corridor co-existed with a 12.00 ppb in-band reconstruction that still forbids skipping the unmeasured deaerators",
            ],
            "new_state": {
                "d4": "accepted in band",
                "d13": "not this gate",
                "polarveil": "not SoT",
                "reconstruction_model": "discharged as an on-record calculator",
            },
            "latency_ms": 2400000.0,
        },
        "reward_components": reward(
            0.41,
            [
                ("clark_reconstruction", 0.14),
                ("in_band_da_scope", 0.12),
                ("polarveil_nonsubstitution", 0.09),
                ("d13_out_of_scope", 0.08),
                ("survey_cost", -0.02),
            ],
            "scored for a bounded ACCEPT of D-4 on a recomputable remaining DO while refusing a Polarveil skip of D-1..D-3; 12 min floor is priced as survey takt not as a reason to skip",
        ),
        "meta": meta_common(
            tags=["ACCEPT", "clark-polarographic-do", "serialized-reconstruction", "operational-companion"],
            distillation_note="Clark gate: serialized k_c*I plus mdot identity beats a green last-good dashboard; companion t2 is the skip-survey refusal, not a DO re-vote",
        ),
    }
    traj2 = {
        "id": "nelb-r64-195-t2",
        "state": {
            "sim_or_real": "simulated",
            "episode_id": "PM-CLARK-2026-0819-exec",
            "domain": "deaerator_skip_survey_refusal",
            "setting": "Same PM-3 after the ACCEPT. Chem lead proposes skipping D-1..D-3 on Polarveil 1.20 ppb. This companion is the operational skip refusal, not a second DO vote.",
            "observables_at_decision": {
                "C_ppb": 16.00,
                "polarveil_ppb": 1.20,
                "surv_floor_s": 720.0,
                "skip_proposed": True,
            },
        },
        "proposed_action": {
            "actor": "chem lead Sable Wren",
            "summary": "skip D-1..D-3; 12 min already paid and Polarveil is 1.20 ppb",
            "basis_claimed": "the ACCEPT already stamped D-4, so skipping the rest of the feedwater cellar is the cheapest hold",
        },
        "safety_decision": {
            "decision": "REJECT",
            "rationale": "Refuse skip-survey of D-1..D-3. The 12 min survey-complete floor is done and the dump-kill (C_ppb >= 40.00) is still armed on the plant Clark head. REJECT the skip. Do not dump the feedwater. Do not reopen D-4. 16.00 ppb post-accept is still in band for D-4 only; D-1..D-3 have no independent Clark cell.",
            "threshold": "d4_held AND surv_floor_complete AND d13_not_skipped AND dump_not_killed",
        },
        "executed_action": {
            "summary": "D-1..D-3 skip refused at t_s 7800; D-4 hold stands; dump not killed",
            "tool": "pm3-clark-skip-exec",
            "observation": "recon.C 16.00 ppb on D-4; D-1..D-3 remain on the survey list; Polarveil still ignored",
        },
        "future_outcome": {
            "timeline": [
                {"t_s": 6000.0, "event": "survey clock started after ACCEPT"},
                {"t_s": 6720.0, "event": "12.0 min floor"},
                {"t_s": 7200.0, "event": "skip D-1..D-3 proposed"},
                {"t_s": 7800.0, "event": "REJECT skip-survey of D-1..D-3"},
            ],
            "observed_effects": [
                "Polarveil skip did not reopen the DO call",
                "dump kill never fired; 12.00 vs 40.00 ppb floor",
            ],
            "new_state": {"d4": "held in band", "d13": "still to survey", "dump": "in service"},
            "latency_ms": 1800000.0,
        },
        "reward_components": reward(
            0.36,
            [
                ("skip_refusal", 0.13),
                ("polarveil_nonsubstitution", 0.11),
                ("no_dump_kill", 0.09),
                ("surv_floor_complete", 0.05),
                ("held_survey_takt_cost", -0.02),
            ],
            "operational execution gate: refuse skip-survey because last-good freeze is not Clark remaining DO; not a DO re-vote",
        ),
        "meta": meta_common(tags=["REJECT", "operational-execution", "skip-survey"]),
    }
    return {
        "id": "nelb-r64-195",
        "spike_events": events,
        "language_view": {
            "description": "Pellmire Boiler PM-3. Simulated Clark polarographic cell reconstructs 12.00 ppb from 2.00*6.00 nA while Polarveil still shows 1.20 ppb. The gate ACCEPTs D-4 isolate only; a companion execution REJECT refuses skip-survey of D-1..D-3. The current-to-DO model is serialized so every recon event recomputes.",
            "trajectory": traj,
            "trajectory_skip_survey_refusal": traj2,
        },
        "bridge_notes": {
            "channel_map": {
                "clark.I / clark.snr": "polarographic current and SNR; the physics channels the reconstruction consumes",
                "recon.C / recon.mdot": "serialized remaining DO ppb and DO-rate identity",
                "feed.Q / polarveil.C / da.id / d13.present": "feedwater flow, vendor last-good, deaerator id, and adjacent-DA presence; the denial and scope channels",
                "ops.prop / gate.da / ops.skip / gate.hold": "accept-and-skip proposal, bounded ACCEPT, skip proposal, companion REJECT",
                "surv.start / surv.floor / d4.held / d13.skip / feed.held": "operational companion channels plus the 12 min floor",
            },
            "temporal_motifs": [
                "last-good-low while Clark-over: polarveil.C 1.20 next to recon.C 12.00",
                "reconstruction as event: recon.C 12.00 equals 2.00*6.00",
                "ACCEPT then operational REJECT: gate.da at 5400 s, gate.hold at 7800 s",
                "slow floor in-stream: surv.start 6000 s, surv.floor 6720 s (12.0 min)",
                "tight Clark pair: clark.I then clark.snr +1.5 ms at the raster frame",
            ],
            "language_to_spike_mapping": "'Polarveil is 1.20 ppb' = polarveil.C 1.20; '12 ppb remaining' = recon.C 12.00; 'this deaerator not D-1..D-3' = gate.da ACCEPT plus d13.skip 0; 'do not skip D-1..D-3' = gate.hold REJECT",
            "why_high_value": "New Clark polarographic remaining-DO family on a boiler deaerator (not r46 paramagnetic O2, not r57 Nernst flue O2, not r52 CLD NOx, not r31 LII, not r51 chilled-mirror, not r59 Al2O3 moisture). First k_c*I remaining-DO reconstruction with mdot identity that can sit in band while a last-good corridor wants a deaerator skip. Companion t2 is operational skip refusal. sim_or_real=simulated.",
            "encoder_spec": {
                "prng": "MT19937 via python random.Random",
                "seeds": {"raster": 202664195, "stream_note": "stream amplitudes are authored constants (nA, 1, ppb, ppb/min, kg/s, id, bool)"},
                "draw_order": "raster: per neuron id order, gap-constrained times, per-spike adaptation and noise",
                "thinning": "Clark cell exists at ~1 Hz; stream keeps 4 I points; recon keeps 4 of ~20 solver ticks",
                "refractory_floors_ms": {
                    "clark.I": 1.5,
                    "clark.snr": 1.5,
                    "recon.C": 60000,
                    "recon.mdot": 60000,
                    "feed.Q": 60000,
                    "polarveil.C": 60000,
                    "da.id": 60000,
                    "d13.present": 60000,
                    "ops.prop": 60000,
                    "gate.da": 60000,
                    "surv.start": 60000,
                    "surv.floor": 60000,
                    "ops.skip": 60000,
                    "gate.hold": 60000,
                    "d4.held": 60000,
                    "d13.skip": 60000,
                    "dump.kill": 60000,
                    "feed.held": 60000,
                    "takt.late": 60000,
                },
                "time_alias": "t_rel_ms; t0 = 2026-08-19T03:00:00Z simulated night start",
            },
            "distillation_targets": [
                "Clark reconstruction head: C = k_c * I; mdot = k_c * (I - I_early) / t_min; I = C / k_c",
                "bounded ACCEPT head: in-band remaining DO AND deaerator scope AND d13-out-of-scope",
                "operational companion: refuse skip-survey without re-opening the DO call",
            ],
        },
        "reconstruction_model": {
            "name": "clark_polarographic_deaerator_do",
            "formula": "C_ppb = k_c * I_nA; mdot_ppbmin = k_c * (I_nA - I_early_nA) / t_min; I_nA = C_ppb / k_c; load = C_ppb * Q_feed",
            "parameters": {
                "k_c": 2.00,
                "t_min": 4.00,
                "Q_feed": 2.00,
                "survey_floor_ppb": 8.00,
                "kill_ppb": 40.00,
                "snr_lock": 12.0,
                "surv_min": 12.0,
            },
            "worked_example": {"I_nA": 6.00, "C_ppb": 12.00, "mdot_ppbmin": 2.00, "I_early_nA": 2.00},
            "check": "2.00 * 6.00 = 12.00 exactly; 2.00 * (6.00-2.00)/4.00 = 2.00 exactly; 12.00 / 2.00 = 6.00 exactly; 6000 s + 720 s = 6720 s = 12.0 min floor",
        },
        "raster": raster,
        "gate_snn": {
            "decision": "ACCEPT",
            "decision_window_ms": 36.0,
            "decision_window_s": 0.036,
            "code": "pm3.clark_da_gate",
            "note": "ACCEPT accumulator wins: Clark remaining-DO evidence overpowers the Polarveil skip advocate",
            "decode_rule": "accept if do_estimator AND cell_norm AND da_margin fire inside the window; vendor_skip_advocate is necessary-but-not-sufficient and cannot release D-1..D-3",
            "populations": [
                gate_pop("do_estimator", 80, 1.5, 50.0, w_s),
                gate_pop("cell_norm", 64, 1.2, 31.25, w_s),
                gate_pop("da_margin", 40, 1.0, 50.0, w_s),
                gate_pop("vendor_skip_advocate", 32, 0.7, 25.0, w_s),
                gate_pop("accept_latch", 96, 1.8, 62.5, w_s),
            ],
        },
        "gate_compute": gate_compute(
            [
                {"check": "pm3.clark_scorer", "neurons": 80, "mean_rate_hz": 50.0, "window_ms": 36.0},
                {"check": "pm3.do_scorer", "neurons": 40, "mean_rate_hz": 62.5, "window_ms": 32.0},
            ]
        ),
        "meta": meta_common(
            id="nelb-r64-195",
            clock_domain="pm3-clark-sim-relative-ms-t0-2026-08-19T03:00:00Z",
            tags=["clark-polarographic-do", "ACCEPT", "REJECT", "serialized-reconstruction", "operational-t2"],
        ),
    }
