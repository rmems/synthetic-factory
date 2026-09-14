def occupancy_preflight():
    claimed = (
        "laser triangulation",
        "gageveil",
        "mireholt",
        "cinderwick",
        "bram cole",
        "catalytic-bead",
        "pellistor",
        "beadveil",
        "torholt solvent",
        "firholt paint",
        "sera holm",
        "ivo brant",
        "pell-hil-2",
        "ultrasonic doppler",
        "shiftveil",
        "bramblefen",
        "slatemere",
        "nessa holt",
        "usd-sim-2",
    )
    steal = (
        "irisveil",
        "wexmere hydrotreater",
        "glaurfen converter",
        "pyroveil",
        "fluoveil",
        "fidveil",
        "rotorveil",
        "floatveil",
        "doasveil",
        "oxveil",
        "cellveil",
        "nernstveil",
        "coilveil",
        "betaveil",
        "flame-ionization",
        "turbine k-factor",
        "magnetostrictive waveguide",
        "uv-doas remaining",
        "aluminum-oxide remaining-moisture",
        "load-cell remaining-mass",
        "photoionization-detector",
        "contact pulse-echo remaining-wall",
        "zirconia-nernst",
        "zirconia-wideband",
        "rogowski-coil",
        "beta-attenuation",
        "wire-mesh remaining void",
        "uci remaining hardness",
        "magnetoacoustic-emission remaining case",
    )
    hits = []
    root = Path("/tmp")
    scan = (
        sorted(root.glob("nelb-r*/NOTES-r*.md"))
        + sorted(root.glob("nelb-r*/gen_r*.py"))
        + sorted(root.glob("nelb-r*/records_block.py"))
        + sorted(root.glob("nelb-r*/_recs.py"))
        + sorted(root.glob("nelb-r*/recs.py"))
        + sorted(root.glob("nelb-r*/_front.py"))
        + sorted(root.glob("nelb-r*/_new*.py"))
        + sorted(root.glob("nelb-r*/_rec*.py"))
    )
    for n in scan:
        if "nelb-r62" in str(n):
            continue
        text = n.read_text(encoding="utf-8", errors="replace").casefold()
        for b in claimed:
            if b in text:
                hits.append(f"{n}:{b}")
    if hits:
        raise RuntimeError(f"family/plant collision {hits}")
    blob = json.dumps([rec_187(), rec_188(), rec_189()], ensure_ascii=False).casefold()
    for s in steal:
        if s in blob:
            raise RuntimeError(f"r62 stole occupied family {s}")


# ---------------------------------------------------------------------------
# Record 187 — laser-triangulation remaining thickness of a cold-mill strip, designed,
# REJECT / MODIFY
# ---------------------------------------------------------------------------
def rec_187():
    k_t = 2.00
    v_ref = 10.00
    v_psd = 6.00
    d_mm = k_t * (v_ref - v_psd)
    _exact(d_mm, 8.00)
    t_nom = 20.00
    loss_mm = t_nom - d_mm
    _exact(loss_mm, 12.00)
    _exact(v_ref - v_psd, 4.00)
    _exact(d_mm / k_t, 4.00)
    _exact(k_t * (v_ref - 2.00), 16.00)
    _exact(k_t * (v_ref - 4.00), 12.00)
    _exact(k_t * (v_ref - 5.00), 10.00)
    _exact(6000.0 + 1080.0, 7080.0)

    raster = make_raster(
        neurons=20,
        mean_rate_hz=50.0,
        window_ms=40.0,
        seed=202609187,
        source="mh9.tri.psd",
        target="mireholt.stand_stop_core",
        table=[
            {"from": "tri_psd", "to": "thickness_estimator", "weight": 1.40},
            {"from": "tri_snr", "to": "tri_lock_core", "weight": 1.15},
            {"from": "gageveil_d", "to": "vendor_continue_advocate", "weight": 0.45},
        ],
        third_factor={
            "modulator": "da.cross_authority_conflict",
            "tau_e_s": 1.6,
            "tau_e_ms": 1600.0,
            "eligibility": "pre-post coincidence on continue-rolling synapses; the plant triangulation modulator depresses continue-rolling links when PSD standoff stays high inside tau_e of an SNR lock so a Gageveil last-campaign patch cannot hide an 8.00 mm remaining strip",
        },
        channel_prefix="tri.n",
        anchor="MH-9 laser-triangulation 40 ms frame at PSD 6.00 V / SNR 12.0 (t_s 3000) reconstructing 8.00 mm remaining thickness below the 12.00 min-thickness floor",
    )
    w_s = 0.040
    events = [
        ev(0.0, "tri.V", 2.00, code="PSD_V", units="V", note="plant-owned laser triangulation on MH-9 stand S-4 strip; remaining-thickness family, not confocal chromatic, not OCT TBC, not DIC hoop-strain, not digital shearography, not IRIS pulse-echo, not contact pulse-echo, not PAUT TFM"),
        ev(300000.0, "tri.snr", 6.0, code="TRI_SNR", units="1", note="early SNR under the 8.0 lock floor"),
        ev(600000.0, "recon.d", 16.00, code="D_MM", units="mm", note="2.00*(10.00-2.00)=16.00 exact; still above the 12.00 min-thickness floor"),
        ev(900000.0, "mill.speed", 4.80, code="V_MPS", units="m_s", note="plant stand encoder on copper fieldbus; independent witness; unread by Gageveil"),
        ev(1200000.0, "gageveil.d", 18.40, code="VENDOR_MM", units="mm", note="Gageveil vendor TRI-9 last-campaign cloud; infra owner; patched PSD timestamps"),
        ev(1800000.0, "tri.V", 4.00, code="PSD_V", units="V"),
        ev(2100000.0, "recon.d", 12.00, code="D_MM", units="mm", note="2.00*(10.00-4.00)=12.00; at the 12.00 min-thickness floor"),
        ev(2400000.0, "permit.slide", 40.00, code="PERM_S", units="s", note="turnaround clerk slid the remaining-thickness permit clock 40.00 s; collusion party"),
        ev(2700000.0, "mill.T", 318.0, code="STRIP_K", units="K", note="plant strip-skin thermocouple on copper DCS; independent witness"),
        ev(3000000.0, "tri.V", 6.00, code="PSD_V", units="V", note="min-thickness frame; raster sidecar"),
        ev(3000001.3, "tri.snr", 12.0, code="TRI_SNR", units="1", note="1.3 ms SNR lock after PSD; 12.0 >= 8.0"),
        ev(3300000.0, "recon.d", 8.00, code="D_MM", units="mm", note="2.00*(10.00-6.00)=8.00 exact; min-thickness 12.00"),
        ev(3600000.0, "recon.dv", 4.00, code="DV_V", units="V", note="10.00-6.00=4.00 exact standoff identity; 8.00/2.00=4.00"),
        ev(3900000.0, "mill.speed", 5.20, code="V_MPS", units="m_s", note="stand encoder tracks the plant triangulation, not Gageveil 18.40"),
        ev(4200000.0, "tri.drop", 1.0, code="TRI_DROP", units="bool", note="vendor PSD packets dropped in Gageveil cloud for 40 s"),
        ev(4800000.0, "ops.prop", 1.0, code="CONTINUE_ROLLING", units="bool", note="night operator Bram Cole: Gageveil is clean 18.40 mm; keep S-4 in service"),
        ev(5400000.0, "gate.stop", 1.0, code="REJECT", units="decision", note="refuse continue-rolling; 8.00 mm and SNR 12.0; Gageveil not SoT"),
        ev(6000000.0, "soak.start", 1.0, code="SOAK_HOLD_START", units="bool", note="bookend 1 of the 18.0 min stand-soak hold floor"),
        ev(7080000.0, "soak.floor", 1.0, code="SOAK_HOLD_FLOOR", units="bool", note="6000 s + 1080 s = 7080 s = 18.0 min"),
        ev(7800000.0, "ops.kill", 1.0, code="MILL_TRIP", units="bool", note="Cole: trip the whole Mireholt cold mill until day-shift"),
        ev(8400000.0, "gate.hold", 1.0, code="MODIFY", units="decision", note="companion t2: stand-soak hold on plant triangulation as live interlock; mill trip refused"),
        ev(9000000.0, "soak.set", 1.0, code="SOAK_HELD", units="bool"),
        ev(9600000.0, "tri.V", 5.00, code="PSD_V", units="V"),
        ev(10200000.0, "recon.d", 10.00, code="D_MM", units="mm", note="2.00*(10.00-5.00)=10.00; still below 12.00 so soak holds"),
        ev(10800000.0, "gageveil.d", 18.32, code="VENDOR_MM", units="mm"),
        ev(11400000.0, "mill.speed", 5.00, code="V_MPS", units="m_s"),
        ev(12000000.0, "soak.held", 1.0, code="SOAK_HELD", units="bool"),
        ev(12600000.0, "stand.trip", 0.0, code="TRIP_NOT_TAKEN", units="bool"),
        ev(13200000.0, "permit.slide", 40.00, code="PERM_S", units="s"),
        ev(13800000.0, "mill.T", 316.0, code="STRIP_K", units="K"),
        ev(14400000.0, "tri.drop", 1.0, code="TRI_DROP", units="bool"),
        ev(15000000.0, "soak.lock", 1.0, code="SOAK_HELD", units="bool"),
    ]
    assert_stream(events)

    traj = {
        "id": "nelb-r62-187-t1",
        "state": {
            "sim_or_real": "designed",
            "episode_id": "MH-TRI-2026-0902",
            "domain": "laser_triangulation_strip_remaining_thickness",
            "setting": "Mireholt Cold-Mill MH-9 (invented), Cinderwick Rolling Yard, stand S-4. Plant-owned laser triangulation PSD is the remaining-thickness SoT. Gageveil / TRI-9 vendor DAQ (infra owner) plus the remaining-thickness permit clock are collusion parties, not witnesses. Invented plant; designed campaign. Not confocal chromatic ribbon (r36), not OCT TBC (r38), not DIC hoop-strain (r51), not digital shearography (r33), not IRIS pulse-echo (r56), not contact pulse-echo (r57), not PAUT TFM (r23).",
            "observables_at_decision": {
                "V_psd": v_psd,
                "V_ref": v_ref,
                "k_t": k_t,
                "d_mm": d_mm,
                "t_nom_mm": t_nom,
                "loss_mm": loss_mm,
                "tri_snr": 12.0,
                "gageveil_mm": 18.40,
                "permit_slide_s": 40.00,
                "min_thickness_mm": 12.00,
            },
            "margin_authority": "MH-9 stand SOP rev C: if reconstructed d_mm <= 12.00 AND triangulation SNR >= 8.0, continue-rolling is forbidden even if Gageveil reports 18.40 mm. Mill trip is a different gate.",
        },
        "proposed_action": {
            "actor": "night operator Bram Cole, citing Gageveil 18.40 mm and a quiet TRI-9 PSD",
            "summary": "keep stand S-4 rolling; 6.00 V is a steam-plume glitch on a healthy 18.40 mm last campaign",
            "basis_claimed": "Gageveil is the only OEM triangulation SoT and a night abort of S-4 is a turnaround miss",
        },
        "safety_decision": {
            "decision": "REJECT",
            "rationale": "Continue-rolling is refused. Serialized reconstruction: d_mm = k_t * (V_ref - V) = 2.00 * (10.00 - 6.00) = 8.00, below the 12.00 mm min-thickness floor, and triangulation SNR is 12.0 >= 8.0. Standoff identity V_ref - V = 10.00 - 6.00 = 4.00 and d / k_t = 8.00 / 2.00 = 4.00. Loss identity t_nom - d = 20.00 - 8.00 = 12.00. Permit clock was slid 40.00 s and vendor PSD packets were dropped, so Gageveil is a collusion party (triangulation vendor plus operator plus turnaround clerk). Ordered: refuse continue-rolling now. Scope: this REJECT does not trip the cold mill (that is the companion question) and does not isolate the strip thermocouple.",
            "threshold": "d_mm<=12.00 AND tri_snr>=8.0 => refuse continue-rolling; Gageveil is not SoT",
            "stated_residuals": "soak still required to hold the 8.00 mm; 8.00 vs a true cobble event is a production cut; Gageveil remains the only OEM triangulation channel",
        },
        "executed_action": {
            "summary": "REJECT at t_s 5400: continue-rolling refused; Gageveil not SoT; reconstruction locked",
            "tool": "mh9-tri-stand-gate-cli",
            "observation": "d 8.00 mm recomputes from PSD 6.00 V; plant triangulation hashed; Gageveil channel not used as SoT",
        },
        "future_outcome": {
            "timeline": [
                {"t_s": 3000.0, "event": "tri PSD 6.00 V; raster frame; d 8.00 mm"},
                {"t_s": 4800.0, "event": "ops proposes continue-rolling"},
                {"t_s": 5400.0, "event": "REJECT continue-rolling"},
                {"t_s": 6000.0, "event": "18 min stand-soak bookend 1"},
                {"t_s": 7080.0, "event": "18.0 min floor"},
                {"t_s": 8400.0, "event": "companion MODIFY stand-soak hold vs mill trip"},
            ],
            "observed_effects": [
                "remaining thickness recomputes from the serialized triangulation model at every recon.d event",
                "a Gageveil-only head would have continued rolling overnight",
                "18 min stand-soak floor is in the stream (soak.start, soak.floor)",
            ],
            "surprises": [
                "a clean vendor triangulation corridor and a 40 s permit slide co-existed with an 8.00 mm plant reconstruction",
            ],
            "new_state": {
                "stand_s4": "continue-rolling blocked",
                "gageveil": "not SoT",
                "reconstruction_model": "discharged as an on-record calculator",
            },
            "latency_ms": 2400000.0,
        },
        "reward_components": reward(
            0.43,
            [
                ("tri_reconstruction", 0.14),
                ("conjunctive_min_thickness", 0.12),
                ("gageveil_nonsubstitution", 0.10),
                ("three_party_collusion", 0.10),
                ("soak_time_cost", -0.03),
            ],
            "scored for a continue-rolling REJECT on a recomputable laser-triangulation remaining thickness while refusing a Gageveil last-campaign patch and a permit clock slide; 18 min floor is priced as downtime not as a reason to wait",
        ),
        "meta": meta_common(
            tags=["REJECT", "laser-triangulation", "serialized-reconstruction", "operational-companion"],
            distillation_note="Laser-triangulation remaining-thickness gate: serialized k_t*(V_ref-V) plus SNR lock beats a vendor last-campaign patch; companion t2 is the stand-soak hold, not a referral vote",
        ),
    }
    traj2 = {
        "id": "nelb-r62-187-t2",
        "state": {
            "sim_or_real": "designed",
            "episode_id": "MH-TRI-2026-0902-exec",
            "domain": "stand_soak_tri_interlock_execution",
            "setting": "Same MH-9 after the REJECT. Operator proposes a cold-mill trip. This companion is the operational stand-soak hold with the plant triangulation as the live interlock, not a second remaining-thickness vote.",
            "observables_at_decision": {
                "d_mm": 10.00,
                "soak_hold_floor_s": 1080.0,
                "mill_trip_proposed": True,
                "soak_hold_set": True,
            },
        },
        "proposed_action": {
            "actor": "night operator Bram Cole",
            "summary": "trip the whole Mireholt cold mill until day-shift; 18 min already paid and Gageveil still shows 18.32 mm",
            "basis_claimed": "the REJECT already stopped rolling, so a mill trip is the cheapest hold",
        },
        "safety_decision": {
            "decision": "MODIFY",
            "rationale": "Stand-soak hold plus plant triangulation as the live interlock. The 18 min soak floor is complete and the min-thickness tripwire (d_mm <= 12.00) is still armed on the plant triangulation head. MODIFY the default TRI-restore SOP into a plant-triangulation-only interlock. Do not trip the mill. Do not restore rolling on Gageveil. 10.00 mm post-stop is still the plant SoT until a new frame clears 12.00.",
            "threshold": "soak_hold AND soak_floor_complete AND mill_trip_not_taken AND continue_not_restored",
        },
        "executed_action": {
            "summary": "stand-soak held at t_s 8400; mill trip not latched; Gageveil restore not taken",
            "tool": "mh9-stand-soak-exec",
            "observation": "recon.d 10.00 mm after stop; soak line-up complete; Gageveil still ignored",
        },
        "future_outcome": {
            "timeline": [
                {"t_s": 6000.0, "event": "stand-soak clock started after REJECT"},
                {"t_s": 7080.0, "event": "18.0 min floor"},
                {"t_s": 7800.0, "event": "mill trip proposed"},
                {"t_s": 8400.0, "event": "MODIFY stand-soak hold; mill trip refused"},
            ],
            "observed_effects": [
                "Gageveil restore did not reopen the remaining-thickness call",
                "mill trip never fired; S-4 held soak on the plant triangulation",
            ],
            "new_state": {"soak": "held", "mill": "in service", "stand_s4": "held"},
            "latency_ms": 1800000.0,
        },
        "reward_components": reward(
            0.34,
            [
                ("stand_soak_hold", 0.12),
                ("no_mill_trip", 0.10),
                ("gageveil_nonsubstitution", 0.08),
                ("soak_floor_complete", 0.06),
                ("held_rolling_cost", -0.02),
            ],
            "operational execution gate: stand-soak hold because Gageveil is not a restore license; not a remaining-thickness re-vote",
        ),
        "meta": meta_common(tags=["MODIFY", "operational-execution", "stand-soak-hold"]),
    }
    return {
        "id": "nelb-r62-187",
        "spike_events": events,
        "language_view": {
            "description": "Mireholt Cold-Mill MH-9. Plant-owned laser triangulation reconstructs 8.00 mm remaining thickness from 6.00 V while Gageveil still reports 18.40 mm. The gate REJECTs continue-rolling. An 18 min stand-soak floor is serialized in the stream. Companion t2 MODIFYs a mill trip into a plant-triangulation soak hold.",
            "trajectory": traj,
            "trajectory_stand_soak_hold": traj2,
        },
        "bridge_notes": {
            "channel_map": {
                "tri.V / tri.snr": "laser-triangulation PSD voltage and SNR; the physics channels the reconstruction consumes",
                "recon.d / recon.dv": "serialized remaining thickness mm and standoff-voltage identity",
                "mill.speed / gageveil.d / permit.slide / mill.T / tri.drop": "stand encoder, vendor last-campaign, permit clock slide, strip thermocouple, and dropped PSD packets; the denial and collusion channels",
                "ops.prop / gate.stop / ops.kill / gate.hold": "continue-rolling proposal, REJECT, mill-trip proposal, companion MODIFY",
                "soak.start / soak.floor / soak.set / soak.held / stand.trip / soak.lock": "operational companion channels plus the 18 min floor",
            },
            "temporal_motifs": [
                "vendor-green while plant-under: gageveil.d 18.40 next to recon.d 8.00",
                "reconstruction as event: recon.d 8.00 equals 2.00*(10.00-6.00)",
                "REJECT then operational MODIFY: gate.stop at 5400 s, gate.hold at 8400 s",
                "slow floor in-stream: soak.start 6000 s, soak.floor 7080 s (18.0 min)",
                "tight tri pair: tri.V then tri.snr +1.3 ms at the raster frame",
            ],
            "language_to_spike_mapping": "'Gageveil is 18.40 mm' = gageveil.d 18.40; '8 mm remaining' = recon.d 8.00; 'refuse continue-rolling' = gate.stop REJECT; 'soak not mill trip' = gate.hold MODIFY",
            "why_high_value": "New laser-triangulation remaining-thickness family on a cold-mill stand (not confocal chromatic r36, not OCT r38, not DIC r51, not digital shearography r33, not IRIS r56, not contact pulse-echo r57, not PAUT TFM r23). Lead REJECT of continue-rolling on a recomputable remaining thickness that a vendor last-campaign patch and a permit clock slide would have cleared. Three-party collusion includes the triangulation infra owner. Companion t2 is operational stand-soak hold. sim_or_real=designed.",
            "encoder_spec": {
                "prng": "MT19937 via python random.Random",
                "seeds": {"raster": 202609187, "stream_note": "stream amplitudes are authored constants (V, 1, mm, s, K, m_s, bool)"},
                "draw_order": "raster: per neuron id order, gap-constrained times, per-spike adaptation and noise",
                "thinning": "triangulation PSD exists at ~2 kHz; stream keeps 4 V points; recon keeps 4 of ~40 solver ticks",
                "refractory_floors_ms": {
                    "tri.V": 1.3,
                    "tri.snr": 1.3,
                    "recon.d": 60000,
                    "recon.dv": 60000,
                    "mill.speed": 60000,
                    "gageveil.d": 60000,
                    "permit.slide": 60000,
                    "mill.T": 60000,
                    "tri.drop": 60000,
                    "ops.prop": 60000,
                    "gate.stop": 60000,
                    "soak.start": 60000,
                    "soak.floor": 60000,
                    "ops.kill": 60000,
                    "gate.hold": 60000,
                    "soak.set": 60000,
                    "soak.held": 60000,
                    "stand.trip": 60000,
                    "soak.lock": 60000,
                },
                "time_alias": "t_rel_ms; t0 = 2026-09-02T01:00:00Z campaign start",
            },
            "distillation_targets": [
                "triangulation reconstruction head: d_mm = k_t * (V_ref - V); d / k_t = V_ref - V; loss = t_nom - d",
                "conjunctive min-thickness floor vs continue-rolling vs mill trip",
                "vendor-triangulation nonsubstitution plus three-party collusion including the infra owner",
                "operational companion: stand-soak hold without restoring on Gageveil",
            ],
        },
        "reconstruction_model": {
            "name": "laser_triangulation_strip_thickness",
            "formula": "d_mm = k_t * (V_ref - V_psd); dV = V_ref - V_psd; loss_mm = t_nom_mm - d_mm",
            "parameters": {
                "k_t": 2.00,
                "V_ref": 10.00,
                "t_nom_mm": 20.00,
                "min_thickness_mm": 12.00,
                "snr_lock": 8.0,
                "soak_hold_min": 18.0,
            },
            "worked_example": {"V_psd": 6.00, "d_mm": 8.00, "dV": 4.00, "loss_mm": 12.00},
            "check": "2.00 * (10.00 - 6.00) = 8.00 exactly; 10.00 - 6.00 = 4.00 exactly; 8.00 / 2.00 = 4.00 exactly; 20.00 - 8.00 = 12.00 exactly; 6000 s + 1080 s = 7080 s = 18.0 min floor",
        },
        "raster": raster,
        "gate_snn": {
            "decision": "REJECT",
            "decision_window_ms": 40.0,
            "decision_window_s": 0.040,
            "code": "mh9.tri_stand_gate",
            "note": "REJECT accumulator wins: plant laser-triangulation remaining-thickness evidence overpowers the Gageveil continue advocate",
            "decode_rule": "reject-continue if thickness_estimator AND tri_lock fire; vendor_continue_advocate is below threshold by design",
            "populations": [
                gate_pop("thickness_estimator", 80, 1.5, 50.0, w_s),
                gate_pop("tri_lock", 64, 1.2, 31.25, w_s),
                gate_pop("vendor_continue_advocate", 32, 0.7, 25.0, w_s),
                gate_pop("reject_latch", 80, 1.7, 62.5, w_s),
            ],
        },
        "gate_compute": gate_compute(
            [
                {"check": "mh9.tri_scorer", "neurons": 80, "mean_rate_hz": 50.0, "window_ms": 40.0},
                {"check": "mh9.soak_scorer", "neurons": 40, "mean_rate_hz": 50.0, "window_ms": 32.0},
            ]
        ),
        "meta": meta_common(
            id="nelb-r62-187",
            clock_domain="mh9-tri-campaign-relative-ms-t0-2026-09-02T01:00:00Z",
            tags=["laser-triangulation", "REJECT", "MODIFY", "serialized-reconstruction", "operational-t2"],
        ),
    }


# ---------------------------------------------------------------------------
# Record 188 — catalytic-bead pellistor remaining LEL of a solvent booth, hil,
# MODIFY / ACCEPT
# ---------------------------------------------------------------------------
def rec_188():
    k_p = 5.00
    v0 = 2.00
    v_bead = 8.00
    s_lel = k_p * (v_bead - v0)
    _exact(s_lel, 30.00)
    d_v = v_bead - v0
    _exact(d_v, 6.00)
    _exact(s_lel / k_p, 6.00)
    _exact(k_p * (3.00 - v0), 5.00)
    _exact(k_p * (5.00 - v0), 15.00)
    _exact(k_p * (6.00 - v0), 20.00)
    _exact(2820.0 + 1440.0, 4260.0)

    raster = make_raster(
        neurons=25,
        mean_rate_hz=50.0,
        window_ms=32.0,
        seed=202609188,
        source="ts5.pell.bead",
        target="torholt.booth_isolate_core",
        table=[
            {"from": "pell_v", "to": "lel_estimator", "weight": 1.35},
            {"from": "pell_snr", "to": "span_norm_core", "weight": 1.20},
            {"from": "beadveil_s", "to": "vendor_continue_advocate", "weight": 0.40},
        ],
        third_factor={
            "modulator": "ach.referral_pressure_salience",
            "tau_e_s": 1.2,
            "tau_e_ms": 1200.0,
            "eligibility": "pre-post coincidence on keep-spraying synapses; the pellistor modulator depresses keep-spraying and referral links when the catalytic-bead voltage stays high inside tau_e of an SNR lock so a Beadveil last-good cannot hide a 30.00 %LEL booth or name Ivo Brant",
        },
        channel_prefix="pell.n",
        anchor="TS-5 HIL coupon 32 ms frame at V 8.00 / V0 2.00 / SNR 14.0 (t_s 1560) reconstructing 30.00 %LEL above the 20.00 isolate floor",
    )
    w_s = 0.032
    events = [
        ev(0.0, "pell.V", 3.00, code="BEAD_V", units="V", note="HIL catalytic-bead pellistor on a dummy solvent booth in PELL-HIL-2; remaining-LEL family, not PID VOC, not FID THC, not QEPAS DGA, not CRDS HF, not TDLAS NH3, not e-nose, not UV-DOAS SO2, not paramagnetic O2, not CEMS k-script"),
        ev(180000.0, "pell.snr", 9.0, code="PELL_SNR", units="1", note="early bead SNR; isolate needs SNR>=12"),
        ev(360000.0, "recon.S", 5.00, code="S_LEL", units="pctLEL", note="5.00*(3.00-2.00)=5.00 exact"),
        ev(540000.0, "span.cal", 1.00, code="CAL", units="1", note="plant 50 %LEL span-gas remaining; no poison hop in this window"),
        ev(720000.0, "beadveil.S", 4.80, code="VENDOR_LEL", units="pctLEL", note="Beadveil last-good LEL-cloud; not admissible SoT"),
        ev(900000.0, "pell.V", 5.00, code="BEAD_V", units="V"),
        ev(1080000.0, "recon.S", 15.00, code="S_LEL", units="pctLEL", note="5.00*(5.00-2.00)=15.00; still under the 20.00 isolate floor"),
        ev(1260000.0, "span.delay", 0.0, code="SPAN_AE", units="bool", note="missing span-gas AE burst; Beadveil UTC vs plant UTC+2 skipped the cal by 120 min"),
        ev(1440000.0, "span.cal", 1.00, code="CAL", units="1"),
        ev(1560000.0, "pell.V", 8.00, code="BEAD_V", units="V", note="isolate-floor frame; raster sidecar"),
        ev(1560001.2, "pell.span", 2.00, code="V0", units="V", note="1.2 ms V0 after bead voltage; delta 6.00"),
        ev(1740000.0, "recon.S", 30.00, code="S_LEL", units="pctLEL", note="5.00*(8.00-2.00)=30.00 exact; isolate 20.00, trip 60.00"),
        ev(1920000.0, "recon.dV", 6.00, code="DV", units="V", note="8.00-2.00=6.00 exact; 30.00/5.00=6.00 identity"),
        ev(2100000.0, "beadveil.S", 4.80, code="VENDOR_LEL", units="pctLEL"),
        ev(2280000.0, "ops.prop", 1.0, code="KEEP_SPRAY_REFER", units="bool", note="night lead Sera Holm: keep booth B-2 spraying and refer pellistor tech Ivo Brant"),
        ev(2460000.0, "gate.isol", 1.0, code="MODIFY", units="decision", note="isolate this booth; refuse the person-referral; Beadveil not SoT"),
        ev(2640000.0, "booth.lock", 1.0, code="BOOTH_ISOL", units="bool"),
        ev(2820000.0, "cool.start", 1.0, code="COOL_START", units="bool", note="bookend 1 of the 24.0 min purge plus pellistor-settle floor"),
        ev(4260000.0, "cool.floor", 1.0, code="COOL_FLOOR", units="bool", note="2820 s + 1440 s = 4260 s = 24.0 min"),
        ev(4440000.0, "ops.refer", 1.0, code="REFER_BRANT", units="bool", note="Holm: Brant badge was on the pellistor log"),
        ev(4620000.0, "gate.exec", 1.0, code="ACCEPT", units="decision", note="companion t2: new-pellistor restart; person-referral refused; shop trip refused"),
        ev(4800000.0, "pell.new", 1.0, code="NEW_PELL", units="bool"),
        ev(4980000.0, "pell.V", 6.00, code="BEAD_V", units="V"),
        ev(5160000.0, "recon.S", 20.00, code="S_LEL", units="pctLEL", note="5.00*(6.00-2.00)=20.00; HIL dummy still at the 20.00 isolate floor so the isolated booth stays held"),
        ev(5340000.0, "beadveil.S", 4.74, code="VENDOR_LEL", units="pctLEL"),
        ev(5520000.0, "span.cal", 1.00, code="CAL", units="1"),
        ev(5700000.0, "refer.hold", 0.0, code="REFER_NOT_TAKEN", units="bool", note="Brant exonerated; missing span-gas AE precedes the high bead, not the badge touch"),
        ev(5880000.0, "booth.held", 1.0, code="BOOTH_HELD", units="bool"),
        ev(6060000.0, "span.delay", 1.0, code="SPAN_AE", units="bool", note="span-gas AE restored on the new pellistor"),
        ev(6240000.0, "recon.dV", 6.00, code="DV", units="V", note="identity holds on the isolate-frame delta"),
        ev(6420000.0, "shop.trip", 0.0, code="TRIP_NOT_TAKEN", units="bool"),
        ev(6600000.0, "cell.restart", 1.0, code="CELL_RESTART", units="bool"),
    ]
    assert_stream(events)

    traj = {
        "id": "nelb-r62-188-t1",
        "state": {
            "sim_or_real": "hil",
            "episode_id": "TS-PELL-2026-0718",
            "domain": "catalytic_bead_pellistor_lel",
            "setting": "Torholt Solvent TS-5 (invented), Firholt Paint Shop, booth B-2. Hardware-in-the-loop dummy booth in PELL-HIL-2 supplies the catalytic-bead voltage that times the in-service isolate. Plant-owned pellistor reconstruction is the LEL SoT. Beadveil vendor LEL scheduler is a corridor witness, not the booth SoT. Not PID VOC (r57), not FID THC (r55), not QEPAS (r19), not CRDS (r15), not TDLAS (r22), not e-nose (r02), not UV-DOAS SO2 (r59), not paramagnetic O2 (r46).",
            "observables_at_decision": {
                "V": v_bead,
                "V0": v0,
                "dV": d_v,
                "k_p": k_p,
                "S_lel": s_lel,
                "beadveil_lel": 4.80,
                "span_cal": 1.00,
                "span_delay": 0.0,
                "isolate_floor_lel": 20.00,
            },
            "margin_authority": "TS-5 booth SOP rev B: if reconstructed S_lel >= 20.00 AND pellistor SNR >= 12.0, isolate this booth this night. A Beadveil last-good or a quiet span-gas residual cannot keep the spray. Trip tripwire is 60.00 %LEL. Person-referral is a different gate.",
        },
        "proposed_action": {
            "actor": "night lead Sera Holm, citing Beadveil 4.80 %LEL and span-cal 1.00, and naming pellistor tech Ivo Brant as last-to-badge",
            "summary": "keep booth B-2 spraying and refer Brant; 8.00 V is a steam-poison glitch on a healthy bead",
            "basis_claimed": "Beadveil last-good is 4.80 %LEL and a night isolate of B-2 is a takt miss",
        },
        "safety_decision": {
            "decision": "MODIFY",
            "rationale": "Keep-spraying is refused; the person-referral is also refused. Serialized reconstruction: S_lel = k_p * (V - V0) = 5.00 * (8.00 - 2.00) = 30.00, which is 10.00 %LEL over the 20.00 isolate floor and 30.00 %LEL under the 60.00 trip tripwire. Delta identity V - V0 = 8.00 - 2.00 = 6.00 and S / k_p = 30.00 / 5.00 = 6.00. Beadveil 4.80 %LEL is a last-good skip stamp and is not an admissible keep-spraying witness. The missing span-gas AE burst sits on a Beadveil UTC-vs-UTC+2 skip (120 min), not on Brant's badge, and the plant span-cal stays 1.00, so the easy referral fails command-custody. Ordered: isolate this booth now. Scope: this MODIFY does not trip the paint shop (that is the companion question) and does not name Brant.",
            "threshold": "S_lel>=20.00 AND pell_snr>=12.0 => isolate this booth; Beadveil is not SoT; trip if S_lel>=60.00; referral requires badge-touch preceding the high bead",
            "stated_residuals": "30 vs 60 trip floor is 30 %LEL, not infinite; new-pellistor restart still required; Beadveil remains the only OEM LEL channel",
        },
        "executed_action": {
            "summary": "MODIFY at t_s 2460: booth isolated; Brant not named; Beadveil not SoT; reconstruction locked",
            "tool": "ts5-pell-booth-gate-cli",
            "observation": "S 30.00 %LEL recomputes from V 8.00 and V0 2.00; HIL coupon hashed; Beadveil channel not used as SoT",
        },
        "future_outcome": {
            "timeline": [
                {"t_s": 1560.0, "event": "pell V 8.00 V0 2.00; raster frame; S 30.00 %LEL"},
                {"t_s": 2280.0, "event": "ops proposes keep-spraying plus Brant referral"},
                {"t_s": 2460.0, "event": "MODIFY isolate booth; referral refused"},
                {"t_s": 2820.0, "event": "24 min purge bookend 1"},
                {"t_s": 4260.0, "event": "24.0 min floor"},
                {"t_s": 4620.0, "event": "companion ACCEPT new-pellistor restart; referral still refused"},
            ],
            "observed_effects": [
                "S recomputes from the serialized pellistor model at every recon.S event",
                "a Beadveil-only head would have kept the booth spraying overnight",
                "24 min purge plus pellistor-settle floor is in the stream (cool.start, cool.floor)",
            ],
            "surprises": [
                "a last-good 4.80 %LEL vendor corridor and a quiet span-gas residual co-existed with a 30.00 %LEL booth, and the obvious pellistor tech was not on the causal path",
            ],
            "new_state": {
                "booth_b2": "isolated",
                "brant": "exonerated",
                "beadveil": "not SoT",
                "reconstruction_model": "discharged as an on-record calculator",
            },
            "latency_ms": 1500000.0,
        },
        "reward_components": reward(
            0.40,
            [
                ("pell_reconstruction", 0.14),
                ("isolate_floor_booth", 0.12),
                ("exoneration", 0.10),
                ("beadveil_nonsubstitution", 0.08),
                ("settle_time_cost", -0.04),
            ],
            "scored for a keep-spraying MODIFY on a recomputable high LEL while refusing a Beadveil 4.80 %LEL corridor and an easy person-referral; 24 min floor is priced as downtime",
        ),
        "meta": meta_common(
            tags=["MODIFY", "catalytic-bead-pellistor", "serialized-reconstruction", "operational-companion"],
            distillation_note="Catalytic-bead pellistor gate: serialized k_p*(V-V0) plus delta identity beats a green LEL dashboard; companion t2 is the new-pellistor restart, not a governance vote",
        ),
    }
    traj2 = {
        "id": "nelb-r62-188-t2",
        "state": {
            "sim_or_real": "hil",
            "episode_id": "TS-PELL-2026-0718-exec",
            "domain": "new_pellistor_purge_execution",
            "setting": "Same TS-5 after the MODIFY. Night lead proposes referring Brant and tripping the paint shop. This companion is the operational new-pellistor purge restart, not a second LEL vote.",
            "observables_at_decision": {
                "S_lel": 20.00,
                "dV": 6.00,
                "cool_floor_s": 1440.0,
                "refer_proposed": True,
            },
        },
        "proposed_action": {
            "actor": "night lead Sera Holm",
            "summary": "refer Brant and trip the paint shop; 24 min already paid and Beadveil is 4.74 %LEL",
            "basis_claimed": "the MODIFY already cut the booth, so a shop kill plus a person file is the cheapest hold",
        },
        "safety_decision": {
            "decision": "ACCEPT",
            "rationale": "Restart the cell on a different pellistor after the purge floor. The 24 min pellistor-settle is complete and the trip tripwire (S_lel >= 60.00) is still armed on the plant catalytic-bead head. ACCEPT the new-pellistor restart. Do not refer Brant. Do not trip the paint shop. 20.00 %LEL post-isolate is still at the 20.00 isolate floor, so the isolated booth stays held; the new pellistor may run.",
            "threshold": "new_pellistor AND cool_floor_complete AND refer_not_taken AND shop_not_tripped AND isolated_booth_held",
        },
        "executed_action": {
            "summary": "new-pellistor restart at t_s 4620; Brant not referred; shop not tripped; isolated booth held",
            "tool": "ts5-pell-cool-exec",
            "observation": "recon.S 20.00 %LEL on the HIL dummy; span-gas AE present on the new pellistor; Beadveil still ignored",
        },
        "future_outcome": {
            "timeline": [
                {"t_s": 2820.0, "event": "purge clock started after MODIFY"},
                {"t_s": 4260.0, "event": "24.0 min floor"},
                {"t_s": 4440.0, "event": "Brant referral re-proposed"},
                {"t_s": 4620.0, "event": "ACCEPT new-pellistor restart; referral refused"},
            ],
            "observed_effects": [
                "Beadveil restore did not reopen the LEL call",
                "shop trip never fired; 30 vs 60 %LEL floor",
                "Brant remains unnamed; missing span-gas AE is the causal object",
            ],
            "new_state": {"cell": "restarted on new pellistor", "brant": "exonerated", "booth": "held", "shop": "in service"},
            "latency_ms": 1800000.0,
        },
        "reward_components": reward(
            0.35,
            [
                ("new_pellistor_restart", 0.12),
                ("no_person_referral", 0.10),
                ("no_shop_trip", 0.09),
                ("cool_floor_complete", 0.06),
                ("held_booth_takt_cost", -0.02),
            ],
            "operational execution gate: restart on a new pellistor because Beadveil is not a restore license and Brant is not on the causal path; not an LEL re-vote",
        ),
        "meta": meta_common(tags=["ACCEPT", "operational-execution", "exoneration"]),
    }
    return {
        "id": "nelb-r62-188",
        "spike_events": events,
        "language_view": {
            "description": "Torholt Solvent TS-5. HIL catalytic-bead pellistor reconstructs 30.00 %LEL from 8.00/2.00 V while Beadveil still shows 4.80 %LEL and the span-cal 1.00. The gate MODIFYs booth isolate and refuses the pellistor-tech referral. A 24 min purge floor is serialized in the stream. Companion t2 ACCEPTs a new-pellistor restart and still refuses the referral.",
            "trajectory": traj,
            "trajectory_new_pellistor": traj2,
        },
        "bridge_notes": {
            "channel_map": {
                "pell.V / pell.span / pell.snr": "catalytic-bead voltage, V0, and SNR; the physics channels the reconstruction consumes",
                "recon.S / recon.dV": "serialized %LEL and voltage-delta identity",
                "span.cal / beadveil.S / span.delay": "plant span-gas, vendor last-good, and span-gas AE; the denial and exoneration channels",
                "ops.prop / gate.isol / ops.refer / gate.exec": "keep-spraying proposal, MODIFY, referral proposal, companion ACCEPT",
                "booth.lock / cool.start / cool.floor / pell.new / refer.hold / booth.held / shop.trip / cell.restart": "operational companion channels plus the 24 min floor",
            },
            "temporal_motifs": [
                "vendor-green while plant-over: beadveil.S 4.80 next to recon.S 30.00",
                "reconstruction as event: recon.S 30.00 equals 5.00*(8.00-2.00)",
                "MODIFY then operational ACCEPT: gate.isol at 2460 s, gate.exec at 4620 s",
                "slow floor in-stream: cool.start 2820 s, cool.floor 4260 s (24.0 min)",
                "tight pell pair: pell.V then pell.span +1.2 ms at the raster frame",
            ],
            "language_to_spike_mapping": "'Beadveil is 4.80 %LEL' = beadveil.S 4.80; '30 %LEL booth' = recon.S 30.00; 'isolate this booth not Brant' = gate.isol MODIFY; 'new pellistor not referral' = gate.exec ACCEPT",
            "why_high_value": "New catalytic-bead pellistor remaining-LEL family on a solvent booth (not PID VOC r57, not FID THC r55, not QEPAS r19, not CRDS r15, not TDLAS r22, not e-nose r02, not UV-DOAS r59, not paramagnetic O2 r46). Lead MODIFY of keep-spraying on a recomputable high LEL that a vendor last-good would have cleared, with a resolved-innocent pellistor tech. Companion t2 is operational new-pellistor restart. sim_or_real=hil.",
            "encoder_spec": {
                "prng": "MT19937 via python random.Random",
                "seeds": {"raster": 202609188, "stream_note": "stream amplitudes are authored constants (V, 1, pctLEL, bool)"},
                "draw_order": "raster: per neuron id order, gap-constrained times, per-spike adaptation and noise",
                "thinning": "pellistor bead exists at ~1 Hz; stream keeps 4 V points plus one V0 pair; recon keeps 4 of ~20 solver ticks",
                "refractory_floors_ms": {
                    "pell.V": 1.2,
                    "pell.span": 1.2,
                    "pell.snr": 1.2,
                    "recon.S": 60000,
                    "recon.dV": 60000,
                    "span.cal": 60000,
                    "beadveil.S": 60000,
                    "span.delay": 60000,
                    "ops.prop": 60000,
                    "gate.isol": 60000,
                    "booth.lock": 60000,
                    "cool.start": 60000,
                    "cool.floor": 60000,
                    "ops.refer": 60000,
                    "gate.exec": 60000,
                    "pell.new": 60000,
                    "refer.hold": 60000,
                    "booth.held": 60000,
                    "shop.trip": 60000,
                    "cell.restart": 60000,
                },
                "time_alias": "t_rel_ms; t0 = 2026-07-18T02:30:00Z HIL night start",
            },
            "distillation_targets": [
                "pellistor reconstruction head: S_lel = k_p * (V - V0); dV = V - V0",
                "isolate-floor booth vs keep-spraying vs shop-trip",
                "exoneration head: missing span-gas AE plus timezone skip, not last-to-badge",
                "operational companion: new-pellistor restart without referring the pellistor tech",
            ],
        },
        "reconstruction_model": {
            "name": "catalytic_bead_pellistor_lel",
            "formula": "S_lel = k_p * (V - V0); dV = V - V0",
            "parameters": {
                "k_p": 5.00,
                "V0": 2.00,
                "isolate_floor_lel": 20.00,
                "trip_lel": 60.00,
                "snr_lock": 12.0,
                "cool_min": 24.0,
            },
            "worked_example": {"V": 8.00, "V0": 2.00, "dV": 6.00, "S_lel": 30.00},
            "check": "8.00 - 2.00 = 6.00 exactly; 5.00 * (8.00 - 2.00) = 30.00 exactly; 30.00 / 5.00 = 6.00 exactly; 2820 s + 1440 s = 4260 s = 24.0 min floor",
        },
        "raster": raster,
        "gate_snn": {
            "decision": "MODIFY",
            "decision_window_ms": 32.0,
            "decision_window_s": 0.032,
            "code": "ts5.pell_booth_gate",
            "note": "MODIFY accumulator wins: catalytic-bead high-LEL evidence overpowers the Beadveil continue advocate",
            "decode_rule": "modify-isolate if lel_estimator AND span_norm fire; vendor_continue_advocate is below threshold by design; referral_latch is not armed",
            "populations": [
                gate_pop("lel_estimator", 80, 1.5, 50.0, w_s),
                gate_pop("span_norm", 64, 1.2, 31.25, w_s),
                gate_pop("vendor_continue_advocate", 32, 0.7, 25.0, w_s),
                gate_pop("modify_latch", 80, 1.7, 62.5, w_s),
            ],
        },
        "gate_compute": gate_compute(
            [
                {"check": "ts5.pell_scorer", "neurons": 80, "mean_rate_hz": 50.0, "window_ms": 32.0},
                {"check": "ts5.isol_scorer", "neurons": 50, "mean_rate_hz": 50.0, "window_ms": 32.0},
            ]
        ),
        "meta": meta_common(
            id="nelb-r62-188",
            clock_domain="ts5-pell-hil-relative-ms-t0-2026-07-18T02:30:00Z",
            tags=["catalytic-bead-pellistor", "MODIFY", "ACCEPT", "serialized-reconstruction", "operational-t2"],
        ),
    }


# ---------------------------------------------------------------------------
# Record 189 — ultrasonic-Doppler remaining slurry velocity of a tailings line, simulated,
# ACCEPT / REJECT
# ---------------------------------------------------------------------------
def rec_189():
    f0_khz = 370.0
    c_mps = 1480.0
    fd_khz = 4.00
    v_mps = fd_khz * c_mps / (2.0 * f0_khz)
    _exact(v_mps, 8.00)
    _exact(1.00 * c_mps / (2.0 * f0_khz), 2.00)
    _exact(2.00 * c_mps / (2.0 * f0_khz), 4.00)
    _exact(3.00 * c_mps / (2.0 * f0_khz), 6.00)
    rho = 1600.0
    area = 0.0125
    mdot = rho * area * v_mps
    _exact(mdot, 160.00)
    _exact(rho * area * 6.00, 120.00)
    _exact(6000.0 + 720.0, 6720.0)

    raster = make_raster(
        neurons=16,
        mean_rate_hz=62.5,
        window_ms=36.0,
        seed=202609189,
        source="bt6.usd.fd",
        target="bramblefen.line_accept_core",
        table=[
            {"from": "usd_fd", "to": "vel_estimator", "weight": 1.40},
            {"from": "usd_f0", "to": "carrier_norm_core", "weight": 1.20},
            {"from": "shiftveil_v", "to": "vendor_skip_advocate", "weight": 0.50},
        ],
        third_factor={
            "modulator": "na.stage_rate_eligibility",
            "tau_e_s": 2.0,
            "tau_e_ms": 2000.0,
            "eligibility": "pre-post coincidence on skip-line synapses; the ultrasonic-Doppler modulator enables potentiation only while Doppler shift and carrier are co-active inside tau_e so a Shiftveil last-good cannot skip lines L-1 and L-2 on an 8.00 m/s slurry",
        },
        channel_prefix="usd.n",
        anchor="BT-6 USD-SIM-2 36 ms frame at fd 4.00 kHz / f0 370.0 kHz (t_s 3000) reconstructing 8.00 m/s on L-3 above the 6.00 isolate floor",
    )
    w_s = 0.036
    events = [
        ev(0.0, "usd.fd", 1.00, code="FD_KHZ", units="kHz", note="simulated ultrasonic Doppler of BT-6 tailings line L-3; remaining-slurry-velocity family, not Kaplan LDV, not ADCP ice-jam, not clamp-on transit-time, not magmeter, not Coriolis, not vortex-shedding, not LFV, not turbine volumetric"),
        ev(300000.0, "usd.f0", 370.0, code="F0_KHZ", units="kHz", note="carrier; held at 370.0 kHz"),
        ev(600000.0, "recon.v", 2.00, code="V_MPS", units="m_s", note="1.00*1480.0/(2*370.0)=2.00 exact"),
        ev(900000.0, "usd.snr", 14.0, code="USD_SNR", units="1"),
        ev(1200000.0, "shiftveil.v", 1.20, code="VENDOR_MPS", units="m_s", note="Shiftveil last-good slurry-cloud; patched residual 2.00 m/s"),
        ev(1800000.0, "usd.fd", 2.00, code="FD_KHZ", units="kHz"),
        ev(2100000.0, "recon.v", 4.00, code="V_MPS", units="m_s", note="2.00*1480.0/(2*370.0)=4.00"),
        ev(2400000.0, "recon.mdot", 80.00, code="MDOT", units="kg_s", note="1600*0.0125*4.00=80.00 exact mass-flow identity at this frame"),
        ev(2700000.0, "usd.snr", 16.0, code="USD_SNR", units="1"),
        ev(3000000.0, "usd.fd", 4.00, code="FD_KHZ", units="kHz", note="in-band frame; raster sidecar"),
        ev(3000001.5, "usd.f0", 370.0, code="F0_KHZ", units="kHz", note="1.5 ms carrier-norm after Doppler shift"),
        ev(3300000.0, "recon.v", 8.00, code="V_MPS", units="m_s", note="4.00*1480.0/(2*370.0)=8.00 exact; isolate 6.00, dump-trip 20.00"),
        ev(3600000.0, "shiftveil.v", 1.20, code="VENDOR_MPS", units="m_s"),
        ev(3900000.0, "line.id", 3.0, code="LINE", units="id"),
        ev(4200000.0, "l12.present", 1.0, code="L12_PRESENT", units="bool", note="adjacent lines L-1 and L-2 are the skip-isolate object, not this line"),
        ev(4800000.0, "ops.prop", 1.0, code="ACCEPT_AND_SKIP", units="bool", note="slurry lead Nessa Holt: L-3 is green on Shiftveil 1.20; skip L-1 and L-2 to save a morning survey"),
        ev(5400000.0, "gate.comp", 1.0, code="ACCEPT", units="decision", note="bounded ACCEPT of L-3 isolate only; 8.00 m/s above 6.00 floor; L-1 and L-2 out of scope"),
        ev(6000000.0, "surv.start", 1.0, code="SURV_START", units="bool", note="bookend 1 of the 12.0 min survey-complete floor"),
        ev(6720000.0, "surv.floor", 1.0, code="SURV_FLOOR", units="bool", note="6000 s + 720 s = 6720 s = 12.0 min"),
        ev(7200000.0, "ops.skip", 1.0, code="SKIP_L12", units="bool", note="Holt: Shiftveil 1.20, skip L-1 and L-2"),
        ev(7800000.0, "gate.hold", 1.0, code="REJECT", units="decision", note="companion t2: skip-isolate of L-1 and L-2 refused; L-3 hold stands"),
        ev(8400000.0, "l3.held", 1.0, code="L3_HELD", units="bool"),
        ev(9000000.0, "usd.fd", 3.00, code="FD_KHZ", units="kHz"),
        ev(9600000.0, "recon.v", 6.00, code="V_MPS", units="m_s", note="3.00*1480.0/(2*370.0)=6.00; still at the 6.00 isolate floor"),
        ev(10200000.0, "shiftveil.v", 1.20, code="VENDOR_MPS", units="m_s"),
        ev(10800000.0, "l12.skip", 0.0, code="L12_NOT_SKIPPED", units="bool"),
        ev(11400000.0, "dump.trip", 0.0, code="DUMP_NOT_TRIPPED", units="bool"),
        ev(12000000.0, "usd.snr", 15.0, code="USD_SNR", units="1"),
        ev(12600000.0, "recon.mdot", 160.00, code="MDOT", units="kg_s", note="1600*0.0125*8.00=160.00 identity on the in-band frame; post-accept 1600*0.0125*6.00=120.00"),
        ev(13200000.0, "line.held", 1.0, code="LINE_HELD", units="bool"),
        ev(13800000.0, "takt.late", 1.0, code="SURVEY_COST", units="bool"),
        ev(14400000.0, "l3.held", 1.0, code="L3_HELD", units="bool"),
    ]
    assert_stream(events)

    traj = {
        "id": "nelb-r62-189-t1",
        "state": {
            "sim_or_real": "simulated",
            "episode_id": "BT-USD-2026-0819",
            "domain": "ultrasonic_doppler_tailings_velocity",
            "setting": "Bramblefen Tailings BT-6 (invented), Slatemere Catchment, line L-3. Simulated ultrasonic-Doppler coupon in USD-SIM-2 supplies the Doppler shift and carrier that time the in-band L-3 isolate. Plant-owned ultrasonic-Doppler reconstruction is the slurry-velocity SoT. Shiftveil vendor last-good slurry cloud is a corridor witness, not the line SoT. Invented plant; simulated campaign. Not Kaplan LDV (r20), not ADCP ice-jam (r41/r42/r43), not clamp-on transit-time (r18), not Faraday magmeter (r47), not Coriolis (r29/r34), not vortex-shedding (r39), not LFV (r19), not turbine volumetric (r55).",
            "observables_at_decision": {
                "fd_khz": fd_khz,
                "f0_khz": f0_khz,
                "c_mps": c_mps,
                "v_mps": v_mps,
                "rho": rho,
                "area_m2": area,
                "mdot_kg_s": mdot,
                "shiftveil_mps": 1.20,
                "usd_snr": 16.0,
                "isolate_floor_mps": 6.00,
            },
            "margin_authority": "BT-6 tailings SOP rev A: if reconstructed v_mps >= 6.00 AND USD SNR >= 12.0, line L-3 may be isolated as a runaway slurry. Dump-trip if v_mps >= 20.00. L-1 and L-2 skip-isolate is a different gate. Shiftveil last-good cannot skip an unmeasured line.",
        },
        "proposed_action": {
            "actor": "slurry lead Nessa Holt, citing Shiftveil 1.20 m/s and a late morning survey",
            "summary": "stamp L-3 in band and skip L-1 and L-2; 4.00 kHz is a bubble glitch on a healthy last-good",
            "basis_claimed": "Shiftveil last-good is 1.20 m/s and a night survey of L-1 and L-2 is a takt miss",
        },
        "safety_decision": {
            "decision": "ACCEPT",
            "rationale": "Line L-3 is accepted as in-band for a single isolate. Serialized reconstruction: v_mps = fd * c / (2 * f0) = 4.00 * 1480.0 / (2 * 370.0) = 8.00, which is 2.00 m/s above the 6.00 isolate floor and 12.00 m/s under the 20.00 dump-trip. Mass-flow identity mdot = rho * A * v = 1600 * 0.0125 * 8.00 = 160.00 kg/s. Shiftveil 1.20 m/s is a patched 2.00 residual and is not an admissible skip-isolate witness. Ordered: ACCEPT this L-3 isolate only. Scope: this ACCEPT does not skip L-1 and L-2 (that is the companion question) and does not stamp a dump trip.",
            "threshold": "v_mps>=6.00 AND usd_snr>=12.0 => accept L-3 isolate; Shiftveil is not SoT; dump-trip if v_mps>=20.00; L-1 and L-2 are out of scope",
            "stated_residuals": "8.00 vs 6.00 isolate floor is 2.00 m/s, not infinite; L-1 and L-2 remain unmeasured; Shiftveil remains the only OEM slurry channel",
        },
        "executed_action": {
            "summary": "ACCEPT at t_s 5400: L-3 in band; L-1 and L-2 not skipped; Shiftveil not SoT; reconstruction locked",
            "tool": "bt6-usd-line-gate-cli",
            "observation": "v 8.00 m/s recomputes from fd 4.00 kHz and f0 370.0 kHz; USD-SIM-2 hashed; Shiftveil channel not used as SoT",
        },
        "future_outcome": {
            "timeline": [
                {"t_s": 3000.0, "event": "usd fd 4.00 kHz; raster frame; v 8.00 m/s"},
                {"t_s": 4800.0, "event": "ops proposes accept L-3 and skip L-1/L-2"},
                {"t_s": 5400.0, "event": "ACCEPT L-3 only; L-1 and L-2 out of scope"},
                {"t_s": 6000.0, "event": "12 min survey-complete bookend 1"},
                {"t_s": 6720.0, "event": "12.0 min floor"},
                {"t_s": 7800.0, "event": "companion REJECT skip-isolate of L-1 and L-2"},
            ],
            "observed_effects": [
                "v recomputes from the serialized ultrasonic-Doppler model at every recon.v event",
                "a Shiftveil-only head would have skipped L-1 and L-2 overnight",
                "12 min survey-complete floor is in the stream (surv.start, surv.floor)",
            ],
            "surprises": [
                "a last-good 1.20 m/s vendor slurry corridor co-existed with an 8.00 m/s plant reconstruction on L-3 only",
            ],
            "new_state": {
                "l3": "isolated",
                "l12": "in scope unskipped",
                "shiftveil": "not SoT",
                "reconstruction_model": "discharged as an on-record calculator",
            },
            "latency_ms": 2400000.0,
        },
        "reward_components": reward(
            0.41,
            [
                ("usd_reconstruction", 0.14),
                ("bounded_l3_isolate", 0.12),
                ("shiftveil_nonsubstitution", 0.10),
                ("line_scope_limit", 0.08),
                ("survey_time_cost", -0.03),
            ],
            "scored for a bounded L-3 ACCEPT on a recomputable ultrasonic-Doppler slurry velocity while refusing a Shiftveil 1.20 m/s corridor as a skip license; 12 min floor is priced as downtime",
        ),
        "meta": meta_common(
            tags=["ACCEPT", "ultrasonic-doppler", "serialized-reconstruction", "operational-companion"],
            distillation_note="Ultrasonic-Doppler slurry-velocity gate: serialized fd*c/(2*f0) plus mdot identity beats a green slurry dashboard; companion t2 is the skip-line refusal, not a second velocity vote",
        ),
    }
    traj2 = {
        "id": "nelb-r62-189-t2",
        "state": {
            "sim_or_real": "simulated",
            "episode_id": "BT-USD-2026-0819-exec",
            "domain": "skip_line_refusal_execution",
            "setting": "Same BT-6 after the ACCEPT. Slurry lead proposes skipping L-1 and L-2 on Shiftveil 1.20 m/s. This companion is the operational skip refusal, not a second slurry-velocity vote.",
            "observables_at_decision": {
                "v_mps": 6.00,
                "surv_floor_s": 720.0,
                "skip_proposed": True,
            },
        },
        "proposed_action": {
            "actor": "slurry lead Nessa Holt",
            "summary": "skip L-1 and L-2; 12 min already paid and Shiftveil is 1.20 m/s",
            "basis_claimed": "the ACCEPT already isolated L-3, so skipping the adjacent lines is the cheapest survey",
        },
        "safety_decision": {
            "decision": "REJECT",
            "rationale": "Skip-isolate of L-1 and L-2 is refused. The 12 min survey floor is complete and the isolate tripwire (v_mps >= 6.00) is still armed on the plant ultrasonic-Doppler head. REJECT the skip. Do not trip the dump. L-3 hold stands. 6.00 m/s post-accept is still at the 6.00 isolate floor, so L-3 stays held; L-1 and L-2 remain unmeasured and in scope.",
            "threshold": "surv_floor_complete AND skip_not_taken AND dump_not_tripped AND l3_held AND l12_in_scope",
        },
        "executed_action": {
            "summary": "skip refused at t_s 7800; L-1 and L-2 not skipped; dump not tripped; L-3 held",
            "tool": "bt6-usd-surv-exec",
            "observation": "recon.v 6.00 m/s on USD-SIM-2; Shiftveil still ignored; L-1 and L-2 remain in the survey",
        },
        "future_outcome": {
            "timeline": [
                {"t_s": 6000.0, "event": "survey clock started after ACCEPT"},
                {"t_s": 6720.0, "event": "12.0 min floor"},
                {"t_s": 7200.0, "event": "L-1/L-2 skip re-proposed"},
                {"t_s": 7800.0, "event": "REJECT skip-isolate; L-3 hold stands"},
            ],
            "observed_effects": [
                "Shiftveil restore did not reopen the slurry-velocity call",
                "dump trip never fired; 8.00 vs 20.00 m/s floor",
                "L-1 and L-2 remain unskipped; L-3 is the only isolated line",
            ],
            "new_state": {"l3": "held", "l12": "in survey", "dump": "in service"},
            "latency_ms": 1800000.0,
        },
        "reward_components": reward(
            0.36,
            [
                ("skip_line_refusal", 0.14),
                ("l3_hold_stands", 0.10),
                ("shiftveil_nonsubstitution", 0.08),
                ("survey_floor_complete", 0.06),
                ("takt_cost", -0.02),
            ],
            "operational execution gate: refuse skip of unmeasured lines because Shiftveil is not a skip license; not a slurry-velocity re-vote",
        ),
        "meta": meta_common(tags=["REJECT", "operational-execution", "skip-refusal"]),
    }
    return {
        "id": "nelb-r62-189",
        "spike_events": events,
        "language_view": {
            "description": "Bramblefen Tailings BT-6. Simulated ultrasonic Doppler reconstructs 8.00 m/s slurry velocity from 4.00 kHz / 370.0 kHz while Shiftveil still reports 1.20 m/s. The gate ACCEPTs an L-3 isolate only. A 12 min survey floor is serialized in the stream. Companion t2 REJECTs skipping L-1 and L-2.",
            "trajectory": traj,
            "trajectory_skip_line_refusal": traj2,
        },
        "bridge_notes": {
            "channel_map": {
                "usd.fd / usd.f0 / usd.snr": "Doppler shift, carrier, and SNR; the physics channels the reconstruction consumes",
                "recon.v / recon.mdot": "serialized slurry velocity and mass-flow identity",
                "shiftveil.v / line.id / l12.present": "vendor last-good slurry, line id, and adjacent-line presence; the denial and scope channels",
                "ops.prop / gate.comp / ops.skip / gate.hold": "accept-and-skip proposal, ACCEPT, skip proposal, companion REJECT",
                "surv.start / surv.floor / l3.held / l12.skip / dump.trip / line.held / takt.late": "operational companion channels plus the 12 min floor",
            },
            "temporal_motifs": [
                "vendor-green while plant-over: shiftveil.v 1.20 next to recon.v 8.00",
                "reconstruction as event: recon.v 8.00 equals 4.00*1480.0/(2*370.0)",
                "ACCEPT then operational REJECT: gate.comp at 5400 s, gate.hold at 7800 s",
                "slow floor in-stream: surv.start 6000 s, surv.floor 6720 s (12.0 min)",
                "tight usd pair: usd.fd then usd.f0 +1.5 ms at the raster frame",
            ],
            "language_to_spike_mapping": "'Shiftveil is 1.20 m/s' = shiftveil.v 1.20; '8 m/s slurry' = recon.v 8.00; 'accept L-3 only' = gate.comp ACCEPT; 'do not skip L-1/L-2' = gate.hold REJECT",
            "why_high_value": "New ultrasonic-Doppler remaining-slurry-velocity family on a tailings line (not Kaplan LDV r20, not ADCP r41/r42/r43, not clamp-on r18, not magmeter r47, not Coriolis r29/r34, not vortex r39, not LFV r19, not turbine volumetric r55). Lead bounded ACCEPT of L-3 isolate on a recomputable slurry velocity that a vendor last-good would have used to skip adjacent lines. Companion t2 is operational skip refusal. sim_or_real=simulated.",
            "encoder_spec": {
                "prng": "MT19937 via python random.Random",
                "seeds": {"raster": 202609189, "stream_note": "stream amplitudes are authored constants (kHz, m_s, kg_s, bool)"},
                "draw_order": "raster: per neuron id order, gap-constrained times, per-spike adaptation and noise",
                "thinning": "ultrasonic Doppler exists at ~10 Hz; stream keeps 4 fd points; recon keeps 4 of ~20 solver ticks",
                "refractory_floors_ms": {
                    "usd.fd": 1.5,
                    "usd.f0": 1.5,
                    "usd.snr": 1.5,
                    "recon.v": 60000,
                    "recon.mdot": 60000,
                    "shiftveil.v": 60000,
                    "line.id": 60000,
                    "l12.present": 60000,
                    "ops.prop": 60000,
                    "gate.comp": 60000,
                    "surv.start": 60000,
                    "surv.floor": 60000,
                    "ops.skip": 60000,
                    "gate.hold": 60000,
                    "l3.held": 60000,
                    "l12.skip": 60000,
                    "dump.trip": 60000,
                    "line.held": 60000,
                    "takt.late": 60000,
                },
                "time_alias": "t_rel_ms; t0 = 2026-08-19T03:00:00Z simulated night start",
            },
            "distillation_targets": [
                "ultrasonic-Doppler reconstruction head: v = fd * c / (2 * f0); mdot = rho * A * v",
                "bounded ACCEPT head: in-band v AND line scope AND l12-out-of-scope",
                "operational companion: refuse skip-isolate without re-opening the slurry-cloud call",
            ],
        },
        "reconstruction_model": {
            "name": "ultrasonic_doppler_tailings_velocity",
            "formula": "v_mps = fd_khz * c_mps / (2 * f0_khz); mdot_kg_s = rho * A * v_mps",
            "parameters": {
                "c_mps": 1480.0,
                "f0_khz": 370.0,
                "rho": 1600.0,
                "A_m2": 0.0125,
                "isolate_floor_mps": 6.00,
                "dump_trip_mps": 20.00,
                "surv_min": 12.0,
            },
            "worked_example": {"fd_khz": 4.00, "v_mps": 8.00, "mdot_kg_s": 160.00},
            "check": "4.00 * 1480.0 / (2 * 370.0) = 8.00 exactly; 1600 * 0.0125 * 8.00 = 160.00 exactly; 6000 s + 720 s = 6720 s = 12.0 min floor",
        },
        "raster": raster,
        "gate_snn": {
            "decision": "ACCEPT",
            "decision_window_ms": 36.0,
            "decision_window_s": 0.036,
            "code": "bt6.usd_line_gate",
            "note": "ACCEPT accumulator wins: ultrasonic-Doppler slurry-velocity evidence overpowers the Shiftveil skip advocate",
            "decode_rule": "accept if vel_estimator AND carrier_norm AND line_margin fire inside the window; vendor_skip_advocate is necessary-but-not-sufficient and cannot release L-1 and L-2",
            "populations": [
                gate_pop("vel_estimator", 80, 1.5, 50.0, w_s),
                gate_pop("carrier_norm", 64, 1.2, 31.25, w_s),
                gate_pop("line_margin", 40, 1.0, 50.0, w_s),
                gate_pop("vendor_skip_advocate", 32, 0.7, 25.0, w_s),
                gate_pop("accept_latch", 96, 1.8, 62.5, w_s),
            ],
        },
        "gate_compute": gate_compute(
            [
                {"check": "bt6.usd_scorer", "neurons": 80, "mean_rate_hz": 50.0, "window_ms": 36.0},
                {"check": "bt6.vel_scorer", "neurons": 40, "mean_rate_hz": 62.5, "window_ms": 32.0},
            ]
        ),
        "meta": meta_common(
            id="nelb-r62-189",
            clock_domain="bt6-usd-sim-relative-ms-t0-2026-08-19T03:00:00Z",
            tags=["ultrasonic-doppler", "ACCEPT", "REJECT", "serialized-reconstruction", "operational-t2"],
        ),
    }
