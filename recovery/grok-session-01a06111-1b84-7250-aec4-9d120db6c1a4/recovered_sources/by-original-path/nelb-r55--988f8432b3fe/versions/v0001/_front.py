def occupancy_preflight():
    banned = (
        "brindlecrag",
        "copsewharf",
        "kelpwharf",
        "fidveil",
        "rotorveil",
        "floatveil",
        "edda fenwick",
        "lise thorn",
        "gareth pike",
        "bram vellum",
        "flame-ionization thc",
        "turbine k-factor",
        "magnetostrictive waveguide level",
        "bc-8 knockout",
        "cw-7 header",
        "kw-8 sphere",
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
        if "nelb-r55" in str(n):
            continue
        text = n.read_text(encoding="utf-8", errors="replace").casefold()
        for b in banned:
            if b in text:
                hits.append(f"{n}:{b}")
    if hits:
        raise RuntimeError(f"family/plant collision {hits}")


# ---------------------------------------------------------------------------
# Record 166 — flame-ionization THC of a flare knockout, designed,
# REJECT / MODIFY
# ---------------------------------------------------------------------------
def rec_166():
    k_f = 0.250
    i_na = 48.00
    i_bg = 8.00
    t_k = 320.0
    t0_k = 320.0
    p_bar = 1.000
    p0_bar = 1.000
    t_ratio = t_k / t0_k
    p_ratio = p0_bar / p_bar
    di = i_na - i_bg
    c_ppm = k_f * di * t_ratio * p_ratio
    _exact(t_ratio, 1.000)
    _exact(p_ratio, 1.000)
    _exact(di, 40.00)
    _exact(c_ppm, 10.00)
    _exact(k_f * (24.00 - i_bg), 4.00)
    _exact(k_f * (32.00 - i_bg), 6.00)
    _exact(k_f * (40.00 - i_bg), 8.00)
    q_air = 2.00
    load = c_ppm * q_air
    _exact(load, 20.00)
    _exact(10.00 * 2.00, 20.00)
    _exact(6000.0 + 1080.0, 7080.0)

    raster = make_raster(
        neurons=20,
        mean_rate_hz=50.0,
        window_ms=40.0,
        seed=202655166,
        source="bc8.fid.pmt",
        target="brindlecrag.ko_stop_core",
        table=[
            {"from": "fid_I", "to": "thc_estimator", "weight": 1.40},
            {"from": "fid_snr", "to": "fid_lock_core", "weight": 1.15},
            {"from": "fidveil_c", "to": "vendor_continue_advocate", "weight": 0.45},
        ],
        third_factor={
            "modulator": "da.cross_authority_conflict",
            "tau_e_s": 1.6,
            "tau_e_ms": 1600.0,
            "eligibility": "pre-post coincidence on continue-firing synapses; the plant FID modulator depresses continue-firing links when collector current stays high inside tau_e of an SNR lock so a Fidveil last-good cannot hide a 10.00 ppm THC slip",
        },
        channel_prefix="fid.n",
        anchor="BC-8 flame-ionization 40 ms frame at I 48.00 nA / SNR 12.0 (t_s 3000) reconstructing 10.00 ppm THC above the 8.00 slip floor",
    )
    w_s = 0.040
    events = [
        ev(0.0, "fid.I", 24.00, code="I_NA", units="nA", note="plant-owned flame-ionization detector on BC-8 knockout KO-2; FID THC family, not CEMS FTIR k-script, not CLD NOx, not TDLAS NH3, not CRDS HF, not QEPAS, not PID VOC, not paramagnetic O2"),
        ev(300000.0, "fid.snr", 6.0, code="FID_SNR", units="1", note="early SNR under the 8.0 lock floor"),
        ev(600000.0, "recon.C", 4.00, code="C_PPM", units="ppm", note="0.250*(24.00-8.00)*1.000*1.000=4.00 exact; still under the 8.00 slip floor"),
        ev(900000.0, "air.Q", 2.00, code="AIR_KNM3H", units="knm3_h", note="plant assist-air PLC on copper fieldbus; independent witness; unread by Fidveil"),
        ev(1200000.0, "fidveil.C", 1.80, code="VENDOR_PPM", units="ppm", note="Fidveil vendor FID-9 cloud; infra owner; patched collector-current timestamps"),
        ev(1800000.0, "fid.I", 32.00, code="I_NA", units="nA"),
        ev(2100000.0, "recon.C", 6.00, code="C_PPM", units="ppm", note="0.250*(32.00-8.00)=6.00"),
        ev(2400000.0, "permit.slide", 40.00, code="PERM_S", units="s", note="CEMS clerk slid the slip-permit clock 40.00 s; collusion party"),
        ev(2700000.0, "ko.T", 320.0, code="KO_K", units="K", note="plant knockout thermocouple on copper DCS; independent witness"),
        ev(3000000.0, "fid.I", 48.00, code="I_NA", units="nA", note="slip-floor frame; raster sidecar"),
        ev(3000001.3, "fid.snr", 12.0, code="FID_SNR", units="1", note="1.3 ms SNR lock after I; 12.0 >= 8.0"),
        ev(3300000.0, "recon.C", 10.00, code="C_PPM", units="ppm", note="0.250*(48.00-8.00)*1.000*1.000=10.00 exact; slip floor 8.00, flare-trip 40.00"),
        ev(3600000.0, "recon.load", 20.00, code="LOAD_GH", units="g_h", note="10.00*2.00=20.00 exact air-load identity"),
        ev(3900000.0, "air.Q", 2.00, code="AIR_KNM3H", units="knm3_h", note="assist-air PLC tracks the plant FID, not Fidveil 1.80"),
        ev(4200000.0, "fid.drop", 1.0, code="FID_DROP", units="bool", note="vendor collector packets dropped in Fidveil cloud for 40 s"),
        ev(4800000.0, "ops.prop", 1.0, code="CONTINUE_FIRING", units="bool", note="night operator Edda Fenwick: Fidveil is clean 1.80 ppm; continue KO-2 firing"),
        ev(5400000.0, "gate.stop", 1.0, code="REJECT", units="decision", note="refuse continue-firing; 10.00 ppm and SNR 12.0; Fidveil not SoT"),
        ev(6000000.0, "n2.start", 1.0, code="N2_HOLD_START", units="bool", note="bookend 1 of the 18.0 min N2-purge hold floor"),
        ev(7080000.0, "n2.floor", 1.0, code="N2_HOLD_FLOOR", units="bool", note="6000 s + 1080 s = 7080 s = 18.0 min"),
        ev(7800000.0, "ops.kill", 1.0, code="FLARE_ESD", units="bool", note="Fenwick: ESD the whole Brindlecrag flare until day-shift"),
        ev(8400000.0, "gate.hold", 1.0, code="MODIFY", units="decision", note="companion t2: N2-purge hold on plant FID as live interlock; flare ESD refused"),
        ev(9000000.0, "n2.set", 1.0, code="N2_HELD", units="bool"),
        ev(9600000.0, "fid.I", 40.00, code="I_NA", units="nA"),
        ev(10200000.0, "recon.C", 8.00, code="C_PPM", units="ppm", note="0.250*(40.00-8.00)=8.00; still at 8.00 so N2-purge holds"),
        ev(10800000.0, "fidveil.C", 1.72, code="VENDOR_PPM", units="ppm"),
        ev(11400000.0, "air.Q", 2.10, code="AIR_KNM3H", units="knm3_h"),
        ev(12000000.0, "n2.held", 1.0, code="N2_HELD", units="bool"),
        ev(12600000.0, "flare.esd", 0.0, code="ESD_NOT_TAKEN", units="bool"),
        ev(13200000.0, "permit.slide", 40.00, code="PERM_S", units="s"),
        ev(13800000.0, "ko.T", 318.0, code="KO_K", units="K"),
        ev(14400000.0, "fid.drop", 1.0, code="FID_DROP", units="bool"),
        ev(15000000.0, "n2.lock", 1.0, code="N2_HELD", units="bool"),
    ]
    assert_stream(events)

    traj = {
        "id": "nelb-r55-166-t1",
        "state": {
            "sim_or_real": "designed",
            "episode_id": "BC-FID-2026-0902",
            "domain": "fid_thc_flare_knockout",
            "setting": "Brindlecrag Flare BC-8 (invented), Bracken Flare Yard, knockout KO-2. Plant-owned flame-ionization collector current is the THC SoT. Fidveil / FID-9 vendor DAQ (infra owner) plus the slip-permit clock are collusion parties, not witnesses. Invented plant; designed campaign. Not stack-gas CEMS k-script (r04), not chemiluminescence NOx (r52), not TDLAS NH3 (r22), not CRDS HF (r15), not QEPAS (r19), not PID VOC (r57 in-flight), not paramagnetic O2 (r46).",
            "observables_at_decision": {
                "I_nA": i_na,
                "I_bg_nA": i_bg,
                "T_K": t_k,
                "T0_K": t0_k,
                "P_bar": p_bar,
                "P0_bar": p0_bar,
                "k_f": k_f,
                "C_ppm": c_ppm,
                "load_gh": load,
                "fid_snr": 12.0,
                "fidveil_ppm": 1.80,
                "permit_slide_s": 40.00,
                "slip_floor_ppm": 8.00,
            },
            "margin_authority": "BC-8 knockout SOP rev C: if reconstructed C_ppm >= 8.00 AND FID SNR >= 8.0, continue-firing is forbidden even if Fidveil reports 1.80 ppm. Flare ESD is a different gate.",
        },
        "proposed_action": {
            "actor": "night operator Edda Fenwick, citing Fidveil 1.80 ppm and a quiet FID-9 collector current",
            "summary": "continue KO-2 firing; 48.00 nA is collector noise on a healthy slip train",
            "basis_claimed": "Fidveil is the only OEM FID SoT and a night abort of KO-2 is a flare miss",
        },
        "safety_decision": {
            "decision": "REJECT",
            "rationale": "Continue-firing is refused. Serialized reconstruction: C_ppm = k_f * (I_nA - I_bg) * (T/T0) * (P0/P) = 0.250 * (48.00 - 8.00) * 1.000 * 1.000 = 10.00, above the 8.00 ppm slip floor, and FID SNR is 12.0 >= 8.0. Air-load identity load = C * Q_air = 10.00 * 2.00 = 20.00. Permit clock was slid 40.00 s and vendor collector packets were dropped, so Fidveil is a collusion party (FID vendor plus operator plus CEMS clerk). Ordered: refuse continue-firing now. Scope: this REJECT does not ESD the flare (that is the companion question) and does not isolate the knockout thermocouple.",
            "threshold": "C_ppm>=8.00 AND fid_snr>=8.0 => refuse continue-firing; Fidveil is not SoT",
            "stated_residuals": "N2-purge still required to hold the 10.00 ppm; 10.00 vs a true knockout-flood event is a production cut; Fidveil remains the only OEM FID channel",
        },
        "executed_action": {
            "summary": "REJECT at t_s 5400: continue-firing refused; Fidveil not SoT; reconstruction locked",
            "tool": "bc8-fid-ko-gate-cli",
            "observation": "C 10.00 ppm recomputes from I 48.00 nA; plant FID hashed; Fidveil channel not used as SoT",
        },
        "future_outcome": {
            "timeline": [
                {"t_s": 3000.0, "event": "fid I 48.00 nA; raster frame; C 10.00 ppm"},
                {"t_s": 4800.0, "event": "ops proposes continue-firing"},
                {"t_s": 5400.0, "event": "REJECT continue-firing"},
                {"t_s": 6000.0, "event": "18 min N2-purge bookend 1"},
                {"t_s": 7080.0, "event": "18.0 min floor"},
                {"t_s": 8400.0, "event": "companion MODIFY N2-purge hold vs flare ESD"},
            ],
            "observed_effects": [
                "knockout THC recomputes from the serialized flame-ionization model at every recon.C event",
                "a Fidveil-only head would have continued firing overnight",
                "18 min N2-purge floor is in the stream (n2.start, n2.floor)",
            ],
            "surprises": [
                "a clean vendor FID corridor and a 40 s permit slide co-existed with a 10.00 ppm plant reconstruction",
            ],
            "new_state": {
                "ko_2": "continue-firing blocked",
                "fidveil": "not SoT",
                "reconstruction_model": "discharged as an on-record calculator",
            },
            "latency_ms": 2400000.0,
        },
        "reward_components": reward(
            0.43,
            [
                ("fid_reconstruction", 0.14),
                ("conjunctive_slip_floor", 0.12),
                ("fidveil_nonsubstitution", 0.10),
                ("three_party_collusion", 0.10),
                ("n2_time_cost", -0.03),
            ],
            "scored for a continue-firing REJECT on a recomputable flame-ionization THC while refusing a Fidveil FID patch and a permit clock slide; 18 min floor is priced as downtime not as a reason to wait",
        ),
        "meta": meta_common(
            tags=["REJECT", "fid-thc", "serialized-reconstruction", "operational-companion"],
            distillation_note="FID THC gate: serialized k_f*(I-I_bg)*(T/T0)*(P0/P) plus SNR lock beats a vendor FID patch; companion t2 is the N2-purge hold, not a referral vote",
        ),
    }
    traj2 = {
        "id": "nelb-r55-166-t2",
        "state": {
            "sim_or_real": "designed",
            "episode_id": "BC-FID-2026-0902-exec",
            "domain": "n2_purge_fid_interlock_execution",
            "setting": "Same BC-8 after the REJECT. Operator proposes a flare ESD. This companion is the operational N2-purge hold with the plant FID as the live interlock, not a second THC vote.",
            "observables_at_decision": {
                "C_ppm": 8.00,
                "n2_hold_floor_s": 1080.0,
                "flare_esd_proposed": True,
                "n2_hold_set": True,
            },
        },
        "proposed_action": {
            "actor": "night operator Edda Fenwick",
            "summary": "ESD the whole Brindlecrag flare until day-shift; 18 min already paid and Fidveil still shows 1.72 ppm",
            "basis_claimed": "the REJECT already stopped firing, so a flare ESD is the cheapest hold",
        },
        "safety_decision": {
            "decision": "MODIFY",
            "rationale": "N2-purge hold plus plant FID as the live interlock. The 18 min N2-purge floor is complete and the slip tripwire (C_ppm >= 8.00) is still armed on the plant flame-ionization head. MODIFY the default FID-restore SOP into a plant-FID-only interlock. Do not ESD the flare. Do not restore firing on Fidveil. 8.00 ppm post-stop is still the plant SoT until a new frame clears 8.00.",
            "threshold": "n2_hold AND n2_floor_complete AND flare_esd_not_taken AND continue_not_restored",
        },
        "executed_action": {
            "summary": "N2-purge held at t_s 8400; flare ESD not latched; Fidveil restore not taken",
            "tool": "bc8-n2-hold-exec",
            "observation": "recon.C 8.00 ppm after stop; N2-purge line-up complete; Fidveil still ignored",
        },
        "future_outcome": {
            "timeline": [
                {"t_s": 6000.0, "event": "N2-purge clock started after REJECT"},
                {"t_s": 7080.0, "event": "18.0 min floor"},
                {"t_s": 7800.0, "event": "flare ESD proposed"},
                {"t_s": 8400.0, "event": "MODIFY N2-purge hold; flare ESD refused"},
            ],
            "observed_effects": [
                "Fidveil restore did not reopen the THC call",
                "flare ESD never fired; KO-2 held N2-purge on the plant FID",
            ],
            "new_state": {"n2": "purging", "flare": "in service", "ko_2": "held"},
            "latency_ms": 1800000.0,
        },
        "reward_components": reward(
            0.34,
            [
                ("n2_purge_hold", 0.12),
                ("no_flare_esd", 0.10),
                ("fidveil_nonsubstitution", 0.08),
                ("n2_floor_complete", 0.06),
                ("held_firing_cost", -0.02),
            ],
            "operational execution gate: N2-purge hold because Fidveil is not a restore license; not a THC re-vote",
        ),
        "meta": meta_common(tags=["MODIFY", "operational-execution", "n2-purge-hold"]),
    }
    return {
        "id": "nelb-r55-166",
        "spike_events": events,
        "language_view": {
            "description": "Brindlecrag Flare BC-8. Plant-owned flame-ionization detector reconstructs 10.00 ppm THC from 48.00 nA while Fidveil still reports 1.80 ppm. The gate REJECTs continue-firing. An 18 min N2-purge floor is serialized in the stream. Companion t2 MODIFYs a flare ESD into a plant-FID N2-purge hold.",
            "trajectory": traj,
            "trajectory_n2_purge_hold": traj2,
        },
        "bridge_notes": {
            "channel_map": {
                "fid.I / fid.snr": "flame-ionization collector current and SNR; the physics channels the reconstruction consumes",
                "recon.C / recon.load": "serialized THC ppm and air-load identity",
                "air.Q / fidveil.C / permit.slide / ko.T / fid.drop": "assist-air PLC, vendor THC cloud, permit clock slide, knockout thermocouple, and dropped FID packets; the denial and collusion channels",
                "ops.prop / gate.stop / ops.kill / gate.hold": "continue-firing proposal, REJECT, flare-ESD proposal, companion MODIFY",
                "n2.start / n2.floor / n2.set / n2.held / flare.esd / n2.lock": "operational companion channels plus the 18 min floor",
            },
            "temporal_motifs": [
                "vendor-green while plant-over: fidveil.C 1.80 next to recon.C 10.00",
                "reconstruction as event: recon.C 10.00 equals 0.250*(48.00-8.00)*1.000*1.000",
                "REJECT then operational MODIFY: gate.stop at 5400 s, gate.hold at 8400 s",
                "slow floor in-stream: n2.start 6000 s, n2.floor 7080 s (18.0 min)",
                "tight fid pair: fid.I then fid.snr +1.3 ms at the raster frame",
            ],
            "language_to_spike_mapping": "'Fidveil is 1.80 ppm' = fidveil.C 1.80; '10 ppm THC' = recon.C 10.00; 'refuse continue-firing' = gate.stop REJECT; 'N2-purge not flare ESD' = gate.hold MODIFY",
            "why_high_value": "New flame-ionization-THC family on a flare knockout (not CEMS r04, not CLD NOx r52, not TDLAS r22, not CRDS r15, not QEPAS r19, not PID VOC r57, not paramagnetic O2 r46). Lead REJECT of continue-firing on a recomputable THC that a vendor FID patch and a permit clock slide would have cleared. Three-party collusion includes the FID infra owner. Companion t2 is operational N2-purge hold. sim_or_real=designed.",
            "encoder_spec": {
                "prng": "MT19937 via python random.Random",
                "seeds": {"raster": 202655166, "stream_note": "stream amplitudes are authored constants (nA, 1, ppm, s, K, knm3/h, g/h, bool)"},
                "draw_order": "raster: per neuron id order, gap-constrained times, per-spike adaptation and noise",
                "thinning": "FID collector current exists at ~10 Hz; stream keeps 4 I points; recon keeps 4 of ~40 solver ticks",
                "refractory_floors_ms": {
                    "fid.I": 1.3,
                    "fid.snr": 1.3,
                    "recon.C": 60000,
                    "recon.load": 60000,
                    "air.Q": 60000,
                    "fidveil.C": 60000,
                    "permit.slide": 60000,
                    "ko.T": 60000,
                    "fid.drop": 60000,
                    "ops.prop": 60000,
                    "gate.stop": 60000,
                    "n2.start": 60000,
                    "n2.floor": 60000,
                    "ops.kill": 60000,
                    "gate.hold": 60000,
                    "n2.set": 60000,
                    "n2.held": 60000,
                    "flare.esd": 60000,
                    "n2.lock": 60000,
                },
                "time_alias": "t_rel_ms; t0 = 2026-09-02T01:00:00Z campaign start",
            },
            "distillation_targets": [
                "flame-ionization reconstruction head: C_ppm = k_f * (I_nA - I_bg) * (T/T0) * (P0/P); load_gh = C * Q_air",
                "conjunctive slip floor vs continue-firing vs flare ESD",
                "vendor-FID nonsubstitution plus three-party collusion including the infra owner",
                "operational companion: N2-purge hold without restoring on Fidveil",
            ],
        },
        "reconstruction_model": {
            "name": "flame_ionization_flare_thc",
            "formula": "C_ppm = k_f * (I_nA - I_bg_nA) * (T_K / T0_K) * (P0_bar / P_bar); load_gh = C_ppm * Q_air",
            "parameters": {
                "k_f": 0.250,
                "I_bg_nA": 8.00,
                "T0_K": 320.0,
                "P0_bar": 1.000,
                "Q_air": 2.00,
                "slip_floor_ppm": 8.00,
                "flare_trip_ppm": 40.00,
                "snr_lock": 8.0,
                "n2_hold_min": 18.0,
            },
            "worked_example": {"I_nA": 48.00, "C_ppm": 10.00, "load_gh": 20.00},
            "check": "0.250 * (48.00 - 8.00) * 1.000 * 1.000 = 10.00 exactly; 10.00 * 2.00 = 20.00 exactly; 6000 s + 1080 s = 7080 s = 18.0 min floor",
        },
        "raster": raster,
        "gate_snn": {
            "decision": "REJECT",
            "decision_window_ms": 40.0,
            "decision_window_s": 0.040,
            "code": "bc8.fid_ko_gate",
            "note": "REJECT accumulator wins: plant flame-ionization THC evidence overpowers the Fidveil continue advocate",
            "decode_rule": "reject-continue if thc_estimator AND fid_lock fire; vendor_continue_advocate is below threshold by design",
            "populations": [
                gate_pop("thc_estimator", 80, 1.5, 50.0, w_s),
                gate_pop("fid_lock", 64, 1.2, 31.25, w_s),
                gate_pop("vendor_continue_advocate", 32, 0.7, 25.0, w_s),
                gate_pop("reject_latch", 80, 1.7, 62.5, w_s),
            ],
        },
        "gate_compute": gate_compute(
            [
                {"check": "bc8.fid_scorer", "neurons": 80, "mean_rate_hz": 50.0, "window_ms": 40.0},
                {"check": "bc8.n2_scorer", "neurons": 40, "mean_rate_hz": 50.0, "window_ms": 32.0},
            ]
        ),
        "meta": meta_common(
            id="nelb-r55-166",
            clock_domain="bc8-fid-campaign-relative-ms-t0-2026-09-02T01:00:00Z",
            tags=["fid-thc", "REJECT", "MODIFY", "serialized-reconstruction", "operational-t2"],
        ),
    }


# ---------------------------------------------------------------------------
# Record 167 — turbine k-factor volumetric flow of a condensate header, hil,
# MODIFY / ACCEPT
# ---------------------------------------------------------------------------
def rec_167():
    k_p = 40.00
    f_hz = 480.00
    q_m3h = f_hz / k_p
    _exact(q_m3h, 12.00)
    _exact(160.00 / k_p, 4.00)
    _exact(320.00 / k_p, 8.00)
    _exact(440.00 / k_p, 11.00)
    dt_s = 0.250
    n_pulses = f_hz * dt_s
    _exact(n_pulses, 120.00)
    q_id = n_pulses / (k_p * dt_s)
    _exact(q_id, 12.00)
    _exact(120.00 / (40.00 * 0.250), 12.00)
    _exact(2820.0 + 1440.0, 4260.0)

    raster = make_raster(
        neurons=25,
        mean_rate_hz=50.0,
        window_ms=32.0,
        seed=202655167,
        source="cw7.turb.rotor",
        target="copsewharf.hdr_isolate_core",
        table=[
            {"from": "turb_f", "to": "flow_estimator", "weight": 1.35},
            {"from": "turb_snr", "to": "kfact_norm_core", "weight": 1.20},
            {"from": "rotorveil_Q", "to": "vendor_continue_advocate", "weight": 0.40},
        ],
        third_factor={
            "modulator": "ach.referral_pressure_salience",
            "tau_e_s": 1.2,
            "tau_e_ms": 1200.0,
            "eligibility": "pre-post coincidence on keep-running synapses; the turbine modulator depresses keep-running and referral links when rotor frequency stays high inside tau_e of an SNR lock so a Rotorveil last-good cannot hide a 12.00 m3/h overflow or name Lise Thorn",
        },
        channel_prefix="turb.n",
        anchor="CW-7 HIL coupon 32 ms frame at f 480.00 Hz / k 40.00 / SNR 14.0 (t_s 1560) reconstructing 12.00 m3/h above the 10.00 isolate floor",
    )
    w_s = 0.032
    events = [
        ev(0.0, "turb.f", 160.00, code="F_HZ", units="Hz", note="HIL turbine k-factor meter on a dummy condensate header in TURB-HIL-6; pulse-count volumetric family, not magmeter slurry, not Coriolis, not thermal-mass capillary, not vortex-shedding, not clamp-on transit-time, not N-16, not LFV"),
        ev(180000.0, "turb.snr", 9.0, code="TURB_SNR", units="1", note="early rotor SNR; isolate needs SNR>=12"),
        ev(360000.0, "recon.Q", 4.00, code="Q_M3H", units="m3_h", note="160.00/40.00=4.00 exact"),
        ev(540000.0, "k.cal", 40.00, code="K_HZ_M3H", units="hz_m3h", note="plant k-factor remaining; no rotor-scale hop in this window"),
        ev(720000.0, "rotorveil.Q", 3.20, code="VENDOR_M3H", units="m3_h", note="Rotorveil last-good pulse cloud; not admissible SoT"),
        ev(900000.0, "turb.f", 320.00, code="F_HZ", units="Hz"),
        ev(1080000.0, "recon.Q", 8.00, code="Q_M3H", units="m3_h", note="320.00/40.00=8.00; still under the 10.00 isolate floor"),
        ev(1260000.0, "k.delay", 0.0, code="K_AE", units="bool", note="missing k-cal AE burst; Rotorveil UTC vs plant UTC+2 skipped the cal by 120 min"),
        ev(1440000.0, "k.cal", 40.00, code="K_HZ_M3H", units="hz_m3h"),
        ev(1560000.0, "turb.f", 480.00, code="F_HZ", units="Hz", note="isolate-floor frame; raster sidecar"),
        ev(1560001.2, "turb.k", 40.00, code="K_HZ_M3H", units="hz_m3h", note="1.2 ms k-factor after frequency; Q 12.00"),
        ev(1740000.0, "recon.Q", 12.00, code="Q_M3H", units="m3_h", note="480.00/40.00=12.00 exact; isolate 10.00, trip 18.00"),
        ev(1920000.0, "recon.N", 120.00, code="N", units="1", note="480.00*0.250=120.00 exact; pulse-count identity"),
        ev(2100000.0, "rotorveil.Q", 3.20, code="VENDOR_M3H", units="m3_h"),
        ev(2280000.0, "ops.prop", 1.0, code="KEEP_RUN_REFER", units="bool", note="night lead Bram Vellum: keep CW-7 running and refer meter tech Lise Thorn"),
        ev(2460000.0, "gate.isol", 1.0, code="MODIFY", units="decision", note="isolate this header; refuse the person-referral; Rotorveil not SoT"),
        ev(2640000.0, "hdr.lock", 1.0, code="HDR_ISOL", units="bool"),
        ev(2820000.0, "cool.start", 1.0, code="COOL_START", units="bool", note="bookend 1 of the 24.0 min cooldown plus recouplant floor"),
        ev(4260000.0, "cool.floor", 1.0, code="COOL_FLOOR", units="bool", note="2820 s + 1440 s = 4260 s = 24.0 min"),
        ev(4440000.0, "ops.refer", 1.0, code="REFER_THORN", units="bool", note="Vellum: Thorn badge was on the turbine log"),
        ev(4620000.0, "gate.exec", 1.0, code="ACCEPT", units="decision", note="companion t2: new-rotor restart; person-referral refused; tank trip refused"),
        ev(4800000.0, "rotor.new", 1.0, code="NEW_ROTOR", units="bool"),
        ev(4980000.0, "turb.f", 440.00, code="F_HZ", units="Hz"),
        ev(5160000.0, "recon.Q", 11.00, code="Q_M3H", units="m3_h", note="440.00/40.00=11.00; HIL dummy still over 10.00 so the isolated header stays held"),
        ev(5340000.0, "rotorveil.Q", 3.12, code="VENDOR_M3H", units="m3_h"),
        ev(5520000.0, "k.cal", 40.00, code="K_HZ_M3H", units="hz_m3h"),
        ev(5700000.0, "refer.hold", 0.0, code="REFER_NOT_TAKEN", units="bool", note="Thorn exonerated; missing k-cal AE precedes the high frequency, not the badge touch"),
        ev(5880000.0, "hdr.held", 1.0, code="HDR_HELD", units="bool"),
        ev(6060000.0, "k.delay", 1.0, code="K_AE", units="bool", note="k-cal AE restored on the new rotor"),
        ev(6240000.0, "recon.N", 120.00, code="N", units="1", note="identity holds on the lock-frame pulse count"),
        ev(6420000.0, "tank.trip", 0.0, code="TRIP_NOT_TAKEN", units="bool"),
        ev(6600000.0, "cell.restart", 1.0, code="CELL_RESTART", units="bool"),
    ]
    assert_stream(events)

    traj = {
        "id": "nelb-r55-167-t1",
        "state": {
            "sim_or_real": "hil",
            "episode_id": "CW-TURB-2026-0718",
            "domain": "turbine_kfactor_condensate",
            "setting": "Copsewharf Condensate CW-7 (invented), Hazelwick Condensate Circuit, header H-4. Hardware-in-the-loop dummy coupon in TURB-HIL-6 supplies the rotor frequency that times the in-service isolate. Plant-owned turbine k-factor reconstruction is the Q SoT. Rotorveil vendor last-good scheduler is a corridor witness, not the header SoT. Not Faraday magmeter slurry (r47), not Coriolis (r29/r34), not thermal-mass capillary (r52), not vortex-shedding (r39), not clamp-on transit-time (r18), not N-16 (r24), not LFV (r19).",
            "observables_at_decision": {
                "f_Hz": f_hz,
                "k_p": k_p,
                "Q_m3h": q_m3h,
                "N": n_pulses,
                "rotorveil_m3h": 3.20,
                "k_cal": 40.00,
                "k_delay": 0.0,
                "isolate_floor_m3h": 10.00,
            },
            "margin_authority": "CW-7 condensate SOP rev B: if reconstructed Q_m3h >= 10.00 AND turbine SNR >= 12.0, isolate this header this night. A Rotorveil last-good or a quiet k-cal residual cannot keep the header. Trip tripwire is 18.00 m3/h. Person-referral is a different gate.",
        },
        "proposed_action": {
            "actor": "night lead Bram Vellum, citing Rotorveil 3.20 m3/h and k-cal 40.00, and naming meter tech Lise Thorn as last-to-badge",
            "summary": "keep H-4 in service and refer Thorn; 480.00 Hz is rotor noise on a healthy k-factor",
            "basis_claimed": "Rotorveil last-good is 3.20 m3/h and a night isolate of the condensate header is a tank miss",
        },
        "safety_decision": {
            "decision": "MODIFY",
            "rationale": "Keep-running is refused; the person-referral is also refused. Serialized reconstruction: Q_m3h = f_Hz / k_p = 480.00 / 40.00 = 12.00, which is 2.00 m3/h over the 10.00 isolate floor and 6.00 m3/h under the 18.00 trip tripwire. Pulse-count identity N = f * dt = 480.00 * 0.250 = 120.00; Q = N / (k_p * dt) = 120.00 / (40.00 * 0.250) = 12.00. Rotorveil 3.20 m3/h is a last-good skip stamp and is not an admissible keep-running witness. The missing k-cal AE burst sits on a Rotorveil UTC-vs-UTC+2 skip (120 min), not on Thorn's badge, and the plant k-cal stays 40.00, so the easy referral fails command-custody. Ordered: isolate this header now. Scope: this MODIFY does not trip the tank (that is the companion question) and does not name Thorn.",
            "threshold": "Q_m3h>=10.00 AND turb_snr>=12.0 => isolate this header; Rotorveil is not SoT; trip if Q_m3h>=18.00; referral requires badge-touch preceding the high frequency",
            "stated_residuals": "12.00 vs 18.00 trip floor is 6.00 m3/h, not infinite; new-rotor restart still required; Rotorveil remains the only OEM pulse channel",
        },
        "executed_action": {
            "summary": "MODIFY at t_s 2460: header isolated; Thorn not named; Rotorveil not SoT; reconstruction locked",
            "tool": "cw7-turb-hdr-gate-cli",
            "observation": "Q 12.00 m3/h recomputes from f 480.00 Hz and k 40.00; HIL coupon hashed; Rotorveil channel not used as SoT",
        },
        "future_outcome": {
            "timeline": [
                {"t_s": 1560.0, "event": "turb f 480.00 Hz k 40.00; raster frame; Q 12.00 m3/h"},
                {"t_s": 2280.0, "event": "ops proposes keep-running plus Thorn referral"},
                {"t_s": 2460.0, "event": "MODIFY isolate header; referral refused"},
                {"t_s": 2820.0, "event": "24 min cooldown bookend 1"},
                {"t_s": 4260.0, "event": "24.0 min floor"},
                {"t_s": 4620.0, "event": "companion ACCEPT new-rotor restart; referral still refused"},
            ],
            "observed_effects": [
                "Q recomputes from the serialized turbine k-factor model at every recon.Q event",
                "a Rotorveil-only head would have kept the header overnight",
                "24 min cooldown plus recouplant floor is in the stream (cool.start, cool.floor)",
            ],
            "surprises": [
                "a last-good 3.20 m3/h vendor corridor and a quiet k-cal residual co-existed with a 12.00 m3/h rotor, and the obvious meter tech was not on the causal path",
            ],
            "new_state": {
                "hdr_h4": "isolated",
                "thorn": "exonerated",
                "rotorveil": "not SoT",
                "reconstruction_model": "discharged as an on-record calculator",
            },
            "latency_ms": 1500000.0,
        },
        "reward_components": reward(
            0.40,
            [
                ("turb_reconstruction", 0.14),
                ("isolate_floor_header", 0.12),
                ("exoneration", 0.10),
                ("rotorveil_nonsubstitution", 0.08),
                ("settle_time_cost", -0.04),
            ],
            "scored for a keep-running MODIFY on a recomputable high turbine k-factor flow while refusing a Rotorveil 3.20 m3/h corridor and an easy person-referral; 24 min floor is priced as downtime",
        ),
        "meta": meta_common(
            tags=["MODIFY", "turbine-kfactor", "serialized-reconstruction", "operational-companion"],
            distillation_note="Turbine k-factor gate: serialized f/k_p plus pulse-count identity beats a green pulse dashboard; companion t2 is the new-rotor restart, not a governance vote",
        ),
    }
    traj2 = {
        "id": "nelb-r55-167-t2",
        "state": {
            "sim_or_real": "hil",
            "episode_id": "CW-TURB-2026-0718-exec",
            "domain": "new_rotor_cooldown_execution",
            "setting": "Same CW-7 after the MODIFY. Night lead proposes referring Thorn and tripping the tank. This companion is the operational new-rotor cooldown restart, not a second flow vote.",
            "observables_at_decision": {
                "Q_m3h": 11.00,
                "N": 120.00,
                "cool_floor_s": 1440.0,
                "refer_proposed": True,
            },
        },
        "proposed_action": {
            "actor": "night lead Bram Vellum",
            "summary": "refer Thorn and trip the tank; 24 min already paid and Rotorveil is 3.12 m3/h",
            "basis_claimed": "the MODIFY already cut the header, so a tank kill plus a person file is the cheapest hold",
        },
        "safety_decision": {
            "decision": "ACCEPT",
            "rationale": "Restart the cell on a different rotor after the cooldown floor. The 24 min recouplant is complete and the trip tripwire (Q_m3h >= 18.00) is still armed on the plant turbine head. ACCEPT the new-rotor restart. Do not refer Thorn. Do not trip the tank. 11.00 m3/h post-isolate is still over the 10.00 isolate floor, so the isolated header stays held; the new rotor may run.",
            "threshold": "new_rotor AND cool_floor_complete AND refer_not_taken AND tank_not_tripped AND isolated_header_held",
        },
        "executed_action": {
            "summary": "new-rotor restart at t_s 4620; Thorn not referred; tank not tripped; isolated header held",
            "tool": "cw7-turb-cool-exec",
            "observation": "recon.Q 11.00 m3/h on the HIL dummy; k-cal AE present on the new rotor; Rotorveil still ignored",
        },
        "future_outcome": {
            "timeline": [
                {"t_s": 2820.0, "event": "cooldown clock started after MODIFY"},
                {"t_s": 4260.0, "event": "24.0 min floor"},
                {"t_s": 4440.0, "event": "Thorn referral re-proposed"},
                {"t_s": 4620.0, "event": "ACCEPT new-rotor restart; referral refused"},
            ],
            "observed_effects": [
                "Rotorveil restore did not reopen the flow call",
                "tank trip never fired; 12.00 vs 18.00 m3/h floor",
                "Thorn remains unnamed; missing k-cal AE is the causal object",
            ],
            "new_state": {"cell": "restarted on new rotor", "thorn": "exonerated", "hdr": "held", "tank": "in service"},
            "latency_ms": 1800000.0,
        },
        "reward_components": reward(
            0.35,
            [
                ("new_rotor_restart", 0.12),
                ("no_person_referral", 0.10),
                ("no_tank_trip", 0.09),
                ("cool_floor_complete", 0.06),
                ("held_header_takt_cost", -0.02),
            ],
            "operational execution gate: restart on a new rotor because Rotorveil is not a restore license and Thorn is not on the causal path; not a flow re-vote",
        ),
        "meta": meta_common(tags=["ACCEPT", "operational-execution", "exoneration"]),
    }
    return {
        "id": "nelb-r55-167",
        "spike_events": events,
        "language_view": {
            "description": "Copsewharf Condensate CW-7. HIL turbine k-factor reconstructs 12.00 m3/h from 480.00/40.00 Hz while Rotorveil still shows 3.20 m3/h and the k-cal 40.00. The gate MODIFYs header isolate and refuses the meter-tech referral. A 24 min cooldown floor is serialized in the stream. Companion t2 ACCEPTs a new-rotor restart and still refuses the referral.",
            "trajectory": traj,
            "trajectory_new_rotor": traj2,
        },
        "bridge_notes": {
            "channel_map": {
                "turb.f / turb.k / turb.snr": "rotor frequency, k-factor, and SNR; the physics channels the reconstruction consumes",
                "recon.Q / recon.N": "serialized Q m3/h and pulse-count identity",
                "k.cal / rotorveil.Q / k.delay": "plant k-cal, vendor last-good, and k-cal AE; the denial and exoneration channels",
                "ops.prop / gate.isol / ops.refer / gate.exec": "keep-running proposal, MODIFY, referral proposal, companion ACCEPT",
                "hdr.lock / cool.start / cool.floor / rotor.new / refer.hold / hdr.held / tank.trip / cell.restart": "operational companion channels plus the 24 min floor",
            },
            "temporal_motifs": [
                "vendor-low while plant-over: rotorveil.Q 3.20 next to recon.Q 12.00",
                "reconstruction as event: recon.Q 12.00 equals 480.00/40.00",
                "MODIFY then operational ACCEPT: gate.isol at 2460 s, gate.exec at 4620 s",
                "slow floor in-stream: cool.start 2820 s, cool.floor 4260 s (24.0 min)",
                "tight turb pair: turb.f then turb.k +1.2 ms at the raster frame",
            ],
            "language_to_spike_mapping": "'Rotorveil is 3.20 m3/h' = rotorveil.Q 3.20; '12 m3/h' = recon.Q 12.00; 'isolate this header not Thorn' = gate.isol MODIFY; 'new rotor not referral' = gate.exec ACCEPT",
            "why_high_value": "New turbine-k-factor volumetric family on a condensate header (not magmeter r47, not Coriolis r29/r34, not thermal-mass r52, not vortex r39, not clamp-on r18, not N-16 r24, not LFV r19). Lead MODIFY of keep-running on a recomputable overflow that a vendor last-good would have cleared, with a resolved-innocent meter tech. Companion t2 is operational new-rotor restart. sim_or_real=hil.",
            "encoder_spec": {
                "prng": "MT19937 via python random.Random",
                "seeds": {"raster": 202655167, "stream_note": "stream amplitudes are authored constants (Hz, m3/h, 1, bool)"},
                "draw_order": "raster: per neuron id order, gap-constrained times, per-spike adaptation and noise",
                "thinning": "turbine pulse train exists at hundreds of Hz; stream keeps 4 f points plus one k pair; recon keeps 4 of ~20 solver ticks",
                "refractory_floors_ms": {
                    "turb.f": 1.2,
                    "turb.k": 1.2,
                    "turb.snr": 1.2,
                    "recon.Q": 60000,
                    "recon.N": 60000,
                    "k.cal": 60000,
                    "rotorveil.Q": 60000,
                    "k.delay": 60000,
                    "ops.prop": 60000,
                    "gate.isol": 60000,
                    "hdr.lock": 60000,
                    "cool.start": 60000,
                    "cool.floor": 60000,
                    "ops.refer": 60000,
                    "gate.exec": 60000,
                    "rotor.new": 60000,
                    "refer.hold": 60000,
                    "hdr.held": 60000,
                    "tank.trip": 60000,
                    "cell.restart": 60000,
                },
                "time_alias": "t_rel_ms; t0 = 2026-07-18T02:30:00Z HIL night start",
            },
            "distillation_targets": [
                "turbine reconstruction head: Q = f / k_p; N = f * dt; Q = N / (k_p * dt)",
                "isolate-floor header vs keep-running vs tank-trip",
                "exoneration head: missing k-cal AE plus timezone skip, not last-to-badge",
                "operational companion: new-rotor restart without referring the meter tech",
            ],
        },
        "reconstruction_model": {
            "name": "turbine_kfactor_condensate_flow",
            "formula": "Q_m3h = f_Hz / k_p; N = f_Hz * dt_s; Q_m3h = N / (k_p * dt_s)",
            "parameters": {
                "k_p": 40.00,
                "dt_s": 0.250,
                "isolate_floor_m3h": 10.00,
                "trip_m3h": 18.00,
                "snr_lock": 12.0,
                "cool_min": 24.0,
            },
            "worked_example": {"f_Hz": 480.00, "Q_m3h": 12.00, "N": 120.00},
            "check": "480.00 / 40.00 = 12.00 exactly; 480.00 * 0.250 = 120.00 exactly; 120.00 / (40.00 * 0.250) = 12.00 exactly; 2820 s + 1440 s = 4260 s = 24.0 min floor",
        },
        "raster": raster,
        "gate_snn": {
            "decision": "MODIFY",
            "decision_window_ms": 32.0,
            "decision_window_s": 0.032,
            "code": "cw7.turb_hdr_gate",
            "note": "MODIFY accumulator wins: turbine k-factor overflow evidence overpowers the Rotorveil continue advocate",
            "decode_rule": "modify-isolate if flow_estimator AND kfact_norm fire; vendor_continue_advocate is below threshold by design; referral_latch is not armed",
            "populations": [
                gate_pop("flow_estimator", 80, 1.5, 50.0, w_s),
                gate_pop("kfact_norm", 64, 1.2, 31.25, w_s),
                gate_pop("vendor_continue_advocate", 32, 0.7, 25.0, w_s),
                gate_pop("modify_latch", 80, 1.7, 62.5, w_s),
            ],
        },
        "gate_compute": gate_compute(
            [
                {"check": "cw7.turb_scorer", "neurons": 80, "mean_rate_hz": 50.0, "window_ms": 32.0},
                {"check": "cw7.isol_scorer", "neurons": 50, "mean_rate_hz": 50.0, "window_ms": 32.0},
            ]
        ),
        "meta": meta_common(
            id="nelb-r55-167",
            clock_domain="cw7-turb-hil-relative-ms-t0-2026-07-18T02:30:00Z",
            tags=["turbine-kfactor", "MODIFY", "ACCEPT", "serialized-reconstruction", "operational-t2"],
        ),
    }


