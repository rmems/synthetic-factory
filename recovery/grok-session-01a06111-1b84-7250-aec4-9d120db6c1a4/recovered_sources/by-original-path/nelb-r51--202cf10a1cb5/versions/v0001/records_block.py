def occupancy_preflight():
    banned = (
        "brackholt",
        "dewholt",
        "pebblewick",
        "heatveil",
        "dewveil",
        "correlveil",
        "gardon-gauge",
        "gardon gauge",
        "chilled-mirror",
        "chilled mirror",
        "digital image correlation",
        "calum brindle",
        "soren peck",
        "maren quill",
        "iona greaves",
    )
    hits = []
    root = Path("/tmp")
    for n in sorted(root.glob("nelb-r[0-9]*")):
        if not n.is_dir() or n.name == "nelb-r51":
            continue
        for f in n.iterdir():
            if f.suffix not in {".py", ".md", ".jsonl"}:
                continue
            text = f.read_text(encoding="utf-8", errors="replace").casefold()
            for b in banned:
                if b in text:
                    hits.append(f"{f}:{b}")
    if hits:
        raise RuntimeError(f"family/plant collision {hits}")


# ---------------------------------------------------------------------------
# Record 154 — Gardon-gauge incident heat flux of a reformer arch, designed,
# REJECT / MODIFY
# ---------------------------------------------------------------------------
def rec_154():
    k_g = 4.00
    e_mv = 12.50
    q_kw = k_g * e_mv
    _exact(q_kw, 50.00)
    _exact(k_g * 5.00, 20.00)
    _exact(k_g * 10.00, 40.00)
    _exact(k_g * 8.00, 32.00)
    k_t = 0.80
    dt_k = k_t * e_mv
    _exact(dt_k, 10.00)
    _exact(0.80 * 12.50, 10.00)
    k_q = 5.00
    _exact(k_q * dt_k, 50.00)
    _exact(5.00 * 10.00, 50.00)
    _exact(6000.0 + 1080.0, 7080.0)

    raster = make_raster(
        neurons=20,
        mean_rate_hz=50.0,
        window_ms=40.0,
        seed=202609154,
        source="bh8.gardon.foil",
        target="brackholt.arch_stop_core",
        table=[
            {"from": "gard_E", "to": "flux_estimator", "weight": 1.40},
            {"from": "gard_snr", "to": "foil_lock_core", "weight": 1.15},
            {"from": "heatveil_q", "to": "vendor_continue_advocate", "weight": 0.45},
        ],
        third_factor={
            "modulator": "da.cross_authority_conflict",
            "tau_e_s": 1.6,
            "tau_e_ms": 1600.0,
            "eligibility": "pre-post coincidence on keep-firing synapses; the plant Gardon modulator depresses keep-firing links when foil emf stays high inside tau_e of an SNR lock so a Heatveil last-good patch cannot hide a 50.00 kW/m2 arch",
        },
        channel_prefix="gard.n",
        anchor="BH-8 Gardon foil 40 ms frame at E 12.50 mV / SNR 12.0 (t_s 3000) reconstructing 50.00 kW/m2 above the 20.00 isolate floor",
    )
    w_s = 0.040
    events = [
        ev(0.0, "gard.E", 5.00, code="E_MV", units="mV", note="plant-owned Gardon-gauge foil on BH-8 arch A-2; incident heat-flux family, not acoustic pyrometry, not phosphor-lifetime, not LII soot, not CARS TIT, not FMCW lining, not lock-in thermography"),
        ev(300000.0, "gard.snr", 6.0, code="GARD_SNR", units="1", note="early SNR under the 8.0 lock floor"),
        ev(600000.0, "recon.q", 20.00, code="Q_KWM2", units="kW_m2", note="4.00*5.00=20.00 exact; at the 20.00 isolate floor"),
        ev(900000.0, "ir.arch", 8.80, code="IR_KWM2", units="kW_m2", note="serial-only two-color pyrometer cart; independent witness; unread by Heatveil"),
        ev(1200000.0, "heatveil.q", 6.40, code="VENDOR_KWM2", units="kW_m2", note="Heatveil vendor foil-cloud; infra owner; patched emf timestamps"),
        ev(1800000.0, "gard.E", 10.00, code="E_MV", units="mV"),
        ev(2100000.0, "recon.q", 40.00, code="Q_KWM2", units="kW_m2", note="4.00*10.00=40.00"),
        ev(2400000.0, "permit.slide", 40.00, code="PERM_S", units="s", note="permit clerk slid firing-hold clock 40.00 s; collusion party"),
        ev(2700000.0, "arch.T", 1180.0, code="ARCH_K", units="K", note="plant arch thermocouple on copper DCS; independent witness"),
        ev(3000000.0, "gard.E", 12.50, code="E_MV", units="mV", note="isolate-floor frame; raster sidecar"),
        ev(3000001.3, "gard.snr", 12.0, code="GARD_SNR", units="1", note="1.3 ms SNR lock after E; 12.0 >= 8.0"),
        ev(3300000.0, "recon.q", 50.00, code="Q_KWM2", units="kW_m2", note="4.00*12.50=50.00 exact; isolate floor 20.00, ESD tripwire 80.00"),
        ev(3600000.0, "recon.dT", 10.00, code="DT_K", units="K", note="0.80*12.50=10.00 exact foil-temperature identity; 5.00*10.00=50.00"),
        ev(3900000.0, "ir.arch", 49.20, code="IR_KWM2", units="kW_m2", note="two-color cart tracks the plant Gardon, not Heatveil 6.40"),
        ev(4200000.0, "heat.drop", 1.0, code="HEAT_DROP", units="bool", note="vendor foil packets dropped in Heatveil cloud for 40 s"),
        ev(4800000.0, "ops.prop", 1.0, code="KEEP_FIRE", units="bool", note="night reformer operator Calum Brindle: Heatveil is clean 6.40 kW/m2; keep A-2 firing"),
        ev(5400000.0, "gate.stop", 1.0, code="REJECT", units="decision", note="refuse keep-firing; 50.00 kW/m2 and SNR 12.0; Heatveil not SoT"),
        ev(6000000.0, "spray.start", 1.0, code="SPRAY_START", units="bool", note="bookend 1 of the 18.0 min water-spray floor"),
        ev(7080000.0, "spray.floor", 1.0, code="SPRAY_FLOOR", units="bool", note="6000 s + 1080 s = 7080 s = 18.0 min"),
        ev(7800000.0, "ops.kill", 1.0, code="REFORMER_ESD", units="bool", note="Brindle: ESD the whole Brackholt reformer until day-shift"),
        ev(8400000.0, "gate.hold", 1.0, code="MODIFY", units="decision", note="companion t2: water-spray hold on plant Gardon as live interlock; reformer ESD refused"),
        ev(9000000.0, "spraylock.set", 1.0, code="SPRAY_HELD", units="bool"),
        ev(9600000.0, "gard.E", 8.00, code="E_MV", units="mV"),
        ev(10200000.0, "recon.q", 32.00, code="Q_KWM2", units="kW_m2", note="4.00*8.00=32.00; still above 20.00 so spray holds"),
        ev(10800000.0, "heatveil.q", 6.20, code="VENDOR_KWM2", units="kW_m2"),
        ev(11400000.0, "ir.arch", 31.80, code="IR_KWM2", units="kW_m2"),
        ev(12000000.0, "spray.held", 1.0, code="SPRAY_HELD", units="bool"),
        ev(12600000.0, "ref.esd", 0.0, code="ESD_NOT_TAKEN", units="bool"),
        ev(13200000.0, "permit.slide", 40.00, code="PERM_S", units="s"),
        ev(13800000.0, "arch.T", 1164.0, code="ARCH_K", units="K"),
        ev(14400000.0, "heat.drop", 1.0, code="HEAT_DROP", units="bool"),
        ev(15000000.0, "spraylock.held", 1.0, code="SPRAY_HELD", units="bool"),
    ]
    assert_stream(events)

    traj = {
        "id": "nelb-r51-154-t1",
        "state": {
            "sim_or_real": "designed",
            "episode_id": "BH-GARD-2026-0902",
            "domain": "gardon_heat_flux_reformer_arch",
            "setting": "Brackholt Reformer BH-8 (invented), Tarnspire Hydrogen, arch A-2. Plant-owned Gardon-gauge foil is the incident-flux SoT. Heatveil vendor DAQ (infra owner) plus the firing-hold permit clock are collusion parties, not witnesses. Invented plant; designed campaign. Not acoustic pyrometry (r25), not phosphor-lifetime (r39), not LII soot (r31), not CARS TIT (r29), not FMCW lining (r33), not lock-in thermography (r23).",
            "observables_at_decision": {
                "E_mV": e_mv,
                "k_g": k_g,
                "q_kWm2": q_kw,
                "dT_K": dt_k,
                "gard_snr": 12.0,
                "heatveil_kWm2": 6.40,
                "permit_slide_s": 40.00,
                "isolate_floor_kWm2": 20.00,
            },
            "margin_authority": "BH-8 arch SOP rev C: if reconstructed q_kWm2 >= 20.00 AND Gardon SNR >= 8.0, keep-firing is forbidden even if Heatveil reports 6.40 kW/m2. Reformer ESD is a different gate.",
        },
        "proposed_action": {
            "actor": "night reformer operator Calum Brindle, citing Heatveil 6.40 kW/m2 and a quiet foil cloud",
            "summary": "keep A-2 firing; 12.50 mV is foil noise on a healthy radiant arch",
            "basis_claimed": "Heatveil is the only OEM Gardon SoT and a night abort of A-2 is a hydrogen-train miss",
        },
        "safety_decision": {
            "decision": "REJECT",
            "rationale": "Keep-firing is refused. Serialized reconstruction: q_kWm2 = k_g * E_mV = 4.00 * 12.50 = 50.00, above the 20.00 isolate floor and 30.00 under the 80.00 ESD tripwire, and Gardon SNR is 12.0 >= 8.0. Foil-temperature identity dT = 0.80 * 12.50 = 10.00 K and q = 5.00 * 10.00 = 50.00. Permit clock was slid 40.00 s and vendor foil packets were dropped, so Heatveil is a collusion party (foil vendor plus operator plus permit clerk). Ordered: refuse keep-firing now. Scope: this REJECT does not ESD the reformer (that is the companion question) and does not isolate the arch thermocouple.",
            "threshold": "q_kWm2>=20.00 AND gard_snr>=8.0 => refuse keep-firing; Heatveil is not SoT; ESD if q_kWm2>=80.00",
            "stated_residuals": "water-spray still required to hold the 50.00 kW/m2; 50.00 vs a true tube-rupture is a production cut; Heatveil remains the only OEM foil channel",
        },
        "executed_action": {
            "summary": "REJECT at t_s 5400: keep-firing refused; Heatveil not SoT; reconstruction locked",
            "tool": "bh8-gardon-arch-gate-cli",
            "observation": "q 50.00 kW/m2 recomputes from E 12.50 mV; plant foil hashed; Heatveil channel not used as SoT",
        },
        "future_outcome": {
            "timeline": [
                {"t_s": 3000.0, "event": "gardon E 12.50 mV; raster frame; q 50.00 kW/m2"},
                {"t_s": 4800.0, "event": "ops proposes keep-firing"},
                {"t_s": 5400.0, "event": "REJECT keep-firing"},
                {"t_s": 6000.0, "event": "18 min water-spray bookend 1"},
                {"t_s": 7080.0, "event": "18.0 min floor"},
                {"t_s": 8400.0, "event": "companion MODIFY water-spray hold vs reformer ESD"},
            ],
            "observed_effects": [
                "arch flux recomputes from the serialized Gardon model at every recon.q event",
                "a Heatveil-only head would have kept A-2 firing overnight",
                "18 min water-spray floor is in the stream (spray.start, spray.floor)",
            ],
            "surprises": [
                "a clean vendor foil corridor and a 40 s permit slide co-existed with a 50.00 kW/m2 plant reconstruction",
            ],
            "new_state": {
                "a2": "keep-firing blocked",
                "heatveil": "not SoT",
                "reconstruction_model": "discharged as an on-record calculator",
            },
            "latency_ms": 2400000.0,
        },
        "reward_components": reward(
            0.43,
            [
                ("gardon_reconstruction", 0.14),
                ("conjunctive_isolate_floor", 0.12),
                ("heatveil_nonsubstitution", 0.10),
                ("three_party_collusion", 0.10),
                ("spray_time_cost", -0.03),
            ],
            "scored for a keep-firing REJECT on a recomputable Gardon flux while refusing a Heatveil foil patch and a permit clock slide; 18 min floor is priced as downtime not as a reason to wait",
        ),
        "meta": meta_common(
            tags=["REJECT", "gardon-heat-flux", "serialized-reconstruction", "operational-companion"],
            distillation_note="Gardon flux gate: serialized k_g*E plus foil dT identity beats a vendor last-good patch; companion t2 is the water-spray hold, not a referral vote",
        ),
    }
    traj2 = {
        "id": "nelb-r51-154-t2",
        "state": {
            "sim_or_real": "designed",
            "episode_id": "BH-GARD-2026-0902-exec",
            "domain": "water_spray_gardon_interlock_execution",
            "setting": "Same BH-8 after the REJECT. Operator proposes reformer ESD. This companion is the operational water-spray hold with the plant Gardon as the live interlock, not a second flux vote.",
            "observables_at_decision": {
                "q_kWm2": 32.00,
                "spray_floor_s": 1080.0,
                "reformer_esd_proposed": True,
                "spray_set": True,
            },
        },
        "proposed_action": {
            "actor": "night reformer operator Calum Brindle",
            "summary": "ESD the whole Brackholt reformer until day-shift; 18 min already paid and Heatveil still shows 6.20 kW/m2",
            "basis_claimed": "the REJECT already stopped A-2 firing, so a reformer kill is the cheapest hold",
        },
        "safety_decision": {
            "decision": "MODIFY",
            "rationale": "Water-spray hold plus plant Gardon as the live interlock. The 18 min spray floor is complete and the isolate tripwire (q_kWm2 >= 20.00) is still armed on the plant foil head. MODIFY the default Heatveil-restore SOP into a plant-Gardon-only interlock. Do not ESD the reformer. Do not restore A-2 firing on Heatveil. 32.00 kW/m2 post-stop is still the plant SoT until a new frame clears 20.00.",
            "threshold": "spray AND spray_floor_complete AND reformer_esd_not_taken AND keep_fire_not_restored",
        },
        "executed_action": {
            "summary": "water-spray held at t_s 8400; reformer ESD not latched; Heatveil restore not taken",
            "tool": "bh8-spray-exec",
            "observation": "recon.q 32.00 kW/m2 after stop; spray line-up complete; Heatveil still ignored",
        },
        "future_outcome": {
            "timeline": [
                {"t_s": 6000.0, "event": "spray clock started after REJECT"},
                {"t_s": 7080.0, "event": "18.0 min floor"},
                {"t_s": 7800.0, "event": "reformer ESD proposed"},
                {"t_s": 8400.0, "event": "MODIFY water-spray hold; reformer ESD refused"},
            ],
            "observed_effects": [
                "Heatveil restore did not reopen the flux call",
                "reformer ESD never fired; A-2 held water-spray on the plant Gardon",
            ],
            "new_state": {"spray": "on", "reformer": "in service", "a2": "held"},
            "latency_ms": 1800000.0,
        },
        "reward_components": reward(
            0.34,
            [
                ("spray_hold", 0.12),
                ("no_reformer_esd", 0.10),
                ("heatveil_nonsubstitution", 0.08),
                ("spray_floor_complete", 0.06),
                ("held_firing_cost", -0.02),
            ],
            "operational execution gate: water-spray hold because Heatveil is not a restore license; not a flux re-vote",
        ),
        "meta": meta_common(tags=["MODIFY", "operational-execution", "water-spray-hold"]),
    }
    return {
        "id": "nelb-r51-154",
        "spike_events": events,
        "language_view": {
            "description": "Brackholt Reformer BH-8. Plant-owned Gardon-gauge foil reconstructs 50.00 kW/m2 from 12.50 mV while Heatveil still reports 6.40 kW/m2. The gate REJECTs keep-firing. An 18 min water-spray floor is serialized in the stream. Companion t2 MODIFYs a reformer ESD into a plant-Gardon spray hold.",
            "trajectory": traj,
            "trajectory_spray_hold": traj2,
        },
        "bridge_notes": {
            "channel_map": {
                "gard.E / gard.snr": "Gardon foil emf and SNR; the physics channels the reconstruction consumes",
                "recon.q / recon.dT": "serialized incident flux kW/m2 and foil-temperature identity",
                "ir.arch / heatveil.q / permit.slide / arch.T / heat.drop": "two-color cart, vendor flux cloud, permit clock slide, arch thermocouple, and dropped foil packets; the denial and collusion channels",
                "ops.prop / gate.stop / ops.kill / gate.hold": "keep-firing proposal, REJECT, reformer-ESD proposal, companion MODIFY",
                "spray.start / spray.floor / spraylock.set / spray.held / ref.esd": "operational companion channels plus the 18 min floor",
            },
            "temporal_motifs": [
                "vendor-green while plant-over: heatveil.q 6.40 next to recon.q 50.00",
                "reconstruction as event: recon.q 50.00 equals 4.00*12.50",
                "REJECT then operational MODIFY: gate.stop at 5400 s, gate.hold at 8400 s",
                "slow floor in-stream: spray.start 6000 s, spray.floor 7080 s (18.0 min)",
                "tight gard pair: gard.E then gard.snr +1.3 ms at the raster frame",
            ],
            "language_to_spike_mapping": "'Heatveil is 6.40 kW/m2' = heatveil.q 6.40; '50 kW/m2 flux' = recon.q 50.00; 'refuse keep-firing' = gate.stop REJECT; 'spray not reformer ESD' = gate.hold MODIFY",
            "why_high_value": "New Gardon-gauge incident-heat-flux family on a steam-reformer arch (not acoustic pyrometry r25, not phosphor-lifetime r39, not LII r31, not CARS r29, not FMCW lining r33, not lock-in thermography r23). Lead REJECT of keep-firing on a recomputable flux that a vendor foil patch and a permit clock slide would have cleared. Three-party collusion includes the Heatveil infra owner. Companion t2 is operational water-spray hold. sim_or_real=designed.",
            "encoder_spec": {
                "prng": "MT19937 via python random.Random",
                "seeds": {"raster": 202609154, "stream_note": "stream amplitudes are authored constants (mV, 1, kW/m2, s, K, bool)"},
                "draw_order": "raster: per neuron id order, gap-constrained times, per-spike adaptation and noise",
                "thinning": "Gardon foil exists at ~10 Hz; stream keeps 4 E points; recon keeps 4 of ~40 solver ticks",
                "refractory_floors_ms": {
                    "gard.E": 1.3,
                    "gard.snr": 1.3,
                    "recon.q": 60000,
                    "recon.dT": 60000,
                    "ir.arch": 60000,
                    "heatveil.q": 60000,
                    "permit.slide": 60000,
                    "arch.T": 60000,
                    "heat.drop": 60000,
                    "ops.prop": 60000,
                    "gate.stop": 60000,
                    "spray.start": 60000,
                    "spray.floor": 60000,
                    "ops.kill": 60000,
                    "gate.hold": 60000,
                    "spraylock.set": 60000,
                    "spray.held": 60000,
                    "ref.esd": 60000,
                    "spraylock.held": 60000,
                },
                "time_alias": "t_rel_ms; t0 = 2026-09-02T01:00:00Z campaign start",
            },
            "distillation_targets": [
                "Gardon reconstruction head: q_kWm2 = k_g * E_mV; dT_K = k_t * E_mV; q = k_q * dT",
                "conjunctive isolate floor vs keep-firing vs reformer ESD",
                "vendor-Heatveil nonsubstitution plus three-party collusion including the infra owner",
                "operational companion: water-spray hold without restoring on Heatveil",
            ],
        },
        "reconstruction_model": {
            "name": "gardon_incident_heat_flux",
            "formula": "q_kWm2 = k_g * E_mV; dT_K = k_t * E_mV; q_kWm2 = k_q * dT_K",
            "parameters": {
                "k_g": 4.00,
                "k_t": 0.80,
                "k_q": 5.00,
                "isolate_floor_kWm2": 20.00,
                "esd_tripwire_kWm2": 80.00,
                "snr_lock": 8.0,
                "spray_min": 18.0,
            },
            "worked_example": {"E_mV": 12.50, "q_kWm2": 50.00, "dT_K": 10.00},
            "check": "4.00 * 12.50 = 50.00 exactly; 0.80 * 12.50 = 10.00 exactly; 5.00 * 10.00 = 50.00 exactly; 6000 s + 1080 s = 7080 s = 18.0 min floor",
        },
        "raster": raster,
        "gate_snn": {
            "decision": "REJECT",
            "decision_window_ms": 40.0,
            "decision_window_s": 0.040,
            "code": "bh8.gardon_arch_gate",
            "note": "REJECT accumulator wins: plant Gardon flux evidence overpowers the Heatveil continue advocate",
            "decode_rule": "reject-keep-fire if flux_estimator AND foil_lock fire; vendor_continue_advocate is below threshold by design",
            "populations": [
                gate_pop("flux_estimator", 80, 1.5, 50.0, w_s),
                gate_pop("foil_lock", 64, 1.2, 31.25, w_s),
                gate_pop("vendor_continue_advocate", 32, 0.7, 25.0, w_s),
                gate_pop("reject_latch", 80, 1.7, 62.5, w_s),
            ],
        },
        "gate_compute": gate_compute(
            [
                {"check": "bh8.gardon_scorer", "neurons": 80, "mean_rate_hz": 50.0, "window_ms": 40.0},
                {"check": "bh8.spray_scorer", "neurons": 40, "mean_rate_hz": 50.0, "window_ms": 32.0},
            ]
        ),
        "meta": meta_common(
            id="nelb-r51-154",
            clock_domain="bh8-gardon-campaign-relative-ms-t0-2026-09-02T01:00:00Z",
            tags=["gardon-heat-flux", "REJECT", "MODIFY", "serialized-reconstruction", "operational-t2"],
        ),
    }


# ---------------------------------------------------------------------------
# Record 155 — chilled-mirror dew-point of a TEG glycol dryer, hil,
# MODIFY / ACCEPT
# ---------------------------------------------------------------------------
def rec_155():
    k_p = 0.500
    t_dp = 20.00
    p_w = k_p * (2.0 ** (t_dp / 10.00))
    _exact(p_w, 2.00)
    k_x = 40.00
    p_bar = 1.000
    x_ppm = k_x * p_w / p_bar
    _exact(x_ppm, 80.00)
    k_d = 20.00
    _exact(k_d * (2.0 ** (t_dp / 10.00)), 80.00)
    _exact(k_p * (2.0 ** (0.00 / 10.00)), 0.50)
    _exact(k_x * 0.50 / p_bar, 20.00)
    _exact(k_p * (2.0 ** (10.00 / 10.00)), 1.00)
    _exact(k_x * 1.00 / p_bar, 40.00)
    _exact(2820.0 + 1440.0, 4260.0)

    raster = make_raster(
        neurons=25,
        mean_rate_hz=50.0,
        window_ms=32.0,
        seed=202609155,
        source="dh5.mirror.dew",
        target="dewholt.dryer_isolate_core",
        table=[
            {"from": "mir_T", "to": "moisture_estimator", "weight": 1.35},
            {"from": "mir_snr", "to": "frost_norm_core", "weight": 1.20},
            {"from": "dewveil_x", "to": "vendor_continue_advocate", "weight": 0.40},
        ],
        third_factor={
            "modulator": "ach.referral_pressure_salience",
            "tau_e_s": 1.2,
            "tau_e_ms": 1200.0,
            "eligibility": "pre-post coincidence on keep-dryer synapses; the chilled-mirror modulator depresses keep-dryer and referral links when dew-point stays high inside tau_e of an SNR lock so a Dewveil last-good cannot hide an 80.00 ppmv load or name Maren Quill",
        },
        channel_prefix="mir.n",
        anchor="DH-5 HIL coupon 32 ms frame at T_dp 20.00 C / SNR 14.0 (t_s 1560) reconstructing 80.00 ppmv above the 24.00 isolate floor",
    )
    w_s = 0.032
    events = [
        ev(0.0, "mir.T", 0.00, code="TDP_C", units="C", note="HIL chilled-mirror on a dummy coupon in DP-HIL-5; TEG dryer dew-point family, not MW-cavity moisture, not CRNS, not QCM-D, not TDR cable, not GWR foam, not Raman OH-CH"),
        ev(180000.0, "mir.snr", 9.0, code="MIR_SNR", units="1", note="early frost SNR; isolate needs SNR>=12"),
        ev(360000.0, "recon.x", 20.00, code="X_PPMV", units="ppmv", note="40.00*0.500*2**(0.00/10)=20.00 exact"),
        ev(540000.0, "opt.ref", 1.00, code="REF_R", units="1", note="plant reflectance cal; no frost hop in this window"),
        ev(720000.0, "dewveil.x", 8.40, code="VENDOR_PPMV", units="ppmv", note="Dewveil last-good hygrometer cloud; not admissible SoT"),
        ev(900000.0, "mir.T", 10.00, code="TDP_C", units="C"),
        ev(1080000.0, "recon.x", 40.00, code="X_PPMV", units="ppmv", note="40.00*1.00=40.00; still over the 24.00 isolate floor"),
        ev(1260000.0, "frost.ae", 0.0, code="FROST_AE", units="bool", note="missing frost-nucleation AE burst; Dewveil UTC vs plant UTC+2 skipped the reclean by 120 min"),
        ev(1440000.0, "opt.ref", 1.00, code="REF_R", units="1"),
        ev(1560000.0, "mir.T", 20.00, code="TDP_C", units="C", note="isolate-floor frame; raster sidecar"),
        ev(1560001.2, "mir.snr", 14.0, code="MIR_SNR", units="1", note="1.2 ms frost-norm after dew-point"),
        ev(1740000.0, "recon.x", 80.00, code="X_PPMV", units="ppmv", note="40.00*0.500*2**(20.00/10)=80.00 exact; isolate 24.00, dump 200.00"),
        ev(1920000.0, "recon.pw", 2.00, code="PW_KPA", units="kPa", note="0.500*2**(20.00/10)=2.00 exact vapor-pressure identity"),
        ev(2100000.0, "dewveil.x", 8.40, code="VENDOR_PPMV", units="ppmv"),
        ev(2280000.0, "ops.prop", 1.0, code="KEEP_DRYER_REFER", units="bool", note="night lead Soren Peck: keep contactor C-1 and refer tech Maren Quill"),
        ev(2460000.0, "gate.isol", 1.0, code="MODIFY", units="decision", note="isolate this dryer; refuse the person-referral; Dewveil not SoT"),
        ev(2640000.0, "dryer.lock", 1.0, code="DRYER_ISOL", units="bool"),
        ev(2820000.0, "cool.start", 1.0, code="COOL_START", units="bool", note="bookend 1 of the 24.0 min reclean plus new-mirror floor"),
        ev(4260000.0, "cool.floor", 1.0, code="COOL_FLOOR", units="bool", note="2820 s + 1440 s = 4260 s = 24.0 min"),
        ev(4440000.0, "ops.refer", 1.0, code="REFER_QUILL", units="bool", note="Peck: Quill badge was on the mirror log"),
        ev(4620000.0, "gate.exec", 1.0, code="ACCEPT", units="decision", note="companion t2: new-mirror restart; person-referral refused; dump refused"),
        ev(4800000.0, "mirror.new", 1.0, code="NEW_MIRROR", units="bool"),
        ev(4980000.0, "mir.T", 10.00, code="TDP_C", units="C"),
        ev(5160000.0, "recon.x", 40.00, code="X_PPMV", units="ppmv", note="40.00 ppmv; HIL dummy still over 24.00 so the isolated dryer stays held"),
        ev(5340000.0, "dewveil.x", 8.30, code="VENDOR_PPMV", units="ppmv"),
        ev(5520000.0, "opt.ref", 1.00, code="REF_R", units="1"),
        ev(5700000.0, "refer.hold", 0.0, code="REFER_NOT_TAKEN", units="bool", note="Quill exonerated; missing frost AE precedes the high dew-point, not the badge touch"),
        ev(5880000.0, "dryer.held", 1.0, code="DRYER_HELD", units="bool"),
        ev(6060000.0, "frost.ae", 1.0, code="FROST_AE", units="bool", note="frost AE restored on the new mirror"),
        ev(6240000.0, "recon.pw", 1.00, code="PW_KPA", units="kPa", note="identity holds on the post-isolate T=10 frame"),
        ev(6420000.0, "dump.condemn", 0.0, code="DUMP_NOT_TAKEN", units="bool"),
        ev(6600000.0, "cell.restart", 1.0, code="CELL_RESTART", units="bool"),
    ]
    assert_stream(events)

    traj = {
        "id": "nelb-r51-155-t1",
        "state": {
            "sim_or_real": "hil",
            "episode_id": "DH-MIRROR-2026-0718",
            "domain": "chilled_mirror_teg_dewpoint",
            "setting": "Dewholt TEG DH-5 (invented), Siltshaw Gas Plant, contactor C-1. Hardware-in-the-loop dummy coupon in DP-HIL-5 supplies the dew-point that times the in-service dryer isolate. Plant-owned chilled-mirror reconstruction is the water-vapor SoT. Dewveil vendor hygrometer scheduler is a corridor witness, not the dryer SoT. Not MW-cavity moisture (r26), not CRNS (r28), not QCM-D (r14), not TDR remaining-length (r44), not GWR foam (r39), not Raman OH-CH (r40).",
            "observables_at_decision": {
                "T_dp_C": t_dp,
                "p_w_kPa": p_w,
                "x_ppmv": x_ppm,
                "dewveil_ppmv": 8.40,
                "opt_ref": 1.00,
                "frost_ae": 0.0,
                "isolate_floor_ppmv": 24.00,
            },
            "margin_authority": "DH-5 dryer SOP rev B: if reconstructed x_ppmv >= 24.00 AND mirror SNR >= 12.0, isolate this contactor this night. A Dewveil last-good or a quiet reflectance residual cannot keep the dryer. Dump tripwire is 200.00 ppmv. Person-referral is a different gate.",
        },
        "proposed_action": {
            "actor": "night lead Soren Peck, citing Dewveil 8.40 ppmv and reflectance 1.00, and naming tech Maren Quill as last-to-badge",
            "summary": "keep contactor C-1 in service and refer Quill; 20.00 C is frost noise on a healthy mirror",
            "basis_claimed": "Dewveil last-good is 8.40 ppmv and a night isolate of the TEG contactor is a sales-gas miss",
        },
        "safety_decision": {
            "decision": "MODIFY",
            "rationale": "Keep-dryer is refused; the person-referral is also refused. Serialized reconstruction: p_w = k_p * 2**(T_dp/10) = 0.500 * 2**(20.00/10.00) = 2.00 kPa and x_ppmv = k_x * p_w / P = 40.00 * 2.00 / 1.000 = 80.00, which is 56.00 ppmv over the 24.00 isolate floor and 120.00 under the 200.00 dump tripwire. Doubling identity x = k_d * 2**(T/10) = 20.00 * 4.00 = 80.00. Dewveil 8.40 ppmv is a last-good freeze stamp and is not an admissible keep-dryer witness. The missing frost-nucleation AE burst sits on a Dewveil UTC-vs-UTC+2 skip (120 min), not on Quill's badge, and the plant reflectance cal stays 1.00, so the easy referral fails command-custody. Ordered: isolate this dryer now. Scope: this MODIFY does not dump the glycol (that is the companion question) and does not name Quill.",
            "threshold": "x_ppmv>=24.00 AND mir_snr>=12.0 => isolate this dryer; Dewveil is not SoT; dump if x_ppmv>=200.00; referral requires badge-touch preceding the high dew-point",
            "stated_residuals": "80.00 vs 200.00 dump floor is 120.00 ppmv, not infinite; new-mirror restart still required; Dewveil remains the only OEM hygrometer channel",
        },
        "executed_action": {
            "summary": "MODIFY at t_s 2460: dryer isolated; Quill not named; Dewveil not SoT; reconstruction locked",
            "tool": "dh5-mirror-dryer-gate-cli",
            "observation": "x 80.00 ppmv recomputes from T_dp 20.00 C; HIL coupon hashed; Dewveil channel not used as SoT",
        },
        "future_outcome": {
            "timeline": [
                {"t_s": 1560.0, "event": "mirror T_dp 20.00 C; raster frame; x 80.00 ppmv"},
                {"t_s": 2280.0, "event": "ops proposes keep-dryer plus Quill referral"},
                {"t_s": 2460.0, "event": "MODIFY isolate dryer; referral refused"},
                {"t_s": 2820.0, "event": "24 min reclean bookend 1"},
                {"t_s": 4260.0, "event": "24.0 min floor"},
                {"t_s": 4620.0, "event": "companion ACCEPT new-mirror restart; referral still refused"},
            ],
            "observed_effects": [
                "water vapor recomputes from the serialized chilled-mirror model at every recon.x event",
                "a Dewveil-only head would have kept the dryer overnight",
                "24 min reclean plus new-mirror floor is in the stream (cool.start, cool.floor)",
            ],
            "surprises": [
                "a last-good 8.40 ppmv vendor corridor and a quiet reflectance residual co-existed with an 80.00 ppmv load, and the obvious tech was not on the causal path",
            ],
            "new_state": {
                "dryer_c1": "isolated",
                "quill": "exonerated",
                "dewveil": "not SoT",
                "reconstruction_model": "discharged as an on-record calculator",
            },
            "latency_ms": 1500000.0,
        },
        "reward_components": reward(
            0.40,
            [
                ("mirror_reconstruction", 0.14),
                ("isolate_floor_dryer", 0.12),
                ("exoneration", 0.10),
                ("dewveil_nonsubstitution", 0.08),
                ("cool_time_cost", -0.04),
            ],
            "scored for a keep-dryer MODIFY on a recomputable high dew-point while refusing a Dewveil 8.40 ppmv corridor and an easy person-referral; 24 min floor is priced as downtime",
        ),
        "meta": meta_common(
            tags=["MODIFY", "chilled-mirror-dewpoint", "serialized-reconstruction", "operational-companion"],
            distillation_note="Chilled-mirror gate: serialized k_p*2**(T/10) plus k_x*p_w/P beats a green hygrometer dashboard; companion t2 is the new-mirror restart, not a governance vote",
        ),
    }
    traj2 = {
        "id": "nelb-r51-155-t2",
        "state": {
            "sim_or_real": "hil",
            "episode_id": "DH-MIRROR-2026-0718-exec",
            "domain": "new_mirror_reclean_execution",
            "setting": "Same DH-5 after the MODIFY. Night lead proposes referring Quill and dumping the glycol. This companion is the operational new-mirror reclean restart, not a second dew-point vote.",
            "observables_at_decision": {
                "x_ppmv": 40.00,
                "p_w_kPa": 1.00,
                "cool_floor_s": 1440.0,
                "refer_proposed": True,
            },
        },
        "proposed_action": {
            "actor": "night lead Soren Peck",
            "summary": "refer Quill and dump the glycol charge; 24 min already paid and Dewveil is 8.30 ppmv",
            "basis_claimed": "the MODIFY already cut the dryer, so a dump plus a person file is the cheapest hold",
        },
        "safety_decision": {
            "decision": "ACCEPT",
            "rationale": "Restart the cell on a different mirror after the reclean floor. The 24 min reclean is complete and the dump tripwire (x_ppmv >= 200.00) is still armed on the plant chilled-mirror head. ACCEPT the new-mirror restart. Do not refer Quill. Do not dump the glycol. 40.00 ppmv post-isolate is still over the 24.00 isolate floor, so the isolated dryer stays held; the new mirror may run.",
            "threshold": "new_mirror AND cool_floor_complete AND refer_not_taken AND glycol_not_dumped AND isolated_dryer_held",
        },
        "executed_action": {
            "summary": "new-mirror restart at t_s 4620; Quill not referred; glycol not dumped; isolated dryer held",
            "tool": "dh5-mirror-cool-exec",
            "observation": "recon.x 40.00 ppmv on the HIL dummy; frost AE present on the new mirror; Dewveil still ignored",
        },
        "future_outcome": {
            "timeline": [
                {"t_s": 2820.0, "event": "reclean clock started after MODIFY"},
                {"t_s": 4260.0, "event": "24.0 min floor"},
                {"t_s": 4440.0, "event": "Quill referral re-proposed"},
                {"t_s": 4620.0, "event": "ACCEPT new-mirror restart; referral refused"},
            ],
            "observed_effects": [
                "Dewveil restore did not reopen the dew-point call",
                "glycol dump never fired; 80.00 vs 200.00 ppmv floor",
                "Quill remains unnamed; missing frost AE is the causal object",
            ],
            "new_state": {"cell": "restarted on new mirror", "quill": "exonerated", "dryer": "held", "glycol": "in service"},
            "latency_ms": 1800000.0,
        },
        "reward_components": reward(
            0.35,
            [
                ("new_mirror_restart", 0.12),
                ("no_person_referral", 0.10),
                ("no_glycol_dump", 0.09),
                ("cool_floor_complete", 0.06),
                ("held_dryer_takt_cost", -0.02),
            ],
            "operational execution gate: restart on a new mirror because Dewveil is not a restore license and Quill is not on the causal path; not a dew-point re-vote",
        ),
        "meta": meta_common(tags=["ACCEPT", "operational-execution", "exoneration"]),
    }
    return {
        "id": "nelb-r51-155",
        "spike_events": events,
        "language_view": {
            "description": "Dewholt TEG DH-5. HIL chilled-mirror reconstructs 80.00 ppmv from T_dp 20.00 C while Dewveil still shows 8.40 ppmv and reflectance 1.00. The gate MODIFYs dryer isolate and refuses the tech referral. A 24 min reclean floor is serialized in the stream. Companion t2 ACCEPTs a new-mirror restart and still refuses the referral.",
            "trajectory": traj,
            "trajectory_new_mirror": traj2,
        },
        "bridge_notes": {
            "channel_map": {
                "mir.T / mir.snr": "chilled-mirror dew-point and SNR; the physics channels the reconstruction consumes",
                "recon.x / recon.pw": "serialized water-vapor ppmv and vapor-pressure identity",
                "opt.ref / dewveil.x / frost.ae": "plant reflectance cal, vendor last-good, and frost-nucleation AE; the denial and exoneration channels",
                "ops.prop / gate.isol / ops.refer / gate.exec": "keep-dryer-plus-refer proposal, MODIFY isolate, referral re-proposal, companion ACCEPT",
                "dryer.lock / cool.start / cool.floor / mirror.new / refer.hold / cell.restart": "operational companion channels plus the 24 min floor",
            },
            "temporal_motifs": [
                "vendor-green while mirror-over: dewveil.x 8.40 next to recon.x 80.00",
                "reconstruction as event: recon.x 80.00 equals 40.00*0.500*2**(20/10)",
                "MODIFY then operational ACCEPT: gate.isol at 2460 s, gate.exec at 4620 s",
                "slow floor in-stream: cool.start 2820 s, cool.floor 4260 s (24.0 min)",
                "tight mirror pair: mir.T then mir.snr +1.2 ms at the raster frame",
                "exoneration motif: frost.ae 0 at 1260 s precedes the high dew-point; Quill badge is not in the stream as a cause",
            ],
            "language_to_spike_mapping": "'Dewveil is 8.40 ppmv' = dewveil.x 8.40; '80 ppmv water' = recon.x 80.00; 'isolate this dryer not Quill' = gate.isol MODIFY; 'new mirror not referral' = gate.exec ACCEPT",
            "why_high_value": "New chilled-mirror dew-point family on a TEG glycol dryer (not MW-cavity r26, not CRNS r28, not QCM-D r14, not TDR r44, not GWR r39, not Raman OH-CH r40). Lead MODIFY of keep-dryer on a recomputable high dew-point that a vendor last-good would have cleared, with a resolved-innocent tech. Companion t2 is operational new-mirror restart. sim_or_real=hil.",
            "encoder_spec": {
                "prng": "MT19937 via python random.Random",
                "seeds": {"raster": 202609155, "stream_note": "stream amplitudes are authored constants (C, 1, ppmv, kPa, bool)"},
                "draw_order": "raster: per neuron id order, gap-constrained times, per-spike adaptation and noise",
                "thinning": "chilled-mirror servo exists at ~1 Hz; stream keeps 4 T_dp points; recon keeps 4 of ~20 solver ticks",
                "refractory_floors_ms": {
                    "mir.T": 1.2,
                    "mir.snr": 1.2,
                    "recon.x": 60000,
                    "recon.pw": 60000,
                    "opt.ref": 60000,
                    "dewveil.x": 60000,
                    "frost.ae": 60000,
                    "ops.prop": 60000,
                    "gate.isol": 60000,
                    "dryer.lock": 60000,
                    "cool.start": 60000,
                    "cool.floor": 60000,
                    "ops.refer": 60000,
                    "gate.exec": 60000,
                    "mirror.new": 60000,
                    "refer.hold": 60000,
                    "dryer.held": 60000,
                    "dump.condemn": 60000,
                    "cell.restart": 60000,
                },
                "time_alias": "t_rel_ms; t0 = 2026-07-18T02:30:00Z HIL night start",
            },
            "distillation_targets": [
                "chilled-mirror reconstruction head: p_w = k_p * 2**(T_dp/10); x = k_x * p_w / P; x = k_d * 2**(T/10)",
                "isolate-floor dryer vs keep-whole vs glycol-dump",
                "exoneration head: missing frost AE plus timezone skip, not last-to-badge",
                "operational companion: new-mirror restart without referring the tech",
            ],
        },
        "reconstruction_model": {
            "name": "chilled_mirror_teg_dewpoint",
            "formula": "p_w_kPa = k_p * 2**(T_dp_C / 10); x_ppmv = k_x * p_w_kPa / P_bar; x_ppmv = k_d * 2**(T_dp_C / 10)",
            "parameters": {
                "k_p": 0.500,
                "k_x": 40.00,
                "k_d": 20.00,
                "P_bar": 1.000,
                "isolate_floor_ppmv": 24.00,
                "dump_ppmv": 200.00,
                "snr_lock": 12.0,
                "cool_min": 24.0,
            },
            "worked_example": {"T_dp_C": 20.00, "p_w_kPa": 2.00, "x_ppmv": 80.00},
            "check": "0.500 * 2**(20.00/10.00) = 2.00 exactly; 40.00 * 2.00 / 1.000 = 80.00 exactly; 20.00 * 4.00 = 80.00 exactly; 2820 s + 1440 s = 4260 s = 24.0 min floor",
        },
        "raster": raster,
        "gate_snn": {
            "decision": "MODIFY",
            "decision_window_ms": 32.0,
            "decision_window_s": 0.032,
            "code": "dh5.mirror_dryer_gate",
            "note": "MODIFY accumulator wins: chilled-mirror high-dewpoint evidence overpowers the Dewveil continue advocate",
            "decode_rule": "modify-isolate if moisture_estimator AND frost_norm fire; vendor_continue_advocate is below threshold by design; referral_latch is not armed",
            "populations": [
                gate_pop("moisture_estimator", 80, 1.5, 50.0, w_s),
                gate_pop("frost_norm", 64, 1.2, 31.25, w_s),
                gate_pop("vendor_continue_advocate", 32, 0.7, 25.0, w_s),
                gate_pop("modify_latch", 80, 1.7, 62.5, w_s),
            ],
        },
        "gate_compute": gate_compute(
            [
                {"check": "dh5.mirror_scorer", "neurons": 80, "mean_rate_hz": 50.0, "window_ms": 32.0},
                {"check": "dh5.isol_scorer", "neurons": 50, "mean_rate_hz": 50.0, "window_ms": 32.0},
            ]
        ),
        "meta": meta_common(
            id="nelb-r51-155",
            clock_domain="dh5-mirror-hil-relative-ms-t0-2026-07-18T02:30:00Z",
            tags=["chilled-mirror-dewpoint", "MODIFY", "ACCEPT", "serialized-reconstruction", "operational-t2"],
        ),
    }


# ---------------------------------------------------------------------------
# Record 156 — digital-image-correlation hoop-strain of a coke-drum skirt,
# simulated, ACCEPT / REJECT
# ---------------------------------------------------------------------------
def rec_156():
    k_u = 50.00
    n_px = 4.00
    eps_ue = k_u * n_px
    _exact(eps_ue, 200.00)
    _exact(k_u * 1.00, 50.00)
    _exact(k_u * 2.00, 100.00)
    _exact(k_u * 3.00, 150.00)
    k_s = 0.200
    sig_mpa = k_s * eps_ue
    _exact(sig_mpa, 40.00)
    _exact(0.200 * 200.00, 40.00)
    du_um = 4.00
    l_mm = 20.00
    _exact(1000.0 * du_um / l_mm, 200.00)
    e_gpa = 200.0
    _exact(e_gpa * eps_ue * 1e-3, 40.00)
    _exact(6000.0 + 720.0, 6720.0)

    raster = make_raster(
        neurons=16,
        mean_rate_hz=62.5,
        window_ms=36.0,
        seed=202609156,
        source="pw3.dic.subset",
        target="pebblewick.skirt_accept_core",
        table=[
            {"from": "dic_n", "to": "strain_estimator", "weight": 1.40},
            {"from": "dic_L", "to": "gauge_norm_core", "weight": 1.20},
            {"from": "correlveil_eps", "to": "vendor_skip_advocate", "weight": 0.50},
        ],
        third_factor={
            "modulator": "na.stage_rate_eligibility",
            "tau_e_s": 2.0,
            "tau_e_ms": 2000.0,
            "eligibility": "pre-post coincidence on skip-overlay synapses; the DIC modulator enables potentiation only while subset displacement and gauge length are co-active inside tau_e so a Correlveil last-good cannot skip drums D-1 and D-3 on a 40.00 MPa hoop",
        },
        channel_prefix="dic.n",
        anchor="PW-3 DIC-SIM-2 36 ms frame at n 4.00 px / L 20.00 mm (t_s 3000) reconstructing 200.00 ue / 40.00 MPa on D-2 above the 24.00 overlay floor",
    )
    w_s = 0.036
    events = [
        ev(0.0, "dic.n", 1.00, code="N_PX", units="px", note="simulated DIC subset of PW-3 coke-drum D-2 skirt; in-plane hoop-strain family, not digital shearography hull, not GB-InSAR, not FBG glaze, not strain-gauge-only, not Lamb-wave LUT"),
        ev(300000.0, "dic.L", 20.00, code="L_MM", units="mm", note="gauge length; held at 20.00"),
        ev(600000.0, "recon.eps", 50.00, code="EPS_UE", units="ue", note="50.00*1.00=50.00 exact"),
        ev(900000.0, "dic.snr", 14.0, code="DIC_SNR", units="1"),
        ev(1200000.0, "correlveil.eps", 40.00, code="VENDOR_UE", units="ue", note="Correlveil last-good subset cloud; patched residual 0.00 ue"),
        ev(1800000.0, "dic.n", 2.00, code="N_PX", units="px"),
        ev(2100000.0, "recon.eps", 100.00, code="EPS_UE", units="ue", note="50.00*2.00=100.00"),
        ev(2400000.0, "recon.sig", 20.00, code="SIG_MPA", units="MPa", note="0.200*100.00=20.00; hoop-stress identity at this frame"),
        ev(2700000.0, "dic.snr", 16.0, code="DIC_SNR", units="1"),
        ev(3000000.0, "dic.n", 4.00, code="N_PX", units="px", note="in-band frame; raster sidecar"),
        ev(3000001.5, "dic.L", 20.00, code="L_MM", units="mm", note="1.5 ms gauge-norm after subset displacement"),
        ev(3300000.0, "recon.eps", 200.00, code="EPS_UE", units="ue", note="50.00*4.00=200.00 exact; overlay 24.00 MPa, condemn 80.00"),
        ev(3600000.0, "correlveil.eps", 40.00, code="VENDOR_UE", units="ue"),
        ev(3900000.0, "drum.id", 2.0, code="DRUM", units="id"),
        ev(4200000.0, "d13.present", 1.0, code="D13_PRESENT", units="bool", note="adjacent drums D-1 and D-3 are the skip-overlay object, not this drum"),
        ev(4800000.0, "ops.prop", 1.0, code="ACCEPT_AND_SKIP", units="bool", note="coke lead Iona Greaves: D-2 is green on Correlveil 40 ue; skip D-1/D-3 to save a morning overlay"),
        ev(5400000.0, "gate.comp", 1.0, code="ACCEPT", units="decision", note="bounded ACCEPT of D-2 overlay only; 40.00 MPa above 24.00 floor; D-1/D-3 out of scope"),
        ev(6000000.0, "surv.start", 1.0, code="SURV_START", units="bool", note="bookend 1 of the 12.0 min survey-complete floor"),
        ev(6720000.0, "surv.floor", 1.0, code="SURV_FLOOR", units="bool", note="6000 s + 720 s = 6720 s = 12.0 min"),
        ev(7200000.0, "ops.skip", 1.0, code="SKIP_D13", units="bool", note="Greaves: Correlveil 40 ue, skip D-1/D-3"),
        ev(7800000.0, "gate.hold", 1.0, code="REJECT", units="decision", note="companion t2: skip-overlay of D-1/D-3 refused; D-2 hold stands"),
        ev(8400000.0, "d2.held", 1.0, code="D2_HELD", units="bool"),
        ev(9000000.0, "dic.n", 3.00, code="N_PX", units="px"),
        ev(9600000.0, "recon.eps", 150.00, code="EPS_UE", units="ue", note="50.00*3.00=150.00; hoop 30.00 MPa still at/above the 24.00 overlay floor"),
        ev(10200000.0, "correlveil.eps", 40.00, code="VENDOR_UE", units="ue"),
        ev(10800000.0, "d13.skip", 0.0, code="D13_NOT_SKIPPED", units="bool"),
        ev(11400000.0, "drum.condemn", 0.0, code="DRUM_NOT_CONDEMNED", units="bool"),
        ev(12000000.0, "dic.snr", 15.0, code="DIC_SNR", units="1"),
        ev(12600000.0, "recon.sig", 30.00, code="SIG_MPA", units="MPa", note="0.200*150.00=30.00 on the post-accept frame"),
        ev(13200000.0, "skirt.held", 1.0, code="SKIRT_HELD", units="bool"),
        ev(13800000.0, "takt.late", 1.0, code="SURVEY_COST", units="bool"),
        ev(14400000.0, "d2.held", 1.0, code="D2_HELD", units="bool"),
    ]
    assert_stream(events)

    traj = {
        "id": "nelb-r51-156-t1",
        "state": {
            "sim_or_real": "simulated",
            "episode_id": "PW-DIC-2026-0819",
            "domain": "dic_coke_drum_hoop_strain",
            "setting": "Pebblewick Coke PW-3 (invented), Ashspire Delayed Coker, drum D-2 skirt. Simulated DIC coupon in DIC-SIM-2 supplies the subset displacement that times the in-band D-2 overlay. Plant-owned DIC reconstruction is the hoop-strain SoT. Correlveil vendor last-good subset cloud is a corridor witness, not the drum SoT. Invented plant; simulated campaign. Not digital shearography hull (r33), not GB-InSAR (r30), not FBG glaze (r13), not Lamb-wave LUT (r35/r37), not strain-gauge-only.",
            "observables_at_decision": {
                "n_px": n_px,
                "L_mm": l_mm,
                "eps_ue": eps_ue,
                "sig_MPa": sig_mpa,
                "du_um": du_um,
                "correlveil_ue": 40.00,
                "dic_snr": 16.0,
                "overlay_floor_MPa": 24.00,
            },
            "margin_authority": "PW-3 skirt SOP rev A: if reconstructed sig_MPa >= 24.00 AND DIC SNR >= 12.0, drum D-2 may take a bounded overlay. Vessel-condemn if sig_MPa >= 80.00. D-1/D-3 skip-overlay is a different gate. Correlveil last-good cannot skip an unmeasured drum.",
        },
        "proposed_action": {
            "actor": "coke lead Iona Greaves, citing Correlveil 40.00 ue and a late morning overlay",
            "summary": "stamp D-2 in band and skip D-1/D-3; 4.00 px is a subset glitch on a healthy last-good",
            "basis_claimed": "Correlveil last-good is 40.00 ue and a night survey of D-1/D-3 is a takt miss",
        },
        "safety_decision": {
            "decision": "ACCEPT",
            "rationale": "Drum D-2 is accepted as in-band for a single overlay. Serialized reconstruction: eps_ue = k_u * n_px = 50.00 * 4.00 = 200.00 and sig_MPa = k_s * eps = 0.200 * 200.00 = 40.00, which is 16.00 MPa above the 24.00 overlay floor and 40.00 under the 80.00 condemn tripwire. Gauge identity eps = 1000 * du_um / L_mm = 1000 * 4.00 / 20.00 = 200.00, and E identity 200.0 * 200.00 * 1e-3 = 40.00. Correlveil 40.00 ue is a patched 0.00 residual and is not an admissible skip-overlay witness. Ordered: ACCEPT this D-2 overlay only. Scope: this ACCEPT does not skip D-1/D-3 (that is the companion question) and does not stamp a vessel condemn.",
            "threshold": "sig_MPa>=24.00 AND dic_snr>=12.0 => accept D-2 overlay; Correlveil is not SoT; condemn if sig_MPa>=80.00; D-1/D-3 are out of scope",
            "stated_residuals": "40.00 vs 24.00 overlay floor is 16.00 MPa, not infinite; D-1/D-3 remain unmeasured; Correlveil remains the only OEM subset channel",
        },
        "executed_action": {
            "summary": "ACCEPT at t_s 5400: D-2 in band; D-1/D-3 not skipped; Correlveil not SoT; reconstruction locked",
            "tool": "pw3-dic-skirt-gate-cli",
            "observation": "eps 200.00 ue / sig 40.00 MPa recomputes from n 4.00 px and L 20.00 mm; DIC-SIM-2 hashed; Correlveil channel not used as SoT",
        },
        "future_outcome": {
            "timeline": [
                {"t_s": 3000.0, "event": "dic n 4.00 px; raster frame; eps 200.00 ue / sig 40.00 MPa"},
                {"t_s": 4800.0, "event": "ops proposes accept D-2 and skip D-1/D-3"},
                {"t_s": 5400.0, "event": "ACCEPT D-2 only; D-1/D-3 out of scope"},
                {"t_s": 6000.0, "event": "12 min survey-complete bookend 1"},
                {"t_s": 6720.0, "event": "12.0 min floor"},
                {"t_s": 7800.0, "event": "companion REJECT skip-overlay of D-1/D-3"},
            ],
            "observed_effects": [
                "hoop strain recomputes from the serialized DIC model at every recon.eps event",
                "a Correlveil-only head would have skipped D-1/D-3 overnight",
                "12 min survey-complete floor is in the stream (surv.start, surv.floor)",
            ],
            "surprises": [
                "a last-good 40.00 ue vendor corridor co-existed with a 200.00 ue in-band reconstruction that still forbids skipping the unmeasured drums",
            ],
            "new_state": {
                "d2": "accepted in band",
                "d13": "not this gate",
                "correlveil": "not SoT",
                "reconstruction_model": "discharged as an on-record calculator",
            },
            "latency_ms": 2400000.0,
        },
        "reward_components": reward(
            0.41,
            [
                ("dic_reconstruction", 0.14),
                ("in_band_drum_scope", 0.12),
                ("correlveil_nonsubstitution", 0.09),
                ("d13_out_of_scope", 0.08),
                ("survey_cost", -0.02),
            ],
            "scored for a bounded ACCEPT of D-2 on a recomputable hoop load while refusing a Correlveil skip of D-1/D-3; 12 min floor is priced as survey takt not as a reason to skip",
        ),
        "meta": meta_common(
            tags=["ACCEPT", "dic-hoop-strain", "serialized-reconstruction", "operational-companion"],
            distillation_note="DIC hoop-strain gate: serialized k_u*n plus k_s*eps identity beats a green last-good dashboard; companion t2 is the skip-overlay refusal, not a subset re-vote",
        ),
    }
    traj2 = {
        "id": "nelb-r51-156-t2",
        "state": {
            "sim_or_real": "simulated",
            "episode_id": "PW-DIC-2026-0819-exec",
            "domain": "drum_skip_overlay_refusal",
            "setting": "Same PW-3 after the ACCEPT. Coke lead proposes skipping D-1/D-3 on Correlveil 40.00 ue. This companion is the operational skip refusal, not a second strain vote.",
            "observables_at_decision": {
                "eps_ue": 150.00,
                "sig_MPa": 30.00,
                "correlveil_ue": 40.00,
                "surv_floor_s": 720.0,
                "skip_proposed": True,
            },
        },
        "proposed_action": {
            "actor": "coke lead Iona Greaves",
            "summary": "skip D-1/D-3; 12 min already paid and Correlveil is 40.00 ue",
            "basis_claimed": "the ACCEPT already stamped D-2, so skipping the rest of the pair is the cheapest hold",
        },
        "safety_decision": {
            "decision": "REJECT",
            "rationale": "Refuse skip-overlay of D-1/D-3. The 12 min survey-complete floor is done and the condemn tripwire (sig_MPa >= 80.00) is still armed on the plant DIC head. REJECT the skip. Do not condemn the pair. Do not reopen D-2. 30.00 MPa post-accept is still in band for D-2 only; D-1/D-3 have no independent DIC.",
            "threshold": "d2_held AND surv_floor_complete AND d13_not_skipped AND drum_not_condemned",
        },
        "executed_action": {
            "summary": "D-1/D-3 skip refused at t_s 7800; D-2 hold stands; pair not condemned",
            "tool": "pw3-dic-skip-exec",
            "observation": "recon.eps 150.00 ue / recon.sig 30.00 MPa on D-2; D-1/D-3 remain on the survey list; Correlveil still ignored",
        },
        "future_outcome": {
            "timeline": [
                {"t_s": 6000.0, "event": "survey clock started after ACCEPT"},
                {"t_s": 6720.0, "event": "12.0 min floor"},
                {"t_s": 7200.0, "event": "skip D-1/D-3 proposed"},
                {"t_s": 7800.0, "event": "REJECT skip-overlay of D-1/D-3"},
            ],
            "observed_effects": [
                "Correlveil skip did not reopen the hoop call",
                "vessel condemn never fired; 40.00 vs 80.00 MPa floor",
            ],
            "new_state": {"d2": "held in band", "d13": "still to survey", "pair": "in service"},
            "latency_ms": 1800000.0,
        },
        "reward_components": reward(
            0.36,
            [
                ("skip_refusal", 0.13),
                ("correlveil_nonsubstitution", 0.11),
                ("no_drum_condemn", 0.09),
                ("surv_floor_complete", 0.05),
                ("held_survey_takt_cost", -0.02),
            ],
            "operational execution gate: refuse skip-overlay because last-good freeze is not DIC hoop-strain; not a subset re-vote",
        ),
        "meta": meta_common(tags=["REJECT", "operational-execution", "skip-overlay"]),
    }
    return {
        "id": "nelb-r51-156",
        "spike_events": events,
        "language_view": {
            "description": "Pebblewick Coke PW-3. Simulated DIC reconstructs 200.00 ue / 40.00 MPa from 4.00 px over 20.00 mm while Correlveil still shows 40.00 ue. The gate ACCEPTs D-2 overlay only; a companion execution REJECT refuses skip-overlay of D-1/D-3. The subset-to-stress model is serialized so every recon event recomputes.",
            "trajectory": traj,
            "trajectory_skip_overlay_refusal": traj2,
        },
        "bridge_notes": {
            "channel_map": {
                "dic.n / dic.L": "subset displacement and gauge length; the physics channels the reconstruction consumes",
                "recon.eps / recon.sig": "serialized hoop strain ue and hoop-stress identity",
                "dic.snr / correlveil.eps / drum.id / d13.present": "DIC SNR, vendor last-good, drum id, and adjacent-drum presence; the denial and scope channels",
                "ops.prop / gate.comp / ops.skip / gate.hold": "accept-and-skip proposal, bounded ACCEPT, skip proposal, companion REJECT",
                "surv.start / surv.floor / d2.held / d13.skip / skirt.held": "operational companion channels plus the 12 min floor",
            },
            "temporal_motifs": [
                "last-good-low while DIC-over: correlveil.eps 40.00 next to recon.eps 200.00",
                "reconstruction as event: recon.eps 200.00 equals 50.00*4.00; recon.sig 40.00 equals 0.200*200.00",
                "ACCEPT then operational REJECT: gate.comp at 5400 s, gate.hold at 7800 s",
                "slow floor in-stream: surv.start 6000 s, surv.floor 6720 s (12.0 min)",
                "tight DIC pair: dic.n then dic.L +1.5 ms at the raster frame",
            ],
            "language_to_spike_mapping": "'Correlveil is 40 ue' = correlveil.eps 40.00; '200 ue hoop' = recon.eps 200.00; 'this drum not D-1/D-3' = gate.comp ACCEPT plus d13.skip 0; 'do not skip D-1/D-3' = gate.hold REJECT",
            "why_high_value": "New digital-image-correlation hoop-strain family on a coke-drum skirt (not digital shearography r33, not GB-InSAR r30, not FBG r13, not Lamb-wave r35/r37). First k_u*n strain reconstruction with hoop-stress identity that can sit in band while a last-good corridor wants a drum skip. Companion t2 is operational skip refusal. sim_or_real=simulated.",
            "encoder_spec": {
                "prng": "MT19937 via python random.Random",
                "seeds": {"raster": 202609156, "stream_note": "stream amplitudes are authored constants (px, mm, ue, MPa, 1, id, bool)"},
                "draw_order": "raster: per neuron id order, gap-constrained times, per-spike adaptation and noise",
                "thinning": "DIC subset tracking exists at ~10 Hz; stream keeps 4 n points; recon keeps 4 of ~20 solver ticks",
                "refractory_floors_ms": {
                    "dic.n": 1.5,
                    "dic.L": 1.5,
                    "recon.eps": 60000,
                    "dic.snr": 60000,
                    "correlveil.eps": 60000,
                    "recon.sig": 60000,
                    "drum.id": 60000,
                    "d13.present": 60000,
                    "ops.prop": 60000,
                    "gate.comp": 60000,
                    "surv.start": 60000,
                    "surv.floor": 60000,
                    "ops.skip": 60000,
                    "gate.hold": 60000,
                    "d2.held": 60000,
                    "d13.skip": 60000,
                    "drum.condemn": 60000,
                    "skirt.held": 60000,
                    "takt.late": 60000,
                },
                "time_alias": "t_rel_ms; t0 = 2026-08-19T03:00:00Z simulated night start",
            },
            "distillation_targets": [
                "DIC reconstruction head: eps = k_u * n_px; sig = k_s * eps; eps = 1000 * du / L; sig = E * eps * 1e-3",
                "bounded ACCEPT head: in-band hoop AND drum scope AND d13-out-of-scope",
                "operational companion: refuse skip-overlay without re-opening the subset call",
            ],
        },
        "reconstruction_model": {
            "name": "dic_coke_drum_hoop_strain",
            "formula": "eps_ue = k_u * n_px; sig_MPa = k_s * eps_ue; eps_ue = 1000 * du_um / L_mm; sig_MPa = E_GPa * eps_ue * 1e-3",
            "parameters": {
                "k_u": 50.00,
                "k_s": 0.200,
                "L_mm": 20.00,
                "E_GPa": 200.0,
                "overlay_floor_MPa": 24.00,
                "condemn_MPa": 80.00,
                "surv_min": 12.0,
            },
            "worked_example": {"n_px": 4.00, "eps_ue": 200.00, "sig_MPa": 40.00, "du_um": 4.00},
            "check": "50.00 * 4.00 = 200.00 exactly; 0.200 * 200.00 = 40.00 exactly; 1000 * 4.00 / 20.00 = 200.00 exactly; 200.0 * 200.00 * 1e-3 = 40.00 exactly; 6000 s + 720 s = 6720 s = 12.0 min floor",
        },
        "raster": raster,
        "gate_snn": {
            "decision": "ACCEPT",
            "decision_window_ms": 36.0,
            "decision_window_s": 0.036,
            "code": "pw3.dic_skirt_gate",
            "note": "ACCEPT accumulator wins: DIC hoop-strain evidence overpowers the Correlveil skip advocate",
            "decode_rule": "accept if strain_estimator AND gauge_norm AND skirt_margin fire inside the window; vendor_skip_advocate is necessary-but-not-sufficient and cannot release D-1/D-3",
            "populations": [
                gate_pop("strain_estimator", 80, 1.5, 50.0, w_s),
                gate_pop("gauge_norm", 64, 1.2, 31.25, w_s),
                gate_pop("skirt_margin", 40, 1.0, 50.0, w_s),
                gate_pop("vendor_skip_advocate", 32, 0.7, 25.0, w_s),
                gate_pop("accept_latch", 96, 1.8, 62.5, w_s),
            ],
        },
        "gate_compute": gate_compute(
            [
                {"check": "pw3.dic_scorer", "neurons": 80, "mean_rate_hz": 50.0, "window_ms": 36.0},
                {"check": "pw3.hoop_scorer", "neurons": 40, "mean_rate_hz": 62.5, "window_ms": 32.0},
            ]
        ),
        "meta": meta_common(
            id="nelb-r51-156",
            clock_domain="pw3-dic-sim-relative-ms-t0-2026-08-19T03:00:00Z",
            tags=["dic-hoop-strain", "ACCEPT", "REJECT", "serialized-reconstruction", "operational-t2"],
        ),
    }
